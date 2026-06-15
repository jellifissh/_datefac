# DateFac 项目进程账本 / Project Milestone Ledger

Generated / last refreshed: 2026-06-11

## 用途 / Purpose

中文：
这份账本是 DateFac 编号任务的项目级事实源，用来记录从项目启动到当前阶段每一步真实完成了什么、哪些路线已经 superseded、当前有效主线是什么，以及下一步应该接着做什么。任何新聊天、新模型或新的 Codex 线程，都不应从零重新判断主线，而应先读这份账本。

English:
This ledger is the project-level source of truth for numbered DateFac work. It records what was actually completed, which routes were superseded, what the effective mainline is now, and what the next task should be. New chats, new models, and new Codex runs should read this file before making any numbered-task decision.

## 当前有效主线 / Current Effective Mainline

中文：
当前有效主线已经不是旧的 text-candidate 路线，而是 MinerU-first / table-first。342E 的旧 435 条 text-candidate 路线已经 superseded；342E 的 table-first 版本才是当前有效版本；342F table-first core financial long-form extraction 已完成；342G、342H、342I、342J、342K、342L、342M、342N 也已经沿着当前有效主线推进完成。当前下一步应是 342O，而不是回头重跑 342C6、342D、旧 342E、342F、342G、342H 或 342I。

English:
The effective mainline is no longer the old text-candidate route. It is now MinerU-first / table-first. The old 342E 435-row text-candidate route is superseded; the table-first 342E route is the effective version; 342F table-first core financial long-form extraction is completed; 342G table-first extraction review package is completed; 342H second reviewed batch apply simulation is the effective upstream human-review state; 342I post-human-review sidecar result has been rerun with 80 reviewed rows; 342J reviewed client preview pilot is completed; 342K LLM-assisted review adjudication pilot is completed as a no-write-back adjudication helper; 342L suggestion-apply simulation is completed as a no-write-back control layer; 342M spot-check / real-response gate has been rerun with reviewed spot-check evidence and is now ready for 342N; 342N correction-aware adoption simulation is completed as the no-write-back adoption-control layer; 342O post-adoption sidecar simulation is completed as the simulated sidecar rollup layer; 342P reviewed plus simulated client preview pilot is completed as the bounded preview aggregation layer; and 342Q preview audit and export-readiness gate is now completed as the current preview-boundary control layer. The current next task is 342R audit-labeled export candidate package rather than rerunning 342C6, 342D, old 342E, 342F, 342G, 342H, 342I, 342J, 342O, or 342P.

```text
legacy demo / Trust Engine / human-review work
-> MinerU-first real PDF benchmark
-> table-first MinerU output audit
-> table-first core financial long-form extraction
```

Current next task / 当前下一步:

```text
342R audit-labeled export candidate package
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

## 342G Table-First Extraction Review Package

Status: `completed`

中文：
342G 已完成。它把 342F 的 table-first long-form extraction 结果整理成了可人工复核的 review workbook：`REVIEW_REQUIRED` 进入主复核队列，`TRUSTED_CELL` 进入受控抽样 spot-check，unit / year / duplicate / growth-row 风险被单独汇总，供下一步 342H apply simulation 使用。342G 仍然只是 sidecar review package，不是正式财务结果，不写回上游 workbook，不是 client-ready，也不是 production-ready。

English:
342G is completed. It packages the 342F table-first long-form extraction output into a human-review workbook: `REVIEW_REQUIRED` rows become the main review queue, `TRUSTED_CELL` rows become a bounded spot-check sample, and unit / year / duplicate / growth-row risks are rolled up for the next 342H apply simulation step. 342G remains a sidecar review package only, does not write back upstream workbooks, and is neither client-ready nor production-ready.

Input:

- `D:/_datefac/output/real_pdf_corpus_intake_342b`
- `D:/_datefac/output/mineru_pilot_network_recovery_342c6`
- `D:/_datefac/output/parser_ensemble_compare_342d`
- `D:/_datefac/output/core_metric_candidate_quality_342e`
- `D:/_datefac/output/table_first_core_financial_extraction_342f`

Output:

- `D:/_datefac/output/table_first_extraction_review_package_342g/table_first_extraction_review_package_342g.xlsx`

Key metrics:

- `audited_pdf_count = 5`
- `input_long_form_cell_count = 5607`
- `input_trusted_cell_count = 1428`
- `input_review_required_cell_count = 1005`
- `input_rejected_cell_count = 3174`
- `review_queue_count = 1005`
- `trusted_audit_sample_count = 150`
- `unit_year_issue_count = 4128`
- `duplicate_issue_count = 210`
- `growth_row_issue_count = 174`
- `high_priority_review_count = 702`
- `medium_priority_review_count = 437`
- `low_priority_review_count = 16`
- `review_template_row_count = 1155`
- `ready_for_342h = true`
- `recommended_342h_scope = table_first_human_review_apply_simulation`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- all required 342F inputs detected
- review queue generated from `05_REVIEW_REQUIRED` only
- trusted audit generated from `04_TRUSTED_CELLS` only
- rejected / excluded / `BASIC_DATA` rows not mixed into core review queue
- source trace fields preserved
- reviewer fields blank in generated template
- no upstream workbook modified
- no protected dirty files staged
- no output artifacts staged

Decision:

- `TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_READY`

Next:

- `342H Table-First Human Review Apply Simulation`

Do not repeat:

- Do not rerun MinerU for 342G.
- Do not call VLM / LLM for 342G.
- Do not go back to the old 435 text-candidate route.
- Do not treat 342G workbook as formal client delivery.
- Do not write back to upstream 342B / 342C6 / 342D / 342E / 342F workbooks.

Touched source files:

- `docs/codex_tasks/342G_table_first_extraction_review_package.md`
- `datefac/benchmark/table_first_extraction_review_package_342g.py`
- `datefac/benchmark/table_first_extraction_review_package_342g_report.py`
- `tools/run_table_first_extraction_review_package_342g.py`
- `tests/benchmark/test_table_first_extraction_review_package_342g.py`

Validation commands:

```powershell
python -m py_compile datefac\benchmark\table_first_extraction_review_package_342g.py datefac\benchmark\table_first_extraction_review_package_342g_report.py tools\run_table_first_extraction_review_package_342g.py tests\benchmark\test_table_first_extraction_review_package_342g.py

python -m pytest tests\benchmark\test_table_first_extraction_review_package_342g.py -q

python tools\run_table_first_extraction_review_package_342g.py --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b --mineru-342c6-dir D:\_datefac\output\mineru_pilot_network_recovery_342c6 --parser-compare-342d-dir D:\_datefac\output\parser_ensemble_compare_342d --candidate-quality-342e-dir D:\_datefac\output\core_metric_candidate_quality_342e --core-extraction-342f-dir D:\_datefac\output\table_first_core_financial_extraction_342f --output-dir D:\_datefac\output\table_first_extraction_review_package_342g
```

---

## 342H Table-First Human Review Apply Simulation

Status: `completed`

Effective version:

- `effective_current_342H_second_reviewed_batch_applied`
- old waiting branch = `superseded_by_reviewed_batch_state`

中文：
342H 已完成，并且已经从最早的 waiting-for-human-review 状态推进到“前两批共 80 条人审已真实应用”的当前有效状态。它读取已填写的人审 workbook，验证 reviewer decisions，并以 no-write-back 方式生成 apply simulation 结果。当前这 80 条结果已经可供 342I 继续消费，但不代表全量人审已经完成。

English:
342H is completed and has moved beyond the original waiting-for-human-review branch into the current effective state where the first two reviewed batches, totaling 80 rows, have been applied. It consumes the reviewed workbook, validates reviewer decisions, and produces a no-write-back apply simulation result. These 80 reviewed rows are now usable by 342I, but they do not mean the full review queue is complete.

Input dirs/files:

- `D:/_datefac/output/table_first_extraction_review_package_342g`
- `D:/_datefac/output/table_first_extraction_review_package_342g/table_first_extraction_review_package_342g.xlsx`
- `D:/_datefac/input/table_first_review_342g_reviewed`
- `D:/_datefac/input/table_first_review_342g_reviewed/table_first_extraction_review_package_342g_reviewed.xlsx`

Output dir:

- `D:/_datefac/output/table_first_human_review_apply_simulation_342h`

Output workbook/report:

- `D:/_datefac/output/table_first_human_review_apply_simulation_342h/table_first_human_review_apply_simulation_342h.xlsx`
- `D:/_datefac/output/table_first_human_review_apply_simulation_342h/table_first_human_review_apply_simulation_342h_report.md`

Key metrics:

- `reviewed_workbook_exists = true`
- `input_review_template_row_count = 1155`
- `reviewed_row_count = 80`
- `pending_review_count = 1075`
- `confirmed_cell_count = 31`
- `corrected_cell_count = 10`
- `rejected_cell_count = 39`
- `still_review_required_count = 0`
- `needs_source_check_count = 0`
- `validation_error_count = 0`
- `net_confirmed_after_human_count = 41`
- `net_review_reduction_count = 80`
- `ready_for_342i = true`
- `recommended_342i_scope = table_first_post_human_review_sidecar_result`
- `recommended_next_action = proceed_to_342i`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 342G summary / QA / workbook detected
- reviewed workbook detected and consumed
- blank reviewer decisions preserved as pending
- allowed reviewer decisions enforced
- corrected rows validated
- source trace preserved
- no upstream workbook modified
- no protected dirty files staged
- no output artifacts staged
- no sheet name exceeds 31 chars

Decision:

- `TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_READY`

Next recommended task:

- `342I Table-First Post-Human-Review Sidecar Result`

Do not repeat:

- Do not rerun MinerU for 342H.
- Do not call VLM / LLM for 342H.
- Do not fabricate human review conclusions.
- Do not write back to upstream 342G workbook or any earlier workbook.
- Do not claim full human review completion from the current 80-row reviewed batch.

Touched source files:

- `docs/codex_tasks/342H_table_first_human_review_apply_simulation.md`
- `datefac/benchmark/table_first_human_review_apply_simulation_342h.py`
- `datefac/benchmark/table_first_human_review_apply_simulation_342h_report.py`
- `tools/run_table_first_human_review_apply_simulation_342h.py`
- `tests/benchmark/test_table_first_human_review_apply_simulation_342h.py`

Validation commands:

```powershell
python -m py_compile datefac\benchmark\table_first_human_review_apply_simulation_342h.py datefac\benchmark\table_first_human_review_apply_simulation_342h_report.py tools\run_table_first_human_review_apply_simulation_342h.py tests\benchmark\test_table_first_human_review_apply_simulation_342h.py

python -m pytest tests\benchmark\test_table_first_human_review_apply_simulation_342h.py -q

python tools\run_table_first_human_review_apply_simulation_342h.py --review-package-342g-dir D:\_datefac\output\table_first_extraction_review_package_342g --reviewed-input-dir D:\_datefac\input\table_first_review_342g_reviewed --output-dir D:\_datefac\output\table_first_human_review_apply_simulation_342h
```

Commit SHA, if known:

- `9d749713be05beedaf9d3d6a08bf9fd180c45911`

---

## 342I Table-First Post-Human-Review Sidecar Result

Status: `completed`

Effective version:

- `effective_current_342I_rerun_with_80_reviewed_rows`

中文：
342I 已完成。它读取当前真实的 342H apply simulation 结果，并已基于最新 80 条 reviewed rows 重跑，把其中 41 条 confirmed/corrected cells 整理成 post-human-review sidecar result，同时保留 1075 条 pending review 和剩余风险统计。342I 只是 sidecar result，不是正式财务结果，也不是正式 client delivery。

English:
342I is completed. It consumes the current real 342H apply simulation output and has been rerun against the latest 80 reviewed rows, packaging 41 human-confirmed or human-corrected cells into a post-human-review sidecar result while preserving 1075 pending review rows plus remaining-risk summaries. 342I is a sidecar result only, not a formal financial output and not a formal client delivery package.

Input dirs/files:

- `D:/_datefac/output/table_first_human_review_apply_simulation_342h`
- `D:/_datefac/output/table_first_human_review_apply_simulation_342h/table_first_human_review_apply_simulation_342h.xlsx`

Output dir:

- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i`

Output workbook/report:

- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i/table_first_post_human_review_sidecar_result_342i.xlsx`
- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i/table_first_post_human_review_sidecar_result_342i_report.md`

Key metrics:

- `input_review_template_row_count = 1155`
- `reviewed_row_count = 80`
- `pending_review_count = 1075`
- `input_confirmed_cell_count = 31`
- `input_corrected_cell_count = 10`
- `input_rejected_cell_count = 0`
- `final_confirmed_cell_count = 31`
- `final_corrected_cell_count = 10`
- `final_rejected_cell_count = 39`
- `post_human_confirmed_count = 41`
- `post_human_reviewed_cell_count = 80`
- `metric_covered_after_human_count = 5`
- `metric_year_pair_after_human_count = 25`
- `remaining_review_count = 1075`
- `unit_year_remaining_count = 889`
- `duplicate_remaining_count = 348`
- `growth_row_remaining_count = 140`
- `source_check_remaining_count = 0`
- `ready_for_342j = true`
- `recommended_342j_scope = table_first_reviewed_client_preview_pilot`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 342H summary / QA / workbook detected
- 342H `ready_for_342i = true` detected
- final confirmed rows come only from `CONFIRM_CELL`
- final corrected rows come only from `CORRECT_AND_CONFIRM`
- corrected rows actually use reviewer correction fields
- pending rows preserved
- source trace preserved
- no upstream workbook modified
- no reviewed input workbook staged
- no protected dirty files staged
- no output artifacts staged
- no sheet name exceeds 31 chars

Decision:

- `TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_READY`

Next recommended task:

- `342J Table-First Reviewed Client Preview Pilot`

Do not repeat:

- Do not rerun MinerU for 342I.
- Do not call VLM / LLM for 342I.
- Do not claim full human review completion from the current 80-row batch.
- Do not claim `client_ready = true`.
- Do not claim `production_ready = true`.
- Do not write back to 342H or any earlier workbook.

Touched source files:

- `docs/codex_tasks/342I_table_first_post_human_review_sidecar_result.md`
- `datefac/benchmark/table_first_post_human_review_sidecar_result_342i.py`
- `datefac/benchmark/table_first_post_human_review_sidecar_result_342i_report.py`
- `tools/run_table_first_post_human_review_sidecar_result_342i.py`
- `tests/benchmark/test_table_first_post_human_review_sidecar_result_342i.py`

Validation commands:

```powershell
python -m py_compile datefac\benchmark\table_first_post_human_review_sidecar_result_342i.py datefac\benchmark\table_first_post_human_review_sidecar_result_342i_report.py tools\run_table_first_post_human_review_sidecar_result_342i.py tests\benchmark\test_table_first_post_human_review_sidecar_result_342i.py

python -m pytest tests\benchmark\test_table_first_post_human_review_sidecar_result_342i.py -q

python tools\run_table_first_post_human_review_sidecar_result_342i.py --human-review-342h-dir D:\_datefac\output\table_first_human_review_apply_simulation_342h --output-dir D:\_datefac\output\table_first_post_human_review_sidecar_result_342i
```

Commit SHA, if known:

- `8d353142170cc3efedc169fcea5d9b568a53e120`

---

## 342J Table-First Reviewed Client Preview Pilot

Status: `completed`

Effective version:

- `effective_current_342J_reviewed_client_preview_pilot`

中文：
342J 已完成。它读取当前真实的 342I post-human-review sidecar result，把 80 条 reviewed rows 中可进入 preview 的 41 条 confirmed/corrected cells 整理成 reviewed client preview pilot，并把 1075 条 pending review、39 条 rejected/not-core 以及剩余风险显式保留下来。342J 只是 reviewed client preview pilot，不是正式 client delivery，也不是 production-ready。

English:
342J is completed. It consumes the current real 342I post-human-review sidecar result, packages the 41 preview-eligible confirmed/corrected rows from the current 80 reviewed rows into a reviewed client preview pilot, and explicitly preserves the 1075 pending review rows, 39 rejected or not-core rows, and remaining-risk counts. 342J is a reviewed client preview pilot only, not formal client delivery and not production-ready.

Input dirs/files:

- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i`
- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i/table_first_post_human_review_sidecar_result_342i.xlsx`

Output dir:

- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`

Output workbook/report:

- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j/table_first_reviewed_client_preview_pilot_342j.xlsx`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j/table_first_reviewed_client_preview_pilot_342j_report.md`

Key metrics:

- `input_review_template_row_count = 1155`
- `reviewed_row_count = 80`
- `pending_review_count = 1075`
- `input_post_human_confirmed_count = 41`
- `reviewed_preview_row_count = 41`
- `confirmed_preview_row_count = 31`
- `corrected_preview_row_count = 10`
- `rejected_in_batch_count = 39`
- `metric_covered_count = 5`
- `metric_year_pair_count = 25`
- `pdf_covered_count = 1`
- `table_covered_count = 4`
- `remaining_review_count = 1075`
- `unit_year_remaining_count = 889`
- `duplicate_remaining_count = 348`
- `growth_row_remaining_count = 140`
- `source_trace_missing_count = 0`
- `ready_for_342k = true`
- `recommended_342k_scope = llm_assisted_review_adjudication_or_preview_polish`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 342I summary / QA / workbook detected
- 342I `ready_for_342j = true` detected
- preview rows come only from confirmed / corrected rows
- rejected rows are not included in preview
- pending review rows are not included in preview
- `NOT_A_CORE_METRIC` rows are not included in preview
- source trace fields are preserved
- no upstream workbook modified
- no reviewed input workbook staged
- no protected dirty files staged
- no output artifacts staged
- no sheet name exceeds 31 chars

Decision:

- `TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY`

Next recommended task:

- `342K LLM-Assisted Review Adjudication`
- `342K Reviewed Preview Polish`

Do not repeat:

- Do not rerun MinerU for 342J.
- Do not call VLM / LLM for 342J.
- Do not claim full human review completion from the current 80-row batch.
- Do not claim `client_ready = true`.
- Do not claim `production_ready = true`.
- Do not write back to 342I or any earlier workbook.

Touched source files:

- `docs/codex_tasks/342J_table_first_reviewed_client_preview_pilot.md`
- `datefac/benchmark/table_first_reviewed_client_preview_pilot_342j.py`
- `datefac/benchmark/table_first_reviewed_client_preview_pilot_342j_report.py`
- `tools/run_table_first_reviewed_client_preview_pilot_342j.py`
- `tests/benchmark/test_table_first_reviewed_client_preview_pilot_342j.py`

Validation commands:

```powershell
python -m py_compile datefac\benchmark\table_first_reviewed_client_preview_pilot_342j.py datefac\benchmark\table_first_reviewed_client_preview_pilot_342j_report.py tools\run_table_first_reviewed_client_preview_pilot_342j.py tests\benchmark\test_table_first_reviewed_client_preview_pilot_342j.py

python -m pytest tests\benchmark\test_table_first_reviewed_client_preview_pilot_342j.py -q

python tools\run_table_first_reviewed_client_preview_pilot_342j.py --post-human-review-342i-dir D:\_datefac\output\table_first_post_human_review_sidecar_result_342i --output-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j
```

Commit SHA, if known:

- pending

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

Status: `completed`

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

Status: `completed`

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

## 342K LLM-Assisted Review Adjudication Pilot

Status: `completed`

Effective version:

- `effective_current_342K_llm_assisted_review_adjudication_pilot`

中文：
342K 已完成。它读取当前真实的 342J reviewed client preview pilot、342I post-human-review sidecar result、342G review package，只从仍然 pending 的 1075 条 review rows 构建 LLM-assisted adjudication candidate pool。342K 默认不调用真实 LLM API，而是生成 rule baseline、prompt/request package、dry-run suggestions、human-required 视图，以及给 342L 使用的 review template draft。342K 仍然是 no-write-back sidecar adjudication pilot，不是正式 client delivery，也不是 production-ready。

English:
342K is completed. It consumes the current real 342J reviewed client preview pilot, 342I post-human-review sidecar result, and 342G review package, then builds an LLM-assisted adjudication candidate pool from the remaining 1075 pending review rows only. By default, 342K does not call a real LLM API. It generates rule baselines, prompt/request packages, dry-run suggestions, human-required views, and a next-stage review template draft for 342L. 342K remains a no-write-back sidecar adjudication pilot, not formal client delivery and not production-ready.

Input dirs/files:

- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j/table_first_reviewed_client_preview_pilot_342j.xlsx`
- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i`
- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i/table_first_post_human_review_sidecar_result_342i.xlsx`
- `D:/_datefac/output/table_first_extraction_review_package_342g`
- `D:/_datefac/output/table_first_extraction_review_package_342g/table_first_extraction_review_package_342g.xlsx`

