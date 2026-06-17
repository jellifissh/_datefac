# 348S-R2-QA Unit/Period Residual Refinement Review

## 中文说明

本任务只做 QA 审查，不改源码。

348S-R2 宣称已经收敛 R1-QA 确认的 7 行 residual false-positive-style issue：

```text
2 个 unit issue：资产负债率(%) / 资产负债率(%,LF)
5 个 period issue：盈利预测分业务 embedded period header
```

R2 后第二样本指标：

```text
unit_issue_count: 2 -> 0
period_issue_count: 5 -> 0
clean_data_row_count: 87 -> 94
review_queue_row_count: 25 -> 18
fail_count: 2 -> 0
```

本任务要确认：这 7 行是不是被正确修复，而不是被误放行。

---

## 1. Goal

Review `348S-R2 Unit/Period Residual Refinement`.

This is a QA-only task.

Do not modify source code.

Do not change audit rules.

Do not rerun MinerU, LLM, VLM, OCR, or PDF extraction.

---

## 2. Required context

Read only:

```text
AGENTS.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
docs/agent/348S_R2_UNIT_PERIOD_RESIDUAL_REFINEMENT_RESULT.md
docs/agent/348S_R1_QA_INTAKE_GENERALIZATION_REVIEW.md
```

Then inspect the output directories listed below.

---

## 3. Working directory

Use:

```text
D:\_datefac_agent
```

Expected branch:

```text
pivot/348-agent-foundation
```

Preflight:

```powershell
cd D:\_datefac_agent
git pull --ff-only origin pivot/348-agent-foundation
git status -sb
git branch --show-current
```

Stop if the worktree is not clean.

---

## 4. Output directories to review

Second sample R2 output:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348s_r2_h3_ap202605231822706325_1
```

Baseline regression R2 output:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348s_r2_regression_348a_baseline
```

R1 comparison output:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_h3_ap202605231822706325_1
```

Review these files when present:

```text
agent_excel_intake_audit_348a_manifest.json
agent_excel_intake_audit_348a_run_summary.json
audit_report.md
evidence_index.json
review_queue.csv
clean_data.csv
```

Do not modify output files.

---

## 5. QA questions

### 5.1 Unit residual QA

Confirm the 2 prior unit residual rows are no longer false failures:

```text
报告概要 / 资产负债率(%,LF)
重要财务与估值指标 / 资产负债率(%)
```

Check:

```text
They should not trigger monetary_unit_mismatch.
They should be treated as ratio/rate metrics.
True amount metrics such as 资产总计(%) and 负债合计(%) should still fail in tests.
```

### 5.2 Period residual QA

Confirm the 5 prior period residual rows from `盈利预测分业务` are no longer false failures:

```text
应急电源
通信指挥系统
军用电源装备
其他业务
合计
```

Check that embedded period headers are recognized:

```text
2025A收入(亿元)
2026E收入(亿元)
2027E收入(亿元)
2028E收入(亿元)
2026E毛利率(%)
```

They should not trigger `period_context_missing` if period context is actually present.

### 5.3 Clean-data quality

Confirm `clean_data.csv` after R2:

```text
clean_data_row_count = 94
```

Check:

```text
No unit issue rows leak into clean_data.
No period issue rows leak into clean_data.
No valuation issue rows leak into clean_data.
No narrative rows leak into clean_data.
Only expected weak-evidence internal candidates enter clean_data.
```

### 5.4 Review-queue quality

Confirm `review_queue.csv` after R2:

```text
review_queue_row_count = 18
```

Check:

```text
The 7 residual false-positive rows are no longer in review queue for unit/period reasons.
The remaining 18 rows are narrative/review-worthy rows.
No clean-data candidates are duplicated back into review queue.
```

### 5.5 Baseline regression

Confirm first baseline sample did not regress:

```text
row_count_total = 82
fail_count = 0
unit_issue_count = 0
period_issue_count = 2
clean_data_row_count = 75
review_queue_row_count = 7
unknown_row_count = 0
```

### 5.6 Gate discipline

Confirm both R2 outputs still have:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
```

---

## 6. Validation

Run:

```powershell
cd D:\_datefac_agent
python -m pytest tests\agent -q
```

If no Python files are changed, py_compile is not required.

---

## 7. Expected report

Create:

```text
docs/agent/348S_R2_QA_UNIT_PERIOD_RESIDUAL_REFINEMENT_REVIEW.md
```

Include:

```text
Task ID
Reviewed output directories
Verified metrics
Unit residual QA
Period residual QA
Clean-data quality analysis
Review-queue quality analysis
Baseline regression analysis
Gate discipline analysis
Remaining risks
Decision
Recommended next task
```

Suggested decision values:

```text
348S_R2_QA_CONFIRMED_RESIDUAL_REFINEMENT_VALID
348S_R2_QA_CONFIRMED_PARTIAL_REFINEMENT_REMAINING_RISKS
348S_R2_QA_CONFIRMED_NEEDS_PERIOD_MODEL_REVIEW
348S_R2_QA_CONFIRMED_NEEDS_UNIT_RULE_REVIEW
```

Choose one primary decision.

---

## 8. Non-goals

Do not edit source code.

Do not edit task docs.

Do not commit output files.

Do not touch legacy `datefac/`.

Do not touch old `D:\_datefac`.

Do not run MinerU / OCR / LLM / VLM.

Do not re-extract the PDF.

Do not use:

```text
git add .
git add -A
git reset --hard
git checkout --
```

---

## 9. Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Which output directories and files were reviewed.
5. Verified second sample R2 metrics.
6. Verified baseline regression metrics.
7. Unit residual QA findings.
8. Period residual QA findings.
9. Clean-data quality findings.
10. Review queue quality findings.
11. Gate discipline findings.
12. Remaining risks.
13. pytest result.
14. Whether source code was untouched.
15. Whether output files were not committed.
16. Whether LLM/MinerU/OCR calls were zero.
17. `git status -sb`.
18. Recommended next task.

---

## 10. Likely next tasks

If QA passes:

```text
348F Fixture Harvest from 346B
348S Third Workbook Pilot
```

If QA finds issues:

```text
348S-R3 Targeted Residual Repair
```
