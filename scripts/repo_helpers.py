"""Shared helpers for local-first review scripts."""

from __future__ import annotations

import re
from pathlib import Path


def slugify(value: str) -> str:
    """Convert text into a filesystem-safe slug."""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def load_canonical_theme_names(themes_path: Path) -> list[str]:
    """Extract canonical theme names from themes/Themes.md headings."""
    themes_text = themes_path.read_text(encoding="utf-8")
    names: list[str] = []

    for line in themes_text.splitlines():
        match = re.match(r"^## Theme \d+:\s*(.+)$", line.strip())
        if match:
            names.append(match.group(1).strip())

    return names


def normalize_theme_name(raw_theme: str, themes_path: Path) -> str:
    """Resolve a user-provided theme string to the canonical repo value."""
    theme = raw_theme.strip()
    canonical_names = load_canonical_theme_names(themes_path)

    for candidate in canonical_names:
        if theme == candidate:
            return candidate

    lowered = theme.lower()
    for candidate in canonical_names:
        if lowered == candidate.lower():
            return candidate

    full_heading = re.sub(r"^\s*##\s*", "", theme)
    for candidate in canonical_names:
        if full_heading.lower().endswith(candidate.lower()):
            return candidate

    valid = ", ".join(canonical_names)
    raise ValueError(f"Unknown theme '{raw_theme}'. Use one of: {valid}")
