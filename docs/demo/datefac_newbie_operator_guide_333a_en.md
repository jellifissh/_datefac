# DateFac Newbie Operator Guide 333A (English)

## 0. Who This Guide Is For

This guide is written for a person who owns or operates the project but did not originally build every stage of it. You may be comfortable opening Excel files, reading JSON summaries, running PowerShell commands, and browsing project folders, but you should not have to reverse-engineer the entire repository just to understand what the current demo path does. The goal of this document is to make the current project usable by a careful new operator without pretending that the project is already a production system.

This guide is intentionally plainspoken. It does not try to impress you with marketing language. It tries to help you answer practical questions:

- What does DateFac actually do?
- Why is this harder than “extract numbers from PDFs”?
- What is trusted, what is review-required, and what is rejected?
- Why does unit review exist as a separate step?
- What is dry-run apply and why does it matter?
- What is a reviewed preview?
- What is demo packaging?
- What is release audit?
- Which files matter most?
- Which files should not be touched casually?
- What goes in and what comes out at each stage?
- How do I read the workbooks?
- How do I fill reviewer fields safely?
- Why can this support a guarded demo workflow while still falling short of production-grade readiness?

If you only remember one principle from this document, remember this: the current DateFac path is a sidecar demo and preview flow with human review and no write-back boundaries. It is not a claim that the project is ready for client delivery or ready for live production use.

## 1. What The Project Actually Does

DateFac is not simply “a parser for financial PDF tables.” It is a project that sits around parser output and organizes the trust problem that begins after extraction. Once a parser has read text and table fragments from financial research PDFs, you still need to answer several difficult questions:

- Is this row really the metric we think it is?
- Is the value aligned with the right year column?
- Is the unit explicit, missing, or conflicting?
- Is there enough evidence to trust the row for a preview export?
- Should the row be isolated for human review instead of being promoted automatically?
- If a human later reviews the row, how do we simulate the effect of that decision without writing back into official assets?
- How do we present the current state honestly on GitHub, in interviews, or in project docs without overclaiming?

DateFac addresses those questions with a sequence of sidecar stages. The project uses extracted candidate rows, retains provenance, routes them into trusted versus review-required buckets, packages risky rows for manual review, turns manual decisions into dry-run actions, refreshes a reviewed preview, and then packages that preview into a demo narrative that is audited for overclaim risk.

That is why the project is interesting from an engineering perspective. It is not only about parsing. It is about trust, review boundaries, controlled preview state, and honest public presentation.

## 2. Why Financial PDF Extraction Cannot Rely On The Parser Alone

This is one of the most important concepts in the whole project.

Many people new to this area assume that once OCR and table detection are “good enough,” the problem is basically solved. That is not true in financial research documents. A parser can tell you what text seems to exist and what table structure seems to exist. It cannot, by itself, guarantee that a candidate row is safe to treat as trusted.

Here are common failure patterns:

- A row looks like EPS, but the numeric value actually belongs to a neighboring peer-comparison column.
- A unit is missing, but the value only makes sense if a human checks the source context.
- A year token is mistaken for a data value.
- A peer table or chart annotation is mistaken for a core forecast table.
- A candidate row preserves enough text to look convincing, while still lacking the evidence needed to treat it as trusted.

The parser layer is still valuable. Without it, there is nothing to route or review. But parser quality alone is not the same as output trustworthiness. DateFac is built around that distinction. It does not deny that parser quality matters. It simply refuses to pretend that parser quality solves the whole problem.

## 3. Trusted, Review-Required, And Rejected

The current demo flow depends on three practical states.

### Trusted

In DateFac, trusted does not mean “perfect forever.” It means that under the current evidence, current routing logic, and current demo boundaries, a row is safe enough to appear in the trusted preview. It is still a preview state. It is not a production truth claim. That distinction matters.

### Review-Required

Review-required means that the system believes the row is too risky to promote automatically. Common reasons include:

- missing unit
- conflicting unit clues
- ambiguous row text
- weak provenance context
- uncertainty about year alignment
- evidence that looks incomplete or mixed with noise

The project would rather leave a row in review-required than pretend it is safe. That is a deliberate engineering choice, not a weakness.

### Rejected

Rejected, in the current 330K2 through 330K4 flow, typically means that after human review the row should not be surfaced into the trusted preview. A rejected row is not hidden. It is kept visible in the reviewed state as something the system chose not to promote. This is actually a strength. It shows that the project can say “no” instead of quietly padding trusted results.

## 4. What Unit Review Means

Unit review is a manual review stage focused specifically on unit-related risk. That may sound narrow, but unit mistakes are extremely dangerous in financial data. A value can be numerically correct and still be operationally wrong if the unit is wrong or unknown.

Examples:

- `RMB_mn` versus `RMB_bn`
- `percent` versus `times`
- `RMB/share` versus `RMB_mn`
- a row that lacks any explicit unit and needs source context

The point of unit review is not to “fix everything.” The point is to isolate a very important class of risk and make it human-reviewable in a controlled workbook. It is also important to understand what unit review is not:

- it is not rerunning the parser
- it is not changing the production pipeline
- it is not writing into official assets
- it is not pretending the row is safe just because a guess seems plausible

It is a review boundary. That is why it matters.

## 5. What Dry-Run Apply Means

Dry-run apply is the stage where human review decisions are translated into simulated actions without write-back.

This idea is central to the current project. The system does not say, “A human filled a workbook, so let us directly mutate the official result.” Instead it says, “Let us first model what would happen if we respected that human decision.”

In the current flow, manual review decisions map to dry-run actions such as:

- `CONFIRM_UNIT -> WOULD_CONFIRM_OR_SET_UNIT`
- `REJECT_UNIT -> WOULD_REJECT_FROM_TRUSTED_EXPORT`
- `KEEP_UNIT_UNKNOWN -> WOULD_KEEP_UNIT_UNKNOWN_REVIEW_REQUIRED`
- `NEEDS_MORE_CONTEXT -> WOULD_KEEP_REVIEW_REQUIRED_FOR_SOURCE_CHECK`

Why is this valuable?

1. It creates an explicit plan instead of an implicit mutation.
2. It preserves the no write-back boundary.
3. It lets you inspect counts and decisions before treating them as refreshed preview state.
4. It keeps the reviewed preview explainable.

If you are operating the project, do not confuse an apply plan with a production update. It is a simulation artifact. That limitation is a feature, not a bug.

## 6. What A Reviewed Preview Is

A reviewed preview is the refreshed preview state generated after human review outcomes are interpreted through the dry-run apply plan. It exists so that the project can show how manual review changes the trust view without overwriting the original baseline export.

The simplest mental model is:

- 330L = baseline client-style preview before manual unit review outcomes are applied
- 330K4 = reviewed preview after manual unit review outcomes are reflected through the dry-run simulation

The current reviewed preview numbers are:

- original trusted preview rows: 96
- reviewed unit-confirmed rows added or surfaced: 2
- reviewed trusted preview rows: 98
- human-rejected rows isolated from trusted preview: 18
- remaining review-required rows after unit review: 1

This is a strong engineering story because it shows that the project did not simply “clean everything up.” It made two rows stronger, kept eighteen rows out of trusted preview, and left one row unresolved. That is much more believable than magically promoting every row.

## 7. What Demo Packaging Means

Demo packaging is the step where project state is turned into reviewer-facing and interviewer-facing documentation. Internal JSON summaries are useful for developers, but not enough for outsiders. A GitHub visitor, project reviewer, interviewer, or future operator needs narrative materials:

- overview
- resume bullets
- README support
- demo script

In this project:

- 331A packaged the earlier 330L preview state
- 331B refreshed the narrative after human unit review and reviewed preview refresh

