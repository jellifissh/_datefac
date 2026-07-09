# 348N-R7BS-QA database schema and migration design review

## Task ID

```text
348N-R7BS-QA database schema and migration design review
```

Task type: QA-review-only.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward 5c6553d..13fdb03; R7BS-QA task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -70
PASS: latest history includes 13fdb03 R7BS-QA task doc, 5c6553d R7BS design report, 408da10 R7BS task doc, and 69578a4 R7BR-QA.
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
- `docs/codex_tasks/348N_R7BS_QA_database_schema_and_migration_design_review.md`
- `docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md`
- `docs/agent/348N_R7BR_QA_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md`
- `docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md`

Current test-only files reviewed read-only:

- `tests/agent/review_queue_fake_repository_boundary_348n.py`
- `tests/agent/test_review_queue_fake_repository_boundary_348n.py`
- `tests/agent/review_queue_persistence_contract_348n.py`
- `tests/agent/test_review_queue_persistence_contract_348n.py`
- `tests/agent/review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`

## R7BS recap

R7BS commit `5c6553d` created exactly one docs-only design report:

- `docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md`

No production code, tests, fixtures, dependency files, output files, database schema files, migration files, repository/model/service implementations, storage implementations, writers, runners, production hooks, or readiness gates were modified.

R7BS designed a future conceptual review_queue persistence schema and migration strategy while explicitly keeping the current stack test-only and in-memory.

## 大白话说明审查

PASS. R7BS 没有“偷偷开始落库”。它只是把将来如果真的要做 review_queue persistence，应该有哪些表、字段、索引、唯一约束、幂等规则、审计字段、回滚/前向修复、软撤回、feature gate 和 readiness 审查说清楚。报告反复声明这不是实现：没有建表、没有 migration、没有 repository、没有数据库连接、没有生产 hook，也没有打开 readiness。

## Docs-only boundary review

PASS. The report clearly states it is conceptual and docs-only. It explicitly says it does not create a database schema, migration, repository, service, runner, output, or production hook.

R7BS changed only the allowed docs-only report. `git show --stat --name-only 5c6553d --` confirms only:

```text
docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md
```

No implementation files were added or modified.

## Current baseline review

PASS. The current baseline is accurately stated:

```text
adapter candidate output
-> test-only dry-run integration boundary
-> test-only writer dry-run preview
-> test-only schema alignment contract
-> test-only persistence contract
-> in-memory persistence candidate batch
-> test-only fake repository / in-memory repository boundary
-> fake repository negative-path and idempotency expansion
```

The report correctly states:

- current persistence stack is still test-only and in-memory;
- no real DB persistence exists;
- no database model exists;
- no repository class exists;
- no migration exists;
- no production persistence hook exists;
- R7BR-QA approved fake repository targeted tests at `63 passed`;
- latest known full `tests/agent` is `543 passed`;
- readiness gates remain CLOSED.

## Conceptual table design review

PASS. The report proposes `review_queue_items` as a conceptual primary table and optional future audit tables:

- `review_queue_item_events`;
- `review_queue_persistence_attempts`;
- `review_queue_migration_runs`.

The optional tables are explicitly marked as future-only and not implemented. The table purpose is metadata-first, review-bound persistence, not clean_data delivery/export.

## Conceptual column design review

PASS. The conceptual column list covers:

- identity fields;
- source/input/version metadata;
- review status/action fields;
- evidence preview/source trace fields;
- idempotency and payload hash fields;
- DB-controlled timestamps;
- soft retraction fields.

The report explicitly says these fields are not an implemented schema. It also flags `candidate_unit` and JSON/JSONB source trace choices as future design decisions rather than irreversible implementation choices.

## Identity and hash field review

PASS. Identity/hash fields are covered:

- `review_item_id`;
- `run_id`;
- `source_file_hash`;
- `input_file_hashes`;
- `audit_hash`;
- `idempotency_key`;
- `record_payload_hash`;
- `evidence_preview_sha256`;
- `matched_text_sha256`.

