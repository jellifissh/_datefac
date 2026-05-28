# 310B Demo Export QA And Readability Check

## Task Goal
QA the 310A demo-ready core metric export package for readability, completeness, and presentation readiness.

Do not change extraction logic or merge any data.

## Requirements
- Do not rerun Marker/pdfplumber.
- Do not call API/LLM/OCR.
- Do not modify production.
- Do not real apply.
- Do not generate `safe_to_apply` or `approve_for_real_apply`.
- Do not merge simulated rescue rows.
- Do not create human review templates.

## Read
- `output/eval_310a_demo_ready_core_metric_export_package/`

## Use
- `310a_demo_core_metric_export.xlsx`
- `310a_trusted_core_metrics.xlsx`
- `310a_review_required_core_metrics.xlsx`
- `310a_pdf_coverage_summary.xlsx`
- `310a_metric_coverage_summary.xlsx`
- `310a_not_merged_rescue_simulation_summary.xlsx`
- `310a_demo_readiness_notes.md`

## Check
- workbook sheets exist and are non-empty where expected
- trusted row count = 70
- review_required row count = 342
- no simulated rescue rows merged into trusted sheet
- trusted sheet contains enough provenance columns:
  - source_bucket
  - source_parser
  - source_page
  - PDF文件名
  - 标准指标
  - 年份
  - value
  - normalized_unit
- Chinese explanation exists and is readable
- identify columns that should be renamed for demo readability
- identify whether workbook is:
  - demo_ready
  - needs_readability_fix
  - not_ready

## Generate
`output/eval_310b_demo_export_qa_and_readability_check/`
- `310b_summary.json`
- `310b_report.md`
- `310b_workbook_sheet_audit.xlsx`
- `310b_column_readability_audit.xlsx`
- `310b_demo_readiness_checklist.xlsx`
- `310b_recommended_demo_export_layout.md`
- `310b_no_apply_proof.json`

## Required Assertions
- 310A trusted row count preserved
- 310A review_required row count preserved
- no simulated rescue rows merged
- no safe_to_apply / approve_for_real_apply fields generated
- sandbox_apply_attempt_count = 0
- production_apply_attempt_count = 0
- check_delivery_state.py --json PASS
- production/official/formal/standardizer/release unchanged
