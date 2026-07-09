# 348N-R7CA-QA local test DB prototype implementation planning review

## Task ID

```text
348N-R7CA-QA local test DB prototype implementation planning review
```

Task type: QA-review-only.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward 0769f8d..66631b9; R7CA-QA task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -120
PASS: latest history includes 66631b9 R7CA-QA task doc, 0769f8d R7CA planning report, f86c790 R7CA task doc, e9a3099 R7BZ-QA, dfdecee R7BZ checkpoint, c1b05dc R7BY-QA, and 06295b5 R7BY negative-path expansion.
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
- `docs/codex_tasks/348N_R7CA_QA_local_test_DB_prototype_implementation_planning_review.md`
- `docs/agent/348N_R7CA_LOCAL_TEST_DB_PROTOTYPE_IMPLEMENTATION_PLANNING_DOCS_ONLY.md`
- `docs/agent/348N_R7BZ_QA_LOCAL_TEST_DB_BOUNDARY_HANDOFF_CHECKPOINT_REVIEW.md`
- `docs/agent/348N_R7BZ_LOCAL_TEST_DB_BOUNDARY_HANDOFF_CHECKPOINT.md`
- `docs/agent/348N_R7BY_QA_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BX_QA_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_REVIEW.md`
- `docs/agent/348N_R7BX_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_TEST_ONLY_REPORT.md`

Read-only boundary files reviewed:

- `tests/agent/review_queue_local_test_db_adapter_boundary_348n.py`
- `tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py`
- `tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py`
- `datefac_agent/review/review_queue_repository.py`
- `tests/agent/test_review_queue_repository_skeleton_348n.py`
- `tests/agent/test_review_queue_repository_skeleton_qa_348n.py`
- `tests/agent/review_queue_fake_repository_boundary_348n.py`
- `tests/agent/test_review_queue_fake_repository_boundary_348n.py`
- `tests/agent/review_queue_persistence_contract_348n.py`
- `tests/agent/test_review_queue_persistence_contract_348n.py`

## R7CA recap

R7CA created a docs-only implementation plan for a future local test DB prototype. It did not implement an adapter, database connection, schema, migration, SQL execution, repository implementation, output writer, production integration, or readiness-gate behavior.

The plan correctly restates the current R7BZ-QA baseline:

- local test DB boundary remains test-only under `tests/agent`;
- production-adjacent repository skeleton remains disabled by default;
- no real local DB adapter, DB connection, SQL, schema, migration, production repository, `review_queue_builder` integration, clean_data integration, or delivery/export integration exists;
- latest known full `tests/agent` at R7CA was `735 passed`;
- readiness gates remain CLOSED.

## 大白话说明审查

PASS. R7CA 的“大白话说明”准确：这一轮只是施工图，不是数据库功能。它明确下一刀只能在测试区做最小 SQLite `:memory:` proof，不能接生产 repository、不能接 `review_queue_builder`、不能写 clean_data、不能导出、不能打开 readiness。

## Allowed file boundary review

PASS. R7CA changed exactly one allowed report file:

- `docs/agent/348N_R7CA_LOCAL_TEST_DB_PROTOTYPE_IMPLEMENTATION_PLANNING_DOCS_ONLY.md`

No code, tests, fixtures, outputs, dependencies, schema files, migrations, handoff docs, planning docs, or readiness gates were modified by R7CA.

## Docs-only planning review

PASS. The report is explicitly docs-only and avoids claiming implementation. It does not describe any already-working DB behavior, real transaction behavior, rollback behavior, schema/migration behavior, uniqueness constraints, concurrency guarantees, cleanup guarantees, production controls, client readiness, or formal export readiness as proven.

## Current baseline review

PASS. The current baseline is stated conservatively:

- no real local DB adapter exists;
- no real DB connection exists;
- no SQL execution exists;
- no schema or migration exists;
- no production repository exists;
- no `review_queue_builder`, clean_data, delivery, export, runner, or CLI integration exists;
- readiness gates remain CLOSED.

