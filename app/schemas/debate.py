from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.core.enums import CaptureStatus, DebatePhase, DebateSide, DebateStatus, SpeakerRole, TurnType


class DebateRules(BaseModel):
    scoring_style: str = "crowd_reaction_plus_final_judging"
    min_utterances_per_side: int = 1


class CreateDebateRequest(BaseModel):
    topic: str
    participant_a_id: str
    participant_b_id: str
    rules: DebateRules = Field(default_factory=DebateRules)


class StartDebateRequest(BaseModel):
    stance_a: str
    stance_b: str
    active_side: DebateSide = DebateSide.A


class UtteranceCreate(BaseModel):
    transcript_text: Optional[str] = None
    audio_ref: Optional[str] = None
    audio_base64: Optional[str] = None
    audio_mime_type: Optional[str] = None
    idempotency_key: Optional[str] = None

    @model_validator(mode="after")
    def validate_payload(self) -> "UtteranceCreate":
        if not self.transcript_text and not self.audio_ref and not self.audio_base64:
            raise ValueError("Provide transcript_text, audio_ref, or audio_base64")
        return self


class SwitchSideRequest(BaseModel):
    next_side: DebateSide


class ParticipantSummary(BaseModel):
    a: str
    b: str


class StanceSummary(BaseModel):
    a: Optional[str] = None
    b: Optional[str] = None


class LiveScore(BaseModel):
    side_a_percent: int
    side_b_percent: int
    delta_a: int = 0
    delta_b: int = 0
    trend: str = "steady"
    confidence: float = 0.5
    reasoning_summary: str = "Debate momentum is balanced."
    topic_relevance: float = 0.5
    argument_quality: float = 0.5
    score_change_allowed: bool = True
    scoring_source: str = "fallback"
    is_provisional: bool = True
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def validate_total(self) -> "LiveScore":
        total = self.side_a_percent + self.side_b_percent
        if total != 100:
            raise ValueError("Live score must normalize to 100")
        return self


class LiveScoreSnapshot(LiveScore):
    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    sequence_no: int


class TurnRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    sequence_no: int
    speaker_id: str
    speaker_role: SpeakerRole = SpeakerRole.PARTICIPANT
    speaker_side: DebateSide
    phase: DebatePhase
    turn_type: TurnType = TurnType.UTTERANCE
    transcript_text: str
    audio_ref: Optional[str] = None
    transcription_source: str = "manual"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClaimRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    speaker_side: DebateSide
    source_turn_id: str
    text: str
    claim_type: str
    confidence: float
    status: str = "reviewed"


class EvidenceRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    claim_id: str
    stance: str
    summary: str
    source_type: str
    relevance_score: float
    credibility_score: float
    notes: str


class ParticipantScore(BaseModel):
    logic: float
    evidence: float
    responsiveness: float
    clarity: float
    cross_exam: float
    penalties: float
    total: float


class ScorecardRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    participant_a: ParticipantScore
    participant_b: ParticipantScore
    winner: DebateSide
    confidence: float
    judge_summary: str
    rubric_version: str = "v1"


class VerdictRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    winner: DebateSide
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    deciding_factors: list[str]
    audit_notes: list[str]


class SessionEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    event_type: str
    from_phase: DebatePhase
    to_phase: DebatePhase
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DebateSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    topic: str
    status: DebateStatus = DebateStatus.CREATED
    current_phase: DebatePhase = DebatePhase.INIT
    capture_status: CaptureStatus = CaptureStatus.IDLE
    participant_a_id: str
    participant_b_id: str
    stance_a: Optional[str] = None
    stance_b: Optional[str] = None
    active_side: DebateSide = DebateSide.A
    rules: DebateRules = Field(default_factory=DebateRules)
    phase_metadata: dict[str, Any] = Field(default_factory=dict)
    current_live_score: LiveScore = Field(
        default_factory=lambda: LiveScore(side_a_percent=50, side_b_percent=50)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    transcript_finalized_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DebateSummaryResponse(BaseModel):
    id: str
    status: DebateStatus
    current_phase: DebatePhase
    capture_status: CaptureStatus
    topic: str
    participants: ParticipantSummary
    stances: StanceSummary
    active_side: DebateSide
    live_score: LiveScore


class TranscriptResponse(BaseModel):
    session_id: str
    turns: list[TurnRecord]


class StartDebateResponse(BaseModel):
    id: str
    status: DebateStatus
    current_phase: DebatePhase
    capture_status: CaptureStatus
    active_side: DebateSide
    next_expected_action: str


class UtteranceResponse(BaseModel):
    accepted: bool
    session_id: str
    active_side: DebateSide
    capture_status: CaptureStatus
    sequence_no: int
    transcript_text: str
    transcription_source: str
    live_score: LiveScore


class EndDebateResponse(BaseModel):
    session_id: str
    capture_status: CaptureStatus
    current_phase: DebatePhase
    verdict_available: bool
    live_score: LiveScore
