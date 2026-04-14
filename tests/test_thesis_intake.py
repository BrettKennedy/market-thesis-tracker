from __future__ import annotations

import json
from pathlib import Path

import new_thesis
import pytest
import thesis_ai
import typer
from thesis_models import Thesis


def sample_interview() -> dict[str, object]:
    return {
        "title": "Cloud Security Consolidation",
        "rough_idea": "Security budgets consolidate toward platforms.",
        "why_this_matters": "It changes which software names deserve attention.",
        "mechanism": "Platform consolidation compresses standalone feature premiums.",
        "time_horizon": "4 to 6 quarters",
        "confirmation_signals": ["Large platforms keep winning bundles"],
        "disconfirming_signals": ["Point solutions reaccelerate together"],
        "counter_narrative": "Best-of-breed vendors keep their edge.",
        "benchmark": ["PANW"],
        "core": ["PANW", "CRWD"],
        "torque": ["ZS"],
        "canary": ["S"],
        "remove": [],
        "research_gaps": ["Check if bundle wins are durable"],
        "tags": ["security", "software"],
    }


def test_make_thesis_id_normalizes_titles():
    assert new_thesis.make_thesis_id("AI Infrastructure Buildout Is Durable") == (
        "ai_infrastructure_buildout_is_durable"
    )
    assert new_thesis.make_thesis_id("2026 Energy Rotation") == "thesis_2026_energy_rotation"


def test_merge_bucket_members_marks_investable_benchmarks_once():
    members = new_thesis._merge_bucket_members(
        benchmark=["PANW", "QQQ"],
        core=["PANW", "CRWD"],
        torque=["ZS"],
        canary=["S"],
        remove=[],
    )

    by_ticker = {member["ticker"]: member for member in members}
    assert by_ticker["PANW"] == {"ticker": "PANW", "role": "core", "is_benchmark": True}
    assert by_ticker["QQQ"] == {"ticker": "QQQ", "role": "benchmark", "is_benchmark": False}


def test_merge_bucket_members_rejects_conflicting_non_benchmark_roles():
    with pytest.raises(ValueError):
        new_thesis._merge_bucket_members(
            benchmark=[],
            core=["PANW"],
            torque=["PANW"],
            canary=[],
            remove=[],
        )


def test_build_manual_thesis_returns_valid_thesis():
    thesis = new_thesis.build_manual_thesis(sample_interview(), target_status="draft")

    assert isinstance(thesis, Thesis)
    assert thesis.thesis_id == "cloud_security_consolidation"
    assert thesis.status == "draft"
    assert any(member.is_benchmark for member in thesis.basket.members)


def test_openai_config_requires_local_env_key(monkeypatch):
    monkeypatch.delenv("MARKET_THESIS_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_TOKEN_MARKET_THESIS", raising=False)

    with pytest.raises(thesis_ai.ProviderConfigError):
        thesis_ai.OpenAIResponsesConfig.from_env()


