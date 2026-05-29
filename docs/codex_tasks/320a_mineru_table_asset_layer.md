# 320A MinerU TableAsset Layer

## task_title
Build MinerU output reader and TableAsset inventory exporter

## project
D:\_datefac

## current_context
DateFac is being upgraded from the old PDF/table extraction route to a MinerU-first table asset pipeline.

Existing downstream governance assets must be preserved:
- structured financial metric layers;
- standardizer and mapping logic;
- trusted/review_required split;
- override-first repair flow;
- dry-run, hash guard, delivery state check;
- Excel delivery artifacts.

The goal of this task is only to add the first upstream layer:

MinerU output directory -> DateFac TableAsset records -> human-readable Excel inventory.

This task must not attempt full table cell extraction, OCR, VLM, LLM, or production candidate application.

## goal
Create a sandbox-only MinerU TableAsset ingestion layer.

The new layer should read MinerU exported files such as:
- *_content_list.json
- *_content_list_v2.json
- *.md
- images/ table crop directory

Then produce normalized DateFac table assets with page, bbox, image path, caption/nearby text, guessed table role, and status.

## expected_new_files
Prefer adding stable reusable modules instead of putting everything into one huge script.

Suggested files:
- datefac/__init__.py
- datefac/domain/__init__.py
- datefac/domain/table_asset.py
- datefac/parser/__init__.py
- datefac/parser/mineru_output_reader.py
- tools/export_mineru_table_assets_excel.py
- tests/test_mineru_output_reader.py if the repository test setup is available; otherwise create a lightweight self-check inside the tool.

If the repository already has a better package layout, adapt to it, but do not scatter core logic across many unrelated tools.

## input_contract
The CLI tool should support:

```powershell
python tools/export_mineru_table_assets_excel.py ^
  --mineru-output-dir D:\_datefac\input\mineru_samples\hard_report ^
  --output-dir D:\_datefac\output\mineru_table_asset_sandbox\hard_report
```

The tool must locate likely MinerU files inside `--mineru-output-dir`:
- content_list json: prefer `*_content_list.json`, fallback to `content_list.json` if present;
- content_list_v2 json: prefer `*_content_list_v2.json`, optional;
- markdown: prefer `*.md`, optional;
- images directory: optional but expected.

The tool must not require the exact hard_report filename. It should work with any MinerU output folder.

## table_asset_schema
Create a dataclass or typed structure with at least these fields:

```python
class TableAsset:
    table_asset_id: str
    source_doc_name: str
    page_idx: int | None
    page_number: int | None
    block_index: int
    block_type: str
    bbox: list | str
    image_path: str
    image_exists: bool
    caption: str
    footnote: str
    nearby_text: str
    table_html_present: bool
    table_html_length: int
    table_role_guess: str
    role_guess_reason: str
    asset_status: str
    raw_source: str
```

Recommended `table_role_guess` values:
- CORE_METRIC_TABLE
- FINANCIAL_FORECAST_VALUATION
- BALANCE_SHEET
- INCOME_STATEMENT
- CASH_FLOW_STATEMENT
- BUSINESS_ASSUMPTION
- BASIC_DATA
- RATING_STANDARD
- DISCLAIMER_OR_LEGAL
- CHART_OR_MARKET_TREND
- UNKNOWN_TABLE

Recommended `asset_status` values:
- READY_FOR_REVIEW
- IMAGE_MISSING
- BBOX_MISSING
- NON_TABLE_SKIPPED
- PARSE_WARNING

## parsing_rules
Read MinerU content blocks defensively. MinerU versions may vary.

Table block detection should handle at least:
- `type == "table"`
- nested `content.image_source.path`
- direct `img_path` / `image_path` if present
- nested `content.html`, which may be empty
- `bbox`
- `page_idx`
- `table_caption`
- `table_footnote`

Do not crash if a key is missing. Record warnings and continue.

For `nearby_text`, use simple local context:
- previous 1 to 3 text/title blocks on the same page;
- following 1 text block if useful;
- avoid footer/header/page_number when possible.

## classification_rules
Implement a simple deterministic role guesser. No LLM.

