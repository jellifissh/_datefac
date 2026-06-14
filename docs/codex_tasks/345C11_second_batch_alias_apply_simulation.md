# 345C11 Second Batch Alias Apply Simulation

## Goal

Implement `345C11 Second Batch Alias Apply Simulation`.

Current context:

- 345C measured full metric candidate normalization coverage.
- 345C5 ingested first-batch reviewed alias decisions.
- 345C6 simulated applying first-batch reviewed approved aliases.
- 345C8 selected the bounded second batch of remaining blind-spot alias candidates.
- 345C9 generated the second-batch human review workbook/package.
- 345C10 ingested the filled 345C9 reviewed workbook and validated second-batch human decisions.

345C6 first-batch simulation result:

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
- all formal/client/production gates remain false

345C10 second-batch ingestion result:

- `decision = SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION_345C10_READY`
- `qa_fail_count = 0`
- `reviewed_row_count = 16`
- `approved_existing_mapping_count = 0`
- `approved_new_standard_count = 15`
- `rejected_too_generic_count = 0`
- `needs_source_context_count = 1`
- `deferred_count = 0`
- `missing_decision_count = 0`
- `invalid_decision_count = 0`
- `validation_issue_count = 0`
- `apply_simulation_eligible_count = 15`
- `needs_alias_family_expansion_count = 15`
- `alias_rule_update_allowed_count = 0`
- all formal/client/production gates remain false

345C11 must simulate applying the second-batch approved aliases on top of the 345C baseline and the 345C6 first-batch simulation context, then produce cumulative before/after coverage, incremental contribution, remaining blind spots, and a final alias-branch stop/return-to-345D recommendation.

345C11 must not modify official normalization rules, official alias assets, upstream data, prior outputs, reviewed workbooks, or formal export gates. It only produces a no-write-back simulation package.

345C11 answers:

> After first-batch and second-batch reviewed aliases are virtually applied, how much does metric normalization coverage improve, what blind spots remain, and should the alias-governance branch stop and return to 345D?

This is a simulation task, not a rule update. If a simulation writes production rules, that is not a feature, that is a very small disaster wearing a script filename.

---

## Required input placement

Before running 345C11, ensure 345C10 output exists:

```text
D:\_datefac\output\second_batch_reviewed_alias_decision_ingestion_345c10
```

345C11 reads 345C10 approved aliases and never edits them.

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Add a concise 345C11 entry after successful implementation and validation.

The ledger entry should include:

- task id: `345C11`
- decision: `SECOND_BATCH_ALIAS_APPLY_SIMULATION_345C11_READY`
- input packages: 345C, 345C6, 345C10 dirs
- output package: 345C11 output dir
- first-batch approved alias count
- second-batch eligible alias count
- second-batch simulated newly normalized row count
- cumulative simulated newly normalized row count
- coverage before / after first batch / after second batch
- remaining unnormalized row count
- alias branch final recommendation
- gate status: all false
- no-write-back confirmation
- validation commands and results
- next recommended step: usually `345D Full Structured Demo Export Package`

