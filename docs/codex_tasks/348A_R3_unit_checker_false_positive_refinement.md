# 348A-R3 Unit Checker False Positive Refinement

## 1. Goal

Refine the 348A unit semantic checker to remove the current false-positive-style `FAIL` on:

```text
市场与基础数据:11
净资产收益率(%)
```

R2-QA confirmed that row-type classification is useful and that the most visible remaining blocker is now the unit checker treating `净资产收益率(%)` as a monetary metric because the label contains `资产`.

The goal is:

```text
Classify percentage/rate metrics such as ROE / 净资产收益率 / 收益率 as percentage metrics before applying broad monetary-token heuristics.
```

The goal is not:

```text
Change row-type rules, define clean-data candidate policy, run MinerU, call LLMs, OCR, or re-extract PDFs.
```

---

## 2. Required context

Read these files first:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
.skills/project_milestone_ledger.md

datefac_agent/README.md
docs/agent/348A_QA_EXCEL_INTAKE_AUDIT_RESULT_REVIEW.md
docs/agent/348A_R1_EVIDENCE_POLICY_REFINEMENT_RESULT.md
docs/agent/348A_R2_ROW_TYPE_CLASSIFICATION_RESULT.md
docs/agent/348A_R2_QA_ROW_TYPE_CLASSIFICATION_RESULT_REVIEW.md

docs/codex_tasks/348A_R2_QA_row_type_classification_result_review.md
```

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

Primary file to modify:

```text
datefac_agent/audit/unit_semantic_checker.py
```

Likely test file:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
```

Optional result doc:

```text
docs/agent/348A_R3_UNIT_CHECKER_FALSE_POSITIVE_REFINEMENT_RESULT.md
```

Avoid changing unrelated modules unless tests prove it is necessary.

---

## 5. Required behavior

The checker should not emit `monetary_unit_mismatch` for:

```text
净资产收益率(%)
净资产收益率
ROE(%)
ROA(%)
收益率(%)
毛利率(%)
净利率(%)
```

These are percentage/rate metrics.

The checker should still flag obvious monetary/ratio mismatches such as:

```text
营业收入(%)
净利润(%)
资产总计(%)
负债合计(%)
营业收入(倍)
净利润(倍)
```

The fix should prefer semantic precedence rather than one-off hardcoding:

```text
rate / percentage terms should override broad monetary tokens when the metric is clearly a rate metric.
```

---

## 6. Suggested rule direction

Improve term sets or classification order in `unit_semantic_checker.py`.

Possible approach:

```text
1. detect valuation metric
2. detect per-share metric
3. detect percentage/rate metric
4. detect monetary amount metric
5. if a metric is a percentage/rate metric, do not treat embedded broad words like 资产 as monetary by default
```

Add terms such as:

```text
收益率
净资产收益率
资产收益率
回报率
率
```

Be careful: not every string containing `率` should automatically be safe if it also has obviously incompatible units. Keep tests conservative.

---

## 7. Non-goals

Do not change row-type classifier behavior.

Do not change R1 evidence policy.

Do not define clean-data candidate policy.

Do not run MinerU.

Do not call LLM/VLM APIs.

Do not run OCR.

Do not re-extract the PDF.

Do not touch legacy `datefac/`.

Do not touch old `D:\_datefac` workspace or historical outputs.

Do not claim `client_ready` or `production_ready`.

Do not use:

```text
git add .
git add -A
git reset --hard
git checkout --
```

Use precise path staging only.

---

## 8. Tests

Add or update focused tests for:

1. `净资产收益率(%)` should not emit `monetary_unit_mismatch`.
2. `ROE(%)` should not emit `monetary_unit_mismatch`.
3. `营业收入(%)` should still emit `monetary_unit_mismatch`.
4. `资产总计(%)` should still emit `monetary_unit_mismatch`.
5. Existing per-share / valuation tests must still pass.

Do not require real Excel/PDF files in unit tests.

---

## 9. Validation

Run:

```powershell
cd D:\_datefac_agent

python -m py_compile datefac_agent\audit\unit_semantic_checker.py tests\agent\test_agent_excel_intake_audit_348a.py

python -m pytest tests\agent -q
```

Then rerun the real pilot to a new R3 output directory:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202606081823352906_1_331fresh_20260615_21591.pdf --excel-path D:\_datefac_agent\input\安井食品研报数据汇总.xlsx --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348a_r3
```

Do not overwrite old 348A, R1, or R2 output directories.

---

## 10. Expected R3 outcome

Expected qualitative outcome:

```text
unit_issue_count should drop from 1 to 0 if the only unit issue was 净资产收益率(%).
fail_count should drop from 1 to 0 if no other error-severity issue remains.
review_count may remain high because weak evidence is still review-worthy.
pass_count may remain 0 unless policy changes, which this task should not do.
```

Do not force clean rows in this task.

---

## 11. Expected changed files

Expected:

```text
datefac_agent/audit/unit_semantic_checker.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Optional:

```text
docs/agent/348A_R3_UNIT_CHECKER_FALSE_POSITIVE_REFINEMENT_RESULT.md
```

Do not commit output files.

---

## 12. Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. What unit-rule change was made.
5. py_compile result.
6. pytest result.
7. Real runner result and R3 output directory.
8. Manifest decision and key R3 metrics.
9. Whether `unit_issue_count` changed from 1 to 0.
10. Whether `fail_count` changed from 1 to 0.
11. Whether `净资产收益率(%)` no longer triggers `monetary_unit_mismatch`.
12. Whether `营业收入(%)` / `资产总计(%)` still trigger mismatch tests.
13. Whether row-type and evidence policies were left unchanged.
14. Whether legacy `datefac/` and old outputs were untouched.
15. Whether LLM/MinerU/OCR calls were zero.
16. `git status -sb`.
17. Recommended next task.

---

## 13. Likely next task

If R3 succeeds, likely next task:

```text
348A-R4 Clean Data Candidate Policy
```

R4 should decide whether selected `WEAK_EVIDENCE + no semantic issues` rows can enter internal clean-data candidates while still keeping client / production gates closed.
