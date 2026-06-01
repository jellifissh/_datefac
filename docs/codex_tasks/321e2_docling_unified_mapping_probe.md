# 321E2 Docling Unified Mapping Probe

## task_title
Convert audited Docling table grids into DateFac Unified Tables and MetricCandidate sandbox output

## project
D:\_datefac

## current_context
321E1 Docling output audit completed and pushed to `main`.

321E1 output directory:

```powershell
D:\_datefac\output\docling_output_audit_321e1
```

Docling raw output directory:

```powershell
E:\mineru_lab\benchmarks\table_extraction_321e\outputs\docling
```

Benchmark input images:

```powershell
E:\mineru_lab\benchmarks\table_extraction_321e\input_images
```

321E1 key results:
- input_image_count: 10
- discovered_docling_folder_count: 10
- discovered_json_file_count: 11
- matched_image_count: 10
- json_parse_success_count: 11
- total_table_count: 11
- image_with_table_count: 10
- image_with_real_cell_grid_count: 10
- total_cell_count: 1256
- overall_empty_cell_rate: 0.0
- numeric_parse_success_rate: 1.0
- valid_year_header_count: 57
- invalid_year_header_count: 15
- comma_space_number_count: 108
- possible_missing_value_count: 56
- good_candidate_count: 10
- partial_review_needed_count: 0
- poor_or_text_only_count: 0
- qa_pass_count: 8
- qa_warn_count: 0
- qa_fail_count: 0
- docling_audit_decision: DOCLING_READY_FOR_321E_TOOL_BAKEOFF

Engineering interpretation:
- Docling is good enough to enter the table extraction bakeoff.
- But 321E1 only audited grid quality. It did not test whether Docling output can become DateFac MetricCandidate rows.
- The next step is a sandbox-only Docling -> Unified Table -> MetricCandidate mapping probe.
- Do not continue 321D2 MinerU normalizer expansion yet.
- Do not claim Docling is better than MinerU until MetricCandidate usefulness is measured.

## goal
Implement 321E2 to consume Docling audited table grids and test whether they can be normalized into DateFac Unified Tables and mapped into MetricCandidate previews.

Pipeline:

```text
Docling JSON/cells
+ 321E1 audit result
-> Unified Table JSON
-> DateFac MetricCandidate
-> trusted / review_required / rejected preview
-> comparison summary vs MinerU body 321D and pure VLM 321B2
```

321E2 should answer:
1. Can Docling cell grids be converted into useful DateFac table rows?
2. Does Docling reduce invalid year / unknown metric / missing value problems compared with MinerU body 321D?
3. Does Docling improve trusted rate compared with pure VLM 321B2 and PPStructure 320G?
4. Which Docling outputs need manual review due possible missing cells or bad headers?
5. Should Docling remain in 321E full tool bakeoff after StructTable/InternVL2 finishes downloading?

This is sandbox-only.

## non_goals
Do not do these in 321E2:
- Do not run Docling again.
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call VLM/API/cloud/network.
- Do not modify E:\mineru_lab.
- Do not modify production delivery files.
- Do not apply data into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not continue 321D2 normalizer rule expansion.
- Do not claim production readiness.

## expected_new_or_modified_files
Likely new/modified files:
- `datefac/table_bakeoff/docling_unified_mapper.py`
- `datefac/table_bakeoff/docling_metric_probe.py`
- `datefac/table_bakeoff/tool_comparison_summary.py`
- `tools/run_docling_unified_mapping_probe_321e2.py`
- `docs/codex_tasks/321e2_docling_unified_mapping_probe.md`

Reuse where safe:
- `datefac/table_bakeoff/docling_output_reader.py`
- `datefac/table_bakeoff/docling_table_normalizer.py`
- `datefac/table_bakeoff/docling_output_audit.py`
- existing domain MetricCandidate classes
- safe alias/unit/year utilities if already separated cleanly

Keep this in `datefac/table_bakeoff`. Do not mix it into MinerU-body, VLM, PPStructure, or production pipeline modules.

## input_contract
Primary inputs:

```powershell
D:\_datefac\output\docling_output_audit_321e1
E:\mineru_lab\benchmarks\table_extraction_321e\outputs\docling
E:\mineru_lab\benchmarks\table_extraction_321e\input_images
```

Optional comparison inputs:

```powershell
D:\_datefac\output\mineru_table_body_ingestion_321d
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
D:\_datefac\output\batch_row_text_delivery_320g
```

CLI:

```powershell
python tools/run_docling_unified_mapping_probe_321e2.py ^
  --docling-audit-dir D:\_datefac\output\docling_output_audit_321e1 ^
  --docling-output-dir E:\mineru_lab\benchmarks\table_extraction_321e\outputs\docling ^
  --input-image-dir E:\mineru_lab\benchmarks\table_extraction_321e\input_images ^
  --mineru-body-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\docling_unified_mapping_321e2
```

If optional comparison dirs are missing, continue with warnings.
If the 321E1 audit dir is missing, output blocked decision:
- `BLOCKED_MISSING_321E1_AUDIT_DIR`

## unified_table_requirements
Convert Docling cells into Unified Table JSON:

```json
{
  "tool": "docling",
  "recognition_source": "DOCLING_TABLE_GRID",
  "image_name": "",
  "table_id": "",
  "table_title": "",
  "unit": "",
  "columns": ["2024A", "2025A", "2026E"],
  "rows": [
    {
      "row_index": 1,
      "metric_name_raw": "营业收入",
      "metric_name_cn": "营业收入",
      "values": [
        {
          "column": "2024A",
          "raw_value": "1,234",
          "normalized_value": 1234
        }
      ],
      "source_cells": [],
      "warnings": []
    }
  ],
  "provenance": {}
}
```

Rules:
- use first column as row labels when table has year-like columns;
- detect title/unit from Docling table title, first row, image/file metadata, and table text;
- normalize comma-space values such as `1, 008` to `1008`;
- preserve original raw text;
- do not invent missing cells;
- mark suspicious cells from 321E1 missing-cell audit as review risk;
- if header cannot be confidently determined, keep table-level review and do not flood invalid-year candidates.

## mapping_requirements
Map unified Docling rows into MetricCandidate-like records.

Set:
- `source_stage = docling_unified_mapping_321e2`
- `recognition_source = DOCLING_TABLE_GRID`

Trust gate:
- trusted only if metric code known, year valid, value parsed, provenance complete, no suspicious missing-cell risk, no conflict;
- review required for unknown metric, invalid header/year, suspicious missing cells, table schema uncertainty, value parse uncertainty;
- reject only clear non-metric/noise rows.

Do not force trusted rate upward. This benchmark is evidence gathering, not a victory parade. Humans do enough fake victory parades already.

## diagnostics_required
Create these sheets:

### `docling_unified_tables`
- image_name
- table_id
- table_title
- unit
- columns
- row_count
- value_cell_count
- warnings

### `docling_normalized_rows`
- image_name
- table_id
- row_index
- metric_name_raw
- metric_name_cn
- values_count
- row_warnings

### `docling_metric_candidates_all`
- image_name
- table_id
- row_index
- metric_code
- metric_family
- year
- raw_value
- normalized_value
- unit
- split_decision
- risk_tags
- reason
- provenance

### `docling_trusted_preview`
### `docling_review_required_preview`
### `docling_rejected_preview`

### `docling_mapping_diagnostics`
- image_name
- table_id
- row_index
- raw_metric_name
- metric_code
- year
- raw_value
- normalized_value
- issue_type
- recommended_action
- reason

### `docling_vs_mineru_vlm_summary`
Compare available routes:
- route_name
- sample_count
- candidate_count
- trusted_count
- review_required_count
- rejected_count
- trusted_rate
- unit_unknown_count
- unknown_metric_count
- invalid_year_count
- value_parse_failed_count
- possible_missing_value_count
- qa_fail_count
- notes

## output_contract
Write to:

```powershell
D:\_datefac\output\docling_unified_mapping_321e2
```

Required files:
1. `docling_unified_mapping_321e2.xlsx`

Sheets:
- `summary`
- `docling_unified_tables`
- `docling_normalized_rows`
- `docling_metric_candidates_all`
- `docling_trusted_preview`
- `docling_review_required_preview`
- `docling_rejected_preview`
- `docling_mapping_diagnostics`
- `docling_vs_mineru_vlm_summary`
- `risk_tag_counts`
- `qa_checks`
- `known_limitations`

2. `docling_unified_mapping_321e2_summary.json`

