# 342E Core Metric Candidate Quality Audit From MinerU Pilot Outputs

## Goal

Convert `342E` from the old text-candidate audit into a strict table-first sidecar audit.

This task must read existing MinerU pilot outputs only and extract table blocks from:

- `.md`
- `content_list.json`
- `content_list_v2.json`
- `middle.json`
- `model.json`
- `images/`

This task is still audit-only.
It must not:

- modify production pipeline
- modify parser abstraction
- modify extraction logic in production code
- modify delivery or export logic
- rerun MinerU
- call any visual model
- write back any upstream workbook
- modify `342B`, `342C`, `342C2`, `342C4`, `342C6`, or `342D` upstream artifacts
- commit output artifacts

## Current Confirmed Context

`342C6` is now fully recovered at the pilot level:

- `final_success_count = 5`
- `final_failed_count = 0`
- `ready_for_342d = true`
- `qa_fail_count = 0`
- `decision = MINERU_PILOT_NETWORK_RECOVERY_342C6_READY`

`342D` is the trusted readiness input for this task:

- `compared_pdf_count = 5`
- `mineru_success_count = 5`
- `mineru_artifact_complete_count = 5`
- `mineru_markdown_usable_count = 5`
- `mineru_content_list_usable_count = 5`
- `ready_for_342e = true`
- `qa_fail_count = 0`
- `decision = PARSER_ENSEMBLE_COMPARE_342D_READY`
- `no_write_back_proof_passed = true`

## Important Source-of-Truth Rule

Do not assume every successful MinerU output lives under local `342C6/mineru_outputs`.

The true parse directory for each PDF must be taken from the `342C6` workbook sheet:

- `04_FINAL_PILOT_ROLLUP`
- field: `output_dir`

Some successful rows were reused from `342C2 after env fix` and point into:

- `D:/_datefac/output/mineru_pilot_retry_verified_env_342c2_after_env_fix`

## Inputs

- `D:/_datefac/output/real_pdf_corpus_intake_342b`
- `D:/_datefac/output/mineru_pilot_network_recovery_342c6`
- `D:/_datefac/output/parser_ensemble_compare_342d`

## Output Dir

- `D:/_datefac/output/core_metric_candidate_quality_342e`

## Output Files

- `core_metric_candidate_quality_342e.xlsx`
- `core_metric_candidate_quality_342e_summary.json`
- `core_metric_candidate_quality_342e_manifest.json`
- `core_metric_candidate_quality_342e_qa.json`
- `core_metric_candidate_quality_342e_report.md`
- `core_metric_candidate_quality_342e_no_write_back_proof.json`

## Workbook Sheets

1. `00_README`
2. `01_TABLE_QUALITY_SUMMARY`
3. `02_PDF_TABLE_SIGNAL`
4. `03_ALL_TABLE_BLOCKS`
5. `04_TABLE_TYPE_COVERAGE`
6. `05_CORE_EXTRACTABLE`
7. `06_METADATA_EXTRACTABLE`
8. `07_EXCLUDED_TABLES`
9. `08_SOURCE_TRACE_AUDIT`
10. `09_342F_READINESS`
11. `10_NO_WRITE_BACK_PROOF`
12. `11_NEXT_STEPS`

All sheet names must remain `<= 31` characters.

## Required Per-Table Fields

Each extracted table row must record at least:

- `table_id`
- `pdf_id`
- `file_name`
- `page_idx`
- `bbox`
- `html`
- `img_path`
- `caption`
- `footnote`
- `source_file`
- `source_kind`
- `row_count`
- `column_count`
- `header_year_tokens`
- `financial_keyword_hits`
- `table_type`
- `table_value_class`
- `extraction_recommendation`

## Allowed `table_type` Values

- `CORE_FORECAST_SUMMARY`
- `BALANCE_SHEET`
- `INCOME_STATEMENT`
- `CASH_FLOW_STATEMENT`
- `VALUATION_METRICS`
- `BASIC_DATA`
- `RATING_STANDARD`
- `RELATED_REPORTS`
- `DISCLAIMER`
- `CHART_OR_IMAGE`
- `NOISE_TABLE`
- `UNKNOWN_TABLE`

## Extraction Recommendation Rules

Only these table types may be marked `core_extractable`:

- `CORE_FORECAST_SUMMARY`
- `BALANCE_SHEET`
- `INCOME_STATEMENT`
- `CASH_FLOW_STATEMENT`
- `VALUATION_METRICS`

`BASIC_DATA` must be marked:

- `metadata_extractable`

These must not enter core financial extraction:

- `RATING_STANDARD`
- `RELATED_REPORTS`
- `DISCLAIMER`
- `CHART_OR_IMAGE`
- `NOISE_TABLE`

Their recommendation must be:

- `exclude_from_core_extraction`

`UNKNOWN_TABLE` should remain:

- `manual_review_required`

## Required Behavior

1. Confirm `342D` readiness:
   - `decision = PARSER_ENSEMBLE_COMPARE_342D_READY`
   - `ready_for_342e = true`
   - `mineru_success_count = 5`
   - `mineru_artifact_complete_count = 5`
   - `qa_fail_count = 0`
2. Read the five successful MinerU outputs only from already-existing files.
3. Extract all table blocks from the available MinerU sidecar evidence.
4. Prefer `content_list.json` and `content_list_v2.json` HTML tables as the main structured table source.
5. Use `middle.json`, `model.json`, and markdown `<table>` blocks as source-trace supplements and additional table evidence.
6. Do not call any vision model.
7. Do not rerun MinerU.
8. Classify every extracted table into one allowed `table_type`.
9. Generate:
   - PDF-level table signal summary
   - table-type coverage summary
   - core-extractable table audit
   - metadata-extractable table audit
   - excluded-table audit
   - source-trace audit
   - `342F` table-first readiness recommendation
10. The previous first version of `342E` produced `435` text candidates.
    That result is now historical only and must not be used as the direct formal extraction source.

## Summary Fields

- `audited_pdf_count = 5`
- `total_table_block_count`
- `core_extractable_table_count`
- `metadata_extractable_table_count`
- `excluded_table_count`
- `manual_review_required_count`
- `pdf_with_core_extractable_table_count`
- `table_source_file_count`
- `ready_for_342f`
- `recommended_342f_scope`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `decision = CORE_METRIC_CANDIDATE_QUALITY_342E_READY`

## Validation

```powershell
python -m py_compile datefac\benchmark\core_metric_candidate_quality_342e.py datefac\benchmark\core_metric_candidate_quality_342e_report.py tools\run_core_metric_candidate_quality_342e.py tests\benchmark\test_core_metric_candidate_quality_342e.py

python -m pytest tests\benchmark\test_core_metric_candidate_quality_342e.py -q

python tools\run_core_metric_candidate_quality_342e.py `
  --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b `
  --mineru-342c6-dir D:\_datefac\output\mineru_pilot_network_recovery_342c6 `
  --parser-compare-342d-dir D:\_datefac\output\parser_ensemble_compare_342d `
  --output-dir D:\_datefac\output\core_metric_candidate_quality_342e
```
