# Review Queue Package

Purpose:
- Review queue schema, workbook round-trip helpers, ingestion, spot-check, strict-review, and demo-package review workflows.

Not responsible for:
- low-level parser runtime

Place new files here when:
- they belong to workbook-based review governance or review-result sidecar handling

Category:
- source code

MinerU-first / table-first relation:
- review-queue flows sit downstream of extraction and table-first packaging, turning bounded outputs into review-governed artifacts.
