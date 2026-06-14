# 345C8 Remaining Blind Spot Alias Candidate Package

## Goal

Implement `345C8 Remaining Blind Spot Alias Candidate Package`.

Current context:

- 345C measured metric normalization coverage on the full structured-data inventory.
- 345C2 live generated LLM alias suggestions for the first high-priority alias batch.
- 345C4 created a human review package.
- 345C5 ingested reviewed alias decisions.
- 345C6 simulated applying the reviewed approved aliases.
- 345C7 packaged official alias rule update candidates and concluded the current batch is not ready for official rule update or full structured demo export.

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
- all formal/client/production gates remain false

345C7 result:

- `decision = OFFICIAL_ALIAS_RULE_UPDATE_CANDIDATE_PACKAGE_345C7_READY`
- `qa_fail_count = 0`
- `candidate_row_count = 22`
- `controlled_rule_update_candidate_count = 0`
- `demo_only_sidecar_candidate_count = 3`
- `needs_additional_review_candidate_count = 19`
- `do_not_update_rule_candidate_count = 0`
- `low_risk_candidate_count = 0`
- `medium_risk_candidate_count = 3`
- `high_risk_candidate_count = 19`
- `full_structured_demo_export_reasonable = false`
- `recommended_next_scope = 345C4/345C5 additional review batch`
- all formal/client/production gates remain false

345C8 must select and package the next bounded batch of remaining high-impact blind-spot aliases from 345C6/345C7 outputs.

345C8 must not perform human review, call LLM/VLM, modify official rules/assets, apply aliases, or open gates. It only prepares a prioritized candidate package for a possible second review batch.

345C8 answers:

> Among the remaining 112 unnormalized raw metric names and 6284 unnormalized rows, which Top N blind spots are worth reviewing next, how much row impact could they have, and should the alias-governance branch continue or stop and return to 345D?

