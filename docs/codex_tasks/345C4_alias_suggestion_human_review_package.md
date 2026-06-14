# 345C4 Alias Suggestion Human Review Package

## Goal

Implement `345C4 Alias Suggestion Human Review Package`.

Current context:

- 345A completed full structured-data inventory.
- 345B completed extraction quality audit.
- 345C completed metric normalization coverage.
- 345C2 request-only generated an alias adjudication request package.
- 345C2 live completed LLM-assisted alias adjudication.

345C2 live result:

- `decision = LLM_ASSISTED_METRIC_ALIAS_ADJUDICATION_345C2_READY`
- `qa_fail_count = 0`
- `llm_mode = live`
- `runtime_config_available = true`
- `live_llm_suggestions_generated = true`
- `input_alias_candidate_count = 134`
- `selected_alias_candidate_count = 26`
- `suggestion_row_count = 26`
- `map_to_existing_count = 0`
- `propose_new_standard_count = 13`
- `exclude_non_core_count = 0`
- `needs_human_review_count = 26`
- `insufficient_evidence_count = 2`
- `high_confidence_suggestion_count = 0`
- `medium_confidence_suggestion_count = 8`
- `low_confidence_suggestion_count = 18`
- `parse_failed_count = 0`
- `validation_failed_count = 1`
- all formal/client/production gates remain false

345C4 must turn the 345C2 live suggestions into a strict human review package. It must not apply alias suggestions, modify normalization rules, modify official alias assets, or open any export/client/production gate.

345C4 answers:

> Which LLM alias suggestions should a human reviewer approve, reject, or mark as needing more context before any alias apply simulation can happen?

This is a review packaging task, not a rule update task. Shocking, yes, humans still get the final vote before the machine edits financial semantics.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345C4_alias_suggestion_human_review_package.md`

Inspect only runner input dirs. Do not scan the whole repo.

---

## Runner inputs

Support:

```powershell
--llm-assisted-metric-alias-adjudication-345c2-live-dir D:\_datefac\output\llm_assisted_metric_alias_adjudication_345c2_live
--output-dir D:\_datefac\output\alias_suggestion_human_review_package_345c4
```

If the live 345C2 manifest, alias suggestions, or review-required files are missing, fail clearly.

The runner should prefer live 345C2 outputs. Do not use request-only output as the main input unless an explicit future flag is added. 345C4 is meant to package actual LLM suggestions, not empty request shells wearing a badge.

---

## Inputs to read from 345C2 live

Read:

- `llm_assisted_metric_alias_adjudication_345c2_manifest.json`
- `llm_assisted_metric_alias_adjudication_345c2_alias_suggestions.json` or `.csv`
- `llm_assisted_metric_alias_adjudication_345c2_review_required.json` or `.csv`
- `llm_assisted_metric_alias_adjudication_345c2_response_audit.json` if available
- `llm_assisted_metric_alias_adjudication_345c2_prompt_audit.md` if available

Validate that:

- 345C2 decision is `LLM_ASSISTED_METRIC_ALIAS_ADJUDICATION_345C2_READY`
- `llm_mode = live`
- `suggestion_row_count > 0`
- `selected_alias_candidate_count = 26` or record a warning if different
- all formal/client/production gates are false

---

## Outputs

Write only under:

```text
D:\_datefac\output\alias_suggestion_human_review_package_345c4
```

Generate:

- `alias_suggestion_human_review_package_345c4_manifest.json`
- `alias_suggestion_human_review_package_345c4_review_rows.json`
- `alias_suggestion_human_review_package_345c4_review_rows.csv`
- `alias_suggestion_human_review_package_345c4.xlsx`
- `alias_suggestion_human_review_package_345c4_reviewer_checklist.md`
- `alias_suggestion_human_review_package_345c4_decision_options.md`
- `alias_suggestion_human_review_package_345c4_llm_suggestion_summary.json`
- `alias_suggestion_human_review_package_345c4_priority_summary.json`
- `alias_suggestion_human_review_package_345c4_executive_summary.md`
- `alias_suggestion_human_review_package_345c4_artifact_index.md`
- `alias_suggestion_human_review_package_345c4_next_plan.md`

Do not write back into 345C2, 345C, 345B, 345A, official rules, alias assets, input dirs, or upstream outputs.

---

## Review row schema

Each review row must include, where available:

- `alias_review_row_id`
- `alias_adjudication_id`
- `raw_metric_name`
- `frequency`
- `alias_candidate_priority`
- `source_stages`
- `pdf_names`
- `sample_row_ids`
- `llm_suggested_action`
- `llm_suggested_standard_metric`
- `llm_suggested_new_standard_metric`
- `llm_confidence`
- `llm_reason`
- `llm_evidence_excerpt`
- `llm_risk_flags`
- `llm_needs_human_review`
- `response_parse_status`
- `response_validation_status`
- `review_priority`
- `recommended_human_focus`
- `human_alias_review_decision`
- `approved_standard_metric`
- `approved_new_standard_metric`
- `alias_reviewer`
- `alias_reviewed_at`
- `alias_review_notes`
- `alias_rule_update_allowed`

Generated reviewer fields must be blank by default:

- `human_alias_review_decision = ""`
- `approved_standard_metric = ""`
- `approved_new_standard_metric = ""`
- `alias_reviewer = ""`
- `alias_reviewed_at = ""`
- `alias_review_notes = ""`
- `alias_rule_update_allowed = false`

Do not pre-approve any LLM suggestion.

---

## Human decision options

Allowed human decisions:

- `APPROVE_EXISTING_MAPPING`
- `APPROVE_NEW_STANDARD`
- `REJECT_ALIAS`
- `NEEDS_MORE_CONTEXT`
- `DEFER`

Rules:

- `APPROVE_EXISTING_MAPPING` requires `approved_standard_metric`.
- `APPROVE_NEW_STANDARD` requires `approved_new_standard_metric` and should normally require notes.
- `REJECT_ALIAS` should include a note.
- `NEEDS_MORE_CONTEXT` should include what context is missing.
- `DEFER` means no apply simulation should use this row.
- `alias_rule_update_allowed` must remain false in generated rows and can only be changed in later reviewed ingestion/apply tasks if explicitly designed.

---

## Priority rules

`review_priority` suggestion:

- `HIGH`: LLM proposed a new standard, validation failed, insufficient evidence, high-frequency alias, or alias was high-priority in 345C.
- `MEDIUM`: medium confidence or medium frequency.
- `LOW`: low frequency and low impact.

`recommended_human_focus` should be short, for example:

- `confirm whether this should become a new standard metric`
- `check if this can map to an existing standard metric`
- `verify insufficient evidence before rejecting`
- `inspect validation failure before deciding`

---

## Manifest metrics

Manifest must include:

- `decision = ALIAS_SUGGESTION_HUMAN_REVIEW_PACKAGE_345C4_READY`
- `input_stage = POST_345C2_LIVE_ALIAS_SUGGESTION_REVIEW_PACKAGE`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_345c2_decision`
- `input_llm_mode`
- `input_suggestion_row_count`
- `review_row_count`
- `llm_map_to_existing_count`
- `llm_propose_new_standard_count`
- `llm_exclude_non_core_count`
- `llm_needs_human_review_count`
- `llm_insufficient_evidence_count`
- `llm_high_confidence_count`
- `llm_medium_confidence_count`
- `llm_low_confidence_count`
- `parse_failed_count`
- `validation_failed_count`
- `generated_review_pending_count`
- `generated_approved_count = 0`
- `alias_rule_update_allowed_count = 0`
- `alias_apply_simulation_allowed = false`

