# 320E Sandbox Delivery Bundle from Row-Text Mapping

## task_title
Build sandbox delivery bundle from 320D2 trusted/review row-text mapping outputs

## project
D:\_datefac

## current_context
320D2 completed context propagation and trust gate calibration.

Latest 320D2 result:
- pushed branch: main
- commit hash: 0727d18
- source_candidate_count: 100
- context_enriched_candidate_count: 100
- trusted_preview_count: 95
- review_required_preview_count: 5
- rejected_preview_count: 0
- unit_unknown_count: 0
- year_inferred_count: 0
- smoke_verified_candidate_count: 90
- row_text_only_trusted_count: 95
- repaired_trusted_count: 25
- sandbox_mapping_decision: ROW_TEXT_MAPPING_READY_FOR_320E_SANDBOX_INTEGRATION

Interpretation:
- MinerU is validated as primary table/layout asset parser.
- Legacy PPStructure is useful as row-text recognizer, not full grid recognizer.
- 320C4 proved row-text repair can recover high-value cash-flow rows.
- 320D2 proved context propagation can reduce false review burden and produce a meaningful trusted/review split.

Next stage 320E should not modify production files. It should build a sandbox delivery bundle that looks like a real DateFac output package, so the user can inspect what would be delivered to a customer or downstream API.

## goal
Implement 320E sandbox delivery bundle:

320D2 context-enriched candidates
-> trusted core metrics sandbox sheet
-> review-required sandbox queue
-> source provenance
-> confidence/risk audit
-> compact customer-facing preview
-> internal QA report

This stage turns the row-text mapping result into a coherent demo/delivery artifact, but still under sandbox naming.

## non_goals
Do not do these in 320E:
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call LLM/VLM/cloud API/network.
- Do not modify production Excel files.
- Do not apply data into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `docs/codex_tasks/320e_sandbox_delivery_bundle_from_row_text_mapping.md`
- `datefac/delivery/__init__.py`
- `datefac/delivery/sandbox_bundle_builder.py`
- `datefac/delivery/sandbox_delivery_schema.py`
- `tools/run_row_text_sandbox_delivery_bundle_320e.py`

Potentially modify only if necessary:
- `datefac/domain/metric_candidate.py`
- `datefac/governance/row_text_candidate_mapper.py`

Keep delivery logic separate from extraction/governance logic.

## input_contract
Primary input directory:

```powershell
D:\_datefac\output\row_text_mapping_320d2
```

Expected files may include:
- `row_text_mapping_320d2.xlsx`
- `row_text_mapping_320d2_summary.json`
- `row_text_mapping_320d2_report.md`
- optional JSONL files

The CLI should support:

```powershell
python tools/run_row_text_sandbox_delivery_bundle_320e.py ^
  --input-dir D:\_datefac\output\row_text_mapping_320d2 ^
  --output-dir D:\_datefac\output\row_text_delivery_320e
```

If input is missing, generate a clear blocked report:
- `BLOCKED_MISSING_320D2_INPUT`

Do not crash.

## input_loading
Load from 320D2 Excel first.

Expected sheets:
- `context_enriched_candidates`
- `trusted_preview`
- `review_required_preview`
- `rejected_preview`
- `risk_tag_counts`
- `metric_counts`
- `trust_gate_audit`
- `context_propagation_audit`

If some sheets are missing, load available sheets and record warnings.

Preserve original columns. Do not silently discard source fields.

## delivery bundle outputs
Write to:

```powershell
D:\_datefac\output\row_text_delivery_320e
```

Required files:

1. `row_text_delivery_320e.xlsx`

Required sheets:
- `summary`
- `customer_trusted_metrics_preview`
- `customer_review_required_preview`
- `metric_wide_preview`
- `source_provenance`
- `risk_audit`
- `trust_gate_audit`
- `context_audit`
- `qa_checks`
- `delivery_manifest`

2. `row_text_delivery_320e_summary.json`

3. `row_text_delivery_320e_report.md`

Optional:
- `customer_trusted_metrics_preview.jsonl`
- `customer_review_required_preview.jsonl`
- `delivery_manifest.json`

## customer_trusted_metrics_preview
This is a sandbox customer-facing preview of trusted candidates.

Columns:
- source_doc_name
- source_file
- table_name_or_context
- metric_code
- canonical_metric_name
- year
- value
- unit
- currency
- confidence
- source_row_text
- extraction_method
- provenance_id

Rules:
- Include only `trusted_preview` rows from 320D2.
- Keep `extraction_method = mineru_ppstructure_row_text`.
- Preserve source row text for auditability.
- Do not include internal raw risk tags unless in audit sheets.

## customer_review_required_preview
This is the customer/internal review queue preview.

