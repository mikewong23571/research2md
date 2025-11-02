"""Markdown generation utilities."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from ..analysis.models import AnalysisStructure


@dataclass
class MarkdownArtifact:
    path: Path
    metadata: Dict[str, str]


class MarkdownGenerator:
    """Create Markdown documents from an analysis structure."""

    def generate(self, structure: AnalysisStructure, pdf_path: Path, output_path: Path) -> MarkdownArtifact:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines: List[str] = ["# TermDive Research Summary", f"_Source: {pdf_path.name}_", ""]
        for section in structure.sections:
            heading = "#" * max(1, section.level)
            lines.append(f"{heading} {section.title}")
            lines.append(section.summary)
            if section.entities:
                lines.append("\n**Entities:** " + ", ".join(section.entities))
            lines.append("")

        document = "\n".join(lines).strip() + "\n"
        output_path.write_text(document, encoding="utf-8")
        return MarkdownArtifact(path=output_path, metadata={"source_pdf": pdf_path.name})
