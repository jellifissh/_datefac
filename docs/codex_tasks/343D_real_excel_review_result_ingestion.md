# 343D：Real Excel Review Result Ingestion

## 1. Positioning

343D ingests a filled 343C Excel review workbook and converts reviewer decisions into reviewed-result sidecar artifacts.

This task must treat the current filled workbook as `AI_ASSISTED_REVIEW`, not pure human review. It must preserve audit honesty by marking the source as AI-assisted, requiring later human spot-check, and avoiding any claim that strict human review is complete.

343D is an ingestion and validation task. It is not a formal client export, not a production review service, not an Argilla integration, not a frontend implementation, and not an upstream extraction rerun.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/343A_review_queue_schema_and_human_review_ui_pilot.md`
- `docs/codex_tasks/343B_excel_round_trip_review_queue_pilot.md`
- `docs/codex_tasks/343C_real_excel_review_queue_pilot.md`
- 343A output summary / schema JSON / sample items JSONL
- 343B output summary / reviewed result mechanics reference
- 343C output summary / qa / real review template / import contract / fill guide
- current git status

Expected current state:

- latest completed milestone = `343C Real Excel Review Queue Pilot`
- 343C decision = `REVIEW_QUEUE_REAL_EXCEL_REVIEW_343C_WAITING_FOR_HUMAN_REVIEW`
- review_queue_schema_version = `343A.review_queue.v1`
- real_review_template_row_count = `30`
- fillable_review_row_count = `30`
- waiting_for_human_review = `true`
- reviewed_result_ingested = `false`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- ready_for_343d = `false`
- recommended_343d_scope = `real_excel_review_result_ingestion_after_user_fills_workbook`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, or delivery code. Do not write back to upstream workbooks. Do not generate formal client export. Do not fabricate pure human review.

Preserve these flags:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

The filled workbook must be marked as:

- `review_source_type = AI_ASSISTED_REVIEW`
- `not_pure_human_review = true`
- `requires_human_spot_check = true`

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343D_real_excel_review_result_ingestion.md`
- `datefac/review_queue/ingest_excel_review_343d.py`
- `datefac/benchmark/review_queue_excel_ingestion_343d.py`
- `datefac/benchmark/review_queue_excel_ingestion_343d_report.py`
- `tools/run_review_queue_excel_ingestion_343d.py`
- `tests/benchmark/test_review_queue_excel_ingestion_343d.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_real_excel_review_343c`
- `D:/_datefac/output/review_queue_excel_round_trip_343b`
- `D:/_datefac/output/review_queue_schema_343a`
- `D:/_datefac/input/review_queue_real_excel_review_343c_filled`

Required filled workbook:

- `D:/_datefac/input/review_queue_real_excel_review_343c_filled/review_queue_real_excel_review_343c_review_template_filled.xlsx`

Primary reference files:

- `review_queue_real_excel_review_343c_summary.json`
- `review_queue_real_excel_review_343c_qa.json`
- `review_queue_real_excel_review_343c_expected_import_contract.json`
- `review_queue_real_excel_review_343c_review_template.xlsx`
- `review_queue_schema_343a_schema.json`
- `review_queue_schema_343a_json_schema.json`

