# DateFac

## 中文

### 项目一句话

DateFac 是一个面向券商研报 PDF 核心财务指标抽取结果的 sidecar 信任路由、人工复核隔离、预览刷新和 demo 叙事治理项目。它当前解决的重点不是“能不能把表格抽出来”，而是“抽出来以后，怎样把候选行做成可追溯、可复核、可展示、不过度宣称的 reviewed preview”。

### 中文摘要

很多 PDF 抽取项目在演示时只回答一个问题：parser 有没有把表格和数字识别出来。DateFac 当前回答的是更偏工程治理的问题：当 parser 已经给出候选结果以后，系统能不能保留 provenance，识别 unit 风险，把记录保守地分成 trusted 与 review_required，把人工判断隔离在 no write-back 的 sidecar 流程里，再把最终状态包装成适合 GitHub、面试、远程协作和项目交接的 demo 文档。当前最新状态已经推进到 `CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY`，也就是“在 reviewed preview 基础上，额外生成了一份更适合非工程读者查看的 client-facing clean preview export”，但仍然 `client_ready = false`，`production_ready = false`。这意味着它适合拿来展示工程思路、review 闭环、preview 刷新、客户视角预览整理和风险边界，不适合被说成正式客户端交付系统，也不适合被说成生产写回已经完成。

### 这个项目解决什么问题

金融研报 PDF 的困难不只在 OCR 或表格识别，还在抽取后的可置信处理：

1. 一条记录看起来像对的，并不代表 metric、year、value、unit、上下文就真的对齐。
2. parser 能读出数字，不等于这条数字就能进入 trusted preview。
3. 如果没有 provenance，后续人工无法追溯这条记录来自哪一页、哪一段、哪张表。
4. 如果没有 review_required 队列，风险候选就会被过早伪装成“可靠结果”。
5. 如果人工 review 结果直接写回正式产物，没有 dry-run apply，就很难证明修改边界和影响范围。
6. 如果对外文档不做 release audit，README、resume、demo script 很容易把 preview 说成 production。

DateFac 当前围绕这些问题构建了一个 sidecar demo 路径：先候选准备，再 trust routing，再 unit review，再 dry-run apply，再 reviewed preview refresh，再 demo packaging，最后做 overclaim audit。这个路径的价值，在于它把“抽取结果什么时候能信、什么时候不能信、什么时候必须留给人看、什么时候只能算 preview”说清楚了。

### 当前状态

| 字段 | 当前值 | 说明 |
|---|---|---|
| `project_status` | `CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY` | 当前是 reviewed preview 之后的 client-facing clean preview export 状态 |
| `client_facing_preview` | `true` | 当前已经有一份更适合非工程读者查看的 clean preview workbook |
| `client_ready` | `false` | 不能宣称已经达到客户可直接接收的交付状态 |
| `production_ready` | `false` | 不能宣称已经达到生产部署或生产写回状态 |
| `overclaim_risk_count` | `0` | 332A 文档审计未发现剩余过度宣称风险 |
| `qa_fail_count` | `0` | 当前 335A clean preview export QA 通过 |

### 当前 headline metrics

| 指标 | 当前值 | 来源阶段 |
|---|---:|---|
| unfamiliar PDFs | 13 | 330L / 331A / 331B / 332A / 335A 叙事基线 |
| PDFs produced candidates | 7 | `source_pdf_unique_count = 7` |
| `prepared_candidate_row_count` | 117 | 330L |
| `original_trusted_sheet_row_count` | 96 | 330L / 330K4 基线 trusted preview |
| `reviewed_unit_confirmed_count` | 2 | 330K3 / 330K4 |
| `reviewed_trusted_preview_row_count` | 98 | 330K4 / 331B / 332A / 335A 来源基线 |
| `core_metrics_reviewed_row_count` | 98 | 335A customer-facing reviewed sheet |
| `needs_review_row_count` | 1 | 335A customer-facing needs-review sheet |
| `excluded_or_rejected_row_count` | 18 | 335A customer-facing excluded / rejected sheet |
| `source_trace_row_count` | 117 | 335A source trace sheet |
| `apply_plan_row_count` | 21 | 330K3 / 330K4 / 331B / 332A / 335A |
| `overclaim_risk_count` | 0 | 332A |
| `source_page_missing_count` | 0 | 335A |
| `qa_fail_count` | 0 | 335A |

