# Stage7O2 Retry Plan

1. Retry scope: failed cases only (`stage7i_review_0001`, `stage7i_review_0013`).
2. For HTTP 503 case: one retry allowed after 10 seconds.
3. For schema_invalid case: run safe schema repair pre-check; if not repairable, re-request once with stricter field-type constraint.
4. Keep `requires_human_approval=true` for all outputs.
5. Keep sandbox-only mode; do not write to production 06.
6. Stop expansion immediately on any HTTP 429.
7. Keep timeout and max_tokens unchanged unless retry still fails.