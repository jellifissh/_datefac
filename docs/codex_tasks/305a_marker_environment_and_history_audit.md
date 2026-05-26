# Task 305A: Marker Environment and History Audit

## Stage
- `EVAL-MARKER-1A-ENV`

## Goal
- Audit current local Marker runtime status and historical Marker-path behavior evidence.
- Produce a small, reproducible audit report without rerunning the 10-PDF benchmark.

## Scope
- Read local environment and existing repo artifacts only.
- Create audit outputs under:
  - `output/eval_marker1a_environment_and_history_audit/`

## Hard Constraints
- No external API calls.
- No LLM API calls.
- No OCR calls.
- Do not rerun full Marker benchmark.
- Do not modify extraction logic.
- Do not modify candidate rules.
- Do not modify production files / official 02B / formal rules / `financial_standardizer.py` / release package.
- Do not modify input PDFs.
- Must keep `check_delivery_state.py --json` as `PASS`.

## Required Checks
- Current Marker version.
- Marker CLI path.
- Marker import availability.
- Current successful no-LLM command template.
- Existing/old marker-related files in repository.
- Likely reason old Marker path failed (if evidence exists).
- Recommended stable Marker invocation policy.

## Expected Outputs
- `output/eval_marker1a_environment_and_history_audit/305a_marker_environment_history_audit_summary.json`
- `output/eval_marker1a_environment_and_history_audit/305a_marker_environment_history_audit_report.md`
- `output/eval_marker1a_environment_and_history_audit/305a_marker_related_files_inventory.xlsx`
- `output/eval_marker1a_environment_and_history_audit/305a_no_apply_proof.json`

## Run
1. `python tools/run_305a_marker_environment_and_history_audit.py`
2. `python tools/check_delivery_state.py --json`

## Git Hygiene
- Commit only minimal required files for this task.
- Do not stage historical untracked files:
  - `tools/run_stage7a_5pdf_regression_sandbox.py`
  - `tools/update_stage5v_production_06_safe_rows.py`
- Do not commit bulky runtime folders.
