from fastapi import FastAPI

from app.api.deps import get_orchestrator
from app.api.routes import router


app = FastAPI(title="Debate Orchestrator", version="0.1.0")
app.include_router(router)


@app.on_event("startup")
def startup() -> None:
    get_orchestrator()
