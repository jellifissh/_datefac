# 331B Demo Packaging Refresh After Human Unit Review

## Goal
Refresh the 331A demo packaging using the 330K4 reviewed export refresh.

This remains a sidecar demo packaging refresh only. It must not modify production pipeline behavior, parser / extraction / delivery behavior, original 330L / 331A / 330K4 output artifacts, or official assets.

## Inputs
- `D:\_datefac\output\demo_packaging_331a`
- `D:\_datefac\output\reviewed_export_refresh_330k4`
- `D:\_datefac\output\human_unit_review_apply_simulation_330k3`
- `D:\_datefac\output\human_unit_review_330k2`
- `D:\_datefac\output\client_style_export_preview_330l`

## Expected Output Dir
- `D:\_datefac\output\demo_packaging_331b`

## Expected Artifacts
- `demo_packaging_331b_summary.json`
- `demo_packaging_331b_manifest.json`
- `demo_packaging_331b_qa.json`
- `demo_packaging_331b_no_apply_proof.json`
- `demo_packaging_331b_summary.xlsx`
- `demo_packaging_331b_report.md`

## Repo Docs To Generate
- `docs/demo/datefac_demo_overview_331b.md`
- `docs/demo/datefac_resume_bullets_331b.md`
- `docs/demo/datefac_github_readme_section_331b.md`
- `docs/demo/datefac_demo_script_331b.md`

## Project Status
- `project_status = DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW`
- `client_ready = false`
- `production_ready = false`

## Core Metrics Expected From 330K4
- `original_trusted_sheet_row_count = 96`
- `reviewed_unit_confirmed_count = 2`
- `reviewed_trusted_preview_row_count = 98`
- `human_rejected_row_count = 18`
- `remaining_review_required_after_unit_review_count = 1`
- `apply_plan_row_count = 21`
- `qa_fail_count = 0`

## Packaging Narrative
- 331A was demo-ready with unit review caveats.
- 330K2 packaged 21 unit-review rows for manual review.
- 330K3 simulated applying the review decisions without write-back.
- 330K4 generated a reviewed preview export:
  - 2 confirmed rows added or surfaced into reviewed trusted preview
  - 18 rejected rows isolated from trusted preview
  - 1 row remains review-required for source check
- 331B packages this reviewed preview state for demo, README, resume, and script usage.
- Do not claim client-ready or production-ready.

## Required Behavior
1. Validate 331A demo packaging readiness:
   - `decision = DEMO_PACKAGING_331A_READY_FOR_PRESENTATION_AND_330K2_HUMAN_UNIT_REVIEW`
   - `qa_fail_count = 0`
   - `project_status = DEMO_READY_WITH_UNIT_REVIEW_CAVEATS`
2. Validate 330K4 reviewed export refresh readiness:
   - `decision = REVIEWED_EXPORT_REFRESH_330K4_READY_FOR_PREVIEW_REVIEW`
   - `qa_fail_count = 0`
   - `reviewed_trusted_preview_row_count = 98`
   - `human_rejected_row_count = 18`
   - `remaining_review_required_after_unit_review_count = 1`
   - `apply_plan_row_count = 21`
3. Read 330K3 / 330K2 / 330L summaries as supporting context.
4. Generate new 331B docs that describe the reviewed preview state without overclaiming.
5. Generate summary, manifest, QA, no-apply proof, workbook, and markdown report.
6. Preserve sidecar-only wording and explicit non-production / non-client boundaries.
7. Confirm original 330L / 331A / 330K4 input artifacts remain unchanged before vs after 331B.
8. Confirm official assets remain unchanged.
9. Confirm protected dirty files remain unstaged.

## QA Requirements
QA must verify:
- 331A demo package exists and was ready
- 330K4 reviewed export refresh exists and `qa_fail_count = 0`
- `reviewed_trusted_preview_row_count = 98`
- `human_rejected_row_count = 18`
- `remaining_review_required_after_unit_review_count = 1`
- `apply_plan_row_count = 21`
- generated docs do not overclaim production-ready or client-ready
- no production-ready or client-ready claims are introduced
- official assets are unchanged
- protected dirty files remain unstaged
- no write-back behavior exists
- all required artifacts exist

## Protected Dirty Files
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## Expected Summary Fields
- `validated_331a_demo_packaging = true`
- `validated_330k4_reviewed_export_refresh = true`
- `project_status = DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW`
- `client_ready = false`
- `production_ready = false`
- `original_trusted_sheet_row_count = 96`
- `reviewed_unit_confirmed_count = 2`
- `reviewed_trusted_preview_row_count = 98`
- `human_rejected_row_count = 18`
- `remaining_review_required_after_unit_review_count = 1`
- `apply_plan_row_count = 21`
- `no_official_asset_modification_during_331b = true`
- `qa_fail_count = 0`
- `decision = DEMO_PACKAGING_331B_READY_FOR_PRESENTATION_REFRESH`

## Suggested Files
- `datefac/trust/demo_packaging_331b.py`
- `datefac/trust/demo_packaging_331b_report.py`
- `tools/run_demo_packaging_331b.py`
- `tests/trust/test_demo_packaging_331b.py`

## Run
```powershell
python -m py_compile datefac\trust\demo_packaging_331b.py datefac\trust\demo_packaging_331b_report.py tools\run_demo_packaging_331b.py tests\trust\test_demo_packaging_331b.py

python -m pytest tests\trust\test_demo_packaging_331b.py -q

python tools\run_demo_packaging_331b.py --demo-packaging-331a-dir D:\_datefac\output\demo_packaging_331a --reviewed-export-refresh-dir D:\_datefac\output\reviewed_export_refresh_330k4 --apply-simulation-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3 --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --output-dir D:\_datefac\output\demo_packaging_331b
```

## Git Constraints
- Use only precise `git add` for files created by this task
- Do not use `git add -A`
- Do not use `git add .`
- Do not commit output Excel / JSON artifacts
