# 348S Second Real Workbook Pilot

## 中文说明 / Chinese Summary

### 任务目标

348A 到 R4-QA 已经在第一份真实 workbook 上跑通：

```text
Excel intake -> audit -> review_queue -> clean_data candidate -> QA
```

现在进入第二真实样本验证，不再只证明“安井食品这一个样本能跑”。

用户已经把新的 PDF / Excel 放进：

```text
D:\_datefac_agent\input
```

截图中可见的候选文件包括：

```text
H3_AP202605231822706325_1.pdf
H3_AP202605231822706325_1_提取结果.xlsx
泰豪科技_深度研报_核心数据提取_豆包AI生成*.xlsx
```

用户还说明：有两个 AI 跑出了两个文档。因此本任务要先做 input inventory，再运行可明确配对的真实样本。

### 核心原则

```text
先验证泛化，不急着产品化。
能配对 PDF + Excel 的样本才跑 real runner。
无法明确配对的 Excel 不要硬跑，先记录为 unmatched / skipped。
不要覆盖 348A/R1/R2/R3/R4 旧输出。
```

### 最小目标

至少尝试运行这一组明确候选：

```text
PDF:   D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf
Excel: D:\_datefac_agent\input\H3_AP202605231822706325_1_提取结果.xlsx
Output:D:\_datefac_agent\output\agent_excel_intake_audit_348s_h3_ap202605231822706325_1
```

如果 `泰豪科技_深度研报_核心数据提取_豆包AI生成*.xlsx` 能在 input 目录中找到明确对应 PDF，也可以作为第二个 348S sample 运行；否则只做 inventory 记录，不要硬凑。

---

## 1. Goal

Run the current 348A/R4 audit workflow against a second real extracted workbook sample, and optionally a second candidate workbook if a matching source PDF can be clearly identified.

The goal is to test generalization beyond the first 安井食品 workbook.

The goal is not to build a new extractor, run MinerU, OCR the PDF, call LLM/VLM APIs, or broaden legacy migration.

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

docs/codex_tasks/348A_R4_clean_data_candidate_policy.md
docs/codex_tasks/348A_R4_QA_clean_data_candidate_policy_review.md
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

## 4. Input discovery

List candidate input files:

```powershell
Get-ChildItem D:\_datefac_agent\input | Select-Object Name,Length,LastWriteTime
```

Confirm the presence of:

```text
H3_AP202605231822706325_1.pdf
H3_AP202605231822706325_1_提取结果.xlsx
```

Also inspect whether there is a matching source PDF for:

```text
泰豪科技_深度研报_核心数据提取_豆包AI生成*.xlsx
```

If no unambiguous matching PDF exists for the 泰豪科技 workbook, do not run it. Record it as skipped due to missing/unmatched source PDF.

---

## 5. Primary sample to run

Run the current runner against the H3_AP202605231822706325 sample:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf --excel-path D:\_datefac_agent\input\H3_AP202605231822706325_1_提取结果.xlsx --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348s_h3_ap202605231822706325_1
```

Do not overwrite old output directories.

---

## 6. Optional second sample

Only if a matching PDF is clearly available, run the 泰豪科技 workbook as a second sample:

```text
Excel: 泰豪科技_深度研报_核心数据提取_豆包AI生成*.xlsx
PDF: matching 泰豪科技 source PDF, only if clearly present
Output: D:\_datefac_agent\output\agent_excel_intake_audit_348s_taihao_doubao
```

If there are multiple possible PDFs or no obvious PDF, skip and report why.

---

## 7. Possible outcomes

### If runner succeeds

Collect manifest / run summary metrics:

```text
decision
row_count_total
row_count_audited
pass_count
review_count
fail_count
issue_count_total
unit_issue_count
period_issue_count
valuation_issue_count
evidence_issue_count
clean_data_row_count
review_queue_row_count
internal_clean_candidate_count
internal_reference_candidate_count
narrative_review_count
review_required_count
excluded_from_clean_data_count
client_ready
production_ready
formal_client_export_allowed
llm_api_call_count
mineru_run_count
ocr_run_count
```

### If runner fails

Do not panic-patch large logic.

First classify failure type:

```text
INPUT_MISSING
WORKBOOK_SCHEMA_INCOMPATIBLE
INTAKE_ASSUMPTION_FAILED
RUNNER_BUG
POLICY_BUG
UNKNOWN_FAILURE
```

If the failure is workbook schema incompatibility, document exactly which workbook structure caused it. Only make small source changes if the fix is clearly generic and covered by tests.

---

## 8. Expected output report

Create:

```text
docs/agent/348S_SECOND_REAL_WORKBOOK_PILOT_RESULT.md
```

The report should include:

```text
Task ID
Input inventory
Samples attempted
Samples skipped and why
Runner result per sample
Manifest metrics per successful sample
Failure analysis per failed sample
Comparison against 348A/R4 baseline
Generalization assessment
Remaining risks
Recommended next task
```

Recommended decision values:

```text
348S_CONFIRMED_SECOND_REAL_WORKBOOK_RUNS
348S_CONFIRMED_WORKBOOK_SCHEMA_GAP
348S_BLOCKED_MISSING_INPUT_PAIR
348S_CONFIRMED_NEEDS_INTAKE_GENERALIZATION
348S_CONFIRMED_READY_FOR_FIXTURE_HARVEST
```

Choose one primary decision and optional supporting decisions.

---

## 9. Tests / validation

Always run:

```powershell
python -m pytest tests\agent -q
```

If source files are changed, also run py_compile for touched Python files.

If no source files are changed and this is only a run/report task, pytest is enough.

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

Expected:

```text
docs/agent/348S_SECOND_REAL_WORKBOOK_PILOT_RESULT.md
```

Optional, only if a small generic compatibility fix is required:

```text
datefac_agent/intake/*.py
datefac_agent/review/*.py
datefac_agent/delivery/*.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Do not commit output files.

---

## 12. Completion report

Report:

1. Which files were created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Input inventory summary.
5. Which PDF/Excel pairs were attempted.
6. Which candidate workbooks were skipped and why.
7. Output directory per attempted sample.
8. pytest result.
9. py_compile result if source changed.
10. Real runner success/failure per sample.
11. Manifest metrics per successful sample.
12. Failure classification if any sample failed.
13. Whether output files were not committed.
14. Whether legacy `datefac/` and old outputs were untouched.
15. Whether LLM/MinerU/OCR calls were zero.
16. `git status -sb`.
17. Recommended next task.

---

## 13. Likely next tasks

If 348S succeeds:

```text
348S-QA Second Real Workbook Pilot Review
348F Fixture Harvest from 346B
```

If 348S reveals workbook schema gaps:

```text
348S-R1 Intake Schema Generalization
```
