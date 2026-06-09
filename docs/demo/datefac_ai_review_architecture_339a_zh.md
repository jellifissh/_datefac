# DateFac AI Review 架构说明 339A（341A 状态同步）

## 1. 这份架构文档现在的作用

这份文档不再只解释“AI 模型怎么比较”，而是解释 AI 在今天完整链路中的真实角色：

> AI 是受 deterministic rules、grounding、人审闭环和 no-write-back 边界约束的 dry-run judgment layer，而不是正式决策层。

## 2. 当前全链路中的 AI 位置

完整链路已经是：

`Real PDFs -> MinerU-first extraction -> AI dry-run review -> Human review -> 340C full validation -> 340D apply plan -> 340E post-human sidecar -> 340F client preview -> 340G audit -> 341A milestone package`

AI 处在中间，不在末端。

## 3. 当前状态

- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `not investment advice`

## 4. AI 之前必须先有 deterministic reviewed gate

337D 之前如果 reviewed 候选仍然很松，AI 只会把噪声解释得更自信。

所以 `337D` 的价值在于：

- stricter reviewed gate
- year alignment repair
- suspicious row QA

这一步把 AI 看到的输入收紧到了更可信的 reviewed pool。

## 5. 338A-338D 的架构意义

### 338A

- DeepSeek baseline dry-run
- 提供保守对照组

### 338B

- `AI_REVIEW_MODEL` 与 baseline 做 A/B
- 验证更强模型是否真的减少 `NEEDS_MORE_CONTEXT` 与低置信度

### 338C

- grounded schema tightening
- 把 raw evidence、supporting context 和 conclusion 分层

### 338D

- adoption simulation
- 把模型输出和正式 adoption policy 分开

这一层最关键的结论是：

- `suggest_set_ai_review_model_default = false`

也就是说，AI 并没有因为局部表现更好就自动获得正式默认地位。

## 6. 为什么今天必须继续往 340B-341A 看

因为 AI dry-run 之后仍然存在三类现实问题：

- 需要人工 confirm
- 需要人工 correction 后再 confirm
- 需要 reject 或 keep under review

因此 340B-341A 的价值，就是证明：

- 人工复核在 preview 前被明确插入
- 所有 apply 相关结果仍然是 sidecar、no-write-back
- 只有被 human-reviewed confirm 的结果才会进入 client preview

## 7. 当前关键数字

- `340B review queue = 77`
- `340C filled = 77 / pending = 0`
- `340D reviewed_after_human_candidate_count = 34`
- `340E reviewed_after_human_total_count = 34`
- `340F client_preview_core_metric_count = 34`
- `340G audited_core_metric_count = 34`
- `duplicate_issue_count = 0`
- `unit_issue_count = 0`
- `missing_source_trace_count = 0`
- `unsafe_claim_count = 0`
- `qa_fail_count = 0`

## 8. AI 在当前系统里的真实角色

- 不是 final truth
- 不是 write-back engine
- 不是 client-ready decision maker
- 不是 production-ready approval layer

而是：

- ambiguous rows 的 text adjudication candidate
- adoption simulation 的输入层
- 被 deterministic rules、human review 和 preview audit 共同约束的中间层

## 9. 今天可以安全讲什么

- AI 提高了 dry-run adjudication 的表达能力与候选判断效率
- grounded review 让 AI 输出更可审计
- AI 结果会被人工复核与 preview audit 继续约束

## 10. 今天绝不能讲什么

- AI 已取代人工复核
- AI 输出可以直接用于 client delivery
- AI 现在已经 production-ready
- AI 结果可以直接作为投资建议

## 11. 当前 benchmark 限制

当前 benchmark 仍然是有限真实 PDF 样本。它证明的是链路在当前样本上可用，不证明更大规模、更复杂版式下的稳定性。

## 12. 总结

> 339A AI 架构今天最重要的价值，不是证明模型够强，而是证明模型即使更强，也仍然必须被 deterministic rules、人审闭环和 preview audit 约束。 
