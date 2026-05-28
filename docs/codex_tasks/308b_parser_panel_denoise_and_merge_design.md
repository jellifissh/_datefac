# 308B Parser Panel Denoise And Merge Design

## Task Goal
Design a sandbox-only parser panel denoise and merge strategy to reduce `review_required` burden.

This stage is diagnosis/design only. Do not modify production extraction logic yet.

## Requirements
- Do not rerun Marker/pdfplumber.
- Do not call API/LLM/OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.
- Do not create human review templates.
- Do not change existing parser outputs.

## Read
- `output/eval_308a_review_burden_reduction_strategy/`
- `output/eval_307g_merge_eps_review_into_final_preview/`
- `output/eval_306x_auto_accept_blocker_diagnosis/`
- `output/eval_306b_fix_hierarchical_panel_splitter/`
- `output/eval_306c_marker_panels_to_full_structured_sandbox/`
- `output/eval_306d_marker_vs_pdfplumber_structured_regression/`
- `output/eval_306e_parser_fusion_pipeline_design/`

## Use
- `308a_blocker_impact_ranking.xlsx`
- `308a_high_impact_fix_candidates.xlsx`
- `307g_review_required_core_metrics_v2.xlsx`
- `306x_blocker_by_group.xlsx`
- `306b_fix_split_panel_index.xlsx`
- `306b_fix_split_panels.xlsx`
- `306c_marker_full_structured_table.xlsx`
- `306d_per_pdf_comparison.xlsx`
- `306e_fusion_source_decision_audit.xlsx`

## Analyze
- Focus on `parser_panel_denoise_and_merge` candidates.
- Identify rows/groups with:
  - `multi_panel_source`
  - `suspicious_value_text`
  - `duplicate_or_conflict`
  - dirty/merged value indicators
  - panel split artifacts
- Rank affected PDFs/pages/metrics.
- Determine whether issue is likely:
  - marker panel split
  - pdfplumber fragmentation
  - fusion routing
  - metric classification
  - unit/year alignment
- Propose sandbox-safe denoise/merge rules:
  - panel row de-duplication
  - panel boundary validation
  - metric-row purity guard
  - numeric value sanity guard
  - year-column continuity guard
  - source parser priority adjustment
- Estimate conservative/moderate review reduction.

## Generate
`output/eval_308b_parser_panel_denoise_and_merge_design/`
- `308b_summary.json`
- `308b_report.md`
- `308b_panel_issue_candidates.xlsx`
- `308b_panel_issue_by_pdf_page_metric.xlsx`
- `308b_parser_source_issue_breakdown.xlsx`
- `308b_proposed_denoise_rules.xlsx`
- `308b_expected_impact_estimate.xlsx`
- `308b_sandbox_experiment_plan.md`
- `308b_no_apply_proof.json`

## Required Assertions
- input `review_required` row count preserved
- no parser output files modified
- no production extraction logic modified
- no safe_to_apply / approve_for_real_apply fields generated
- `sandbox_apply_attempt_count = 0`
- `production_apply_attempt_count = 0`
- `check_delivery_state.py --json` PASS
- `production/official/formal/standardizer/release` unchanged
