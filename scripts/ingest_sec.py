"""Ingest SEC filing metadata into local raw storage and SQLite."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import httpx
import typer
from rich.console import Console

from config_models import load_ticker_theme_map, load_tracked_tickers
from data_store import ResearchEvent, default_db_path, insert_events

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
DEFAULT_SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
DEFAULT_SEC_USER_AGENT = "market-thesis-tracker/0.1 local research workflow"


def build_company_ticker_map(payload: dict[str, Any]) -> dict[str, str]:
    """Map ticker symbols to zero-padded SEC CIK strings."""
    ticker_map: dict[str, str] = {}

    for entry in payload.values():
        if not isinstance(entry, dict):
            continue
        ticker = str(entry.get("ticker", "")).upper()
        cik_str = str(entry.get("cik_str", "")).strip()
        if ticker and cik_str:
            ticker_map[ticker] = cik_str.zfill(10)

    return ticker_map


def build_filing_events(
    ticker: str,
    themes: list[str],
    submissions: dict[str, Any],
    *,
    limit: int,
    local_path: Path,
) -> list[ResearchEvent]:
    """Convert SEC submissions JSON into normalized event rows."""
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    accession_numbers = recent.get("accessionNumber", [])
    primary_documents = recent.get("primaryDocument", [])
    cik = str(submissions.get("cik", "")).strip().lstrip("0")

    events: list[ResearchEvent] = []
    upper_ticker = ticker.upper()
    theme_values = themes or [None]
    event_count = min(limit, len(forms), len(filing_dates))

    for index in range(event_count):
        filing_date = str(filing_dates[index])
        form = str(forms[index])
        accession_number = str(accession_numbers[index]) if index < len(accession_numbers) else ""
        primary_document = str(primary_documents[index]) if index < len(primary_documents) else ""
        filing_url = None
        if cik and accession_number and primary_document:
            filing_url = (
                f"https://www.sec.gov/Archives/edgar/data/{cik}/"
                f"{accession_number.replace('-', '')}/{primary_document}"
            )

        raw_payload = {
            "ticker": upper_ticker,
            "form": form,
            "filing_date": filing_date,
            "accession_number": accession_number,
            "primary_document": primary_document,
        }

        for theme in theme_values:
            events.append(
                ResearchEvent(
                    source="sec",
                    event_date=filing_date,
                    ticker=upper_ticker,
                    theme=theme,
                    event_type=f"sec_{form.lower()}",
                    title=f"{upper_ticker} filed {form}",
                    url=filing_url,
                    local_path=str(local_path),
                    summary=f"Form {form} filed on {filing_date}",
                    raw_payload=raw_payload,
                )
            )

    return events


@app.command()
def main(
    date: str = typer.Option(None, help="Snapshot date in YYYY-MM-DD format. Defaults to today."),
    ticker: list[str] = typer.Option(
        None, help="Optional tickers to ingest. Defaults to configured baskets."
    ),
    limit: int = typer.Option(5, min=1, max=25, help="Max recent filings per ticker."),
    db_path: Path = typer.Option(
        None, help="Optional SQLite path. Defaults to data/processed/research.db."
    ),
    user_agent: str = typer.Option(
        DEFAULT_SEC_USER_AGENT,
        "--user-agent",
        envvar="MARKET_THESIS_SEC_USER_AGENT",
        help="SEC-compatible user agent string.",
    ),
    company_tickers_url: str = typer.Option(
        DEFAULT_COMPANY_TICKERS_URL,
        help="SEC company_tickers.json endpoint.",
    ),
) -> None:
    """Fetch SEC submission metadata and persist local events."""
    as_of = date or dt.date.today().isoformat()
    output_dir = BASE_DIR / "data" / "raw" / "sec"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"sec_snapshot_{as_of}.jsonl"
    db_path = db_path or default_db_path(BASE_DIR)
    theme_map = load_ticker_theme_map(BASE_DIR / "config" / "Ticker_Baskets.yaml")
    selected_tickers = sorted(
        {value.upper() for value in ticker}
        if ticker
        else load_tracked_tickers(BASE_DIR / "config" / "Ticker_Baskets.yaml")
    )

    headers = {"User-Agent": user_agent}
    events: list[ResearchEvent] = []

    with httpx.Client(headers=headers, timeout=20.0, follow_redirects=True) as client:
        company_tickers_payload = client.get(company_tickers_url)
        company_tickers_payload.raise_for_status()
        ticker_map = build_company_ticker_map(company_tickers_payload.json())

        for ticker_value in selected_tickers:
            cik = ticker_map.get(ticker_value)
            if not cik:
                console.print(
                    f"[yellow]Skipping ticker with no SEC CIK mapping[/yellow] {ticker_value}"
                )
                continue

            submissions_url = DEFAULT_SEC_SUBMISSIONS_URL.format(cik=cik)
            response = client.get(submissions_url)
            response.raise_for_status()
            submissions = response.json()
            events.extend(
                build_filing_events(
                    ticker_value,
                    theme_map.get(ticker_value, []),
                    submissions,
                    limit=limit,
                    local_path=output_path,
                )
            )

    with output_path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(event.model_dump_json() + "\n")

    inserted = insert_events(db_path, events)
    console.print(f"[green]Wrote SEC snapshot:[/green] {output_path}")
    console.print(f"[green]Stored {inserted} SEC events in SQLite:[/green] {db_path}")


if __name__ == "__main__":
    app()
