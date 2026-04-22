from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

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
        self.api_key = api_key or settings.nim_api_key
        self.model = model or settings.nim_model
        self.api_base = api_base or settings.nim_api_base

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
        with httpx.Client(timeout=45.0) as client:
            response = client.post(url, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        return httpx.Response(200, content=content).json()

    @staticmethod
    def _json_dump(payload: Dict[str, Any]) -> str:
        import json

        return json.dumps(payload, ensure_ascii=True)


class FallbackReasoningProvider(ReasoningProvider):
    def complete_json(self, system_prompt: str, user_payload: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError("Fallback provider should not be called directly.")
