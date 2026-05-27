# 306J Clean Candidate Human Review Input Design

## Goal
- Design a human review input package for `306I` clean core candidate review results.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.

## Inputs
- `output/eval_306i_clean_candidate_review_package/`

## Source Rule
- Use `306i_clean_core_candidates_review.xlsx` as the only source candidate set.

## Outputs
- `output/eval_306j_clean_candidate_human_review_input_design/`
  - `306j_summary.json`
  - `306j_report.md`
  - `306j_human_review_input_template.xlsx`
  - `306j_human_review_readme.md`
  - `306j_review_validation_policy.json`
  - `306j_sample_review_input.xlsx`
  - `306j_candidate_id_manifest.xlsx`
  - `306j_no_apply_proof.json`

## Decision Schema
- Allowed decisions:
  - `approve`
  - `reject`
  - `needs_more_info`
  - `correct_value`
- Required fields:
  - all decisions require: `reviewer_id`, `reviewed_at`
  - `correct_value` requires: `corrected_value`, `corrected_unit`
- Forbidden fields:
  - no `safe_to_apply`
  - no `approve_for_real_apply`

## Validation
- Run `python tools/check_delivery_state.py --json` and keep `PASS`.
- Confirm production / official / formal rules / standardizer / release unchanged.
