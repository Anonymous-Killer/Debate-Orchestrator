from __future__ import annotations

from collections import defaultdict
from typing import Optional

from app.core.exceptions import DebateNotFound
from app.schemas.debate import (
    ClaimRecord,
    DebateSession,
    EvidenceRecord,
    LiveScoreSnapshot,
    ScorecardRecord,
    SessionEvent,
    TurnRecord,
    VerdictRecord,
)


class InMemoryDebateRepository:
    def __init__(self) -> None:
        self.sessions: dict[str, DebateSession] = {}
        self.turns: dict[str, list[TurnRecord]] = defaultdict(list)
        self.events: dict[str, list[SessionEvent]] = defaultdict(list)
        self.live_scores: dict[str, list[LiveScoreSnapshot]] = defaultdict(list)
        self.claims: dict[str, list[ClaimRecord]] = defaultdict(list)
        self.evidence: dict[str, list[EvidenceRecord]] = defaultdict(list)
        self.scorecards: dict[str, ScorecardRecord] = {}
        self.verdicts: dict[str, VerdictRecord] = {}
        self.idempotency: dict[str, dict[str, TurnRecord]] = defaultdict(dict)

    def create_session(self, session: DebateSession) -> DebateSession:
        self.sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> DebateSession:
        session = self.sessions.get(session_id)
        if not session:
            raise DebateNotFound(f"Debate session {session_id} was not found")
        return session

    def save_session(self, session: DebateSession) -> DebateSession:
        self.sessions[session.id] = session
        return session

    def list_sessions(self) -> list[DebateSession]:
        return list(self.sessions.values())

    def add_turn(self, turn: TurnRecord, idempotency_key: Optional[str] = None) -> TurnRecord:
        if idempotency_key and idempotency_key in self.idempotency[turn.session_id]:
            return self.idempotency[turn.session_id][idempotency_key]
        self.turns[turn.session_id].append(turn)
        if idempotency_key:
            self.idempotency[turn.session_id][idempotency_key] = turn
        return turn

    def list_turns(self, session_id: str) -> list[TurnRecord]:
        return list(self.turns[session_id])

    def add_event(self, event: SessionEvent) -> SessionEvent:
        self.events[event.session_id].append(event)
        return event

    def add_live_score(self, snapshot: LiveScoreSnapshot) -> LiveScoreSnapshot:
        self.live_scores[snapshot.session_id].append(snapshot)
        return snapshot

    def list_live_scores(self, session_id: str) -> list[LiveScoreSnapshot]:
        return list(self.live_scores[session_id])

    def save_claims(self, session_id: str, claims: list[ClaimRecord]) -> None:
        self.claims[session_id] = claims

    def list_claims(self, session_id: str) -> list[ClaimRecord]:
        return list(self.claims[session_id])

    def save_evidence(self, session_id: str, evidence: list[EvidenceRecord]) -> None:
        self.evidence[session_id] = evidence

    def list_evidence(self, session_id: str) -> list[EvidenceRecord]:
        return list(self.evidence[session_id])

    def save_scorecard(self, scorecard: ScorecardRecord) -> ScorecardRecord:
        self.scorecards[scorecard.session_id] = scorecard
        return scorecard

    def get_scorecard(self, session_id: str) -> Optional[ScorecardRecord]:
        return self.scorecards.get(session_id)

    def save_verdict(self, verdict: VerdictRecord) -> VerdictRecord:
        self.verdicts[verdict.session_id] = verdict
        return verdict

    def get_verdict(self, session_id: str) -> Optional[VerdictRecord]:
        return self.verdicts.get(session_id)
