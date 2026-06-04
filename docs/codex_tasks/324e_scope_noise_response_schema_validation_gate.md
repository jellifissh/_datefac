# DateFac 324E Task
## Scope Noise Raw Response Schema Validation and Deterministic Gate

## Context

324D scope noise adjudicator response collection is complete. The implementation is already on remote main.

324D implementation HEAD:

```text
7b31f58df88ffdc808bf35d621a02702674b75fd
```

324D collect-manual was run locally with the filled manual response workbook.

324D output dir:

```text
D:\_datefac\output\scope_noise_adjudicator_response_collection_324d
```

324D collect-manual result:

```text
request_count = 1
raw_response_count = 1
response_received_count = 1
request_id matched = Yes
llm_called = false
qa_fail_count = 0
decision = SCOPE_NOISE_ADJUDICATOR_RESPONSE_COLLECTION_324D_RAW_RESPONSE_READY_FOR_324E_SCHEMA_VALIDATION
```

324E is the next step:

> Validate the single raw response from 324D against the 324C response schema and apply deterministic safety gates.

324E must not confirm the suggestion as final, must not apply rules, and must not create sandbox replay candidates unless the response passes schema and deterministic safety gates.

## Goal

Implement 324E: schema validation and deterministic gate for the single 324D raw response.

324E should classify the response into one of:

```text
ACCEPTED_FOR_HUMAN_CONFIRMATION
REJECTED_BY_SCHEMA
REJECTED_BY_DETERMINISTIC_GATE
NEEDS_MORE_INFO
REJECTED_OUT_OF_SCOPE_SUGGESTION
```

If the response is an acceptable `ACCEPT_OUT_OF_SCOPE` suggestion, it must still require human confirmation before sandbox replay.

## Hard constraints

- Do not modify production pipeline.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted directly.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 324D raw response output and 324C request schema only.
- Process only the single 324D raw response.
- Do not produce official rule candidates.
- Do not modify official assets.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 324E source/report/runner files.

Known existing dirty files to leave untouched:

```text
datefac/benchmark/batch_row_text_delivery_benchmark.py
datefac/extraction/row_text_metric_extractor.py
datefac/pipeline/batch_ppstructure_row_text_pipeline.py
tools/run_batch_ppstructure_outputs_320g.py
input/semantic_adjudicator_responses_322d/
input/semantic_adjudicator_responses_322f/
temp/
```

## Inputs

Primary input:

```text
D:\_datefac\output\scope_noise_adjudicator_response_collection_324d
```

Expected files may include:

```text
scope_noise_adjudicator_response_collection_324d_summary.json
scope_noise_adjudicator_response_collection_324d_qa.json
scope_noise_adjudicator_response_collection_324d_raw_responses.jsonl
scope_noise_adjudicator_response_collection_324d_response_manifest.json
scope_noise_adjudicator_response_collection_324d_request_response_workbook.xlsx
```

Reference input:

```text
D:\_datefac\output\scope_noise_safe_adjudicator_request_324c
```

Expected request schema:

```text
scope_noise_safe_adjudicator_request_324c_schema.json
scope_noise_safe_adjudicator_request_324c_request_package.json
scope_noise_safe_adjudicator_request_324c_request_items.jsonl
```

