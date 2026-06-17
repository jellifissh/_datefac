# 348A-R4-QA Clean Data Candidate Policy Review

## Task ID

`348A-R4-QA Clean Data Candidate Policy Review`

## Reviewed Output Directories

Primary required review target:

- `D:\_datefac_agent\output\agent_excel_intake_audit_348s_r4_third_taihao_keji_doubaoai`

Additional locally available sample coverage:

- `D:\_datefac_agent\output\agent_excel_intake_audit_348a_r4`
- `D:\_datefac_agent\output\agent_excel_intake_audit_348s_r2_h3_ap202605231822706325_1`

## Available Sample Coverage

This QA was able to review three latest local clean-data outputs:

- first real workbook R4 baseline
- second real workbook R2 latest validated output
- third real workbook R4 latest validated output

Coverage conclusion:

- sample coverage is sufficient for a cross-sample clean-data boundary QA
- third workbook R4 remains the main stress case because it has the largest review queue

## Verified Metrics

### Third workbook R4

- `clean_data_row_count = 94`
- `review_queue_row_count = 64`
- `unknown_row_count = 0`
- `unit_issue_count = 11`
- `period_issue_count = 2`
- `valuation_issue_count = 1`
- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`
- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

### First workbook local baseline

- `clean_data_row_count = 75`
- `review_queue_row_count = 7`
- `unknown_row_count = 0`
- readiness gates all `false`
- external call counters all `0`

### Second workbook local baseline

- `clean_data_row_count = 94`
- `review_queue_row_count = 18`
- `unknown_row_count = 0`
- readiness gates all `false`
- external call counters all `0`

## Clean-Data Composition QA

Conclusion:

- clean data contains only `STRICT_FINANCIAL_TABLE_ROW` and `MARKET_REFERENCE_ROW`
- no `NARRATIVE_ASSERTION` rows were found in clean data
- no `UNKNOWN_ROW` rows were found in clean data
- across all three reviewed outputs, clean data contains only internal clean/reference candidates

Observed clean-data row-type composition:

- first workbook: `STRICT_FINANCIAL_TABLE_ROW = 65`, `MARKET_REFERENCE_ROW = 10`
- second workbook: `STRICT_FINANCIAL_TABLE_ROW = 81`, `MARKET_REFERENCE_ROW = 13`
- third workbook: `STRICT_FINANCIAL_TABLE_ROW = 92`, `MARKET_REFERENCE_ROW = 2`

## Narrative/Layout/Metadata Exclusion QA

Conclusion:

- clean data excludes narrative rows
- clean data excludes metadata rows
- clean data excludes section-anchor and table-title rows

Evidence:

- third workbook R4 clean data has `0` `NARRATIVE_ASSERTION` rows
- third workbook R4 clean data has `0` `UNKNOWN_ROW` rows
- review queue still contains narrative rows, which confirms these rows were not mistakenly promoted into clean data

## Unit Issue Exclusion QA

Conclusion:

- clean data excludes rows with `percentage_unit_missing`
- clean data excludes rows with `implicit_percentage_unit_confirmation_needed`
- clean data excludes rows with `monetary_unit_mismatch`

Evidence:

- third workbook R4 review queue contains `implicit_percentage_unit_confirmation_needed = 10`
- third workbook R4 clean data contains `0` rows with that signal
- all reviewed clean-data outputs contain `0` rows with blocked unit issue codes

## Period Issue Exclusion QA

Conclusion:

- clean data excludes rows with `period_values_missing`
- the remaining two period review signals remain in review queue, not clean data

Evidence:

- third workbook R4 review queue still contains `period_values_missing = 2`
- third workbook R4 clean data contains `0` rows with `period_values_missing`

## Valuation Issue Exclusion QA

Conclusion:

- clean data excludes `valuation_metric_unit_suspicious`
- clean data excludes the associated mixed valuation blocker row

Evidence:

- third workbook R4 review queue still contains `valuation_metric_unit_suspicious = 1`
- third workbook R4 clean data contains `0` rows with valuation blocking issue codes

## Review-Queue Boundary QA

Conclusion:

- review queue still preserves rows that need human review
- review queue contains narrative review rows, implicit-percentage review rows, residual period review rows, and the mixed valuation blocker row
- the clean-data candidate policy is still conservative rather than permissive

Cross-sample signal:

- all three reviewed output directories retain non-empty review queues
- this indicates the policy still routes unresolved rows to review rather than over-promoting them into clean data

## Readiness Gate QA

Conclusion:

- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`

These gates remain closed across the reviewed outputs.

## External Call QA

Conclusion:

- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

These counters remain zero across the reviewed outputs.

## Baseline Validation

- `python -m pytest tests\agent -q`
- result: `38 passed`

## Decision

`348A_R4_QA_CONFIRMED_CLEAN_DATA_CANDIDATE_POLICY_VALID`

## Recommended Next Task

`348S next real-workbook generalization or next policy QA task, depending on newly added sample availability`

