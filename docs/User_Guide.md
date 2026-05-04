# User Guide

This repository currently supports two related workflows:

1. Thesis intake into `theses/*.yaml`
2. Review and reporting workflows that still run off `themes/themes.md` and `config/ticker_baskets.yaml`

That split is the most important thing to understand before using the repo. A saved thesis draft does not yet rewire the rest of the system automatically.

## Start Here

If this is a fresh clone, do these first:

1. Run `uv sync`.
2. Run `uv run pre-commit install`.
3. Read `docs/Investment_Policy.md`.
4. Decide whether you are doing thesis intake, review operations, or both.

If you are using the current review and reporting scripts, also:

1. Replace the starter content in `themes/themes.md`.
2. Align `config/ticker_baskets.yaml` to those exact theme names.
3. Review `config/risk_rules.yaml`.
4. Update `config/positions.yaml` or leave `positions: []` until funded.

## Thesis Intake Workflow

Use `scripts/new_thesis.py` to create or preview canonical thesis drafts.

Manual draft:

```bash
uv run python scripts/new_thesis.py --no-use-ai
```

Preview only:

```bash
uv run python scripts/new_thesis.py --no-use-ai --dry-run
```

AI-normalized draft:

```bash
export MARKET_THESIS_OPENAI_API_KEY="your-local-key"
uv run python scripts/new_thesis.py --use-ai --target-status draft
```

Local secret rules:

- keep the API key in a local shell env var or ignored `.env` only
- `OPENAI_TOKEN_MARKET_THESIS` also works as a local fallback env var
- never commit keys or paste them into tracked files, fixtures, docs, or GitHub comments

Useful flags:

- `--target-status draft|active`
- `--dry-run`
- `--yes`
- `--overwrite`
- `--output-dir <PATH>`

The interview captures:

- title and rough thesis statement
- why it matters and mechanism
- confirmation and disconfirming signals
- strongest counter-narrative
- benchmark, core, torque, canary, and remove tickers
- research gaps and tags

## What AI Mode Does And Does Not Do

AI mode can polish the thesis title and narrative fields, but several things stay anchored to operator input:

- `thesis_id` is derived from the operator-entered title, not the model-rewritten title
- persisted basket members come from the operator-entered basket inputs
- AI-added tickers are rejected
- invalid operator basket overlaps fail before an AI call is made

Treat the saved thesis as a draft to review, not an automatically trusted output.

## After You Save A Thesis

If the thesis is only for intake or future migration work, the YAML file may be enough.

If the thesis should drive the current operational scripts, manually mirror the accepted changes into:

- `themes/themes.md`
- `config/ticker_baskets.yaml`

Until the repo completes the later cutover, those legacy files still power review generation, narrative checks, and reporting scripts.

## What To Treat As Canonical

### For Thesis Intake

- `theses/*.yaml`
- `docs/Thesis_Schema.md`

### For Current Review And Reporting

- `docs/README_Project_Goal.md`
- `docs/Investment_Policy.md`
- `themes/themes.md`
- `config/ticker_baskets.yaml`
- `config/positions.yaml`
- `config/risk_rules.yaml`
- `reviews/decisions/Prediction_Log.md`
- files in `templates/`

## Daily Operating Sequence

Use the current repo in this order:

1. update the relevant canonical files
2. create or refresh review documents
3. ingest or review source material
4. complete the review manually
5. generate disposable outputs
6. revisit or log decisions

Do not start with generated outputs and backfill the canonical files later.

## Review And Reporting Commands

Create a monthly review:

```bash
uv run python scripts/new_monthly_review.py --theme "<Theme Name>"
```

Create an earnings review:

```bash
uv run python scripts/new_earnings_review.py --ticker <TICKER> --theme "<Theme Name>"
```

Create a decision checklist:

```bash
uv run python scripts/new_decision_review.py --ticker <TICKER> --theme "<Theme Name>" --decision-type Add
```

Build disposable outputs:

```bash
uv run python scripts/build_weekly_digest.py
uv run python scripts/build_post_earnings.py --ticker <TICKER>
uv run python scripts/narrative_drift.py
```

News and SEC ingestion:

```bash
uv run python scripts/ingest_news.py --feed <URL> --limit <N>
MARKET_THESIS_SEC_USER_AGENT="market-thesis-tracker/0.1 your-email@example.com" uv run python scripts/ingest_sec.py --ticker <TICKER> --limit <N>
```

## Weekly Loop

- ingest or review the latest source material
- refresh the relevant monthly review if the evidence changed materially
- update `reviews/decisions/Prediction_Log.md` when a prediction became more concrete or more testable
- generate a digest only after the underlying review is current

## Post-Earnings Loop

- ingest the new filing and supporting materials
- create the earnings review if it does not exist yet
- complete the scorecard from primary sources
- generate the post-earnings summary only after the scorecard is written

## Pre-Decision Loop

- confirm the latest theme review exists and is current
- confirm the latest relevant earnings review exists when applicable
- create and complete a decision checklist
- compare the action against `docs/Investment_Policy.md`, `config/risk_rules.yaml`, and `config/positions.yaml`

Do not let a generated summary substitute for a completed checklist.

## Best Practices

- keep one stable canonical name for each theme
- keep `theses/*.yaml` and the legacy theme and basket files aligned when the same thesis is operationally active
- treat `templates/` as durable forms and `reviews/` as completed records
- treat `outputs/` as disposable summaries, not as evidence records
- record disconfirming evidence even when conviction is rising
- prefer primary sources over summaries for material conclusions
- make small, traceable edits to canonical files instead of broad rewrites

## Useful Prompting Patterns

Good prompts:

- "Read `theses/ai_infrastructure_buildout_is_durable.yaml` and help me improve the draft without inventing new tickers."
- "Read `themes/themes.md` and `config/ticker_baskets.yaml`, then draft a monthly review using the existing template."
- "Compare this proposed decision against `docs/Investment_Policy.md`, `config/risk_rules.yaml`, and the latest monthly review."

Good constraints:

- require references to canonical files
- require explicit disconfirming evidence
- forbid invented tickers or hidden scoring systems
- keep disposable summaries in `outputs/`

## Anti-Patterns

- assuming a thesis YAML file automatically updates `themes/themes.md` or `config/ticker_baskets.yaml`
- letting an LLM rewrite operational basket membership without explicit review
- using `outputs/` as source-of-truth analysis
- making position decisions without a checklist and current review
- letting generated summaries override primary-source evidence
