"""Markdown parsing helpers for repo review artifacts."""

from __future__ import annotations

from pathlib import Path

from repo_helpers import slugify


def extract_section(text: str, heading: str) -> str:
    lines = text.splitlines()

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if line != heading:
            continue

        level = len(line.split(" ", 1)[0])
        section_lines: list[str] = []

        for candidate in lines[index + 1 :]:
            stripped = candidate.strip()
            if stripped.startswith("#"):
                next_level = len(stripped.split(" ", 1)[0])
                if next_level <= level:
                    break
            section_lines.append(candidate)

        return "\n".join(section_lines).strip()

    return ""


def extract_bullets(section_text: str) -> list[str]:
    bullets: list[str] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            content = stripped[2:].strip()
            if is_meaningful_text(content):
                bullets.append(content)
    return bullets


def extract_first_meaningful_line(section_text: str) -> str | None:
    for line in section_text.splitlines():
        stripped = line.strip()
        if is_meaningful_text(stripped):
            return stripped
    return None


def extract_selected_option(section_text: str) -> str | None:
    non_bullet_lines = [
        line.strip()
        for line in section_text.splitlines()
        if line.strip() and not line.strip().startswith("- ")
    ]
    for line in non_bullet_lines:
        if is_meaningful_text(line):
            return line

    bullets = extract_bullets(section_text)
    if len(bullets) == 1:
        return bullets[0]
    return None


def has_heading(text: str, heading: str) -> bool:
    return heading in text


def is_meaningful_text(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    if stripped in {"-", "[]", "N/A"}:
        return False
    if stripped == "YYYY-MM-DD":
        return False
    if stripped.startswith("[") and stripped.endswith("]"):
        return False
    if stripped in {"Yes", "No", "Maybe", "Partly", "Clean", "Mixed", "Noisy"}:
        return True
    return True


def section_has_meaningful_content(section_text: str) -> bool:
    return extract_first_meaningful_line(section_text) is not None


def find_latest_review_for_theme(review_dir: Path, theme_name: str) -> Path | None:
    candidates = sorted(review_dir.glob(f"*_{slugify(theme_name)}*.md"))
    return candidates[-1] if candidates else None


def find_latest_earnings_review(
    review_dir: Path, ticker: str, theme_name: str | None = None
) -> Path | None:
    if theme_name:
        candidates = sorted(
            review_dir.glob(f"*_{ticker.upper()}_{slugify(theme_name)}_earnings_review.md")
        )
    else:
        candidates = sorted(review_dir.glob(f"*_{ticker.upper()}_*.md"))
    return candidates[-1] if candidates else None
