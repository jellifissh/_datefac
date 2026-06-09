# DateFac 真实 PDF + MinerU + AI Review Runbook 339A（341A 状态同步）

## 1. 这份 runbook 现在讲什么

这份文档仍然以 `337A-338D` 的真实 PDF + MinerU + AI dry-run 链路为主，但已经同步到 `341A` 里程碑状态。

现在它要表达的是：

> AI review 只是中间治理层。当前对外最完整的链路，已经延伸到 human review、client preview 和 preview audit，而不是停在 AI adoption simulation。

## 2. 当前总状态

- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `not investment advice`

## 3. 339A 在今天链路里的位置

339A 讲清楚的是前半段：

1. 真实 PDF 进入 MinerU-first intake
2. deterministic rules 做 precision calibration 与 context repair
3. reviewed strictness / year alignment QA 收紧 reviewed 候选
4. AI review 以 dry-run 方式对 ambiguous rows 做建议判断

但今天真正完整的链路已经是：

`Real PDFs -> MinerU-first extraction -> AI dry-run review -> Human review -> 340C full validation -> 340D apply plan -> 340E post-human sidecar -> 340F client preview -> 340G audit -> 341A milestone package`

## 4. 当前建议阅读顺序

1. `README.md`
2. 本文档
3. `docs/demo/datefac_ai_review_architecture_339a_zh.md`
4. `docs/demo/datefac_human_reviewed_client_preview_runbook_341b_zh.md`
5. `docs/demo/datefac_human_reviewed_client_preview_architecture_341b_zh.md`

## 5. 337A-338D 建议运行顺序

```powershell
python tools\run_mineru_real_pdf_intake_337a.py --input-pdf-dir D:\_datefac\input\real_test --output-dir D:\_datefac\output\mineru_real_test_337a

python tools\run_mineru_candidate_precision_337b.py --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\mineru_candidate_precision_337b

python tools\run_core_financial_context_repair_337c.py --precision-337b-dir D:\_datefac\output\mineru_candidate_precision_337b --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\core_financial_context_repair_337c

python tools\run_reviewed_strictness_year_alignment_337d.py --context-repair-337c-dir D:\_datefac\output\core_financial_context_repair_337c --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d

python tools\run_deepseek_text_adjudicator_338a.py --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\deepseek_text_adjudicator_338a --limit 50

python tools\run_ai_review_model_ab_338b.py --baseline-338a-dir D:\_datefac\output\deepseek_text_adjudicator_338a --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_model_ab_338b --limit 50

python tools\run_grounded_ai_review_338c.py --ab-338b-dir D:\_datefac\output\ai_review_model_ab_338b --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\grounded_ai_review_338c --limit 50

python tools\run_ai_review_adoption_simulation_338d.py --grounded-ai-review-338c-dir D:\_datefac\output\grounded_ai_review_338c --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_adoption_simulation_338d
```

## 6. 前半段关键结果仍然要记住

### 337A-337D

- 337A 成功解析 `3` 份真实 PDF
- 337A reviewed / needs_review / rejected = `303 / 42 / 2`
- 337B reviewed 从 `303` 降到 `98`
- 337C reviewed 升到 `148`
- 337D reviewed 收紧到 `112`

### 338A-338D

- 338A DeepSeek baseline `NEEDS_MORE_CONTEXT = 33 / 50`
- 338B `gpt-5.5` 在 sampled adjudication 上更强
- 338C grounded review 把 invalid response 进一步压低
- 338D 仍然不给出默认正式 adoption，`suggest_set_ai_review_model_default = false`

## 7. 341A 同步后的新增里程碑数字

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

## 8. 现在最关键的边界

- AI decisions are dry-run only
- human review was used before client preview
- `340F` 是 human-reviewed client preview，不是 official delivery
- `340G` audit passed，但这仍然不是 production-ready
- 当前 benchmark 仍然是有限真实 PDF 样本，不代表规模化稳定性

## 9. 当前最适合打开哪些文件

- `D:\_datefac\output\mineru_real_test_337a\00_batch_summary.json`
- `D:\_datefac\output\reviewed_strictness_year_alignment_337d\reviewed_strictness_year_alignment_337d_summary.json`
- `D:\_datefac\output\ai_review_adoption_simulation_338d\ai_review_adoption_simulation_338d_summary.json`
- `D:\_datefac\output\human_reviewed_client_preview_milestone_341a\human_reviewed_client_preview_milestone_341a.xlsx`
- `D:\_datefac\output\client_preview_export_audit_340g\client_preview_export_audit_340g.xlsx`

## 10. 一句话收尾

> 339A 现在不再只是“AI review runbook”，而是 341A milestone 的前半段解释层，用来说明为什么 AI dry-run 之后仍然必须经过 human review 和 preview audit。 
