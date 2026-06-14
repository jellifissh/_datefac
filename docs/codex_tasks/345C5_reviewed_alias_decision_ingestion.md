# 345C5 Reviewed Alias Decision Ingestion

## Goal

Implement `345C5 Reviewed Alias Decision Ingestion`.

Current context:

- 345C2 live generated 26 LLM alias suggestions.
- 345C4 packaged those 26 suggestions into a strict human review workbook.
- The reviewed workbook has now been filled by the human reviewer.

Reviewed workbook expected result:

- `review_row_count = 26`
- `APPROVE_NEW_STANDARD = 22`
- `NEEDS_MORE_CONTEXT = 2`
- `REJECT_ALIAS = 2`
- `APPROVE_EXISTING_MAPPING = 0`
- `alias_rule_update_allowed` remains false in generated/input rows unless a later explicit rule-update task changes it.

345C5 must ingest the reviewed 345C4 workbook, validate human decisions, and generate a no-write-back reviewed-alias decision package.

345C5 must not apply alias decisions to upstream data, modify normalization rules, modify official alias assets, or open any formal/client/production gate.

345C5 answers:

> Which LLM alias suggestions were approved, rejected, deferred, or marked as needing more context by the human reviewer, and is the reviewed alias decision set ready for no-write-back apply simulation?

---

## Required reviewed workbook placement

Before running 345C5, copy the reviewed workbook to the project output area, for example:

```text
D:\_datefac\output\alias_suggestion_human_review_package_345c4\alias_suggestion_human_review_package_345c4_reviewed.xlsx
```

345C5 must never edit this reviewed workbook. It only reads it.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345C5_reviewed_alias_decision_ingestion.md`

Inspect only runner input files/dirs. Do not scan the whole repo.

---

## Runner inputs

Support:

```powershell
--alias-suggestion-human-review-package-345c4-dir D:\_datefac\output\alias_suggestion_human_review_package_345c4
--reviewed-alias-workbook D:\_datefac\output\alias_suggestion_human_review_package_345c4\alias_suggestion_human_review_package_345c4_reviewed.xlsx
--output-dir D:\_datefac\output\reviewed_alias_decision_ingestion_345c5
```

If the 345C4 manifest, original review rows, or reviewed workbook are missing, fail clearly.

---

## Inputs to read

Read from 345C4 package dir:

- `alias_suggestion_human_review_package_345c4_manifest.json`
- `alias_suggestion_human_review_package_345c4_review_rows.json` or `.csv`
- `alias_suggestion_human_review_package_345c4.xlsx` only as original generated package reference if needed

Read reviewed workbook:

- `alias_suggestion_human_review_package_345c4_reviewed.xlsx`

The reviewed workbook should include review fields:

- `human_alias_review_decision`
- `approved_standard_metric`
- `approved_new_standard_metric`
- `alias_reviewer`
- `alias_reviewed_at`
- `alias_review_notes`

Do not trust row order alone. Prefer stable ids such as `alias_review_row_id` and `alias_adjudication_id` when matching original rows to reviewed rows. If ids are missing or duplicated, fail clearly.

---

## Outputs

Write only under:

```text
D:\_datefac\output\reviewed_alias_decision_ingestion_345c5
```

Generate:

- `reviewed_alias_decision_ingestion_345c5_manifest.json`
- `reviewed_alias_decision_ingestion_345c5_reviewed_decisions.json`
- `reviewed_alias_decision_ingestion_345c5_reviewed_decisions.csv`
- `reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.json`
- `reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.csv`
- `reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.json`
- `reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.csv`
- `reviewed_alias_decision_ingestion_345c5_validation_issues.json`
- `reviewed_alias_decision_ingestion_345c5_decision_summary.json`
- `reviewed_alias_decision_ingestion_345c5_executive_summary.md`
- `reviewed_alias_decision_ingestion_345c5_artifact_index.md`
- `reviewed_alias_decision_ingestion_345c5_next_plan.md`

Do not write back into 345C4, 345C2, 345C, 345B, 345A, official rules, alias assets, input dirs, or upstream outputs.

---

## Decision validation rules

Allowed human decisions:

- `APPROVE_EXISTING_MAPPING`
- `APPROVE_NEW_STANDARD`
- `REJECT_ALIAS`
- `NEEDS_MORE_CONTEXT`
- `DEFER`

Validation requirements:

- `APPROVE_EXISTING_MAPPING` requires non-empty `approved_standard_metric` and empty or consistent `approved_new_standard_metric`.
- `APPROVE_NEW_STANDARD` requires non-empty `approved_new_standard_metric` and should include review notes.
- `REJECT_ALIAS` should include review notes.
- `NEEDS_MORE_CONTEXT` should include review notes explaining missing context.
- `DEFER` should not be used in apply simulation.
- Missing or unknown decision must be counted as validation issue.
- Duplicate reviewed row ids must fail QA.
- Reviewed row count must match original 345C4 review row count unless explicitly recorded as fatal QA failure.

The generated ingestion package may mark rows as apply-simulation eligible only when:

- decision is `APPROVE_EXISTING_MAPPING` or `APPROVE_NEW_STANDARD`
- required approved metric field is present
- validation passed

Even eligible rows must not update official rules in 345C5.

---

## Output row schema

Each reviewed decision row should include:

- `alias_review_row_id`
- `alias_adjudication_id`
- `raw_metric_name`
- `frequency`
- `alias_candidate_priority`
- `llm_suggested_action`
- `llm_suggested_standard_metric`
- `llm_suggested_new_standard_metric`
- `llm_confidence`
- `human_alias_review_decision`
- `approved_standard_metric`
- `approved_new_standard_metric`
- `alias_reviewer`
- `alias_reviewed_at`
- `alias_review_notes`
- `decision_validation_status`
- `decision_validation_issues`
- `apply_simulation_eligible`
- `canonical_alias_target`
- `alias_rule_update_allowed`

`canonical_alias_target` should be:

- `approved_standard_metric` for `APPROVE_EXISTING_MAPPING`
- `approved_new_standard_metric` for `APPROVE_NEW_STANDARD`
- blank for rejected / needs-context / deferred / invalid rows

`alias_rule_update_allowed` must remain false unless the reviewed workbook explicitly set it and the task is explicitly designed to accept it. For this task, force output `alias_rule_update_allowed = false`.

---

## Manifest metrics

Manifest must include:

- `decision = REVIEWED_ALIAS_DECISION_INGESTION_345C5_READY`
- `input_stage = POST_345C4_REVIEWED_ALIAS_DECISION_INGESTION`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_345c4_decision`
- `input_review_row_count`
- `reviewed_row_count`
- `approved_existing_mapping_count`
- `approved_new_standard_count`
- `rejected_alias_count`
- `needs_more_context_count`
- `deferred_count`
- `missing_decision_count`
- `invalid_decision_count`
- `validation_issue_count`
- `apply_simulation_eligible_count`
- `alias_rule_update_allowed_count = 0`
- `alias_apply_simulation_ready`

