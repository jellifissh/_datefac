# 343G：AI-assisted Review Spot-check Result Ingestion

## 1. Positioning

343G ingests a filled 343F spot-check review workbook and converts spot-check decisions into a validated spot-check result sidecar.

The current filled workbook is AI-assisted. It was not completed by a strict independent human reviewer. Therefore 343G must preserve audit honesty and mark the result as AI-assisted spot-check, not strict human verification.

343G is an ingestion and validation task. It is not production apply, not formal client export, not Argilla integration, not a frontend implementation, not a real LLM/VLM review, and not an upstream extraction rerun.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/343A_review_queue_schema_and_human_review_ui_pilot.md`
- `docs/codex_tasks/343E_ai_assisted_review_result_apply_simulation_and_audit_gate.md`
- `docs/codex_tasks/343F_ai_assisted_review_spot_check_package.md`
- 343A schema summary / schema JSON
- 343E apply simulation summary / apply plan / simulated sidecar / audit gate
- 343F summary / QA / review template / expected import contract / source-check todo
- current git status

Expected current state:

- latest completed milestone = `343F AI-assisted Review Spot-check Package`
- 343F decision = `AI_ASSISTED_REVIEW_SPOT_CHECK_PACKAGE_343F_WAITING_FOR_SPOT_CHECK`
- review_queue_schema_version = `343A.review_queue.v1`
- input_apply_plan_row_count = `30`
- input_simulated_sidecar_row_count = `10`
- spot_check_item_count = `30`
- simulated_applied_spot_check_count = `10`
- source_check_required_count = `19`
- skipped_hold_count = `1`
- review_template_generated = `true`
- expected_import_contract_generated = `true`
- review_source_type = `AI_ASSISTED_REVIEW`
- not_pure_human_review = `true`
- strict_human_review_completed = `false`
- requires_human_spot_check = `true`
- apply_mode = `SIMULATION_ONLY`
- waiting_for_spot_check = `true`
- spot_check_result_ingested = `false`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- ready_for_343g = `false`
- recommended_343g_scope = `ai_assisted_review_spot_check_result_ingestion_after_user_fills_workbook`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, or delivery code. Do not write back to upstream workbooks. Do not generate formal client export. Do not perform real production apply. Do not claim strict human spot-check is complete.

Preserve these flags:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`

Preserve AI-assisted disclosure:

- `review_source_type = AI_ASSISTED_REVIEW`
- `spot_check_source_type = AI_ASSISTED_SPOT_CHECK`
- `not_pure_human_review = true`
- `apply_mode = SIMULATION_ONLY`

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343G_ai_assisted_review_spot_check_result_ingestion.md`
- `datefac/review_queue/ingest_spot_check_343g.py`
- `datefac/benchmark/review_queue_spot_check_ingestion_343g.py`
- `datefac/benchmark/review_queue_spot_check_ingestion_343g_report.py`
- `tools/run_review_queue_spot_check_ingestion_343g.py`
- `tests/benchmark/test_review_queue_spot_check_ingestion_343g.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_spot_check_package_343f`
- `D:/_datefac/output/review_queue_apply_simulation_343e`
- `D:/_datefac/output/review_queue_schema_343a`
- `D:/_datefac/input/review_queue_spot_check_package_343f_filled`

Required filled workbook:

- `D:/_datefac/input/review_queue_spot_check_package_343f_filled/review_queue_spot_check_package_343f_review_template_filled.xlsx`

Primary reference files:

- `review_queue_spot_check_package_343f_summary.json`
- `review_queue_spot_check_package_343f_qa.json`
- `review_queue_spot_check_package_343f_expected_import_contract.json`
- `review_queue_spot_check_package_343f_review_template.xlsx`
- `review_queue_spot_check_package_343f_spot_check_items.jsonl`
- `review_queue_spot_check_package_343f_source_check_todo.jsonl`
- `review_queue_apply_simulation_343e_apply_plan.jsonl`
- `review_queue_apply_simulation_343e_simulated_sidecar.jsonl`
- `review_queue_schema_343a_schema.json`

If the filled workbook is missing, fail gracefully with a clear error explaining the expected path. Do not fabricate spot-check results.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_spot_check_ingestion_343g`

Output files:

- `review_queue_spot_check_ingestion_343g.xlsx`
- `review_queue_spot_check_ingestion_343g_summary.json`
- `review_queue_spot_check_ingestion_343g_manifest.json`
- `review_queue_spot_check_ingestion_343g_qa.json`
- `review_queue_spot_check_ingestion_343g_report.md`
- `review_queue_spot_check_ingestion_343g_result.jsonl`
- `review_queue_spot_check_ingestion_343g_validation_errors.json`
- `review_queue_spot_check_ingestion_343g_validation_warnings.json`
- `review_queue_spot_check_ingestion_343g_decision_summary.json`
- `review_queue_spot_check_ingestion_343g_ai_assisted_spot_check_disclosure.md`
- `review_queue_spot_check_ingestion_343g_no_write_back_proof.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_INGEST_SUMMARY`
- `02_INPUT_343F_SUMMARY`
- `03_FILLED_SPOT_ROWS`
- `04_VALID_ROWS`
- `05_INVALID_ROWS`
- `06_DECISION_SUMMARY`
- `07_STATUS_MAPPING`
- `08_AI_SPOT_DISCLOSURE`
- `09_STRICT_HUMAN_GAP`
- `10_343H_READINESS`
- `11_NO_WRITE_BACK`
- `12_NEXT_STEPS`

## 8. Core logic

### 8.1 Read filled spot-check workbook

Read the filled workbook from the required input path. Prefer the sheet named `04_REVIEW_TEMPLATE`, as defined by the 343F import contract. Fail with a clear message if no valid sheet is found.

### 8.2 Validate identity columns

Required identity columns:

- `queue_item_id`
- `review_item_id`
- `simulated_downstream_action`
- `priority_tier`

If a required identity field is missing, record validation errors and set the task decision to NOT_READY.

### 8.3 Validate editable spot-check columns

Required editable columns:

- `spot_check_decision`
- `spot_check_metric_standardized`
- `spot_check_year_standardized`
- `spot_check_value_numeric`
- `spot_check_normalized_unit`
- `spot_check_note`
- `spot_checker_id`
- `spot_checked_at`

Allowed spot-check decisions:

- `CONFIRM_AI_ASSISTED_RESULT`
- `CORRECT_AI_ASSISTED_RESULT`
- `REJECT_AI_ASSISTED_RESULT`
- `SOURCE_CHECK_REQUIRED`
- `KEEP_HOLD`
- `SKIP_SPOT_CHECK`

Rules:

- `CORRECT_AI_ASSISTED_RESULT` requires corrected metric/year/value/unit.
- `REJECT_AI_ASSISTED_RESULT` requires a note.
- `SOURCE_CHECK_REQUIRED` requires a note.
- `KEEP_HOLD` should include a note when possible.
- Empty spot-check decisions are invalid for this ingestion task.

### 8.4 Map spot-check decisions to spot-check statuses

Map decisions:

- `CONFIRM_AI_ASSISTED_RESULT` -> `SPOT_CHECK_CONFIRMED_AI_ASSISTED`
- `CORRECT_AI_ASSISTED_RESULT` -> `SPOT_CHECK_CORRECTED_AI_ASSISTED`
- `REJECT_AI_ASSISTED_RESULT` -> `SPOT_CHECK_REJECTED_AI_ASSISTED`
- `SOURCE_CHECK_REQUIRED` -> `SPOT_CHECK_SOURCE_CHECK_REQUIRED`
- `KEEP_HOLD` -> `SPOT_CHECK_KEEP_HOLD`
- `SKIP_SPOT_CHECK` -> `SPOT_CHECK_SKIPPED`

Do not implement production apply logic.

### 8.5 AI-assisted spot-check disclosure

Every result row must include:

- `review_source_type = AI_ASSISTED_REVIEW`
- `spot_check_source_type = AI_ASSISTED_SPOT_CHECK`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `apply_mode = SIMULATION_ONLY`
- `spot_check_source_disclosure = filled by AI assistant from available workbook evidence; not strict pure human spot-check`

Rows are useful for pilot validation only. They must not be treated as fully human-confirmed production evidence.

### 8.6 Result JSONL

Generate `review_queue_spot_check_ingestion_343g_result.jsonl` with one object per ingested spot-check row:

- identity
- original simulated downstream action
- priority tier
- spot-check decision
- corrected fields if any
- resulting spot-check status
- validation status
- validation errors/warnings
- AI-assisted spot-check disclosure fields
- formal/client/production readiness flags all false
- no-write-back marker

## 9. 343H readiness

If QA passes and validation errors are zero, set:

- `spot_check_result_ingested = true`
- `ai_assisted_spot_check_completed = true`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `ready_for_343h = true`
- `recommended_343h_scope = ai_assisted_spot_check_audit_summary_and_strict_human_gap_report`

