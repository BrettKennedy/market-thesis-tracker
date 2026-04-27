"""AI-assisted thesis normalization helpers."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
)
from thesis_models import Thesis, ThesisStatus

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
OPENAI_API_KEY_ENV_VARS = (
    "MARKET_THESIS_OPENAI_API_KEY",
    "OPENAI_TOKEN_MARKET_THESIS",
)


class ProviderConfigError(ValueError):
    """Raised when local provider configuration is missing or invalid."""


class OpenAIResponsesConfig(BaseModel):
    """Secret-safe runtime config for OpenAI Responses API usage."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    api_key: SecretStr
    model: str = DEFAULT_OPENAI_MODEL
    base_url: str = DEFAULT_OPENAI_BASE_URL
    timeout_seconds: float = 60.0

    @field_validator("model", "base_url", mode="before")
    @classmethod
    def require_non_empty_text(cls, value: object) -> str:
        text = str(value).strip() if value is not None else ""
        if not text:
            raise ValueError("value must not be blank")
        return text

    @classmethod
    def from_env(cls) -> OpenAIResponsesConfig:
        api_key = ""
        for env_var in OPENAI_API_KEY_ENV_VARS:
            api_key = os.getenv(env_var, "").strip()
            if api_key:
                break
        if not api_key:
            raise ProviderConfigError(
                "Missing OpenAI API key. Set MARKET_THESIS_OPENAI_API_KEY or "
                "OPENAI_TOKEN_MARKET_THESIS locally in your shell or .env; "
                "never commit it to the repo."
            )

        model = os.getenv("MARKET_THESIS_OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip()
        base_url = os.getenv("MARKET_THESIS_OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL).strip()
        timeout_raw = os.getenv("MARKET_THESIS_OPENAI_TIMEOUT_SECONDS", "60").strip()

        try:
            timeout_seconds = float(timeout_raw)
        except ValueError as exc:
            raise ProviderConfigError(
                "MARKET_THESIS_OPENAI_TIMEOUT_SECONDS must be a number if set."
            ) from exc

        return cls(
            api_key=SecretStr(api_key),
            model=model,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )


class NormalizedContent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    thesis_statement: str = ""
    why_this_matters: str = ""
    mechanism: str = ""
    time_horizon: str = ""


class NormalizedEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    confirmation_signals: list[str] = Field(default_factory=list)
    disconfirming_signals: list[str] = Field(default_factory=list)
    counter_narrative: str = ""


class NormalizedBasketMember(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str
    role: str
    is_benchmark: bool = False


class NormalizedBasket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    members: list[NormalizedBasketMember] = Field(default_factory=list)


class NormalizedWorkingNotes(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    research_gaps: list[str] = Field(default_factory=list)
    source_notes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class NormalizedThesisDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str
    status: ThesisStatus
    content: NormalizedContent
    evidence: NormalizedEvidence
    basket: NormalizedBasket
    working_notes: NormalizedWorkingNotes


NORMALIZED_THESIS_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "status": {"type": "string", "enum": ["draft", "active"]},
        "content": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "thesis_statement": {"type": "string"},
                "why_this_matters": {"type": "string"},
                "mechanism": {"type": "string"},
                "time_horizon": {"type": "string"},
            },
            "required": [
                "thesis_statement",
                "why_this_matters",
                "mechanism",
                "time_horizon",
            ],
        },
        "evidence": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "confirmation_signals": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "disconfirming_signals": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "counter_narrative": {"type": "string"},
            },
            "required": [
                "confirmation_signals",
                "disconfirming_signals",
                "counter_narrative",
            ],
        },
        "basket": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "members": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "ticker": {"type": "string"},
                            "role": {
                                "type": "string",
                                "enum": ["benchmark", "core", "torque", "canary", "remove"],
                            },
                            "is_benchmark": {"type": "boolean"},
                        },
                        "required": ["ticker", "role", "is_benchmark"],
                    },
                }
            },
            "required": ["members"],
        },
        "working_notes": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "research_gaps": {"type": "array", "items": {"type": "string"}},
                "source_notes": {"type": "array", "items": {"type": "string"}},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["research_gaps", "source_notes", "tags"],
        },
    },
    "required": [
        "title",
        "status",
        "content",
        "evidence",
        "basket",
        "working_notes",
    ],
}


def _extract_output_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text":
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    return text
            if content.get("type") == "refusal":
                refusal = content.get("refusal") or content.get("text") or "Request refused."
                raise RuntimeError(f"OpenAI refused the normalization request: {refusal}")

    raise RuntimeError("OpenAI response did not include any structured output text.")


def build_openai_normalization_payload(
    *,
    prompt_text: str,
    model: str,
    target_status: ThesisStatus,
) -> dict[str, Any]:
    return {
        "model": model,
        "instructions": (
            "You are helping convert an operator's rough market-thesis intake interview into a "
            "structured thesis draft JSON object. You may sharpen phrasing and organize the "
            "thinking, but you must not claim external facts or add specific tickers that the "
            "operator did not mention. Keep uncertainty visible by returning empty strings or "
            "empty arrays when the interview does not justify more specificity. Return JSON only."
        ),
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"Target thesis status: {target_status}\n\n"
                            "Normalize the following interview into the required JSON schema.\n\n"
                            f"{prompt_text}"
                        ),
                    }
                ],
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "normalized_thesis_draft",
                "description": "A structured thesis draft produced from an intake interview.",
                "schema": NORMALIZED_THESIS_JSON_SCHEMA,
                "strict": True,
            }
        },
    }


def normalize_interview_with_openai(
    *,
    prompt_text: str,
    target_status: ThesisStatus,
    config: OpenAIResponsesConfig | None = None,
    http_client: httpx.Client | None = None,
) -> NormalizedThesisDraft:
    resolved_config = config or OpenAIResponsesConfig.from_env()
    payload = build_openai_normalization_payload(
        prompt_text=prompt_text,
        model=resolved_config.model,
        target_status=target_status,
    )
    headers = {
        "Authorization": f"Bearer {resolved_config.api_key.get_secret_value()}",
        "Content-Type": "application/json",
    }
    url = f"{resolved_config.base_url.rstrip('/')}/responses"

    if http_client is not None:
        response = http_client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()
    else:
        with httpx.Client(timeout=resolved_config.timeout_seconds) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()

    output_text = _extract_output_text(body)

    try:
        data = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenAI returned non-JSON structured output.") from exc

    try:
        return NormalizedThesisDraft.model_validate(data)
    except ValidationError as exc:
        raise RuntimeError(
            "OpenAI returned JSON that did not match the expected draft shape."
        ) from exc


def normalized_draft_to_thesis(
    *,
    normalized: NormalizedThesisDraft,
    thesis_id: str,
    target_status: ThesisStatus,
    basket_members: list[dict[str, object]] | None = None,
) -> Thesis:
    resolved_basket_members = basket_members
    if resolved_basket_members is None:
        resolved_basket_members = []
        for member in normalized.basket.members:
            role = member.role
            is_benchmark = member.is_benchmark
            if role == "benchmark":
                is_benchmark = False

            resolved_basket_members.append(
                {
                    "ticker": member.ticker,
                    "role": role,
                    "is_benchmark": is_benchmark,
                }
            )

    return Thesis.model_validate(
        {
            "schema_version": 1,
            "thesis_id": thesis_id,
            "title": normalized.title,
            "status": target_status,
            "content": normalized.content.model_dump(),
            "evidence": normalized.evidence.model_dump(),
            "basket": {"members": resolved_basket_members},
            "working_notes": normalized.working_notes.model_dump(),
        }
    )
