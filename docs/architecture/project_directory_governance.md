# Project Directory Governance

## Scope

This document is a lightweight directory governance guide for `D:\_datefac`.
It clarifies where code, docs, inputs, outputs, and temporary files belong.
It does not move source code.
It does not change business behavior.

## Root vs Package

`D:\_datefac` is the project root.
It contains source code, docs, tools, tests, inputs, outputs, and local runtime folders.

`D:\_datefac\datefac` is the main Python package.
It contains importable application modules and numbered-task implementations.

Rule of thumb:

- Put importable application logic under `datefac/`.
- Put runnable entry scripts under `tools/`.
- Put tests under `tests/`.
- Put human-readable guidance under `docs/`.
- Put local runtime inputs under `input/`.
- Put generated artifacts under `output/`.

## Root Directory Responsibilities

### `docs/`

Purpose:
- Project docs, task specs, runbooks, architecture notes, and handoff material.

Not responsible for:
- Runtime code.
- Generated benchmark payloads.

### `tools/`

Purpose:
- Runnable entry points, helper scripts, PowerShell utilities, and task launchers.

Not responsible for:
- Core library logic that should be imported elsewhere.

### `tests/`

Purpose:
- Focused automated checks for task modules, reports, and helpers.

Not responsible for:
- Long-lived runtime outputs.

### `input/`

Purpose:
- Local input workbooks, PDFs, filled review templates, and user-provided sidecar inputs.

Not responsible for:
- Versioned source code.

### `output/`

Purpose:
- Generated task outputs, workbooks, summaries, manifests, QA reports, JSONL/CSV exports, and sidecar evidence.

Not responsible for:
- Canonical source code or stable Git-tracked business assets.

### `temp/`

Purpose:
- Local scratch space and throwaway runtime intermediates.

Not responsible for:
- Durable benchmark evidence.

### `_codex_test_tmp_*/`

Purpose:
- Codex-created temporary test cases and isolated fixture directories.

Not responsible for:
- Persistent project outputs.

### `_codex_debug_*/`

Purpose:
- Local debug-only scratch folders.

Not responsible for:
- Stable docs or benchmark deliverables.

## Source Package Responsibilities

### `datefac/`

Purpose:
- Main Python package for DateFac code.

Not responsible for:
- User-facing task docs or generated output artifacts.

### `datefac/benchmark/`

Purpose:
- Numbered benchmark, audit, retry, recovery, and sidecar task implementations.

Not responsible for:
- Generic shared helpers that belong in stable packages.

### `datefac/extraction/`

Purpose:
- Extraction-layer helpers such as row-text extraction, cleanup, and repair support.

Not responsible for:
- Full end-to-end benchmark packaging.

### `datefac/pipeline/`

Purpose:
- Multi-step pipeline assembly and pipeline-facing integration code.

Not responsible for:
- Human-facing documentation or review workbooks by itself.

### `datefac/review_queue/`

Purpose:
- Review queue schema, workbook round-trip helpers, ingestion, spot-check, strict-review, and demo-package review flows.

Not responsible for:
- Low-level parser implementation.

### `datefac/trust/`

Purpose:
- Trust-governed sidecars, preview exports, audit gates, and human-reviewed preview chain logic.

Not responsible for:
- MinerU runtime environment repair.

### `datefac/mineru_body/`

Purpose:
- MinerU table/body readers, candidate mapping, normalization, and delivery-adjacent sidecar consumption helpers.

Not responsible for:
- Running the MinerU CLI itself.

### `datefac/parser/`

Purpose:
- Parser output readers such as MinerU output readers.

Not responsible for:
- Review queue governance or client-preview claims.

### `datefac/recognition/`

Purpose:
- Recognition-layer helpers such as table image recognition and legacy PPStructure result reading.

Not responsible for:
- Formal benchmark packaging.

### `datefac/classification/`

Purpose:
- Table/class role classification helpers.

Not responsible for:
- Full extraction audit chains.

### `datefac/semantic/`

Purpose:
- Semantic adjudication, alias refinement, response reading, and semantic validation helpers.

Not responsible for:
- Direct MinerU runtime orchestration.

### `datefac/router/`

Purpose:
- Routing policies and router-side integration helpers.

Not responsible for:
- Human review workbook packaging.

### `datefac/utils/`

Purpose:
- Small reusable helpers such as artifact naming, logging, and run-state utilities.

Not responsible for:
- Numbered-task business orchestration.

### `datefac/vlm/`

Purpose:
- VLM-facing readers, prompt templates, quality gates, and mapping helpers.

Not responsible for:
- Current MinerU-first table-first mainline execution by default.

## Git-Tracked vs Local-Only

Normally Git-tracked:

- `datefac/`
- `docs/`
- `tools/`
- `tests/`

Normally local-only by default:

- `output/`
- `temp/`
- `_codex_test_tmp_*/`
- `_codex_debug_*/`
- large local PDFs and generated Excel artifacts unless explicitly requested

## Input / Output Boundary

Use `input/` for user-supplied or manually filled artifacts.
Use `output/` for generated artifacts.
Do not write generated outputs back into upstream input folders unless a task explicitly says so.

## MinerU-Related Directory Boundary

MinerU-related logic is spread across:

- `tools/` runnable scripts
- `datefac/benchmark/` pilot/retry/recovery sidecars
- `datefac/mineru_body/` MinerU body/table consumers
- `datefac/parser/` MinerU output reading
- `docs/demo/` and `docs/codex_tasks/` runbooks and task specs

This document does not redefine that structure.
It only explains it.

## Second-Phase Cleanup Principles

If a later structural cleanup is requested, follow these principles:

- Preserve import stability unless a dedicated refactor task approves path changes.
- Move code in small, reviewable batches.
- Separate source code cleanup from benchmark or trust-chain logic changes.
- Keep numbered task history intact.
- Do not mix directory cleanup with parser or extraction behavior changes.
- Update docs, READMEs, and task references together with any approved structural move.

## Current Non-Goals

This round does not:

- move core Python source files
- rename core package directories
- rewrite imports at scale
- rerun MinerU
- change benchmark conclusions
- change business logic
