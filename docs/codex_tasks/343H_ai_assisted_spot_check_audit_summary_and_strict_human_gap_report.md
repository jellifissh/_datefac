# 343H：AI-assisted Spot-check Audit Summary And Strict Human Gap Report

## 1. Positioning

343H consumes the completed 343G spot-check ingestion outputs and generates an audit summary plus strict-human-gap report for the AI-assisted review and spot-check chain.

This task summarizes what has been validated, what remains AI-assisted only, what still needs strict human review, and why formal client export remains forbidden.

343H is an audit-summary and gap-report task. It is not production apply, not formal client export, not Argilla integration, not a frontend implementation, not real LLM/VLM review, and not an upstream extraction rerun.

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
- `docs/codex_tasks/343G_ai_assisted_review_spot_check_result_ingestion.md`
- 343A schema summary / schema JSON
- 343D ingestion summary / AI-assisted disclosure
- 343E apply simulation summary / apply plan / audit gate / risk register
- 343F spot-check package summary / source-check todo / import contract
- 343G spot-check ingestion summary / QA / result JSONL / disclosure / workbook
- current git status

Expected current state:

- latest completed milestone = `343G AI-assisted Review Spot-check Result Ingestion`
- 343G decision = `AI_ASSISTED_SPOT_CHECK_INGESTION_343G_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- filled_spot_check_row_count = `30`
- valid_row_count = `30`
- invalid_row_count = `0`
- confirm_ai_assisted_result_count = `10`
- correct_ai_assisted_result_count = `0`
- reject_ai_assisted_result_count = `0`
- source_check_required_count = `19`
- keep_hold_count = `1`
- skip_spot_check_count = `0`
- validation_error_count = `0`
- validation_warning_count = `0`
- review_source_type = `AI_ASSISTED_REVIEW`
- spot_check_source_type = `AI_ASSISTED_SPOT_CHECK`
- not_pure_human_review = `true`
- strict_human_review_completed = `false`
- requires_strict_human_review = `true`
- apply_mode = `SIMULATION_ONLY`
- spot_check_result_ingested = `true`
- spot_check_result_jsonl_generated = `true`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- ready_for_343h = `true`
- recommended_343h_scope = `ai_assisted_spot_check_audit_summary_and_strict_human_gap_report`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, or delivery code. Do not write back to upstream workbooks. Do not generate formal client export. Do not perform real production apply. Do not claim strict human review is complete.

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

- `docs/codex_tasks/343H_ai_assisted_spot_check_audit_summary_and_strict_human_gap_report.md`
- `datefac/review_queue/audit_summary_343h.py`
- `datefac/benchmark/review_queue_audit_summary_343h.py`
- `datefac/benchmark/review_queue_audit_summary_343h_report.py`
- `tools/run_review_queue_audit_summary_343h.py`
- `tests/benchmark/test_review_queue_audit_summary_343h.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_spot_check_ingestion_343g`
- `D:/_datefac/output/review_queue_spot_check_package_343f`
- `D:/_datefac/output/review_queue_apply_simulation_343e`
- `D:/_datefac/output/review_queue_excel_ingestion_343d`
- `D:/_datefac/output/review_queue_schema_343a`

Required 343G files:

- `review_queue_spot_check_ingestion_343g_summary.json`
- `review_queue_spot_check_ingestion_343g_qa.json`
- `review_queue_spot_check_ingestion_343g_result.jsonl`
- `review_queue_spot_check_ingestion_343g_decision_summary.json`
- `review_queue_spot_check_ingestion_343g_ai_assisted_spot_check_disclosure.md`
- `review_queue_spot_check_ingestion_343g_no_write_back_proof.json`

Reference files:

- `review_queue_spot_check_package_343f_summary.json`
- `review_queue_spot_check_package_343f_source_check_todo.jsonl`
- `review_queue_apply_simulation_343e_summary.json`
- `review_queue_apply_simulation_343e_apply_plan.jsonl`
- `review_queue_apply_simulation_343e_risk_register.json`
- `review_queue_excel_ingestion_343d_summary.json`
- `review_queue_schema_343a_schema.json`

If required 343G files are missing, fail gracefully with a clear error. Do not fabricate audit conclusions.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_audit_summary_343h`

