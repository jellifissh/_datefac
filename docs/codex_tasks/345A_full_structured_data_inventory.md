# 345A Full Structured Data Inventory

## Goal

Implement `345A Full Structured Data Inventory`.

Current boundary:

- 344E generated 29-row expanded demo audit snapshot.
- 344F generated 29-row strict human review package.
- 344F is a pause point for trusted-review demo work.
- 344G should wait until the 344F workbook is genuinely human-filled.
- `formal_client_export_allowed = false`.
- `client_ready = false`.
- `production_ready = false`.
- `global_strict_human_review_completed = false`.

345A starts the full structured-data branch. It inventories existing MinerU-first / table-first artifacts and reports coverage, stage/status distribution, missing fields, and downstream-readiness candidates.

345A is not extraction, not LLM/VLM work, not formal export, and not production hardening.

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345A_full_structured_data_inventory.md`

Inspect only runner input dirs. Do not scan the whole repo.

## Runner inputs

Support:

```powershell
--table-first-core-financial-extraction-342f-dir D:\_datefac\output\table_first_core_financial_extraction_342f
--table-first-extraction-review-package-342g-dir D:\_datefac\output\table_first_extraction_review_package_342g
--table-first-human-review-apply-simulation-342h-dir D:\_datefac\output\table_first_human_review_apply_simulation_342h
--review-queue-strict-human-review-package-344f-dir D:\_datefac\output\review_queue_strict_human_review_package_344f
--output-dir D:\_datefac\output\full_structured_data_inventory_345a
```

Prefer CSV/JSON. Read XLSX only using already available project dependencies. Missing optional input dirs become warnings. If both 342F and 342G are missing, fail clearly.

## Outputs

Write only under:

```text
D:\_datefac\output\full_structured_data_inventory_345a
```

Generate:

- `full_structured_data_inventory_345a_manifest.json`
- `full_structured_data_inventory_345a_source_artifact_map.json`
- `full_structured_data_inventory_345a_row_inventory.json`
- `full_structured_data_inventory_345a_row_inventory.csv`
- `full_structured_data_inventory_345a_stage_status_summary.json`
- `full_structured_data_inventory_345a_stage_status_summary.csv`
- `full_structured_data_inventory_345a_missing_field_summary.json`
- `full_structured_data_inventory_345a_missing_field_summary.csv`
- `full_structured_data_inventory_345a_downstream_readiness_summary.json`
- `full_structured_data_inventory_345a_executive_summary.md`
- `full_structured_data_inventory_345a_artifact_index.md`
- `full_structured_data_inventory_345a_next_plan.md`

Do not write back into any input dir.

## Classification

Classify rows when possible as:

- `RAW_TABLE_CELL`
- `LONG_FORM_CELL`
- `TRUSTED_CELL`
- `REVIEW_REQUIRED`
- `REJECTED_OR_EXCLUDED`
- `HUMAN_REVIEW_APPLIED`
- `STRICT_HUMAN_REVIEW_PENDING_ROW`
- `UNKNOWN_STAGE`

Do not invent unavailable values. Keep unavailable fields blank/null and count them.

Normalized row fields should include where possible:

- `inventory_row_id`, `source_artifact`, `source_stage`, `source_row_id`
- `pdf_id`, `pdf_name`, `table_id`, `row_index`, `column_name`
- `metric_name`, `normalized_metric_name`
- `value_raw`, `value_normalized`, `unit`, `period`, `source_page`
- `confidence`, `trust_status`, `review_status`, `human_review_status`
- `is_metric_candidate`, `is_normalized_metric`, `is_downstream_ready_candidate`
- `missing_required_field_count`, `missing_required_fields`

## Manifest metrics

Manifest must include:

- `decision = FULL_STRUCTURED_DATA_INVENTORY_345A_READY`
- `input_stage = POST_344F_FULL_STRUCTURED_INVENTORY`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `total_input_artifact_count`
- `readable_input_artifact_count`
- `missing_input_artifact_count`
- `total_inventory_row_count`
- `long_form_cell_count`
- `trusted_cell_count`
- `review_required_count`
- `rejected_or_excluded_count`
- `human_review_applied_count`
- `strict_human_review_pending_row_count`
- `metric_candidate_row_count`
- `normalized_metric_row_count`
- `downstream_ready_candidate_count`
- `missing_unit_count`
- `missing_period_count`
- `missing_source_page_count`
- `missing_metric_name_count`
- `unknown_stage_count`

Use `null` plus `metric_limitations` when a metric cannot be computed. Do not fake zeros.

## Downstream readiness

For inventory only, `is_downstream_ready_candidate = true` means the row has metric name, value, non-rejected status, and at least one source trace field such as page/evidence.

This never means client-ready.

## Reports

Executive summary must explain inputs, total rows, stage/status distribution, missing-field hotspots, why export remains false, and what 345B should do next.

Next plan must recommend:

- `345B Full Extraction Quality Audit`
- `345C Metric Candidate Normalization Coverage`
- `345D Full Structured Demo Export Package`
- `345E Full Structured QA Gate`

Also state that 344G waits for a truly filled 344F workbook.

## Allowed files

Only add/modify:

- `docs/codex_tasks/345A_full_structured_data_inventory.md`
- `datefac/benchmark/full_structured_data_inventory_345a.py`
- `datefac/benchmark/full_structured_data_inventory_345a_report.py`
- `tools/run_full_structured_data_inventory_345a.py`
- `tests/benchmark/test_full_structured_data_inventory_345a.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md` only if clean or explicitly requested as ledger-only

If the ledger is dirty, do not modify it during 345A.

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
python -m py_compile datefac\benchmark\full_structured_data_inventory_345a.py datefac\benchmark\full_structured_data_inventory_345a_report.py tools\run_full_structured_data_inventory_345a.py tests\benchmark\test_full_structured_data_inventory_345a.py
python -m pytest tests\benchmark\test_full_structured_data_inventory_345a.py -q
python tools\run_full_structured_data_inventory_345a.py --table-first-core-financial-extraction-342f-dir D:\_datefac\output\table_first_core_financial_extraction_342f --table-first-extraction-review-package-342g-dir D:\_datefac\output\table_first_extraction_review_package_342g --table-first-human-review-apply-simulation-342h-dir D:\_datefac\output\table_first_human_review_apply_simulation_342h --review-queue-strict-human-review-package-344f-dir D:\_datefac\output\review_queue_strict_human_review_package_344f --output-dir D:\_datefac\output\full_structured_data_inventory_345a
```

Tests must verify outputs exist, decision ready, QA zero, all client/export/production gates false, no input write-back, and optional missing inputs become warnings.

## Completion report

Report files changed, py_compile, pytest, real runner, output dir, decision/QA, total inventory rows, stage/status distribution, missing-field summary, downstream-ready candidate count, final gate status, first file to open, `git status -sb`, and no-touch confirmation for existing output/temp/input/reviewed workbook/LLM response/protected dirty files.