All formal/client/production gates must remain false.

---

## Reports

Reviewer checklist must explain:

1. This package is for human review of LLM alias suggestions only.
2. LLM suggestions are not approved by default.
3. Reviewers should inspect raw metric name, frequency, source stages, sample row ids, LLM action, reason, evidence, confidence, and validation status.
4. Reviewers should fill only the human review fields.
5. Reviewers must not edit LLM evidence fields or source fields.
6. This task does not modify normalization rules or official alias assets.
7. 345C5 or later should ingest reviewed decisions.

Executive summary must explain:

- input 345C2 live result
- why every suggestion needs human review
- how many review rows were generated
- proposed-new-standard count
- insufficient-evidence count
- validation-failed count
- why no rules were changed
- why all gates remain false
- what 345C5 should do next

Next plan must recommend:

- `345C5 Reviewed Alias Decision Ingestion`
- `345C6 Reviewed Alias Apply Simulation`
- `345D Full Structured Demo Export Package` only after reviewed alias impact is measured

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/345C4_alias_suggestion_human_review_package.md`
- `datefac/benchmark/alias_suggestion_human_review_package_345c4.py`
- `datefac/benchmark/alias_suggestion_human_review_package_345c4_report.py`
- `tools/run_alias_suggestion_human_review_package_345c4.py`
- `tests/benchmark/test_alias_suggestion_human_review_package_345c4.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md` only if clean or explicitly requested as ledger-only

If the ledger is dirty, do not modify it during 345C4.

---

## Forbidden

Do not:

- modify normalization rules
- modify official alias assets
- apply alias suggestions to upstream data
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
python -m py_compile datefac\benchmark\alias_suggestion_human_review_package_345c4.py datefac\benchmark\alias_suggestion_human_review_package_345c4_report.py tools\run_alias_suggestion_human_review_package_345c4.py tests\benchmark\test_alias_suggestion_human_review_package_345c4.py
python -m pytest tests\benchmark\test_alias_suggestion_human_review_package_345c4.py -q
python tools\run_alias_suggestion_human_review_package_345c4.py --llm-assisted-metric-alias-adjudication-345c2-live-dir D:\_datefac\output\llm_assisted_metric_alias_adjudication_345c2_live --output-dir D:\_datefac\output\alias_suggestion_human_review_package_345c4
```

Tests must verify:

- outputs exist
- workbook is generated
- decision is ready
- QA is zero
- review row count equals 345C2 live suggestion row count
- all human review fields are blank by default
- `alias_rule_update_allowed = false` for generated rows
- all client/export/production gates remain false
- no input write-back occurs
- missing/invalid required 345C2 live inputs fail clearly

---

## Completion report

Report:

1. Files changed.
2. py_compile result.
3. pytest result.
4. real runner result.
5. output dir.
6. decision and QA metrics.
7. input 345C2 decision and llm_mode.
8. review row count.
9. LLM suggestion distribution summary.
10. generated pending/approved/rule-update counts.
11. final gate status.
12. first file to open.
13. `git status -sb`.
14. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/protected dirty files.
