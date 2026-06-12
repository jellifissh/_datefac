# 343E：AI-assisted Review Result Apply Simulation And Audit Gate

## 1. Positioning

343E consumes the 343D reviewed-result sidecar and performs an apply simulation plus audit gate for AI-assisted review results.

The input review result is explicitly `AI_ASSISTED_REVIEW`, not strict pure human review. This task must simulate how valid reviewed decisions could affect downstream queue/application state, while preserving audit boundaries and avoiding any formal client export claim.

343E is an apply-simulation and audit-gate task. It is not production apply, not formal client export, not a production review service, not Argilla integration, not a frontend implementation, and not an upstream extraction rerun.

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
- `docs/codex_tasks/343D_real_excel_review_result_ingestion.md`
- 343A output summary / schema JSON / sample items JSONL
- 343C output summary / expected import contract
- 343D output summary / qa / reviewed result JSONL / disclosure / workbook
- current git status

Expected current state:

- latest completed milestone = `343D Real Excel Review Result Ingestion`
- 343D decision = `REVIEW_QUEUE_EXCEL_INGESTION_343D_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- filled_row_count = `30`
- valid_row_count = `30`
- invalid_row_count = `0`
- confirmed_count = `10`
- corrected_count = `0`
- rejected_count = `0`
- needs_source_check_count = `19`
- skipped_count = `1`
- validation_error_count = `0`
- review_source_type = `AI_ASSISTED_REVIEW`
- not_pure_human_review = `true`
- strict_human_review_completed = `false`
- requires_human_spot_check = `true`
- reviewed_result_ingested = `true`
- reviewed_result_jsonl_generated = `true`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- ready_for_343e = `true`
- recommended_343e_scope = `ai_assisted_review_result_apply_simulation_and_audit_gate`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, or delivery code. Do not write back to upstream workbooks. Do not generate formal client export. Do not perform real production apply.

Preserve these flags:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

Preserve AI-assisted disclosure:

- `review_source_type = AI_ASSISTED_REVIEW`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_human_spot_check = true`

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343E_ai_assisted_review_result_apply_simulation_and_audit_gate.md`
- `datefac/review_queue/apply_simulation_343e.py`
- `datefac/benchmark/review_queue_apply_simulation_343e.py`
- `datefac/benchmark/review_queue_apply_simulation_343e_report.py`
- `tools/run_review_queue_apply_simulation_343e.py`
- `tests/benchmark/test_review_queue_apply_simulation_343e.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_excel_ingestion_343d`
- `D:/_datefac/output/review_queue_real_excel_review_343c`
- `D:/_datefac/output/review_queue_schema_343a`

Required 343D files:

- `review_queue_excel_ingestion_343d_summary.json`
- `review_queue_excel_ingestion_343d_qa.json`
- `review_queue_excel_ingestion_343d_reviewed_result.jsonl`
- `review_queue_excel_ingestion_343d_ai_assisted_review_disclosure.md`
- `review_queue_excel_ingestion_343d_no_write_back_proof.json`

Reference files:

- `review_queue_schema_343a_schema.json`
- `review_queue_schema_343a_json_schema.json`
- `review_queue_real_excel_review_343c_expected_import_contract.json`

If the 343D reviewed-result JSONL is missing, fail gracefully with a clear error. Do not fabricate reviewed results.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_apply_simulation_343e`

Output files:

- `review_queue_apply_simulation_343e.xlsx`
- `review_queue_apply_simulation_343e_summary.json`
- `review_queue_apply_simulation_343e_manifest.json`
- `review_queue_apply_simulation_343e_qa.json`
- `review_queue_apply_simulation_343e_report.md`
- `review_queue_apply_simulation_343e_apply_plan.jsonl`
- `review_queue_apply_simulation_343e_simulated_sidecar.jsonl`
- `review_queue_apply_simulation_343e_audit_gate.json`
- `review_queue_apply_simulation_343e_risk_register.json`
- `review_queue_apply_simulation_343e_ai_assisted_boundary.md`
- `review_queue_apply_simulation_343e_no_write_back_proof.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_SIM_SUMMARY`
- `02_INPUT_343D_SUMMARY`
- `03_REVIEWED_RESULTS`
- `04_APPLY_PLAN`
- `05_SIMULATED_SIDECAR`
- `06_HOLD_ROWS`
- `07_AUDIT_GATE`
- `08_RISK_REGISTER`
- `09_AI_ASSISTED_BOUNDARY`
- `10_343F_READINESS`
- `11_NO_WRITE_BACK`
- `12_NEXT_STEPS`

## 8. Core logic

### 8.1 Read reviewed-result sidecar

Read `review_queue_excel_ingestion_343d_reviewed_result.jsonl` and validate that every row contains:

- queue/review identity
- reviewer decision
- resulting status
- validation status
- review source disclosure fields
- formal/client/production readiness flags all false

Fail if any row claims strict pure human review or production readiness.

### 8.2 Determine apply simulation action

Map ingested decisions/statuses to simulated downstream actions:

- `CONFIRM` / `REVIEWED_CONFIRMED` -> `SIMULATE_CONFIRM_APPLY`
- `CORRECT` / `REVIEWED_CORRECTED` -> `SIMULATE_CORRECTION_APPLY`
- `REJECT` / `REJECTED` -> `HOLD_REJECTED`
- `NEEDS_SOURCE_CHECK` -> `HOLD_SOURCE_CHECK_REQUIRED`
- `SKIP` / `SKIPPED` -> `HOLD_SKIPPED`

