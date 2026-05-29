# 320B MinerU Benchmark Runner

## Task Goal
新增 sandbox-only benchmark 工具，批量评估 MinerU TableAsset 层在多份金融研报 MinerU 输出上的稳定性，并生成可审计的 Excel/JSON/Markdown 报告。

## Background
320A 已完成以下组件，并作为 320B 唯一解析入口：
- `datefac/domain/table_asset.py`
- `datefac/parser/mineru_output_reader.py`
- `tools/export_mineru_table_assets_excel.py`

320B 必须复用 320A reader / TableAsset，不允许复制一套新解析逻辑。

## Input Root
- `E:\mineru_lab\output_new`
- 该目录下每个一级子目录视为一份报告 MinerU 输出。

## Absolute Constraints
1. 不运行 MinerU。
2. 不运行 OCR / PaddleOCR / PP-Structure / VLM / LLM。
3. 不调用任何模型、API、网络请求。
4. 不修改生产 `01/02/02A/05/06`。
5. 不修改 `data/overrides/02B_ai_repair_override.xlsx`。
6. 不修改 `data/mapping/formal_scope_rules.json`。
7. 不重写旧 Stage7 pipeline。
8. 不提交 `output/` 运行产物。
9. 不提交 `E:\mineru_lab` 下文件。
10. 仅统计路径、存在性、bbox、role guess、warning，不做图片内容识别。

## New Files
- `datefac/benchmark/__init__.py`
- `datefac/benchmark/mineru_benchmark_runner.py`
- `tools/run_mineru_benchmark_320b.py`

## CLI Contract
```powershell
python tools/run_mineru_benchmark_320b.py ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --output-dir D:\_datefac\output\mineru_benchmark_320b
```

可选参数：
- `--min-report-count`（默认 5）
- `--exclude-name`（可重复）
- `--include-name-regex`（可选）

## Per-report Metrics
每个报告输出：
- `report_name`
- `mineru_output_dir`
- `benchmark_status`
- `content_list_found`
- `content_list_v2_found`
- `markdown_found`
- `source_file_count`
- `table_asset_count`
- `image_missing_count`
- `bbox_missing_count`
- `warning_count`
- `role_counts`
- `status_counts`
- `core_metric_table_count`
- `financial_forecast_table_count`
- `balance_sheet_count`
- `income_statement_count`
- `cash_flow_statement_count`
- `business_assumption_count`
- `basic_data_count`
- `rating_standard_count`
- `disclaimer_or_legal_count`
- `unknown_table_count`

缺少 content_list 时不得崩溃，标记 `FAILED_OR_INCOMPLETE` 并记录 warning。

## Global Metrics
- `report_count`
- `parsed_report_count`
- `failed_report_count`
- `total_table_asset_count`
- `avg_table_asset_per_report`
- `image_path_coverage_rate`
- `bbox_coverage_rate`
- `unknown_table_rate`
- `core_table_detected_report_count`
- `core_table_detected_rate`
- `financial_statement_detected_report_count`
- `business_assumption_detected_report_count`
- `total_warning_count`
- `parser_decision`

### parser_decision Rule
若满足：
- `parsed_report_count >= 5`
- `image_path_coverage_rate >= 0.95`
- `bbox_coverage_rate >= 0.90`
- `core_table_detected_rate >= 0.80`

则：
- `MINERU_CANDIDATE_PRIMARY_PARSER`

否则：
- `NEED_MORE_BENCHMARK_OR_FALLBACK`

## benchmark_status Suggestion
- `PASS`
- `WARN_INSUFFICIENT_REPORT_COUNT`
- `WARN_HIGH_UNKNOWN_TABLE_RATE`
- `WARN_LOW_CORE_TABLE_DETECTION`
- `FAILED_OR_INCOMPLETE`

## Output Files
输出到 `--output-dir`：

1. `mineru_benchmark_320b.xlsx`  
Sheets:
- `summary`
- `per_report`
- `table_assets_all`
- `role_counts`
- `warning_summary`
- `missing_image_cases`
- `missing_bbox_cases`
- `failed_reports`
- `candidate_primary_parser_decision`
- `source_dirs`

2. `mineru_benchmark_320b_summary.json`
3. `mineru_benchmark_320b_report.md`

## Report Content
`mineru_benchmark_320b_report.md` 必须覆盖：
- benchmark 输入目录
- 报告数量
- 成功/失败数量
- table asset 总数
- image path coverage
- bbox coverage
- core table detected rate
- unknown table rate
- parser_decision
- next recommendation

## Validation
先编译：
```powershell
python -m py_compile datefac/benchmark/mineru_benchmark_runner.py
python -m py_compile tools/run_mineru_benchmark_320b.py
```

存在样本时实跑：
```powershell
python tools/run_mineru_benchmark_320b.py --mineru-output-root E:\mineru_lab\output_new --output-dir D:\_datefac\output\mineru_benchmark_320b
```

## Acceptance
PASS 条件：
- 复用 320A reader；
- 批量 benchmark 可运行；
- 单报告失败不拖垮整体；
- 输出 Excel/JSON/MD 齐全；
- deterministic 分类，无 LLM；
- 缺字段只记 warning 不崩溃；
- 不触碰生产资产链路。
