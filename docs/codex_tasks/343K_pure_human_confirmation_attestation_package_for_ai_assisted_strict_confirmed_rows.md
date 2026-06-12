# 343K：Pure Human Confirmation Attestation Package For AI-assisted Strict-confirmed Rows

## 1. Positioning

343K consumes the 343J AI-assisted strict-review ingestion outputs and creates a pure-human-confirmation attestation package for the 10 rows that are currently AI-assisted strict-review confirmed.

The purpose is to give a real human reviewer a focused package to independently attest whether they personally checked the source evidence and accept, override, or reject the AI-assisted strict-review decisions.

343K only creates the attestation package and fillable template. It must not ingest attestation results yet, must not claim pure strict human review is complete, and must not enable formal client export.

343K is a human-attestation package generation task. It is not production apply, not formal client export, not Argilla integration, not a frontend implementation, not real LLM/VLM review, and not an upstream extraction rerun.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/343J_strict_review_result_ingestion_from_enriched_workbook.md`
- `docs/codex_tasks/343I2_source_evidence_enrichment_for_strict_human_review_package.md`
- 343J summary / QA / result JSONL / decision summary / reviewer-source disclosure / client export gate
- 343I2 enriched items / evidence resolution map / enriched review template / import contract
- 343H audit summary / client export gate
- 343A schema artifacts
- current git status

Expected current state:

- latest completed milestone = `343J Strict Review Result Ingestion From Enriched Workbook`
- 343J decision = `AI_ASSISTED_STRICT_REVIEW_INGESTION_343J_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- filled_row_count = `10`
- valid_row_count = `10`
- invalid_row_count = `0`
- strict_confirm_count = `10`
- strict_correct_count = `0`
- strict_reject_count = `0`
- strict_needs_source_check_count = `0`
- strict_defer_count = `0`
- strict_review_input_source_type = `AI_ASSISTED_EVIDENCE_CHECK`
- not_pure_human_review = `true`
- pure_strict_human_confirm_count = `0`
- ai_assisted_strict_review_confirm_count = `10`
- strict_review_result_ingested = `true`
- pure_strict_human_review_completed = `false`
- strict_human_review_completed = `false`
- requires_strict_human_review = `true`
- requires_pure_human_confirmation = `true`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- ready_for_343k = `true`
- recommended_343k_scope = `pure_human_confirmation_attestation_package_for_ai_assisted_strict_confirmed_rows`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, or delivery code. Do not write back to upstream workbooks. Do not generate formal client export. Do not perform real production apply.

343K must not ingest pure human attestation results. That belongs to a later ingestion task after the user fills the workbook.

Preserve these flags:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `pure_strict_human_review_completed = false`
- `strict_human_review_completed = false`
- `requires_pure_human_confirmation = true`

Current upstream disclosure:

- `strict_review_input_source_type = AI_ASSISTED_EVIDENCE_CHECK`
- `not_pure_human_review = true`
- current 10 confirms are AI-assisted strict-review confirms, not pure human confirms

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343K_pure_human_confirmation_attestation_package_for_ai_assisted_strict_confirmed_rows.md`
- `datefac/review_queue/pure_human_attestation_package_343k.py`
- `datefac/benchmark/review_queue_pure_human_attestation_package_343k.py`
- `datefac/benchmark/review_queue_pure_human_attestation_package_343k_report.py`
- `tools/run_review_queue_pure_human_attestation_package_343k.py`
- `tests/benchmark/test_review_queue_pure_human_attestation_package_343k.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_strict_review_ingestion_343j`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2`
- `D:/_datefac/output/review_queue_strict_human_review_package_343i`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_schema_343a`

Required 343J files:

- `review_queue_strict_review_ingestion_343j_summary.json`
- `review_queue_strict_review_ingestion_343j_qa.json`
- `review_queue_strict_review_ingestion_343j_result.jsonl`
- `review_queue_strict_review_ingestion_343j_decision_summary.json`
- `review_queue_strict_review_ingestion_343j_client_export_gate.json`
- `review_queue_strict_review_ingestion_343j_reviewer_source_disclosure.md`
- `review_queue_strict_review_ingestion_343j_no_write_back_proof.json`

Required 343I2 reference files:

- `review_queue_source_evidence_enrichment_343i2_enriched_items.jsonl`
- `review_queue_source_evidence_enrichment_343i2_evidence_resolution_map.json`
- `review_queue_source_evidence_enrichment_343i2_expected_import_contract.json`

Required 343A schema file:

- `review_queue_schema_343a_schema.json`

If required 343J files are missing or 343J is not ready, fail gracefully with a clear error. Do not fabricate attestation rows.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_pure_human_attestation_package_343k`

Output files:

