from __future__ import annotations

import json
from typing import Callable, List, Optional

from sqlmodel import Session, delete, select

from app.core.enums import CaptureStatus, DebatePhase, DebateSide, DebateStatus, SpeakerRole, TurnType
from app.core.exceptions import DebateNotFound
from app.models.entities import (
    ClaimEntity,
    DebateSessionEntity,
    EvidenceEntity,
    LiveScoreSnapshotEntity,
    ScorecardEntity,
    SessionEventEntity,
    TurnEntity,
    VerdictEntity,
)
from app.schemas.debate import (
    ClaimRecord,
    DebateRules,
    DebateSession,
    EvidenceRecord,
    LiveScore,
    LiveScoreSnapshot,
    ParticipantScore,
    ScorecardRecord,
    SessionEvent,
    TurnRecord,
    VerdictRecord,
)


class SQLDebateRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def create_session(self, session: DebateSession) -> DebateSession:
        with self.session_factory() as db:
            db.add(self._session_to_entity(session))
            db.commit()
        return session

    def get_session(self, session_id: str) -> DebateSession:
        with self.session_factory() as db:
            entity = db.get(DebateSessionEntity, session_id)
            if not entity:
                raise DebateNotFound(f"Debate session {session_id} was not found")
            return self._session_from_entity(entity)

    def save_session(self, session: DebateSession) -> DebateSession:
        with self.session_factory() as db:
            existing = db.get(DebateSessionEntity, session.id)
            if existing:
                db.delete(existing)
                db.commit()
            db.add(self._session_to_entity(session))
            db.commit()
        return session

    def list_sessions(self) -> List[DebateSession]:
        with self.session_factory() as db:
            rows = db.exec(select(DebateSessionEntity)).all()
            return [self._session_from_entity(row) for row in rows]

    def add_turn(self, turn: TurnRecord, idempotency_key: Optional[str] = None) -> TurnRecord:
        del idempotency_key
        with self.session_factory() as db:
            existing = db.exec(select(TurnEntity).where(TurnEntity.id == turn.id)).first()
            if existing:
                return self._turn_from_entity(existing)
            db.add(self._turn_to_entity(turn))
            db.commit()
        return turn

    def list_turns(self, session_id: str) -> List[TurnRecord]:
        with self.session_factory() as db:
            rows = db.exec(
                select(TurnEntity)
                .where(TurnEntity.session_id == session_id)
                .order_by(TurnEntity.sequence_no)
            ).all()
            return [self._turn_from_entity(row) for row in rows]

    def add_event(self, event: SessionEvent) -> SessionEvent:
        with self.session_factory() as db:
            db.add(
                SessionEventEntity(
                    id=event.id,
                    session_id=event.session_id,
                    event_type=event.event_type,
                    from_phase=event.from_phase.value,
                    to_phase=event.to_phase.value,
                    payload_json=json.dumps(event.payload),
                    created_at=event.created_at,
                )
            )
            db.commit()
        return event

    def add_live_score(self, snapshot: LiveScoreSnapshot) -> LiveScoreSnapshot:
        with self.session_factory() as db:
            db.add(
                LiveScoreSnapshotEntity(
                    id=snapshot.id,
                    session_id=snapshot.session_id,
                    sequence_no=snapshot.sequence_no,
                    side_a_percent=snapshot.side_a_percent,
                    side_b_percent=snapshot.side_b_percent,
                    delta_a=snapshot.delta_a,
                    delta_b=snapshot.delta_b,
                    trend=snapshot.trend,
                    confidence=snapshot.confidence,
                    reasoning_summary=snapshot.reasoning_summary,
                    is_provisional=snapshot.is_provisional,
                    updated_at=snapshot.updated_at,
                )
            )
            db.commit()
        return snapshot

    def list_live_scores(self, session_id: str) -> List[LiveScoreSnapshot]:
        with self.session_factory() as db:
            rows = db.exec(
                select(LiveScoreSnapshotEntity)
                .where(LiveScoreSnapshotEntity.session_id == session_id)
                .order_by(LiveScoreSnapshotEntity.sequence_no)
            ).all()
            return [
                LiveScoreSnapshot(
                    id=row.id,
                    session_id=row.session_id,
                    sequence_no=row.sequence_no,
                    side_a_percent=row.side_a_percent,
                    side_b_percent=row.side_b_percent,
                    delta_a=row.delta_a,
                    delta_b=row.delta_b,
                    trend=row.trend,
                    confidence=row.confidence,
                    reasoning_summary=row.reasoning_summary,
                    is_provisional=row.is_provisional,
                    updated_at=row.updated_at,
                )
                for row in rows
            ]

    def save_claims(self, session_id: str, claims: List[ClaimRecord]) -> None:
        with self.session_factory() as db:
            db.exec(delete(ClaimEntity).where(ClaimEntity.session_id == session_id))
            for claim in claims:
                db.add(
                    ClaimEntity(
                        id=claim.id,
                        session_id=claim.session_id,
                        speaker_side=claim.speaker_side.value,
                        source_turn_id=claim.source_turn_id,
                        text=claim.text,
                        claim_type=claim.claim_type,
                        confidence=claim.confidence,
                        status=claim.status,
                    )
                )
            db.commit()

    def list_claims(self, session_id: str) -> List[ClaimRecord]:
        with self.session_factory() as db:
            rows = db.exec(select(ClaimEntity).where(ClaimEntity.session_id == session_id)).all()
            return [
                ClaimRecord(
                    id=row.id,
                    session_id=row.session_id,
                    speaker_side=DebateSide(row.speaker_side),
                    source_turn_id=row.source_turn_id,
                    text=row.text,
                    claim_type=row.claim_type,
                    confidence=row.confidence,
                    status=row.status,
                )
                for row in rows
            ]

    def save_evidence(self, session_id: str, evidence: List[EvidenceRecord]) -> None:
        with self.session_factory() as db:
            db.exec(delete(EvidenceEntity).where(EvidenceEntity.session_id == session_id))
            for item in evidence:
                db.add(
                    EvidenceEntity(
                        id=item.id,
                        session_id=item.session_id,
                        claim_id=item.claim_id,
                        stance=item.stance,
                        summary=item.summary,
                        source_type=item.source_type,
                        relevance_score=item.relevance_score,
                        credibility_score=item.credibility_score,
                        notes=item.notes,
                    )
                )
            db.commit()

    def list_evidence(self, session_id: str) -> List[EvidenceRecord]:
        with self.session_factory() as db:
            rows = db.exec(select(EvidenceEntity).where(EvidenceEntity.session_id == session_id)).all()
            return [
                EvidenceRecord(
                    id=row.id,
                    session_id=row.session_id,
                    claim_id=row.claim_id,
                    stance=row.stance,
                    summary=row.summary,
                    source_type=row.source_type,
                    relevance_score=row.relevance_score,
                    credibility_score=row.credibility_score,
                    notes=row.notes,
                )
                for row in rows
            ]

    def save_scorecard(self, scorecard: ScorecardRecord) -> ScorecardRecord:
        with self.session_factory() as db:
            existing = db.exec(
                select(ScorecardEntity).where(ScorecardEntity.session_id == scorecard.session_id)
            ).first()
            if existing:
                db.delete(existing)
                db.commit()
            db.add(
                ScorecardEntity(
                    id=scorecard.id,
                    session_id=scorecard.session_id,
                    participant_a_json=json.dumps(scorecard.participant_a.model_dump()),
                    participant_b_json=json.dumps(scorecard.participant_b.model_dump()),
                    winner=scorecard.winner.value,
                    confidence=scorecard.confidence,
                    judge_summary=scorecard.judge_summary,
                    rubric_version=scorecard.rubric_version,
                )
            )
            db.commit()
        return scorecard

    def get_scorecard(self, session_id: str) -> Optional[ScorecardRecord]:
        with self.session_factory() as db:
            row = db.exec(select(ScorecardEntity).where(ScorecardEntity.session_id == session_id)).first()
            if not row:
                return None
            return ScorecardRecord(
                id=row.id,
                session_id=row.session_id,
                participant_a=ParticipantScore(**json.loads(row.participant_a_json)),
                participant_b=ParticipantScore(**json.loads(row.participant_b_json)),
                winner=DebateSide(row.winner),
                confidence=row.confidence,
                judge_summary=row.judge_summary,
                rubric_version=row.rubric_version,
            )

    def save_verdict(self, verdict: VerdictRecord) -> VerdictRecord:
        with self.session_factory() as db:
            existing = db.exec(select(VerdictEntity).where(VerdictEntity.session_id == verdict.session_id)).first()
            if existing:
                db.delete(existing)
                db.commit()
            db.add(
                VerdictEntity(
                    id=verdict.id,
                    session_id=verdict.session_id,
                    winner=verdict.winner.value,
                    summary=verdict.summary,
                    strengths_json=json.dumps(verdict.strengths),
                    weaknesses_json=json.dumps(verdict.weaknesses),
                    deciding_factors_json=json.dumps(verdict.deciding_factors),
                    audit_notes_json=json.dumps(verdict.audit_notes),
                )
            )
            db.commit()
        return verdict

    def get_verdict(self, session_id: str) -> Optional[VerdictRecord]:
        with self.session_factory() as db:
            row = db.exec(select(VerdictEntity).where(VerdictEntity.session_id == session_id)).first()
            if not row:
                return None
            return VerdictRecord(
                id=row.id,
                session_id=row.session_id,
                winner=DebateSide(row.winner),
                summary=row.summary,
                strengths=json.loads(row.strengths_json),
                weaknesses=json.loads(row.weaknesses_json),
                deciding_factors=json.loads(row.deciding_factors_json),
                audit_notes=json.loads(row.audit_notes_json),
            )

    @staticmethod
    def _session_to_entity(session: DebateSession) -> DebateSessionEntity:
        return DebateSessionEntity(
            id=session.id,
            topic=session.topic,
            status=session.status.value,
            current_phase=session.current_phase.value,
            capture_status=session.capture_status.value,
            participant_a_id=session.participant_a_id,
            participant_b_id=session.participant_b_id,
            stance_a=session.stance_a,
            stance_b=session.stance_b,
            active_side=session.active_side.value,
            rules_json=json.dumps(session.rules.model_dump()),
            phase_metadata_json=json.dumps(session.phase_metadata),
            current_live_score_a=session.current_live_score.side_a_percent,
            current_live_score_b=session.current_live_score.side_b_percent,
            created_at=session.created_at,
            updated_at=session.updated_at,
            started_at=session.started_at,
            ended_at=session.ended_at,
            transcript_finalized_at=session.transcript_finalized_at,
            completed_at=session.completed_at,
        )

    @staticmethod
    def _session_from_entity(entity: DebateSessionEntity) -> DebateSession:
        phase_metadata = json.loads(entity.phase_metadata_json or "{}")
        live_score = LiveScore(
            side_a_percent=entity.current_live_score_a,
            side_b_percent=entity.current_live_score_b,
            reasoning_summary=phase_metadata.get("last_live_score_reason", "Debate momentum is balanced."),
        )
        return DebateSession(
            id=entity.id,
            topic=entity.topic,
            status=DebateStatus(entity.status),
            current_phase=DebatePhase(entity.current_phase),
            capture_status=CaptureStatus(entity.capture_status),
            participant_a_id=entity.participant_a_id,
            participant_b_id=entity.participant_b_id,
            stance_a=entity.stance_a,
            stance_b=entity.stance_b,
            active_side=DebateSide(entity.active_side),
            rules=DebateRules(**json.loads(entity.rules_json or "{}")),
            phase_metadata=phase_metadata,
            current_live_score=live_score,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            started_at=entity.started_at,
            ended_at=entity.ended_at,
            transcript_finalized_at=entity.transcript_finalized_at,
            completed_at=entity.completed_at,
        )

    @staticmethod
    def _turn_to_entity(turn: TurnRecord) -> TurnEntity:
        return TurnEntity(
            id=turn.id,
            session_id=turn.session_id,
            sequence_no=turn.sequence_no,
            speaker_id=turn.speaker_id,
            speaker_role=turn.speaker_role.value,
            speaker_side=turn.speaker_side.value,
            phase=turn.phase.value,
            turn_type=turn.turn_type.value,
            transcript_text=turn.transcript_text,
            audio_ref=turn.audio_ref,
            transcription_source=turn.transcription_source,
            metadata_json=json.dumps(turn.metadata),
            created_at=turn.created_at,
        )

    @staticmethod
    def _turn_from_entity(entity: TurnEntity) -> TurnRecord:
        return TurnRecord(
            id=entity.id,
            session_id=entity.session_id,
            sequence_no=entity.sequence_no,
            speaker_id=entity.speaker_id,
            speaker_role=SpeakerRole(entity.speaker_role),
            speaker_side=DebateSide(entity.speaker_side),
            phase=DebatePhase(entity.phase),
            turn_type=TurnType(entity.turn_type),
            transcript_text=entity.transcript_text,
            audio_ref=entity.audio_ref,
            transcription_source=entity.transcription_source,
            created_at=entity.created_at,
            metadata=json.loads(entity.metadata_json or "{}"),
        )
