# 348S-R1 Intake Schema Generalization

## 中文说明 / Chinese Summary

### 任务目标

348S 第二真实 workbook 已经端到端跑通，但结果暴露出明显泛化问题：

```text
row_count_total = 119
unknown_row_count = 53
period_issue_count = 66
clean_data_row_count = 0
review_queue_row_count = 119
```

这说明 runner 没崩，但当前 intake / row-type / period-header 假设太贴合第一份安井 workbook，换成第二份 workbook 后大量行变成 `UNKNOWN_ROW`，严格财务表行又大量触发 `period_context_missing`。

本任务目标是做一个保守的泛化修复：

```text
减少 UNKNOWN_ROW
减少错误的 period_context_missing
让第二真实样本重新产生合理的 internal clean-data candidates
同时不破坏第一份 348A/R4 baseline
```

### 关键约束

```text
不要为了让 clean_data 好看而强行放行
不要把 UNKNOWN_ROW 全部粗暴改成财务行
不要关闭 period checker
不要把 weak evidence 当成 strong evidence
不要跑 MinerU / OCR / LLM
不要重新抽 PDF
```

### 最小验收目标

第二真实样本：

```text
unknown_row_count 应明显下降
period_issue_count 应明显下降
clean_data_row_count 应从 0 上升
review_queue_row_count 应下降
client_ready / production_ready / formal_client_export_allowed 仍为 false
LLM / MinerU / OCR 调用仍为 0
```

第一份 348A/R4 baseline：

```text
不应明显回退
不应重新出现 unit false positive
不应让 narrative 进入 clean_data
不应打开 client/prod/formal gates
```

---

## 1. Goal

Generalize intake / row classification / period context detection based on the 348S second real workbook result.

The second workbook completed successfully but produced:

```text
UNKNOWN_ROW = 53
period_context_missing = 66
clean_data_row_count = 0
review_queue_row_count = 119
```

The goal is to reduce schema-specific brittleness while preserving conservative audit semantics.

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
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
docs/agent/348S_SECOND_REAL_WORKBOOK_PILOT_RESULT.md

docs/codex_tasks/348S_second_real_workbook_pilot.md
docs/codex_tasks/348A_R4_clean_data_candidate_policy.md
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
Output:D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_h3_ap202605231822706325_1
```

Also rerun the first baseline sample for regression comparison:

```text
PDF:   D:\_datefac_agent\input\H3_AP202606081823352906_1_331fresh_20260615_21591.pdf
Excel: D:\_datefac_agent\input\安井食品研报数据汇总.xlsx
Output:D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_regression_348a_baseline
```

Do not overwrite previous output directories.

---

## 5. Investigation focus

Inspect second workbook structure before changing code.

Recommended commands / checks:

```powershell
python - <<'PY'
from openpyxl import load_workbook
p = r'D:\_datefac_agent\input\H3_AP202605231822706325_1_提取结果.xlsx'
wb = load_workbook(p, data_only=True)
for ws in wb.worksheets:
    print('SHEET', ws.title, 'rows', ws.max_row, 'cols', ws.max_column)
    for r in range(1, min(ws.max_row, 8)+1):
        print(r, [ws.cell(r, c).value for c in range(1, min(ws.max_column, 8)+1)])
    print()
PY
```

Focus on:

```text
sheet names
header rows
period columns
metric-name columns
whether the workbook uses non-standard first columns
whether there is a 报告概要 / summary sheet that should be narrative or market reference instead of UNKNOWN_ROW
whether financial tables use year labels in a row or columns differently from 348A baseline
```

---

## 6. Likely source areas

Likely files:

```text
datefac_agent/intake/excel_intake.py
datefac_agent/audit/row_type_classifier.py
datefac_agent/audit/period_alignment_checker.py
datefac_agent/review/clean_candidate_policy.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Do not change unrelated modules unless necessary.

---

## 7. Desired fix direction

### 7.1 Row type generalization

Improve classification for workbook sheets / rows seen in the second sample.

Do not simply classify every unknown row as strict financial.

Possible generalized mappings:

