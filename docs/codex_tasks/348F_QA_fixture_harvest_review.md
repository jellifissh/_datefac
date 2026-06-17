# 348F-QA Fixture Harvest Review

## 中文说明

本任务只做 QA 审查，不改源码。

348F 已经把 346B 语义教训、348A-R4 clean candidate policy、348S-R2 residual 修复沉淀成 fixture-backed tests。

本任务要确认：

```text
fixture 是否足够小
fixture 是否语义清晰
fixture 是否真的覆盖关键行为
fixture-backed tests 是否调用真实 checker / policy
是否没有复制旧 output / legacy runner / 大文件
是否没有把测试写成永远通过的安慰剂
```

---

## 1. Goal

Review `348F Fixture Harvest from 346B`.

This is a QA-only task.

Do not modify source code unless a critical test-breaking typo prevents the QA from running. If that happens, stop and report first.

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
docs/agent/348F_FIXTURE_HARVEST_RESULT.md
docs/agent/348S_R2_QA_UNIT_PERIOD_RESIDUAL_REFINEMENT_REVIEW.md
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
```

Do not read broad legacy directories unless you need to verify a narrow traceability claim.

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

## 4. Files to review

Review fixture files:

```text
tests/agent/fixtures/unit_semantics__346b_lessons_and_348s_r2__v1.json
tests/agent/fixtures/period_detection__embedded_headers_and_missing_period__v1.json
tests/agent/fixtures/routing_policy__narrative_market_strict_and_missing_evidence__v1.json
```

Review tests:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
```

Review report:

```text
docs/agent/348F_FIXTURE_HARVEST_RESULT.md
```

---

## 5. QA checks

### 5.1 Fixture size and structure

Confirm:

```text
fixtures are compact JSON files
fixtures do not copy large output snapshots
fixtures do not depend on input/ or output/ directories
fixtures include source_task / issue_type / expected_outcome or equivalent traceability fields
fixtures are readable enough for future maintainers
```

### 5.2 Unit fixture QA

Confirm fixture coverage for:

```text
资产负债率(%) -> no monetary_unit_mismatch
资产负债率(%,LF) -> no monetary_unit_mismatch
资产总计(%) -> monetary_unit_mismatch
负债合计(%) -> monetary_unit_mismatch
ROE / 净资产收益率 -> rate metric behavior preserved
```

Confirm tests actually call the unit checker logic, not merely assert constants from fixture JSON.

### 5.3 Period fixture QA

Confirm fixture coverage for:

```text
2025A收入(亿元) -> 2025A
2026E收入(亿元) -> 2026E
2027E收入(亿元) -> 2027E
2028E收入(亿元) -> 2028E
2026E毛利率(%) -> 2026E
truly periodless strict financial row -> period_context_missing
```

Confirm tests actually call period detection / period checker logic.

### 5.4 Routing policy fixture QA

Confirm fixture coverage for:

```text
narrative rows do not enter clean_data
market reference weak-evidence rows can become INTERNAL_REFERENCE_CANDIDATE
strict financial weak-evidence clean rows can become INTERNAL_CLEAN_CANDIDATE
strict financial rows with period issue stay REVIEW_REQUIRED
missing-evidence rows do not enter clean_data
```

Confirm tests call the real clean candidate / review routing policy.

### 5.5 Regression discipline

Run:

```powershell
python -m py_compile tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
```

Expected currently:

```text
29 passed
```

### 5.6 Boundary discipline

Confirm:

```text
no output files committed
legacy datefac/ untouched
old runners untouched
LLM / MinerU / OCR not called
no PDF re-extraction
```

---

## 6. Expected QA report

Create:

```text
docs/agent/348F_QA_FIXTURE_HARVEST_REVIEW.md
```

Include:

```text
Task ID
Files reviewed
Fixture structure QA
Unit fixture QA
Period fixture QA
Routing policy fixture QA
Test implementation quality
Validation results
Boundary discipline
Remaining risks
Decision
Recommended next task
```

Suggested decision values:

```text
348F_QA_CONFIRMED_FIXTURE_HARVEST_VALID
348F_QA_CONFIRMED_PARTIAL_FIXTURE_HARVEST_REMAINING_GAPS
348F_QA_CONFIRMED_TESTS_TOO_WEAK
348F_QA_CONFIRMED_FIXTURE_SCOPE_TOO_BROAD
```

Choose one primary decision.

---

## 7. Non-goals

Do not modify source code.

Do not add new fixture categories.

Do not rewrite tests unless QA is blocked by a trivial typo.

Do not submit output files.

Do not touch legacy `datefac/`.

Do not run MinerU / OCR / LLM / VLM.

Do not re-extract PDFs.

Do not use:

```text
git add .
git add -A
git reset --hard
git checkout --
```

---

## 8. Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Which fixture files were reviewed.
5. Fixture structure QA findings.
6. Unit fixture QA findings.
7. Period fixture QA findings.
8. Routing fixture QA findings.
9. Whether tests call real checker/policy logic.
10. py_compile result.
11. pytest result.
12. Boundary discipline findings.
13. Remaining risks.
14. `git status -sb`.
15. Recommended next task.

---

## 9. Likely next tasks

If QA passes:

```text
348S Third Workbook Pilot
```

Alternative if the project wants more test hardening first:

```text
348F-R1 Add Valuation/Per-Share Fixtures
```
