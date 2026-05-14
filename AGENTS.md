# _datefac 项目级工作说明

## 项目概览
- 项目名称：`_datefac`
- 项目定位：本地 Windows 环境下的券商研报 PDF 自动结构化系统。
- 核心目标：把研报 PDF 转成可追溯、可复核、可回归的结构化资产包，支持批量回归与分层诊断。

## Codex 执行前必读
每次修改前，必须先阅读以下文档并按其约束执行：
- `.skills/asset_artifacts.md`
- `.skills/table_extraction.md`
- `.skills/financial_standardizer.md`
- `.skills/regression_validation.md`
- `.skills/git_workflow.md`

## 修改边界与禁止事项
- 不要随意修改 `TableSegmenter`。
- 不要随意修改 `marker / vision_runtime / prewarm` 链路。
- 不要删除历史资产包或历史产物。
- 不要把 `debug_reports`、`output` 运行产物随便提交。
- 不要把不同资产包的 `02A / 02 / 05` 混合分析后下结论。
- 不要在未明确需求时扩散改动到主流程与规则层。

## 执行规范
- 修改前必须说明影响范围与不改范围。
- 修改后必须说明验证结果、样本范围与残余风险。
- 诊断结论必须分层：抽取层、后处理层、标准化层。
- 如果证据不足，优先补诊断，不做猜测性改规则。
