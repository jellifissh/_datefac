# 348S Second Real Workbook Pilot Result

## Task ID

`348S Second Real Workbook Pilot`

## Input Inventory

Discovered candidate files under `D:\_datefac_agent\input`:

- `H3_AP202605231822706325_1.pdf`
- `H3_AP202605231822706325_1_提取结果.xlsx`
- `H3_AP202606081823352906_1_331fresh_20260615_21591.pdf`
- `安井食品研报数据汇总.xlsx`
- `泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx`
- `real_second_review/README_REAL_SECOND_REVIEW_INPUT.md`

## Samples Attempted

### Attempted sample 1

- PDF: `D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf`
- Excel: `D:\_datefac_agent\input\H3_AP202605231822706325_1_提取结果.xlsx`
- Output: `D:\_datefac_agent\output\agent_excel_intake_audit_348s_h3_ap202605231822706325_1`

## Samples Skipped And Why

### Skipped candidate 1

- Excel: `D:\_datefac_agent\input\泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx`
- Status: skipped
- Reason: `unmatched source PDF`

No unambiguous `泰豪科技` source PDF was found under `D:\_datefac_agent\input`, so this workbook was not forced through the runner.

### Not used as second sample

- PDF: `D:\_datefac_agent\input\H3_AP202606081823352906_1_331fresh_20260615_21591.pdf`
- Excel: `D:\_datefac_agent\input\安井食品研报数据汇总.xlsx`

This pair is the earlier baseline sample rather than the new second-real-workbook target, so it was not rerun as the 348S sample.

## Runner Result Per Sample

### H3_AP202605231822706325_1

- Runner status: `success`
- Manifest decision: `AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX`

## Manifest Metrics Per Successful Sample

### H3_AP202605231822706325_1

- `sheet_count = 8`
- `row_count_total = 119`
- `row_count_audited = 119`
- `pass_count = 0`
- `review_count = 117`
- `fail_count = 2`
- `issue_count_total = 187`
- `unit_issue_count = 2`
- `period_issue_count = 66`
- `valuation_issue_count = 0`
- `evidence_issue_count = 119`
- `strong_evidence_count = 0`
- `weak_evidence_count = 119`
- `missing_evidence_count = 0`
- `not_applicable_evidence_count = 0`
- `strict_financial_table_row_count = 66`
- `market_reference_row_count = 0`
- `narrative_assertion_count = 0`
- `unknown_row_count = 53`
- `clean_data_row_count = 0`
- `review_queue_row_count = 119`
- `internal_clean_candidate_count = 0`
- `internal_reference_candidate_count = 0`
- `narrative_review_count = 0`
- `review_required_count = 117`
- `excluded_from_clean_data_count = 2`
- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`
- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

## Failure Analysis

Primary failure classification:

`348S_CONFIRMED_NEEDS_INTAKE_GENERALIZATION`

Supporting classification:

`348S_CONFIRMED_WORKBOOK_SCHEMA_GAP`

Why this is not a runner crash:

- the runner completed successfully;
- all expected output files were produced;
- manifest and run summary were written normally.

Why this still counts as a real generalization gap:

- `unknown_row_count = 53` is extremely high;
- `market_reference_row_count = 0`;
- `narrative_assertion_count = 0`;
- `clean_data_row_count = 0`;
- `review_queue_row_count = 119`;
- `period_issue_count = 66`.

The new workbook contains a large `报告概要`-style area that the current row-type mapping does not understand. Those rows all fall into `UNKNOWN_ROW`, which prevents R4 candidate policy from helping.

The workbook also appears to encode structured financial rows in a way that triggers broad `period_context_missing` results across `66` strict rows, suggesting the current intake / row-shape assumptions are tuned too tightly to the first workbook family.

Observed review distribution:

- `UNKNOWN_ROW = 53`
- `STRICT_FINANCIAL_TABLE_ROW = 66`
- `REVIEW_REQUIRED = 117`
- `EXCLUDED_FROM_CLEAN_DATA = 2`

Observed issue distribution:

- `weak_evidence = 119`
- `period_context_missing = 66`
- `monetary_unit_mismatch = 2`

## Comparison Against 348A/R4 Baseline

### Baseline first workbook

- `clean_data_row_count = 75`
- `review_queue_row_count = 7`
- `internal_clean_candidate_count = 65`
- `internal_reference_candidate_count = 10`
- `narrative_review_count = 5`
- `review_required_count = 2`
- `unknown_row_count = 0`

### Second real workbook

- `clean_data_row_count = 0`
- `review_queue_row_count = 119`
- `internal_clean_candidate_count = 0`
- `internal_reference_candidate_count = 0`
- `narrative_review_count = 0`
- `review_required_count = 117`
- `unknown_row_count = 53`

Assessment:

The current 348A/R4 workflow is stable on the first workbook family, but it does not yet generalize to the second real workbook family without intake / row-type / period-context generalization.

## Generalization Assessment

Current primary decision:

`348S_CONFIRMED_NEEDS_INTAKE_GENERALIZATION`

Supporting decisions:

- `348S_CONFIRMED_WORKBOOK_SCHEMA_GAP`

Interpretation:

- The workflow can run end-to-end on a second real sample.
- The workflow does not yet classify or route that second workbook correctly enough to preserve internal clean candidates.
- The next task should not be broad legacy migration.
- The next task should be a narrow compatibility/generalization refinement driven by this workbook shape.

## Remaining Risks

- New workbook families may contain summary sheets, metadata sheets, or alternate table layouts that the current row-type mapping does not recognize.
- Period detection currently appears too strict for the second workbook’s financial-sheet structure.
- The two remaining unit failures should be rechecked after workbook-shape generalization, because some may be downstream of row-type/context mismatch.

## Recommended Next Task

Primary next task:

`348S-R1 Intake Schema Generalization`

Secondary follow-up after that:

- `348S-QA Second Real Workbook Pilot Review`
- `348F Fixture Harvest from 346B`

## Decision

Primary decision:

`348S_CONFIRMED_NEEDS_INTAKE_GENERALIZATION`

Supporting decision:

`348S_CONFIRMED_WORKBOOK_SCHEMA_GAP`
