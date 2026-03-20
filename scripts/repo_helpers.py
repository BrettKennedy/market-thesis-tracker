"""Shared helpers for local-first review scripts."""

from __future__ import annotations

import datetime as dt
import email.utils
import logging
import re
import time
from pathlib import Path

import httpx
import typer
from pydantic import BaseModel, Field

THEMES_FILENAME = "themes.md"
TICKER_BASKETS_FILENAME = "ticker_baskets.yaml"


def get_themes_path(base_dir: Path) -> Path:
    """Return the required tracked themes file and fail clearly if it is missing."""
    themes_path = base_dir / "themes" / THEMES_FILENAME
    if themes_path.exists():
        return themes_path
    raise FileNotFoundError(f"Missing required themes file at {themes_path}.")


def get_ticker_baskets_path(base_dir: Path) -> Path:
    """Return the required tracked basket file and fail clearly if it is missing."""
    baskets_path = base_dir / "config" / TICKER_BASKETS_FILENAME
    if baskets_path.exists():
        return baskets_path
    raise FileNotFoundError(f"Missing required ticker basket file at {baskets_path}.")


def slugify(value: str) -> str:
    """Convert text into a filesystem-safe slug."""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def load_canonical_theme_names(themes_path: Path) -> list[str]:
    """Extract canonical theme names from the tracked themes file."""
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


logger = logging.getLogger(__name__)


def normalize_date_str(value: str, *, fallback: str) -> str:
    """Best-effort conversion of *value* to an ISO ``YYYY-MM-DD`` string.

    Tries ``fromisoformat`` first, then RFC 2822 (the standard RSS date
    format) via :func:`email.utils.parsedate_to_datetime`.  Returns
    *fallback* when the string cannot be parsed at all.
    """
    stripped = value.strip()
    if not stripped:
        return fallback

    # Fast path: already ISO
    try:
        dt.date.fromisoformat(stripped)
        return stripped
    except ValueError:
        pass

    # RFC 2822 / RFC 5322 (e.g. "Mon, 10 Mar 2026 12:00:00 GMT")
    try:
        parsed = email.utils.parsedate_to_datetime(stripped)
        return parsed.date().isoformat()
    except (ValueError, TypeError):
        pass

    logger.warning("Unparseable date '%s', using fallback '%s'", value, fallback)
    return fallback


def validate_date_str(value: str) -> str:
    """Validate an ISO date string, raising typer.BadParameter on failure."""
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        raise typer.BadParameter(f"Invalid date '{value}'. Use YYYY-MM-DD format.") from None
    return value


def http_get_with_retry(
    client: httpx.Client,
    url: str,
    *,
    max_attempts: int = 3,
    backoff_base: float = 1.0,
) -> httpx.Response:
    """GET with retry on transient network errors.

    Retries on transport errors (connection, timeout, read, protocol)
    with exponential backoff.  Does not retry HTTP status errors (4xx/5xx).
    """
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            response = client.get(url)
            response.raise_for_status()
            return response
        except httpx.TransportError as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                time.sleep(backoff_base * 2**attempt)
    raise last_exc  # type: ignore[misc]


def setup_logging(verbose: bool = False) -> None:
    """Configure root logger with a standard format."""
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG if verbose else logging.INFO,
    )
