from __future__ import annotations

from pathlib import Path

import pytest
import typer

import new_decision_review
import new_earnings_review
import new_monthly_review


def test_monthly_review_generator_creates_expected_file(monkeypatch, temp_repo: Path):
    monkeypatch.setattr(new_monthly_review, "BASE_DIR", temp_repo)

    new_monthly_review.main(theme="ai infrastructure buildout is durable", date="2026-05-01")

    output_path = (
        temp_repo / "reviews" / "monthly" / "2026-05-01_ai_infrastructure_buildout_is_durable.md"
    )
    assert output_path.exists()
    assert "AI Infrastructure Buildout Is Durable" in output_path.read_text(encoding="utf-8")


def test_earnings_review_generator_rejects_unknown_theme(monkeypatch, temp_repo: Path):
    monkeypatch.setattr(new_earnings_review, "BASE_DIR", temp_repo)

    with pytest.raises(typer.BadParameter):
        new_earnings_review.main(ticker="VRT", theme="Not A Theme", date="2026-03-10")


def test_decision_review_generator_stamps_decision_and_prevents_duplicates(
    monkeypatch,
    temp_repo: Path,
):
    monkeypatch.setattr(new_decision_review, "BASE_DIR", temp_repo)

    new_decision_review.main(
        ticker="VRT",
        theme="AI Infrastructure Buildout Is Durable",
        decision_type="Add",
        date="2026-03-10",
    )

    output_path = (
        temp_repo
        / "reviews"
        / "decisions"
        / "2026-03-10_VRT_ai_infrastructure_buildout_is_durable_add.md"
    )
    text = output_path.read_text(encoding="utf-8")

    assert output_path.exists()
    assert "Selected: Add" in text

    with pytest.raises(typer.Exit):
        new_decision_review.main(
            ticker="VRT",
            theme="AI Infrastructure Buildout Is Durable",
            decision_type="Add",
            date="2026-03-10",
        )
