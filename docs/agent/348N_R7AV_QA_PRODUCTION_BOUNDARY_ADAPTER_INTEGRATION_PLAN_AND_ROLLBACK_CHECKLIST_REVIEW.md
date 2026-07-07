# 348N-R7AV-QA production-boundary adapter integration plan and rollback checklist review

## Task ID

```text
348N-R7AV-QA production-boundary adapter integration plan and rollback checklist review
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Already up to date.

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  1edcfc9 docs: add R7AV QA review task
  a5d6ff1 docs: add R7AV adapter integration plan
  071c449 docs: add R7AV next task
  cf3785c docs: add R7AU QA review
  928e2e1 docs: append R7AU QA pointer
  4ad2e39 test: add production boundary review queue adapter contract prototype
  6e3070c docs: add R7AU contract prototype task
  ecb5908 docs: add R7AT QA review
  897681a docs: add R7AT production boundary adapter design
  b402e57 docs: add R7AS QA review
  5bddf67 test: add discrepancy review queue integration boundary prototype
  f01bd54 docs: add R7AR integration boundary design
```

Worktree was clean after pull and before this QA report.

## Files reviewed

Required task and project context:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R7AV_QA_production_boundary_adapter_integration_plan_and_rollback_checklist_review.md`

R7AV/R7AU/R7AT evidence:

- `docs/agent/348N_R7AV_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST.md`
- `docs/agent/348N_R7AU_QA_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7AU_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7AT_QA_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_DESIGN_REVIEW.md`

Read-only boundary files:

- `tests/agent/production_boundary_review_queue_adapter_contract_348n.py`
- `tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py`
- `tests/agent/discrepancy_review_queue_integration_boundary_348n.py`
- `tests/agent/discrepancy_review_queue_policy_348n.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/delivery/evidence_index_writer.py`

## R7AV recap

R7AV commit reviewed:

```text
a5d6ff1 docs: add R7AV adapter integration plan
```

Observed changed file:

```text
docs/agent/348N_R7AV_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST.md
```

QA result:

```text
PASS: R7AV created a docs-only integration plan and rollback checklist.
PASS: R7AV did not modify datefac_agent/, tests/, fixtures, outputs, dependencies, DateFac Excel, or MinerU artifacts.
PASS: R7AV did not implement a production adapter, runner, extraction path, or readiness change.
```

## Planning review

R7AV defines a conservative integration sequence:

```text
R7AV-QA
-> test-only production-boundary integration skeleton under tests/agent/
-> QA of skeleton
-> design-only production module contract
-> minimal production implementation only if explicitly approved
-> production implementation QA
-> controlled local dry-run
-> dry-run QA
```

QA result:

```text
PASS: phases are explicit and do not jump directly from R7AU-QA into production implementation.
PASS: future adapter boundary is placed after validated comparison/discrepancy output and before review persistence/delivery writing.
PASS: R7AV states the adapter is not a MinerU adapter, PDF/OCR extractor, matcher, clean_data writer, delivery gate, or reviewer UI.
PASS: recommended next task remains a test-only skeleton under disabled conditions, not production wiring.
```

## Rollback checklist review

R7AV rollback triggers include:

```text
unexpected datefac_agent/ drift
unexpected tests/fixtures drift
output, DateFac Excel, or MinerU artifact staging
dependency/config changes
MinerU/OCR/LLM/VLM/PDF extraction invocation
raw MinerU or Excel rows accepted as adapter input
full source_text serialization
VERIFIED -> STRONG_EVIDENCE promotion
VERIFIED -> clean_data auto admission
non-VERIFIED clean_data_eligible=true without explicit future gate
delivery_clean_admitted=true
readiness gates opened
nonzero external calls without explicit approval
nondeterministic review_item_id / audit_hash
missing or mismatched input_file_hashes
```

QA result:

```text
PASS: rollback checklist covers git/source drift, dependency/config drift, data/output artifacts, unsafe inputs, clean/readiness mutation, and reproducibility failures.
PASS: rollback action is fail-closed: stop, discard generated adapter outputs, avoid clean_data/review_queue production writes, avoid success manifests, and require QA before retry.
PASS: checklist is suitable before any implementation slice.
```

## Input validation plan review

Allowed future input is limited to validated boundary output:

```text
R7AS/R7AU-shaped boundary output
review_queue_items
discrepancy_report_rows
blocked_delivery_rows
delivery_reaudit rows
audit_metadata
run_id
adapter_version
input_file_hashes
readiness_gates snapshot
external_call_counts
bounded evidence_preview
locator/hash metadata
```

Forbidden input includes:

```text
raw MinerU artifacts
raw DateFac Excel rows
full source_text
full table HTML
raw PDF text
unreviewed comparison rows
unknown statuses
rows missing audit metadata
opened readiness gates
clean_data_admitted=true
evidence_level=STRONG_EVIDENCE caused by VERIFIED alone
```

QA result:

```text
PASS: input plan accepts only validated, metadata-first boundary output.
PASS: invalid, uncontrolled, raw, full-text, or missing-metadata inputs are rejected by plan.
PASS: plan is aligned with R7AU contract tests that reject raw MinerU-like, raw Excel-like, and full-source-text inputs.
```

## Review queue write plan review

R7AV output contract separates:

```text
review_queue_contract_items -> review workflow only
discrepancy_report_contract_rows -> audit/report output only
blocked_delivery_contract_rows -> delivery blockers only
delivery_reaudit_contract_rows -> re-audit candidate metadata only
audit_contract -> reproducibility and boundary flags
```

QA result:

```text
PASS: non-VERIFIED rows remain review-bound.
PASS: VERIFIED rows do not become discrepancy review_queue records by default.
PASS: review queue payload remains metadata-first and bounded.
PASS: output contract is not clean_data admission, formal delivery, production readiness, or STRONG_EVIDENCE promotion.
```

## Clean data gate plan review

R7AV keeps clean-data admission out of the adapter plan:

```text
VERIFIED cannot automatically become STRONG_EVIDENCE.
VERIFIED cannot automatically enter clean_data.
non-VERIFIED cannot become clean_data_eligible=true without explicit future gate.
delivery_clean_admitted=true is a rollback trigger.
```

QA result:

```text
PASS: clean_data remains guarded by a separate future policy gate.
PASS: adapter can prepare review/re-audit metadata but cannot write clean rows or mutate clean admission.
PASS: plan aligns with existing clean_candidate_policy and R7AU contract behavior.
```

## Delivery gate plan review

R7AV blocks unresolved or unsafe rows from delivery:

```text
blocked_delivery_contract_rows are blockers only.
delivery_reaudit rows are metadata-only candidates.
attempted production delivery or delivery_clean_admitted=true fails closed.
```

QA result:

```text
PASS: unresolved rows remain delivery-blocked.
PASS: review/discrepancy outputs are not treated as formal client delivery.
PASS: plan preserves demo/review boundaries and does not open delivery readiness.
```

## Audit metadata plan review

R7AV requires audit anchors:

```text
run_id
adapter_version
input_file_hashes
audit_metadata_hash
review_item_id
audit_hash
readiness_gates snapshot
external_call_counts
locator/hash metadata
```

QA result:

```text
PASS: audit metadata is sufficient for reproducibility without full source_text.
PASS: missing run_id, adapter_version, input_file_hashes, audit_metadata_hash, review_item_id, or audit_hash fails closed by plan.
PASS: nondeterministic IDs/hashes and missing/mismatched input_file_hashes are rollback triggers.
```

## Readiness gate plan review

R7AV keeps the default readiness state:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

Future readiness can only be considered after:

```text
production implementation QA
controlled local dry-run QA
reviewer action audit path
clean_data gate QA
output_schema_guardrails pass
no unresolved critical/high blockers for target scope
explicit human approval
```

QA result:

```text
PASS: readiness gates remain CLOSED.
PASS: adapter tasks cannot open readiness by themselves.
PASS: future readiness criteria are separate, explicit, and gated by QA plus human approval.
```

## Boundary review

QA result:

```text
PASS: this QA creates only docs/agent/348N_R7AV_QA_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST_REVIEW.md.
PASS: no production code was modified.
PASS: no tests or fixtures were modified.
PASS: no output, DateFac Excel, MinerU artifact, dependency, or config file was modified or staged.
PASS: no MinerU / OCR / LLM / VLM / real PDF extraction was run.
PASS: no production pipeline hook was created.
PASS: no VERIFIED -> STRONG_EVIDENCE promotion.
PASS: no VERIFIED -> clean_data admission.
PASS: readiness gates remain CLOSED.
```

## Validation outputs

Required commands run:

```text
python -m py_compile tests/agent/production_boundary_review_queue_adapter_contract_348n.py tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py
  PASS