This is the branch-stop decision task. If this does not impose a limit, alias governance will become a treadmill with a folder structure.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345C8_remaining_blind_spot_alias_candidate_package.md`

Inspect only runner input dirs. Do not scan the whole repo.

---

## Runner inputs

Support:

```powershell
--reviewed-alias-apply-simulation-345c6-dir D:\_datefac\output\reviewed_alias_apply_simulation_345c6
--official-alias-rule-update-candidate-package-345c7-dir D:\_datefac\output\official_alias_rule_update_candidate_package_345c7
--output-dir D:\_datefac\output\remaining_blind_spot_alias_candidate_package_345c8
```

Also support:

```powershell
--max-blind-spot-candidates 30
--min-row-impact 10
```

Defaults:

- `max_blind_spot_candidates = 30`
- `min_row_impact = 10`

If 345C6 manifest/remaining blind spots or 345C7 manifest/remaining blind spot summary are missing, fail clearly.

---

## Inputs to read

From 345C6:

- `reviewed_alias_apply_simulation_345c6_manifest.json`
- `reviewed_alias_apply_simulation_345c6_remaining_blind_spots.json` or `.csv`
- `reviewed_alias_apply_simulation_345c6_non_applied_aliases.json` or `.csv`
- `reviewed_alias_apply_simulation_345c6_coverage_before_after.json` or `.csv`
- `reviewed_alias_apply_simulation_345c6_simulated_metric_rows.json` or `.csv` only if needed for candidate evidence

From 345C7:

- `official_alias_rule_update_candidate_package_345c7_manifest.json`
- `official_alias_rule_update_candidate_package_345c7_remaining_blind_spot_summary.json` or `.csv`
- `official_alias_rule_update_candidate_package_345c7_risk_review.json` or `.csv`
- `official_alias_rule_update_candidate_package_345c7_executive_summary.md` if available

Validate that:

- 345C6 decision is `REVIEWED_ALIAS_APPLY_SIMULATION_345C6_READY`
- 345C7 decision is `OFFICIAL_ALIAS_RULE_UPDATE_CANDIDATE_PACKAGE_345C7_READY`
- `remaining_unnormalized_metric_row_count > 0`
- all formal/client/production gates are false
- official rules/assets modified flags are false

---

## Outputs

Write only under:

```text
D:\_datefac\output\remaining_blind_spot_alias_candidate_package_345c8
```

Generate:

- `remaining_blind_spot_alias_candidate_package_345c8_manifest.json`
- `remaining_blind_spot_alias_candidate_package_345c8_selected_candidates.json`
- `remaining_blind_spot_alias_candidate_package_345c8_selected_candidates.csv`
- `remaining_blind_spot_alias_candidate_package_345c8_unselected_blind_spots.json`
- `remaining_blind_spot_alias_candidate_package_345c8_unselected_blind_spots.csv`
- `remaining_blind_spot_alias_candidate_package_345c8_candidate_impact_summary.json`
- `remaining_blind_spot_alias_candidate_package_345c8_candidate_impact_summary.csv`
- `remaining_blind_spot_alias_candidate_package_345c8_review_batch_recommendation.json`
- `remaining_blind_spot_alias_candidate_package_345c8_stop_or_continue_decision.json`
- `remaining_blind_spot_alias_candidate_package_345c8_executive_summary.md`
- `remaining_blind_spot_alias_candidate_package_345c8_artifact_index.md`
- `remaining_blind_spot_alias_candidate_package_345c8_next_plan.md`

Do not write back into 345C7, 345C6, 345C5, 345C4, 345C2, 345C, 345B, 345A, official rules, alias assets, input dirs, or upstream outputs.

---

## Candidate selection logic

Rank remaining blind spots by impact and review value.

Candidate ranking should consider:

1. remaining row count / frequency
2. number of source stages affected
3. number of PDFs/source artifacts affected
4. whether the raw metric name appears to be a concrete financial metric
5. whether the raw metric name is too generic or ambiguous
6. whether it resembles first-batch rejected or needs-context rows
7. whether it appears in high-value stages such as `TRUSTED_CELL`, `HUMAN_REVIEW_APPLIED`, or downstream-ready candidate rows when available

Do not select more than `--max-blind-spot-candidates`.

Do not select rows below `--min-row-impact` unless needed to reach a reasonable batch and explicitly mark the reason.

Do not blindly select generic names such as:

- `率`
- `变动`
- `成本` if no context is available
- empty / whitespace-only names
- names that look like units, suffixes, or table fragments

Generic candidates may be included only as `NEEDS_MORE_CONTEXT` if their impact is large and the summary clearly explains the risk.

---

## Candidate row schema

Each selected candidate row must include, where available:

- `blind_spot_candidate_id`
- `raw_metric_name`
- `remaining_row_count`
- `remaining_raw_metric_rank`
- `source_stages`
- `pdf_names`
- `source_artifacts`
- `sample_row_ids`
- `sample_evidence_excerpt`
- `candidate_priority`
- `review_recommendation`
- `candidate_reason`
- `risk_level`
- `risk_reasons`
- `estimated_max_newly_normalized_rows`
- `estimated_coverage_delta_if_resolved`
- `estimated_ready_candidate_delta_if_resolved`
- `needs_llm_adjudication`
- `needs_human_review`
- `suggested_next_review_action`
- `candidate_package_only`
- `official_rules_modified`
- `official_alias_assets_modified`

`candidate_priority` must be one of:

- `HIGH`
- `MEDIUM`
- `LOW`

`review_recommendation` must be one of:

- `INCLUDE_IN_SECOND_REVIEW_BATCH`
- `INCLUDE_AS_CONTEXT_ONLY`
- `DEFER_LOW_IMPACT`
- `EXCLUDE_TOO_GENERIC`
- `NEEDS_SOURCE_CONTEXT_BEFORE_REVIEW`

`risk_level` must be one of:

- `LOW`
- `MEDIUM`
- `HIGH`

For this task:

- `candidate_package_only = true`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`

---

## Stop-or-continue decision

345C8 must produce a stop/continue recommendation for the alias-governance branch.

Use the following decision values:

- `CONTINUE_WITH_SECOND_REVIEW_BATCH`
- `STOP_ALIAS_BRANCH_AND_RETURN_TO_345D`
- `CONTINUE_ONLY_IF_HUMAN_REVIEW_CAPACITY_EXISTS`

Suggested logic:

Continue if:

- selected candidates can plausibly cover a meaningful share of remaining unnormalized rows, and
- at least several candidates look concrete enough for human review, and
- the estimated coverage delta is meaningful.

Stop if:

- remaining blind spots are too fragmented, too generic, or too evidence-poor, or
- selected candidates would not materially improve coverage, or
- review cost outweighs expected improvement.

If the result is borderline, choose `CONTINUE_ONLY_IF_HUMAN_REVIEW_CAPACITY_EXISTS`.

---

