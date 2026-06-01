# 321D2 MinerU Body Normalization Calibration

## task_title
Calibrate MinerU table-body normalization, aliases, year/header filtering, and review inflation before route comparison

## project
D:\_datefac

## current_context
321D MinerU table-body ingestion has completed and pushed to `main`.

Latest 321D result:
- pushed branch: main
- commit hash: b1a4005
- output: `D:\_datefac\output\mineru_table_body_ingestion_321d`
- selected_table_count: 20
- attempted_table_count: 20
- table_body_found_count: 20
- table_body_missing_count: 0
- parsed_table_count: 20
- unified_table_count: 20
- table_with_candidates_count: 20
- table_with_trusted_count: 14
- total_candidate_count: 1375
- trusted_total_count: 527
- review_required_total_count: 713
- rejected_total_count: 135
- trusted_rate: 0.38327272727272726
- unit_unknown_count: 0
- year_invalid_count: 156
- unknown_metric_code_count: 802
- conflict_count: 0
- provenance_complete_rate: 1.0
- qa_pass_count: 10
- qa_warn_count: 0
- qa_fail_count: 0
- pure_vlm_calibrated_trusted_rate: 0.3361963190184049
- ppstructure_trusted_rate: 0.07194244604316546
- mineru_body_ingestion_decision: MINERU_BODY_INGESTION_PARTIAL_NEEDS_NORMALIZATION_CALIBRATION

Top risk tags:
- UNKNOWN_METRIC_CODE: 802
- INVALID_YEAR: 156
- NO_YEAR_COLUMNS: 135
- VALUE_PARSE_FAILED: 69
- ROW_LABEL_MISSING: 24

Important positive checks:
- table_body_found_count = 20/20, so MinerU table-body coverage is strong for the selected worklist.
- parsed_table_count = 20/20, so table body extraction is not the bottleneck.
- table_with_trusted_count = 14/20, stronger than pure VLM 321B2 and much stronger than PPStructure 320G.
- unit_unknown_count = 0, so unit propagation worked better than pure VLM.
- conflict_count = 0.
- trusted_year_invalid_count = 0.
- trusted_unknown_metric_code_count = 0.

Engineering interpretation:
- 321D succeeded as a first ingestion proof, but the normalizer/mapping layer is too noisy.
- The main problems are not parser coverage. The problems are:
  1. candidate inflation from unknown rows;
  2. non-year columns being converted into invalid-year candidates;
  3. incomplete alias coverage for forecast/valuation/balance-sheet rows;
  4. row labels/group headers being treated as metric rows;
  5. value parse failures from decorative text, dashes, footnotes, or nested cells.
- Do not jump to 321E route comparison yet. First calibrate 321D output so route comparison is meaningful.

## goal
Implement 321D2 sandbox calibration for MinerU table-body ingestion.

321D2 should:
1. diagnose unknown metric rows and propose safe alias expansions;
2. reduce candidate inflation from group headers / non-metric rows;
3. fix year/header normalization so non-year columns are not candidate years;
4. reduce `INVALID_YEAR`, `NO_YEAR_COLUMNS`, `VALUE_PARSE_FAILED`, and `UNKNOWN_METRIC_CODE` where safely possible;
5. keep trusted output conservative: no unknown metric, invalid year, conflict, or missing provenance in trusted;
6. produce calibrated MinerU-body benchmark output and a clear decision on whether to proceed to 321E route comparison.

This is sandbox-only.

## non_goals
Do not do these in 321D2:
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call VLM/API/cloud/network.
- Do not use pure VLM outputs to repair MinerU table-body output.
- Do not modify E:\mineru_lab.
- Do not modify production delivery files.
- Do not apply data into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not claim production readiness.

## expected_new_or_modified_files
Likely modified:
- `datefac/mineru_body/mineru_table_normalizer.py`
- `datefac/mineru_body/mineru_body_candidate_mapper.py`
- `datefac/mineru_body/mineru_body_benchmark.py`
- `datefac/mineru_body/mineru_body_delivery_builder.py`
- `tools/run_mineru_table_body_ingestion_321d.py`

Suggested new files if cleaner:
- `datefac/mineru_body/mineru_body_calibration.py`
- `datefac/mineru_body/mineru_body_diagnostics.py`
- `tools/run_mineru_table_body_calibration_321d2.py`
- `docs/codex_tasks/321d2_mineru_body_normalization_calibration.md`

Keep MinerU-body logic inside `datefac/mineru_body`. Do not touch PPStructure pipeline, VLM modules, old Stage7, or 320G2 experimental files unless absolutely required, which they should not be.

## input_contract
Primary inputs:

```powershell
D:\_datefac\output\mineru_table_body_ingestion_321d
D:\_datefac\output\source_aware_router_revision_321c2
E:\mineru_lab\output_new
```

Optional comparison inputs:

```powershell
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
D:\_datefac\output\batch_row_text_delivery_320g
```

CLI should support either a new calibration tool:

```powershell
python tools/run_mineru_table_body_calibration_321d2.py ^
  --previous-ingestion-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --router-dir D:\_datefac\output\source_aware_router_revision_321c2 ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\mineru_table_body_calibration_321d2 ^
  --max-tables 20
```

