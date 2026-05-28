# 309C Unit Semantic Rescue Safety Validation

## Task Goal
Validate the safety of 309B simulated unit semantic rescue rows before any merge.

This is sandbox-only safety validation. Do not apply or merge anything.

## Requirements
- Do not rerun Marker/pdfplumber.
- Do not call API/LLM/OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.
- Do not merge would_rescue rows into final trusted preview.
- Do not modify parser outputs.
- Do not require human review input.

## Read
- `output/eval_309b_unit_semantic_standardization_simulation/`
- `output/eval_309a_unit_semantic_standardization_diagnosis/`
- `output/eval_307g_merge_eps_review_into_final_preview/`
- `output/eval_306x_auto_accept_blocker_diagnosis/`

## Use
- `309b_would_rescue_unit_standardized.xlsx`
- `309b_unit_rule_hit_audit.xlsx`
- `309b_conflict_audit.xlsx`
- `309b_impact_estimate.xlsx`
- `309a_proposed_unit_rules.xlsx`
- `307g_final_core_metric_preview_v2.xlsx`
- `307g_review_required_core_metrics_v2.xlsx`
- `306x_blocker_by_group.xlsx`

## Validation
- Stratify would_rescue rows by metric, PDF, source_parser, source_page, inferred_unit.
- Compute safety risk labels:
  - low_risk_unit_rescue_candidate
  - medium_risk_needs_spot_check
  - high_risk_keep_review_required
- Low-risk candidate requirements:
  - metric in roe/gross_margin/pe/pb/ev_ebitda/eps
  - deterministic inferred unit matches metric family
  - value numeric-like
  - year valid
  - no duplicate/conflict with final preview v2
  - no suspicious value text
  - no multi_panel_source blocker
  - no zero_candidate_rescued blocker
  - no alias_recovered blocker
  - no missing_year blocker
  - no abnormal value range by metric
- Medium risk:
  - deterministic unit ok but has one soft blocker, e.g. non-page1, source concentration, or source_parser warning
- High risk:
  - metric/unit mismatch, abnormal value, suspicious blocker, multi_panel, zero_candidate_rescued, alias_recovered, missing_year, conflict risk.
- Do not mark anything trusted.

## Generate
`output/eval_309c_unit_semantic_rescue_safety_validation/`
- `309c_summary.json`
- `309c_report.md`
- `309c_unit_rescue_safety_scored_rows.xlsx`
- `309c_low_risk_unit_rescue_candidates.xlsx`
- `309c_medium_risk_unit_spot_check_candidates.xlsx`
- `309c_high_risk_unit_keep_review_required.xlsx`
- `309c_risk_distribution_by_metric.xlsx`
- `309c_risk_distribution_by_pdf.xlsx`
- `309c_unit_safety_rule_audit.xlsx`
- `309c_no_apply_proof.json`

## Required Assertions
- input would_rescue row count preserved
- no rows merged into final preview
- final preview v2 unchanged
- parser output files unchanged
- no safe_to_apply / approve_for_real_apply fields generated
- sandbox_apply_attempt_count = 0
- production_apply_attempt_count = 0
- check_delivery_state.py --json PASS
- production/official/formal/standardizer/release unchanged
