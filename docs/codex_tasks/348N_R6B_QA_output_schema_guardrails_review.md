# 348N-R6B-QA Output Schema Guardrails Review

## Goal

Independently review the R6B output schema guardrails implementation.

This is a QA/review task, not an implementation task.

R6B implemented a stdlib-only guardrail layer in:

```text
datefac_agent/audit/output_schema_guardrails.py
```

and integrated it into:

```text
tools/run_agent_excel_intake_audit_348a.py
```

The QA task must verify that the guardrails are correct, fail loudly on violations, preserve historical manifest semantics, and introduce no dependency/input/output/legacy boundary violation.

---

## Current context

R6B reported:

```text
348N_R6B_CONFIRMED_OUTPUT_SCHEMA_GUARDRAILS_VALID
new_dependency_added = no
pydantic_used = no
pandera_used = no
guardrail_module = datefac_agent/audit/output_schema_guardrails.py
pytest_result = 74 passed
LLM / MinerU / OCR / VLM calls = 0
readiness_gates = closed / unchanged
```

R6B pilot values:

```text
clean_data_row_count = 0
clean_data_csv_row_count = 0
review_queue_row_count = 489
review_queue_csv_row_count = 46
unknown_row_count = 0
normalized_testset_record_row_count = 320
market_reference_row_count = 10
testset_supporting_row_count = 83
```

Important compatibility note:

```text
review_queue_row_count is a historical logical count.
review_queue_csv_row_count is the physical review_queue.csv row count added by R6B.
```

Do not collapse or rename these semantics in QA.

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
docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md
docs/agent/348N_R6_SCHEMA_HARDENING_DESIGN.md
docs/agent/348N_R5_QA_QUALITATIVE_FACTS_HEADER_FIX_REVIEW.md
```

Inspect source/test files read-only:

```text
datefac_agent/audit/output_schema_guardrails.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Also inspect dependency/config files read-only to verify no new dependency was added:

```text
requirements.txt
requirements*.txt
pyproject.toml
setup.py
setup.cfg
Pipfile
poetry.lock
```

Only inspect files that exist.

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

Reason: this QA reviews code, runner integration, manifest semantics, and failure-mode coverage.

---

## Allowed changes

This QA task should only create:

```text
docs/agent/348N_R6B_QA_OUTPUT_SCHEMA_GUARDRAILS_REVIEW.md
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

Confirm R6B only changed the intended files:

```text
datefac_agent/audit/output_schema_guardrails.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md
```

Confirm dependency files were not modified.

### 2. Dependency QA

Confirm:

```text
Pydantic not added
Pandera not added
pandas not newly introduced into datefac_agent active package
no new runtime dependency added
```

### 3. Guardrail correctness QA

Confirm `validate_outputs(...)` checks:

```text
clean_data forbidden row_type values
clean_data allowed clean_candidate_type values
missing row_type / clean_candidate_type fails
clean_data count matches manifest clean_data_row_count / clean_data_csv_row_count as applicable
review_queue CSV count matches manifest review_queue_csv_row_count
manifest exposes clean_data_row_count / review_queue_row_count / unknown_row_count
review_queue required fields are non-empty
readiness gates are closed
external-call counters are zero
legacy touch flags remain false when present
```

### 4. Loud failure QA

Confirm guardrail violations raise `OutputSchemaGuardrailError` or an equivalent explicit failure.

Confirm the runner does not swallow the exception, silently downgrade it, or write a success manifest after a guardrail violation.

### 5. Runner integration QA

Confirm runner integration point is safe:

```text
clean_rows, review_rows, and manifest are built
clean_data_csv_row_count and review_queue_csv_row_count are set
validate_outputs(clean_rows, review_rows, manifest) runs before manifest JSON is written
```

### 6. Manifest semantics QA

Confirm historical `review_queue_row_count` semantics are preserved.

Confirm `review_queue_csv_row_count` is additive and does not replace the historical logical count.

Confirm `clean_data_csv_row_count` is additive or at least does not break existing manifest semantics.

### 7. Test coverage QA

Confirm tests cover:

```text
valid outputs pass
forbidden clean_data row_type raises for all four forbidden values
invalid clean_candidate_type raises
clean_data count mismatch raises
review_queue CSV count mismatch raises
review_queue required field empty raises
gates opened raises
external counter nonzero raises
legacy touch true raises
```

### 8. Real pilot QA

Inspect the R6B pilot output directory read-only if present:

```text
output/agent_excel_intake_audit_348n_r6b_output_schema_guardrails
```

Confirm reported manifest values:

```text
clean_data_row_count = 0
clean_data_csv_row_count = 0
review_queue_row_count = 489
review_queue_csv_row_count = 46
unknown_row_count = 0
normalized_testset_record_row_count = 320
market_reference_row_count = 10
```

If output is missing, do not rerun unless necessary. The QA can rely on source/tests/report if sufficient. If rerun is needed, do not commit output.

### 9. Validation

Run:

```powershell
python -m py_compile datefac_agent\audit\output_schema_guardrails.py tools\run_agent_excel_intake_audit_348a.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
git diff --check
```

---

## Required QA report

Create:

```text
docs/agent/348N_R6B_QA_OUTPUT_SCHEMA_GUARDRAILS_REVIEW.md
```

The report must include:

```text
Task ID
Reviewed files and artifacts
Implementation boundary QA
Dependency QA
Guardrail correctness QA
Loud failure QA
Runner integration QA
Manifest semantics QA
Test coverage QA
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
348N_R6B_QA_CONFIRMED_OUTPUT_SCHEMA_GUARDRAILS_VALID
348N_R6B_QA_BLOCKED_BY_SCOPE_OR_DEPENDENCY_VIOLATION
348N_R6B_QA_BLOCKED_BY_GUARDRAIL_COVERAGE_GAP
348N_R6B_QA_BLOCKED_BY_RUNNER_INTEGRATION_ISSUE
348N_R6B_QA_BLOCKED_BY_MANIFEST_SEMANTICS_REGRESSION
348N_R6B_QA_BLOCKED_BY_TEST_FAILURE
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
guardrail_loud_fail（护栏是否 loud fail）= yes/no
runner_integration_before_manifest_write（runner 是否在写 manifest 前验证）= yes/no
review_queue_row_count_semantics_preserved（review_queue_row_count 语义是否保留）= yes/no
review_queue_csv_row_count_added（是否新增物理 CSV 行数字段）= yes/no
clean_data_forbidden_row_type_guardrail（clean_data 禁止 row_type 护栏）= valid/invalid
count_consistency_guardrail（计数一致性护栏）= valid/invalid
review_queue_required_fields_guardrail（review_queue 必填字段护栏）= valid/invalid
manifest_gate_guardrail（manifest 就绪门护栏）= valid/invalid
external_counter_guardrail（外部调用计数护栏）= valid/invalid
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
5. Dependency QA.
6. Guardrail correctness QA.
7. Loud failure QA.
8. Runner integration QA.
9. Manifest semantics QA.
10. Test coverage QA.
11. Validation commands and results.
12. Whether any pilot was rerun.
13. git status -sb.
14. Recommended next task.
15. Data Result / 数据结果.
