from __future__ import annotations

from config_models import (
    load_positions_config,
    load_risk_rules,
    load_ticker_baskets,
    load_ticker_theme_map,
)


def test_repo_configs_parse(repo_root):
    baskets = load_ticker_baskets(repo_root / "config" / "ticker_baskets.yaml")
    positions = load_positions_config(repo_root / "config" / "positions.yaml")
    risk_rules = load_risk_rules(repo_root / "config" / "risk_rules.yaml")

    assert "Replace With Your First Theme Name" in baskets
    assert baskets["Replace With Your First Theme Name"].benchmark == ["TICKER"]
    assert positions.positions == []
    assert positions.thematic_sleeve.cash_reserve_pct == 30.0
    assert risk_rules.max_core_position_pct == 5.0
    assert risk_rules.requires_primary_sources_for_material_conclusions is True


def test_ticker_theme_map_uses_canonical_theme_names(temp_repo):
    theme_map = load_ticker_theme_map(temp_repo / "config" / "ticker_baskets.yaml")

    assert theme_map["VRT"] == ["AI Infrastructure Buildout Is Durable"]
    assert theme_map["NOW"] == ["SaaS Shakeout Is Real but Selective"]
