## Task ID

`348N-R6B Output Schema Guardrails Implementation`

## Files modified

- `datefac_agent/audit/output_schema_guardrails.py` (new)
- `tools/run_agent_excel_intake_audit_348a.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md` (this report)

No dependency files, input files, committed output artifacts, legacy `datefac/`, or historical reports were modified.

## Implementation summary

Implemented the R6-recommended first schema layer as a stdlib-only internal validator. No Pydantic, Pandera, pandas, or other dependency was added.

New module:

```text
datefac_agent/audit/output_schema_guardrails.py
```

Exports:

```python
class OutputSchemaGuardrailError(ValueError): ...
def validate_outputs(clean_rows: list[dict], review_rows: list[dict], manifest: dict) -> None: ...
```

The validator operates on the same in-memory dicts the runner already builds for `clean_data.csv`, `review_queue.csv`, and the manifest. It raises `OutputSchemaGuardrailError` with a clear row/sheet/field-specific message on the first violation.

## Guardrails implemented

### Clean-data row_type guardrail

`clean_data` fails if any row has `row_type` in:

```text
TESTSET_SUPPORTING_ROW
NORMALIZED_TESTSET_RECORD_ROW
MARKET_REFERENCE_ROW
UNKNOWN_ROW
```

Missing `row_type` also fails.

### Clean-candidate type guardrail

`clean_data` fails unless every row has `clean_candidate_type` in:

```text
INTERNAL_CLEAN_CANDIDATE
INTERNAL_REFERENCE_CANDIDATE
```

Missing `clean_candidate_type` also fails.

### Count consistency guardrail

Implemented:

```text
len(clean_rows) == manifest["clean_data_row_count"]
len(review_rows) == manifest["review_queue_csv_row_count"]
manifest exposes clean_data_row_count / review_queue_row_count / unknown_row_count
```

Important compatibility note: the existing manifest field `review_queue_row_count` is a logical non-clean/review-required pool count, not the physical `review_queue.csv` row count. In R5/R6B Linyang output it is `489`, while `review_queue.csv` has `46` rows (only REVIEW/FAIL queue rows). To avoid breaking existing semantics, R6B adds an additive manifest field:

```text
review_queue_csv_row_count = len(review_rows)
clean_data_csv_row_count = len(clean_rows)
```

The guardrail validates physical CSV count against `review_queue_csv_row_count` when present, while still requiring the original `review_queue_row_count` to remain exposed.

### Review queue required fields guardrail

Every review queue row must have non-empty:

```text
decision
clean_candidate_type
evidence_level
```

Missing or blank values fail loudly.

### Manifest readiness gate guardrail

Manifest must keep:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

Any opened gate fails.

### External-call counter guardrail

Manifest must keep:

```text
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
```

Any nonzero counter fails. There is no VLM counter field in the current manifest; no VLM call path was added.

### Legacy-touch guardrail

If present in the manifest, these must remain false:

```text
legacy_datefac_touched = false
legacy_outputs_touched = false
```

Both fields exist in the current manifest and are enforced.

## Runner integration point

Integrated in `tools/run_agent_excel_intake_audit_348a.py`:

```python
manifest["clean_data_csv_row_count"] = len(clean_rows)
manifest["review_queue_csv_row_count"] = len(review_rows)
validate_outputs(clean_rows, review_rows, manifest)
_write_json(output_dir / "agent_excel_intake_audit_348a_manifest.json", manifest)
```

Placement is after `clean_rows`, `review_rows`, and `manifest` are built, and before manifest/run_summary are written/returned. A guardrail violation raises loudly and stops the run; it is not hidden or downgraded to success.

## Tests added

Added direct deterministic unit tests using small in-memory dict lists (no external services):

- valid outputs pass
- clean_data containing each forbidden row_type raises:
  - `TESTSET_SUPPORTING_ROW`
  - `NORMALIZED_TESTSET_RECORD_ROW`
  - `MARKET_REFERENCE_ROW`
  - `UNKNOWN_ROW`
- invalid clean_candidate_type raises
- clean_data count mismatch raises
- review_queue CSV count mismatch raises
- review_queue required field empty raises for:
  - `decision`
  - `clean_candidate_type`
  - `evidence_level`