python -m py_compile tests/agent/discrepancy_review_queue_integration_boundary_348n.py tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py
  PASS

python -m py_compile tests/agent/discrepancy_review_queue_policy_348n.py tests/agent/test_discrepancy_review_queue_policy_348n.py
  PASS

python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
  PASS

python -m py_compile datefac_agent/review/clean_candidate_policy.py
  PASS

python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
  PASS

pytest tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py -q
  13 passed in 0.10s

pytest tests/agent -q
  240 passed in 0.95s

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  ?? docs/agent/348N_R7AV_QA_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST_REVIEW.md

git diff --stat
  no tracked diff before staging because the QA report was untracked

git diff --name-only
  no tracked diff before staging because the QA report was untracked

git diff --check
  PASS
```

## Limitations

- This QA reviews a docs-only plan and rollback checklist; it does not validate a production implementation.
- No production adapter exists in `datefac_agent/`.
- Current project progress handoff files still contain older milestone pointers; the current task document and recent git history are used as the authoritative task scope for R7AV-QA.
- The next safe step should remain test-only and disabled by default.

## Decision

```text
Decision = 348N_R7AV_QA_CONFIRMED_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST_VALID
```

R7AV-QA confirms the integration plan is conservative, rollback-ready, metadata-first, fail-closed, and non-promotional. It authorizes no production implementation, no production hook, no full-source serialization, no clean_data admission, and no readiness change. The next step should remain a test-only production-boundary adapter skeleton under a disabled flag.

## Recommended next task

```text
348N-R7AW test-only production-boundary adapter skeleton under disabled flag
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：348N_R7AV_QA_CONFIRMED_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST_VALID
build_result（构建结果）= PASS：py_compile validation passed
test_result（测试结果）= PASS：pytest tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py -q => 13 passed；pytest tests/agent -q => 240 passed
files_modified（修改文件数）= 1：docs/agent/348N_R7AV_QA_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST_REVIEW.md
error_count（错误数）= 0
planning_review_result（计划审查结果）= PASS：phased plan remains QA/test-only first and does not jump to production
rollback_checklist_review_result（回滚清单审查结果）= PASS：unsafe source drift, output/dependency drift, raw inputs, full text leakage, clean/readiness mutation, and reproducibility failures are rollback triggers
input_validation_plan_review_result（输入校验计划审查结果）= PASS：only validated metadata-first boundary output is accepted; raw/uncontrolled/full-text/missing-metadata input fails closed
review_queue_write_plan_review_result（复核队列写入计划审查结果）= PASS：non-VERIFIED rows remain review-bound; VERIFIED remains non-promotional
clean_data_gate_plan_review_result（clean_data闸门计划审查结果）= PASS：adapter cannot write or admit clean_data; explicit future gate required
delivery_gate_plan_review_result（交付闸门计划审查结果）= PASS：unresolved rows remain blocked from delivery; re-audit rows are metadata-only
audit_metadata_plan_review_result（审计元数据计划审查结果）= PASS：run_id / adapter_version / input_file_hashes / stable ids / hashes are required
readiness_gate_plan_review_result（就绪门计划审查结果）= PASS：readiness stays closed and future opening requires separate QA plus explicit approval
boundary_check（边界检查）= PASS：QA report only; no datefac_agent/tests/fixture/output/dependency changes; no extraction/model calls
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AW test-only production-boundary adapter skeleton under disabled flag
```
