# 348S-R2 Unit/Period Residual Refinement

## 中文说明 / Chinese Summary

### 任务目标

348S-R1 已经把第二真实样本的 intake 泛化修好大半：

```text
unknown_row_count: 53 -> 0
period_issue_count: 66 -> 5
clean_data_row_count: 0 -> 87
```

348S-R1-QA 确认这是真改善，不是漏读数据。但 QA 也确认剩下两个窄问题：

```text
1. 盈利预测分业务 的 5 个 period false-positive-style issue
2. 资产负债率(%) 的 2 个 unit false-positive-style issue
```

本任务只收敛这两个残留误报。

### 不要做什么

```text
不要重构 intake
不要重写 row-type classifier
不要修改 clean candidate policy
不要关闭 period checker
不要删除 unit checker
不要为了让 clean_data 好看而强行放行所有 REVIEW
不要跑 MinerU / LLM / OCR
不要重新抽 PDF
```

### 期望结果

第二真实样本：

```text
unit_issue_count: 2 -> 0 或明显下降
period_issue_count: 5 -> 0 或明显下降
clean_data_row_count: 87 -> 上升
review_queue_row_count: 25 -> 下降
```

baseline 348A/R4：

```text
不能回退
unit_issue_count 仍应为 0
period_issue_count 仍应为 2
clean_data_row_count 仍应接近 75
review_queue_row_count 仍应接近 7
```

---

## 1. Goal

Refine the residual unit and period false-positive-style issues found after `348S-R1 Intake Schema Generalization`.

This is a narrow refinement task. Do not broaden scope.

The target residuals are:

```text
5 period issues in 盈利预测分业务
2 unit issues related to 资产负债率(%) / 资产负债率(%,LF)
```

---

## 2. Required context

Read these files first:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
.skills/project_milestone_ledger.md

datefac_agent/README.md
docs/agent/348S_R1_INTAKE_SCHEMA_GENERALIZATION_RESULT.md
docs/agent/348S_R1_QA_INTAKE_GENERALIZATION_REVIEW.md

docs/codex_tasks/348S_R1_intake_schema_generalization.md
docs/codex_tasks/348S_R1_QA_intake_generalization_review.md
```

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

## 4. Inputs / outputs

Use the second real sample:

```text
PDF:   D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf
Excel: D:\_datefac_agent\input\H3_AP202605231822706325_1_提取结果.xlsx
Output:D:\_datefac_agent\output\agent_excel_intake_audit_348s_r2_h3_ap202605231822706325_1
```

Also rerun the first baseline regression sample:

```text
PDF:   D:\_datefac_agent\input\H3_AP202606081823352906_1_331fresh_20260615_21591.pdf
Excel: D:\_datefac_agent\input\安井食品研报数据汇总.xlsx
Output:D:\_datefac_agent\output\agent_excel_intake_audit_348s_r2_regression_348a_baseline
```

Do not overwrite previous output directories.

---

## 5. Investigation focus

Before changing code, inspect the current R1 output rows that triggered the residual issues:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_h3_ap202605231822706325_1\review_queue.csv
```

Find rows with:

```text
period_context_missing
monetary_unit_mismatch
资产负债率
盈利预测分业务
```

Recommended quick check:

```powershell
python - <<'PY'
import csv
p = r'D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_h3_ap202605231822706325_1\review_queue.csv'
with open(p, newline='', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
for r in rows:
    issues = r.get('issue_codes','')
    label = r.get('metric_label','') or r.get('metric','') or ''
    sheet = r.get('sheet_name','')
    if 'period' in issues or 'unit' in issues or '资产负债率' in label or '盈利预测分业务' in sheet:
        print({'sheet': sheet, 'label': label, 'row_type': r.get('row_type'), 'issues': issues, 'unit': r.get('unit_hint'), 'periods': r.get('periods') or r.get('period_values')})
PY
```

Do not rely on guesses. Inspect actual rows.

---

## 6. Desired fix direction

### 6.1 Unit checker residual false positives

Problem:

```text
资产负债率(%)
资产负债率(%,LF)
```

These are ratio / percentage metrics, not monetary amount metrics, even though the label contains `资产` and `负债`.

Improve unit semantic checker so debt/asset ratio metrics are treated as percentage/ratio metrics, similar to earlier ROE-style fixes.

Likely file:

```text
datefac_agent/audit/unit_semantic_checker.py
```

Expected behavior:

```text
资产负债率(%) should not trigger monetary_unit_mismatch
资产负债率(%,LF) should not trigger monetary_unit_mismatch
资产总计(%) should still trigger monetary_unit_mismatch
负债合计(%) should still trigger monetary_unit_mismatch
```

Do not remove `资产` or `负债` from money terms globally.

### 6.2 Period checker residual false positives

Problem:

`盈利预测分业务` has embedded period headers such as:

