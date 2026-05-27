# 306Z Conservative Relaxation Policy v2

## Goal
- Create conservative auto-accept policy v2 based on 306Y sampled review.
- Sandbox-only simulation, no apply.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.

## Inputs
- `output/eval_306y_potential_safe_relaxation_review_package/`
- `output/eval_306w_relaxed_auto_accept_policy_simulation/`
- `output/eval_306x_auto_accept_blocker_diagnosis/`
- `output/eval_306l_fix_grouped_review_risk_rules/`

## Policy v2 (Allow Only)
- `auto_accept_v2` only if:
  - `page1_summary_clean_candidate = true`
  - `unit_unknown_semantic_resolvable = true`
  - metric in `eps / pe / pb / ev_ebitda / roe / gross_margin`
  - values are numeric-like
  - years are continuous
  - no `missing_year`
  - no suspicious value text
  - no duplicate/conflict
  - no `alias_recovered`
  - no `zero_candidate_rescued`
  - no `multi_panel_source`
  - no human corrected/rejected/needs_more_info group
  - not missing candidate intake

## Policy v2 (Always Review)
- `clean_multi_panel_candidate`
- `clean_missing_year_partial_series`
- `marker_clean_non_page1_candidate`
- `zero_candidate_rescued`
- `alias_recovered`
- `multi_panel_source`
- `missing_year`
- human corrected/rejected/needs_more_info groups
- missing candidate intake

## Outputs
- `output/eval_306z_conservative_relaxation_policy_v2/`
  - `306z_summary.json`
  - `306z_report.md`
  - `306z_group_routing_v2.xlsx`
  - `306z_auto_accept_candidate_preview_v2.xlsx`
  - `306z_review_required_v2.xlsx`
  - `306z_v1_vs_v2_comparison.xlsx`
  - `306z_policy_safety_audit.xlsx`
  - `306z_policy_rules.json`
  - `306z_no_apply_proof.json`

## Required Assertions
- corrected/rejected/needs_more_info groups routed to auto_accept_v2 count = 0
- missing candidates routed to auto_accept_v2 count = 0
- multi_panel groups routed to auto_accept_v2 count = 0
- zero_candidate_rescued groups routed to auto_accept_v2 count = 0
- marker_clean_non_page1_candidate-only groups routed to auto_accept_v2 count = 0
- missing_year groups routed to auto_accept_v2 count = 0
- duplicate_key_count_auto_accept_v2 = 0
- value_conflict_count_auto_accept_v2 = 0
- no safe_to_apply / approve_for_real_apply fields
- sandbox_apply_attempt_count = 0
- production_apply_attempt_count = 0
- check_delivery_state.py --json = PASS
- production/official/formal/standardizer/release unchanged
