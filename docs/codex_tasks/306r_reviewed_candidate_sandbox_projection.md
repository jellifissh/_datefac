# 306R Reviewed Candidate Sandbox Projection

## Goal
- Project 306Q reviewed candidate pool into sandbox-only effective candidate preview rows.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.

## Inputs
- `output/eval_306q_post_review_candidate_package_validation/306q_reviewed_candidate_pool.xlsx`
- `output/eval_306q_post_review_candidate_package_validation/306q_corrected_value_audit.xlsx`
- `output/eval_306q_post_review_candidate_package_validation/306q_missing_candidate_intake_audit.xlsx`
- `output/eval_306q_post_review_candidate_package_validation/306q_excluded_rejected_needs_more_info_audit.xlsx`

## Projection Rules
1. approved candidate:
   - `effective_value = original_value`
   - `effective_unit = original_unit` if present
2. corrected candidate:
   - `effective_value = corrected_value`
   - `effective_unit = corrected_unit` if present, else `original_unit`
   - preserve `original_value` and `corrected_value` audit fields
3. rejected + needs_more_info:
   - must not appear in reviewed projection
4. missing_candidate_intake:
   - generate separate `missing_candidate_projection_preview`
   - no fake candidate_id
   - never mixed into existing candidate projection
5. no `safe_to_apply`
6. no `approve_for_real_apply`

## Outputs
- `output/eval_306r_reviewed_candidate_sandbox_projection/`
  - `306r_summary.json`
  - `306r_report.md`
  - `306r_reviewed_candidate_projection.xlsx`
  - `306r_effective_value_audit.xlsx`
  - `306r_unit_sanity_audit.xlsx`
  - `306r_missing_candidate_projection_preview.xlsx`
  - `306r_excluded_candidate_audit.xlsx`
  - `306r_projection_duplicate_key_audit.xlsx`
  - `306r_projection_value_conflict_audit.xlsx`
  - `306r_no_apply_proof.json`

## Assertions
- reviewed_candidate_projection_count = 306Q reviewed_candidate_pool_count.
- rejected and needs_more_info count in projection = 0.
- missing candidates only in missing_candidate_projection_preview.
- fake_candidate_id_generated_count = 0.
- duplicate_key_count = 0.
- value_conflict_count = 0.
- no safe_to_apply / approve_for_real_apply fields.
- sandbox_apply_attempt_count = 0.
- production_apply_attempt_count = 0.
- check_delivery_state.py --json = PASS.
- production/official/formal rules/standardizer/release unchanged.
