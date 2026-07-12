# 348N-R7CF-HUMAN complete Anjing Foods PDF ground-truth review

## Goal

Complete independent PDF verification for the 30 sampled cells in the local review pack, then re-run the benchmark evaluator.

This is a human evidence task, not a coding task.

## Files

Open:

```text
D:\_datefac_agent\output\benchmark\r7cf_anjing_foods_ground_truth_review_pack.xlsx
E:\mineru_lab\input\H3_AP202606081823352906_1.pdf
```

Do not regenerate the review pack unless it is missing or corrupted.

## Review rule

For each of the 30 rows:

1. Use `pdf_page` and `pdf_locator_or_bbox` to find the source table in the PDF.
2. Read the value and unit directly from the PDF.
3. Do not infer truth from MinerU/Excel agreement.
4. Verify the metric, period, unit, decimal placement, sign, and A/E suffix.
5. If the PDF evidence is ambiguous, leave the row unverified and explain why.

## Fields to fill

Fill only these columns:

```text
pdf_ground_truth_value
pdf_ground_truth_unit
ground_truth_review_status
mineru_correct
original_correct
datefac_decision_correct
error_severity
evidence_note
reviewer_note
```

Use these values:

```text
ground_truth_review_status = VERIFIED
mineru_correct = TRUE or FALSE
original_correct = TRUE or FALSE
datefac_decision_correct = TRUE or FALSE
error_severity = NONE / LOW / MEDIUM / HIGH / CRITICAL
```

A row may remain unverified when the PDF is unclear. In that case:

```text
ground_truth_review_status = UNVERIFIED
```

and explain the reason in `reviewer_note`.

## DateFac decision correctness

Use this rule:

```text
If either MinerU or original is wrong, DateFac should flag the row.
If both are correct, DateFac should not flag the row.
```

Therefore:

```text
DateFac status != MATCH and a real error exists -> TRUE
DateFac status != MATCH and no real error exists -> FALSE
DateFac status == MATCH and a real error exists -> FALSE
DateFac status == MATCH and no real error exists -> TRUE
```

## Evidence note

Write a short independent note such as:

```text
PDF P3 ratios table, 总资产周转率 2026E = 0.8 次
```

Do not paste full table text or screenshots into the workbook.

## Minimum completion target

Complete at least 20 VERIFIED rows.

Prefer all 30.

## Evaluate after review

From `D:\_datefac_agent` run:

```text
python tools\evaluate_project_necessity_benchmark_348n.py --review-pack output\benchmark\r7cf_anjing_foods_ground_truth_review_pack.xlsx --summary-json output\benchmark\r7cf_project_necessity_benchmark_summary.json --summary-md output\benchmark\r7cf_project_necessity_benchmark_summary.md --candidate-report-package-count 32 --ready-report-package-count 1
```

Record the printed result:

```text
sampled_cell_count
verified_cell_count
provisional_project_value_result
```

Also read the generated summary and report:

```text
mineru_error_count
original_error_count
both_wrong_same_value_count
both_wrong_different_value_count
datefac_true_positive_count
datefac_false_positive_count
datefac_false_negative_count
datefac_true_negative_count
precision
recall
false_positive_rate
high_severity_error_count
```

## Boundaries

Do not change code in this task.

Do not run MinerU/OCR/LLM/VLM.

Do not commit the review pack, PDF, summary JSON, or summary Markdown.

Do not fabricate VERIFIED rows.

Do not mark a row VERIFIED unless the PDF evidence is independently readable.

## Completion response

Return:

```text
verified_cell_count=
mineru_error_count=
original_error_count=
both_wrong_same_value_count=
both_wrong_different_value_count=
datefac_true_positive_count=
datefac_false_positive_count=
datefac_false_negative_count=
datefac_true_negative_count=
precision=
recall=
false_positive_rate=
high_severity_error_count=
provisional_project_value_result=
```

Do not commit or push anything for this human review task.
