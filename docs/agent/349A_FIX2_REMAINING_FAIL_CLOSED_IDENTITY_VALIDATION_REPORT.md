# 349A-FIX2 remaining fail-closed identity validation report

## Task ID

```text
349A-FIX2 remediate remaining fail-closed identity validation defect
```

## P1 recap

349A-FIX-QA found that the original unknown-selector false `MATCH` was closed,
but plain mapping inputs could still turn non-string identity components into
strings and pair them as `MATCH`.  For example, equal left/right mappings with
`{"context": 123}` were accepted when `context` was selected.

## Root cause

`NormalizedRecord.from_mapping(...)` intentionally converts general mapping text
values through `str(...)`.  The previous reconciliation path constructed that
model before checking selected mapping identity components, so the later identity
validator could no longer distinguish an invalid integer, list, boolean, or
object from legitimate text.

## Files changed

- `document-reconciliation-kit/src/document_reconciliation/reconciliation.py`
- `document-reconciliation-kit/src/document_reconciliation/__init__.py`
- `document-reconciliation-kit/pyproject.toml`
- `document-reconciliation-kit/tests/test_reconciliation.py`
- `document-reconciliation-kit/tests/test_adapters.py`
- `docs/agent/349A_FIX2_REMAINING_FAIL_CLOSED_IDENTITY_VALIDATION_REPORT.md`

`models.py`, adapters, fixtures, CLI, benchmarks, legacy DateFac code, and
dependencies are unchanged.

## Raw mapping validation order

The narrow preferred strategy is implemented in reconciliation rather than
changing the general `NormalizedRecord.from_mapping(...)` conversion contract:

```text
validate identity selector configuration
-> validate raw selected mapping identity values
-> construct NormalizedRecord
-> validate selected direct-record identity values
-> index
-> pair
-> calculate status
```

For each selected public identity field, a mapping must contain a nonblank
`str`.  Missing values raise a bounded `missing identity field` error; `None` and
blank strings raise `blank identity field`; every other type raises
`non-string identity field`.  Errors identify only side, record position, field,
and short reason.  No raw value is converted before this check.

## Mapping invalid-value matrix

The regression suite covers every public identity field:

```text
context
metric_key
metric_display_name
period
```

For every field it rejects `123`, `1.5`, `True`, `[]`, and `object()` from both
left and right mapping inputs: 40 parameterized checks.  It also rejects missing,
`None`, empty string, whitespace-only string, bytes, tuple, dict, and set values.
The missing-field test uses a generator that raises if a second record is
consumed, proving rejection occurs at the invalid record before indexing/pairing.

The explicit former false-match shape—equal left/right mapping `context=123`
with matching normalized value and unit—now raises `ValueError` and cannot return
`MATCH`.

## Direct-record preservation

Direct `NormalizedRecord` inputs continue through `_identity_key(...)`, which
rejects selected `None`, blank, whitespace-only, and non-string components before
they become keys.  Existing default/custom identity, duplicate, conflict, unit
review, left/right-only, ordering, and input-nonmutation tests remain passing.

## Error-safety review

The new mapping tests assert that a rejecting error does not contain a supplied
private evidence preview.  The validation messages contain neither mapping
values, normalized values, units, source traces, raw HTML, nor paths.  An invalid
mapping raises before result construction; `reconcile_records(...)` therefore
cannot serialize a partial comparison result.

## Version 0.1.2

Both package metadata and the public package attribute are bumped to `0.1.2`.
The editable installation metadata and `document_reconciliation.__version__` were
verified to agree on that value.

## Excel all-sheet regression test

The Excel adapter remains unchanged.  The expanded anonymous temporary-workbook
test now proves that `sheets=None` returns records from both worksheets, while
`sheets=["Income"]` returns only the selected worksheet.  This matches the
documented public behavior without altering selection semantics.

## Validation outputs

```text
python -m pip install -e "document-reconciliation-kit[dev]"
PASS: editable package installed as 0.1.2

python -m py_compile document-reconciliation-kit/src/document_reconciliation/models.py
PASS

python -m py_compile document-reconciliation-kit/src/document_reconciliation/reconciliation.py
PASS

python -m py_compile document-reconciliation-kit/src/document_reconciliation/__init__.py
PASS

python -m pytest document-reconciliation-kit/tests/test_reconciliation.py -q
PASS: 101 tests

python -m pytest document-reconciliation-kit/tests/test_adapters.py -q
PASS: 12 tests

python -m pytest document-reconciliation-kit/tests -q
PASS: 172 tests

python -c "from document_reconciliation import __version__; from importlib.metadata import version; assert __version__ == '0.1.2'; assert version('document-reconciliation-kit') == '0.1.2'; print(__version__)"
PASS: 0.1.2

standalone manual matrix
PASS: mapping non-string 20/20 ValueError; mapping missing/blank 32/32 ValueError; direct-record non-string 4/4 ValueError
```

## Standalone and legacy boundary

- No dependency, network, database, queue, persistence, OCR, MinerU runtime,
  LLM, VLM, real-data, or generated-output change was added.
- No `datefac_agent/`, legacy `datefac/`, or legacy-test file changed.
- The fix does not alter readiness, clean-data, delivery, or repository-split
  behavior.

## Decision

```text
PASS
```

Raw mapping identity components now fail closed before model coercion, indexing,
or pairing, while the public allowlist and valid comparison semantics remain
unchanged.

## Recommended next task

```text
349A-FIX2-QA remaining fail-closed identity validation review
```

## Data Result / 数据结果

```text
Decision（任务结论）=PASS
build_result（构建结果）=PASS
test_result（测试结果）=PASS; reconciliation 101, adapters 12, full standalone suite 172
files_modified（修改文件数）=6
error_count（错误数）=0
raw_mapping_validation_result（原始映射验证结果）=PASS; selected mapping identity fields validate before NormalizedRecord construction
mapping_non_string_rejection_result（映射非字符串拒绝结果）=PASS; 20/20 required independent cases and both input sides reject
mapping_blank_missing_rejection_result（映射空值缺失拒绝结果）=PASS; missing/None/empty/whitespace/bytes/tuple/dict/set reject fail-closed
direct_record_preservation_result（直接记录行为保持结果）=PASS; selected invalid direct values still reject and valid statuses remain passing
false_match_regression_result（错误MATCH回归结果）=PASS; equal invalid mapping context=123 now raises ValueError
error_safety_result（错误安全结果）=PASS; bounded side/position/field/reason messages without payload exposure
version_result（版本结果）=PASS; pyproject, public package, and installed metadata equal 0.1.2
excel_all_sheets_test_result（Excel全工作表测试结果）=PASS; None reads all worksheets and explicit selection reads only requested worksheet
standalone_boundary_result（独立边界结果）=PASS; no new runtime/dependency/integration/data boundary change
legacy_source_untouched（旧项目源码未改动）=PASS
recommended_next_task（推荐下一任务）=349A-FIX2-QA remaining fail-closed identity validation review
```
