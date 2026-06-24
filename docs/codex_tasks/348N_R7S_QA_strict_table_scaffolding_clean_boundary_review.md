# 348N-R7S-QA strict_table scaffolding clean-boundary review

## Task Goal

Review and validate the pushed R7S implementation.

Task ID:

```text
348N-R7S-QA strict_table scaffolding clean-boundary review
```

This is a QA / review task.

It is not an implementation task unless the QA finds a blocking issue and stops with a clear recommendation.

It is not a Taihao output rerun task.

Do not run a new workbook pilot.

Do not modify code or tests in this task.

Create one QA report only.

---

## Required Preflight

Run and report:

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -8
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
docs/codex_tasks/348N_R7S_strict_table_pseudo_header_comparison_row_clean_boundary_implementation.md
docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md
docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md
```

Review these implementation files:

```text
datefac_agent/review/clean_candidate_policy.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Allowed read-only output references:

```text
output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/agent_excel_intake_audit_348a_manifest.json
output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/clean_data.csv
output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/review_queue.csv
output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/evidence_index.json
```

Do not modify output files.

---

## QA Questions

Answer all questions in the report:

1. Does R7S implement the R7R recommendation as a narrower clean-candidate policy, not a new row type?
2. Does the guard apply only to weak-evidence strict-table rows that would otherwise enter clean_data?
3. Does the guard route scaffolding / pseudo-header / comparison-dimension rows to `REVIEW_REQUIRED`?
4. Does it preserve normal numeric financial fact rows as clean candidates under the existing policy?
5. Does it preserve mixed numeric rows such as rows with dash plus numeric values?
6. Does it preserve `MARKET_REFERENCE_ROW` behavior?
7. Does it preserve qualitative_facts behavior?
8. Does it avoid changes to row_type_classifier and output_schema_guardrails?
9. Are tests specific enough and not over-broad?
10. Are there any false-positive risks, especially for text-valued financial facts?
11. Is a Taihao pilot rerun recommended as a later separate task?

---

## Allowed Scope

This task may create exactly one report:

```text
docs/agent/348N_R7S_QA_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_REVIEW.md
```

No other file may be created or modified.

---

## Forbidden Actions

Do not modify code.

Do not modify tests.

Do not modify docs except for the single allowed QA report.

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

Do not run MinerU, OCR, LLM, VLM, a new extraction pipeline, or a new workbook pilot.

Do not change readiness gates.

Do not change MARKET_REFERENCE_ROW policy.

Do not broaden qualitative_facts admission.

Do not use broad Git staging or destructive cleanup commands.

---

## Validation Commands

Run and report:

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
pytest tests/agent -q
pytest tests -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

If full `pytest tests -q` fails because of known unrelated legacy failures, report:

1. failure count,
2. failing areas,
3. why they are unrelated to R7S,
4. whether `pytest tests/agent -q` passed.

Do not fix unrelated tests in this task.

---

## Expected Report Content

The QA report must include:

```text
Task ID
Preflight
Files reviewed
Implementation review
Test review
Validation outputs
Policy boundary review
Risk review
Decision
Recommended next task
Data Result / 数据结果
```

The Data Result section must include:

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
boundary_check（边界检查）=
qa_result（QA结果）=
recommended_next_task（推荐下一任务）=
```

---

## Commit / Push Rule

If and only if:

1. only the allowed QA report was created,
2. validation was run and reported,
3. `git diff --name-only` contains only the QA report,
4. `git diff --check` is clean,

then stage exactly this file:

```text
git add docs/agent/348N_R7S_QA_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_REVIEW.md
```

Do not use `git add .`.

Do not use `git add -A`.

Commit:

```text
git commit -m "docs: add R7S QA review"
```

Push:

```text
git push origin pivot/348-agent-foundation
```

Post-push validation:

```text
git status -sb
git log --oneline -8
```

Expected final state:

```text
## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
```

No `M`, no `??`, no `[ahead 1]`.

Stop after push. Do not start the Taihao rerun task.
