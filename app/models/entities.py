from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class DebateSessionEntity(SQLModel, table=True):
    id: str = Field(primary_key=True)
    topic: str
    status: str
    current_phase: str
    capture_status: str
    participant_a_id: str
    participant_b_id: str
    stance_a: Optional[str] = None
    stance_b: Optional[str] = None
    active_side: str
    rules_json: str = "{}"
    phase_metadata_json: str = "{}"
    current_live_score_a: int = 50
    current_live_score_b: int = 50
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    transcript_finalized_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TurnEntity(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    sequence_no: int
    speaker_id: str
    speaker_role: str
    speaker_side: str
    phase: str
    turn_type: str
    transcript_text: str
    audio_ref: Optional[str] = None
    transcription_source: str = "manual"
    metadata_json: str = "{}"
    created_at: datetime


class LiveScoreSnapshotEntity(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    sequence_no: int
    side_a_percent: int
    side_b_percent: int
    delta_a: int = 0
    delta_b: int = 0
    trend: str = "steady"
    confidence: float = 0.5
    reasoning_summary: str = ""
    is_provisional: bool = True
    updated_at: datetime


class ClaimEntity(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    speaker_side: str
    source_turn_id: str = Field(index=True)
    text: str
    claim_type: str
    confidence: float
    status: str


class EvidenceEntity(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    claim_id: str = Field(index=True)
    stance: str
    summary: str
    source_type: str
    relevance_score: float
    credibility_score: float
    notes: str


class ScorecardEntity(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True, unique=True)
    participant_a_json: str
    participant_b_json: str
    winner: str
    confidence: float
    judge_summary: str
    rubric_version: str = "v1"


class VerdictEntity(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True, unique=True)
    winner: str
    summary: str
    strengths_json: str = "[]"
    weaknesses_json: str = "[]"
    deciding_factors_json: str = "[]"
    audit_notes_json: str = "[]"


class SessionEventEntity(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    event_type: str
    from_phase: str
    to_phase: str
    payload_json: str = "{}"
    created_at: datetime
