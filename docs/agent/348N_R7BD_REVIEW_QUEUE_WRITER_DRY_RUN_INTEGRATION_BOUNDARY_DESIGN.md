# 348N-R7BD review-queue writer dry-run integration boundary design

## Task ID

```text
348N-R7BD review-queue writer dry-run integration boundary design
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating d9aa2f4..d05a3ab
  Fast-forward
  docs/codex_tasks/348N_R7BD_review_queue_writer_dry_run_integration_boundary_design.md created

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -15:
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
  f423e36 docs: add R7AZ QA review
  a8e2252 docs: add R7AZ QA review task
```

Worktree was clean after pull. This R7BD slice is docs-only and creates only this design report.

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
- `docs/codex_tasks/348N_R7BD_review_queue_writer_dry_run_integration_boundary_design.md`

Prior reports:

- `docs/agent/348N_R7BC_QA_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7BC_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7BB_QA_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE_REVIEW.md`
- `docs/agent/348N_R7BB_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE.md`
- `docs/agent/348N_R7BA_QA_DISABLED_ADAPTER_CONTRACT_SUMMARY_AND_HANDOFF_CHECKPOINT_REVIEW.md`

Current slices reviewed read-only:

- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json`

Read-only facts observed:

```text
R7BC changed four allowed files only.
R7BC writer helper path = tests/agent/review_queue_writer_contract_348n.py
R7BC writer helper has no production references from datefac_agent/.
R7BC fixture scope = test_only_r7bc.
R7BC fixture size = 46844 bytes.
R7BC valid fixture review rows = 2.
R7BC fixture non-VERIFIED statuses include MISSING_EVIDENCE and UNVERIFIED.
R7BC corrected fixture delivery row remains re-audit-required.
```

## R7BC-QA recap

R7BC-QA confirmed:

```text
writer contract is test-only
writer contract is disabled by default
explicit test-only token is required
writer returns dry-run preview only
no database write exists
no file output or export exists
no migration, repository class, or production writer exists
no production pipeline hook exists
only adapter candidate output is accepted
raw MinerU / raw Excel / full source_text inputs fail closed
readiness_gates remain CLOSED
VERIFIED rows do not become clean_data
non-VERIFIED rows remain review-bound
unresolved rows retain blocked_delivery_reason
corrected rows remain re-audit-required
idempotency is deterministic
no IO / parser / model / MinerU / OCR / VLM calls exist
```

R7BD therefore designs only the future integration boundary between the disabled adapter output and the R7BC test-only dry-run writer. It does not implement that boundary.

## 大白话说明

现在有两块安全积木：一块是 disabled adapter，能把已经验证过的差异候选项变成内存里的 candidate output；另一块是 test-only dry-run writer，能把 candidate output 模拟成“如果以后要存，会长什么样”的预览。

R7BD 不把两块积木真的接进生产。它只是画清楚以后如果要接，中间这段桥必须怎样开关、怎样验字段、什么输入必须拒绝、失败怎么停、怎么回滚。简单说：先画安全桥的施工图，不开桥、不通车、不收费。

## Integration boundary scope

The proposed future integration boundary is a narrow test-only adapter-to-writer bridge.

In scope for a future implementation:

- accept already-built disabled adapter candidate output;
- validate the integration envelope before calling the test-only writer;
- call only `tests/agent/review_queue_writer_contract_348n.py` in future tests;
- return the writer dry-run preview under a small integration envelope;
- keep all outputs in memory;
- expose counts, status, and boundary flags for test assertions;
- preserve adapter audit metadata and writer dry-run record metadata.

Out of scope:

- production pipeline hook;
- real persistence;
- database model, repository, migration, or storage code;
- file output, CSV/XLSX/JSON export, or delivery artifact;
- clean_data admission;
- evidence index write;
- readiness gate change;
- MinerU/OCR/LLM/VLM/PDF extraction;
- raw artifact parsing.

## Proposed flow

Future test-only flow:

```text
1. Build disabled adapter candidate output under explicit adapter test-only enable.
2. Pass only that adapter output into a future integration-boundary helper.
3. Integration boundary verifies its own feature flag is disabled by default.
4. If explicitly test-enabled, integration boundary revalidates envelope-level safety:
   - adapter_status = ENABLED_TEST_ONLY
   - audit_contract exists
   - readiness_gates = CLOSED
   - external_call_counts = ZERO
   - no forbidden raw/full-source keys
   - no clean/delivery write flags
