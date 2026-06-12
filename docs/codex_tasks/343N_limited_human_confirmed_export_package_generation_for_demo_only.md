# 343N：Limited Human-confirmed Export Package Generation For Demo Only

## 1. Positioning

343N consumes the 343M human-confirmed sidecar simulation outputs and generates a limited export package for demo / sample / handoff only.

The purpose is to package the 10 package-scope human-confirmed rows into a clearly labeled demo-only export artifact while preserving all scope boundaries and blocking any formal client export or production use.

343N is a limited package generation and demo handoff task. It is not production apply, not formal client export, not global client export, not Argilla integration, not a frontend implementation, not real LLM/VLM review, and not an upstream extraction rerun.

Important scope boundary: 343M generated a limited export candidate only for the 10-row `343K_PACKAGE_ONLY` scope. The remaining source-check backlog and global review gaps still exist.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/343M_human_confirmed_sidecar_apply_simulation_and_limited_export_gate.md`
- 343M summary / QA / sidecar JSONL / apply plan / limited export gate / limited export candidate / remaining backlog / scope boundary
- 343L summary / result JSONL / client export gate / scope boundary
- 343H audit summary / strict human gap report / source-check backlog
- 343A schema artifacts
- current git status

Expected current state:

- latest completed milestone = `343M Human-confirmed Sidecar Apply Simulation And Limited Export Gate`
- 343M decision = `HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- input_human_attested_row_count = `10`
- valid_human_attested_row_count = `10`
- sidecar_row_count = `10`
- sidecar_human_accept_count = `10`
- sidecar_human_correct_count = `0`
- sidecar_blocked_count = `0`
- limited_export_candidate_row_count = `10`
- remaining_source_check_backlog_count = `19`
- package_strict_human_review_completed = `true`
- strict_human_review_completed_scope = `343K_PACKAGE_ONLY`
- global_strict_human_review_completed = `false`
- sidecar_apply_simulation_completed = `true`
- limited_export_gate_evaluated = `true`
- limited_package_export_candidate_allowed = `true`
- limited_export_scope = `343K_PACKAGE_ONLY`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- ready_for_343n = `true`
- recommended_343n_scope = `limited_human_confirmed_export_package_generation_for_demo_only`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, delivery, or approval code. Do not write back to upstream workbooks. Do not perform real production apply.

343N may generate a limited demo-only export package from the 343M limited export candidate.

It must not generate or claim a formal client export.

Formal/global export boundary must remain conservative:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Allowed scoped/demo flags:

- `demo_only_export_package_generated = true` if package generation succeeds
- `limited_package_export_candidate_allowed = true` from 343M may be carried forward
- `limited_export_scope = 343K_PACKAGE_ONLY`
- `demo_handoff_ready = true` only for the limited 10-row package
- `formal_client_export_allowed = false` must remain false

Every exported artifact must be visibly labeled as demo-only / limited-scope / not formal client export.

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343N_limited_human_confirmed_export_package_generation_for_demo_only.md`
- `datefac/review_queue/limited_demo_export_package_343n.py`
- `datefac/benchmark/review_queue_limited_demo_export_package_343n.py`
- `datefac/benchmark/review_queue_limited_demo_export_package_343n_report.py`
- `tools/run_review_queue_limited_demo_export_package_343n.py`
- `tests/benchmark/test_review_queue_limited_demo_export_package_343n.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m`
- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_schema_343a`

Required 343M files:

- `review_queue_human_confirmed_sidecar_simulation_343m_summary.json`
- `review_queue_human_confirmed_sidecar_simulation_343m_qa.json`
- `review_queue_human_confirmed_sidecar_simulation_343m_sidecar.jsonl`
- `review_queue_human_confirmed_sidecar_simulation_343m_apply_plan.jsonl`
- `review_queue_human_confirmed_sidecar_simulation_343m_limited_export_gate.json`
- `review_queue_human_confirmed_sidecar_simulation_343m_limited_export_candidate.jsonl`
- `review_queue_human_confirmed_sidecar_simulation_343m_remaining_backlog.jsonl`
- `review_queue_human_confirmed_sidecar_simulation_343m_scope_boundary.md`
- `review_queue_human_confirmed_sidecar_simulation_343m_no_write_back_proof.json`

Reference files:

- `review_queue_pure_human_attestation_ingestion_343l_summary.json`
- `review_queue_pure_human_attestation_ingestion_343l_result.jsonl`
- `review_queue_audit_summary_343h_source_check_backlog.jsonl`
- `review_queue_audit_summary_343h_strict_human_gap_report.md`
- `review_queue_schema_343a_schema.json`

If required 343M files are missing or 343M is not ready, fail gracefully with a clear error. Do not fabricate export candidates.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_limited_demo_export_package_343n`

Output files:

- `review_queue_limited_demo_export_package_343n.xlsx`
- `review_queue_limited_demo_export_package_343n_summary.json`
- `review_queue_limited_demo_export_package_343n_manifest.json`
- `review_queue_limited_demo_export_package_343n_qa.json`
- `review_queue_limited_demo_export_package_343n_report.md`
- `review_queue_limited_demo_export_package_343n_demo_readme.md`
- `review_queue_limited_demo_export_package_343n_export_rows.jsonl`
- `review_queue_limited_demo_export_package_343n_export_rows.csv`
- `review_queue_limited_demo_export_package_343n_audit_labels.jsonl`
- `review_queue_limited_demo_export_package_343n_export_gate.json`
- `review_queue_limited_demo_export_package_343n_scope_boundary.md`
- `review_queue_limited_demo_export_package_343n_remaining_backlog.jsonl`
- `review_queue_limited_demo_export_package_343n_no_write_back_proof.json`

Optional but recommended if lightweight:

- `review_queue_limited_demo_export_package_343n_handoff_summary.md`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_PACKAGE_SUMMARY`
- `02_INPUT_343M_SUMMARY`
- `03_DEMO_EXPORT_ROWS`
- `04_AUDIT_LABELS`
- `05_EXPORT_GATE`
- `06_REMAINING_BACKLOG`
- `07_SCOPE_BOUNDARY`
- `08_NO_WRITE_BACK`
- `09_NEXT_STEPS`

## 8. Core logic

### 8.1 Read 343M limited export candidate

Read 343M summary, QA, limited export gate, limited export candidate, remaining backlog, and scope boundary.

Validate:

- 343M is ready
- sidecar apply simulation is complete
- limited export gate is evaluated
- limited package export candidate is allowed
- limited export scope is `343K_PACKAGE_ONLY`
- limited export candidate row count is 10
- remaining source-check backlog count is 19 if available
- formal/client/production readiness flags remain false

### 8.2 Build demo-only export rows

Generate demo export rows only from `review_queue_human_confirmed_sidecar_simulation_343m_limited_export_candidate.jsonl`.

Each exported row must include at least:

- `export_scope = 343K_PACKAGE_ONLY`
- `export_usage = DEMO_ONLY`
- `formal_client_export_allowed = false`
- `production_ready = false`
- `client_ready = false`
- `source_milestone = 343M`
- `human_confirmation_scope = 343K_PACKAGE_ONLY`
- `metric_standardized`
- `year_standardized`
- `value_numeric`
- `normalized_unit`
- human attestation fields where available
- source evidence locator summary where available
- audit label fields

Do not include remaining backlog rows in demo export rows.

### 8.3 Generate audit labels

For each demo export row, generate explicit audit labels:

- `PACKAGE_SCOPE_HUMAN_CONFIRMED`
- `DEMO_ONLY`
- `NOT_FORMAL_CLIENT_EXPORT`
- `NOT_PRODUCTION_READY`
- `GLOBAL_REVIEW_INCOMPLETE`
- `SOURCE_CHECK_BACKLOG_REMAINS`

### 8.4 Generate demo README / scope boundary

Generate Markdown files that state plainly:

- this package contains only 10 rows
- those 10 rows are human-confirmed within `343K_PACKAGE_ONLY`
- the package is demo-only / sample-only / handoff-only
- formal client export is still forbidden
- production use is forbidden
- client readiness is false
- global strict human review is incomplete
- 19 source-check backlog rows remain outside this package

### 8.5 Export gate

Generate a demo export gate JSON:

- `demo_only_export_package_generated = true`
- `demo_handoff_ready = true`
- `limited_package_export_candidate_allowed = true`
- `limited_export_scope = 343K_PACKAGE_ONLY`
- `limited_export_row_count = 10`
- `remaining_source_check_backlog_count = 19` if available
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `reason = Demo-only limited package is allowed for scoped presentation/handoff; formal client export remains blocked by global review incompleteness and remaining backlog.`

### 8.6 Next action plan

If QA passes and demo package is generated, recommend either:

- `343O Demo Package Audit Snapshot And Handoff Summary`, if the next goal is demo/handoff documentation
- `344A Source-check Backlog Resolution Package`, if the next goal is expanding trusted coverage beyond the 10-row package

Default recommendation should be:

`343O Demo Package Audit Snapshot And Handoff Summary`

because it finishes the current 10-row trusted demo arc.

## 9. 343O readiness

If QA passes, set:

- `demo_only_export_package_generated = true`
- `demo_handoff_ready = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343o = true`
- `recommended_343o_scope = demo_package_audit_snapshot_and_handoff_summary`

If QA fails, set:

- `demo_only_export_package_generated = false`
- `demo_handoff_ready = false`
- `ready_for_343o = false`

## 10. Summary JSON

`review_queue_limited_demo_export_package_343n_summary.json` must include at least:

- `source_milestone = 343M`
- `decision`
- `review_queue_schema_version`
- `input_limited_export_candidate_row_count`
- `demo_export_row_count`
- `audit_label_row_count`
- `remaining_source_check_backlog_count`
- `limited_export_scope = 343K_PACKAGE_ONLY`
- `export_usage = DEMO_ONLY`
- `package_strict_human_review_completed = true`
- `global_strict_human_review_completed = false`
- `demo_only_export_package_generated`
- `demo_handoff_ready`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343o`
- `recommended_343o_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready: `LIMITED_HUMAN_CONFIRMED_DEMO_EXPORT_PACKAGE_343N_READY`
- otherwise: `LIMITED_HUMAN_CONFIRMED_DEMO_EXPORT_PACKAGE_343N_NOT_READY`

## 11. QA requirements

Must check:

- 343M input exists and is ready
- limited export gate allows limited package candidate only
- formal/client/production readiness flags remain false
- limited export scope is `343K_PACKAGE_ONLY`
- demo export row count matches input candidate row count
- every demo export row carries demo-only and not-formal-export labels
- audit labels are generated
- remaining backlog is carried forward or explicitly marked unavailable
- demo README is generated
- export gate is generated
- no formal client export workbook is generated
- no Argilla call is made
- no real production apply is performed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_limited_demo_export_package_343n_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343N generated a 10-row limited demo export package
- the package scope is only `343K_PACKAGE_ONLY`
- every row is package-scope human-confirmed
- the package is demo-only / sample-only / handoff-only
- 19 source-check backlog rows still remain
- formal client export remains forbidden
- next task is a demo package audit snapshot / handoff summary, or source-check backlog resolution if expanding trusted coverage

## 13. Ledger update

Update the project milestone ledger with:

- 343N ready/not-ready status
- inputs
- outputs
- key metrics
- validation result
- decision
- demo export package summary
- export gate summary
- remaining backlog summary
- next recommended task

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\limited_demo_export_package_343n.py datefac\benchmark\review_queue_limited_demo_export_package_343n.py datefac\benchmark\review_queue_limited_demo_export_package_343n_report.py tools\run_review_queue_limited_demo_export_package_343n.py tests\benchmark\test_review_queue_limited_demo_export_package_343n.py
python -m pytest tests\benchmark\test_review_queue_limited_demo_export_package_343n.py -q
python tools\run_review_queue_limited_demo_export_package_343n.py --human-confirmed-sidecar-simulation-343m-dir D:\_datefac\output\review_queue_human_confirmed_sidecar_simulation_343m --pure-human-attestation-ingestion-343l-dir D:\_datefac\output\review_queue_pure_human_attestation_ingestion_343l --audit-summary-343h-dir D:\_datefac\output\review_queue_audit_summary_343h --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_limited_demo_export_package_343n
```

## 15. Completion report

Report in Chinese:

1. 343N decision
2. review_queue_schema_version
3. input_limited_export_candidate_row_count
4. demo_export_row_count
5. audit_label_row_count
6. remaining_source_check_backlog_count
7. limited_export_scope
8. export_usage
9. package_strict_human_review_completed
10. global_strict_human_review_completed
11. demo_only_export_package_generated
12. demo_handoff_ready
13. formal_client_export_allowed
14. client_ready
15. production_ready
16. ready_for_343o
17. recommended_343o_scope
18. qa_fail_count
19. no-write-back proof status
20. output directory
21. most important Excel/demo-readme/export-rows/gate/scope artifacts
22. modified files
23. validation command results
24. git status summary
25. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
