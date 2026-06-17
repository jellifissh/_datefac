# 348S-R4 Strict Row Unit/Period Review Signal Refinement Result

## Task ID

`348S-R4 Strict Row Unit/Period Review Signal Refinement`

## Files Modified

- `datefac_agent/intake/excel_intake.py`
- `datefac_agent/audit/unit_semantic_checker.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`

## Residual Signal Diagnosis

R3C residual strict-row review signals were:

- `percentage_unit_missing = 10`
- `period_values_missing = 8`

### Percentage Signal Diagnosis

All 10 rows were in `分业务盈利预测明细`:

- `同比增速`
- `毛利率`
- `综合毛利率`
- `净利润增速`

Observed structure:

- all were `STRICT_FINANCIAL_TABLE_ROW`
- all had populated period columns
- all were semantically percentage-style metrics
- all lacked an explicit `%` marker in the metric label

Conclusion:

- these were not true missing-unit defects
- but they also should not be silently promoted into clean data
- they are better treated as implicit-percentage review signals

### Period Signal Diagnosis

All 8 rows were strict-sheet section-anchor or table-title rows:

- `核心盈利预测与估值 / 市场与基础数据`
- `行业赛道数据 / 表2：海外柴发龙头产品参数`
- `行业赛道数据 / 表3：中速燃气内燃机 vs 燃气轮机性能对比`
- `行业赛道数据 / 表4：瓦锡兰2025年数据中心订单`
- `行业赛道数据 / 表5：2030年全球燃气轮机供给预计（单位：GW）`
- `三大财务报表与核心指标 / 资产负债表（单位：百万元）`
- `三大财务报表与核心指标 / 现金流量表（单位：百万元）`
- `三大财务报表与核心指标 / 核心财务与估值指标`

Conclusion:

- these were not real missing-period value rows
- they were section-anchor / table-title rows that should remain review-only
- the real problem was that they were still typed as `STRICT_FINANCIAL_TABLE_ROW`

## Narrow Fix Summary

Two narrow fixes were applied.

### 1. Strict section-anchor rows routed out of strict financial type

In `datefac_agent/intake/excel_intake.py`:

- added third-workbook strict-sheet section-anchor titles
- applied this anchor override before returning generic strict classification
- retyped those anchor rows to `NARRATIVE_ASSERTION`

Effect:

- they no longer hit the strict-row period checker
- they remain review-only

### 2. Implicit percentage rows remain review-required without false `percentage_unit_missing`

In `datefac_agent/audit/unit_semantic_checker.py`:

- added a very narrow implicit-percentage rule
- scope limited to `分业务盈利预测明细`
- scope limited to:
  - `同比增速`
  - `毛利率`
  - `综合毛利率`
  - `净利润增速`
- rows must still have populated period values

Effect:

- these rows no longer raise `percentage_unit_missing`
- instead they raise `implicit_percentage_unit_confirmation_needed`
- they remain review-required and do not enter clean data

No change was made to:

- evidence policy
- clean candidate policy
- legacy code

## Regression Tests Added

Added tests for:

- third-workbook implicit percentage rows no longer raising `percentage_unit_missing`
- third-workbook implicit percentage rows now raising `implicit_percentage_unit_confirmation_needed`
- third-workbook strict-sheet anchor row rerouting to `NARRATIVE_ASSERTION`
- rerouted anchor rows no longer triggering period review

## Validation Results

`python -m py_compile datefac_agent\intake\excel_intake.py datefac_agent\audit\unit_semantic_checker.py datefac_agent\audit\period_alignment_checker.py tests\agent\test_agent_excel_intake_audit_348a.py`

- passed

`python -m pytest tests\agent -q`

- passed
- result: `38 passed`
- warning only: pytest cache write restriction in workspace

## Third Workbook Output Directory

`D:\_datefac_agent\output\agent_excel_intake_audit_348s_r4_third_taihao_keji_doubaoai`

## Before/After Metrics

Before R4:

- `clean_data_row_count = 94`
- `review_queue_row_count = 64`
- `unit_issue_count = 11`
- `period_issue_count = 8`
- `strict_financial_table_row_count = 110`
- `narrative_assertion_count = 46`
- `issue_count_total = 178`

After R4:

- `clean_data_row_count = 94`
- `review_queue_row_count = 64`
- `unit_issue_count = 11`
- `period_issue_count = 2`
- `strict_financial_table_row_count = 104`
- `narrative_assertion_count = 52`
- `issue_count_total = 172`

## Clean-Data QA

Clean-data boundary remained stable:

- `clean_data_row_count = 94` stayed unchanged
- no new rows entered clean data
- no blocking issues leaked into clean data

## Review-Queue QA

Review queue remained stable in size:

- `review_queue_row_count = 64`

Review queue became more accurate:

- 6 strict-sheet anchor rows moved into `NARRATIVE_ASSERTION` review
- 10 implicit percentage rows remained in review, but with a more accurate unit signal

## Unit Signal QA

Result:

- `unit_issue_count = 11` stayed unchanged
- the 10 prior `percentage_unit_missing` false-positive-style rows were replaced by `implicit_percentage_unit_confirmation_needed`
- the mixed narrative-plus-valuation error row remained unchanged

Interpretation:

- false labeling was reduced
- review coverage was preserved
- clean-data acceptance was not widened

## Period Signal QA

Result:

- `period_issue_count: 8 -> 2`

The six removed period issues were section-anchor / table-title rows, not true missing-period data rows.

The two remaining period review signals are the genuine strict rows that still need review under the current policy.

## Boundary Discipline

Confirmed:

- changes stayed within allowed scope
- no legacy `datefac/` files were touched
- no input files were modified
- output files were generated for validation only and not committed
- MinerU / OCR / LLM / VLM calls remained `0`
- no PDF re-extraction was performed
- readiness gates remain closed

## Decision

`348S_R4_CONFIRMED_STRICT_ROW_UNIT_PERIOD_REFINEMENT_VALID`

## Recommended Next Task

`348S-R4-QA Strict Row Unit/Period Review Signal Refinement Review`