Output files:

- `review_queue_audit_summary_343h.xlsx`
- `review_queue_audit_summary_343h_summary.json`
- `review_queue_audit_summary_343h_manifest.json`
- `review_queue_audit_summary_343h_qa.json`
- `review_queue_audit_summary_343h_report.md`
- `review_queue_audit_summary_343h_strict_human_gap_report.md`
- `review_queue_audit_summary_343h_audit_matrix.json`
- `review_queue_audit_summary_343h_gap_items.jsonl`
- `review_queue_audit_summary_343h_confirmed_ai_assisted_items.jsonl`
- `review_queue_audit_summary_343h_source_check_backlog.jsonl`
- `review_queue_audit_summary_343h_client_export_gate.json`
- `review_queue_audit_summary_343h_next_action_plan.json`
- `review_queue_audit_summary_343h_no_write_back_proof.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_AUDIT_SUMMARY`
- `02_INPUT_343G_SUMMARY`
- `03_CHAIN_OVERVIEW`
- `04_AI_CONFIRMED_ITEMS`
- `05_SOURCE_CHECK_BACKLOG`
- `06_STRICT_HUMAN_GAP`
- `07_CLIENT_EXPORT_GATE`
- `08_AUDIT_MATRIX`
- `09_RISK_REGISTER`
- `10_NEXT_ACTION_PLAN`
- `11_343I_READINESS`
- `12_NO_WRITE_BACK`
- `13_NEXT_STEPS`

## 8. Core logic

### 8.1 Read 343G outputs

Read and validate 343G summary, QA, result JSONL, decision summary, disclosure, and no-write-back proof.

Fail if 343G is not ready or if any summary/output claims:

- strict pure human review completed
- formal client export allowed
- client ready
- production ready
- real production apply

### 8.2 Build audit chain overview

Build a stage-level matrix from 343A through 343G showing:

- milestone id
- decision
- input row count
- output row count
- review source type
- whether simulated or AI-assisted
- readiness flag
- downstream limitation
- formal/client/production readiness flags

### 8.3 Summarize AI-assisted confirmed items

From 343G result JSONL, summarize rows with:

- `CONFIRM_AI_ASSISTED_RESULT`
- resulting status `SPOT_CHECK_CONFIRMED_AI_ASSISTED`

These rows may be reported as AI-assisted spot-check confirmed, but must not be reported as strict human confirmed.

Generate `review_queue_audit_summary_343h_confirmed_ai_assisted_items.jsonl`.

### 8.4 Summarize strict-human gaps

Generate a strict human gap report covering:

- all AI-assisted confirmed rows that still lack strict human review
- all source-check-required rows
- all keep-hold / skipped / ambiguous rows
- stage-level reasons why formal client export remains blocked

Generate `review_queue_audit_summary_343h_gap_items.jsonl` and `review_queue_audit_summary_343h_strict_human_gap_report.md`.

### 8.5 Source-check backlog

Generate a source-check backlog from:

- 343G rows with `SOURCE_CHECK_REQUIRED`
- 343F source-check todo rows
- 343E hold-source-check rows

Deduplicate by `queue_item_id` / `review_item_id` where possible.

Expected based on 343G:

- 19 rows requiring source check

### 8.6 Client export gate

Generate a client export gate JSON that explicitly states:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `ai_assisted_only = true`
- `reason = AI-assisted review and spot-check are pilot validation artifacts, not strict human approval`

### 8.7 Next action plan

Generate a next action plan with two safe options:

1. Strict human review package for the 10 AI-assisted confirmed rows.
2. Source-check resolution package for the 19 source-check-required rows.

Recommend the next milestone based on safety:

- if the priority is to validate the 10 simulated-applied rows, recommend `343I Strict Human Review Package For AI-assisted Confirmed Rows`.
- if the priority is to clear uncertainty, recommend `343I Source-check Resolution Package`.

Default recommendation should be strict human review for the 10 AI-assisted confirmed rows because it directly addresses the formal gap for the only rows currently simulated-applied.

## 9. 343I readiness

