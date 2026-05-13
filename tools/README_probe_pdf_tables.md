# PDF 表格探针说明

## 脚本用途
`tools/probe_pdf_tables.py` 是独立 POC 工具，用于对同一份研报 PDF 比较多种表格抽取后端效果，并输出统一对比报告。  
它不修改主流程，不导入 `factory_core.py`，不接入正式 `02_研报全量结构化数据.xlsx` 产物。

## 支持的 backend
- `marker_cache`：读取已有 Markdown 缓存，按连续 `|` 行抽取表格块并转 DataFrame。
- `pdfplumber`：调用 `page.extract_tables()`。
- `camelot_stream`：调用 `camelot.read_pdf(..., flavor="stream")`。
- `camelot_lattice`：调用 `camelot.read_pdf(..., flavor="lattice")`。
- `pymupdf_probe`：输出页面文本块数量与预览，用于布局判断（不做正式抽表）。

## 运行方式（Conda 固定环境）
```powershell
conda run -n factory_v4 python D:\_datefac\tools\probe_pdf_tables.py ^
  --pdf "D:\_datefac\input\9c7dd6a029d063bb0a8792e4f31591c7_加水印.pdf" ^
  --marker-cache "D:\_datefac\output\.temp_cache\9c7dd6a029d063bb0a8792e4f31591c7_加水印.pdf.txt" ^
  --output "D:\_datefac\output\_probe_tables" ^
  --pages all
```

可选页码示例：
```powershell
conda run -n factory_v4 python D:\_datefac\tools\probe_pdf_tables.py --pdf "D:\_datefac\input\xxx.pdf" --pages 1
conda run -n factory_v4 python D:\_datefac\tools\probe_pdf_tables.py --pdf "D:\_datefac\input\xxx.pdf" --pages 1-3
conda run -n factory_v4 python D:\_datefac\tools\probe_pdf_tables.py --pdf "D:\_datefac\input\xxx.pdf" --pages 2,3,5
```

## 参数说明
- `--pdf`：必填，目标 PDF 路径。
- `--output`：可选，输出目录。默认 `D:\_datefac\output\_probe_tables`。
- `--marker-cache`：可选，已有 markdown 缓存（`.txt` / `.md`）。
- `--pages`：可选，支持 `all`、`1`、`1-3`、`2,3,5`，默认 `all`。

## 输出文件
输出目录默认在 `D:\_datefac\output\_probe_tables`，包含：
- `table_probe_all_tables.xlsx`：统一工作簿（推荐优先查看）。
  - `00_report` Sheet：与 `table_probe_report.xlsx` 内容一致。
  - 其余 Sheet：各 backend 表格结果，命名示例：
    - `marker_p{page}_t{table_index}`
    - `plumber_p{page}_t{table_index}`
    - `camS_p{page}_t{table_index}`
    - `camL_p{page}_t{table_index}`
    - `fitz_blocks`
- `table_probe_report.xlsx`：总报告，字段包含 `backend/status/page/table_index/rows/cols/preview/output_file/error`。
- `probe_log.txt`：运行日志、backend 可用性、抽取数量和失败摘要。

兼容产物（可选保留）：
- `marker_cache_tables.xlsx`
- `pdfplumber_tables.xlsx`
- `camelot_stream_tables.xlsx`
- `camelot_lattice_tables.xlsx`
- `pymupdf_page_blocks.xlsx`

说明：
- 每张表独立一个 Sheet，Sheet 名会自动处理非法字符和 Excel 31 字符长度限制。
- 如果目标输出文件被占用，脚本会自动添加时间戳副本文件名，不会崩溃。
- 某 backend 没有表或依赖缺失时，不会中断其它 backend。

## 依赖建议（按需安装）
先安装轻依赖：
```powershell
conda run -n factory_v4 python -m pip install pdfplumber pymupdf
```

Camelot 后续评估：
```powershell
conda run -n factory_v4 python -m pip install "camelot-py[cv]"
```

Windows 说明：
- `camelot` 的 `lattice` 模式可能额外依赖 Ghostscript。
- 缺失依赖时会记录 `dependency_missing` 或 `error`，但不会中断整体探针运行。
