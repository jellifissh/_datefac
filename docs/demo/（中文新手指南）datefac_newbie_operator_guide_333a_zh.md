# DateFac 新手操作指南 333A（中文）

## 0. 这份文档是给谁看的

这份文档是写给“项目拥有者本人、但不是项目原始作者”的。假设你能打开电脑、能运行命令、会看 Excel，但是你并没有参与 DateFac 这套 330L 到 332A 的实现过程，也不熟悉里面每个阶段的细节。你想知道的不是“某个函数内部怎么写”，而是：

- 这个项目到底在做什么
- 现在能做到什么、不能做到什么
- 每个阶段的输入和输出在哪
- 我需要打开哪些文件，避开哪些文件
- 人工 unit review 到底怎么填
- 为什么明明看起来已经很完整了，项目还是不能说已经达到生产级就绪
- 如果以后要把这个项目拿去试点、拿去展示、拿去接小额人工兜底单，应该怎么说、怎么做、怎么避坑

如果你是第一次接触这个项目，请按这份文档一步一步看，不要急着跑命令，不要急着改 Excel，更不要急着改 `data/` 下的正式资产。

---

## 1. 这个项目到底是干嘛的

一句话版本：

> DateFac 是一个“围绕券商研报 PDF 指标抽取结果做可信化治理、人工复核隔离、预览刷新和 demo 包装”的项目。

再展开一点：

很多人理解 PDF 抽取项目时，只盯着一个问题：能不能把表格抽出来、把数字识别出来。但 DateFac 当前 demo 的重点不只是“抽”，而是“抽完以后怎么负责任地处理这些结果”。

为什么要这样做？因为现实里最危险的错误通常不是“完全抽不到”，而是：

- 抽出来一个看上去很像真的数字
- 行标签也像对的
- 但是 unit 丢了、year 错了、表头修复过头了、或者其实那一行根本不是正式财务预测表
- 如果直接把这种行推进 trusted，再包成一个像正式交付物的 Excel，就很容易制造“看起来正规、其实风险很高”的结果

所以 DateFac 当前这条链路做的是：

1. 从 parser / 结构化结果里拿到 candidate rows
2. 对这些 candidate 做 trust routing
3. 把明显可信的和需要人工复核的分开
4. 对 unit 风险行专门生成人工复核工作簿
5. 人工填完以后，先做 dry-run apply simulation
6. 再生成 reviewed preview，而不是直接改正式产物
7. 最后把当前状态包成 overview / README / resume / demo script / release audit

也就是说，DateFac 现在是“有治理边界的 demo 工程”，不是“已经全自动交付的商业系统”。

---

## 2. 为什么金融研报 PDF 提取不能只靠 parser

很多新手会有一个误区：只要 OCR 够强、表格识别够强，抽取问题就算解决了。实际不是这样。

### 2.1 parser 解决的是“看见什么”

parser 的本职工作是：

- 识别表格边界
- 切行切列
- 读出文本
- 尽量恢复结构

这很重要，但它解决的是“机器看见了什么”。

### 2.2 业务可用性还要解决“这东西能不能信”

真正要交给人看、交给后续流程用的时候，还要回答下面这些问题：

- 这一行到底是不是我要的核心指标
- 这一列年份是不是跟 value 对上了
- 这一行的 unit 是不是完整
- 这个 unit 是真 unit，还是图注、说明文字、对比公司表里的噪声
- 这一行是应该 trusted，还是应该 review_required
- 如果人工看完说不行，系统能不能把它从 trusted preview 里隔离出去

这些问题不是 parser 一层能独立解决的。即使 parser 输出看起来“很像对的”，也可能仍然不安全。

### 2.3 一个很典型的错误场景

例如行里出现 `EPS`、`PE`、`总市值（亿元）`、`公司代码` 混在一起。parser 可以把这些词都读出来，但它并不知道：

- 这是不是对比公司估值表
- 这是不是核心预测表
- 这行里的数字到底对应 EPS 还是 PE 还是别的列
- `亿元` 到底是不是 EPS 的 unit，还是总市值这一列的 unit

所以 DateFac 不把“parser 读出来了”直接等价成“这条记录可信”。

