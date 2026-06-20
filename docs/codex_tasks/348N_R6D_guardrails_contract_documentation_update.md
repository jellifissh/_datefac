# 348N-R6D Guardrails Contract Documentation Update

## Goal

Document the validated output schema guardrails as the standard runner contract for the current DateFac Agent Excel intake/audit runner.

This is a docs-only contract update task.

R6C decision:

```text
348N_R6C_RECOMMENDS_ADOPT_OUTPUT_GUARDRAILS_AS_RUNNER_CONTRACT
```

The goal is to make the guardrail contract and count semantics visible in stable project guidance so future tasks/reports do not confuse logical counts with physical CSV counts.

Do not modify code.

---

## Current context

The output guardrails are now validated:

```text
clean_data_row_count = validated
clean_data_csv_row_count = validated
review_queue_csv_row_count = validated
review_queue_row_count historical logical semantics = preserved
pytest = 75 passed
new_dependency_added = no
Pydantic/Pandera/pandas used = no
readiness_gates = closed / unchanged
```

R6C standardized count semantics:

```text
clean_data_row_count = logical clean row count
clean_data_csv_row_count = physical clean_data.csv data-row count
review_queue_row_count = historical logical non-clean / review-required pool count
review_queue_csv_row_count = physical review_queue.csv data-row count
unknown_row_count = logical UNKNOWN_ROW classification count
```

Critical rule:

```text
Do not interpret review_queue_row_count as the physical review_queue.csv row count.
When discussing the review_queue.csv file, use review_queue_csv_row_count.
```

Future reports with output guardrails should include:

```text
clean_data_row_count
clean_data_csv_row_count
review_queue_row_count
review_queue_csv_row_count
unknown_row_count
output_guardrails = passed / failed
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
docs/agent/348N_R6C_OUTPUT_GUARDRAILS_ADOPTION_REVIEW.md
docs/agent/348N_R6B_FIX_QA_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_REVIEW.md
```

Inspect current docs to update:

```text
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
项目进展大白话说明.md
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

Reason: this is a docs-only contract update. It requires care, not code archaeology cosplay.

---

## Allowed changes

Allowed files:

```text
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/agent/348N_R6D_GUARDRAILS_CONTRACT_DOCUMENTATION_UPDATE.md
```

Do not modify source code or tests.

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
old docs/agent historical reports except the new R6D result report
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

## Documentation requirements

### 1. `.skills/agent_excel_intake_audit_workflow.md`

Add a stable section explaining output schema guardrails as the current Excel audit runner contract.

Include:

```text
validate_outputs(...) is part of the current 348A-style / 348N-style Excel audit runner contract.
It runs before manifest success output is written.
Guardrail violations must fail loudly.
No Pydantic/Pandera/pandas dependency is required for this contract.
```

Document count semantics:

```text
clean_data_row_count = logical clean row count
clean_data_csv_row_count = physical clean_data.csv data-row count
review_queue_row_count = historical logical non-clean / review-required pool count
review_queue_csv_row_count = physical review_queue.csv data-row count
unknown_row_count = logical UNKNOWN_ROW classification count
```

Add report-template requirement:

```text
Future output-guarded reports must list both logical and physical CSV counts.
```

### 2. `docs/agent/项目进程.md`

Add a concise milestone entry for R6B/R6B-FIX/R6C/R6D.

It should say:

```text
R6B implemented stdlib-only output schema guardrails.
R6B-QA found clean_data_csv_row_count was not validated.
R6B-FIX fixed that gap.
R6B-FIX-QA confirmed the fix.
R6C recommended adopting output guardrails as current runner contract.
R6D documents the contract.
```

Keep this file concise. Do not dump full reports into it.

### 3. `项目进展大白话说明.md`

Add or update a plain-language section explaining:

```text
什么是 output guardrails
为什么 clean_data / review_queue 要分 logical count 和 physical CSV count
为什么 review_queue_row_count 不等于 review_queue.csv 行数
以后报告里应该同时看哪些字段
```

Keep it understandable to the user. Avoid turning it into a legal contract, because apparently humans will read it.

### 4. New R6D result report

Create:

```text
docs/agent/348N_R6D_GUARDRAILS_CONTRACT_DOCUMENTATION_UPDATE.md
```

Include what was updated and what rules were added.

---

## Validation commands

Run:

```powershell
git diff --check
```

No pytest required unless code/tests are modified, which should not happen.

---

## Required result report

Create:

```text
docs/agent/348N_R6D_GUARDRAILS_CONTRACT_DOCUMENTATION_UPDATE.md
```

Include:

```text
Task ID
Files modified
Documentation updates
Guardrails contract wording added
Count semantics wording added
Future report template wording added
Validation result
Boundary check
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_R6D_CONFIRMED_GUARDRAILS_CONTRACT_DOCUMENTED
348N_R6D_BLOCKED_BY_DOC_CONFLICT
348N_R6D_BLOCKED_BY_SCOPE_VIOLATION
```

---

## Required Data Result / 数据结果 fields

Include at least:

```text
Decision（任务结论）= ...
guardrails_contract_documented（护栏契约是否写入文档）= yes/no
count_semantics_documented（计数语义是否写入文档）= yes/no
future_report_template_documented（未来报告模板是否写入文档）= yes/no
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
4. Documentation updates.
5. Count semantics added.
6. Future report template wording added.
7. Validation result.
8. Whether dependency/input/output/legacy/code/test boundaries were respected.
9. git status -sb.
10. Recommended next task.
11. Data Result / 数据结果.