This matches the reviewed R7BZ-QA/R7BY/R7BX materials and read-only source inspection.

## Smallest safe future implementation slice review

PASS. The proposed first implementation slice is appropriately small and test-only:

- new prototype module under `tests/agent`;
- explicit local-test config gates;
- stdlib SQLite in-memory connection only;
- schema created only inside test-owned setup/object initialization;
- metadata-only row insertion after gates pass;
- transaction rollback and teardown tests;
- production skeleton remains disabled.

The plan also includes a smaller fallback split if insert/rollback is too much for one task.

## Candidate future files review

PASS. The candidate future files are limited to test-only prototype/test/report paths plus one optional curated fixture:

- `tests/agent/review_queue_local_test_db_adapter_prototype_348n.py`
- `tests/agent/test_review_queue_local_test_db_adapter_prototype_348n.py`
- `docs/agent/348N_R7CB_LOCAL_TEST_DB_ADAPTER_PROTOTYPE_TEST_ONLY_REPORT.md`
- optional `tests/agent/fixtures/review_queue_local_test_db/r7cb_metadata_only_candidates.json`

The plan explicitly forbids changing `datefac_agent/review/review_queue_repository.py`, `review_queue_builder`, clean candidate policy, delivery code, dependency/config files, output/input/temp/data/legacy directories, or migration/schema directories in the first slice.

## Candidate future tests review

PASS. The future test plan covers the right conservative dimensions:

- test-only import placement and no production importer;
- default-disabled and explicit-config-required behavior;
- environment-only activation rejection;
- production/staging/cloud/remote/file-path DB rejection;
- only `sqlite_memory` + `:memory:` acceptance;
- test-owned schema setup only;
- metadata-only insert;
- full `source_text` and raw payload rejection before insert;
- transaction rollback on invalid batch;
- idempotency/uniqueness conflicts;
- teardown/close behavior;
- readiness, clean_data, delivery, and export counters remain closed/zero;
- compatibility with existing R7BX/R7BY/R7BU/R7BV tests.

## Candidate local DB choice review

PASS. `sqlite3` in-memory is the safest first local DB choice because it is stdlib-only, requires no dependency addition, no Docker, no external service, no file path by default, and state disappears when the connection closes. The plan correctly rejects temp-file SQLite and PostgreSQL/container work for the first slice.

## Activation gate plan review

PASS. The plan requires all activation gates:

- explicit config object;
- `enabled = true`;
- `test_only = true`;
- `environment = local_test`;
- exact future test-only token;
- `db_selection = sqlite_memory`;
- `dsn = :memory:`;
- explicit activation source;
- explicit no production writer, clean_data, delivery/export, or readiness intent.

It rejects environment-only activation and keeps the adapter unavailable to production code even when valid test activation is provided.

## Config allowlist plan review

PASS. The allowlist is narrow and conservative:

- allowed keys: `enabled`, `test_only`, `environment`, `db_selection`, `dsn`, `activation_source`, `test_only_enable_token`, optional `schema_version`, optional `run_id`;
- forbidden keys include production/staging/dev-prod env values, production DSNs, remote endpoints, connection strings, secrets, caller table/schema/migration names, production writer config, readiness override, clean_data intent, and delivery/export intent.

Failure messages are required to stay generic and not echo sensitive values.

## Local-only schema setup plan review

PASS. Schema creation is permitted only inside the future test-owned in-memory SQLite connection. The plan forbids schema files, migration files, caller-supplied table names, raw/full source text columns, clean_data tables, delivery/export tables, production factories, and partial usable adapter state after setup failure.

## Transaction and rollback plan review

PASS. The future tests are required to prove atomic behavior, invalid-row rollback, injected mid-batch failure rollback, empty read-after-failed-write state, input mutation safety, and no clean_data/delivery/export/readiness side effects. The plan does not overclaim that this behavior already exists.

