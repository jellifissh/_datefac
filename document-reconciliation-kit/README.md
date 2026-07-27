# document-reconciliation-kit

`document-reconciliation-kit` is a small, deterministic Python library for comparing two structured document outputs. It converts MinerU-style JSON and Excel or normalized JSON into a common record model, identifies discrepancies, and produces compact JSON and Markdown review reports.

It is deliberately not an extraction runtime, workflow platform, database service, or delivery system. The kit makes no network calls and does not invoke MinerU, OCR, LLMs, VLMs, or PDF parsers.

## Install

```powershell
python -m pip install -e "document-reconciliation-kit[dev]"
```

## CLI

```powershell
doc-reconcile compare --left mineru_content_list_v2.json --right workbook.xlsx --output comparison.json
doc-reconcile report --comparison comparison.json --output-dir review-report
doc-reconcile benchmark --review-pack reviewed_cells.xlsx --output-dir benchmark-summary
```

`compare` accepts page-grouped MinerU `content_list_v2` JSON on the left. The right input may be an Excel workbook or a normalized JSON record list. Output paths are explicit and existing files are never overwritten.

## Python API

```python
from document_reconciliation.adapters.mineru import extract_mineru_records
from document_reconciliation.reconciliation import reconcile_records

left_records = extract_mineru_records(mineru_payload)
result = reconcile_records(left_records, right_records)
```

The default comparison identity is `context + metric_key + period`. Financial aliases are optional and live in `document_reconciliation.profiles.financial`; the core package uses generic text normalization by default.

## Boundaries

- Inputs are read only from caller-supplied paths.
- Report output contains bounded evidence previews and compact source trace metadata.
- Full raw artifacts and full HTML table dumps are not included in comparison or report payloads.
- Benchmark metrics count only rows explicitly marked `VERIFIED`.
