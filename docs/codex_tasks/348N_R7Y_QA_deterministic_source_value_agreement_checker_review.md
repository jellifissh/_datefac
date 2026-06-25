# 348N-R7Y-QA deterministic source-value agreement checker review

## Recommended reasoning level

```text
recommended_reasoning_level = max
reason = This QA reviews VERIFIED / DISAGREED evidence-agreement semantics. A false pass would make future evidence_strength and readiness interpretation unsafe.
```

## Task Goal

Review and validate the R7Y implementation.

Task ID:

```text
348N-R7Y-QA deterministic source-value agreement checker review
```

This is a QA / review task.

Do not modify implementation code.

Do not modify tests.

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

Read these files:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/codex_tasks/348N_R7Y_deterministic_source_value_agreement_checker.md
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
docs/agent/348N_R7W_EVIDENCE_STRENGTHENING_DESIGN_WEAK_TO_STRONG_PATH.md
```

Review R7Y implementation files:

```text
datefac_agent/audit/evidence_checker.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Also inspect, read-only, if needed:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/review/clean_candidate_policy.py
```

---

## QA Questions

Answer all questions in the report:

1. Does `classify_agreement_status(row, evidence_refs, source_text=None)` keep no provenance as `MISSING`?
2. Does explicit/page provenance without source text remain `UNVERIFIED`?
3. Does exact numeric source-text match become `VERIFIED`?
4. Does comma-formatted numeric equivalence become `VERIFIED`?
5. Does percentage equivalence such as `12.30%` vs `12.3%` become `VERIFIED` without converting to `0.123`?
6. Does parenthesized negative equivalence such as `(123)` vs `-123` become `VERIFIED`?
7. Does numeric mismatch become `DISAGREED` only when deterministic comparison proves mismatch?
8. Does partial multi-period coverage remain conservative, preferably `UNVERIFIED`?
9. Do text-only / non-numeric facts remain `UNVERIFIED`, not `VERIFIED`?
10. Does the production pipeline still remain `UNVERIFIED` unless source text is supplied?
11. Does `VERIFIED` not automatically become `STRONG_EVIDENCE`?
12. Does `VERIFIED` not automatically enter clean_data?
13. Does `VERIFIED` not open readiness gates?
14. Does MARKET_REFERENCE_ROW policy remain unchanged?
15. Does qualitative_facts admission remain unchanged?
16. Does R7S strict-table scaffolding guard remain unchanged?
17. Do tests cover R7X parser behavior and R7S clean-boundary behavior after R7Y?
18. Are there any unsafe numeric-normalization false-positive risks?
19. Are there any compatibility risks from introducing `VERIFIED` / `DISAGREED` values?
20. What is the recommended next task?

---

## Expected QA Position

Be strict about these boundaries:

```text
VERIFIED = deterministic numeric source-value match, not plausibility
DISAGREED = deterministic mismatch, not partial absence
partial coverage = conservative, usually UNVERIFIED
text-valued facts = UNVERIFIED unless a future text agreement checker exists
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not imply clean admission
VERIFIED does not imply production readiness
```

If R7Y violates any of these boundaries, mark QA as failed or needs fix.

If R7Y preserves them, mark QA as valid.

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md
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
Agreement checker review
Numeric normalization review
Evidence level behavior review
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
agreement_checker_result（一致性检查器结果）=
verified_status_result（VERIFIED状态结果）=
disagreed_status_result（DISAGREED状态结果）=
strong_evidence_claim_result（强证据声明结果）=
readiness_gates（就绪门）=
qa_result（QA结果）=
recommended_next_task（推荐下一任务）=
```

---

## Commit / Push Rule

If and only if:

1. exactly one QA report was created under `docs/agent/`,
2. no code/tests/output/input/previous docs other than the allowed report were modified,
3. validation commands were run and reported,
4. `git diff --name-only` contains only the allowed report,
5. `git diff --check` is clean,

then stage exactly the report file:

```text
git add docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7Y QA review"
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
