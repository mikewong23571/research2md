"""Prompt loading utilities."""
from __future__ import annotations

from importlib import resources


def load_prompt(name: str) -> str:
    with resources.files(__package__).joinpath(f"{name}.prompt").open("r", encoding="utf-8") as fp:
        return fp.read()
