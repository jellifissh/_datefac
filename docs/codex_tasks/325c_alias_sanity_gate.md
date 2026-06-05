# DateFac 325C Task
## Alias Review Batch Sanity Gate

## Context

325B alias review batch preparation is complete and pushed to remote main.

325B commit:

```text
c45bf2b5cb34e992e0d29696254207787b53e77a
```

325B output dir:

```text
D:\_datefac\output\alias_review_batch_325b
```

325B result:

```text
loaded_safe_alias_candidate_count = 12
review_record_count = 12
pending_count = 12
accepted_count = 0
rejected_count = 0
needs_more_info_count = 0
holdout_count = 0
top_review_examples = 市盈率 (PE), P/E（现价&最新股本摊薄）, P/B（现价）, EBIT, 市净率（PB）
official_assets_modified = false
llm_or_adjudicator_called = false
qa_fail_count = 0
decision = ALIAS_REVIEW_BATCH_325B_READY_FOR_HUMAN_OR_ADJUDICATOR_REVIEW
```

325C is the next safety gate:

> Deterministically route the 12 alias review records into safe adjudicator/human review subsets and holdout buckets before any model/adjudicator call.

Alias rules are riskier than scope-noise rules because they can map noisy or ambiguous labels into trusted core metrics. Therefore 325C must be stricter than 325B and must not auto-accept any alias.

## Goal

Implement 325C: alias review batch sanity gate.

The goal is to inspect the 12 pending alias review records from 325B and produce a routing manifest with these buckets:

```text
SEND_TO_ADJUDICATOR
HUMAN_SPOT_CHECK_FIRST
HOLDOUT_ALREADY_OFFICIAL
HOLDOUT_TARGET_AMBIGUOUS
HOLDOUT_GENERIC_AMBIGUOUS_LABEL
HOLDOUT_CATEGORY_MISMATCH
HOLDOUT_UNIT_OR_PRICE_AMBIGUITY
HOLDOUT_SCOPE_NOISE_OR_DISCLOSURE_TEXT
HOLDOUT_DUPLICATE_OR_CONFLICT
HOLDOUT_WEAK_EVIDENCE
HOLDOUT_INVALID_TEXT
```

