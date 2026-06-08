# DateFac Demo Overview 331B

## Problem
Financial PDF extraction quality depends not only on parser coverage, but also on whether unit handling, provenance, and human review boundaries are visible before anything is treated as trusted.

## Current Status
DateFac is a financial PDF core-metric extraction and trust-routing demo.
Current status: demo-ready after human unit review preview.
The project is not production-ready and not client-ready yet.

## What Changed From 331A
331A was demo-ready with unit review caveats.
330K2 packaged 21 unit-review rows for manual review.
330K3 simulated applying those human decisions without write-back.
330K4 refreshed the preview state so only reviewed-safe rows were surfaced into the trusted preview.

## Reviewed Preview State
- Original trusted preview rows: 96
- Reviewed unit-confirmed rows added or surfaced: 2
- Reviewed trusted preview rows: 98
- Human-rejected rows isolated from trusted preview: 18
- Remaining review-required rows after unit review: 1

## Safe Claims
The demo can claim sidecar trust routing, provenance preservation, manual unit review packaging, dry-run review application, reviewed preview refresh, and conservative demo documentation.
If available, official rule milestones remain scope rules 1 and alias rules 6.

## Unsafe Claims
Do not claim production routing changes, client delivery readiness, or write-back into official assets.
Do not claim that the 330K4 reviewed preview is a production export.

## Next Steps
Next steps can focus on presentation polish, additional human validation, and future safe write-back planning, but not on production-ready claims.
331A baseline project status remains DEMO_READY_WITH_UNIT_REVIEW_CAVEATS.
