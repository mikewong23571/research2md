"""Configuration utilities for TermDive."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_OUTPUT_DIR = Path("artifacts")


@dataclass
class AppConfig:
    """Resolved configuration for a TermDive run."""

    provider: str = "openai"
    model: str = "gpt-4o-mini"
    pdf: bool = True
    markdown: bool = True
    use_markitdown: bool = False
    output_dir: Path = DEFAULT_OUTPUT_DIR
    prompt_version: str = "v1"
    analysis_provider: str = "openai"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "pdf": self.pdf,
            "markdown": self.markdown,
            "use_markitdown": self.use_markitdown,
            "output_dir": str(self.output_dir),
            "prompt_version": self.prompt_version,
            "analysis_provider": self.analysis_provider,
        }


def _bool_from_env(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    value = value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


def load_config(cli_overrides: Optional[Dict[str, Any]] = None) -> AppConfig:
    """Load configuration using environment variables and CLI overrides."""

    cli_overrides = cli_overrides or {}
    env = os.environ

    provider = cli_overrides.get("provider") or env.get("TERMDIVE_DEFAULT_PROVIDER", "openai")
    model = cli_overrides.get("model") or env.get("TERMDIVE_DEFAULT_MODEL", "gpt-4o-mini")
    pdf = cli_overrides.get("pdf") if cli_overrides.get("pdf") is not None else _bool_from_env(
        env.get("TERMDIVE_ENABLE_PDF"), True
    )
    markdown = (
        cli_overrides.get("markdown")
        if cli_overrides.get("markdown") is not None
        else _bool_from_env(env.get("TERMDIVE_ENABLE_MD"), True)
    )
    use_markitdown = (
        cli_overrides.get("use_markitdown")
        if cli_overrides.get("use_markitdown") is not None
        else _bool_from_env(env.get("TERMDIVE_USE_MARKITDOWN"), False)
    )
    output_dir = Path(cli_overrides.get("output_dir") or env.get("TERMDIVE_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))
    prompt_version = cli_overrides.get("prompt_version") or env.get("TERMDIVE_PROMPT_VERSION", "v1")
    analysis_provider = cli_overrides.get("analysis_provider") or env.get("TERMDIVE_ANALYSIS_PROVIDER", provider)

    return AppConfig(
        provider=provider,
        model=model,
        pdf=pdf,
        markdown=markdown,
        use_markitdown=use_markitdown,
        output_dir=output_dir,
        prompt_version=prompt_version,
        analysis_provider=analysis_provider,
    )