If the ledger has unrelated dirty changes, do not overwrite them blindly. Append only the 345C11 entry. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345C11_second_batch_alias_apply_simulation.md`

Inspect only runner input dirs and the milestone ledger. Do not scan the whole repo.

---

## Runner inputs

Support:

```powershell
--metric-candidate-normalization-coverage-345c-dir D:\_datefac\output\metric_candidate_normalization_coverage_345c
--reviewed-alias-apply-simulation-345c6-dir D:\_datefac\output\reviewed_alias_apply_simulation_345c6
--second-batch-reviewed-alias-decision-ingestion-345c10-dir D:\_datefac\output\second_batch_reviewed_alias_decision_ingestion_345c10
--output-dir D:\_datefac\output\second_batch_alias_apply_simulation_345c11
```

If 345C metric candidates, 345C6 first-batch simulation outputs, or 345C10 validated approved aliases are missing, fail clearly.

---

## Inputs to read

From 345C:

- `metric_candidate_normalization_coverage_345c_manifest.json`
- `metric_candidate_normalization_coverage_345c_metric_candidates.json` or `.csv`
- `metric_candidate_normalization_coverage_345c_alias_candidates.json` or `.csv` if useful

From 345C6:

- `reviewed_alias_apply_simulation_345c6_manifest.json`
- `reviewed_alias_apply_simulation_345c6_applied_alias_map.json` or `.csv`
- `reviewed_alias_apply_simulation_345c6_simulated_metric_rows.json` or `.csv`
- `reviewed_alias_apply_simulation_345c6_coverage_before_after.json` or `.csv`
- `reviewed_alias_apply_simulation_345c6_remaining_blind_spots.json` or `.csv`

From 345C10:

- `second_batch_reviewed_alias_decision_ingestion_345c10_manifest.json`
- `second_batch_reviewed_alias_decision_ingestion_345c10_validated_approved_aliases.json` or `.csv`
- `second_batch_reviewed_alias_decision_ingestion_345c10_reviewed_decisions.json` or `.csv`
- `second_batch_reviewed_alias_decision_ingestion_345c10_rejected_or_blocked_aliases.json` or `.csv`

Validate that:

- 345C decision is `METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_READY`
- 345C6 decision is `REVIEWED_ALIAS_APPLY_SIMULATION_345C6_READY`
- 345C10 decision is `SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION_345C10_READY`
- 345C10 `apply_simulation_eligible_count > 0`
- 345C6 official rules/assets modified flags are false
- 345C10 official rules/assets modified flags are false
- all formal/client/production gates are false

---

## Outputs

Write only under:

```text
D:\_datefac\output\second_batch_alias_apply_simulation_345c11
```

Generate:

- `second_batch_alias_apply_simulation_345c11_manifest.json`
- `second_batch_alias_apply_simulation_345c11_combined_alias_map.json`
- `second_batch_alias_apply_simulation_345c11_combined_alias_map.csv`
- `second_batch_alias_apply_simulation_345c11_second_batch_applied_alias_map.json`
- `second_batch_alias_apply_simulation_345c11_second_batch_applied_alias_map.csv`
- `second_batch_alias_apply_simulation_345c11_simulated_metric_rows.json`
- `second_batch_alias_apply_simulation_345c11_simulated_metric_rows.csv`
- `second_batch_alias_apply_simulation_345c11_coverage_before_after.json`
- `second_batch_alias_apply_simulation_345c11_coverage_before_after.csv`
- `second_batch_alias_apply_simulation_345c11_incremental_impact_summary.json`
- `second_batch_alias_apply_simulation_345c11_incremental_impact_summary.csv`
- `second_batch_alias_apply_simulation_345c11_remaining_blind_spots.json`
- `second_batch_alias_apply_simulation_345c11_remaining_blind_spots.csv`
- `second_batch_alias_apply_simulation_345c11_non_applied_aliases.json`
- `second_batch_alias_apply_simulation_345c11_non_applied_aliases.csv`
- `second_batch_alias_apply_simulation_345c11_stop_or_return_to_345d_decision.json`
- `second_batch_alias_apply_simulation_345c11_executive_summary.md`
- `second_batch_alias_apply_simulation_345c11_artifact_index.md`
- `second_batch_alias_apply_simulation_345c11_next_plan.md`

Do not write back into 345C10, 345C9, 345C8, 345C7, 345C6, 345C5, 345C4, 345C2, 345C, 345B, 345A, official rules, alias assets, input dirs, reviewed workbooks, or upstream outputs.

---

## Simulation logic

Build a no-write-back combined simulation.

Recommended approach:

1. Load the 345C metric candidate rows as baseline.
2. Load first-batch alias mapping/effect from 345C6.
3. Load second-batch validated approved aliases from 345C10.
4. Apply first-batch aliases virtually, then second-batch aliases virtually, without mutating input rows.
5. A row is newly normalized by second batch only if:
   - it was unnormalized after the first-batch simulation, and
   - its raw metric name matches a second-batch approved alias key, and
   - the approved alias decision passed 345C10 validation.
6. Preserve first-batch simulated normalization and avoid double-counting rows already normalized by 345C6.
7. Compute before/after metrics for baseline, after first batch, and after second batch.

Matching should be deterministic and conservative:

- normalize whitespace
- strip obvious leading/trailing punctuation
- preserve meaningful slash/case variants when necessary
- do not fuzzy-match unless existing project utilities already support a deterministic safe variant
- do not use LLM/VLM

If exact matching misses obvious alias-family variants, record that as a limitation. Do not silently invent fuzzy matches just to make the chart prettier. Charts already lie enough in human hands.

---

## Impact metrics

Compute at minimum:

- `metric_candidate_row_count`
- `baseline_normalized_metric_row_count`
- `baseline_unnormalized_metric_row_count`
- `first_batch_alias_count`
- `first_batch_simulated_newly_normalized_row_count`
- `second_batch_eligible_alias_count`
- `second_batch_applied_alias_key_count`
- `second_batch_simulated_alias_applied_row_count`
- `second_batch_simulated_newly_normalized_row_count`
- `cumulative_applied_alias_key_count`
- `cumulative_simulated_newly_normalized_row_count`
- `coverage_ratio_before`
- `coverage_ratio_after_first_batch`
- `coverage_ratio_after_second_batch`
- `coverage_delta_first_batch`
- `coverage_delta_second_batch_incremental`
- `coverage_delta_cumulative`
- `ready_candidate_count_before`
- `ready_candidate_count_after_first_batch`
- `ready_candidate_count_after_second_batch`
- `ready_candidate_delta_first_batch`
- `ready_candidate_delta_second_batch_incremental`
- `ready_candidate_delta_cumulative`
- `remaining_unnormalized_raw_metric_name_count`
- `remaining_unnormalized_metric_row_count`

If ready-candidate delta cannot be reliably recomputed from available row fields, preserve 345C6 ready-candidate metrics and set second-batch ready-candidate delta to `null` with a clear limitation note. Do not fake it. Fake precision is just cosplay with decimals.

---

## Alias branch final decision

345C11 must produce a final alias-branch recommendation.

Use:

- `STOP_ALIAS_BRANCH_AND_RETURN_TO_345D`
- `CONTINUE_ONLY_WITH_EXPLICIT_NEW_SCOPE_APPROVAL`
- `CONTINUE_WITH_ADDITIONAL_REVIEW_BATCH`

Default preference after this second batch should be:

- `STOP_ALIAS_BRANCH_AND_RETURN_TO_345D`

Choose `CONTINUE_ONLY_WITH_EXPLICIT_NEW_SCOPE_APPROVAL` only if remaining blind spots are still large but further review would be a separate explicit scope decision.

Choose `CONTINUE_WITH_ADDITIONAL_REVIEW_BATCH` only if the second batch produced exceptional improvement and the remaining blind spots still contain a very concentrated, concrete, low-risk set.

The next plan should normally recommend `345D Full Structured Demo Export Package` with explicit caveats:

- alias updates are reviewed and simulated, not official rule mutations
- official rules/assets remain unchanged
- formal client export remains false
- production ready remains false
- remaining blind spots still exist and must be reported

---

## Manifest metrics

Manifest must include:

- `decision = SECOND_BATCH_ALIAS_APPLY_SIMULATION_345C11_READY`
- `input_stage = POST_345C10_SECOND_BATCH_ALIAS_APPLY_SIMULATION`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_345c_decision`
- `input_345c6_decision`
- `input_345c10_decision`
- `metric_candidate_row_count`
- `baseline_normalized_metric_row_count`
- `baseline_unnormalized_metric_row_count`
- `first_batch_alias_count`
- `first_batch_simulated_newly_normalized_row_count`
- `second_batch_eligible_alias_count`
- `second_batch_applied_alias_key_count`
- `second_batch_simulated_alias_applied_row_count`
- `second_batch_simulated_newly_normalized_row_count`
- `cumulative_applied_alias_key_count`
- `cumulative_simulated_newly_normalized_row_count`
- `coverage_ratio_before`
- `coverage_ratio_after_first_batch`
- `coverage_ratio_after_second_batch`
- `coverage_delta_first_batch`
- `coverage_delta_second_batch_incremental`
- `coverage_delta_cumulative`
- `ready_candidate_count_before`
- `ready_candidate_count_after_first_batch`
- `ready_candidate_count_after_second_batch`
- `ready_candidate_delta_first_batch`
- `ready_candidate_delta_second_batch_incremental`
- `ready_candidate_delta_cumulative`
- `remaining_unnormalized_raw_metric_name_count`
- `remaining_unnormalized_metric_row_count`
- `non_applied_second_batch_alias_count`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `alias_apply_simulation_only = true`
- `candidate_package_only = true`
- `alias_branch_final_recommendation`
- `full_structured_demo_export_reasonable_after_345c11`
- `milestone_ledger_updated`

