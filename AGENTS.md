# AGENTS.md

This repo now has a merged thesis-intake foundation on `main`.

## Current State

- `scripts/new_thesis.py` is the live intake entrypoint for creating `theses/*.yaml`
- `scripts/thesis_models.py` defines the canonical thesis schema
- `scripts/thesis_ai.py` handles optional AI normalization for intake
- `docs/Thesis_Schema.md` documents the schema and validation rules
- review, ingestion, and reporting scripts still read `themes/themes.md` and `config/ticker_baskets.yaml`

## Working Guidance

- Treat `theses/*.yaml` as the canonical intake format.
- Remember that the repo is currently split:
  - thesis intake writes YAML files in `theses/`
  - operational review and reporting flows still depend on `themes/themes.md` and `config/ticker_baskets.yaml`
- If a task changes an operationally active thesis, be explicit about whether the legacy theme and basket files also need to be updated.
- Keep the thesis object focused on durable definition data.
- Do not fold monthly review state, prediction outcomes, or calibration history into the core thesis schema unless the task explicitly covers a later lifecycle phase.
- Prefer the normalized `basket.members[]` model over duplicate role buckets when touching thesis schema logic.

## Validation

- Run `uv run pytest` after meaningful code changes.
- Use targeted `uv run ruff check ...` for changed Python files or tests.

## Repo Hygiene

- Do not commit `.claude/` or other local app state.
- Never commit API keys or provider secrets in any form.
- For AI intake work, read secrets only from local environment variables such as `MARKET_THESIS_OPENAI_API_KEY`.
- `OPENAI_TOKEN_MARKET_THESIS` is acceptable as a local fallback env var, but it is still secret material and must never be committed.
- Reject any edit that would place a real key in tracked code, docs, fixtures, sample config, commit history, or GitHub content.
- Keep changes traceable and avoid mixing thesis-intake work with unrelated workflow refactors unless the task explicitly calls for both.
