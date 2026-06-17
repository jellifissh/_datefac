# 348S-R3B Third Workbook Zero-Row Intake Follow-up Result

## Task ID

`348S-R3B Third Workbook Zero-Row Intake Follow-up`

## Files Modified

- `datefac_agent/intake/excel_intake.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`

## Zero-Row Root Cause

The workbook was not actually empty.

Root cause:

- the source `.xlsx` worksheet XML files contain real multi-row tabular data
- but their cached worksheet dimension metadata is incorrectly recorded as `A1`
- `openpyxl` read-only mode trusted that undersized dimension and yielded only the first row of each sheet
- the intake logic then treated each sheet as a title-only sheet and produced no auditable rows

This is why R3 removed the crash but still produced:

- `sheet_count = 8`
- `row_count_total = 0`

## Workbook Shape Observations

Observed sheet families:

- one-column section/title first rows:
  - `报告核心信息与投资要点`
  - `核心盈利预测与估值`
  - `公司业务与产品矩阵`
  - `北美AIDC电力供需与技术路径`
  - `行业赛道数据`
  - `分业务盈利预测明细`
  - `可比公司估值对比`
  - `三大财务报表与核心指标`

Observed hidden later tabular content from raw worksheet XML after dimension reset:

- `核心盈利预测与估值` contains 6-column forecast table
- `公司业务与产品矩阵` contains later 5-column rows
- `北美AIDC电力供需与技术路径` contains later 7-column rows
- `行业赛道数据` contains later 7-column rows
- `分业务盈利预测明细` contains later 6-column rows
- `可比公司估值对比` contains later 8-column rows
- `三大财务报表与核心指标` contains later 5-column rows

Why existing intake skipped them:

- `worksheet.iter_rows()` in read-only mode only exposed row 1 because the cached dimension was `A1:A1`
- intake never saw the later header rows or data rows

## Narrow Fix Summary

Added a narrow read-only worksheet safeguard:

- detect worksheets whose cached dimension is exactly `A1:A1`
- call `reset_dimensions()` before iterating rows

This keeps the current intake architecture intact:

- no audit-policy changes
- no broad row-type remapping
- no synthetic rows created
- existing header detection and key-value detection still decide what becomes auditable

## Regression Test Added

Added compact regression tests:

- `test_should_reset_read_only_dimensions_flags_a1_only_dimension`
- `test_should_reset_read_only_dimensions_ignores_normal_dimension`

These protect the new dimension-reset guard without depending on the full local workbook.

## Validation Results

- `python -m py_compile datefac_agent\intake\excel_intake.py tests\agent\test_agent_excel_intake_audit_348a.py`
- `python -m pytest tests\agent -q`
- third workbook runner rerun:
  - `python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf --excel-path D:\_datefac_agent\input\泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348s_r3b_third_taihao_keji_doubaoai`
  - result: completed successfully and generated manifest/output artifacts

## Third Workbook Output Directory

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r3b_third_taihao_keji_doubaoai`

## Third Workbook Manifest Metrics

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

## Top Review Queue Issue Codes

- `weak_evidence = 64`
- `percentage_unit_missing = 10`
- `period_values_missing = 8`
- `monetary_unit_mismatch = 1`
- `valuation_metric_unit_suspicious = 1`

## Row-Count Outcome

`row_count_total` is now nonzero.

Specifically:

- R3: `row_count_total = 0`
- R3B: `row_count_total = 158`

This confirms the zero-row intake blocker was fixed.

## Explainability

The resulting output is explainable at a high level:

- the workbook now surfaces substantial strict-financial content
- clean-data candidates are nonzero (`94`)
- review queue is also substantial (`64`)
- residual risk is now about classification/quality rather than a broken intake entrypoint

The remaining `unknown_row_count = 44` indicates more workbook-shape follow-up may still be needed, but it is no longer a zero-row failure.

## Baseline Regression Notes

This task intentionally does not modify:

- unit semantics
- period alignment
- valuation logic
- review routing policy

The `tests\agent` suite remains the first/second-sample regression surface.

## Boundary Discipline

- changes limited to intake/tests
- no legacy `datefac/` changes
- no `input/` changes
- no output files committed
- no MinerU / LLM / OCR calls
- no PDF re-extraction

## Decision

`348S_R3B_CONFIRMED_ZERO_ROW_INTAKE_FIXED`

## Recommended Next Task

`348S-QA Third Workbook Pilot Review`

Recommended review focus:

- whether `unknown_row_count = 44` is acceptable
- whether the `percentage_unit_missing = 10` rows are true issues or shape artifacts
- whether `period_values_missing = 8` belongs to strict rows only
