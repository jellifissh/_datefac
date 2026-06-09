# 340C Human Review Apply Simulation After AI Adoption

## Goal

Create a sidecar dry-run apply simulation that reads the partially filled 340B human review workbook,
validates reviewer decisions, and generates an apply plan for the first manual-review batch.

This task is dry-run only.
It must not write back to 337D, 338D, 340B, or any upstream workbook.
It must not generate a refreshed client export.

## Inputs

- `D:/_datefac/output/human_review_after_ai_adoption_340b`
- `D:/_datefac/output/human_review_after_ai_adoption_340b/human_review_after_ai_adoption_340b_review_template.xlsx`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d`
- `D:/_datefac/output/ai_review_adoption_simulation_338d`

## Output Dir

- `D:/_datefac/output/human_review_apply_simulation_340c`

## Expected Artifacts

- `human_review_apply_simulation_340c_summary.json`
- `human_review_apply_simulation_340c_manifest.json`
- `human_review_apply_simulation_340c_qa.json`
- `human_review_apply_simulation_340c_no_apply_proof.json`
- `human_review_apply_simulation_340c_apply_plan.xlsx`
- `human_review_apply_simulation_340c_report.md`

## Dry-Run Boundary

- Do not modify the 340B review workbook.
- Do not modify 337D workbook.
- Do not modify 338D workbook.
- Do not modify other 340B outputs.
- Do not create refreshed client export.
- Do not write back to any source data.
- Do not modify production pipeline, parser, extraction, or delivery behavior.
- Do not modify official assets.

## Reviewer Decision Values

- `CONFIRM_AS_REVIEWED`
- `CORRECT_AND_CONFIRM`
- `KEEP_NEEDS_REVIEW`
- `REJECT`
- `NEEDS_MORE_CONTEXT`

## Validation Logic

1. Read sheet `01_REVIEW_QUEUE` from the 340B review workbook.
2. Detect rows where `reviewer_decision` is filled.
3. Validate each filled row:
   - `reviewer_decision` must be an allowed value.
   - `CORRECT_AND_CONFIRM` requires corrected fields needed for the correction.
   - corrected value must not be empty for `CORRECT_AND_CONFIRM`.
   - corrected unit must not be empty for revenue / net_profit style amount rows.
   - `REJECT` without `reviewer_notes` should raise a warning.
   - `NEEDS_MORE_CONTEXT` without `reviewer_notes` should raise a warning.
4. Unfilled rows remain pending and untouched.

## Expected Partial-Test State

- `total_review_queue_count = 77`
- `filled_review_row_count = 5`
- `pending_review_row_count = 72`
- `CORRECT_AND_CONFIRM = 3`
- `CONFIRM_AS_REVIEWED = 2`
- `qa_fail_count = 0` if the workbook is filled correctly

## Dry-Run Action Mapping

- `CONFIRM_AS_REVIEWED -> WOULD_CONFIRM_REVIEWED`
- `CORRECT_AND_CONFIRM -> WOULD_APPLY_CORRECTION_AND_CONFIRM`
- `KEEP_NEEDS_REVIEW -> WOULD_KEEP_NEEDS_REVIEW`
- `REJECT -> WOULD_REJECT`
- `NEEDS_MORE_CONTEXT -> WOULD_KEEP_NEEDS_MORE_CONTEXT`

## Output Workbook

Workbook:
- `human_review_apply_simulation_340c_apply_plan.xlsx`

Sheets:
1. `00_README`
2. `01_APPLY_PLAN`
3. `02_FILLED_REVIEW_ROWS`
4. `03_PENDING_REVIEW_ROWS`
5. `04_VALIDATION_WARNINGS`
6. `05_NO_APPLY_PROOF`
7. `06_SUMMARY`

`01_APPLY_PLAN` columns:
- `apply_plan_id`
- `review_id`
- `document`
- `metric_before`
- `year_before`
- `value_before`
- `unit_before`
- `reviewer_decision`
- `corrected_metric`
- `corrected_year`
- `corrected_value`
- `corrected_unit`
- `dry_run_action`
- `action_status`
- `validation_status`
- `reviewer_notes`
- `source_row_reference`

## Summary Requirements

Summary must include:
- `total_review_queue_count`
- `filled_review_row_count`
- `pending_review_row_count`
- `confirm_as_reviewed_count`
- `correct_and_confirm_count`
- `keep_needs_review_count`
- `reject_count`
- `needs_more_context_count`
- `validation_warning_count`
- `qa_fail_count`
- `no_write_back = true`
- `client_ready = false`
- `production_ready = false`
- `decision = HUMAN_REVIEW_APPLY_SIMULATION_340C_READY_FOR_PARTIAL_REVIEW_VALIDATION`

## QA Requirements

- Input review workbook exists.
- Sheet `01_REVIEW_QUEUE` exists.
- Filled rows are detected.
- Pending rows are counted.
- Apply plan is generated.
- No upstream workbook is modified.
- No write-back behavior exists.
- No client-ready claim is introduced.
- No production-ready claim is introduced.
- `qa_fail_count = 0` if validation passes.

## Files To Create

- `docs/codex_tasks/340C_human_review_apply_simulation_after_ai_adoption.md`
- `datefac/trust/human_review_apply_simulation_340c.py`
- `datefac/trust/human_review_apply_simulation_340c_report.py`
- `tools/run_human_review_apply_simulation_340c.py`
- `tests/trust/test_human_review_apply_simulation_340c.py`

## Run

```powershell
python -m py_compile datefac\trust\human_review_apply_simulation_340c.py datefac\trust\human_review_apply_simulation_340c_report.py tools\run_human_review_apply_simulation_340c.py tests\trust\test_human_review_apply_simulation_340c.py

python -m pytest tests\trust\test_human_review_apply_simulation_340c.py -q

python tools\run_human_review_apply_simulation_340c.py --human-review-340b-dir D:\_datefac\output\human_review_after_ai_adoption_340b --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --ai-adoption-338d-dir D:\_datefac\output\ai_review_adoption_simulation_338d --output-dir D:\_datefac\output\human_review_apply_simulation_340c
```
