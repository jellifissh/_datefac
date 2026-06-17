# 348S-R1 Intake Schema Generalization Result

## Task ID

`348S-R1 Intake Schema Generalization`

## Problem Statement

The second real workbook could run end-to-end, but the pre-fix result was heavily biased by first-workbook assumptions:

- `row_count_total = 119`
- `unknown_row_count = 53`
- `period_issue_count = 66`
- `clean_data_row_count = 0`
- `review_queue_row_count = 119`

This indicated schema brittleness rather than a runner crash.

## Second Workbook Shape Findings

The second workbook uses a different shape from the first baseline sample.

Key findings:

- `报告概要` is a two-column key-value summary sheet rather than a period-table sheet.
- `盈利预测与估值` uses a title row, a blank row, then a real header row at row 3:
  - `指标 / 2024A / 2025A / 2026E / 2027E / 2028E`
- `资产负债表` / `利润表` / `现金流量表` also place their usable period header row at row 3 rather than row 1.
- `重要财务与估值指标` is a strict financial-style table with period columns, but the sheet name was not included in the original strict-sheet mapping.
- `可比公司估值` is reference/market-like, not a strict financial statement sheet.
- `盈利预测分业务` is a structured forecast table with mixed business rows and period-like columns, and it is closer to a strict table than to narrative text.

These workbook-shape differences explain why the original intake and row-type logic over-produced `UNKNOWN_ROW` and `period_context_missing`.

## Code Changes

Changed files:

- `datefac_agent/intake/excel_intake.py`
- `datefac_agent/audit/row_type_classifier.py`
- `datefac_agent/audit/period_alignment_checker.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`

### Intake changes

- Added header-row detection instead of assuming the first row is always the real header.
- Added two-column key-value sheet support for summary-like sheets such as `报告概要`.
- Generalized period-label extraction to use search semantics rather than exact row-1-only assumptions.

### Row-type changes

- Expanded strict-sheet mapping to include:
  - `盈利预测与估值`
  - `重要财务与估值指标`
  - `盈利预测分业务`
- Expanded market-reference mapping to include:
  - `可比公司估值`
- Expanded narrative mapping to include:
  - `报告概要`
  - `核心摘要`
  - `投资要点`
- Added metric-level fallback hints so summary-sheet rows can split into:
  - `NARRATIVE_ASSERTION`
  - `MARKET_REFERENCE_ROW`

### Period changes

- Generalized detected label formats to include:
  - `FY2026`
  - `2027FY`
  - `2028 Q1`
- Preserved conservative period checking without disabling it.

### Test changes

- Added second-workbook-oriented tests for:
  - generalized period labels
  - summary-sheet row splitting
  - second-workbook strict-financial sheet classification

## Validation

- `python -m py_compile ...` passed
- `python -m pytest tests\agent -q` passed
- pytest result: `25 passed in 0.50s`

## Second Sample Before/After Comparison

### Before R1

- `row_count_total = 119`
- `unknown_row_count = 53`
- `period_issue_count = 66`
- `clean_data_row_count = 0`
- `review_queue_row_count = 119`
- `internal_clean_candidate_count = 0`
- `internal_reference_candidate_count = 0`

### After R1

Output directory:

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_h3_ap202605231822706325_1`

Manifest highlights:

- `decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX`
- `sheet_count = 8`
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

### Improvement summary

- `unknown_row_count`: `53 -> 0`
- `period_issue_count`: `66 -> 5`
- `clean_data_row_count`: `0 -> 87`
- `review_queue_row_count`: `119 -> 25`

This is a strong improvement rather than a marginal patch.

## Second Sample Review Distribution After Fix

Observed review queue split:

- `NARRATIVE_ASSERTION = 18`
- `MARKET_REFERENCE_ROW = 1`
- `STRICT_FINANCIAL_TABLE_ROW = 6`

Observed candidate split in review queue:

- `NARRATIVE_REVIEW = 18`
- `REVIEW_REQUIRED = 5`
- `EXCLUDED_FROM_CLEAN_DATA = 2`

Observed issue-code distribution:

- `weak_evidence = 25`
- `period_context_missing = 5`
- `monetary_unit_mismatch = 2`

Observed clean-data split:

- `INTERNAL_CLEAN_CANDIDATE = 75`
- `INTERNAL_REFERENCE_CANDIDATE = 12`

## Baseline Regression Comparison

Regression output directory:

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r1_regression_348a_baseline`

Regression key metrics:

- `decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX`
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

Regression assessment:

- baseline `unknown_row_count` stayed at `0`
- baseline `clean_data_row_count` stayed at `75`
- baseline `review_queue_row_count` stayed at `7`
- no reintroduced unit false positive was observed in manifest counts

So the second-sample generalization did not produce a visible regression on the first workbook family.

## Remaining Risks

- The second workbook still has `2` unit issues and `5` period issues that may warrant targeted QA.
- `报告概要` currently mixes narrative and market-reference rows successfully, but additional summary-sheet formats may still exist in future workbooks.
- `row_count_total` shifted from `119` to `112` because header/blank-row handling became more selective; this is likely correct, but should be reviewed in the next QA task.

## Decision

Primary decision:

`348S_R1_CONFIRMED_INTAKE_GENERALIZATION_IMPROVED`

## Recommended Next Task

`348S-R1-QA Intake Generalization Review`
