"""A very small stub emulating a Claude Agent SDK client."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict


@dataclass
class ClaudeResponse:
    text: str
    usage: Dict[str, int]
    raw_json: Dict


class ClaudeAgentClient:
    """A synchronous stub that echoes prompt text into a plausible response."""

    def execute(self, *, provider_name: str, model: str, request: Dict, metadata: Dict) -> ClaudeResponse:
        prompt_text: str = request["prompt"]
        summary = (
            f"Provider {provider_name} ({model}) researched '{metadata.get('term', 'unknown term')}'.\n"
            f"Prompt version: {metadata.get('prompt_version')}.\n\n"
            f"{prompt_text.strip()}"
        )
        usage = {"prompt_tokens": len(prompt_text.split()), "completion_tokens": len(summary.split())}
        raw = {
            "provider": provider_name,
            "model": model,
            "metadata": metadata,
            "request": request,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return ClaudeResponse(text=summary, usage=usage, raw_json=raw)
