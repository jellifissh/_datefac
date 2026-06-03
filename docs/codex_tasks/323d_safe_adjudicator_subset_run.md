# DateFac 323D Task
## Safe Semantic Adjudicator Subset Request Package and Optional Run

## 1. Stage context

DateFac has completed 323C sanity gate and 323C human spot-check routing workflow.

Latest confirmed commit:

```text
50efb2d4b9b86f7c9a3a67205216459f7d7850b2
```

323C human spot-check changed files:

```text
datefac/semantic/adjudication_batch_human_spot_check.py
datefac/semantic/adjudication_batch_human_spot_check_report.py
tools/run_adjudication_batch_human_spot_check_323c.py
```

323C human spot-check output dir:

```text
D:\_datefac\output\adjudication_batch_human_spot_check_323c
```

323C reviewed routing result:

```text
reviewed_human_item_count = 4
send_to_adjudicator_count = 11
holdout_count = 20
reclassified_scope_candidate_count = 0
reclassified_alias_candidate_count = 0
needs_more_info_count = 3
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = ADJUDICATION_BATCH_HUMAN_SPOT_CHECK_323C_REVIEWED_READY_FOR_FINAL_ROUTING
```

Key routing facts:

```text
11 items are allowed to go to adjudicator.
20 items are holdout.
3 items need more information.
0 items are pending.
0 items are reclassified.
```

323D is the next step:

> Prepare a safe semantic adjudicator subset package for the 11 SEND_TO_ADJUDICATOR items, and optionally run the adjudicator only if the project already has a safe local/request-file workflow.

323D must not apply any semantic rules. Adjudicator responses, if generated, remain suggestions only.

## 2. Goal

Implement 323D: safe semantic adjudicator subset request package and optional run.

The goal is to transform the final 323C routing plan into a compact, schema-valid request package for the 11 safe adjudicator items.

323D should support two modes:

1. `prepare` mode:
   - read final routing plan;
   - extract only SEND_TO_ADJUDICATOR items;
   - generate adjudicator request JSONL / XLSX / prompt package;
   - do not call LLM.

2. `run-offline-or-configured` mode, only if an existing safe project convention exists:
   - send or process only the prepared 11 items;
   - save raw responses to an output-only directory;
   - do not apply responses;
   - do not mark anything trusted.

If uncertain, implement only `prepare` mode.

## 3. Hard constraints

