# 348A Excel Intake Audit Plan

## Goal

`348A` should validate an already extracted Excel workbook against a source financial PDF and related evidence, without re-running PDF extraction as part of the pilot.

## Pilot Scope

The first pilot should stay minimal and evidence-driven:

- accept one extracted Excel workbook plus its source PDF;
- map workbook tables or rows to PDF sections or pages when possible;
- audit core financial metrics for label, unit, and period alignment;
- identify rows that require human review before any delivery step.

## Expected Flow

```text
input workbook + source PDF
-> intake
-> schema normalization
-> audit checks
-> review queue
-> delivery-ready audit summary
```

## Initial Audit Checks

The first implementation pass should focus on a small set of high-value checks:

- metric alias normalization for common financial indicators;
- year and period alignment such as `2024A / 2025E / 2026E`;
- unit semantics across monetary, percentage, per-share, and valuation metrics;
- evidence presence and traceability;
- missing, duplicated, or suspicious core rows.

## Expected Outputs

`348A` should aim to produce review-oriented artifacts such as:

- a clean structured workbook or table export;
- an audit summary in Markdown;
- a review queue for human follow-up;
- an evidence index that preserves traceability.

## Non-Goals

`348A` should not:

- re-implement full PDF extraction;
- call MinerU as the mainline step;
- migrate broad legacy code into the new package;
- become a generic assistant workflow.

## Dependency on Foundation Stage

This plan depends on the current foundation cleanup creating:

- a clean package skeleton;
- minimal shared schemas;
- import smoke tests;
- a documented boundary between legacy assets and the new agent mainline.
