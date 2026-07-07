# 348N-R7AX disabled adapter skeleton contract hardening

Task type: contract-hardening-only.

Workspace: D:\_datefac_agent
Branch: pivot/348-agent-foundation

R7AW-QA passed. The disabled adapter skeleton is valid. R7AX should harden only that skeleton slice against malformed boundary-like payloads. Keep it disabled by default. Do not add pipeline hookup, IO, exports, dependency changes, or readiness changes.

Read first:
- docs/agent/348N_R7AW_QA_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REVIEW.md
- docs/agent/348N_R7AW_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REPORT.md
- docs/agent/348N_R7AV_QA_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST_REVIEW.md
- docs/agent/348N_R7AU_QA_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REVIEW.md

Allowed files:
- datefac_agent/review/production_boundary_review_queue_adapter.py
- tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
- tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
- docs/agent/348N_R7AX_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REPORT.md

No other tracked files may change.

Harden checks for:
- required audit metadata
- expected contract_version
- run_id, adapter_version, input_file_hashes
- unknown agreement_status
- unknown reviewer_action
- unsafe clean_data_eligible input
- unsafe readiness_gates input
- unresolved non-VERIFIED delivery state
- nested source_text fields
- oversized evidence_preview
- missing evidence_preview where required
- output not sharing mutable input references
- stable review_item_id and audit_hash
- parser-like payload rejected

Preserve behavior:
- disabled by default
- explicit test-only enable required
- in-memory candidate output only
- no IO
- no production hook
- VERIFIED never auto-enters clean_data
- non-VERIFIED stays review-bound
- unresolved rows stay blocked from clean delivery
- readiness gates stay CLOSED

Run:
- python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
- python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
- pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
- pytest tests/agent -q
- git status -sb
- git diff --stat
- git diff --name-only
- git diff --check

Report must include Data Result with:
Decision, build_result, test_result, files_modified, error_count, hardening_result, input_contract_hardening_result, reviewer_action_hardening_result, clean_data_delivery_guard_result, evidence_preview_hardening_result, audit_metadata_hardening_result, determinism_immutability_result, no_hook_no_io_result, boundary_check, readiness_gates, recommended_next_task.

Recommended next task: 348N-R7AX-QA disabled adapter skeleton contract hardening review

Commit exactly the allowed files:
- git add datefac_agent/review/production_boundary_review_queue_adapter.py
- git add tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
- git add tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
- git add docs/agent/348N_R7AX_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REPORT.md
- git commit -m "test: harden disabled review queue adapter contract"
- git push origin pivot/348-agent-foundation

Stop after push.
