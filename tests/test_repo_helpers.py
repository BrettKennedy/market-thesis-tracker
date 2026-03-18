from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest
import typer

from repo_helpers import (
    http_get_with_retry,
    load_canonical_theme_names,
    load_theme_definitions,
    normalize_theme_name,
    validate_date_str,
)


def test_normalize_theme_name_accepts_canonical_and_heading_forms(repo_root):
    themes_path = repo_root / "tests" / "fixtures" / "themes.md"

    assert normalize_theme_name("AI Infrastructure Buildout Is Durable", themes_path) == (
        "AI Infrastructure Buildout Is Durable"
    )
    assert normalize_theme_name("## Theme 2: SaaS Shakeout Is Real but Selective", themes_path) == (
        "SaaS Shakeout Is Real but Selective"
    )


def test_load_theme_definitions_extracts_thesis_text(repo_root):
    themes_path = repo_root / "tests" / "fixtures" / "themes.md"
    names = load_canonical_theme_names(themes_path)
    definitions = load_theme_definitions(themes_path)

    assert names == [
        "AI Infrastructure Buildout Is Durable",
        "SaaS Shakeout Is Real but Selective",
    ]
    assert definitions["AI Infrastructure Buildout Is Durable"].benchmark == ["VRT", "ANET", "ETN"]
    assert definitions["SaaS Shakeout Is Real but Selective"].thesis_statement.startswith(
        "Over the next 4 to 6 quarters, AI does not break software broadly."
    )


def test_validate_date_str_accepts_valid_date():
    assert validate_date_str("2026-03-10") == "2026-03-10"


def test_validate_date_str_rejects_invalid_date():
    with pytest.raises(typer.BadParameter, match="Invalid date"):
        validate_date_str("not-a-date")


def test_validate_date_str_rejects_partial_date():
    with pytest.raises(typer.BadParameter, match="Invalid date"):
        validate_date_str("2026-13-01")


def test_http_get_with_retry_succeeds_on_first_attempt():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    client = MagicMock()
    client.get.return_value = mock_response

    result = http_get_with_retry(client, "https://example.com", backoff_base=0.0)

    assert result is mock_response
    assert client.get.call_count == 1


@patch("repo_helpers.time.sleep")
def test_http_get_with_retry_retries_on_connect_error(mock_sleep):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    client = MagicMock()
    client.get.side_effect = [
        httpx.ConnectError("connection refused"),
        mock_response,
    ]

    result = http_get_with_retry(client, "https://example.com", backoff_base=0.1)

    assert result is mock_response
    assert client.get.call_count == 2
    mock_sleep.assert_called_once()


@patch("repo_helpers.time.sleep")
def test_http_get_with_retry_raises_after_max_attempts(mock_sleep):
    client = MagicMock()
    client.get.side_effect = httpx.TimeoutException("timed out")

    with pytest.raises(httpx.TimeoutException):
        http_get_with_retry(client, "https://example.com", max_attempts=3, backoff_base=0.0)

    assert client.get.call_count == 3


def test_http_get_with_retry_does_not_retry_http_status_error():
    mock_response = MagicMock()
    mock_request = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404", request=mock_request, response=mock_response
    )
    client = MagicMock()
    client.get.return_value = mock_response

    with pytest.raises(httpx.HTTPStatusError):
        http_get_with_retry(client, "https://example.com")

    assert client.get.call_count == 1
