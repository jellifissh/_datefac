# 344D：Expanded Trusted Export Package Generation For Review/Demo Only

## 1. Positioning

344D consumes the 344C expanded trusted candidates and generates an expanded trusted export package for review/demo only.

343O closed the original 10-row demo trusted arc. 344B resolved the 19-row source-check backlog, and 344C simulated applying those 19 rows into an expanded trusted sidecar set. 344D packages the resulting 29 expanded trusted candidates into a clearly labeled review/demo export package.

344D is an expanded package generation task. It is not production apply, not formal client export, not global client export, not Argilla integration, not frontend work, not real LLM/VLM review, and not an upstream extraction rerun.

Important scope boundary: 344D may generate a review/demo-only package from the 29 expanded trusted candidates, but it must not claim formal client export, client readiness, or production readiness.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/344C_source_check_confirmed_sidecar_apply_simulation_and_expanded_trust_gate.md`
- 344C summary / QA / source-check apply plan / applied sidecar / expanded trusted candidates / dedup audit / expanded trust gate / scope boundary
- 344B summary / validated sidecar / corrections / audit gate
- 343O summary / handoff summary / export gate snapshot
- 343N demo export package / export rows / audit labels / export gate
- 343A schema artifacts
- current git status

Expected current state:

- latest completed milestone = `344C Source-check Confirmed Sidecar Apply Simulation And Expanded Trust Gate`
- 344C decision = `SOURCE_CHECK_SIDECAR_SIMULATION_344C_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- source_check_input_sidecar_row_count = `19`
- source_check_apply_plan_row_count = `19`
- source_check_apply_confirm_count = `10`
- source_check_apply_correct_count = `9`
- source_check_apply_blocked_count = `0`
- source_check_applied_sidecar_row_count = `19`
- corrections_applied_count = `9`
- prior_demo_trusted_row_count = `10`
- source_check_trusted_row_count = `19`
- expanded_trusted_candidate_count = `29`
- deduplicated_expanded_trusted_candidate_count = `29`
- dedup_conflict_count = `0`
- expanded_trusted_scope = `343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`
- source_check_sidecar_apply_simulation_completed = `true`
- expanded_trust_gate_evaluated = `true`
- source_check_backlog_resolved = `true`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- global_strict_human_review_completed = `false`
- ready_for_344d = `true`
- recommended_344d_scope = `expanded_trusted_export_package_generation_for_review_demo_only`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun MinerU, PPStructure, VLM, OCR, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, delivery, approval, or formal export code. Do not write back to upstream workbooks. Do not perform real production apply. Do not generate formal client export.

344D may only generate review/demo-only export package artifacts under its own output directory.

Formal/global export boundary must remain conservative:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Allowed review/demo flags:

- `expanded_review_demo_package_generated = true` if package generation succeeds
- `expanded_demo_handoff_ready = true` only for review/demo use
- `expanded_trusted_candidate_count = 29`
- `export_usage = REVIEW_DEMO_ONLY`
- `expanded_export_scope = 343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`

Every exported artifact must visibly state:

- review/demo only
- not formal client export
- not production ready
- no production write-back
- formal client export still blocked

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/344D_expanded_trusted_export_package_generation_for_review_demo_only.md`
- `datefac/review_queue/expanded_trusted_demo_export_package_344d.py`
- `datefac/benchmark/review_queue_expanded_trusted_demo_export_package_344d.py`
- `datefac/benchmark/review_queue_expanded_trusted_demo_export_package_344d_report.py`
- `tools/run_review_queue_expanded_trusted_demo_export_package_344d.py`
- `tests/benchmark/test_review_queue_expanded_trusted_demo_export_package_344d.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c`
- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o`
- `D:/_datefac/output/review_queue_limited_demo_export_package_343n`
- `D:/_datefac/output/review_queue_schema_343a`

Required 344C files:

- `review_queue_source_check_sidecar_simulation_344c_summary.json`
- `review_queue_source_check_sidecar_simulation_344c_qa.json`
- `review_queue_source_check_sidecar_simulation_344c_expanded_trusted_candidates.jsonl`
- `review_queue_source_check_sidecar_simulation_344c_source_check_applied_sidecar.jsonl`
- `review_queue_source_check_sidecar_simulation_344c_corrections_applied.jsonl`
- `review_queue_source_check_sidecar_simulation_344c_dedup_audit.jsonl`
- `review_queue_source_check_sidecar_simulation_344c_expanded_trust_gate.json`
- `review_queue_source_check_sidecar_simulation_344c_scope_boundary.md`
- `review_queue_source_check_sidecar_simulation_344c_no_write_back_proof.json`

Reference files:

- `review_queue_source_check_evidence_review_ingestion_344b_summary.json`
- `review_queue_source_check_evidence_review_ingestion_344b_audit_gate.json`
- `review_queue_demo_audit_snapshot_343o_summary.json`
- `review_queue_demo_audit_snapshot_343o_artifact_index.json`
- `review_queue_limited_demo_export_package_343n_export_gate.json`
- `review_queue_schema_343a_schema.json`

