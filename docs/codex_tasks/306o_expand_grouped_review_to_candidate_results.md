# 306O Expand Grouped Review To Candidate Results

## Goal
- Expand validated grouped human review results from 306N into candidate-level review results.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.

## Inputs
- `output/eval_306n_grouped_human_review_input_validation/306n_valid_group_review_results.xlsx`
- `output/eval_306m_grouped_human_review_input_design/306m_group_to_candidate_manifest.xlsx`
- `output/eval_306m_grouped_human_review_input_design/306m_group_id_manifest.xlsx`

## Expansion Rules
1. `approve_series`:
   - all mapped candidate_ids in group -> `approve`.
2. `reject_series`:
   - all mapped candidate_ids in group -> `reject`.
3. `needs_more_info`:
   - all mapped candidate_ids in group -> `needs_more_info`.
4. `correct_series`:
   - corrected year matching existing candidate year -> `correct_value`.
   - existing years without corrected year -> `approve`.
   - corrected year without existing candidate_id -> `human_discovered_missing_candidate` only.
   - `corrected_unit` applies to corrected and missing-candidate rows.

## Hard Rules
- Only expand validated real review rows.
- Preserve candidate_id mapping.
- No fake candidate_id.
- No `safe_to_apply` / `approve_for_real_apply` fields.
- No apply / no production write.

## Outputs
- `output/eval_306o_expand_grouped_review_to_candidate_results/`
  - `306o_summary.json`
  - `306o_report.md`
  - `306o_candidate_review_results.xlsx`
  - `306o_corrected_candidate_results.xlsx`
  - `306o_rejected_candidate_results.xlsx`
  - `306o_needs_more_info_candidate_results.xlsx`
  - `306o_human_discovered_missing_candidates.xlsx`
  - `306o_group_review_expansion_audit.xlsx`
  - `306o_no_apply_proof.json`

## Assertions
- expanded reviewed group count = 19.
- every existing expanded candidate_id exists in candidate manifest.
- missing corrected years without candidate_id only in human_discovered_missing_candidates.
- no fake candidate_id generated.
- no `safe_to_apply` / `approve_for_real_apply` fields.
- `check_delivery_state.py --json` = PASS.
- production/official/formal rules/standardizer/release unchanged.
