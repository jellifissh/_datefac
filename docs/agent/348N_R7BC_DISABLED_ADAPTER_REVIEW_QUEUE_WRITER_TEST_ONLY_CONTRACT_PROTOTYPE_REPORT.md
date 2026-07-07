# 348N-R7BC disabled adapter review-queue writer test-only contract prototype

## Task ID

```text
348N-R7BC disabled adapter review-queue writer test-only contract prototype
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 879c471..2da5521
  Fast-forward
  docs/codex_tasks/348N_R7BC_disabled_adapter_review_queue_writer_test_only_contract_prototype.md created

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -15:
  2da5521 docs: add R7BC writer contract task
  879c471 docs: add R7BB QA review
  57296c2 docs: add R7BB QA review task
  553e0ee docs: add R7BB review queue persistence plan
  d3ef02a docs: add R7BB persistence planning task
  e55b1d6 docs: add R7BA QA review
  983125f docs: add R7BA QA review task
  f4c507f docs: add R7BA adapter handoff checkpoint
  6ac9910 docs: add R7BA handoff checkpoint task
  f423e36 docs: add R7AZ QA review
  a8e2252 docs: add R7AZ QA review task
  4d3f599 test: consolidate disabled adapter positive contract
  adaf893 docs: add R7AZ positive contract task
  2037d3d docs: add R7AY QA review
  d13e013 docs: add R7AY QA review task
```

Worktree was clean after pull. This task creates only the four allowed R7BC files.

## Files reviewed

Required context:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `docs/codex_tasks/348N_R7BC_disabled_adapter_review_queue_writer_test_only_contract_prototype.md`
- `docs/agent/348N_R7BB_QA_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE_REVIEW.md`
- `docs/agent/348N_R7BB_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE.md`
- `docs/agent/348N_R7BA_QA_DISABLED_ADAPTER_CONTRACT_SUMMARY_AND_HANDOFF_CHECKPOINT_REVIEW.md`
- `docs/agent/348N_R7AZ_QA_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_REVIEW.md`
- `docs/agent/348N_R7AY_QA_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REVIEW.md`

Current adapter slice reviewed:

- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json`

Related modules reviewed read-only:

- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`

## R7BB-QA recap

R7BB-QA confirmed the persistence planning slice was valid and boundary-safe:

```text
future writer must be disabled by default
future writer must accept only adapter candidate output
future writer must be dry-run-first
future writer must be deterministic and duplicate-safe
future writer must keep audit metadata
future writer must store bounded evidence_preview only
future writer must never write clean_data
future writer must never export delivery files
future writer must keep readiness_gates CLOSED
```

R7BC implements only a test-only in-memory contract prototype that exercises those rules without adding real persistence.

## 大白话说明

这一轮像是在桌面上摆了一个“模拟落库沙盘”：把 adapter 已经验证过的候选复核项放进去，看未来如果要存，会生成哪些 review_queue 记录、哪些会因为重复跳过、哪些会因为冲突拒绝。

它不是数据库写入器，不写文件、不建表、不导出、不接生产。默认还是关的；只有测试 token 打开后，才返回内存里的 dry-run 预览。

## Test-only writer contract scope

Created test-only helper:

```text
tests/agent/review_queue_writer_contract_348n.py
```

Scope:

- in-memory only;
- disabled by default;
- explicit R7BC test-only token required;
- accepts only enabled adapter candidate output shape;
- returns dry-run preview records;
- does not write filesystem, database, clean_data, evidence index, delivery, or output artifacts;
- does not modify `datefac_agent/`;
- does not create production hook.

## In-memory dry-run design

Main entry point:

```text
build_review_queue_writer_dry_run_preview(...)
```

Default behavior:

```text
writer_status = DISABLED
dry_run_only = true
review_queue_dry_run_records = []
all write counts = 0
readiness_gates = CLOSED
```

Enabled test-only behavior:

```text
writer_status = ENABLED_TEST_ONLY_DRY_RUN
dry_run_only = true
review_queue_dry_run_records = metadata-only records
dry_run_action = WOULD_INSERT or WOULD_SKIP_DUPLICATE
clean_data_write_count = 0
delivery_write_count = 0
filesystem_write_count = 0
database_write_count = 0
```

