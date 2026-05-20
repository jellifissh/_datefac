# Stage 2A AI Repair Override Layer Design

## 1. Background and Goal
Stage 1 real apply has written 13 approved AI extract-positive records into `06_最终核心财务指标.xlsx`.

Current risk:
- These 13 rows are delivery-layer results.
- They are not yet represented as a rebuildable upstream input layer.
- Future rebuild flows may overwrite 06 and lose Stage 1 gains.

Stage 2A goal:
- Introduce a rebuildable AI override input layer.
- Make Stage 1 real-applied records reproducible in deterministic rebuilds.
- Keep full provenance and conflict visibility.

## 2. Recommended Storage Location
Recommended source-of-truth location:
- `data/overrides/ai_repair_override.xlsx`

Recommended runtime mirror for delivery workflow compatibility:
- `output/delivery_package/02B_ai_repair_override.xlsx`

Rationale:
- `output/*` is usually not committed.
- Rebuild-critical override inputs should be version-controlled.
- Existing delivery tooling can still read runtime mirror under `output/delivery_package`.

## 3. Override Table Schema
Sheet name: `ai_repair_override`

Primary business key:
- `asset_package + standard_metric + year`

Required columns:
- `repair_id`
- `candidate_id`
- `asset_package`
- `standard_metric`
- `year`
- `final_value`
- `final_unit`
- `final_value_source`
- `final_review_status`
- `evidence`
- `source_reference`
- `approval_review_file`
- `real_apply_log_file`
- `stage_name`
- `apply_batch_id`
- `created_from_commit`
- `provenance_status`

Recommended additional operational columns:
- `override_priority` (default `2`, between manual and auto)
- `key_hash` (deterministic hash of key fields)
- `ingested_at`
- `ingested_by`
- `is_active` (`true/false`)
- `conflict_flag`
- `conflict_reason`

Field constraints:
- `year` matches current system year token style (`2025A`, `2026E`, `2025` etc.).
- `final_value` numeric.
- `provenance_status` enum:
  - `verified_from_stage1_artifacts`
  - `partial_evidence`
  - `conflict_pending`
  - `rejected`

## 4. Stage 1 Backfill Mapping Plan
Backfill target: exactly 13 rows from Stage 1 real apply.

Input artifacts:
- `68_ai_extract_real_apply_approval_review.xlsx`
- `70_ai_extract_real_apply_log.xlsx`
- `71_ai_extract_real_apply_diff.xlsx`
- `72_ai_extract_real_apply_summary.json`
- current `06` rows where `final_value_source=ai_extract_real_apply`

Backfill mapping logic:
1. Use `68` approved rows (`review_decision in {auto_approve, approved}`) as candidate scope.
2. Join with `70` by `candidate_id` for apply status and operation trace.
3. Join with `71` by `candidate_id` for diff-level key/value confirmation.
4. Cross-check with current `06` rows filtered by `final_value_source=ai_extract_real_apply`.
5. Only rows present in all required joins and key/value matched are marked `verified_from_stage1_artifacts`.
6. Generate `repair_id` deterministically, e.g. `S1A-<candidate_id>` or hash-based stable ID.
7. Set:
   - `stage_name = stage1_extract_positive`
   - `apply_batch_id = stage1_real_apply_20260520`
   - `created_from_commit = f518a10` (Stage 1 closure checkpoint)
   - `final_value_source = ai_extract_real_apply` (or normalized `ai_repair_override`)
   - `final_review_status = approved_auto_applied`

## 5. Rebuild Integration Design (01 + 02/02A + 02B -> 06)
Target flow in future rebuild:
1. Baseline: `01_自动可信核心指标.xlsx`
2. Apply manual layers: `02_人工复核指标队列.xlsx` + `02A_人工年份修正覆盖表.xlsx`
3. Apply AI override layer: `02B_ai_repair_override.xlsx`
4. Emit `06_最终核心财务指标.xlsx`

Source priority rule:
- `manual correction > AI repair override > auto trusted baseline`

Conflict handling rule:
- If key conflict under same priority or unresolved cross-source mismatch:
  - do not silently overwrite
  - route to conflict queue (`06B_未解决问题清单.xlsx` or dedicated queue)
  - mark `conflict_flag=true`

## 6. Key and Dedup Rules
Dedup key:
- `asset_package + standard_metric + year`

If existing script has stricter canonicalization:
- keep current canonicalization behavior
- apply same normalization before key build (trim, metric alias normalization, year token normalization)

Dedup policy:
- Same key + same value/unit: keep highest-priority row, mark duplicates as merged.
- Same key + different value/unit: conflict queue; never silent replace.

## 7. Validation Rules
For Stage 2A acceptance:
1. Rebuild 06 key/value set equals current production 06 key/value set (or explicitly approved delta list only).
2. Stage 1 13 records still exist after rebuild.
3. For these 13 rows, `final_value_source` remains `ai_extract_real_apply` or normalized `ai_repair_override`.
4. `check_delivery_state.py --json` remains `overall_status=PASS`.
5. 01/02/02A remain unchanged unless intentionally revised by manual workflow.

Recommended validation reports:
- key-level diff report (`before_rebuild_06` vs `after_rebuild_06`)
- Stage1-13 presence check report
- conflict queue report with counts and reasons

## 8. Failure and Rollback Design
If any of these fail:
- key/value mismatch beyond allowed scope
- missing Stage1-13 rows
- delivery check not PASS

Then:
- abort publish
- keep backup
- keep conflict queue for triage
- do not overwrite final release 06

## 9. Implementation Boundaries for Stage 2A
In-scope:
- add override schema and ingestion script(s)
- extend rebuild merger to read 02B layer
- add conflict queue and validation checks

Out-of-scope:
- re-running factory main flow
- any OCR/vision model path
- introducing new AI inference in apply step

## 10. Deliverable Checklist for Stage 2A Execution
- Override workbook schema defined and versioned.
- Stage1 13-row backfill completed with provenance.
- Rebuild merger supports 01+02/02A+02B priority logic.
- Conflict queue enabled (no silent overwrite).
- Validation confirms reproducibility and PASS delivery state.