Or extend the existing `run_mineru_table_body_ingestion_321d.py` with a calibration mode. Prefer a new CLI if it keeps risk lower.

If previous ingestion dir is missing, rerun from router + MinerU output root and produce equivalent calibrated output.

## diagnostics_required
Add these sheets to the 321D2 output.

### `unknown_metric_diagnostics`
Columns:
- table_id
- source_report_name
- table_asset_id
- effective_role_category
- table_title
- row_index
- raw_metric_name
- normalized_label
- source_row_text
- candidate_count_generated
- years_or_columns
- suggested_metric_code
- suggested_metric_family
- suggested_action
- reason

Suggested actions:
- `add_safe_alias`
- `keep_review_required`
- `ignore_group_header`
- `skip_non_metric_row`
- `unsupported_segment_row`
- `needs_manual_label_review`

Do not blindly add aliases. Only add obvious financial aliases.

### `header_year_diagnostics`
Columns:
- table_id
- raw_columns
- normalized_columns
- accepted_year_columns
- rejected_non_year_columns
- year_invalid_count_before
- year_invalid_count_after
- no_year_columns_before
- no_year_columns_after
- action
- reason

Rules:
- Accept year-like labels such as `2022`, `2023`, `2024`, `2024A`, `2025E`, `2026E`, `2027E`, `2028E`.
- Strip whitespace, newlines, full-width spaces, punctuation artifacts, and simple suffix noise.
- Reject non-year columns like `项目`, `指标`, `评级`, `单位`, `备注`, `报告期`, `同比`, `环比`, `行业`, `公司` from value-year candidate generation unless explicitly part of a supported non-year table schema.
- If no valid year columns exist, create table-level review or row-level review, not many invalid-year candidates.

### `row_filter_diagnostics`
Columns:
- table_id
- row_index
- raw_row_label
- source_row_text
- row_class
- action
- candidate_count_before
- candidate_count_after
- reason

Row classes:
- `METRIC_ROW`
- `GROUP_HEADER_ROW`
- `SECTION_TITLE_ROW`
- `FOOTNOTE_ROW`
- `EMPTY_ROW`
- `NON_CORE_ROW`
- `UNSUPPORTED_ROW`

### `value_parse_diagnostics`
Columns:
- table_id
- row_index
- metric_label
- column
- raw_value
- parse_status
- normalized_value
- action
- reason

Handle safely:
- `-`, `—`, `--`, `N/A`, empty cells -> missing value review or skip depending context;
- comma separators;
- parentheses negatives;
- percentage signs;
- Chinese units mixed into value cells;
- footnote markers.

### `alias_expansion_audit`
Columns:
- alias
- metric_code
- metric_family
- source_count
- trusted_impact_estimate
- added_in_321d2
- safety_level
- reason

Safe alias examples to consider if present:
- `营业总收入` -> revenue
- `收入` when table context is income/forecast -> revenue, otherwise review
- `归母净利润` / `归属于母公司所有者的净利润` -> net_profit_attributable_parent
- `扣非归母净利润` -> recurring_net_profit_attributable_parent
- `EPS` / `每股收益` / `基本每股收益` -> eps
- `PE` / `P/E` / `市盈率` -> pe
- `PB` / `P/B` / `市净率` -> pb
- `ROE` / `净资产收益率` -> roe
- `资产总额` / `资产总计` -> total_assets
- `负债合计` / `总负债` -> total_liabilities
- `股东权益合计` / `所有者权益合计` -> total_equity
- `经营活动现金流量净额` / `经营性现金流` -> operating_cash_flow
- `自由现金流` -> free_cash_flow, if context supports it

Keep ambiguous rows in review.

## calibration_requirements

### 1. Candidate inflation control
Do not create candidates for every cell in rows that are clearly group headers, section titles, empty rows, footnotes, or unsupported segment rows.

Expected effect:
- total_candidate_count may decrease from 1375.
- UNKNOWN_METRIC_CODE should decrease from 802.
- rejected/review rows should become more interpretable.

### 2. Year/header filtering
Do not produce candidate rows for non-year columns unless the table schema explicitly supports them.

Expected effect:
- year_invalid_count should drop from 156.
- NO_YEAR_COLUMNS should drop or move to table-level review.
- trusted output must continue to have zero invalid years.

### 3. Safe alias expansion
Add only high-confidence aliases for core financial tables. Keep ambiguous aliases as review.

Expected effect:
- unknown_metric_code_count should drop.
- trusted_total_count may improve, but do not force it.

### 4. Table-aware unit/value handling
321D already has unit_unknown_count = 0. Preserve this. Do not assign monetary units to percentage/ratio/per-share metrics incorrectly.

### 5. Conflict and QA preservation
321D had conflict_count = 0 and provenance_complete_rate = 1.0. Preserve these.

## output_contract
Write to:

```powershell
D:\_datefac\output\mineru_table_body_calibration_321d2
```

Required files:

1. `mineru_table_body_calibration_321d2.xlsx`

