"""Build a lightweight weekly markdown digest.

This script reads local canonical files, summarizes basic context, and produces a markdown
output stub. It intentionally leaves analytical judgment as a manual TODO.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

import typer
import yaml
from jinja2 import Template
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]


def fetch_event_count(db_path: Path) -> int:
    """Return event count from local SQLite if the table exists, else 0."""
    if not db_path.exists():
        return 0

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
        )
        if cursor.fetchone() is None:
            return 0
        cursor.execute("SELECT COUNT(*) FROM events")
        return int(cursor.fetchone()[0])


@app.command()
def main(date: str = typer.Option(None, help="Digest date (YYYY-MM-DD). Defaults to today.")) -> None:
    """Generate outputs/weekly/weekly_digest_<date>.md."""
    as_of = date or dt.date.today().isoformat()
    output_dir = BASE_DIR / "outputs" / "weekly"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"weekly_digest_{as_of}.md"

    themes_text = (BASE_DIR / "themes" / "Themes.md").read_text(encoding="utf-8")
    baskets = yaml.safe_load((BASE_DIR / "config" / "Ticker_Baskets.yaml").read_text(encoding="utf-8"))
    event_count = fetch_event_count(BASE_DIR / "data" / "processed" / "research.db")
    prompt_text = (BASE_DIR / "prompts" / "weekly_digest.txt").read_text(encoding="utf-8")

    template = Template(
        """# Weekly Digest ({{ as_of }})

## Context
- Themes tracked: {{ theme_count }}
- Basket config themes: {{ basket_count }}
- Events in local SQLite (`events` table): {{ event_count }}

## Canonical Prompt
{{ prompt_text }}

## Theme Snapshot (Raw)
{{ themes_text }}

## Analyst TODO
- TODO: Add explicit strengthening evidence by theme.
- TODO: Add explicit weakening/disconfirming evidence by theme.
- TODO: Record uncertainty and open questions.
"""
    )

    markdown = template.render(
        as_of=as_of,
        theme_count=themes_text.count("## Theme"),
        basket_count=len(baskets or {}),
        event_count=event_count,
        prompt_text=prompt_text,
        themes_text=themes_text,
    )

    output_path.write_text(markdown, encoding="utf-8")
    console.print(f"[green]Wrote weekly digest:[/green] {output_path}")


if __name__ == "__main__":
    app()
