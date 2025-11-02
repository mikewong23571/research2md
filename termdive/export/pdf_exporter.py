"""PDF exporter for TermDive."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict

from ..providers.base import ProviderResponse


@dataclass
class PDFArtifact:
    path: Path
    metadata: Dict[str, str]


class PDFExporter:
    """Convert provider responses into simple PDF-like files."""

    def export(self, response: ProviderResponse, output_path: Path) -> PDFArtifact:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        header = [
            "TermDive Research Report",
            f"Model: {response.model}",
            f"Created: {response.created_at.isoformat()}",
        ]
        body = response.text.strip()
        content = "\n".join(["\n".join(header), "", body])
        output_path.write_text(content, encoding="utf-8")

        metadata = {
            "model": response.model,
            "created_at": response.created_at.isoformat(),
        }
        metadata.update(response.metadata)
        return PDFArtifact(path=output_path, metadata=metadata)