Output dir:

- `D:/_datefac/output/llm_assisted_review_adjudication_342k`

Output workbook/report:

- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k.xlsx`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k_report.md`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k_prompt_pack.jsonl`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k_request_pack.jsonl`

Key metrics:

- `input_review_template_row_count = 1155`
- `reviewed_row_count = 80`
- `pending_review_count = 1075`
- `llm_candidate_pool_count = 1075`
- `prompt_package_count = 358`
- `request_pack_count = 358`
- `rule_baseline_count = 1075`
- `dry_run_suggestion_count = 1075`
- `human_required_count = 717`
- `auto_confirm_candidate_count = 254`
- `conflict_count = 763`
- `unit_year_risk_count = 577`
- `duplicate_risk_count = 348`
- `growth_row_risk_count = 152`
- `source_trace_risk_count = 498`
- `metric_mapping_risk_count = 309`
- `high_priority_risk_count = 663`
- `review_template_draft_count = 1075`
- `ready_for_342l = true`
- `recommended_342l_scope = llm_suggestion_apply_or_human_spot_check_simulation`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 342J summary / QA / workbook detected
- 342J `ready_for_342k = true` detected
- 342I workbook detected and already-reviewed rows excluded
- 342G workbook detected and review-template context reused
- prompt package generated
- expected schema generated
- dry-run suggestions clearly labeled as dry-run only
- auto-confirm rows remain candidates only
- reviewer fields stay blank in the draft template
- no upstream workbook modified
- no protected dirty files staged
- no output artifacts staged

Decision:

- `LLM_ASSISTED_REVIEW_ADJUDICATION_342K_READY`

Next:

- `342L LLM Suggestion Apply Or Human Spot-Check Simulation`

Do not repeat:

- Do not treat dry-run suggestions as real LLM output.
- Do not treat LLM suggestions as human-review results.
- Do not rerun MinerU for 342K.
- Do not call VLM for 342K.
- Do not write back to 342G / 342H / 342I / 342J workbooks.
- Do not claim `client_ready = true` or `production_ready = true`.

Touched source files:

- `docs/codex_tasks/342K_llm_assisted_review_adjudication_pilot.md`
- `datefac/benchmark/llm_assisted_review_adjudication_342k.py`
- `datefac/benchmark/llm_assisted_review_adjudication_342k_report.py`
- `tools/run_llm_assisted_review_adjudication_342k.py`
- `tests/benchmark/test_llm_assisted_review_adjudication_342k.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Validation commands:

```powershell
python -m py_compile datefac\benchmark\llm_assisted_review_adjudication_342k.py datefac\benchmark\llm_assisted_review_adjudication_342k_report.py tools\run_llm_assisted_review_adjudication_342k.py tests\benchmark\test_llm_assisted_review_adjudication_342k.py

python -m pytest tests\benchmark\test_llm_assisted_review_adjudication_342k.py -q

python tools\run_llm_assisted_review_adjudication_342k.py --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --post-human-review-342i-dir D:\_datefac\output\table_first_post_human_review_sidecar_result_342i --review-package-342g-dir D:\_datefac\output\table_first_extraction_review_package_342g --output-dir D:\_datefac\output\llm_assisted_review_adjudication_342k
```

Commit SHA, if known:

- `cfeedd563ea009271823eba1c177c58dd38b675e`

---

## 342L LLM Suggestion Apply Or Human Spot-Check Simulation

Status: `completed`

Effective version:

- `effective_current_342L_suggestion_apply_simulation`

中文：
342L 已完成。它读取当前真实的 342K adjudication pilot 与 342J reviewed preview boundary，不把 dry-run suggestions 当成真实 LLM 输出，也不把 auto-confirm candidates 当成最终确认，而是生成 suggestion-apply simulation、mandatory spot-check sample、prefill review draft、conflict blockers 和 reduction simulation。342L 仍然是 no-write-back sidecar，不是正式 client delivery，也不是 production-ready。

English:
342L is completed. It consumes the current real 342K adjudication pilot plus the 342J reviewed-preview boundary. It does not treat dry-run suggestions as real LLM outputs, and it does not treat auto-confirm candidates as final confirmations. Instead, it generates a suggestion-apply simulation, a mandatory spot-check sample, a prefilled review draft, conflict blockers, and a review-reduction simulation. 342L remains a no-write-back sidecar, not formal client delivery and not production-ready.

Input dirs/files:

- `D:/_datefac/output/llm_assisted_review_adjudication_342k`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k.xlsx`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k_prompt_pack.jsonl`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k_request_pack.jsonl`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j/table_first_reviewed_client_preview_pilot_342j.xlsx`

Output dir:

- `D:/_datefac/output/llm_suggestion_apply_simulation_342l`

Output workbook/report:

- `D:/_datefac/output/llm_suggestion_apply_simulation_342l/llm_suggestion_apply_simulation_342l.xlsx`
- `D:/_datefac/output/llm_suggestion_apply_simulation_342l/llm_suggestion_apply_simulation_342l_report.md`

Key metrics:

- `pending_review_count = 1075`
- `auto_confirm_candidate_count = 254`
- `spot_check_sample_count = 50`
- `human_required_count = 717`
- `conflict_count = 763`
- `prefill_review_draft_count = 1075`
- `prompt_pack_count = 358`
- `request_pack_count = 358`
- `jsonl_parse_error_count = 0`
- `theoretical_review_reduction_count = 254`
- `risk_adjusted_reduction_count = 204`
- `required_human_review_after_strategy = 767`
- `reduction_rate = 0.236279`
- `conservative_reduction_rate = 0.189767`
- `unit_year_risk_count = 577`
- `duplicate_risk_count = 348`
- `growth_row_risk_count = 152`
- `source_trace_risk_count = 498`
- `metric_mapping_risk_count = 309`
- `ready_for_342m = true`
- `recommended_342m_scope = llm_suggestion_spot_check_apply_or_real_llm_response_ingestion`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 342K summary / QA / workbook / prompt pack / request pack detected
- 342K `ready_for_342l = true` detected
- auto-confirm candidates remain candidates only
- human-required rows remain outside auto-apply
- conflict blockers remain outside auto-apply
- reviewer fields stay blank in prefill review draft
- spot-check sample generated
- prompt/request jsonl parsed successfully
- no upstream workbook modified
- no protected dirty files staged
- no output artifacts staged

Decision:

- `LLM_SUGGESTION_APPLY_SIMULATION_342L_READY`

Next:

- `342M LLM Suggestion Spot-Check Apply Or Real LLM Response Ingestion`

Do not repeat:

- Do not treat dry-run suggestions as real LLM output.
- Do not treat auto-confirm candidates as final confirmations.
- Do not skip human spot-check before any broader adoption.
- Do not write back to 342J / 342K or earlier workbooks.
- Do not claim `client_ready = true` or `production_ready = true`.

Touched source files:

- `docs/codex_tasks/342L_llm_suggestion_apply_or_human_spot_check_simulation.md`
- `datefac/benchmark/llm_suggestion_apply_simulation_342l.py`
- `datefac/benchmark/llm_suggestion_apply_simulation_342l_report.py`
- `tools/run_llm_suggestion_apply_simulation_342l.py`
- `tests/benchmark/test_llm_suggestion_apply_simulation_342l.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Validation commands:

```powershell
python -m py_compile datefac\benchmark\llm_suggestion_apply_simulation_342l.py datefac\benchmark\llm_suggestion_apply_simulation_342l_report.py tools\run_llm_suggestion_apply_simulation_342l.py tests\benchmark\test_llm_suggestion_apply_simulation_342l.py

python -m pytest tests\benchmark\test_llm_suggestion_apply_simulation_342l.py -q

python tools\run_llm_suggestion_apply_simulation_342l.py --llm-review-342k-dir D:\_datefac\output\llm_assisted_review_adjudication_342k --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --output-dir D:\_datefac\output\llm_suggestion_apply_simulation_342l
```

Commit SHA, if known:

- `pending current 342L commit`

---

## 342M LLM Suggestion Spot-Check Apply Or Real LLM Response Ingestion

Status: `completed_with_warnings`

Effective version:

- `effective_current_342M_reviewed_spot_check_ready_gate`

中文：
342M 已完成，并且已经基于真实的人审 spot-check workbook 重跑成功。它读取真实的 342L / 342K / 342J 产物，消费 reviewed spot-check evidence，验证 reviewer decisions，并生成 adoption gate 结果。342M 仍然是 no-write-back sidecar，不写回上游 workbook，不是 client-ready，也不是 production-ready。

English:
342M is completed and has been rerun successfully with real reviewed spot-check evidence. It consumes the real 342L / 342K / 342J artifacts, validates reviewer decisions from the reviewed spot-check workbook, and produces an adoption gate result. 342M remains a no-write-back sidecar, does not write back to upstream workbooks, and is neither client-ready nor production-ready.

Input dirs/files:

- `D:/_datefac/output/llm_suggestion_apply_simulation_342l`
- `D:/_datefac/output/llm_suggestion_apply_simulation_342l/llm_suggestion_apply_simulation_342l.xlsx`
- `D:/_datefac/output/llm_suggestion_apply_simulation_342l/llm_suggestion_apply_simulation_342l_summary.json`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k_prompt_pack.jsonl`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k_request_pack.jsonl`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j/table_first_reviewed_client_preview_pilot_342j_summary.json`
- optional reviewed evidence dir: `D:/_datefac/input/spot_check_reviewed_342m`
- optional real response dir: `D:/_datefac/input/llm_review_responses_342m`

Output dir:

- `D:/_datefac/output/llm_suggestion_spot_check_gate_342m`

Output workbook/report:

- `D:/_datefac/output/llm_suggestion_spot_check_gate_342m/llm_suggestion_spot_check_gate_342m.xlsx`
- `D:/_datefac/output/llm_suggestion_spot_check_gate_342m/llm_suggestion_spot_check_gate_342m_report.md`
- `D:/_datefac/output/llm_suggestion_spot_check_gate_342m/llm_suggestion_spot_check_review_template_342m.xlsx`
- `D:/_datefac/output/llm_suggestion_spot_check_gate_342m/real_llm_response_schema_342m.json`
- `D:/_datefac/output/llm_suggestion_spot_check_gate_342m/real_llm_response_ingestion_template_342m.jsonl`

Key metrics:

- `pending_review_count = 1075`
- `auto_confirm_candidate_count = 254`
- `spot_check_sample_count = 50`
- `reviewed_spot_check_count = 50`
- `spot_check_confirm_count = 17`
- `spot_check_correct_count = 33`
- `spot_check_reject_count = 0`
- `spot_check_validation_error_count = 0`
- `response_count = 0`
- `valid_llm_response_count = 0`
- `jsonl_parse_error_count = 0`
- `schema_validation_error_count = 0`
- `adoption_candidate_count = 254`
- `blocked_candidate_count = 0`
- `risk_adjusted_reduction_count = 254`
- `required_human_review_after_gate = 821`
- `conservative_reduction_rate_after_gate = 0.236279`
- `waiting_for_human_spot_check = false`
- `waiting_for_real_llm_responses = true`
- `ready_for_342n = true`
- `recommended_342n_scope = spot_check_adoption_simulation_or_real_llm_response_apply`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 342L summary / QA / workbook detected
- 342L `ready_for_342m = true` detected
- 342K prompt pack / request pack parsed successfully
- 342J boundary summary confirmed `client_ready=false` and `production_ready=false`
- spot-check reviewed workbook detected and validated
- reviewed spot-check counts rolled into the gate result
- real LLM response schema and ingestion template still preserved for optional future use
- no fake real LLM response generated
- no upstream workbook modified
- no protected dirty files staged
- no output artifacts staged

Decision:

- `LLM_SUGGESTION_SPOT_CHECK_APPLY_342M_READY`

Next recommended task:

- `342N Spot-Check Adoption Simulation Or Real LLM Response Apply`

Do not repeat:

- Do not claim 342M is a final apply stage.
- Do not treat dry-run suggestions as real LLM output.
- Do not treat auto-confirm candidates as final confirmations.
- Do not treat spot-check gate evidence as final human-review completion for the full queue.
- Do not write back to 342J / 342K / 342L or earlier workbooks.

Touched source files:

- `docs/codex_tasks/342M_llm_suggestion_spot_check_apply_or_real_llm_response_ingestion.md`
- `datefac/benchmark/llm_suggestion_spot_check_gate_342m.py`
- `datefac/benchmark/llm_suggestion_spot_check_gate_342m_report.py`
- `tools/run_llm_suggestion_spot_check_gate_342m.py`
- `tests/benchmark/test_llm_suggestion_spot_check_gate_342m.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Validation commands:

```powershell
python -m py_compile datefac\benchmark\llm_suggestion_spot_check_gate_342m.py datefac\benchmark\llm_suggestion_spot_check_gate_342m_report.py tools\run_llm_suggestion_spot_check_gate_342m.py tests\benchmark\test_llm_suggestion_spot_check_gate_342m.py

python -m pytest tests\benchmark\test_llm_suggestion_spot_check_gate_342m.py -q

python tools\run_llm_suggestion_spot_check_gate_342m.py --llm-suggestion-342l-dir D:\_datefac\output\llm_suggestion_apply_simulation_342l --llm-review-342k-dir D:\_datefac\output\llm_assisted_review_adjudication_342k --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --spot-check-reviewed-dir D:\_datefac\input\spot_check_reviewed_342m --llm-response-dir D:\_datefac\input\llm_review_responses_342m --output-dir D:\_datefac\output\llm_suggestion_spot_check_gate_342m
```

Commit SHA, if known:

- `pending current 342M commit`

---

## 342N Correction-Aware Spot-Check Adoption Simulation

Status: `completed`

Effective version:

- `effective_current_342N_correction_aware_adoption_simulation`

中文：
342N 已完成。它读取真实的 342M reviewed spot-check apply 结果和 342L/342K/342J 上游边界，在不写回任何上游 workbook 的前提下，对 254 条 adoption candidates 做 correction-aware adoption simulation。342N 不把 simulation rows 当成最终 confirmed，而是基于 50 条 spot-check 中 33 条 correction 的真实证据，把安全 direct pairs 和显式 correction patterns 分开处理，并把剩余 unresolved rows 保持在 human-required 状态。

English:
342N is completed. It consumes the real 342M reviewed spot-check apply result plus the 342L / 342K / 342J upstream boundaries, then runs a correction-aware adoption simulation over 254 adoption candidates without writing back to any upstream workbook. 342N does not treat simulation rows as final confirmations. Instead, it separates safe direct pairs from explicit correction-pattern rows using the real evidence that 33 out of 50 spot-check rows required correction, while keeping unresolved rows in a human-required state.

Input dirs/files:

- `D:/_datefac/output/llm_suggestion_spot_check_gate_342m`
- `D:/_datefac/output/llm_suggestion_spot_check_gate_342m/llm_suggestion_spot_check_gate_342m.xlsx`
- `D:/_datefac/output/llm_suggestion_spot_check_gate_342m/llm_suggestion_spot_check_gate_342m_summary.json`
- `D:/_datefac/output/llm_suggestion_apply_simulation_342l`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`

Output dir:

- `D:/_datefac/output/correction_aware_adoption_simulation_342n`

Output workbook/report:

- `D:/_datefac/output/correction_aware_adoption_simulation_342n/correction_aware_adoption_simulation_342n.xlsx`
- `D:/_datefac/output/correction_aware_adoption_simulation_342n/correction_aware_adoption_simulation_342n_report.md`

Key metrics:

- `pending_review_count = 1075`
- `input_adoption_candidate_count = 254`
- `spot_check_sample_count = 50`
- `spot_check_confirm_count = 17`
- `spot_check_correct_count = 33`
- `spot_check_reject_count = 0`
- `spot_check_correction_rate = 0.66`
- `direct_adopt_sim_count = 110`
- `correction_adopt_sim_count = 78`
- `still_human_required_count = 66`
- `adoption_sim_total_count = 188`
- `REVENUE_AMOUNT_NOT_YOY_count = 31`
- `REVENUE_YOY_PERCENT_count = 1`
- `NET_PROFIT_YOY_PERCENT_count = 1`
- `risk_adjusted_reduction_count = 188`
- `required_human_review_after_342n = 887`
- `conservative_reduction_rate_after_342n = 0.174884`
- `ready_for_342o = true`
- `recommended_342o_scope = post_adoption_sidecar_simulation_or_review_template_generation`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 342M input exists and `LLM_SUGGESTION_SPOT_CHECK_APPLY_342M_READY` is detected
- 342M `ready_for_342n = true` and `qa_fail_count = 0` detected
- spot-check count `= 50` and spot-check validation errors `= 0`
- adoption candidates loaded from 342M and source trace fields preserved from 342L
- direct adoption simulation only uses safe metric/unit pairs
- correction adoption simulation applies only explicit correction patterns
- still-human-required rows remain outside auto-apply
- no candidate becomes final confirmed
- no upstream workbook modified
- no production pipeline / parser / extraction / delivery modified
- no protected dirty files staged
- no output artifacts staged
- no optional input artifacts staged

Decision:

- `CORRECTION_AWARE_ADOPTION_SIMULATION_342N_READY`

Next recommended task:

- `342O Post-Adoption Sidecar Simulation Or Review Template Generation`

Do not repeat:

- Do not treat 342N simulation rows as final confirmations.
- Do not treat 342N as full human-review completion.
- Do not treat 342N as real LLM review completion.
- Do not claim `client_ready = true` or `production_ready = true`.
- Do not write back to 342J / 342K / 342L / 342M or earlier workbooks.

Touched source files:

- `docs/codex_tasks/342N_correction_aware_spot_check_adoption_simulation.md`
- `datefac/benchmark/correction_aware_adoption_simulation_342n.py`
- `datefac/benchmark/correction_aware_adoption_simulation_342n_report.py`
- `tools/run_correction_aware_adoption_simulation_342n.py`
- `tests/benchmark/test_correction_aware_adoption_simulation_342n.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Validation commands:

```powershell
python -m py_compile datefac\benchmark\correction_aware_adoption_simulation_342n.py datefac\benchmark\correction_aware_adoption_simulation_342n_report.py tools\run_correction_aware_adoption_simulation_342n.py tests\benchmark\test_correction_aware_adoption_simulation_342n.py

python -m pytest tests\benchmark\test_correction_aware_adoption_simulation_342n.py -q

python tools\run_correction_aware_adoption_simulation_342n.py --spot-check-gate-342m-dir D:\_datefac\output\llm_suggestion_spot_check_gate_342m --llm-suggestion-342l-dir D:\_datefac\output\llm_suggestion_apply_simulation_342l --llm-review-342k-dir D:\_datefac\output\llm_assisted_review_adjudication_342k --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --output-dir D:\_datefac\output\correction_aware_adoption_simulation_342n
```

Commit SHA, if known:

- `pending current 342N commit`

---

## 342O Post-Adoption Sidecar Simulation

Status: `completed`

Effective version:

- `effective_current_342O_post_adoption_sidecar_simulation`

English:
342O is completed. It consumes the real 342N correction-aware adoption simulation output plus 342M / 342J / 342I boundary summaries, then builds a no-write-back post-adoption sidecar simulation package. 342O does not turn simulated rows into final confirmations, does not write back to upstream workbooks, and does not change `client_ready=false` or `production_ready=false`.

Input dirs/files:

- `D:/_datefac/output/correction_aware_adoption_simulation_342n`
- `D:/_datefac/output/correction_aware_adoption_simulation_342n/correction_aware_adoption_simulation_342n.xlsx`
- `D:/_datefac/output/correction_aware_adoption_simulation_342n/correction_aware_adoption_simulation_342n_summary.json`
- `D:/_datefac/output/llm_suggestion_spot_check_gate_342m/llm_suggestion_spot_check_gate_342m_summary.json`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j/table_first_reviewed_client_preview_pilot_342j_summary.json`
- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i/table_first_post_human_review_sidecar_result_342i_summary.json`

Output dir:

- `D:/_datefac/output/post_adoption_sidecar_simulation_342o`

Output workbook/report:

- `D:/_datefac/output/post_adoption_sidecar_simulation_342o/post_adoption_sidecar_simulation_342o.xlsx`
- `D:/_datefac/output/post_adoption_sidecar_simulation_342o/post_adoption_sidecar_simulation_342o_report.md`

Key metrics:

- `pending_review_count = 1075`
- `input_adoption_candidate_count = 254`
- `direct_adopted_count = 110`
- `corrected_adopted_count = 78`
- `simulated_adopted_cell_count = 188`
- `still_human_required_count = 66`
- `remaining_review_count = 887`
- `reduction_rate_after_342o = 0.174884`
- `metric_covered_count = 17`
- `metric_year_pair_count = 50`
- `direct_metric_year_pair_count = 39`
- `correction_metric_year_pair_count = 15`
- `correction_pattern_count = 3`
- `REVENUE_AMOUNT_NOT_YOY_count = 58`
- `REVENUE_YOY_PERCENT_count = 10`
- `NET_PROFIT_YOY_PERCENT_count = 10`
- `ready_for_342p = true`
- `recommended_342p_scope = reviewed_plus_simulated_client_preview_pilot`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 342N summary / QA / workbook detected
- 342N `ready_for_342o = true` and `qa_fail_count = 0` detected
- required 342N workbook sheets detected
- direct + corrected simulated rows = 188
- simulated + still-human-required rows = 254
- remaining review count reduced from 1075 to 887
- no simulated row became final confirmed
- correction before/after trace preserved for all 78 correction-aware rows
- no upstream workbook modified
- no protected dirty files staged
- no output artifacts staged
- no optional reviewed / response input dirs staged

Decision:

- `POST_ADOPTION_SIDECAR_SIMULATION_342O_READY`

Next recommended task:

- `342P Reviewed Plus Simulated Client Preview Pilot`

Do not repeat:

- Do not treat 342O as final human-review completion.
- Do not treat 342O as real LLM review completion.
- Do not claim `client_ready = true` or `production_ready = true`.
- Do not write simulated adoption rows back to 342I / 342J / 342M / 342N or earlier workbooks.
- Do not use 342O as formal client delivery or investment advice.

Touched source files:

- `docs/codex_tasks/342O_post_adoption_sidecar_simulation.md`
- `datefac/benchmark/post_adoption_sidecar_simulation_342o.py`
- `datefac/benchmark/post_adoption_sidecar_simulation_342o_report.py`
- `tools/run_post_adoption_sidecar_simulation_342o.py`
- `tests/benchmark/test_post_adoption_sidecar_simulation_342o.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Validation commands:

```powershell
python -m py_compile datefac\benchmark\post_adoption_sidecar_simulation_342o.py datefac\benchmark\post_adoption_sidecar_simulation_342o_report.py tools\run_post_adoption_sidecar_simulation_342o.py tests\benchmark\test_post_adoption_sidecar_simulation_342o.py

python -m pytest tests\benchmark\test_post_adoption_sidecar_simulation_342o.py -q

python tools\run_post_adoption_sidecar_simulation_342o.py --adoption-simulation-342n-dir D:\_datefac\output\correction_aware_adoption_simulation_342n --spot-check-gate-342m-dir D:\_datefac\output\llm_suggestion_spot_check_gate_342m --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --post-human-sidecar-342i-dir D:\_datefac\output\table_first_post_human_review_sidecar_result_342i --output-dir D:\_datefac\output\post_adoption_sidecar_simulation_342o
```

Commit SHA, if known:

- `pending current 342O commit`

---

## 342P Reviewed Plus Simulated Client Preview Pilot

Status: `completed`

Effective version:

- `effective_current_342P_reviewed_plus_simulated_client_preview_pilot`

English:
342P is completed. It consumes the real 342J human-reviewed client preview pilot plus the real 342O post-adoption sidecar simulation, enriches the simulated rows with 342N metadata, resolves collisions with human-reviewed rows taking priority, and produces a bounded reviewed-plus-simulated preview workbook. 342P does not write back to upstream workbooks, does not turn simulated rows into final confirmations, and keeps `client_ready=false` and `production_ready=false`.

Input dirs/files:

- `D:/_datefac/output/post_adoption_sidecar_simulation_342o`
- `D:/_datefac/output/post_adoption_sidecar_simulation_342o/post_adoption_sidecar_simulation_342o.xlsx`
- `D:/_datefac/output/post_adoption_sidecar_simulation_342o/post_adoption_sidecar_simulation_342o_summary.json`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j/table_first_reviewed_client_preview_pilot_342j.xlsx`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j/table_first_reviewed_client_preview_pilot_342j_summary.json`
- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i`
- `D:/_datefac/output/correction_aware_adoption_simulation_342n`

Output dir:

- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p`

Output workbook/report:

- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p/reviewed_plus_simulated_client_preview_342p.xlsx`
- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p/reviewed_plus_simulated_client_preview_342p_report.md`

Key metrics:

- `human_reviewed_preview_count = 30`
- `simulated_preview_count = 100`
- `simulated_direct_preview_count = 61`
- `simulated_corrected_preview_count = 39`
- `combined_preview_row_count = 130`
- `still_human_required_count = 66`
- `remaining_review_count = 887`
- `metric_covered_count = 17`
- `metric_year_pair_count = 50`
- `human_metric_year_pair_count = 25`
- `simulated_metric_year_pair_count = 50`
- `duplicate_review_item_id_count = 0`
- `duplicate_metric_year_source_count = 99`
- `human_over_simulation_override_count = 9`
- `simulated_duplicate_dropped_count = 79`
- `collision_logged_count = 99`
- `ready_for_342q = true`
- `recommended_342q_scope = preview_audit_and_export_readiness_gate`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 342O summary / QA / workbook detected and `POST_ADOPTION_SIDECAR_SIMULATION_342O_READY` confirmed
- 342J summary / QA / workbook detected and `TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY` confirmed
- 342I / 342N supporting summaries and workbook metadata detected
- human-reviewed preview rows loaded
- simulated direct and simulated corrected rows loaded
- collision handling applied after merge
- human-reviewed rows kept higher priority than simulated rows
- simulated rows kept as `not_final_confirmation = true`
- still-human-required rows remained outside preview
- no upstream workbook modified
- no protected dirty files staged
- no output artifacts staged

Decision:

- `REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_READY`

Next recommended task:

- `342Q Preview Audit And Export Readiness Gate`

Do not repeat:

- Do not treat 342P as final human-review completion.
- Do not treat 342P as real LLM review completion.
- Do not claim `client_ready = true` or `production_ready = true`.
- Do not write reviewed or simulated preview rows back to 342I / 342J / 342N / 342O or earlier workbooks.
- Do not use 342P as formal client delivery or investment advice.

Touched source files:

- `docs/codex_tasks/342P_reviewed_plus_simulated_client_preview_pilot.md`
- `datefac/benchmark/reviewed_plus_simulated_client_preview_342p.py`
- `datefac/benchmark/reviewed_plus_simulated_client_preview_342p_report.py`
- `tools/run_reviewed_plus_simulated_client_preview_342p.py`
- `tests/benchmark/test_reviewed_plus_simulated_client_preview_342p.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Validation commands:

```powershell
python -m py_compile datefac\benchmark\reviewed_plus_simulated_client_preview_342p.py datefac\benchmark\reviewed_plus_simulated_client_preview_342p_report.py tools\run_reviewed_plus_simulated_client_preview_342p.py tests\benchmark\test_reviewed_plus_simulated_client_preview_342p.py

python -m pytest tests\benchmark\test_reviewed_plus_simulated_client_preview_342p.py -q

python tools\run_reviewed_plus_simulated_client_preview_342p.py --post-adoption-sidecar-342o-dir D:\_datefac\output\post_adoption_sidecar_simulation_342o --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --post-human-sidecar-342i-dir D:\_datefac\output\table_first_post_human_review_sidecar_result_342i --adoption-simulation-342n-dir D:\_datefac\output\correction_aware_adoption_simulation_342n --output-dir D:\_datefac\output\reviewed_plus_simulated_client_preview_342p
```

Commit SHA, if known:

- `pending current 342P commit`

---

## 342Q Preview Audit And Export Readiness Gate

Status: `completed`

Effective version:

- `effective_current_342Q_preview_audit_export_readiness_gate`

English:
342Q is completed. It reads the real 342P reviewed-plus-simulated preview package, audits trust-level separation, simulation-only boundary labels, collision handling, dropped-duplicate exclusion, and human-over-simulation override behavior, and then produces an audit-only readiness gate for a later 342R package. 342Q does not generate a formal client export, does not write back to upstream workbooks, does not mark any output as client-ready or production-ready, and must not be used as investment advice.

Input dirs/files:

- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p`
- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p/reviewed_plus_simulated_client_preview_342p.xlsx`
- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p/reviewed_plus_simulated_client_preview_342p_summary.json`
- `D:/_datefac/output/post_adoption_sidecar_simulation_342o`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`
- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i`
- `D:/_datefac/output/correction_aware_adoption_simulation_342n`

Output dir:

- `D:/_datefac/output/preview_audit_export_readiness_gate_342q`

Output workbook/report:

- `D:/_datefac/output/preview_audit_export_readiness_gate_342q/preview_audit_export_readiness_gate_342q.xlsx`
- `D:/_datefac/output/preview_audit_export_readiness_gate_342q/preview_audit_export_readiness_gate_342q_report.md`

Key metrics:

- `human_reviewed_preview_count = 30`
- `simulated_preview_count = 100`
- `simulated_direct_preview_count = 61`
- `simulated_corrected_preview_count = 39`
- `combined_preview_row_count = 130`
- `export_candidate_row_count = 130`
- `unknown_trust_level_count = 0`
- `trust_level_mismatch_count = 0`
- `simulated_final_confirmed_true_count = 0`
- `simulated_client_ready_true_count = 0`
- `simulated_production_ready_true_count = 0`
- `missing_display_warning_count = 0`
- `collision_logged_count = 99`
- `duplicate_metric_year_source_count = 99`
- `human_over_simulation_override_count = 9`
- `simulated_duplicate_dropped_count = 79`
- `unresolved_collision_count = 0`
- `severe_collision_count = 20`
- `formal_client_export_allowed = false`
- `export_candidate_scope_allowed = true`
- `export_risk_level = HIGH`
- `still_human_required_count = 66`
- `remaining_review_count = 887`
- `ready_for_342r = true`
- `recommended_342r_scope = audit_labeled_export_candidate_package`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 342P summary / QA / workbook detected and `REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_READY` confirmed
- 342P required sheets detected
- combined preview rows loaded and consistent with 342P summary counts
- trust levels remained valid with no source/trust mismatch
- no simulated row became final confirmed, client-ready, or production-ready
- dropped duplicate simulated rows stayed outside export candidate scope
- human-over-simulation override kept human priority
- no upstream workbook modified
- no protected dirty files staged
- no output artifacts staged

Decision:

- `PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_READY`

Next recommended task:

- `342R Audit-Labeled Export Candidate Package`

Do not repeat:

- Do not treat 342Q as formal client export.
- Do not treat 342Q as final human-review completion.
- Do not treat 342Q as real LLM review completion.
- Do not claim `client_ready = true` or `production_ready = true`.
- Do not write 342Q results back to 342P / 342O / 342J / 342I / 342N or earlier workbooks.
- Do not use 342Q as investment advice.

Touched source files:

- `docs/codex_tasks/342Q_preview_audit_export_readiness_gate.md`
- `datefac/benchmark/preview_audit_export_readiness_gate_342q.py`
- `datefac/benchmark/preview_audit_export_readiness_gate_342q_report.py`
- `tools/run_preview_audit_export_readiness_gate_342q.py`
- `tests/benchmark/test_preview_audit_export_readiness_gate_342q.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Validation commands:

```powershell
python -m py_compile datefac\benchmark\preview_audit_export_readiness_gate_342q.py datefac\benchmark\preview_audit_export_readiness_gate_342q_report.py tools\run_preview_audit_export_readiness_gate_342q.py tests\benchmark\test_preview_audit_export_readiness_gate_342q.py

python -m pytest tests\benchmark\test_preview_audit_export_readiness_gate_342q.py -q

python tools\run_preview_audit_export_readiness_gate_342q.py --reviewed-plus-preview-342p-dir D:\_datefac\output\reviewed_plus_simulated_client_preview_342p --post-adoption-sidecar-342o-dir D:\_datefac\output\post_adoption_sidecar_simulation_342o --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --post-human-sidecar-342i-dir D:\_datefac\output\table_first_post_human_review_sidecar_result_342i --adoption-simulation-342n-dir D:\_datefac\output\correction_aware_adoption_simulation_342n --output-dir D:\_datefac\output\preview_audit_export_readiness_gate_342q
```

Commit SHA, if known:

- `pending current 342Q commit`

---

## 342R Audit-Labeled Export Candidate Package

Status: `completed`

Effective version:

- `effective_current_342R_audit_labeled_export_candidate_package`

English:
342R is completed. It reads the real 342Q export-candidate scope, preserves trust-level separation and risk disclosures, and packages the approved 130 candidate rows into an audit-labeled export candidate package. 342R does not generate a formal client export, does not write back to upstream workbooks, does not turn simulated rows into final confirmations, and must keep `formal_client_export_allowed=false`, `client_ready=false`, and `production_ready=false`.

Input dirs/files:

- `D:/_datefac/output/preview_audit_export_readiness_gate_342q`
- `D:/_datefac/output/preview_audit_export_readiness_gate_342q/preview_audit_export_readiness_gate_342q.xlsx`
- `D:/_datefac/output/preview_audit_export_readiness_gate_342q/preview_audit_export_readiness_gate_342q_summary.json`
- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p`
- `D:/_datefac/output/post_adoption_sidecar_simulation_342o`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`

Output dir:

- `D:/_datefac/output/audit_labeled_export_candidate_package_342r`

Output workbook/report:

- `D:/_datefac/output/audit_labeled_export_candidate_package_342r/audit_labeled_export_candidate_package_342r.xlsx`
- `D:/_datefac/output/audit_labeled_export_candidate_package_342r/audit_labeled_export_candidate_package_342r_report.md`

Key metrics:

- `export_candidate_package_row_count = 130`
- `human_reviewed_candidate_count = 30`
- `simulated_candidate_count = 100`
- `simulated_direct_candidate_count = 61`
- `simulated_corrected_candidate_count = 39`
- `formal_client_export_allowed = false`
- `export_candidate_scope_allowed = true`
- `export_risk_level = HIGH`
- `collision_logged_count = 99`
- `duplicate_metric_year_source_count = 99`
- `severe_collision_count = 20`
- `human_over_simulation_override_count = 9`
- `simulated_duplicate_dropped_count = 79`
- `still_human_required_count = 66`
- `remaining_review_count = 887`
- `disclaimer_required_count = 100`
- `later_audit_required_count = 100`
- `package_row_fail_count = 0`
- `ready_for_342s = true`
- `recommended_342s_scope = package_audit_snapshot_or_demo_handoff`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 342Q summary / QA / workbook detected and `PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_READY` confirmed
- 342Q required sheets detected
- 342P context workbook detected for source-trace enrichment
- package row count matched `342Q export_candidate_row_count`
- trust-level separation preserved with no invalid trust labels
- no package row became final confirmed, client-ready, or production-ready
- all simulated package rows retained later-audit boundary
- required disclaimers preserved
- no upstream workbook modified
- no protected dirty files staged
- no output artifacts staged
- no sheet name exceeds 31 chars

Decision:

- `AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_READY`

Next recommended task:

- `342S Package Audit Snapshot Or Demo Handoff`

Do not repeat:

- Do not treat 342R as formal client export.
- Do not treat 342R as final human-review completion.
- Do not treat 342R as real LLM review completion.
- Do not claim `formal_client_export_allowed = true`.
- Do not claim `client_ready = true` or `production_ready = true`.
- Do not write 342R package rows back to 342Q / 342P / 342O / 342J or earlier workbooks.
- Do not use 342R as investment advice.

Touched source files:

- `docs/codex_tasks/342R_audit_labeled_export_candidate_package.md`
- `datefac/benchmark/audit_labeled_export_candidate_package_342r.py`
- `datefac/benchmark/audit_labeled_export_candidate_package_342r_report.py`
- `tools/run_audit_labeled_export_candidate_package_342r.py`
- `tests/benchmark/test_audit_labeled_export_candidate_package_342r.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Validation commands:

```powershell
python -m py_compile datefac\benchmark\audit_labeled_export_candidate_package_342r.py datefac\benchmark\audit_labeled_export_candidate_package_342r_report.py tools\run_audit_labeled_export_candidate_package_342r.py tests\benchmark\test_audit_labeled_export_candidate_package_342r.py

python -m pytest tests\benchmark\test_audit_labeled_export_candidate_package_342r.py -q

python tools\run_audit_labeled_export_candidate_package_342r.py --preview-audit-342q-dir D:\_datefac\output\preview_audit_export_readiness_gate_342q --reviewed-plus-preview-342p-dir D:\_datefac\output\reviewed_plus_simulated_client_preview_342p --post-adoption-sidecar-342o-dir D:\_datefac\output\post_adoption_sidecar_simulation_342o --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --output-dir D:\_datefac\output\audit_labeled_export_candidate_package_342r
```

Commit SHA, if known:

- `pending current 342R commit`

---

## 342S Package Audit Snapshot Or Demo Handoff

Status: `completed`

Effective version:

- `effective_current_342S_package_audit_snapshot_demo_handoff`

English:
342S is completed. It reads the real 342R audit-labeled export candidate package and generates a bounded package audit snapshot / demo handoff bundle. 342S does not create a formal client export, does not write back to upstream workbooks, does not convert simulated rows into final confirmations, and must keep `formal_client_export_allowed=false`, `client_ready=false`, and `production_ready=false`.

Input dirs/files:

- `D:/_datefac/output/audit_labeled_export_candidate_package_342r`
- `D:/_datefac/output/audit_labeled_export_candidate_package_342r/audit_labeled_export_candidate_package_342r.xlsx`
- `D:/_datefac/output/audit_labeled_export_candidate_package_342r/audit_labeled_export_candidate_package_342r_summary.json`
- `D:/_datefac/output/audit_labeled_export_candidate_package_342r/audit_labeled_export_candidate_package_342r_qa.json`
- `D:/_datefac/output/preview_audit_export_readiness_gate_342q`
- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p`
- `D:/_datefac/output/post_adoption_sidecar_simulation_342o`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`

Output dir:

- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s`

Output workbook/report:

- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s/package_audit_snapshot_demo_handoff_342s.xlsx`
- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s/package_audit_snapshot_demo_handoff_342s_report.md`
- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s/package_audit_snapshot_demo_handoff_342s_demo_readme.md`
- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s/package_audit_snapshot_demo_handoff_342s_handoff_checklist.md`
- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s/package_audit_snapshot_demo_handoff_342s_next_step_plan.md`

Key metrics:

- `latest_completed_milestone = 342R`
- `current_milestone = 342S`
- `current_mainline = MinerU-first / table-first`
- `export_candidate_package_row_count = 130`
- `human_reviewed_candidate_count = 30`
- `simulated_candidate_count = 100`
- `simulated_direct_candidate_count = 61`
- `simulated_corrected_candidate_count = 39`
- `disclaimer_required_count = 100`
- `later_audit_required_count = 100`
- `export_risk_level = HIGH`
- `collision_logged_count = 99`
- `duplicate_metric_year_source_count = 99`
- `severe_collision_count = 20`
- `unresolved_collision_count = 0`
- `human_over_simulation_override_count = 9`
- `simulated_duplicate_dropped_count = 79`
- `still_human_required_count = 66`
- `remaining_review_count = 887`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `demo_handoff_ready = true`
- `ready_for_343a = true`
- `recommended_343a_scope = review_queue_schema_and_human_review_ui_pilot`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 342R summary / QA / workbook / candidates CSV / metadata detected
- 342R decision `AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_READY` confirmed
- 342R required sheets detected
- supporting 342Q / 342P / 342O / 342J ready summaries detected
- 342R workbook counts matched summary counts
- trust-level split remained consistent with 30 HUMAN_REVIEWED + 100 SIMULATED rows
- risk boundary preserved with `formal_client_export_allowed=false`, `client_ready=false`, `production_ready=false`
- demo guide generated
- artifact index generated
- handoff checklist generated
- no upstream workbook modified
- no protected dirty files staged
- no output artifacts staged
- no sheet name exceeds 31 chars

Decision:

- `PACKAGE_AUDIT_SNAPSHOT_DEMO_HANDOFF_342S_READY`

Next recommended task:

- `343A Review Queue Schema And Human Review UI Pilot`

Do not repeat:

- Do not treat 342S as formal client export.
- Do not treat 342S as final human-review completion.
- Do not treat 342S as real LLM review completion.
- Do not claim `formal_client_export_allowed = true`.
- Do not claim `client_ready = true` or `production_ready = true`.
- Do not write 342S outputs back to 342R / 342Q / 342P / 342O / 342J or earlier workbooks.
- Do not use 342S as investment advice.

Touched source files:

- `docs/codex_tasks/342S_package_audit_snapshot_demo_handoff.md`
- `datefac/benchmark/package_audit_snapshot_demo_handoff_342s.py`
- `datefac/benchmark/package_audit_snapshot_demo_handoff_342s_report.py`
- `tools/run_package_audit_snapshot_demo_handoff_342s.py`
- `tests/benchmark/test_package_audit_snapshot_demo_handoff_342s.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Validation commands:

```powershell
python -m py_compile datefac\benchmark\package_audit_snapshot_demo_handoff_342s.py datefac\benchmark\package_audit_snapshot_demo_handoff_342s_report.py tools\run_package_audit_snapshot_demo_handoff_342s.py tests\benchmark\test_package_audit_snapshot_demo_handoff_342s.py

python -m pytest tests\benchmark\test_package_audit_snapshot_demo_handoff_342s.py -q

python tools\run_package_audit_snapshot_demo_handoff_342s.py --audit-labeled-package-342r-dir D:\_datefac\output\audit_labeled_export_candidate_package_342r --preview-audit-342q-dir D:\_datefac\output\preview_audit_export_readiness_gate_342q --reviewed-plus-preview-342p-dir D:\_datefac\output\reviewed_plus_simulated_client_preview_342p --post-adoption-sidecar-342o-dir D:\_datefac\output\post_adoption_sidecar_simulation_342o --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --output-dir D:\_datefac\output\package_audit_snapshot_demo_handoff_342s
```

Commit SHA, if known:

- `pending current 342S commit`

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
- 342G completed table-first extraction review package: review_template_row_count=1155, review_queue_count=1005, trusted_audit_sample_count=150, qa_fail_count=0.
- 342H completed reviewed apply simulation: reviewed_row_count=80, pending_review_count=1075, confirmed_cell_count=31, corrected_cell_count=10, rejected_cell_count=39, qa_fail_count=0.
- 342I completed post-human-review sidecar result: post_human_confirmed_count=41, pending_review_count=1075, qa_fail_count=0.
- 342J completed reviewed client preview pilot: reviewed_preview_row_count=41, confirmed_preview_row_count=31, corrected_preview_row_count=10, pending_review_count=1075, qa_fail_count=0.
- 342K completed LLM-assisted adjudication pilot: llm_candidate_pool_count=1075, prompt_package_count=358, request_pack_count=358, human_required_count=717, auto_confirm_candidate_count=254, ready_for_342l=true, qa_fail_count=0.
- 342L completed LLM suggestion apply simulation: auto_confirm_candidate_count=254, spot_check_sample_count=50, human_required_count=717, conflict_count=763, risk_adjusted_reduction_count=204, ready_for_342m=true, qa_fail_count=0.
- 342M completed reviewed spot-check gate: reviewed_spot_check_count=50, spot_check_confirm_count=17, spot_check_correct_count=33, adoption_candidate_count=254, required_human_review_after_gate=821, ready_for_342n=true, qa_fail_count=0.
- 342N completed correction-aware adoption simulation: input_adoption_candidate_count=254, direct_adopt_sim_count=110, correction_adopt_sim_count=78, still_human_required_count=66, adoption_sim_total_count=188, required_human_review_after_342n=887, ready_for_342o=true, qa_fail_count=0.
- 342O completed post-adoption sidecar simulation: input_adoption_candidate_count=254, direct_adopted_count=110, corrected_adopted_count=78, simulated_adopted_cell_count=188, still_human_required_count=66, remaining_review_count=887, ready_for_342p=true, qa_fail_count=0.
- 342P completed reviewed plus simulated client preview pilot: human_reviewed_preview_count=30, simulated_preview_count=100, combined_preview_row_count=130, duplicate_metric_year_source_count=99, human_over_simulation_override_count=9, simulated_duplicate_dropped_count=79, ready_for_342q=true, qa_fail_count=0.
- 342Q completed preview audit and export-readiness gate: export_candidate_row_count=130, unknown_trust_level_count=0, trust_level_mismatch_count=0, collision_logged_count=99, formal_client_export_allowed=false, export_candidate_scope_allowed=true, ready_for_342r=true, qa_fail_count=0.

Do not repeat 342C6. Do not redo 342D. Do not use the old 342E 435 text candidate route. Do not rerun 342F. Do not rerun MinerU. Do not call VLM/LLM. Do not mix BASIC_DATA into core financial extraction.

Current next task:
Proceed to 342R audit-labeled export candidate package.

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
- 342H second reviewed batch apply simulation is the effective upstream human-review state.
- 342I post-human-review sidecar result has been rerun with 80 reviewed rows.
- 342J reviewed client preview pilot is completed.
- 342K LLM-assisted review adjudication pilot is completed.
- 342L suggestion-apply simulation is completed.
- 342M spot-check / real-response gate has been rerun with reviewed spot-check evidence and is ready for 342N.
- 342N correction-aware adoption simulation is completed and ready for 342O.

Unsafe statements:

- Do not say production-ready.
- Do not say client-ready.
- Do not say MinerU universally beats all parsers.
- Do not say all financial tables are fully extracted.
- Do not say old 435 text candidates are the current main input.
- Do not call generated outputs official financial advice or investment advice.
---

Task ID:

- `343A Review Queue Schema And Human Review UI Pilot`

Status:

- `completed`

Effective version:

- `review_queue_schema_343a`
- Current mainline remains `MinerU-first / table-first`
- 343A is a schema/pilot package stage, not a production UI, not a formal client export, and not an upstream rerun

Input dirs/files:

- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s`
- `D:/_datefac/output/audit_labeled_export_candidate_package_342r`
- `D:/_datefac/output/preview_audit_export_readiness_gate_342q`
- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p`
- Primary row source: `audit_labeled_export_candidate_package_342r.xlsx` -> `03_EXPORT_CANDIDATES`

Output dir:

- `D:/_datefac/output/review_queue_schema_343a`

Output workbook/report:

- `D:/_datefac/output/review_queue_schema_343a/review_queue_schema_343a.xlsx`
- `D:/_datefac/output/review_queue_schema_343a/review_queue_schema_343a_report.md`
- `D:/_datefac/output/review_queue_schema_343a/review_queue_schema_343a_schema.json`
- `D:/_datefac/output/review_queue_schema_343a/review_queue_schema_343a_json_schema.json`
- `D:/_datefac/output/review_queue_schema_343a/review_queue_schema_343a_excel_template_spec.json`
- `D:/_datefac/output/review_queue_schema_343a/review_queue_schema_343a_argilla_mapping.json`
- `D:/_datefac/output/review_queue_schema_343a/review_queue_schema_343a_ui_contract.md`
- `D:/_datefac/output/review_queue_schema_343a/review_queue_schema_343a_sample_items.jsonl`

Key metrics:

- `review_queue_schema_version = 343A.review_queue.v1`
- `field_count = 58`
- `required_field_count = 29`
- `status_count = 13`
- `reason_code_count = 12`
- `priority_level_count = 5`
- `sample_queue_item_count = 51`
- `human_reviewed_sample_count = 10`
- `simulated_sample_count = 40`
- `summary_derived_sample_count = 1`
- `argilla_mapping_generated = true`
- `excel_template_spec_generated = true`
- `ui_contract_generated = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

QA result:

- 342S ready summary / qa / report / demo README were detected
- 342R workbook / summary / qa were detected
- 342Q and 342P ready summaries were detected
- queue fields, lifecycle, reason codes, priorities, trust mapping, sample queue, Excel spec, Argilla mapping, and UI contract were generated
- simulated rows were kept non-final and all readiness flags remained false
- no upstream workbook was modified
- no protected dirty files were staged
- no output / temp / forbidden input paths were staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_READY`

Next recommended task:

- `343B Argilla Human Review UI Pilot`
- Rationale: 343A now provides a stable queue contract, deterministic pilot sample, Excel round-trip spec, and Argilla mapping, so the next safe step is to validate a pluggable human review UI against this schema rather than expand production logic.

Do not repeat:

- Do not treat 343A as a production UI implementation.
- Do not treat Argilla as the core system contract.
- Do not write back 343A queue results to 342R / 342S / 342Q / 342P or earlier workbooks.
- Do not claim `formal_client_export_allowed = true`.
- Do not claim `client_ready = true` or `production_ready = true`.
- Do not treat simulated preview rows as final confirmed export rows.
- Do not convert 343A into investment advice or formal client delivery.

Touched source files:

- `docs/codex_tasks/343A_review_queue_schema_and_human_review_ui_pilot.md`
- `datefac/review_queue/__init__.py`
- `datefac/review_queue/schema_343a.py`
- `datefac/benchmark/review_queue_schema_343a.py`
- `datefac/benchmark/review_queue_schema_343a_report.py`
- `tools/run_review_queue_schema_343a.py`
- `tests/benchmark/test_review_queue_schema_343a.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_椤圭洰杩涚▼.md`

Validation commands:

```powershell
python -m py_compile datefac\review_queue\schema_343a.py datefac\benchmark\review_queue_schema_343a.py datefac\benchmark\review_queue_schema_343a_report.py tools\run_review_queue_schema_343a.py tests\benchmark\test_review_queue_schema_343a.py

python -m pytest tests\benchmark\test_review_queue_schema_343a.py -q

python tools\run_review_queue_schema_343a.py --snapshot-342s-dir D:\_datefac\output\package_audit_snapshot_demo_handoff_342s --audit-labeled-package-342r-dir D:\_datefac\output\audit_labeled_export_candidate_package_342r --preview-audit-342q-dir D:\_datefac\output\preview_audit_export_readiness_gate_342q --reviewed-plus-preview-342p-dir D:\_datefac\output\reviewed_plus_simulated_client_preview_342p --output-dir D:\_datefac\output\review_queue_schema_343a
```

Commit SHA, if known:

- `pending current 343A commit`

---

Task ID:

- `343B Excel Round-trip Review Queue Pilot`

Status:

- `completed`

Effective version:

- `review_queue_excel_round_trip_343b`
- Current mainline remains `MinerU-first / table-first`
- 343B validates the 343A Review Queue contract through deterministic Excel round-trip only

Input dirs/files:

- `D:/_datefac/output/review_queue_schema_343a`
- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s`
- `D:/_datefac/output/audit_labeled_export_candidate_package_342r`
- Primary 343A inputs: summary / qa / schema / json schema / Excel template spec / sample items JSONL / workbook

Output dir:

- `D:/_datefac/output/review_queue_excel_round_trip_343b`

Output workbook/report:

- `D:/_datefac/output/review_queue_excel_round_trip_343b/review_queue_excel_round_trip_343b.xlsx`
- `D:/_datefac/output/review_queue_excel_round_trip_343b/review_queue_excel_round_trip_343b_report.md`
- `D:/_datefac/output/review_queue_excel_round_trip_343b/review_queue_excel_round_trip_343b_review_template.xlsx`
- `D:/_datefac/output/review_queue_excel_round_trip_343b/review_queue_excel_round_trip_343b_import_simulation.xlsx`
- `D:/_datefac/output/review_queue_excel_round_trip_343b/review_queue_excel_round_trip_343b_reviewed_result.jsonl`
- `D:/_datefac/output/review_queue_excel_round_trip_343b/review_queue_excel_round_trip_343b_validation_errors.json`

Key metrics:

- `source_milestone = 343A`
- `review_queue_schema_version = 343A.review_queue.v1`
- `template_row_count = 51`
- `import_simulation_row_count = 51`
- `reviewed_result_row_count = 51`
- `confirmed_count = 10`
- `corrected_count = 10`
- `rejected_count = 10`
- `needs_source_check_count = 11`
- `skipped_count = 10`
- `validation_error_count = 0`
- `validation_warning_count = 1`
- `excel_template_generated = true`
- `import_simulation_generated = true`
- `reviewed_result_jsonl_generated = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

QA result:

- 343A input exists and is ready
- schema JSON / JSON schema / Excel template spec / sample JSONL detected
- review template generated
- import simulation generated
- reviewed result JSONL generated
- happy-path validation has zero errors
- intentional error cases were captured separately without failing the happy path
- no Argilla call was made
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `REVIEW_QUEUE_EXCEL_ROUND_TRIP_343B_READY`

Next recommended task:

- `343C Argilla Human Review UI Pilot`
- Rationale: 343B has validated that the Review Queue contract can survive deterministic Excel export/import/validation, so Argilla can now be added as a pluggable UI layer instead of becoming the core system contract.

Do not repeat:

- Do not treat 343B import simulation as real human review evidence.
- Do not treat 343B as formal client export.
- Do not implement production apply logic in 343B.
- Do not call or import Argilla inside 343B.
- Do not write back 343B reviewed results to 343A / 342R / 342S or earlier artifacts.
- Do not claim `client_ready = true` or `production_ready = true`.
- Do not convert 343B outputs into investment advice or formal client delivery.

Touched source files:

- `docs/codex_tasks/343B_excel_round_trip_review_queue_pilot.md`
- `datefac/review_queue/excel_round_trip_343b.py`
- `datefac/benchmark/review_queue_excel_round_trip_343b.py`
- `datefac/benchmark/review_queue_excel_round_trip_343b_report.py`
- `tools/run_review_queue_excel_round_trip_343b.py`
- `tests/benchmark/test_review_queue_excel_round_trip_343b.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_椤圭洰杩涚▼.md`

Validation commands:

```powershell
python -m py_compile datefac\review_queue\excel_round_trip_343b.py datefac\benchmark\review_queue_excel_round_trip_343b.py datefac\benchmark\review_queue_excel_round_trip_343b_report.py tools\run_review_queue_excel_round_trip_343b.py tests\benchmark\test_review_queue_excel_round_trip_343b.py

python -m pytest tests\benchmark\test_review_queue_excel_round_trip_343b.py -q

python tools\run_review_queue_excel_round_trip_343b.py --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --snapshot-342s-dir D:\_datefac\output\package_audit_snapshot_demo_handoff_342s --audit-labeled-package-342r-dir D:\_datefac\output\audit_labeled_export_candidate_package_342r --output-dir D:\_datefac\output\review_queue_excel_round_trip_343b
```

Commit SHA, if known:

- `pending current 343B commit`

---

Task ID:

- `343C Real Excel Review Queue Pilot`

Status:

- `completed`
- 343C completed as waiting-for-human-review template generation

Input dirs/files:

- `D:/_datefac/output/review_queue_excel_round_trip_343b`
- `D:/_datefac/output/review_queue_schema_343a`
- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s`

Output dir:

- `D:/_datefac/output/review_queue_real_excel_review_343c`

Output workbook/report/template:

- `D:/_datefac/output/review_queue_real_excel_review_343c/review_queue_real_excel_review_343c.xlsx`
- `D:/_datefac/output/review_queue_real_excel_review_343c/review_queue_real_excel_review_343c_review_template.xlsx`
- `D:/_datefac/output/review_queue_real_excel_review_343c/review_queue_real_excel_review_343c_reviewer_instructions.md`
- `D:/_datefac/output/review_queue_real_excel_review_343c/review_queue_real_excel_review_343c_fill_guide.md`
- `D:/_datefac/output/review_queue_real_excel_review_343c/review_queue_real_excel_review_343c_expected_import_contract.json`
- `D:/_datefac/output/review_queue_real_excel_review_343c/review_queue_real_excel_review_343c_report.md`

Key metrics:

- `source_milestone = 343B`
- `review_queue_schema_version = 343A.review_queue.v1`
- `real_review_template_row_count = up to 30 deterministic pilot rows`
- `allowed_decision_count = 5`
- `real_review_template_generated = true`
- `reviewer_instructions_generated = true`
- `fill_guide_generated = true`
- `expected_import_contract_generated = true`
- `waiting_for_human_review = true`
- `reviewed_result_ingested = false`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343d = false`

QA result:

- 343B input exists and is ready
- 343A schema and sample inputs exist
- real review template generated
- reviewer instructions generated
- fill guide generated
- expected import contract generated
- editable reviewer columns exist
- allowed decision list is present
- no simulated/imported reviewer decision is treated as real human evidence
- no Argilla call made
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `REVIEW_QUEUE_REAL_EXCEL_REVIEW_343C_WAITING_FOR_HUMAN_REVIEW`

Next required user action:

- Open the dedicated `review_queue_real_excel_review_343c_review_template.xlsx`
- Fill the reviewer columns with real human review decisions
- Save a human-filled workbook copy for later ingestion

Next recommended task after user fills workbook:

- `343D real_excel_review_result_ingestion_after_user_fills_workbook`

Do not repeat:

- Do not treat 343C as completed human review.
- Do not ingest reviewed results inside 343C.
- Do not call Argilla or implement a production UI in 343C.
- Do not write back to upstream workbooks.
- Do not claim `client_ready = true` or `production_ready = true`.

---

Task ID:

- `343D Real Excel Review Result Ingestion`

Status:

- `completed`
- Current ingestion is explicitly AI-assisted review, not strict pure human review

Input dirs/files:

- `D:/_datefac/output/review_queue_real_excel_review_343c`
- `D:/_datefac/output/review_queue_schema_343a`
- `D:/_datefac/input/review_queue_real_excel_review_343c_filled/review_queue_real_excel_review_343c_review_template_filled.xlsx`

Output dir:

- `D:/_datefac/output/review_queue_excel_ingestion_343d`

Output workbook/report/result:

- `D:/_datefac/output/review_queue_excel_ingestion_343d/review_queue_excel_ingestion_343d.xlsx`
- `D:/_datefac/output/review_queue_excel_ingestion_343d/review_queue_excel_ingestion_343d_reviewed_result.jsonl`
- `D:/_datefac/output/review_queue_excel_ingestion_343d/review_queue_excel_ingestion_343d_decision_summary.json`
- `D:/_datefac/output/review_queue_excel_ingestion_343d/review_queue_excel_ingestion_343d_ai_assisted_review_disclosure.md`
- `D:/_datefac/output/review_queue_excel_ingestion_343d/review_queue_excel_ingestion_343d_report.md`

Key metrics:

- `review_source_type = AI_ASSISTED_REVIEW`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_human_spot_check = true`
- `reviewed_result_ingested = true` only when validation errors are zero
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

QA result:

- 343C input exists and is waiting for review
- filled workbook exists and is readable
- expected sheet resolved
- identity columns and reviewer columns validated
- allowed decisions enforced
- AI-assisted disclosure written to every ingested row
- no Argilla call made
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `REVIEW_QUEUE_EXCEL_INGESTION_343D_READY`

AI-assisted disclosure:

- `review_source_type = AI_ASSISTED_REVIEW`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_human_spot_check = true`

Next recommended task:

- `343E AI-assisted Review Result Apply Simulation And Audit Gate`

---

Task ID:

- `343E AI-assisted Review Result Apply Simulation And Audit Gate`

Status:

- `completed`
- simulation-only apply gate for AI-assisted review results

Input dirs/files:

- `D:/_datefac/output/review_queue_excel_ingestion_343d`
- `D:/_datefac/output/review_queue_schema_343a`

Output dir:

- `D:/_datefac/output/review_queue_apply_simulation_343e`

Output workbook/report/sidecars:

- `D:/_datefac/output/review_queue_apply_simulation_343e/review_queue_apply_simulation_343e.xlsx`
- `D:/_datefac/output/review_queue_apply_simulation_343e/review_queue_apply_simulation_343e_apply_plan.jsonl`
- `D:/_datefac/output/review_queue_apply_simulation_343e/review_queue_apply_simulation_343e_simulated_sidecar.jsonl`
- `D:/_datefac/output/review_queue_apply_simulation_343e/review_queue_apply_simulation_343e_audit_gate.json`
- `D:/_datefac/output/review_queue_apply_simulation_343e/review_queue_apply_simulation_343e_risk_register.json`
- `D:/_datefac/output/review_queue_apply_simulation_343e/review_queue_apply_simulation_343e_ai_assisted_boundary.md`

Key metrics:

- `apply_mode = SIMULATION_ONLY`
- `review_source_type = AI_ASSISTED_REVIEW`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_human_spot_check = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

QA result:

- 343D input exists and is ready
- reviewed-result JSONL exists and is readable
- AI-assisted disclosure preserved on all rows
- no row claims strict pure human review
- apply plan generated
- simulated sidecar generated for simulation-eligible rows only
- hold rows classified
- audit gate generated
- risk register generated
- no real production apply performed
- no Argilla call made
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `AI_ASSISTED_REVIEW_APPLY_SIMULATION_343E_READY`

