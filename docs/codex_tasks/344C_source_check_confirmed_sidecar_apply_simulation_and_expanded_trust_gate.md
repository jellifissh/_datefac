# 344C：Source-check Confirmed Sidecar Apply Simulation And Expanded Trust Gate

## 1. Positioning

344C consumes the 344B source-check evidence review ingestion outputs and simulates applying the 19 source-check resolved rows into an expanded trusted sidecar set.

343O closed a 10-row trusted demo arc. 344B resolved the remaining 19 source-check backlog rows as sidecar review results. 344C combines those two audited scopes into an expanded trusted-coverage simulation and generates an expanded trust gate.

344C is a sidecar apply simulation and expanded trust-gate task. It is not production apply, not formal client export, not global client export, not Argilla integration, not frontend work, not real LLM/VLM review, and not an upstream extraction rerun.

Important scope boundary: 344C may simulate expanded trusted coverage across 29 reviewed candidate rows, but it must not write back to production data or generate formal client export.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/344B_source_check_evidence_review_result_ingestion.md`
- 344B summary / QA / result JSONL / validated sidecar / corrections / audit gate / scope boundary
- 344A2 summary / evidence map / enriched backlog items
- 343O summary / handoff summary / trust chain / artifact index / export gate snapshot
- 343N demo export package / export rows / audit labels / export gate
- 343M sidecar simulation / limited export candidate / limited gate
- 343L pure-human attestation ingestion result
- 343A schema artifacts
- current git status

Expected current state:

- latest completed milestone = `344B Source-check Evidence Review Result Ingestion`
- 344B decision = `SOURCE_CHECK_EVIDENCE_REVIEW_INGESTION_344B_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- filled_row_count = `19`
- valid_row_count = `19`
- invalid_row_count = `0`
- source_confirm_count = `10`
- source_correct_count = `9`
- source_reject_count = `0`
- source_still_insufficient_count = `0`
- source_defer_count = `0`
- validated_sidecar_row_count = `19`
- correction_row_count = `9`
- source_check_result_ingested = `true`
- source_check_backlog_resolved = `true`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- global_strict_human_review_completed = `false`
- ready_for_344c = `true`
- recommended_344c_scope = `source_check_confirmed_sidecar_apply_simulation_and_expanded_trust_gate`
- qa_fail_count = `0`

Expected 343O closed demo scope:

- demo_arc_closed = `true`
- input_demo_export_row_count = `10`
- audit_label_row_count = `10`
- limited_export_scope = `343K_PACKAGE_ONLY`
- export_usage = `DEMO_ONLY`
- formal_client_export_allowed = `false`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun MinerU, PPStructure, VLM, OCR, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, delivery, approval, or formal export code. Do not write back to upstream workbooks. Do not perform real production apply. Do not generate formal client export.

344C may only generate a sidecar apply simulation and expanded trust gate under its own output directory.

Formal/global export boundary must remain conservative:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Allowed scoped flags:

- `source_check_sidecar_apply_simulation_completed = true` if simulation succeeds
- `expanded_trust_gate_evaluated = true` if gate is generated
- `expanded_trusted_candidate_count = 29` if 10 demo rows + 19 source-check resolved rows are valid and deduplicated
- `source_check_backlog_resolved = true` may be carried forward from 344B
- `expanded_trusted_scope = 343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/344C_source_check_confirmed_sidecar_apply_simulation_and_expanded_trust_gate.md`
- `datefac/review_queue/source_check_sidecar_simulation_344c.py`
- `datefac/benchmark/review_queue_source_check_sidecar_simulation_344c.py`
- `datefac/benchmark/review_queue_source_check_sidecar_simulation_344c_report.py`
- `tools/run_review_queue_source_check_sidecar_simulation_344c.py`
- `tests/benchmark/test_review_queue_source_check_sidecar_simulation_344c.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o`
- `D:/_datefac/output/review_queue_limited_demo_export_package_343n`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m`
- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l`
- `D:/_datefac/output/review_queue_schema_343a`

Required 344B files:

