# 306V Risk Policy Calibration

## Goal
- Calibrate and evaluate 306U risk-based auto-accept policy using existing real human review results (sandbox-only).

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.

## Inputs
- `output/eval_306u_risk_based_auto_accept_policy_simulation/306u_group_risk_routing.xlsx`
- `output/eval_306u_risk_based_auto_accept_policy_simulation/306u_auto_accept_candidate_preview.xlsx`
- `output/eval_306u_risk_based_auto_accept_policy_simulation/306u_sample_review_required.xlsx`
- `output/eval_306u_risk_based_auto_accept_policy_simulation/306u_human_review_required.xlsx`
- `output/eval_306u_risk_based_auto_accept_policy_simulation/306u_blocked_or_review_required.xlsx`
- `output/eval_306u_risk_based_auto_accept_policy_simulation/306u_review_workload_estimate.xlsx`
- `output/eval_306o_expand_grouped_review_to_candidate_results/306o_candidate_review_results.xlsx`
- `output/eval_306p_post_review_candidate_decision_gate/306p_corrected_reviewed_candidates.xlsx`
- `output/eval_306p_post_review_candidate_decision_gate/306p_rejected_candidates.xlsx`
- `output/eval_306p_post_review_candidate_decision_gate/306p_needs_more_info_candidates.xlsx`
- `output/eval_306q_post_review_candidate_package_validation/306q_reviewed_candidate_pool.xlsx`
- `output/eval_306s_reviewed_projection_unit_normalization_gate/306s_unit_normalized_projection.xlsx`
- `output/eval_306t_missing_candidate_intake_validation/306t_valid_missing_candidate_intake.xlsx`

## Calibration Checks
- Check if any real corrected/rejected/needs_more_info group would route to auto_accept.
- Check whether reviewed approved groups were mostly LOW vs review-required.
- Check auto_accept group/candidate counts and review reduction estimate.
- Judge too strict vs too loose behavior.
- Missing candidates stay outside auto_accept.
- Reviewed/corrected candidates stay separate from auto_accept.
- No safe_to_apply / approve_for_real_apply.
- No apply.

## Outputs
- `output/eval_306v_risk_policy_calibration/`
  - `306v_summary.json`
  - `306v_report.md`
  - `306v_policy_calibration_by_review_result.xlsx`
  - `306v_auto_accept_safety_audit.xlsx`
  - `306v_review_reduction_estimate.xlsx`
  - `306v_policy_too_strict_or_too_loose_audit.xlsx`
  - `306v_recommended_policy_adjustments.md`
  - `306v_no_apply_proof.json`

## Assertions
- corrected/rejected/needs_more_info reviewed groups routed to auto_accept count = 0.
- missing candidates routed to auto_accept count = 0.
- reviewed/corrected candidates routed to auto_accept count = 0.
- auto_accept duplicate_key_count = 0.
- auto_accept value_conflict_count = 0.
- no safe_to_apply / approve_for_real_apply fields.
- sandbox_apply_attempt_count = 0.
- production_apply_attempt_count = 0.
- check_delivery_state.py --json = PASS.
- production/official/formal rules/standardizer/release unchanged.
