# 345C7 Official Alias Rule Update Candidate Package

## Goal

Implement `345C7 Official Alias Rule Update Candidate Package`.

Current context:

- 345C measured full metric candidate normalization coverage.
- 345C2 live generated LLM alias suggestions.
- 345C4 turned suggestions into a human review package.
- 345C5 ingested the reviewed human decisions.
- 345C6 simulated the impact of applying reviewed approved aliases without writing back.

345C6 result:

- `decision = REVIEWED_ALIAS_APPLY_SIMULATION_345C6_READY`
- `qa_fail_count = 0`
- `validated_approved_alias_count = 22`
- `applied_alias_key_count = 22`
- `simulated_alias_applied_row_count = 1813`
- `simulated_newly_normalized_row_count = 1813`
- `normalization_coverage_ratio_before = 0.452461`
- `normalization_coverage_ratio_after_simulation = 0.575061`
- `normalization_coverage_ratio_delta = 0.1226`
- `ready_candidate_count_before_simulation = 6676`
- `ready_candidate_count_after_alias_simulation = 8146`
- `ready_candidate_count_delta = 1470`
- `remaining_unnormalized_raw_metric_name_count = 112`
- `remaining_unnormalized_metric_row_count = 6284`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `alias_apply_simulation_only = true`
- all formal/client/production gates remain false

345C7 must convert the reviewed approved alias set and its measured 345C6 impact into a controlled official rule-update candidate package.

345C7 must not modify official normalization rules, official alias assets, upstream data, reviewed workbooks, or formal export gates. It only prepares a reviewable candidate package for a later explicit rule update or demo export decision.

345C7 answers:

> Which reviewed aliases are strong candidates for official alias-rule update, what impact did each candidate have in simulation, what risks remain, and is it reasonable to proceed to a controlled rule update or 345D demo export?

