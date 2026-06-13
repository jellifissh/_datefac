# 344E：Expanded Trusted Demo Audit Snapshot And Final Handoff Summary

## 1. Positioning

344E consumes the 344D expanded trusted review/demo export package and produces the final audit snapshot, handoff summary, executive summary, artifact index, trust-chain report, and final demo boundary package for the 29-row expanded trusted candidate set.

343O closed the original 10-row trusted demo arc. 344B resolved the remaining 19 source-check backlog rows. 344C simulated expanded trusted sidecar coverage. 344D generated a 29-row review/demo-only expanded trusted package. 344E closes this expanded trusted demo arc with a final documentation and audit handoff layer.

344E is a final audit snapshot and handoff documentation task for review/demo use. It is not production apply, not formal client export, not global client export, not Argilla integration, not frontend work, not real LLM/VLM review, and not an upstream extraction rerun.

Important scope boundary: 344E may describe the 29-row expanded trusted review/demo package, but it must not claim formal client export, client readiness, production readiness, or global strict-human-review completion.

## 2. Required preflight

Before coding, read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/344D_expanded_trusted_export_package_generation_for_review_demo_only.md`
- 344D summary / QA / Excel / demo README / export rows / audit labels / lineage summary / export gate / scope boundary
- 344C summary / expanded trusted candidates / expanded trust gate / dedup audit
- 344B summary / validated sidecar / corrections / audit gate
- 344A2 summary / evidence map / enriched template / match candidates
- 343O summary / handoff summary / trust chain / artifact index / export gate snapshot
- 343N demo export package / export gate
- 343A schema artifacts
- current git status

Expected current state:

- latest completed milestone = `344D Expanded Trusted Export Package Generation For Review/Demo Only`
- 344D decision = `EXPANDED_TRUSTED_DEMO_EXPORT_PACKAGE_344D_READY`
- review_queue_schema_version = `343A.review_queue.v1`
- input_expanded_trusted_candidate_count = `29`
- expanded_export_row_count = `29`
- audit_label_row_count = `29`
- prior_demo_trusted_row_count = `10`
- source_check_trusted_row_count = `19`
- source_check_confirmed_row_count = `10`
- source_check_corrected_row_count = `9`
- correction_row_count = `9`
- dedup_conflict_count = `0`
- expanded_export_scope = `343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`
- export_usage = `REVIEW_DEMO_ONLY`
- expanded_review_demo_package_generated = `true`
- expanded_demo_handoff_ready = `true`
- expanded_export_gate_generated = `true`
- lineage_summary_generated = `true`
- audit_labels_generated = `true`
- source_check_backlog_resolved = `true`
- formal_client_export_allowed = `false`
- client_ready = `false`
- production_ready = `false`
- global_strict_human_review_completed = `false`
- ready_for_344e = `true`
- recommended_344e_scope = `expanded_trusted_demo_audit_snapshot_and_final_handoff_summary`
- qa_fail_count = `0`

## 3. Git responsibility boundary

Codex must not run `git pull`, `git add`, `git commit`, or `git push`.

Codex may run read-only git inspection commands such as `git status -sb` or `git diff --name-only` to report state.

The user is responsible for pulling, staging, committing, and pushing.

Never use `git add .`, `git add -A`, `git reset --hard`, or `git checkout --`.

## 4. Hard boundaries

Do not rerun MinerU, PPStructure, VLM, OCR, or real LLM calls. Do not call or import Argilla. Do not implement a frontend UI. Do not modify production pipeline, parser, extraction, delivery, approval, or formal export code. Do not write back to upstream workbooks. Do not perform real production apply. Do not generate formal client export.

344E may only generate final review/demo handoff and audit snapshot artifacts under its own output directory.

Formal/global export boundary must remain conservative:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Allowed review/demo/handoff flags:

- `expanded_demo_audit_snapshot_generated = true` if snapshot succeeds
- `final_handoff_summary_generated = true` if handoff succeeds
- `executive_summary_generated = true` if executive summary succeeds
- `artifact_index_generated = true` if artifact index succeeds
- `trust_chain_report_generated = true` if trust-chain report succeeds
- `expanded_demo_arc_closed = true` only when all required 344E artifacts pass QA
- `expanded_demo_handoff_ready = true` only for review/demo handoff
- `export_usage = REVIEW_DEMO_ONLY`

Every artifact must visibly state:

- review/demo only
- not formal client export
- not production ready
- no production write-back
- formal client export still blocked

Do not stage generated outputs, temp files, reviewed input workbooks, semantic adjudicator response folders, LLM response folders, `tools/mineru_new_runner.cmd`, or protected dirty files.

## 5. New or updated files

Create or update only these task/code/test files plus the ledger:

- `docs/codex_tasks/344E_expanded_trusted_demo_audit_snapshot_and_final_handoff_summary.md`
- `datefac/review_queue/expanded_demo_audit_snapshot_344e.py`
- `datefac/benchmark/review_queue_expanded_demo_audit_snapshot_344e.py`
- `datefac/benchmark/review_queue_expanded_demo_audit_snapshot_344e_report.py`
- `tools/run_review_queue_expanded_demo_audit_snapshot_344e.py`
- `tests/benchmark/test_review_queue_expanded_demo_audit_snapshot_344e.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If a package initializer must be touched, keep the change minimal.

