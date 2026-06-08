# DateFac 当前运行手册 333A/339A 同步版

## 1. 适用范围

这份 runbook 覆盖当前真实 PDF 预览主链路：

- 337A MinerU-first intake
- 337B precision calibration
- 337C core financial context repair
- 337D reviewed strictness / year alignment QA
- 338A DeepSeek baseline dry-run
- 338B `AI_REVIEW_MODEL` A/B
- 338C grounded AI review
- 338D adoption simulation

这不是生产运维手册。

它不授权你：

- 修改生产 pipeline
- 修改 parser / extraction / delivery 代码
- 修改 official assets
- 修改 output 产物并提交

## 2. 运行前提

默认环境：

- Windows
- repo 根目录：`D:\_datefac`
- PowerShell
- 本地 Python 可用
- 337A-338D 代码已经存在

当前文档必须统一承认：

- `client_ready = false`
- `production_ready = false`
- AI 结论当前仅为 dry-run
- no-write-back 仍然有效

## 3. 关键路径

输入目录：

- `D:\_datefac\input\real_test`

关键输出目录：

- `D:\_datefac\output\mineru_real_test_337a`
- `D:\_datefac\output\mineru_candidate_precision_337b`
- `D:\_datefac\output\core_financial_context_repair_337c`
- `D:\_datefac\output\reviewed_strictness_year_alignment_337d`
- `D:\_datefac\output\deepseek_text_adjudicator_338a`
- `D:\_datefac\output\ai_review_model_ab_338b`
- `D:\_datefac\output\grounded_ai_review_338c`
- `D:\_datefac\output\ai_review_adoption_simulation_338d`

## 4. 当前推荐运行顺序

### 4.1 真实 PDF intake

```powershell
python tools\run_mineru_real_pdf_intake_337a.py --input-pdf-dir D:\_datefac\input\real_test --output-dir D:\_datefac\output\mineru_real_test_337a
```

### 4.2 candidate precision calibration

```powershell
python tools\run_mineru_candidate_precision_337b.py --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\mineru_candidate_precision_337b
```

### 4.3 core financial context repair

```powershell
python tools\run_core_financial_context_repair_337c.py --precision-337b-dir D:\_datefac\output\mineru_candidate_precision_337b --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\core_financial_context_repair_337c
```

### 4.4 reviewed strictness / year alignment

```powershell
python tools\run_reviewed_strictness_year_alignment_337d.py --context-repair-337c-dir D:\_datefac\output\core_financial_context_repair_337c --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d
```

### 4.5 AI baseline dry-run

```powershell
python tools\run_deepseek_text_adjudicator_338a.py --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\deepseek_text_adjudicator_338a --limit 50
```

### 4.6 A/B evaluation

```powershell
python tools\run_ai_review_model_ab_338b.py --baseline-338a-dir D:\_datefac\output\deepseek_text_adjudicator_338a --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_model_ab_338b --limit 50
```

### 4.7 grounded review

```powershell
python tools\run_grounded_ai_review_338c.py --ab-338b-dir D:\_datefac\output\ai_review_model_ab_338b --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\grounded_ai_review_338c --limit 50
```

### 4.8 adoption simulation

```powershell
python tools\run_ai_review_adoption_simulation_338d.py --grounded-ai-review-338c-dir D:\_datefac\output\grounded_ai_review_338c --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_adoption_simulation_338d
```

## 5. 每一步跑完后先看什么

### 337A 看什么

- `00_batch_summary.json`
- `real_test_mineru_client_export_337a.xlsx`
- 每个 PDF 的 `datefac_debug/<pdf_stem>/document_summary.json`

当前应看到：

- `pdf_found_count = 3`
- `mineru_success_count = 3`
- `reviewed_count = 303`
- `needs_review_count = 42`
- `rejected_or_excluded_count = 2`

### 337B 看什么

- `mineru_candidate_precision_337b_summary.json`

当前应看到：

- `reviewed_before_count = 303`
- `reviewed_after_count = 98`

### 337C 看什么

- `core_financial_context_repair_337c_summary.json`

当前应看到：

- `reviewed_after_count = 148`
- `table_role_repair_count = 35`
- `unit_filled_count = 119`

### 337D 看什么

- `reviewed_strictness_year_alignment_337d_summary.json`
- `real_test_mineru_client_export_337d.xlsx`

当前应看到：

- `reviewed_after_count = 112`
- `year_alignment_repaired_count = 33`
- `reviewed_duplicate_removed_count = 27`
- `qa_fail_count = 0`

### 338A 看什么

- `deepseek_text_adjudicator_338a_summary.json`

当前应看到：

- `model_name = deepseek-v4-flash`
- `low_confidence_count = 34`
- `needs_more_context_count = 33`

### 338B 看什么

- `ai_review_model_ab_338b_summary.json`

当前应看到：

- `new_model_name = gpt-5.5`
- `low_confidence_count_new = 0`
- `needs_more_context_count_new = 3`
- `invalid_response_count_new = 3`

### 338C 看什么

- `grounded_ai_review_338c_summary.json`

当前应看到：

- `invalid_response_count_338c = 1`
- `grounding_source_counts.BOTH = 49`

### 338D 看什么

- `ai_review_adoption_simulation_338d_summary.json`
- `ai_review_adoption_simulation_338d_plan.xlsx`

当前应看到：

- `accept_model_confirm_count = 39`
- `accept_model_reject_count = 3`
- `hold_for_human_review_count = 3`
- `invalid_model_response_count = 1`
- `deterministic_rule_override_count = 0`

## 6. 当前必须理解的边界

这几条不能丢：

- 当前是 sidecar preview，不是 production
- AI 结论是 dry-run，不是正式写回
- deterministic rules 优先于模型
- human review 仍然必要
- `AI_REVIEW_MODEL` 现在只是候选默认文本裁决器，不是已批准默认生产模型

## 7. 常见误区

### 误区 1

“337A 成功解析 3 个 PDF，所以系统已经可交付。”

不对。337A 只证明真实 PDF intake 可以跑通，并不等于正式可交付。

### 误区 2

“338B/338C 里 `gpt-5.5` 表现更好，所以可以直接默认替换。”

不对。338D 明确给出：

- `suggest_set_ai_review_model_default = false`

### 误区 3

“AI adoption simulation 已经是正式采用。”

不对。它只是 simulation，不是 write-back。

## 8. Git 纪律

当前文档同步任务里：

- 不要 `git add -A`
- 不要 `git add .`
- 不要 stage `output/*`
- 不要 stage protected dirty files

受保护脏文件仍然包括：

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## 9. 最小检查顺序

每次接手前建议按这个顺序：

1. `git status -sb`
2. 看 `README.md`
3. 看本 runbook
4. 看 `datefac_ai_review_architecture_339a_zh.md`
5. 看 337A / 337D / 338D 三个 summary
6. 再决定要不要打开 Excel

## 10. 一句收尾

> 当前 runbook 的核心不是教你“怎样把系统说得更强”，而是教你“怎样在真实能力范围内把系统跑对、看对、讲对”。