Sheets:
- `summary`
- `selected_worklist`
- `table_body_extraction_audit`
- `unified_tables`
- `normalized_rows`
- `metric_candidates_all`
- `trusted_preview`
- `review_required_preview`
- `rejected_preview`
- `per_table_summary`
- `metric_coverage`
- `unit_year_context_summary`
- `risk_tag_counts`
- `provenance_coverage`
- `normalization_audit`
- `mapping_diagnostics`
- `unknown_metric_diagnostics`
- `header_year_diagnostics`
- `row_filter_diagnostics`
- `value_parse_diagnostics`
- `alias_expansion_audit`
- `mineru_vs_vlm_ppstructure_summary`
- `qa_checks`
- `known_limitations`

2. `mineru_table_body_calibration_321d2_summary.json`

3. `mineru_table_body_calibration_321d2_report.md`

Optional:
- `trusted_preview.jsonl`
- `review_required_preview.jsonl`
- `unknown_metric_diagnostics.jsonl`

## summary_metrics
Include previous 321D metrics plus:
- calibrated_total_candidate_count
- calibrated_trusted_total_count
- calibrated_review_required_total_count
- calibrated_rejected_total_count
- calibrated_trusted_rate
- table_with_trusted_count
- unit_unknown_count
- year_invalid_count
- no_year_columns_count
- unknown_metric_code_count
- value_parse_failed_count
- row_label_missing_count
- group_header_skipped_count
- non_year_column_rejected_count
- alias_added_count
- candidate_count_reduction
- conflict_count
- provenance_complete_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- pure_vlm_calibrated_trusted_rate
- ppstructure_trusted_rate
- mineru_body_calibration_decision

Expected improvements over 321D:
- UNKNOWN_METRIC_CODE should drop from 802.
- INVALID_YEAR should drop from 156.
- NO_YEAR_COLUMNS should drop from 135 or move to table-level review.
- VALUE_PARSE_FAILED should drop from 69 where safely parseable.
- trusted_rate should improve if aliases/year handling are safe.

Decision rule:
- If qa_fail_count > 0:
  `MINERU_BODY_CALIBRATION_BLOCKED_BY_QA_FAILURE`
- If provenance_complete_rate < 0.95:
  `MINERU_BODY_CALIBRATION_BLOCKED_BY_PROVENANCE_GAP`
- If calibrated_trusted_rate >= 0.45, table_with_trusted_count >= 14, year_invalid_count == 0, unit_unknown_count == 0, conflict_count == 0:
  `MINERU_BODY_CALIBRATION_READY_FOR_321E_ROUTE_COMPARISON`
- If calibrated_trusted_rate >= 0.35 and diagnostics are complete:
  `MINERU_BODY_CALIBRATION_PARTIAL_NEEDS_ALIAS_REVIEW`
- Otherwise:
  `MINERU_BODY_CALIBRATION_NOT_READY`

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run PaddleOCR/PPStructure.
3. Do not call VLM/API/cloud/network.
4. Do not modify E-drive input/output folders.
5. Do not modify production delivery files.
6. Do not modify `data/overrides/02B_ai_repair_override.xlsx`.
7. Do not modify `data/mapping/formal_scope_rules.json`.
8. Do not run `factory_core.py`.
9. Do not rewrite old Stage7 pipeline.
10. Do not commit `output/` artifacts.
11. Do not commit anything under `E:\mineru_lab`.
12. Do not commit unrelated 320G2 experimental files or temp scripts.
13. Preserve Chinese text as UTF-8.

## validation
Run compile checks, for example:

```powershell
python -m py_compile datefac/mineru_body/mineru_table_normalizer.py
python -m py_compile datefac/mineru_body/mineru_body_candidate_mapper.py
python -m py_compile datefac/mineru_body/mineru_body_benchmark.py
python -m py_compile datefac/mineru_body/mineru_body_delivery_builder.py
```

If new files are added:

```powershell
python -m py_compile datefac/mineru_body/mineru_body_calibration.py
python -m py_compile datefac/mineru_body/mineru_body_diagnostics.py
python -m py_compile tools/run_mineru_table_body_calibration_321d2.py
```

Then run:

```powershell
python tools/run_mineru_table_body_calibration_321d2.py ^
  --previous-ingestion-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --router-dir D:\_datefac\output\source_aware_router_revision_321c2 ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\mineru_table_body_calibration_321d2 ^
  --max-tables 20
```

If using the existing 321D runner with calibration mode, report the exact equivalent command.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 321D2 code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Calibrate MinerU table body normalization`
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
- calibrated_rejected_total_count
- calibrated_trusted_rate
- table_with_trusted_count
- unit_unknown_count
- year_invalid_count
- no_year_columns_count
- unknown_metric_code_count
- value_parse_failed_count
- row_label_missing_count
- group_header_skipped_count
- non_year_column_rejected_count
- alias_added_count
- candidate_count_reduction
- conflict_count
- provenance_complete_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- pure_vlm_calibrated_trusted_rate
- ppstructure_trusted_rate
- mineru_body_calibration_decision
- top risk tags
- skipped/untracked files
