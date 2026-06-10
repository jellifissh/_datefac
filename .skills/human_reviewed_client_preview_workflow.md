# Skill: Human-Reviewed Client Preview Workflow

## Scope
This skill covers the validated human-reviewed preview chain from `340B` through `341B`.

## Workflow
- `340B` human review package
- `340C` full validation
- `340D` apply plan
- `340E` post-human sidecar
- `340F` client preview
- `340G` client preview audit
- `341A` milestone package
- `341B` documentation sync

## Current Key Results
- `340B review queue = 77`
- `340C filled = 77 / pending = 0`
- `340D final reviewed after human candidate count = 34`
- `340E reviewed_after_human_total_count = 34`
- `340F client_preview_core_metric_count = 34`
- `340G audited_core_metric_count = 34`
- `duplicate_issue_count = 0`
- `unit_issue_count = 0`
- `missing_source_trace_count = 0`
- `unsafe_claim_count = 0`
- `qa_fail_count = 0`
- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`

## Interpretation Rules
- human-reviewed preview is not official delivery
- not investment advice
- not production-ready
- AI decisions are dry-run only
- no write-back to upstream workbook unless explicitly requested and separately validated

## Safe Claims
- the demo can show a real review loop
- the preview can show 34 human-reviewed core metrics
- the audit chain shows duplicate/unit/source-trace/claim issues were controlled in the preview package

## Unsafe Claims
- do not say official client delivery is ready
- do not say production deployment is ready
- do not say AI review alone is sufficient
- do not say the current sample proves scalable production stability