- manifest readiness gate opened raises for:
  - `client_ready`
  - `production_ready`
  - `formal_client_export_allowed`
  - `demo_export_only`
- external-call counter nonzero raises for:
  - `llm_api_call_count`
  - `mineru_run_count`
  - `ocr_run_count`
- `legacy_datefac_touched=True` raises

The full agent test suite now reports:

```text
74 passed
```

## Validation commands and results

```text
python -m py_compile datefac_agent\audit\output_schema_guardrails.py tools\run_agent_excel_intake_audit_348a.py tests\agent\test_agent_excel_intake_audit_348a.py
  -> OK

python -m pytest tests\agent -q
  -> 74 passed in 0.61s

git diff --check
  -> no whitespace/conflict errors
     (Windows warning only: LF will be replaced by CRLF in tools/run_agent_excel_intake_audit_348a.py)
```

## Pilot result if rerun

Reran the Linyang pilot into a new uncommitted output directory:

```text
output/agent_excel_intake_audit_348n_r6b_output_schema_guardrails
```

The run completed successfully, meaning the new guardrail validator passed on real R5-style output.

Key manifest/result values:

```text
clean_data_row_count = 0
clean_data_csv_row_count = 0
review_queue_row_count = 489
review_queue_csv_row_count = 46
unknown_row_count = 0
normalized_testset_record_row_count = 320
market_reference_row_count = 10
testset_supporting_row_count = 83
```

CSV count verification:

```text
clean_data.csv rows = 0 == manifest clean_data_csv_row_count
review_queue.csv rows = 46 == manifest review_queue_csv_row_count
```

The original logical `review_queue_row_count = 489` remains preserved for continuity with prior reports.

## External call check

R6B added no external-service call path. The R6B pilot manifest reports:

```text
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
```

No MinerU / OCR / LLM / VLM call was run.

## Readiness gate check

R6B did not change gate meanings. The R6B pilot manifest reports:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

The new guardrail enforces these values.

## Boundary check

The guardrail directly encodes the R4/R5 boundary lesson:

```text
clean_data cannot contain TESTSET_SUPPORTING_ROW
clean_data cannot contain NORMALIZED_TESTSET_RECORD_ROW
clean_data cannot contain MARKET_REFERENCE_ROW
clean_data cannot contain UNKNOWN_ROW
clean_data clean_candidate_type must be INTERNAL_CLEAN_CANDIDATE or INTERNAL_REFERENCE_CANDIDATE
```

The R6B real pilot has `clean_data_row_count = 0`, so it passes by having no clean rows. Future leaks like the pre-R5 `qualitative_facts` situation will raise `OutputSchemaGuardrailError` before the manifest is written.

## Decision

`348N_R6B_CONFIRMED_OUTPUT_SCHEMA_GUARDRAILS_VALID`

R6B implemented the intended stdlib-only output guardrail layer, integrated it into the runner, added violation/pass tests, preserved existing manifest semantics by adding explicit CSV row count fields, and confirmed the guardrail passes on real Linyang output.

## Recommended next task

`348N-R6B-QA output schema guardrails review`

A focused QA task should independently verify:

- guardrail failure cases truly fail loudly
- runner integration placement is safe
- `review_queue_row_count` historical semantics remain preserved
- new `*_csv_row_count` fields do not break downstream docs/tests
- no dependency/input/output/legacy boundary violations occurred

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R6B_CONFIRMED_OUTPUT_SCHEMA_GUARDRAILS_VALID
new_dependency_added（是否新增依赖）= no
pydantic_used（是否使用 Pydantic）= no
pandera_used（是否使用 Pandera）= no
guardrail_module（护栏模块）= datefac_agent/audit/output_schema_guardrails.py
clean_data_forbidden_row_type_guardrail（clean_data 禁止 row_type 护栏）= implemented
clean_candidate_type_guardrail（clean 候选类型护栏）= implemented
count_consistency_guardrail（计数一致性护栏）= implemented (clean_data_row_count + review_queue_csv_row_count)
review_queue_required_fields_guardrail（review_queue 必填字段护栏）= implemented
manifest_gate_guardrail（manifest 就绪门护栏）= implemented
external_counter_guardrail（外部调用计数护栏）= implemented
pytest_result（测试结果）= 74 passed
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= closed / unchanged
```
