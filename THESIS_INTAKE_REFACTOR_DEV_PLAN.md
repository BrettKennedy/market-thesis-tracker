# Thesis Intake Refactor Development Plan

## Purpose

Upgrade the tracker from an experimental markdown-and-YAML control surface into a schema-first system that can turn a rough market idea into a validated thesis object, with CLI intake and optional AI assistance layered on afterward.

This refactor is intentionally allowed to be breaking if the result is cleaner. The current codebase has only been used experimentally, so the design should optimize for a better long-term operating model rather than preserving short-lived file contracts.

## Why this update matters

The repo already has the right underlying ideas:

- themes first, tickers second
- explicit confirming and disconfirming signals
- counter-narratives and falsifiability
- normalized basket roles
- prediction and review discipline

Today those ideas are split across multiple artifacts and several scripts still read those artifacts directly. The result is unnecessary duplication and awkward intake.

The goal of this refactor is to make a canonical thesis object the center of the system, then layer intake, review, and optional exports around that object.

---

## Current repo reality

This plan reflects the codebase as it exists now:

- `scripts/repo_helpers.py` currently parses `themes/themes.md` with regex-based helpers
- `scripts/config_models.py` currently validates and loads `config/ticker_baskets.yaml`
- current scripts and tests still treat those files as the active inputs
- the tracked root files are still bootstrap placeholders
- the real example themes currently live in `tests/fixtures/themes.md` and `tests/fixtures/ticker_baskets.yaml`

That means Phase 1 should establish the new canonical schema cleanly, and Phase 2 should cut repo consumers over to it.

---

## Target architecture

### Canonical state

One thesis per file under `theses/` becomes the canonical definition layer.

Example layout:

```text
theses/
  ai_infrastructure_buildout_is_durable.yaml
  saas_shakeout_is_real_but_selective.yaml
```

### Core flow

1. User starts with a rough idea
2. CLI intake captures the idea
3. Optional AI can help normalize the input
4. A canonical thesis YAML file is created and validated
5. Human review happens before persistence or activation
6. Review workflows and downstream tools consume the thesis object
7. Optional legacy exports can be generated later if still useful

### Breaking-change posture

- Breaking changes are acceptable when they simplify the design
- The repo should not carry a long-lived compatibility layer for the old theme and basket files
- `themes/themes.md` and `config/ticker_baskets.yaml` are future optional exports, not permanent canonical inputs
- `reviews/decisions/Prediction_Log.md` remains a separate decision and outcome history stream rather than part of the core thesis-definition object

---

## Design principles

- **Schema first, AI second**
- **Themes first, tickers second**
- **Human approval before activation**
- **Preserve falsifiability**
- **Prefer explicit structure over cleverness**
- **Avoid fake precision in draft mode**
- **Keep the canonical object focused on durable thesis-definition data**

---

## Canonical thesis object direction

Phase 1 should lock this high-level shape:

- `schema_version`
- `thesis_id`
- `title`
- `status`
- `content`
- `evidence`
- `basket`
- `working_notes`

### `content`

- `thesis_statement`
- `why_this_matters`
- `mechanism`
- `time_horizon`

### `evidence`

- `confirmation_signals`
- `disconfirming_signals`
- `counter_narrative`

### `basket.members[]`

Each basket member contains:

- `ticker`
- `role`
- `is_benchmark`

Supported roles:

- `benchmark`
- `core`
- `torque`
- `canary`
- `remove`

Benchmark rules:

- benchmark-only tracking names use `role: benchmark`
- names that are both investable expressions and benchmarks use `role: core|torque|canary` plus `is_benchmark: true`
- each ticker appears only once in the canonical basket list

### `working_notes`

- `research_gaps`
- `source_notes`
- `tags`

### Intentionally deferred from the Phase 1 schema

- `slug`
- `created_at`
- `updated_at`
- `thesis_health`
- `next_review_date`
- `best_current_expressions`
- prediction outcomes and calibration history

Monthly review score, stance, and next-review state remain downstream review artifacts rather than canonical thesis-definition fields.

---

## Development phases

## Phase 0 - Lock architecture and breaking-change posture

### Objective

Define the boundary between the current experimental inputs and the new canonical thesis object.

### Tasks

- document current repo reality and coupling points
- decide that thesis YAML files become canonical early
- decide that legacy markdown and basket YAML are optional exports later
- define the normalized basket-member model

### Deliverables

- architecture note
- canonical object direction
- cutover posture

### Exit criteria

A contributor can explain why the refactor is allowed to break the old control surface and why Phase 2 is the cutover point.

---

## Phase 1 - Build the canonical thesis schema

### Objective

Introduce the canonical thesis schema, validation layer, example thesis files, focused tests, and schema documentation.

### Tasks

- define schema fields and nested structures
- define required versus optional behavior for `draft` and `active`
- implement validation rules
- create example serialized thesis files from fixture-backed themes
- write schema-focused tests
- document mapping from legacy artifacts into the new schema

### Deliverables

- `scripts/thesis_models.py`
- example thesis YAML files under `theses/`
- `docs/Thesis_Schema.md`
- focused schema tests

### Exit criteria

- the AI infrastructure and SaaS shakeout themes validate as canonical thesis files
- the new schema has explicit draft and active rules
- current pytest coverage remains green during this phase

---

## Phase 2 - Cut the repo over to thesis files

### Objective

Make thesis files the actual runtime source of truth across the repo.

### Tasks

- add thesis repository utilities for discovery and validation-on-load
- replace regex theme parsing with thesis-repository helpers
- replace direct basket-YAML loading with thesis-repository helpers
- update docs so thesis files are treated as canonical
- rewrite or replace existing consumer tests around the new helpers

