# 348N-R7CC-QA mainline MinerU/original reconciliation vertical slice review

## Goal

Review the completed R7CC mainline vertical slice before extending it to real MinerU artifacts.

Plain Chinese: 这一轮只做 QA，确认 R7CC 真的实现了“MinerU 风格产物 + 现有产物 -> 标准化 -> 对比 -> review_queue 候选”这条主线小闭环，而且没有偷偷继续 DB、clean_data、delivery/export 或 readiness 工作。

## Workspace

```text
D:\_datefac_agent
branch = pivot/348-agent-foundation
```

## Preflight

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -140
```

Stop if the worktree is not clean after pull.

## Read first

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md
docs/agent/348N_R7CC_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_DEMO_REPORT.md
```

Review R7CC files:

```text
datefac_agent/reconciliation/__init__.py
datefac_agent/reconciliation/mineru_original_reconciliation_348n.py
tests/agent/test_mineru_original_reconciliation_348n.py
tests/agent/fixtures/mineru_original_reconciliation/mineru_content_list_sample.json
tests/agent/fixtures/mineru_original_reconciliation/original_extraction_sample.json
docs/agent/348N_R7CC_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_DEMO_REPORT.md
```

## QA checklist

Confirm:

```text
R7CC changed only the 6 allowed files.
The package whitespace cleanup commit changed no behavior.
The implementation is deterministic pure Python.
MinerU-like and original artifacts can be loaded from path/dict as designed.
Metric aliases normalize consistently.
Annual period forms normalize consistently.
Numeric strings normalize commas, percent signs, and parenthesized negatives safely.
Revenue 2023 is MATCH in the fixture.
Net Profit 2023 is CONFLICT.
EPS 2023 is MINERU_ONLY.
ROE 2023 is ORIGINAL_ONLY.
MATCH rows do not require review by default.
CONFLICT, MINERU_ONLY, ORIGINAL_ONLY, and UNPARSEABLE require review.
Review candidates contain bounded evidence_preview and source_trace.
Review candidates do not contain full source_text or full raw artifacts.
Review candidates set clean_data_eligible=false and keep readiness closed.
Input dictionaries are not mutated.
Output ordering and review_item_id generation are deterministic.
No DB/SQL/network/Docker/LLM/OCR/MinerU runtime dependency was added.
No clean_data write, delivery/export trigger, DB write, schema, migration, or readiness mutation exists.
Existing writer contract and schema alignment tests remain compatible.
Full tests/agent baseline is 803 passed.
The report correctly states current limitations: tiny fixture only, no full MinerU parsing, no unit conversion, no duplicate metric resolution, no production review UI.
```

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7CC_QA_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_REVIEW.md
```

No other tracked files may change. Do not implement the next mainline slice in this task.

## Validation commands

```text
python -m py_compile datefac_agent/reconciliation/mineru_original_reconciliation_348n.py
python -m py_compile tests/agent/test_mineru_original_reconciliation_348n.py
python -m pytest tests/agent/test_mineru_original_reconciliation_348n.py -q
python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
python -m pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

## Report sections

```text
Task ID
Preflight
Files reviewed
R7CC recap
Allowed file boundary review
Mainline vertical slice review
Artifact loading review
Normalization review
Comparison status review
Review_queue candidate review
Raw artifact exclusion review
Determinism and mutation safety review
Compatibility review
Boundary review
Validation outputs
Limitations
Decision
Recommended next task
Data Result / 数据结果
```

## Required Data Result

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
mainline_vertical_slice_review_result（主线纵切审查结果）=
artifact_loading_review_result（产物加载审查结果）=
normalization_review_result（标准化审查结果）=
comparison_review_result（对比审查结果）=
review_queue_candidate_review_result（review_queue候选审查结果）=
raw_artifact_exclusion_review_result（原始产物排除审查结果）=
determinism_mutation_review_result（确定性与输入不变审查结果）=
compatibility_review_result（兼容性审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7CD real MinerU artifact compatibility slice demo-only
```

## Commit and push

```text
git add docs/agent/348N_R7CC_QA_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_REVIEW.md
git commit -m "docs: add R7CC QA review"
git push origin pivot/348-agent-foundation
```

Stop after push.
