# 340D Full Human Review Apply Plan

## Goal

Create a sidecar full human review apply plan that reads the fully filled 340B review workbook and the fully validated 340C apply simulation,
then produces a final dry-run human review application plan.

This task is still dry-run only.
It must not write back to 337D, 338D, 340B, or 340C.
It must not generate a client export yet.

## Inputs

- `D:/_datefac/output/human_review_after_ai_adoption_340b`
- `D:/_datefac/output/human_review_after_ai_adoption_340b/human_review_after_ai_adoption_340b_review_template.xlsx`
- `D:/_datefac/output/human_review_apply_simulation_340c`
- `D:/_datefac/output/human_review_apply_simulation_340c/human_review_apply_simulation_340c_apply_plan.xlsx`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d/real_test_mineru_client_export_337d.xlsx`
- `D:/_datefac/output/ai_review_adoption_simulation_338d`
- `D:/_datefac/output/ai_review_adoption_simulation_338d/ai_review_adoption_simulation_338d_plan.xlsx`

## Output Dir

- `D:/_datefac/output/full_human_review_apply_plan_340d`

## Expected Artifacts

- `full_human_review_apply_plan_340d_summary.json`
- `full_human_review_apply_plan_340d_manifest.json`
- `full_human_review_apply_plan_340d_qa.json`
- `full_human_review_apply_plan_340d_no_apply_proof.json`
- `full_human_review_apply_plan_340d_report.md`
- `full_human_review_apply_plan_340d.xlsx`

## No-Write-Back Boundary

- Do not modify 337D workbook.
- Do not modify 338D workbook.
- Do not modify 340B workbook.
- Do not modify 340C workbook.
- Do not create client export.
- Do not apply changes to official assets.
- Do not modify production pipeline, parser, extraction, or delivery behavior.

## Required Behavior

1. Read the fully filled 340B review workbook.
2. Read the 340C apply plan workbook and summary.
3. Confirm 340C is full-validation ready:
   - `filled_review_row_count = total_review_queue_count`
   - `pending_review_row_count = 0`
   - `validation_warning_count = 0`
   - `qa_fail_count = 0`
   - `decision = HUMAN_REVIEW_APPLY_SIMULATION_340C_READY_FOR_FULL_REVIEW_VALIDATION`
4. Convert reviewer decisions into final dry-run actions:
   - `CONFIRM_AS_REVIEWED -> FINAL_WOULD_CONFIRM_REVIEWED`
   - `CORRECT_AND_CONFIRM -> FINAL_WOULD_APPLY_CORRECTION_AND_CONFIRM`
   - `KEEP_NEEDS_REVIEW -> FINAL_WOULD_KEEP_NEEDS_REVIEW`
   - `REJECT -> FINAL_WOULD_REJECT`
   - `NEEDS_MORE_CONTEXT -> FINAL_WOULD_KEEP_NEEDS_MORE_CONTEXT`
5. Generate a final sidecar plan only.

## Final Route Mapping

- `FINAL_WOULD_CONFIRM_REVIEWED -> reviewed_after_human`
- `FINAL_WOULD_APPLY_CORRECTION_AND_CONFIRM -> reviewed_after_human_corrected`
- `FINAL_WOULD_REJECT -> rejected_after_human`
- `FINAL_WOULD_KEEP_NEEDS_REVIEW -> needs_review_after_human`
- `FINAL_WOULD_KEEP_NEEDS_MORE_CONTEXT -> needs_more_context_after_human`

## Output Workbook Sheets

1. `00_README`
2. `01_FINAL_APPLY_SUMMARY`
3. `02_FINAL_APPLY_PLAN`
4. `03_WOULD_CONFIRM_REVIEWED`
5. `04_WOULD_CORRECT_AND_CONFIRM`
6. `05_WOULD_REJECT`
7. `06_WOULD_KEEP_NEEDS_REVIEW`
8. `07_DUPLICATE_AND_UNIT_RISK_AUDIT`
9. `08_NO_APPLY_PROOF`
10. `09_NEXT_STEP_RECOMMENDATION`

## Sheet 02 Columns

- `final_apply_id`
- `review_id`
- `document`
- `source_sheet`
- `source_row_no`
- `metric_before`
- `year_before`
- `value_before`
- `unit_before`
- `reviewer_decision`
- `corrected_metric`
- `corrected_year`
- `corrected_value`
- `corrected_unit`
- `final_dry_run_action`
- `final_route_after_apply`
- `source_page`
- `evidence`
- `reviewer_notes`
- `risk_flags`
- `adoption_action_338d`
- `dry_run_action_340c`

## Summary Requirements

Summary should include:
- `total_review_queue_count = 77`
- `final_confirm_count = 22`
- `final_correct_and_confirm_count = 12`
- `final_reject_count = 31`
- `final_keep_needs_review_count = 12`
- `final_needs_more_context_count = 0`
- `final_reviewed_after_human_candidate_count = 34`
- `final_non_reviewed_after_human_count = 43`
- `no_write_back = true`
- `client_ready = false`
- `production_ready = false`
- `decision = FULL_HUMAN_REVIEW_APPLY_PLAN_340D_READY`

## QA Requirements

- Input 340B workbook exists.
- Input 340C apply plan exists.
- 340C decision is full-validation ready.
- All 77 review rows are represented.
- No pending review rows remain.
- Decision counts total 77.
- Corrected rows have required corrected fields.
- Money metrics corrected to non-empty money units.
- EPS corrected unit should remain non-empty where applicable.
- No upstream workbook is modified.
- No client-ready claim is introduced.
- No production-ready claim is introduced.
- `no_apply_proof` is generated.
- `qa_fail_count = 0`.

## Files

- `docs/codex_tasks/340D_full_human_review_apply_plan.md`
- `datefac/trust/full_human_review_apply_plan_340d.py`
- `datefac/trust/full_human_review_apply_plan_340d_report.py`
- `tools/run_full_human_review_apply_plan_340d.py`
- `tests/trust/test_full_human_review_apply_plan_340d.py`

## Run

```powershell
python -m py_compile datefac\trust\full_human_review_apply_plan_340d.py datefac\trust\full_human_review_apply_plan_340d_report.py tools\run_full_human_review_apply_plan_340d.py tests\trust\test_full_human_review_apply_plan_340d.py

python -m pytest tests\trust\test_full_human_review_apply_plan_340d.py -q

python tools\run_full_human_review_apply_plan_340d.py --human-review-340b-dir D:\_datefac\output\human_review_after_ai_adoption_340b --human-review-apply-340c-dir D:\_datefac\output\human_review_apply_simulation_340c --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --ai-adoption-338d-dir D:\_datefac\output\ai_review_adoption_simulation_338d --output-dir D:\_datefac\output\full_human_review_apply_plan_340d
```
