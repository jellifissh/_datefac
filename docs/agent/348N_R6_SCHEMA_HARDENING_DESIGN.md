## Task ID

`348N-R6 Schema Hardening Design`

## Reviewed files

Read-only inspection (no files modified by this design task):

- `datefac_agent/schemas/audit_models.py` — internal data models
- `datefac_agent/intake/excel_intake.py` — intake + header detection
- `datefac_agent/review/clean_candidate_policy.py` — clean candidate classification
- `datefac_agent/review/review_queue_builder.py` — review queue + row audit result
- `datefac_agent/delivery/evidence_index_writer.py` — JSON/CSV output writers
- `datefac_agent/audit/evidence_checker.py` — evidence level logic (context)
- `tools/run_agent_excel_intake_audit_348a.py` — runner, manifest builder, clean_data CSV builder
- `tests/agent/test_agent_excel_intake_audit_348a.py` — test patterns
- `requirements.txt` — dependency manifest
- Context docs: `AGENTS.md`, `.skills/*`, `CURRENT_MODEL_HANDOFF.md`, R4/R5/R5-QA reports

## Current schema state

The active `datefac_agent/` package uses a **lightweight internal schema layer built on stdlib only** — no Pydantic, no Pandera, no pandas inside the package.

Representation:

```text
Internal models : @dataclass(slots=True) + Literal type aliases
                   (SpreadsheetRow, AuditRowResult, AuditSummary, EvidenceRef, ...)
Type enums       : Literal string unions, not Enum
                   EvidenceLevel / RowType / CleanCandidateType / AuditDecision.decision
Outputs          : hand-built dict[str, str|Any] -> csv.DictWriter (CSV)
                                       -> json.dumps (JSON)
clean_data.csv   : 10-field dict from _row_to_clean_csv (runner)
review_queue.csv : 12-field dict from build_review_queue_rows
evidence_index   : list of hand-built dicts (write_evidence_index)
manifest         : ~45-field hand-built dict from build_manifest, gates/counters hardcoded
```

Key observation: `clean_data_row_count` in the manifest is computed as `len(clean_rows)` in the runner, but nothing re-checks that the written `clean_data.csv` row count matches the manifest count, and nothing asserts the clean-data boundary invariants that R4/R5 found were violated (e.g. "clean_data must not contain TESTSET_SUPPORTING_ROW"). The gates are hardcoded `False` literals with no assertion that they remain closed.

## Pydantic usage assessment

**Current usage: none.**

`grep` for `pydantic` across `datefac_agent/` returns zero matches. `requirements.txt` does not list pydantic.

Fit assessment (if adopted):

- **Manifest schema** — strong fit. The manifest is a single nested dict with typed counters, closed gates, and external-call counters. A Pydantic model would enforce types (int vs str), required fields, and gate defaults, and could assert `client_ready is False` at construction. This is the highest-value Pydantic target.
- **Run summary schema** — good fit, mirrors manifest subset.
- **Evidence item schema** — moderate fit; the dataclass `AuditRowResult`/`EvidenceRef` already carry `Literal` types, so Pydantic would add runtime validation but limited new information over the existing `Literal` aliases.
- **Review queue item schema** — moderate fit; object-level validation is possible but the CSV is already flat and string-typed.
- **Task config / future API** — good fit for later stages, not needed now.

Risks: adds a runtime dependency; pydantic v1 vs v2 migration surface; over-modeling the flat CSV rows. For the current pilot stage the manifest is the only place where Pydantic's value clearly exceeds the existing `dataclass`+`Literal` approach.

## Pandera usage assessment

**Current usage: none.**

`grep` for `pandera` across `datefac_agent/` returns zero matches. `requirements.txt` does not list pandera. (`pandas` is listed but the active package does not import it; it is a legacy-script dependency.)

Fit assessment (if adopted):

