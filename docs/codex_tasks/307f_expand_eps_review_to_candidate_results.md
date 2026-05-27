# 307F Expand EPS Review To Candidate Results

## Goal
- Expand validated real EPS focused review results from 307E into candidate-level EPS review results.
- Sandbox-only; do not apply anything.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.

## Inputs
- `output/eval_307e_eps_focused_review_input_validation/307e_valid_eps_review_results.xlsx`
- `output/eval_307d_eps_focused_human_review_package/307d_eps_group_to_candidate_manifest.xlsx`

## Expansion Rules
- Expand only validated EPS review rows.
- Preserve candidate_id mapping.
- `approve_eps_series`:
  - all mapped candidate_ids become `approve_eps`
- `reject_eps_series`:
  - all mapped candidate_ids become `reject_eps`
- `needs_more_info`:
  - all mapped candidate_ids become `needs_more_info`
- `correct_eps_series`:
  - corrected year matching mapped candidate year => `correct_value`
    - `corrected_value = corrected_YEAR`
    - apply `corrected_unit` if present
  - mapped years without corrected year => keep original value, status `approve_eps`
  - corrected year without mapped candidate => `eps_human_discovered_missing_candidate`
  - do not generate fake candidate_id
- missing candidate rows must not enter normal existing-candidate pool.
- Preserve `reviewer_id`, `reviewed_at`, `review_comment`, `original_value`, `corrected_value`, `corrected_unit`.

## Outputs
- `output/eval_307f_expand_eps_review_to_candidate_results/`
  - `307f_summary.json`
  - `307f_report.md`
  - `307f_eps_candidate_review_results.xlsx`
  - `307f_eps_corrected_candidate_results.xlsx`
  - `307f_eps_approved_candidate_results.xlsx`
  - `307f_eps_rejected_candidate_results.xlsx`
  - `307f_eps_needs_more_info_candidate_results.xlsx`
  - `307f_eps_human_discovered_missing_candidates.xlsx`
  - `307f_eps_review_expansion_audit.xlsx`
  - `307f_no_apply_proof.json`

## Required Assertions
- `expanded_eps_review_group_count == 14`
- every existing expanded `candidate_id` exists in EPS manifest
- `fake_candidate_id_generated_count = 0`
- corrected years without existing candidate_id appear only in `eps_human_discovered_missing_candidates`
- no `safe_to_apply / approve_for_real_apply` fields generated
- sandbox/production apply attempts remain 0
- `check_delivery_state.py --json` remains PASS
- production/official/formal/standardizer/release unchanged
