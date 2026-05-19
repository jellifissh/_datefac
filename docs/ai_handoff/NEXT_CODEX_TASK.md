# NEXT CODEX TASK

## task_title
Add Stage 1 AI repair guardrail replay tests

## project
D:\_datefac

## current_status
The Stage 1 AI repair offline file replay validation has completed and was committed.

Latest committed result:
- commit: ae261af add stage1 ai repair offline replay

Latest user-uploaded/reviewed outputs:
- D:\_datefac\output\delivery_package\42_stage1_ai_repair_offline_replay_log.md
- D:\_datefac\output\delivery_package\42_stage1_ai_repair_offline_replay_log.xlsx
- D:\_datefac\output\delivery_package\43_stage1_ai_repair_offline_replay_evaluation.md
- D:\_datefac\output\delivery_package\43_stage1_ai_repair_offline_replay_evaluation.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_offline_replay\ai_repair_results.jsonl
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_offline_replay\ai_repair_results.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_offline_replay\ai_repair_candidates.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_offline_replay\ai_repair_validation.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_offline_replay\ai_repair_merge_preview.xlsx

Key result from 42/43:
- task_title = Add Stage 1 AI repair offline file replay validation
- provider = offline_file
- processed_task_count = 77
- response_file_task_count = 2
- decision_counts = {manual_review: 76, ignore: 1}
- extracted_candidate_count = 0
- schema_validation_status = PASS
- extraction_value_evidence_check_status = PASS
- unknown_response_task_count = 0
- duplicate_response_task_count = 0
- missing_response_task_count = 75
- production_delivery_status_after = PASS / pass_count=17 / warn_count=0 / fail_count=0
- production_files_unchanged = true
- production_guard_changed_count = 0
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model download not triggered
- no real AI inference call was made

Interpretation:
The offline_file provider path is working, but it was only a small happy-path replay with two responses. Before connecting any real local/cloud provider, the worker needs a guardrail replay test suite that verifies schema errors, duplicate task ids, unknown task ids, missing fields, fabricated values, invalid years, and safe demotion behavior.

## goal
Add a sandbox-only AI repair guardrail replay test suite.

This task must create controlled offline response files representing valid and invalid model outputs, run the worker against them, and generate reports that prove invalid outputs are blocked or safely demoted.

Target code:
- D:\_datefac\tools\run_stage1_ai_repair_worker.py

Recommended new helper:
- D:\_datefac\tools\build_stage1_ai_repair_guardrail_cases.py

Target local reports:
- D:\_datefac\output\delivery_package\44_stage1_ai_repair_guardrail_tests_log.md
- D:\_datefac\output\delivery_package\44_stage1_ai_repair_guardrail_tests_log.xlsx
- D:\_datefac\output\delivery_package\45_stage1_ai_repair_guardrail_tests_evaluation.md
- D:\_datefac\output\delivery_package\45_stage1_ai_repair_guardrail_tests_evaluation.xlsx

Sandbox guardrail dir:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_guardrail_tests

Expected files under guardrail dir:
- guardrail_case_valid_manual_review.jsonl
- guardrail_case_valid_ignore.jsonl
- guardrail_case_valid_extract_if_possible.jsonl
- guardrail_case_unknown_task_id.jsonl
- guardrail_case_duplicate_task_id.jsonl
- guardrail_case_fabricated_value.jsonl
- guardrail_case_invalid_decision.jsonl
- guardrail_case_missing_required_fields.jsonl
- guardrail_case_malformed_json.jsonl
- per_case_results\<case_name>\ai_repair_results.jsonl
- per_case_results\<case_name>\ai_repair_validation.xlsx
- per_case_results\<case_name>\ai_repair_merge_preview.xlsx

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

### 1. Improve worker validation if needed
Ensure `run_stage1_ai_repair_worker.py` can clearly report these validation conditions:
- unknown_response_task_id
- duplicate_response_task_id
- missing_response_task_id
- malformed_json_line
- missing_required_fields
- invalid_decision
- value_not_in_evidence
- year_not_in_evidence
- metric_not_allowed_or_not_in_evidence
- schema_validation_failed

Invalid extracts must not become `ai_candidate_for_rule_validation`.
They must be blocked, demoted to manual_review_candidate, or cause case-level FAIL depending on severity.

### 2. Build controlled guardrail cases
Create helper `build_stage1_ai_repair_guardrail_cases.py` that reads:
- D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json

It should generate offline response JSONL cases under guardrail dir.

Case expectations:

1. `valid_manual_review`
- At least 2 known repair_task_id responses.
- decision = manual_review.
- Expected worker status: PASS or WARN only due missing responses.

2. `valid_ignore`
- At least 1 known repair_task_id.
- decision = ignore.
- Expected: PASS/WARN, route ignore.

3. `valid_extract_if_possible`
- Only create if exact value/year evidence can be deterministically found in a repair task.
- decision = extract with value copied exactly from evidence.
- If no safe extract can be built, generate a case file with metadata explaining skipped, and mark as SKIP in evaluation.

4. `unknown_task_id`
- Response references repair_task_id not in packet.
- Expected: validation FAIL for this case.

5. `duplicate_task_id`
- Same repair_task_id appears twice.
- Expected: validation FAIL for this case.

