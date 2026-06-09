# DateFac 项目总览 333A / 341A 同步版

## 1. 一句话定位

DateFac 当前最值得展示的不是“已经能自动交付”，而是“已经把真实 PDF、AI dry-run、人审闭环、client preview 和 preview audit 组织成了一条可信 demo 链路”。

## 2. 当前里程碑状态

- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `not investment advice`

## 3. 当前完整链路

`Real PDFs -> MinerU-first extraction -> AI dry-run review -> Human review -> 340C full validation -> 340D apply plan -> 340E post-human sidecar -> 340F client preview -> 340G audit -> 341A milestone package`

## 4. 当前 demo 能展示什么

- 真实 PDF intake
- deterministic reviewed 治理
- AI dry-run judgement
- human review 闭环
- human-reviewed client preview
- client preview export audit
- milestone package 汇总

## 5. 关键数字

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

## 6. 当前不能承诺什么

- 正式 client delivery
- production-ready
- 自动写回
- 无需人工复核
- 投资建议
- 规模化稳定性

## 7. 当前最真实的价值

- 真实 PDF 到 preview 的链路已贯通
- AI 被放在受约束的 dry-run 角色中
- human review 在 preview 前形成闭环
- preview 已通过审计，适合 demo / client preview 展示

## 8. 当前 benchmark 限制

当前 benchmark 仍然是有限真实 PDF 样本，不代表规模化生产稳定性。

## 9. 下一阶段路线图

- 更大 benchmark
- parser robustness
- metadata extraction
- UI review workflow
- batch reliability

## 10. 总结

> DateFac 当前的最佳定位，是一个已经达到 human-reviewed client preview milestone 的可信 demo 系统，而不是一个已经完成正式交付闭环的生产产品。 
