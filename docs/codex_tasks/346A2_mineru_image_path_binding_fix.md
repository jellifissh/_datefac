# 346A2 MinerU Image Path Binding Fix

## Goal

Implement `346A2 MinerU Image Path Binding Fix`.

346A completed the first vision-assisted evidence pilot package, but the real runner produced:

```text
selected_pilot_row_count = 100
evidence_bundle_count = 100
image_bound_count = 0
image_missing_count = 100
ambiguous_image_candidate_count = 0
vlm_request_count = 0
live_vlm_call_count = 0
```

This is a valid 346A result, not a failure. It means 346A selected 100 high-value quality-limited rows, but no deterministic MinerU image evidence was provided or bound. A live VLM pilot must not run until image paths are bound.

346A2 fixes the missing evidence-binding layer.

346A2 must answer:

> Given 346A selected pilot rows and local MinerU output directories, can we deterministically bind each pilot row to table crop images, page images, JSON/Markdown context, and optional bbox/page/table evidence without mutating upstream data?

This task is still request-package preparation only. It must not call live VLM/LLM APIs.

---

## Strategic alignment

Follow the repository-root tactical playbook:

```text
DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md
```

Relevant doctrine:

- JSON/Markdown is the structured draft.
- Table/page images are visual evidence.
- Images are evidence, not automatic replacements.
- VLM repair is targeted and suggestion-only.
- Never overwrite source data.
- Quality-limited rows are the current recovery target.
- Excluded rows remain frozen/archive-first.

346A2 is the evidence binding step required before any targeted visual repair can be considered.

---

## Current context

346A output directory:

```text
D:\_datefac\output\vision_assisted_table_evidence_pilot_346a
```

346A selected 100 pilot rows from 345D quality-limited rows.

346A generated, among others:

- `vision_assisted_table_evidence_pilot_346a_manifest.json`
- `vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.json`
- `vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.csv`
- `vision_assisted_table_evidence_pilot_346a_evidence_bundle_index.json`
- `vision_assisted_table_evidence_pilot_346a_image_resolution_status.json`
- `vision_assisted_table_evidence_pilot_346a_field_repair_targets.json`
- `vision_assisted_table_evidence_pilot_346a_vlm_request_package.jsonl`
- `vision_assisted_table_evidence_pilot_346a_vlm_output_schema.json`
- `vision_assisted_table_evidence_pilot_346a_conflict_handling_policy.md`
- `vision_assisted_table_evidence_pilot_346a_next_plan.md`

346A next plan recommended:

```text
346A2 MinerU Image Path Binding Fix
```

Reason:

```text
No deterministic image evidence was bound, so a live VLM pilot would be premature.
```

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Append a concise 346A2 entry after successful implementation and validation.

The ledger entry must include:

- task id: `346A2`
- decision: `MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY`
- input 346A output dir
- supplied MinerU evidence dirs/manifests
- output dir
- selected pilot row count
- binding candidate count
- image-bound count
- table-crop-bound count
- page-image-bound count
- json/md-context-bound count
- image-missing count
- ambiguous candidate count
- generated VLM request count
- live VLM call count: `0`
- no-write-back confirmation
- gate status: all false
- next recommended step

