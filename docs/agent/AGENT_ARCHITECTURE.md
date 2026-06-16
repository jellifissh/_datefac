# DateFac Agent Architecture

## Purpose

`datefac_agent/` is the clean foundation for the new DateFac mainline after the pivot from raw PDF extraction toward extraction audit, review, and trusted delivery.

This first-round architecture document stays intentionally narrow. It does not define a generic chatbot, an automated trading workflow, or any external automation promises.

## Core Flow

The target high-level workflow is:

```text
intake -> audit -> review -> delivery
```

Each stage has a clear responsibility boundary:

- `intake`: accept extracted spreadsheets, structured outputs, or related evidence packages.
- `audit`: run reusable checks on metric labels, units, periods, evidence, and delivery risk.
- `review`: route suspicious or high-risk records into a human review workflow.
- `delivery`: write clean, review-aware outputs such as audit summaries, evidence indexes, and reviewed structured tables.

## Module Layout

The initial package skeleton is:

```text
datefac_agent/
  intake/
  audit/
  review/
  delivery/
  orchestrator/
  schemas/
  llm/
```

Current intent for each area:

- `intake/`: input adapters for Excel, extracted artifacts, and related source bundles.
- `audit/`: pure checker modules that return structured audit results.
- `review/`: review queue construction and decision helpers.
- `delivery/`: report writing and clean-output packaging.
- `orchestrator/`: workflow routing and stage coordination.
- `schemas/`: shared models used across the new agent flow.
- `llm/`: future isolation area for prompts and model-client wiring, not business logic.

## Safety Boundary

This foundation stage does not:

- replace the legacy `datefac/` package;
- migrate old runner scripts wholesale;
- claim `client_ready` or `production_ready`;
- convert benchmark outputs into delivery assets.

The new package should grow by rebuilding reusable audit capabilities from legacy lessons, not by copying historical baggage.

## Near-Term Direction

The next milestone is expected to be `348A AI-Extracted Excel Intake Audit Pilot`.

That pilot should start from an already extracted Excel file plus the corresponding PDF evidence, then validate whether the extracted data is correct, traceable, complete, and safe for review-oriented delivery.
