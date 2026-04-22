from __future__ import annotations

import math
from typing import Optional

from app.core.config import settings
from app.core.enums import DebateSide
from app.schemas.debate import DebateSession, LiveScore, TurnRecord
from app.services.crowd_reaction_rules import analyze_crowd_signal, stance_consistency
from app.services.reasoning import NvidiaNIMReasoningProvider


class LiveScoreService:
    def __init__(self, reasoning_provider: Optional[NvidiaNIMReasoningProvider] = None) -> None:
        self.reasoning_provider = reasoning_provider

    def update(self, session: DebateSession, recent_turns: list[TurnRecord]) -> LiveScore:
        if self.reasoning_provider and self.reasoning_provider.available:
            try:
                return self._provider_update(session, recent_turns)
            except Exception:
                pass

        return self._fallback_update(session, recent_turns)

    def _provider_update(self, session: DebateSession, recent_turns: list[TurnRecord]) -> LiveScore:
        latest = recent_turns[-1]
        payload = {
            "topic": session.topic,
            "active_side": latest.speaker_side.value,
            "latest_transcript_text": latest.transcript_text,
            "previous_live_score": session.current_live_score.model_dump(),
        }
        result = self.reasoning_provider.complete_json(
            (
                "You are a debate crowd reaction scorer. "
                "Return JSON with side_a_percent, side_b_percent, delta_a, delta_b, trend, "
                "confidence, reasoning_summary. Normalize the score to 100, keep it provisional, "
                "never exceed a 90/10 split, and allow sharp momentum swings for unusually strong, "
                "compassion-driven, emotionally resonant, or controversial arguments. "
                "Also score whether the latest point is consistent with the speaker's declared stance. "
                "If a speaker makes a strong point that actually helps the opposing stance, reduce that speaker's live score."
            ),
            {
                **payload,
                "stance_a": session.stance_a,
                "stance_b": session.stance_b,
            },
        )
        return LiveScore(**result)

    def _fallback_update(self, session: DebateSession, recent_turns: list[TurnRecord]) -> LiveScore:
        latest = recent_turns[-1]
        signal = analyze_crowd_signal(latest.transcript_text)
        words = latest.transcript_text.lower().split()
        punctuation_bonus = latest.transcript_text.count("?") + latest.transcript_text.count("!")
        brevity_bonus = 1 if 8 <= len(words) <= 45 else 0
        raw_delta = (
            2
            + signal.weighted_terms
            + punctuation_bonus
            + brevity_bonus
            + (signal.emotional_hits * 2)
            + (signal.controversial_hits * 2)
            + (signal.amplifier_bonus * 3)
            + signal.contrast_bonus
            + signal.emphasis_bonus
        )
        if signal.emotional_hits >= 2 or signal.controversial_hits >= 2 or signal.amplifier_bonus >= 1:
            raw_delta += 3
        crowd_backlash = signal.crowd_backlash
        if crowd_backlash:
            raw_delta += 8
        raw_delta = min(settings.live_score_max_delta, max(2, raw_delta))

        stance = session.stance_a if latest.speaker_side == DebateSide.A else session.stance_b
        consistency = stance_consistency(stance or "", latest.transcript_text)
        if consistency == -1:
            raw_delta += 6

        previous_a = session.current_live_score.side_a_percent
        direction = 1 if latest.speaker_side == DebateSide.A else -1
        if consistency == -1 or crowd_backlash:
            direction *= -1
        next_a = previous_a + (raw_delta * direction)
        next_a = max(settings.live_score_floor, min(settings.live_score_ceiling, next_a))
        next_b = 100 - next_a
        delta_a = next_a - previous_a
        delta_b = -delta_a
        trend = "A_up" if delta_a > 0 else "B_up" if delta_a < 0 else "steady"
        confidence = round(min(0.98, 0.52 + math.fabs(delta_a) / 16), 2)
        descriptors = list(signal.descriptors)
        if consistency == -1:
            descriptors.append("stance-breaking")
        descriptor_text = ", ".join(descriptors) if descriptors else "clear"
        if crowd_backlash:
            reason = (
                f"Side {latest.speaker_side.value} lost momentum because the point triggered a strong crowd backlash "
                f"for discriminatory or ethically toxic framing."
            )
        elif consistency == -1:
            reason = (
                f"Side {latest.speaker_side.value} lost momentum because the point sounded strong "
                f"but cut against that side's stated stance."
            )
        else:
            reason = (
                f"Side {latest.speaker_side.value} gained momentum with a {descriptor_text} point that hit the crowd harder."
                if delta_a != 0
                else "Momentum remained balanced during the latest exchange."
            )
        return LiveScore(
            side_a_percent=next_a,
            side_b_percent=next_b,
            delta_a=delta_a,
            delta_b=delta_b,
            trend=trend,
            confidence=confidence,
            reasoning_summary=reason,
        )
