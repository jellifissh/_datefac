# 348S-R3 Targeted Third Workbook Schema Refinement Result

## Task ID

`348S-R3 Targeted Third Workbook Schema Refinement`

## Files Modified

- `datefac_agent/intake/excel_intake.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`

## Crash Root Cause

The third workbook includes summary-style rows with fewer than two cells, including one-column rows such as:

- `('一、报告基本信息',)`
- `('核心盈利预测与估值（摘要版）',)`

`_find_key_value_start()` iterated through early rows, sliced `values[:2]`, then unconditionally accessed `texts[1]`.
For one-cell rows this produced:

- `IndexError: list index out of range`

## Narrow Fix Summary

The fix is limited to `_find_key_value_start()`:

- if the first-two-cell slice contains fewer than two cells, skip that row
- continue only when two cells exist and both cells are non-empty

This preserves the existing intent:

- empty rows are ignored
- one-cell summary rows no longer crash intake
- real two-column key-value summary rows are still detected
- header-row detection and downstream audit policy remain unchanged

## Regression Test Added

Added one regression test:

- `test_find_key_value_start_ignores_short_summary_rows_without_crashing`

The test reproduces mixed short-row input with:

- one-cell summary rows
- an empty row
- then three valid two-column key-value rows

Expected behavior:

- no crash
- detected key-value start row remains `4`

## Validation Results

- `python -m py_compile datefac_agent\intake\excel_intake.py tests\agent\test_agent_excel_intake_audit_348a.py`
- `python -m pytest tests\agent -q`
- third workbook runner rerun:
  - `python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf --excel-path D:\_datefac_agent\input\泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348s_r3_third_taihao_keji_doubaoai`
  - result: runner completed without `IndexError`

Observed runner outcome after the crash fix:

- manifest generated
- no new exception raised
- `sheet_count = 8`
- `row_count_total = 0`
- `row_count_audited = 0`
- `clean_data_row_count = 0`
- `review_queue_row_count = 0`

This confirms the narrow crash fix worked, but the third workbook still does not produce auditable rows under the current intake assumptions.

## Third Workbook Output Directory

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r3_third_taihao_keji_doubaoai`

## Third Workbook Manifest Metrics

- `decision = AI_EXCEL_INTAKE_AUDIT_348A_READY`
- `sheet_count = 8`
- `row_count_total = 0`
- `row_count_audited = 0`
- `pass_count = 0`
- `review_count = 0`
- `fail_count = 0`
- `issue_count_total = 0`
- `unit_issue_count = 0`
- `period_issue_count = 0`
- `valuation_issue_count = 0`
- `evidence_issue_count = 0`
- `strict_financial_table_row_count = 0`
- `market_reference_row_count = 0`
- `narrative_assertion_count = 0`
- `unknown_row_count = 0`
- `clean_data_row_count = 0`
- `review_queue_row_count = 0`
- `internal_clean_candidate_count = 0`
- `internal_reference_candidate_count = 0`
- `narrative_review_count = 0`
- `review_required_count = 0`
- `excluded_from_clean_data_count = 0`

## Residual Blocker

The original intake crash is fixed, but the workbook is still effectively blocked because the current intake logic produces zero parsed rows for all eight sheets.

This is a distinct follow-up issue from the crash:

- stage: intake interpretation, not exception handling
- current symptom: all sheets look like section-title-only or non-tabular layouts to the current parser
- consequence: runner exits successfully but produces an empty audit artifact set

## Baseline Regression Notes

This task intentionally does not modify:

- unit semantics
- period alignment
- valuation checks
- row-type routing
- clean candidate policy

The existing `tests\agent` suite remains the baseline guardrail for first and second sample behavior.

## Boundary Discipline

- source changes limited to intake plus tests
- no legacy `datefac/` changes
- no `input/` changes
- no output files committed
- no MinerU / LLM / OCR calls
- no PDF re-extraction

## Decision

`348S_R3_CONFIRMED_PARTIAL_FIX_STILL_BLOCKED`

## Recommended Next Task

- `348S-R3B Third Workbook Zero-Row Intake Follow-up`

Focus of the follow-up:

- interpret one-column summary sheets and later tabular content safely
- do not reopen unit / period / routing policy
- treat this as a deeper intake-shape adaptation, not an audit-rule task
