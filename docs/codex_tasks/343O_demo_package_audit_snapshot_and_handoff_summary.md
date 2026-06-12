# 343O：Demo Package Audit Snapshot And Handoff Summary

## 1. Positioning

343O consumes the 343N limited demo export package and produces an audit snapshot plus handoff summary for the 10-row human-confirmed demo package.

The purpose is to close the current 343-series trusted-demo arc by creating a clear handoff package that explains what was produced, what evidence and review chain supports it, what boundaries remain, and why it is still not a formal client export or production artifact.

343O is an audit snapshot and handoff documentation task. It is not production apply, not formal client export, not global client export, not Argilla integration, not a frontend implementation, not real LLM/VLM review, and not an upstream extraction rerun.

Important scope boundary: 343N generated a demo-only limited export package for the 10-row `343K_PACKAGE_ONLY` scope. The remaining source-check backlog and global review gaps still exist.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/343N_limited_human_confirmed_export_package_generation_for_demo_only.md`
- 343N summary / QA / workbook / demo README / export rows / audit labels / export gate / scope boundary / remaining backlog
- 343M summary / limited export gate / sidecar / limited export candidate
- 343L summary / scope boundary / client export gate
- 343H audit summary / strict-human-gap report / source-check backlog
- 343A schema artifacts
- current git status

Expected current state:

- latest completed milestone = `343N Limited Human-confirmed Export Package Generation For Demo Only`
- 343N decision = `LIMITED_HUMAN_CONFIRMED_DEMO_EXPORT_PACKAGE_343N_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- input_limited_export_candidate_row_count = `10`
- demo_export_row_count = `10`
- audit_label_row_count = `10`
- remaining_source_check_backlog_count = `19`
- limited_export_scope = `343K_PACKAGE_ONLY`
- export_usage = `DEMO_ONLY`
- package_strict_human_review_completed = `true`
- global_strict_human_review_completed = `false`
- demo_only_export_package_generated = `true`
- demo_handoff_ready = `true`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- ready_for_343o = `true`
- recommended_343o_scope = `demo_package_audit_snapshot_and_handoff_summary`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun upstream stages, MinerU, VLM, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, delivery, or approval code. Do not write back to upstream workbooks. Do not perform real production apply. Do not generate formal client export.

343O may generate audit snapshot and handoff materials for the demo-only 10-row package.

Formal/global export boundary must remain conservative:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Allowed demo/handoff flags:

- `demo_audit_snapshot_generated = true` if snapshot generation succeeds
- `handoff_summary_generated = true` if handoff summary generation succeeds
- `demo_handoff_ready = true` only for the limited 10-row package
- `limited_export_scope = 343K_PACKAGE_ONLY`
- `export_usage = DEMO_ONLY`

Every artifact must clearly label the package as demo-only / limited-scope / not formal client export / not production ready.

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/343O_demo_package_audit_snapshot_and_handoff_summary.md`
- `datefac/review_queue/demo_audit_snapshot_343o.py`
- `datefac/benchmark/review_queue_demo_audit_snapshot_343o.py`
- `datefac/benchmark/review_queue_demo_audit_snapshot_343o_report.py`
- `tools/run_review_queue_demo_audit_snapshot_343o.py`
- `tests/benchmark/test_review_queue_demo_audit_snapshot_343o.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_limited_demo_export_package_343n`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m`
- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_schema_343a`

Required 343N files:

- `review_queue_limited_demo_export_package_343n_summary.json`
- `review_queue_limited_demo_export_package_343n_qa.json`
- `review_queue_limited_demo_export_package_343n.xlsx`
- `review_queue_limited_demo_export_package_343n_demo_readme.md`
- `review_queue_limited_demo_export_package_343n_export_rows.jsonl`
- `review_queue_limited_demo_export_package_343n_export_rows.csv`
- `review_queue_limited_demo_export_package_343n_audit_labels.jsonl`
- `review_queue_limited_demo_export_package_343n_export_gate.json`
- `review_queue_limited_demo_export_package_343n_scope_boundary.md`
- `review_queue_limited_demo_export_package_343n_remaining_backlog.jsonl`
- `review_queue_limited_demo_export_package_343n_no_write_back_proof.json`

Reference files:

- `review_queue_human_confirmed_sidecar_simulation_343m_summary.json`
- `review_queue_human_confirmed_sidecar_simulation_343m_limited_export_gate.json`
- `review_queue_pure_human_attestation_ingestion_343l_summary.json`
- `review_queue_pure_human_attestation_ingestion_343l_scope_boundary.md`
- `review_queue_audit_summary_343h_summary.json`
- `review_queue_audit_summary_343h_strict_human_gap_report.md`
- `review_queue_audit_summary_343h_source_check_backlog.jsonl`
- `review_queue_schema_343a_schema.json`

If required 343N files are missing or 343N is not ready, fail gracefully with a clear error. Do not fabricate handoff conclusions.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_demo_audit_snapshot_343o`

