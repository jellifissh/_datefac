# 346A Vision-Assisted Table Evidence Pilot

## Goal

Implement `346A Vision-Assisted Table Evidence Pilot`.

Current context:

- 345A built the full structured data inventory.
- 345B audited extraction quality across the full inventory.
- 345C measured baseline metric normalization coverage.
- 345C11 completed the reviewed alias simulation branch and recommended returning to 345D.
- 345D generated the full structured demo export package.
- 345E reviewed the 345D demo package and confirmed it is safe for demo-only presentation.
- 345F generated narrative/report assets from 345D and 345E.

345D result:

- `decision = FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY`
- `qa_fail_count = 0`
- `demo_export_row_count = 109`
- `quality_limited_row_count = 5558`
- `excluded_row_count = 9121`
- `inventory_row_count = 14788`
- row count closure: `109 + 5558 + 9121 = 14788`
- `coverage_ratio_before_alias_simulation = 0.452461`
- `coverage_ratio_after_alias_simulation = 0.684136`
- `baseline_normalized_demo_row_count = 109`
- `alias_simulated_demo_row_count = 1532`
- `remaining_unnormalized_raw_metric_name_count = 96`
- `remaining_unnormalized_metric_row_count = 4671`
- `high_severity_issue_count = 7595`
- `medium_severity_issue_count = 7084`
- `missing_unit_count = 838`
- `missing_period_count = 0`
- `missing_source_trace_count = 0`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `formal_export_generated = false`
- `demo_export_only = true`
- all formal/client/production gates remain false

345E result:

- `decision = DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_READY`
- `qa_fail_count = 0`
- `checked_artifact_count = 18`
- `missing_required_artifact_count = 0`
- `artifact_read_error_count = 0`
- `row_count_closure_passed = true`
- `gate_safety_check_passed = true`
- `caveat_completeness_passed = true`
- `presentation_ready_for_demo_only = true`
- all formal/client/production gates remain false

345F result:

- `decision = DEMO_NARRATIVE_REPORT_PACKAGE_345F_READY`
- `qa_fail_count = 0`
- `generated_report_count = 10`
- `sample_rows_for_story_count = 10`
- all formal/client/production gates remain false

346A starts a new technical branch: using MinerU table images as bounded visual evidence, not just audit screenshots. The goal is not to run a costly full visual extraction. The goal is to bind existing structured rows to table/page image evidence, select a small high-value pilot set from quality-limited rows, and generate a deterministic VLM request package for future vision-assisted repair.

346A answers:

> Which quality-limited rows are good candidates for vision-assisted repair, which MinerU image evidence can be bound to them, what exact fields should a vision model inspect, and what request package would be safe to run later without mutating upstream data?

This is an evidence-bundle and VLM-request-package task. It does **not** call a live VLM by default. If a pilot package accidentally becomes a full paid VLM sweep, congratulations, the cost center has discovered fire and is now worshipping it.

---

## Design principle

Use a `text-first, vision-on-demand` workflow:

1. Treat MinerU JSON/MD and 345D structured rows as the primary text source.
2. Treat MinerU table/page images as visual evidence for low-confidence fields.
3. Select only bounded high-value quality-limited rows for the pilot.
4. Generate strict VLM requests for specific fields such as unit, period/header alignment, source trace, and suspicious values.
5. Do not let VLM output overwrite source rows.
6. Route conflicts or low-confidence suggestions to future human review.

346A must not run live VLM inference. It only prepares the evidence and request package. A later explicitly approved task may run VLM calls and ingest responses.

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Add a concise 346A entry after successful implementation and validation.

The ledger entry should include:

- task id: `346A`
- decision: `VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY`
- input packages: 345D and 345E dirs, plus optional MinerU evidence dirs
- output package: 346A output dir
- selected pilot row count
- evidence bundle count
- image-bound / image-missing counts
- generated VLM request count
- live VLM call count: `0`
- target field distribution
- no-write-back confirmation
- gate status: all false
- validation commands and results
- next recommended step