If validation errors exist, set:

- `spot_check_result_ingested = false`
- `ready_for_343h = false`

## 10. Summary JSON

`review_queue_spot_check_ingestion_343g_summary.json` must include at least:

- `source_milestone = 343F`
- `decision`
- `review_queue_schema_version`
- `filled_workbook_path`
- `filled_spot_check_row_count`
- `valid_row_count`
- `invalid_row_count`
- `confirm_ai_assisted_result_count`
- `correct_ai_assisted_result_count`
- `reject_ai_assisted_result_count`
- `source_check_required_count`
- `keep_hold_count`
- `skip_spot_check_count`
- `validation_error_count`
- `validation_warning_count`
- `review_source_type = AI_ASSISTED_REVIEW`
- `spot_check_source_type = AI_ASSISTED_SPOT_CHECK`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `apply_mode = SIMULATION_ONLY`
- `spot_check_result_ingested`
- `spot_check_result_jsonl_generated`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343h`
- `recommended_343h_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready: `AI_ASSISTED_SPOT_CHECK_INGESTION_343G_READY`
- otherwise: `AI_ASSISTED_SPOT_CHECK_INGESTION_343G_NOT_READY`

## 11. QA requirements

Must check:

- 343F input exists and is waiting for spot-check
- filled workbook exists
- filled workbook can be read
- expected sheet `04_REVIEW_TEMPLATE` exists
- identity columns exist
- editable spot-check columns exist
- spot-check decisions are all allowed and non-empty
- correction rows have required corrected fields
- source-check rows have notes
- status mapping is generated
- result JSONL is generated when validation passes
- AI-assisted spot-check disclosure fields exist on every row
- strict human review is not claimed
- no formal/client/production readiness flag is true
- no Argilla call is made
- no real production apply is performed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_spot_check_ingestion_343g_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343G ingests a filled spot-check workbook
- this workbook is AI-assisted, not strict pure human spot-check
- how spot-check decisions were validated and mapped to statuses
- how result JSONL was generated
- why formal client export remains forbidden
- why strict human review is still incomplete
- recommended next step: 343H audit summary and strict-human-gap report, not production export

## 13. Ledger update

Update the project milestone ledger with:

- 343G completed or not-ready status
- inputs
- outputs
- key metrics
- QA result
- decision
- AI-assisted spot-check disclosure
- next recommended task

If ready_for_343h is true, recommend:

`343H AI-assisted Spot-check Audit Summary And Strict Human Gap Report`

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\ingest_spot_check_343g.py datefac\benchmark\review_queue_spot_check_ingestion_343g.py datefac\benchmark\review_queue_spot_check_ingestion_343g_report.py tools\run_review_queue_spot_check_ingestion_343g.py tests\benchmark\test_review_queue_spot_check_ingestion_343g.py
python -m pytest tests\benchmark\test_review_queue_spot_check_ingestion_343g.py -q
python tools\run_review_queue_spot_check_ingestion_343g.py --spot-check-package-343f-dir D:\_datefac\output\review_queue_spot_check_package_343f --apply-simulation-343e-dir D:\_datefac\output\review_queue_apply_simulation_343e --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --filled-workbook D:\_datefac\input\review_queue_spot_check_package_343f_filled\review_queue_spot_check_package_343f_review_template_filled.xlsx --output-dir D:\_datefac\output\review_queue_spot_check_ingestion_343g
```

## 15. Completion report

Report in Chinese:

1. 343G decision
2. review_queue_schema_version
3. filled_workbook_path
4. filled_spot_check_row_count
5. valid_row_count
6. invalid_row_count
7. confirm_ai_assisted_result_count
8. correct_ai_assisted_result_count
9. reject_ai_assisted_result_count
10. source_check_required_count
11. keep_hold_count
12. skip_spot_check_count
13. validation_error_count
14. validation_warning_count
15. review_source_type
16. spot_check_source_type
17. not_pure_human_review
18. strict_human_review_completed
19. requires_strict_human_review
20. apply_mode
21. spot_check_result_ingested
22. spot_check_result_jsonl_generated
23. formal_client_export_allowed
24. client_ready
25. production_ready
26. ready_for_343h
27. recommended_343h_scope
28. qa_fail_count
29. no-write-back proof status
30. output directory
31. most important Excel/result/disclosure artifacts
32. modified files
33. validation command results
34. git status summary
35. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