### Deliverables

- thesis repository module
- repo-wide consumer cutover
- updated contributor docs

### Exit criteria

Repo consumers read thesis files directly, and `themes/themes.md` plus `config/ticker_baskets.yaml` are no longer required inputs.

---

## Phase 3 - Build a manual CLI intake flow

### Objective

Create a working intake flow that writes draft thesis files without any AI dependency.

### Tasks

- add a `new-thesis` CLI command
- prompt for thesis title, statement, mechanism, signals, counter-narrative, and basket ideas
- validate draft payloads before save
- support review, retry, or cancel paths

### Deliverables

- interactive CLI command
- draft save flow
- validation feedback in the CLI

### Exit criteria

A user can create a valid draft thesis file from scratch without AI assistance.

---

## Phase 4 - Add optional AI normalization

### Objective

Allow optional AI help for structuring rough ideas into schema-compliant thesis drafts.

### Tasks

- define provider config format
- support provider name, model, API key, optional base URL, timeout, and retry settings
- implement provider abstraction
- add an AI normalization path for rough intake output
- preserve raw user input alongside normalized fields where useful

### Deliverables

- config model
- provider abstraction
- normalization interface
- structured parsing into the thesis schema

### Exit criteria

A rough idea can be turned into a valid thesis draft through AI-assisted normalization, with human review before save.

---

## Phase 5 - Add a critique pass

### Objective

Challenge weak thesis construction before a thesis moves from draft to active.

### Tasks

- evaluate falsifiability
- evaluate whether the mechanism is economic rather than narrative fluff
- evaluate whether signals are observable and meaningful
- check whether basket members actually express the thesis
- check whether the counter-narrative is strong enough
- detect overlap with existing theses

### Deliverables

- critique interface
- structured critique output
- pass/warn/fail quality findings

### Exit criteria

Every thesis draft can be reviewed for clarity and structure before activation.

---

## Phase 6 - Add optional legacy exports

### Objective

Generate old-style human-readable views only if they still provide value.

### Tasks

- optionally render `themes/themes.md`
- optionally render `config/ticker_baskets.yaml`
- support preview or dry-run behavior
- keep exported formatting deterministic

### Deliverables

- export renderers
- preview mode
- optional export workflow

### Exit criteria

Legacy markdown and basket YAML can be regenerated from thesis files when needed, but are no longer required by the runtime.

---

## Phase 7 - Add lifecycle and review-state tooling

### Objective

Support ongoing thesis evolution after initial creation.

### Tasks

- add later lifecycle states such as `paused` and `retired`
- add update flows for review metadata and operating state
- support links between thesis files and downstream review or history records
- support logging of outcome reviews without mutating the core definition shape recklessly

### Deliverables

- lifecycle tooling
- review-state update flows
- history-linking conventions

### Exit criteria

A thesis can evolve over time without losing prior reasoning or blurring the line between canonical definition data and downstream review history.

---

## Phase 8 - Harden the system

### Objective

Make the redesigned workflow stable, testable, and easy to understand.

### Tasks

- add integration coverage for cut-over consumers
- add tests for CLI edge cases
- add fixtures for additional thesis examples
- tighten contributor documentation
- document provider configuration and critique workflows

### Deliverables

- broader test suite
- additional fixtures
- contributor-facing docs

### Exit criteria

A new contributor can create, validate, inspect, and extend thesis files without reverse-engineering the codebase.

---

## Recommended implementation sequence

1. Lock the canonical schema
2. Validate it against real fixture-backed themes
3. Cut repo consumers over to thesis files
4. Build manual CLI intake
5. Add optional AI normalization
6. Add critique tooling
7. Add optional legacy exports
8. Add lifecycle and hardening work

This order matters. The canonical schema should settle before CLI, AI, or export layers harden around it.

---

## Key risks and failure modes

### Risk 1 - Schema too rigid

If the schema forces too much precision too early, rough ideas will stay outside the system.

**Mitigation:** require only the thesis statement for drafts and keep working-note fields flexible.

### Risk 2 - Canonical object becomes a dumping ground

If review-state fields, prediction history, and downstream analysis all get folded into the thesis definition too early, the schema will become hard to reason about.

**Mitigation:** keep the canonical thesis focused on durable definition data; push review scores and history to later linked workflows.

### Risk 3 - Cutover drift

If the repo keeps reading old files for too long, the new schema will be treated as aspirational rather than real.

**Mitigation:** make Phase 2 a true cutover phase instead of maintaining a long compatibility bridge.

### Risk 4 - AI overreach

If AI is allowed to invent basket members or evidence silently, the workflow becomes a plausibility generator rather than a discipline tool.

**Mitigation:** keep schema validation explicit and require human review before activation.

---

## Acceptance criteria for the overall update

The refactor is directionally successful when:

- a user can start from a rough thesis idea
- the system can structure that idea into a validated thesis file
- thesis files become the runtime source of truth
- AI assistance remains optional rather than mandatory
- legacy exports are optional, not controlling
- the workflow becomes easier without weakening decision discipline

---

## Immediate next steps

1. Finish Phase 1 schema work
2. Prepare Phase 2 consumer cutover
3. Rewire repo helpers and scripts onto thesis files
4. Only then move on to CLI intake and AI-assisted normalization

---

## Notes for contributors

This refactor is a schema and workflow redesign, not a convenience wrapper around the current markdown files.

The long-term goal is not automated stock picking.

The long-term goal is a cleaner operating system for thesis formation, validation, review, and learning.
