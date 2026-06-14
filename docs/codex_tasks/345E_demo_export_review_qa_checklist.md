# 345E Demo Export Review / QA Checklist

## Goal

Implement `345E Demo Export Review / QA Checklist`.

Current context:

- 345A built the full structured data inventory.
- 345B audited extraction quality across the full inventory.
- 345C measured baseline metric normalization coverage.
- 345C11 completed the reviewed alias simulation branch and recommended returning to 345D.
- 345D generated the full structured demo export package.

345D result:

- `decision = FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY`
- `qa_fail_count = 0`
- `demo_export_row_count = 109`
- `quality_limited_row_count = 5558`
- `excluded_row_count = 9121`
- `inventory_row_count = 14788`
- row count closure: `109 + 5558 + 9121 = 14788`
- `coverage_ratio_before_alias_simulation = 0.452461`
- `coverage_ratio_after_alias_simulation = 0.684136`
- `baseline_normalized_demo_row_count = 109`
- `alias_simulated_demo_row_count = 1532`
- `remaining_unnormalized_raw_metric_name_count = 96`
- `remaining_unnormalized_metric_row_count = 4671`
- `remaining_ready_candidate_count = null`
- `high_severity_issue_count = 7595`
- `medium_severity_issue_count = 7084`
- `missing_unit_count = 838`
- `missing_period_count = 0`
- `missing_source_trace_count = 0`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `formal_export_generated = false`
- `demo_export_only = true`
- all formal/client/production gates remain false

345E must review the 345D demo export package and generate a QA checklist/report package. It must verify artifact completeness, row-count closure, caveat clarity, gate safety, and presentation readiness for a bounded demo. It must not create a new export dataset, mutate prior outputs, or convert demo output into client-ready output.

345E answers:

> Is the 345D demo export package internally consistent, safe to present as a demo, honest about its caveats, and ready to feed a demo narrative/report package without claiming formal client or production readiness?

This is a QA review task, not a new extraction/export task. If QA starts inventing new data, the QA has become the bug. Very entrepreneurial, very cursed.

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Add a concise 345E entry after successful implementation and validation.

The ledger entry should include:

- task id: `345E`
- decision: `DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_READY`
- input package: 345D output dir
- output package: 345E output dir
- checked artifact count
- missing artifact count
- row-count closure status
- demo row / quality-limited / excluded counts
- caveat completeness status
- gate status: all false
- no-write-back confirmation
- validation commands and results
- next recommended step

