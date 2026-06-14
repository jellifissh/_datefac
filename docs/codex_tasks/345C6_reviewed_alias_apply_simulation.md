# 345C6 Reviewed Alias Apply Simulation

## Goal

Implement `345C6 Reviewed Alias Apply Simulation`.

Current context:

- 345C measured metric candidate normalization coverage.
- 345C2 live generated LLM alias suggestions.
- 345C4 created a human review package for the alias suggestions.
- 345C5 ingested the reviewed alias decisions.

345C5 result:

- `decision = REVIEWED_ALIAS_DECISION_INGESTION_345C5_READY`
- `qa_fail_count = 0`
- `reviewed_row_count = 26`
- `approved_existing_mapping_count = 0`
- `approved_new_standard_count = 22`
- `rejected_alias_count = 2`
- `needs_more_context_count = 2`
- `deferred_count = 0`
- `validation_issue_count = 0`
- `apply_simulation_eligible_count = 22`
- `alias_rule_update_allowed_count = 0`
- all formal/client/production gates remain false

345C6 must simulate the impact of applying the 22 reviewed approved alias decisions to the 345C metric candidate coverage dataset.

345C6 must not modify normalization rules, official alias assets, upstream data, reviewed workbooks, or formal export gates. It only produces a no-write-back simulation of expected coverage improvement.

345C6 answers:

> If the reviewed approved aliases from 345C5 were applied virtually, how many currently unnormalized metric rows would become normalized, how would coverage change, and which rows would remain blocked?

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345C6_reviewed_alias_apply_simulation.md`

Inspect only runner input dirs. Do not scan the whole repo.

---

## Runner inputs

Support:

```powershell
--metric-candidate-normalization-coverage-345c-dir D:\_datefac\output\metric_candidate_normalization_coverage_345c
--reviewed-alias-decision-ingestion-345c5-dir D:\_datefac\output\reviewed_alias_decision_ingestion_345c5
--output-dir D:\_datefac\output\reviewed_alias_apply_simulation_345c6
```

If the 345C manifest/metric rows or the 345C5 manifest/validated approved aliases are missing, fail clearly.

---

## Inputs to read

From 345C:

- `metric_candidate_normalization_coverage_345c_manifest.json`
- `metric_candidate_normalization_coverage_345c_metric_rows.json` or `.csv`
- `metric_candidate_normalization_coverage_345c_raw_metric_summary.json` or `.csv`
- `metric_candidate_normalization_coverage_345c_alias_candidate_queue.json` or `.csv`

From 345C5:

- `reviewed_alias_decision_ingestion_345c5_manifest.json`
- `reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.json` or `.csv`
- `reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.json` or `.csv`
- `reviewed_alias_decision_ingestion_345c5_validation_issues.json`

Validate that:

- 345C5 decision is `REVIEWED_ALIAS_DECISION_INGESTION_345C5_READY`
- `apply_simulation_eligible_count > 0`
- `alias_rule_update_allowed_count = 0`
- all formal/client/production gates are false

---

## Outputs

Write only under:

```text
D:\_datefac\output\reviewed_alias_apply_simulation_345c6
```

Generate:

- `reviewed_alias_apply_simulation_345c6_manifest.json`
- `reviewed_alias_apply_simulation_345c6_simulated_metric_rows.json`
- `reviewed_alias_apply_simulation_345c6_simulated_metric_rows.csv`
- `reviewed_alias_apply_simulation_345c6_applied_alias_map.json`
- `reviewed_alias_apply_simulation_345c6_applied_alias_map.csv`
- `reviewed_alias_apply_simulation_345c6_coverage_before_after.json`
- `reviewed_alias_apply_simulation_345c6_coverage_before_after.csv`
- `reviewed_alias_apply_simulation_345c6_remaining_blind_spots.json`
- `reviewed_alias_apply_simulation_345c6_remaining_blind_spots.csv`
- `reviewed_alias_apply_simulation_345c6_non_applied_aliases.json`
- `reviewed_alias_apply_simulation_345c6_non_applied_aliases.csv`
- `reviewed_alias_apply_simulation_345c6_executive_summary.md`
- `reviewed_alias_apply_simulation_345c6_artifact_index.md`
- `reviewed_alias_apply_simulation_345c6_next_plan.md`

Do not write back into 345C5, 345C4, 345C2, 345C, 345B, 345A, official rules, alias assets, input dirs, or upstream outputs.

---

## Simulation logic

Build an in-memory alias map from 345C5 validated approved aliases:

- key: raw metric name
- value: canonical alias target
- source decision: `APPROVE_EXISTING_MAPPING` or `APPROVE_NEW_STANDARD`

Apply this map virtually to 345C metric rows only when:

- row is currently unnormalized or has empty `normalized_metric_name`
- raw metric name exactly matches a reviewed approved alias key, after safe whitespace normalization
- the approved decision passed validation

For simulated rows, set simulation fields such as:

- `simulated_normalized_metric_name`
- `simulation_action`
- `simulation_source = REVIEWED_ALIAS_345C5`
- `simulation_applied = true`
- `simulation_rule_update_required = true`
- `simulation_only_no_write_back = true`

Do not overwrite original row fields. Keep original and simulated fields side by side.

Rows that remain unnormalized should be counted in remaining blind spots.

---

## Simulated row schema

Each simulated metric row should include, where available:

- `metric_coverage_row_id`
- `inventory_row_id`
- `quality_row_id`
- `raw_metric_name`
- `normalized_metric_name`
- `simulated_normalized_metric_name`
- `normalization_status_before`
- `normalization_status_after_simulation`
- `simulation_applied`
- `simulation_action`
- `simulation_source`
- `simulation_rule_update_required`
- `simulation_only_no_write_back`
- `source_stage`
- `source_artifact`
- `pdf_name`
- `quality_severity`
- `quality_issues`
- `downstream_ready_before_normalization`
- `downstream_ready_after_alias_simulation`

---

## Coverage metrics

Calculate before/after metrics:

- `metric_candidate_row_count_before`
- `normalized_metric_row_count_before`
- `unnormalized_metric_row_count_before`
- `normalization_coverage_ratio_before`
- `simulated_alias_applied_row_count`
- `simulated_newly_normalized_row_count`
- `normalized_metric_row_count_after_simulation`
- `unnormalized_metric_row_count_after_simulation`
- `normalization_coverage_ratio_after_simulation`
- `normalization_coverage_ratio_delta`
- `ready_candidate_count_before_simulation`
- `ready_candidate_count_after_alias_simulation`
- `ready_candidate_count_delta`
- `remaining_unnormalized_raw_metric_name_count`
- `remaining_unnormalized_metric_row_count`

If a metric cannot be computed, use `null` and explain in `metric_limitations`. Do not fake zeros.

---

## Manifest metrics

Manifest must include:

- `decision = REVIEWED_ALIAS_APPLY_SIMULATION_345C6_READY`
- `input_stage = POST_345C5_REVIEWED_ALIAS_APPLY_SIMULATION`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_345c_decision`
- `input_345c5_decision`
- `validated_approved_alias_count`
- `applied_alias_key_count`
- `metric_candidate_row_count_before`
- `normalized_metric_row_count_before`
- `unnormalized_metric_row_count_before`
- `normalization_coverage_ratio_before`
- `simulated_alias_applied_row_count`
- `simulated_newly_normalized_row_count`
- `normalized_metric_row_count_after_simulation`
- `unnormalized_metric_row_count_after_simulation`
- `normalization_coverage_ratio_after_simulation`
- `normalization_coverage_ratio_delta`
- `ready_candidate_count_before_simulation`
- `ready_candidate_count_after_alias_simulation`
- `ready_candidate_count_delta`
- `remaining_unnormalized_raw_metric_name_count`
- `remaining_unnormalized_metric_row_count`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `alias_apply_simulation_only = true`

