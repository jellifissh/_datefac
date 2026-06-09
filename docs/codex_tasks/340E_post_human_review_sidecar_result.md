# 340E Post-Human-Review Sidecar Result

## Goal

Create a post-human-review sidecar result from the final 340D dry-run apply plan.
This task produces a new sidecar result package only.

It must not write back to any upstream workbook.
It must not generate a client export.
It must not modify official assets.

## Inputs

- `D:/_datefac/output/full_human_review_apply_plan_340d`
- `D:/_datefac/output/full_human_review_apply_plan_340d/full_human_review_apply_plan_340d.xlsx`

## Output Dir

- `D:/_datefac/output/post_human_review_sidecar_result_340e`

## Output Files

- `post_human_review_sidecar_result_340e.xlsx`
- `post_human_review_sidecar_result_340e_summary.json`
- `post_human_review_sidecar_result_340e_manifest.json`
- `post_human_review_sidecar_result_340e_qa.json`
- `post_human_review_sidecar_result_340e_no_write_back_proof.json`
- `post_human_review_sidecar_result_340e_report.md`

## No-Write-Back Boundary

- Do not modify 337D workbook.
- Do not modify 338D workbook.
- Do not modify 340B workbook.
- Do not modify 340C workbook.
- Do not modify 340D workbook.
- Do not create client export.
- Do not modify official assets.
- Do not modify production pipeline, parser, extraction, or delivery behavior.

## Core Rules

- `FINAL_WOULD_CONFIRM_REVIEWED -> reviewed_after_human`
- `FINAL_WOULD_APPLY_CORRECTION_AND_CONFIRM -> reviewed_after_human_corrected`
- `FINAL_WOULD_REJECT -> rejected_after_human`
- `FINAL_WOULD_KEEP_NEEDS_REVIEW -> needs_review_after_human`
- `FINAL_WOULD_KEEP_NEEDS_MORE_CONTEXT -> needs_review_after_human`
- corrected rows must use corrected fields as final sidecar values

## Workbook Sheets

1. `00_README`
2. `01_REVIEWED_AFTER_HUMAN`
3. `02_REVIEWED_HUMAN_CORRECTED`
4. `03_NEEDS_REVIEW_AFTER_HUMAN`
5. `04_REJECTED_AFTER_HUMAN`
6. `05_CORRECTION_LOG`
7. `06_SOURCE_TRACE`
8. `07_RISK_AUDIT`
9. `08_SUMMARY`
10. `09_NO_WRITE_BACK_PROOF`
11. `10_NEXT_STEP_RECOMMENDATION`

## Summary Requirements

- `total_input_rows = 77`
- `reviewed_after_human_count = 22`
- `reviewed_after_human_corrected_count = 12`
- `reviewed_after_human_total_count = 34`
- `rejected_after_human_count = 31`
- `needs_review_after_human_count = 12`
- `qa_fail_count = 0`
- `client_ready = false`
- `production_ready = false`
- `decision = POST_HUMAN_REVIEW_SIDECAR_RESULT_340E_READY`

## Validation

- 340D workbook exists
- 340D decision is ready
- all 77 input rows are represented
- sidecar counts are internally consistent
- corrected rows use corrected values
- no upstream workbook is modified
- no official assets are modified
- no client-ready claim is introduced
- no production-ready claim is introduced
- no-write-back proof is generated

## Files

- `docs/codex_tasks/340E_post_human_review_sidecar_result.md`
- `datefac/trust/post_human_review_sidecar_result_340e.py`
- `datefac/trust/post_human_review_sidecar_result_340e_report.py`
- `tools/run_post_human_review_sidecar_result_340e.py`
- `tests/trust/test_post_human_review_sidecar_result_340e.py`

## Run

```powershell
python -m py_compile datefac\trust\post_human_review_sidecar_result_340e.py datefac\trust\post_human_review_sidecar_result_340e_report.py tools\run_post_human_review_sidecar_result_340e.py tests\trust\test_post_human_review_sidecar_result_340e.py

python -m pytest tests\trust\test_post_human_review_sidecar_result_340e.py -q

python tools\run_post_human_review_sidecar_result_340e.py --full-human-review-apply-340d-dir D:\_datefac\output\full_human_review_apply_plan_340d --output-dir D:\_datefac\output\post_human_review_sidecar_result_340e
```
