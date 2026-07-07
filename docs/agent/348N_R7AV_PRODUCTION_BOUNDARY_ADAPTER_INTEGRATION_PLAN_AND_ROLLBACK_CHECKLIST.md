# 348N-R7AV production-boundary adapter integration plan and rollback checklist

## Task ID

```text
348N-R7AV production-boundary adapter integration plan and rollback checklist
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating cf3785c..071c449
  Fast-forward
  docs/codex_tasks/348N_R7AV_next.md created

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
```

Worktree was clean after pull and before this report.

## Files reviewed

Task pointer:

- `docs/codex_tasks/348N_R7AV_next.md`

R7AU context:

- `docs/agent/348N_R7AU_QA_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7AU_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REPORT.md`
- `tests/agent/production_boundary_review_queue_adapter_contract_348n.py`
- `tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7au_production_boundary_contract_fixture.json`

R7AT/R7AS context:

- `docs/agent/348N_R7AT_QA_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_DESIGN_REVIEW.md`
- `docs/agent/348N_R7AT_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_DESIGN.md`
- `docs/agent/348N_R7AS_QA_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7AS_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_PROTOTYPE_REPORT.md`

## R7AU-QA recap

R7AU-QA confirmed:

```text
test-only prototype location = tests/agent/
fixture rows = 8 curated rows
invalid input cases = raw MinerU-like, raw Excel-like, full-source-text
review_queue_contract_count = 7
blocked_delivery_contract_count = 6
delivery_reaudit_contract_count = 1
clean_data_eligible_contract_count = 0 by default
verified_review_queue_contract_count = 0
readiness_gates = CLOSED
external_call_counts = zero
production code modified = no
```

R7AU proved the future adapter contract shape but did not create production code.

## Integration goal

Goal:

```text
Plan the next safe adapter step after R7AU-QA: define how the test-only contract can move toward a production-boundary integration slice while preserving fail-closed behavior, metadata-only evidence, delivery blocking, and closed readiness gates.
```

Non-goal:

```text
Do not implement a production adapter in this task.
Do not modify datefac_agent/.
Do not modify tests or fixtures.
Do not create runners or outputs.
Do not open readiness gates.
```

## Recommended boundary

Future integration should sit at this boundary:

```text
validated comparison/discrepancy boundary output
  -> production-boundary adapter contract validation
  -> review_queue candidate records
  -> review/discrepancy outputs
  -> delivery blocking metadata
```

It must not sit inside:

```text
MinerU adapter
PDF/OCR extraction
evidence matcher
clean_data writer
delivery export gate
reviewer UI/persistence layer
```

Recommended future module, only after QA approval:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
```

## Input contract plan

Allowed inputs:

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

Forbidden inputs:

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
evidence_level=STRONG_EVIDENCE from VERIFIED alone
```

## Output contract plan

Future adapter output should remain separated:

```text
review_queue_contract_items -> review workflow only
discrepancy_report_contract_rows -> audit/report output only
blocked_delivery_contract_rows -> delivery blockers only
delivery_reaudit_contract_rows -> re-audit candidate metadata only
audit_contract -> reproducibility and boundary flags
```

No output should be interpreted as:

```text
clean_data admission
formal client delivery
production readiness
STRONG_EVIDENCE promotion
```

## Integration phases

Recommended sequence:

```text
Phase 1: R7AV-QA review of this plan.
Phase 2: test-only production-boundary integration skeleton under tests/agent/, reusing R7AU fixture.
Phase 3: QA of test-only integration skeleton.
Phase 4: design-only production module contract, including exact datefac_agent/ placement and public function signatures.
Phase 5: minimal production implementation behind explicit non-runner imports only.
Phase 6: QA of production implementation with no real output writing.
Phase 7: controlled local dry-run, output not committed.
Phase 8: QA of controlled local dry-run.
```

Do not skip directly from R7AU-QA to production implementation.

## Rollback checklist

Rollback is required if any future adapter slice shows:

```text
datefac_agent/ modified outside approved files
tests/fixtures modified outside approved files
output/ staged or committed
DateFac Excel staged or committed
MinerU output staged or committed
new dependency/config changes
MinerU/OCR/LLM/VLM/PDF extraction invoked
full source_text serialized
raw MinerU or Excel rows accepted as adapter input
VERIFIED becomes STRONG_EVIDENCE automatically
VERIFIED enters clean_data automatically
non-VERIFIED clean_data_eligible=true without explicit future gate
delivery_clean_admitted=true
readiness gate opened
external_call_counts nonzero without explicit task approval
review_item_id / audit_hash nondeterministic
input_file_hashes missing or mismatched
```

Rollback action:

```text
stop the task
discard generated adapter outputs
do not write clean_data
do not write production review_queue records
do not mark manifests successful
record BLOCKED diagnostics in the task report
require a QA task before retry
```

## Fail-closed gates

Future adapter validation must fail closed for:

```text
unknown agreement_status
missing run_id
missing adapter_version
missing input_file_hashes
missing audit_metadata_hash
missing review_item_id for non-VERIFIED item
missing audit_hash
unbounded evidence_preview
forbidden full text fields
unsupported reviewer action
readiness mutation
attempted clean_data admission
attempted production delivery
```

## Readiness policy

R7AV keeps readiness closed:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

Future readiness cannot be opened by the adapter task. It requires a separate readiness task after:

```text
production implementation QA
controlled local dry-run QA
reviewer action audit path
clean_data gate QA
output_schema_guardrails pass
no unresolved critical/high blockers for target scope
explicit human approval
```

## Validation plan for next slice

Minimum validation commands for the next test-only integration skeleton:

```text
python -m py_compile tests/agent/production_boundary_review_queue_adapter_contract_348n.py tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py
python -m py_compile tests/agent/discrepancy_review_queue_integration_boundary_348n.py tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py
pytest tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py -q
pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

If production code is later approved, add targeted py_compile for only the approved production files.

## Boundary review

R7AV stayed docs-only:

```text
datefac_agent/ modified = no
tests/ modified = no
fixtures modified = no
implementation created = no
runner created = no
output committed = no
DateFac Excel committed = no
MinerU output committed = no
dependencies modified = no
MinerU/OCR/LLM/VLM/PDF extraction run = no
readiness gates opened = no
```

## Validation outputs

Commands run:

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
  13 passed

pytest tests/agent -q
  240 passed

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  ?? docs/agent/348N_R7AV_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST.md

git diff --stat
  no tracked diff before staging because the report was untracked

git diff --name-only
  no tracked diff before staging because the report was untracked

git diff --check
  PASS
```

## Decision

```text
Decision = 348N_R7AV_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST_VALID
```

The next adapter step should remain QA/design-first. R7AV recommends R7AV-QA before any production implementation, then a test-only integration skeleton or explicitly approved production-module design. Rollback and fail-closed criteria are explicit, and readiness gates remain closed.

## Recommended next task

```text
348N-R7AV-QA production-boundary adapter integration plan and rollback checklist review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：348N_R7AV_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST_VALID
build_result（构建结果）= PASS：py_compile validation passed
test_result（测试结果）= PASS：pytest tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py -q => 13 passed；pytest tests/agent -q => 240 passed
files_modified（修改文件数）= 1
error_count（错误数）= 0
planning_result（计划结果）= PASS：integration phases defined without production implementation
rollback_checklist_result（回滚清单结果）= PASS：unsafe input, output, clean_data, readiness, and dependency triggers listed
boundary_check（边界检查）= PASS：docs-only; no code/tests/fixtures/output/dependency changes
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AV-QA production-boundary adapter integration plan and rollback checklist review
```
