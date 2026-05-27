# 307D EPS Focused Human Review Package

## Goal
- Create a focused human review package for EPS review-required groups diagnosed in 307C.
- Sandbox-only; do not apply anything.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.

## Inputs
- `output/eval_307c_eps_review_burden_drilldown/`
- `output/eval_307a_core_metric_final_export_preview/`
- `output/eval_306l_fix_grouped_review_risk_rules/`
- `output/eval_306z_conservative_relaxation_policy_v2/`

## Required Files
- `307c_eps_review_required_rows.xlsx`
- `307c_eps_suspicious_value_audit.xlsx`
- `307c_eps_must_review_candidates.xlsx`
- `306l_fix_grouped_review_table.xlsx`
- `306l_fix_group_to_candidate_manifest.xlsx`

## Outputs
- `output/eval_307d_eps_focused_human_review_package/`
  - `307d_summary.json`
  - `307d_report.md`
  - `307d_eps_grouped_review_template.xlsx`
  - `307d_eps_suspicious_review_priority.xlsx`
  - `307d_eps_by_pdf_review_order.xlsx`
  - `307d_eps_review_readme.md`
  - `307d_eps_group_to_candidate_manifest.xlsx`
  - `307d_no_apply_proof.json`

## Template Requirements
- One row per EPS group.
- Include:
  - `PDF文件名`
  - `group_id`
  - `source_page`
  - `source_parser`
  - `blocker_reasons`
  - `suspicious_value_flags`
- Include year columns `2020` ... `2030` with current EPS values.
- Include review fields:
  - `decision`
  - `reviewer_id`
  - `reviewed_at`
  - `review_comment`
  - `corrected_2020` ... `corrected_2030`
  - `corrected_unit`
  - `extra_info_request`
- Decision enum:
  - `approve_eps_series`
  - `reject_eps_series`
  - `correct_eps_series`
  - `needs_more_info`
- Validation rule notes:
  - `correct_eps_series` requires at least one corrected year value or corrected_unit.
  - `needs_more_info` requires `extra_info_request`.
- Do not include `safe_to_apply` or `approve_for_real_apply`.

## Required Assertions
- `eps_group_count` equals 307C `eps_must_review_group_count`.
- suspicious EPS groups are prioritized.
- group_to_candidate mapping preserved.
- no safe_to_apply / approve_for_real_apply fields generated.
- sandbox/production apply attempts remain 0.
- `check_delivery_state.py --json` remains PASS.
- production/official/formal/standardizer/release unchanged.
