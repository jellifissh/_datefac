# 307B Core Metric Export Quality Diagnosis

## Goal
- Diagnose quality, coverage, and remaining review burden of 307A final core metric export preview.
- Sandbox-only; do not apply anything.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.

## Inputs
- `output/eval_307a_core_metric_final_export_preview/`
  - `307a_final_core_metric_preview.xlsx`
  - `307a_review_required_core_metrics.xlsx`
  - `307a_coverage_by_pdf_metric.xlsx`
  - `307a_export_quality_summary.xlsx`
  - `307a_conflict_audit.xlsx`

## Outputs
- `output/eval_307b_core_metric_export_quality_diagnosis/`
  - `307b_summary.json`
  - `307b_report.md`
  - `307b_pdf_level_coverage.xlsx`
  - `307b_metric_level_coverage.xlsx`
  - `307b_source_bucket_distribution.xlsx`
  - `307b_review_required_breakdown.xlsx`
  - `307b_review_burden_by_pdf.xlsx`
  - `307b_review_burden_by_metric.xlsx`
  - `307b_export_readiness_assessment.xlsx`
  - `307b_next_bottleneck_recommendation.md`
  - `307b_no_apply_proof.json`

## Diagnosis Scope
- Count trusted final preview rows by PDF / metric / year / source_bucket.
- Count review-required rows by PDF / metric / source_parser / risk flags (if present).
- Estimate trusted coverage over target core metrics.
- Identify lowest-coverage PDFs and metrics.
- Identify top remaining review blockers.
- Assess readiness:
  - `demo_ready`
  - `internal_test_ready`
  - `not_ready`

## Required Assertions
- final preview rows remain unchanged.
- review_required rows remain separate.
- no safe_to_apply / approve_for_real_apply fields generated.
- sandbox/production apply attempt counts remain 0.
- `check_delivery_state.py --json` remains PASS.
- production/official/formal/standardizer/release unchanged.
