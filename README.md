# Market Thesis Tracker

Local-first thematic investing research system focused on decision discipline.

This repository is for research, review cadence, and narrative tracking. It is **not** a trading bot.

Start with [docs/User_Guide.md](docs/User_Guide.md) for day-to-day usage and [docs/Review_Workflow.md](docs/Review_Workflow.md) for the operating cadence.

## Purpose

- Track durable market themes and supporting evidence.
- Keep basket definitions consistent and reviewable.
- Improve judgment quality through repeatable review templates.
- Log predictions and decision rationale for later calibration.

## Canonical Files

These are the source-of-truth artifacts for this system:

- `docs/README_Project_Goal.md`
- `docs/Investment_Policy.md`
- `themes/Themes.md`
- `config/Ticker_Baskets.yaml`
- `reviews/decisions/Prediction_Log.md`
- `templates/Monthly_Theme_Review_Template.md`
- `templates/Company_Earnings_Scorecard_Template.md`
- `templates/Decision_Checklist.md`

## Repository Structure

```text
config/                 Portfolio/risk configs and ticker baskets
themes/                 Current theme statements and evidence definitions
templates/              Canonical review/checklist templates
reviews/
  monthly/              Monthly theme reviews created from template
  earnings/             Post-earnings reviews created from template
  decisions/            Decision checklists and prediction log
prompts/                Reusable prompt text for LLM-assisted synthesis
scripts/                Thin local automation scripts (no scheduling/brokers)
data/
  raw/                  Raw fetched inputs (local files)
  processed/            Local SQLite DB and derived datasets
outputs/                Generated markdown reports (ignored in git)
docs/                   Goals, policy, and workflow documentation
```

## Local Setup (uv)

1. Install `uv` if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create/sync environment:

```bash
uv sync
```

3. Install git hooks:

```bash
uv run pre-commit install
```

4. Validate the local setup:

```bash
uv run pytest
uv run pre-commit run --all-files
```

## Running Core Scripts

Use `uv run python ...` from repo root.

```bash
uv run python scripts/ingest_news.py --feed https://www.sec.gov/news/pressreleases.rss --limit 5
MARKET_THESIS_SEC_USER_AGENT="market-thesis-tracker/0.1 your-email@example.com" uv run python scripts/ingest_sec.py --ticker VRT --limit 5
uv run python scripts/build_weekly_digest.py
uv run python scripts/new_monthly_review.py --theme "AI Infrastructure Buildout Is Durable"
uv run python scripts/new_earnings_review.py --ticker VRT --theme "AI Infrastructure Buildout Is Durable"
uv run python scripts/new_decision_review.py --ticker VRT --theme "AI Infrastructure Buildout Is Durable" --decision-type Add
```

## Generating Review Docs From Templates

- Monthly theme review: `scripts/new_monthly_review.py` -> `reviews/monthly/`
- Earnings scorecard: `scripts/new_earnings_review.py` -> `reviews/earnings/`
- Decision checklist: `scripts/new_decision_review.py` -> `reviews/decisions/`
- News/SEC ingestion: writes raw JSONL snapshots under `data/raw/` and normalized event rows into `data/processed/research.db`
- Reporting scripts: read the latest reviews plus SQLite events and write disposable markdown to `outputs/`

All generators copy from canonical files in `templates/`.

## Using With ChatGPT Projects + Codex

- Keep this repo as your local source of truth.
- Use ChatGPT/Codex for drafting and analysis against files in this repo.
- Paste generated outputs back into `reviews/` or `outputs/` with clear dates.
- Require explicit evidence references to canonical docs/templates when making changes.

## Intentionally Out of Scope

- Trade execution and broker APIs
- Auto-ranking or hidden strategy logic
- Always-on services, schedulers, workflow engines
- Vector DBs, agent frameworks, frontend stacks, Docker, or Airflow

## Remaining TODO Boundaries

- Fill `config/positions.yaml` with your actual live holdings and sleeve target weight.
- Replace the bootstrap baseline reviews with current primary-source earnings and filing work.
- Set a real SEC user-agent string in `MARKET_THESIS_SEC_USER_AGENT` before relying on SEC ingestion.