- `review_queue_source_check_evidence_review_ingestion_344b_summary.json`
- `review_queue_source_check_evidence_review_ingestion_344b_qa.json`
- `review_queue_source_check_evidence_review_ingestion_344b_result.jsonl`
- `review_queue_source_check_evidence_review_ingestion_344b_validated_sidecar.jsonl`
- `review_queue_source_check_evidence_review_ingestion_344b_corrections.jsonl`
- `review_queue_source_check_evidence_review_ingestion_344b_audit_gate.json`
- `review_queue_source_check_evidence_review_ingestion_344b_scope_boundary.md`
- `review_queue_source_check_evidence_review_ingestion_344b_no_write_back_proof.json`

Required 343O/343N references:

- `review_queue_demo_audit_snapshot_343o_summary.json`
- `review_queue_demo_audit_snapshot_343o_export_gate_snapshot.json`
- `review_queue_limited_demo_export_package_343n_export_rows.jsonl`
- `review_queue_limited_demo_export_package_343n_audit_labels.jsonl`
- `review_queue_limited_demo_export_package_343n_export_gate.json`

If 344B is missing or not ready, fail gracefully. Do not fabricate source-check sidecar rows.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c`

Output files:

- `review_queue_source_check_sidecar_simulation_344c.xlsx`
- `review_queue_source_check_sidecar_simulation_344c_summary.json`
- `review_queue_source_check_sidecar_simulation_344c_manifest.json`
- `review_queue_source_check_sidecar_simulation_344c_qa.json`
- `review_queue_source_check_sidecar_simulation_344c_report.md`
- `review_queue_source_check_sidecar_simulation_344c_source_check_apply_plan.jsonl`
- `review_queue_source_check_sidecar_simulation_344c_source_check_applied_sidecar.jsonl`
- `review_queue_source_check_sidecar_simulation_344c_expanded_trusted_candidates.jsonl`
- `review_queue_source_check_sidecar_simulation_344c_corrections_applied.jsonl`
- `review_queue_source_check_sidecar_simulation_344c_dedup_audit.jsonl`
- `review_queue_source_check_sidecar_simulation_344c_expanded_trust_gate.json`
- `review_queue_source_check_sidecar_simulation_344c_scope_boundary.md`
- `review_queue_source_check_sidecar_simulation_344c_no_write_back_proof.json`

Optional but recommended if lightweight:

- `review_queue_source_check_sidecar_simulation_344c_expanded_trust_summary.md`
- `review_queue_source_check_sidecar_simulation_344c_next_action_plan.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_SIM_SUMMARY`
- `02_INPUT_344B_SUMMARY`
- `03_SOURCE_CHECK_SIDECAR`
- `04_CORRECTIONS_APPLIED`
- `05_EXPANDED_TRUSTED`
- `06_DEDUP_AUDIT`
- `07_EXPANDED_GATE`
- `08_SCOPE_BOUNDARY`
- `09_NO_WRITE_BACK`
- `10_NEXT_STEPS`

## 8. Core logic

### 8.1 Read and validate 344B state

Read 344B summary, QA, result JSONL, validated sidecar, corrections, audit gate, scope boundary, and no-write-back proof.

Validate:

- 344B is ready
- 19 filled rows were valid
- invalid row count is 0
- source-check result was ingested
- source-check backlog was resolved
- validated sidecar row count is 19
- correction row count is 9
- formal/client/production readiness flags remain false

### 8.2 Read 343O/343N trusted demo rows

Read the 10 demo rows from the 343N demo export rows and cross-check with 343O summary/gate.

Validate:

- 343O demo arc is closed
- 343N demo export row count is 10
- 343N/343O formal/client/production readiness flags remain false
- the demo rows are scoped as `343K_PACKAGE_ONLY` and `DEMO_ONLY`

### 8.3 Build source-check apply plan

For each 344B validated sidecar row:

- `SOURCE_CHECK_CONFIRMED` -> `SIMULATE_APPLY_SOURCE_CHECK_CONFIRM`
- `SOURCE_CHECK_CORRECTED` -> `SIMULATE_APPLY_SOURCE_CHECK_CORRECTION`

Carry forward source-checked metric/year/value/unit, evidence locator, source checker fields, and correction note where applicable.

Expected counts:

- `source_check_apply_plan_row_count = 19`
- `source_check_apply_confirm_count = 10`
- `source_check_apply_correct_count = 9`
- `source_check_apply_blocked_count = 0`

### 8.4 Build source-check applied sidecar

Generate `review_queue_source_check_sidecar_simulation_344c_source_check_applied_sidecar.jsonl` from apply-plan rows that are confirm/correct and validation-clean.

Expected:

- `source_check_applied_sidecar_row_count = 19`
- `corrections_applied_count = 9`

### 8.5 Build expanded trusted candidates

Combine:

- 10 trusted demo rows from 343N/343O arc
- 19 source-check applied sidecar rows from 344C simulation

Deduplicate conservatively by stable keys and metric/year/value/unit/source identity. If a duplicate exists, preserve both source lineage references in a dedup audit and keep one canonical row only if values are identical and lineage is compatible.

Expected happy path:

- `prior_demo_trusted_row_count = 10`
- `source_check_trusted_row_count = 19`
- `expanded_trusted_candidate_count = 29`
- `deduplicated_expanded_trusted_candidate_count = 29`
- `dedup_conflict_count = 0`

Every expanded trusted candidate must include:

- `expanded_trusted_scope = 343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`
- `source_lineage_stage = 343N_DEMO | 344B_SOURCE_CHECK`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- metric/year/value/unit fields
- evidence/review lineage fields

### 8.6 Expanded trust gate

Generate expanded trust gate JSON:

- `source_check_sidecar_apply_simulation_completed = true`
- `expanded_trust_gate_evaluated = true`
- `source_check_backlog_resolved = true`
- `prior_demo_trusted_row_count = 10`
- `source_check_trusted_row_count = 19`
- `expanded_trusted_candidate_count = 29`
- `deduplicated_expanded_trusted_candidate_count = 29`
- `dedup_conflict_count = 0`
- `expanded_trusted_scope = 343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Reason: expanded trusted coverage is available as a sidecar simulation, but formal client export remains blocked until a dedicated expanded export package and final audit/export gate are generated.

