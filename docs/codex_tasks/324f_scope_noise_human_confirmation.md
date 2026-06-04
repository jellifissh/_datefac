# DateFac 324F Task
## Scope Noise Human Confirmation after 324E Validation Gate

## Context

324E scope noise response schema validation and deterministic gate is complete and pushed to remote main.

324E HEAD:

```text
bfee1e0a3c8082f896d53b47f1c930e9af0e633a
```

324E output dir:

```text
D:\_datefac\output\scope_noise_response_schema_validation_324e
```

324E result:

```text
request_count = 1
response_count = 1
schema_valid_count = 1
schema_invalid_count = 0
deterministic_gate_result = PASS
accepted_for_human_confirmation_count = 1
rejected_by_schema_count = 0
rejected_by_deterministic_gate_count = 0
needs_more_info_count = 0
rejected_out_of_scope_suggestion_count = 0
official_assets_modified = false
qa_fail_count = 0
decision = SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_READY_FOR_324F_HUMAN_CONFIRMATION
```

324F is the next step:

> Package the single 324E accepted out-of-scope suggestion for human confirmation, then validate the reviewed confirmation workbook.

324F must not apply rules and must not create sandbox replay output until the reviewed confirmation has been validated.

## Goal

Implement 324F: human confirmation workflow for the single scope-noise accepted suggestion from 324E.

324F should support:

```text
prepare
validate-reviewed
```

Prepare mode creates a human confirmation workbook with one pending confirmation record.

Validate-reviewed mode reads the filled workbook and creates a reviewed confirmation plan only if the user confirms the suggestion.

## Hard constraints

- Do not modify production pipeline.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted directly.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 324E output and cached evidence only.
- Process only the single accepted-for-human-confirmation suggestion from 324E.
- Do not produce sandbox replay output in prepare mode.
- Do not produce official rule candidates.
- Do not modify official assets.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 324F source/report/runner files.

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
D:\_datefac\output\scope_noise_response_schema_validation_324e
```

Expected files:

```text
scope_noise_response_schema_validation_324e_summary.json
scope_noise_response_schema_validation_324e_qa.json
scope_noise_response_schema_validation_324e_accepted_for_human_confirmation.json
scope_noise_response_schema_validation_324e_validated_responses.jsonl
scope_noise_response_schema_validation_324e_review_package.xlsx
```

Reference inputs:

```text
D:\_datefac\output\scope_noise_safe_adjudicator_request_324c
D:\_datefac\output\scope_noise_human_review_324b_reviewed
D:\_datefac\output\scope_noise_refinement_324a
```

Official assets may be read only for reference checks:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/scope_noise_human_confirmation_324f.py
datefac/semantic/scope_noise_human_confirmation_324f_report.py
tools/run_scope_noise_human_confirmation_324f.py
```

## Output directories

Prepare mode:

```text
D:\_datefac\output\scope_noise_human_confirmation_324f
```

Reviewed mode:

```text
D:\_datefac\output\scope_noise_human_confirmation_324f_reviewed
```

Suggested prepare outputs:

```text
scope_noise_human_confirmation_324f_summary.json
scope_noise_human_confirmation_324f_qa.json
scope_noise_human_confirmation_324f_confirmation_workbook.xlsx
scope_noise_human_confirmation_324f_confirmation_package.json
scope_noise_human_confirmation_324f_review_instructions.md
scope_noise_human_confirmation_324f_no_apply_proof.json
```

Suggested reviewed outputs:

```text
scope_noise_human_confirmation_324f_reviewed_summary.json
scope_noise_human_confirmation_324f_reviewed_qa.json
scope_noise_human_confirmation_324f_human_confirmed_plan.json
scope_noise_human_confirmation_324f_reviewed_workbook.xlsx
scope_noise_human_confirmation_324f_rejected_or_needs_more_info.xlsx
scope_noise_human_confirmation_324f_no_apply_proof.json
```

## Prepare mode required behavior

