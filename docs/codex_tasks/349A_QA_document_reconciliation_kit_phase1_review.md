# 349A-QA document-reconciliation-kit phase 1 review

## Goal

Perform an independent QA review of the standalone `document-reconciliation-kit` extraction before any legacy DateFac deletion, archival notice, or repository split.

Plain Chinese: 这一轮只审查新工具包是否真的独立、精简、可安装、可运行、没有偷偷依赖旧 DateFac，也没有把真实数据和旧项目垃圾一起搬进来。不要继续加功能。

## Workspace

```text
D:\_datefac_agent
branch = extract/document-reconciliation-kit
implementation commit = 1fb0302
```

## Preflight

```text
git status -sb
git pull origin extract/document-reconciliation-kit
git status -sb
git log --oneline -8
```

Stop if the worktree is not clean after pull.

## Read first

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
docs/codex_tasks/349A_extract_document_reconciliation_kit_phase1.md
docs/agent/349A_DOCUMENT_RECONCILIATION_KIT_PHASE1_EXTRACTION_REPORT.md
document-reconciliation-kit/README.md
document-reconciliation-kit/pyproject.toml
```

Review every file under:

```text
document-reconciliation-kit/
```

Also compare behavior with the source modules that were extracted from:

```text
datefac_agent/reconciliation/mineru_original_reconciliation_348n.py
datefac_agent/reconciliation/real_artifact_compatibility_348n.py
datefac_agent/reconciliation/discrepancy_diagnosis_348n.py
datefac_agent/benchmark/project_necessity_benchmark_348n.py
```

The goal is behavioral preservation of useful generic capabilities, not line-for-line copying.

## Allowed tracked change

Create exactly one QA report:

```text
docs/agent/349A_QA_DOCUMENT_RECONCILIATION_KIT_PHASE1_REVIEW.md
```

No source, test, fixture, README, packaging, legacy DateFac, output, task, or configuration file may change in this QA task.

## Commit boundary review

Verify the implementation range:

```text
973e1899edaaffc988d8e5537785d38554f0bded..1fb0302
```

Expected:

```text
one implementation commit
24 added files
all implementation files are under document-reconciliation-kit/
one added implementation report under docs/agent/
no legacy file modified or deleted
```

Confirm there are no committed real PDFs, Excel workbooks, generated reports, local output directories, absolute D:/E: paths, secrets, credentials, or confidential report text.

## Standalone packaging review

Validate from the repository root and from outside the repository package directory.

Recommended isolated environment:

```text
python -m venv .tmp_349a_qa_venv
.tmp_349a_qa_venv\Scripts\python -m pip install --upgrade pip
.tmp_349a_qa_venv\Scripts\python -m pip install -e "document-reconciliation-kit[dev]"
```

Confirm:

```text
package imports without repository-root path hacks
doc-reconcile console script is installed
only declared runtime dependency is openpyxl
pytest is development-only
Python requirement is explicit
no datefac_agent import occurs
no import reaches legacy datefac modules
```

Delete the temporary virtual environment after validation. Do not commit it.

## MinerU adapter review

Confirm:

```text
page-grouped content_list_v2 input is supported
only intended table / explicit normalized record shapes are consumed
HTML rowspan and colspan expansion is deterministic
malformed or missing HTML fails safely
page/block/row/column/bbox/caption/footnote trace remains bounded and compact
full HTML is not retained in normalized records or reports
input objects are not mutated
record ordering is deterministic
```

Pay particular attention to rowspan behavior across rows and colspan behavior in period headers. A passing fixture must represent the behavior honestly rather than matching a flawed implementation.

## Excel adapter review

Confirm:

```text
read_only=True
data_only=True
workbook closes in finally
caller selects sheets explicitly
missing sheet selection fails clearly
period-header matrices expand deterministically
source trace contains sheet/row/column/locator
no workbook write occurs
no hidden DateFac sheet-name assumptions remain in the generic adapter
```

## Normalization and model review

Confirm:

```text
text normalization is generic by default
financial aliases live only in the optional profile
periods preserve A/E/F and supported quarterly/half-year forms
numeric normalization handles commas, percent signs, parenthesized negatives, and null/bool safely
unit normalization does not silently convert incompatible scales
preview length is bounded
stable hashes are deterministic
models do not contain clean_data, delivery, readiness, DB, queue, or DateFac-specific fields
```

## Reconciliation review

Confirm:

```text
default identity = context + metric_key + period
identity is configurable without accepting unsafe missing fields
MATCH
CONFLICT
LEFT_ONLY
RIGHT_ONLY
UNPARSEABLE
UNIT_REVIEW
```

Review duplicate-key handling carefully. Duplicate records must not be silently discarded or converted into a false MATCH.

Confirm:

```text
left/right inputs are not mutated
comparison output ordering is deterministic
unit mismatch is review-required
unparseable rows retain bounded evidence and compact trace
source-neutral naming is used
```

## Discrepancy report review

Confirm:

```text
related rows group deterministically
case IDs are stable
severity and recommended action mappings are coherent
JSON and Markdown are deterministic
only compact derived evidence and trace are rendered
unsafe output directories or unrelated existing files are not overwritten
no product readiness or automatic acceptance claim exists
```

## Benchmark review

Confirm:

```text
only VERIFIED rows count
unverified rows cannot become errors or correct rows implicitly
both-wrong-same-value and both-wrong-different-value are correct
precision/recall/false-positive rate are zero-division safe
review-pack schema validation is strict
benchmark remains generic and does not contain Anjing Foods or hard-coded local report paths
```

## CLI review

Exercise all three commands with anonymous temporary data:

```text
doc-reconcile compare
doc-reconcile report
doc-reconcile benchmark
```

Confirm:

```text
--help works
missing input returns nonzero
invalid input returns nonzero with a useful bounded message
compare refuses to overwrite an existing output
report/benchmark require a safe new or empty output directory
commands print compact useful results
no network, DB, OCR, MinerU runtime, LLM, VLM, Docker, Java, or agent framework is invoked
```

Do not use real local report artifacts for QA. Use only committed anonymous fixtures or temporary anonymous files.

## Test quality review

Do not judge only by `84 passed`.

Check that tests:

```text
assert real behavior rather than implementation trivia
cover negative paths
cover input nonmutation and deterministic ordering
cover rowspan/colspan edge cases
cover duplicate identities
cover unsafe overwrite refusal
cover VERIFIED-only benchmark accounting
contain no real paths or client data
```

Report weak or misleading tests even when all tests pass.

## Required validation

```text
python -m pip install -e "document-reconciliation-kit[dev]"
python -m pytest document-reconciliation-kit/tests -q
python -m document_reconciliation.cli --help
doc-reconcile --help
doc-reconcile compare --help
doc-reconcile report --help
doc-reconcile benchmark --help
python -c "from document_reconciliation import __version__; print(__version__)"
python -c "from pathlib import Path; p=Path('document-reconciliation-kit'); text='\n'.join(x.read_text(encoding='utf-8') for x in p.rglob('*.py')); assert 'datefac_agent' not in text"
python -c "from pathlib import Path; p=Path('document-reconciliation-kit'); text='\n'.join(x.read_text(encoding='utf-8', errors='ignore') for x in p.rglob('*') if x.is_file()); assert 'D:\\_datefac' not in text and 'E:\\mineru' not in text"
git diff 973e1899edaaffc988d8e5537785d38554f0bded..1fb0302 --stat
git diff 973e1899edaaffc988d8e5537785d38554f0bded..1fb0302 --name-status
git status -sb
git diff --check
```

If `document_reconciliation.__version__` is intentionally not exported, record that as a packaging usability issue rather than modifying code in QA.

## Decision rules

PASS only when:

```text
standalone installation is genuine
all capabilities are source-neutral
legacy DateFac remains untouched
no real data or local paths leaked
core behavior is deterministic and fail-safe
CLI output safety is sound
tests are meaningful
no critical packaging/API defect exists
```

Use `PASS_WITH_FOLLOWUP` for noncritical documentation, version export, API ergonomics, or missing edge-case tests.

Use `FAIL` for:

```text
legacy dependency
real data leak
unsafe overwrite
false MATCH caused by duplicate loss
broken rowspan/colspan behavior
unverified benchmark rows counted as truth
package not actually installable outside repository context
```

## Required report sections

```text
Task ID
Decision
Implementation range and file boundary
Standalone packaging review
MinerU adapter review
Excel adapter review
Normalization/model review
Reconciliation review
Discrepancy report review
Benchmark review
CLI review
Test quality review
Real-data and legacy exclusion review
Validation outputs
Findings by severity
Limitations
Recommended next task
Data Result / 数据结果
```

## Required Data Result

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=1
error_count（错误数）=
implementation_file_boundary_result（实现文件边界结果）=
standalone_install_review_result（独立安装审查结果）=
mineru_adapter_review_result（MinerU适配器审查结果）=
excel_adapter_review_result（Excel适配器审查结果）=
normalization_model_review_result（标准化与模型审查结果）=
reconciliation_review_result（对账审查结果）=
discrepancy_review_result（差异审查结果）=
benchmark_review_result（基准审查结果）=
cli_review_result（CLI审查结果）=
test_quality_review_result（测试质量审查结果）=
legacy_source_untouched（旧项目源代码未修改）=
real_data_exclusion_result（真实数据排除结果）=
recommended_next_task（推荐下一任务）=
```

Recommended next task when PASS or PASS_WITH_FOLLOWUP:

```text
349B standalone repository split and DateFac archival preparation
```

## Commit and push

```text
git add docs/agent/349A_QA_DOCUMENT_RECONCILIATION_KIT_PHASE1_REVIEW.md
git commit -m "docs: add 349A phase 1 QA review"
git push origin extract/document-reconciliation-kit
```

Stop after push.
