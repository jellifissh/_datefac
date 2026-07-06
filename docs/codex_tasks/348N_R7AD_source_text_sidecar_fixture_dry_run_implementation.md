# 348N-R7AD source_text sidecar fixture dry-run implementation

## Recommended reasoning level

```text
recommended_reasoning_level = max
reason = R7AD implements the first controlled fixture/dry-run path for R7AB source_text wiring. It must prove the wiring works with safe in-test source_text sidecars while avoiding real workbook reruns, unsafe workbook fields, serialized full text, or readiness changes.
```

## Task Goal

Implement the first fixture-first dry-run coverage for R7AB source_text wiring.

Task ID:

```text
348N-R7AD source_text sidecar fixture dry-run implementation
```

This is an implementation + tests task.

This task should use in-test `SourceTextEvidence` objects first.

This task must not run workbook reruns.

This task must not run MinerU, OCR, LLM, or VLM.

This task must not add PDF extraction.

This task must not open readiness gates.

---

## Background

R7AC design concluded:

```text
fixture format = in-test SourceTextEvidence objects first
future fixture files = tests/agent/fixtures/source_text_sidecars/ only when loader/file contract is needed
dry-run path = lower-level helpers first, not run_pilot(...) or real workbook reruns
evidence_index validation = tempfile
review_queue validation = in-memory
full source_text must not be serialized
```

R7AB-QA confirmed:

```text
SourceTextEvidence / SourceTextSelection contract = PASS
trusted source_text selection = PASS
checker-call-time injection = PASS
evidence_index metadata = PASS, metadata/hash only, no full source_text
review_queue compact fields = PASS, no full source_text
VERIFIED does not affect STRONG_EVIDENCE, clean admission, or readiness
pytest tests/agent -q = 123 passed
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
docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md
docs/codex_tasks/348N_R7AC_source_text_sidecar_fixture_integration_dry_run_design.md
docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md
docs/codex_tasks/348N_R7AB_QA_source_text_availability_evidence_index_wiring_review.md
docs/codex_tasks/348N_R7AB_source_text_availability_evidence_index_wiring_implementation.md
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

## Required Implementation Scope

Prefer tests-only unless a small helper is clearly needed.

Use in-test `SourceTextEvidence` objects first.

Do not add JSON/JSONL fixture files unless the existing code already has a clean loader path and the change remains tiny. The preferred R7AD path is in-memory fixtures.

Do not create or commit output artifacts.

Do not call `run_pilot(...)` or perform real workbook-family reruns.

---

## Required Test Coverage

Add compact tests covering a controlled dry-run path.

### Positive cases

1. A row with explicit page provenance and a matching trusted `SourceTextEvidence` verifies numeric agreement.
2. Evidence index metadata records source_text status/id/source/page/locator/kind/hash/char_count/used flag.
3. Review queue compact fields expose agreement_status and source_text status/page/locator/reason without full source_text.
4. Full source_text does not appear in evidence_index serialization.
5. Full source_text does not appear in review_queue output/row fields.

### Negative cases

6. Missing fixture source_text keeps agreement_status `UNVERIFIED`.
7. Source id mismatch keeps agreement_status `UNVERIFIED` and source_text not used.
8. Page number mismatch keeps agreement_status `UNVERIFIED` and source_text not used.
9. Locator mismatch keeps agreement_status `UNVERIFIED` or uses the existing conservative mismatch behavior.
10. Untrusted source_text keeps agreement_status `UNVERIFIED`.
11. Empty source_text keeps agreement_status `UNVERIFIED`.
12. Numeric mismatch with trusted matching source_text can produce `DISAGREED`, but must not affect clean/readiness gates.

### Boundary cases

13. VERIFIED must not become STRONG_EVIDENCE.
14. VERIFIED must not change MARKET_REFERENCE_ROW policy.
15. VERIFIED must not change clean admission.
16. Readiness gates remain closed.
17. Existing R7X/R7Y/R7Z/R7AB tests still pass.

---

## Evidence Index Validation

Use `tempfile` or in-memory-safe temporary paths if a writer requires a file.

Required assertions:

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

---

## Review Queue Validation

Validate in memory where possible.

Required assertions:

```text
agreement_status present
source_text_status present
source_text_page_number present or empty as appropriate
source_text_locator present or empty as appropriate
source_text_unavailable_reason deterministic when not used
full source_text absent
```

If review_queue validation requires file writing and that would create output churn, do not create output artifacts. Use existing builders/helpers directly.

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

Do not run MinerU, OCR, LLM, or VLM.

Do not add PDF extraction.

Do not trust Excel raw fields as source_text.

Do not serialize full source_text by default.

Do not change MARKET_REFERENCE_ROW policy.

Do not broaden qualitative_facts admission.

Do not change clean_candidate_policy unless you stop and explain why R7AD cannot proceed otherwise.

Do not change evidence_level promotion.

Do not change readiness gates.

Do not stage or commit output files.

Do not use broad Git staging.

---

## Allowed Scope

Allowed implementation files only if necessary:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tools/run_agent_excel_intake_audit_348a.py
```

Allowed tests:

```text
tests/agent/
```

Preferred file to extend if still manageable:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
```

Do not modify docs in this task.

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

If `pytest tests/agent -q` fails, report the full failure and whether it is caused by R7AD.

Do not run full `pytest tests -q` unless you choose to confirm historical failures.

---

## Expected Output

Final execution report must include:

```text
Recommended reasoning level used
Preflight
Files modified
Fixture dry-run implementation summary
Positive cases covered
Negative cases covered
Evidence index validation summary
Review queue validation summary
Full source_text serialization check
Boundary checks
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
fixture_dry_run_result（fixture dry-run结果）=
evidence_index_validation_result（证据索引验证结果）=
review_queue_validation_result（复核队列验证结果）=
full_text_serialization_result（全文序列化结果）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

---

## Commit / Push Rule

If and only if:

1. only allowed implementation/test files were modified,
2. validation commands were run and reported,
3. `git diff --name-only` contains only allowed implementation/test files,
4. `git diff --check` is clean,
5. no output/input/temp/data/legacy/config/docs files were modified,

then stage only exact modified files with explicit path staging.

Do not use broad staging commands.

Suggested commit message:

```text
test: add source text fixture dry-run coverage
```

If tiny implementation helper changes were required:

```text
test: add source text fixture dry-run coverage
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
