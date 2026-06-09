# DateFac Current Runbook 333A / 341A Synced

## 1. Scope

This runbook now covers the current displayable path from real PDFs through AI dry-run, human review, client preview, and audit.

## 2. Current Stage

- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `not investment advice`

## 3. What To Read First

1. `README.md`
2. `docs/demo/datefac_human_reviewed_client_preview_runbook_341b_en.md`
3. `docs/demo/datefac_human_reviewed_client_preview_architecture_341b_en.md`
4. `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_en.md`
5. `docs/demo/datefac_ai_review_architecture_339a_en.md`

## 4. Most Important Outputs Right Now

- `D:\_datefac\output\human_reviewed_client_preview_milestone_341a\human_reviewed_client_preview_milestone_341a.xlsx`
- `D:\_datefac\output\client_preview_export_audit_340g\client_preview_export_audit_340g.xlsx`
- `D:\_datefac\output\client_preview_after_human_review_340f\client_preview_after_human_review_340f.xlsx`

## 5. Most Important Counts Right Now

- `340B review queue = 77`
- `340C filled = 77 / pending = 0`
- `340D reviewed_after_human_candidate_count = 34`
- `340E reviewed_after_human_total_count = 34`
- `340F client_preview_core_metric_count = 34`
- `340G audited_core_metric_count = 34`

## 6. Boundaries That Must Stay Visible

- AI decisions are dry-run only
- human review was used before client preview
- `340F` is a human-reviewed client preview, not official delivery
- `340G` passed audit, but the system is still not production-ready

## 7. Demo Order

1. establish boundaries from the README
2. open the 341A milestone workbook for the full-chain summary
3. open the 340G audit workbook for risk-audit evidence
4. drill into 340D / 340E / 340F only if needed

## 8. What Not To Do

- do not treat output artifacts as formal delivery
- do not claim client-ready
- do not claim production-ready
- do not imply investment advice

## 9. Next Directions

- larger benchmark
- parser robustness
- metadata extraction
- UI review workflow
- batch reliability
