## Task ID

`348N-R6B-QA Output Schema Guardrails Review`

## Reviewed files and artifacts

Reviewed source/test files read-only:

- `datefac_agent/audit/output_schema_guardrails.py`
- `tools/run_agent_excel_intake_audit_348a.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `requirements.txt`

Reviewed docs:

- `docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md`
- `docs/agent/348N_R6_SCHEMA_HARDENING_DESIGN.md`
- `docs/agent/348N_R5_QA_QUALITATIVE_FACTS_HEADER_FIX_REVIEW.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R6B_QA_output_schema_guardrails_review.md`

Reviewed output artifacts read-only:

- `output/agent_excel_intake_audit_348n_r6b_output_schema_guardrails/agent_excel_intake_audit_348a_manifest.json`
- `output/agent_excel_intake_audit_348n_r6b_output_schema_guardrails/clean_data.csv`
- `output/agent_excel_intake_audit_348n_r6b_output_schema_guardrails/review_queue.csv`

## Implementation boundary QA

Conclusion: VALID.

- R6B commit `cccb19c` changed exactly the intended files:
  - `datefac_agent/audit/output_schema_guardrails.py`
  - `tools/run_agent_excel_intake_audit_348a.py`
  - `tests/agent/test_agent_excel_intake_audit_348a.py`
  - `docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md`
- No dependency files were modified by R6B (`requirements.txt`, `pyproject.toml`, `setup.py`, `setup.cfg`, `Pipfile`, `poetry.lock` not touched).
- No input, output, legacy `datefac/`, old reports, or old task files were modified.
- `git ls-files output\agent_excel_intake_audit_348n_r6b_output_schema_guardrails` returned no tracked output files.

## Dependency QA

Conclusion: VALID.

- No new dependency was added.
- `requirements.txt` still contains only existing entries: `pandas`, `openpyxl`, `requests`, `pyyaml`.
- `datefac_agent/` has no `pydantic`, `pandera`, or `pandas` import/string matches.
- R6B uses stdlib only in `output_schema_guardrails.py` (`typing.Any` plus plain dict/list/frozenset checks).
- Note: `pandas` is still present in the repository-level `requirements.txt` from legacy/project history, but it is not newly introduced and is not imported by the active `datefac_agent/` package.

## Guardrail correctness QA

Conclusion: MOSTLY VALID, with one coverage gap.

Confirmed implemented and valid:

- `clean_data` forbidden `row_type` values:
  - `TESTSET_SUPPORTING_ROW`
  - `NORMALIZED_TESTSET_RECORD_ROW`
  - `MARKET_REFERENCE_ROW`
  - `UNKNOWN_ROW`
- missing `row_type` fails.
- `clean_candidate_type` must be `INTERNAL_CLEAN_CANDIDATE` or `INTERNAL_REFERENCE_CANDIDATE`.
- missing/invalid `clean_candidate_type` fails.
- `clean_data_row_count`, `review_queue_row_count`, and `unknown_row_count` are required manifest fields.
- `len(clean_rows) == manifest['clean_data_row_count']` is enforced.
- `len(review_rows) == manifest['review_queue_csv_row_count']` is enforced when `review_queue_csv_row_count` exists; fallback to `review_queue_row_count` preserves older manifests.
- review queue required fields (`decision`, `clean_candidate_type`, `evidence_level`) must be non-empty.
- gates are enforced closed: `client_ready=false`, `production_ready=false`, `formal_client_export_allowed=false`, `demo_export_only=true`.
- external-call counters are enforced zero: `llm_api_call_count=0`, `mineru_run_count=0`, `ocr_run_count=0`.
- legacy flags are enforced false when present: `legacy_datefac_touched=false`, `legacy_outputs_touched=false`.

Coverage gap found:

- R6B adds `clean_data_csv_row_count = len(clean_rows)`, but `validate_outputs(...)` does **not** validate `clean_data_csv_row_count` when present.
- Independent probe: a manifest with `clean_data_row_count=1` and `clean_data_csv_row_count=999` still passes `validate_outputs(...)` if `len(clean_rows)=1`.
- This conflicts with the R6B-QA requirement that `clean_data_csv_row_count / review_queue_csv_row_count` be additive and safe, and with the checklist item that clean-data count should match `clean_data_row_count / clean_data_csv_row_count as applicable`.
- The corresponding negative test is also missing.

Impact: low-to-medium. The canonical historical count `clean_data_row_count` is protected, so the original R4/R5 clean-data boundary inversion class is guarded. However, the newly added physical CSV count field is not itself protected, making the additive field less safe than intended.

## Loud failure QA

Conclusion: VALID for implemented guardrails.

- Violations raise `OutputSchemaGuardrailError`, a clear custom `ValueError` subclass.
- Failure messages identify the row, sheet/metric where available, and the violating field/value.
- Unit tests use `pytest.raises(OutputSchemaGuardrailError, ...)` across forbidden row types, invalid clean candidate type, count mismatches, review required fields, gates, external counters, and legacy touched flag.
- Runner does not catch or swallow `OutputSchemaGuardrailError`; therefore a guardrail violation fails the run loudly.
- There is no silent downgrade to success.

Caveat: the specific `clean_data_csv_row_count` mismatch is not currently a loud failure because it is not checked.

## Runner integration QA

Conclusion: VALID.

Confirmed integration in `tools/run_agent_excel_intake_audit_348a.py`:

```text
manifest["clean_data_csv_row_count"] = len(clean_rows)
manifest["review_queue_csv_row_count"] = len(review_rows)
validate_outputs(clean_rows, review_rows, manifest)
_write_json(...manifest...)
```

Placement is safe:

- `clean_rows`, `review_rows`, and `manifest` are built first.
- additive CSV count fields are populated before validation.
- `validate_outputs(...)` runs before the manifest JSON and run summary JSON are written.
- a validation failure stops before writing success artifacts.

## Manifest semantics QA

Conclusion: VALID, with the same clean_data_csv guardrail caveat.

- Historical `review_queue_row_count` is preserved as the logical non-clean/review-required pool count. It remains `489` in the R6B pilot.
- New `review_queue_csv_row_count` is additive and represents the physical `review_queue.csv` row count (`46`). It does not replace or rename `review_queue_row_count`.
- `review_queue_csv_row_count` is validated against `len(review_rows)` and the actual CSV count observed from output.
- `clean_data_csv_row_count` is additive and does not break existing manifest semantics; in the real R6B pilot it equals `0` and matches `clean_data.csv`.
- Gap: `clean_data_csv_row_count` is not validated by `validate_outputs(...)`; it is populated by the runner but could diverge without guardrail failure.

## Test coverage QA

Conclusion: MOSTLY VALID, with one missing case.

Covered:

- valid outputs pass.
- forbidden clean_data row_type raises for all four values.
- invalid clean_candidate_type raises.
- clean_data count mismatch raises (`clean_data_row_count`).
- review_queue CSV count mismatch raises (`review_queue_csv_row_count`).
- review_queue required field empty raises (`decision`, `clean_candidate_type`, `evidence_level`).
- gates opened raises (`client_ready`, `production_ready`, `formal_client_export_allowed`, `demo_export_only`).
- external counter nonzero raises (`llm_api_call_count`, `mineru_run_count`, `ocr_run_count`).
- legacy touch true raises (`legacy_datefac_touched`).

Missing:

- no test ensures `clean_data_csv_row_count` mismatch raises.
- because the validator does not check it, such a test would currently fail.

Test command result remains green:

```text
74 passed
```

## Real pilot QA

Conclusion: VALID.

R6B output directory exists and was inspected read-only:

```text
output/agent_excel_intake_audit_348n_r6b_output_schema_guardrails
```

Confirmed values:

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
testset_supporting_row_count = 83
```

