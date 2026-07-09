# 348N-R7BY-QA local test DB boundary negative-path expansion review

## Task ID

```text
348N-R7BY-QA local test DB boundary negative-path expansion review
```

Task type: QA-review-only.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward 06295b5..ee9d4bb; R7BY-QA task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -100
PASS: latest history includes ee9d4bb R7BY-QA task doc, 06295b5 R7BY negative-path expansion, 727cec0 R7BY task doc, bd3fe1e R7BX-QA, and b6bf4b7 R7BX skeleton.
```

## Files reviewed

Required context reviewed:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/348N_R7BY_QA_local_test_DB_boundary_negative_path_expansion_review.md`
- `docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BX_QA_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_REVIEW.md`
- `docs/agent/348N_R7BX_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BW_QA_LOCAL_TEST_DB_PROTOTYPE_DESIGN_REVIEW.md`
- `docs/agent/348N_R7BV_QA_REPOSITORY_SKELETON_QA_REVIEW.md`

R7BY files reviewed:

- `tests/agent/review_queue_local_test_db_adapter_boundary_348n.py`
- `tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py`
- `docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md`

Related baseline files reviewed read-only:

- `tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py`
- `datefac_agent/review/review_queue_repository.py`
- `tests/agent/test_review_queue_repository_skeleton_348n.py`
- `tests/agent/test_review_queue_repository_skeleton_qa_348n.py`
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

## R7BY recap

R7BY expanded the test-only local test DB boundary negative-path coverage and created:

- `tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py`
- `docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md`

R7BY also made a minimal allowed test-only hardening change to:

- `tests/agent/review_queue_local_test_db_adapter_boundary_348n.py`

The helper change added explicit rejection for dangerous config/candidate keys and validated `idempotency_key` shape. It did not add DB connection, SQL, schema, migration, IO, network, production hook, clean_data mutation, delivery/export path, or readiness changes.

R7BY commit file check:

```text
git diff --name-only 06295b5^ 06295b5
PASS:
docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md
tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py
```

## 大白话说明审查

PASS. R7BY 的核心是拿各种“坏输入”撞门：生产 DSN、远程 host、环境变量偷激活、schema preview 自动激活、repository factory 自动激活、raw payload、clean_data/delivery/export 意图、伪造 DB row/receipt/internal state、坏幂等键和冲突批次。QA 结论是门仍然锁着：它只在 `tests/agent` 里增强防线，不连库、不写 SQL、不建表、不 migration、不写文件、不接生产，也不打开 readiness。

## Allowed file boundary review

PASS. R7BY changed only the allowed files:

- existing test-only helper under `tests/agent/`;
- new negative-path test suite under `tests/agent/`;
- R7BY report under `docs/agent/`.

This QA task creates only:

- `docs/agent/348N_R7BY_QA_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_REVIEW.md`

No `datefac_agent/` production code, outputs, dependencies, configs, fixtures, schema/migration files, integrations, handoff docs, existing reports, or readiness gates were changed.

## Test-only boundary/helper review

PASS. The modified helper remains under `tests/agent/`, remains clearly test-only by module docstring, constants, metadata, and tests, and remains planned-disabled.

The helper still imports only:

```text
__future__
collections.abc
copy
dataclasses
typing
```

The helper still reports no DB connection, no schema/migration/table creation, no storage/database/filesystem/network writes, no clean_data/delivery/export writes, and closed readiness gates.

## Negative-path expansion scope review

PASS. The new suite adds 88 focused tests covering:

- activation gate negative paths;
- production-looking config negative paths;
- environment-variable activation negative paths;
- schema preview / repository factory auto-activation negative paths;
- candidate raw payload negative paths;
- clean_data/delivery/export/readiness negative paths;
- caller-supplied DB row / receipt / internal state negative paths;
- transaction/idempotency conflict negative paths;
- input mutation safety;
- error leakage safety;
- source inspection;
- compatibility with existing R7BX tests.

## Activation gate negative-path review

PASS. The tests cover missing or invalid explicit flags and activation sources:

- missing `test_only`;
- false `test_only`;
- missing environment;
- empty environment;
- production/staging environment;
- mixed local/prod environment;
- missing DB selection;
- unsupported DB selection;
- schema preview auto-activation;
- repository skeleton factory auto-activation.

The explicit valid activation shape still returns planned-disabled metadata only; it does not open a database connection or enable persistence.

## Production-looking config negative-path review

