# 343C：Real Excel Review Queue Pilot

## 1. Positioning

343C is the first real human-review preparation task after the 343A Review Queue schema and the 343B Excel round-trip simulation.

343C must generate a real Excel review package from the Review Queue sample/schema, with reviewer instructions and validation expectations. It must not simulate reviewer decisions, must not claim real human review has happened, and must not ingest reviewed results yet.

The purpose is to create a small, safe, fillable review workbook that the user can inspect and manually review later. The follow-up task will ingest a human-filled workbook.

343C is not Argilla integration, not a production UI, not a formal client export, and not an upstream extraction rerun.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/343A_review_queue_schema_and_human_review_ui_pilot.md`
- `docs/codex_tasks/343B_excel_round_trip_review_queue_pilot.md`
- 343A output summary / qa / schema JSON / sample items JSONL / workbook
- 343B output summary / qa / report / review template / import simulation / reviewed result JSONL
- current git status

Expected current state:

- latest completed milestone = `343B Excel Round-trip Review Queue Pilot`
- 343B decision = `REVIEW_QUEUE_EXCEL_ROUND_TRIP_343B_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- template_row_count = `51`
- import_simulation_row_count = `51`
- reviewed_result_row_count = `51`
- validation_error_count = `0`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- ready_for_343c = `true`
- recommended_343c_scope = `argilla_human_review_ui_pilot`, but this task intentionally performs a safer real Excel review pilot first
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, or delivery code. Do not write back to upstream workbooks. Do not generate formal client export. Do not fabricate human review. Preserve `formal_client_export_allowed=false`, `client_ready=false`, and `production_ready=false`.

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343C_real_excel_review_queue_pilot.md`
- `datefac/review_queue/real_excel_review_343c.py`
- `datefac/benchmark/review_queue_real_excel_review_343c.py`
- `datefac/benchmark/review_queue_real_excel_review_343c_report.py`
- `tools/run_review_queue_real_excel_review_343c.py`
- `tests/benchmark/test_review_queue_real_excel_review_343c.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_excel_round_trip_343b`
- `D:/_datefac/output/review_queue_schema_343a`
- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s`

Primary files:

- `review_queue_excel_round_trip_343b_summary.json`
- `review_queue_excel_round_trip_343b_qa.json`
- `review_queue_excel_round_trip_343b_review_template.xlsx`
- `review_queue_excel_round_trip_343b.xlsx`
- `review_queue_schema_343a_schema.json`
- `review_queue_schema_343a_json_schema.json`
- `review_queue_schema_343a_sample_items.jsonl`
- `review_queue_schema_343a_excel_template_spec.json`

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_real_excel_review_343c`

Output files:

- `review_queue_real_excel_review_343c.xlsx`
- `review_queue_real_excel_review_343c_summary.json`
- `review_queue_real_excel_review_343c_manifest.json`
- `review_queue_real_excel_review_343c_qa.json`
- `review_queue_real_excel_review_343c_report.md`
- `review_queue_real_excel_review_343c_review_template.xlsx`
- `review_queue_real_excel_review_343c_reviewer_instructions.md`
- `review_queue_real_excel_review_343c_fill_guide.md`
- `review_queue_real_excel_review_343c_expected_import_contract.json`
- `review_queue_real_excel_review_343c_no_write_back_proof.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_REVIEW_SUMMARY`
- `02_INPUT_343B_SUMMARY`
- `03_REVIEW_QUEUE_ITEMS`
- `04_FILLABLE_REVIEW`
- `05_DECISION_RULES`
- `06_VALIDATION_RULES`
- `07_FIELD_GUIDE`
- `08_RISK_CONTEXT`
- `09_IMPORT_CONTRACT`
- `10_WAITING_FOR_REVIEW`
- `11_343D_READINESS`
- `12_NO_WRITE_BACK`
- `13_NEXT_STEPS`

## 8. Core logic

### 8.1 Real review template generation

Read the 343B review template and/or 343A sample queue. Generate a real fillable review template for a small pilot batch.

Recommended pilot size: up to 30 rows, selected deterministically:

- human-reviewed audit examples where available
- simulated-direct rows requiring later audit
- simulated-corrected rows requiring later audit
- summary-derived/high-risk examples when present

Do not use 343B's simulated reviewer decisions as human evidence. They may be used only as a schema mechanics reference.

### 8.2 Fillable columns

The review sheet must include non-editable identity/evidence/candidate columns and editable reviewer columns:

- `reviewer_decision`
- `reviewer_metric_standardized`
- `reviewer_year_standardized`
- `reviewer_value_numeric`
- `reviewer_normalized_unit`
- `reviewer_note`
- `reviewer_id`
- `reviewed_at`

Allowed reviewer decisions:

- `CONFIRM`
- `CORRECT`
- `REJECT`
- `NEEDS_SOURCE_CHECK`
- `SKIP`

The workbook should make it obvious which fields are to be filled by the reviewer. If styling helpers already exist, use them. If not, use simple pandas/openpyxl output without introducing a heavy dependency.

### 8.3 Instructions and fill guide

Generate Markdown instructions explaining:

- what the reviewer should inspect
- how to choose each decision
- which corrected fields are required for `CORRECT`
- why simulated rows require extra caution
- why this is not a formal client export
- how the filled workbook should be saved for the next ingestion task

### 8.4 Import contract for 343D

Generate a JSON import contract describing the expected filled workbook shape for the next task:

- required sheets
- required identity columns
- editable reviewer columns
- allowed decisions
- validation rules
- expected next input path pattern

343C must not ingest filled results. It must set a waiting-for-human-review state.

## 9. 343D readiness

If QA passes, set:

- `real_review_template_generated = true`
- `waiting_for_human_review = true`
- `reviewed_result_ingested = false`
- `ready_for_343d = false`
- `recommended_343d_scope = real_excel_review_result_ingestion_after_user_fills_workbook`

This is intentional: 343D should start only after the user provides a human-filled workbook.

## 10. Summary JSON

`review_queue_real_excel_review_343c_summary.json` must include at least:

- `source_milestone = 343B`
- `decision`
- `review_queue_schema_version`
- `real_review_template_row_count`
- `fillable_review_row_count`
- `human_reviewed_audit_row_count`
- `simulated_direct_review_row_count`
- `simulated_corrected_review_row_count`
- `summary_derived_review_row_count`
- `allowed_decision_count`
- `real_review_template_generated`
- `reviewer_instructions_generated`
- `fill_guide_generated`
- `expected_import_contract_generated`
- `waiting_for_human_review`
- `reviewed_result_ingested = false`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343d = false`
- `recommended_343d_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready for user review: `REVIEW_QUEUE_REAL_EXCEL_REVIEW_343C_WAITING_FOR_HUMAN_REVIEW`
- otherwise: `REVIEW_QUEUE_REAL_EXCEL_REVIEW_343C_NOT_READY`

## 11. QA requirements

Must check:

- 343B input exists and is ready
- 343A schema/sample input exists
- real review template is generated
- reviewer instructions are generated
- fill guide is generated
- expected import contract is generated
- editable reviewer columns exist
- allowed decision list is present
- no simulated/imported reviewer decision is treated as real human evidence
- `reviewed_result_ingested` is false
- `waiting_for_human_review` is true
- no formal/client/production readiness flag is true
- no Argilla call is made
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_real_excel_review_343c_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343C generates a real Excel review template
- it does not ingest reviewed results yet
- it does not represent completed human review
- it does not implement Argilla or a full UI
- how the reviewer should fill the workbook
- why formal client export remains forbidden
- the next task after user filling is 343D real Excel review result ingestion

## 13. Ledger update

Update the project milestone ledger with:

- 343C completed as waiting-for-human-review template generation
- status
- inputs
- outputs
- key metrics
- QA result
- decision
- next required user action
- next recommended task after user fills workbook

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\real_excel_review_343c.py datefac\benchmark\review_queue_real_excel_review_343c.py datefac\benchmark\review_queue_real_excel_review_343c_report.py tools\run_review_queue_real_excel_review_343c.py tests\benchmark\test_review_queue_real_excel_review_343c.py
python -m pytest tests\benchmark\test_review_queue_real_excel_review_343c.py -q
python tools\run_review_queue_real_excel_review_343c.py --excel-round-trip-343b-dir D:\_datefac\output\review_queue_excel_round_trip_343b --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --snapshot-342s-dir D:\_datefac\output\package_audit_snapshot_demo_handoff_342s --output-dir D:\_datefac\output\review_queue_real_excel_review_343c
```

## 15. Completion report

Report in Chinese:

1. 343C decision
2. review_queue_schema_version
3. real_review_template_row_count
4. fillable_review_row_count
5. human_reviewed_audit_row_count
6. simulated_direct_review_row_count
7. simulated_corrected_review_row_count
8. summary_derived_review_row_count
9. allowed_decision_count
10. real_review_template_generated
11. reviewer_instructions_generated
12. fill_guide_generated
13. expected_import_contract_generated
14. waiting_for_human_review
15. reviewed_result_ingested
16. formal_client_export_allowed
17. client_ready
18. production_ready
19. ready_for_343d
20. recommended_343d_scope
21. qa_fail_count
22. no-write-back proof status
23. output directory
24. most important Excel/template/fill guide artifacts
25. modified files
26. validation command results
27. git status summary
28. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
