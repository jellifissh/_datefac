# DateFac Project Overview 333A (English)

## 1. Background

DateFac is best understood as an engineering layer built around financial research PDF extraction, not as a claim that PDF parsing alone solves the downstream trust problem. In many document-extraction projects, the public story stops too early. A parser reads text, tables are detected, candidate rows are surfaced, and the demo ends there. That approach may look impressive, but it leaves out the hardest and most operationally important question: after candidate rows exist, which ones can actually be trusted, which ones need human review, which ones should be rejected from the trusted preview, and how should all of that be explained to others without overstating the project’s maturity?

DateFac’s current reviewed-preview path exists precisely because the team chose not to hand-wave those questions away. The project treats parser output as the beginning of the trust problem rather than the end of it. That is why the current late-stage work focuses on provenance, routing, unit risk, review isolation, dry-run simulation, preview refresh, demo packaging, and release-audit discipline.

## 2. The Problem Being Solved

The project solves a layered problem.

At the extraction layer, candidate rows may already exist. But raw extraction does not answer these business-critical questions:

- Does the row actually represent the intended metric?
- Is the value aligned with the correct year?
- Is the unit explicit, missing, or contradictory?
- Is the row part of a core forecast table or an unrelated peer-comparison or annotation fragment?
- Is the evidence strong enough to justify promotion into a trusted preview?
- If a human disagrees with the system, how do we reflect that safely?
- How do we show the project publicly without implying client delivery readiness or live deployment readiness?

DateFac handles the trust and presentation side of those questions. That is why it matters as an engineering project even in a repository that also contains parser and delivery work.

## 3. Why This Is Not Just PDF Table Extraction

A table extractor is mainly concerned with recognition and structure:

- Where are the tables?
- What are the rows and columns?
- What text is inside the cells?

DateFac goes further by asking:

- Is this candidate defensible?
- Is there provenance for human follow-up?
- Should the candidate remain in a review-required queue?
- Is the unit risk significant enough to isolate manually?
- Can the result be shown as a preview without pretending it is an official export?

This distinction matters because many financially dangerous errors look superficially plausible. A wrong unit, a wrong year alignment, or a misread context can create a candidate row that looks “clean enough” to non-specialists. Without a trust layer, those rows are likely to be over-promoted.

DateFac therefore reframes the project from “How good is the parser?” to “How disciplined is the system once parser output exists?”

## 4. Architecture

The current reviewed-preview path can be summarized like this:

```text
Input PDFs / Cached Parser Outputs
    -> candidate extraction and preparation
    -> sidecar trust routing
    -> trusted preview / review_required preview
    -> human unit review queue
    -> dry-run apply plan
    -> reviewed preview refresh
    -> demo packaging
    -> demo release audit
```

Several design choices are important here.

### 4.1 Sidecar instead of production mutation

The current late-stage demo work deliberately avoids production write-back. That allows the project to demonstrate controlled trust and review logic without pretending that official outputs are already safe to mutate automatically.

### 4.2 Human review before any future write-back conversation

The project treats human review as a first-class control. It does not hide manual review outcomes or collapse them into invisible post-processing. Human feedback is isolated, explicitly interpreted, and then surfaced into preview form only after a dry-run stage.

### 4.3 Preview refresh instead of baseline overwrite

The 330K4 stage creates a reviewed preview rather than overwriting the 330L baseline workbook. This matters because it keeps the baseline state inspectable and makes the effect of manual review explainable.

### 4.4 Documentation as part of system safety

The 332A release audit shows that documentation is not treated as an afterthought. Public-facing claims are audited for consistency and overclaim risk. This is not a cosmetic decision. It prevents the engineering work from being misrepresented.

## 5. Trust-Routing Design

The trust-routing design is one of the strongest parts of the current project story. It explicitly avoids the common anti-pattern of promoting everything that looks plausible.

Instead, the system distinguishes between:

- trusted preview rows
- review-required rows
- rows rejected after human review

That separation creates three benefits:

1. It preserves uncertainty instead of flattening it.
2. It makes manual review targeted rather than random.
3. It keeps the preview honest by showing what was not trusted.

Trusted, in this project, should be understood as “safe enough for the current preview state under the current evidence and review boundaries.” It should not be read as “universally correct forever.”

## 6. The Human Review Loop

The current human review loop is implemented through `330K2`, `330K3`, and `330K4`.

### 6.1 330K2: human unit review package

This stage packages the relevant unit-risk rows into a workbook for manual inspection. The purpose is not to fix parser quality directly. The purpose is to isolate the rows that are risky specifically because of unit ambiguity or unit conflict.

### 6.2 330K3: human unit review apply simulation

This stage reads the filled review workbook and maps reviewer decisions to dry-run actions. The important idea is that human decisions are first converted into a plan, not an automatic mutation.

### 6.3 330K4: reviewed export refresh

This stage refreshes the preview state according to the dry-run plan. The current reviewed outcome is:

- original trusted preview row count: 96
- reviewed unit-confirmed count: 2
- reviewed trusted preview row count: 98
- human rejected row count: 18
- remaining review-required row count: 1

Those numbers tell a useful story. The system did not magically absorb every risky row. It promoted two reviewed-safe rows, kept eighteen out of trusted preview, and left one unresolved. That is conservative and credible.

### 6.4 335A: client-facing clean export

The 335A stage does not change the underlying review decisions. It takes the reviewed preview and reorganizes it into a cleaner workbook that is easier for non-engineering readers to inspect. Its current customer-facing counts are:

- core metrics reviewed row count: 98
- needs review row count: 1
- excluded or rejected row count: 18
- source trace row count: 117

This matters because it improves readability without crossing the boundary into client-ready delivery or production write-back.

## 7. Stage Timeline From Stage 1 To 335A

### 7.1 Stage 1 to Stage 4

The earlier stages were focused on structured repair and governance rather than the current reviewed-preview packaging flow. Their value was foundational:

- establish guarded repair discipline
- prove rebuildability
- separate official assets from temporary sidecar work
- formalize governance rules

These stages matter because they created the habits that make later demo claims believable.

### 7.2 330L to 332A

The later demo-oriented stages build the current public story:

- `330L` created the baseline client-style export preview
- `331A` packaged that baseline into a demo-ready narrative with unit review caveats
- `330K2` isolated the 21 unit-review rows for manual review
- `330K3` simulated the effect of those manual decisions without write-back
- `330K4` refreshed the reviewed preview state
- `331B` refreshed the demo packaging to match the reviewed preview
- `332A` audited the entire story for consistency and overclaim risk
- `335A` generated a cleaner customer-facing preview workbook from the reviewed preview state

The value of this timeline is not just chronological clarity. It shows that the project has a disciplined transition from parser-adjacent preview logic to human review, then to refreshed preview, and finally to audited public explanation.

## 8. Current Metrics

The current clean-preview state is summarized by the following metrics:

| Metric | Value |
|---|---:|
| unfamiliar PDFs | 13 |
| PDFs produced candidates | 7 |
| `prepared_candidate_row_count` | 117 |
| `original_trusted_sheet_row_count` | 96 |
| `reviewed_unit_confirmed_count` | 2 |
| `reviewed_trusted_preview_row_count` | 98 |
| `core_metrics_reviewed_row_count` | 98 |
| `needs_review_row_count` | 1 |
| `excluded_or_rejected_row_count` | 18 |
| `source_trace_row_count` | 117 |
| `human_rejected_row_count` | 18 |
| `remaining_review_required_after_unit_review_count` | 1 |
| `apply_plan_row_count` | 21 |
| `source_page_missing_count` | 0 |
| `overclaim_risk_count` | 0 |
| `qa_fail_count` | 0 |

These values should remain consistent across README, overview docs, runbooks, and interview materials. If they drift, the documentation is no longer trustworthy.

## 9. Safe Claims

The project can currently and safely claim that:

- it supports financial research PDF core metric candidate preparation
- it preserves provenance for review-sensitive rows
- it performs sidecar trust-routing
- it detects unit-related risk
- it packages manual unit review workbooks
- it creates no-write-back dry-run apply plans
- it refreshes a reviewed preview state
- it generates a cleaner client-facing preview workbook while preserving source traceability
- it packages the current state into demo-facing materials
- it audits public-facing documentation for overclaim risk

These are meaningful claims. They are also careful claims.

## 10. Unsafe Claims

The project should not claim any of the following:

- direct client delivery readiness
- production deployment completion
- automatic correctness without human review
- fully automated commercial system maturity
- guaranteed extraction certainty
- customer-facing SaaS readiness
- direct investment-decision suitability

The reason is simple: these statements are inconsistent with the actual current state.

## 11. Interview Talking Points

The best interview framing for DateFac is not “we built a parser.” The better framing is:

1. parser quality alone is not enough because trust depends on provenance, units, and review boundaries
2. the project deliberately separates trusted, review-required, and rejected states
3. manual unit review exists because financially plausible outputs can still be unsafe
4. human decisions are converted into dry-run actions before they affect preview state
5. the demo narrative itself is audited so that presentation does not outrun engineering reality

This framing is strong because it highlights judgment, not just automation.

## 12. Commercial Trial Boundary

If this project is ever used in a small trial or highly supervised pilot, the honest positioning is:

- human-in-the-loop
- preview-oriented
- no write-back
- bounded scope
- explicit documentation of rejected and unresolved rows

That can still be valuable. It may be enough for an internal proof-of-concept or a tightly supervised trial. But it is not the same as a production-grade client delivery system, and it should not be presented that way.

## 13. Current Limitations

To keep the overview aligned with the README and runbook, it is useful to state the current limitations directly.

Current limitations include:

- the path is still a sidecar reviewed preview flow
- the current clean export is still a preview artifact rather than a final delivery export
- the project still enforces a no write-back boundary
- parser quality remains an upstream bottleneck
- the benchmark scope is still limited relative to real production expectations
- deployment, security, permissions, monitoring, and data-isolation work remain unfinished

These limitations do not reduce the engineering value of the project. They define the honest scope of that value.

## 14. Why 331A To 331B Matters

The transition from 331A to 331B is important because it shows the project doing more than static packaging.

331A showed a demo-ready baseline with unit review caveats.

331B showed what changed after:

- packaging unit-risk rows for human review
- simulating the effect of those decisions
- refreshing the reviewed preview
- updating demo materials accordingly

This is a better engineering story than a one-off export because it demonstrates a feedback loop. The project is not only generating a preview. It is showing how controlled human review changes the preview state without breaking safety boundaries.

## 15. Final Positioning

The strongest honest description of DateFac today is this:

It is a sidecar trust-routing, reviewed-preview, and client-facing clean-preview demo for financial research PDF extraction that emphasizes provenance, manual review boundaries, dry-run simulation, and audited public documentation. Its current state is `CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY`. It is not client-ready. It is not production-ready. It does not perform production write-back. Its value lies in making the trust problem visible and manageable, not in pretending that the trust problem has already disappeared.
