# DateFac Agent Project Background

## 1. Original Project Background

The original DateFac project started as a financial PDF table extraction and structured export system.

The early goal was straightforward:

```text
Take financial PDFs, research reports, or financial statements, extract tables and metrics, clean them, and export usable structured data.
```

The project focused on:

- PDF table extraction.
- MinerU outputs.
- Markdown and JSON parsing.
- Table images and page images as evidence.
- Structured data inventory.
- Quality gating.
- Human review packages.
- Demo exports.

This direction was reasonable at the time because extracting tables from financial PDFs was still painful and inconsistent.

## 2. What the Old Project Achieved

The old DateFac work produced several important assets.

### 2.1 Extraction and Evidence Experiments

The project tested how MinerU and related outputs could support financial PDF processing:

- Markdown outputs.
- JSON content lists.
- Table image crops.
- Page-level evidence.
- Image path binding.
- Evidence linkage between rows and source documents.

The key lesson was that extraction alone is not enough. A usable system needs evidence, lineage, and auditability.

### 2.2 Strict Quality Filtering

The project established a strict quality-first posture.

Instead of allowing all extracted rows through, DateFac separated rows into:

- demo-ready rows;
- quality-limited rows;
- excluded rows;
- human review rows;
- rule-refinement rows.

This strict quality gate is one of the most important project assets.

The value is not simply that DateFac can extract rows. The value is that DateFac can decide which rows should not be trusted.

### 2.3 346B Series Recovery and QA Work

The 346B series proved that many quality-limited rows could be recovered only if semantic class, unit policy, lineage, and false-positive guardrails were handled carefully.

The 346B chain included:

```text
346B    quality-limited recovery pilot
346B2   QA audit that found false-positive risks
346B3   rule refinement for semantic/unit risks
346B2R  re-audit after refinement
346B4   controlled expansion
346B3R  follow-up patch
346B4R  replay with patched rules
346B4Q  independent QA audit
346B5   larger expansion
346B5Q  larger expansion QA audit
```

This work created reusable ideas:

- semantic class checking;
- unit repair and unit-risk detection;
- ratio / percentage / per-share / monetary amount separation;
- lineage audit;
- evidence audit;
- false-positive guardrails;
- independent QA report pattern;
- human review queue pattern.

These ideas should be reused in DateFac Agent.

## 3. Why the Project Is Pivoting

Recent manual comparison showed that general large-model apps can already extract core financial tables from certain research report PDFs very well.

That changes the project economics.

Raw table extraction is becoming less defensible as the main moat. General LLM/VLM apps, MinerU upgrades, and future extraction services will keep improving.

Therefore, DateFac should move upward:

```text
from extraction
into audit, validation, evidence, review, and trusted delivery
```

The new project should not try to beat every frontier model at raw table extraction.

Instead, it should accept extracted artifacts from different sources and decide whether the result is safe to use.

## 4. What Should Be Preserved

The following old assets should be preserved:

- 345D full structured demo export package.
- 346B series recovery and QA logic.
- Unit and semantic guardrails.
- Evidence binding ideas.
- Human review package design.
- QA report patterns.
- Strict demo-only and sidecar-only safety posture.
- MinerU 3.3.1 benchmark work as sidecar extractor evaluation.

These should be treated as legacy validation assets and future audit-engine ingredients.

## 5. What Should Be Paused

The following should be paused as the mainline:

- Immediate continuation into 346B6 full recovery.
- More full-scale recovery on old MinerU outputs.
- Writing more rules whose only purpose is to rescue old extraction artifacts.
- Treating any single parser as the central project moat.

Paused does not mean deleted. These branches can remain as references, regression assets, or optional side experiments.

## 6. New Foundation Principle

The new foundation should be built as:

```text
Legacy DateFac assets + clean agent-oriented audit workflow
```

The old project proved what kinds of errors exist.

The new project should turn those lessons into reusable audit tools.

## 7. Current Boundary

This document does not define the full future business product.

It only defines why the project is moving from raw extraction to an agent-oriented audit foundation and why the `datefac_agent/` directory exists.
