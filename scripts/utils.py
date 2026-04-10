"""Shared utility helpers used across multiple scripts."""

from __future__ import annotations


def dedupe(values: list[str]) -> list[str]:
    """Preserve insertion order while removing blank strings and duplicates."""
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        stripped = value.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        result.append(stripped)
    return result
