# 348N New Real Workbook Generalization Pilot

## Goal

Run the current DateFac Agent intake/audit/review pipeline on a new real PDF+Excel workbook pair.

This is a generalization pilot, not a policy redesign task.

The goal is to test whether the current rules generalize beyond the three already reviewed real workbooks.

---

## Current validated baseline

Recently confirmed:

```text
348S_R3C_QA_CONFIRMED_UNKNOWN_ROW_REFINEMENT_VALID
348S_R4_QA_CONFIRMED_STRICT_ROW_UNIT_PERIOD_REFINEMENT_VALID
348A_R4_QA_CONFIRMED_CLEAN_DATA_CANDIDATE_POLICY_VALID
```

Known baseline behavior:

```text
clean_data boundary is conservative
review_queue preserves unresolved rows
unknown_row_count can be reduced by explicit row typing when justified
strict-row unit/period review signals should not be globally loosened
readiness gates remain closed
LLM / MinerU / OCR counters remain zero
```

---

## Required context

Read:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
docs/agent/348S_R4_QA_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_REVIEW.md
```

---

## Preflight

```powershell
cd D:\_datefac_agent
git pull --ff-only origin pivot/348-agent-foundation
git status -sb
git branch --show-current
```

Stop if the worktree is not clean.

---

## Input-pair discovery

Inspect `D:\_datefac_agent\input` and list available PDFs and Excel files.

Identify candidate new pairs.

Do not reuse these already-tested pairs unless no new pair exists:

```text
H3_AP202606081823352906_1_331fresh_20260615_21591.pdf + 安井食品研报数据汇总.xlsx
H3_AP202605231822706325_1.pdf + H3_AP202605231822706325_1_提取结果.xlsx
H3_AP202605231822706325_1.pdf + 泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
```

Pairing rules:

```text
prefer filename company match
prefer PDF first-page company/title match if already accessible from existing text/metadata
if no safe pair can be established, stop and report BLOCKED_MISSING_NEW_PAIR
```

Do not run OCR or PDF extraction to establish the pair.

---

## Execution

If a new pair is found, run the existing 348A runner to a new output directory:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path <PDF_PATH> --excel-path <EXCEL_PATH> --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348n_<safe_slug>
```

Do not modify source code during the first pilot run.

Do not commit output files.

---

## Review focus

After the runner completes, inspect manifest, run summary, clean_data, review_queue, evidence index, and audit report.

Report:

```text
row_count_total
clean_data_row_count
review_queue_row_count
unknown_row_count
unit_issue_count
period_issue_count
valuation_issue_count
evidence_issue_count
readiness flags
external call counters
```

Also answer:

```text
Did intake complete without crash?
Did clean_data remain conservative?
Did review_queue remain explainable?
Did unknown_row_count spike compared with previous samples?
Did unit/period/valuation signals look like true review signals or possible false positives?
Did any current policy obviously overfit the first three workbooks?
```

---

## Scope

Allowed to create:

```text
docs/agent/348N_NEW_REAL_WORKBOOK_GENERALIZATION_PILOT_RESULT.md
```

Do not modify source code.

Do not modify tests.

Do not modify input or output files.

Do not run MinerU, OCR, LLM, or VLM.

Do not re-extract PDFs.

---

## Required validation

Run baseline tests:

```powershell
python -m pytest tests\agent -q
```

No py_compile is required if no Python files are changed.

---

## Expected report

Create:

```text
docs/agent/348N_NEW_REAL_WORKBOOK_GENERALIZATION_PILOT_RESULT.md
```

Include:

```text
Task ID
Input-pair discovery
Selected PDF and Excel pair
Runner command
Output directory
Manifest metrics
Clean-data QA
Review-queue QA
Unknown-row QA
Unit/period/valuation signal QA
Readiness gate QA
External call QA
Baseline validation
Decision
Recommended next task
```

Decision values:

```text
348N_CONFIRMED_NEW_REAL_WORKBOOK_GENERALIZATION_PASS_WITH_REVIEW_QUEUE
348N_CONFIRMED_NEW_REAL_WORKBOOK_NEEDS_TARGETED_REFINEMENT
348N_BLOCKED_MISSING_NEW_PAIR
348N_BLOCKED_RUNNER_FAILURE
```

---

## Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Input-pair discovery result.
5. Selected pair or blocked reason.
6. Runner command and output directory.
7. Manifest metrics.
8. Clean-data QA conclusion.
9. Review-queue QA conclusion.
10. Unknown-row QA conclusion.
11. Unit/period/valuation signal QA conclusion.
12. Readiness gate QA conclusion.
13. External call QA conclusion.
14. pytest result.
15. Whether source code was untouched.
16. Whether output files were not committed.
17. Whether LLM/MinerU/OCR calls were zero.
18. git status -sb.
19. Recommended next task.
