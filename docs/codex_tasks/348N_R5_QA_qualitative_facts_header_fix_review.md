# 348N-R5-QA Qualitative Facts Header Fix Review

## Goal

Review the R5 implementation that fixed `qualitative_facts` Chinese header detection.

This is a QA/review task. It should independently verify that R5 fixed the root cause identified in R4, did not mask the issue in `clean_candidate_policy`, and did not introduce regressions for existing workbook families.

R5 changed intake behavior so that `qualitative_facts` is recognized as a facts-schema/supporting sheet with the real header:

```text
事实ID, 页码, 类别, 主体, 指标/事件, 数值, 单位, 期间, 摘录/说明, 置信度
```

R5 expected result:

```text
clean_data_row_count: 33 -> 0
qualitative_facts_explicit_ref: 0/33 -> 34/34
qualitative_facts evidence: WEAK_EVIDENCE -> STRONG_EVIDENCE
unknown_row_count remains 0
normalized_testset_record_row_count remains 320
market_reference_row_count remains 10
pytest: 55 passed
external calls: 0
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
docs/codex_tasks/348N_R5_qualitative_facts_header_detection_fix.md
docs/agent/348N_R4_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
docs/agent/348N_R5_QUALITATIVE_FACTS_HEADER_DETECTION_FIX_RESULT.md
```

Also inspect the changed files:

```text
datefac_agent/intake/excel_intake.py
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

## Allowed changes

This QA task should only create:

```text
docs/agent/348N_R5_QA_QUALITATIVE_FACTS_HEADER_FIX_REVIEW.md
```

Do not modify source code, tests, input files, output files, generated pilot artifacts, or historical result/QA reports.

---

## Forbidden changes

Do not modify:

```text
datefac_agent/
tests/
tools/
legacy datefac/
input/
output/
temp/
data/
old docs/agent result reports
old docs/agent QA reports
old docs/codex_tasks files
readiness gates
```

Do not run MinerU, OCR, LLM, or VLM.

Do not re-extract PDFs.

Do not commit output artifacts.

Do not use `git add .` or `git add -A`.

---

## QA checklist

Verify all of the following:

### 1. Implementation boundary

Confirm R5 only changed the intended implementation/test/report files:

```text
datefac_agent/intake/excel_intake.py
tests/agent/test_agent_excel_intake_audit_348a.py
docs/agent/348N_R5_QUALITATIVE_FACTS_HEADER_DETECTION_FIX_RESULT.md
```

Confirm `clean_candidate_policy.py` was not changed to special-case `qualitative_facts`.

### 2. Correct layer

Confirm the fix is in intake/header detection, not in clean candidate policy.

Confirm the approach recognizes the real facts-schema header and does not merely ban the sheet by name from clean data.

### 3. Header detection correctness

Confirm:

```text
qualitative_facts real header row is detected
F001 data row is no longer selected as the header
事实ID / 页码 / 类别 / 指标/事件 / 数值 / 单位 / 期间 / 摘录/说明 / 置信度 are preserved as headers
```

### 4. Evidence recovery

Confirm:

```text
页码 is preserved as an evidence-bearing column
explicit_evidence_ref is restored for qualitative_facts rows
qualitative_facts evidence level becomes STRONG_EVIDENCE or the intended page-evidenced status
```

### 5. Clean-data boundary

Confirm:

```text
qualitative_facts rows no longer enter clean_data
clean_data_row_count for the R5 Linyang pilot is 0
review_queue_row_count grows accordingly
TESTSET_SUPPORTING_ROW routes to REVIEW_REQUIRED under existing policy
```

### 6. Regression coverage

Confirm no regression for:

```text
normalized_testset -> NORMALIZED_TESTSET_RECORD_ROW, count remains 320
market_base_data -> MARKET_REFERENCE_ROW, count remains 10
remaining unknown count remains 0
five Linyang financial sheets retain page evidence
prior workbook tests still pass
```

### 7. Test adequacy

Review the new tests and confirm they cover:

```text
real header detection
F001 data row not selected as header
page column preservation
explicit evidence extraction
metric extraction from 指标/事件
STRONG evidence + TESTSET_SUPPORTING_ROW + not clean
WEAK facts-schema supporting rows do not enter clean_data
```

### 8. Validation

Run at minimum:

```powershell
python -m py_compile datefac_agent\intake\excel_intake.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
git diff --check
```

Do not commit output directories.

If the R5 pilot output directory already exists, inspect it read-only:

```text
output/agent_excel_intake_audit_348n_r5_linyang_qualitative_facts_header_fix
```

If it is missing and the task report alone is insufficient to verify the before/after metrics, rerun the existing pilot command used by R5 into the same or a new R5-QA output directory. Do not commit that output.

### 9. External calls and gates

Confirm:

```text
LLM calls = 0
MinerU calls = 0
OCR calls = 0
VLM calls = 0
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

---

## Required QA report

Create:

```text
docs/agent/348N_R5_QA_QUALITATIVE_FACTS_HEADER_FIX_REVIEW.md
```

The report must include:

```text
Task ID
Reviewed files and artifacts
Implementation boundary QA
Correct-layer QA
Header detection QA
Evidence recovery QA
Clean-data boundary QA
Regression QA
Test adequacy QA
Validation result
External call QA
Readiness gate QA
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_R5_QA_CONFIRMED_QUALITATIVE_FACTS_HEADER_FIX_VALID
348N_R5_QA_BLOCKED_BY_IMPLEMENTATION_BOUNDARY_VIOLATION
348N_R5_QA_BLOCKED_BY_HEADER_DETECTION_REGRESSION
348N_R5_QA_BLOCKED_BY_CLEAN_DATA_BOUNDARY_REGRESSION
348N_R5_QA_BLOCKED_BY_TEST_COVERAGE_GAP
348N_R5_QA_BLOCKED_BY_MISSING_OUTPUT
```

---

## Required Data Result / 数据结果 fields

Include at least:

```text
Decision（任务结论）= ...
clean_data_row_count_before（修复前清洗数据行数）= 33
clean_data_row_count_after（修复后清洗数据行数）= ...
qualitative_facts_row_count（定性事实行数）= ...
qualitative_facts_explicit_ref_after（修复后显式证据引用）= ...
qualitative_facts_evidence_level_after（修复后证据级别）= ...
unknown_row_count（未知行数）= ...
normalized_testset_record_row_count（标准化测试集记录行数）= ...
market_reference_row_count（市场参考行数）= ...
pytest_result（测试结果）= ...
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= closed
clean_data_boundary（清洗数据边界）= ...
```

---

## Completion report

Report back with:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Implementation boundary QA.
5. Header detection QA.
6. Evidence recovery QA.
7. Clean-data boundary QA.
8. Regression QA.
9. Test adequacy QA.
10. Validation commands and results.
11. External call and readiness gate status.
12. git status -sb.
13. Recommended next task.
14. Data Result / 数据结果.
