from enum import Enum


class DebatePhase(str, Enum):
    INIT = "INIT"
    TOPIC_LOCK = "TOPIC_LOCK"
    STANCE_CAPTURE = "STANCE_CAPTURE"
    LIVE_CAPTURE = "LIVE_CAPTURE"
    TRANSCRIPT_FINALIZED = "TRANSCRIPT_FINALIZED"
    CLAIM_EXTRACTION = "CLAIM_EXTRACTION"
    FACT_CHECK = "FACT_CHECK"
    SCORING = "SCORING"
    VERDICT = "VERDICT"
    AUDIT = "AUDIT"


class DebateStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    COMPLETED = "completed"


class CaptureStatus(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    ENDED = "ended"
    PROCESSING = "processing"
    COMPLETED = "completed"


class DebateSide(str, Enum):
    A = "A"
    B = "B"


class TurnType(str, Enum):
    UTTERANCE = "utterance"
    SYSTEM = "system"


class SpeakerRole(str, Enum):
    PARTICIPANT = "participant"
    SYSTEM = "system"
    AGENT = "agent"

