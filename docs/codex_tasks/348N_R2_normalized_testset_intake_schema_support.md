# 348N-R2 Normalized Testset Intake Schema Support

## Goal

Add narrow intake support for the `normalized_testset` long-record schema found in the Linyang Energy workbook.

This is a targeted implementation task, not a broad policy redesign.

The goal is to make the pipeline recognize the testset long-record shape explicitly instead of counting it as generic `UNKNOWN_ROW`.

---

## Current diagnosis

R1 result:

```text
348N_R1_CONFIRMED_LINYANG_UNKNOWN_ROW_FAMILIES_DIAGNOSED
```

Key facts:

```text
row_count_total = 483
clean_data_row_count = 37
review_queue_row_count = 446
unknown_row_count = 367
normalized_testset unknown rows = 319
```

R1 conclusion:

```text
The unknown-row spike is mostly testset-specific workbook structure, not ordinary financial workbook schema mismatch.
normalized_testset is a normalized long-record extraction dataset, not a standard wide financial table.
```

Important warning:

```text
Do not directly reroute normalized_testset rows into STRICT_FINANCIAL_TABLE_ROW.
Do not directly reroute normalized_testset rows into MARKET_REFERENCE_ROW.
Do not let normalized_testset rows enter clean_data by default.
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
docs/agent/348N_R1_LINYANG_UNKNOWN_ROW_SHAPE_DIAGNOSIS.md
docs/agent/348N_NEW_REAL_WORKBOOK_GENERALIZATION_PILOT_RESULT.md
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
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

## Input/output for replay

Input pair:

```text
PDF:   D:\_datefac_agent\input\6862e6f3995d3dbfbed310b51601fb0a.pdf
Excel: D:\_datefac_agent\input\linyang_energy_pdf_extracted_testset (1).xlsx
```

Baseline output to compare:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348n_linyang_energy_testset
```

New output directory:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348n_r2_linyang_normalized_testset_schema
```

Do not commit output files.

---

## Required implementation direction

Implement narrow schema recognition for the `normalized_testset` sheet.

Detect the sheet by header family, not by only filename.

Expected header-like fields include:

```text
record_id
source_pdf
source_page
table_name
statement
line_item
period
value
unit
value_text_original
confidence
note
```

If this header family is detected:

```text
classify rows as explicit normalized-testset records, not generic UNKNOWN_ROW
keep them review-only / schema-specific unless later policy says otherwise
do not route them into normal strict-table clean_data path
do not route them into market-reference clean_data path
preserve source_pdf / source_page / table_name / line_item / period / value / unit lineage where current model supports it
```

Preferred outcome:

```text
unknown_row_count should drop materially, especially for normalized_testset rows
clean_data_row_count should not increase because of normalized_testset rows
review_queue may remain large, but should become more explainable
```

If current row-type model cannot safely add a new row type, implement the smallest safe explicit marker available in the existing architecture, but do not hide the schema-specific nature of these rows.

---

## Out-of-scope for this task

Do not solve every Linyang unknown family in this task.

Keep these separate unless needed for tests:

```text
README metadata/narrative routing
data_dictionary bookkeeping routing
figure_index routing
doc_metadata routing
related_research routing
market_base_data MARKET_REFERENCE_ROW routing
```

Do not broaden global unit, period, valuation, evidence, or clean-candidate rules.

Do not change readiness gates.

---

## Allowed changes

Allowed source/test/docs changes:

```text
datefac_agent/intake/excel_intake.py
datefac_agent/audit/  # only if the new explicit row type requires audit-layer exclusion from clean path
datefac_agent/review/ # only if the new explicit row type requires review routing support
tests/agent/test_agent_excel_intake_audit_348a.py
tests/agent/fixtures/  # compact fixture only if useful
docs/agent/348N_R2_NORMALIZED_TESTSET_INTAKE_SCHEMA_SUPPORT_RESULT.md
```

Do not modify legacy `datefac/` package.

Do not modify input files.

Do not commit output files.

---

## Required tests

Add targeted tests for:

```text
normalized_testset header detection
normalized_testset row classification is no longer generic UNKNOWN_ROW
normalized_testset rows remain excluded from clean_data
normal wide workbook rows still classify as before
clean-data candidate policy is not widened
```

Existing agent tests must still pass.

---

## Required validation

Run:

```powershell
python -m py_compile datefac_agent\intake\excel_intake.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\6862e6f3995d3dbfbed310b51601fb0a.pdf --excel-path "D:\_datefac_agent\input\linyang_energy_pdf_extracted_testset (1).xlsx" --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348n_r2_linyang_normalized_testset_schema
```

If more Python files are modified, include them in py_compile.

---

## Expected report

Create:

```text
docs/agent/348N_R2_NORMALIZED_TESTSET_INTAKE_SCHEMA_SUPPORT_RESULT.md
```

Include:

```text
Task ID
Files modified
Schema detection summary
Row-type / routing behavior
Before/after metrics
Clean-data boundary QA
Review-queue QA
Unknown-row QA
Regression test summary
Validation commands and results
Boundary discipline
Decision
Recommended next task
```

Decision values:

```text
348N_R2_CONFIRMED_NORMALIZED_TESTSET_SCHEMA_SUPPORT_VALID
348N_R2_CONFIRMED_PARTIAL_SCHEMA_SUPPORT_STILL_NEEDS_REFINEMENT
348N_R2_BLOCKED_BY_MODEL_CONTRACT_LIMITATION
348N_R2_BLOCKED_BY_RUNNER_FAILURE
```

---

## Completion report

Report:

1. Files modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Schema detection behavior.
5. Row type / routing behavior.
6. Before/after metrics.
7. Whether normalized_testset rows stopped being generic UNKNOWN_ROW.
8. Whether clean_data stayed conservative.
9. Whether review_queue became more explainable.
10. pytest result.
11. Runner result and output directory.
12. Whether legacy datefac/ was untouched.
13. Whether output files were not committed.
14. Whether LLM/MinerU/OCR calls were zero.
15. git status -sb.
16. Recommended next task.
