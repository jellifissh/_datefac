# NEXT CODEX TASK

## task_title
Add Stage 1 AI repair offline file replay validation

## project
D:\_datefac

## current_status
The Stage 1 sandbox AI repair worker MVP has completed and was committed.

Latest committed result:
- commit: 1314fad implement stage1 ai repair worker mvp

Latest user-uploaded/reviewed outputs:
- D:\_datefac\output\delivery_package\40_stage1_ai_repair_worker_log.md
- D:\_datefac\output\delivery_package\40_stage1_ai_repair_worker_log.xlsx
- D:\_datefac\output\delivery_package\41_stage1_ai_repair_worker_evaluation.md
- D:\_datefac\output\delivery_package\41_stage1_ai_repair_worker_evaluation.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_trial\ai_repair_results.jsonl
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_trial\ai_repair_results.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_trial\ai_repair_candidates.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_trial\ai_repair_validation.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_trial\ai_repair_merge_preview.xlsx

Key result from 40/41:
- task_title = Implement Stage 1 sandbox AI repair worker MVP
- provider = offline_mock
- processed_task_count = 77
- decision_counts = {manual_review: 77}
- extracted_candidate_count = 0
- manual_review_count = 77
- schema_validation_status = PASS
- extraction_value_evidence_check_status = PASS
- production_delivery_status_after = PASS / pass_count=17 / warn_count=0 / fail_count=0
- production_files_unchanged = true
- production_guard_changed_count = 0
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model download not triggered
- no real AI inference call was made

Interpretation:
The AI repair worker harness is working safely, but offline_mock intentionally returns conservative manual_review for all tasks. The next step is to validate the `offline_file` provider path with a small local replay file that simulates model outputs. This still must not call any model or network. It should prove that future real-model outputs can be parsed, schema-validated, evidence-checked, and merged into sandbox candidate previews.

## goal
Add and validate offline file replay support for Stage 1 AI repair worker.

This task must not call any real AI model. It should generate a small local offline response JSONL from the existing repair packet and then run the worker with `--provider offline_file`.

Target code:
- D:\_datefac\tools\run_stage1_ai_repair_worker.py

Optional helper if useful:
- D:\_datefac\tools\build_stage1_ai_repair_offline_responses.py

Target local reports:
- D:\_datefac\output\delivery_package\42_stage1_ai_repair_offline_replay_log.md
- D:\_datefac\output\delivery_package\42_stage1_ai_repair_offline_replay_log.xlsx
- D:\_datefac\output\delivery_package\43_stage1_ai_repair_offline_replay_evaluation.md
- D:\_datefac\output\delivery_package\43_stage1_ai_repair_offline_replay_evaluation.xlsx

Sandbox AI repair replay dir:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_offline_replay

Expected sandbox files:
- offline_model_responses_sample.jsonl
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

### 1. offline_file provider
Ensure `run_stage1_ai_repair_worker.py` supports:
- `--provider offline_file`
- `--offline-response-jsonl <path>`

Rules:
- offline_file reads one JSON object per line.
- Each response must include repair_task_id.
- Responses must be schema-compliant with `38_stage1_ai_repair_schema.json`.
- If a task is missing in offline response file, default to safe manual_review with flag `offline_response_missing`.
- If duplicate repair_task_id exists in response file, mark validation FAIL.
- If response references an unknown repair_task_id, mark validation FAIL.
- If response contains extraction values not present in evidence, mark validation FAIL or demote to manual_review with flag `value_not_in_evidence`, but do not accept as candidate.

### 2. Build a safe sample offline response file
Create a local sample response JSONL under replay dir:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_offline_replay\offline_model_responses_sample.jsonl

It should include a small subset of tasks, not necessarily all 77.

Suggested content:
- At least 1 manual_review response for S2 table-level repair.
- At least 1 ignore response for a clearly unsafe semantic_guard_review row if present.
- At least 1 extract response only if a repair task has clear evidence and the values copied exactly from evidence.
- If no safe extract can be constructed deterministically from packet evidence, do not fake it. Use manual_review only and document why.

The goal is provider/replay validation, not high extraction count.

### 3. Evidence checking
Strengthen evidence checking:
- For every extracted repair value, verify exact string or normalized numeric form appears in evidence row_cells / row_preview / nearby_rows_context / raw_table_preview.
- If a year is output, verify year appears in detected_years or evidence text.
- If standard_metric is output, verify it is in allowed target metric list or appears in evidence.
- Store evidence_check_status per repair.

