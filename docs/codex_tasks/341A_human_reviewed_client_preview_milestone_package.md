# 341A Human-Reviewed Client Preview Milestone Package

## Goal

Create a milestone package that summarizes the real PDF -> MinerU -> AI dry-run -> human review -> client preview -> audit chain across 337A to 340G.

This is a milestone package only.
It is not a new extraction run, not a production pipeline output, and not a client delivery package.

It must not write back to any upstream workbook.
It must not modify parser, extraction, or delivery behavior.
It must not modify official assets.
It must not commit output artifacts.

## Inputs

- `D:/_datefac/output/human_review_after_ai_adoption_340b`
- `D:/_datefac/output/human_review_apply_simulation_340c`
- `D:/_datefac/output/full_human_review_apply_plan_340d`
- `D:/_datefac/output/post_human_review_sidecar_result_340e`
- `D:/_datefac/output/client_preview_after_human_review_340f`
- `D:/_datefac/output/client_preview_export_audit_340g`

## Output Dir

- `D:/_datefac/output/human_reviewed_client_preview_milestone_341a`

## Output Files

- `human_reviewed_client_preview_milestone_341a.xlsx`
- `human_reviewed_client_preview_milestone_341a_summary.json`
- `human_reviewed_client_preview_milestone_341a_manifest.json`
- `human_reviewed_client_preview_milestone_341a_qa.json`
- `human_reviewed_client_preview_milestone_341a_report.md`

## Workbook Sheets

1. `00_README`
2. `01_MILESTONE_SUMMARY`
3. `02_PIPELINE_STAGES`
4. `03_KEY_COUNTS`
5. `04_CLIENT_PREVIEW_AUDIT`
6. `05_OUTPUT_ARTIFACTS`
7. `06_REMAINING_RISKS`
8. `07_DEMO_RUNBOOK`
9. `08_NEXT_STEP_ROADMAP`
10. `09_NO_WRITE_BACK_PROOF`

All sheet names must be `<= 31` characters.

## Required Milestone Statements

The package must clearly state:

- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- not investment advice
- still not scalable production
- current benchmark is limited to the current real PDF sample set
- next bottlenecks are parser robustness, larger benchmark, metadata extraction, batch stability, and UI review workflow

## Required Key Counts

- `340B total review queue = 77`
- `340C full validation passed`
- `340D final reviewed after human candidate count = 34`
- `340E reviewed_after_human_total_count = 34`
- `340F client_preview_core_metric_count = 34`
- `340G audited_core_metric_count = 34`
- `duplicate_issue_count = 0`
- `unit_issue_count = 0`
- `missing_source_trace_count = 0`
- `unsafe_claim_count = 0`
- `qa_fail_count = 0`

## QA

- all expected input artifacts exist
- `340G decision = CLIENT_PREVIEW_EXPORT_AUDIT_340G_READY`
- key counts are consistent across `340D / 340E / 340F / 340G`
- no `client_ready = true`
- no `production_ready = true`
- no investment advice claim
- no write-back to upstream workbook
- `qa_fail_count = 0`
- `decision = HUMAN_REVIEWED_CLIENT_PREVIEW_MILESTONE_341A_READY`

## Files

- `docs/codex_tasks/341A_human_reviewed_client_preview_milestone_package.md`
- `datefac/trust/human_reviewed_client_preview_milestone_341a.py`
- `datefac/trust/human_reviewed_client_preview_milestone_341a_report.py`
- `tools/run_human_reviewed_client_preview_milestone_341a.py`
- `tests/trust/test_human_reviewed_client_preview_milestone_341a.py`

## Run

```powershell
python -m py_compile datefac\trust\human_reviewed_client_preview_milestone_341a.py datefac\trust\human_reviewed_client_preview_milestone_341a_report.py tools\run_human_reviewed_client_preview_milestone_341a.py tests\trust\test_human_reviewed_client_preview_milestone_341a.py

python -m pytest tests\trust\test_human_reviewed_client_preview_milestone_341a.py -q

python tools\run_human_reviewed_client_preview_milestone_341a.py --human-review-340b-dir D:\_datefac\output\human_review_after_ai_adoption_340b --human-review-apply-340c-dir D:\_datefac\output\human_review_apply_simulation_340c --full-human-review-apply-340d-dir D:\_datefac\output\full_human_review_apply_plan_340d --post-human-review-340e-dir D:\_datefac\output\post_human_review_sidecar_result_340e --client-preview-340f-dir D:\_datefac\output\client_preview_after_human_review_340f --client-preview-audit-340g-dir D:\_datefac\output\client_preview_export_audit_340g --output-dir D:\_datefac\output\human_reviewed_client_preview_milestone_341a
```