If the ledger has unrelated dirty changes, do not overwrite them blindly. Append only the 346A entry. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/346A_vision_assisted_table_evidence_pilot.md`

Inspect only runner input dirs, optional MinerU evidence dirs supplied by CLI, and the milestone ledger. Do not scan the whole repo.

---

## Runner inputs

Support:

```powershell
--full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d
--demo-export-review-qa-checklist-345e-dir D:\_datefac\output\demo_export_review_qa_checklist_345e
--output-dir D:\_datefac\output\vision_assisted_table_evidence_pilot_346a
```

Optional evidence inputs:

```powershell
--mineru-json-md-dir <path-to-mineru-json-md-output-dir>
--mineru-table-image-dir <path-to-mineru-table-crop-image-dir>
--mineru-page-image-dir <path-to-mineru-page-image-dir>
--table-image-manifest <path-to-image-manifest-json-or-csv>
--max-pilot-rows 100
--max-context-rows-per-request 5
```

Default behavior:

- use 345D quality-limited rows as the candidate pool;
- bind image evidence when image paths or table/page identifiers can be resolved from supplied evidence dirs or manifests;
- if image evidence cannot be resolved, record image-missing status instead of failing the whole task;
- generate VLM request JSONL only for image-bound evidence bundles;
- produce no live VLM calls;
- do not modify 345D, 345E, MinerU outputs, or upstream data.

If 345D or 345E manifest is missing, fail clearly. If no image evidence is provided, still produce candidate selection, unresolved evidence status, prompt templates, and a clear next-plan note that image path binding is required before running a live VLM pilot.

---

## Inputs to read

From 345D:

- `full_structured_demo_export_package_345d_manifest.json`
- `full_structured_demo_export_package_345d_quality_limited_rows.json` or `.csv`
- `full_structured_demo_export_package_345d_demo_rows.json` or `.csv` for schema reference if useful
- `full_structured_demo_export_package_345d_excluded_rows.json` or `.csv` only if useful for negative samples
- `full_structured_demo_export_package_345d_quality_caveats.json` or `.md`
- `full_structured_demo_export_package_345d_alias_simulation_sidecar.json` or `.csv` if useful
- `full_structured_demo_export_package_345d_artifact_index.md`

From 345E:

- `demo_export_review_qa_checklist_345e_manifest.json`
- `demo_export_review_qa_checklist_345e_sample_demo_rows.json` or `.csv`
- `demo_export_review_qa_checklist_345e_quality_limited_sample_rows.json` or `.csv`
- `demo_export_review_qa_checklist_345e_caveat_completeness_check.json`
- `demo_export_review_qa_checklist_345e_demo_presentation_readiness.json`

From optional MinerU evidence dirs/manifests:

- MinerU JSON files if present
- MinerU Markdown files if present
- table crop images if present
- page images if present
- image manifest if present

Validate that:

- 345D decision is `FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY`
- 345D `qa_fail_count = 0`
- 345D `demo_export_only = true`
- 345D `formal_export_generated = false`
- 345E decision is `DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_READY`
- 345E `qa_fail_count = 0`
- 345E `gate_safety_check_passed = true`
- 345E `caveat_completeness_passed = true`
- 345E `presentation_ready_for_demo_only = true`
- official rules/assets modified flags are false
- all formal/client/production gates are false

---

## Outputs

Write only under:

```text
D:\_datefac\output\vision_assisted_table_evidence_pilot_346a
```

Generate:

- `vision_assisted_table_evidence_pilot_346a_manifest.json`
- `vision_assisted_table_evidence_pilot_346a_candidate_pool.json`
- `vision_assisted_table_evidence_pilot_346a_candidate_pool.csv`
- `vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.json`
- `vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.csv`
- `vision_assisted_table_evidence_pilot_346a_evidence_bundle_index.json`
- `vision_assisted_table_evidence_pilot_346a_evidence_bundle_index.csv`
- `vision_assisted_table_evidence_pilot_346a_image_resolution_status.json`
- `vision_assisted_table_evidence_pilot_346a_image_resolution_status.csv`
- `vision_assisted_table_evidence_pilot_346a_field_repair_targets.json`
- `vision_assisted_table_evidence_pilot_346a_field_repair_targets.csv`
- `vision_assisted_table_evidence_pilot_346a_vlm_request_package.jsonl`
- `vision_assisted_table_evidence_pilot_346a_vlm_request_package_preview.json`
- `vision_assisted_table_evidence_pilot_346a_vlm_output_schema.json`
- `vision_assisted_table_evidence_pilot_346a_vlm_prompt_templates.md`
- `vision_assisted_table_evidence_pilot_346a_conflict_handling_policy.md`
- `vision_assisted_table_evidence_pilot_346a_cost_latency_estimate.json`
- `vision_assisted_table_evidence_pilot_346a_executive_summary.md`
- `vision_assisted_table_evidence_pilot_346a_artifact_index.md`
- `vision_assisted_table_evidence_pilot_346a_next_plan.md`

Do not write back into 345F, 345E, 345D, 345C11, 345C10, 345C9, 345C8, 345C7, 345C6, 345C5, 345C4, 345C2, 345C, 345B, 345A, MinerU outputs, official rules, alias assets, input dirs, reviewed workbooks, or upstream outputs.

Do not copy image binaries into git-tracked source paths. Output JSON/CSV may store image paths and metadata; avoid duplicating large image files unless already inside the output dir as explicitly generated small thumbnails. Default should not copy images.

---

## Candidate selection logic

Candidate pool comes from 345D `quality_limited_rows`.

Prioritize rows that are:

- normalized or alias-simulated enough to be useful;
- blocked from strict demo-ready mainly by fixable visual evidence issues;
- missing or uncertain unit;
- uncertain period/header alignment;
- suspicious row/column alignment;
- suspicious value cell;
- missing or weak source trace but has page/table identifiers;
- high-impact or repeated metric names;
- diverse across source PDFs/pages/tables to avoid overfitting the pilot.

De-prioritize rows that are:

- completely unnormalized remaining blind spots;
- missing all core fields;
- excluded for non-visual reasons that VLM cannot reasonably fix;
- low-value duplicate rows beyond the diversity cap.

Select up to `--max-pilot-rows` rows. Default max is 100.

Each selected row should have:

- `pilot_row_id`
- `source_row_id`
- `source_pdf_name`
- `source_page`
- `source_table_id`
- `raw_metric_name`
- `demo_normalized_metric_name`
- `value`
- `unit`
- `period`
- `quality_severity`
- `quality_issue_codes`
- `demo_export_caveats`
- `target_field_types`
- `vision_task_type`
- `selection_reason`
- `requires_image_evidence`
- `image_bound`
- `image_resolution_status`

---

## Image evidence binding

Bind image evidence using the most reliable available keys:

1. explicit image path in row or manifest;
2. source PDF name + page + table id;
3. page image path + bbox if available;
4. table crop image filename patterns that include PDF/page/table identifiers;
5. unresolved if no deterministic match exists.

Do not fuzzy-match aggressively. If binding is uncertain, record `AMBIGUOUS_IMAGE_CANDIDATE` and do not generate a live-ready VLM request for that row.

Image resolution status values:

- `BOUND_TABLE_CROP_IMAGE`
- `BOUND_PAGE_IMAGE_WITH_BBOX`
- `BOUND_PAGE_IMAGE_NO_BBOX`
- `IMAGE_MANIFEST_MATCH`
- `NO_IMAGE_EVIDENCE_PROVIDED`
- `NO_MATCH_FOUND`
- `AMBIGUOUS_IMAGE_CANDIDATE`
- `READ_ERROR`

---

## VLM request package

Generate JSONL requests only for rows/evidence bundles with usable image evidence.

Each request must include:

- `request_id`
- `pilot_row_id`
- `source_row_id`
- `source_pdf_name`
- `source_page`
- `source_table_id`
- `image_path`
- `image_evidence_type`
- `mineru_json_or_md_context` when available and small enough
- `structured_row_before_vision`
- `neighbor_context_rows` bounded by `--max-context-rows-per-request`
- `target_field_types`
- `question_list`
- `strict_output_schema_ref`
- `do_not_overwrite_source_data = true`
- `live_vlm_call_allowed = false`

Do not include raw base64 images in JSONL. Store paths only.

Request questions should be narrow, such as:

- confirm or infer the table-level unit;
- confirm the period/header for a specific value column;
- check whether a value cell appears aligned with the given metric row and period column;
- identify if the row is likely a metric row, header row, subtotal row, or footnote;
- report uncertainty and visual evidence, without inventing missing values.

---

## VLM output schema

Generate a strict schema for future VLM responses:

```json
{
  "request_id": "string",
  "source_row_id": "string",
  "vision_decision": "CONFIRM_EXISTING | SUGGEST_FIELD_REPAIR | FLAG_CONFLICT | INSUFFICIENT_VISUAL_EVIDENCE | NOT_A_DATA_ROW",
  "field_suggestions": [
    {
      "field_name": "unit | period | value | raw_metric_name | source_trace | row_type | table_header",
      "existing_value": "string|null",
      "suggested_value": "string|null",
      "confidence": "HIGH | MEDIUM | LOW",
      "visual_evidence_note": "string",
      "requires_human_review": true
    }
  ],
  "overall_confidence": "HIGH | MEDIUM | LOW",
  "conflict_reason": "string|null",
  "do_not_auto_apply": true
}
```

Future ingestion must treat VLM output as suggestions, not authoritative writes.

---

## Cost and latency estimate

346A must estimate the pilot cost/latency without calling VLM.

Include:

- `vlm_request_count`
- `image_bound_request_count`
- `estimated_images_per_request`
- `estimated_text_context_tokens_per_request`
- `estimated_total_requests`
- `cost_estimate_note`
- `latency_estimate_note`
- `recommended_batch_size`
- `recommended_cache_key_fields`

Do not invent vendor prices. Use qualitative tiers unless explicit pricing config exists in the project.

Recommended cache key fields:

- source PDF hash/path
- page
- table id
- image file path/hash if available
- structured row hash
- target field list
- prompt template version

---

## Manifest metrics

Manifest must include:

- `decision = VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY`
- `input_stage = POST_345F_VISION_ASSISTED_TABLE_EVIDENCE_PILOT`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_345d_decision`
- `input_345e_decision`
- `quality_limited_row_count`
- `candidate_pool_row_count`
- `selected_pilot_row_count`
- `evidence_bundle_count`
- `image_bound_count`
- `image_missing_count`
- `ambiguous_image_candidate_count`
- `vlm_request_count`
- `live_vlm_call_count = 0`
- `vlm_response_count = 0`
- `unit_repair_target_count`
- `period_repair_target_count`
- `value_alignment_check_target_count`
- `source_trace_check_target_count`
- `header_structure_check_target_count`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `formal_export_generated = false`
- `demo_export_only = true`
- `vision_assisted_data_source_strategy = TEXT_FIRST_VISION_ON_DEMAND`
- `vlm_request_package_only = true`
- `upstream_data_mutated = false`
- `milestone_ledger_updated`

