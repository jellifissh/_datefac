# 306Q Post-Review Candidate Package Validation

## Goal
- Validate 306P post-review decision pools before any sandbox projection or apply stage.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.

## Inputs
- `output/eval_306p_post_review_candidate_decision_gate/306p_approved_reviewed_candidates.xlsx`
- `output/eval_306p_post_review_candidate_decision_gate/306p_corrected_reviewed_candidates.xlsx`
- `output/eval_306p_post_review_candidate_decision_gate/306p_rejected_candidates.xlsx`
- `output/eval_306p_post_review_candidate_decision_gate/306p_needs_more_info_candidates.xlsx`
- `output/eval_306p_post_review_candidate_decision_gate/306p_missing_candidate_intake.xlsx`
- `output/eval_306p_post_review_candidate_decision_gate/306p_post_review_decision_audit.xlsx`

## Validation Rules
1. approved + corrected -> reviewed_candidate_pool.
2. rejected must not enter reviewed_candidate_pool.
3. needs_more_info must not enter reviewed_candidate_pool.
4. missing_candidate_intake must not enter existing candidate pool.
5. corrected candidates preserve:
   - original_value, corrected_value, corrected_unit, reviewer_id, reviewed_at, review_comment.
6. candidate_id required for approved/corrected/rejected/needs_more_info existing candidates.
7. missing_candidate_intake must not have fake candidate_id.
8. reviewed_candidate_pool has no duplicate PDF/standard_metric/year keys.
9. reviewed_candidate_pool has no conflicting values on same key.
10. no safe_to_apply field.
11. no approve_for_real_apply field.
12. no production apply.

## Outputs
- `output/eval_306q_post_review_candidate_package_validation/`
  - `306q_summary.json`
  - `306q_report.md`
  - `306q_reviewed_candidate_pool.xlsx`
  - `306q_corrected_value_audit.xlsx`
  - `306q_excluded_rejected_needs_more_info_audit.xlsx`
  - `306q_missing_candidate_intake_audit.xlsx`
  - `306q_duplicate_key_audit.xlsx`
  - `306q_value_conflict_audit.xlsx`
  - `306q_no_apply_proof.json`

## Assertions
- reviewed_candidate_pool_count = approved_count + corrected_count.
- rejected_count + needs_more_info_count excluded from reviewed_candidate_pool.
- missing_candidate_intake_count separate.
- duplicate_key_count = 0.
- value_conflict_count = 0.
- fake_candidate_id_generated_count = 0.
- no safe_to_apply / approve_for_real_apply fields generated.
- check_delivery_state.py --json = PASS.
- production/official/formal rules/standardizer/release unchanged.
