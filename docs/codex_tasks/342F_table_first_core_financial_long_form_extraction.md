# 342F Table-First Core Financial Table Long-Form Extraction

## Goal

Build a sidecar `342F` long-form extraction pilot from the completed `342E` table-first audit.

This task must:

- read only `core_extractable` tables from `342E`
- expand those tables into long-form metric-year-value cells
- keep trusted / review-required / rejected cells separate
- remain a sidecar extraction pilot only

This task must not:

- modify production pipeline
- modify parser abstraction
- modify production extraction logic
- modify delivery or export logic
- rerun MinerU
- call any visual model
- write back any upstream workbook
- generate client export
- claim `342F` as a formal financial result
- modify `342B`, `342C6`, `342D`, or `342E` upstream artifacts
- commit output artifacts

## Confirmed Upstream State

`342E` is now table-first and already rerun on the real `342C6 / 342D` inputs.

Confirmed `342E` summary:

- `audited_pdf_count = 5`
- `total_table_block_count = 370`
- `core_extractable_table_count = 66`
- `metadata_extractable_table_count = 18`
- `excluded_table_count = 62`
- `manual_review_required_count = 224`
- `pdf_with_core_extractable_table_count = 5`
- `table_source_file_count = 25`
- `ready_for_342f = true`
- `recommended_342f_scope = table_first_core_extractable_only`
- `qa_fail_count = 0`
- `decision = CORE_METRIC_CANDIDATE_QUALITY_342E_READY`

## Inputs

- `D:/_datefac/output/real_pdf_corpus_intake_342b`
- `D:/_datefac/output/mineru_pilot_network_recovery_342c6`
- `D:/_datefac/output/parser_ensemble_compare_342d`
- `D:/_datefac/output/core_metric_candidate_quality_342e`

## Output Dir

- `D:/_datefac/output/table_first_core_financial_extraction_342f`

## Output Files

- `table_first_core_financial_extraction_342f.xlsx`
- `table_first_core_financial_extraction_342f_summary.json`
- `table_first_core_financial_extraction_342f_manifest.json`
- `table_first_core_financial_extraction_342f_qa.json`
- `table_first_core_financial_extraction_342f_report.md`
- `table_first_core_financial_extraction_342f_no_write_back_proof.json`

## Workbook Sheets

1. `00_README`
2. `01_EXTRACTION_SUMMARY`
3. `02_INPUT_CORE_TABLES`
4. `03_LONG_FORM_CELLS`
5. `04_TRUSTED_CELLS`
6. `05_REVIEW_REQUIRED`
7. `06_REJECTED_CELLS`
8. `07_METRIC_COVERAGE`
9. `08_UNIT_NORMALIZATION`
10. `09_TABLE_TRACE`
11. `10_342G_READINESS`
12. `11_NO_WRITE_BACK_PROOF`
13. `12_NEXT_STEPS`

All sheet names must remain `<= 31` characters.

## Required Input Gates

`342F` must confirm from `342E`:

- `ready_for_342f = true`
- `recommended_342f_scope = table_first_core_extractable_only`
- `core_extractable_table_count > 0`
- `pdf_with_core_extractable_table_count = 5`
- `qa_fail_count = 0`

If any gate fails, `342F` must QA fail.

## Required Table Scope

`342F` must read `342E` workbook sheets:

- `03_ALL_TABLE_BLOCKS`
- `05_CORE_EXTRACTABLE`
- `06_METADATA_EXTRACTABLE`
- `07_EXCLUDED_TABLES`

But the long-form core extraction may only consume:

- `05_CORE_EXTRACTABLE`

`06_METADATA_EXTRACTABLE` and `07_EXCLUDED_TABLES` may only be used for boundary checks.

## Allowed Core Table Types

Only process:

- `CORE_FORECAST_SUMMARY`
- `BALANCE_SHEET`
- `INCOME_STATEMENT`
- `CASH_FLOW_STATEMENT`
- `VALUATION_METRICS`

Do not process:

- `BASIC_DATA`
- `RATING_STANDARD`
- `DISCLAIMER`
- `RELATED_REPORTS`
- `CHART_OR_IMAGE`
- `NOISE_TABLE`
- `UNKNOWN_TABLE`

## Long-Form Output Fields

Each extracted cell row must include at least:

- `long_cell_id`
- `corpus_pdf_id`
- `file_name`
- `table_id`
- `table_type`
- `table_value_class`
- `source_file`
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
- `row_index`
- `col_index`
- `source_html_snippet`
- `extraction_status`
- `review_reason`
- `risk_flags`
- `confidence_signal`

## Core Rules

1. Parse HTML tables only from existing `342E` core table rows.
2. If HTML is missing or cannot be parsed:
   - `table_parse_status = HTML_PARSE_FAILED`
   - create review-required evidence
   - do not call a visual model
3. Expand wide tables into long-form cells.
4. Detect years from column headers:
   - `2024A`
   - `2025A`
   - `2026E`
   - `2027E`
   - `2028E`
   - and compatible plain-year forms `2024` to `2028`
5. If year header is missing, do not promote cells to trusted automatically.
6. Support core metric mappings for:
   - `revenue`
   - `net_profit`
   - `EPS`
   - `PE`
   - `PB`
   - `ROE`
   - `gross_margin`
   - `net_margin`
   - `revenue_yoy`
   - `net_profit_yoy`
   - `operating_cash_flow`
   - `investing_cash_flow`
   - `financing_cash_flow`
   - `cash_net_change`
   - `total_assets`
   - `total_liabilities`
   - `shareholder_equity`
   - `total_liabilities_and_equity`
7. `(+/-%)` rows cannot stand alone.
   They must bind to the previous meaningful metric row:
   - previous `revenue` -> `revenue_yoy`
   - previous `net_profit` -> `net_profit_yoy`
   - otherwise `REVIEW_REQUIRED_GROWTH_ROW_UNBOUND`
8. Parse parenthesized negatives:
   - `(10)` -> `-10`
   - `(57)` -> `-57`
   - `(140)` -> `-140`
   and add risk flag:
   - `PAREN_NEGATIVE_VALUE`
9. Deduplicate by:
   - `corpus_pdf_id`
   - `table_id`
   - `metric_standardized`
   - `year_standardized`
   - `value_numeric`
   - `normalized_unit`
   Keep the highest-confidence row and downgrade the rest to review-required duplicate evidence.

## `extraction_status` Values

Allowed values:

- `TRUSTED_CELL`
- `REVIEW_REQUIRED`
- `REJECTED_CELL`

## Summary Fields

- `audited_pdf_count = 5`
- `input_core_extractable_table_count`
- `parsed_core_table_count`
- `html_parse_failed_table_count`
- `long_form_cell_count`
- `trusted_cell_count`
- `review_required_cell_count`
- `rejected_cell_count`
- `metric_covered_count`
- `metric_year_pair_count`
- `unit_issue_count`
- `year_header_issue_count`
- `duplicate_cell_count`
- `table_trace_count`
- `ready_for_342g`
- `recommended_342g_scope`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `decision = TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_READY`

## Validation

```powershell
python -m py_compile datefac\benchmark\table_first_core_financial_extraction_342f.py datefac\benchmark\table_first_core_financial_extraction_342f_report.py tools\run_table_first_core_financial_extraction_342f.py tests\benchmark\test_table_first_core_financial_extraction_342f.py

python -m pytest tests\benchmark\test_table_first_core_financial_extraction_342f.py -q

python tools\run_table_first_core_financial_extraction_342f.py `
  --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b `
  --mineru-342c6-dir D:\_datefac\output\mineru_pilot_network_recovery_342c6 `
  --parser-compare-342d-dir D:\_datefac\output\parser_ensemble_compare_342d `
  --candidate-quality-342e-dir D:\_datefac\output\core_metric_candidate_quality_342e `
  --output-dir D:\_datefac\output\table_first_core_financial_extraction_342f
```
