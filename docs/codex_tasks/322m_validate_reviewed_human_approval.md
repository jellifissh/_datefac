# DateFac 322M-R Task
## Validate Reviewed Human Approval Path Hardening

## 1. Stage context

DateFac is currently at 322M.

322M prepare mode completed successfully and pushed to `main`.

322M commit:

```text
1050a7f3533eb7df3258de01f4fcfd06c54e8fc1
```

322M changed files:

```text
datefac/semantic/official_patch_human_approval.py
datefac/semantic/official_patch_human_approval_report.py
tools/run_official_semantic_patch_human_approval_322m.py
```

322M prepare output dir:

```text
D:\_datefac\output\official_semantic_patch_human_approval_322m
```

322M prepare result:

```text
approval_record_count = 10
alias_approval_count = 3
scope_approval_count = 7
unit_approval_count = 0
rejected_noise_approval_count = 0
decision_distribution = {"PENDING_HUMAN_APPROVAL": 10}
qa_fail_count = 0
decision = OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_READY_FOR_HUMAN_REVIEW
```

Residual risk from 322M:

```text
validate-reviewed mode was implemented, but quick safe sample verification did not complete cleanly enough to promote it beyond implemented.
Prepare mode is verified. Validate-reviewed mode needs hardening and complete safe-sample verification before using it for real reviewed approval workbooks.
```

322M-R is the next step:

> Validate and harden the `validate-reviewed` path before moving toward 322N official patch application.

This is not official patch application.

## 2. Goal

Implement 322M-R: validate-reviewed human approval path hardening.

The goal is to make the reviewed approval workbook ingestion and validation path reliable, deterministic, and testable before a real human-reviewed workbook is used to generate a final approved patch plan.

322M-R should:

1. Generate a safe reviewed-approval sample workbook from the 322M prepare output.
2. Validate the sample workbook through `validate-reviewed` mode.
3. Produce a final approved patch plan only when all records have valid non-pending decisions.
4. Prove invalid / pending / malformed reviewed workbooks fail safely.
5. Not apply any official semantic patch.

## 3. Hard constraints

1. Do not modify the production pipeline.
2. Do not directly modify official mapping / override files.
3. Do not apply the official patch.
4. Do not assume real human approval.
5. Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
6. Do not modify `E:\mineru_lab`.
7. Do not commit `output/`, `E:\mineru_lab`, `input/semantic_adjudicator_responses_*`, `temp/`, or historical dirty files.
8. Do not promote semantic / LLM suggestions directly to trusted.
9. Every reviewed approval must remain traceable to 322L dry run and 322M approval record.
10. Stay validation-first. Do not jump to official application.
11. Do not use `git add -A` or `git add .`.
12. Only precisely add or modify 322M-R source/test/helper files.

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

322M-R should read the verified 322M prepare output:

```text
D:\_datefac\output\official_semantic_patch_human_approval_322m
```

It may read upstream outputs for consistency checks:

```text
D:\_datefac\output\official_semantic_patch_dry_run_322l
D:\_datefac\output\controlled_official_semantic_patch_proposal_322k
```

Relevant source modules:

```text
datefac/semantic/official_patch_human_approval.py
datefac/semantic/official_patch_human_approval_report.py
tools/run_official_semantic_patch_human_approval_322m.py
```

## 5. Suggested implementation options

Prefer small, focused changes to existing 322M files if possible.

Possible changes:

```text
datefac/semantic/official_patch_human_approval.py
datefac/semantic/official_patch_human_approval_report.py
tools/run_official_semantic_patch_human_approval_322m.py
```

If a helper is useful, add a dedicated tool such as:

```text
tools/create_safe_reviewed_approval_sample_322m.py
```

Only add this helper if it materially improves verification.

## 6. Output directories

Use output-only directories, such as:

```text
D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed_sample
D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed_validation
D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed_negative_cases
```

Do not commit these outputs.

## 7. Required behavior

### Step 1: Inspect prepare output structure

Read the 322M approval workbook / JSON produced by prepare mode.

Verify:

- approval_record_count = 10
- decisions are all PENDING_HUMAN_APPROVAL in prepare output
- editable reviewer fields exist
- stable approval ids / patch operation ids exist
- provenance fields are preserved

### Step 2: Create safe sample reviewed workbook

Create a safe sample reviewed workbook for validation testing.

Important:

- This is not real human approval.
- It must be labeled clearly as a sample / fixture.
- Use deterministic reviewer fields, for example:
  - reviewer_name = `SAFE_SAMPLE_REVIEWER`
  - reviewer_note = `safe sample validation fixture, not real approval`

Recommended sample decision distribution:

```text
APPROVED = 10
REJECTED = 0
NEEDS_MORE_REVIEW = 0
PENDING_HUMAN_APPROVAL = 0
```

The output should be stored under an output-only path and must not be committed.

### Step 3: Validate sample workbook

Run `validate-reviewed` mode on the safe sample workbook.

Expected successful result:

```text
reviewed_approval_record_count = 10
approved_count = 10
rejected_count = 0
needs_more_review_count = 0
pending_count = 0
invalid_decision_count = 0
final_approved_patch_count = 10
qa_fail_count = 0
decision = OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_REVIEWED_READY_FOR_322N_OFFICIAL_PATCH_APPLICATION
```

The generated final approved patch plan must still not apply the patch.

### Step 4: Negative case validation

Create or simulate at least three negative cases:

1. One record remains `PENDING_HUMAN_APPROVAL`.
2. One record has an invalid decision value.
3. One required reviewer / provenance / patch operation field is missing.

Each negative case must fail safely with:

```text
OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_REVIEWED_NOT_READY
```

and `qa_fail_count > 0`.

### Step 5: Validate no-apply proof

For both positive and negative validation runs, confirm:

- official mapping files not modified
- official override files not modified
- production pipeline not modified
- output-only writes only
- no official patch application

### Step 6: QA

322M-R QA must include:

- positive sample validation pass
- negative pending case fail
- negative invalid decision case fail
- negative missing field case fail
- no-apply proof pass
- final approved patch plan count check
- provenance completeness check
- duplicate approval id check
- duplicate patch operation id check
- official patch not applied check

### Step 7: Decision

If all checks pass:

```text
OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_VALIDATE_REVIEWED_READY_FOR_REAL_HUMAN_REVIEWED_WORKBOOK
```

If any check fails:

```text
OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_VALIDATE_REVIEWED_NOT_READY
```

## 8. Suggested commands

Compile:

```bash
python -m py_compile datefac\semantic\official_patch_human_approval.py datefac\semantic\official_patch_human_approval_report.py tools\run_official_semantic_patch_human_approval_322m.py
```

Run prepare mode only if needed:

```bash
python tools\run_official_semantic_patch_human_approval_322m.py --mode prepare
```

Run validate-reviewed sample path after generating a safe sample reviewed workbook:

```bash
python tools\run_official_semantic_patch_human_approval_322m.py \
  --mode validate-reviewed \
  --reviewed-approval-workbook D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed_sample\reviewed_sample.xlsx \
  --dry-run-dir D:\_datefac\output\official_semantic_patch_dry_run_322l \
  --output-dir D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed_validation
```

If a helper tool is added, document and run it.

## 9. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 322M-R source/helper files. Examples:

```bash
git add datefac/semantic/official_patch_human_approval.py
git add datefac/semantic/official_patch_human_approval_report.py
git add tools/run_official_semantic_patch_human_approval_322m.py
```

If a helper was added:

```bash
git add tools/create_safe_reviewed_approval_sample_322m.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Harden 322M reviewed human approval validation
```

Push to main only after successful checks.

## 10. Final report expected from Codex

After completion, report:

1. Modified files.
2. Commands run.
3. Whether a safe sample reviewed workbook was generated.
4. Positive validation result.
5. Negative validation results.
6. Final approved patch plan count for safe sample.
7. qa_fail_count for the 322M-R meta validation.
8. decision.
9. no-apply proof summary.
10. git status result.
11. commit hash.
12. push result.