### 2.4 DateFac 的核心态度

DateFac 当前的工程态度是保守的：

- 宁可先留 review_required
- 也不要过早推进 trusted
- 宁可要求人工看一眼
- 也不要把弱证据包装成看起来很正式的结果

这就是为什么它现在是一个“可信化治理 demo”，而不是一个“全自动商业成品”。

---

## 3. 什么是 trusted / review_required / rejected

这是整个项目最核心的三个概念。

### 3.1 trusted

`trusted` 的意思不是“永远绝对正确”，而是：

- 当前证据比较强
- provenance 比较完整
- 风险标记比较干净
- 在当前 sidecar 规则下，可以被放进 trusted preview

注意，这里是 `trusted preview`，不是“正式生产交付”。

### 3.2 review_required

`review_required` 的意思是：

- 当前不能放心自动推进 trusted
- 需要人工进一步看
- 常见原因包括：
  - unit 缺失
  - unit 冲突
  - row_text 噪声较重
  - year 推断风险高
  - 表头修复过重
  - 语义证据不够强

### 3.3 rejected

在当前 330K2 -> 330K3 -> 330K4 这条链里，`rejected` 主要是“人工 unit review 之后，被明确判定不应该进入 trusted preview 的行”。

这些行会被隔离出来，而不是继续留在 trusted 里“凑数”。

### 3.4 为什么 rejected 很重要

很多 demo 会怕难看，不愿意展示 rejected。DateFac 恰恰相反：它把 rejected 明确展示出来，原因是：

- 这说明系统知道哪些东西不能乱信
- 这说明人工 review 没有被伪装成自动正确
- 这说明 preview 的可信度不是靠“藏错误”得来的

从工程可信度看，能诚实展示 rejected，比盲目扩大 trusted 更重要。

---

## 4. 什么是 unit review

`unit review` 指的是：专门针对“单位相关风险”做人工复核。

为什么要单独做这个阶段？因为单位问题在财务数据里极其致命：

- 同一个数字，如果 unit 是 `RMB_mn` 和 `RMB_bn`，意义完全不同
- `percent`、`times`、`RMB/share`、`USD/kW`、`MW` 这种量纲，一旦搞错，下游所有解释都错
- 某些行本身就没有明确 unit，只能靠上下文推断，这种时候自动推进 trusted 风险很高

所以 330K2 这一步不是“修所有问题”，而是先把 unit 风险行单独打包出来，让人看。

### 4.1 unit review 不是在修 parser

这点要特别清楚：

- unit review 不是回头去改 OCR
- 不是重新跑 parser
- 不是改 production pipeline
- 不是改正式 mapping 规则

它只是把“当前这条行在当前证据下是否能认 unit”这件事交给人工判断。

---

## 5. 什么是 dry-run apply

`dry-run apply` 的意思是：先模拟“如果采纳人工复核结果，会发生什么”，但不真正写回。

在 330K3 里，系统会把人工复核 workbook 里的决定转成动作类型，例如：

- `CONFIRM_UNIT -> WOULD_CONFIRM_OR_SET_UNIT`
- `REJECT_UNIT -> WOULD_REJECT_FROM_TRUSTED_EXPORT`
- `KEEP_UNIT_UNKNOWN -> WOULD_KEEP_UNIT_UNKNOWN_REVIEW_REQUIRED`
- `NEEDS_MORE_CONTEXT -> WOULD_KEEP_REVIEW_REQUIRED_FOR_SOURCE_CHECK`

### 5.1 为什么一定要 dry-run

因为人工复核结果虽然比自动更可靠，但也不能直接跳过审查写入正式链路。先 dry-run 有几个好处：

- 可以先看分布是否合理
- 可以先看 trusted 会增加多少
- 可以先看 rejected 会有多少
- 可以先看有没有明显冲突
- 可以先证明“没有 write-back”

### 5.2 dry-run apply 的定位

它是“模拟后的计划”，不是“已经生效的事实”。

你看到 `apply_plan.json` 或 `apply_plan.xlsx` 时，要始终记住：

- 这是计划
- 不是正式更新
- 不是 production write-back
- 只是下一步 preview refresh 的输入

