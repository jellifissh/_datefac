# 310A Demo Ready Core Metric Export Package

## Task Goal
Create a demo-ready core metric export package from current trusted final preview v2 and review_required v2.

This is export/package only. Do not apply anything.

## Requirements
- Do not rerun Marker/pdfplumber.
- Do not call API/LLM/OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.
- Do not merge 308C or 309B simulated rescue rows.
- Do not create human review input templates.
- Keep simulated rescue outputs separate and marked as not merged.

## Read
- `output/eval_307g_merge_eps_review_into_final_preview/`
- `output/eval_307h_final_preview_v2_quality_diagnosis/`
- `output/eval_307x_core_metric_pipeline_stage_summary/`
- `output/eval_308d_panel_denoise_rescue_safety_validation/`
- `output/eval_309c_unit_semantic_rescue_safety_validation/`

## Use
- `307g_final_core_metric_preview_v2.xlsx`
- `307g_review_required_core_metrics_v2.xlsx`
- `307h_pdf_level_coverage_v2.xlsx`
- `307h_metric_level_coverage_v2.xlsx`
- `307h_export_readiness_assessment_v2.xlsx`
- `307x_stage_summary_report.md`
- `308d_summary.json`
- `309c_summary.json`

## Generate
`output/eval_310a_demo_ready_core_metric_export_package/`
- `310a_summary.json`
- `310a_demo_report.md`
- `310a_demo_core_metric_export.xlsx`
- `310a_trusted_core_metrics.xlsx`
- `310a_review_required_core_metrics.xlsx`
- `310a_pdf_coverage_summary.xlsx`
- `310a_metric_coverage_summary.xlsx`
- `310a_not_merged_rescue_simulation_summary.xlsx`
- `310a_demo_readiness_notes.md`
- `310a_no_apply_proof.json`

## Export Requirements
- trusted rows must come only from 307g_final_core_metric_preview_v2.
- review_required rows must remain separate.
- 308C panel rescue rows must not enter trusted export.
- 309B unit semantic rescue rows must not enter trusted export.
- Include source_bucket, review_status, source_parser, source_page, risk_level where available.
- Add a plain Chinese explanation sheet/note describing:
  - current demo-ready status
  - trusted row count
  - review_required row count
  - why simulated rescue rows were not merged
  - next recommended engineering direction

## Required Assertions
- final_preview_v2 row count preserved
- review_required_v2 row count preserved
- no simulated rescue rows merged into trusted export
- no safe_to_apply / approve_for_real_apply fields generated
- sandbox_apply_attempt_count = 0
- production_apply_attempt_count = 0
- check_delivery_state.py --json PASS
- production/official/formal/standardizer/release unchanged