All formal/client/production gates must remain false.

---

## Reports

Executive summary must explain:

- input 345C baseline, 345C6 first-batch simulation, and 345C10 second-batch approved aliases
- first-batch impact
- second-batch incremental impact
- cumulative coverage and ready-candidate effect
- top second-batch aliases by row impact
- remaining blind spots
- matching limitations such as exact-match-only alias family gaps
- why official rules/assets were not modified
- why all gates remain false
- final recommendation on stopping alias governance and returning to 345D

Next plan must recommend one of:

- `345D Full Structured Demo Export Package` if the alias branch should stop.
- `345D with alias-risk caveat` if demo export is useful but blind spots remain large.
- a separate explicitly approved new alias-governance scope only if continuing is strongly justified.

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/345C11_second_batch_alias_apply_simulation.md`
- `datefac/benchmark/second_batch_alias_apply_simulation_345c11.py`
- `datefac/benchmark/second_batch_alias_apply_simulation_345c11_report.py`
- `tools/run_second_batch_alias_apply_simulation_345c11.py`
- `tests/benchmark/test_second_batch_alias_apply_simulation_345c11.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

The milestone ledger update is required for this task.

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
python -m py_compile datefac\benchmark\second_batch_alias_apply_simulation_345c11.py datefac\benchmark\second_batch_alias_apply_simulation_345c11_report.py tools\run_second_batch_alias_apply_simulation_345c11.py tests\benchmark\test_second_batch_alias_apply_simulation_345c11.py
python -m pytest tests\benchmark\test_second_batch_alias_apply_simulation_345c11.py -q
python tools\run_second_batch_alias_apply_simulation_345c11.py --metric-candidate-normalization-coverage-345c-dir D:\_datefac\output\metric_candidate_normalization_coverage_345c --reviewed-alias-apply-simulation-345c6-dir D:\_datefac\output\reviewed_alias_apply_simulation_345c6 --second-batch-reviewed-alias-decision-ingestion-345c10-dir D:\_datefac\output\second_batch_reviewed_alias_decision_ingestion_345c10 --output-dir D:\_datefac\output\second_batch_alias_apply_simulation_345c11
```

Tests must verify:

- outputs exist
- decision is ready
- QA is zero for valid fixtures
- first-batch 345C6 metrics are preserved
- second-batch eligible aliases are loaded from 345C10
- second-batch simulation does not double-count first-batch-normalized rows
- cumulative coverage is computed consistently
- remaining blind spots are generated
- alias branch final recommendation is generated
- official rules/assets modified flags remain false
- alias apply simulation only flag remains true
- all client/export/production gates remain false
- milestone ledger is updated with a 345C11 entry
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
8. first-batch alias count / impact.
9. second-batch eligible alias count / applied alias count / impact.
10. cumulative alias count / cumulative newly normalized rows.
11. coverage before / after first batch / after second batch.
12. ready-candidate before / after first batch / after second batch, or limitation note.
13. remaining blind spot totals.
14. alias branch final recommendation.
15. whether 345D is reasonable after 345C11.
16. official rules/assets modified flags.
17. final gate status.
18. first file to open.
19. next recommended step.
20. `git status -sb`.
21. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/protected dirty files.