If the filled workbook is missing, fail gracefully with a clear error explaining the expected path. Do not fabricate filled results.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_excel_ingestion_343d`

Output files:

- `review_queue_excel_ingestion_343d.xlsx`
- `review_queue_excel_ingestion_343d_summary.json`
- `review_queue_excel_ingestion_343d_manifest.json`
- `review_queue_excel_ingestion_343d_qa.json`
- `review_queue_excel_ingestion_343d_report.md`
- `review_queue_excel_ingestion_343d_reviewed_result.jsonl`
- `review_queue_excel_ingestion_343d_validation_errors.json`
- `review_queue_excel_ingestion_343d_validation_warnings.json`
- `review_queue_excel_ingestion_343d_decision_summary.json`
- `review_queue_excel_ingestion_343d_ai_assisted_review_disclosure.md`
- `review_queue_excel_ingestion_343d_no_write_back_proof.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_INGEST_SUMMARY`
- `02_INPUT_343C_SUMMARY`
- `03_FILLED_ROWS`
- `04_VALID_ROWS`
- `05_INVALID_ROWS`
- `06_DECISION_SUMMARY`
- `07_STATUS_MAPPING`
- `08_REVIEW_SOURCE_DISCLOSURE`
- `09_SPOT_CHECK_REQUIRED`
- `10_343E_READINESS`
- `11_NO_WRITE_BACK`
- `12_NEXT_STEPS`

## 8. Core logic

### 8.1 Read filled workbook

Read the filled workbook from the required input path. Prefer the fillable review sheet generated by 343C, expected as `04_FILLABLE_REVIEW`. If the actual sheet differs, use the 343C import contract to identify the expected sheet. Fail with a clear message if no valid sheet can be found.

### 8.2 Validate identity columns

Verify identity columns are present and unchanged enough to map back to queue items:

- `queue_item_id`
- `review_item_id`
- `source_stage`
- `source_artifact_path` or equivalent source reference

If a required identity field is missing, record validation errors and set the task decision to NOT_READY.

### 8.3 Validate reviewer columns

Required reviewer columns:

- `reviewer_decision`
- `reviewer_metric_standardized`
- `reviewer_year_standardized`
- `reviewer_value_numeric`
- `reviewer_normalized_unit`
- `reviewer_note`
- `reviewer_id`
- `reviewed_at`

Allowed decisions:

- `CONFIRM`
- `CORRECT`
- `REJECT`
- `NEEDS_SOURCE_CHECK`
- `SKIP`

Rules:

- `CONFIRM` may keep candidate fields unchanged.
- `CORRECT` requires corrected metric/year/value/unit where applicable.
- `REJECT` requires a reviewer note.
- `NEEDS_SOURCE_CHECK` requires a reviewer note.
- `SKIP` should include a reason when available.
- Empty decisions are invalid for this ingestion task.

### 8.4 Map decisions to statuses

Map reviewer decisions to queue statuses:

- `CONFIRM` -> `REVIEWED_CONFIRMED`
- `CORRECT` -> `REVIEWED_CORRECTED`
- `REJECT` -> `REJECTED`
- `NEEDS_SOURCE_CHECK` -> `NEEDS_SOURCE_CHECK`
- `SKIP` -> `SKIPPED`

Do not implement production apply logic.

### 8.5 AI-assisted review disclosure

Every reviewed result row must include:

- `review_source_type = AI_ASSISTED_REVIEW`
- `not_pure_human_review = true`
- `requires_human_spot_check = true`
- `review_source_disclosure = filled by AI assistant from available workbook evidence; not strict pure human review`

Rows may be useful for pilot ingestion validation, but they must not be treated as fully human-confirmed production evidence.

### 8.6 Reviewed result JSONL

Generate JSONL with one object per ingested row:

- queue item identity
- original candidate fields
- reviewer decision
- corrected fields if any
- resulting status
- validation status
- validation errors/warnings
- review source disclosure fields
- formal/client/production readiness flags all false
- no-write-back marker

## 9. 343E readiness

If QA passes and validation errors are zero, set:

- `reviewed_result_ingested = true`
- `ready_for_343e = true`
- `recommended_343e_scope = ai_assisted_review_result_apply_simulation_and_audit_gate`

Also preserve:

- `strict_human_review_completed = false`
- `requires_human_spot_check = true`

If validation errors exist, set:

- `reviewed_result_ingested = false`
- `ready_for_343e = false`

## 10. Summary JSON

`review_queue_excel_ingestion_343d_summary.json` must include at least:

- `source_milestone = 343C`
- `decision`
- `review_queue_schema_version`
- `filled_workbook_path`
- `filled_row_count`
- `valid_row_count`
- `invalid_row_count`
- `confirmed_count`
- `corrected_count`
- `rejected_count`
- `needs_source_check_count`
- `skipped_count`
- `validation_error_count`
- `validation_warning_count`
- `review_source_type = AI_ASSISTED_REVIEW`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_human_spot_check = true`
- `reviewed_result_ingested`
- `reviewed_result_jsonl_generated`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343e`
- `recommended_343e_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready: `REVIEW_QUEUE_EXCEL_INGESTION_343D_READY`
- otherwise: `REVIEW_QUEUE_EXCEL_INGESTION_343D_NOT_READY`

## 11. QA requirements

Must check:

- 343C input exists and is waiting for review
- filled workbook exists
- filled workbook can be read
- expected sheet exists or is resolved by import contract
- identity columns exist
- reviewer columns exist
- reviewer decisions are all allowed and non-empty
- `CORRECT` rows have required corrected fields
- `REJECT` and `NEEDS_SOURCE_CHECK` rows have notes
- status mapping is generated
- reviewed result JSONL is generated when validation passes
- AI-assisted disclosure fields exist on every row
- strict human review is not claimed
- no formal/client/production readiness flag is true
- no Argilla call is made
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_excel_ingestion_343d_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343D ingests a filled Excel review workbook
- this workbook is AI-assisted, not strict pure human review
- how decisions were validated and mapped to statuses
- how reviewed-result JSONL was generated
- why formal client export remains forbidden
- why human spot-check is still required
- recommended next step: 343E apply simulation and audit gate, not production export

## 13. Ledger update

Update the project milestone ledger with:

- 343D completed or not-ready status
- status
- inputs
- outputs
- key metrics
- QA result
- decision
- AI-assisted disclosure
- next recommended task

If ready_for_343e is true, recommend:

`343E AI-assisted Review Result Apply Simulation And Audit Gate`

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\ingest_excel_review_343d.py datefac\benchmark\review_queue_excel_ingestion_343d.py datefac\benchmark\review_queue_excel_ingestion_343d_report.py tools\run_review_queue_excel_ingestion_343d.py tests\benchmark\test_review_queue_excel_ingestion_343d.py
python -m pytest tests\benchmark\test_review_queue_excel_ingestion_343d.py -q
python tools\run_review_queue_excel_ingestion_343d.py --real-excel-review-343c-dir D:\_datefac\output\review_queue_real_excel_review_343c --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --filled-workbook D:\_datefac\input\review_queue_real_excel_review_343c_filled\review_queue_real_excel_review_343c_review_template_filled.xlsx --output-dir D:\_datefac\output\review_queue_excel_ingestion_343d
```

## 15. Completion report

Report in Chinese:

1. 343D decision
2. review_queue_schema_version
3. filled_workbook_path
4. filled_row_count
5. valid_row_count
6. invalid_row_count
7. confirmed_count
8. corrected_count
9. rejected_count
10. needs_source_check_count
11. skipped_count
12. validation_error_count
13. validation_warning_count
14. review_source_type
15. not_pure_human_review
16. strict_human_review_completed
17. requires_human_spot_check
18. reviewed_result_ingested
19. reviewed_result_jsonl_generated
20. formal_client_export_allowed
21. client_ready
22. production_ready
23. ready_for_343e
24. recommended_343e_scope
25. qa_fail_count
26. no-write-back proof status
27. output directory
28. most important Excel/result/disclosure artifacts
29. modified files
30. validation command results
31. git status summary
32. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
