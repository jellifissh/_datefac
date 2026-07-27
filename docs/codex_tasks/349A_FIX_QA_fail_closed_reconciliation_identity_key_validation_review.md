# 349A-FIX-QA fail-closed reconciliation identity-key validation review

## Goal

Independently review commit `18ea45def2f9a4c15895b68f87b4cfeeb5314bb0` and determine whether the Phase 1 release-blocking false-`MATCH` defect is fully closed without introducing a new identity, packaging, or boundary defect.

This is QA-only. Do not modify implementation, tests, fixtures, package metadata, README, or legacy DateFac code.

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

## Review range

```text
base = b6e8745
head = 18ea45def2f9a4c15895b68f87b4cfeeb5314bb0
```

Expected changed files only:

```text
document-reconciliation-kit/src/document_reconciliation/models.py
document-reconciliation-kit/src/document_reconciliation/reconciliation.py
document-reconciliation-kit/src/document_reconciliation/__init__.py
document-reconciliation-kit/pyproject.toml
document-reconciliation-kit/README.md
document-reconciliation-kit/tests/test_reconciliation.py
docs/agent/349A_FIX_FAIL_CLOSED_RECONCILIATION_IDENTITY_KEY_VALIDATION_REPORT.md
```

Reject unexpected legacy, adapter, fixture, dependency, generated-output, or real-data changes.

## Read first

```text
docs/agent/349A_QA_DOCUMENT_RECONCILIATION_KIT_PHASE1_REVIEW.md
docs/agent/349A_FIX_FAIL_CLOSED_RECONCILIATION_IDENTITY_KEY_VALIDATION_REPORT.md
document-reconciliation-kit/src/document_reconciliation/models.py
document-reconciliation-kit/src/document_reconciliation/reconciliation.py
document-reconciliation-kit/src/document_reconciliation/__init__.py
document-reconciliation-kit/pyproject.toml
document-reconciliation-kit/README.md
document-reconciliation-kit/tests/test_reconciliation.py
```

## Release-blocking review

### 1. Original P1 reproduction

Independently reproduce the former defect with unrelated records of equal value/unit and:

```python
identity_fields=("unknown_identity_field",)
```

Required result:

```text
ValueError before either iterable is consumed
no comparison rows
no MATCH
```

Do not rely only on the committed regression test.

### 2. Identity selector configuration

Verify fail-closed rejection for:

```text
empty sequence
plain string
bytes
non-sequence
blank field name
whitespace-only field name
non-string field name
duplicate field name
unknown field
forbidden payload field such as normalized_value
forbidden unit field such as normalized_unit
forbidden trace/evidence/parse-status field
```

Verify the public allowlist is exactly:

```text
context
metric_key
metric_display_name
period
```

Verify validation occurs before either left or right iterable is consumed.

### 3. Per-record identity values

For every allowed field, test requested identity components supplied through both input forms:

```text
NormalizedRecord instance
plain Mapping/dict
```

Verify rejection before indexing/pairing for:

```text
None
empty string
whitespace-only string
non-string value such as integer, float, bool, list, or object
```

Important independent check: `NormalizedRecord.from_mapping(...)` must not silently stringify a non-string identity component and allow it into the identity key. The implementation report claims non-string identity values fail closed; test the mapping path directly rather than assuming type hints enforce it.

If mapping identity values such as `{"context": 123}` become `"123"` and proceed, mark QA FAIL unless the public contract explicitly permits coercion and the tests/docs accurately state that behavior. The current fix report states rejection, not coercion.

### 4. Valid behavior preservation

Verify these still work:

```text
default context + metric_key + period identity
valid custom subset identity
valid metric_display_name identity
duplicate valid identity -> UNPARSEABLE
same identity + different value -> CONFLICT
same identity + different normalized unit -> UNIT_REVIEW
left-only and right-only behavior
deterministic ordering
input nonmutation
```

Ensure fail-closed validation does not turn legitimate unit differences into `LEFT_ONLY`/`RIGHT_ONLY` by allowing unit fields into identity.

### 5. Error safety

Invalid selector/value errors may include only bounded configuration context:

```text
side
record position
field name
```

They must not expose:

```text
full record
normalized value
evidence preview
source trace
raw HTML
file path
client data
```

Check that errors contain no partial comparison output and that no output file is created by a failing CLI/API path.

## P2 review

### Version

Verify all of these agree on `0.1.1`:

```text
pyproject.toml
importlib.metadata.version("document-reconciliation-kit")
document_reconciliation.__version__
```

