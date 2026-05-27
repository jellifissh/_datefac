# 307I ROE Review Burden Drilldown

## Goal
- Diagnose why ROE is the top review-required core metric after 307H.
- Sandbox-only; do not apply anything.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.

## Inputs
- `output/eval_307g_merge_eps_review_into_final_preview/`
- `output/eval_307h_final_preview_v2_quality_diagnosis/`
- `output/eval_306z_conservative_relaxation_policy_v2/`
- `output/eval_306l_fix_grouped_review_risk_rules/`
- `output/eval_306x_auto_accept_blocker_diagnosis/`

## Required Files
- `307g_final_core_metric_preview_v2.xlsx`
- `307g_review_required_core_metrics_v2.xlsx`
- `307h_review_burden_by_metric_v2.xlsx`
- `306z_review_required_v2.xlsx`
- `306l_fix_grouped_review_table.xlsx`
- `306x_blocker_by_group.xlsx`

## Diagnosis Scope
- Filter rows where `标准指标 = roe`.
- Count trusted ROE rows vs review-required ROE rows.
- Break down ROE review-required by:
  - PDF
  - source_parser
  - source_bucket
  - risk_level
  - blocker reasons
- Detect suspicious ROE values:
  - `abs(value) > 100`
  - percent-like missing unit
  - value looks like PE/PB multiple
  - values mixed with Chinese text
  - non-numeric values
- Identify ROE groups for focused human review.
- Identify ROE groups that must remain human review.
- No auto-accept changes in this stage.

## Outputs
- `output/eval_307i_roe_review_burden_drilldown/`
  - `307i_summary.json`
  - `307i_report.md`
  - `307i_roe_trusted_rows.xlsx`
  - `307i_roe_review_required_rows.xlsx`
  - `307i_roe_review_burden_by_pdf.xlsx`
  - `307i_roe_blocker_distribution.xlsx`
  - `307i_roe_suspicious_value_audit.xlsx`
  - `307i_roe_potential_focused_review_candidates.xlsx`
  - `307i_roe_must_review_candidates.xlsx`
  - `307i_no_apply_proof.json`

## Required Assertions
- no `safe_to_apply / approve_for_real_apply` fields generated
- sandbox/production apply attempts remain 0
- `check_delivery_state.py --json` remains PASS
- production/official/formal/standardizer/release unchanged
