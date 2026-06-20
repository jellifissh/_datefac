# 348N-R6B-FIX Clean Data CSV Row Count Guardrail Completion

## Goal

Fix the guardrail coverage gap found by R6B-QA.

This is a tiny implementation task. Do not expand scope.

R6B-QA decision:

```text
348N_R6B_QA_BLOCKED_BY_GUARDRAIL_COVERAGE_GAP
```

The specific blocker:

```text
R6B added manifest["clean_data_csv_row_count"] = len(clean_rows),
but validate_outputs(...) does not validate clean_data_csv_row_count.
```

Independent R6B-QA probe confirmed this invalid manifest still passes today:

```text
len(clean_rows) = 1
manifest["clean_data_row_count"] = 1
manifest["clean_data_csv_row_count"] = 999
validate_outputs(...) passes unexpectedly
```

The fix should make this mismatch raise `OutputSchemaGuardrailError`.

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
docs/agent/348N_R6B_QA_OUTPUT_SCHEMA_GUARDRAILS_REVIEW.md
docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md
docs/agent/348N_R6_SCHEMA_HARDENING_DESIGN.md
```

Inspect:

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
highest
```

Reason: implementation is tiny, but it touches guardrail semantics. Do not break `review_queue_row_count` / `review_queue_csv_row_count` compatibility.

---

## Allowed changes

Allowed files:

```text
datefac_agent/audit/output_schema_guardrails.py
tests/agent/test_agent_excel_intake_audit_348a.py
docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md
```

Only modify `tools/run_agent_excel_intake_audit_348a.py` if strictly necessary. It should probably not be necessary because the runner already populates `clean_data_csv_row_count` and `review_queue_csv_row_count` before calling `validate_outputs(...)`.

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

## Implementation requirements

### 1. Validator fix

Update:

```text
datefac_agent/audit/output_schema_guardrails.py
```

Add validation for:

```text
if "clean_data_csv_row_count" exists in manifest:
    len(clean_rows) must equal manifest["clean_data_csv_row_count"]
```

This should be analogous to the existing `review_queue_csv_row_count` validation.

If the project already has a helper for count validation, reuse it.

Failure must raise:

```text
OutputSchemaGuardrailError
```

with a clear message naming:

```text
clean_data_csv_row_count
expected / actual values, or manifest / actual values
```

Do not remove the existing validation for `clean_data_row_count`.

Both should be valid:

```text
len(clean_rows) == manifest["clean_data_row_count"]
len(clean_rows) == manifest["clean_data_csv_row_count"]  # when present
```

### 2. Negative test

Add a test proving the exact R6B-QA probe now fails:

```text
clean_data_row_count = len(clean_rows)
clean_data_csv_row_count != len(clean_rows)
validate_outputs(...) raises OutputSchemaGuardrailError
```

The test should fail before the fix and pass after the fix.

Prefer direct in-memory unit test of `validate_outputs(...)`.

### 3. Regression tests

Keep existing tests passing.

Do not weaken or delete existing guardrail tests.

### 4. Result report

Create:

```text
docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md
```

The report should state the exact gap, the exact fix, and validation result.

---

## Validation commands

Run at minimum:

```powershell
python -m py_compile datefac_agent\audit\output_schema_guardrails.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
git diff --check
```

Also rerun the Linyang pilot if cheap, to confirm the fixed guardrail still passes on real output:

```text
output/agent_excel_intake_audit_348n_r6b_fix_clean_data_csv_row_count_guardrail
```

Do not commit that output directory.

---

## Required result report

Create:

```text
docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md
```

Include:

```text
Task ID
Files modified
Implementation summary
Exact guardrail gap fixed
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
348N_R6B_FIX_CONFIRMED_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_VALID
348N_R6B_FIX_BLOCKED_BY_TEST_FAILURE
348N_R6B_FIX_BLOCKED_BY_SCOPE_OR_DEPENDENCY_VIOLATION
348N_R6B_FIX_BLOCKED_BY_PILOT_FAILURE
```

---

## Required Data Result / 数据结果 fields

Include at least:

```text
Decision（任务结论）= ...
fixed_gap（修复缺口）= clean_data_csv_row_count mismatch now raises OutputSchemaGuardrailError
new_dependency_added（是否新增依赖）= no
pydantic_used（是否使用 Pydantic）= no
pandera_used（是否使用 Pandera）= no
clean_data_row_count_guardrail（clean_data_row_count 护栏）= still valid
clean_data_csv_row_count_guardrail（clean_data_csv_row_count 护栏）= implemented / valid
review_queue_csv_row_count_guardrail（review_queue_csv_row_count 护栏）= still valid
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
5. Exact guardrail gap fixed.
6. Tests added or updated.
7. Validation commands and results.
8. Whether any pilot was rerun.
9. Whether dependency/input/output/legacy boundaries were respected.
10. git status -sb.
11. Recommended next task.
12. Data Result / 数据结果.
