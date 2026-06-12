# 343M：Human-confirmed Sidecar Apply Simulation And Limited Export Gate

## 1. Positioning

343M consumes the 343L pure-human attestation ingestion outputs and simulates applying the 10 package-level human-confirmed rows into a sidecar result set.

The purpose is to produce a limited, scoped export gate for the 343K/343L package only, while keeping formal client export, production apply, and global readiness disabled.

343M is a sidecar apply simulation and limited export-gate task. It is not production apply, not formal client export, not Argilla integration, not a frontend implementation, not real LLM/VLM review, and not an upstream extraction rerun.

Important scope boundary: 343L completed pure-human confirmation only for the 10-row 343K package. It does not complete review for the whole corpus, the remaining source-check backlog, or production/client delivery.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/343L_pure_human_attestation_result_ingestion.md`
- 343L summary / QA / result JSONL / decision summary / client export gate / scope boundary
- 343K attestation items JSONL and import contract
- 343J strict review ingestion result JSONL and disclosure
- 343I2 enriched items and evidence resolution map
- 343H source-check backlog / strict-human-gap report / audit matrix
- 343A schema artifacts
- current git status

Expected current state:

- latest completed milestone = `343L Pure Human Attestation Result Ingestion`
- 343L decision = `PURE_HUMAN_ATTESTATION_INGESTION_343L_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- filled_row_count = `10`
- valid_row_count = `10`
- invalid_row_count = `0`
- human_accept_count = `10`
- human_correct_count = `0`
- human_reject_count = `0`
- human_needs_source_check_count = `0`
- human_defer_count = `0`
- human_source_evidence_checked_true_count = `10`
- human_independent_check_attested_true_count = `10`
- pure_human_attestation_result_ingested = `true`
- pure_strict_human_confirm_count = `10`
- pure_strict_human_correct_count = `0`
- pure_strict_human_review_completed_for_package = `true`
- strict_human_review_completed_scope = `343K_PACKAGE_ONLY`
- global_strict_human_review_completed = `false`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- ready_for_343m = `true`
- recommended_343m_scope = `human_confirmed_sidecar_apply_simulation_and_limited_export_gate`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, or delivery code. Do not write back to upstream workbooks. Do not generate formal client export. Do not perform real production apply.

343M may only generate a sidecar apply simulation and a limited export gate for the 10-row 343K package scope.

Formal/global export boundary must remain conservative:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Allowed scoped flags:

- `package_strict_human_review_completed = true` if 343L confirms all 10 rows
- `sidecar_apply_simulation_completed = true` if simulation succeeds
- `limited_export_gate_evaluated = true` if gate is generated
- `limited_package_export_candidate_allowed = true` only for the 10-row package-scope candidate, not formal client export

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343M_human_confirmed_sidecar_apply_simulation_and_limited_export_gate.md`
- `datefac/review_queue/human_confirmed_sidecar_simulation_343m.py`
- `datefac/benchmark/review_queue_human_confirmed_sidecar_simulation_343m.py`
- `datefac/benchmark/review_queue_human_confirmed_sidecar_simulation_343m_report.py`
- `tools/run_review_queue_human_confirmed_sidecar_simulation_343m.py`
- `tests/benchmark/test_review_queue_human_confirmed_sidecar_simulation_343m.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l`
- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k`
- `D:/_datefac/output/review_queue_strict_review_ingestion_343j`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_schema_343a`

Required 343L files:

- `review_queue_pure_human_attestation_ingestion_343l_summary.json`
- `review_queue_pure_human_attestation_ingestion_343l_qa.json`
- `review_queue_pure_human_attestation_ingestion_343l_result.jsonl`
- `review_queue_pure_human_attestation_ingestion_343l_decision_summary.json`
- `review_queue_pure_human_attestation_ingestion_343l_client_export_gate.json`
- `review_queue_pure_human_attestation_ingestion_343l_scope_boundary.md`
- `review_queue_pure_human_attestation_ingestion_343l_no_write_back_proof.json`

Reference files:

- `review_queue_strict_review_ingestion_343j_result.jsonl`
- `review_queue_source_evidence_enrichment_343i2_enriched_items.jsonl`
- `review_queue_audit_summary_343h_source_check_backlog.jsonl`
- `review_queue_audit_summary_343h_client_export_gate.json`
- `review_queue_schema_343a_schema.json`

If required 343L files are missing or 343L is not ready, fail gracefully with a clear error. Do not fabricate human-confirmed rows.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m`

Output files:

- `review_queue_human_confirmed_sidecar_simulation_343m.xlsx`
- `review_queue_human_confirmed_sidecar_simulation_343m_summary.json`
- `review_queue_human_confirmed_sidecar_simulation_343m_manifest.json`
- `review_queue_human_confirmed_sidecar_simulation_343m_qa.json`
- `review_queue_human_confirmed_sidecar_simulation_343m_report.md`
- `review_queue_human_confirmed_sidecar_simulation_343m_sidecar.jsonl`
- `review_queue_human_confirmed_sidecar_simulation_343m_apply_plan.jsonl`
- `review_queue_human_confirmed_sidecar_simulation_343m_limited_export_gate.json`
- `review_queue_human_confirmed_sidecar_simulation_343m_limited_export_candidate.jsonl`
- `review_queue_human_confirmed_sidecar_simulation_343m_remaining_backlog.jsonl`
- `review_queue_human_confirmed_sidecar_simulation_343m_scope_boundary.md`
- `review_queue_human_confirmed_sidecar_simulation_343m_no_write_back_proof.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_SIM_SUMMARY`
- `02_INPUT_343L_SUMMARY`
- `03_HUMAN_CONFIRMED_ROWS`
- `04_SIDECAR_SIMULATION`
- `05_LIMITED_EXPORT_GATE`
- `06_REMAINING_BACKLOG`
- `07_SCOPE_BOUNDARY`
- `08_NO_WRITE_BACK`
- `09_NEXT_STEPS`

## 8. Core logic

### 8.1 Read 343L attestation results

Read 343L summary, QA, decision summary, client export gate, scope boundary, and result JSONL.

Validate:

- 343L is ready
- 343L has 10 valid rows
- invalid row count is 0
- package-level human confirmation is complete
- strict_human_review_completed_scope is `343K_PACKAGE_ONLY`
- global strict human review remains false
- formal/client/production readiness flags remain false

### 8.2 Build sidecar apply simulation

Generate a sidecar item for each human-accepted or human-corrected row.

For `HUMAN_ACCEPT_AI_ASSISTED_CONFIRM`, carry forward the accepted metric/year/value/unit and mark:

- `sidecar_action = SIMULATE_APPLY_HUMAN_ACCEPT`
- `sidecar_result_status = HUMAN_CONFIRMED_ACCEPTED`

For `HUMAN_CORRECT`, carry forward the corrected metric/year/value/unit and mark:

- `sidecar_action = SIMULATE_APPLY_HUMAN_CORRECTION`
- `sidecar_result_status = HUMAN_CONFIRMED_CORRECTED`

If any row is rejected, source-check-required, deferred, or invalid, do not mark limited package as export-candidate-ready; generate remediation status instead.

Expected current happy-path counts:

- sidecar_row_count = `10`
- sidecar_human_accept_count = `10`
- sidecar_human_correct_count = `0`
- sidecar_blocked_count = `0`

### 8.3 Generate limited export candidate

Generate `review_queue_human_confirmed_sidecar_simulation_343m_limited_export_candidate.jsonl` only from sidecar-applied human-confirmed rows.

This is a limited package-scope candidate. It must include:

- `export_scope = 343K_PACKAGE_ONLY`
- `source_milestone = 343L`
- `human_confirmation_scope = 343K_PACKAGE_ONLY`
- `formal_client_export_allowed = false`
- `limited_package_export_candidate = true`
- source evidence locator summary
- human reviewer / attestation fields
- metric/year/value/unit fields

Do not create a formal client export workbook.

### 8.4 Remaining backlog

Generate a remaining backlog file from 343H source-check backlog and any rows not accepted/corrected in 343L.

Expected known backlog context:

- 19 source-check-required rows remain outside the 10-row package
- global strict review is incomplete

### 8.5 Limited export gate

Generate a limited export gate JSON:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `package_strict_human_review_completed = true`
- `strict_human_review_completed_scope = 343K_PACKAGE_ONLY`
- `sidecar_apply_simulation_completed = true`
- `limited_export_gate_evaluated = true`
- `limited_package_export_candidate_allowed = true` only if all 10 rows are human accepted/corrected and QA passes
- `limited_export_scope = 343K_PACKAGE_ONLY`
- `remaining_source_check_backlog_count = 19` if available
- `reason = Limited package candidate may be used only as a scoped audited sample/demo artifact; formal client export remains blocked until global review/export gates are satisfied.`

### 8.6 Scope boundary report

Generate a Markdown boundary report explaining:

- what was simulated
- what was not written back
- what the limited export candidate means
- why formal client export remains false
- why global strict review remains false
- what backlog remains
- what the next safe milestone should be

