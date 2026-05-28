# 309B Unit Semantic Standardization Simulation

## Task Goal
Run a sandbox-only simulation of unit semantic standardization based on 309A.

Do not merge into final preview.

## Requirements
- Do not rerun Marker/pdfplumber.
- Do not call API/LLM/OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.
- Do not merge simulated rows into final preview.
- Do not require human review input.

## Read
- `output/eval_309a_unit_semantic_standardization_diagnosis/`
- `output/eval_307g_merge_eps_review_into_final_preview/`
- `output/eval_306x_auto_accept_blocker_diagnosis/`
- `output/eval_306z_conservative_relaxation_policy_v2/`

## Use
- `309a_safe_semantic_unit_candidates.xlsx`
- `309a_ambiguous_monetary_unit_candidates.xlsx`
- `309a_proposed_unit_rules.xlsx`
- `307g_review_required_core_metrics_v2.xlsx`
- `307g_final_core_metric_preview_v2.xlsx`
- `306x_blocker_by_group.xlsx`
- `306z_review_required_v2.xlsx`

## Simulation Rules
- Only simulate on review_required rows.
- Only allow deterministic semantic unit fixes:
  - roe / gross_margin -> percent
  - pe / pb / ev_ebitda -> multiple
  - eps -> yuan_per_share
- Do not rescue ambiguous monetary unit rows.
- Candidate can enter `would_rescue_unit_standardized` only if:
  - candidate_id exists
  - metric is target core metric
  - value is numeric-like
  - year is valid
  - no duplicate/conflict with final preview v2
  - no human rejected/needs_more_info status
  - no suspicious value text
- Use `source_bucket=simulated_unit_semantic_rescue` only in simulation outputs.
- Do not mark anything trusted.

## Generate
`output/eval_309b_unit_semantic_standardization_simulation/`
- `309b_summary.json`
- `309b_report.md`
- `309b_would_rescue_unit_standardized.xlsx`
- `309b_still_review_required_after_unit_simulation.xlsx`
- `309b_blocked_unit_candidates.xlsx`
- `309b_unit_rule_hit_audit.xlsx`
- `309b_conflict_audit.xlsx`
- `309b_impact_estimate.xlsx`
- `309b_no_apply_proof.json`

## Required Assertions
- input review_required_v2 row count preserved
- final preview v2 unchanged
- ambiguous monetary rows not rescued
- no rows merged into final preview
- duplicate trusted key count for would_rescue = 0
- value conflict count with final preview v2 = 0
- no safe_to_apply / approve_for_real_apply fields generated
- sandbox_apply_attempt_count = 0
- production_apply_attempt_count = 0
- check_delivery_state.py --json PASS
- production/official/formal/standardizer/release unchanged
