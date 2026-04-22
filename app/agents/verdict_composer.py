from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.schemas.debate import ParticipantScore, ScorecardRecord, VerdictRecord
from app.services.reasoning import NvidiaNIMReasoningProvider


class VerdictComposerInput(BaseModel):
    session_id: str
    scorecard: ScorecardRecord


class VerdictComposerOutput(BaseModel):
    verdict: VerdictRecord


class VerdictComposer(BaseAgent[VerdictComposerInput, VerdictComposerOutput]):
    def __init__(self, reasoning_provider: Optional[NvidiaNIMReasoningProvider] = None) -> None:
        self.reasoning_provider = reasoning_provider

    def run(self, payload: VerdictComposerInput) -> VerdictComposerOutput:
        if self.reasoning_provider and self.reasoning_provider.available:
            try:
                result = self.reasoning_provider.complete_json(
                    (
                        "Compose the final verdict and return strict JSON with verdict. "
                        "Include winner, summary, strengths, weaknesses, deciding_factors, audit_notes."
                    ),
                    payload.model_dump(),
                )
                return VerdictComposerOutput(
                    verdict=VerdictRecord(session_id=payload.session_id, **result["verdict"])
                )
            except Exception:
                pass

        winning_side = payload.scorecard.winner.value
        losing_side = "B" if winning_side == "A" else "A"
        winner_scores = (
            payload.scorecard.participant_a
            if winning_side == "A"
            else payload.scorecard.participant_b
        )
        loser_scores = (
            payload.scorecard.participant_b
            if winning_side == "A"
            else payload.scorecard.participant_a
        )
        strengths = self._build_strengths(winning_side, winner_scores)
        weaknesses = self._build_weaknesses(losing_side, loser_scores)
        deciding_factors = self._build_deciding_factors(winner_scores, loser_scores)
        verdict = VerdictRecord(
            session_id=payload.session_id,
            winner=payload.scorecard.winner,
            summary=f"Side {winning_side} won on the final judged rubric.",
            strengths=strengths,
            weaknesses=weaknesses,
            deciding_factors=deciding_factors,
            audit_notes=[
                "Live score remained provisional throughout capture.",
                "Final verdict was generated only after the debate was explicitly ended.",
            ],
        )
        return VerdictComposerOutput(verdict=verdict)

    @staticmethod
    def _build_strengths(winning_side: str, scores: ParticipantScore) -> list[str]:
        strengths: list[str] = []
        if scores.logic >= 7:
            strengths.append(f"Side {winning_side} maintained stronger logical structure.")
        if scores.evidence >= 6:
            strengths.append(f"Side {winning_side} supported more of its case with usable evidence.")
        if scores.responsiveness >= 6:
            strengths.append(f"Side {winning_side} responded more directly to the opposing case.")
        if scores.clarity >= 6:
            strengths.append(f"Side {winning_side} presented its position more clearly.")
        if not strengths:
            strengths.append(f"Side {winning_side} put together the more complete judged performance.")
        return strengths[:3]

    @staticmethod
    def _build_weaknesses(losing_side: str, scores: ParticipantScore) -> list[str]:
        weakness_checks = [
            ("logic", f"Side {losing_side} had weaker logical consistency."),
            ("evidence", f"Side {losing_side} relied on weaker or thinner evidence support."),
            ("responsiveness", f"Side {losing_side} answered the opposing points less directly."),
            ("clarity", f"Side {losing_side} made parts of its case less clearly."),
            ("cross_exam", f"Side {losing_side} was less effective in pressure-testing the opposing side."),
        ]
        ranked = sorted(weakness_checks, key=lambda item: getattr(scores, item[0]))
        weaknesses = [
            message
            for field, message in ranked[:2]
            if getattr(scores, field) < 7
        ]
        if scores.penalties > 0:
            weaknesses.append(f"Side {losing_side} also incurred penalties that hurt its final score.")
        if not weaknesses:
            weaknesses.append(f"Side {losing_side} was edged out on overall debate execution.")
        return weaknesses[:3]

    @staticmethod
    def _build_deciding_factors(
        winner_scores: ParticipantScore,
        loser_scores: ParticipantScore,
    ) -> list[str]:
        categories = [
            ("logic", "Logical structure"),
            ("evidence", "Evidence support"),
            ("responsiveness", "Responsiveness"),
            ("clarity", "Clarity"),
            ("cross_exam", "Cross-exam performance"),
        ]
        ranked = sorted(
            categories,
            key=lambda item: getattr(winner_scores, item[0]) - getattr(loser_scores, item[0]),
            reverse=True,
        )
        deciding = [
            label
            for field, label in ranked
            if getattr(winner_scores, field) > getattr(loser_scores, field)
        ]
        return deciding[:3] or ["Overall judged consistency"]
