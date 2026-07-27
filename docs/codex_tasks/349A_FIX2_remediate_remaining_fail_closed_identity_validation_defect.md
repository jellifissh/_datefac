# 349A-FIX2 remediate remaining fail-closed identity validation defect

## Goal

Close the remaining P1 path where mapping inputs silently coerce non-string identity values through `str(...)` and can still return a false `MATCH`.

This is a focused bug fix for the standalone package only.

## Workspace

```text
D:\_datefac_agent
branch = extract/document-reconciliation-kit
```

## Preflight

```text
git status -sb
git pull origin extract/document-reconciliation-kit
git status -sb
```

Stop if the worktree is not clean after pull.

## Read first

```text
docs/agent/349A_QA_DOCUMENT_RECONCILIATION_KIT_PHASE1_REVIEW.md
docs/agent/349A_FIX_FAIL_CLOSED_RECONCILIATION_IDENTITY_KEY_VALIDATION_REPORT.md
docs/agent/349A_FIX_QA_FAIL_CLOSED_RECONCILIATION_IDENTITY_KEY_VALIDATION_REVIEW.md
document-reconciliation-kit/src/document_reconciliation/models.py
document-reconciliation-kit/src/document_reconciliation/reconciliation.py
document-reconciliation-kit/tests/test_reconciliation.py
document-reconciliation-kit/tests/test_adapters.py
document-reconciliation-kit/pyproject.toml
document-reconciliation-kit/src/document_reconciliation/__init__.py
```

## Confirmed defect

The original unknown-selector false `MATCH` is fixed.

The remaining defect is the mapping input path:

```python
NormalizedRecord.from_mapping(...)
```

currently converts public identity text fields with `str(value)` before reconciliation validates their type.

Examples that must fail before indexing or pairing:

```python
{"context": 123, ...}
{"metric_key": 1.5, ...}
{"metric_display_name": True, ...}
{"period": ["2026E"], ...}
```

When the affected field is selected in `identity_fields`, equal invalid left/right mappings must never produce `MATCH`.

## Required fix behavior

### 1. Validate raw mapping identity values before coercion

For mapping inputs, inspect each requested identity field on the raw mapping before constructing `NormalizedRecord`.

For every selected identity field, reject with `ValueError` when the raw mapping value is:

```text
missing
None
empty string
whitespace-only string
int
float
bool
list
tuple
dict
set
bytes
arbitrary object
```

Only nonblank `str` values are accepted as mapping identity components.

Do not call `str(...)` before this validation.

### 2. Preserve direct-record validation

Direct `NormalizedRecord` inputs must continue to reject selected identity components that are:

```text
None
blank
whitespace-only
non-string
```

Do not weaken the current direct-record behavior.

### 3. Validate before indexing and pairing

Required order:

```text
validate identity selector configuration
-> validate raw mapping selected identity fields
-> construct normalized records
-> validate direct-record selected identity fields
-> index
-> pair
-> calculate statuses
```

An invalid record must produce no partial comparison rows and no serialized result.

### 4. Keep error messages bounded

Errors may include only:

```text
side
record position
field name
short reason such as missing / blank / non-string
```

Do not include:

```text
full record
identity value
normalized value
unit
evidence preview
source trace
raw payload
local path
```

### 5. Preserve valid public semantics

The public allowlist remains exactly:

```text
context
metric_key
metric_display_name
period
```

The default identity remains:

```text
context + metric_key + period
```

Preserve:

```text
valid default MATCH
valid custom subsets
duplicate identity -> UNPARSEABLE
value mismatch -> CONFLICT
unit mismatch -> UNIT_REVIEW
LEFT_ONLY / RIGHT_ONLY behavior
deterministic ordering
input nonmutation
unknown selector rejection before iterable consumption
```

### 6. Mapping conversion contract

Choose one narrow implementation strategy and document it in the report:

Preferred strategy:

```text
reconciliation validates raw Mapping selected identity values before NormalizedRecord.from_mapping
```

This avoids changing unrelated mapping conversion behavior.

A stricter `NormalizedRecord.from_mapping` identity-field type contract is allowed only if all compatibility effects are explicit and tested.

### 7. Version

Bump the standalone package bugfix version consistently to:

```text
0.1.2
```

Update both:

```text
document-reconciliation-kit/pyproject.toml
document-reconciliation-kit/src/document_reconciliation/__init__.py
```

Verify:

```python
from document_reconciliation import __version__
assert __version__ == "0.1.2"
```

and installed metadata must also report `0.1.2`.

### 8. Excel P2 regression test

Do not change Excel adapter behavior.

Add a direct regression test proving:

```text
load_excel_records(..., sheets=None)
```

reads all worksheets in a small anonymous temporary workbook, while explicit selection reads only the requested sheet.

## Required regression matrix

Add tests for every public identity field:

```text
context
metric_key
metric_display_name
period
```

Against at least these mapping values:

```text
123
1.5
True
[]
object()
```

That is the minimum independent 20-case matrix from QA.

Also add mapping tests for:

```text
missing field
None
""
"   "
bytes
tuple
dict
set
```

For each invalid case:

```text
ValueError raised before indexing or pairing
no MATCH returned
no iterable over-consumption beyond the invalid record
bounded error message
input mapping not mutated
```

Include a specific reproduction of the prior defect:

```text
left and right mappings contain equal invalid identity value
normalized values and units are equal
old result was MATCH
new result must be ValueError
```

## Suggested allowed files

```text
document-reconciliation-kit/src/document_reconciliation/reconciliation.py
document-reconciliation-kit/src/document_reconciliation/models.py          # only if needed
document-reconciliation-kit/src/document_reconciliation/__init__.py
document-reconciliation-kit/pyproject.toml
document-reconciliation-kit/tests/test_reconciliation.py
document-reconciliation-kit/tests/test_adapters.py
docs/agent/349A_FIX2_REMAINING_FAIL_CLOSED_IDENTITY_VALIDATION_REPORT.md
```

Do not modify adapters, benchmark, discrepancy, CLI, fixtures, legacy DateFac source, or other project files unless strictly required. Explain any deviation.

## Boundaries

Do not add dependencies.

Do not touch:

```text
datefac_agent/
datefac/
legacy tests
DB / persistence / queue code
real reports or outputs
network / OCR / MinerU runtime / LLM / VLM code
```

Do not begin standalone repository split or DateFac archival in this task.

Do not use `git add .` or `git add -A`.

## Validation

```text
python -m pip install -e "document-reconciliation-kit[dev]"
python -m py_compile document-reconciliation-kit/src/document_reconciliation/models.py
python -m py_compile document-reconciliation-kit/src/document_reconciliation/reconciliation.py
python -m py_compile document-reconciliation-kit/src/document_reconciliation/__init__.py
python -m pytest document-reconciliation-kit/tests/test_reconciliation.py -q
python -m pytest document-reconciliation-kit/tests/test_adapters.py -q
python -m pytest document-reconciliation-kit/tests -q
python -c "from document_reconciliation import __version__; from importlib.metadata import version; assert __version__ == '0.1.2'; assert version('document-reconciliation-kit') == '0.1.2'; print(__version__)"
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

Also run a standalone manual matrix proving all 20 previously accepted mapping cases now raise `ValueError`.

## Required report

Create:

```text
docs/agent/349A_FIX2_REMAINING_FAIL_CLOSED_IDENTITY_VALIDATION_REPORT.md
```

Required sections:

```text
Task ID
P1 recap
Root cause
Files changed
Raw mapping validation order
Mapping invalid-value matrix
Direct-record preservation
Error-safety review
Version 0.1.2
Excel all-sheet regression test
Validation outputs
Standalone/legacy boundary
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
raw_mapping_validation_result（原始映射验证结果）=
mapping_non_string_rejection_result（映射非字符串拒绝结果）=
mapping_blank_missing_rejection_result（映射空值缺失拒绝结果）=
direct_record_preservation_result（直接记录行为保持结果）=
false_match_regression_result（错误MATCH回归结果）=
error_safety_result（错误安全结果）=
version_result（版本结果）=
excel_all_sheets_test_result（Excel全工作表测试结果）=
standalone_boundary_result（独立边界结果）=
legacy_source_untouched（旧项目源代码未修改）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
349A-FIX2-QA remaining fail-closed identity validation review
```

## Commit and push

Stage only explicit allowed files, then:

```text
git commit -m "fix: reject non-string mapping identity values"
git push origin extract/document-reconciliation-kit
```

Stop after push.