If QA passes, set:

- `audit_summary_generated = true`
- `strict_human_gap_report_generated = true`
- `client_export_gate_generated = true`
- `ready_for_343i = true`
- `recommended_343i_scope = strict_human_review_package_for_ai_assisted_confirmed_rows`

Also preserve:

- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

If QA fails, set:

- `audit_summary_generated = false`
- `ready_for_343i = false`

## 10. Summary JSON

`review_queue_audit_summary_343h_summary.json` must include at least:

- `source_milestone = 343G`
- `decision`
- `review_queue_schema_version`
- `input_spot_check_result_row_count`
- `ai_assisted_confirmed_count`
- `source_check_required_count`
- `keep_hold_count`
- `strict_human_gap_item_count`
- `source_check_backlog_count`
- `audit_stage_count`
- `audit_summary_generated`
- `strict_human_gap_report_generated`
- `client_export_gate_generated`
- `next_action_plan_generated`
- `review_source_type = AI_ASSISTED_REVIEW`
- `spot_check_source_type = AI_ASSISTED_SPOT_CHECK`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `apply_mode = SIMULATION_ONLY`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343i`
- `recommended_343i_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready: `AI_ASSISTED_SPOT_CHECK_AUDIT_SUMMARY_343H_READY`
- otherwise: `AI_ASSISTED_SPOT_CHECK_AUDIT_SUMMARY_343H_NOT_READY`

## 11. QA requirements

Must check:

- 343G input exists and is ready
- 343G result JSONL exists and is readable
- all rows preserve AI-assisted disclosure
- no row claims strict pure human review
- no formal/client/production readiness flag is true
- audit matrix is generated
- strict-human-gap report is generated
- source-check backlog is generated
- client export gate is generated and remains false
- next action plan is generated
- no Argilla call is made
- no real production apply is performed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_audit_summary_343h_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343H summarizes the AI-assisted review and spot-check chain
- 10 rows are AI-assisted spot-check confirmed, not strict-human confirmed
- 19 rows still need source check
- 1 row remains hold/keep-hold
- why formal client export remains forbidden
- why strict human review is still incomplete
- what the next safe task should be

## 13. Ledger update

Update the project milestone ledger with:

- 343H completed or not-ready status
- inputs
- outputs
- key metrics
- QA result
- decision
- strict human gap summary
- client export gate summary
- next recommended task

If ready_for_343i is true, recommend:

`343I Strict Human Review Package For AI-assisted Confirmed Rows`

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\audit_summary_343h.py datefac\benchmark\review_queue_audit_summary_343h.py datefac\benchmark\review_queue_audit_summary_343h_report.py tools\run_review_queue_audit_summary_343h.py tests\benchmark\test_review_queue_audit_summary_343h.py
python -m pytest tests\benchmark\test_review_queue_audit_summary_343h.py -q
python tools\run_review_queue_audit_summary_343h.py --spot-check-ingestion-343g-dir D:\_datefac\output\review_queue_spot_check_ingestion_343g --spot-check-package-343f-dir D:\_datefac\output\review_queue_spot_check_package_343f --apply-simulation-343e-dir D:\_datefac\output\review_queue_apply_simulation_343e --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_audit_summary_343h
```

## 15. Completion report

Report in Chinese:

1. 343H decision
2. review_queue_schema_version
3. input_spot_check_result_row_count
4. ai_assisted_confirmed_count
5. source_check_required_count
6. keep_hold_count
7. strict_human_gap_item_count
8. source_check_backlog_count
9. audit_stage_count
10. audit_summary_generated
11. strict_human_gap_report_generated
12. client_export_gate_generated
13. next_action_plan_generated
14. review_source_type
15. spot_check_source_type
16. not_pure_human_review
17. strict_human_review_completed
18. requires_strict_human_review
19. apply_mode
20. formal_client_export_allowed
21. client_ready
22. production_ready
23. ready_for_343i
24. recommended_343i_scope
25. qa_fail_count
26. no-write-back proof status
27. output directory
28. most important Excel/report/gap/export-gate artifacts
29. modified files
30. validation command results
31. git status summary
32. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
