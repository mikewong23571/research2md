"""Analyzer agent that extracts structure from generated PDFs."""
from __future__ import annotations

from pathlib import Path

from .models import AnalysisStructure
from .parsers import extract_sections_from_pdf


class AnalyzerAgent:
    """Deterministic analyzer that reads PDF text and produces a structure."""

    def analyze(self, pdf_path: Path) -> AnalysisStructure:
        sections = extract_sections_from_pdf(pdf_path)
        return AnalysisStructure(sections=sections)