AI-assisted boundary:

- `review_source_type = AI_ASSISTED_REVIEW`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_human_spot_check = true`
- `apply_mode = SIMULATION_ONLY`

Next recommended task:

- `343F AI-assisted Review Spot-check Package`

---

Task ID:

- `343F AI-assisted Review Spot-check Package`

Status:

- `completed`
- waiting-for-spot-check package generation only

Input dirs/files:

- `D:/_datefac/output/review_queue_apply_simulation_343e`
- `D:/_datefac/output/review_queue_excel_ingestion_343d`
- `D:/_datefac/output/review_queue_schema_343a`

Output dir:

- `D:/_datefac/output/review_queue_spot_check_package_343f`

Output workbook/report/template:

- `D:/_datefac/output/review_queue_spot_check_package_343f/review_queue_spot_check_package_343f.xlsx`
- `D:/_datefac/output/review_queue_spot_check_package_343f/review_queue_spot_check_package_343f_review_template.xlsx`
- `D:/_datefac/output/review_queue_spot_check_package_343f/review_queue_spot_check_package_343f_spot_check_items.jsonl`
- `D:/_datefac/output/review_queue_spot_check_package_343f/review_queue_spot_check_package_343f_source_check_todo.jsonl`
- `D:/_datefac/output/review_queue_spot_check_package_343f/review_queue_spot_check_package_343f_priority_plan.json`
- `D:/_datefac/output/review_queue_spot_check_package_343f/review_queue_spot_check_package_343f_expected_import_contract.json`

Key metrics:

- `review_source_type = AI_ASSISTED_REVIEW`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_human_spot_check = true`
- `apply_mode = SIMULATION_ONLY`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `waiting_for_spot_check = true`
- `spot_check_result_ingested = false`

QA result:

- 343E input exists and is ready
- apply plan / simulated sidecar readable
- audit gate passed for spot-check package
- AI-assisted boundary preserved
- no row claims strict pure human review
- spot-check package workbook generated
- review template generated
- source-check todo generated
- expected import contract generated
- editable spot-check columns exist
- no Argilla call made
- no real production apply performed
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `AI_ASSISTED_REVIEW_SPOT_CHECK_PACKAGE_343F_WAITING_FOR_SPOT_CHECK`

Next required user action:

- Open the dedicated 343F spot-check workbook
- Fill the `spot_check_*` columns for all 30 rows
- Save a filled copy for later 343G ingestion

Next recommended task after user fills workbook:

- `343G ai_assisted_review_spot_check_result_ingestion_after_user_fills_workbook`

---

Task ID:

- `343G AI-assisted Review Spot-check Result Ingestion`

Status:

- `completed`
- Current ingestion is explicitly AI-assisted spot-check, not strict pure human spot-check

Input dirs/files:

- `D:/_datefac/output/review_queue_spot_check_package_343f`
- `D:/_datefac/output/review_queue_apply_simulation_343e`
- `D:/_datefac/output/review_queue_schema_343a`
- `D:/_datefac/input/review_queue_spot_check_package_343f_filled/review_queue_spot_check_package_343f_review_template_filled.xlsx`

Output dir:

- `D:/_datefac/output/review_queue_spot_check_ingestion_343g`

Output workbook/report/result:

- `D:/_datefac/output/review_queue_spot_check_ingestion_343g/review_queue_spot_check_ingestion_343g.xlsx`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g/review_queue_spot_check_ingestion_343g_result.jsonl`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g/review_queue_spot_check_ingestion_343g_decision_summary.json`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g/review_queue_spot_check_ingestion_343g_ai_assisted_spot_check_disclosure.md`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g/review_queue_spot_check_ingestion_343g_report.md`

Key metrics:

- `review_source_type = AI_ASSISTED_REVIEW`
- `spot_check_source_type = AI_ASSISTED_SPOT_CHECK`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `apply_mode = SIMULATION_ONLY`
- `spot_check_result_ingested = true` only when validation errors are zero
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

QA result:

- 343F input exists and is waiting for spot-check
- filled workbook exists and is readable
- expected sheet resolved
- identity columns and editable spot-check columns validated
- allowed spot-check decisions enforced
- correction rows validated
- source-check rows require notes
- AI-assisted spot-check disclosure written to every ingested row
- strict human review is not claimed
- no Argilla call made
- no real production apply performed
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `AI_ASSISTED_SPOT_CHECK_INGESTION_343G_READY`

AI-assisted spot-check disclosure:

- `review_source_type = AI_ASSISTED_REVIEW`
- `spot_check_source_type = AI_ASSISTED_SPOT_CHECK`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `apply_mode = SIMULATION_ONLY`

Next recommended task:

- `343H AI-assisted Spot-check Audit Summary And Strict Human Gap Report`

Do not repeat:

- Do not treat 343G as strict pure human spot-check completion.
- Do not perform real write-back or production apply in 343G.
- Do not generate formal client export from 343G.
- Do not claim `client_ready = true` or `production_ready = true`.
- Do not write back 343G results to 343F / 343E / 343A or earlier artifacts.

Touched source files:

- `datefac/review_queue/ingest_spot_check_343g.py`
- `datefac/benchmark/review_queue_spot_check_ingestion_343g.py`
- `datefac/benchmark/review_queue_spot_check_ingestion_343g_report.py`
- `tools/run_review_queue_spot_check_ingestion_343g.py`
- `tests/benchmark/test_review_queue_spot_check_ingestion_343g.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Validation commands:

```powershell
python -m py_compile datefac\review_queue\ingest_spot_check_343g.py datefac\benchmark\review_queue_spot_check_ingestion_343g.py datefac\benchmark\review_queue_spot_check_ingestion_343g_report.py tools\run_review_queue_spot_check_ingestion_343g.py tests\benchmark\test_review_queue_spot_check_ingestion_343g.py

python -m pytest tests\benchmark\test_review_queue_spot_check_ingestion_343g.py -q

python tools\run_review_queue_spot_check_ingestion_343g.py --spot-check-package-343f-dir D:\_datefac\output\review_queue_spot_check_package_343f --apply-simulation-343e-dir D:\_datefac\output\review_queue_apply_simulation_343e --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --filled-workbook D:\_datefac\input\review_queue_spot_check_package_343f_filled\review_queue_spot_check_package_343f_review_template_filled.xlsx --output-dir D:\_datefac\output\review_queue_spot_check_ingestion_343g
```

Commit SHA, if known:

- `pending current 343G commit`

---

Task ID:

- `343H AI-assisted Spot-check Audit Summary And Strict Human Gap Report`

Status:

- `completed`
- Current summary remains explicitly AI-assisted review plus AI-assisted spot-check, not strict pure human review

Input dirs/files:

- `D:/_datefac/output/review_queue_spot_check_ingestion_343g`
- `D:/_datefac/output/review_queue_spot_check_package_343f`
- `D:/_datefac/output/review_queue_apply_simulation_343e`
- `D:/_datefac/output/review_queue_excel_ingestion_343d`
- `D:/_datefac/output/review_queue_schema_343a`

Output dir:

- `D:/_datefac/output/review_queue_audit_summary_343h`

Output workbook/report/result:

- `D:/_datefac/output/review_queue_audit_summary_343h/review_queue_audit_summary_343h.xlsx`
- `D:/_datefac/output/review_queue_audit_summary_343h/review_queue_audit_summary_343h_report.md`
- `D:/_datefac/output/review_queue_audit_summary_343h/review_queue_audit_summary_343h_strict_human_gap_report.md`
- `D:/_datefac/output/review_queue_audit_summary_343h/review_queue_audit_summary_343h_audit_matrix.json`
- `D:/_datefac/output/review_queue_audit_summary_343h/review_queue_audit_summary_343h_gap_items.jsonl`
- `D:/_datefac/output/review_queue_audit_summary_343h/review_queue_audit_summary_343h_confirmed_ai_assisted_items.jsonl`
- `D:/_datefac/output/review_queue_audit_summary_343h/review_queue_audit_summary_343h_source_check_backlog.jsonl`
- `D:/_datefac/output/review_queue_audit_summary_343h/review_queue_audit_summary_343h_client_export_gate.json`
- `D:/_datefac/output/review_queue_audit_summary_343h/review_queue_audit_summary_343h_next_action_plan.json`

Key metrics:

- `review_source_type = AI_ASSISTED_REVIEW`
- `spot_check_source_type = AI_ASSISTED_SPOT_CHECK`
- `not_pure_human_review = true`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `apply_mode = SIMULATION_ONLY`
- `ai_assisted_confirmed_count = 10`
- `source_check_required_count = 19`
- `keep_hold_count = 1`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

QA result:

- 343G input exists and is ready
- 343G result JSONL exists and is readable
- all rows preserve AI-assisted disclosure
- no row claims strict pure human review
- no formal/client/production readiness flag is true
- audit matrix generated
- strict-human-gap report generated
- source-check backlog generated
- client export gate generated and remains false
- next action plan generated
- no Argilla call made
- no real production apply performed
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `AI_ASSISTED_SPOT_CHECK_AUDIT_SUMMARY_343H_READY`

Strict human gap summary:

- 10 rows are AI-assisted spot-check confirmed only, not strict-human confirmed
- 19 rows still require source check
- 1 row remains keep-hold

Client export gate summary:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`

Next recommended task:

- `343I Strict Human Review Package For AI-assisted Confirmed Rows`

Do not repeat:

- Do not treat 343H as strict pure human review completion.
- Do not perform real write-back or production apply in 343H.
- Do not generate formal client export from 343H.
- Do not claim `client_ready = true` or `production_ready = true`.
- Do not write back 343H results to 343G / 343F / 343E / 343D or earlier artifacts.

Touched source files:

- `datefac/review_queue/audit_summary_343h.py`
- `datefac/benchmark/review_queue_audit_summary_343h.py`
- `datefac/benchmark/review_queue_audit_summary_343h_report.py`
- `tools/run_review_queue_audit_summary_343h.py`
- `tests/benchmark/test_review_queue_audit_summary_343h.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Validation commands:

```powershell
python -m py_compile datefac\review_queue\audit_summary_343h.py datefac\benchmark\review_queue_audit_summary_343h.py datefac\benchmark\review_queue_audit_summary_343h_report.py tools\run_review_queue_audit_summary_343h.py tests\benchmark\test_review_queue_audit_summary_343h.py

python -m pytest tests\benchmark\test_review_queue_audit_summary_343h.py -q

python tools\run_review_queue_audit_summary_343h.py --spot-check-ingestion-343g-dir D:\_datefac\output\review_queue_spot_check_ingestion_343g --spot-check-package-343f-dir D:\_datefac\output\review_queue_spot_check_package_343f --apply-simulation-343e-dir D:\_datefac\output\review_queue_apply_simulation_343e --review-queue-schema-343a-dir D:\_datefac\output\review_queue_schema_343a --output-dir D:\_datefac\output\review_queue_audit_summary_343h
```

Commit SHA, if known:

- `pending current 343H commit`

---

Task ID:

- `343I Strict Human Review Package For AI-assisted Confirmed Rows`

Status:

- `completed`
- waiting-for-strict-human-review package generation only

Input dirs/files:

- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g`
- `D:/_datefac/output/review_queue_schema_343a`

Output dir:

- `D:/_datefac/output/review_queue_strict_human_review_package_343i`

Output workbook/report/template:

- `D:/_datefac/output/review_queue_strict_human_review_package_343i/review_queue_strict_human_review_package_343i.xlsx`
- `D:/_datefac/output/review_queue_strict_human_review_package_343i/review_queue_strict_human_review_package_343i_review_template.xlsx`
- `D:/_datefac/output/review_queue_strict_human_review_package_343i/review_queue_strict_human_review_package_343i_review_items.jsonl`
- `D:/_datefac/output/review_queue_strict_human_review_package_343i/review_queue_strict_human_review_package_343i_reviewer_instructions.md`
- `D:/_datefac/output/review_queue_strict_human_review_package_343i/review_queue_strict_human_review_package_343i_fill_guide.md`
- `D:/_datefac/output/review_queue_strict_human_review_package_343i/review_queue_strict_human_review_package_343i_expected_import_contract.json`
- `D:/_datefac/output/review_queue_strict_human_review_package_343i/review_queue_strict_human_review_package_343i_client_export_boundary.md`
- `D:/_datefac/output/review_queue_strict_human_review_package_343i/review_queue_strict_human_review_package_343i_report.md`

Key metrics:

- `source_milestone = 343H`
- `review_queue_schema_version = 343A.review_queue.v1`
- `input_ai_assisted_confirmed_count = 10`
- `strict_review_item_count = 10`
- `source_check_backlog_context_count = 19`
- `strict_human_gap_item_count = 30`
- `strict_human_review_package_generated = true`
- `review_template_generated = true`
- `reviewer_instructions_generated = true`
- `fill_guide_generated = true`
- `expected_import_contract_generated = true`
- `waiting_for_strict_human_review = true`
- `strict_human_review_result_ingested = false`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343j = false`
- `recommended_343j_scope = strict_human_review_result_ingestion_after_user_fills_workbook`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 343H input exists and is ready
- confirmed AI-assisted items JSONL exists and is readable
- client export gate remains false
- strict review item count matches input confirmed count
- review template generated
- reviewer instructions generated
- fill guide generated
- expected import contract generated
- editable strict review columns exist
- allowed decision list is present
- no strict review decision is prefilled as completed
- waiting state remains true
- strict human review result ingestion remains false
- no strict human completion claim is made
- no Argilla call made
- no real production apply performed
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `STRICT_HUMAN_REVIEW_PACKAGE_343I_WAITING_FOR_STRICT_REVIEW`

Strict human review package summary:

- Only the 10 AI-assisted confirmed rows are included in the fillable strict review template
- The 19 source-check-required rows remain separate backlog context, not fillable strict-review rows
- The generated package is waiting for user strict human review and does not ingest results yet

Client export boundary:

- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

Next required user action:

- Open `review_queue_strict_human_review_package_343i_review_template.xlsx`
- Fill the `strict_review_*` columns plus `strict_reviewer_id` and `strict_reviewed_at`
- Save the filled workbook under `D:/_datefac/input/review_queue_strict_human_review_343i_filled/`

Next recommended task after user fills workbook:

- `343J Strict Human Review Result Ingestion After User Fills Workbook`

---

Task ID:

- `343I2 Source Evidence Enrichment For Strict Human Review Package`

Status:

- `completed`
- waiting-for-strict-review package enrichment only

Input dirs/files:

- `D:/_datefac/output/review_queue_strict_human_review_package_343i`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g`
- `D:/_datefac/output/review_queue_apply_simulation_343e`
- `D:/_datefac/output/review_queue_excel_ingestion_343d`
- `D:/_datefac/output/review_queue_schema_343a`
- `D:/_datefac/output/audit_labeled_export_candidate_package_342r`
- `D:/_datefac/output/preview_audit_export_readiness_gate_342q`
- `D:/_datefac/output/package_audit_snapshot_demo_handoff_342s`

Output dir:

- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2`

Output workbook/report/template:

- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2/review_queue_source_evidence_enrichment_343i2.xlsx`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2/review_queue_source_evidence_enrichment_343i2_enriched_review_template.xlsx`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2/review_queue_source_evidence_enrichment_343i2_enriched_items.jsonl`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2/review_queue_source_evidence_enrichment_343i2_evidence_gap_report.md`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2/review_queue_source_evidence_enrichment_343i2_evidence_resolution_map.json`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2/review_queue_source_evidence_enrichment_343i2_unresolved_evidence_items.jsonl`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2/review_queue_source_evidence_enrichment_343i2_expected_import_contract.json`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2/review_queue_source_evidence_enrichment_343i2_report.md`

Key metrics:

- `source_milestone = 343I`
- `review_queue_schema_version = 343A.review_queue.v1`
- `input_strict_review_item_count = 10`
- `enriched_review_item_count = 10`
- `evidence_resolved_count = 10`
- `evidence_partial_count = 0`
- `evidence_unresolved_count = 0`
- `source_pdf_name_available_count = 10`
- `source_pdf_path_available_count = 0`
- `page_number_available_count = 10`
- `source_text_snippet_available_count = 10`
- `image_path_available_count = 10`
- `enriched_review_template_generated = true`
- `evidence_gap_report_generated = true`
- `expected_import_contract_generated = true`
- `source_evidence_enrichment_completed = true`
- `waiting_for_strict_human_review = true`
- `strict_human_review_result_ingested = false`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343j = false`
- `recommended_343j_scope = strict_human_review_result_ingestion_after_user_fills_enriched_workbook`
- `qa_fail_count = 0`
- `no-write-back proof passed`

Evidence resolution summary:

- 343I2 traced the 10 strict review rows back through 343D source row ids
- 342R candidate CSV supplied `file_name`, `source_page`, `table_id`, `bbox`, `image_path`, and HTML evidence
- Absolute `source_pdf_path` was not available in the current upstream artifacts, so it remains blank without fabrication

QA result:

- 343I input exists and is waiting for strict human review
- strict review items exist and are readable
- exactly the expected 10 items are carried forward
- enrichment does not fabricate evidence fields
- every item has an evidence resolution status
- unresolved evidence items would be explicitly listed
- enriched review template is generated
- editable strict review columns exist
- no strict review decision is prefilled as completed
- expected import contract is generated
- no strict human completion claim is made
- no formal/client/production readiness flag is true
- no Argilla call made
- no real production apply performed
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `SOURCE_EVIDENCE_ENRICHMENT_343I2_WAITING_FOR_STRICT_REVIEW`

Client export boundary:

- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

Next required user action:

- Open `review_queue_source_evidence_enrichment_343i2_enriched_review_template.xlsx`
- Review the new evidence locator fields before filling any strict review decision
- Save the filled workbook under `D:/_datefac/input/review_queue_strict_human_review_343i2_filled/`

Next recommended task after user fills workbook:

- `343J Strict Human Review Result Ingestion After User Fills Enriched Workbook`

---

Task ID:

- `343J Strict Review Result Ingestion From Enriched Workbook`

Status:

- `completed`
- Current ingestion remains explicitly AI-assisted evidence-check input, not pure strict human review

Input dirs/files:

- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2`
- `D:/_datefac/output/review_queue_strict_human_review_package_343i`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g`
- `D:/_datefac/output/review_queue_schema_343a`
- `D:/_datefac/input/review_queue_strict_human_review_343i2_filled/review_queue_source_evidence_enrichment_343i2_enriched_review_template_filled.xlsx`

Output dir:

- `D:/_datefac/output/review_queue_strict_review_ingestion_343j`

Output workbook/report/result:

- `D:/_datefac/output/review_queue_strict_review_ingestion_343j/review_queue_strict_review_ingestion_343j.xlsx`
- `D:/_datefac/output/review_queue_strict_review_ingestion_343j/review_queue_strict_review_ingestion_343j_result.jsonl`
- `D:/_datefac/output/review_queue_strict_review_ingestion_343j/review_queue_strict_review_ingestion_343j_summary.json`
- `D:/_datefac/output/review_queue_strict_review_ingestion_343j/review_queue_strict_review_ingestion_343j_qa.json`
- `D:/_datefac/output/review_queue_strict_review_ingestion_343j/review_queue_strict_review_ingestion_343j_decision_summary.json`
- `D:/_datefac/output/review_queue_strict_review_ingestion_343j/review_queue_strict_review_ingestion_343j_client_export_gate.json`
- `D:/_datefac/output/review_queue_strict_review_ingestion_343j/review_queue_strict_review_ingestion_343j_reviewer_source_disclosure.md`
- `D:/_datefac/output/review_queue_strict_review_ingestion_343j/review_queue_strict_review_ingestion_343j_report.md`

Key metrics:

- `source_milestone = 343I2`
- `review_queue_schema_version = 343A.review_queue.v1`
- `filled_row_count = 10`
- `valid_row_count = 10`
- `invalid_row_count = 0`
- `strict_confirm_count = 10`
- `strict_correct_count = 0`
- `strict_reject_count = 0`
- `strict_needs_source_check_count = 0`
- `strict_defer_count = 0`
- `strict_review_input_source_type = AI_ASSISTED_EVIDENCE_CHECK`
- `not_pure_human_review = true`
- `pure_strict_human_confirm_count = 0`
- `ai_assisted_strict_review_confirm_count = 10`
- `strict_review_result_ingested = true`
- `pure_strict_human_review_completed = false`
- `strict_human_review_completed = false`
- `requires_strict_human_review = true`
- `requires_pure_human_confirmation = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343k = true`
- `recommended_343k_scope = pure_human_confirmation_attestation_package_for_ai_assisted_strict_confirmed_rows`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- filled workbook exists and is readable
- required sheet `04_REVIEW_TEMPLATE` exists
- required identity columns and editable strict review columns are present
- row identity matches 343I2 enriched items
- all decision values are allowed
- reviewer id/date are present for all 10 `STRICT_CONFIRM` rows
- no row claims pure strict human review completion
- reviewer-source disclosure is generated
- formal client export remains forbidden
- no Argilla call made
- no real production apply performed
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `AI_ASSISTED_STRICT_REVIEW_INGESTION_343J_READY`

