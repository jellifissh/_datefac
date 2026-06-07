# DateFac README Section 331A

## Current Status
DateFac is currently demo-ready with manual review caveats.
The repository demonstrates sidecar trust scoring and preview packaging, but it is not production-ready or client-ready yet.

## Architecture
- Parser-output normalization and candidate shaping
- Semantic rule curation and closure reporting
- Sidecar trust scoring and risk routing
- Provenance preservation and client-style preview packaging

## What The Demo Shows
- 330A foundation: risk registry 18 and routing-policy smoke tests
- 330B scoring: scoring model component count 7
- 330C cached benchmark: 12076 cached candidates when available
- 330L preview: 96 trusted preview rows and 21 review-required rows

## How To Run Key Sidecar Reports
```powershell
python tools\run_delivery_report_refresh_after_330k_330j2.py --unit-signal-review-dir D:\_datefac\output\unit_signal_review_330k --fixed-prepared-dir D:\_datefac\output\unfamiliar_trust_split_330k --previous-delivery-report-dir D:\_datefac\output\delivery_report_refresh_330j --deduped-candidate-benchmark-dir D:\_datefac\output\deduped_candidate_trust_benchmark_330e --trust-scoring-dir D:\_datefac\output\trust_engine_scoring_330b --rerun-330f --output-dir D:\_datefac\output\delivery_report_refresh_after_330k_330j2
python tools\run_client_style_export_preview_330l.py --delivery-report-refresh-dir D:\_datefac\output\delivery_report_refresh_after_330k_330j2 --fixed-prepared-dir D:\_datefac\output\unfamiliar_trust_split_330k --unit-signal-review-dir D:\_datefac\output\unit_signal_review_330k --output-dir D:\_datefac\output\client_style_export_preview_330l
```

## Known Limitations
- Sidecar-only trust scoring; no production routing changes
- Residual unit review remains
- Cached unfamiliar PDF evidence only; no fresh PDF reopen in this demo path
