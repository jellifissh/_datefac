# DateFac 325D Task
## Alias Human Spot-Check Workflow

## Context

325C alias review batch sanity gate is complete and pushed to remote main.

325C commit:

```text
db3d55fcbecb93fd916b822a69ba915381402091
```

325C output dir:

```text
D:\_datefac\output\alias_review_batch_sanity_gate_325c
```

325C result:

```text
input_review_record_count = 12
routing_bucket_counts = {
  HUMAN_SPOT_CHECK_FIRST = 11,
  HOLDOUT_DUPLICATE_OR_CONFLICT = 1,
  all_other_buckets = 0
}
send_to_adjudicator_count = 0
human_spot_check_count = 11
holdout_count = 1
holdout_reason = duplicate/conflict
qa_fail_count = 0
decision = ALIAS_REVIEW_BATCH_SANITY_GATE_325C_READY_FOR_HUMAN_SPOT_CHECK_OR_SAFE_ADJUDICATOR_SUBSET
official_assets_modified = false
llm_or_adjudicator_called = false
```

325D is the next stage:

> Turn the 11 `HUMAN_SPOT_CHECK_FIRST` alias candidates into a human spot-check workbook/package, then support validation of the reviewed workbook.

325D must not call LLM/adjudicator and must not create official rule candidates. It only prepares and validates human routing decisions.

## Goal

Implement 325D: alias human spot-check workflow.

Prepare mode should create a human spot-check workbook containing exactly the 11 candidates routed to `HUMAN_SPOT_CHECK_FIRST` in 325C.

Validate-reviewed mode should read a filled workbook and produce a final routing plan:

```text
SEND_TO_ADJUDICATOR
HOLDOUT
REJECT_ALIAS
NEEDS_MORE_INFO
```

Only candidates explicitly confirmed by human review should proceed to safe adjudicator request prep in the next stage.

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 325C routing output and 325B/325A evidence only.
- Process only the 11 `HUMAN_SPOT_CHECK_FIRST` records from 325C.
- Carry forward the single 325C holdout into the final routing plan in validate-reviewed mode, but do not ask the human to review it again.
- Do not produce official rule candidates in 325D.
- Do not produce controlled proposals.
- Do not produce sandbox replay packages.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 325D source/report/runner files.

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
D:\_datefac\output\alias_review_batch_sanity_gate_325c
```

Expected files may include:

```text
alias_review_batch_sanity_gate_325c_summary.json
alias_review_batch_sanity_gate_325c_qa.json
alias_review_batch_sanity_gate_325c_routing_manifest.json
alias_review_batch_sanity_gate_325c_routing_manifest.xlsx
alias_review_batch_sanity_gate_325c_human_spot_check.xlsx
alias_review_batch_sanity_gate_325c_holdout.xlsx
```

Reference inputs:

```text
D:\_datefac\output\alias_review_batch_325b
D:\_datefac\output\alias_candidate_refinement_325a
```

Official assets may be read only for context:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/alias_human_spot_check_325d.py
datefac/semantic/alias_human_spot_check_325d_report.py
tools/run_alias_human_spot_check_325d.py
```

## Output directories

Prepare mode:

```text
D:\_datefac\output\alias_human_spot_check_325d
```

Reviewed mode:

```text
D:\_datefac\output\alias_human_spot_check_325d_reviewed
```

Suggested prepare outputs:

```text
alias_human_spot_check_325d_summary.json
alias_human_spot_check_325d_qa.json
alias_human_spot_check_325d_workbook.xlsx
alias_human_spot_check_325d_review_package.json
alias_human_spot_check_325d_review_instructions.md
alias_human_spot_check_325d_no_apply_proof.json
```

Suggested reviewed outputs:

```text
alias_human_spot_check_325d_reviewed_summary.json
alias_human_spot_check_325d_reviewed_qa.json
alias_human_spot_check_325d_final_routing_plan.json
alias_human_spot_check_325d_reviewed_workbook.xlsx
alias_human_spot_check_325d_send_to_adjudicator.xlsx
alias_human_spot_check_325d_holdout_or_rejected.xlsx
alias_human_spot_check_325d_no_apply_proof.json
```

## Prepare mode required behavior

1. Validate 325C readiness:

```text
decision = ALIAS_REVIEW_BATCH_SANITY_GATE_325C_READY_FOR_HUMAN_SPOT_CHECK_OR_SAFE_ADJUDICATOR_SUBSET
qa_fail_count = 0
input_review_record_count = 12
human_spot_check_count = 11
send_to_adjudicator_count = 0
holdout_count = 1
```

