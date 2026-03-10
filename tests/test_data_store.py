from __future__ import annotations

from pathlib import Path

from data_store import ResearchEvent, insert_events, read_events


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
