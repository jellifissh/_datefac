# NEXT CODEX TASK

## task_title
Expand Stage 1 AI repair deterministic extract replay coverage

## project
D:\_datefac

## current_status
The Stage 1 AI repair deterministic extract replay set has completed.

Latest user-uploaded/reviewed outputs:
- D:\_datefac\output\delivery_package\46_stage1_ai_repair_extract_replay_log.md
- D:\_datefac\output\delivery_package\46_stage1_ai_repair_extract_replay_log.xlsx
- D:\_datefac\output\delivery_package\47_stage1_ai_repair_extract_replay_evaluation.md
- D:\_datefac\output\delivery_package\47_stage1_ai_repair_extract_replay_evaluation.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_replay\extract_replay_responses.jsonl
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_replay\ai_repair_results.jsonl
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_replay\ai_repair_results.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_replay\ai_repair_candidates.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_replay\ai_repair_validation.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_replay\ai_repair_merge_preview.xlsx

Key result from 46/47:
- task_title = Add Stage 1 AI repair deterministic extract replay set
- extract_replay_status = WARN
- processed_task_count = 77
- response_file_task_count = 9
- decision_counts = {extract: 7, manual_review: 69, ignore: 1}
- extracted_candidate_count = 7
- ai_candidate_for_rule_validation_count = 7
- manual_review_candidate_count = 69
- ignore_count = 1
- schema_validation_status = PASS
- evidence_check_status = PASS
- invalid_extract_count = 0
- value_not_in_evidence_count = 0
- year_not_in_evidence_count = 0
- sample_extract_summary = S1: 6, S3: 1
- target_metric_extract_summary = EBITDA: 1, EV/EBITDA: 2, P/B: 1, P/E: 1, 营业收入: 2
- production_delivery_status_after = PASS / pass_count=17 / warn_count=0 / fail_count=0
- production_files_unchanged = true
- production_guard_changed_count = 0
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model download not triggered
- no real AI inference call was made

Interpretation:
The extract path now works end-to-end: deterministic offline extract responses can pass schema/evidence checks and appear as `ai_candidate_for_rule_validation` in merge preview. Coverage is still limited: S1 dominates, S3 has only one extract, S2 has none, and target metrics do not yet cover net profit/EPS/ROE. Before connecting a real provider, expand the deterministic extract replay set with per-sample curated task selection.

## goal
Expand deterministic extract replay coverage by selecting more safe, evidence-backed extract tasks from the Stage 1 packet.

This task must remain sandbox-only and offline-only. It must not call a real model.

Target code:
- D:\_datefac\tools\run_stage1_ai_repair_worker.py if validation changes are needed
- D:\_datefac\tools\build_stage1_ai_repair_extract_replay_set.py

Target local reports:
- D:\_datefac\output\delivery_package\48_stage1_ai_repair_extract_coverage_log.md
- D:\_datefac\output\delivery_package\48_stage1_ai_repair_extract_coverage_log.xlsx
- D:\_datefac\output\delivery_package\49_stage1_ai_repair_extract_coverage_evaluation.md
- D:\_datefac\output\delivery_package\49_stage1_ai_repair_extract_coverage_evaluation.xlsx

Sandbox extract coverage replay dir:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_coverage

Expected sandbox files:
- extract_coverage_responses.jsonl
- ai_repair_results.jsonl
- ai_repair_results.xlsx
- ai_repair_candidates.xlsx
- ai_repair_validation.xlsx
- ai_repair_merge_preview.xlsx
- extract_task_selection_diagnostics.xlsx

## absolute_hard_constraints
1. Do not run factory_core.py.
2. Do not trigger marker / surya / vision / PaddleOCR.
3. Do not download model.safetensors or any model.
4. Do not call any real LLM, local model, cloud API, or AI inference endpoint.
5. Do not use network.
6. Do not run OCR.
7. Do not reprocess PDFs.
8. Do not rebuild production delivery_package.
9. Do not run apply_manual_review_corrections.py.
10. Do not modify production delivery files:
   - 01_自动可信核心指标.xlsx
   - 02_人工复核指标队列.xlsx
   - 02A_人工年份修正覆盖表.xlsx
   - 06_最终核心财务指标.xlsx
11. Do not process baseline 091 as Stage 1 sample.
12. Do not commit output artifacts.
13. Worklog must be English only and UTF-8.
14. Chinese company/metric text must remain readable, no `????` or `�`.

## implementation_requirements

### 1. Curated task selection
Enhance `build_stage1_ai_repair_extract_replay_set.py` to select deterministic extracts more deliberately.

Read:
- D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json

Selection targets:
- Prefer 10 to 20 response tasks total, if deterministic evidence allows.
- Try to include at least:
  - S1: 5 to 10 extract responses
  - S3: 3 to 8 extract responses
  - S2: keep table-level manual_review unless deterministic metric/value evidence exists
- Try to cover target metrics beyond previous set:
  - 营业收入
  - 归属母公司净利润 / 归母净利润
  - 每股收益 / EPS
  - P/E
  - P/B
  - EV/EBITDA
  - ROE
  - EBITDA
- Do not fabricate coverage. If a metric/sample cannot be safely extracted, record why in diagnostics.

### 2. Safe extract construction rules
Every extract response must obey:
- value appears in row_cells, row_preview, nearby_rows_context, or raw_table_preview;
- year appears in detected_years or evidence text;
- standard_metric is target metric or appears in evidence;
- source task has enough context to justify metric-year-value alignment;
- no hard-risk evidence should be hidden.

If exact alignment is unclear, generate manual_review instead of extract.