2. Load exactly 11 `HUMAN_SPOT_CHECK_FIRST` records.
3. Preserve the 1 holdout record from 325C separately for final routing context.
4. Generate exactly 11 human spot-check records.
5. Default decision:

```text
PENDING_HUMAN_SPOT_CHECK
```

6. Allowed human decisions:

```text
SEND_TO_ADJUDICATOR
HOLDOUT
REJECT_ALIAS
NEEDS_MORE_INFO
```

7. Include candidate id, alias label, proposed target metric if available, evidence, risk flags, ambiguity notes, 325C routing reason, sample rows, and provenance.
8. Explicitly warn that PE/PB/P/E/P/B/EBIT/EBITDA style aliases are definition-sensitive and must not be auto-promoted.
9. Confirm official assets are not modified.
10. Generate QA and no-apply proof.

## Validate-reviewed mode required behavior

1. Read the reviewed 325D workbook.
2. Validate exactly 11 spot-check records.
3. Require every reviewed record to have one allowed decision.
4. Require no pending decisions.
5. If decision is `SEND_TO_ADJUDICATOR`, include the record in the final safe adjudicator candidate set.
6. If decision is `HOLDOUT`, `REJECT_ALIAS`, or `NEEDS_MORE_INFO`, exclude it from adjudicator request prep and preserve it in holdout/rejected outputs.
7. Carry forward the 325C automatic holdout record.
8. Do not call LLM/adjudicator.
9. Do not produce official candidates.
10. Confirm official assets are not modified.

## Expected prepare result

```text
spot_check_record_count = 11
pending_count = 11
send_to_adjudicator_count = 0
holdout_count = 0
rejected_count = 0
needs_more_info_count = 0
carried_forward_325c_holdout_count = 1
qa_fail_count = 0
decision = ALIAS_HUMAN_SPOT_CHECK_325D_READY_FOR_HUMAN_REVIEW
```

## Expected reviewed result if some aliases are approved for adjudicator

```text
spot_check_record_count = 11
pending_count = 0
invalid_decision_count = 0
send_to_adjudicator_count = <computed>
holdout_count = <computed>
rejected_count = <computed>
needs_more_info_count = <computed>
carried_forward_325c_holdout_count = 1
qa_fail_count = 0
decision = ALIAS_HUMAN_SPOT_CHECK_325D_REVIEWED_READY_FOR_SAFE_ADJUDICATOR_REQUEST_PREP
```

If no item is sent to adjudicator but QA passes:

```text
ALIAS_HUMAN_SPOT_CHECK_325D_REVIEWED_NO_SAFE_ADJUDICATOR_ITEMS
```

If pending/invalid decisions remain:

```text
ALIAS_HUMAN_SPOT_CHECK_325D_REVIEWED_NOT_READY
```

## Suggested commands

Prepare mode:

```bash
python tools/run_alias_human_spot_check_325d.py \
  --mode prepare \
  --sanity-gate-dir D:\_datefac\output\alias_review_batch_sanity_gate_325c \
  --alias-review-batch-dir D:\_datefac\output\alias_review_batch_325b \
  --output-dir D:\_datefac\output\alias_human_spot_check_325d
```

Validate-reviewed mode:

```bash
python tools/run_alias_human_spot_check_325d.py \
  --mode validate-reviewed \
  --sanity-gate-dir D:\_datefac\output\alias_review_batch_sanity_gate_325c \
  --reviewed-workbook D:\_datefac\output\alias_human_spot_check_325d\alias_human_spot_check_325d_workbook.xlsx \
  --output-dir D:\_datefac\output\alias_human_spot_check_325d_reviewed
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\alias_human_spot_check_325d.py datefac\semantic\alias_human_spot_check_325d_report.py tools\run_alias_human_spot_check_325d.py
```

Then run prepare mode at minimum.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/alias_human_spot_check_325d.py
git add datefac/semantic/alias_human_spot_check_325d_report.py
git add tools/run_alias_human_spot_check_325d.py
```

Suggested commit message:

```text
Add 325D alias human spot-check workflow
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Mode used.
5. Spot-check record count.
6. Pending / send-to-adjudicator / holdout / rejected / needs-more-info counts.
7. Carried-forward 325C holdout count.
8. Top spot-check examples.
9. Whether validate-reviewed mode was implemented.
10. Official asset modification confirmation.
11. QA fail count.
12. Decision.
13. Git status result.
14. Commit hash.
15. Push result.
