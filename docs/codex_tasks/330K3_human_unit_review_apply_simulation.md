# 330K3 Human Unit Review Apply Simulation

## Goal
Read the manually filled 330K2 review workbook and generate a dry-run apply simulation.

This task is sidecar-only. It must not write back to the 330L workbook, must not refresh the client-style export, must not modify production pipeline / parser / extraction / delivery behavior, and must not modify official assets.

## Input Filled Review Workbook
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_filled.xlsx`

## Upstream Context
- `D:\_datefac\output\human_unit_review_330k2`
- `D:\_datefac\output\demo_packaging_331a`
- `D:\_datefac\output\client_style_export_preview_330l`

## Expected Output Dir
- `D:\_datefac\output\human_unit_review_apply_simulation_330k3`

## Expected Artifacts
- `human_unit_review_apply_simulation_330k3_summary.json`
- `human_unit_review_apply_simulation_330k3_manifest.json`
- `human_unit_review_apply_simulation_330k3_qa.json`
- `human_unit_review_apply_simulation_330k3_no_apply_proof.json`
- `human_unit_review_apply_simulation_330k3_apply_plan.json`
- `human_unit_review_apply_simulation_330k3_apply_plan.xlsx`
- `human_unit_review_apply_simulation_330k3_report.md`

## Expected Reviewed Decision Counts
- `reviewed_row_count = 21`
- `REJECT_UNIT = 18`
- `CONFIRM_UNIT = 2`
- `NEEDS_MORE_CONTEXT = 1`
- `KEEP_UNIT_UNKNOWN = 0`

## Allowed reviewer_decision Values
- `CONFIRM_UNIT`
- `REJECT_UNIT`
- `KEEP_UNIT_UNKNOWN`
- `NEEDS_MORE_CONTEXT`

## Dry-Run Action Mapping
- `CONFIRM_UNIT -> WOULD_CONFIRM_OR_SET_UNIT`
- `REJECT_UNIT -> WOULD_REJECT_FROM_TRUSTED_EXPORT`
- `KEEP_UNIT_UNKNOWN -> WOULD_KEEP_UNIT_UNKNOWN_REVIEW_REQUIRED`
- `NEEDS_MORE_CONTEXT -> WOULD_KEEP_REVIEW_REQUIRED_FOR_SOURCE_CHECK`

## Implementation Scope
- New sidecar trust / demo code only
- New runner only
- New tests only
- New `docs/codex_tasks` task doc only
- Do not modify production pipeline / parser / extraction / delivery files
- Do not modify official assets
- Do not modify or stage protected dirty files
- Do not commit output Excel / JSON artifacts

## Suggested Files
- `datefac/trust/human_unit_review_apply_simulation_330k3.py`
- `datefac/trust/human_unit_review_apply_simulation_330k3_report.py`
- `tools/run_human_unit_review_apply_simulation_330k3.py`
- `tests/trust/test_human_unit_review_apply_simulation_330k3.py`

## Required Behavior
1. Validate 330K2 readiness:
   - `decision = HUMAN_UNIT_REVIEW_330K2_READY_FOR_MANUAL_REVIEW`
   - `qa_fail_count = 0`
   - `packaged_unit_review_row_count = 21`
2. Validate the filled review workbook exists.
3. Load exactly 21 reviewed rows from the filled workbook.
4. Validate all `reviewer_decision` values are allowed and non-blank.
5. Validate the decision counts match the expected distribution.
6. Generate a 21-row dry-run apply plan with no write-back behavior.
7. Confirm no production-ready / client-ready claims are introduced.
8. Confirm official assets are unchanged.
9. Confirm protected dirty files remain unstaged.

## QA Requirements
QA must verify:
- filled review workbook exists
- exactly 21 review rows are loaded
- reviewer_decision values are all allowed
- no blank reviewer_decision exists
- decision counts match expected values
- dry-run apply plan has exactly 21 rows
- no write-back behavior exists
- no production-ready / client-ready claims are introduced
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
- `validated_330k2_review_package = true`
- `reviewed_row_count = 21`
- `confirm_unit_count = 2`
- `reject_unit_count = 18`
- `needs_more_context_count = 1`
- `keep_unit_unknown_count = 0`
- `apply_plan_row_count = 21`
- `no_official_asset_modification_during_330k3 = true`
- `qa_fail_count = 0`
- `decision = HUMAN_UNIT_REVIEW_APPLY_SIMULATION_330K3_READY_FOR_REVIEW_SUMMARY_AND_NEXT_STEP_DECISION`

## Run
```powershell
python -m py_compile datefac\trust\human_unit_review_apply_simulation_330k3.py datefac\trust\human_unit_review_apply_simulation_330k3_report.py tools\run_human_unit_review_apply_simulation_330k3.py tests\trust\test_human_unit_review_apply_simulation_330k3.py

python -m pytest tests\trust\test_human_unit_review_apply_simulation_330k3.py -q

python tools\run_human_unit_review_apply_simulation_330k3.py --filled-review-workbook D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_filled.xlsx --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --demo-packaging-dir D:\_datefac\output\demo_packaging_331a --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --output-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3
```

## Git Constraints
- Use only precise `git add` for files created by this task
- Do not use `git add -A`
- Do not use `git add .`