Examples:
- contains `盈利预测和财务指标`, `每股收益`, `ROE`, `P/E`, `P/B`, `EV/EBITDA` -> CORE_METRIC_TABLE
- contains `财务预测与估值`, `关键财务与估值指标` -> FINANCIAL_FORECAST_VALUATION
- contains `资产负债表`, `资产总计`, `负债合计`, `股东权益` -> BALANCE_SHEET
- contains `利润表`, `营业收入`, `营业成本`, `归属于母公司净利润` -> INCOME_STATEMENT
- contains `现金流量表`, `经营活动现金流`, `投资活动现金流`, `融资活动现金流` -> CASH_FLOW_STATEMENT
- contains `主营业务假设`, `正面银浆业务`, `合计`, `毛利润` -> BUSINESS_ASSUMPTION
- contains `基础数据`, `收盘价`, `总市值` -> BASIC_DATA
- contains `投资评级标准`, `优于大市`, `弱于大市` -> RATING_STANDARD
- contains `免责声明`, `分析师声明`, `重要声明` -> DISCLAIMER_OR_LEGAL

Use caption + nearby_text + table html preview if present. If uncertain, return UNKNOWN_TABLE.

## output_contract
Write these files under `--output-dir`:

1. `mineru_table_assets.xlsx`
   Required sheets:
   - summary
   - table_assets
   - warnings
   - role_counts
   - source_files

2. `mineru_table_assets.json`
   JSON list of normalized table asset records.

3. `mineru_table_assets_summary.json`
   Include:
   - source_dir
   - content_list_found
   - content_list_v2_found
   - markdown_found
   - table_asset_count
   - image_missing_count
   - bbox_missing_count
   - role_counts
   - status_counts
   - generated_at

4. `mineru_table_assets_report.md`
   Human-readable report with concise inventory and next-step recommendation.

Do not embed large images into Excel in this task. Put image paths only. Image embedding can be a later task.

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run Marker, Surya, pdfplumber, PaddleOCR, OCR, VLM, or any model.
3. Do not call any LLM, local model, cloud API, or network endpoint.
4. Do not modify production delivery files:
   - 01_自动可信核心指标.xlsx
   - 02_人工复核指标队列.xlsx
   - 02A_人工年份修正覆盖表.xlsx
   - 05_核心财务指标标准化.xlsx
   - 06_最终核心财务指标.xlsx
5. Do not modify official override or mapping files:
   - data/overrides/02B_ai_repair_override.xlsx
   - data/mapping/formal_scope_rules.json
6. Do not run factory_core.py.
7. Do not write output artifacts into git-tracked production folders unless the repository already uses that pattern for sandbox output.
8. Preserve Chinese text as UTF-8. No `????` or replacement characters.

## compatibility_requirements
Reuse existing helper style where reasonable:
- pandas + openpyxl Excel writer style;
- safe sheet name handling if an existing helper is available;
- repo-local import path pattern used in existing tools.

Do not rewrite existing Stage 7 pipeline in this task.
Do not delete old pdfplumber/marker/docling adapters.

## validation
Run at minimum:

```powershell
python -m py_compile datefac/domain/table_asset.py
python -m py_compile datefac/parser/mineru_output_reader.py
python -m py_compile tools/export_mineru_table_assets_excel.py
```

If a MinerU sample output directory exists locally, run the exporter against it.
If not, produce a clear BLOCKED_MISSING_MINERU_SAMPLE message in the report, but still keep the code compilable.

## acceptance_criteria
PASS if:
- new reusable MinerU output reader exists;
- CLI exporter exists;
- exporter can read a MinerU output folder without exact filename assumptions;
- table assets are normalized into JSON and Excel;
- role guessing is deterministic and does not use LLM;
- missing fields do not crash the run;
- production delivery files remain unchanged;
- old downstream pipeline remains untouched.

## recommended_next_step_after_this_task
After 320A passes, proceed to 320B:
MinerU benchmark runner over 10 hard financial research PDFs, measuring table recall, image path coverage, bbox coverage, and role classification quality.
