# DateFac 324B Task
## Scope Noise Human Review for 324A Refined Candidate

## Context

324A scope noise refinement is complete and pushed to remote main.

324A commit:

```text
3e638420b6fe686418e4fb0ea87b1104fb186f79
```

324A output dir:

```text
D:\_datefac\output\scope_noise_refinement_324a
```

324A result:

```text
input_scope_group_count = 19
excluded_already_official_count = 9
refined_scope_candidate_count = 1
holdout_count = 18
qa_fail_count = 0
decision = SCOPE_NOISE_REFINEMENT_324A_READY_FOR_SCOPE_REVIEW_BATCH
```

The single refined candidate is a long narrative rating-disclaimer style label:

```text
candidate_id = 324a::scope_noise::001
affected_review_required_count = 42
risk_flags = INVALID_YEAR | NO_YEAR_COLUMNS | UNKNOWN_METRIC_CODE | VALUE_PARSE_FAILED | LONG_LABEL_REVIEW_REQUIRED
```

Important interpretation:

```text
This candidate should not be treated like low-risk stock-code or balance-sheet-line noise. It requires explicit human scope review before any adjudicator response, sandbox replay, or official rule candidate flow.
```

## Goal

Implement 324B: human scope review package and reviewed validation for the single 324A refined scope candidate.

324B should prepare a human review workbook first. If reviewed validation is implemented, it should safely validate the filled workbook and produce a reviewed scope decision package.

324B must not apply rules, must not modify official assets, and must not run adjudicator/LLM.

## Hard constraints

- Do not modify production pipeline.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted directly.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 324A output and existing cached evidence only.
- Process only refined scope candidates from 324A.
- Do not treat long narrative labels as automatically safe scope exclusions.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 324B source/report/runner files.

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
D:\_datefac\output\scope_noise_refinement_324a
```

Expected files:

```text
scope_noise_refinement_324a_summary.json
scope_noise_refinement_324a_qa.json
scope_noise_refinement_324a_refined_batch.json
scope_noise_refinement_324a_scope_review_batch.xlsx
```

Reference inputs:

```text
D:\_datefac\output\remaining_burden_planning_323p
D:\_datefac\output\post_patch_regression_validation_323n
D:\_datefac\output\high_impact_semantic_candidates_mining_323a
D:\_datefac\output\candidate_text_repair_323ar
```

Official assets may be read only for already-official/reference checks:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/scope_noise_human_review_324b.py
datefac/semantic/scope_noise_human_review_324b_report.py
tools/run_scope_noise_human_review_324b.py
```

## Output directory

Prepare mode:

```text
D:\_datefac\output\scope_noise_human_review_324b
```

Reviewed validation mode, if implemented:

```text
D:\_datefac\output\scope_noise_human_review_324b_reviewed
```

Suggested prepare outputs:

```text
scope_noise_human_review_324b_summary.json
scope_noise_human_review_324b_qa.json
scope_noise_human_review_324b_review_workbook.xlsx
scope_noise_human_review_324b_review_package.json
scope_noise_human_review_324b_review_instructions.md
```

Suggested reviewed outputs:

```text
scope_noise_human_review_324b_reviewed_summary.json
scope_noise_human_review_324b_reviewed_qa.json
scope_noise_human_review_324b_reviewed_decision_plan.json
scope_noise_human_review_324b_reviewed_workbook.xlsx
```

## Prepare mode required behavior

1. Validate 324A readiness:

```text
decision = SCOPE_NOISE_REFINEMENT_324A_READY_FOR_SCOPE_REVIEW_BATCH
qa_fail_count = 0
refined_scope_candidate_count = 1
```

2. Load the refined scope candidate.
3. Preserve provenance, source group ids, affected review count, sample evidence, and all risk flags.
4. Generate exactly one human review record.
5. Default decision to:

```text
PENDING_HUMAN_SCOPE_REVIEW
```

6. Allowed human review decisions:

```text
CONFIRM_SCOPE_NOISE
REJECT_SCOPE_NOISE
NEEDS_MORE_INFO
ESCALATE_TO_ADJUDICATOR
```

7. Because the candidate has `LONG_LABEL_REVIEW_REQUIRED`, the review instructions must explicitly warn that it is not a low-risk automatic exclusion.
8. Generate workbook / JSON package / QA.

## Reviewed validation behavior

If implemented, reviewed validation should:

1. Read the reviewed workbook.
2. Validate exactly one review record.
3. Require decision in the allowed set.
4. Require no pending decision.
5. If `CONFIRM_SCOPE_NOISE`, produce a reviewed scope plan for later sandbox replay.
6. If `ESCALATE_TO_ADJUDICATOR`, produce a safe adjudicator request recommendation, but do not call LLM.
7. If `REJECT_SCOPE_NOISE` or `NEEDS_MORE_INFO`, do not produce a sandbox replay candidate.
8. Preserve all evidence and reviewer notes.
9. Confirm no official assets were modified.

## Expected prepare result

```text
review_record_count = 1
pending_human_scope_review_count = 1
qa_fail_count = 0
decision = SCOPE_NOISE_HUMAN_REVIEW_324B_READY_FOR_HUMAN_REVIEW
```

## Expected reviewed result if confirmed

```text
review_record_count = 1
confirmed_scope_noise_count = 1
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = SCOPE_NOISE_HUMAN_REVIEW_324B_REVIEWED_READY_FOR_324C_SANDBOX_REPLAY
```

## Expected reviewed result if escalation is chosen

```text
review_record_count = 1
escalate_to_adjudicator_count = 1
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = SCOPE_NOISE_HUMAN_REVIEW_324B_REVIEWED_READY_FOR_SAFE_ADJUDICATOR_REQUEST_PREP
```

## Suggested commands

Prepare mode:

```bash
python tools/run_scope_noise_human_review_324b.py \
  --mode prepare \
  --scope-refinement-dir D:\_datefac\output\scope_noise_refinement_324a \
  --output-dir D:\_datefac\output\scope_noise_human_review_324b
```

Reviewed validation mode, if implemented:

```bash
python tools/run_scope_noise_human_review_324b.py \
  --mode validate-reviewed \
  --reviewed-workbook D:\_datefac\output\scope_noise_human_review_324b\scope_noise_human_review_324b_review_workbook.xlsx \
  --scope-refinement-dir D:\_datefac\output\scope_noise_refinement_324a \
  --output-dir D:\_datefac\output\scope_noise_human_review_324b_reviewed
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\scope_noise_human_review_324b.py datefac\semantic\scope_noise_human_review_324b_report.py tools\run_scope_noise_human_review_324b.py
```

Then run prepare mode.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/scope_noise_human_review_324b.py
git add datefac/semantic/scope_noise_human_review_324b_report.py
git add tools/run_scope_noise_human_review_324b.py
```

Suggested commit message:

```text
Add 324B scope noise human review workflow
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Mode used.
5. Review record count.
6. Pending / confirmed / rejected / needs-more-info / escalation counts.
7. Risk flags carried forward.
8. qa_fail_count.
9. decision.
10. Whether reviewed validation mode was implemented.
11. git status result.
12. commit hash.
13. push result.