```text
2025A收入(亿元)
2026E收入(亿元)
2027E收入(亿元)
2028E收入(亿元)
2026E毛利率(%)
```

These contain period information inside longer header strings.

Improve period detection/normalization so embedded period prefixes are recognized.

Likely files:

```text
datefac_agent/intake/excel_intake.py
datefac_agent/audit/period_alignment_checker.py
```

Expected behavior:

```text
2026E收入(亿元) should be recognized as period 2026E
2027E收入(亿元) should be recognized as period 2027E
2028E收入(亿元) should be recognized as period 2028E
2026E毛利率(%) should be recognized as period 2026E with metric/unit context, not missing period context
```

Do not disable period checking.

Do not mark all rows as valid if periods are truly absent.

---

## 7. Tests

Add focused tests.

Required test coverage:

### Unit tests

```text
资产负债率(%) does not trigger monetary_unit_mismatch
资产负债率(%,LF) does not trigger monetary_unit_mismatch
资产总计(%) still triggers monetary_unit_mismatch
负债合计(%) still triggers monetary_unit_mismatch
```

### Period tests

```text
2026E收入(亿元) is recognized as containing 2026E period
2027E收入(亿元) is recognized as containing 2027E period
2028E收入(亿元) is recognized as containing 2028E period
2026E毛利率(%) is recognized as containing 2026E period
A truly periodless financial row still triggers period issue
```

### Regression tests

Ensure existing 348A/R4 behavior remains stable:

```text
ROE / 净资产收益率 percentage behavior remains fixed
narrative rows remain excluded from clean_data
baseline regression keeps unit_issue_count = 0
```

---

## 8. Validation

Run:

```powershell
cd D:\_datefac_agent
python -m py_compile datefac_agent\audit\unit_semantic_checker.py datefac_agent\audit\period_alignment_checker.py datefac_agent\intake\excel_intake.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
```

Then run second sample:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf --excel-path D:\_datefac_agent\input\H3_AP202605231822706325_1_提取结果.xlsx --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348s_r2_h3_ap202605231822706325_1
```

Then run baseline regression sample:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202606081823352906_1_331fresh_20260615_21591.pdf --excel-path D:\_datefac_agent\input\安井食品研报数据汇总.xlsx --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348s_r2_regression_348a_baseline
```

---

## 9. Expected result report

Create:

```text
docs/agent/348S_R2_UNIT_PERIOD_RESIDUAL_REFINEMENT_RESULT.md
```

Include:

```text
Task ID
Problem statement
Residual rows inspected
Code changes
Test results
Second sample before/after comparison
Baseline regression comparison
Remaining risks
Decision
Recommended next task
```

Suggested decision values:

```text
348S_R2_CONFIRMED_RESIDUAL_FALSE_POSITIVES_REDUCED
348S_R2_CONFIRMED_PARTIAL_REFINEMENT_REMAINING_GAPS
348S_R2_CONFIRMED_NEEDS_DEEPER_PERIOD_HEADER_MODEL
348S_R2_BLOCKED_BY_AMBIGUOUS_ROW_CONTEXT
```

Choose one primary decision.

---

## 10. Non-goals

Do not run MinerU.

Do not call LLM/VLM APIs.

Do not run OCR.

Do not re-extract PDFs.

Do not touch legacy `datefac/`.

Do not touch old `D:\_datefac` workspace or historical outputs.

Do not claim `client_ready` or `production_ready`.

Do not commit output files.

Do not use:

```text
git add .
git add -A
git reset --hard
git checkout --
```

Use precise path staging only.

---

## 11. Expected changed files

Expected source changes may include:

```text
datefac_agent/audit/unit_semantic_checker.py
datefac_agent/audit/period_alignment_checker.py
datefac_agent/intake/excel_intake.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Expected report:

```text
docs/agent/348S_R2_UNIT_PERIOD_RESIDUAL_REFINEMENT_RESULT.md
```

Do not commit output files.

---

## 12. Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Which residual rows were inspected.
5. What unit checker changes were made.
6. What period detection changes were made.
7. py_compile result.
8. pytest result.
9. Second sample output directory.
10. Second sample key metrics after fix.
11. Whether unit_issue_count decreased.
12. Whether period_issue_count decreased.
13. Whether clean_data_row_count increased.
14. Baseline regression output directory.
15. Baseline regression key metrics.
16. Whether client/prod/formal gates remain false.
17. Whether output files were not committed.
18. Whether legacy `datefac/` and old outputs were untouched.
19. Whether LLM/MinerU/OCR calls were zero.
20. `git status -sb`.
21. Recommended next task.

---

## 13. Likely next task

If R2 is successful:

```text
348S-R2-QA Unit/Period Residual Refinement Review
```

If period residuals remain:

```text
348S-R3 Period Header Model Refinement
```
