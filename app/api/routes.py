from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_orchestrator
from app.core.exceptions import DebateError, DebateNotFound
from app.orchestrator.debate_orchestrator import DebateOrchestrator
from app.schemas.debate import (
    CreateDebateRequest,
    DebateSummaryResponse,
    EndDebateResponse,
    LiveScore,
    StartDebateRequest,
    StartDebateResponse,
    SwitchSideRequest,
    TranscriptResponse,
    UtteranceCreate,
    UtteranceResponse,
    VerdictRecord,
)


router = APIRouter()


def _map_error(error: DebateError) -> HTTPException:
    if isinstance(error, DebateNotFound):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@router.post("/debates", response_model=DebateSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_debate(
    request: CreateDebateRequest,
    orchestrator: DebateOrchestrator = Depends(get_orchestrator),
) -> DebateSummaryResponse:
    return orchestrator.create_debate(request)


@router.post("/debates/{session_id}/start", response_model=StartDebateResponse)
def start_debate(
    session_id: str,
    request: StartDebateRequest,
    orchestrator: DebateOrchestrator = Depends(get_orchestrator),
) -> StartDebateResponse:
    try:
        return orchestrator.start_debate(session_id, request)
    except DebateError as error:
        raise _map_error(error) from error


@router.post("/debates/{session_id}/utterance", response_model=UtteranceResponse)
def ingest_utterance(
    session_id: str,
    request: UtteranceCreate,
    orchestrator: DebateOrchestrator = Depends(get_orchestrator),
) -> UtteranceResponse:
    try:
        return orchestrator.ingest_utterance(session_id, request)
    except DebateError as error:
        raise _map_error(error) from error


@router.post("/debates/{session_id}/switch-side", response_model=DebateSummaryResponse)
def switch_side(
    session_id: str,
    request: SwitchSideRequest,
    orchestrator: DebateOrchestrator = Depends(get_orchestrator),
) -> DebateSummaryResponse:
    try:
        return orchestrator.switch_side(session_id, request.next_side)
    except DebateError as error:
        raise _map_error(error) from error


@router.post("/debates/{session_id}/end", response_model=EndDebateResponse)
def end_debate(
    session_id: str,
    orchestrator: DebateOrchestrator = Depends(get_orchestrator),
) -> EndDebateResponse:
    try:
        return orchestrator.end_debate(session_id)
    except DebateError as error:
        raise _map_error(error) from error


@router.get("/debates/{session_id}", response_model=DebateSummaryResponse)
def get_debate(
    session_id: str,
    orchestrator: DebateOrchestrator = Depends(get_orchestrator),
) -> DebateSummaryResponse:
    try:
        return orchestrator.get_debate(session_id)
    except DebateError as error:
        raise _map_error(error) from error


@router.get("/debates/{session_id}/transcript", response_model=TranscriptResponse)
def get_transcript(
    session_id: str,
    orchestrator: DebateOrchestrator = Depends(get_orchestrator),
) -> TranscriptResponse:
    try:
        return orchestrator.get_transcript(session_id)
    except DebateError as error:
        raise _map_error(error) from error


@router.get("/debates/{session_id}/live-score", response_model=LiveScore)
def get_live_score(
    session_id: str,
    orchestrator: DebateOrchestrator = Depends(get_orchestrator),
) -> LiveScore:
    try:
        return orchestrator.get_live_score(session_id)
    except DebateError as error:
        raise _map_error(error) from error


@router.post("/debates/{session_id}/verdict", response_model=VerdictRecord)
def get_verdict(
    session_id: str,
    orchestrator: DebateOrchestrator = Depends(get_orchestrator),
) -> VerdictRecord:
    try:
        return orchestrator.get_verdict(session_id)
    except DebateError as error:
        raise _map_error(error) from error