- **clean_data.csv / review_queue.csv schema validation** — strong fit in principle. Pandera DataFrame schemas express exactly the guardrails R4/R5 needed: column presence, non-null, enum constraints on `row_type`/`clean_candidate_type`, and **forbidden-value constraints** (`row_type` must not be `TESTSET_SUPPORTING_ROW` in clean_data).
- **Audit table validation** — good fit.
- **row_type enum constraints / non-null / forbidden-row-type** — this is Pandera's core strength and the single most relevant capability for the R4/R5 boundary-inversion class of bug.

Risks: Pandera pulls in pandas as a hard runtime dependency for the active package (currently pandas-free); pandas DataFrame construction from the existing dict-list outputs adds an intermediate representation; Pandera's schema API has churned across versions. Introducing it means the active package gains a pandas dependency it does not currently have, just to validate CSVs it already writes from dicts.

## Schema hardening targets

The first guardrails — the ones that would have caught or reduced the R4/R5 problem directly:

```text
clean_data must not contain row_type in {TESTSET_SUPPORTING_ROW, NORMALIZED_TESTSET_RECORD_ROW, MARKET_REFERENCE_ROW, UNKNOWN_ROW}
clean_data must not contain clean_candidate_type != {INTERNAL_CLEAN_CANDIDATE, INTERNAL_REFERENCE_CANDIDATE}
clean_data row count (CSV) == manifest clean_data_row_count
review_queue rows must have non-empty decision / clean_candidate_type / evidence_level
manifest readiness gates all False; demo_export_only True
manifest external-call counters (llm/mineru/ocr) == 0
manifest exposes clean_data_row_count / review_queue_row_count / unknown_row_count
legacy_datefac_touched == False; legacy_outputs_touched == False
```

These are boundary invariants, not field-type niceties. The first two are precisely what R4/R5 caught only via manual QA; encoding them as assertions would catch the next inversion at build time.

## Minimal recommended implementation

**Recommendation: A — Lightweight internal validation first, no new dependency.**

Rationale:

1. The active package is intentionally stdlib-only (`dataclass` + `Literal` + `csv` + `json`). The R4/R5 gap was not a lack of schema framework — it was a lack of **boundary invariant assertions**. Those assertions are ~30 lines of plain Python checking enum membership and forbidden row types against the existing dicts.
2. Pandera's strongest capability (forbidden-value constraints on a DataFrame) is exactly what is needed, but it costs a pandas dependency the package does not have. That is not justified for validating three small CSVs that are already in memory as dict-lists.
3. Pydantic's clearest win is the manifest, but the manifest gates/counters are already hardcoded literals; an assertion `assert client_ready is False` captures the same guarantee today without a dependency.
4. The project is at `demo_export_only=True` with closed gates and a single pilot sample. Adding framework dependencies now is premature; the validation logic should prove its value first, and a framework can be layered on top of stable assertions later if complexity grows.

Not recommended now:
- **B (Pandera only)** — introduces pandas into a pandas-free active package for marginal gain over dict assertions.
- **C (Pydantic only)** — covers the manifest well but leaves the clean_data boundary (the actual R4/R5 failure site) to ad-hoc checks anyway.
- **D (Pandera + Pydantic together)** — two new dependencies; violates "be conservative, do not recommend a large refactor."

Phased option (deferred, not the first step): if the pilot grows to many workbooks or an API surface appears, revisit Pydantic for the manifest/run-summary and Pandera for batch CSV validation. That decision belongs to a later design task after the lightweight guardrails prove out.

## Where validation should run

For the current stage, the lowest-risk placement is a **validation helper called inside the runner, after output generation and before the manifest is finalized/returned** — combined with unit tests that exercise the same validator directly.

```text
Placement : new module datefac_agent/audit/output_schema_guardrails.py
Called by : tools/run_agent_excel_intake_audit_348a.py run_pilot(), after write_csv_rows / write_evidence_index, before returning the manifest
Also      : unit tests in tests/agent/ call the validator directly on constructed dicts
```

Why here:

