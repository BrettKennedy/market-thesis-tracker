# Phase 1 Brief - Canonical Thesis Schema And Validation Layer

## Objective

Introduce the canonical thesis schema and validation layer that Phase 2 will cut the repo over to.

This phase should stay tightly scoped. Do not build CLI intake, AI integration, lifecycle tooling, legacy exports, or repo-wide consumer rewiring yet.

---

## Why this phase matters

Right now the repo still relies on experimental canonical inputs:

- `themes/themes.md`
- `config/ticker_baskets.yaml`

Those files are useful for bootstrap workflows, but they are not a good long-term intake model.

Phase 1 exists to define the clean source-of-truth object that the rest of the refactor will harden around.

If this phase is done well, Phase 2 can cut the repo over with confidence. If it is done poorly, every later phase will have to unwind schema mistakes.

---

## Scope

### In scope

- define the canonical thesis schema
- implement validation rules
- define enums and constrained fields
- create example thesis YAML files
- document how legacy repo concepts map into the schema
- add focused schema tests
- document assumptions and tradeoffs

### Out of scope

- repository load or save utilities beyond basic validation helpers
- repo-wide consumer cutover
- CLI interview flows
- API or LLM integration
- provider config
- lifecycle tooling
- review-state tracking
- legacy export generation

---

## Deliverables

Phase 1 should produce:

1. **Schema model(s)** for the canonical thesis object
2. **Validation logic** for required structure and field constraints
3. **Example serialized thesis files** for at least two existing themes
4. **Migration notes** explaining how current repo concepts map into the schema
5. **Basic schema documentation**
6. **Focused tests** for schema behavior

---

## Design requirements

## 1. Make the thesis object the design target

The schema must be capable of representing the full logical content of a thesis without relying on separate markdown files for interpretation.

It should be possible to load a single thesis file and know:

- what the thesis is
- why it matters
- how it works
- what confirms it
- what weakens it
- how it is expressed through tickers

## 2. Preserve the repo's philosophy

The schema should reflect the repo's existing operating philosophy:

- themes first, tickers second
- falsifiable theses
- explicit confirming and disconfirming evidence
- strong counter-narratives
- normalized basket roles

## 3. Avoid fake precision

Draft theses should be able to capture incomplete ideas without forcing every downstream field to be filled in immediately.

## 4. Prefer clarity over cleverness

Use explicit field names and straightforward nested structures. Optimize for maintainability and readability.

---

## Canonical schema shape

Phase 1 should lock this interface:

- `schema_version`
- `thesis_id`
- `title`
- `status`
- `content`
- `evidence`
- `basket`
- `working_notes`

## `content`

- `thesis_statement`
- `why_this_matters`
- `mechanism`
- `time_horizon`

## `evidence`

- `confirmation_signals`
- `disconfirming_signals`
- `counter_narrative`

## `basket.members[]`

Each basket member contains:

- `ticker`
- `role`
- `is_benchmark`

Supported `role` values:

- `benchmark`
- `core`
- `torque`
- `canary`
- `remove`

## `working_notes`

- `research_gaps`
- `source_notes`
- `tags`

Example shape:

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

---

## Basket model

The canonical basket schema is normalized.

Rules:

- each ticker appears only once in `basket.members`
- benchmark-only names use `role: benchmark`
- names that are both investable expressions and benchmarks use `role: core|torque|canary` plus `is_benchmark: true`
- `remove` cannot be combined with `is_benchmark: true`

This replaces the old duplicated bucket layout with one explicit member record per ticker.

---

## Validation expectations

At minimum, validation should enforce rules like these:

### Required for all thesis objects

- `schema_version` must be `1`
- `thesis_id` must be lowercase snake_case
- `title` must not be blank
- `status` must be a supported enum value
- `content.thesis_statement` must not be blank

### Required for active theses

- `content.why_this_matters` must not be empty
- `content.mechanism` must not be empty
- `content.time_horizon` must not be empty
- at least one confirmation signal
- at least one disconfirming signal
- `counter_narrative` must not be empty
- at least one benchmark member

### Basket rules

- basket tickers should normalize to uppercase
- blank ticker values should fail
- each ticker may appear only once
- `benchmark` role is allowed as a standalone tracking name
- `is_benchmark: true` is allowed on `core`, `torque`, or `canary`
- `remove` plus `is_benchmark: true` should fail

### List behavior

- list values should be trimmed
- blank list items should fail

### Draft-friendly behavior

- draft theses can omit rationale, mechanism, signals, and basket detail
- research gaps can remain open
- notes fields can be incomplete

If a rule is intentionally not implemented, document why.

---

## Serialization expectations

Use one thesis per file. YAML is the preferred serialized format.

Expected path:

```text
theses/
  ai_infrastructure_buildout_is_durable.yaml
  saas_shakeout_is_real_but_selective.yaml
```

Phase 1 does not need to build repository discovery or storage workflows yet. It only needs the schema, example files, and validation helpers.

---

## Mapping notes to capture explicitly

Document these design choices:

- `mechanism` is authored explicitly in thesis YAML even when it was only implicit in current thesis prose
- disconfirming signals serve as the falsification surface in Phase 1 rather than adding a second near-duplicate invalidation field
- overlapping benchmark and investable names from the old basket YAML become one normalized member with `is_benchmark: true`
- `Prediction_Log.md` informs future linked history work but is not folded into the Phase 1 thesis-definition schema

---

## Example output requirements

Create at least two example thesis files that prove the schema is expressive enough for the current repo concepts:

1. **AI Infrastructure Buildout Is Durable**
2. **SaaS Shakeout Is Real but Selective**

Build those examples from:

- `tests/fixtures/themes.md`
- `tests/fixtures/ticker_baskets.yaml`

Do not derive them from the root bootstrap files, because those are still placeholders.

---

## Documentation requirement

Include a schema document that explains:

- field definitions
- validation rules
- normalized basket-member behavior
- legacy-to-schema mapping
- explicit note that legacy markdown and basket YAML become future optional exports rather than canonical inputs

---

## Suggested acceptance criteria

Phase 1 is complete when all of the following are true:

- there is a canonical thesis schema in code
- validation rules are implemented and tested
- both example thesis files validate successfully
- the schema can represent all major concepts from the fixture-backed themes
- draft versus active behavior is sensible
- contributors can understand how current repo concepts map into the new structure
- the existing pytest suite remains green during this phase

---

## Non-goals

Do not spend time on these yet:

- repo-wide cutover to thesis files
- interactive CLI prompting
- LLM provider integration
- critique flows
- markdown rendering
- legacy export generation
- portfolio sizing logic
- review dashboards

Those come later.

---

## Implementation notes for Codex

When making design decisions, optimize for:

- maintainability
- explicitness
- easy testability
- low surprise for future contributors

Prefer simple nested models over abstract frameworks.

If you need to choose between a more elegant schema and a more readable one, choose readability.