## Idempotency and uniqueness plan review

PASS. The future plan requires unique `idempotency_key`, unique `review_item_id`, deterministic `record_payload_hash`, deterministic same-key/same-hash retry/no-duplicate behavior, conflict fail-closed behavior for same-key/different-hash and same-review-item/conflicting identity, duplicate-in-batch rollback, and rejection of caller-supplied DB primary keys. It explicitly avoids claiming production-grade idempotency.

## Raw payload exclusion plan review

PASS. The plan rejects before storage:

- full `source_text`;
- `full_source_text`;
- raw MinerU/Excel/parser/OCR/LLM/VLM payloads;
- unbounded evidence text;
- clean_data payload;
- delivery/export payload;
- readiness override;
- caller-supplied DB row/receipt/internal adapter state.

Only bounded metadata may be stored.

## Cleanup and teardown plan review

PASS. The plan requires close-after-use, post-close operation rejection, no filesystem DB file, independent state across repeated test runs, no usable adapter after failed setup, no rows after failed insert, and loud/test-visible cleanup failure. It correctly keeps temp-file DB out of the first slice.

## No-production-connection guarantee review

PASS. The plan guarantees no production code integration, no env-var auto-activation, no production DSN, no remote host, no cloud endpoint, no file path DB by default, no migration files, no `review_queue_builder` integration, no production repository factory activation, no runner/CLI integration, no output writer, and no production persistence claim. It also requires that `datefac_agent/` must not import the test-only adapter.

## clean_data/delivery/export separation review

PASS. The plan preserves the current safety boundary:

- no clean_data mutation;
- no delivery/export trigger;
- no readiness gate mutation;
- no `VERIFIED -> STRONG_EVIDENCE` promotion;
- no `VERIFIED -> clean_data` automatic admission;
- non-VERIFIED rows remain review-bound;
- unresolved rows remain delivery-blocked;
- corrected rows remain re-audit-required.

## Future validation commands review

PASS. The future validation list includes py_compile for the existing boundary/repository files and new prototype files, targeted tests for the prototype and existing boundary/repository chains, full `tests/agent`, and git status/diff/diff-check. It also asks for source-inspection tests covering no production import, no file DB path, no network, no Docker, no dependency additions, and no output writes.

## Stop conditions review

PASS. Stop conditions are explicit and conservative. Future implementation must stop if it needs production code changes, dependency additions, file-path DB, PostgreSQL/Docker, schema/migration files, env-only activation, production DSN/host/path acceptance, raw payload/source_text storage, clean_data/delivery/export integration, readiness gate opening, output/input/temp/data/legacy writes, or cannot prove no partial writes after failed batch.

## Risks and open questions review

PASS. Risks are clearly stated:

- SQLite `:memory:` is not production PostgreSQL;
- test-only schema may diverge from future production schema;
- idempotency semantics may change for real persistence;
- in-memory cleanup is not representative of file/container DB cleanup;
- concurrency is not meaningfully proven by the first slice.

Open questions are appropriate for the future R7CB task and do not block this QA.

## Non-goals review

PASS. R7CA lists non-goals clearly: no production code, tests, fixtures, DB adapter, repository implementation, model, schema, migration, connection, SQL execution, file writes, output writer, extraction, MinerU/OCR/LLM/VLM, SQLite/PostgreSQL/Docker connection, readiness gate opening, production persistence, production readiness, client readiness, or formal export readiness.

## Decision

PASS. R7CA is a conservative docs-only implementation plan for a future test-only local DB prototype. It is specific enough to guide R7CB, remains narrow, and does not overclaim existing database, transaction, rollback, migration, production, clean_data, delivery/export, or readiness behavior.

## Validation outputs

