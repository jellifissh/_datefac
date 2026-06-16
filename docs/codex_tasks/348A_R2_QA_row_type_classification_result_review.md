# 348A-R2-QA Row Type Classification Result Review

## 1. Goal

Review the output of `348A-R2 Row Type Classification Refinement`.

This is a QA/review task, not a code-fix task.

The goal is:

```text
Verify whether R2 row-type classification made the 348A review queue and delivery artifacts more diagnostically useful.
```

The goal is not:

```text
Change row-type rules, fix unit checker false positives, define clean-data candidate policy, rerun MinerU, call LLMs, or re-extract the PDF.
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
datefac_agent/PROJECT_BACKGROUND.md
datefac_agent/CODE_MIGRATION_PLAN.md

docs/agent/AGENT_ARCHITECTURE.md
docs/agent/FIXTURE_STRATEGY.md
docs/agent/348A_EXCEL_INTAKE_AUDIT_PLAN.md
docs/agent/348A_INPUT_OUTPUT_CONTRACT.md
docs/agent/348A_QA_EXCEL_INTAKE_AUDIT_RESULT_REVIEW.md
docs/agent/348A_R1_EVIDENCE_POLICY_REFINEMENT_RESULT.md
docs/agent/348A_R2_ROW_TYPE_CLASSIFICATION_RESULT.md
docs/legacy/LEGACY_ASSET_MAP.md

docs/codex_tasks/348A_ai_extracted_excel_intake_audit_pilot.md
docs/codex_tasks/348A_QA_excel_intake_audit_result_review.md
docs/codex_tasks/348A_R1_evidence_policy_refinement.md
docs/codex_tasks/348A_R2_row_type_classification_refinement.md
```

The QA report, R1 result, and R2 result note are the direct basis for this task.

---

## 3. Working directory

Use the clean worktree:

```text
D:\_datefac_agent
```

Expected branch:

```text
pivot/348-agent-foundation
```

Before starting:

```powershell
cd D:\_datefac_agent
git pull --ff-only origin pivot/348-agent-foundation
git status -sb
git branch --show-current
```

The worktree must be clean before starting. If there are uncommitted changes, stop and report.

---

## 4. Input artifacts to review

Review the R2 output directory:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348a_r2
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

If these files are missing, do not fake QA. Report missing artifacts clearly.

Do not modify these output files during QA.

---

## 5. Known R2 metrics to verify

The user reported these R2 metrics:

```text
decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
sheet_count = 6
row_count_total = 82
row_count_audited = 82
pass_count = 0
review_count = 81
fail_count = 1
issue_count_total = 85
unit_issue_count = 1
period_issue_count = 2
valuation_issue_count = 0
evidence_issue_count = 82
strong_evidence_count = 0
weak_evidence_count = 82
missing_evidence_count = 0
not_applicable_evidence_count = 0
strict_financial_table_row_count = 67
market_reference_row_count = 10
narrative_assertion_count = 5
unknown_row_count = 0
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
```

The QA task should verify these from manifest / run summary / review queue / evidence index, not merely repeat them.

---

## 6. Review questions

Answer these questions from the generated outputs.

### 6.1 Row-type distribution

- Do row-type counts add up to `row_count_total = 82`?
- Does `strict_financial_table_row_count = 67` appear plausible?
- Does `market_reference_row_count = 10` appear plausible?
- Does `narrative_assertion_count = 5` appear plausible?
- Does `unknown_row_count = 0` appear safe, or is it suspiciously overconfident?

### 6.2 Sheet-to-row-type mapping

Verify the current workbook mapping:

```text
财务估值 -> STRICT_FINANCIAL_TABLE_ROW
资产负债表 -> STRICT_FINANCIAL_TABLE_ROW
利润表 -> STRICT_FINANCIAL_TABLE_ROW
现金流量表 -> STRICT_FINANCIAL_TABLE_ROW
市场与基础数据 -> MARKET_REFERENCE_ROW
核心观点 -> NARRATIVE_ASSERTION
```

Check whether any row appears misclassified.

### 6.3 Review queue quality

