# 348N-R7Z-QA agreement checker edge-case review

## Recommended reasoning level

```text
recommended_reasoning_level = max
reason = R7Z changed the verified-agreement checker from set membership to multiplicity-aware matching. QA must verify the fix really reduces VERIFIED false positives without making DISAGREED too aggressive or changing clean/readiness boundaries.
```

## Task Goal

Review and validate the R7Z agreement checker edge-case fixture coverage and conservative multiplicity fix.

Task ID:

```text
348N-R7Z-QA agreement checker edge-case review
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
docs/codex_tasks/348N_R7Z_agreement_checker_edge_case_fixture_coverage.md
docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
```

Review R7Z implementation files:

```text
datefac_agent/audit/evidence_checker.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Also inspect, read-only, if useful:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/review/clean_candidate_policy.py
```

---

## QA Questions

Answer all questions in the report:

1. Did R7Z reproduce the duplicate-value false positive before the fix?
2. Does duplicate row numeric value matching now require duplicate source numeric occurrences?
3. Does one source occurrence for two identical row values stay `UNVERIFIED`?
4. Do enough duplicate source occurrences allow `VERIFIED`?
5. Does partial multi-period coverage remain `UNVERIFIED`?
6. Does source text with many unrelated numeric tokens avoid false `VERIFIED` when coverage is incomplete?
7. Does full mismatch with unrelated standalone numeric tokens remain `DISAGREED` only when no row values match?
8. Does source text with no numeric tokens remain `UNVERIFIED`?
9. Do text-only / non-numeric facts remain `UNVERIFIED`?
10. Did R7Z avoid period-aware or coordinate-aware matching changes?
11. Did R7Z avoid source_text integration into the real pipeline?
12. Did R7Z avoid mapping `VERIFIED` to `STRONG_EVIDENCE`?
13. Did R7Z avoid mapping `VERIFIED` to clean admission?
14. Did R7Z avoid opening readiness gates?
15. Did MARKET_REFERENCE_ROW policy remain unchanged?
16. Did qualitative_facts admission remain unchanged?
17. Did R7S strict-table scaffolding guard remain unchanged?
18. Do all R7X / R7Y / R7Z tests pass together?
19. Are any compatibility risks introduced by using `Counter[Decimal]` instead of set membership?
20. What is the recommended next task?

---

## Expected QA Position

Be strict about these boundaries:

```text
VERIFIED requires enough deterministic numeric evidence for every row numeric value occurrence
partial / ambiguous / no-number cases stay UNVERIFIED
DISAGREED must not be triggered by partial coverage
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not imply clean admission
VERIFIED does not imply production readiness
source_text is still not wired into the production pipeline
```

If R7Z violates any boundary, mark QA as failed or needs fix.

If R7Z preserves these boundaries, mark QA as valid.

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7Z_QA_AGREEMENT_CHECKER_EDGE_CASE_REVIEW.md
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

Do not wire source_text into the real pipeline.

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
Multiplicity fix review
Edge-case coverage review
Agreement checker behavior review
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
edge_case_coverage_result（边界用例覆盖结果）=
verified_false_positive_result（VERIFIED误判风险结果）=
disagreed_status_result（DISAGREED状态结果）=
source_text_integration_result（source_text接入结果）=
qa_result（QA结果）=
readiness_gates（就绪门）=
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
git add docs/agent/348N_R7Z_QA_AGREEMENT_CHECKER_EDGE_CASE_REVIEW.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7Z QA review"
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
