# User Guide

This repository is a local-first research system for thematic investing. It is designed to help you keep thesis definitions, basket roles, reviews, and decisions consistent over time.

## What To Treat As Canonical

These files define the system. Generated outputs should reference them, not replace them.

- `docs/README_Project_Goal.md`
- `docs/Investment_Policy.md`
- `themes/Themes.md`
- `config/Ticker_Baskets.yaml`
- `reviews/decisions/Prediction_Log.md`
- `templates/Monthly_Theme_Review_Template.md`
- `templates/Company_Earnings_Scorecard_Template.md`
- `templates/Decision_Checklist.md`

## Daily Use

Use the repo in a simple sequence:

1. Read the current thesis language in `themes/Themes.md`.
2. Check basket roles in `config/Ticker_Baskets.yaml`.
3. Add raw notes or fetched inputs into `data/raw/` if needed.
4. Generate the relevant review document from the canonical template.
5. Fill the review manually with evidence and disconfirming signals.
6. Write disposable summaries to `outputs/` only after the review exists.

## Core Commands

Install dependencies and hooks:

```bash
uv sync
uv run pre-commit install
```

Create a monthly theme review:

```bash
uv run python scripts/new_monthly_review.py --theme "AI Infrastructure Buildout Is Durable"
```

Create an earnings review:

```bash
uv run python scripts/new_earnings_review.py --ticker VRT --theme "AI Infrastructure Buildout Is Durable"
```

Create a decision checklist:

```bash
uv run python scripts/new_decision_review.py --ticker VRT --theme "AI Infrastructure Buildout Is Durable" --decision-type Add
```

Build disposable outputs:

```bash
uv run python scripts/build_weekly_digest.py
uv run python scripts/build_post_earnings.py --ticker VRT
uv run python scripts/narrative_drift.py
```

## Recommended Workflow

When a theme changes:

- Update `themes/Themes.md` first.
- Update `config/Ticker_Baskets.yaml` if basket roles changed.
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

## Best Practices

- Keep one canonical name for each theme. Use the exact names from `themes/Themes.md`.
- Treat `templates/` as durable forms and `reviews/` as completed records.
- Treat `outputs/` as disposable summaries, not as source-of-truth analysis.
- Record disconfirming evidence even when conviction is rising.
- Prefer primary sources over press summaries for any important conclusion.
- Keep raw fetched data in `data/raw/` and derived SQLite data in `data/processed/`.
- Make small, traceable edits to canonical files instead of broad rewrites.

## Using ChatGPT Projects And Codex Well

Good prompts:

- "Read `themes/Themes.md` and `config/Ticker_Baskets.yaml`, then draft a monthly review for Theme X using the exact structure from `templates/Monthly_Theme_Review_Template.md`."
- "Read the latest earnings release and help me fill `reviews/earnings/...` without inventing facts or changing the thesis language."
- "Compare this proposed decision against `docs/Investment_Policy.md`, `config/risk_rules.yaml`, and the latest monthly review."

Good constraints to include:

- Require references to canonical files.
- Require explicit disconfirming evidence.
- Forbid new scoring systems unless you explicitly asked for them.
- Keep outputs in markdown and local files.

## Anti-Patterns

- Letting an LLM rewrite `themes/Themes.md` casually.
- Creating alternate templates outside `templates/`.
- Using `outputs/` as if they were canonical records.
- Making position decisions without a checklist and current theme review.
- Letting generated summaries override primary-source evidence.
- Expanding the repo into a trading system, ranking engine, or automation stack.

## What The Scripts Do Today

- `scripts/new_*` create review documents from canonical templates.
- `scripts/ingest_sec.py` writes placeholder SEC snapshot rows.
- `scripts/ingest_news.py` writes raw RSS/news snapshots.
- `scripts/build_weekly_digest.py` and `scripts/build_post_earnings.py` produce lightweight markdown stubs.
- `scripts/narrative_drift.py` produces a lightweight audit stub.

Several scripts intentionally contain TODO markers. That is deliberate. They are scaffolding for a disciplined local workflow, not hidden strategy logic.
