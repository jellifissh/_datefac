# 348S Third Workbook Pilot

## 中文说明

本任务目标：在已经通过两份真实 workbook 和 348F fixture QA 后，选择第三份真实 PDF + Excel workbook，验证当前 `datefac_agent` 审计链路是否继续泛化。

这不是调规则任务。

这不是 MinerU 任务。

这不是重新抽 PDF 任务。

先只做第三样本 pilot：识别可用输入、匹配 PDF/Excel、运行现有 runner、输出结果报告。

---

## 1. Goal

Run a third real workbook pilot for the current DateFac Agent Excel intake audit workflow.

The task should answer:

```text
Can the current 348A/348S pipeline handle a third real workbook without new rule changes?
```

If it fails or produces poor metrics, report the failure clearly.

Do not patch rules in this task.

---

## 2. Required context

Read only:

```text
AGENTS.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
docs/agent/348F_QA_FIXTURE_HARVEST_REVIEW.md
docs/agent/348S_R2_QA_UNIT_PERIOD_RESIDUAL_REFINEMENT_REVIEW.md
```

Do not read broad legacy docs unless needed for a narrow path check.

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

## 4. Input discovery

Inspect:

```text
D:\_datefac_agent\input
```

Find candidate real inputs:

```text
*.pdf
*.xlsx
```

Do not modify input files.

Do not move input files.

Do not create synthetic workbook data.

The third pilot must not reuse the two already-used pairs:

```text
H3_AP202606081823352906_1_331fresh_20260615_21591.pdf + 安井食品研报数据汇总.xlsx
H3_AP202605231822706325_1.pdf + H3_AP202605231822706325_1_提取结果.xlsx
```

If there is no clearly matched third PDF + Excel pair, do not fake one. Create a blocked report explaining the discovered candidates and why no valid third pair was selected.

Possible known unmatched workbook from earlier discovery:

```text
泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
```

Only use it if a matching source PDF is present and can be justified by file name or metadata.

---

## 5. Candidate selection rules

Select one third sample pair using this priority:

1. Exact or near-exact filename match between PDF and Excel.
2. Same report/company identifier in both filenames.
3. Existing README or notes in input directory proving the pair.
4. If uncertain, stop and report `THIRD_WORKBOOK_PAIR_UNCLEAR`.

Record:

```text
selected_source_pdf
selected_source_excel
selection_reason
skipped_candidates
```

---

## 6. Run existing audit workflow

Use the existing runner or tool used for 348A/348S Excel intake audit.

Do not change source code.

Do not change audit rules.

Do not change clean candidate policy.

Write to a new task-specific output directory, for example:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348s_third_<safe_sample_id>
```

Do not overwrite old 348A / 348S / R1 / R2 / 348F outputs.

---

## 7. Required metrics

Collect from manifest / run summary / output files:

```text
decision
sheet_count
row_count_total
row_count_audited
pass_count
review_count
fail_count
issue_count_total
unit_issue_count
period_issue_count
valuation_issue_count
evidence_issue_count
strict_financial_table_row_count
market_reference_row_count
narrative_assertion_count
unknown_row_count
clean_data_row_count
review_queue_row_count
internal_clean_candidate_count
internal_reference_candidate_count
narrative_review_count
review_required_count
excluded_from_clean_data_count
client_ready
production_ready
formal_client_export_allowed
llm_api_call_count
mineru_run_count
ocr_run_count
```

Also summarize the top issue codes in `review_queue.csv` when present.

---

## 8. Baseline regression

Run the existing tests:

```powershell
python -m py_compile datefac_agent\intake\excel_intake.py datefac_agent\audit\unit_semantic_checker.py datefac_agent\audit\period_alignment_checker.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
```

Expected currently:

```text
29 passed
```

If no source code changed, py_compile is still useful as a sanity check.

---

## 9. Expected report

Create:

```text
docs/agent/348S_THIRD_REAL_WORKBOOK_PILOT_RESULT.md
```

Include:

```text
Task ID
Candidate inventory
Selected PDF/Excel pair
Selection reason
Skipped candidates
Output directory
Verified metrics
Top issue codes
Comparison to first and second sample
Whether unknown_row_count is acceptable
Whether clean_data_row_count is nonzero
Whether review_queue is explainable
Gate discipline
External-call discipline
Validation results
Decision
Recommended next task
```

Suggested decision values:

```text
348S_THIRD_WORKBOOK_PILOT_CONFIRMED_GENERALIZATION
348S_THIRD_WORKBOOK_PILOT_CONFIRMED_NEEDS_SCHEMA_REFINEMENT
348S_THIRD_WORKBOOK_PILOT_BLOCKED_NO_MATCHED_INPUT_PAIR
348S_THIRD_WORKBOOK_PILOT_CONFIRMED_NEEDS_UNIT_PERIOD_REVIEW
348S_THIRD_WORKBOOK_PILOT_CONFIRMED_NEEDS_ROWTYPE_REVIEW
```

Choose one primary decision.

---

## 10. Non-goals

Do not run MinerU.

Do not call LLM/VLM APIs.

Do not run OCR.

Do not re-extract PDFs.

Do not edit source code.

Do not add fixtures.

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

## 11. Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Candidate PDF/Excel inventory.
5. Selected third pair and selection reason.
6. Skipped candidates and reasons.
7. Output directory.
8. Third sample verified metrics.
9. Top review queue issue codes.
10. Whether unknown rows are acceptable.
11. Whether clean data is nonzero.
12. Whether review queue is explainable.
13. py_compile result.
14. pytest result.
15. Whether source code was untouched.
16. Whether output files were not committed.
17. Whether LLM/MinerU/OCR calls were zero.
18. `git status -sb`.
19. Recommended next task.

---

## 12. Likely next tasks

If third sample generalizes:

```text
348S-QA Third Workbook Pilot Review
```

If blocked by unmatched input:

```text
348S-Input Pairing Manifest
```

If third sample exposes schema issues:

```text
348S-R3 Targeted Third Workbook Schema Refinement
```
