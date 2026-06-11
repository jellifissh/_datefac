# 342R Audit-Labeled Export Candidate Package

## Goal

Read the real `342Q preview_audit_export_readiness_gate` output and package its approved export-candidate scope into a bounded audit-labeled candidate package.

342R is:

- an audit-labeled export candidate package
- a bounded downstream handoff package
- a risk-disclosed preview-side artifact

342R is not:

- a formal client export
- final human-review completion
- real LLM review completion
- client-ready output
- production-ready output
- investment advice

## Required Inputs

- `D:/_datefac/output/preview_audit_export_readiness_gate_342q`
- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p`
- `D:/_datefac/output/post_adoption_sidecar_simulation_342o`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`

Key 342Q artifacts:

- `preview_audit_export_readiness_gate_342q.xlsx`
- `preview_audit_export_readiness_gate_342q_summary.json`
- `preview_audit_export_readiness_gate_342q_qa.json`
- `preview_audit_export_readiness_gate_342q_report.md`

342R must treat `342Q / 10_EXPORT_CANDIDATE_SCOPE` as the primary candidate source.
It must not rebuild candidate scope from scratch from `342P` or `342O`.

## Output Dir

- `D:/_datefac/output/audit_labeled_export_candidate_package_342r`

## Output Files

- `audit_labeled_export_candidate_package_342r.xlsx`
- `audit_labeled_export_candidate_package_342r_summary.json`
- `audit_labeled_export_candidate_package_342r_manifest.json`
- `audit_labeled_export_candidate_package_342r_qa.json`
- `audit_labeled_export_candidate_package_342r_report.md`
- `audit_labeled_export_candidate_package_342r_no_write_back_proof.json`

Optional companion artifacts:

- `audit_labeled_export_candidate_package_342r_candidates.csv`
- `audit_labeled_export_candidate_package_342r_metadata.json`

## Workbook Sheets

All sheet names must stay `<= 31` chars.

- `00_README`
- `01_PACKAGE_SUMMARY`
- `02_INPUT_342Q_SUMMARY`
- `03_EXPORT_CANDIDATES`
- `04_HUMAN_REVIEWED`
- `05_SIMULATED_DIRECT`
- `06_SIMULATED_CORRECTED`
- `07_AUDIT_LABELS`
- `08_REQUIRED_WARNINGS`
- `09_RISK_DISCLOSURE`
- `10_COLLISION_CONTEXT`
- `11_BACKLOG_CONTEXT`
- `12_342S_READINESS`
- `13_NO_WRITE_BACK`
- `14_NEXT_STEPS`

## Core Rules

### Candidate source

Use only `342Q / 10_EXPORT_CANDIDATE_SCOPE` as the package input scope.

342P / 342O / 342J may be used only for:

- context enrichment
- source trace preservation
- trust-level consistency validation
- risk / collision / backlog recap

### Required export-candidate fields

At minimum every packaged row must include:

