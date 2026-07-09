# 348N-R7BM-QA review_queue persistence contract negative-path expansion review

## Task ID

```text
348N-R7BM-QA review_queue persistence contract negative-path expansion review
```

Task type: QA-review-only.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: already up to date.

git status -sb
PASS: clean after pull.

git log --oneline -40
PASS: latest history includes c54508e R7BM-QA task doc and 9daca34 R7BM negative-path expansion.
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
- `docs/codex_tasks/348N_R7BM_QA_review_queue_persistence_contract_negative_path_expansion_review.md`
- `docs/agent/348N_R7BM_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7BK_QA_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE_REVIEW.md`
- `docs/agent/348N_R7BI_QA_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md`

R7BM artifacts reviewed:

- `tests/agent/review_queue_persistence_contract_348n.py`
- `tests/agent/test_review_queue_persistence_contract_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json`
- `docs/agent/348N_R7BM_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md`

Related slices reviewed read-only:

- `tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json`
- `tests/agent/review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`

## R7BM recap

R7BM expanded the R7BL test-only in-memory persistence candidate contract with negative-path coverage for malformed previews, bypass attempts, nested forbidden fields, duplicate conflicts, hash/idempotency mismatch, evidence preview boundary failures, and hidden clean/delivery/export/production intent.

R7BM changed only:

- `tests/agent/review_queue_persistence_contract_348n.py`
- `tests/agent/test_review_queue_persistence_contract_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json`
- `docs/agent/348N_R7BM_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md`

No `datefac_agent/`, output, dependency, database, migration, repository, production hook, or readiness file was modified in the R7BM implementation commit.

## 大白话说明审查

PASS. R7BM 的大白话说明准确：这一轮不是实现真实落库，而是用坏输入、绕路输入、嵌套危险字段、重复幂等键、伪造候选、隐藏 clean/export 意图去撞测试区 persistence contract，证明坏 payload 不能变成 persistence candidate。

The explanation remains aligned with the project safety rule: uncertain or unsafe records stay review-bound; they do not become clean_data, delivery/export, production readiness, or real persistence.

## Negative-path expansion scope review

PASS. The expansion is limited to test-only contract hardening under `tests/agent/`, a small curated fixture, and the R7BM implementation report. It does not add a runner, output writer, database model, repository, migration, storage adapter, production import, external call, or formal export path.

## Contract hardening review

PASS. `tests/agent/review_queue_persistence_contract_348n.py` remains disabled by default and requires `R7BL_TEST_ONLY_PERSISTENCE_ENABLE`. Enabled execution accepts only the R7BI schema-alignment preview envelope, deep-copies accepted payloads, returns in-memory candidates only, and keeps write counters at zero.

The contract now validates schema preview hash, status counts, review-bound count, source trace exact shape, idempotency consistency, duplicate `idempotency_key`, duplicate `review_item_id`, bounded non-empty evidence preview, non-string critical fields, NaN/Infinity-like values, and clean/delivery auto-approval statuses.

## Fixture coverage review

PASS. `r7bm_persistence_contract_negative_path_fixture.json` is a small curated mutation fixture with 35 negative cases. It stores mutation descriptions and expected errors, not full DateFac output, MinerU output, PDFs, Excel workbooks, raw source text, or secrets.

Covered case groups include missing/wrong schema proof, trusted/untrusted mixing, mixed valid/invalid batch, nested raw artifacts, hidden clean/delivery/export/production intent, leaked test-only token, direct persistence candidate bypass, idempotency/hash mismatch, duplicate conflicts, evidence preview failures, bad hash shape, non-string metric/period, NaN/Infinity values, timestamp policy attempts, and reviewer status/action auto-unblock attempts.

## Nested forbidden field coverage review

PASS. Recursive validation rejects forbidden fields at any depth. Tests cover nested `source_text`, raw MinerU, raw Excel, raw parser payload, raw LLM/VLM responses, hidden clean_data intent, hidden delivery/export intent, production writer config, readiness override, output/table/DSN/path attempts, and test-only token/config leakage.

## Batch fail-closed coverage review

PASS. Mixed valid+invalid batch coverage verifies that any invalid record fails the whole batch and returns no partial `review_queue_persistence_candidate_batch`. Duplicate idempotency and duplicate review item conflicts are also fail-closed before a candidate batch can be trusted.

## Idempotency and hash consistency review

PASS. `idempotency_key` must be SHA-256-like and consistent with deterministic row identity inputs. Duplicate `idempotency_key` fails closed. Duplicate `review_item_id` with recomputed idempotency also fails closed. Input mutation after a successful call cannot mutate returned nested candidates.

## Record payload hash derivation review

PASS. `record_payload_hash` is derived inside the persistence contract from the candidate payload with the hash field excluded. Direct user-supplied persistence candidate shapes, including supplied `record_payload_hash`, remain rejected as forbidden bypasses.

