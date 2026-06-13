# 345B Full Extraction Quality Audit

## Goal

Implement `345B Full Extraction Quality Audit`.

345A is completed and produced the full structured-data inventory:

- `decision = FULL_STRUCTURED_DATA_INVENTORY_345A_READY`
- `total_inventory_row_count = 14788`
- `LONG_FORM_CELL = 5607`
- `TRUSTED_CELL = 1578`
- `REVIEW_REQUIRED = 4240`
- `REJECTED_OR_EXCLUDED = 3213`
- `HUMAN_REVIEW_APPLIED = 121`
- `STRICT_HUMAN_REVIEW_PENDING_ROW = 29`
- `UNKNOWN_STAGE = 0`
- `downstream_ready_candidate_count = 11575`
- `missing_unit_count = 3949`
- `missing_period_count = 399`
- `missing_source_page_count = 5232`
- `missing_metric_name_count = 0`
- all formal/client/production gates remain false

345B must audit quality problems in the inventoried structured rows. 345A answered "how much data exists". 345B answers "where is the extraction quality weak, how severe are the weak spots, and what should be fixed first".

345B is audit-only. It must not rerun MinerU, call LLM/VLM, rewrite extraction outputs, or create formal client export.

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345B_full_extraction_quality_audit.md`

Inspect only runner input dirs. Do not scan the whole repo.

## Runner inputs

Support:

```powershell
--full-structured-data-inventory-345a-dir D:\_datefac\output\full_structured_data_inventory_345a
--output-dir D:\_datefac\output\full_extraction_quality_audit_345b
```

Optional supporting input dirs may be accepted, but 345B should primarily consume 345A outputs:

```powershell
--table-first-core-financial-extraction-342f-dir D:\_datefac\output\table_first_core_financial_extraction_342f
--table-first-extraction-review-package-342g-dir D:\_datefac\output\table_first_extraction_review_package_342g
--table-first-human-review-apply-simulation-342h-dir D:\_datefac\output\table_first_human_review_apply_simulation_342h
--review-queue-strict-human-review-package-344f-dir D:\_datefac\output\review_queue_strict_human_review_package_344f
```

If the 345A manifest, row inventory, or summary files are missing, fail clearly.

## Outputs

Write only under:

```text
D:\_datefac\output\full_extraction_quality_audit_345b
```

Generate:

- `full_extraction_quality_audit_345b_manifest.json`
- `full_extraction_quality_audit_345b_quality_rows.json`
- `full_extraction_quality_audit_345b_quality_rows.csv`
- `full_extraction_quality_audit_345b_stage_quality_summary.json`
- `full_extraction_quality_audit_345b_stage_quality_summary.csv`
- `full_extraction_quality_audit_345b_pdf_quality_summary.json`
- `full_extraction_quality_audit_345b_pdf_quality_summary.csv`
- `full_extraction_quality_audit_345b_missing_field_hotspots.json`
- `full_extraction_quality_audit_345b_evidence_trace_quality.json`
- `full_extraction_quality_audit_345b_priority_fix_queue.json`
- `full_extraction_quality_audit_345b_priority_fix_queue.csv`
- `full_extraction_quality_audit_345b_executive_summary.md`
- `full_extraction_quality_audit_345b_artifact_index.md`
- `full_extraction_quality_audit_345b_next_plan.md`

Do not write back into 345A or any upstream output dir.

## Quality dimensions

For each inventory row from 345A, compute audit fields where possible:

- `quality_row_id`
- `inventory_row_id`
- `source_artifact`
- `source_stage`
- `pdf_id`
- `pdf_name`
- `table_id`
- `metric_name`
- `normalized_metric_name`
- `value_raw`
- `value_normalized`
- `unit`
- `period`
- `source_page`
- `trust_status`
- `review_status`
- `human_review_status`
- `missing_required_fields`
- `has_metric_name`
- `has_value`
- `has_unit`
- `has_period`
- `has_source_trace`
- `is_rejected_or_excluded`
- `is_downstream_ready_candidate`
- `quality_issue_count`
- `quality_issues`
- `quality_severity`
- `recommended_action`

Suggested issue labels:

- `MISSING_UNIT`
- `MISSING_PERIOD`
- `MISSING_SOURCE_TRACE`
- `REJECTED_OR_EXCLUDED`
- `REVIEW_REQUIRED`
- `UNNORMALIZED_METRIC`
- `HUMAN_REVIEW_PENDING`
- `STRICT_HUMAN_REVIEW_PENDING`
- `LOW_TRACEABILITY`

Severity rule:

- `HIGH`: rejected/excluded, missing source trace on candidate rows, or multiple critical missing fields
- `MEDIUM`: review-required, missing unit/period, unnormalized metric, or human-review pending
- `LOW`: trusted/downstream-ready rows with minor missing non-critical fields
- `NONE`: no detected quality issue

Recommended actions may include:

- `KEEP_AS_READY_CANDIDATE`
- `REVIEW_REQUIRED`
- `FIX_SOURCE_TRACE`
- `FIX_UNIT_OR_PERIOD`
- `NORMALIZE_METRIC_NAME`
- `KEEP_REJECTED`
- `WAIT_FOR_HUMAN_REVIEW`

Do not invent evidence. Only classify using available fields.

## Manifest metrics

Manifest must include:

- `decision = FULL_EXTRACTION_QUALITY_AUDIT_345B_READY`
- `input_stage = POST_345A_FULL_STRUCTURED_QUALITY_AUDIT`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_inventory_row_count`
- `audited_row_count`
- `high_severity_issue_count`
- `medium_severity_issue_count`
- `low_severity_issue_count`
- `no_issue_row_count`
- `missing_unit_issue_count`
- `missing_period_issue_count`
- `missing_source_trace_issue_count`
- `rejected_or_excluded_issue_count`
- `review_required_issue_count`
- `unnormalized_metric_issue_count`
- `human_review_pending_issue_count`
- `strict_human_review_pending_issue_count`
- `priority_fix_queue_count`
- `ready_candidate_count_after_quality_audit`

