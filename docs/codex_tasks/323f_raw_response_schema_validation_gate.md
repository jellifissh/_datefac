# DateFac 323F Task
## Raw Response Schema Validation and Deterministic Gate

## 1. Stage context

DateFac has completed 323E raw response collection from the 323D safe adjudicator subset.

323D prepared exactly 11 safe request items:

```text
safe_request_item_count = 11
alias_request_count = 2
scope_request_count = 9
excluded_holdout_count = 20
excluded_needs_more_info_count = 3
qa_fail_count = 0
decision = SAFE_ADJUDICATOR_SUBSET_323D_PREPARED_READY_FOR_CONFIGURED_ADJUDICATOR_RUN
```

323E was first implemented as prepare-manual and then rerun with a reviewed manual response source.

Latest 323E raw response collection result:

```text
request_count = 11
raw_response_count = 11
response_received_count = 11
qa_fail_count = 0
decision = CONFIGURED_ADJUDICATOR_RUN_323E_RAW_RESPONSES_READY_FOR_323F_SCHEMA_VALIDATION
```

Important note:

```text
The 323E configured-run did not call an external LLM. It read the reviewed workbook converted to JSONL and collected those manual responses as raw responses. Treat them as raw adjudication responses, not official rules.
```

323E output dir:

```text
D:\_datefac\output\configured_adjudicator_run_323e
```

Key files:

```text
configured_adjudicator_run_323e_summary.json
configured_adjudicator_run_323e_qa.json
configured_adjudicator_run_323e_raw_responses.jsonl
configured_adjudicator_run_323e_response_manifest.json
configured_adjudicator_run_323e_request_response_workbook.xlsx
```

323F is the next step:

> Validate the 11 raw responses against response schema and deterministic safety gates, then classify them as accepted suggestions, rejected suggestions, or needs-more-info suggestions.

323F must not apply any semantic rules and must not mark anything trusted.

## 2. Goal

Implement 323F: raw response schema validation and deterministic gate.

The goal is to read the 11 raw responses collected in 323E, validate them against the response schema from 323D, and produce a gated response package for the next human/proposal stage.

323F should produce structured outputs such as:

- schema-valid accepted suggestions;
- schema-valid rejected suggestions;
- needs-more-info suggestions;
- schema-invalid responses;
- deterministic-gate failures;
- QA and decision.

323F must not create official rules, must not modify official assets, and must not apply responses to trusted data.

## 3. Hard constraints

1. Do not modify production pipeline.
2. Do not modify official mapping / override assets.
3. Do not apply semantic rules.
4. Do not mark anything trusted.
5. Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
6. Do not call LLM / semantic adjudicator.
7. Process only the 11 raw responses from 323E.
8. Do not include holdout or needs-more-info items excluded before 323E.
9. Do not invent missing responses.
10. Do not promote ACCEPT_* responses directly to official rules.
11. Every accepted suggestion must still require human confirmation and sandbox replay.
12. Do not commit `output/`, `input/semantic_adjudicator_responses_*`, `temp/`, or historical dirty files.
13. Do not modify `E:\mineru_lab`.
14. Do not use `git add -A` or `git add .`.
15. Only precisely add 323F source/report/runner files.

Known pre-existing dirty files that must remain untouched:

```text
datefac/benchmark/batch_row_text_delivery_benchmark.py
datefac/extraction/row_text_metric_extractor.py
datefac/pipeline/batch_ppstructure_row_text_pipeline.py
tools/run_batch_ppstructure_outputs_320g.py
input/semantic_adjudicator_responses_322d/
input/semantic_adjudicator_responses_322f/
temp/
```

## 4. Inputs

Primary input:

```text
D:\_datefac\output\configured_adjudicator_run_323e
```

Expected files:

```text
configured_adjudicator_run_323e_summary.json
configured_adjudicator_run_323e_qa.json
configured_adjudicator_run_323e_raw_responses.jsonl
configured_adjudicator_run_323e_response_manifest.json
configured_adjudicator_run_323e_request_response_workbook.xlsx
```

Also read 323D request package for schema and request context:

```text
D:\_datefac\output\safe_adjudicator_subset_323d
```

Official assets may be read for conflict/reference checks only:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## 5. Suggested new files

Follow project style. Suggested names:

```text
datefac/semantic/raw_response_schema_validation.py
datefac/semantic/raw_response_schema_validation_report.py
tools/run_raw_response_schema_validation_323f.py
```

Only add extra helpers if clearly justified.

## 6. Output directory

323F should write output artifacts to:

```text
D:\_datefac\output\raw_response_schema_validation_323f
```

Suggested outputs:

```text
raw_response_schema_validation_323f_summary.json
raw_response_schema_validation_323f_qa.json
raw_response_schema_validation_323f_validated_responses.jsonl
raw_response_schema_validation_323f_accepted_suggestions.json
raw_response_schema_validation_323f_rejected_suggestions.json
raw_response_schema_validation_323f_needs_more_info.json
raw_response_schema_validation_323f_schema_invalid.xlsx
raw_response_schema_validation_323f_gate_failures.xlsx
raw_response_schema_validation_323f_review_package.xlsx
raw_response_schema_validation_323f_notes.md
```

Do not commit output artifacts.

## 7. Required behavior

### Step 1: Validate 323E readiness

Load 323E summary and QA.

Require:

```text
decision = CONFIGURED_ADJUDICATOR_RUN_323E_RAW_RESPONSES_READY_FOR_323F_SCHEMA_VALIDATION
qa_fail_count = 0
request_count = 11
raw_response_count = 11
response_received_count = 11
```

If this fails, stop.

### Step 2: Load requests and raw responses

Load the 11 request items from 323D and the 11 raw responses from 323E.

Validate:

- request ids match exactly;
- no missing response;
- no duplicate response;
- no response for unknown request id;
- every raw response has `response_received = true`.

### Step 3: Parse raw response JSON

For each raw response:

- parse `raw_response_json` if present;
- if only `raw_response_text` exists, parse only if it is valid JSON text;
- do not infer or invent fields;
- preserve original raw response text / JSON.

### Step 4: Schema validation

Validate parsed response against the request's `response_schema`.

Required response fields:

```text
response_label
confidence
rationale
normalized_target_metric_if_any
safety_flags
needs_human_confirmation
```

Allowed `confidence` values:

```text
high
medium
low
```

Allowed labels for alias requests:

```text
ACCEPT_ALIAS
REJECT_ALIAS
NEEDS_MORE_INFO
OUT_OF_SCOPE
```

Allowed labels for scope_noise requests:

```text
ACCEPT_OUT_OF_SCOPE
REJECT_OUT_OF_SCOPE
NEEDS_MORE_INFO
POSSIBLE_CORE_METRIC
```

Responses outside the allowed labels must be schema-invalid.

### Step 5: Deterministic safety gate

Schema-valid responses must also pass deterministic gates.

For alias accepted suggestions:

- `response_label = ACCEPT_ALIAS`;
- candidate type must be `alias`;
- `normalized_target_metric_if_any` must be non-empty;
- confidence should be high or medium;
- `needs_human_confirmation` must be true;
- no safety flag may indicate conflict / weak evidence / possible scope mismatch;
- target metric must be in selected-core or recognized canonical metric set if such a set exists.

For scope accepted suggestions:

- `response_label = ACCEPT_OUT_OF_SCOPE`;
- candidate type must be `scope_noise`;
- `normalized_target_metric_if_any` should be null or empty;
- confidence should be high or medium;
- `needs_human_confirmation` must be true;
- no safety flag may indicate possible core metric;
- candidate must not look like a selected core metric.

For rejected / needs-more-info responses:

- preserve them, but do not include in accepted suggestion proposals.

### Step 6: Classification

Classify each response into exactly one bucket:

```text
ACCEPTED_SUGGESTION
REJECTED_SUGGESTION
NEEDS_MORE_INFO
SCHEMA_INVALID
DETERMINISTIC_GATE_FAILED
```

No item should be lost.

### Step 7: Generate review package

Generate a human-readable review package with:

- all validated responses;
- accepted suggestions;
- rejected suggestions;
- needs-more-info;
- schema invalids;
- deterministic gate failures;
- source request evidence;
- rationale;
- safety flags;
- next action.

Accepted suggestions are still proposals only.

### Step 8: QA

QA must include:

- 323E readiness pass;
- request/response id alignment pass;
- raw response count = 11;
- schema validation count;
- schema invalid count;
- accepted suggestion count;
- rejected suggestion count;
- needs-more-info count;
- deterministic gate failure count;
- every response classified exactly once;
- no official asset modification confirmation;
- no parser run confirmation;
- no LLM call confirmation;
- no trusted promotion confirmation;
- output artifact presence check;
- qa_fail_count.

### Step 9: Decision

If validation succeeds and there is at least one accepted suggestion:

```text
RAW_RESPONSE_SCHEMA_VALIDATION_323F_READY_FOR_HUMAN_CONFIRMED_SUGGESTION_PROPOSALS
```

If validation succeeds but no accepted suggestions exist:

```text
RAW_RESPONSE_SCHEMA_VALIDATION_323F_NO_ACCEPTED_SUGGESTIONS
```

If validation fails:

```text
RAW_RESPONSE_SCHEMA_VALIDATION_323F_NOT_READY
```

Include blocking reasons.

## 8. Suggested command

```bash
python tools/run_raw_response_schema_validation_323f.py \
  --configured-run-dir D:\_datefac\output\configured_adjudicator_run_323e \
  --safe-subset-dir D:\_datefac\output\safe_adjudicator_subset_323d \
  --output-dir D:\_datefac\output\raw_response_schema_validation_323f
```

If safe defaults are implemented:

```bash
python tools/run_raw_response_schema_validation_323f.py
```

## 9. Compile / run checks

Run:

```bash
python -m py_compile datefac\semantic\raw_response_schema_validation.py datefac\semantic\raw_response_schema_validation_report.py tools\run_raw_response_schema_validation_323f.py
```

Then run the 323F runner.

## 10. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 323F source files. Example:

```bash
git add datefac/semantic/raw_response_schema_validation.py
git add datefac/semantic/raw_response_schema_validation_report.py
git add tools/run_raw_response_schema_validation_323f.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Add 323F raw response schema validation gate
```

Push to main only after successful checks.

## 11. Final report expected from Codex

After completion, report:

1. Modified files.
2. Commands run.
3. 323F output directory.
4. Request / response count.
5. Schema valid / invalid counts.
6. Accepted / rejected / needs-more-info counts.
7. Deterministic gate failure count.
8. Accepted suggestion examples.
9. qa_fail_count.
10. decision.
11. git status result.
12. commit hash.
13. push result.
