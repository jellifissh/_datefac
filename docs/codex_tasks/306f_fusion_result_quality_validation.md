# 306F Fusion Result Quality Validation

## Background
- Upstream stage `306E` produced sandbox-only parser fusion outputs by routing between pdfplumber (`EVAL-1B`) and Marker (`306C/306D`) without any apply action.
- Before any downstream candidate/application stage, we need a dedicated quality validation pass on fusion outputs.

## Goal
- Validate quality and risk posture of `306E` fusion outputs.
- This stage is **audit-only** and **sandbox-only**.

## Hard Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber extraction.
- Do not call API / LLM / OCR.
- Do not modify production.
- Keep production / official / formal-rules / standardizer / release package unchanged.
- `python tools/check_delivery_state.py --json` must remain `PASS`.

## Required Inputs
- `output/eval_306e_parser_fusion_pipeline_design/`
- `output/eval_306d_marker_vs_pdfplumber_structured_regression/`
- `output/eval_306c_marker_panels_to_full_structured_sandbox/`

## Validation Focus
1. Fusion core metric candidate quality.
2. Conflict audit row quality and reason sanity.
3. Blocked dirty row reason quality.
4. Source routing decision consistency.
5. Rescued pdfplumber zero-candidate PDFs.
6. Page-1 summary table rows in fusion.
7. Multi-panel / split-panel rows in fusion.

## Deliverables
Output directory:
- `output/eval_306f_fusion_result_quality_validation/`

Generate:
- `306f_summary.json`
- `306f_report.md`
- `306f_core_candidate_quality_audit.xlsx`
- `306f_conflict_reason_audit.xlsx`
- `306f_source_routing_audit.xlsx`
- `306f_rescued_zero_candidate_pdf_audit.xlsx`
- `306f_suspicious_fusion_rows.xlsx`
- `306f_manual_review_samples.xlsx`
- `306f_no_apply_proof.json`

## Execution
1. Run:
   - `python tools/run_306f_fusion_result_quality_validation.py`
2. Run:
   - `python tools/check_delivery_state.py --json`
3. Confirm unchanged-file constraints.
