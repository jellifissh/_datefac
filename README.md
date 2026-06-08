# DateFac

## 中文

### 项目定位

DateFac 是一个面向券商研报 PDF 的本地结构化与可信预览治理项目。它当前最有价值的部分，不是单纯“把表格抽出来”，而是把抽取后的候选行继续做 provenance 保留、风险分流、人工复核隔离、预览刷新和对外叙事审计。

当前仓库已经具备：

- MinerU-first 的真实 PDF 预览 intake
- 规则驱动的 candidate precision 校准
- 核心财务表上下文修复与 unit 补全
- reviewed strictness 与 year alignment QA
- AI 文本裁决 dry-run、A/B 对比、grounded schema 收紧、adoption simulation

当前仓库仍然不是：

- `client-ready`
- `production-ready`
- 正式生产写回系统
- 无需人工复核的自动交付系统

### 当前状态

- `project_status` for 337A intake: `LOCAL_PREVIEW_ONLY_MINERU_FIRST`
- 337D decision: `REVIEWED_STRICTNESS_YEAR_ALIGNMENT_337D_READY`
- 338D decision: `AI_REVIEW_ADOPTION_SIMULATION_338D_READY`
- `client_ready = false`
- `production_ready = false`
- AI 决策当前仅用于 dry-run 评估与 adoption simulation，不写回上游 workbook 或 official assets

### 当前真实 PDF -> 预览链路

功能优先，阶段号其次：

1. 把真实研报 PDF 放进 `D:\_datefac\input\real_test`
2. 运行 MinerU-first intake，拿到原始解析与 DateFac debug 预览
3. 做 precision calibration，压缩明显噪声 candidate
4. 做 core financial context repair，补充表角色与单位上下文
5. 做 reviewed strictness / year alignment QA，保守收紧 reviewed 集合
6. 如需 AI 文本裁决，先跑 DeepSeek baseline dry-run
7. 用 `AI_REVIEW_MODEL` 对比 DeepSeek flash，做 A/B 评估
8. 做 grounded AI review，要求原始证据与上下文引用更严格
9. 做 adoption simulation，只模拟哪些模型结论可以被安全吸收

对应命令：

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

### 最新关键指标

真实 PDF intake 与规则修复：

- 337A 使用 MinerU 成功解析 `3` 份真实 PDF
- 337A metric candidates:
  - `352620_1 = 134`
  - `352906_1 = 111`
  - `356439_1 = 102`
- 337A reviewed / needs_review / rejected = `303 / 42 / 2`
- 337B reviewed 从 `303` 降到 `98`
- 337C reviewed 变为 `148`，其中：
  - `table_role_repair_count = 35`
  - `unit_filled_count = 119`
- 337D reviewed 变为 `112`
  - `year_alignment_repaired_count = 33`
  - `percent_amount_guard_downgraded_count = 4`
  - `reviewed_duplicate_removed_count = 27`

AI dry-run 与 adoption simulation：

- 338A DeepSeek flash baseline:
  - `low_confidence = 34 / 50`
  - `NEEDS_MORE_CONTEXT = 33 / 50`
- 338B `AI_REVIEW_MODEL` vs DeepSeek flash:
  - baseline model = `deepseek-v4-flash`
  - new model = `gpt-5.5`
  - `low_confidence_new = 0 / 50`
  - `needs_more_context_new = 3 / 50`
  - `invalid_response_count_new = 3`
- 338C grounded review:
  - `invalid_response_count_338c = 1`
  - `grounding_source BOTH = 49`
  - `final_recommendation = PROMPT_CONTEXT_STILL_TOO_WEAK`
- 338D adoption simulation:
  - `ACCEPT_MODEL_CONFIRM = 39`
  - `ACCEPT_MODEL_REJECT = 3`
  - `HOLD_FOR_HUMAN_REVIEW = 3`
  - `REJECT_BY_DETERMINISTIC_RULE = 4`
  - `INVALID_MODEL_RESPONSE = 1`
  - `deterministic_rule_override_count = 0`
  - `suggest_set_ai_review_model_default = false`

### 模型与规则角色

- MinerU: 当前真实 PDF 版面与表格抽取的主解析器
- Deterministic rules: 当前最优先的硬约束层，负责单位、重复、百分比误映射、明显噪声等安全拦截
- `AI_REVIEW_MODEL`: 文本裁决候选模型，用于 ambiguous rows 的 dry-run 评估
- DeepSeek flash: 当前保守 baseline / fallback
- Vision model: 预留给未来版面、截图、图表或 image-table 不确定性场景，不是当前主线
- Human review: held / invalid / conflicting rows 的最终安全层

### 当前可安全宣称的能力

- 支持真实研报 PDF 的 MinerU-first preview intake
- 支持 candidate precision calibration
- 支持核心财务表上下文修复与 unit 相关保守增强
- 支持 reviewed strictness、year alignment 与 suspicious row QA
- 支持 AI 文本裁决 dry-run、A/B 评估、grounded schema 收紧、adoption simulation
- 支持 no-write-back 的 sidecar 预览治理链路

### 当前禁止宣称的内容

- 已 client-ready
- 已 production-ready
- 100% 准确
- fully automatic commercial SaaS
- 可直接用于投资决策
- 不再需要人工复核
- AI 决策已成为最终正式结果

### 推荐阅读顺序

1. `README.md`
2. `docs/demo/（中文项目总览）datefac_project_overview_333a_zh.md`
3. `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_zh.md`
4. `docs/demo/datefac_ai_review_architecture_339a_zh.md`
5. `docs/demo/datefac_demo_release_checklist_332a.md`
6. `docs/demo/datefac_interview_talking_points_332a.md`

