from __future__ import annotations

from app.core.enums import DebatePhase
from app.core.exceptions import InvalidStateTransition


class DebateStateMachine:
    transitions: dict[DebatePhase, set[DebatePhase]] = {
        DebatePhase.INIT: {DebatePhase.TOPIC_LOCK},
        DebatePhase.TOPIC_LOCK: {DebatePhase.STANCE_CAPTURE},
        DebatePhase.STANCE_CAPTURE: {DebatePhase.LIVE_CAPTURE},
        DebatePhase.LIVE_CAPTURE: {DebatePhase.TRANSCRIPT_FINALIZED},
        DebatePhase.TRANSCRIPT_FINALIZED: {DebatePhase.CLAIM_EXTRACTION},
        DebatePhase.CLAIM_EXTRACTION: {DebatePhase.FACT_CHECK},
        DebatePhase.FACT_CHECK: {DebatePhase.SCORING},
        DebatePhase.SCORING: {DebatePhase.VERDICT},
        DebatePhase.VERDICT: {DebatePhase.AUDIT},
        DebatePhase.AUDIT: set(),
    }

    def ensure_can_transition(self, current: DebatePhase, target: DebatePhase) -> None:
        if target not in self.transitions[current]:
            raise InvalidStateTransition(f"Cannot transition from {current} to {target}")

