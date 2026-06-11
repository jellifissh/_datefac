# 343A：Review Queue Schema And Human Review UI Pilot

## 1. Positioning

343A starts the 343-series after the 342S snapshot/handoff milestone. The goal is to define a durable Review Queue schema that can support future human review, spot-checking, high-risk sample handling, an Argilla pilot, Excel round-trip, and a future custom review UI.

343A is a schema and pilot-package task. It is not a production UI implementation, not an Argilla integration, not a formal client export, and not an upstream extraction rerun.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/342S_package_audit_snapshot_demo_handoff.md`
- 342S output summary / qa / report / demo README / handoff checklist
- 342R output summary / qa / workbook
- 342Q output summary / qa / workbook
- recent git log and current git status

Expected current state:

- latest completed milestone = `342S Package Audit Snapshot Or Demo Handoff`
- latest known commit = `db7d03731f56a38afd7aa712aa835733a9347a79`
- current mainline = `MinerU-first / table-first`
- 342S decision = `PACKAGE_AUDIT_SNAPSHOT_DEMO_HANDOFF_342S_READY`
- ready_for_343a = `true`
- recommended_343a_scope = `review_queue_schema_and_human_review_ui_pilot`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- qa_fail_count = `0`

## 3. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not fake real LLM responses. Do not require a new manual workbook fill in this task. Do not implement full Argilla or a full frontend UI. Do not modify production pipeline, parser, extraction, or delivery code. Do not write back to upstream workbooks. Do not generate formal client export. Preserve `formal_client_export_allowed=false`, `client_ready=false`, and `production_ready=false`.

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or the protected dirty files listed in the ledger/status. Use precise file staging only.

## 4. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343A_review_queue_schema_and_human_review_ui_pilot.md`
- `datefac/review_queue/__init__.py`
- `datefac/review_queue/schema_343a.py`
- `datefac/benchmark/review_queue_schema_343a.py`
- `datefac/benchmark/review_queue_schema_343a_report.py`
- `tools/run_review_queue_schema_343a.py`
- `tests/benchmark/test_review_queue_schema_343a.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If the repository already has a better non-production schema location, follow it, but keep production pipeline/parser/extraction/delivery untouched.

## 5. Inputs

Input directories:

- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s`
- `D:/_datefac/output/audit_labeled_export_candidate_package_342r`
- `D:/_datefac/output/preview_audit_export_readiness_gate_342q`
- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p`

Primary files:

- 342S summary / qa / report / demo README
- 342R workbook and summary
- 342Q summary
- 342P summary

Expected 342S values include: current mainline `MinerU-first / table-first`, 130 export candidate package rows, 30 human reviewed candidates, 100 simulated candidates, 100 disclaimer-required rows, 100 later-audit-required rows, export risk `HIGH`, 99 logged collisions, 20 severe collisions, 66 still-human-required rows, 887 remaining review rows, and all formal/client/production readiness flags false.

## 6. Outputs

Output directory:

`D:/_datefac/output/review_queue_schema_343a`

Output files:

- `review_queue_schema_343a.xlsx`
- `review_queue_schema_343a_summary.json`
- `review_queue_schema_343a_manifest.json`
- `review_queue_schema_343a_qa.json`
- `review_queue_schema_343a_report.md`
- `review_queue_schema_343a_schema.json`
- `review_queue_schema_343a_json_schema.json`
- `review_queue_schema_343a_excel_template_spec.json`
- `review_queue_schema_343a_argilla_mapping.json`
- `review_queue_schema_343a_ui_contract.md`
- `review_queue_schema_343a_sample_items.jsonl`
- `review_queue_schema_343a_no_write_back_proof.json`

All outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_SCHEMA_SUMMARY`
- `02_INPUT_342S_SUMMARY`
- `03_QUEUE_FIELDS`
- `04_STATUS_LIFECYCLE`
- `05_REASON_CODES`
- `06_PRIORITY_RULES`
- `07_TRUST_MAPPING`
- `08_SAMPLE_QUEUE_ITEMS`
- `09_EXCEL_TEMPLATE`
- `10_ARGILLA_MAPPING`
- `11_UI_CONTRACT`
- `12_BACKLOG_STRATEGY`
- `13_343B_READINESS`
- `14_NO_WRITE_BACK`
- `15_NEXT_STEPS`

