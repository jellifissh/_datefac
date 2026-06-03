# DateFac 323G Task
## Human-Confirmed Semantic Suggestion Proposals

## 1. Stage context

DateFac has completed 323F raw response schema validation and deterministic gate.

323F commit:

```text
fec1637d4175fcf1b260dee1d3979d7ac64ea504
```

323F changed files:

```text
datefac/semantic/raw_response_schema_validation.py
datefac/semantic/raw_response_schema_validation_report.py
tools/run_raw_response_schema_validation_323f.py
```

323F output dir:

```text
D:\_datefac\output\raw_response_schema_validation_323f
```

323F result:

```text
request_count = 11
response_count = 11
schema_valid_count = 11
schema_invalid_count = 0
accepted_suggestion_count = 11
rejected_suggestion_count = 0
needs_more_info_count = 0
deterministic_gate_failure_count = 0
qa_fail_count = 0
decision = RAW_RESPONSE_SCHEMA_VALIDATION_323F_READY_FOR_HUMAN_CONFIRMED_SUGGESTION_PROPOSALS
```

Accepted suggestion examples:

```text
323d::323ab__scope_noise__001 -> ACCEPT_OUT_OF_SCOPE
323d::323ab__scope_noise__002 -> ACCEPT_OUT_OF_SCOPE
323d::323ab__alias__023 -> ACCEPT_ALIAS target EBITDA
323d::323ab__alias__024 -> ACCEPT_ALIAS target 归母净利润
```

323G is the next step:

> Convert the 323F accepted suggestions into a human-confirmation proposal package.

323G must not apply semantic rules, must not mark anything trusted, and must not modify official assets.

## 2. Goal

Implement 323G: human-confirmed semantic suggestion proposals.

The goal is to produce a reviewable human confirmation package from the 11 schema-valid, deterministic-gate-passing accepted suggestions from 323F.

323G should support two modes:

1. `prepare` mode:
   - generate an approval workbook / JSON package;
   - default every suggestion to `PENDING_HUMAN_CONFIRMATION`;
   - do not assume approval.

2. `validate-reviewed` mode, if straightforward and safe:
   - read a human-reviewed workbook;
   - validate human decisions;
   - produce a human-confirmed suggestion plan for 323H sandbox replay;
   - still do not apply rules.

If implementing only one mode, prioritize `prepare` mode.

## 3. Hard constraints

