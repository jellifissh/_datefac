# NEXT CODEX TASK

## task_title
Add Stage 1 AI repair provider response intake gate

## project
D:\_datefac

## current_status
The Stage 1 AI repair real-provider preflight bundle has completed.

Latest committed result:
- commit: 2244dd0 prepare stage1 ai repair provider preflight

Latest user-uploaded/reviewed output summary:
- task_title = Prepare Stage 1 AI repair real-provider preflight bundle
- provider_preflight_status = PASS
- provider_request_count = 20
- selected_sample_counts = {S1: 12, S2: 5, S3: 3}
- selected_task_type_counts = {row_segment_repair: 5, metric_year_value_alignment: 2, s2_table_level_repair: 5, semantic_guard_review: 8}
- priority_counts = {P0: 7, P1: 5, P2: 8}
- no_secret_check_status = PASS
- production_delivery_status_after = PASS / pass_count=17 / warn_count=0 / fail_count=0
- production_files_unchanged = true
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model download not triggered
- no real AI inference call was made

Interpretation:
The first real-provider request bundle is ready, but no model should be called from the pipeline yet. Before any future manual/controlled real-provider run, we need an intake gate that validates a provider response JSONL against the request batch, schema, evidence, and safety rules, then writes a quarantined offline_file-ready response set.

## goal
Add a sandbox-only provider response intake gate.

The intake gate must validate and normalize a future real-provider response file before it is passed to the existing offline_file worker path.

This task must not call any real model or network. It only creates validation/import tooling and runs it against synthetic local response files.

Target new helper:
- D:\_datefac\tools\intake_stage1_ai_repair_provider_responses.py

Target code may also update if needed:
- D:\_datefac\tools\run_stage1_ai_repair_worker.py

Target local reports:
- D:\_datefac\output\delivery_package\52_stage1_ai_repair_provider_intake_log.md
- D:\_datefac\output\delivery_package\52_stage1_ai_repair_provider_intake_log.xlsx
- D:\_datefac\output\delivery_package\53_stage1_ai_repair_provider_intake_evaluation.md
- D:\_datefac\output\delivery_package\53_stage1_ai_repair_provider_intake_evaluation.xlsx

Sandbox intake dir:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_intake

Expected sandbox files:
- provider_response_synthetic_raw.jsonl
- provider_response_intake_clean.jsonl
- provider_response_intake_rejected.jsonl
- provider_response_intake_validation.xlsx
- provider_response_intake_summary.xlsx
- offline_file_replay_after_intake\ai_repair_results.jsonl
- offline_file_replay_after_intake\ai_repair_results.xlsx
- offline_file_replay_after_intake\ai_repair_candidates.xlsx
- offline_file_replay_after_intake\ai_repair_validation.xlsx
- offline_file_replay_after_intake\ai_repair_merge_preview.xlsx

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
15. Do not put any API key, token, password, endpoint secret, or credential in any file.

## implementation_requirements

### 1. Intake helper CLI
Implement:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\intake_stage1_ai_repair_provider_responses.py ^
  --request-batch D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_preflight\provider_request_batch.jsonl ^
  --schema-json D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json ^
  --packet-jsonl D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl ^
  --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --raw-provider-response D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_intake\provider_response_synthetic_raw.jsonl ^
  --run-offline-replay
