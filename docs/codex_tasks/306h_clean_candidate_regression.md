# 306H Clean Candidate Regression

## Goal
- Run regression validation on `306G-Fix` clean core candidates before any downstream approval/apply stage.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.

## Inputs
- `output/eval_306g_fix_core_semantic_quality_gate/`
- `output/eval_306e_parser_fusion_pipeline_design/`
- `output/eval_306f_fusion_result_quality_validation/`

## Validation Scope
1. Per-PDF clean core candidate coverage.
2. Rescued zero-candidate PDFs status.
3. Duplicate `(pdf, metric, year)` keys.
4. Value conflicts on duplicate keys.
5. Missing key metrics by PDF.
6. Source parser distribution.
7. Remaining suspicious patterns.

## Outputs
- `output/eval_306h_clean_candidate_regression/`
  - `306h_summary.json`
  - `306h_report.md`
  - `306h_per_pdf_clean_candidate_coverage.xlsx`
  - `306h_core_metric_matrix.xlsx`
  - `306h_duplicate_key_audit.xlsx`
  - `306h_value_conflict_audit.xlsx`
  - `306h_missing_core_metric_audit.xlsx`
  - `306h_source_parser_distribution.xlsx`
  - `306h_manual_spot_check_samples.xlsx`
  - `306h_no_apply_proof.json`

## Validation
- Run `python tools/check_delivery_state.py --json` and keep `PASS`.
- Confirm production / official / formal rules / standardizer / release unchanged.
