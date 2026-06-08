# DateFac README Section 331B

## Current Status
DateFac is demo-ready after human unit review preview.
The repository demonstrates sidecar trust scoring, manual unit review packaging, dry-run application, and reviewed preview refresh.
It is not production-ready and not client-ready yet.

## What The Refreshed Demo Shows
- 331A baseline status: DEMO_READY_WITH_UNIT_REVIEW_CAVEATS
- 330A foundation: risk registry 18
- 330B scoring: scoring model component count 7
- 330K4 reviewed preview: 98 reviewed trusted rows, 18 human-rejected rows, 1 remaining review-required row

## Human Review Narrative
- 330K2 packaged unit-risk rows for manual review.
- 330K3 simulated applying reviewer decisions without write-back.
- 330K4 refreshed the preview so reviewed-safe rows are visible while rejected or unresolved rows remain isolated.

## Limitations
- Sidecar-only refresh; no production routing changes
- No write-back into the original 330L workbook
- Not a client-ready or production-ready export
