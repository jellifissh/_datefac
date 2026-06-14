# 345C9 Remaining Blind Spot Human Review Package

## Goal

Implement `345C9 Remaining Blind Spot Human Review Package`.

Current context:

- 345C measured metric normalization coverage on the full structured-data inventory.
- 345C5 ingested first-batch reviewed alias decisions.
- 345C6 simulated first-batch reviewed alias application.
- 345C7 packaged first-batch official alias-rule update candidates and concluded the batch was not ready for official rule update.
- 345C8 selected the next bounded batch of remaining blind-spot alias candidates and recommended continuing with a second review batch.

345C8 result:

- `decision = REMAINING_BLIND_SPOT_ALIAS_CANDIDATE_PACKAGE_345C8_READY`
- `qa_fail_count = 0`
- `remaining_unnormalized_raw_metric_name_count = 112`
- `remaining_unnormalized_metric_row_count = 6284`
- `selected_candidate_count = 30`
- `max_blind_spot_candidates = 30`
- `min_row_impact = 10`
- `selected_estimated_row_impact_total = 3071`
- `selected_estimated_coverage_delta_total = 0.207667`
- `selected_estimated_ready_candidate_delta_total = 0`
- `high_priority_candidate_count = 25`
- `medium_priority_candidate_count = 5`
- `low_priority_candidate_count = 0`
- `include_in_second_review_batch_count = 16`
- `include_as_context_only_count = 3`
- `exclude_too_generic_count = 6`
- `needs_source_context_before_review_count = 11`
- `low_risk_candidate_count = 0`
- `medium_risk_candidate_count = 16`
- `high_risk_candidate_count = 14`
- `alias_branch_stop_or_continue_decision = CONTINUE_WITH_SECOND_REVIEW_BATCH`
- `full_structured_demo_export_reasonable_after_345c8 = false`
- all formal/client/production gates remain false

345C9 must turn the 345C8 selected remaining blind-spot candidates into a bounded human review workbook/package for the second alias review batch.

345C9 must not perform the human review itself. It must not call LLM/VLM, modify normalization rules, modify official alias assets, apply aliases to upstream data, or open gates. It only prepares a reviewer-facing package.

345C9 answers:

> Which remaining blind-spot candidates should a human reviewer inspect in the second batch, what evidence should be shown, what decision fields should be filled, and which candidates should remain context-only or blocked until more source context exists?

This is a human review packaging task, not a semantic adjudication task. Do not let the code cosplay as a reviewer.

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Add a concise 345C9 entry after successful implementation and validation.

The ledger entry should include:

- task id: `345C9`
- decision: `REMAINING_BLIND_SPOT_HUMAN_REVIEW_PACKAGE_345C9_READY`
- input package: 345C8 output dir
- output package: 345C9 output dir
- review row count
- context-only / source-context / too-generic counts
- gate status: all false
- no-write-back confirmation
- validation commands and results
- next recommended step: human fills workbook, then 345C10 ingestion