The real pilot passed the implemented guardrails. No output files are tracked by git.

## Validation result

Commands run:

```text
python -m py_compile datefac_agent\audit\output_schema_guardrails.py tools\run_agent_excel_intake_audit_348a.py tests\agent\test_agent_excel_intake_audit_348a.py
  -> OK

python -m pytest tests\agent -q
  -> 74 passed in 1.52s

git diff --check
  -> clean
```

No code, tests, dependencies, input, output, or historical reports were modified by this QA task before the QA report creation.

## External call QA

Conclusion: VALID.

- R6B real pilot manifest: `llm_api_call_count=0`, `mineru_run_count=0`, `ocr_run_count=0`.
- No VLM counter exists in the current manifest and no VLM path was added.
- This QA task did not run MinerU, OCR, LLM, or VLM.

## Readiness gate QA

Conclusion: VALID.

R6B real pilot manifest:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

Gate meanings were not changed.

## Decision

`348N_R6B_QA_BLOCKED_BY_GUARDRAIL_COVERAGE_GAP`

Rationale: R6B is correct on dependency scope, runner integration, loud failures for implemented checks, review_queue historical semantics, physical review_queue CSV count validation, tests, and real pilot behavior. However, R6B introduced `clean_data_csv_row_count` as an additive physical count field but does not validate it. A manifest can contain `clean_data_row_count=1`, `clean_data_csv_row_count=999`, and one clean row, and `validate_outputs(...)` still passes. This is a direct gap against the QA checklist's additive-field safety requirement.

## Recommended next task

`348N-R6B-FIX clean_data_csv_row_count guardrail completion`

Scope:

- update `validate_outputs(...)` to validate `clean_data_csv_row_count` when present, analogous to `review_queue_csv_row_count`;
- add a negative unit test proving `clean_data_csv_row_count` mismatch raises `OutputSchemaGuardrailError`;
- rerun `py_compile`, `pytest tests\agent -q`, and the R6B Linyang pilot;
- update a short result report.

No dependency or architecture change needed.

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R6B_QA_BLOCKED_BY_GUARDRAIL_COVERAGE_GAP
new_dependency_added（是否新增依赖）= no
pydantic_used（是否使用 Pydantic）= no
pandera_used（是否使用 Pandera）= no
guardrail_module（护栏模块）= datefac_agent/audit/output_schema_guardrails.py
guardrail_loud_fail（护栏是否 loud fail）= yes for implemented checks; no for clean_data_csv_row_count mismatch because it is not checked
runner_integration_before_manifest_write（runner 是否在写 manifest 前验证）= yes
review_queue_row_count_semantics_preserved（review_queue_row_count 语义是否保留）= yes
review_queue_csv_row_count_added（是否新增物理 CSV 行数字段）= yes, validated
clean_data_forbidden_row_type_guardrail（clean_data 禁止 row_type 护栏）= valid
count_consistency_guardrail（计数一致性护栏）= partially valid; clean_data_row_count and review_queue_csv_row_count valid, clean_data_csv_row_count not validated
review_queue_required_fields_guardrail（review_queue 必填字段护栏）= valid
manifest_gate_guardrail（manifest 就绪门护栏）= valid
external_counter_guardrail（外部调用计数护栏）= valid
pytest_result（测试结果）= 74 passed
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= closed / unchanged
```
