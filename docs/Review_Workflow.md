# Review Workflow

This workflow keeps the repo local-first, disciplined, and easy to audit later.

Use this document for the operating sequence. Use `docs/User_Guide.md` for the more practical day-to-day reference.

The repo currently has a split between thesis intake and operational review scripts:

- thesis intake writes `theses/*.yaml`
- review and reporting scripts still run from `themes/themes.md` and `config/ticker_baskets.yaml`

If you accept a thesis change that should affect current operations, mirror it into the legacy theme and basket files before relying on the review or reporting scripts.

## Operating Order

Do the work in this order:

1. update canonical inputs
2. create or refresh review documents
3. ingest or read new source material
4. write the review itself
5. generate disposable outputs
6. revisit or make decisions

Do not start with generated outputs and then backfill the canonical files later.

## 1) Maintain Canonical Inputs

- Update `themes/themes.md` when thesis language changes.
- Update `config/ticker_baskets.yaml` when basket roles change.
- Keep `config/positions.yaml` and `config/risk_rules.yaml` current enough to support real decisions.
- Keep policy constraints aligned with `docs/Investment_Policy.md`.

These files are the control surface for the framework. Reviews and outputs should follow them, not compete with them.

## 2) Create Review Documents From Templates

Create review files before you start synthesizing conclusions.

- Monthly theme review:
  - `uv run python scripts/new_monthly_review.py --theme "<Theme Name>"`
  - writes to `reviews/monthly/` from `templates/Monthly_Theme_Review_Template.md`
- Post-earnings scorecard:
  - `uv run python scripts/new_earnings_review.py --ticker <TICKER> --theme "<Theme Name>"`
  - writes to `reviews/earnings/` from `templates/Company_Earnings_Scorecard_Template.md`
- Decision checklist:
  - `uv run python scripts/new_decision_review.py --ticker <TICKER> --theme "<Theme Name>" --decision-type <Buy|Add|Hold|Trim|Cut|Watch only>`
  - writes to `reviews/decisions/` from `templates/Decision_Checklist.md`

If the relevant review file does not exist, create it first instead of drafting free-form notes somewhere else.

## 3) Ingest And Read Source Material

Use local ingestion to collect raw inputs and normalize them into SQLite.

- News and RSS:
  - `uv run python scripts/ingest_news.py --feed <URL> --limit <N>`
- SEC metadata:
  - `MARKET_THESIS_SEC_USER_AGENT="market-thesis-tracker/0.1 your-email@example.com" uv run python scripts/ingest_sec.py --ticker <TICKER> --limit <N>`

Use primary materials first for any material conclusion:

- company filings
- earnings releases and calls
- shareholder letters
- official company or regulator disclosures

Treat press summaries and market commentary as secondary context, not as the main evidence base.

## 4) Complete The Review

Fill the review document manually.

Minimum discipline:

- state what changed
- state what still holds
- record what is weakening
- include disconfirming evidence
- keep the strongest counter-narrative current
- make score changes explicit rather than implied

If conviction increased but disconfirming evidence also increased, record both.

## 5) Generate Disposable Outputs

Use outputs only after the underlying reviews are current.

- Weekly digest:
  - `uv run python scripts/build_weekly_digest.py`
- Post-earnings summary:
  - `uv run python scripts/build_post_earnings.py --ticker <TICKER>`
- Narrative audit:
  - `uv run python scripts/narrative_drift.py`

Outputs are written to `outputs/` and are intentionally disposable.

## 6) Record Calibration Inputs

- Add notable predictions and outcomes to `reviews/decisions/Prediction_Log.md`.
- Keep entries concrete, time-bounded, and judgeable later.

If a prediction cannot be judged later, it is not useful for calibration.

## Weekly Loop

- ingest or review the latest source material
- refresh the relevant monthly review if the evidence changed materially
- build a digest only after the review is current

## Post-Earnings Loop

- ingest the new filing and supporting materials
- create the earnings review if it does not exist yet
- complete the scorecard from primary sources
- generate the post-earnings summary only after the scorecard is written

## Pre-Decision Loop

- confirm the latest theme review exists
- confirm the latest relevant earnings review exists when applicable
- create and complete a decision checklist
- compare the action against `docs/Investment_Policy.md`, `config/risk_rules.yaml`, and `config/positions.yaml`

Do not let a generated summary substitute for a completed checklist.

## Keep Scope Tight

Allowed:
- Research synthesis
- Evidence tracking
- Review discipline
- Local file and SQLite automation

Not allowed:
- Trade execution automation
- Hidden model scoring logic
- Infrastructure-heavy workflows
- Broker APIs or trading integrations
