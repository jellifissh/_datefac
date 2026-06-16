# 348A-R1 Evidence Policy Refinement

## 1. Goal

Refine the evidence policy in the first `348A AI-Extracted Excel Intake Audit Pilot` implementation.

The 348A-QA report found that the first real run classified all 82 rows as `missing_evidence`, even though every row had weak lineage through:

```text
source_pdf
workbook_row
sheet_name
row_index
metric label
```

This task should split evidence severity into meaningful levels and stop collapsing weak workbook lineage into total missing evidence.

The goal is:

```text
Distinguish STRONG_EVIDENCE, WEAK_EVIDENCE, MISSING_EVIDENCE, and NOT_APPLICABLE in the 348A workflow.
```

The goal is not:

```text
Re-extract the PDF, run MinerU, call LLMs, implement row-type classification, or fix every checker issue.
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
docs/legacy/LEGACY_ASSET_MAP.md

docs/codex_tasks/348A_ai_extracted_excel_intake_audit_pilot.md
docs/codex_tasks/348A_QA_excel_intake_audit_result_review.md
```

The QA report is the direct basis for this refinement.

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

Before editing:

```powershell
cd D:\_datefac_agent
git pull --ff-only origin pivot/348-agent-foundation
git status -sb
git branch --show-current
```

The worktree must be clean before starting. If there are uncommitted changes, stop and report.

---

## 4. Source files in scope

Allowed source files:

```text
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/delivery/audit_report_writer.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Only modify files needed for evidence policy refinement.

Do not modify intake logic unless a test proves evidence metadata is unavailable due to intake structure. If intake must be changed, explain why.

---

## 5. Non-goals and hard boundaries

Do not implement full row-type classification in this task.

Do not fix the `净资产收益率(%)` unit false-positive in this task unless it is unavoidable for tests. That belongs to a later checker refinement task.

Do not run MinerU.

Do not call LLM/VLM APIs.

Do not run OCR.

Do not re-extract the PDF.

Do not continue 346B6.

Do not mutate legacy `datefac/`.

Do not touch old `D:\_datefac` workspace or historical outputs.

Do not claim `client_ready` or `production_ready`.

Do not use:

```text
git add .
git add -A
git reset --hard
git checkout --
```

Use precise path staging only.

---

## 6. Evidence policy requirements

Introduce or support these evidence levels:

```text
STRONG_EVIDENCE
WEAK_EVIDENCE
MISSING_EVIDENCE
NOT_APPLICABLE
```

Recommended semantics:

### STRONG_EVIDENCE

Use when a row has explicit traceability such as:

- page number;
- source/evidence column;
- explicit evidence reference;
- section/page locator that can be reviewed.

### WEAK_EVIDENCE

Use when a row lacks explicit page evidence but still has workbook lineage:

- source PDF path exists;
- workbook path or source workbook exists;
- sheet name exists;
- row index exists;
- metric label or row identity exists.

For the current 348A workbook, most rows should move from `missing_evidence` to `weak_evidence` or equivalent review-worthy weak lineage.

### MISSING_EVIDENCE

Use only when the row lacks usable lineage beyond raw value presence.

Examples:

- no source PDF path;
- no workbook row reference;
- no sheet/row identity;
- no metric label;
- evidence references are empty or malformed.

### NOT_APPLICABLE

Reserve for future row-type classification or content types where strict table evidence policy does not apply.

Do not overuse this in R1 because row-type classification is not the main target.

---

## 7. Review decision expectations

Do not automatically turn weak-evidence rows into clean `PASS` if the policy still requires human review.

Acceptable behavior for R1:

```text
WEAK_EVIDENCE -> REVIEW, but no longer counted as true MISSING_EVIDENCE
MISSING_EVIDENCE -> REVIEW or FAIL depending on severity
STRONG_EVIDENCE with no other issues -> PASS candidate
NOT_APPLICABLE -> review policy depends on future row classification
```

The main improvement should be better triage, not fake confidence.

The review queue should distinguish at least:

```text
weak_evidence
missing_evidence
period_values_missing
monetary_unit_mismatch
```

---

## 8. Manifest and report expectations

Update manifest and run summary metrics to avoid hiding the distinction.

Keep existing fields when possible for compatibility:

```text
evidence_issue_count
```

Add more precise fields if useful:

```text
strong_evidence_count
weak_evidence_count
missing_evidence_count
not_applicable_evidence_count
weak_evidence_issue_count
missing_evidence_issue_count
```

The audit report should state whether rows are blocked by weak evidence or true missing evidence.

The evidence index should preserve evidence level per row if feasible.

---

## 9. Expected real-run improvement

After rerunning the same 348A real runner, the expected qualitative change is:

```text
missing_evidence should no longer equal 82 if workbook row lineage exists.
```

A good R1 result may still have many REVIEW rows.

The success condition is not `PASS everything`.

The success condition is:

```text
review_queue becomes diagnostically richer and separates weak lineage from true missing evidence.
```

---

## 10. Tests

Update or add tests in:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
```

Minimum test cases:

1. Row with explicit page/source evidence -> `STRONG_EVIDENCE` or no evidence issue.
2. Row with source PDF + sheet + row index but no page -> `WEAK_EVIDENCE` / `weak_evidence` issue.
3. Row without usable source PDF or workbook row lineage -> `MISSING_EVIDENCE` / `missing_evidence` issue.
4. Review queue distinguishes weak evidence from missing evidence.
5. Manifest or summary can count weak evidence separately from missing evidence if implemented.

Do not require real Excel/PDF files in unit tests.

Use compact in-memory records.

---

## 11. Validation commands

Run:

```powershell
cd D:\_datefac_agent

python -m py_compile datefac_agent\schemas\audit_models.py datefac_agent\audit\evidence_checker.py datefac_agent\review\review_queue_builder.py datefac_agent\delivery\evidence_index_writer.py datefac_agent\delivery\audit_report_writer.py tools\run_agent_excel_intake_audit_348a.py tests\agent\test_agent_excel_intake_audit_348a.py

python -m pytest tests\agent -q
```

Then rerun the real 348A pilot:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202606081823352906_1_331fresh_20260615_21591.pdf --excel-path D:\_datefac_agent\input\安井食品研报数据汇总.xlsx --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348a_r1
```

Use a new output directory for R1:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348a_r1
```

Do not overwrite the original 348A output directory.

---

## 12. Expected changed files

Expected source/test files:

```text
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/delivery/audit_report_writer.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Optional report doc:

```text
docs/agent/348A_R1_EVIDENCE_POLICY_REFINEMENT_RESULT.md
```

Do not commit output files under `output/`.

---

## 13. Completion report

Report:

1. Files created or modified.
2. Whether branch is `pivot/348-agent-foundation`.
3. Whether worktree was clean before editing.
4. What evidence levels were implemented.
5. py_compile result.
6. pytest result.
7. Real runner result and output directory.
8. Manifest decision and key R1 metrics.
9. `strong_evidence_count`, `weak_evidence_count`, `missing_evidence_count`, and `not_applicable_evidence_count` if available.
10. Whether `missing_evidence = 82` was resolved.
11. Whether review queue now distinguishes weak evidence from missing evidence.
12. Whether source code outside evidence/review/delivery runner scope was touched.
13. Whether legacy `datefac/` and old outputs were untouched.
14. Whether LLM/MinerU/OCR calls were zero.
15. `git status -sb`.
16. Recommended next task.

---

## 14. Likely next task

If R1 succeeds, the likely next task is:

```text
348A-R2 Row Type Classification Refinement
```

R2 should split narrative, market/reference, and strict financial table rows, but R1 should not try to solve all of that at once.