## 7. Review Queue schema

Define fields grouped as:

1. Identity: `queue_item_id`, `review_item_id`, `source_stage`, `source_commit_sha`, `source_artifact_path`, `source_artifact_sheet`, `source_row_id`.
2. Document/table provenance: `source_pdf_id`, `source_pdf_path`, `page_number`, `table_id`, `cell_id`, `bbox`, `image_path`, `source_html_snippet`, `source_text_snippet`.
3. Candidate value: `metric_candidate_raw`, `metric_standardized`, `year_standardized`, `value_numeric`, `normalized_unit`, `original_metric_standardized`, `original_normalized_unit`, `correction_pattern`, `correction_reason`.
4. Trust/risk: `data_trust_level`, `audit_label`, `preview_source_type`, `risk_level`, `risk_tags`, `queue_reason_code`, `confidence_score`, `collision_group_id`, `requires_disclaimer`, `requires_later_audit`, `formal_client_export_allowed`, `client_ready`, `production_ready`, `not_final_confirmation`.
5. Review workflow: `review_status`, `review_priority`, `assigned_reviewer_id`, `reviewer_decision`, `reviewer_metric_standardized`, `reviewer_year_standardized`, `reviewer_value_numeric`, `reviewer_normalized_unit`, `reviewer_note`, `reviewed_at`, `review_round`.
6. Output/application control: `apply_allowed`, `apply_target`, `applied_at`, `applied_by`, `apply_batch_id`, `no_write_back_required`, `audit_log_ref`.

For every field, define: name, group, data type, Excel requirement, Argilla requirement, future UI requirement, allowed values, nullability, default value, description, example, and validation rule.

## 8. Lifecycle, reason codes, and priority

Lifecycle statuses:

- `CREATED`
- `QUEUED`
- `ASSIGNED`
- `IN_REVIEW`
- `REVIEWED_CONFIRMED`
- `REVIEWED_CORRECTED`
- `REJECTED`
- `NEEDS_SOURCE_CHECK`
- `NEEDS_ESCALATION`
- `SKIPPED`
- `READY_FOR_APPLY_SIMULATION`
- `APPLIED_TO_SIDECAR_SIMULATION`
- `ARCHIVED`

Define valid transitions, without implementing production apply logic.

Reason codes:

- `STILL_HUMAN_REQUIRED`
- `SIMULATED_REQUIRES_LATER_AUDIT`
- `SEVERE_COLLISION`
- `DUPLICATE_METRIC_YEAR_SOURCE`
- `LOW_CONFIDENCE`
- `UNIT_METRIC_MISMATCH`
- `YEAR_ALIGNMENT_RISK`
- `VALUE_OUTLIER`
- `NEW_TEMPLATE_OR_LAYOUT`
- `RANDOM_SPOT_CHECK`
- `REGRESSION_FAILURE`
- `BACKLOG_REVIEW`

Priority levels:

- `P0_BLOCKER`
- `P1_HIGH_RISK`
- `P2_STANDARD_REVIEW`
- `P3_SPOT_CHECK`
- `P4_BACKLOG`

## 9. Trust mapping

Map existing trust levels:

- `HUMAN_REVIEWED`
- `SIMULATED_DIRECT_ADOPTED`
- `SIMULATED_CORRECTION_ADOPTED`

Rules:

- human-reviewed rows may be shown in demo but are still not formal export rows
- simulated rows may be shown only with disclaimer and require later audit
- all rows keep formal/client/production readiness flags false in this task

## 10. Sample queue generation

Use 342R workbook sheet `03_EXPORT_CANDIDATES` as the primary source when available.

Generate a deterministic sample queue, not a full production review workload:

- up to 10 human-reviewed rows
- up to 20 simulated-direct rows
- up to 20 simulated-corrected rows
- summary-derived placeholder rows only when row-level severe-collision/backlog details are unavailable

Do not fabricate detailed dropped-duplicate or severe-collision rows. If only summary data exists, mark those samples with `source_detail_level = SUMMARY_DERIVED` and include a caveat.

## 11. Excel, Argilla, and future UI specs

Generate:

- an Excel template spec for human review round-trip
- an Argilla mapping JSON, but do not call Argilla or import its SDK
- a future UI contract Markdown describing list view, detail view, review actions, validation rules, export contract, and audit log expectations