```text
python -m py_compile tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py
PASS

python -m py_compile datefac_agent/review/review_queue_repository.py
PASS

python -m py_compile tests/agent/test_review_queue_repository_skeleton_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_repository_skeleton_qa_348n.py
PASS

python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py -q
PASS: 88 passed in 0.19s

python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py -q
PASS: 55 passed in 0.13s

python -m pytest tests/agent/test_review_queue_repository_skeleton_qa_348n.py -q
PASS: 32 passed in 0.13s

python -m pytest tests/agent/test_review_queue_repository_skeleton_348n.py -q
PASS: 17 passed in 0.09s

python -m pytest tests/agent -q
PASS: 735 passed in 2.67s

git status -sb
PASS before report creation: clean.

git diff --stat
PASS before report creation: no tracked diff.

git diff --name-only
PASS before report creation: no tracked diff.

git diff --check
PASS before report creation: no whitespace errors.
```

Post-report git diff checks were run after creating this report and confirmed only this allowed QA report changed and `git diff --check` passed.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7CA docs-only implementation planning is accurate, conservative, and no-overclaim.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; negative-path tests 88 passed; R7BX boundary tests 55 passed; repository QA 32 passed; repository skeleton 17 passed; full tests/agent 735 passed.
files_modified（修改文件数）= 1; only docs/agent/348N_R7CA_QA_LOCAL_TEST_DB_PROTOTYPE_IMPLEMENTATION_PLANNING_REVIEW.md was created.
error_count（错误数）= 0.
implementation_planning_review_result（实施计划审查结果）= PASS; plan is docs-only and does not implement or claim DB behavior.
smallest_safe_slice_review_result（最小安全切片审查结果）= PASS; future slice is explicit-gated, test-only, in-memory SQLite under tests/agent only.
candidate_file_plan_review_result（候选文件计划审查结果）= PASS; future file plan avoids production code and limits changes to test-only prototype/test/report plus optional curated fixture.
candidate_test_plan_review_result（候选测试计划审查结果）= PASS; future tests cover activation gates, allowlist rejection, local-only schema, rollback, idempotency, raw payload exclusion, teardown, and compatibility.
activation_gate_plan_review_result（激活门计划审查结果）= PASS; explicit local-test config/token/:memory: gates are required and env-only activation is rejected.
config_allowlist_plan_review_result（配置白名单计划审查结果）= PASS; narrow config allowlist and broad production/secret/readiness/clean/export rejection are specified.
local_schema_setup_plan_review_result（本地schema设置计划审查结果）= PASS; schema may exist only in test-owned in-memory connection with no schema/migration files.
transaction_rollback_plan_review_result（事务回滚计划审查结果）= PASS; future atomic/no-partial rollback tests are required and not claimed as already proven.
idempotency_uniqueness_plan_review_result（幂等唯一性计划审查结果）= PASS; uniqueness, deterministic retry/no-duplicate, and conflict fail-closed semantics are planned.
raw_payload_exclusion_plan_review_result（原始payload排除计划审查结果）= PASS; full source_text, raw artifacts, clean_data/export/readiness intent, and caller DB state are forbidden before storage.
cleanup_teardown_plan_review_result（清理teardown计划审查结果）= PASS; close/reject-after-close/no-file/no-residual-state requirements are explicit.
no_production_connection_plan_review_result（无生产连接计划审查结果）= PASS; no production DSN, remote host, env activation, runner/CLI, output writer, or production hook is allowed.
clean_data_delivery_boundary_review_result（clean_data/交付边界审查结果）= PASS; clean_data, delivery/export, evidence promotion, and readiness gates remain separated and closed.
boundary_check（边界检查）= PASS; QA creates only the allowed report and does not modify code/tests/fixtures/output/dependencies/schema/migration/readiness.
readiness_gates（就绪门）= CLOSED; client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true.
recommended_next_task（推荐下一任务）= 348N-R7CB local test DB prototype minimum implementation test-only.
```
