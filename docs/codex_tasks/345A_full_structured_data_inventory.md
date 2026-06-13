# 345A Full Structured Data Inventory

## 1. Purpose

Implement `345A Full Structured Data Inventory` for the DateFac project.

This task starts the post-344F shift from the 29-row trusted review demo chain toward full structured-data coverage analysis.

344F is now treated as a completed boundary point for the trusted-review chain:

- 344E produced the 29-row expanded demo audit snapshot.
- 344F produced the 29-row strict human review package.
- Formal client export is still not allowed.
- `client_ready = false`.
- `production_ready = false`.
- `global_strict_human_review_completed = false`.

345A does not continue 344G human-review ingestion. 344G should wait until a real human-filled 344F workbook exists and the user explicitly wants to ingest it.

345A must answer a different question:

> Across the existing table-first / MinerU-first structured-data artifacts, how much full structured data do we actually have, and how is it distributed by source, stage, status, confidence, missing fields, and downstream readiness?

This is an inventory and measurement task, not a re-extraction task. Apparently counting what already exists is now a feature. Welcome to engineering.

---

## 2. Required Preflight

Before coding, read these files if they exist locally:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345A_full_structured_data_inventory.md`

Also inspect the existing output directories that are passed through runner args. Do not scan the whole repository.

---

## 3. Inputs

The runner must accept these optional input dirs:

- `--table-first-core-financial-extraction-342f-dir`
- `--table-first-extraction-review-package-342g-dir`
- `--table-first-human-review-apply-simulation-342h-dir`
- `--review-queue-strict-human-review-package-344f-dir`
- `--output-dir`

Default real paths should be:

- `D:\_datefac\output\table_first_core_financial_extraction_342f`
- `D:\_datefac\output\table_first_extraction_review_package_342g`
- `D:\_datefac\output\table_first_human_review_apply_simulation_342h`
- `D:\_datefac\output\review_queue_strict_human_review_package_344f`
- `D:\_datefac\output\full_structured_data_inventory_345a`

Inputs may contain CSV, JSON, XLSX, or Markdown summaries. Prefer machine-readable CSV/JSON when available. If a workbook must be read, use existing project conventions and already available dependencies only. Do not add new dependencies.

If a non-critical input directory is missing, continue with a warning and record it in the manifest. If the primary 342F and 342G sources are both missing, fail clearly.

---

## 4. Output Directory

Generate all 345A artifacts under:

- `D:\_datefac\output\full_structured_data_inventory_345a`

Do not modify any existing output directory. Do not write back into 342F, 342G, 342H, or 344F outputs.

Required output files:

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

---

## 5. Inventory Scope

345A should inventory existing structured-data rows from the table-first chain and the recent trusted-review chain.

At minimum, classify available rows into these conceptual stages when the fields or artifact names make it possible:

- `RAW_TABLE_CELL`
- `LONG_FORM_CELL`
- `TRUSTED_CELL`
- `REVIEW_REQUIRED`
- `REJECTED_OR_EXCLUDED`
- `HUMAN_REVIEW_APPLIED`
- `TRUSTED_DEMO_REVIEW_ROW`
- `STRICT_HUMAN_REVIEW_PENDING_ROW`
- `UNKNOWN_STAGE`

Do not invent row-level values that are not present. Missing source fields should remain blank or null and be counted in missing-field summaries.

---

## 6. Required Row Inventory Fields

Each inventory row should include the following normalized fields where possible:

- `inventory_row_id`
- `source_artifact`
- `source_stage`
- `source_row_id`
- `pdf_id`
- `pdf_name`
- `table_id`
- `row_index`
- `column_name`
- `metric_name`
- `normalized_metric_name`
- `value_raw`
- `value_normalized`
- `unit`
- `period`
- `source_page`
- `confidence`
- `trust_status`
- `review_status`
- `human_review_status`
- `is_metric_candidate`
- `is_normalized_metric`
- `is_downstream_ready_candidate`
- `missing_required_field_count`
- `missing_required_fields`

If an upstream artifact lacks a field, keep the normalized field blank/null and include it in the missing-field summary.

---

## 7. Metrics Required In Manifest

The manifest must include at least:

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
- `trusted_demo_review_row_count`
- `strict_human_review_pending_row_count`
- `metric_candidate_row_count`
- `normalized_metric_row_count`
- `downstream_ready_candidate_count`
- `missing_unit_count`
- `missing_period_count`
- `missing_source_page_count`
- `missing_metric_name_count`
- `unknown_stage_count`

When a metric cannot be computed from available artifacts, set it to `0` only if truly zero. Otherwise use `null` and explain the reason in `metric_limitations`.

---

## 8. Downstream Readiness Rule

345A is not allowed to mark data as client-ready.

For inventory purposes only, a row may be marked `is_downstream_ready_candidate = true` if it has enough fields for later review-queue or export-candidate processing. Suggested minimum fields:

- metric name or normalized metric name
- value raw or value normalized
- unit, if available in the source domain
- period, if available in the source domain
- source page or evidence reference
- non-rejected status

This readiness is only an internal candidate flag. It must not set:

- `formal_client_export_allowed = true`
- `client_ready = true`
- `production_ready = true`

---

## 9. Reports

`full_structured_data_inventory_345a_executive_summary.md` must explain:

- What inputs were read.
- How many rows were inventoried.
- How rows distribute across trusted, review-required, rejected, human-reviewed, and strict-review-pending stages.
- Which fields are most often missing.
- Why formal client export remains false.
- What 345B should do next.

`full_structured_data_inventory_345a_next_plan.md` must recommend the next tasks:

- `345B Full Extraction Quality Audit`
- `345C Metric Candidate Normalization Coverage`
- `345D Full Structured Demo Export Package`
- `345E Full Structured QA Gate`

It must also state that 344G should only happen after the 344F review workbook has been truly filled by a human reviewer.

---

## 10. Allowed File Changes

Only add or modify:

- `docs/codex_tasks/345A_full_structured_data_inventory.md`
- `datefac/benchmark/full_structured_data_inventory_345a.py`
- `datefac/benchmark/full_structured_data_inventory_345a_report.py`
- `tools/run_full_structured_data_inventory_345a.py`
- `tests/benchmark/test_full_structured_data_inventory_345a.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md` only if it is clean or if the user explicitly requests a ledger-only append

If the milestone ledger is already dirty, do not modify it during 345A implementation. Report that it should be updated in a separate ledger-only step.

---

## 11. Forbidden Changes

Do not:

- rerun MinerU
- call VLM or LLM
- scan the whole repository
- modify production pipeline
- modify parser, extraction, or delivery logic
- modify formal client export logic
- modify existing 342F / 342G / 342H / 344F outputs
- modify reviewed workbooks
- modify LLM response directories
- modify `input/`, `temp/`, or existing `output/` content
- add dependencies
- auto commit
- auto push
- auto merge
- use `git add -A`, `git add .`, `git reset --hard`, or `git checkout --`

Protected dirty files must not be touched:

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

---

## 12. Validation Commands

Run:

```powershell
python -m py_compile datefac\benchmark\full_structured_data_inventory_345a.py datefac\benchmark\full_structured_data_inventory_345a_report.py tools\run_full_structured_data_inventory_345a.py tests\benchmark\test_full_structured_data_inventory_345a.py
```

Run:

```powershell
python -m pytest tests\benchmark\test_full_structured_data_inventory_345a.py -q
```

Run the real runner:

```powershell
python tools\run_full_structured_data_inventory_345a.py --table-first-core-financial-extraction-342f-dir D:\_datefac\output\table_first_core_financial_extraction_342f --table-first-extraction-review-package-342g-dir D:\_datefac\output\table_first_extraction_review_package_342g --table-first-human-review-apply-simulation-342h-dir D:\_datefac\output\table_first_human_review_apply_simulation_342h --review-queue-strict-human-review-package-344f-dir D:\_datefac\output\review_queue_strict_human_review_package_344f --output-dir D:\_datefac\output\full_structured_data_inventory_345a
```

Tests must verify:

- inventory artifacts are generated
- manifest decision is `FULL_STRUCTURED_DATA_INVENTORY_345A_READY`
- `qa_fail_count = 0`
- all client/export/production gates remain false
- source artifact map exists
- row inventory exists
- stage/status summaries exist
- missing-field summaries exist
- no write-back to input dirs
- missing optional input dirs are reported as warnings, not silent failures

---

## 13. Completion Report Required From Codex

After implementation, report:

1. Files changed.
2. Whether py_compile passed.
3. Whether pytest passed.
4. Whether the real runner passed.
5. Output directory.
6. Decision and QA metrics.
7. Total inventory row count.
8. Stage/status distribution.
9. Missing-field summary.
10. Downstream-ready candidate count.
11. Final gate status.
12. First file the user should open.
13. `git status -sb`.
14. Whether existing output/temp/input/reviewed workbook/LLM response/protected dirty files were not modified.
