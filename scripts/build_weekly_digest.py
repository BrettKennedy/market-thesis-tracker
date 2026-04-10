"""Build a weekly markdown digest from reviews and local SQLite events."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import typer
from config_models import load_positions_config, load_risk_rules, load_ticker_baskets
from data_store import default_db_path, read_events
from jinja2 import Template
from repo_helpers import get_themes_path, get_ticker_baskets_path, load_theme_definitions
from review_helpers import (
    extract_bullets,
    extract_first_meaningful_line,
    extract_section,
    extract_selected_option,
    find_latest_review_for_theme,
)
from rich.console import Console
from utils import dedupe

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]



def summarize_monthly_review(review_path: Path) -> dict[str, object]:
    """Extract digest-friendly content from a monthly review file."""
    text = review_path.read_text(encoding="utf-8")
    strengthened = dedupe(
        extract_bullets(extract_section(text, "### Important New Evidence"))
        + extract_bullets(extract_section(text, "### Confirmation Signals Observed This Month"))
        + extract_bullets(extract_section(text, "## 3) What Still Holds"))
    )
    weakened = dedupe(
        extract_bullets(extract_section(text, "## 4) What Is Weakening"))
        + extract_bullets(extract_section(text, "### Disconfirming Signals Observed This Month"))
    )
    open_questions = dedupe(
        extract_bullets(extract_section(text, "### Evidence That Would Improve the Score"))
        + extract_bullets(extract_section(text, "### Evidence That Would Lower the Score"))
    )

    return {
        "path": review_path,
        "score": extract_first_meaningful_line(extract_section(text, "### Total Score"))
        or "Not scored",
        "stance": extract_selected_option(extract_section(text, "### Current Stance")) or "Not set",
        "judgment": extract_selected_option(extract_section(text, "### Theme-Level Judgment"))
        or "Not set",
        "strengthened": strengthened or ["No strengthening items recorded in latest review."],
        "weakened": weakened or ["No weakening items recorded in latest review."],
        "open_questions": open_questions or ["No explicit next-month evidence tests recorded."],
    }


@app.command()
def main(
    date: str = typer.Option(None, help="Digest date (YYYY-MM-DD). Defaults to today."),
    db_path: Path = typer.Option(
        None, help="Optional SQLite path. Defaults to data/processed/research.db."
    ),
    days: int = typer.Option(14, min=1, max=90, help="How many days of local events to include."),
) -> None:
    """Generate outputs/weekly/weekly_digest_<date>.md."""
    as_of = date or dt.date.today().isoformat()
    output_dir = BASE_DIR / "outputs" / "weekly"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"weekly_digest_{as_of}.md"
    db_path = db_path or default_db_path(BASE_DIR)
    since_date = (dt.date.fromisoformat(as_of) - dt.timedelta(days=days)).isoformat()

    positions = load_positions_config(BASE_DIR / "config" / "positions.yaml")
    risk_rules = load_risk_rules(BASE_DIR / "config" / "risk_rules.yaml")
    baskets = load_ticker_baskets(get_ticker_baskets_path(BASE_DIR))
    theme_definitions = load_theme_definitions(get_themes_path(BASE_DIR))

    theme_rows: list[dict[str, object]] = []
    for theme_name, theme_definition in theme_definitions.items():
        latest_review = find_latest_review_for_theme(BASE_DIR / "reviews" / "monthly", theme_name)
        review_summary = summarize_monthly_review(latest_review) if latest_review else None
        events = read_events(db_path, theme=theme_name, since_date=since_date, limit=8)
        theme_rows.append(
            {
                "theme_name": theme_name,
                "theme_definition": theme_definition,
                "review_summary": review_summary,
                "events": events,
            }
        )

    template = Template(
        """# Weekly Digest ({{ as_of }})

## Operating Context
- Themes tracked: {{ theme_rows | length }}
- Basket config themes: {{ basket_count }}
- Local events window: {{ since_date }} to {{ as_of }}
- Configured positions: {{ positions_count }}
- Thematic sleeve target weight: {{ target_weight }}
- Current cash reserve target / operating value:
  {{ target_cash_reserve }} / {{ current_cash_reserve }}

## Risk Guardrails
- Max core position: {{ risk_rules.max_core_position_pct }}%
- Max torque position: {{ risk_rules.max_torque_position_pct }}%
- New adds require checklist: {{ risk_rules.requires_checklist_before_decision }}
- Primary sources required for material conclusions:
  {{ risk_rules.requires_primary_sources_for_material_conclusions }}

{% for row in theme_rows %}
## Theme: {{ row.theme_name }}

### Canonical Thesis
{{ row.theme_definition.thesis_statement }}

### Latest Monthly Review
{% if row.review_summary %}
- File: {{ row.review_summary.path.name }}
- Score: {{ row.review_summary.score }}
- Current stance: {{ row.review_summary.stance }}
- Theme-level judgment: {{ row.review_summary.judgment }}
{% else %}
- No monthly review on file yet.
{% endif %}

### Strengthened
{% if row.review_summary %}
{% for item in row.review_summary.strengthened %}
- {{ item }}
{% endfor %}
{% else %}
- No strengthening evidence recorded yet.
{% endif %}

### Weakened
{% if row.review_summary %}
{% for item in row.review_summary.weakened %}
- {{ item }}
{% endfor %}
{% else %}
- No weakening evidence recorded yet.
{% endif %}

### Open Questions
{% if row.review_summary %}
{% for item in row.review_summary.open_questions %}
- {{ item }}
{% endfor %}
{% else %}
- No explicit monthly review questions recorded yet.
{% endif %}

### Recent Local Events
{% if row.events %}
{% for event in row.events %}
- [{{ event.event_date }}] {{ event.title }}{% if event.ticker %} ({{ event.ticker }}){% endif %}
{% endfor %}
{% else %}
- No local events in SQLite for this time window.
{% endif %}
{% endfor %}
"""
    )

    markdown = template.render(
        as_of=as_of,
        basket_count=len(baskets),
        current_cash_reserve=positions.thematic_sleeve.cash_reserve_pct
        if positions.thematic_sleeve.cash_reserve_pct is not None
        else "unset",
        positions_count=len(positions.positions),
        risk_rules=risk_rules,
        since_date=since_date,
        target_cash_reserve=risk_rules.target_cash_reserve_pct,
        target_weight=positions.thematic_sleeve.target_weight_pct
        if positions.thematic_sleeve.target_weight_pct is not None
        else "unset",
        theme_rows=theme_rows,
    )

    output_path.write_text(markdown, encoding="utf-8")
    console.print(f"[green]Wrote weekly digest:[/green] {output_path}")


if __name__ == "__main__":
    app()
