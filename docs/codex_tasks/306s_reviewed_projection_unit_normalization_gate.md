# 306S Reviewed Projection Unit Normalization Gate

## Goal
- Normalize and validate units for 306R reviewed candidate sandbox projection before downstream export/apply stage.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.

## Inputs
- `output/eval_306r_reviewed_candidate_sandbox_projection/306r_reviewed_candidate_projection.xlsx`
- `output/eval_306r_reviewed_candidate_sandbox_projection/306r_unit_sanity_audit.xlsx`
- `output/eval_306r_reviewed_candidate_sandbox_projection/306r_missing_candidate_projection_preview.xlsx`

## Unit Normalization Rules
- `eps` -> `yuan_per_share`
- `pe` / `pb` / `ev_ebitda` -> `multiple`
- `roe` / `gross_margin` / `margin` / `growth_rate` metrics -> `percent`
- `revenue` / `net_profit` / `attributable_net_profit` / `operating_cash_flow` / `total_assets` / `total_liabilities`:
  infer from `effective_unit` / `original_unit`; preserve warning if unknown
- If `effective_unit` unknown but metric has deterministic semantic unit:
  fill `normalized_unit` with semantic default and set `unit_resolution_source=semantic_default`
- If monetary metric unit cannot be inferred:
  set `unit_warning=monetary_unit_unknown`
- Missing candidate preview applies same unit normalization but remains separate.

## Outputs
- `output/eval_306s_reviewed_projection_unit_normalization_gate/`
  - `306s_summary.json`
  - `306s_report.md`
  - `306s_unit_normalized_projection.xlsx`
  - `306s_unit_normalization_audit.xlsx`
  - `306s_unit_warning_audit.xlsx`
  - `306s_missing_candidate_unit_preview.xlsx`
  - `306s_no_apply_proof.json`

## Assertions
- projection_input_count equals 306R reviewed_candidate_projection_count.
- normalized_projection_count equals projection_input_count.
- missing candidates remain separate.
- no safe_to_apply / approve_for_real_apply fields generated.
- sandbox_apply_attempt_count = 0.
- production_apply_attempt_count = 0.
- check_delivery_state.py --json = PASS.
- production/official/formal rules/standardizer/release unchanged.