Demo packaging is not fluff. It is part of the system boundary. A preview project can still mislead people if its public-facing docs overclaim. Packaging therefore has to be conservative and consistent.

## 8. What Release Audit Means

Release audit is the final documentation check. It does not change parser results. It does not change official assets. It does not write back. It audits the narrative itself.

The release audit asks questions such as:

- Do all required docs exist?
- Do the metrics match across overview, resume bullets, README section, and demo script?
- Do the docs consistently say the project is not ready for client delivery and not ready for live production use?
- Do the docs avoid false claims about certainty or live deployment readiness?
- Do the docs mention preview, sidecar, no write-back, and human review boundaries?

This matters because public claims can outrun engineering reality very easily. A conservative system can still become a misleading project if the docs are sloppy. DateFac explicitly treats documentation integrity as part of engineering quality.

## 9. Which Files Matter Most

If you are new to the project, you should build familiarity in layers.

### First layer: root and docs

- `README.md`
- `docs/demo/`
- `docs/codex_tasks/`

These tell you what the project is trying to do, what each stage means, and what is safe to say publicly.

### Second layer: runners

- `tools/run_human_unit_review_330k2.py`
- `tools/run_human_unit_review_apply_simulation_330k3.py`
- `tools/run_reviewed_export_refresh_330k4.py`
- `tools/run_demo_packaging_331b.py`
- `tools/run_demo_release_audit_332a.py`

These runners tell you what each stage expects as input and what it writes as output.

### Third layer: trust modules

- `datefac/trust/*.py`

These implement the sidecar logic behind packaging, apply simulation, preview refresh, demo packaging, and audit.

### Fourth layer: outputs

- `output/client_style_export_preview_330l`
- `output/human_unit_review_330k2`
- `output/human_unit_review_apply_simulation_330k3`
- `output/reviewed_export_refresh_330k4`
- `output/demo_packaging_331b`
- `output/demo_release_audit_332a`

These output directories are where you actually inspect the current state.

## 10. Which Files You Should Not Touch Casually

There are several categories of files that should not be modified just because you are trying to “make the demo look cleaner.”

### Official assets

- `data/overrides/semantic_alias_candidates.json`
- `data/mapping/formal_scope_rules.json`

These are protected assets. The current demo path is not the place to edit them casually.

### Production pipeline, parser, extraction, and delivery files

The 330L to 332A path is intentionally a sidecar flow. Do not blur the scope by touching core pipeline code during a documentation or preview task unless there is a separate and justified change request.

### Protected dirty files

The repository already has specific dirty paths that must remain untouched and unstaged in these tasks. If you do not know why a file is dirty, that is exactly why you should not stage it.

### Output artifacts

The `output/*` tree is run output, not source code. It is useful to inspect. It is not normally what you commit.

## 11. What Goes Into Each Stage

Here is the input flow in operator language.

### 330K2 inputs

- demo packaging output from 331A
- baseline preview output from 330L
- unit signal review context
- delivery report refresh context

This stage packages review rows. It does not read a filled workbook yet.

### 330K3 inputs

- the 330K2 output directory
- the manually filled review workbook
- baseline demo packaging context
- baseline preview context

This stage converts human decisions into dry-run actions.

### 330K4 inputs

- baseline 330L preview
- 330K2 review package
- 330K3 apply simulation

This stage refreshes preview state.

### 331B inputs

- 331A demo packaging
- 330K4 reviewed export refresh
- 330K3 apply simulation
- 330K2 review package
- 330L preview

This stage refreshes public-facing docs.

### 332A inputs

- 331B demo packaging
- 330K4 reviewed export refresh
- 331A demo packaging
- current demo docs

This stage audits the final narrative.

## 12. What Comes Out Of Each Stage

### 330K2 outputs

Main artifacts:

- review template workbook
- summary JSON
- manifest JSON
- QA JSON
- no-apply proof JSON
- report markdown

