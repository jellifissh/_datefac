# 348N-R7AF-QA source_text file-backed sidecar loader review

## Execution sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
reason = R7AF added a test-only file-backed source_text sidecar loader and fixtures. QA must verify it remains test-only, fail-closed, metadata-only, and does not create any production path or readiness boundary leak.
```

## Task Goal

Review and validate the R7AF file-backed source_text sidecar loader implementation.

Task ID:

```text
348N-R7AF-QA source_text file-backed sidecar loader review
```

This is a QA / review task.

Do not modify implementation code.

Do not modify tests.

Do not modify fixtures.

Do not run workbook reruns.

Do not run MinerU, OCR, LLM, or VLM.

Create one QA report only.

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
docs/codex_tasks/348N_R7AF_test_only_source_text_file_backed_sidecar_loader_implementation.md
docs/agent/348N_R7AE_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_DESIGN.md
docs/agent/348N_R7AD_QA_SOURCE_TEXT_FIXTURE_DRY_RUN_REVIEW.md
docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md
```

Review R7AF implementation files:

```text
tests/agent/source_text_sidecar_loader_348n.py
tests/agent/test_source_text_sidecar_loader_348n.py
tests/agent/fixtures/source_text_sidecars/r7af_source_text_sidecar__basic_positive_negative__v1.json
```

Also inspect, read-only, if useful:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tools/run_agent_excel_intake_audit_348a.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/audit/output_schema_guardrails.py
```

---

## QA Questions

Answer all questions in the report:

1. Was R7AF limited to allowed test/helper/fixture files?
2. Does the loader live only under `tests/agent/`?
3. Is there no hook into `datefac_agent/`, runner, CLI, `run_pilot(...)`, or production paths?
4. Is the sidecar format JSON object v1, not JSONL?
5. Are top-level keys exactly `schema_version`, `fixture_scope`, `records`?
6. Are record keys exactly the required R7AE keys?
7. Does `schema_version` have to be exactly `1`?
8. Does `fixture_scope` have to be exactly `test_only`?
9. Does the loader reject non-list records?
10. Does the loader reject unknown top-level keys?
11. Does the loader reject unknown record keys?
12. Does the loader reject missing required record keys?
13. Does the loader reject duplicate `source_text_id`?
14. Does the loader reject empty `source_text_id`, empty `source_document_id`, empty `locator`, empty `text_kind`, empty `text`, and empty `extraction_method`?
15. Does the loader reject missing / non-int / <= 0 `page_number`?
16. Does the loader recompute UTF-8 SHA-256 and reject hash mismatch?
17. Does the loader validate `char_count == len(text)`?
18. Does the loader reject `trusted_source = false`?
19. Does any invalid record reject the entire file with no partial records returned?
20. Does a valid sidecar map cleanly into `SourceTextEvidence` records?
21. Does a file-backed fixture drive `VERIFIED` through existing source_text wiring?
22. Does trusted numeric mismatch still produce `DISAGREED` when appropriate?
23. Do missing / source_id mismatch / page mismatch / locator mismatch cases remain `UNVERIFIED` or follow the existing conservative mismatch behavior?
24. Does evidence_index validation remain metadata/hash/count/status only, with no full `source_text`?
25. Does review_queue validation remain compact fields only, with no full `source_text`?
26. Does `VERIFIED` remain non-promotional: no STRONG_EVIDENCE, no clean admission, no readiness change?
27. Did R7AF avoid workbook reruns, MinerU, OCR, LLM, VLM, PDF extraction, and output artifacts?
28. Do all tests pass together?
29. What is the recommended next task?

---

## Expected QA Position

Be strict:

```text
file-backed sidecar loader must be test-only
fixture source_text is not production source_text
malformed files must fail closed
invalid records must not partially load
full source_text must not be serialized by default
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not imply clean admission
VERIFIED does not imply production readiness
```

If any of these are violated, mark QA as failed or needs fix.

If all are preserved, mark QA as valid.

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7AF_QA_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_REVIEW.md
```

No other file may be created or modified.

---

## Forbidden Actions

Do not modify code.

Do not modify tests.

Do not modify fixtures.

Do not modify output.

Do not modify input.

Do not modify previous reports.

Do not modify:

```text
AGENTS.md
.skills/
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/codex_tasks/
temp/
data/
legacy datefac/
dependencies
config files
```

Do not run workbook reruns.

Do not run `run_pilot(...)` or real workbook-family reruns.

Do not run MinerU, OCR, LLM, or VLM.

Do not add a PDF extraction pipeline.

Do not change MARKET_REFERENCE_ROW policy.

Do not broaden qualitative_facts admission.

Do not change output_schema_guardrails unless reporting a read-only finding.

Do not change clean_candidate_policy.

Do not change evidence_level promotion.

Do not change readiness gates.

Do not stage or commit output files.

Do not use broad Git staging.

---

## Validation Commands

Run and report:

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
python -m py_compile tests/agent/source_text_sidecar_loader_348n.py tests/agent/test_source_text_sidecar_loader_348n.py tests/agent/test_agent_excel_intake_audit_348a.py
pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

Do not run full `pytest tests -q` unless you choose to confirm historical failures.

---

## Expected Report Content

The report must include:

```text
Task ID
Task size / reasoning level used
Preflight
Files reviewed
Loader placement review
Sidecar schema review
Fail-closed review
Positive integration review
Negative behavior review
Evidence index validation review
Review queue validation review
Full source_text serialization review
Boundary policy review
Readiness gates review
Test review
Compatibility risk review
Validation outputs
Decision
Recommended next task
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
qa_result（QA结果）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should normally be:

```text
348N-R7AG single-real-MinerU-artifact adapter design
```

---

## Commit / Push Rule

If and only if:

1. exactly one QA report was created under `docs/agent/`,
2. no code/tests/fixtures/output/input/previous docs other than the allowed report were modified,
3. validation commands were run and reported,
4. `git diff --name-only` contains only the allowed report,
5. `git diff --check` is clean,

then stage exactly the report file:

```text
git add docs/agent/348N_R7AF_QA_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_REVIEW.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7AF QA review"
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