### 8.7 Scope boundary report

Generate Markdown explaining:

- 344C simulates applying 19 source-check resolved rows
- it combines the 19 rows with the earlier 10-row demo trusted arc
- expanded trusted candidate coverage is 29 rows if dedup passes
- no production data was written back
- no formal client export was generated
- next safe task is expanded trusted export package generation for review/demo, not production delivery

## 9. 344D readiness

If QA passes, set:

- `source_check_sidecar_apply_simulation_completed = true`
- `source_check_applied_sidecar_generated = true`
- `expanded_trusted_candidates_generated = true`
- `expanded_trust_gate_evaluated = true`
- `dedup_audit_generated = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_344d = true`
- `recommended_344d_scope = expanded_trusted_export_package_generation_for_review_demo_only`

If QA fails, set:

- `source_check_sidecar_apply_simulation_completed = false`
- `expanded_trusted_candidates_generated = false`
- `ready_for_344d = false`

## 10. Summary JSON

`review_queue_source_check_sidecar_simulation_344c_summary.json` must include at least:

- `source_milestone = 344B`
- `decision`
- `review_queue_schema_version`
- `source_check_input_sidecar_row_count`
- `source_check_apply_plan_row_count`
- `source_check_apply_confirm_count`
- `source_check_apply_correct_count`
- `source_check_apply_blocked_count`
- `source_check_applied_sidecar_row_count`
- `corrections_applied_count`
- `prior_demo_trusted_row_count`
- `source_check_trusted_row_count`
- `expanded_trusted_candidate_count`
- `deduplicated_expanded_trusted_candidate_count`
- `dedup_conflict_count`
- `expanded_trusted_scope`
- `source_check_sidecar_apply_simulation_completed`
- `expanded_trust_gate_evaluated`
- `source_check_backlog_resolved`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `ready_for_344d`
- `recommended_344d_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready: `SOURCE_CHECK_SIDECAR_SIMULATION_344C_READY`
- otherwise: `SOURCE_CHECK_SIDECAR_SIMULATION_344C_NOT_READY`

## 11. QA requirements

Must check:

- 344B input exists and is ready
- 344B validated sidecar has 19 rows
- source-check confirm/correct counts match 10/9
- apply plan has 19 rows and no blocked rows
- source-check applied sidecar has 19 rows
- correction sidecar has 9 rows and correction semantics are carried forward
- 343N/343O demo trusted rows are readable and count 10
- expanded trusted candidates count is 29 unless dedup explicitly removes compatible duplicates
- dedup audit is generated
- dedup conflict count is 0 for happy path
- expanded trust gate is generated
- no production write-back is performed
- formal/client/production readiness flags remain false
- no formal client export workbook is generated
- no Argilla call is made
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_source_check_sidecar_simulation_344c_report.md` in Chinese-first, English-friendly style.