All formal/client/production gates must remain false.

---

## Reports

Executive summary must explain:

- input 345C and 345C5 context
- how many reviewed aliases were applied in simulation
- how many rows became newly normalized
- before/after coverage ratio
- ready-candidate before/after delta
- remaining blind spots
- why official rules were not modified
- why all gates remain false
- whether 345D is now reasonable or whether another alias governance step is needed

Next plan must recommend one of:

- `345D Full Structured Demo Export Package`, if simulation shows meaningful improvement and remaining blockers are acceptable
- `345C7 Official Alias Rule Update Candidate Package`, if a controlled rule update package should be prepared before 345D
- `345C4/345C5 additional review batch`, if remaining blind spots still dominate

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/345C6_reviewed_alias_apply_simulation.md`
- `datefac/benchmark/reviewed_alias_apply_simulation_345c6.py`
- `datefac/benchmark/reviewed_alias_apply_simulation_345c6_report.py`
- `tools/run_reviewed_alias_apply_simulation_345c6.py`
- `tests/benchmark/test_reviewed_alias_apply_simulation_345c6.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md` only if clean or explicitly requested as ledger-only

If the ledger is dirty, do not modify it during 345C6.

---

## Forbidden

Do not:

- modify normalization rules
- modify official alias assets
- apply alias decisions to upstream data
- rerun MinerU
- call LLM/VLM
- scan the repo
- add dependencies
- modify `datefac/llm/`
- modify production pipeline/parser/extraction/delivery/formal export logic
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
python -m py_compile datefac\benchmark\reviewed_alias_apply_simulation_345c6.py datefac\benchmark\reviewed_alias_apply_simulation_345c6_report.py tools\run_reviewed_alias_apply_simulation_345c6.py tests\benchmark\test_reviewed_alias_apply_simulation_345c6.py
python -m pytest tests\benchmark\test_reviewed_alias_apply_simulation_345c6.py -q
python tools\run_reviewed_alias_apply_simulation_345c6.py --metric-candidate-normalization-coverage-345c-dir D:\_datefac\output\metric_candidate_normalization_coverage_345c --reviewed-alias-decision-ingestion-345c5-dir D:\_datefac\output\reviewed_alias_decision_ingestion_345c5 --output-dir D:\_datefac\output\reviewed_alias_apply_simulation_345c6
```

Tests must verify:

- outputs exist
- decision is ready
- QA is zero
- alias simulation uses only validated approved aliases
- original normalized fields are not overwritten
- before/after coverage metrics are computed
- official rules/assets modified flags remain false
- all client/export/production gates remain false
- no input write-back occurs
- missing/invalid required inputs fail clearly

---

## Completion report

Report:

1. Files changed.
2. py_compile result.
3. pytest result.
4. real runner result.
5. output dir.
6. decision and QA metrics.
7. validated approved alias count.
8. simulated alias applied row count.
9. newly normalized row count.
10. before/after normalization coverage ratio and delta.
11. ready candidate before/after delta.
12. remaining blind spot summary.
13. official rules/assets modified flags.
14. final gate status.
15. first file to open.
16. `git status -sb`.
17. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/protected dirty files.