5. Integration boundary calls only the R7BC in-memory writer contract.
6. Writer returns dry-run preview records.
7. Integration boundary wraps the preview with minimal envelope metadata.
8. Integration boundary returns memory-only result.
```

No production runner, CLI, review queue persistence writer, or delivery pipeline should call this boundary until a later explicit implementation and QA task permits it.

## Accepted inputs

Accepted input must be exactly:

```text
validated disabled-adapter candidate output
```

Required characteristics:

- produced by the current disabled adapter output shape;
- `adapter_status = ENABLED_TEST_ONLY`;
- `audit_contract.contract_version` matches the disabled adapter contract;
- `review_queue_candidate_items` contains only review-bound non-`VERIFIED` statuses;
- `delivery_reaudit_candidate_rows` may include `VERIFIED` or corrected rows, but only as re-audit/explicit-clean-gate-required metadata;
- readiness gates are closed;
- external call counts are zero;
- boundary flags show no production hook, no clean write, no delivery write, and no full source text serialization;
- bounded evidence previews only;
- run id, adapter version, input file hashes, review item id, audit hash, and locator/hash metadata are present.

The integration boundary should treat the adapter output as the only source of truth for writer input. It must not merge in side data from raw local outputs.

## Rejected inputs

The future integration boundary must reject:

- direct user payloads;
- raw MinerU output, including `content_list_v2`;
- raw DateFac Excel rows or workbook sheets;
- raw parser output;
- raw PDF page text or OCR output;
- full `source_text`, `full_source_text`, `raw_source_text`, or nested equivalents;
- file paths to raw artifacts as implicit input sources;
- opened readiness gates;
- nonzero external call counts;
- `clean_data_eligible=true`;
- `delivery_clean_admitted=true`;
- `clean_data_admitted=true`;
- `evidence_level=STRONG_EVIDENCE`;
- `VERIFIED` rows inside review_queue candidates;
- unsupported agreement statuses;
- missing audit metadata;
- count mismatches;
- unsupported writer configuration;
- any payload containing production hook or write-intent flags.

Rejection must occur before the writer call when the invalid shape is detectable at the integration boundary.

## Dry-run writer call boundary

The future integration boundary may call only:

```text
build_review_queue_writer_dry_run_preview(...)
```

Call constraints:

- the integration boundary itself must be disabled by default;
- a separate explicit integration test-only enable token should be required;
- the writer must also require its own R7BC test-only token;
- the integration boundary must not bypass writer validation;
- `existing_record_hashes`, if passed, must be metadata-only and deterministic;
- writer result must remain dry-run only;
- writer write counters must remain zero;
- writer output must be returned without mutation except for an allowed outer integration envelope.

The boundary should not import or call a future production storage adapter.

## Output envelope design

Future integration output should be a small memory-only envelope:

```text
integration_status
integration_contract_version
dry_run_only
source_adapter_contract_version
writer_contract_version
run_id
adapter_version
input_file_hashes
review_queue_dry_run_records
dry_run_summary
integration_summary
readiness_gates
external_call_counts
boundary_flags
```

Envelope boundary flags must include:

```text
production_hook = false
writes_review_queue = false
writes_clean_data = false
writes_delivery = false
writes_filesystem = false
writes_database = false
dry_run_preview_only = true
verified_auto_clean = false
verified_promotes_to_strong_evidence = false
full_source_text_serialized = false
```

The envelope must not add wall-clock timestamps unless a future test defines deterministic timestamps. It must not add `created_at` from system time.

## Idempotency and duplicate prevention

The integration boundary must preserve writer idempotency unchanged.

Rules:

- do not recompute writer `idempotency_key` differently;
- do not reorder dry-run records unless future tests define deterministic ordering;
- do not strip `record_payload_hash`;
- pass through duplicate skip plans;
- pass through idempotency collision failures;
- same adapter output and same existing record hashes must produce the same integration dry-run output;
- integration envelope metadata must not change the writer record idempotency key.

If the integration boundary adds its own `integration_run_id`, that id must not participate in writer idempotency.

## Audit metadata pass-through

The integration boundary must pass through:

- `run_id`;
- `adapter_version`;
- adapter contract version;
- writer contract version;
- `input_file_hashes`;
- `review_item_id`;
- `audit_hash`;
- `adapter_item_id`;
- `matched_locator`;
- `matched_text_sha256`;
- `evidence_preview_sha256`;
- `adapter_audit_hash` or source audit metadata hash when present;
- status counts;
- readiness gates;
- external call counts;
- boundary flags.

No audit metadata should be recomputed from raw MinerU, raw Excel, or raw source text. The bridge should copy or reference validated adapter/writer metadata only.

## Evidence preview and source_text boundary

Allowed through the integration boundary:

- bounded `evidence_preview`;
- `evidence_preview_sha256`;
- `matched_text_sha256`;
- locator metadata;
- compact source trace.

Forbidden through the boundary:

- full source text;
- raw page text;
- raw MinerU blocks;
- raw table HTML;
- raw Excel rows;
- workbook sheets/cells;
- parser/PDF/OCR/LLM/VLM output bodies.

The boundary must reject forbidden keys before the writer call if they are present in the envelope or adapter output. It must also verify the writer output does not introduce forbidden raw/full-source fields.

## clean_data safety boundary

The integration boundary must not write or imply clean_data.

Rules:

- `clean_data_write_count` must remain `0`;
- `clean_data_eligible=true` must fail closed;
- `clean_data_admitted=true` must fail closed;
- `VERIFIED` is not clean admission;
- corrected rows are not clean admission;
- no delivery-clean candidate may be turned into a clean row;
- no `STRONG_EVIDENCE` promotion is allowed.

Any future clean_data admission must remain a separate explicit gate with its own design, implementation, tests, and QA.

## Delivery gate boundary

Delivery remains blocked for unresolved rows.

Rules:

- non-`VERIFIED` review rows remain review-bound;
- unresolved rows retain `blocked_delivery_reason`;
- `delivery_write_count` remains `0`;
- no delivery export file is generated;
- `formal_client_export_allowed` remains false;
- `demo_export_only` remains true;
- writer dry-run preview is not a delivery artifact.

The integration boundary may report delivery blocking counts, but must not resolve or override them.

## Corrected row and re-audit policy

Corrected rows remain re-audit-required:

- `CORRECT_VALUE`, `CORRECT_UNIT`, `CORRECT_PERIOD`, or `CORRECT_METRIC` reviewer actions are review metadata only;
- corrected rows cannot become clean_data through this integration boundary;
- corrected rows cannot become delivery rows through this integration boundary;
- re-audit status must pass through unchanged;
- future clean eligibility requires a separate explicit policy gate.

This protects against turning manual corrections into silent delivery facts.

## Failure and fail-closed behavior

The future integration boundary must fail closed on:

- disabled boundary without explicit test-only enable;
- invalid or missing integration token;
- invalid adapter output schema;
- invalid writer output schema;
- raw/full-source payload;
- opened readiness gate;
- nonzero external call count;
- clean or delivery write intent;
- unsupported status;
- `VERIFIED` inside review_queue candidates;
- missing or mismatched audit metadata;
- idempotency collision;
- duplicate idempotency key inside a batch;
- non-deterministic output envelope;
- any writer exception.

On failure, it must return or raise a failure state without producing partial dry-run records unless a future test explicitly defines a safe failure envelope. It must not fallback to raw artifacts.

## Rollback plan

Because R7BD is design-only, rollback for this slice is simply:

```text
remove docs/agent/348N_R7BD_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN.md
```

For a future implementation slice, rollback must:

- delete or disable only the integration boundary helper;
- keep disabled adapter tests intact;
- keep R7BC writer contract tests intact;
- keep fixtures intact unless the future task specifically owns them;
- remove any integration-specific fixture/report only;
- not touch production code if the implementation remains test-only;
- not touch outputs, clean_data, delivery, database, or migrations;
- preserve readiness gates closed.

If a future implementation accidentally adds production hooks or writes, rollback must remove those hooks first and then re-run full adapter/writer tests.

## Future tests before implementation

Future integration-boundary implementation should add tests for:

```text
default integration boundary disabled
explicit test-only enable required
valid adapter candidate output reaches dry-run writer preview
invalid raw payload rejected before writer call
raw MinerU / raw Excel / raw parser / full source_text rejected
adapter metadata passed through unchanged
writer dry-run preview returned unchanged except allowed envelope metadata
VERIFIED rows do not become clean_data
non-VERIFIED rows remain review-bound
unresolved rows retain blocked_delivery_reason
corrected rows retain re-audit requirement
readiness_gates OPEN rejected
full source_text rejected before writer call
idempotency key stable end-to-end
same input retry produces same dry-run preview
writer idempotency collision propagates fail-closed
input mutation cannot mutate output
no IO / no DB / no export / no production hook
```

Implementation must not proceed until these tests are part of the future task.

## No-hook and no-IO boundary

The integration boundary must not import:

```text
os
pathlib for write paths
sqlite3
sqlalchemy
requests
socket
subprocess
fitz
pdfplumber
pypdf
openai
datefac legacy package
```

It must not call:

```text
open
write
write_text
mkdir
connect
unlink
remove
replace
rename
run_pilot
MinerU
OCR
LLM
VLM
```

Static tests should scan the future integration helper for forbidden imports/calls and scan `datefac_agent/` for production references.

## Validation outputs

Required commands run:

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
  24 passed in 0.15s

pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
  75 passed in 0.27s

pytest tests/agent -q
  339 passed in 1.32s

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  ?? docs/agent/348N_R7BD_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN.md

git diff --stat
  no tracked diff before staging because the report is untracked

git diff --name-only
  no tracked diff before staging because the report is untracked

git diff --check
  PASS
```