All formal/client/production gates must remain false.

If 345D/345E are valid but no image evidence is supplied, keep decision READY and set `vlm_request_count = 0`, with `image_missing_count = selected_pilot_row_count` and a next-plan note requiring image-path binding. If a required 345D/345E input is invalid, fail QA.

---

## Reports

Executive summary must explain:

- why images are now treated as bounded visual evidence instead of only audit screenshots;
- why 346A does not run live VLM calls;
- candidate selection from quality-limited rows;
- image binding success/failure;
- generated VLM request package status;
- target fields for potential repair;
- cost/latency considerations;
- conflict handling and human review boundary;
- why upstream data, official rules/assets, and gates remain unchanged;
- recommended next step.

Next plan must recommend one of:

- `346A2 MinerU Image Path Binding Fix` if image evidence is missing or unresolved;
- `346C Vision-Assisted Repair Response Ingestion` only after an explicitly approved live VLM run exists;
- `346D Vision-Assisted Quality-Limited Row Recovery Simulation` after VLM responses are ingested;
- `345G Demo Presentation Slide Outline` if the project should return to presentation work;
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists.

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/346A_vision_assisted_table_evidence_pilot.md`
- `datefac/benchmark/vision_assisted_table_evidence_pilot_346a.py`
- `datefac/benchmark/vision_assisted_table_evidence_pilot_346a_report.py`
- `tools/run_vision_assisted_table_evidence_pilot_346a.py`
- `tests/benchmark/test_vision_assisted_table_evidence_pilot_346a.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

