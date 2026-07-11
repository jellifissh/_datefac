# 348N-R7CE real discrepancy diagnosis and review report demo-only

## Goal

Turn the two raw review-required rows from R7CD into one human-readable discrepancy case and generate a real demo review report from the real MinerU JSON and DateFac workbook.

Plain Chinese: 现在不再扩解析范围，也不回 DB 线。把真实 smoke 里 `总资产周转率 2026E` 的两条异常合并成一个“差异案件”，解释清楚哪边有值、哪边解析失败、证据在哪、为什么不能自动进 clean_data，并输出一份人能看的 Markdown + JSON 复核报告。

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

## Real local inputs

Use the same real local basenames already proven in R7CD:

```text
H3_AP202606081823352906_1_content_list_v2.json
datefac_raw_material_anjing_foods.xlsx
```

Do not commit either complete input.

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
docs/agent/348N_R7CD_QA_REAL_ARTIFACT_COMPATIBILITY_SLICE_REVIEW.md
docs/agent/348N_R7CD_REAL_MINERU_ARTIFACT_COMPATIBILITY_SLICE_DEMO_ONLY_REPORT.md
datefac_agent/reconciliation/real_artifact_compatibility_348n.py
tools/run_real_artifact_reconciliation_348n.py
```

## Scope

Create a demo-only discrepancy diagnosis layer on top of R7CD results.

Required pipeline:

```text
real reconciliation result
-> select review-required rows
-> group rows by statement_context + metric + period
-> collapse related raw rows into one discrepancy case
-> assign diagnosis category
-> render compact JSON and Markdown review report
```

For the real smoke, the two raw review-required rows should collapse into one case:

```text
statement_context = ratios_per_share
metric = total_asset_turnover
period = 2026E
raw statuses = ORIGINAL_ONLY + UNPARSEABLE
case_count = 1
```

## Suggested files

```text
datefac_agent/reconciliation/discrepancy_diagnosis_348n.py
tests/agent/test_discrepancy_diagnosis_348n.py
tools/run_real_discrepancy_review_report_348n.py
docs/agent/348N_R7CE_REAL_DISCREPANCY_DIAGNOSIS_AND_REVIEW_REPORT_DEMO_ONLY_REPORT.md
```

A small targeted update to the R7CD compatibility module is allowed only if required to expose safe structured fields already present in memory. Do not alter matching behavior unless a test proves a real defect.

## Required discrepancy case shape

Each case should include at least:

```text
case_id
statement_context
metric
metric_display_name
period
raw_statuses
diagnosis_category
severity
review_required
blocked_delivery_reason
mineru_value
original_value
normalized_unit
mineru_evidence_preview
original_evidence_preview
mineru_source_trace
original_source_trace
recommended_action
clean_data_eligible
readiness_gates
```

## Required diagnosis categories

Support at least:

```text
VALUE_CONFLICT
SOURCE_PARSE_FAILURE
MISSING_MINERU_EVIDENCE
MISSING_ORIGINAL_VALUE
UNIT_MISMATCH
UNRESOLVED_MULTI_CAUSE
```

For the real `总资产周转率 2026E` case, expected diagnosis should be `SOURCE_PARSE_FAILURE` or `UNRESOLVED_MULTI_CAUSE`, with a clear reason. Do not auto-approve `0.8` into clean_data.

## Required report behavior

Generate two demo outputs to a caller-supplied local directory:

```text
real_discrepancy_review_report.json
real_discrepancy_review_report.md
```

The Markdown report must contain:

```text
input basenames
reconciliation summary
raw review row count
collapsed discrepancy case count
one section per discrepancy case
side-by-side MinerU vs original values
bounded evidence previews
source trace summary
why review is required
recommended human action
explicit note: no clean_data write performed
readiness remains CLOSED
```

The JSON must contain compact structured cases only. Do not embed full HTML tables, full workbook rows, full raw JSON, source_text, or binary content.

## CLI

Add a CLI accepting:

```text
--mineru-json <path>
--original-xlsx <path>
--output-dir <path>
```

Required CLI behavior:

```text
run reconciliation
build discrepancy cases
write the two demo report files
print only compact counts and output paths
refuse to overwrite unrelated existing files
return nonzero on missing input or unsafe output path
```

Use a dedicated local demo output directory. Generated files must not be committed.

## Tests

Cover at least:

```text
review rows group by statement_context + metric + period
ORIGINAL_ONLY + UNPARSEABLE collapse into one case
case_id is deterministic
VALUE_CONFLICT maps correctly
UNIT_REVIEW maps to UNIT_MISMATCH
missing-side statuses map correctly
bounded previews remain bounded
full raw artifacts are excluded
clean_data_eligible is false
readiness gates remain closed
Markdown rendering is deterministic
JSON rendering is deterministic
CLI writes exactly two expected files
CLI does not overwrite unrelated files
input objects are not mutated
R7CD and R7CC tests remain green
full tests/agent remains green
```

## Real local smoke

Run once on the same real inputs. Expected high-level result:

```text
comparison_row_count = 416
raw_review_required_count = 2
discrepancy_case_count = 1
metric = 总资产周转率 / total_asset_turnover
period = 2026E
original_value = 0.8
clean_data_write_count = 0
```

Record only counts, basenames, diagnosis category, bounded evidence examples, and output filenames in the task report. Do not commit generated review reports.

## Boundaries

Do not modify DB/repository/schema/migration work. Do not write clean_data. Do not trigger delivery/export beyond the two explicit local demo report files. Do not run MinerU/OCR/LLM/VLM. Do not open readiness gates. Do not commit real inputs or generated outputs. Do not use broad Git staging.

## Validation

```text
python -m py_compile datefac_agent/reconciliation/discrepancy_diagnosis_348n.py
python -m py_compile tools/run_real_discrepancy_review_report_348n.py
python -m py_compile tests/agent/test_discrepancy_diagnosis_348n.py
python -m pytest tests/agent/test_discrepancy_diagnosis_348n.py -q
python -m pytest tests/agent/test_real_artifact_compatibility_348n.py -q
python -m pytest tests/agent/test_mineru_original_reconciliation_348n.py -q
python -m pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

## Report sections

```text
Task ID
Preflight
Files reviewed
R7CD-QA recap
Mainline business goal
Files changed
Discrepancy grouping behavior
Diagnosis behavior
Case schema
Markdown report behavior
JSON report behavior
CLI behavior
Real local smoke
Output safety
clean_data/readiness boundary
Validation outputs
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
discrepancy_grouping_result（差异分组结果）=
diagnosis_result（诊断结果）=
review_report_json_result（JSON复核报告结果）=
review_report_markdown_result（Markdown复核报告结果）=
real_local_smoke_result（真实本地smoke结果）=
raw_review_required_count（原始待复核条数）=
discrepancy_case_count（差异案件数）=
clean_data_write_count（clean_data写入数）=0
boundary_check（边界检查）=
readiness_gates（就绪门）=CLOSED
recommended_next_task（推荐下一任务）=348N-R7CE-QA real discrepancy diagnosis and review report review
```

## Commit and push

Stage only the allowed changed source, test, CLI, and task report files explicitly, then:

```text
git commit -m "feat: add real discrepancy diagnosis report"
git push origin pivot/348-agent-foundation
```

Stop after push.
