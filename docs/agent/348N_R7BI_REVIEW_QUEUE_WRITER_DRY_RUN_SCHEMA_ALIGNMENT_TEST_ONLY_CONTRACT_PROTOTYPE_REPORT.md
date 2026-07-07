# 348N-R7BI review-queue writer dry-run schema alignment test-only contract prototype

## Task ID

```text
348N-R7BI review-queue writer dry-run schema alignment test-only contract prototype
```

Task type: test-only-schema-alignment-contract-prototype.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward 5482b43..e055b0b; R7BI task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -25
PASS: latest commits include e055b0b task doc and 5482b43 R7BH-QA.
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
- `docs/codex_tasks/348N_R7BI_review_queue_writer_dry_run_schema_alignment_test_only_contract_prototype.md`
- `docs/agent/348N_R7BH_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE_REVIEW.md`
- `docs/agent/348N_R7BH_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE.md`
- `docs/agent/348N_R7BG_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_HANDOFF_CHECKPOINT_REVIEW.md`
- `docs/agent/348N_R7BF_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REVIEW.md`
- `docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7BC_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md`

Current test-only slices reviewed:

- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7be_dry_run_integration_boundary_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json`

## R7BH-QA recap

R7BH-QA confirmed the schema alignment plan is complete, conservative, docs-only, boundary-safe, metadata-first, fail-closed, source_text-safe, clean_data-safe, delivery-gate-safe, dry-run/test-only-aware, and readiness-closed.

R7BI implements the next safe test-only slice: a schema alignment contract prototype that validates already-built R7BE dry-run integration output and maps R7BC writer preview records into an in-memory future review_queue record preview.

## 大白话说明

这一轮只在 `tests/agent/` 做字段闸门。它检查“已经通过 dry-run integration boundary 的 writer preview”能不能安全映射成未来 `review_queue` 记录预览。它不写库、不建表、不导出、不接生产，也不把 `VERIFIED` 变成 `clean_data`。

## Test-only schema alignment scope

Implemented files:

- `tests/agent/review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bi_schema_alignment_contract_fixture.json`
- `docs/agent/348N_R7BI_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md`

The prototype validates only this chain:

```text
disabled adapter candidate output
-> dry-run integration boundary output
-> test-only writer dry-run preview
-> future review_queue record preview
```

## Contract design

The contract is disabled by default and requires explicit token:

```text
R7BI_TEST_ONLY_SCHEMA_ALIGNMENT_ENABLE
```

When enabled, it accepts only R7BE integration output with:

- `integration_status = ENABLED_TEST_ONLY_DRY_RUN`
- `dry_run_only = true`
- expected integration boundary version
- expected writer contract version
- closed readiness gates
- zero external-call counts
- zero write counts
- closed boundary flags
- deterministic `writer_preview_hash`

It rejects adapter-only payloads, direct writer-preview payloads, raw extraction payloads, full source text, clean_data intent, delivery/export intent, production config, opened readiness gates, malformed idempotency, timestamp-like fields, and test-only config leakage.

## Field classification

The prototype classifies required R7BH fields:

- `required_audit`: `run_id`, `adapter_version`, `writer_contract_version`, `input_file_hashes`, `audit_hash`, `source_trace`, `readiness_gates`
- `required_persistence_safe`: `source_file_hash`, `review_item_id`, `metric_name`, `period`, `candidate_value`, `agreement_status`, `review_status`, `review_reason`, `reviewer_action`, `schema_version`
- `required_idempotency`: `idempotency_key`
- `required_delivery_blocking`: `blocked_delivery_reason`
- `required_reaudit`: `re_audit_required`
- `optional_bounded_evidence`: `evidence_preview`
- `normalized_derived`: `normalized_candidate_value`
- `dry_run_only`: `integration_boundary_version`, `dry_run_only`, `validation_errors`
- `test_only_only`: generic `contract_version`

## Future persistence preview shape

Future review_queue record previews are metadata-first and include only safe fields:

- schema/version metadata
- row/source identity
- input/source hashes
- adapter/writer contract metadata
- metric/period/value/unit fields
- deterministic normalized candidate value
- agreement/review status and reason
- blocking/re-audit fields
- bounded evidence preview
- compact source trace
- audit/idempotency hashes
- explicit `clean_data_eligible = false`
- explicit `delivery_blocked = true`

The preview excludes `dry_run_only`, integration boundary version, validation errors, test-only tokens/config, raw payloads, full source text, and delivery/clean payloads from future record rows.

## Required fields

Required input validation covers:

- integration envelope fields;
- adapter audit contract fields;
- writer preview fields;
- writer summary fields;
- writer dry-run record fields;
- idempotency and record payload hashes;
- source trace fields.

Missing required fields fail closed.

## Forbidden fields

The contract recursively rejects forbidden fields, including:

- full `source_text` / `full_source_text` / raw source text;
- raw MinerU / raw Excel / raw parser / raw PDF / OCR / LLM / VLM payloads;
- `clean_data` payload or intent;
- formal delivery/export payloads;
- production writer config;
- direct/user-supplied writer preview;
- test-only tokens/config leaking into future preview;
- non-deterministic timestamp/execution/database ID fields.

## Pass-through and normalization rules

Pass-through fields include `run_id`, `adapter_version`, `input_file_hashes`, `review_item_id`, `audit_hash`, status fields, source trace, and bounded evidence preview.

Normalization is deterministic:

- `metric_name`, `period`, and `review_reason` are whitespace-normalized.
- `normalized_candidate_value` is derived by trimming/collapsing whitespace and removing comma separators.
- No wall-clock timestamp is required or accepted for idempotency.

## Idempotency and duplicate prevention

The contract validates writer-generated `idempotency_key` and `record_payload_hash` as deterministic 64-character SHA-256 hex digests. Tests confirm idempotency keys and schema alignment preview hashes are stable across retries.

Duplicate write behavior remains dry-run-only; no real persistence is added.

## Audit metadata retention

The contract preserves:

- `run_id`
- `adapter_version`
- adapter/writer/integration versions
- `input_file_hashes`
- `source_file_hash`
- `adapter_audit_hash`
- per-record `audit_hash`
- status counts
- re-audit count
- verified-without-clean-gate count
- closed readiness gates
- zero external-call counts

It does not recompute audit metadata from raw artifacts.

## Evidence preview and source_text boundary

Bounded `evidence_preview`, hashes, matched locator, matched text hash, and compact `source_trace` are allowed. Full source text and raw extraction content are rejected before preview generation.

## clean_data safety boundary

The prototype proves:

- `VERIFIED` does not imply `STRONG_EVIDENCE`;
- `VERIFIED` does not auto-write `clean_data`;
- `clean_data_eligible = true` is rejected;
- future preview rows explicitly keep `clean_data_eligible = false`;
- all write counts remain zero.

## Delivery gate and blocked_delivery_reason fields

Non-`VERIFIED` rows remain review-bound and carry `blocked_delivery_reason`. Future preview rows explicitly keep `delivery_blocked = true`.

## Corrected row and re-audit policy

Corrected/re-audit-only scenarios produce no clean delivery and preserve `re_audit_required_count = 1`. Corrected rows still require future explicit re-audit before any clean delivery path.

## Dry-run-only and test-only boundary

Dry-run and test-only fields stay in the deterministic envelope/summary. They do not become future persisted row authority. The module has no production hook and no production import.

## Failure and fail-closed behavior

Covered fail-closed cases:

- default disabled path;
- missing explicit R7BI token;
- adapter-only payload;
- direct writer-preview payload;
- missing audit field;
- missing/malformed idempotency key;
- timestamp-like field;
- full source text;
- raw extraction payload;
- clean_data intent;
- delivery/export intent;
- production config;
- readiness open;
- writer preview missing `dry_run_only`;
- test-only config leak.

## No-hook and no-IO boundary

The module performs no file, DB, network, export, parser, MinerU, OCR, LLM, VLM, subprocess, or production pipeline work. Static AST tests check for forbidden imports and calls.

## Validation outputs

```text
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

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
29 passed in 0.20s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
36 passed in 0.20s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
24 passed in 0.13s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
75 passed in 0.27s

