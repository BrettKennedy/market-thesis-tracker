"""Fetch RSS/news snapshots into local raw files and SQLite."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import feedparser
import httpx
import typer
from rich.console import Console

from config_models import load_ticker_theme_map, load_tracked_tickers
from data_store import ResearchEvent, default_db_path, insert_events

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_FEEDS = [
    "https://www.sec.gov/news/pressreleases.rss",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=MSFT,CRM,NOW&region=US&lang=en-US",
]


def detect_tickers(text: str, tracked_tickers: set[str]) -> list[str]:
    """Find tracked tickers mentioned in a text blob."""
    if not text:
        return []

    haystack = text.upper()
    matches = [
        ticker for ticker in tracked_tickers if re.search(rf"\b{re.escape(ticker)}\b", haystack)
    ]
    return sorted(matches)


def build_news_events(
    parsed_feed: feedparser.FeedParserDict,
    *,
    feed_url: str,
    local_path: Path,
    tracked_tickers: set[str],
    theme_map: dict[str, list[str]],
    limit: int,
    fallback_date: str,
) -> list[ResearchEvent]:
    """Normalize feed entries into event rows."""
    events: list[ResearchEvent] = []

    for entry in parsed_feed.entries[:limit]:
        title = str(entry.get("title", "")).strip()
        summary = str(entry.get("summary", "") or entry.get("description", "")).strip()
        combined_text = f"{title}\n{summary}"
        if entry.get("published_parsed"):
            published = entry.get("published_parsed")
            event_date = dt.date(published.tm_year, published.tm_mon, published.tm_mday).isoformat()
        else:
            event_date = str(entry.get("published", "")).strip() or fallback_date
        link = str(entry.get("link", "")).strip() or None
        matched_tickers = detect_tickers(combined_text, tracked_tickers)

        raw_payload = {
            "title": title,
            "link": link,
            "published": event_date,
            "summary": summary,
            "feed_url": feed_url,
        }

        if not matched_tickers:
            events.append(
                ResearchEvent(
                    source="news",
                    event_date=event_date,
                    ticker=None,
                    theme=None,
                    event_type="news",
                    title=title or "Untitled feed entry",
                    url=link,
                    local_path=str(local_path),
                    summary=summary or None,
                    raw_payload=raw_payload,
                )
            )
            continue

        for ticker in matched_tickers:
            theme_names = theme_map.get(ticker, []) or [None]
            for theme_name in theme_names:
                events.append(
                    ResearchEvent(
                        source="news",
                        event_date=event_date,
                        ticker=ticker,
                        theme=theme_name,
                        event_type="news",
                        title=title or "Untitled feed entry",
                        url=link,
                        local_path=str(local_path),
                        summary=summary or None,
                        raw_payload=raw_payload,
                    )
                )

    return events


@app.command()
def main(
    feed: list[str] = typer.Option(None, help="One or more RSS/Atom feed URLs."),
    limit: int = typer.Option(10, min=1, max=100, help="Max items per feed."),
    ticker: list[str] = typer.Option(None, help="Optional tracked tickers to match against."),
    date: str = typer.Option(None, help="Snapshot date in YYYY-MM-DD format. Defaults to today."),
    db_path: Path = typer.Option(
        None, help="Optional SQLite path. Defaults to data/processed/research.db."
    ),
) -> None:
    """Fetch RSS entries and store both raw snapshots and SQLite events."""
    feeds = feed or DEFAULT_FEEDS
    as_of = date or dt.date.today().isoformat()
    output_dir = BASE_DIR / "data" / "raw" / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"news_snapshot_{as_of}.jsonl"
    db_path = db_path or default_db_path(BASE_DIR)
    theme_map = load_ticker_theme_map(BASE_DIR / "config" / "Ticker_Baskets.yaml")
    tracked_tickers = (
        {item.upper() for item in ticker}
        if ticker
        else set(load_tracked_tickers(BASE_DIR / "config" / "Ticker_Baskets.yaml"))
    )

    rows: list[ResearchEvent] = []
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        for feed_url in feeds:
            try:
                response = client.get(feed_url)
                response.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                console.print(
                    f"[yellow]Skipping feed due to fetch error[/yellow] {feed_url}: {exc}"
                )
                continue

            parsed = feedparser.parse(response.text)
            rows.extend(
                build_news_events(
                    parsed,
                    feed_url=feed_url,
                    local_path=output_path,
                    tracked_tickers=tracked_tickers,
                    theme_map=theme_map,
                    limit=limit,
                    fallback_date=as_of,
                )
            )

    with output_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(row.model_dump_json() + "\n")

    inserted = insert_events(db_path, rows)
    console.print(f"[green]Wrote {len(rows)} news rows:[/green] {output_path}")
    console.print(f"[green]Stored {inserted} news events in SQLite:[/green] {db_path}")


if __name__ == "__main__":
    app()