## 9. 343N readiness

If QA passes and limited package candidate is allowed, set:

- `sidecar_apply_simulation_completed = true`
- `limited_export_gate_evaluated = true`
- `limited_package_export_candidate_allowed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343n = true`
- `recommended_343n_scope = limited_human_confirmed_export_package_generation_for_demo_only`

If QA fails or candidate is blocked, set:

- `sidecar_apply_simulation_completed = false`
- `limited_package_export_candidate_allowed = false`
- `ready_for_343n = false`

## 10. Summary JSON

`review_queue_human_confirmed_sidecar_simulation_343m_summary.json` must include at least:

- `source_milestone = 343L`
- `decision`
- `review_queue_schema_version`
- `input_human_attested_row_count`
- `valid_human_attested_row_count`
- `sidecar_row_count`
- `sidecar_human_accept_count`
- `sidecar_human_correct_count`
- `sidecar_blocked_count`
- `limited_export_candidate_row_count`
- `remaining_source_check_backlog_count`
- `package_strict_human_review_completed`
- `strict_human_review_completed_scope`
- `global_strict_human_review_completed = false`
- `sidecar_apply_simulation_completed`
- `limited_export_gate_evaluated`
- `limited_package_export_candidate_allowed`
- `limited_export_scope = 343K_PACKAGE_ONLY`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343n`
- `recommended_343n_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready: `HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_READY`
- if remediation required: `HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_REMEDIATION_REQUIRED`
- otherwise: `HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_NOT_READY`

## 11. QA requirements

Must check:

- 343L input exists and is ready
- 343L package completion is true
- global strict human review remains false
- formal/client/production readiness flags remain false
- sidecar row count matches accepted/corrected human rows
- limited export candidate row count matches sidecar row count when gate passes
- limited export candidate carries explicit package scope
- remaining backlog is carried forward or explicitly marked unavailable
- limited export gate is generated and formal export remains false
- no Argilla call is made
- no real production apply is performed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_human_confirmed_sidecar_simulation_343m_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343M simulates applying 10 package-level human-confirmed rows into a sidecar
- the candidate is limited to `343K_PACKAGE_ONLY`
- remaining backlog/source-check rows still block global readiness
- formal client export remains forbidden
- next task, if needed, is limited human-confirmed export package generation for demo only

## 13. Ledger update

Update the project milestone ledger with:

- 343M ready/not-ready/remediation status
- inputs
- outputs
- key metrics
- validation result
- decision
- sidecar simulation summary
- limited export gate summary
- remaining backlog summary
- next recommended task

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\human_confirmed_sidecar_simulation_343m.py datefac\benchmark\review_queue_human_confirmed_sidecar_simulation_343m.py datefac\benchmark\review_queue_human_confirmed_sidecar_simulation_343m_report.py tools\run_review_queue_human_confirmed_sidecar_simulation_343m.py tests\benchmark\test_review_queue_human_confirmed_sidecar_simulation_343m.py
python -m pytest tests\benchmark\test_review_queue_human_confirmed_sidecar_simulation_343m.py -q
python tools\run_review_queue_human_confirmed_sidecar_simulation_343m.py --pure-human-attestation-ingestion-343l-dir D:\_datefac\output\review_queue_pure_human_attestation_ingestion_343l --pure-human-attestation-package-343k-dir D:\_datefac\output\review_queue_pure_human_attestation_package_343k --source-evidence-enrichment-343i2-dir D:\_datefac\output\review_queue_source_evidence_enrichment_343i2 --audit-summary-343h-dir D:\_datefac\output\review_queue_audit_summary_343h --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_human_confirmed_sidecar_simulation_343m
```

## 15. Completion report

Report in Chinese:

1. 343M decision
2. review_queue_schema_version
3. input_human_attested_row_count
4. valid_human_attested_row_count
5. sidecar_row_count
6. sidecar_human_accept_count
7. sidecar_human_correct_count
8. sidecar_blocked_count
9. limited_export_candidate_row_count
10. remaining_source_check_backlog_count
11. package_strict_human_review_completed
12. strict_human_review_completed_scope
13. global_strict_human_review_completed
14. sidecar_apply_simulation_completed
15. limited_export_gate_evaluated
16. limited_package_export_candidate_allowed
17. limited_export_scope
18. formal_client_export_allowed
19. client_ready
20. production_ready
21. ready_for_343n
22. recommended_343n_scope
23. qa_fail_count
24. no-write-back proof status
25. output directory
26. most important Excel/sidecar/gate/candidate/scope artifacts
27. modified files
28. validation command results
29. git status summary
30. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