为避免读者只扫表格而忽略真实边界，下面再用精确字符串重申当前 client-facing clean preview 状态：

- `project_status = CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY`
- `client_facing_preview = true`
- `client_ready = false`
- `production_ready = false`
- `core_metrics_reviewed_row_count = 98`
- `needs_review_row_count = 1`
- `excluded_or_rejected_row_count = 18`
- `source_page_missing_count = 0`
- `qa_fail_count = 0`

这些行不是无意义重复，而是为了确保任何引用 README 的人都能直接看到当前状态，不把 clean preview 误说成正式交付结果。尤其是 `excluded_or_rejected_row_count = 18` 和 `needs_review_row_count = 1`，它们提醒读者：系统当前并不是“把所有候选都整理成可直接交付结果”，而是明确保留了拒绝和未决状态。

### 核心能力

当前可以安全宣称的能力包括：

| 能力 | 当前含义 |
|---|---|
| financial research PDF core metric extraction | 面向券商研报 PDF 的核心指标候选提取与整理 |
| candidate preparation | 将抽取结果整理成带 provenance 的 candidate records |
| trusted / review_required routing | 用 sidecar trust-routing 逻辑保守分流 |
| unit risk detection | 识别 unit missing、unit conflict、单位语义不清等风险 |
| human unit review packaging | 把 unit 风险行打包成 workbook 供人工 review |
| dry-run apply simulation | 将人工决策转成 no write-back 的 apply plan |
| reviewed preview export | 基于人工结果刷新 reviewed preview，但不覆盖原始 330L 预览 |
| client-facing clean preview export | 将 reviewed preview 整理成更适合客户视角检查的 clean workbook，但仍保持 preview 边界 |
| demo packaging | 生成 overview、resume bullets、README section、demo script 等对外文档 |
| release audit / overclaim audit | 检查叙事一致性、边界声明、禁语和指标一致性 |

### 架构概览

当前架构不是“直接改生产结果”，而是“围绕已有 parser 输出做 sidecar 治理”：

```text
Input PDFs / Cached Parser Outputs
    -> candidate extraction and preparation
    -> sidecar trust routing
    -> trusted preview / review_required preview
    -> unit review queue
    -> dry-run apply plan
    -> reviewed preview refresh
    -> demo packaging
    -> release audit
    -> client-facing clean preview export
```

这个架构有四个关键设计选择：

1. parser 输出只是起点，不被自动视为可信终点。
2. review 风险候选先留在 preview 侧，不直接推进正式资产。
3. 人工判断先进入 dry-run apply，再进入 reviewed preview，而不是立即 write-back。
4. 文档本身也接受审计，避免“工程边界保守，但 README 说得过满”。

### 阶段历史

#### Stage 1 到 Stage 4

早期 Stage 1 到 Stage 4 主要是 legacy structured repair / governance work，重点是建立修复、可重建、可审计和规则治理的工程纪律：

| 阶段 | 主题 | 价值 |
|---|---|---|
| Stage 1 | safe AI extract-positive repair | 证明修复动作必须带边界和门禁 |
| Stage 2 | override-first rebuildability | 证明结果应该可从官方输入重建 |
| Stage 3 | final metric override backlog repair | 推进正式 override 路径同时保留审计性 |
| Stage 4 | structured-layer scope rule governance | 让结构层规则治理具备 promotion 与验证机制 |

#### 当前 demo 链路

