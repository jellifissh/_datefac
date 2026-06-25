# 348N-R7X-QA evidence provenance parsing review

## Task Goal

Review and validate the R7X implementation.

Task ID:

```text
348N-R7X-QA evidence provenance parsing review
```

This is a QA / review task.

It is not an implementation task unless a blocking issue is found and the task stops with a clear recommendation.

Do not modify implementation code or tests in this task.

Do not run workbook reruns.

Do not run MinerU, OCR, LLM, or VLM.

Do not create or modify output artifacts.

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
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/codex_tasks/348N_R7X_evidence_provenance_parsing_page_number_agreement_status.md
docs/agent/348N_R7W_EVIDENCE_STRENGTHENING_DESIGN_WEAK_TO_STRONG_PATH.md
docs/agent/348N_R7V_CROSS_FAMILY_CLEAN_BOUNDARY_SUMMARY_AND_READINESS_REVIEW.md
docs/agent/348N_R7U_LINYANG_ANJING_WORKBOOK_FAMILY_REGRESSION_CHECK.md
docs/agent/348N_R7T_TAIHAO_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_PILOT_RERUN.md
```

Review R7X implementation files:

```text
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

No output directory needs to be modified.

---

## QA Questions

Answer all questions in the report:

1. Does R7X parse deterministic page references from `explicit_evidence_ref` correctly?
2. Does the parser handle Chinese and English forms, including ranges?
3. Does the parser preserve raw locator text when parsing succeeds or fails?
4. Does unparseable text such as `附录A` leave `page_number = None`?
5. Is `agreement_status` added in a backward-compatible way?
6. Does `agreement_status` distinguish `MISSING` vs `UNVERIFIED`?
7. Does R7X avoid setting `VERIFIED` or `DISAGREED` without a true value-agreement checker?
8. Does explicit/page provenance with `UNVERIFIED` remain `WEAK_EVIDENCE` instead of incorrectly becoming verified `STRONG_EVIDENCE`?
9. Does workbook-row weak evidence behavior remain preserved?
10. Does `evidence_index.json` writing include `agreement_status` without requiring output artifact changes?
11. Did R7X avoid changing MARKET_REFERENCE_ROW policy?
12. Did R7X avoid broadening qualitative_facts admission?
13. Did R7X avoid changing clean-boundary / R7S scaffolding logic?
14. Did R7X avoid changing readiness gates?
15. Are the tests specific and sufficient?
16. Are there any compatibility risks from changing explicit refs from STRONG to WEAK+UNVERIFIED?
17. What should the next task be?

---

## Expected QA Position

Be strict about this distinction:

```text
page_number parsed = provenance anchor exists
agreement_status = UNVERIFIED = source-value agreement not checked yet
STRONG_EVIDENCE = should not be claimed solely from parsed page_number
```

If the implementation violates this distinction, mark QA as failed.

If the implementation preserves this distinction, mark QA as valid.

Do not propose production readiness.

Do not propose formal client export.

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
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

Do not use broad Git staging or destructive cleanup commands.

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

Do not run full `pytest tests -q` unless you choose to confirm historical failures. `pytest tests/agent -q` is sufficient for this QA task.

If `pytest tests/agent -q` fails, report the full failure and whether it is caused by R7X.

---

## Expected Report Content

The report must include:

```text
Task ID
Preflight
Files reviewed
Implementation review
Page parser review
Agreement status review
Evidence level behavior review
Evidence index writer review
Test review
Compatibility risk review
Readiness gates review
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
page_number_parsing_result（页码解析结果）=
agreement_status_result（一致性状态结果）=
strong_evidence_claim_result（强证据声明结果）=
qa_result（QA结果）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

---

## Commit / Push Rule

If and only if:

1. exactly one report was created under `docs/agent/`,
2. no code/tests/output/input/previous docs other than the allowed report were modified,
3. validation commands were run and reported,
4. `git diff --name-only` contains only the allowed report,
5. `git diff --check` is clean,

then stage exactly the report file:

```text
git add docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
```

Do not use `git add .`.

Do not use `git add -A`.

Commit:

```text
git commit -m "docs: add R7X QA review"
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
