# Codex Worklog - Latest

## task_title
Expand Stage 1 AI repair deterministic extract replay coverage

## started_at
2026-05-19 21:35:00

## finished_at
2026-05-19 21:50:00

## git_commit_before
976a962

## git_commit_after
pending

## commands_run
- Read D:\_datefac\docs\ai_handoff\NEXT_CODEX_TASK.md
- D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\build_stage1_ai_repair_extract_replay_set.py
- D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\run_stage1_ai_repair_worker.py
- D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\build_stage1_ai_repair_extract_replay_set.py --packet-jsonl D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl --schema-json D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 --delivery-dir D:\_datefac\output\delivery_package --max-extracts 20 --coverage-mode curated
- D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json

## files_read
- D:\_datefac\docs\ai_handoff\NEXT_CODEX_TASK.md
- D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json

## files_changed
- D:\_datefac\tools\build_stage1_ai_repair_extract_replay_set.py
- D:\_datefac\docs\codex_worklog\LATEST.md
- D:\_datefac\docs\codex_worklog\history\20260519_215910_expand_stage1_ai_repair_extract_coverage.md

## files_generated
- D:\_datefac\output\delivery_package\48_stage1_ai_repair_extract_coverage_log.md
- D:\_datefac\output\delivery_package\48_stage1_ai_repair_extract_coverage_log.xlsx
- D:\_datefac\output\delivery_package\49_stage1_ai_repair_extract_coverage_evaluation.md
- D:\_datefac\output\delivery_package\49_stage1_ai_repair_extract_coverage_evaluation.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_coverage\extract_coverage_responses.jsonl
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_coverage\extract_task_selection_diagnostics.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_coverage\ai_repair_results.jsonl
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_coverage\ai_repair_results.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_coverage\ai_repair_candidates.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_coverage\ai_repair_validation.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\ai_repair_extract_coverage\ai_repair_merge_preview.xlsx

## extract_coverage_status
WARN

## decision_counts
- extract: 7
- manual_review: 69
- ignore: 1

## extracted_candidate_count
7

## evidence_check_status
PASS

## production_delivery_status_after
- overall_status: PASS
- pass_count: 17
- warn_count: 0
- fail_count: 0

## result_summary
Expanded the deterministic extract replay helper to perform curated selection, write extract coverage diagnostics, and replay offline_file responses against the worker. Seven deterministic extracts still passed schema/evidence checks and routed to ai_candidate_for_rule_validation. Coverage remained limited because S1 and S3 deterministic evidence do not safely support more extracts, and S2 still has no metric candidates.

## remaining_issues
- Coverage gaps remain for 归属母公司净利润, 每股收益, ROE, 毛利率, and 净利率.
- S2 still has no deterministic metric candidates, so the replay remains WARN rather than PASS.

## next_step_suggestion
Keep this as the deterministic baseline and only expand further when packet evidence supports more safe extracts without weakening evidence checks.

## safety_notes
- Did not run factory_core.py.
- Did not trigger marker/surya/vision/PaddleOCR.
- Did not download model.safetensors or any model.
- Did not call any real AI model/API/network endpoint.
- Did not modify production 01/02/02A/06.
- Output artifacts were not committed.
