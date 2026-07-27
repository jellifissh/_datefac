# 349A-FIX fail-closed reconciliation identity-key validation report

## Task ID

```text
349A-FIX fail-closed reconciliation identity-key validation
```

## QA failure recap

349A-QA reproduced a release-blocking false `MATCH`: an unknown custom identity selector was resolved to an empty string and paired unrelated singleton records with the same value and unit.

```text
identity_fields=("unknown_identity_field",)
income / revenue / 2026E / 100 / million
balance / assets / 2025A / 100 / million
-> MATCH   (incorrect before this fix)
```

## Root cause

`reconciliation._index_records(...)` formed keys through `getattr(record, field, "")`. Unknown fields therefore became `""`; no configuration validation or per-record identity-value validation occurred before indexing and comparison.

## Files changed

- `document-reconciliation-kit/src/document_reconciliation/models.py`
- `document-reconciliation-kit/src/document_reconciliation/reconciliation.py`
- `document-reconciliation-kit/src/document_reconciliation/__init__.py`
- `document-reconciliation-kit/pyproject.toml`
- `document-reconciliation-kit/README.md`
- `document-reconciliation-kit/tests/test_reconciliation.py`
- `docs/agent/349A_FIX_FAIL_CLOSED_RECONCILIATION_IDENTITY_KEY_VALIDATION_REPORT.md`

No legacy DateFac source, adapters, fixtures, output, dependencies, or external integrations changed.

## Identity-field allowlist

The standalone public API now exports `PUBLIC_IDENTITY_FIELDS`:

```text
context
metric_key
metric_display_name
period
```

The default remains:

```text
context + metric_key + period
```

Comparison payload and unstable fields (`normalized_value`, `normalized_unit`, `evidence_preview`, `source_trace`, and `parse_status`) are rejected as identity components. This preserves unit mismatch detection rather than converting it into left/right-only rows.

## Configuration validation

`validate_identity_fields(...)` executes before either input iterable is consumed. It rejects with `ValueError`:

- plain string or bytes input;
- non-sequence input;
- empty field lists;
- non-string or blank field names;
- duplicate field names;
- fields outside the public allowlist.

No invalid configuration reaches indexing, status calculation, or result rendering.

## Per-record identity validation

Before pairing, every requested field is checked on every left and right record. `None`, empty values, whitespace-only values, and non-string values fail with a bounded `ValueError` identifying only:

```text
side + record position + field name
```

No evidence preview, full record, source trace, or payload value is included in the error. Invalid records produce no partial comparison result.

## Mapping null handling

`NormalizedRecord.from_mapping(...)` now maps explicit null values in public identity text fields to `""`, not the literal string `"None"`. The reconciliation validator then rejects the blank component before indexing.

## Version export

Package metadata and the public package attribute now consistently use:

```text
0.1.1
```

The supported import is:

```python
from document_reconciliation import __version__
```

## Excel behavior note

No Excel parsing behavior changed. The README now clearly states that `load_excel_records(..., sheets=None)` reads every worksheet and that callers handling mixed workbooks should pass an explicit sheet list. Requiring explicit selection remains a separate future change.

## Regression tests

`test_reconciliation.py` now covers:

- unknown, forbidden, duplicate, blank, non-string, string, bytes, and empty identity configuration;
- validation before an input iterable is consumed;
- blank default `context`, `metric_key`, and `period` rejection;
- explicit null mapping identity rejection without a literal `"None"` identity;
- blank custom `metric_display_name` rejection when selected;
- public allowlist contents;
- package version export;
- retained default and custom-subset match behavior;
- retained duplicate-identity `UNPARSEABLE` behavior;
- retained unit-mismatch `UNIT_REVIEW` behavior.

The targeted reconciliation suite now has 28 tests. The full standalone suite has 99 tests.

## Validation outputs

```text
python -m pip install -e "document-reconciliation-kit[dev]"
PASS; installed document-reconciliation-kit 0.1.1

python -m py_compile document-reconciliation-kit/src/document_reconciliation/models.py
PASS

python -m py_compile document-reconciliation-kit/src/document_reconciliation/reconciliation.py
PASS

python -m py_compile document-reconciliation-kit/src/document_reconciliation/__init__.py
PASS

python -m pytest document-reconciliation-kit/tests/test_reconciliation.py -q
PASS: 28 tests

python -m pytest document-reconciliation-kit/tests -q
PASS: 99 tests

python -c "from document_reconciliation import __version__; assert __version__ == '0.1.1'; print(__version__)"
PASS: 0.1.1

unknown identity false-MATCH reproduction
PASS: ValueError raised before comparison; no MATCH path remains

git diff --check
PASS
```

## Legacy/data boundary

- No `datefac_agent` or legacy `datefac` import was added.
- No DateFac production behavior, DB/persistence/queue code, network call, OCR, MinerU runtime, LLM, or VLM code was added.
- No real report data, local absolute path, generated output, or dependency was added.
- The remediation changes only the standalone package contract and its anonymous tests.

## Decision

```text
PASS
```

The false-MATCH configuration path is now fail-closed. Invalid configuration and invalid requested identity values stop comparison before indexing or pairing, while valid default/custom behavior and existing conservative statuses remain intact.

## Recommended next task

```text
349A-FIX-QA fail-closed reconciliation identity-key validation review
```

## Data Result / 数据结果

```text
Decision（任务结论）=PASS
build_result（构建结果）=PASS
test_result（测试结果）=PASS; targeted reconciliation 28 passed; full standalone suite 99 passed
files_modified（修改文件数）=7
error_count（错误数）=0
identity_allowlist_result（身份字段白名单结果）=PASS; context, metric_key, metric_display_name, period only
unknown_identity_rejection_result（未知身份字段拒绝结果）=PASS; rejects before input consumption or pairing
blank_identity_rejection_result（空身份值拒绝结果）=PASS; requested null/blank/whitespace identity values fail closed
null_mapping_result（null映射处理结果）=PASS; explicit null remains blank and is rejected, never converted to "None"
false_match_regression_result（错误MATCH回归结果）=PASS; prior unknown-selector false-MATCH reproduction now raises ValueError
version_export_result（版本导出结果）=PASS; __version__ == 0.1.1
excel_behavior_documentation_result（Excel行为说明结果）=PASS; README documents sheets=None all-worksheet behavior
standalone_boundary_result（独立边界结果）=PASS; no legacy dependency, real data, local path, or new runtime dependency
legacy_source_untouched（旧项目源代码未修改）=PASS
recommended_next_task（推荐下一任务）=349A-FIX-QA fail-closed reconciliation identity-key validation review
```
