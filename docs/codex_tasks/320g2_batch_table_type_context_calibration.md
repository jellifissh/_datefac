# 320G2 Batch Table-Type Context Calibration

## task_title
Diagnose 320G batch failures and calibrate table-type-specific row-text mapping/context gates

## project
D:\_datefac

## current_context
320G imported 10 manually generated PPStructure outputs and ran the row-text extraction/mapping/delivery benchmark across multiple tables.

Latest 320G result:
- pushed branch: main
- commit hash: 32950d920463e2148a3233e0e23e34e1de181af9
- batch_table_count: 10
- batch_ok_count: 10
- parsed_table_count: 10
- table_with_row_text_count: 10
- table_with_candidates_count: 8
- table_with_trusted_count: 1
- report_count: 9
- trusted_total_count: 10
- review_required_total_count: 129
- rejected_total_count: 0
- trusted_rate: 0.07194244604316546
- provenance_complete_rate: 1.0
- qa_pass_count: 9
- qa_warn_count: 0
- qa_fail_count: 0
- batch_delivery_decision: BATCH_ROW_TEXT_DELIVERY_PARTIAL_NEEDS_CALIBRATION

Top risk tags:
- ROW_TEXT_ONLY: 139
- UNIT_UNKNOWN: 129
- VALUE_CONFLICT: 113
- SMOKE_CHECK_FAILED: 89
- TABLE_TYPE_MISMATCH: 89
- YEAR_INFERRED: 89
- NUMERIC_COUNT_MISMATCH: 64
- ROW_REPAIRED_CONTINUATION: 64
- SMOKE_VERIFIED_ROW: 50

Engineering interpretation:
- 320G did not fail: 10/10 tables were parsed and 8 tables generated candidates.
- But the multi-table trust split is far too conservative/noisy.
- The 320C4 single cash-flow smoke logic appears to be leaking into unrelated table types, producing many `SMOKE_CHECK_FAILED` and `TABLE_TYPE_MISMATCH` tags.
- Unit/year context propagation that worked in 320D2 for one table is not general enough for batch tables.
- `VALUE_CONFLICT` is very high and must be diagnosed before any broader integration.

Do not proceed to 320H yet. 320G2 should diagnose and calibrate batch behavior.

## goal
Implement 320G2 calibration diagnostics and targeted fixes:

1. Identify why 113 `VALUE_CONFLICT` tags are produced.
2. Stop applying the original cash-flow smoke check to non-matching table types.
3. Improve table-title/header unit propagation for income statement, balance sheet, cash flow, and valuation tables.
4. Improve year detection from row/table headers across batch outputs.
5. Produce per-table failure reasons and a calibrated benchmark output.
6. Increase trusted rows where evidence is strong, while keeping ambiguous rows in review.

This is still sandbox-only.

## non_goals
Do not do these in 320G2:
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call cloud APIs, LLMs, VLMs, or network endpoints.
- Do not modify production Excel files.
- Do not apply data into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not claim production readiness.

## expected_new_or_modified_files
Likely modified:
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `tools/run_batch_ppstructure_outputs_320g.py`

Potential new files:
- `datefac/pipeline/table_context_detector.py`
- `datefac/pipeline/batch_conflict_diagnostics.py`
- `datefac/pipeline/table_type_calibration.py`
- `docs/codex_tasks/320g2_batch_table_type_context_calibration.md`

Modify extractor/governance only if necessary:
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/governance/risk_splitter.py`
- `datefac/governance/row_text_candidate_mapper.py`

Keep table-type calibration modular. Do not bury all logic inside the CLI script.

## input_contract
Primary input:

```powershell
E:\mineru_lab\ppstructure_batch_outputs_320f
```

Previous benchmark input/output:

```powershell
D:\_datefac\output\batch_row_text_delivery_320g
```

CLI should support:

```powershell
python tools/run_batch_ppstructure_outputs_320g.py ^
  --ppstructure-batch-dir E:\mineru_lab\ppstructure_batch_outputs_320f ^
  --previous-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\batch_row_text_delivery_320g2
