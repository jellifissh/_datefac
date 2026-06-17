# 348S-R2-QA Unit/Period Residual Refinement Review

## Task ID

`348S-R2-QA Unit/Period Residual Refinement Review`

## Reviewed Output Directories

Second sample R2 output:

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r2_h3_ap202605231822706325_1`

Baseline regression R2 output:

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r2_regression_348a_baseline`

R1 comparison output:

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_h3_ap202605231822706325_1`

Reviewed files:

- `agent_excel_intake_audit_348a_manifest.json`
- `agent_excel_intake_audit_348a_run_summary.json`
- `audit_report.md`
- `evidence_index.json`
- `review_queue.csv`
- `clean_data.csv`

## Verified Metrics

### Second sample R2

- `decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX`
- `row_count_total = 112`
- `row_count_audited = 112`
- `fail_count = 0`
- `unit_issue_count = 0`
- `period_issue_count = 0`
- `clean_data_row_count = 94`
- `review_queue_row_count = 18`
- `strict_financial_table_row_count = 81`
- `market_reference_row_count = 13`
- `narrative_assertion_count = 18`
- `unknown_row_count = 0`
- `internal_clean_candidate_count = 81`
- `internal_reference_candidate_count = 13`
- `narrative_review_count = 18`
- `review_required_count = 0`
- `excluded_from_clean_data_count = 0`
- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`
- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

### Baseline regression R2

- `decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX`
- `row_count_total = 82`
- `row_count_audited = 82`
- `fail_count = 0`
- `unit_issue_count = 0`
- `period_issue_count = 2`
- `clean_data_row_count = 75`
- `review_queue_row_count = 7`
- `strict_financial_table_row_count = 67`
- `market_reference_row_count = 10`
- `narrative_assertion_count = 5`
- `unknown_row_count = 0`
- `internal_clean_candidate_count = 65`
- `internal_reference_candidate_count = 10`
- `narrative_review_count = 5`
- `review_required_count = 2`
- `excluded_from_clean_data_count = 0`
- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`
- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

## Unit Residual QA

The two prior unit residual rows were verified as repaired rather than dropped:

- `报告概要 / row 15 / 资产负债率(%,LF)`
- `重要财务与估值指标 / row 8 / 资产负债率(%)`

Observed in R2:

- both rows still exist in `clean_data.csv`
- both rows still exist in `evidence_index.json`
- neither row appears in `review_queue.csv`
- both rows now carry only `weak_evidence`
- neither row carries `monetary_unit_mismatch`

Interpretation:

- they were reclassified as acceptable rate metrics
- they were not silently deleted
- the unit false-positive behavior was genuinely removed

## Period Residual QA

The five prior period residual rows from `盈利预测分业务` were verified as repaired rather than dropped:

- `row 4 / 应急电源`
- `row 5 / 通信指挥系统`
- `row 6 / 军用电源装备`
- `row 7 / 其他业务`
- `row 8 / 合计`

Observed in R2:

- all five rows still exist in `clean_data.csv`
- all five rows still exist in `evidence_index.json`
- none of the five rows appear in `review_queue.csv`
- all five rows retain embedded header context in `period_labels`
- none of the five rows carry `period_context_missing`
- all five rows now carry only `weak_evidence`

Interpretation:

- embedded period headers are now being recognized well enough for this workbook
- the five period false positives were genuinely removed
- the rows were not lost from the output

## Clean-Data Quality Analysis

`clean_data.csv` contains `94` rows.

Verified:

- `STRICT_FINANCIAL_TABLE_ROW = 81`
- `MARKET_REFERENCE_ROW = 13`
- `NARRATIVE_ASSERTION = 0`
- all clean rows have `issue_codes = weak_evidence`
- no unit issue rows in clean data
- no period issue rows in clean data
- no valuation issue rows in clean data
- the 7 repaired residual rows are now represented as clean candidates

Conclusion:

The `94` clean rows are consistent with the intended R4 candidate policy plus the R2 residual fixes.

## Review-Queue Quality Analysis

`review_queue.csv` contains `18` rows.

Verified:

- all 18 rows are `NARRATIVE_ASSERTION`
- all 18 rows are `NARRATIVE_REVIEW`
- all 18 rows carry only `weak_evidence`
- none of the 7 repaired residual rows remain in review queue
- no strict or market clean candidates were duplicated back into review queue

Conclusion:

The review queue is narrower and more diagnostic than R1.
It now contains only narrative review rows for this second workbook.

## Baseline Regression Analysis

Baseline R2 remains stable against the R1/R4-era expectations:

- `row_count_total = 82`
- `fail_count = 0`
- `unit_issue_count = 0`
- `period_issue_count = 2`
- `clean_data_row_count = 75`
- `review_queue_row_count = 7`
- `unknown_row_count = 0`

No visible regression was found in:

- clean-data count
- review-queue count
- row-type distribution
- gate discipline
- external-call discipline

## Gate Discipline Analysis

Both reviewed R2 outputs preserve:

- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`

Both reviewed R2 outputs preserve zero external calls:

- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

## Remaining Risks

- The second sample still remains `AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX` because evidence remains weak-only and narrative rows remain review-only.
- `run_summary.json` is intentionally lightweight and does not duplicate every manifest counter; QA should continue treating manifest plus CSV outputs as the primary verification surface.
- Embedded period extraction is adequate for this workbook family, but future workbooks may still introduce richer mixed-header variants.

## Decision

Primary decision:

`348S_R2_QA_CONFIRMED_RESIDUAL_REFINEMENT_VALID`

## Recommended Next Task

`348F Fixture Harvest from 346B`

Alternative next task if the goal is broader generalization instead of fixture harvest:

`348S Third Workbook Pilot`
