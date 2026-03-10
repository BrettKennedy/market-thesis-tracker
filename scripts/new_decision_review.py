"""Create a new decision checklist file from the canonical template."""

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
    ticker: str = typer.Option(..., help="Ticker symbol"),
    theme: str = typer.Option(..., help="Theme name"),
    decision_type: str = typer.Option(
        ..., "--decision-type", help="Buy/Add/Hold/Trim/Cut/Watch only"
    ),
    date: str = typer.Option(None, help="Decision date in YYYY-MM-DD. Defaults to today."),
) -> None:
    """Create reviews/decisions/<date>_<ticker>_<decision>.md from decision checklist."""
    as_of = date or dt.date.today().isoformat()
    ticker_up = ticker.upper()
    allowed_decisions = {"Buy", "Add", "Hold", "Trim", "Cut", "Watch only"}
    if decision_type not in allowed_decisions:
        allowed = ", ".join(sorted(allowed_decisions))
        raise typer.BadParameter(f"Unknown decision type '{decision_type}'. Use one of: {allowed}")
    try:
        canonical_theme = normalize_theme_name(theme, BASE_DIR / "themes" / "Themes.md")
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    template_path = BASE_DIR / "templates" / "Decision_Checklist.md"
    output_dir = BASE_DIR / "reviews" / "decisions"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = (
        output_dir / f"{as_of}_{ticker_up}_{slugify(canonical_theme)}_{slugify(decision_type)}.md"
    )

    if output_path.exists():
        console.print(f"[red]File already exists:[/red] {output_path}")
        raise typer.Exit(code=1)

    content = template_path.read_text(encoding="utf-8")
    content = content.replace("YYYY-MM-DD", as_of, 1)
    content = content.replace("[Ticker]", ticker_up, 1)
    content = content.replace("[Theme name]", canonical_theme, 1)
    content = content.replace(
        "### Decision Type\n",
        f"### Decision Type\nSelected: {decision_type}\n\n",
        1,
    )

    output_path.write_text(content, encoding="utf-8")
    console.print(f"[green]Created decision checklist:[/green] {output_path}")
    console.print("[cyan]TODO:[/cyan] complete checklist fields before acting on any decision.")


if __name__ == "__main__":
    app()
