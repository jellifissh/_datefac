# DateFac

> Pivot notice: the current foundation mainline is moving toward DateFac Agent, a financial document extraction audit workflow rather than a new raw PDF extraction push.
>
> Start here:
> - [datefac_agent/README.md](datefac_agent/README.md)
> - [docs/agent/AGENT_ARCHITECTURE.md](docs/agent/AGENT_ARCHITECTURE.md)
> - [docs/legacy/LEGACY_ASSET_MAP.md](docs/legacy/LEGACY_ASSET_MAP.md)

## 中文

### 一句话定位

DateFac 是一个面向券商研报 PDF 的本地结构化与可信预览治理项目，当前最成熟的能力不是“自动交付”，而是把真实 PDF 解析、规则约束、AI dry-run、人审闭环、client preview 和审计说明组织成一条可追溯、可复核、不过度承诺的 demo 链路。

### 当前阶段

- `project_status = HUMAN_REVIEWED_CLIENT_PREVIEW_MILESTONE_341A_READY`
- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `not investment advice`

### 当前完整链路

`Real PDFs -> MinerU-first extraction -> AI dry-run review -> Human review -> 340C full validation -> 340D apply plan -> 340E post-human sidecar -> 340F client preview -> 340G audit -> 341A milestone package`

### 当前可以安全描述的能力

- 支持真实研报 PDF 的 MinerU-first intake 与侧车化预览
- 支持规则驱动的 candidate precision calibration、context repair、reviewed strictness 与 year alignment QA
- 支持 AI review dry-run、A/B 对比、grounded review 与 adoption simulation
- 支持在 AI dry-run 之后把高风险行隔离到人工复核模板中
- 支持人工复核完成后的 full validation、apply plan、post-human sidecar result、client preview 和 preview audit
- 支持 no-write-back 的 milestone package 和 demo 文档同步

### 当前绝不能承诺的内容

- 宣称已经 client-ready
- 宣称已经 production-ready
- 正式 client delivery
- 自动写回上游 workbook 或 official assets
- 100% extraction accuracy
- 无需人工复核
- 投资建议或可直接用于投资决策
- 已具备规模化生产稳定性

### 341A 里程碑关键数字

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

### 337A-341A 阶段概览

#### Real PDF intake and deterministic repair

- `337A` MinerU-first real PDF intake
- `337B` candidate precision calibration
- `337C` core financial context repair
- `337D` reviewed strictness / year alignment QA

#### AI dry-run governance

- `338A` DeepSeek flash baseline
- `338B` `AI_REVIEW_MODEL` A/B evaluation
- `338C` grounded AI review
- `338D` adoption simulation

#### Human review and preview closure

- `340B` human review package after AI adoption
- `340C` human review apply simulation with full validation support
- `340D` full human review apply plan
- `340E` post-human-review sidecar result
- `340F` human-reviewed client preview export
- `340G` client preview export audit
- `341A` human-reviewed client preview milestone package

### 340B-341A 的里程碑含义

这组阶段证明的不是“系统已经可以正式交付”，而是：

1. AI 决策仍然是 dry-run only。
2. 人工复核被明确放在 client preview 之前。
3. 所有应用结果都以 sidecar / no-write-back 方式存在。
4. client preview 经过了 duplicate、unit、source trace、unsafe claim 审计。
5. 当前最适合展示的是 human-reviewed client preview milestone，而不是 production pipeline。

### 当前 demo 能展示什么

- 真实 PDF 如何进入 MinerU-first 解析链路
- deterministic rules 如何压缩明显噪声并修复上下文
- AI review 如何作为 dry-run 判断层，而不是最终 truth layer
- 人审工作簿如何承接 AI adoption 之后仍需人工判断的队列
- full validation、apply plan 和 post-human sidecar 如何保证不写回上游
- client preview 如何只展示 34 条经过人审确认或修正确认的核心指标
- preview audit 如何确认 duplicate/unit/source trace/claim 风险为零

### 当前 benchmark 边界

- 当前 benchmark 仍然是有限真实 PDF 样本，不代表规模化生产稳定性
- 当前结果最适合用于 demo、GitHub 说明、面试讲解、技术路线审计
- 当前结果不代表 parser 在更多版式、更多券商、更多跨页表格上的稳定表现
- 当前结果不代表 metadata extraction、batch reliability、权限治理、可运维性已经闭环

### 下一阶段瓶颈

- 更大 benchmark
- parser robustness
- metadata extraction
- UI review workflow
- batch reliability

### 推荐阅读顺序