If 344C is missing or not ready, fail gracefully. Do not fabricate expanded trusted candidates.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d`

Output files:

- `review_queue_expanded_trusted_demo_export_package_344d.xlsx`
- `review_queue_expanded_trusted_demo_export_package_344d_summary.json`
- `review_queue_expanded_trusted_demo_export_package_344d_manifest.json`
- `review_queue_expanded_trusted_demo_export_package_344d_qa.json`
- `review_queue_expanded_trusted_demo_export_package_344d_report.md`
- `review_queue_expanded_trusted_demo_export_package_344d_demo_readme.md`
- `review_queue_expanded_trusted_demo_export_package_344d_export_rows.jsonl`
- `review_queue_expanded_trusted_demo_export_package_344d_export_rows.csv`
- `review_queue_expanded_trusted_demo_export_package_344d_audit_labels.jsonl`
- `review_queue_expanded_trusted_demo_export_package_344d_export_gate.json`
- `review_queue_expanded_trusted_demo_export_package_344d_lineage_summary.json`
- `review_queue_expanded_trusted_demo_export_package_344d_scope_boundary.md`
- `review_queue_expanded_trusted_demo_export_package_344d_no_write_back_proof.json`

Optional but recommended if lightweight:

- `review_queue_expanded_trusted_demo_export_package_344d_handoff_summary.md`
- `review_queue_expanded_trusted_demo_export_package_344d_metric_distribution.json`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_PACKAGE_SUMMARY`
- `02_INPUT_344C_SUMMARY`
- `03_EXPANDED_EXPORT_ROWS`
- `04_AUDIT_LABELS`
- `05_LINEAGE_SUMMARY`
- `06_EXPORT_GATE`
- `07_SCOPE_BOUNDARY`
- `08_NO_WRITE_BACK`
- `09_NEXT_STEPS`

## 8. Core logic

### 8.1 Read and validate 344C state

Read 344C summary, QA, expanded trusted candidates, expanded trust gate, dedup audit, and no-write-back proof.

Validate:

- 344C is ready
- source-check sidecar apply simulation is complete
- expanded trust gate is evaluated
- expanded trusted candidate count is 29
- deduplicated expanded trusted candidate count is 29
- dedup conflict count is 0
- formal/client/production readiness flags remain false
- global strict human review remains false

### 8.2 Build review/demo export rows

Generate export rows only from `review_queue_source_check_sidecar_simulation_344c_expanded_trusted_candidates.jsonl`.

Each row must include at least:

- `expanded_export_scope = 343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`
- `export_usage = REVIEW_DEMO_ONLY`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `source_lineage_stage`
- `source_lineage_summary`
- `metric_standardized`
- `year_standardized`
- `value_numeric`
- `normalized_unit`
- source evidence locator fields where available
- human/source-check review fields where available
- correction fields where applicable

Expected row count:

- `expanded_export_row_count = 29`

Do not include unreviewed/untrusted rows.

### 8.3 Generate audit labels

For each export row, generate explicit audit labels.

Base labels for every row:

- `EXPANDED_TRUSTED_CANDIDATE`
- `REVIEW_DEMO_ONLY`
- `NOT_FORMAL_CLIENT_EXPORT`
- `NOT_PRODUCTION_READY`
- `NO_PRODUCTION_WRITE_BACK`

Additional labels based on lineage:

- for 343O/343N demo rows: `PACKAGE_SCOPE_HUMAN_CONFIRMED`
- for 344B source-check rows: `SOURCE_CHECK_RESOLVED`
- for corrected 344B rows: `SOURCE_CHECK_CORRECTED`
- for confirmed 344B rows: `SOURCE_CHECK_CONFIRMED`

Expected audit label row count:

- `audit_label_row_count = 29`

### 8.4 Generate lineage summary

Generate lineage summary JSON describing:

- prior demo trusted rows = 10
- source-check resolved rows = 19
- source-check confirmed rows = 10
- source-check corrected rows = 9
- correction semantics: 9 corrected rows use `YOY` and `%`
- dedup conflict count = 0
- expanded trusted candidate count = 29

### 8.5 Export gate

Generate review/demo export gate JSON:

- `expanded_review_demo_package_generated = true`
- `expanded_demo_handoff_ready = true`
- `expanded_export_row_count = 29`
- `audit_label_row_count = 29`
- `expanded_export_scope = 343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`
- `export_usage = REVIEW_DEMO_ONLY`
- `source_check_backlog_resolved = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `reason = Expanded trusted package is generated for review/demo handoff only; formal client export remains blocked until final export audit and production readiness gates are satisfied.`

### 8.6 Demo README and scope boundary

Generate Markdown that states plainly:

- the package contains 29 reviewed trusted candidate rows
- the package combines the 10-row closed demo arc and 19 source-check resolved rows
- it is review/demo only
- it is not formal client export
- it is not production ready
- no production write-back happened
- the next task should generate an expanded package audit snapshot and final demo handoff summary, or a formal export readiness assessment if that becomes the goal later

## 9. 344E readiness

If QA passes, set:

- `expanded_review_demo_package_generated = true`
- `expanded_demo_handoff_ready = true`
- `expanded_export_gate_generated = true`
- `lineage_summary_generated = true`
- `audit_labels_generated = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_344e = true`
- `recommended_344e_scope = expanded_trusted_demo_audit_snapshot_and_final_handoff_summary`

If QA fails, set:

- `expanded_review_demo_package_generated = false`
- `expanded_demo_handoff_ready = false`
- `ready_for_344e = false`

## 10. Summary JSON

`review_queue_expanded_trusted_demo_export_package_344d_summary.json` must include at least:

- `source_milestone = 344C`
- `decision`
- `review_queue_schema_version`
- `input_expanded_trusted_candidate_count`
- `expanded_export_row_count`
- `audit_label_row_count`
- `prior_demo_trusted_row_count`
- `source_check_trusted_row_count`
- `source_check_confirmed_row_count`
- `source_check_corrected_row_count`
- `correction_row_count`
- `dedup_conflict_count`
- `expanded_export_scope`
- `export_usage = REVIEW_DEMO_ONLY`
- `expanded_review_demo_package_generated`
- `expanded_demo_handoff_ready`
- `expanded_export_gate_generated`
- `lineage_summary_generated`
- `audit_labels_generated`
- `source_check_backlog_resolved`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `ready_for_344e`
- `recommended_344e_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready: `EXPANDED_TRUSTED_DEMO_EXPORT_PACKAGE_344D_READY`
- otherwise: `EXPANDED_TRUSTED_DEMO_EXPORT_PACKAGE_344D_NOT_READY`

## 11. QA requirements

Must check:

- 344C input exists and is ready
- expanded trusted candidates file has 29 rows
- no dedup conflicts exist
- export rows count is 29
- audit labels count is 29
- each export row has explicit review/demo-only and not-formal-export labels
- lineage summary is generated and counts match 10 + 19 = 29
- corrected row semantics from 344B are preserved: `YOY` and `%` for 9 corrected rows
- export gate is generated
- formal/client/production readiness flags remain false
- no formal client export workbook is generated
- no Argilla call is made
- no real production apply is performed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_expanded_trusted_demo_export_package_344d_report.md` in Chinese-first, English-friendly style.

It must explain:

- 344D generated a 29-row expanded trusted review/demo package
- the package combines 10 demo-arc rows and 19 source-check resolved rows
- 10 source-check rows were confirmed and 9 were corrected
- corrected rows carry YOY/% semantics
- the package is review/demo only
- no production write-back or formal client export occurred
- next task is 344E expanded trusted demo audit snapshot and final handoff summary

## 13. Ledger update

Update the project milestone ledger with:

- 344D ready/not-ready status
- inputs
- outputs
- key metrics
- validation result
- decision
- expanded export package summary
- lineage summary
- export gate summary
- audit label summary
- export/global boundary
- next recommended task

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\expanded_trusted_demo_export_package_344d.py datefac\benchmark\review_queue_expanded_trusted_demo_export_package_344d.py datefac\benchmark\review_queue_expanded_trusted_demo_export_package_344d_report.py tools\run_review_queue_expanded_trusted_demo_export_package_344d.py tests\benchmark\test_review_queue_expanded_trusted_demo_export_package_344d.py
python -m pytest tests\benchmark\test_review_queue_expanded_trusted_demo_export_package_344d.py -q
python tools\run_review_queue_expanded_trusted_demo_export_package_344d.py --source-check-sidecar-simulation-344c-dir D:\_datefac\output\review_queue_source_check_sidecar_simulation_344c --source-check-ingestion-344b-dir D:\_datefac\output\review_queue_source_check_evidence_review_ingestion_344b --demo-audit-snapshot-343o-dir D:\_datefac\output\review_queue_demo_audit_snapshot_343o --limited-demo-export-package-343n-dir D:\_datefac\output\review_queue_limited_demo_export_package_343n --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_expanded_trusted_demo_export_package_344d
```

## 15. Completion report

Report in Chinese:

1. 344D decision
2. review_queue_schema_version
3. input_expanded_trusted_candidate_count
4. expanded_export_row_count
5. audit_label_row_count
6. prior_demo_trusted_row_count
7. source_check_trusted_row_count
8. source_check_confirmed_row_count
9. source_check_corrected_row_count
10. correction_row_count
11. dedup_conflict_count
12. expanded_export_scope
13. export_usage
14. expanded_review_demo_package_generated
15. expanded_demo_handoff_ready
16. expanded_export_gate_generated
17. lineage_summary_generated
18. audit_labels_generated
19. source_check_backlog_resolved
20. formal_client_export_allowed
21. client_ready
22. production_ready
23. global_strict_human_review_completed
24. ready_for_344e
25. recommended_344e_scope
26. qa_fail_count
27. no-write-back proof status
28. output directory
29. most important Excel/export rows/audit labels/lineage summary/export gate/scope boundary artifacts
30. modified files
31. validation command results
32. git status summary
33. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
