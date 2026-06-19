# Skill: DateFac Agent Foundation

## Purpose

This skill defines the current DateFac Agent pivot and the default boundary for new work.

The current mainline is:

```text
DateFac Agent foundation / extraction audit workflow
```

The active new package is:

```text
datefac_agent/
```

The legacy `datefac/` package remains valuable, but it is not the default place for new Agent work.

## Current Positioning

DateFac is no longer primarily competing as a raw PDF table extraction tool.

The new focus is:

```text
Accept extracted financial data from LLM apps, MinerU, spreadsheets, or other tools, then audit whether the data is correct, complete, traceable, and safe to deliver.
```

Chinese positioning:

```text
金融文档 AI 抽取结果审计与可信交付系统
```

## Default New Workflow

The target workflow is:

```text
intake -> audit -> review -> delivery
```

Module responsibilities:

- `datefac_agent/intake/`: read extracted Excel/workbook/structured artifacts without doing heavy business logic
- `datefac_agent/audit/`: pure checker modules for units, periods, valuation metrics, evidence, and other risk signals
- `datefac_agent/review/`: combine audit issues into `PASS`, `REVIEW`, or `FAIL`
- `datefac_agent/delivery/`: write audit reports, review queues, evidence indexes, and clean outputs
- `datefac_agent/schemas/`: shared typed models
- `datefac_agent/llm/`: future isolation area for model clients and prompts, not business logic

## Legacy Boundary

Treat these legacy chains as reference assets unless explicitly assigned:

- `340B-341B`: human-reviewed client preview chain
- `342A-342F`: real PDF / MinerU benchmark chain
- `345D`: full structured demo export chain
- `346B-346B5Q`: quality-limited recovery and QA chain

Do not continue `346B6` as the immediate mainline.

Do not migrate old runners wholesale.

Do not delete or move old `datefac/` code during Agent foundation work.

## Capability Harvest Rule

When old code contains useful logic, harvest the capability, not the historical script.

Prefer:

```text
rewrite as small pure checker + tests + fixture
```

Avoid:

```text
copy old runner with hard-coded output paths into datefac_agent
```

High-value legacy capability categories:

- metric alias normalization
- unit semantic guardrails
- period and year alignment
- valuation metric checks
- per-share vs total amount distinction
- ratio / percentage / multiple distinction
- evidence and lineage structures
- review queue generation
- audit report patterns
- readiness / manifest / decision flag patterns

## Fixture Harvest Rule

The `346B` chain is especially valuable as future fixture material.

Known error patterns should be reduced into compact cases under:

```text
tests/agent/fixtures/
```

Do not copy large historical output folders into fixtures.

Do not treat fixture coverage as `client_ready` or `production_ready`.

## Default Safety Flags

Unless a task explicitly says otherwise:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

Do not promote pilot or sidecar output into formal delivery.

## Worktree Rule

Prefer working from:

```text
D:\_datefac_agent
```

Do not use the dirty legacy workspace:

```text
D:\_datefac
```

unless the user explicitly asks for legacy inspection or one-file checkout.

## Git Rule

Follow `.skills/git_workflow.md` for the full staging / protected-file / risk rules. The stable invariants are:

- precise path staging only; never `git add .` / `git add -A`
- never `git reset --hard` / `git checkout --`
- never stage `output/` / `temp/` / unrelated dirty files
