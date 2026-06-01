# 321B2 Pure VLM Mapping Calibration

## task_title
Calibrate pure-VLM table mapping before manual VLM ingestion adapter

## project
D:\_datefac

## current_context
The user generated a pure image-only VLM sample set and ran 321A/321B on it.

Pure VLM input:

```powershell
E:\mineru_lab\vlm_table_outputs_321d_pure_vlm
```

321A quality output:

```powershell
D:\_datefac\output\vlm_output_quality_321d_pure_vlm
```

321A pure VLM result:
- vlm_folder_count: 10
- parsed_json_count: 10
- table_ready_count: 7
- corrupted_label_rate: 0.0110
- numeric_parse_success_rate: 0.9954
- global_vlm_quality_decision: VLM_OUTPUT_READY_FOR_321B_MAPPING_BENCHMARK

321B pure VLM mapping output:

```powershell
D:\_datefac\output\vlm_mapping_benchmark_321d_pure_vlm
```

321B pure VLM mapping result:
- vlm_folder_count: 10
- parsed_json_count: 10
- table_ready_count: 7
- mapped_table_count: 10
- table_with_candidates_count: 10
- table_with_trusted_count: 5
- total_candidate_count: 897
- trusted_total_count: 219
- review_required_total_count: 678
- rejected_total_count: 0
- trusted_rate: 0.24414715719063546
- unique_metric_count: 53
- unique_year_count: 23
- unique_report_count: 10
- unit_unknown_count: 316
- year_inferred_count: 0
- conflict_count: 37
- corrupted_label_candidate_count: 0
- provenance_complete_rate: 1.0
- qa_pass_count: 8
- qa_warn_count: 0
- qa_fail_count: 0
- ppstructure_comparison_available: true
- vlm_benchmark_decision: VLM_MAPPING_PARTIAL_NEEDS_ALIAS_OR_SCHEMA_CALIBRATION

Top risk tags:
- UNKNOWN_METRIC_CODE: 435
- UNREADABLE_LABEL: 417
- UNIT_UNKNOWN: 316
- TABLE_NOT_READY_321A: 227
- VALUE_CONFLICT: 130
- INVALID_YEAR: 65
- SCHEMA_REVIEW_REQUIRED: 41
- VALUE_MISSING: 26
- VALUE_PARSE_FAILED: 12

Engineering interpretation:
- Pure VLM is usable, but it is much weaker than MinerU-assisted VLM output on the same general route.
- The issue is not Chinese corruption anymore: corrupted_label_candidate_count is 0 and provenance is complete.
- The blockers are mapping calibration, unreadable/null labels, unit propagation, invalid year normalization, and conflict diagnostics.
- Do not proceed to 321D ingestion adapter yet. First calibrate 321B pure-VLM mapping output to reduce false review burden and make the benchmark interpretable.

Important distinction:
- `E:\mineru_lab\vlm_table_outputs_321d_pure_vlm` must remain tagged as pure VLM image-only output.
- Do not mix it with MinerU-assisted outputs.
- Do not use MinerU table_body/table_caption to repair this benchmark.

## goal
Implement 321B2 as a sandbox-only calibration and diagnostic stage for pure-VLM mapping.

321B2 should:
1. diagnose why pure VLM produced 435 UNKNOWN_METRIC_CODE and 417 UNREADABLE_LABEL tags;
2. reduce false review burden by collapsing unreadable-label cell-level noise into table/row-level review items;
3. improve unit propagation for financial statement tables;
4. normalize valid year-like columns and isolate truly invalid columns;
5. scope conflicts correctly by table/sample/metric/year;
6. add top unknown label diagnostics for alias expansion;
7. produce a calibrated mapping benchmark output and clear go/no-go decision for 321D.

This is not production integration.

## non_goals
Do not do these in 321B2:
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call VLM/API/cloud/network.
- Do not read or use MinerU table_body/table_caption/content_list to repair pure VLM outputs.
- Do not modify production Excel files.
- Do not apply data into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not claim production readiness.

## expected_new_or_modified_files
Likely modified:
- `datefac/vlm/vlm_candidate_mapper.py`
- `datefac/vlm/vlm_mapping_benchmark.py`
- `datefac/vlm/vlm_delivery_builder.py`
- `tools/run_vlm_mapping_benchmark_321b.py`

Suggested new files if cleaner:
- `datefac/vlm/vlm_mapping_calibration.py`
- `datefac/vlm/vlm_mapping_diagnostics.py`
- `docs/codex_tasks/321b2_pure_vlm_mapping_calibration.md`

Keep this inside the VLM module. Do not touch PPStructure pipeline or old 320G2 experimental files.

## input_contract
Primary inputs:

```powershell
E:\mineru_lab\vlm_table_outputs_321d_pure_vlm
D:\_datefac\output\vlm_output_quality_321d_pure_vlm
D:\_datefac\output\vlm_mapping_benchmark_321d_pure_vlm
```

Optional comparison:

```powershell
D:\_datefac\output\batch_row_text_delivery_320g
```

CLI should support either a new tool:

