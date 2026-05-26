# Task 306B: Marker Multi-Panel Splitter (Sandbox Only)

## Stage
- `EVAL-306B`

## Goal
- Implement a sandbox-only splitter for Marker tables classified as `multi_panel_split_required` in 306A.

## Scope
- Read:
  - `output/eval_306a_marker_table_quality_gate_and_parser_fusion_design/`
  - `output/eval_marker1b_html_table_readable_render_fix/`
- Write:
  - `output/eval_306b_marker_multi_panel_splitter/`

## Hard Constraints
- Do not rerun Marker.
- Do not call external API.
- Do not call LLM API.
- Do not call OCR.
- Do not modify production / official / formal rules / standardizer / release package.
- Keep `check_delivery_state.py --json` as `PASS`.

## Mandatory Target Filtering (Manual Correction)
Only process rows where all are true:
- `render_status = SUCCESS`
- `table_classification = multi_panel_split_required`
- `parsed_table_count > 0`
- `row_count > 0`
- `col_count > 0`

Ignore rows where any are true:
- `render_status = FAILED_PARSE`
- `table_classification = low_value_or_junk`
- `empty_shell_table = true`
- `table_text_preview` is empty

Expected:
- `306a_multi_panel_candidates.xlsx` has 47 rows total.
- Only 16 rows are real split targets.

## Split Output Panels
- `balance_sheet`
- `income_statement`
- `cash_flow_statement`
- `valuation_metrics`
- `financial_summary`
- `business_assumption`

## Required Outputs
- `306b_summary.json`
- `306b_report.md`
- `306b_split_panel_index.xlsx`
- `306b_split_panels.xlsx`
- `306b_split_panels_markdown/`
- `306b_failed_split_candidates.xlsx`
- `306b_no_apply_proof.json`

## Run
1. `python tools/run_306b_marker_multi_panel_splitter.py`
2. `python tools/check_delivery_state.py --json`

## Git Hygiene
- Commit only task doc + runner implementation.
- Do not stage historical untracked files:
  - `tools/run_stage7a_5pdf_regression_sandbox.py`
  - `tools/update_stage5v_production_06_safe_rows.py`
