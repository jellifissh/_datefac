# DateFac 324C Task
## Scope Noise Safe Adjudicator Request Prep

## Context

324B scope noise human review prepare workflow is complete and pushed to remote main.

324B commit:

```text
7da6d59f7895ad2dff04a7eb0ff3c01db91c4e47
```

324B reviewed validation has been run locally with this result:

```text
review_record_count = 1
confirmed_scope_noise_count = 0
rejected_scope_noise_count = 0
needs_more_info_count = 0
escalate_to_adjudicator_count = 1
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = SCOPE_NOISE_HUMAN_REVIEW_324B_REVIEWED_READY_FOR_SAFE_ADJUDICATOR_REQUEST_PREP
```

324B reviewed output dir:

```text
D:\_datefac\output\scope_noise_human_review_324b_reviewed
```

Important interpretation:

```text
The single 324A refined long-narrative scope candidate was not human-confirmed as scope noise. It was escalated for semantic adjudicator review. Therefore the next step is not sandbox replay. The next step is safe adjudicator request preparation.
```

The candidate carries high-risk flags:

```text
INVALID_YEAR | NO_YEAR_COLUMNS | UNKNOWN_METRIC_CODE | VALUE_PARSE_FAILED | LONG_LABEL_REVIEW_REQUIRED
```

## Goal

Implement 324C: prepare a safe semantic adjudicator request package for the single escalated long-narrative scope candidate.

324C must create a request package only. It must not call an LLM/adjudicator and must not apply rules.

The request should ask the adjudicator to decide whether the long narrative label is:

1. safe out-of-scope/non-core noise;
2. not safe to exclude;
3. needs more information.

## Hard constraints

- Do not modify production pipeline.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted directly.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 324B reviewed output, 324A refinement output, and cached evidence only.
- Process only the single escalated 324B review record.
- Do not treat the long narrative label as automatically safe scope noise.
- Do not produce sandbox replay candidates in 324C.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 324C source/report/runner files.

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
D:\_datefac\output\scope_noise_human_review_324b_reviewed
```

Expected files may include:

```text
scope_noise_human_review_324b_reviewed_summary.json
scope_noise_human_review_324b_reviewed_qa.json
scope_noise_human_review_324b_reviewed_decision_plan.json
scope_noise_human_review_324b_reviewed_workbook.xlsx
```

Reference input:

```text
D:\_datefac\output\scope_noise_human_review_324b
D:\_datefac\output\scope_noise_refinement_324a
D:\_datefac\output\remaining_burden_planning_323p
D:\_datefac\output\post_patch_regression_validation_323n
```

Official assets may be read only for reference checks:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/scope_noise_safe_adjudicator_request_324c.py
datefac/semantic/scope_noise_safe_adjudicator_request_324c_report.py
tools/run_scope_noise_safe_adjudicator_request_324c.py
```

## Output directory

```text
D:\_datefac\output\scope_noise_safe_adjudicator_request_324c
```

Suggested outputs:

```text
scope_noise_safe_adjudicator_request_324c_summary.json
scope_noise_safe_adjudicator_request_324c_qa.json
scope_noise_safe_adjudicator_request_324c_request_package.json
scope_noise_safe_adjudicator_request_324c_request.jsonl
scope_noise_safe_adjudicator_request_324c_manual_prompt.md
scope_noise_safe_adjudicator_request_324c_evidence.xlsx
scope_noise_safe_adjudicator_request_324c_notes.md
```

## Required request schema

Create exactly one request item with fields such as:

```text
request_id
source_scope_review_id
source_refined_scope_candidate_id
candidate_type
candidate_label
risk_flags
affected_review_required_count
source_group_ids
sample_evidence
reviewer_decision
reviewer_note
adjudication_question
allowed_response_labels
response_schema
safety_constraints
provenance
```

Allowed response labels:

```text
ACCEPT_OUT_OF_SCOPE
REJECT_OUT_OF_SCOPE
NEEDS_MORE_INFO
```

Required response schema should require:

```text
request_id
response_label
confidence
rationale
normalized_target_metric_if_any
safety_flags
needs_human_confirmation
```

For `ACCEPT_OUT_OF_SCOPE`, require:

```text
normalized_target_metric_if_any = null or empty
needs_human_confirmation = true
confidence = high or medium
safety_flags must not indicate conflict, core metric risk, weak evidence, or unit ambiguity
```

## Required behavior

1. Validate 324B reviewed readiness:

```text
decision = SCOPE_NOISE_HUMAN_REVIEW_324B_REVIEWED_READY_FOR_SAFE_ADJUDICATOR_REQUEST_PREP
qa_fail_count = 0
review_record_count = 1
escalate_to_adjudicator_count = 1
confirmed_scope_noise_count = 0
pending_count = 0
invalid_decision_count = 0
```

2. Load exactly one escalated review record.
3. Preserve risk flags and reviewer evidence.
4. Build one safe adjudicator request.
5. Include explicit caution that this is a long narrative label and must not be auto-accepted.
6. Include samples and provenance, but do not call any LLM.
7. Generate request JSON / JSONL / manual prompt / QA.
8. Confirm official assets were not modified.

## Expected result

```text
request_count = 1
scope_noise_request_count = 1
llm_called = false
qa_fail_count = 0
decision = SCOPE_NOISE_SAFE_ADJUDICATOR_REQUEST_324C_READY_FOR_MANUAL_OR_CONFIGURED_ADJUDICATOR_RUN
```

## Decision

If the request package is valid:

```text
SCOPE_NOISE_SAFE_ADJUDICATOR_REQUEST_324C_READY_FOR_MANUAL_OR_CONFIGURED_ADJUDICATOR_RUN
```

If invalid:

```text
SCOPE_NOISE_SAFE_ADJUDICATOR_REQUEST_324C_NOT_READY
```

## Suggested command

```bash
python tools/run_scope_noise_safe_adjudicator_request_324c.py \
  --reviewed-human-review-dir D:\_datefac\output\scope_noise_human_review_324b_reviewed \
  --scope-refinement-dir D:\_datefac\output\scope_noise_refinement_324a \
  --output-dir D:\_datefac\output\scope_noise_safe_adjudicator_request_324c
```

If safe defaults are implemented:

```bash
python tools/run_scope_noise_safe_adjudicator_request_324c.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\scope_noise_safe_adjudicator_request_324c.py datefac\semantic\scope_noise_safe_adjudicator_request_324c_report.py tools\run_scope_noise_safe_adjudicator_request_324c.py
```

Then run the 324C runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/scope_noise_safe_adjudicator_request_324c.py
git add datefac/semantic/scope_noise_safe_adjudicator_request_324c_report.py
git add tools/run_scope_noise_safe_adjudicator_request_324c.py
```

Suggested commit message:

```text
Add 324C scope noise safe adjudicator request prep
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Request count.
5. Scope noise request count.
6. Risk flags carried forward.
7. Allowed response labels.
8. Whether LLM/adjudicator was called.
9. qa_fail_count.
10. decision.
11. git status result.
12. commit hash.
13. push result.
