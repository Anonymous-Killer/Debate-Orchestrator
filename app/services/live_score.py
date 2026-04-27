from __future__ import annotations

import math
from typing import Optional

from pydantic import ValidationError

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
            return self._provider_update_with_retries(session, recent_turns)

        return self._fallback_update(session, recent_turns)

    def _provider_update_with_retries(self, session: DebateSession, recent_turns: list[TurnRecord]) -> LiveScore:
        attempts = max(1, settings.nim_live_score_retries + 1)
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                return self._provider_update(session, recent_turns)
            except Exception as error:
                last_error = error
        return self._preserve_score_after_provider_failure(session, last_error)

    @staticmethod
    def _preserve_score_after_provider_failure(session: DebateSession, error: Exception | None) -> LiveScore:
        previous = session.current_live_score
        return LiveScore(
            side_a_percent=previous.side_a_percent,
            side_b_percent=previous.side_b_percent,
            delta_a=0,
            delta_b=0,
            trend="steady",
            confidence=0.0,
            reasoning_summary=(
                "NIM live scoring failed after retries, so the previous score was preserved. "
                f"Provider error: {error}"
            ),
            topic_relevance=0.0,
            argument_quality=0.0,
            score_change_allowed=False,
            scoring_source="nim_failed_preserved",
        )

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
                "Return strict JSON with these fields: side_a_percent, side_b_percent, delta_a, delta_b, "
                "trend, confidence, reasoning_summary, topic_relevance, argument_quality, "
                "score_change_allowed, scoring_source. "
                "topic_relevance and argument_quality must be numbers from 0.0 to 1.0. "
                "score_change_allowed must be false unless the latest point is a meaningful argument connected "
                "to the debate topic and the speaker's declared stance. "
                "Filler, greetings, repeated words, hesitation, nonsense, very short non-arguments, and off-topic "
                "remarks must have topic_relevance below 0.25 or argument_quality below 0.25, "
                "score_change_allowed false, and must not increase the speaker's score. "
                "If score_change_allowed is false, keep the split unchanged or apply a small penalty to the speaker. "
                "If the point is relevant but helps the opposing stance, reduce the speaker's score. "
                "Normalize the score to 100, keep it provisional, and never exceed a 90/10 split. "
                "Use scoring_source='nim'."
            ),
            {
                **payload,
                "stance_a": session.stance_a,
                "stance_b": session.stance_b,
            },
        )
        try:
            live_score = LiveScore(**self._normalize_provider_result(result))
        except ValidationError as error:
            raise RuntimeError(f"NIM returned invalid live score JSON: {error}") from error
        return self._enforce_provider_score_gates(session, latest, live_score)

    @staticmethod
    def _normalize_provider_result(result: dict) -> dict:
        normalized = dict(result)
        for key in ("side_a_percent", "side_b_percent", "delta_a", "delta_b"):
            if key in normalized and isinstance(normalized[key], float):
                normalized[key] = int(round(normalized[key]))

        if "side_a_percent" in normalized:
            normalized["side_a_percent"] = max(0, min(100, int(normalized["side_a_percent"])))
            normalized["side_b_percent"] = 100 - normalized["side_a_percent"]

        return normalized

    def _enforce_provider_score_gates(
        self,
        session: DebateSession,
        latest: TurnRecord,
        live_score: LiveScore,
    ) -> LiveScore:
        signal = analyze_crowd_signal(latest.transcript_text)
        if signal.crowd_backlash:
            return self._force_crowd_backlash_penalty(session, latest, live_score)

        too_low_quality = live_score.topic_relevance < 0.25 or live_score.argument_quality < 0.25
        if live_score.score_change_allowed and not too_low_quality:
            live_score.side_a_percent = max(
                settings.live_score_floor,
                min(settings.live_score_ceiling, live_score.side_a_percent),
            )
            live_score.side_b_percent = 100 - live_score.side_a_percent
            live_score.delta_a = live_score.side_a_percent - session.current_live_score.side_a_percent
            live_score.delta_b = -live_score.delta_a
            live_score.trend = "A_up" if live_score.delta_a > 0 else "B_up" if live_score.delta_a < 0 else "steady"
            live_score.scoring_source = live_score.scoring_source or "nim"
            return live_score

        previous_a = session.current_live_score.side_a_percent
        penalty = 2
        if latest.speaker_side == DebateSide.A:
            next_a = max(settings.live_score_floor, previous_a - penalty)
        else:
            next_a = min(settings.live_score_ceiling, previous_a + penalty)
        next_b = 100 - next_a
        delta_a = next_a - previous_a
        return LiveScore(
            side_a_percent=next_a,
            side_b_percent=next_b,
            delta_a=delta_a,
            delta_b=-delta_a,
            trend="A_up" if delta_a > 0 else "B_up" if delta_a < 0 else "steady",
            confidence=max(0.5, live_score.confidence),
            reasoning_summary=(
                "No positive momentum awarded because the point was not sufficiently relevant "
                "or did not make a meaningful argument."
            ),
            topic_relevance=live_score.topic_relevance,
            argument_quality=live_score.argument_quality,
            score_change_allowed=False,
            scoring_source="nim_gated",
        )

    @staticmethod
    def _force_crowd_backlash_penalty(
        session: DebateSession,
        latest: TurnRecord,
        live_score: LiveScore,
    ) -> LiveScore:
        previous_a = session.current_live_score.side_a_percent
        penalty = 10
        if latest.speaker_side == DebateSide.A:
            next_a = max(settings.live_score_floor, previous_a - penalty)
        else:
            next_a = min(settings.live_score_ceiling, previous_a + penalty)
        next_b = 100 - next_a
        delta_a = next_a - previous_a
        return LiveScore(
            side_a_percent=next_a,
            side_b_percent=next_b,
            delta_a=delta_a,
            delta_b=-delta_a,
            trend="A_up" if delta_a > 0 else "B_up" if delta_a < 0 else "steady",
            confidence=max(0.75, live_score.confidence),
            reasoning_summary=(
                "NIM response was overridden because the point triggered a strong crowd backlash "
                "for discriminatory or ethically toxic framing."
            ),
            topic_relevance=live_score.topic_relevance,
            argument_quality=live_score.argument_quality,
            score_change_allowed=False,
            scoring_source="nim_overridden_crowd_backlash",
        )

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
            topic_relevance=0.5,
            argument_quality=0.5,
            score_change_allowed=True,
            scoring_source="fallback",
        )
