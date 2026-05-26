# Task 306C: Marker Panels to Full Structured (Sandbox)

## Stage
- `EVAL-306C`

## Goal
- Convert validated Marker `direct_structurable` tables and `306B-Fix` successful split panels into sandbox full-structured-like rows.

## Scope
- Read:
  - `output/eval_306a_marker_table_quality_gate_and_parser_fusion_design/`
  - `output/eval_306b_fix_hierarchical_panel_splitter/`
  - `output/eval_marker1b_html_table_readable_render_fix/`
- Write:
  - `output/eval_306c_marker_panels_to_full_structured_sandbox/`

## Hard Constraints
- Do not rerun Marker.
- Do not call external API.
- Do not call LLM API.
- Do not call OCR.
- Do not modify production / official / formal rules / standardizer / release package.
- Keep `check_delivery_state.py --json` as `PASS`.

## Inclusion/Exclusion
Only process:
- `306A` `direct_structurable` tables
- `306B-Fix` successful split panels

Exclude:
- `low_value_or_junk`
- `FAILED_PARSE`
- `split_failed`
- `context_required`

## Output Schema
Each structured row should include:
- `source_pdf_name`
- `page_number`
- `panel_label`
- `statement_type`
- `raw_metric_name`
- `normalized_metric_name`
- `year`
- `value_raw`
- `value`
- `inferred_unit`
- `confidence_flags`
- `source_panel_id`

## Dirty-Data Guards
- `polluted_metric_name` (e.g. `74 财务费用`)
- `suspicious_year` (e.g. outlier like 2020 in 2024-2028 context)
- `merged_value_cell` (e.g. `40 35`, `82 (163)`)
- `empty_metric_name_with_value`
- `missing_value_for_core_metric`

## Required Outputs
- `306c_summary.json`
- `306c_report.md`
- `306c_marker_full_structured_table.xlsx`
- `306c_high_confidence_structured_rows.xlsx`
- `306c_dirty_cell_audit.xlsx`
- `306c_suspicious_year_audit.xlsx`
- `306c_merged_value_audit.xlsx`
- `306c_blocked_rows_audit.xlsx`
- `306c_no_apply_proof.json`

## Run
1. `python tools/run_306c_marker_panels_to_full_structured_sandbox.py`
2. `python tools/check_delivery_state.py --json`

## Git Hygiene
- Commit only task doc + runner implementation.
- Do not stage historical untracked files:
  - `tools/run_stage7a_5pdf_regression_sandbox.py`
  - `tools/update_stage5v_production_06_safe_rows.py`