Because the review source is AI-assisted, even simulated apply rows must keep:

- `apply_mode = SIMULATION_ONLY`
- `requires_human_spot_check = true`
- `strict_human_review_completed = false`
- `not_formal_export = true`

### 8.3 Generate apply plan JSONL

Generate `review_queue_apply_simulation_343e_apply_plan.jsonl` with one row per reviewed result:

- identity
- original reviewer decision/status
- simulated downstream action
- apply eligibility classification
- risk notes
- audit boundary fields
- no-write-back marker

### 8.4 Generate simulated sidecar JSONL

Generate `review_queue_apply_simulation_343e_simulated_sidecar.jsonl` for rows eligible for simulated application only.

Expected based on current 343D values:

- confirmed rows should be eligible for simulated confirm apply
- corrected rows would be eligible for simulated correction apply if present
- needs-source-check rows must be held
- skipped rows must be held
- rejected rows must be held

Do not write back to original queue artifacts or upstream workbooks.

### 8.5 Audit gate

Generate an audit gate that decides whether the simulated result may proceed to the next review stage.

Expected outcome:

- formal client export remains forbidden
- production readiness remains false
- strict human review remains incomplete
- human spot-check remains required
- ready_for_343f may be true only for a spot-check package or human verification package, not production export

### 8.6 Risk register

Generate risk register entries for:

- AI-assisted review source
- 19 rows needing source check
- skipped row
- absence of strict human review
- any missing evidence/source limitations found in reviewed rows

## 9. 343F readiness

If QA passes and simulation is generated, set:

- `apply_simulation_completed = true`
- `ready_for_343f = true`
- `recommended_343f_scope = ai_assisted_review_spot_check_package`

Also preserve:

- `strict_human_review_completed = false`
- `requires_human_spot_check = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

If QA fails, set:

- `apply_simulation_completed = false`
- `ready_for_343f = false`

## 10. Summary JSON

`review_queue_apply_simulation_343e_summary.json` must include at least:

- `source_milestone = 343D`
- `decision`
- `review_queue_schema_version`
- `input_reviewed_result_row_count`
- `apply_plan_row_count`
- `simulated_sidecar_row_count`
- `hold_row_count`
- `simulate_confirm_apply_count`
- `simulate_correction_apply_count`
- `hold_rejected_count`
- `hold_source_check_required_count`
- `hold_skipped_count`
- `review_source_type = AI_ASSISTED_REVIEW`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_human_spot_check = true`
- `apply_mode = SIMULATION_ONLY`
- `apply_simulation_completed`
- `audit_gate_passed_for_spot_check_package`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343f`
- `recommended_343f_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready: `AI_ASSISTED_REVIEW_APPLY_SIMULATION_343E_READY`
- otherwise: `AI_ASSISTED_REVIEW_APPLY_SIMULATION_343E_NOT_READY`

## 11. QA requirements

Must check:

- 343D input exists and is ready
- reviewed-result JSONL exists and is readable
- all rows preserve AI-assisted disclosure
- no row claims strict pure human review
- no formal/client/production readiness flag is true
- apply plan JSONL is generated
- simulated sidecar JSONL is generated for eligible simulation-only rows
- hold rows are correctly classified
- audit gate JSON is generated
- risk register JSON is generated
- no real production apply is performed
- no Argilla call is made
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_apply_simulation_343e_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343E performs simulation-only application of AI-assisted reviewed results
- which rows would be simulated-applied and which rows are held
- why human spot-check is still required
- why formal client export remains forbidden
- why production readiness remains false
- recommended next step: 343F AI-assisted review spot-check package, not production export

## 13. Ledger update

Update the project milestone ledger with:

- 343E completed or not-ready status
- inputs
- outputs
- key metrics
- QA result
- decision
- AI-assisted boundary
- next recommended task

If ready_for_343f is true, recommend:

`343F AI-assisted Review Spot-check Package`

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\apply_simulation_343e.py datefac\benchmark\review_queue_apply_simulation_343e.py datefac\benchmark\review_queue_apply_simulation_343e_report.py tools\run_review_queue_apply_simulation_343e.py tests\benchmark\test_review_queue_apply_simulation_343e.py
python -m pytest tests\benchmark\test_review_queue_apply_simulation_343e.py -q
python tools\run_review_queue_apply_simulation_343e.py --excel-ingestion-343d-dir D:\_datefac\output\review_queue_excel_ingestion_343d --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_apply_simulation_343e
```

## 15. Completion report

Report in Chinese:

1. 343E decision
2. review_queue_schema_version
3. input_reviewed_result_row_count
4. apply_plan_row_count
5. simulated_sidecar_row_count
6. hold_row_count
7. simulate_confirm_apply_count
8. simulate_correction_apply_count
9. hold_rejected_count
10. hold_source_check_required_count
11. hold_skipped_count
12. review_source_type
13. not_pure_human_review
14. strict_human_review_completed
15. requires_human_spot_check
16. apply_mode
17. apply_simulation_completed
18. audit_gate_passed_for_spot_check_package
19. formal_client_export_allowed
20. client_ready
21. production_ready
22. ready_for_343f
23. recommended_343f_scope
24. qa_fail_count
25. no-write-back proof status
26. output directory
27. most important Excel/apply plan/sidecar/audit artifacts
28. modified files
29. validation command results
30. git status summary
31. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