This is a candidate packaging task, not a rule mutation task. The difference matters, because software projects have enough tiny grenades already.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345C7_official_alias_rule_update_candidate_package.md`

Inspect only runner input dirs. Do not scan the whole repo.

---

## Runner inputs

Support:

```powershell
--reviewed-alias-decision-ingestion-345c5-dir D:\_datefac\output\reviewed_alias_decision_ingestion_345c5
--reviewed-alias-apply-simulation-345c6-dir D:\_datefac\output\reviewed_alias_apply_simulation_345c6
--output-dir D:\_datefac\output\official_alias_rule_update_candidate_package_345c7
```

If 345C5 manifest/validated approved aliases or 345C6 manifest/applied alias map/coverage files are missing, fail clearly.

---

## Inputs to read

From 345C5:

- `reviewed_alias_decision_ingestion_345c5_manifest.json`
- `reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.json` or `.csv`
- `reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.json` or `.csv`
- `reviewed_alias_decision_ingestion_345c5_decision_summary.json`

From 345C6:

- `reviewed_alias_apply_simulation_345c6_manifest.json`
- `reviewed_alias_apply_simulation_345c6_applied_alias_map.json` or `.csv`
- `reviewed_alias_apply_simulation_345c6_coverage_before_after.json` or `.csv`
- `reviewed_alias_apply_simulation_345c6_remaining_blind_spots.json` or `.csv`
- `reviewed_alias_apply_simulation_345c6_non_applied_aliases.json` or `.csv`
- `reviewed_alias_apply_simulation_345c6_simulated_metric_rows.json` or `.csv` only if needed for per-alias impact calculation

Validate that:

- 345C5 decision is `REVIEWED_ALIAS_DECISION_INGESTION_345C5_READY`
- 345C6 decision is `REVIEWED_ALIAS_APPLY_SIMULATION_345C6_READY`
- `validated_approved_alias_count > 0`
- `simulated_newly_normalized_row_count > 0`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- all formal/client/production gates are false

---

## Outputs

Write only under:

```text
D:\_datefac\output\official_alias_rule_update_candidate_package_345c7
```

Generate:

- `official_alias_rule_update_candidate_package_345c7_manifest.json`
- `official_alias_rule_update_candidate_package_345c7_alias_rule_candidates.json`
- `official_alias_rule_update_candidate_package_345c7_alias_rule_candidates.csv`
- `official_alias_rule_update_candidate_package_345c7_impact_summary.json`
- `official_alias_rule_update_candidate_package_345c7_impact_summary.csv`
- `official_alias_rule_update_candidate_package_345c7_risk_review.json`
- `official_alias_rule_update_candidate_package_345c7_risk_review.csv`
- `official_alias_rule_update_candidate_package_345c7_remaining_blind_spot_summary.json`
- `official_alias_rule_update_candidate_package_345c7_remaining_blind_spot_summary.csv`
- `official_alias_rule_update_candidate_package_345c7_rule_update_checklist.md`
- `official_alias_rule_update_candidate_package_345c7_executive_summary.md`
- `official_alias_rule_update_candidate_package_345c7_artifact_index.md`
- `official_alias_rule_update_candidate_package_345c7_next_plan.md`

Do not write back into 345C6, 345C5, 345C4, 345C2, 345C, 345B, 345A, official rules, alias assets, input dirs, or upstream outputs.

---

## Candidate row schema

Each candidate row must include, where available:

- `alias_rule_candidate_id`
- `raw_metric_name`
- `proposed_standard_metric`
- `human_alias_review_decision`
- `alias_reviewer`
- `alias_reviewed_at`
- `alias_review_notes`
- `source_345c5_alias_review_row_id`
- `source_345c5_alias_adjudication_id`
- `source_345c6_applied_alias_key`
- `simulation_applied_row_count`
- `simulation_newly_normalized_row_count`
- `coverage_delta_contribution`
- `ready_candidate_delta_contribution`
- `source_stages`
- `pdf_names`
- `sample_row_ids`
- `rule_update_risk_level`
- `risk_reasons`
- `rule_update_recommendation`
- `requires_manual_rule_commit`
- `official_rules_modified`
- `official_alias_assets_modified`
- `candidate_package_only`

`rule_update_risk_level` must be one of:

- `LOW`
- `MEDIUM`
- `HIGH`

`rule_update_recommendation` must be one of:

- `READY_FOR_CONTROLLED_RULE_UPDATE`
- `READY_FOR_DEMO_ONLY_SIDECAR_USE`
- `NEEDS_ADDITIONAL_REVIEW`
- `DO_NOT_UPDATE_RULE`

For this task:

- `requires_manual_rule_commit = true` for candidates recommended for controlled rule update.
- `official_rules_modified = false` for every row.
- `official_alias_assets_modified = false` for every row.
- `candidate_package_only = true` for every row.

---

## Impact logic

Use 345C6 simulated rows or applied alias map to compute per-alias impact.

At minimum, compute:

- count of rows simulated by each alias
- count of newly normalized rows by each alias
- contribution to total simulated newly normalized rows
- contribution to ready-candidate delta if row-level fields allow it

If ready-candidate delta cannot be attributed per alias reliably, set per-alias `ready_candidate_delta_contribution = null` and explain the limitation in `impact_metric_limitations`. Do not fake per-alias numbers.

Coverage delta contribution may be estimated as:

```text
simulation_newly_normalized_row_count_for_alias / metric_candidate_row_count_before
```

Record this as a simulation-derived estimate, not a formal production metric.

---

## Risk rules

Assign risk conservatively.

`HIGH` risk if:

- raw metric name is too generic, ambiguous, or looks like a unit/ratio suffix rather than a stable metric
- approved standard metric is too broad
- source evidence is weak or missing
- the row came from a validation edge case
- the alias has low row impact but broad semantic ambiguity

`MEDIUM` risk if:

- the alias is a plausible metric but may need family-level alias expansion
- there are remaining blind-spot variants with similar names
- the candidate proposes a new standard metric not yet represented in official rules

`LOW` risk if:

- raw metric name is a clear financial metric
- approved standard metric is specific
- simulated impact is meaningful
- no validation issues exist
- evidence fields are stable enough for a controlled rule update package

Do not mark every row LOW by default. Human optimism is not a validation framework.

---

## Manifest metrics

Manifest must include:

- `decision = OFFICIAL_ALIAS_RULE_UPDATE_CANDIDATE_PACKAGE_345C7_READY`
- `input_stage = POST_345C6_OFFICIAL_ALIAS_RULE_UPDATE_CANDIDATE_PACKAGE`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_345c5_decision`
- `input_345c6_decision`
- `validated_approved_alias_count`
- `candidate_row_count`
- `controlled_rule_update_candidate_count`
- `demo_only_sidecar_candidate_count`
- `needs_additional_review_candidate_count`
- `do_not_update_rule_candidate_count`
- `low_risk_candidate_count`
- `medium_risk_candidate_count`
- `high_risk_candidate_count`
- `simulated_alias_applied_row_count`
- `simulated_newly_normalized_row_count`
- `normalization_coverage_ratio_before`
- `normalization_coverage_ratio_after_simulation`
- `normalization_coverage_ratio_delta`
- `ready_candidate_count_before_simulation`
- `ready_candidate_count_after_alias_simulation`
- `ready_candidate_count_delta`
- `remaining_unnormalized_raw_metric_name_count`
- `remaining_unnormalized_metric_row_count`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `candidate_package_only = true`
- `controlled_rule_update_ready`
- `full_structured_demo_export_reasonable`