```text
报告概要 / 核心摘要 / 投资要点 / 核心观点 -> NARRATIVE_ASSERTION or MARKET_REFERENCE_ROW depending on row shape
财务数据 / 财务摘要 / 财务预测 / 估值 / 资产负债表 / 利润表 / 现金流量表 -> STRICT_FINANCIAL_TABLE_ROW when row shape contains metric + period values
市场数据 / 基础数据 / 估值指标 -> MARKET_REFERENCE_ROW when row shape is reference-like rather than period table
```

### 7.2 Period detection generalization

Reduce false `period_context_missing` for valid financial rows.

Detect period labels more flexibly, including:

```text
2023A / 2024A / 2025E / 2026E / 2027E / 2028E
2023 / 2024 / 2025 / 2026
2026E
2026Q1 / 2026 Q1
FY2026 / 2026FY
```

If the workbook has period labels in a different header row, adjust intake to find the correct header row.

Do not disable period checking.

### 7.3 Clean candidate recovery

Once row types and period labels are correctly detected, R4 candidate policy should naturally produce clean candidates.

Do not patch clean candidate policy merely to inflate clean counts.

---

## 8. Tests

Add focused tests using small synthetic workbook-like rows, not massive real files.

Required test coverage:

1. New period labels from second workbook are detected.
2. A second-workbook financial sheet / row shape becomes `STRICT_FINANCIAL_TABLE_ROW` when appropriate.
3. A summary/narrative sheet does not become internal clean data.
4. A valid strict financial row with period labels and weak evidence can become `INTERNAL_CLEAN_CANDIDATE`.
5. Baseline 348A row-type / unit / clean-candidate behavior still passes.
6. Client/prod/formal gates remain false in manifest.

---

## 9. Validation

Run:

```powershell
cd D:\_datefac_agent
python -m py_compile datefac_agent\intake\excel_intake.py datefac_agent\audit\row_type_classifier.py datefac_agent\audit\period_alignment_checker.py datefac_agent\review\clean_candidate_policy.py tools\run_agent_excel_intake_audit_348a.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
```

Then run second sample:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf --excel-path D:\_datefac_agent\input\H3_AP202605231822706325_1_提取结果.xlsx --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_h3_ap202605231822706325_1
```

Then run first baseline regression sample:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202606081823352906_1_331fresh_20260615_21591.pdf --excel-path D:\_datefac_agent\input\安井食品研报数据汇总.xlsx --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_regression_348a_baseline
```

---

## 10. Expected result report

Create:

```text
docs/agent/348S_R1_INTAKE_SCHEMA_GENERALIZATION_RESULT.md
```

Include:

```text
Task ID
Problem statement
Second workbook shape findings
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
348S_R1_CONFIRMED_INTAKE_GENERALIZATION_IMPROVED
348S_R1_CONFIRMED_PARTIAL_IMPROVEMENT_REMAINING_GAPS
348S_R1_CONFIRMED_NEEDS_DEEPER_WORKBOOK_SCHEMA_SUPPORT
348S_R1_BLOCKED_BY_INPUT_SCHEMA
```

Choose one primary decision.

---

## 11. Non-goals

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

## 12. Expected changed files

Expected source changes may include:

```text
datefac_agent/intake/excel_intake.py
datefac_agent/audit/row_type_classifier.py
datefac_agent/audit/period_alignment_checker.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Expected report:

```text
docs/agent/348S_R1_INTAKE_SCHEMA_GENERALIZATION_RESULT.md
```

Do not commit output files.

---

## 13. Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Second workbook structure findings.
5. What intake / row-type / period changes were made.
6. py_compile result.
7. pytest result.
8. Second sample output directory.
9. Second sample key metrics after fix.
10. Whether unknown_row_count decreased.
11. Whether period_issue_count decreased.
12. Whether clean_data_row_count increased from 0.
13. Baseline regression output directory.
14. Baseline regression key metrics.
15. Whether client/prod/formal gates remain false.
16. Whether output files were not committed.
17. Whether legacy `datefac/` and old outputs were untouched.
18. Whether LLM/MinerU/OCR calls were zero.
19. `git status -sb`.
20. Recommended next task.

---

## 14. Likely next task

If R1 improves second sample without baseline regression:

```text
348S-R1-QA Intake Generalization Review
```

If improvement is partial:

```text
348S-R2 Workbook Schema Adapter
```
