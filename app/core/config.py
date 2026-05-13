import os
from pathlib import Path

from pydantic import BaseModel
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseModel):
    app_name: str = "Debate Orchestrator"
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if origin.strip()
    ]
    live_score_max_delta: int = 18
    live_score_floor: int = 10
    live_score_ceiling: int = 90
    nim_live_score_retries: int = int(os.getenv("NIM_LIVE_SCORE_RETRIES", "2"))
    nim_timeout_seconds: float = float(os.getenv("NIM_TIMEOUT_SECONDS", "20"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./debate_orchestrator.db")
    database_echo: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_TRANSCRIBE_MODEL", "gemini-2.5-flash")
    gemini_api_base: str = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com")
    nim_api_key: str = os.getenv("NVIDIA_NIM_API_KEY", "")
    nim_model: str = os.getenv("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct")
    nim_api_base: str = os.getenv("NVIDIA_NIM_API_BASE", "https://integrate.api.nvidia.com")


settings = Settings()
