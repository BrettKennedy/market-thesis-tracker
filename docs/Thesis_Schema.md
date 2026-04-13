# Thesis Schema

This document defines the canonical thesis schema introduced in Phase 1 of the thesis intake refactor.

The goal is to establish a clean source-of-truth object now, then cut the repo over to thesis files in Phase 2.

## Canonical Status

In the current repo, scripts still read `themes/themes.md` and `config/ticker_baskets.yaml` directly.

That is temporary.

The Phase 1 schema is the canonical design target, and Phase 2 is responsible for cutting repo consumers over to `theses/*.yaml`.

Legacy markdown and YAML files are future optional exports, not long-term canonical inputs.

## Top-Level Shape

Each thesis file uses this structure:

```yaml
schema_version: 1
thesis_id: example_thesis
title: Example Thesis
status: draft
content:
  thesis_statement: ...
  why_this_matters: ...
  mechanism: ...
  time_horizon: ...
evidence:
  confirmation_signals: []
  disconfirming_signals: []
  counter_narrative: ...
basket:
  members: []
working_notes:
  research_gaps: []
  source_notes: []
  tags: []
```

## Field Definitions

### `schema_version`

Schema version for the canonical thesis object. Phase 1 requires `1`.

### `thesis_id`

Machine identifier for the thesis. It must be lowercase snake_case and match the YAML filename stem.

Example:

```text
theses/ai_infrastructure_buildout_is_durable.yaml
```

### `title`

Human-readable thesis name.

### `status`

Supported Phase 1 values:

- `draft`
- `active`

Later lifecycle states such as `paused` or `retired` are deferred to a later phase.

### `content`

Core thesis-definition text:

- `thesis_statement`
- `why_this_matters`
- `mechanism`
- `time_horizon`

### `evidence`

Evidence and challenge structure:

- `confirmation_signals`
- `disconfirming_signals`
- `counter_narrative`

Phase 1 intentionally uses disconfirming signals as the falsification surface rather than introducing a second near-duplicate invalidation field.

### `basket.members`

Normalized list of ticker members. Each ticker appears once.

Each member has:

- `ticker`
- `role`
- `is_benchmark`

Supported roles:

- `benchmark`
- `core`
- `torque`
- `canary`
- `remove`

### `working_notes`

Flexible fields that support thesis formation without driving downstream runtime behavior:

- `research_gaps`
- `source_notes`
- `tags`

## Basket Model

The canonical basket model is normalized to remove the ambiguity from the old bucket-per-role layout.

Rules:

- each ticker appears once in `basket.members`
- a benchmark-only tracking name can use `role: benchmark`
- a name that is both an investable expression and a benchmark uses `role: core`, `torque`, or `canary` plus `is_benchmark: true`
- `remove` members cannot also be benchmarks

This lets the schema express the old overlap between benchmark names and investable names without duplicating the same ticker across multiple arrays.

## Validation Rules

### Required for all theses

- `schema_version` must be `1`
- `thesis_id` must be lowercase snake_case
- `title` must not be blank
- `status` must be one of `draft` or `active`
- `content.thesis_statement` must not be blank

### Additional requirements for `active` theses

- `content.why_this_matters` must not be blank
- `content.mechanism` must not be blank
- `content.time_horizon` must not be blank
- `evidence.confirmation_signals` must contain at least one item
- `evidence.disconfirming_signals` must contain at least one item
- `evidence.counter_narrative` must not be blank
- `basket.members` must contain at least one benchmark member

### Basket-member validation

- tickers are normalized to uppercase
- blank ticker values are rejected
- each ticker may appear only once
- `remove` cannot be combined with `is_benchmark: true`
- `benchmark` role should be used without `is_benchmark: true`

### List behavior

- list values are trimmed
- blank list items are rejected

## Legacy Mapping

The Phase 1 examples are derived from:

- `tests/fixtures/themes.md`
- `tests/fixtures/ticker_baskets.yaml`

Mapping summary:

- `themes.md` thesis statement maps to `content.thesis_statement`
- `themes.md` why-this-matters section maps to `content.why_this_matters`
- mechanism is authored explicitly in the thesis YAML when it was only implicit in the original prose
- confirmation and disconfirming bullet lists map into `evidence`
- strongest counter-narrative maps to `evidence.counter_narrative`
- basket role arrays from `ticker_baskets.yaml` become normalized `basket.members`
- overlapping benchmark plus core names become one member with `is_benchmark: true`

## Intentionally Out Of Scope In Phase 1

These are not part of the canonical thesis-definition schema yet:

- theme health score
- current stance
- next review date
- best current expressions
- prediction outcomes
- calibration history
- lifecycle timestamps such as `created_at` and `updated_at`

Monthly review state remains downstream review data, and `reviews/decisions/Prediction_Log.md` remains a separate history stream for future linking work.
