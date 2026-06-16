# 348A-QA Excel Intake Audit Result Review

## 1. Goal

Review the first real-run output of `348A AI-Extracted Excel Intake Audit Pilot`.

This is a QA/review task, not a code-fix task.

The goal is:

```text
Understand why the first 348A run produced mostly REVIEW rows and decide what should be refined next.
```

The goal is not:

```text
Rewrite checkers, rerun MinerU, call LLMs, re-extract the PDF, or implement a production agent.
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
datefac_agent/FOUNDATION_TASK.md

docs/agent/AGENT_ARCHITECTURE.md
docs/agent/FIXTURE_STRATEGY.md
docs/agent/348A_EXCEL_INTAKE_AUDIT_PLAN.md
docs/agent/348A_INPUT_OUTPUT_CONTRACT.md
docs/legacy/LEGACY_ASSET_MAP.md
docs/project_strategy/348_agent_pivot_brief.md

docs/codex_tasks/348A_ai_extracted_excel_intake_audit_pilot.md
```

These define the Agent pivot, 348A contract, conservative audit posture, and no-MinerU/no-LLM boundaries.

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

Review the 348A output directory:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348a
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

If these files are missing, do not fake the QA. Report missing artifacts clearly.

Do not modify these source output files during QA.

---

## 5. Known first-run metrics to verify

The user reported the first real-run metrics:

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
clean_data_row_count = 0
review_queue_row_count = 82
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
recommended_next_step = 348A-QA Excel Intake Audit Result Review
```

The QA task should verify these from manifest / run summary, not merely repeat them.

---

## 6. Review questions

Answer these questions from the generated outputs:

### 6.1 Evidence classification

- Why did `evidence_issue_count = 82`?
- Are these truly `MISSING_EVIDENCE`, or should many be downgraded to `WEAK_EVIDENCE` because sheet/row lineage exists?
- Does the workbook contain explicit page/source columns?
- Should source PDF path + workbook sheet + row index count as weak traceability for the pilot?

### 6.2 Sheet and row classification

- What are the workbook sheet names?
- Which sheets look like strict financial tables?
- Which sheets look like narrative / investment-point / risk-description sheets?
- Should narrative rows be audited with the same unit/period/evidence policy as strict financial metric rows?

### 6.3 Review queue quality

- Are review reasons specific and useful?
- Are all rows pushed into one generic reason bucket?
- Can a human reviewer understand why each row needs review?
- Which issue codes dominate?

### 6.4 Clean data policy

- Is `clean_data_row_count = 0` expected under current conservative evidence policy?
- Which row types could safely become `PASS` after evidence policy refinement?
- Should first-pass clean data require strong page evidence, or allow weak lineage for non-client pilot output?

### 6.5 Checker behavior

- Is `unit_issue_count = 1` plausible?
- Is `period_issue_count = 2` plausible?
- Is `valuation_issue_count = 0` plausible for this workbook?
- Are there obvious false negatives in unit/period/valuation checks?

---

## 7. Output for this QA task

Create a QA review report under:

```text
docs/agent/348A_QA_EXCEL_INTAKE_AUDIT_RESULT_REVIEW.md
```

The report should include:

```text
Task ID
Input output directory reviewed
Manifest decision
Key metrics
Evidence issue analysis
Sheet/row classification analysis
Review queue quality analysis
Clean data policy analysis
Checker behavior analysis
Risks
Recommended refinements
Decision
```

Recommended decision values:

```text
348A_QA_CONFIRMED_NEEDS_EVIDENCE_POLICY_REFINEMENT
348A_QA_CONFIRMED_NEEDS_ROW_CLASSIFICATION_REFINEMENT
348A_QA_CONFIRMED_NEEDS_CHECKER_REFINEMENT
348A_QA_BLOCKED_MISSING_OUTPUT_ARTIFACTS
```

Multiple refinements may be recommended, but choose one primary decision.

Optional local-only QA output may be written under:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348a_qa
```

Do not stage or commit bulk output artifacts.

---

## 8. Non-goals

Do not modify 348A source code in this task.

Do not edit:

```text
datefac_agent/intake/excel_intake.py
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

Because this task is documentation/QA review only, run the existing agent tests to ensure nothing was broken:

```powershell
cd D:\_datefac_agent
python -m pytest tests\agent -q
```

If no Python files were changed, py_compile is optional.

---

## 10. Expected changed files

Expected committed file:

```text
docs/agent/348A_QA_EXCEL_INTAKE_AUDIT_RESULT_REVIEW.md
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
4. Which 348A output files were reviewed.
5. Manifest decision and verified key metrics.
6. Main evidence classification finding.
7. Main sheet/row classification finding.
8. Main review queue quality finding.
9. Whether source code was untouched.
10. Whether legacy `datefac/` and old outputs were untouched.
11. Whether LLM/MinerU/OCR calls were zero.
12. pytest result.
13. `git status -sb`.
14. Recommended next task.

---

## 12. Likely next tasks

Depending on findings, likely next tasks are:

```text
348A-R1 Evidence Policy Refinement
348A-R2 Row Type Classification Refinement
348F Fixture Harvest from 346B
348M Legacy Capability Inventory
```

Do not choose a code refinement task until this QA report explains the failure mode clearly.