If the ledger has unrelated dirty changes, append only the 346A2 entry. Do not overwrite unrelated edits. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/346A2_mineru_image_path_binding_fix.md`

Do not scan the whole repository.

Inspect only:

- 346A output dir
- explicitly supplied MinerU output dirs/manifests
- the milestone ledger
- the root tactical playbook

---

## Runner inputs

Support:

```powershell
--vision-assisted-table-evidence-pilot-346a-dir D:\_datefac\output\vision_assisted_table_evidence_pilot_346a
--output-dir D:\_datefac\output\mineru_image_path_binding_fix_346a2
```

Optional MinerU evidence inputs:

```powershell
--mineru-output-root <path-to-mineru-output-root>
--mineru-json-md-dir <path-to-mineru-json-md-output-dir>
--mineru-table-image-dir <path-to-mineru-table-crop-image-dir>
--mineru-page-image-dir <path-to-mineru-page-image-dir>
--table-image-manifest <path-to-image-manifest-json-or-csv>
--page-image-manifest <path-to-page-image-manifest-json-or-csv>
--max-binding-candidates-per-row 5
--max-context-chars 4000
```

Default behavior:

- read 346A selected pilot rows and evidence bundle index;
- attempt deterministic binding with supplied evidence directories/manifests;
- if no image evidence dirs are supplied, produce a clear READY package with all rows marked `NO_IMAGE_EVIDENCE_PROVIDED`, and recommend providing MinerU output paths;
- generate live-ready VLM request package only for rows with deterministic image binding;
- never call live VLM/LLM APIs;
- never mutate 346A outputs, MinerU outputs, 345D/345E/345F outputs, official rules, or alias assets.

---

## Supported MinerU evidence patterns

346A2 must support flexible but deterministic discovery.

Look for common MinerU output assets under supplied roots:

```text
*.json
*.md
*.markdown
*.png
*.jpg
*.jpeg
*.webp
```

Do not recurse into unrelated repository paths. Only inspect explicitly supplied evidence roots.

Build a local evidence catalog with:

```text
evidence_id
evidence_type = TABLE_CROP_IMAGE | PAGE_IMAGE | JSON_CONTEXT | MD_CONTEXT | MANIFEST_ROW
path
filename
suffix
source_pdf_name_candidate
page_candidate
table_id_candidate
bbox_candidate
hash_or_size_mtime_fingerprint
```

Extract candidates from filenames and manifests using conservative patterns, for example:

```text
page_12
p12
page-12
table_3
table-3
tbl_3
```

Also handle source PDF stem matching when safe:

```text
source_pdf_name -> source_pdf_stem
```

Avoid aggressive fuzzy matching. If multiple plausible images remain for one row, record ambiguity instead of pretending certainty.

---

## Binding strategy

For each 346A pilot row, try binding in this priority order:

1. explicit image path already present in 346A row/evidence bundle;
2. table image manifest match by source PDF + page + table id;
3. page image manifest match by source PDF + page;
4. table crop directory match by source PDF stem + page + table id;
5. page image directory match by source PDF stem + page;
6. JSON/MD context match by source PDF stem + page/table id;
7. unresolved.

Binding statuses:

```text
BOUND_TABLE_CROP_IMAGE
BOUND_PAGE_IMAGE_WITH_BBOX
BOUND_PAGE_IMAGE_NO_BBOX
BOUND_JSON_CONTEXT_ONLY
BOUND_MD_CONTEXT_ONLY
BOUND_TEXT_CONTEXT_ONLY
IMAGE_MANIFEST_MATCH
NO_IMAGE_EVIDENCE_PROVIDED
NO_MATCH_FOUND
AMBIGUOUS_IMAGE_CANDIDATE
READ_ERROR
```

A row is considered `image_bound = true` only when it has a deterministic table crop image or page image binding.

JSON/MD context alone is useful, but it is not image binding.

---

## VLM request regeneration

346A2 must generate a refreshed VLM request package for image-bound rows only.

Each request must include:

```text
request_id
pilot_row_id
source_row_id
source_pdf_name
source_page
source_table_id
image_path
image_evidence_type
bbox if available
mineru_json_or_md_context if available and bounded
structured_row_before_vision
neighbor_context_rows if available
target_field_types
question_list
strict_output_schema_ref
do_not_overwrite_source_data = true
live_vlm_call_allowed = false
```

Do not include raw base64 image content.

Do not send any API request.

If no rows are image-bound, create an empty JSONL and a preview explaining why no live-ready requests were generated.

---

## Outputs

Write only under:

```text
D:\_datefac\output\mineru_image_path_binding_fix_346a2
```

Generate:

- `mineru_image_path_binding_fix_346a2_manifest.json`
- `mineru_image_path_binding_fix_346a2_evidence_catalog.json`
- `mineru_image_path_binding_fix_346a2_evidence_catalog.csv`
- `mineru_image_path_binding_fix_346a2_binding_candidates.json`
- `mineru_image_path_binding_fix_346a2_binding_candidates.csv`
- `mineru_image_path_binding_fix_346a2_bound_rows.json`
- `mineru_image_path_binding_fix_346a2_bound_rows.csv`
- `mineru_image_path_binding_fix_346a2_unresolved_rows.json`
- `mineru_image_path_binding_fix_346a2_unresolved_rows.csv`
- `mineru_image_path_binding_fix_346a2_ambiguous_rows.json`
- `mineru_image_path_binding_fix_346a2_ambiguous_rows.csv`
- `mineru_image_path_binding_fix_346a2_image_resolution_status.json`
- `mineru_image_path_binding_fix_346a2_image_resolution_status.csv`
- `mineru_image_path_binding_fix_346a2_json_md_context_index.json`
- `mineru_image_path_binding_fix_346a2_json_md_context_index.csv`
- `mineru_image_path_binding_fix_346a2_vlm_request_package.jsonl`
- `mineru_image_path_binding_fix_346a2_vlm_request_package_preview.json`
- `mineru_image_path_binding_fix_346a2_binding_summary.json`
- `mineru_image_path_binding_fix_346a2_executive_summary.md`
- `mineru_image_path_binding_fix_346a2_artifact_index.md`
- `mineru_image_path_binding_fix_346a2_next_plan.md`

Do not copy large image binaries into the output directory by default. Store paths and metadata.

---

## Manifest metrics

Manifest must include:

```text
decision = MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY
input_stage = POST_346A_MINERU_IMAGE_PATH_BINDING_FIX
qa_fail_count = 0
no_write_back_proof_passed = true
formal_client_export_allowed = false
client_ready = false
production_ready = false
global_strict_human_review_completed = false
input_346a_decision = VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY
input_346a_qa_fail_count = 0
selected_pilot_row_count
input_346a_image_bound_count
input_346a_image_missing_count
binding_candidate_count
evidence_catalog_count
table_crop_image_catalog_count
page_image_catalog_count
json_context_catalog_count
md_context_catalog_count
bound_row_count
image_bound_count
table_crop_bound_count
page_image_bound_count
json_md_context_bound_count
image_missing_count
ambiguous_image_candidate_count
vlm_request_count
live_vlm_call_count = 0
vlm_response_count = 0
official_rules_modified = false
official_alias_assets_modified = false
formal_export_generated = false
demo_export_only = true
vlm_request_package_only = true
upstream_data_mutated = false
milestone_ledger_updated
```

If no evidence dirs are supplied, still produce READY with:

```text
bound_row_count = 0
image_bound_count = 0
image_missing_count = selected_pilot_row_count
vlm_request_count = 0
```

and next recommended step should clearly ask for the correct MinerU output roots.

---

## Reports

Executive summary must explain:

- why 346A2 exists after 346A;
- what evidence roots/manifests were supplied;
- how the evidence catalog was built;
- binding success/failure counts;
- table crop vs page image vs JSON/MD context binding counts;
- why no live VLM calls were made;
- whether a live-ready request package exists;
- what remains unresolved;
- next recommended step.

Next plan must recommend one of:

- `346A2R Provide MinerU Evidence Roots` if no evidence directories were supplied;
- `346A3 Binding Rule Refinement` if many ambiguous or unresolved rows remain despite evidence dirs;
- `346B Quality-Limited Row Recovery Pilot` if enough evidence is bound to continue deterministic recovery;
- `346C Vision-Assisted Repair Response Ingestion` only after an explicitly approved live VLM run exists;
- `345G Demo Presentation Slide Outline` if the project returns to presentation work;
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/346A2_mineru_image_path_binding_fix.md`
- `datefac/benchmark/mineru_image_path_binding_fix_346a2.py`
- `datefac/benchmark/mineru_image_path_binding_fix_346a2_report.py`
- `tools/run_mineru_image_path_binding_fix_346a2.py`
- `tests/benchmark/test_mineru_image_path_binding_fix_346a2.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

The milestone ledger update is required.

---

## Forbidden

Do not:

- call live VLM/LLM APIs
- copy large images into git-tracked paths
- mutate 346A outputs
- mutate MinerU outputs
- mutate 345D/345E/345F outputs
- modify normalization rules
- modify official alias assets
- modify production pipeline/parser/extraction/delivery/formal export logic
- generate formal client delivery artifacts
- modify reviewed workbooks
- modify previous LLM response dirs
- modify `input/`, `temp/`, or existing `output/` content except the new 346A2 output dir
- auto commit/push/merge
- use `git add -A`, `git add .`, `git reset --hard`, or `git checkout --`

Do not touch protected dirty files:

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`
- `tools/mineru_new_runner.cmd`

