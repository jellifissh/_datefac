# DateFac 当前运行手册 333A（中文）

## 1. 适用范围

这份 runbook 只覆盖当前从 `330K2` 到 `332A` 的 sidecar / demo / preview / no write-back 路线。它不是生产运维手册，不授权修改 production pipeline，也不授权改写官方资产。它的目标很明确：让不是原始作者的人，也能在 Windows 本地环境中读懂当前链路、检查输入、运行命令、核对输出，并在不越界的前提下解释当前 reviewed preview 状态。

如果你现在要做的是：

- 新跑一遍 330K2 人工 unit review 打包
- 读取人工填写过的 workbook 做 330K3 dry-run apply
- 基于 dry-run 结果生成 330K4 reviewed preview
- 刷新 331B demo packaging 文档
- 审计 332A release audit 文档一致性

这份 runbook 就是给你用的。如果你现在要做的是：

- 改 parser
- 改 extraction
- 改 delivery
- 改官方资产
- 改生产写回逻辑

那这份 runbook 不适用，应该停下来重新确认任务范围。

## 2. 环境假设

当前文档假设以下前提成立：

- 操作系统：Windows
- 仓库根目录：`D:\_datefac`
- 命令行：PowerShell
- Python 可从当前环境直接调用
- 上游阶段 `330L`、`331A`、`330K2`、`330K3`、`330K4`、`331B`、`332A` 的代码与输出已经存在
- 当前对外状态是 `DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW`
- 当前明确边界是 `client_ready = false`、`production_ready = false`

这里最重要的一点不是“命令能不能跑”，而是“你是不是在对的阶段状态上跑”。如果上游 summary 不满足预期，继续往下跑只会让链路更乱。

## 3. 重要路径

### 3.1 仓库与文档路径

| 类型 | 路径 |
|---|---|
| 仓库根目录 | `D:\_datefac` |
| demo 文档目录 | `D:\_datefac\docs\demo` |
| codex 任务文档目录 | `D:\_datefac\docs\codex_tasks` |

### 3.2 关键输出目录

| 阶段 | 路径 |
|---|---|
| 330L | `D:\_datefac\output\client_style_export_preview_330l` |
| 331A | `D:\_datefac\output\demo_packaging_331a` |
| 330K2 | `D:\_datefac\output\human_unit_review_330k2` |
| 330K3 | `D:\_datefac\output\human_unit_review_apply_simulation_330k3` |
| 330K4 | `D:\_datefac\output\reviewed_export_refresh_330k4` |
| 331B | `D:\_datefac\output\demo_packaging_331b` |
| 332A | `D:\_datefac\output\demo_release_audit_332a` |

### 3.3 关键 workbook 和 summary 文件

最常看的几个文件是：