Output files:

- `review_queue_demo_audit_snapshot_343o.xlsx`
- `review_queue_demo_audit_snapshot_343o_summary.json`
- `review_queue_demo_audit_snapshot_343o_manifest.json`
- `review_queue_demo_audit_snapshot_343o_qa.json`
- `review_queue_demo_audit_snapshot_343o_report.md`
- `review_queue_demo_audit_snapshot_343o_handoff_summary.md`
- `review_queue_demo_audit_snapshot_343o_executive_summary.md`
- `review_queue_demo_audit_snapshot_343o_trust_chain.md`
- `review_queue_demo_audit_snapshot_343o_scope_boundary.md`
- `review_queue_demo_audit_snapshot_343o_export_gate_snapshot.json`
- `review_queue_demo_audit_snapshot_343o_artifact_index.json`
- `review_queue_demo_audit_snapshot_343o_artifact_index.md`
- `review_queue_demo_audit_snapshot_343o_backlog_summary.json`
- `review_queue_demo_audit_snapshot_343o_next_action_plan.json`
- `review_queue_demo_audit_snapshot_343o_no_write_back_proof.json`

Optional but recommended if lightweight:

- `review_queue_demo_audit_snapshot_343o_presentation_notes.md`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_SNAPSHOT_SUMMARY`
- `02_INPUT_343N_SUMMARY`
- `03_TRUST_CHAIN`
- `04_DEMO_EXPORT_OVERVIEW`
- `05_EXPORT_GATE_SNAPSHOT`
- `06_BACKLOG_SUMMARY`
- `07_ARTIFACT_INDEX`
- `08_SCOPE_BOUNDARY`
- `09_NEXT_ACTION_PLAN`
- `10_NO_WRITE_BACK`

## 8. Core logic

### 8.1 Read 343N demo package

Read 343N summary, QA, demo README, export rows, audit labels, export gate, scope boundary, remaining backlog, and no-write-back proof.

Validate:

- 343N is ready
- demo export package is generated
- demo handoff is ready
- demo export row count is 10
- audit label row count is 10
- limited export scope is `343K_PACKAGE_ONLY`
- export usage is `DEMO_ONLY`
- formal/client/production readiness flags remain false
- global strict human review remains false

### 8.2 Build trust chain snapshot

Generate a concise trust-chain table from 343A through 343N showing:

- milestone id
- milestone purpose
- key input/output row count
- review/evidence status
- human/AI/source disclosure
- gate decision
- export/client/production readiness flags
- remaining limitation

The chain should highlight:

- 343A review queue schema
- 343H audit summary and strict-human gap
- 343I2 source evidence enrichment
- 343L package-level pure human attestation ingestion
- 343M sidecar simulation and limited export gate
- 343N demo-only limited export package

### 8.3 Build handoff summary

Generate `review_queue_demo_audit_snapshot_343o_handoff_summary.md` explaining:

- what artifacts to open first
- what the 10-row demo package contains
- why it is trustworthy within package scope
- why it is not a formal client export
- what the 19-row backlog means
- how a reviewer/client/demo audience should interpret the package
- what should not be claimed

### 8.4 Build executive summary

Generate an executive summary suitable for project reporting. It should be Chinese-first and concise, explaining:

- the project now has a 10-row human-confirmed demo-only export package
- the trust chain includes evidence enrichment and pure human attestation for the package scope
- formal client export remains blocked
- global strict human review remains incomplete
- remaining source-check backlog count is 19

### 8.5 Build artifact index

Generate a machine-readable and Markdown artifact index covering the key files from:

- 343N demo package
- 343M sidecar simulation and limited export gate
- 343L pure human attestation ingestion
- 343H audit/gap report

For each artifact include:

- artifact name
- path
- role
- whether user-facing/demo-facing
- whether formal-client-export
- scope
- caution label

### 8.6 Export gate snapshot

Generate a snapshot JSON that carries forward:

- `demo_only_export_package_generated = true`
- `demo_handoff_ready = true`
- `limited_package_export_candidate_allowed = true`
- `limited_export_scope = 343K_PACKAGE_ONLY`
- `export_usage = DEMO_ONLY`
- `limited_export_row_count = 10`
- `remaining_source_check_backlog_count = 19`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

### 8.7 Next action plan

Generate next action plan with two clear routes:

1. `344A Source-check Backlog Resolution Package` to expand trusted coverage beyond the 10-row demo package.
2. `343P Demo Presentation / Report Material Assembly` if the immediate goal is class/project presentation.

Default recommendation:

- `344A Source-check Backlog Resolution Package`

because the current 10-row trusted demo arc is now closed and the remaining blocker is backlog expansion.

## 9. 344A readiness

If QA passes, set:

- `demo_audit_snapshot_generated = true`
- `handoff_summary_generated = true`
- `artifact_index_generated = true`
- `export_gate_snapshot_generated = true`
- `demo_arc_closed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_344a = true`
- `recommended_344a_scope = source_check_backlog_resolution_package`

If QA fails, set:

- `demo_audit_snapshot_generated = false`
- `demo_arc_closed = false`
- `ready_for_344a = false`

## 10. Summary JSON

`review_queue_demo_audit_snapshot_343o_summary.json` must include at least:

- `source_milestone = 343N`
- `decision`
- `review_queue_schema_version`
- `input_demo_export_row_count`
- `audit_label_row_count`
- `limited_export_scope = 343K_PACKAGE_ONLY`
- `export_usage = DEMO_ONLY`
- `remaining_source_check_backlog_count`
- `package_strict_human_review_completed = true`
- `global_strict_human_review_completed = false`
- `demo_only_export_package_generated = true`
- `demo_handoff_ready = true`
- `demo_audit_snapshot_generated`
- `handoff_summary_generated`
- `executive_summary_generated`
- `trust_chain_generated`
- `artifact_index_generated`
- `export_gate_snapshot_generated`
- `demo_arc_closed`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_344a`
- `recommended_344a_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready: `DEMO_PACKAGE_AUDIT_SNAPSHOT_343O_READY`
- otherwise: `DEMO_PACKAGE_AUDIT_SNAPSHOT_343O_NOT_READY`

## 11. QA requirements

Must check:

- 343N input exists and is ready
- demo package row count is 10
- audit label row count is 10
- limited export scope is `343K_PACKAGE_ONLY`
- export usage is `DEMO_ONLY`
- demo README exists
- export gate exists and formal export remains false
- scope boundary exists
- remaining backlog is carried forward or explicitly marked unavailable
- trust chain is generated
- handoff summary is generated
- executive summary is generated
- artifact index is generated
- export gate snapshot is generated
- demo arc closed is true only when snapshot/handoff/index/gate all succeed
- no formal client export workbook is generated
- no Argilla call is made
- no real production apply is performed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_demo_audit_snapshot_343o_report.md` in Chinese-first, English-friendly style.

