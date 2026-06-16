# 348A-R2 Row Type Classification Refinement

## 1. Goal

Refine the 348A Excel intake audit workflow by adding row-type classification.

348A-R1 successfully separated weak workbook lineage from true missing evidence. R1 intentionally did not implement row-type classification. The next bottleneck is that narrative, market/reference, and strict financial statement rows are still handled with nearly the same review posture.

The goal is:

```text
Classify workbook rows into useful row types and make review/evidence outputs show that classification.
```

The goal is not:

```text
Fix unit checker false positives, re-extract PDFs, run MinerU, call LLMs, or make weak-evidence rows production/client ready.
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
docs/legacy/LEGACY_ASSET_MAP.md

docs/codex_tasks/348A_ai_extracted_excel_intake_audit_pilot.md
docs/codex_tasks/348A_QA_excel_intake_audit_result_review.md
docs/codex_tasks/348A_R1_evidence_policy_refinement.md
```

The QA report and R1 result are the direct basis for this task.

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

## 4. Why R2 exists

The 348A-QA report identified these row groups:

```text
核心观点
市场与基础数据
财务估值
资产负债表
利润表
现金流量表
```

It classified these as strict financial table sheets:

```text
财务估值
资产负债表
利润表
现金流量表
```

It classified these as narrative / semi-structured sheets:

```text
核心观点
市场与基础数据
```

The report also stated that narrative rows should not be audited under the same strict period/evidence expectations as structured financial-table rows.

R1 separated evidence levels:

```text
STRONG_EVIDENCE
WEAK_EVIDENCE
MISSING_EVIDENCE
NOT_APPLICABLE
```

But R1 explicitly did not implement row-type classification.

---

## 5. Row types to implement

Add a small row-type vocabulary.

Recommended values:

```text
STRICT_FINANCIAL_TABLE_ROW
MARKET_REFERENCE_ROW
NARRATIVE_ASSERTION
UNKNOWN_ROW
```

Recommended mapping for the current workbook:

```text
财务估值 -> STRICT_FINANCIAL_TABLE_ROW
资产负债表 -> STRICT_FINANCIAL_TABLE_ROW
利润表 -> STRICT_FINANCIAL_TABLE_ROW
现金流量表 -> STRICT_FINANCIAL_TABLE_ROW
市场与基础数据 -> MARKET_REFERENCE_ROW
核心观点 -> NARRATIVE_ASSERTION
```

If the classifier cannot identify a row, use:

```text
UNKNOWN_ROW
```

Do not add many fine-grained classes in this task. This is a first-pass classifier, not a taxonomy museum. Humanity has suffered enough taxonomies.

---

## 6. Source files in scope

Allowed source/test files:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/intake/excel_intake.py
datefac_agent/audit/row_type_classifier.py
datefac_agent/audit/period_alignment_checker.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/delivery/audit_report_writer.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Only modify files needed for row type classification and output visibility.

Expected new file:

```text
datefac_agent/audit/row_type_classifier.py
```

Optional result doc:

```text
docs/agent/348A_R2_ROW_TYPE_CLASSIFICATION_RESULT.md
```

---

## 7. Implementation expectations

### 7.1 Schema

Add a `RowType` type alias or equivalent simple model in:

```text
datefac_agent/schemas/audit_models.py
```

Suggested values:

```text
STRICT_FINANCIAL_TABLE_ROW
MARKET_REFERENCE_ROW
NARRATIVE_ASSERTION
UNKNOWN_ROW
```

Store row type either on `SpreadsheetRow` or `AuditRowResult`. Prefer placing it where downstream review/delivery can access it without reclassifying.

### 7.2 Classifier

Create:

```text
datefac_agent/audit/row_type_classifier.py
```

It should expose a small pure function such as:

```text
classify_row_type(row: SpreadsheetRow) -> RowType
```

The function should use sheet name and light structural cues.

Basic classification rules:

```text
sheet in 财务估值 / 资产负债表 / 利润表 / 现金流量表 -> STRICT_FINANCIAL_TABLE_ROW
sheet == 市场与基础数据 -> MARKET_REFERENCE_ROW
sheet == 核心观点 -> NARRATIVE_ASSERTION
otherwise -> UNKNOWN_ROW
```

Optionally, use header/period cues to keep strict table detection robust:

```text
has period columns such as 2024A / 2025A / 2026E -> strict financial table candidate
```

Do not use LLMs or semantic inference beyond deterministic rules.

### 7.3 Review queue output

Add `row_type` to `review_queue.csv` rows.

The queue should distinguish at least:

```text
NARRATIVE_ASSERTION + WEAK_EVIDENCE
MARKET_REFERENCE_ROW + WEAK_EVIDENCE
STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE
STRICT_FINANCIAL_TABLE_ROW + PERIOD_VALUES_MISSING
```

