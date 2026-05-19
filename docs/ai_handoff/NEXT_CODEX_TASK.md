# NEXT CODEX TASK

## task_title
Prepare Stage 1 AI repair real-provider preflight bundle

## project
D:\_datefac

## current_status
The deterministic extract replay coverage expansion has completed.

Latest committed result:
- commit: ab2b60d expand stage1 ai repair extract coverage

Latest user-uploaded/reviewed output summary:
- task_title = Expand Stage 1 AI repair deterministic extract replay coverage
- extract_coverage_status = WARN
- response_file_task_count = 12
- decision_counts = {extract: 7, manual_review: 69, ignore: 1}
- extracted_candidate_count = 7
- ai_candidate_for_rule_validation_count = 7
- evidence_check_status = PASS
- invalid_extract_count = 0
- production_delivery_status_after = PASS / pass_count=17 / warn_count=0 / fail_count=0
- production_files_unchanged = true
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model download not triggered
- no real AI inference call was made

Interpretation:
Deterministic replay proved the extract path but did not materially expand safe extract coverage beyond 7. This is now a reasonable boundary for purely deterministic replay. The next step is not to call a real model yet, but to prepare a real-provider preflight bundle: request JSONL, provider interface contract, safety budget, response file contract, and validation checklist.

## goal
Prepare a sandbox-only real-provider preflight bundle for the Stage 1 AI repair worker.

This task must not call any model or network. It only prepares request batches, provider contracts, config templates, and validation documents for a future controlled provider run.

Target code:
- D:\_datefac\tools\run_stage1_ai_repair_worker.py if interface validation changes are needed
- New helper preferred:
  D:\_datefac\tools\prepare_stage1_ai_repair_provider_preflight.py

Target local reports:
- D:\_datefac\output\delivery_package\50_stage1_ai_repair_provider_preflight_log.md
- D:\_datefac\output\delivery_package\50_stage1_ai_repair_provider_preflight_log.xlsx
- D:\_datefac\output\delivery_package\51_stage1_ai_repair_provider_preflight_evaluation.md
- D:\_datefac\output\delivery_package\51_stage1_ai_repair_provider_preflight_evaluation.xlsx

Sandbox preflight dir:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_provider_preflight

Expected sandbox files:
- provider_request_batch.jsonl
- provider_request_batch_sample.md
- provider_response_contract.md
- provider_config_template.json
- provider_run_checklist.md
- provider_response_validation_plan.md
- provider_preflight_inventory.xlsx

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

### 1. Build provider request batch
Read:
- D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema_and_prompt.md

Create:
- provider_request_batch.jsonl

Each line should include:
- request_id
- repair_task_id
- sample_id
- company
- task_type
- priority
- provider_prompt
- expected_output_schema
- evidence_digest
- source_trace_id
- safety_constraints
- response_required_json_only = true
- must_not_invent_values = true

Do not include full PDF contents or raw binary data.
Keep each provider prompt bounded and evidence-only.

### 2. Task selection for first real-provider run
Do not send all 77 tasks by default.

Select a controlled first batch:
- 10 to 20 tasks total
- include S1/S3 ambiguous high-value cases
- include S2 table-level repair tasks
- include at least one row_segment_repair if available
- include at least one semantic_guard_review
- include at least one metric_year_value_alignment if available

Add priority:
- P0: high-value extract candidate ambiguity
- P1: S2 table-level no-metric diagnosis
- P2: semantic guard review / lower-value ambiguity

Create diagnostics in XLSX:
- selected_provider_requests
- excluded_packet_tasks
- sample_task_counts
- task_type_counts
- priority_counts

### 3. Provider config template
Create `provider_config_template.json` with placeholders only:
- provider_name: local_or_cloud_provider_placeholder
- model_name: placeholder
- endpoint_url: placeholder_do_not_commit_real_endpoint
- api_key_env_var: STAGE1_AI_REPAIR_API_KEY
- timeout_seconds
- max_retries
- max_concurrent_requests
- max_input_chars_per_task
- max_output_tokens
- temperature: 0
- json_only: true
- dry_run: true