The report requires lowercase 64-character SHA-256 hex hashes, repository-side hash recomputation before write, immutability after accepted write unless versioned/retracted, and fail-closed behavior on mismatch.

## Review status/action field review

PASS. The design admits only review-bound statuses by default:

```text
UNVERIFIED
DISAGREED
AMBIGUOUS
MISSING_EVIDENCE
PARSE_SKIPPED
```

It explicitly prevents `VERIFIED` from automatically entering review_queue persistence and forbids review statuses/actions that imply clean_data approval, delivery unblock, export readiness, or evidence-level promotion.

Corrective reviewer actions require `re_audit_required = true`, preserving the conservative policy that reviewer correction does not bypass later audit gates.

## Evidence preview and source trace review

PASS. Evidence design remains bounded and metadata-only:

- `evidence_preview` is bounded;
- `evidence_preview_sha256` is stored as hash identity;
- `source_trace` uses required metadata fields;
- `matched_text_sha256` stores a hash rather than full matched text.

The report explicitly forbids full `source_text`, raw PDF text pages, raw MinerU/Excel/parser/OCR/LLM/VLM payloads, DB DSN, file/output path config, production writer config, readiness override, clean_data intent, and delivery/export intent.

## Audit metadata review

PASS. Audit metadata covers run/input/version/hash identity and future metadata-only event concepts. The report recommends recording persistence attempt/result metadata without raw source payloads.

Audit metadata remains explanatory and reproducibility-focused; it does not claim real audit-event persistence exists today.

## Idempotency and uniqueness review

PASS. The report covers:

- `unique(idempotency_key)`;
- `unique(review_item_id)`;
- conceptual composite uniqueness on `(run_id, source_file_hash, metric_name, period, schema_version, contract_version)`;
- same key + same hash retry as deterministic no-op or same-receipt policy;
- same key + different hash as fail-closed conflict;
- same review item + different idempotency key as fail-closed conflict;
- changed payload under same identity as fail-closed;
- no silent duplicate insert;
- duplicate idempotency/review item in a batch fails before insert.

The active-row versus global uniqueness question for soft retraction is correctly left open for future review.

## Index and query pattern review

PASS. The design covers indexes and query patterns for:

- `review_item_id`;
- `idempotency_key`;
- `run_id`;
- `source_file_hash`;
- `review_status`;
- `agreement_status`;
- `re_audit_required`;
- `created_at` / `updated_at`;
- reviewer UI pagination;
- `record_payload_hash`;
- source/debug lookup by `source_document_id`, `source_row_id`, and `matched_locator`.

The report correctly postpones JSON/JSONB indexing choices until DB backend selection and performance testing.

## Constraint and enum review

PASS. The design includes conceptual check/enum constraints for:

- agreement status;
- review status;
- reviewer action;
- blocked delivery reason;
- boolean `re_audit_required`;
- allowlisted `created_by_system`;
- bounded `evidence_preview`;
- SHA-256 hash format fields;
- retraction reason requirement.

It explicitly states stored review_queue rows must not imply `STRONG_EVIDENCE`, clean_data admission, delivery/export unblock, or readiness-gate opening.

## Raw-payload exclusion review

PASS. Raw-payload exclusion is explicit and layered:

1. contract validation rejects forbidden keys recursively;
2. repository validation repeats forbidden-key checks;
3. DB schema stores only allowlisted columns;
4. audit events store metadata and hashes only;
5. QA tests inspect serialized rows/receipts for full-source/raw-payload leakage.

Only bounded `evidence_preview` and `source_trace` metadata may be stored.

## Transaction and batch atomicity review

PASS. The report preserves:

- single-row atomicity;
- batch all-or-nothing behavior;
- no partial success by default;
- rollback transaction on invalid row/hash mismatch/conflict/forbidden field/enum violation/readiness or clean/delivery implication;
- idempotent retry after transient failure;
- metadata-only persistence attempt/result audit.

The report correctly states real DB transaction behavior remains unproven and must be validated in a future local test DB prototype.

## Migration order review

PASS. Migration order is conservative:

```text
schema design review
migration design QA
disabled repository skeleton
local test DB prototype behind explicit test flag
negative-path / rollback tests against local test DB
idempotency and concurrency tests against local test DB
metadata-only audit event design
production gate review docs-only
disabled production config skeleton
only then consider production hook
```

The report explicitly says not to create actual migration files in R7BS.

## Rollback and forward-fix review

PASS. The report favors:

- normal rollback only before persisted data exists;
- forward-fix migrations after data exists;
- soft retraction/quarantine over destructive deletion;
- manual recovery that preserves metadata, hash identities, and retraction reason;
- rollback paths that do not change readiness, clean_data, or delivery/export state.

## Retention and retraction review

PASS. Retention and retraction are conservative:

- records retained for audit reproducibility;
- retention windows deferred to separate policy review;
- raw source payload retention remains forbidden;
- retraction uses `retracted_at` and `retraction_reason`;
- retracted rows remain excluded from clean_data and delivery/export;
- destructive delete requires a separate data retention/privacy design and QA review.

## Feature gate and environment planning review

PASS. Feature gate planning requires:

- readiness gates CLOSED until separate production gate review;
- explicit test-only DB flag for local DB stages;
- separate production persistence flag only after production gate review;
- environment allowlist;
- no default production DB connection;
- no production writer config in test-only paths;
- no automatic activation from schema alignment preview;
- no activation from environment variables alone.

This avoids the classic “one env var accidentally made it production” trap. Good little guardrail goblin.

## Readiness gate review

PASS. The report preserves:

- `client_ready = false`;
- `production_ready = false`;
- `formal_client_export_allowed = false`;
- `demo_export_only = true`;
- `VERIFIED` does not imply `STRONG_EVIDENCE`;
- `VERIFIED` does not auto-write clean_data;
- non-VERIFIED rows remain review-bound;
- unresolved rows keep `blocked_delivery_reason`;
- corrected rows remain `re_audit_required`;
- persistence candidate does not trigger delivery;
- persistence candidate does not mutate clean_data;
- persistence candidate does not open readiness gates.

## Open questions review

PASS. Open questions are explicit and appropriately deferred:

- DB backend choice;
- `candidate_unit` first-class status;
- `source_trace` JSON/normalized storage;
- global versus active-row uniqueness under soft retraction;
- audit event table timing;
- retention period;
- reviewer UI pagination/sorting;
- concurrency requirements;
- manual retraction/repair workflow.

None of these are silently decided as production behavior.

## Non-goals review

PASS. R7BS explicitly does not:

- modify production code;
- modify tests;
- modify fixtures;
- add repository/model/service code;
- add DB schema;
- add migration;
- add DB connection;
- add storage implementation;
- write output files;
- run extraction;
- run MinerU/OCR/LLM/VLM;
- open readiness gates;
- claim production/client/formal export readiness.

## Remaining risks review

PASS. Remaining risks are clear:

- schema is conceptual only;
- migration is planned only;
- no real DB behavior is proven;
- no local test DB adapter exists;
- transaction/rollback behavior is not implemented;
- performance/concurrency not proven;
- real review UI integration not proven;
- production operational controls not proven;
- client/export readiness is not implied.

## Recommended next task review

PASS. The R7BS report recommended R7BS-QA, which is appropriate for its point in the sequence. For this QA task, the task document recommends:

```text
348N-R7BT schema/migration QA docs-only
```

That next task is safe only if it remains docs-only / QA-only and does not jump directly into DB implementation, migration creation, repository code, or production persistence.

## Boundary review

PASS. R7BS did not implement real persistence. This R7BS-QA task creates only:

```text
docs/agent/348N_R7BS_QA_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_REVIEW.md
```

No production code, tests, fixtures, outputs, dependencies, integrations, database models, migrations, schema files, writer implementations, handoff docs, planning docs, or readiness gates were modified.

## Validation outputs

