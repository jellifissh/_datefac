# 348N-R7CE real discrepancy diagnosis and review report demo-only

## Task ID

```text
348N-R7CE real discrepancy diagnosis and review report demo-only
```

Task type: demo-only implementation.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward 4ba9c83..250a252; R7CE task doc added.

git status -sb
PASS: clean after pull.
```

## Files reviewed

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/348N_R7CE_real_discrepancy_diagnosis_and_review_report_demo_only.md`
- `docs/agent/348N_R7CD_QA_REAL_ARTIFACT_COMPATIBILITY_SLICE_REVIEW.md`
- `docs/agent/348N_R7CD_REAL_MINERU_ARTIFACT_COMPATIBILITY_SLICE_DEMO_ONLY_REPORT.md`
- `datefac_agent/reconciliation/real_artifact_compatibility_348n.py`
- `tools/run_real_artifact_reconciliation_348n.py`

## R7CD-QA recap

R7CD-QA confirmed the real-artifact compatibility slice reads the real MinerU JSON and DateFac workbook safely, preserves period/context/unit identity, produces reproducible counts, and leaves two review-required rows in one `总资产周转率 2026E` discrepancy cluster.

R7CD real smoke baseline:

```text
comparison_row_count=416
match_count=414
original_only_count=1
unparseable_count=1
review_required_count=2
```

## Mainline business goal

R7CE stays on the reconciliation mainline and does not return to DB or persistence work. Its goal is to turn raw review-required rows into a human-readable discrepancy case and local demo review report, without approving any value into clean_data.

## Files changed

Created four R7CE files:

- `datefac_agent/reconciliation/discrepancy_diagnosis_348n.py`
- `tools/run_real_discrepancy_review_report_348n.py`
- `tests/agent/test_discrepancy_diagnosis_348n.py`
- `docs/agent/348N_R7CE_REAL_DISCREPANCY_DIAGNOSIS_AND_REVIEW_REPORT_DEMO_ONLY_REPORT.md`

No R7CD compatibility behavior was changed.

## Discrepancy grouping behavior

`build_discrepancy_cases(...)` selects only `review_required` rows and groups them by:

```text
statement_context + metric_key + period
```

For the real smoke, the two raw rows collapse into one case:

```text
statement_context=ratios_per_share
metric=total_asset_turnover
metric_display_name=总资产周转率
period=2026E
raw_statuses=ORIGINAL_ONLY, UNPARSEABLE
case_count=1
```

The deterministic case id is:

```text
r7ce:fa0baad9689f81c9813e9150
```

## Diagnosis behavior

Implemented diagnosis categories:

- `VALUE_CONFLICT`
- `SOURCE_PARSE_FAILURE`
- `MISSING_MINERU_EVIDENCE`
- `MISSING_ORIGINAL_VALUE`
- `UNIT_MISMATCH`
- `UNRESOLVED_MULTI_CAUSE`

The real `总资产周转率 2026E` case is diagnosed as:

```text
diagnosis_category=SOURCE_PARSE_FAILURE
severity=MEDIUM_HIGH
recommended_action=REQUEST_REEXTRACTION
```

Reason: the MinerU-side row cannot be normalized, while the workbook side preserves corrected value `0.8`; this remains review-bound and is not auto-approved.

## Case schema

Each case includes:

- `case_id`
- `statement_context`
- `metric`
- `metric_display_name`
- `period`
- `raw_statuses`
- `diagnosis_category`
- `severity`
- `review_required`
- `blocked_delivery_reason`
- `mineru_value`
- `original_value`
- `normalized_unit`
- `mineru_evidence_preview`
- `original_evidence_preview`
- `mineru_source_trace`
- `original_source_trace`
- `recommended_action`
- `clean_data_eligible`
- `readiness_gates`

For the real case:

```text
mineru_value=null
original_value=0.8
normalized_unit=times
clean_data_eligible=false
```

## Markdown report behavior

The Markdown demo report contains:

- input basenames only;
- reconciliation summary;
- raw review row count;
- collapsed discrepancy case count;
- one section per case;
- side-by-side MinerU and original values;
- bounded evidence previews;
- source trace summary;
- why review is required;
- recommended human action;
- explicit no-clean-data and readiness-closed notes.

Generated local filename:

```text
real_discrepancy_review_report.md
```

## JSON report behavior

The JSON demo report contains compact structured metadata and cases. It does not include full HTML tables, full workbook rows, full raw JSON, source_text, binary content, DB payloads, or clean_data payloads.

Generated local filename:

```text
real_discrepancy_review_report.json
```

## CLI behavior

Added CLI:

```text
tools/run_real_discrepancy_review_report_348n.py
```

Required arguments:

```text
--mineru-json <path>
--original-xlsx <path>
--output-dir <path>
```

The CLI:

- requires explicit input paths;
- writes exactly two demo report files;
- prints compact counts and output paths only;
- refuses output directories containing unrelated existing files;
- returns nonzero on missing input or unsafe output path.

## Real local smoke

Command run:

```text
python tools/run_real_discrepancy_review_report_348n.py --mineru-json E:\mineru_lab\output_new\H3_AP202606081823352906_1\auto\H3_AP202606081823352906_1_content_list_v2.json --original-xlsx D:\_datefac_agent\output\datefac_raw_material_anjing_foods.xlsx --output-dir D:\_datefac_agent\output\comparison\anjing_foods_r7ce_demo
```

Compact output:

```text
comparison_row_count=416
raw_review_required_count=2
discrepancy_case_count=1
diagnosis_category=SOURCE_PARSE_FAILURE
output_json=D:\_datefac_agent\output\comparison\anjing_foods_r7ce_demo\real_discrepancy_review_report.json
output_markdown=D:\_datefac_agent\output\comparison\anjing_foods_r7ce_demo\real_discrepancy_review_report.md
```

Safe bounded evidence examples:

```text
MinerU: Ratios & Per Share | 总资产周转率 | 2026E | 次
Original: Ratios & Per Share | 总资产周转率 | 2026E | 0.8 次；P3原文“0.08.8”按表格语境修正为0.8
```

Source trace summary:

```text
MinerU locator=page:3:block:3:row:15:col:3
Original locator=sheet:Ratios_Per_Share:row:14:col:4
```

## Output safety

The generated demo reports were written only under the caller-supplied local output directory:

```text
D:\_datefac_agent\output\comparison\anjing_foods_r7ce_demo
```

They are not staged or committed. The task report records only counts, basenames, diagnosis category, bounded evidence examples, and output filenames.

## clean_data/readiness boundary

PASS. R7CE does not write clean_data, does not create delivery/export artifacts beyond the two explicit local demo reports, does not call DB persistence, does not add repository/schema/migration code, and does not open readiness gates.

Readiness remains:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

## Validation outputs

```text
python -m py_compile datefac_agent/reconciliation/discrepancy_diagnosis_348n.py
PASS

python -m py_compile tools/run_real_discrepancy_review_report_348n.py
PASS

python -m py_compile tests/agent/test_discrepancy_diagnosis_348n.py
PASS

python -m pytest tests/agent/test_discrepancy_diagnosis_348n.py -q
PASS: 10 passed in 0.95s

python -m pytest tests/agent/test_real_artifact_compatibility_348n.py -q
PASS: 10 passed in 0.57s

python -m pytest tests/agent/test_mineru_original_reconciliation_348n.py -q
PASS: 11 passed in 0.09s

python -m pytest tests/agent -q
PASS: 823 passed in 2.95s

python tools/run_real_discrepancy_review_report_348n.py --mineru-json E:\mineru_lab\output_new\H3_AP202606081823352906_1\auto\H3_AP202606081823352906_1_content_list_v2.json --original-xlsx D:\_datefac_agent\output\datefac_raw_material_anjing_foods.xlsx --output-dir D:\_datefac_agent\output\comparison\anjing_foods_r7ce_demo
PASS: compact count output reproduced

git status -sb
PASS before staging: only allowed R7CE files are untracked/modified

git diff --stat
PASS before staging

git diff --name-only
PASS before staging

git diff --check
PASS: no whitespace errors
```

## Limitations

- This is still demo-only report generation, not production review UI.
- It does not change reconciliation matching behavior.
- It does not auto-repair the MinerU parse issue.
- It does not write clean_data or delivery exports.
- It does not add DB persistence, schema, repository, migrations, or readiness integration.
- It does not run MinerU/OCR/LLM/VLM.

## Decision

PASS. R7CE collapses the two real R7CD review-required rows into one human-readable discrepancy case, diagnoses it as `SOURCE_PARSE_FAILURE`, generates local Markdown and JSON demo review reports, and keeps clean_data/readiness/persistence boundaries closed.

## Recommended next task

```text
348N-R7CE-QA real discrepancy diagnosis and review report review
```

## Data Result / 数据结果

```text
Decision（任务结论）=PASS
build_result（构建结果）=PASS
test_result（测试结果）=PASS; R7CE targeted tests 10 passed, R7CD tests 10 passed, R7CC tests 11 passed, full tests/agent 823 passed
files_modified（修改文件数）=4
error_count（错误数）=0
discrepancy_grouping_result（差异分组结果）=PASS; 2 raw review-required rows collapsed into 1 case by statement_context + metric + period
diagnosis_result（诊断结果）=PASS; real case diagnosed as SOURCE_PARSE_FAILURE
review_report_json_result（JSON复核报告结果）=PASS; compact structured JSON generated locally
review_report_markdown_result（Markdown复核报告结果）=PASS; human-readable Markdown generated locally
real_local_smoke_result（真实本地smoke结果）=PASS; comparison_row_count=416, raw_review_required_count=2, discrepancy_case_count=1
raw_review_required_count（原始待复核条数）=2
discrepancy_case_count（差异案件数）=1
clean_data_write_count（clean_data写入数）=0
boundary_check（边界检查）=PASS; no DB, no clean_data, no production hook, no committed output, no MinerU/OCR/LLM/VLM run
readiness_gates（就绪门）=CLOSED
recommended_next_task（推荐下一任务）=348N-R7CE-QA real discrepancy diagnosis and review report review
```
