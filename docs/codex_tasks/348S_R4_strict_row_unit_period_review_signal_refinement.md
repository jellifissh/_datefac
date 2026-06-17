# 348S-R4 Strict Row Unit/Period Review Signal Refinement

## Goal

Refine the remaining strict-row review signals after R3C-QA validated unknown-row routing.

Current third workbook state after R3C:

```text
row_count_total = 158
clean_data_row_count = 94
review_queue_row_count = 64
unknown_row_count = 0
narrative_assertion_count = 46
unit_issue_count = 11
period_issue_count = 8
valuation_issue_count = 1
```

R3C-QA confirmed:

```text
348S_R3C_QA_CONFIRMED_UNKNOWN_ROW_REFINEMENT_VALID
```

This task should focus only on residual strict financial table review signals:

```text
percentage_unit_missing = 10
period_values_missing = 8
```

Do not revisit unknown-row routing unless a direct regression is found.

---

## Required context

Read:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348S_R3C_QA_UNKNOWN_ROW_REFINEMENT_REVIEW.md
docs/agent/348S_R3C_UNKNOWN_ROW_REFINEMENT_RESULT.md
docs/agent/348S_QA_THIRD_WORKBOOK_PILOT_REVIEW.md
```

Inspect the R3C output directory read-only before changing code:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348s_r3c_third_taihao_keji_doubaoai
```

---

## Preflight

```powershell
cd D:\_datefac_agent
git pull --ff-only origin pivot/348-agent-foundation
git status -sb
git branch --show-current
```

Stop if the worktree is not clean.

---

## Scope

Allowed to modify:

```text
datefac_agent/intake/excel_intake.py
datefac_agent/audit/unit_semantic_checker.py
datefac_agent/audit/period_alignment_checker.py
tests/agent/test_agent_excel_intake_audit_348a.py
tests/agent/fixtures/  # only compact fixture additions if useful
docs/agent/348S_R4_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_RESULT.md
```

Do not modify:

```text
evidence policy
clean candidate policy
legacy datefac/
input/
output/
```

---

## Required diagnosis

Before modifying code, inspect the R3C review queue and classify the residual strict-row signals.

Report:

```text
percentage_unit_missing rows by sheet, row, metric, value sample
period_values_missing rows by sheet, row, metric, value sample
which rows are true missing-unit or missing-period issues
which rows are table-title / section-anchor rows that should remain review-only
which rows are false positives due to implicit percentage metrics or embedded period labels
whether any proposed refinement would move rows into clean_data
```

Do not blindly remove review signals.

---

## Fix intent

Implement the smallest safe refinement.

Possible safe fixes:

```text
recognize known implicit percentage metrics such as 同比增速 / 毛利率 / 综合毛利率 / 净利润增速 when context clearly implies percentage rows
recognize period context in row labels or nearby headers only when confidence is high
route section-anchor rows more explicitly if they should not be treated as strict financial data
```

Avoid:

```text
loosening all percentage checks globally
removing period_values_missing globally
moving ambiguous rows into clean data without evidence
changing clean candidate acceptance rules
```

---

## Required tests

Add compact regression tests for any new behavior.

Tests should prove:

```text
true problematic strict rows still go to review
safe implicit percentage rows no longer create false positive percentage_unit_missing only when context supports it
safe period-context rows no longer create false positive period_values_missing only when context supports it
clean-data boundary is not widened accidentally
```

---

## Required validation

Run:

```powershell
python -m py_compile datefac_agent\intake\excel_intake.py datefac_agent\audit\unit_semantic_checker.py datefac_agent\audit\period_alignment_checker.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
```

Then rerun third workbook runner to a new output directory:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf --excel-path "D:\_datefac_agent\input\泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348s_r4_third_taihao_keji_doubaoai
```

If feasible, rerun first/second sample baselines or at least explain why pytest coverage is sufficient.

Do not commit output files.

---

## Expected result report

Create:

```text
docs/agent/348S_R4_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_RESULT.md
```

Include:

```text
Task ID
Files modified
Residual signal diagnosis
Narrow fix summary
Regression tests added
Validation results
Third workbook output directory
Before/after metrics
Clean-data QA
Review-queue QA
Unit signal QA
Period signal QA
Boundary discipline
Decision
Recommended next task
```

Decision values:

```text
348S_R4_CONFIRMED_STRICT_ROW_UNIT_PERIOD_REFINEMENT_VALID
348S_R4_CONFIRMED_PARTIAL_REFINEMENT_STILL_REVIEW_SIGNALS
348S_R4_CONFIRMED_NEEDS_DEEPER_STRICT_ROW_SCHEMA_REDESIGN
```

---

## Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Residual signal diagnosis.
5. Exact narrow fix made.
6. Tests added.
7. py_compile result.
8. pytest result.
9. Third workbook runner result.
10. Output directory.
11. Before/after metrics.
12. Clean-data QA after R4.
13. Review-queue QA after R4.
14. Unit signal QA.
15. Period signal QA.
16. Whether source changes stayed in allowed scope.
17. Whether output files were not committed.
18. Whether LLM/MinerU/OCR calls were zero.
19. git status -sb.
20. Recommended next task.
