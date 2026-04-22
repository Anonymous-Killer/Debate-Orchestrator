from __future__ import annotations

from collections import Counter
from typing import Optional

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.core.enums import DebateSide
from app.schemas.debate import ClaimRecord, EvidenceRecord, ParticipantScore, ScorecardRecord
from app.services.reasoning import NvidiaNIMReasoningProvider


class JudgeInput(BaseModel):
    session_id: str
    transcript: list[dict]
    claims: list[ClaimRecord]
    evidence_items: list[EvidenceRecord]


class JudgeOutput(BaseModel):
    scorecard: ScorecardRecord


class JudgeAgent(BaseAgent[JudgeInput, JudgeOutput]):
    def __init__(self, reasoning_provider: Optional[NvidiaNIMReasoningProvider] = None) -> None:
        self.reasoning_provider = reasoning_provider

    def run(self, payload: JudgeInput) -> JudgeOutput:
        if self.reasoning_provider and self.reasoning_provider.available:
            try:
                result = self.reasoning_provider.complete_json(
                    (
                        "Judge the debate using a rubric and return strict JSON with scorecard. "
                        "Include participant_a, participant_b, winner, confidence, judge_summary, rubric_version."
                    ),
                    payload.model_dump(),
                )
                return JudgeOutput(scorecard=ScorecardRecord(session_id=payload.session_id, **result["scorecard"]))
            except Exception:
                pass

        utterance_counts = Counter(turn["speaker_side"] for turn in payload.transcript)
        claim_counts = Counter(claim.speaker_side for claim in payload.claims)
        evidence_counts = Counter()
        claim_lookup = {claim.id: claim for claim in payload.claims}
        for item in payload.evidence_items:
            claim = claim_lookup.get(item.claim_id)
            if claim:
                evidence_counts[claim.speaker_side] += 1

        score_a = self._participant_score(
            utterance_counts[DebateSide.A], claim_counts[DebateSide.A], evidence_counts[DebateSide.A]
        )
        score_b = self._participant_score(
            utterance_counts[DebateSide.B], claim_counts[DebateSide.B], evidence_counts[DebateSide.B]
        )
        winner = DebateSide.A if score_a.total >= score_b.total else DebateSide.B
        scorecard = ScorecardRecord(
            session_id=payload.session_id,
            participant_a=score_a,
            participant_b=score_b,
            winner=winner,
            confidence=0.66,
            judge_summary="Final judging used transcript coverage, claim density, and contextual evidence.",
        )
        return JudgeOutput(scorecard=scorecard)

    @staticmethod
    def _participant_score(utterances: int, claims: int, evidence: int) -> ParticipantScore:
        logic = min(10.0, 4 + claims * 0.8)
        evidence_score = min(10.0, 3 + evidence * 0.5)
        responsiveness = min(10.0, 3 + utterances * 0.7)
        clarity = min(10.0, 4 + utterances * 0.4)
        cross_exam = min(10.0, 3 + claims * 0.3)
        penalties = 1.5 if utterances == 0 else 0.0
        total = round(logic + evidence_score + responsiveness + clarity + cross_exam - penalties, 2)
        return ParticipantScore(
            logic=round(logic, 2),
            evidence=round(evidence_score, 2),
            responsiveness=round(responsiveness, 2),
            clarity=round(clarity, 2),
            cross_exam=round(cross_exam, 2),
            penalties=round(penalties, 2),
            total=total,
        )
