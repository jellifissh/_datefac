# Skill: Asset Artifacts

## Core Artifact Layers
- `02A`: extraction-layer evidence
- `02`: post-processed structured result
- `05`: financial standardization result

## Current Trusted Demo Path
- Human review sidecar
- Post-human sidecar result
- Human-reviewed client preview
- Client preview audit
- Milestone package

This chain is the current trusted demo path.
It is not the same thing as production-ready delivery.

## Benchmark Evidence Boundary
- `342A` to `342C*` outputs are parser evaluation evidence
- benchmark outputs are not client delivery artifacts
- benchmark outputs should not be treated as production source-of-truth assets

## Analysis Order
- inspect `02A` first
- then inspect `02`
- then inspect `05`
- avoid mixing files from different asset bundles before drawing conclusions

## Key Rules
- do not commit `output` artifacts casually
- do not use sidecar benchmark outputs as formal delivery claims
- record exactly which artifact version and timestamp the conclusion used

