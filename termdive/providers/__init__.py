"""Provider factory helpers."""
from __future__ import annotations

from .base import ProviderAdapter
from .claude_agent_client import ClaudeAgentClient
from .gemini_adapter import GeminiAdapter
from .openai_adapter import OpenAIAdapter


def build_provider(name: str, *, model: str) -> ProviderAdapter:
    client = ClaudeAgentClient()
    adapter: ProviderAdapter
    if name.lower() == "openai":
        adapter = OpenAIAdapter(client=client, model=model)
    elif name.lower() == "gemini":
        adapter = GeminiAdapter(client=client, model=model)
    else:
        raise ValueError(f"Unsupported provider '{name}'")

    return adapter


__all__ = [
    "build_provider",
    "ClaudeAgentClient",
    "ProviderAdapter",
    "OpenAIAdapter",
    "GeminiAdapter",
]
