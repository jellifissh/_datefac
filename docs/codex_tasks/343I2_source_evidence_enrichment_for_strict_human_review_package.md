# 343I2：Source Evidence Enrichment For Strict Human Review Package

## 1. Positioning

343I2 fixes the evidence gap exposed by 343I. The 343I strict human review template contains 10 AI-assisted confirmed rows, but it does not provide enough source evidence for a reviewer to independently verify each row.

This task must enrich the strict human review package with source evidence locators and evidence context wherever available, so a reviewer can know which PDF/page/table/text/image should be checked before making a strict human decision.

343I2 is an evidence-enrichment task. It is not strict human review ingestion, not production apply, not formal client export, not Argilla integration, not a frontend implementation, not real LLM/VLM review, and not an upstream extraction rerun.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/343I_strict_human_review_package_for_ai_assisted_confirmed_rows.md`
- 343I summary / QA / review template / review items JSONL / import contract / fill guide
- 343H summary / confirmed AI-assisted items / gap items / source-check backlog / client export gate
- 343G result JSONL and summary
- 343E apply plan / simulated sidecar
- 343D reviewed result JSONL
- 343A schema artifacts
- current git status

Expected current state:

- latest completed milestone = `343I Strict Human Review Package For AI-assisted Confirmed Rows`
- 343I decision = `STRICT_HUMAN_REVIEW_PACKAGE_343I_WAITING_FOR_STRICT_REVIEW`
- input_ai_assisted_confirmed_count = `10`
- strict_review_item_count = `10`
- waiting_for_strict_human_review = `true`
- strict_human_review_result_ingested = `false`
- strict_human_review_completed = `false`
- requires_strict_human_review = `true`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- ready_for_343j = `false`
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

Evidence enrichment must be conservative:

- do not fabricate PDF names, page numbers, bbox, image paths, or source snippets
- if evidence cannot be resolved, mark it as missing or unresolved
- if evidence is available only through inherited upstream fields, clearly mark its source stage
- do not turn unresolved evidence into confirmation

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343I2_source_evidence_enrichment_for_strict_human_review_package.md`
- `datefac/review_queue/source_evidence_enrichment_343i2.py`
- `datefac/benchmark/review_queue_source_evidence_enrichment_343i2.py`
- `datefac/benchmark/review_queue_source_evidence_enrichment_343i2_report.py`
- `tools/run_review_queue_source_evidence_enrichment_343i2.py`
- `tests/benchmark/test_review_queue_source_evidence_enrichment_343i2.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_strict_human_review_package_343i`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g`
- `D:/_datefac/output/review_queue_apply_simulation_343e`
- `D:/_datefac/output/review_queue_excel_ingestion_343d`
- `D:/_datefac/output/review_queue_schema_343a`

Optional upstream directories to inspect if they exist:

- `D:/_datefac/output/review_queue_spot_check_package_343f`
- `D:/_datefac/output/review_queue_real_excel_review_343c`
- `D:/_datefac/output/audit_labeled_export_candidate_package_342r`
- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p`
- `D:/_datefac/output/preview_audit_export_readiness_gate_342q`
- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s`

Required 343I files:

- `review_queue_strict_human_review_package_343i_summary.json`
- `review_queue_strict_human_review_package_343i_qa.json`
- `review_queue_strict_human_review_package_343i_review_template.xlsx`
- `review_queue_strict_human_review_package_343i_review_items.jsonl`
- `review_queue_strict_human_review_package_343i_expected_import_contract.json`

Required upstream reference files:

- `review_queue_audit_summary_343h_confirmed_ai_assisted_items.jsonl`
- `review_queue_audit_summary_343h_gap_items.jsonl`
- `review_queue_spot_check_ingestion_343g_result.jsonl`
- `review_queue_apply_simulation_343e_apply_plan.jsonl`
- `review_queue_excel_ingestion_343d_reviewed_result.jsonl`
- `review_queue_schema_343a_schema.json`

If source-evidence fields are not present in available upstream artifacts, do not fail solely for that reason. Generate an evidence gap report and mark those rows as evidence unresolved.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_source_evidence_enrichment_343i2`

Output files:

- `review_queue_source_evidence_enrichment_343i2.xlsx`
- `review_queue_source_evidence_enrichment_343i2_summary.json`
- `review_queue_source_evidence_enrichment_343i2_manifest.json`
- `review_queue_source_evidence_enrichment_343i2_qa.json`
- `review_queue_source_evidence_enrichment_343i2_report.md`
- `review_queue_source_evidence_enrichment_343i2_enriched_review_template.xlsx`
- `review_queue_source_evidence_enrichment_343i2_enriched_items.jsonl`
- `review_queue_source_evidence_enrichment_343i2_evidence_gap_report.md`
- `review_queue_source_evidence_enrichment_343i2_evidence_resolution_map.json`
- `review_queue_source_evidence_enrichment_343i2_unresolved_evidence_items.jsonl`
- `review_queue_source_evidence_enrichment_343i2_expected_import_contract.json`
- `review_queue_source_evidence_enrichment_343i2_no_write_back_proof.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_ENRICH_SUMMARY`
- `02_INPUT_343I_SUMMARY`
- `03_ENRICHED_ITEMS`
- `04_REVIEW_TEMPLATE`
- `05_EVIDENCE_FIELDS`
- `06_RESOLUTION_MAP`
- `07_UNRESOLVED_EVIDENCE`
- `08_DECISION_GUIDE`
- `09_IMPORT_CONTRACT`
- `10_343J_READINESS`
- `11_NO_WRITE_BACK`
- `12_NEXT_STEPS`

## 8. Core logic

### 8.1 Read 343I review items

Read the 10 strict review items from `review_queue_strict_human_review_package_343i_review_items.jsonl` and the 343I workbook/template.

Each item must preserve identity fields:

- `queue_item_id`
- `review_item_id`
- `resulting_status`
- `simulated_downstream_action`
- `priority_tier`

### 8.2 Trace upstream evidence fields

For each strict review item, attempt to trace evidence fields through available artifacts using stable identifiers such as:

- `queue_item_id`
- `review_item_id`
- `source_stage`
- `source_row_id`
- `source_artifact_path`
- `source_artifact_sheet`

Candidate evidence fields to resolve:

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

Do not invent missing fields. If upstream artifacts do not contain PDF/page/source evidence, set:

- `evidence_resolution_status = UNRESOLVED`
- `evidence_gap_reason = source PDF/page/table evidence not present in available upstream artifacts`

If partial evidence is found, set:

- `evidence_resolution_status = PARTIAL`

If enough evidence is found to locate the original PDF/page/table, set:

- `evidence_resolution_status = RESOLVED`

### 8.3 Generate enriched strict review template

Generate an enriched strict review template that includes the original strict review fields plus source evidence locator columns.

Editable columns remain only:

- `strict_review_decision`
- `strict_review_metric_standardized`
- `strict_review_year_standardized`
- `strict_review_value_numeric`
- `strict_review_normalized_unit`
- `strict_review_note`
- `strict_reviewer_id`
- `strict_reviewed_at`

Allowed decisions remain:

- `STRICT_CONFIRM`
- `STRICT_CORRECT`
- `STRICT_REJECT`
- `STRICT_NEEDS_SOURCE_CHECK`
- `STRICT_DEFER`

No strict review decision should be prefilled as completed.

### 8.4 Decision guide based on evidence status

Add a decision guide:

- `RESOLVED`: reviewer may inspect source evidence and decide `STRICT_CONFIRM`, `STRICT_CORRECT`, `STRICT_REJECT`, `STRICT_NEEDS_SOURCE_CHECK`, or `STRICT_DEFER`.
- `PARTIAL`: recommend `STRICT_NEEDS_SOURCE_CHECK` unless the reviewer can independently locate the missing source evidence.
- `UNRESOLVED`: recommend `STRICT_NEEDS_SOURCE_CHECK`; do not allow the package to claim strict human review completeness.

### 8.5 Import contract for 343J

Generate an updated import contract for 343J that points to the enriched workbook:

- expected input path pattern: `D:/_datefac/input/review_queue_strict_human_review_343i2_filled/*.xlsx`
- required sheet name: `04_REVIEW_TEMPLATE`
- required identity columns
- source evidence columns
- editable strict review columns
- allowed strict review decisions
- validation rules

343I2 must not ingest strict review results. It must set a waiting-for-strict-human-review state.

## 9. 343J readiness

If QA passes, set:

- `source_evidence_enrichment_completed = true`
- `enriched_review_template_generated = true`
- `waiting_for_strict_human_review = true`
- `strict_human_review_result_ingested = false`
- `strict_human_review_completed = false`
- `ready_for_343j = false`
- `recommended_343j_scope = strict_human_review_result_ingestion_after_user_fills_enriched_workbook`

