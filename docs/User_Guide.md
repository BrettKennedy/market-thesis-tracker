# User Guide

This repository is a local-first research system for thematic investing. It is designed to help you keep thesis definitions, basket roles, reviews, and decisions consistent over time.

## Start Here

If this is a fresh clone, do these in order:

1. Run `uv sync`.
2. Run `uv run pre-commit install`.
3. Replace the starter content in `themes/themes.md`.
4. Align `config/ticker_baskets.yaml` to those exact theme names.
5. Review `config/risk_rules.yaml`.
6. Update `config/positions.yaml` or leave `positions: []` until funded.
7. Generate one monthly review, one earnings review, and one decision checklist.

## What To Treat As Canonical

These files define the system. Generated outputs should reference them, not replace them.

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

## Daily Use

Use the repo in a simple sequence:

1. Read the current thesis language in `themes/themes.md`.
2. Check basket roles in `config/ticker_baskets.yaml`.
3. Check `config/positions.yaml` and `config/risk_rules.yaml` if a decision may follow.
4. Add raw notes or fetched inputs into `data/raw/` if needed.
5. Generate the relevant review document from the canonical template.
6. Fill the review manually with evidence and disconfirming signals.
7. Write disposable summaries to `outputs/` only after the review exists.

## First 30 Minutes

1. Run `uv sync`.
2. Run `uv run pre-commit install`.
3. Review `config/risk_rules.yaml` and confirm the default guardrails match how you want to operate.
4. Open `themes/themes.md` and replace the starter theme sections with your own.
5. Open `config/ticker_baskets.yaml` and align the basket keys and tickers with your framework.
6. Open `config/positions.yaml`, set your sleeve target weight, and either fill live positions or leave `positions: []` until the sleeve is funded.
7. Generate one monthly review, one earnings review, and one decision checklist.
8. Run one local ingest command and then build one weekly digest.

## Core Commands

Install dependencies and hooks:

```bash
uv sync
uv run pre-commit install
```

Create a monthly theme review:

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
uv run python scripts/build_post_earnings.py --ticker VRT
uv run python scripts/narrative_drift.py
```

For SEC ingestion, set a real user-agent string first:

```bash
export MARKET_THESIS_SEC_USER_AGENT="market-thesis-tracker/0.1 your-email@example.com"
uv run python scripts/ingest_sec.py --ticker VRT --limit 5
```

## Recommended Workflow

The operating order matters:

1. update canonical files
2. create or refresh review documents
3. ingest new source material
4. generate disposable outputs
5. make or revisit decisions

Do not reverse that order unless you are deliberately doing exploratory work.

When a theme changes:

- Update `themes/themes.md` first.
- Update `config/ticker_baskets.yaml` if basket roles changed.
- Do not patch downstream reviews first and backfill canonical files later.

When a company reports earnings:

- Create an earnings review from `templates/Company_Earnings_Scorecard_Template.md`.
- Use primary materials first: release, call transcript, filing, shareholder letter.
- Only after the scorecard is written should you update basket role or decision files.

Before any buy, add, trim, cut, or watch-only action:

- Create a decision checklist from `templates/Decision_Checklist.md`.
- Fill in both confirming and disconfirming evidence.
- Check the decision against `docs/Investment_Policy.md` and `config/risk_rules.yaml`.

Once per month:

- Create one monthly review per active theme.
- Update `reviews/decisions/Prediction_Log.md` with any major prediction that can be judged later.
- Generate a weekly or monthly digest only after the underlying reviews are current.

## Weekly Loop

- Run `scripts/ingest_news.py` for the feeds you care about.
- Review new rows in `data/raw/news/` only if the SQLite-backed digest points to something worth deeper work.
- Refresh the relevant monthly review if the evidence set changed materially.
- Build `outputs/weekly/weekly_digest_<date>.md` after the review work is current.

## Post-Earnings Loop

- Ingest the current SEC/fundamental inputs you care about.
- Create a new earnings review with `scripts/new_earnings_review.py`.
- Fill the scorecard from primary materials first.
- Run `scripts/build_post_earnings.py --ticker <TICKER>` to produce a disposable summary for decision review.

## Pre-Decision Loop

- Confirm the latest monthly theme review exists and is current.
- Confirm the relevant earnings review exists if the company recently reported.
- Create a decision checklist with `scripts/new_decision_review.py`.
- Compare the decision against `docs/Investment_Policy.md`, `config/risk_rules.yaml`, and `config/positions.yaml` before acting.

## Best Practices

- Keep one canonical name for each theme. Use the exact names from `themes/themes.md`.
- Keep theme names plain and stable. Renaming a theme creates avoidable drift across reviews.
- Treat `templates/` as durable forms and `reviews/` as completed records.
- Treat `outputs/` as disposable summaries, not as source-of-truth analysis.
- Record disconfirming evidence even when conviction is rising.
- Prefer primary sources over press summaries for any important conclusion.
- Keep raw fetched data in `data/raw/` and derived SQLite data in `data/processed/`.
- Make small, traceable edits to canonical files instead of broad rewrites.

## Using ChatGPT Projects And Codex Well

Good prompts:

- "Read `themes/themes.md` and `config/ticker_baskets.yaml`, then draft a monthly review for Theme X using the exact structure from `templates/Monthly_Theme_Review_Template.md`."
- "Read the latest earnings release and help me fill `reviews/earnings/...` without inventing facts or changing the thesis language."
- "Compare this proposed decision against `docs/Investment_Policy.md`, `config/risk_rules.yaml`, and the latest monthly review."
- "Given `config/positions.yaml` and `config/risk_rules.yaml`, point out where this draft decision would violate my own operating rules."

Good constraints to include:

- Require references to canonical files.
- Require explicit disconfirming evidence.
- Forbid new scoring systems unless you explicitly asked for them.
- Keep outputs in markdown and local files.

## Anti-Patterns

- Letting an LLM rewrite `themes/themes.md` casually without a deliberate thesis change.
- Creating alternate templates outside `templates/`.
- Using `outputs/` as if they were canonical records.
- Making position decisions without a checklist and current theme review.
- Letting generated summaries override primary-source evidence.
- Expanding the repo into a trading system, ranking engine, or automation stack.

## What The Scripts Do Today

- `scripts/new_*` create review documents from canonical templates.
- `scripts/ingest_sec.py` writes raw SEC filing snapshots and normalized SQLite events.
- `scripts/ingest_news.py` writes raw RSS/news snapshots and normalized SQLite events.
- `scripts/build_weekly_digest.py` reads the latest monthly reviews plus local SQLite events and produces a weekly digest.
- `scripts/build_post_earnings.py` reads the latest earnings review for a ticker and produces a disposable summary.
- `scripts/narrative_drift.py` runs deterministic checks against canonical theme language and required review sections.

The repo still uses conservative bootstrap examples. Replace them with live primary-source review work before using the system for real add/trim decisions.