All formal/client/production gates must remain false.

---

## Reports

Executive summary must explain:

- input 345C5 and 345C6 context
- how many candidate aliases were packaged
- measured simulation impact from 345C6
- before/after coverage ratio and ready-candidate delta
- top impact aliases
- risk distribution
- remaining blind spots
- why official rules/assets were not modified
- why all formal/client/production gates remain false
- whether 345D is reasonable now or whether a controlled rule update task should happen first

Rule update checklist must explain:

1. This package does not modify official rules.
2. Only candidates marked `READY_FOR_CONTROLLED_RULE_UPDATE` may be considered for a later explicit rule update.
3. Official alias assets should be changed only in a separate reviewed task.
4. Any future official rule update must include before/after tests and a rollback plan.
5. Demo export may use this candidate package only as a documented sidecar unless a rule update is explicitly applied.

Next plan must recommend one of:

- `345C8 Controlled Official Alias Rule Update` if candidate quality and impact justify updating rules before 345D.
- `345D Full Structured Demo Export Package` if using reviewed alias sidecar as demo-only evidence is acceptable.
- `345C4/345C5 additional review batch` if remaining blind spots still dominate and 345D would be too weak.

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/345C7_official_alias_rule_update_candidate_package.md`
- `datefac/benchmark/official_alias_rule_update_candidate_package_345c7.py`
- `datefac/benchmark/official_alias_rule_update_candidate_package_345c7_report.py`
- `tools/run_official_alias_rule_update_candidate_package_345c7.py`
- `tests/benchmark/test_official_alias_rule_update_candidate_package_345c7.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md` only if clean or explicitly requested as ledger-only

If the ledger is dirty, do not modify it during 345C7.

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
python -m py_compile datefac\benchmark\official_alias_rule_update_candidate_package_345c7.py datefac\benchmark\official_alias_rule_update_candidate_package_345c7_report.py tools\run_official_alias_rule_update_candidate_package_345c7.py tests\benchmark\test_official_alias_rule_update_candidate_package_345c7.py
python -m pytest tests\benchmark\test_official_alias_rule_update_candidate_package_345c7.py -q
python tools\run_official_alias_rule_update_candidate_package_345c7.py --reviewed-alias-decision-ingestion-345c5-dir D:\_datefac\output\reviewed_alias_decision_ingestion_345c5 --reviewed-alias-apply-simulation-345c6-dir D:\_datefac\output\reviewed_alias_apply_simulation_345c6 --output-dir D:\_datefac\output\official_alias_rule_update_candidate_package_345c7
```

Tests must verify:

- outputs exist
- decision is ready
- QA is zero
- candidate count matches validated approved aliases when expected
- 345C6 impact metrics are preserved
- candidate rows include risk and recommendation fields
- official rules/assets modified flags remain false
- candidate package only flag remains true
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
7. candidate row count.
8. rule update recommendation distribution.
9. risk distribution.
10. preserved 345C6 coverage and ready-candidate impact.
11. remaining blind spot summary.
12. official rules/assets modified flags.
13. candidate package only status.
14. final gate status.
15. first file to open.
16. `git status -sb`.
17. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/protected dirty files.
