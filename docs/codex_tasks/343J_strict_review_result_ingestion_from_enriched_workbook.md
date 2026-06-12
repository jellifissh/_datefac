# 343J：Strict Review Result Ingestion From Enriched Workbook

## 1. Positioning

343J ingests the filled enriched strict review workbook produced after 343I2 source evidence enrichment.

Important boundary: the current filled workbook may be AI-assisted if the user used an AI assistant to fill decisions. Therefore this task must not blindly claim pure strict human review. It must preserve reviewer-source disclosure and gate formal client export accordingly.

343J is a review-result ingestion and audit-gating task. It is not production apply, not formal client export, not Argilla integration, not a frontend implementation, not real LLM/VLM review, and not an upstream extraction rerun.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/343I2_source_evidence_enrichment_for_strict_human_review_package.md`
- 343I2 summary / QA / enriched review template / enriched items JSONL / evidence gap report / import contract
- 343I summary / review items JSONL / import contract
- 343H audit summary / client export gate
- 343G result JSONL
- 343A schema artifacts
- current git status

Expected current state:

- latest completed milestone = `343I2 Source Evidence Enrichment For Strict Human Review Package`
- 343I2 decision = `SOURCE_EVIDENCE_ENRICHMENT_343I2_WAITING_FOR_STRICT_REVIEW`
- input_strict_review_item_count = `10`
- enriched_review_item_count = `10`
- evidence_resolved_count = `10`
- evidence_partial_count = `0`
- evidence_unresolved_count = `0`
- enriched_review_template_generated = `true`
- source_evidence_enrichment_completed = `true`
- waiting_for_strict_human_review = `true`
- strict_human_review_result_ingested = `false`
- strict_human_review_completed = `false`
- requires_strict_human_review = `true`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- ready_for_343j = `false`
- recommended_343j_scope = `strict_human_review_result_ingestion_after_user_fills_enriched_workbook`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, or delivery code. Do not write back to upstream workbooks. Do not generate formal client export. Do not perform real production apply.

Do not claim pure strict human review if the filled workbook is AI-assisted.

Default current disclosure for the provided filled workbook:

- `strict_review_input_source_type = AI_ASSISTED_EVIDENCE_CHECK`
- `not_pure_human_review = true`
- `pure_strict_human_review_completed = false`
- `strict_human_review_completed = false`
- `requires_pure_human_confirmation = true`

Preserve these flags unless the user provides a documented pure-human-filled workbook and reviewer attestation in a later task:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343J_strict_review_result_ingestion_from_enriched_workbook.md`
- `datefac/review_queue/ingest_strict_review_343j.py`
- `datefac/benchmark/review_queue_strict_review_ingestion_343j.py`
- `datefac/benchmark/review_queue_strict_review_ingestion_343j_report.py`
- `tools/run_review_queue_strict_review_ingestion_343j.py`
- `tests/benchmark/test_review_queue_strict_review_ingestion_343j.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2`
- `D:/_datefac/output/review_queue_strict_human_review_package_343i`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g`
- `D:/_datefac/output/review_queue_schema_343a`

Filled workbook input path pattern:

- `D:/_datefac/input/review_queue_strict_human_review_343i2_filled/*.xlsx`

Expected filled workbook name for the current run:

- `D:/_datefac/input/review_queue_strict_human_review_343i2_filled/review_queue_source_evidence_enrichment_343i2_enriched_review_template_filled.xlsx`

Required 343I2 files:

- `review_queue_source_evidence_enrichment_343i2_summary.json`
- `review_queue_source_evidence_enrichment_343i2_qa.json`
- `review_queue_source_evidence_enrichment_343i2_enriched_items.jsonl`
- `review_queue_source_evidence_enrichment_343i2_expected_import_contract.json`
- `review_queue_source_evidence_enrichment_343i2_no_write_back_proof.json`

Required workbook sheet:

- `04_REVIEW_TEMPLATE`

Required identity columns:

- `queue_item_id`
- `review_item_id`
- `resulting_status`
- `simulated_downstream_action`
- `priority_tier`

Editable strict review columns to ingest:

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

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_strict_review_ingestion_343j`

Output files:

- `review_queue_strict_review_ingestion_343j.xlsx`
- `review_queue_strict_review_ingestion_343j_summary.json`
- `review_queue_strict_review_ingestion_343j_manifest.json`
- `review_queue_strict_review_ingestion_343j_qa.json`
- `review_queue_strict_review_ingestion_343j_report.md`
- `review_queue_strict_review_ingestion_343j_result.jsonl`
- `review_queue_strict_review_ingestion_343j_validation_errors.json`
- `review_queue_strict_review_ingestion_343j_decision_summary.json`
- `review_queue_strict_review_ingestion_343j_client_export_gate.json`
- `review_queue_strict_review_ingestion_343j_reviewer_source_disclosure.md`
- `review_queue_strict_review_ingestion_343j_no_write_back_proof.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_INGEST_SUMMARY`
- `02_INPUT_343I2_SUMMARY`
- `03_REVIEW_RESULTS`
- `04_VALIDATION_ERRORS`
- `05_DECISION_SUMMARY`
- `06_EXPORT_GATE`
- `07_SOURCE_DISCLOSURE`
- `08_NO_WRITE_BACK`
- `09_NEXT_STEPS`

## 8. Core logic

### 8.1 Read filled enriched workbook

Read exactly one filled workbook from the input directory unless a `--filled-workbook` argument is supplied.

Validate:

- required sheet exists
- identity columns exist
- editable strict review columns exist
- no identity mismatch versus 343I2 enriched items
- row count matches expected 10 unless explicitly allowed by input contract
- every filled row has an allowed decision

### 8.2 Validate strict review decisions

Rules:

- `STRICT_CONFIRM` requires reviewer id and reviewed date.
- `STRICT_CORRECT` requires reviewer id, reviewed date, corrected metric/year/value/unit, and note.
- `STRICT_REJECT` requires reviewer id, reviewed date, and note.
- `STRICT_NEEDS_SOURCE_CHECK` requires reviewer id, reviewed date, and note.
- `STRICT_DEFER` requires reviewer id and reviewed date; note is strongly recommended.

Keep validation conservative. Invalid rows should make the milestone NOT_READY and produce validation errors.

### 8.3 Preserve reviewer-source disclosure

Because the current workbook was filled through an AI-assisted evidence check, set:

- `strict_review_input_source_type = AI_ASSISTED_EVIDENCE_CHECK`
- `not_pure_human_review = true`
- `pure_strict_human_review_completed = false`
- `strict_human_review_completed = false`
- `requires_pure_human_confirmation = true`

Even if all rows are `STRICT_CONFIRM`, do not set pure strict human review completed to true unless a later task explicitly ingests a pure human reviewer attestation.

### 8.4 Count decisions

Count:

- `strict_confirm_count`
- `strict_correct_count`
- `strict_reject_count`
- `strict_needs_source_check_count`
- `strict_defer_count`
- `valid_row_count`
- `invalid_row_count`

For current filled workbook, expected values are likely:

- strict_confirm_count = `10`
- strict_correct_count = `0`
- strict_reject_count = `0`
- strict_needs_source_check_count = `0`
- strict_defer_count = `0`
- valid_row_count = `10`
- invalid_row_count = `0`

### 8.5 Client export gate

Generate client export gate:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `requires_pure_human_confirmation = true`
- `reason = Current strict-review-style decisions were filled via AI-assisted evidence check; pure human reviewer confirmation is still required.`

### 8.6 Next action plan

If QA passes and all 10 rows are validly ingested, recommend:

- `343K Pure Human Confirmation Attestation Package`

This package should allow a human reviewer to attest that they independently checked the 10 confirmed rows and accepts or overrides the AI-assisted filled decisions.

If there are validation errors, recommend re-filling the workbook and rerunning 343J.

## 9. 343K readiness

If QA passes, set:

- `strict_review_result_ingested = true`
- `ai_assisted_strict_review_confirm_count = strict_confirm_count`
- `pure_strict_human_confirm_count = 0`
- `pure_strict_human_review_completed = false`
- `requires_pure_human_confirmation = true`
- `ready_for_343k = true`
- `recommended_343k_scope = pure_human_confirmation_attestation_package_for_ai_assisted_strict_confirmed_rows`

Also preserve:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`

If QA fails, set:

- `strict_review_result_ingested = false`
- `ready_for_343k = false`

## 10. Summary JSON

`review_queue_strict_review_ingestion_343j_summary.json` must include at least:

- `source_milestone = 343I2`
- `decision`
- `review_queue_schema_version`
- `filled_workbook_path`
- `filled_row_count`
- `valid_row_count`
- `invalid_row_count`
- `strict_confirm_count`
- `strict_correct_count`
- `strict_reject_count`
- `strict_needs_source_check_count`
- `strict_defer_count`
- `strict_review_input_source_type = AI_ASSISTED_EVIDENCE_CHECK`
- `not_pure_human_review = true`
- `pure_strict_human_confirm_count = 0`
- `ai_assisted_strict_review_confirm_count`
- `strict_review_result_ingested`
- `pure_strict_human_review_completed = false`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `requires_pure_human_confirmation = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343k`
- `recommended_343k_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready: `AI_ASSISTED_STRICT_REVIEW_INGESTION_343J_READY`
- otherwise: `AI_ASSISTED_STRICT_REVIEW_INGESTION_343J_NOT_READY`

## 11. QA requirements

Must check:

- filled workbook exists
- required sheet exists
- required identity columns exist
- editable strict review columns exist
- identity is preserved versus 343I2 enriched items
- decision values are allowed
- required reviewer id/date are present
- required correction payload is present for `STRICT_CORRECT`
- note is present for `STRICT_REJECT` and `STRICT_NEEDS_SOURCE_CHECK`
- no row claims pure strict human review by itself
- reviewer-source disclosure is generated
- client export gate remains false
- strict human review is not claimed as complete
- no formal/client/production readiness flag is true
- no Argilla call is made
- no real production apply is performed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_strict_review_ingestion_343j_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343J ingested the enriched strict review workbook
- the current filled workbook is AI-assisted evidence-check filled, not pure human review
- 10 rows may be AI-assisted strict-review confirmed if valid
- pure strict human confirmation is still required
- formal client export remains forbidden
- next task is 343K pure human confirmation attestation package

## 13. Ledger update

Update the project milestone ledger with:

- 343J ready or not-ready status
- inputs
- outputs
- key metrics
- validation result
- decision
- reviewer-source disclosure
- client export boundary
- next required user action
- next recommended task

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\ingest_strict_review_343j.py datefac\benchmark\review_queue_strict_review_ingestion_343j.py datefac\benchmark\review_queue_strict_review_ingestion_343j_report.py tools\run_review_queue_strict_review_ingestion_343j.py tests\benchmark\test_review_queue_strict_review_ingestion_343j.py
python -m pytest tests\benchmark\test_review_queue_strict_review_ingestion_343j.py -q
python tools\run_review_queue_strict_review_ingestion_343j.py --source-evidence-enrichment-343i2-dir D:\_datefac\output\review_queue_source_evidence_enrichment_343i2 --strict-human-review-package-343i-dir D:\_datefac\output\review_queue_strict_human_review_package_343i --audit-summary-343h-dir D:\_datefac\output\review_queue_audit_summary_343h --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --filled-workbook D:\_datefac\input\review_queue_strict_human_review_343i2_filled\review_queue_source_evidence_enrichment_343i2_enriched_review_template_filled.xlsx --output-dir D:\_datefac\output\review_queue_strict_review_ingestion_343j
```

## 15. Completion report

Report in Chinese:

1. 343J decision
2. review_queue_schema_version
3. filled_workbook_path
4. filled_row_count
5. valid_row_count
6. invalid_row_count
7. strict_confirm_count
8. strict_correct_count
9. strict_reject_count
10. strict_needs_source_check_count
11. strict_defer_count
12. strict_review_input_source_type
13. not_pure_human_review
14. pure_strict_human_confirm_count
15. ai_assisted_strict_review_confirm_count
16. strict_review_result_ingested
17. pure_strict_human_review_completed
18. strict_human_review_completed
19. requires_strict_human_review
20. requires_pure_human_confirmation
21. formal_client_export_allowed
22. client_ready
23. production_ready
24. ready_for_343k
25. recommended_343k_scope
26. qa_fail_count
27. no-write-back proof status
28. output directory
29. most important Excel/result/disclosure/export-gate artifacts
30. modified files
31. validation command results
32. git status summary
33. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
