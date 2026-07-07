# 348N-R7BB disabled adapter review-queue persistence planning slice

## Task ID

```text
348N-R7BB disabled adapter review-queue persistence planning slice
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Already up to date.
  From https://github.com/jellifissh/_datefac
   * branch            pivot/348-agent-foundation -> FETCH_HEAD

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -15:
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
  a29fca1 test: expand disabled adapter negative matrix
  9377b9c docs: add R7AY negative matrix task
  904724f docs: add R7AX QA review
  1c6ee8a docs: add R7AX QA review task
```

Worktree was clean after pull. This task is docs-only and creates only this planning report.

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
- `docs/codex_tasks/348N_R7BB_disabled_adapter_review_queue_persistence_planning_slice.md`

Directly related reports:

- `docs/agent/348N_R7BA_QA_DISABLED_ADAPTER_CONTRACT_SUMMARY_AND_HANDOFF_CHECKPOINT_REVIEW.md`
- `docs/agent/348N_R7BA_DISABLED_ADAPTER_CONTRACT_SUMMARY_AND_HANDOFF_CHECKPOINT.md`
- `docs/agent/348N_R7AZ_QA_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_REVIEW.md`
- `docs/agent/348N_R7AY_QA_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7AX_QA_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REVIEW.md`
- `docs/agent/348N_R7AW_QA_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REVIEW.md`

Current adapter slice reviewed read-only:

- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json`

Related persistence-adjacent modules reviewed read-only:

- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`

## R7BA-QA recap

R7BA-QA confirmed the disabled adapter checkpoint is accurate and boundary-safe:

```text
current adapter path = datefac_agent/review/production_boundary_review_queue_adapter.py
default config enabled = false
disabled output candidate lists = empty
enabled mode requires TEST_ONLY_ENABLE_TOKEN
enabled mode validates already-built boundary payloads only
enabled mode returns in-memory candidate structures only
no production hook exists
no IO, parser, model, extraction, or delivery write exists
review_queue candidates are metadata-first and bounded-preview only
VERIFIED does not enter review_queue automatically
VERIFIED does not enter clean_data automatically
VERIFIED does not become STRONG_EVIDENCE
readiness_gates remain CLOSED
```

The QA result makes R7BB a planning slice only: it can describe future persistence, but must not implement a writer or connect production.

## 大白话说明

这一轮不是“把复核队列写进数据库”，也不是“开始生产上线”。这一轮只是先把未来如果要存，应该怎么存、只能存什么、什么绝对不能存、重复执行怎么不写重复行、出错怎么回滚写清楚。

更直白地说：现在 adapter 只会在测试开关打开时生成内存里的候选复核项。R7BB 只是给未来的“落库按钮”画安全图纸：按钮默认必须关着；只能吃 adapter 已经验证过的候选输出；不能吃原始 MinerU、Excel、parser 输出或完整 `source_text`；不能写 `clean_data`；不能开交付闸门。

## Persistence planning scope

This plan covers only a future persistence layer for review-bound adapter candidate output.

In scope for future design:

- a disabled-by-default review_queue persistence writer;
- a dry-run preview that shows exactly what would be written;
- a strict input contract that accepts only output from the disabled adapter candidate shape;
- a minimal persisted review_queue record shape;
- deterministic idempotency and duplicate prevention;
- audit metadata retention;
- rollback requirements;
- validation requirements before any implementation task.

Out of scope for R7BB:

- no database model;
- no repository class;
- no writer implementation;
- no migration;
- no output file;
- no production pipeline hook;
- no clean_data write;
- no delivery export;
- no readiness gate change.

## Candidate output allowed for future persistence

A future writer may accept only validated adapter candidate output, not upstream raw extraction artifacts.

Allowed input source:

```text
build_production_boundary_review_queue_adapter_output(...)
  -> review_queue_candidate_items
  -> audit_contract
  -> optional blocked_delivery_candidate_rows for blocked_delivery_reason derivation
```

Allowed candidate classes:

- `review_queue_candidate_items` with non-`VERIFIED` agreement statuses;
- metadata from `audit_contract` needed to prove run identity, adapter contract, input hashes, closed readiness, and zero external calls;
- bounded `evidence_preview` and its hash;
- blocked delivery metadata for unresolved rows.

Persistable statuses remain review-bound only:

```text
UNVERIFIED
DISAGREED
AMBIGUOUS
MISSING_EVIDENCE
PARSE_SKIPPED
```

Future writer must reject:

- `VERIFIED` review_queue records;
- any record implying direct clean admission;
- any record missing audit metadata;
- any record not produced by the adapter candidate output contract.

## Forbidden inputs and forbidden writes

Forbidden inputs:

- raw MinerU artifacts, including `content_list_v2`, raw blocks, full table HTML, markdown, OCR output, or parser output;
- raw DateFac Excel rows, workbook sheets, worksheets, cells, or unvalidated spreadsheet payloads;
- raw PDF pages, page texts, extracted text layers, or PDF parser outputs;
- full `source_text`, `full_source_text`, `raw_source_text`, `full_text`, or nested equivalents;
- payloads with opened readiness gates;
- payloads with `STRONG_EVIDENCE` promotion;
- payloads with `clean_data_eligible=true`, `delivery_clean_admitted=true`, or `clean_data_admitted=true`;
- payloads not matching the adapter contract version.

Forbidden writes:

- no `clean_data` rows;
- no delivery exports;
- no evidence index writes;
- no DateFac Excel mutation;
- no MinerU output mutation;
- no output/input/temp/data/legacy writes;
- no production readiness state updates;
- no automatic reviewer decision writes;
- no raw evidence body or full source text persistence.

## Proposed review_queue record shape

Minimal future persisted record shape:

| Field | Requirement | Notes |
| --- | --- | --- |
| `review_item_id` | required | Preserved from adapter candidate; stable human/audit identity. |
| `run_id` | required | Preserved from adapter/audit metadata. |
| `source_file_hash` | optional | Use when one primary source file hash is available; otherwise use `input_file_hashes`. |
| `input_file_hashes` | required | Non-empty mapping copied from adapter metadata. |
| `adapter_version` | required | Identifies upstream adapter output source. |
| `contract_version` | required | Must match current adapter contract accepted by the future writer. |
| `audit_hash` | required | Preserved source audit hash or row audit hash. |
| `metric_name` | required | Derived from `candidate_metric_name`. |
| `period` | required | Derived from `candidate_period`. |
| `candidate_value` | required | Candidate extracted value, string-preserved. |
| `candidate_unit` | optional | Required if present in candidate; absent value must not be invented. |
| `agreement_status` | required | Must be one of non-`VERIFIED` review-bound statuses. |
| `review_status` | required | Initial value should be `OPEN` or equivalent unresolved state. |
| `reviewer_action` | optional | Empty until human action; must be enum-validated if present. |
| `review_reason` | required | Derived from `risk_reason` / `suggested_action`. |
| `blocked_delivery_reason` | required | Required for unresolved persisted rows; derived from blocked delivery candidate or status policy. |
| `evidence_preview` | required | Bounded preview only; no full source text. |
| `created_at` | required | Future writer timestamp; must not affect idempotency key. |
| `source_trace` | required | Compact metadata: source document, row id, locator, subqueue, matched hash. |
| `idempotency_key` | required | Deterministic key used for upsert/duplicate prevention. |

Optional fields may include:

- `severity`;
- `subqueue`;
- `matched_locator`;
- `matched_text_sha256`;
- `evidence_preview_sha256`;
- `source_document_id`;
- `source_row_id`;
- `adapter_item_id`.

Forbidden persisted fields:

- `source_text`;
- `full_source_text`;
- `raw_source_text`;
- `full_text`;
- `raw_mineru_block`;
- `content_list_v2`;
- `raw_excel_row`;
- `workbook_sheets`;
- `cells`;
- `full_table_html`;
- `raw_pdf_text`;
- `parser_output`;
- any field carrying full raw evidence bodies.

## Idempotency and duplicate prevention

Future writer must use deterministic idempotency before any real write.

Recommended idempotency key:

```text
sha256(
  contract_version
  + run_id
  + review_item_id
  + source_row_id
  + agreement_status
  + audit_hash
  + sorted(input_file_hashes)
)
```

Rules:

- `created_at`, dry-run timestamp, database auto IDs, and writer execution ID must not participate in idempotency.
- Same adapter output retried with the same run/input hashes must not create duplicate rows.
- If the same idempotency key already exists with identical payload hash, retry is a no-op.
- If the same idempotency key exists with different payload hash, future writer must fail closed and require manual conflict resolution.
- If a later run produces a different `run_id` but same source row and different evidence/audit hash, it should create a new auditable version rather than mutate the old record silently.
- Duplicate prevention must happen before write, not after a partial insert.

## Audit metadata retention

Future persistence must retain enough metadata to reconstruct what was reviewed without storing raw artifacts.

Required retained metadata:

- `run_id`;
- `adapter_version`;
- `contract_version`;
- `input_file_hashes`;
- `review_item_id`;
- `audit_hash`;
- `adapter_item_id` when present;
- `adapter_audit_hash` or `source_audit_metadata_hash`;
- `agreement_status`;
- `review_status`;
- `subqueue`;
- `severity`;
- `matched_locator`;
- `matched_text_sha256`;
- `evidence_preview_sha256`;
- `readiness_gates`;
- `external_call_counts`;
- `boundary_flags`.

Retention rules:

- readiness must remain exactly closed at persistence time;
- external call counts must remain zero for this disabled adapter slice;
- audit metadata is copied from adapter output, not recomputed from raw MinerU/Excel;
- record payload hash should be computed over the normalized persisted record for later integrity checks.

## Evidence preview and source_text boundary

Future persistence stores only bounded evidence previews and metadata.

Allowed:

- `evidence_preview` with the adapter-enforced length limit;
- `evidence_preview_sha256`;
- `matched_text_sha256`;
- `matched_locator`;
- compact `source_trace`;
- source document identity and source row identity.

Forbidden:

- full source text;
- raw page text;
- raw MinerU block text;
- full table HTML;
- raw Excel row dumps;
- parser/OCR/LLM/VLM output bodies.

If `evidence_preview` exceeds the limit, is missing, or appears to be a raw full-text dump, future writer must reject the whole batch. It must not truncate silently because silent truncation could hide an uncontrolled serialization path.

## clean_data safety boundary

Future review_queue persistence must never write `clean_data`.

Rules:

- `clean_data_eligible=true` is rejected.
- `delivery_clean_admitted=true` is rejected.
- `clean_data_admitted=true` is rejected.
- `VERIFIED` does not imply clean admission.
- corrected reviewer decisions do not imply clean admission.
- persisted review_queue records are review obligations, not clean-data records.

Even after a reviewer action such as `ACCEPT_CANDIDATE` or `CORRECT_VALUE`, the row remains re-audit-required until a separate future explicit clean gate is designed, implemented, tested, QA-reviewed, and enabled.

## Delivery gate boundary

Future persistence must preserve delivery blocking for unresolved rows.

Rules:

- every unresolved persisted review row must carry `blocked_delivery_reason`;
- unresolved `DISAGREED`, `AMBIGUOUS`, `MISSING_EVIDENCE`, `PARSE_SKIPPED`, and `UNVERIFIED` rows block formal delivery for the affected row;
- persisted review_queue output is not a delivery export;
- no delivery file should be written by the persistence writer;
- readiness gates remain closed;
- `formal_client_export_allowed` remains false;
- `demo_export_only` remains true.

Recommended `blocked_delivery_reason` values:

```text
EVIDENCE_DISAGREEMENT_UNRESOLVED
EVIDENCE_AMBIGUITY_UNRESOLVED
EVIDENCE_MISSING_UNRESOLVED
PARSE_SKIPPED_REVIEW_REQUIRED
UNVERIFIED_REVIEW_REQUIRED
EXPLICIT_CLEAN_GATE_REQUIRED
```

## Corrected row and re-audit policy

Reviewer-corrected rows are not clean rows.

Rules:

- `CORRECT_VALUE`, `CORRECT_UNIT`, `CORRECT_PERIOD`, and `CORRECT_METRIC` must create a corrected-review state only;
- corrected rows require re-audit before any clean-data eligibility;
- future persistence may store corrected fields as review metadata, but not as delivery facts;
- re-audit must use an explicit future policy and validation task;
- if corrected values lack evidence support, they stay blocked;
- if corrected values have evidence support, they still require future clean gate review before delivery.

This prevents a human correction from bypassing the same evidence and readiness boundaries that block automated clean admission.

## Dry-run preview requirement

Before any future real write, the writer must support a dry-run preview mode.

Dry-run preview must show:

- candidate count;
- status counts;
- inserted count if committed;
- no-op duplicate count;
- conflict count;
- rejected count;
- per-record idempotency key;
- per-record action: `WOULD_INSERT`, `WOULD_SKIP_DUPLICATE`, `WOULD_FAIL_CONFLICT`, or `WOULD_REJECT`;
- blocked delivery count;
- clean_data write count, always `0`;
- delivery write count, always `0`;
- readiness gates, always closed.

No real write may occur unless dry-run preview passes and a separate future task explicitly enables a non-dry-run mode.

## Failure and fail-closed behavior

Future writer must fail closed on:

- schema mismatch;
- unknown contract version;
- missing required field;
- unexpected raw/full-source fields;
- unsupported agreement status;
- `VERIFIED` row submitted for review_queue persistence;
- opened readiness gate;
- nonzero external call count in this disabled slice;
- missing or invalid `input_file_hashes`;
- missing `audit_hash`;
- missing or oversized `evidence_preview`;
- duplicate idempotency key with different payload hash;
- any partial batch validation failure.

Batch behavior should be all-or-nothing for a real write. If any row fails validation, no rows should be committed unless a future task explicitly designs a safe partial-write mode with per-row audit manifest and rollback semantics.

## Rollback plan

Future implementation must define rollback before enabling writes.

Minimum rollback design:

- every persisted batch has `run_id`, `writer_run_id`, `contract_version`, and `batch_audit_hash`;
- all inserted rows are tagged with the same batch identifier;
- rollback by batch identifier marks rows as rolled back or deletes them only if project policy allows deletion;
- rollback must not touch `clean_data`, delivery files, evidence index, raw inputs, or adapter fixtures;
- rollback manifest records row count, idempotency keys, rollback reason, operator, timestamp, and before/after status;
- rollback itself must be dry-run previewable;
- rollback must preserve audit history if the storage backend supports immutable audit logs.

Safer default:

```text
soft rollback by setting persistence_status = ROLLED_BACK
```

rather than destructive deletion.

## Validation plan before future implementation

Before any persistence implementation, add tests proving:

- writer is disabled by default;
- real writes require explicit future flag separate from the adapter test-only token;
- dry-run preview produces no writes;
- only adapter candidate output is accepted;
- raw MinerU/Excel/parser/full source_text inputs fail closed;
- readiness gates must be closed;
- `VERIFIED` cannot be persisted as review_queue row;
- non-`VERIFIED` statuses map to review-bound persisted records;
- idempotency key is deterministic;
- retry with identical payload does not duplicate;
- duplicate key with changed payload fails closed;
- `evidence_preview` is bounded and no full text is serialized;
- `clean_data` write count is always zero;
- delivery write count is always zero;
- corrected rows remain re-audit-required;
- rollback preview and rollback execution are auditable;
- current adapter skeleton tests remain green.

Required validation for the implementation task should include targeted writer tests plus full `tests/agent`.

## Remaining risks

- No persistence backend is selected yet.
- No DB/file schema exists.
- No transaction model exists.
- No rollback implementation exists.
- No production invocation point is approved.
- Older progress/handoff docs may still contain stale pointers from earlier tasks.
- Current adapter fixtures are curated and synthetic.
- Future implementation could accidentally broaden input if it reads raw MinerU/Excel directly; this plan forbids that.
- Future implementation could accidentally serialize full source text; this plan forbids that.
- Future implementation could blur review persistence with clean delivery; this plan forbids that.

## Validation outputs

Required commands run:

```text
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
  PASS

python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
  PASS

pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
  75 passed in 0.32s

pytest tests/agent -q
  315 passed in 1.25s

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  ?? docs/agent/348N_R7BB_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE.md

git diff --stat
  no tracked diff before staging because the report is untracked

git diff --name-only
  no tracked diff before staging because the report is untracked

git diff --check
  PASS
```

## Decision

```text
Decision = 348N_R7BB_PLANNED_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_BOUNDARY_ONLY
```

R7BB defines a conservative future persistence plan only. Future review_queue persistence must be disabled by default, accept only validated adapter candidate output, persist review-bound records only, keep audit metadata and bounded previews, enforce deterministic idempotency, block unresolved delivery, never write `clean_data`, never export delivery files, and fail closed on schema/boundary mismatch.

## Recommended next task

```text
348N-R7BB-QA disabled adapter review-queue persistence planning slice review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：docs-only persistence planning slice completed; no implementation added
build_result（构建结果）= PASS：required py_compile commands passed
test_result（测试结果）= PASS：targeted adapter tests 75 passed；full tests/agent 315 passed
files_modified（修改文件数）= 1：docs/agent/348N_R7BB_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE.md
error_count（错误数）= 0
planning_result（计划结果）= PASS：future writer is disabled-by-default, adapter-output-only, dry-run-first, and fail-closed
plain_language_result（大白话说明结果）= PASS：explains this is safety planning for a future persistence button, not database implementation or production launch
record_shape_result（记录结构结果）= PASS：required/optional/forbidden fields are specified for minimal persisted review_queue records
idempotency_result（幂等设计结果）= PASS：deterministic key and duplicate/conflict behavior are defined
audit_metadata_result（审计元数据结果）= PASS：run_id, adapter_version, contract_version, input_file_hashes, review_item_id, audit_hash, and hashes are retained
evidence_boundary_result（证据边界结果）= PASS：bounded evidence_preview and hashes only; full source_text/raw artifacts forbidden
clean_data_boundary_result（clean_data边界结果）= PASS：future persistence must never write clean_data or treat VERIFIED/corrected rows as clean admission
delivery_gate_boundary_result（交付闸门边界结果）= PASS：unresolved rows retain blocked_delivery_reason and delivery gates remain closed
dry_run_preview_result（dry-run预览结果）= PASS：future writer must preview would-insert/skip/conflict/reject before any real write
rollback_plan_result（回滚计划结果）= PASS：batch-scoped rollback/soft rollback plan is defined before implementation
boundary_check（边界检查）= PASS：report-only plan; no code/tests/fixtures/output/dependencies/readiness changes
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7BB-QA disabled adapter review-queue persistence planning slice review
```