If the ledger has unrelated dirty changes, do not overwrite them blindly. Append only the 345C9 entry. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345C9_remaining_blind_spot_human_review_package.md`

Inspect only runner input dirs and the milestone ledger. Do not scan the whole repo.

---

## Runner inputs

Support:

```powershell
--remaining-blind-spot-alias-candidate-package-345c8-dir D:\_datefac\output\remaining_blind_spot_alias_candidate_package_345c8
--output-dir D:\_datefac\output\remaining_blind_spot_human_review_package_345c9
```

Also support:

```powershell
--include-context-only
```

Default behavior:

- Main review rows should include candidates recommended as `INCLUDE_IN_SECOND_REVIEW_BATCH`.
- Context-only / needs-source-context / too-generic candidates should be written to separate sheets/files, not mixed into the main actionable review sheet unless `--include-context-only` is explicitly passed.

If the 345C8 manifest or selected candidates are missing, fail clearly.

---

## Inputs to read

From 345C8:

- `remaining_blind_spot_alias_candidate_package_345c8_manifest.json`
- `remaining_blind_spot_alias_candidate_package_345c8_selected_candidates.json` or `.csv`
- `remaining_blind_spot_alias_candidate_package_345c8_candidate_impact_summary.json` or `.csv`
- `remaining_blind_spot_alias_candidate_package_345c8_review_batch_recommendation.json`
- `remaining_blind_spot_alias_candidate_package_345c8_stop_or_continue_decision.json`
- `remaining_blind_spot_alias_candidate_package_345c8_executive_summary.md` if available

Validate that:

- 345C8 decision is `REMAINING_BLIND_SPOT_ALIAS_CANDIDATE_PACKAGE_345C8_READY`
- `alias_branch_stop_or_continue_decision = CONTINUE_WITH_SECOND_REVIEW_BATCH` or `CONTINUE_ONLY_IF_HUMAN_REVIEW_CAPACITY_EXISTS`
- selected candidate count is greater than zero
- all formal/client/production gates are false
- official rules/assets modified flags are false

---

## Outputs

Write only under:

```text
D:\_datefac\output\remaining_blind_spot_human_review_package_345c9
```

Generate:

- `remaining_blind_spot_human_review_package_345c9_manifest.json`
- `remaining_blind_spot_human_review_package_345c9_review_rows.json`
- `remaining_blind_spot_human_review_package_345c9_review_rows.csv`
- `remaining_blind_spot_human_review_package_345c9_context_only_rows.json`
- `remaining_blind_spot_human_review_package_345c9_context_only_rows.csv`
- `remaining_blind_spot_human_review_package_345c9_blocked_rows.json`
- `remaining_blind_spot_human_review_package_345c9_blocked_rows.csv`
- `remaining_blind_spot_human_review_package_345c9.xlsx`
- `remaining_blind_spot_human_review_package_345c9_reviewer_checklist.md`
- `remaining_blind_spot_human_review_package_345c9_decision_options.md`
- `remaining_blind_spot_human_review_package_345c9_package_summary.json`
- `remaining_blind_spot_human_review_package_345c9_executive_summary.md`
- `remaining_blind_spot_human_review_package_345c9_artifact_index.md`
- `remaining_blind_spot_human_review_package_345c9_next_plan.md`

The workbook should include clear sheets such as:

- `review_required`
- `context_only`
- `blocked_or_too_generic`
- `decision_options`
- `reviewer_checklist`
- `package_summary`

Do not write back into 345C8, 345C7, 345C6, 345C5, 345C4, 345C2, 345C, 345B, 345A, official rules, alias assets, input dirs, or upstream outputs.

---

## Human review row schema

Main review rows should include, where available:

- `blind_spot_review_row_id`
- `source_345c8_blind_spot_candidate_id`
- `raw_metric_name`
- `remaining_row_count`
- `remaining_raw_metric_rank`
- `source_stages`
- `pdf_names`
- `source_artifacts`
- `sample_row_ids`
- `sample_evidence_excerpt`
- `candidate_priority`
- `candidate_reason`
- `risk_level`
- `risk_reasons`
- `estimated_max_newly_normalized_rows`
- `estimated_coverage_delta_if_resolved`
- `estimated_ready_candidate_delta_if_resolved`
- `needs_llm_adjudication`
- `needs_human_review`
- `suggested_next_review_action`

Add blank human review fields:

- `human_blind_spot_review_decision`
- `approved_standard_metric`
- `approved_new_standard_metric`
- `needs_alias_family_expansion`
- `needs_source_context`
- `reviewer`
- `reviewed_at`
- `review_notes`
- `alias_rule_update_allowed`

Default values:

- `human_blind_spot_review_decision = ""`
- `approved_standard_metric = ""`
- `approved_new_standard_metric = ""`
- `needs_alias_family_expansion = false`
- `needs_source_context = false`
- `reviewer = ""`
- `reviewed_at = ""`
- `review_notes = ""`
- `alias_rule_update_allowed = false`

`alias_rule_update_allowed` must remain false in the generated package. Human review may approve a semantic mapping, but official rule mutation is still a separate future task.

---

## Decision options

Allowed human decisions:

- `APPROVE_EXISTING_MAPPING`
- `APPROVE_NEW_STANDARD`
- `REJECT_TOO_GENERIC`
- `NEEDS_SOURCE_CONTEXT`
- `DEFER`

Decision guidance:

- `APPROVE_EXISTING_MAPPING` requires `approved_standard_metric`.
- `APPROVE_NEW_STANDARD` requires `approved_new_standard_metric`.
- `REJECT_TOO_GENERIC` should include review notes.
- `NEEDS_SOURCE_CONTEXT` should include review notes describing missing source context.
- `DEFER` should include review notes if possible.

Warn reviewers not to approve generic fragments such as:

- `率`
- `变动`
- `成本`
- empty names
- unit-like or suffix-like fragments

unless source context proves the raw name has a stable financial meaning.

---

## Row grouping logic

Generate separate groups:

1. `review_required`: candidates recommended as `INCLUDE_IN_SECOND_REVIEW_BATCH`.
2. `context_only`: candidates recommended as `INCLUDE_AS_CONTEXT_ONLY`.
3. `blocked_or_too_generic`: candidates recommended as `EXCLUDE_TOO_GENERIC` or `NEEDS_SOURCE_CONTEXT_BEFORE_REVIEW`.
4. `unselected_reference`: optional summary of unselected blind spots, if available and cheap to include.

Main review count should primarily track `review_required` rows.

Do not silently inflate the actionable review row count by including context-only or blocked rows.

---

## Manifest metrics

Manifest must include:

- `decision = REMAINING_BLIND_SPOT_HUMAN_REVIEW_PACKAGE_345C9_READY`
- `input_stage = POST_345C8_REMAINING_BLIND_SPOT_HUMAN_REVIEW_PACKAGE`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_345c8_decision`
- `input_alias_branch_stop_or_continue_decision`
- `selected_candidate_count`
- `review_required_row_count`
- `context_only_row_count`
- `blocked_or_too_generic_row_count`
- `main_review_workbook_generated`
- `reviewer_checklist_generated`
- `decision_options_generated`
- `human_review_completed = false`
- `generated_review_pending_count`
- `generated_approved_count = 0`
- `alias_rule_update_allowed_count = 0`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `candidate_package_only = true`
- `alias_apply_simulation_allowed = false`
- `full_structured_demo_export_reasonable_after_345c9 = false`
- `milestone_ledger_updated`

