# 308A Review Burden Reduction Strategy

## Task Goal
Analyze the remaining 342 `review_required` rows after 307X and produce a high-impact review burden reduction strategy.

This stage is diagnosis/planning only.

## Constraints
- Do not rerun Marker/pdfplumber.
- Do not call API/LLM/OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.
- Do not create new human review templates in this stage.
- Do not continue single-metric focused review chains.

## Required Inputs
- `output/eval_307x_core_metric_pipeline_stage_summary/307x_summary.json`
- `output/eval_307h_final_preview_v2_quality_diagnosis/307h_review_required_breakdown_v2.xlsx`
- `output/eval_307h_final_preview_v2_quality_diagnosis/307h_review_burden_by_metric_v2.xlsx`
- `output/eval_307h_final_preview_v2_quality_diagnosis/307h_review_burden_by_pdf_v2.xlsx`
- `output/eval_307g_merge_eps_review_into_final_preview/307g_review_required_core_metrics_v2.xlsx`
- `output/eval_306x_auto_accept_blocker_diagnosis/306x_blocker_by_group.xlsx`
- `output/eval_306z_conservative_relaxation_policy_v2/306z_review_required_v2.xlsx`
- `output/eval_306l_fix_grouped_review_risk_rules/306l_fix_grouped_review_table.xlsx`

## Required Analysis
- Remaining `review_required` rows by metric, PDF, source_parser, source_bucket, risk_level.
- Blocker reasons distribution.
- Single-blocker vs multi-blocker review burden.
- Rows caused by:
  - `multi_panel_source`
  - `missing_year`
  - `unit_unknown_or_warning`
  - `zero_candidate_rescued`
  - `alias_recovered`
  - `suspicious_value_text`
  - `years_not_continuous`
  - `unresolved_monetary_unit`
  - `duplicate_or_conflict`
- Top 3 high-impact generic fixes.
- Estimated row reduction for each fix.
- Recommendation for next stage direction:
  - parser fix
  - metric standardization fix
  - auto_accept policy refinement
  - human review UI/export productization
  - targeted human review batch

## Required Outputs
- `output/eval_308a_review_burden_reduction_strategy/308a_summary.json`
- `output/eval_308a_review_burden_reduction_strategy/308a_report.md`
- `output/eval_308a_review_burden_reduction_strategy/308a_review_required_global_breakdown.xlsx`
- `output/eval_308a_review_burden_reduction_strategy/308a_blocker_impact_ranking.xlsx`
- `output/eval_308a_review_burden_reduction_strategy/308a_single_vs_multi_blocker_analysis.xlsx`
- `output/eval_308a_review_burden_reduction_strategy/308a_high_impact_fix_candidates.xlsx`
- `output/eval_308a_review_burden_reduction_strategy/308a_metric_pdf_bottleneck_matrix.xlsx`
- `output/eval_308a_review_burden_reduction_strategy/308a_next_action_recommendation.md`
- `output/eval_308a_review_burden_reduction_strategy/308a_no_apply_proof.json`

## Required Assertions
- Input `review_required_v2` row count preserved.
- No `safe_to_apply` / `approve_for_real_apply` fields generated.
- `sandbox_apply_attempt_count = 0`.
- `production_apply_attempt_count = 0`.
- `check_delivery_state.py --json` PASS.
- `production/official/formal/standardizer/release` unchanged.
