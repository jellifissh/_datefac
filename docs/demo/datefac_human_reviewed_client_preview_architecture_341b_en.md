# DateFac Human-Reviewed Client Preview Architecture 341B (English)

## 1. One-Line Positioning

This architecture document describes DateFac at its strongest current external-telling state: real PDFs enter parsing and rule layers, AI stays dry-run only, human review absorbs residual risk, and an audited client preview becomes the top demo artifact.

## 2. Current Boundary State

- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `not investment advice`

## 3. Why A Human-Review Closure Was Still Required

337A-338D proved that:

- real PDFs can enter a MinerU-first intake path
- deterministic rules can materially reduce reviewed noise
- AI dry-run can perform text adjudication, grounding, and adoption simulation

But that still was not enough for an external preview state because:

- adoption simulation is not formal adoption
- AI output can still require correction, rejection, or continued review
- client preview needs stronger unit, source-trace, and claim-safety boundaries

That is why 340B-340G exist: they convert post-AI residual risk into a human-reviewed and audited preview state.

## 4. Current Architecture Layers

1. real-PDF intake layer
2. deterministic repair and QA layer
3. AI dry-run review layer
4. workbook-based human review layer
5. post-human sidecar result layer
6. client-preview packaging layer
7. preview-audit and milestone-packaging layer

## 5. Stage Responsibilities

### 337A-337D

- `337A` handles real-PDF MinerU-first intake
- `337B` handles candidate precision calibration
- `337C` handles financial-context repair and unit recovery
- `337D` handles reviewed strictness, year alignment, and suspicious-row QA

### 338A-338D

- `338A` provides the DeepSeek baseline dry-run
- `338B` provides `AI_REVIEW_MODEL` A/B comparison
- `338C` provides grounded schema tightening
- `338D` provides adoption simulation

The most important architectural conclusion here is that AI output remains advisory, not final apply behavior.

### 340B-340G

- `340B` packages the rows requiring manual review into a workbook
- `340C` validates manual review content for full or incremental validation
- `340D` generates the full human-review apply plan
- `340E` generates the post-human-review sidecar result
- `340F` generates the human-reviewed client preview
- `340G` audits whether that preview is safe for demo or client-preview presentation

### 341A

- `341A` packages 340B-340G into a milestone-level explanation artifact

## 6. How The Counts Connect

- `340B review queue = 77`
- `340C filled = 77 / pending = 0`
- `340D reviewed_after_human_candidate_count = 34`
- `340E reviewed_after_human_total_count = 34`
- `340F client_preview_core_metric_count = 34`
- `340G audited_core_metric_count = 34`

This count chain means:

- not every reviewed queue row becomes preview material
- only 34 human-confirmed or corrected-confirmed core metrics enter the preview
- the remaining rows are either rejected or left under review

## 7. Why 340G Matters

340G is not just another packaging step. It is the boundary audit that confirms:

- `duplicate_issue_count = 0`
- `unit_issue_count = 0`
- `missing_source_trace_count = 0`
- `unsafe_claim_count = 0`
- `qa_fail_count = 0`

That is the direct reason the client preview can be described as safe for demo or preview presentation.

## 8. Safe System Claims

- the path from real PDFs to preview now exists end to end
- AI remains constrained inside dry-run and adoption-simulation boundaries
- human review closes the loop before preview promotion
- the preview output has been audited and is suitable for demo or client-preview discussion

## 9. Unsafe System Claims

- formal client delivery
- production write-back
- human-free automation
- scalable stable production
- investment advice

## 10. Risk-Control Framework

Current risk control does not depend on claiming that the model is stronger. It depends on:

- deterministic rules first
- AI dry-run only
- human review before preview
- no-write-back proof
- preview audit
- persistent documentation of `client_ready = false` and `production_ready = false`

## 11. Benchmark Limitation

The current benchmark is still a limited real-PDF sample set, which means:

- it proves the chain can run on the current sample
- it does not prove scalable, layout-diverse, production-grade stability

## 12. Real Next Bottlenecks

- larger benchmark
- parser robustness
- metadata extraction
- UI review workflow
- batch reliability

## 13. Summary

> The value of the 341B architecture is not that it makes DateFac sound like a mature product. It accurately positions DateFac as a trust-governed demo system that has completed a human-reviewed client-preview milestone while keeping explicit engineering boundaries. 
