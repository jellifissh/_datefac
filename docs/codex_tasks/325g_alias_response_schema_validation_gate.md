# DateFac 325G Task
## Alias Raw Response Schema Validation and Deterministic Gate

## Context

325F alias adjudicator response collection has completed successfully.

325F output dir:

```text
D:\_datefac\output\alias_adjudicator_response_collection_325f
```

325F collect-manual result:

```text
request_count = 6
raw_response_count = 6
response_received_count = 6
request_id_alignment = PASS
aligned = 6
qa_fail_count = 0
decision = ALIAS_ADJUDICATOR_RESPONSE_COLLECTION_325F_RAW_RESPONSE_READY_FOR_325G_SCHEMA_VALIDATION
official_assets_modified = false
llm_or_adjudicator_called = false
```

325G is the next gate:

> Validate the 6 collected alias raw responses against the 325E response schema, then apply deterministic safety gates before any accepted suggestion can proceed to human confirmation.

Alias responses are higher-risk than scope-noise responses because accepted aliases can eventually map text labels into core financial metrics. 325G must be strict and must not trust a raw response simply because it says `ACCEPT_ALIAS`.

## Goal

Implement 325G: alias raw response schema validation and deterministic gate.

The goal is to produce validated alias suggestions from the 6 raw responses collected in 325F.

325G should classify each response as one of:

```text
ACCEPTED_FOR_HUMAN_CONFIRMATION
REJECTED_BY_SCHEMA
REJECTED_BY_DETERMINISTIC_GATE
NEEDS_MORE_INFO
REJECTED_ALIAS_SUGGESTION
```

Only responses that pass schema validation and deterministic safety checks may proceed to 325H human confirmation.

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 325F raw responses, 325E request package, and cached 325D/325C/325B/325A evidence only.
- Process exactly the 6 collected raw responses.
- Do not produce official rule candidates in 325G.
- Do not produce controlled proposals.
- Do not produce sandbox replay packages.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 325G source/report/runner files.

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
D:\_datefac\output\alias_adjudicator_response_collection_325f
```

Expected files may include:

```text
alias_adjudicator_response_collection_325f_summary.json
alias_adjudicator_response_collection_325f_qa.json
alias_adjudicator_response_collection_325f_raw_responses.jsonl
alias_adjudicator_response_collection_325f_collected_responses.xlsx
```

Reference inputs:

```text
D:\_datefac\output\alias_safe_adjudicator_request_325e
D:\_datefac\output\alias_human_spot_check_325d_reviewed
D:\_datefac\output\alias_review_batch_sanity_gate_325c
D:\_datefac\output\alias_review_batch_325b
D:\_datefac\output\alias_candidate_refinement_325a
```

Official assets may be read only for overlap/conflict checks:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/alias_response_schema_validation_325g.py
datefac/semantic/alias_response_schema_validation_325g_report.py
tools/run_alias_response_schema_validation_325g.py
```

## Output directory

```text
D:\_datefac\output\alias_response_schema_validation_325g
```

Suggested outputs:

```text
alias_response_schema_validation_325g_summary.json
alias_response_schema_validation_325g_qa.json
alias_response_schema_validation_325g_validated_suggestions.json
alias_response_schema_validation_325g_validated_suggestions.xlsx
alias_response_schema_validation_325g_accepted_for_human_confirmation.xlsx
alias_response_schema_validation_325g_rejected_or_needs_more_info.xlsx
alias_response_schema_validation_325g_deterministic_gate_report.xlsx
alias_response_schema_validation_325g_no_apply_proof.json
alias_response_schema_validation_325g_report.md
```

## Required response schema

Each raw response must contain:

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

Allowed response labels:

```text
ACCEPT_ALIAS
REJECT_ALIAS
NEEDS_MORE_INFO
```

Allowed confidence values:

```text
high
medium
low
```

`needs_human_confirmation` must be boolean-like and must be true for any `ACCEPT_ALIAS` response that proceeds.

## Required behavior

1. Validate 325F readiness:

```text
decision = ALIAS_ADJUDICATOR_RESPONSE_COLLECTION_325F_RAW_RESPONSE_READY_FOR_325G_SCHEMA_VALIDATION
qa_fail_count = 0
request_count = 6
raw_response_count = 6
response_received_count = 6
request_id_alignment = PASS
```

2. Load exactly 6 raw responses.
3. Match every response to a 325E request item.
4. Validate schema fields and allowed values.
5. For `REJECT_ALIAS`, classify as `REJECTED_ALIAS_SUGGESTION` if schema is otherwise valid.
6. For `NEEDS_MORE_INFO`, classify as `NEEDS_MORE_INFO` if schema is otherwise valid.
7. For `ACCEPT_ALIAS`, require:

```text
target_metric_if_accept is non-empty
normalized_alias_label is non-empty
confidence is high or medium
needs_human_confirmation = true
rationale is non-empty
```

8. Apply deterministic safety gates for accepted alias responses:

- Reject if target metric is missing or not in known/allowed core metric vocabulary.
- Reject if normalized alias label is empty, mojibake, long narrative text, or generic ambiguous text.
- Reject if alias already exists officially with a conflicting target.
- Reject if the alias label is officially excluded as scope noise.
- Reject if safety flags contain blocking flags.
- Reject adjusted aliases if they are mapped to non-adjusted metrics, e.g.:

```text
经调整 EPS -> EPS
经调整归母净利润 -> 归母净利润
```

- Reject diluted/latest-diluted EPS aliases if mapped to basic EPS.
- Reject ROE aliases if mapped to generic profitability or margin metrics.
- Reject net margin / attributable net margin aliases if mapped to net profit.
- Reject EBIT aliases if mapped to EBITDA, operating profit, or profit before tax.

9. Accept for human confirmation only if schema validation and deterministic gate both pass.
10. Do not apply any alias rule.
11. Do not create official candidates.
12. Confirm official assets are not modified.
13. Generate QA and no-apply proof.

## Known alias safety guidance

The following labels were part of the 325E request examples:

```text
EBIT
归母净利率
净资产收益率（ROE)
每股收益(最新摊薄)
经调整 EPS
经调整归母净利润
```

Safe target mapping depends on project vocabulary, but these semantic constraints must hold:

```text
EBIT -> EBIT only
归母净利率 -> attributable_net_margin / parent_net_margin style metric only, not net profit
净资产收益率（ROE) -> ROE only
每股收益(最新摊薄) -> diluted_EPS / EPS_diluted only, not basic EPS
经调整 EPS -> adjusted_EPS only, not ordinary EPS
经调整归母净利润 -> adjusted_attributable_net_profit / adjusted_parent_net_profit only, not ordinary attributable net profit
```

If project vocabulary does not contain the precise adjusted or attributable metric, route to `NEEDS_MORE_INFO` or reject by deterministic gate rather than silently mapping to a nearby ordinary metric.

## Expected summary metrics

Compute actual counts, but expected fields are:

```text
request_count
response_count
schema_valid_count
schema_invalid_count
accepted_for_human_confirmation_count
rejected_by_schema_count
rejected_by_deterministic_gate_count
rejected_alias_suggestion_count
needs_more_info_count
deterministic_gate_failure_count
official_overlap_count
target_conflict_count
adjusted_metric_mismatch_count
diluted_eps_mismatch_count
qa_fail_count
```

Expected decision if at least one suggestion is accepted for human confirmation:

```text
ALIAS_RESPONSE_SCHEMA_VALIDATION_325G_READY_FOR_HUMAN_CONFIRMATION
```

Expected decision if QA passes but no suggestions are accepted:

```text
ALIAS_RESPONSE_SCHEMA_VALIDATION_325G_NO_ACCEPTED_SUGGESTIONS
```

If blocking QA fails:

```text
ALIAS_RESPONSE_SCHEMA_VALIDATION_325G_NOT_READY
```

## Suggested command

```bash
python tools/run_alias_response_schema_validation_325g.py \
  --response-collection-dir D:\_datefac\output\alias_adjudicator_response_collection_325f \
  --request-dir D:\_datefac\output\alias_safe_adjudicator_request_325e \
  --output-dir D:\_datefac\output\alias_response_schema_validation_325g
```

If safe defaults are implemented:

```bash
python tools/run_alias_response_schema_validation_325g.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\alias_response_schema_validation_325g.py datefac\semantic\alias_response_schema_validation_325g_report.py tools\run_alias_response_schema_validation_325g.py
```

Then run the 325G runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/alias_response_schema_validation_325g.py
git add datefac/semantic/alias_response_schema_validation_325g_report.py
git add tools/run_alias_response_schema_validation_325g.py
```

Suggested commit message:

```text
Add 325G alias response validation gate
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Request / response counts.
5. Schema valid / invalid counts.
6. Accepted / rejected / needs-more-info counts.
7. Deterministic gate failure counts and reasons.
8. Official overlap / target conflict counts.
9. Adjusted/diluted metric mismatch counts.
10. Whether official assets were modified.
11. QA fail count.
12. Decision.
13. Git status result.
14. Commit hash.
15. Push result.
