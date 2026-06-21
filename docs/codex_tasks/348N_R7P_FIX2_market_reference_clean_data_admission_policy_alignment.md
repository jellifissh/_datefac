# 348N-R7P-FIX2 Market Reference Clean Data Admission Policy Alignment

## Goal

Align `clean_candidate_policy.py` with the current output guardrail contract so `MARKET_REFERENCE_ROW` no longer becomes eligible for `clean_data` through `INTERNAL_REFERENCE_CANDIDATE`.

This is a tiny implementation fix task.

R7P-FIX confirmed the root cause:

```text
clean_candidate_policy.py still maps MARKET_REFERENCE_ROW + WEAK_EVIDENCE + no unit issue -> INTERNAL_REFERENCE_CANDIDATE
clean_rows assembly includes INTERNAL_REFERENCE_CANDIDATE
output_schema_guardrails forbids MARKET_REFERENCE_ROW in clean_data
```

The policy and guardrail contract are inconsistent. Fix the policy, not the guardrail.

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
docs/agent/348N_R7P_FIX_MARKET_REFERENCE_CLEAN_DATA_BOUNDARY_LEAK_INVESTIGATION.md
docs/agent/348N_R7P_ANOTHER_WORKBOOK_GUARDRAILS_PILOT_RESULT.md
docs/agent/348N_R7_QUALITATIVE_FACTS_NARROW_CLEAN_ADMISSION_POLICY_DESIGN.md
docs/agent/348N_R6D_QA_GUARDRAILS_CONTRACT_DOCUMENTATION_REVIEW.md
```

Inspect:

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

## Required behavior change

Currently, market-reference rows can become clean-output eligible:

```text
MARKET_REFERENCE_ROW + WEAK_EVIDENCE + no unit issue -> INTERNAL_REFERENCE_CANDIDATE
```

This must change to:

```text
MARKET_REFERENCE_ROW -> REVIEW_REQUIRED
```

for the current 348A/348N Excel audit runner contract.

Do not broaden clean admission policy.

Do not change row typing.

Do not weaken output guardrails.

Do not change clean row assembly unless tests prove it is necessary. Current diagnosis says clean row assembly is not the bug.

---

## Failing pilot row

```text
workbook = input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
pdf = input/H3_AP202605231822706325_1.pdf
sheet = 报告核心信息与投资要点
metric = 收盘价
row_type = MARKET_REFERENCE_ROW
old clean_candidate_type = INTERNAL_REFERENCE_CANDIDATE
```

The fix should prevent this row type from entering `clean_data` through clean admission.

---

## Allowed changes

Allowed files:

```text
datefac_agent/review/clean_candidate_policy.py
tests/agent/test_agent_excel_intake_audit_348a.py
docs/agent/348N_R7P_FIX2_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_ALIGNMENT_RESULT.md
```

Only modify these files unless absolutely necessary. If another file seems necessary, stop and explain before editing.

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
old docs/agent reports except the new FIX2 result report
old docs/codex_tasks files
readiness gates
export behavior
output_schema_guardrails contract
row_type_classifier semantics
```

Do not add dependencies.

Do not use Pydantic, Pandera, or pandas.

Do not run MinerU, OCR, LLM, or VLM.

Do not re-extract PDFs.

Do not submit output artifacts.

Do not use `git add .` or `git add -A`.

---

## Required tests

Add or update tests to prove:

1. `MARKET_REFERENCE_ROW + WEAK_EVIDENCE + no unit issue -> REVIEW_REQUIRED`
2. `MARKET_REFERENCE_ROW + WEAK_EVIDENCE + unit issue -> REVIEW_REQUIRED` still holds
3. No forbidden market-reference row can become `INTERNAL_REFERENCE_CANDIDATE`
4. Existing clean/review/output guardrail tests still pass

If there is an existing test expecting market-reference rows to become `INTERNAL_REFERENCE_CANDIDATE`, update it and explain why the expectation changed after R6 guardrail contract adoption.

---

## Validation commands

Run:

```powershell
python -m py_compile datefac_agent\review\clean_candidate_policy.py tools\run_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
python tools\run_agent_excel_intake_audit_348a.py --pdf-path "input/H3_AP202605231822706325_1.pdf" --excel-path "input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir "output/agent_excel_intake_audit_348n_r7p_fix2_market_reference_boundary"
git diff --check
```

Pilot rerun expectations:

- The previous `MARKET_REFERENCE_ROW entered clean_data` guardrail failure should be gone.
- If a new guardrail failure appears, stop and report it. Do not broaden policy to force success.
- Do not commit output directory.

---

## Required result report

Create:

```text
docs/agent/348N_R7P_FIX2_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_ALIGNMENT_RESULT.md
```

Include:

```text
Task ID
Files modified
Policy change
Tests added/updated
Validation commands and results
Taihao pilot rerun result
Output guardrails result
Boundary check
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_R7P_FIX2_IMPLEMENTED_MARKET_REFERENCE_POLICY_ALIGNMENT
348N_R7P_FIX2_BLOCKED_BY_TEST_FAILURE
348N_R7P_FIX2_BLOCKED_BY_NEW_GUARDRAIL_FAILURE
348N_R7P_FIX2_BLOCKED_BY_SCOPE_RISK
```

---

## Required Data Result / 数据结果 fields

Include at least:

```text
Decision（任务结论）= ...
policy_change（策略变更）= MARKET_REFERENCE_ROW -> REVIEW_REQUIRED
market_reference_internal_reference_candidate_allowed（是否仍允许 MARKET_REFERENCE_ROW -> INTERNAL_REFERENCE_CANDIDATE）= no
pytest_result（测试结果）= ...
taihao_pilot_rerun（泰豪 pilot 重跑）= ...
previous_market_reference_guardrail_failure_fixed（此前 MARKET_REFERENCE_ROW clean_data guardrail failure 是否消失）= yes/no
new_guardrail_failure（是否出现新 guardrail failure）= yes/no/details
code_changes_made（是否改代码）= yes
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
4. Policy change.
5. Tests added/updated.
6. Validation commands and results.
7. Taihao pilot rerun result.
8. Whether previous guardrail failure is fixed.
9. Whether new guardrail failure appeared.
10. Boundary check.
11. git status -sb.
12. Recommended next task.
13. Data Result / 数据结果.
