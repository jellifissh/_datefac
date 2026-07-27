# 349A-FIX fail-closed reconciliation identity-key validation

## Goal

Fix the Phase 1 release-blocking defect found by 349A-QA:

```text
identity_fields=("unknown_identity_field",)
```

must never collapse unrelated records onto an empty identity and return `MATCH`.

Plain Chinese: 自定义身份键必须先验证，再建立索引。字段名未知、字段重复、字段值为空或为 null 时，整个对账操作都要立刻失败，不能继续配对，更不能产生 MATCH。

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
document-reconciliation-kit/src/document_reconciliation/models.py
document-reconciliation-kit/src/document_reconciliation/reconciliation.py
document-reconciliation-kit/src/document_reconciliation/__init__.py
document-reconciliation-kit/pyproject.toml
document-reconciliation-kit/tests/test_reconciliation.py
document-reconciliation-kit/README.md
```

## Required P1 fix

### Public identity-field allowlist

Define and export an explicit allowlist for public comparison identity components.

Minimum safe allowlist:

```text
context
metric_key
metric_display_name
period
```

Do not allow these fields as identity components:

```text
normalized_value
normalized_unit
evidence_preview
source_trace
parse_status
```

Reason:

- values and units are comparison payloads, not identity;
- using unit as identity would hide `UNIT_REVIEW` as left/right-only rows;
- evidence and trace are unstable/non-scalar;
- parse status must not split otherwise identical records before parse review.

A narrower allowlist is acceptable if justified, but the default identity must remain:

```text
context + metric_key + period
```

### Validate identity_fields before indexing

Reject with `ValueError` before consuming/comparing records when:

```text
identity_fields is a string or bytes instead of a sequence of field names
identity_fields is empty
any field name is not a string
any field name is blank after strip
any field name is duplicated
any field name is not in the public allowlist
```

Do not silently normalize an unknown selector to an empty value.

### Validate every requested identity component

For every left and right record, reject with `ValueError` before pairing when a requested identity component is:

```text
None
blank string
whitespace-only string
```

The error should identify the side (`left` or `right`), record position, and field name, but must not dump full records, evidence, or source traces.

Validation must occur before status calculation. No partial comparison result may be returned.

### Mapping conversion safety

`NormalizedRecord.from_mapping(...)` must not convert an explicit null identity value into the literal string `"None"`.

For public identity text fields, explicit null should become an empty value so the reconciliation validator rejects it.

Do not loosen parsing or fabricate replacement identities.

## P2 packaging correction

Export:

```python
from document_reconciliation import __version__
```

Set the package patch version consistently in:

```text
document-reconciliation-kit/pyproject.toml
document-reconciliation-kit/src/document_reconciliation/__init__.py
```

Use:

```text
0.1.1
```

Do not add dynamic version dependencies.

## Excel P2 boundary

Do not change Excel all-sheet behavior in this P1 remediation unless it is required by a failing regression test.

Add a clear README note that:

```text
load_excel_records(..., sheets=None) reads every worksheet
callers handling mixed workbooks should pass an explicit sheet list
```

A future release may make sheet selection mandatory. Keep that separate from the identity-key fix.

## Required tests

Add regression coverage for at least:

```text
unknown identity field raises before pairing
unknown identity field cannot return MATCH
identity_fields passed as a plain string raises
empty identity field list raises
blank field name raises
duplicate identity field raises
non-string field name raises
blank default context raises
blank default metric_key raises
blank default period raises
explicit null mapping identity becomes invalid rather than "None"
blank custom metric_display_name raises when selected
valid default identity behavior remains unchanged
valid custom subset such as context + metric_key works deterministically
duplicate valid comparison identities still produce UNPARSEABLE
unit mismatch still produces UNIT_REVIEW
__version__ imports and equals 0.1.1
```

Tests must assert that invalid identity configuration/value validation happens before any comparison rows are returned.

## Allowed files

Prefer changes only to:

```text
document-reconciliation-kit/src/document_reconciliation/models.py
document-reconciliation-kit/src/document_reconciliation/reconciliation.py
document-reconciliation-kit/src/document_reconciliation/__init__.py
document-reconciliation-kit/pyproject.toml
document-reconciliation-kit/README.md
document-reconciliation-kit/tests/test_reconciliation.py
document-reconciliation-kit/tests/test_normalization.py
```

A tiny dedicated version test file is allowed if clearer.

Do not modify legacy DateFac code.

## Boundaries

Do not add:

```text
DateFac imports
DB / persistence / queue code
network calls
OCR / MinerU runtime / LLM / VLM calls
real report data
local absolute paths
new runtime dependencies
```

Do not begin repository split or legacy archival in this task.

Do not broadly rewrite the toolkit.

## Validation

```text
python -m pip install -e "document-reconciliation-kit[dev]"
python -m py_compile document-reconciliation-kit/src/document_reconciliation/models.py
python -m py_compile document-reconciliation-kit/src/document_reconciliation/reconciliation.py
python -m py_compile document-reconciliation-kit/src/document_reconciliation/__init__.py
python -m pytest document-reconciliation-kit/tests/test_reconciliation.py -q
python -m pytest document-reconciliation-kit/tests -q
python -c "from document_reconciliation import __version__; assert __version__ == '0.1.1'; print(__version__)"
python -c "from document_reconciliation.models import NormalizedRecord; from document_reconciliation.reconciliation import compare_records; a=NormalizedRecord('left','income','revenue','Revenue','2026E','100','million'); b=NormalizedRecord('right','balance','assets','Assets','2025A','100','million');
try:
 compare_records([a],[b],identity_fields=('unknown_identity_field',))
except ValueError:
 print('PASS')
else:
 raise SystemExit('FAIL: false MATCH path still open')"
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

## Report

Create:

```text
docs/agent/349A_FIX_FAIL_CLOSED_RECONCILIATION_IDENTITY_KEY_VALIDATION_REPORT.md
```

Required sections:

```text
Task ID
QA failure recap
Root cause
Files changed
Identity-field allowlist
Configuration validation
Per-record identity validation
Mapping null handling
Version export
Excel behavior note
Regression tests
Validation outputs
Legacy/data boundary
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
identity_allowlist_result（身份字段白名单结果）=
unknown_identity_rejection_result（未知身份字段拒绝结果）=
blank_identity_rejection_result（空身份值拒绝结果）=
null_mapping_result（null映射处理结果）=
false_match_regression_result（错误MATCH回归结果）=
version_export_result（版本导出结果）=
excel_behavior_documentation_result（Excel行为说明结果）=
standalone_boundary_result（独立边界结果）=
legacy_source_untouched（旧项目源代码未修改）=
recommended_next_task（推荐下一任务）=349A-FIX-QA fail-closed reconciliation identity-key validation review
```

## Commit and push

Stage only explicit allowed paths and the fix report, then:

```text
git commit -m "fix: validate reconciliation identity keys"
git push origin extract/document-reconciliation-kit
```

Stop after push.
