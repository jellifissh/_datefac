# 345D Full Structured Demo Export Package

## Goal

Implement `345D Full Structured Demo Export Package`.

Current context:

- 345A built the full structured data inventory.
- 345B audited extraction quality across the full inventory.
- 345C measured baseline metric normalization coverage.
- 345C6 simulated first-batch reviewed alias application.
- 345C11 simulated first + second batch reviewed alias application and explicitly recommended stopping the alias-governance branch and returning to 345D.

345A result:

- `decision = FULL_STRUCTURED_DATA_INVENTORY_345A_READY`
- `qa_fail_count = 0`
- `total_inventory_row_count = 14788`
- `downstream_ready_candidate_count = 11575`
- all formal/client/production gates remain false

345B result:

- `decision = FULL_EXTRACTION_QUALITY_AUDIT_345B_READY`
- `qa_fail_count = 0`
- `input_inventory_row_count = 14788`
- `audited_row_count = 14788`
- `high_severity_issue_count = 7595`
- `medium_severity_issue_count = 7084`
- `no_issue_row_count = 109`
- `priority_fix_queue_count = 8817`
- `ready_candidate_count_after_quality_audit = 109`
- all formal/client/production gates remain false

345C baseline result:

- `decision = METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_READY`
- `qa_fail_count = 0`
- `metric_candidate_row_count = 14788`
- `normalized_metric_row_count = 6691`
- `unnormalized_metric_row_count = 8097`
- `normalization_coverage_ratio = 0.452461`
- all formal/client/production gates remain false

345C11 alias simulation result:

- `decision = SECOND_BATCH_ALIAS_APPLY_SIMULATION_345C11_READY`
- `qa_fail_count = 0`
- `first_batch_alias_count = 22`
- `first_batch_simulated_newly_normalized_row_count = 1813`
- `second_batch_eligible_alias_count = 15`
- `second_batch_applied_alias_key_count = 15`
- `second_batch_simulated_newly_normalized_row_count = 1613`
- `cumulative_applied_alias_key_count = 37`
- `cumulative_simulated_newly_normalized_row_count = 3426`
- `coverage_ratio_before = 0.452461`
- `coverage_ratio_after_first_batch = 0.575061`
- `coverage_ratio_after_second_batch = 0.684136`
- `ready_candidate_count_before = 6676`
- `ready_candidate_count_after_first_batch = 8146`
- `ready_candidate_count_after_second_batch = 8974`
- `ready_candidate_delta_cumulative = 2298`
- `remaining_unnormalized_raw_metric_name_count = 96`
- `remaining_unnormalized_metric_row_count = 4671`
- `remaining_ready_candidate_count = 0`
- `alias_branch_final_recommendation = STOP_ALIAS_BRANCH_AND_RETURN_TO_345D`
- `full_structured_demo_export_reasonable_after_345c11 = true`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- all formal/client/production gates remain false

345D must create a demo export package using the best available no-write-back structured rows, quality audit summaries, and reviewed alias simulation sidecar. It must not modify official normalization rules/assets or claim production/client readiness.

345D answers:

> Given the full inventory, quality audit, baseline metric coverage, and reviewed alias simulation, what structured demo export can be safely produced now, what rows are export-ready for demo purposes, what caveats remain, and what should be shown to stakeholders without pretending this is a formal client export?

This is a demo export package, not a production export. If a demo quietly becomes production, congratulations, the project has discovered the traditional enterprise software failure mode.

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Add a concise 345D entry after successful implementation and validation.

The ledger entry should include:

- task id: `345D`
- decision: `FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY`
- input packages: 345A, 345B, 345C, 345C11 dirs
- output package: 345D output dir
- demo export row count
- demo export eligible / excluded counts
- coverage after alias simulation
- remaining blind spot totals
- quality caveat counts
- gate status: all false
- no-write-back confirmation
- validation commands and results
- next recommended step

