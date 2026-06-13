# 345C Metric Candidate Normalization Coverage

## Goal

Implement `345C Metric Candidate Normalization Coverage`.

345A inventoried full structured data:

- `total_inventory_row_count = 14788`
- `downstream_ready_candidate_count = 11575`
- `normalized_metric_row_count = 6691`

345B audited extraction quality:

- `decision = FULL_EXTRACTION_QUALITY_AUDIT_345B_READY`
- `audited_row_count = 14788`
- `high_severity_issue_count = 7595`
- `medium_severity_issue_count = 7084`
- `no_issue_row_count = 109`
- `unnormalized_metric_issue_count = 8097`
- `priority_fix_queue_count = 8817`
- `ready_candidate_count_after_quality_audit = 109`
- all formal/client/production gates remain false

345C must measure metric-name normalization coverage and blind spots across the inventoried/audited rows. 345B showed that unnormalized metrics are a major blocker. 345C should quantify which raw metric names fail normalization, how often, in which stages/PDFs, and which alias/rule candidates should be considered later.

345C is analysis-only. It must not modify normalization rules, extraction outputs, reviewed workbooks, or formal export gates.

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345C_metric_candidate_normalization_coverage.md`

Inspect only runner input dirs. Do not scan the whole repo.

## Runner inputs

Support:

```powershell
--full-structured-data-inventory-345a-dir D:\_datefac\output\full_structured_data_inventory_345a
--full-extraction-quality-audit-345b-dir D:\_datefac\output\full_extraction_quality_audit_345b
--output-dir D:\_datefac\output\metric_candidate_normalization_coverage_345c
```

If required 345A or 345B manifest / row files are missing, fail clearly.

## Outputs

Write only under:

```text
D:\_datefac\output\metric_candidate_normalization_coverage_345c
```

Generate:

- `metric_candidate_normalization_coverage_345c_manifest.json`
- `metric_candidate_normalization_coverage_345c_metric_rows.json`
- `metric_candidate_normalization_coverage_345c_metric_rows.csv`
- `metric_candidate_normalization_coverage_345c_raw_metric_summary.json`
- `metric_candidate_normalization_coverage_345c_raw_metric_summary.csv`
- `metric_candidate_normalization_coverage_345c_stage_coverage_summary.json`
- `metric_candidate_normalization_coverage_345c_stage_coverage_summary.csv`
- `metric_candidate_normalization_coverage_345c_pdf_coverage_summary.json`
- `metric_candidate_normalization_coverage_345c_pdf_coverage_summary.csv`
- `metric_candidate_normalization_coverage_345c_alias_candidate_queue.json`
- `metric_candidate_normalization_coverage_345c_alias_candidate_queue.csv`
- `metric_candidate_normalization_coverage_345c_normalization_blind_spots.json`
- `metric_candidate_normalization_coverage_345c_executive_summary.md`
- `metric_candidate_normalization_coverage_345c_artifact_index.md`
- `metric_candidate_normalization_coverage_345c_next_plan.md`

Do not write back into 345A, 345B, or upstream dirs.

## Row analysis

For each metric candidate row, produce normalized analysis fields where possible:

- `metric_coverage_row_id`
- `inventory_row_id`
- `quality_row_id`
- `source_stage`
- `source_artifact`
- `pdf_id`
- `pdf_name`
- `raw_metric_name`
- `normalized_metric_name`
- `has_raw_metric_name`
- `has_normalized_metric_name`
- `is_metric_candidate`
- `is_normalized_metric`
- `quality_severity`
- `quality_issues`
- `review_status`
- `trust_status`
- `downstream_ready_before_normalization`
- `normalization_status`
- `normalization_gap_reason`
- `alias_candidate_key`
- `alias_candidate_priority`

Suggested `normalization_status` values:

- `NORMALIZED`
- `UNNORMALIZED_WITH_RAW_NAME`
- `MISSING_RAW_METRIC_NAME`
- `NON_METRIC_ROW`
- `UNKNOWN`

Suggested `normalization_gap_reason` values:

- `RAW_NAME_NOT_MAPPED`
- `RAW_NAME_TOO_NOISY`
- `POSSIBLE_TABLE_HEADER_OR_TOTAL`
- `REJECTED_OR_EXCLUDED_ROW`
- `SOURCE_STAGE_NOT_TARGETED`
- `NO_GAP`

Do not invent normalized names. 345C may propose alias candidates, but must not apply them to upstream data.

## Manifest metrics

Manifest must include:

- `decision = METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_READY`
- `input_stage = POST_345B_NORMALIZATION_COVERAGE`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_inventory_row_count`
- `input_audited_row_count`
- `metric_candidate_row_count`
- `normalized_metric_row_count`
- `unnormalized_metric_row_count`
- `normalization_coverage_ratio`
- `unique_raw_metric_name_count`
- `unique_normalized_metric_name_count`
- `unique_unnormalized_raw_metric_name_count`
- `alias_candidate_count`
- `high_priority_alias_candidate_count`
- `stage_with_lowest_coverage`
- `pdf_with_lowest_coverage`
- `ready_candidate_count_before_normalization_filter`
- `ready_candidate_count_after_normalization_filter`

