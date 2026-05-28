# 309A Unit Semantic Standardization Diagnosis

## Task Goal
Diagnose `unit_unknown_or_warning` and `unresolved_monetary_unit` review burden after 308E.

This is diagnosis/design only. Do not apply anything.

## Requirements
- Do not rerun Marker/pdfplumber.
- Do not call API/LLM/OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.
- Do not merge any rescue rows into final preview.
- Do not require human review input.

## Read
- `output/eval_308a_review_burden_reduction_strategy/`
- `output/eval_307g_merge_eps_review_into_final_preview/`
- `output/eval_306x_auto_accept_blocker_diagnosis/`
- `output/eval_306z_conservative_relaxation_policy_v2/`
- `output/eval_306l_fix_grouped_review_risk_rules/`

## Use
- `308a_high_impact_fix_candidates.xlsx`
- `308a_blocker_impact_ranking.xlsx`
- `307g_review_required_core_metrics_v2.xlsx`
- `307g_final_core_metric_preview_v2.xlsx`
- `306x_blocker_by_group.xlsx`
- `306z_review_required_v2.xlsx`
- `306l_fix_grouped_review_table.xlsx`

## Analyze
- Focus on `unit_unknown_or_warning` and `unresolved_monetary_unit`.
- Break down affected rows by metric, PDF, source_parser, source_page, unit, normalized_unit.
- Identify metrics where unit can be safely inferred:
  - roe / gross_margin -> percent
  - pe / pb / ev_ebitda -> multiple
  - eps -> yuan_per_share
  - revenue / attributable_net_profit -> monetary unit, only if source context supports it
- Separate safe semantic unit cases from monetary ambiguous cases.
- Do not auto-merge anything.
- Produce proposed unit standardization rules and estimated review reduction.

## Generate
`output/eval_309a_unit_semantic_standardization_diagnosis/`
- `309a_summary.json`
- `309a_report.md`
- `309a_unit_issue_candidates.xlsx`
- `309a_unit_issue_by_metric_pdf.xlsx`
- `309a_safe_semantic_unit_candidates.xlsx`
- `309a_ambiguous_monetary_unit_candidates.xlsx`
- `309a_proposed_unit_rules.xlsx`
- `309a_expected_impact_estimate.xlsx`
- `309a_next_action_recommendation.md`
- `309a_no_apply_proof.json`

## Required Assertions
- input review_required_v2 row count preserved
- final preview v2 unchanged
- no rows merged into final preview
- no safe_to_apply / approve_for_real_apply fields generated
- sandbox_apply_attempt_count = 0
- production_apply_attempt_count = 0
- check_delivery_state.py --json PASS
- production/official/formal/standardizer/release unchanged
