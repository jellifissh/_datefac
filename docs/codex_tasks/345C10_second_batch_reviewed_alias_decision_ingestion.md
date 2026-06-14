# 345C10 Second Batch Reviewed Alias Decision Ingestion

## Goal

Implement `345C10 Second Batch Reviewed Alias Decision Ingestion`.

Current context:

- 345C8 selected the bounded second batch of remaining blind-spot alias candidates.
- 345C9 generated the human review workbook/package for that second batch.
- The 345C9 reviewed workbook has now been filled.

345C9 package result:

- `decision = REMAINING_BLIND_SPOT_HUMAN_REVIEW_PACKAGE_345C9_READY`
- `qa_fail_count = 0`
- `review_required_row_count = 16`
- `context_only_row_count = 3`
- `blocked_or_too_generic_row_count = 11`
- `generated_review_pending_count = 16`
- `generated_approved_count = 0`
- `alias_rule_update_allowed_count = 0`
- all formal/client/production gates remain false

Expected reviewed workbook result for this run:

- `reviewed_row_count = 16`
- `APPROVE_NEW_STANDARD = 15`
- `NEEDS_SOURCE_CONTEXT = 1`
- `APPROVE_EXISTING_MAPPING = 0`
- `REJECT_TOO_GENERIC = 0`
- `DEFER = 0`
- `alias_rule_update_allowed_count = 0`

345C10 must ingest the reviewed 345C9 workbook, validate human decisions, and generate a no-write-back second-batch reviewed-alias decision package.

345C10 must not apply alias decisions to upstream data, modify normalization rules, modify official alias assets, modify the reviewed workbook, call LLM/VLM, or open any formal/client/production gate.

345C10 answers:

> Which second-batch remaining blind-spot candidates were approved, rejected, deferred, or marked as needing source context by the human reviewer, and which approved rows are eligible for second-batch apply simulation?

This is ingestion and validation, not rule mutation. Excel being filled does not mean production assets get to wake up and mutate themselves like a horror movie.

---

## Required reviewed workbook placement

Before running 345C10, copy the reviewed workbook to the 345C9 output directory:

```text
D:\_datefac\output\remaining_blind_spot_human_review_package_345c9\remaining_blind_spot_human_review_package_345c9_reviewed.xlsx
```

345C10 must never edit this reviewed workbook. It only reads it.

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Add a concise 345C10 entry after successful implementation and validation.

The ledger entry should include:

- task id: `345C10`
- decision: `SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION_345C10_READY`
- input package: 345C9 output dir
- reviewed workbook path
- output package: 345C10 output dir
- reviewed row count
- decision distribution
- validation issue count
- apply simulation eligible count
- gate status: all false
- no-write-back confirmation
- validation commands and results
- next recommended step: `345C11 Second Batch Alias Apply Simulation`

