# DateFac 项目进程账本 / Project Milestone Ledger

Generated / last refreshed: 2026-06-10

## 用途 / Purpose

中文：
这份账本是 DateFac 编号任务的项目级事实源，用来记录从项目启动到当前阶段每一步真实完成了什么、哪些路线已经 superseded、当前有效主线是什么，以及下一步应该接着做什么。任何新聊天、新模型或新的 Codex 线程，都不应从零重新判断主线，而应先读这份账本。

English:
This ledger is the project-level source of truth for numbered DateFac work. It records what was actually completed, which routes were superseded, what the effective mainline is now, and what the next task should be. New chats, new models, and new Codex runs should read this file before making any numbered-task decision.

## 当前有效主线 / Current Effective Mainline

中文：
当前有效主线已经不是旧的 text-candidate 路线，而是 MinerU-first / table-first。342E 的旧 435 条 text-candidate 路线已经 superseded；342E 的 table-first 版本才是当前有效版本；342F table-first core financial long-form extraction 已完成。当前下一步仍应是 342G，而不是回头重跑 342C6、342D、旧 342E 或 342F。

English:
The effective mainline is no longer the old text-candidate route. It is now MinerU-first / table-first. The old 342E 435-row text-candidate route is superseded; the table-first 342E route is the effective version; and 342F table-first core financial long-form extraction is completed. The current next task remains 342G rather than rerunning 342C6, 342D, old 342E, or 342F.

```text
legacy demo / Trust Engine / human-review work
-> MinerU-first real PDF benchmark
-> table-first MinerU output audit
-> table-first core financial long-form extraction
```

Current next task / 当前下一步:

```text
342G Table-First Extraction Review Package
```

## 文档目录职责 / Docs And Skills Responsibilities

中文：
- `.skills/`：写“怎么做事”的流程规则、前置检查、git 纪律、验证边界。
- `docs/project_milestones/`：写“项目做到哪一步了”的事实账本、阶段状态、no-repeat source of truth。
- `docs/codex_tasks/`：写“单个编号任务怎么做”的任务说明。
- `docs/project_handoffs/`：写给新线程、新模型、新接手者的交接文档。
- `docs/project_timelines/`：写按时间顺序整理的阶段演进记录。
- `docs/demo/`：写对外 demo、runbook、架构讲解、操作手册。
- `docs/architecture/`：写架构边界、模块责任、迁移/设计说明。
- `docs/assets/`：写资产包、证据层和产物说明。

English:
- `.skills/`: workflow rules, preflight, git discipline, and validation boundaries.
- `docs/project_milestones/`: project facts, stage status, and the no-repeat source of truth.
- `docs/codex_tasks/`: single numbered task specifications.
- `docs/project_handoffs/`: handoff notes for new chats, new models, and new contributors.
- `docs/project_timelines/`: chronological project evolution records.
- `docs/demo/`: external demo materials, runbooks, and presentation-friendly guides.
- `docs/architecture/`: architecture boundaries, module responsibilities, and migration/design notes.
- `docs/assets/`: artifact-layer and evidence-layer documentation.

## 任务开始前必读 / Required Preflight Before Any Numbered Task

