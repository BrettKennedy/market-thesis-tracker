# Review Workflow

This workflow keeps research disciplined and local-first.

See `docs/User_Guide.md` for the practical day-to-day operating version of this workflow.

## 1) Maintain Canonical Inputs

- Update `themes/Themes.md` when thesis language changes.
- Update `config/Ticker_Baskets.yaml` when basket roles change.
- Keep policy constraints aligned with `docs/Investment_Policy.md`.

## 2) Create Scheduled Review Documents

- Monthly theme review:
  - `uv run python scripts/new_monthly_review.py --theme "<Theme Name>"`
  - fills file in `reviews/monthly/` from `templates/Monthly_Theme_Review_Template.md`
- Post-earnings scorecard:
  - `uv run python scripts/new_earnings_review.py --ticker <TICKER> --theme "<Theme Name>"`
  - fills file in `reviews/earnings/` from `templates/Company_Earnings_Scorecard_Template.md`
- Decision checklist:
  - `uv run python scripts/new_decision_review.py --ticker <TICKER> --theme "<Theme Name>" --decision-type <Buy|Add|Hold|Trim|Cut|Watch only>`
  - fills file in `reviews/decisions/` from `templates/Decision_Checklist.md`

## 3) Record Calibration Inputs

- Add notable predictions and outcomes to `reviews/decisions/Prediction_Log.md`.
- Keep entries concrete and time-bounded.

## 4) Build Lightweight Output Artifacts

- `uv run python scripts/build_weekly_digest.py`
- `uv run python scripts/narrative_drift.py`

Outputs are written to `outputs/` and are intentionally disposable.

## 5) Keep Scope Tight

Allowed:
- Research synthesis
- Evidence tracking
- Review discipline

Not allowed:
- Trade execution automation
- Hidden model scoring logic
- Infrastructure-heavy workflows