## Duplicate conflict coverage review

PASS. R7BM covers both duplicate `idempotency_key` and duplicate `review_item_id` conflict classes. These cases do not produce a partial batch and do not silently deduplicate, skip, or overwrite records.

## Evidence boundary review

PASS. Evidence remains metadata-first and compact. `evidence_preview` is required, bounded by the test-only preview limit, and cannot contain nested full `source_text` or raw artifact payloads. Full source text is still forbidden from accepted input and output candidate rows.

## clean_data and delivery/export boundary review

PASS. The persistence candidate path remains non-promotional:

```text
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not auto-write clean_data
non-VERIFIED remains review-bound
persistence candidate does not trigger delivery/export
clean_data_write_count = 0
delivery_write_count = 0
export_write_count = 0
readiness_gates = CLOSED
```

Reviewer actions and review statuses that imply clean_data approval or delivery unblock are rejected.

## No-hook and no-IO boundary review

PASS. Static test coverage checks the persistence contract module for forbidden production imports and IO/DB/export/parser/model calls. Manual review found no `datefac_agent` import, database driver, file writer, Excel/CSV writer, network client, MinerU/PDF parser, OCR, LLM, VLM, runner, CLI, production hook, migration, repository, or storage implementation in the test-only contract module.

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
PASS: 76 passed in 0.42s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.18s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.15s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.12s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.23s

python -m pytest tests/agent -q
PASS: 480 passed in 1.73s

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

- This remains test-only, in-memory, and fixture-driven.
- No real review_queue persistence, database transaction, repository, migration, output writer, production runner, or production adapter is implemented.
- No real DateFac Excel, MinerU output, PDF extraction, OCR, LLM, or VLM was run.
- Duplicate conflict behavior is conservative fail-closed only; no production duplicate resolution policy exists yet.
- Project progress/handoff docs are read-only in this QA slice; R7BM-specific status is recorded in the R7BM and R7BM-QA reports.

## Decision

PASS. R7BM correctly expands negative-path coverage for the test-only review_queue persistence contract while preserving disabled-by-default, explicit-token, schema-preview-only, metadata-first, source_text-safe, no-IO, no-hook, no-clean-data, no-delivery/export, and readiness-closed boundaries.

## Recommended next task review

Recommended next task is appropriate:

```text
348N-R7BN review_queue persistence contract handoff checkpoint
```

R7BN should remain a handoff/checkpoint slice unless a future task explicitly designs and QA-approves a production persistence boundary.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BM-QA approved.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; targeted suites passed 76/29/36/24/75; full tests/agent passed 480.
files_modified（修改文件数）= 1 QA report only.
error_count（错误数）= 0.
negative_path_expansion_review_result（负路径扩展审查结果）= PASS; 35 curated negative cases cover bypass, malformed, nested forbidden, duplicate, hash, evidence, clean/delivery/export, and readiness misuse.
contract_hardening_review_result（契约加固审查结果）= PASS; disabled-by-default explicit-token contract accepts only validated R7BI schema alignment previews.
fixture_coverage_review_result（fixture覆盖审查结果）= PASS; small curated fixture only, no full outputs or raw artifacts.
nested_forbidden_field_review_result（嵌套禁止字段审查结果）= PASS; recursive forbidden-field validation covers full source_text and raw MinerU/Excel/parser/LLM/VLM/clean/export/production/readiness payloads.
batch_fail_closed_review_result（批次fail-closed审查结果）= PASS; mixed valid/invalid batch returns no partial candidate batch.
idempotency_consistency_review_result（幂等一致性审查结果）= PASS; idempotency_key shape, deterministic identity consistency, and duplicate conflicts are enforced.
record_payload_hash_review_result（record_payload_hash审查结果）= PASS; hash is derived by the contract and user-supplied direct candidate hashes are rejected.
duplicate_conflict_review_result（重复冲突审查结果）= PASS; duplicate idempotency_key and duplicate review_item_id fail closed.
evidence_boundary_review_result（证据边界审查结果）= PASS; bounded evidence_preview only, no full source_text serialization.
clean_data_boundary_review_result（clean_data边界审查结果）= PASS; no STRONG_EVIDENCE promotion and no clean_data write/admission.
delivery_export_boundary_review_result（交付导出边界审查结果）= PASS; no delivery/export trigger or unblock.
no_hook_no_io_review_result（无hook无IO审查结果）= PASS; no production hook, DB, file output, network, parser, model, MinerU, OCR, LLM, or VLM call found.
boundary_check（边界检查）= PASS; only this QA report is created.
readiness_gates（就绪门）= CLOSED.
recommended_next_task（推荐下一任务）= 348N-R7BN review_queue persistence contract handoff checkpoint.
```