No real secrets.

### 4. Response contract and validation plan
Create:
- provider_response_contract.md
- provider_response_validation_plan.md

Must specify:
- response must be one JSON object per request;
- repair_task_id must match request;
- output must conform to 38 schema;
- extracted values must appear in evidence;
- invalid responses are demoted or blocked;
- no AI response can directly write production 06;
- all real-provider outputs must first be saved to local response JSONL and then replayed via offline_file.

### 5. Preflight evaluation
Generate 50/51 reports.

50 report must include:
- task_title
- started_at / finished_at
- commands_run
- input_files_read
- output_files_generated
- provider_request_count
- selected_sample_counts
- selected_task_type_counts
- config_template_status
- no_secret_check_status
- production_guard_changed_count
- safety_checks

51 report must include:
- provider_preflight_status: PASS / WARN / FAIL
- provider_request_count
- selected_sample_counts
- selected_task_type_counts
- priority_counts
- prompt_size_summary
- schema_reference_status
- response_contract_status
- validation_plan_status
- no_secret_check_status
- production_delivery_status_after
- production_files_unchanged
- recommended_next_step

Excel sheets required:
- summary
- selected_provider_requests
- excluded_packet_tasks
- sample_task_counts
- task_type_counts
- priority_counts
- prompt_size_summary
- config_template
- no_secret_check
- production_guard
- safety_checks
- next_steps

## validation_commands
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\prepare_stage1_ai_repair_provider_preflight.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\prepare_stage1_ai_repair_provider_preflight.py ^
  --packet-jsonl D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl ^
  --schema-json D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json ^
  --prompt-md D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema_and_prompt.md ^
  --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --max-provider-tasks 20
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

If `run_stage1_ai_repair_worker.py` is modified, also py_compile it.

## acceptance_criteria
This task passes if:
1. py_compile passes.
2. Provider request batch is generated.
3. Provider request count is between 10 and 20 unless insufficient eligible tasks are documented.
4. S1/S2/S3 are represented where possible.
5. Task type coverage includes at least S2 table-level and at least one ambiguity/review task type.
6. Provider config template contains no real secrets.
7. Response contract and validation plan are generated.
8. No network/model/API call occurs.
9. 50/51 reports are generated.
10. Production 01/02/02A/06 are unchanged.
11. Production delivery remains PASS.
12. No factory_core/marker/surya/vision/PaddleOCR/model download occurred.
13. Output artifacts are not committed.

A WARN status is acceptable if eligible provider task diversity is limited, provided this is clearly documented.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_prepare_stage1_ai_repair_provider_preflight.md

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
- provider_preflight_status
- provider_request_count
- production_delivery_status_after
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Allowed to commit:
- tools/prepare_stage1_ai_repair_provider_preflight.py
- tools/run_stage1_ai_repair_worker.py if modified
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

Do not commit:
- output/delivery_package/50_stage1_ai_repair_provider_preflight_log.md
- output/delivery_package/50_stage1_ai_repair_provider_preflight_log.xlsx
- output/delivery_package/51_stage1_ai_repair_provider_preflight_evaluation.md
- output/delivery_package/51_stage1_ai_repair_provider_preflight_evaluation.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/prepare_stage1_ai_repair_provider_preflight.py tools/run_stage1_ai_repair_worker.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "prepare stage1 ai repair provider preflight"
git push origin main
```

If worker was not modified, omit it from git add.

## expected_final_response
After completion, output:
1. task_title
2. helper_path
3. py_compile_status
4. provider_preflight_status
5. provider_request_count
6. selected_sample_counts
7. selected_task_type_counts
8. priority_counts
9. no_secret_check_status
10. generated_outputs
11. production_delivery_status_after
12. production_files_unchanged
13. factory_core/vision/model_download_status
14. next_step_suggestion
15. commit sha

## safety_notes
- This task only prepares a real-provider preflight bundle.
- It must not call a real model.
- It must not write AI results into production delivery_package.
- It must not run factory_core.py.
- It must not trigger vision/OCR/model backends.
- It must not modify production delivery data.
