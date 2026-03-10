"""Build a post-earnings markdown summary from the latest earnings review."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import typer
from jinja2 import Template
from rich.console import Console

from data_store import default_db_path, read_events
from repo_helpers import normalize_theme_name
from review_helpers import (
    extract_bullets,
    extract_first_meaningful_line,
    extract_selected_option,
    extract_section,
    find_latest_earnings_review,
)

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]


@app.command()
def main(
    ticker: str = typer.Option(..., help="Ticker symbol, e.g., VRT"),
    theme: str = typer.Option(None, help="Optional theme name from themes/Themes.md."),
    date: str = typer.Option(None, help="Report date (YYYY-MM-DD). Defaults to today."),
    db_path: Path = typer.Option(
        None, help="Optional SQLite path. Defaults to data/processed/research.db."
    ),
) -> None:
    """Create a markdown post-earnings summary from the latest review file."""
    as_of = date or dt.date.today().isoformat()
    ticker_up = ticker.upper()
    db_path = db_path or default_db_path(BASE_DIR)
    canonical_theme = None
    if theme:
        try:
            canonical_theme = normalize_theme_name(theme, BASE_DIR / "themes" / "Themes.md")
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc

    latest_review = find_latest_earnings_review(
        BASE_DIR / "reviews" / "earnings",
        ticker_up,
        canonical_theme,
    )
    if latest_review is None:
        raise typer.BadParameter(
            f"No earnings review found for ticker '{ticker_up}'"
            + (f" under theme '{canonical_theme}'." if canonical_theme else ".")
        )

    output_dir = BASE_DIR / "outputs" / "post_earnings"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{as_of}_{ticker_up}_post_earnings.md"

    review_text = latest_review.read_text(encoding="utf-8")
    theme_name = (
        canonical_theme
        or extract_first_meaningful_line(extract_section(review_text, "### Theme"))
        or "Unknown theme"
    )
    total_score = (
        extract_first_meaningful_line(extract_section(review_text, "### Total Score"))
        or "Not scored"
    )
    bottom_line = (
        extract_first_meaningful_line(extract_section(review_text, "### One-Sentence Bottom Line"))
        or "No bottom-line statement recorded."
    )
    read_through = (
        extract_selected_option(
            extract_section(review_text, "### What This Quarter Says About the Theme")
        )
        or "Not recorded"
    )
    role_after = (
        extract_selected_option(
            extract_section(review_text, "### Current Role After the Print Should Be")
        )
        or "Not recorded"
    )
    role_action = (
        extract_selected_option(
            extract_section(review_text, "### Keep / Promote / Demote / Remove?")
        )
        or "Not recorded"
    )
    judgment = (
        extract_selected_option(extract_section(review_text, "### Judgment")) or "Not recorded"
    )
    rationale = extract_bullets(extract_section(review_text, "### Why"))
    upgrade_conditions = extract_bullets(
        extract_section(
            review_text, "### What Would Have to Happen Next Quarter to Upgrade the View?"
        )
    )
    downgrade_conditions = extract_bullets(
        extract_section(review_text, "### What Would Force a Downgrade Next Quarter?")
    )
    recent_events = read_events(db_path, ticker=ticker_up, limit=8)

    template = Template(
        """# Post-Earnings Summary: {{ ticker }} ({{ as_of }})

## Source Review File
`{{ source_file }}`

## Review Snapshot
- Theme: {{ theme_name }}
- Total score: {{ total_score }}
- Bottom line: {{ bottom_line }}
- Theme read-through: {{ read_through }}
- Basket role after print: {{ role_after }}
- Role action: {{ role_action }}
- Capital judgment: {{ judgment }}

## Why This Matters
{% for item in rationale %}
- {{ item }}
{% endfor %}
{% if not rationale %}
- No explicit rationale bullets recorded in the source review.
{% endif %}

## What Would Upgrade The View Next Quarter
{% for item in upgrade_conditions %}
- {{ item }}
{% endfor %}
{% if not upgrade_conditions %}
- No upgrade conditions were recorded.
{% endif %}

## What Would Force A Downgrade Next Quarter
{% for item in downgrade_conditions %}
- {{ item }}
{% endfor %}
{% if not downgrade_conditions %}
- No downgrade conditions were recorded.
{% endif %}

## Recent Local Events
{% for event in recent_events %}
- [{{ event.event_date }}] {{ event.title }}
{% endfor %}
{% if not recent_events %}
- No local news or SEC events for this ticker are stored in SQLite yet.
{% endif %}
"""
    )

    output_path.write_text(
        template.render(
            ticker=ticker_up,
            as_of=as_of,
            bottom_line=bottom_line,
            downgrade_conditions=downgrade_conditions,
            judgment=judgment,
            rationale=rationale,
            read_through=read_through,
            recent_events=recent_events,
            role_action=role_action,
            role_after=role_after,
            source_file=latest_review.name,
            theme_name=theme_name,
            total_score=total_score,
            upgrade_conditions=upgrade_conditions,
        ),
        encoding="utf-8",
    )

    console.print(f"[green]Wrote post-earnings summary:[/green] {output_path}")


if __name__ == "__main__":
    app()
