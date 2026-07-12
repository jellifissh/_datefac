# 348N-R7CF project necessity ground-truth benchmark pilot report

## Task ID

```text
348N-R7CF project necessity ground-truth benchmark pilot
```

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward to b214b21; R7CF task doc updated.

git status -sb
PASS: clean after pull.
```

## Why feature development is paused

This task is not extending reconciliation features. It measures whether the project-necessity benchmark method can answer one narrow question: whether DateFac finds meaningful errors that MinerU and the existing extraction artifact do not already expose.

The benchmark is intentionally conservative:

- ground truth comes only from independently verified PDF evidence;
- MinerU and the Excel artifact are not treated as truth;
- only `ground_truth_review_status=VERIFIED` rows count toward metrics;
- if verified evidence is insufficient, the correct outcome is to ask for more ground-truth review instead of inflating a product conclusion.

## Input inventory

Searched only the explicit roots requested by the task:

```text
D:\_datefac_agent
D:\_datefac
E:\mineru_lab
E:\_datefac_toolbench
```

Inventory result:

- candidate report package identities discovered: `32`
- strict READY packages by inventory classification: `0`
- strict status distribution: `16 MISSING_MINERU_ARTIFACT`, `10 AMBIGUOUS_PAIRING`, `5 MISSING_PDF`, `1 MISSING_ORIGINAL_ARTIFACT`

The strict inventory contains many historical copies and partials. The pilot therefore uses one canonical Anjing Foods trio selected from the inventory, not every candidate identity.

## Selected reports

Selected benchmark report package:

```text
H3_AP202606081823352906_1
```

Canonical paths used for the one-report pilot:

- PDF: `E:\mineru_lab\input\H3_AP202606081823352906_1.pdf`
- MinerU JSON: `E:\mineru_lab\output_new\H3_AP202606081823352906_1\auto\H3_AP202606081823352906_1_content_list_v2.json`
- Original artifact: `D:\_datefac_agent\output\datefac_raw_material_anjing_foods.xlsx`

## Sampling plan

Deterministic high-value sampling was used on the selected report only.

Target:

- `20` to `30` cells

Actual sample:

- `30` cells

Coverage priority:

- revenue
- parent net profit / net profit
- EPS
- ROE
- PE / PB
- balance-sheet metrics
- cash-flow metrics
- units
- A / E / F periods
- footnote-sensitive rows

## Review pack schema

Generated local review pack:

```text
output/benchmark/r7cf_anjing_foods_ground_truth_review_pack.xlsx
```

Columns:

```text
report_id
pdf_basename
pdf_page
pdf_locator_or_bbox
statement_context
metric
period
unit
mineru_value
original_value
datefac_status
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

Ground-truth policy:

- machine-derived columns were populated automatically;
- truth fields were left blank because no independent PDF verification was performed in this coding turn;
- no ground truth was inferred from MinerU/Excel agreement.

## Ground-truth rules

- only rows marked `ground_truth_review_status=VERIFIED` count toward metrics;
- unverified rows are excluded from precision/recall and error counts;
- the benchmark does not count MinerU or Excel as truth;
- the benchmark does not fabricate verified cells.

## Benchmark implementation

Implemented files:

- `datefac_agent/benchmark/__init__.py`
- `datefac_agent/benchmark/project_necessity_benchmark_348n.py`
- `tools/build_project_necessity_benchmark_pack_348n.py`
- `tools/evaluate_project_necessity_benchmark_348n.py`
- `tests/benchmark/test_project_necessity_benchmark_348n.py`

Core behavior:

- inventories candidate report packages from explicit roots;
- classifies package readiness honestly;
- resolves a canonical benchmark trio for the Anjing Foods report;
- samples high-value comparison rows deterministically;
- writes the local review-pack workbook;
- reads a completed review pack;
- evaluates metrics only from `VERIFIED` rows;
- emits compact JSON and Markdown summaries.

## Metric definitions

- `verified_cell_count`: number of rows with `ground_truth_review_status=VERIFIED`
- `mineru_error_count`: verified rows where MinerU is not correct
- `original_error_count`: verified rows where the original artifact is not correct
- `both_wrong_same_value_count`: verified rows where both systems are wrong in the same way
- `both_wrong_different_value_count`: verified rows where both systems are wrong but disagree
- `datefac_true_positive_count`: DateFac flags a real error
- `datefac_false_positive_count`: DateFac flags a row with no verified error
- `datefac_false_negative_count`: DateFac does not flag a row with a verified error
- `datefac_true_negative_count`: DateFac does not flag a row with no verified error
- `precision`, `recall`, `false_positive_rate`: zero-division-safe ratios
- `high_severity_error_count`: verified rows with high/critical severity

## Decision rules

- `< 20 verified cells` -> `NEEDS_MORE_VERIFIED_CELLS`
- zero verified rows are still treated as insufficient evidence, not method invalidation
- repeated meaningful catches with acceptable false-positive rate can justify lightweight QA value
- almost no independent catches with no high-severity findings suggest low value
- never conclude full product value from one report

## Local generated files

Generated locally and not committed:

- `output/benchmark/r7cf_anjing_foods_ground_truth_review_pack.xlsx`
- `output/benchmark/r7cf_project_necessity_benchmark_summary.json`
- `output/benchmark/r7cf_project_necessity_benchmark_summary.md`

## Verified sample size

```text
0
```

## Current provisional result

```text
NEEDS_MORE_VERIFIED_CELLS
```

Reason: the pilot produced a valid 30-cell review pack, but no row was independently verified during this coding turn, so there is not enough truth evidence to score the benchmark.

## Limitations

- No independent PDF evidence was recorded as verified in this turn.
- The review pack remains truth-bounded and mostly blank in the ground-truth columns by design.
- The benchmark cannot yet make a strong product-necessity claim from zero verified cells.
- The generated workbook and summaries are local evidence only and are not committed.

## Decision

PASS for method implementation, but the benchmark outcome is provisional and not product-conclusive.

The safe conclusion is:

```text
NEEDS_MORE_VERIFIED_CELLS
```

## Recommended next task

```text
348N-R7CF-HUMAN complete Anjing Foods PDF ground-truth review
```

## Data Result / 数据结果

```text
Decision（任务结论）=PASS
build_result（构建结果）=PASS
test_result（测试结果）=PASS; benchmark targeted tests 12 passed, full tests/agent 823 passed
files_modified（修改文件数）=5
error_count（错误数）=0
candidate_report_package_count（候选报告包数量）=32
ready_report_package_count（可用完整报告包数量）=1
sampled_cell_count（抽样单元格数量）=30
verified_cell_count（已验证真值数量）=0
review_pack_result（复核包结果）=PASS; local workbook generated successfully
benchmark_metric_result（基准指标结果）=PASS; metrics computed from VERIFIED rows only, all zero because verified cells are absent
provisional_project_value_result（暂定项目价值结论）=NEEDS_MORE_VERIFIED_CELLS
boundary_check（边界检查）=PASS; no DB, no clean_data, no delivery/export, no MinerU/OCR/LLM/VLM, no readiness change
readiness_gates（就绪门）=CLOSED
recommended_next_task（推荐下一任务）=348N-R7CF-HUMAN complete Anjing Foods PDF ground-truth review
```
