# 348F Fixture Harvest from 346B

## 中文说明

本任务目标：从历史 `346B` 系列和当前 348A/348S 已确认的问题中，提炼一批小型、稳定、可重复运行的 agent audit fixtures。

这不是继续跑旧 346B，也不是迁移旧 runner。

要做的是：

```text
把历史里已经证明有价值的失败模式，压缩成 tests/agent/fixtures/ 下的小样本
再用 tests/agent/ 里的单元测试固定这些行为
```

重点 fixture 类型：

```text
unit_mismatch
rate_metric_false_positive
period_context_missing
embedded_period_header
narrative_exclusion
market_reference_candidate
clean_candidate_policy
```

---

## 1. Goal

Harvest compact fixtures for DateFac Agent audit tests from:

```text
346B historical lessons
348A-R4 clean candidate policy
348S-R1/R2 real workbook issues and repairs
```

The goal is to prevent future regressions in unit, period, row-type, and clean/review routing rules.

---

## 2. Required context

Read only:

```text
AGENTS.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
docs/agent/FIXTURE_STRATEGY.md
docs/agent/348S_R2_QA_UNIT_PERIOD_RESIDUAL_REFINEMENT_REVIEW.md
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
```

Read legacy files only if needed and keep scope small.

---

## 3. Working directory

Use:

```text
D:\_datefac_agent
```

Expected branch:

```text
pivot/348-agent-foundation
```

Preflight:

```powershell
cd D:\_datefac_agent
git pull --ff-only origin pivot/348-agent-foundation
git status -sb
git branch --show-current
```

Stop if the worktree is not clean.

---

## 4. Scope

Allowed to create or modify:

```text
tests/agent/fixtures/
tests/agent/test_agent_excel_intake_audit_348a.py
possibly docs/agent/348F_FIXTURE_HARVEST_RESULT.md
```

Allowed to inspect, but do not modify:

```text
docs/agent/348S_R2_QA_UNIT_PERIOD_RESIDUAL_REFINEMENT_REVIEW.md
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
docs/agent/FIXTURE_STRATEGY.md
old docs/agent or docs/legacy references when needed
```

Do not modify:

```text
legacy datefac/
old tools/
input/
output/
temp/
data/
```

---

## 5. Fixture design rules

Fixtures must be small and semantic.

Do not copy full output folders.

Do not copy real PDF contents.

Do not copy huge CSVs.

Prefer compact JSON fixtures such as:

```text
tests/agent/fixtures/unit_mismatch__asset_total_percent__v1.json
tests/agent/fixtures/unit_mismatch__asset_total_percent__expected.json
```

or compact directory cases:

```text
tests/agent/fixtures/period__embedded_header_forecast_business__v1/
  input.json
  expected.json
  notes.md
```

Each fixture should record:

```text
source_task
issue_type
input_shape
expected_outcome
why_it_matters
```

---

## 6. Required fixture cases

Create fixtures and tests for at least these cases:

### 6.1 Unit / rate cases

1. `资产负债率(%)` should be treated as rate metric, not monetary mismatch.
2. `资产负债率(%,LF)` should be treated as rate metric, not monetary mismatch.
3. `资产总计(%)` should still trigger monetary mismatch.
4. `负债合计(%)` should still trigger monetary mismatch.
5. `净资产收益率(%)` / ROE-style label should remain rate metric.

### 6.2 Period cases

1. `2025A收入(亿元)` should expose period `2025A`.
2. `2026E收入(亿元)` should expose period `2026E`.
3. `2027E收入(亿元)` should expose period `2027E`.
4. `2028E收入(亿元)` should expose period `2028E`.
5. `2026E毛利率(%)` should expose period `2026E`.
6. A truly periodless strict financial row should still trigger period issue.

### 6.3 Row type / clean policy cases

1. Narrative rows should not enter clean_data.
2. Market reference rows with weak evidence and no unit issue can become internal reference candidates.
3. Strict financial rows with weak evidence and no unit/period/valuation issue can become internal clean candidates.
4. Strict financial rows with period issue must stay in review queue.
5. Missing evidence must not enter clean_data.

---

## 7. Tests

Add focused tests that load fixtures and assert current behavior.

Prefer testing existing pure functions / policy functions directly.

If existing tests already cover some cases inline, move or supplement them with fixture-backed cases.

Do not make the tests depend on large local input/output directories.

Required validation:

```powershell
python -m py_compile tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
```

If you add helper modules under tests, include them in py_compile.

---

## 8. Expected report

Create:

```text
docs/agent/348F_FIXTURE_HARVEST_RESULT.md
```

Include:

```text
Task ID
Fixture sources used
Fixture files created
Test changes
Validation results
What behavior is now protected
What was intentionally not harvested
Remaining risks
Decision
Recommended next task
```

Suggested decision values:

```text
348F_CONFIRMED_FIXTURE_HARVEST_COMPLETE
348F_CONFIRMED_PARTIAL_FIXTURE_HARVEST
348F_BLOCKED_BY_UNCLEAR_FIXTURE_SOURCE
```

---

## 9. Non-goals

Do not run MinerU.

Do not call LLM/VLM APIs.

Do not run OCR.

Do not re-extract PDFs.

Do not touch legacy `datefac/`.

Do not touch old `D:\_datefac`.

Do not submit output files.

Do not claim `client_ready` or `production_ready`.

Do not use:

```text
git add .
git add -A
git reset --hard
git checkout --
```

---

## 10. Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Which fixture sources were used.
5. Which fixture files were created.
6. Which tests were added or modified.
7. Which behaviors are now protected.
8. py_compile result.
9. pytest result.
10. Whether no output files were committed.
11. Whether legacy `datefac/` was untouched.
12. Whether LLM/MinerU/OCR calls were zero.
13. `git status -sb`.
14. Recommended next task.

---

## 11. Likely next tasks

If fixture harvest succeeds:

```text
348F-QA Fixture Harvest Review
348S Third Workbook Pilot
```
