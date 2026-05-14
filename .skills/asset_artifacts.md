# Skill: 资产包产物规范

## 产物清单
- `01_全量脱水底稿.md`：Markdown 底稿。
- `02A_研报原始表格资产.xlsx`：抽取器原始表格资产层；不做清洗、不做分段、不做分类、不做标准化。
- `02_研报全量结构化数据.xlsx`：后处理后的结构化表格。
- `03_投研结论精华.xlsx`：AI 摘要。
- `04_表格分类结果.xlsx`：表格分类结果。
- `05_核心财务指标标准化.xlsx`：8 项核心财务指标标准化结果。
- `06_pdfplumber_merge_diagnostics.xlsx`：pdfplumber 合并诊断。
- `07_table_segment_map.xlsx`：分段诊断。
- `08_批量回归报告.xlsx`：批量回归报告。
- `09_batch_run_status.xlsx`：批次运行状态。
- `10_extractor_compare_report_*.xlsx`：抽取器 probe 对比报告。
- `11_raw_vs_structured_report.xlsx`：`02A` vs `02` 对比报告。
- `12_asset_consistency_report.xlsx`：资产包一致性报告。
- `13_financial_standardizer_diagnostics.xlsx`：05 诊断报告。
- `14_invalid_output_paths_report.xlsx`：非法/乱码路径诊断报告。

## 关键原则
- `02A` 是证据底稿；先看 `02A` 再评估 `02/05`。
- `02` 是后处理结果，不等同于抽取器原始输出。
- `05` 依赖 `02`，不直接依赖 PDF。
- 分析时必须确保同一资产包内文件来源一致。

## 归因规则
- `02A` 没表：抽取层问题。
- `02A` 有表但 `02` 丢表：后处理问题。
- `02` 有表但 `05` 不命中：标准化问题。

## 实操建议
- 先跑 `12` 一致性，再做跨文件分析。
- 多版本 `02` 存在时优先最新时间戳版本。
- 结论中写明“使用的具体文件名与时间”。