```

If `--previous-benchmark-dir` is not implemented, rerun from batch dir and still produce 320G2 outputs. Preserve backward compatibility where practical.

## diagnostics_required
Add these sheets to the 320G2 output:

### `conflict_diagnostics`
Columns:
- conflict_key
- table_run_id
- report
- table_asset_id
- table_type
- metric_code
- year
- candidate_count
- distinct_values
- values
- source_row_texts
- source_files
- conflict_class
- recommended_action

Conflict classes:
- `DUPLICATE_SAME_ROW`
- `DUPLICATE_SAME_VALUE_COLLAPSIBLE`
- `TRUE_VALUE_CONFLICT`
- `YEAR_ALIGNMENT_CONFLICT`
- `METRIC_ALIAS_COLLISION`
- `CROSS_TABLE_DUPLICATE_FALSE_POSITIVE`
- `UNKNOWN_CONFLICT`

Important: conflict keys must include `table_run_id` or `table_asset_id`. Do not mark the same metric/year from different tables/reports as a conflict just because metric_code/year match. That would be impressively useless, a specialty of bad spreadsheets.

### `table_context_detection`
Columns:
- table_run_id
- table_type
- detected_table_title
- detected_unit
- unit_source
- detected_years
- year_source
- raw_header_rows
- confidence
- warnings

### `table_type_risk_breakdown`
Columns:
- table_type
- table_count
- candidate_count
- trusted_count
- review_required_count
- unit_unknown_count
- year_inferred_count
- value_conflict_count
- smoke_failed_count
- table_type_mismatch_count
- numeric_mismatch_count
- main_failure_reason

### `smoke_check_scope_audit`
Columns:
- table_run_id
- table_type
- smoke_check_applied
- smoke_check_name
- applied_reason
- skipped_reason
- smoke_check_failed_count
- table_type_mismatch_count

Rules:
- The original 320C4 hardcoded cash-flow expected-values smoke check may only apply to the known original sample or a clearly matching table identity.
- For other cash-flow tables, use generic structural checks, not the original exact-value smoke expected values.
- For non-cash-flow tables, do not apply cash-flow smoke expected values.

## calibration_requirements

### 1. Conflict key fix
Conflict detection must be table-scoped:
- report + table_asset_id + metric_code + year
or
- table_run_id + metric_code + year

Do not create global conflicts across different reports/tables.

Same-value duplicate candidates inside one table may be collapsed with tag:
- `DUPLICATE_SAME_VALUE_COLLAPSED`

Different-value duplicates inside one table remain review-required with:
- `VALUE_CONFLICT`

### 2. Smoke check scope fix
Do not use 320C4 exact expected-value smoke check as a universal trust source.

Use statuses:
- `SMOKE_EXACT_SAMPLE_PASSED` only for the known original sample.
- `STRUCTURAL_CHECK_PASSED` for generic multi-table checks.
- `SMOKE_NOT_APPLICABLE_TABLE_TYPE` for unrelated table types.

Generic structural checks:
- valid known metric_code;
- valid year/header source;
- normalized value exists;
- no numeric count mismatch;
- no table-scoped conflict;
- unit known or metric is ratio/unitless.

### 3. Unit context detector
Detect units from table title/header/nearby text/row texts:
- `利润表（百万元）` -> `百万元`
- `资产负债表（百万元）` -> `百万元`
- `现金流量表（百万元）` -> `百万元`
- `盈利预测和财务指标` rows may mix units; be conservative.
- `营业收入（百万元）` row-level unit -> `百万元`
- `每股收益（元）` -> `元`
- percentages -> `%` when raw value contains `%` or metric implies percent.

If table is key financial/valuation and mixed units are detected, row-level unit has priority over table-level unit.

### 4. Year context detector
Detect years from header-like rows:
- 2024, 2025, 2026E, 2027E, 2028E
- 2022, 2023, 2024, 2025, 2026E, etc.
- 2024A / 2025A if present.

If header years are found in the same table, do not tag all candidates `YEAR_INFERRED`.

### 5. Table-type-specific trust gate
Do not let `ROW_TEXT_ONLY` alone block trust. It is recognizer mode, not a fatal flaw.

Trusted preview may be allowed if:
- no table-scoped conflict;
- valid known metric;
- valid year with table/header source;
- normalized value exists;
- unit known or unitless/ratio;
- numeric count match;
- table-type-compatible metric;
- confidence strong enough.

Keep review-required if:
- mixed-unit valuation table and unit is not row-level clear;
- generic `其它` row without section disambiguation;
- repaired continuation but no structural/smoke support;
- true value conflict;
- table type mismatch still present.

## output_contract
Write to:

```powershell
D:\_datefac\output\batch_row_text_delivery_320g2
```

Required files:

1. `batch_row_text_delivery_320g2.xlsx`

Required sheets:
- `summary`
- `table_run_inventory`
- `extracted_row_texts_all`
- `metric_candidates_all`
- `normalized_candidates_all`
- `trusted_preview_all`
- `review_required_preview_all`
- `rejected_preview_all`
- `per_table_summary`
- `per_report_summary`
- `metric_coverage`
- `table_type_performance`
- `risk_tag_counts`
- `provenance_coverage`
- `qa_checks`
- `known_limitations`
- `conflict_diagnostics`
- `table_context_detection`
- `table_type_risk_breakdown`
- `smoke_check_scope_audit`

2. `batch_row_text_delivery_320g2_summary.json`

3. `batch_row_text_delivery_320g2_report.md`

## summary_metrics
Include all 320G metrics plus:
- table_scoped_conflict_count
- global_false_conflict_count
- same_value_duplicate_collapsed_count
- true_value_conflict_count
- smoke_not_applicable_count
- structural_check_passed_count
- table_context_detected_count
- unit_context_detected_count
- year_context_detected_count
- batch_calibration_decision

Expected improvements over 320G:
- VALUE_CONFLICT should drop substantially if conflicts were global false positives.
- UNIT_UNKNOWN should drop for income/cashflow/balance sheet tables with title units.
- YEAR_INFERRED should drop where table headers contain years.
- TABLE_TYPE_MISMATCH and SMOKE_CHECK_FAILED should no longer dominate non-cashflow tables.
- trusted_rate should improve only if diagnostics justify it.

Decision rule:
- If qa_fail_count > 0:
  `BATCH_CALIBRATION_BLOCKED_BY_QA_FAILURE`
- If true_value_conflict_count > 0 but scoped diagnostics are complete:
  `BATCH_CALIBRATION_READY_WITH_REVIEW_CONFLICTS`
- If parsed_table_count >= 8, table_with_trusted_count >= 5, trusted_rate >= 0.35, provenance_complete_rate >= 0.95, and qa_fail_count == 0:
  `BATCH_CALIBRATION_READY_FOR_320H_PIPELINE_PLAN`
- If parsed_table_count >= 8, table_with_candidates_count >= 5, and risk tags are diagnosable:
  `BATCH_CALIBRATION_PARTIAL_NEEDS_RULE_REFINEMENT`
- Otherwise:
  `BATCH_CALIBRATION_NOT_READY`

## validation
Run:

```powershell
python -m py_compile datefac/pipeline/batch_ppstructure_row_text_pipeline.py
python -m py_compile datefac/benchmark/batch_row_text_delivery_benchmark.py
```

If new files are added:

```powershell
python -m py_compile datefac/pipeline/table_context_detector.py
python -m py_compile datefac/pipeline/batch_conflict_diagnostics.py
python -m py_compile datefac/pipeline/table_type_calibration.py
```

Then run:

```powershell
python tools/run_batch_ppstructure_outputs_320g.py ^
  --ppstructure-batch-dir E:\mineru_lab\ppstructure_batch_outputs_320f ^
  --previous-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\batch_row_text_delivery_320g2