It must explain:

- 343O closes the 10-row trusted demo arc
- the demo package is supported by evidence enrichment, pure human attestation, sidecar simulation, limited export gate, and demo-only package generation
- the package scope is only `343K_PACKAGE_ONLY`
- formal client export remains forbidden
- global strict human review remains incomplete
- 19 source-check backlog rows remain
- next recommended task is 344A source-check backlog resolution, unless the immediate need is presentation/report assembly

## 13. Ledger update

Update the project milestone ledger with:

- 343O ready/not-ready status
- inputs
- outputs
- key metrics
- validation result
- decision
- demo audit snapshot summary
- handoff summary
- artifact index summary
- export gate snapshot summary
- remaining backlog summary
- next recommended task

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\demo_audit_snapshot_343o.py datefac\benchmark\review_queue_demo_audit_snapshot_343o.py datefac\benchmark\review_queue_demo_audit_snapshot_343o_report.py tools\run_review_queue_demo_audit_snapshot_343o.py tests\benchmark\test_review_queue_demo_audit_snapshot_343o.py
python -m pytest tests\benchmark\test_review_queue_demo_audit_snapshot_343o.py -q
python tools\run_review_queue_demo_audit_snapshot_343o.py --limited-demo-export-package-343n-dir D:\_datefac\output\review_queue_limited_demo_export_package_343n --human-confirmed-sidecar-simulation-343m-dir D:\_datefac\output\review_queue_human_confirmed_sidecar_simulation_343m --pure-human-attestation-ingestion-343l-dir D:\_datefac\output\review_queue_pure_human_attestation_ingestion_343l --audit-summary-343h-dir D:\_datefac\output\review_queue_audit_summary_343h --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_demo_audit_snapshot_343o
```

## 15. Completion report

Report in Chinese:

1. 343O decision
2. review_queue_schema_version
3. input_demo_export_row_count
4. audit_label_row_count
5. limited_export_scope
6. export_usage
7. remaining_source_check_backlog_count
8. package_strict_human_review_completed
9. global_strict_human_review_completed
10. demo_only_export_package_generated
11. demo_handoff_ready
12. demo_audit_snapshot_generated
13. handoff_summary_generated
14. executive_summary_generated
15. trust_chain_generated
16. artifact_index_generated
17. export_gate_snapshot_generated
18. demo_arc_closed
19. formal_client_export_allowed
20. client_ready
21. production_ready
22. ready_for_344a
23. recommended_344a_scope
24. qa_fail_count
25. no-write-back proof status
26. output directory
27. most important snapshot/handoff/executive/artifact-index/gate files
28. modified files
29. validation command results
30. git status summary
31. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
