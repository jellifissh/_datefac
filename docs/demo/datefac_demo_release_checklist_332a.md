# Demo Release Checklist 332A / 341A Synced

## 1. Safe To Show On GitHub

- MinerU-first real PDF intake
- deterministic precision calibration, context repair, and reviewed strictness QA
- AI review as dry-run only
- workbook-based human review before client preview
- post-human sidecar result, client preview, and client preview audit
- `341A` milestone wording: `demo_ready = true`, `client_preview_ready = true`
- explicit `client_ready = false`
- explicit `production_ready = false`
- explicit `not investment advice`

## 2. Safe To Say In Interview

- parser quality alone is not enough
- deterministic rules stay above model suggestions
- AI decisions are dry-run only
- human review is deliberately isolated before preview promotion
- `340F` is a human-reviewed client preview, not official delivery
- `340G` audit passed with `duplicate_issue_count = 0`, `unit_issue_count = 0`, `missing_source_trace_count = 0`, `unsafe_claim_count = 0`
- the current benchmark is still limited to the present real-PDF sample set

## 3. Must Not Claim

- client-ready delivery
- production-ready deployment
- automatic write-back
- no human review needed
- 100% extraction accuracy
- direct investment advice
- scalable production stability

## 4. Known Limitations

- current benchmark remains a limited real-PDF sample set
- parser robustness still needs broader validation
- metadata extraction is not fully solved
- UI review workflow is still workbook-centric
- batch reliability still needs stronger proof
- broader operational hardening is unfinished

## 5. Suggested Next Engineering Milestones

- expand the real-PDF benchmark
- improve parser robustness
- improve metadata extraction
- build a stronger UI review workflow
- improve batch reliability
- define production governance only after those foundations improve
