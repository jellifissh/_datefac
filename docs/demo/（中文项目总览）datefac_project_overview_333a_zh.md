# DateFac 项目总览 333A/339A 同步版

## 1. 项目现在在解决什么问题

DateFac 当前不是在重复做一个“普通 PDF 表格抽取器”。

它更像是在回答这个问题：

> 当 parser 已经能从研报 PDF 里抽出一批候选行之后，系统如何保守地判断哪些能先信、哪些要继续复核、哪些应该明确拒绝，以及怎样把这一切讲清楚而不夸大？

这就是为什么仓库最近的重点是：

- MinerU-first 真实 PDF intake
- precision calibration
- 表格上下文修复
- reviewed strictness 与 year alignment QA
- AI 文本裁决 dry-run
- grounded review
- adoption simulation

## 2. 当前工程定位

当前定位可以概括成：

- 本地运行
- sidecar
- demo
- preview
- no-write-back

这几个词都不是装饰词，而是边界说明。

当前必须承认：

- `client_ready = false`
- `production_ready = false`
- AI 结论当前不写回 official assets

## 3. 当前链路的功能化理解

不要先用阶段号记忆，先按功能看：

1. 用 MinerU 把真实 PDF 解析成可读的页面、表格和候选项
2. 用规则校准把明显噪声和低质量 candidate 压掉
3. 用财务表上下文修复补足表角色和单位信息
4. 用 stricter QA 把 reviewed 集合收紧到更可信的状态
5. 用 AI 做文本层 dry-run 裁决
6. 再做 grounded review 和 adoption simulation
7. 让最终 preview 与文档都保持保守边界

## 4. 337A-338D 的阶段作用

- 336A：从 PDF 文件夹起跑的 smoke runner
- 336B：单文档 debug package
- 337A：MinerU-first 真实 PDF intake
- 337B：candidate precision calibration
- 337C：核心财务表上下文修复
- 337D：reviewed strictness、year alignment、可疑行 QA
- 338A：DeepSeek flash 文本裁决 baseline
- 338B：`AI_REVIEW_MODEL` 对比 DeepSeek flash
- 338C：grounded schema tightening
- 338D：adoption simulation

其中 338A-338D 最重要的边界是：

> 它们在决定“模型建议是否值得参考”，而不是在做正式生产采用。

## 5. 当前关键指标

### 真实 PDF intake

- 337A 成功解析 `3` 份真实 PDF
- 每份 PDF metric candidates:
  - `H3_AP202606081823352620_1.pdf = 134`
  - `H3_AP202606081823352906_1.pdf = 111`
  - `H3_AP202606081823356439_1.pdf = 102`
- 337A 总体：
  - `reviewed = 303`
  - `needs_review = 42`
  - `rejected_or_excluded = 2`

### 规则校准与修复

- 337B reviewed 从 `303` 降到 `98`
- 337C reviewed 升到 `148`
- 337C `table_role_repair_count = 35`
- 337C `unit_filled_count = 119`
- 337D reviewed 再收紧到 `112`
- 337D `year_alignment_repaired_count = 33`
- 337D `reviewed_duplicate_removed_count = 27`

### AI dry-run

- 338A DeepSeek flash baseline:
  - `low_confidence = 34 / 50`
  - `NEEDS_MORE_CONTEXT = 33 / 50`
- 338B `gpt-5.5` A/B:
  - `low_confidence = 0 / 50`
  - `NEEDS_MORE_CONTEXT = 3 / 50`
  - `invalid_response = 3`
- 338C grounded review:
  - `invalid_response = 1`
  - `grounding_source BOTH = 49`
- 338D adoption simulation:
  - `ACCEPT_MODEL_CONFIRM = 39`
  - `ACCEPT_MODEL_REJECT = 3`
  - `HOLD_FOR_HUMAN_REVIEW = 3`
  - `REJECT_BY_DETERMINISTIC_RULE = 4`
  - `INVALID_MODEL_RESPONSE = 1`
  - `deterministic_rule_override_count = 0`

## 6. 模型角色分工

- MinerU：当前主解析器
- deterministic rules：当前最优先的安全层
- `AI_REVIEW_MODEL`：当前主文本裁决候选模型
- DeepSeek flash：baseline / fallback
- vision model：未来版面或截图不确定性工具
- human review：最终安全层

特别重要的一点：

> 338D 没有建议直接把 `AI_REVIEW_MODEL` 设为默认正式模型，`suggest_set_ai_review_model_default = false`。

## 7. 为什么这个状态有价值

这个状态的价值，不在于“已经可以对客户正式交付”，而在于：

- 真实 PDF intake 已经能稳定跑起来
- 规则层能显著压缩错误 reviewed
- AI 层不是黑盒直接上产，而是被 deterministic rules、grounding 和 adoption policy 约束
- 文档层明确承认系统还不成熟

这比“只给一个看上去很完整的 Excel”更可信。

## 8. 安全宣称与禁止宣称

### 当前可安全宣称

- 支持真实研报 PDF 的 MinerU-first intake preview
- 支持规则驱动的 candidate precision repair
- 支持核心财务上下文修复与 stricter reviewed QA
- 支持 AI text adjudication dry-run、A/B 评估、grounded review 和 adoption simulation
- 支持 no-write-back 的 preview 治理链路

### 当前不能宣称

- 已 client-ready
- 已 production-ready
- AI 已取代人工
- 100% 准确
- fully automatic commercial SaaS
- 可直接用于投资决策

## 9. 当前限制

当前限制至少包括：

- 整条链路仍然是 sidecar / demo / preview
- AI 决策仍然只是 dry-run
- human review 仍然必要
- 更大规模 benchmark 还不够
- deployment / security / permission / data isolation 还未闭环

## 10. 结论

DateFac 现在最值得展示的，不是“自动化已经完成”，而是：

> 它已经把真实 PDF 解析、规则约束、AI 裁决试验、人工复核边界和对外叙事安全，组织成了一条比较完整、比较诚实的工程链路。
