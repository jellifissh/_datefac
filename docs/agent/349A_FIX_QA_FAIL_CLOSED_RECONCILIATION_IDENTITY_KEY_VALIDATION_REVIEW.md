# 349A-FIX-QA fail-closed reconciliation identity-key validation review

## Task ID

```text
349A-FIX-QA fail-closed reconciliation identity-key validation review
```

## Decision

```text
FAIL
```

The original unknown-selector false `MATCH` is fixed, but the mapping input path
still silently coerces non-string identity values.  For every public identity
field, mapping values such as `123`, `1.5`, `True`, a list, and an object are
converted to text by `NormalizedRecord.from_mapping(...)`; equal invalid mapping
inputs then produce `MATCH`.  This violates the required fail-closed contract and
is a release-blocking P1 defect.

## Reviewed range and file boundary

Reviewed range:

```text
b6e8745..18ea45def2f9a4c15895b68f87b4cfeeb5314bb0
```

- The remediation commit `18ea45d` changes exactly the seven task-allowed
  implementation, test, documentation, and package files.
- The full review range also includes the preceding task-instruction document;
  it is not an implementation change.
- No legacy `datefac/`, `datefac_agent/`, fixture, real-data, output, dependency,
  or persistence file is changed by the remediation commit.

## Original false MATCH review

PASS.  An independent call with
`identity_fields=("unknown_identity_field",)` and inputs whose iteration raises
immediately produced `ValueError` before either iterable was consumed.  No
indexing, comparison row, or `MATCH` result is reachable for that configuration.

## Identity-selector validation review

PASS.  The public allowlist is exactly:

```text
context, metric_key, metric_display_name, period
```

Independent no-consumption probes rejected all 13 invalid configurations:
empty, plain string, bytes, non-sequence set, blank, non-string, duplicate,
unknown, and each forbidden payload field (`normalized_value`,
`normalized_unit`, `evidence_preview`, `source_trace`, and `parse_status`).
Validation executes before the left or right iterable is indexed.

## Per-record identity validation review

PARTIAL / FAIL for the public mapping API.

- Direct `NormalizedRecord` input is fail-closed: all 32 combinations of the
  four allowed selected fields with `None`, empty, whitespace, integer, float,
  boolean, list, and object values raised bounded `ValueError` before pairing.
- Mapping input rejects `None`, empty, and whitespace values because those end up
  blank after normalization.
- Mapping input does **not** reject non-string values.  `_mapping_text` invokes
  `str(value)` for public identity text fields before `_identity_key` validates
  their type, so type information is lost.

## Mapping coercion review

FAIL — P1 release blocker.

For each of `context`, `metric_key`, `metric_display_name`, and `period`, the
independent matrix supplied equal left/right mappings containing `int`, `float`,
`bool`, `list`, and `object` values while selecting that field as the identity.
All 20 cases returned `MATCH`; none raised `ValueError`.

For example, `{"context": 123, ...}` is normalized to a record with
`context == "123"`, rather than being rejected.  The contract requires the
mapping path to reject non-string requested identity components before indexing
or pairing.  The implementation must preserve raw mapping types until that
validation, or reject invalid mapping values in `from_mapping`, without changing
the accepted public identity semantics.

## Valid behavior preservation review

PASS based on the targeted and full test suites.  Default identity, valid custom
subsets including `metric_display_name`, duplicate-key `UNPARSEABLE`, conflict,
unit review, left-only, right-only, deterministic ordering, and input
non-mutation remain covered and pass.

## Error-safety review

PASS for the exercised rejecting paths.  The unknown-selector and blank-record
errors contain only configuration or `side + position + field`; an independent
probe confirmed that a sensitive preview, source-trace value, normalized value,
and unit were absent.  `compare_records` has no output-file side effect, so a
rejection produces no partial comparison serialization.  This does not mitigate
the P1 acceptance path above.

## Version and package review

PASS.  `pyproject.toml`, `document_reconciliation.__version__`, and
`importlib.metadata.version("document-reconciliation-kit")` all report `0.1.1`.
A fresh temporary virtual environment installed the editable package and imported
it from outside the package directory successfully; the temporary environment and
editable-install metadata were removed after validation.

## Excel documentation review

