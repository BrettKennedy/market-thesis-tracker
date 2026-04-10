"""Fetch RSS/news snapshots into local raw files and SQLite."""

from __future__ import annotations

import datetime as dt
import logging
import re
from pathlib import Path

import feedparser
import httpx
import typer
from config_models import load_ticker_theme_map, load_tracked_tickers
from data_store import ResearchEvent, default_db_path, insert_events
from repo_helpers import (
    get_ticker_baskets_path,
    http_get_with_retry,
    normalize_date_str,
    setup_logging,
    validate_date_str,
)
from rich.console import Console

logger = logging.getLogger(__name__)

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]
# SEC press-release feed is safe as a default since it's theme-agnostic.
# The Yahoo Finance feed included here is an EXAMPLE only — replace the ticker
# list with symbols from your own basket before using it in production.
DEFAULT_FEEDS = [
    "https://www.sec.gov/news/pressreleases.rss",
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
            raw_date = str(entry.get("published", "")).strip()
            event_date = (
                normalize_date_str(raw_date, fallback=fallback_date) if raw_date else fallback_date
            )
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
    setup_logging()
    feeds = feed or DEFAULT_FEEDS
    as_of = date or dt.date.today().isoformat()
    if date:
        validate_date_str(as_of)
    output_dir = BASE_DIR / "data" / "raw" / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"news_snapshot_{as_of}.jsonl"
    db_path = db_path or default_db_path(BASE_DIR)
    baskets_path = get_ticker_baskets_path(BASE_DIR)
    theme_map = load_ticker_theme_map(baskets_path)
    tracked_tickers = (
        {item.upper() for item in ticker} if ticker else set(load_tracked_tickers(baskets_path))
    )

    rows: list[ResearchEvent] = []
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        for feed_url in feeds:
            logger.info("Fetching feed %s", feed_url)
            try:
                response = http_get_with_retry(client, feed_url)
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                logger.warning("Skipping feed %s: %s", feed_url, exc)
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
