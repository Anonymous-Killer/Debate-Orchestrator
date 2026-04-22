from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.deps import get_orchestrator
from app.api.routes import router


app = FastAPI(title="Debate Orchestrator", version="0.1.0")
app.include_router(router)
STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


@app.get("/", include_in_schema=False)
def local_ui() -> FileResponse:
    return FileResponse(STATIC_INDEX)


@app.on_event("startup")
def startup() -> None:
    get_orchestrator()
