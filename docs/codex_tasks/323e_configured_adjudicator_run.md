# DateFac 323E Task
## Configured Safe Adjudicator Run and Raw Response Collection

## 1. Stage context

DateFac has completed 323D safe adjudicator subset package.

323D commit:

```text
07c4442e2999a4786138d3e9a03bab7344ea0b60
```

323D changed files:

```text
datefac/semantic/safe_adjudicator_subset.py
datefac/semantic/safe_adjudicator_subset_report.py
tools/run_safe_adjudicator_subset_323d.py
```

323D output dir:

```text
D:\_datefac\output\safe_adjudicator_subset_323d
```

323D result:

```text
mode = prepare
prepare_only = true
safe_request_item_count = 11
excluded_holdout_count = 20
excluded_needs_more_info_count = 3
alias_request_count = 2
scope_request_count = 9
qa_fail_count = 0
decision = SAFE_ADJUDICATOR_SUBSET_323D_PREPARED_READY_FOR_CONFIGURED_ADJUDICATOR_RUN
```

Highest-priority request examples:

```text
323d__323ab__alias__023 | alias | EBITDA
323d__323ab__alias__024 | alias | 归属母公司净利润
323d__323ab__scope_noise__001 | scope_noise | 其他非流动负债
323d__323ab__scope_noise__002 | scope_noise | 其他非流动资产
323d__323ab__scope_noise__003 | scope_noise | 股票代码
```

323E is the next step:

> Run or collect semantic adjudicator responses for only the 11 safe 323D request items.

323E must collect raw responses only. It must not validate them into accepted rules, must not apply rules, and must not mark anything trusted.

## 2. Goal

Implement 323E: configured safe adjudicator run and raw response collection.

323E should read the 323D request package and either:

1. run an existing configured semantic adjudicator workflow safely for exactly 11 items, or
2. if no safe configured runner exists, generate a clear manual-response package and stop with a NOT_READY_FOR_AUTOMATED_RUN decision.

The preferred output is a raw response package ready for the next stage, 323F schema validation and deterministic gate.

## 3. Hard constraints

