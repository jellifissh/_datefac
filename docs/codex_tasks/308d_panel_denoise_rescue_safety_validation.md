# 308D Panel Denoise Rescue Safety Validation

## Task Goal
Validate the safety of 308C simulated `would_rescue` rows before any merge.

This is sandbox-only safety validation. Do not apply or merge anything.

## Requirements
- Do not rerun Marker/pdfplumber.
- Do not call API/LLM/OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.
- Do not merge `would_rescue` rows into final trusted preview.
- Do not modify parser outputs.

## Read
- `output/eval_308c_parser_panel_denoise_rule_simulation/`
- `output/eval_308b_parser_panel_denoise_and_merge_design/`
- `output/eval_307g_merge_eps_review_into_final_preview/`
- `output/eval_306l_fix_grouped_review_risk_rules/`
- `output/eval_306x_auto_accept_blocker_diagnosis/`

## Use
- `308c_would_rescue_from_review.xlsx`
- `308c_denoise_rule_hit_audit.xlsx`
- `308c_conflict_audit.xlsx`
- `308c_impact_estimate.xlsx`
- `308b_panel_issue_by_pdf_page_metric.xlsx`
- `307g_final_core_metric_preview_v2.xlsx`
- `307g_review_required_core_metrics_v2.xlsx`
- `306l_fix_grouped_review_table.xlsx`
- `306x_blocker_by_group.xlsx`

## Validation
- Stratify would_rescue rows by:
  - metric
  - PDF文件名
  - source_parser
  - source_page
  - denoise_rule
  - risk_level
- Generate manual spot-check sample of 30-40 rows, prioritizing:
  - top rescue metric
  - top rescue PDF
  - ROE/gross_margin percent metrics
  - revenue/net_profit monetary metrics
  - PE/PB/EV_EBITDA valuation metrics
  - multi_panel_source rows
- Compute safety risk labels:
  - low_risk_rescue_candidate
  - medium_risk_needs_spot_check
  - high_risk_keep_review_required
- Detect possible silent risks:
  - metric family mismatch
  - unit mismatch
  - year sequence gap
  - abnormal value range by metric
  - source page concentration risk
  - repeated identical series across PDFs
- Do not mark anything as trusted.
- Do not create safe_to_apply or approve_for_real_apply.

## Generate
`output/eval_308d_panel_denoise_rescue_safety_validation/`
- `308d_summary.json`
- `308d_report.md`
- `308d_rescue_safety_scored_rows.xlsx`
- `308d_manual_spot_check_sample.xlsx`
- `308d_risk_distribution_by_metric.xlsx`
- `308d_risk_distribution_by_pdf.xlsx`
- `308d_rule_safety_audit.xlsx`
- `308d_silent_risk_audit.xlsx`
- `308d_merge_readiness_recommendation.md`
- `308d_no_apply_proof.json`

## Required Assertions
- input would_rescue row count preserved
- no rows merged into final preview
- final preview v2 unchanged
- parser output files unchanged
- no safe_to_apply / approve_for_real_apply fields generated
- sandbox_apply_attempt_count = 0
- production_apply_attempt_count = 0
- check_delivery_state.py --json PASS
- production/official/formal/standardizer/release unchanged