### 当前限制

- 当前链路仍然是 `sidecar / demo / preview / no-write-back`
- 真实 PDF intake 已可运行，但不代表生产可交付
- AI review 仅是 dry-run 与 adoption simulation，不会写回
- `gpt-5.5` 在 338B/338C 上表现更强，但 338D 仍不建议直接设为默认正式裁决器
- 更大样本 benchmark、部署、安全、权限、数据隔离、持续运维能力仍未闭环

## English

### Project Positioning

DateFac is a local engineering project for financial research PDF structuring and trust-governed preview generation. Its most important value is not merely “extract tables from PDFs,” but “preserve provenance, route risk conservatively, isolate human review, simulate adoption safely, and present the resulting preview state without overclaiming.”

The repository now includes:

- MinerU-first real PDF intake preview
- rule-based candidate precision calibration
- core financial context repair and unit recovery
- reviewed strictness and year-alignment QA
- AI text adjudication dry-runs, A/B evaluation, grounded schema tightening, and adoption simulation

It still is not:

- client-ready
- production-ready
- a production write-back system
- a no-human-review automation claim

### Current Status

- 337A status: `LOCAL_PREVIEW_ONLY_MINERU_FIRST`
- 337D decision: `REVIEWED_STRICTNESS_YEAR_ALIGNMENT_337D_READY`
- 338D decision: `AI_REVIEW_ADOPTION_SIMULATION_338D_READY`
- `client_ready = false`
- `production_ready = false`
- AI model decisions remain dry-run only and do not write back upstream

### Current Real-PDF Pipeline

1. Put real research PDFs in `D:\_datefac\input\real_test`
2. Run MinerU-first intake
3. Run precision calibration
4. Run core financial context repair
5. Run reviewed strictness and year-alignment QA
6. Optionally run DeepSeek text adjudication baseline
7. Run `AI_REVIEW_MODEL` A/B evaluation against DeepSeek flash
8. Run grounded AI review
9. Run AI adoption simulation

The exact commands are shown in the Chinese section above and reused in the runbooks.

### Latest Headline Metrics

Real PDF parsing and rule repair:

- 337A parsed 3 real PDFs successfully with MinerU
- 337A metric candidates:
  - `352620_1 = 134`
  - `352906_1 = 111`
  - `356439_1 = 102`
- 337A reviewed / needs_review / rejected = `303 / 42 / 2`
- 337B reduced reviewed rows from `303` to `98`
- 337C raised reviewed rows to `148`
  - `table_role_repair_count = 35`
  - `unit_filled_count = 119`
- 337D reduced reviewed rows to `112`
  - `year_alignment_repaired_count = 33`
  - `percent_amount_guard_downgraded_count = 4`
  - `reviewed_duplicate_removed_count = 27`

AI dry-run and adoption simulation:

- 338A DeepSeek flash baseline:
  - `low_confidence = 34 / 50`
  - `NEEDS_MORE_CONTEXT = 33 / 50`
- 338B `AI_REVIEW_MODEL` A/B:
  - baseline = `deepseek-v4-flash`
  - new model = `gpt-5.5`
  - `low_confidence_new = 0 / 50`
  - `needs_more_context_new = 3 / 50`
  - `invalid_response_count_new = 3`
- 338C grounded review:
  - `invalid_response_count_338c = 1`
  - `grounding_source BOTH = 49`
  - `final_recommendation = PROMPT_CONTEXT_STILL_TOO_WEAK`
- 338D adoption simulation:
  - `ACCEPT_MODEL_CONFIRM = 39`
  - `ACCEPT_MODEL_REJECT = 3`
  - `HOLD_FOR_HUMAN_REVIEW = 3`
  - `REJECT_BY_DETERMINISTIC_RULE = 4`
  - `INVALID_MODEL_RESPONSE = 1`
  - `deterministic_rule_override_count = 0`
  - `suggest_set_ai_review_model_default = false`

### Role Split

- MinerU: primary parser for layout and table extraction
- deterministic rules: highest-priority safety layer for units, duplicates, percentage-as-amount guards, and obvious noise
- `AI_REVIEW_MODEL`: candidate text adjudicator for ambiguous rows
- DeepSeek flash: conservative fallback / baseline
- vision models: reserved for future layout, screenshot, or image-table uncertainty
- human review: final safety layer for held, invalid, or conflicting rows

### Safe Claims

- real PDF preview intake exists and runs with MinerU-first routing
- the project performs conservative rule repair before AI review
- AI review is available as dry-run evaluation only
- grounded review and adoption simulation are explicit no-write-back layers

### Unsafe Claims

- client-ready
- production-ready
- 100% accurate
- fully automatic commercial SaaS
- direct investment-decision suitability
- no human review needed
- AI decisions are final

### Recommended Reading

1. `README.md`
2. `docs/demo/（英文项目总览）datefac_project_overview_333a_en.md`
3. `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_en.md`
4. `docs/demo/datefac_ai_review_architecture_339a_en.md`
5. `docs/demo/datefac_demo_release_checklist_332a.md`
6. `docs/demo/datefac_interview_talking_points_332a.md`

### Current Limitations

- the current path is still sidecar, demo, preview, and no-write-back
- the real PDF intake is useful for guarded preview work, not production delivery
- AI review remains dry-run and adoption-simulation only
- `gpt-5.5` looks stronger in 338B and 338C, but 338D still does not recommend making it the default adjudicator
- broader benchmarking, deployment, security, permissions, data isolation, and operational hardening remain unfinished