Verify isolated editable installation from a fresh temporary virtual environment outside the package directory.

### Excel behavior documentation

Confirm implementation behavior remains unchanged:

```text
sheets=None -> all worksheets
explicit sheets -> only selected worksheets
```

Confirm README states this clearly and recommends explicit selection for mixed workbooks. This is documentation review only; do not require an API-breaking change in this QA.

## Test quality

Run the committed suite, then add independent one-off reproductions without modifying tracked files.

Check that the new tests genuinely cover:

```text
unknown selector false-MATCH regression
blank/null default identity fields
custom metric_display_name blank handling
validation before iterable consumption
duplicate selectors
forbidden selectors
version export
valid behavior preservation
```

Look specifically for untested mapping coercion, generator consumption, custom subset edge cases, and assertions that only match error text while missing comparison behavior.

## Boundary review

Confirm:

```text
no datefac_agent or legacy datefac import
no DB / queue / persistence / network / OCR / MinerU runtime / LLM / VLM
no D: or E: hard-coded path in standalone project
no real PDF / Excel / report / client data
no generated output committed
no new runtime dependency
legacy DateFac source untouched
```

## Validation

```text
python -m pip install -e "document-reconciliation-kit[dev]"
python -m py_compile document-reconciliation-kit/src/document_reconciliation/models.py
python -m py_compile document-reconciliation-kit/src/document_reconciliation/reconciliation.py
python -m py_compile document-reconciliation-kit/src/document_reconciliation/__init__.py
python -m pytest document-reconciliation-kit/tests/test_reconciliation.py -q
python -m pytest document-reconciliation-kit/tests -q
python -c "import document_reconciliation as d; from importlib.metadata import version; assert d.__version__ == version('document-reconciliation-kit') == '0.1.1'"
git diff b6e8745..18ea45def2f9a4c15895b68f87b4cfeeb5314bb0 --stat
git diff b6e8745..18ea45def2f9a4c15895b68f87b4cfeeb5314bb0 --name-status
git diff --check
git status -sb
```

Also run isolated one-off Python reproductions for all release-blocking cases above.

## Allowed QA output

Create exactly one tracked file:

```text
docs/agent/349A_FIX_QA_FAIL_CLOSED_RECONCILIATION_IDENTITY_KEY_VALIDATION_REVIEW.md
```

Do not change any other tracked file.

## Required report sections

```text
Task ID
Decision
Reviewed range and file boundary
Original false-MATCH reproduction
Identity selector validation review
Per-record identity validation review
Mapping input coercion review
Valid behavior preservation
Error safety review
Version/package review
Excel documentation review
Test quality review
Standalone and real-data boundary review
Validation outputs
Findings by severity
Limitations
Recommended next task
Data Result / 数据结果
```

## Decision rule

PASS only if:

```text
original unknown-field false MATCH is independently closed
all invalid selector configurations fail before input consumption
all requested blank/null/non-string identity values fail through both dataclass and Mapping inputs
valid comparison behavior remains intact
errors remain bounded and safe
version metadata is consistent
only expected files changed
standalone and real-data boundaries remain clean
```

Any path that can still pair unrelated records because an identity selector/value is missing, blank, unknown, or silently coerced is release-blocking FAIL.

## Required Data Result

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=1
error_count（错误数）=
original_false_match_review_result（原错误MATCH审查结果）=
identity_selector_validation_review_result（身份选择器验证审查结果）=
record_identity_validation_review_result（记录身份值验证审查结果）=
mapping_coercion_review_result（映射强制转换审查结果）=
valid_behavior_preservation_result（有效行为保持结果）=
error_safety_review_result（错误安全审查结果）=
version_consistency_review_result（版本一致性审查结果）=
excel_documentation_review_result（Excel说明审查结果）=
standalone_boundary_review_result（独立边界审查结果）=
legacy_source_untouched（旧项目源代码未修改）=
recommended_next_task（推荐下一任务）=
```

Recommended next task on PASS:

```text
349B split document-reconciliation-kit into standalone repository and archive DateFac
```

Recommended next task on FAIL:

```text
349A-FIX2 remediate remaining fail-closed identity validation defect
```

## Commit and push

Stage only the QA report explicitly:

```text
git add docs/agent/349A_FIX_QA_FAIL_CLOSED_RECONCILIATION_IDENTITY_KEY_VALIDATION_REVIEW.md
git commit -m "docs: add 349A identity fix QA review"
git push origin extract/document-reconciliation-kit
```

Stop after push.
