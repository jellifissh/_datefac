# DateFac 新手指南 333A/339A 同步版

## 1. 先记住项目现在是什么

DateFac 现在不是“已经能自动给客户交付结果”的系统。

它现在是一个本地、侧车式、可追溯的研报 PDF 预览治理链路，重点在：

- 用 MinerU 先把真实 PDF 解析出来
- 用保守规则把 candidate 做降噪和修复
- 把不够稳的行继续留在 review 或 reject
- 把 AI 裁决当成 dry-run 评估，而不是正式写回
- 把最终结果组织成可解释的 preview 与文档

一句话理解：

> DateFac 当前最强的能力，不是“自动得出最终答案”，而是“把真实 PDF 抽取后的不确定性管理清楚”。

## 2. 现在已经多了什么新能力

相比早期只讲 330L-335A 的 reviewed preview 链路，现在文档必须把下面这些能力也算进去：

- 336A：原始 PDF 文件夹 smoke runner
- 336B：单 PDF debug package
- 337A：MinerU-first 真实 PDF intake
- 337B：candidate precision calibration
- 337C：核心财务表上下文修复
- 337D：reviewed strictness、year alignment、可疑行 QA
- 338A：DeepSeek 文本裁决 baseline dry-run
- 338B：`AI_REVIEW_MODEL` 对比 DeepSeek flash 的 A/B 评估
- 338C：grounded AI review schema tightening
- 338D：AI review adoption simulation

这些能力都还是 sidecar / demo / preview / no-write-back 范围内。

## 3. 最简单的真实 PDF 流程怎么理解

不要先背阶段号，先按功能理解：

1. 你把真实研报 PDF 放进 `D:\_datefac\input\real_test`
2. MinerU 负责先做版面和表格抽取
3. DateFac 再把抽出的 candidate 做规则校准和修复
4. 把更稳的留在 reviewed preview，把不稳的继续压回 review 或 reject
5. 如需 AI 裁决，只做 dry-run 和 adoption simulation

你可以把这条链路想成：

```text
真实 PDF
-> MinerU 解析
-> candidate 降噪
-> 表格上下文修复
-> reviewed 严格化 QA
-> AI dry-run 裁决
-> adoption simulation
-> 可解释 preview
```

## 4. 当前最重要的事实

这些数字现在在文档里必须一致：

- 337A 成功解析真实 PDF `3` 份
- 337A metric candidates:
  - `352620_1 = 134`
  - `352906_1 = 111`
  - `356439_1 = 102`
- 337A `reviewed / needs_review / rejected = 303 / 42 / 2`
- 337B reviewed 从 `303` 降到 `98`
- 337C reviewed 变成 `148`
- 337C `unit_filled_count = 119`
- 337D reviewed 变成 `112`
- 338A DeepSeek baseline:
  - `low_confidence = 34 / 50`
  - `NEEDS_MORE_CONTEXT = 33 / 50`
- 338B `gpt-5.5` 对比 DeepSeek:
  - `low_confidence = 0 / 50`
  - `NEEDS_MORE_CONTEXT = 3 / 50`
  - `invalid_response = 3`
- 338C:
  - `invalid_response = 1`
  - `grounding_source BOTH = 49`
- 338D:
  - `ACCEPT_MODEL_CONFIRM = 39`
  - `ACCEPT_MODEL_REJECT = 3`
  - `HOLD_FOR_HUMAN_REVIEW = 3`
  - `INVALID_MODEL_RESPONSE = 1`

## 5. 模型各自干什么

- MinerU：主解析器，负责真实 PDF 的版面和表格抽取
- Deterministic rules：最先执行的硬规则，负责单位、重复、明显噪声、百分比误映射等安全问题
- `AI_REVIEW_MODEL`：当前主文本裁决候选模型
- DeepSeek flash：保守 baseline / fallback
- Vision model：未来处理截图、图表、image-table、布局不确定性的候选工具
- Human review：最终安全层

最重要的一句：

> AI 现在不是最终决定者，只是 dry-run 裁决候选层。

## 6. 现在最该怎么跑

真实 PDF 的当前最简运行顺序：

```powershell
python tools\run_mineru_real_pdf_intake_337a.py --input-pdf-dir D:\_datefac\input\real_test --output-dir D:\_datefac\output\mineru_real_test_337a

python tools\run_mineru_candidate_precision_337b.py --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\mineru_candidate_precision_337b

python tools\run_core_financial_context_repair_337c.py --precision-337b-dir D:\_datefac\output\mineru_candidate_precision_337b --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\core_financial_context_repair_337c

python tools\run_reviewed_strictness_year_alignment_337d.py --context-repair-337c-dir D:\_datefac\output\core_financial_context_repair_337c --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d
```

如果你要继续看 AI dry-run：

```powershell
python tools\run_deepseek_text_adjudicator_338a.py --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\deepseek_text_adjudicator_338a --limit 50

python tools\run_ai_review_model_ab_338b.py --baseline-338a-dir D:\_datefac\output\deepseek_text_adjudicator_338a --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_model_ab_338b --limit 50

python tools\run_grounded_ai_review_338c.py --ab-338b-dir D:\_datefac\output\ai_review_model_ab_338b --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\grounded_ai_review_338c --limit 50

python tools\run_ai_review_adoption_simulation_338d.py --grounded-ai-review-338c-dir D:\_datefac\output\grounded_ai_review_338c --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_adoption_simulation_338d
```

## 7. 最值得先打开哪些文件

先看这几个：

- `README.md`
- `docs/demo/（中文项目总览）datefac_project_overview_333a_zh.md`
- `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_zh.md`
- `docs/demo/datefac_ai_review_architecture_339a_zh.md`

再看输出：

- `D:\_datefac\output\mineru_real_test_337a\00_batch_summary.json`
- `D:\_datefac\output\reviewed_strictness_year_alignment_337d\reviewed_strictness_year_alignment_337d_summary.json`
- `D:\_datefac\output\ai_review_adoption_simulation_338d\ai_review_adoption_simulation_338d_summary.json`

如果要看 Excel：

- `D:\_datefac\output\mineru_real_test_337a\real_test_mineru_client_export_337a.xlsx`
- `D:\_datefac\output\reviewed_strictness_year_alignment_337d\real_test_mineru_client_export_337d.xlsx`
- `D:\_datefac\output\ai_review_adoption_simulation_338d\ai_review_adoption_simulation_338d_plan.xlsx`

## 8. 现在绝对不要误解成什么

不要把当前状态理解成：

- 已经 client-ready
- 已经 production-ready
- AI 已经替代人工
- 模型结论已经正式写回
- 系统已经 100% 准确

现在允许说的是：

- 不是 client-ready
- 不是 production-ready
- AI 决策仍然是 dry-run only
- human review 仍然必要

## 9. 如果你只记一条

> DateFac 现在是一条“真实 PDF -> MinerU -> 规则修复 -> 严格化 QA -> AI dry-run -> adoption simulation -> 可信 preview”的工程链路，而不是正式生产写回系统。
