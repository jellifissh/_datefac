# 343F：AI-assisted Review Spot-check Package

## 1. Positioning

343F consumes the 343E apply-simulation and audit-gate outputs, then generates a focused spot-check package for AI-assisted review results.

The goal is to make the 10 simulation-applied rows, 20 held rows, and AI-assisted audit boundaries easy to inspect in a small reviewer-facing package. This task prepares the next human verification step; it must not claim that human spot-check has already been completed.

343F is a spot-check package generation task. It is not production apply, not formal client export, not Argilla integration, not a frontend implementation, not a real LLM/VLM review, and not an upstream extraction rerun.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/343A_review_queue_schema_and_human_review_ui_pilot.md`
- `docs/codex_tasks/343D_real_excel_review_result_ingestion.md`
- `docs/codex_tasks/343E_ai_assisted_review_result_apply_simulation_and_audit_gate.md`
- 343A schema summary / schema JSON
- 343D reviewed result summary / disclosure
- 343E summary / QA / apply plan / simulated sidecar / audit gate / risk register / AI-assisted boundary
- current git status

Expected current state:

- latest completed milestone = `343E AI-assisted Review Result Apply Simulation And Audit Gate`
- 343E decision = `AI_ASSISTED_REVIEW_APPLY_SIMULATION_343E_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- input_reviewed_result_row_count = `30`
- apply_plan_row_count = `30`
- simulated_sidecar_row_count = `10`
- hold_row_count = `20`
- simulate_confirm_apply_count = `10`
- simulate_correction_apply_count = `0`
- hold_rejected_count = `0`
- hold_source_check_required_count = `19`
- hold_skipped_count = `1`
- review_source_type = `AI_ASSISTED_REVIEW`
- not_pure_human_review = `true`
- strict_human_review_completed = `false`
- requires_human_spot_check = `true`
- apply_mode = `SIMULATION_ONLY`
- apply_simulation_completed = `true`
- audit_gate_passed_for_spot_check_package = `true`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- ready_for_343f = `true`
- recommended_343f_scope = `ai_assisted_review_spot_check_package`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, or delivery code. Do not write back to upstream workbooks. Do not generate formal client export. Do not perform real production apply. Do not claim human spot-check is complete.

Preserve these flags:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `strict_human_review_completed = false`
- `requires_human_spot_check = true`

Preserve AI-assisted disclosure:

- `review_source_type = AI_ASSISTED_REVIEW`
- `not_pure_human_review = true`
- `apply_mode = SIMULATION_ONLY`

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343F_ai_assisted_review_spot_check_package.md`
- `datefac/review_queue/spot_check_package_343f.py`
- `datefac/benchmark/review_queue_spot_check_package_343f.py`
- `datefac/benchmark/review_queue_spot_check_package_343f_report.py`
- `tools/run_review_queue_spot_check_package_343f.py`
- `tests/benchmark/test_review_queue_spot_check_package_343f.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_apply_simulation_343e`
- `D:/_datefac/output/review_queue_excel_ingestion_343d`
- `D:/_datefac/output/review_queue_schema_343a`

Required 343E files:

- `review_queue_apply_simulation_343e_summary.json`
- `review_queue_apply_simulation_343e_qa.json`
- `review_queue_apply_simulation_343e_apply_plan.jsonl`
- `review_queue_apply_simulation_343e_simulated_sidecar.jsonl`
- `review_queue_apply_simulation_343e_audit_gate.json`
- `review_queue_apply_simulation_343e_risk_register.json`
- `review_queue_apply_simulation_343e_ai_assisted_boundary.md`
- `review_queue_apply_simulation_343e_no_write_back_proof.json`

Reference files:

- `review_queue_excel_ingestion_343d_summary.json`
- `review_queue_excel_ingestion_343d_reviewed_result.jsonl`
- `review_queue_schema_343a_schema.json`
- `review_queue_schema_343a_json_schema.json`

If required 343E files are missing, fail gracefully with a clear error. Do not fabricate apply simulation results.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_spot_check_package_343f`

Output files:

- `review_queue_spot_check_package_343f.xlsx`
- `review_queue_spot_check_package_343f_summary.json`
- `review_queue_spot_check_package_343f_manifest.json`
- `review_queue_spot_check_package_343f_qa.json`
- `review_queue_spot_check_package_343f_report.md`
- `review_queue_spot_check_package_343f_review_template.xlsx`
- `review_queue_spot_check_package_343f_spot_check_items.jsonl`
- `review_queue_spot_check_package_343f_priority_plan.json`
- `review_queue_spot_check_package_343f_source_check_todo.jsonl`
- `review_queue_spot_check_package_343f_reviewer_instructions.md`
- `review_queue_spot_check_package_343f_expected_import_contract.json`
- `review_queue_spot_check_package_343f_ai_assisted_boundary.md`
- `review_queue_spot_check_package_343f_no_write_back_proof.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_PACKAGE_SUMMARY`
- `02_INPUT_343E_SUMMARY`
- `03_SPOT_CHECK_ITEMS`
- `04_REVIEW_TEMPLATE`
- `05_SIM_APPLIED_ROWS`
- `06_HOLD_ROWS`
- `07_SOURCE_CHECK_TODO`
- `08_PRIORITY_PLAN`
- `09_RISK_REGISTER`
- `10_AI_BOUNDARY`
- `11_IMPORT_CONTRACT`
- `12_343G_READINESS`
- `13_NO_WRITE_BACK`
- `14_NEXT_STEPS`

## 8. Core logic

### 8.1 Read 343E outputs

Read and validate the 343E summary, apply plan, simulated sidecar, audit gate, risk register, and AI-assisted boundary.

Fail if any row or summary claims:

- strict pure human review completed
- formal client export allowed
- client ready
- production ready
- real production apply

### 8.2 Build spot-check population

Build a spot-check population from:

- simulated-applied rows from 343E simulated sidecar
- held rows from the 343E apply plan
- risk register entries

Expected based on 343E:

- 10 simulated-applied rows
- 19 source-check-required held rows
- 1 skipped held row

### 8.3 Deterministic priority plan

Create deterministic priority tiers:

- `P0_SOURCE_CHECK_REQUIRED` for `HOLD_SOURCE_CHECK_REQUIRED`
- `P1_AI_ASSISTED_SIM_APPLIED` for simulation-applied rows
- `P2_SKIPPED_OR_AMBIGUOUS` for skipped rows
- `P3_AUDIT_BOUNDARY_ONLY` for package-level disclosure checks

Recommended package composition:

- include all 10 simulated-applied rows
- include all 19 source-check-required rows
- include the skipped row

Because the package is only 30 rows, do not downsample unless a future larger input requires it.

### 8.4 Review template

Generate a fillable spot-check review template with non-editable evidence/candidate/action fields and editable spot-check columns:

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

- rows with source-check-required action should default to blank decision but include recommended decision `SOURCE_CHECK_REQUIRED`
- simulated-applied rows should default to blank decision but include recommended decision `CONFIRM_AI_ASSISTED_RESULT` only as a suggestion, not as completed review
- skipped rows should default to blank decision with recommended decision `KEEP_HOLD`
- no spot-check decision should be treated as completed until a filled workbook is ingested in 343G

### 8.5 Source-check todo

Generate `review_queue_spot_check_package_343f_source_check_todo.jsonl` for held rows requiring source check. Include:

- identity
- metric/year/value/unit candidate
- source reference fields
- reason for source check
- suggested reviewer action
- AI-assisted boundary fields

### 8.6 Expected import contract for 343G

Generate a JSON import contract describing the expected filled spot-check workbook shape for the next task:

- required sheet name
- required identity columns
- editable spot-check columns
- allowed spot-check decisions
- correction validation rules
- expected input path pattern for 343G

343F must not ingest spot-check results. It must set a waiting-for-spot-check state.

## 9. 343G readiness

If QA passes, set:

- `spot_check_package_generated = true`
- `waiting_for_spot_check = true`
- `spot_check_result_ingested = false`
- `ready_for_343g = false`
- `recommended_343g_scope = ai_assisted_review_spot_check_result_ingestion_after_user_fills_workbook`

