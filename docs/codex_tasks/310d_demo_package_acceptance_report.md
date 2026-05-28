# 310D Demo Package Acceptance Report

## Task Goal
Create a final acceptance report for the readable demo export package after 310C. This is documentation/QA only. Do not modify data.

## Requirements
- Do not rerun Marker/pdfplumber.
- Do not call API/LLM/OCR.
- Do not modify production.
- Do not real apply.
- Do not generate safe_to_apply or approve_for_real_apply.
- Do not merge simulated rescue rows.
- Do not alter trusted/review_required row membership.
- Do not create human review templates.

## Read
- `output/eval_310c_readable_demo_export_layout_generation/`
- `output/eval_310b_demo_export_qa_and_readability_check/`
- `output/eval_310a_demo_ready_core_metric_export_package/`
- `output/eval_307x_core_metric_pipeline_stage_summary/`

## Use
- `310c_readable_demo_core_metric_export.xlsx`
- `310c_summary.json`
- `310c_export_layout_audit.xlsx`
- `310b_summary.json`
- `310a_summary.json`
- `307x_stage_summary_report.md`

## Generate
`output/eval_310d_demo_package_acceptance_report/`
- `310d_summary.json`
- `310d_acceptance_report.md`
- `310d_demo_walkthrough.md`
- `310d_demo_acceptance_checklist.xlsx`
- `310d_known_limitations.md`
- `310d_next_phase_roadmap.md`
- `310d_no_apply_proof.json`

## Report Must Cover
- demo workbook path
- trusted row count = 70
- review_required row count = 342
- readable workbook sheet list
- why simulated rescue rows are not merged
- current demo readiness label
- what can be safely demonstrated
- what must not be claimed
- next phase recommendations:
  1. reduce review_required through safer parser/standardizer improvements
  2. improve evidence/source page display
  3. build lightweight UI around trusted/review_required split
  4. later consider production apply only after validation

## Required Assertions
- readable workbook exists
- trusted row count preserved
- review_required row count preserved
- no simulated rescue rows merged
- no safe_to_apply / approve_for_real_apply fields generated
- sandbox_apply_attempt_count = 0
- production_apply_attempt_count = 0
- check_delivery_state.py --json PASS
- production/official/formal/standardizer/release unchanged

Commit and push.
