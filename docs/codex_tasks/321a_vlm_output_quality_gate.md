# 321A VLM Output Quality Gate

## task_title
Validate manually generated VLM table JSON outputs before integrating VLM into DateFac pipeline

## project
D:\_datefac

## current_context
The project has shifted from pure row-text repair toward evaluating VLM table recognition as a possible replacement/fallback for PPStructure row-text repair on complex financial tables.

Current state:
- MinerU table crop/layout extraction is strong.
- PPStructure row-text route works but multi-table calibration is becoming rule-heavy.
- A manual VLM test on a cash-flow table produced structurally good values, but the uploaded sample JSON shows Chinese labels are corrupted as `?????` / `???`.
- This means VLM value recognition may be good, but output encoding/label preservation is currently not trustworthy enough for DateFac mapping.

Known VLM output root:

```powershell
E:\mineru_lab\vlm_table_outputs_321a
```

Expected structure:

```text
E:\mineru_lab\vlm_table_outputs_321a
├── <image_hash_or_table_id>\
│   ├── table_meta.json
│   ├── raw_response.txt
│   └── vlm_output.json
└── ...
```

Important observed issue from sample:
- `vlm_output.json` is valid JSON.
- numeric values look plausible.
- `columns` are detected: 2024A, 2025A, 2026E, 2027E, 2028E.
- but `table_title`, `unit`, and `row_name` are corrupted as question marks.

This must be treated as a blocking quality issue. Do not integrate VLM outputs into metric mapping until labels are preserved.

## goal
Implement 321A as a sandbox-only VLM output quality gate.

The task should:
1. scan all VLM output folders under `E:\mineru_lab\vlm_table_outputs_321a`;
2. validate JSON schema and row/value structure;
3. detect Chinese corruption such as `????`, replacement characters, or empty labels;
4. evaluate numeric completeness and year/header consistency;
5. generate a quality report that decides whether VLM outputs are ready for mapping;
6. produce a clean re-run prompt/template if outputs are not ready;
7. do not call VLM/API/network.

This stage is not a DateFac production integration. It is a gate before building VLM recognizer ingestion.

## non_goals
Do not do these in 321A:
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call AI/VLM/cloud/network APIs.
- Do not modify production Excel files.
- Do not apply data to `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not claim VLM readiness from one good-looking table.

## expected_new_or_modified_files
Suggested new files:
- `docs/codex_tasks/321a_vlm_output_quality_gate.md`
- `datefac/vlm/__init__.py`
- `datefac/vlm/vlm_output_reader.py`
- `datefac/vlm/vlm_quality_gate.py`
- `datefac/vlm/vlm_prompt_templates.py`
- `tools/run_vlm_output_quality_gate_321a.py`

Keep this separate from PPStructure pipeline modules. VLM is a new recognizer path.

## input_contract
Primary input:

```powershell
E:\mineru_lab\vlm_table_outputs_321a
```

CLI:

```powershell
python tools/run_vlm_output_quality_gate_321a.py ^
  --vlm-output-root E:\mineru_lab\vlm_table_outputs_321a ^
  --output-dir D:\_datefac\output\vlm_output_quality_321a
