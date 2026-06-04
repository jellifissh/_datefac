# DateFac 324D Task
## Scope Noise Adjudicator Response Collection

## Context

324C scope noise safe adjudicator request prep is complete and pushed to remote main.

324C commit:

```text
279e5cffc2562ef17203613b01a15be1db40e655
```

324C output dir:

```text
D:\_datefac\output\scope_noise_safe_adjudicator_request_324c
```

324C result:

```text
request_count = 1
scope_noise_request_count = 1
risk_flags_carried_forward = INVALID_YEAR | NO_YEAR_COLUMNS | UNKNOWN_METRIC_CODE | VALUE_PARSE_FAILED | LONG_LABEL_REVIEW_REQUIRED
allowed_response_labels = ACCEPT_OUT_OF_SCOPE | REJECT_OUT_OF_SCOPE | NEEDS_MORE_INFO
llm_called = false
qa_fail_count = 0
decision = SCOPE_NOISE_SAFE_ADJUDICATOR_REQUEST_324C_READY_FOR_MANUAL_OR_CONFIGURED_ADJUDICATOR_RUN
```

324D is the next step:

> Collect one raw adjudicator response for the single 324C request.

324D should support a manual response workflow by default. It must not call an LLM unless an explicit configured mode is implemented and deliberately enabled. For this task, prefer `prepare-manual` and/or `collect-manual` from a reviewed response workbook / JSONL.

## Goal

Implement 324D: prepare and/or collect raw adjudicator response for the single 324C scope-noise request.

324D should produce a raw response collection package, not a validated decision and not a rule.

The raw response must later go through:

```text
324E schema validation + deterministic gate
324F human confirmation if accepted
324G sandbox replay if human-confirmed
```

## Hard constraints

