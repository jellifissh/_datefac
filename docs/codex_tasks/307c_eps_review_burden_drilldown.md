# 307C EPS Review Burden Drilldown

## Goal
- Diagnose why `EPS` is the top review-required core metric after 307B.
- Sandbox-only; do not apply anything.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.

## Inputs
- `output/eval_307a_core_metric_final_export_preview/`
- `output/eval_307b_core_metric_export_quality_diagnosis/`
- `output/eval_306z_conservative_relaxation_policy_v2/`
- `output/eval_306l_fix_grouped_review_risk_rules/`
- `output/eval_306x_auto_accept_blocker_diagnosis/`

## Required Files
- `307a_final_core_metric_preview.xlsx`
- `307a_review_required_core_metrics.xlsx`
- `307b_review_burden_by_metric.xlsx`
- `306z_review_required_v2.xlsx`
- `306l_fix_grouped_review_table.xlsx`
- `306x_blocker_by_group.xlsx`

## Diagnosis Scope
- Filter all rows where `标准指标 = eps`.
- Count trusted EPS rows vs review-required EPS rows.
- Break down EPS review-required by:
  - PDF
  - source_parser
  - source_bucket
  - risk_level
  - blocker reasons
- Detect suspicious EPS values:
  - `abs(value) > 20`
  - percent-like EPS
  - values mixed with Chinese text
  - non-numeric values
- Identify EPS groups that could safely move to auto-accept if:
  - page1 summary
  - numeric-like values
  - semantic unit `yuan_per_share`
  - no multi_panel
  - no zero_candidate_rescued
  - no missing_year
  - no duplicate/conflict
- Identify EPS groups that must remain human review.

## Outputs
- `output/eval_307c_eps_review_burden_drilldown/`
  - `307c_summary.json`
  - `307c_report.md`
  - `307c_eps_trusted_rows.xlsx`
  - `307c_eps_review_required_rows.xlsx`
  - `307c_eps_review_burden_by_pdf.xlsx`
  - `307c_eps_blocker_distribution.xlsx`
  - `307c_eps_suspicious_value_audit.xlsx`
  - `307c_eps_potential_auto_accept_candidates.xlsx`
  - `307c_eps_must_review_candidates.xlsx`
  - `307c_no_apply_proof.json`

## Required Assertions
- no `safe_to_apply / approve_for_real_apply` fields generated
- sandbox/production apply attempts remain 0
- `check_delivery_state.py --json` remains PASS
- production/official/formal/standardizer/release unchanged