Official assets may be read only for safety/reference checks:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/scope_noise_response_schema_validation_324e.py
datefac/semantic/scope_noise_response_schema_validation_324e_report.py
tools/run_scope_noise_response_schema_validation_324e.py
```

## Output directory

```text
D:\_datefac\output\scope_noise_response_schema_validation_324e
```

Suggested outputs:

```text
scope_noise_response_schema_validation_324e_summary.json
scope_noise_response_schema_validation_324e_qa.json
scope_noise_response_schema_validation_324e_validated_responses.json
scope_noise_response_schema_validation_324e_validated_responses.xlsx
scope_noise_response_schema_validation_324e_gate_report.xlsx
scope_noise_response_schema_validation_324e_candidate_for_human_confirmation.json
scope_noise_response_schema_validation_324e_notes.md
```

## Required response schema

The raw response must conform to the 324C schema and include:

```text
request_id
response_label
confidence
rationale
normalized_target_metric_if_any
safety_flags
needs_human_confirmation
```

Allowed response labels:

```text
ACCEPT_OUT_OF_SCOPE
REJECT_OUT_OF_SCOPE
NEEDS_MORE_INFO
```

Allowed confidence values:

```text
high
medium
low
```

## Deterministic gate rules

### Common gates

For all response labels:

1. `request_id` must match the 324C request id.
2. `response_label` must be allowed.
3. `confidence` must be one of the allowed values.
4. `rationale` must be non-empty.
5. `needs_human_confirmation` must be boolean.
6. Official assets must remain unchanged.

### ACCEPT_OUT_OF_SCOPE gates

If `response_label = ACCEPT_OUT_OF_SCOPE`, require:

```text
normalized_target_metric_if_any is null or empty
needs_human_confirmation = true
confidence in {high, medium}
safety_flags does not contain blocking flags
```

Blocking safety flags include, but are not limited to:

```text
CORE_METRIC_RISK
WEAK_EVIDENCE
CONFLICT
UNIT_AMBIGUITY
NEEDS_MORE_INFO
LOW_CONFIDENCE
```

If accepted by schema and gate, output status:

```text
ACCEPTED_FOR_HUMAN_CONFIRMATION
```

and decision:

```text
SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_READY_FOR_324F_HUMAN_CONFIRMATION
```

### REJECT_OUT_OF_SCOPE gates

If `response_label = REJECT_OUT_OF_SCOPE`, output status:

```text
REJECTED_OUT_OF_SCOPE_SUGGESTION
```

and decision:

```text
SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_REJECTED_NO_SANDBOX_REPLAY
```

### NEEDS_MORE_INFO gates

If `response_label = NEEDS_MORE_INFO`, output status:

```text
NEEDS_MORE_INFO
```

and decision:

```text
SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_NEEDS_MORE_INFO_NO_SANDBOX_REPLAY
```

## Required behavior

1. Validate 324D readiness:

```text
decision = SCOPE_NOISE_ADJUDICATOR_RESPONSE_COLLECTION_324D_RAW_RESPONSE_READY_FOR_324E_SCHEMA_VALIDATION
qa_fail_count = 0
request_count = 1
raw_response_count = 1
response_received_count = 1
llm_called = false
```

2. Load exactly one 324D raw response.
3. Load the 324C response schema and request item.
4. Parse raw response JSON.
5. Validate schema.
6. Apply deterministic gates.
7. Generate validated response package and QA.
8. Confirm no parser/LLM/adjudicator call occurred in 324E.
9. Confirm official assets were not modified.
10. Do not create official candidates, rules, or sandbox replay package here.

## Expected result if raw response accepts out-of-scope safely

```text
request_count = 1
response_count = 1
schema_valid_count = 1
schema_invalid_count = 0
accepted_for_human_confirmation_count = 1
rejected_by_schema_count = 0
rejected_by_deterministic_gate_count = 0
needs_more_info_count = 0
rejected_out_of_scope_suggestion_count = 0
qa_fail_count = 0
decision = SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_READY_FOR_324F_HUMAN_CONFIRMATION
```

## Expected result if response rejects out-of-scope

```text
request_count = 1
response_count = 1
schema_valid_count = 1
rejected_out_of_scope_suggestion_count = 1
qa_fail_count = 0
decision = SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_REJECTED_NO_SANDBOX_REPLAY
```

## Expected result if response needs more info

```text
request_count = 1
response_count = 1
schema_valid_count = 1
needs_more_info_count = 1
qa_fail_count = 0
decision = SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_NEEDS_MORE_INFO_NO_SANDBOX_REPLAY
```

## Suggested command

```bash
python tools/run_scope_noise_response_schema_validation_324e.py \
  --response-collection-dir D:\_datefac\output\scope_noise_adjudicator_response_collection_324d \
  --safe-request-dir D:\_datefac\output\scope_noise_safe_adjudicator_request_324c \
  --output-dir D:\_datefac\output\scope_noise_response_schema_validation_324e
```

If safe defaults are implemented:

```bash
python tools/run_scope_noise_response_schema_validation_324e.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\scope_noise_response_schema_validation_324e.py datefac\semantic\scope_noise_response_schema_validation_324e_report.py tools\run_scope_noise_response_schema_validation_324e.py
```

Then run the 324E runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/scope_noise_response_schema_validation_324e.py
git add datefac/semantic/scope_noise_response_schema_validation_324e_report.py
git add tools/run_scope_noise_response_schema_validation_324e.py
```

Suggested commit message:

```text
Add 324E scope noise response schema validation gate
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Request / response counts.
5. Schema valid / invalid counts.
6. Deterministic gate result.
7. Accepted / rejected / needs-more-info counts.
8. Whether official assets were modified.
9. qa_fail_count.
10. decision.
11. git status result.
12. commit hash.
13. push result.
