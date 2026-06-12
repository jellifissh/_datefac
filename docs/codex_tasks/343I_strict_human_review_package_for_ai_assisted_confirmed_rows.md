# 343I：Strict Human Review Package For AI-assisted Confirmed Rows

## 1. Positioning

343I consumes the 343H audit summary and creates a strict-human-review package for the 10 rows that are currently only AI-assisted spot-check confirmed.

The purpose is to move from AI-assisted validation toward strict human verification. This task only prepares the package and template. It must not ingest strict human review results yet, must not claim strict human review has been completed, and must not enable formal client export.

343I is a strict-human-review package generation task. It is not production apply, not formal client export, not Argilla integration, not a frontend implementation, not real LLM/VLM review, and not an upstream extraction rerun.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/343H_ai_assisted_spot_check_audit_summary_and_strict_human_gap_report.md`
- 343A schema summary / schema JSON
- 343G spot-check ingestion summary / result JSONL / disclosure
- 343H summary / QA / report / strict human gap report / audit matrix / confirmed AI-assisted items / source-check backlog / client export gate / next action plan
- current git status

Expected current state:

- latest completed milestone = `343H AI-assisted Spot-check Audit Summary And Strict Human Gap Report`
- 343H decision = `AI_ASSISTED_SPOT_CHECK_AUDIT_SUMMARY_343H_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- input_spot_check_result_row_count = `30`
- ai_assisted_confirmed_count = `10`
- source_check_required_count = `19`
- keep_hold_count = `1`
- strict_human_gap_item_count = `30`
- source_check_backlog_count = `19`
- audit_summary_generated = `true`
- strict_human_gap_report_generated = `true`
- client_export_gate_generated = `true`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- strict_human_review_completed = `false`
- requires_strict_human_review = `true`
- ready_for_343i = `true`
- recommended_343i_scope = `strict_human_review_package_for_ai_assisted_confirmed_rows`
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

Preserve source disclosure:

- source rows are currently AI-assisted confirmed only
- strict human review is still pending
- any package generated here is waiting for strict human review

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343I_strict_human_review_package_for_ai_assisted_confirmed_rows.md`
- `datefac/review_queue/strict_human_review_package_343i.py`
- `datefac/benchmark/review_queue_strict_human_review_package_343i.py`
- `datefac/benchmark/review_queue_strict_human_review_package_343i_report.py`
- `tools/run_review_queue_strict_human_review_package_343i.py`
- `tests/benchmark/test_review_queue_strict_human_review_package_343i.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g`
- `D:/_datefac/output/review_queue_apply_simulation_343e`
- `D:/_datefac/output/review_queue_schema_343a`

Required 343H files:

- `review_queue_audit_summary_343h_summary.json`
- `review_queue_audit_summary_343h_qa.json`
- `review_queue_audit_summary_343h_report.md`
- `review_queue_audit_summary_343h_strict_human_gap_report.md`
- `review_queue_audit_summary_343h_confirmed_ai_assisted_items.jsonl`
- `review_queue_audit_summary_343h_gap_items.jsonl`
- `review_queue_audit_summary_343h_client_export_gate.json`
- `review_queue_audit_summary_343h_next_action_plan.json`
- `review_queue_audit_summary_343h_no_write_back_proof.json`

Reference files:

- `review_queue_spot_check_ingestion_343g_result.jsonl`
- `review_queue_apply_simulation_343e_apply_plan.jsonl`
- `review_queue_schema_343a_schema.json`
- `review_queue_schema_343a_json_schema.json`

If required 343H files are missing, fail gracefully with a clear error. Do not fabricate strict human review rows.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_strict_human_review_package_343i`

Output files:

- `review_queue_strict_human_review_package_343i.xlsx`
- `review_queue_strict_human_review_package_343i_summary.json`
- `review_queue_strict_human_review_package_343i_manifest.json`
- `review_queue_strict_human_review_package_343i_qa.json`
- `review_queue_strict_human_review_package_343i_report.md`
- `review_queue_strict_human_review_package_343i_review_template.xlsx`
- `review_queue_strict_human_review_package_343i_review_items.jsonl`
- `review_queue_strict_human_review_package_343i_reviewer_instructions.md`
- `review_queue_strict_human_review_package_343i_fill_guide.md`
- `review_queue_strict_human_review_package_343i_expected_import_contract.json`
- `review_queue_strict_human_review_package_343i_client_export_boundary.md`
- `review_queue_strict_human_review_package_343i_no_write_back_proof.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_PACKAGE_SUMMARY`
- `02_INPUT_343H_SUMMARY`
- `03_STRICT_REVIEW_ITEMS`
- `04_REVIEW_TEMPLATE`
- `05_EVIDENCE_CONTEXT`
- `06_DECISION_RULES`
- `07_VALIDATION_RULES`
- `08_CLIENT_EXPORT_BOUNDARY`
- `09_IMPORT_CONTRACT`
- `10_343J_READINESS`
- `11_NO_WRITE_BACK`
- `12_NEXT_STEPS`

## 8. Core logic

### 8.1 Read 343H confirmed AI-assisted items

Read `review_queue_audit_summary_343h_confirmed_ai_assisted_items.jsonl` and validate that it contains the AI-assisted confirmed rows from 343H.

Expected based on 343H:

- 10 AI-assisted confirmed rows

Fail if any row claims strict human review completion or client/production readiness.

### 8.2 Build strict human review package

Generate a package only for the AI-assisted confirmed rows. The package should include enough identity, candidate, evidence, and AI-assisted decision context for a strict human reviewer to verify or reject the result.

Do not include the 19 source-check-required rows in this package except as context in summary sheets. Those belong to a separate source-check resolution task.

### 8.3 Fillable strict review template

