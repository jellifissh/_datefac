# 342Q Preview Audit And Export Readiness Gate

## Goal

Audit the real `342P reviewed_plus_simulated_client_preview` output and decide whether it may proceed only to a bounded `342R audit-labeled export candidate package`.

342Q is:

- an audit gate
- a preview-boundary review
- an export-readiness risk screen

342Q is not:

- a formal client export
- final human-review completion
- real LLM review completion
- client-ready output
- production-ready output

## Required Inputs

- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p`
- `D:/_datefac/output/post_adoption_sidecar_simulation_342o`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`
- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i`
- `D:/_datefac/output/correction_aware_adoption_simulation_342n`

Key 342P artifacts:

- `reviewed_plus_simulated_client_preview_342p.xlsx`
- `reviewed_plus_simulated_client_preview_342p_summary.json`
- `reviewed_plus_simulated_client_preview_342p_qa.json`
- `reviewed_plus_simulated_client_preview_342p_report.md`

## Output Dir

- `D:/_datefac/output/preview_audit_export_readiness_gate_342q`

## Output Files

- `preview_audit_export_readiness_gate_342q.xlsx`
- `preview_audit_export_readiness_gate_342q_summary.json`
- `preview_audit_export_readiness_gate_342q_manifest.json`
- `preview_audit_export_readiness_gate_342q_qa.json`
- `preview_audit_export_readiness_gate_342q_report.md`
- `preview_audit_export_readiness_gate_342q_no_write_back_proof.json`

## Workbook Sheets

All sheet names must stay `<= 31` chars.

- `00_README`
- `01_AUDIT_SUMMARY`
- `02_INPUT_342P_SUMMARY`
- `03_PREVIEW_AUDIT`
- `04_TRUST_LEVEL_AUDIT`
- `05_SIM_BOUNDARY_AUDIT`
- `06_COLLISION_AUDIT`
- `07_DROPPED_DUP_AUDIT`
- `08_OVERRIDE_AUDIT`
- `09_EXPORT_RISK_GATE`
- `10_EXPORT_CANDIDATE_SCOPE`
- `11_REMAINING_BACKLOG`
- `12_342R_READINESS`
- `13_NO_WRITE_BACK`
- `14_NEXT_STEPS`

## Core Audit Questions

342Q must answer:

1. Whether the 342P combined preview structure is complete.
2. Whether `HUMAN_REVIEWED`, `SIMULATED_DIRECT`, and `SIMULATED_CORRECTED` remain explicitly separated.
3. Whether simulated rows keep `not_final_confirmation = true`.
4. Whether any simulated row was incorrectly marked final/client-ready/production-ready.
5. Whether 342P collision logging remains complete.
6. Whether dropped simulated duplicates stay outside the combined preview and 342R candidate scope.
7. Whether human-over-simulation override preserves human priority.
8. Whether 342P may proceed only to `342R audit_labeled_export_candidate_package`.
9. Whether `client_ready=false` and `production_ready=false` remain enforced.
10. Whether formal client export must still be blocked.

## Required Logic

### `03_PREVIEW_AUDIT`

Read `342P / 04_COMBINED_PREVIEW`.

Audit each row for:

- source type / trust-level alignment
- boundary warning presence
- `client_ready`
- `production_ready`
- simulated-row non-final boundary

Required row outputs:

- `audit_status = PASS / WARN / FAIL`
- `audit_reason`
- `included_in_export_candidate_scope`
- `export_candidate_allowed`
- `requires_disclaimer`
- `requires_later_audit`

Rules:

- `HUMAN_REVIEWED` may enter the bounded export-candidate scope, but still does not become formal client export.
- `SIMULATED_DIRECT` and `SIMULATED_CORRECTED` may only enter an audit-labeled candidate scope.
- Any `client_ready=true` or `production_ready=true` must fail.
- Any simulated row without `not_final_confirmation=true` must fail.
- Simulated rows must keep warning text that clearly signals simulation-only and later-audit boundaries.

### `04_TRUST_LEVEL_AUDIT`

Audit:

- `HUMAN_REVIEWED`
- `SIMULATED_DIRECT_ADOPTED`
- `SIMULATED_CORRECTION_ADOPTED`
- unknown trust levels
- trust/source mismatch
- missing warnings

### `05_SIM_BOUNDARY_AUDIT`

Audit simulated rows for:

- total simulated preview count
- `not_final_confirmation=true` count
- simulated final/client/production readiness violations
- warning completeness
- later-audit boundary coverage

### `06_COLLISION_AUDIT`

Read `342P / 09_COLLISION_CHECK`.

Track:

- `collision_logged_count`
- `duplicate_metric_year_source_count`
- `human_over_simulation_override_count`
- `unresolved_collision_count`
- `severe_collision_count`

Collision logging itself is not a failure. Unresolved collisions or human-priority violations are failures.

### `07_DROPPED_DUP_AUDIT`

Derive dropped rows from `342P / 06_SIM_DIRECT` and `07_SIM_CORRECTED` where `dropped_reason` is non-empty.

Verify:

- dropped simulated duplicate count is preserved
- dropped rows do not appear inside the combined preview
- dropped rows do not enter 342R candidate scope

### `08_OVERRIDE_AUDIT`

Verify all human-over-simulation overrides keep the human-reviewed row as winner.

### `09_EXPORT_RISK_GATE`

Always keep:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

If QA passes and combined preview exists:

- `export_candidate_scope_allowed = true`

Risk guidance:

- if simulated rows exist and collision counts are non-trivial, `export_risk_level` should be `HIGH`
- required disclaimers must stay explicit

### `10_EXPORT_CANDIDATE_SCOPE`

Build only a bounded candidate scope for `342R`.

Include:

- audit-passing human rows
- audit-warning simulated rows

Exclude:

- failed rows
- still-human-required rows
- dropped duplicates

### `11_REMAINING_BACKLOG`

Must carry:

- `still_human_required_count`
- `remaining_review_count`

Must explain that the current preview is still partial.

### `12_342R_READINESS`

If:

- `qa_fail_count = 0`
- export-candidate scope is allowed
- no-write-back proof passes
- no client/prod-ready violation exists
- combined preview is non-empty

Then:

- `ready_for_342r = true`
- `recommended_342r_scope = audit_labeled_export_candidate_package`

Else:

- `ready_for_342r = false`

## Summary Fields

At minimum:

- `human_reviewed_preview_count`
- `simulated_preview_count`
- `simulated_direct_preview_count`
- `simulated_corrected_preview_count`
- `combined_preview_row_count`
- `export_candidate_row_count`
- `unknown_trust_level_count`
- `trust_level_mismatch_count`
- `simulated_final_confirmed_true_count`
- `simulated_client_ready_true_count`
- `simulated_production_ready_true_count`
- `missing_display_warning_count`
- `collision_logged_count`
- `duplicate_metric_year_source_count`
- `human_over_simulation_override_count`
- `simulated_duplicate_dropped_count`
- `unresolved_collision_count`
- `severe_collision_count`
- `formal_client_export_allowed = false`
- `export_candidate_scope_allowed`
- `export_risk_level`
- `still_human_required_count`
- `remaining_review_count`
- `ready_for_342r`
- `recommended_342r_scope`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count`
- `decision`

