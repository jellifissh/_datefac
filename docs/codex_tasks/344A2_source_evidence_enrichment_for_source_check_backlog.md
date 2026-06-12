# 344A2：Source Evidence Enrichment For Source-check Backlog

## 1. Positioning

344A generated a source-check backlog review package for 19 remaining rows, but all 19 rows were marked `UNRESOLVED` because the available backlog artifacts did not contain enough source evidence fields such as PDF name, page number, table locator, image path, or source text snippet.

344A2 enriches those 19 unresolved backlog rows by searching upstream extraction, review, table-first, MinerU, and source-evidence artifacts for source locators and evidence snippets.

The purpose is to turn as many rows as possible from `UNRESOLVED` into `PARTIAL` or `RESOLVED`, so a later human source-check review can actually inspect evidence instead of staring at an empty template like civilization has learned nothing.

344A2 is an evidence enrichment task. It is not source-check result ingestion, not production apply, not formal client export, not global client export, not Argilla integration, not frontend work, not real LLM/VLM review, and not an upstream extraction rerun.

Important boundary: 344A2 must not mark any backlog row as confirmed/corrected/rejected. It only enriches source evidence and regenerates an evidence-aware review template.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/344A_source_check_backlog_resolution_package.md`
- 344A summary / QA / backlog items / evidence map / review template / import contract / scope boundary
- 343O summary / backlog summary / artifact index / export gate snapshot
- 343H audit summary / source-check backlog / strict-human-gap report
- 343F source-check todo if available
- 343G spot-check result if available
- 343I2 source evidence enrichment code and outputs for the earlier 10-row package
- table-first and MinerU candidate/evidence artifacts if present
- current git status

Expected current state:

- latest completed milestone = `344A Source-check Backlog Resolution Package`
- 344A decision = `SOURCE_CHECK_BACKLOG_PACKAGE_344A_WAITING_FOR_SOURCE_CHECK_REVIEW`
- review_queue_schema_version = `343A.review_queue.v1`
- input_remaining_source_check_backlog_count = `19`
- source_check_backlog_item_count = `19`
- deduplicated_backlog_item_count = `19`
- evidence_resolved_count = `0`
- evidence_partial_count = `0`
- evidence_unresolved_count = `19`
- source_pdf_name_available_count = `0`
- source_text_snippet_available_count = `0`
- source_check_backlog_package_generated = `true`
- review_template_generated = `true`
- waiting_for_source_check_review = `true`
- source_check_result_ingested = `false`
- source_check_backlog_resolved = `false`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun MinerU, PPStructure, VLM, OCR, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, delivery, approval, or formal export code. Do not write back to upstream workbooks. Do not perform real production apply. Do not generate formal client export.

344A2 may read existing upstream artifacts and generate enriched backlog package artifacts under its own output directory.

Formal/global export boundary must remain conservative:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Source-check boundary:

- `source_check_result_ingested = false`
- `source_check_backlog_resolved = false`
- no row may be marked as source-confirmed by 344A2
- no source-check decision should be prefilled as completed

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/344A2_source_evidence_enrichment_for_source_check_backlog.md`
- `datefac/review_queue/source_check_evidence_enrichment_344a2.py`
- `datefac/benchmark/review_queue_source_check_evidence_enrichment_344a2.py`
- `datefac/benchmark/review_queue_source_check_evidence_enrichment_344a2_report.py`
- `tools/run_review_queue_source_check_evidence_enrichment_344a2.py`
- `tests/benchmark/test_review_queue_source_check_evidence_enrichment_344a2.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Primary input directory:

- `D:/_datefac/output/review_queue_source_check_backlog_package_344a`

Reference directories, read-only:

- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g`
- `D:/_datefac/output/review_queue_spot_check_package_343f`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2`
- `D:/_datefac/output/review_queue_schema_343a`
- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k`
- `D:/_datefac/output/post_adoption_sidecar_simulation_342o`
- `D:/_datefac/output/review_queue_real_excel_review_343c`
- `D:/_datefac/output/review_queue_excel_ingestion_343d`
- any existing `D:/_datefac/output/*342*` or `D:/_datefac/output/*343*` JSONL/JSON/XLSX artifacts that contain candidate ids, metric/year/value/unit, source page, source text, source PDF, image path, or table locator fields

Required 344A files:

- `review_queue_source_check_backlog_package_344a_summary.json`
- `review_queue_source_check_backlog_package_344a_qa.json`
- `review_queue_source_check_backlog_package_344a_backlog_items.jsonl`
- `review_queue_source_check_backlog_package_344a_evidence_map.json`
- `review_queue_source_check_backlog_package_344a_review_template.xlsx`
- `review_queue_source_check_backlog_package_344a_expected_import_contract.json`
- `review_queue_source_check_backlog_package_344a_no_write_back_proof.json`

If the primary 344A package is missing or not ready, fail gracefully. Do not fabricate source evidence.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2`

Output files:

- `review_queue_source_check_evidence_enrichment_344a2.xlsx`
- `review_queue_source_check_evidence_enrichment_344a2_summary.json`
- `review_queue_source_check_evidence_enrichment_344a2_manifest.json`
- `review_queue_source_check_evidence_enrichment_344a2_qa.json`
- `review_queue_source_check_evidence_enrichment_344a2_report.md`
- `review_queue_source_check_evidence_enrichment_344a2_enriched_backlog_items.jsonl`
- `review_queue_source_check_evidence_enrichment_344a2_evidence_match_candidates.jsonl`
- `review_queue_source_check_evidence_enrichment_344a2_evidence_map.json`
- `review_queue_source_check_evidence_enrichment_344a2_enriched_review_template.xlsx`
- `review_queue_source_check_evidence_enrichment_344a2_reviewer_instructions.md`
- `review_queue_source_check_evidence_enrichment_344a2_fill_guide.md`
- `review_queue_source_check_evidence_enrichment_344a2_expected_import_contract.json`
- `review_queue_source_check_evidence_enrichment_344a2_unresolved_evidence_report.md`
- `review_queue_source_check_evidence_enrichment_344a2_artifact_search_report.md`
- `review_queue_source_check_evidence_enrichment_344a2_scope_boundary.md`
- `review_queue_source_check_evidence_enrichment_344a2_no_write_back_proof.json`

Optional but recommended if lightweight:

- `review_queue_source_check_evidence_enrichment_344a2_match_confidence_audit.jsonl`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_ENRICH_SUMMARY`
- `02_INPUT_344A_SUMMARY`
- `03_ENRICHED_BACKLOG`
- `04_REVIEW_TEMPLATE`
- `05_EVIDENCE_MAP`
- `06_MATCH_CANDIDATES`
- `07_UNRESOLVED_REPORT`
- `08_IMPORT_CONTRACT`
- `09_SCOPE_BOUNDARY`
- `10_NO_WRITE_BACK`
- `11_NEXT_STEPS`

## 8. Core logic

### 8.1 Read and validate 344A state

Read 344A summary, QA, backlog items, evidence map, import contract, and no-write-back proof.

Validate:

- 344A is ready / waiting for source-check review
- backlog item count is 19
- deduplicated backlog item count is 19
- all 19 rows are unresolved or otherwise require evidence enrichment
- source-check result is not ingested
- source-check backlog is not resolved
- formal/client/production readiness flags remain false

### 8.2 Search upstream artifacts for evidence

Implement a conservative artifact scanner that can read existing JSON, JSONL, CSV, and XLSX artifacts from specified output directories.

The scanner should look for fields such as:

- identity: `queue_item_id`, `review_item_id`, `candidate_id`, `row_id`, `item_id`, `source_candidate_id`, `stable_key`
- candidate content: `metric_candidate_raw`, `metric_standardized`, `year_standardized`, `value_numeric`, `normalized_unit`, `value_raw`
- source locator: `source_pdf_name`, `source_pdf_path`, `pdf_name`, `pdf_path`, `source_file`, `source_file_name`, `source_page`, `page_number`, `page_idx`, `page`, `table_id`, `cell_id`, `bbox`, `image_path`, `table_image_path`
- evidence snippets: `source_text_snippet`, `source_html_snippet`, `row_text`, `table_text`, `evidence_text`, `matched_text`, `context_text`
- audit hints: `source_stage`, `artifact_path`, `sheet_name`, `line_number`, `match_reason`

Prefer exact identity matches. If identity is missing, use conservative composite matching with metric/year/value/unit and optional source/context fields.

### 8.3 Matching rules

For each 344A backlog item, attempt matches in this order:

1. exact `queue_item_id` / `review_item_id` / candidate id match
2. exact metric + year + numeric value + unit match
3. exact metric + year + numeric value match
4. metric + year + close numeric value match only if the match is unique and evidence locator exists

Do not accept fuzzy matches that produce multiple plausible candidates.

Each match candidate must record:

- `match_type`
- `match_confidence = HIGH | MEDIUM | LOW`
- `match_reason`
- `matched_artifact_path`
- `matched_artifact_type`
- `matched_sheet_or_line`
- matched source/evidence fields

Use only HIGH/MEDIUM matches to enrich fields automatically. LOW matches must be recorded in candidate report but not used as resolved evidence.

### 8.4 Evidence resolution status

For each backlog item after matching:

Set `evidence_resolution_status = RESOLVED` only if enough information exists for a reviewer to locate source evidence, meaning at least one of these combinations is present:

- source PDF name/path + page number + source text snippet
- source PDF name/path + page number + image/table path
- image/table path + source text snippet + metric/year/value fields
- explicit upstream evidence object with locator and snippet

Set `PARTIAL` if some locator or snippet exists but not enough to confidently inspect source.

Set `UNRESOLVED` if no usable locator/snippet is found.

Never invent PDF/page/text/image values.

### 8.5 Regenerate enriched source-check review template

Generate an enriched review template for 344B/344B2 human source check.

It must include all 19 rows and preserve editable columns from 344A:

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

Do not prefill any completed source-check decision.

Non-editable fields must include enriched evidence fields and match metadata:

- `evidence_resolution_status`
- `evidence_gap_reason`
- `source_pdf_name`
- `source_pdf_path`
- `page_number`
- `table_id`
- `cell_id`
- `bbox`
- `image_path`
- `source_text_snippet`
- `source_html_snippet`
- `evidence_source_stage`
- `evidence_source_artifact`
- `match_type`
- `match_confidence`
- `match_reason`

### 8.6 Reviewer instructions and fill guide

Generate updated instructions explaining:

- 344A2 enriches evidence but does not decide source-check outcomes
- which rows are RESOLVED/PARTIAL/UNRESOLVED
- how to open evidence using PDF/page/image/snippet fields
- what to do for unresolved rows
- allowed source-check decisions remain:
  - `SOURCE_CONFIRM`
  - `SOURCE_CORRECT`
  - `SOURCE_REJECT`
  - `SOURCE_STILL_INSUFFICIENT`
  - `SOURCE_DEFER`
- where to save the filled workbook for ingestion

Expected filled workbook path pattern:

`D:/_datefac/input/review_queue_source_check_evidence_344a2_filled/*.xlsx`

### 8.7 Expected import contract

Generate a new import contract for a later 344B or 344B2 ingestion task.

Required sheet name:

- `04_REVIEW_TEMPLATE`

The contract must include:

- identity columns
- enriched evidence columns
- editable source-check columns
- allowed decisions
- validation rules
- expected input path pattern above

344A2 must set waiting state and must not ingest filled results.

## 9. 344B readiness

If QA passes, set:

- `source_check_evidence_enrichment_completed = true`
- `enriched_review_template_generated = true`
- `evidence_map_generated = true`
- `expected_import_contract_generated = true`
- `waiting_for_source_check_review = true`
- `source_check_result_ingested = false`
- `source_check_backlog_resolved = false`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

Set:

- `ready_for_344b = false`
- `recommended_344b_scope = source_check_evidence_review_result_ingestion_after_user_fills_workbook`

This is intentional: 344B should start only after the user fills the enriched review workbook.

If all 19 rows remain unresolved, the task can still be ready if it truthfully reports no evidence found and produces a usable unresolved-evidence report.

## 10. Summary JSON

`review_queue_source_check_evidence_enrichment_344a2_summary.json` must include at least:

- `source_milestone = 344A`
- `decision`
- `review_queue_schema_version`
- `input_source_check_backlog_item_count`
- `deduplicated_backlog_item_count`
- `evidence_resolved_count`
- `evidence_partial_count`
- `evidence_unresolved_count`
- `source_pdf_name_available_count`
- `page_number_available_count`
- `image_path_available_count`
- `source_text_snippet_available_count`
- `match_candidate_count`
- `high_confidence_match_count`
- `medium_confidence_match_count`
- `low_confidence_match_count`
- `auto_enriched_item_count`
- `unresolved_item_count`
- `source_check_evidence_enrichment_completed`
- `enriched_review_template_generated`
- `reviewer_instructions_generated`
- `fill_guide_generated`
- `expected_import_contract_generated`
- `waiting_for_source_check_review`
- `source_check_result_ingested = false`
- `source_check_backlog_resolved = false`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_344b = false`
- `recommended_344b_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if enrichment artifacts are generated: `SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_WAITING_FOR_SOURCE_CHECK_REVIEW`
- otherwise: `SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_NOT_READY`

