## Task ID

`348N-R6B-FIX-QA Clean Data CSV Row Count Guardrail Review`

## Reviewed files and artifacts

Reviewed source/test files read-only:

- `datefac_agent/audit/output_schema_guardrails.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `tools/run_agent_excel_intake_audit_348a.py`

Reviewed docs:

- `docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md`
- `docs/agent/348N_R6B_QA_OUTPUT_SCHEMA_GUARDRAILS_REVIEW.md`
- `docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R6B_FIX_QA_clean_data_csv_row_count_guardrail_review.md`

Reviewed output artifacts read-only:

- `output/agent_excel_intake_audit_348n_r6b_fix_clean_data_csv_row_count_guardrail/agent_excel_intake_audit_348a_manifest.json`
- `output/agent_excel_intake_audit_348n_r6b_fix_clean_data_csv_row_count_guardrail/clean_data.csv`
- `output/agent_excel_intake_audit_348n_r6b_fix_clean_data_csv_row_count_guardrail/review_queue.csv`

## Implementation boundary QA

Conclusion: VALID.

- R6B-FIX commit `a4338a9` changed exactly:
  - `datefac_agent/audit/output_schema_guardrails.py`
  - `tests/agent/test_agent_excel_intake_audit_348a.py`
  - `docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md`
- `tools/run_agent_excel_intake_audit_348a.py` was not modified by the FIX, which is correct because R6B already populated `clean_data_csv_row_count` before validation.
- No dependency files were modified.
- No `input/`, `output/`, `legacy datefac/`, `temp/`, `data/`, readiness-gate, or export behavior changes were made.
- No output files from the pilot are tracked by git.

## Exact gap fix QA

Conclusion: VALID.

R6B-FIX added the missing check in `_validate_count_consistency(...)`:

```text
if "clean_data_csv_row_count" in manifest:
    len(clean_rows) == manifest["clean_data_csv_row_count"]
```

The existing checks remain intact:

```text
len(clean_rows) == manifest["clean_data_row_count"]
len(review_rows) == manifest["review_queue_csv_row_count"]  # when present
```

No `review_queue_row_count` / `review_queue_csv_row_count` compatibility behavior was changed.

## Loud failure QA

Conclusion: VALID.

The exact R6B-QA probe now raises `OutputSchemaGuardrailError`:

```text
len(clean_rows) = 1
manifest["clean_data_row_count"] = 1
manifest["clean_data_csv_row_count"] = 999
validate_outputs(...) -> raises
```

Observed error:

```text
EXPECTED_RAISE clean_data count mismatch: clean_data.csv has 1 rows but manifest clean_data_csv_row_count=999
```

The message names `clean_data_csv_row_count`, satisfying the task requirement.

## Test coverage QA

Conclusion: VALID.

New test exists:

```text
test_output_schema_guardrails_clean_data_csv_count_mismatch_raises
```

It asserts the exact gap: `clean_data_row_count` is correct, `clean_data_csv_row_count` is wrong, and `validate_outputs(...)` raises `OutputSchemaGuardrailError`.

Existing guardrail tests remain present, including:

- forbidden clean row type values
- invalid clean_candidate_type
- `clean_data_row_count` mismatch
- `review_queue_csv_row_count` mismatch
- review_queue required fields
- opened gates
- nonzero external counters
- legacy touched flag

Full test result: `75 passed`.

## Manifest semantics QA

Conclusion: VALID.

- `clean_data_row_count` remains the historical clean-row count and is still validated.
- `clean_data_csv_row_count` remains additive and is now validated when present.
- `review_queue_row_count` historical logical semantics remain unchanged.
- `review_queue_csv_row_count` remains the physical `review_queue.csv` row count and is still validated.
- No runner changes were needed, so no manifest field was renamed or repurposed.

## Real pilot QA

Conclusion: VALID.

R6B-FIX pilot output exists and was inspected read-only:

```text
output/agent_excel_intake_audit_348n_r6b_fix_clean_data_csv_row_count_guardrail
```

Confirmed manifest/output values:

```text
clean_data_row_count = 0
clean_data_csv_row_count = 0
actual clean_data.csv rows = 0
review_queue_row_count = 489
review_queue_csv_row_count = 46
actual review_queue.csv rows = 46
unknown_row_count = 0
normalized_testset_record_row_count = 320
market_reference_row_count = 10
```

Output directory is not tracked by git.

## Validation result

Commands run:

```text
python -m py_compile datefac_agent\audit\output_schema_guardrails.py tests\agent\test_agent_excel_intake_audit_348a.py
  -> OK

python -m pytest tests\agent -q
  -> 75 passed in 0.52s

git diff --check
  -> clean
```

No code/tests/dependency/input/output files were modified by this QA task before the QA report creation.

## External call QA

Conclusion: VALID.

- R6B-FIX pilot manifest: `llm_api_call_count=0`, `mineru_run_count=0`, `ocr_run_count=0`.
- No VLM counter exists and no VLM path was added.
- This QA task did not run MinerU, OCR, LLM, or VLM.

## Readiness gate QA

Conclusion: VALID.

R6B-FIX pilot manifest:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

Readiness gates remain closed / unchanged.

## Decision

`348N_R6B_FIX_QA_CONFIRMED_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_VALID`

The R6B-QA blocker is fixed. `clean_data_csv_row_count` mismatch now loud-fails with `OutputSchemaGuardrailError`, the original `clean_data_row_count` and `review_queue_csv_row_count` guardrails remain valid, manifest semantics are unchanged, no dependencies were added, and tests pass.

## Recommended next task

`348N-R6C output guardrails adoption review`

Suggested narrow follow-up: decide whether the validated guardrails should be documented as the standard runner contract and whether future task reports should include both logical and physical queue counts (`review_queue_row_count` and `review_queue_csv_row_count`) consistently.

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R6B_FIX_QA_CONFIRMED_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_VALID
fixed_gap_confirmed（是否确认修复缺口）= yes
clean_data_csv_row_count_mismatch_loud_fail（clean_data_csv_row_count mismatch 是否 loud fail）= yes
clean_data_row_count_guardrail（clean_data_row_count 护栏）= still valid
clean_data_csv_row_count_guardrail（clean_data_csv_row_count 护栏）= valid
review_queue_csv_row_count_guardrail（review_queue_csv_row_count 护栏）= still valid
new_dependency_added（是否新增依赖）= no
pydantic_used（是否使用 Pydantic）= no
pandera_used（是否使用 Pandera）= no
pytest_result（测试结果）= 75 passed
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= closed / unchanged
```
