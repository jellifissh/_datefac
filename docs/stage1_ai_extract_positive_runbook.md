# Stage 1 AI Extract-Positive Runbook

## Scope
This runbook defines the repeatable operational procedure for future Stage 1 AI extract-positive repair batches.

## Global Preconditions
- Production delivery package is readable.
- Required Stage 1 scripts are available and py_compile-clean.
- No unresolved repository conflicts.
- Output paths are writable.

## Hard Prohibitions
- Do not skip intake/replay.
- Do not skip allowlist gate.
- Do not skip sandbox dry-run apply.
- Do not skip approval review.
- Do not run real apply without backup + hash guard.

## Step-by-Step Procedure
### Step 1: Provider Intake / Replay
- preconditions: provider request batch + raw response JSONL exist
- command/tool: `tools/intake_stage1_ai_repair_provider_responses.py` + offline replay path
- expected outputs: clean/rejected response JSONL and replay candidates
- pass criteria: schema/evidence linkage checks pass for clean set
- stop criteria: malformed response ratio or schema violations block replay

### Step 2: Allowlist Standardization Gate
- preconditions: replay candidate workbook exists
- command/tool: `tools/standardize_ai_extract_candidates.py`
- expected outputs:
  - `ai_extract_candidates_standardized.xlsx`
  - `ai_extract_candidates_accepted.xlsx`
  - `ai_extract_candidates_manual_review.xlsx`
  - `ai_extract_candidates_rejected.xlsx`
- pass criteria: accepted set only includes allowlisted + evidence-pass candidates
- stop criteria: evidence gate failures or uncontrolled metric mapping

### Step 3: Merge Simulation
- preconditions: accepted candidates and read-only production 06 available
- command/tool: `tools/simulate_ai_extract_candidate_merge.py`
- expected outputs:
  - `ai_extract_merge_simulation_all.xlsx`
  - `ai_extract_merge_safe_candidates.xlsx`
  - `ai_extract_merge_manual_review.xlsx`
  - `ai_extract_merge_blocked.xlsx`
- pass criteria: safe candidates identifiable; blocked/conflict diagnostics complete
- stop criteria: unresolved duplicate/conflict patterns without routing

### Step 4: Apply Plan Preparation
- preconditions: merge simulation artifacts exist
- command/tool: `tools/prepare_ai_extract_apply_plan.py`
- expected outputs:
  - `ai_extract_apply_plan_all.xlsx`
  - `ai_extract_apply_plan_safe_apply.xlsx`
  - `ai_extract_apply_plan_review.xlsx`
  - `ai_extract_apply_plan_blocked.xlsx`
- pass criteria: clear split between SAFE_APPLY and REVIEW/BLOCKED
- stop criteria: missing apply decision traceability

### Step 5: Sandbox Dry-Run Apply
- preconditions: safe_apply file exists
- command/tool: `tools/dry_run_apply_ai_extract_candidates.py`
- expected outputs:
  - `ai_extract_apply_dry_run_06_copy.xlsx`
  - `ai_extract_apply_dry_run_diff.xlsx`
  - `ai_extract_apply_dry_run_applied_rows.xlsx`
  - `ai_extract_apply_dry_run_skipped_rows.xlsx`
- pass criteria: dry-run outputs generated with conflict/duplicate checks
- stop criteria: dry-run apply failures or unexplainable skips

### Step 6: Approval Review Package
- preconditions: dry-run diff/applied/log/eval outputs exist
- command/tool: approval review generator (current workflow package for 68/69 artifacts)
- expected outputs:
  - `68_ai_extract_real_apply_approval_review.xlsx/.md`
  - `69_ai_extract_real_apply_readiness_summary.json`
- pass criteria:
  - `ready_for_real_apply=true`
  - `blocked_count=0`
  - `need_manual_review_count=0`
  - `approved_candidate_count` equals intended apply count
- stop criteria: any condition above not satisfied

### Step 7: Real Apply (06 Only)
- preconditions:
  - Step 6 pass criteria all true
  - backup path writable
  - hash guard enabled
- command/tool: `tools/real_apply_ai_extract_candidates.py`
- expected outputs:
  - backup `06_*.before_ai_extract_real_apply.xlsx`
  - `70_ai_extract_real_apply_log.xlsx/.md`
  - `71_ai_extract_real_apply_diff.xlsx`
  - `72_ai_extract_real_apply_summary.json`
- pass criteria:
  - apply count equals approved count
  - skipped=0
  - failed=0
  - 01/02/02A hashes unchanged
  - 06 hash changed
- stop criteria:
  - any candidate apply fails
  - hash guard violation
  - unauthorized file mutation detected

### Step 8: Post-Apply Verification
- preconditions: 68/70/71/72 + backup/current 06 available
- command/tool: `tools/post_real_apply_verify_stage1_extract.py` and closure report generator
- expected outputs:
  - `73_stage1_ai_extract_post_apply_verification.xlsx/.md`
  - `74_stage1_ai_extract_closure_summary.json`
- pass criteria:
  - cross-artifact alignment pass
  - expected 06 delta only
  - delivery status PASS
  - `stage1_extract_positive_closed=true`
- stop criteria: any mismatch across approval/log/diff/summary or unexpected production delta

### Step 9: Version-Control Checkpoint
- preconditions: post-apply closure true
- command/tool: git add/commit/push
- expected outputs: closure checkpoint commit
- pass criteria: only allowed files committed; no output artifacts committed
- stop criteria: staged output artifacts or unresolved repo boundary issues

