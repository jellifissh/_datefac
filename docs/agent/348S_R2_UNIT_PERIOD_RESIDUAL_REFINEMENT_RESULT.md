# 348S-R2 Unit/Period Residual Refinement Result

## Task ID

`348S-R2 Unit/Period Residual Refinement`

## Problem Statement

`348S-R1-QA` confirmed 7 residual false-positive-style rows in the second real workbook:

- 2 unit issues on `资产负债率(%)` / `资产负债率(%,LF)`
- 5 period issues on `盈利预测分业务`

This task only refined those residuals without broad intake refactor or clean-policy changes.

## Residual Rows Inspected

Inspected from:

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_h3_ap202605231822706325_1\review_queue.csv`

Reviewed residual rows:

- `报告概要 / row 15 / 资产负债率(%,LF) / MARKET_REFERENCE_ROW / monetary_unit_mismatch;weak_evidence`
- `重要财务与估值指标 / row 8 / 资产负债率(%) / STRICT_FINANCIAL_TABLE_ROW / monetary_unit_mismatch;weak_evidence`
- `盈利预测分业务 / rows 4-8 / 应急电源, 通信指挥系统, 军用电源装备, 其他业务, 合计 / period_context_missing;weak_evidence`

The five period rows carried embedded header labels:

- `2025A收入(亿元)`
- `2026E收入(亿元)`
- `2027E收入(亿元)`
- `2028E收入(亿元)`
- `2026E毛利率(%)`

## Code Changes

Changed files:

- `datefac_agent/audit/unit_semantic_checker.py`
- `datefac_agent/audit/period_alignment_checker.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`

### Unit checker refinement

- Added narrow rate overrides for `资产负债率` / `负债率`.
- Preserved existing monetary-term behavior for true amount metrics such as `资产总计(%)` and `负债合计(%)`.
- Did not remove `资产` / `负债` from global money terms.

### Period detection refinement

- Added embedded period extraction for labels that contain period prefixes inside richer headers.
- Normalized cases such as:
  - `2025A收入(亿元)` -> `2025A`
  - `2026E收入(亿元)` -> `2026E`
  - `2027E收入(亿元)` -> `2027E`
  - `2028E收入(亿元)` -> `2028E`
  - `2026E毛利率(%)` -> `2026E`
- Kept period checking enabled for truly periodless strict financial rows.

### Test additions

Added focused coverage for:

- `资产负债率(%)` no longer triggering `monetary_unit_mismatch`
- `资产负债率(%,LF)` no longer triggering `monetary_unit_mismatch`
- `资产总计(%)` still triggering `monetary_unit_mismatch`
- `负债合计(%)` still triggering `monetary_unit_mismatch`
- embedded period header detection for `2025A/2026E/2027E/2028E`
- truly periodless strict financial rows still triggering `period_context_missing`

## Test Results

- `python -m py_compile datefac_agent\audit\unit_semantic_checker.py datefac_agent\audit\period_alignment_checker.py datefac_agent\intake\excel_intake.py tests\agent\test_agent_excel_intake_audit_348a.py` -> passed
- `python -m pytest tests\agent -q` -> passed (`26 passed`)

## Second Sample Before/After Comparison

Before R2, from R1:

- `row_count_total = 112`
- `fail_count = 2`
- `unit_issue_count = 2`
- `period_issue_count = 5`
- `clean_data_row_count = 87`
- `review_queue_row_count = 25`

After R2:

Output directory:

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r2_h3_ap202605231822706325_1`

Manifest highlights:

- `decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX`
- `row_count_total = 112`
- `fail_count = 0`
- `unit_issue_count = 0`
- `period_issue_count = 0`
- `clean_data_row_count = 94`
- `review_queue_row_count = 18`
- `strict_financial_table_row_count = 81`
- `market_reference_row_count = 13`
- `narrative_assertion_count = 18`
- `unknown_row_count = 0`

Improvement summary:

- `unit_issue_count: 2 -> 0`
- `period_issue_count: 5 -> 0`
- `fail_count: 2 -> 0`
- `clean_data_row_count: 87 -> 94`
- `review_queue_row_count: 25 -> 18`

The drop in review queue count matches removal of the 7 inspected residual rows.

## Baseline Regression Comparison

Regression output directory:

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r2_regression_348a_baseline`

Manifest highlights:

- `decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX`
- `row_count_total = 82`
- `fail_count = 0`
- `unit_issue_count = 0`
- `period_issue_count = 2`
- `clean_data_row_count = 75`
- `review_queue_row_count = 7`
- `strict_financial_table_row_count = 67`
- `market_reference_row_count = 10`
- `narrative_assertion_count = 5`
- `unknown_row_count = 0`

Assessment:

- no visible regression in baseline counts
- unit checker stayed at `0`
- period checker stayed at `2`
- clean-data and review-queue counts stayed stable

## Remaining Risks

- The second sample still remains `AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX` because all rows are still weak-evidence based and narrative rows remain review-only.
- Embedded period extraction is now adequate for this workbook pattern, but future workbooks may introduce more complex mixed headers.
- This task did not broaden clean candidate policy or summary-sheet semantics.

## Decision

Primary decision:

`348S_R2_CONFIRMED_RESIDUAL_FALSE_POSITIVES_REDUCED`

## Recommended Next Task

`348S-R2-QA Unit/Period Residual Refinement Review`
