# 348N-R7AO-QA test-only MinerU adapter controlled comparison runner review

## Execution sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
reason = R7AO completed a local no-commit controlled comparison runner. QA must verify the local outputs, status counts, probe coverage, boundary safety, and no tracked-code/output contamination before any next integration step.
```

## Task Goal

Review the R7AO local controlled comparison runner result and outputs.

Task ID:

```text
348N-R7AO-QA test-only MinerU adapter controlled comparison runner review
```

This is QA review only.

Do not modify production code.
Do not modify tests.
Do not modify the local runner unless a blocking defect is found and you stop first to report it.
Do not commit local runner or reports.
Do not run MinerU, OCR, LLM, VLM, or real PDF extraction.
Do not add dependencies.
Do not open readiness gates.

---

## Background

R7AO completed locally with:

```text
Decision = PASS，348N_R7AO_LOCAL_CONTROLLED_COMPARISON_COMPLETED
451 rows compared
MinerU adapter blocks = 89
VERIFIED = 402
review_required = 49
DISAGREED = 5
AMBIGUOUS = 10
MISSING_EVIDENCE = 1
PARSE_SKIPPED = 18
probe_examples_result = VERIFIED:11
boundary_check = PASS
readiness_gates = CLOSED
no commit / no push / no staging
```

Local output directory:

```text
D:\_datefac_agent\output\comparison\anjing_foods_mineru_adapter_r7ao\
```

Expected local outputs:

```text
run_r7ao_mineru_adapter_comparison.py
r7ao_mineru_adapter_comparison_report.xlsx
r7ao_mineru_adapter_comparison_summary.md
r7ao_mineru_adapter_evidence_rows.csv
r7ao_mineru_adapter_unmatched_rows.csv
r7ao_mineru_adapter_run_metadata.json
```

Some outputs may be absent if the runner only produced a subset; QA must record exactly what exists.

---

## Required Preflight

Run and report:

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -12
```

If worktree has tracked changes after pull, stop and report.

Untracked or ignored files under:

```text
output/comparison/anjing_foods_mineru_adapter_r7ao/
```

are allowed as local outputs, but must not be staged or committed.

---

## Required Read Order

Read:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/codex_tasks/348N_R7AO_test_only_mineru_adapter_controlled_comparison_runner.md
docs/agent/348N_R7AN_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_DRY_RUN_DESIGN.md
docs/agent/348N_R7AM_QA_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REVIEW.md
docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md
```

Review R7AM adapter files read-only:

```text
tests/agent/mineru_artifact_adapter_348n.py
tests/agent/test_mineru_artifact_adapter_348n.py
```

Review local R7AO outputs read-only:

```text
D:\_datefac_agent\output\comparison\anjing_foods_mineru_adapter_r7ao\run_r7ao_mineru_adapter_comparison.py
D:\_datefac_agent\output\comparison\anjing_foods_mineru_adapter_r7ao\r7ao_mineru_adapter_comparison_summary.md
D:\_datefac_agent\output\comparison\anjing_foods_mineru_adapter_r7ao\r7ao_mineru_adapter_run_metadata.json
D:\_datefac_agent\output\comparison\anjing_foods_mineru_adapter_r7ao\r7ao_mineru_adapter_comparison_report.xlsx
D:\_datefac_agent\output\comparison\anjing_foods_mineru_adapter_r7ao\r7ao_mineru_adapter_evidence_rows.csv
D:\_datefac_agent\output\comparison\anjing_foods_mineru_adapter_r7ao\r7ao_mineru_adapter_unmatched_rows.csv
```

If any expected local output is missing, record it. Missing optional CSV files may be WARN, not automatic FAIL, if xlsx/md/json are complete.

---

## QA Questions

Answer all:

1. Did R7AO leave tracked files unchanged?
2. Were local outputs kept under the approved output directory?
3. Were no outputs staged, committed, or pushed?
4. Does the local runner import and reuse `tests.agent.mineru_artifact_adapter_348n`?
5. Does the runner avoid production pipeline imports or side effects?
6. Did the runner resolve exactly one DateFac Excel and one MinerU content_list_v2?
7. Does metadata JSON record input paths, branch/head, row counts, block counts, status counts, and readiness gates?
8. Are status counts internally consistent?
9. Do `verified + review_required` add up to total candidate rows, or is any difference explained by `PARSE_SKIPPED` semantics?
10. Are DISAGREED / AMBIGUOUS / MISSING_EVIDENCE / PARSE_SKIPPED represented clearly?
11. Are all 11 required probe examples reported and VERIFIED?
12. Does the report explain why R7AO differs from R7AL if counts changed?
13. Does the evidence sheet/report avoid full uncontrolled source_text dumping?
14. Does the runner keep VERIFIED non-promotional?
15. Does the runner avoid STRONG_EVIDENCE promotion?
16. Does the runner avoid clean_data admission changes?
17. Does the runner avoid readiness gate changes?
18. Did validation commands pass?
19. What limitations should be carried forward?
20. What is the safest next task?

---

## Required Count Sanity Checks

Validate and report:

```text
total_rows = 451
verified_count = 402
review_required_count = 49
disagreed_count = 5
ambiguous_count = 10
missing_evidence_count = 1
parse_skipped_count = 18
probe_examples_result = VERIFIED:11
```

Important: `review_required_count` may include DISAGREED / AMBIGUOUS / MISSING_EVIDENCE / PARSE_SKIPPED categories, or may be a separate aggregate. QA must explain the aggregation rule based on the report/metadata.

---

## Boundary Checks

Must confirm:

```text
no datefac_agent/ changes
no tests/ changes
no docs/ changes except QA report
no dependency changes
no output files committed
no local runner committed
no DateFac Excel committed
no MinerU output committed
no MinerU run
no OCR / LLM / VLM use
no production pipeline hook
VERIFIED remains non-promotional
readiness_gates remain CLOSED
```

---

## Validation Commands

Run and report:

```text
python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
pytest tests/agent/test_mineru_artifact_adapter_348n.py -q
pytest tests/agent -q
python output/comparison/anjing_foods_mineru_adapter_r7ao/run_r7ao_mineru_adapter_comparison.py
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

Re-running the local runner is allowed if it only overwrites local output files under the approved output directory and does not change tracked files.

---

## Allowed File

Allowed to create exactly one QA report:

```text
docs/agent/348N_R7AO_QA_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_RUNNER_REVIEW.md
```

No other tracked files may be changed.

---

## Expected Report Content

Create:

```text
docs/agent/348N_R7AO_QA_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_RUNNER_REVIEW.md
```

Include:

```text
Task ID
Task size / reasoning level used
Preflight
Files reviewed
Local outputs reviewed
Runner review
Input resolution review
Metadata review
Report/output review
Status count sanity check
Probe examples review
Boundary review
Validation outputs
Limitations
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
runner_review_result（runner审查结果）=
metadata_review_result（metadata审查结果）=
comparison_output_review_result（对比输出审查结果）=
count_sanity_result（计数一致性结果）=
probe_examples_review_result（探针样例审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should normally be one of:

```text
348N-R7AP production-boundary MinerU evidence adapter integration design
348N-R7AP test-only multi-document MinerU adapter dry-run design
348N-R7AP DateFac-MinerU discrepancy review workflow design
```

Choose based on QA findings.

---

## Commit / Push Rule

If QA passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7AO_QA_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_RUNNER_REVIEW.md
```

Do not use broad staging.

Commit:

```text
git commit -m "docs: add R7AO QA review"
```

Push:

```text
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
