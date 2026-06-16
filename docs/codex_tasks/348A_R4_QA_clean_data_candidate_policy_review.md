# 348A-R4-QA Clean Data Candidate Policy Review

## 中文说明 / Chinese Summary

### 任务目标

本任务只做 QA 审查，不改代码。

R4 已经把原来 82 行全 REVIEW 的结果，分成了：

```text
clean_data_row_count = 75
review_queue_row_count = 7
internal_clean_candidate_count = 65
internal_reference_candidate_count = 10
narrative_review_count = 5
review_required_count = 2
excluded_from_clean_data_count = 0
```

本轮 QA 要检查这套分流是否合理：

```text
75 行 clean_data 是否真的都没有 unit / period / valuation 问题
7 行 review_queue 是否确实是 5 个 narrative + 2 个 period_values_missing
narrative 是否没有混进 clean_data
period_values_missing 是否没有混进 clean_data
client_ready / production_ready / formal_client_export_allowed 是否仍然是 false
```

### 不做什么

```text
不改源码
不调规则
不跑 MinerU
不调用 LLM/VLM
不 OCR
不重新抽 PDF
不提交 output 文件
不打开 client_ready / production_ready
```

### QA 结论方向

如果 R4 分流合理，主结论应类似：

```text
348A_R4_QA_CONFIRMED_INTERNAL_CLEAN_CANDIDATE_POLICY_USEFUL
```

如果发现 clean_data 混入 narrative 或 period issue，则应标记为需要修复。

---

## 1. Goal

Review the output of `348A-R4 Clean Data Candidate Policy`.

This is a QA/review task, not a code-fix task.

The goal is:

```text
Verify whether R4 correctly separates internal clean/reference candidates from rows that still require review.
```

The goal is not:

```text
Change candidate policy, edit source code, declare client readiness, or run any extraction/OCR/LLM tool.
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
docs/agent/348A_R1_EVIDENCE_POLICY_REFINEMENT_RESULT.md
docs/agent/348A_R2_ROW_TYPE_CLASSIFICATION_RESULT.md
docs/agent/348A_R2_QA_ROW_TYPE_CLASSIFICATION_RESULT_REVIEW.md

docs/codex_tasks/348A_R3_unit_checker_false_positive_refinement.md
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

## 4. Input artifacts to review

Review the R4 output directory:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348a_r4
```

Expected files:

```text
agent_excel_intake_audit_348a_manifest.json
agent_excel_intake_audit_348a_run_summary.json
audit_report.md
evidence_index.json
review_queue.csv
clean_data.csv
```

Do not modify these output files during QA.

---

## 5. Known R4 metrics to verify

The user reported:

```text
decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
row_count_total = 82
row_count_audited = 82
pass_count = 0
review_count = 82
fail_count = 0
issue_count_total = 84
unit_issue_count = 0
period_issue_count = 2
valuation_issue_count = 0
evidence_issue_count = 82
clean_data_row_count = 75
review_queue_row_count = 7
internal_clean_candidate_count = 65
internal_reference_candidate_count = 10
narrative_review_count = 5
review_required_count = 2
excluded_from_clean_data_count = 0
client_ready = false
production_ready = false
formal_client_export_allowed = false
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
```

Verify these from manifest / run summary / clean_data / review_queue / evidence_index.

---

## 6. Review questions

### 6.1 Clean-data candidate quality

- Does `clean_data.csv` contain 75 rows?
- Do all clean rows have `clean_candidate_type`?
- Are strict financial table candidates marked as `INTERNAL_CLEAN_CANDIDATE`?
- Are market reference rows marked as `INTERNAL_REFERENCE_CANDIDATE`?
- Are there any `NARRATIVE_ASSERTION` rows in clean data? There should not be.
- Are there any rows with `period_values_missing` in clean data? There should not be.
- Are there any unit / period / valuation issue rows in clean data? There should not be.

### 6.2 Review queue quality

- Does `review_queue.csv` contain 7 rows?
- Are the 7 rows expected to be:

```text
5 NARRATIVE_ASSERTION rows
2 STRICT_FINANCIAL_TABLE_ROW rows with period_values_missing
```

- Does review queue preserve row type, evidence level, and issue codes?
- Are there any internal clean candidates still duplicated into review queue? Prefer no duplication for R4.

### 6.3 Evidence index quality

- Does `evidence_index.json` include `row_type`, `evidence_level`, and `clean_candidate_type`?
- Does evidence index preserve R1 evidence-level distinction and R2 row-type distinction?

### 6.4 Audit report quality

- Does `audit_report.md` include clean candidate summary counts?
- Does it clearly state internal candidate status is not client / production readiness?

### 6.5 Gate discipline

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
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
```

The report should include:

```text
Task ID
Input output directory reviewed
Manifest decision
Verified key metrics
Clean-data candidate quality analysis
Review queue quality analysis
Evidence index quality analysis
Audit report quality analysis
Gate discipline analysis
Remaining risks
Recommended refinements
Decision
```

Recommended decision values:

```text
348A_R4_QA_CONFIRMED_INTERNAL_CLEAN_CANDIDATE_POLICY_USEFUL
348A_R4_QA_CONFIRMED_NEEDS_CLEAN_POLICY_REFINEMENT
348A_R4_QA_BLOCKED_MISSING_OUTPUT_ARTIFACTS
348A_R4_QA_CONFIRMED_READY_FOR_SECOND_REAL_WORKBOOK
348A_R4_QA_CONFIRMED_READY_FOR_FIXTURE_HARVEST
```

Choose one primary decision. Supporting decisions are allowed.

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
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
```

Do not commit output files.

---

## 11. Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Which R4 output files were reviewed.
5. Verified manifest metrics.
6. Clean-data candidate quality findings.
7. Review queue quality findings.
8. Evidence index quality findings.
9. Audit report quality findings.
10. Whether client/prod/formal delivery gates remain false.
11. Whether external calls remain zero.
12. Whether source code was untouched.
13. Whether output files were not committed.
14. pytest result.
15. `git status -sb`.
16. Recommended next task.

---

## 12. Likely next tasks

If R4-QA confirms the policy, likely next tasks are:

```text
348S Second Real Workbook Pilot
348F Fixture Harvest from 346B
348M Legacy Capability Inventory
```

Do not start broad legacy migration until the current single-sample workflow is QA-confirmed.