It must explain:

- 344C simulated applying 19 source-check resolved rows
- 10 rows were source-check confirmed and 9 rows were source-check corrected
- the corrected rows carry YOY/% semantics from 344B
- expanded trusted candidate coverage reaches 29 rows after combining with the 10-row demo arc
- no production write-back or formal client export occurred
- next task is 344D expanded trusted export package generation for review/demo only

## 13. Ledger update

Update the project milestone ledger with:

- 344C ready/not-ready status
- inputs
- outputs
- key metrics
- validation result
- decision
- source-check sidecar apply summary
- expanded trusted candidate summary
- dedup audit summary
- expanded trust gate summary
- export/global boundary
- next recommended task

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\source_check_sidecar_simulation_344c.py datefac\benchmark\review_queue_source_check_sidecar_simulation_344c.py datefac\benchmark\review_queue_source_check_sidecar_simulation_344c_report.py tools\run_review_queue_source_check_sidecar_simulation_344c.py tests\benchmark\test_review_queue_source_check_sidecar_simulation_344c.py
python -m pytest tests\benchmark\test_review_queue_source_check_sidecar_simulation_344c.py -q
python tools\run_review_queue_source_check_sidecar_simulation_344c.py --source-check-ingestion-344b-dir D:\_datefac\output\review_queue_source_check_evidence_review_ingestion_344b --source-check-evidence-enrichment-344a2-dir D:\_datefac\output\review_queue_source_check_evidence_enrichment_344a2 --demo-audit-snapshot-343o-dir D:\_datefac\output\review_queue_demo_audit_snapshot_343o --limited-demo-export-package-343n-dir D:\_datefac\output\review_queue_limited_demo_export_package_343n --human-confirmed-sidecar-simulation-343m-dir D:\_datefac\output\review_queue_human_confirmed_sidecar_simulation_343m --pure-human-attestation-ingestion-343l-dir D:\_datefac\output\review_queue_pure_human_attestation_ingestion_343l --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_source_check_sidecar_simulation_344c
```

## 15. Completion report

Report in Chinese:

1. 344C decision
2. review_queue_schema_version
3. source_check_input_sidecar_row_count
4. source_check_apply_plan_row_count
5. source_check_apply_confirm_count
6. source_check_apply_correct_count
7. source_check_apply_blocked_count
8. source_check_applied_sidecar_row_count
9. corrections_applied_count
10. prior_demo_trusted_row_count
11. source_check_trusted_row_count
12. expanded_trusted_candidate_count
13. deduplicated_expanded_trusted_candidate_count
14. dedup_conflict_count
15. expanded_trusted_scope
16. source_check_sidecar_apply_simulation_completed
17. expanded_trust_gate_evaluated
18. source_check_backlog_resolved
19. formal_client_export_allowed
20. client_ready
21. production_ready
22. global_strict_human_review_completed
23. ready_for_344d
24. recommended_344d_scope
25. qa_fail_count
26. no-write-back proof status
27. output directory
28. most important apply-plan / applied-sidecar / expanded-trusted-candidates / dedup-audit / gate artifacts
29. modified files
30. validation command results
31. git status summary
32. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
