# DateFac 322M Task
## Human Approval Package for Official Semantic Patch

## 1. Stage context

DateFac is currently at 322L.

322L completed an official semantic patch dry run and pushed it to `main`.

322L commit:

```text
6575143
```

322L changed files:

```text
datefac/semantic/official_patch_dry_run.py
datefac/semantic/official_patch_dry_run_report.py
tools/run_official_semantic_patch_dry_run_322l.py
```

322L output dir:

```text
D:\_datefac\output\official_semantic_patch_dry_run_322l
```

322L result:

```text
total_patch_operation_count = 10
alias_patch_operation_count = 3
scope_patch_operation_count = 7
unit_patch_operation_count = 0
rejected_noise_patch_operation_count = 0
expected_affected_candidate_count = 287
expected_trusted_gain = 49
expected_review_reduction = 287
expected_out_of_scope_or_rejected_gain = 238
qa_fail_count = 0
decision = OFFICIAL_SEMANTIC_PATCH_DRY_RUN_322L_READY_FOR_322M_HUMAN_APPROVAL
```

322L inspected target official files / rule groups:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\02B_ai_repair_override.xlsx
data/overrides/semantic_alias_candidates::virtual_target_group
resolved target rule groups:
- profitability
- cash_flow
- core_metric_scope_exclusions
```

322L no-apply proof:

```text
files_read_count = 6
files_written = [] inside proof object
target_official_files_inspected_count = 3
target_official_files_not_modified_count = 3
output_only_write_confirmation = true
decision = dry_run_only_no_apply
```

322M is the next step:

> Human Approval Package for Official Semantic Patch

322M must create a human-reviewable approval package from 322L dry-run patch operations. It must not apply the official patch.

## 2. Goal

Implement 322M: human approval package for the official semantic patch.

322M should read the 322L official patch dry-run package and produce a clean approval workbook / JSON package that allows a human reviewer to approve, reject, or request more review for each of the 10 patch operations.

322M should also be able to read a reviewed approval workbook, validate decisions, and generate a final official patch approval summary.

However, 322M must not modify official semantic mapping / override / production pipeline behavior.

## 3. Important design decision

322M should support two modes:

1. `prepare` mode:
   - generate the human approval package from 322L dry-run outputs;
   - default every patch decision to `PENDING_HUMAN_APPROVAL`;
   - do not assume approval.

2. `validate-reviewed` mode:
   - read a human-reviewed approval workbook;
   - validate approval decisions;
   - produce a final approved patch plan for 322N;
   - still do not apply the official patch.

If the current task only implements one mode first, prioritize `prepare` mode and clearly report that `validate-reviewed` is pending.

## 4. Hard constraints

1. Do not modify the production pipeline.
2. Do not directly modify official mapping / override files.
3. Do not apply the official patch.
4. Do not assume human approval.
5. Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
6. Do not modify `E:\mineru_lab`.
7. Do not commit `output/`, `E:\mineru_lab`, `input/semantic_adjudicator_responses_*`, `temp/`, or historical dirty files.
8. Do not promote semantic / LLM suggestions directly to trusted.
9. Every patch operation must remain traceable to schema validation, deterministic gate, human confirmation, 322J sandbox replay, 322K controlled proposal, and 322L dry run.
10. Stay approval-package first. Do not jump to official application.
11. Do not use `git add -A` or `git add .`.
12. Only precisely add 322M source files and docs if needed.

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

## 5. Inputs

322M should read:

```text
D:\_datefac\output\official_semantic_patch_dry_run_322l
```

It may also read for provenance and alignment checks:

```text
D:\_datefac\output\controlled_official_semantic_patch_proposal_322k
D:\_datefac\output\official_semantic_rule_candidates_322j
D:\_datefac\output\official_semantic_rule_candidates_322i
```

Relevant source modules:

```text
datefac/semantic/official_patch_dry_run.py
datefac/semantic/official_patch_dry_run_report.py
tools/run_official_semantic_patch_dry_run_322l.py
datefac/semantic/controlled_official_patch_proposal.py
```

322M may inspect official reference rule files for provenance display, but must not write to them.

## 6. Suggested new files

Follow existing project style, but suggested names are:

```text
datefac/semantic/official_patch_human_approval.py
datefac/semantic/official_patch_human_approval_report.py
tools/run_official_semantic_patch_human_approval_322m.py
```

Only create additional files if clearly justified.

## 7. Output directory

322M should write to:

```text
D:\_datefac\output\official_semantic_patch_human_approval_322m
```

Suggested output files:

```text
official_semantic_patch_human_approval_322m_summary.json
official_semantic_patch_human_approval_322m_approval_workbook.xlsx
official_semantic_patch_human_approval_322m_approval_template.json
official_semantic_patch_human_approval_322m_qa.json
official_semantic_patch_human_approval_322m_no_apply_proof.json
official_semantic_patch_human_approval_322m_review_instructions.md
```

If validate-reviewed mode is implemented, also support outputs such as:

```text
official_semantic_patch_human_approval_322m_reviewed_summary.json
official_semantic_patch_human_approval_322m_final_approved_patch_plan.json
official_semantic_patch_human_approval_322m_reviewed_qa.json
```

If existing naming conventions differ, follow project conventions.

## 8. Required behavior: prepare mode

### Step 1: Validate 322L readiness

Load 322L summary and QA.

Require:

```text
decision = OFFICIAL_SEMANTIC_PATCH_DRY_RUN_322L_READY_FOR_322M_HUMAN_APPROVAL
qa_fail_count = 0
total_patch_operation_count = 10
alias_patch_operation_count = 3
scope_patch_operation_count = 7
unit_patch_operation_count = 0
rejected_noise_patch_operation_count = 0
expected_affected_candidate_count = 287
expected_trusted_gain = 49
expected_review_reduction = 287
expected_out_of_scope_or_rejected_gain = 238
```

If any readiness check fails, stop and produce a NOT_READY decision.

### Step 2: Load dry-run patch operations

Load the 10 dry-run patch operations from 322L.

Each operation should preserve:

- patch operation id
- source proposal id
- source rule id
- rule type
- target official rule file or group
- operation type
- before state if available
- after state preview
- expected affected candidate count
- expected trusted gain / review reduction
- safety rationale
- rollback instruction
- complete provenance references

### Step 3: Build human approval records

Create one approval record per patch operation.

Each approval record should include:

- approval id
- patch operation id
- rule type
- target official rule file or group
- exact proposed change
- expected impact
- evidence summary
- risk note
- rollback note
- reviewer decision field
- reviewer note field
- approval timestamp field
- reviewer identity field if available

Default decision must be:

```text
PENDING_HUMAN_APPROVAL
```

Allowed future human decisions:

```text
APPROVED
REJECTED
NEEDS_MORE_REVIEW
```

322M prepare mode must not default any record to `APPROVED`.

### Step 4: Generate approval workbook

Generate an XLSX workbook suitable for manual review.

Suggested sheets:

1. `approval_summary`
2. `alias_approvals`
3. `scope_approvals`
4. `all_patch_operations`
5. `qa`
6. `review_instructions`
7. `no_apply_proof`

The workbook must make reviewer-editable fields obvious:

- reviewer_decision
- reviewer_note
- reviewer_name

### Step 5: Generate review instructions

Generate a Markdown review instruction file explaining:

- what this approval package is
- what the reviewer should check
- allowed decision values
- when to reject
- when to mark needs_more_review
- why this does not apply the official patch
- what happens in 322N

### Step 6: Generate no-apply proof

322M must prove it did not modify official mapping / override / production pipeline.

The no-apply proof should include:

- files read
- files written
- official target files inspected
- official target files not modified
- output-only write confirmation
- approval-package-only decision

### Step 7: QA checks

Prepare-mode QA must include:

- 322L readiness check
- patch operation count check
- approval record count check
- alias approval count = 3
- scope approval count = 7
- unit approval count = 0
- rejected noise approval count = 0
- all decisions are PENDING_HUMAN_APPROVAL
- duplicate approval id check
- duplicate patch operation id check
- provenance completeness check
- rollback note completeness check
- reviewer fields present check
- no official file modification check
- qa_fail_count

### Step 8: Prepare-mode decision

If all QA passes:

```text
OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_READY_FOR_HUMAN_REVIEW
```

If any blocking issue exists:

```text
OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_NOT_READY
```

Blocking reasons must be listed.

## 9. Required behavior: validate-reviewed mode

If implemented, validate-reviewed mode should:

1. Read a reviewed approval workbook.
2. Validate every reviewer decision is one of:
   - `APPROVED`
   - `REJECTED`
   - `NEEDS_MORE_REVIEW`
3. Require no `PENDING_HUMAN_APPROVAL` records before producing a final plan.
4. Generate final approved patch plan containing only `APPROVED` records.
5. Preserve rejected and needs-more-review records in a separate report.
6. Still not modify official mapping / override / pipeline.

Decision if all reviewed records are valid and at least one approved patch exists:

```text
OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_REVIEWED_READY_FOR_322N_OFFICIAL_PATCH_APPLICATION
```

Decision if any pending / invalid / conflicting review exists:

```text
OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_REVIEWED_NOT_READY
```

## 10. Suggested commands

Prepare mode:

```bash
python tools/run_official_semantic_patch_human_approval_322m.py \
  --mode prepare \
  --dry-run-dir D:\_datefac\output\official_semantic_patch_dry_run_322l \
  --controlled-proposal-dir D:\_datefac\output\controlled_official_semantic_patch_proposal_322k \
  --output-dir D:\_datefac\output\official_semantic_patch_human_approval_322m