If the ledger has unrelated dirty changes, do not overwrite them blindly. Append only the 345D entry. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345D_full_structured_demo_export_package.md`

Inspect only runner input dirs and the milestone ledger. Do not scan the whole repo.

---

## Runner inputs

Support:

```powershell
--full-structured-data-inventory-345a-dir D:\_datefac\output\full_structured_data_inventory_345a
--full-extraction-quality-audit-345b-dir D:\_datefac\output\full_extraction_quality_audit_345b
--metric-candidate-normalization-coverage-345c-dir D:\_datefac\output\metric_candidate_normalization_coverage_345c
--second-batch-alias-apply-simulation-345c11-dir D:\_datefac\output\second_batch_alias_apply_simulation_345c11
--output-dir D:\_datefac\output\full_structured_demo_export_package_345d
```

Optional:

```powershell
--include-quality-limited-rows
--max-sample-rows-per-caveat 20
```

Default behavior:

- generate a demo export package from rows that are normalized after 345C11 alias simulation and have enough structured fields to be useful for demo;
- keep quality-limited, unnormalized, rejected/excluded, missing-source, missing-period, or missing-unit rows in separate caveat/exclusion artifacts;
- do not pretend quality-limited rows are client-ready.

If any required input manifest or required row file is missing, fail clearly.

---

## Inputs to read

From 345A:

- `full_structured_data_inventory_345a_manifest.json`
- full inventory rows `.json` or `.csv`
- stage distribution / source distribution outputs if available

From 345B:

- `full_extraction_quality_audit_345b_manifest.json`
- audited row outputs `.json` or `.csv`
- priority fix queue / issue summary outputs if available

From 345C:

- `metric_candidate_normalization_coverage_345c_manifest.json`
- `metric_candidate_normalization_coverage_345c_metric_candidates.json` or `.csv`
- baseline alias candidate outputs if useful

From 345C11:

- `second_batch_alias_apply_simulation_345c11_manifest.json`
- `second_batch_alias_apply_simulation_345c11_simulated_metric_rows.json` or `.csv`
- `second_batch_alias_apply_simulation_345c11_combined_alias_map.json` or `.csv`
- `second_batch_alias_apply_simulation_345c11_coverage_before_after.json` or `.csv`
- `second_batch_alias_apply_simulation_345c11_incremental_impact_summary.json` or `.csv`
- `second_batch_alias_apply_simulation_345c11_remaining_blind_spots.json` or `.csv`
- `second_batch_alias_apply_simulation_345c11_stop_or_return_to_345d_decision.json`

Validate that:

- 345A decision is `FULL_STRUCTURED_DATA_INVENTORY_345A_READY`
- 345B decision is `FULL_EXTRACTION_QUALITY_AUDIT_345B_READY`
- 345C decision is `METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_READY`
- 345C11 decision is `SECOND_BATCH_ALIAS_APPLY_SIMULATION_345C11_READY`
- 345C11 `alias_branch_final_recommendation = STOP_ALIAS_BRANCH_AND_RETURN_TO_345D`
- 345C11 `full_structured_demo_export_reasonable_after_345c11 = true`
- official rules/assets modified flags are false
- all formal/client/production gates are false

---

## Outputs

Write only under:

```text
D:\_datefac\output\full_structured_demo_export_package_345d
```

Generate:

- `full_structured_demo_export_package_345d_manifest.json`
- `full_structured_demo_export_package_345d_demo_rows.json`
- `full_structured_demo_export_package_345d_demo_rows.csv`
- `full_structured_demo_export_package_345d_demo_rows.xlsx`
- `full_structured_demo_export_package_345d_quality_limited_rows.json`
- `full_structured_demo_export_package_345d_quality_limited_rows.csv`
- `full_structured_demo_export_package_345d_excluded_rows.json`
- `full_structured_demo_export_package_345d_excluded_rows.csv`
- `full_structured_demo_export_package_345d_remaining_blind_spots.json`
- `full_structured_demo_export_package_345d_remaining_blind_spots.csv`
- `full_structured_demo_export_package_345d_alias_simulation_sidecar.json`
- `full_structured_demo_export_package_345d_alias_simulation_sidecar.csv`
- `full_structured_demo_export_package_345d_quality_caveats.json`
- `full_structured_demo_export_package_345d_quality_caveats.md`
- `full_structured_demo_export_package_345d_demo_export_summary.json`
- `full_structured_demo_export_package_345d_executive_summary.md`
- `full_structured_demo_export_package_345d_artifact_index.md`
- `full_structured_demo_export_package_345d_next_plan.md`

Do not generate formal Word/PDF client delivery unless the existing project clearly treats it as demo-only and the output file names clearly say demo. Prefer structured CSV/XLSX/JSON plus markdown summaries for 345D.

Do not write back into 345C11, 345C10, 345C9, 345C8, 345C7, 345C6, 345C5, 345C4, 345C2, 345C, 345B, 345A, official rules, alias assets, input dirs, reviewed workbooks, or upstream outputs.

---

## Demo row selection logic

Build the demo export rows conservatively.

A row can be in `demo_rows` when:

- it exists in the 345C/345C11 simulated metric row set;
- it has a usable raw metric name;
- it has a normalized metric name after baseline normalization or 345C11 alias simulation;
- it has a value field, where available;
- it has period and unit fields where available, or the missing field is explicitly flagged as a demo caveat;
- it is not rejected/excluded by inventory stage or quality-audit status;
- it does not have high-severity quality issues unless `--include-quality-limited-rows` is passed, in which case it should go to `quality_limited_rows`, not the default demo rows.

A row should go to `quality_limited_rows` when:

- it is normalized and potentially useful for demo, but has medium/high quality caveats such as missing unit, missing period, missing source trace, or quality-audit issue flags;
- it should be shown only with caveats.

A row should go to `excluded_rows` when:

- it remains unnormalized after 345C11;
- it is rejected/excluded upstream;
- it is too ambiguous or lacks core fields;
- it cannot be safely shown even as a caveated demo row.

If exact source schemas differ from the expected names, infer fields defensively and record schema limitations in the manifest and caveats. Do not silently drop important fields.

---

## Demo row schema

Each demo row should include, where available:

- `demo_export_row_id`
- `source_row_id`
- `source_pdf_name`
- `source_artifact`
- `source_page`
- `source_table_id`
- `stage`
- `raw_metric_name`
- `demo_normalized_metric_name`
- `normalization_source`
- `alias_simulation_batch`
- `value`
- `unit`
- `period`
- `currency`
- `company_name`
- `report_type`
- `quality_severity`
- `quality_issue_codes`
- `source_trace_available`
- `demo_export_eligible`
- `demo_export_caveat_level`
- `demo_export_caveats`
- `formal_client_export_allowed`
- `client_ready`
- `production_ready`

For every row in 345D output:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

`normalization_source` should indicate one of:

- `BASELINE_345C`
- `FIRST_BATCH_ALIAS_SIMULATION_345C6`
- `SECOND_BATCH_ALIAS_SIMULATION_345C11`
- `UNNORMALIZED_REMAINING_BLIND_SPOT`

`alias_simulation_batch` should indicate:

- `NONE`
- `FIRST_BATCH`
- `SECOND_BATCH`
- `NOT_APPLIED`

---

## Quality caveats

The demo export must report caveats openly.

At minimum, caveats should cover:

- remaining unnormalized rows and raw metric names
- missing unit count
- missing period count
- missing source trace/source page count
- high-severity issue count
- medium-severity issue count
- rejected/excluded count
- rows normalized only through simulation, not official rule mutation
- exact-match limitation for alias family variants
- formal export and production gates remaining false

Do not bury caveats in one vague sentence. Demo packages that hide caveats are just sales decks with better file extensions.

---

## Manifest metrics

Manifest must include:

- `decision = FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY`
- `input_stage = POST_345C11_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_345a_decision`
- `input_345b_decision`
- `input_345c_decision`
- `input_345c11_decision`
- `inventory_row_count`
- `quality_audited_row_count`
- `metric_candidate_row_count`
- `coverage_ratio_before_alias_simulation`
- `coverage_ratio_after_alias_simulation`
- `cumulative_alias_simulated_newly_normalized_row_count`
- `demo_export_row_count`
- `quality_limited_row_count`
- `excluded_row_count`
- `remaining_unnormalized_raw_metric_name_count`
- `remaining_unnormalized_metric_row_count`
- `remaining_ready_candidate_count`
- `high_severity_issue_count`
- `medium_severity_issue_count`
- `missing_unit_count`
- `missing_period_count`
- `missing_source_trace_count`
- `baseline_normalized_demo_row_count`
- `alias_simulated_demo_row_count`
- `first_batch_alias_simulated_demo_row_count`
- `second_batch_alias_simulated_demo_row_count`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `alias_simulation_sidecar_used = true`
- `formal_export_generated = false`
- `demo_export_only = true`
- `full_structured_demo_export_reasonable = true`
- `milestone_ledger_updated`

All formal/client/production gates must remain false.

---

## Reports

Executive summary must explain:

- input 345A/345B/345C/345C11 context
- why alias branch was stopped before 345D
- what 345D exported
- how many rows are demo-ready vs quality-limited vs excluded
- coverage before and after alias simulation
- how much of the demo depends on simulated alias mappings
- remaining blind spots
- quality caveats and known limitations
- why official rules/assets were not modified
- why all gates remain false
- recommended next step

Next plan must recommend one of:

- `345E Demo Export Review / QA Checklist`
- `345E Demo Narrative Report Package`
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists
- a separate official rule-update task only after explicit approval, not automatically from demo output

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/345D_full_structured_demo_export_package.md`
- `datefac/benchmark/full_structured_demo_export_package_345d.py`
- `datefac/benchmark/full_structured_demo_export_package_345d_report.py`
- `tools/run_full_structured_demo_export_package_345d.py`
- `tests/benchmark/test_full_structured_demo_export_package_345d.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

The milestone ledger update is required for this task.

---

## Forbidden

Do not:

- modify normalization rules
- modify official alias assets
- apply alias decisions to upstream data
- modify 345C11 or prior outputs
- rerun MinerU
- call LLM/VLM
- scan the repo
- add dependencies
- modify `datefac/llm/`
- modify production pipeline/parser/extraction/delivery/formal export logic
- generate formal client delivery artifacts unless clearly demo-only
- modify reviewed workbooks
- modify previous LLM response dirs
- modify `input/`, `temp/`, or existing `output/` content
- auto commit/push/merge
- use `git add -A`, `git add .`, `git reset --hard`, or `git checkout --`

Do not touch protected dirty files:

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

---

## Validation

Run:

```powershell
python -m py_compile datefac\benchmark\full_structured_demo_export_package_345d.py datefac\benchmark\full_structured_demo_export_package_345d_report.py tools\run_full_structured_demo_export_package_345d.py tests\benchmark\test_full_structured_demo_export_package_345d.py
python -m pytest tests\benchmark\test_full_structured_demo_export_package_345d.py -q
python tools\run_full_structured_demo_export_package_345d.py --full-structured-data-inventory-345a-dir D:\_datefac\output\full_structured_data_inventory_345a --full-extraction-quality-audit-345b-dir D:\_datefac\output\full_extraction_quality_audit_345b --metric-candidate-normalization-coverage-345c-dir D:\_datefac\output\metric_candidate_normalization_coverage_345c --second-batch-alias-apply-simulation-345c11-dir D:\_datefac\output\second_batch_alias_apply_simulation_345c11 --output-dir D:\_datefac\output\full_structured_demo_export_package_345d
```

Tests must verify:

- outputs exist
- decision is ready
- QA is zero for valid fixtures
- demo export rows are generated
- quality-limited and excluded rows are separated
- remaining blind spots are reported
- alias simulation sidecar is included
- formal/client/production gates remain false
- official rules/assets modified flags remain false
- formal export generated flag remains false
- demo export only flag remains true
- milestone ledger is updated with a 345D entry
- no input write-back occurs
- missing/invalid required inputs fail clearly

---

## Completion report

Report:

1. Files changed.
2. Milestone ledger update summary.
3. py_compile result.
4. pytest result.
5. real runner result.
6. output dir.
7. decision and QA metrics.
8. demo export row count.
9. quality-limited row count.
10. excluded row count.
11. coverage before / after alias simulation.
12. baseline vs alias-simulated demo row counts.
13. remaining blind spot totals.
14. quality caveat counts.
15. official rules/assets modified flags.
16. formal export generated / demo export only flags.
17. final gate status.
18. first file to open.
19. next recommended step.
20. `git status -sb`.
21. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/protected dirty files.
