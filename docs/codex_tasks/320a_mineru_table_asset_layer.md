# 320A MinerU TableAsset Layer

## Task Goal
新增 MinerU 输出读取层，把 MinerU 导出的 content_list/content_list_v2/md/images 转成 DateFac 标准 TableAsset，并导出 `mineru_table_assets.xlsx/json/summary/report`。

## Scope
- 仅做 MinerU 输出读取和表格资产清单。
- 不运行 MinerU。
- 不运行 OCR/VLM/LLM。
- 不改生产 01/02/02A/05/06。
- 不改 02B 与 formal_scope_rules。
- 不重写旧 Stage7 pipeline。

## Priority Files
- `datefac/domain/table_asset.py`
- `datefac/parser/mineru_output_reader.py`
- `tools/export_mineru_table_assets_excel.py`

## Requirements
- 自动识别任意 MinerU 输出目录下的 `*_content_list.json`、`*_content_list_v2.json`、`*.md`、`images/`。
- 提取 table block 的 `page_idx`、`bbox`、`image_path`、`caption`、`footnote`、`nearby_text`。
- 生成 deterministic `table_role_guess`，不使用大模型。
- 输出 Excel sheets：`summary`、`table_assets`、`warnings`、`role_counts`、`source_files`。
- 输出 `mineru_table_assets.json`、`mineru_table_assets_summary.json`、`mineru_table_assets_report.md`。
- 缺字段不能崩，需记录 warning。
- 保持 UTF-8 中文正常。
- 通过 `py_compile`。
