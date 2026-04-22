from functools import lru_cache

from app.agents.claim_extractor import ClaimExtractorAgent
from app.agents.evidence import EvidenceAgent
from app.agents.judge import JudgeAgent
from app.agents.moderator import ModeratorAgent
from app.agents.verdict_composer import VerdictComposer
from app.orchestrator.debate_orchestrator import DebateOrchestrator
from app.orchestrator.state_machine import DebateStateMachine
from app.repositories.memory import InMemoryDebateRepository
from app.services.live_score import LiveScoreService
from app.services.reasoning import NvidiaNIMReasoningProvider
from app.services.transcription import GeminiTranscriptionProvider

try:
    from app.db.session import create_db_engine, create_session_factory, init_db
    from app.repositories.sql import SQLDebateRepository

    SQL_BACKEND_AVAILABLE = True
except ImportError:
    SQL_BACKEND_AVAILABLE = False


@lru_cache
def get_orchestrator() -> DebateOrchestrator:
    reasoning_provider = NvidiaNIMReasoningProvider()
    repository = InMemoryDebateRepository()
    if SQL_BACKEND_AVAILABLE:
        engine = create_db_engine()
        init_db(engine)
        session_factory = create_session_factory(engine)
        repository = SQLDebateRepository(session_factory=session_factory)

    return DebateOrchestrator(
        repository=repository,
        state_machine=DebateStateMachine(),
        live_score_service=LiveScoreService(reasoning_provider=reasoning_provider),
        transcription_provider=GeminiTranscriptionProvider(),
        moderator_agent=ModeratorAgent(),
        claim_extractor_agent=ClaimExtractorAgent(reasoning_provider=reasoning_provider),
        evidence_agent=EvidenceAgent(reasoning_provider=reasoning_provider),
        judge_agent=JudgeAgent(reasoning_provider=reasoning_provider),
        verdict_composer=VerdictComposer(reasoning_provider=reasoning_provider),
    )
