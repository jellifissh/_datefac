# DateFac 322L Task
## Official Semantic Patch Dry Run

## 1. Stage context

DateFac is currently at 322K.

322K completed a controlled official semantic patch proposal package and pushed it to `main`.

322K commit:

```text
cd8d0c1
```

322K changed files:

```text
datefac/semantic/controlled_official_patch_proposal.py
datefac/semantic/controlled_official_patch_proposal_report.py
tools/run_controlled_official_semantic_patch_proposal_322k.py
```

322K output dir:

```text
D:\_datefac\output\controlled_official_semantic_patch_proposal_322k
```

322K result:

```text
total_patch_proposal_count = 10
alias_patch_proposal_count = 3
scope_patch_proposal_count = 7
unit_patch_proposal_count = 0
rejected_noise_patch_proposal_count = 0
expected_affected_candidate_count = 287
expected_trusted_gain = 49
expected_review_reduction = 287
expected_out_of_scope_or_rejected_gain = 238
qa_fail_count = 0
decision = CONTROLLED_OFFICIAL_SEMANTIC_PATCH_PROPOSAL_322K_READY_FOR_322L_OFFICIAL_PATCH_DRY_RUN
```

322L is the next step:

> Official Semantic Patch Dry Run

322L must simulate how the 10 controlled patch proposals would be transformed into official semantic rule changes, but must not actually modify official mapping / override / production pipeline behavior.

## 2. Goal

Implement 322L: official semantic patch dry run.

322L should read the 322K controlled official patch proposal package and generate a dry-run official patch diff package.

The dry run should answer:

1. Which official semantic rule files or rule groups would be changed in a future official patch?
2. What exact additions or modifications would be proposed?
3. Are the patch targets valid and non-conflicting?
4. Is the patch still aligned with 322J / 322K expected gains?
5. Is rollback obvious?
6. Is the system ready for 322M human approval / final official patch?

322L is not allowed to apply the official patch.

## 3. Hard constraints

1. Do not modify the production pipeline.
2. Do not directly modify official mapping / override files.
3. Do not apply the official patch.
4. Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
5. Do not modify `E:\mineru_lab`.
6. Do not commit `output/`, `E:\mineru_lab`, `input/semantic_adjudicator_responses_*`, `temp/`, or historical dirty files.
7. Do not promote semantic / LLM suggestions directly to trusted.
8. Every proposed patch must remain traceable to schema validation, deterministic gate, human confirmation, 322J sandbox replay, and 322K controlled proposal.
9. Stay dry-run first. Do not jump to official application.
10. Do not use `git add -A` or `git add .`.
11. Only precisely add 322L source files and docs if needed.

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

322L should read:

```text
D:\_datefac\output\controlled_official_semantic_patch_proposal_322k
```

It may also read for provenance and alignment checks:

```text
D:\_datefac\output\official_semantic_rule_candidates_322j
D:\_datefac\output\official_semantic_rule_candidates_322i
```

Relevant source modules:

```text
datefac/semantic/controlled_official_patch_proposal.py
datefac/semantic/controlled_official_patch_proposal_report.py
tools/run_controlled_official_semantic_patch_proposal_322k.py
datefac/semantic/official_rule_candidates.py
datefac/semantic/official_rule_candidates_sandbox_application.py
```

322L may inspect official reference rule files to build a diff, but must not write to them.

## 5. Suggested new files

Follow existing project style, but suggested names are:

```text
datefac/semantic/official_patch_dry_run.py
datefac/semantic/official_patch_dry_run_report.py
tools/run_official_semantic_patch_dry_run_322l.py
```

Only create additional files if clearly justified.

## 6. Output directory

322L should write to:

```text
D:\_datefac\output\official_semantic_patch_dry_run_322l
```

Suggested output files:

```text
official_semantic_patch_dry_run_322l_summary.json
official_semantic_patch_dry_run_322l_patch_diff_preview.json
official_semantic_patch_dry_run_322l_patch_diff_preview.md
official_semantic_patch_dry_run_322l_patch_diff_preview.xlsx
official_semantic_patch_dry_run_322l_target_files.json
official_semantic_patch_dry_run_322l_qa.json
official_semantic_patch_dry_run_322l_no_apply_proof.json
official_semantic_patch_dry_run_322l_rollback_plan.md
```

If existing naming conventions differ, follow project conventions.

## 7. Required behavior

### Step 1: Validate 322K readiness

Load the 322K summary and QA.

Require:

```text
decision = CONTROLLED_OFFICIAL_SEMANTIC_PATCH_PROPOSAL_322K_READY_FOR_322L_OFFICIAL_PATCH_DRY_RUN
qa_fail_count = 0
total_patch_proposal_count = 10
alias_patch_proposal_count = 3
scope_patch_proposal_count = 7
unit_patch_proposal_count = 0
rejected_noise_patch_proposal_count = 0
expected_affected_candidate_count = 287
expected_trusted_gain = 49
expected_review_reduction = 287
expected_out_of_scope_or_rejected_gain = 238
```

If any readiness check fails, stop and produce a NOT_READY decision.

### Step 2: Load controlled patch proposals

Load the 10 proposal records from 322K.

Each record should retain:

- proposal id
- source rule id
- rule type
- target official rule category
- proposed semantic change
- human confirmation provenance
- 322I provenance
- 322J sandbox evidence
- 322K proposal evidence
- expected affected candidate count
- expected gain / review reduction
- rollback note

### Step 3: Resolve official patch targets

For each proposal, resolve the future official target location.

322L should identify but not modify target files or rule groups, such as:

- official semantic alias mapping group
- official semantic scope / out_of_scope group
- related official reference rule group

The target resolution must verify:

- target file or rule group exists, if the project has an official file for it
- target category is valid
- proposed key does not duplicate existing official rule unless it is intended as an idempotent no-op
- proposed key does not conflict with existing official rule
- proposed value does not weaken safety gates

### Step 4: Generate dry-run patch diff

Generate a structured patch diff preview without applying it.

The diff preview should include:

- target file or rule group
- operation type, usually ADD_RULE or ADD_SCOPE_RULE
- before state, if applicable
- after state preview
- source proposal id
- expected affected candidate count
- expected trusted gain / review reduction
- safety rationale
- rollback instruction

No official file should be written.

### Step 5: Run dry-run consistency checks

322L must check:

- proposal count remains 10
- alias patch count remains 3
- scope patch count remains 7
- expected affected candidate count remains 287
- expected trusted gain remains 49
- expected review reduction remains 287
- expected out_of_scope_or_rejected gain remains 238
- every proposal maps to exactly one dry-run patch operation
- no duplicate patch operation
- no conflicting patch operation
- no target category mismatch
- no missing provenance
- no missing rollback instruction
- no official file modification

### Step 6: Generate no-apply proof

322L must produce a no-apply proof proving that it did not modify official mapping / override / production pipeline.

The no-apply proof should include:

- files read
- files written
- target official files inspected
- target official files not modified
- output-only write confirmation
- dry-run-only decision

### Step 7: Generate rollback plan

Even though 322L does not apply anything, it should generate a rollback plan for the future official patch.

Rollback plan should include:

- each proposed rule id
- target rule group
- rollback action
- expected effect of rollback
- provenance reference

### Step 8: Decision

If all QA passes:

```text
OFFICIAL_SEMANTIC_PATCH_DRY_RUN_322L_READY_FOR_322M_HUMAN_APPROVAL
```

If any blocking issue exists:

```text
OFFICIAL_SEMANTIC_PATCH_DRY_RUN_322L_NOT_READY
```

Blocking reasons must be listed.

## 8. Suggested command

```bash
python tools/run_official_semantic_patch_dry_run_322l.py \
  --controlled-proposal-dir D:\_datefac\output\controlled_official_semantic_patch_proposal_322k \
  --sandbox-application-dir D:\_datefac\output\official_semantic_rule_candidates_322j \
  --official-rule-candidate-dir D:\_datefac\output\official_semantic_rule_candidates_322i \
  --output-dir D:\_datefac\output\official_semantic_patch_dry_run_322l
```

If the project prefers defaults, allow running:

```bash
python tools/run_official_semantic_patch_dry_run_322l.py
```

## 9. Compile / run checks

Run:

```bash
python -m py_compile datefac\semantic\official_patch_dry_run.py datefac\semantic\official_patch_dry_run_report.py tools\run_official_semantic_patch_dry_run_322l.py
```

Then run the 322L runner.

## 10. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 322L files, for example:

```bash
git add datefac/semantic/official_patch_dry_run.py
git add datefac/semantic/official_patch_dry_run_report.py
git add tools/run_official_semantic_patch_dry_run_322l.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Add 322L official semantic patch dry run
```

Push to main only after successful checks.

## 11. Final report expected from Codex

After completion, report:

1. Modified files.
2. Commands run.
3. 322L output directory.
4. Dry-run patch operation counts.
5. Target official files / rule groups inspected.
6. qa_fail_count.
7. decision.
8. no-apply proof summary.
9. git status result.
10. commit hash.
11. push result.
