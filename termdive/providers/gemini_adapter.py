"""Gemini provider adapter."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from .base import PromptRequest, ProviderAdapter, ProviderResponse
from .claude_agent_client import ClaudeAgentClient


class GeminiAdapter(ProviderAdapter):
    """Adapter that proxies through the Claude Agent stub for determinism."""

    def __init__(self, *, client: ClaudeAgentClient, model: str) -> None:
        self._client = client
        self._model = model
        self._last_metadata: Dict[str, str] = {}

    def call(self, request: PromptRequest) -> ProviderResponse:
        metadata = {
            "run_id": request.run_id,
            "prompt_version": request.version,
            "prompt_name": request.prompt_name,
            "term": request.text.split("\n", 1)[0].split(":")[-1].strip() if ":" in request.text else request.text[:50],
        }
        response = self._client.execute(
            provider_name="gemini",
            model=self._model,
            request={"prompt": request.text},
            metadata=metadata,
        )
        self._last_metadata = {**metadata, "tokens": str(response.usage)}
        return ProviderResponse(
            text=response.text,
            raw=response.raw_json,
            model=self._model,
            created_at=datetime.now(timezone.utc),
            metadata=self._last_metadata,
        )

    def get_metadata(self) -> Dict[str, str]:
        return dict(self._last_metadata)
