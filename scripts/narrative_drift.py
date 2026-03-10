"""Create a lightweight narrative-drift audit stub.

This script compares available review artifacts against canonical theme text at a high level.
Detailed semantic analysis is intentionally left as a TODO.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]


@app.command()
def main(date: str = typer.Option(None, help="Audit date (YYYY-MM-DD). Defaults to today.")) -> None:
    """Generate outputs/narrative_drift_<date>.md."""
    as_of = date or dt.date.today().isoformat()

    themes_path = BASE_DIR / "themes" / "Themes.md"
    monthly_reviews = sorted((BASE_DIR / "reviews" / "monthly").glob("*.md"))
    earnings_reviews = sorted((BASE_DIR / "reviews" / "earnings").glob("*.md"))

    output_path = BASE_DIR / "outputs" / f"narrative_drift_{as_of}.md"
    output = f"""# Narrative Drift Audit ({as_of})

## Inputs
- Canonical themes: {themes_path}
- Monthly reviews found: {len(monthly_reviews)}
- Earnings reviews found: {len(earnings_reviews)}

## TODO Analysis Checklist
- TODO: Compare each monthly review thesis language vs canonical theme statements.
- TODO: Flag where confidence increased without supporting evidence.
- TODO: Flag where disconfirming evidence was omitted.
- TODO: Identify contradictions across monthly vs earnings reviews.

## Recent Files
"""

    for p in monthly_reviews[-5:]:
        output += f"- monthly: {p.name}\n"
    for p in earnings_reviews[-5:]:
        output += f"- earnings: {p.name}\n"

    output_path.write_text(output, encoding="utf-8")
    console.print(f"[green]Wrote narrative drift audit:[/green] {output_path}")


if __name__ == "__main__":
    app()
