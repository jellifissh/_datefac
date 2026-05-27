# 306K Human Review Input Validation

## Goal
- Validate human review input files generated from the `306J` clean candidate human review template.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.

## Inputs
- `output/eval_306j_clean_candidate_human_review_input_design/`
- Immutable candidate source: `306j_candidate_id_manifest.xlsx`

## Validation Scope
- Validate `306j_sample_review_input.xlsx` first.
- Future real input path:
  - `input/human_review/306k_human_review_input.xlsx`
  - If absent: validate sample only and set `real_input_present=false`.

## Required Checks
1. `candidate_id` exists in manifest.
2. `candidate_id` not duplicated.
3. Immutable candidate fields unchanged.
4. `decision` in:
   - `approve`, `reject`, `needs_more_info`, `correct_value`
5. `reviewer_id` required.
6. `reviewed_at` required and parseable.
7. `decision=correct_value` requires:
   - `corrected_value`, `corrected_unit`
8. `decision=reject` should include `review_comment`.
9. `decision=needs_more_info` should include `extra_info_request`.
10. Forbidden fields absent:
   - `safe_to_apply`
   - `approve_for_real_apply`

## Outputs
- `output/eval_306k_human_review_input_validation/`
  - `306k_summary.json`
  - `306k_report.md`
  - `306k_valid_review_results.xlsx`
  - `306k_invalid_review_results.xlsx`
  - `306k_review_validation_audit.xlsx`
  - `306k_negative_validation_tests.json`
  - `306k_no_apply_proof.json`

## Validation
- Run `python tools/check_delivery_state.py --json` and keep `PASS`.
- Confirm production / official / formal rules / standardizer / release unchanged.
