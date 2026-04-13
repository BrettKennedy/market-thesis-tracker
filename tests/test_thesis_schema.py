from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from thesis_models import Thesis, load_thesis


def test_example_thesis_files_validate(repo_root: Path):
    ai_thesis = load_thesis(repo_root / "theses" / "ai_infrastructure_buildout_is_durable.yaml")
    saas_thesis = load_thesis(repo_root / "theses" / "saas_shakeout_is_real_but_selective.yaml")

    assert ai_thesis.status == "active"
    assert saas_thesis.status == "active"
    assert any(member.is_benchmark for member in ai_thesis.basket.members)
    assert any(member.role == "remove" for member in saas_thesis.basket.members)


def test_draft_allows_incomplete_fields_but_active_does_not():
    draft = Thesis.model_validate(
        {
            "schema_version": 1,
            "thesis_id": "draft_theme",
            "title": "Draft Theme",
            "status": "draft",
            "content": {"thesis_statement": "A rough idea worth capturing."},
        }
    )

    assert draft.status == "draft"
    assert draft.content.why_this_matters is None

    with pytest.raises(ValidationError):
        Thesis.model_validate(
            {
                "schema_version": 1,
                "thesis_id": "broken_active_theme",
                "title": "Broken Active Theme",
                "status": "active",
                "content": {"thesis_statement": "This is missing the rest."},
            }
        )


def test_thesis_id_must_be_lowercase_snake_case():
    with pytest.raises(ValidationError):
        Thesis.model_validate(
            {
                "schema_version": 1,
                "thesis_id": "Not-Snake-Case",
                "title": "Bad Id",
                "status": "draft",
                "content": {"thesis_statement": "Still a draft."},
            }
        )


def test_ticker_normalization_and_benchmark_only_members():
    thesis = Thesis.model_validate(
        {
            "schema_version": 1,
            "thesis_id": "benchmark_member_theme",
            "title": "Benchmark Member Theme",
            "status": "active",
            "content": {
                "thesis_statement": "A complete thesis statement.",
                "why_this_matters": "It matters for portfolio construction.",
                "mechanism": "A clear mechanism exists.",
                "time_horizon": "4 to 6 quarters",
            },
            "evidence": {
                "confirmation_signals": ["Something improved"],
                "disconfirming_signals": ["Something weakened"],
                "counter_narrative": "The thesis could still fail.",
            },
            "basket": {"members": [{"ticker": " spy ", "role": "benchmark"}]},
        }
    )

    assert thesis.basket.members[0].ticker == "SPY"
    assert thesis.basket.members[0].role == "benchmark"
    assert thesis.basket.members[0].is_benchmark is False


def test_benchmark_flagged_canary_members_are_allowed():
    thesis = Thesis.model_validate(
        {
            "schema_version": 1,
            "thesis_id": "benchmark_flag_theme",
            "title": "Benchmark Flag Theme",
            "status": "active",
            "content": {
                "thesis_statement": "A complete thesis statement.",
                "why_this_matters": "It matters for review discipline.",
                "mechanism": "A clear mechanism exists.",
                "time_horizon": "4 to 6 quarters",
            },
            "evidence": {
                "confirmation_signals": ["Something improved"],
                "disconfirming_signals": ["Something weakened"],
                "counter_narrative": "The thesis could still fail.",
            },
            "basket": {"members": [{"ticker": "adbe", "role": "canary", "is_benchmark": True}]},
        }
    )

    assert thesis.basket.members[0].ticker == "ADBE"
    assert thesis.basket.members[0].is_benchmark is True


def test_duplicate_tickers_are_rejected():
    with pytest.raises(ValidationError):
        Thesis.model_validate(
            {
                "schema_version": 1,
                "thesis_id": "duplicate_theme",
                "title": "Duplicate Theme",
                "status": "active",
                "content": {
                    "thesis_statement": "A complete thesis statement.",
                    "why_this_matters": "It matters for review discipline.",
                    "mechanism": "A clear mechanism exists.",
                    "time_horizon": "4 to 6 quarters",
                },
                "evidence": {
                    "confirmation_signals": ["Something improved"],
                    "disconfirming_signals": ["Something weakened"],
                    "counter_narrative": "The thesis could still fail.",
                },
                "basket": {
                    "members": [
                        {"ticker": "VRT", "role": "core", "is_benchmark": True},
                        {"ticker": "VRT", "role": "canary"},
                    ]
                },
            }
        )


def test_remove_members_cannot_also_be_benchmarks():
    with pytest.raises(ValidationError):
        Thesis.model_validate(
            {
                "schema_version": 1,
                "thesis_id": "remove_benchmark_theme",
                "title": "Remove Benchmark Theme",
                "status": "active",
                "content": {
                    "thesis_statement": "A complete thesis statement.",
                    "why_this_matters": "It matters for review discipline.",
                    "mechanism": "A clear mechanism exists.",
                    "time_horizon": "4 to 6 quarters",
                },
                "evidence": {
                    "confirmation_signals": ["Something improved"],
                    "disconfirming_signals": ["Something weakened"],
                    "counter_narrative": "The thesis could still fail.",
                },
                "basket": {
                    "members": [{"ticker": "ORCL", "role": "remove", "is_benchmark": True}]
                },
            }
        )


def test_invalid_status_values_are_rejected():
    with pytest.raises(ValidationError):
        Thesis.model_validate(
            {
                "schema_version": 1,
                "thesis_id": "invalid_status_theme",
                "title": "Invalid Status Theme",
                "status": "paused",
                "content": {"thesis_statement": "A rough idea worth capturing."},
            }
        )
