# 348A Input Output Contract Draft

## Status

This document is a draft contract for `348A AI-Extracted Excel Intake Audit Pilot`.

It defines the intended boundaries for the next milestone only. It does not imply implementation completeness, client readiness, or production readiness.

Current gate status remains:

- `client_ready = false`
- `production_ready = false`

## Expected Inputs

`348A` should start from already extracted artifacts, not from raw PDF extraction.

Expected minimum inputs:

- one source financial PDF;
- one already extracted Excel workbook or equivalent spreadsheet artifact;
- optional supporting evidence references such as page mappings or extraction notes.

Expected input characteristics:

- workbook should contain candidate financial tables or metric rows;
- source PDF should be available for evidence lookup;
- inputs should be local and reviewable;
- no MinerU run is required as part of the pilot contract itself.

## Expected Outputs

The pilot should aim to produce review-oriented outputs such as:

- `clean_data.xlsx` or an equivalent clean structured workbook;
- `audit_report.md`;
- `review_queue.xlsx`;
- `evidence_index.json`.

Output intent:

- `clean_data.xlsx`: structured values that survived the first audit pass;
- `audit_report.md`: summary of findings, counts, limitations, and boundary statements;
- `review_queue.xlsx`: rows that require human review before any further promotion;
- `evidence_index.json`: traceability mapping between extracted values and available evidence.

## Audit Categories

The first contract should support at least these audit categories:

- metric label normalization;
- unit semantic checking;
- year and period alignment;
- valuation metric classification;
- per-share versus total amount distinction;
- duplicate or suspicious core metric detection;
- evidence presence and lineage completeness.

## Review Queue Expectations

The review queue should be explicit and conservative.

Rows should enter review when:

- unit semantics look suspicious;
- year columns appear shifted, missing, or duplicated;
- valuation metrics may be misclassified;
- evidence is weak or absent;
- row meaning is ambiguous enough that automatic pass would be unsafe.

The review queue is not a production approval system. It is a human-follow-up artifact for the pilot.

## Evidence Index Expectations

The evidence index should preserve a minimal traceability contract:

- identify the source PDF;
- identify where a metric was observed or inferred from;
- preserve page-level or section-level reference when available;
- make missing evidence visible instead of silently passing it through.

The pilot may start with lightweight evidence references and refine them later.

## Non-Goals

`348A` should not:

- re-extract the PDF from scratch;
- call LLM APIs as a required step;
- run MinerU as the mainline path;
- migrate broad legacy runner code;
- open any production or client delivery gate.

## Delivery Boundary

`348A` outputs should be treated as pilot-side audit artifacts.

They are not:

- official client delivery;
- upstream workbook write-back;
- proof of production stability.
