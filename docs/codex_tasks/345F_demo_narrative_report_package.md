# 345F Demo Narrative Report Package

## Goal

Implement `345F Demo Narrative Report Package`.

Current context:

- 345A built the full structured data inventory.
- 345B audited extraction quality across the full inventory.
- 345C measured baseline metric normalization coverage.
- 345C11 completed the reviewed alias simulation branch and recommended returning to 345D.
- 345D generated the full structured demo export package.
- 345E reviewed the 345D demo package and confirmed it is safe for demo-only presentation.

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

345E result:

- `decision = DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_READY`
- `qa_fail_count = 0`
- `checked_artifact_count = 18`
- `missing_required_artifact_count = 0`
- `optional_missing_artifact_count = 0`
- `artifact_read_error_count = 0`
- `row_count_closure_passed = true`
- `gate_safety_check_passed = true`
- `caveat_completeness_passed = true`
- `missing_caveat_topic_count = 0`
- `presentation_ready_for_demo_only = true`
- `sample_demo_row_count = 30`
- `sample_quality_limited_row_count = 30`
- `sample_excluded_row_count = 30`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `formal_export_generated = false`
- `demo_export_only = true`
- all formal/client/production gates remain false

345F must generate a narrative/report package from existing 345D and 345E artifacts. It must explain what the demo package proves, what it does not prove, how alias simulation improved coverage, why strict demo rows remain only 109, what caveats must be shown, and what can be presented to teachers/team/interviewers/frontend viewers without implying client-ready or production-ready status.

345F answers:

> How should the 345D/345E demo export results be explained to stakeholders in a clear, honest, reusable narrative package, while preserving all demo-only and no-production boundaries?

This is report packaging, not data mutation. If a narrative report starts quietly changing numbers, it is not storytelling, it is fraud wearing Markdown.

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Add a concise 345F entry after successful implementation and validation.

The ledger entry should include:

- task id: `345F`
- decision: `DEMO_NARRATIVE_REPORT_PACKAGE_345F_READY`
- input packages: 345D and 345E output dirs
- output package: 345F output dir
- generated report count
- demo row / quality-limited / excluded counts
- coverage before / after alias simulation
- QA readiness summary
- gate status: all false
- no-write-back confirmation
- validation commands and results
- next recommended step

