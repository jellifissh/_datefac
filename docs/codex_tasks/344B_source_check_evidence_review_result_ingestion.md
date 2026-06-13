# 344B：Source-check Evidence Review Result Ingestion

## 1. Positioning

344B ingests the filled 344A2 enriched source-check review workbook.

344A2 enriched all 19 source-check backlog rows with source evidence. The user then performed source-check review and filled the workbook. 344B validates those review decisions, imports them into a sidecar result set, and generates an audit gate for the source-check backlog resolution scope.

344B is an ingestion, validation, and sidecar-audit task. It is not production apply, not formal client export, not global client export, not Argilla integration, not frontend work, not real LLM/VLM review, and not an upstream extraction rerun.

Important scope boundary: 344B only ingests review results for the 19-row source-check backlog package from 344A2. It must not modify the already closed 343O 10-row demo arc.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/344A2_source_evidence_enrichment_for_source_check_backlog.md`
- 344A2 summary / QA / enriched backlog items / evidence map / enriched review template / expected import contract / scope boundary
- 344A summary / backlog package / review template / import contract
- 343O summary / demo arc boundary / backlog summary
- 343A schema artifacts
- current git status

Expected current state:

- latest completed milestone = `344A2 Source Evidence Enrichment For Source-check Backlog`
- 344A2 decision = `SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_WAITING_FOR_SOURCE_CHECK_REVIEW`
- review_queue_schema_version = `343A.review_queue.v1`
- input_source_check_backlog_item_count = `19`
- deduplicated_backlog_item_count = `19`
- evidence_resolved_count = `19`
- evidence_partial_count = `0`
- evidence_unresolved_count = `0`
- source_pdf_name_available_count = `19`
- page_number_available_count = `19`
- image_path_available_count = `19`
- source_text_snippet_available_count = `19`
- source_check_evidence_enrichment_completed = `true`
- enriched_review_template_generated = `true`
- waiting_for_source_check_review = `true`
- source_check_result_ingested = `false`
- source_check_backlog_resolved = `false`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- qa_fail_count = `0`

Expected filled workbook path:

`D:/_datefac/input/review_queue_source_check_evidence_344a2_filled/review_queue_source_check_evidence_enrichment_344a2_enriched_review_template_filled_independent.xlsx`

The filled workbook should contain the user's source-check review results. Current expected review decision distribution:

- `SOURCE_CONFIRM = 10`
- `SOURCE_CORRECT = 9`
- `SOURCE_REJECT = 0`
- `SOURCE_STILL_INSUFFICIENT = 0`
- `SOURCE_DEFER = 0`

Current expected correction semantics:

- the first 10 rows confirm ROE values and `%` units
- the last 9 rows correct metric from `revenue` to `YOY` and unit from `亿元` to `%`, preserving the source-checked year/value

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun MinerU, PPStructure, VLM, OCR, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, delivery, approval, or formal export code. Do not write back to upstream workbooks. Do not perform real production apply. Do not generate formal client export.

344B may read the filled workbook and generate validated source-check ingestion artifacts under its own output directory.

Formal/global export boundary must remain conservative:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Source-check boundary:

- `source_check_result_ingested = true` only if validation passes
- `source_check_backlog_resolved = true` only if all 19 rows are `SOURCE_CONFIRM` or `SOURCE_CORRECT` and all required fields/evidence flags pass
- this remains a sidecar import and must not production-write any result

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/344B_source_check_evidence_review_result_ingestion.md`
- `datefac/review_queue/source_check_evidence_review_ingestion_344b.py`
- `datefac/benchmark/review_queue_source_check_evidence_review_ingestion_344b.py`
- `datefac/benchmark/review_queue_source_check_evidence_review_ingestion_344b_report.py`
- `tools/run_review_queue_source_check_evidence_review_ingestion_344b.py`
- `tests/benchmark/test_review_queue_source_check_evidence_review_ingestion_344b.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Primary input directory:

- `D:/_datefac/input/review_queue_source_check_evidence_344a2_filled`

Primary filled workbook:

- `review_queue_source_check_evidence_enrichment_344a2_enriched_review_template_filled_independent.xlsx`

Reference directories:

- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2`
- `D:/_datefac/output/review_queue_source_check_backlog_package_344a`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o`
- `D:/_datefac/output/review_queue_schema_343a`

Required 344A2 files:

- `review_queue_source_check_evidence_enrichment_344a2_summary.json`
- `review_queue_source_check_evidence_enrichment_344a2_qa.json`
- `review_queue_source_check_evidence_enrichment_344a2_enriched_backlog_items.jsonl`
- `review_queue_source_check_evidence_enrichment_344a2_evidence_map.json`
- `review_queue_source_check_evidence_enrichment_344a2_expected_import_contract.json`
- `review_queue_source_check_evidence_enrichment_344a2_no_write_back_proof.json`

If the filled workbook is missing, fail gracefully and report the exact expected path. Do not fabricate source-check decisions.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b`

Output files:

- `review_queue_source_check_evidence_review_ingestion_344b.xlsx`
- `review_queue_source_check_evidence_review_ingestion_344b_summary.json`
- `review_queue_source_check_evidence_review_ingestion_344b_manifest.json`
- `review_queue_source_check_evidence_review_ingestion_344b_qa.json`
- `review_queue_source_check_evidence_review_ingestion_344b_report.md`
- `review_queue_source_check_evidence_review_ingestion_344b_result.jsonl`
- `review_queue_source_check_evidence_review_ingestion_344b_validated_sidecar.jsonl`
- `review_queue_source_check_evidence_review_ingestion_344b_corrections.jsonl`
- `review_queue_source_check_evidence_review_ingestion_344b_validation_errors.jsonl`
- `review_queue_source_check_evidence_review_ingestion_344b_decision_summary.json`
- `review_queue_source_check_evidence_review_ingestion_344b_audit_gate.json`
- `review_queue_source_check_evidence_review_ingestion_344b_scope_boundary.md`
- `review_queue_source_check_evidence_review_ingestion_344b_no_write_back_proof.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_INGEST_SUMMARY`
- `02_INPUT_344A2_SUMMARY`
- `03_REVIEW_RESULTS`
- `04_VALIDATED_SIDECAR`
- `05_CORRECTIONS`
- `06_VALIDATION_ERRORS`
- `07_AUDIT_GATE`
- `08_SCOPE_BOUNDARY`
- `09_NO_WRITE_BACK`
- `10_NEXT_STEPS`

## 8. Core logic

### 8.1 Read and validate 344A2 state

Read 344A2 summary / QA / import contract / enriched backlog items / evidence map.

Validate:

- 344A2 is ready / waiting for source-check review
- 19 backlog rows are preserved
- evidence is resolved for all 19 rows or explicitly disclosed
- source-check result is not already ingested in 344A2
- source-check backlog is not resolved in 344A2
- formal/client/production readiness flags remain false

### 8.2 Read filled workbook

Read sheet `04_REVIEW_TEMPLATE` from the filled workbook.

Validate identity columns against 344A2 enriched backlog rows:

- `backlog_item_key`
- `queue_item_id`
- `review_item_id`
- `source_row_id` if available

Do not accept rows whose identity does not match 344A2.

### 8.3 Validate decisions

Allowed decisions:

- `SOURCE_CONFIRM`
- `SOURCE_CORRECT`
- `SOURCE_REJECT`
- `SOURCE_STILL_INSUFFICIENT`
- `SOURCE_DEFER`

Validation rules:

- `SOURCE_CONFIRM` requires source checker id/date, `source_evidence_checked = true`, `source_evidence_sufficient = true`, and source-check metric/year/value/unit present.
- `SOURCE_CORRECT` requires source checker id/date, note, corrected metric/year/value/unit, `source_evidence_checked = true`, and `source_evidence_sufficient = true`.
- `SOURCE_REJECT` requires source checker id/date, note, and `source_evidence_checked = true`.
- `SOURCE_STILL_INSUFFICIENT` requires source checker id/date and note.
- `SOURCE_DEFER` requires checker id/date and note where possible.

For current expected workbook:

- confirm count should be 10
- correct count should be 9
- invalid count should be 0
- all 9 corrections should have `source_check_metric_standardized = YOY` and `source_check_normalized_unit = %`

### 8.4 Build validated sidecar

For `SOURCE_CONFIRM`, carry forward source-checked metric/year/value/unit and mark:

- `sidecar_action = SOURCE_CHECK_CONFIRMED`
- `source_check_status = CONFIRMED`

For `SOURCE_CORRECT`, carry forward corrected source-check metric/year/value/unit and mark:

- `sidecar_action = SOURCE_CHECK_CORRECTED`
- `source_check_status = CORRECTED`

For reject/insufficient/defer rows, keep them in result JSONL but do not add to confirmed sidecar.

Expected current happy path:

- `validated_sidecar_row_count = 19`
- `source_confirm_count = 10`
- `source_correct_count = 9`
- `source_reject_count = 0`
- `source_still_insufficient_count = 0`
- `source_defer_count = 0`
- `validation_error_count = 0`

### 8.5 Audit gate

Generate audit gate JSON:

- `source_check_result_ingested = true`
- `source_check_backlog_resolved = true` only if all 19 rows are confirmed/corrected and validation errors = 0
- `source_check_resolved_row_count = 19` if happy path
- `source_check_confirm_count = 10`
- `source_check_correct_count = 9`
- `source_check_reject_count = 0`
- `source_check_still_insufficient_count = 0`
- `source_check_defer_count = 0`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Reason: source-check backlog may be resolved as a sidecar review result, but formal client export and production readiness still require downstream merge/simulation/export gates and global audit checks.

### 8.6 Scope boundary report

Generate Markdown explaining:

- 344B imports filled source-check results for the 19-row backlog
- 10 rows are confirmed, 9 rows are corrected from revenue/亿元 to YOY/%
- no production data was written back
- formal client export remains forbidden
- the next safe task is a source-check confirmed sidecar apply simulation and expanded trusted coverage audit gate

