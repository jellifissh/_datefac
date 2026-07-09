# 348N-R7BP-QA review_queue persistence implementation planning slice review

## Task ID

```text
348N-R7BP-QA review_queue persistence implementation planning slice review
```

Task type: QA-review-only.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward e08f6c6..06c64a3; R7BP-QA task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -55
PASS: latest history includes 06c64a3 R7BP-QA task doc, e08f6c6 R7BP planning report, d027e85 R7BO-QA, 214a006 R7BO, b223c05 R7BN-QA, 4162ea6 R7BN, ce10b99 R7BM-QA, and c76499e R7BL.
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
- `docs/codex_tasks/348N_R7BP_QA_review_queue_persistence_implementation_planning_slice_review.md`
- `docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md`
- `docs/agent/348N_R7BO_QA_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE_REVIEW.md`
- `docs/agent/348N_R7BO_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE.md`
- `docs/agent/348N_R7BN_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT_REVIEW.md`
- `docs/agent/348N_R7BN_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT.md`
- `docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7BM_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7BK_QA_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE_REVIEW.md`

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

Production-adjacent modules reviewed read-only for boundary awareness:

- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`

## R7BP recap

R7BP created a docs-only implementation planning report:

```text
docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md
```

Commit scope check:

```text
git show --stat --oneline --name-only e08f6c6
PASS: R7BP changed only the allowed planning report.
```

The report plans a future path from test-only in-memory persistence candidates toward possible real review_queue persistence, but explicitly does not implement persistence.

## 大白话说明审查

PASS. R7BP clearly says this slice only plans “future real persistence should be staged safely.” It does not build tables, write repository code, add migration code, connect to a database, add production flags, or open readiness gates.

The plain-language explanation correctly says future work must pass fake repository, negative paths, schema/migration design, disabled skeleton, local test database, rollback tests, and production gate review before any production hook.

## Current baseline review

PASS. The baseline is accurate:

```text
adapter candidate output
-> test-only dry-run integration boundary
-> test-only writer dry-run preview
-> test-only schema alignment contract
-> test-only persistence contract
-> in-memory persistence candidate batch
```

The report states the current persistence contract is test-only and in-memory, R7BL/R7BM/R7BN/R7BO are QA-approved, latest validation is `76 / 29 / 36 / 24 / 75 / 480 passed`, and readiness gates remain `CLOSED`.

## Why real persistence remains blocked review

PASS. The report correctly lists blockers:

- database schema and storage representation not designed;
- repository interface and transaction semantics not implemented;
- migration and rollback plan missing;
- storage engine and environment allowlist undecided;
- idempotent retry and duplicate conflict behavior against real storage unproven;
- observability and audit event policy not implemented;
- raw payload leakage prevention not proven against real storage/logging;
- review UI integration missing;
- production gate review and readiness approval absent.

## Implementation planning scope review

PASS. Scope is planning only:

```text
test-only persistence contract
-> in-memory persistence candidate batch
-> future fake repository / in-memory repository boundary
-> future database schema planning
-> future migration planning
-> future real repository implementation
-> future production gate review
```

The report explicitly says R7BP does not implement those steps.

## Proposed future task sequence review

PASS. The sequence is conservative and does not jump to production implementation:

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

The plan includes fake repository before DB, schema/migration design and QA before implementation, skeleton and QA before DB connection, local test DB behind explicit test flag only, negative-path/rollback tests before production gate review, and a production gate review before any hook.

## Future file/module boundaries review

PASS. The report lists possible future module locations only and explicitly says they do not exist as part of R7BP:

- `datefac_agent/review/review_queue_persistence_models.py`
- `datefac_agent/review/review_queue_repository.py`
- `datefac_agent/review/review_queue_persistence_service.py`
- `datefac_agent/review/review_queue_persistence_policy.py`
- `tests/agent/test_review_queue_persistence_repository_348n.py`
- `tests/agent/test_review_queue_persistence_service_348n.py`

No such files were created in R7BP.

## Future data model planning review

PASS. The report lists conceptual candidate fields only, including identity, hash, audit, status, evidence preview, source trace, timestamps, and retraction fields. It explicitly says these are planning candidates only and that R7BP does not create a schema, migration, model class, table, index, or repository.

## Future repository interface planning review

PASS. The proposed interface is narrow and future-facing:

- `validate_storage_capability()`;
- `persist_review_queue_candidates(...)`;
- `get_by_idempotency_key(...)`;
- `get_by_review_item_id(...)`;
- `mark_retracted(...)`.

The behavior rejects raw adapter/schema/writer/direct write payloads, returns deterministic retry behavior, surfaces duplicate conflicts as fail-closed errors or explicit deterministic no-ops, never writes clean_data or delivery/export artifacts, and exposes no default production DB connection.

## Fake repository stage planning review

PASS. The fake/in-memory repository stage is planned before real DB work and covers:

- pre-repository batch validation;
- no partial in-memory writes on invalid batch;
- idempotent retry behavior;
- duplicate `idempotency_key` and `review_item_id` behavior;
- source_text/raw artifact leakage prevention;
- clean_data/delivery/readiness non-mutation.

The negative-path expansion stage is also planned separately for R7BR.

## Database schema and migration planning review

PASS. The report defers schema and migration questions to R7BS/R7BT and does not implement them. It asks the necessary questions about storage engine, table naming, columns, JSON fields, length limits, constraints, indexes, migration versioning, rollback, retraction, audit history, retention, deletion, and review UI compatibility.

## Idempotency and uniqueness planning review

PASS. The plan covers:

- `idempotency_key`;
- `record_payload_hash`;
- `review_item_id`;
- `run_id`;
- `source_file_hash` / `input_file_hashes`;
- `schema_version`;
- `contract_version`.

It forbids silent duplicate insert. Duplicate same-key/same-payload no-op is allowed only if explicitly designed and tested; same-key/different-payload must fail closed.

## Transaction and rollback planning review

PASS. The plan requires:

- single-row atomic writes;
- batch atomic write by default;
- no partial commit unless explicitly designed later;
- rollback on any invalid row;
- retraction/disable strategy for bad persisted rows;
- no destructive delete as default recovery;
- persistence attempt/result audit event;
- idempotent retry after transient failure.

## Audit and record hash planning review

PASS. The report requires preserving run, adapter, contract/schema, source hash, input hashes, audit hash, idempotency key, `record_payload_hash`, source trace, attempt id, result status, and fail-closed error class. It also requires `record_payload_hash` to remain derived from canonical safe fields, not user supplied.

## Feature flag and environment gate planning review

PASS. The report requires:

- readiness gates remain closed until separate gate review;
- explicit test-only persistence flag for test DB stages;
- separate production persistence flag only after production gate review;
- environment allowlist;
- no default production DB connection;
- no production writer config in test-only paths;
- no automatic activation from validated schema alignment preview.

## Observability and leakage constraints review

PASS. The plan keeps observability metadata-first and forbids logging full source text, raw MinerU/Excel/parser/OCR/LLM/VLM payloads, DB credentials, DSNs, and production writer config. It also requires bounded preview snippets and leakage checks before repository calls and audit-event writes.

## clean_data and delivery/export separation review

PASS. The report restates all core safety rules:

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

It says future persisted review_queue rows may inform reviewer workflow only and must not become clean_data admission or export authorization.

## Production gate review requirements review

PASS. Before any production hook, the report requires separate docs-only gate review covering schema/migration QA, repository skeleton QA, local test DB QA, rollback/idempotent retry tests, leakage tests, clean_data/delivery/readiness separation, environment allowlist, disabled production connection defaults, rollback/retraction procedures, reviewer UI/export boundaries, credential/log/audit security review, and readiness gate status.

## QA sequence before real persistence review

PASS. The report requires QA gates before real persistence:

1. R7BQ-QA fake repository contract review.
2. R7BR-QA fake repository negative-path review.
3. R7BT schema/migration design QA.
4. R7BV repository skeleton QA.
5. R7BX local test database negative-path/rollback QA.
6. R7BY production gate review.

## Open questions review

PASS. Open questions are explicit and relevant: storage engine, storage boundary, timestamp policy, append-only history, correction/retraction model, review UI authority, preview/source trace limits, migration tool, rollback policy, and production monitoring.

## Non-goals review

PASS. R7BP explicitly does not:

- modify production code;
- modify tests;
- modify fixtures;
- add repository/model/service code;
- add DB schema;
- add migration;
- add DB connection;
- add storage implementation;
- write output files;
- run extraction or MinerU/OCR/LLM/VLM;
- open readiness gates;
- claim production persistence, production readiness, client readiness, or formal export readiness.

## Remaining risks review

PASS. Remaining risks are explicit:

- real database schema still not implemented;
- migration/rollback still not implemented;
- transaction behavior still only planned;
- storage performance/concurrency not proven;
- real review UI integration not proven;
- production operational controls not proven;
- client/export readiness still not implied;
- fake repository and local test DB may not fully match production DB behavior.

## Recommended next task review

PASS. R7BP recommends:

```text
348N-R7BP-QA review_queue persistence implementation planning slice review
```

That was correct for this turn. After this QA, the safe next task is:

```text
348N-R7BQ fake repository / in-memory repository boundary contract test-only
```

## Boundary review

PASS. This QA creates only:

```text
docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md
```

No production code, tests, fixtures, outputs, dependencies, integrations, database models, writer implementations, migrations, planning docs, handoff docs, extraction systems, or readiness gates are modified.

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
PASS: 29 passed in 0.18s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.15s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.15s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.26s

python -m pytest tests/agent -q
PASS: 480 passed in 1.85s

git status -sb
PASS before QA report creation: clean.

git diff --stat
PASS before QA report creation: no tracked diff.

git diff --name-only
PASS before QA report creation: no tracked diff.

git diff --check
PASS before QA report creation: no whitespace errors.
```

