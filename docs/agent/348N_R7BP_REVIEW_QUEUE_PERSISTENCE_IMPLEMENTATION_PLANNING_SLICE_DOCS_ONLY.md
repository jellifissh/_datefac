# 348N-R7BP review_queue persistence implementation planning slice docs-only

## Task ID

```text
348N-R7BP review_queue persistence implementation planning slice docs-only
```

Task type: docs-only-implementation-planning.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward d027e85..a95995e; R7BP task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -55
PASS: latest history includes a95995e R7BP task doc, d027e85 R7BO-QA, 214a006 R7BO, b223c05 R7BN-QA, 4162ea6 R7BN, ce10b99 R7BM-QA, 9daca34 R7BM, 7713db4 R7BL-QA, and c76499e R7BL.
```

## Files reviewed

Required context reviewed:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/348N_R7BP_review_queue_persistence_implementation_planning_slice_docs_only.md`
- `docs/agent/348N_R7BO_QA_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE_REVIEW.md`
- `docs/agent/348N_R7BO_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE.md`
- `docs/agent/348N_R7BN_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT_REVIEW.md`
- `docs/agent/348N_R7BN_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT.md`
- `docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7BM_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7BK_QA_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE_REVIEW.md`
- `docs/agent/348N_R7BK_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE.md`

Current test-only files reviewed read-only:

- `tests/agent/review_queue_persistence_contract_348n.py`
- `tests/agent/test_review_queue_persistence_contract_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json`
- `tests/agent/review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`

Production-adjacent files reviewed read-only for boundary awareness:

- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`

## R7BO-QA recap

R7BO-QA approved the project documentation sync after the review_queue persistence contract milestone.

Approved baseline:

```text
current chain reaches only test-only persistence contract and in-memory persistence candidate batch
validation counts = 76 / 29 / 36 / 24 / 75 / 480 passed
no real persistence exists
no production readiness exists
readiness_gates = CLOSED
recommended next task = R7BP docs-only implementation planning
```

## 大白话说明

这一轮只写“未来要怎么一步一步安全落库”的计划，不写任何落库代码。

现在已经有的是：

```text
测试区的 review_queue persistence contract
-> 内存里的 persistence candidate batch
```

未来如果要接近真实持久化，不能一步跳到生产数据库。必须先经过 fake repository、负路径扩展、schema/migration 设计、disabled skeleton、本地测试数据库、rollback 测试、生产 gate review。任何一步失败，都不能写 clean_data，不能导出，不能打开 readiness。

## Current baseline

Current approved chain:

```text
adapter candidate output
-> test-only dry-run integration boundary
-> test-only writer dry-run preview
-> test-only schema alignment contract
-> test-only persistence contract
-> in-memory persistence candidate batch
```

Current facts:

```text
current persistence contract is test-only and in-memory
R7BL/R7BM/R7BN/R7BO are approved through QA
latest known validation: persistence targeted 76 passed; schema alignment 29 passed; dry-run integration 36 passed; writer contract 24 passed; adapter skeleton 75 passed; full tests/agent 480 passed
readiness_gates remain CLOSED
```

## Why real persistence remains blocked

Real persistence remains blocked because these have not been designed, implemented, or QA-approved:

- database schema and field-level storage representation;
- repository interface and transaction semantics;
- migration and rollback plan;
- storage engine decision and environment allowlist;
- idempotent retry behavior against real storage;
- duplicate conflict behavior against real constraints;
- production observability and audit event policy;
- leakage prevention for raw payloads in persisted records;
- review UI integration and lifecycle behavior;
- production gate review and readiness approval.

The current in-memory candidate batch proves a validation boundary, not durable storage.

## Implementation planning scope

R7BP only plans the safe sequence from:

```text
test-only persistence contract
-> in-memory persistence candidate batch
-> future fake repository / in-memory repository boundary
-> future database schema planning
-> future migration planning
-> future real repository implementation
-> future production gate review
```

R7BP does not implement any of those steps.

## Proposed future task sequence

Recommended conservative sequence:

```text
R7BQ: fake repository / in-memory repository boundary contract test-only
R7BR: fake repository negative-path and idempotency expansion test-only
R7BS: database schema and migration design docs-only
R7BT: schema/migration QA docs-only
R7BU: repository interface skeleton disabled-by-default, no DB connection
R7BV: repository skeleton QA
R7BW: local test database adapter prototype behind explicit test flag only
R7BX: local test database negative-path and rollback tests
R7BY: production gate review docs-only before any production hook
```

Do not start any of these tasks from R7BP.

## Future file/module boundaries

Possible future files or modules, planning only:

```text
datefac_agent/review/review_queue_persistence_models.py
datefac_agent/review/review_queue_repository.py
datefac_agent/review/review_queue_persistence_service.py
datefac_agent/review/review_queue_persistence_policy.py
tests/agent/test_review_queue_persistence_repository_348n.py
tests/agent/test_review_queue_persistence_service_348n.py
```

These files do not exist as part of R7BP. Creating any of them requires a later explicit implementation task and QA scope.

Boundary intent:

- model/policy modules should define safe record shape and write eligibility only;
- repository module should be the only storage boundary;
- service module should orchestrate validation + repository call but not mutate clean_data or delivery;
- tests should begin with fake/in-memory repository behavior before any DB adapter;
- production code should not import test-only tokens or fixtures.

## Future data model planning

Conceptual persisted record fields may include:

```text
review_item_id
run_id
source_file_hash
input_file_hashes
adapter_version
contract_version
writer_contract_version
schema_version
audit_hash
idempotency_key
metric_name
period
candidate_value
normalized_candidate_value
agreement_status
review_status
review_reason
reviewer_action
blocked_delivery_reason
re_audit_required
evidence_preview
source_trace
created_by_system
record_payload_hash
created_at
updated_at
retracted_at
retraction_reason
```

These are planning candidates only. R7BP does not create a schema, migration, model class, table, index, or repository.

Open data model questions:

- Should `input_file_hashes` and `source_trace` be JSON fields, normalized child tables, or stored compact JSON blobs with hash constraints?
- Should `evidence_preview` length be enforced at application layer, database constraint layer, or both?
- Which timestamp source is acceptable without breaking deterministic idempotency?
- How should retraction records reference the original row without destructive delete?
- Should review status history be a separate event table rather than mutable columns?

## Future repository interface planning

Future repository interface should be narrow and explicit:

```text
validate_storage_capability()
persist_review_queue_candidates(batch, *, policy, request_context)
get_by_idempotency_key(idempotency_key)
get_by_review_item_id(review_item_id)
mark_retracted(review_item_id, reason, audit_context)
```

Required interface behavior:

- accept only validated persistence candidates from the approved service boundary;
- reject raw adapter payloads, schema alignment previews, writer previews, and user direct write payloads;
- return deterministic results for retries;
- surface duplicate conflicts as fail-closed errors or deterministic no-ops;
- never write clean_data, delivery/export artifacts, or readiness state;
- expose no default production DB connection.

## Fake repository stage planning

R7BQ should introduce a fake/in-memory repository boundary contract only.

Goals:

- model repository write shape without DB connection;
- prove candidate batch validation before repository call;
- prove no partial in-memory writes on invalid batch;
- prove idempotent retry behavior;
- prove duplicate `idempotency_key` and duplicate `review_item_id` behavior;
- prove no source_text/raw artifact leakage;
- prove clean_data/delivery/readiness are not mutated.

R7BR should expand negative paths:

- mixed valid/invalid batch;
- duplicate key with same payload;
- duplicate key with different payload;
- malformed source/hash identity;
- forbidden nested raw payloads;
- unbounded `evidence_preview`;
- production writer config leakage;
- test-only token leakage into candidate rows;
- accidental clean_data/delivery/export/review readiness intent.

## Database schema and migration planning

R7BS should be docs-only and answer:

- storage engine choice for local test DB and possible future production DB;
- table naming and namespace;
- required columns, JSON fields, length limits, and nullability;
- unique constraints for `idempotency_key`, `review_item_id`, and batch identity;
- index strategy for run, source file, status, severity, and reviewer workflow;
- migration versioning policy;
- rollback and down migration policy;
- retraction/disable strategy for bad persisted rows;
- audit event table or append-only history strategy;
- retention and deletion policy;
- compatibility with future review UI.

R7BT should QA the schema/migration design before any skeleton code.

## Idempotency and uniqueness planning

Plan uniqueness around:

```text
idempotency_key
record_payload_hash
review_item_id
run_id
source_file_hash / input_file_hashes
schema_version
contract_version
```

Required behavior:

- duplicate `idempotency_key` + identical `record_payload_hash` may become deterministic no-op only if explicitly designed and tested;
- duplicate `idempotency_key` + different `record_payload_hash` must fail closed;
- duplicate `review_item_id` must fail closed unless a retraction/update policy is explicitly designed;
- duplicate behavior must never silently insert multiple active rows;
- unique constraints should match application-level preflight checks;
- retries after transient failure must not create duplicate active records.

## Transaction and rollback planning

Future implementation must handle:

```text
single-row atomic write
batch atomic write or explicitly designed partial mode
no partial commit by default
rollback on any invalid row
retraction/disable strategy for bad persisted rows
no destructive delete as default recovery
write audit event with persistence attempt/result
idempotent retry after transient failure
```

Default policy should be all-or-nothing batch atomicity. Partial commit is out of scope unless a later task designs user-visible partial state, retry semantics, and audit reporting.

## Audit and record hash planning

Future persistence must preserve:

- `run_id`;
- `adapter_version`;
- contract and schema versions;
- `source_file_hash`;
- `input_file_hashes`;
- `audit_hash`;
- `idempotency_key`;
- `record_payload_hash`;
- compact `source_trace`;
- persistence attempt id;
- persistence result status;
- error class for fail-closed rejection.

`record_payload_hash` must remain derived from canonical safe payload fields, not user supplied. Audit events should record both attempted batch hash and final persisted batch hash when a write succeeds.

## Feature flag and environment gate planning

Future implementation must require:

```text
readiness_gates remain CLOSED until a separate gate review
explicit test-only persistence flag for test DB stages
separate production persistence flag only after production gate review
environment allowlist
no default production DB connection
no production writer config in test-only paths
no automatic activation from validated schema alignment preview
```

Suggested staged flags, names to be finalized later:

- `DATEFAC_REVIEW_QUEUE_FAKE_REPOSITORY_TEST_ONLY`;
- `DATEFAC_REVIEW_QUEUE_LOCAL_DB_TEST_ONLY`;
- `DATEFAC_REVIEW_QUEUE_PRODUCTION_PERSISTENCE_ENABLED`, only after R7BY-like gate review.

No future flag should open clean_data, delivery/export, or client readiness automatically.

## Observability and leakage constraints

Future logging/observability must be metadata-first:

- log run id, batch hash, counts, status, and error class;
- do not log full source text;
- do not log raw MinerU, Excel, parser, OCR, LLM, or VLM payloads;
- do not log DB credentials or DSNs;
- do not serialize production writer config into records;
- bound preview snippets and error messages;
- include enough audit metadata for reproducibility without exposing raw artifacts.

Leakage checks should run before any repository call and before any audit event write.

## clean_data and delivery/export separation

Persistence must stay separate from clean_data and delivery/export:

```text
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not auto-write clean_data
non-VERIFIED rows remain review-bound
unresolved rows keep blocked_delivery_reason
corrected rows remain re-audit-required
persistence candidate does not trigger delivery
persistence candidate does not mutate clean_data
persistence candidate does not open readiness gates
bounded evidence_preview allowed
full source_text forbidden
raw MinerU/raw Excel/raw parser/raw LLM-VLM payloads forbidden
```

Future persisted review_queue rows may inform reviewer workflow only. They must not be treated as clean_data admission or export authorization.

## Production gate review requirements

Before any production hook, a docs-only production gate review must verify:

- schema and migration QA passed;
- repository skeleton QA passed;
- local test DB adapter QA passed;
- rollback and idempotent retry tests passed;
- no raw payload leakage tests passed;
- clean_data/delivery/readiness separation tests passed;
- environment allowlist is explicit;
- production connection defaults to disabled;
- operational rollback/retraction procedure is documented;
- reviewer UI and export boundaries are defined;
- security review covers credentials, logs, and audit metadata;
- readiness gates remain closed unless explicitly approved in that gate review.

Production gate review must be separate from implementation tasks.

## QA sequence before real persistence

Minimum QA sequence:

1. R7BQ-QA fake repository contract review.
2. R7BR-QA fake repository negative-path review.
3. R7BT schema/migration design QA.
4. R7BV repository skeleton QA.
5. R7BX local test database negative-path/rollback QA.
6. R7BY production gate review.

Only after this sequence should any production integration planning begin.

## Open questions

- Which storage engine is acceptable for local test DB stages?
- Should production persistence eventually use an existing project DB layer or a new isolated review_queue storage boundary?
- What is the canonical timestamp policy that does not undermine deterministic hashes?
- Is append-only review history required before first real persistence?
- Should corrections create new records, retractions, or linked revision rows?
- How should reviewer UI consume persisted rows without gaining clean_data authority?
- What are maximum `evidence_preview` and `source_trace` sizes in real storage?
- Which migration tool, if any, is already acceptable in this repo?
- What is the rollback policy for a bad migration after rows are persisted?
- What monitoring is required before production hook consideration?

## Non-goals

R7BP does not:

```text
modify production code
modify tests
modify fixtures
add repository/model/service code
add DB schema
add migration
add DB connection
add storage implementation
write output files
run extraction
run MinerU/OCR/LLM/VLM
open readiness gates
claim production persistence
claim production readiness
claim client readiness
claim formal export readiness
```

## Remaining risks

Remaining risks:

- real database schema still not implemented;
- migration/rollback still not implemented;
- transaction behavior is still only planned;
- storage performance/concurrency not proven;
- real review UI integration not proven;
- production operational controls not proven;
- client/export readiness still not implied;
- fake repository tests may miss DB-specific constraint behavior;
- local test DB behavior may not match future production DB behavior;
- production gate scope must remain strict to prevent accidental writer activation.

## Recommended next task

Recommended next task:

```text
348N-R7BP-QA review_queue persistence implementation planning slice review
```

Do not start R7BQ until R7BP-QA verifies this planning slice.

## Validation outputs

```text
python -m py_compile tests/agent/review_queue_persistence_contract_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_persistence_contract_348n.py
PASS

