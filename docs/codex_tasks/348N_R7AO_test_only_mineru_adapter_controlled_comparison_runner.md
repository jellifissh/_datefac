# 348N-R7AO test-only MinerU adapter controlled comparison runner

## Execution sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = single-run-data-analysis + no-commit
reason = R7AN completed the design for a test-only controlled dry-run. R7AO should execute the dry-run locally using the R7AM adapter shape, full local Anjing DateFac Excel, and full local MinerU content_list_v2, while writing only local output reports and committing nothing.
```

## Task Goal

Run a local, test-only controlled comparison using:

```text
DateFac candidate rows from Anjing Excel
MinerU content_list_v2 evidence blocks
R7AM test-only adapter module
```

Task ID:

```text
348N-R7AO test-only MinerU adapter controlled comparison runner
```

This is not production integration.

Do not modify production code.
Do not modify tests.
Do not commit output files.
Do not commit the local runner script.
Do not run MinerU, OCR, LLM, VLM, or real PDF extraction.
Do not add dependencies.
Do not open readiness gates.

---

## Required Inputs

DateFac Excel:

```text
D:\_datefac_agent\output\datefac_raw_material_anjing_foods.xlsx
```

MinerU artifact root candidates:

```text
E:\mineru331\smoke_output\H3_AP202606081823352906_1\auto
E:\mineru331\smoke_output\H3_AP202606081823352906_1
E:\mineru331\smoke_output
E:\mineru331
E:\mineru_lab
```

Required MinerU file pattern:

```text
*H3_AP202606081823352906_1*content_list_v2.json
```

Optional cross-check files:

```text
*H3_AP202606081823352906_1*content_list.json
*H3_AP202606081823352906_1*.md
```

If the DateFac Excel or content_list_v2 cannot be resolved to exactly one usable file, stop as BLOCKED and report candidate paths. Do not guess.

---

## Required Preflight

Run and report:

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -12
```

If worktree is not clean after pull, stop and report.

---

## Required Read Order

