# DateFac 322K Task
## Controlled Official Semantic Patch Proposal

## 1. Stage context

DateFac is currently at 322J.

322J has completed official semantic rule candidates sandbox application and has been pushed to `main`.

322J result:

```text
input_official_rule_candidate_count = 10
alias_rule_candidate_count = 3
scope_rule_candidate_count = 7
unit_rule_candidate_count = 0
rejected_noise_rule_candidate_count = 0
duplicate_rule_candidate_count = 0
conflict_rule_candidate_count = 0
ready_for_sandbox_application_count = 10
needs_additional_review_count = 0
trusted_total_before_322j = 2479
trusted_total_after_322j = 2528
review_required_total_before_322j = 3358
review_required_total_after_322j = 3071
rejected_total_before_322j = 135
rejected_total_after_322j = 373
trusted_gain_322j = 49
review_reduction_322j = 287
out_of_scope_or_rejected_gain_322j = 238
affected_candidate_count = 287
selected_core_trusted_rate_before_322j = 0.415104
selected_core_trusted_rate_after_322j = 0.423309
remaining_unknown_metric_candidate_count = 2897
remaining_unit_unknown_candidate_count = 491
remaining_manual_review_count = 3071
322I alignment delta = 0 for all core metrics
qa_fail_count = 0
decision = OFFICIAL_RULE_CANDIDATES_322J_READY_FOR_322K_CONTROLLED_OFFICIAL_PATCH_PROPOSAL
```

322J commit:

```text
99952bf
```

322J changed files:

```text
datefac/semantic/official_rule_candidates_sandbox_application.py
datefac/semantic/official_rule_candidates_sandbox_report.py
tools/run_official_semantic_rule_candidates_322j.py
```

322J output dir:

```text
D:\_datefac\output\official_semantic_rule_candidates_322j
```

## 2. Goal

Implement 322K: controlled official semantic patch proposal.

322K should read the 322J sandbox application results and generate a controlled, reviewable official patch proposal package for the 10 human-confirmed semantic rules.

322K must not directly modify production mapping / override / pipeline behavior.

The purpose is to prepare a precise proposal for the future official patch step, not to apply the official patch yet.

## 3. Hard constraints

1. Do not modify the production pipeline.
2. Do not directly modify official mapping / override files.
3. Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
4. Do not modify `E:\mineru_lab`.
5. Do not commit `output/`, `E:\mineru_lab`, `input/semantic_adjudicator_responses_*`, `temp/`, or historical dirty files.
6. Do not promote semantic / LLM suggestions directly to trusted.
7. All semantic rules must remain traceable to schema validation, deterministic gate, human confirmation, and sandbox replay.
8. Stay sandbox/proposal-first. Do not jump to production application.
9. Do not use `git add -A` or `git add .`.
10. Only precisely add 322K source files and docs if needed.

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

322K should read:

```text
D:\_datefac\output\official_semantic_rule_candidates_322j
```

It may also read 322I candidate package if needed for provenance:

```text
D:\_datefac\output\official_semantic_rule_candidates_322i
```

And relevant source modules:

```text
datefac/semantic/official_rule_candidates.py
datefac/semantic/official_rule_candidates_report.py
datefac/semantic/official_rule_candidates_sandbox_application.py
datefac/semantic/official_rule_candidates_sandbox_report.py
tools/run_official_semantic_rule_candidates_322j.py
```

Reuse existing report / validation / QA helpers where possible.

## 5. Suggested new files

Follow existing project style, but suggested names are:

```text
datefac/semantic/controlled_official_patch_proposal.py
datefac/semantic/controlled_official_patch_proposal_report.py
tools/run_controlled_official_semantic_patch_proposal_322k.py
```

Only create additional files if clearly justified.

## 6. Output directory

322K should write to:

```text
D:\_datefac\output\controlled_official_semantic_patch_proposal_322k
```

Suggested output files:

```text
controlled_official_semantic_patch_proposal_322k_summary.json
controlled_official_semantic_patch_proposal_322k_patch_proposals.xlsx
controlled_official_semantic_patch_proposal_322k_alias_patch_proposals.json
controlled_official_semantic_patch_proposal_322k_scope_patch_proposals.json
controlled_official_semantic_patch_proposal_322k_qa.json
controlled_official_semantic_patch_proposal_322k_no_apply_proof.json
controlled_official_semantic_patch_proposal_322k_review_notes.md
```

