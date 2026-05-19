# NEXT CODEX TASK

## task_title
Implement Stage 1 sandbox AI repair worker MVP

## project
D:\_datefac

## current_status
The Stage 1 sandbox AI repair input packet has been prepared and committed.

Latest committed result:
- commit: 851b234 prepare stage1 ai repair packet

Latest user-uploaded/reviewed outputs:
- D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.md
- D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.xlsx
- D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema_and_prompt.md
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema_and_prompt.xlsx
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_packet_validation.xlsx
- D:\_datefac\output\delivery_package\39_stage1_ai_repair_packet_build_log.md
- D:\_datefac\output\delivery_package\39_stage1_ai_repair_packet_build_log.xlsx

Key result from 37/38/39:
- task_title = Prepare Stage 1 sandbox AI repair packet
- helper_path = D:\_datefac\tools\prepare_stage1_ai_repair_packet.py
- py_compile_status = PASS
- packet_build_status = PASS
- repair_task_count = 77
- task_type_counts:
  - row_segment_repair = 5
  - metric_year_value_alignment = 2
  - semantic_guard_review = 65
  - s2_table_level_repair = 5
- sample_task_counts:
  - S1 = 56
  - S2 = 5
  - S3 = 16
- s2_table_level_task_count = 5
- jsonl_validation_status = PASS
- production_delivery_status_after = PASS / warn_count=0 / fail_count=0
- production_guard_changed_count = 0
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model download not triggered
- no AI inference call was made

Interpretation:
The AI repair packet and strict output schema are ready. The next step is to implement a sandbox-only AI repair worker MVP that consumes the 37 JSONL packet and produces schema-constrained candidate outputs. This task must not call any real AI model yet. It should implement a worker shell, schema validation, offline/mock response path, and repair candidate merge/evaluation reports. Real local/cloud model integration can be added later.

## goal
Implement a sandbox-only AI repair worker MVP.

The worker should:
1. read `37_stage1_ai_repair_input_packet.jsonl`;
2. read and enforce `38_stage1_ai_repair_schema.json`;
3. produce one schema-compliant repair result per task;
4. support an offline/mock mode by default, with no model call;
5. support a future provider interface but leave real AI providers disabled;
6. validate all outputs;
7. generate sandbox-only AI repair candidate files and evaluation reports;
8. avoid production delivery writes.

Target new helper/tool:
- D:\_datefac\tools\run_stage1_ai_repair_worker.py

Do not modify `prepare_stage1_ai_repair_packet.py` unless required for compatibility.

Target local outputs:
- D:\_datefac\output\delivery_package\40_stage1_ai_repair_worker_log.md
- D:\_datefac\output\delivery_package\40_stage1_ai_repair_worker_log.xlsx
- D:\_datefac\output\delivery_package\41_stage1_ai_repair_worker_evaluation.md
- D:\_datefac\output\delivery_package\41_stage1_ai_repair_worker_evaluation.xlsx

Sandbox AI repair output dir:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_trial

Output files under sandbox AI repair dir:
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

## worker_modes
Implement CLI modes:

1. default safe mode:
   - `--provider offline_mock`
   - no model call
   - produces conservative JSON results based on task type and evidence only

2. future provider stubs:
   - optional accepted values: `offline_mock`, `offline_file`
   - `offline_file` may read precomputed model responses from a local JSONL file if provided
   - no `openai`, `deepseek`, `ollama`, `vllm`, `sglang`, or network providers in this task

Required arguments:
- `--packet-jsonl D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl`
- `--schema-json D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json`
- `--trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315`
- `--delivery-dir D:\_datefac\output\delivery_package`
- `--provider offline_mock`
- `--max-tasks 80`

Optional:
- `--offline-response-jsonl <path>` only for provider `offline_file`
- `--strict-schema`
- `--no-production-write` default true

## offline_mock_behavior
The offline mock is not meant to be smart. It must be safe and conservative.

Suggested behavior:
- For `s2_table_level_repair`: return decision `manual_review`, no repairs, with reason `no metric labels detected by rule packet; requires AI/model or human visual review`.
- For `semantic_guard_review`: return decision `manual_review` unless evidence contains an exact positive source label and no hard-risk flags. Since the packet is already demoted by rules, default to manual_review.
- For `metric_year_value_alignment`: if there is explicit unambiguous evidence in row_cells with a single metric and year/value count matches exactly, optional extract is allowed; otherwise manual_review.
- For `row_segment_repair`: do not attempt complex segmentation in mock mode unless the row clearly contains separate segments and exact year/value counts. Otherwise manual_review.