325C must not call an LLM/adjudicator. It only prepares routing.

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 325B review package and 325A evidence only.
- Process only the 12 325B review records.
- Do not produce official rule candidates in 325C.
- Do not produce controlled proposals.
- Do not produce sandbox replay packages.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 325C source/report/runner files.

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
D:\_datefac\output\alias_review_batch_325b
```

Expected files may include:

```text
alias_review_batch_325b_summary.json
alias_review_batch_325b_qa.json
alias_review_batch_325b_review_package.json
alias_review_batch_325b_workbook.xlsx
alias_review_batch_325b_review_records.json
```

Reference input:

```text
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
datefac/semantic/alias_review_batch_sanity_gate_325c.py
datefac/semantic/alias_review_batch_sanity_gate_325c_report.py
tools/run_alias_review_batch_sanity_gate_325c.py
```

## Output directory

```text
D:\_datefac\output\alias_review_batch_sanity_gate_325c
```

Suggested outputs:

```text
alias_review_batch_sanity_gate_325c_summary.json
alias_review_batch_sanity_gate_325c_qa.json
alias_review_batch_sanity_gate_325c_routing_manifest.json
alias_review_batch_sanity_gate_325c_routing_manifest.xlsx
alias_review_batch_sanity_gate_325c_send_to_adjudicator.jsonl
alias_review_batch_sanity_gate_325c_human_spot_check.xlsx
alias_review_batch_sanity_gate_325c_holdout.xlsx
alias_review_batch_sanity_gate_325c_notes.md
alias_review_batch_sanity_gate_325c_no_apply_proof.json
```

## Required behavior

1. Validate 325B readiness:

```text
decision = ALIAS_REVIEW_BATCH_325B_READY_FOR_HUMAN_OR_ADJUDICATOR_REVIEW
qa_fail_count = 0
loaded_safe_alias_candidate_count = 12
review_record_count = 12
pending_count = 12
accepted_count = 0
rejected_count = 0
needs_more_info_count = 0
holdout_count = 0
```

2. Load exactly 12 review records.
3. Preserve every record; each record must enter exactly one routing bucket.
4. Do not auto-accept any alias.
5. Check already-official overlap against `semantic_alias_candidates.json`.
6. Check conflict with official scope exclusions from `formal_scope_rules.json`.
7. Check invalid/mojibake/empty labels.
8. Check price/market-ratio ambiguity, especially:

```text
市盈率 (PE)
P/E（现价&最新股本摊薄）
P/B（现价）
市净率（PB）
```

These can be valid aliases, but they are high-impact and can be definition-sensitive. Route to `HUMAN_SPOT_CHECK_FIRST` unless evidence and target mapping are extremely explicit.

9. Check EBIT / EBITDA / profitability metrics for target ambiguity. Route to `HUMAN_SPOT_CHECK_FIRST` if target metric is not explicit and stable.
10. Route only candidates with strong evidence, explicit target, no official overlap, no scope conflict, no generic ambiguity, and no unit/price ambiguity to `SEND_TO_ADJUDICATOR`.
11. Route weaker or high-impact ambiguous candidates to `HUMAN_SPOT_CHECK_FIRST`.
12. Route unsafe candidates to appropriate HOLDOUT buckets.
13. Generate a compact safe adjudicator subset and a human spot-check workbook.
14. Confirm official assets are not modified.
15. Generate QA and no-apply proof.

## Routing policy

### SEND_TO_ADJUDICATOR
Use only if:

```text
label is specific
proposed target metric is explicit
no official overlap
no scope conflict
not unit/price ambiguous
not generic
not narrative/disclosure text
strong evidence/provenance exists
```

### HUMAN_SPOT_CHECK_FIRST
Use if:

```text
candidate may be valid but is high-impact or definition-sensitive
PE/PB/EBIT/EBITDA style ambiguity exists
target metric may need human confirmation before adjudicator
```

### HOLDOUT
Use holdout if:

```text
already official
category mismatch
label is generic ambiguous
unit or price ambiguity blocks safe routing
duplicate/conflict exists
weak evidence
invalid/mojibake/empty text
scope noise/disclosure text
```

## Expected summary fields

Do not hard-code routing counts; compute actual counts. Expected fields:

```text
input_review_record_count
routing_bucket_counts
send_to_adjudicator_count
human_spot_check_count
holdout_count
already_official_count
official_scope_conflict_count
invalid_text_count
price_or_ratio_ambiguity_count
target_ambiguity_count
duplicate_or_conflict_count
qa_fail_count
```

Expected decision if at least one routeable item exists and QA passes:

```text
ALIAS_REVIEW_BATCH_SANITY_GATE_325C_READY_FOR_HUMAN_SPOT_CHECK_OR_SAFE_ADJUDICATOR_SUBSET
```

Expected decision if no item is safe and QA passes:

```text
ALIAS_REVIEW_BATCH_SANITY_GATE_325C_NO_SAFE_ROUTEABLE_ITEMS
```

If blocking QA fails:

```text
ALIAS_REVIEW_BATCH_SANITY_GATE_325C_NOT_READY
```

## Suggested command

```bash
python tools/run_alias_review_batch_sanity_gate_325c.py \
  --alias-review-batch-dir D:\_datefac\output\alias_review_batch_325b \
  --alias-refinement-dir D:\_datefac\output\alias_candidate_refinement_325a \
  --output-dir D:\_datefac\output\alias_review_batch_sanity_gate_325c
```

If safe defaults are implemented:

```bash
python tools/run_alias_review_batch_sanity_gate_325c.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\alias_review_batch_sanity_gate_325c.py datefac\semantic\alias_review_batch_sanity_gate_325c_report.py tools\run_alias_review_batch_sanity_gate_325c.py
```

Then run the 325C runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/alias_review_batch_sanity_gate_325c.py
git add datefac/semantic/alias_review_batch_sanity_gate_325c_report.py
git add tools/run_alias_review_batch_sanity_gate_325c.py
```

Suggested commit message:

```text
Add 325C alias review sanity gate
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Input review record count.
5. Routing bucket counts.
6. Send-to-adjudicator count.
7. Human spot-check count.
8. Holdout count and reasons.
9. Top routed examples.
10. Official asset modification confirmation.
11. QA fail count.
12. Decision.
13. Git status result.
14. Commit hash.
15. Push result.