The milestone ledger update is required for this task.

---

## Forbidden

Do not:

- call live VLM/LLM APIs
- create a new production export dataset
- modify normalization rules
- modify official alias assets
- apply alias decisions to upstream data
- modify 345F, 345E, 345D, or prior outputs
- modify MinerU outputs
- rerun MinerU
- scan the repo
- add dependencies
- modify `datefac/llm/`
- modify production pipeline/parser/extraction/delivery/formal export logic
- generate formal client delivery artifacts
- modify reviewed workbooks
- modify previous LLM response dirs
- modify `input/`, `temp/`, or existing `output/` content
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

---

## Validation

Run:

```powershell
python -m py_compile datefac\benchmark\vision_assisted_table_evidence_pilot_346a.py datefac\benchmark\vision_assisted_table_evidence_pilot_346a_report.py tools\run_vision_assisted_table_evidence_pilot_346a.py tests\benchmark\test_vision_assisted_table_evidence_pilot_346a.py
python -m pytest tests\benchmark\test_vision_assisted_table_evidence_pilot_346a.py -q
python tools\run_vision_assisted_table_evidence_pilot_346a.py --full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d --demo-export-review-qa-checklist-345e-dir D:\_datefac\output\demo_export_review_qa_checklist_345e --output-dir D:\_datefac\output\vision_assisted_table_evidence_pilot_346a
```

