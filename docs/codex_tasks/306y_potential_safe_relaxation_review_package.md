# 306Y Potential Safe Relaxation Review Package

## Goal
- Create a human-readable review package for potential safe auto-accept relaxation candidates from 306X.
- Policy remains unchanged.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not apply.
- Do not modify production.

## Inputs
- `output/eval_306x_auto_accept_blocker_diagnosis/`
- `output/eval_306l_fix_grouped_review_risk_rules/`
- `output/eval_306w_relaxed_auto_accept_policy_simulation/`

## Outputs
- `output/eval_306y_potential_safe_relaxation_review_package/`
  - `306y_summary.json`
  - `306y_report.md`
  - `306y_relaxation_candidate_review.xlsx`
  - `306y_sampled_relaxation_review.xlsx`
  - `306y_relaxation_type_distribution.xlsx`
  - `306y_recommended_review_order.xlsx`
  - `306y_no_apply_proof.json`

## Requirements
- Preserve `group_id` and candidate mapping.
- Group candidates by relaxation type.
- Sample 20-30 groups, prioritize single-blocker groups first.
- Include year columns, values, units, blocker reasons, relaxation type, source parser, page info, risk flags.
- No `safe_to_apply` or `approve_for_real_apply` fields.
- `check_delivery_state.py --json` must remain PASS.
