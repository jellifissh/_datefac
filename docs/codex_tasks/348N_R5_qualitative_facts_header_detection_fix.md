# 348N-R5 Qualitative Facts Header Detection Fix

## Goal

Fix the intake-layer header detection bug for the `qualitative_facts` sheet in the Linyang Energy workbook.

R4 confirmed that the 33 `qualitative_facts` rows should not stay in `clean_data` in their current state. The root cause is not the clean-candidate policy. The root cause is that intake failed to recognize the real Chinese header row:

```text
事实ID, 页码, 类别, 主体, 指标/事件, 数值, 单位, 期间, 摘录/说明, 置信度
```

Instead, intake accepted the `F001` data row as the header because `1995` matched the period regex. This caused page evidence loss, corrupted period labels, and accidental admission into clean data.

This task should fix the header detection path, add regression tests, rerun the pilot, and produce a result report.

---

## Current context

R4 decision:

```text
348N_R4_RECOMMENDS_QUALITATIVE_FACTS_REVIEW_ONLY_IMPLEMENTATION
```

R4 key findings:

```text
clean_data_row_count = 33
all 33 clean rows are qualitative_facts
all 33 are WEAK_EVIDENCE
0/33 have explicit page evidence
true header row was skipped
F001 data row was accepted as header
other financial sheets are STRONG_EVIDENCE, 76/76 with page evidence
fix should be intake header detection, not sheet-name policy masking
```

Expected effect after the fix:

```text
qualitative_facts true header is recognized
页码 column is preserved
explicit_evidence_ref is restored for qualitative_facts rows
qualitative_facts evidence becomes STRONG_EVIDENCE or equivalent page-evidenced status
these rows naturally leave clean_data through existing policy
clean_data_row_count for this workbook should drop from 33 to 0 unless a deliberately justified clean-admission rule is introduced later
unknown_row_count should remain 0
normalized_testset_record_row_count should remain 320
market_reference_row_count should remain 10
historical workbooks should not regress
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
docs/agent/348N_R4_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
docs/agent/348N_R3_QA_REMAINING_NON_NORMALIZED_UNKNOWN_FAMILY_REFINEMENT_REVIEW.md
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

Allowed source/test/report changes:

```text
datefac_agent/intake/excel_intake.py
tests/agent/test_agent_excel_intake_audit_348a.py
docs/agent/348N_R5_QUALITATIVE_FACTS_HEADER_DETECTION_FIX_RESULT.md
```

Only modify additional files if strictly necessary, and explain why in the result report.

---

## Forbidden changes

Do not modify:

```text
legacy datefac/
input/
output/
temp/
data/
old docs/agent result or QA reports
old docs/codex_tasks files
readiness gates except reporting unchanged values
```

Do not run MinerU, OCR, LLM, or VLM.

Do not re-extract PDFs.

Do not commit generated output artifacts.

Do not use `git add .` or `git add -A`.

---

## Implementation requirements

Fix the intake header detection so that `qualitative_facts` recognizes its real schema header.

Acceptable approaches:

1. Add a named/special header detection path for `qualitative_facts`, similar to existing special-sheet header handling.
2. Or safely broaden `_is_header_candidate` to recognize rows containing facts-schema headers such as `事实ID`, `页码`, `指标/事件`, `数值`, `单位`, `期间`, `摘录/说明`, `置信度`.

The fix must not make ordinary data rows easier to misclassify as headers.

The fix must not route by filename only. It should be based on sheet/header-family evidence.

Do not solve the issue by changing `clean_candidate_policy` to special-case `qualitative_facts`. R4 already identified that as the wrong layer.

---

## Test requirements

Add or update tests proving:

```text
real qualitative_facts Chinese header is detected as header
F001 data row is not selected as header when the real header exists
页码 column is preserved in parsed rows
explicit_evidence_ref is extracted from 页码
qualitative_facts rows become page-evidenced / STRONG_EVIDENCE in the pilot
qualitative_facts rows no longer enter clean_data under existing policy
normalized_testset behavior remains unchanged
market_base_data behavior remains unchanged
wide workbook classification does not regress
historical clean-data behavior does not regress unless explicitly explained
external call counters remain 0
readiness gates remain closed
```

Keep tests deterministic. Do not call external services.

---

## Validation commands

Run at minimum:

```powershell
python -m py_compile datefac_agent\intake\excel_intake.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
```

Then rerun the relevant Linyang R3-style pilot using the existing runner command or tool script already used for this series. Use a new output directory name for R5, for example:

```text
output/agent_excel_intake_audit_348n_r5_linyang_qualitative_facts_header_fix
```

Do not commit the output directory.

---

## Expected R5 result report

Create:

```text
docs/agent/348N_R5_QUALITATIVE_FACTS_HEADER_DETECTION_FIX_RESULT.md
```

Include:

```text
Task ID
Files modified
Implementation summary
Header detection fix details
Test coverage added
Pilot output directory
Before/after metrics
Qualitative_facts evidence result
Clean-data boundary result
Regression checks
External call check
Readiness gate check
Validation commands and results
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_R5_CONFIRMED_QUALITATIVE_FACTS_HEADER_FIX_VALID
348N_R5_BLOCKED_BY_HEADER_DETECTION_REGRESSION
348N_R5_BLOCKED_BY_CLEAN_DATA_BOUNDARY_REGRESSION
348N_R5_BLOCKED_BY_MISSING_OUTPUT
```

---

## Required Data Result / 数据结果 fields

Include at least:

```text
Decision（任务结论）= ...
clean_data_row_count_before（修复前清洗数据行数）= 33
clean_data_row_count_after（修复后清洗数据行数）= ...
qualitative_facts_row_count（定性事实行数）= ...
qualitative_facts_explicit_ref_before（修复前显式证据引用）= 0 / 33
qualitative_facts_explicit_ref_after（修复后显式证据引用）= ...
qualitative_facts_evidence_level_before（修复前证据级别）= WEAK_EVIDENCE
qualitative_facts_evidence_level_after（修复后证据级别）= ...
unknown_row_count（未知行数）= ...
normalized_testset_record_row_count（标准化测试集记录行数）= ...
market_reference_row_count（市场参考行数）= ...
pytest_result（测试结果）= ...
LLM / MinerU / OCR calls（外部调用次数）= 0
clean_data_boundary（清洗数据边界）= ...
```

---

## Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Implementation summary.
5. Tests added or updated.
6. Validation commands and results.
7. Pilot output directory.
8. Before/after metrics.
9. Whether code/tests/input/output boundaries were respected.
10. Whether external calls remained zero.
11. git status -sb.
12. Recommended next task.
13. Data Result / 数据结果.