### 4. Merge preview behavior
For valid extract results:
- recommended_route_after_ai = ai_candidate_for_rule_validation.

For invalid extract results:
- recommended_route_after_ai = manual_review_candidate.
- add validation flag.

For manual_review:
- recommended_route_after_ai = manual_review_candidate.

For ignore/non_target:
- route accordingly.

Do not write any result into production 01/02/06.

## report_requirements
Generate:
- D:\_datefac\output\delivery_package\42_stage1_ai_repair_offline_replay_log.md
- D:\_datefac\output\delivery_package\42_stage1_ai_repair_offline_replay_log.xlsx

42 report must include:
- task_title
- started_at / finished_at
- command_run
- provider
- packet_path
- schema_path
- offline_response_path
- processed_task_count
- response_file_task_count
- decision_counts
- validation_status
- evidence_check_status
- output_files_generated
- production_guard_changed_count
- safety_checks

Generate:
- D:\_datefac\output\delivery_package\43_stage1_ai_repair_offline_replay_evaluation.md
- D:\_datefac\output\delivery_package\43_stage1_ai_repair_offline_replay_evaluation.xlsx

43 report must include:
- ai_repair_worker_status: PASS / WARN / FAIL
- provider = offline_file
- task_count
- response_file_task_count
- decision_counts
- extracted_candidate_count
- manual_review_count
- ignored_count
- non_target_count
- schema_validation_status
- extraction_value_evidence_check_status
- unknown_response_task_count
- duplicate_response_task_count
- missing_response_task_count
- sample_decision_summary
- task_type_decision_summary
- merge_preview_summary
- production_delivery_status_after
- production_files_unchanged
- recommended_next_step

Excel sheets required:
- summary
- decision_summary
- task_results
- extracted_candidates
- manual_review_items
- schema_validation
- evidence_check
- offline_response_validation
- merge_preview
- production_guard
- safety_checks
- next_steps

## validation_commands
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\run_stage1_ai_repair_worker.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_ai_repair_worker.py --help
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_ai_repair_worker.py ^
  --packet-jsonl D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl ^
  --schema-json D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json ^
  --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --provider offline_file ^
  --offline-response-jsonl D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_offline_replay\offline_model_responses_sample.jsonl ^
  --max-tasks 80 ^
  --strict-schema
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

If optional helper is created, also py_compile it.

## acceptance_criteria
This task passes if:
1. py_compile passes.
2. --help passes.
3. offline_file provider runs without real AI/network/model call.
4. sample offline response JSONL is created.
5. worker processes all 77 tasks or documented max-task count.
6. missing responses are safely handled.
7. schema validation passes.
8. evidence checking passes for accepted extracted candidates, or invalid extracts are demoted.
9. 42/43 reports are generated.
10. sandbox offline replay output files are generated.
11. production 01/02/02A/06 are unchanged.
12. production delivery remains PASS.
13. no factory_core/marker/surya/vision/PaddleOCR/model download occurred.
14. output artifacts are not committed.

A WARN status is acceptable if most tasks are manual_review or if no safe extract sample can be created, provided validation is honest.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_add_stage1_ai_repair_offline_replay.md

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
- provider
- decision_counts
- validation_status
- evidence_check_status
- production_delivery_status_after
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Allowed to commit:
- tools/run_stage1_ai_repair_worker.py
- optional helper if created
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

Do not commit:
- output/delivery_package/42_stage1_ai_repair_offline_replay_log.md
- output/delivery_package/42_stage1_ai_repair_offline_replay_log.xlsx
- output/delivery_package/43_stage1_ai_repair_offline_replay_evaluation.md
- output/delivery_package/43_stage1_ai_repair_offline_replay_evaluation.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/run_stage1_ai_repair_worker.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "add stage1 ai repair offline replay"
git push origin main
```

## expected_final_response
After completion, output:
1. task_title
2. worker_path
3. py_compile_status
4. help_status
5. ai_repair_worker_status
6. provider
7. offline_response_path
8. processed_task_count
9. response_file_task_count
10. decision_counts
11. schema_validation_status
12. evidence_check_status
13. generated_outputs
14. production_delivery_status_after
15. production_files_unchanged
16. factory_core/vision/model_download_status
17. next_step_suggestion
18. commit sha

## safety_notes
- This task validates offline_file replay only.
- It must not call a real model yet.
- It must not write AI results into production delivery_package.
- It must not run factory_core.py.
- It must not trigger vision/OCR/model backends.
- It must not modify production delivery data.
