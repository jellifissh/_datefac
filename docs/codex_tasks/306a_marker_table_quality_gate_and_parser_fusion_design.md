# Task 306A: Marker Table Quality Gate and Parser Fusion Design

## Stage
- `EVAL-306A`

## Goal
- Design and implement a table-quality gate over existing Marker outputs.
- Produce parser-fusion planning artifacts (Marker vs pdfplumber), without rerunning Marker.

## Scope
- Read only existing outputs:
  - `output/eval_marker1b_html_table_readable_render_fix/`
  - `output/eval_marker1_no_llm_parser_benchmark/`
  - `output/eval1b_profile_selection_fix_regression/`
- Write outputs to:
  - `output/eval_306a_marker_table_quality_gate_and_parser_fusion_design/`

## Hard Constraints
- Do not rerun Marker.
- Do not call external API.
- Do not call LLM API.
- Do not call OCR.
- Do not modify production files / official 02B / formal rules / `financial_standardizer.py` / release package.
- Keep `check_delivery_state.py --json` at `PASS`.

## Required Processing
- Score every Marker-rendered table.
- Classify each table into one of:
  - `direct_structurable`
  - `multi_panel_split_required`
  - `context_required`
  - `low_value_or_junk`
  - `manual_inspection_required`
- Detect and flag:
  - high-value financial forecast tables
  - financial summary tables
  - balance sheet / income statement / cash flow / valuation panels
  - business assumption tables
  - empty shell tables
  - disclaimer/rating/contact tables
  - multi-panel wide tables

## Required Outputs
- `306a_summary.json`
- `306a_report.md`
- `306a_marker_table_quality_gate.xlsx`
- `306a_high_value_marker_tables.xlsx`
- `306a_junk_or_low_value_tables.xlsx`
- `306a_multi_panel_candidates.xlsx`
- `306a_parser_fusion_recommendation.md`
- `306a_parser_fusion_recommendation.json`
- `306a_no_apply_proof.json`

## Run
1. `python tools/run_306a_marker_table_quality_gate_and_parser_fusion_design.py`
2. `python tools/check_delivery_state.py --json`

## Git Hygiene
- Commit only task doc + runner implementation.
- Do not stage historical untracked files:
  - `tools/run_stage7a_5pdf_regression_sandbox.py`
  - `tools/update_stage5v_production_06_safe_rows.py`