| 阶段 | 作用 | 当前结果 |
|---|---|---|
| `330L` client-style export preview | 生成第一版 client-style preview workbook | `trusted_sheet_row_count = 96`，`review_required_sheet_row_count = 21` |
| `331A` demo packaging | 把 330L 状态包装成可展示的 demo 文档 | `DEMO_READY_WITH_UNIT_REVIEW_CAVEATS` |
| `330K2` human unit review package | 打包 21 条 unit-review 记录供人工复核 | `packaged_unit_review_row_count = 21` |
| `330K3` human unit review apply simulation | 把人工 review 结果变成 dry-run apply plan | `apply_plan_row_count = 21` |
| `330K4` reviewed export refresh | 用 dry-run 结果刷新 reviewed preview | `reviewed_trusted_preview_row_count = 98` |
| `331B` demo packaging refresh | 用 reviewed preview 刷新 demo 文档叙事 | `DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW` |
| `332A` demo release audit | 审计 overview、resume、README section、script 的一致性与 overclaim 风险 | `overclaim_risk_count = 0`，`qa_fail_count = 0` |
| `335A` client-facing clean export | 从 reviewed preview 生成更适合客户视角检查的 clean preview workbook | `CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY`，`core_metrics_reviewed_row_count = 98` |

### 当前 demo pipeline 怎么跑

下面是当前 330K2 到 335A 的 demo 路线。它们都属于 sidecar / demo / preview / no write-back 流程。

#### 330K2 Human Unit Review Package

上游依赖：

- `D:\_datefac\output\demo_packaging_331a`
- `D:\_datefac\output\client_style_export_preview_330l`
- `D:\_datefac\output\unit_signal_review_330k`
- `D:\_datefac\output\delivery_report_refresh_after_330k_330j2`

命令：

```powershell
python tools\run_human_unit_review_330k2.py --demo-packaging-dir D:\_datefac\output\demo_packaging_331a --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --unit-signal-review-dir D:\_datefac\output\unit_signal_review_330k --delivery-report-refresh-dir D:\_datefac\output\delivery_report_refresh_after_330k_330j2 --output-dir D:\_datefac\output\human_unit_review_330k2
```

输出目录：

- `D:\_datefac\output\human_unit_review_330k2`

#### 330K3 Human Unit Review Apply Simulation

上游依赖：