- `D:\_datefac\output\client_style_export_preview_330l\client_style_export_preview_330l_preview.xlsx`
- `D:\_datefac\output\client_style_export_preview_330l\client_style_export_preview_330l_summary.json`
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_template.xlsx`
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_filled.xlsx`
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_summary.json`
- `D:\_datefac\output\human_unit_review_apply_simulation_330k3\human_unit_review_apply_simulation_330k3_apply_plan.xlsx`
- `D:\_datefac\output\human_unit_review_apply_simulation_330k3\human_unit_review_apply_simulation_330k3_summary.json`
- `D:\_datefac\output\reviewed_export_refresh_330k4\reviewed_export_refresh_330k4_preview.xlsx`
- `D:\_datefac\output\reviewed_export_refresh_330k4\reviewed_export_refresh_330k4_summary.json`
- `D:\_datefac\output\demo_packaging_331b\demo_packaging_331b_summary.json`
- `D:\_datefac\output\demo_release_audit_332a\demo_release_audit_332a_summary.json`

## 4. 当前阶段必须满足的上游输出

### 4.1 330K2 需要什么

330K2 是 human unit review package。它不重新抽取数据，而是把已有链路里需要人工 unit 复核的 21 条记录打包出来。因此它需要：

- `demo_packaging_331a`
- `client_style_export_preview_330l`
- `unit_signal_review_330k`
- `delivery_report_refresh_after_330k_330j2`

在真正运行前，你至少要先确认：

- `client_style_export_preview_330l_summary.json` 存在
- `client_style_export_preview_330l_preview.xlsx` 存在
- `demo_packaging_331a_summary.json` 存在
- 330L summary 里 `trusted_sheet_row_count = 96`
- 330L summary 里 `review_required_sheet_row_count = 21`

### 4.2 330K3 需要什么

330K3 是 human unit review apply simulation。它的作用不是写回，而是把人工 workbook 的决策翻译成 dry-run apply actions。因此它需要：

- `human_unit_review_330k2`
- 填写过的 `human_unit_review_330k2_review_filled.xlsx`
- `demo_packaging_331a`
- `client_style_export_preview_330l`

运行前必须确认人工 workbook 已经填完，而且 `reviewer_decision` 不是空白。

### 4.3 330K4 需要什么

330K4 是 reviewed export refresh。它要做的是根据 330K3 的 dry-run 计划刷新 preview，而不是改原始 330L workbook。它需要：

- `client_style_export_preview_330l`
- `human_unit_review_330k2`
- `human_unit_review_apply_simulation_330k3`

这里最重要的核对点是：330K3 必须先成功产出 apply plan，且 summary 中的 decision 合法，计数符合预期。

### 4.4 331B 需要什么

331B 是 demo packaging refresh after human unit review。它要把 reviewed preview 状态翻译成可展示的文档，因此需要：

- `demo_packaging_331a`
- `reviewed_export_refresh_330k4`
- `human_unit_review_apply_simulation_330k3`
- `human_unit_review_330k2`
- `client_style_export_preview_330l`

如果你发现 331B 的输入来自旧版 331A 文档，而不是新版 330K4 summary，文档叙事就会失真。

### 4.5 332A 需要什么

332A 是 demo release audit。它的作用不是再改数据，而是审核 331B 文档说法。因此它需要：

- `demo_packaging_331b`
- `reviewed_export_refresh_330k4`
- `demo_packaging_331a`
- `docs\demo\` 中的 331B 文档

如果 331B 文档没生成或没更新，332A 只是空审，意义不大。

## 5. 精确运行命令

下面的命令保持当前 Windows 路径原样，不要随意翻译路径、runner 名称或参数名称。

### 5.1 330K2

```powershell
python tools\run_human_unit_review_330k2.py --demo-packaging-dir D:\_datefac\output\demo_packaging_331a --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --unit-signal-review-dir D:\_datefac\output\unit_signal_review_330k --delivery-report-refresh-dir D:\_datefac\output\delivery_report_refresh_after_330k_330j2 --output-dir D:\_datefac\output\human_unit_review_330k2
```

### 5.2 330K3

```powershell
python tools\run_human_unit_review_apply_simulation_330k3.py --filled-review-workbook D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_filled.xlsx --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --demo-packaging-dir D:\_datefac\output\demo_packaging_331a --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --output-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3
```

### 5.3 330K4

```powershell
python tools\run_reviewed_export_refresh_330k4.py --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --apply-simulation-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3 --output-dir D:\_datefac\output\reviewed_export_refresh_330k4
```

### 5.4 331B

```powershell
python tools\run_demo_packaging_331b.py --demo-packaging-331a-dir D:\_datefac\output\demo_packaging_331a --reviewed-export-refresh-dir D:\_datefac\output\reviewed_export_refresh_330k4 --apply-simulation-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3 --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --output-dir D:\_datefac\output\demo_packaging_331b
```

### 5.5 332A

```powershell
python tools\run_demo_release_audit_332a.py --demo-packaging-331b-dir D:\_datefac\output\demo_packaging_331b --reviewed-export-refresh-dir D:\_datefac\output\reviewed_export_refresh_330k4 --demo-packaging-331a-dir D:\_datefac\output\demo_packaging_331a --docs-demo-dir D:\_datefac\docs\demo --output-dir D:\_datefac\output\demo_release_audit_332a
```

## 6. 预期输出目录与关键文件

| 阶段 | 输出目录 | 最值得先看的文件 |
|---|---|---|
| 330K2 | `D:\_datefac\output\human_unit_review_330k2` | `human_unit_review_330k2_review_template.xlsx` |
| 330K3 | `D:\_datefac\output\human_unit_review_apply_simulation_330k3` | `human_unit_review_apply_simulation_330k3_apply_plan.xlsx` |
| 330K4 | `D:\_datefac\output\reviewed_export_refresh_330k4` | `reviewed_export_refresh_330k4_preview.xlsx` |
| 331B | `D:\_datefac\output\demo_packaging_331b` | `demo_packaging_331b_summary.json` |
| 332A | `D:\_datefac\output\demo_release_audit_332a` | `demo_release_audit_332a_summary.json` |

## 7. 当前应该核对的 summary 指标

这一步很关键。你不要先猜逻辑对不对，先看 summary 有没有落在预期范围内。

| 阶段 | 指标 | 当前值 |
|---|---|---:|
| 330L | `prepared_candidate_row_count` | 117 |
| 330L | `trusted_sheet_row_count` | 96 |
| 330L | `review_required_sheet_row_count` | 21 |
| 330K2 | `packaged_unit_review_row_count` | 21 |
| 330K2 | `unit_missing_count` | 18 |
| 330K2 | `unit_conflict_risk_count` | 12 |
| 330K3 | `apply_plan_row_count` | 21 |
| 330K3 | `confirm_unit_count` | 2 |
| 330K3 | `reject_unit_count` | 18 |
| 330K3 | `needs_more_context_count` | 1 |
| 330K4 | `reviewed_trusted_preview_row_count` | 98 |
| 330K4 | `human_rejected_row_count` | 18 |
| 330K4 | `remaining_review_required_after_unit_review_count` | 1 |
| 331B | `project_status` | `DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW` |
| 332A | `overclaim_risk_count` | 0 |
| 332A | `qa_fail_count` | 0 |

这些数字在 README、overview、runbook、demo script 里应该保持一致。如果出现不一致，优先相信 summary，再去修正文档。

## 8. 验证命令

文档任务、代码任务、交接任务都建议先做这几步验证：

```powershell
git status -sb
python -m py_compile <changed_python_files>
python -m pytest <relevant_test_file> -q
```

对于当前这条 demo 链路，额外建议直接检查关键 summary：

```powershell
Get-Content D:\_datefac\output\client_style_export_preview_330l\client_style_export_preview_330l_summary.json
Get-Content D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_summary.json
Get-Content D:\_datefac\output\human_unit_review_apply_simulation_330k3\human_unit_review_apply_simulation_330k3_summary.json
Get-Content D:\_datefac\output\reviewed_export_refresh_330k4\reviewed_export_refresh_330k4_summary.json
Get-Content D:\_datefac\output\demo_packaging_331b\demo_packaging_331b_summary.json
Get-Content D:\_datefac\output\demo_release_audit_332a\demo_release_audit_332a_summary.json
```

核对重点：

- `decision`
- `qa_fail_count`
- `blocking_reasons`
- 是否声明没有 official asset modification

## 9. Git 安全规则

当前阶段的 Git 纪律比命令本身更重要，因为很多任务都只是 sidecar preview 文档或 sidecar 数据产物，最容易犯的错误就是把输出和脏文件一起带进提交。

必须遵守：

- 不要用 `git add -A`
- 不要用 `git add .`
- 只精确 `git add <file>`
- `output/*` 默认不提交
- `input/semantic_adjudicator_responses_*` 默认不提交
- `temp/*` 默认不提交
- 不要顺手 stage 受保护脏文件

如果在 `rebase` 或 `pull` 前被脏文件阻塞，只能按明确范围 stash 指定路径，不能顺手把整个工作区一锅端。

## 10. Protected dirty files

当前明确受保护的脏文件是：

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

这几类内容在当前文档任务和 sidecar 任务中都不应该被修改、stage 或顺手提交。

## 11. 提交前应该做什么

如果某个阶段最终要提交代码或文档，建议按这个顺序：

1. `git status -sb`
2. 确认只有当前任务相关文件被改动
3. 重新跑最小必要验证
4. 核对 summary、doc、路径名和阶段名是否一致
5. 确认 `output/*` 没被 stage
6. 确认 protected dirty files 没被 stage
7. 再逐个执行 `git add <precise-file>`

这一步看起来啰嗦，但它能避免最常见的错误：本来只是交一个 demo 文档任务，结果把本地受保护脏文件也一起带上去了。

## 12. 永远不要 stage 的东西

当前至少有以下内容不应进入普通提交：

- `output/*`
- `temp/*`
- `input/semantic_adjudicator_responses_*`
- 当前任务无关的 production code
- official assets
- protected dirty files
- 本地人工填写的中间 workbook，除非任务明确要求提交模板本身的代码生成逻辑，而不是 workbook 产物

## 13. 故障排查 checklist

命令失败时，不要第一反应就改代码。先按下面顺序排查：

1. 上游输出目录是否真的存在
2. workbook 路径是否写对
3. `review_filled.xlsx` 是否真的填写了关键列
4. summary 里的 `decision` 是否处于 ready 状态
5. summary 里的 `qa_fail_count` 是否为 0
6. 是否把 330L preview 和 330K4 reviewed preview 混用
7. 是否把 331A 文档和 331B 文档混用
8. 是否误把 release audit 文档当成源数据
9. `git status -sb` 是否暴露了意外变更
10. 是否遇到 `.git/index.lock` 或权限问题

尤其要注意：330K4 的 preview 是 reviewed preview，不是 330L 原始 preview 的直接替代物。看文件时要明确自己看的是哪一版。

## 14. 当前运行边界

最后再强调一次当前 runbook 的边界词，因为这些词应该贯穿 README、overview、runbook 和对外解释：

- sidecar
- demo
- preview
- no write-back
- human review
- current limitations

它们不是装饰词，而是当前工程状态的真实边界。如果这些词从文档里消失，就很容易把项目说过头。

## 15. 交接时的最小检查顺序

如果你是把项目交给下一位操作者，或者过一段时间之后再自己接回来，建议用下面这个顺序重新建立上下文：

1. 先看 `README.md`，确认当前公开叙事还是 reviewed preview 而不是正式交付。
2. 再看 `docs/demo/datefac_project_overview_333a_zh.md`，把整体链路、阶段历史和当前指标重新对齐。
3. 再看 `docs/demo/datefac_current_runbook_333a_zh.md`，确认命令、输入目录和输出目录没有记混。
4. 再打开 330L、330K2、330K3、330K4、331B、332A 的 summary，核对 `decision` 和 `qa_fail_count`。
5. 最后才去打开 workbook，看 trusted、review_required、human rejected 和 reviewed preview 的具体记录。

这个顺序的作用，是先恢复边界认知，再恢复操作认知，最后才进入数据细节。很多交接失败并不是因为命令不会跑，而是因为一上来就盯着 workbook 看数字，却忘了当前链路本质上是 sidecar demo preview、坚持 human review、坚持 no write-back、并且有明确 current limitations 的一条演示路线。

再补一句最实用的提醒：只要你一时分不清某个文件到底是“源代码、文档、summary、workbook 还是 output 产物”，就不要急着修改或 stage。先回到这份 runbook 看路径分类，再决定下一步。对当前项目来说，慢一拍确认边界，通常比快一步改错地方更安全。
