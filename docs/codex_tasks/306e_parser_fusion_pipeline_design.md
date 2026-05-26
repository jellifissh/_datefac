# Task 306E: Parser Fusion Pipeline Design (Sandbox Only)

## Stage
- `EVAL-306E`

## Goal
- Design and implement a sandbox-only parser fusion pipeline using pdfplumber `EVAL-1B` and Marker `306C/306D` outputs.

## Scope
- Read:
  - `output/eval_306d_marker_vs_pdfplumber_structured_regression/`
  - `output/eval_306c_marker_panels_to_full_structured_sandbox/`
  - `output/eval1b_profile_selection_fix_regression/`
- Write:
  - `output/eval_306e_parser_fusion_pipeline_design/`

## Hard Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber extraction.
- Do not call external API.
- Do not call LLM API.
- Do not call OCR.
- Do not modify production / official / formal rules / standardizer / release package.
- Keep `check_delivery_state.py --json` as `PASS`.

## Required Fusion Routing Rules
- Prefer Marker for page1 summary/forecast tables.
- Prefer Marker for multi-panel pages and split panels.
- Prefer Marker for pdfplumber zero-candidate PDFs.
- Prefer pdfplumber when Marker row has dirty flags.
- Block rows with `merged_value_cell`, `suspicious_year`, `polluted_metric_name`.
- If same `pdf/metric/year` has conflicting values, do not auto-resolve; send to conflict audit.

## Required Outputs
- `306e_summary.json`
- `306e_report.md`
- `306e_fusion_structured_table.xlsx`
- `306e_fusion_core_metric_candidates.xlsx`
- `306e_fusion_source_decision_audit.xlsx`
- `306e_fusion_conflict_audit.xlsx`
- `306e_fusion_blocked_rows.xlsx`
- `306e_parser_routing_policy.json`
- `306e_no_apply_proof.json`

## Run
1. `python tools/run_306e_parser_fusion_pipeline_design.py`
2. `python tools/check_delivery_state.py --json`

## Git Hygiene
- Commit only task doc + runner implementation.
- Do not stage historical untracked files:
  - `tools/run_stage7a_5pdf_regression_sandbox.py`
  - `tools/update_stage5v_production_06_safe_rows.py`
