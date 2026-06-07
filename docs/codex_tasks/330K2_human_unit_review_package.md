# 330K2 Human Unit Review Package

## Goal
Build a reviewer-facing package for the 21 `unit_review` rows from the 330L / 331A demo state.

This task is sidecar-only. It must not change production pipeline behavior, parser behavior, extraction behavior, delivery behavior, or official assets.

## Inputs
- `D:\_datefac\output\client_style_export_preview_330l`
- `D:\_datefac\output\client_style_export_preview_330l\client_style_export_preview_330l_preview.xlsx`
- `D:\_datefac\output\demo_packaging_331a`
- `D:\_datefac\output\unit_signal_review_330k`
- `D:\_datefac\output\delivery_report_refresh_after_330k_330j2`

## Expected Outputs
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_summary.json`
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_manifest.json`
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_qa.json`
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_no_apply_proof.json`
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_template.xlsx`
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_report.md`

## Implementation Scope
- New 330K2 demo / trust code only
- New runner only
- New tests only
- New `docs/codex_tasks` task doc only
- Do not modify production pipeline / parser / extraction / delivery files
- Do not modify official assets
- Do not touch existing dirty files

## Suggested Files
- `datefac/trust/human_unit_review_330k2.py`
- `datefac/trust/human_unit_review_330k2_report.py`
- `tools/run_human_unit_review_330k2.py`
- `tests/trust/test_human_unit_review_330k2.py`

## Review Workbook Requirements
The review workbook must package exactly the 21 unit review rows with enough context for a human reviewer:
- pdf / document id
- metric
- year
- value
- current unit
- `unit_missing` flag
- `unit_conflict_risk` flag
- source page
- source evidence / source text if available
- parser / provenance if available
- recommended reviewer action
- `reviewer_unit`
- `reviewer_decision`
- `reviewer_notes`

Allowed reviewer decisions:
- `CONFIRM_UNIT`
- `REJECT_UNIT`
- `KEEP_UNIT_UNKNOWN`
- `NEEDS_MORE_CONTEXT`

## Required Behavior
1. Validate 330L readiness:
   - `decision = CLIENT_STYLE_EXPORT_PREVIEW_330L_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_331A_DEMO_PACKAGING`
   - `qa_fail_count = 0`
   - `preview_workbook_generated = true`
   - `prepared_candidate_row_count = 117`
   - `strict_deduped_candidate_count = 117`
   - `unit_missing_count = 18`
   - `unit_conflict_risk_count = 12`
   - `delivery_readiness_judgment = DEMO_READY_WITH_UNIT_REVIEW_CAVEATS`
   - `no_official_asset_modification_during_330l = true`
2. Validate 331A demo packaging readiness where available:
   - `decision = DEMO_PACKAGING_331A_READY_FOR_PRESENTATION_AND_330K2_HUMAN_UNIT_REVIEW`
   - `qa_fail_count = 0`
3. Load the 21 review rows from the 330L / 330K reviewer-facing state.
4. Enrich the review rows with value / year / evidence / parser / provenance context when available from upstream cached artifacts.
5. Generate reviewer template workbook with conservative wording only.
6. Do not introduce production-ready or client-ready claims.
7. Do not introduce apply / write-back behavior.
8. Confirm official assets are unchanged.

## QA Requirements
QA must verify:
- exactly 21 unit review rows are packaged
- `source_page_missing_count` remains `0`
- `unit_missing_count` remains `18` if available from upstream
- `unit_conflict_risk_count` remains `12` if available from upstream
- no production / client-ready claims are introduced
- no apply / write-back behavior exists
- official assets are unchanged
- existing protected dirty files are not staged or altered by 330K2

## Expected Summary Fields
- `validated_330l_export_preview = true`
- `validated_331a_demo_packaging = true`
- `packaged_unit_review_row_count = 21`
- `review_template_workbook_generated = true`
- `source_page_missing_count = 0`
- `unit_missing_count = 18`
- `unit_conflict_risk_count = 12`
- `no_official_asset_modification_during_330k2 = true`
- `qa_fail_count = 0`
- `decision = HUMAN_UNIT_REVIEW_330K2_READY_FOR_MANUAL_REVIEW`

## Run
```powershell
python -m py_compile datefac\trust\human_unit_review_330k2.py datefac\trust\human_unit_review_330k2_report.py tools\run_human_unit_review_330k2.py tests\trust\test_human_unit_review_330k2.py

python -m pytest tests\trust\test_human_unit_review_330k2.py -q

python tools\run_human_unit_review_330k2.py --demo-packaging-dir D:\_datefac\output\demo_packaging_331a --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --unit-signal-review-dir D:\_datefac\output\unit_signal_review_330k --delivery-report-refresh-dir D:\_datefac\output\delivery_report_refresh_after_330k_330j2 --output-dir D:\_datefac\output\human_unit_review_330k2
```

## Git Constraints
- Use only precise `git add` for files created / modified by this task
- Do not use `git add -A`
- Do not use `git add .`

