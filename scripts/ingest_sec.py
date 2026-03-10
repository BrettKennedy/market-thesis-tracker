"""Ingest placeholder SEC filing metadata into local raw storage.

This script intentionally avoids heavy parsing logic. It prepares a local JSONL snapshot
that can be extended later with real SEC endpoint calls.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import httpx
import typer
import yaml
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]


def load_tickers_from_config(config_path: Path) -> list[str]:
    """Load unique tickers from config/Ticker_Baskets.yaml."""
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    tickers: set[str] = set()
    for theme_value in data.values():
        if not isinstance(theme_value, dict):
            continue
        for basket_value in theme_value.values():
            if isinstance(basket_value, list):
                tickers.update(str(t).upper() for t in basket_value)

    return sorted(tickers)


@app.command()
def main(
    date: str = typer.Option(None, help="Snapshot date in YYYY-MM-DD format. Defaults to today."),
) -> None:
    """Create a local SEC snapshot placeholder file."""
    as_of = date or dt.date.today().isoformat()
    output_dir = BASE_DIR / "data" / "raw" / "sec"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"sec_snapshot_{as_of}.jsonl"

    tickers = load_tickers_from_config(BASE_DIR / "config" / "Ticker_Baskets.yaml")

    headers = {
        # TODO: Replace with your own contact details before live SEC requests.
        "User-Agent": "market-thesis-tracker local research <replace-with-email>",
    }

    # TODO: Add real SEC submissions endpoint requests using httpx and local caching.
    with httpx.Client(headers=headers, timeout=20.0) as _client, output_path.open(
        "w", encoding="utf-8"
    ) as f:
        for ticker in tickers:
            row = {
                "ticker": ticker,
                "as_of": as_of,
                "source": "sec_placeholder",
                "note": "TODO: implement SEC fetch and filing extraction",
            }
            f.write(json.dumps(row) + "\n")

    console.print(f"[green]Wrote placeholder SEC snapshot:[/green] {output_path}")


if __name__ == "__main__":
    app()