- Do not modify production pipeline.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted directly.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator in the default/manual path.
- Use 324C request package and cached evidence only.
- Process only the single 324C request.
- Do not turn raw responses into rules.
- Do not do schema validation or deterministic gate in 324D.
- Do not produce sandbox replay candidates.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 324D source/report/runner files.

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
D:\_datefac\output\scope_noise_safe_adjudicator_request_324c
```

Expected files:

```text
scope_noise_safe_adjudicator_request_324c_summary.json
scope_noise_safe_adjudicator_request_324c_qa.json
scope_noise_safe_adjudicator_request_324c_request_package.json
scope_noise_safe_adjudicator_request_324c_request_items.jsonl
scope_noise_safe_adjudicator_request_324c_manual_prompt.md
scope_noise_safe_adjudicator_request_324c_schema.json
scope_noise_safe_adjudicator_request_324c_evidence_workbook.xlsx
```

Optional manual reviewed response source, if collecting responses:

```text
D:\_datefac\input\scope_noise_adjudicator_responses_324d\manual_responses.jsonl
```

or an output workbook copied and filled by the user.

## Suggested files

```text
datefac/semantic/scope_noise_adjudicator_response_collection_324d.py
datefac/semantic/scope_noise_adjudicator_response_collection_324d_report.py
tools/run_scope_noise_adjudicator_response_collection_324d.py
```

## Output directory

```text
D:\_datefac\output\scope_noise_adjudicator_response_collection_324d
```

Suggested outputs:

```text
scope_noise_adjudicator_response_collection_324d_summary.json
scope_noise_adjudicator_response_collection_324d_qa.json
scope_noise_adjudicator_response_collection_324d_manual_response_template.xlsx
scope_noise_adjudicator_response_collection_324d_raw_responses.jsonl
scope_noise_adjudicator_response_collection_324d_response_manifest.json
scope_noise_adjudicator_response_collection_324d_request_response_workbook.xlsx
scope_noise_adjudicator_response_collection_324d_notes.md
```

## Modes

Recommended modes:

```text
prepare-manual
collect-manual
```

### prepare-manual

Generate a manual response workbook/template from the 324C request.

Default response fields should be blank and require a human/model operator to fill:

```text
response_label
confidence
rationale
normalized_target_metric_if_any
safety_flags
needs_human_confirmation
raw_response_json
operator_note
```

Do not invent a response.

### collect-manual

Read a filled manual response workbook or JSONL and collect one raw response.

Do not validate schema beyond basic presence and request-id alignment. Full schema validation belongs to 324E.

## Required behavior

1. Validate 324C readiness:

```text
decision = SCOPE_NOISE_SAFE_ADJUDICATOR_REQUEST_324C_READY_FOR_MANUAL_OR_CONFIGURED_ADJUDICATOR_RUN
qa_fail_count = 0
request_count = 1
scope_noise_request_count = 1
llm_called = false
```

2. Load exactly one request item.
3. Preserve request id, candidate label, risk flags, sample evidence, response schema, and allowed response labels.
4. For prepare-manual:
   - create a manual response template workbook;
   - raw_response_count = 0;
   - decision = SCOPE_NOISE_ADJUDICATOR_RESPONSE_COLLECTION_324D_MANUAL_TEMPLATE_READY.
5. For collect-manual:
   - read exactly one raw response;
   - ensure request id matches the 324C request;
   - preserve raw response JSON/text exactly;
   - do not do deterministic acceptance;
   - decision = SCOPE_NOISE_ADJUDICATOR_RESPONSE_COLLECTION_324D_RAW_RESPONSE_READY_FOR_324E_SCHEMA_VALIDATION.
6. Confirm no official assets were modified.
7. Confirm no parser/LLM/adjudicator call occurred in manual mode.

## Expected prepare-manual result

```text
request_count = 1
raw_response_count = 0
response_received_count = 0
qa_fail_count = 0
decision = SCOPE_NOISE_ADJUDICATOR_RESPONSE_COLLECTION_324D_MANUAL_TEMPLATE_READY
```

## Expected collect-manual result if one response is supplied

```text
request_count = 1
raw_response_count = 1
response_received_count = 1
qa_fail_count = 0
decision = SCOPE_NOISE_ADJUDICATOR_RESPONSE_COLLECTION_324D_RAW_RESPONSE_READY_FOR_324E_SCHEMA_VALIDATION
```

## Suggested commands

Prepare manual template:

```bash
python tools/run_scope_noise_adjudicator_response_collection_324d.py \
  --mode prepare-manual \
  --safe-request-dir D:\_datefac\output\scope_noise_safe_adjudicator_request_324c \
  --output-dir D:\_datefac\output\scope_noise_adjudicator_response_collection_324d
```

Collect manual response:

```bash
python tools/run_scope_noise_adjudicator_response_collection_324d.py \
  --mode collect-manual \
  --safe-request-dir D:\_datefac\output\scope_noise_safe_adjudicator_request_324c \
  --manual-response-workbook D:\_datefac\output\scope_noise_adjudicator_response_collection_324d\scope_noise_adjudicator_response_collection_324d_manual_response_template.xlsx \
  --output-dir D:\_datefac\output\scope_noise_adjudicator_response_collection_324d
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\scope_noise_adjudicator_response_collection_324d.py datefac\semantic\scope_noise_adjudicator_response_collection_324d_report.py tools\run_scope_noise_adjudicator_response_collection_324d.py
```

Then run prepare-manual mode at minimum.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/scope_noise_adjudicator_response_collection_324d.py
git add datefac/semantic/scope_noise_adjudicator_response_collection_324d_report.py
git add tools/run_scope_noise_adjudicator_response_collection_324d.py
```

Suggested commit message:

```text
Add 324D scope noise adjudicator response collection
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Mode used.
5. Request count.
6. Raw response count.
7. Response received count.
8. Whether LLM/adjudicator was called.
9. qa_fail_count.
10. decision.
11. Whether collect-manual mode was implemented.
12. git status result.
13. commit hash.
14. push result.