## Remaining risks

- No integration boundary implementation exists yet.
- No production invocation point is approved.
- The writer contract is test-only and curated-fixture based.
- No persistence backend, transaction model, or rollback code exists.
- Future implementation could accidentally accept direct raw payloads; this design forbids that.
- Future implementation could accidentally mutate writer preview output; this design restricts mutation to envelope metadata only.
- Future implementation could accidentally blur dry-run preview with persistence; this design forbids real writes.
- Older progress/handoff docs may still contain stale task pointers.

## Decision

```text
Decision = 348N_R7BD_DRY_RUN_INTEGRATION_BOUNDARY_DESIGNED_DOCS_ONLY
```

R7BD defines a conservative future integration boundary between disabled adapter candidate output and the test-only dry-run writer. The boundary must remain disabled by default, explicit-test-only, adapter-output-only, dry-run-only, metadata-first, idempotent, fail-closed, no-hook, no-IO, no-clean-data, no-delivery, and readiness-closed.

## Recommended next task

```text
348N-R7BD-QA review-queue writer dry-run integration boundary design review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：docs-only dry-run integration boundary design completed
build_result（构建结果）= PASS：required py_compile commands passed
test_result（测试结果）= PASS：writer tests 24 passed；adapter skeleton tests 75 passed；full tests/agent 339 passed
files_modified（修改文件数）= 1：docs/agent/348N_R7BD_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN.md
error_count（错误数）= 0
integration_design_result（集成设计结果）= PASS：future bridge is disabled-by-default, explicit-test-only, adapter-output-only, dry-run-only
plain_language_result（大白话说明结果）= PASS：explains this is safety bridge design, not implementation or production connection
accepted_input_boundary_result（允许输入边界结果）= PASS：only validated disabled-adapter candidate output is accepted
rejected_input_boundary_result（拒绝输入边界结果）= PASS：raw MinerU/Excel/parser/full source_text/direct payload/readiness/clean/write intents rejected
dry_run_boundary_result（dry-run边界结果）= PASS：future boundary may call only test-only writer and return memory-only preview
idempotency_result（幂等结果）= PASS：writer idempotency and duplicate behavior must pass through unchanged
audit_metadata_result（审计元数据结果）= PASS：adapter/writer audit metadata pass-through requirements specified
evidence_boundary_result（证据边界结果）= PASS：bounded evidence_preview and hashes only; full source_text forbidden
clean_data_boundary_result（clean_data边界结果）= PASS：no clean_data writes or VERIFIED/corrected clean admission
delivery_gate_boundary_result（交付闸门边界结果）= PASS：unresolved rows remain delivery-blocked; no delivery export
rollback_plan_result（回滚计划结果）= PASS：future rollback limited to integration boundary slice without touching adapter/writer contracts
future_test_plan_result（未来测试计划结果）= PASS：negative, positive, metadata, idempotency, no-IO, and readiness tests listed before implementation
boundary_check（边界检查）= PASS：design report only; no production code/tests/fixtures/output/dependencies/readiness changes
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7BD-QA review-queue writer dry-run integration boundary design review
```