Generate a fillable strict human review template with non-editable identity/evidence/candidate fields and editable strict-review columns:

- `strict_review_decision`
- `strict_review_metric_standardized`
- `strict_review_year_standardized`
- `strict_review_value_numeric`
- `strict_review_normalized_unit`
- `strict_review_note`
- `strict_reviewer_id`
- `strict_reviewed_at`

Allowed strict review decisions:

- `STRICT_CONFIRM`
- `STRICT_CORRECT`
- `STRICT_REJECT`
- `STRICT_NEEDS_SOURCE_CHECK`
- `STRICT_DEFER`

Rules:

- `STRICT_CONFIRM` means the strict reviewer verifies the AI-assisted result.
- `STRICT_CORRECT` requires metric/year/value/unit corrected fields.
- `STRICT_REJECT` requires a note.
- `STRICT_NEEDS_SOURCE_CHECK` requires a note.
- `STRICT_DEFER` should include a reason when possible.
- No strict review decision should be prefilled as completed.

### 8.4 Reviewer instructions and fill guide

Generate Markdown instructions explaining:

- this is a strict human review package for AI-assisted confirmed rows
- AI-assisted confirmation is not enough for formal client export
- what evidence/candidate fields should be checked
- how to fill each decision
- which corrected fields are required for `STRICT_CORRECT`
- where to save the filled workbook for 343J ingestion

### 8.5 Expected import contract for 343J

Generate a JSON import contract describing:

- required sheet name: `04_REVIEW_TEMPLATE`
- required identity columns
- editable strict review columns
- allowed strict review decisions
- correction validation rules
- expected input path pattern: `D:/_datefac/input/review_queue_strict_human_review_343i_filled/*.xlsx`

343I must not ingest strict review results. It must set a waiting-for-strict-human-review state.

## 9. 343J readiness

If QA passes, set:

- `strict_human_review_package_generated = true`
- `waiting_for_strict_human_review = true`
- `strict_human_review_result_ingested = false`
- `strict_human_review_completed = false`
- `ready_for_343j = false`
- `recommended_343j_scope = strict_human_review_result_ingestion_after_user_fills_workbook`

This is intentional: 343J should start only after the user fills the strict human review workbook.

## 10. Summary JSON

`review_queue_strict_human_review_package_343i_summary.json` must include at least:

- `source_milestone = 343H`
- `decision`
- `review_queue_schema_version`
- `input_ai_assisted_confirmed_count`
- `strict_review_item_count`
- `source_check_backlog_context_count`
- `strict_human_gap_item_count`
- `strict_human_review_package_generated`
- `review_template_generated`
- `reviewer_instructions_generated`
- `fill_guide_generated`
- `expected_import_contract_generated`
- `waiting_for_strict_human_review`
- `strict_human_review_result_ingested = false`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343j = false`
- `recommended_343j_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready for user strict review: `STRICT_HUMAN_REVIEW_PACKAGE_343I_WAITING_FOR_STRICT_REVIEW`
- otherwise: `STRICT_HUMAN_REVIEW_PACKAGE_343I_NOT_READY`

## 11. QA requirements

Must check:

- 343H input exists and is ready
- confirmed AI-assisted items JSONL exists and is readable
- client export gate exists and remains false
- strict review item count matches AI-assisted confirmed count
- review template is generated
- reviewer instructions are generated
- fill guide is generated
- expected import contract is generated
- editable strict review columns exist
- allowed decision list is present
- strict review decisions are not prefilled as completed
- `waiting_for_strict_human_review` is true
- `strict_human_review_result_ingested` is false
- strict human review is not claimed as complete
- no formal/client/production readiness flag is true
- no Argilla call is made
- no real production apply is performed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_strict_human_review_package_343i_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343I creates a strict human review package for 10 AI-assisted confirmed rows
- it does not ingest strict review results yet
- it does not mean strict human review is complete
- 19 source-check-required rows remain separate backlog
- formal client export remains forbidden
- next task after user filling is 343J strict human review result ingestion

## 13. Ledger update

Update the project milestone ledger with:

- 343I completed as waiting-for-strict-human-review package generation
- inputs
- outputs
- key metrics
- QA result
- decision
- strict human review package summary
- client export boundary
- next required user action
- next recommended task after user fills workbook

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\strict_human_review_package_343i.py datefac\benchmark\review_queue_strict_human_review_package_343i.py datefac\benchmark\review_queue_strict_human_review_package_343i_report.py tools\run_review_queue_strict_human_review_package_343i.py tests\benchmark\test_review_queue_strict_human_review_package_343i.py
python -m pytest tests\benchmark\test_review_queue_strict_human_review_package_343i.py -q
python tools\run_review_queue_strict_human_review_package_343i.py --audit-summary-343h-dir D:\_datefac\output\review_queue_audit_summary_343h --spot-check-ingestion-343g-dir D:\_datefac\output\review_queue_spot_check_ingestion_343g --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_strict_human_review_package_343i
```

## 15. Completion report

Report in Chinese:

1. 343I decision
2. review_queue_schema_version
3. input_ai_assisted_confirmed_count
4. strict_review_item_count
5. source_check_backlog_context_count
6. strict_human_gap_item_count
7. strict_human_review_package_generated
8. review_template_generated
9. reviewer_instructions_generated
10. fill_guide_generated
11. expected_import_contract_generated
12. waiting_for_strict_human_review
13. strict_human_review_result_ingested
14. strict_human_review_completed
15. requires_strict_human_review
16. formal_client_export_allowed
17. client_ready
18. production_ready
19. ready_for_343j
20. recommended_343j_scope
21. qa_fail_count
22. no-write-back proof status
23. output directory
24. most important Excel/template/fill-guide/import-contract artifacts
25. modified files
26. validation command results
27. git status summary
28. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
