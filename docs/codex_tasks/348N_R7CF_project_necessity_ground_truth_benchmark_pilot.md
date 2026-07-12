# 348N-R7CF project necessity ground-truth benchmark pilot

## Correction

Do not assume five ready report packages exist.

Current proven complete package count is one:

```text
H3_AP202606081823352906_1 PDF
+ MinerU content_list_v2 JSON
+ datefac_raw_material_anjing_foods.xlsx
```

Other PDFs or prior candidate outputs may exist locally, but they must not be treated as ready benchmark packages unless the required PDF, MinerU artifact, and original artifact can actually be paired.

Plain Chinese: 先别幻想五份。现在明确跑通的只有安井食品这一份。R7CF 先做“库存盘点 + 单报告独立真值试验”，确认这个 benchmark 方法本身能不能跑，再决定是否补第二份、第三份。

## Goal

Answer two narrower questions:

```text
1. 当前本地到底有多少个可用的完整报告包？
2. 对安井食品这一份，PDF 独立真值抽检后，MinerU、原始 Excel、DateFac 各自表现如何？
```

Do not continue reconciliation feature development in this task.

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
docs/agent/348N_R7CE_REAL_DISCREPANCY_DIAGNOSIS_AND_REVIEW_REPORT_DEMO_ONLY_REPORT.md
docs/agent/348N_R7CD_QA_REAL_ARTIFACT_COMPATIBILITY_SLICE_REVIEW.md
```

## Phase A: inventory only

Search only known project roots:

```text
D:\_datefac_agent
D:\_datefac
E:\mineru_lab
E:\_datefac_toolbench
```

Build an inventory of candidate report packages.

A package is `READY` only when all three are present and can be paired by stable report identity:

```text
original PDF
MinerU content_list_v2 JSON
existing/original Excel or JSON artifact
```

Possible statuses:

```text
READY
MISSING_PDF
MISSING_MINERU_ARTIFACT
MISSING_ORIGINAL_ARTIFACT
AMBIGUOUS_PAIRING
```

Do not create missing MinerU outputs in this task. Do not run MinerU.

## Phase B: one-report ground-truth pilot

Use only the proven Anjing Foods package unless inventory finds another genuinely READY package.

Target sample:

```text
20 to 30 high-value cells from the one ready report
```

Cover a mix of:

```text
Revenue
parent net profit / net profit
EPS
ROE
PE / PB
balance-sheet metrics
cash-flow metrics
units
historical A periods
forecast E periods
footnote-sensitive values
```

Ground truth must come from independent PDF evidence review.

Never treat agreement between MinerU and Excel as proof of correctness.

## Required local review pack

Generate locally and do not commit:

```text
output/benchmark/r7cf_anjing_foods_ground_truth_review_pack.xlsx
```

Required columns:

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

Populate machine-derived columns automatically.

Leave truth fields blank unless the PDF evidence is independently and unambiguously verified.

## Required implementation

Suggested files:

```text
datefac_agent/benchmark/project_necessity_benchmark_348n.py
tools/build_project_necessity_benchmark_pack_348n.py
tools/evaluate_project_necessity_benchmark_348n.py
tests/benchmark/test_project_necessity_benchmark_348n.py
docs/agent/348N_R7CF_PROJECT_NECESSITY_GROUND_TRUTH_BENCHMARK_PILOT_REPORT.md
```

Create `datefac_agent/benchmark/__init__.py` only if needed.

Required behavior:

```text
inventory candidate report packages from explicit roots
classify package readiness honestly
build the one-report local review pack
read a completed review pack
calculate metrics only from VERIFIED rows
refuse to count unverified rows as truth
produce compact local JSON/Markdown summary
```

## Metrics

Calculate at least:

```text
ready_report_package_count
sampled_cell_count
verified_cell_count
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

## Decision rules

This one-report pilot cannot justify a full-product conclusion.

Allowed provisional results:

```text
BENCHMARK_METHOD_VALID
BENCHMARK_METHOD_INVALID
NEEDS_MORE_VERIFIED_CELLS
ONE_REPORT_SUGGESTS_LIGHTWEIGHT_QA_VALUE
ONE_REPORT_SUGGESTS_LOW_VALUE
```

Rules:

```text
verified_cell_count < 20 -> NEEDS_MORE_VERIFIED_CELLS
credible independent catches with low false positives -> ONE_REPORT_SUGGESTS_LIGHTWEIGHT_QA_VALUE
almost no independent catches and no high-severity errors -> ONE_REPORT_SUGGESTS_LOW_VALUE
never conclude full product value from one report
```

## Tests

Cover at least:

```text
package readiness classification
ambiguous pairing rejection
deterministic sampling
unverified rows excluded from metrics
both systems agreeing on the same wrong value counted correctly
DateFac false positive and false negative accounting
zero-division-safe metrics
one-report decision rules
review pack schema
no real input artifact committed
```

## Boundaries

Do not add DB, repository, schema, migration, clean_data writes, delivery/export workflow, readiness changes, MinerU execution, OCR, LLM, or VLM.

Do not commit generated benchmark files, PDFs, MinerU outputs, or real workbooks.

Do not fabricate ground truth.

Do not use broad Git staging.

## Validation

```text
python -m py_compile datefac_agent/benchmark/project_necessity_benchmark_348n.py
python -m py_compile tools/build_project_necessity_benchmark_pack_348n.py
python -m py_compile tools/evaluate_project_necessity_benchmark_348n.py
python -m py_compile tests/benchmark/test_project_necessity_benchmark_348n.py
python -m pytest tests/benchmark/test_project_necessity_benchmark_348n.py -q
python -m pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

## Required Data Result

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
candidate_report_package_count（候选报告包数量）=
ready_report_package_count（可用完整报告包数量）=
sampled_cell_count（抽样单元格数量）=
verified_cell_count（已验证真值数量）=
review_pack_result（复核包结果）=
benchmark_metric_result（基准指标结果）=
provisional_project_value_result（暂定项目价值结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=CLOSED
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
if verified_cell_count < 20:
348N-R7CF-HUMAN complete Anjing Foods PDF ground-truth review

else:
348N-R7CF-QA one-report benchmark review
```

## Commit and push

Stage only the allowed source, tools, tests, and task report files explicitly, then:

```text
git commit -m "feat: add one-report ground-truth benchmark pilot"
git push origin pivot/348-agent-foundation
```

Stop after push.
