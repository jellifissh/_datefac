# 348N-R7BM review_queue persistence contract negative-path expansion test-only

## Task ID

```text
348N-R7BM review_queue persistence contract negative-path expansion test-only
```

Task type: test-only-negative-path-expansion.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
WARN: first attempts failed due transient GitHub/network reset and timeout.

git -c http.version=HTTP/1.1 pull --ff-only origin pivot/348-agent-foundation
PASS: fast-forward 7713db4..317d5e8; R7BM task doc added.

git status -sb
PASS: clean after successful pull.

git log --oneline -40
PASS: latest commits include 317d5e8 R7BM task doc and 7713db4 R7BL-QA.
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
- `docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7BK_QA_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE_REVIEW.md`
- `docs/agent/348N_R7BI_QA_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md`

R7BL files reviewed and modified where allowed:

- `tests/agent/review_queue_persistence_contract_348n.py`
- `tests/agent/test_review_queue_persistence_contract_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json` read-only
- `tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json`

Related slices reviewed read-only:

- `tests/agent/review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`

## R7BL-QA recap

R7BL-QA confirmed the persistence contract prototype is safe, conservative, test-only, disabled by default, explicit-token gated, metadata-first, source_text-safe, clean_data-safe, delivery/export-safe, no-hook, no-IO, and readiness-closed.

R7BM therefore expands misuse coverage only. It does not add real persistence, database models, repositories, migrations, runners, exports, production hooks, or readiness changes.

## 大白话说明

这一轮继续补防线：用坏输入、绕路输入、嵌套脏字段、重复幂等键、伪造候选、隐藏 clean/export 意图去撞 R7BL 的“模拟落库前最后一道闸”。目标不是新增产品行为，而是证明坏 payload 不能变成 persistence candidate。

## Negative-path expansion scope

Implemented/updated files:

- `tests/agent/review_queue_persistence_contract_348n.py`
- `tests/agent/test_review_queue_persistence_contract_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json`
- `docs/agent/348N_R7BM_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md`

No `datefac_agent/`, output, dependency, migration, database, production, or readiness files were modified.

## Contract hardening changes

R7BM hardens the test-only contract with additional fail-closed validation:

- verifies `schema_alignment_preview_hash`;
- verifies schema alignment `status_counts` and `review_bound_record_count`;
- rejects duplicate `review_item_id`;
- rejects duplicate `idempotency_key` before candidate construction;
- verifies `idempotency_key` is consistent with row payload;
- enforces compact exact `source_trace` fields;
- rejects non-string key candidate fields such as `metric_name`, `period`, and `candidate_value`;
- rejects NaN/Infinity-like candidate values;
- rejects empty `evidence_preview`;
- rejects reviewer actions or statuses that imply clean_data approval or delivery unblock;
- expands nested forbidden keys for hidden persistence destination, DSN, table, output path, raw MinerU/Excel/parser/LLM/VLM, clean_data, delivery, export, and production config intent.

The contract still produces only in-memory candidate batches and still performs no IO.

## Fixture coverage

New curated fixture:

```text
tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json
```

The fixture stores small mutation descriptions only. It contains no real PDF, no DateFac Excel, no MinerU output, no long source text, and no secrets.

Covered case groups include:

- wrong/missing schema alignment proof;
- wrong contract/schema version;
- mixed trusted/untrusted rows;
- valid+invalid mixed batch;
- nested forbidden raw payloads;
- hidden clean/delivery/export/production intent;
- leaked test-only token;
- direct persistence candidate bypass;
- idempotency/hash mismatch and duplicates;
- missing/invalid evidence preview;
- bad input hash shape;
- non-string metric/period/value;
- NaN/Infinity-like values;
- persistence destination/table/DSN/path attempts;
- timestamp policy attempts;
- reviewer action/review status auto-approval attempts.

## Nested forbidden field coverage

PASS. Recursive validation rejects forbidden fields at arbitrary depth. R7BM tests cover:

- `source_text` nested under `evidence_preview`;
- `raw_mineru` nested under `source_trace`;
- `raw_excel` nested under metadata;
- `raw_parser_payload` nested under audit-like metadata;
- `raw_llm_response` and `raw_vlm_response`;
- hidden `clean_data_write_intent`;
- hidden `delivery_export_intent`;
- hidden `production_writer_config`;
- hidden readiness override.

## Batch fail-closed coverage

PASS. R7BM proves a mixed valid+invalid record batch fails as a whole and returns no partial candidate batch.

The prior duplicate-idempotency fail-closed behavior remains covered, and all invalid R7BM mutations raise `ReviewQueuePersistenceContractError`.

## Idempotency and hash consistency coverage

PASS. R7BM adds stricter checks that:

- `idempotency_key` must be SHA-256-like;
- `idempotency_key` must match deterministic row identity inputs;
- duplicate `idempotency_key` fails closed;
- duplicate `review_item_id` fails closed even with a different idempotency key;
- `schema_alignment_preview_hash` must match the records/status counts;
- `record_payload_hash` is derived by the persistence contract, not accepted from direct candidate bypasses;
- derived candidate `record_payload_hash` remains deterministic.

## Evidence boundary coverage

PASS. R7BM keeps bounded evidence previews while rejecting:

- empty evidence preview;
- oversized evidence preview;
- full source text nested under evidence preview;
- raw evidence artifacts nested elsewhere.

Full `source_text` remains forbidden, and candidate rows remain compact metadata-first records.

## clean_data and delivery/export boundary coverage

PASS. R7BM rejects:

- hidden clean_data write intent;
- hidden delivery/export intent;
- reviewer action implying auto-approval to clean_data;
- review status implying delivery unblock;
- production writer config.

The existing safety rules remain intact:

```text
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not auto-write clean_data
non-VERIFIED remains review-bound
candidate does not trigger delivery/export
readiness gates remain CLOSED
```

## No-hook and no-IO boundary

PASS. R7BM stays under `tests/agent/`. Static AST coverage still checks the persistence contract module for forbidden production imports and IO/DB/export/parser/model hooks.

No database model, repository class, migration, storage code, output writer, runner, production hook, MinerU/OCR/LLM/VLM call, or real extraction was added.

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
PASS: 76 passed in 0.43s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.19s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.16s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.13s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.43s

python -m pytest tests/agent -q
PASS: 480 passed in 3.04s

git status -sb
PASS: only allowed R7BM files changed/untracked before report finalization.

git diff --stat
PASS: code/test diff limited to R7BM allowed files before report finalization.

git diff --name-only
PASS: code/test diff limited to R7BM allowed files before report finalization.

git diff --check
PASS: no whitespace errors reported.
```

## Limitations

- This remains test-only and in-memory.
- No real database transaction or storage write exists.
- No production persistence implementation exists.
- The expanded fixture uses synthetic curated mutations, not full real R7AO output.
- Real persistence still requires separate design, implementation, rollback planning, and QA before any production boundary can open.

## Decision

PASS. R7BM expands negative-path coverage and hardens the test-only persistence contract. Bad payloads, hidden intents, nested raw artifacts, inconsistent idempotency/hash identities, duplicate identities, unbounded evidence, direct candidate bypasses, and clean/delivery/readiness misuse all fail closed without partial candidate output or side effects.

## Recommended next task

```text
348N-R7BM-QA review_queue persistence contract negative-path expansion review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BM negative-path expansion implemented.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; R7BM/R7BL persistence contract tests 76 passed; full tests/agent 480 passed.
files_modified（修改文件数）= 4 allowed files.
error_count（错误数）= 0.
negative_path_expansion_result（负路径扩展结果）= PASS; expanded malformed/bypass/nested-intent/idempotency/hash/evidence/status tests.
contract_hardening_result（契约加固结果）= PASS; schema preview hash, source_trace, idempotency consistency, duplicate review_item_id, NaN/Infinity, and auto-clean/delivery statuses fail closed.
fixture_coverage_result（fixture覆盖结果）= PASS; new small curated R7BM fixture covers 35 negative cases.
nested_forbidden_field_result（嵌套禁止字段结果）= PASS; nested source_text/raw MinerU/raw Excel/raw parser/raw LLM/VLM/clean/delivery/production/readiness attempts rejected.
batch_fail_closed_result（批次fail-closed结果）= PASS; valid+invalid mixed batch returns no partial candidate batch.
idempotency_consistency_result（幂等一致性结果）= PASS; inconsistent or duplicate idempotency keys fail closed.
record_payload_hash_result（record_payload_hash结果）= PASS; hashes are derived deterministically; direct user-supplied candidate hash bypass rejected.
evidence_boundary_result（证据边界结果）= PASS; empty/oversized/full-source nested evidence rejected; bounded preview remains allowed.
clean_data_boundary_result（clean_data边界结果）= PASS; clean_data intent and auto-clean reviewer actions rejected.
delivery_export_boundary_result（交付导出边界结果）= PASS; delivery/export intent and delivery-unblock statuses rejected.
no_hook_no_io_result（无hook无IO结果）= PASS; no IO/DB/export/parser/model/MinerU/OCR/VLM/production hook added.
boundary_check（边界检查）= PASS; only allowed R7BM test-only files/report changed.
readiness_gates（就绪门）= CLOSED.
recommended_next_task（推荐下一任务）= 348N-R7BM-QA review_queue persistence contract negative-path expansion review.
```
