# 348N-R7P-FIX2-QA Market Reference Clean Data Admission Policy Review

## Goal

Independently review the R7P-FIX2 implementation that aligned market-reference clean admission with the current output guardrail contract.

This is a focused QA / review task, not a new implementation task.

R7P-FIX2 decision to review:

```text
348N_R7P_FIX2_IMPLEMENTED_MARKET_REFERENCE_POLICY_ALIGNMENT
```

Required behavior after FIX2:

```text
MARKET_REFERENCE_ROW -> REVIEW_REQUIRED
```

`MARKET_REFERENCE_ROW` must no longer become `INTERNAL_REFERENCE_CANDIDATE` in the current 348A/348N runner contract.

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
docs/agent/348N_R7P_FIX2_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_ALIGNMENT_RESULT.md
docs/agent/348N_R7P_FIX_MARKET_REFERENCE_CLEAN_DATA_BOUNDARY_LEAK_INVESTIGATION.md
docs/agent/348N_R7P_ANOTHER_WORKBOOK_GUARDRAILS_PILOT_RESULT.md
```

Review implementation files:

```text
datefac_agent/review/clean_candidate_policy.py
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

Stop if worktree is not clean.

---

## Recommended thinking mode

```text
high
```

---

## What to verify

Verify all of the following:

1. `datefac_agent/review/clean_candidate_policy.py` now routes `MARKET_REFERENCE_ROW` to `REVIEW_REQUIRED`.
2. No `MARKET_REFERENCE_ROW` path still returns `INTERNAL_REFERENCE_CANDIDATE`.
3. `row_type_classifier` semantics were not changed.
4. `output_schema_guardrails` contract was not weakened.
5. `clean_rows` assembly was not changed unless clearly justified.
6. Tests cover both:
   - `MARKET_REFERENCE_ROW + WEAK_EVIDENCE + no unit issue -> REVIEW_REQUIRED`
   - `MARKET_REFERENCE_ROW + WEAK_EVIDENCE + unit issue -> REVIEW_REQUIRED`
7. Existing routing fixture expectations were updated consistently.
8. Full agent tests pass.
9. Taihao pilot no longer fails with the previous `MARKET_REFERENCE_ROW entered clean_data` guardrail error.
10. No new guardrail failure appears during Taihao pilot rerun.
11. Output artifacts are not committed.
12. Readiness gates stay closed.
13. External call counters remain zero.

---

## Commands to run

Run:

```powershell
python -m py_compile datefac_agent\review\clean_candidate_policy.py tools\run_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
python tools\run_agent_excel_intake_audit_348a.py --pdf-path "input/H3_AP202605231822706325_1.pdf" --excel-path "input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir "output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary"
git diff --check
```

Do not commit output directory.

---

## Allowed changes

Create only:

```text
docs/agent/348N_R7P_FIX2_QA_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_REVIEW.md
```

This is a QA task. Do not modify code or tests unless you find a blocking issue. If a blocking issue is found, stop and report it in the QA report rather than fixing it.

---

## Forbidden changes

Do not modify:

```text
datefac_agent/ source files
tests/
legacy datefac/
input/
output/
temp/
data/
dependency files
readiness gates
export behavior
old docs/agent reports
old docs/codex_tasks files
```

Do not add dependencies.

Do not use Pydantic, Pandera, or pandas.

Do not run MinerU, OCR, LLM, or VLM.

Do not re-extract PDFs.

Do not use `git add .` or `git add -A`.

---

## Required report

Create:

```text
docs/agent/348N_R7P_FIX2_QA_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_REVIEW.md
```

The report must include:

```text
Task ID
Reviewed files
Policy behavior verification
Test coverage verification
Taihao pilot rerun verification
Output guardrails verification
Boundary check
Validation commands and results
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_R7P_FIX2_QA_CONFIRMED_MARKET_REFERENCE_POLICY_ALIGNMENT_VALID
348N_R7P_FIX2_QA_BLOCKED_BY_POLICY_REGRESSION
348N_R7P_FIX2_QA_BLOCKED_BY_TEST_FAILURE
348N_R7P_FIX2_QA_BLOCKED_BY_NEW_GUARDRAIL_FAILURE
348N_R7P_FIX2_QA_BLOCKED_BY_SCOPE_VIOLATION
```

---

## Required Data Result / 数据结果 fields

Include at least:

```text
Decision（任务结论）= ...
market_reference_policy_valid（market reference 策略是否有效）= yes/no
market_reference_internal_reference_candidate_allowed（是否仍允许 MARKET_REFERENCE_ROW -> INTERNAL_REFERENCE_CANDIDATE）= no/yes
pytest_result（测试结果）= ...
taihao_pilot_rerun（泰豪 pilot 重跑）= ...
previous_market_reference_guardrail_failure_fixed（此前 MARKET_REFERENCE_ROW clean_data guardrail failure 是否消失）= yes/no
new_guardrail_failure（是否出现新 guardrail failure）= yes/no/details
code_changes_made（是否改代码）= no
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
4. Policy behavior verification.
5. Test coverage verification.
6. Validation commands and results.
7. Taihao pilot rerun result.
8. Whether previous guardrail failure is fixed.
9. Whether new guardrail failure appeared.
10. Boundary check.
11. git status -sb.
12. Recommended next task.
13. Data Result / 数据结果.