## Input contract

Accepted top-level shape:

```text
adapter_status
review_queue_candidate_items
discrepancy_report_candidate_rows
blocked_delivery_candidate_rows
delivery_reaudit_candidate_rows
audit_contract
```

Required safeguards:

- `adapter_status` must be `ENABLED_TEST_ONLY`;
- adapter contract version must match the disabled adapter contract;
- audit metadata must include run id, adapter version, input hashes, counts, readiness gates, external-call counts, boundary flags, and adapter audit hash;
- readiness gates must equal CLOSED;
- external-call counts must be zero;
- review_queue candidate statuses must be non-`VERIFIED`;
- clean and delivery admission flags must remain false;
- forbidden raw/full-source fields fail closed.

## Dry-run record shape

Dry-run preview records include:

```text
review_item_id
run_id
source_file_hash
input_file_hashes
adapter_version
contract_version
adapter_contract_version
audit_hash
metric_name
period
candidate_value
candidate_unit
agreement_status
review_status
reviewer_action
review_reason
blocked_delivery_reason
evidence_preview
source_trace
idempotency_key
dry_run_only
dry_run_action
record_payload_hash
clean_data_write_count
delivery_write_count
```

The record shape is metadata-first and does not contain full source text, raw MinerU blocks, raw Excel rows, raw parser output, full table HTML, PDF text, or OCR/model output bodies.

## Idempotency and duplicate prevention

Idempotency key is deterministic from:

```text
writer contract version
run_id
review_item_id
source_row_id
agreement_status
audit_hash
sorted input_file_hashes
```

Duplicate behavior:

- no existing hash -> `WOULD_INSERT`;
- same idempotency key and same payload hash -> `WOULD_SKIP_DUPLICATE`;
- same idempotency key and different payload hash -> fail closed;
- duplicate idempotency key inside one dry-run batch -> fail closed.

No actual insert/update occurs because this is dry-run only.

## Audit metadata retention

The dry-run preview retains:

- `run_id`;
- `adapter_version`;
- writer `contract_version`;
- adapter `contract_version`;
- `input_file_hashes`;
- `review_item_id`;
- `audit_hash`;
- `adapter_item_id` in `source_trace`;
- `matched_locator`;
- `matched_text_sha256`;
- `evidence_preview_sha256`;
- readiness gates;
- external-call counters;
- boundary flags.

Input hashes are deep-copied so input mutation after a call cannot mutate output.

## Evidence preview and source_text boundary

Allowed:

- bounded `evidence_preview`;
- preview hash metadata;
- locator/hash metadata;
- compact source trace.

Rejected:

- `source_text`;
- `full_source_text`;
- `raw_source_text`;
- `content_list_v2`;
- `raw_mineru_block`;
- `raw_excel_row`;
- `workbook_sheets`;
- parser/PDF/OCR/model raw payload keys;
- oversized evidence preview.

Tests also verify forbidden full-source keys are absent from serialized dry-run output.

## clean_data safety boundary

The writer contract never writes clean data:

```text
clean_data_write_count = 0
delivery_write_count = 0
clean_data_eligible=true fails closed
delivery_clean_admitted=true fails closed
clean_data_admitted=true fails closed
VERIFIED-only input produces no review_queue persistence and no clean persistence
```

`VERIFIED` is not promoted to `STRONG_EVIDENCE` and is not admitted to clean_data.

## Delivery gate boundary

Unresolved review rows keep a `blocked_delivery_reason`. Corrected delivery candidates remain re-audit-required and do not become clean delivery records.

The dry-run summary keeps:

```text
blocked_delivery_count
reaudit_required_count
verified_without_clean_gate_count
delivery_write_count = 0
```

## Corrected row and re-audit policy

The fixture includes a corrected non-`VERIFIED` delivery candidate. The writer preview:

- creates no review_queue persistence record for it;
- keeps `reaudit_required_count = 1`;
- keeps `delivery_write_count = 0`;
- keeps `clean_data_write_count = 0`.

This proves reviewer correction still cannot bypass future re-audit or clean gate policy.

## Failure and fail-closed behavior

Covered fail-closed cases:

- missing adapter candidate output fields;
- unexpected top-level fields;
- raw MinerU-like payload;
- raw Excel-like payload;
- full source_text payload;
- opened readiness gate;
- clean_data write intent;
- missing audit metadata;
- `VERIFIED` inside review_queue candidates;
- duplicate idempotency collision;
- wrong adapter status/schema mismatch;
- evidence preview boundary violations.

## No-hook and no-IO boundary

The test-only helper imports only standard in-memory utilities plus constants from the existing disabled adapter module.

Static tests assert no imports/calls for:

```text
filesystem writes
database connections
network calls
subprocess calls
PDF parser hooks
OpenAI/model hooks
MinerU/OCR/VLM hooks
```

No production module imports this test helper.

## Validation outputs

Required commands:

```text
python -m py_compile tests/agent/review_queue_writer_contract_348n.py
  PASS

python -m py_compile tests/agent/test_review_queue_writer_contract_348n.py
  PASS

python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
  PASS

python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
  PASS

pytest tests/agent/test_review_queue_writer_contract_348n.py -q
  24 passed in 0.13s

pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
  75 passed in 0.25s

pytest tests/agent -q
  339 passed in 1.32s

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  ?? docs/agent/348N_R7BC_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
  ?? tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json
  ?? tests/agent/review_queue_writer_contract_348n.py
  ?? tests/agent/test_review_queue_writer_contract_348n.py

git diff --stat
  no tracked diff before staging because all R7BC files are new and untracked

git diff --name-only
  no tracked diff before staging because all R7BC files are new and untracked

git diff --check
  PASS
```

## Limitations

- This is not real persistence.
- No database model, repository, migration, writer outside tests, filesystem output, or production hook exists.
- Fixture is curated and synthetic.
- R7BC proves contract shape only; production persistence remains forbidden until a future explicit task.

## Decision

```text
Decision = 348N_R7BC_TEST_ONLY_REVIEW_QUEUE_WRITER_CONTRACT_PROTOTYPE_ADDED
```

R7BC adds a test-only in-memory writer contract prototype. It validates adapter candidate output, returns dry-run review_queue records, proves idempotency and duplicate handling, rejects raw/full-source/clean/readiness violations, and keeps clean_data, delivery, filesystem, database, and readiness gates closed.

## Recommended next task

```text
348N-R7BC-QA disabled adapter review-queue writer test-only contract prototype review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：test-only in-memory review_queue writer contract prototype added
build_result（构建结果）= PASS：required py_compile commands passed
test_result（测试结果）= PASS：writer tests 24 passed；adapter skeleton tests 75 passed；full tests/agent 339 passed
files_modified（修改文件数）= 4
error_count（错误数）= 0
writer_contract_result（writer契约结果）= PASS：disabled-by-default, explicit-test-token gated, adapter-output-only, in-memory only
dry_run_preview_result（dry-run预览结果）= PASS：preview records are dry_run_only and all write counts remain zero
fixture_result（fixture结果）= PASS：small curated R7BC fixture covers valid, verified-only, non-verified, unresolved, corrected, and invalid cases
input_rejection_result（输入拒绝结果）= PASS：raw MinerU/Excel/full source_text/readiness/clean/schema cases fail closed
idempotency_result（幂等结果）= PASS：deterministic keys, duplicate skip plan, and collision failure are covered
audit_metadata_result（审计元数据结果）= PASS：run_id, adapter_version, contract versions, input hashes, review_item_id, audit_hash, and source trace retained
evidence_boundary_result（证据边界结果）= PASS：bounded evidence_preview only; full source_text/raw artifacts rejected and absent from output
clean_data_boundary_result（clean_data边界结果）= PASS：no clean_data writes; VERIFIED/corrected rows do not become clean records
delivery_gate_boundary_result（交付闸门边界结果）= PASS：blocked_delivery_reason and re-audit-required state retained; no delivery writes
no_hook_no_io_result（无hook无IO结果）= PASS：test-only helper has no filesystem/database/network/parser/model hook
boundary_check（边界检查）= PASS：only allowed R7BC files changed; no production code/tests/fixtures outside allowed scope/output/dependencies/readiness changes
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7BC-QA disabled adapter review-queue writer test-only contract prototype review
```