PASS. Production-looking config rejection coverage includes:

- `postgres://`, `postgresql://`, `mysql://`, and `sqlite:///` URLs;
- file path DB URLs;
- remote/non-local/cloud hosts;
- port endpoints;
- HTTP/HTTPS endpoints;
- connection strings;
- DB passwords/secrets/API keys/tokens;
- schema/table/migration names;
- output/file paths;
- production writer config;
- readiness override.

Failure messages remain generic and do not echo sensitive values.

## Environment activation negative-path review

PASS. The tests set local-test-looking environment variables and production-looking DSN environment variables. The boundary rejects empty config and `activation_source = environment` / `activation_source = env`.

No environment-only activation path exists.

## Candidate raw payload negative-path review

PASS. Candidate negative paths reject:

- `source_text`;
- `full_source_text`;
- `raw_mineru_payload`;
- `raw_excel_payload`;
- `raw_parser_payload`;
- `raw_ocr_payload`;
- `raw_llm_payload`;
- `raw_vlm_payload`;
- unbounded evidence text;
- oversized `evidence_preview`.

Only bounded preview/trace-style metadata can be validated for future design, and it is still not persisted.

## clean_data/delivery/export/readiness negative-path review

PASS. Tests reject:

- `clean_data_payload`;
- `normalized_clean_data`;
- `approved_export_payload`;
- `delivery_payload`;
- `export_payload`;
- `delivery_export_intent`;
- `readiness_override`;
- `readiness_gates`;
- `production_timestamp_override`.

There is no clean_data admission path, delivery/export path, evidence promotion path, or readiness-gate mutation path.

## Caller-supplied DB row / receipt / internal state negative-path review

PASS. Tests reject caller-supplied persistence-looking fields:

- DB primary-key aliases;
- caller-supplied DB rows;
- database rows / DB rows;
- committed DB receipts / committed receipts / DB receipts;
- adapter internal state aliases.

These inputs fail closed without being retained or echoed.

## Transaction/idempotency negative-path review

PASS. Tests cover:

- missing `review_item_id`;
- missing/malformed `idempotency_key`;
- missing/malformed `record_payload_hash`;
- same `idempotency_key` with different `record_payload_hash`;
- same `review_item_id` with conflicting identity;
- invalid first row;
- invalid later row;
- duplicate conflicting entries;
- no partial success result;
- no silent duplicate insert.

The boundary models future transaction/idempotency policy as metadata only and still does not implement persistence state.

## Input mutation safety review

PASS. Tests deep-copy activation payloads and candidate batches before fail-closed validation and assert inputs remain unchanged. Nested forbidden fields also fail closed without mutation.

## Error leakage safety review

PASS. Errors remain generic and do not echo:

- raw payload values;
- full source text;
- DSNs;
- passwords;
- secrets;
- endpoints;
- table names;
- paths;
- readiness override values;
- DB receipt/internal-state values.

## Source inspection review

PASS. AST/source inspection confirmed the boundary helper has:

- no forbidden DB/storage/network/Docker imports;
- no SQL execution calls;
- no file-write calls;
- no SQL statement markers;
- no `datefac_agent` production import;
- no test fake-repository import.

Static inspection output:

```text
imports = ['__future__', 'collections.abc', 'copy', 'dataclasses', 'typing']
forbidden_import_hits = []
forbidden_call_hits = []
sql_or_docker_marker_hits = []
```

## Compatibility with R7BX boundary tests

PASS. Existing R7BX target tests still pass:

```text
python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py -q
PASS: 55 passed in 0.16s
```

The new negative-path suite passes:

```text
python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py -q
PASS: 88 passed in 0.19s
```

## No-DB / no-IO / no-network review

PASS. R7BY added no real DB adapter, database model, schema, migration, DB connection, SQL execution, file write, storage implementation, output writer, export/delivery path, production hook, extraction runner, dependency, or readiness change.

Repository skeleton and fake repository compatibility suites still pass, so R7BY did not weaken adjacent review_queue boundaries.

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

python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py -q
PASS: 88 passed in 0.19s

python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py -q
PASS: 55 passed in 0.16s

python -m pytest tests/agent/test_review_queue_repository_skeleton_qa_348n.py -q
PASS: 32 passed in 0.12s

python -m pytest tests/agent/test_review_queue_repository_skeleton_348n.py -q
PASS: 17 passed in 0.09s

