"""Data models for analysis results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class AnalysisSection:
    title: str
    summary: str
    level: int
    entities: List[str] = field(default_factory=list)


@dataclass
class AnalysisStructure:
    sections: List[AnalysisSection]

    def to_dict(self) -> Dict:
        return {
            "sections": [
                {
                    "title": section.title,
                    "summary": section.summary,
                    "level": section.level,
                    "entities": section.entities,
                }
                for section in self.sections
            ]
        }