```

Default command may run prepare mode:

```bash
python tools/run_official_semantic_patch_human_approval_322m.py
```

If validate-reviewed mode is implemented:

```bash
python tools/run_official_semantic_patch_human_approval_322m.py \
  --mode validate-reviewed \
  --reviewed-approval-workbook D:\_datefac\input\official_semantic_patch_human_approval_322m_reviewed.xlsx \
  --dry-run-dir D:\_datefac\output\official_semantic_patch_dry_run_322l \
  --output-dir D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed
```

## 11. Compile / run checks

Run:

```bash
python -m py_compile datefac\semantic\official_patch_human_approval.py datefac\semantic\official_patch_human_approval_report.py tools\run_official_semantic_patch_human_approval_322m.py
```

Then run the 322M prepare-mode runner.

If validate-reviewed mode is implemented, test it only with an explicit reviewed workbook fixture or a generated safe sample. Do not invent human approval as a real decision.

## 12. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 322M files, for example:

```bash
git add datefac/semantic/official_patch_human_approval.py
git add datefac/semantic/official_patch_human_approval_report.py
git add tools/run_official_semantic_patch_human_approval_322m.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Add 322M official semantic patch human approval package
```

Push to main only after successful checks.

## 13. Final report expected from Codex

After completion, report:

1. Modified files.
2. Commands run.
3. 322M output directory.
4. Approval record counts.
5. Decision distribution.
6. qa_fail_count.
7. decision.
8. no-apply proof summary.
9. Whether validate-reviewed mode was implemented.
10. git status result.
11. commit hash.
12. push result.
