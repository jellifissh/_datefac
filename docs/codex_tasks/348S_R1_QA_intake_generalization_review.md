# 348S-R1-QA Intake Generalization Review

## 中文说明 / Chinese Summary

### 任务目标

本任务只做 QA 审查，不改源码。

348S-R1 把第二真实样本从：

```text
unknown_row_count = 53
period_issue_count = 66
clean_data_row_count = 0
review_queue_row_count = 119
```

改善到：

```text
unknown_row_count = 0
period_issue_count = 5
clean_data_row_count = 87
review_queue_row_count = 25
```

这看起来非常好，但 QA 必须确认它不是靠“漏读行”或“误分类”换来的。

重点检查：

```text
row_count_total 119 -> 112 是否合理
7 行减少是否来自合理过滤/summary 行处理，而不是误删有效数据
UNKNOWN_ROW = 0 是否真的分类正确
period_issue_count = 5 是否是真问题，不是误报
clean_data 87 行是否没有 unit/period/valuation 问题
baseline 348A/R4 是否没有回退
client/prod/formal gates 是否仍然关闭
```

### 不做什么

```text
不改源码
不改规则
不提交 output 文件
不跑 MinerU
不调用 LLM/VLM
不 OCR
不重新抽 PDF
不打开 client_ready / production_ready
```

---

## 1. Goal

Review the output and code impact of `348S-R1 Intake Schema Generalization`.

This is a QA/review task, not a code-fix task.

The goal is:

```text
Verify whether 348S-R1 genuinely improved second-workbook intake generalization without hiding rows, weakening audit policy, or regressing the 348A baseline.
```

The goal is not:

```text
Modify intake code, change row-type rules, change period checker, or inflate clean-data counts.
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
docs/agent/348S_SECOND_REAL_WORKBOOK_PILOT_RESULT.md
docs/agent/348S_R1_INTAKE_SCHEMA_GENERALIZATION_RESULT.md
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md

docs/codex_tasks/348S_R1_intake_schema_generalization.md
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

## 4. Output artifacts to review

Review second sample output:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_h3_ap202605231822706325_1
```