中文：
开始任何编号任务前，必须先读：
1. `AGENTS.md`
2. `.skills/README.md`
3. `.skills/git_workflow.md`
4. `.skills/project_milestone_ledger.md`
5. `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
6. 当前任务相关的 `docs/codex_tasks/*.md`
7. 上一阶段 output 中的 summary / qa JSON / report

English:
Before starting any numbered task, read:
1. `AGENTS.md`
2. `.skills/README.md`
3. `.skills/git_workflow.md`
4. `.skills/project_milestone_ledger.md`
5. `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
6. the relevant `docs/codex_tasks/*.md`
7. previous-stage summary / QA JSON / reports

## 防重复规则 / No-Repeat Rules

中文：
- 如果某个编号任务已经 `completed` 且 `qa_fail_count = 0`，不要重复执行，除非用户明确要求 revision 或 rerun。
- 每当旧路线被新路线替代，必须保留历史并明确标记 `superseded`，不能直接抹掉历史。
- 当前不要重跑：`342C6`、`342D`、旧 `342E` 435 text-candidate 路线、`342F`。
- 当前不要把 `BASIC_DATA` 混入 core financial extraction。
- 当前不要重新跑 MinerU。
- 当前不要调用 VLM/LLM 参与这条 table-first benchmark 主线。

English:
- If a numbered task is already `completed` with `qa_fail_count = 0`, do not repeat it unless the user explicitly requests a revision or rerun.
- When a new route replaces an old one, keep history and mark the old route as `superseded`.
- Do not rerun `342C6`, `342D`, the old 342E 435-row text-candidate route, or `342F`.
- Do not mix `BASIC_DATA` into core financial extraction.
- Do not rerun MinerU for this current table-first chain.
- Do not call VLM/LLM for this benchmark mainline.

Completed chains that should not be restarted by default / 默认不要重启的已完成链路:

- `306N-310D` legacy core metric demo-ready pipeline
- `320D-322I` parser / router / semantic adjudicator chain
- `324 / 325` official rule governance cycles
- `330A-330L` Trust Engine and client-style preview chain
- `340B-341A` human-reviewed client preview milestone chain
- `342A-342F` current MinerU real-PDF benchmark chain

## Git 与安全边界 / Git And Safety Guardrails

中文：
本账本相关更新也必须遵守项目级 git 纪律。不要 stage output、temp、semantic adjudicator 响应目录、受保护脏文件，也不要用 `git add -A`、`git add .`、`git reset --hard`、`git checkout --` 之类会放大风险的命令。

English:
Ledger refreshes must follow the project git discipline as well. Never stage output artifacts, temp files, semantic adjudicator response folders, or protected dirty files, and never use `git add -A`, `git add .`, `git reset --hard`, or `git checkout --`.

Never stage these unless explicitly requested / 除非用户明确要求，否则不要 stage:

- `output/`
- `temp/`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- large generated benchmark/demo artifacts
- unrelated dirty files

Protected dirty files / dirs:

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## 状态词汇 / Status Vocabulary

- `completed`: task output exists and QA passed.
- `completed_with_warnings`: output exists and QA passed, but caveats remain.
- `superseded`: older behavior replaced by a later effective version.
- `blocked`: task could not proceed due to missing input/environment.
- `planned`: task designed but not implemented.
- `do_not_repeat`: completed stage should not be rerun without explicit revision request.

---

# 1. 旧版核心指标主线 306N-310D / Legacy Core Metric Pipeline: 306N-310D

中文：
这一段是 DateFac 较早期的 demo-ready 核心指标主线，证明过“可信预览 + review-required 分流”可以跑通，但它不是当前 MinerU-first / table-first 主线。

English:
This was the earlier demo-ready core-metric pipeline. It proved the trusted-preview plus review-required split, but it is not the current MinerU-first / table-first mainline.

## 306N Grouped Human Review Validation

Status: `completed`

Purpose:

- Validate grouped human review input.
- Check `group_id`, `reviewer_id`, `reviewed_at`, `decision`, forbidden fields, and group-to-candidate mapping.

Result:

- Human review workbooks can be safely recognized and validated.

Do not repeat:

- Do not rebuild grouped human review validation unless changing the review schema.

## 306O / 306P / 306Q Human Review Expansion And Candidate Pool

Status: `completed`

Purpose:

- Expand group-level review to candidate-level review.
- Build reviewed candidate pool.

Key validated behavior:

- No fake candidate IDs.
- Missing candidates handled separately.
- Rejected / needs_more_info do not enter trusted.
- Duplicate key count = 0.
- Value conflict count = 0.

Result:

- Human review results can safely flow into preview/export layers.

## 306R / 306S / 306T Human Review Projection, Unit Gate, Missing Intake

Status: `completed`

Purpose:

- Project reviewed candidates.
- Normalize units conservatively.
- Validate missing candidate intake.

Result:

- Manual corrections, units, and missing candidates do not break trusted preview.

## 306U-306Z Auto-Accept Policy Simulations

Status: `completed`

Purpose:

- Explore strict, relaxed, and conservative auto-accept policies.

Conclusion:

- Auto-accept can help but must remain risk-calibrated.
- No blind merge of simulated rescue rows.

## 307A Core Metric Final Export Preview

Status: `completed`

Key metrics:

- `auto_accept_core_rows = 15`
- `manual_reviewed_core_rows = 24`
- `missing_intake_core_rows = 16`
- `final_core_preview_rows = 55`
- `review_required_rows_separate = 357`

Result:

- First dual-track output: trusted core preview + review-required pool.

## 307B Export Quality Diagnosis

Status: `completed`

Key metrics:

- `final_preview_row_count = 55`
- `review_required_row_count = 357`
- `trusted_to_total_ratio <= 13.3%`
- `covered_target_metric_count = 7/8`
- `readiness_assessment = demo_ready`
- top review burden metric = `eps`

Conclusion:

- Demo works, but trusted ratio is low.

## 307C-307G EPS Focused Human Review Closure

Status: `completed`

Purpose:

- Build and apply EPS focused human review package.

Key metrics after merge:

- `final_v1_row_count = 55`
- `final_v2_row_count = 70`
- `review_required_v1_row_count = 357`
- `review_required_v2_row_count = 342`
- `eps_trusted_added_row_count = 15`

Result:

- EPS focused review increased trusted rows and reduced review-required rows.

## 307H Final Preview V2 Quality Diagnosis

Status: `completed`

Key metrics:

- `final_preview_v2_row_count = 70`
- `review_required_v2_row_count = 342`
- `trusted_rows_delta = +15`
- `review_required_delta = -15`
- new bottleneck metric = `roe`
- `readiness_assessment_v2 = demo_ready`

## 307I ROE Review Burden Drilldown

Status: `completed`

Key metrics:

- `roe_trusted_row_count = 5`
- `roe_review_required_row_count = 41`
- `roe_suspicious_value_row_count = 10`
- `roe_focused_candidate_group_count = 1`
- `roe_must_review_group_count = 10`

Conclusion:

- ROE did not justify a full EPS-style focused review chain.

## 307X Core Metric Pipeline Stage Summary

Status: `completed`

Current state at that time:

- `trusted_rows_current = 70`
- `review_required_rows_current = 342`
- top bottleneck = `roe`
- recommended next phase = `B > C > A > D`

Interpretation:

- Legacy pipeline had an end-to-end demo, but review burden remained high.

## 308A-308E Review Burden Reduction Attempts

Status: `completed_with_warnings`

Purpose:

- Simulate parser panel denoise / merge strategies.

Key results:

- 308A identified high impact opportunities: parser panel denoise, unit semantic standardization, series continuity/year gap repair.
- 308B estimated panel issue reduction rows: conservative 85, moderate 147.
- 308C simulated `would_rescue_row_count = 148`.
- 308D safety validation: `low_risk_rescue_candidate_count = 0`, `merge_readiness = not_ready_for_merge`.
- 308E produced spot-check package, but manual continuation was not prioritized.

Conclusion:

- Panel denoise looked promising but unsafe for automatic merge.

Do not repeat:

- Do not blindly continue 308E spot-check unless explicitly reprioritized.

## 309A-309C Unit Semantic Standardization Attempts

Status: `completed_with_warnings`

Purpose:

- Simulate unit semantic rescue.

Key results:

- 309A: `unit_issue_row_count = 202`, safe/contextual candidate rows = 98.
- 309B: `would_rescue_row_count = 82`.
- 309C: `low_risk_count = 0`, `medium_risk_count = 5`, `high_risk_count = 77`.

Conclusion:

- Unit semantic rescue was not safe for direct auto-merge.

## 310A-310D Demo-Ready Export Closure

Status: `completed`

Purpose:

- Package the demo-ready trusted/review-required outputs.

Key results:

- 310A generated demo-ready export package.
- 310B QA: data safe but readability needed fixing.
- 310C generated readable workbook.
- 310D acceptance passed.

Final state:

- `status = demo_ready`
- `trusted_core_metrics = 70`
- `review_required_core_metrics = 342`
- `production_apply = false`
- `simulated_rescue_merged = false`

Do not repeat:

- Do not re-close 310D unless rebuilding the legacy demo package.

---

# 2. Parser / Router / Semantic Adjudicator 链路 320D-322I / Parser / Router / Semantic Adjudicator Chain: 320D-322I

中文：
这一段建立了 parser/router/semantic adjudicator 的架构判断，说明 PPStructure 不是主线、Pure VLM 不应做默认批量抽取、MinerU table body 逐步成为 PDF table_body baseline。

English:
This chain established the parser/router/semantic-adjudicator architecture. It confirmed that PPStructure is not the mainline, Pure VLM should not be the default batch extractor, and MinerU table body became the baseline for PDF table_body extraction.

## Effective Parser Strategy From This Chain

Status: `completed`

Effective architecture conclusion:

```text
PDF table_body: MINERU_TABLE_BODY
image-table: STRUCTTABLE_INTERVL2 / StructEqTable
semantic review: LLM / VLM semantic adjudicator
backup: Docling
weak fallback: PPStructure
```

Important boundary:

- Pure VLM / LLM is not the default batch extractor.
- LLM provides semantic suggestions only, with schema validation, deterministic gates, replay, and human confirmation.

## 320D-320G Row-Text / PPStructure Route

Status: `completed`

Key result:

- 320G `trusted_rate <= 0.0719`

Conclusion:

- PPStructure is a weak legacy fallback, not the main route.

## 321A-321B2 VLM / Pure VLM Calibration

Status: `completed`

Key result:

- 321B2 pure VLM calibrated `trusted_rate <= 0.3362`

Conclusion:

- VLM has semantic value but should not be default full-batch table extraction.

## 321C / 321C2 / 321F / 321G Recognizer Router

Status: `completed`

Router policy:

- PDF table_body -> `MINERU_TABLE_BODY`
- image-table -> `STRUCTTABLE_INTERVL2`
- pure VLM -> semantic adjudicator only
- Docling -> backup
- PPStructure -> weak fallback

321G key metrics:

- `route_total_count = 216`
- `selected_output_table_count = 38`
- `no_available_output_count = 139`
- `missing_output_worklist_count = 138`
- decision = `ROUTER_SANDBOX_INTEGRATION_READY_NEEDS_RECOGNIZER_OUTPUTS`

## 321D MinerU Body Ingestion

Status: `completed`

Key result:

- `trusted_rate <= 0.3833`

Conclusion:

- MinerU body became the PDF table_body baseline.

## 321E1-321E5 Docling / StructEqTable / Full Bakeoff

Status: `completed`

Docling:

- `trusted_rate <= 0.3068`
- status = backup candidate

StructEqTable:

- 321E3: `10 / 10` image tables parsed successfully.
- 321E4B: `core_candidate_trusted_rate <= 0.3587`, `all_candidate_trusted_rate <= 0.3054`.

321E5 ranking:

1. `MINERU_TABLE_BODY_321D`
2. `STRUCTTABLE_INTERVL2_321E4B`
3. `PURE_VLM_321B2_CALIBRATED`
4. `DOCLING_TABLE_GRID_321E2`
5. `PPSTRUCTURE_320G`

Do not repeat:

- Do not rerun full bakeoff unless adding a new parser or changing evaluation criteria.

## 322A Router-Driven Sandbox Pipeline

Status: `completed`

Key metrics:

- `selected_output_table_count: 38 -> 88`
- `no_available_output_count: 139 -> 89`
- `newly_processed_mineru_table_count = 50`
- `newly_failed_mineru_table_count = 0`
- `mineru_coverage_after_322a = 0.4`

## 322B Larger Batch Review Burden Diagnosis

Status: `completed`

Key metrics:

- `newly_processed_mineru_table_count = 45`
- `selected_output_table_count_after_322b = 133`
- `selected_candidate_total_count = 5972`
- `selected_review_required_total_count = 5310`
- top review reason = `PENDING_MINERU_BODY_TRUST_SPLIT = 4597`

Conclusion:

- Large review burden was mostly unrun trust split, not true review complexity.

## 322B2 Apply Router MinerU Trust Split

Status: `completed`

Key metrics:

- `pending_split_before_count = 4597`
- `pending_split_after_count = 0`
- `trusted_total_after_322b2 = 2479`
- `review_required_total_after_322b2 = 3358`
- `selected_core_trusted_rate_after_322b2 = 0.415104`

Conclusion:

- Trust rate restored after deterministic split.

## 322C-322F Semantic Adjudicator Design And Execution

Status: `completed`

322C:

- `input_review_required_count = 3358`
- `semantic_case_count = 120`
- `estimated_llm_resolvable_candidate_count = 1283`

322D limited execution:

- dry-run payloads = 20
- 5 response apply: accepted alias suggestion count = 1, estimated trusted gain = 22

322E replay:

- `replay_allowed_instruction_count = 1`
- `trusted_gain_322e = 22`
- `review_reduction_322e = 22`

322F larger batch:

- `response_available_count = 30`
- `accepted_alias_suggestion_count = 3`
- `out_of_scope_classification_count = 7`
- `replay_allowed_instruction_count = 10`
- `trusted_gain_322f = 49`
- `review_reduction_322f = 287`
- `qa_fail_count = 0`

Conclusion:

- LLM semantic adjudicator can reduce review burden when gated and human-confirmed.

## 322G-322I Human-Confirmed Semantic Rules

Status: `completed`

322G:

- proposal total = 10
- alias proposals = 3
- out-of-scope proposals = 7
- human reviewed file accepted all 10

322H:

- `accepted_proposal_count = 10`
- `trusted_gain_322h = 49`
- `review_reduction_322h = 287`
- `official_rule_candidate_count = 10`
- `qa_fail_count = 0`

322I:

- commit = `f7d5a6f`
- output dir = `D:/_datefac/output/official_semantic_rule_candidates_322i`
- `input_official_rule_candidate_count = 10`
- `alias_rule_candidate_count = 3`
- `scope_rule_candidate_count = 7`
- `ready_for_sandbox_application_count = 10`
- expected trusted gain = 49
- expected review reduction = 287
- `qa_fail_count = 0`
- decision = `OFFICIAL_RULE_CANDIDATES_322I_READY_FOR_322J_SANDBOX_APPLICATION`

Do not repeat:

- Do not recreate 322I package unless changing the human-confirmed proposals.

---

# 3. 官方规则治理与 Trust Engine 330A-330L / Official Rule Governance And Trust Engine: 324 / 325 / 330A-330L

中文：
这一段形成了 official rule governance 与 Trust Engine 的治理历史，说明 Trust Engine、dedup、risk scoring、client-style preview 是重要支持层，但不是当前 342 系列 MinerU benchmark 主线本身。

English:
This chain established the governance history for official rules and the Trust Engine. It remains an important support layer, but it is not the same as the current 342-series MinerU benchmark mainline.

## 324 Scope-Noise Official Rule Cycle

Status: `completed`

Final closure: 324N

Key metrics:

- official scope rule count = 1
- affected candidates = 42
- review reduction = 42
- out-of-scope or rejected gain = 42
- decision = `OFFICIAL_SCOPE_PATCH_CYCLE_324N_CLOSED_READY_FOR_NEXT_CYCLE_PLANNING`

## 325 Alias Official Rule Cycle

Status: `completed_with_warnings`

Final closure: 325P

Key metrics:

- official alias rules added = 6
- trusted gain = 45
- review reduction = 45
- cumulative official rules after 325 = 23
- cumulative trusted gain after 325 = 138
- cumulative review reduction after 325 = 503
- decision = `ALIAS_PATCH_CYCLE_325P_CLOSED_WITH_WARNINGS_READY_FOR_TRUST_ENGINE_CONSOLIDATION`

## 330A-330E Trust Engine Foundation, Scoring, Dedup, Calibration

Status: `completed`

330A:

- `risk_registry_count = 18`
- decision = `TRUST_ENGINE_FOUNDATION_330A_READY_FOR_330B_RISK_REGISTRY_AND_SCORING_INTEGRATION`

330B:

- `scoring_model_component_count = 7`
- decision = `TRUST_ENGINE_SCORING_330B_READY_FOR_330C_CACHED_CANDIDATE_TRUST_SCORING_BENCHMARK`

330C:

- `cached_candidate_count = 12076`
- `scored_record_count = 12076`
- HIGH = 5210, MEDIUM = 4445, LOW = 2133, UNKNOWN = 288
- TRUSTED = 5210, REVIEW_REQUIRED = 6866

330D:

- artifact rows = 12076
- deduped candidates = 11974
- potential false trusted = 252
- target metric ambiguous = 6720
- recommended trusted min score = 85
- recommended review min score = 60

330E:

- strict deduped candidates = 11974
- cross-artifact deduped candidates = 10911
- strict duplicate count = 102
- cross-artifact duplicate count = 1165
- dedup reliability = MEDIUM

Do not repeat:

- Do not rebuild Trust Engine foundation unless changing scoring model / risk registry.

## 330F-330H Unfamiliar PDF Benchmark

Status: `completed`

330F initial:

- unfamiliar outputs missing/empty; blocked waiting for candidate outputs.

330F4:

- lightweight candidate export smoke for 3 PDFs.
- `prepared_candidate_row_count = 83`

330H:

- unfamiliar PDFs = 13
- processed PDFs = 13
- failed PDFs = 0
- PDFs with candidates = 7
- prepared candidate rows = 117
- source pages preserved
- unit missing = 64

330F rerun:

- scored unfamiliar records = 234
- decision = `FULL_UNFAMILIAR_EXPORT_BENCHMARK_330H_READY_FOR_330I_SOURCE_ATTRIBUTION_UNIT_FIX`

## 330I-330K Source / Unit Fix And Review Sample

Status: `completed`

330I:

- input candidate rows = 117
- source page missing after = 0
- unit missing before = 64
- unit missing after = 54
- unit filled = 19
- unit unknown risk added = 54
- unit conflict flag added = 12

330J:

- strict deduped candidates = 117
- source page missing = 0
- unit missing = 54
- unit unknown risk = 54
- unit conflict risk = 12
- trusted suggestions = 120
- review-required suggestions = 114
- readiness = `DEMO_READY_WITH_MANUAL_REVIEW_CAVEATS`

330K:

- unit missing input = 54
- additional safe unit fixes = 36
- unit missing after = 18
- review sample rows = 21
- unit review required = 21
- unit conflict review = 12
- unit unknown review = 9
- decision = `UNIT_SIGNAL_REVIEW_330K_READY_FOR_330J2_DELIVERY_REFRESH`

## 330J2 / 330L Client-Style Preview

Status: `completed`

330J2:

- prepared candidate rows = 117
- strict deduped candidates = 117
- source PDF unique = 7
- source page missing = 0
- unit missing = 18
- unit conflict risk = 12
- trusted suggestions = 192
- review required = 42
- readiness = `DEMO_READY_WITH_UNIT_REVIEW_CAVEATS`

330L:

- commit = `036a2250e34fa7892349a34d77b7e993a99f2519`
- output dir = `D:/_datefac/output/client_style_export_preview_330l`
- preview workbook = `D:/_datefac/output/client_style_export_preview_330l/client_style_export_preview_330l_preview.xlsx`
- trusted sheet rows = 96
- review required sheet rows = 21
- unit review sample rows = 21
- source provenance rows = 14
- QA caveats = 7
- decision = `CLIENT_STYLE_EXPORT_PREVIEW_330L_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_331A_DEMO_PACKAGING`

331A:

- task doc created: `docs/codex_tasks/331a_demo_packaging.md`
- commit = `dd45a8d41a84a15c7bd55895e10d35d32c19328f`
- status = `planned / task_doc_created`

Do not repeat:

- Do not reimplement 330L.
- Continue from 331A only if returning to demo packaging thread.

---

# 4. 人审后客户预览里程碑 340B-341A / Human-Reviewed Client Preview Milestone: 340B-341A

中文：
这一段是当前 demo-safe / client-preview-safe 链路，已经经过 human review、apply simulation、post-human sidecar、client preview 和 audit，但它依然不是 production-ready，也不是正式投研交付。

English:
This is the current demo-safe and client-preview-safe chain. It passed human review, apply simulation, sidecar packaging, client preview generation, and audit, but it is still not production-ready and not an official research delivery pipeline.

## 340B Human Review

Status: `completed`

Key metrics:

- review queue = 77
- filled = 77
- `CORRECT_AND_CONFIRM = 12`
- `CONFIRM_AS_REVIEWED = 22`
- `REJECT = 31`
- `KEEP_NEEDS_REVIEW = 12`
- `qa_fail_count = 0`

## 340C Apply Simulation

Status: `completed`

Key metrics:

- total review queue = 77
- filled rows = 77
- pending rows = 0
- confirm as reviewed = 22
- correct and confirm = 12
- keep needs review = 12
- reject = 31
- `qa_fail_count = 0`

## 340D Full Human Review Apply Plan

Status: `completed`

Key metrics:

- final would confirm reviewed = 22
- final would apply correction and confirm = 12
- final would reject = 31
- final would keep needs review = 12
- final reviewed after human candidate count = 34
- `qa_fail_count = 0`

## 340E Sidecar Result

Status: `completed`

Key metrics:

- reviewed after human = 22
- reviewed after human corrected = 12
- reviewed after human total = 34
- rejected after human = 31
- needs review after human = 12
- `qa_fail_count = 0`

## 340F Client Preview

Status: `completed`

Key metrics:

- client preview core metric count = 34
- confirmed = 22
- corrected = 12
- needs review after human = 12
- rejected after human = 31
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`

## 340G Audit

Status: `completed`

Key metrics:

- audited core metric count = 34
- duplicate issue count = 0
- unit issue count = 0
- missing source trace count = 0
- unsafe claim count = 0
- `client_preview_audit_passed = true`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`

## 341A Human-Reviewed Client Preview Milestone

Status: `completed`

Key flags:

- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- decision = `HUMAN_REVIEWED_CLIENT_PREVIEW_MILESTONE_341A_READY`

Do not repeat:

- Do not rebuild the 340B-341A human-reviewed preview chain unless changing the review workbook or preview policy.

---

# 5. 真实 PDF / MinerU benchmark 主线 342A-342F / Real PDF / MinerU Benchmark Mainline: 342A-342F

中文：
这是当前与 342F 紧密相关的有效 benchmark 主线。关键结论是：342C 首跑因环境失败，342C2 部分恢复，342C6 成为有效的 5/5 pilot 成功基线；342D 做 parser evidence compare；342E 旧 text-candidate 版本被 superseded；342E table-first 成为有效版本；342F 已完成 long-form extraction。

English:
This is the effective benchmark chain that leads into 342F. The key story is: 342C first failed due to environment issues, 342C2 partially recovered, 342C6 became the effective 5/5 pilot-success baseline, 342D compared parser evidence, the old 342E text-candidate version was superseded, the table-first 342E route became the effective version, and 342F completed long-form extraction.

## 342A Larger Real-PDF Benchmark Plan

Status: `completed`

Key metrics:

- current PDF count = 31
- benchmark status = `READY_FOR_SMALL_SCALE_BENCHMARK`
- target PDF count min/recommended/stretch = 10 / 30 / 50
- target metrics count = 10
- sample tiers count = 6
- run plan stages = 7
- `qa_fail_count = 0`
- decision = `LARGER_REAL_PDF_BENCHMARK_PLAN_342A_READY`

## 342B Real PDF Corpus Intake

Status: `completed`

Key metrics:

- current PDF count = 31
- unique PDF count = 31
- duplicate PDF count = 0
- assigned tier count = 11
- unknown tier count = 20
- pilot / benchmark / holdout = 5 / 20 / 6
- ready for 342C = true
- recommended first run PDF count = 5
- unreadable PDF count = 0
- zero byte file count = 0
- oversized PDF count = 1
- decision = `REAL_PDF_CORPUS_INTAKE_342B_READY`

## 342C MinerU Pilot First Run

Status: `completed_with_failures / superseded_by_342C6`

Key metrics:

- pilot total = 5
- MinerU success = 0
- MinerU failed = 5
- empty output = 5
- ready for 342D = false
- decision = `MINERU_BATCH_PARSE_BENCHMARK_342C_READY_WITH_FAILURES`

Conclusion:

- Failure was environmental / SSL / HuggingFace, not final PDF parsing quality.

## 342C2 MinerU Pilot Retry After Env Fix

Status: `completed / superseded_by_342C6`

Key metrics:

- retry pilot total = 5
- success = 3
- failed = 2
- empty output = 2
- ready for 342D = conditional
- recommended next scope = inspect failed retry rows then compare
- original SSL / HuggingFace failure detected = true
- no-write-back proof = passed
- `qa_fail_count = 0`
- decision = `MINERU_PILOT_RETRY_VERIFIED_ENV_342C2_READY`

Environment note:

- Conda env = `mineru_new`
- lab dir = `E:/mineru_lab`
- model/cache dir = `E:/mineru_lab/models`
- MinerU command = `D:/anaconda/envs/mineru_new/Scripts/mineru.exe`

## 342C6 MinerU Pilot Network Recovery Rerun

Status: `completed / effective_mineru_pilot_success_baseline`

Key metrics:

- original success / failed = 3 / 2
- rerun target count = 2
- rerun success / failed = 2 / 0
- final success / failed = 5 / 0
- final empty output count = 0
- ready for 342D = true
- recommended 342D scope = `full_pilot_set_5`
- no-write-back proof = passed
- `qa_fail_count = 0`

Output:

- `D:/_datefac/output/mineru_pilot_network_recovery_342c6/mineru_pilot_network_recovery_342c6.xlsx`

New files:

- `docs/codex_tasks/342C6_mineru_pilot_network_recovery_rerun.md`
- `datefac/benchmark/mineru_pilot_network_recovery_342c6.py`
- `datefac/benchmark/mineru_pilot_network_recovery_342c6_report.py`
- `tools/run_mineru_pilot_network_recovery_342c6.py`
- `tests/benchmark/test_mineru_pilot_network_recovery_342c6.py`

Validation:

- py_compile passed
- pytest passed, 2 tests

Do not repeat:

- Do not rerun 342C / 342C2 / 342C6 unless adding new PDFs or debugging a new environment issue.

## 342D Parser Ensemble Compare Benchmark

Status: `completed`

Key metrics:

- compared PDF count = 5
- MinerU success count = 5
- MinerU artifact complete count = 5
- MinerU markdown usable count = 5
- MinerU content_list usable count = 5
- baseline available count = 2
- MinerU stronger signal count = 1
- insufficient baseline count = 3
- ready for 342E = true
- recommended 342E scope = `full_pilot_set_5_mineru_outputs`
- no-write-back proof = passed
- `qa_fail_count = 0`

Output:

- `D:/_datefac/output/parser_ensemble_compare_342d/parser_ensemble_compare_342d.xlsx`

New files:

- `docs/codex_tasks/342D_parser_ensemble_compare_benchmark.md`
- `datefac/benchmark/parser_ensemble_compare_342d.py`
- `datefac/benchmark/parser_ensemble_compare_342d_report.py`
- `tools/run_parser_ensemble_compare_342d.py`
- `tests/benchmark/test_parser_ensemble_compare_342d.py`

Boundary:

- 342D only compared parser evidence signals.
- It did not perform formal metric extraction.
- It did not claim MinerU universally beats every parser.

Do not repeat:

- Do not redo 342D unless new parser baselines or new PDFs are added.

## 342E Core Metric Candidate Quality Audit - Original Text-Candidate Version

Status: `superseded_by_table_first_342E`

Original key metrics:

- audited PDF count = 5
- target metric count = 10
- total candidate row count = 435
- PDF with candidate signal count = 5
- metrics with high/medium coverage = 10
- likely usable candidates = 17
- review-required candidates = 418
- false positive risk count = 261
- unit issue signal count = 354
- ready for 342F = true
- recommended 342F scope = `full_pilot_set_5_candidate_extraction`
- `qa_fail_count = 0`

Reason superseded:

- The text-candidate route was too noisy.
- Actual MinerU outputs already contained structured HTML table blocks in `.md`, `content_list.json`, `content_list_v2.json`, `middle.json`, and `model.json`.

Do not repeat:

- Do not use the old 435 text candidate route as the primary 342F input.

## 342E Core Metric Candidate Quality Audit - Table-First Effective Version

Status: `completed / effective_current_342E`

Purpose:

- Systematically audit MinerU table assets from the 5 successful 342C6 pilot outputs.
- Move from text-candidate-first to table-first.

Effective behavior:

- Does not continue official extraction from the old 435 text candidates.
- Reads real `output_dir` values from 342C6 final rollup.
- Reads `content_list.json`, `content_list_v2.json`, `middle.json`, `model.json`, `.md`, and `images/`.
- Performs table-first table audit and classification.
- Classifies table blocks into:
  - `CORE_FORECAST_SUMMARY`
  - `BALANCE_SHEET`
  - `INCOME_STATEMENT`
  - `CASH_FLOW_STATEMENT`
  - `VALUATION_METRICS`
  - `BASIC_DATA`
  - excluded / manual-review classes
- Marks only the core five classes as `core_extractable`.
- Marks `BASIC_DATA` as `metadata_extractable`.

Key metrics:

- `audited_pdf_count = 5`
- `total_table_block_count = 370`
- `core_extractable_table_count = 66`
- `metadata_extractable_table_count = 18`
- `excluded_table_count = 62`
- `manual_review_required_count = 224`
- `pdf_with_core_extractable_table_count = 5`
- `table_source_file_count = 25`
- `ready_for_342f = true`
- `recommended_342f_scope = table_first_core_extractable_only`
- `qa_fail_count = 0`
- decision = `CORE_METRIC_CANDIDATE_QUALITY_342E_READY`

Output:

- `D:/_datefac/output/core_metric_candidate_quality_342e/core_metric_candidate_quality_342e.xlsx`

Important sheets:

- `03_ALL_TABLE_BLOCKS`
- `05_CORE_EXTRACTABLE`
- `06_METADATA_EXTRACTABLE`
- `07_EXCLUDED_TABLES`

Changed files:

- `docs/codex_tasks/342E_core_metric_candidate_quality_audit.md`
- `datefac/benchmark/core_metric_candidate_quality_342e.py`
- `datefac/benchmark/core_metric_candidate_quality_342e_report.py`
- `tools/run_core_metric_candidate_quality_342e.py`
- `tests/benchmark/test_core_metric_candidate_quality_342e.py`

Validation:

- py_compile passed
- pytest passed, 2 tests
- real run completed
- no MinerU rerun
- no VLM call
- no production pipeline / parser / extraction / delivery modifications
- no upstream workbook write-back
- output artifacts not submitted

Do not repeat:

- Do not repeat old 342E text-candidate extraction.
- Do not rerun MinerU for 342E.
- Do not call a visual model for 342E.
- Do not mix `BASIC_DATA` into core financial extraction.

## 342F Table-First Core Financial Table Long-Form Extraction

Status: `completed`

中文：
342F 已完成，并且它建立在 342E table-first 的 `05_CORE_EXTRACTABLE` 上，而不是旧 435 条 text-candidate 路线。下一步应该是 review package，而不是再回头做抽取主干。

English:
342F is completed, and it is built on `05_CORE_EXTRACTABLE` from the effective table-first 342E workbook rather than the old 435-row text-candidate route. The next step should be the review package rather than redoing the extraction core.

Input:

- `D:/_datefac/output/real_pdf_corpus_intake_342b`
- `D:/_datefac/output/mineru_pilot_network_recovery_342c6`
- `D:/_datefac/output/parser_ensemble_compare_342d`
- `D:/_datefac/output/core_metric_candidate_quality_342e`

Key metrics:

- `audited_pdf_count = 5`
- `input_core_extractable_table_count = 66`
- `parsed_core_table_count = 66`
- `html_parse_failed_table_count = 0`
- `long_form_cell_count = 5607`
- `trusted_cell_count = 1428`
- `review_required_cell_count = 1005`
- `rejected_cell_count = 3174`
- `metric_covered_count = 17`
- `metric_year_pair_count = 94`
- `unit_issue_count = 18`
- `year_header_issue_count = 135`
- `duplicate_cell_count = 387`
- `ready_for_342g = true`
- `recommended_342g_scope = table_first_extraction_review_package`
- `qa_fail_count = 0`
- `no-write-back proof passed`

Output:

- `D:/_datefac/output/table_first_core_financial_extraction_342f/table_first_core_financial_extraction_342f.xlsx`

Decision:

- `TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_READY`

Next:

- `342G Table-First Extraction Review Package`

Do not repeat:

- Do not rerun 342F unless revising extraction policy.
- Do not return to the old 435 text-candidate route.
- Do not mix BASIC_DATA into core financial extraction.
- Do not use excluded tables for core extraction.
- Do not rerun MinerU.
- Do not call VLM/LLM.

Effective behavior:

- Read 342E table-first output.
- Use `05_CORE_EXTRACTABLE` as the primary input.
- Ignore `07_EXCLUDED_TABLES` for core extraction.
- Keep `06_METADATA_EXTRACTABLE` out of core extraction.
- Parse HTML tables.
- Expand wide financial tables into long-form cells:

```text
pdf_id | table_id | table_type | metric | year | value | unit | page | bbox | image_path | review_status
```

Hard boundaries:

- Do not modify production pipeline.
- Do not modify parser abstraction.
- Do not modify production extraction logic.
- Do not modify delivery/export logic.
- Do not modify upstream 342B / 342C6 / 342D / 342E outputs.
- Do not write back to upstream workbooks.
- Do not rerun MinerU.
- Do not call VLM / LLM.
- Do not submit output artifacts.
- `client_ready = false`
- `production_ready = false`

---

# 6. 环境账本 / Environment Ledger

## MinerU Environment

Effective local environment:

- Conda env: `mineru_new`
- Lab dir: `E:/mineru_lab`
- Lab input: `E:/mineru_lab/input`
- Lab output: `E:/mineru_lab/output_new`
- Model/cache dir: `E:/mineru_lab/models`
- MinerU executable: `D:/anaconda/envs/mineru_new/Scripts/mineru.exe`

Manual smoke command:

```powershell
conda activate mineru_new
mineru -p E:\mineru_lab\input -o E:\mineru_lab\output_new -b pipeline --formula false --table true
```

Important repair notes:

- Do not use `verify=False` as the formal SSL fix.
- Do not blindly run `pip install -U`.
- Keep `huggingface_hub==0.36.2` unless dependencies change intentionally.
- Use environment variables when needed:

```powershell
$env:PYTHONNOUSERSITE="1"
$env:PIP_USER="0"
```

Known user site pollution path:

- `C:/Users/哥哥/AppData/Roaming/Python/Python312/site-packages`

Do not repeat:

- Do not reinstall MinerU unless environment is broken and documented.
- Do not delete model cache unless explicitly required.

---

# 7. 已 superseded / deprecated 的主路线 / Superseded And Deprecated Routes

## Deprecated As Main Route

- PPStructure as primary parser.
- Pure VLM as default full-batch parser.
- Handwritten endless cleaning rules as the main project value.
- 342E old text-candidate route for the MinerU pilot.

## Still Valid As Support Layers

- Trust Engine scoring and routing.
- Human review and correction flow.
- Sidecar dry-run and no-write-back proof.
- Official rule candidate governance.
- Demo/client preview export patterns.
- VLM/LLM semantic adjudicator as gated helper.
- Images as visual evidence / fallback, not primary extraction if HTML tables exist.

---

# 8. 新聊天恢复提示词 / New Topic Recovery Prompt

Paste this into a new chat/model when continuing DateFac:

```text
This is DateFac, a financial research-report PDF core metric extraction project at D:/_datefac.

Do not start from scratch. First read docs/PROJECT_MILESTONE_LEDGER.md, docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md, AGENTS.md, .skills/README.md, .skills/git_workflow.md, .skills/project_milestone_ledger.md, .skills/mineru_local_benchmark_workflow.md, .skills/real_pdf_benchmark_workflow.md, .skills/human_reviewed_client_preview_workflow.md, and .skills/table_extraction.md.

The current effective mainline is MinerU-first / table-first.

Completed current chain:
- 342A real PDF benchmark plan completed.
- 342B corpus intake completed: 31 unique PDFs, pilot/benchmark/holdout = 5/20/6.
- 342C initial MinerU run failed due environment/SSL/HF, superseded.
- 342C2 retry succeeded 3/5, superseded.
- 342C6 network recovery rerun succeeded 5/5 and is the effective MinerU pilot success baseline.
- 342D parser ensemble compare completed, MinerU outputs artifact complete 5/5, ready_for_342E true.
- 342E old text-candidate route is superseded.
- 342E table-first audit completed: total_table_block_count=370, core_extractable_table_count=66, metadata_extractable_table_count=18, excluded_table_count=62, manual_review_required_count=224, pdf_with_core_extractable_table_count=5, ready_for_342f=true, recommended_342f_scope=table_first_core_extractable_only, qa_fail_count=0.
- 342F completed table-first long-form extraction: input_core_extractable_table_count=66, parsed_core_table_count=66, long_form_cell_count=5607, trusted_cell_count=1428, review_required_cell_count=1005, rejected_cell_count=3174, metric_covered_count=17, metric_year_pair_count=94, unit_issue_count=18, year_header_issue_count=135, duplicate_cell_count=387, ready_for_342g=true, qa_fail_count=0.

Do not repeat 342C6. Do not redo 342D. Do not use the old 342E 435 text candidate route. Do not rerun 342F. Do not rerun MinerU. Do not call VLM/LLM. Do not mix BASIC_DATA into core financial extraction.

Current next task:
342G Table-First Extraction Review Package.

Keep client_ready=false and production_ready=false.
Do not modify production pipeline/parser/extraction/delivery.
Do not write back to upstream workbooks.
Do not stage output/, temp/, semantic_adjudicator_responses dirs, tools/mineru_new_runner.cmd, or protected dirty files.
Use precise git add only.
```

---

# 9. 账本维护要求 / Ledger Maintenance Requirement

中文：
每完成一个编号任务，就必须马上更新这份账本；如果旧路线被替代，也必须及时写成 superseded；每累计完成 3 到 5 个编号任务，必须做一次 rollup refresh，把 current effective mainline、next task、superseded routes、no-repeat rules、以及 readiness flag 一并刷新。做完任务却不更新账本，属于流程 bug。

English:
This ledger must be updated immediately after every completed numbered task. When an old route is replaced, mark it as superseded. After every 3 to 5 numbered tasks, perform a rollup refresh that updates the effective mainline, next task, superseded routes, no-repeat rules, and readiness flags. Finishing a numbered task without refreshing the ledger is a process bug.

Minimum ledger update fields per completed task:

```text
Task ID:
Status:
Effective version:
Input dirs/files:
Output dir:
Output workbook/report:
Key metrics:
QA result:
Decision:
Next recommended task:
Do not repeat:
Touched source files:
Validation commands:
Commit SHA, if known:
```

---

# 10. 当前安全标记 / Current Safety Flags

Current safe statements:

- `demo_ready = true` for the human-reviewed preview milestone.
- `client_preview_ready = true` for 341A only.
- `client_ready = false`.
- `production_ready = false`.
- 342C6 pilot is 5/5 successful and is the effective pilot success baseline.
- 342E table-first table audit is the effective current candidate quality audit.
- 342F table-first long-form extraction is completed.
- 342G should be the next table-first extraction review package stage.

Unsafe statements:

- Do not say production-ready.
- Do not say client-ready.
- Do not say MinerU universally beats all parsers.
- Do not say all financial tables are fully extracted.
- Do not say old 435 text candidates are the current main input.
- Do not call generated outputs official financial advice or investment advice.
