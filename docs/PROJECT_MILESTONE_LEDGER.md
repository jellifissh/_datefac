# DateFac Project Milestone Ledger

Generated / last refreshed: 2026-06-10

This ledger is the project-level source of truth for completed numbered DateFac tasks. Its purpose is to prevent future chats, Codex runs, or new models from repeating completed work.

## How To Use This Ledger

Before starting any numbered DateFac task:

1. Read `AGENTS.md`.
2. Read this file: `docs/PROJECT_MILESTONE_LEDGER.md`.
3. Read the relevant `.skills/*.md` workflow files.
4. Read the latest task document in `docs/codex_tasks/`.
5. Check existing output summary / QA files for the previous stage.
6. If the requested task is already `completed` with `qa_fail_count = 0`, do not rerun it unless the user explicitly asks for a revision.
7. If a task was revised, mark the older behavior as `superseded` and record the effective version.

After completing any numbered DateFac task:

1. Update this ledger in the same source commit as the task code or in an immediate follow-up commit.
2. Record: task id, status, effective version, input dirs, output dir, key metrics, QA result, next task, and do-not-repeat notes.
3. Keep `client_ready = false` and `production_ready = false` unless a task explicitly and safely changes that status.

## Global Git And Safety Guardrails

Never stage these unless explicitly requested:

- `output/`
- `temp/`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- large generated benchmark/demo artifacts
- unrelated dirty files

Never use:

- `git add -A`
- `git add .`
- `git reset --hard`
- `git checkout --` to discard unrelated work

Protected dirty files / dirs:

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## Current Effective Mainline

The effective current mainline is:

```text
legacy demo / Trust Engine / human-review work
-> MinerU-first real PDF benchmark
-> table-first MinerU output audit
-> table-first core financial long-form extraction
```

Current next task:

```text
342G Table-First Extraction Review Package
```

Do not restart these completed stages unless explicitly requested as a revision:

- 306N-310D legacy core metric demo-ready pipeline
- 320D-322I router / parser / semantic adjudicator chain
- 324 / 325 official rule governance cycles
- 330A-330L Trust Engine and client-style preview chain
- 340B-341A human-reviewed client preview milestone chain
- 342A-342E real PDF / MinerU benchmark chain

## Status Vocabulary

- `completed`: task output exists and QA passed.
- `completed_with_warnings`: output exists and QA passed, but caveats remain.
- `superseded`: older behavior replaced by a later effective version.
- `blocked`: task could not proceed due to missing input/environment.
- `planned`: task designed but not implemented.
- `do_not_repeat`: completed stage should not be rerun without explicit revision request.

---

# 1. Legacy Core Metric Pipeline: 306N-310D

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
- `trusted_to_total_ratio ≈ 13.3%`
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

# 2. Parser / Router / Semantic Adjudicator Chain: 320D-322I

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

- 320G `trusted_rate ≈ 0.0719`

Conclusion:

- PPStructure is a weak legacy fallback, not the main route.

## 321A-321B2 VLM / Pure VLM Calibration

Status: `completed`

Key result:

- 321B2 pure VLM calibrated `trusted_rate ≈ 0.3362`

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

- `trusted_rate ≈ 0.3833`

Conclusion:

- MinerU body became the PDF table_body baseline.

## 321E1-321E5 Docling / StructEqTable / Full Bakeoff

Status: `completed`

Docling:

- `trusted_rate ≈ 0.3068`
- status = backup candidate

StructEqTable:

- 321E3: `10 / 10` image tables parsed successfully.
- 321E4B: `core_candidate_trusted_rate ≈ 0.3587`, `all_candidate_trusted_rate ≈ 0.3054`.

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

# 3. Official Rule Governance And Trust Engine: 324 / 325 / 330A-330L

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

# 4. Human-Reviewed Client Preview Milestone: 340B-341A

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

# 5. Real PDF / MinerU Benchmark Mainline: 342A-342E

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

---

# 6. Current Next Task: 342G

## 342F Table-First Core Financial Table Long-Form Extraction

Status: `completed`

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
- Keep `06_METADATA_EXTRACTABLE` out of core extraction; metadata tables may be handled by a separate future task.
- Parse HTML tables.
- Expand wide financial tables into long-form cells:

```text
pdf_id | table_id | table_type | metric | year | value | unit | page | bbox | image_path | review_status
```

Output dir:

- `D:/_datefac/output/table_first_core_financial_extraction_342f`

Expected output workbook:

- `table_first_core_financial_extraction_342f.xlsx`

Expected decision:

- `TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_READY`

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

# 7. Environment Ledger

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

# 8. Superseded / Deprecated Routes

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

# 9. New Topic Recovery Prompt

Paste this into a new chat/model when continuing DateFac:

```text
This is DateFac, a financial research-report PDF core metric extraction project at D:/_datefac.

Do not start from scratch. First read docs/PROJECT_MILESTONE_LEDGER.md, AGENTS.md, .skills/README.md, .skills/git_workflow.md, .skills/mineru_local_benchmark_workflow.md, .skills/real_pdf_benchmark_workflow.md, .skills/human_reviewed_client_preview_workflow.md, and .skills/table_extraction.md.

The current effective mainline is MinerU-first / table-first.

Completed current chain:
- 342A real PDF benchmark plan completed.
- 342B corpus intake completed: 31 unique PDFs, pilot/benchmark/holdout = 5/20/6.
- 342C initial MinerU run failed due environment/SSL/HF, superseded.
- 342C2 retry succeeded 3/5, superseded.
- 342C6 network recovery rerun succeeded 5/5 and is the effective MinerU pilot success baseline.
- 342D parser ensemble compare completed, MinerU outputs artifact complete 5/5, ready_for_342E true.
- 342E was revised to table-first and completed: total_table_block_count=370, core_extractable_table_count=66, metadata_extractable_table_count=18, excluded_table_count=62, manual_review_required_count=224, pdf_with_core_extractable_table_count=5, ready_for_342f=true, recommended_342f_scope=table_first_core_extractable_only, qa_fail_count=0.

Do not repeat old 342E text candidate route. Do not rerun MinerU. Do not call VLM. Do not redo 342D.

Current next task:
342G Table-First Extraction Review Package.

342F has completed table-first long-form extraction from D:/_datefac/output/core_metric_candidate_quality_342e, primarily sheet 05_CORE_EXTRACTABLE. BASIC_DATA remained metadata-only and EXCLUDED tables were not used.

Next:
342G should package the table-first extraction review workflow on top of the completed 342F long-form output.

Keep client_ready=false and production_ready=false.
Do not modify production pipeline/parser/extraction/delivery.
Do not write back to upstream workbooks.
Do not stage output/, temp/, semantic_adjudicator_responses dirs, or protected dirty files.
Use precise git add only.
```

---

# 10. Ledger Maintenance Requirement

This ledger must be updated whenever any of these happens:

- a numbered task is completed;
- a task is rerun with a new effective behavior;
- an old route is superseded;
- the next recommended task changes;
- `client_ready`, `client_preview_ready`, `demo_ready`, or `production_ready` changes;
- a new parser/tool becomes the effective mainline;
- a new no-repeat / protected boundary is discovered.

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

Failure to update this file after a completed milestone is a process bug.

---

# 11. Current Safety Flags

Current safe statements:

- `demo_ready = true` for the human-reviewed preview milestone.
- `client_preview_ready = true` for 341A only.
- `client_ready = false`.
- `production_ready = false`.
- MinerU 342C6 pilot is 5/5 successful.
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