If local MinerU evidence dirs are available, also run a real evidence-binding smoke test, for example:

```powershell
python tools\run_vision_assisted_table_evidence_pilot_346a.py --full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d --demo-export-review-qa-checklist-345e-dir D:\_datefac\output\demo_export_review_qa_checklist_345e --mineru-json-md-dir <MINERU_JSON_MD_DIR> --mineru-table-image-dir <MINERU_TABLE_IMAGE_DIR> --mineru-page-image-dir <MINERU_PAGE_IMAGE_DIR> --output-dir D:\_datefac\output\vision_assisted_table_evidence_pilot_346a
```

Tests must verify:

- outputs exist
- decision is ready for valid 345D/345E fixtures
- QA is zero for valid fixtures
- candidate pool is selected from quality-limited rows
- selected pilot rows are bounded by max pilot rows
- image resolution statuses are generated
- VLM request JSONL is generated only for image-bound rows
- no live VLM calls occur
- VLM output schema is generated
- cost/latency estimate is generated without vendor-price invention
- official rules/assets modified flags remain false
- formal export generated flag remains false
- demo export only flag remains true
- all formal/client/production gates remain false
- milestone ledger is updated with a 346A entry
- no input write-back occurs
- missing/invalid required 345D/345E inputs fail clearly

---

## Completion report

Report:

1. Files changed.
2. Milestone ledger update summary.
3. py_compile result.
4. pytest result.
5. real runner result.
6. optional MinerU evidence-binding smoke result, if run.
7. output dir.
8. decision and QA metrics.
9. candidate pool / selected pilot row counts.
10. evidence bundle / image-bound / image-missing / ambiguous counts.
11. VLM request count and live VLM call count.
12. target field distribution.
13. cost/latency estimate summary.
14. conflict-handling policy status.
15. official rules/assets modified flags.
16. formal export generated / demo export only flags.
17. final gate status.
18. first file to open.
19. next recommended step.
20. `git status -sb`.
21. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/MinerU outputs/protected dirty files.
