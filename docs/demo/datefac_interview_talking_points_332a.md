# Interview Talking Points 332A

## Why Parser Quality Alone Is Not Enough
A parser can recover text and table cells, but downstream trust still depends on whether the metric label, unit, year alignment, and provenance are all coherent. Good raw extraction does not automatically mean a row is safe to trust.

## Why Unit Review Matters
Unit ambiguity can silently flip the meaning of a value. By forcing a human review stage for unit-risk rows, the system avoids treating weakly supported rows as trusted output.

## How Trust Routing Works
The system keeps sidecar trust scoring separate from production routing. Rows with strong evidence and clean risk profiles surface into trusted preview, while ambiguous rows stay review-required and risky rows can be isolated.

## Why Human Review Is Isolated Before Write-Back
Write-back creates a much higher correctness bar. Isolating manual review outcomes in a dry-run and reviewed-preview path preserves traceability and avoids accidentally promoting unresolved rows into official assets.

## What Changed From 331A To 331B
331A packaged a demo-ready baseline with unit review caveats. 330K2 collected unit-review rows, 330K3 simulated applying decisions without write-back, 330K4 refreshed the reviewed preview, and 331B updated the demo narrative around that safer reviewed state.
