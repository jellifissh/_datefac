# NEXT CODEX TASK

## task_title
Prepare Stage 1 real-provider micro test harness

## project
D:\_datefac

## current_status
The Stage 1 AI repair provider dry-run controller has completed or is considered ready enough for the next planning step.

Context:
The project has already built the Stage 1 AI repair safety chain:
- AI repair packet and schema
- offline_mock worker
- offline_file replay
- guardrail replay tests
- deterministic extract replay
- provider preflight bundle
- provider response intake gate
- provider dry-run controller

The next useful step is not more infrastructure. The next step is to prepare a very small real-provider micro test harness so the user can manually test a local/cloud model later and then feed the raw response back through the existing intake/replay/evaluation pipeline.

This task must only prepare the test harness. It must not call any model.

## goal
Prepare a sandbox-only real-provider micro test harness for Stage 1 AI repair.

The harness should:
1. select 5 to 10 representative requests from the existing provider request batch;
2. prefer row_segment_repair and metric_year_value_alignment tasks;
3. avoid semantic_guard_review in the first micro test unless needed as a low-priority example;
4. generate a compact JSONL request batch for manual model testing;
5. generate a prompt file that the user can paste into a local/cloud model;
6. generate a raw response template JSONL for the model output;
7. generate manual local-model test instructions;
8. generate intake/replay/evaluation command templates for after the user saves model outputs;
9. produce 56/57 local reports;
10. avoid production writes.

Target new helper:
- D:\_datefac\tools\prepare_stage1_real_provider_micro_test_harness.py

Target local reports:
- D:\_datefac\output\delivery_package\56_stage1_real_provider_micro_test_harness_log.md
- D:\_datefac\output\delivery_package\56_stage1_real_provider_micro_test_harness_log.xlsx
- D:\_datefac\output\delivery_package\57_stage1_real_provider_micro_test_harness_plan.md
- D:\_datefac\output\delivery_package\57_stage1_real_provider_micro_test_harness_plan.xlsx

Sandbox micro test dir:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_micro_test

Expected sandbox files:
- micro_test_request_batch.jsonl
- micro_test_request_batch.xlsx
- micro_test_prompt.md
- local_model_response_template.jsonl
- local_model_response_raw_PLACEHOLDER.jsonl
- run_local_model_manual_steps.md
- micro_test_intake_replay_commands.md
- micro_test_selection_diagnostics.xlsx

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

## input_sources
Read existing files only:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_preflight\provider_request_batch.jsonl
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_preflight\provider_config_template.json
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema_and_prompt.md
- D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl

If provider_request_batch.jsonl is missing, stop with BLOCKED_MISSING_PROVIDER_REQUEST_BATCH and explain.

## selection_rules
Select 5 to 10 requests.

Priority:
1. row_segment_repair, especially rows with multiple metric blocks and clear evidence.
2. metric_year_value_alignment, especially rows with explicit detected years and values.
3. S2 table-level repair may include 1 item only if needed for sample coverage.
4. semantic_guard_review should be excluded from the first micro test unless there are not enough other tasks.

Selection should include where possible:
- at least 2 S1 tasks;
- at least 1 S3 task;
- at most 1 S2 task;
- at least 1 row_segment_repair;
- at least 1 metric_year_value_alignment if available.

Do not fabricate tasks. If eligible tasks are fewer than 5, report WARN_INSUFFICIENT_ELIGIBLE_TASKS.

## prompt_requirements
Generate `micro_test_prompt.md` for manual use.

It must include:
- role: strict financial table repair worker;
- return JSONL only;
- one output JSON object per input request;
- output must conform to 38 schema;
- do not invent values;
- copy numbers from evidence only;
- if ambiguous, choose manual_review;
- preserve repair_task_id;
- preserve year labels unless explicitly flagged `year_normalized`;
- no markdown in model output;
- no explanations outside JSON.

Also include a compact section explaining how the user should paste 5 to 10 requests into the model and save the output to:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_micro_test\local_model_response_raw.jsonl

## response_template_requirements
Generate `local_model_response_template.jsonl` with one placeholder response per selected request.

Each placeholder should be valid JSON and default to:
- decision = manual_review
- repairs = []
- manual_review_items includes a placeholder reason
- notes = "Replace this placeholder with actual model output or keep manual_review if ambiguous."

Also generate `local_model_response_raw_PLACEHOLDER.jsonl` with comments avoided because JSONL does not allow comments.

