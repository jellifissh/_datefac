# DateFac 当前运行手册 333A / 341A 同步版

## 1. 适用范围

这份运行手册现在覆盖的是“真实 PDF -> AI dry-run -> human review -> client preview -> audit”的当前可展示链路。

## 2. 当前阶段

- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `not investment advice`

## 3. 推荐先看什么

1. `README.md`
2. `docs/demo/datefac_human_reviewed_client_preview_runbook_341b_zh.md`
3. `docs/demo/datefac_human_reviewed_client_preview_architecture_341b_zh.md`
4. `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_zh.md`
5. `docs/demo/datefac_ai_review_architecture_339a_zh.md`

## 4. 当前最关键的输出

- `D:\_datefac\output\human_reviewed_client_preview_milestone_341a\human_reviewed_client_preview_milestone_341a.xlsx`
- `D:\_datefac\output\client_preview_export_audit_340g\client_preview_export_audit_340g.xlsx`
- `D:\_datefac\output\client_preview_after_human_review_340f\client_preview_after_human_review_340f.xlsx`

## 5. 当前最重要的数字

- `340B review queue = 77`
- `340C filled = 77 / pending = 0`
- `340D reviewed_after_human_candidate_count = 34`
- `340E reviewed_after_human_total_count = 34`
- `340F client_preview_core_metric_count = 34`
- `340G audited_core_metric_count = 34`

## 6. 当前必须保留的边界

- AI decisions are dry-run only
- human review was used before client preview
- `340F` 是 human-reviewed client preview，不是 official delivery
- `340G` audit passed，但仍然不是 production-ready

## 7. 当前 demo 操作顺序

1. 讲 README 里的阶段边界
2. 打开 341A milestone workbook 讲全链路
3. 打开 340G audit workbook 讲风险审计
4. 如需展开，回看 340D / 340E / 340F

## 8. 当前不能做什么

- 不要把 output 当正式交付
- 不要宣称 client-ready
- 不要宣称 production-ready
- 不要宣称 investment advice

## 9. 下一阶段方向

- 更大 benchmark
- parser robustness
- metadata extraction
- UI review workflow
- batch reliability
