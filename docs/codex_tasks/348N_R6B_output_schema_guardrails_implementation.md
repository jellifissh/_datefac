# 348N-R6B Output Schema Guardrails Implementation

## Goal

Implement lightweight internal output schema guardrails for DateFac Agent, following the R6 design decision.

This is an implementation task.

Do not add Pandera, Pydantic, pandas, or any new dependency. The first guardrail layer must be stdlib-only.

R6 decision:

```text
348N_R6_RECOMMENDS_LIGHTWEIGHT_SCHEMA_GUARDRAILS_FIRST
```

R6 recommended adding a small internal validator to catch boundary inversions like the R4/R5 `qualitative_facts` leak earlier and automatically.

---

## Current context

R5-QA confirmed:

```text
348N_R5_QA_CONFIRMED_QUALITATIVE_FACTS_HEADER_FIX_VALID
clean_data_row_count: 33 -> 0
qualitative_facts_explicit_ref: 0/33 -> 34/34
qualitative_facts_evidence_level: WEAK_EVIDENCE -> STRONG_EVIDENCE
unknown_row_count = 0
normalized_testset_record_row_count = 320
market_reference_row_count = 10
pytest = 55 passed
LLM / MinerU / OCR / VLM calls = 0
readiness_gates = closed
```

R6 confirmed:

```text
current_pydantic_usage = no
current_pandera_usage = no
recommended_first_schema_layer = lightweight internal output_schema_guardrails validator
first_guardrail_targets = clean_data forbidden row_type/clean_candidate_type; clean CSV count == manifest count; review_queue required fields; manifest gates closed; external-call counters zero; legacy_*_touched False
```

---

## Required context

Read:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348N_R6_SCHEMA_HARDENING_DESIGN.md
docs/agent/348N_R5_QA_QUALITATIVE_FACTS_HEADER_FIX_REVIEW.md
```

Inspect:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

---

## Preflight

```powershell
cd D:\_datefac_agent
git pull --ff-only origin pivot/348-agent-foundation
git status -sb
git branch --show-current
```

Stop if the worktree is not clean.

---

## Recommended thinking mode

```text
highest
```

Reason: this is a small implementation, but it touches runner validation and must avoid breaking existing pilots/tests.

---

## Allowed changes

Allowed files:

```text
datefac_agent/audit/output_schema_guardrails.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md
```

Only modify additional files if strictly necessary, and explain why in the result report.

---

## Forbidden changes

Do not modify:

```text
requirements.txt
requirements*.txt
pyproject.toml
setup.py
setup.cfg
Pipfile
poetry.lock
legacy datefac/
input/
output/
temp/
data/
old docs/agent reports
old docs/codex_tasks files
readiness gate meanings
export behavior
```

Do not add Pydantic, Pandera, pandas, or any new dependency.

Do not run MinerU, OCR, LLM, or VLM.

Do not re-extract PDFs.

Do not commit output artifacts.

Do not use `git add .` or `git add -A`.

---

## Implementation requirements

### 1. New guardrail module

Create:

```text
datefac_agent/audit/output_schema_guardrails.py
```

It should expose a clear validation function, for example:

```python
validate_outputs(clean_rows: list[dict], review_rows: list[dict], manifest: dict) -> None
```

A custom exception is allowed and preferred, for example:

```python
class OutputSchemaGuardrailError(ValueError):
    pass