1. `README.md`
2. `docs/demo/datefac_human_reviewed_client_preview_runbook_341b_zh.md`
3. `docs/demo/datefac_human_reviewed_client_preview_architecture_341b_zh.md`
4. `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_zh.md`
5. `docs/demo/datefac_ai_review_architecture_339a_zh.md`
6. `docs/demo/datefac_demo_release_checklist_332a.md`
7. `docs/demo/（中文项目总览）datefac_project_overview_333a_zh.md`
8. `docs/demo/（中文运行手册）datefac_current_runbook_333a_zh.md`

## English

### One-Line Positioning

DateFac is a local trust-governed structuring and preview project for financial research PDFs. Its most mature capability today is not automatic delivery, but a disciplined demo chain that combines real-PDF parsing, deterministic constraints, AI dry-run review, human review, client-preview packaging, and claim-safe auditability.

### Current Status

- `project_status = HUMAN_REVIEWED_CLIENT_PREVIEW_MILESTONE_341A_READY`
- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `not investment advice`

### Current End-To-End Path

`Real PDFs -> MinerU-first extraction -> AI dry-run review -> Human review -> 340C full validation -> 340D apply plan -> 340E post-human sidecar -> 340F client preview -> 340G audit -> 341A milestone package`

### Safe Current Claims

- real research PDFs can enter a MinerU-first sidecar preview flow
- deterministic calibration, context repair, reviewed strictness, and year-alignment QA exist
- AI review exists as dry-run evaluation, A/B comparison, grounded review, and adoption simulation
- human review is inserted before client preview
- post-human sidecar result, client preview export, and client preview audit exist without write-back
- milestone packaging and demo documentation now reflect the audited human-reviewed preview state

### Unsafe Claims

- claiming the project is already client-ready
- claiming the project is already production-ready
- official client delivery readiness
- upstream workbook write-back
- 100% extraction correctness
- no-human-review automation
- investment advice
- scalable production stability

### 341A Milestone Headline Metrics

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

### Stage Groups

#### Real PDF intake and deterministic repair

- `337A` MinerU-first real PDF intake
- `337B` candidate precision calibration
- `337C` core financial context repair
- `337D` reviewed strictness / year alignment QA

#### AI dry-run governance

- `338A` DeepSeek flash baseline
- `338B` `AI_REVIEW_MODEL` A/B evaluation
- `338C` grounded AI review
- `338D` adoption simulation

#### Human review and preview closure

- `340B` human review package after AI adoption
- `340C` human review apply simulation with full validation support
- `340D` full human review apply plan
- `340E` post-human-review sidecar result
- `340F` human-reviewed client preview export
- `340G` client preview export audit
- `341A` human-reviewed client preview milestone package

### What 340B-341A Actually Prove

These stages do not prove production adoption. They prove that:

1. AI decisions remain dry-run only.
2. Human review is explicitly required before client preview.
3. All application results remain sidecar and no-write-back.
4. The client preview was audited for duplicate, unit, source-trace, and unsafe-claim risk.
5. The current strongest deliverable is a human-reviewed client preview milestone, not a production pipeline.

### What The Current Demo Can Show

- how real PDFs enter the MinerU-first parsing flow
- how deterministic rules suppress obvious noise and repair context
- how AI review stays assistive and dry-run only
- how workbook-based human review closes the loop before preview promotion
- how full validation, apply planning, and post-human sidecar handling preserve no-write-back boundaries
- how the client preview includes only 34 human-reviewed core metrics
- how the preview audit confirms zero duplicate, unit, source-trace, and unsafe-claim issues

### Benchmark Boundary

- the current benchmark is still a limited real-PDF sample set, not evidence of scalable production stability
- the present state is strongest for demos, GitHub explanations, interviews, and technical audits
- it does not prove broad parser robustness across more layouts, brokers, and cross-page tables
- it does not prove metadata extraction, batch reliability, permissions, or operational hardening are solved

### Next Bottlenecks

- larger benchmark
- parser robustness
- metadata extraction
- UI review workflow
- batch reliability

### Recommended Reading

1. `README.md`
2. `docs/demo/datefac_human_reviewed_client_preview_runbook_341b_en.md`
3. `docs/demo/datefac_human_reviewed_client_preview_architecture_341b_en.md`
4. `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_en.md`
5. `docs/demo/datefac_ai_review_architecture_339a_en.md`
6. `docs/demo/datefac_demo_release_checklist_332a.md`
7. `docs/demo/（英文项目总览）datefac_project_overview_333a_en.md`
8. `docs/demo/（英文运行手册）datefac_current_runbook_333a_en.md`

### Repository Navigation

- `docs/architecture/project_directory_governance.md`: lightweight directory responsibility guide
- `docs/demo/mineru_runbook.md`: current MinerU runbook and benchmark entry references
- `docs/codex_tasks/`: numbered task specs and boundaries
- `tools/`: runnable entry points and local environment helpers
- `datefac/`: importable source package
- `tests/`: focused automated checks
