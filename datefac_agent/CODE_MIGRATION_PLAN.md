# DateFac Agent Code Migration Plan

## 1. Purpose

This document defines how code should be moved from the legacy DateFac project into the new `datefac_agent/` foundation.

The goal is not to move everything.

The goal is to extract stable audit capabilities from legacy experiments and rebuild them as clean, reusable, agent-oriented modules.

## 2. Migration Rule

The core rule is:

```text
Move capabilities, not historical baggage.
```

Do not copy a whole old runner just because it contains one useful helper function.

Do not move old experiment files just because they once produced a useful output.

Do not bring hard-coded output paths into the new package.

## 3. What Can Be Migrated

The following capability types are migration candidates.

### 3.1 Metric Normalization

Old logic related to metric alias handling, canonical metric names, and financial indicator normalization may be migrated into:

```text
datefac_agent/audit/metric_normalizer.py
```

Expected future responsibilities:

- normalize metric aliases;
- detect ambiguous metric names;
- separate business metrics from valuation metrics;
- preserve original label and canonical label.

### 3.2 Unit Semantic Checking

Old logic for monetary, percentage, per-share, ratio, and multiple units may be migrated into:

```text
datefac_agent/audit/unit_semantic_checker.py
```

Expected future responsibilities:

- detect unit and metric semantic mismatches;
- prevent P/E or P/B from being treated as percentages;
- prevent EPS or per-share values from being treated as total monetary amounts;
- flag missing or suspicious units.

### 3.3 Period and Year Alignment

Old logic related to year columns, forecast years, historical years, period labels, and column alignment may be migrated into:

```text
datefac_agent/audit/period_alignment_checker.py
```

Expected future responsibilities:

- validate year columns such as 2024A / 2025A / 2026E;
- detect shifted or duplicated year columns;
- classify historical vs forecast periods.

### 3.4 Valuation Metric Checking

Old valuation-related guardrails may be migrated into:

```text
datefac_agent/audit/valuation_metric_checker.py
```

Expected future responsibilities:

- check P/E, P/B, EV/EBITDA, EPS and other valuation metrics;
- prevent valuation ratios from being mixed with percentage margins;
- detect suspicious valuation row types.

### 3.5 Evidence and Lineage Structures

Old evidence binding ideas may be migrated into:

```text
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
```

Expected future responsibilities:

- attach extracted values to source PDF page, table, image, or text evidence;
- flag missing evidence;
- preserve lineage for review and delivery.

### 3.6 Review Queue Logic

Old human review ideas may be migrated into:

```text
datefac_agent/review/review_queue_builder.py
datefac_agent/review/risk_classifier.py
```

Expected future responsibilities:

- classify PASS / REVIEW / FAIL;
- generate human review rows;
- explain why a row needs review.

### 3.7 Report Writing

Old QA report patterns may be migrated into:

```text
datefac_agent/delivery/audit_report_writer.py
```

Expected future responsibilities:

- write audit summaries;
- report issue counts;
- explain decision and limitations;
- produce review-friendly Markdown.

## 4. What Must Not Be Migrated During Foundation Stage

Do not migrate the following yet:

- old MinerU command runners;
- old 346B-specific runner scripts;
- old benchmark wrappers with hard-coded output paths;
- large output directories;
- old local temp files;
- old task-specific reports;
- one-off scripts that only replay historical outputs;
- code that mutates official assets without explicit review.

These remain legacy assets.

## 5. Suggested New Package Skeleton

The new package should eventually look like:

```text
datefac_agent/
  __init__.py
  intake/
  audit/
  review/
  delivery/
  orchestrator/
  schemas/
  llm/
```

The `llm/` directory is included only as a future isolation area for model clients, prompts, and response parsing. It should not become a place for hard-coded business logic.

## 6. Pure Function Principle

Audit modules should be as pure as possible.

A checker should generally follow this pattern:

```text
Input: structured record or table object
Output: AuditResult or list[AuditIssue]
```

Avoid inside checkers:

- file reads;
- file writes;
- API calls;
- console printing;
- direct mutation of global state;
- hidden dependency on output directories.

The orchestrator should handle workflow decisions. Audit tools should only audit.

## 7. Test Migration

The most valuable migration target is not only code.

It is also the error cases found in previous work.

The 346B series produced many useful failure examples:

- unit mismatch;
- ratio multiple vs percentage confusion;
- per-share vs monetary amount confusion;
- weak evidence;
- false-positive recovery risks;
- semantic class uncertainty;
- row lineage concerns.

These should become `tests/agent/fixtures` and unit tests over time.

The new system should prove that it can reject known bad cases, not merely process happy-path data.

## 8. Migration Stages

### Stage 1: Foundation Docs and Skeleton

- Create `datefac_agent/README.md`.
- Create project background and migration documents.
- Define what to keep and what to freeze.
- Do not move large code yet.

### Stage 2: Minimal Schemas

- Define `ExtractedMetric`.
- Define `EvidenceRef`.
- Define `AuditIssue`.
- Define `AuditResult`.
- Define `ReviewDecision`.

### Stage 3: Minimal Audit Tools

- Implement unit checker.
- Implement period checker.
- Implement valuation checker.
- Add unit tests using known bad cases.

### Stage 4: 348A Pilot

- Add Excel intake.
- Audit extracted spreadsheet against expected financial table patterns.
- Generate audit report and review queue.

## 9. Completion Criteria for Foundation Stage

Foundation stage is complete when:

- `datefac_agent/` has clear documentation;
- the pivot is documented;
- migration boundaries are clear;
- old code is not accidentally moved wholesale;
- next milestone 348A is ready to be implemented;
- protected dirty files and legacy output directories remain untouched.

## 10. One-Sentence Rule

Do not move old DateFac into `datefac_agent`; rebuild the reusable audit core inside `datefac_agent` using lessons from old DateFac.
