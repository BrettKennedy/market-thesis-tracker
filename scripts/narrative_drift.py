"""Create a deterministic narrative-drift audit from local review files."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import typer
from rich.console import Console

from repo_helpers import ThemeDefinition, get_themes_path, load_theme_definitions
from review_helpers import (
    extract_bullets,
    extract_first_meaningful_line,
    extract_selected_option,
    extract_section,
    find_latest_review_for_theme,
    has_heading,
)

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]


def audit_monthly_review(theme_definition: ThemeDefinition, review_path: Path | None) -> list[str]:
    """Return deterministic findings for one theme's latest monthly review."""
    if review_path is None:
        return ["Missing monthly review file."]

    text = review_path.read_text(encoding="utf-8")
    findings: list[str] = []
    required_headings = [
        "### Thesis Statement",
        "### Strongest Counter-Narrative",
        "### Disconfirming Signals Observed This Month",
        "### Evidence That Would Lower the Score",
    ]
    for heading in required_headings:
        if not has_heading(text, heading):
            findings.append(f"Missing required heading: {heading}")

    thesis_statement = extract_first_meaningful_line(extract_section(text, "### Thesis Statement"))
    if thesis_statement != theme_definition.thesis_statement:
        findings.append("Thesis statement differs from canonical theme text.")

    counter_narrative = extract_first_meaningful_line(
        extract_section(text, "### Strongest Counter-Narrative")
    )
    if not counter_narrative:
        findings.append("Strongest counter-narrative is missing or left as a placeholder.")

    disconfirming_signals = extract_bullets(
        extract_section(text, "### Disconfirming Signals Observed This Month")
    )
    if not disconfirming_signals:
        findings.append("No disconfirming evidence was recorded in the review.")

    score = extract_first_meaningful_line(extract_section(text, "### Total Score"))
    if not score:
        findings.append("Total score is missing.")

    return findings


def audit_earnings_review(review_path: Path) -> list[str]:
    """Return deterministic findings for one earnings review."""
    text = review_path.read_text(encoding="utf-8")
    findings: list[str] = []
    required_headings = [
        "### One-Sentence Bottom Line",
        "### What This Quarter Says About the Theme",
        "### Current Role After the Print Should Be",
        "### Judgment",
    ]
    for heading in required_headings:
        if not has_heading(text, heading):
            findings.append(f"Missing required heading: {heading}")

    if not extract_first_meaningful_line(extract_section(text, "### One-Sentence Bottom Line")):
        findings.append("One-sentence bottom line is missing.")

    if not extract_selected_option(
        extract_section(text, "### What This Quarter Says About the Theme")
    ):
        findings.append("Theme read-through was not selected.")

    if not extract_selected_option(extract_section(text, "### Judgment")):
        findings.append("Capital action judgment was not selected.")

    anti_bias = extract_selected_option(
        extract_section(
            text,
            "### Did I identify at least one piece of evidence that cuts against my preferred view?",
        )
    )
    if not anti_bias:
        findings.append("Anti-bias check is incomplete.")

    return findings


@app.command()
def main(
    date: str = typer.Option(None, help="Audit date (YYYY-MM-DD). Defaults to today."),
) -> None:
    """Generate outputs/narrative_drift_<date>.md."""
    as_of = date or dt.date.today().isoformat()
    theme_definitions = load_theme_definitions(get_themes_path(BASE_DIR))
    earnings_reviews = sorted((BASE_DIR / "reviews" / "earnings").glob("*.md"))

    output_path = BASE_DIR / "outputs" / f"narrative_drift_{as_of}.md"
    output = f"""# Narrative Drift Audit ({as_of})

## Monthly Review Checks
"""

    for theme_name, theme_definition in theme_definitions.items():
        review_path = find_latest_review_for_theme(BASE_DIR / "reviews" / "monthly", theme_name)
        findings = audit_monthly_review(theme_definition, review_path)
        output += f"\n### {theme_name}\n"
        output += f"- Latest file: {review_path.name if review_path else 'missing'}\n"
        if findings:
            for finding in findings:
                output += f"- Finding: {finding}\n"
        else:
            output += "- Result: no drift findings in latest monthly review.\n"

    output += f"""

## Earnings Review Checks
- Earnings reviews found: {len(earnings_reviews)}
"""

    for review_path in earnings_reviews[-10:]:
        findings = audit_earnings_review(review_path)
        output += f"\n### {review_path.name}\n"
        if findings:
            for finding in findings:
                output += f"- Finding: {finding}\n"
        else:
            output += "- Result: no audit findings in this earnings review.\n"

    output_path.write_text(output, encoding="utf-8")
    console.print(f"[green]Wrote narrative drift audit:[/green] {output_path}")


if __name__ == "__main__":
    app()