- `D:\_datefac\output\human_unit_review_330k2`
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_filled.xlsx`
- `D:\_datefac\output\demo_packaging_331a`
- `D:\_datefac\output\client_style_export_preview_330l`

命令：

```powershell
python tools\run_human_unit_review_apply_simulation_330k3.py --filled-review-workbook D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_filled.xlsx --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --demo-packaging-dir D:\_datefac\output\demo_packaging_331a --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --output-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3
```

输出目录：

- `D:\_datefac\output\human_unit_review_apply_simulation_330k3`

#### 330K4 Reviewed Export Refresh

上游依赖：

- `D:\_datefac\output\client_style_export_preview_330l`
- `D:\_datefac\output\human_unit_review_330k2`
- `D:\_datefac\output\human_unit_review_apply_simulation_330k3`

命令：

```powershell
python tools\run_reviewed_export_refresh_330k4.py --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --apply-simulation-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3 --output-dir D:\_datefac\output\reviewed_export_refresh_330k4
```

输出目录：

- `D:\_datefac\output\reviewed_export_refresh_330k4`

#### 331B Demo Packaging Refresh

上游依赖：

- `D:\_datefac\output\demo_packaging_331a`
- `D:\_datefac\output\reviewed_export_refresh_330k4`
- `D:\_datefac\output\human_unit_review_apply_simulation_330k3`
- `D:\_datefac\output\human_unit_review_330k2`
- `D:\_datefac\output\client_style_export_preview_330l`

命令：

```powershell
python tools\run_demo_packaging_331b.py --demo-packaging-331a-dir D:\_datefac\output\demo_packaging_331a --reviewed-export-refresh-dir D:\_datefac\output\reviewed_export_refresh_330k4 --apply-simulation-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3 --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --output-dir D:\_datefac\output\demo_packaging_331b
```

输出目录：

- `D:\_datefac\output\demo_packaging_331b`

#### 332A Demo Release Audit

上游依赖：

- `D:\_datefac\output\demo_packaging_331b`
- `D:\_datefac\output\reviewed_export_refresh_330k4`
- `D:\_datefac\output\demo_packaging_331a`
- `D:\_datefac\docs\demo`

命令：

```powershell
python tools\run_demo_release_audit_332a.py --demo-packaging-331b-dir D:\_datefac\output\demo_packaging_331b --reviewed-export-refresh-dir D:\_datefac\output\reviewed_export_refresh_330k4 --demo-packaging-331a-dir D:\_datefac\output\demo_packaging_331a --docs-demo-dir D:\_datefac\docs\demo --output-dir D:\_datefac\output\demo_release_audit_332a
```

输出目录：

- `D:\_datefac\output\demo_release_audit_332a`

#### 335A Client-Facing Clean Export

上游依赖：

- `D:\_datefac\output\reviewed_export_refresh_330k4`
- `D:\_datefac\output\demo_packaging_331b`
- `D:\_datefac\output\demo_release_audit_332a`
- `D:\_datefac\output\client_style_export_preview_330l`

命令：

```powershell
python tools\run_client_facing_clean_export_335a.py --reviewed-export-refresh-dir D:\_datefac\output\reviewed_export_refresh_330k4 --demo-packaging-331b-dir D:\_datefac\output\demo_packaging_331b --demo-release-audit-dir D:\_datefac\output\demo_release_audit_332a --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --output-dir D:\_datefac\output\client_facing_clean_export_335a
```

输出目录：

- `D:\_datefac\output\client_facing_clean_export_335a`

### 当前哪些文件适合展示

这些文件比较适合放到 GitHub、项目介绍、远程面试材料或协作交接里：

- `docs/demo/datefac_demo_overview_331b.md`
- `docs/demo/datefac_resume_bullets_331b.md`
- `docs/demo/datefac_github_readme_section_331b.md`
- `docs/demo/datefac_demo_script_331b.md`
- `docs/demo/datefac_demo_release_checklist_332a.md`
- `docs/demo/datefac_interview_talking_points_332a.md`
- `docs/demo/（中文新手指南）datefac_newbie_operator_guide_333a_zh.md`
- `docs/demo/（英文新手指南）datefac_newbie_operator_guide_333a_en.md`
- `docs/demo/（中文运行手册）datefac_current_runbook_333a_zh.md`
- `docs/demo/（英文运行手册）datefac_current_runbook_333a_en.md`
- `docs/demo/（中文项目总览）datefac_project_overview_333a_zh.md`
- `docs/demo/（英文项目总览）datefac_project_overview_333a_en.md`

另外，以下运行产物适合在本地演示时打开，但不应提交到 Git：

- `D:\_datefac\output\client_facing_clean_export_335a\client_facing_clean_export_335a_preview.xlsx`
- `D:\_datefac\output\client_facing_clean_export_335a\client_facing_clean_export_335a_summary.json`

如果只想给第一次接触仓库的人一个最稳妥的阅读顺序，可以先看 `README.md`，再看 333A 的项目总览，再看 333A 的 runbook，最后再打开 330L、330K2、330K3、330K4、331B、332A 对应的 summary 与 workbook。这样能先理解边界，再理解命令，再理解产物，不容易把 preview 和正式资产混在一起。

### Safety boundaries

当前必须反复强调的边界包括：

- 没有 production write-back
- 不能把项目描述成可直接对客交付
- 不能把项目描述成可直接进入生产部署或生产写回
- `output/*` 是运行产物，默认不提交
- official assets 受保护，不在这条 demo 路线上被修改
- protected dirty files 不应被 stage
- 当前是 sidecar、demo、preview 路线
- human review 被故意隔离在任何未来 write-back 讨论之前

### Current limitations / 当前局限

当前系统的价值主要在可追溯 preview 治理，而不是在生产交付完成度上。主要局限包括：

1. 仍然是 client-facing clean preview，不是正式客户端交付导出。
2. parser 质量仍然是瓶颈，尤其是复杂表格、噪声行和跨列修复场景。
3. clean preview 仍然是 preview 产物，不是 production export，也没有正式 write-back。
4. benchmark 范围仍然有限，当前叙事主要围绕 13 份 unfamiliar PDFs。
5. 人工 unit review 仍然是 workbook 流程，缺少更友好的 UI。
6. 缺少部署、安全、权限、数据隔离、多租户和运维层设计。

### 下一步里程碑

下一步合理的工程方向包括：

1. 继续验证并加固 client-facing clean preview export 对更多文档变体的稳定性。
2. 扩大 unfamiliar-PDF benchmark 样本范围。
3. 优化 manual review UI 或引导式 operator workflow。
4. 在积累足够 dry-run 证据后，再讨论 production write-back design。
5. 在任何生产化叙事之前补齐 deployment、security 和 data isolation 设计。

## English

### One-Paragraph Summary

DateFac is a sidecar trust-routing, human-review isolation, preview refresh, and demo-packaging project built around financial research PDF extraction. Its current focus is not simply “can a parser read a table,” but “once parser output exists, how do we preserve provenance, detect unit risk, route rows conservatively, isolate manual review before any write-back discussion, refresh a reviewed preview safely, and describe the result without overclaiming?”

### Why This Project Exists

Many PDF extraction demos stop at the parser layer. They show that a table can be detected, that text can be read, or that a number can be surfaced. DateFac works on the harder engineering question that starts after that point: a number that looks plausible is still not automatically trustworthy. It may have the wrong unit, the wrong year alignment, insufficient evidence, or the wrong semantic context. A preview workbook can also become misleading if it looks polished enough to be mistaken for a production deliverable. DateFac therefore concentrates on the control layer around extracted candidate rows: provenance retention, trust-routing, unit-risk detection, human review packaging, dry-run apply simulation, reviewed preview refresh, demo packaging, and release-audit discipline.

### Current Status

| Field | Value | Meaning |
|---|---|---|
| `project_status` | `CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY` | The project currently reflects a cleaner customer-facing preview built on top of the reviewed preview state |
| `client_facing_preview` | `true` | A cleaner workbook now exists for non-engineering inspection |
| `client_ready` | `false` | It should not be presented as ready for direct client delivery |
| `production_ready` | `false` | It should not be presented as suitable for live production use or production write-back |
| `overclaim_risk_count` | `0` | The 332A release audit found no remaining overclaim risk in the current public-facing docs |
| `qa_fail_count` | `0` | The current client-facing clean preview export QA is clean |

### Current Headline Metrics

| Metric | Value | Why It Matters |
|---|---:|---|
| unfamiliar PDFs | 13 | Current unfamiliar-PDF benchmark scope used in the demo narrative |
| PDFs produced candidates | 7 | Only seven unfamiliar PDFs yielded candidate rows in the current cached flow |
| `prepared_candidate_row_count` | 117 | Total prepared candidate rows in the 330L baseline |
| `original_trusted_sheet_row_count` | 96 | Trusted preview baseline before manual unit review outcomes were surfaced |
| `reviewed_unit_confirmed_count` | 2 | Human-confirmed rows that were safely surfaced into the reviewed trusted preview |
| `reviewed_trusted_preview_row_count` | 98 | Trusted preview count after the reviewed refresh |
| `core_metrics_reviewed_row_count` | 98 | Customer-facing reviewed clean-sheet row count in 335A |
| `needs_review_row_count` | 1 | Customer-facing needs-review row count in 335A |
| `excluded_or_rejected_row_count` | 18 | Customer-facing excluded / rejected row count in 335A |
| `source_trace_row_count` | 117 | Customer-facing trace row count in 335A |
| `apply_plan_row_count` | 21 | Number of rows carried through the dry-run review application plan |
| `overclaim_risk_count` | 0 | Release audit sees no remaining overclaim hits |
| `source_page_missing_count` | 0 | No source-page loss in the customer-facing clean preview export |
| `qa_fail_count` | 0 | Latest QA passed |

### Core Capabilities

The current project can safely claim the following:

| Capability | Meaning In The Current Demo State |
|---|---|
| financial research PDF core metric extraction | Build candidate rows from financial research PDF evidence |
| candidate preparation | Normalize extracted rows into prepared records with provenance |
| trusted / review_required routing | Route rows conservatively using sidecar trust logic |
| unit risk detection | Detect unit-missing, unit-conflict, and unit-ambiguity situations |
| human unit review packaging | Generate workbook-based review queues for risky rows |
| dry-run apply simulation | Convert manual review outcomes into no-write-back actions |
| reviewed preview export | Refresh a reviewed preview workbook without mutating the baseline workbook |
| client-facing clean preview export | Repackage the reviewed preview into a cleaner customer-facing workbook while preserving preview boundaries |
| demo packaging | Build overview, README-support, resume-support, and demo-script materials |
| release audit / overclaim audit | Check consistency, boundary language, and claim safety before public presentation |

### Architecture Overview

The project is best understood as a sidecar governance path layered on top of parser output:

```text
Input PDFs / Cached Parser Outputs
    -> candidate extraction and preparation
    -> sidecar trust routing
    -> trusted preview / review_required preview
    -> unit review queue
    -> dry-run apply plan
    -> reviewed preview refresh
    -> demo packaging
    -> release audit
    -> client-facing clean preview export
```

This architecture makes four deliberate choices:

1. parser output is treated as the beginning of the trust problem, not the end of it
2. risky rows stay in preview-oriented review space instead of being promoted automatically
3. manual review outcomes become dry-run actions before they become refreshed preview state
4. documentation itself is audited so that a conservative engineering flow is not undermined by unsafe public wording

### Stage History

#### Stage 1 to Stage 4

Stage 1 to Stage 4 were earlier structured repair and governance stages that established the auditability mindset behind the current project:

| Stage | Theme | Lasting Role |
|---|---|---|
| Stage 1 | safe AI extract-positive repair | Introduced guarded repair application instead of ad hoc editing |
| Stage 2 | override-first rebuildability | Established that important outputs should be reconstructable |
| Stage 3 | final metric override backlog repair | Advanced official override work while preserving traceability |
| Stage 4 | structured-layer scope rule governance | Strengthened rule-governance discipline before later demo work |

#### Current Demo Path

| Stage | Purpose | Result |
|---|---|---|
| `330L` client-style export preview | Build the first client-style preview workbook | `trusted_sheet_row_count = 96`, `review_required_sheet_row_count = 21` |
| `331A` demo packaging | Package the 330L state into demo-facing materials | `DEMO_READY_WITH_UNIT_REVIEW_CAVEATS` |
| `330K2` human unit review package | Package 21 unit-risk rows for manual review | `packaged_unit_review_row_count = 21` |
| `330K3` human unit review apply simulation | Turn manual decisions into a dry-run apply plan | `apply_plan_row_count = 21` |
| `330K4` reviewed export refresh | Refresh the preview state from dry-run outcomes | `reviewed_trusted_preview_row_count = 98` |
| `331B` demo packaging refresh | Refresh the public-facing demo narrative from the reviewed preview | `DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW` |
| `332A` demo release audit | Audit metrics, wording, and overclaim risk | `overclaim_risk_count = 0`, `qa_fail_count = 0` |
| `335A` client-facing clean export | Build a cleaner customer-facing preview workbook from the reviewed preview | `CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY`, `core_metrics_reviewed_row_count = 98` |

### How To Run The Current Demo Pipeline

The current documented pipeline begins at the 330K2 packaging stage and extends through the 335A client-facing clean preview export stage. It assumes cached upstream outputs already exist.

#### 330K2

```powershell
python tools\run_human_unit_review_330k2.py --demo-packaging-dir D:\_datefac\output\demo_packaging_331a --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --unit-signal-review-dir D:\_datefac\output\unit_signal_review_330k --delivery-report-refresh-dir D:\_datefac\output\delivery_report_refresh_after_330k_330j2 --output-dir D:\_datefac\output\human_unit_review_330k2
```

#### 330K3

```powershell
python tools\run_human_unit_review_apply_simulation_330k3.py --filled-review-workbook D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_filled.xlsx --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --demo-packaging-dir D:\_datefac\output\demo_packaging_331a --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --output-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3
```

#### 330K4

```powershell
python tools\run_reviewed_export_refresh_330k4.py --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --apply-simulation-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3 --output-dir D:\_datefac\output\reviewed_export_refresh_330k4
```

#### 331B

```powershell
python tools\run_demo_packaging_331b.py --demo-packaging-331a-dir D:\_datefac\output\demo_packaging_331a --reviewed-export-refresh-dir D:\_datefac\output\reviewed_export_refresh_330k4 --apply-simulation-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3 --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --output-dir D:\_datefac\output\demo_packaging_331b
```

#### 332A

```powershell
python tools\run_demo_release_audit_332a.py --demo-packaging-331b-dir D:\_datefac\output\demo_packaging_331b --reviewed-export-refresh-dir D:\_datefac\output\reviewed_export_refresh_330k4 --demo-packaging-331a-dir D:\_datefac\output\demo_packaging_331a --docs-demo-dir D:\_datefac\docs\demo --output-dir D:\_datefac\output\demo_release_audit_332a
```

#### 335A

```powershell
python tools\run_client_facing_clean_export_335a.py --reviewed-export-refresh-dir D:\_datefac\output\reviewed_export_refresh_330k4 --demo-packaging-331b-dir D:\_datefac\output\demo_packaging_331b --demo-release-audit-dir D:\_datefac\output\demo_release_audit_332a --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --output-dir D:\_datefac\output\client_facing_clean_export_335a
```

### Safe Files To Show

The current safest showcase files are:

- `docs/demo/datefac_demo_overview_331b.md`
- `docs/demo/datefac_resume_bullets_331b.md`
- `docs/demo/datefac_github_readme_section_331b.md`
- `docs/demo/datefac_demo_script_331b.md`
- `docs/demo/datefac_demo_release_checklist_332a.md`
- `docs/demo/datefac_interview_talking_points_332a.md`
- `docs/demo/（中文新手指南）datefac_newbie_operator_guide_333a_zh.md`
- `docs/demo/（英文新手指南）datefac_newbie_operator_guide_333a_en.md`
- `docs/demo/（中文运行手册）datefac_current_runbook_333a_zh.md`
- `docs/demo/（英文运行手册）datefac_current_runbook_333a_en.md`
- `docs/demo/（中文项目总览）datefac_project_overview_333a_zh.md`
- `docs/demo/（英文项目总览）datefac_project_overview_333a_en.md`

For live local walkthroughs, the following 335A output artifacts are also useful to open, but they should remain unstaged because they are generated output:

- `D:\_datefac\output\client_facing_clean_export_335a\client_facing_clean_export_335a_preview.xlsx`
- `D:\_datefac\output\client_facing_clean_export_335a\client_facing_clean_export_335a_summary.json`

### Safety Boundaries

The project description should always keep these boundaries visible:

- no production write-back
- do not present the project as directly deliverable to a client
- do not present the project as ready for production deployment or production write-back
- `output/*` should not be committed
- official assets are protected
- protected dirty files should not be staged
- the current path is sidecar, demo, and preview oriented
- human review is isolated before any future write-back design discussion

### Current Limitations

The project remains limited in important ways:

1. It is still a client-facing clean preview export rather than a production release.
2. Parser quality remains a bottleneck, especially for noisy or structurally messy tables.
3. The clean export is still a preview artifact and not a final client-delivery export contract.
4. It still needs broader real-world benchmarking.
5. It still needs a clearer operator UI and workflow than workbook-only review.
6. It still lacks deployment, security, access-control, and data-isolation work required for production.

### Next Milestones

The most reasonable next milestones are:

1. validate and harden the client-facing clean preview export against broader document variability
2. expand the unfamiliar-PDF benchmark scope
3. improve the manual review workflow and operator ergonomics
4. discuss production write-back design only after sufficient dry-run proof exists
5. add deployment, security, and data-isolation design before any production ambition
