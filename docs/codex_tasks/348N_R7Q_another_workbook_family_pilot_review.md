# 348N-R7Q Another Workbook Family Pilot Review

## Goal

Review the Taihao non-Linyang workbook pilot as a standalone guarded-pilot result after the R7P-FIX2 market-reference policy alignment.

This is a review / diagnosis task, not an implementation task.

The purpose is to characterize the new clean/review shape after the market-reference boundary leak was fixed and decide the safest next direction.

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
docs/agent/348N_R7P_FIX2_QA_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_REVIEW.md
docs/agent/348N_R7P_FIX2_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_ALIGNMENT_RESULT.md
docs/agent/348N_R7P_FIX_MARKET_REFERENCE_CLEAN_DATA_BOUNDARY_LEAK_INVESTIGATION.md
docs/agent/348N_R7P_ANOTHER_WORKBOOK_GUARDRAILS_PILOT_RESULT.md
docs/agent/348N_R7_QUALITATIVE_FACTS_NARROW_CLEAN_ADMISSION_POLICY_DESIGN.md
```

Review generated pilot artifacts read-only, if present locally:

```text
output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/agent_excel_intake_audit_348a_manifest.json
output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/clean_data.csv
output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/review_queue.csv
output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/evidence_index.json
```

Do not commit output artifacts.

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

## Review target

Workbook:

```text
input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
```

PDF:

```text
input/H3_AP202605231822706325_1.pdf
```

Post-FIX2 QA pilot output directory:

```text
output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary
```

Known post-FIX2 QA manifest values:

```text
decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
clean_data_row_count = 92
clean_data_csv_row_count = 92
review_queue_row_count = 66
review_queue_csv_row_count = 66
unknown_row_count = 0
market_reference_row_count = 2
normalized_testset_record_row_count = 0
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

---

## Questions to answer

Answer all of the following:

1. What does the Taihao pilot now show after the market-reference fix?
2. Does `clean_data` now appear free of forbidden row types?
3. What is the clean/review split after FIX2?
4. What are the dominant row types in `clean_data.csv` and `review_queue.csv`?
5. Are there remaining high-confidence rows stuck in review_queue?
6. Are there facts-like or qualitative-like rows worth future policy design?
7. Does this workbook expose a different class of boundary issue after market-reference alignment?
8. Does `AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX` represent a remaining system issue, expected review pressure, or insufficient confidence?
9. Should the next task be another workbook-family pilot, a focused policy design, or a QA expansion?
10. Should any readiness gate change? Default answer should remain no unless evidence is overwhelming.

---

## Allowed changes

Create only:

```text
docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md
```

No code or test changes are expected.

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

Do not submit output artifacts.

Do not use `git add .` or `git add -A`.

---

## Validation commands

Run:

```powershell
git diff --check
```

If you read local output artifacts and want to confirm manifest values with a small script, use only Python stdlib and read-only file access. Do not modify output.

No pytest is required unless code or tests are unexpectedly changed. Code and tests should not be changed.

---

## Required report

Create:

```text
docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md
```

The report must include:

```text
Task ID
Input workbook
Reviewed artifacts
Manifest summary
Clean/review split
Clean data boundary assessment
Review queue assessment
Facts-like / qualitative-like observation
Remaining risks
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_R7Q_CONFIRMED_TAIHAO_GUARDED_PILOT_REVIEW_VALID
348N_R7Q_RECOMMENDS_ANOTHER_WORKBOOK_FAMILY_PILOT
348N_R7Q_RECOMMENDS_FOCUSED_POLICY_DESIGN
348N_R7Q_BLOCKED_BY_MISSING_OUTPUT_ARTIFACTS
348N_R7Q_BLOCKED_BY_SCOPE_VIOLATION
```

---

## Required Data Result / 数据结果 fields

Include at least:

```text
Decision（任务结论）= ...
input_workbook（输入 workbook）= ...
post_fix2_pilot_decision（FIX2 后 pilot decision）= ...
clean_data_row_count（逻辑 clean 行数）= ...
clean_data_csv_row_count（clean CSV 物理行数）= ...
review_queue_row_count（逻辑 review/non-clean 池行数）= ...
review_queue_csv_row_count（review_queue CSV 物理行数）= ...
unknown_row_count（UNKNOWN_ROW 逻辑计数）= ...
market_reference_row_count（market reference 行数）= ...
forbidden_clean_row_type_found（clean_data 是否仍有 forbidden row_type）= yes/no/unknown
facts_like_schema_found（是否发现 facts-like schema）= yes/no/unknown
qualitative_facts_like_rows（类似 qualitative_facts 行）= ...
readiness_gates（就绪门）= unchanged / closed
code_changes_made（是否改代码）= no
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
recommended_next_task（推荐下一任务）= ...
```

---

## Completion report

Report back with:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Reviewed artifacts.
5. Manifest summary.
6. Clean/review split.
7. Clean data boundary assessment.
8. Review queue assessment.
9. Facts-like / qualitative-like observation.
10. Decision.
11. Validation result.
12. Boundary check.
13. git status -sb.
14. Recommended next task.
15. Data Result / 数据结果.
