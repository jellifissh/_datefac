# DateFac 项目总览 333A（中文）

## 1. 项目背景

DateFac 的背景不是“再做一个 PDF 表格抽取器”，而是“在金融研报 PDF 抽取结果之上，建立一个更可追溯、更可复核、更适合演示与交接的信任治理层”。在真实业务里，抽取本身只是第一步。真正难的是抽取完成以后，如何判断哪些记录能先进入 trusted preview，哪些记录必须停留在 review_required，哪些记录在人工看过以后应该明确排除，哪些记录只能继续保留为 unresolved preview 状态。

这个问题在金融研报场景里尤其突出，因为数字看起来对，并不代表它真的对。一个值可能来自错误的 row_text，可能单位缺失，可能年份列错位，可能其实来自对比表、图注或说明段，而不是核心财务预测表。DateFac 选择正面处理这些问题，而不是把它们藏在一个“看起来已经很完整”的导出结果后面。

## 2. 项目要解决的问题

DateFac 当前要解决的是三个层次的问题：

### 2.1 抽取结果能否被可信地解释

很多 parser 可以把表格切出来，也能把字符识别出来，但业务真正需要的是“这条记录能不能被可信地解释”。可信解释至少意味着：

- 有 provenance
- 有 metric、year、value、unit 的上下文
- 有 routing 决策
- 有风险标记
- 有人工复核边界

### 2.2 风险记录能否被保守处理

如果系统没有 review_required 队列，就会天然倾向于把更多行推进 trusted。DateFac 当前恰恰反过来：宁可保守、宁可留下 review_required，也不把高风险行伪装成“已经可信”。

### 2.3 对外叙事能否不过度宣称

一个工程 demo 即便内部逻辑保守，如果 README、overview、resume bullets 或 demo script 说得过满，依然会制造错误预期。332A release audit 的存在，就是为了把“文档叙事也纳入工程审计”。

## 3. 为什么这不只是 PDF table extraction

如果只从 PDF table extraction 角度看，通常只会问：

- 表格有没有识别出来
- 单元格切分对不对
- OCR 是否足够清晰

但对金融数据来说，决定可用性的并不只有这些，还有：

- metric 语义是否对
- year 和 value 是否真正对齐
- unit 是否明确且没有冲突
- provenance 是否足够支撑人工回溯
- 风险是否被正确隔离
- 对外展示是否带有当前限制说明

因此 DateFac 的重点不是重复发明 parser，而是把 parser 之后的可信治理工程补齐。这也是它为什么反复强调 sidecar、preview、human review、no write-back 和 release audit。

## 4. 当前架构

当前架构最适合被理解为一个多层 sidecar 信任路由链路：

1. 输入 PDF 或缓存 parser 输出
2. candidate extraction 与 candidate preparation
3. trusted / review_required routing
4. unit risk detection
5. human unit review packaging
6. dry-run apply simulation
7. reviewed preview refresh
8. demo packaging
9. demo release audit

这条链路不是从头改生产，而是从 preview 侧补充治理能力。它最大的价值是把“自动候选”、“人工确认”、“仍需复核”、“明确拒绝”和“仅限演示”这几类状态分清楚。

## 5. Trust-routing 设计

DateFac 当前 trust-routing 设计的核心，是不把 candidate rows 一股脑推进 trusted。相反，它明确区分：

- trusted
- review_required
- human rejected after review

这个设计的意义有三点：

1. 系统承认自己有不确定性。
2. 风险被显式暴露，而不是被 UI 或文档遮掩。
3. 人工 review 的工作量被收敛到真正高风险的区域。

在当前链路里，trusted 并不等于“永远绝对正确”，而是“在当前证据、当前 sidecar 规则和当前 review 状态下，可以被放进 trusted preview”。这个定义非常关键，因为它把“可信 preview”与“生产真理”明确区分开来。

## 6. Human review loop

当前 human review loop 对应的阶段是 `330K2 -> 330K3 -> 330K4`。

### 6.1 330K2

330K2 的任务是把 21 条 unit-review 行打包出来。它不是修 parser，不是改生产规则，而是把高风险行组织成一个人工可读、可填、可追溯的 workbook。

### 6.2 330K3

330K3 读取人工填写过的 workbook，把 `CONFIRM_UNIT`、`REJECT_UNIT`、`NEEDS_MORE_CONTEXT` 等决策翻译成 dry-run apply actions。重点在于：先形成“如果接受这些人工判断，会发生什么”的计划，而不是立刻生效。

### 6.3 330K4

330K4 再基于 dry-run apply plan 刷新 reviewed preview。当前结果是：

- 原始 trusted preview：96 行
- reviewed unit confirmed：2 行
- reviewed trusted preview：98 行
- human rejected：18 行
- remaining review required：1 行

这说明系统在当前阶段并没有试图“把 21 条风险行全都洗进 trusted”，而是只把证据变强后仍然安全的 2 行推进 reviewed trusted preview。

