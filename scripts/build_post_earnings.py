"""Build a post-earnings markdown summary from review artifacts.

This is a thin local report builder. It does not perform automated trading decisions.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import typer
from jinja2 import Template
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]


@app.command()
def main(
    ticker: str = typer.Option(..., help="Ticker symbol, e.g., VRT"),
    date: str = typer.Option(None, help="Report date (YYYY-MM-DD). Defaults to today."),
) -> None:
    """Create a lightweight post-earnings summary in outputs/post_earnings/."""
    as_of = date or dt.date.today().isoformat()
    ticker_up = ticker.upper()

    earnings_dir = BASE_DIR / "reviews" / "earnings"
    candidates = sorted(earnings_dir.glob(f"*_{ticker_up}_*.md"))
    latest_review = candidates[-1] if candidates else None

    output_dir = BASE_DIR / "outputs" / "post_earnings"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{as_of}_{ticker_up}_post_earnings.md"

    review_excerpt = "No matching earnings review file found. TODO: create one first."
    if latest_review:
        review_excerpt = latest_review.read_text(encoding="utf-8")[:4000]

    template = Template(
        """# Post-Earnings Summary: {{ ticker }} ({{ as_of }})

## Source Review File
{{ source_file }}

## Review Excerpt
{{ review_excerpt }}

## Analyst TODO
- TODO: Confirm whether evidence strengthens or weakens the theme.
- TODO: Capture any role change (core/torque/canary/remove) with rationale.
- TODO: Log any related follow-up in `reviews/decisions/Prediction_Log.md`.
"""
    )

    output_path.write_text(
        template.render(
            ticker=ticker_up,
            as_of=as_of,
            source_file=str(latest_review) if latest_review else "N/A",
            review_excerpt=review_excerpt,
        ),
        encoding="utf-8",
    )

    console.print(f"[green]Wrote post-earnings summary:[/green] {output_path}")


if __name__ == "__main__":
    app()