python -m pytest tests/agent -q
404 passed in 1.68s

git status -sb
PASS：only the four allowed R7BI files are untracked before staging.

git diff --stat
PASS：no tracked diff before staging.

git diff --name-only
PASS：no tracked diff before staging.

git diff --check
PASS
```

## Limitations

- This is a test-only in-memory schema alignment preview, not persistence.
- It does not create database models, repositories, migrations, transactions, rollback, exports, or production hooks.
- Fixtures remain curated and synthetic.
- Future production persistence still requires separate design, implementation, QA, and rollback planning.

## Decision

```text
Decision = 348N_R7BI_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_ADDED
```

## Recommended next task

```text
348N-R7BI-QA review-queue writer dry-run schema alignment test-only contract prototype review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：test-only schema alignment contract prototype added
build_result（构建结果）= PASS：required py_compile commands passed
test_result（测试结果）= PASS：schema alignment contract tests 29 passed；dry-run integration tests 36 passed；writer contract tests 24 passed；adapter skeleton tests 75 passed；full tests/agent 404 passed
files_modified（修改文件数）= 4：tests/agent/review_queue_writer_schema_alignment_contract_348n.py；tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py；tests/agent/fixtures/discrepancy_review_queue/r7bi_schema_alignment_contract_fixture.json；docs/agent/348N_R7BI_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
error_count（错误数）= 0
schema_alignment_contract_result（schema对齐契约结果）= PASS：disabled-by-default explicit-token test-only contract validates R7BE dry-run integration output
field_classification_result（字段分类结果）= PASS：required R7BH fields classified into audit/persistence/idempotency/blocking/re-audit/evidence/dry-run/test-only categories
future_persistence_preview_result（未来持久化预览结果）= PASS：future review_queue record previews include safe metadata-first fields only
required_field_result（必需字段结果）= PASS：required envelope/audit/writer/record fields fail closed when missing
forbidden_field_result（禁止字段结果）= PASS：full source_text/raw extraction/clean intent/delivery export/production config/test-token leak rejected
normalization_result（标准化结果）= PASS：candidate field normalization is deterministic and timestamp-free
idempotency_result（幂等结果）= PASS：idempotency key and preview hash are deterministic across retries
audit_metadata_result（审计元数据结果）= PASS：run/version/input hash/audit hash/count/readiness/external-call metadata retained
evidence_boundary_result（证据边界结果）= PASS：bounded evidence_preview allowed; full source_text/raw payload forbidden
clean_data_boundary_result（clean_data边界结果）= PASS：VERIFIED does not promote to STRONG_EVIDENCE or clean_data; clean intent rejected
delivery_gate_boundary_result（交付闸门边界结果）= PASS：non-VERIFIED rows remain review-bound; blocked_delivery_reason retained; corrected rows re-audit-required
dry_run_test_only_boundary_result（dry-run/test-only边界结果）= PASS：dry-run/test-only fields stay in envelope and do not authorize persistence
no_hook_no_io_result（无hook无IO结果）= PASS：no IO/DB/export/production/parser/model hook in prototype module
boundary_check（边界检查）= PASS：only allowed test-only files and report changed; no production/output/dependency/readiness changes
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7BI-QA review-queue writer dry-run schema alignment test-only contract prototype review
```
