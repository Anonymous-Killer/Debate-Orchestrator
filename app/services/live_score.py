from __future__ import annotations

import math
import re
from typing import Optional

from app.core.config import settings
from app.core.enums import DebateSide
from app.schemas.debate import DebateSession, LiveScore, TurnRecord
from app.services.reasoning import NvidiaNIMReasoningProvider


class LiveScoreService:
    strong_terms = {
        "because",
        "evidence",
        "data",
        "therefore",
        "example",
        "shows",
        "impact",
        "clear",
        "direct",
    }

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
                "confidence, reasoning_summary. Normalize the score to 100 and keep it provisional."
            ),
            payload,
        )
        return LiveScore(**result)

    def _fallback_update(self, session: DebateSession, recent_turns: list[TurnRecord]) -> LiveScore:
        latest = recent_turns[-1]
        words = re.findall(r"\w+", latest.transcript_text.lower())
        weighted_terms = sum(1 for word in words if word in self.strong_terms)
        punctuation_bonus = latest.transcript_text.count("?") + latest.transcript_text.count("!")
        brevity_bonus = 1 if 8 <= len(words) <= 45 else 0
        raw_delta = min(
            settings.live_score_max_delta,
            max(1, weighted_terms + punctuation_bonus + brevity_bonus),
        )

        previous_a = session.current_live_score.side_a_percent
        direction = 1 if latest.speaker_side == DebateSide.A else -1
        next_a = previous_a + (raw_delta * direction)
        next_a = max(settings.live_score_floor, min(settings.live_score_ceiling, next_a))
        next_b = 100 - next_a
        delta_a = next_a - previous_a
        delta_b = -delta_a
        trend = "A_up" if delta_a > 0 else "B_up" if delta_a < 0 else "steady"
        confidence = round(min(0.95, 0.5 + math.fabs(delta_a) / 20), 2)
        reason = (
            f"Side {latest.speaker_side.value} gained momentum with a clearer recent exchange."
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
