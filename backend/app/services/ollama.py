from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import settings


class LocalModelError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds

    def is_ready(self) -> bool:
        try:
            with httpx.Client(timeout=3) as client:
                response = client.get(f"{self.base_url}/api/tags")
                if not response.is_success:
                    return False
                names = {str(item.get("name", "")) for item in response.json().get("models", [])}
                return self.model in names or any(name.startswith(f"{self.model}:") for name in names)
        except httpx.HTTPError:
            return False

    def chat_json(self, system: str, user: str, temperature: float = 0.2) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "think": False,
            "options": {"temperature": temperature},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise LocalModelError(f"Local model request failed: {exc}") from exc

        content = body.get("message", {}).get("content", "")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise LocalModelError("Local model returned invalid JSON") from exc


ollama = OllamaClient()
