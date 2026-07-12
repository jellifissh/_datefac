# 348N-R7CF project necessity ground-truth benchmark pilot

## Goal

Stop extending reconciliation features for now. Build a small independent benchmark that answers one business question:

```text
Does DateFac find meaningful errors that MinerU and the existing extraction artifact do not already expose?
```

Plain Chinese: R7CE 已经能把一个差异案件讲清楚，但这还不能证明项目值得继续。下一步不是继续修报告，也不是回 DB 线，而是拿多份真实研报做独立真值抽检，决定项目是继续、缩小，还是归档。

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

## Benchmark principle

Do not treat MinerU or the existing Excel as ground truth.

Ground truth must come from independent PDF evidence review.

The benchmark should compare:

```text
PDF evidence truth
vs MinerU-derived value
vs existing/original artifact value
vs DateFac reconciliation decision
```

## Input inventory

Search only known project roots for real report packages:

```text
D:\_datefac_agent
D:\_datefac
E:\mineru_lab
E:\_datefac_toolbench
```

Select 5 reports if available, otherwise select the maximum available number and state the limitation.

Each selected report should preferably have:

```text
original PDF
MinerU content_list_v2 JSON
existing/original Excel or JSON artifact
```

Do not commit complete real PDFs, MinerU outputs, or workbooks.

## Sampling plan

Sample 20 high-value cells per report when possible.

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
cross-page or merged-cell tables
footnote-sensitive values
```

Target pilot size:

```text
5 reports x 20 cells = 100 independently reviewed cells
```

If fewer reports or cells are available, continue with the largest honest sample and report the exact size.

## Required local review pack

Generate a caller-local, uncommitted Excel workbook:

```text
output/benchmark/r7cf_project_necessity_benchmark_review_pack.xlsx
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

Populate all machine-derived columns automatically.

Leave manual truth fields blank unless the PDF evidence can be verified independently and unambiguously during this task.

Never infer ground truth merely because MinerU and the original artifact agree.

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
inventory report packages from explicit roots
pair PDF, MinerU artifact, and original artifact by stable report identity
sample deterministic high-value metric-period cells
write the local Excel review pack
read a completed review pack
calculate benchmark metrics only from rows marked ground_truth_review_status=VERIFIED
refuse to count unverified rows as truth
produce a compact local JSON/Markdown benchmark summary
```

## Required benchmark metrics

Calculate at least:

```text
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
manual_review_minutes_if_available
```

## Required decision rule

The local benchmark summary must produce one of:

```text
CONTINUE_AS_FULL_RECONCILIATION_PRODUCT
CONTINUE_AS_LIGHTWEIGHT_QA_TOOL
PAUSE_FOR_MORE_DATA
ARCHIVE_OR_REPOSITION
```

Use conservative rules. At minimum:

```text
fewer than 30 verified cells -> PAUSE_FOR_MORE_DATA
very low independent error incidence and no high-severity catches -> ARCHIVE_OR_REPOSITION
useful catches but low volume -> CONTINUE_AS_LIGHTWEIGHT_QA_TOOL
repeated meaningful catches across reports with acceptable false-positive rate -> CONTINUE_AS_FULL_RECONCILIATION_PRODUCT
```

Do not claim product value from one report or one discrepancy case.

## Tests

Cover at least:

```text
stable package pairing
missing artifact handling
deterministic sampling
unverified rows excluded from metrics
both systems agreeing on the same wrong value is counted correctly
DateFac false positive and false negative accounting
zero-division-safe precision/recall
conservative decision rules
review pack schema
no real input artifact committed
```

## Boundaries

Do not add DB, repository, schema, migration, clean_data write, delivery/export workflow, readiness change, MinerU execution, OCR, LLM, or VLM.

Do not commit generated benchmark workbook, benchmark summaries, PDFs, real MinerU files, or real original workbooks.

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

## Required report sections

```text
Task ID
Preflight
Why feature development is paused
Input inventory
Selected reports
Sampling plan
Review pack schema
Ground-truth rules
Benchmark implementation
Metric definitions
Decision rules
Local generated files
Verified sample size
Current provisional result
Limitations
Decision
Recommended next task
Data Result / 数据结果
```

## Required Data Result

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
report_package_count（报告包数量）=
sampled_cell_count（抽样单元格数量）=
verified_cell_count（已验证真值数量）=
review_pack_result（复核包结果）=
benchmark_metric_result（基准指标结果）=
project_value_decision（项目价值决策）=
boundary_check（边界检查）=
readiness_gates（就绪门）=CLOSED
recommended_next_task（推荐下一任务）=
```

Recommended next task depends on verified sample size:

```text
if verified_cell_count < 30:
348N-R7CF-HUMAN complete independent PDF ground-truth review

otherwise:
348N-R7CF-QA project necessity benchmark review
```

## Commit and push

Stage only the allowed source, tools, tests, and task report files explicitly, then:

```text
git commit -m "feat: add project necessity benchmark pilot"
git push origin pivot/348-agent-foundation
```

Stop after push.
