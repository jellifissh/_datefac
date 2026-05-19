# NEXT CODEX TASK

## task_title
Add Stage 1 AI repair provider dry-run controller

## project
D:\_datefac

## current_status
The Stage 1 AI repair provider response intake gate has completed.

Latest committed result:
- commit: 857ed06 add stage1 ai repair provider response intake gate

Latest user-uploaded/reviewed output summary:
- task_title = Add Stage 1 AI repair provider response intake gate
- provider_intake_status = PASS
- raw_response_count = 9
- clean_response_count = 3
- rejected_response_count = 6
- offline_replay_status = PASS
- no_secret_check_status = PASS
- rejection_reason_summary includes:
  - unknown_request / unknown repair task
  - duplicate repair task
  - fabricated value / value not in evidence
  - missing required field: decision
  - malformed JSON
- production_delivery_status_after = PASS / pass_count=17 / warn_count=0 / fail_count=0
- production_files_unchanged = true
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model download not triggered
- no real AI inference call was made

Interpretation:
The request bundle, response contract, intake gate, offline replay, schema validation, evidence checking, and production isolation are now in place. Before a future real model run, add a dry-run controller that prepares execution batches and run manifests without sending any requests. This creates a final safety and operations layer for a future controlled provider call.

## goal
Add a sandbox-only provider dry-run controller for Stage 1 AI repair.

This task must not call any model or network. It only reads the provider request batch and configuration template, produces dry-run manifests, request shards, cost/budget estimates, execution checklist, and a replay plan.

Target new helper:
- D:\_datefac\tools\dry_run_stage1_ai_repair_provider.py

Target code may also update if needed:
- D:\_datefac\tools\intake_stage1_ai_repair_provider_responses.py
- D:\_datefac\tools\run_stage1_ai_repair_worker.py

Target local reports:
- D:\_datefac\output\delivery_package\54_stage1_ai_repair_provider_dry_run_log.md
- D:\_datefac\output\delivery_package\54_stage1_ai_repair_provider_dry_run_log.xlsx
- D:\_datefac\output\delivery_package\55_stage1_ai_repair_provider_dry_run_evaluation.md
- D:\_datefac\output\delivery_package\55_stage1_ai_repair_provider_dry_run_evaluation.xlsx

Sandbox dry-run dir:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_dry_run

Expected sandbox files:
- provider_dry_run_manifest.json
- provider_request_shard_001.jsonl
- provider_request_shard_002.jsonl if needed
- provider_request_shard_index.xlsx
- provider_execution_checklist.md
- provider_command_template.md
- provider_response_save_contract.md
- provider_post_run_replay_plan.md
- provider_budget_estimate.xlsx

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
16. The controller must default to dry_run=true and must refuse execution if a non-dry-run flag is attempted in this task.

## implementation_requirements

### 1. Dry-run helper CLI
Implement:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\dry_run_stage1_ai_repair_provider.py ^
  --request-batch D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_preflight\provider_request_batch.jsonl ^
  --config-template D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_preflight\provider_config_template.json ^
  --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --max-requests-per-shard 10 ^
  --dry-run
