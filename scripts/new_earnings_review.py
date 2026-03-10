"""Create a new earnings review file from the canonical template."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import typer
from rich.console import Console
from repo_helpers import normalize_theme_name, slugify

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]


@app.command()
def main(
    ticker: str = typer.Option(..., help="Ticker symbol, e.g., VRT"),
    theme: str = typer.Option(..., help="Theme name from themes/Themes.md"),
    date: str = typer.Option(None, help="Review date in YYYY-MM-DD. Defaults to today."),
) -> None:
    """Create reviews/earnings/<date>_<ticker>_earnings_review.md from earnings template."""
    as_of = date or dt.date.today().isoformat()
    ticker_up = ticker.upper()
    try:
        canonical_theme = normalize_theme_name(theme, BASE_DIR / "themes" / "Themes.md")
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    template_path = BASE_DIR / "templates" / "Company_Earnings_Scorecard_Template.md"
    output_dir = BASE_DIR / "reviews" / "earnings"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{as_of}_{ticker_up}_{slugify(canonical_theme)}_earnings_review.md"

    if output_path.exists():
        console.print(f"[red]File already exists:[/red] {output_path}")
        raise typer.Exit(code=1)

    content = template_path.read_text(encoding="utf-8")
    content = content.replace("YYYY-MM-DD", as_of, 1)
    content = content.replace("[Ticker / company name]", ticker_up, 1)
    content = content.replace("[Theme name]", canonical_theme, 1)

    output_path.write_text(content, encoding="utf-8")
    console.print(f"[green]Created earnings review:[/green] {output_path}")
    console.print(
        "[cyan]TODO:[/cyan] complete scorecard sections after reviewing source materials."
    )


if __name__ == "__main__":
    app()
