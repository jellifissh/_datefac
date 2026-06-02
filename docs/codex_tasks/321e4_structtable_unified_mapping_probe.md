# 321E4 StructEqTable Unified Mapping Probe

## task_title
Convert audited StructEqTable / StructTable-InternVL2 outputs into DateFac Unified Tables and MetricCandidate sandbox previews

## project
D:\_datefac

## current_context
321E3 StructEqTable output audit completed and was pushed to `origin/main`.

321E3 output directory:

```powershell
D:\_datefac\output\structtable_output_audit_321e3
```

StructEqTable raw output directory:

```powershell
E:\mineru_lab\benchmarks\table_extraction_321e\outputs\structtable_intervl2
```

Benchmark input images:

```powershell
E:\mineru_lab\benchmarks\table_extraction_321e\input_images
```

321E3 key results:
- input_image_count: 10
- discovered_structtable_folder_count: 10
- matched_image_count: 10
- raw_response_exists_count: 10
- markdown_exists_count: 10
- xlsx_exists_count: 10
- csv_exists_count: 10
- parse_success_count: 10
- table_count: 10
- image_with_real_table_grid_count: 10
- numeric_parse_success_rate: 0.9418472063854048
- valid_year_header_count: 52
- invalid_year_header_count: 12
- chinese_label_row_count: 162
- label_corruption_count: 0
- suspicious_short_label_count: 0
- possible_missing_value_count: 0
- timeout_warning_count: 0
- good_candidate_count: 10
- partial_review_needed_count: 0
- poor_or_text_only_count: 0
- qa_pass_count: 8
- qa_warn_count: 0
- qa_fail_count: 0
- structtable_audit_decision: STRUCTTABLE_READY_FOR_321E4_FULL_BAKEOFF

Important interpretation:
- StructEqTable is the strongest extraction-level candidate so far.
- But 321E3 only proves table reconstruction quality. It does not prove DateFac metric mapping quality.
- Before full bakeoff, we need a StructEqTable -> Unified Table -> MetricCandidate mapping probe comparable to Docling 321E2.
- Therefore 321E4 is a mapping probe, not production integration.

Prior comparison baselines:
- MinerU body 321D trusted_rate: 0.38327272727272726
- Pure VLM 321B2 trusted_rate: 0.3361963190184049
- Docling 321E2 trusted_rate: 0.306832298136646
- PPStructure 320G trusted_rate: 0.07194244604316546

## goal
Implement 321E4 to consume audited StructEqTable Markdown/CSV/XLSX outputs and test whether they can be normalized into DateFac Unified Tables and mapped into MetricCandidate previews.

Pipeline:

```text
StructEqTable markdown/csv/xlsx
+ 321E3 audit result
-> Unified Table JSON
-> DateFac MetricCandidate
-> trusted / review_required / rejected preview
-> comparison summary vs MinerU body 321D, pure VLM 321B2, Docling 321E2, PPStructure 320G
```

321E4 should answer:
1. Can StructEqTable reconstructed tables become useful DateFac Unified Tables?
2. Does StructEqTable reduce missing-value / label-corruption / invalid-year problems?
3. Does StructEqTable produce a better trusted rate than MinerU body, pure VLM, Docling, and PPStructure on the same 321E image sample?
4. Which remaining failures are real mapping gaps versus extraction errors?
5. Should StructEqTable become the preferred image-table recognizer candidate for 321E5 full bakeoff and router planning?

This is sandbox-only.

## non_goals
Do not do these in 321E4:
- Do not run StructEqTable again.
- Do not run Docling.
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
- `datefac/table_bakeoff/structtable_unified_mapper.py`
- `datefac/table_bakeoff/structtable_metric_probe.py`
- `datefac/table_bakeoff/structtable_mapping_comparison.py`
- `tools/run_structtable_unified_mapping_probe_321e4.py`
- `docs/codex_tasks/321e4_structtable_unified_mapping_probe.md`

Reuse where safe:
- `datefac/table_bakeoff/structtable_output_reader.py`
- `datefac/table_bakeoff/structtable_table_normalizer.py`
- `datefac/table_bakeoff/structtable_output_audit.py`
- existing domain MetricCandidate classes
- existing risk splitter / mapping helpers only if they are stable and isolated

