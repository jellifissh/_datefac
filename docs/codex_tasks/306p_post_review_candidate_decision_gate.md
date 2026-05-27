# 306P Post-Review Candidate Decision Gate

## Goal
- Gate 306O candidate-level human review results into safe post-review decision pools, without apply.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.

## Inputs
- `output/eval_306o_expand_grouped_review_to_candidate_results/306o_candidate_review_results.xlsx`
- `output/eval_306o_expand_grouped_review_to_candidate_results/306o_corrected_candidate_results.xlsx`
- `output/eval_306o_expand_grouped_review_to_candidate_results/306o_rejected_candidate_results.xlsx`
- `output/eval_306o_expand_grouped_review_to_candidate_results/306o_needs_more_info_candidate_results.xlsx`
- `output/eval_306o_expand_grouped_review_to_candidate_results/306o_human_discovered_missing_candidates.xlsx`

## Decision Gate Rules
- `approve` -> approved_reviewed_candidates
- `correct_value` -> corrected_reviewed_candidates
- `reject` -> rejected_candidates
- `needs_more_info` -> needs_more_info_candidates
- `human_discovered_missing_candidate` -> missing_candidate_intake (separate pool)

## Hard Rules
- No `safe_to_apply`.
- No `approve_for_real_apply`.
- No production apply.
- No fake candidate_id.
- corrected candidates must preserve: original_value, corrected_value, corrected_unit, reviewer_id, reviewed_at, review_comment.
- missing candidates must not be mixed into existing candidate_id pool.

## Outputs
- `output/eval_306p_post_review_candidate_decision_gate/`
  - `306p_summary.json`
  - `306p_report.md`
  - `306p_approved_reviewed_candidates.xlsx`
  - `306p_corrected_reviewed_candidates.xlsx`
  - `306p_rejected_candidates.xlsx`
  - `306p_needs_more_info_candidates.xlsx`
  - `306p_missing_candidate_intake.xlsx`
  - `306p_post_review_decision_audit.xlsx`
  - `306p_no_apply_proof.json`

## Assertions
- no safe_to_apply or approve_for_real_apply fields generated.
- fake_candidate_id_generated_count = 0.
- missing candidates only appear in missing_candidate_intake.
- approved + corrected + rejected + needs_more_info counts == expanded existing candidate review count.
- `check_delivery_state.py --json` = PASS.
- production/official/formal rules/standardizer/release unchanged.
