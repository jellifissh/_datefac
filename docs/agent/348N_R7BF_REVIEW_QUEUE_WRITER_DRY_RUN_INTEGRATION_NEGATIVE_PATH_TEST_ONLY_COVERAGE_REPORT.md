# 348N-R7BF review-queue writer dry-run integration negative-path test-only coverage

## Task ID

```text
348N-R7BF review-queue writer dry-run integration negative-path test-only coverage
```

## Scope

This slice expands the existing R7BE test-only dry-run integration boundary with negative-path coverage only. It keeps the boundary under `tests/agent/`, does not modify production code, does not change writer behavior, and does not commit output/dependency/readiness changes.

## Files modified

```text
tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7be_dry_run_integration_boundary_fixture.json
docs/agent/348N_R7BF_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REPORT.md
```

## Negative-path cases added

- Missing explicit integration token rejects before writer call.
- Invalid explicit integration token rejects before writer call.
- Default disabled path returns a disabled dry-run envelope and does not validate/call writer, even with malformed payload.
- Valid path constructs only the R7BC test-only writer config with the exact writer token and contract version.
- Unsafe or production-like writer preview is blocked, including production writer status, non-dry-run output, write counts, production hook flag, non-dry-run records, and `VERIFIED` writer records.
- Empty payload, minimal adapter-like payload, and direct writer-preview-like payload fail closed before writer call.

## Helper hardening

Added a test-only `_validate_writer_preview_boundary(...)` guard inside the R7BE integration boundary helper. It verifies the writer preview is still:

- `ENABLED_TEST_ONLY_DRY_RUN`;
- `dry_run_only = true`;
- closed readiness gates;
- zero external calls;
- zero clean/delivery/filesystem/database writes;
- closed boundary flags;
- review-bound dry-run records only.

Forbidden fields from the writer contract are wrapped as `ReviewQueueWriterDryRunIntegrationBoundaryError` so misuse fails at the integration boundary surface.

## Fixture updates

Added small curated malformed/minimal cases to the existing R7BE fixture:

```text
invalid_empty_payload
invalid_minimal_adapter_like_payload
invalid_direct_writer_preview_payload
```

No real PDF, MinerU output, DateFac Excel, full source text, output artifact, or production payload was added.

## Validation outputs

```text
python -m py_compile tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
  PASS

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
  36 passed in 0.17s

python -m pytest tests/agent -q
  375 passed in 1.57s
```

## Boundary check

```text
production_code_modified = false
output_files_modified = false
dependency_files_modified = false
readiness_gates_modified = false
writer_behavior_changed = false
legacy_directories_modified = false
network_database_api_side_effects_added = false
commit_performed = false
```

## Decision

```text
Decision = PASS
```

R7BF negative-path coverage confirms the test-only dry-run integration boundary remains closed when misused, rejects missing/invalid tokens before writer access, keeps disabled behavior inert, prevents production-like writer preview escape, and fails closed on malformed/minimal fixture inputs.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：negative-path test-only coverage added
build_result（构建结果）= PASS：py_compile passed
test_result（测试结果）= PASS：targeted tests 36 passed；full tests/agent 375 passed
files_modified（修改文件数）= 4
error_count（错误数）= 0
negative_path_result（负路径结果）= PASS：missing token, invalid token, disabled path, malformed/minimal inputs, and unsafe writer preview covered
writer_invocation_guard_result（writer调用防护结果）= PASS：invalid inputs rejected before writer call; valid path uses exact test-only writer config
dry_run_boundary_result（dry-run边界结果）= PASS：production-like/non-dry-run writer preview is blocked
boundary_check（边界检查）= PASS：only allowed test/report/fixture files modified; no production/output/dependency/readiness changes
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
commit_result（提交结果）= NOT_COMMITTED_BY_REQUEST
```
