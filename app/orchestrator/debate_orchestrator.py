from __future__ import annotations

from datetime import datetime

from app.agents.claim_extractor import ClaimExtractorAgent, ClaimExtractorInput
from app.agents.evidence import EvidenceAgent, EvidenceInput
from app.agents.judge import JudgeAgent, JudgeInput
from app.agents.moderator import ModeratorAgent, ModeratorInput
from app.agents.verdict_composer import VerdictComposer, VerdictComposerInput
from app.core.enums import CaptureStatus, DebatePhase, DebateSide, DebateStatus, SpeakerRole
from app.core.exceptions import InvalidDebateAction
from app.orchestrator.state_machine import DebateStateMachine
from app.repositories.memory import InMemoryDebateRepository
from app.schemas.debate import (
    CreateDebateRequest,
    DebateSession,
    DebateSummaryResponse,
    EndDebateResponse,
    LiveScoreSnapshot,
    SessionEvent,
    StartDebateRequest,
    StartDebateResponse,
    TranscriptResponse,
    TurnRecord,
    UtteranceCreate,
    UtteranceResponse,
)
from app.services.live_score import LiveScoreService
from app.services.transcription import GeminiTranscriptionProvider


class DebateOrchestrator:
    def __init__(
        self,
        repository: InMemoryDebateRepository,
        state_machine: DebateStateMachine,
        live_score_service: LiveScoreService,
        transcription_provider: GeminiTranscriptionProvider,
        moderator_agent: ModeratorAgent,
        claim_extractor_agent: ClaimExtractorAgent,
        evidence_agent: EvidenceAgent,
        judge_agent: JudgeAgent,
        verdict_composer: VerdictComposer,
    ) -> None:
        self.repository = repository
        self.state_machine = state_machine
        self.live_score_service = live_score_service
        self.transcription_provider = transcription_provider
        self.moderator_agent = moderator_agent
        self.claim_extractor_agent = claim_extractor_agent
        self.evidence_agent = evidence_agent
        self.judge_agent = judge_agent
        self.verdict_composer = verdict_composer

    def create_debate(self, request: CreateDebateRequest) -> DebateSummaryResponse:
        session = DebateSession(
            topic=request.topic,
            participant_a_id=request.participant_a_id,
            participant_b_id=request.participant_b_id,
            rules=request.rules,
        )
        self.repository.create_session(session)
        return self._summary(session)

    def start_debate(self, session_id: str, request: StartDebateRequest) -> StartDebateResponse:
        session = self.repository.get_session(session_id)
        self._transition(session, DebatePhase.TOPIC_LOCK, {"action": "topic_locked"})
        session.stance_a = request.stance_a
        session.stance_b = request.stance_b
        self._transition(session, DebatePhase.STANCE_CAPTURE, {"action": "stances_captured"})
        session.active_side = request.active_side
        session.status = DebateStatus.ACTIVE
        session.capture_status = CaptureStatus.RECORDING
        session.started_at = datetime.utcnow()
        self._transition(session, DebatePhase.LIVE_CAPTURE, {"action": "live_capture_started"})
        self.repository.save_session(session)
        return StartDebateResponse(
            id=session.id,
            status=session.status,
            current_phase=session.current_phase,
            capture_status=session.capture_status,
            active_side=session.active_side,
            next_expected_action="submit_voice_utterance",
        )

    def ingest_utterance(self, session_id: str, request: UtteranceCreate) -> UtteranceResponse:
        session = self.repository.get_session(session_id)
        if session.current_phase != DebatePhase.LIVE_CAPTURE or session.capture_status != CaptureStatus.RECORDING:
            raise InvalidDebateAction("Utterances are only accepted while the debate is live.")

        transcription = self.transcription_provider.transcribe(request)
        sequence_no = len(self.repository.list_turns(session_id)) + 1
        speaker_id = session.participant_a_id if session.active_side == DebateSide.A else session.participant_b_id
        turn = TurnRecord(
            session_id=session_id,
            sequence_no=sequence_no,
            speaker_id=speaker_id,
            speaker_role=SpeakerRole.PARTICIPANT,
            speaker_side=session.active_side,
            phase=session.current_phase,
            transcript_text=transcription.transcript_text,
            audio_ref=request.audio_ref,
            transcription_source=transcription.provider,
            metadata={"transcription_source": transcription.source},
        )
        persisted = self.repository.add_turn(turn, idempotency_key=request.idempotency_key)
        turns = self.repository.list_turns(session_id)
        session.current_live_score = self.live_score_service.update(session, turns)
        session.phase_metadata["last_live_score_reason"] = session.current_live_score.reasoning_summary
        session.updated_at = datetime.utcnow()
        self.repository.add_live_score(
            LiveScoreSnapshot(
                session_id=session_id,
                sequence_no=persisted.sequence_no,
                **session.current_live_score.model_dump(),
            )
        )
        self.repository.save_session(session)
        return UtteranceResponse(
            accepted=True,
            session_id=session_id,
            active_side=session.active_side,
            capture_status=session.capture_status,
            sequence_no=persisted.sequence_no,
            transcript_text=persisted.transcript_text,
            transcription_source=persisted.transcription_source,
            live_score=session.current_live_score,
        )

    def switch_side(self, session_id: str, next_side: DebateSide) -> DebateSummaryResponse:
        session = self.repository.get_session(session_id)
        if session.current_phase != DebatePhase.LIVE_CAPTURE or session.capture_status != CaptureStatus.RECORDING:
            raise InvalidDebateAction("Sides can only be switched during live capture.")
        if session.active_side == next_side:
            raise InvalidDebateAction("The requested side is already active.")
        session.active_side = next_side
        session.updated_at = datetime.utcnow()
        self.repository.save_session(session)
        return self._summary(session)

    def end_debate(self, session_id: str) -> EndDebateResponse:
        session = self.repository.get_session(session_id)
        if session.current_phase != DebatePhase.LIVE_CAPTURE:
            raise InvalidDebateAction("The debate is not in a live state.")
        session.capture_status = CaptureStatus.ENDED
        session.ended_at = datetime.utcnow()
        self._transition(session, DebatePhase.TRANSCRIPT_FINALIZED, {"action": "debate_ended"})
        session.capture_status = CaptureStatus.PROCESSING
        self.repository.save_session(session)

        turns = self.repository.list_turns(session_id)
        moderator_output = self.moderator_agent.run(
            ModeratorInput(
                session_id=session_id,
                topic=session.topic,
                utterance_count=len(turns),
                side_a_utterances=sum(1 for turn in turns if turn.speaker_side == DebateSide.A),
                side_b_utterances=sum(1 for turn in turns if turn.speaker_side == DebateSide.B),
            )
        )
        session.phase_metadata["moderator_issues"] = moderator_output.issues
        self._transition(session, DebatePhase.CLAIM_EXTRACTION, {"action": "moderated"})

        transcript = [turn.model_dump() for turn in turns]
        claims = self.claim_extractor_agent.run(ClaimExtractorInput(session_id=session_id, transcript=transcript)).claims
        self.repository.save_claims(session_id, claims)
        self._transition(session, DebatePhase.FACT_CHECK, {"action": "claims_extracted", "count": len(claims)})

        evidence = self.evidence_agent.run(EvidenceInput(session_id=session_id, claims=claims)).evidence_items
        self.repository.save_evidence(session_id, evidence)
        self._transition(session, DebatePhase.SCORING, {"action": "evidence_completed", "count": len(evidence)})

        scorecard = self.judge_agent.run(
            JudgeInput(
                session_id=session_id,
                transcript=transcript,
                claims=claims,
                evidence_items=evidence,
            )
        ).scorecard
        self.repository.save_scorecard(scorecard)
        self._transition(session, DebatePhase.VERDICT, {"action": "scorecard_completed"})

        verdict = self.verdict_composer.run(
            VerdictComposerInput(session_id=session_id, scorecard=scorecard)
        ).verdict
        self.repository.save_verdict(verdict)
        self._transition(session, DebatePhase.AUDIT, {"action": "verdict_completed"})

        session.capture_status = CaptureStatus.COMPLETED
        session.status = DebateStatus.COMPLETED
        session.transcript_finalized_at = session.ended_at
        session.completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        self.repository.save_session(session)
        return EndDebateResponse(
            session_id=session_id,
            capture_status=session.capture_status,
            current_phase=session.current_phase,
            verdict_available=True,
            live_score=session.current_live_score,
        )

    def list_debates(self) -> list[DebateSummaryResponse]:
        return [self._summary(s) for s in self.repository.list_sessions()]

    def get_debate(self, session_id: str) -> DebateSummaryResponse:
        return self._summary(self.repository.get_session(session_id))

    def get_transcript(self, session_id: str) -> TranscriptResponse:
        self.repository.get_session(session_id)
        return TranscriptResponse(session_id=session_id, turns=self.repository.list_turns(session_id))

    def get_live_score(self, session_id: str):
        return self.repository.get_session(session_id).current_live_score

    def get_verdict(self, session_id: str):
        session = self.repository.get_session(session_id)
        verdict = self.repository.get_verdict(session_id)
        if verdict is None:
            if session.current_phase == DebatePhase.LIVE_CAPTURE:
                raise InvalidDebateAction("Verdict is not available until the debate is ended.")
            raise InvalidDebateAction("Verdict is not available for this debate yet.")
        return verdict

    def _transition(self, session: DebateSession, target: DebatePhase, payload: dict) -> None:
        current = session.current_phase
        self.state_machine.ensure_can_transition(current, target)
        session.current_phase = target
        session.updated_at = datetime.utcnow()
        self.repository.add_event(
            SessionEvent(
                session_id=session.id,
                event_type=payload.get("action", "transition"),
                from_phase=current,
                to_phase=target,
                payload=payload,
            )
        )

    @staticmethod
    def _summary(session: DebateSession) -> DebateSummaryResponse:
        return DebateSummaryResponse(
            id=session.id,
            status=session.status,
            current_phase=session.current_phase,
            capture_status=session.capture_status,
            topic=session.topic,
            participants={"a": session.participant_a_id, "b": session.participant_b_id},
            stances={"a": session.stance_a, "b": session.stance_b},
            active_side=session.active_side,
            live_score=session.current_live_score,
        )