```powershell
python tools/run_vlm_mapping_calibration_321b2.py ^
  --vlm-output-root E:\mineru_lab\vlm_table_outputs_321d_pure_vlm ^
  --quality-dir D:\_datefac\output\vlm_output_quality_321d_pure_vlm ^
  --previous-mapping-dir D:\_datefac\output\vlm_mapping_benchmark_321d_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
```

Or extend the existing 321B runner with a calibration mode. Prefer a new CLI if it keeps risk lower.

If previous mapping dir is missing, rerun from VLM outputs and quality dir, then produce calibration output.

## diagnostics_required
Add these sheets/files to the output.

### `unknown_metric_diagnostics`
Columns:
- table_id
- table_folder
- table_title
- row_index
- raw_metric_name
- metric_name_cn
- normalized_label
- candidate_count_generated
- years_or_columns
- risk_tags
- suggested_alias
- suggested_metric_family
- suggested_action

Suggested actions:
- `add_alias`
- `keep_review_required`
- `ignore_group_header`
- `unsupported_segment_row`
- `unreadable_label_rerun_vlm`

### `unreadable_label_diagnostics`
Columns:
- table_id
- row_index
- row_label_raw
- affected_cell_count
- values_preview
- table_ready_321a
- image_source_path
- recommended_action

Rule:
- If a row label is null/unreadable, do not create one review-required candidate for every cell unless useful.
- Create a row-level review item, or keep cells in a separate audit sheet, to avoid inflating review_required_total_count.

### `unit_propagation_audit`
Columns:
- table_id
- table_title
- table_unit
- row_label
- metric_code
- old_unit
- new_unit
- unit_source
- action

Rules:
- For cash flow, income statement, and balance sheet tables with clear table unit, propagate table unit to monetary rows.
- For valuation/key metrics, row-level or metric-implied unit has priority.
- Do not assign monetary unit to ratio metrics such as P/E, P/B, EV/EBITDA, ROE, margin, growth.

### `year_normalization_audit`
Columns:
- table_id
- raw_column
- normalized_year
- valid_year
- action
- reason

Rules:
- Accept: 2024, 2025, 2026E, 2027E, 2028E, 2024A, 2025A, and similar year-like labels.
- Strip whitespace/newlines/colon artifacts.
- Reject non-year columns instead of turning them into metric candidates.

### `conflict_diagnostics`
Columns:
- table_id
- metric_code
- year
- candidate_count
- distinct_values
- values
- source_rows
- conflict_class
- recommended_action

Conflict classes:
- `DUPLICATE_SAME_VALUE_COLLAPSIBLE`
- `TRUE_VALUE_CONFLICT`
- `METRIC_ALIAS_COLLISION`
- `NON_YEAR_COLUMN_COLLISION`
- `UNKNOWN_CONFLICT`

Conflict keys must be table-scoped:
- table_id + metric_code + year

Do not create global conflicts across different tables.

## calibration_requirements

### 1. Do not let table-not-ready rows flood candidate counts
If a table failed 321A due to schema invalid/hierarchical structure, keep it in mapping inventory and review queue, but do not allow it to flood candidate-level review with hundreds of low-value rows.

Expected:
- TABLE_NOT_READY_321A candidate count should drop or be separated into table-level review.
- schema-invalid segment tables remain review-required/unsupported, not trusted.

### 2. Unreadable label collapse
If raw_metric_name / metric_name_cn is null, empty, `?`, `????`, or explicitly unreadable:
- do not map to UNKNOWN_METRIC_CODE per cell by default;
- create row-level review/audit entry;
- if values are present, preserve them in `unreadable_label_diagnostics` for manual review.

This should reduce UNKNOWN_METRIC_CODE and UNREADABLE_LABEL inflated counts.

### 3. Alias diagnostics before blind alias expansion
Do not blindly trust new aliases. Add safe aliases only for obvious core financial labels.

Safe alias expansions may include common variants found in VLM outputs:
- 经营现金流 / 经营活动现金流量 / 经营活动现金流
- 现金及现金等价物净增加额 / 现金净增加额 / 现金净变动
- 归母净利润 / 归属于母公司净利润
- 营业总收入 / 营业收入
- 净利润增长 / 净利润增长率
- 资产总额 / 资产总计
- 所有者权益 / 股东权益

Unknown labels from segment/business tables should usually remain review or unsupported.

### 4. Unit propagation
Reduce unit_unknown_count where table title/unit clearly provides context.

Target:
- unit_unknown_count should drop substantially from 316.
- percentage/ratio rows should not receive monetary units.

### 5. Year normalization
Reduce INVALID_YEAR where raw columns are year-like with suffixes or whitespace.

Do not infer years from sequence if columns are not year-like.

### 6. Trust gate calibration
Trusted allowed only if:
- table passed 321A or was explicitly schema-compatible;
- known metric code;
- valid year;
- normalized value exists;
- no unreadable/corrupted label;
- no table-scoped conflict;
- unit known or safely unitless/ratio/per-share;
- row/value not uncertain.

Review required if:
- unknown metric label;
- unreadable row label;
- table not ready in 321A;
- schema invalid/hierarchical table;
- unit unknown for monetary metrics;
- true conflict;
- invalid year.