## Manifest metrics

Manifest must include:

- `decision = REMAINING_BLIND_SPOT_ALIAS_CANDIDATE_PACKAGE_345C8_READY`
- `input_stage = POST_345C7_REMAINING_BLIND_SPOT_CANDIDATE_SELECTION`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_345c6_decision`
- `input_345c7_decision`
- `remaining_unnormalized_raw_metric_name_count`
- `remaining_unnormalized_metric_row_count`
- `max_blind_spot_candidates`
- `min_row_impact`
- `selected_candidate_count`
- `unselected_blind_spot_count`
- `selected_estimated_row_impact_total`
- `selected_estimated_coverage_delta_total`
- `selected_estimated_ready_candidate_delta_total`
- `high_priority_candidate_count`
- `medium_priority_candidate_count`
- `low_priority_candidate_count`
- `include_in_second_review_batch_count`
- `include_as_context_only_count`
- `defer_low_impact_count`
- `exclude_too_generic_count`
- `needs_source_context_before_review_count`
- `low_risk_candidate_count`
- `medium_risk_candidate_count`
- `high_risk_candidate_count`
- `alias_branch_stop_or_continue_decision`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `candidate_package_only = true`
- `full_structured_demo_export_reasonable_after_345c8`

All formal/client/production gates must remain false.

---

## Reports

Executive summary must explain:

- input 345C6/345C7 context
- why 345C8 exists after 345C7
- how many remaining blind spots exist
- how many candidates were selected
- top selected candidates and estimated impact
- risk distribution
- selected vs unselected coverage estimate
- alias branch stop/continue recommendation
- why no rules/assets were changed
- why all gates remain false
- whether to proceed to a second review batch or return to 345D

Next plan must recommend one of:

- `345C9 Remaining Blind Spot Human Review Package` if second batch is justified.
- `345D Full Structured Demo Export Package` if the alias branch should stop.
- `345D with alias-risk caveat` if demo export is useful but blind spots remain large.

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/345C8_remaining_blind_spot_alias_candidate_package.md`
- `datefac/benchmark/remaining_blind_spot_alias_candidate_package_345c8.py`
- `datefac/benchmark/remaining_blind_spot_alias_candidate_package_345c8_report.py`
- `tools/run_remaining_blind_spot_alias_candidate_package_345c8.py`
- `tests/benchmark/test_remaining_blind_spot_alias_candidate_package_345c8.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md` only if clean or explicitly requested as ledger-only

If the ledger is dirty, do not modify it during 345C8.

---

## Forbidden

Do not:

- modify normalization rules
- modify official alias assets
- apply alias decisions to upstream data
- perform human review
- call LLM/VLM
- rerun MinerU
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
python -m py_compile datefac\benchmark\remaining_blind_spot_alias_candidate_package_345c8.py datefac\benchmark\remaining_blind_spot_alias_candidate_package_345c8_report.py tools\run_remaining_blind_spot_alias_candidate_package_345c8.py tests\benchmark\test_remaining_blind_spot_alias_candidate_package_345c8.py
python -m pytest tests\benchmark\test_remaining_blind_spot_alias_candidate_package_345c8.py -q
python tools\run_remaining_blind_spot_alias_candidate_package_345c8.py --reviewed-alias-apply-simulation-345c6-dir D:\_datefac\output\reviewed_alias_apply_simulation_345c6 --official-alias-rule-update-candidate-package-345c7-dir D:\_datefac\output\official_alias_rule_update_candidate_package_345c7 --output-dir D:\_datefac\output\remaining_blind_spot_alias_candidate_package_345c8 --max-blind-spot-candidates 30 --min-row-impact 10
```

Tests must verify:

- outputs exist
- decision is ready
- QA is zero
- selected candidate count respects max limit
- candidates below min impact are handled explicitly
- generic names are not silently accepted as safe update candidates
- selected candidates include priority/risk/recommendation fields
- stop-or-continue decision is generated
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
7. remaining blind spot totals.
8. selected candidate count and max/min settings.
9. selected estimated row impact / coverage delta / ready-candidate delta.
10. priority distribution.
11. review recommendation distribution.
12. risk distribution.
13. alias branch stop-or-continue decision.
14. whether 345D is reasonable after 345C8.
15. official rules/assets modified flags.
16. candidate package only status.
17. final gate status.
18. first file to open.
19. `git status -sb`.
20. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/protected dirty files.
