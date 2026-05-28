# 310C Readable Demo Export Layout Generation

## Task Goal
Generate a more readable demo export workbook based on 310A/310B, without changing any extracted data or merging any simulated rescue rows.

## Requirements
- Do not rerun Marker/pdfplumber.
- Do not call API/LLM/OCR.
- Do not modify production.
- Do not real apply.
- Do not generate safe_to_apply or approve_for_real_apply.
- Do not merge simulated rescue rows.
- Do not alter trusted/review_required row membership.
- This is presentation/export formatting only.

## Read
- `output/eval_310a_demo_ready_core_metric_export_package/`
- `output/eval_310b_demo_export_qa_and_readability_check/`

## Use
- `310a_demo_core_metric_export.xlsx`
- `310a_trusted_core_metrics.xlsx`
- `310a_review_required_core_metrics.xlsx`
- `310a_pdf_coverage_summary.xlsx`
- `310a_metric_coverage_summary.xlsx`
- `310a_not_merged_rescue_simulation_summary.xlsx`
- `310b_column_readability_audit.xlsx`
- `310b_recommended_demo_export_layout.md`

## Generate
`output/eval_310c_readable_demo_export_layout_generation/`
- `310c_summary.json`
- `310c_report.md`
- `310c_readable_demo_core_metric_export.xlsx`
- `310c_trusted_core_metrics_readable.xlsx`
- `310c_review_required_summary_readable.xlsx`
- `310c_column_rename_mapping.xlsx`
- `310c_export_layout_audit.xlsx`
- `310c_no_apply_proof.json`

## Readable Workbook Requirements
- Sheet order:
  1. 使用说明
  2. 可信核心指标_宽表
  3. 可信核心指标_明细
  4. PDF覆盖率
  5. 指标覆盖率
  6. 待复核摘要
  7. 未合并模拟救援说明
  8. 原始可信明细_审计用
  9. 原始待复核明细_审计用
- Rename display columns:
  - PDF文件名 -> 报告文件
  - 标准指标 -> 核心指标
  - 指标名 -> 原始指标名
  - 年份 -> 年份
  - value -> 指标值
  - normalized_unit -> 标准单位
  - source_bucket -> 来源分组
  - source_parser -> 解析器
  - source_page -> 来源页码
  - review_status -> 审核状态
  - risk_level -> 风险级别
- Create a pivot/wide trusted metric sheet:
  - rows: 报告文件 + 核心指标 + 标准单位
  - columns: 年份
  - values: 指标值
- Keep original audit sheets unchanged in membership.
- Review_required rows should be summarized by PDF, metric, risk_level, not only dumped as raw rows.
- Preserve trusted row count = 70.
- Preserve review_required row count = 342.
- Do not include safe_to_apply or approve_for_real_apply.

## Required Assertions
- trusted row count preserved
- review_required row count preserved
- no simulated rescue rows merged
- no safe_to_apply / approve_for_real_apply fields generated
- readable workbook generated
- workbook contains required sheet order
- sandbox_apply_attempt_count = 0
- production_apply_attempt_count = 0
- check_delivery_state.py --json PASS
- production/official/formal/standardizer/release unchanged

Commit and push.
