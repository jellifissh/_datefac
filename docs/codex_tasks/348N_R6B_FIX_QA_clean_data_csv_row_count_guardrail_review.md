# 348N-R6B-FIX-QA Clean Data CSV Row Count Guardrail Review

## Goal

Independently review the tiny R6B-FIX that completed the `clean_data_csv_row_count` guardrail.

This is a QA/review task, not an implementation task.

R6B-QA previously blocked R6B because:

```text
clean_data_csv_row_count was added but not validated.
```

R6B-FIX reported that the exact gap is now fixed:

```text
clean_data_csv_row_count mismatch now raises OutputSchemaGuardrailError
pytest = 75 passed
new_dependency_added = no
Pydantic/Pandera/pandas used = no
```

This QA task must independently confirm that.

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
docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md
docs/agent/348N_R6B_QA_OUTPUT_SCHEMA_GUARDRAILS_REVIEW.md
docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md
```

Inspect source/test files read-only:

```text
datefac_agent/audit/output_schema_guardrails.py
tests/agent/test_agent_excel_intake_audit_348a.py
tools/run_agent_excel_intake_audit_348a.py
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
high
```

Reason: this is a focused QA of a tiny guardrail completion. Do not expand into a full schema review.

---

## Allowed changes

This QA task should only create:

```text
docs/agent/348N_R6B_FIX_QA_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_REVIEW.md
```

Do not modify source code, tests, dependency files, input files, output files, generated output directories, or historical reports.

---

## Forbidden changes

Do not modify:

```text
datefac_agent/
tools/
tests/
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
readiness gates
export behavior
```

Do not add dependencies.

Do not use Pydantic, Pandera, or pandas.

Do not run MinerU, OCR, LLM, or VLM.

Do not re-extract PDFs.

Do not commit output artifacts.

Do not use `git add .` or `git add -A`.

---

## QA checklist

### 1. Implementation boundary QA

Confirm R6B-FIX only changed:

```text
datefac_agent/audit/output_schema_guardrails.py
tests/agent/test_agent_excel_intake_audit_348a.py
docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md
```

Confirm runner was not modified unless justified.

Confirm dependency/input/output/legacy boundaries were respected.

### 2. Exact gap fix QA

Confirm `validate_outputs(...)` now validates:

```text
len(clean_rows) == manifest["clean_data_csv_row_count"]
```

when `clean_data_csv_row_count` is present.

Confirm existing validation remains intact:

```text
len(clean_rows) == manifest["clean_data_row_count"]
len(review_rows) == manifest["review_queue_csv_row_count"]
```

### 3. Loud failure QA

Run or inspect a direct probe equivalent to:

```text
len(clean_rows) = 1
manifest["clean_data_row_count"] = 1
manifest["clean_data_csv_row_count"] = 999
validate_outputs(...) raises OutputSchemaGuardrailError
```

Confirm the error message mentions `clean_data_csv_row_count`.

### 4. Test coverage QA

Confirm the new test exists:

```text
test_output_schema_guardrails_clean_data_csv_count_mismatch_raises
```

Confirm it fails before the fix conceptually and passes now.

Confirm no previous guardrail tests were removed or weakened.

### 5. Manifest semantics QA

Confirm:

```text
clean_data_row_count remains validated
clean_data_csv_row_count is additive and now validated
review_queue_row_count historical semantics remain unchanged
review_queue_csv_row_count remains validated
```

### 6. Real pilot QA

If the R6B-FIX pilot output exists, inspect read-only:

```text
output/agent_excel_intake_audit_348n_r6b_fix_clean_data_csv_row_count_guardrail
```

Confirm reported values:

```text
clean_data_row_count = 0
clean_data_csv_row_count = 0
review_queue_row_count = 489
review_queue_csv_row_count = 46
unknown_row_count = 0
normalized_testset_record_row_count = 320
market_reference_row_count = 10
```

Do not commit output. Do not rerun unless necessary.

### 7. Validation

Run:

```powershell
python -m py_compile datefac_agent\audit\output_schema_guardrails.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
git diff --check
```

---

## Required QA report

Create:

```text
docs/agent/348N_R6B_FIX_QA_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_REVIEW.md
```

The report must include:

```text
Task ID
Reviewed files and artifacts
Implementation boundary QA
Exact gap fix QA
Loud failure QA
Test coverage QA
Manifest semantics QA
Real pilot QA
Validation result
External call QA
Readiness gate QA
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_R6B_FIX_QA_CONFIRMED_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_VALID
348N_R6B_FIX_QA_BLOCKED_BY_GAP_NOT_FIXED
348N_R6B_FIX_QA_BLOCKED_BY_TEST_FAILURE
348N_R6B_FIX_QA_BLOCKED_BY_SCOPE_OR_DEPENDENCY_VIOLATION
348N_R6B_FIX_QA_BLOCKED_BY_MANIFEST_SEMANTICS_REGRESSION
```

---

## Required Data Result / 数据结果 fields

Include at least:

```text
Decision（任务结论）= ...
fixed_gap_confirmed（是否确认修复缺口）= yes/no
clean_data_csv_row_count_mismatch_loud_fail（clean_data_csv_row_count mismatch 是否 loud fail）= yes/no
clean_data_row_count_guardrail（clean_data_row_count 护栏）= still valid / invalid
clean_data_csv_row_count_guardrail（clean_data_csv_row_count 护栏）= valid / invalid
review_queue_csv_row_count_guardrail（review_queue_csv_row_count 护栏）= still valid / invalid
new_dependency_added（是否新增依赖）= no
pydantic_used（是否使用 Pydantic）= no
pandera_used（是否使用 Pandera）= no
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
4. Implementation boundary QA.
5. Exact gap fix QA.
6. Loud failure QA.
7. Test coverage QA.
8. Manifest semantics QA.
9. Validation commands and results.
10. Whether any pilot was rerun.
11. git status -sb.
12. Recommended next task.
13. Data Result / 数据结果.
