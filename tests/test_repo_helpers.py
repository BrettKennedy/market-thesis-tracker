from __future__ import annotations

from repo_helpers import load_canonical_theme_names, load_theme_definitions, normalize_theme_name


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
