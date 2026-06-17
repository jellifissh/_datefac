# 348S-R3C Unknown Row Refinement Result

## Task ID

`348S-R3C Unknown Row Refinement`

## Files Modified

- `datefac_agent/intake/excel_intake.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`

## Unknown-Row Root Cause

R3B left `unknown_row_count = 44` because the generic row-type classifier had no workbook-specific routing for three third-workbook families:

- report metadata and long thesis/risk narrative rows in `报告核心信息与投资要点`
- business matrix rows in `公司业务与产品矩阵`
- North America AIDC comparative rows and section-anchor rows in `北美AIDC电力供需与技术路径`

These rows were not parser noise. They were structurally readable workbook content, but the generic classifier lacked enough context to map them into an existing review-only row type.

## Unknown-Row Family Audit

R3B unknown-row distribution:

- `报告核心信息与投资要点 = 13`
- `公司业务与产品矩阵 = 6`
- `北美AIDC电力供需与技术路径 = 25`

Family diagnosis:

- report metadata rows such as `报告类型` / `标的公司` / `发布日期` are narrative context, not clean financial data
- long thesis and risk lines are narrative assertions and should remain review-only
- business matrix rows are descriptive business-structure rows with light `%`-style share fields, not strict clean-data candidates
- North America AIDC rows are comparative/reference-style content and section anchors, but under the current clean-candidate policy they are safer as explicitly typed narrative review rows rather than internal reference candidates
- the mixed valuation sentence row must remain review-required / blocked from clean data

## Narrow Fix Summary

Only intake-side row typing was refined.

Changes made:

- added `_refine_third_workbook_row_type(...)` in `datefac_agent/intake/excel_intake.py`
- applied the refinement only when the generic classifier returns `UNKNOWN_ROW`
- mapped all third-workbook rows in `报告核心信息与投资要点` to `NARRATIVE_ASSERTION`
- mapped all third-workbook rows in `公司业务与产品矩阵` to `NARRATIVE_ASSERTION`
- mapped `北美AIDC电力供需与技术路径` section anchors and comparative rows to `NARRATIVE_ASSERTION`

Why the North America AIDC rows were not changed to `MARKET_REFERENCE_ROW`:

- current clean-candidate policy would route weak-evidence market rows into `INTERNAL_REFERENCE_CANDIDATE`
- that would increase clean/reference output volume, which is outside the R3C goal
- R3C was intended to reduce `UNKNOWN_ROW` noise and improve explainability, not widen clean-data acceptance

No checker or policy logic was modified:

- unit checker unchanged
- period checker unchanged
- valuation checker unchanged
- evidence policy unchanged
- clean candidate policy unchanged

## Regression Tests Added

Added compact tests for:

- third-workbook report metadata row -> `NARRATIVE_ASSERTION`
- third-workbook business matrix row -> `NARRATIVE_ASSERTION`
- third-workbook North America AIDC comparative row -> `NARRATIVE_ASSERTION`
- mixed narrative-plus-valuation sentence stays review-only and excluded from clean data

## Validation Results

`python -m py_compile datefac_agent\intake\excel_intake.py tests\agent\test_agent_excel_intake_audit_348a.py`

- passed

`python -m pytest tests\agent -q`

- passed
- result: `36 passed`
- warning only: pytest cache write restriction in workspace

## Third Workbook Output Directory

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r3c_third_taihao_keji_doubaoai`

## Before/After Manifest Metrics

Before R3C:

- `row_count_total = 158`
- `review_queue_row_count = 64`
- `clean_data_row_count = 94`
- `strict_financial_table_row_count = 110`
- `market_reference_row_count = 2`
- `narrative_assertion_count = 2`
- `unknown_row_count = 44`
- `unit_issue_count = 11`
- `period_issue_count = 8`
- `valuation_issue_count = 1`
- `fail_count = 1`

After R3C:

- `row_count_total = 158`
- `review_queue_row_count = 64`
- `clean_data_row_count = 94`
- `strict_financial_table_row_count = 110`
- `market_reference_row_count = 2`
- `narrative_assertion_count = 46`
- `unknown_row_count = 0`
- `unit_issue_count = 11`
- `period_issue_count = 8`
- `valuation_issue_count = 1`
- `fail_count = 1`

## Unknown-Row Count Change

- `unknown_row_count: 44 -> 0`

Interpretation:

- the reduction came from clearer intake-side routing, not from loosening audit standards
- the remaining review volume is still visible in `review_queue.csv`

## Clean-Data QA

Post-R3C clean-data state remains disciplined:

- `clean_data_row_count = 94`
- clean row types remain:
  - `STRICT_FINANCIAL_TABLE_ROW = 92`
  - `MARKET_REFERENCE_ROW = 2`
- clean rows still contain only `weak_evidence`
- no blocking issue leaked into clean data
- R3C did not inflate clean output

## Review-Queue QA

Post-R3C review-queue state remains explainable:

- `review_queue_row_count = 64`
- row-type distribution:
  - `NARRATIVE_ASSERTION = 46`
  - `STRICT_FINANCIAL_TABLE_ROW = 18`
- candidate-type distribution:
  - `NARRATIVE_REVIEW = 45`
  - `REVIEW_REQUIRED = 18`
  - `EXCLUDED_FROM_CLEAN_DATA = 1`
- top issue codes remain:
  - `weak_evidence = 64`
  - `percentage_unit_missing = 10`
  - `period_values_missing = 8`
  - `monetary_unit_mismatch = 1`
  - `valuation_metric_unit_suspicious = 1`

Interpretation:

- unknown-row noise has been converted into explicit narrative review
- the mixed valuation sentence still remains blocked from clean data
- strict-row unit and period review signals are unchanged and still visible

## Boundary Discipline

Confirmed:

- only allowed source files were changed
- no legacy `datefac/` files were touched
- no `input/` files were modified
- output files were generated for validation only and not committed
- MinerU / OCR / LLM / VLM calls remained `0`
- no PDF re-extraction was performed
- readiness gates remain closed:
  - `client_ready = false`
  - `production_ready = false`
  - `formal_client_export_allowed = false`

## Decision

`348S_R3C_CONFIRMED_UNKNOWN_ROW_REFINEMENT_VALID`

## Recommended Next Task

`348S-R3C-QA Third Workbook Unknown-Row Refinement Review`

Secondary follow-up after QA:

- if QA accepts the new narrative routing, next technical refinement should return to the residual strict-row review signals:
  - `percentage_unit_missing = 10`
  - `period_values_missing = 8`
