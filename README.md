# Market Thesis Tracker

Local-first thematic investing research system focused on thesis discipline, review quality, and clear audit trails.

This repository is for research and decision support. It is not a trading bot.

Start with [docs/User_Guide.md](docs/User_Guide.md) for day-to-day usage and [docs/Review_Workflow.md](docs/Review_Workflow.md) for the operating cadence.

## Current State

The repo currently has two active layers:

- Thesis intake layer:
  - `scripts/new_thesis.py` creates thesis drafts in `theses/*.yaml`
  - `scripts/thesis_models.py` and `docs/Thesis_Schema.md` define the canonical thesis schema
- Review and reporting layer:
  - current review, ingestion, and reporting scripts still read `themes/themes.md` and `config/ticker_baskets.yaml`
  - review generators still write into `reviews/` from `templates/`

That split matters. Saving a thesis YAML file does not automatically update the legacy theme and basket files yet. If a thesis should drive the current review or reporting workflow, mirror the accepted changes into `themes/themes.md` and `config/ticker_baskets.yaml`.

## Quick Start

Set up the local environment:

```bash
uv sync
uv run pre-commit install
```

Then choose the workflow you need.

### Thesis Intake

Create a manual thesis draft:

```bash
uv run python scripts/new_thesis.py --no-use-ai
```

Preview without writing:

```bash
uv run python scripts/new_thesis.py --no-use-ai --dry-run
```

Use AI normalization with a local-only API key:

```bash
export MARKET_THESIS_OPENAI_API_KEY="your-local-key"
uv run python scripts/new_thesis.py --use-ai
```

The script also accepts `OPENAI_TOKEN_MARKET_THESIS` as a local fallback env var. Never commit either key, put it in tracked config, or include it in docs, tests, fixtures, or GitHub comments.

Useful intake flags:

- `--target-status draft|active`
- `--dry-run`
- `--yes`
- `--overwrite`
- `--output-dir <PATH>`

### Review And Reporting

If you want the current review and reporting scripts to work end to end, set up the legacy runtime inputs:

- replace the starter content in `themes/themes.md`
- align `config/ticker_baskets.yaml` to those exact theme names
- review `config/risk_rules.yaml`
- update `config/positions.yaml` or leave `positions: []` until funded

Then generate the review documents you need:

```bash
uv run python scripts/new_monthly_review.py --theme "<Theme Name>"
uv run python scripts/new_earnings_review.py --ticker <TICKER> --theme "<Theme Name>"
uv run python scripts/new_decision_review.py --ticker <TICKER> --theme "<Theme Name>" --decision-type Add
```

## Canonical Files Today

These are the main files to treat as source-of-truth today, grouped by role.

### Thesis Intake Canonical Files

- `theses/*.yaml`
- `scripts/thesis_models.py`
- `docs/Thesis_Schema.md`

### Review And Reporting Canonical Files

- `docs/README_Project_Goal.md`
- `docs/Investment_Policy.md`
- `themes/themes.md`
- `config/ticker_baskets.yaml`
- `config/positions.yaml`
- `config/risk_rules.yaml`
- `reviews/decisions/Prediction_Log.md`
- `templates/Monthly_Theme_Review_Template.md`
- `templates/Company_Earnings_Scorecard_Template.md`
- `templates/Decision_Checklist.md`

## Core Commands

Use `uv run python ...` from repo root.

```bash
uv run python scripts/new_thesis.py --no-use-ai
uv run python scripts/new_thesis.py --use-ai --target-status draft
uv run python scripts/new_monthly_review.py --theme "<Theme Name>"
uv run python scripts/new_earnings_review.py --ticker <TICKER> --theme "<Theme Name>"
uv run python scripts/new_decision_review.py --ticker <TICKER> --theme "<Theme Name>" --decision-type Add
uv run python scripts/ingest_news.py --feed https://www.sec.gov/news/pressreleases.rss --limit 5
MARKET_THESIS_SEC_USER_AGENT="market-thesis-tracker/0.1 your-email@example.com" uv run python scripts/ingest_sec.py --ticker <TICKER> --limit 5
uv run python scripts/build_weekly_digest.py
uv run python scripts/build_post_earnings.py --ticker <TICKER>
uv run python scripts/narrative_drift.py
```

## Repository Structure

```text
config/                 Portfolio, risk, and legacy basket inputs
theses/                 Canonical thesis draft files
themes/                 Legacy theme statements used by current runtime scripts
templates/              Canonical review and checklist templates
reviews/
  monthly/              Monthly theme reviews created from template
  earnings/             Post-earnings reviews created from template
  decisions/            Decision checklists and prediction log
prompts/                Reusable prompt text for LLM-assisted synthesis
scripts/                Local automation scripts
data/
  raw/                  Raw fetched inputs
  processed/            Local SQLite DB and derived datasets
outputs/                Generated markdown summaries
docs/                   Policy, workflow, and schema documentation
```

## Using ChatGPT Projects And Codex

Good collaboration patterns:

- point the model at the exact canonical files you want used
- require explicit disconfirming evidence and source references
- keep generated summaries in `outputs/` unless you are intentionally editing canonical files
- remember that `theses/*.yaml` and `themes/themes.md` are not auto-synced yet

Example prompt:

```text
Read theses/ai_infrastructure_buildout_is_durable.yaml, themes/themes.md,
config/ticker_baskets.yaml, and docs/Investment_Policy.md. Help me draft a
review update without inventing facts or changing tickers that are not already
in the repo.
```

## Local Validation

```bash
uv run pytest
uv run pre-commit run --all-files
```

## Intentionally Out Of Scope

- trade execution and broker APIs
- hidden ranking or scoring engines
- always-on workflow infrastructure
- frontend apps, agent frameworks, or deployment-heavy stacks
