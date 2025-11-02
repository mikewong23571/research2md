"""Pipeline orchestration for TermDive."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from ..analysis.analyzer_agent import AnalyzerAgent, AnalysisStructure
from ..artifacts.manifest import ArtifactManifest
from ..config import AppConfig
from ..export.pdf_exporter import PDFExporter, PDFArtifact
from ..markdown.generator import MarkdownGenerator, MarkdownArtifact
from ..markdown.markitdown_extractor import MarkItDownExtractor
from ..providers.base import PromptRequest, ProviderAdapter

logger = logging.getLogger(__name__)


@dataclass
class RunSummary:
    run_id: str
    artifacts: Dict[str, Path]


class RunManager:
    """Coordinates provider calls, exports, analysis, and markdown generation."""

    def __init__(
        self,
        *,
        config: AppConfig,
        provider: ProviderAdapter,
        pdf_exporter: PDFExporter,
        analyzer: AnalyzerAgent,
        markdown_generator: MarkdownGenerator,
        artifact_manifest: ArtifactManifest,
        markitdown_extractor: Optional[MarkItDownExtractor] = None,
    ) -> None:
        self.config = config
        self.provider = provider
        self.pdf_exporter = pdf_exporter
        self.analyzer = analyzer
        self.markdown_generator = markdown_generator
        self.manifest = artifact_manifest
        self.markitdown_extractor = markitdown_extractor

    def run(self, term: str, *, prompt_text: str, run_id: str) -> RunSummary:
        logger.info("Starting run", extra={"run_id": run_id, "term": term})

        prompt_request = PromptRequest(
            prompt_name="deep_search_v1",
            text=prompt_text,
            run_id=run_id,
            version=self.config.prompt_version,
        )
        provider_response = self.provider.call(prompt_request)
        logger.info("Provider call complete", extra={"run_id": run_id, "provider": self.config.provider})

        artifacts: Dict[str, Path] = {}

        responses_dir = self.manifest.ensure_directory("responses")
        response_path = responses_dir / "deep_search.json"
        response_path.write_text(json.dumps(provider_response.raw, indent=2), encoding="utf-8")
        self.manifest.record("provider_response", response_path, metadata=provider_response.metadata)
        artifacts["provider_response"] = response_path

        pdf_artifact: Optional[PDFArtifact] = None
        if self.config.pdf:
            pdf_dir = self.manifest.ensure_directory("pdf")
            pdf_artifact = self.pdf_exporter.export(provider_response, pdf_dir / "deep_search.pdf")
            self.manifest.record("pdf", pdf_artifact.path, metadata=pdf_artifact.metadata)
            artifacts["pdf"] = pdf_artifact.path

        analysis_structure: Optional[AnalysisStructure] = None
        if self.config.markdown and pdf_artifact is not None:
            analysis_dir = self.manifest.ensure_directory("analysis")
            analysis_structure = self.analyzer.analyze(pdf_artifact.path)
            analysis_path = analysis_dir / "structure.json"
            analysis_path.write_text(
                json.dumps(analysis_structure.to_dict(), indent=2),
                encoding="utf-8",
            )
            self.manifest.record("analysis", analysis_path, metadata={"provider": self.config.analysis_provider})
            artifacts["analysis"] = analysis_path

            markdown_dir = self.manifest.ensure_directory("markdown")
            markdown_artifact = self.markdown_generator.generate(
                analysis_structure,
                pdf_artifact.path,
                markdown_dir / "deep_search.md",
            )
            self.manifest.record("markdown", markdown_artifact.path, metadata=markdown_artifact.metadata)
            artifacts["markdown"] = markdown_artifact.path

            if self.config.use_markitdown and self.markitdown_extractor is not None:
                markitdown_path = markdown_dir / "deep_search_markitdown.md"
                extracted = self.markitdown_extractor.extract(pdf_artifact.path)
                markitdown_path.write_text(extracted, encoding="utf-8")
                self.manifest.record("markitdown", markitdown_path, metadata={"source": "markitdown"})
                artifacts["markitdown"] = markitdown_path

        self.manifest.finalize()

        logger.info(
            "Run complete",
            extra={
                "run_id": run_id,
                "artifacts": {name: str(path) for name, path in artifacts.items()},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        return RunSummary(run_id=run_id, artifacts=artifacts)
