"""Create a new monthly review file from the canonical template."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import typer
from rich.console import Console

from repo_helpers import get_themes_path, normalize_theme_name, slugify

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]


@app.command()
def main(
    theme: str = typer.Option(..., help="Theme name exactly as tracked in themes/themes.md"),
    date: str = typer.Option(None, help="Review date in YYYY-MM-DD. Defaults to today."),
) -> None:
    """Create reviews/monthly/<date>_<theme>.md from monthly template."""
    as_of = date or dt.date.today().isoformat()
    try:
        canonical_theme = normalize_theme_name(theme, get_themes_path(BASE_DIR))
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    template_path = BASE_DIR / "templates" / "Monthly_Theme_Review_Template.md"
    output_dir = BASE_DIR / "reviews" / "monthly"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{as_of}_{slugify(canonical_theme)}.md"

    if output_path.exists():
        console.print(f"[red]File already exists:[/red] {output_path}")
        raise typer.Exit(code=1)

    content = template_path.read_text(encoding="utf-8")
    content = content.replace("YYYY-MM-DD", as_of, 1)
    content = content.replace("[Theme name]", canonical_theme, 1)

    output_path.write_text(content, encoding="utf-8")
    console.print(f"[green]Created monthly review:[/green] {output_path}")
    console.print("[cyan]TODO:[/cyan] complete fields using current evidence.")


if __name__ == "__main__":
    app()