6. `fabricated_value`
- Response extracts a value not present in evidence.
- Expected: evidence check FAIL or extract demoted, and no ai_candidate_for_rule_validation.

7. `invalid_decision`
- decision outside extract/manual_review/ignore/non_target.
- Expected: validation FAIL.

8. `missing_required_fields`
- missing decision or repair_task_id or required arrays.
- Expected: validation FAIL.

9. `malformed_json`
- contains a syntactically invalid JSON line.
- Expected: validation FAIL.

### 3. Case runner
Either add a CLI option to the worker or implement case orchestration in the helper.

The task should run the worker against every generated case file using `--provider offline_file`.

Each case should capture:
- case_name
- case_path
- expected_status
- actual_status
- expected_failure_type
- actual_validation_flags
- processed_task_count
- response_file_task_count
- decision_counts
- schema_validation_status
- evidence_check_status
- extracted_candidate_count
- invalid_extract_candidate_count
- production_guard_changed_count

### 4. Reports 44/45
Generate:
- D:\_datefac\output\delivery_package\44_stage1_ai_repair_guardrail_tests_log.md
- D:\_datefac\output\delivery_package\44_stage1_ai_repair_guardrail_tests_log.xlsx

44 report must include:
- task_title
- started_at / finished_at
- commands_run
- packet_path
- schema_path
- guardrail_dir
- case_files_generated
- per_case_commands
- output_files_generated
- production_guard_changed_count
- safety_checks

Generate:
- D:\_datefac\output\delivery_package\45_stage1_ai_repair_guardrail_tests_evaluation.md
- D:\_datefac\output\delivery_package\45_stage1_ai_repair_guardrail_tests_evaluation.xlsx

45 report must include:
- guardrail_test_status: PASS / WARN / FAIL
- total_cases
- passed_cases
- failed_cases
- skipped_cases
- per_case_result_summary
- invalid_output_blocking_summary
- fabricated_value_blocking_status
- unknown_task_id_blocking_status
- duplicate_task_id_blocking_status
- malformed_json_blocking_status
- missing_required_fields_blocking_status
- invalid_decision_blocking_status
- production_delivery_status_after
- production_files_unchanged
- recommended_next_step

Excel sheets required:
- summary
- case_inventory
- per_case_results
- validation_flags
- invalid_output_blocking
- fabricated_value_tests
- production_guard
- safety_checks
- next_steps

## validation_commands
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\run_stage1_ai_repair_worker.py
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\build_stage1_ai_repair_guardrail_cases.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\build_stage1_ai_repair_guardrail_cases.py ^
  --packet-jsonl D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl ^
  --schema-json D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json ^
  --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 ^
  --delivery-dir D:\_datefac\output\delivery_package
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

If the helper invokes the worker internally for each case, do not separately run each worker command by hand unless needed for debugging.

## acceptance_criteria
This task passes if:
1. py_compile passes for worker and guardrail helper.
2. Guardrail case files are generated.
3. Worker is run against each relevant case using offline_file only.
4. Valid manual_review/ignore cases pass or warn only for missing responses.
5. Unknown task id is detected.
6. Duplicate task id is detected.
7. Fabricated value is detected and does not produce accepted candidate.
8. Invalid decision is detected.
9. Missing required fields are detected.
10. Malformed JSON is detected.
11. 44/45 reports are generated.
12. Production 01/02/02A/06 are unchanged.
13. Production delivery remains PASS.
14. No factory_core/marker/surya/vision/PaddleOCR/model download occurred.
15. Output artifacts are not committed.

A WARN status is acceptable if valid_extract_if_possible is skipped because no deterministic safe extract could be constructed.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_add_stage1_ai_repair_guardrail_tests.md

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
- guardrail_test_status
- per_case_result_summary
- validation_status_summary
- production_delivery_status_after
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Allowed to commit:
- tools/run_stage1_ai_repair_worker.py
- tools/build_stage1_ai_repair_guardrail_cases.py
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

Do not commit:
- output/delivery_package/44_stage1_ai_repair_guardrail_tests_log.md
- output/delivery_package/44_stage1_ai_repair_guardrail_tests_log.xlsx
- output/delivery_package/45_stage1_ai_repair_guardrail_tests_evaluation.md
- output/delivery_package/45_stage1_ai_repair_guardrail_tests_evaluation.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/run_stage1_ai_repair_worker.py tools/build_stage1_ai_repair_guardrail_cases.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "add stage1 ai repair guardrail replay tests"
git push origin main
```

## expected_final_response
After completion, output:
1. task_title
2. worker_path
3. guardrail_helper_path
4. py_compile_status
5. guardrail_test_status
6. total_cases / passed_cases / failed_cases / skipped_cases
7. per_case_result_summary
8. fabricated_value_blocking_status
9. unknown_task_id_blocking_status
10. duplicate_task_id_blocking_status
11. malformed_json_blocking_status
12. missing_required_fields_blocking_status
13. invalid_decision_blocking_status
14. generated_outputs
15. production_delivery_status_after
16. production_files_unchanged
17. factory_core/vision/model_download_status
18. next_step_suggestion
19. commit sha

## safety_notes
- This task validates guardrails only.
- It must not call a real model.
- It must not write AI results into production delivery_package.
- It must not run factory_core.py.
- It must not trigger vision/OCR/model backends.
- It must not modify production delivery data.