---

## 6. 什么是 reviewed preview

`reviewed preview` 指的是：在不覆盖原始 330L 预览工作簿的前提下，基于人工复核结果生成的新预览状态。

### 6.1 330L 和 330K4 的关系

可以这么理解：

- `330L` 是“人工 unit review 之前的 client-style export preview”
- `330K4` 是“人工 unit review 之后、基于 dry-run apply plan 刷新的 reviewed preview”
- `335A` 是“把 reviewed preview 再整理成更适合非工程读者查看的 client-facing clean preview export”

### 6.2 330K4 做了什么

当前 330K4 的结果是：

- 原始 trusted preview 行数：96
- 人工确认后新增或显式 surfaced 的 reviewed unit-confirmed 行：2
- refreshed trusted preview 行数：98
- 被人工拒绝、因此隔离出 trusted preview 的行：18
- 仍保留 review_required 的行：1

### 6.3 为什么 reviewed preview 仍然不是正式输出

因为它依然满足下面这些条件：

- 没有写回原始 330L workbook
- 没有修改 production pipeline
- 没有修改 official assets
- 只是 sidecar refreshed preview

所以它适合 demo、适合 review、适合讲解，但不适合宣称成“正式客户交付版本”。

### 6.4 335A client-facing clean export 做了什么

335A 不改变 330K4 的底层审核结论，它做的是把 reviewed preview 重新整理成一份更适合客户视角检查的 workbook。当前关键结果是：

- reviewed clean rows：98
- needs-review rows：1
- excluded / rejected rows：18
- source-trace rows：117
- `project_status = CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY`
- `client_facing_preview = true`

---

## 7. 什么是 demo packaging

`demo packaging` 指的是：把当前工程状态转成更容易展示和解释的文档。

在 DateFac 里，331A 和 331B 做的都是这个事情，只是时点不一样：

- `331A`：在 330L 状态上做第一版 demo packaging
- `331B`：在 330K4 reviewed preview 状态上做刷新后的 demo packaging
- `335A`：在 330K4 / 331B / 332A 之后，再生成一份更便于非工程读者阅读的 clean preview workbook

### 7.1 demo packaging 里面通常有什么

- overview
- resume bullets
- GitHub README section
- demo script

### 7.2 为什么需要这一步

因为工程内部 summary.json 很适合给程序或工程师看，但不适合给：

- GitHub 访客
- 面试官
- 非原作者的项目持有者
- 想快速了解项目的人

demo packaging 的作用就是把工程真相翻译成“可展示、但不造假”的文档。

---

## 8. 什么是 release audit

`release audit` 是最后一道“文档和说法审计”。

332A 做的事情不是再改数据，而是检查：

- 文档是不是都存在
- 文档里的指标是否一致
- 有没有 overclaim
- 有没有把 preview 说成正式交付
- 有没有把 demo 说成 production
- 有没有把“人工 review 之后的 preview”说成“已经自动商业化完成”

### 8.1 为什么 release audit 很重要

很多项目技术上已经相对稳了，但介绍方式会出问题。尤其是：

- README 里写太满
- resume 里用词太夸张
- demo script 里把 preview 说成 delivery
- interview 时把 sidecar 说成 production pipeline

332A 的意义就是：在你对外讲项目之前，先审一遍“说法是否安全”。

---

## 9. 哪些文件最重要

如果你是项目拥有者，不是原始作者，请先认识下面这些文件和目录。

### 9.1 根目录最重要的几个位置

- `README.md`
  - 项目的总说明
- `docs/demo/`
  - 对外展示、内部讲解、操作指南都在这里
- `docs/codex_tasks/`
  - 每个阶段的任务说明，能帮助你知道每一步为什么存在
- `tools/`
  - 各阶段 runner 入口
- `datefac/trust/`
  - sidecar trust、review、demo packaging、audit 逻辑
- `output/`
  - 各阶段运行产物目录

### 9.2 当前最值得熟悉的 output 目录

- `output/client_style_export_preview_330l`
- `output/human_unit_review_330k2`
- `output/human_unit_review_apply_simulation_330k3`
- `output/reviewed_export_refresh_330k4`
- `output/demo_packaging_331b`
- `output/demo_release_audit_332a`
- `output/client_facing_clean_export_335a`