- `export_candidate_row_id`
- `source_preview_row_id`
- `review_item_id`
- `metric_standardized`
- `year_standardized`
- `value_numeric`
- `normalized_unit`
- `data_trust_level`
- `export_scope_status`
- `display_warning`
- `required_disclaimer`
- `not_formal_client_export = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `package_row_status = INCLUDED_IN_AUDIT_LABELED_PACKAGE`
- `package_warning_level`
- `requires_later_audit`
- `source_stage = 342Q`
- `package_note`

If upstream context is available, also preserve:

- `upstream_source_stage`
- `preview_source_type`
- `review_status_for_client_display`
- `corpus_pdf_id`
- `file_name`
- `table_id`
- `table_type`
- `source_page`
- `bbox`
- `image_path`
- `evidence`
- `adoption_confidence`
- `adoption_evidence`
- `correction_pattern`
- `correction_reason`
- `original_metric_standardized`
- `original_normalized_unit`
- `collision_key`

Do not invent correction details when upstream fields are blank.

### Trust-level split

`04_HUMAN_REVIEWED`:

- rows where `data_trust_level = HUMAN_REVIEWED`

`05_SIMULATED_DIRECT`:

- rows where `data_trust_level = SIMULATED_DIRECT_ADOPTED`

`06_SIMULATED_CORRECTED`:

- rows where `data_trust_level = SIMULATED_CORRECTION_ADOPTED`

### Audit labels

Mapping:

- `HUMAN_REVIEWED -> AUDIT_LABEL_HUMAN_REVIEWED / REVIEWED_PILOT`
- `SIMULATED_DIRECT_ADOPTED -> AUDIT_LABEL_SIMULATED_DIRECT / SIMULATION_ONLY`
- `SIMULATED_CORRECTION_ADOPTED -> AUDIT_LABEL_SIMULATED_CORRECTED / SIMULATION_CORRECTED_ONLY`

### Warnings and risk disclosure

The package must stay explicit that:

- formal client export is not allowed
- `client_ready=false`
- `production_ready=false`
- simulated rows require later audit
- `export_risk_level = HIGH`
- `887 rows remain outside current reviewed/simulated scope`

### Collision context

Carry forward:

- `collision_logged_count = 99`
- `duplicate_metric_year_source_count = 99`
- `human_over_simulation_override_count = 9`
- `simulated_duplicate_dropped_count = 79`
- `unresolved_collision_count = 0`
- `severe_collision_count = 20`

Collision context is risk evidence, not a license to ignore audit labels.

### Backlog context

Carry forward:

- `still_human_required_count = 66`
- `remaining_review_count = 887`

### 342S readiness

Only if all of the following hold:

- `qa_fail_count = 0`
- package row count is positive
- package row count equals `342Q export_candidate_row_count`
- no row has `final_confirmed = true`
- no row has `client_ready = true`
- no row has `production_ready = true`
- all simulated rows require later audit
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- no-write-back proof passes

Then:

- `ready_for_342s = true`
- `recommended_342s_scope = package_audit_snapshot_or_demo_handoff`
- `decision = AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_READY`

Else:

- `ready_for_342s = false`
- `decision = AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_NOT_READY`

## Summary Fields

At minimum:

- `export_candidate_package_row_count`
- `human_reviewed_candidate_count`
- `simulated_candidate_count`
- `simulated_direct_candidate_count`
- `simulated_corrected_candidate_count`
- `formal_client_export_allowed = false`
- `export_candidate_scope_allowed = true`
- `export_risk_level = HIGH`
- `collision_logged_count`
- `duplicate_metric_year_source_count`
- `severe_collision_count`
- `human_over_simulation_override_count`
- `simulated_duplicate_dropped_count`
- `still_human_required_count`
- `remaining_review_count`
- `disclaimer_required_count`
- `later_audit_required_count`
- `package_row_fail_count`
- `ready_for_342s`
- `recommended_342s_scope`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count`
- `decision`

## QA Requirements

Required checks:

- 342Q input exists
- 342Q decision is ready
- 342Q `ready_for_342r = true`
- 342Q `qa_fail_count = 0`
- 342Q `export_candidate_scope_allowed = true`
- 342Q `formal_client_export_allowed = false`
- export candidate rows loaded
- package row count equals `342Q export_candidate_row_count`
- trust levels are valid
- no row `final_confirmed = true`
- no row `client_ready = true`
- no row `production_ready = true`
- simulated rows require later audit
- required disclaimers exist
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- no upstream workbook modified
- no production pipeline / parser / extraction / delivery modified
- no output artifacts staged
- no optional input artifacts staged
- no investment advice claim
- all sheet names `<= 31`
- no-write-back proof generated

## Report Requirements

The report must state:

- 342R is an audit-labeled export candidate package
- it is not a formal client export
- it is based on the 130-row 342Q export-candidate scope
- `HUMAN_REVIEWED` and `SIMULATED_*` rows remain explicitly separated
- simulated rows still require later audit
- `export_risk_level = HIGH`
- `formal_client_export_allowed=false`
- `client_ready=false`
- `production_ready=false`
- `887 rows remain outside current scope`
- next step is `342S package audit snapshot or demo handoff`
- the package must not be treated as formal client delivery or investment advice

## Ledger Update

After completion, update:

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If ready:

- next task becomes `342S Package Audit Snapshot Or Demo Handoff`

Keep explicit:

- 342R is not formal client export
- 342R is not final human-review completion
- 342R is not real LLM review completion
- 342R is not client-ready
- 342R is not production-ready

## Validation

```powershell
python -m py_compile datefac\benchmark\audit_labeled_export_candidate_package_342r.py datefac\benchmark\audit_labeled_export_candidate_package_342r_report.py tools\run_audit_labeled_export_candidate_package_342r.py tests\benchmark\test_audit_labeled_export_candidate_package_342r.py

python -m pytest tests\benchmark\test_audit_labeled_export_candidate_package_342r.py -q

python tools\run_audit_labeled_export_candidate_package_342r.py --preview-audit-342q-dir D:\_datefac\output\preview_audit_export_readiness_gate_342q --reviewed-plus-preview-342p-dir D:\_datefac\output\reviewed_plus_simulated_client_preview_342p --post-adoption-sidecar-342o-dir D:\_datefac\output\post_adoption_sidecar_simulation_342o --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --output-dir D:\_datefac\output\audit_labeled_export_candidate_package_342r
```
