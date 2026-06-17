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

- `clean_data_row_count = 94` is materially credible for the current policy
- clean data is not contaminated by blocking issues
- all 94 clean rows carry only `weak_evidence`
- no clean row carries `percentage_unit_missing`
- no clean row carries `period_values_missing`
- no clean row carries `monetary_unit_mismatch`
- no clean row carries `valuation_metric_unit_suspicious`

Composition:

- `STRICT_FINANCIAL_TABLE_ROW = 92`
- `MARKET_REFERENCE_ROW = 2`
- `NARRATIVE_ASSERTION = 0`

Interpretation:

- current clean-data policy is still holding its intended boundary
- the third workbook did not leak review-only rows into clean output

## Review-Queue QA

Conclusion:

- `review_queue_row_count = 64` is explainable
- review queue is not polluted by clean candidates
- `clean_candidate_type` in review queue is only:
  - `REVIEW_REQUIRED = 61`
  - `NARRATIVE_REVIEW = 2`
  - `EXCLUDED_FROM_CLEAN_DATA = 1`
- there are `0` `INTERNAL_CLEAN_CANDIDATE` rows in review queue
- there are `0` `INTERNAL_REFERENCE_CANDIDATE` rows in review queue

Top issue codes:

- `weak_evidence = 64`
- `percentage_unit_missing = 10`
- `period_values_missing = 8`
- `monetary_unit_mismatch = 1`
- `valuation_metric_unit_suspicious = 1`

Interpretation:

- the queue is still review-heavy, but it is diagnostically meaningful rather than structurally noisy
- most queue volume is driven by unknown-row routing plus current weak-evidence policy

## Unknown-Row QA

Conclusion:

- `unknown_row_count = 44` is only partially reasonable
- most unknown rows are understandable as metadata, narrative bullet, industry table title, or non-standard comparative layout rows
- but `44` is too large to call fully acceptable if the goal is stronger third-workbook generalization

Observed unknown-row families:

- report metadata rows such as report type, target company, institution, publication date
- long investment thesis / risk text rows
- business matrix rows
- North America AIDC power-supply comparative rows
- industry table title rows and layout rows

Interpretation:

- these are not random parsing failures
- however, a material share of the workbook remains outside current row typing
- this supports a targeted follow-up on unknown-row refinement rather than unit/period policy first

## Unit Issue QA

Conclusion:

- `percentage_unit_missing = 10` looks mostly like true current-policy issues, not obvious false positives
- all 10 such rows are concentrated in `分业务盈利预测明细`
- all 10 are `STRICT_FINANCIAL_TABLE_ROW`
- affected metrics are:
  - `同比增速`
  - `毛利率`
  - `综合毛利率`
  - `净利润增速`

Interpretation:

- these are percentage/rate-style metrics without an explicit `%` unit hint
- under current unit policy, sending them to review is conservative and reasonable
- this does not look like the same kind of false positive as the earlier ROE / debt-ratio issues

`monetary_unit_mismatch = 1`:

- this appears on one `UNKNOWN_ROW` narrative-style sentence:
  - `3. 业绩弹性：2026-2028年归母净利润预计3.6/5.3/6.1亿元，对应PE 34/23/20倍，成长空间持续打开。`
- it is bundled with `valuation_metric_unit_suspicious`
- because the row is still `UNKNOWN_ROW` and sentence-like, this is not the strongest evidence of a pure unit-checker blocker

Interpretation:

- it is a real review blocker for this row
- but it is better understood as a mixed narrative-plus-valuation sentence routing problem than a core strict-table unit defect

## Period Issue QA

Conclusion:

- `period_values_missing = 8` is fully concentrated in `STRICT_FINANCIAL_TABLE_ROW`
- no period issue appears in clean data

Affected rows:

- `核心盈利预测与估值 / row 10 / 市场与基础数据`
- `行业赛道数据 / rows 12, 18, 28, 33`
- `三大财务报表与核心指标 / rows 16, 27, 34`

Interpretation:

- these are mostly table-title or section-anchor rows inside strict financial / industry tables
- current behavior is conservative and explainable
- the issue is not dispersed into narrative or market-reference rows

## Valuation Issue QA

Conclusion:

- `valuation_metric_unit_suspicious = 1` is reasonable under current policy
- it hits the same mixed narrative row that also triggered `monetary_unit_mismatch`
- the sentence combines profit forecast amounts with `PE` multiples in one free-text row

Interpretation:

- routing this to review is appropriate
- this does not currently indicate a broad valuation-checker defect

## Evidence QA

Conclusion:

- all rows remaining at `WEAK_EVIDENCE` is consistent with the current stage and current policy
- `weak_evidence_count = 158`
- `missing_evidence_count = 0`

Interpretation:

- workbook lineage plus source PDF identity exists for all rows
- no explicit page/evidence reference exists, so strong evidence is not expected
- current output remains review-oriented rather than delivery-ready

## Gate Discipline

Confirmed:

- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`
- `demo_export_only = true`

The third workbook output does not justify changing any gate.

## Baseline Validation

- `python -m pytest tests\agent -q` -> passed (`32 passed`)

Residual note:

- pytest emitted one cache warning due to local write restriction on `.pytest_cache`
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
- keep unit / period / routing policy stable unless QA evidence later shows a true checker defect
