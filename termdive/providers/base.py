"""Provider abstractions for TermDive."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Protocol


@dataclass
class PromptRequest:
    """A request rendered from a prompt template."""

    prompt_name: str
    text: str
    run_id: str
    version: str


@dataclass
class ProviderResponse:
    """Normalized provider response payload."""

    text: str
    raw: Dict
    model: str
    created_at: datetime
    metadata: Dict[str, str]


class ProviderAdapter(Protocol):
    """Adapter interface for LLM providers."""

    def call(self, request: PromptRequest) -> ProviderResponse:
        raise NotImplementedError

    def get_metadata(self) -> Dict[str, str]:
        raise NotImplementedError


class ProviderError(RuntimeError):
    """Raised when a provider call fails."""


class ProviderFactory:
    """Instantiate provider adapters by name."""

    _registry: Dict[str, ProviderAdapter] = {}

    @classmethod
    def register(cls, name: str, adapter: ProviderAdapter) -> None:
        cls._registry[name.lower()] = adapter

    @classmethod
    def get(cls, name: str) -> ProviderAdapter:
        try:
            return cls._registry[name.lower()]
        except KeyError as exc:
            raise ProviderError(f"Unknown provider '{name}'. Registered providers: {list(cls._registry)}") from exc