def test_openai_config_reads_env(monkeypatch):
    monkeypatch.setenv("MARKET_THESIS_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("MARKET_THESIS_OPENAI_MODEL", "gpt-4o-mini")
    config = thesis_ai.OpenAIResponsesConfig.from_env()

    assert config.model == "gpt-4o-mini"
    assert config.api_key.get_secret_value() == "test-key"


def test_openai_config_reads_fallback_env(monkeypatch):
    monkeypatch.delenv("MARKET_THESIS_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_TOKEN_MARKET_THESIS", "fallback-key")

    config = thesis_ai.OpenAIResponsesConfig.from_env()

    assert config.api_key.get_secret_value() == "fallback-key"


class FakeResponse:
    def __init__(self, payload: dict[str, object]):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


class FakeClient:
    def __init__(self, payload: dict[str, object]):
        self.payload = payload
        self.calls: list[dict[str, object]] = []

    def post(self, url: str, *, headers: dict[str, str], json: dict[str, object]) -> FakeResponse:
        self.calls.append({"url": url, "headers": headers, "json": json})
        return FakeResponse(self.payload)


def test_normalize_interview_with_openai_parses_structured_output():
    response_payload = {
        "output_text": json.dumps(
            {
                "title": "Cloud Security Consolidation",
                "status": "draft",
                "content": {
                    "thesis_statement": "Security budgets consolidate toward platforms.",
                    "why_this_matters": "It changes which software names deserve attention.",
                    "mechanism": "Platform consolidation compresses standalone feature premiums.",
                    "time_horizon": "4 to 6 quarters",
                },
                "evidence": {
                    "confirmation_signals": ["Large platforms keep winning bundles"],
                    "disconfirming_signals": ["Point solutions reaccelerate together"],
                    "counter_narrative": "Best-of-breed vendors keep their edge.",
                },
                "basket": {
                    "members": [
                        {"ticker": "PANW", "role": "core", "is_benchmark": True},
                        {"ticker": "CRWD", "role": "core", "is_benchmark": False},
                    ]
                },
                "working_notes": {
                    "research_gaps": ["Check if bundle wins are durable"],
                    "source_notes": ["AI-normalized from operator interview"],
                    "tags": ["security", "software"],
                },
            }
        )
    }
    fake_client = FakeClient(response_payload)
    config = thesis_ai.OpenAIResponsesConfig(
        api_key="test-key",
        model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        timeout_seconds=30.0,
    )

    normalized = thesis_ai.normalize_interview_with_openai(
        prompt_text='{"operator_interview": "test"}',
        target_status="draft",
        config=config,
        http_client=fake_client,
    )

    assert normalized.title == "Cloud Security Consolidation"
    assert fake_client.calls[0]["url"] == "https://api.openai.com/v1/responses"
    assert fake_client.calls[0]["json"]["text"]["format"]["type"] == "json_schema"


def test_normalized_draft_to_thesis_coerces_benchmark_role_flags():
    normalized = thesis_ai.NormalizedThesisDraft.model_validate(
        {
            "title": "Grid Modernization Compounds",
            "status": "draft",
            "content": {
                "thesis_statement": "Grid spending stays durable.",
                "why_this_matters": "It affects which infrastructure names matter.",
                "mechanism": "Utilities need physical upgrades.",
                "time_horizon": "4 to 6 quarters",
            },
            "evidence": {
                "confirmation_signals": ["Capex plans rise"],
                "disconfirming_signals": ["Capex plans get cut"],
                "counter_narrative": "Spending proves lumpy.",
            },
            "basket": {
                "members": [
                    {"ticker": "ETN", "role": "benchmark", "is_benchmark": True},
                    {"ticker": "HUBB", "role": "core", "is_benchmark": True},
                ]
            },
            "working_notes": {
                "research_gaps": [],
                "source_notes": [],
                "tags": [],
            },
        }
    )

    thesis = thesis_ai.normalized_draft_to_thesis(
        normalized=normalized,
        thesis_id="grid_modernization_compounds",
    )

    assert thesis.basket.members[0].role == "benchmark"
    assert thesis.basket.members[0].is_benchmark is False
    assert thesis.basket.members[1].is_benchmark is True


def test_new_thesis_main_writes_manual_draft(monkeypatch, temp_repo: Path):
    monkeypatch.setattr(new_thesis, "BASE_DIR", temp_repo)
    monkeypatch.setattr(new_thesis, "conduct_thesis_interview", lambda: sample_interview())
    monkeypatch.setattr(new_thesis.typer, "confirm", lambda *args, **kwargs: True)

    new_thesis.main(
        use_ai=False,
        target_status="draft",
        output_dir=None,
        overwrite=False,
        yes=False,
        dry_run=False,
    )

    output_path = temp_repo / "theses" / "cloud_security_consolidation.yaml"
    text = output_path.read_text(encoding="utf-8")

    assert output_path.exists()
    assert "cloud_security_consolidation" in text
    assert "Generated from the thesis intake interview without AI normalization." in text


def test_new_thesis_main_can_write_ai_normalized_draft(monkeypatch, temp_repo: Path):
    monkeypatch.setattr(new_thesis, "BASE_DIR", temp_repo)
    monkeypatch.setattr(new_thesis, "conduct_thesis_interview", lambda: sample_interview())
    monkeypatch.setattr(new_thesis.typer, "confirm", lambda *args, **kwargs: True)

    ai_thesis = Thesis.model_validate(
        {
            "schema_version": 1,
            "thesis_id": "cloud_security_consolidation",
            "title": "Cloud Security Consolidation",
            "status": "draft",
            "content": {
                "thesis_statement": "Security budgets consolidate toward platforms.",
                "why_this_matters": "It changes which software names deserve attention.",
                "mechanism": "Platform consolidation compresses standalone feature premiums.",
                "time_horizon": "4 to 6 quarters",
            },
            "evidence": {
                "confirmation_signals": ["Large platforms keep winning bundles"],
                "disconfirming_signals": ["Point solutions reaccelerate together"],
                "counter_narrative": "Best-of-breed vendors keep their edge.",
            },
            "basket": {
                "members": [
                    {"ticker": "PANW", "role": "core", "is_benchmark": True},
                    {"ticker": "CRWD", "role": "core", "is_benchmark": False},
                ]
            },
            "working_notes": {
                "research_gaps": ["Check if bundle wins are durable"],
                "source_notes": ["AI-normalized from the thesis intake interview."],
                "tags": ["security", "software"],
            },
        }
    )
    monkeypatch.setattr(new_thesis, "build_ai_thesis", lambda interview, target_status: ai_thesis)

    new_thesis.main(
        use_ai=True,
        target_status="draft",
        output_dir=None,
        overwrite=False,
        yes=False,
        dry_run=False,
    )

    output_path = temp_repo / "theses" / "cloud_security_consolidation.yaml"
    assert output_path.exists()


def test_new_thesis_main_honors_dry_run(monkeypatch, temp_repo: Path):
    monkeypatch.setattr(new_thesis, "BASE_DIR", temp_repo)
    monkeypatch.setattr(new_thesis, "conduct_thesis_interview", lambda: sample_interview())

    new_thesis.main(
        use_ai=False,
        target_status="draft",
        output_dir=None,
        overwrite=False,
        yes=True,
        dry_run=True,
    )

    output_path = temp_repo / "theses" / "cloud_security_consolidation.yaml"
    assert not output_path.exists()


def test_new_thesis_main_rejects_overwrite_without_flag(monkeypatch, temp_repo: Path):
    monkeypatch.setattr(new_thesis, "BASE_DIR", temp_repo)
    monkeypatch.setattr(new_thesis, "conduct_thesis_interview", lambda: sample_interview())

    new_thesis.main(
        use_ai=False,
        target_status="draft",
        output_dir=None,
        overwrite=False,
        yes=True,
        dry_run=False,
    )

    with pytest.raises(typer.Exit):
        new_thesis.main(
            use_ai=False,
            target_status="draft",
            output_dir=None,
            overwrite=False,
            yes=True,
            dry_run=False,
        )
