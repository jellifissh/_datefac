# 306X Auto-Accept Blocker Diagnosis

## Goal
- Diagnose why most groups are still not auto-accepted after 306W relaxed policy.
- Sandbox-only diagnosis. No apply.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.

## Inputs
- `output/eval_306w_relaxed_auto_accept_policy_simulation/`
- `output/eval_306l_fix_grouped_review_risk_rules/`
- `output/eval_306u_risk_based_auto_accept_policy_simulation/`
- `output/eval_306v_risk_policy_calibration/`

## Required Files
- `306w_relaxed_group_routing.xlsx`
- `306w_relaxed_auto_accept_candidate_preview.xlsx`
- `306w_relaxed_review_required.xlsx`
- `306w_strict_vs_relaxed_comparison.xlsx`
- `306l_fix_grouped_review_table.xlsx`
- `306u_group_risk_routing.xlsx`
- `306v_policy_calibration_by_review_result.xlsx`

## Diagnosis Scope
- For each non-auto-accepted group, identify blocker reasons:
  - `missing_year`
  - `unit_unknown_or_warning`
  - `zero_candidate_rescued`
  - `alias_recovered`
  - `multi_panel_source`
  - `suspicious_value_text`
  - `years_not_continuous`
  - `unresolved_monetary_unit`
  - `reviewed_risky_group`
  - `duplicate_or_conflict`
  - `unknown_priority`
- Count blocker frequency by:
  - group count
  - candidate count
- Identify:
  - single-blocker groups
  - multi-blocker groups
  - potential safe relaxation candidates:
    - `unit_unknown_semantic_resolvable`
    - `clean_multi_panel_candidate`
    - `clean_missing_year_partial_series`
    - `page1_summary_clean_candidate`
    - `marker_clean_non_page1_candidate`

## Outputs
- `output/eval_306x_auto_accept_blocker_diagnosis/`
  - `306x_summary.json`
  - `306x_report.md`
  - `306x_blocker_by_group.xlsx`
  - `306x_blocker_distribution.xlsx`
  - `306x_candidate_impact_by_blocker.xlsx`
  - `306x_single_blocker_groups.xlsx`
  - `306x_multi_blocker_groups.xlsx`
  - `306x_potential_safe_relaxation_candidates.xlsx`
  - `306x_no_apply_proof.json`

## Required Assertions
- no `safe_to_apply` / `approve_for_real_apply` fields generated.
- `sandbox_apply_attempt_count = 0`
- `production_apply_attempt_count = 0`
- `check_delivery_state.py --json` remains `PASS`
- production/official/formal rules/standardizer/release unchanged