Reviewer-source disclosure:

- `strict_review_input_source_type = AI_ASSISTED_EVIDENCE_CHECK`
- `review_source_type = AI_ASSISTED_REVIEW`
- `spot_check_source_type = AI_ASSISTED_SPOT_CHECK`
- `not_pure_human_review = true`
- `pure_strict_human_review_completed = false`
- `strict_human_review_completed = false`
- `requires_pure_human_confirmation = true`

Client export boundary:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- current 10-row `STRICT_CONFIRM` result still requires later pure human confirmation

Next required user action:

- Open the 343J workbook/result bundle and inspect the ingested `STRICT_CONFIRM` rows
- Preserve the AI-assisted evidence-check disclosure
- Prepare a later pure human confirmation attestation rather than treating 343J as final export approval

Next recommended task:

- `343K Pure Human Confirmation Attestation Package`

---

Task ID:

- `343K Pure Human Confirmation Attestation Package For AI-assisted Strict-confirmed Rows`

Status:

- `completed`
- Current state is intentionally waiting for later pure human attestation input

Input dirs/files:

- `D:/_datefac/output/review_queue_strict_review_ingestion_343j`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2`
- `D:/_datefac/output/review_queue_schema_343a`

Output dir:

- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k`

Output workbook/package artifacts:

- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k/review_queue_pure_human_attestation_package_343k.xlsx`
- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k/review_queue_pure_human_attestation_package_343k_attestation_template.xlsx`
- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k/review_queue_pure_human_attestation_package_343k_attestation_items.jsonl`
- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k/review_queue_pure_human_attestation_package_343k_summary.json`
- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k/review_queue_pure_human_attestation_package_343k_qa.json`
- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k/review_queue_pure_human_attestation_package_343k_report.md`
- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k/review_queue_pure_human_attestation_package_343k_reviewer_instructions.md`
- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k/review_queue_pure_human_attestation_package_343k_fill_guide.md`
- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k/review_queue_pure_human_attestation_package_343k_expected_import_contract.json`
- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k/review_queue_pure_human_attestation_package_343k_client_export_boundary.md`

Key metrics:

- `source_milestone = 343J`
- `review_queue_schema_version = 343A.review_queue.v1`
- `input_ai_assisted_strict_review_confirm_count = 10`
- `attestation_item_count = 10`
- `evidence_resolved_count = 10`
- `source_pdf_name_available_count = 10`
- `source_text_snippet_available_count = 10`
- `pure_human_attestation_package_generated = true`
- `attestation_template_generated = true`
- `reviewer_instructions_generated = true`
- `fill_guide_generated = true`
- `expected_import_contract_generated = true`
- `waiting_for_pure_human_attestation = true`
- `pure_human_attestation_result_ingested = false`
- `pure_strict_human_confirm_count = 0`
- `ai_assisted_strict_review_confirm_count = 10`
- `pure_strict_human_review_completed = false`
- `strict_human_review_completed = false`
- `requires_pure_human_confirmation = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343l = false`
- `recommended_343l_scope = pure_human_confirmation_attestation_result_ingestion_after_user_fills_workbook`
- `qa_fail_count = 0`
- `no-write-back proof passed`

QA result:

- 343J input exists and is ready
- AI-assisted evidence-check disclosure is preserved
- all 10 `STRICT_CONFIRM` rows are carried forward as attestation items
- source locator fields are preserved into the attestation package
- attestation template is generated
- reviewer instructions are generated
- fill guide is generated
- expected import contract is generated
- editable `human_*` attestation columns exist
- human attestation decisions are intentionally blank
- waiting-for-human-attestation state is preserved
- pure strict human review is not claimed complete
- formal client export remains forbidden
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `PURE_HUMAN_ATTESTATION_PACKAGE_343K_WAITING_FOR_HUMAN_ATTESTATION`

Attestation package summary:

- Current 10 rows remain AI-assisted strict-confirm rows, not pure human final confirmations
- Human reviewers must independently verify source evidence before attesting accept/correct/reject/check-source/defer

Client export boundary:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

Next required user action:

- Open the 343K attestation template workbook
- Independently inspect source evidence for each of the 10 rows
- Fill only the `human_*` columns and save the workbook under `D:/_datefac/input/review_queue_pure_human_attestation_343k_filled/`

Next recommended task after user fills workbook:

- `343L Pure Human Confirmation Attestation Result Ingestion`

---

Task ID:

- `343L Pure Human Attestation Result Ingestion`

Status:

- `completed`
- Current completion is explicitly limited to the `343K_PACKAGE_ONLY` scope

Input dirs/files:

- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k`
- `D:/_datefac/output/review_queue_strict_review_ingestion_343j`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2`
- `D:/_datefac/output/review_queue_schema_343a`
- `D:/_datefac/input/review_queue_pure_human_attestation_343k_filled/review_queue_pure_human_attestation_package_343k_attestation_template_filled.xlsx`

Output dir:

- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l`

Output workbook/result artifacts:

- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l/review_queue_pure_human_attestation_ingestion_343l.xlsx`
- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l/review_queue_pure_human_attestation_ingestion_343l_result.jsonl`
- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l/review_queue_pure_human_attestation_ingestion_343l_summary.json`
- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l/review_queue_pure_human_attestation_ingestion_343l_qa.json`
- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l/review_queue_pure_human_attestation_ingestion_343l_decision_summary.json`
- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l/review_queue_pure_human_attestation_ingestion_343l_client_export_gate.json`
- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l/review_queue_pure_human_attestation_ingestion_343l_scope_boundary.md`
- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l/review_queue_pure_human_attestation_ingestion_343l_report.md`

Key metrics:

- `source_milestone = 343K`
- `review_queue_schema_version = 343A.review_queue.v1`
- `filled_row_count = 10`
- `valid_row_count = 10`
- `invalid_row_count = 0`
- `human_accept_count = 10`
- `human_correct_count = 0`
- `human_reject_count = 0`
- `human_needs_source_check_count = 0`
- `human_defer_count = 0`
- `human_source_evidence_checked_true_count = 10`
- `human_independent_check_attested_true_count = 10`
- `pure_human_attestation_result_ingested = true`
- `pure_strict_human_confirm_count = 10`
- `pure_strict_human_correct_count = 0`
- `pure_strict_human_review_completed_for_package = true`
- `strict_human_review_completed_scope = 343K_PACKAGE_ONLY`
- `global_strict_human_review_completed = false`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343m = true`
- `recommended_343m_scope = human_confirmed_sidecar_apply_simulation_and_limited_export_gate`
- `qa_fail_count = 0`
- `no-write-back proof passed`

Validation result:

- filled workbook exists and is readable
- required sheet `04_ATTESTATION_TEMPLATE` exists
- required identity columns and editable human attestation columns are present
- workbook identity matches 343K attestation items
- all 10 rows use allowed human attestation decisions
- all 10 rows are `HUMAN_ACCEPT_AI_ASSISTED_CONFIRM`
- reviewer id/date are present
- `human_source_evidence_checked = true` for all 10 rows
- `human_independent_check_attested = true` for all 10 rows
- package-level human confirmation is completed
- global strict human review is not claimed complete
- formal client export remains forbidden
- no Argilla call made
- no real production apply performed
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `PURE_HUMAN_ATTESTATION_INGESTION_343L_READY`

Package-level human attestation completion summary:

- The current 10-row 343K package has completed pure human confirmation
- This completion scope is explicitly limited to `343K_PACKAGE_ONLY`
- It does not mean the whole corpus has completed global strict human review

Client export boundary:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Next recommended task:

- `343M Human-confirmed Sidecar Apply Simulation And Limited Export Gate`

---

Task ID:

- `343M Human-confirmed Sidecar Apply Simulation And Limited Export Gate`

Status:

- `completed`
- Current output is a limited package-scope sidecar simulation only

Input dirs/files:

- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l`
- `D:/_datefac/output/review_queue_pure_human_attestation_package_343k`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_schema_343a`

Output dir:

- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m`

Output workbook/sidecar/gate artifacts:

- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m/review_queue_human_confirmed_sidecar_simulation_343m.xlsx`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m/review_queue_human_confirmed_sidecar_simulation_343m_summary.json`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m/review_queue_human_confirmed_sidecar_simulation_343m_qa.json`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m/review_queue_human_confirmed_sidecar_simulation_343m_sidecar.jsonl`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m/review_queue_human_confirmed_sidecar_simulation_343m_apply_plan.jsonl`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m/review_queue_human_confirmed_sidecar_simulation_343m_limited_export_gate.json`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m/review_queue_human_confirmed_sidecar_simulation_343m_limited_export_candidate.jsonl`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m/review_queue_human_confirmed_sidecar_simulation_343m_remaining_backlog.jsonl`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m/review_queue_human_confirmed_sidecar_simulation_343m_scope_boundary.md`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m/review_queue_human_confirmed_sidecar_simulation_343m_report.md`

Key metrics:

- `source_milestone = 343L`
- `review_queue_schema_version = 343A.review_queue.v1`
- `input_human_attested_row_count = 10`
- `valid_human_attested_row_count = 10`
- `sidecar_row_count = 10`
- `sidecar_human_accept_count = 10`
- `sidecar_human_correct_count = 0`
- `sidecar_blocked_count = 0`
- `limited_export_candidate_row_count = 10`
- `remaining_source_check_backlog_count = 19`
- `package_strict_human_review_completed = true`
- `strict_human_review_completed_scope = 343K_PACKAGE_ONLY`
- `global_strict_human_review_completed = false`
- `sidecar_apply_simulation_completed = true`
- `limited_export_gate_evaluated = true`
- `limited_package_export_candidate_allowed = true`
- `limited_export_scope = 343K_PACKAGE_ONLY`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_343n = true`
- `recommended_343n_scope = limited_human_confirmed_export_package_generation_for_demo_only`
- `qa_fail_count = 0`
- `no-write-back proof passed`

Validation result:

- 343L input exists and is ready
- package-level human confirmation is true
- global strict human review remains false
- formal/client/production flags remain false
- sidecar row count matches accepted/corrected human rows
- limited export candidate row count matches sidecar row count
- limited export candidate explicitly carries `343K_PACKAGE_ONLY`
- remaining backlog is carried forward with `19` source-check rows
- limited export gate is generated
- no Argilla call made
- no real production apply performed
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_READY`

Sidecar simulation summary:

- The 10 package-confirmed rows were simulated into a sidecar-only result set
- All 10 current sidecar rows are human-confirmed accepts
- No blocked package rows remain inside the current 343K scope

Limited export gate summary:

- `limited_package_export_candidate_allowed = true`
- `limited_export_scope = 343K_PACKAGE_ONLY`
- This is only a scoped audited sample/demo candidate, not formal client export approval

Remaining backlog summary:

- `remaining_source_check_backlog_count = 19`
- Global strict-human review remains incomplete outside the package scope

Next recommended task:

- `343N Limited Human-confirmed Export Package Generation For Demo Only`

---

Task ID:

- `343O Demo Package Audit Snapshot And Handoff Summary`

Status:

- `completed`
- Current output closes only the 10-row trusted demo arc; it does not expand trusted coverage.

Input dirs/files:

- `D:/_datefac/output/review_queue_limited_demo_export_package_343n`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m`
- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_schema_343a`

Output dir:

- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o`

Output workbook/report/artifacts:

- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o/review_queue_demo_audit_snapshot_343o.xlsx`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o/review_queue_demo_audit_snapshot_343o_report.md`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o/review_queue_demo_audit_snapshot_343o_handoff_summary.md`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o/review_queue_demo_audit_snapshot_343o_executive_summary.md`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o/review_queue_demo_audit_snapshot_343o_trust_chain.md`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o/review_queue_demo_audit_snapshot_343o_artifact_index.json`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o/review_queue_demo_audit_snapshot_343o_export_gate_snapshot.json`

Key metrics:

- `review_queue_schema_version = 343A.review_queue.v1`
- `input_demo_export_row_count = 10`
- `audit_label_row_count = 10`
- `limited_export_scope = 343K_PACKAGE_ONLY`
- `export_usage = DEMO_ONLY`
- `remaining_source_check_backlog_count = 19`
- `package_strict_human_review_completed = true`
- `global_strict_human_review_completed = false`
- `demo_only_export_package_generated = true`
- `demo_handoff_ready = true`
- `demo_audit_snapshot_generated = true`
- `handoff_summary_generated = true`
- `executive_summary_generated = true`
- `trust_chain_generated = true`
- `artifact_index_generated = true`
- `export_gate_snapshot_generated = true`
- `demo_arc_closed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_344a = true`
- `recommended_344a_scope = source_check_backlog_resolution_package`
- `qa_fail_count = 0`
- `no-write-back proof passed`

Validation result:

- 343N input exists and is ready
- demo package row count is 10
- audit label row count is 10
- limited export scope remains `343K_PACKAGE_ONLY`
- export usage remains `DEMO_ONLY`
- demo README / scope boundary / export gate are all present
- trust chain, handoff summary, executive summary, artifact index, and gate snapshot are generated
- demo arc is closed only for the current 10-row package scope
- formal client export remains forbidden
- no Argilla call made
- no real production apply performed
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `DEMO_PACKAGE_AUDIT_SNAPSHOT_343O_READY`

Demo audit snapshot summary:

- 343O turns the 343N demo-only export package into a handoff-ready audit snapshot bundle.
- The trust chain is documented from schema through AI-assisted audit, evidence enrichment reference, pure human attestation, sidecar simulation, and limited demo export packaging.
- The current trusted arc is now documentation-complete for the 10-row package scope.

Boundary summary:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- remaining backlog outside the package scope still blocks any global export claim

Next recommended task:

- `344A Source-check Backlog Resolution Package`

---

Task ID:

- `344A Source-check Backlog Resolution Package`

Status:

- `completed`
- Current output is intentionally waiting for reviewer source-check input and does not ingest results yet.

Input dirs/files:

- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o`
- `D:/_datefac/output/review_queue_limited_demo_export_package_343n`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g`
- `D:/_datefac/output/review_queue_spot_check_package_343f`
- `D:/_datefac/output/review_queue_schema_343a`

Output dir:

- `D:/_datefac/output/review_queue_source_check_backlog_package_344a`

Output workbook/package artifacts:

- `D:/_datefac/output/review_queue_source_check_backlog_package_344a/review_queue_source_check_backlog_package_344a.xlsx`
- `D:/_datefac/output/review_queue_source_check_backlog_package_344a/review_queue_source_check_backlog_package_344a_review_template.xlsx`
- `D:/_datefac/output/review_queue_source_check_backlog_package_344a/review_queue_source_check_backlog_package_344a_backlog_items.jsonl`
- `D:/_datefac/output/review_queue_source_check_backlog_package_344a/review_queue_source_check_backlog_package_344a_evidence_map.json`
- `D:/_datefac/output/review_queue_source_check_backlog_package_344a/review_queue_source_check_backlog_package_344a_reviewer_instructions.md`
- `D:/_datefac/output/review_queue_source_check_backlog_package_344a/review_queue_source_check_backlog_package_344a_fill_guide.md`
- `D:/_datefac/output/review_queue_source_check_backlog_package_344a/review_queue_source_check_backlog_package_344a_expected_import_contract.json`
- `D:/_datefac/output/review_queue_source_check_backlog_package_344a/review_queue_source_check_backlog_package_344a_report.md`

Key metrics:

- `review_queue_schema_version = 343A.review_queue.v1`
- `input_remaining_source_check_backlog_count = 19`
- `source_check_backlog_item_count = 19`
- `deduplicated_backlog_item_count = 19`
- `evidence_resolved_count = 0`
- `evidence_partial_count = 0`
- `evidence_unresolved_count = 19`
- `source_pdf_name_available_count = 0`
- `source_text_snippet_available_count = 0`
- `source_check_backlog_package_generated = true`
- `review_template_generated = true`
- `reviewer_instructions_generated = true`
- `fill_guide_generated = true`
- `expected_import_contract_generated = true`
- `waiting_for_source_check_review = true`
- `source_check_result_ingested = false`
- `source_check_backlog_resolved = false`
- `demo_arc_closed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_344b = false`
- `recommended_344b_scope = source_check_backlog_result_ingestion_after_user_fills_workbook`
- `qa_fail_count = 0`
- `no-write-back proof passed`

Validation result:

- 343O input exists and is ready
- backlog source exists and is readable
- deduplicated backlog count matches the expected 19 rows
- every backlog item has a stable identity key
- every backlog item has an evidence resolution status
- unresolved evidence is explicitly disclosed
- review template, reviewer instructions, fill guide, and expected import contract are generated
- editable source-check columns exist and no source-check decision is prefilled
- waiting-for-source-check-review state is preserved
- source-check results are not ingested yet
- formal/client/production readiness flags remain false
- 343O demo arc remains unchanged
- no Argilla call made
- no real production apply performed
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `SOURCE_CHECK_BACKLOG_PACKAGE_344A_WAITING_FOR_SOURCE_CHECK_REVIEW`

Backlog package summary:

- 344A creates a focused review package for the 19 remaining source-check backlog rows after the 10-row trusted demo arc was closed by 343O.
- Current upstream backlog artifacts contain almost no usable PDF/page/table evidence locators for these 19 rows, so the package discloses them conservatively as unresolved rather than fabricating evidence.

Export/global boundary:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `source_check_result_ingested = false`
- `source_check_backlog_resolved = false`

Next required user action:

- Open the 344A review template workbook
- Review each backlog row conservatively against whatever source evidence can be independently located
- Save the filled workbook under `D:/_datefac/input/review_queue_source_check_backlog_344a_filled/`

Next recommended task after user fills workbook:

- `344B Source-check Backlog Result Ingestion After User Fills Workbook`

---

Task ID:

- `344A2 Source Evidence Enrichment For Source-check Backlog`

Status:

- `completed`
- Current output is intentionally waiting for reviewer source-check input and does not ingest results yet.

Input dirs/files:

- `D:/_datefac/output/review_queue_source_check_backlog_package_344a`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o`
- `D:/_datefac/output/review_queue_audit_summary_343h`
- `D:/_datefac/output/review_queue_spot_check_ingestion_343g`
- `D:/_datefac/output/review_queue_spot_check_package_343f`
- `D:/_datefac/output/review_queue_source_evidence_enrichment_343i2`
- `D:/_datefac/output/review_queue_schema_343a`
- scanned read-only `D:/_datefac/output/*342*` and `D:/_datefac/output/*343*` artifact candidates, with exact evidence hits coming primarily from `342R` and `343D`

Output dir:

- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2`

Output workbook/package artifacts:

- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2/review_queue_source_check_evidence_enrichment_344a2.xlsx`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2/review_queue_source_check_evidence_enrichment_344a2_enriched_review_template.xlsx`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2/review_queue_source_check_evidence_enrichment_344a2_enriched_backlog_items.jsonl`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2/review_queue_source_check_evidence_enrichment_344a2_evidence_match_candidates.jsonl`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2/review_queue_source_check_evidence_enrichment_344a2_match_confidence_audit.jsonl`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2/review_queue_source_check_evidence_enrichment_344a2_evidence_map.json`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2/review_queue_source_check_evidence_enrichment_344a2_reviewer_instructions.md`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2/review_queue_source_check_evidence_enrichment_344a2_fill_guide.md`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2/review_queue_source_check_evidence_enrichment_344a2_expected_import_contract.json`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2/review_queue_source_check_evidence_enrichment_344a2_unresolved_evidence_report.md`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2/review_queue_source_check_evidence_enrichment_344a2_artifact_search_report.md`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2/review_queue_source_check_evidence_enrichment_344a2_scope_boundary.md`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2/review_queue_source_check_evidence_enrichment_344a2_report.md`

Scanned artifact categories:

- `342R audit-labeled export candidates`
- `343D reviewed result ingestion`
- `343B excel round-trip reviewed result`
- `343E apply simulation`
- `343G spot-check ingestion`
- `343H audit summary backlog`
- `343I2 prior source-evidence enrichment package`

Key metrics:

- `review_queue_schema_version = 343A.review_queue.v1`
- `input_source_check_backlog_item_count = 19`
- `deduplicated_backlog_item_count = 19`
- `evidence_resolved_count = 19`
- `evidence_partial_count = 0`
- `evidence_unresolved_count = 0`
- `source_pdf_name_available_count = 19`
- `page_number_available_count = 19`
- `image_path_available_count = 19`
- `source_text_snippet_available_count = 19`
- `match_candidate_count = 209`
- `high_confidence_match_count = 57`
- `medium_confidence_match_count = 0`
- `low_confidence_match_count = 152`
- `auto_enriched_item_count = 19`
- `unresolved_item_count = 0`
- `source_check_evidence_enrichment_completed = true`
- `enriched_review_template_generated = true`
- `evidence_map_generated = true`
- `reviewer_instructions_generated = true`
- `fill_guide_generated = true`
- `expected_import_contract_generated = true`
- `waiting_for_source_check_review = true`
- `source_check_result_ingested = false`
- `source_check_backlog_resolved = false`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `ready_for_344b = false`
- `recommended_344b_scope = source_check_evidence_review_result_ingestion_after_user_fills_workbook`
- `qa_fail_count = 0`
- `no-write-back proof passed`

Validation result:

- 344A input exists and is ready
- all 19 backlog rows are preserved
- no source-check decision is prefilled
- every backlog item has an evidence resolution status
- exact `review_item_id` / `343D source_row_id -> 342R export_candidate_row_id` trace is sufficient to auto-enrich all 19 rows
- low-confidence matches are logged but not required for the applied enrichment
- enriched review template, reviewer instructions, fill guide, expected import contract, unresolved report, and artifact search report are generated
- waiting-for-source-check-review state is preserved
- source-check results are not ingested
- formal/client/production readiness flags remain false
- no Argilla call made
- no real production apply performed
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_WAITING_FOR_SOURCE_CHECK_REVIEW`

Evidence enrichment summary:

- 344A2 closes the evidence-locator gap left by 344A for the 19 remaining source-check backlog rows.
- The enrichment is still conservative: it fills source PDF / page / table / image / snippet locators, but does not confirm, correct, reject, or defer any row automatically.

Export/global boundary:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `source_check_result_ingested = false`
- `source_check_backlog_resolved = false`

Next required user action:

- Open the 344A2 enriched review template workbook
- Review each row using the enriched PDF/page/table/image/snippet evidence fields
- Save the filled workbook under `D:/_datefac/input/review_queue_source_check_evidence_344a2_filled/`

Next recommended task after user fills workbook:

- `344B Source-check Evidence Review Result Ingestion After User Fills Workbook`

---

Task ID:

- `344B Source-check Evidence Review Result Ingestion`

Status:

- `completed`
- Current output ingests the filled 344A2 enriched source-check workbook into sidecar-only result artifacts.

Input dirs/files:

- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2`
- `D:/_datefac/output/review_queue_source_check_backlog_package_344a`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o`
- `D:/_datefac/output/review_queue_schema_343a`
- `D:/_datefac/input/review_queue_source_check_evidence_344a2_filled/review_queue_source_check_evidence_enrichment_344a2_enriched_review_template_filled_independent.xlsx`

Output dir:

- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b`

Output workbook/report/artifacts:

- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b/review_queue_source_check_evidence_review_ingestion_344b.xlsx`
- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b/review_queue_source_check_evidence_review_ingestion_344b_summary.json`
- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b/review_queue_source_check_evidence_review_ingestion_344b_qa.json`
- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b/review_queue_source_check_evidence_review_ingestion_344b_result.jsonl`
- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b/review_queue_source_check_evidence_review_ingestion_344b_validated_sidecar.jsonl`
- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b/review_queue_source_check_evidence_review_ingestion_344b_corrections.jsonl`
- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b/review_queue_source_check_evidence_review_ingestion_344b_audit_gate.json`
- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b/review_queue_source_check_evidence_review_ingestion_344b_scope_boundary.md`
- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b/review_queue_source_check_evidence_review_ingestion_344b_report.md`

Key metrics:

- `review_queue_schema_version = 343A.review_queue.v1`
- `filled_row_count = 19`
- `valid_row_count = 19`
- `invalid_row_count = 0`
- `source_confirm_count = 10`
- `source_correct_count = 9`
- `source_reject_count = 0`
- `source_still_insufficient_count = 0`
- `source_defer_count = 0`
- `validated_sidecar_row_count = 19`
- `correction_row_count = 9`
- `source_check_result_ingested = true`
- `source_check_backlog_resolved = true`
- `validated_sidecar_generated = true`
- `correction_sidecar_generated = true`
- `audit_gate_generated = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `ready_for_344c = true`
- `recommended_344c_scope = source_check_confirmed_sidecar_apply_simulation_and_expanded_trust_gate`
- `qa_fail_count = 0`
- `no-write-back proof passed`

Validation result:

- 344A2 input exists and remains in waiting-for-source-check-review state
- filled workbook exists and sheet `04_REVIEW_TEMPLATE` is readable
- exactly 19 filled rows are ingested
- filled row identities match the 344A2 enriched backlog rows
- all source-check decisions are allowed
- 10 rows are `SOURCE_CONFIRM`
- 9 rows are `SOURCE_CORRECT`
- all 9 corrected rows preserve source year/value and correct `revenue / 亿元` to `YOY / %`
- validated sidecar and corrections JSONL are generated
- audit gate is generated
- no production write-back occurred
- no formal client export occurred
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `SOURCE_CHECK_EVIDENCE_REVIEW_INGESTION_344B_READY`

Source-check result summary:

- 344B resolves the 19-row source-check backlog only as a sidecar review-result ingestion scope.
- The 9 corrected rows are YOY percentage rows, not revenue amount rows.

Export/global boundary:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Next recommended task:

- `344C Source-check Confirmed Sidecar Apply Simulation And Expanded Trust Gate`

---

Task ID:

- `344C Source-check Confirmed Sidecar Apply Simulation And Expanded Trust Gate`

Status:

- `completed`
- Current output expands trusted coverage only as a sidecar apply simulation across the prior 10-row demo arc plus 19 source-check resolved rows.

Input dirs/files:

- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o`
- `D:/_datefac/output/review_queue_limited_demo_export_package_343n`
- `D:/_datefac/output/review_queue_human_confirmed_sidecar_simulation_343m`
- `D:/_datefac/output/review_queue_pure_human_attestation_ingestion_343l`
- `D:/_datefac/output/review_queue_schema_343a`

Output dir:

- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c`

Output workbook/report/artifacts:

- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c/review_queue_source_check_sidecar_simulation_344c.xlsx`
- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c/review_queue_source_check_sidecar_simulation_344c_summary.json`
- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c/review_queue_source_check_sidecar_simulation_344c_qa.json`
- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c/review_queue_source_check_sidecar_simulation_344c_source_check_apply_plan.jsonl`
- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c/review_queue_source_check_sidecar_simulation_344c_source_check_applied_sidecar.jsonl`
- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c/review_queue_source_check_sidecar_simulation_344c_expanded_trusted_candidates.jsonl`
- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c/review_queue_source_check_sidecar_simulation_344c_corrections_applied.jsonl`
- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c/review_queue_source_check_sidecar_simulation_344c_dedup_audit.jsonl`
- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c/review_queue_source_check_sidecar_simulation_344c_expanded_trust_gate.json`
- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c/review_queue_source_check_sidecar_simulation_344c_scope_boundary.md`
- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c/review_queue_source_check_sidecar_simulation_344c_report.md`

Key metrics:

- `review_queue_schema_version = 343A.review_queue.v1`
- `source_check_input_sidecar_row_count = 19`
- `source_check_apply_plan_row_count = 19`
- `source_check_apply_confirm_count = 10`
- `source_check_apply_correct_count = 9`
- `source_check_apply_blocked_count = 0`
- `source_check_applied_sidecar_row_count = 19`
- `corrections_applied_count = 9`
- `prior_demo_trusted_row_count = 10`
- `source_check_trusted_row_count = 19`
- `expanded_trusted_candidate_count = 29`
- `deduplicated_expanded_trusted_candidate_count = 29`
- `dedup_conflict_count = 0`
- `expanded_trusted_scope = 343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`
- `source_check_sidecar_apply_simulation_completed = true`
- `source_check_applied_sidecar_generated = true`
- `expanded_trusted_candidates_generated = true`
- `expanded_trust_gate_evaluated = true`
- `dedup_audit_generated = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `ready_for_344d = true`
- `recommended_344d_scope = expanded_trusted_export_package_generation_for_review_demo_only`
- `qa_fail_count = 0`
- `no-write-back proof passed`

Validation result:

- 344B input exists and is ready
- 344B validated sidecar has 19 rows
- source-check confirm/correct counts match 10/9
- apply plan has 19 rows and no blocked rows
- source-check applied sidecar has 19 rows
- correction semantics are carried forward as YOY/% rows
- 343N/343O demo trusted rows are readable and count 10
- expanded trusted candidate count is 29
- dedup audit is generated
- dedup conflict count is 0
- expanded trust gate is generated
- no production write-back occurred
- no formal client export occurred
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `SOURCE_CHECK_SIDECAR_SIMULATION_344C_READY`

Expanded trusted candidate summary:

- 344C combines the prior 10-row demo trusted arc with the 19 source-check resolved rows from 344B.
- The resulting 29-row expanded trusted coverage remains simulation-only and review/demo scoped.

Export/global boundary:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Next recommended task:

- `344D Expanded Trusted Export Package Generation For Review Demo Only`

---

Task ID:

- `344D Expanded Trusted Export Package Generation For Review Demo Only`

Status:

- `completed`
- Current output packages the 29-row expanded trusted candidate set into a review/demo-only export package with audit labels, lineage summary, export gate, and scope boundary.

Input dirs/files:

- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c`
- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o`
- `D:/_datefac/output/review_queue_limited_demo_export_package_343n`
- `D:/_datefac/output/review_queue_schema_343a`

Output dir:

- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d`

Output workbook/report/artifacts:

- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d.xlsx`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_summary.json`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_manifest.json`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_qa.json`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_report.md`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_demo_readme.md`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_export_rows.jsonl`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_export_rows.csv`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_audit_labels.jsonl`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_export_gate.json`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_lineage_summary.json`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_scope_boundary.md`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_handoff_summary.md`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_metric_distribution.json`
- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d/review_queue_expanded_trusted_demo_export_package_344d_no_write_back_proof.json`

Key metrics:

- `review_queue_schema_version = 343A.review_queue.v1`
- `input_expanded_trusted_candidate_count = 29`
- `expanded_export_row_count = 29`
- `audit_label_row_count = 29`
- `prior_demo_trusted_row_count = 10`
- `source_check_trusted_row_count = 19`
- `source_check_confirmed_row_count = 10`
- `source_check_corrected_row_count = 9`
- `correction_row_count = 9`
- `dedup_conflict_count = 0`
- `expanded_export_scope = 343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`
- `export_usage = REVIEW_DEMO_ONLY`
- `expanded_review_demo_package_generated = true`
- `expanded_demo_handoff_ready = true`
- `expanded_export_gate_generated = true`
- `lineage_summary_generated = true`
- `audit_labels_generated = true`
- `source_check_backlog_resolved = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `ready_for_344e = true`
- `recommended_344e_scope = expanded_trusted_demo_audit_snapshot_and_final_handoff_summary`
- `qa_fail_count = 0`
- `no-write-back proof passed`

Validation result:

- 344C input exists and is ready
- expanded trusted candidates file has 29 rows
- no dedup conflicts exist
- expanded export rows count is 29
- audit labels count is 29
- every export row carries explicit review/demo-only and not-formal-export labels
- lineage summary matches 10 prior demo rows + 19 source-check resolved rows
- corrected row semantics are preserved as `YOY / %` for 9 corrected rows
- export gate is generated
- no production write-back occurred
- no formal client export occurred
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `EXPANDED_TRUSTED_DEMO_EXPORT_PACKAGE_344D_READY`

Expanded export package summary:

- 344D packages the prior 10-row demo trusted arc together with 19 source-check resolved rows from 344B.
- The resulting 29-row package is explicitly labeled for review/demo-only handoff.

Lineage summary:

- `343N_DEMO` rows = `10`
- `344B_SOURCE_CHECK` rows = `19`
- source-check confirmed rows = `10`
- source-check corrected rows = `9`
- corrected rows keep `YOY` and `%` semantics
- dedup conflict count = `0`

Export gate summary:

- `expanded_review_demo_package_generated = true`
- `expanded_demo_handoff_ready = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Audit label summary:

- every row carries:
  `EXPANDED_TRUSTED_CANDIDATE`,
  `REVIEW_DEMO_ONLY`,
  `NOT_FORMAL_CLIENT_EXPORT`,
  `NOT_PRODUCTION_READY`,
  `NO_PRODUCTION_WRITE_BACK`
- prior demo rows additionally carry `PACKAGE_SCOPE_HUMAN_CONFIRMED`
- source-check resolved rows additionally carry `SOURCE_CHECK_RESOLVED`
- corrected source-check rows additionally carry `SOURCE_CHECK_CORRECTED`
- confirmed source-check rows additionally carry `SOURCE_CHECK_CONFIRMED`

Export/global boundary:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Next recommended task:

- `344E Expanded Trusted Demo Audit Snapshot And Final Handoff Summary`

---

Task ID:

- `344E Expanded Trusted Demo Audit Snapshot And Final Handoff Summary`

Status:

- `completed`
- Current output closes the 29-row expanded trusted review/demo arc with the final audit snapshot, final handoff summary, executive summary, trust-chain report, artifact index, final export gate snapshot, and scope boundary.

Input dirs/files:

- `D:/_datefac/output/review_queue_expanded_trusted_demo_export_package_344d`
- `D:/_datefac/output/review_queue_source_check_sidecar_simulation_344c`
- `D:/_datefac/output/review_queue_source_check_evidence_review_ingestion_344b`
- `D:/_datefac/output/review_queue_source_check_evidence_enrichment_344a2`
- `D:/_datefac/output/review_queue_demo_audit_snapshot_343o`
- `D:/_datefac/output/review_queue_limited_demo_export_package_343n`
- `D:/_datefac/output/review_queue_schema_343a`

Output dir:

- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e`

Output workbook/report/artifacts:

- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e.xlsx`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_summary.json`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_manifest.json`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_qa.json`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_report.md`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_final_handoff_summary.md`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_executive_summary.md`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_trust_chain_report.md`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_artifact_index.json`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_artifact_index.md`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_final_export_gate_snapshot.json`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_lineage_audit_summary.json`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_metric_distribution.json`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_scope_boundary.md`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_next_action_plan.json`
- `D:/_datefac/output/review_queue_expanded_demo_audit_snapshot_344e/review_queue_expanded_demo_audit_snapshot_344e_no_write_back_proof.json`

Key metrics:

- `review_queue_schema_version = 343A.review_queue.v1`
- `input_expanded_export_row_count = 29`
- `audit_label_row_count = 29`
- `prior_demo_trusted_row_count = 10`
- `source_check_trusted_row_count = 19`
- `source_check_confirmed_row_count = 10`
- `source_check_corrected_row_count = 9`
- `correction_row_count = 9`
- `expanded_export_scope = 343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`
- `export_usage = REVIEW_DEMO_ONLY`
- `expanded_demo_audit_snapshot_generated = true`
- `final_handoff_summary_generated = true`
- `executive_summary_generated = true`
- `trust_chain_report_generated = true`
- `artifact_index_generated = true`
- `final_export_gate_snapshot_generated = true`
- `lineage_audit_summary_generated = true`
- `metric_distribution_generated = true`
- `expanded_demo_arc_closed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `ready_for_345a = true`
- `recommended_345a_scope = formal_export_readiness_gap_assessment`
- `qa_fail_count = 0`
- `no-write-back proof passed`

Validation result:

- 344D input exists and is ready
- expanded export rows count is 29
- audit labels count is 29
- expanded export scope is correct
- export usage is `REVIEW_DEMO_ONLY`
- lineage summary matches `10 + 19 = 29`
- source-check corrected rows count is 9
- corrected row semantics `YOY / %` are disclosed
- final handoff summary is generated
- executive summary is generated
- trust-chain report is generated
- artifact index is generated
- final export gate snapshot is generated
- final boundary still blocks formal/client/production readiness
- no production write-back occurred
- no formal client export occurred
- no upstream workbook modified
- no protected dirty files staged
- no output / temp / forbidden input paths staged
- no sheet name exceeds 31 chars
- no-write-back proof passed

Decision:

- `EXPANDED_TRUSTED_DEMO_AUDIT_SNAPSHOT_344E_READY`

Final expanded demo audit snapshot summary:

- 344E closes the expanded 29-row review/demo arc formed by the 10 earlier demo rows plus 19 source-check resolved rows.
- The package remains review/demo-only and should not be described as formal client export.

Final handoff summary:

- open 344E executive summary, trust-chain report, artifact index, and final export gate snapshot first
- then open the 344D workbook to inspect the 29-row expanded trusted package itself
- 9 corrected rows must be interpreted as `YOY / %`, not revenue amount rows

Trust-chain summary:

- trust accumulation now spans schema -> audit baseline -> evidence enrichment -> package human confirmation -> limited gate -> 10-row demo arc -> 19-row source-check resolution -> expanded 29-row package -> final audit snapshot
- the earlier 10-row arc and later 19-row source-check resolution are both explicitly represented

Artifact index summary:

- indexes the key 344D / 344C / 344B / 344A2 / 343O artifacts
- every indexed artifact remains non-formal-export and review/demo scoped

Final export gate snapshot:

- `expanded_review_demo_package_generated = true`
- `expanded_demo_handoff_ready = true`
- `expanded_demo_audit_snapshot_generated = true`
- `final_handoff_summary_generated = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Export/global boundary:

- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

Next recommended task:

- `345A Formal Export Readiness Gap Assessment`

## 344F Strict Human Review Package

Status: completed

Decision:

- `STRICT_HUMAN_REVIEW_PACKAGE_344F_READY`

Output:

- `D:\_datefac\output\review_queue_strict_human_review_package_344f`

Key metrics:

- `strict_review_row_count = 29`
- `prior_demo_trusted_row_count = 10`
- `source_check_trusted_row_count = 19`
- `source_check_confirmed_row_count = 10`
- `corrected_row_count = 9`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `upstream_workbooks_unchanged = true`
- `strict_human_review_package_generated = true`
- `global_strict_human_review_completed = false`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `export_usage = STRICT_HUMAN_REVIEW_ONLY`

Validation result:

- `py_compile` passed
- `pytest` passed: `2 passed`
- real runner passed

Boundary reminder:

- 344F only generates a strict human review package for the 29-row expanded trusted demo set
- 344F does not enable formal client export
- `global_strict_human_review_completed = false`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

## 345A Full Structured Data Inventory

Status: completed

Decision:

- `FULL_STRUCTURED_DATA_INVENTORY_345A_READY`

Output:

- `D:\_datefac\output\full_structured_data_inventory_345a`

Input stage:

- `POST_344F_FULL_STRUCTURED_INVENTORY`

Key metrics:

- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `total_inventory_row_count = 14788`
- `LONG_FORM_CELL = 5607`
- `TRUSTED_CELL = 1578`
- `REVIEW_REQUIRED = 4240`
- `REJECTED_OR_EXCLUDED = 3213`
- `HUMAN_REVIEW_APPLIED = 121`
- `STRICT_HUMAN_REVIEW_PENDING_ROW = 29`
- `UNKNOWN_STAGE = 0`
- `missing_unit_count = 3949`
- `missing_period_count = 399`
- `missing_source_page_count = 5232`
- `missing_metric_name_count = 0`
- `downstream_ready_candidate_count = 11575`
- `blocked_rejected_status_count = 3213`
- `blocked_missing_metric_name_count = 0`
- `blocked_missing_value_count = 0`
- `blocked_missing_source_trace_count = 0`

Validation result:

- `py_compile` passed
- `pytest` passed: `3 passed`
- real runner passed

Boundary reminder:

- 345A only inventories existing structured artifacts
- it does not rerun MinerU
- it does not call LLM / VLM
- it does not enable formal client export
- 344G still waits for a genuinely human-filled 344F workbook

Next recommended tasks:

- `345B Full Extraction Quality Audit`
- `345C Metric Candidate Normalization Coverage`
- `345D Full Structured Demo Export Package`
- `345E Full Structured QA Gate`

## 345C Metric Candidate Normalization Coverage

Status: completed

Decision:

- `METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_READY`

Output:

- `D:\_datefac\output\metric_candidate_normalization_coverage_345c`

Input stage:

- `POST_345B_NORMALIZATION_COVERAGE`

Key metrics:

- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `input_inventory_row_count = 14788`
- `input_audited_row_count = 14788`
- `metric_candidate_row_count = 14788`
- `normalized_metric_row_count = 6691`
- `unnormalized_metric_row_count = 8097`
- `normalization_coverage_ratio = 0.452461`
- `unique_raw_metric_name_count = 207`
- `unique_normalized_metric_name_count = 18`
- `unique_unnormalized_raw_metric_name_count = 134`
- `alias_candidate_count = 134`
- `high_priority_alias_candidate_count = 26`
- `stage_with_lowest_coverage = REJECTED_OR_EXCLUDED`
- `pdf_with_lowest_coverage = H3_AP202606061823323264_1.pdf`
- `ready_candidate_count_before_normalization_filter = 11575`
- `ready_candidate_count_after_normalization_filter = 6676`

Validation result:

- `py_compile` passed
- `pytest` passed: `3 passed`
- real runner passed

Top blind spots:

- `财务费用`
- `利润总额`
- `EV/EBITDA`
- `成本`
- `营业利润`

Boundary reminder:

- 345C is analysis-only across existing 345A / 345B artifacts
- it does not modify normalization rules
- it does not rerun MinerU
- it does not call LLM / VLM
- it does not enable formal client export
- 344G still waits for a genuinely human-filled 344F workbook

Next recommended tasks:

- `345D Full Structured Demo Export Package`
- `345E Full Structured QA Gate`

## 345C7 Official Alias Rule Update Candidate Package

Status: completed

Decision:

- `OFFICIAL_ALIAS_RULE_UPDATE_CANDIDATE_PACKAGE_345C7_READY`

Output:

- `D:\_datefac\output\official_alias_rule_update_candidate_package_345c7`

Input stage:

- `POST_345C6_OFFICIAL_ALIAS_RULE_UPDATE_CANDIDATE_PACKAGE`

Key metrics:

- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `validated_approved_alias_count = 22`
- `candidate_row_count = 22`
- `controlled_rule_update_candidate_count = 0`
- `demo_only_sidecar_candidate_count = 3`
- `needs_additional_review_candidate_count = 19`
- `do_not_update_rule_candidate_count = 0`
- `low_risk_candidate_count = 0`
- `medium_risk_candidate_count = 3`
- `high_risk_candidate_count = 19`
- `simulated_alias_applied_row_count = 1813`
- `simulated_newly_normalized_row_count = 1813`
- `normalization_coverage_ratio_before = 0.452461`
- `normalization_coverage_ratio_after_simulation = 0.575061`
- `normalization_coverage_ratio_delta = 0.1226`
- `ready_candidate_count_before_simulation = 6676`
- `ready_candidate_count_after_alias_simulation = 8146`
- `ready_candidate_count_delta = 1470`
- `remaining_unnormalized_raw_metric_name_count = 112`
- `remaining_unnormalized_metric_row_count = 6284`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `candidate_package_only = true`
- `controlled_rule_update_ready = false`
- `full_structured_demo_export_reasonable = false`

Validation result:

- `py_compile` passed
- `pytest` passed: `2 passed`
- real runner passed

Boundary reminder:

- 345C7 only packages reviewed approved aliases into a candidate package for later explicit review
- it does not modify normalization rules
- it does not modify official alias assets
- it does not write back into 345C5 / 345C6 or upstream data
- it does not enable formal client export
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

Next recommended task:

- `345C4/345C5 additional review batch`

## 345C8 Remaining Blind Spot Alias Candidate Package

Status: completed

Decision:

- `REMAINING_BLIND_SPOT_ALIAS_CANDIDATE_PACKAGE_345C8_READY`

Output:

- `D:\_datefac\output\remaining_blind_spot_alias_candidate_package_345c8`

Input stage:

- `POST_345C7_REMAINING_BLIND_SPOT_CANDIDATE_SELECTION`

Key metrics:

- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `remaining_unnormalized_raw_metric_name_count = 112`
- `remaining_unnormalized_metric_row_count = 6284`
- `max_blind_spot_candidates = 30`
- `min_row_impact = 10`
- `selected_candidate_count = 30`
- `unselected_blind_spot_count = 82`
- `selected_estimated_row_impact_total = 3071`
- `selected_estimated_coverage_delta_total = 0.207667`
- `selected_estimated_ready_candidate_delta_total = 0`
- `high_priority_candidate_count = 25`
- `medium_priority_candidate_count = 5`
- `low_priority_candidate_count = 0`
- `include_in_second_review_batch_count = 16`
- `include_as_context_only_count = 3`
- `defer_low_impact_count = 0`
- `exclude_too_generic_count = 6`
- `needs_source_context_before_review_count = 11`
- `low_risk_candidate_count = 0`
- `medium_risk_candidate_count = 16`
- `high_risk_candidate_count = 14`
- `alias_branch_stop_or_continue_decision = CONTINUE_WITH_SECOND_REVIEW_BATCH`
- `full_structured_demo_export_reasonable_after_345c8 = false`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`
- `candidate_package_only = true`

Validation result:

- `py_compile` passed
- `pytest` passed: `2 passed`
- real runner passed

Boundary reminder:

- 345C8 only selects Top N remaining blind-spot alias candidates and emits a stop-or-continue decision
- it does not perform human review
- it does not call LLM / VLM
- it does not modify normalization rules or official alias assets
- it does not write back into 345C6 / 345C7 or upstream data
- it does not enable formal client export
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`

Next recommended task:

- `345C9 Remaining Blind Spot Human Review Package`

## 345C9 Remaining Blind Spot Human Review Package

Status: completed

Decision:
- `REMAINING_BLIND_SPOT_HUMAN_REVIEW_PACKAGE_345C9_READY`

Input package:
- `D:\_datefac\output\remaining_blind_spot_alias_candidate_package_345c8`

Output package:
- `D:\_datefac\output\remaining_blind_spot_human_review_package_345c9`

Key metrics:
- `selected_candidate_count = 30`
- `review_required_row_count = 16`
- `context_only_row_count = 3`
- `blocked_or_too_generic_row_count = 11`
- `generated_review_pending_count = 16`
- `generated_approved_count = 0`
- `alias_rule_update_allowed_count = 0`
- `qa_fail_count = 0`

Gate status:
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

No-write-back confirmation:
- `no_write_back_proof_passed = true`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`

Validation commands and results:
- `python -m py_compile ...` passed
- `python -m pytest tests\benchmark\test_remaining_blind_spot_human_review_package_345c9.py -q` passed
- real runner passed

Next recommended step:
- human fills workbook, then `345C10 Second Batch Reviewed Alias Decision Ingestion`

## 345C10 Second Batch Reviewed Alias Decision Ingestion

Status: completed

Decision:
- `SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION_345C10_READY`

Input package:
- `D:\_datefac\output\remaining_blind_spot_human_review_package_345c9`

Reviewed workbook path:
- `D:\_datefac\output\remaining_blind_spot_human_review_package_345c9\remaining_blind_spot_human_review_package_345c9_reviewed.xlsx`

Output package:
- `D:\_datefac\output\second_batch_reviewed_alias_decision_ingestion_345c10`

Key metrics:
- `reviewed_row_count = 16`
- `approved_existing_mapping_count = 0`
- `approved_new_standard_count = 15`
- `rejected_too_generic_count = 0`
- `needs_source_context_count = 1`
- `deferred_count = 0`
- `validation_issue_count = 0`
- `apply_simulation_eligible_count = 15`
- `qa_fail_count = 0`

Gate status:
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

No-write-back confirmation:
- `no_write_back_proof_passed = true`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`

Validation commands and results:
- `python -m py_compile ...` passed
- `python -m pytest tests\benchmark\test_second_batch_reviewed_alias_decision_ingestion_345c10.py -q` passed
- real runner passed

Next recommended step:
- `345C11 Second Batch Alias Apply Simulation`

## 345C11 Second Batch Alias Apply Simulation

Status: completed

Decision:
- `SECOND_BATCH_ALIAS_APPLY_SIMULATION_345C11_READY`

Input packages:
- `345C = D:\_datefac\output\metric_candidate_normalization_coverage_345c`
- `345C6 = D:\_datefac\output\reviewed_alias_apply_simulation_345c6`
- `345C10 = D:\_datefac\output\second_batch_reviewed_alias_decision_ingestion_345c10`

Output package:
- `D:\_datefac\output\second_batch_alias_apply_simulation_345c11`

Key metrics:
- `first_batch_alias_count = 22`
- `second_batch_eligible_alias_count = 15`
- `second_batch_simulated_newly_normalized_row_count = 1613`
- `cumulative_simulated_newly_normalized_row_count = 3426`
- `coverage_ratio_before = 0.452461`
- `coverage_ratio_after_first_batch = 0.575061`
- `coverage_ratio_after_second_batch = 0.684136`
- `remaining_unnormalized_metric_row_count = 4671`
- `remaining_unnormalized_raw_metric_name_count = 96`
- `ready_candidate_count_after_first_batch = 8146`
- `ready_candidate_count_after_second_batch = 8974`
- `qa_fail_count = 0`

Alias branch final recommendation:
- `STOP_ALIAS_BRANCH_AND_RETURN_TO_345D`

Gate status:
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

No-write-back confirmation:
- `no_write_back_proof_passed = true`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`

Validation commands and results:
- `python -m py_compile ...` passed
- `python -m pytest tests\benchmark\test_second_batch_alias_apply_simulation_345c11.py -q` passed
- real runner passed

Next recommended step:
- `345D Full Structured Demo Export Package`

## 345D Full Structured Demo Export Package

Status: completed

Decision:
- `FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY`

Input packages:
- `345A = D:\_datefac\output\full_structured_data_inventory_345a`
- `345B = D:\_datefac\output\full_extraction_quality_audit_345b`
- `345C = D:\_datefac\output\metric_candidate_normalization_coverage_345c`
- `345C11 = D:\_datefac\output\second_batch_alias_apply_simulation_345c11`

Output package:
- `D:\_datefac\output\full_structured_demo_export_package_345d`

Key metrics:
- `demo_export_row_count = 109`
- `quality_limited_row_count = 5558`
- `excluded_row_count = 9121`
- `coverage_ratio_after_alias_simulation = 0.684136`
- `remaining_unnormalized_raw_metric_name_count = 96`
- `remaining_unnormalized_metric_row_count = 4671`
- `high_severity_issue_count = 7595`
- `medium_severity_issue_count = 7084`
- `qa_fail_count = 0`

Gate status:
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

No-write-back confirmation:
- `no_write_back_proof_passed = true`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`

Validation commands and results:
- `python -m py_compile ...` passed
- `python -m pytest tests\benchmark\test_full_structured_demo_export_package_345d.py -q` passed
- real runner passed

Next recommended step:
- `345E Demo Export Review / QA Checklist`

## 345E Demo Export Review / QA Checklist

Status: completed

Decision:
- `DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_READY`

Input package:
- `345D = D:\_datefac\output\full_structured_demo_export_package_345d`

Output package:
- `D:\_datefac\output\demo_export_review_qa_checklist_345e`

QA checklist summary:
- `checked_artifact_count = 18`
- `missing_required_artifact_count = 0`
- `optional_missing_artifact_count = 0`
- `artifact_read_error_count = 0`
- `row_count_closure_passed = true`
- `demo_export_row_count = 109`
- `quality_limited_row_count = 5558`
- `excluded_row_count = 9121`
- `caveat_completeness_passed = true`
- `gate_safety_check_passed = true`
- `presentation_ready_for_demo_only = true`
- `qa_fail_count = 0`

Gate status:
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `formal_export_generated = false`
- `demo_export_only = true`

No-write-back confirmation:
- `no_write_back_proof_passed = true`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`

Validation commands and results:
- `python -m py_compile ...` passed
- `python -m pytest tests\benchmark\test_demo_export_review_qa_checklist_345e.py -q` passed
- real runner passed

Next recommended step:
- `345F Demo Narrative Report Package`
- `344G` still waits for a genuinely human-filled `344F` workbook

## 345F Demo Narrative Report Package

Status: completed

Decision:
- `DEMO_NARRATIVE_REPORT_PACKAGE_345F_READY`

Input packages:
- `345D = D:\_datefac\output\full_structured_demo_export_package_345d`
- `345E = D:\_datefac\output\demo_export_review_qa_checklist_345e`

Output package:
- `D:\_datefac\output\demo_narrative_report_package_345f`

Key metrics:
- `generated_report_count = 10`
- `demo_export_row_count = 109`
- `quality_limited_row_count = 5558`
- `excluded_row_count = 9121`
- `inventory_row_count = 14788`
- `coverage_ratio_before_alias_simulation = 0.452461`
- `coverage_ratio_after_alias_simulation = 0.684136`
- `sample_rows_for_story_count = 10`
- `qa_fail_count = 0`

QA readiness summary:
- `row_count_closure_passed = true`
- `gate_safety_check_passed = true`
- `caveat_completeness_passed = true`
- `presentation_ready_for_demo_only = true`

Gate status:
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `formal_export_generated = false`
- `demo_export_only = true`

No-write-back confirmation:
- `no_write_back_proof_passed = true`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`

Validation commands and results:
- `python -m py_compile ...` passed
- `python -m pytest tests\benchmark\test_demo_narrative_report_package_345f.py -q` passed
- real runner passed

Next recommended step:
- `345G Demo Presentation Slide Outline`
- `344G` still waits for a genuinely human-filled `344F` workbook

## 345E Demo Export Review / QA Checklist

Status: completed

- decision: DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_READY
- input package: D:\_datefac\output\full_structured_demo_export_package_345d
- output package: D:\_datefac\output\demo_export_review_qa_checklist_345e
- checked_artifact_count: 18
- missing_required_artifact_count: 0
- optional_missing_artifact_count: 0
- artifact_read_error_count: 0
- row_count_closure_passed: True
- demo_export_row_count: 109
- quality_limited_row_count: 5558
- excluded_row_count: 9121
- caveat_completeness_passed: False
- gate_safety_check_passed: True
- presentation_ready_for_demo_only: False
- no_write_back_proof_passed: True
- formal_client_export_allowed: False
- client_ready: False
- production_ready: False
- global_strict_human_review_completed: False
- sample_demo_row_count: 30
- sample_quality_limited_row_count: 30
- sample_excluded_row_count: 30
- next recommended step: 345F Demo Narrative Report Package

Validation commands and results:
- py_compile: 
- pytest: 
- real runner: 

No-write-back confirmation:
- upstream inputs unchanged; official assets unchanged; protected dirty status preserved; no protected paths staged

## 345F Demo Narrative Report Package

Status: completed

Decision:
- `DEMO_NARRATIVE_REPORT_PACKAGE_345F_READY`

Input packages:
- `345D = D:\_datefac\output\full_structured_demo_export_package_345d`
- `345E = D:\_datefac\output\demo_export_review_qa_checklist_345e`

Output package:
- `D:\_datefac\output\demo_narrative_report_package_345f`

Key metrics:
- `generated_report_count = 10`
- `demo_export_row_count = 109`
- `quality_limited_row_count = 5558`
- `excluded_row_count = 9121`
- `coverage_ratio_before_alias_simulation = 0.452461`
- `coverage_ratio_after_alias_simulation = 0.684136`
- `sample_rows_for_story_count = 10`
- `qa_fail_count = 0`

Gate status:
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`

No-write-back confirmation:
- `no_write_back_proof_passed = true`
- `official_rules_modified = false`
- `official_alias_assets_modified = false`

Validation commands and results:
- `python -m py_compile ...` passed
- `python -m pytest tests\benchmark\test_demo_narrative_report_package_345f.py -q` passed
- real runner passed

Next recommended step:
- `345G Demo Presentation Slide Outline`
- `344G` still waits for a genuinely human-filled `344F` workbook

## 346A Vision-Assisted Table Evidence Pilot

Status: completed

- decision: VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY
- input packages: 345D=D:\_datefac\output\full_structured_demo_export_package_345d; 345E=D:\_datefac\output\demo_export_review_qa_checklist_345e; optional MinerU evidence dirs were suggestion-only
- output package: D:\_datefac\output\vision_assisted_table_evidence_pilot_346a
- selected_pilot_row_count: 100
- evidence_bundle_count: 100
- image_bound_count: 0
- image_missing_count: 100
- ambiguous_image_candidate_count: 0
- vlm_request_count: 0
- live_vlm_call_count: 0
- target_field_distribution: {"raw_metric_name": 94, "unit": 92, "value": 100}
- no_write_back_proof_passed: True
- gate status: formal_client_export_allowed=False, client_ready=False, production_ready=False
- validation commands and results:
- `python -m py_compile ...` passed
- `python -m pytest tests\benchmark\test_vision_assisted_table_evidence_pilot_346a.py -q` passed
- real runner passed
- next recommended step: 346A2 MinerU Image Path Binding Fix

## 346A2 MinerU Image Path Binding Fix

Status: completed

- decision: MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY
- input_346a_dir: D:\_datefac\output\vision_assisted_table_evidence_pilot_346a
- supplied_mineru_evidence_dirs: D:\_datefac\output\mineru_pilot_network_recovery_342c6\mineru_outputs
- output_dir: D:\_datefac\output\mineru_image_path_binding_fix_346a2
- selected_pilot_row_count: 100
- binding_candidate_count: 178
- image_bound_count: 38
- table_crop_bound_count: 38
- page_image_bound_count: 0
- json_md_context_bound_count: 70
- image_missing_count: 62
- ambiguous_image_candidate_count: 0
- vlm_request_count: 38
- live_vlm_call_count: 0
- no_write_back_proof_passed: True
- gate_status: formal_client_export_allowed=False, client_ready=False, production_ready=False
- next_recommended_step: 346B Quality-Limited Row Recovery Pilot

## 346B Quality-Limited Row Recovery Pilot

Status: completed

- decision: QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY
- input_345d_dir: D:\_datefac\output\full_structured_demo_export_package_345d
- input_346a_dir: D:\_datefac\output\vision_assisted_table_evidence_pilot_346a
- input_346a2_dir: D:\_datefac\output\mineru_image_path_binding_fix_346a2
- output_dir: D:\_datefac\output\quality_limited_row_recovery_pilot_346b
- full_quality_limited_row_count: 5558
- pilot_input_row_count: 100
- image_bound_input_count: 38
- json_md_context_bound_input_count: 70
- sanitized_value_success_count: 100
- unit_injection_success_count: 78
- period_injection_success_count: 0
- evidence_assisted_recovery_success_count: 70
- recovered_demo_candidate_count: 70
- still_quality_limited_count: 4
- needs_vlm_count: 0
- needs_human_review_count: 26
- downgraded_excluded_count: 0
- live_vlm_call_count: 0
- no_write_back_proof_passed: True
- gate_status: formal_client_export_allowed=False, client_ready=False, production_ready=False
- next_recommended_step: 345G Demo Presentation Slide Outline

## 346B2 Recovery Candidate QA Audit

Status: completed

- decision: RECOVERY_CANDIDATE_QA_AUDIT_346B2_READY
- input_345d_dir: D:\_datefac\output\full_structured_demo_export_package_345d
- input_346a_dir: D:\_datefac\output\vision_assisted_table_evidence_pilot_346a
- input_346a2_dir: D:\_datefac\output\mineru_image_path_binding_fix_346a2
- input_346b_dir: D:\_datefac\output\quality_limited_row_recovery_pilot_346b
- output_dir: D:\_datefac\output\recovery_candidate_qa_audit_346b2
- audited_recovered_candidate_count: 70
- safe_recovered_candidate_count: 32
- risky_recovered_candidate_count: 0
- false_positive_suspect_count: 38
- unit_repair_risk_count: 38
- ratio_multiple_unit_mismatch_count: 24
- percentage_unit_mismatch_count: 0
- per_share_unit_mismatch_count: 14
- monetary_unit_mismatch_count: 0
- unit_not_applicable_verified_count: 0
- unit_not_applicable_risk_count: 0
- image_bound_recovered_count: 38
- text_context_only_recovered_count: 32
- needs_rule_refinement_count: 0
- human_review_triage_count: 26
- still_limited_triage_count: 4
- safe_to_expand_recovery: False
- live_vlm_call_count: 0
- no_write_back_proof_passed: True
- gate_status: formal_client_export_allowed=False, client_ready=False, production_ready=False
- next_recommended_step: 346B3 Recovery Rule Refinement
