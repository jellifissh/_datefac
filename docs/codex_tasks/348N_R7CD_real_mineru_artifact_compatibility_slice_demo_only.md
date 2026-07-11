# 348N-R7CD real MinerU artifact compatibility slice demo-only

## Goal

Move the reconciliation mainline from hand-written fixtures to the real Anjing Foods artifacts already used in this project.

Target inputs, by exact basename:

```text
H3_AP202606081823352906_1_content_list_v2.json
datefac_raw_material_anjing_foods.xlsx
```

The first file is a real MinerU 3.3.1 page-grouped `content_list_v2` artifact whose table blocks carry HTML in `content.html`. The second file is the existing eight-sheet DateFac extraction workbook.

Plain Chinese: 这一轮开始吃真实产物。把真实 MinerU 表格 JSON 和现有 DateFac Excel 产物读进来，转换为同一套记录，再做真实对账。不要再用手写的 Revenue/Net Profit 小样例冒充主线。

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
python -c "import openpyxl; print(openpyxl.__version__)"
```

Stop if the worktree is dirty or `openpyxl` is unavailable. Do not add dependencies.

## Locate the real local inputs

Search only known project/tool roots for the two exact basenames:

```text
D:\_datefac_agent
D:\_datefac
E:\mineru_lab
E:\_datefac_toolbench
```

Do not scan unrelated drives. Do not copy the complete real artifacts into Git. If either input cannot be found, stop before code changes and report the missing basename.

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
docs/agent/348N_R7CC_QA_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_REVIEW.md
docs/agent/348N_R7CC_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_DEMO_REPORT.md
datefac_agent/reconciliation/mineru_original_reconciliation_348n.py
tests/agent/test_mineru_original_reconciliation_348n.py
```

## Scope

Implement the minimum compatibility layer needed to reconcile real table data from both artifacts.

Required real MinerU support:

```text
top-level list of pages
blocks with type=table
content.html table markup
content.table_caption and bbox
header row containing periods such as 2024A, 2025A, 2026E
first column containing metric names
one normalized record per metric-period cell
```

Required Excel support:

```text
Financial_Data_Valuation
Balance_Sheet
Income_Statement
Cash_Flow
Ratios_Per_Share
```

Key_Info and Q1_Event_and_Text may be reported as deferred if they require separate paragraph/pair-field extraction.

## Important corrections to R7CC

R7CC currently strips periods to bare years and does not parse real table HTML. R7CD must:

```text
preserve 2024A / 2025A / 2026E rather than collapsing them to 2024 / 2025 / 2026
carry statement/table context so duplicate labels from different statements do not collide
strip unit suffixes from metric labels while preserving normalized unit metadata
support common label variants such as 营业收入(百万元), EPS(摊薄/元), ROE(%), P/E(倍), P/B(倍), 归属母公司净利润
reject or review unit-incompatible comparisons rather than silently matching them
```

## Suggested files

```text
datefac_agent/reconciliation/real_artifact_compatibility_348n.py
tests/agent/test_real_artifact_compatibility_348n.py
tests/agent/fixtures/mineru_original_reconciliation/real_content_list_v2_table_sample.json
tools/run_real_artifact_reconciliation_348n.py
docs/agent/348N_R7CD_REAL_MINERU_ARTIFACT_COMPATIBILITY_SLICE_DEMO_ONLY_REPORT.md
```

A small update to `mineru_original_reconciliation_348n.py` is allowed only when required for shared period/context comparison behavior. Do not commit a binary workbook fixture; build tiny workbook objects in tests with `openpyxl`.

## Required behavior

```text
parse real MinerU HTML tables with standard-library code or existing dependencies only
read the selected Excel sheets read-only
normalize metric, period, unit, statement context, value, evidence preview, and source trace
compare on statement_context + metric + period
produce MATCH / CONFLICT / MINERU_ONLY / ORIGINAL_ONLY / UNPARSEABLE and an explicit unit-review result when needed
build review_queue-style candidates for all review-required rows
never write clean_data
never call DB persistence
do not run MinerU, OCR, LLM, or VLM
```

## Real local smoke

Add a CLI that accepts:

```text
--mineru-json <path>
--original-xlsx <path>
```

Run it once against the two real local inputs. Print a compact summary only:

```text
mineru_record_count
original_record_count
comparison_row_count
match_count
conflict_count
mineru_only_count
original_only_count
unparseable_count
unit_review_count
review_required_count
```

Do not commit generated outputs or full rows. Record only counts, selected safe examples, and basenames in the report.

## Tests

Cover at least:

```text
real page-grouped content_list_v2 shape
HTML table matrix expansion
caption/bbox/page source trace
A/E period preservation
statement-context separation
Excel sheet matrix expansion
metric and unit normalization
matching real-style rows
conflict and missing-row detection
unit incompatibility goes to review
bounded evidence preview
input mutation safety
deterministic output
R7CC tests remain green
full tests/agent remains green
```

## Boundaries

Do not modify DB/repository work, clean_data, delivery/export, readiness gates, or production integration. Do not commit the complete MinerU JSON, PDF, Markdown, or real Excel workbook. Do not use broad Git staging.

## Allowed report result

The report must include:

```text
Decision=
build_result=
test_result=
files_modified=
error_count=
real_mineru_compatibility_result=
real_xlsx_compatibility_result=
html_table_expansion_result=
period_context_result=
unit_handling_result=
real_local_smoke_result=
comparison_summary=
boundary_check=
readiness_gates=CLOSED
recommended_next_task=348N-R7CD-QA real artifact compatibility slice review
```

## Validation

```text
python -m py_compile datefac_agent/reconciliation/real_artifact_compatibility_348n.py
python -m py_compile tools/run_real_artifact_reconciliation_348n.py
python -m py_compile tests/agent/test_real_artifact_compatibility_348n.py
python -m pytest tests/agent/test_real_artifact_compatibility_348n.py -q
python -m pytest tests/agent/test_mineru_original_reconciliation_348n.py -q
python -m pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

## Commit

Stage only the allowed changed files explicitly, then:

```text
git commit -m "feat: add real MinerU artifact compatibility slice"
git push origin pivot/348-agent-foundation
```

Stop after push.
