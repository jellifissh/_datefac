# 348N-R7BL review_queue persistence contract test-only prototype

## Task ID

```text
348N-R7BL review_queue persistence contract test-only prototype
```

Task type: test-only-persistence-contract-prototype.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: already up to date after prior fast-forward to edb0901.

git status -sb
PASS: clean after pull.

git log --oneline -35
PASS: latest commits include edb0901 R7BL task doc and 70daade R7BK-QA.
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
- `docs/codex_tasks/348N_R7BL_review_queue_persistence_contract_test_only_prototype.md`
- `docs/agent/348N_R7BK_QA_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE_REVIEW.md`
- `docs/agent/348N_R7BK_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE.md`
- `docs/agent/348N_R7BJ_QA_PROJECT_DOCUMENTATION_SYNC_REVIEW_AFTER_REVIEW_QUEUE_DRY_RUN_SCHEMA_ALIGNMENT_MILESTONE.md`
- `docs/agent/348N_R7BI_QA_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7BI_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md`

Current test-only slices reviewed:

- `tests/agent/review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`

## R7BK-QA recap

R7BK-QA confirmed the future persistence boundary design is conservative, metadata-first, source_text-safe, clean_data-safe, delivery-safe, readiness-closed, and still not a real persistence implementation.

R7BL implements the next bounded test-only slice: it validates an R7BI schema alignment preview and produces only an in-memory `review_queue_persistence_candidate_batch`.

## 大白话说明

这一轮只是在 `tests/agent/` 里模拟“落库前最后一道闸”。它检查已经通过 R7BI schema alignment 的 future review_queue preview 是否能安全变成“待落库候选批次”，但不写数据库、不建表、不写文件、不导出、不接生产，也不让 `VERIFIED` 自动进入 `clean_data`。

## Test-only persistence contract scope

Implemented files:

- `tests/agent/review_queue_persistence_contract_348n.py`
- `tests/agent/test_review_queue_persistence_contract_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json`
- `docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md`

The implemented chain is:

```text
test-only schema alignment preview
-> test-only persistence boundary
-> in-memory review_queue persistence candidate batch
```

## Contract design

The contract is disabled by default and requires explicit token:

```text
R7BL_TEST_ONLY_PERSISTENCE_ENABLE
```

When enabled, it accepts only R7BI schema alignment preview payloads with:

- `schema_alignment_status = ENABLED_TEST_ONLY_SCHEMA_ALIGNMENT`
- `dry_run_only = true`
- expected R7BI schema alignment contract version
- expected future review_queue schema version
- closed readiness gates
- zero external-call counts
- zero clean/delivery/filesystem/database/export write counts
- closed boundary flags
- metadata-first future record previews

## Accepted input shape

The only accepted input is the R7BI preview envelope:

- top-level schema alignment metadata;
- `run_id`, `adapter_version`, and `input_file_hashes`;
- `field_classification`;
- `future_review_queue_record_previews[]`;
- `schema_alignment_summary`.

Each record must carry identity, audit, status, blocking, idempotency, bounded evidence preview, and compact source trace fields.

## Rejected bypass shapes

The prototype rejects:

- schema-alignment bypass payloads;
- direct R7BE dry-run integration output;
- direct R7BC writer preview output;
- direct adapter candidate output;
- user-provided direct persistence candidate output;
- raw MinerU, Excel, parser, OCR, LLM, or VLM payloads;
- production writer config;
- clean_data write intent;
- delivery/export intent;
- readiness gates not CLOSED.

## Persistence candidate batch shape

Output is a pure data object:

```text
review_queue_persistence_candidate_batch[]
```

Each candidate row includes deterministic safe fields only:

- identity and audit fields;
- contract/schema versions;
- metric/period/value/normalized value;
- agreement and review status;
- blocked delivery and re-audit fields;
- bounded `evidence_preview`;
- compact `source_trace`;
- deterministic `idempotency_key`;
- deterministic `record_payload_hash`;
- `created_by_system = r7bl_test_only_persistence_contract`.

## Required fields

Required persistence candidate fields are enforced by `REQUIRED_PERSISTENCE_CANDIDATE_FIELDS`:

- `review_item_id`, `run_id`, `source_file_hash`, `input_file_hashes`;
- `adapter_version`, `contract_version`, `writer_contract_version`, `schema_version`;
- `audit_hash`, `idempotency_key`, `record_payload_hash`;
- `metric_name`, `period`, `candidate_value`, `normalized_candidate_value`;
- `agreement_status`, `review_status`, `review_reason`, `reviewer_action`;
- `blocked_delivery_reason`, `re_audit_required`;
- `evidence_preview`, `source_trace`, `created_by_system`.

Missing required fields fail closed before any candidate batch is returned.

## Forbidden fields

The contract recursively rejects or excludes:

- full `source_text` / `full_source_text` / raw source text;
- raw MinerU / Excel / parser / PDF / OCR / LLM / VLM payloads;
- clean_data payloads or write intent;
- delivery/export payloads;
- production writer config;
- direct writer preview, adapter candidate, or persistence candidate bypasses;
- test-only token/config leakage;
- database IDs, migration IDs, connection strings, table names, and repository hints;
- non-deterministic timestamp-like fields.

## Idempotency and duplicate prevention

The contract requires each input record to carry a 64-character SHA-256-style `idempotency_key`.

The output preserves stable idempotency keys and sorts candidates deterministically by:

```text
run_id, review_item_id, idempotency_key
```

Duplicate `idempotency_key` values fail closed for the whole batch.

## Record payload hash strategy

Each persistence candidate receives a deterministic `record_payload_hash` computed from the candidate row with `record_payload_hash` excluded from the hash input.

Tests prove:

- identical input produces identical output;
- retry output is stable;
- reversed input order produces the same sorted output and batch hash;
- each row hash recomputes to the expected SHA-256 digest.

## Batch fail-closed behavior

The prototype validates the entire batch before returning an output. If any record is invalid, the function raises `ReviewQueuePersistenceContractError` and returns no partial `review_queue_persistence_candidate_batch`.

Covered fail-closed cases include missing fields, malformed idempotency, missing hash identity, duplicate idempotency, full source text, unbounded evidence preview, opened readiness gates, production config, clean_data intent, delivery/export intent, and direct bypass payloads.

## Transaction and rollback simulation

No database transaction is implemented. The test-only simulation is pure data:

```text
all valid rows -> in-memory candidate batch returned
any invalid row -> entire batch fails closed
duplicate idempotency_key -> entire batch fails closed
```

This models rollback semantics without creating a repository, table, migration, or file output.

## Audit metadata retention

The candidate batch preserves:

- `run_id`;
- `adapter_version`;
- `writer_contract_version`;
- `input_file_hashes`;
- `source_file_hash`;
- per-record `audit_hash`;
- per-record `source_trace`;
- status counts;
- closed readiness gates;
- zero external-call counts;
- zero write counts.

The prototype does not recompute audit metadata from raw artifacts.

## Evidence preview and source_text boundary

Only bounded `evidence_preview` and compact source trace metadata are allowed. Full source text and raw extraction payloads fail closed.

The default preview limit is 160 characters, matching the existing test-only writer/schema alignment boundary.

## clean_data safety boundary

The prototype proves:

- `VERIFIED` does not imply `STRONG_EVIDENCE`;
- `VERIFIED` does not auto-write `clean_data`;
- `clean_data_eligible = true` is rejected;
- candidate rows exclude `clean_data_eligible`;
- clean_data write counts remain zero.

## Delivery/export boundary

Persistence candidates do not trigger delivery or export. Delivery/export payloads and intents are rejected, and summary counts stay zero:

```text
delivery_write_count = 0
export_write_count = 0
```

## Readiness gates boundary

Readiness gates remain closed:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

Opened readiness gates fail closed.

## No-hook and no-IO boundary

The module is under `tests/agent/`, imports no production package, and performs no file, DB, network, export, migration, or repository operation.

Static AST tests reject forbidden imports/calls such as database drivers, `datefac_agent`, filesystem write helpers, Excel/CSV writers, MinerU/PDF parsers, and HTTP clients.

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
PASS: 37 passed in 0.23s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.17s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.14s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.13s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.22s

python -m pytest tests/agent -q
PASS: 441 passed in 1.50s

git status -sb
PASS: only R7BL allowed files untracked before exact stage.

git diff --stat
PASS: no tracked unstaged diff before exact stage.

git diff --name-only
PASS: no tracked unstaged diff before exact stage.

git diff --check
PASS: no whitespace errors reported.
```

## Limitations

- This is not real persistence.
- No database model, repository, migration, table, connection, output writer, or production hook is added.
- Duplicate handling is fail-closed only; no duplicate-skip persistence policy is implemented.
- Candidate rows intentionally exclude clean_data eligibility and delivery/export fields.
- R7BL accepts only the current R7BI test-only preview shape; production enablement remains out of scope.

## Decision

PASS. R7BL adds a bounded test-only persistence contract prototype that converts validated schema alignment previews into in-memory review_queue persistence candidates while preserving fail-closed, metadata-first, no-IO, no-production, no-clean-data, no-delivery, and readiness-closed boundaries.

## Recommended next task

```text
348N-R7BL-QA review_queue persistence contract test-only prototype review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; test-only persistence contract prototype implemented.
build_result（构建结果）= PASS; required py_compile commands passed.
test_result（测试结果）= PASS; R7BL targeted tests 37 passed; tests/agent 441 passed.
files_modified（修改文件数）= 4 allowed files.
error_count（错误数）= 0.
persistence_contract_result（持久化契约结果）= PASS; disabled by default, explicit token required, accepts only R7BI schema alignment preview.
persistence_candidate_batch_result（持久化候选批次结果）= PASS; produces in-memory review_queue_persistence_candidate_batch only.
required_field_result（必需字段结果）= PASS; required persistence candidate fields enforced.
forbidden_field_result（禁止字段结果）= PASS; raw artifacts, source_text, clean_data, delivery/export, production config, and tokens rejected/excluded.
idempotency_result（幂等结果）= PASS; idempotency keys stable across retries.
duplicate_prevention_result（去重结果）= PASS; duplicate idempotency_key fails closed.
record_payload_hash_result（record_payload哈希结果）= PASS; deterministic SHA-256 payload hashes recompute in tests.
batch_fail_closed_result（批次fail-closed结果）= PASS; invalid row prevents any candidate batch return.
rollback_simulation_result（回滚模拟结果）= PASS; pure-data all-or-nothing simulation only.
audit_metadata_result（审计元数据结果）= PASS; run/input/source/audit/source_trace metadata retained.
evidence_boundary_result（证据边界结果）= PASS; bounded evidence_preview only, no full source_text.
clean_data_boundary_result（clean_data边界结果）= PASS; no VERIFIED promotion, no clean_data write/admission.
delivery_export_boundary_result（交付导出边界结果）= PASS; no delivery/export trigger.
readiness_gate_boundary_result（就绪门边界结果）= PASS; readiness gates remain CLOSED.
no_hook_no_io_result（无hook无IO结果）= PASS; no production import, DB, file output, network, migration, or export.
boundary_check（边界检查）= PASS; only allowed R7BL files created.
readiness_gates（就绪门）= CLOSED.
recommended_next_task（推荐下一任务）= 348N-R7BL-QA review_queue persistence contract test-only prototype review.
```
