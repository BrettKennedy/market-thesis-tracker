from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from data_store import ResearchEvent, ensure_schema, insert_events, read_events
from pydantic import ValidationError


def _make_event(**kwargs) -> ResearchEvent:
    defaults = dict(
        source="news",
        event_date="2026-03-10",
        event_type="news",
        title="Test event",
    )
    defaults.update(kwargs)
    return ResearchEvent(**defaults)


def test_insert_events_replaces_rows_for_the_same_snapshot(tmp_path: Path):
    db_path = tmp_path / "research.db"
    local_path = tmp_path / "news_snapshot_2026-03-10.jsonl"

    insert_events(db_path, [_make_event(title="Old row", local_path=str(local_path))])
    insert_events(db_path, [_make_event(title="Updated row", local_path=str(local_path))])

    rows = read_events(db_path)

    assert len(rows) == 1
    assert rows[0].title == "Updated row"


def test_insert_events_empty_list_returns_zero(tmp_path: Path):
    db_path = tmp_path / "research.db"
    result = insert_events(db_path, [])
    assert result == 0


def test_read_events_returns_empty_list_when_db_missing(tmp_path: Path):
    db_path = tmp_path / "nonexistent.db"
    assert read_events(db_path) == []


def test_read_events_filters_by_ticker(tmp_path: Path):
    db_path = tmp_path / "research.db"
    insert_events(db_path, [_make_event(ticker="VRT", title="VRT event")])
    insert_events(db_path, [_make_event(ticker="NVDA", title="NVDA event")])

    rows = read_events(db_path, ticker="VRT")

    assert len(rows) == 1
    assert rows[0].ticker == "VRT"


def test_read_events_ticker_filter_is_case_insensitive(tmp_path: Path):
    db_path = tmp_path / "research.db"
    insert_events(db_path, [_make_event(ticker="VRT", title="VRT event")])

    rows = read_events(db_path, ticker="vrt")

    assert len(rows) == 1
    assert rows[0].ticker == "VRT"


def test_read_events_filters_by_since_date(tmp_path: Path):
    db_path = tmp_path / "research.db"
    insert_events(db_path, [_make_event(event_date="2026-01-01", title="Old")])
    insert_events(db_path, [_make_event(event_date="2026-03-10", title="Recent")])

    rows = read_events(db_path, since_date="2026-02-01")

    assert len(rows) == 1
    assert rows[0].title == "Recent"


def test_read_events_respects_limit(tmp_path: Path):
    db_path = tmp_path / "research.db"
    for i in range(5):
        insert_events(db_path, [_make_event(title=f"Event {i}")])

    rows = read_events(db_path, limit=3)

    assert len(rows) == 3


def test_research_event_rejects_invalid_event_date():
    with pytest.raises(ValidationError, match="event_date must be YYYY-MM-DD"):
        _make_event(event_date="not-a-date")


def test_research_event_rejects_non_iso_event_date():
    with pytest.raises(ValidationError, match="event_date must be YYYY-MM-DD"):
        _make_event(event_date="10/03/2026")


def test_research_event_normalizes_ticker_to_uppercase():
    event = _make_event(ticker="vrt")
    assert event.ticker == "VRT"


def test_research_event_strips_event_date_whitespace():
    event = _make_event(event_date="  2026-03-10  ")
    assert event.event_date == "2026-03-10"


def test_read_events_skips_legacy_rows_with_invalid_dates(tmp_path: Path):
    db_path = tmp_path / "research.db"
    ensure_schema(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO events (source, event_date, ticker, theme, event_type, title)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            ("news", "Mon, 10 Mar 2026", "VRT", None, "news", "Legacy row"),
        )
        conn.execute(
            "INSERT INTO events (source, event_date, ticker, theme, event_type, title)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            ("news", "2026-03-10", "VRT", None, "news", "Valid row"),
        )

    rows = read_events(db_path, ticker="VRT")

    assert len(rows) == 1
    assert rows[0].title == "Valid row"
