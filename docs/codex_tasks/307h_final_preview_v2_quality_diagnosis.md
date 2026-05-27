# 307H Final Preview v2 Quality Diagnosis

## Goal
- Diagnose quality, coverage, and remaining review burden after 307G final preview v2.
- Sandbox-only; do not apply anything.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.

## Inputs
- `output/eval_307g_merge_eps_review_into_final_preview/`
  - `307g_final_core_metric_preview_v2.xlsx`
  - `307g_review_required_core_metrics_v2.xlsx`
  - `307g_coverage_delta_from_307a.xlsx`
  - `307g_conflict_audit.xlsx`
- `output/eval_307b_core_metric_export_quality_diagnosis/`
  - `307b_metric_level_coverage.xlsx`
  - `307b_review_burden_by_metric.xlsx`

## Outputs
- `output/eval_307h_final_preview_v2_quality_diagnosis/`
  - `307h_summary.json`
  - `307h_report.md`
  - `307h_pdf_level_coverage_v2.xlsx`
  - `307h_metric_level_coverage_v2.xlsx`
  - `307h_source_bucket_distribution_v2.xlsx`
  - `307h_review_required_breakdown_v2.xlsx`
  - `307h_review_burden_by_pdf_v2.xlsx`
  - `307h_review_burden_by_metric_v2.xlsx`
  - `307h_v1_vs_v2_quality_delta.xlsx`
  - `307h_export_readiness_assessment_v2.xlsx`
  - `307h_next_bottleneck_recommendation.md`
  - `307h_no_apply_proof.json`

## Diagnosis Scope
- Count trusted v2 rows by PDF / metric / year / source_bucket.
- Count review_required v2 rows by PDF / metric / source_parser / risk flags.
- Compare v1 vs v2:
  - trusted rows delta
  - review_required delta
  - EPS review burden delta
  - target metric coverage delta
- Identify current top review burden metric after EPS merge.
- Identify current top review burden PDF.
- Assess readiness:
  - `demo_ready`
  - `internal_test_ready`
  - `not_ready`

## Required Assertions
- final preview v2 rows remain unchanged.
- review_required v2 rows remain separate.
- no safe_to_apply / approve_for_real_apply fields generated.
- sandbox/production apply attempts remain 0.
- `check_delivery_state.py --json` remains PASS.
- production/official/formal/standardizer/release unchanged.
