"""Validated loaders for repo configuration files."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator


BasketRole = Literal["benchmark", "core", "torque", "canary", "remove"]


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _normalize_ticker(value: str) -> str:
    return value.strip().upper()


class ThemeBasket(BaseModel):
    benchmark: list[str] = Field(default_factory=list)
    core: list[str] = Field(default_factory=list)
    torque: list[str] = Field(default_factory=list)
    canary: list[str] = Field(default_factory=list)
    remove: list[str] = Field(default_factory=list)

    @field_validator("benchmark", "core", "torque", "canary", "remove", mode="before")
    @classmethod
    def normalize_basket_lists(cls, value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise TypeError("basket values must be lists")
        return [_normalize_ticker(str(item)) for item in value]


class ThematicSleeve(BaseModel):
    target_weight_pct: float | None = None
    cash_reserve_pct: float | None = None


class Position(BaseModel):
    ticker: str
    theme: str
    basket_role: BasketRole
    shares: float
    cost_basis: float | None = None
    notes: str | None = None

    @field_validator("ticker")
    @classmethod
    def normalize_position_ticker(cls, value: str) -> str:
        return _normalize_ticker(value)

    @field_validator("theme")
    @classmethod
    def strip_theme(cls, value: str) -> str:
        return value.strip()


class PositionsConfig(BaseModel):
    as_of: str
    base_currency: str
    thematic_sleeve: ThematicSleeve
    positions: list[Position] = Field(default_factory=list)


class RiskRules(BaseModel):
    max_core_position_pct: float
    max_torque_position_pct: float
    max_initial_torque_position_pct: float
    target_cash_reserve_pct: float
    min_cash_reserve_pct: float
    max_cash_reserve_pct: float
    requires_checklist_before_decision: bool
    requires_monthly_theme_review: bool
    requires_post_earnings_review_for_material_changes: bool
    requires_primary_sources_for_material_conclusions: bool


def load_ticker_baskets(path: Path) -> dict[str, ThemeBasket]:
    raw = _load_yaml(path)
    return {str(theme): ThemeBasket.model_validate(payload or {}) for theme, payload in raw.items()}


def load_ticker_theme_map(path: Path) -> dict[str, list[str]]:
    baskets = load_ticker_baskets(path)
    theme_map: dict[str, list[str]] = {}

    for theme_name, basket in baskets.items():
        for ticker in basket.benchmark + basket.core + basket.torque + basket.canary + basket.remove:
            theme_map.setdefault(ticker, [])
            if theme_name not in theme_map[ticker]:
                theme_map[ticker].append(theme_name)

    return theme_map


def load_tracked_tickers(path: Path) -> list[str]:
    return sorted(load_ticker_theme_map(path))


def load_positions_config(path: Path) -> PositionsConfig:
    return PositionsConfig.model_validate(_load_yaml(path))


def load_risk_rules(path: Path) -> RiskRules:
    return RiskRules.model_validate(_load_yaml(path))