```text
python -m py_compile tests/agent/review_queue_fake_repository_boundary_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_fake_repository_boundary_348n.py
PASS

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

python -m pytest tests/agent/test_review_queue_fake_repository_boundary_348n.py -q
PASS: 63 passed in 0.51s

python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
PASS: 76 passed in 0.39s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.19s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.15s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.12s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.23s

python -m pytest tests/agent -q
PASS: 543 passed in 2.27s

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

- R7BS remains docs-only; no real schema, migration, DB, repository, service, or production hook exists.
- R7BS-QA reviewed design completeness and boundary safety, not real DB behavior.
- Transaction, rollback, idempotency, uniqueness, concurrency, retention, and retraction are not proven against a real database.
- A future local test DB prototype and separate production gate review are still required before any production persistence path can be considered.

## Decision

PASS. R7BS is an accurate, conservative, docs-only schema and migration design. It does not implement or authorize real database persistence, and it preserves the current test-only/in-memory boundary, raw-payload exclusion, non-promotional VERIFIED policy, clean_data/delivery isolation, and CLOSED readiness gates.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BS-QA approved the docs-only schema and migration design.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; fake repository 63 passed; persistence contract 76 passed; schema alignment 29 passed; dry-run integration 36 passed; writer contract 24 passed; adapter skeleton 75 passed; full tests/agent 543 passed.
files_modified（修改文件数）= 1 allowed QA report file.
error_count（错误数）= 0.
schema_design_review_result（schema设计审查结果）= PASS; conceptual schema is complete enough for next docs-only review and does not implement DB persistence.
migration_design_review_result（migration设计审查结果）= PASS; migration sequence is conservative and requires QA, disabled skeleton, local test DB, rollback tests, and production gate review before production hook.
conceptual_table_review_result（概念表审查结果）= PASS; review_queue_items and optional audit/migration tables are clearly future-only concepts.
conceptual_column_review_result（概念字段审查结果）= PASS; identity, review, evidence, audit, idempotency, timestamps, and soft-retraction fields are covered.
identity_hash_design_review_result（身份/哈希设计审查结果）= PASS; required identity/hash fields and SHA-256 validation policy are covered.
status_action_design_review_result（状态/动作设计审查结果）= PASS; review-bound statuses/actions do not imply clean_data, delivery, export, readiness, or STRONG_EVIDENCE.
evidence_trace_design_review_result（证据/trace设计审查结果）= PASS; bounded evidence_preview/source_trace metadata allowed; full source_text and raw payloads forbidden.
audit_metadata_design_review_result（审计元数据设计审查结果）= PASS; run/input/version/hash metadata and metadata-only persistence attempt/result audit are planned.
idempotency_uniqueness_design_review_result（幂等唯一性设计审查结果）= PASS; uniqueness, no-op retry, changed-payload conflict, no silent duplicate insert, and batch duplicate rejection are covered.
index_query_design_review_result（索引查询设计审查结果）= PASS; review UI, audit/debug, run/source/status/re-audit/hash lookup patterns and candidate indexes are covered.
constraint_enum_design_review_result（约束枚举设计审查结果）= PASS; check/enum constraints are planned to block invalid statuses/actions/hash/preview/readiness/clean/delivery implications.
raw_payload_exclusion_design_review_result（原始payload排除设计审查结果）= PASS; full source_text, raw MinerU/Excel/parser/OCR/LLM/VLM, DB/path/config, readiness, clean_data, and delivery/export intent remain forbidden.
transaction_atomicity_design_review_result（事务原子性设计审查结果）= PASS; single-row atomicity, batch all-or-nothing, rollback on invalid row, and idempotent retry are designed but not implemented.
rollback_forward_fix_design_review_result（回滚/前向修复设计审查结果）= PASS; forward-fix after data exists and soft retraction over destructive delete are covered.
feature_gate_design_review_result（feature gate设计审查结果）= PASS; explicit test-only DB flag, environment allowlist, no default production DB, and separate production gate review are required.
readiness_gate_review_result（就绪门审查结果）= PASS; readiness gates remain CLOSED and no production/client/formal export readiness is claimed.
boundary_check（边界检查）= PASS; only docs/agent/348N_R7BS_QA_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_REVIEW.md is created in this task.
readiness_gates（就绪门）= CLOSED.
recommended_next_task（推荐下一任务）= 348N-R7BT schema/migration QA docs-only.
```
