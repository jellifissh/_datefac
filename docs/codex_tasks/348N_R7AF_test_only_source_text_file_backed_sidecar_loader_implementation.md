# 348N-R7AF test-only source_text file-backed sidecar loader implementation

## Execution sizing

```text
task_size = large
recommended_reasoning_level = max
execution_mode = phased-hard-stop + implementation-with-self-QA
reason = R7AF implements the first file-backed source_text sidecar loader. It should move faster than the prior design-only tasks, but it still needs strict phase boundaries because loader mistakes can make unsafe sidecar text look like trusted evidence.
```

## Task Goal

Implement the first test-only file-backed source_text sidecar loader, with committed JSON fixture(s), tests, and self-QA checks.

Task ID:

```text
348N-R7AF test-only source_text file-backed sidecar loader implementation
```

This is an implementation + tests + self-QA task.

The implementation must stay test-only first.

Do not connect the loader to production paths, `run_pilot(...)`, real workbook reruns, CLI, or runner defaults.

Do not run MinerU, OCR, LLM, or VLM.

Do not add PDF extraction.

Do not open readiness gates.

---

## Background

R7AE design concluded:

```text
sidecar format = JSON object v1, not JSONL
schema = schema_version + fixture_scope=test_only + records[]
strict required fields, no unknown keys
fixture location = tests/agent/fixtures/source_text_sidecars/
loader placement = test-only first
fail-closed = malformed/unsafe/hash mismatch/duplicate/unsupported fields reject with no partial records
hash/text = recompute UTF-8 SHA-256, validate char_count, keep full text test-only
evidence_index/review_queue remain metadata-only, no full source_text
readiness gates remain CLOSED
```

R7AD-QA confirmed:

```text
R7AD in-memory fixture dry-run is valid
trusted fixture source_text can VERIFIED
trusted numeric mismatch can DISAGREED
missing / source_id mismatch / page mismatch / locator mismatch / untrusted / empty -> UNVERIFIED
evidence_index metadata-only, no full source_text
review_queue compact fields exclude full source_text
pytest tests/agent -q = 134 passed
```

---

## Required Preflight

Run and report:

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -12
```

If the worktree is not clean after pull, stop and report.

---

## Required Read Order

Read these files first:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348N_R7AE_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_DESIGN.md
docs/codex_tasks/348N_R7AE_source_text_file_backed_sidecar_loader_design.md
docs/agent/348N_R7AD_QA_SOURCE_TEXT_FIXTURE_DRY_RUN_REVIEW.md
docs/codex_tasks/348N_R7AD_source_text_sidecar_fixture_dry_run_implementation.md
docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md
```

Inspect implementation before editing:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
tests/agent/conftest.py
```

Also inspect, read-only if useful:

```text
datefac_agent/intake/excel_intake.py
datefac_agent/audit/output_schema_guardrails.py
datefac_agent/review/clean_candidate_policy.py
```

---

## Phase Rules

This is a larger task, but it must still stop at checkpoints internally.

### Phase 1: Plan

Write a short internal implementation plan before editing.

The plan must answer:

```text
Where will the test-only loader live?
Which JSON fixture file(s) will be created?
Which tests will validate valid loading?
Which tests will validate fail-closed behavior?
Which tests will validate evidence_index/review_queue metadata-only behavior?
```

If any required boundary cannot be preserved, stop and report.

### Phase 2: Implement test-only loader and fixture(s)

Preferred loader placement:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
```

If that file becomes too large, a small test-only helper is allowed under:

```text
tests/agent/source_text_sidecar_loader_348n.py
```

Do not put loader code under `datefac_agent/` in this task unless you stop and explain why test-only placement is impossible.

Preferred fixture location:

```text
tests/agent/fixtures/source_text_sidecars/
```

Create at least one valid JSON fixture file.

Do not create output artifacts.

### Phase 3: Tests

Add compact tests for valid loading, fail-closed behavior, and integration with existing source_text wiring.

### Phase 4: Validation and self-QA

Run all validation commands and include a self-QA section in the final report.

Do not begin any real workbook dry-run or production integration.

---

## Required JSON Sidecar Format

Use JSON object v1:

```json
{
  "schema_version": 1,
  "fixture_scope": "test_only",
  "records": [
    {
      "source_text_id": "st-valid-001",
      "source_document_id": "source-pdf-001",
      "page_number": 3,
      "locator": "p3:table:row:revenue",
      "text_kind": "table_row",
      "text": "Revenue 2023 123.45",
      "text_sha256": "<sha256-of-utf8-text>",
      "char_count": 19,
      "trusted_source": true,
      "extraction_method": "fixture_manual"
    }
  ]
}
```

Required top-level keys, exactly:

```text
schema_version
fixture_scope
records
```

Required record keys, exactly:

```text
source_text_id
source_document_id
page_number
locator
text_kind
text
text_sha256
char_count
trusted_source
extraction_method
```

No unknown top-level keys.

No unknown record keys.

`schema_version` must be exactly `1`.

`fixture_scope` must be exactly `test_only`.

`records` must be a list.

Each record must map to `SourceTextEvidence`.

---

## Fail-Closed Loader Rules

The loader must reject the entire sidecar file with a clear deterministic exception/message if any record is invalid.

Do not return partial records.

Reject:

```text
invalid JSON
non-object top-level JSON
missing top-level keys
unknown top-level keys
schema_version != 1
fixture_scope != test_only
records not a list
missing record keys
unknown record keys
duplicate source_text_id
source_text_id empty
source_document_id empty
page_number missing / non-int / <= 0
locator empty
text_kind empty
text empty
text_sha256 missing or not matching recomputed UTF-8 SHA-256
char_count missing or not equal to len(text)
trusted_source is not true
extraction_method empty
```