## 9. 344C readiness

If QA passes, set:

- `source_check_result_ingested = true`
- `source_check_backlog_resolved = true` if all rows are confirmed/corrected
- `validated_sidecar_generated = true`
- `correction_sidecar_generated = true`
- `audit_gate_generated = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_344c = true`
- `recommended_344c_scope = source_check_confirmed_sidecar_apply_simulation_and_expanded_trust_gate`

If QA fails, set:

- `source_check_result_ingested = false`
- `source_check_backlog_resolved = false`
- `ready_for_344c = false`

## 10. Summary JSON

`review_queue_source_check_evidence_review_ingestion_344b_summary.json` must include at least:

- `source_milestone = 344A2`
- `decision`
- `review_queue_schema_version`
- `filled_row_count`
- `valid_row_count`
- `invalid_row_count`
- `source_confirm_count`
- `source_correct_count`
- `source_reject_count`
- `source_still_insufficient_count`
- `source_defer_count`
- `validated_sidecar_row_count`
- `correction_row_count`
- `source_check_result_ingested`
- `source_check_backlog_resolved`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `ready_for_344c`
- `recommended_344c_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready: `SOURCE_CHECK_EVIDENCE_REVIEW_INGESTION_344B_READY`
- if validation errors exist: `SOURCE_CHECK_EVIDENCE_REVIEW_INGESTION_344B_VALIDATION_FAILED`
- otherwise: `SOURCE_CHECK_EVIDENCE_REVIEW_INGESTION_344B_NOT_READY`

## 11. QA requirements

Must check:

- 344A2 input exists and is ready
- filled workbook exists
- sheet `04_REVIEW_TEMPLATE` exists
- exactly 19 filled rows are read
- identity columns match 344A2 enriched backlog rows
- all source-check decisions are in allowed list
- required fields pass decision-specific validation
- current expected distribution is accepted if validation passes: 10 confirm, 9 correct, 0 reject/insufficient/defer
- all 9 correction rows have corrected metric/year/value/unit
- corrections are captured in correction JSONL
- validated sidecar is generated
- audit gate is generated
- no production write-back is performed
- formal/client/production readiness flags remain false
- no formal client export workbook is generated
- no Argilla call is made
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_source_check_evidence_review_ingestion_344b_report.md` in Chinese-first, English-friendly style.

It must explain:

- 344B ingested the filled source-check evidence review workbook
- 10 rows were confirmed and 9 rows were corrected
- the 9 corrected rows are YOY percentage rows, not revenue amount rows
- source-check backlog is resolved only as a sidecar review result
- no production write-back or formal client export occurred
- next task is 344C sidecar apply simulation and expanded trust gate

## 13. Ledger update

Update the project milestone ledger with:

- 344B ready/failed/not-ready status
- inputs
- outputs
- key metrics
- validation result
- decision
- source-check result distribution
- correction summary
- audit gate summary
- export/global boundary
- next recommended task

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\source_check_evidence_review_ingestion_344b.py datefac\benchmark\review_queue_source_check_evidence_review_ingestion_344b.py datefac\benchmark\review_queue_source_check_evidence_review_ingestion_344b_report.py tools\run_review_queue_source_check_evidence_review_ingestion_344b.py tests\benchmark\test_review_queue_source_check_evidence_review_ingestion_344b.py
python -m pytest tests\benchmark\test_review_queue_source_check_evidence_review_ingestion_344b.py -q
python tools\run_review_queue_source_check_evidence_review_ingestion_344b.py --source-check-evidence-enrichment-344a2-dir D:\_datefac\output\review_queue_source_check_evidence_enrichment_344a2 --source-check-backlog-package-344a-dir D:\_datefac\output\review_queue_source_check_backlog_package_344a --demo-audit-snapshot-343o-dir D:\_datefac\output\review_queue_demo_audit_snapshot_343o --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --filled-workbook D:\_datefac\input\review_queue_source_check_evidence_344a2_filled\review_queue_source_check_evidence_enrichment_344a2_enriched_review_template_filled_independent.xlsx --output-dir D:\_datefac\output\review_queue_source_check_evidence_review_ingestion_344b
```

## 15. Completion report

Report in Chinese:

1. 344B decision
2. review_queue_schema_version
3. filled_row_count
4. valid_row_count
5. invalid_row_count
6. source_confirm_count
7. source_correct_count
8. source_reject_count
9. source_still_insufficient_count
10. source_defer_count
11. validated_sidecar_row_count
12. correction_row_count
13. source_check_result_ingested
14. source_check_backlog_resolved
15. formal_client_export_allowed
16. client_ready
17. production_ready
18. global_strict_human_review_completed
19. ready_for_344c
20. recommended_344c_scope
21. qa_fail_count
22. no-write-back proof status
23. output directory
24. most important result / sidecar / corrections / audit gate / scope boundary artifacts
25. modified files
26. validation command results
27. git status summary
28. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
