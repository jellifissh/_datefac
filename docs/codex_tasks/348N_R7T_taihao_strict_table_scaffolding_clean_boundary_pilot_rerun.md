# 348N-R7T Taihao strict_table scaffolding clean-boundary pilot rerun

## Task Goal

Run a controlled Taihao pilot rerun after the R7S implementation and verify the real output impact of the strict-table scaffolding clean-boundary guard.

Task ID:

```text
348N-R7T Taihao strict_table scaffolding clean-boundary pilot rerun
```

This is a validation / rerun / result-report task.

It is not an implementation task.

Do not modify code or tests.

Do not run MinerU, OCR, LLM, or VLM.

Do not run a new PDF extraction pipeline.

Use the existing Excel workbook input and the existing local runner/tooling documented in the repository.

---

## Required Preflight

Run and report:

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -10
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
docs/codex_tasks/348N_R7S_QA_strict_table_scaffolding_clean_boundary_review.md
docs/agent/348N_R7S_QA_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_REVIEW.md
docs/codex_tasks/348N_R7S_strict_table_pseudo_header_comparison_row_clean_boundary_implementation.md
docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md
docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md
```

Review implementation files read-only:

```text
datefac_agent/review/clean_candidate_policy.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Use the existing R7Q baseline output as read-only comparison input:

```text
output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/agent_excel_intake_audit_348a_manifest.json
output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/clean_data.csv
output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/review_queue.csv
output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/evidence_index.json
```

---

## Input Workbook

Use the Taihao workbook:

```text
input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
```

Do not modify the input workbook.

---

## Rerun Requirements

Find the existing local runner/tooling from prior tasks and repository docs. Prefer the same runner pattern used for R7P/R7P-FIX2-QA Taihao pilot outputs.

Run the Excel intake/audit pipeline on the Taihao workbook after R7S.

Create a new output directory with a unique R7T name, for example:

```text
output/agent_excel_intake_audit_348n_r7t_taihao_scaffolding_boundary_rerun/
```

The output directory is allowed to be created or overwritten only for this R7T rerun. Do not modify any previous output directory.

Expected output files should include the normal runner artifacts if the runner produces them:

```text
agent_excel_intake_audit_348a_manifest.json
clean_data.csv
review_queue.csv
evidence_index.json
```

Do not commit output files.

---

## Validation Questions

Answer all of the following in the report:

1. Did the rerun complete without a new guardrail failure?
2. What is the new manifest decision?
3. What are the new clean_data and review_queue logical counts?
4. What are the new clean_data.csv and review_queue.csv physical counts?
5. Did logical and physical counts remain aligned?
6. Did the risky rows identified by R7Q/R7R move out of clean_data?
7. Specifically check rows or labels:

```text
市场数据
厂商
对比维度
订单日期
项目
指标
```

8. Did `收盘价` and `总市值` remain in review_queue and stay out of clean_data?
9. Did any forbidden row_type enter clean_data?
10. Did normal numeric financial fact rows remain in clean_data?
11. Did readiness gates remain closed?
12. Did the output remain demo-only and not formal-client-export ready?

---

## Required Comparison Baseline

Compare R7T rerun against R7Q baseline:

```text
R7Q clean_data_row_count = 92
R7Q clean_data_csv_row_count = 92
R7Q review_queue_row_count = 66
R7Q review_queue_csv_row_count = 66
R7Q unknown_row_count = 0
R7Q market_reference_row_count = 2
```

Expected direction after R7S:

```text
clean_data count should likely decrease
review_queue count should likely increase
unknown_row_count should remain 0 unless the runner semantics explain otherwise
market_reference_row_count should remain stable
readiness gates should remain closed
```

Do not force exact counts in advance. Report observed counts honestly.

---

## Allowed Scope

Allowed to create one result report:

```text
docs/agent/348N_R7T_TAIHAO_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_PILOT_RERUN.md
```

Allowed to create one new output directory for the R7T rerun under `output/`.

Allowed to read existing docs, implementation, tests, input workbook, and R7Q baseline output.

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

Run the Taihao rerun command that the repository tooling supports. Report the exact command.

After creating the report, run:

```text
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

If `output/` files appear in git status, do not stage them. Report them as generated local artifacts only.

---

## Expected Report Content

The report must include:

```text
Task ID
Preflight
Files and artifacts reviewed
Exact rerun command
R7Q baseline
R7T manifest summary
Clean/review count comparison
Risky row migration check
Market reference boundary check
Normal financial fact preservation check
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
rerun_result（重跑结果）=
clean_data_row_count_before（R7Q clean逻辑行数）=
clean_data_row_count_after（R7T clean逻辑行数）=
review_queue_row_count_before（R7Q review逻辑行数）=
review_queue_row_count_after（R7T review逻辑行数）=
unknown_row_count_after（R7T unknown行数）=
market_reference_row_count_after（R7T market reference行数）=
risky_rows_in_clean_after（风险行是否仍在clean）=
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

1. the rerun completed or failed with a useful diagnosis,
2. exactly one report was created under `docs/agent/`,
3. no code/tests/docs other than the allowed report were modified,
4. output artifacts are not staged,
5. `git diff --check` is clean for the report,

then stage exactly the report file:

```text
git add docs/agent/348N_R7T_TAIHAO_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_PILOT_RERUN.md
```

Do not stage output files.

Do not use `git add .`.

Do not use `git add -A`.

Commit:

```text
git commit -m "docs: add R7T Taihao rerun review"
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

If generated output files remain untracked after commit, report them clearly and do not delete them unless the repository docs explicitly require cleanup.

Stop after push. Do not start the next task.
