# 348N-R6C Output Guardrails Adoption Review

## Goal

Review whether the now-validated output schema guardrails should be adopted as the standard runner contract for the DateFac Agent Excel intake/audit workflow.

This is a focused adoption/design review task, not a code implementation task.

R6B and R6B-FIX established a stdlib-only guardrail layer. R6B-FIX-QA confirmed that the final known gap is fixed:

```text
348N_R6B_FIX_QA_CONFIRMED_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_VALID
```

Now decide how this should be documented and treated in future tasks:

```text
Should output schema guardrails be considered part of the runner contract?
Should future reports consistently distinguish logical row counts from physical CSV row counts?
Should a short contract document be created in a later task?
```

Do not modify code in this task.

---

## Current context

Confirmed guardrail status:

```text
clean_data_row_count is validated
clean_data_csv_row_count is validated
review_queue_csv_row_count is validated
review_queue_row_count historical logical semantics are preserved
clean_data forbidden row_type guardrails are active
review_queue required fields are checked
manifest gates remain closed
external-call counters remain zero
no new dependency added
Pydantic/Pandera/pandas not used
pytest = 75 passed
```

Important count semantics:

```text
clean_data_row_count = logical clean row count
clean_data_csv_row_count = physical clean_data.csv row count
review_queue_row_count = historical logical non-clean / review-required pool count
review_queue_csv_row_count = physical review_queue.csv row count
```

R6B-FIX-QA recommended:

```text
348N-R6C output guardrails adoption review
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
docs/agent/348N_R6B_FIX_QA_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_REVIEW.md
docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md
docs/agent/348N_R6B_QA_OUTPUT_SCHEMA_GUARDRAILS_REVIEW.md
docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md
docs/agent/348N_R6_SCHEMA_HARDENING_DESIGN.md
```

Inspect read-only:

```text
datefac_agent/audit/output_schema_guardrails.py
tools/run_agent_excel_intake_audit_348a.py
docs/agent/项目进程.md
.skills/agent_excel_intake_audit_workflow.md
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

Reason: this is a focused design/review task. Do not expand into implementation.

---

## Allowed changes

This task should only create:

```text
docs/agent/348N_R6C_OUTPUT_GUARDRAILS_ADOPTION_REVIEW.md
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

## Review questions

### 1. Contract adoption

Decide whether `validate_outputs(...)` should be considered part of the standard runner contract for this workflow.

Answer:

```text
yes / no / yes but only for demo Excel audit runner for now
```

Explain why.

### 2. Count semantics standardization

Decide how future task reports should name and interpret row counts.

At minimum, evaluate:

```text
clean_data_row_count
clean_data_csv_row_count
review_queue_row_count
review_queue_csv_row_count
unknown_row_count
```

Clarify which are logical counts and which are physical CSV counts.

### 3. Future report template

Recommend whether future DateFac Agent result reports should always include both logical and physical row counts when output guardrails are active.

### 4. Skill / handoff documentation needs

Decide whether the guardrail contract should be documented in a future update to:

```text
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
项目进展大白话说明.md
```

Do not update them in this task unless absolutely necessary. Prefer recommending a follow-up docs task.

### 5. Next implementation/design task

Recommend the next task after R6C. Candidate directions:

```text
A. 348N-R6D guardrails contract documentation update
B. 348N-R7 qualitative_facts narrow clean-admission policy design
C. 348N-R7 pilot another workbook family under guardrails
D. 348N-R7 export/delivery gate preparation
```

Pick one and explain the sequence.

---

## Validation commands

Since this is docs/design-only, run:

```powershell
git diff --check
```

No pytest is required unless code is unexpectedly modified, which should not happen.

---

## Required report

Create:

```text
docs/agent/348N_R6C_OUTPUT_GUARDRAILS_ADOPTION_REVIEW.md
```

The report must include:

```text
Task ID
Reviewed files
Contract adoption decision
Count semantics standardization
Future report template recommendation
Skill/handoff documentation recommendation
Risks and non-goals
Validation result
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_R6C_RECOMMENDS_ADOPT_OUTPUT_GUARDRAILS_AS_RUNNER_CONTRACT
348N_R6C_RECOMMENDS_LIMITED_GUARDRAIL_ADOPTION_FOR_DEMO_RUNNER_ONLY
348N_R6C_BLOCKED_BY_MISSING_CONTEXT
```

---

## Required Data Result / 数据结果 fields

Include at least:

```text
Decision（任务结论）= ...
guardrails_contract_adoption（护栏契约采用）= ...
logical_counts（逻辑计数字段）= ...
physical_csv_counts（物理 CSV 计数字段）= ...
future_reports_include_both_counts（未来报告是否同时列出两类计数）= yes/no
code_changes_made（是否改代码）= no
pytest_result（测试结果）= not run / not required
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= unchanged / closed
recommended_next_task（推荐下一任务）= ...
```

---

## Completion report

Report back with:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Contract adoption decision.
5. Count semantics standardization.
6. Future report template recommendation.
7. Documentation recommendation.
8. Validation result.
9. Whether dependency/input/output/legacy boundaries were respected.
10. git status -sb.
11. Recommended next task.
12. Data Result / 数据结果.
