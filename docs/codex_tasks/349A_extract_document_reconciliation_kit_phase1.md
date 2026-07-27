# 349A extract document-reconciliation-kit phase 1

## Decision

DateFac product development is stopped.

Do not delete or rewrite the legacy DateFac code in this task. Preserve the existing repository as an archive and extract the reusable parts into a small standalone Python project on this branch.

Plain Chinese: 这一轮不是继续 DateFac，也不是把旧仓库大删一遍。先在新目录里做出一个能独立安装、运行、测试的小项目。等新项目确认可用后，再决定旧代码是否只保留归档分支。

## Workspace

```text
repository = jellifissh/_datefac
branch = extract/document-reconciliation-kit
local workspace = D:\_datefac_agent
```

## Preflight

```text
git status -sb
git fetch origin
git switch extract/document-reconciliation-kit
git pull origin extract/document-reconciliation-kit
git status -sb
```

Stop if the worktree is not clean.

## Read first

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
项目进展大白话说明.md
docs/agent/348N_R7CC_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_DEMO_REPORT.md
docs/agent/348N_R7CD_REAL_MINERU_ARTIFACT_COMPATIBILITY_SLICE_DEMO_ONLY_REPORT.md
docs/agent/348N_R7CE_REAL_DISCREPANCY_DIAGNOSIS_AND_REVIEW_REPORT_DEMO_ONLY_REPORT.md
docs/agent/348N_R7CF_PROJECT_NECESSITY_GROUND_TRUTH_BENCHMARK_PILOT_REPORT.md
```

Review source assets:

```text
datefac_agent/reconciliation/mineru_original_reconciliation_348n.py
datefac_agent/reconciliation/real_artifact_compatibility_348n.py
datefac_agent/reconciliation/discrepancy_diagnosis_348n.py
datefac_agent/benchmark/project_necessity_benchmark_348n.py
tools/run_real_artifact_reconciliation_348n.py
tools/run_real_discrepancy_review_report_348n.py
tools/build_project_necessity_benchmark_pack_348n.py
tools/evaluate_project_necessity_benchmark_348n.py
tests/agent/test_mineru_original_reconciliation_348n.py
tests/agent/test_real_artifact_compatibility_348n.py
tests/agent/test_discrepancy_diagnosis_348n.py
tests/benchmark/test_project_necessity_benchmark_348n.py
```

## New standalone project

Create:

```text
document-reconciliation-kit/
├─ README.md
├─ pyproject.toml
├─ src/
│  └─ document_reconciliation/
│     ├─ __init__.py
│     ├─ models.py
│     ├─ normalization.py
│     ├─ reconciliation.py
│     ├─ discrepancy.py
│     ├─ benchmark.py
│     ├─ cli.py
│     ├─ adapters/
│     │  ├─ __init__.py
│     │  ├─ mineru.py
│     │  └─ excel.py
│     └─ profiles/
│        ├─ __init__.py
│        └─ financial.py
├─ tests/
│  ├─ fixtures/
│  │  ├─ mineru_table_sample.json
│  │  └─ original_rows_sample.json
│  ├─ test_normalization.py
│  ├─ test_adapters.py
│  ├─ test_reconciliation.py
│  ├─ test_discrepancy.py
│  └─ test_benchmark.py
└─ examples/
   └─ README.md