## 7. Stage timeline：Stage 1 到 332A

### 7.1 Stage 1 到 Stage 4

Stage 1 到 Stage 4 更像工程治理的前史，关注的是 repair discipline、override-first rebuildability 和 rule governance。它们的价值不在当前 preview 数字，而在于它们建立了一个原则：所有重要修复都应该可解释、可重建、可审计。

### 7.2 330L 到 332A

330L 之后的链路则更像“把治理原则用于 demo-ready preview state”：

- `330L` 生成 baseline client-style export preview
- `331A` 把 baseline preview 包装成 demo 文档
- `330K2` 对 unit 风险行做人工 review 打包
- `330K3` 生成 no write-back 的 dry-run apply plan
- `330K4` 生成 reviewed preview
- `331B` 基于 reviewed preview 刷新 demo 文档
- `332A` 对文档说法、数字一致性和 overclaim 风险做最终审计

这条链路最值得展示的，不是单点命中率，而是“系统如何有纪律地把人类判断吸收到 preview 叙事里，同时不越界到生产写回”。

## 8. 当前关键指标

当前应保持一致的指标如下：

| 指标 | 当前值 |
|---|---:|
| unfamiliar PDFs | 13 |
| PDFs produced candidates | 7 |
| `prepared_candidate_row_count` | 117 |
| `original_trusted_sheet_row_count` | 96 |
| `reviewed_unit_confirmed_count` | 2 |
| `reviewed_trusted_preview_row_count` | 98 |
| `human_rejected_row_count` | 18 |
| `remaining_review_required_after_unit_review_count` | 1 |
| `apply_plan_row_count` | 21 |
| `overclaim_risk_count` | 0 |
| `qa_fail_count` | 0 |

这些数字不仅要在 summary 中对齐，也应该在 README、overview、runbook、demo script 和面试介绍中对齐。

## 9. Safe claims

当前可以安全宣称的内容包括：

- 这是一个 financial research PDF core metric extraction + trust-routing demo
- 当前状态是 `DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW`
- 项目具备 provenance 保留、unit risk detection、human review packaging、dry-run apply、reviewed preview refresh 和 release audit
- 项目有明确的 no write-back 边界
- 项目能展示从 baseline preview 到 reviewed preview 的演化过程
- 项目对 rejected 与 unresolved 状态采取保守展示策略

## 10. Unsafe claims

当前不能宣称的内容包括：

- 已达到可直接对客交付
- 已达到可直接进入生产部署
- 自动结果可以替代人工 review
- 准确性被保证到没有误差空间
- 已经是全自动商业系统
- 已经是可直接卖给客户的 SaaS
- 可以直接驱动投资决策

这些说法的问题不是“听起来夸张”，而是它们与当前工程事实不一致。

## 11. 面试与展示时的重点话术

当前最有价值的面试话术不是“我们抽出来了多少表”，而是：

1. parser quality 很重要，但它不是终点，trust routing 才决定展示层是否可信。
2. unit review 是金融数据可信化里最关键的一类人工兜底。
3. dry-run apply 把人工判断先变成计划，而不是变成未经审查的正式写回。
4. reviewed preview 体现了 human-in-the-loop 的工程化，而不是手工修 Excel 的偶然结果。
5. release audit 说明项目连“对外怎么说”都纳入了审计范围。

## 12. 商业试点边界

如果未来把这个项目用于小规模试点，当前最合理的边界是：

- 可以做 demo
- 可以做内部展示
- 可以做有人盯着的 human-in-the-loop 小样本验证
- 可以做人工兜底的 preview 服务

但不能说成：

- 正式客户交付系统
- 无人值守自动化生产线
- 已完成部署与安全治理的 SaaS

原因很简单：当前链路仍然依赖 preview、review 和 no write-back 设计，生产级系统所需的部署、安全、权限、数据隔离与持续运行能力尚未完成。

## 13. Current limitations / 当前局限

为了让总览文档和 README、runbook 保持同一套边界，这里也明确保留 `current limitations` 这个词。当前局限包括：

- 当前仍然是 reviewed preview，而不是官方结果刷新
- 当前仍然依赖 human review 来处理 unit 风险和剩余不确定性
- 当前没有 production write-back，也没有官方资产 promotion 逻辑
- 当前 benchmark 样本虽然足够支持 demo 叙事，但不足以支撑大规模商业承诺
- 当前没有真正面向最终客户的 clean export 体验
- 当前没有把安全、权限、部署、监控和故障恢复做成生产级能力

这些局限不是失败说明，而是当前阶段应被诚实保留的边界说明。

## 14. 结论

DateFac 当前最值得展示的，不是“已经完全自动化”，而是“已经把可信化治理、人工 review 隔离、preview 刷新和过度宣称防护这几层工程问题分清楚了”。它是一个适合展示工程判断力、review 闭环和风险边界意识的项目；它不是一个应该被包装成已经达到生产级就绪的系统。