Most operators will first open the review workbook and the summary JSON.

### 330K3 outputs

Main artifacts:

- apply plan JSON
- apply plan workbook
- summary JSON
- manifest JSON
- QA JSON
- no-apply proof JSON

This is where you understand how human review decisions would affect the preview state.

### 330K4 outputs

Main artifacts:

- reviewed preview workbook
- summary JSON
- manifest JSON
- QA JSON
- no-apply proof JSON

This is the most important place to see the new trust picture after manual review.

### 331B outputs

Main artifacts:

- summary JSON
- overview doc
- resume bullets doc
- GitHub README section doc
- demo script doc

This is where technical state becomes presentation material.

### 332A outputs

Main artifacts:

- summary JSON
- checklist markdown
- report markdown
- release checklist doc
- interview talking points doc

This is where narrative safety is checked.

## 13. How To Read The Excel Files

A new operator often opens a workbook and looks at the first visible number. That is a mistake. The right reading order is:

1. sheet name
2. candidate identifier
3. metric and year
4. current unit and risk flags
5. source page and evidence text
6. reviewer fields or dry-run action

The workbook is not just a value table. It is a review tool. If you ignore provenance and decision columns, you lose the entire point of the sidecar design.

### Baseline preview workbook

Use it to understand:

- trusted baseline
- review-required baseline
- sample rows requiring unit review

### Human review workbook

Use it to decide:

- whether a unit can be confirmed
- whether the row should be rejected
- whether it must remain unknown
- whether more context is needed

### Reviewed preview workbook

Use it to compare:

- what stayed trusted
- what was added to reviewed trusted preview
- what was rejected
- what remains unresolved

## 14. How To Understand The 330K2 Human Unit Review Workbook

The 330K2 review workbook is a controlled queue, not a general spreadsheet for ad hoc edits. Each row is effectively asking:

“Given the evidence we have, what should happen to this unit-risk candidate?”

You should pay particular attention to:

- `candidate_id`
- `pdf_document_id`
- `metric`
- `year`
- `value`
- `current_unit`
- `source_page`
- `source_evidence_text`
- `reviewer_unit`
- `reviewer_decision`
- `reviewer_notes`

The key mindset is not “pick the nicest answer.” The key mindset is “make the most defensible judgment based on the visible evidence.”

## 15. How To Fill `reviewer_unit`, `reviewer_decision`, And `reviewer_notes`

### `reviewer_unit`

Only fill a specific unit if the evidence supports it. If the unit is truly unclear, do not invent confidence.

### `reviewer_decision`

Allowed values are:

- `CONFIRM_UNIT`
- `REJECT_UNIT`
- `KEEP_UNIT_UNKNOWN`
- `NEEDS_MORE_CONTEXT`

Use them literally and carefully. Do not improvise new decision strings.

### `reviewer_notes`

This field should explain why the decision is defensible. Good notes are short, factual, and traceable. For example:

- “Value belongs to peer-comparison section, not core EPS forecast row.”
- “Percent unit is supported by evidence text and metric convention.”
- “Need source table check because extracted token may be a year header.”

Bad notes are vague emotional impressions like “feels wrong” or “not sure.”

## 16. What 330K3, 330K4, 331B, And 332A Each Do

If these stages blur together for you, use the following shorthand:

- 330K3 turns human review into a dry-run action plan.
- 330K4 turns the dry-run action plan into a refreshed reviewed preview.
- 331B turns the reviewed preview into public-facing demo documentation.
- 332A checks whether those documents are accurate, bounded, and not overclaiming.

That is the whole late-stage demo chain in one line.

## 17. What To Check First When Something Goes Wrong

Do not begin by assuming the code is broken. Check the simpler failure points first.

