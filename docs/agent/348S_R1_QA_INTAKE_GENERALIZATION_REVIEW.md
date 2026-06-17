# 348S-R1-QA Intake Generalization Review

## Task ID

`348S-R1-QA Intake Generalization Review`

## Input/Output Directories Reviewed

Second sample output:

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_h3_ap202605231822706325_1`

Baseline regression output:

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_regression_348a_baseline`

Reviewed files in each directory:

- `agent_excel_intake_audit_348a_manifest.json`
- `agent_excel_intake_audit_348a_run_summary.json`
- `audit_report.md`
- `evidence_index.json`
- `review_queue.csv`
- `clean_data.csv`

## Verified Metrics

### Second sample

- `row_count_total = 112`
- `row_count_audited = 112`
- `pass_count = 0`
- `review_count = 110`
- `fail_count = 2`
- `issue_count_total = 119`
- `unit_issue_count = 2`
- `period_issue_count = 5`
- `valuation_issue_count = 0`
- `evidence_issue_count = 112`
- `strict_financial_table_row_count = 81`
- `market_reference_row_count = 13`
- `narrative_assertion_count = 18`
- `unknown_row_count = 0`
- `clean_data_row_count = 87`
- `review_queue_row_count = 25`
- `internal_clean_candidate_count = 75`
- `internal_reference_candidate_count = 12`
- `narrative_review_count = 18`
- `review_required_count = 5`
- `excluded_from_clean_data_count = 2`
- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`
- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

### Baseline regression

- `row_count_total = 82`
- `row_count_audited = 82`
- `pass_count = 0`
- `review_count = 82`
- `fail_count = 0`
- `issue_count_total = 84`
- `unit_issue_count = 0`
- `period_issue_count = 2`
- `valuation_issue_count = 0`
- `evidence_issue_count = 82`
- `strict_financial_table_row_count = 67`
- `market_reference_row_count = 10`
- `narrative_assertion_count = 5`
- `unknown_row_count = 0`
- `clean_data_row_count = 75`
- `review_queue_row_count = 7`
- `internal_clean_candidate_count = 65`
- `internal_reference_candidate_count = 10`
- `narrative_review_count = 5`
- `review_required_count = 2`
- `excluded_from_clean_data_count = 0`

## Row-Count Delta Analysis

Observed change:

- before R1: `119`
- after R1: `112`
- delta: `-7`

The 7-row difference is credible and appears to come from removal of accidental header/data contamination rather than loss of valid business rows.

Per-sheet change:

- `盈利预测与估值`: `7 -> 6`
- `资产负债表`: `31 -> 30`
- `利润表`: `27 -> 26`
- `现金流量表`: `8 -> 7`
- `重要财务与估值指标`: `8 -> 7`
- `可比公司估值`: `5 -> 4`
- `盈利预测分业务`: `6 -> 5`
- `报告概要`: unchanged at `27`

Interpretation:

- each of the seven structured sheets dropped exactly one row;
- the missing row is the row-3 header-like row such as `项目` / `指标` / `公司` / `业务板块`;
- `报告概要` did not drop rows because it is a key-value summary sheet rather than a structured table with a later header row.

Conclusion:

The `119 -> 112` reduction is acceptable and looks like a genuine intake cleanup, not hidden row loss.

## Row-Type Quality Analysis

Second-sample post-R1 distribution:

- `STRICT_FINANCIAL_TABLE_ROW = 81`
- `MARKET_REFERENCE_ROW = 13`
- `NARRATIVE_ASSERTION = 18`
- `UNKNOWN_ROW = 0`

Quality assessment:

- `UNKNOWN_ROW = 0` is credible for this workbook after R1.
- `报告概要` now splits sensibly:
  - narrative rows such as `报告标题`, `投资评级`, `核心投资逻辑`, `风险提示`
  - market/reference rows such as `收盘价(元)`, `市净率(倍)`, `总市值(百万元)`
- `盈利预测与估值`, `重要财务与估值指标`, and `盈利预测分业务` are now mostly treated as strict rows, which is directionally correct for this workbook.
- `可比公司估值` is now market/reference rather than strict financial, which is correct.

Residual concern:

- `报告概要` still contains mixed summary rows like `2026E PE` and `2026E 归母净利润(亿元)` that are treated as narrative. That is defensible for this pilot, but it means the summary-sheet split is useful rather than perfect.

## Period Issue Quality Analysis

Remaining period issues: `5`

All five appear in `盈利预测分业务` and are currently flagged as `period_context_missing;weak_evidence`.

These do not look like true missing-period cases.

Reason:

- the sheet clearly has period-bearing headers like `2025A收入(亿元)`, `2026E收入(亿元)`, `2027E收入(亿元)`, `2028E收入(亿元)`, and `2026E毛利率(%)`;
- the rows under that sheet have populated values;
- the remaining issue appears to come from period detection not fully normalizing embedded period labels inside richer header strings.

Conclusion:

The remaining `5` period issues are likely false-positive-style residuals, not true business-data defects.

## Unit Issue Quality Analysis

Remaining unit issues: `2`

Observed affected rows:

- `报告概要 / 资产负债率(%,LF)` as `MARKET_REFERENCE_ROW`
- `重要财务与估值指标 / 资产负债率(%)` as `STRICT_FINANCIAL_TABLE_ROW`

These do not look like true monetary-unit mismatches.

They look analogous to the earlier `净资产收益率(%)` class of issue:

- the metric contains a broad monetary-token term such as `资产`;
- the actual metric is a percentage/rate metric;
- the unit checker still treats it as monetary and raises `monetary_unit_mismatch`.

Conclusion:

The remaining `2` unit issues are likely false-positive-style residuals, not true positives.

## Clean-Data Quality Analysis

`clean_data.csv` contains `87` rows.

Observed split:

- `INTERNAL_CLEAN_CANDIDATE = 75`
- `INTERNAL_REFERENCE_CANDIDATE = 12`

Observed row-type split:

- `STRICT_FINANCIAL_TABLE_ROW = 75`
- `MARKET_REFERENCE_ROW = 12`

Observed issue codes in clean data:

- only `weak_evidence`

Verified:

- no `NARRATIVE_ASSERTION` rows in clean data
- no period issue rows in clean data
- no unit issue rows in clean data
- no valuation issue rows in clean data

Conclusion:

The `87` clean rows look genuinely clean under the current pilot policy.

## Review Queue Quality Analysis

`review_queue.csv` contains `25` rows.

Observed split:

- `NARRATIVE_REVIEW = 18`
- `REVIEW_REQUIRED = 5`
- `EXCLUDED_FROM_CLEAN_DATA = 2`

Observed row-type split:

- `NARRATIVE_ASSERTION = 18`
- `STRICT_FINANCIAL_TABLE_ROW = 6`
- `MARKET_REFERENCE_ROW = 1`

Observed issue-code split:

- `weak_evidence = 18`
- `period_context_missing;weak_evidence = 5`
- `monetary_unit_mismatch;weak_evidence = 2`

This queue is rational:

- narrative rows are kept out of clean data;
- period-residual rows are review-required;
- the two residual unit false positives are excluded from clean data.

No internal clean candidates were duplicated into review queue.

## Baseline Regression Analysis

The baseline did not regress in visible ways.

Confirmed:

- `clean_data_row_count` stayed `75`
- `review_queue_row_count` stayed `7`
- `unit_issue_count` stayed `0`
- `unknown_row_count` stayed `0`
- narrative rows did not leak into clean data

Conclusion:

Baseline behavior is stable after R1.

## Gate Discipline Analysis

Both reviewed outputs preserved:

- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`

Both reviewed outputs preserved zero external calls:

- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

## Remaining Risks

- `盈利预测分业务` still needs richer embedded-header period normalization.
- `资产负债率(%)` / `资产负债率(%,LF)` still expose a rate-vs-monetary unit false-positive gap.
- `报告概要` summary splitting is useful, but future summary-sheet variants may still require new row-shape patterns.

## Decision

Primary decision:

`348S_R1_QA_CONFIRMED_PARTIAL_IMPROVEMENT_REMAINING_GAPS`

Supporting decisions:

- `348S_R1_QA_CONFIRMED_INTAKE_GENERALIZATION_IMPROVED`
- `348S_R1_QA_CONFIRMED_NEEDS_UNIT_CHECKER_REFINEMENT`
- `348S_R1_QA_CONFIRMED_NEEDS_PERIOD_RULE_REFINEMENT`

## Recommended Next Task

`348S-R2 Unit/Period Residual Refinement`