```

Add task report:

```text
docs/agent/349A_DOCUMENT_RECONCILIATION_KIT_PHASE1_EXTRACTION_REPORT.md
```

## Product scope

The new project is a deterministic document-output reconciliation toolkit.

It should support this small pipeline:

```text
MinerU JSON or normalized record list
+ Excel workbook or normalized record list
-> common record model
-> deterministic comparison
-> discrepancy cases
-> JSON / Markdown review report
-> optional ground-truth benchmark pack and metrics
```

The new project is not:

```text
DateFac product
financial delivery platform
Agent framework
review_queue persistence service
DB application
Spring Boot application
production-ready extraction service
```

## Reusable functionality to extract

### MinerU adapter

Extract and clean up:

```text
page-grouped content_list_v2 support
table blocks with content.html
HTML table expansion
caption / footnote / bbox / page source trace
rowspan and colspan handling when present
bounded evidence preview
```

Do not depend on real local files.

### Excel adapter

Extract and clean up:

```text
openpyxl read_only=True and data_only=True loading
caller-selected sheets
matrix-to-record expansion
sheet / row / column source trace
workbook close safety
```

Do not hard-code Anjing Foods paths.

### Normalization

Keep generic normalization in `normalization.py`:

```text
text compaction
period normalization with A/E/F suffix preservation
numeric normalization
unit normalization
bounded preview
stable hashing
```

Keep finance-specific aliases and statement/sheet profiles in:

```text
profiles/financial.py
```

The generic core must not require the financial profile.

### Reconciliation

Use generic status names:

```text
MATCH
CONFLICT
LEFT_ONLY
RIGHT_ONLY
UNPARSEABLE
UNIT_REVIEW
```

Compare on a configurable identity key. The default should be:

```text
context + metric_key + period
```

Do not use names such as MinerU-only/original-only in the generic core. Source-specific display labels may be supplied by the caller.

### Discrepancy cases

Keep:

```text
grouping related raw rows into one case
deterministic case_id
diagnosis categories
severity
recommended action
bounded evidence
compact source trace
JSON rendering
Markdown rendering
```

Rename product-specific fields:

```text
clean_data_eligible -> auto_accept_eligible
blocked_delivery_reason -> blocked_resolution_reason
readiness_gates -> remove from the standalone data model
```

Do not carry DateFac readiness flags into the new package.

### Benchmark

Keep only reusable benchmark pieces:

```text
review-pack schema
VERIFIED-only metric calculation
system error counts
both-systems-wrong counts
true positive / false positive / false negative / true negative
precision / recall / false-positive rate
zero-division safety
```

Remove:

```text
Anjing Foods constants
D:/E: hard-coded paths
DateFac product-value decision constants
project-specific inventory roots
R7CF task identifiers
```

## CLI

Expose one console command through `pyproject.toml`:

```text
doc-reconcile
```

Required subcommands:

```text
doc-reconcile compare --left <json> --right <json-or-xlsx> --output <json>
doc-reconcile report --comparison <json> --output-dir <dir>
doc-reconcile benchmark --review-pack <xlsx> --output-dir <dir>
```

Phase 1 may restrict `compare` to MinerU JSON on the left and Excel/normalized JSON on the right, but the internal reconciliation API must remain source-neutral.

CLI requirements:

```text
explicit input paths
nonzero exit on missing input
safe output directory handling
no overwrite of unrelated files
compact terminal summary
no network calls
```

## Data model

Use typed dataclasses where they improve clarity.

Suggested record fields:

```text
source
context
metric_key
metric_display_name
period
normalized_value
normalized_unit
evidence_preview
source_trace
parse_status
```

Suggested comparison fields:

```text
context
metric_key
metric_display_name
period
left_value
right_value
left_unit
right_unit
status
reason
review_required
evidence_preview
source_trace
```

Keep dictionaries at public serialization boundaries if that makes CLI JSON simpler.

## Tests

Target 50 to 100 focused tests, not hundreds of repetitive contract tests.

Must cover:

```text
MinerU page-grouped table parsing
HTML rowspan/colspan behavior
Excel read-only parsing
period A/E/F preservation
numeric normalization
unit normalization
context separation
MATCH / CONFLICT / LEFT_ONLY / RIGHT_ONLY / UNPARSEABLE / UNIT_REVIEW
input nonmutation
deterministic output ordering
deterministic case_id
case grouping
bounded evidence
full raw artifact exclusion
JSON/Markdown deterministic rendering
VERIFIED-only benchmark metrics
both sides agreeing on the same wrong value
precision/recall zero division
CLI missing-input failure
CLI safe output behavior
```

Use only small anonymous fixtures. Do not copy real reports, real workbooks, local output files, full HTML dumps, or client data.

## Dependency policy

Prefer:

```text
Python >= 3.11
standard library
openpyxl
pytest as development dependency
```

Do not add web frameworks, DB libraries, queues, Agent frameworks, LLM SDKs, OCR libraries, MinerU runtime, Docker, or Java dependencies.

## Legacy boundary

In this task, do not delete or modify existing DateFac source modules, legacy tests, task documents, outputs, or project history.

The only allowed tracked changes are:

```text
document-reconciliation-kit/**
docs/agent/349A_DOCUMENT_RECONCILIATION_KIT_PHASE1_EXTRACTION_REPORT.md
```

Do not add a root archive banner yet. Do not archive the GitHub repository yet. First prove the extracted kit works independently.

## Validation

From repository root:

```text
python -m pip install -e "document-reconciliation-kit[dev]"
python -m pytest document-reconciliation-kit/tests -q
python -m document_reconciliation.cli --help
doc-reconcile --help
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

Also run a static check proving the standalone package does not import from `datefac_agent`:

```text
python -c "from pathlib import Path; p=Path('document-reconciliation-kit'); assert 'datefac_agent' not in '\n'.join(x.read_text(encoding='utf-8') for x in p.rglob('*.py'))"
```

## Required report result

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
standalone_install_result（独立安装结果）=
mineru_adapter_result（MinerU适配器结果）=
excel_adapter_result（Excel适配器结果）=
normalization_result（标准化结果）=
reconciliation_result（对账结果）=
discrepancy_result（差异报告结果）=
benchmark_result（基准评估结果）=
cli_result（CLI结果）=
legacy_source_untouched（旧项目源代码未修改）=
real_data_exclusion_result（真实数据排除结果）=
recommended_next_task（推荐下一任务）=349A-QA document-reconciliation-kit phase 1 review
```

## Commit and push

Stage only explicit allowed paths:

```text
git add document-reconciliation-kit
git add docs/agent/349A_DOCUMENT_RECONCILIATION_KIT_PHASE1_EXTRACTION_REPORT.md
git commit -m "feat: extract document reconciliation kit"
git push origin extract/document-reconciliation-kit
```

Stop after push.
