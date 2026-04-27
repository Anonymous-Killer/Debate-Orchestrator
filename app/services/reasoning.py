from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from app.core.config import settings


class ReasoningProvider:
    def complete_json(self, system_prompt: str, user_payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class NvidiaNIMReasoningProvider(ReasoningProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_base: Optional[str] = None,
    ) -> None:
        self.api_key = settings.nim_api_key if api_key is None else api_key
        self.model = settings.nim_model if model is None else model
        self.api_base = settings.nim_api_base if api_base is None else api_base

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def complete_json(self, system_prompt: str, user_payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError("NVIDIA NIM API key is not configured.")

        url = "{base}/v1/chat/completions".format(base=self.api_base.rstrip("/"))
        body = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "Return strict JSON only.\n"
                        + self._json_dump(user_payload)
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": "Bearer {key}".format(key=self.api_key),
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=settings.nim_timeout_seconds) as client:
            response = client.post(url, json=body, headers=headers)
            if response.is_error:
                raise RuntimeError(
                    "NVIDIA NIM request failed with status "
                    f"{response.status_code}: {response.text}"
                )
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        return httpx.Response(200, content=content).json()

    @staticmethod
    def _json_dump(payload: Dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=True, default=_json_default)


def _json_default(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class FallbackReasoningProvider(ReasoningProvider):
    def complete_json(self, system_prompt: str, user_payload: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError("Fallback provider should not be called directly.")