If the ledger has unrelated dirty changes, do not overwrite them blindly. Append only the 345E entry. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345E_demo_export_review_qa_checklist.md`

Inspect only runner input dirs and the milestone ledger. Do not scan the whole repo.

---

## Runner inputs

Support:

```powershell
--full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d
--output-dir D:\_datefac\output\demo_export_review_qa_checklist_345e
```

Optional:

```powershell
--max-display-sample-rows 30
--strict-artifact-check
```

Default behavior:

- review existing 345D artifacts;
- compute QA status and checklist results;
- create sample display/readiness artifacts from existing 345D rows only;
- do not modify 345D outputs;
- do not generate a new demo export dataset.

If the 345D manifest or required row artifacts are missing, fail clearly.

---

## Inputs to read

From 345D:

- `full_structured_demo_export_package_345d_manifest.json`
- `full_structured_demo_export_package_345d_demo_rows.json` or `.csv`
- `full_structured_demo_export_package_345d_quality_limited_rows.json` or `.csv`
- `full_structured_demo_export_package_345d_excluded_rows.json` or `.csv`
- `full_structured_demo_export_package_345d_remaining_blind_spots.json` or `.csv`
- `full_structured_demo_export_package_345d_alias_simulation_sidecar.json` or `.csv`
- `full_structured_demo_export_package_345d_quality_caveats.json` or `.md`
- `full_structured_demo_export_package_345d_demo_export_summary.json`
- `full_structured_demo_export_package_345d_executive_summary.md`
- `full_structured_demo_export_package_345d_artifact_index.md`
- `full_structured_demo_export_package_345d_next_plan.md`

Validate that:

- 345D decision is `FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY`
- 345D `qa_fail_count = 0`
- `demo_export_only = true`
- `formal_export_generated = false`
- official rules/assets modified flags are false
- all formal/client/production gates are false

---

## Outputs

Write only under:

```text
D:\_datefac\output\demo_export_review_qa_checklist_345e
```

Generate:

- `demo_export_review_qa_checklist_345e_manifest.json`
- `demo_export_review_qa_checklist_345e_artifact_completeness.json`
- `demo_export_review_qa_checklist_345e_artifact_completeness.csv`
- `demo_export_review_qa_checklist_345e_row_count_reconciliation.json`
- `demo_export_review_qa_checklist_345e_row_count_reconciliation.csv`
- `demo_export_review_qa_checklist_345e_gate_safety_check.json`
- `demo_export_review_qa_checklist_345e_caveat_completeness_check.json`
- `demo_export_review_qa_checklist_345e_demo_presentation_readiness.json`
- `demo_export_review_qa_checklist_345e_sample_demo_rows.json`
- `demo_export_review_qa_checklist_345e_sample_demo_rows.csv`
- `demo_export_review_qa_checklist_345e_quality_limited_sample_rows.json`
- `demo_export_review_qa_checklist_345e_quality_limited_sample_rows.csv`
- `demo_export_review_qa_checklist_345e_excluded_sample_rows.json`
- `demo_export_review_qa_checklist_345e_excluded_sample_rows.csv`
- `demo_export_review_qa_checklist_345e_review_checklist.md`
- `demo_export_review_qa_checklist_345e_executive_summary.md`
- `demo_export_review_qa_checklist_345e_artifact_index.md`
- `demo_export_review_qa_checklist_345e_next_plan.md`

Do not write back into 345D, 345C11, 345C10, 345C9, 345C8, 345C7, 345C6, 345C5, 345C4, 345C2, 345C, 345B, 345A, official rules, alias assets, input dirs, reviewed workbooks, or upstream outputs.

---

## QA checks

### 1. Artifact completeness

Check expected 345D artifacts:

- manifest
- demo rows csv/json/xlsx if present
- quality-limited rows csv/json
- excluded rows csv/json
- remaining blind spots csv/json
- alias simulation sidecar csv/json
- quality caveats json/md
- demo export summary json
- executive summary md
- artifact index md
- next plan md

Record each artifact as:

- `present`
- `missing`
- `optional_missing`
- `empty`
- `read_error`

If `--strict-artifact-check` is passed, missing expected artifacts should fail QA.

### 2. Row-count reconciliation

Verify:

```text
demo_export_row_count + quality_limited_row_count + excluded_row_count == inventory_row_count
```

Expected from 345D:

```text
109 + 5558 + 9121 = 14788
```

Also verify row counts from actual files match manifest counts where possible.

### 3. Gate safety check

Verify across manifest and representative row artifacts:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `formal_export_generated = false`
- `demo_export_only = true`

If any row or artifact claims formal/client/production readiness, fail QA.

### 4. Caveat completeness

Verify caveats clearly mention:

- remaining unnormalized rows / raw metric names
- high severity quality issues
- medium severity quality issues
- missing unit count
- missing period count
- missing source trace count
- alias simulation is not official rule mutation
- official rules/assets remain unchanged
- formal/client/production gates remain false

Record missing caveat topics.

### 5. Presentation readiness

Generate a bounded presentation readiness summary:

- whether 345D is safe to show as demo only
- which artifacts to open first
- which row sample is safe for quick demo
- which caveats must be spoken aloud in any presentation
- what must not be claimed

Do not create sales copy. This is QA, not a perfume ad for CSV files.

### 6. Sample rows

Create sample row files by copying a bounded sample from existing 345D artifacts:

- demo rows sample: up to `--max-display-sample-rows`
- quality-limited sample: up to `--max-display-sample-rows`
- excluded sample: up to `--max-display-sample-rows`

Do not modify row values. Do not normalize or repair rows in 345E.

---

## Manifest metrics

Manifest must include:

- `decision = DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_READY`
- `input_stage = POST_345D_DEMO_EXPORT_REVIEW_QA_CHECKLIST`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_345d_decision`
- `checked_artifact_count`
- `missing_required_artifact_count`
- `optional_missing_artifact_count`
- `artifact_read_error_count`
- `row_count_closure_passed`
- `manifest_row_count_total`
- `actual_row_count_total`
- `demo_export_row_count`
- `quality_limited_row_count`
- `excluded_row_count`
- `coverage_ratio_before_alias_simulation`
- `coverage_ratio_after_alias_simulation`
- `remaining_unnormalized_raw_metric_name_count`
- `remaining_unnormalized_metric_row_count`
- `high_severity_issue_count`
- `medium_severity_issue_count`
- `missing_unit_count`
- `missing_period_count`
- `missing_source_trace_count`
- `caveat_completeness_passed`
- `missing_caveat_topic_count`
- `gate_safety_check_passed`
- `presentation_ready_for_demo_only`
- `formal_export_generated = false`
- `demo_export_only = true`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `milestone_ledger_updated`

