# DateFac Agent

## 1. Project Positioning

DateFac Agent is the new clean foundation for the DateFac project after the pivot from raw PDF table extraction to financial document extraction audit.

Chinese positioning:

```text
金融文档 AI 抽取结果审计与可信交付系统
```

This directory is intentionally separate from the legacy `datefac/` package.

The new project direction is not:

```text
Build another PDF table extraction tool.
```

The new project direction is:

```text
Accept extracted financial data from LLM apps, MinerU, spreadsheets, or other tools, then audit whether the data is correct, complete, traceable, and safe to deliver.
```

## 2. Why This Directory Exists

The original DateFac repository accumulated many useful experiments and validation assets:

- MinerU extraction experiments.
- PDF / Markdown / JSON evidence binding attempts.
- Full structured demo exports.
- Quality-limited recovery experiments.
- Semantic class and unit guardrails.
- Independent QA audits.
- Human review package design.

Those assets are valuable, but the old codebase also contains many experiment-specific runners, benchmark scripts, output-path assumptions, temporary workflows, and historical task documents.

`datefac_agent/` exists to create a clean new mainline without immediately deleting or rewriting the legacy project.

## 3. What Belongs Here

Only stable, reusable agent-oriented capabilities should be moved into this directory.

Good candidates:

- Excel / extraction artifact intake.
- Metric alias normalization.
- Unit semantic checking.
- Period and year alignment checking.
- Valuation metric checking.
- Evidence reference structures.
- Risk classification.
- Human review queue building.
- Audit report writing.
- Clean delivery artifact writing.
- Workflow orchestration.

## 4. What Does Not Belong Here Yet

Do not move the following into `datefac_agent/` during the foundation stage:

- Old MinerU runners.
- 346B-specific recovery runners.
- One-off benchmark scripts.
- Hard-coded output replay scripts.
- Historical demo-only snapshots.
- Large old output datasets.
- Temporary local experiment files.

These should remain in legacy locations until a dedicated migration decision is made.

## 5. Current Foundation Stage

This first stage is only about rebuilding the project foundation:

```text
Create clean docs.
Define the pivot.
Define what to migrate.
Define what to freeze.
Prepare for 348A.
```

It is not yet the full agent implementation stage.

## 6. Immediate Next Milestone

The next practical milestone is expected to be:

```text
348A AI-Extracted Excel Intake Audit Pilot
```

348A should start from a PDF plus an already extracted Excel file and audit the extracted data instead of re-extracting the PDF from scratch.

## 7. Safety Rules

During the foundation stage:

- Do not delete legacy code.
- Do not rewrite the old `datefac/` package.
- Do not mutate old 345D / 346B / 346B4 / 346B5 / 346B5Q outputs.
- Do not move large input or output directories.
- Do not treat MinerU 3.3.1 as the new single core parser.
- Do not build a generic chatbot agent.

## 8. One-Sentence Summary

DateFac Agent is a clean new project foundation that reuses the old DateFac project's audit, evidence, guardrail, and review assets while moving away from raw PDF table extraction as the core moat.