Important: for this first file-backed loader, `trusted_source` must be `true`; untrusted file-backed records should fail closed instead of being loaded.

Existing in-memory tests already cover untrusted `SourceTextEvidence` selection behavior.

---

## Required Test Coverage

### Loader-positive tests

1. Valid JSON sidecar loads into `SourceTextEvidence` records.
2. Loaded record preserves `source_text_id`, `source_document_id`, page, locator, kind, text, hash, char_count, trusted flag, and extraction method.
3. Loaded valid fixture can be used by existing source_text selection and agreement checker to produce `VERIFIED`.

### Integration-positive tests

4. File-backed loaded fixture drives evidence_index metadata through tempfile validation.
5. File-backed loaded fixture drives review_queue compact fields through in-memory validation.
6. evidence_index output contains metadata/hash/count/status/used flag, not full source_text.
7. review_queue output contains compact fields, not full source_text.

### Fail-closed negative tests

8. Unknown top-level key rejects entire file.
9. Unknown record key rejects entire file.
10. Missing required record key rejects entire file.
11. Duplicate `source_text_id` rejects entire file.
12. `schema_version` not 1 rejects entire file.
13. `fixture_scope` not `test_only` rejects entire file.
14. Invalid page_number rejects entire file.
15. Empty text rejects entire file.
16. Hash mismatch rejects entire file.
17. char_count mismatch rejects entire file.
18. `trusted_source = false` rejects entire file.

### Existing wiring regressions

19. Missing source_text still leads to `UNVERIFIED`.
20. source_id/page/locator mismatch still leads to `UNVERIFIED` or the existing conservative mismatch behavior.
21. trusted numeric mismatch can still be `DISAGREED`.
22. `VERIFIED` still does not become `STRONG_EVIDENCE`.
23. `VERIFIED` still does not change clean admission.
24. readiness gates remain closed.
25. Existing tests still pass.

---

## Evidence Index and Review Queue Requirements

Evidence index assertions must confirm:

```text
source_text_status present
source_text_id present when used
source_text_source_id present when used
source_text_page_number present when used
source_text_locator present when available
source_text_kind present when used
source_text_sha256 present when used
source_text_char_count present when used
source_text_used_for_agreement true only when used
source_text_unavailable_reason deterministic when not used
full source_text absent
```

Review queue assertions must confirm:

```text
agreement_status present
source_text_status present
source_text_page_number present or empty as appropriate
source_text_locator present or empty as appropriate
source_text_unavailable_reason deterministic when not used
full source_text absent
```

---

## Forbidden Actions

Do not modify:

```text
AGENTS.md
.skills/
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/codex_tasks/
input/
output/
temp/
data/
legacy datefac/
dependencies
config files
```

Do not run workbook reruns.

Do not run `run_pilot(...)` or real workbook-family reruns.

Do not run MinerU, OCR, LLM, or VLM.

Do not add PDF extraction.

Do not trust Excel raw fields as source_text.

Do not serialize full source_text to evidence_index or review_queue.

Do not connect the sidecar loader to production code paths.

Do not add CLI/runner defaults.

Do not change MARKET_REFERENCE_ROW policy.

Do not broaden qualitative_facts admission.

Do not change clean_candidate_policy unless you stop and explain why R7AF cannot proceed otherwise.

Do not change evidence_level promotion.

Do not change readiness gates.

Do not stage or commit output files.

Do not use broad Git staging.

---

## Allowed Scope

Allowed test/helper files:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
tests/agent/source_text_sidecar_loader_348n.py
tests/agent/fixtures/source_text_sidecars/*.json
```

If a new test file is cleaner, allowed:

```text
tests/agent/test_source_text_sidecar_loader_348n.py
```

Prefer tests-only. Do not modify production files unless impossible.

Do not modify docs in this task.

---

## Validation Commands

Run and report:

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
python -m py_compile tests/agent/test_agent_excel_intake_audit_348a.py
pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

If `pytest tests/agent -q` fails, report the full failure and whether it is caused by R7AF.

Do not run full `pytest tests -q` unless you choose to confirm historical failures.

---

## Expected Final Report

Final execution report must include:

```text
Recommended reasoning level used
Task size and execution mode used
Preflight
Files modified
Loader placement summary
Fixture files created
JSON sidecar schema implemented
Fail-closed behavior implemented
Positive loader cases covered
Negative loader cases covered
Evidence index validation summary
Review queue validation summary
Full source_text serialization check
Boundary checks
Self-QA checklist result
Validation outputs
Commit hash
Push result
Final git status
Data Result / 数据结果
```

Data Result must include:

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
boundary_check（边界检查）=
sidecar_loader_result（sidecar loader结果）=
fail_closed_result（失败关闭结果）=
evidence_index_validation_result（证据索引验证结果）=
review_queue_validation_result（复核队列验证结果）=
full_text_serialization_result（全文序列化结果）=
self_qa_result（自检结果）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should normally be:

```text
348N-R7AF-QA source_text file-backed sidecar loader review
```

---

## Commit / Push Rule

If and only if:

1. only allowed test/helper/fixture files were modified,
2. validation commands were run and reported,
3. `git diff --name-only` contains only allowed test/helper/fixture files,
4. `git diff --check` is clean,
5. no output/input/temp/data/legacy/config/docs/production files were modified,

then stage only exact modified files with explicit path staging.

Do not use broad staging commands.

Suggested commit message:

```text
test: add source text sidecar loader coverage
```

Push:

```text
git push origin pivot/348-agent-foundation
```

Post-push validation:

```text
git status -sb
git log --oneline -10
```

Stop after push. Do not start the next task.