Columns:
- source_doc_name
- source_file
- table_name_or_context
- metric_code
- canonical_metric_name
- year
- raw_value
- normalized_value
- unit
- reason_for_review
- risk_tags
- source_row_text
- suggested_action
- provenance_id

Suggested actions:
- `confirm_value`
- `confirm_unit`
- `confirm_repaired_row`
- `ignore_or_reject`

## metric_wide_preview
Create a human-friendly wide table:

Rows:
- metric_code / canonical_metric_name

Columns:
- 2024
- 2025
- 2026E
- 2027E
- 2028E

Include:
- value
- unit if needed
- trust status if mixed

For multiple values of same metric/year, show warning and do not silently overwrite.

## source_provenance
Every delivered candidate must have a provenance row.

Columns:
- provenance_id
- candidate_id
- source_stage
- source_file
- source_doc_name
- source_table_id
- source_row_index
- source_row_text
- source_image_path if available
- table_asset_id if available
- recognizer_name
- smoke_check_status
- year_source
- unit_source
- mapping_decision
- split_reason

## qa_checks
Include explicit QA checks:
- no rejected rows in customer trusted preview
- no invalid years
- no unknown metric codes in trusted preview
- no unit unknown in trusted preview
- no duplicate metric/year in trusted preview
- trusted count matches source trusted_preview count
- review count matches source review_required_preview count
- smoke verified rows count matches or is explained

Each QA check should have:
- check_name
- status: PASS/WARN/FAIL
- detail

## delivery_manifest
Include:
- bundle_name
- created_at
- source_input_dir
- output_dir
- source_candidate_count
- trusted_delivery_count
- review_required_delivery_count
- rejected_source_count
- unique_metric_count
- unique_year_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- delivery_decision

## summary_metrics
Include:
- source_candidate_count
- trusted_delivery_count
- review_required_delivery_count
- rejected_source_count
- unique_metric_count
- unique_year_count
- metric_wide_row_count
- provenance_row_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- delivery_decision

Decision rule:
- If qa_fail_count > 0:
  `SANDBOX_DELIVERY_BLOCKED_BY_QA_FAILURE`
- If trusted_delivery_count >= 50 and review_required_delivery_count <= 10 and qa_fail_count == 0:
  `SANDBOX_DELIVERY_READY_FOR_320F_MULTI_REPORT_BENCHMARK`
- If trusted_delivery_count > 0 and qa_fail_count == 0:
  `SANDBOX_DELIVERY_USABLE_NEEDS_MORE_BENCHMARK`
- Otherwise:
  `SANDBOX_DELIVERY_NOT_READY`

## important_design_constraint
Do not make this only for cash-flow rows. The builder should work with any 320D2 candidate rows, but the current sample is cash-flow-heavy.

Use generic metric/year/value/provenance schema. Cash-flow-specific logic should not leak into delivery formatting except through canonical metric names.

## validation
Run:

```powershell
python -m py_compile datefac/delivery/sandbox_bundle_builder.py
python -m py_compile datefac/delivery/sandbox_delivery_schema.py
python -m py_compile tools/run_row_text_sandbox_delivery_bundle_320e.py
```

Then run:

```powershell
python tools/run_row_text_sandbox_delivery_bundle_320e.py ^
  --input-dir D:\_datefac\output\row_text_mapping_320d2 ^
  --output-dir D:\_datefac\output\row_text_delivery_320e
```

If input dir is missing, output blocked report but keep compile clean.

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run PaddleOCR/PPStructure.
3. Do not call cloud APIs, LLMs, VLMs, or network endpoints.
4. Do not modify production delivery files:
   - `01_自动可信核心指标.xlsx`
   - `02_人工复核指标队列.xlsx`
   - `02A_人工年份修正覆盖表.xlsx`
   - `05_核心财务指标标准化.xlsx`
   - `06_最终核心财务指标.xlsx`
5. Do not modify:
   - `data/overrides/02B_ai_repair_override.xlsx`
   - `data/mapping/formal_scope_rules.json`
6. Do not run `factory_core.py`.
7. Do not rewrite old Stage7 pipeline.
8. Do not commit `output/` artifacts.
9. Do not commit anything under `E:\mineru_lab`.
10. Preserve Chinese text as UTF-8. No `????` or replacement characters.

## commit_requirements
After implementation:
1. `git status`
2. only add 320E code and this task document;
3. do not add `output/`;
4. do not add `E:\mineru_lab`;
5. do not add unrelated untracked files such as:
   - `fix_307e_reviewed_at.py`
   - `tools/run_stage7a_5pdf_regression_sandbox.py`
   - `tools/update_stage5v_production_06_safe_rows.py`
6. commit message:
   `Build row text sandbox delivery bundle`
7. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- source_candidate_count
- trusted_delivery_count
- review_required_delivery_count
- rejected_source_count
- unique_metric_count
- unique_year_count
- provenance_row_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- delivery_decision
- skipped/untracked files
