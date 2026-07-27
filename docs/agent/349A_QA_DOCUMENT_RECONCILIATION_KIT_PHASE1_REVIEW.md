# 349A-QA document-reconciliation-kit Phase 1 review

## Task ID

```text
349A-QA document-reconciliation-kit phase 1 review
```

## Decision

```text
FAIL
```

The standalone extraction is genuinely installable and cleanly bounded, but a caller can supply an unknown identity field and receive a false `MATCH` between unrelated records. This violates the required fail-safe behavior for configurable reconciliation identity keys.

## Implementation range and file boundary

Reviewed range:

```text
973e1899edaaffc988d8e5537785d38554f0bded..1fb0302
```

Result:

- Exactly one implementation commit was present: `1fb0302`.
- The commit added exactly 24 files.
- 23 implementation files are under `document-reconciliation-kit/`.
- The only remaining file is the intended Phase 1 extraction report under `docs/agent/`.
- The range contains additions only. No legacy source, existing test, output, task, configuration, or project-history file was modified or deleted.

## Standalone packaging review

PASS with one nonblocking usability finding.

- A fresh temporary virtual environment installed `document-reconciliation-kit[dev]` successfully.
- The isolated environment installed only the declared runtime dependency `openpyxl`; `pytest` is under the `dev` optional extra.
- Python requirement is explicitly `>=3.11`.
- From outside the repository package directory, `import document_reconciliation` resolved through the installed editable package and `doc-reconcile --help` ran successfully.
- The package source contains no `datefac_agent` import and no legacy `datefac` import.
- `from document_reconciliation import __version__` fails because `__version__` is not exported. This is a P2 packaging ergonomics issue, not the release-blocking defect.

## MinerU adapter review

PASS.

- Page-grouped `content_list_v2` input is consumed as page lists containing block lists.
- Table blocks read only `content.html`; non-table blocks are ignored unless they carry explicit normalized `records`.
- The HTML parser expands `rowspan` and `colspan` into a deterministic grid. The committed fixture exercises a two-row header with both a row span and a column span.
- Empty or malformed table content yields no records rather than fabricated records.
- Derived traces retain page, block, row, column, locator, bbox, caption preview, and footnote preview.
- Normalized records and block summaries exclude full HTML. Input nonmutation is covered by a test.

## Excel adapter review

PASS with a P2 follow-up.

- Workbook loading uses `read_only=True` and `data_only=True`, then closes in `finally`.
- Explicit caller-selected sheets are supported; a missing selection raises a clear `ValueError`.
- Period-header matrices produce deterministic records with sheet, row, column, and locator trace.
- No workbook write or DateFac-specific sheet name is present.
- P2: `sheets=None` reads every workbook sheet. For a conservative public adapter, the next implementation slice should decide whether selection must be explicit or document the all-sheets behavior more prominently.

## Normalization/model review

PASS.

- Generic text, period, numeric, unit, preview, and hash helpers are source-neutral.
- Financial aliases are isolated in the optional profile.
- Period normalization preserves A/E/F, quarterly, and half-year forms.
- Numeric handling safely supports commas, percent signs, parenthesized negatives, nulls, and booleans.
- Unit normalization canonicalizes labels but performs no implicit scale conversion.
- Previews and stable hashes are bounded and deterministic.
- Public dataclasses contain no clean-data, delivery, readiness, DB, queue, or DateFac-specific field.

## Reconciliation review

FAIL.

The default identity is correct:

```text
context + metric_key + period
```

All required generic statuses are present, duplicate keys become `UNPARSEABLE`, outputs are ordered deterministically, inputs are not mutated, and unit mismatches require review.

However, `compare_records(..., identity_fields=...)` only rejects an empty identity-field list. Its indexer resolves every requested field with `getattr(record, field, "")`. Therefore an unknown selector becomes an empty-string key for every record and can pair unrelated singleton records.

Independent reproduction in the isolated environment:

```text
left  = income / revenue / 2026E / 100 / million
right = balance / assets / 2025A / 100 / million
identity_fields = ("unknown_identity_field",)
result = MATCH
```

This is a false positive match, not a review-required result. The implementation must reject unknown identity fields and reject blank/null values for each requested identity component before it can pass Phase 1 QA.

## Discrepancy report review

PASS.

- Review-required rows group by context, metric key, and period.
- Case IDs are stable hashes of identity, statuses, and diagnosis.
- Diagnosis, severity, and recommended actions are coherent for the generic six statuses.
- JSON and Markdown rendering are deterministic and contain bounded evidence plus compact source traces.
- Report writing refuses a nonempty directory, so unrelated files are not overwritten.
- No automatic acceptance, product readiness, delivery, or persistence claim is present.

## Benchmark review

PASS.

- Only `ground_truth_review_status=VERIFIED` rows are included in counts.
- Unverified rows do not contribute errors or correct outcomes.
- Both-systems-wrong same-value and different-value accounting are covered.
- Precision, recall, and false-positive rate are zero-division safe.
- The workbook schema is strictly checked.
- No project-specific report identity, Anjing Foods string, or local report path appears in the standalone package.

## CLI review

PASS.

The isolated console script successfully executed all three commands with committed anonymous fixtures and temporary output:

```text
doc-reconcile compare   -> comparison_row_count=6; review_required_count=3
doc-reconcile report    -> discrepancy_report.json and discrepancy_report.md
doc-reconcile benchmark -> benchmark_summary.json and benchmark_summary.md
```

- Top-level and all subcommand `--help` paths work.
- Missing input exits nonzero (`2`) with a bounded useful message.
- Existing `compare` output exits nonzero (`2`) and is not overwritten.
- `report` and `benchmark` require a new or empty output directory.
- No network, database, OCR, MinerU runtime, LLM, VLM, Docker, Java, or agent framework was invoked.

## Test quality review

PASS with a release-blocking coverage gap.

The 84 tests are focused and cover meaningful positive and negative behavior: page grouping, rowspan/colspan, Excel selection, normalization, all statuses, input nonmutation, deterministic ordering, grouping, bounded rendering, safe directories, VERIFIED-only metrics, and CLI safety.

The suite does not test invalid or blank configurable identity components. That absence allowed the false `MATCH` defect above to pass. The remediation must add regression coverage for:

- unknown identity field names;
- blank/null identity values for default and custom identity keys;
- rejection before any pairing or status calculation.

The suite also does not export/test `__version__` and does not exercise malformed JSON input through the CLI. These are P2 follow-ups.

## Real-data and legacy exclusion review

PASS.

- The implementation commit contains no PDF, Excel, CSV, generated report, local output directory, credentials, or confidential report text.
- Static scans found no `D:\_datefac` or `E:\mineru` reference in the standalone project after temporary validation caches were removed.
- Static source scanning found no `datefac_agent` dependency, legacy DateFac import, readiness, clean-data, queue, DB, HTTP, or client-data code.
- Only the two small anonymous JSON fixtures are committed.
- Temporary virtual-environment, editable-install metadata, cache, and CLI-output directories were removed after validation.

## Validation outputs

```text
python -m pip install -e "document-reconciliation-kit[dev]"
PASS

isolated venv install outside repository package directory
PASS

python -m pytest document-reconciliation-kit/tests -q
PASS: 84 tests

python -m document_reconciliation.cli --help
PASS

doc-reconcile --help
PASS

doc-reconcile compare --help
PASS

doc-reconcile report --help
PASS

doc-reconcile benchmark --help
PASS

python -c "from document_reconciliation import __version__; print(__version__)"
FAIL: __version__ is not exported (P2)

no-datefac_agent static scan
PASS

no D:/E: local-path static scan
PASS after removing generated bytecode caches

configured unknown identity-field reproduction
FAIL: unrelated singleton records returned MATCH

git diff implementation range --stat / --name-status
PASS: one commit, 24 additions, allowed paths only

git status -sb
PASS: clean before QA report creation

git diff --check
PASS
```

## Findings by severity

### P1: configurable identity key can emit a false MATCH

`reconciliation._index_records` silently replaces unknown field values with an empty string. The public configurable identity API must fail closed instead. This is the release-blocking finding.

### P2: version is not exported

The package metadata holds version `0.1.0`, but the documented QA import cannot retrieve it. Export a static `__version__` in a future implementation slice.

### P2: all-sheet default should be made explicit

`load_excel_records(..., sheets=None)` reads all worksheets. Either require a caller selection for the public API or document/test this default as an intentional behavior.

## Limitations

- QA does not alter implementation, tests, fixtures, package metadata, or legacy code.
- The report does not replace a future remediation and re-review.
- Free-text semantic extraction, automatic unit conversion, persistence, delivery, PDF parsing, and production integrations remain out of scope.

## Recommended next task

```text
349A-FIX fail-closed reconciliation identity-key validation
```

Do not begin standalone repository split or DateFac archival preparation until the P1 defect is fixed and a focused QA review passes.

## Data Result / 数据结果

```text
Decision（任务结论）=FAIL
build_result（构建结果）=PASS
test_result（测试结果）=PASS; 84 focused tests passed, but no test covered unsafe identity selectors
files_modified（修改文件数）=1
error_count（错误数）=1; P1 false MATCH through unknown configurable identity field
implementation_file_boundary_result（实现文件边界结果）=PASS; one implementation commit, 24 additions, allowed paths only
standalone_install_review_result（独立安装审查结果）=PASS; fresh isolated editable installation and external import succeeded
mineru_adapter_review_result（MinerU适配器审查结果）=PASS
excel_adapter_review_result（Excel适配器审查结果）=PASS_WITH_FOLLOWUP; optional sheet selection defaults to all sheets
normalization_model_review_result（标准化与模型审查结果）=PASS
reconciliation_review_result（对账审查结果）=FAIL; unsafe custom identity field can produce false MATCH
discrepancy_review_result（差异审查结果）=PASS
benchmark_review_result（基准审查结果）=PASS
cli_review_result（CLI审查结果）=PASS; all commands exercised anonymously with safe output checks
test_quality_review_result（测试质量审查结果）=FAIL; missing regression coverage for unsafe identity fields/blank identity values
legacy_source_untouched（旧项目源代码未修改）=PASS
real_data_exclusion_result（真实数据排除结果）=PASS
recommended_next_task（推荐下一任务）=349A-FIX fail-closed reconciliation identity-key validation
```
