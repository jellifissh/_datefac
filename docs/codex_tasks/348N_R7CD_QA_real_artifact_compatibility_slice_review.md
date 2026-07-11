# 348N-R7CD-QA real artifact compatibility slice review

## Goal

Review the completed R7CD real-artifact compatibility slice before extending the mainline to discrepancy diagnosis and review output.

Plain Chinese: 这一轮只做 QA。确认真实 MinerU JSON 和真实 DateFac Excel 的兼容层确实可靠，415 对 415 的记录不是靠错误吞数据凑出来的，414 个 MATCH 和 2 个待复核项也能被解释清楚。

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
git log --oneline -145
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
docs/agent/348N_R7CD_REAL_MINERU_ARTIFACT_COMPATIBILITY_SLICE_DEMO_ONLY_REPORT.md
docs/agent/348N_R7CC_QA_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_REVIEW.md
docs/agent/348N_R7CC_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_DEMO_REPORT.md
```

Review R7CD files:

```text
datefac_agent/reconciliation/real_artifact_compatibility_348n.py
tools/run_real_artifact_reconciliation_348n.py
tests/agent/test_real_artifact_compatibility_348n.py
tests/agent/fixtures/mineru_original_reconciliation/real_content_list_v2_table_sample.json
docs/agent/348N_R7CD_REAL_MINERU_ARTIFACT_COMPATIBILITY_SLICE_DEMO_ONLY_REPORT.md
```

## QA checklist

Confirm:

```text
R7CD changed only the 5 allowed files.
No complete real JSON, PDF, Markdown, or Excel workbook was committed.
The MinerU parser handles page-grouped lists, table blocks, content.html, captions, footnotes, bbox, and page trace.
HTML table expansion is deterministic and does not silently drop normal rows.
The workbook is opened read_only=True and data_only=True and closed reliably.
Only the five approved financial sheets are read.
Periods preserve A/E/F suffixes such as 2024A and 2026E.
Statement context participates in comparison identity.
Metric labels and units are normalized without silently changing incompatible units.
UNIT_REVIEW is review-required.
Comparison statuses are deterministic.
Review candidates contain bounded evidence and source trace only.
No full raw artifact or source text is copied into review candidates.
No input objects are mutated.
CLI accepts only explicit input paths and prints compact counts only.
CLI does not create output files.
No DB/repository/schema/migration/clean_data/delivery/export/readiness integration was added.
No MinerU/OCR/LLM/VLM runtime invocation was added.
R7CC tests remain green.
Full tests/agent baseline is 813 passed.
Real smoke can be reproduced from the same two local basenames.
Real smoke result is internally consistent: 416 comparison rows = 414 MATCH + 1 ORIGINAL_ONLY + 1 UNPARSEABLE.
The two review-required rows both belong to the 总资产周转率 discrepancy cluster and are not two unrelated hidden failures.
The workbook-side corrected value 0.8 is preserved in trace/evidence without being written to clean_data.
The report does not claim production readiness or final reconciliation accuracy.
readiness_gates remain CLOSED.
```

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7CD_QA_REAL_ARTIFACT_COMPATIBILITY_SLICE_REVIEW.md
```

No other tracked files may change. Do not implement R7CE in this task.

## Validation commands

```text
python -m py_compile datefac_agent/reconciliation/real_artifact_compatibility_348n.py
python -m py_compile tools/run_real_artifact_reconciliation_348n.py
python -m py_compile tests/agent/test_real_artifact_compatibility_348n.py
python -m pytest tests/agent/test_real_artifact_compatibility_348n.py -q
python -m pytest tests/agent/test_mineru_original_reconciliation_348n.py -q
python -m pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

Re-run the real local smoke if both exact local inputs are still available. Record counts only; do not create or commit outputs.

## Report sections

```text
Task ID
Preflight
Files reviewed
R7CD recap
Allowed file boundary review
Real MinerU parsing review
Real workbook parsing review
HTML table expansion review
Period/context/unit review
Comparison identity and status review
Review candidate safety review
CLI smoke behavior review
Real smoke count reconciliation
总资产周转率 discrepancy cluster review
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
real_mineru_compatibility_review_result（真实MinerU兼容审查结果）=
real_xlsx_compatibility_review_result（真实xlsx兼容审查结果）=
html_table_expansion_review_result（HTML表格展开审查结果）=
period_context_unit_review_result（期间上下文单位审查结果）=
comparison_identity_review_result（对比身份审查结果）=
review_candidate_safety_review_result（复核候选安全审查结果）=
real_smoke_reproducibility_result（真实smoke复现结果）=
discrepancy_cluster_review_result（差异簇审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7CE real discrepancy diagnosis and review report demo-only
```

## Commit and push

```text
git add docs/agent/348N_R7CD_QA_REAL_ARTIFACT_COMPATIBILITY_SLICE_REVIEW.md
git commit -m "docs: add R7CD QA review"
git push origin pivot/348-agent-foundation
```

Stop after push.
