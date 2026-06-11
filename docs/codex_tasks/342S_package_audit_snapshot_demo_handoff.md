# 342S Package Audit Snapshot Or Demo Handoff

## Goal

Read the real `342R audit_labeled_export_candidate_package` output and turn the current mainline result into a bounded snapshot / demo handoff package.

342S is:

- a package audit snapshot
- a demo handoff package
- an internal milestone recap artifact

342S is not:

- a formal client export
- final human-review completion
- real LLM review completion
- client-ready delivery
- production-ready delivery
- investment advice

## Required Inputs

- `D:/_datefac/output/audit_labeled_export_candidate_package_342r`
- `D:/_datefac/output/preview_audit_export_readiness_gate_342q`
- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p`
- `D:/_datefac/output/post_adoption_sidecar_simulation_342o`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`

Key 342R artifacts:

- `audit_labeled_export_candidate_package_342r.xlsx`
- `audit_labeled_export_candidate_package_342r_summary.json`
- `audit_labeled_export_candidate_package_342r_qa.json`
- `audit_labeled_export_candidate_package_342r_report.md`
- `audit_labeled_export_candidate_package_342r_candidates.csv`
- `audit_labeled_export_candidate_package_342r_metadata.json`

342S must treat 342R as the primary source.
342Q / 342P / 342O / 342J are supporting context only.

## Output Dir

- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s`

## Output Files

- `package_audit_snapshot_demo_handoff_342s.xlsx`
- `package_audit_snapshot_demo_handoff_342s_summary.json`
- `package_audit_snapshot_demo_handoff_342s_manifest.json`
- `package_audit_snapshot_demo_handoff_342s_qa.json`
- `package_audit_snapshot_demo_handoff_342s_report.md`
- `package_audit_snapshot_demo_handoff_342s_no_write_back_proof.json`
- `package_audit_snapshot_demo_handoff_342s_demo_readme.md`
- `package_audit_snapshot_demo_handoff_342s_handoff_checklist.md`
- `package_audit_snapshot_demo_handoff_342s_artifact_index.json`
- `package_audit_snapshot_demo_handoff_342s_next_step_plan.md`

## Workbook Sheets

All sheet names must stay `<= 31` chars.

- `00_README`
- `01_SNAPSHOT_SUMMARY`
- `02_MILESTONE_CHAIN`
- `03_KEY_ARTIFACTS`
- `04_DEMO_GUIDE`
- `05_PACKAGE_OVERVIEW`
- `06_TRUST_LEVELS`
- `07_RISK_BOUNDARY`
- `08_COLLISION_SUMMARY`
- `09_BACKLOG_SUMMARY`
- `10_HANDOFF_CHECKLIST`
- `11_NEXT_STEP_OPTIONS`
- `12_343A_READINESS`
- `13_NO_WRITE_BACK`
- `14_NEXT_STEPS`

## Core Logic

### Snapshot scope

342S must answer:

1. What the current MinerU-first / table-first mainline has completed from 342C6 through 342R
2. Which artifacts should be opened first for demo or audit handoff
3. How the 130-row package is split across trust levels
4. Why `export_risk_level = HIGH`
5. Why `formal_client_export_allowed=false`
6. Why `client_ready=false` and `production_ready=false`
7. What `still_human_required_count = 66` and `remaining_review_count = 887` imply
8. What the recommended next step should be

### Required summary fields

At minimum:

- `latest_completed_milestone = 342R`
- `current_milestone = 342S`
- `current_mainline = MinerU-first / table-first`
- `export_candidate_package_row_count = 130`
- `human_reviewed_candidate_count = 30`
- `simulated_candidate_count = 100`
- `simulated_direct_candidate_count = 61`
- `simulated_corrected_candidate_count = 39`
- `disclaimer_required_count = 100`
- `later_audit_required_count = 100`
- `export_risk_level = HIGH`
- `collision_logged_count = 99`
- `duplicate_metric_year_source_count = 99`
- `severe_collision_count = 20`
- `unresolved_collision_count = 0`
- `human_over_simulation_override_count = 9`
- `simulated_duplicate_dropped_count = 79`
- `still_human_required_count = 66`
- `remaining_review_count = 887`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `demo_handoff_ready`
- `ready_for_343a`
- `recommended_343a_scope`
- `qa_fail_count`
- `decision`

### Milestone chain

`02_MILESTONE_CHAIN` must include:

- 342C6 effective MinerU pilot success baseline
- 342D parser ensemble compare completed
- 342E table-first audit completed and old text-candidate route superseded
- 342F table-first long-form extraction completed
- 342G extraction review package completed
- 342H reviewed apply simulation completed
- 342I post-human-review sidecar completed
- 342J reviewed client preview pilot completed
- 342K LLM-assisted adjudication pilot completed as dry-run helper
- 342L suggestion-apply simulation completed
- 342M reviewed spot-check gate completed
- 342N correction-aware adoption simulation completed
- 342O post-adoption sidecar simulation completed
- 342P reviewed plus simulated preview completed
- 342Q preview audit gate completed
- 342R audit-labeled export candidate package completed
- 342S current snapshot / handoff stage

Each row must include:

- `milestone_id`
- `milestone_name`
- `status`
- `decision`
- `key_output`
- `key_risk_or_boundary`
- `next_dependency`

### Artifact index

`03_KEY_ARTIFACTS` must include at least:

- 342R workbook
- 342R candidates csv
- 342R report
- 342Q workbook
- 342P workbook
- 342O workbook
- 342J workbook
- `PROJECT_MILESTONE_LEDGER_项目进程.md`

342R workbook must be highest priority:

- `D:/_datefac/output/audit_labeled_export_candidate_package_342r/audit_labeled_export_candidate_package_342r.xlsx`

Recommended sheets:

- `03_EXPORT_CANDIDATES`
- `07_AUDIT_LABELS`
- `08_REQUIRED_WARNINGS`
- `09_RISK_DISCLOSURE`
- `10_COLLISION_CONTEXT`
- `11_BACKLOG_CONTEXT`
- `12_342S_READINESS`

### Risk boundary

342S must preserve:

- `export_risk_level = HIGH`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- no investment advice
- no full human-review completion claim
- no real LLM review completion claim
- no production-ready claim
- no final client delivery claim

Risk reasons must include:

- `package contains 100 simulated rows`
- `100 rows require disclaimer`
- `100 rows require later audit`
- `duplicate_metric_year_source_count = 99`
- `severe_collision_count = 20`
- `remaining_review_count = 887`
- `still_human_required_count = 66`

### Next step options

`11_NEXT_STEP_OPTIONS` must include:

- `343A Review Queue Schema And Human Review UI Pilot`
- `343B Argilla Human Review UI Pilot`
- `343C Real LLM/VLM Response Ingestion Pilot`
- `343D Phoenix Observability Trace Pilot`
- manual review expansion / larger spot-check route

Current recommendation:

- `343A Review Queue Schema And Human Review UI Pilot`

Not recommended right now:

- immediate lakeFS adoption
- large LangGraph rewrite
- Dify as the core pipeline

## Readiness Rule

If all of the following hold:

- 342R input exists
- 342R decision is ready
- 342R `ready_for_342s = true`
- 342R `qa_fail_count = 0`
- supporting 342Q / 342P / 342O / 342J context exists
- 342R workbook loads
- 342R counts are internally consistent
- demo guide generated
- artifact index generated
- handoff checklist generated
- no-write-back proof passes
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

Then:

- `demo_handoff_ready = true`
- `ready_for_343a = true`
- `recommended_343a_scope = review_queue_schema_and_human_review_ui_pilot`
- `decision = PACKAGE_AUDIT_SNAPSHOT_DEMO_HANDOFF_342S_READY`

Else:

- `ready_for_343a = false`
- `decision = PACKAGE_AUDIT_SNAPSHOT_DEMO_HANDOFF_342S_NOT_READY`

## QA Requirements

Required checks:

- 342R input exists
- 342R decision is ready
- 342R `ready_for_342s = true`
- 342R `qa_fail_count = 0`
- 342R workbook loaded
- 342R required sheets exist
- supporting 342Q / 342P / 342O / 342J ready summaries exist
- 342R workbook counts match summary
- trust split matches summary
- risk boundary preserved
- demo guide generated
- artifact index generated
- handoff checklist generated
- `formal_client_export_allowed = false`
- no `client_ready = true`
- no `production_ready = true`
- no final delivery claim
- no investment advice claim
- no upstream workbook modified
- no production pipeline / parser / extraction / delivery modified
- no output artifacts staged
- no optional input artifacts staged
- all sheet names `<= 31`
- no-write-back proof generated

## Report Requirements

The report must say:

- 342S is a package audit snapshot / demo handoff
- it is based on 342R
- the current package has 130 candidate rows
- 30 rows are `HUMAN_REVIEWED`
- 100 rows are `SIMULATED`
- simulated rows require disclaimer / later audit
- `export_risk_level = HIGH`
- `formal_client_export_allowed=false`
- `client_ready=false`
- `production_ready=false`
- `887 rows remain outside current package`
- `66 adoption candidates still human required`
- this stage is usable for internal demo / audit recap / handoff
- this stage is not formal client delivery or investment advice
- recommended next task is `343A Review Queue Schema And Human Review UI Pilot`

## Ledger Update

After completion update:

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Must make clear:

- 342S is not formal client export
- 342S is not final human-review completion
- 342S is not real LLM review completion
- 342S is not `client_ready` or `production_ready`
- 342S is a package audit snapshot / demo handoff

## Validation

```powershell
python -m py_compile datefac\benchmark\package_audit_snapshot_demo_handoff_342s.py datefac\benchmark\package_audit_snapshot_demo_handoff_342s_report.py tools\run_package_audit_snapshot_demo_handoff_342s.py tests\benchmark\test_package_audit_snapshot_demo_handoff_342s.py

python -m pytest tests\benchmark\test_package_audit_snapshot_demo_handoff_342s.py -q

python tools\run_package_audit_snapshot_demo_handoff_342s.py --audit-labeled-package-342r-dir D:\_datefac\output\audit_labeled_export_candidate_package_342r --preview-audit-342q-dir D:\_datefac\output\preview_audit_export_readiness_gate_342q --reviewed-plus-preview-342p-dir D:\_datefac\output\reviewed_plus_simulated_client_preview_342p --post-adoption-sidecar-342o-dir D:\_datefac\output\post_adoption_sidecar_simulation_342o --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --output-dir D:\_datefac\output\package_audit_snapshot_demo_handoff_342s
```