- It runs on the real outputs every pilot run, so an inversion is caught immediately, not only in QA.
- It sits after output generation, so it validates what was actually written (dicts in memory that mirror the CSV/JSON), not a separate reconstruction.
- It does not gate delivery (gates are closed anyway), so a failure surfaces as a raised assertion / error in the manifest's `decision`, not a silent export.
- Tests call the validator directly for determinism, independent of the xlsx pilot.

Not recommended now:
- Tests-only placement — would not catch inversions in actual pilot runs between QA cycles (exactly the R4/R5 gap).
- Future delivery/export gate placement — correct eventually, but premature while gates are closed and there is no export path.

## Risks and non-goals

Risks of the recommended lightweight approach:

- Plain assertions lack Pandera's rich error reporting; mitigated by clear assertion messages naming the offending row/sheet.
- Without a framework, schema drift (new manifest field) is not auto-detected; mitigated by a required-fields set check in the validator.
- If the team later wants typed API request/response models, Pydantic will still need to be added then — this task does not preclude it.

Non-goals (explicitly out of scope for the first implementation):

- Migrating `audit_models.py` dataclasses to Pydantic.
- Adding pandas to the active package.
- Validating `input/` workbooks (intake correctness is covered by R5 + tests).
- Any change to readiness gates or export paths.
- Large refactor of the runner.

## Validation result

```text
git pull --ff-only origin pivot/348-agent-foundation
  -> fast-forward 3c0e7ce..142e4f4 (R6 task doc + handoff), then up to date

git status -sb before editing
  -> clean (## pivot/348-agent-foundation...origin/pivot/348-agent-foundation)

git diff --check
  -> clean (no whitespace/conflict errors; design-only, no code changes)
```

No pytest required (no code/tests changed). No dependencies installed. No code, tests, dependency files, input, output, or historical reports modified.

## Decision

`348N_R6_RECOMMENDS_LIGHTWEIGHT_SCHEMA_GUARDRAILS_FIRST`

The active package is stdlib-only and the R4/R5 gap was missing boundary-invariant assertions, not missing a schema framework. Add a small internal `output_schema_guardrails` validator (no new dependency) that asserts the clean-data forbidden-row-type invariants, CSV/manifest count consistency, and closed gates. Defer Pandera/Pydantic to a later design task if complexity grows.

## Recommended next task

```text
348N-R6B output schema guardrails implementation
```

Scope (narrow and testable):

- New module `datefac_agent/audit/output_schema_guardrails.py` with a `validate_outputs(...)` function taking the clean_rows dict-list, review_rows dict-list, and manifest dict.
- Assertions: clean_data forbidden row_types/clean_candidate_types; clean CSV row count == manifest `clean_data_row_count`; review_queue required fields non-empty; manifest gates closed; external-call counters zero; `legacy_*_touched` False.
- Runner calls `validate_outputs` after writing outputs, before returning the manifest; on failure sets `decision` to a `_NEEDS_FIX` value and records the violation.
- Unit tests constructing passing and intentionally-violating dicts (e.g. a TESTSET_SUPPORTING_ROW sneaking into clean_rows must raise).
- No new dependencies; no change to gates or export paths.

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R6_RECOMMENDS_LIGHTWEIGHT_SCHEMA_GUARDRAILS_FIRST
current_pydantic_usage（当前 Pydantic 使用）= no
current_pandera_usage（当前 Pandera 使用）= no
recommended_first_schema_layer（推荐第一层 schema）= lightweight internal output_schema_guardrails validator (stdlib only, no new dependency)
first_guardrail_targets（第一批护栏目标）= clean_data forbidden row_type/clean_candidate_type; clean CSV count == manifest count; review_queue required fields; manifest gates closed; external-call counters zero; legacy_*_touched False
code_changes_made（是否改代码）= no
pytest_result（测试结果）= not run / not required
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= unchanged / closed
recommended_next_task（推荐下一任务）= 348N-R6B output schema guardrails implementation
```
