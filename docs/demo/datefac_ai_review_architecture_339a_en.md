# DateFac AI Review Architecture 339A (Synced To 341A State)

## 1. What This Architecture Document Now Does

This document no longer only explains “how models were compared.” It explains the real role of AI in the current complete chain:

> AI is a dry-run judgment layer constrained by deterministic rules, grounding requirements, human-review closure, and no-write-back boundaries. It is not the formal decision layer.

## 2. Where AI Sits In The Full Chain

The full chain is now:

`Real PDFs -> MinerU-first extraction -> AI dry-run review -> Human review -> 340C full validation -> 340D apply plan -> 340E post-human sidecar -> 340F client preview -> 340G audit -> 341A milestone package`

AI sits in the middle, not at the end.

## 3. Current State

- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `not investment advice`

## 4. Why AI Must Still Come After Deterministic Reviewed Gating

If the reviewed pool is still loose before `337D`, AI just explains noise more confidently.

That is why `337D` matters:

- stricter reviewed gate
- year-alignment repair
- suspicious-row QA

It tightens the pool before the AI layer sees it.

## 5. Architectural Meaning Of 338A-338D

### 338A

- DeepSeek baseline dry-run
- conservative reference point

### 338B

- A/B comparison between `AI_REVIEW_MODEL` and the baseline
- checks whether the stronger model actually reduces low-confidence and needs-more-context behavior

### 338C

- grounded schema tightening
- separates raw evidence, supporting context, and conclusion

### 338D

- adoption simulation
- separates model output from formal adoption policy

The most important conclusion at this layer remains:

- `suggest_set_ai_review_model_default = false`

So AI does not become the formal default simply because local task performance improved.

## 6. Why 340B-341A Still Matter After AI Dry-Run

Because after AI dry-run there are still real rows that:

- need human confirmation
- need correction before confirmation
- need rejection or continued review

That is why 340B-341A matter:

- human review is explicitly inserted before preview
- all apply-like results remain sidecar and no-write-back
- only human-reviewed confirmed results reach the client preview

## 7. Current Headline Counts

- `340B review queue = 77`
- `340C filled = 77 / pending = 0`
- `340D reviewed_after_human_candidate_count = 34`
- `340E reviewed_after_human_total_count = 34`
- `340F client_preview_core_metric_count = 34`
- `340G audited_core_metric_count = 34`
- `duplicate_issue_count = 0`
- `unit_issue_count = 0`
- `missing_source_trace_count = 0`
- `unsafe_claim_count = 0`
- `qa_fail_count = 0`

## 8. The Real Role Of AI In Today’s System

AI is not:

- the final truth layer
- a write-back engine
- a client-ready decision-maker
- a production-ready approval layer

It is:

- a text-adjudication candidate for ambiguous rows
- an input layer for adoption simulation
- a mid-layer constrained by deterministic rules, human review, and preview audit

## 9. Safe Claims Today

- AI improves dry-run adjudication quality and candidate suggestion quality
- grounded review makes AI output more auditable
- AI output is still constrained by human review and preview audit

## 10. Unsafe Claims Today

- AI has replaced human review
- AI output can be used directly for client delivery
- AI is now production-ready
- AI output should be treated as investment advice

## 11. Current Benchmark Limitation

The current benchmark is still a limited real-PDF sample set. It proves the chain works on the current sample, not that it is stable at larger scale or across broader layout diversity.

## 12. Summary

> The main value of the 339A AI architecture today is not proving that the model is strong enough. It is proving that even a stronger model must remain constrained by deterministic rules, human-review closure, and preview audit. 