### 9.3 当前最适合对外展示的文档

- `docs/demo/datefac_demo_overview_331b.md`
- `docs/demo/datefac_resume_bullets_331b.md`
- `docs/demo/datefac_github_readme_section_331b.md`
- `docs/demo/datefac_demo_script_331b.md`
- `docs/demo/datefac_demo_release_checklist_332a.md`
- `docs/demo/datefac_interview_talking_points_332a.md`

---

## 10. 哪些文件不要乱碰

下面这些东西如果你不是非常确定，就不要碰：

### 10.1 official assets

- `data/overrides/semantic_alias_candidates.json`
- `data/mapping/formal_scope_rules.json`

这两个是正式资产，不是 demo 层文档。

### 10.2 production pipeline / parser / extraction / delivery 文件

当前 330L 之后的链路都是 sidecar / demo / preview 路线。你如果在这个阶段乱改生产代码，会把“文档任务”和“生产逻辑任务”混在一起。

### 10.3 protected dirty files

当前明确受保护的脏文件包括：

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

这些文件不要顺手 stage，不要顺手 commit。

### 10.4 output 产物

`output/*` 默认不应该进 Git 提交。它们是运行产物，不是代码主干。

---

## 11. 每一步输入是什么

从当前 demo 链路看，最关键的输入关系如下：

### 11.1 330K2 的输入

- `demo_packaging_331a`
- `client_style_export_preview_330l`
- `unit_signal_review_330k`
- `delivery_report_refresh_after_330k_330j2`

### 11.2 330K3 的输入

- `human_unit_review_330k2`
- 已填写的 `human_unit_review_330k2_review_filled.xlsx`
- `demo_packaging_331a`
- `client_style_export_preview_330l`

### 11.3 330K4 的输入

- `client_style_export_preview_330l`
- `human_unit_review_330k2`
- `human_unit_review_apply_simulation_330k3`

### 11.4 331B 的输入

- `demo_packaging_331a`
- `reviewed_export_refresh_330k4`
- `human_unit_review_apply_simulation_330k3`
- `human_unit_review_330k2`
- `client_style_export_preview_330l`

### 11.5 332A 的输入

- `demo_packaging_331b`
- `reviewed_export_refresh_330k4`
- `demo_packaging_331a`
- `docs/demo/` 下的 331B 文档

---

## 12. 每一步输出是什么

### 12.1 330K2 输出

核心输出：

- `human_unit_review_330k2_review_template.xlsx`
- `human_unit_review_330k2_summary.json`

你可以把它理解成：

> “把需要人工看 unit 的 21 行，做成一个待填表。”

### 12.2 330K3 输出

核心输出：

- `human_unit_review_apply_simulation_330k3_apply_plan.json`
- `human_unit_review_apply_simulation_330k3_apply_plan.xlsx`

你可以把它理解成：

> “把人工填写的决定，翻译成 dry-run 动作计划。”

### 12.3 330K4 输出

核心输出：

- `reviewed_export_refresh_330k4_preview.xlsx`
- `reviewed_export_refresh_330k4_summary.json`

你可以把它理解成：

> “在不改原始 preview 的前提下，生成一个 reviewed preview 状态。”

### 12.4 331B 输出

核心输出：

- `demo_packaging_331b_summary.json`
- `docs/demo/datefac_demo_overview_331b.md`
- `docs/demo/datefac_resume_bullets_331b.md`
- `docs/demo/datefac_github_readme_section_331b.md`
- `docs/demo/datefac_demo_script_331b.md`

你可以把它理解成：

> “把 reviewed preview 这个状态，包装成适合展示的文档。”

### 12.5 332A 输出

核心输出：

- `demo_release_audit_332a_summary.json`
- `demo_release_audit_332a_checklist.md`
- `docs/demo/datefac_demo_release_checklist_332a.md`
- `docs/demo/datefac_interview_talking_points_332a.md`

你可以把它理解成：

> “对 demo 说法做最后审计，确认没有过度宣传。”

### 12.6 335A 输出