This is intentional: 343G should start only after the user fills the spot-check workbook.

## 10. Summary JSON

`review_queue_spot_check_package_343f_summary.json` must include at least:

- `source_milestone = 343E`
- `decision`
- `review_queue_schema_version`
- `input_apply_plan_row_count`
- `input_simulated_sidecar_row_count`
- `spot_check_item_count`
- `simulated_applied_spot_check_count`
- `source_check_required_count`
- `skipped_hold_count`
- `priority_tier_count`
- `review_template_generated`
- `source_check_todo_generated`
- `expected_import_contract_generated`
- `review_source_type = AI_ASSISTED_REVIEW`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_human_spot_check = true`
- `apply_mode = SIMULATION_ONLY`
- `spot_check_package_generated`
- `waiting_for_spot_check`
- `spot_check_result_ingested = false`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343g = false`
- `recommended_343g_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready for user spot-check: `AI_ASSISTED_REVIEW_SPOT_CHECK_PACKAGE_343F_WAITING_FOR_SPOT_CHECK`
- otherwise: `AI_ASSISTED_REVIEW_SPOT_CHECK_PACKAGE_343F_NOT_READY`

## 11. QA requirements

Must check:

- 343E input exists and is ready
- apply plan JSONL exists and is readable
- simulated sidecar JSONL exists and is readable
- audit gate passed for spot-check package
- all rows preserve AI-assisted disclosure
- no row claims strict pure human review
- no formal/client/production readiness flag is true
- spot-check package workbook is generated
- spot-check review template is generated
- source-check todo JSONL is generated
- expected import contract is generated
- editable spot-check columns exist
- allowed decision list is present
- `waiting_for_spot_check` is true
- `spot_check_result_ingested` is false
- no Argilla call is made
- no real production apply is performed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_spot_check_package_343f_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343F creates a spot-check package for AI-assisted review results
- it does not ingest spot-check results yet
- it does not represent completed strict human review
- which rows need source check and which rows were simulated-applied
- why formal client export remains forbidden
- why production readiness remains false
- how the reviewer should fill the spot-check workbook
- recommended next step: 343G spot-check result ingestion after the user fills the workbook

## 13. Ledger update

Update the project milestone ledger with:

- 343F completed as waiting-for-spot-check package generation
- inputs
- outputs
- key metrics
- QA result
- decision
- AI-assisted boundary
- next required user action
- next recommended task after user fills workbook

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\spot_check_package_343f.py datefac\benchmark\review_queue_spot_check_package_343f.py datefac\benchmark\review_queue_spot_check_package_343f_report.py tools\run_review_queue_spot_check_package_343f.py tests\benchmark\test_review_queue_spot_check_package_343f.py
python -m pytest tests\benchmark\test_review_queue_spot_check_package_343f.py -q
python tools\run_review_queue_spot_check_package_343f.py --apply-simulation-343e-dir D:\_datefac\output\review_queue_apply_simulation_343e --excel-ingestion-343d-dir D:\_datefac\output\review_queue_excel_ingestion_343d --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_spot_check_package_343f
```

## 15. Completion report

Report in Chinese:

1. 343F decision
2. review_queue_schema_version
3. input_apply_plan_row_count
4. input_simulated_sidecar_row_count
5. spot_check_item_count
6. simulated_applied_spot_check_count
7. source_check_required_count
8. skipped_hold_count
9. priority_tier_count
10. review_template_generated
11. source_check_todo_generated
12. expected_import_contract_generated
13. review_source_type
14. not_pure_human_review
15. strict_human_review_completed
16. requires_human_spot_check
17. apply_mode
18. spot_check_package_generated
19. waiting_for_spot_check
20. spot_check_result_ingested
21. formal_client_export_allowed
22. client_ready
23. production_ready
24. ready_for_343g
25. recommended_343g_scope
26. qa_fail_count
27. no-write-back proof status
28. output directory
29. most important Excel/template/source-check/artifacts
30. modified files
31. validation command results
32. git status summary
33. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