Review baseline regression output:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_regression_348a_baseline
```

Expected files in each output directory:

```text
agent_excel_intake_audit_348a_manifest.json
agent_excel_intake_audit_348a_run_summary.json
audit_report.md
evidence_index.json
review_queue.csv
clean_data.csv
```

Do not modify these output files.

---

## 5. Known metrics to verify

### Second sample after R1

```text
row_count_total = 112
row_count_audited = 112
fail_count = 2
unit_issue_count = 2
period_issue_count = 5
evidence_issue_count = 112
strict_financial_table_row_count = 81
market_reference_row_count = 13
narrative_assertion_count = 18
unknown_row_count = 0
clean_data_row_count = 87
review_queue_row_count = 25
internal_clean_candidate_count = 75
internal_reference_candidate_count = 12
narrative_review_count = 18
review_required_count = 5
excluded_from_clean_data_count = 2
client_ready = false
production_ready = false
formal_client_export_allowed = false
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
```

### Baseline regression after R1

```text
row_count_total = 82
unit_issue_count = 0
period_issue_count = 2
unknown_row_count = 0
clean_data_row_count = 75
review_queue_row_count = 7
internal_clean_candidate_count = 65
internal_reference_candidate_count = 10
narrative_review_count = 5
review_required_count = 2
excluded_from_clean_data_count = 0
```

Verify from manifest / run summary / clean_data / review_queue / evidence_index.

---

## 6. QA questions

### 6.1 Row-count change check

Investigate why row count changed:

```text
Before R1: row_count_total = 119
After R1:  row_count_total = 112
Delta: -7
```

Answer:

- Which rows/sheets account for the 7-row difference?
- Were they blank/title/header rows, duplicate header rows, malformed summary rows, or valid data rows?
- Is the decrease acceptable?
- If uncertain, mark it as a remaining risk.

### 6.2 Row-type quality

Review row type distribution and sample rows:

```text
STRICT_FINANCIAL_TABLE_ROW = 81
MARKET_REFERENCE_ROW = 13
NARRATIVE_ASSERTION = 18
UNKNOWN_ROW = 0
```

Answer:

- Is `UNKNOWN_ROW = 0` credible?
- Did `报告概要` split into narrative/reference rows correctly?
- Did `盈利预测与估值` / `重要财务与估值指标` / `盈利预测分业务` classify as strict rows only where appropriate?
- Did `可比公司估值` classify as market/reference rather than strict financial?

### 6.3 Period issue quality

Review remaining 5 period issues:

- Which rows have `period_context_missing` or related period issue codes?
- Are they truly missing period context?
- Did R1 over-suppress period issues anywhere?

### 6.4 Unit issue quality

Review remaining 2 unit issues:

- Which rows trigger `monetary_unit_mismatch` or other unit issue codes?
- Are they true positives?
- Are they related to market/reference rows, strict rows, or summary rows?

### 6.5 Clean-data candidate quality

Review `clean_data.csv`:

- Does it contain 87 rows?
- Do clean rows have only weak evidence issues, or are unit/period/valuation issues leaking in?
- Are narrative rows excluded from clean data?
- Are market reference candidates separate from strict internal clean candidates?

### 6.6 Review queue quality

Review `review_queue.csv`:

- Does it contain 25 rows?
- Does it include the 18 narrative rows, 5 period review rows, and 2 excluded/error rows?
- Are clean candidates absent from review queue unless intentionally duplicated?

### 6.7 Baseline regression

Compare baseline output after R1 to the previous R4-QA baseline:

- Did clean data remain 75?
- Did review queue remain 7?
- Did unit issue remain 0?
- Did unknown row remain 0?
- Did narrative handling remain conservative?

### 6.8 Gate discipline

Confirm these remain false:

```text
client_ready
production_ready
formal_client_export_allowed
```

Confirm external calls remain zero:

```text
llm_api_call_count
mineru_run_count
ocr_run_count
```

---

## 7. Output for this QA task

Create:

```text
docs/agent/348S_R1_QA_INTAKE_GENERALIZATION_REVIEW.md
```

The report should include:

```text
Task ID
Input/output directories reviewed
Verified metrics
Row-count delta analysis
Row-type quality analysis
Period issue quality analysis
Unit issue quality analysis
Clean-data quality analysis
Review queue quality analysis
Baseline regression analysis
Gate discipline analysis
Remaining risks
Decision
Recommended next task
```

Recommended decision values:

```text
348S_R1_QA_CONFIRMED_INTAKE_GENERALIZATION_IMPROVED
348S_R1_QA_CONFIRMED_PARTIAL_IMPROVEMENT_REMAINING_GAPS
348S_R1_QA_CONFIRMED_ROW_COUNT_DELTA_NEEDS_REVIEW
348S_R1_QA_CONFIRMED_NEEDS_UNIT_CHECKER_REFINEMENT
348S_R1_QA_CONFIRMED_NEEDS_PERIOD_RULE_REFINEMENT
348S_R1_QA_CONFIRMED_READY_FOR_FIXTURE_HARVEST
```

Choose one primary decision and optional supporting decisions.

---

## 8. Non-goals

Do not modify source code.

Do not edit:

```text
datefac_agent/**/*.py
tools/run_agent_excel_intake_audit_348a.py
```

Do not run MinerU.

Do not call LLM/VLM APIs.

Do not run OCR.

Do not re-extract the PDF.

Do not touch legacy `datefac/`.

Do not touch old `D:\_datefac` workspace or historical outputs.

Do not claim `client_ready` or `production_ready`.

Do not commit output files.

---

## 9. Validation

Run:

```powershell
cd D:\_datefac_agent
python -m pytest tests\agent -q
```

If no Python files were changed, py_compile is optional.

---

## 10. Expected changed files

Expected committed file:

```text
docs/agent/348S_R1_QA_INTAKE_GENERALIZATION_REVIEW.md
```

Do not commit output files.

---

## 11. Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Which output directories/files were reviewed.
5. Verified second sample metrics.
6. Verified baseline regression metrics.
7. Row-count delta analysis.
8. Row-type quality findings.
9. Period issue quality findings.
10. Unit issue quality findings.
11. Clean-data quality findings.
12. Review queue quality findings.
13. Gate discipline findings.
14. Remaining risks.
15. pytest result.
16. Whether source code was untouched.
17. Whether output files were not committed.
18. Whether LLM/MinerU/OCR calls were zero.
19. `git status -sb`.
20. Recommended next task.

---

## 12. Likely next tasks

If QA confirms R1:

```text
348F Fixture Harvest from 346B
348S-R2 Unit/Period Residual Refinement
348S Third Workbook Pilot
```

If QA finds row-count delta risk:

```text
348S-R2 Row Retention Audit
```
