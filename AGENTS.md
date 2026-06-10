# _datefac 项目级工作说明

## 项目概览
- 项目名称：`_datefac`
- 项目定位：本地 Windows 环境下的真实券商研报 PDF 结构化 benchmark / demo 系统
- 当前主线：人审后 client preview 演示链路 + MinerU 本地 benchmark 链路
- 当前状态：`demo_ready = true`，`client_preview_ready = true`，`client_ready = false`，`production_ready = false`
- 重要边界：
  - AI decisions are dry-run only
  - Human review is required before client preview
  - `340F` 是 human-reviewed client preview，不是正式交付
  - `340G` audit passed 不等于 production-ready
  - `342C2` 当前是 `3/5` MinerU pilot success，`ready_for_342d = conditional`
  - 进入 `342D` 前必须先 inspect failed retry rows

## Codex 执行前必读
每次修改前，必须先阅读以下文档并按其约束执行：
- `.skills/asset_artifacts.md`
- `.skills/table_extraction.md`
- `.skills/financial_standardizer.md`
- `.skills/regression_validation.md`
- `.skills/git_workflow.md`
- `.skills/mineru_local_benchmark_workflow.md`
- `.skills/human_reviewed_client_preview_workflow.md`
- `.skills/real_pdf_benchmark_workflow.md`
- `.skills/environment_troubleshooting.md`

如果上述文件缺失，先补齐再继续工作。

## 修改边界与禁止事项
- 不要随意修改 `TableSegmenter`
- 不要随意修改 `marker / vision_runtime / prewarm` 链路
- 不要删除历史资产包或历史产物
- 不要把 `debug_reports`、`output` 运行产物随便提交
- 不要把不同资产包的 `02A / 02 / 05` 混合分析后下结论
- 不要在未明确需求时扩散改动到主流程与规则层
- 不要把 partial MinerU benchmark 结果写成 full pass
- 不要把 `client_preview_ready` 写成 `client_ready`
- 不要把 `production_ready = false` 误写成 true
- 不要把 benchmark sidecar 输出写成正式 client delivery

## 当前重点工作流
- Human-reviewed client preview 链路：
  - `340B` human review package
  - `340C` full validation
  - `340D` apply plan
  - `340E` post-human sidecar
  - `340F` client preview
  - `340G` client preview audit
  - `341A` milestone package
  - `341B` documentation sync
- Real PDF benchmark / MinerU 链路：
  - `342A` larger real-PDF benchmark plan
  - `342B` real PDF corpus intake
  - `342C` MinerU pilot first failure
  - `342C2` verified env retry
  - `342C4` mineru_new env repair / SSL fix

## 执行规范
- 修改前必须说明影响范围与不改范围
- 修改后必须说明验证结果、样本范围与残余风险
- 诊断结论必须分层：抽取层、后处理层、标准化层
- 如果证据不足，优先补诊断，不做猜测性改规则
- Parser 结论必须证据驱动：
  - 先看 extraction artifacts
  - 再看 post-processing
  - 最后看 standardization
- MinerU benchmark 结论必须区分：
  - 手工 MinerU lab 命令是否可跑
  - DateFac runner 是否正确调用 `D:/anaconda/envs/mineru_new/Scripts/mineru.exe`
  - 真实 parse outputs 是否完整
  - failed retry rows 是否已单独检查

