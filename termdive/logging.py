"""Logging helpers for TermDive."""
from __future__ import annotations

import logging
from typing import Optional


def configure_logging(level: int = logging.INFO, *, run_id: Optional[str] = None) -> None:
    """Configure root logging with basic formatting."""

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]

    if run_id:
        logging.LoggerAdapter(root, extra={"run_id": run_id})
