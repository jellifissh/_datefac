# DateFac 人审后 Client Preview 架构说明 341B（中文）

## 1. 一句话定位

341B 架构文档描述的是 DateFac 当前最完整、最可安全对外叙述的链路：真实 PDF 进入解析与规则层，AI 仅做 dry-run，人工复核承接风险，最后生成经过审计的 client preview。

## 2. 当前状态边界

- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `not investment advice`

## 3. 为什么 341A 之前必须加人审闭环

337A-338D 证明了：

- 真实 PDF 可进入 MinerU-first intake
- deterministic rules 可显著压缩 reviewed 噪声
- AI dry-run 可以做 text adjudication、grounding 和 adoption simulation

但这些还不够直接生成对外 preview。原因是：

- adoption simulation 仍然不是正式 adoption
- AI 结果仍可能需要 correction、reject 或 keep under review
- client preview 需要更强的 unit、source trace、claim safety 边界

所以 340B-340G 的目标，是把 AI 之后仍有风险的部分，放进人工复核闭环，再把结果转换成可审计的 preview state。

## 4. 当前架构层次

1. 真实 PDF intake 层
2. deterministic repair 与 QA 层
3. AI dry-run review 层
4. workbook-based human review 层
5. post-human sidecar result 层
6. client preview packaging 层
7. preview audit 与 milestone packaging 层

## 5. 各阶段职责

### 337A-337D

- `337A` 负责真实 PDF 进入 MinerU-first 链路
- `337B` 负责 candidate precision calibration
- `337C` 负责核心财务上下文修复与 unit 补全
- `337D` 负责 reviewed strictness、year alignment 与 suspicious row QA

### 338A-338D

- `338A` 提供 DeepSeek baseline dry-run
- `338B` 提供 `AI_REVIEW_MODEL` A/B 对比
- `338C` 提供 grounded schema tightening
- `338D` 提供 adoption simulation

这里最重要的架构结论是：AI 决策只是一层建议，不是 final apply。

### 340B-340G

- `340B` 把需要人工复核的队列打包成 review workbook
- `340C` 校验人工填写内容，允许 full validation 或 incremental validation
- `340D` 生成 full human review apply plan
- `340E` 生成 post-human-review sidecar result
- `340F` 生成 human-reviewed client preview
- `340G` 审计 client preview 是否适合 demo/client preview 展示

### 341A

- `341A` 把 340B-340G 的真实结果整合为可对外讲解的 milestone package

## 6. 关键计数如何贯通

- `340B review queue = 77`
- `340C filled = 77 / pending = 0`
- `340D reviewed_after_human_candidate_count = 34`
- `340E reviewed_after_human_total_count = 34`
- `340F client_preview_core_metric_count = 34`
- `340G audited_core_metric_count = 34`

这条计数链说明：

- 77 条人工队列并不会全部进入 preview
- 只有 34 条被 human-reviewed confirm 或 corrected-confirm 的核心指标进入 preview
- 其余行要么 rejected，要么保持 needs review

## 7. 340G 审计为什么关键

340G 不是“再生成一个表”，而是对 340F 进行边界审计，确认：

- `duplicate_issue_count = 0`
- `unit_issue_count = 0`
- `missing_source_trace_count = 0`
- `unsafe_claim_count = 0`
- `qa_fail_count = 0`

这一步是 client preview 能被安全展示的直接依据。

## 8. 当前可讲的系统能力

- 真实 PDF 到 preview 的链路已贯通
- AI 角色被限制在 dry-run 与 adoption-simulation 边界内
- 人工复核已在 preview 前形成明确闭环
- preview 输出已被审计，适合 demo / client preview 展示

## 9. 当前不能讲的系统能力

- 正式 client delivery
- production write-back
- 自动化替代人工复核
- 规模化稳定生产
- 投资建议

## 10. 风险控制框架

当前风险控制不是靠一句“模型更强了”，而是靠以下组合：

- deterministic rules 优先
- AI dry-run only
- human review before preview
- no-write-back proof
- preview audit
- 统一文档中持续保留 `client_ready = false` 与 `production_ready = false`

## 11. 当前 benchmark 限制

当前 benchmark 仍然是有限真实 PDF 样本集，所以：

- 能证明“这条链路在当前样本上可跑通”
- 不能证明“面对更大规模、更复杂版式时已具备稳定产能”

## 12. 下一阶段真正的工程瓶颈

- 更大 benchmark
- parser robustness
- metadata extraction
- UI review workflow
- batch reliability

## 13. 总结

> 341B 架构的核心价值不是把 DateFac 说成成熟产品，而是把它准确定位成一个已经完成 human-reviewed client preview milestone、但仍明确保留工程边界的可信 demo 系统。 