## 11. QA requirements

Must check:

- 344A input exists and is ready
- 19 backlog rows are preserved
- no backlog row is dropped
- no source-check decision is prefilled as completed
- every backlog item has evidence resolution status
- every enriched field is traceable to a matched artifact or explicitly blank/unresolved
- match candidates are logged
- low-confidence ambiguous matches are not auto-applied
- unresolved evidence is explicitly disclosed
- enriched review template is generated
- reviewer instructions are generated
- fill guide is generated
- expected import contract is generated
- waiting_for_source_check_review is true
- source_check_result_ingested is false
- source_check_backlog_resolved is false
- formal/client/production readiness flags remain false
- no formal client export workbook is generated
- no Argilla call is made
- no real production apply is performed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_source_check_evidence_enrichment_344a2_report.md` in Chinese-first, English-friendly style.

It must explain:

- 344A2 attempts to enrich 19 source-check backlog rows with source evidence
- what artifact sources were scanned
- how many rows became RESOLVED/PARTIAL/UNRESOLVED
- whether evidence is sufficient for human source-check review
- no row was confirmed/corrected/rejected in this task
- formal client export remains forbidden
- next task after user fills the enriched workbook is source-check review result ingestion

## 13. Ledger update

Update the project milestone ledger with:

- 344A2 evidence enrichment status
- inputs
- scanned artifact categories
- outputs
- key metrics
- validation result
- decision
- evidence resolution summary
- unresolved evidence summary
- source-check/global export boundary
- next required user action
- next recommended task after user fills workbook

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\source_check_evidence_enrichment_344a2.py datefac\benchmark\review_queue_source_check_evidence_enrichment_344a2.py datefac\benchmark\review_queue_source_check_evidence_enrichment_344a2_report.py tools\run_review_queue_source_check_evidence_enrichment_344a2.py tests\benchmark\test_review_queue_source_check_evidence_enrichment_344a2.py
python -m pytest tests\benchmark\test_review_queue_source_check_evidence_enrichment_344a2.py -q
python tools\run_review_queue_source_check_evidence_enrichment_344a2.py --source-check-backlog-package-344a-dir D:\_datefac\output\review_queue_source_check_backlog_package_344a --demo-audit-snapshot-343o-dir D:\_datefac\output\review_queue_demo_audit_snapshot_343o --audit-summary-343h-dir D:\_datefac\output\review_queue_audit_summary_343h --spot-check-ingestion-343g-dir D:\_datefac\output\review_queue_spot_check_ingestion_343g --spot-check-package-343f-dir D:\_datefac\output\review_queue_spot_check_package_343f --source-evidence-enrichment-343i2-dir D:\_datefac\output\review_queue_source_evidence_enrichment_343i2 --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-search-root D:\_datefac\output --output-dir D:\_datefac\output\review_queue_source_check_evidence_enrichment_344a2
```

## 15. Completion report

Report in Chinese:

1. 344A2 decision
2. review_queue_schema_version
3. input_source_check_backlog_item_count
4. deduplicated_backlog_item_count
5. evidence_resolved_count
6. evidence_partial_count
7. evidence_unresolved_count
8. source_pdf_name_available_count
9. page_number_available_count
10. image_path_available_count
11. source_text_snippet_available_count
12. match_candidate_count
13. high/medium/low confidence match counts
14. auto_enriched_item_count
15. unresolved_item_count
16. source_check_evidence_enrichment_completed
17. enriched_review_template_generated
18. expected_import_contract_generated
19. waiting_for_source_check_review
20. source_check_result_ingested
21. source_check_backlog_resolved
22. formal_client_export_allowed
23. client_ready
24. production_ready
25. ready_for_344b
26. recommended_344b_scope
27. qa_fail_count
28. no-write-back proof status
29. output directory
30. most important enriched template / evidence map / match candidates / unresolved report / import contract artifacts
31. modified files
32. validation command results
33. git status summary
34. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