- `review_queue_pure_human_attestation_package_343k.xlsx`
- `review_queue_pure_human_attestation_package_343k_summary.json`
- `review_queue_pure_human_attestation_package_343k_manifest.json`
- `review_queue_pure_human_attestation_package_343k_qa.json`
- `review_queue_pure_human_attestation_package_343k_report.md`
- `review_queue_pure_human_attestation_package_343k_attestation_template.xlsx`
- `review_queue_pure_human_attestation_package_343k_attestation_items.jsonl`
- `review_queue_pure_human_attestation_package_343k_reviewer_instructions.md`
- `review_queue_pure_human_attestation_package_343k_fill_guide.md`
- `review_queue_pure_human_attestation_package_343k_expected_import_contract.json`
- `review_queue_pure_human_attestation_package_343k_client_export_boundary.md`
- `review_queue_pure_human_attestation_package_343k_no_write_back_proof.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_PACKAGE_SUMMARY`
- `02_INPUT_343J_SUMMARY`
- `03_ATTESTATION_ITEMS`
- `04_ATTESTATION_TEMPLATE`
- `05_SOURCE_EVIDENCE`
- `06_ATTESTATION_RULES`
- `07_CLIENT_EXPORT_BOUNDARY`
- `08_IMPORT_CONTRACT`
- `09_343L_READINESS`
- `10_NO_WRITE_BACK`
- `11_NEXT_STEPS`

## 8. Core logic

### 8.1 Read 343J results

Read `review_queue_strict_review_ingestion_343j_result.jsonl` and summary/QA files.

Validate:

- 343J is ready
- row count is 10
- valid row count is 10
- invalid row count is 0
- strict_confirm_count is 10
- strict_review_input_source_type is `AI_ASSISTED_EVIDENCE_CHECK`
- pure strict human review is not completed
- formal/client/production readiness flags remain false

### 8.2 Build attestation package

Generate attestation items only for rows that are currently valid `STRICT_CONFIRM` under the AI-assisted evidence-check source.

Each item should carry forward:

- `queue_item_id`
- `review_item_id`
- `resulting_status`
- `simulated_downstream_action`
- `priority_tier`
- `metric_standardized`
- `year_standardized`
- `value_numeric`
- `normalized_unit`
- source evidence locator fields from 343I2
- AI-assisted strict review decision and note from 343J
- reviewer source disclosure fields

### 8.3 Fillable pure human attestation template

Generate a fillable attestation template with non-editable identity/evidence/candidate fields and editable pure-human attestation columns:

- `human_attestation_decision`
- `human_attested_metric_standardized`
- `human_attested_year_standardized`
- `human_attested_value_numeric`
- `human_attested_normalized_unit`
- `human_attestation_note`
- `human_reviewer_id`
- `human_reviewed_at`
- `human_source_evidence_checked`
- `human_independent_check_attested`

Allowed human attestation decisions:

- `HUMAN_ACCEPT_AI_ASSISTED_CONFIRM`
- `HUMAN_CORRECT`
- `HUMAN_REJECT`
- `HUMAN_NEEDS_SOURCE_CHECK`
- `HUMAN_DEFER`

Rules:

- `HUMAN_ACCEPT_AI_ASSISTED_CONFIRM` requires human reviewer id, reviewed date, source evidence checked = true, independent check attested = true.
- `HUMAN_CORRECT` requires corrected metric/year/value/unit plus note, reviewer id/date, and source evidence checked = true.
- `HUMAN_REJECT` requires note, reviewer id/date, and source evidence checked = true.
- `HUMAN_NEEDS_SOURCE_CHECK` requires note and reviewer id/date.
- `HUMAN_DEFER` requires reviewer id/date and note when possible.
- No human attestation decision should be prefilled as completed.

### 8.4 Reviewer instructions and fill guide

Generate Markdown instructions explaining:

- this package is for real human attestation over AI-assisted strict-review confirmed rows
- the human must independently inspect source evidence, not just approve the AI result
- how to use source PDF/page/table/snippet/image evidence fields
- how to fill each decision
- which fields are mandatory for human acceptance or correction
- where to save the filled workbook for 343L ingestion

### 8.5 Expected import contract for 343L

Generate a JSON import contract describing:

- required sheet name: `04_ATTESTATION_TEMPLATE`
- required identity columns
- source evidence columns
- editable attestation columns
- allowed human attestation decisions
- validation rules
- expected input path pattern: `D:/_datefac/input/review_queue_pure_human_attestation_343k_filled/*.xlsx`

343K must not ingest attestation results. It must set a waiting-for-pure-human-attestation state.

## 9. 343L readiness

If QA passes, set:

- `pure_human_attestation_package_generated = true`
- `attestation_template_generated = true`
- `reviewer_instructions_generated = true`
- `fill_guide_generated = true`
- `expected_import_contract_generated = true`
- `waiting_for_pure_human_attestation = true`
- `pure_human_attestation_result_ingested = false`
- `pure_strict_human_review_completed = false`
- `strict_human_review_completed = false`
- `ready_for_343l = false`
- `recommended_343l_scope = pure_human_confirmation_attestation_result_ingestion_after_user_fills_workbook`

This is intentional: 343L should start only after the user fills the pure human attestation workbook.

## 10. Summary JSON

`review_queue_pure_human_attestation_package_343k_summary.json` must include at least:

- `source_milestone = 343J`
- `decision`
- `review_queue_schema_version`
- `input_ai_assisted_strict_review_confirm_count`
- `attestation_item_count`
- `evidence_resolved_count`
- `source_pdf_name_available_count`
- `source_text_snippet_available_count`
- `pure_human_attestation_package_generated`
- `attestation_template_generated`
- `reviewer_instructions_generated`
- `fill_guide_generated`
- `expected_import_contract_generated`
- `waiting_for_pure_human_attestation`
- `pure_human_attestation_result_ingested = false`
- `pure_strict_human_confirm_count = 0`
- `ai_assisted_strict_review_confirm_count`
- `pure_strict_human_review_completed = false`
- `strict_human_review_completed = false`
- `requires_pure_human_confirmation = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343l = false`
- `recommended_343l_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready for user attestation: `PURE_HUMAN_ATTESTATION_PACKAGE_343K_WAITING_FOR_HUMAN_ATTESTATION`
- otherwise: `PURE_HUMAN_ATTESTATION_PACKAGE_343K_NOT_READY`

## 11. QA requirements

Must check:

- 343J input exists and is ready
- 343J disclosure confirms AI-assisted evidence-check source
- exactly 10 valid AI-assisted strict-confirm rows are carried forward unless upstream says otherwise
- source evidence locator fields are preserved
- attestation template is generated
- reviewer instructions are generated
- fill guide is generated
- expected import contract is generated
- editable attestation columns exist
- allowed human attestation decision list is present
- human attestation decisions are not prefilled as completed
- waiting_for_pure_human_attestation is true
- pure human attestation result is not ingested
- pure strict human review is not claimed as complete
- no formal/client/production readiness flag is true
- no Argilla call is made
- no real production apply is performed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_pure_human_attestation_package_343k_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343K creates a pure-human attestation package for 10 AI-assisted strict-confirm rows
- it does not ingest human attestation results yet
- it does not mean pure strict human review is complete
- the human reviewer must independently inspect source evidence
- formal client export remains forbidden
- next task after user filling is 343L pure human attestation result ingestion

## 13. Ledger update

Update the project milestone ledger with:

- 343K completed as waiting-for-pure-human-attestation package generation
- inputs
- outputs
- key metrics
- QA result
- decision
- attestation package summary
- client export boundary
- next required user action
- next recommended task after user fills workbook

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\pure_human_attestation_package_343k.py datefac\benchmark\review_queue_pure_human_attestation_package_343k.py datefac\benchmark\review_queue_pure_human_attestation_package_343k_report.py tools\run_review_queue_pure_human_attestation_package_343k.py tests\benchmark\test_review_queue_pure_human_attestation_package_343k.py
python -m pytest tests\benchmark\test_review_queue_pure_human_attestation_package_343k.py -q
python tools\run_review_queue_pure_human_attestation_package_343k.py --strict-review-ingestion-343j-dir D:\_datefac\output\review_queue_strict_review_ingestion_343j --source-evidence-enrichment-343i2-dir D:\_datefac\output\review_queue_source_evidence_enrichment_343i2 --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_pure_human_attestation_package_343k
```

## 15. Completion report

Report in Chinese:

1. 343K decision
2. review_queue_schema_version
3. input_ai_assisted_strict_review_confirm_count
4. attestation_item_count
5. evidence_resolved_count
6. source_pdf_name_available_count
7. source_text_snippet_available_count
8. pure_human_attestation_package_generated
9. attestation_template_generated
10. reviewer_instructions_generated
11. fill_guide_generated
12. expected_import_contract_generated
13. waiting_for_pure_human_attestation
14. pure_human_attestation_result_ingested
15. pure_strict_human_confirm_count
16. ai_assisted_strict_review_confirm_count
17. pure_strict_human_review_completed
18. strict_human_review_completed
19. requires_pure_human_confirmation
20. formal_client_export_allowed
21. client_ready
22. production_ready
23. ready_for_343l
24. recommended_343l_scope
25. qa_fail_count
26. no-write-back proof status
27. output directory
28. most important Excel/template/fill-guide/import-contract artifacts
29. modified files
30. validation command results
31. git status summary
32. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
