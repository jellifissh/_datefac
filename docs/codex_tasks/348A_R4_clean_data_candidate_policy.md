# 348A-R4 Clean Data Candidate Policy

## 中文说明 / Chinese Summary

### 任务目标

R1 解决了“弱证据”和“真正缺证据”混在一起的问题。

R2 解决了“严格财务表格行 / 市场参考数据行 / 叙事性观点行”混在一起的问题。

R3 解决了 `净资产收益率(%)` 被误判成货币单位错误的问题。

现在 348A 的主要剩余问题是：

```text
82 行都是 WEAK_EVIDENCE
82 行都是 REVIEW
clean_data_row_count = 0
```

本任务要定义一个保守的内部候选规则：

```text
有些弱证据行不能正式交付客户，但可以进入 internal clean-data candidate，供内部 demo / 内部分析使用。
```

### 核心原则

```text
internal clean-data candidate ≠ client_ready
internal clean-data candidate ≠ production_ready
internal clean-data candidate ≠ formal client delivery
```

换句话说：

```text
可以作为内部候选干净数据使用，但不能声称已经可以正式交付客户。
```

### 建议最小规则

```text
STRICT_FINANCIAL_TABLE_ROW
+ WEAK_EVIDENCE
+ 无 unit issue
+ 无 period issue
+ 无 valuation issue
=> INTERNAL_CLEAN_CANDIDATE

MARKET_REFERENCE_ROW
+ WEAK_EVIDENCE
+ 无 unit issue
=> INTERNAL_REFERENCE_CANDIDATE

NARRATIVE_ASSERTION
+ WEAK_EVIDENCE
=> NARRATIVE_REVIEW，不进 clean_data

有 period_values_missing
=> REVIEW，不进 clean_data

MISSING_EVIDENCE
=> REVIEW / FAIL，不进 clean_data
```

### 最小验收标准

```text
clean_data_row_count 应该从 0 上升
review_queue_row_count 应该下降或至少 clean_data.csv 不再为空
client_ready 仍然必须是 false
production_ready 仍然必须是 false
formal_client_export_allowed 仍然必须是 false
LLM / MinerU / OCR 调用仍然必须是 0
```

---

## 1. Goal

Define a conservative clean-data candidate policy for the 348A Excel intake audit workflow.

R3 removed the current unit false positive. The remaining blocker is that all rows still remain in `REVIEW` because `WEAK_EVIDENCE` is review-worthy. R4 should separate internal clean candidates from formal delivery readiness.

The goal is:

```text
Allow selected weak-evidence rows with no semantic issues to enter internal clean-data candidate output while keeping client / production gates closed.
```

The goal is not:

```text
Make output client-ready, make output production-ready, weaken evidence policy globally, or treat weak evidence as formal proof.
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
docs/agent/348A_QA_EXCEL_INTAKE_AUDIT_RESULT_REVIEW.md
docs/agent/348A_R1_EVIDENCE_POLICY_REFINEMENT_RESULT.md
docs/agent/348A_R2_ROW_TYPE_CLASSIFICATION_RESULT.md
docs/agent/348A_R2_QA_ROW_TYPE_CLASSIFICATION_RESULT_REVIEW.md

docs/codex_tasks/348A_R3_unit_checker_false_positive_refinement.md
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

## 4. Scope

Likely source files:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/delivery/audit_report_writer.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Optional new helper file if it keeps logic clean:

```text
datefac_agent/review/clean_candidate_policy.py
```

Optional result doc:

```text
docs/agent/348A_R4_CLEAN_DATA_CANDIDATE_POLICY_RESULT.md
```

Do not modify unit/period/valuation checkers unless a test proves the clean candidate policy cannot be expressed without doing so.

---

## 5. Policy requirements

Add a clean candidate concept without pretending the row is formally deliverable.

Suggested candidate labels:

```text
INTERNAL_CLEAN_CANDIDATE
INTERNAL_REFERENCE_CANDIDATE
NARRATIVE_REVIEW
REVIEW_REQUIRED
EXCLUDED_FROM_CLEAN_DATA
```

Minimum acceptable behavior:

### Strict financial table rows

```text
STRICT_FINANCIAL_TABLE_ROW
+ WEAK_EVIDENCE
+ no unit issue
+ no period issue
+ no valuation issue
=> INTERNAL_CLEAN_CANDIDATE
```

Rows with `period_values_missing` must remain review-required and must not enter clean data.

### Market reference rows

```text
MARKET_REFERENCE_ROW
+ WEAK_EVIDENCE
+ no unit issue
=> INTERNAL_REFERENCE_CANDIDATE
```

Market reference candidates may be written to clean data, but should keep a candidate label showing they are reference-level, not formal financial statement rows.

### Narrative rows

```text
NARRATIVE_ASSERTION
+ WEAK_EVIDENCE
=> NARRATIVE_REVIEW
```

Narrative assertions should not enter `clean_data.csv` in R4.

### Missing evidence rows

```text
MISSING_EVIDENCE
=> do not enter clean data
```

### Error rows

```text
Any error-severity issue
=> do not enter clean data
```

---

## 6. Output requirements

### clean_data.csv

`clean_data.csv` should no longer be empty if the policy finds internal candidates.

Add fields such as:

```text
clean_candidate_type
row_type
evidence_level
issue_codes
```

Keep existing useful fields such as sheet name, row index, metric name, unit hint, period labels, and period values.

### review_queue.csv

Rows excluded from clean data should stay in review queue.

If a row is also an internal candidate, do not duplicate it into the review queue unless the policy explicitly wants candidate-review tracking. Prefer a clean separation for R4:

```text
clean candidate rows -> clean_data.csv
review-required rows -> review_queue.csv
```

### evidence_index.json

Preserve row type, evidence level, and optionally clean candidate type.

### audit_report.md

Add a clean candidate summary:

```text
internal_clean_candidate_count
internal_reference_candidate_count
narrative_review_count
review_required_count
excluded_from_clean_data_count
```

### manifest / run summary

Add or update fields:

```text
clean_data_row_count
review_queue_row_count
internal_clean_candidate_count
internal_reference_candidate_count
narrative_review_count
review_required_count
excluded_from_clean_data_count
client_ready = false
production_ready = false
formal_client_export_allowed = false
```

---

## 7. Decision semantics

Do not confuse row-level decision with candidate policy.

Acceptable options:

1. Keep row-level `decision = REVIEW` for weak-evidence rows but still mark some as internal clean candidates; or
2. Add a separate candidate field while decision remains conservative; or
3. Use a new internal-only status if the current schema supports it cleanly.

Prefer the least disruptive approach:

```text
keep PASS / REVIEW / FAIL conservative
add clean_candidate_type separately
```

Do not claim `PASS` means formal client delivery.

---

## 8. Non-goals

Do not run MinerU.

Do not call LLM/VLM APIs.

Do not run OCR.

Do not re-extract the PDF.

Do not touch legacy `datefac/`.

Do not touch old `D:\_datefac` workspace or historical outputs.

Do not claim `client_ready` or `production_ready`.

Do not change row-type classifier rules unless absolutely required.

Do not change unit checker behavior unless absolutely required.

Do not use:

```text
git add .
git add -A
git reset --hard
git checkout --
```

Use precise path staging only.

---

## 9. Tests

Add or update focused tests for:

1. Strict financial weak-evidence row with no semantic issues becomes `INTERNAL_CLEAN_CANDIDATE`.
2. Strict financial row with `period_values_missing` does not enter clean data.
3. Market reference weak-evidence row with no semantic issues becomes `INTERNAL_REFERENCE_CANDIDATE`.
4. Narrative assertion weak-evidence row stays `NARRATIVE_REVIEW` and does not enter clean data.
5. Missing evidence row does not enter clean data.
6. Error-severity issue row does not enter clean data.
7. Manifest/run summary counts candidate rows separately from review rows.
8. `client_ready`, `production_ready`, and `formal_client_export_allowed` remain false.

Do not require real Excel/PDF files in unit tests.

---

## 10. Validation

Run:

```powershell
cd D:\_datefac_agent

python -m py_compile datefac_agent\schemas\audit_models.py datefac_agent\review\review_queue_builder.py datefac_agent\delivery\evidence_index_writer.py datefac_agent\delivery\audit_report_writer.py tools\run_agent_excel_intake_audit_348a.py tests\agent\test_agent_excel_intake_audit_348a.py

python -m pytest tests\agent -q
```

Then rerun the real pilot to a new R4 output directory:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202606081823352906_1_331fresh_20260615_21591.pdf --excel-path D:\_datefac_agent\input\安井食品研报数据汇总.xlsx --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348a_r4
```

Do not overwrite old 348A, R1, R2, or R3 output directories.

---

## 11. Expected R4 outcome

Expected qualitative outcome:

```text
clean_data_row_count should become greater than 0.
review_queue_row_count should become smaller than 82 if candidate rows are removed from the queue.
internal candidate counts should be visible in manifest/report.
client_ready should remain false.
production_ready should remain false.
formal_client_export_allowed should remain false.
```

Do not force exact row counts in the task document. Let the implementation compute them from the current workbook.

---

## 12. Expected changed files

Expected:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/delivery/audit_report_writer.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Optional:

```text
datefac_agent/review/clean_candidate_policy.py
docs/agent/348A_R4_CLEAN_DATA_CANDIDATE_POLICY_RESULT.md
```

Do not commit output files.

---

## 13. Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. What clean candidate policy was implemented.
5. py_compile result.
6. pytest result.
7. Real runner result and R4 output directory.
8. Manifest decision and key R4 metrics.
9. `clean_data_row_count` and `review_queue_row_count`.
10. Internal clean/reference/narrative/review/excluded candidate counts.
11. Whether client/prod/formal delivery gates remain false.
12. Whether output files were not committed.
13. Whether row-type/evidence/unit policies were left intact.
14. Whether legacy `datefac/` and old outputs were untouched.
15. Whether LLM/MinerU/OCR calls were zero.
16. `git status -sb`.
17. Recommended next task.

---

## 14. Likely next task

If R4 succeeds, likely next task:

```text
348A-R4-QA Clean Data Candidate Policy Review
```

After that, consider fixture harvest from 346B or a second real workbook sample.