Do not necessarily turn weak-evidence rows into `PASS`. This task improves triage, not confidence theater.

### 7.4 Evidence index output

Add `row_type` to `evidence_index.json` entries.

### 7.5 Audit report output

Add row-type distribution to `audit_report.md`, for example:

```text
strict_financial_table_row_count
market_reference_row_count
narrative_assertion_count
unknown_row_count
```

### 7.6 Manifest and run summary

Add row-type count metrics if reasonable:

```text
strict_financial_table_row_count
market_reference_row_count
narrative_assertion_count
unknown_row_count
```

Keep existing manifest fields for compatibility.

Update `recommended_next_step` to a sensible next task, likely:

```text
348A-R3 Unit Checker False Positive Refinement
```

or:

```text
348A-R2-QA Row Type Classification Result Review
```

Pick conservatively based on the R2 result.

### 7.7 Period checker interaction

Avoid applying strict period expectations to narrative rows.

The current period checker uses sheet-name heuristics for financial sheets. Preserve or refine that behavior, but ensure R2 does not create period issues for `NARRATIVE_ASSERTION` rows.

Do not overhaul period logic beyond row-type-aware gating if needed.

### 7.8 Evidence checker interaction

Do not undo R1.

`WEAK_EVIDENCE` should remain distinct from `MISSING_EVIDENCE`.

R2 may include row type in evidence issue metadata if useful, but should not weaken evidence discipline into silent PASS.

---

## 8. Non-goals and hard boundaries

Do not fix the `净资产收益率(%)` monetary false positive in this task unless an existing R2 test cannot pass without minimal isolation. That belongs to a later unit checker refinement task.

Do not implement full clean-data candidate policy in this task.

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

## 9. Tests

Update or add tests in:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
```

Minimum tests:

1. `核心观点` row -> `NARRATIVE_ASSERTION`.
2. `市场与基础数据` row -> `MARKET_REFERENCE_ROW`.
3. `财务估值` row -> `STRICT_FINANCIAL_TABLE_ROW`.
4. `资产负债表` / `利润表` / `现金流量表` row -> `STRICT_FINANCIAL_TABLE_ROW`.
5. unknown sheet -> `UNKNOWN_ROW`.
6. review queue row includes `row_type`.
7. evidence index payload includes `row_type` if writer is unit-testable.
8. manifest or summary can count row types if implemented.

Do not require real Excel/PDF files in unit tests.

Use compact in-memory rows.

---

## 10. Validation commands

Run:

```powershell
cd D:\_datefac_agent

python -m py_compile datefac_agent\schemas\audit_models.py datefac_agent\intake\excel_intake.py datefac_agent\audit\row_type_classifier.py datefac_agent\audit\period_alignment_checker.py datefac_agent\audit\evidence_checker.py datefac_agent\review\review_queue_builder.py datefac_agent\delivery\evidence_index_writer.py datefac_agent\delivery\audit_report_writer.py tools\run_agent_excel_intake_audit_348a.py tests\agent\test_agent_excel_intake_audit_348a.py

python -m pytest tests\agent -q
```

Then rerun the real 348A pilot to a new R2 output directory:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202606081823352906_1_331fresh_20260615_21591.pdf --excel-path D:\_datefac_agent\input\安井食品研报数据汇总.xlsx --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348a_r2
```

Use a new output directory:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348a_r2
```

Do not overwrite the original 348A or R1 output directories.

---

## 11. Expected changed files

Expected source/test files:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/intake/excel_intake.py
datefac_agent/audit/row_type_classifier.py
datefac_agent/audit/period_alignment_checker.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/delivery/audit_report_writer.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Optional result doc:

```text
docs/agent/348A_R2_ROW_TYPE_CLASSIFICATION_RESULT.md
```

Do not commit output files under `output/`.

---

## 12. Completion report

Report:

1. Files created or modified.
2. Whether branch is `pivot/348-agent-foundation`.
3. Whether worktree was clean before editing.
4. What row types were implemented.
5. py_compile result.
6. pytest result.
7. Real runner result and R2 output directory.
8. Manifest decision and key R2 metrics.
9. Row-type distribution counts.
10. Whether `review_queue.csv` includes `row_type`.
11. Whether `evidence_index.json` includes `row_type`.
12. Whether review queue is more diagnostically useful than R1.
13. Whether source code outside R2 scope was touched.
14. Whether legacy `datefac/` and old outputs were untouched.
15. Whether LLM/MinerU/OCR calls were zero.
16. `git status -sb`.
17. Recommended next task.

---

## 13. Likely next task

If R2 succeeds, likely next tasks are:

```text
348A-R3 Unit Checker False Positive Refinement
348A-R2-QA Row Type Classification Result Review
348A-R4 Clean Data Candidate Policy
```

Do not start full legacy capability migration until the 348A single-sample workflow is explainable enough to become a stable regression target.
