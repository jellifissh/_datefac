# 348N-R6D-QA Guardrails Contract Documentation Review

## Goal

Independently review the R6D docs-only guardrails contract documentation update.

This is a QA/review task, not an implementation task.

R6D reported:

```text
348N_R6D_CONFIRMED_GUARDRAILS_CONTRACT_DOCUMENTED
```

R6D updated stable documentation so future models and future task reports consistently understand:

```text
validate_outputs(...) is the current Excel audit runner contract
logical row counts and physical CSV row counts are different
review_queue_row_count is not review_queue.csv physical row count
future reports must list both logical and physical counts when output guardrails are active
```

This QA task must verify that the documentation update is correct, concise, user-readable, and did not modify forbidden areas.

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
docs/agent/348N_R6D_GUARDRAILS_CONTRACT_DOCUMENTATION_UPDATE.md
docs/agent/348N_R6C_OUTPUT_GUARDRAILS_ADOPTION_REVIEW.md
docs/agent/348N_R6B_FIX_QA_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_REVIEW.md
```

Inspect updated target docs read-only:

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

Reason: this is a focused docs QA task. It needs careful reading, not code work.

---

## Allowed changes

This QA task should only create:

```text
docs/agent/348N_R6D_QA_GUARDRAILS_CONTRACT_DOCUMENTATION_REVIEW.md
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
old docs/agent historical reports except the new R6D-QA result report
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

### 1. Contract documentation QA

Verify `.skills/agent_excel_intake_audit_workflow.md` states:

```text
validate_outputs(...) is part of the current 348A-style / 348N-style Excel audit runner contract.
validate_outputs(...) runs before manifest success output is written.
Guardrail violations must fail loudly.
No Pydantic / Pandera / pandas dependency is required for this contract.
The contract applies to the current Agent Excel audit runner, not legacy datefac/ and not production/export readiness.
```

### 2. Count semantics QA

Verify the stable docs define:

```text
clean_data_row_count = logical clean row count
clean_data_csv_row_count = physical clean_data.csv data-row count
review_queue_row_count = historical logical non-clean / review-required pool count
review_queue_csv_row_count = physical review_queue.csv data-row count
unknown_row_count = logical UNKNOWN_ROW classification count
```

Verify the docs explicitly warn:

```text
Do not interpret review_queue_row_count as the physical review_queue.csv row count.
When discussing review_queue.csv, use review_queue_csv_row_count.
```

### 3. Future report template QA

Verify the docs say future output-guarded reports should list:

```text
clean_data_row_count
clean_data_csv_row_count
review_queue_row_count
review_queue_csv_row_count
unknown_row_count
output_guardrails = passed / failed
```

### 4. Project ledger QA

Verify `docs/agent/项目进程.md` has a concise milestone entry covering:

```text
R6B implemented guardrails
R6B-QA found clean_data_csv_row_count gap
R6B-FIX fixed it
R6B-FIX-QA confirmed it
R6C adopted guardrails as runner contract
R6D documented the contract
```

The ledger must remain compact. It should not paste full reports.

### 5. Plain-language explanation QA

Verify `项目进展大白话说明.md` explains in user-readable language:

```text
what output guardrails are
why logical counts and physical CSV counts differ
why review_queue_row_count != review_queue.csv row count
which fields to compare in future reports
```

The explanation should be understandable to a non-core developer. No legalese wall of doom.

### 6. Boundary QA

Confirm R6D did not modify:

```text
source code
tests
dependency files
input/output/legacy files
readiness gates
export behavior
```

### 7. Validation

Run:

```powershell
git diff --check
```

Do not run pytest unless code/tests were unexpectedly modified.

---

## Required QA report

Create:

```text
docs/agent/348N_R6D_QA_GUARDRAILS_CONTRACT_DOCUMENTATION_REVIEW.md
```

The report must include:

```text
Task ID
Reviewed files
Contract documentation QA
Count semantics QA
Future report template QA
Project ledger QA
Plain-language explanation QA
Boundary QA
Validation result
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_R6D_QA_CONFIRMED_GUARDRAILS_CONTRACT_DOCUMENTATION_VALID
348N_R6D_QA_BLOCKED_BY_CONTRACT_DOC_GAP
348N_R6D_QA_BLOCKED_BY_COUNT_SEMANTICS_GAP
348N_R6D_QA_BLOCKED_BY_PLAIN_LANGUAGE_DOC_GAP
348N_R6D_QA_BLOCKED_BY_SCOPE_VIOLATION
```

---

## Required Data Result / 数据结果 fields

Include at least:

```text
Decision（任务结论）= ...
guardrails_contract_documented（护栏契约是否写入文档）= yes/no
count_semantics_documented（计数语义是否写入文档）= yes/no
future_report_template_documented（未来报告模板是否写入文档）= yes/no
plain_language_doc_updated（大白话说明是否更新）= yes/no
project_ledger_updated（项目进程是否更新）= yes/no
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
4. Contract documentation QA.
5. Count semantics QA.
6. Future report template QA.
7. Project ledger QA.
8. Plain-language explanation QA.
9. Validation result.
10. Boundary check.
11. git status -sb.
12. Recommended next task.
13. Data Result / 数据结果.
