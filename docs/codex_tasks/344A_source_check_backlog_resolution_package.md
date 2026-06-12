# 344A：Source-check Backlog Resolution Package

## 1. Positioning

344A starts the next phase after the 343-series trusted demo arc.

343O closed the 10-row demo-only trusted package, but 19 source-check backlog rows still remain. 344A creates a focused source-check resolution package for those remaining backlog rows, so reviewers can trace source evidence, decide whether each row can be confirmed/corrected/rejected/deferred, and expand trusted coverage beyond the 10-row demo package.

344A is a backlog-resolution package generation task. It is not production apply, not formal client export, not global client export, not Argilla integration, not a frontend implementation, not real LLM/VLM review, and not an upstream extraction rerun.

Important scope boundary: 343O closed only the 10-row `343K_PACKAGE_ONLY` trusted demo arc. 344A works on the 19-row source-check backlog and must not retroactively change the 343O demo package.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/343O_demo_package_audit_snapshot_and_handoff_summary.md`
- 343O summary / QA / handoff summary / executive summary / trust chain / artifact index / export gate snapshot / backlog summary
- 343N summary / remaining backlog / demo export gate / scope boundary
- 343M summary / limited export gate / remaining backlog
- 343H audit summary / source-check backlog / strict-human-gap report / gap items
- 343G spot-check ingestion result JSONL
- 343F source-check todo JSONL if available
- 343I2 source evidence enrichment logic and evidence-resolution conventions
- 343A schema artifacts
- current git status

Expected current state:

- latest completed milestone = `343O Demo Package Audit Snapshot And Handoff Summary`
- 343O decision = `DEMO_PACKAGE_AUDIT_SNAPSHOT_343O_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- input_demo_export_row_count = `10`
- audit_label_row_count = `10`
- limited_export_scope = `343K_PACKAGE_ONLY`
- export_usage = `DEMO_ONLY`
- remaining_source_check_backlog_count = `19`
- package_strict_human_review_completed = `true`
- global_strict_human_review_completed = `false`
- demo_arc_closed = `true`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- ready_for_344a = `true`
- recommended_344a_scope = `source_check_backlog_resolution_package`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, delivery, approval, or formal export code. Do not write back to upstream workbooks. Do not perform real production apply. Do not generate formal client export.

344A may generate a source-check backlog resolution package and a fillable source-check review template.

Formal/global export boundary must remain conservative:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Scope boundary:

- 343O demo arc remains closed and unchanged
- 344A handles backlog rows outside the 10-row demo package
- source-check backlog package is waiting for reviewer action
- no backlog row is considered resolved until the filled workbook is ingested in a later task

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/344A_source_check_backlog_resolution_package.md`
- `datefac/review_queue/source_check_backlog_package_344a.py`
- `datefac/benchmark/review_queue_source_check_backlog_package_344a.py`
- `datefac/benchmark/review_queue_source_check_backlog_package_344a_report.py`
- `tools/run_review_queue_source_check_backlog_package_344a.py`
- `tests/benchmark/test_review_queue_source_check_backlog_package_344a.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o`
- `D:/_datefac/output/review_queue_limited_demo_export_package_343n`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g`
- `D:/_datefac/output/review_queue_spot_check_package_343f`
- `D:/_datefac/output/review_queue_schema_343a`

Required 343O files:

- `review_queue_demo_audit_snapshot_343o_summary.json`
- `review_queue_demo_audit_snapshot_343o_qa.json`
- `review_queue_demo_audit_snapshot_343o_backlog_summary.json`
- `review_queue_demo_audit_snapshot_343o_export_gate_snapshot.json`
- `review_queue_demo_audit_snapshot_343o_next_action_plan.json`
- `review_queue_demo_audit_snapshot_343o_no_write_back_proof.json`

Required backlog/reference files, use whichever exist and cross-check counts:

- `review_queue_audit_summary_343h_source_check_backlog.jsonl`
- `review_queue_human_confirmed_sidecar_simulation_343m_remaining_backlog.jsonl`
- `review_queue_limited_demo_export_package_343n_remaining_backlog.jsonl`
- `review_queue_spot_check_ingestion_343g_result.jsonl`
- `review_queue_spot_check_package_343f_source_check_todo.jsonl`
- `review_queue_audit_summary_343h_gap_items.jsonl`
- `review_queue_schema_343a_schema.json`

If no usable backlog source exists, fail gracefully. Do not fabricate backlog rows.

Expected backlog count based on 343O:

- `19` source-check backlog rows

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_source_check_backlog_package_344a`

Output files:

- `review_queue_source_check_backlog_package_344a.xlsx`
- `review_queue_source_check_backlog_package_344a_summary.json`
- `review_queue_source_check_backlog_package_344a_manifest.json`
- `review_queue_source_check_backlog_package_344a_qa.json`
- `review_queue_source_check_backlog_package_344a_report.md`
- `review_queue_source_check_backlog_package_344a_review_template.xlsx`
- `review_queue_source_check_backlog_package_344a_backlog_items.jsonl`
- `review_queue_source_check_backlog_package_344a_evidence_map.json`
- `review_queue_source_check_backlog_package_344a_reviewer_instructions.md`
- `review_queue_source_check_backlog_package_344a_fill_guide.md`
- `review_queue_source_check_backlog_package_344a_expected_import_contract.json`
- `review_queue_source_check_backlog_package_344a_scope_boundary.md`
- `review_queue_source_check_backlog_package_344a_no_write_back_proof.json`

Optional but recommended if lightweight:

- `review_queue_source_check_backlog_package_344a_priority_plan.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_PACKAGE_SUMMARY`
- `02_INPUT_343O_SUMMARY`
- `03_BACKLOG_ITEMS`
- `04_REVIEW_TEMPLATE`
- `05_EVIDENCE_MAP`
- `06_DECISION_RULES`
- `07_IMPORT_CONTRACT`
- `08_SCOPE_BOUNDARY`
- `09_NO_WRITE_BACK`
- `10_NEXT_STEPS`

## 8. Core logic

### 8.1 Read and validate 343O state

Read 343O summary / QA / export gate snapshot / backlog summary.

Validate:

- 343O is ready
- demo arc is closed
- remaining source-check backlog count is 19
- formal/client/production readiness flags remain false
- global strict human review remains false
- ready_for_344a is true

### 8.2 Build backlog item set

Read backlog rows from the strongest available source in this order:

1. `review_queue_human_confirmed_sidecar_simulation_343m_remaining_backlog.jsonl`
2. `review_queue_limited_demo_export_package_343n_remaining_backlog.jsonl`
3. `review_queue_audit_summary_343h_source_check_backlog.jsonl`
4. `review_queue_spot_check_package_343f_source_check_todo.jsonl`
5. fallback from 343G result rows with `SOURCE_CHECK_REQUIRED`

Deduplicate by stable identifiers:

- `queue_item_id`
- `review_item_id`
- if both missing, use a conservative composite key from metric/year/value/source fields

Expected count after deduplication:

- `source_check_backlog_item_count = 19`

If counts disagree, produce warnings and do not hide the discrepancy.

### 8.3 Enrich backlog evidence conservatively

For each backlog item, preserve any available evidence fields:

- `source_pdf_name`
- `source_pdf_path`
- `source_pdf_id`
- `page_number`
- `table_id`
- `cell_id`
- `bbox`
- `image_path`
- `source_text_snippet`
- `source_html_snippet`
- `metric_candidate_raw`
- `metric_standardized`
- `year_standardized`
- `value_numeric`
- `normalized_unit`
- `evidence_source_stage`
- `evidence_source_artifact`
- `evidence_resolution_status`
- `evidence_gap_reason`

Do not invent missing fields. If evidence is insufficient, mark it explicitly:

- `evidence_resolution_status = UNRESOLVED`
- `evidence_gap_reason = source evidence not available in selected backlog artifact`

If partial locator/snippet exists, mark `PARTIAL`. If enough locator evidence exists to find the source, mark `RESOLVED`.

### 8.4 Generate fillable source-check review template

Generate a fillable workbook for the 19 backlog rows.

Non-editable identity/evidence fields should include:

- `queue_item_id`
- `review_item_id`
- `source_status`
- `priority_tier`
- candidate metric/year/value/unit fields
- source evidence locator fields
- backlog reason fields

Editable source-check columns:

- `source_check_decision`
- `source_check_metric_standardized`
- `source_check_year_standardized`
- `source_check_value_numeric`
- `source_check_normalized_unit`
- `source_check_note`
- `source_checker_id`
- `source_checked_at`
- `source_evidence_checked`
- `source_evidence_sufficient`

Allowed source-check decisions:

- `SOURCE_CONFIRM`
- `SOURCE_CORRECT`
- `SOURCE_REJECT`
- `SOURCE_STILL_INSUFFICIENT`
- `SOURCE_DEFER`

Decision rules:

- `SOURCE_CONFIRM` requires source checker id, checked date, source evidence checked = true, source evidence sufficient = true.
- `SOURCE_CORRECT` requires corrected metric/year/value/unit, note, checker id/date, source evidence checked = true, source evidence sufficient = true.
- `SOURCE_REJECT` requires note, checker id/date, source evidence checked = true.
- `SOURCE_STILL_INSUFFICIENT` requires note, checker id/date.
- `SOURCE_DEFER` requires checker id/date and note when possible.
- No source-check decision should be prefilled as completed.

### 8.5 Reviewer instructions and fill guide

Generate Markdown instructions explaining:

- this package is for resolving the remaining 19 source-check backlog rows
- the 343O 10-row demo arc is already closed and is not being modified
- how to inspect source evidence locator fields
- how to fill each source-check decision
- which corrected fields are mandatory for `SOURCE_CORRECT`
- why formal client export remains blocked
- where to save the filled workbook for 344B ingestion

### 8.6 Expected import contract for 344B

Generate a JSON import contract describing:

- required sheet name: `04_REVIEW_TEMPLATE`
- required identity columns
- source evidence columns
- editable source-check columns
- allowed source-check decisions
- validation rules
- expected input path pattern: `D:/_datefac/input/review_queue_source_check_backlog_344a_filled/*.xlsx`

344A must not ingest source-check results. It must set a waiting-for-source-check-review state.

## 9. 344B readiness

If QA passes, set:

- `source_check_backlog_package_generated = true`
- `review_template_generated = true`
- `reviewer_instructions_generated = true`
- `fill_guide_generated = true`
- `expected_import_contract_generated = true`
- `waiting_for_source_check_review = true`
- `source_check_result_ingested = false`
- `source_check_backlog_resolved = false`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_344b = false`
- `recommended_344b_scope = source_check_backlog_result_ingestion_after_user_fills_workbook`

This is intentional: 344B should start only after the user fills the source-check backlog workbook.

## 10. Summary JSON

`review_queue_source_check_backlog_package_344a_summary.json` must include at least:

- `source_milestone = 343O`
- `decision`
- `review_queue_schema_version`
- `input_remaining_source_check_backlog_count`
- `source_check_backlog_item_count`
- `deduplicated_backlog_item_count`
- `evidence_resolved_count`
- `evidence_partial_count`
- `evidence_unresolved_count`
- `source_pdf_name_available_count`
- `source_text_snippet_available_count`
- `source_check_backlog_package_generated`
- `review_template_generated`
- `reviewer_instructions_generated`
- `fill_guide_generated`
- `expected_import_contract_generated`
- `waiting_for_source_check_review`
- `source_check_result_ingested = false`
- `source_check_backlog_resolved = false`
- `demo_arc_closed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_344b = false`
- `recommended_344b_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready for user source-check review: `SOURCE_CHECK_BACKLOG_PACKAGE_344A_WAITING_FOR_SOURCE_CHECK_REVIEW`
- otherwise: `SOURCE_CHECK_BACKLOG_PACKAGE_344A_NOT_READY`

## 11. QA requirements

Must check:

- 343O input exists and is ready
- backlog source exists and is readable
- deduplicated backlog count is 19 unless upstream explicitly differs
- every backlog item has identity or fallback key
- every backlog item has evidence resolution status
- unresolved evidence is explicitly disclosed
- review template is generated
- reviewer instructions are generated
- fill guide is generated
- expected import contract is generated
- editable source-check columns exist
- allowed source-check decision list exists
- source-check decisions are not prefilled as completed
- waiting_for_source_check_review is true
- source_check_result_ingested is false
- source_check_backlog_resolved is false
- formal/client/production readiness flags remain false
- 343O demo arc is not modified
- no formal client export workbook is generated
- no Argilla call is made
- no real production apply is performed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_source_check_backlog_package_344a_report.md` in Chinese-first, English-friendly style.

It must explain:

- 344A starts backlog expansion after the 10-row trusted demo arc was closed by 343O
- it packages the 19 remaining source-check backlog rows for review
- it does not ingest review results yet
- evidence availability / unresolved evidence is disclosed
- formal client export remains forbidden
- next task after user filling is 344B source-check backlog result ingestion

## 13. Ledger update

Update the project milestone ledger with:

- 344A waiting-for-source-check-review package generation status
- inputs
- outputs
- key metrics
- validation result
- decision
- backlog package summary
- evidence resolution summary
- export/global boundary
- next required user action
- next recommended task after user fills workbook

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\source_check_backlog_package_344a.py datefac\benchmark\review_queue_source_check_backlog_package_344a.py datefac\benchmark\review_queue_source_check_backlog_package_344a_report.py tools\run_review_queue_source_check_backlog_package_344a.py tests\benchmark\test_review_queue_source_check_backlog_package_344a.py
python -m pytest tests\benchmark\test_review_queue_source_check_backlog_package_344a.py -q
python tools\run_review_queue_source_check_backlog_package_344a.py --demo-audit-snapshot-343o-dir D:\_datefac\output\review_queue_demo_audit_snapshot_343o --limited-demo-export-package-343n-dir D:\_datefac\output\review_queue_limited_demo_export_package_343n --human-confirmed-sidecar-simulation-343m-dir D:\_datefac\output\review_queue_human_confirmed_sidecar_simulation_343m --audit-summary-343h-dir D:\_datefac\output\review_queue_audit_summary_343h --spot-check-ingestion-343g-dir D:\_datefac\output\review_queue_spot_check_ingestion_343g --spot-check-package-343f-dir D:\_datefac\output\review_queue_spot_check_package_343f --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_source_check_backlog_package_344a
```

## 15. Completion report

Report in Chinese:

1. 344A decision
2. review_queue_schema_version
3. input_remaining_source_check_backlog_count
4. source_check_backlog_item_count
5. deduplicated_backlog_item_count
6. evidence_resolved_count
7. evidence_partial_count
8. evidence_unresolved_count
9. source_pdf_name_available_count
10. source_text_snippet_available_count
11. source_check_backlog_package_generated
12. review_template_generated
13. reviewer_instructions_generated
14. fill_guide_generated
15. expected_import_contract_generated
16. waiting_for_source_check_review
17. source_check_result_ingested
18. source_check_backlog_resolved
19. demo_arc_closed
20. formal_client_export_allowed
21. client_ready
22. production_ready
23. ready_for_344b
24. recommended_344b_scope
25. qa_fail_count
26. no-write-back proof status
27. output directory
28. most important Excel/template/fill-guide/import-contract/evidence-map artifacts
29. modified files
30. validation command results
31. git status summary
32. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