Use `null` plus `metric_limitations` when a metric cannot be computed. Do not fake zeros.

## Alias candidate queue

Generate alias candidates by grouping frequent unnormalized raw metric names. Include:

- raw name
- frequency
- source stages
- PDFs/source artifacts
- sample row ids
- quality severity distribution
- suggested priority: `HIGH`, `MEDIUM`, `LOW`

Priority suggestion:

- `HIGH`: frequent, downstream-ready except normalization, and not rejected
- `MEDIUM`: frequent but review-required or quality-blocked
- `LOW`: rare or mostly rejected/excluded

No automatic rule update is allowed.

## Reports

Executive summary must explain normalization coverage, top blind spots, stage/PDF hotspots, alias candidate priorities, why gates remain false, and what 345D should do next.

Next plan must recommend:

- `345D Full Structured Demo Export Package`
- `345E Full Structured QA Gate`

It must also state that 344G still waits for a genuinely human-filled 344F workbook.

## Allowed files

Only add/modify:

- `docs/codex_tasks/345C_metric_candidate_normalization_coverage.md`
- `datefac/benchmark/metric_candidate_normalization_coverage_345c.py`
- `datefac/benchmark/metric_candidate_normalization_coverage_345c_report.py`
- `tools/run_metric_candidate_normalization_coverage_345c.py`
- `tests/benchmark/test_metric_candidate_normalization_coverage_345c.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md` only if clean or explicitly requested as ledger-only

If the ledger is dirty, do not modify it during 345C.

## Forbidden

Do not modify normalization rules, rerun MinerU, call LLM/VLM, scan the repo, add dependencies, modify production pipeline/parser/extraction/delivery/formal export logic, reviewed workbooks, LLM response dirs, `input/`, `temp/`, or existing `output/` content.

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
python -m py_compile datefac\benchmark\metric_candidate_normalization_coverage_345c.py datefac\benchmark\metric_candidate_normalization_coverage_345c_report.py tools\run_metric_candidate_normalization_coverage_345c.py tests\benchmark\test_metric_candidate_normalization_coverage_345c.py
python -m pytest tests\benchmark\test_metric_candidate_normalization_coverage_345c.py -q
python tools\run_metric_candidate_normalization_coverage_345c.py --full-structured-data-inventory-345a-dir D:\_datefac\output\full_structured_data_inventory_345a --full-extraction-quality-audit-345b-dir D:\_datefac\output\full_extraction_quality_audit_345b --output-dir D:\_datefac\output\metric_candidate_normalization_coverage_345c
```

Tests must verify outputs exist, decision ready, QA zero, all client/export/production gates false, row counts are consistent with 345A/345B, alias candidate queue exists, no input write-back, and missing/invalid required inputs fail clearly.

## Completion report

Report files changed, py_compile, pytest, real runner, output dir, decision/QA, metric candidate count, normalized/unnormalized counts, coverage ratio, unique raw/normalized counts, alias candidate count, top blind spots, final gate status, first file to open, `git status -sb`, and no-touch confirmation for existing output/temp/input/reviewed workbook/LLM response/protected dirty files.
