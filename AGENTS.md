# AGENTS.md

This repo is in the middle of a thesis-intake refactor.

## Current state

- Phase 1 schema work lives in `scripts/thesis_models.py`
- example canonical thesis files live in `theses/`
- schema documentation lives in `docs/Thesis_Schema.md`
- current runtime scripts still read `themes/themes.md` and `config/ticker_baskets.yaml`
- Phase 2 is expected to cut repo consumers over to thesis files

## Working guidance

- Treat `theses/*.yaml` as the canonical design target for new intake work.
- Keep the canonical thesis object focused on durable definition data.
- Do not fold monthly review state, prediction outcomes, or calibration history into the core thesis schema unless the task explicitly covers a later lifecycle phase.
- Prefer the normalized `basket.members[]` model over duplicate role buckets when adding schema logic.
- When touching pre-cutover scripts, be explicit about whether a change is Phase 1-compatible or part of the Phase 2 cutover.

## Validation

- Run `uv run pytest` after meaningful changes.
- Use targeted `uv run ruff check ...` for new Python files or tests.

## Repo hygiene

- Do not commit `.claude/` or other local app state.
- Never commit API keys or provider secrets in any form.
- For AI intake work, read secrets only from local environment variables such as `MARKET_THESIS_OPENAI_API_KEY`.
- Reject any edit that would place a real key in tracked code, docs, fixtures, sample config, commit history, or GitHub content.
- Keep changes traceable and avoid mixing schema-design work with unrelated workflow refactors unless the task explicitly calls for both.
