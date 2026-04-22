from __future__ import annotations

from typing import Optional

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import InvalidDebateAction
from app.schemas.debate import UtteranceCreate


class TranscriptionResult(BaseModel):
    transcript_text: str
    source: str
    provider: str


class TranscriptionProvider:
    def transcribe(self, payload: UtteranceCreate) -> TranscriptionResult:
        raise NotImplementedError


class GeminiTranscriptionProvider(TranscriptionProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_base: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.api_base = api_base or settings.gemini_api_base

    def transcribe(self, payload: UtteranceCreate) -> TranscriptionResult:
        if payload.transcript_text:
            return TranscriptionResult(
                transcript_text=payload.transcript_text,
                source="provided_text",
                provider="client",
            )

        if not self.api_key:
            raise InvalidDebateAction(
                "Gemini transcription requires GEMINI_API_KEY when transcript_text is not provided."
            )

        if payload.audio_base64:
            transcript = self._transcribe_audio_inline(payload.audio_base64)
            return TranscriptionResult(
                transcript_text=transcript,
                source="gemini_audio_base64",
                provider="gemini",
            )

        if payload.audio_ref:
            # The backend stores the reference but does not fetch arbitrary files in v1.
            raise InvalidDebateAction(
                "audio_ref-only transcription is not supported yet. Provide audio_base64 or transcript_text."
            )

        raise InvalidDebateAction("Unable to transcribe utterance payload.")

    def _transcribe_audio_inline(self, audio_base64: str) -> str:
        url = "{base}/v1beta/models/{model}:generateContent?key={key}".format(
            base=self.api_base.rstrip("/"),
            model=self.model,
            key=self.api_key,
        )
        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "Transcribe this debate audio into plain text only. "
                                "Return only the transcript with no commentary."
                            )
                        },
                        {
                            "inline_data": {
                                "mime_type": "audio/webm",
                                "data": audio_base64,
                            }
                        },
                    ]
                }
            ]
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=body)
            response.raise_for_status()
            data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise InvalidDebateAction("Gemini returned no transcription candidates.")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = " ".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise InvalidDebateAction("Gemini returned an empty transcript.")
        return text

