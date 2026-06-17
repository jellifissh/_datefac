# 348S Input Pairing Manifest

## Goal

Create a clear pairing manifest for the current `input/` directory so future real-workbook pilots do not guess PDF and Excel relationships from filenames alone.

The previous third workbook pilot was blocked because no third justified PDF + Excel pair existed.

This task is input-governance only:

- do not run the audit runner
- do not edit source code
- do not run MinerU, OCR, LLM, or VLM
- do not re-extract PDFs
- do not modify files under `input/` or `output/`

## Required context

Read:

```text
AGENTS.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
docs/agent/348S_THIRD_REAL_WORKBOOK_PILOT_RESULT.md
```

## Preflight

```powershell
cd D:\_datefac_agent
git pull --ff-only origin pivot/348-agent-foundation
git status -sb
git branch --show-current
```

Stop if the worktree is not clean.

## Input inventory

Inspect filenames under:

```text
D:\_datefac_agent\input
```

Record PDFs, Excel workbooks, and notes files.

Do not move, copy, edit, or delete input files.

Known current files from the blocked third pilot:

```text
PDF:
H3_AP202605231822706325_1.pdf
H3_AP202606081823352906_1_331fresh_20260615_21591.pdf

Excel:
H3_AP202605231822706325_1_提取结果.xlsx
安井食品研报数据汇总.xlsx
泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx

Other:
input/real_second_review/README_REAL_SECOND_REVIEW_INPUT.md
```

## Required manifest

Create:

```text
docs/agent/348S_INPUT_PAIRING_MANIFEST.md
```

The manifest should include a table with:

```text
pair_id
source_pdf
source_excel
status
used_in_task
pilot_eligible
selection_evidence
blocked_reason
notes
```

Suggested status values:

```text
MATCHED_USED
MATCHED_ELIGIBLE
UNMATCHED_PDF
UNMATCHED_EXCEL
NOT_A_PILOT_INPUT
UNCLEAR
```

Expected known pairs:

```text
pair_001:
  PDF: H3_AP202606081823352906_1_331fresh_20260615_21591.pdf
  Excel: 安井食品研报数据汇总.xlsx
  status: MATCHED_USED
  used_in_task: 348A first real workbook

pair_002:
  PDF: H3_AP202605231822706325_1.pdf
  Excel: H3_AP202605231822706325_1_提取结果.xlsx
  status: MATCHED_USED
  used_in_task: 348S second real workbook

unmatched:
  Excel: 泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
  status: UNMATCHED_EXCEL
  blocked_reason: missing source PDF
```

If new input files exist locally, include them accurately.

Do not force a pair.

## Third pilot readiness

The manifest must include one clear readiness value:

```text
READY_WITH_PAIR: <pair_id>
BLOCKED_NO_MATCHED_INPUT_PAIR
BLOCKED_PAIR_UNCLEAR
```

## Validation

Run:

```powershell
python -m pytest tests\agent -q
```

No Python files should be changed.

## Expected result report

Create:

```text
docs/agent/348S_INPUT_PAIRING_MANIFEST_RESULT.md
```

Include:

```text
Task ID
Input inventory summary
Manifest path
Pairs recorded
Unmatched files
Third pilot readiness
Validation result
Boundary discipline
Decision
Recommended next task
```

Decision values:

```text
348S_INPUT_PAIRING_MANIFEST_CREATED_BLOCKED_NO_THIRD_PAIR
348S_INPUT_PAIRING_MANIFEST_CREATED_WITH_ELIGIBLE_THIRD_PAIR
348S_INPUT_PAIRING_MANIFEST_BLOCKED_BY_INPUT_INSPECTION_ERROR
```

## Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Input files discovered.
5. Pairs recorded.
6. Unmatched files recorded.
7. Third pilot readiness result.
8. pytest result.
9. Whether source code was untouched.
10. Whether input/output files were untouched.
11. Whether LLM/MinerU/OCR calls were zero.
12. `git status -sb`.
13. Recommended next task.
