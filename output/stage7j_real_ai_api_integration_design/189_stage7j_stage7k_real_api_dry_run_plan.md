# Stage7K Real API Sandbox Dry-Run Plan

## Objective
Run real provider integration in sandbox mode with strict guardrails and zero production impact.

## Preconditions
- Stage7J design artifacts committed.
- Reviewed provider adapter implementation available.
- Explicit operator flag `--enable-external-api` required.
- Runtime env var `AI_REVIEW_API_KEY` provided out-of-repo.

## Execution scope
1. Read Stage7G remaining manual review groups.
2. Build requests via Stage7H schema.
3. Invoke provider adapter with capped requests/tokens/cost.
4. Validate responses with Stage7H/7I rules.
5. Route to suggestion/rejected queue.
6. Produce sandbox preview only.

## Hard limits
- max_requests_per_run <= 5
- max_total_tokens_per_run <= 10k
- max_total_cost_usd_per_run <= 2.0
- timeout_seconds <= 30
- retries <= 2

## Success criteria
- external API call traceable and bounded.
- no secret leakage in logs.
- no production file changes.
- validation pass rate reported.
- all suggestions remain human-approval required.
