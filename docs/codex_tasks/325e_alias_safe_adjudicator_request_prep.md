# DateFac 325E Task
## Alias Safe Adjudicator Request Prep

## Context

325D alias human spot-check reviewed validation has passed.

325D reviewed output dir:

```text
D:\_datefac\output\alias_human_spot_check_325d_reviewed
```

325D reviewed result:

```text
send_to_adjudicator_count = 6
holdout_count = 5
rejected_count = 0
needs_more_info_count = 0
pending_count = 0
invalid_decision_count = 0
carried_forward_325c_holdout_count = 1
qa_fail_count = 0
decision = ALIAS_HUMAN_SPOT_CHECK_325D_REVIEWED_READY_FOR_SAFE_ADJUDICATOR_REQUEST_PREP
official_assets_modified = false
```

325E is the next stage:

> Package only the 6 human-approved alias records into a safe adjudicator request package.

325E must not call the adjudicator/LLM. It only prepares schema-constrained request items for a later configured/manual adjudicator run.

## Goal

Implement 325E: alias safe adjudicator request prep.

The goal is to take the 6 `SEND_TO_ADJUDICATOR` records from 325D reviewed output and produce a compact, schema-controlled adjudicator request package with evidence and constraints.

The package must exclude:

```text
325D holdout_count = 5
325C carried-forward holdout_count = 1
all rejected/needs-more-info/pending/invalid records
```

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 325D reviewed output plus 325C/325B/325A evidence only.
- Process only the 6 records explicitly routed as `SEND_TO_ADJUDICATOR` by 325D reviewed validation.
- Do not include 325D holdouts, 325C carried-forward holdouts, rejected records, needs-more-info records, pending records, or invalid records.
- Do not produce official rule candidates in 325E.
- Do not produce controlled proposals.
- Do not produce sandbox replay packages.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 325E source/report/runner files.

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
D:\_datefac\output\alias_human_spot_check_325d_reviewed
```

Expected files may include:

```text
alias_human_spot_check_325d_reviewed_summary.json
alias_human_spot_check_325d_reviewed_qa.json
alias_human_spot_check_325d_final_routing_plan.json
alias_human_spot_check_325d_send_to_adjudicator.xlsx
alias_human_spot_check_325d_holdout_or_rejected.xlsx
```

Reference inputs:

```text
D:\_datefac\output\alias_review_batch_sanity_gate_325c
D:\_datefac\output\alias_review_batch_325b
D:\_datefac\output\alias_candidate_refinement_325a
```

Official assets may be read only for overlap/context checks:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/alias_safe_adjudicator_request_325e.py
datefac/semantic/alias_safe_adjudicator_request_325e_report.py
tools/run_alias_safe_adjudicator_request_325e.py
```

## Output directory

```text
D:\_datefac\output\alias_safe_adjudicator_request_325e
```

Suggested outputs:

```text
alias_safe_adjudicator_request_325e_summary.json
alias_safe_adjudicator_request_325e_qa.json
alias_safe_adjudicator_request_325e_request_package.json
alias_safe_adjudicator_request_325e_request_items.jsonl
alias_safe_adjudicator_request_325e_evidence_workbook.xlsx
alias_safe_adjudicator_request_325e_manual_prompt.md
alias_safe_adjudicator_request_325e_schema.json
alias_safe_adjudicator_request_325e_excluded_items.xlsx
alias_safe_adjudicator_request_325e_no_apply_proof.json
```

## Required behavior

1. Validate 325D reviewed readiness:

```text
decision = ALIAS_HUMAN_SPOT_CHECK_325D_REVIEWED_READY_FOR_SAFE_ADJUDICATOR_REQUEST_PREP
qa_fail_count = 0
send_to_adjudicator_count = 6
holdout_count = 5
rejected_count = 0
needs_more_info_count = 0
pending_count = 0
invalid_decision_count = 0
carried_forward_325c_holdout_count = 1
```

2. Load exactly 6 records routed as `SEND_TO_ADJUDICATOR`.
3. Exclude exactly 6 non-send records from request prep:
   - 5 325D holdouts;
   - 1 325C carried-forward holdout.
4. Generate exactly 6 request items.
5. Each request item must include:

```text
request_id
source_review_id
source_candidate_id
alias_label
proposed_target_metric
candidate_type = alias
human_decision = SEND_TO_ADJUDICATOR
evidence_summary
sample_rows
risk_flags
ambiguity_notes
human_reviewer_notes
provenance
allowed_response_labels
response_schema_version
```

6. Allowed adjudicator response labels:

```text
ACCEPT_ALIAS
REJECT_ALIAS
NEEDS_MORE_INFO
```

7. Require adjudicator response schema to include:

```text
request_id
response_label
target_metric_if_accept
normalized_alias_label
confidence
rationale
safety_flags
needs_human_confirmation
```

8. Do not allow the adjudicator to apply rules or mark trusted rows.
9. Make clear that accepted suggestions from the adjudicator still require later schema validation, deterministic gate, human confirmation, sandbox replay, controlled proposal, dry run, human approval, official patch application, and post-patch regression.
10. Confirm official assets are not modified.
11. Generate QA and no-apply proof.

## Expected summary metrics

```text
request_count = 6
alias_request_count = 6
excluded_holdout_count = 6
excluded_rejected_count = 0
excluded_needs_more_info_count = 0
excluded_pending_count = 0
llm_or_adjudicator_called = false
official_assets_modified = false
qa_fail_count = 0
```

Expected decision:

```text
ALIAS_SAFE_ADJUDICATOR_REQUEST_325E_READY_FOR_MANUAL_OR_CONFIGURED_ADJUDICATOR_RUN
```

If no request items are available but QA passes:

```text
ALIAS_SAFE_ADJUDICATOR_REQUEST_325E_NO_REQUEST_ITEMS
```

If blocking QA fails:

```text
ALIAS_SAFE_ADJUDICATOR_REQUEST_325E_NOT_READY
```

## Suggested command

```bash
python tools/run_alias_safe_adjudicator_request_325e.py \
  --reviewed-dir D:\_datefac\output\alias_human_spot_check_325d_reviewed \
  --sanity-gate-dir D:\_datefac\output\alias_review_batch_sanity_gate_325c \
  --alias-review-batch-dir D:\_datefac\output\alias_review_batch_325b \
  --output-dir D:\_datefac\output\alias_safe_adjudicator_request_325e
```

If safe defaults are implemented:

```bash
python tools/run_alias_safe_adjudicator_request_325e.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\alias_safe_adjudicator_request_325e.py datefac\semantic\alias_safe_adjudicator_request_325e_report.py tools\run_alias_safe_adjudicator_request_325e.py
```

Then run the 325E runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/alias_safe_adjudicator_request_325e.py
git add datefac/semantic/alias_safe_adjudicator_request_325e_report.py
git add tools/run_alias_safe_adjudicator_request_325e.py
```

Suggested commit message:

```text
Add 325E alias safe adjudicator request prep
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Request count.
5. Alias request count.
6. Excluded holdout/rejected/needs-more-info/pending counts.
7. Top request examples.
8. Allowed response labels and schema summary.
9. Whether LLM/adjudicator was called.
10. Official asset modification confirmation.
11. QA fail count.
12. Decision.
13. Git status result.
14. Commit hash.
15. Push result.