## output_contract
Write to:

```powershell
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
```

Required files:

1. `vlm_mapping_calibration_321b2.xlsx`

Sheets:
- `summary`
- `vlm_table_inventory`
- `vlm_rows_normalized`
- `metric_candidates_all`
- `trusted_preview`
- `review_required_preview`
- `rejected_preview`
- `per_table_summary`
- `metric_coverage`
- `unit_year_context_summary`
- `risk_tag_counts`
- `provenance_coverage`
- `qa_checks`
- `unknown_metric_diagnostics`
- `unreadable_label_diagnostics`
- `unit_propagation_audit`
- `year_normalization_audit`
- `conflict_diagnostics`
- `known_limitations`

2. `vlm_mapping_calibration_321b2_summary.json`

3. `vlm_mapping_calibration_321b2_report.md`

Optional:
- `trusted_preview.jsonl`
- `review_required_preview.jsonl`
- `unknown_metric_diagnostics.jsonl`

## summary_metrics
Include previous 321B metrics plus:
- calibrated_total_candidate_count
- calibrated_trusted_total_count
- calibrated_review_required_total_count
- calibrated_trusted_rate
- unknown_metric_code_count
- unreadable_label_count
- unit_unknown_count
- invalid_year_count
- table_not_ready_candidate_count
- table_level_review_count
- unreadable_label_row_review_count
- same_value_duplicate_collapsed_count
- true_value_conflict_count
- alias_added_count
- unit_propagated_count
- year_normalized_count
- calibration_decision

Expected improvements over 321B pure VLM:
- UNKNOWN_METRIC_CODE should drop from 435 if unreadable rows are no longer cell-expanded.
- UNREADABLE_LABEL should drop from 417 if row-level review is used.
- UNIT_UNKNOWN should drop from 316 where table units are clear.
- INVALID_YEAR should drop from 65 if year normalization is working.
- trusted_rate may improve, but do not force it.

Decision rule:
- If qa_fail_count > 0:
  `PURE_VLM_CALIBRATION_BLOCKED_BY_QA_FAILURE`
- If corrupted_label_candidate_count > 0:
  `PURE_VLM_CALIBRATION_BLOCKED_BY_LABEL_CORRUPTION`
- If calibrated_trusted_rate >= 0.45, table_with_trusted_count >= 6, provenance_complete_rate >= 0.95, and qa_fail_count == 0:
  `PURE_VLM_CALIBRATION_READY_FOR_321D_MANUAL_INGESTION`
- If calibrated_trusted_rate >= 0.25 and diagnostics are complete:
  `PURE_VLM_CALIBRATION_PARTIAL_NEEDS_MORE_PROMPT_OR_ALIAS_WORK`
- Otherwise:
  `PURE_VLM_CALIBRATION_NOT_READY`

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run PaddleOCR/PPStructure.
3. Do not call AI/VLM/cloud/network APIs.
4. Do not read MinerU table_body/table_caption/content_list to repair pure VLM outputs.
5. Do not modify production delivery files.
6. Do not modify `data/overrides/02B_ai_repair_override.xlsx`.
7. Do not modify `data/mapping/formal_scope_rules.json`.
8. Do not run `factory_core.py`.
9. Do not rewrite old Stage7 pipeline.
10. Do not commit `output/` artifacts.
11. Do not commit anything under `E:\mineru_lab`.
12. Do not commit unrelated 320G2 experimental files.
13. Preserve Chinese text as UTF-8.

## validation
Run relevant compile checks, for example:

```powershell
python -m py_compile datefac/vlm/vlm_candidate_mapper.py
python -m py_compile datefac/vlm/vlm_mapping_benchmark.py
python -m py_compile datefac/vlm/vlm_delivery_builder.py
```

If new files are added:

```powershell
python -m py_compile datefac/vlm/vlm_mapping_calibration.py
python -m py_compile datefac/vlm/vlm_mapping_diagnostics.py
python -m py_compile tools/run_vlm_mapping_calibration_321b2.py
```

Then run:

```powershell
python tools/run_vlm_mapping_calibration_321b2.py ^
  --vlm-output-root E:\mineru_lab\vlm_table_outputs_321d_pure_vlm ^
  --quality-dir D:\_datefac\output\vlm_output_quality_321d_pure_vlm ^
  --previous-mapping-dir D:\_datefac\output\vlm_mapping_benchmark_321d_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
```

If using an extended existing runner instead, report the equivalent command clearly.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 321B2 code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated files such as 320G2 leftovers or temp scripts;
5. commit message:
   `Calibrate pure VLM mapping diagnostics`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- calibrated_total_candidate_count
- calibrated_trusted_total_count
- calibrated_review_required_total_count
- calibrated_trusted_rate
- table_with_trusted_count
- unknown_metric_code_count
- unreadable_label_count
- unit_unknown_count
- invalid_year_count
- table_not_ready_candidate_count
- table_level_review_count
- unreadable_label_row_review_count
- same_value_duplicate_collapsed_count
- true_value_conflict_count
- alias_added_count
- unit_propagated_count
- year_normalized_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- calibration_decision
- top risk tags
- skipped/untracked files
