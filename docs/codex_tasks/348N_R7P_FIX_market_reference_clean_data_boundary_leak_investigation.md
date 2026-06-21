# 348N-R7P-FIX Market Reference Clean Data Boundary Leak Investigation

## Goal

Investigate why `MARKET_REFERENCE_ROW` entered `clean_data` during the R7P non-Linyang workbook pilot.

This is a focused diagnosis / root-cause task.

Do not implement a fix unless the root cause is unambiguous, tiny, and fully covered by tests. Prefer diagnosis-first. If unsure, stop with a blocked investigation report.

R7P decision:

```text
348N_R7P_BLOCKED_BY_OUTPUT_GUARDRAIL_FAILURE
```

R7P blocking error:

```text
datefac_agent.audit.output_schema_guardrails.OutputSchemaGuardrailError:
clean_data boundary violation: row 0
(sheet='报告核心信息与投资要点' metric='收盘价')
has forbidden row_type 'MARKET_REFERENCE_ROW';
clean_data must not contain ['MARKET_REFERENCE_ROW', 'NORMALIZED_TESTSET_RECORD_ROW', 'TESTSET_SUPPORTING_ROW', 'UNKNOWN_ROW']
```

This is a valid guardrail catch. The task is to find the upstream reason the violating row became eligible for `clean_data`.

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
docs/agent/348N_R7P_ANOTHER_WORKBOOK_GUARDRAILS_PILOT_RESULT.md
docs/agent/348N_R7_QUALITATIVE_FACTS_NARROW_CLEAN_ADMISSION_POLICY_DESIGN.md
docs/agent/348N_R6D_QA_GUARDRAILS_CONTRACT_DOCUMENTATION_REVIEW.md
docs/agent/348N_R6B_FIX_QA_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_REVIEW.md
```

Inspect relevant implementation paths read-only first:

```text
datefac_agent/
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

Stop if worktree is not clean.

---

## Recommended thinking mode

```text
high
```

---

## Input that exposed the issue

Workbook:

```text
input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
```

PDF:

```text
input/H3_AP202605231822706325_1.pdf
```

Prior output directory, diagnostic only:

```text
output/agent_excel_intake_audit_348n_r7p_another_workbook_guardrails_pilot
```

Do not commit output artifacts.

---

## Investigation questions

Answer all of the following:

1. Where is `MARKET_REFERENCE_ROW` assigned?
2. Where is `clean_candidate_type` assigned for this row?
3. Where are `clean_rows` assembled?
4. Why did a row with forbidden row_type become part of `clean_rows`?
5. Is the root cause:
   - row typing error,
   - clean admission policy error,
   - workbook-family-specific path,
   - clean row assembly bug,
   - missing pre-guardrail filter,
   - or another cause?
6. Is `收盘价` correctly typed as `MARKET_REFERENCE_ROW`?
7. Should `MARKET_REFERENCE_ROW` ever be eligible for `clean_data`?
8. Should the row go to `review_queue`, a future `market_reference` output, or be excluded from clean output?
9. What is the narrowest safe fix?
10. What tests would prove the fix?

---

## Preferred outcome

Preferred result is a diagnosis report with a recommended fix plan.

Only implement a code fix in this task if all of these are true:

```text
root cause is unambiguous
change is tiny
change is local to active datefac_agent/tools/tests
no policy broadening is needed
existing guardrail contract remains strict
tests can prove the fix
```

If any condition is not true, do not modify source code. Create a blocked investigation report instead.

---

## Allowed changes

Diagnosis-only preferred allowed file:

```text
docs/agent/348N_R7P_FIX_MARKET_REFERENCE_CLEAN_DATA_BOUNDARY_LEAK_INVESTIGATION.md
```

If and only if implementing a tiny fix is clearly justified, allowed code/test files:

```text
datefac_agent/**/*.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
docs/agent/348N_R7P_FIX_MARKET_REFERENCE_CLEAN_DATA_BOUNDARY_LEAK_INVESTIGATION.md
```

Keep changes minimal. Do not touch unrelated files.

---

## Forbidden changes

Do not modify:

```text
legacy datefac/
input/
output/
temp/
data/
requirements.txt
requirements*.txt
pyproject.toml
setup.py
setup.cfg
Pipfile
poetry.lock
old docs/agent reports except the new R7P-FIX report
old docs/codex_tasks files
readiness gates
export behavior
```

Do not add dependencies.

Do not use Pydantic, Pandera, or pandas.

Do not run MinerU, OCR, LLM, or VLM.

Do not re-extract PDFs.

Do not submit output artifacts.

Do not use `git add .` or `git add -A`.

---

## Validation commands

Always run:

```powershell
python -m py_compile tools\run_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
git diff --check
```

If code is changed, also rerun the failing R7P pilot command to confirm whether it now passes or fails at a different boundary:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path "input/H3_AP202605231822706325_1.pdf" --excel-path "input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir "output/agent_excel_intake_audit_348n_r7p_fix_market_reference_boundary"
```

If no code is changed, do not rerun the pilot unless needed for diagnosis.

---

## Required report

Create:

```text
docs/agent/348N_R7P_FIX_MARKET_REFERENCE_CLEAN_DATA_BOUNDARY_LEAK_INVESTIGATION.md
```

The report must include:

```text
Task ID
Reviewed files
Failing row summary
Root-cause analysis
Row typing finding
Clean admission finding
Clean row assembly finding
Recommended fix
Whether code was changed
Validation result
Boundary check
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_R7P_FIX_CONFIRMED_MARKET_REFERENCE_BOUNDARY_ROOT_CAUSE
348N_R7P_FIX_IMPLEMENTED_MARKET_REFERENCE_BOUNDARY_FIX
348N_R7P_FIX_BLOCKED_BY_AMBIGUOUS_ROOT_CAUSE
348N_R7P_FIX_BLOCKED_BY_SCOPE_RISK
348N_R7P_FIX_BLOCKED_BY_TEST_FAILURE
```

---

## Required Data Result / 数据结果 fields

Include at least:

```text
Decision（任务结论）= ...
root_cause（根因）= ...
failing_row（失败行）= sheet='报告核心信息与投资要点', metric='收盘价', row_type='MARKET_REFERENCE_ROW'
row_typing_correct（row_type 是否正确）= yes/no/unclear
clean_admission_fault（是否 clean admission 问题）= yes/no/unclear
clean_row_assembly_fault（是否 clean row assembly 问题）= yes/no/unclear
recommended_fix（推荐修复）= ...
code_changes_made（是否改代码）= yes/no
pytest_result（测试结果）= ...
rerun_pilot_result（是否重跑 pilot）= ...
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
4. Root cause.
5. Whether row typing was correct.
6. Whether clean admission or clean row assembly was at fault.
7. Recommended fix.
8. Whether code was changed.
9. Validation commands and results.
10. Rerun pilot result if applicable.
11. Boundary check.
12. git status -sb.
13. Recommended next task.
14. Data Result / 数据结果.
