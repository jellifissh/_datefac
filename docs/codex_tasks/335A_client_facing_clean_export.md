# 335A Client-Facing Clean Export

## Goal
Generate a customer-facing clean Excel export from the `330K4` reviewed export refresh.

This is a sidecar client-preview export only. It should make the data easier for a non-engineering customer to inspect, while preserving source traceability and risk boundaries.

## Prerequisite
- `334B` shim-first root utility migration must already be committed and pushed.
- If `334B` is still uncommitted, stop and report:
  - `334B should be committed and pushed before starting 335A.`

## Required Current Demo Line
- `330L` client-style export preview
- `331A` demo packaging
- `330K2` human unit review package
- `330K3` human unit review apply simulation
- `330K4` reviewed export refresh
- `331B` demo packaging refresh after human unit review
- `332A` demo release audit
- `333A` bilingual README and operator guides
- `334A` repository layout audit
- `334B` shim-first root utility migration

## Boundaries
This task must not modify:
- production pipeline
- parser / extraction / delivery behavior
- official assets
- `330L / 331A / 330K2 / 330K3 / 330K4 / 331B / 332A` output artifacts
- protected dirty files

This task must not claim:
- `client_ready = true`
- `production_ready = true`
- `100% accuracy`
- fully automatic delivery
- investment-decision readiness

## Required Wording
Use:
- `client_facing_preview = true`
- `client_ready = false`
- `production_ready = false`
- `project_status = CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY`

Describe the result as:
- `client-facing clean preview export`

Do not describe it as:
- production client delivery
- client-ready automated delivery

## Inputs
- `D:/_datefac/output/reviewed_export_refresh_330k4`
- `D:/_datefac/output/reviewed_export_refresh_330k4/reviewed_export_refresh_330k4_preview.xlsx`
- `D:/_datefac/output/demo_packaging_331b`
- `D:/_datefac/output/demo_release_audit_332a`
- `D:/_datefac/output/client_style_export_preview_330l`

## Output Directory
- `D:/_datefac/output/client_facing_clean_export_335a`

## Expected Artifacts
- `client_facing_clean_export_335a_summary.json`
- `client_facing_clean_export_335a_manifest.json`
- `client_facing_clean_export_335a_qa.json`
- `client_facing_clean_export_335a_no_apply_proof.json`
- `client_facing_clean_export_335a_preview.xlsx`
- `client_facing_clean_export_335a_report.md`

## Expected Source Workbook Sheets From 330K4
- `00_README`
- `01_REVIEWED_TRUSTED_PREVIEW`
- `02_REMAINING_REVIEW_REQUIRED`
- `03_HUMAN_REJECTED_BY_UNIT_REV`
- `04_APPLY_PLAN_TRACE`
- `05_QA_CONTEXT`

## New Customer-Facing Workbook Sheets
1. `00_README_FOR_CUSTOMER`
2. `01_CORE_METRICS_REVIEWED`
3. `02_NEEDS_REVIEW`
4. `03_EXCLUDED_OR_REJECTED`
5. `04_SOURCE_TRACE`
6. `05_DELIVERY_SUMMARY`

## Workbook Design Principles
- Hide internal engineering noise.
- Do not expose `dry_run_action`, `preview_routing_bucket`, sidecar internals, or `330K` stage names in main customer-facing sheets.
- Keep `source_page` and evidence text because traceability matters.
- Keep internal row id / candidate id only in `04_SOURCE_TRACE`, not in the main reviewed sheet when avoidable.
- Make status labels easy to understand.
- Preserve enough traceability for manual checking.
- Do not mutate upstream workbooks.

## Sheet Requirements

### 00_README_FOR_CUSTOMER
Explain in plain language:
- This workbook is a clean preview export generated from financial research PDF extraction.
- Reviewed rows are the safest rows in this demo state.
- Needs-review rows should be checked manually before use.
- Excluded/rejected rows are kept for transparency and should not be treated as trusted.
- This workbook is for data organization and review assistance, not investment advice.
- This is not a production-ready or client-ready automated delivery system.
- Source pages and evidence text are included for checking.

### 01_CORE_METRICS_REVIEWED
Source:
- `330K4` sheet `01_REVIEWED_TRUSTED_PREVIEW`

Columns:
- `row_no`
- `document`
- `metric`
- `year`
- `value`
- `unit`
- `source_page`
- `confidence_status`
- `review_status`
- `source_evidence`
- `notes`

Mapping guidance:
- `document`: `pdf_document_id`, fallback `source_pdf`
- `metric`: `normalized_metric`, fallback `metric_label_raw`
- `year`: `year`
- `value`: `value`
- `unit`: `final_unit_preview`, fallback `reviewer_unit`, fallback `current_unit`
- `source_page`: `source_page`
- `confidence_status`: `reviewed_trusted_preview`
- `review_status`:
  - baseline trusted rows => `system_trusted`
  - human confirmed rows => `human_unit_confirmed`
- `source_evidence`: `source_evidence_text`
- `notes`:
  - baseline trusted rows => `High-confidence preview row from trust routing.`
  - human confirmed rows => `Unit reviewed and confirmed during manual unit review.`

Expected row count:
- `reviewed_trusted_preview_row_count = 98`

### 02_NEEDS_REVIEW
Source:
- `330K4` sheet `02_REMAINING_REVIEW_REQUIRED`

Columns:
- `row_no`
- `document`
- `metric`
- `year`
- `value`
- `current_unit`
- `source_page`
- `review_reason`
- `source_evidence`
- `recommended_action`
- `notes`

