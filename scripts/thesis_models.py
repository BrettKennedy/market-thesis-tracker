"""Canonical thesis schema and validation helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

ThesisStatus = Literal["draft", "active"]
BasketRole = Literal["benchmark", "core", "torque", "canary", "remove"]

_THESIS_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]*$")


def _normalize_optional_text(value: object) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


def _normalize_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("value must be a list")

    normalized: list[str] = []
    for item in value:
        stripped = str(item).strip()
        if not stripped:
            raise ValueError("list values must not be blank")
        normalized.append(stripped)

    return normalized


class ThesisContent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    thesis_statement: str | None = None
    why_this_matters: str | None = None
    mechanism: str | None = None
    time_horizon: str | None = None

    @field_validator(
        "thesis_statement",
        "why_this_matters",
        "mechanism",
        "time_horizon",
        mode="before",
    )
    @classmethod
    def normalize_optional_fields(cls, value: object) -> str | None:
        return _normalize_optional_text(value)


class ThesisEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    confirmation_signals: list[str] = Field(default_factory=list)
    disconfirming_signals: list[str] = Field(default_factory=list)
    counter_narrative: str | None = None

    @field_validator("confirmation_signals", "disconfirming_signals", mode="before")
    @classmethod
    def normalize_signal_lists(cls, value: object) -> list[str]:
        return _normalize_string_list(value)

    @field_validator("counter_narrative", mode="before")
    @classmethod
    def normalize_counter_narrative(cls, value: object) -> str | None:
        return _normalize_optional_text(value)


class BasketMember(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str
    role: BasketRole
    is_benchmark: bool = False

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: object) -> str:
        ticker = _normalize_optional_text(value)
        if ticker is None:
            raise ValueError("ticker must not be blank")

        normalized = ticker.upper()
        if not _TICKER_PATTERN.fullmatch(normalized):
            raise ValueError("ticker must use a supported symbol format")
        return normalized

    @model_validator(mode="after")
    def validate_role_flags(self) -> BasketMember:
        if self.role == "remove" and self.is_benchmark:
            raise ValueError("remove members cannot also be benchmark names")
        if self.role == "benchmark" and self.is_benchmark:
            raise ValueError("benchmark role should not also set is_benchmark")
        return self


class ThesisBasket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    members: list[BasketMember] = Field(default_factory=list)

    @field_validator("members", mode="before")
    @classmethod
    def normalize_members(cls, value: object) -> list[object]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("members must be a list")
        return value

    @model_validator(mode="after")
    def validate_unique_tickers(self) -> ThesisBasket:
        seen: set[str] = set()
        duplicates: list[str] = []

        for member in self.members:
            if member.ticker in seen:
                duplicates.append(member.ticker)
                continue
            seen.add(member.ticker)

        if duplicates:
            dupes = ", ".join(sorted(set(duplicates)))
            raise ValueError(f"each basket ticker may appear only once: {dupes}")

        return self


class ThesisWorkingNotes(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    research_gaps: list[str] = Field(default_factory=list)
    source_notes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("research_gaps", "source_notes", "tags", mode="before")
    @classmethod
    def normalize_lists(cls, value: object) -> list[str]:
        return _normalize_string_list(value)


class Thesis(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    thesis_id: str
    title: str
    status: ThesisStatus
    content: ThesisContent = Field(default_factory=ThesisContent)
    evidence: ThesisEvidence = Field(default_factory=ThesisEvidence)
    basket: ThesisBasket = Field(default_factory=ThesisBasket)
    working_notes: ThesisWorkingNotes = Field(default_factory=ThesisWorkingNotes)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: int) -> int:
        if value != 1:
            raise ValueError("schema_version must be 1")
        return value

    @field_validator("thesis_id", mode="before")
    @classmethod
    def validate_thesis_id(cls, value: object) -> str:
        thesis_id = _normalize_optional_text(value)
        if thesis_id is None:
            raise ValueError("thesis_id must not be blank")
        if not _THESIS_ID_PATTERN.fullmatch(thesis_id):
            raise ValueError("thesis_id must be lowercase snake_case")
        return thesis_id

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: object) -> str:
        title = _normalize_optional_text(value)
        if title is None:
            raise ValueError("title must not be blank")
        return title

    @model_validator(mode="after")
    def validate_status_requirements(self) -> Thesis:
        missing: list[str] = []

        if not self.content.thesis_statement:
            missing.append("content.thesis_statement")

        if self.status == "active":
            if not self.content.why_this_matters:
                missing.append("content.why_this_matters")
            if not self.content.mechanism:
                missing.append("content.mechanism")
            if not self.content.time_horizon:
                missing.append("content.time_horizon")
            if not self.evidence.confirmation_signals:
                missing.append("evidence.confirmation_signals")
            if not self.evidence.disconfirming_signals:
                missing.append("evidence.disconfirming_signals")
            if not self.evidence.counter_narrative:
                missing.append("evidence.counter_narrative")

            has_benchmark_member = any(
                member.role == "benchmark" or member.is_benchmark for member in self.basket.members
            )
            if not has_benchmark_member:
                missing.append("basket.members (at least one benchmark member)")

        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"{self.status} theses are missing required fields: {joined}")

        return self


def load_thesis(path: Path) -> Thesis:
    """Load and validate a thesis YAML file."""
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    if not isinstance(payload, dict):
        error_message = f"Thesis file {path} must contain a mapping at the top level"
        raise ValidationError.from_exception_data(
            "Thesis",
            [
                {
                    "type": "value_error",
                    "loc": (),
                    "msg": f"Value error, {error_message}",
                    "input": payload,
                    "ctx": {"error": ValueError(error_message)},
                }
            ],
        )

    thesis = Thesis.model_validate(payload)
    if path.suffix in {".yaml", ".yml"} and path.stem != thesis.thesis_id:
        raise ValidationError.from_exception_data(
            "Thesis",
            [
                {
                    "type": "value_error",
                    "loc": ("thesis_id",),
                    "msg": f"Value error, thesis_id must match filename stem '{path.stem}'",
                    "input": thesis.thesis_id,
                    "ctx": {
                        "error": ValueError(
                            f"thesis_id must match filename stem '{path.stem}'"
                        )
                    },
                }
            ],
        )

    return thesis
