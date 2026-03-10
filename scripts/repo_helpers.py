"""Shared helpers for local-first review scripts."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field


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


class ThemeDefinition(BaseModel):
    name: str
    thesis_statement: str = ""
    strongest_counter_narrative: str = ""
    benchmark: list[str] = Field(default_factory=list)
    canary: list[str] = Field(default_factory=list)


def _extract_theme_section(block: str, heading: str) -> str:
    match = re.search(
        rf"^### {re.escape(heading)}\n(.*?)(?=^### |\Z)",
        block,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return ""
    return match.group(1).strip()


def _extract_theme_bullets(block: str, heading: str) -> list[str]:
    section = _extract_theme_section(block, heading)
    bullets: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return bullets


def load_theme_definitions(themes_path: Path) -> dict[str, ThemeDefinition]:
    themes_text = themes_path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^## Theme \d+:\s*(.+)$", themes_text, re.MULTILINE))
    definitions: dict[str, ThemeDefinition] = {}

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(themes_text)
        block = themes_text[start:end].strip()
        name = match.group(1).strip()
        definitions[name] = ThemeDefinition(
            name=name,
            thesis_statement=_extract_theme_section(block, "Thesis Statement"),
            strongest_counter_narrative=_extract_theme_section(
                block, "Strongest Counter-Narrative"
            ),
            benchmark=_extract_theme_bullets(block, "Benchmark"),
            canary=_extract_theme_bullets(block, "Control / Canaries"),
        )

    return definitions


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
