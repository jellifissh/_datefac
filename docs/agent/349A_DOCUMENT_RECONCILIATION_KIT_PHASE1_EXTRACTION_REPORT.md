# 349A document-reconciliation-kit Phase 1 extraction report

## Task ID

```text
349A extract document-reconciliation-kit phase 1
```

## Decision

PASS. A small standalone Python project now provides deterministic document-output reconciliation without importing, modifying, or depending on the DateFac application package.

## Scope and legacy boundary

The existing DateFac repository remains preserved as an archive on this branch. This Phase 1 change adds only:

- `document-reconciliation-kit/`
- this extraction report

No existing `datefac_agent/`, legacy `datefac/`, tests, task documents, output directories, local report packages, readiness flags, database code, or delivery logic changed.

## Standalone package

`document-reconciliation-kit` installs independently with Python 3.11+, `openpyxl`, and `pytest` as the only development dependency.

The `doc-reconcile` command exposes three explicit-path subcommands:

```text
doc-reconcile compare --left <json> --right <json-or-xlsx> --output <json>
doc-reconcile report --comparison <json> --output-dir <dir>
doc-reconcile benchmark --review-pack <xlsx> --output-dir <dir>
```

The CLI rejects missing inputs, refuses to overwrite an existing comparison file, and requires a new empty directory for report and benchmark output.

## Extracted capabilities

### MinerU adapter

- Handles page-grouped `content_list_v2` lists.
- Reads `table` blocks from `content.html`.
- Expands HTML `rowspan` and `colspan` deterministically.
- Keeps page, block, row, column, bbox, caption, and footnote trace metadata.
- Supports bounded evidence previews only; it does not retain full HTML output in derived records.

### Excel adapter

- Opens workbooks with `read_only=True` and `data_only=True`.
- Accepts caller-selected worksheets and rejects missing selections.
- Expands a period-header matrix into normalized records.
- Preserves sheet, row, column, and locator source trace.
- Closes workbooks in `finally` blocks.

### Source-neutral core

- `models.py` supplies typed normalized and comparison dataclasses.
- `normalization.py` supplies generic text, period, numeric, unit, preview, and stable-hash helpers.
- A/E/F and quarterly/half-year period suffixes are retained.
- `profiles/financial.py` holds optional financial aliases; the generic core does not require it.
- `reconciliation.py` compares the configurable identity key, defaulting to `context + metric_key + period`.
- Generic statuses are `MATCH`, `CONFLICT`, `LEFT_ONLY`, `RIGHT_ONLY`, `UNPARSEABLE`, and `UNIT_REVIEW`.

### Discrepancy and benchmark

- Related review-required rows collapse into deterministic cases with severity, diagnosis, action, compact trace, bounded evidence, JSON, and Markdown output.
- Product-specific acceptance and readiness fields are absent. The standalone case model uses neither `clean_data_eligible` nor delivery/readiness gates.
- Benchmark review packs use `VERIFIED`-only metric calculation, system error counts, both-wrong counts, precision, recall, false-positive rate, and zero-division-safe ratios.

## Fixtures and test coverage

Only two anonymous compact fixtures are committed:

- a two-page MinerU-style table sample;
- a normalized JSON record list.

No real reports, workbooks, client data, local outputs, full HTML dumps, or local paths appear in the standalone project.

The suite contains 84 focused tests covering:

- HTML table row/column spans and page-grouped table parsing;
- read-only Excel parsing and source trace;
- numeric, unit, text, and A/E/F period normalization;
- context separation, all six comparison statuses, input nonmutation, and ordering;
- deterministic case grouping, bounded evidence, compact JSON/Markdown rendering, and safe output directories;
- `VERIFIED`-only benchmark metrics, both systems wrong in the same value, and zero-division behavior;
- CLI help, missing-input failure, comparison output safety, report generation, and benchmark generation.

## Validation

```text
python -m pip install -e "document-reconciliation-kit[dev]"
PASS

python -m py_compile document-reconciliation-kit/src/document_reconciliation/models.py ...
PASS

python -m pytest document-reconciliation-kit/tests -q
PASS: 84 tests

python -m document_reconciliation.cli --help
PASS

doc-reconcile --help
PASS

python -c "from pathlib import Path; p=Path('document-reconciliation-kit'); assert 'datefac_agent' not in '\n'.join(x.read_text(encoding='utf-8') for x in p.rglob('*.py'))"
PASS
```

## Boundary review

- No `datefac_agent` imports in standalone Python sources.
- No hard-coded `D:` or `E:` paths.
- No real report, workbook, MinerU artifact, or output artifact committed.
- No network, database, OCR, MinerU runtime, LLM, VLM, agent framework, queue, Docker, or Java dependency.
- No PDF extraction, review queue persistence, clean-data decision, delivery export, or readiness integration.

## Remaining limitations

- This is a Phase 1 deterministic reconciliation toolkit, not a production extraction service.
- The MinerU adapter intentionally converts only structured table blocks and explicit normalized paragraph records; free-text semantic extraction remains out of scope.
- Unit conversion is not automatic; unit differences are conservatively routed to `UNIT_REVIEW`.
- Reports contain compact derived evidence and source trace, not full raw input artifacts.

## Recommended next task

```text
349A-QA document-reconciliation-kit phase 1 review
```

## Data Result / 数据结果

```text
Decision（任务结论）=PASS
build_result（构建结果）=PASS
test_result（测试结果）=PASS; 84 focused standalone tests passed
files_modified（修改文件数）=24
error_count（错误数）=0
standalone_install_result（独立安装结果）=PASS; editable installation succeeded
mineru_adapter_result（MinerU适配器结果）=PASS; page-grouped tables, HTML spans, trace, and bounded previews covered
excel_adapter_result（Excel适配器结果）=PASS; read-only selected-sheet matrix expansion and close-safe loading covered
normalization_result（标准化结果）=PASS; text, A/E/F period, numeric, unit, preview, and stable hash behavior covered
reconciliation_result（对账结果）=PASS; source-neutral identity and all six statuses covered
discrepancy_result（差异报告结果）=PASS; deterministic grouped cases and compact JSON/Markdown reports covered
benchmark_result（基准评估结果）=PASS; VERIFIED-only metrics, both-wrong counts, and zero-division safety covered
cli_result（CLI结果）=PASS; compare/report/benchmark help and safety paths covered
legacy_source_untouched（旧项目源代码未修改）=PASS
real_data_exclusion_result（真实数据排除结果）=PASS; anonymous fixtures only
recommended_next_task（推荐下一任务）=349A-QA document-reconciliation-kit phase 1 review
```