If the ledger has unrelated dirty changes, do not overwrite them blindly. Append only the 345C10 entry. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345C10_second_batch_reviewed_alias_decision_ingestion.md`

Inspect only runner input dirs and the milestone ledger. Do not scan the whole repo.

---

## Runner inputs

Support:

```powershell
--remaining-blind-spot-human-review-package-345c9-dir D:\_datefac\output\remaining_blind_spot_human_review_package_345c9
--reviewed-blind-spot-workbook D:\_datefac\output\remaining_blind_spot_human_review_package_345c9\remaining_blind_spot_human_review_package_345c9_reviewed.xlsx
--output-dir D:\_datefac\output\second_batch_reviewed_alias_decision_ingestion_345c10
```

If the 345C9 manifest, original review rows, or reviewed workbook are missing, fail clearly.

---

## Inputs to read

From 345C9 package dir:

- `remaining_blind_spot_human_review_package_345c9_manifest.json`
- `remaining_blind_spot_human_review_package_345c9_review_rows.json` or `.csv`
- `remaining_blind_spot_human_review_package_345c9_context_only_rows.json` or `.csv`
- `remaining_blind_spot_human_review_package_345c9_blocked_rows.json` or `.csv`

Read reviewed workbook:

- `remaining_blind_spot_human_review_package_345c9_reviewed.xlsx`

The reviewed workbook should include review fields:

- `human_blind_spot_review_decision`
- `approved_standard_metric`
- `approved_new_standard_metric`
- `needs_alias_family_expansion`
- `needs_source_context`
- `reviewer`
- `reviewed_at`
- `review_notes`
- `alias_rule_update_allowed`

Do not trust row order alone. Prefer stable ids such as `blind_spot_review_row_id` and `source_345c8_blind_spot_candidate_id` when matching original rows to reviewed rows. If ids are missing or duplicated, fail clearly.

Only the `review_required` rows are actionable for ingestion. Context-only and blocked rows may be copied into reports as reference, but they must not become apply-simulation eligible.

---

## Outputs

Write only under:

```text
D:\_datefac\output\second_batch_reviewed_alias_decision_ingestion_345c10
```

Generate:

- `second_batch_reviewed_alias_decision_ingestion_345c10_manifest.json`
- `second_batch_reviewed_alias_decision_ingestion_345c10_reviewed_decisions.json`
- `second_batch_reviewed_alias_decision_ingestion_345c10_reviewed_decisions.csv`
- `second_batch_reviewed_alias_decision_ingestion_345c10_validated_approved_aliases.json`
- `second_batch_reviewed_alias_decision_ingestion_345c10_validated_approved_aliases.csv`
- `second_batch_reviewed_alias_decision_ingestion_345c10_rejected_or_blocked_aliases.json`
- `second_batch_reviewed_alias_decision_ingestion_345c10_rejected_or_blocked_aliases.csv`
- `second_batch_reviewed_alias_decision_ingestion_345c10_validation_issues.json`
- `second_batch_reviewed_alias_decision_ingestion_345c10_decision_summary.json`
- `second_batch_reviewed_alias_decision_ingestion_345c10_executive_summary.md`
- `second_batch_reviewed_alias_decision_ingestion_345c10_artifact_index.md`
- `second_batch_reviewed_alias_decision_ingestion_345c10_next_plan.md`

Do not write back into 345C9, 345C8, 345C7, 345C6, 345C5, 345C4, 345C2, 345C, 345B, 345A, official rules, alias assets, input dirs, or upstream outputs.

---

## Decision validation rules

Allowed human decisions:

- `APPROVE_EXISTING_MAPPING`
- `APPROVE_NEW_STANDARD`
- `REJECT_TOO_GENERIC`
- `NEEDS_SOURCE_CONTEXT`
- `DEFER`

Validation requirements:

- `APPROVE_EXISTING_MAPPING` requires non-empty `approved_standard_metric` and empty or consistent `approved_new_standard_metric`.
- `APPROVE_NEW_STANDARD` requires non-empty `approved_new_standard_metric` and should include review notes.
- `REJECT_TOO_GENERIC` should include review notes.
- `NEEDS_SOURCE_CONTEXT` should include review notes describing missing source context.
- `DEFER` should include review notes if possible.
- Missing or unknown decision must be counted as validation issue.
- Duplicate reviewed row ids must fail QA.
- Reviewed actionable row count must match the original 345C9 `review_required_row_count` unless explicitly recorded as fatal QA failure.
- `alias_rule_update_allowed` must be forced false in output, even if the workbook contains true.

The generated ingestion package may mark rows as apply-simulation eligible only when:

- decision is `APPROVE_EXISTING_MAPPING` or `APPROVE_NEW_STANDARD`
- required approved metric field is present
- validation passed

Even eligible rows must not update official rules in 345C10.

---

## Output row schema

Each reviewed decision row should include:

- `blind_spot_review_row_id`
- `source_345c8_blind_spot_candidate_id`
- `raw_metric_name`
- `remaining_row_count`
- `remaining_raw_metric_rank`
- `candidate_priority`
- `risk_level`
- `estimated_max_newly_normalized_rows`
- `estimated_coverage_delta_if_resolved`
- `estimated_ready_candidate_delta_if_resolved`
- `human_blind_spot_review_decision`
- `approved_standard_metric`
- `approved_new_standard_metric`
- `needs_alias_family_expansion`
- `needs_source_context`
- `reviewer`
- `reviewed_at`
- `review_notes`
- `decision_validation_status`
- `decision_validation_issues`
- `apply_simulation_eligible`
- `canonical_alias_target`
- `alias_rule_update_allowed`

`canonical_alias_target` should be:

- `approved_standard_metric` for `APPROVE_EXISTING_MAPPING`
- `approved_new_standard_metric` for `APPROVE_NEW_STANDARD`
- blank for rejected / needs-source-context / deferred / invalid rows

For this task, force output `alias_rule_update_allowed = false` for every row.

---

## Manifest metrics

Manifest must include:

- `decision = SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION_345C10_READY`
- `input_stage = POST_345C9_SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_345c9_decision`
- `input_review_required_row_count`
- `reviewed_row_count`
- `approved_existing_mapping_count`
- `approved_new_standard_count`
- `rejected_too_generic_count`
- `needs_source_context_count`
- `deferred_count`
- `missing_decision_count`
- `invalid_decision_count`
- `validation_issue_count`
- `apply_simulation_eligible_count`
- `needs_alias_family_expansion_count`
- `alias_rule_update_allowed_count = 0`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `human_review_completed`
- `alias_apply_simulation_ready`
- `milestone_ledger_updated`

Expected reviewed counts for this run:

- `approved_new_standard_count = 15`
- `needs_source_context_count = 1`
- `approved_existing_mapping_count = 0`
- `rejected_too_generic_count = 0`
- `deferred_count = 0`
- `apply_simulation_eligible_count = 15`

If actual counts differ, do not automatically fail; record the difference in summary and validation notes unless it violates schema rules.

All formal/client/production gates must remain false.

---

## Reports

Executive summary must explain:

- input 345C9 package and reviewed workbook path
- reviewed row count
- decision distribution
- validation issues, if any
- approved aliases eligible for second-batch simulation
- rows needing source context / rejected / deferred
- why rules were not updated
- why all gates remain false
- what 345C11 should do next

Next plan must recommend:

- `345C11 Second Batch Alias Apply Simulation`
- then stop alias governance or decide explicitly before returning to `345D Full Structured Demo Export Package`

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/345C10_second_batch_reviewed_alias_decision_ingestion.md`
- `datefac/benchmark/second_batch_reviewed_alias_decision_ingestion_345c10.py`
- `datefac/benchmark/second_batch_reviewed_alias_decision_ingestion_345c10_report.py`
- `tools/run_second_batch_reviewed_alias_decision_ingestion_345c10.py`
- `tests/benchmark/test_second_batch_reviewed_alias_decision_ingestion_345c10.py`
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
python -m py_compile datefac\benchmark\second_batch_reviewed_alias_decision_ingestion_345c10.py datefac\benchmark\second_batch_reviewed_alias_decision_ingestion_345c10_report.py tools\run_second_batch_reviewed_alias_decision_ingestion_345c10.py tests\benchmark\test_second_batch_reviewed_alias_decision_ingestion_345c10.py
python -m pytest tests\benchmark\test_second_batch_reviewed_alias_decision_ingestion_345c10.py -q
python tools\run_second_batch_reviewed_alias_decision_ingestion_345c10.py --remaining-blind-spot-human-review-package-345c9-dir D:\_datefac\output\remaining_blind_spot_human_review_package_345c9 --reviewed-blind-spot-workbook D:\_datefac\output\remaining_blind_spot_human_review_package_345c9\remaining_blind_spot_human_review_package_345c9_reviewed.xlsx --output-dir D:\_datefac\output\second_batch_reviewed_alias_decision_ingestion_345c10
```

Tests must verify:

- outputs exist
- decision is ready
- QA is zero for valid reviewed workbook fixture
- reviewed row count matches original review_required row count
- decision distribution is computed correctly
- approved rows become apply-simulation eligible
- needs-source-context / rejected / deferred rows are not apply-simulation eligible
- alias_rule_update_allowed remains false
- official rules/assets modified flags remain false
- all client/export/production gates remain false
- milestone ledger is updated with a 345C10 entry
- no input write-back occurs
- missing/invalid required inputs fail clearly
- duplicate ids fail clearly

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
8. reviewed row count.
9. decision distribution.
10. validation issue count.
11. apply simulation eligible count.
12. alias family expansion / source context counts.
13. alias rule update allowed count.
14. official rules/assets modified flags.
15. final gate status.
16. first file to open.
17. next recommended step.
18. `git status -sb`.
19. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/protected dirty files.
