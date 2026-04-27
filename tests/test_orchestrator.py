from app.agents.claim_extractor import ClaimExtractorAgent
from app.agents.evidence import EvidenceAgent
from app.agents.judge import JudgeAgent
from app.agents.moderator import ModeratorAgent
from app.agents.verdict_composer import VerdictComposer
from app.core.enums import DebatePhase, DebateSide
from app.core.exceptions import InvalidDebateAction
from app.orchestrator.debate_orchestrator import DebateOrchestrator
from app.orchestrator.state_machine import DebateStateMachine
from app.repositories.memory import InMemoryDebateRepository
from app.schemas.debate import CreateDebateRequest, StartDebateRequest, UtteranceCreate
from app.services.live_score import LiveScoreService
from app.services.reasoning import NvidiaNIMReasoningProvider
from app.services.transcription import GeminiTranscriptionProvider, TranscriptionResult


class FakeNIMReasoningProvider:
    available = True

    def __init__(self, response=None, error=None):
        self.response = response or {}
        self.error = error
        self.last_prompt = ""

    def complete_json(self, system_prompt, user_payload):
        self.last_prompt = system_prompt
        if self.error:
            raise self.error
        return self.response


class FakeGeminiTranscriptionProvider(GeminiTranscriptionProvider):
    def transcribe(self, payload: UtteranceCreate) -> TranscriptionResult:
        if payload.transcript_text:
            return TranscriptionResult(
                transcript_text=payload.transcript_text,
                source="provided_text",
                provider="client",
            )
        return TranscriptionResult(
            transcript_text="Transcribed audio argument from Gemini.",
            source="fake_audio",
            provider="gemini",
        )


def build_orchestrator() -> DebateOrchestrator:
    reasoning_provider = NvidiaNIMReasoningProvider(api_key="")
    return build_orchestrator_with_reasoning(reasoning_provider)


def build_orchestrator_with_reasoning(reasoning_provider) -> DebateOrchestrator:
    return DebateOrchestrator(
        repository=InMemoryDebateRepository(),
        state_machine=DebateStateMachine(),
        live_score_service=LiveScoreService(reasoning_provider=reasoning_provider),
        transcription_provider=FakeGeminiTranscriptionProvider(api_key="test"),
        moderator_agent=ModeratorAgent(),
        claim_extractor_agent=ClaimExtractorAgent(reasoning_provider=reasoning_provider),
        evidence_agent=EvidenceAgent(reasoning_provider=reasoning_provider),
        judge_agent=JudgeAgent(reasoning_provider=reasoning_provider),
        verdict_composer=VerdictComposer(reasoning_provider=reasoning_provider),
    )


def test_full_voice_debate_flow():
    orchestrator = build_orchestrator()
    created = orchestrator.create_debate(
        CreateDebateRequest(
            topic="Should social platforms be regulated?",
            participant_a_id="alice",
            participant_b_id="bob",
        )
    )
    session_id = created.id

    started = orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.A),
    )
    assert started.current_phase == DebatePhase.LIVE_CAPTURE

    first = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(transcript_text="Platforms should be regulated because algorithms shape public opinion."),
    )
    assert first.live_score.side_a_percent > 50

    switched = orchestrator.switch_side(session_id, DebateSide.B)
    assert switched.active_side == DebateSide.B

    second = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(transcript_text="Regulation can chill speech, and the data does not justify broad intervention."),
    )
    assert second.live_score.side_a_percent + second.live_score.side_b_percent == 100

    ended = orchestrator.end_debate(session_id)
    assert ended.verdict_available is True
    assert ended.current_phase == DebatePhase.AUDIT

    verdict = orchestrator.get_verdict(session_id)
    assert verdict is not None
    assert verdict.winner in {DebateSide.A, DebateSide.B}


def test_rejects_utterance_after_end():
    orchestrator = build_orchestrator()
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Topic", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id

    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Pro", stance_b="Con", active_side=DebateSide.A),
    )
    orchestrator.ingest_utterance(session_id, UtteranceCreate(transcript_text="First point because it matters."))
    orchestrator.switch_side(session_id, DebateSide.B)
    orchestrator.ingest_utterance(session_id, UtteranceCreate(transcript_text="Counterpoint because freedom matters."))
    orchestrator.end_debate(session_id)

    try:
        orchestrator.ingest_utterance(session_id, UtteranceCreate(transcript_text="This should not be accepted."))
    except InvalidDebateAction:
        assert True
    else:
        assert False, "Expected utterance ingestion to be rejected after the debate ends"


def test_audio_payload_uses_transcription_provider():
    orchestrator = build_orchestrator()
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Audio Topic", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Pro", stance_b="Con", active_side=DebateSide.A),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(audio_base64="ZmFrZWF1ZGlv"),
    )

    assert response.accepted is True
    assert response.transcription_source == "gemini"
    assert response.transcript_text == "Transcribed audio argument from Gemini."


