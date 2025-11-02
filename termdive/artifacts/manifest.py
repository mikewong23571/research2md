"""Artifact manifest utilities."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


@dataclass
class ManifestEntry:
    path: str
    metadata: Dict[str, str]
    created_at: str


@dataclass
class ArtifactManifest:
    root: Path
    entries: Dict[str, ManifestEntry] = field(default_factory=dict)

    def ensure_directory(self, name: str) -> Path:
        directory = self.root / name
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def record(self, name: str, path: Path, *, metadata: Dict[str, str]) -> None:
        logger.debug("Recording artifact", extra={"name": name, "path": str(path)})
        self.entries[name] = ManifestEntry(
            path=str(path.relative_to(self.root.parent)),
            metadata=metadata,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def finalize(self) -> None:
        manifest_path = self.root / "manifest.json"
        payload = {
            "root": str(self.root),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entries": {name: entry.__dict__ for name, entry in self.entries.items()},
        }
        manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def create(cls, base_dir: Path, run_id: str) -> "ArtifactManifest":
        root = base_dir / run_id
        root.mkdir(parents=True, exist_ok=True)
        return cls(root=root)