```

If input dir is missing, generate blocked output:
- `BLOCKED_MISSING_VLM_OUTPUT_ROOT`

Do not crash.

## supported_input_files
For each VLM table folder, read if present:
- `table_meta.json`
- `vlm_output.json`
- `raw_response.txt`
- optionally any `*.json` or `*.txt` files matching future output names

Preserve source paths in output, but do not copy images or local E-drive files into git.

## expected_vlm_json_schema
Support at least these shapes:

### Shape A
```json
{
  "table_title": "现金流量表",
  "unit": "百万元",
  "columns": ["2024A", "2025A", "2026E", "2027E", "2028E"],
  "rows": [
    {
      "row_name": "经营活动现金流",
      "values": [
        {"column": "2024A", "raw_value": "92464", "normalized_value": 92464}
      ]
    }
  ]
}
```

### Shape B
```json
{
  "is_table": true,
  "table_title": "现金流量表",
  "unit": "百万元",
  "columns": ["2024A", "2025A", "2026E", "2027E", "2028E"],
  "rows": [
    {
      "metric_name": "经营活动现金流",
      "values": [
        {"year": "2024A", "raw_value": "92464", "normalized_value": 92464}
      ]
    }
  ]
}
```

Reader should normalize both shapes into a common internal structure.

## quality_checks
For each table output, compute:

### Schema checks
- JSON parse success
- has rows
- has columns
- every row has label/name
- every row has values
- value count matches column count or has explicit year/column labels

### Chinese/label checks
Detect:
- `????` in table_title/unit/row labels
- Unicode replacement character `�`
- empty row label
- label made mostly of punctuation/question marks
- label not containing any Chinese/Latin letter where expected

Tags:
- `CHINESE_LABEL_CORRUPTED`
- `TABLE_TITLE_CORRUPTED`
- `UNIT_CORRUPTED`
- `ROW_LABEL_CORRUPTED`
- `EMPTY_ROW_LABEL`

### Numeric checks
- normalized_value parseable for numeric rows
- parentheses negatives normalized correctly if raw contains parentheses
- negative values preserved
- no obvious split of 4-digit years or values
- numeric completeness rate

### Column/year checks
- columns detected
- allowed year-like labels: 2024, 2025, 2026E, 2027E, 2028E, 2024A, 2025A, etc.
- value years/columns align with header columns

### VLM readiness decision per table
Suggested table decisions:
- `VLM_TABLE_READY_FOR_MAPPING`
- `VLM_TABLE_VALUES_OK_LABELS_CORRUPTED`
- `VLM_TABLE_SCHEMA_INVALID`
- `VLM_TABLE_NUMERIC_WEAK`
- `VLM_TABLE_EMPTY_OR_NOT_TABLE`

## global_decision_rules
Summary metrics:
- vlm_folder_count
- parsed_json_count
- table_output_count
- table_ready_count
- values_ok_labels_corrupted_count
- schema_invalid_count
- total_row_count
- corrupted_label_row_count
- corrupted_label_rate
- numeric_cell_count
- numeric_parse_success_count
- numeric_parse_success_rate
- column_alignment_pass_count
- unit_detected_count
- table_title_detected_count
- global_vlm_quality_decision

Decision:
- If no parsable JSON:
  `VLM_OUTPUT_QUALITY_BLOCKED_NO_JSON`
- If corrupted_label_rate > 0.05 or table title/unit mostly corrupted:
  `VLM_OUTPUT_NOT_READY_LABEL_CORRUPTION`
- If numeric_parse_success_rate < 0.95:
  `VLM_OUTPUT_NOT_READY_NUMERIC_WEAK`
- If table_ready_count >= 7 and numeric_parse_success_rate >= 0.98 and corrupted_label_rate <= 0.02:
  `VLM_OUTPUT_READY_FOR_321B_MAPPING_BENCHMARK`
- Otherwise:
  `VLM_OUTPUT_PARTIAL_NEEDS_RERUN_OR_PROMPT_FIX`

## output_contract
Write to:

```powershell
D:\_datefac\output\vlm_output_quality_321a
```

Required files:

1. `vlm_output_quality_321a.xlsx`

Sheets:
- `summary`
- `table_inventory`
- `row_quality`
- `cell_quality`
- `corrupted_labels`
- `numeric_quality`
- `schema_errors`
- `rerun_worklist`
- `recommended_prompt`
- `source_files`

2. `vlm_output_quality_321a_summary.json`

3. `vlm_output_quality_321a_report.md`

4. `vlm_rerun_prompt_321a.md`

## rerun_worklist
If any output is corrupted or invalid, produce a rerun worklist.

Columns:
- priority
- table_folder
- image_filename
- source_image_path
- current_decision
- main_issue
- recommended_action

Recommended actions:
- `rerun_vlm_preserve_chinese_labels`
- `rerun_with_strict_json_schema`
- `manual_check_image_quality`
- `skip_not_core_table`

## recommended prompt requirements
Generate a prompt file `vlm_rerun_prompt_321a.md` for the user to copy into Codex/ChatGPT/VLM client.

The prompt must strongly require:
- Preserve all Chinese text exactly as seen.
- Never replace Chinese with `?`, `????`, pinyin, or English translations.
- If a Chinese label cannot be read, output `null` and add warning `UNREADABLE_LABEL`, not `????`.
- Output strict JSON only.
- Include both `metric_name_raw` and `metric_name_cn`.
- Include `row_index`, `columns`, `unit`, `currency`, `raw_value`, `normalized_value`.
- Do not guess missing cells.
- Preserve A/E suffixes in years like `2024A`, `2026E`.

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run PaddleOCR/PPStructure.
3. Do not call AI/VLM/cloud/network APIs.
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
10. Preserve Chinese text as UTF-8. No `????` in generated repo docs/code unless used literally as corruption detection examples.

## validation
Run:

```powershell
python -m py_compile datefac/vlm/vlm_output_reader.py
python -m py_compile datefac/vlm/vlm_quality_gate.py
python -m py_compile datefac/vlm/vlm_prompt_templates.py
python -m py_compile tools/run_vlm_output_quality_gate_321a.py
```

Then run:

```powershell
python tools/run_vlm_output_quality_gate_321a.py ^
  --vlm-output-root E:\mineru_lab\vlm_table_outputs_321a ^
  --output-dir D:\_datefac\output\vlm_output_quality_321a
```

If input is missing, produce blocked output and keep compile-clean.

## commit_requirements
After implementation:
1. `git status`
2. only add 321A code and this task document;
3. do not add `output/`;
4. do not add `E:\mineru_lab`;
5. do not add unrelated untracked files such as:
   - `fix_307e_reviewed_at.py`
   - `tools/run_stage7a_5pdf_regression_sandbox.py`
   - `tools/update_stage5v_production_06_safe_rows.py`
6. commit message:
   `Add VLM output quality gate`
7. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- vlm_folder_count
- parsed_json_count
- table_output_count
- table_ready_count
- values_ok_labels_corrupted_count
- corrupted_label_rate
- numeric_parse_success_rate
- unit_detected_count
- table_title_detected_count
- global_vlm_quality_decision
- top quality issues
- skipped/untracked files