1. Do not modify production pipeline.
2. Do not modify official mapping / override assets.
3. Do not apply semantic rules.
4. Do not mark anything trusted.
5. Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
6. Do not include holdout or needs-more-info items in adjudicator requests.
7. Do not call LLM unless the task explicitly uses a safe existing configured workflow and records the call boundary.
8. Prefer prepare-only mode.
9. Use 323C final routing outputs and cached candidate data only.
10. Do not modify `E:\mineru_lab`.
11. Do not commit `output/`, `input/semantic_adjudicator_responses_*`, `temp/`, or historical dirty files.
12. Do not use `git add -A` or `git add .`.
13. Only precisely add 323D source/report/runner files.

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
D:\_datefac\output\adjudication_batch_human_spot_check_323c\adjudication_batch_human_spot_check_323c_final_routing_plan.json
```

Also read:

```text
D:\_datefac\output\adjudication_batch_human_spot_check_323c\adjudication_batch_human_spot_check_323c_reviewed_summary.json
D:\_datefac\output\adjudication_batch_human_spot_check_323c\adjudication_batch_human_spot_check_323c_reviewed_qa.json
D:\_datefac\output\adjudication_batch_sanity_gate_323c
D:\_datefac\output\semantic_adjudication_batch_prep_323ab
D:\_datefac\output\candidate_text_repair_323ar
```

Official assets may be read for reference only:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## 5. Suggested new files

Follow project style. Suggested names:

```text
datefac/semantic/safe_adjudicator_subset.py
datefac/semantic/safe_adjudicator_subset_report.py
tools/run_safe_adjudicator_subset_323d.py
```

Only add extra helpers if clearly justified.

## 6. Output directory

323D should write output artifacts to:

```text
D:\_datefac\output\safe_adjudicator_subset_323d
```

Suggested outputs:

```text
safe_adjudicator_subset_323d_summary.json
safe_adjudicator_subset_323d_qa.json
safe_adjudicator_subset_323d_request_items.jsonl
safe_adjudicator_subset_323d_request_package.json
safe_adjudicator_subset_323d_request_workbook.xlsx
safe_adjudicator_subset_323d_prompt_template.md
safe_adjudicator_subset_323d_schema.json
safe_adjudicator_subset_323d_excluded_items.xlsx
safe_adjudicator_subset_323d_notes.md
```

If optional run mode is implemented and actually used, responses should go only to an output-only directory such as:

```text
D:\_datefac\output\safe_adjudicator_subset_323d_responses
```

Do not commit output artifacts.

## 7. Request schema policy

Each adjudicator request item must be self-contained and schema-valid.

Recommended request fields:

```text
request_id
source_batch_item_id
source_group_id
candidate_type
candidate_label
candidate_question
allowed_response_labels
expected_rule_type_if_accepted
sample_candidate_ids
sample_texts
affected_candidate_count
affected_review_required_count
priority_score
risk_flags
provenance
safety_context
response_schema
```

Allowed response labels for alias items:

```text
ACCEPT_ALIAS
REJECT_ALIAS
NEEDS_MORE_INFO
OUT_OF_SCOPE
```

Allowed response labels for scope items:

```text
ACCEPT_OUT_OF_SCOPE
REJECT_OUT_OF_SCOPE
NEEDS_MORE_INFO
POSSIBLE_CORE_METRIC
```

Each response schema should require:

```text
response_label
confidence
rationale
normalized_target_metric_if_any
safety_flags
needs_human_confirmation
```

Adjudicator cannot directly create official rules.

## 8. Required behavior

### Step 1: Validate 323C final routing readiness

Load 323C reviewed summary and QA.

Require:

```text
decision = ADJUDICATION_BATCH_HUMAN_SPOT_CHECK_323C_REVIEWED_READY_FOR_FINAL_ROUTING
qa_fail_count = 0
send_to_adjudicator_count = 11
pending_count = 0
invalid_decision_count = 0
```

If this fails, stop.

### Step 2: Load final routing plan

Load final routing plan and verify:

- 34 total items preserved;
- 11 items routed to adjudicator;
- 20 holdout items excluded;
- 3 needs-more-info items excluded;
- no pending items;
- no invalid decisions.

### Step 3: Extract safe adjudicator subset

Extract only items with final route `SEND_TO_ADJUDICATOR` or equivalent safe adjudicator routing.

Must exclude:

- HOLDOUT;
- NEEDS_MORE_INFO;
- HUMAN_SPOT_CHECK_FIRST unresolved;
- category mismatch;
- ambiguous;
- invalid text;
- already official rules;
- any item not explicitly allowed for adjudicator.

### Step 4: Build request package

Build JSONL and workbook request package for the 11 safe items.

For every request, include:

- exact candidate label;
- candidate type;
- deterministic question;
- allowed response labels;
- sample rows / sample candidate IDs;
- provenance;
- risk flags;
- explicit instruction that the response is a suggestion only and must go through schema validation, deterministic gate, human confirmation, and sandbox replay before becoming any official rule.

### Step 5: Generate prompt template

Generate a prompt template suitable for the semantic adjudicator.

The prompt must instruct:

- do not invent metrics;
- do not mark rule as trusted;
- choose only allowed response labels;
- provide concise rationale;
- flag uncertainty;
- require human confirmation for all accepted suggestions.

### Step 6: Optional run boundary

If a configured adjudicator run is implemented, it must:

- only process the 11 request items;
- save raw responses;
- not parse them into accepted rules yet;
- not apply anything;
- not modify official assets;
- produce run metadata.

If no safe run is configured, output `prepare_only = true`.

### Step 7: QA

QA must include:

- 323C final routing readiness pass;
- input routing count check;
- safe subset count = 11;
- excluded holdout / needs-more-info count check;
- no unsafe item included;
- request schema completeness check;
- unique request id check;
- allowed response labels present;
- sample evidence present;
- provenance present;
- prompt template generated;
- no official asset modification confirmation;
- no parser run confirmation;
- LLM call status explicit;
- qa_fail_count.

### Step 8: Decision

If prepare-only succeeds:

```text
SAFE_ADJUDICATOR_SUBSET_323D_PREPARED_READY_FOR_CONFIGURED_ADJUDICATOR_RUN
```

If run mode succeeds and raw responses are saved:

```text
SAFE_ADJUDICATOR_SUBSET_323D_RESPONSES_READY_FOR_SCHEMA_VALIDATION
```

If anything fails:

```text
SAFE_ADJUDICATOR_SUBSET_323D_NOT_READY
```

Include blocking reasons.

## 9. Suggested command

Prepare mode:

```bash
python tools/run_safe_adjudicator_subset_323d.py \
  --mode prepare \
  --human-spot-check-dir D:\_datefac\output\adjudication_batch_human_spot_check_323c \
  --sanity-gate-dir D:\_datefac\output\adjudication_batch_sanity_gate_323c \
  --output-dir D:\_datefac\output\safe_adjudicator_subset_323d
```

If safe defaults are implemented:

```bash
python tools/run_safe_adjudicator_subset_323d.py
```

## 10. Compile / run checks

Run:

```bash
python -m py_compile datefac\semantic\safe_adjudicator_subset.py datefac\semantic\safe_adjudicator_subset_report.py tools\run_safe_adjudicator_subset_323d.py
```

Then run the 323D runner.

## 11. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 323D source files if needed. Example:

```bash
git add datefac/semantic/safe_adjudicator_subset.py
git add datefac/semantic/safe_adjudicator_subset_report.py
git add tools/run_safe_adjudicator_subset_323d.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Add 323D safe adjudicator subset package
```

Push to main only after successful checks.

## 12. Final report expected from Codex

After completion, report:

1. Modified files.
2. Commands run.
3. 323D output directory.
4. Mode used: prepare or run.
5. Safe request item count.
6. Excluded holdout / needs-more-info counts.
7. Highest-priority request examples.
8. Whether LLM/adjudicator was called.
9. qa_fail_count.
10. decision.
11. git status result.
12. commit hash.
13. push result.