python -m py_compile tests/agent/review_queue_writer_schema_alignment_contract_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py
PASS

python -m py_compile tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
PASS

python -m py_compile tests/agent/review_queue_writer_contract_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_writer_contract_348n.py
PASS

python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
PASS

python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
PASS

python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
PASS: 76 passed in 0.41s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.17s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.15s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.12s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.25s

python -m pytest tests/agent -q
PASS: 480 passed in 1.92s

git status -sb
PASS before report creation: clean.

git diff --stat
PASS before report creation: no tracked diff.

git diff --name-only
PASS before report creation: no tracked diff.

git diff --check
PASS before report creation: no whitespace errors.
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BP docs-only implementation planning report created.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; persistence targeted 76 passed; schema alignment 29 passed; dry-run integration 36 passed; writer contract 24 passed; adapter skeleton 75 passed; full tests/agent 480 passed.
files_modified（修改文件数）= 1 planning report only.
error_count（错误数）= 0.
implementation_planning_result（实施规划结果）= PASS; future persistence path planned without implementation.
current_baseline_result（当前基线结果）= PASS; approved test-only/in-memory chain and validation baseline stated.
future_sequence_result（未来任务顺序结果）= PASS; R7BQ through R7BY conservative sequence proposed.
module_boundary_planning_result（模块边界规划结果）= PASS; possible future files listed as planning-only and not created.
data_model_planning_result（数据模型规划结果）= PASS; candidate fields listed as conceptual only, no schema created.
repository_interface_planning_result（repository接口规划结果）= PASS; narrow future repository interface and behavior planned.
fake_repository_stage_planning_result（fake repository阶段规划结果）= PASS; fake/in-memory stage and negative paths planned.
schema_migration_planning_result（schema/migration规划结果）= PASS; schema and migration questions deferred to docs-only design/QA.
idempotency_uniqueness_planning_result（幂等唯一性规划结果）= PASS; key uniqueness, deterministic no-op, and fail-closed conflicts planned.
transaction_rollback_planning_result（事务回滚规划结果）= PASS; all-or-nothing default, rollback, retraction, and retry requirements planned.
audit_hash_planning_result（审计哈希规划结果）= PASS; audit metadata and derived record_payload_hash strategy planned.
feature_gate_planning_result（feature gate规划结果）= PASS; test flags, production flag separation, and environment allowlist planned.
clean_data_delivery_boundary_result（clean_data/交付边界结果）= PASS; clean_data, delivery/export, evidence, and readiness separation preserved.
production_gate_planning_result（生产gate规划结果）= PASS; separate production gate review required before any production hook.
remaining_risk_result（剩余风险结果）= PASS; schema, migration, transaction, concurrency, review UI, operations, and readiness risks documented.
boundary_check（边界检查）= PASS; only allowed planning report created.
readiness_gates（就绪门）= CLOSED.
recommended_next_task（推荐下一任务）= 348N-R7BP-QA review_queue persistence implementation planning slice review.
```
