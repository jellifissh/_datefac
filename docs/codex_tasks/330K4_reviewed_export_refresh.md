# 330K4 Reviewed Export Refresh

## Goal
Generate a reviewed export preview from the 330L client-style export preview and the 330K3 dry-run apply plan.

This stage remains a sidecar preview refresh only. It must not modify the original 330L workbook, production pipeline, parser / extraction / delivery behavior, or official assets.

## Inputs
- `D:\_datefac\output\client_style_export_preview_330l`
- `D:\_datefac\output\client_style_export_preview_330l\client_style_export_preview_330l_preview.xlsx`
- `D:\_datefac\output\human_unit_review_330k2`
- `D:\_datefac\output\human_unit_review_apply_simulation_330k3`

## Expected Output Dir
- `D:\_datefac\output\reviewed_export_refresh_330k4`

## Expected Artifacts
- `reviewed_export_refresh_330k4_summary.json`
- `reviewed_export_refresh_330k4_manifest.json`
- `reviewed_export_refresh_330k4_qa.json`
- `reviewed_export_refresh_330k4_no_apply_proof.json`
- `reviewed_export_refresh_330k4_preview.xlsx`
- `reviewed_export_refresh_330k4_report.md`

## Workbook Sheets
- `00_README`
- `01_REVIEWED_TRUSTED_PREVIEW`
- `02_REMAINING_REVIEW_REQUIRED`
- `03_HUMAN_REJECTED_BY_UNIT_REV`
- `04_APPLY_PLAN_TRACE`
- `05_QA_CONTEXT`

Note:
- The original longer label `03_HUMAN_REJECTED_BY_UNIT_REVIEW` exceeds the Excel 31-character sheet-name limit.
- The workbook therefore uses the Excel-safe alias `03_HUMAN_REJECTED_BY_UNIT_REV`.

## Expected Human Review Decision Counts From 330K3
- `apply_plan_row_count = 21`
- `CONFIRM_UNIT = 2`
- `REJECT_UNIT = 18`
- `NEEDS_MORE_CONTEXT = 1`
- `KEEP_UNIT_UNKNOWN = 0`

## Refresh Behavior
- Start from the 330L trusted sheet as baseline.
- Add or surface `CONFIRM_UNIT` rows as reviewed unit-confirmed preview rows.
- Put `REJECT_UNIT` rows into `03_HUMAN_REJECTED_BY_UNIT_REVIEW`, not trusted.
- Put `NEEDS_MORE_CONTEXT` and `KEEP_UNIT_UNKNOWN` rows into `02_REMAINING_REVIEW_REQUIRED`.
- Preserve traceability to `candidate_id`, `pdf_document_id`, metric, year, value, source_page, source evidence, `reviewer_unit`, `reviewer_decision`, `reviewer_notes`, and `dry_run_action`.
- Do not write back to 330L.
- Do not overwrite 331A or 330K3 outputs.
- Do not claim client-ready or production-ready.

## Suggested Derived Counts
- `original_trusted_sheet_row_count = 96`
- `reviewed_unit_confirmed_count = 2`
- `human_rejected_row_count = 18`
- `remaining_review_required_after_unit_review_count = 1`
- `reviewed_trusted_preview_row_count` should equal original trusted rows plus reviewed unit-confirmed preview rows unless QA finds duplicate `candidate_id` overlap or another blocker.

## Required Behavior
1. Validate 330L readiness:
   - `decision = CLIENT_STYLE_EXPORT_PREVIEW_330L_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_331A_DEMO_PACKAGING`
   - `qa_fail_count = 0`
   - `trusted_sheet_row_count = 96`
   - `review_required_sheet_row_count = 21`
2. Validate 330K3 readiness:
   - `decision = HUMAN_UNIT_REVIEW_APPLY_SIMULATION_330K3_READY_FOR_REVIEW_SUMMARY_AND_NEXT_STEP_DECISION`
   - `qa_fail_count = 0`
   - `apply_plan_row_count = 21`
   - `confirm_unit_count = 2`
   - `reject_unit_count = 18`
   - `needs_more_context_count = 1`
   - `keep_unit_unknown_count = 0`
3. Read the 330L preview workbook and the 330K3 apply plan.
4. Read the filled 330K2 workbook from:
   - `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_filled.xlsx`
5. Generate the reviewed preview workbook with exactly the required six sheets.
6. Keep the 330L trusted baseline rows in the reviewed trusted preview.
7. Append only non-duplicate `CONFIRM_UNIT` rows into the reviewed trusted preview.
8. Route `REJECT_UNIT` rows to the human rejected sheet only.
9. Route `NEEDS_MORE_CONTEXT` and `KEEP_UNIT_UNKNOWN` rows to remaining review required.
10. Preserve traceability and dry-run provenance in the workbook and summary artifacts.
11. Confirm no write-back behavior exists and no official assets are modified.
12. Confirm protected dirty files remain unstaged.

## QA Requirements
QA must verify:
- 330L preview workbook exists
- 330K3 apply plan exists
- apply plan has exactly 21 rows
- decision counts match expected values
- `REJECT_UNIT` rows are not included in reviewed trusted preview
- `NEEDS_MORE_CONTEXT` rows remain review required
- reviewed preview workbook is generated
- no production-ready or client-ready claims are introduced
- no write-back behavior exists
- official assets are unchanged
- protected dirty files remain unstaged

## Protected Dirty Files
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## Expected Summary Fields
- `validated_330l_preview = true`
- `validated_330k3_apply_simulation = true`
- `original_trusted_sheet_row_count = 96`
- `reviewed_unit_confirmed_count = 2`
- `human_rejected_row_count = 18`
- `remaining_review_required_after_unit_review_count = 1`
- `reviewed_trusted_preview_row_count = 98`
- `duplicate_confirmed_candidate_overlap_count = 0`
- `apply_plan_row_count = 21`
- `no_official_asset_modification_during_330k4 = true`
- `qa_fail_count = 0`
- `decision = REVIEWED_EXPORT_REFRESH_330K4_READY_FOR_PREVIEW_REVIEW`

## Suggested Files
- `datefac/trust/reviewed_export_refresh_330k4.py`
- `datefac/trust/reviewed_export_refresh_330k4_report.py`
- `tools/run_reviewed_export_refresh_330k4.py`
- `tests/trust/test_reviewed_export_refresh_330k4.py`

## Run
```powershell
python -m py_compile datefac\trust\reviewed_export_refresh_330k4.py datefac\trust\reviewed_export_refresh_330k4_report.py tools\run_reviewed_export_refresh_330k4.py tests\trust\test_reviewed_export_refresh_330k4.py

python -m pytest tests\trust\test_reviewed_export_refresh_330k4.py -q

python tools\run_reviewed_export_refresh_330k4.py --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --apply-simulation-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3 --output-dir D:\_datefac\output\reviewed_export_refresh_330k4
```

## Git Constraints
- Use only precise `git add` for files created by this task
- Do not use `git add -A`
- Do not use `git add .`
- Do not commit output Excel / JSON artifacts
