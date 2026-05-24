# Stage 7B Full Structured Table Block Segmentation (Sandbox)

## 1) 背景
- Stage 7A 证明 parse/raw 可跑通，但 clean wide 对复杂多面板研报表格保留不足。
- 现阶段问题核心是缺少 full_structured_table 分层，而不是继续向 06 收敛。

## 2) 本轮目标
- 在 sandbox 中新增 full_structured_table 架构层，保留更多财务表行。
- 保留 mapping miss 行，不因未标准化而丢弃。
- core_metrics_06 仅做 preview，不写生产 06。

## 3) 每份 PDF 对比（Stage7A vs Stage7B）
- H3_AP202605091822098939_1.pdf: clean_wide=9, full_structured=302, gain=293, blocks=4, status=OK
- H3_AP202605141822317295_1.pdf: clean_wide=18, full_structured=470, gain=452, blocks=6, status=OK
- H3_AP202605141822317484_1.pdf: clean_wide=0, full_structured=325, gain=325, blocks=3, status=OK
- H3_AP202605141822318031_1.pdf: clean_wide=3, full_structured=182, gain=179, blocks=36, status=OK
- H3_AP202605141822322334_1.pdf: clean_wide=0, full_structured=128, gain=128, blocks=3, status=OK

## 4) 检测到的表块类型/语义
- detected_statement_types: financial_ratios, income_statement, non_financial_table, rating_explanation, unknown_financial_table

## 5) 仍未完全解析的情况
- 复杂跨栏/跨行合并表仍会出现 metric 缺失或单元格语义歧义，已落入 parse_debug。
- 对非年份列或段落嵌入型指标采用保守提取策略，避免误写年份值。

## 6) 为什么 clean wide 不能代表全量结构化表
- clean wide 偏向核心指标和审阅友好格式，会提前过滤大量未映射/单位不确定行。
- full_structured_table 需要优先保留原始财务证据行，再分层进入标准化与核心层。

## 7) 分层建议
- raw_tables -> table_blocks -> full_structured_table -> standardized_structured_table -> core_metrics_preview/06。
- full_structured_table 与 core_metrics_06 必须解耦，避免早删导致不可追溯。

## 8) Stage 7C 建议
- 建议将上述分层固化到统一 pipeline，先做保留率，再做标准化命中率优化。

## 9) 安全检查
- production_files_modified: False
- official_02b_modified: False
- formal_rules_modified: False
- standardizer_modified: False
- release_package_modified: False
- check_delivery_state_overall_status: PASS
- ready_for_stage7c_pipeline_refactor: True