### 3. Diagnostics
Create `extract_task_selection_diagnostics.xlsx` with sheets:
- candidate_task_pool
- selected_extract_tasks
- rejected_extract_candidates
- sample_metric_coverage_gap
- manual_review_due_to_ambiguity

Required diagnostic fields:
- repair_task_id
- sample_id
- task_type
- standard_metric_hint
- detected_years
- selected_decision
- selected_metric
- selected_year
- selected_value
- evidence_source
- reject_reason if any
- confidence

### 4. Worker replay
Run `run_stage1_ai_repair_worker.py` with provider `offline_file` using the generated `extract_coverage_responses.jsonl`.

Expected behavior:
- schema validation PASS;
- evidence check PASS;
- invalid_extract_count = 0;
- accepted extracts route to `ai_candidate_for_rule_validation`;
- missing responses route to manual_review_candidate;
- production files unchanged.

### 5. Reports 48/49
Generate:
- D:\_datefac\output\delivery_package\48_stage1_ai_repair_extract_coverage_log.md
- D:\_datefac\output\delivery_package\48_stage1_ai_repair_extract_coverage_log.xlsx

48 report must include:
- task_title
- started_at / finished_at
- commands_run
- packet_path
- schema_path
- extract_coverage_dir
- response_file_path
- response_file_task_count
- extract_response_count
- manual_review_response_count
- ignore_response_count
- output_files_generated
- production_guard_changed_count
- safety_checks

Generate:
- D:\_datefac\output\delivery_package\49_stage1_ai_repair_extract_coverage_evaluation.md
- D:\_datefac\output\delivery_package\49_stage1_ai_repair_extract_coverage_evaluation.xlsx

49 report must include:
- extract_coverage_status: PASS / WARN / FAIL
- processed_task_count
- response_file_task_count
- decision_counts
- extracted_candidate_count
- ai_candidate_for_rule_validation_count
- manual_review_candidate_count
- ignore_count
- schema_validation_status
- evidence_check_status
- invalid_extract_count
- value_not_in_evidence_count
- year_not_in_evidence_count
- merge_preview_summary
- sample_extract_summary
- target_metric_extract_summary
- sample_metric_coverage_gap
- rejected_extract_candidate_summary
- production_delivery_status_after
- production_files_unchanged
- recommended_next_step

Excel sheets required:
- summary
- response_inventory
- task_results
- extracted_candidates
- evidence_check
- merge_preview
- sample_extract_summary
- target_metric_extract_summary
- coverage_gap
- rejected_extract_candidates
- production_guard
- safety_checks
- next_steps

## validation_commands
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\run_stage1_ai_repair_worker.py
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\build_stage1_ai_repair_extract_replay_set.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\build_stage1_ai_repair_extract_replay_set.py ^
  --packet-jsonl D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl ^
  --schema-json D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json ^
  --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --max-extracts 20 ^
  --coverage-mode curated
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

## acceptance_criteria
This task passes if:
1. py_compile passes.
2. Extract coverage response JSONL is generated.
3. Worker runs offline_file with the extract coverage JSONL.
4. At least 7 previously accepted extracts still pass, unless explicitly rejected with valid reason.
5. S3 extract count increases if deterministic evidence allows; if not, gap is documented.
6. Every accepted extract value passes evidence check.
7. No invalid extract becomes `ai_candidate_for_rule_validation`.
8. Coverage diagnostics are generated.
9. 48/49 reports are generated.
10. Production 01/02/02A/06 are unchanged.
11. Production delivery remains PASS.
12. No factory_core/marker/surya/vision/PaddleOCR/model download occurred.
13. Output artifacts are not committed.

A WARN status is acceptable if safe extract coverage remains limited, provided evidence checks are strict and gaps are clearly explained.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_expand_stage1_ai_repair_extract_coverage.md

Worklog must be English only and UTF-8.

Worklog must include:
- task_title
- started_at
- finished_at
- git_commit_before
- git_commit_after
- commands_run
- files_read
- files_changed
- files_generated
- extract_coverage_status
- decision_counts
- extracted_candidate_count
- evidence_check_status
- production_delivery_status_after
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Allowed to commit:
- tools/run_stage1_ai_repair_worker.py if modified
- tools/build_stage1_ai_repair_extract_replay_set.py
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

Do not commit:
- output/delivery_package/48_stage1_ai_repair_extract_coverage_log.md
- output/delivery_package/48_stage1_ai_repair_extract_coverage_log.xlsx
- output/delivery_package/49_stage1_ai_repair_extract_coverage_evaluation.md
- output/delivery_package/49_stage1_ai_repair_extract_coverage_evaluation.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/run_stage1_ai_repair_worker.py tools/build_stage1_ai_repair_extract_replay_set.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "expand stage1 ai repair extract coverage"
git push origin main
```

If some listed files are unchanged, adjust git add accordingly.

## expected_final_response
After completion, output:
1. task_title
2. worker_path
3. extract_replay_helper_path
4. py_compile_status
5. extract_coverage_status
6. response_file_task_count
7. decision_counts
8. extracted_candidate_count
9. ai_candidate_for_rule_validation_count
10. evidence_check_status
11. invalid_extract_count
12. sample_extract_summary
13. target_metric_extract_summary
14. coverage_gap_summary
15. generated_outputs
16. production_delivery_status_after
17. production_files_unchanged
18. factory_core/vision/model_download_status
19. next_step_suggestion
20. commit sha

## safety_notes
- This task expands deterministic extract replay only.
- It must not call a real model.
- It must not write AI results into production delivery_package.
- It must not run factory_core.py.
- It must not trigger vision/OCR/model backends.
- It must not modify production delivery data.