Expected row count:
- `remaining_review_required_after_unit_review_count = 1`

### 03_EXCLUDED_OR_REJECTED
Source:
- `330K4` sheet `03_HUMAN_REJECTED_BY_UNIT_REV`

Columns:
- `row_no`
- `document`
- `metric`
- `year`
- `value`
- `current_unit`
- `source_page`
- `rejection_reason`
- `source_evidence`
- `reviewer_notes`
- `notes`

Expected row count:
- `human_rejected_row_count = 18`

Important:
- Rows in `03_EXCLUDED_OR_REJECTED` must never appear in `01_CORE_METRICS_REVIEWED`.

### 04_SOURCE_TRACE
Source:
- `330K4` sheet `04_APPLY_PLAN_TRACE` plus relevant source fields from reviewed / remaining / rejected sheets

Columns:
- `trace_id`
- `internal_candidate_id`
- `document`
- `metric`
- `year`
- `value`
- `unit`
- `source_page`
- `source_evidence_refs`
- `source_evidence_text`
- `customer_sheet`
- `customer_row_no`
- `trace_status`
- `internal_review_decision`

This sheet may include `internal_candidate_id` because it is for audit traceability.

### 05_DELIVERY_SUMMARY
Include:
- `project_status = CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY`
- `client_facing_preview = true`
- `client_ready = false`
- `production_ready = false`
- `source_reviewed_trusted_preview_row_count = 98`
- `core_metrics_reviewed_row_count = 98`
- `needs_review_row_count = 1`
- `excluded_or_rejected_row_count = 18`
- `source_page_missing_count` should be `0` if available
- `qa_fail_count = 0`
- `generated_at`
- `source_output_dir = D:/_datefac/output/reviewed_export_refresh_330k4`

Also include safe usage notes:
- Use reviewed rows as the safest preview output.
- Review needs-review rows before using them.
- Do not use excluded / rejected rows as trusted data.
- Verify critical numbers against source PDFs before business or investment use.

## Formatting
- Use `openpyxl` formatting if reasonable.
- Freeze top row on all sheets.
- Apply autofilter to all sheets.
- Set readable column widths.
- Bold header rows.
- Do not introduce heavy dependencies.
- Do not use LibreOffice.
- Do not require manual Excel operations.

## Implementation Scope
- New sidecar trust / demo code only
- New runner only
- New tests only
- New `docs/codex_tasks` task doc only
- Optional docs/demo client export note only if genuinely useful
- Do not modify production pipeline / parser / extraction / delivery files
- Do not modify official assets
- Do not modify output artifacts except writing the new `335A` output dir
- Do not modify or stage protected dirty files
- Do not commit generated output Excel / JSON artifacts

## Expected Source Metrics From 330K4
- `original_trusted_sheet_row_count = 96`
- `reviewed_unit_confirmed_count = 2`
- `reviewed_trusted_preview_row_count = 98`
- `human_rejected_row_count = 18`
- `remaining_review_required_after_unit_review_count = 1`
- `apply_plan_row_count = 21`
- `qa_fail_count = 0`

## QA Requirements
- `330K4` reviewed export refresh summary exists
- `330K4` reviewed export refresh QA fail count is `0`
- `330K4` preview workbook exists
- `01_REVIEWED_TRUSTED_PREVIEW` has `98` rows
- `02_REMAINING_REVIEW_REQUIRED` has `1` row
- `03_HUMAN_REJECTED_BY_UNIT_REV` has `18` rows
- `04_APPLY_PLAN_TRACE` exists
- customer workbook is generated
- customer reviewed sheet has `98` rows
- customer needs-review sheet has `1` row
- customer excluded / rejected sheet has `18` rows
- no rejected `candidate_id` appears in the reviewed customer sheet
- no needs-review `candidate_id` appears in the reviewed customer sheet
- main customer-facing sheets do not expose `dry_run_action` or `preview_routing_bucket`
- source trace sheet preserves `internal_candidate_id`
- no production-ready / client-ready positive claims are introduced
- official assets are unchanged
- protected dirty files remain unstaged
- no write-back behavior exists

## Files To Create
- `docs/codex_tasks/335A_client_facing_clean_export.md`
- `datefac/trust/client_facing_clean_export_335a.py`
- `datefac/trust/client_facing_clean_export_335a_report.py`
- `tools/run_client_facing_clean_export_335a.py`
- `tests/trust/test_client_facing_clean_export_335a.py`

## Commands
```powershell
python -m py_compile datefac\trust\client_facing_clean_export_335a.py datefac\trust\client_facing_clean_export_335a_report.py tools\run_client_facing_clean_export_335a.py tests\trust\test_client_facing_clean_export_335a.py

python -m pytest tests\trust\test_client_facing_clean_export_335a.py -q

python tools\run_client_facing_clean_export_335a.py --reviewed-export-refresh-dir D:\_datefac\output\reviewed_export_refresh_330k4 --demo-packaging-331b-dir D:\_datefac\output\demo_packaging_331b --demo-release-audit-dir D:\_datefac\output\demo_release_audit_332a --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --output-dir D:\_datefac\output\client_facing_clean_export_335a
```

## Protected Dirty Files
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## Reporting Requirements
After completion, report:
- files changed
- output dir
- generated workbook path
- row counts by customer sheet
- QA result
- tests run
- `py_compile` result
- `git status -sb`
- confirm protected dirty files remain unstaged
