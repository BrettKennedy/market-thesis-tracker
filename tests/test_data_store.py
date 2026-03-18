from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

import sqlite3

from data_store import ResearchEvent, ensure_schema, insert_events, read_events


def test_insert_events_replaces_rows_for_the_same_snapshot(tmp_path: Path):
    db_path = tmp_path / "research.db"
    local_path = tmp_path / "news_snapshot_2026-03-10.jsonl"

    insert_events(
        db_path,
        [
            ResearchEvent(
                source="news",
                event_date="2026-03-10",
                ticker="VRT",
                theme="AI Infrastructure Buildout Is Durable",
                event_type="news",
                title="Old row",
                local_path=str(local_path),
            )
        ],
    )
    insert_events(
        db_path,
        [
            ResearchEvent(
                source="news",
                event_date="2026-03-10",
                ticker="VRT",
                theme="AI Infrastructure Buildout Is Durable",
                event_type="news",
                title="Updated row",
                local_path=str(local_path),
            )
        ],
    )

    rows = read_events(db_path, ticker="VRT")

    assert len(rows) == 1
    assert rows[0].title == "Updated row"


def test_research_event_rejects_invalid_event_date():
    with pytest.raises(ValidationError, match="event_date must be YYYY-MM-DD"):
        ResearchEvent(
            source="test",
            event_date="not-a-date",
            event_type="test",
            title="Bad date event",
        )


def test_research_event_strips_event_date_whitespace():
    event = ResearchEvent(
        source="test",
        event_date="  2026-03-10  ",
        event_type="test",
        title="Whitespace date",
    )
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
