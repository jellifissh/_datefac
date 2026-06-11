# 343B：Excel Round-trip Review Queue Pilot

## 1. Positioning

343B validates the Review Queue schema from 343A through an Excel round-trip pilot. It must prove that review queue items can be exported to a human-review workbook, re-imported from a reviewed workbook shape, validated, and summarized without writing back to upstream artifacts.

This task is intentionally lighter and safer than an Argilla integration. Argilla remains a future pluggable UI option; 343B first validates the schema contract using Excel because it is deterministic and easy to inspect.

343B is not a formal client export, not a production review service, not an Argilla integration, and not a full frontend implementation.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/343A_review_queue_schema_and_human_review_ui_pilot.md`
- 343A output summary / qa / report / workbook / schema JSON / Excel template spec / sample items JSONL
- 342S summary / qa / report for stage boundary context
- current git status

Expected current state:

- latest completed milestone = `343A Review Queue Schema And Human Review UI Pilot`
- 343A decision = `REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- ready_for_343b = `true`
- recommended_343b_scope = `argilla_human_review_ui_pilot`, but this task deliberately chooses the safer Excel round-trip pilot first
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use:

- `git add .`
- `git add -A`
- `git reset --hard`
- `git checkout --`

## 4. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, or delivery code. Do not write back to upstream workbooks. Do not generate formal client export. Preserve `formal_client_export_allowed=false`, `client_ready=false`, and `production_ready=false`.

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343B_excel_round_trip_review_queue_pilot.md`
- `datefac/review_queue/excel_round_trip_343b.py`
- `datefac/benchmark/review_queue_excel_round_trip_343b.py`
- `datefac/benchmark/review_queue_excel_round_trip_343b_report.py`
- `tools/run_review_queue_excel_round_trip_343b.py`
- `tests/benchmark/test_review_queue_excel_round_trip_343b.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched because the package requires it, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_schema_343a`
- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s`
- `D:/_datefac/output/audit_labeled_export_candidate_package_342r`

Primary 343A files:

- `review_queue_schema_343a_summary.json`
- `review_queue_schema_343a_qa.json`
- `review_queue_schema_343a_schema.json`
- `review_queue_schema_343a_json_schema.json`
- `review_queue_schema_343a_excel_template_spec.json`
- `review_queue_schema_343a_sample_items.jsonl`
- `review_queue_schema_343a.xlsx`

Expected 343A metrics:

- field_count = 58
- required_field_count = 29
- status_count = 13
- reason_code_count = 12
- priority_level_count = 5
- sample_queue_item_count = 51
- human_reviewed_sample_count = 10
- simulated_sample_count = 40
- summary_derived_sample_count = 1
- formal_client_export_allowed = false
- client_ready = false
- production_ready = false
- qa_fail_count = 0

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_excel_round_trip_343b`

Output files:

- `review_queue_excel_round_trip_343b.xlsx`
- `review_queue_excel_round_trip_343b_summary.json`
- `review_queue_excel_round_trip_343b_manifest.json`
- `review_queue_excel_round_trip_343b_qa.json`
- `review_queue_excel_round_trip_343b_report.md`
- `review_queue_excel_round_trip_343b_review_template.xlsx`
- `review_queue_excel_round_trip_343b_import_simulation.xlsx`
- `review_queue_excel_round_trip_343b_reviewed_result.jsonl`
- `review_queue_excel_round_trip_343b_validation_errors.json`
- `review_queue_excel_round_trip_343b_no_write_back_proof.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_ROUND_TRIP_SUMMARY`
- `02_INPUT_343A_SUMMARY`
- `03_REVIEW_TEMPLATE_SPEC`
- `04_EXPORT_TEMPLATE_ROWS`
- `05_IMPORT_SIMULATION`
- `06_VALIDATION_RULES`
- `07_STATUS_MAPPING`
- `08_DECISION_MAPPING`
- `09_ERROR_CASES`
- `10_REVIEWED_RESULT`
- `11_BACKLOG_NOTE`
- `12_343C_READINESS`
- `13_NO_WRITE_BACK`
- `14_NEXT_STEPS`

## 8. Core logic

### 8.1 Export review template

Read 343A sample queue items and schema artifacts. Generate a review template workbook/spec that contains only review-safe fields:

- identity fields needed to map back to queue items
- source/evidence display fields
- candidate metric/year/value/unit fields
- trust/risk/reason/priority fields
- reviewer editable fields
- reviewer note and metadata fields

Do not include fields that would encourage formal client export claims. Preserve readiness flags as false.

### 8.2 Import simulation

Generate a deterministic import simulation from the exported template. This is not a user-filled workbook. It should simulate representative reviewer decisions to validate schema mechanics:

- confirmed rows
- corrected rows
- rejected rows
- needs source check rows
- skipped rows

The simulation must be deterministic and documented. It must not claim real human review.

### 8.3 Validation

Validate imported rows against the 343A schema:

- required identity fields exist
- reviewer decisions are allowed
- corrected fields are present when decision requires correction
- value fields are numeric where required
- simulated rows remain not-final unless properly reviewed in a later real review task
- formal/client/production flags remain false
- no upstream artifact is modified

### 8.4 Status and decision mapping

Map reviewer decisions to queue lifecycle statuses:

- confirm -> `REVIEWED_CONFIRMED`
- correct -> `REVIEWED_CORRECTED`
- reject -> `REJECTED`
- needs source check -> `NEEDS_SOURCE_CHECK`
- skip -> `SKIPPED`

Do not implement production apply logic. If an item becomes eligible for apply simulation, only mark that as a future-state candidate in the output.

### 8.5 Reviewed result JSONL

Generate reviewed-result JSONL with:

- queue item identity
- reviewer decision
- corrected values if any
- resulting status
- validation status
- audit note
- no-write-back marker

## 9. 343C readiness

If QA passes, set:

- `ready_for_343c = true`
- `recommended_343c_scope = argilla_human_review_ui_pilot`

The report should explain that Excel round-trip validated the stable Review Queue contract, so Argilla can now be integrated as a pluggable UI rather than becoming the core system.

## 10. Summary JSON

`review_queue_excel_round_trip_343b_summary.json` must include at least:

- `source_milestone = 343A`
- `decision`
- `review_queue_schema_version`
- `template_row_count`
- `import_simulation_row_count`
- `reviewed_result_row_count`
- `confirmed_count`
- `corrected_count`
- `rejected_count`
- `needs_source_check_count`
- `skipped_count`
- `validation_error_count`
- `validation_warning_count`
- `excel_template_generated`
- `import_simulation_generated`
- `reviewed_result_jsonl_generated`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343c`
- `recommended_343c_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready: `REVIEW_QUEUE_EXCEL_ROUND_TRIP_343B_READY`
- otherwise: `REVIEW_QUEUE_EXCEL_ROUND_TRIP_343B_NOT_READY`

## 11. QA requirements

Must check:

- 343A input exists and is ready
- schema JSON and sample JSONL exist
- review template is generated
- import simulation is generated
- reviewed result JSONL is generated
- validation rules run
- validation_error_count is zero for the happy-path simulated import
- intentional error cases are captured separately without failing the happy path
- no formal/client/production readiness flag is true
- no real human review claim is made
- no Argilla call is made
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_excel_round_trip_343b_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343B validates the Review Queue schema through Excel round-trip
- it does not represent real human review
- it does not implement Argilla or a full UI
- how export template, import simulation, validation, decision mapping, and reviewed JSONL work
- why formal client export remains forbidden
- why 343C can safely move to an Argilla UI pilot after this

## 13. Ledger update

Update the project milestone ledger with:

- 343B completed
- status
- inputs
- outputs
- key metrics
- QA result
- decision
- next recommended task

If ready_for_343c is true, recommend:

`343C Argilla Human Review UI Pilot`

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\excel_round_trip_343b.py datefac\benchmark\review_queue_excel_round_trip_343b.py datefac\benchmark\review_queue_excel_round_trip_343b_report.py tools\run_review_queue_excel_round_trip_343b.py tests\benchmark\test_review_queue_excel_round_trip_343b.py
python -m pytest tests\benchmark\test_review_queue_excel_round_trip_343b.py -q
python tools\run_review_queue_excel_round_trip_343b.py --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --snapshot-342s-dir D:\_datefac\output\package_audit_snapshot_demo_handoff_342s --audit-labeled-package-342r-dir D:\_datefac\output\audit_labeled_export_candidate_package_342r --output-dir D:\_datefac\output\review_queue_excel_round_trip_343b
```

## 15. Completion report

Report in Chinese:

1. 343B decision
2. review_queue_schema_version
3. template_row_count
4. import_simulation_row_count
5. reviewed_result_row_count
6. confirmed_count
7. corrected_count
8. rejected_count
9. needs_source_check_count
10. skipped_count
11. validation_error_count
12. validation_warning_count
13. excel_template_generated
14. import_simulation_generated
15. reviewed_result_jsonl_generated
16. formal_client_export_allowed
17. client_ready
18. production_ready
19. ready_for_343c
20. recommended_343c_scope
21. qa_fail_count
22. no-write-back proof status
23. output directory
24. most important Excel/template/result artifacts
25. modified files
26. validation command results
27. git status summary
28. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
