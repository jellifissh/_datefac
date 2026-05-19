# NEXT CODEX TASK

## task_title
Add Stage 1 AI repair deterministic extract replay set

## project
D:\_datefac

## current_status
The Stage 1 AI repair guardrail replay tests have completed successfully.

Latest user-uploaded/reviewed outputs:
- D:\_datefac\output\delivery_package\44_stage1_ai_repair_guardrail_tests_log.md
- D:\_datefac\output\delivery_package\44_stage1_ai_repair_guardrail_tests_log.xlsx
- D:\_datefac\output\delivery_package\45_stage1_ai_repair_guardrail_tests_evaluation.md
- D:\_datefac\output\delivery_package\45_stage1_ai_repair_guardrail_tests_evaluation.xlsx

Key result from 44/45:
- task_title = Add Stage 1 AI repair guardrail replay tests
- guardrail_test_status = PASS
- total_cases = 9
- passed_cases = 9
- failed_cases = 0
- skipped_cases = 0
- fabricated_value_blocking_status = PASS
- unknown_task_id_blocking_status = PASS
- duplicate_task_id_blocking_status = PASS
- malformed_json_blocking_status = PASS
- missing_required_fields_blocking_status = PASS
- invalid_decision_blocking_status = PASS
- production_delivery_status_after = PASS / pass_count=17 / warn_count=0 / fail_count=0
- production_files_unchanged = true
- production_guard_changed_count = 0
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model download not triggered
- no real AI inference call was made

Interpretation:
The worker guardrails now block invalid or unsafe AI outputs. Before connecting a real provider, we need a larger deterministic extract replay set that proves the happy extract path works: valid evidence-based extract responses should pass schema/evidence checks, enter `ai_candidate_for_rule_validation`, and appear in merge preview without touching production data.

## goal
Build and validate a larger deterministic offline extract replay set for Stage 1 AI repair.

This task must remain sandbox-only and offline-only. It must not call a real model.

Target code:
- D:\_datefac\tools\run_stage1_ai_repair_worker.py
- D:\_datefac\tools\build_stage1_ai_repair_guardrail_cases.py

You may add a new helper if cleaner:
- D:\_datefac\tools\build_stage1_ai_repair_extract_replay_set.py

Target local reports:
- D:\_datefac\output\delivery_package\46_stage1_ai_repair_extract_replay_log.md
- D:\_datefac\output\delivery_package\46_stage1_ai_repair_extract_replay_log.xlsx
- D:\_datefac\output\delivery_package\47_stage1_ai_repair_extract_replay_evaluation.md
- D:\_datefac\output\delivery_package\47_stage1_ai_repair_extract_replay_evaluation.xlsx

Sandbox extract replay dir:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_replay

Expected sandbox files:
- extract_replay_responses.jsonl
- ai_repair_results.jsonl
- ai_repair_results.xlsx
- ai_repair_candidates.xlsx
- ai_repair_validation.xlsx
- ai_repair_merge_preview.xlsx

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

### 1. Construct deterministic extract responses from packet evidence only
Read:
- D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json

Build 3 to 8 valid extract responses if possible.

Rules:
- Every extracted value must be copied from evidence exactly or in normalized numeric form.
- Every extracted year must appear in detected_years or evidence text.
- Every standard_metric must be in the target metric list or clearly present in evidence.
- Prefer tasks with task_type:
  - row_segment_repair
  - metric_year_value_alignment
- If not enough safe row-level extract tasks exist, use only those that are deterministic and document shortage.
- Do not fabricate values just to reach target count.

### 2. Include mixed decision replay
The replay file should include:
- valid extract responses, if deterministic evidence allows;
- manual_review responses for ambiguous cases;
- ignore responses for clearly unsafe semantic guard cases, if present.

Goal:
- at least 1 extract candidate if possible;
- at least 1 manual_review;
- at least 1 ignore;
- no invalid response should be included in this replay set.

### 3. Worker evidence and merge behavior
Run worker with provider `offline_file` and the generated `extract_replay_responses.jsonl`.

