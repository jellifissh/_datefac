# DateFac 325H Task
## Alias Human Confirmation for 325G Accepted Suggestions

## Context

325G alias response schema validation and deterministic gate has been rerun with corrected 325F manual responses and passed.

325G output dir:

```text
D:\_datefac\output\alias_response_schema_validation_325g
```

325G rerun result:

```text
request_count = 6
response_count = 6
schema_valid_count = 6
schema_invalid_count = 0
accepted_for_human_confirmation_count = 6
rejected_by_schema_count = 0
rejected_by_deterministic_gate_count = 0
rejected_alias_suggestion_count = 0
needs_more_info_count = 0
deterministic_gate_failure_reasons = {}
official_overlap_count = 0
target_conflict_count = 0
adjusted_metric_mismatch_count = 0
diluted_eps_mismatch_count = 0
official_assets_modified = false
qa_fail_count = 0
decision = ALIAS_RESPONSE_SCHEMA_VALIDATION_325G_READY_FOR_HUMAN_CONFIRMATION
```

Accepted alias suggestions likely include:

```text
EBIT -> EBIT
归母净利率 -> attributable_net_margin
净资产收益率（ROE) -> ROE
每股收益(最新摊薄) -> diluted_EPS
经调整 EPS -> adjusted_EPS
经调整归母净利润 -> adjusted_attributable_net_profit
```

325H is the next stage:

> Create a human confirmation workbook/package for the 6 validated alias suggestions, then support reviewed validation.

325H must not apply rules and must not create official candidates. It only collects explicit human confirmation before sandbox replay.

## Goal

Implement 325H: alias human confirmation workflow.

Prepare mode should generate a confirmation workbook with exactly the 6 suggestions accepted by 325G.

Validate-reviewed mode should read the filled confirmation workbook and produce a human-confirmed alias suggestion plan only for confirmed suggestions.

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 325G validated suggestions and cached 325F/325E/325D/325C/325B/325A evidence only.
- Process only the 6 `ACCEPTED_FOR_HUMAN_CONFIRMATION` suggestions from 325G.
- Do not produce official rule candidates in 325H.
- Do not produce controlled proposals.
- Do not run sandbox replay in 325H.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 325H source/report/runner files.

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
D:\_datefac\output\alias_response_schema_validation_325g
```

Expected files may include:

```text
alias_response_schema_validation_325g_summary.json
alias_response_schema_validation_325g_qa.json
alias_response_schema_validation_325g_validated_suggestions.json
alias_response_schema_validation_325g_validated_suggestions.xlsx
alias_response_schema_validation_325g_accepted_for_human_confirmation.xlsx
```

Reference inputs:

```text
D:\_datefac\output\alias_adjudicator_response_collection_325f
D:\_datefac\output\alias_safe_adjudicator_request_325e
D:\_datefac\output\alias_human_spot_check_325d_reviewed
D:\_datefac\output\alias_review_batch_sanity_gate_325c
D:\_datefac\output\alias_review_batch_325b
D:\_datefac\output\alias_candidate_refinement_325a
```

Official assets may be read only for context/overlap checks:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/alias_human_confirmation_325h.py
datefac/semantic/alias_human_confirmation_325h_report.py
tools/run_alias_human_confirmation_325h.py
```

## Output directories

Prepare mode:

```text
D:\_datefac\output\alias_human_confirmation_325h
```

Reviewed mode:

```text
D:\_datefac\output\alias_human_confirmation_325h_reviewed
```

Suggested prepare outputs:

```text
alias_human_confirmation_325h_summary.json
alias_human_confirmation_325h_qa.json
alias_human_confirmation_325h_workbook.xlsx
alias_human_confirmation_325h_package.json
alias_human_confirmation_325h_review_notes.md
alias_human_confirmation_325h_no_apply_proof.json
```

Suggested reviewed outputs:

```text
alias_human_confirmation_325h_reviewed_summary.json
alias_human_confirmation_325h_reviewed_qa.json
alias_human_confirmation_325h_human_confirmed_plan.json
alias_human_confirmation_325h_reviewed_workbook.xlsx
alias_human_confirmation_325h_rejected_or_needs_more_info.xlsx
alias_human_confirmation_325h_no_apply_proof.json
```

## Prepare mode required behavior

1. Validate 325G readiness:

```text
decision = ALIAS_RESPONSE_SCHEMA_VALIDATION_325G_READY_FOR_HUMAN_CONFIRMATION
qa_fail_count = 0
request_count = 6
response_count = 6
schema_valid_count = 6
schema_invalid_count = 0
accepted_for_human_confirmation_count = 6
rejected_by_schema_count = 0
rejected_by_deterministic_gate_count = 0
rejected_alias_suggestion_count = 0
needs_more_info_count = 0
official_overlap_count = 0
target_conflict_count = 0
adjusted_metric_mismatch_count = 0
diluted_eps_mismatch_count = 0
official_assets_modified = false
```

2. Load exactly 6 `ACCEPTED_FOR_HUMAN_CONFIRMATION` suggestions.
3. Generate exactly 6 human confirmation records.
4. Default decision:

```text
PENDING_HUMAN_CONFIRMATION
```

5. Allowed human decisions:

```text
CONFIRM
REJECT
NEEDS_MORE_INFO
```

6. Include request id, source candidate id, alias label, normalized alias label, target metric, confidence, rationale, deterministic gate result, risk flags, evidence, provenance, and warning notes.
7. Explicitly warn that confirmation still does not apply official rules; confirmed suggestions must go through sandbox replay next.
8. Confirm official assets are not modified.
9. Generate QA and no-apply proof.

## Validate-reviewed mode required behavior

1. Read the reviewed confirmation workbook.
2. Validate exactly 6 confirmation records.
3. Require every reviewed record to have one allowed decision.
4. Require no pending decisions.
5. If decision is `CONFIRM`, include it in the human-confirmed alias plan for 325I sandbox replay.
6. If `REJECT` or `NEEDS_MORE_INFO`, exclude from sandbox replay and preserve in rejected/needs-more-info output.
7. Do not call LLM/adjudicator.
8. Do not produce official candidates.
9. Do not run sandbox replay.
10. Confirm official assets are not modified.

## Expected prepare result

```text
confirmation_record_count = 6
pending_count = 6
confirmed_count = 0
rejected_count = 0
needs_more_info_count = 0
qa_fail_count = 0
decision = ALIAS_HUMAN_CONFIRMATION_325H_READY_FOR_HUMAN_REVIEW
```

## Expected reviewed result if all six are confirmed

```text
confirmation_record_count = 6
confirmed_count = 6
rejected_count = 0
needs_more_info_count = 0
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = ALIAS_HUMAN_CONFIRMATION_325H_REVIEWED_READY_FOR_325I_SANDBOX_REPLAY
```

If some are confirmed and others are rejected/needs-more-info:

```text
confirmation_record_count = 6
confirmed_count = <computed>
rejected_count = <computed>
needs_more_info_count = <computed>
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = ALIAS_HUMAN_CONFIRMATION_325H_REVIEWED_READY_FOR_325I_SANDBOX_REPLAY
```

if `confirmed_count > 0`.

If no records are confirmed:

```text
ALIAS_HUMAN_CONFIRMATION_325H_REVIEWED_NO_CONFIRMED_ALIAS_SUGGESTIONS
```

If pending or invalid decisions remain:

```text
ALIAS_HUMAN_CONFIRMATION_325H_REVIEWED_NOT_READY
```

## Suggested commands

Prepare mode:

```bash
python tools/run_alias_human_confirmation_325h.py \
  --mode prepare \
  --schema-validation-dir D:\_datefac\output\alias_response_schema_validation_325g \
  --output-dir D:\_datefac\output\alias_human_confirmation_325h
```

Validate-reviewed mode:

```bash
python tools/run_alias_human_confirmation_325h.py \
  --mode validate-reviewed \
  --schema-validation-dir D:\_datefac\output\alias_response_schema_validation_325g \
  --reviewed-workbook D:\_datefac\output\alias_human_confirmation_325h\alias_human_confirmation_325h_workbook.xlsx \
  --output-dir D:\_datefac\output\alias_human_confirmation_325h_reviewed
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\alias_human_confirmation_325h.py datefac\semantic\alias_human_confirmation_325h_report.py tools\run_alias_human_confirmation_325h.py
```

Then run prepare mode at minimum.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/alias_human_confirmation_325h.py
git add datefac/semantic/alias_human_confirmation_325h_report.py
git add tools/run_alias_human_confirmation_325h.py
```

Suggested commit message:

```text
Add 325H alias human confirmation workflow
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Mode used.
5. Confirmation record count.
6. Pending / confirmed / rejected / needs-more-info counts.
7. Top confirmation examples.
8. Whether validate-reviewed mode was implemented.
9. Official asset modification confirmation.
10. QA fail count.
11. Decision.
12. Git status result.
13. Commit hash.
14. Push result.
