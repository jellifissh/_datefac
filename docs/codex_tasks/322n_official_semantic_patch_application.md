# DateFac 322N Task
## Official Semantic Patch Application

## 1. Stage context

DateFac has completed the real human-reviewed validation for the 322M approval workbook.

The reviewed approval validation result is:

```text
reviewed_approval_record_count = 10
approved_patch_count = 10
rejected_patch_count = 0
needs_more_review_count = 0
pending_count = 0
invalid_decision_count = 0
final_approved_patch_count = 10
qa_fail_count = 0
decision = OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_REVIEWED_READY_FOR_322N_OFFICIAL_PATCH_APPLICATION
decision_distribution = {'APPROVED': 10}
```

Reviewed validation output dir:

```text
D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed
```

It contains:

```text
official_semantic_patch_human_approval_322m_reviewed_workbook.xlsx
official_semantic_patch_human_approval_322m_reviewed_summary.json
official_semantic_patch_human_approval_322m_reviewed_qa.json
official_semantic_patch_human_approval_322m_final_approved_patch_plan.json
```

Upstream completed stages:

```text
322J: official rule candidates sandbox application
322K: controlled official patch proposal
322L: official patch dry run
322M: human approval package
322M-R: validate-reviewed path hardening
322M reviewed validation: real reviewed workbook passed
```

322N is the first stage that may modify official semantic rule assets, but only through a controlled, approved, auditable patch application.

## 2. Goal

Implement 322N: official semantic patch application.

322N should read the final approved patch plan from 322M reviewed validation and apply only the 10 approved semantic patch operations to their official target rule assets.

322N must:

1. Validate the reviewed approval result.
2. Validate the final approved patch plan.
3. Apply only approved patch operations.
4. Modify only the intended official semantic rule assets.
5. Generate before / after snapshots.
6. Generate exact patch application logs.
7. Generate rollback artifacts.
8. Run post-apply QA.
9. Prepare the system for 322O post-patch regression validation.

## 3. Critical boundary

322N is allowed to modify official semantic rule assets only if all safety gates pass.

322N is not allowed to modify:

- production pipeline code
- parser code
- extraction code
- delivery pipeline code
- unrelated benchmark / temp / input artifacts
- `E:\mineru_lab`

322N must not run MinerU / StructEqTable / Docling / PPStructure / VLM.

322N must not commit `output/`, `input/semantic_adjudicator_responses_*`, `temp/`, or historical dirty files.

## 4. Hard constraints

1. Read the final approved patch plan from 322M reviewed validation.
2. Require `decision = OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_REVIEWED_READY_FOR_322N_OFFICIAL_PATCH_APPLICATION`.
3. Require `qa_fail_count = 0`.
4. Require exactly 10 approved patch operations.
5. Require no rejected, no needs-more-review, no pending, no invalid decision.
6. Apply only the approved operations present in the final approved patch plan.
7. Do not invent new rules.
8. Do not broaden rule scope.
9. Do not modify production pipeline.
10. Do not run PDF parsers or OCR/VLM tools.
11. Generate rollback artifacts before or during application.
12. Run post-apply QA.
13. Do not use `git add -A` or `git add .`.
14. Only precisely add / modify 322N source files and official semantic rule asset files that the patch explicitly targets.

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

Primary input:

```text
D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed\official_semantic_patch_human_approval_322m_final_approved_patch_plan.json
```

Also read:

```text
D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed\official_semantic_patch_human_approval_322m_reviewed_summary.json
D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed\official_semantic_patch_human_approval_322m_reviewed_qa.json
D:\_datefac\output\official_semantic_patch_dry_run_322l
D:\_datefac\output\controlled_official_semantic_patch_proposal_322k
```

