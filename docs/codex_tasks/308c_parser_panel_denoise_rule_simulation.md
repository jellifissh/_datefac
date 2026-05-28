# 308C Parser Panel Denoise Rule Simulation

## Task Goal
Run a sandbox-only simulation of parser panel denoise/merge rules proposed by 308B.

Do not modify parser outputs or production logic.

## Requirements
- Do not rerun Marker/pdfplumber.
- Do not call API/LLM/OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.
- Do not modify existing parser output files.
- Do not merge simulated rescue rows into final trusted preview yet.

## Read
- `output/eval_308b_parser_panel_denoise_and_merge_design/`
- `output/eval_307g_merge_eps_review_into_final_preview/`
- `output/eval_306x_auto_accept_blocker_diagnosis/`
- `output/eval_306z_conservative_relaxation_policy_v2/`

## Use
- `308b_panel_issue_candidates.xlsx`
- `308b_proposed_denoise_rules.xlsx`
- `308b_expected_impact_estimate.xlsx`
- `307g_review_required_core_metrics_v2.xlsx`
- `307g_final_core_metric_preview_v2.xlsx`
- `306x_blocker_by_group.xlsx`
- `306z_review_required_v2.xlsx`

## Simulation Rules
- Only simulate on review_required rows.
- Candidate can enter `would_rescue_from_review` only if:
  - numeric-like value
  - no Chinese text mixed with value
  - no merged value cell
  - no duplicate/conflict with trusted final preview v2
  - no missing candidate_id
  - no human rejected/needs_more_info status
  - year is valid
  - metric is target core metric
- Apply proposed rule categories:
  - panel_row_deduplication
  - panel_boundary_validation
  - metric_row_purity_guard
  - numeric_value_sanity_guard
  - year_column_continuity_guard
  - source_parser_priority_adjustment
- Rows failing guards go to `still_review_required` or `blocked_by_denoise`.
- Do not mark anything as `safe_to_apply`.
- Use `source_bucket=simulated_panel_denoise_rescue` only in simulation output.

## Generate
`output/eval_308c_parser_panel_denoise_rule_simulation/`
- `308c_summary.json`
- `308c_report.md`
- `308c_would_rescue_from_review.xlsx`
- `308c_still_review_required_after_simulation.xlsx`
- `308c_blocked_by_denoise_rules.xlsx`
- `308c_denoise_rule_hit_audit.xlsx`
- `308c_conflict_audit.xlsx`
- `308c_impact_estimate.xlsx`
- `308c_no_apply_proof.json`

## Required Assertions
- input review_required row count preserved
- final trusted preview v2 unchanged
- parser output files unchanged
- no safe_to_apply / approve_for_real_apply fields generated
- duplicate trusted key count for would_rescue = 0
- value conflict count with final preview v2 = 0
- sandbox_apply_attempt_count = 0
- production_apply_attempt_count = 0
- check_delivery_state.py --json PASS
- production/official/formal/standardizer/release unchanged
