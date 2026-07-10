# 348N-R7CC mainline MinerU/original reconciliation vertical slice demo

## Goal

Pause the local test DB chain. Do not run R7CB now.

Build a small mainline demo slice:

```text
MinerU-style artifact + existing extraction artifact
-> normalize metrics
-> compare values
-> produce reconciliation rows
-> produce review_queue-style candidates
```

In plain Chinese: 先别继续修 DB/adapter/repository。现在先跑主线：拿 MinerU 产物和别人已有产物做对比，找出 MATCH、CONFLICT、MINERU_ONLY、ORIGINAL_ONLY，并生成需要人工复核的候选项。

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
```

## Allowed tracked files

Prefer creating only:

```text
datefac_agent/reconciliation/mineru_original_reconciliation_348n.py
tests/agent/test_mineru_original_reconciliation_348n.py
tests/agent/fixtures/mineru_original_reconciliation/mineru_content_list_sample.json
tests/agent/fixtures/mineru_original_reconciliation/original_extraction_sample.json
docs/agent/348N_R7CC_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_DEMO_REPORT.md
```

If needed, also create:

```text
datefac_agent/reconciliation/__init__.py
```

## Required behavior

Implement deterministic pure-Python logic for a tiny demo fixture.

The sample should prove:

```text
Revenue 2023 = MATCH
Net Profit 2023 = CONFLICT
EPS 2023 = MINERU_ONLY
ROE 2023 = ORIGINAL_ONLY
```

The module should return comparison rows with:

```text
metric
period
mineru_value
original_value
status
reason
review_required
blocked_delivery_reason
evidence_preview
source_trace
```

Only CONFLICT, MINERU_ONLY, ORIGINAL_ONLY, and UNPARSEABLE require review by default.

## Boundaries

Do not continue DB work in this task. Do not add schema, migration, database adapter, delivery/export integration, clean_data writes, or readiness changes. Do not run MinerU/OCR/LLM. Use tiny fixtures only.

## Tests

Cover:

```text
loading fixtures
metric normalization
numeric normalization
MATCH
CONFLICT
MINERU_ONLY
ORIGINAL_ONLY
review candidates
bounded evidence_preview
input objects not mutated
deterministic output
no DB/network/LLM/OCR imports
existing review_queue contract tests still pass
```

## Report sections

```text
Task ID
Preflight
Reason for pivot back to mainline
Mainline vertical slice scope
Files changed
Fixture design
Loading behavior
Normalization behavior
Comparison behavior
Review_queue candidate behavior
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
mainline_vertical_slice_result（主线纵切结果）=
normalization_result（标准化结果）=
comparison_result（对比结果）=
review_queue_candidate_result（review_queue候选结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7CC-QA mainline MinerU/original reconciliation vertical slice review
```

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

## Commit and push

Stage changed allowed files explicitly. Then:

```text
git commit -m "feat: add MinerU original reconciliation vertical slice"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
