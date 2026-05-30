# 320C TableAsset Recognition Probe

## task_title
Probe TableAsset image-to-table recognition for MinerU core tables

## project
D:\_datefac

## current_context
320A and 320B are complete.

320A added a MinerU TableAsset layer:
- `datefac/domain/table_asset.py`
- `datefac/parser/mineru_output_reader.py`
- `tools/export_mineru_table_assets_excel.py`

320B and 320B2 added MinerU benchmark and calibration:
- `datefac/benchmark/mineru_benchmark_runner.py`
- `datefac/classification/table_role_classifier.py`
- `tools/run_mineru_benchmark_320b.py`

Latest 320B2 benchmark result:
- report_count: 10
- parsed_report_count: 10
- total_table_asset_count: 216
- image_path_raw_coverage_rate: 0.99537
- image_path_resolved_exists_rate: 0.99537
- bbox_coverage_rate: 1.0
- core_table_detected_rate: 1.0
- unknown_table_rate: 0.175926
- parser_decision: MINERU_ASSET_LAYER_NEEDS_TABLE_RECOGNITION_NEXT
- top warnings: missing_page_idx=108, IMAGE_PATH_MISSING=1

Decision:
MinerU is now validated as a strong layout/table asset layer. The next step is not production integration yet. The next step is a sandbox-only recognition probe that converts selected core TableAsset images into rough structured table grids and measures whether the output is usable for the existing DateFac metric extraction pipeline.

## goal
Create a sandbox-only TableAsset recognition probe for selected MinerU core table images.

The task should:
1. read TableAssets from MinerU output directories using the existing 320A/320B code;
2. select only high-value tables by `table_role_guess`;
3. run a lightweight local table recognition attempt only on selected table images;
4. normalize recognition output into an `ExtractedTable` / cell-grid format;
5. export Excel/JSON diagnostics;
6. not write production delivery files;
7. not generate final trusted metrics yet.

This task is a probe, not a production recognizer.

## scope
Allowed table roles for this probe:
- CORE_METRIC_TABLE
- FINANCIAL_FORECAST_VALUATION
- BALANCE_SHEET
- INCOME_STATEMENT
- CASH_FLOW_STATEMENT
- BUSINESS_ASSUMPTION

Limit recognition workload by default:
- max 3 reports unless user passes a larger value;
- max 20 table assets total unless user passes a larger value;
- prioritize CORE_METRIC_TABLE and FINANCIAL_FORECAST_VALUATION first.

## expected_new_files
Suggested files:
- `docs/codex_tasks/320c_table_asset_recognition_probe.md`
- `datefac/domain/extracted_table.py`
- `datefac/recognition/__init__.py`
- `datefac/recognition/table_image_recognizer.py`
- `tools/run_table_asset_recognition_probe_320c.py`

Optional if useful:
- `datefac/recognition/paddleocr_adapter.py`
- `datefac/recognition/cv_image_precheck.py`

Do not scatter recognition logic into benchmark runner directly.

## CLI contract
The CLI should support:

```powershell
python tools/run_table_asset_recognition_probe_320c.py ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --output-dir D:\_datefac\output\table_asset_recognition_320c ^
  --max-reports 3 ^
  --max-tables 20
```

Optional flags:
- `--roles CORE_METRIC_TABLE,FINANCIAL_FORECAST_VALUATION,BALANCE_SHEET,INCOME_STATEMENT,CASH_FLOW_STATEMENT,BUSINESS_ASSUMPTION`
- `--recognizer auto|paddleocr|ocr_text_only|none`
- `--dry-run-selection-only`

Default behavior:
- If no local recognizer is available, do not fail the whole task. Output `RECOGNIZER_UNAVAILABLE` and still generate selection diagnostics.
- Do not download any model automatically.
- Do not call any remote endpoint.

## recognizer policy
The recognizer layer must be adapter-based.

Recommended interface:

```python
class TableImageRecognizer:
    name: str
    version: str

    def is_available(self) -> bool:
        ...

    def recognize(self, image_path: str) -> ExtractedTable:
        ...
```

For this task, implement one or more of these local-only modes:

1. `none`
   - selection and diagnostics only;
   - no image recognition.

2. `ocr_text_only`
   - allowed only if a local OCR package already exists;
   - extract text lines if available;
   - no table structure promise.

3. `paddleocr`
   - use only if PaddleOCR / PP-Structure is already installed locally;
   - do not install or download anything;
   - if unavailable, return a clear warning.

If using PaddleOCR / PP-Structure requires model downloads, do not trigger them. The task should report `BLOCKED_RECOGNIZER_MODEL_MISSING` or `RECOGNIZER_UNAVAILABLE` instead.

## extracted_table_schema
Create a dataclass or typed structure with at least:

```python
class ExtractedTable:
    extracted_table_id: str
    table_asset_id: str
    source_doc_name: str
    table_role_guess: str
    image_path: str
    recognizer_name: str
    recognizer_version: str
    recognition_status: str
    row_count: int
    col_count: int
    cell_count: int
    non_empty_cell_count: int
    raw_text: str
    table_grid: list[list[str]]
    cells: list[dict]
    warnings: list[str]
```

Recommended `recognition_status` values:
- RECOGNIZED_GRID
- RECOGNIZED_TEXT_ONLY
- RECOGNIZER_UNAVAILABLE
- IMAGE_MISSING
- FAILED
- SKIPPED_BY_ROLE
- SKIPPED_BY_LIMIT

## selection rules
Read TableAssets from all report folders under `--mineru-output-root` using existing 320A reader.

Sort selected assets by priority:
1. CORE_METRIC_TABLE
2. FINANCIAL_FORECAST_VALUATION
3. BALANCE_SHEET
4. INCOME_STATEMENT
5. CASH_FLOW_STATEMENT
6. BUSINESS_ASSUMPTION
7. lower warning count
8. image_exists = true first

Do not process assets whose image is missing.

## output contract
Write these files under `--output-dir`:

1. `table_asset_recognition_320c.xlsx`
   Required sheets:
   - summary
   - selected_table_assets
   - extracted_tables
   - extracted_cells
   - raw_text_preview
   - warnings
   - recognizer_status_counts
   - skipped_assets

2. `table_asset_recognition_320c_summary.json`

3. `table_asset_recognition_320c_report.md`

4. Optional debug JSONL:
   - `selected_table_assets.jsonl`
   - `extracted_tables.jsonl`

Do not embed images into Excel in this task. Use image paths.

## summary metrics
Include:
- report_count_scanned
- table_asset_count_scanned
- selected_table_asset_count
- recognizer_name
- recognizer_available
- recognized_grid_count
- recognized_text_only_count
- recognizer_unavailable_count
- image_missing_count
- failed_count
- avg_non_empty_cell_count
- recognition_probe_decision

Decision rule:
- If selected_table_asset_count > 0 and recognized_grid_count >= 3:
  `TABLE_RECOGNITION_PROBE_READY_FOR_320D_METRIC_CANDIDATE_MAPPING`
- If recognizer is unavailable:
  `BLOCKED_RECOGNIZER_UNAVAILABLE_CHOOSE_LOCAL_OCR_OR_VLM_NEXT`
- If only text-only output is available:
  `TEXT_ONLY_RECOGNITION_NEEDS_TABLE_STRUCTURE_ENGINE`
- Otherwise:
  `NEED_RECOGNIZER_CALIBRATION`

## safety constraints
Absolute constraints:
1. Do not modify production delivery files:
   - `01_自动可信核心指标.xlsx`
   - `02_人工复核指标队列.xlsx`
   - `02A_人工年份修正覆盖表.xlsx`
   - `05_核心财务指标标准化.xlsx`
   - `06_最终核心财务指标.xlsx`
2. Do not modify:
   - `data/overrides/02B_ai_repair_override.xlsx`
   - `data/mapping/formal_scope_rules.json`
3. Do not run `factory_core.py`.
4. Do not rewrite old Stage7 pipeline.
5. Do not call any cloud API, remote LLM, or network endpoint.
6. Do not download OCR or model weights.
7. Do not commit output artifacts.
8. Do not commit anything under `E:\mineru_lab`.
9. Preserve Chinese text as UTF-8. No `????` or replacement characters.

## validation
Run:

```powershell
python -m py_compile datefac/domain/extracted_table.py
python -m py_compile datefac/recognition/table_image_recognizer.py
python -m py_compile tools/run_table_asset_recognition_probe_320c.py
```

Then run:

```powershell
python tools/run_table_asset_recognition_probe_320c.py ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --output-dir D:\_datefac\output\table_asset_recognition_320c ^
  --max-reports 3 ^
  --max-tables 20
```

If no recognizer is available, the run should still produce a valid report with a blocked decision.

## commit requirements
After implementation and local validation:
1. `git status`
2. only add 320C code and this task document;
3. do not add `output/`;
4. do not add `E:\mineru_lab`;
5. do not add unrelated untracked files such as:
   - `fix_307e_reviewed_at.py`
   - `tools/run_stage7a_5pdf_regression_sandbox.py`
   - `tools/update_stage5v_production_06_safe_rows.py`
6. commit message:
   `Add table asset recognition probe`
7. push to remote `main`.

## final response requirements
After push, report:
- pushed branch
- commit hash
- changed files
- probe report path
- selected_table_asset_count
- recognizer_name
- recognizer_available
- recognized_grid_count
- recognized_text_only_count
- recognition_probe_decision
- top warning types
- skipped/untracked files
