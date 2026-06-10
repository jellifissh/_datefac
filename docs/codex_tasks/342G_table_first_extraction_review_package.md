# 342G Table-First Extraction Review Package

## Goal

Build a sidecar `342G` review package from the completed `342F` table-first long-form extraction output.

This task must:

- read the completed `342F` review-ready workbook and summary / QA artifacts
- organize `REVIEW_REQUIRED` cells into a reviewer-friendly queue
- create a bounded trusted-cell audit sample for spot checking
- summarize unit / year / duplicate / growth-row / source-trace risks
- generate a reusable manual review template for the next `342H` apply simulation step

This task must not:

- modify production pipeline
- modify parser abstraction
- modify production extraction logic
- modify delivery or export logic
- rerun MinerU
- call any visual model or LLM
- write back any upstream workbook
- generate client export
- claim `342G` as a formal financial result
- modify `342B`, `342C6`, `342D`, `342E`, or `342F` upstream artifacts
- commit output artifacts

## Confirmed Upstream State

`342F` is completed and is the only formal upstream extraction input for `342G`.

Confirmed `342F` summary:

- `audited_pdf_count = 5`
- `input_core_extractable_table_count = 66`
- `parsed_core_table_count = 66`
- `html_parse_failed_table_count = 0`
- `long_form_cell_count = 5607`
- `trusted_cell_count = 1428`
- `review_required_cell_count = 1005`
- `rejected_cell_count = 3174`
- `metric_covered_count = 17`
- `metric_year_pair_count = 94`
- `unit_issue_count = 18`
- `year_header_issue_count = 135`
- `duplicate_cell_count = 387`
- `ready_for_342g = true`
- `recommended_342g_scope = table_first_extraction_review_package`
- `qa_fail_count = 0`
- `decision = TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_READY`
- `no_write_back_proof_passed = true`

## Inputs

- `D:/_datefac/output/real_pdf_corpus_intake_342b`
- `D:/_datefac/output/mineru_pilot_network_recovery_342c6`
- `D:/_datefac/output/parser_ensemble_compare_342d`
- `D:/_datefac/output/core_metric_candidate_quality_342e`
- `D:/_datefac/output/table_first_core_financial_extraction_342f`

## Primary Input Workbook

- `D:/_datefac/output/table_first_core_financial_extraction_342f/table_first_core_financial_extraction_342f.xlsx`

Priority workbook sheets to read:

- `01_EXTRACTION_SUMMARY`
- `03_LONG_FORM_CELLS`
- `04_TRUSTED_CELLS`
- `05_REVIEW_REQUIRED`
- `06_REJECTED_CELLS`
- `07_METRIC_COVERAGE`
- `08_UNIT_NORMALIZATION`
- `09_TABLE_TRACE`
- `10_342G_READINESS`
- `11_NO_WRITE_BACK_PROOF`

## Output Dir

- `D:/_datefac/output/table_first_extraction_review_package_342g`

## Output Files

- `table_first_extraction_review_package_342g.xlsx`
- `table_first_extraction_review_package_342g_summary.json`
- `table_first_extraction_review_package_342g_manifest.json`
- `table_first_extraction_review_package_342g_qa.json`
- `table_first_extraction_review_package_342g_report.md`
- `table_first_extraction_review_package_342g_no_write_back_proof.json`

## Workbook Sheets

1. `00_README`
2. `01_REVIEW_SUMMARY`
3. `02_INPUT_342F_SUMMARY`
4. `03_REVIEW_QUEUE`
5. `04_TRUSTED_AUDIT`
6. `05_UNIT_YEAR_ISSUES`
7. `06_DUPLICATE_ISSUES`
8. `07_GROWTH_ROW_ISSUES`
9. `08_TABLE_TRACE`
10. `09_REVIEW_GUIDE`
11. `10_REVIEW_TEMPLATE`
12. `11_DECISION_OPTIONS`
13. `12_342H_READINESS`
14. `13_NO_WRITE_BACK`
15. `14_NEXT_STEPS`

All sheet names must remain `<= 31` characters.

## Required Input Gates

`342G` must confirm from `342F`:

- `table_first_core_financial_extraction_342f_summary.json` exists
- `table_first_core_financial_extraction_342f_qa.json` exists
- `table_first_core_financial_extraction_342f.xlsx` exists
- `decision = TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_READY`
- `ready_for_342g = true`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- workbook includes:
  - `03_LONG_FORM_CELLS`
  - `04_TRUSTED_CELLS`
  - `05_REVIEW_REQUIRED`
  - `09_TABLE_TRACE`

If any gate fails:

- `qa_fail_count > 0`
- `ready_for_342h = false`
- `decision = TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_NOT_READY`
- do not emit a misleading review package

## Scope Rules

### 1. Review Queue

Build `03_REVIEW_QUEUE` from `342F` sheet `05_REVIEW_REQUIRED` only.

Must not:

- mix `06_REJECTED_CELLS` into the main review queue
- mix metadata / `BASIC_DATA` into the core review queue
- mix excluded tables into the core review queue

### 2. Trusted Audit

Build `04_TRUSTED_AUDIT` from `342F` sheet `04_TRUSTED_CELLS` only.

Sampling strategy must cover:

- every PDF
- every `table_type`
- every `metric_standardized`
- high value / negative value / percent / ratio style metrics
- weaker source trace cases when present

Trusted audit is spot check only.
It does not downgrade all trusted cells.

Recommended upper bound:

- `trusted_audit_sample_count <= 150`

### 3. Unit / Year Issue Rollup

Build `05_UNIT_YEAR_ISSUES` from `LONG_FORM_CELLS` and `REVIEW_REQUIRED`.

Must include issue classes such as:

- `UNIT_MISMATCH`
- `UNIT_MISSING`
- `YEAR_HEADER_MISSING`
- `YEAR_ALIGNMENT_RISK`
- `REVIEW_REQUIRED_YEAR_HEADER_MISSING`
- empty `normalized_unit`
- empty `year_standardized`

### 4. Duplicate Issue Rollup

Build `06_DUPLICATE_ISSUES` from duplicate evidence in `342F`.

Fields must include:

- `duplicate_group_key`
- `corpus_pdf_id`
- `table_id`
- `metric_standardized`
- `year_standardized`
- `value_numeric`
- `normalized_unit`
- `duplicate_count`
- `recommended_review_action`

### 5. Growth-Row Issue Rollup

Build `07_GROWTH_ROW_ISSUES`.

Focus on:

- `(+/-%)` rows
- `revenue_yoy`
- `net_profit_yoy`
- growth rows needing source confirmation
- any growth-row trace ambiguity that should be reviewed before `342H`

### 6. Table Trace

Build `08_TABLE_TRACE` from `342F` sheet `09_TABLE_TRACE`.

Must preserve:

- `corpus_pdf_id`
- `file_name`
- `table_id`
- `table_type`
- `source_page`
- `bbox`
- `image_path`
- `source_file`
- `html_available`
- `parse_status`
- `extracted_cell_count`
- `trusted_cell_count`
- `review_required_count`
- `rejected_cell_count`

### 7. Review Template

Build `10_REVIEW_TEMPLATE`.

This sheet is the main human-editable workbook surface for `342H`.

Each review row must include at least:

- `review_item_id`
- `review_priority`
- `review_bucket`
- `corpus_pdf_id`
- `file_name`
- `table_id`
- `table_type`
- `source_page`
- `bbox`
- `image_path`
- `metric_raw`
- `metric_standardized`
- `year_raw`
- `year_standardized`
- `value_raw`
- `value_numeric`
- `unit_raw`
- `normalized_unit`
- `extraction_status`
- `review_reason`
- `risk_flags`
- `confidence_signal`
- `source_html_snippet`

The following reviewer-editable fields must exist and remain blank in generated output:

- `reviewer_decision`
- `reviewer_metric_standardized`
- `reviewer_year_standardized`
- `reviewer_value_numeric`
- `reviewer_normalized_unit`
- `reviewer_note`
- `reviewer_id`
- `reviewed_at`

### 8. Decision Options

Build `11_DECISION_OPTIONS`.

Allowed `reviewer_decision` values:

- `CONFIRM_CELL`
- `CORRECT_AND_CONFIRM`
- `REJECT_CELL`
- `KEEP_REVIEW_REQUIRED`
- `NOT_A_CORE_METRIC`
- `NEEDS_SOURCE_CHECK`

Meanings:

- `CONFIRM_CELL`: original extraction is correct
- `CORRECT_AND_CONFIRM`: reviewer fixes metric / year / value / unit, then confirms
- `REJECT_CELL`: not a valid core metric cell
- `KEEP_REVIEW_REQUIRED`: still uncertain, remain pending
- `NOT_A_CORE_METRIC`: not part of the target core financial metric scope
- `NEEDS_SOURCE_CHECK`: needs PDF / image / bbox checking before decision

### 9. Review Priority

Every review item must get a priority.

`HIGH` examples:

- unit mismatch
- year header missing
- duplicate conflict
- metric / year / value conflict
- growth-row ambiguity
- trusted audit row with weak source trace

`MEDIUM` examples:

- unit missing but metric is otherwise clear
- value parse uncertain
- parenthesized negative value requiring extra confirmation
- table alignment risk

`LOW` examples:

- ordinary review-required row with complete source trace
- trusted audit sample without obvious risk

## Summary Fields

`table_first_extraction_review_package_342g_summary.json` must include at least:

- `audited_pdf_count`
- `input_long_form_cell_count`
- `input_trusted_cell_count`
- `input_review_required_cell_count`
- `input_rejected_cell_count`
- `review_queue_count`
- `trusted_audit_sample_count`
- `unit_year_issue_count`
- `duplicate_issue_count`
- `growth_row_issue_count`
- `high_priority_review_count`
- `medium_priority_review_count`
- `low_priority_review_count`
- `pdf_with_review_item_count`
- `table_with_review_item_count`
- `metric_with_review_item_count`
- `review_template_row_count`
- `ready_for_342h`
- `recommended_342h_scope`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count`
- `decision`

Recommended decision logic:

```text
if qa_fail_count == 0 and review_template_row_count > 0:
  ready_for_342h = true
  recommended_342h_scope = table_first_human_review_apply_simulation
  decision = TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_READY
else:
  ready_for_342h = false
  decision = TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_NOT_READY
```

## QA Requirements

Must check:

- `342F` input exists
- `342F ready_for_342g = true`
- `342F qa_fail_count = 0`
- required `342F` workbook sheets exist
- review queue generated from `REVIEW_REQUIRED` only
- trusted audit generated from `TRUSTED_CELL` only
- rejected cells not mixed into review queue
- `BASIC_DATA` not mixed into core review queue
- excluded tables not mixed into core review queue
- source trace fields preserved
- reviewer fields are blank
- decision options generated
- review guide generated
- `342H` readiness generated
- no upstream workbook modified
- no production pipeline / parser / extraction / delivery modified
- no output artifacts staged
- `client_ready = false`
- `production_ready = false`
- no investment advice claim
- all sheet names `<= 31` chars
- `qa_fail_count = 0`

## Report

Generate:

- `table_first_extraction_review_package_342g_report.md`

The report should say clearly:

- `342G` is a review package, not a formal financial result
- `342F` already completed long-form extraction
- `342G` uses `342F` `REVIEW_REQUIRED` rows and a trusted audit sample to build a review workbook
- current state is still not `client_ready` and not `production_ready`
- next step is `342H Table-First Human Review Apply Simulation`

Chinese should be primary, with supporting English where useful.

## Ledger Update

After task completion, update:

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Add `342G` record with:

- status
- input
- output
- key metrics
- QA result
- decision
- next recommended task = `342H Table-First Human Review Apply Simulation`
- do-not-repeat notes

If `.skills/project_milestone_ledger.md` rules do not change, do not modify that skill.

## Validation

```powershell
python -m py_compile datefac\benchmark\table_first_extraction_review_package_342g.py datefac\benchmark\table_first_extraction_review_package_342g_report.py tools\run_table_first_extraction_review_package_342g.py tests\benchmark\test_table_first_extraction_review_package_342g.py

python -m pytest tests\benchmark\test_table_first_extraction_review_package_342g.py -q

python tools\run_table_first_extraction_review_package_342g.py `
  --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b `
  --mineru-342c6-dir D:\_datefac\output\mineru_pilot_network_recovery_342c6 `
  --parser-compare-342d-dir D:\_datefac\output\parser_ensemble_compare_342d `
  --candidate-quality-342e-dir D:\_datefac\output\core_metric_candidate_quality_342e `
  --core-extraction-342f-dir D:\_datefac\output\table_first_core_financial_extraction_342f `
  --output-dir D:\_datefac\output\table_first_extraction_review_package_342g
```
