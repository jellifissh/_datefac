# 307A Core Metric Final Export Preview

## Goal
- Build a sandbox-only final core metric export preview by combining:
  - `auto_accept_v2`
  - manually reviewed normalized projection
  - valid missing-intake candidates
- Do not apply anything.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.

## Inputs
- `output/eval_306z_conservative_relaxation_policy_v2/`
- `output/eval_306s_reviewed_projection_unit_normalization_gate/`
- `output/eval_306t_missing_candidate_intake_validation/`
- `output/eval_306q_post_review_candidate_package_validation/`
- `output/eval_306l_fix_grouped_review_risk_rules/`

## Required Files
- `306z_auto_accept_candidate_preview_v2.xlsx`
- `306z_review_required_v2.xlsx`
- `306s_unit_normalized_projection.xlsx`
- `306t_valid_missing_candidate_intake.xlsx`
- `306q_reviewed_candidate_pool.xlsx`
- `306l_fix_group_to_candidate_manifest.xlsx`

## Final Preview Rules
- Include auto-accepted v2 rows as `source_bucket=auto_accept_v2`.
- Include manual reviewed normalized projection rows as `source_bucket=manual_reviewed`.
- Include valid missing intake rows as `source_bucket=human_missing_intake`.
- Keep review-required rows in separate output only.
- Preserve `candidate_id` for existing candidates.
- Do not fake `candidate_id` for missing intake.
- Normalize columns:
  - `PDF文件名`
  - `group_id`
  - `candidate_id`
  - `标准指标`
  - `指标名`
  - `年份`
  - `value`
  - `unit`
  - `normalized_unit`
  - `source_bucket`
  - `review_status`
  - `risk_level`
  - `source_parser`
  - `source_page`
  - `evidence_note`
- Deduplicate by `PDF文件名 + 标准指标 + 年份 + source_bucket`.
- Trusted bucket priority for same `PDF/metric/year`:
  - `manual_reviewed > human_missing_intake > auto_accept_v2`
- Any conflicts must go to conflict audit, not silent merge.

## Outputs
- `output/eval_307a_core_metric_final_export_preview/`
  - `307a_summary.json`
  - `307a_report.md`
  - `307a_final_core_metric_preview.xlsx`
  - `307a_auto_accept_core_metrics.xlsx`
  - `307a_manual_reviewed_core_metrics.xlsx`
  - `307a_missing_intake_core_metrics.xlsx`
  - `307a_review_required_core_metrics.xlsx`
  - `307a_conflict_audit.xlsx`
  - `307a_coverage_by_pdf_metric.xlsx`
  - `307a_export_quality_summary.xlsx`
  - `307a_no_apply_proof.json`

## Required Assertions
- no `safe_to_apply / approve_for_real_apply` fields generated
- `fake_candidate_id_generated_count = 0`
- duplicate trusted key count = 0 after priority resolution
- unresolved conflict count = 0 for final preview
- review_required rows remain separate
- `sandbox_apply_attempt_count = 0`
- `production_apply_attempt_count = 0`
- `check_delivery_state.py --json = PASS`
- production/official/formal/standardizer/release unchanged