Expected behavior:
- valid extracts pass schema validation;
- valid extracts pass evidence check;
- valid extracts route to `ai_candidate_for_rule_validation` in merge preview;
- manual_review routes to `manual_review_candidate`;
- ignore routes to `ignore`;
- missing responses safely default to manual_review with `offline_response_missing` or equivalent flag;
- production files remain unchanged.

### 4. Reports 46/47
Generate:
- D:\_datefac\output\delivery_package\46_stage1_ai_repair_extract_replay_log.md
- D:\_datefac\output\delivery_package\46_stage1_ai_repair_extract_replay_log.xlsx

46 report must include:
- task_title
- started_at / finished_at
- commands_run
- packet_path
- schema_path
- extract_replay_dir
- response_file_path
- response_file_task_count
- extract_response_count
- manual_review_response_count
- ignore_response_count
- output_files_generated
- production_guard_changed_count
- safety_checks

Generate:
- D:\_datefac\output\delivery_package\47_stage1_ai_repair_extract_replay_evaluation.md
- D:\_datefac\output\delivery_package\47_stage1_ai_repair_extract_replay_evaluation.xlsx

47 report must include:
- extract_replay_status: PASS / WARN / FAIL
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
- production_guard
- safety_checks
- next_steps

## validation_commands
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\run_stage1_ai_repair_worker.py
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\build_stage1_ai_repair_guardrail_cases.py
```

If a new helper is created:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\build_stage1_ai_repair_extract_replay_set.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\build_stage1_ai_repair_extract_replay_set.py ^
  --packet-jsonl D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl ^
  --schema-json D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json ^
  --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --max-extracts 8
```

If the existing guardrail helper is extended instead, run that helper with an explicit extract replay mode.

At end run:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

## acceptance_criteria
This task passes if:
1. py_compile passes for all changed helpers.
2. Extract replay response JSONL is generated.
3. Worker runs offline_file with the extract replay JSONL.
4. At least one safe extract candidate is accepted if deterministic evidence exists.
5. If no safe extract can be built, status is WARN with exact reason, not fake PASS.
6. Every accepted extract value passes evidence check.
7. No invalid extract becomes `ai_candidate_for_rule_validation`.
8. Merge preview contains valid route counts.
9. 46/47 reports are generated.
10. Production 01/02/02A/06 are unchanged.
11. Production delivery remains PASS.
12. No factory_core/marker/surya/vision/PaddleOCR/model download occurred.
13. Output artifacts are not committed.

A WARN status is acceptable if safe extract coverage is limited, provided evidence checks are strict.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_add_stage1_ai_repair_extract_replay.md

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
- extract_replay_status
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
- tools/build_stage1_ai_repair_guardrail_cases.py if modified
- tools/build_stage1_ai_repair_extract_replay_set.py if created
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

Do not commit:
- output/delivery_package/46_stage1_ai_repair_extract_replay_log.md
- output/delivery_package/46_stage1_ai_repair_extract_replay_log.xlsx
- output/delivery_package/47_stage1_ai_repair_extract_replay_evaluation.md
- output/delivery_package/47_stage1_ai_repair_extract_replay_evaluation.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/run_stage1_ai_repair_worker.py tools/build_stage1_ai_repair_guardrail_cases.py tools/build_stage1_ai_repair_extract_replay_set.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "add stage1 ai repair extract replay set"
git push origin main
```

If some listed files are unchanged or missing, adjust git add accordingly.

## expected_final_response
After completion, output:
1. task_title
2. worker_path
3. extract_replay_helper_path
4. py_compile_status
5. extract_replay_status
6. response_file_task_count
7. decision_counts
8. extracted_candidate_count
9. ai_candidate_for_rule_validation_count
10. evidence_check_status
11. invalid_extract_count
12. generated_outputs
13. production_delivery_status_after
14. production_files_unchanged
15. factory_core/vision/model_download_status
16. next_step_suggestion
17. commit sha

## safety_notes
- This task validates deterministic extract replay only.
- It must not call a real model.
- It must not write AI results into production delivery_package.
- It must not run factory_core.py.
- It must not trigger vision/OCR/model backends.
- It must not modify production delivery data.