1. Do not modify production pipeline.
2. Do not modify official mapping / override assets.
3. Do not apply semantic rules.
4. Do not mark anything trusted.
5. Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
6. Process only the 11 request items from 323D.
7. Do not include holdout or needs-more-info items.
8. Do not invent responses.
9. Do not parse raw responses into accepted mappings in this stage.
10. Do not write to `input/semantic_adjudicator_responses_*` unless explicitly required by an existing project convention; prefer output-only paths.
11. Do not commit raw response outputs, output directories, temp files, or `input/semantic_adjudicator_responses_*`.
12. Do not modify `E:\mineru_lab`.
13. Do not use `git add -A` or `git add .`.
14. Only precisely add 323E source/report/runner files.

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
D:\_datefac\output\safe_adjudicator_subset_323d
```

Expected files include:

```text
safe_adjudicator_subset_323d_request_items.jsonl
safe_adjudicator_subset_323d_request_package.json
safe_adjudicator_subset_323d_request_workbook.xlsx
safe_adjudicator_subset_323d_prompt_template.md
safe_adjudicator_subset_323d_schema.json
safe_adjudicator_subset_323d_qa.json
safe_adjudicator_subset_323d_summary.json
```

## 5. Suggested new files

Follow project style. Suggested names:

```text
datefac/semantic/configured_adjudicator_run.py
datefac/semantic/configured_adjudicator_run_report.py
tools/run_configured_adjudicator_run_323e.py
```

Only add extra helpers if clearly justified.

## 6. Output directory

323E should write output artifacts to:

```text
D:\_datefac\output\configured_adjudicator_run_323e
```

Suggested outputs:

```text
configured_adjudicator_run_323e_summary.json
configured_adjudicator_run_323e_qa.json
configured_adjudicator_run_323e_raw_responses.jsonl
configured_adjudicator_run_323e_response_manifest.json
configured_adjudicator_run_323e_request_response_workbook.xlsx
configured_adjudicator_run_323e_run_metadata.json
configured_adjudicator_run_323e_manual_response_template.xlsx
configured_adjudicator_run_323e_notes.md
```

Do not commit output artifacts.

## 7. Required behavior

### Step 1: Validate 323D readiness

Load 323D summary and QA.

Require:

```text
decision = SAFE_ADJUDICATOR_SUBSET_323D_PREPARED_READY_FOR_CONFIGURED_ADJUDICATOR_RUN
qa_fail_count = 0
safe_request_item_count = 11
alias_request_count = 2
scope_request_count = 9
excluded_holdout_count = 20
excluded_needs_more_info_count = 3
prepare_only = true
```

If this fails, stop.

### Step 2: Load request items

Load exactly 11 request items from the 323D JSONL / JSON package.

Validate:

- request count = 11;
- every request id is unique;
- every request has response_schema;
- every request has allowed_response_labels;
- every request has sample evidence;
- every request has safety_context;
- every request states suggestions require schema validation, deterministic gate, human confirmation, and sandbox replay.

### Step 3: Resolve run mode

Support at least two modes:

```text
prepare-manual
configured-run
```

Default should be `prepare-manual` unless a safe configured adjudicator runner is already present and explicitly requested.

In `prepare-manual` mode:

- generate a manual response template workbook / JSONL;
- do not call LLM;
- decision should indicate manual or configured run is still required.

In `configured-run` mode:

- use only an existing safe project convention or explicitly configured endpoint;
- process exactly 11 requests;
- save raw responses;
- do not validate into official suggestions yet;
- do not apply anything.

### Step 4: Raw response contract

Each raw response, whether manual template or model output, must be associated with:

```text
request_id
source_batch_item_id
candidate_type
candidate_label
raw_response_text or raw_response_json
response_received
provider_or_source
model_or_review_source
run_timestamp
```

Raw responses should not be treated as accepted decisions in 323E.

### Step 5: QA

QA must include:

- 323D readiness pass;
- request count = 11;
- no holdout item included;
- no needs-more-info item included;
- request schema completeness;
- unique request id check;
- run mode explicitly recorded;
- LLM/adjudicator call status explicitly recorded;
- if configured-run: raw response count = 11;
- if prepare-manual: manual response template generated;
- official assets not modified;
- parser not run;
- no semantic rule application;
- qa_fail_count.

### Step 6: Decision

If prepare-manual succeeds without LLM call:

```text
CONFIGURED_ADJUDICATOR_RUN_323E_MANUAL_RESPONSE_TEMPLATE_READY
```

If configured-run succeeds and 11 raw responses are saved:

```text
CONFIGURED_ADJUDICATOR_RUN_323E_RAW_RESPONSES_READY_FOR_323F_SCHEMA_VALIDATION
```

If no safe run can be configured and no manual template is generated:

```text
CONFIGURED_ADJUDICATOR_RUN_323E_NOT_READY
```

If anything fails, include blocking reasons.

## 8. Suggested commands

Prepare manual mode:

```bash
python tools/run_configured_adjudicator_run_323e.py \
  --mode prepare-manual \
  --safe-subset-dir D:\_datefac\output\safe_adjudicator_subset_323d \
  --output-dir D:\_datefac\output\configured_adjudicator_run_323e
```

Configured run mode, only if safe and explicitly configured:

```bash
python tools/run_configured_adjudicator_run_323e.py \
  --mode configured-run \
  --safe-subset-dir D:\_datefac\output\safe_adjudicator_subset_323d \
  --output-dir D:\_datefac\output\configured_adjudicator_run_323e
```

## 9. Compile / run checks

Run:

```bash
python -m py_compile datefac\semantic\configured_adjudicator_run.py datefac\semantic\configured_adjudicator_run_report.py tools\run_configured_adjudicator_run_323e.py
```

Then run the 323E runner in the chosen mode.

## 10. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 323E source files. Example:

```bash
git add datefac/semantic/configured_adjudicator_run.py
git add datefac/semantic/configured_adjudicator_run_report.py
git add tools/run_configured_adjudicator_run_323e.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Add 323E configured adjudicator run package
```

Push to main only after successful checks.

## 11. Final report expected from Codex

After completion, report:

1. Modified files.
2. Commands run.
3. 323E output directory.
4. Mode used.
5. Request count.
6. Raw response count if any.
7. Whether LLM/adjudicator was called.
8. Highest-priority response/template examples.
9. qa_fail_count.
10. decision.
11. git status result.
12. commit hash.
13. push result.