If existing naming conventions differ, follow the project conventions.

## 7. Required behavior

### Step 1: Validate 322J readiness

Load the 322J summary and QA.

Require:

```text
decision = OFFICIAL_RULE_CANDIDATES_322J_READY_FOR_322K_CONTROLLED_OFFICIAL_PATCH_PROPOSAL
qa_fail_count = 0
trusted_gain_322j = 49
review_reduction_322j = 287
out_of_scope_or_rejected_gain_322j = 238
affected_candidate_count = 287
322I alignment delta = 0
```

If any requirement fails, stop and produce a NOT_READY decision.

### Step 2: Build controlled official patch proposal model

Create a structured proposal model for the 10 rules:

- 3 alias patch proposals
- 7 scope / out_of_scope patch proposals
- 0 unit proposals
- 0 rejected noise proposals

Each proposal must include:

- proposal id
- source rule id
- rule type
- human confirmation provenance
- 322I source provenance
- 322J sandbox application evidence
- expected affected candidate count
- expected trusted gain if applicable
- expected review reduction if applicable
- target official rule category
- intended future target file or rule group
- exact proposed semantic change
- safety rationale
- rollback note
- whether it is eligible for official patch

322K should propose where the rule would go, but must not write it there.

### Step 3: Generate reviewable patch proposal artifacts

Generate machine-readable JSON and human-readable XLSX / Markdown outputs.

The XLSX should be suitable for manual review and should clearly separate:

1. alias patch proposals
2. scope / out_of_scope patch proposals
3. QA summary
4. no-apply proof
5. risk notes

### Step 4: Generate no-apply proof

322K must prove that it did not modify official mapping / override / production pipeline.

The no-apply proof should include:

- files read
- files written
- explicit list of official files not modified
- output-only write confirmation
- decision that this is proposal-only

### Step 5: QA checks

322K QA must include at least:

- 322J readiness check
- proposal count check
- alias proposal count = 3
- scope proposal count = 7
- unit proposal count = 0
- rejected noise proposal count = 0
- duplicate proposal check
- conflict proposal check
- target category validation
- provenance completeness check
- no-apply proof check
- expected gain alignment check
- rollback note completeness check
- qa_fail_count

### Step 6: Decision

If all QA passes:

```text
CONTROLLED_OFFICIAL_SEMANTIC_PATCH_PROPOSAL_322K_READY_FOR_322L_OFFICIAL_PATCH_DRY_RUN
```

If any blocking issue exists:

```text
CONTROLLED_OFFICIAL_SEMANTIC_PATCH_PROPOSAL_322K_NOT_READY
```

Blocking reasons must be listed.

## 8. Suggested command

```bash
python tools/run_controlled_official_semantic_patch_proposal_322k.py \
  --sandbox-application-dir D:\_datefac\output\official_semantic_rule_candidates_322j \
  --official-rule-candidate-dir D:\_datefac\output\official_semantic_rule_candidates_322i \
  --output-dir D:\_datefac\output\controlled_official_semantic_patch_proposal_322k
```

If the project prefers defaults, allow running:

```bash
python tools/run_controlled_official_semantic_patch_proposal_322k.py
```

## 9. Compile / run checks

Run:

```bash
python -m py_compile datefac\semantic\controlled_official_patch_proposal.py datefac\semantic\controlled_official_patch_proposal_report.py tools\run_controlled_official_semantic_patch_proposal_322k.py
```

Then run the 322K runner.

## 10. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 322K files, for example:

```bash
git add datefac/semantic/controlled_official_patch_proposal.py
git add datefac/semantic/controlled_official_patch_proposal_report.py
git add tools/run_controlled_official_semantic_patch_proposal_322k.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Add 322K controlled official semantic patch proposal
```

Push to main only after successful checks.

## 11. Final report expected from Codex

After completion, report:

1. Modified files.
2. Commands run.
3. 322K output directory.
4. Proposal counts.
5. qa_fail_count.
6. decision.
7. git status result.
8. commit hash.
9. push result.
