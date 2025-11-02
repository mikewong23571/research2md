"""Fallback Markdown extractor mimicking markitdown behaviour."""
from __future__ import annotations

from pathlib import Path


class MarkItDownExtractor:
    """Return a naive Markdown view of the PDF text."""

    def extract(self, pdf_path: Path) -> str:
        text = pdf_path.read_text(encoding="utf-8")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        converted = []
        for line in lines:
            if line.startswith("TermDive Research Report"):
                converted.append(f"# {line}")
            else:
                converted.append(line)
        return "\n\n".join(converted) + "\n"
