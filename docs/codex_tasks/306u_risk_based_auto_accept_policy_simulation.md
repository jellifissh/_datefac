# 306U Risk-Based Auto-Accept Policy Simulation

## Goal
- Simulate a risk-based auto-accept / human-review routing policy for clean core candidates (sandbox-only).

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.

## Inputs
- `output/eval_306l_fix_grouped_review_risk_rules/306l_fix_grouped_review_table.xlsx`
- `output/eval_306l_fix_grouped_review_risk_rules/306l_fix_group_to_candidate_manifest.xlsx`
- `output/eval_306q_post_review_candidate_package_validation/306q_reviewed_candidate_pool.xlsx`
- `output/eval_306s_reviewed_projection_unit_normalization_gate/306s_unit_normalized_projection.xlsx`
- `output/eval_306t_missing_candidate_intake_validation/306t_valid_missing_candidate_intake.xlsx`
- `output/eval_306t_missing_candidate_intake_validation/306t_combined_reviewed_plus_missing_preview.xlsx`

## Policy Routing
- LOW clean groups -> `auto_accept_candidate_preview` only if all gates pass:
  - no missing_year
  - no unit warning
  - no zero_candidate_rescued
  - no alias_recovered
  - no multi_panel_source
  - no suspicious value text
  - continuous years where applicable
- MEDIUM groups -> `sample_review_required`
- HIGH groups -> `human_review_required`
- Any duplicate/conflict/unit warning -> `blocked_or_review_required`
- Reviewed/corrected candidates from 306S -> `manual_reviewed_preview`
- Missing candidates from 306T -> `missing_candidate_preview` only

## Hard Rules
- Do not generate `safe_to_apply`.
- Do not generate `approve_for_real_apply`.

## Outputs
- `output/eval_306u_risk_based_auto_accept_policy_simulation/`
  - `306u_summary.json`
  - `306u_report.md`
  - `306u_group_risk_routing.xlsx`
  - `306u_auto_accept_candidate_preview.xlsx`
  - `306u_sample_review_required.xlsx`
  - `306u_human_review_required.xlsx`
  - `306u_blocked_or_review_required.xlsx`
  - `306u_manual_reviewed_preview.xlsx`
  - `306u_missing_candidate_preview.xlsx`
  - `306u_review_workload_estimate.xlsx`
  - `306u_policy_rules.json`
  - `306u_no_apply_proof.json`

## Assertions
- no safe_to_apply / approve_for_real_apply fields
- auto_accept rows contain no HIGH risk groups
- missing candidates never enter auto_accept
- reviewed/corrected candidates remain separate from auto_accept
- duplicate_key_count = 0 for auto_accept preview
- value_conflict_count = 0 for auto_accept preview
- sandbox_apply_attempt_count = 0
- production_apply_attempt_count = 0
- check_delivery_state.py --json = PASS
- production/official/formal/standardizer/release unchanged