1. Do not modify production pipeline.
2. Do not modify official mapping / override assets.
3. Do not apply semantic rules.
4. Do not mark anything trusted.
5. Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
6. Do not call LLM / semantic adjudicator.
7. Process only accepted suggestions from 323F.
8. Do not include rejected / needs-more-info / schema-invalid / deterministic-gate-failed responses.
9. Do not assume human approval.
10. Do not promote accepted suggestions directly to official rules.
11. Every confirmed suggestion must still go through sandbox replay before official candidates.
12. Do not commit `output/`, `input/semantic_adjudicator_responses_*`, `temp/`, or historical dirty files.
13. Do not modify `E:\mineru_lab`.
14. Do not use `git add -A` or `git add .`.
15. Only precisely add 323G source/report/runner files.

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
D:\_datefac\output\raw_response_schema_validation_323f
```

Expected files:

```text
raw_response_schema_validation_323f_summary.json
raw_response_schema_validation_323f_qa.json
raw_response_schema_validation_323f_validated_responses.jsonl
raw_response_schema_validation_323f_accepted_suggestions.json
raw_response_schema_validation_323f_review_package.xlsx
```

Also read for context:

```text
D:\_datefac\output\safe_adjudicator_subset_323d
D:\_datefac\output\configured_adjudicator_run_323e
```

Official assets may be read for reference checks only:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## 5. Suggested new files

Follow project style. Suggested names:

```text
datefac/semantic/human_confirmed_suggestion_proposals.py
datefac/semantic/human_confirmed_suggestion_proposals_report.py
tools/run_human_confirmed_suggestion_proposals_323g.py
```

Only add extra helpers if clearly justified.

## 6. Output directory

323G should write output artifacts to:

```text
D:\_datefac\output\human_confirmed_suggestion_proposals_323g
```

Suggested outputs for prepare mode:

```text
human_confirmed_suggestion_proposals_323g_summary.json
human_confirmed_suggestion_proposals_323g_qa.json
human_confirmed_suggestion_proposals_323g_confirmation_workbook.xlsx
human_confirmed_suggestion_proposals_323g_proposal_package.json
human_confirmed_suggestion_proposals_323g_alias_suggestions.xlsx
human_confirmed_suggestion_proposals_323g_scope_suggestions.xlsx
human_confirmed_suggestion_proposals_323g_review_instructions.md
```

If validate-reviewed mode is implemented:

```text
human_confirmed_suggestion_proposals_323g_reviewed_summary.json
human_confirmed_suggestion_proposals_323g_reviewed_qa.json
human_confirmed_suggestion_proposals_323g_human_confirmed_plan.json
human_confirmed_suggestion_proposals_323g_reviewed_workbook.xlsx
```

Do not commit output artifacts.

## 7. Prepare mode required behavior

### Step 1: Validate 323F readiness

Load 323F summary and QA.

Require:

```text
decision = RAW_RESPONSE_SCHEMA_VALIDATION_323F_READY_FOR_HUMAN_CONFIRMED_SUGGESTION_PROPOSALS
qa_fail_count = 0
request_count = 11
response_count = 11
schema_valid_count = 11
schema_invalid_count = 0
accepted_suggestion_count = 11
rejected_suggestion_count = 0
needs_more_info_count = 0
deterministic_gate_failure_count = 0
```

If this fails, stop.

### Step 2: Load accepted suggestions

Load exactly 11 accepted suggestions from 323F.

Expected count:

```text
total_accepted_suggestion_count = 11
alias_accepted_suggestion_count = 2
scope_accepted_suggestion_count = 9
```

Each accepted suggestion should retain:

- request id;
- source batch item id;
- candidate type;
- candidate label;
- response label;
- confidence;
- rationale;
- normalized target metric if any;
- safety flags;
- gate details;
- sample evidence;
- provenance;
- expected affected count;
- expected review reduction potential;
- source raw response reference.

### Step 3: Build human confirmation records

Create one confirmation record per accepted suggestion.

Each record should include:

```text
confirmation_id
request_id
source_batch_item_id
suggestion_type
candidate_label
suggested_response_label
suggested_target_metric_if_any
confidence
rationale
sample_evidence
provenance
expected_impact
risk_note
sandbox_replay_required
reviewer_decision
reviewer_note
reviewer_name
review_timestamp
allowed_reviewer_decisions
```

Default reviewer decision must be:

```text
PENDING_HUMAN_CONFIRMATION
```

Allowed human decisions:

```text
CONFIRM
REJECT
NEEDS_MORE_INFO
```

323G prepare mode must not default anything to `CONFIRM`.

### Step 4: Generate workbook and JSON package

Generate:

- confirmation workbook;
- proposal package JSON;
- alias suggestions sheet;
- scope suggestions sheet;
- review instructions.

The workbook should clearly mark editable fields:

```text
reviewer_decision
reviewer_note
reviewer_name
review_timestamp
```

### Step 5: QA

QA must include:

- 323F readiness pass;
- accepted suggestion count = 11;
- alias suggestion count = 2;
- scope suggestion count = 9;
- no rejected / needs-more-info / schema-invalid items included;
- default decisions all PENDING_HUMAN_CONFIRMATION;
- required reviewer fields present;
- provenance completeness;
- sample evidence present;
- sandbox replay required flag present;
- unique confirmation id check;
- no official asset modification confirmation;
- no parser run confirmation;
- no LLM call confirmation;
- qa_fail_count.

### Step 6: Prepare decision

If all checks pass:

```text
HUMAN_CONFIRMED_SUGGESTION_PROPOSALS_323G_READY_FOR_HUMAN_CONFIRMATION
```

If not:

```text
HUMAN_CONFIRMED_SUGGESTION_PROPOSALS_323G_NOT_READY
```

## 8. Validate-reviewed mode behavior

If implemented, validate-reviewed mode should:

1. Read a reviewed confirmation workbook.
2. Require every reviewer decision to be one of:
   - `CONFIRM`
   - `REJECT`
   - `NEEDS_MORE_INFO`
3. Require no `PENDING_HUMAN_CONFIRMATION` before producing a final confirmed plan.
4. Produce a human-confirmed plan containing only `CONFIRM` records.
5. Preserve rejected and needs-more-info records separately.
6. Still not apply rules or run sandbox replay.

If all reviewed decisions are valid and at least one confirmed suggestion exists:

```text
HUMAN_CONFIRMED_SUGGESTION_PROPOSALS_323G_REVIEWED_READY_FOR_323H_SANDBOX_REPLAY
```

If not:

```text
HUMAN_CONFIRMED_SUGGESTION_PROPOSALS_323G_REVIEWED_NOT_READY
```

## 9. Suggested commands

Prepare mode:

```bash
python tools/run_human_confirmed_suggestion_proposals_323g.py \
  --mode prepare \
  --raw-response-validation-dir D:\_datefac\output\raw_response_schema_validation_323f \
  --safe-subset-dir D:\_datefac\output\safe_adjudicator_subset_323d \
  --output-dir D:\_datefac\output\human_confirmed_suggestion_proposals_323g
```

If safe defaults are implemented:

```bash
python tools/run_human_confirmed_suggestion_proposals_323g.py
```

Validate-reviewed mode, if implemented:

```bash
python tools/run_human_confirmed_suggestion_proposals_323g.py \
  --mode validate-reviewed \
  --reviewed-confirmation-workbook D:\_datefac\input\human_confirmed_suggestion_proposals_323g_reviewed.xlsx \
  --raw-response-validation-dir D:\_datefac\output\raw_response_schema_validation_323f \
  --output-dir D:\_datefac\output\human_confirmed_suggestion_proposals_323g_reviewed
```

## 10. Compile / run checks

Run:

```bash
python -m py_compile datefac\semantic\human_confirmed_suggestion_proposals.py datefac\semantic\human_confirmed_suggestion_proposals_report.py tools\run_human_confirmed_suggestion_proposals_323g.py
```

Then run the 323G runner in prepare mode.

If validate-reviewed mode is implemented, test only with a safe fixture or explicit reviewed workbook. Do not invent real approval.

## 11. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 323G source files. Example:

```bash
git add datefac/semantic/human_confirmed_suggestion_proposals.py
git add datefac/semantic/human_confirmed_suggestion_proposals_report.py
git add tools/run_human_confirmed_suggestion_proposals_323g.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Add 323G human-confirmed suggestion proposals
```

Push to main only after successful checks.

## 12. Final report expected from Codex

After completion, report:

1. Modified files.
2. Commands run.
3. 323G output directory.
4. Mode used.
5. Accepted suggestion counts.
6. Confirmation record counts.
7. Decision distribution.
8. qa_fail_count.
9. decision.
10. Whether validate-reviewed mode was implemented.
11. git status result.
12. commit hash.
13. push result.
