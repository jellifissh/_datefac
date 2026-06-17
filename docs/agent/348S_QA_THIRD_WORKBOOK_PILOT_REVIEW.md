# 348S-QA Third Workbook Pilot Review

## Task ID

`348S-QA Third Workbook Pilot Review`

## Reviewed Output Directory

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r3b_third_taihao_keji_doubaoai`

## Manifest Metrics

- `decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX`
- `sheet_count = 8`
- `row_count_total = 158`
- `row_count_audited = 158`
- `pass_count = 0`
- `review_count = 157`
- `fail_count = 1`
- `issue_count_total = 178`
- `unit_issue_count = 11`
- `period_issue_count = 8`
- `valuation_issue_count = 1`
- `evidence_issue_count = 158`
- `strong_evidence_count = 0`
- `weak_evidence_count = 158`
- `missing_evidence_count = 0`
- `strict_financial_table_row_count = 110`
- `market_reference_row_count = 2`
- `narrative_assertion_count = 2`
- `unknown_row_count = 44`
- `clean_data_row_count = 94`
- `review_queue_row_count = 64`
- `internal_clean_candidate_count = 92`
- `internal_reference_candidate_count = 2`
- `narrative_review_count = 2`
- `review_required_count = 61`
- `excluded_from_clean_data_count = 1`

## Clean-Data QA

Conclusion:

- `clean_data_row_count = 94` is clean under the current policy
- no clean row contains blocking issues
- all clean rows contain only `weak_evidence`
- no clean row contains `percentage_unit_missing`
- no clean row contains `period_values_missing`
- no clean row contains `monetary_unit_mismatch`
- no clean row contains `valuation_metric_unit_suspicious`

Composition:

- `STRICT_FINANCIAL_TABLE_ROW = 92`
- `MARKET_REFERENCE_ROW = 2`
- `NARRATIVE_ASSERTION = 0`

Interpretation:

- clean data did not absorb review-only rows
- the current clean-candidate boundary is still working on the third workbook

## Review-Queue QA

Conclusion:

- `review_queue_row_count = 64` is explainable
- review queue is not polluted by clean candidates
- there are `0` `INTERNAL_CLEAN_CANDIDATE` rows in review queue
- there are `0` `INTERNAL_REFERENCE_CANDIDATE` rows in review queue

Candidate-type distribution:

- `REVIEW_REQUIRED = 61`
- `NARRATIVE_REVIEW = 2`
- `EXCLUDED_FROM_CLEAN_DATA = 1`

Row-type distribution:

- `UNKNOWN_ROW = 44`
- `STRICT_FINANCIAL_TABLE_ROW = 18`
- `NARRATIVE_ASSERTION = 2`

Top issue codes:

- `weak_evidence = 64`
- `percentage_unit_missing = 10`
- `period_values_missing = 8`
- `monetary_unit_mismatch = 1`
- `valuation_metric_unit_suspicious = 1`

Interpretation:

- queue volume is high but diagnostic
- current queue is driven mainly by `UNKNOWN_ROW` routing plus a smaller set of strict-row unit/period gaps

## Unknown-Row QA

Conclusion:

- `unknown_row_count = 44` is only partially acceptable
- most unknown rows are understandable workbook-content rows rather than parser garbage
- but the count is too high to treat as a fully generalized third-workbook result

Observed unknown-row families:

- report metadata rows such as report type, target company, institution, publication date
- long thesis or risk narrative lines
- business matrix rows
- North America AIDC comparative table rows
- industry table title or layout rows

Interpretation:

- these rows are not obviously wrong to keep in review
- however, too much of the workbook still falls outside current row typing
- this is the strongest remaining refinement signal

## Unit Issue QA

Conclusion:

- `percentage_unit_missing = 10` appears to be a real current-policy review signal, not an obvious false positive
- all 10 rows are in `分业务盈利预测明细`
- all 10 rows are `STRICT_FINANCIAL_TABLE_ROW`
- affected metrics are:
  - `同比增速`
  - `毛利率`
  - `综合毛利率`
  - `净利润增速`

Interpretation:

- these are rate/percentage-style metrics without an explicit `%` unit hint
- under the current conservative policy, sending them to review is reasonable

`monetary_unit_mismatch = 1`:

- this falls on one `UNKNOWN_ROW` narrative-style sentence:
  - `3. 业绩弹性：2026-2028年归母净利润预计3.6/5.3/6.1亿元，对应PE 34/23/20倍，成长空间持续打开。`

Interpretation:

- it is a real blocker for that row
- but it looks more like a mixed narrative-plus-valuation row problem than a broad strict-table unit-checker defect

## Period Issue QA

Conclusion:

- `period_values_missing = 8` is fully concentrated in `STRICT_FINANCIAL_TABLE_ROW`
- no period-issue row leaked into clean data

Affected rows:

- `核心盈利预测与估值 / row 10 / 市场与基础数据`
- `行业赛道数据 / rows 12, 18, 28, 33`
- `三大财务报表与核心指标 / rows 16, 27, 34`

Interpretation:

- these are mostly table-title or section-anchor rows within strict table regions
- current behavior is conservative and contained

## Valuation Issue QA

Conclusion:

- `valuation_metric_unit_suspicious = 1` is reasonable
- it appears on the same mixed sentence row that also triggered `monetary_unit_mismatch`

Interpretation:

- routing this row to review is appropriate
- this does not suggest a broad valuation-checker defect

## Evidence QA

Conclusion:

- all rows remaining at `WEAK_EVIDENCE` is consistent with the current stage
- `weak_evidence_count = 158`
- `missing_evidence_count = 0`

Interpretation:

- workbook lineage plus source PDF identity exists
- explicit page-level evidence does not exist
- current output remains review-oriented, not delivery-ready

## Gate Discipline

Confirmed:

- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`
- `demo_export_only = true`

## Baseline Validation

- `python -m pytest tests\agent -q` -> passed (`32 passed`)

Residual note:

- pytest emitted one cache warning due to `.pytest_cache` write restriction
- test result itself still passed

## Boundary Discipline

Confirmed:

- source code was not modified in this QA task
- tests were not modified in this QA task
- input files were not modified
- output files were not modified or committed
- legacy `datefac/` was not touched
- MinerU / OCR / LLM / VLM calls = `0`
- no PDF re-extraction was performed

## Decision

`348S_QA_THIRD_WORKBOOK_REVIEW_CONFIRMED_NEEDS_R3C_UNKNOWN_ROW_REFINEMENT`

## Recommended Next Task

`348S-R3C Unknown Row Refinement`

Recommended focus:

- reduce `unknown_row_count = 44`
- split metadata / narrative / industry comparative rows more intentionally
- keep unit / period / routing policy stable unless later QA shows a true checker defect