1. Validate 324E readiness:

```text
decision = SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_READY_FOR_324F_HUMAN_CONFIRMATION
qa_fail_count = 0
request_count = 1
response_count = 1
schema_valid_count = 1
schema_invalid_count = 0
accepted_for_human_confirmation_count = 1
rejected_by_schema_count = 0
rejected_by_deterministic_gate_count = 0
needs_more_info_count = 0
rejected_out_of_scope_suggestion_count = 0
deterministic_gate_result = PASS
```

2. Load exactly one accepted suggestion.
3. Preserve request id, response label, confidence, rationale, safety flags, risk flags, sample evidence, and provenance.
4. Generate one confirmation record.
5. Default decision:

```text
PENDING_HUMAN_CONFIRMATION
```

6. Allowed human confirmation decisions:

```text
CONFIRM
REJECT
NEEDS_MORE_INFO
```

7. Include an explicit warning that this is a long narrative label and must not be auto-promoted.
8. Confirm no official assets were modified.

## Validate-reviewed mode required behavior

1. Read reviewed confirmation workbook.
2. Validate exactly one confirmation record.
3. Require decision in the allowed set.
4. Require no pending decision.
5. If decision is `CONFIRM`, produce a human-confirmed plan for 324G sandbox replay.
6. If `REJECT` or `NEEDS_MORE_INFO`, do not produce a sandbox replay plan.
7. Preserve all reviewer notes and evidence.
8. Confirm official assets were not modified.

## Expected prepare result

```text
confirmation_record_count = 1
pending_count = 1
confirmed_count = 0
rejected_count = 0
needs_more_info_count = 0
qa_fail_count = 0
decision = SCOPE_NOISE_HUMAN_CONFIRMATION_324F_READY_FOR_HUMAN_REVIEW
```

## Expected reviewed result if confirmed

```text
confirmation_record_count = 1
confirmed_count = 1
rejected_count = 0
needs_more_info_count = 0
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = SCOPE_NOISE_HUMAN_CONFIRMATION_324F_REVIEWED_READY_FOR_324G_SANDBOX_REPLAY
```

## Expected reviewed result if rejected

```text
confirmation_record_count = 1
confirmed_count = 0
rejected_count = 1
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = SCOPE_NOISE_HUMAN_CONFIRMATION_324F_REVIEWED_REJECTED_NO_SANDBOX_REPLAY
```

## Suggested commands

Prepare mode:

```bash
python tools/run_scope_noise_human_confirmation_324f.py \
  --mode prepare \
  --validated-response-dir D:\_datefac\output\scope_noise_response_schema_validation_324e \
  --output-dir D:\_datefac\output\scope_noise_human_confirmation_324f
```

Validate-reviewed mode:

```bash
python tools/run_scope_noise_human_confirmation_324f.py \
  --mode validate-reviewed \
  --validated-response-dir D:\_datefac\output\scope_noise_response_schema_validation_324e \
  --reviewed-confirmation-workbook D:\_datefac\output\scope_noise_human_confirmation_324f\scope_noise_human_confirmation_324f_confirmation_workbook.xlsx \
  --output-dir D:\_datefac\output\scope_noise_human_confirmation_324f_reviewed
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\scope_noise_human_confirmation_324f.py datefac\semantic\scope_noise_human_confirmation_324f_report.py tools\run_scope_noise_human_confirmation_324f.py
```

Then run prepare mode at minimum.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/scope_noise_human_confirmation_324f.py
git add datefac/semantic/scope_noise_human_confirmation_324f_report.py
git add tools/run_scope_noise_human_confirmation_324f.py
```

Suggested commit message:

```text
Add 324F scope noise human confirmation workflow
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Mode used.
5. Confirmation record count.
6. Pending / confirmed / rejected / needs-more-info counts.
7. qa_fail_count.
8. decision.
9. Whether validate-reviewed mode was implemented.
10. Whether official assets were modified.
11. git status result.
12. commit hash.
13. push result.
