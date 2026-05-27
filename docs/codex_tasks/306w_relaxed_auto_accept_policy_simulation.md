# 306W Relaxed Auto-Accept Policy Simulation

## Goal
- Create a relaxed but still safe auto-accept policy simulation based on 306V, then compare strict vs relaxed policy and estimate review reduction improvement.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.

## Inputs
- `output/eval_306v_risk_policy_calibration/`
- `output/eval_306u_risk_based_auto_accept_policy_simulation/`
- `output/eval_306l_fix_grouped_review_risk_rules/`
- `output/eval_306s_reviewed_projection_unit_normalization_gate/`
- `output/eval_306t_missing_candidate_intake_validation/`

## Baseline (Strict from 306V)
- `strict_auto_accept_group_count`
- `strict_auto_accept_candidate_count`
- `strict_review_reduction_rate`

## Relaxed Policy Rules
- Allow auto-accept when `unit_unknown` can be resolved by deterministic metric semantics:
  - `eps -> yuan_per_share`
  - `pe/pb/ev_ebitda -> multiple`
  - `roe/gross_margin -> percent`
- Allow marker-only clean groups when:
  - no `missing_year`
  - no unit warning
  - no suspicious value text
  - no duplicate/conflict
  - years continuous
- Allow page1 summary clean groups when:
  - values numeric
  - years continuous
  - no risk flags

## Still Block / Review Required
- `zero_candidate_rescued`
- `alias_recovered`
- `multi_panel_source`
- `missing_year`
- value conflict
- duplicate key
- unresolved monetary unit
- real human reviewed risky groups (`corrected/rejected/needs_more_info`)
- missing candidate intake

## Outputs
- `output/eval_306w_relaxed_auto_accept_policy_simulation/`
  - `306w_summary.json`
  - `306w_report.md`
  - `306w_relaxed_group_routing.xlsx`
  - `306w_relaxed_auto_accept_candidate_preview.xlsx`
  - `306w_relaxed_review_required.xlsx`
  - `306w_strict_vs_relaxed_comparison.xlsx`
  - `306w_relaxed_policy_safety_audit.xlsx`
  - `306w_policy_rules.json`
  - `306w_no_apply_proof.json`

## Required Assertions
- corrected/rejected/needs_more_info reviewed groups routed to relaxed auto_accept count = 0.
- missing candidates routed to relaxed auto_accept count = 0.
- relaxed auto_accept duplicate_key_count = 0.
- relaxed auto_accept value_conflict_count = 0.
- no `safe_to_apply` / `approve_for_real_apply` fields generated.
- `sandbox_apply_attempt_count = 0`.
- `production_apply_attempt_count = 0`.
- `check_delivery_state.py --json = PASS`.
- production/official/formal/standardizer/release unchanged.
