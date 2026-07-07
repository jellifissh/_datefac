# 348N-R7BE review-queue writer dry-run integration boundary test-only prototype

## Task ID

```text
348N-R7BE review-queue writer dry-run integration boundary test-only prototype
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 9da4c5a..08bc0ea
  Fast-forward
  docs/codex_tasks/348N_R7BE_review_queue_writer_dry_run_integration_boundary_test_only_prototype.md created

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -15:
  08bc0ea docs: add R7BE dry-run integration prototype task
  9da4c5a docs: add R7BD QA review
  8ed172d docs: add R7BD QA review task
  5cf401b docs: add R7BD dry-run integration design
  d05a3ab docs: add R7BD dry-run integration design task
  d9aa2f4 docs: add R7BC QA review
  3d0058b docs: add R7BC QA review task
  fbae83f test: add review queue writer contract prototype
  2da5521 docs: add R7BC writer prototype task
  879c471 docs: add R7BB QA review
  57296c2 docs: add R7BB QA review task
  553e0ee docs: add R7BB review queue persistence plan
  d3ef02a docs: add R7BB persistence planning task
  e55b1d6 docs: add R7BA QA review
  983125f docs: add R7BA QA review task
```

Worktree was clean after pull.

## Files reviewed

Required context:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R7BE_review_queue_writer_dry_run_integration_boundary_test_only_prototype.md`

Directly related reports:

- `docs/agent/348N_R7BD_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN_REVIEW.md`
- `docs/agent/348N_R7BD_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN.md`
- `docs/agent/348N_R7BC_QA_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7BC_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7BB_QA_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE_REVIEW.md`

Current slices reviewed:

- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json`

Related modules reviewed read-only:

- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`

## R7BD-QA recap

R7BD-QA confirmed that the future adapter-to-writer dry-run integration boundary design was safe:

```text
disabled adapter candidate output
  -> dry-run integration boundary
  -> R7BC test-only in-memory writer preview