3. `docling_unified_mapping_321e2_report.md`

Optional:
- `docling_unified_tables.jsonl`
- `docling_metric_candidates_all.jsonl`

## summary_metrics
Include:
- input_image_count
- docling_table_count
- unified_table_count
- table_with_candidates_count
- table_with_trusted_count
- total_candidate_count
- trusted_total_count
- review_required_total_count
- rejected_total_count
- trusted_rate
- unit_unknown_count
- invalid_year_count
- unknown_metric_code_count
- value_parse_failed_count
- possible_missing_value_count
- suspicious_missing_cell_candidate_count
- comma_space_number_fixed_count
- conflict_count
- provenance_complete_rate
- mineru_body_trusted_rate
- pure_vlm_calibrated_trusted_rate
- ppstructure_trusted_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- docling_mapping_decision

Decision rule:
- If qa_fail_count > 0:
  `DOCLING_MAPPING_BLOCKED_BY_QA_FAILURE`
- If unified_table_count >= 8, table_with_trusted_count >= 5, trusted_rate >= 0.35, provenance_complete_rate >= 0.95:
  `DOCLING_MAPPING_READY_FOR_321E_FULL_BAKEOFF`
- If unified_table_count >= 5 and table_with_candidates_count >= 5:
  `DOCLING_MAPPING_PARTIAL_INCLUDE_IN_BAKEOFF`
- Otherwise:
  `DOCLING_MAPPING_NOT_READY`

## qa_checks
Required checks:
- 321E1 audit dir exists;
- Docling output dir exists;
- no E-drive files modified;
- no Docling/MinerU/VLM/PPStructure command executed;
- every candidate has table_id and source_stage;
- trusted candidates have valid year;
- trusted candidates have known metric code;
- trusted candidates have parsed numeric value;
- trusted candidates have provenance;
- suspicious missing cells are not silently trusted;
- output files written successfully.

## safety_constraints
Absolute constraints:
1. Do not run Docling.
2. Do not run MinerU.
3. Do not run PaddleOCR/PPStructure.
4. Do not call VLM/API/cloud/network.
5. Do not modify E-drive input/output folders.
6. Do not modify production delivery files.
7. Do not modify `data/overrides/02B_ai_repair_override.xlsx`.
8. Do not modify `data/mapping/formal_scope_rules.json`.
9. Do not run `factory_core.py`.
10. Do not rewrite old Stage7 pipeline.
11. Do not continue 321D2 normalizer expansion.
12. Do not commit `output/` artifacts.
13. Do not commit anything under `E:\mineru_lab`.
14. Do not commit unrelated 320G2 leftovers or temp scripts.
15. Preserve Chinese text as UTF-8.

## validation
Run compile checks:

```powershell
python -m py_compile datefac/table_bakeoff/docling_unified_mapper.py
python -m py_compile datefac/table_bakeoff/docling_metric_probe.py
python -m py_compile datefac/table_bakeoff/tool_comparison_summary.py
python -m py_compile tools/run_docling_unified_mapping_probe_321e2.py
```

Then run:

```powershell
python tools/run_docling_unified_mapping_probe_321e2.py ^
  --docling-audit-dir D:\_datefac\output\docling_output_audit_321e1 ^
  --docling-output-dir E:\mineru_lab\benchmarks\table_extraction_321e\outputs\docling ^
  --input-image-dir E:\mineru_lab\benchmarks\table_extraction_321e\input_images ^
  --mineru-body-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\docling_unified_mapping_321e2
```

PowerShell one-line form is also acceptable. Report the exact command used.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 321E2 code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Probe Docling unified table mapping`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- input_image_count
- docling_table_count
- unified_table_count
- table_with_candidates_count
- table_with_trusted_count
- total_candidate_count
- trusted_total_count
- review_required_total_count
- rejected_total_count
- trusted_rate
- unit_unknown_count
- invalid_year_count
- unknown_metric_code_count
- value_parse_failed_count
- possible_missing_value_count
- suspicious_missing_cell_candidate_count
- comma_space_number_fixed_count
- conflict_count
- provenance_complete_rate
- mineru_body_trusted_rate
- pure_vlm_calibrated_trusted_rate
- ppstructure_trusted_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- docling_mapping_decision
- top risk tags
- skipped/untracked files
