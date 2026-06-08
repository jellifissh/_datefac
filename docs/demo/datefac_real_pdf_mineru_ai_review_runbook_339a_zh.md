# DateFac 真实 PDF + MinerU + AI Review 运行手册 339A（中文）

## 1. 这份手册是干什么的

这份手册只讲当前最现实的一条链路：

> 从真实研报 PDF 出发，先用 MinerU 解析，再用规则修复与严格 QA 收紧结果，最后可选地做 AI 文本裁决 dry-run。

这不是生产手册，不授权写回 official assets，也不授权把模型结论当正式结果。

## 2. 先决条件

- 输入目录：`D:\_datefac\input\real_test`
- 当前示例 PDF 共 `3` 份
- 本地已有 MinerU 可执行文件
- Python 可运行

## 3. 当前建议命令顺序

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

## 4. 每一步最关键看什么

### 337A

看：

- `00_batch_summary.json`
- `real_test_mineru_client_export_337a.xlsx`

当前结果：

- 3 份 PDF 全部成功
- reviewed `303`
- needs_review `42`
- rejected `2`

### 337B

看：

- `mineru_candidate_precision_337b_summary.json`

当前结果：

- reviewed 从 `303` 压到 `98`

### 337C

看：

- `core_financial_context_repair_337c_summary.json`

当前结果：

- reviewed 变为 `148`
- `unit_filled_count = 119`

### 337D

看：

- `reviewed_strictness_year_alignment_337d_summary.json`

当前结果：

- reviewed 收紧到 `112`

### 338A-338D

核心结论：

- DeepSeek flash baseline 比较保守，低置信度很多
- `gpt-5.5` 文本裁决更强，但仍有 invalid cases
- grounded schema 能继续收紧无效输出
- adoption simulation 仍未建议直接默认采用

## 5. 当前最重要的边界

- 当前不是 client-ready
- 当前不是 production-ready
- AI 结论不写回
- deterministic rules 优先于模型
- human review 仍然必要

## 6. 推荐先打开的文件

- `README.md`
- `docs/demo/datefac_ai_review_architecture_339a_zh.md`
- `D:\_datefac\output\mineru_real_test_337a\00_batch_summary.json`
- `D:\_datefac\output\reviewed_strictness_year_alignment_337d\reviewed_strictness_year_alignment_337d_summary.json`
- `D:\_datefac\output\ai_review_adoption_simulation_338d\ai_review_adoption_simulation_338d_summary.json`

## 7. 一句话总结

> 这条链路的目标不是把 AI 包装成正式决定者，而是把真实 PDF 到可信 preview 的约束过程跑清楚。
