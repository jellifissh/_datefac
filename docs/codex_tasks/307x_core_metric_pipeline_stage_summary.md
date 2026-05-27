# 307X Core Metric Pipeline Stage Summary

## Goal
- Create stage summary and MVP readiness report for core metric extraction/review/export pipeline after 307I.
- Documentation/diagnosis only; no apply.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.
- Do not create new review input templates.
- Do not continue ROE-focused review chain in this stage.

## Inputs
- `output/eval_306e_parser_fusion_pipeline_design/`
- `output/eval_306g_fix_core_semantic_quality_gate/`
- `output/eval_306h_fix2_alias_recovery_growth_guard/`
- `output/eval_306z_conservative_relaxation_policy_v2/`
- `output/eval_307a_core_metric_final_export_preview/`
- `output/eval_307b_core_metric_export_quality_diagnosis/`
- `output/eval_307g_merge_eps_review_into_final_preview/`
- `output/eval_307h_final_preview_v2_quality_diagnosis/`
- `output/eval_307i_roe_review_burden_drilldown/`

## Outputs
- `output/eval_307x_core_metric_pipeline_stage_summary/`
  - `307x_summary.json`
  - `307x_stage_summary_report.md`
  - `307x_pipeline_capability_matrix.xlsx`
  - `307x_mvp_readiness_assessment.xlsx`
  - `307x_remaining_bottleneck_ranking.xlsx`
  - `307x_next_phase_recommendation.md`
  - `307x_no_apply_proof.json`

## Required Coverage in Report
- parser fusion status
- clean core candidate status
- human review loop status
- EPS focused fix result
- final preview v2 quality
- current trusted vs review_required counts
- current top bottleneck metric and PDF
- why ROE should not immediately get a full EPS-like chain
- demo readiness vs internal-test readiness vs paid MVP readiness
- recommended next phase:
  - A. productized export/UI
  - B. review burden reduction
  - C. parser/metric standardization improvement
  - D. all of the above with priority order

## Required Assertions
- no `safe_to_apply / approve_for_real_apply` fields generated
- sandbox/production apply attempts remain 0
- `check_delivery_state.py --json` remains PASS
- production/official/formal/standardizer/release unchanged
