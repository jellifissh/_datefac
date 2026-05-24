# Stage7H Runtime Integration Plan (Design Only)

## Goal
Integrate AI-assisted suggestion layer between manual-review queue and sandbox clean preview generation, with strict deterministic validation and human approval.

## Proposed entrypoint
`python tools/run_stage7i_ai_runtime_dry_run.py --input output/stage7g_manual_review_reduction_sandbox --output output/stage7i_ai_runtime_dry_run`

## Pipeline placement
1. Build deterministic reduced preview (existing Stage 7G flow).
2. Build manual review evidence package per conflict group.
3. Generate AI request payloads.
4. Call AI runtime adapter (Stage 7I; mock in dry-run mode).
5. Validate AI responses using deterministic rules.
6. Route validated suggestions to `ai_suggestion_queue` (still requires human approval).
7. Keep rejected/invalid suggestions in `manual_review_queue`.
8. Produce audit logs and stage summary.

## Safety gates
- AI cannot write production 06.
- AI cannot modify formal rules.
- True conflicts remain human-approved.
- EPS unit guard (元/股 only).
- Non-traceable suggestions are automatically rejected.

## Audit artifacts
- ai_review_requests.jsonl
- ai_review_responses.jsonl
- ai_validation_results.xlsx/json
- ai_suggestion_audit_log.xlsx
- manual_approval_queue.xlsx

## Human-in-the-loop protocol
- Reviewer accepts/rejects per review_id.
- Any rejected item returns to manual queue.
- Accepted items can be merged into sandbox preview only.
