# 307G Merge EPS Review Into Final Preview

## Goal
- Merge 307F EPS candidate-level review results back into 307A final core metric preview.
- Build enhanced sandbox-only final preview v2.
- Do not apply anything.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.

## Inputs
- `output/eval_307a_core_metric_final_export_preview/`
  - `307a_final_core_metric_preview.xlsx`
  - `307a_review_required_core_metrics.xlsx`
- `output/eval_307f_expand_eps_review_to_candidate_results/`
  - `307f_eps_candidate_review_results.xlsx`
  - `307f_eps_corrected_candidate_results.xlsx`
  - `307f_eps_approved_candidate_results.xlsx`
  - `307f_eps_rejected_candidate_results.xlsx`
  - `307f_eps_needs_more_info_candidate_results.xlsx`
  - `307f_eps_human_discovered_missing_candidates.xlsx`

## Merge Rules
- approved EPS candidates -> trusted preview with `source_bucket=eps_manual_reviewed`
- corrected EPS candidates -> trusted preview with `source_bucket=eps_manual_corrected`
- corrected candidates use `corrected_value` when present, otherwise `original_value`
- corrected unit uses `corrected_unit` when present, otherwise `normalized_unit=yuan_per_share`
- rejected EPS candidates remain excluded
- needs_more_info EPS candidates remain review_required
- EPS missing candidates remain separate as `eps_missing_intake_preview` and no fake candidate_id
- Remove corresponding EPS rows from review_required if candidate_id resolved by
  approved / corrected / rejected / needs_more_info
- Trusted key priority:
  - `eps_manual_corrected > eps_manual_reviewed > human_missing_intake > manual_reviewed > auto_accept_v2`
- Conflicts go to conflict audit, not silent merge.

## Outputs
- `output/eval_307g_merge_eps_review_into_final_preview/`
  - `307g_summary.json`
  - `307g_report.md`
  - `307g_final_core_metric_preview_v2.xlsx`
  - `307g_eps_manual_reviewed_core_metrics.xlsx`
  - `307g_eps_missing_intake_preview.xlsx`
  - `307g_review_required_core_metrics_v2.xlsx`
  - `307g_excluded_eps_candidates.xlsx`
  - `307g_conflict_audit.xlsx`
  - `307g_coverage_delta_from_307a.xlsx`
  - `307g_no_apply_proof.json`

## Required Assertions
- no `safe_to_apply / approve_for_real_apply` fields generated
- `fake_candidate_id_generated_count = 0`
- duplicate trusted key count after priority resolution = 0
- unresolved conflict count = 0 for final preview v2
- resolved EPS candidate_ids removed from review_required_v2
- rejected and needs_more_info EPS do not enter trusted preview
- sandbox/production apply attempts remain 0
- `check_delivery_state.py --json` remains PASS
- production/official/formal/standardizer/release unchanged