All formal/client/production gates must remain false.

If QA finds a true package-safety failure, decision should become `DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_BLOCKED` and `qa_fail_count` should be greater than 0. Valid 345D input is expected to produce READY.

---

## Reports

Executive summary must explain:

- input 345D package
- artifact completeness result
- row-count reconciliation result
- gate safety result
- caveat completeness result
- demo-only presentation readiness
- what artifacts should be opened first
- what must not be claimed
- recommended next step

Review checklist must include a human-readable checklist with status markers, including:

- artifact completeness
- row-count closure
- demo rows present
- quality-limited rows separated
- excluded rows separated
- remaining blind spots reported
- alias simulation caveat present
- official rules/assets unchanged
- formal/client/production gates false
- demo-only flag true
- no formal export generated

Next plan must recommend one of:

- `345F Demo Narrative Report Package`
- `345F Frontend Demo Sample Package`
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists
- a separate official rule-update task only after explicit approval, not automatically from demo output

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/345E_demo_export_review_qa_checklist.md`
- `datefac/benchmark/demo_export_review_qa_checklist_345e.py`
- `datefac/benchmark/demo_export_review_qa_checklist_345e_report.py`
- `tools/run_demo_export_review_qa_checklist_345e.py`
- `tests/benchmark/test_demo_export_review_qa_checklist_345e.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

The milestone ledger update is required for this task.

---

## Forbidden

Do not:

- create a new export dataset beyond bounded sample copies
- modify normalization rules
- modify official alias assets
- apply alias decisions to upstream data
- modify 345D or prior outputs
- rerun MinerU
- call LLM/VLM
- scan the repo
- add dependencies
- modify `datefac/llm/`
- modify production pipeline/parser/extraction/delivery/formal export logic
- generate formal client delivery artifacts
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
python -m py_compile datefac\benchmark\demo_export_review_qa_checklist_345e.py datefac\benchmark\demo_export_review_qa_checklist_345e_report.py tools\run_demo_export_review_qa_checklist_345e.py tests\benchmark\test_demo_export_review_qa_checklist_345e.py
python -m pytest tests\benchmark\test_demo_export_review_qa_checklist_345e.py -q
python tools\run_demo_export_review_qa_checklist_345e.py --full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d --output-dir D:\_datefac\output\demo_export_review_qa_checklist_345e
```

Tests must verify:

- outputs exist
- decision is ready for valid 345D fixture
- QA is zero for valid 345D fixture
- artifact completeness is checked
- row-count closure is checked
- gate safety is checked
- caveat completeness is checked
- demo-only presentation readiness is generated
- bounded sample files are generated from existing 345D rows
- formal/client/production gates remain false
- official rules/assets modified flags remain false
- formal export generated flag remains false
- demo export only flag remains true
- milestone ledger is updated with a 345E entry
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
8. checked / missing / optional missing artifact counts.
9. row-count closure result.
10. demo / quality-limited / excluded row counts.
11. gate safety result.
12. caveat completeness result.
13. presentation readiness result.
14. sample row counts.
15. official rules/assets modified flags.
16. formal export generated / demo export only flags.
17. final gate status.
18. first file to open.
19. next recommended step.
20. `git status -sb`.
21. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/protected dirty files.
