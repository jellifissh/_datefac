## Task ID

`348N-R6B-FIX Clean Data CSV Row Count Guardrail Completion`

## Files modified

- `datefac_agent/audit/output_schema_guardrails.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md`

No runner change was needed. `tools/run_agent_excel_intake_audit_348a.py` already populates `clean_data_csv_row_count` and `review_queue_csv_row_count` before calling `validate_outputs(...)`.

No dependency files, input files, output artifacts, legacy `datefac/`, or historical reports were modified.

## Implementation summary

Fixed the exact R6B-QA blocker: `validate_outputs(...)` now validates `manifest["clean_data_csv_row_count"]` when the field is present, in addition to the existing `manifest["clean_data_row_count"]` check.

The added logic in `_validate_count_consistency(...)` is:

```text
len(clean_rows) == manifest["clean_data_row_count"]
len(clean_rows) == manifest["clean_data_csv_row_count"]  # when present
```

This mirrors the existing `review_queue_csv_row_count` behavior and preserves all existing semantics.

## Exact guardrail gap fixed

R6B-QA found this passed unexpectedly:

```text
len(clean_rows) = 1
manifest["clean_data_row_count"] = 1
manifest["clean_data_csv_row_count"] = 999
validate_outputs(...) passes
```

After this fix, that mismatch raises `OutputSchemaGuardrailError` with a message naming `clean_data_csv_row_count`:

```text
clean_data count mismatch: clean_data.csv has 1 rows but manifest clean_data_csv_row_count=999
```

The existing `clean_data_row_count` guardrail was not removed or weakened.

## Tests added

Added one direct in-memory negative test:

```text
test_output_schema_guardrails_clean_data_csv_count_mismatch_raises
```

It proves the exact R6B-QA probe now fails:

```text
clean_data_row_count = len(clean_rows)
clean_data_csv_row_count != len(clean_rows)
validate_outputs(...) raises OutputSchemaGuardrailError
```

All existing guardrail tests were kept intact.

## Validation commands and results

```text
python -m py_compile datefac_agent\audit\output_schema_guardrails.py tests\agent\test_agent_excel_intake_audit_348a.py
  -> OK

python -m pytest tests\agent -q
  -> 75 passed in 0.98s

git diff --check
  -> no whitespace/conflict errors
     (Windows warning only: LF will be replaced by CRLF in datefac_agent/audit/output_schema_guardrails.py)
```

## Pilot result if rerun

Reran the Linyang pilot into a new uncommitted output directory:

```text
output/agent_excel_intake_audit_348n_r6b_fix_clean_data_csv_row_count_guardrail
```

The guardrail passed on real output.

Key manifest/result values:

```text
clean_data_row_count = 0
clean_data_csv_row_count = 0
review_queue_row_count = 489
review_queue_csv_row_count = 46
unknown_row_count = 0
normalized_testset_record_row_count = 320
market_reference_row_count = 10
```

The output directory is not committed.

## External call check

No external-service call path was added or used.

```text
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
VLM calls = 0
```

## Readiness gate check

Readiness gates remain closed / unchanged:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

## Boundary check

- No dependency files modified.
- No Pydantic / Pandera / pandas used.
- No input/output files modified as source artifacts; only an untracked pilot output directory was generated.
- No legacy `datefac/` touch.
- No readiness gate or export behavior change.
- No `git add .` / `git add -A` used.

## Decision

`348N_R6B_FIX_CONFIRMED_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_VALID`

The exact R6B-QA blocker is fixed with a minimal validator change and one targeted negative test. Existing guardrails and runner semantics are preserved.

## Recommended next task

`348N-R6B-FIX-QA clean_data_csv_row_count guardrail review`

A focused QA task should independently confirm the new `clean_data_csv_row_count` mismatch now loud-fails, that `review_queue_row_count` / `review_queue_csv_row_count` semantics remain unchanged, and that the real Linyang pilot still passes.

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R6B_FIX_CONFIRMED_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_VALID
fixed_gap（修复缺口）= clean_data_csv_row_count mismatch now raises OutputSchemaGuardrailError
new_dependency_added（是否新增依赖）= no
pydantic_used（是否使用 Pydantic）= no
pandera_used（是否使用 Pandera）= no
clean_data_row_count_guardrail（clean_data_row_count 护栏）= still valid
clean_data_csv_row_count_guardrail（clean_data_csv_row_count 护栏）= implemented / valid
review_queue_csv_row_count_guardrail（review_queue_csv_row_count 护栏）= still valid
pytest_result（测试结果）= 75 passed
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= closed / unchanged
```