def test_live_score_allows_large_but_capped_swings_for_emotional_points():
    orchestrator = build_orchestrator()
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Public policy", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Pro", stance_b="Con", active_side=DebateSide.A),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(
            transcript_text=(
                "This is about compassion and justice because real families are suffering, "
                "children face direct harm, and ignoring that human cost is morally indefensible."
            )
        ),
    )

    assert response.live_score.side_a_percent >= 65
    assert response.live_score.side_b_percent <= 35
    assert response.live_score.side_a_percent <= 90


def test_live_score_penalizes_points_that_conflict_with_side_stance():
    orchestrator = build_orchestrator()
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Algorithm regulation", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.B),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(
            transcript_text=(
                "We should regulate these systems because they protect children, improve safety, "
                "and are necessary to prevent harm."
            )
        ),
    )

    assert response.live_score.side_a_percent > 50
    assert "stated stance" in response.live_score.reasoning_summary


def test_live_score_penalizes_ethically_toxic_argument_even_if_stance_aligned():
    orchestrator = build_orchestrator()
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Should abortion be legal?", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.A),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(
            transcript_text="If a child is a girl, then we can just abort until a boy is born."
        ),
    )

    assert response.live_score.side_a_percent < 50
    assert "crowd backlash" in response.live_score.reasoning_summary


def test_live_score_penalizes_professional_sounding_discriminatory_argument():
    orchestrator = build_orchestrator()
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Should abortion be legal?", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.A),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(
            transcript_text="It should be legal to let us abort any female babies and keep only male ones."
        ),
    )

    assert response.live_score.side_a_percent < 50
    assert "crowd backlash" in response.live_score.reasoning_summary


def test_live_score_penalizes_existence_denial_discriminatory_argument():
    orchestrator = build_orchestrator()
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Should abortion be legal?", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.A),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(
            transcript_text="It should be legal so that we can make sure no girl child is born."
        ),
    )

    assert response.live_score.side_a_percent < 50
    assert "crowd backlash" in response.live_score.reasoning_summary


def test_live_score_penalizes_religious_exclusion_argument():
    orchestrator = build_orchestrator()
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Immigration policy", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.A),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(
            transcript_text="We should exclude muslim immigrants because of religion and keep them out."
        ),
    )

    assert response.live_score.side_a_percent < 50
    assert "crowd backlash" in response.live_score.reasoning_summary


def test_live_score_penalizes_financial_status_discrimination_argument():
    orchestrator = build_orchestrator()
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Housing policy", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.A),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(
            transcript_text="Poor families should be excluded from these neighborhoods because of income."
        ),
    )

    assert response.live_score.side_a_percent < 50
    assert "crowd backlash" in response.live_score.reasoning_summary


def test_live_score_treats_unpredictable_not_beneficial_replacement_argument_as_no_aligned():
    orchestrator = build_orchestrator()
    created = orchestrator.create_debate(
        CreateDebateRequest(
            topic="Should wars be replaced by 1vs1 duels?",
            participant_a_id="a",
            participant_b_id="b",
        )
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.B),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(
            transcript_text="Replacing war will mean a new system which is not predictable and not beneficial for us."
        ),
    )

    assert response.live_score.side_b_percent > 50
    assert "stated stance" not in response.live_score.reasoning_summary


def test_nim_scoring_gates_filler_argument_even_if_model_returns_score_increase():
    reasoning_provider = FakeNIMReasoningProvider(
        response={
            "side_a_percent": 60,
            "side_b_percent": 40,
            "delta_a": 10,
            "delta_b": -10,
            "trend": "A_up",
            "confidence": 0.8,
            "reasoning_summary": "Bad model response that incorrectly rewards filler.",
            "topic_relevance": 0.05,
            "argument_quality": 0.05,
            "score_change_allowed": False,
            "scoring_source": "nim",
        }
    )
    orchestrator = build_orchestrator_with_reasoning(reasoning_provider)
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Should school uniforms be mandatory?", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.A),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(transcript_text="Hello, hello, hello, hello."),
    )

    assert response.live_score.side_a_percent < 50
    assert response.live_score.score_change_allowed is False
    assert response.live_score.scoring_source == "nim_gated"
    assert "not sufficiently relevant" in response.live_score.reasoning_summary
    assert "topic_relevance" in reasoning_provider.last_prompt
    assert "argument_quality" in reasoning_provider.last_prompt
    assert "score_change_allowed" in reasoning_provider.last_prompt


