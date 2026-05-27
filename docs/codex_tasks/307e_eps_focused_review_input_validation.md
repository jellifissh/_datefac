# 307E EPS Focused Review Input Validation

## Goal
- Validate real EPS focused human review input based on 307D template.
- Sandbox-only; do not apply anything.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.

## Inputs
- `output/eval_307d_eps_focused_human_review_package/`
  - `307d_eps_grouped_review_template.xlsx`
  - `307d_eps_group_to_candidate_manifest.xlsx`
- real input path (optional):
  - `input/human_review/307e_eps_focused_review_input.xlsx`

## Validation Rules
- `group_id` exists in EPS manifest.
- `group_id` not duplicated.
- immutable group fields unchanged.
- `decision` in:
  - `approve_eps_series`
  - `reject_eps_series`
  - `correct_eps_series`
  - `needs_more_info`
- `reviewer_id` required if decision present.
- `reviewed_at` required and parseable if decision present.
- `correct_eps_series` requires at least one corrected year or corrected_unit.
- `needs_more_info` requires `extra_info_request`.
- `reject_eps_series` should include `review_comment`.
- forbidden fields `safe_to_apply / approve_for_real_apply` absent.
- candidate mapping preserved.

## Real Input Handling
- If real input exists: validate real input.
- If absent: validate template shallow structure only and set `real_input_present=false`.

## Outputs
- `output/eval_307e_eps_focused_review_input_validation/`
  - `307e_summary.json`
  - `307e_report.md`
  - `307e_valid_eps_review_results.xlsx`
  - `307e_invalid_eps_review_results.xlsx`
  - `307e_eps_review_validation_audit.xlsx`
  - `307e_negative_validation_tests.json`
  - `307e_no_apply_proof.json`

## Required Assertions
- no safe_to_apply / approve_for_real_apply fields generated.
- candidate mapping preserved.
- sandbox/production apply attempts remain 0.
- `check_delivery_state.py --json` remains PASS.
- production/official/formal/standardizer/release unchanged.