---

## Validation

Run the no-evidence baseline:

```powershell
python -m py_compile datefac\benchmark\mineru_image_path_binding_fix_346a2.py datefac\benchmark\mineru_image_path_binding_fix_346a2_report.py tools\run_mineru_image_path_binding_fix_346a2.py tests\benchmark\test_mineru_image_path_binding_fix_346a2.py
python -m pytest tests\benchmark\test_mineru_image_path_binding_fix_346a2.py -q
python tools\run_mineru_image_path_binding_fix_346a2.py --vision-assisted-table-evidence-pilot-346a-dir D:\_datefac\output\vision_assisted_table_evidence_pilot_346a --output-dir D:\_datefac\output\mineru_image_path_binding_fix_346a2
```

If local MinerU evidence dirs are known, also run evidence binding smoke:

```powershell
python tools\run_mineru_image_path_binding_fix_346a2.py --vision-assisted-table-evidence-pilot-346a-dir D:\_datefac\output\vision_assisted_table_evidence_pilot_346a --mineru-output-root <MINERU_OUTPUT_ROOT> --mineru-json-md-dir <MINERU_JSON_MD_DIR> --mineru-table-image-dir <MINERU_TABLE_IMAGE_DIR> --mineru-page-image-dir <MINERU_PAGE_IMAGE_DIR> --output-dir D:\_datefac\output\mineru_image_path_binding_fix_346a2
```