def test_nim_scoring_accepts_fractional_percentages_before_gating():
    reasoning_provider = FakeNIMReasoningProvider(
        response={
            "side_a_percent": 49.5,
            "side_b_percent": 50.5,
            "delta_a": -0.5,
            "delta_b": 0.5,
            "trend": "B_up",
            "confidence": 0.7,
            "reasoning_summary": "Filler should not move the score up.",
            "topic_relevance": 0.05,
            "argument_quality": 0.05,
            "score_change_allowed": False,
            "scoring_source": "nim",
        }
    )
    orchestrator = build_orchestrator_with_reasoning(reasoning_provider)
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Should school uniforms be mandatory?", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.A),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(transcript_text="Hello, hello, hello, hello."),
    )

    assert response.live_score.side_a_percent == 48
    assert response.live_score.side_b_percent == 52
    assert response.live_score.scoring_source == "nim_gated"


def test_nim_scoring_is_overridden_for_ethically_toxic_point():
    reasoning_provider = FakeNIMReasoningProvider(
        response={
            "side_a_percent": 60,
            "side_b_percent": 40,
            "delta_a": 10,
            "delta_b": -10,
            "trend": "A_up",
            "confidence": 0.7,
            "reasoning_summary": "Incorrectly rewarding an unethical point.",
            "topic_relevance": 0.9,
            "argument_quality": 0.8,
            "score_change_allowed": True,
            "scoring_source": "nim",
        }
    )
    orchestrator = build_orchestrator_with_reasoning(reasoning_provider)
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Should abortion be legal?", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.A),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(transcript_text="Abortion should be made legal so that we can avoid having the birth of any girl."),
    )

    assert response.live_score.side_a_percent < 50
    assert response.live_score.score_change_allowed is False
    assert response.live_score.scoring_source == "nim_overridden_crowd_backlash"
    assert "overridden" in response.live_score.reasoning_summary


def test_financial_readiness_abortion_argument_is_not_locally_overridden_as_discriminatory():
    reasoning_provider = FakeNIMReasoningProvider(
        response={
            "side_a_percent": 56,
            "side_b_percent": 44,
            "delta_a": 6,
            "delta_b": -6,
            "trend": "A_up",
            "confidence": 0.75,
            "reasoning_summary": "The point is relevant and supports the stated stance.",
            "topic_relevance": 0.9,
            "argument_quality": 0.7,
            "score_change_allowed": True,
            "scoring_source": "nim",
        }
    )
    orchestrator = build_orchestrator_with_reasoning(reasoning_provider)
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Should abortion be legal?", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.A),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(
            transcript_text=(
                "Yes abortion should be legal as some parents are not financially ready "
                "or mentally ready to have a child."
            )
        ),
    )

    assert response.live_score.scoring_source == "nim"
    assert response.live_score.side_a_percent == 56


def test_nim_scoring_is_overridden_for_socially_frowned_devaluation_point():
    reasoning_provider = FakeNIMReasoningProvider(
        response={
            "side_a_percent": 60,
            "side_b_percent": 40,
            "delta_a": 10,
            "delta_b": -10,
            "trend": "A_up",
            "confidence": 0.7,
            "reasoning_summary": "Incorrectly rewarding a socially toxic point.",
            "topic_relevance": 0.9,
            "argument_quality": 0.8,
            "score_change_allowed": True,
            "scoring_source": "nim",
        }
    )
    orchestrator = build_orchestrator_with_reasoning(reasoning_provider)
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Should abortion be legal?", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.A),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(
            transcript_text=(
                "Yes, abortion should be legal as some children are just unwanted and if we somehow "
                "get a girl who's about to be born, that's something we want to avoid."
            )
        ),
    )

    assert response.live_score.side_a_percent < 50
    assert response.live_score.scoring_source == "nim_overridden_crowd_backlash"


def test_nim_failure_is_visible_in_live_score_reasoning():
    reasoning_provider = FakeNIMReasoningProvider(error=RuntimeError("NIM exploded"))
    orchestrator = build_orchestrator_with_reasoning(reasoning_provider)
    created = orchestrator.create_debate(
        CreateDebateRequest(topic="Should school uniforms be mandatory?", participant_a_id="a", participant_b_id="b")
    )
    session_id = created.id
    orchestrator.start_debate(
        session_id,
        StartDebateRequest(stance_a="Yes", stance_b="No", active_side=DebateSide.A),
    )

    response = orchestrator.ingest_utterance(
        session_id,
        UtteranceCreate(transcript_text="Uniforms help students focus because they reduce distractions."),
    )

    assert response.live_score.side_a_percent == 50
    assert response.live_score.side_b_percent == 50
    assert response.live_score.delta_a == 0
    assert response.live_score.scoring_source == "nim_failed_preserved"
    assert "NIM live scoring failed after retries" in response.live_score.reasoning_summary
    assert "NIM exploded" in response.live_score.reasoning_summary