Argilla must be treated as a pluggable review interface, not the main system.

## 12. Readiness and decision

If QA passes, set:

- `decision = REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_READY`
- `ready_for_343b = true`
- `recommended_343b_scope = argilla_human_review_ui_pilot`

If QA fails, set:

- `decision = REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_NOT_READY`
- `ready_for_343b = false`

Summary JSON must include: schema version, field counts, status count, reason code count, priority count, sample queue item counts, generated mapping/spec flags, formal/client/production readiness flags, ready_for_343b, recommended scope, qa_fail_count, and no-write-back proof status.

## 13. QA requirements

Check that:

- 342S input exists and is ready
- 342R workbook/summary exists
- schema fields, lifecycle, reason codes, priorities, trust mapping, sample queue, Excel spec, Argilla mapping, and UI contract are generated
- no formal/client/production readiness flag is true
- no simulated row is treated as final confirmed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 14. Report

Generate `review_queue_schema_343a_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343A defines a durable Review Queue schema
- it does not implement full Argilla or a full UI
- Review Queue is the stable core and Argilla is only a pluggable interface
- how 342R/342S outputs map into review items
- how trust levels, reason codes, statuses, priorities, and reviewer decisions work
- why formal client export remains forbidden
- recommended next step: 343B Argilla pilot or Excel round-trip pilot

## 15. Ledger update

Update the project milestone ledger with:

- 343A completed
- status
- inputs
- outputs
- key metrics
- QA result
- decision
- next recommended task

If ready_for_343b is true, recommend `343B Argilla Human Review UI Pilot` or `343B Excel Round-trip Review Queue Pilot`, with a short rationale.

## 16. Validation commands

Run py_compile, pytest, and the real runner:

```powershell
python -m py_compile datefac\review_queue\schema_343a.py datefac\benchmark\review_queue_schema_343a.py datefac\benchmark\review_queue_schema_343a_report.py tools\run_review_queue_schema_343a.py tests\benchmark\test_review_queue_schema_343a.py
python -m pytest tests\benchmark\test_review_queue_schema_343a.py -q
python tools\run_review_queue_schema_343a.py --snapshot-342s-dir D:\_datefac\output\package_audit_snapshot_demo_handoff_342s --audit-labeled-package-342r-dir D:\_datefac\output\audit_labeled_export_candidate_package_342r --preview-audit-342q-dir D:\_datefac\output\preview_audit_export_readiness_gate_342q --reviewed-plus-preview-342p-dir D:\_datefac\output\reviewed_plus_simulated_client_preview_342p --output-dir D:\_datefac\output\review_queue_schema_343a
```

## 17. Precise staging

Stage only:

- `docs/codex_tasks/343A_review_queue_schema_and_human_review_ui_pilot.md`
- `datefac/review_queue/__init__.py`
- `datefac/review_queue/schema_343a.py`
- `datefac/benchmark/review_queue_schema_343a.py`
- `datefac/benchmark/review_queue_schema_343a_report.py`
- `tools/run_review_queue_schema_343a.py`
- `tests/benchmark/test_review_queue_schema_343a.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Commit message:

`Add 343A review queue schema pilot`

Push to `origin/main`.

## 18. Completion report

Report in Chinese:

1. 343A commit sha
2. decision
3. review_queue_schema_version
4. field_count
5. required_field_count
6. status_count
7. reason_code_count
8. priority_level_count
9. sample_queue_item_count
10. human_reviewed_sample_count
11. simulated_sample_count
12. summary_derived_sample_count
13. argilla_mapping_generated
14. excel_template_spec_generated
15. ui_contract_generated
16. formal_client_export_allowed
17. client_ready
18. production_ready
19. ready_for_343b
20. recommended_343b_scope
21. qa_fail_count
22. no-write-back proof 是否通过
23. 最该打开哪个 Excel
24. 最该打开哪个 schema/json/ui contract artifact
25. 是否已更新 PROJECT_MILESTONE_LEDGER_项目进程.md
26. 是否没有提交 output/temp/input reviewed workbook/LLM response/受保护脏文件
## 19. Implementation note

343A must remain a read-only schema and pilot-package task. Do not silently expand it into production apply logic, full Argilla integration, or a full frontend rewrite inside this task.