PASS with a non-blocking coverage note.  README states that `sheets=None` reads
all worksheets and explicit selection reads only requested worksheets.  The
adapter implements `list(workbook.sheetnames)` for `None` and iterates only the
validated requested list otherwise; existing tests cover selected-sheet handling
and missing-sheet rejection.  A direct all-sheet regression test remains a useful
P2 coverage follow-up, but no behavior mismatch was found.

## Test-quality review

FAIL for the P1 coverage gap.  The added tests cover selector configuration,
direct-record blanks, explicit mapping null, and valid behavior, but do not test
mapping non-string identity components for every allowed selected field.  That
gap allowed the string-coercion bypass to ship with an otherwise passing suite.

## Standalone and real-data boundary review

PASS.  The remediation range introduces no `datefac_agent` or legacy DateFac
import, local `D:`/`E:` path, real report artifact, database/persistence hook,
network client, OCR, LLM, VLM, or new dependency.  The `README` reference to a
MinerU-style input is descriptive only; no runtime rerun or parser integration
was introduced.  The legacy source tree is untouched.

## Validation outputs

```text
python -m pip install -e "document-reconciliation-kit[dev]"
PASS

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

isolated editable install and version equality check
PASS: 0.1.1

independent selector no-consumption matrix
PASS: 13/13 rejected before consumption

independent direct NormalizedRecord identity-value matrix
PASS: 32/32 invalid selected components rejected

independent mapping non-string identity-value matrix
FAIL: 20/20 invalid components accepted and returned MATCH

git diff --check b6e8745..18ea45def2f9a4c15895b68f87b4cfeeb5314bb0
PASS
```

## Findings by severity

### P1: mapping identity values are silently coerced and can emit MATCH

`models._mapping_text` calls `str(...)` for `context`, `metric_key`,
`metric_display_name`, and `period`.  Consequently,
`reconciliation._identity_key` observes strings instead of the original invalid
types.  The reconciliation contract must fail before indexing/pairing for every
non-string requested identity component from both `NormalizedRecord` and mapping
inputs.

### P2: all-sheet behavior lacks a direct regression test

The implementation and documentation align, but add explicit `sheets=None`
coverage when the P1 remediation adds the required mapping-type matrix.

## Limitations

- This QA task does not change implementation, tests, fixtures, dependencies, or
  production/DateFac code.
- It reviews the standalone reconciliation package only; semantic extraction,
  unit conversion, persistence, delivery, and real-document operations remain
  out of scope.

## Recommended next task

```text
349A-FIX2 remediate remaining fail-closed identity validation defect
```

The follow-up must reject non-string selected identity components in mappings
before `str(...)` coercion, add the complete mapping matrix regression tests, and
then repeat this focused QA review.  Do not start the repository split or DateFac
archival work until this P1 is resolved.

## Data Result / 数据结果

```text
Decision（任务结论）=FAIL
build_result（构建结果）=PASS
test_result（测试结果）=PASS; targeted reconciliation 28 passed; full standalone suite 99 passed; independent mapping coercion matrix failed
files_modified（修改文件数）=1
error_count（错误数）=1; P1 mapping non-string identity values are coerced and can return MATCH
original_false_match_review_result（原始误匹配审查结果）=PASS; unknown selector raises ValueError before input consumption
identity_selector_validation_review_result（身份选择器验证审查结果）=PASS; exact four-field allowlist and 13 invalid configurations reject fail-closed
record_identity_validation_review_result（记录身份验证审查结果）=FAIL; direct records pass, but mapping non-string components bypass validation
mapping_coercion_review_result（映射强制转换审查结果）=FAIL; int/float/bool/list/object for each allowed field returned MATCH
valid_behavior_preservation_result（有效行为保持结果）=PASS; default/custom matching and conservative statuses remain passing
error_safety_review_result（错误安全审查结果）=PASS; exercised errors are bounded and no API output side effect exists
version_consistency_review_result（版本一致性审查结果）=PASS; metadata and public package version are 0.1.1 in an isolated install
excel_documentation_review_result（Excel文档审查结果）=PASS_WITH_FOLLOWUP; documented and implemented all-sheet default, direct regression test remains P2
standalone_boundary_review_result（独立边界审查结果）=PASS; no DateFac, real data, local path, persistence, or new dependency
legacy_source_untouched（旧源码未改动）=PASS
recommended_next_task（推荐下一任务）=349A-FIX2 remediate remaining fail-closed identity validation defect
```