```

The approved boundary is disabled-by-default, explicit-test-only, adapter-output-only, dry-run-only, metadata-first, idempotency-preserving, fail-closed, no-hook, no-IO, no-clean-data, no-delivery, and readiness-closed.

## 大白话说明

这一轮只在 `tests/agent/` 里搭了一条“安全传送带”：把已经通过 adapter 形状校验的候选输出，送进 R7BC 的 test-only writer，看看未来如果写 review_queue 会长成什么 dry-run preview。

它仍然不是生产集成：不写数据库、不写文件、不导出、不接 runner/CLI、不改 `datefac_agent/`、不打开 readiness。简单说，这只是沙盘里的一段传送带，不是上线的流水线。

## Test-only integration boundary scope

Created test-only helper:

```text
tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
```

Scope:

- lives only under `tests/agent/`;
- disabled by default;
- requires explicit `R7BE_TEST_ONLY_INTEGRATION_ENABLE` token;
- accepts only R7BC-compatible adapter candidate output;
- validates adapter candidate output before writer call;
- calls only the R7BC test-only in-memory writer contract;
- returns deterministic in-memory dry-run envelope plus unchanged writer preview;
- performs no database, filesystem, export, parser, model, MinerU, OCR, VLM, runner, CLI, or production pipeline action.

## Integration flow

Implemented flow:

```text
1. Receive already-built adapter candidate output.
2. If integration config is disabled, return DISABLED dry-run-only result without calling writer.
3. If enabled without exact test-only token, fail closed.
4. Validate candidate output with the R7BC writer contract validator before writer call.
5. Deep-copy the adapter payload.
6. Call R7BC build_review_queue_writer_dry_run_preview(...) with explicit writer test-only config.
7. Wrap the writer preview in deterministic integration metadata.
8. Validate the integration output remains dry-run-only, closed-readiness, no-write, no-full-source.
9. Return a deep copy.
```

## Input validation

Accepted:

- exact adapter candidate output shape expected by R7BC writer;
- closed readiness gates;
- zero external call counts;
- non-`VERIFIED` review_queue candidate rows;
- bounded `evidence_preview`;
- adapter audit metadata including `run_id`, `adapter_version`, `input_file_hashes`, and `adapter_audit_hash`.

Rejected before writer call:

- raw MinerU-like payload;
- raw Excel-like payload;
- raw parser-like payload;
- direct user payload;
- full `source_text`;
- opened readiness gates;
- schema mismatch;
- clean_data write intent.

## Writer call boundary

The integration helper imports and calls only `tests.agent.review_queue_writer_contract_348n`. It does not call the disabled adapter builder, production pipeline, repository, database writer, filesystem writer, runner, CLI, parser, or extraction system.

Tests monkeypatch the writer call for invalid inputs and confirm those payloads are rejected before the writer function is invoked.

## Dry-run output envelope

The enabled output contains:

```text
integration_status = ENABLED_TEST_ONLY_DRY_RUN
dry_run_only = true
integration_contract_version
adapter_audit_contract
writer_dry_run_preview
integration_summary
```

The `writer_dry_run_preview` is preserved exactly as returned by R7BC writer. The integration summary adds deterministic envelope metadata only:

- integration contract version;
- writer contract version;
- source adapter contract version;
- run id;
- adapter version;
- input file hashes;
- adapter audit hash;
- writer preview hash;
- integration envelope hash;
- dry-run counts and closed boundary flags.

All write counts remain zero.

## Idempotency and duplicate prevention

PASS. The integration boundary does not recompute writer idempotency keys. It preserves writer records unchanged, including `idempotency_key` and `record_payload_hash`.

Tests cover:

- same input produces identical integration output;
- same input preserves stable writer idempotency keys;
- retry with existing hashes produces writer `WOULD_SKIP_DUPLICATE` plan;
- duplicate plan remains dry-run-only with zero database writes.

## Audit metadata pass-through

PASS. The integration output includes `adapter_audit_contract` as a deep-copied pass-through from the input, and the summary preserves:

- `run_id`;
- `adapter_version`;
- source adapter contract version;
- writer contract version;
- input file hashes;
- `adapter_audit_hash`;
- review record `review_item_id` and `audit_hash` through the writer preview.

Input mutation after call cannot mutate output.

## Evidence preview and source_text boundary

PASS. The integration boundary accepts only bounded `evidence_preview` already validated by the writer contract. It rejects `source_text`, `full_source_text`, `raw_source_text`, raw MinerU, raw Excel, and raw parser payloads before the writer call.

Tests walk the serialized integration output and confirm forbidden full-source keys are absent.

## clean_data safety boundary

PASS. The integration helper never writes or admits clean_data:

- `clean_data_write_count = 0`;
- `delivery_write_count = 0`;
- `clean_data_eligible=true` fails closed;
- `delivery_clean_admitted=true` remains rejected by writer validation;
- `VERIFIED` rows do not enter review_queue dry-run records;
- `VERIFIED` is not promoted to `STRONG_EVIDENCE`;
- boundary flags keep `verified_auto_clean=false` and `verified_promotes_to_strong_evidence=false`.

## Delivery gate boundary

PASS. Non-`VERIFIED` rows remain review-bound and carry blocked delivery reasons through writer preview records. The integration preview is not a delivery artifact and does not export files.

## Corrected row and re-audit policy

PASS. The corrected re-audit fixture case produces no review_queue dry-run records, keeps `reaudit_required_count = 1`, and keeps clean/delivery writes at zero. Corrected rows therefore remain re-audit-required and cannot bypass clean delivery through this boundary.

## Failure and fail-closed behavior

Covered fail-closed cases:

- disabled default returns no writer preview;
- enabled config without exact test-only token raises;
- raw MinerU-like payload rejected;
- raw Excel-like payload rejected;
- raw parser-like payload rejected;
- direct user payload rejected;
- full `source_text` rejected;
- opened readiness gate rejected;
- schema mismatch rejected;
- clean_data intent rejected.

## No-hook and no-IO boundary

PASS. Static AST tests verify the integration helper does not import:

```text
datefac_agent, pathlib, os, sqlite3, sqlalchemy, requests, socket, subprocess,
fitz, pdfplumber, pypdf, openai
```

Static tests also reject filesystem/database/export-style calls such as `open`, `write`, `write_text`, `mkdir`, `unlink`, `remove`, `rename`, `replace`, and `connect`.

## Validation outputs

```text
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

pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
  22 passed in 0.16s

pytest tests/agent/test_review_queue_writer_contract_348n.py -q
  24 passed in 0.18s

pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
  75 passed in 0.26s

pytest tests/agent -q
  361 passed in 1.49s

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  ?? docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md
  ?? tests/agent/fixtures/discrepancy_review_queue/r7be_dry_run_integration_boundary_fixture.json
  ?? tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
  ?? tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py

git diff --stat
  no tracked diff before staging because all R7BE files are new and untracked

git diff --name-only
  no tracked diff before staging because all R7BE files are new and untracked

git diff --check
  PASS
```

## Limitations

- This is a test-only prototype under `tests/agent/`, not production integration.
- No database model, repository, migration, transaction, persistence writer, filesystem export, delivery artifact, runner, CLI hook, or production pipeline hook exists.
- Fixture data is curated and synthetic.
- This prototype proves boundary shape only; production enablement remains forbidden until future explicit design, implementation, and QA tasks.

## Decision

```text
Decision = 348N_R7BE_TEST_ONLY_DRY_RUN_INTEGRATION_BOUNDARY_PROTOTYPE_ADDED
```

R7BE adds a test-only dry-run integration boundary prototype. It validates adapter candidate output before writer call, invokes only the R7BC test-only writer under explicit test enablement, preserves writer preview and metadata, proves idempotency and fail-closed behavior, and keeps clean_data, delivery, filesystem, database, export, production hook, and readiness gates closed.

## Recommended next task

```text
348N-R7BE-QA review-queue writer dry-run integration boundary test-only prototype review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：test-only dry-run writer integration boundary prototype added
build_result（构建结果）= PASS：required py_compile commands passed
test_result（测试结果）= PASS：integration boundary tests 22 passed；writer tests 24 passed；adapter skeleton tests 75 passed；full tests/agent 361 passed
files_modified（修改文件数）= 4
error_count（错误数）= 0
integration_boundary_result（集成边界结果）= PASS：disabled-by-default, explicit-test-token gated, adapter-output-only, test-only helper
dry_run_preview_result（dry-run预览结果）= PASS：writer preview preserved unchanged inside deterministic dry-run envelope
fixture_result（fixture结果）= PASS：small curated R7BE fixture covers valid, mixed, unresolved, corrected, and invalid cases
input_rejection_result（输入拒绝结果）= PASS：raw MinerU/Excel/parser/direct/full source_text/readiness/schema/clean cases fail closed
writer_call_boundary_result（writer调用边界结果）= PASS：invalid inputs rejected before writer call; valid path calls only R7BC test-only writer
idempotency_result（幂等结果）= PASS：writer idempotency keys preserved; same input stable; duplicate skip plan passes through
audit_metadata_result（审计元数据结果）= PASS：adapter audit contract and writer record metadata pass through by deep copy
evidence_boundary_result（证据边界结果）= PASS：bounded evidence_preview only; full source_text/raw artifacts rejected and absent
clean_data_boundary_result（clean_data边界结果）= PASS：no clean_data writes/admission, no VERIFIED auto-clean, no STRONG_EVIDENCE promotion
delivery_gate_boundary_result（交付闸门边界结果）= PASS：non-VERIFIED rows remain review-bound; unresolved rows blocked; corrected rows re-audit-required
no_hook_no_io_result（无hook无IO结果）= PASS：no production import, DB, filesystem, export, parser, model, MinerU/OCR/VLM hook in integration helper
boundary_check（边界检查）= PASS：only allowed R7BE test/report/fixture files changed; no production code/output/dependency/readiness changes
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7BE-QA review-queue writer dry-run integration boundary test-only prototype review
```
