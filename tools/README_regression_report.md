# 批量回归报告工具

## 脚本用途
`tools/build_regression_report.py` 用于扫描 `D:\_datefac\output` 下已有 `*_资产包`，汇总结构化产物质量。

本工具只读取已有文件，不会：
- 重新跑 PDF
- 调用 marker
- 调用 pdfplumber
- 调用 Ollama

## 运行方式（Conda 固定环境）
```powershell
conda run -n factory_v4 python D:\_datefac\tools\build_regression_report.py --output-dir D:\_datefac\output
```

可选参数：
- `--output-dir`：默认 `D:\_datefac\output`
- `--report-path`：默认 `D:\_datefac\output\08_批量回归报告.xlsx`

## 扫描与选择规则
- 扫描目录：`<output-dir>\*_资产包`
- 文件宽松匹配（同类取最新修改时间）：
  - `01`: 以 `01_` 开头且 `.md`
  - `02`: 以 `02_` 开头且 `.xlsx`
  - `03`: 以 `03_` 开头且 `.xlsx`
  - `04`: 以 `04_` 开头且 `.xlsx`
  - `05`: 以 `05_` 开头且 `.xlsx`
  - `07`: 文件名包含 `segment_map` 或以 `07_` 开头且 `.xlsx`

## 输出文件
- `08_批量回归报告.xlsx`
- 若目标文件被占用，会自动生成带时间戳副本。

## 输出 Sheet 说明
1. `summary`
- 每个资产包一行，包含：
  - 01~07 是否存在
  - 选择的 02/05 文件
  - 02 的 sheet 数量与名称
  - 是否命中核心 5 张业务表（主指标/资产负债/利润/现金流/比率）
  - 05 核心指标数量与指标名
  - 错误信息

2. `details_02`
- 每个 02 Sheet 一行：
  - `asset_package`
  - `sheet_name`
  - `rows`
  - `cols`
  - `preview`（前 3 行、前 5 列）

3. `details_05`
- 从 05 的“核心指标宽表”读取每个指标一行：
  - `asset_package`
  - `指标`
  - `年份列和值`
  - `来源表`
  - `来源类型`
  - `置信度`

4. `segment_map`
- 若存在 `07_table_segment_map.xlsx` 且包含 `segment_map` Sheet，则汇总并追加 `asset_package`。
