# DateFac 323L-R Task
## Reviewed Human Approval Validation

## Context

323L human approval package is complete and pushed to remote main.

323L commit:

```text
1f72657cf993f06cd69e57b4e4a2e677fe04dca9
```

323L output dir:

```text
D:\_datefac\output\controlled_official_proposal_human_approval_323l
```

323L result:

```text
approval_record_count = 6
alias_approval_count = 2
scope_approval_count = 4
decision_distribution = {"PENDING_HUMAN_APPROVAL": 6}
qa_fail_count = 0
decision = CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_323L_READY_FOR_HUMAN_REVIEW
```

323L-R is the next step after the human approval workbook is filled.

## Goal

Validate a reviewed 323L human approval workbook and produce a final approved patch operation plan for 323M official patch application.

323L-R is validation only. It must not write official assets and must not apply rules.

## Hard constraints

- Do not modify production pipeline.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 323L approval package and reviewed workbook only.
- Process only the 6 approval records from 323L.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely patch/add 323L-R validation source/runner code if needed.

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

Reviewed workbook:

```text
D:\_datefac\output\controlled_official_proposal_human_approval_323l\controlled_official_proposal_human_approval_323l_workbook.xlsx
```

323L package dir:

```text
D:\_datefac\output\controlled_official_proposal_human_approval_323l
```

Expected source files:

```text
controlled_official_proposal_human_approval_323l_summary.json
controlled_official_proposal_human_approval_323l_qa.json
controlled_official_proposal_human_approval_323l_package.json
controlled_official_proposal_human_approval_323l_workbook.xlsx
```

## Output directory

```text
D:\_datefac\output\controlled_official_proposal_human_approval_323l_reviewed
```

Suggested outputs:

```text
controlled_official_proposal_human_approval_323l_reviewed_summary.json
controlled_official_proposal_human_approval_323l_reviewed_qa.json
controlled_official_proposal_human_approval_323l_final_approved_patch_plan.json
controlled_official_proposal_human_approval_323l_reviewed_workbook.xlsx
controlled_official_proposal_human_approval_323l_rejected_or_needs_more_info.xlsx
controlled_official_proposal_human_approval_323l_no_apply_proof.json
```

## Required behavior

1. Validate 323L prepare readiness.
2. Read reviewed workbook.
3. Validate exactly 6 approval records.
4. Require each decision to be one of:
   - APPROVE
   - REJECT
   - NEEDS_MORE_INFO
5. Require no PENDING_HUMAN_APPROVAL before producing a final approved plan.
6. Build final approved patch plan only from APPROVE rows.
7. Preserve rejected / needs-more-info rows separately.
8. Validate no duplicate approval ids.
9. Validate no approval record was added or removed.
10. Validate target asset/group/provenance/rollback fields are present for approved rows.
11. Confirm official assets were not modified.
12. Confirm no parser, LLM, or rule application occurred.

## Expected if all 6 are approved

```text
approval_record_count = 6
approved_patch_operation_count = 6
alias_approved_patch_operation_count = 2
scope_approved_patch_operation_count = 4
rejected_count = 0
needs_more_info_count = 0
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_323L_REVIEWED_READY_FOR_323M_OFFICIAL_PATCH_APPLICATION
```

## Decision

If reviewed workbook is valid and at least one patch operation is approved:

```text
CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_323L_REVIEWED_READY_FOR_323M_OFFICIAL_PATCH_APPLICATION
```

If valid but no operations are approved:

```text
CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_323L_REVIEWED_NO_APPROVED_PATCH_OPERATIONS
```

If invalid:

```text
CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_323L_REVIEWED_NOT_READY
```

## Suggested command

If validate-reviewed mode is added to the existing runner:

```bash
python tools/run_controlled_official_proposal_human_approval_323l.py \
  --mode validate-reviewed \
  --reviewed-approval-workbook D:\_datefac\output\controlled_official_proposal_human_approval_323l\controlled_official_proposal_human_approval_323l_workbook.xlsx \
  --approval-package-dir D:\_datefac\output\controlled_official_proposal_human_approval_323l \
  --output-dir D:\_datefac\output\controlled_official_proposal_human_approval_323l_reviewed
```

If a separate runner is clearer:

```bash
python tools/run_controlled_official_proposal_human_approval_reviewed_323lr.py \
  --reviewed-approval-workbook D:\_datefac\output\controlled_official_proposal_human_approval_323l\controlled_official_proposal_human_approval_323l_workbook.xlsx \
  --approval-package-dir D:\_datefac\output\controlled_official_proposal_human_approval_323l \
  --output-dir D:\_datefac\output\controlled_official_proposal_human_approval_323l_reviewed
```

## Compile / run checks

Run py_compile for any modified 323L/323L-R source files and runners.

## Git workflow

Use precise adds only. Do not add output files.

Suggested commit message:

```text
Add 323L reviewed human approval validation
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Reviewed workbook path.
4. Output directory.
5. Approval record count.
6. Approved / rejected / needs-more-info / pending / invalid counts.
7. Alias / scope approved counts.
8. Final approved patch plan path.
9. qa_fail_count.
10. decision.
11. Whether official assets were modified.
12. git status result.
13. commit hash.
14. push result.