Use `null` plus `metric_limitations` for metrics that cannot be computed. Do not fake zeros.

## Reports

Executive summary must explain:

- 345A input totals
- quality issue totals
- stage-level quality distribution
- PDF-level or source-artifact-level hotspots when computable
- missing field hotspots
- evidence/source trace quality
- priority fix queue meaning
- why all formal/client/production gates remain false
- what 345C should do next

Next plan must recommend:

- `345C Metric Candidate Normalization Coverage`
- `345D Full Structured Demo Export Package`
- `345E Full Structured QA Gate`

Also state that 344G still waits for a truly human-filled 344F workbook.

## Allowed files

Only add/modify:

- `docs/codex_tasks/345B_full_extraction_quality_audit.md`
- `datefac/benchmark/full_extraction_quality_audit_345b.py`
- `datefac/benchmark/full_extraction_quality_audit_345b_report.py`
- `tools/run_full_extraction_quality_audit_345b.py`
- `tests/benchmark/test_full_extraction_quality_audit_345b.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md` only if clean or explicitly requested as ledger-only

If the ledger is dirty, do not modify it during 345B.

## Forbidden

Do not rerun MinerU, call LLM/VLM, scan the repo, add dependencies, modify production pipeline/parser/extraction/delivery/formal export logic, modify reviewed workbooks, LLM response dirs, `input/`, `temp/`, or existing `output/` content.

Do not auto commit/push/merge. Do not use `git add -A`, `git add .`, `git reset --hard`, or `git checkout --`.

Do not touch protected dirty files:

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## Validation

Run:

```powershell
python -m py_compile datefac\benchmark\full_extraction_quality_audit_345b.py datefac\benchmark\full_extraction_quality_audit_345b_report.py tools\run_full_extraction_quality_audit_345b.py tests\benchmark\test_full_extraction_quality_audit_345b.py
python -m pytest tests\benchmark\test_full_extraction_quality_audit_345b.py -q
python tools\run_full_extraction_quality_audit_345b.py --full-structured-data-inventory-345a-dir D:\_datefac\output\full_structured_data_inventory_345a --output-dir D:\_datefac\output\full_extraction_quality_audit_345b
```

Tests must verify outputs exist, decision ready, QA zero, all client/export/production gates false, audited row count matches 345A input row count, quality summary exists, priority fix queue exists, no input write-back, and missing/invalid required 345A inputs fail clearly.

## Completion report

Report files changed, py_compile, pytest, real runner, output dir, decision/QA, audited row count, quality severity distribution, major issue counts, priority fix queue count, ready candidate count after audit, final gate status, first file to open, `git status -sb`, and no-touch confirmation for existing output/temp/input/reviewed workbook/LLM response/protected dirty files.
