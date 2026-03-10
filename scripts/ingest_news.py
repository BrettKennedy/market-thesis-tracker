"""Fetch lightweight RSS/news snapshots into local raw files.

This script is intentionally simple and local-first. It stores a JSONL file that can be
reviewed and transformed later.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import feedparser
import httpx
import typer
from pydantic import BaseModel
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_FEEDS = [
    "https://www.sec.gov/news/pressreleases.rss",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=MSFT,CRM,NOW&region=US&lang=en-US",
]


class NewsItem(BaseModel):
    title: str
    link: str | None = None
    published: str | None = None
    feed_url: str | None = None


@app.command()
def main(
    feed: list[str] = typer.Option(None, help="One or more RSS/Atom feed URLs."),
    limit: int = typer.Option(10, min=1, max=100, help="Max items per feed."),
) -> None:
    """Fetch RSS entries and store a local JSONL snapshot."""
    feeds = feed or DEFAULT_FEEDS
    as_of = dt.date.today().isoformat()
    output_dir = BASE_DIR / "data" / "raw" / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"news_snapshot_{as_of}.jsonl"

    rows: list[NewsItem] = []
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        for feed_url in feeds:
            try:
                response = client.get(feed_url)
                response.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                console.print(f"[yellow]Skipping feed due to fetch error[/yellow] {feed_url}: {exc}")
                continue

            parsed = feedparser.parse(response.text)
            for entry in parsed.entries[:limit]:
                item = NewsItem(
                    title=str(entry.get("title", "")),
                    link=entry.get("link"),
                    published=entry.get("published"),
                    feed_url=feed_url,
                )
                rows.append(item)

    with output_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(row.model_dump_json() + "\n")

    console.print(f"[green]Wrote {len(rows)} news rows:[/green] {output_path}")
    console.print("[cyan]TODO:[/cyan] add de-duplication and relevance filtering rules.")


if __name__ == "__main__":
    app()
