# 308E Panel Denoise Spot-Check Review Package

## Task Goal
Create a human spot-check review package for 308D panel denoise rescue candidates.

This is for calibrating safety rules only. Do not merge anything.

## Requirements
- Do not rerun Marker/pdfplumber.
- Do not call API/LLM/OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.
- Do not merge any would_rescue rows into trusted preview.
- Do not modify parser outputs.

## Read
- `output/eval_308d_panel_denoise_rescue_safety_validation/`
- `output/eval_308c_parser_panel_denoise_rule_simulation/`
- `output/eval_307g_merge_eps_review_into_final_preview/`

## Use
- `308d_manual_spot_check_sample.xlsx`
- `308d_rescue_safety_scored_rows.xlsx`
- `308d_risk_distribution_by_metric.xlsx`
- `308d_risk_distribution_by_pdf.xlsx`
- `308d_rule_safety_audit.xlsx`
- `308c_would_rescue_from_review.xlsx`
- `307g_final_core_metric_preview_v2.xlsx`
- `307g_review_required_core_metrics_v2.xlsx`

## Generate
`output/eval_308e_panel_denoise_spot_check_review_package/`
- `308e_summary.json`
- `308e_report.md`
- `308e_spot_check_review_template.xlsx`
- `308e_spot_check_readme.md`
- `308e_spot_check_candidate_manifest.xlsx`
- `308e_rule_metric_pdf_context.xlsx`
- `308e_no_apply_proof.json`

## Template Requirements
- One row per sampled spot-check candidate.
- Include:
  - candidate_id
  - group_id
  - PDF文件名
  - 标准指标
  - 指标名
  - 年份
  - value
  - unit
  - normalized_unit
  - source_parser
  - source_page
  - source_bucket
  - denoise_rule
  - risk_label
  - silent_risk_flags
  - nearby trusted rows if available
  - review_required context if available
- Include reviewer fields:
  - decision
  - reviewer_id
  - reviewed_at
  - review_comment
  - corrected_metric
  - corrected_year
  - corrected_value
  - corrected_unit
  - extra_info_request
- decision enum:
  - approve_rescue
  - reject_rescue
  - correct_rescue
  - needs_more_info
- correct_rescue requires at least one corrected_* field.
- needs_more_info requires extra_info_request.
- reject_rescue should include review_comment.
- Do not include safe_to_apply or approve_for_real_apply.

## Required Assertions
- sampled row count equals 308D manual_spot_check_sample_row_count.
- candidate manifest preserved.
- no rows merged into final preview.
- final preview v2 unchanged.
- parser output files unchanged.
- no safe_to_apply / approve_for_real_apply fields generated.
- sandbox_apply_attempt_count = 0.
- production_apply_attempt_count = 0.
- check_delivery_state.py --json PASS.
- production/official/formal/standardizer/release unchanged.
