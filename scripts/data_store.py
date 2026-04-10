"""SQLite helpers for local research events."""

from __future__ import annotations

import datetime as dt
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError, field_validator

logger = logging.getLogger(__name__)


class ResearchEvent(BaseModel):
    source: str
    event_date: str
    ticker: str | None = None
    theme: str | None = None
    event_type: str
    title: str
    url: str | None = None
    local_path: str | None = None
    summary: str | None = None
    raw_payload: dict[str, Any] | list[Any] | str | None = None

    @field_validator("event_date")
    @classmethod
    def validate_event_date(cls, value: str) -> str:
        stripped = value.strip()
        try:
            dt.date.fromisoformat(stripped)
        except ValueError:
            raise ValueError(f"event_date must be YYYY-MM-DD, got '{value}'") from None
        return stripped

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip().upper()
        return stripped or None

    @field_validator("theme")
    @classmethod
    def normalize_theme(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


def default_db_path(base_dir: Path) -> Path:
    return base_dir / "data" / "processed" / "research.db"


def ensure_schema(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                source TEXT NOT NULL,
                event_date TEXT NOT NULL,
                ticker TEXT,
                theme TEXT,
                event_type TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                local_path TEXT,
                summary TEXT,
                raw_payload TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_events_event_date ON events(event_date DESC);
            CREATE INDEX IF NOT EXISTS idx_events_ticker ON events(ticker);
            CREATE INDEX IF NOT EXISTS idx_events_theme ON events(theme);
            """
        )


def insert_events(db_path: Path, events: list[ResearchEvent]) -> int:
    ensure_schema(db_path)
    if not events:
        return 0

    # Deduplicate rows that share a (source, local_path) snapshot key.
    # Events without a local_path are not part of a snapshot batch and are
    # inserted without prior deletion; callers that omit local_path should
    # ensure they are not re-inserting stale data.
    snapshot_keys = {(event.source, event.local_path) for event in events if event.local_path}
    with sqlite3.connect(db_path) as conn:
        for source, local_path in snapshot_keys:
            conn.execute(
                "DELETE FROM events WHERE source = ? AND local_path = ?",
                (source, local_path),
            )

        conn.executemany(
            """
            INSERT INTO events (
                source,
                event_date,
                ticker,
                theme,
                event_type,
                title,
                url,
                local_path,
                summary,
                raw_payload
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    event.source,
                    event.event_date,
                    event.ticker,
                    event.theme,
                    event.event_type,
                    event.title,
                    event.url,
                    event.local_path,
                    event.summary,
                    json.dumps(event.raw_payload, sort_keys=True)
                    if isinstance(event.raw_payload, (dict, list))
                    else event.raw_payload,
                )
                for event in events
            ],
        )
        return len(events)


def read_events(
    db_path: Path,
    *,
    ticker: str | None = None,
    theme: str | None = None,
    since_date: str | None = None,
    limit: int = 50,
) -> list[ResearchEvent]:
    if not db_path.exists():
        return []

    clauses: list[str] = []
    params: list[str | int] = []

    if ticker:
        clauses.append("ticker = ?")
        params.append(ticker.upper())
    if theme:
        clauses.append("theme = ?")
        params.append(theme)
    if since_date:
        clauses.append("event_date >= ?")
        params.append(since_date)

    where_clause = ""
    if clauses:
        where_clause = "WHERE " + " AND ".join(clauses)

    query = f"""
        SELECT
            source,
            event_date,
            ticker,
            theme,
            event_type,
            title,
            url,
            local_path,
            summary,
            raw_payload
        FROM events
        {where_clause}
        ORDER BY event_date DESC, title ASC
        LIMIT ?
    """
    params.append(limit)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()

    events: list[ResearchEvent] = []
    for row in rows:
        payload = row["raw_payload"]
        if payload:
            try:
                parsed_payload: dict[str, Any] | list[Any] | str = json.loads(payload)
            except json.JSONDecodeError:
                parsed_payload = payload
        else:
            parsed_payload = None

        try:
            events.append(
                ResearchEvent(
                    source=row["source"],
                    event_date=row["event_date"],
                    ticker=row["ticker"],
                    theme=row["theme"],
                    event_type=row["event_type"],
                    title=row["title"],
                    url=row["url"],
                    local_path=row["local_path"],
                    summary=row["summary"],
                    raw_payload=parsed_payload,
                )
            )
        except ValidationError:
            logger.warning(
                "Skipping stored event with invalid data (title=%r, date=%r)",
                row["title"],
                row["event_date"],
            )

    return events
