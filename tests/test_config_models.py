from __future__ import annotations

from config_models import (
    load_positions_config,
    load_risk_rules,
    load_ticker_baskets,
    load_ticker_theme_map,
)


def test_repo_configs_parse(repo_root):
    baskets = load_ticker_baskets(repo_root / "config" / "Ticker_Baskets.yaml")
    positions = load_positions_config(repo_root / "config" / "positions.yaml")
    risk_rules = load_risk_rules(repo_root / "config" / "risk_rules.yaml")

    assert "AI Infrastructure Buildout Is Durable" in baskets
    assert baskets["AI Infrastructure Buildout Is Durable"].core == ["VRT", "ETN", "ANET", "PWR"]
    assert positions.positions == []
    assert positions.thematic_sleeve.cash_reserve_pct == 30.0
    assert risk_rules.max_core_position_pct == 5.0
    assert risk_rules.requires_primary_sources_for_material_conclusions is True


def test_ticker_theme_map_uses_canonical_theme_names(repo_root):
    theme_map = load_ticker_theme_map(repo_root / "config" / "Ticker_Baskets.yaml")

    assert theme_map["VRT"] == ["AI Infrastructure Buildout Is Durable"]
    assert theme_map["NOW"] == ["SaaS Shakeout Is Real but Selective"]