```

### 2. Synthetic raw response file
Create a synthetic provider raw response JSONL for testing under intake dir.

Include mixed cases:
- valid manual_review response;
- valid ignore response;
- valid extract response with evidence-backed value if possible;
- response with unknown request_id or repair_task_id;
- response with duplicated repair_task_id;
- response with fabricated value;
- response with malformed JSON;
- response with missing decision;
- response with extra wrapper fields that must be normalized if safe.

### 3. Intake validation rules
Validate against:
- provider_request_batch.jsonl request_id and repair_task_id;
- 38_stage1_ai_repair_schema.json;
- original packet evidence from 37 JSONL.

Checks required:
- request_id known;
- repair_task_id known and matches request mapping;
- no duplicate repair_task_id accepted;
- JSON parses;
- decision valid;
- required schema fields present;
- extracted values appear in evidence;
- extracted years appear in evidence or detected_years;
- no obvious secret strings in raw or clean responses;
- Chinese text not garbled.

### 4. Clean and reject outputs
Write:
- `provider_response_intake_clean.jsonl` for accepted/normalized responses only;
- `provider_response_intake_rejected.jsonl` for rejected responses with rejection reasons.

Clean output must be compatible with `run_stage1_ai_repair_worker.py --provider offline_file`.

Rejected outputs must not be replayed.

### 5. Offline replay after intake
If `--run-offline-replay` is set:
- Run existing worker with provider offline_file using `provider_response_intake_clean.jsonl`.
- Write results under `offline_file_replay_after_intake`.
- This proves the intake output can flow through existing schema/evidence/merge preview path.

### 6. Reports 52/53
Generate:
- D:\_datefac\output\delivery_package\52_stage1_ai_repair_provider_intake_log.md
- D:\_datefac\output\delivery_package\52_stage1_ai_repair_provider_intake_log.xlsx

52 report must include:
- task_title
- started_at / finished_at
- commands_run
- request_batch_path
- raw_provider_response_path
- clean_response_path
- rejected_response_path
- raw_response_count
- clean_response_count
- rejected_response_count
- offline_replay_status
- output_files_generated
- production_guard_changed_count
- safety_checks

Generate:
- D:\_datefac\output\delivery_package\53_stage1_ai_repair_provider_intake_evaluation.md
- D:\_datefac\output\delivery_package\53_stage1_ai_repair_provider_intake_evaluation.xlsx

53 report must include:
- provider_intake_status: PASS / WARN / FAIL
- raw_response_count
- clean_response_count
- rejected_response_count
- rejection_reason_summary
- valid_extract_count
- accepted_manual_review_count
- accepted_ignore_count
- unknown_request_blocking_status
- duplicate_response_blocking_status
- fabricated_value_blocking_status
- malformed_json_blocking_status
- missing_required_fields_blocking_status
- wrapper_normalization_status
- offline_replay_status
- offline_replay_merge_preview_summary
- no_secret_check_status
- production_delivery_status_after
- production_files_unchanged
- recommended_next_step

Excel sheets required:
- summary
- raw_response_inventory
- clean_responses
- rejected_responses
- rejection_reason_summary
- evidence_check
- offline_replay_summary
- offline_replay_merge_preview
- no_secret_check
- production_guard
- safety_checks
- next_steps

## validation_commands
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\intake_stage1_ai_repair_provider_responses.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\intake_stage1_ai_repair_provider_responses.py ^
  --request-batch D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_preflight\provider_request_batch.jsonl ^
  --schema-json D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json ^
  --packet-jsonl D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl ^
  --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --raw-provider-response D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_intake\provider_response_synthetic_raw.jsonl ^
  --run-offline-replay
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

If worker is modified, also py_compile it.

## acceptance_criteria
This task passes if:
1. py_compile passes.
2. Intake helper generates synthetic raw response file.
3. Clean/rejected response JSONL files are generated.
4. Unknown request/task responses are rejected.
5. Duplicate responses are rejected.
6. Fabricated values are rejected or demoted and never accepted as clean extract.
7. Malformed JSON is rejected.
8. Missing required fields are rejected.
9. Safe wrapper normalization is handled if included.
10. Clean responses replay through offline_file successfully.
11. 52/53 reports are generated.
12. No secrets are written.
13. Production 01/02/02A/06 are unchanged.
14. Production delivery remains PASS.
15. No factory_core/marker/surya/vision/PaddleOCR/model download occurred.
16. Output artifacts are not committed.

A WARN status is acceptable if no clean extract is accepted, provided invalid responses are blocked and clean manual_review/ignore replay works.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_add_stage1_ai_repair_provider_intake_gate.md

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
- provider_intake_status
- clean_response_count
- rejected_response_count
- offline_replay_status
- production_delivery_status_after
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Allowed to commit:
- tools/intake_stage1_ai_repair_provider_responses.py
- tools/run_stage1_ai_repair_worker.py if modified
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

Do not commit:
- output/delivery_package/52_stage1_ai_repair_provider_intake_log.md
- output/delivery_package/52_stage1_ai_repair_provider_intake_log.xlsx
- output/delivery_package/53_stage1_ai_repair_provider_intake_evaluation.md
- output/delivery_package/53_stage1_ai_repair_provider_intake_evaluation.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/intake_stage1_ai_repair_provider_responses.py tools/run_stage1_ai_repair_worker.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "add stage1 ai repair provider response intake gate"
git push origin main
```

If worker was not modified, omit it from git add.

## expected_final_response
After completion, output:
1. task_title
2. intake_helper_path
3. py_compile_status
4. provider_intake_status
5. raw_response_count
6. clean_response_count
7. rejected_response_count
8. rejection_reason_summary
9. offline_replay_status
10. no_secret_check_status
11. generated_outputs
12. production_delivery_status_after
13. production_files_unchanged
14. factory_core/vision/model_download_status
15. next_step_suggestion
16. commit sha

## safety_notes
- This task creates a provider response intake gate only.
- It must not call a real model.
- It must not write AI results into production delivery_package.
- It must not run factory_core.py.
- It must not trigger vision/OCR/model backends.
- It must not modify production delivery data.
