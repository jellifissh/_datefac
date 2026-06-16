# Legacy Asset Map

## Purpose

This document classifies major legacy DateFac assets so the new `datefac_agent/` mainline can reuse the right ideas without dragging old historical baggage into the foundation stage.

## KEEP_AS_LEGACY_REFERENCE

Assets that should remain intact as reference material:

- `345D` full structured demo export package.
- Human-reviewed client preview chain `340B` through `341B`.
- MinerU benchmark documents and sidecar evidence from `342A` through `342C4`.
- Historical architecture, demo, and milestone documents under `docs/`.

These assets provide context, evidence, and regression references, but they should stay in legacy locations.

## MIGRATE_CAPABILITY_LATER

Reusable capability ideas that should later be rebuilt inside `datefac_agent/`:

- metric alias normalization;
- unit semantic guardrails;
- period and year alignment checks;
- valuation metric checking;
- evidence and lineage structures;
- review queue generation;
- QA and audit report patterns.

The `346B` series is especially valuable here as audit-rule and test-fixture material. It should inform future agent audits, but it should not continue as the immediate mainline during this foundation round.

## FREEZE_AS_HISTORICAL_EXPERIMENT

Historical experiments that should stay available but not drive the new mainline:

- one-off recovery runners tied to old extraction artifacts;
- benchmark replay scripts with hard-coded output assumptions;
- parser-specific rescue paths built only for historical outputs;
- paused expansions such as immediate continuation of `346B6`.

These assets may still support regression analysis or future fixture harvesting.

## DO_NOT_TOUCH

Protected legacy areas that should remain untouched during the agent foundation cleanup:

- legacy `datefac/` package source;
- old `tools/` runners not required by this task;
- `input/`, `output/`, `temp/`, and `data/` directories;
- old `345D / 346B / 346B4 / 346B5 / 346B5Q` outputs.

These boundaries protect historical evidence and avoid accidental disruption of existing workflows.
