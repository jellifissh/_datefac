# 348N-R7AC source_text sidecar fixture integration / dry-run design

## Recommended reasoning level

```text
recommended_reasoning_level = max
reason = R7AC decides how the newly implemented R7AB source_text wiring should be exercised safely with fixture sidecars or a dry-run path. This affects whether VERIFIED/DISAGREED can be tested against realistic source_text without changing production readiness or trusting unsafe workbook fields.
```

## Task Goal

Design the first safe fixture/dry-run path for R7AB source_text wiring.

Task ID:

```text
348N-R7AC source_text sidecar fixture integration / dry-run design
```

This is a design / review task, not an implementation task.

Do not modify implementation code.

Do not modify tests.

Do not run workbook reruns.

Do not run MinerU, OCR, LLM, or VLM.

Create one design report only.

---

## Background

R7AB-QA confirmed:

```text
SourceTextEvidence / SourceTextSelection contract = PASS
trusted source_text selection = PASS
checker-call-time injection = PASS
evidence_index metadata = PASS, metadata/hash only, no full source_text
review_queue compact fields = PASS, no full source_text
VERIFIED does not affect STRONG_EVIDENCE, clean admission, or readiness
readiness gates remain CLOSED
pytest tests/agent -q = 123 passed
```

R7AB implemented wiring, but it still needs a safe way to exercise that wiring with controlled source_text sidecars before any broader pipeline or real workbook rerun.

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
docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md
docs/codex_tasks/348N_R7AB_QA_source_text_availability_evidence_index_wiring_review.md
docs/codex_tasks/348N_R7AB_source_text_availability_evidence_index_wiring_implementation.md
docs/agent/348N_R7AA_SOURCE_TEXT_INTEGRATION_DESIGN_EVIDENCE_INDEX_WIRING.md
docs/agent/348N_R7Z_QA_AGREEMENT_CHECKER_EDGE_CASE_REVIEW.md
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

1. What is the safest first way to exercise R7AB source_text wiring with fixture sidecars?
2. Should the fixture sidecar be JSON, JSONL, or an in-test Python object first?
3. Where should fixture sidecars live if a future implementation creates files?
4. Should fixture sidecars be committed test fixtures or generated in tests?
5. What minimal fields must a fixture sidecar contain?
6. How should source_text_id, source_document_id, page_number, locator, text_kind, text_sha256, and trusted_source be represented?
7. Should the dry-run be performed through `tools/run_agent_excel_intake_audit_348a.py` or lower-level test helpers first?
8. How should the design avoid trusting Excel workbook raw fields as source_text?
9. How should evidence_index metadata be validated in the dry-run?
10. How should review_queue compact fields be validated in the dry-run?
11. Should output files be generated in the next implementation task, or should tests inspect in-memory rows only?
12. What should happen if fixture source_id / page_number / locator mismatches row provenance?
13. How should the design keep full source_text out of evidence_index and review_queue?
14. What are the minimum positive and negative cases for the next implementation task?
15. What is the recommended next task after R7AC?

---

## Required Design Position

The design must stay conservative:

```text
fixture source_text is not production source_text
fixture source_text must be provenance-tied
mismatch/untrusted/empty fixture source_text remains UNVERIFIED
fixture source_text must not open readiness gates
fixture VERIFIED must not imply STRONG_EVIDENCE
fixture VERIFIED must not imply clean admission
full source_text must not be serialized by default
```

Prefer a fixture-first test path before any real workbook rerun.

Do not design OCR/PDF extraction.

Do not design MinerU integration in this task.

Do not design LLM/VLM verification.

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md
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
Fixture sidecar format recommendation
Fixture location recommendation
Dry-run path recommendation
Positive fixture cases
Negative fixture cases
Evidence index validation design
Review queue validation design
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
fixture_design_result（fixture设计结果）=
dry_run_design_result（dry-run设计结果）=
evidence_index_validation_design_result（证据索引验证设计结果）=
review_queue_validation_design_result（复核队列验证设计结果）=
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
git add docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7AC source text fixture design"
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
