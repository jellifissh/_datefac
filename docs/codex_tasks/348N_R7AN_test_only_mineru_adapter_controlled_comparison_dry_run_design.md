# 348N-R7AN test-only MinerU adapter controlled comparison dry-run design

## Execution sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = design-review-only
reason = R7AM-QA confirmed the test-only MinerU artifact adapter prototype is valid. R7AN should design the next controlled dry-run that uses the prototype shape against the Anjing DateFac-vs-MinerU comparison flow without modifying production code or committing local outputs.
```

## Task Goal

Design a safe, test-only controlled comparison dry-run that uses the R7AM MinerU adapter prototype as the evidence-block source for the Anjing DateFac-vs-MinerU comparison path.

Task ID:

```text
348N-R7AN test-only MinerU adapter controlled comparison dry-run design
```

This is a design task only.

Do not implement the dry-run runner yet.
Do not modify production code.
Do not modify tests.
Do not commit local output files.
Do not run MinerU, OCR, LLM, VLM, or real PDF extraction.
Do not add dependencies.
Do not open readiness gates.

---

## Background

R7AL completed a real local controlled comparison:

```text
DateFac candidate rows normalized = 451
MinerU blocks indexed = 173
VERIFIED = 395
review_required_total = 56
DISAGREED = 10
AMBIGUOUS = 10
MISSING_EVIDENCE = 2
required 11 probe examples = all found and VERIFIED against MinerU v2 blocks
primary input recommendation = content_list_v2
fallback/cross-check = content_list
readiness_gates = CLOSED
```

R7AM then created a test-only adapter prototype:

```text
commit = 0de3a4a test: add MinerU artifact adapter prototype
pytest tests/agent/test_mineru_artifact_adapter_348n.py -q = 21 passed
pytest tests/agent -q = 201 passed
adapter = tests/agent/mineru_artifact_adapter_348n.py
fixture = tests/agent/fixtures/mineru_artifacts/anjing_minimal_content_list_v2__r7am.json
```

R7AM-QA confirmed:

```text
commit = 4daa3bf docs: add R7AM QA review
fixture = small curated, 2599 bytes / 7 blocks
adapter = test-only, no production hook
matching helper = conservative
boundary_check = PASS
readiness_gates = CLOSED
```

R7AN should decide how to safely perform the next dry-run using this test-only adapter shape, without jumping into production integration.

---

## Required Preflight

Run and report:

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -12
```

If worktree is not clean after pull, stop and report.

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
docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md
docs/agent/348N_R7AM_QA_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REVIEW.md
```

Review read-only:

```text
tests/agent/mineru_artifact_adapter_348n.py
tests/agent/test_mineru_artifact_adapter_348n.py
tests/agent/fixtures/mineru_artifacts/anjing_minimal_content_list_v2__r7am.json
```

Review local R7AL outputs if present, but do not commit them:

```text
D:\_datefac_agent\output\comparison\anjing_foods_datefac_vs_mineru\anjing_datefac_vs_mineru_comparison_summary.md
D:\_datefac_agent\output\comparison\anjing_foods_datefac_vs_mineru\run_anjing_comparison.py
D:\_datefac_agent\output\comparison\anjing_foods_datefac_vs_mineru\anjing_datefac_vs_mineru_comparison_report.xlsx
```

If local R7AL outputs are absent, continue from the summary above.

---

## Design Questions

Answer all:

1. Should the next dry-run reuse the full local Anjing DateFac Excel and full local MinerU output, or use a smaller controlled subset?
2. Which inputs should be required, optional, or explicitly forbidden?
3. Should the next task create a test-only runner script under `tests/agent/`, an output-only local script under `output/comparison/`, or a docs-only procedure?
4. How should the runner call the R7AM adapter without making it production code?
5. How should DateFac rows be normalized for this dry-run?
6. Should the dry-run compare all 451 rows or only a small selected subset?
7. What row fields are mandatory for comparison: metric, period, value, unit, page_number, source_document_id?
8. How should rows missing page numbers be handled?
9. How should table evidence and paragraph evidence be prioritized?
10. How should AMBIGUOUS / DISAGREED / MISSING_EVIDENCE be reported?
11. Should output files be committed? If not, where should they be written locally?
12. What metrics should the summary report include?
13. How should this differ from R7AL's one-off local script?
14. What would make the next dry-run PASS, BLOCKED, or FAIL?
15. What should be the next task after this design?

---

## Required Design Decisions

The report must make explicit decisions on:

```text
input_scope
local_output_policy
committed_fixture_policy
runner_location
whether to reuse R7AM adapter directly
candidate_row_normalization_strategy
evidence_block_indexing_strategy
matching_status_semantics
report_sheet_design
validation_commands
pass_fail_blocked_criteria
next_task_name
```

---

## Boundary Rules

Forbidden:

```text
modify datefac_agent/
modify tests/
create runner implementation
create new fixtures
commit full MinerU output
commit DateFac Excel
commit comparison xlsx/csv/md outputs
run MinerU
run OCR / LLM / VLM
run real PDF extraction
add dependencies
promote VERIFIED to STRONG_EVIDENCE
promote VERIFIED to clean_data admission
open readiness gates
```

Allowed:

```text
create one design report under docs/agent/
read local R7AL outputs if present
read R7AM test-only adapter and fixture
run validation commands that do not create artifacts
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
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

---

## Allowed File

Allowed to create exactly one file:

```text
docs/agent/348N_R7AN_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_DRY_RUN_DESIGN.md
```

No other files may be changed.

---

## Expected Report Content

Create:

```text
docs/agent/348N_R7AN_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_DRY_RUN_DESIGN.md
```

Include:

```text
Task ID
Task size / reasoning level used
Preflight
Files reviewed
R7AL/R7AM/R7AM-QA evidence recap
Design decision matrix
Input scope
Runner scope
Candidate row normalization design
MinerU adapter usage design
Evidence matching design
Output report design
Pass / fail / blocked criteria
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
input_scope_decision（输入范围决策）=
runner_scope_decision（runner范围决策）=
adapter_usage_decision（adapter使用决策）=
output_policy_decision（输出策略决策）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should normally be:

```text
348N-R7AO test-only MinerU adapter controlled comparison runner
```

Only recommend a different next task if the design finds a blocking issue.

---

## Commit / Push Rule

If validation passes and only the design report is created, stage exactly:

```text
git add docs/agent/348N_R7AN_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_DRY_RUN_DESIGN.md
```

Do not use broad staging.

Commit:

```text
git commit -m "docs: add R7AN controlled comparison design"
```

Push:

```text
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
