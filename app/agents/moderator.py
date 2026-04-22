from __future__ import annotations

from pydantic import BaseModel

from app.agents.base import BaseAgent


class ModeratorInput(BaseModel):
    session_id: str
    topic: str
    utterance_count: int
    side_a_utterances: int
    side_b_utterances: int


class ModeratorOutput(BaseModel):
    status: str
    phase_complete: bool
    issues: list[str]
    normalized_topic: str
    next_expected_action: str


class ModeratorAgent(BaseAgent[ModeratorInput, ModeratorOutput]):
    def run(self, payload: ModeratorInput) -> ModeratorOutput:
        issues: list[str] = []
        if payload.utterance_count == 0:
            issues.append("No utterances were captured.")
        if payload.side_a_utterances == 0:
            issues.append("Side A never spoke.")
        if payload.side_b_utterances == 0:
            issues.append("Side B never spoke.")
        return ModeratorOutput(
            status="processable" if payload.utterance_count else "insufficient",
            phase_complete=payload.utterance_count > 0,
            issues=issues,
            normalized_topic=payload.topic.strip(),
            next_expected_action="claim_extraction",
        )

