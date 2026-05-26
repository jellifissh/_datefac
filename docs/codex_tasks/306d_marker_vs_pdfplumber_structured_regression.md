# Task 306D: Marker vs pdfplumber Structured Regression

## Stage
- `EVAL-306D`

## Goal
- Compare Marker `306C` structured output against pdfplumber `EVAL-1B` structured output.

## Scope
- Read:
  - `output/eval_306c_marker_panels_to_full_structured_sandbox/`
  - `output/eval1b_profile_selection_fix_regression/`
  - `output/eval_img1_visual_table_layout_audit/`
- Write:
  - `output/eval_306d_marker_vs_pdfplumber_structured_regression/`

## Hard Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber extraction.
- Do not call external API.
- Do not call LLM API.
- Do not call OCR.
- Do not modify production / official / formal rules / standardizer / release package.
- Keep `check_delivery_state.py --json` as `PASS`.

## Required Comparison Dimensions
- row counts
- high-confidence rows
- core metric coverage
- zero-candidate PDFs
- dirty/blocked rows
- duplicate/value/unit/year conflicts
- page 1 summary table coverage
- multi-panel table coverage

## Required Outputs
- `306d_summary.json`
- `306d_report.md`
- `306d_per_pdf_comparison.xlsx`
- `306d_core_metric_coverage_comparison.xlsx`
- `306d_conflict_comparison.xlsx`
- `306d_marker_only_improvements.xlsx`
- `306d_pdfplumber_only_advantages.xlsx`
- `306d_fusion_next_step_recommendation.md`
- `306d_no_apply_proof.json`

## Run
1. `python tools/run_306d_marker_vs_pdfplumber_structured_regression.py`
2. `python tools/check_delivery_state.py --json`

## Git Hygiene
- Commit only task doc + runner implementation.
- Do not stage historical untracked files:
  - `tools/run_stage7a_5pdf_regression_sandbox.py`
  - `tools/update_stage5v_production_06_safe_rows.py`
