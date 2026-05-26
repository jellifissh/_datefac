# Task 306B-FIX: Hierarchical Panel Splitter

## Stage
- `EVAL-306B-FIX`

## Goal
- Fix `306B` multi-panel splitting by adding a hierarchical second-pass.
- Preserve existing first-pass column splitting behavior.

## Scope
- Read existing outputs from:
  - `output/eval_306b_marker_multi_panel_splitter/`
  - `output/eval_marker1b_html_table_readable_render_fix/readable_excel/`
- Do not rerun Marker.

## Hard Constraints
- Do not call external API.
- Do not call LLM API.
- Do not call OCR.
- Do not modify production / official / formal rules / standardizer / release package.
- Keep `check_delivery_state.py --json` as `PASS`.

## Required Fix Behavior
- Keep first-pass split result as baseline.
- Add second-pass row splitting inside each first-pass **column panel** when another statement title appears.
- Example expected behavior:
  - `balance_sheet` panel containing `关键财务与估值指标` => split into `balance_sheet` + `valuation_metrics`.
  - `income_statement` panel containing `现金流量表` => split into `income_statement` + `cash_flow_statement`.

## Required Outputs
- `output/eval_306b_fix_hierarchical_panel_splitter/306b_fix_summary.json`
- `output/eval_306b_fix_hierarchical_panel_splitter/306b_fix_report.md`
- `output/eval_306b_fix_hierarchical_panel_splitter/306b_fix_split_panel_index.xlsx`
- `output/eval_306b_fix_hierarchical_panel_splitter/306b_fix_split_panels.xlsx`
- `output/eval_306b_fix_hierarchical_panel_splitter/306b_fix_split_panels_markdown/`
- `output/eval_306b_fix_hierarchical_panel_splitter/306b_fix_failed_split_candidates.xlsx`
- `output/eval_306b_fix_hierarchical_panel_splitter/306b_fix_no_apply_proof.json`

## Run
1. `python tools/run_306b_fix_hierarchical_panel_splitter.py`
2. `python tools/check_delivery_state.py --json`

## Git Hygiene
- Commit only task doc + runner implementation.
- Do not stage historical untracked files:
  - `tools/run_stage7a_5pdf_regression_sandbox.py`
  - `tools/update_stage5v_production_06_safe_rows.py`
