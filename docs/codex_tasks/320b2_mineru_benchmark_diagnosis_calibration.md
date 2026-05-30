# 320B2 MinerU Benchmark Diagnosis & Calibration

## Task Goal
在不进入 OCR / 320C 的前提下，针对 320B 两个异常指标做诊断与校准：
1. `image_path_coverage_rate` 偏低
2. `core_table_detected_rate` 偏低

本阶段仅做读取层与分类规则校准，不做模型推理。

## Background
320A / 320B 已完成并 push：
- 320B commit: `71444f2726b4cdbf7fedce22f87ce3a6a219caf1`
- benchmark 关键指标：
  - `report_count=10`
  - `parsed_report_count=10`
  - `bbox_coverage_rate=1.0`
  - `image_path_coverage_rate=0.49537`
  - `core_table_detected_rate=0.2`

结论倾向：layout/table asset 层可用，但 reader 口径与 role 分类器需校准。

## Scope
- 修正 MinerU image path 解析与覆盖率统计口径。
- 增强 deterministic role classifier（禁止 LLM）。
- 追加 320B2 诊断输出，保留 sandbox-only。

## Forbidden
1. 不运行 MinerU。
2. 不运行 OCR / PaddleOCR / PP-Structure / VLM / LLM。
3. 不调用任何模型或网络 API。
4. 不修改生产 `01/02/02A/05/06`。
5. 不修改 `data/overrides/02B_ai_repair_override.xlsx`。
6. 不修改 `data/mapping/formal_scope_rules.json`。
7. 不重写旧 Stage7 pipeline。
8. 不提交 `output/` 产物。
9. 不提交 `E:\mineru_lab` 任何文件。
10. 不删除旧 parser 逻辑。

## Files
新增/修改：
- `docs/codex_tasks/320b2_mineru_benchmark_diagnosis_calibration.md`
- `datefac/parser/mineru_output_reader.py`
- `datefac/benchmark/mineru_benchmark_runner.py`
- `datefac/classification/table_role_classifier.py`

## Image Path Diagnosis Requirements
- 新增统一函数：`resolve_mineru_image_path(...)`
- 覆盖字段：
  - `block["img_path"]`
  - `block["image_path"]`
  - `block["image"]`
  - `block["content"]["img_path"]`
  - `block["content"]["image_path"]`
  - `block["content"]["image_source"]["path"]`
  - `block["content"]["image_source"]["relative_path"]`
  - markdown 临近 `![](images/xxx.jpg)`
- 兼容路径形态：
  - `images/xxx.jpg`
  - `./images/xxx.jpg`
  - 绝对路径
  - Windows 反斜杠路径
- 输出字段：
  - `image_path_raw`
  - `image_path_resolved`
  - `image_exists`
- warning 规则：
  - raw 有值但解析不存在：`IMAGE_PATH_RESOLVE_FAILED`
  - raw 为空：`IMAGE_PATH_MISSING`
- coverage 口径：
  - `image_path_raw_coverage_rate`
  - `image_path_resolved_exists_rate`

## Core Role Calibration Requirements
- role 输入信号：
  - `caption`
  - `nearby_text`
  - `table_html_preview`（若存在）
  - markdown 邻近上下文
  - 文件名/页码局部上下文
  - 前后 3 个 text/title block
- 强化关键词识别（CORE / FORECAST / 三大表 / BUSINESS_ASSUMPTION / DISCLAIMER / RATING_STANDARD）
- 优先级：
  - `CORE_METRIC_TABLE` / `FINANCIAL_FORECAST_VALUATION` 优先于普通 `INCOME_STATEMENT`

## 320B2 Output Contract
输出目录：`D:\_datefac\output\mineru_benchmark_320b2`

1. `mineru_benchmark_320b2.xlsx`  
Sheets:
- `summary`
- `per_report`
- `table_assets_all`
- `role_counts`
- `warning_summary`
- `image_path_diagnostics`
- `core_table_detection_diagnostics`
- `unknown_table_samples`
- `missing_image_cases`
- `failed_reports`
- `parser_decision`

2. `mineru_benchmark_320b2_summary.json`
3. `mineru_benchmark_320b2_report.md`

## Added Metrics
- `image_path_raw_coverage_rate`
- `image_path_resolved_exists_rate`
- `table_image_missing_count`
- `image_path_resolve_failed_count`
- `core_signal_hit_count`
- `core_signal_hit_rate`
- `unknown_table_rate_before_or_current`
- `unknown_table_sample_count`
- `role_guess_confidence_distribution`

## Updated parser_decision Rules
若满足：
- `parsed_report_count >= 5`
- `image_path_raw_coverage_rate >= 0.90`
- `image_path_resolved_exists_rate >= 0.80`
- `bbox_coverage_rate >= 0.90`
- `core_table_detected_rate >= 0.60`

则：
- `MINERU_ASSET_LAYER_NEEDS_TABLE_RECOGNITION_NEXT`

若 `image_path_raw_coverage_rate < 0.70` 且 `bbox_coverage_rate >= 0.90`：
- `MINERU_LAYOUT_OK_IMAGE_PATH_READER_NEEDS_FIX`

若 `core_table_detected_rate < 0.40`：
- `ROLE_CLASSIFIER_NEEDS_CALIBRATION`

否则：
- `NEED_MORE_BENCHMARK_OR_FALLBACK`

## Validation
```powershell
python -m py_compile datefac/parser/mineru_output_reader.py
python -m py_compile datefac/benchmark/mineru_benchmark_runner.py
python -m py_compile datefac/classification/table_role_classifier.py
python tools/run_mineru_benchmark_320b.py --mineru-output-root E:\mineru_lab\output_new --output-dir D:\_datefac\output\mineru_benchmark_320b2
```

## Acceptance
- 320B2 仅诊断/校准，不引入 OCR/LLM。
- image path 指标拆分并可定位失败原因。
- core table 检测率由规则校准提升。
- benchmark 输出新增诊断 sheets 与摘要字段。
- 不触碰生产资产链路文件。