All formal/client/production gates must remain false.

---

## Reports

Executive summary must explain:

- input 345C8 context
- why 345C9 exists
- how many rows require human review
- how many rows are context-only or blocked
- estimated row/coverage impact from the packaged review batch
- risk distribution
- why no rules/assets were changed
- why all gates remain false
- that the workbook must be filled before 345C10 ingestion

Reviewer checklist must explain:

1. Open `remaining_blind_spot_human_review_package_345c9.xlsx`.
2. Fill only the human review fields in the `review_required` sheet.
3. Do not edit evidence/source fields.
4. Use only allowed decision options.
5. Do not set `alias_rule_update_allowed` true.
6. Save reviewed workbook separately, for example:

```text
D:\_datefac\output\remaining_blind_spot_human_review_package_345c9\remaining_blind_spot_human_review_package_345c9_reviewed.xlsx
```

Next plan must recommend:

- human reviewer fills the 345C9 workbook
- `345C10 Second Batch Reviewed Alias Decision Ingestion`
- `345C11 Second Batch Alias Apply Simulation`
- then decide whether to stop alias governance and return to `345D Full Structured Demo Export Package`

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/345C9_remaining_blind_spot_human_review_package.md`
- `datefac/benchmark/remaining_blind_spot_human_review_package_345c9.py`
- `datefac/benchmark/remaining_blind_spot_human_review_package_345c9_report.py`
- `tools/run_remaining_blind_spot_human_review_package_345c9.py`
- `tests/benchmark/test_remaining_blind_spot_human_review_package_345c9.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

The milestone ledger update is required for this task.

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
python -m py_compile datefac\benchmark\remaining_blind_spot_human_review_package_345c9.py datefac\benchmark\remaining_blind_spot_human_review_package_345c9_report.py tools\run_remaining_blind_spot_human_review_package_345c9.py tests\benchmark\test_remaining_blind_spot_human_review_package_345c9.py
python -m pytest tests\benchmark\test_remaining_blind_spot_human_review_package_345c9.py -q
python tools\run_remaining_blind_spot_human_review_package_345c9.py --remaining-blind-spot-alias-candidate-package-345c8-dir D:\_datefac\output\remaining_blind_spot_alias_candidate_package_345c8 --output-dir D:\_datefac\output\remaining_blind_spot_human_review_package_345c9
```

Tests must verify:

- outputs exist
- decision is ready
- QA is zero
- review workbook is generated
- review rows contain blank human review fields
- context-only and blocked rows are separated from actionable review rows
- generated approved count is zero
- alias_rule_update_allowed remains false
- official rules/assets modified flags remain false
- all client/export/production gates remain false
- milestone ledger is updated with a 345C9 entry
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
8. review required row count.
9. context-only row count.
10. blocked / too-generic row count.
11. generated pending / approved / alias-rule-update-allowed counts.
12. workbook path and first file to open.
13. official rules/assets modified flags.
14. final gate status.
15. next required human action.
16. `git status -sb`.
17. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/protected dirty files.