Important:
- offline_mock may produce mostly manual_review. That is acceptable.
- Do not fake high-confidence extraction.
- Never invent values.
- Always copy values only from evidence if extracting.

## schema_validation
Implement output validation:
- every output has repair_task_id;
- every output decision is one of extract/manual_review/ignore/non_target;
- repairs list exists;
- manual_review_items list exists;
- JSONL line count equals processed task count;
- all task IDs unique;
- all output task IDs exist in packet;
- extracted values, if any, must appear in evidence text or row_cells;
- if decision is extract, at least one repair item exists;
- if decision is manual_review, at least one manual_review_item exists;
- no garbled text;
- no production guard file changed.

## merge_preview
Generate `ai_repair_merge_preview.xlsx` but do not apply it to production.

Merge preview should show:
- repair_task_id
- sample_id
- company
- source_trace_id
- decision
- candidate standard_metric/year/value/unit if any
- evidence
- validation_flags
- recommended_route_after_ai:
  - ai_candidate_for_rule_validation
  - manual_review_candidate
  - ignore
  - non_target

Rules:
- AI repair result must not directly become trusted output.
- Extract decisions should route to `ai_candidate_for_rule_validation`, not production 06.
- Manual_review decisions route to `manual_review_candidate`.

## reports
Generate:
- D:\_datefac\output\delivery_package\40_stage1_ai_repair_worker_log.md
- D:\_datefac\output\delivery_package\40_stage1_ai_repair_worker_log.xlsx

40 report must include:
- task_title
- started_at / finished_at
- command_run
- provider
- packet_path
- schema_path
- trial_run_root
- processed_task_count
- decision_counts
- validation_status
- output_files_generated
- production_guard_changed_count
- safety_checks

Generate:
- D:\_datefac\output\delivery_package\41_stage1_ai_repair_worker_evaluation.md
- D:\_datefac\output\delivery_package\41_stage1_ai_repair_worker_evaluation.xlsx

41 report must include:
- ai_repair_worker_status: PASS / WARN / FAIL
- provider
- task_count
- decision_counts
- extracted_candidate_count
- manual_review_count
- ignored_count
- non_target_count
- schema_validation_status
- extraction_value_evidence_check_status
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
  --provider offline_mock ^
  --max-tasks 80 ^
  --strict-schema
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

## acceptance_criteria
This task passes if:
1. py_compile passes.
2. --help passes.
3. worker processes 37 JSONL with 77 tasks or documented max-task count.
4. no real AI/model/API/network call occurs.
5. output JSONL is valid and schema-compliant.
6. every processed task has exactly one repair result.
7. extracted values, if any, are copied from evidence only.
8. 40/41 reports are generated.
9. sandbox AI repair output files are generated.
10. production 01/02/02A/06 are unchanged.
11. production delivery remains PASS.
12. no factory_core/marker/surya/vision/PaddleOCR/model download occurred.
13. output artifacts are not committed.

A WARN status is acceptable if offline_mock yields mostly manual_review, as long as validation passes and the pipeline is ready for a future real provider.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_implement_stage1_ai_repair_worker_mvp.md

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
- production_delivery_status_after
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Allowed to commit:
- tools/run_stage1_ai_repair_worker.py
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

Do not commit:
- output/delivery_package/40_stage1_ai_repair_worker_log.md
- output/delivery_package/40_stage1_ai_repair_worker_log.xlsx
- output/delivery_package/41_stage1_ai_repair_worker_evaluation.md
- output/delivery_package/41_stage1_ai_repair_worker_evaluation.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/run_stage1_ai_repair_worker.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "implement stage1 ai repair worker mvp"
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
7. processed_task_count
8. decision_counts
9. schema_validation_status
10. generated_outputs
11. production_delivery_status_after
12. production_files_unchanged
13. factory_core/vision/model_download_status
14. next_step_suggestion
15. commit sha

## safety_notes
- This task creates a sandbox AI repair worker harness only.
- It must not call a real model yet.
- It must not write AI results into production delivery_package.
- It must not run factory_core.py.
- It must not trigger vision/OCR/model backends.
- It must not modify production delivery data.
