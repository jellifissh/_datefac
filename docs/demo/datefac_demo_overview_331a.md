# DateFac Demo Overview 331A

## Problem
Financial PDF core-metric extraction is difficult to trust because parser output, units, semantics, and provenance often drift before anything reaches downstream review.

## System Capability
DateFac is a financial PDF core-metric extraction and trust-routing demo.
Current status: demo-ready with manual review caveats.
The system demonstrates parser-output normalization, semantic rule curation, sidecar trust scoring, risk flagging, provenance preservation, and client-style Excel preview generation.
It is not production-ready or client-ready yet.

## Architecture Summary
The demo uses cached parser outputs and sidecar trust artifacts rather than changing production routing.
Key layers are parser-output normalization, candidate shaping, semantic-rule curation, trust scoring, risk routing, and Excel/report packaging.

## Trust Engine Workflow
1. Load prepared candidate rows with provenance preserved.
2. Apply sidecar trust scoring and route rows into trusted vs review-required buckets.
3. Surface unit-risk and conflict rows for human review instead of auto-promoting them.
4. Package results into client-style preview outputs and demo-facing summaries.

## Demo Output Artifacts
- 330L preview workbook: D:\_datefac\output\client_style_export_preview_330l\client_style_export_preview_330l_preview.xlsx
- Prepared candidate rows: 117
- Trusted preview rows: 96
- Review-required rows: 21
- Unit review sample rows: 21

## What Is Safe To Claim
The demo can truthfully claim parser-output normalization, provenance-preserving sidecar trust scoring, curated semantic patch history, and conservative preview packaging.
If available, official rule milestones include scope rules 1 and alias rules 6.

## What Is Not Safe To Claim
Do not claim production routing changes, client-ready deployment, or zero-manual-review operation.
Do not claim that the preview workbook is a production export.

## Next Steps
Immediate next step remains 330K2 human unit review to reduce residual unit-risk rows.
After that, demo packaging can extend into a clearer presentation flow without changing production behavior.
