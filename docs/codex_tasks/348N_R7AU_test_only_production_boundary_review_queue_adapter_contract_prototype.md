# 348N-R7AU test-only production-boundary review queue adapter contract prototype

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-contract-prototype
```

## Reason

R7AT-QA passed. The production-boundary review queue adapter design is valid, but production code must still remain untouched. R7AU should create a test-only contract prototype that proves the boundary contract with small curated fixtures.

## Workspace

```text
D:\_datefac_agent
branch = pivot/348-agent-foundation
```

## Preflight

Run:

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -12
```

Stop if the worktree is not clean after pull.

## Read first

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348N_R7AT_QA_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_DESIGN_REVIEW.md
docs/agent/348N_R7AT_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_DESIGN.md
docs/agent/348N_R7AS_QA_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_PROTOTYPE_REVIEW.md
docs/agent/348N_R7AS_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_PROTOTYPE_REPORT.md
```

Inspect read-only:

```text
tests/agent/discrepancy_review_queue_integration_boundary_348n.py
tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py
tests/agent/discrepancy_review_queue_policy_348n.py
tests/agent/test_discrepancy_review_queue_policy_348n.py
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
datefac_agent/delivery/evidence_index_writer.py
```

## Goal

Create a test-only production-boundary adapter contract prototype. It should validate the contract between comparison/discrepancy boundary output and future production review queue input without modifying production modules.

The prototype should produce in-memory structures only. It should not write local output reports.

## Allowed tracked files

Create exactly these files:

```text
tests/agent/production_boundary_review_queue_adapter_contract_348n.py
tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7au_production_boundary_contract_fixture.json
docs/agent/348N_R7AU_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REPORT.md
```

No other tracked files may change.

## Prototype requirements

The contract prototype must validate:

```text
1. comparison/discrepancy boundary output is the only accepted input shape.
2. raw MinerU artifacts are rejected.
3. raw DateFac Excel rows are rejected.
4. uncontrolled full source_text is rejected.
5. unreviewed rows cannot become clean_data.
6. VERIFIED rows do not bypass the clean_data gate.
7. non-VERIFIED rows become review queue contract items.
8. unresolved rows become blocked delivery contract rows.
9. discrepancy rows remain metadata-first and bounded-preview only.
10. audit fields preserve run_id, adapter_version, input_file_hashes and deterministic hashes.
11. review_item_id and audit_hash are deterministic.
12. unsupported reviewer actions fail closed.
13. explicit future policy gate is required for any clean_data eligibility.
14. readiness gates remain closed.
```

## Fixture requirements

Use a small curated fixture with at least:

```text
VERIFIED row
DISAGREED row
AMBIGUOUS row
MISSING_EVIDENCE row
PARSE_SKIPPED row
UNVERIFIED row
resolved correction row
unresolved reviewer action row
invalid raw MinerU-like input
invalid raw Excel-like input
invalid full-source-text input
```

## Contract item fields

The future review queue contract item should include at least:

```text
contract_item_id
review_item_id
source_document_id
source_row_id
candidate_metric_name
candidate_period
candidate_value
candidate_unit
agreement_status
subqueue
risk_reason
severity
review_status
reviewer_action
clean_data_eligible
delivery_blocked
evidence_preview
matched_locator
run_id
adapter_version
input_file_hashes
audit_hash
contract_version
created_from
```

## Tests must cover

```text
fixture loads and stays curated
valid boundary output accepted
invalid raw inputs rejected
VERIFIED not auto-cleaned
non-VERIFIED admitted to review queue contract
unresolved rows blocked from clean delivery
bounded evidence preview
metadata-first contract
stable ids and hashes
reviewer action validation is fail-closed
readiness gates remain closed
no production modules are modified
```

## Boundaries

Do not modify production code, existing tests, existing fixtures, output files, dependency files, or readiness gates. Do not run extraction systems. Do not promote VERIFIED to STRONG_EVIDENCE or clean_data.

## Validation commands

Run:

```text
python -m py_compile tests/agent/production_boundary_review_queue_adapter_contract_348n.py tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py
python -m py_compile tests/agent/discrepancy_review_queue_integration_boundary_348n.py tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py
python -m py_compile tests/agent/discrepancy_review_queue_policy_348n.py tests/agent/test_discrepancy_review_queue_policy_348n.py
python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
pytest tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py -q
pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

## Commit rule

If validation passes, stage exactly the four allowed files. Do not use broad staging.

Commit:

```text
git commit -m "test: add production boundary review queue adapter contract prototype"
```

Push:

```text
git push origin pivot/348-agent-foundation
```

Stop after push.

## Required Data Result

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
fixture_result（fixture结果）=
contract_prototype_result（契约原型结果）=
input_rejection_result（输入拒绝结果）=
review_queue_contract_result（复核队列契约结果）=
delivery_gate_contract_result（交付闸门契约结果）=
clean_data_gate_contract_result（clean_data闸门契约结果）=
audit_contract_result（审计契约结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7AU-QA test-only production-boundary review queue adapter contract prototype review
```