## Decision Rules

If inputs are not ready or QA fails:

- `PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_NOT_READY`

If 342R gate conditions pass:

- `PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_READY`

## Report Requirements

The report must say:

- 342Q is a preview audit and export-readiness gate
- it audits 342P trust-level separation, simulation boundary, and collision handling
- it does not generate a formal client export
- `formal_client_export_allowed=false`
- `client_ready=false`
- `production_ready=false`
- only an audit-labeled 342R package may follow
- simulated rows still require disclaimer and later audit
- collision handling is logged but keeps preview risk non-trivial
- this output must not be used as investment advice

## Ledger Update

After completion, update:

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If ready:

- next task becomes `342R Audit-Labeled Export Candidate Package`

Must stay explicit:

- 342Q is not formal client export
- 342Q is not final human-review completion
- 342Q is not real LLM review completion
- 342Q is not client-ready
- 342Q is not production-ready

## Validation

```powershell
python -m py_compile datefac\benchmark\preview_audit_export_readiness_gate_342q.py datefac\benchmark\preview_audit_export_readiness_gate_342q_report.py tools\run_preview_audit_export_readiness_gate_342q.py tests\benchmark\test_preview_audit_export_readiness_gate_342q.py

python -m pytest tests\benchmark\test_preview_audit_export_readiness_gate_342q.py -q

python tools\run_preview_audit_export_readiness_gate_342q.py --reviewed-plus-preview-342p-dir D:\_datefac\output\reviewed_plus_simulated_client_preview_342p --post-adoption-sidecar-342o-dir D:\_datefac\output\post_adoption_sidecar_simulation_342o --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --post-human-sidecar-342i-dir D:\_datefac\output\table_first_post_human_review_sidecar_result_342i --adoption-simulation-342n-dir D:\_datefac\output\correction_aware_adoption_simulation_342n --output-dir D:\_datefac\output\preview_audit_export_readiness_gate_342q
```