## Limitations

- This is a docs-only QA review.
- It does not implement fake repository, real repository, schema, migrations, DB connection, storage code, production hook, or readiness gates.
- Future implementation still requires separate scoped tasks and QA.

## Decision

PASS. R7BP is a conservative, accurate docs-only implementation planning slice. It plans a staged future persistence path without implementing or authorizing real persistence, and it preserves test-only, in-memory, clean_data-safe, delivery/export-safe, source_text-safe, no-production, and readiness-closed boundaries.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BP-QA approved.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; persistence targeted 76 passed; schema alignment 29 passed; dry-run integration 36 passed; writer contract 24 passed; adapter skeleton 75 passed; full tests/agent 480 passed.
files_modified（修改文件数）= 1 QA report only.
error_count（错误数）= 0.
implementation_planning_review_result（实施规划审查结果）= PASS; docs-only plan is conservative and does not implement persistence.
current_baseline_review_result（当前基线审查结果）= PASS; approved test-only/in-memory chain and validation baseline are accurate.
future_sequence_review_result（未来任务顺序审查结果）= PASS; R7BQ through R7BY sequence is conservative and gate-ordered.
module_boundary_planning_review_result（模块边界规划审查结果）= PASS; future module paths are planning-only and not created.
data_model_planning_review_result（数据模型规划审查结果）= PASS; future fields are conceptual only and no schema exists.
repository_interface_planning_review_result（repository接口规划审查结果）= PASS; interface is narrow and rejects wrong-layer/raw/direct write payloads.
fake_repository_stage_planning_review_result（fake repository阶段规划审查结果）= PASS; fake/in-memory stage precedes real DB work and includes negative paths.
schema_migration_planning_review_result（schema/migration规划审查结果）= PASS; schema and migration are deferred to docs-only design and QA.
idempotency_uniqueness_planning_review_result（幂等唯一性规划审查结果）= PASS; silent duplicate insert forbidden; conflicts fail closed unless explicit no-op is designed/tested.
transaction_rollback_planning_review_result（事务回滚规划审查结果）= PASS; atomic/no-partial default, rollback, retraction, retry, and no destructive delete planned.
audit_hash_planning_review_result（审计哈希规划审查结果）= PASS; audit metadata and derived record_payload_hash requirements are explicit.
feature_gate_planning_review_result（feature gate规划审查结果）= PASS; test flags, production flag separation, environment allowlist, no default production DB connection, and no automatic activation are explicit.
clean_data_delivery_boundary_review_result（clean_data/交付边界审查结果）= PASS; clean_data, delivery/export, evidence, source_text, and readiness separation preserved.
production_gate_planning_review_result（生产gate规划审查结果）= PASS; separate production gate review required before any production hook.
remaining_risk_review_result（剩余风险审查结果）= PASS; schema, migration, transaction, performance/concurrency, review UI, operations, and readiness risks explicit.
boundary_check（边界检查）= PASS; only this QA report is created.
readiness_gates（就绪门）= CLOSED.
recommended_next_task（推荐下一任务）= 348N-R7BQ fake repository / in-memory repository boundary contract test-only.
```
