from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.schemas.debate import ClaimRecord
from app.services.reasoning import NvidiaNIMReasoningProvider


class ClaimExtractorInput(BaseModel):
    session_id: str
    transcript: list[dict]


class ClaimExtractorOutput(BaseModel):
    claims: list[ClaimRecord]


class ClaimExtractorAgent(BaseAgent[ClaimExtractorInput, ClaimExtractorOutput]):
    def __init__(self, reasoning_provider: Optional[NvidiaNIMReasoningProvider] = None) -> None:
        self.reasoning_provider = reasoning_provider

    def run(self, payload: ClaimExtractorInput) -> ClaimExtractorOutput:
        if self.reasoning_provider and self.reasoning_provider.available:
            try:
                result = self.reasoning_provider.complete_json(
                    (
                        "Extract debate claims from the transcript. Return strict JSON with a claims array. "
                        "Each claim must include speaker_side, source_turn_id, text, claim_type, confidence, status."
                    ),
                    payload.model_dump(),
                )
                return ClaimExtractorOutput(
                    claims=[ClaimRecord(session_id=payload.session_id, **claim) for claim in result["claims"]]
                )
            except Exception:
                pass

        claims: list[ClaimRecord] = []
        for turn in payload.transcript:
            sentences = [item.strip() for item in re.split(r"[.!?]+", turn["transcript_text"]) if item.strip()]
            for sentence in sentences[:2]:
                claims.append(
                    ClaimRecord(
                        session_id=payload.session_id,
                        speaker_side=turn["speaker_side"],
                        source_turn_id=turn["id"],
                        text=sentence,
                        claim_type="assertion",
                        confidence=0.68,
                    )
                )
        return ClaimExtractorOutput(claims=claims)