## intake/replay command templates
Generate `micro_test_intake_replay_commands.md` with commands for after the user manually creates local_model_response_raw.jsonl.

The commands should route the raw response through:
1. intake_stage1_ai_repair_provider_responses.py
2. run_stage1_ai_repair_worker.py provider offline_file if needed or via intake --run-offline-replay
3. check_delivery_state.py --json

Must clearly state:
- Do not write output directly to production 06.
- Raw model output must go through intake gate first.
- Clean responses only can be replayed.

## reports
Generate:
- D:\_datefac\output\delivery_package\56_stage1_real_provider_micro_test_harness_log.md
- D:\_datefac\output\delivery_package\56_stage1_real_provider_micro_test_harness_log.xlsx

56 report must include:
- task_title
- started_at / finished_at
- commands_run
- provider_request_batch_path
- selected_request_count
- selected_sample_counts
- selected_task_type_counts
- output_files_generated
- no_secret_check_status
- production_guard_changed_count
- safety_checks

Generate:
- D:\_datefac\output\delivery_package\57_stage1_real_provider_micro_test_harness_plan.md
- D:\_datefac\output\delivery_package\57_stage1_real_provider_micro_test_harness_plan.xlsx

57 report must include:
- micro_test_harness_status: PASS / WARN / FAIL
- selected_request_count
- selected_sample_counts
- selected_task_type_counts
- selected_priority_counts
- excluded_task_summary
- manual_test_steps_summary
- expected_user_action
- intake_replay_plan_status
- no_secret_check_status
- production_delivery_status_after
- production_files_unchanged
- recommended_next_step

Excel sheets required:
- summary
- selected_requests
- excluded_requests
- sample_counts
- task_type_counts
- priority_counts
- output_files
- no_secret_check
- production_guard
- safety_checks
- next_steps

## validation_commands
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\prepare_stage1_real_provider_micro_test_harness.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\prepare_stage1_real_provider_micro_test_harness.py ^
  --request-batch D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_preflight\provider_request_batch.jsonl ^
  --schema-json D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json ^
  --prompt-md D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema_and_prompt.md ^
  --packet-jsonl D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl ^
  --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --min-requests 5 ^
  --max-requests 10
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

## acceptance_criteria
This task passes if:
1. py_compile passes.
2. Micro test request batch is generated.
3. Selected request count is between 5 and 10 unless insufficient eligible tasks are documented.
4. row_segment_repair is included if available.
5. metric_year_value_alignment is included if available.
6. S1 and S3 are represented if possible.
7. Prompt and response template are generated.
8. Intake/replay command template is generated.
9. No real model/API/network call occurs.
10. No secrets are written.
11. 56/57 reports are generated.
12. Production 01/02/02A/06 are unchanged.
13. Production delivery remains PASS.
14. No factory_core/marker/surya/vision/PaddleOCR/model download occurred.
15. Output artifacts are not committed.

A WARN status is acceptable if eligible task diversity is limited, provided this is documented.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_prepare_stage1_real_provider_micro_test_harness.md

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
- micro_test_harness_status
- selected_request_count
- no_secret_check_status
- production_delivery_status_after
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Allowed to commit:
- tools/prepare_stage1_real_provider_micro_test_harness.py
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

Do not commit:
- output/delivery_package/56_stage1_real_provider_micro_test_harness_log.md
- output/delivery_package/56_stage1_real_provider_micro_test_harness_log.xlsx
- output/delivery_package/57_stage1_real_provider_micro_test_harness_plan.md
- output/delivery_package/57_stage1_real_provider_micro_test_harness_plan.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/prepare_stage1_real_provider_micro_test_harness.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "prepare stage1 real provider micro test harness"
git push origin main
```

## expected_final_response
After completion, output:
1. task_title
2. helper_path
3. py_compile_status
4. micro_test_harness_status
5. selected_request_count
6. selected_sample_counts
7. selected_task_type_counts
8. generated_outputs
9. no_secret_check_status
10. production_delivery_status_after
11. production_files_unchanged
12. factory_core/vision/model_download_status
13. next_step_suggestion
14. commit sha

## safety_notes
- This task prepares a micro test harness only.
- It must not call a real model.
- It must not write AI results into production delivery_package.
- It must not run factory_core.py.
- It must not trigger vision/OCR/model backends.
- It must not modify production delivery data.
