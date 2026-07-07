# 348N-R7BF-QA review-queue writer dry-run integration negative-path test-only coverage review

## Task ID

```text
348N-R7BF-QA review-queue writer dry-run integration negative-path test-only coverage review
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating ced68ca..8a7b4d3
  Fast-forward
  docs/codex_tasks/348N_R7BF_QA_review_queue_writer_dry_run_integration_negative_path_test_only_coverage_review.md created

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -20:
  8a7b4d3 docs: add R7BF QA review task
  ced68ca test: harden dry-run writer integration negative paths
  1585e16 test: add dry-run writer integration boundary prototype
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
  f4c507f docs: add R7BA adapter handoff checkpoint
  6ac9910 docs: add R7BA handoff checkpoint task
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
- `docs/codex_tasks/348N_R7BF_QA_review_queue_writer_dry_run_integration_negative_path_test_only_coverage_review.md`

Direct reports:

- `docs/agent/348N_R7BF_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REPORT.md`
- `docs/agent/348N_R7BD_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN_REVIEW.md`
- `docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7BC_QA_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md`

R7BF files:

- `tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7be_dry_run_integration_boundary_fixture.json`
- `docs/agent/348N_R7BF_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REPORT.md`

Related slices reviewed read-only:

- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json`

## R7BF recap

R7BF hardened the R7BE test-only integration boundary by adding negative-path coverage around misuse cases:

- missing explicit integration token;
- invalid integration token;
- default disabled path with malformed payload;
- exact test-only writer config construction;
- unsafe or production-like writer preview blocking;
- malformed/minimal/direct-writer-preview-shaped input rejection.

R7BF changed exactly the intended files:

```text
docs/agent/348N_R7BF_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REPORT.md
tests/agent/fixtures/discrepancy_review_queue/r7be_dry_run_integration_boundary_fixture.json
tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
```

No production code was changed.

## 大白话说明审查

PASS. R7BF is a “bad-input guardrail” slice. It does not make the dry-run bridge more powerful; it makes it harder to misuse. The tests now prove that wrong tokens, missing tokens, fake writer previews, and malformed payloads do not escape the test-only dry-run boundary.

## Negative-path coverage review

PASS. The test suite now covers:

- missing explicit token rejected before writer call;
- invalid explicit token rejected before writer call;
- disabled path remains inert with malformed payload;
- raw MinerU-like input rejected;
- raw Excel-like input rejected;
- raw parser-like input rejected;
- direct user payload rejected;
- full `source_text` rejected;
- readiness-open payload rejected;
- clean_data intent rejected;
- schema mismatch rejected;
- empty payload rejected;
- minimal adapter-like payload rejected;
- direct writer-preview-shaped payload rejected.

These cases are conservative and focused on misuse prevention.

## Writer-preview hardening review

PASS. R7BF added `_validate_writer_preview_boundary(...)` inside the test-only integration helper. It blocks writer previews that are not:

- `writer_status = ENABLED_TEST_ONLY_DRY_RUN`;
- `dry_run_only = true`;
- closed readiness gates;
- zero external call counts;
- zero clean/delivery/filesystem/database writes;
- closed boundary flags;
- review-bound records only.

The guard also wraps forbidden-field failures as `ReviewQueueWriterDryRunIntegrationBoundaryError`, keeping the failure at the integration boundary surface.

## Test-only token and config review

PASS. Tests verify:

- enabled config without the exact R7BE token fails before writer call;
- invalid token fails before writer call;
- default disabled path never calls the writer;
- valid path constructs a `ReviewQueueWriterContractConfig` with `enabled=True`, exact R7BC writer contract version, and exact R7BC test-only writer token.

This prevents accidental production writer invocation from being reachable through the R7BE helper.

## Malformed payload review

PASS. The fixture now contains small curated malformed/minimal cases:

```text
invalid_empty_payload
invalid_minimal_adapter_like_payload
invalid_direct_writer_preview_payload
```

Tests prove these fail closed before writer call. The existing malformed raw-artifact cases remain covered.

## Fixture review

PASS. The R7BE fixture remains compact and curated:

```text
fixture_scope = test_only_r7be
fixture size = 6555 bytes
no real PDF
no complete MinerU output
no DateFac Excel
no full source_text fixture
no output artifact
no production payload
```

The fixture adds only metadata-shaped negative cases needed for R7BF coverage.

## Positive path regression review

PASS. R7BF hardening does not break the positive path. The valid adapter candidate still reaches the test-only writer preview, writer preview records are preserved unchanged, adapter metadata passes through by deep copy, idempotency remains stable, and same-input retry can still produce `WOULD_SKIP_DUPLICATE` without writes.

## Dry-run output boundary review

PASS. The integration output remains:

- in-memory only;
- `dry_run_only = true`;
- deterministic envelope plus writer dry-run preview;
- no database write;
- no filesystem write;
- no export write;
- no production hook.

Unsafe or production-like writer previews are rejected rather than wrapped.