```

If the existing CLI does not support `--previous-benchmark-dir`, run equivalent command and report that clearly.

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run PaddleOCR/PPStructure.
3. Do not call cloud APIs, LLMs, VLMs, or network endpoints.
4. Do not modify production delivery files:
   - `01_自动可信核心指标.xlsx`
   - `02_人工复核指标队列.xlsx`
   - `02A_人工年份修正覆盖表.xlsx`
   - `05_核心财务指标标准化.xlsx`
   - `06_最终核心财务指标.xlsx`
5. Do not modify:
   - `data/overrides/02B_ai_repair_override.xlsx`
   - `data/mapping/formal_scope_rules.json`
6. Do not run `factory_core.py`.
7. Do not rewrite old Stage7 pipeline.
8. Do not commit `output/` artifacts.
9. Do not commit anything under `E:\mineru_lab`.
10. Preserve Chinese text as UTF-8. No `????` or replacement characters.

## commit_requirements
After implementation:
1. `git status`
2. only add 320G2 code and this task document;
3. do not add `output/`;
4. do not add `E:\mineru_lab`;
5. do not add unrelated untracked files such as:
   - `fix_307e_reviewed_at.py`
   - `tools/run_stage7a_5pdf_regression_sandbox.py`
   - `tools/update_stage5v_production_06_safe_rows.py`
6. commit message:
   `Calibrate batch row text table contexts`
7. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- parsed_table_count
- table_with_candidates_count
- table_with_trusted_count
- trusted_total_count
- review_required_total_count
- trusted_rate
- unit_unknown_count
- year_inferred_count
- value_conflict_count
- true_value_conflict_count
- table_type_mismatch_count
- smoke_not_applicable_count
- structural_check_passed_count
- provenance_complete_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- batch_calibration_decision
- top risk tags
- skipped/untracked files