```

### 2. Request sharding
Split provider_request_batch.jsonl into shards:
- default max 10 requests per shard;
- preserve request_id / repair_task_id / priority / sample_id / task_type;
- produce shard index xlsx with counts by sample, task_type, priority.

### 3. Budget estimate
Create a rough token/character budget estimate:
- input_char_count per request;
- estimated_input_tokens = ceil(chars / 4) unless better deterministic estimator exists;
- estimated_output_tokens from config template max_output_tokens;
- per-shard token totals;
- total estimated tokens.

Do not call tokenizer libraries that trigger downloads.

### 4. Command template
Generate provider_command_template.md with safe placeholders only.

It must say:
- This is not executed by this pipeline.
- Use external credentials only via env var.
- Save raw provider responses to a local JSONL file.
- Do not paste API keys into repo files.
- After provider run, feed raw response JSONL to `intake_stage1_ai_repair_provider_responses.py`, not directly to worker.

### 5. Post-run replay plan
Generate provider_post_run_replay_plan.md:
- raw response path convention;
- intake command template;
- expected clean/rejected files;
- offline_file replay path;
- production write remains forbidden until separate approval.

### 6. Safety checks
Verify:
- dry_run is true;
- no network call attempted;
- no secret-like strings in outputs;
- no production files changed;
- no model/vision/OCR triggered.

### 7. Reports 54/55
Generate:
- D:\_datefac\output\delivery_package\54_stage1_ai_repair_provider_dry_run_log.md
- D:\_datefac\output\delivery_package\54_stage1_ai_repair_provider_dry_run_log.xlsx

54 report must include:
- task_title
- started_at / finished_at
- commands_run
- request_batch_path
- config_template_path
- dry_run_dir
- request_count
- shard_count
- output_files_generated
- no_secret_check_status
- production_guard_changed_count
- safety_checks

Generate:
- D:\_datefac\output\delivery_package\55_stage1_ai_repair_provider_dry_run_evaluation.md
- D:\_datefac\output\delivery_package\55_stage1_ai_repair_provider_dry_run_evaluation.xlsx

55 report must include:
- provider_dry_run_status: PASS / WARN / FAIL
- dry_run_mode
- request_count
- shard_count
- selected_sample_counts
- selected_task_type_counts
- priority_counts
- estimated_total_input_tokens
- estimated_total_output_tokens
- no_secret_check_status
- command_template_status
- post_run_replay_plan_status
- production_delivery_status_after
- production_files_unchanged
- recommended_next_step

Excel sheets required:
- summary
- shard_index
- request_inventory
- sample_counts
- task_type_counts
- priority_counts
- budget_estimate
- no_secret_check
- production_guard
- safety_checks
- next_steps

## validation_commands
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\dry_run_stage1_ai_repair_provider.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\dry_run_stage1_ai_repair_provider.py ^
  --request-batch D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_preflight\provider_request_batch.jsonl ^
  --config-template D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_preflight\provider_config_template.json ^
  --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --max-requests-per-shard 10 ^
  --dry-run
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

If intake or worker code is modified, also py_compile them.

## acceptance_criteria
This task passes if:
1. py_compile passes.
2. Dry-run manifest is generated.
3. Request shards are generated.
4. Shard index and budget estimate are generated.
5. Command template and post-run replay plan are generated.
6. Dry-run controller refuses or does not expose actual execution in this task.
7. No network/model/API call occurs.
8. No secrets are written.
9. 54/55 reports are generated.
10. Production 01/02/02A/06 are unchanged.
11. Production delivery remains PASS.
12. No factory_core/marker/surya/vision/PaddleOCR/model download occurred.
13. Output artifacts are not committed.

A WARN status is acceptable if request batch is missing or smaller than expected, provided this is clearly documented and no unsafe action occurs.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_add_stage1_ai_repair_provider_dry_run_controller.md

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
- provider_dry_run_status
- request_count
- shard_count
- no_secret_check_status
- production_delivery_status_after
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Allowed to commit:
- tools/dry_run_stage1_ai_repair_provider.py
- tools/intake_stage1_ai_repair_provider_responses.py if modified
- tools/run_stage1_ai_repair_worker.py if modified
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

Do not commit:
- output/delivery_package/54_stage1_ai_repair_provider_dry_run_log.md
- output/delivery_package/54_stage1_ai_repair_provider_dry_run_log.xlsx
- output/delivery_package/55_stage1_ai_repair_provider_dry_run_evaluation.md
- output/delivery_package/55_stage1_ai_repair_provider_dry_run_evaluation.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/dry_run_stage1_ai_repair_provider.py tools/intake_stage1_ai_repair_provider_responses.py tools/run_stage1_ai_repair_worker.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "add stage1 ai repair provider dry run controller"
git push origin main
```

If intake/worker were not modified, omit them from git add.

## expected_final_response
After completion, output:
1. task_title
2. dry_run_helper_path
3. py_compile_status
4. provider_dry_run_status
5. dry_run_mode
6. request_count
7. shard_count
8. selected_sample_counts
9. selected_task_type_counts
10. priority_counts
11. estimated_total_input_tokens
12. estimated_total_output_tokens
13. no_secret_check_status
14. generated_outputs
15. production_delivery_status_after
16. production_files_unchanged
17. factory_core/vision/model_download_status
18. next_step_suggestion
19. commit sha

## safety_notes
- This task creates a provider dry-run controller only.
- It must not call a real model.
- It must not write AI results into production delivery_package.
- It must not run factory_core.py.
- It must not trigger vision/OCR/model backends.
- It must not modify production delivery data.