This is intentional: 343J should start only after the user fills the enriched strict human review workbook.

## 10. Summary JSON

`review_queue_source_evidence_enrichment_343i2_summary.json` must include at least:

- `source_milestone = 343I`
- `decision`
- `review_queue_schema_version`
- `input_strict_review_item_count`
- `enriched_review_item_count`
- `evidence_resolved_count`
- `evidence_partial_count`
- `evidence_unresolved_count`
- `source_pdf_name_available_count`
- `source_pdf_path_available_count`
- `page_number_available_count`
- `source_text_snippet_available_count`
- `image_path_available_count`
- `enriched_review_template_generated`
- `evidence_gap_report_generated`
- `expected_import_contract_generated`
- `source_evidence_enrichment_completed`
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

- if ready for user strict review with enriched evidence: `SOURCE_EVIDENCE_ENRICHMENT_343I2_WAITING_FOR_STRICT_REVIEW`
- otherwise: `SOURCE_EVIDENCE_ENRICHMENT_343I2_NOT_READY`

## 11. QA requirements

Must check:

- 343I input exists and is waiting for strict human review
- strict review items exist and are readable
- exactly the expected 10 items are carried forward unless upstream says otherwise
- enrichment does not fabricate evidence fields
- every item has an evidence resolution status
- unresolved evidence items are explicitly listed
- enriched review template is generated
- editable strict review columns exist
- no strict review decision is prefilled as completed
- expected import contract is generated
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

Generate `review_queue_source_evidence_enrichment_343i2_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343I exposed that strict human review was not possible without source evidence locators
- 343I2 enriches the review package with all available evidence fields
- unresolved evidence is not hidden or fabricated
- how reviewers should decide based on RESOLVED/PARTIAL/UNRESOLVED evidence
- strict human review is still pending
- formal client export remains forbidden
- next task after user filling is 343J strict human review result ingestion

## 13. Ledger update

Update the project milestone ledger with:

- 343I2 completed as source evidence enrichment / waiting-for-strict-review package generation
- inputs
- outputs
- key metrics
- QA result
- decision
- evidence resolution summary
- unresolved evidence summary
- client export boundary
- next required user action
- next recommended task after user fills workbook

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\source_evidence_enrichment_343i2.py datefac\benchmark\review_queue_source_evidence_enrichment_343i2.py datefac\benchmark\review_queue_source_evidence_enrichment_343i2_report.py tools\run_review_queue_source_evidence_enrichment_343i2.py tests\benchmark\test_review_queue_source_evidence_enrichment_343i2.py
python -m pytest tests\benchmark\test_review_queue_source_evidence_enrichment_343i2.py -q
python tools\run_review_queue_source_evidence_enrichment_343i2.py --strict-human-review-package-343i-dir D:\_datefac\output\review_queue_strict_human_review_package_343i --audit-summary-343h-dir D:\_datefac\output\review_queue_audit_summary_343h --spot-check-ingestion-343g-dir D:\_datefac\output\review_queue_spot_check_ingestion_343g --apply-simulation-343e-dir D:\_datefac\output\review_queue_apply_simulation_343e --excel-ingestion-343d-dir D:\_datefac\output\review_queue_excel_ingestion_343d --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_source_evidence_enrichment_343i2
```

## 15. Completion report

Report in Chinese:

1. 343I2 decision
2. review_queue_schema_version
3. input_strict_review_item_count
4. enriched_review_item_count
5. evidence_resolved_count
6. evidence_partial_count
7. evidence_unresolved_count
8. source_pdf_name_available_count
9. source_pdf_path_available_count
10. page_number_available_count
11. source_text_snippet_available_count
12. image_path_available_count
13. enriched_review_template_generated
14. evidence_gap_report_generated
15. expected_import_contract_generated
16. source_evidence_enrichment_completed
17. waiting_for_strict_human_review
18. strict_human_review_result_ingested
19. strict_human_review_completed
20. requires_strict_human_review
21. formal_client_export_allowed
22. client_ready
23. production_ready
24. ready_for_343j
25. recommended_343j_scope
26. qa_fail_count
27. no-write-back proof status
28. output directory
29. most important enriched Excel/template/evidence-gap/import-contract artifacts
30. modified files
31. validation command results
32. git status summary
33. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