If the ledger has unrelated dirty changes, do not overwrite them blindly. Append only the 345F entry. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345F_demo_narrative_report_package.md`

Inspect only runner input dirs and the milestone ledger. Do not scan the whole repo.

---

## Runner inputs

Support:

```powershell
--full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d
--demo-export-review-qa-checklist-345e-dir D:\_datefac\output\demo_export_review_qa_checklist_345e
--output-dir D:\_datefac\output\demo_narrative_report_package_345f
```

Optional:

```powershell
--max-sample-rows-in-report 10
--audience teacher
--audience team
--audience interview
--audience frontend
```

Default audience may be `teacher`.

Default behavior:

- read existing 345D and 345E outputs;
- generate narrative reports and talking points only;
- include bounded sample row references from 345E samples;
- do not create a new export dataset;
- do not modify 345D/345E outputs;
- do not claim formal client or production readiness.

If 345D or 345E manifest is missing, fail clearly.

---

## Inputs to read

From 345D:

- `full_structured_demo_export_package_345d_manifest.json`
- `full_structured_demo_export_package_345d_demo_export_summary.json`
- `full_structured_demo_export_package_345d_quality_caveats.json` or `.md`
- `full_structured_demo_export_package_345d_executive_summary.md`
- `full_structured_demo_export_package_345d_artifact_index.md`
- `full_structured_demo_export_package_345d_next_plan.md`
- demo rows / quality-limited / excluded rows if needed for counts or examples

From 345E:

- `demo_export_review_qa_checklist_345e_manifest.json`
- `demo_export_review_qa_checklist_345e_review_checklist.md`
- `demo_export_review_qa_checklist_345e_demo_presentation_readiness.json`
- `demo_export_review_qa_checklist_345e_row_count_reconciliation.json` or `.csv`
- `demo_export_review_qa_checklist_345e_gate_safety_check.json`
- `demo_export_review_qa_checklist_345e_caveat_completeness_check.json`
- `demo_export_review_qa_checklist_345e_sample_demo_rows.json` or `.csv`
- `demo_export_review_qa_checklist_345e_quality_limited_sample_rows.json` or `.csv`
- `demo_export_review_qa_checklist_345e_excluded_sample_rows.json` or `.csv`
- `demo_export_review_qa_checklist_345e_executive_summary.md`
- `demo_export_review_qa_checklist_345e_artifact_index.md`
- `demo_export_review_qa_checklist_345e_next_plan.md`

Validate that:

- 345D decision is `FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY`
- 345D `qa_fail_count = 0`
- 345D `demo_export_only = true`
- 345D `formal_export_generated = false`
- 345E decision is `DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_READY`
- 345E `qa_fail_count = 0`
- 345E `row_count_closure_passed = true`
- 345E `gate_safety_check_passed = true`
- 345E `caveat_completeness_passed = true`
- 345E `presentation_ready_for_demo_only = true`
- official rules/assets modified flags are false
- all formal/client/production gates are false

---

## Outputs

Write only under:

```text
D:\_datefac\output\demo_narrative_report_package_345f
```

Generate:

- `demo_narrative_report_package_345f_manifest.json`
- `demo_narrative_report_package_345f_stakeholder_report.md`
- `demo_narrative_report_package_345f_teacher_brief.md`
- `demo_narrative_report_package_345f_team_update.md`
- `demo_narrative_report_package_345f_interview_project_summary.md`
- `demo_narrative_report_package_345f_frontend_demo_copy.md`
- `demo_narrative_report_package_345f_talking_points.md`
- `demo_narrative_report_package_345f_risk_and_caveat_section.md`
- `demo_narrative_report_package_345f_metrics_summary.json`
- `demo_narrative_report_package_345f_metrics_summary.csv`
- `demo_narrative_report_package_345f_sample_rows_for_story.json`
- `demo_narrative_report_package_345f_sample_rows_for_story.csv`
- `demo_narrative_report_package_345f_claims_allowed_vs_forbidden.md`
- `demo_narrative_report_package_345f_artifact_index.md`
- `demo_narrative_report_package_345f_next_plan.md`

Do not write back into 345E, 345D, 345C11, 345C10, 345C9, 345C8, 345C7, 345C6, 345C5, 345C4, 345C2, 345C, 345B, 345A, official rules, alias assets, input dirs, reviewed workbooks, or upstream outputs.

Do not generate formal Word/PDF client delivery artifacts. Markdown/CSV/JSON narrative assets are enough for this task.

---

## Narrative requirements

Generated reports must be clear enough for a student/project demo.

They must explain:

- what problem the pipeline addresses: financial PDF table extraction to structured demo rows;
- what 345A/345B/345C/345C11/345D/345E contributed;
- why alias simulation increased normalization coverage from `0.452461` to `0.684136`;
- why strict demo-ready rows remain `109` despite alias simulated rows reaching `1532`;
- why `5558` rows are quality-limited and `9121` rows are excluded;
- what row-count closure proves: `109 + 5558 + 9121 = 14788`;
- what QA checks passed in 345E;
- what caveats remain: high/medium severity issues, missing unit count, remaining blind spots, simulated aliases not official rules;
- what can be safely presented;
- what must not be claimed;
- why formal/client/production gates remain false;
- what should happen next.

Reports must not claim:

- formal client export is ready;
- production readiness;
- official normalization rules were updated;
- all financial extraction quality issues are solved;
- all rows are reliable;
- alias simulation equals official rule mutation;
- 344G can proceed without a genuinely human-filled 344F workbook.

---

## Audience-specific outputs

### Stakeholder report

A general narrative report that explains:

- project objective
- current demo export result
- quantitative improvements
- QA status
- caveats
- recommended next steps

### Teacher brief

A concise classroom-friendly report, suitable for weekly/project presentation, focused on:

- what was completed
- what was verified
- what metrics improved
- what remains limited
- what the next task is

### Team update

A technical team-facing update, focused on:

- artifacts generated
- exact output paths
- row counts and QA status
- implementation boundaries
- tasks for frontend/report/UI teammates

### Interview project summary

A polished but truthful summary suitable for resume/interview preparation:

- project challenge
- architecture/process contribution
- validation/QA discipline
- metrics achieved
- honest caveats

Do not overclaim. The point is to sound competent, not like a startup homepage after too much caffeine.

### Frontend demo copy

Short UI copy that can appear near demo tables/cards:

- demo-only label
- coverage summary
- caveat badge text
- tooltip copy explaining simulated aliases
- warning text for quality-limited rows

---

## Claims allowed vs forbidden

Create a clear allowed/forbidden claims table.

Allowed examples:

- `Generated a full structured demo export package from 14,788 inventory rows.`
- `Validated row-count closure and demo-only gate safety.`
- `Alias simulation improved normalization coverage from 45.25% to 68.41%.`
- `Produced 109 strict demo-ready rows and separated 5,558 quality-limited rows from 9,121 excluded rows.`

Forbidden examples:

- `Production ready.`
- `Formal client export completed.`
- `Official alias rules updated.`
- `All extracted financial rows are correct.`
- `Human review pipeline is globally complete.`

---

## Manifest metrics

Manifest must include:

- `decision = DEMO_NARRATIVE_REPORT_PACKAGE_345F_READY`
- `input_stage = POST_345E_DEMO_NARRATIVE_REPORT_PACKAGE`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_345d_decision`
- `input_345e_decision`
- `demo_export_row_count`
- `quality_limited_row_count`
- `excluded_row_count`
- `inventory_row_count`
- `row_count_closure_passed`
- `coverage_ratio_before_alias_simulation`
- `coverage_ratio_after_alias_simulation`
- `baseline_normalized_demo_row_count`
- `alias_simulated_demo_row_count`
- `remaining_unnormalized_raw_metric_name_count`
- `remaining_unnormalized_metric_row_count`
- `high_severity_issue_count`
- `medium_severity_issue_count`
- `missing_unit_count`
- `gate_safety_check_passed`
- `caveat_completeness_passed`
- `presentation_ready_for_demo_only`
- `generated_report_count`
- `sample_rows_for_story_count`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `formal_export_generated = false`
- `demo_export_only = true`
- `milestone_ledger_updated`

