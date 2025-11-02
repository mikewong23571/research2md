"""CLI entrypoint for TermDive."""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from typing import Dict

from .analysis.analyzer_agent import AnalyzerAgent
from .artifacts.manifest import ArtifactManifest
from .config import load_config
from .logging import configure_logging
from .markdown.generator import MarkdownGenerator
from .markdown.markitdown_extractor import MarkItDownExtractor
from .pipeline.run_manager import RunManager
from .prompts import load_prompt
from .providers import build_provider
from .export.pdf_exporter import PDFExporter


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the TermDive research pipeline")
    parser.add_argument("term", help="Term to research")
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--no-pdf", dest="pdf", action="store_false", help="Disable PDF export")
    parser.add_argument("--no-md", dest="markdown", action="store_false", help="Disable Markdown generation")
    parser.add_argument("--use-markitdown", action="store_true")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--prompt-version", default=None)
    parser.add_argument("--analysis-provider", default=None)
    parser.set_defaults(pdf=None, markdown=None)
    return parser


def _generate_run_id(term: str) -> str:
    slug = "".join(ch for ch in term.lower().replace(" ", "-") if ch.isalnum() or ch == "-")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{timestamp}-{slug or 'run'}"


def _render_prompt(term: str, *, run_id: str, version: str) -> str:
    template = load_prompt("deep_search_v1")
    return template.format(term=term, run_id=run_id, version=version)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    cli_overrides: Dict[str, object] = {
        key: getattr(args, key)
        for key in [
            "provider",
            "model",
            "pdf",
            "markdown",
            "use_markitdown",
            "output_dir",
            "prompt_version",
            "analysis_provider",
        ]
        if getattr(args, key) is not None
    }
    config = load_config(cli_overrides)

    run_id = _generate_run_id(args.term)
    configure_logging(run_id=run_id)
    logging.getLogger(__name__).info("Loaded configuration", extra={"config": config.to_dict()})

    provider = build_provider(config.provider, model=config.model)
    pdf_exporter = PDFExporter()
    analyzer = AnalyzerAgent()
    markdown_generator = MarkdownGenerator()
    markitdown_extractor = MarkItDownExtractor() if config.use_markitdown else None

    artifact_root = config.output_dir
    artifact_manifest = ArtifactManifest.create(artifact_root, run_id)

    manager = RunManager(
        config=config,
        provider=provider,
        pdf_exporter=pdf_exporter,
        analyzer=analyzer,
        markdown_generator=markdown_generator,
        artifact_manifest=artifact_manifest,
        markitdown_extractor=markitdown_extractor,
    )

    prompt = _render_prompt(args.term, run_id=run_id, version=config.prompt_version)
    summary = manager.run(args.term, prompt_text=prompt, run_id=run_id)

    print(f"Run complete. Run ID: {summary.run_id}")
    for name, path in summary.artifacts.items():
        print(f" - {name}: {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
