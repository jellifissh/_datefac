# 348 Agent Pivot Brief

## 1. Decision

DateFac will pivot from a primary focus on full-scale PDF table extraction to a financial document extraction audit agent.

The new direction is:

```text
Financial Document Extraction Audit Agent
```

Chinese positioning:

```text
金融文档 AI 抽取结果审计与可信交付 Agent
```

This is not a full project reset. Existing extraction, quality audit, semantic unit guardrail, lineage, evidence binding, and human review work will be reused as the audit engine of the new agent workflow.

---

## 2. Why pivot now

Recent manual testing on the Anjoy Foods research report showed that general large-model app products can already extract the core financial tables from this type of PDF with very high quality.

That changes the project economics:

- Full PDF table extraction is becoming commoditized.
- Competing directly with general VLM / LLM apps on raw extraction quality is no longer the best use of project time.
- The higher-value problem is whether extracted financial data is correct, traceable, auditable, and ready for delivery.

Therefore, the extraction layer should become pluggable, while DateFac should move upward into audit, validation, orchestration, and trusted delivery.

---

## 3. Old vs new positioning

### Old positioning

```text
Financial PDF table extraction and structured export system
```

Main question:

```text
Can we extract tables from financial PDFs ourselves?
```

### New positioning

```text
Financial document AI extraction audit agent
```

Main question:

```text
Given PDF, LLM/MinerU/App-generated Excel, or other extracted artifacts, can the agent verify whether the data is correct, complete, traceable, and safe to deliver?
```

---

## 4. What is paused

The following work should no longer be treated as the highest-priority mainline:

- Full-scale recovery on old MinerU outputs.
- Continuing 346B6 immediately as the main task.
- More fine-grained recovery rules whose only purpose is to rescue old extraction output.
- Treating MinerU or any single parser as the core moat.

These items are not deleted. They are downgraded to supporting assets or fallback branches.

---

## 5. What is retained

The following DateFac assets remain valuable and should be reused:

- 345D full structured demo export package.
- 346B series quality-limited recovery experiments.
- 346B3 / 346B3R semantic-class-aware unit policy.
- 346B4 / 346B4R controlled replay validation.
- 346B4Q / 346B5Q independent QA audit pattern.
- Lineage and evidence binding logic.
- Human review package design.
- Guardrails around ratio, percentage, per-share, monetary, and valuation metrics.
- Demo-only / sidecar-only safety posture.

These become the audit and trust layer of the new agent.

---

## 6. New product shape

The agent should support this workflow:

```text
PDF / research report / financial report
+
LLM-app extracted Excel / MinerU output / manually prepared spreadsheet

↓

Agent intake

↓

Metric normalization
Unit and period alignment
Financial semantic checks
Evidence lookup against PDF text/images
Cross-source comparison
Risk classification
Human review queue generation

↓

Clean data table
Audit report
Review queue
Evidence index
```

The agent does not need to be a general-purpose chatbot. It should be a task-focused financial document audit agent.

---

## 7. Target MVP

The next practical milestone should be:

```text
348A AI-Extracted Excel Intake Audit Agent Pilot
```

Initial input candidates:

```text
H3_AP202606081823352906_1_331fresh_20260615_21591.pdf
安井食品研报数据汇总.xlsx
```

348A should not re-extract the PDF from scratch. It should audit the already extracted Excel against the PDF.

Minimum checks:

- Whether each Excel table can be mapped to a PDF page or section.
- Whether year columns such as 2024A / 2025A / 2026E / 2027E / 2028E are complete and aligned.
- Whether units are correct: 百万元, 元, %, 倍, 元/股, etc.
- Whether valuation metrics such as P/E, P/B, EV/EBITDA are not misclassified as percentages.
- Whether per-share metrics are not treated as total monetary amounts.
- Whether key metrics such as revenue, net profit, EPS, ROE, gross margin, net margin, PE, PB are missing or duplicated.
- Whether suspicious rows should be sent to human review.

Expected outputs:

```text
clean_data.xlsx
audit_report.md
review_queue.xlsx
evidence_index.json
```

---

## 8. Agent architecture draft

### 8.1 Extractor layer

Pluggable sources:

- LLM app exported Excel.
- MinerU 3.3.1 output.
- Old MinerU output.
- Manual spreadsheet.
- Future OCR/VLM tools.

### 8.2 Agent orchestrator

Responsibilities:

- Identify input type.
- Route to the correct audit tool.
- Decide whether PDF evidence is needed.
- Decide whether human review is needed.
- Generate final delivery artifacts.

### 8.3 Audit tools

Reusable tool modules:

- Metric alias normalization.
- Unit semantic checker.
- Period/year alignment checker.
- Numeric value sanity checker.
- Financial statement table classifier.
- Valuation metric checker.
- Evidence locator.
- Human review queue builder.

### 8.4 Delivery layer

Outputs:

- Clean structured Excel.
- Audit summary.
- Risk-tagged review queue.
- Evidence index.
- Optional report narrative.

---

## 9. MinerU 3.3.1 role after pivot

MinerU 3.3.1 remains important, but its role changes.

It should be treated as:

```text
sidecar extraction engine / high-precision recovery source
```

not:

```text
single main parser that defines the whole project
```

347A MinerU 3.3.1 Side-by-Side Compatibility Benchmark can continue as a parallel evaluation branch. Its output should inform which extractor sources the agent can trust or route to, but it should not block the agent pivot.

---

## 10. Recommended next milestones

```text
348A AI-Extracted Excel Intake Audit Agent Pilot
348B Agent Tool Router
348C PDF Evidence Checker
348D Human Review Queue Generator
348E End-to-End Demo Package
```

346B6 Full Quality-Limited Recovery Expansion is paused unless it becomes useful as an audit benchmark or regression test.

347A MinerU 3.3.1 benchmark remains useful as a side branch.

---

## 11. Non-goals

Do not build a generic chat assistant.

Do not build another broad all-purpose agent demo.

Do not compete with frontier models on raw table extraction.

Do not discard existing DateFac audit work.

Do not immediately rewrite the whole repository.

---

## 12. One-sentence summary

DateFac should stop trying to make PDF table extraction itself the core moat and should become a financial document AI extraction audit agent that turns model-extracted data into trustworthy, traceable, reviewable, and deliverable financial data assets.