## Idempotency and metadata review

PASS. R7BF preserves:

- `review_item_id`;
- `audit_hash`;
- `run_id`;
- `adapter_version`;
- adapter and writer contract versions;
- `input_file_hashes`;
- writer `idempotency_key`;
- writer `record_payload_hash`;
- deterministic integration envelope hash.

R7BF does not recompute writer idempotency differently.

## clean_data safety boundary review

PASS. R7BF keeps clean_data blocked:

- `clean_data_write_count = 0`;
- `clean_data_eligible=true` fails closed;
- `VERIFIED` rows do not become clean_data;
- writer-preview records with `agreement_status = VERIFIED` are blocked;
- no `STRONG_EVIDENCE` promotion is introduced.

## Delivery gate boundary review

PASS. Non-`VERIFIED` rows remain review-bound. Unresolved rows retain `blocked_delivery_reason`. Corrected rows retain re-audit requirement and do not become delivery-clean records.

## No-hook and no-IO boundary review

PASS. R7BF remains under `tests/agent/` and adds no production integration. Static test coverage continues to reject imports/calls associated with:

```text
datefac_agent, pathlib, os, sqlite3, sqlalchemy, requests, socket, subprocess,
fitz, pdfplumber, pypdf, openai, open, write, write_text, mkdir, unlink,
remove, rename, replace, connect
```

No database model, repository, migration, output writer, export path, parser, model, MinerU, OCR, VLM, or production hook was added.

## Boundary review

PASS. This QA creates only:

```text
docs/agent/348N_R7BF_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REVIEW.md
```

No production code, tests, fixtures, outputs, dependencies, integrations, database models, writer implementations, migrations, or readiness gates are modified by this QA.

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

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
  36 passed in 0.14s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
  24 passed in 0.12s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
  75 passed in 0.22s

python -m pytest tests/agent -q
  375 passed in 1.33s

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  ?? docs/agent/348N_R7BF_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REVIEW.md

git diff --stat
  no tracked diff before staging because the QA report is untracked

git diff --name-only
  no tracked diff before staging because the QA report is untracked

git diff --check
  PASS
```

## Limitations

- This QA reviews a test-only dry-run integration helper; it is not production integration.
- No persistence backend, database model, repository, migration, transaction, filesystem export, delivery artifact, runner, CLI hook, or production review_queue writer exists.
- Fixture coverage remains curated and synthetic.
- Future tasks must keep production enablement separate from this test-only boundary.

## Decision

```text
Decision = 348N_R7BF_QA_CONFIRMED_NEGATIVE_PATH_HARDENING_VALID
```

R7BF-QA confirms the negative-path hardening is correct, conservative, test-only, fail-closed, no-hook, no-IO, dry-run-only, clean_data-safe, delivery-gate-safe, metadata-preserving, and readiness-closed.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：R7BF negative-path hardening is valid and boundary-safe
build_result（构建结果）= PASS：required py_compile commands passed
test_result（测试结果）= PASS：integration tests 36 passed；writer tests 24 passed；adapter skeleton tests 75 passed；full tests/agent 375 passed
files_modified（修改文件数）= 1：docs/agent/348N_R7BF_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REVIEW.md
error_count（错误数）= 0
negative_path_review_result（负路径审查结果）= PASS：missing/invalid token, disabled malformed path, malformed/minimal inputs, and raw/full-source cases covered
writer_preview_hardening_review_result（writer预览加固审查结果）= PASS：unsafe or production-like writer preview is blocked before envelope wrapping
test_only_token_review_result（test-only token审查结果）= PASS：valid path uses exact R7BE token and exact R7BC test-only writer config
malformed_payload_review_result（畸形payload审查结果）= PASS：empty, minimal adapter-like, and direct writer-preview-like payloads fail closed
fixture_review_result（fixture审查结果）= PASS：small curated test_only_r7be fixture; no raw full artifact payloads added
positive_path_regression_review_result（正路径回归审查结果）= PASS：valid dry-run integration path, metadata passthrough, and duplicate skip behavior still pass
dry_run_boundary_review_result（dry-run边界审查结果）= PASS：dry-run-only in-memory output; no DB/filesystem/export writes
idempotency_metadata_review_result（幂等与元数据审查结果）= PASS：writer idempotency keys and audit metadata remain preserved
clean_data_boundary_review_result（clean_data边界审查结果）= PASS：VERIFIED does not become clean_data or STRONG_EVIDENCE; clean intent fails closed
delivery_gate_boundary_review_result（交付闸门边界审查结果）= PASS：non-VERIFIED review-bound, unresolved blocked, corrected re-audit-required
no_hook_no_io_review_result（无hook无IO审查结果）= PASS：no IO, DB, export, parser, model, MinerU/OCR/VLM, or production hook added
boundary_check（边界检查）= PASS：QA report only; no production/tests/fixtures/output/dependency/readiness changes
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7BG review-queue writer dry-run integration boundary handoff checkpoint
```
