"""Provide utilities for testing."""

from pathlib import Path


def load_fixture(path: str) -> str:
    """Load a fixture."""
    return Path(__file__).parent.joinpath("fixtures", path).read_text(encoding="utf-8")
