from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import get_orchestrator
from app.api.routes import router
from app.core.config import settings


app = FastAPI(title="Debate Orchestrator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/", include_in_schema=False)
def api_root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "ok",
        "docs": "/docs",
    }


@app.on_event("startup")
def startup() -> None:
    get_orchestrator()