## 6. Inputs

Input directories:

- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d`
- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c`
- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o`
- `D:/_datefac/output/review_queue_limited_demo_export_package_343n`
- `D:/_datefac/output/review_queue_schema_343a`

Required 344D files:

- `review_queue_expanded_trusted_demo_export_package_344d_summary.json`
- `review_queue_expanded_trusted_demo_export_package_344d_qa.json`
- `review_queue_expanded_trusted_demo_export_package_344d.xlsx`
- `review_queue_expanded_trusted_demo_export_package_344d_demo_readme.md`
- `review_queue_expanded_trusted_demo_export_package_344d_export_rows.jsonl`
- `review_queue_expanded_trusted_demo_export_package_344d_export_rows.csv`
- `review_queue_expanded_trusted_demo_export_package_344d_audit_labels.jsonl`
- `review_queue_expanded_trusted_demo_export_package_344d_export_gate.json`
- `review_queue_expanded_trusted_demo_export_package_344d_lineage_summary.json`
- `review_queue_expanded_trusted_demo_export_package_344d_scope_boundary.md`
- `review_queue_expanded_trusted_demo_export_package_344d_no_write_back_proof.json`

Reference files:

- `review_queue_source_check_sidecar_simulation_344c_summary.json`
- `review_queue_source_check_sidecar_simulation_344c_expanded_trusted_candidates.jsonl`
- `review_queue_source_check_sidecar_simulation_344c_expanded_trust_gate.json`
- `review_queue_source_check_evidence_review_ingestion_344b_summary.json`
- `review_queue_source_check_evidence_review_ingestion_344b_corrections.jsonl`
- `review_queue_source_check_evidence_enrichment_344a2_summary.json`
- `review_queue_source_check_evidence_enrichment_344a2_evidence_map.json`
- `review_queue_demo_audit_snapshot_343o_summary.json`
- `review_queue_demo_audit_snapshot_343o_handoff_summary.md`
- `review_queue_demo_audit_snapshot_343o_artifact_index.json`
- `review_queue_schema_343a_schema.json`

If 344D is missing or not ready, fail gracefully. Do not fabricate handoff conclusions.

## 7. Outputs

Output directory:

`D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e`

Output files:

- `review_queue_expanded_demo_audit_snapshot_344e.xlsx`
- `review_queue_expanded_demo_audit_snapshot_344e_summary.json`
- `review_queue_expanded_demo_audit_snapshot_344e_manifest.json`
- `review_queue_expanded_demo_audit_snapshot_344e_qa.json`
- `review_queue_expanded_demo_audit_snapshot_344e_report.md`
- `review_queue_expanded_demo_audit_snapshot_344e_final_handoff_summary.md`
- `review_queue_expanded_demo_audit_snapshot_344e_executive_summary.md`
- `review_queue_expanded_demo_audit_snapshot_344e_trust_chain_report.md`
- `review_queue_expanded_demo_audit_snapshot_344e_artifact_index.json`
- `review_queue_expanded_demo_audit_snapshot_344e_artifact_index.md`
- `review_queue_expanded_demo_audit_snapshot_344e_final_export_gate_snapshot.json`
- `review_queue_expanded_demo_audit_snapshot_344e_lineage_audit_summary.json`
- `review_queue_expanded_demo_audit_snapshot_344e_metric_distribution.json`
- `review_queue_expanded_demo_audit_snapshot_344e_scope_boundary.md`
- `review_queue_expanded_demo_audit_snapshot_344e_next_action_plan.json`
- `review_queue_expanded_demo_audit_snapshot_344e_no_write_back_proof.json`

Optional but recommended if lightweight:

- `review_queue_expanded_demo_audit_snapshot_344e_presentation_notes.md`
- `review_queue_expanded_demo_audit_snapshot_344e_claims_and_forbidden_claims.md`

All generated outputs remain under `output/` and must not be committed.

Workbook sheets, all <=31 chars:

- `00_README`
- `01_SNAPSHOT_SUMMARY`
- `02_INPUT_344D_SUMMARY`
- `03_EXPANDED_PACKAGE`
- `04_TRUST_CHAIN`
- `05_LINEAGE_AUDIT`
- `06_ARTIFACT_INDEX`
- `07_FINAL_GATE`
- `08_SCOPE_BOUNDARY`
- `09_NEXT_ACTION_PLAN`
- `10_NO_WRITE_BACK`

## 8. Core logic

### 8.1 Read and validate 344D state

Read 344D summary, QA, demo README, export rows, audit labels, export gate, lineage summary, scope boundary, and no-write-back proof.

Validate:

- 344D is ready
- expanded review/demo package is generated
- expanded demo handoff is ready
- expanded export row count is 29
- audit label row count is 29
- expanded export scope is `343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`
- export usage is `REVIEW_DEMO_ONLY`
- formal/client/production readiness flags remain false
- global strict human review remains false

### 8.2 Build final expanded trust-chain report

Generate a trust-chain report from 343A through 344D showing:

- milestone id
- purpose
- input/output row counts
- review/evidence status
- AI/human/source-check disclosure
- correction handling
- gate decision
- export/client/production readiness flags
- remaining limitation

Must highlight these key stages:

- `343A` review queue schema
- `343H` audit summary and strict-human gap
- `343I2` source evidence enrichment for the first 10-row package
- `343L` package-level pure human attestation ingestion
- `343M` sidecar simulation and limited gate
- `343N` 10-row demo-only package
- `343O` 10-row demo arc audit snapshot
- `344A` 19-row source-check backlog package
- `344A2` source evidence enrichment resolving all 19 evidence locators
- `344B` source-check review ingestion with 10 confirm / 9 correct
- `344C` expanded sidecar simulation and 29-row trust gate
- `344D` expanded review/demo package generation

### 8.3 Build final handoff summary

Generate `review_queue_expanded_demo_audit_snapshot_344e_final_handoff_summary.md` explaining:

- what to open first
- what the 29-row package contains
- how it differs from the earlier 10-row demo package
- how the 19 source-check rows were resolved
- how the 9 corrected rows should be interpreted as `YOY` / `%`
- why it is trustworthy within review/demo scope
- why it is not formal client export
- what claims are allowed
- what claims are forbidden
- what downstream work is required for formal export readiness

### 8.4 Build executive summary

Generate an executive summary suitable for project reporting. It should be Chinese-first and concise, explaining:

- the project now has a 29-row expanded trusted review/demo package
- the package combines 10 previously human-confirmed demo rows and 19 source-check resolved rows
- all 19 backlog rows now have source evidence and review decisions
- 10 source-check rows were confirmed and 9 were corrected
- formal client export remains blocked
- production readiness remains false

### 8.5 Build artifact index

Generate a machine-readable and Markdown artifact index covering the key files from:

- 344D expanded package
- 344C expanded trusted candidates and gate
- 344B source-check ingestion and corrections
- 344A2 evidence enrichment
- 343O final 10-row demo arc snapshot

For each artifact include:

- artifact name
- path
- role
- milestone
- whether user-facing/demo-facing
- whether formal-client-export
- scope
- caution label

### 8.6 Build final export gate snapshot

Generate a final gate snapshot JSON that carries forward:

- `expanded_review_demo_package_generated = true`
- `expanded_demo_handoff_ready = true`
- `expanded_demo_audit_snapshot_generated = true`
- `final_handoff_summary_generated = true`
- `expanded_export_row_count = 29`
- `audit_label_row_count = 29`
- `expanded_export_scope = 343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`
- `export_usage = REVIEW_DEMO_ONLY`
- `source_check_backlog_resolved = true`
- `prior_demo_trusted_row_count = 10`
- `source_check_trusted_row_count = 19`
- `source_check_confirmed_row_count = 10`
- `source_check_corrected_row_count = 9`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

### 8.7 Build next action plan

Generate next action plan with clear routes:

1. `345A Formal Export Readiness Gap Assessment`, if the next goal is to move toward formal export readiness.
2. `345B Presentation Report Material Assembly`, if the immediate goal is class/project presentation.
3. `345C UI/API Integration Planning For Review Queue`, if the next goal is productization.

Default recommendation:

- `345A Formal Export Readiness Gap Assessment`

because the expanded demo arc is now closed and the next logical gap is determining what remains before formal export readiness.

### 8.8 Claims and forbidden claims

If generating optional claims file, include:

Allowed claims:

- 29 reviewed trusted candidate rows are available for review/demo handoff.
- 19 source-check backlog rows were enriched with source evidence and reviewed.
- 10 source-check rows were confirmed and 9 were corrected.
- No production write-back occurred.
- Formal client export remains blocked.

Forbidden claims:

- formal client export is ready
- production export is ready
- all corpus data is globally reviewed
- system is production ready
- output can be sent to clients as final audited results

## 9. 345A readiness

If QA passes, set:

- `expanded_demo_audit_snapshot_generated = true`
- `final_handoff_summary_generated = true`
- `executive_summary_generated = true`
- `trust_chain_report_generated = true`
- `artifact_index_generated = true`
- `final_export_gate_snapshot_generated = true`
- `expanded_demo_arc_closed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_345a = true`
- `recommended_345a_scope = formal_export_readiness_gap_assessment`

If QA fails, set:

- `expanded_demo_audit_snapshot_generated = false`
- `expanded_demo_arc_closed = false`
- `ready_for_345a = false`

## 10. Summary JSON

`review_queue_expanded_demo_audit_snapshot_344e_summary.json` must include at least:

- `source_milestone = 344D`
- `decision`
- `review_queue_schema_version`
- `input_expanded_export_row_count`
- `audit_label_row_count`
- `prior_demo_trusted_row_count`
- `source_check_trusted_row_count`
- `source_check_confirmed_row_count`
- `source_check_corrected_row_count`
- `correction_row_count`
- `expanded_export_scope`
- `export_usage = REVIEW_DEMO_ONLY`
- `expanded_review_demo_package_generated = true`
- `expanded_demo_handoff_ready = true`
- `expanded_demo_audit_snapshot_generated`
- `final_handoff_summary_generated`
- `executive_summary_generated`
- `trust_chain_report_generated`
- `artifact_index_generated`
- `final_export_gate_snapshot_generated`
- `lineage_audit_summary_generated`
- `metric_distribution_generated`
- `expanded_demo_arc_closed`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `ready_for_345a`
- `recommended_345a_scope`
- `qa_fail_count`
- `no_write_back_proof_passed`

Decision:

- if ready: `EXPANDED_TRUSTED_DEMO_AUDIT_SNAPSHOT_344E_READY`
- otherwise: `EXPANDED_TRUSTED_DEMO_AUDIT_SNAPSHOT_344E_NOT_READY`

## 11. QA requirements

Must check:

- 344D input exists and is ready
- expanded export rows count is 29
- audit labels count is 29
- expanded export scope is correct
- export usage is `REVIEW_DEMO_ONLY`
- lineage summary exists and counts match 10 + 19 = 29
- source-check corrected rows count is 9
- corrected row semantics `YOY` / `%` are disclosed
- final handoff summary is generated
- executive summary is generated
- trust-chain report is generated
- artifact index is generated
- final export gate snapshot is generated
- final boundary still blocks formal/client/production readiness
- expanded demo arc closed is true only when all required artifacts pass QA
- no formal client export workbook is generated
- no Argilla call is made
- no real production apply is performed
- no upstream workbook or production pipeline/parser/extraction/delivery file is modified
- no generated output or forbidden input/temp path is staged
- workbook sheet names are <=31 chars
- no-write-back proof is generated

## 12. Report

Generate `review_queue_expanded_demo_audit_snapshot_344e_report.md` in Chinese-first, English-friendly style.

It must explain:

- 344E closes the 29-row expanded trusted demo arc
- the expanded package combines 10 demo-arc rows and 19 source-check resolved rows
- 10 source-check rows were confirmed and 9 were corrected
- corrected rows carry YOY/% semantics
- all outputs are review/demo-only
- formal client export remains forbidden
- no production write-back occurred
- next recommended task is formal export readiness gap assessment

## 13. Ledger update

Update the project milestone ledger with:

- 344E ready/not-ready status
- inputs
- outputs
- key metrics
- validation result
- decision
- final expanded demo audit snapshot summary
- final handoff summary
- trust-chain summary
- artifact index summary
- final export gate snapshot
- export/global boundary
- next recommended task

## 14. Validation commands

Run:

```powershell
python -m py_compile datefac\review_queue\expanded_demo_audit_snapshot_344e.py datefac\benchmark\review_queue_expanded_demo_audit_snapshot_344e.py datefac\benchmark\review_queue_expanded_demo_audit_snapshot_344e_report.py tools\run_review_queue_expanded_demo_audit_snapshot_344e.py tests\benchmark\test_review_queue_expanded_demo_audit_snapshot_344e.py
python -m pytest tests\benchmark\test_review_queue_expanded_demo_audit_snapshot_344e.py -q
python tools\run_review_queue_expanded_demo_audit_snapshot_344e.py --expanded-trusted-demo-export-package-344d-dir D:\_datefac\output\review_queue_expanded_trusted_demo_export_package_344d --source-check-sidecar-simulation-344c-dir D:\_datefac\output\review_queue_source_check_sidecar_simulation_344c --source-check-ingestion-344b-dir D:\_datefac\output\review_queue_source_check_evidence_review_ingestion_344b --source-check-evidence-enrichment-344a2-dir D:\_datefac\output\review_queue_source_check_evidence_enrichment_344a2 --demo-audit-snapshot-343o-dir D:\_datefac\output\review_queue_demo_audit_snapshot_343o --limited-demo-export-package-343n-dir D:\_datefac\output\review_queue_limited_demo_export_package_343n --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_expanded_demo_audit_snapshot_344e
```

## 15. Completion report

Report in Chinese:

1. 344E decision
2. review_queue_schema_version
3. input_expanded_export_row_count
4. audit_label_row_count
5. prior_demo_trusted_row_count
6. source_check_trusted_row_count
7. source_check_confirmed_row_count
8. source_check_corrected_row_count
9. correction_row_count
10. expanded_export_scope
11. export_usage
12. expanded_demo_audit_snapshot_generated
13. final_handoff_summary_generated
14. executive_summary_generated
15. trust_chain_report_generated
16. artifact_index_generated
17. final_export_gate_snapshot_generated
18. lineage_audit_summary_generated
19. metric_distribution_generated
20. expanded_demo_arc_closed
21. formal_client_export_allowed
22. client_ready
23. production_ready
24. global_strict_human_review_completed
25. ready_for_345a
26. recommended_345a_scope
27. qa_fail_count
28. no-write-back proof status
29. output directory
30. most important final handoff / executive / trust-chain / artifact-index / final gate / scope boundary files
31. modified files
32. validation command results
33. git status summary
34. confirmation that output/temp/input reviewed workbook/LLM response/protected dirty files were not modified or staged