Tests must verify:

- outputs exist;
- valid 346A input produces READY;
- no-evidence baseline produces image_missing_count equal to selected pilot row count;
- supplied fixture image dirs produce deterministic image-bound rows;
- ambiguous candidates are not treated as image-bound;
- JSON/MD context binding alone does not count as image-bound;
- VLM JSONL is generated only for image-bound rows;
- live VLM call count is always 0;
- source 346A outputs are not mutated;
- official rules/assets flags remain false;
- formal/client/production gates remain false;
- milestone ledger is updated with 346A2 entry.

---

## Completion report

Report:

1. Files changed.
2. Milestone ledger update summary.
3. py_compile result.
4. pytest result.
5. no-evidence baseline runner result.
6. evidence-binding smoke result if MinerU evidence dirs were supplied.
7. output dir.
8. decision and QA metrics.
9. selected pilot row count.
10. evidence catalog counts.
11. bound / missing / ambiguous counts.
12. table crop / page image / JSON/MD context binding counts.
13. VLM request count and live VLM call count.
14. whether VLM request package is live-ready.
15. official rules/assets modified flags.
16. formal export generated / demo export only flags.
17. final gate status.
18. first file to open.
19. next recommended step.
20. `git status -sb`.
21. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/MinerU outputs/protected dirty files.
