# Stage 1 AI Extract-Positive Pipeline

## Goal
Stage 1 AI repair extract-positive is an **AI-assisted, gate-controlled, auditable data repair pipeline**.
It does **not** allow AI to directly mutate production financial outputs.

The core objective is to convert AI repair suggestions into production-safe updates through strict staged controls.

## End-to-End Flow
1. AI extract JSONL
2. intake / replay
3. allowlist gate
4. merge simulation
5. apply plan
6. sandbox dry-run apply
7. approval review
8. real apply
9. post-apply verification
10. closure checkpoint

## Stage Definitions
### 1) AI extract JSONL
- stage name: `ai_extract_jsonl`
- purpose: collect structured AI repair proposals
- input: provider or offline JSONL responses
- output: candidate JSONL records
- gate condition: schema and evidence fields must be present
- production mutation allowed: no
- failure behavior: reject malformed records and stop downstream promotion

### 2) Intake / Replay
- stage name: `provider_intake_and_replay`
- purpose: validate request/response linkage and replay candidates deterministically
- input: raw provider response JSONL, request batch JSONL, schema contract
- output: clean response JSONL, rejected response JSONL, replay candidates
- gate condition: request_id/repair_task_id/schema/evidence checks pass
- production mutation allowed: no
- failure behavior: quarantine invalid responses; replay only clean set

### 3) Allowlist Gate
- stage name: `extract_candidate_allowlist_gate`
- purpose: standardize metrics and route to accepted/manual/rejected
- input: replay candidates, validation artifacts
- output: standardized candidates; accepted/manual_review/rejected splits
- gate condition: evidence check PASS + metric allowlist policy
- production mutation allowed: no
- failure behavior: block or manual-route non-compliant candidates

### 4) Merge Simulation
- stage name: `accepted_candidate_merge_simulation`
- purpose: simulate merge with production keyspace without writing production
- input: accepted candidates, read-only production 06
- output: SAFE / MANUAL / BLOCK decision sets
- gate condition: no invalid year/unit, no duplicate/conflict violations
- production mutation allowed: no
- failure behavior: mark as `BLOCK_*` or `MANUAL_REVIEW_REQUIRED`

### 5) Apply Plan
- stage name: `apply_plan_preparation`
- purpose: split simulated safe candidates into apply-ready vs review-before-apply
- input: merge simulation outputs
- output: apply_plan_all, safe_apply, review, blocked
- gate condition: `SAFE_APPLY_CANDIDATE` rules pass
- production mutation allowed: no
- failure behavior: keep non-passing rows in review/blocked buckets

### 6) Sandbox Dry-Run Apply
- stage name: `sandbox_dry_run_apply`
- purpose: test writes on sandbox copy with diff logs
- input: safe_apply candidates, read-only production 06
- output: sandbox 06 copy, dry-run diff, applied/skipped logs
- gate condition: duplicate/conflict/year/value guards pass in sandbox execution
- production mutation allowed: no
- failure behavior: skip or fail candidate; generate diagnostics

### 7) Approval Review
- stage name: `real_apply_approval_review`
- purpose: candidate-level approval package for real apply decision
- input: dry-run diff, applied rows, dry-run log/evaluation
- output: approval review workbook + readiness summary JSON
- gate condition: ready_for_real_apply true and risk review passes
- production mutation allowed: no
- failure behavior: block real apply until unresolved items are cleared

### 8) Real Apply
- stage name: `real_apply_with_backup_and_hash_guard`
- purpose: apply approved candidates to production 06 under strict protection
- input: approval review, readiness summary, production 06
- output: updated production 06, backup file, apply log, real diff, summary JSON
- gate condition: readiness true, blocked_count=0, need_manual_review_count=0, approved count aligned
- production mutation allowed: yes (06 only)
- failure behavior: stop on first failure, keep backup, emit failure summary

### 9) Post-Apply Verification
- stage name: `post_apply_verification`
- purpose: verify cross-artifact consistency and production safety after real apply
- input: approval review, apply log, diff, summary, backup 06, current 06
- output: verification workbook/markdown + closure summary JSON
- gate condition: expected row/key changes only, delivery state PASS
- production mutation allowed: no
- failure behavior: mark stage not closed, trigger rollback decision workflow

### 10) Closure Checkpoint
- stage name: `closure_checkpoint`
- purpose: freeze Stage 1 outcome in version control
- input: verified results and scripts
- output: git commit/push checkpoint
- gate condition: post-apply verification closed=true and repo boundary rules satisfied
- production mutation allowed: no
- failure behavior: do not checkpoint until boundary violations are resolved

