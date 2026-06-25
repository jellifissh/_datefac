# 348N-R7U Linyang / Anjing workbook family regression check

## Task Goal

Run a controlled regression check after R7S and R7T to verify that the strict-table scaffolding clean-boundary guard did not regress prior workbook families.

Task ID:

```text
348N-R7U Linyang / Anjing workbook family regression check
```

This is a regression validation / rerun / result-report task.

It is not an implementation task.

Do not modify code or tests.

Do not run MinerU, OCR, LLM, or VLM.

Do not run a new PDF extraction pipeline beyond the existing local Excel-intake audit runner pattern already used by R7T.

Use existing local input files and existing local runner/tooling documented in the repository.

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
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/codex_tasks/348N_R7T_taihao_strict_table_scaffolding_clean_boundary_pilot_rerun.md
docs/agent/348N_R7T_TAIHAO_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_PILOT_RERUN.md
docs/codex_tasks/348N_R7S_QA_strict_table_scaffolding_clean_boundary_review.md
docs/agent/348N_R7S_QA_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_REVIEW.md
docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md
docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md
```

Review implementation files read-only:

```text
datefac_agent/review/clean_candidate_policy.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

---

## Scope Discovery

Find the existing Linyang and Anjing workbook/PDF inputs and prior outputs from repository docs, prior reports, runner history, or local file names.

The likely families are:

```text
Linyang / 林洋
Anjing / 安井
```

Do not guess if names differ locally. Report the exact input files and baseline output folders you find.

If either workbook family cannot be located, do not invent a replacement. Complete the report with a useful diagnosis and mark the missing family clearly.

---

## Rerun Requirements

For each located family, run the existing Excel intake/audit runner using the same local runner pattern as R7T.

Create new output directories with unique R7U names, for example:

```text
output/agent_excel_intake_audit_348n_r7u_linyang_regression_check/
output/agent_excel_intake_audit_348n_r7u_anjing_regression_check/
```

The new R7U output directories may be generated locally.

Do not modify any previous output directory.

Do not commit output files.

Expected normal artifacts, if the runner produces them:

```text
agent_excel_intake_audit_348a_manifest.json
clean_data.csv
review_queue.csv
evidence_index.json
```

---

## Validation Questions

Answer these for each family:

1. Did the rerun complete without a new guardrail failure?
2. What is the manifest decision?
3. What are clean_data logical and physical counts?
4. What are review_queue logical and physical counts?
5. Did logical and physical counts remain aligned?
6. Did unknown_row_count remain acceptable and explainable?
7. Did market_reference behavior remain stable?
8. Did forbidden row_type enter clean_data?
9. Did normal numeric financial fact rows remain in clean_data?
10. Did the R7S scaffolding guard over-filter legitimate rows?
11. Did readiness gates remain closed?
12. Did output remain demo-only and not formal-client-export ready?

Also compare against available baseline reports or previous outputs. If exact old baseline counts are unavailable, state that clearly and compare against current behavior and invariants instead.

---

## Allowed Scope

Allowed to create exactly one result report:

```text
docs/agent/348N_R7U_LINYANG_ANJING_WORKBOOK_FAMILY_REGRESSION_CHECK.md
```

Allowed to create new local R7U output directories under `output/`.

Allowed to read docs, implementation, tests, input files, previous output artifacts, and new output artifacts.

---

## Forbidden Actions

Do not modify code.

Do not modify tests.

Do not modify previous output directories.

Do not modify input files.

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
pytest tests/agent -q
```

Run the Linyang and Anjing rerun commands that the repository tooling supports. Report the exact commands.

After creating the report, run:

```text
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

If output files appear in git status, do not stage them. Report them as generated local artifacts only.

---

## Expected Report Content

The report must include:

```text
Task ID
Preflight
Files and artifacts reviewed
Discovered Linyang inputs and baselines
Discovered Anjing inputs and baselines
Exact rerun commands
Manifest summary for each family
Clean/review count comparison
Forbidden clean row_type check
Market reference boundary check
Normal financial fact preservation check
Over-filter risk check
Readiness gates
Output artifact policy
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
linyang_rerun_result（林洋重跑结果）=
anjing_rerun_result（安井重跑结果）=
linyang_clean_data_row_count（林洋clean逻辑行数）=
linyang_review_queue_row_count（林洋review逻辑行数）=
anjing_clean_data_row_count（安井clean逻辑行数）=
anjing_review_queue_row_count（安井review逻辑行数）=
forbidden_clean_row_type_found（clean中是否发现禁止row_type）=
market_reference_boundary_ok（市场引用边界是否正常）=
normal_fact_preservation_ok（正常事实是否保留）=
readiness_gates（就绪门）=
output_committed（是否提交output）=
files_modified（修改文件数）=
error_count（错误数）=
boundary_check（边界检查）=
recommended_next_task（推荐下一任务）=
```

---

## Commit / Push Rule

If and only if:

1. the regression check completed or failed with a useful diagnosis,
2. exactly one report was created under `docs/agent/`,
3. no code/tests/docs other than the allowed report were modified,
4. output artifacts are not staged,
5. `git diff --check` is clean for the report,

then stage exactly the report file:

```text
git add docs/agent/348N_R7U_LINYANG_ANJING_WORKBOOK_FAMILY_REGRESSION_CHECK.md
```

Do not stage output files.

Do not use `git add .`.

Do not use `git add -A`.

Commit:

```text
git commit -m "docs: add R7U workbook regression review"
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

If generated output files remain untracked after commit, report them clearly and do not delete them unless repository docs explicitly require cleanup.

Stop after push. Do not start the next task.