Read:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348N_R7AN_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_DRY_RUN_DESIGN.md
docs/agent/348N_R7AM_QA_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REVIEW.md
docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md
```

Review and reuse read-only:

```text
tests/agent/mineru_artifact_adapter_348n.py
tests/agent/test_mineru_artifact_adapter_348n.py
tests/agent/fixtures/mineru_artifacts/anjing_minimal_content_list_v2__r7am.json
```

Local R7AL outputs may be read if present, but must not be committed:

```text
D:\_datefac_agent\output\comparison\anjing_foods_datefac_vs_mineru\
```

---

## Local Output Location

Create local output directory only:

```text
D:\_datefac_agent\output\comparison\anjing_foods_mineru_adapter_r7ao\
```

Allowed local output files:

```text
run_r7ao_mineru_adapter_comparison.py
r7ao_mineru_adapter_comparison_report.xlsx
r7ao_mineru_adapter_comparison_summary.md
r7ao_mineru_adapter_evidence_rows.csv
r7ao_mineru_adapter_unmatched_rows.csv
r7ao_mineru_adapter_run_metadata.json
```

These files must not be committed or staged.

---

## Runner Requirements

Create a local runner script under the local output directory:

```text
D:\_datefac_agent\output\comparison\anjing_foods_mineru_adapter_r7ao\run_r7ao_mineru_adapter_comparison.py
```

The runner should:

1. Resolve the DateFac Excel path exactly.
2. Resolve exactly one MinerU `content_list_v2.json` file.
3. Import and reuse:

```text
tests.agent.mineru_artifact_adapter_348n
```

4. Load MinerU v2 blocks through the adapter shape.
5. Read all DateFac Excel sheets.
6. Detect the likely candidate rows sheet.
7. Normalize rows into:

```text
row_id
metric_name
period
value
unit
source_page / page_number
source_document_id
raw_text
source_sheet
```

8. Compare candidate rows against adapter evidence blocks.
9. Write local xlsx/csv/md/json reports.
10. Print a final Data Result.

Do not import production DateFac pipeline modules unless the task explicitly requires a read-only enum or model and doing so creates no side effects. Prefer self-contained local analysis plus R7AM adapter.

---

## Candidate Row Normalization Requirements

Read all Excel sheets and report sheet names/columns/row counts.

Candidate field inference may include:

```text
metric_name / 指标 / 指标名称 / name
period / 期间 / 年份 / 会计年度 / reporting_period
value / 数值 / amount / extracted_value
unit / 单位
page_number / source_page / 页码
source_document_id / document_id
raw_text / evidence / text / 原文
```

If fields are inferred, report the mapping.

Numeric normalization must handle:

```text
18,379 -> 18379
47.10 -> 47.10
+30.84% -> 30.84
-8.5 -> -8.5
5.37\6.30\7.23 -> split only if row semantics clearly allow it; otherwise mark review-required
亿元 / 百万元 / 元 / % / 倍 preserved as unit context
```

Rows missing metric, period, or value should not be VERIFIED.

Rows missing page number may use capped all-page search and must be flagged:

```text
source_page_status = NO_PAGE_CAPPED_SEARCH
```

---

## Matching Semantics

Use the R7AM adapter helper when suitable. If additional local matching is required, keep it conservative and document differences from R7AM.

Statuses:

```text
VERIFIED
UNVERIFIED
DISAGREED
AMBIGUOUS
MISSING_EVIDENCE
PARSE_SKIPPED
```

Required rules:

```text
VERIFIED requires value + metric + period support.
For table evidence, VERIFIED requires row metric + column period + value or an explicitly documented equivalent conservative rule.
value-only must not be VERIFIED.
metric-only must not be VERIFIED.
period-only must not be VERIFIED.
multiple plausible evidence blocks without disambiguation => AMBIGUOUS.
metric + period present with conflicting values => DISAGREED.
no usable block => MISSING_EVIDENCE.
parse/normalization failure => PARSE_SKIPPED.
```

Evidence priority:

```text
1. table html evidence
2. text paragraph evidence
3. title/header/footer/page number blocks only as weak context, never alone for VERIFIED
4. md fallback is optional and must not be primary trusted evidence
```

---

## Required Probe Examples

If these rows exist in the DateFac Excel, they must be explicitly reported:

```text
2026Q1 营业收入 = 47.10 亿元
2026Q1 归母净利润 = 5.63 亿元
2026Q1 扣非归母净利润 = 5.25 亿元
2026Q1 毛利率 = 24.99%
2026Q1 净利率 = 12.05%
2026E EPS = 5.37 元
2026E PE = 18.3 倍
2026E 营业收入 = 18,379 百万元
2026E 净利润 = 1,791 百万元
2026E ROE = 10.3%
2026E P/B = 1.9 倍
```

If missing from DateFac rows, report as probe_missing_from_datefac; do not inject them into candidate rows.

---

## Output Report Requirements

Excel report sheets:

```text
input_summary
sheet_detection
candidate_rows_normalized
mineru_adapter_blocks_index
comparison_results
source_text_evidence_draft
unmatched_or_review_required
probe_examples
run_metadata
```

Markdown summary must include:

```text
Task ID
Input paths resolved
R7AM adapter import result
DateFac sheet detection result
MinerU block count
Candidate row count
Status counts
Probe example results
Top VERIFIED examples
Top review-required examples
DISAGREED / AMBIGUOUS / MISSING_EVIDENCE examples
Differences from R7AL if comparable
Boundary statement
Recommended next task
Data Result / 数据结果
```

Run metadata JSON must include:

```text
timestamp
branch
commit_head
input_paths
resolved_mineru_content_list_v2_path
candidate_sheet
row_count
block_count
status_counts
readiness_gates
boundary_flags
```

---

## PASS / BLOCKED / FAIL Criteria

PASS if:

```text
DateFac Excel resolved
MinerU content_list_v2 resolved
R7AM adapter imported
candidate rows normalized
MinerU blocks indexed
comparison reports generated locally
status counts produced
probe examples reported
no production code/test/dependency changes
no output staged/committed
readiness_gates CLOSED
```

BLOCKED if:

```text
required input missing
multiple ambiguous MinerU v2 candidates cannot be disambiguated
DateFac Excel schema cannot be normalized enough for comparison
R7AM adapter import fails
worktree not clean before run
```

FAIL if:

```text
runner changes production code
commits output files
requires new dependency
uses MinerU/OCR/LLM/VLM
promotes VERIFIED to STRONG_EVIDENCE or clean_data
opens readiness gates
produces internally inconsistent status counts
```

---

## Boundary Rules

Forbidden:

```text
modify datefac_agent/
modify tests/
modify docs/ except none for this task
commit local runner
commit local reports
commit DateFac Excel
commit MinerU output
run MinerU
run OCR / LLM / VLM
run real PDF extraction
add dependencies
pip install / uv add / poetry add
promote VERIFIED to STRONG_EVIDENCE
promote VERIFIED to clean_data admission
open readiness gates
git add .
git add -A
```

Allowed:

```text
create local output directory under output/comparison/anjing_foods_mineru_adapter_r7ao/
create local runner and local reports there
read local input files
import tests.agent.mineru_artifact_adapter_348n
run validation commands
```

---

## Validation Commands

Run before and after as appropriate:

```text
python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
pytest tests/agent/test_mineru_artifact_adapter_348n.py -q
pytest tests/agent -q
python output/comparison/anjing_foods_mineru_adapter_r7ao/run_r7ao_mineru_adapter_comparison.py
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

Expected git status after run may show untracked local output files only if `.gitignore` does not ignore them. Do not stage them. If tracked files changed, stop and report.

---

## Commit / Push Rule

No commit.
No push.

This task is local dry-run only.

Stop after printing the final Data Result.

Data Result must include:

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
runner_result（runner结果）=
comparison_result（对比结果）=
datefac_rows_count（DateFac候选行数）=
mineru_adapter_blocks_count（MinerU adapter块数）=
verified_count（已验证数量）=
review_required_count（需复核数量）=
disagreed_count（冲突数量）=
ambiguous_count（歧义数量）=
missing_evidence_count（缺证据数量）=
parse_skipped_count（解析跳过数量）=
probe_examples_result（探针样例结果）=
output_report_xlsx（输出Excel报告路径）=
output_summary_md（输出Markdown报告路径）=
output_metadata_json（输出metadata路径）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should normally be:

```text
348N-R7AO-QA test-only MinerU adapter controlled comparison runner review
```
