from __future__ import annotations

from pathlib import Path

import build_post_earnings
import build_weekly_digest
import narrative_drift
from data_store import ResearchEvent, default_db_path, insert_events


def test_build_weekly_digest_reads_reviews_and_sqlite(monkeypatch, temp_repo: Path):
    db_path = default_db_path(temp_repo)
    insert_events(
        db_path,
        [
            ResearchEvent(
                source="news",
                event_date="2026-03-09",
                ticker="VRT",
                theme="AI Infrastructure Buildout Is Durable",
                event_type="news",
                title="VRT expands AI cooling capacity",
            )
        ],
    )
    monkeypatch.setattr(build_weekly_digest, "BASE_DIR", temp_repo)

    build_weekly_digest.main(date="2026-03-10", db_path=db_path, days=30)

    output_path = temp_repo / "outputs" / "weekly" / "weekly_digest_2026-03-10.md"
    text = output_path.read_text(encoding="utf-8")

    assert output_path.exists()
    assert "AI Infrastructure Buildout Is Durable" in text
    assert "VRT expands AI cooling capacity" in text


def test_build_post_earnings_uses_latest_earnings_review(monkeypatch, temp_repo: Path):
    db_path = default_db_path(temp_repo)
    insert_events(
        db_path,
        [
            ResearchEvent(
                source="sec",
                event_date="2026-02-20",
                ticker="VRT",
                theme="AI Infrastructure Buildout Is Durable",
                event_type="sec_10-q",
                title="VRT filed 10-Q",
            )
        ],
    )
    monkeypatch.setattr(build_post_earnings, "BASE_DIR", temp_repo)

    build_post_earnings.main(
        ticker="VRT",
        theme="AI Infrastructure Buildout Is Durable",
        date="2026-03-10",
        db_path=db_path,
    )

    output_path = temp_repo / "outputs" / "post_earnings" / "2026-03-10_VRT_post_earnings.md"
    text = output_path.read_text(encoding="utf-8")

    assert output_path.exists()
    assert "Capital judgment: Watch only" in text
    assert "VRT filed 10-Q" in text


def test_narrative_drift_audit_passes_for_bootstrap_examples(monkeypatch, temp_repo: Path):
    monkeypatch.setattr(narrative_drift, "BASE_DIR", temp_repo)

    narrative_drift.main(date="2026-03-10")

    output_path = temp_repo / "outputs" / "narrative_drift_2026-03-10.md"
    text = output_path.read_text(encoding="utf-8")

    assert output_path.exists()
    assert "Result: no drift findings in latest monthly review." in text
    assert "Result: no audit findings in this earnings review." in text