1. Does the upstream output directory exist?
2. Does the expected summary JSON exist?
3. Does the summary say the previous stage is ready?
4. Did you point to the correct workbook path?
5. Are you mixing the 330L baseline preview with the 330K4 reviewed preview?
6. Are you reading 331A docs when you meant to read 331B docs?
7. Did the manual workbook actually get filled?
8. Did someone introduce an unstaged local change that shifts the working state?

This order saves time because many “logic bugs” turn out to be path, version, or staging mistakes.

## 18. What Is Safe To Show On GitHub

The safest showcase materials are the documentation artifacts that already explain boundaries clearly:

- the main README
- the 331B demo overview
- the 331B resume bullets
- the 331B GitHub README section
- the 331B demo script
- the 332A release checklist
- the 332A interview talking points
- the 333A bilingual operator docs

These are safe because they present the project as a demo preview with human review boundaries and no write-back claims.

## 19. What Is Safe To Say In Interviews

Good interview framing includes:

- parser quality is necessary but not sufficient
- trust-routing is a separate engineering concern
- unit review exists because financially plausible values can still be unsafe
- human review is intentionally isolated before any write-back discussion
- the project demonstrates disciplined preview refresh, not blind automation
- 331A established the demo baseline and 331B showed the reviewed preview after manual feedback

These are strong claims because they are true and grounded in the current artifacts.

## 20. What You Must Not Claim

Avoid claims such as:

- direct client delivery readiness
- live production deployment completion
- guaranteed correctness
- no remaining need for human review
- suitability for direct investment action
- customer-facing SaaS maturity
- fully automated commercial-system readiness

These claims are forbidden not because they sound bold, but because they contradict the current engineering state.

## 21. How This Could Be Used In A Small Human-Supervised Trial

The current project can support a narrow, human-supervised demonstration or internal trial if the scope is framed honestly:

- small sample size
- human in the loop
- preview-only outputs
- no write-back
- clear documentation of rejected and unresolved cases

That is very different from saying the system is ready for large-scale unattended client delivery.

## 22. Why It Can Support A Guarded Demo While Still Short Of Production-Grade Readiness

This is a subtle but important distinction.

The project can support a guarded demo because it already has several valuable controls:

- provenance-aware candidate handling
- trust-routing separation
- explicit unit review packaging
- dry-run apply simulation
- reviewed preview refresh
- conservative demo packaging
- release audit

But it is still short of production-grade readiness because production readiness requires more than a good demo flow. It requires:

- broader real-world benchmarking
- stronger operational tooling
- deployment design
- security design
- data isolation
- permissions
- monitoring
- recovery procedures
- client-facing export standards

A good demo is evidence of engineering progress. It is not the same thing as a production system.

## 23. Current Limitations

This section deliberately keeps the exact phrase “current limitations” visible because that phrase should appear consistently across the README, runbook, overview, and demo explanations.

The current limitations include:

- the path is still a sidecar demo preview
- the project still enforces a no write-back boundary
- parser quality remains an upstream bottleneck
- workbook-based human review is still operator-heavy
- the reviewed preview is not the same thing as a clean client-facing final export
- the benchmark scope is still narrower than what a production claim would require
- deployment, security, permissions, and data-isolation work remain unfinished

Those limitations do not erase the value of the project. They define the honest boundary around that value.

## 24. Recommended Next Engineering Steps

If you want to push the project forward responsibly, the next steps should look something like this:

1. improve the clarity of client-facing preview exports
2. expand the benchmark set beyond the current unfamiliar PDFs
3. reduce manual friction in the review workflow
4. collect stronger dry-run evidence before even discussing write-back promotion
5. design production-safe deployment, security, and data-isolation boundaries

These are pragmatic steps. They build on the current architecture instead of pretending the architecture has already finished.

## 25. Final Takeaway

The current value of DateFac is not “we fully automated financial PDF delivery.” The value is that the project clearly separates what can be trusted now, what still needs review, what was rejected after review, what can be shown as a preview, and what must not be claimed publicly. That makes it a credible engineering demo and a good discussion project. It does not make it a production release.
