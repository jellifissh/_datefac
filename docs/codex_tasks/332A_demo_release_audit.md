# 332A Demo Release Audit

## Goal
Create a final demo release audit package for the 331B reviewed preview demo state.

This task audits presentation, README, resume, and demo-script consistency plus overclaim risk. It must not change production pipeline, parser / extraction / delivery behavior, official assets, or any prior output artifacts.

## Inputs
- `D:\_datefac\output\demo_packaging_331b`
- `D:\_datefac\output\reviewed_export_refresh_330k4`
- `D:\_datefac\output\demo_packaging_331a`
- `D:\_datefac\docs\demo\datefac_demo_overview_331b.md`
- `D:\_datefac\docs\demo\datefac_resume_bullets_331b.md`
- `D:\_datefac\docs\demo\datefac_github_readme_section_331b.md`
- `D:\_datefac\docs\demo\datefac_demo_script_331b.md`

## Expected Output Dir
- `D:\_datefac\output\demo_release_audit_332a`

## Expected Artifacts
- `demo_release_audit_332a_summary.json`
- `demo_release_audit_332a_manifest.json`
- `demo_release_audit_332a_qa.json`
- `demo_release_audit_332a_no_apply_proof.json`
- `demo_release_audit_332a_checklist.md`
- `demo_release_audit_332a_report.md`

## Optional Repo Docs To Generate
- `docs/demo/datefac_demo_release_checklist_332a.md`
- `docs/demo/datefac_interview_talking_points_332a.md`

## Current Expected Demo State
- `project_status = DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW`
- `client_ready = false`
- `production_ready = false`
- `original_trusted_sheet_row_count = 96`
- `reviewed_unit_confirmed_count = 2`
- `reviewed_trusted_preview_row_count = 98`
- `human_rejected_row_count = 18`
- `remaining_review_required_after_unit_review_count = 1`
- `apply_plan_row_count = 21`
- `qa_fail_count = 0`

## Audit Requirements
- Verify all 331B docs exist.
- Verify 331B output summary exists and `qa_fail_count = 0`.
- Verify 330K4 summary exists and reviewed counts match expected values.
- Verify all demo docs consistently say not client-ready and not production-ready.
- Verify docs do not claim production deployment, client delivery readiness, guaranteed extraction accuracy, automatic correctness, or full-scale commercial readiness.
- Verify docs mention sidecar, demo, preview, and no-write-back boundaries.
- Verify metrics are consistent across overview, resume bullets, README section, and demo script.
- Generate a checklist that separates:
  1. Safe to show on GitHub
  2. Safe to say in interview
  3. Must not claim
  4. Known limitations
  5. Suggested next engineering milestones
- Generate interview talking points explaining:
  - why parser quality alone is not enough
  - why unit review matters
  - how trust routing works
  - why human review is deliberately isolated before write-back
  - what changed from 331A to 331B

## Required Behavior
1. Validate 331B readiness:
   - `decision = DEMO_PACKAGING_331B_READY_FOR_PRESENTATION_REFRESH`
   - `qa_fail_count = 0`
   - `project_status = DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW`
   - `client_ready = false`
   - `production_ready = false`
2. Validate 330K4 readiness:
   - `decision = REVIEWED_EXPORT_REFRESH_330K4_READY_FOR_PREVIEW_REVIEW`
   - `qa_fail_count = 0`
   - `reviewed_trusted_preview_row_count = 98`
   - `human_rejected_row_count = 18`
   - `remaining_review_required_after_unit_review_count = 1`
   - `apply_plan_row_count = 21`
3. Validate 331A baseline readiness:
   - `decision = DEMO_PACKAGING_331A_READY_FOR_PRESENTATION_AND_330K2_HUMAN_UNIT_REVIEW`
   - `qa_fail_count = 0`
4. Read and audit the four 331B demo docs.
5. Generate checklist and report artifacts under the output dir.
6. Optionally generate the two 332A helper docs under `docs/demo`.
7. Confirm all audited metrics stay consistent with 331B and 330K4 summaries.
8. Confirm no overclaim language is introduced.
9. Confirm official assets remain unchanged.
10. Confirm protected dirty files remain unstaged.

## Protected Dirty Files
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## Expected Summary Fields
- `validated_331b_demo_packaging = true`
- `validated_330k4_reviewed_export_refresh = true`
- `validated_331a_demo_packaging = true`
- `project_status = DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW`
- `client_ready = false`
- `production_ready = false`
- `reviewed_trusted_preview_row_count = 98`
- `human_rejected_row_count = 18`
- `remaining_review_required_after_unit_review_count = 1`
- `apply_plan_row_count = 21`
- `doc_consistency_passed = true`
- `overclaim_risk_count = 0`
- `no_official_asset_modification_during_332a = true`
- `qa_fail_count = 0`
- `decision = DEMO_RELEASE_AUDIT_332A_READY_FOR_FINAL_DEMO_USE`

## Suggested Files
- `datefac/trust/demo_release_audit_332a.py`
- `datefac/trust/demo_release_audit_332a_report.py`
- `tools/run_demo_release_audit_332a.py`
- `tests/trust/test_demo_release_audit_332a.py`

## Run
```powershell
python -m py_compile datefac\trust\demo_release_audit_332a.py datefac\trust\demo_release_audit_332a_report.py tools\run_demo_release_audit_332a.py tests\trust\test_demo_release_audit_332a.py

python -m pytest tests\trust\test_demo_release_audit_332a.py -q

python tools\run_demo_release_audit_332a.py --demo-packaging-331b-dir D:\_datefac\output\demo_packaging_331b --reviewed-export-refresh-dir D:\_datefac\output\reviewed_export_refresh_330k4 --demo-packaging-331a-dir D:\_datefac\output\demo_packaging_331a --docs-demo-dir D:\_datefac\docs\demo --output-dir D:\_datefac\output\demo_release_audit_332a
```

## Git Constraints
- Use only precise `git add` for files created by this task
- Do not use `git add -A`
- Do not use `git add .`
- Do not commit output artifacts
