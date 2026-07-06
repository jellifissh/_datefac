# 348N-R7AE source_text file-backed sidecar loader design

## Recommended reasoning level

```text
recommended_reasoning_level = max
reason = R7AE designs the first file-backed source_text sidecar loader after R7AD fixture dry-run QA. A bad loader contract could turn fixture-only evidence into unsafe production-like evidence, serialize full text, or weaken provenance binding.
```

## Task Goal

Design the first file-backed source_text sidecar loader contract.

Task ID:

```text
348N-R7AE source_text file-backed sidecar loader design
```

This is a design / review task, not an implementation task.

Do not modify implementation code.

Do not modify tests.

Do not run workbook reruns.

Do not run MinerU, OCR, LLM, or VLM.

Create one design report only.

---

## Background

R7AD-QA confirmed:

```text
R7AD fixture dry-run is valid
R7AD is tests-only and uses in-test SourceTextEvidence
trusted fixture source_text can VERIFIED
trusted numeric mismatch can DISAGREED
missing / source_id mismatch / page mismatch / locator mismatch / untrusted / empty -> UNVERIFIED
evidence_index writes metadata/hash/count/status only, no full source_text
review_queue compact fields exclude full source_text
readiness gates remain CLOSED
pytest tests/agent -q = 134 passed
```

R7AE should design the next narrow step: a file-backed fixture/sidecar loader that remains test/demo-safe and provenance-bound.

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
docs/agent/348N_R7AD_QA_SOURCE_TEXT_FIXTURE_DRY_RUN_REVIEW.md
docs/codex_tasks/348N_R7AD_QA_source_text_fixture_dry_run_review.md
docs/codex_tasks/348N_R7AD_source_text_sidecar_fixture_dry_run_implementation.md
docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md
docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md
```

Inspect current implementation read-only:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
tests/agent/conftest.py
```

---

## Design Questions To Answer

The report must answer:

1. Should the first file-backed sidecar format be JSON or JSONL?
2. What exact schema should the sidecar file use?
3. Which fields are required vs optional?
4. Where should committed test fixtures live?
5. Should the loader be test-only first or production-code reachable?
6. How should the loader reject unknown fields, missing fields, duplicate ids, invalid page numbers, empty text, untrusted records, and locator mismatches?
7. How should `text_sha256` be calculated and validated?
8. Should sidecar files contain full source_text, or should text be referenced through a second file? If full text is allowed for tests, how is it prevented from being serialized to evidence_index/review_queue?
9. How should file-backed sidecars map into `SourceTextEvidence` records?
10. How should source_document_id be tied to EvidenceRef.source_id?
11. Should the loader be connected to `tools/run_agent_excel_intake_audit_348a.py` in the first implementation slice, or only tests?
12. What positive and negative tests should the loader implementation require?
13. What evidence_index and review_queue assertions should remain mandatory?
14. What must remain out of scope for the first loader implementation?
15. What is the recommended next task after R7AE?

---

## Required Design Position

The design must stay conservative:

```text
file-backed sidecar source_text is still not production source_text
sidecar records must be provenance-tied
unknown or malformed sidecar records must fail closed
missing / mismatch / untrusted / empty sidecar source_text remains UNVERIFIED
full source_text must not be serialized to evidence_index or review_queue
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not imply clean admission
VERIFIED does not imply production readiness
```

Prefer a test-only loader implementation first unless the current code already has a narrow safe CLI hook.

Do not design OCR/PDF extraction.

Do not design MinerU integration.

Do not design LLM/VLM verification.

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7AE_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_DESIGN.md
```

No other file may be created or modified.

---

## Forbidden Actions

Do not modify code.

Do not modify tests.

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

Do not run MinerU, OCR, LLM, or VLM.

Do not add a PDF extraction pipeline.

Do not change MARKET_REFERENCE_ROW policy.

Do not broaden qualitative_facts admission.

Do not change output_schema_guardrails.

Do not change readiness gates.

Do not stage or commit output files.

Do not use broad Git staging.

---

## Validation Commands

Run and report:

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
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
Recommended reasoning level used
Preflight
Files reviewed
Sidecar format recommendation
Sidecar schema recommendation
Fixture location recommendation
Loader placement recommendation
Validation and fail-closed rules
Hash and text handling design
Integration boundary design
Positive loader cases
Negative loader cases
Evidence index / review queue validation design
Out-of-scope list
Risk review
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
sidecar_format_result（sidecar格式结果）=
loader_design_result（loader设计结果）=
fail_closed_design_result（失败关闭设计结果）=
evidence_index_review_queue_design_result（证据索引/复核队列设计结果）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

---

## Commit / Push Rule

If and only if:

1. exactly one design report was created under `docs/agent/`,
2. no code/tests/output/input/previous docs other than the allowed report were modified,
3. validation commands were run and reported,
4. `git diff --name-only` contains only the allowed report,
5. `git diff --check` is clean,

then stage exactly the report file:

```text
git add docs/agent/348N_R7AE_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_DESIGN.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7AE source text loader design"
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