Expected reviewed counts for this run:

- `approved_new_standard_count = 22`
- `needs_more_context_count = 2`
- `rejected_alias_count = 2`
- `approved_existing_mapping_count = 0`

If actual counts differ, do not automatically fail; record the difference in summary and validation notes unless it violates schema rules.

All formal/client/production gates must remain false.

---

## Reports

Executive summary must explain:

- input 345C4 package and reviewed workbook path
- reviewed row count
- decision distribution
- validation issues, if any
- approved aliases eligible for simulation
- rejected / needs-context rows
- why rules were not updated
- why all gates remain false
- what 345C6 should do next

Next plan must recommend:

- `345C6 Reviewed Alias Apply Simulation`
- `345D Full Structured Demo Export Package` only after simulation impact is measured

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/345C5_reviewed_alias_decision_ingestion.md`
- `datefac/benchmark/reviewed_alias_decision_ingestion_345c5.py`
- `datefac/benchmark/reviewed_alias_decision_ingestion_345c5_report.py`
- `tools/run_reviewed_alias_decision_ingestion_345c5.py`
- `tests/benchmark/test_reviewed_alias_decision_ingestion_345c5.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md` only if clean or explicitly requested as ledger-only

If the ledger is dirty, do not modify it during 345C5.

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
python -m py_compile datefac\benchmark\reviewed_alias_decision_ingestion_345c5.py datefac\benchmark\reviewed_alias_decision_ingestion_345c5_report.py tools\run_reviewed_alias_decision_ingestion_345c5.py tests\benchmark\test_reviewed_alias_decision_ingestion_345c5.py
python -m pytest tests\benchmark\test_reviewed_alias_decision_ingestion_345c5.py -q
python tools\run_reviewed_alias_decision_ingestion_345c5.py --alias-suggestion-human-review-package-345c4-dir D:\_datefac\output\alias_suggestion_human_review_package_345c4 --reviewed-alias-workbook D:\_datefac\output\alias_suggestion_human_review_package_345c4\alias_suggestion_human_review_package_345c4_reviewed.xlsx --output-dir D:\_datefac\output\reviewed_alias_decision_ingestion_345c5
```

Tests must verify:

- outputs exist
- decision is ready
- QA is zero for valid reviewed workbook fixture
- reviewed row count matches original review row count
- decision distribution is computed correctly
- approved rows become apply-simulation eligible
- rejected/needs-context/deferred rows are not apply-simulation eligible
- alias_rule_update_allowed remains false
- all client/export/production gates remain false
- no input write-back occurs
- missing/invalid required inputs fail clearly
- duplicate ids fail clearly

---

## Completion report

Report:

1. Files changed.
2. py_compile result.
3. pytest result.
4. real runner result.
5. output dir.
6. decision and QA metrics.
7. reviewed row count.
8. decision distribution.
9. validation issue count.
10. apply simulation eligible count.
11. alias rule update allowed count.
12. final gate status.
13. first file to open.
14. `git status -sb`.
15. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/protected dirty files.
