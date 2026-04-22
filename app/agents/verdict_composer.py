from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.schemas.debate import ScorecardRecord, VerdictRecord
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
        verdict = VerdictRecord(
            session_id=payload.session_id,
            winner=payload.scorecard.winner,
            summary=f"Side {winning_side} won on the final judged rubric.",
            strengths=[
                f"Side {winning_side} maintained stronger judged structure.",
                "The winner converted more of its transcript into scoreable claims.",
            ],
            weaknesses=["The debate still depends on transcript-quality voice capture."],
            deciding_factors=[
                "Claim density",
                "Contextual evidence coverage",
                "Responsiveness across the captured exchange",
            ],
            audit_notes=[
                "Live score remained provisional throughout capture.",
                "Final verdict was generated only after the debate was explicitly ended.",
            ],
        )
        return VerdictComposerOutput(verdict=verdict)
