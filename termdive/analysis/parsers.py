"""Simple parsing helpers for PDF text."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from .models import AnalysisSection


_SECTION_HEADER = re.compile(r"^#{1,3}\s*(?P<title>.+)$")


def _read_pdf_text(pdf_path: Path) -> str:
    """Read the PDF file as text. The generated PDF is plain text for the MVP."""

    try:
        return pdf_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return pdf_path.read_text(encoding="latin-1")


def extract_sections_from_pdf(pdf_path: Path) -> List[AnalysisSection]:
    """Parse sections from the exported PDF text."""

    content = _read_pdf_text(pdf_path)
    lines = [line.strip() for line in content.splitlines() if line.strip()]

    sections: List[AnalysisSection] = []
    current_title = "Overview"
    current_body: List[str] = []
    current_level = 2

    def flush() -> None:
        if current_body:
            summary = " ".join(current_body)
            entities = sorted({word for word in summary.split() if word.istitle()})
            sections.append(AnalysisSection(title=current_title, summary=summary, level=current_level, entities=entities))

    for line in lines:
        header_match = _SECTION_HEADER.match(line)
        if header_match:
            flush()
            current_body.clear()
            current_title = header_match.group("title").strip()
            current_level = line.count("#")
        else:
            current_body.append(line)

    flush()
    if not sections:
        sections.append(AnalysisSection(title="Overview", summary=" ".join(lines[:5]), level=1, entities=[]))

    return sections