- Does `review_queue.csv` include `row_type`?
- Does row type make review triage more useful than R1?
- Can a reviewer now separate narrative weak-evidence rows from strict financial-table weak-evidence rows?
- Are `period_values_missing` issues limited to strict financial table rows?
- Is the one `FAIL` still the `净资产收益率(%)` unit false-positive-style case?

### 6.4 Evidence index quality

- Does `evidence_index.json` include `row_type`?
- Does row type plus evidence level make traceability clearer?
- Are R1 evidence-level distinctions still preserved?

### 6.5 Audit report quality

- Does `audit_report.md` include row-type distribution?
- Does it describe the R2 boundary clearly?
- Does it avoid implying client or production readiness?

### 6.6 Remaining blocker analysis

Decide the next real blocker after R2:

- unit false positive on `净资产收益率(%)`;
- clean-data candidate policy;
- row-type classifier accuracy;
- evidence policy still too strict for non-client pilot output;
- fixture coverage gap.

---

## 7. Output for this QA task

Create a QA review report under:

```text
docs/agent/348A_R2_QA_ROW_TYPE_CLASSIFICATION_RESULT_REVIEW.md
```

The report should include:

```text
Task ID
Input output directory reviewed
Manifest decision
Verified key metrics
Row-type distribution analysis
Sheet-to-row-type mapping analysis
Review queue quality analysis
Evidence index quality analysis
Audit report quality analysis
Remaining risks
Recommended refinements
Decision
```

Recommended decision values:

```text
348A_R2_QA_CONFIRMED_ROW_TYPE_CLASSIFICATION_USEFUL
348A_R2_QA_CONFIRMED_NEEDS_ROW_TYPE_RULE_REFINEMENT
348A_R2_QA_CONFIRMED_NEXT_UNIT_CHECKER_REFINEMENT
348A_R2_QA_CONFIRMED_NEXT_CLEAN_DATA_POLICY
348A_R2_QA_BLOCKED_MISSING_OUTPUT_ARTIFACTS
```

Choose one primary decision. Supporting decisions are allowed.

Optional local-only QA scratch output may be written under:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348a_r2_qa
```

Do not stage or commit bulk output artifacts.

---

## 8. Non-goals

Do not modify source code in this task.

Do not edit:

```text
datefac_agent/intake/*.py
datefac_agent/audit/*.py
datefac_agent/review/*.py
datefac_agent/delivery/*.py
tools/run_agent_excel_intake_audit_348a.py
```

Do not run MinerU.

Do not call LLM/VLM APIs.

Do not run OCR.

Do not re-extract the PDF.

Do not continue 346B6.

Do not mutate legacy `datefac/`.

Do not touch old `D:\_datefac` workspace or historical outputs.

Do not claim `client_ready` or `production_ready`.

---

## 9. Validation

Because this task is documentation/QA review only, run the existing tests to ensure nothing was broken:

```powershell
cd D:\_datefac_agent
python -m pytest tests\agent -q
```

If no Python files were changed, py_compile is optional.

---

## 10. Expected changed files

Expected committed file:

```text
docs/agent/348A_R2_QA_ROW_TYPE_CLASSIFICATION_RESULT_REVIEW.md
```

Optional ledger update if appropriate:

```text
docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md
```

Do not commit output files.

---

## 11. Completion report

Report:

1. Files created or modified.
2. Whether branch is `pivot/348-agent-foundation`.
3. Whether worktree was clean before editing.
4. Which R2 output files were reviewed.
5. Manifest decision and verified key metrics.
6. Row-type distribution findings.
7. Sheet-to-row-type mapping findings.
8. Review queue quality findings.
9. Evidence index quality findings.
10. Audit report quality findings.
11. Whether source code was untouched.
12. Whether legacy `datefac/` and old outputs were untouched.
13. Whether LLM/MinerU/OCR calls were zero.
14. pytest result.
15. `git status -sb`.
16. Recommended next task.

---

## 12. Likely next tasks

Depending on findings, likely next tasks are:

```text
348A-R3 Unit Checker False Positive Refinement
348A-R4 Clean Data Candidate Policy
348F Fixture Harvest from 346B
348M Legacy Capability Inventory
```

Do not start broad legacy migration until the single-sample 348A workflow is explainable and stable enough to become a regression target.