```

Use stdlib only.

### 2. Clean-data guardrails

The validator must fail if any clean row violates these invariants:

```text
row_type must NOT be TESTSET_SUPPORTING_ROW
row_type must NOT be NORMALIZED_TESTSET_RECORD_ROW
row_type must NOT be MARKET_REFERENCE_ROW
row_type must NOT be UNKNOWN_ROW
clean_candidate_type must be INTERNAL_CLEAN_CANDIDATE or INTERNAL_REFERENCE_CANDIDATE
```

If a field is missing, fail with a clear message.

### 3. Count consistency guardrails

The validator must check:

```text
len(clean_rows) == manifest["clean_data_row_count"]
len(review_rows) == manifest["review_queue_row_count"]
manifest exposes clean_data_row_count / review_queue_row_count / unknown_row_count
```

If the runner's manifest names differ, use the actual field names already present, but preserve the intent.

### 4. Review queue guardrails

Each review row must have non-empty required fields, at minimum:

```text
decision
clean_candidate_type
evidence_level
```

If existing review rows use different exact field names, choose the closest actual fields and document it in the result report.

### 5. Manifest guardrails

The validator must confirm:

```text
client_ready is False
production_ready is False
formal_client_export_allowed is False
demo_export_only is True
llm_api_call_count == 0
mineru_run_count == 0
ocr_run_count == 0
legacy_datefac_touched is False
legacy_outputs_touched is False
```

If a legacy field does not exist yet, either add a guarded presence requirement only if the manifest already includes it, or document why it is not enforced yet. Do not invent unrelated manifest semantics without checking the existing manifest.

### 6. Runner integration

Integrate `validate_outputs(...)` in:

```text
tools/run_agent_excel_intake_audit_348a.py
```

Preferred placement: after the runner has built the clean rows, review rows, and manifest, and before it returns / reports final success.

Do not hide validation failures. A guardrail violation should fail the run loudly, with a clear error message.

Do not silently downgrade the run to success.

### 7. Tests

Add tests for:

```text
valid outputs pass
clean_data containing TESTSET_SUPPORTING_ROW raises
clean_data containing NORMALIZED_TESTSET_RECORD_ROW raises
clean_data containing MARKET_REFERENCE_ROW raises
clean_data containing UNKNOWN_ROW raises
invalid clean_candidate_type raises
clean_data count mismatch raises
review_queue required field missing/empty raises
manifest gates opened raises
external call counter nonzero raises
```

Tests should be deterministic and should not call external services.

Prefer direct unit tests of `validate_outputs(...)` using small in-memory dict lists.

Also keep existing agent tests passing.

---

## Validation commands

Run at minimum:

```powershell
python -m py_compile datefac_agent\audit\output_schema_guardrails.py tools\run_agent_excel_intake_audit_348a.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
git diff --check
```

If relevant and cheap, rerun the latest Linyang pilot to confirm the guardrail passes on real R5-style output. Do not commit output directories.

---

## Required result report

Create:

```text
docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md
```

Include:

```text
Task ID
Files modified
Implementation summary
Guardrails implemented
Runner integration point
Tests added
Validation commands and results
Pilot result if rerun
External call check
Readiness gate check
Boundary check
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_R6B_CONFIRMED_OUTPUT_SCHEMA_GUARDRAILS_VALID
348N_R6B_BLOCKED_BY_RUNNER_INTEGRATION_ISSUE
348N_R6B_BLOCKED_BY_TEST_FAILURE
348N_R6B_BLOCKED_BY_MANIFEST_FIELD_MISMATCH
348N_R6B_BLOCKED_BY_SCOPE_OR_DEPENDENCY_VIOLATION
```

---

## Required Data Result / 数据结果 fields

Include at least:

```text
Decision（任务结论）= ...
new_dependency_added（是否新增依赖）= no
pydantic_used（是否使用 Pydantic）= no
pandera_used（是否使用 Pandera）= no
guardrail_module（护栏模块）= datefac_agent/audit/output_schema_guardrails.py
clean_data_forbidden_row_type_guardrail（clean_data 禁止 row_type 护栏）= implemented / not implemented
clean_candidate_type_guardrail（clean 候选类型护栏）= implemented / not implemented
count_consistency_guardrail（计数一致性护栏）= implemented / not implemented
review_queue_required_fields_guardrail（review_queue 必填字段护栏）= implemented / not implemented
manifest_gate_guardrail（manifest 就绪门护栏）= implemented / not implemented
external_counter_guardrail（外部调用计数护栏）= implemented / not implemented
pytest_result（测试结果）= ...
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= closed / unchanged
```

---

## Completion report

Report back with:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Implementation summary.
5. Guardrails implemented.
6. Runner integration point.
7. Tests added or updated.
8. Validation commands and results.
9. Whether any pilot was rerun.
10. Whether dependency/input/output/legacy boundaries were respected.
11. git status -sb.
12. Recommended next task.
13. Data Result / 数据结果.