All formal/client/production gates must remain false.

---

## Reports

Artifact index must list every generated file and its purpose.

Next plan must recommend one of:

- `345G Frontend Demo Sample Package`
- `345G Demo Presentation Slide Outline`
- `345G Demo Narrative QA Polish`
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists
- a separate official rule-update task only after explicit approval, not automatically from demo output

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/345F_demo_narrative_report_package.md`
- `datefac/benchmark/demo_narrative_report_package_345f.py`
- `datefac/benchmark/demo_narrative_report_package_345f_report.py`
- `tools/run_demo_narrative_report_package_345f.py`
- `tests/benchmark/test_demo_narrative_report_package_345f.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

The milestone ledger update is required for this task.

---

## Forbidden

Do not:

- create a new export dataset beyond bounded sample/story rows copied from 345E/345D
- modify normalization rules
- modify official alias assets
- apply alias decisions to upstream data
- modify 345E, 345D, or prior outputs
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
python -m py_compile datefac\benchmark\demo_narrative_report_package_345f.py datefac\benchmark\demo_narrative_report_package_345f_report.py tools\run_demo_narrative_report_package_345f.py tests\benchmark\test_demo_narrative_report_package_345f.py
python -m pytest tests\benchmark\test_demo_narrative_report_package_345f.py -q
python tools\run_demo_narrative_report_package_345f.py --full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d --demo-export-review-qa-checklist-345e-dir D:\_datefac\output\demo_export_review_qa_checklist_345e --output-dir D:\_datefac\output\demo_narrative_report_package_345f
```

Tests must verify:

- outputs exist
- decision is ready for valid 345D/345E fixtures
- QA is zero for valid fixtures
- input 345D/345E decisions and gates are validated
- narrative reports are generated
- allowed/forbidden claims report is generated
- metrics summary preserves 345D/345E numbers accurately
- sample story rows are copied, not mutated
- formal/client/production gates remain false
- official rules/assets modified flags remain false
- formal export generated flag remains false
- demo export only flag remains true
- milestone ledger is updated with a 345F entry
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
8. generated report count.
9. demo / quality-limited / excluded row counts.
10. coverage before / after alias simulation.
11. row-count closure result.
12. QA readiness summary.
13. sample rows for story count.
14. allowed/forbidden claims artifact status.
15. official rules/assets modified flags.
16. formal export generated / demo export only flags.
17. final gate status.
18. first file to open.
19. next recommended step.
20. `git status -sb`.
21. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/protected dirty files.