核心输出：
- `client_facing_clean_export_335a_preview.xlsx`
- `client_facing_clean_export_335a_summary.json`

你可以把它理解成：
> “把 reviewed preview 整理成更适合客户视角检查的 clean preview workbook，但仍然不是正式交付物。”

---

## 13. 从拿到 PDF 到生成 demo 包怎么走

如果你只是想理解当前项目路线，可以这么记：

1. parser 或已有结构化链路先产出 candidate
2. sidecar trust routing 先做 trusted / review_required 分流
3. 330L 做第一版 preview
4. 331A 把第一版 preview 包成 demo 文档
5. 330K2 把 unit 风险行单独拎出来做人工复核
6. 330K3 读取人工复核结果，生成 dry-run apply plan
7. 330K4 基于 dry-run 结果生成 reviewed preview
8. 331B 把 reviewed preview 重新包成新的 demo 文档
9. 332A 对文档说法和指标一致性做 release audit

如果你以后真的拿到新的 PDF，要非常清楚一件事：

> 当前项目还不是“扔进去新 PDF 就自动产出可对客交付包”的状态。

目前更适合的说法是：

- 它可以支撑小规模、有人盯着的 demo / 人工兜底试点
- 但还不适合说成已经达到生产级就绪的自动系统

---

## 14. 怎么打开 Excel 看结果

当前最常看的 Excel 有三类：

### 14.1 330L preview workbook

路径：

- `D:\_datefac\output\client_style_export_preview_330l\client_style_export_preview_330l_preview.xlsx`

适合看：

- trusted preview baseline
- review_required baseline
- unit review sample

### 14.2 330K2 human review workbook

路径：

- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_template.xlsx`
- 或人工填写后的  
  `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_filled.xlsx`

适合看：

- 候选 id
- metric
- year
- value
- current unit
- source_page
- source_evidence_text
- reviewer_unit
- reviewer_decision
- reviewer_notes

### 14.3 330K4 reviewed preview workbook

路径：

- `D:\_datefac\output\reviewed_export_refresh_330k4\reviewed_export_refresh_330k4_preview.xlsx`

适合看：

- reviewed trusted preview
- remaining review required
- human rejected by unit review
- apply plan trace

看 Excel 时最重要的是：

- 先看 sheet 名字
- 再看 candidate_id
- 再看 source_page 和 source_evidence_text
- 再看 reviewer_decision
- 不要只盯着 value

---

## 15. 怎么理解 330K2 的人工 unit review workbook

330K2 workbook 其实就是一个“待判断清单”。你可以把每一行理解成：

> “系统当前不敢完全自动相信这条记录，请你帮我判断 unit 和处理方式。”

这类表里，最值得关注的列一般有：

- `candidate_id`
- `pdf_document_id`
- `metric_label_raw`
- `normalized_metric`
- `year`
- `value`
- `current_unit`
- `source_page`
- `source_evidence_text`
- `reviewer_unit`
- `reviewer_decision`
- `reviewer_notes`

你填表时，重点不是“猜一个最好看的答案”，而是：

- 看证据够不够
- 看 unit 能不能明确
- 看这条是不是根本不应该 trusted

---

## 16. reviewer_unit / reviewer_decision / reviewer_notes 怎么填

### 16.1 `reviewer_unit`

如果你能明确判断这条记录应该是什么 unit，就填。

例如：

- `percent`
- `RMB_mn`
- `RMB/share`
- `times`

如果你根本无法确定，不要硬猜。

### 16.2 `reviewer_decision`

当前允许的值是：

- `CONFIRM_UNIT`
- `REJECT_UNIT`
- `KEEP_UNIT_UNKNOWN`
- `NEEDS_MORE_CONTEXT`

可以这样理解：

- `CONFIRM_UNIT`
  - 我认为这条记录可以保留，unit 也能确认
- `REJECT_UNIT`
  - 我认为这条记录不应该进 trusted preview
- `KEEP_UNIT_UNKNOWN`
  - 我认为这条记录暂时不能确认 unit，但也不想直接判死
- `NEEDS_MORE_CONTEXT`
  - 目前证据不够，需要回源再看

### 16.3 `reviewer_notes`

这里不要写“感觉不太对”这种模糊句子。尽量写清楚原因，例如：

- `False positive: evidence is company-code/peer table fragment, not EPS unit.`
- `Gross margin unit confirmed as percent; value is plausible from metric convention.`
- `Needs original table check because extracted value looks like a year token.`

写 notes 的意义，是让下一步看到 dry-run apply plan 或 reviewed preview 的人，知道你为什么这么判。

---

## 17. 330K3 / 330K4 / 331B / 332A 分别干什么

这一组阶段很容易混。可以这么记：

### 17.1 330K3

> 把人工决定翻译成模拟动作计划。

它不改正式数据，只告诉你“如果按这个决定走，接下来应该怎么处理每条 candidate”。

### 17.2 330K4

> 把模拟动作计划映射成 reviewed preview。

它会让 2 条确认过 unit 的行进入 reviewed trusted preview，把 18 条 rejected 行隔离出去，把 1 条 unresolved 行继续留 review_required。

### 17.3 331B

> 把 reviewed preview 这个状态翻译成人能看的 demo 文档。

也就是 overview、resume、README section、demo script。

### 17.4 332A

> 检查 331B 文档有没有说过头。

它会审：

- 指标是否一致
- 文案是否一致
- 有没有 overclaim
- 有没有忘记明确写出“现在还不是对客交付状态，也还不是生产级状态”

---

## 18. 出错时先检查什么

如果你遇到问题，请按下面的顺序检查：

### 18.1 先看 summary.json

每个阶段都有 summary.json。不要先猜，先看：

- `qa_fail_count`
- `blocking_reasons`
- `decision`

### 18.2 再看输入路径是不是齐了

很多问题不是代码错，而是：

- 上游目录没生成
- workbook 路径写错
- filled workbook 没放到默认位置

### 18.3 再看是不是把旧文件和新文件混了

常见混乱包括：

- 把 330L preview 和 330K4 reviewed preview 混着看
- 把 331A 文档和 331B 文档混着引用
- 把 review_template 和 review_filled 搞混

### 18.4 再看 Git 工作区

如果你准备提交，先看：

- 有没有误 stage `output/*`
- 有没有误 stage protected dirty files

### 18.5 最后再怀疑逻辑

在证据不足时，不要第一反应就是“代码有 bug”。先把路径、输入、阶段顺序、文档版本核对清楚。

---

## 19. 哪些东西可以放 GitHub

当前比较安全的，是那些明确写清楚边界、且不伪装成 production deliverable 的文档，例如：

- `README.md`
- `docs/demo/datefac_demo_overview_331b.md`
- `docs/demo/datefac_resume_bullets_331b.md`
- `docs/demo/datefac_github_readme_section_331b.md`
- `docs/demo/datefac_demo_script_331b.md`
- `docs/demo/datefac_demo_release_checklist_332a.md`
- `docs/demo/datefac_interview_talking_points_332a.md`
- 本次 333A 的中英双语文档

如果是本地演示，下面两个 335A 产物也很值得打开，但它们仍然属于 `output/*`，不应该被 stage：

- `D:\_datefac\output\client_facing_clean_export_335a\client_facing_clean_export_335a_preview.xlsx`
- `D:\_datefac\output\client_facing_clean_export_335a\client_facing_clean_export_335a_summary.json`

但是不要把 `output/*` 当成应该提交的演示文件。原则是：

- 文档可以进 Git
- 代码可以进 Git
- summary 逻辑可以进 Git
- 运行产物通常不进 Git

---

## 20. 哪些话面试时可以说

安全说法包括：

- 这个项目不是单纯的 PDF 表格抽取，而是抽取结果的可信化治理
- 我们把 parser 输出之后的 trust routing、unit review、dry-run apply、reviewed preview 和 release audit 都做了 sidecar 化
- 系统能区分 trusted、review_required、rejected，而不是把所有 candidate 一股脑推进 trusted
- 人工 review 被故意隔离在 write-back 前面
- 331A 到 331B 的变化，体现的是“人工 review 反馈如何影响 preview”，不是“如何自动改生产”

---

## 21. 哪些话千万别说

不要说：

- 已经达到可直接对客交付
- 已经达到生产级就绪
- 已经可以自动给客户交付
- 准确率 100%
- 已经 fully automatic
- 已经是可直接卖给客户的 SaaS
- 已经可以直接用于投资决策
- 不需要人工 review

这些说法会直接破坏项目可信度，因为和当前真实状态不符。

---

## 22. 如果以后要接单，应该怎么用这个项目

如果以后你想把这个项目用于“小额人工兜底试点”或“半手工 demo 服务”，合理的方式不是把它包装成全自动系统，而是：

1. 明确告诉对方这是 demo / preview / human-in-the-loop 路线
2. 先限定 PDF 范围和场景
3. 先跑 candidate preparation 和 trust routing
4. 对 review_required 尤其是 unit 风险行保留人工复核
5. 用 reviewed preview 做演示，而不是宣称正式生产结果
6. 最终输出必须带边界说明

### 22.1 现在适合做什么样的试点

适合做：

- 小样本、有人盯着的内部验证
- demo 演示
- 项目能力说明
- 试点式人工兜底服务

不适合做：

- 无人值守自动交付
- 大规模批量对客生产
- 带正式 SLA 的商业 SaaS

---

## 23. 为什么现在可以做小额人工兜底试点，但不能说已经达到生产级就绪

这是很多项目拥有者最容易被问到的问题。

原因其实很简单：

### 23.1 可以试点，是因为已经有了工程边界

当前已经具备：

- trusted / review_required / rejected 分流
- human unit review workbook
- dry-run apply simulation
- reviewed preview refresh
- demo packaging
- release audit

这意味着你不是在“瞎跑一个模型”，而是在“有边界、有文档、有审计”的方式下做小规模试点。

### 23.2 不能说已经达到生产级就绪，是因为还缺生产级条件

生产级通常至少还需要：

- 更强和更广的 parser benchmark
- 客户导向的 clean export
- 更正式的人机协作 UI
- 权限控制
- 数据隔离
- 安全设计
- 部署和运维方案
- 失败重试与监控
- 更大规模真实样本验证

这些目前都还没有闭环，所以不能说已经达到生产级就绪。

---

## 24. Current limitations / 当前局限

这一节故意保留 `current limitations` 这个英文词，因为你以后在 README、overview、runbook 和对外介绍里都会反复见到它。它不是客套话，而是当前阶段必须被保留的真实边界。

当前局限至少包括：

- 当前 330K2、330K3、330K4、331B、332A 都属于 sidecar demo preview，不是正式生产链路
- 当前 335A 虽然已经有 clean export，但它仍然只是 client-facing clean preview，不是正式客户交付导出
- 当前坚持 `no write-back`，也就是人工 workbook 的结论不会直接写进 official assets
- parser 质量仍然会影响 candidate 质量，尤其是在复杂表、噪声行、图注混入和列错位场景
- human review 目前还是 workbook 驱动，不是更顺手的 UI
- reviewed preview 适合解释“现在能信到什么程度”，不适合包装成正式客户交付物
- benchmark 范围虽然足以说明工程思路，但还不足以支撑更大规模商业承诺
- deployment、security、permission、data isolation、多用户协作这些生产问题尚未闭环

如果你以后接手这个项目，最危险的误判不是“觉得它没价值”，而是“看到 preview 很整齐，就误以为它已经跨过了生产边界”。

---

## 25. 推荐的下一步工程路线

如果你是项目拥有者，接下来最推荐的路线不是“赶紧吹成产品”，而是：

1. 继续扩 demo 文档和操作文档
2. 把 current runbook 固化，让非原作者也能跑通
3. 扩真实 PDF benchmark
4. 优化 human review 流程，减少纯手工摩擦
5. 先做更清晰的 client-facing clean preview
6. 等 dry-run 和 preview 证据足够稳后，再讨论正式 write-back 设计
7. 最后才考虑 deployment、security、multi-user、commercialization

一句话收尾：

> DateFac 现在最强的价值，不是“已经自动化完成”，而是“已经把可信化、人工复核、预览刷新、展示边界这几层工程问题分清楚了”。