python -m pytest tests/agent/test_review_queue_fake_repository_boundary_348n.py -q
PASS: 63 passed in 0.54s

python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
PASS: 76 passed in 0.45s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.26s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.16s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.13s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.26s

python -m pytest tests/agent -q
PASS: 735 passed in 2.63s

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

- R7BY-QA is review-only.
- R7BY remains test-only.
- No local test DB adapter implementation exists.
- No real DB connection, schema, model, migration, table, SQL execution, transaction, rollback, cleanup, concurrency, or retention behavior is implemented or proven.
- No production persistence, production hook, client readiness, production readiness, or formal export readiness is implied.

## Decision

PASS. R7BY safely expands negative-path coverage for the local test DB boundary and applies only minimal allowed test-only fail-closed hardening. It stays test-only, planned-disabled, no-DB/no-IO/no-network, metadata-first, raw-payload-safe, mutation-safe, non-leaking, clean_data/delivery/export-safe, compatible with R7BX and adjacent repository chains, and readiness-closed.

## Recommended next task review

Recommended next task:

```text
348N-R7BZ local test DB boundary handoff checkpoint
```

The next task should remain docs/checkpoint focused and must not jump to a real DB adapter, DB model, schema, migration, SQL execution, production hook, output writer, clean_data admission, delivery/export path, dependency addition, or readiness-gate opening.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BY-QA approves the local test DB boundary negative-path expansion.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; negative-path tests 88 passed; R7BX boundary tests 55 passed; repository QA 32 passed; repository skeleton 17 passed; fake repository 63 passed; persistence contract 76 passed; schema alignment 29 passed; dry-run integration 36 passed; writer contract 24 passed; production boundary adapter skeleton 75 passed; full tests/agent 735 passed.
files_modified（修改文件数）= 1; QA report only.
error_count（错误数）= 0.
negative_path_expansion_review_result（负路径扩展审查结果）= PASS; R7BY covers malicious, production-looking, malformed, conflicting, leakage-prone, and boundary-bypass inputs.
activation_gate_negative_path_review_result（激活门负路径审查结果）= PASS; missing/invalid flags, production/staging-like environments, missing/unsupported DB selection, and auto-activation paths fail closed.
production_config_negative_path_review_result（生产配置负路径审查结果）= PASS; DB URLs, remote/cloud hosts, endpoints, connection strings, secrets, schema/table/migration names, paths, writer config, and readiness override fail closed without echo.
environment_activation_negative_path_review_result（环境激活负路径审查结果）= PASS; environment variables and env activation sources cannot activate the boundary.
candidate_payload_negative_path_review_result（候选payload负路径审查结果）= PASS; source_text, full_source_text, raw MinerU/Excel/parser/OCR/LLM/VLM payloads, and unbounded evidence fail closed.
clean_data_delivery_negative_path_review_result（clean_data/交付负路径审查结果）= PASS; clean_data, normalized clean data, approved export, delivery/export, readiness, and production timestamp intents fail closed.
caller_supplied_db_state_negative_path_review_result（调用方伪造DB状态负路径审查结果）= PASS; DB identifiers/rows/receipts/internal state aliases fail closed.
transaction_idempotency_negative_path_review_result（事务/幂等负路径审查结果）= PASS; missing/malformed keys/hashes, conflicting keys, conflicting review IDs, invalid rows, duplicate conflicts, no partial success, and no silent duplicate insert are covered.
input_mutation_safety_review_result（输入变更安全审查结果）= PASS; activation payloads and candidate batches are not mutated.
error_leakage_safety_review_result（错误泄漏安全审查结果）= PASS; errors do not echo raw payloads, source text, secrets, DSNs, endpoints, paths, table names, or internal state.
source_inspection_review_result（源码检查审查结果）= PASS; static inspection found no forbidden imports/calls/SQL markers/file-write/network/Docker behavior.
no_db_no_io_no_network_review_result（无DB/IO/网络审查结果）= PASS; no DB adapter/model/schema/migration/connection/SQL/file/network/output/export/production hook exists.
compatibility_with_r7bx_review_result（与R7BX兼容审查结果）= PASS; existing R7BX boundary tests still pass at 55 passed.
boundary_check（边界检查）= PASS; QA creates only docs/agent/348N_R7BY_QA_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_REVIEW.md.
readiness_gates（就绪门）= CLOSED; client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true.
recommended_next_task（推荐下一任务）= 348N-R7BZ local test DB boundary handoff checkpoint.
```
