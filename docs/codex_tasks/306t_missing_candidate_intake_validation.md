# 306T Missing Candidate Intake Validation

## Goal
- Validate human-discovered missing candidates from 306S before they can join any sandbox export preview.

## Constraints
- Do not rerun Marker / pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.
- Do not real apply.

## Inputs
- `output/eval_306s_reviewed_projection_unit_normalization_gate/306s_unit_normalized_projection.xlsx`
- `output/eval_306s_reviewed_projection_unit_normalization_gate/306s_missing_candidate_unit_preview.xlsx`

## Validation Rules (missing candidates)
1. no fake candidate_id
2. required fields present:
   - PDF/metric/year/value/unit
3. year in valid range
4. normalized_unit present OR warning recorded
5. no duplicate key against reviewed projection
6. no value conflict against reviewed projection
7. no `safe_to_apply` or `approve_for_real_apply`

## Outputs
- `output/eval_306t_missing_candidate_intake_validation/`
  - `306t_summary.json`
  - `306t_report.md`
  - `306t_valid_missing_candidate_intake.xlsx`
  - `306t_invalid_missing_candidate_intake.xlsx`
  - `306t_missing_candidate_conflict_audit.xlsx`
  - `306t_missing_candidate_duplicate_audit.xlsx`
  - `306t_combined_reviewed_plus_missing_preview.xlsx`
  - `306t_no_apply_proof.json`

## Assertions
- check_delivery_state.py --json = PASS
- production/official/formal rules/standardizer/release unchanged
