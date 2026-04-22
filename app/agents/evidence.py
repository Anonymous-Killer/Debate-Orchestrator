from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.schemas.debate import ClaimRecord, EvidenceRecord
from app.services.reasoning import NvidiaNIMReasoningProvider


class EvidenceInput(BaseModel):
    session_id: str
    claims: list[ClaimRecord]


class EvidenceOutput(BaseModel):
    evidence_items: list[EvidenceRecord]


class EvidenceAgent(BaseAgent[EvidenceInput, EvidenceOutput]):
    def __init__(self, reasoning_provider: Optional[NvidiaNIMReasoningProvider] = None) -> None:
        self.reasoning_provider = reasoning_provider

    def run(self, payload: EvidenceInput) -> EvidenceOutput:
        if self.reasoning_provider and self.reasoning_provider.available:
            try:
                result = self.reasoning_provider.complete_json(
                    (
                        "Assess debate claims and return strict JSON with evidence_items. "
                        "Each item must include claim_id, stance, summary, source_type, relevance_score, "
                        "credibility_score, notes."
                    ),
                    payload.model_dump(),
                )
                return EvidenceOutput(
                    evidence_items=[EvidenceRecord(session_id=payload.session_id, **item) for item in result["evidence_items"]]
                )
            except Exception:
                pass

        evidence_items = [
            EvidenceRecord(
                session_id=payload.session_id,
                claim_id=claim.id,
                stance="contextual",
                summary=f"Context summary for claim: {claim.text[:80]}",
                source_type="transcript_context",
                relevance_score=0.7,
                credibility_score=0.55,
                notes="Stub evidence assessment based on transcript only.",
            )
            for claim in payload.claims
        ]
        return EvidenceOutput(evidence_items=evidence_items)