Official target assets previously inspected by 322L:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\02B_ai_repair_override.xlsx
data/overrides/semantic_alias_candidates::virtual_target_group
```

Resolved target rule groups from 322L:

```text
profitability
cash_flow
core_metric_scope_exclusions
```

322N should inspect current official assets again before applying patches.

## 6. Suggested new files

Follow existing project style. Suggested names:

```text
datefac/semantic/official_patch_application.py
datefac/semantic/official_patch_application_report.py
tools/run_official_semantic_patch_application_322n.py
```

Only add extra helper files if clearly justified.

## 7. Output directory

322N should write output artifacts to:

```text
D:\_datefac\output\official_semantic_patch_application_322n
```

Suggested outputs:

```text
official_semantic_patch_application_322n_summary.json
official_semantic_patch_application_322n_application_log.jsonl
official_semantic_patch_application_322n_before_snapshot.json
official_semantic_patch_application_322n_after_snapshot.json
official_semantic_patch_application_322n_asset_diff_preview.md
official_semantic_patch_application_322n_asset_diff_preview.xlsx
official_semantic_patch_application_322n_rollback_plan.json
official_semantic_patch_application_322n_rollback_instructions.md
official_semantic_patch_application_322n_qa.json
```

Do not commit output artifacts.

## 8. Required behavior

### Step 1: Validate reviewed approval readiness

Load reviewed summary and QA.

Require:

```text
decision = OFFICIAL_SEMANTIC_PATCH_HUMAN_APPROVAL_322M_REVIEWED_READY_FOR_322N_OFFICIAL_PATCH_APPLICATION
qa_fail_count = 0
reviewed_approval_record_count = 10
approved_patch_count = 10
rejected_patch_count = 0
needs_more_review_count = 0
pending_count = 0
invalid_decision_count = 0
final_approved_patch_count = 10
```

If any check fails, do not apply anything.

### Step 2: Load and validate final approved patch plan

Load the final approved patch plan JSON.

Validate:

- patch plan exists
- approved patch count = 10
- each patch has a stable patch operation id
- each patch has a source approval id
- each patch has a target official asset or rule group
- each patch has exact proposed change
- each patch has rollback instruction
- each patch has complete provenance
- every patch came from an APPROVED reviewed record

If any check fails, do not apply anything.

### Step 3: Load official target assets

Load target official assets resolved by 322L and final patch plan.

Known likely targets include:

```text
data/mapping/formal_scope_rules.json
data/overrides/02B_ai_repair_override.xlsx
```

and a virtual semantic alias target group if the project represents alias candidates through a generated or override-backed asset.

Do not guess target formats. Inspect existing code / asset conventions and reuse existing structures.

### Step 4: Build before snapshot

Before modifying anything, generate a before snapshot of all official target assets to be changed.

The before snapshot should include:

- file path
- file exists
- content hash where possible
- relevant target rule groups
- relevant existing rule entries
- row counts / rule counts

### Step 5: Pre-apply conflict / idempotency check

For each approved operation, check:

- target exists or can be safely created only if the project convention supports it
- proposed rule does not duplicate an existing rule with different semantics
- proposed rule does not conflict with an existing rule
- if an equivalent rule already exists, mark as idempotent already-applied rather than duplicate failure only if semantics exactly match
- all 10 operations map to expected targets

If there are conflicts, do not apply anything.

### Step 6: Apply official patch operations

Apply the 10 approved operations to the official target assets.

Expected operation counts:

```text
total_applied_or_idempotent_operation_count = 10
alias_operation_count = 3
scope_operation_count = 7
unit_operation_count = 0
rejected_noise_operation_count = 0
```

If the project requires separate handling for alias and scope:

- alias operations should go to the official alias / override target used by DateFac conventions;
- scope / out_of_scope operations should go to official scope rules, likely `formal_scope_rules.json` or the appropriate group under it.

Do not modify unrelated rules.

### Step 7: Generate after snapshot and diff

After applying, generate after snapshot and a human-readable diff.

The diff must show:

- target file / group
- operation type
- rule id or key
- before state
- after state
- source approval id
- rollback instruction

### Step 8: Generate rollback artifacts

Generate rollback plan and rollback instructions.

Rollback must be able to remove the 10 newly applied operations or restore previous entries if an operation modified an existing entry.

### Step 9: Post-apply QA

QA must include:

- reviewed approval readiness pass
- final approved patch plan validation pass
- target asset existence pass
- before snapshot pass
- conflict check pass
- operation count check
- alias operation count = 3
- scope operation count = 7
- no unit operation
- no rejected noise operation
- all operations applied or exactly idempotent
- no unrelated official asset modified
- rollback artifact completeness
- after snapshot pass
- qa_fail_count

### Step 10: Decision

If all QA passes:

```text
OFFICIAL_SEMANTIC_PATCH_APPLICATION_322N_READY_FOR_322O_POST_PATCH_REGRESSION
```

If anything fails:

```text
OFFICIAL_SEMANTIC_PATCH_APPLICATION_322N_NOT_READY
```

If anything fails before application, no official files should be modified.

If anything fails after partial application, stop, report partial application, and provide rollback instructions. Do not hide partial state.

## 9. Suggested command

```bash
python tools/run_official_semantic_patch_application_322n.py \
  --reviewed-approval-dir D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed \
  --dry-run-dir D:\_datefac\output\official_semantic_patch_dry_run_322l \
  --output-dir D:\_datefac\output\official_semantic_patch_application_322n
```

If safe defaults are implemented:

```bash
python tools/run_official_semantic_patch_application_322n.py
```

## 10. Compile / run checks

Run:

```bash
python -m py_compile datefac\semantic\official_patch_application.py datefac\semantic\official_patch_application_report.py tools\run_official_semantic_patch_application_322n.py
```

Then run the 322N runner.

## 11. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 322N files and official target asset files that were intentionally modified.

Example source additions:

```bash
git add datefac/semantic/official_patch_application.py
git add datefac/semantic/official_patch_application_report.py
git add tools/run_official_semantic_patch_application_322n.py
```

Example official assets, only if actually and intentionally modified:

```bash
git add data/mapping/formal_scope_rules.json
git add data/overrides/02B_ai_repair_override.xlsx
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Apply 322N official semantic patch
```

Push to main only after successful checks and after confirming git status contains only intended 322N source files plus intended official semantic assets.

## 12. Final report expected from Codex

After completion, report:

1. Modified files.
2. Official assets modified.
3. Commands run.
4. 322N output directory.
5. Applied / idempotent operation counts.
6. Alias operation count.
7. Scope operation count.
8. Conflict count.
9. qa_fail_count.
10. decision.
11. Before / after snapshot paths.
12. Rollback artifact paths.
13. git status result.
14. commit hash.
15. push result.
