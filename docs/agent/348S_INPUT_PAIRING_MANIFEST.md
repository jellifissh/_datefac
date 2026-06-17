# 348S Input Pairing Manifest

## Task ID

`348S Input Pairing Manifest`

## Scope

This manifest records current `input/` pairing evidence only.

Boundary discipline:

- no source-code changes
- no audit runner execution
- no `input/` mutation
- no `output/` mutation
- no MinerU / LLM / OCR calls
- no legacy `datefac/` touch

## Input Inventory

PDF files:

- `H3_AP202605231822706325_1.pdf`
- `H3_AP202606081823352906_1_331fresh_20260615_21591.pdf`

Excel files:

- `H3_AP202605231822706325_1_提取结果.xlsx`
- `安井食品研报数据汇总.xlsx`
- `泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx`

Other files:

- `input/real_second_review/README_REAL_SECOND_REVIEW_INPUT.md`

## Pairing Table

| pair_id | source_pdf | source_excel | status | used_in_task | pilot_eligible | selection_evidence | blocked_reason | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `pair_001` | `H3_AP202606081823352906_1_331fresh_20260615_21591.pdf` | `安井食品研报数据汇总.xlsx` | `MATCHED_USED` | `348A first real workbook` | `NO` | explicitly used by first real workbook pilot and subsequent 348A refinement chain | already consumed by first sample; third pilot cannot reuse it | stable matched pair |
| `pair_002` | `H3_AP202605231822706325_1.pdf` | `H3_AP202605231822706325_1_提取结果.xlsx` | `MATCHED_USED` | `348S second real workbook` | `NO` | explicitly used by second real workbook pilot and subsequent 348S refinement chain | already consumed by second sample; third pilot cannot reuse it | stable matched pair |
| `unmatched_excel_001` | `` | `泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx` | `UNMATCHED_EXCEL` | `` | `NO` | workbook is present in `input/`, but no corresponding source PDF exists in the same directory | missing source PDF | cannot justify a third real workbook pilot from this file alone |
| `note_001` | `` | `` | `NOT_A_PILOT_INPUT` | `` | `NO` | file is a note under `input/real_second_review/` rather than a workbook or source PDF | not a candidate input pair | retained as reference-only material |

## Unmatched Files

- `泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx`
- `input/real_second_review/README_REAL_SECOND_REVIEW_INPUT.md`

## Third Pilot Readiness

`BLOCKED_NO_MATCHED_INPUT_PAIR`

Reason:

- the only two justified PDF + Excel pairs are already used by the first and second real workbook pilots
- the remaining extra workbook does not have a matched source PDF in current `input/`
- no third independent PDF + Excel pair can be justified without adding new input evidence

## Selection Policy Notes

- pairing is based on existing task history and verified prior pilot usage, not filename guessing alone
- unmatched workbooks must remain unmatched unless a source PDF is present and can be justified
- readiness remains blocked until a third independent matched pair is added