Keep all 321E4 code in `datefac/table_bakeoff` and the independent CLI. Do not mix it into production, MinerU-body, VLM, PPStructure, or old Stage7 modules.

## input_contract
Primary inputs:

```powershell
D:\_datefac\output\structtable_output_audit_321e3
E:\mineru_lab\benchmarks\table_extraction_321e\outputs\structtable_intervl2
E:\mineru_lab\benchmarks\table_extraction_321e\input_images
```

Optional comparison inputs:

```powershell
D:\_datefac\output\docling_unified_mapping_321e2
D:\_datefac\output\docling_output_audit_321e1
D:\_datefac\output\mineru_table_body_ingestion_321d
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
D:\_datefac\output\batch_row_text_delivery_320g
```

CLI:

```powershell
python tools/run_structtable_unified_mapping_probe_321e4.py ^
  --structtable-audit-dir D:\_datefac\output\structtable_output_audit_321e3 ^
  --structtable-output-dir E:\mineru_lab\benchmarks\table_extraction_321e\outputs\structtable_intervl2 ^
  --input-image-dir E:\mineru_lab\benchmarks\table_extraction_321e\input_images ^
  --docling-mapping-dir D:\_datefac\output\docling_unified_mapping_321e2 ^
  --docling-audit-dir D:\_datefac\output\docling_output_audit_321e1 ^
  --mineru-body-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\structtable_unified_mapping_321e4
```

If optional comparison dirs are missing, continue with warnings.
If the 321E3 audit dir is missing, output blocked decision:
- `BLOCKED_MISSING_321E3_AUDIT_DIR`

## unified_table_requirements
Convert StructEqTable outputs into Unified Table JSON:

```json
{
  "tool": "structtable_intervl2",
  "recognition_source": "STRUCTTABLE_MARKDOWN",
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
- prefer Markdown/CSV text over XLSX for Chinese preservation;
- use first column as row labels when table has year-like columns;
- detect title/unit from StructEqTable title row, run_meta, table text, and filename metadata;
- normalize comma-space values such as `1, 008` to `1008`;
- preserve original raw text;
- do not invent missing cells;
- propagate 321E3 audit risks such as invalid year headers, numeric parse issues, or label issues into candidate risk tags;
- if header cannot be confidently determined, mark table-level review and do not flood invalid-year candidates;
- handle sector/peer-comparison tables with non-year metadata columns such as code/company/currency/price/market cap; do not force these into year-only schema when inappropriate.

## mapping_requirements
Map unified StructEqTable rows into MetricCandidate-like records.

Set:
- `source_stage = structtable_unified_mapping_321e4`
- `recognition_source = STRUCTTABLE_MARKDOWN`

Trust gate:
- trusted only if metric code known, year valid, value parsed, provenance complete, no suspicious extraction risk, no conflict;
- review required for unknown metric, invalid header/year, suspicious extraction risk, table schema uncertainty, value parse uncertainty;
- reject only clear non-metric/noise rows;
- do not silently trust rows from peer-comparison tables if row semantics are company names rather than financial metric names.

Do not force trusted rate upward. This benchmark is evidence gathering, not a corporate earnings call.

## diagnostics_required
Create these sheets:

### `structtable_unified_tables`
- image_name
- table_id
- table_title
- unit
- table_type_guess
- columns
- row_count
- value_cell_count
- warnings

### `structtable_normalized_rows`
- image_name
- table_id
- row_index
- metric_name_raw
- metric_name_cn
- values_count
- row_warnings

### `structtable_metric_candidates_all`
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

### `structtable_trusted_preview`
### `structtable_review_required_preview`
### `structtable_rejected_preview`

### `structtable_mapping_diagnostics`
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

### `structtable_vs_tools_summary`
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
- label_issue_count
- qa_fail_count
- notes

## output_contract
Write to:

```powershell
D:\_datefac\output\structtable_unified_mapping_321e4
```

Required files:
1. `structtable_unified_mapping_321e4.xlsx`

Sheets:
- `summary`
- `structtable_unified_tables`
- `structtable_normalized_rows`
- `structtable_metric_candidates_all`
- `structtable_trusted_preview`
- `structtable_review_required_preview`
- `structtable_rejected_preview`
- `structtable_mapping_diagnostics`
- `structtable_vs_tools_summary`
- `risk_tag_counts`
- `qa_checks`
- `known_limitations`

2. `structtable_unified_mapping_321e4_summary.json`

3. `structtable_unified_mapping_321e4_report.md`

Optional:
- `structtable_unified_tables.jsonl`
- `structtable_metric_candidates_all.jsonl`

## summary_metrics
Include:
- input_image_count
- structtable_table_count
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
- extraction_risk_candidate_count
- label_issue_candidate_count
- conflict_count
- provenance_complete_rate
- mineru_body_trusted_rate
- pure_vlm_calibrated_trusted_rate
- docling_mapping_trusted_rate
- ppstructure_trusted_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- structtable_mapping_decision

Decision rule:
- If qa_fail_count > 0:
  `STRUCTTABLE_MAPPING_BLOCKED_BY_QA_FAILURE`
- If unified_table_count >= 8, table_with_trusted_count >= 6, trusted_rate >= 0.35, provenance_complete_rate >= 0.95:
  `STRUCTTABLE_MAPPING_READY_FOR_321E5_FULL_BAKEOFF`
- If unified_table_count >= 5 and table_with_candidates_count >= 5:
  `STRUCTTABLE_MAPPING_PARTIAL_INCLUDE_IN_BAKEOFF`
- Otherwise:
  `STRUCTTABLE_MAPPING_NOT_READY`

## qa_checks
Required checks:
- 321E3 audit dir exists;
- StructEqTable output dir exists;
- no E-drive files modified;
- no StructEqTable/Docling/MinerU/VLM/PPStructure command executed;
- every candidate has table_id and source_stage;
- trusted candidates have valid year;
- trusted candidates have known metric code;
- trusted candidates have parsed numeric value;
- trusted candidates have provenance;
- extraction-risk candidates are not silently trusted;
- output files written successfully.

## safety_constraints
Absolute constraints:
1. Do not run StructEqTable.
2. Do not run Docling.
3. Do not run MinerU.
4. Do not run PaddleOCR/PPStructure.
5. Do not call VLM/API/cloud/network.
6. Do not modify E-drive input/output folders.
7. Do not modify production delivery files.
8. Do not modify `data/overrides/02B_ai_repair_override.xlsx`.
9. Do not modify `data/mapping/formal_scope_rules.json`.
10. Do not run `factory_core.py`.
11. Do not rewrite old Stage7 pipeline.
12. Do not continue 321D2 normalizer expansion.
13. Do not commit `output/` artifacts.
14. Do not commit anything under `E:\mineru_lab`.
15. Do not commit unrelated 320G2 leftovers or temp scripts.
16. Preserve Chinese text as UTF-8.

## validation
Run compile checks:

```powershell
python -m py_compile datefac/table_bakeoff/structtable_unified_mapper.py
python -m py_compile datefac/table_bakeoff/structtable_metric_probe.py
python -m py_compile datefac/table_bakeoff/structtable_mapping_comparison.py
python -m py_compile tools/run_structtable_unified_mapping_probe_321e4.py
```

Then run:

```powershell
python tools/run_structtable_unified_mapping_probe_321e4.py ^
  --structtable-audit-dir D:\_datefac\output\structtable_output_audit_321e3 ^
  --structtable-output-dir E:\mineru_lab\benchmarks\table_extraction_321e\outputs\structtable_intervl2 ^
  --input-image-dir E:\mineru_lab\benchmarks\table_extraction_321e\input_images ^
  --docling-mapping-dir D:\_datefac\output\docling_unified_mapping_321e2 ^
  --docling-audit-dir D:\_datefac\output\docling_output_audit_321e1 ^
  --mineru-body-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\structtable_unified_mapping_321e4
```

PowerShell one-line form is also acceptable. Report the exact command used.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 321E4 code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Probe StructEqTable unified table mapping`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- input_image_count
- structtable_table_count
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
- extraction_risk_candidate_count
- label_issue_candidate_count
- conflict_count
- provenance_complete_rate
- mineru_body_trusted_rate
- pure_vlm_calibrated_trusted_rate
- docling_mapping_trusted_rate
- ppstructure_trusted_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- structtable_mapping_decision
- top risk tags
- skipped/untracked files
