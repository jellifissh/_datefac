# DateFac Tactical Cleaning Playbook

> This file is intentionally placed at repository root so the cleaning strategy is visible before opening implementation details.
>
> Core idea: DateFac is not just a PDF table extractor. It is a financial PDF table extraction, evidence binding, quality grading, and controlled recovery system.

## One-line strategy

```text
MinerU provides structured text and visual evidence.
DateFac turns those raw materials into auditable, quality-graded, evidence-backed financial data.
```

Do not treat MinerU output as final clean data. MinerU output is raw material: JSON/Markdown/table images/page images/bbox/context. DateFac must clean, inherit context, bind evidence, repair carefully, and re-audit.

---

## Current quality posture

The current demo export split is:

```text
demo-ready rows       = 109
quality-limited rows  = 5558
excluded rows         = 9121
total inventory rows  = 14788
```

Interpretation:

```text
109 rows can be shown as strict demo-ready samples.
5558 rows are the main recovery target.
9121 rows are frozen/archive-first rows and should not consume cleaning effort now.
```

This does **not** mean only 109 rows were extracted. It means 14,788 candidate rows were extracted and then quality-graded.

---

## Tactical doctrine

### 1. Freeze excluded rows

Do not spend active cleaning effort on the 9,121 excluded rows by default.

Treat them as archived dirty data:

```text
archive_excluded_rows
```

Keep:

```text
source_pdf
source_page
source_table_id
raw_text
raw_metric_name
value
exclude_reason
quality_issue_codes
demo_export_caveats
evidence pointers if available
```

Do not delete them. Do not prioritize them. They are kept for traceability, later sampling, and failure analysis.

---

### 2. Focus on quality-limited rows

The active battlefield is:

```text
quality_limited_rows = 5558
```

These rows are most likely to be upgraded because they often have useful structure but are blocked by fixable issues:

```text
missing or uncertain unit
uncertain period/header alignment
suspicious row/column alignment
weak source trace
value format noise
metric normalized but not yet strict-demo safe
```

The first recovery goal is not full production quality. The first goal is:

```text
quality-limited -> demo-ready candidate
```

---

### 3. Deterministic sanitizer first

Always clean deterministic value noise before using expensive or fuzzy methods.

Use Python deterministic cleaning for:

```text
(15.4)       -> -15.4
1,200.00     -> 1200
12.5%        -> normalized percent representation
\u200b        -> removed
\xa0          -> normalized whitespace
full-width spaces -> normalized whitespace
-- / — / N/A / 不适用 -> normalized missing-value markers
```

Recommended fields:

```text
raw_value
sanitized_value
value_parse_status
value_parse_error
value_numeric_type
```

Never overwrite the original value. Preserve raw, sanitized, and final values separately.

---

### 4. Context state machine second

Financial PDF tables often hide key meaning in surrounding context rather than the row itself.

Maintain layered context, not a single global variable:

```text
PDFContext
  PageContext
    TableContext
      HeaderContext
        RowContext
```

Context can include:

```text
source_pdf
page_number
table_id
table_title
statement_type
unit_context
currency_context
period_headers
period_type_headers
footnotes
nearby_text
bbox/page coordinates
```

Use context inheritance for:

```text
unit
currency
period
period_type
statement_type
source trace
```

Example:

```text
Table title says: 单位：亿元
Row says: 营业收入 | 150.2
Injected field: inherited_unit = 亿元
context_source = table_title
context_confidence = HIGH
```

Never inject context blindly across tables. A page may contain one table using `亿元`, another using `%`, and another using `倍`.

---

### 5. Text + image evidence binding third

Do not treat images as audit-only screenshots.

Treat MinerU outputs as a dual-source evidence system:

```text
JSON/Markdown = structured draft
Table/page images = visual evidence
```

Each recoverable row should become:

```text
row_with_evidence
```

Recommended evidence bundle fields:

```text
source_row_id
source_pdf
source_page
source_table_id
bbox
mineru_json_context
mineru_md_context
neighbor_rows
table_crop_image_path
page_image_path
image_resolution_status
```

Image evidence is especially useful for:

```text
table-level unit detection
multi-level header interpretation
period/header alignment
row/column alignment
value-cell verification
row type judgment: data row/header/subtotal/footnote
```

Image evidence should support decisions. It should not automatically replace structured text output.

---

### 6. Targeted VLM repair fourth

Use visual models only after cheaper methods fail.

VLM should be used only for high-value, bounded, evidence-backed rows:

```text
rules cannot decide
state machine confidence is low or medium
image evidence is available
row has recovery value
```

Ask narrow questions only:

```text
What is the table-level unit?
Which period/header does this value belong to?
Does this value cell align with this metric row and period column?
Is this row a data row, header row, subtotal row, or footnote?
Is there enough visual evidence to suggest a field repair?
```

Do **not** ask:

```text
Convert the whole table into JSON.
Fix all rows.
Decide all financial data is correct.
Overwrite the source data.
```

VLM output must be treated as suggestion, not truth:

```text
vision_suggestion
confidence
visual_evidence_note
requires_human_review
do_not_auto_apply = true
```

---

### 7. Human review for conflicts

Human review is required when:

```text
text and image evidence conflict
VLM confidence is LOW or MEDIUM for critical fields
VLM suggests changing value/period/unit with unclear visual support
row has financial importance but incomplete evidence
```

Human review should receive the full evidence bundle:

```text
raw row
sanitized row
context injection result
image evidence
VLM suggestion if any
conflict reason
```

---

### 8. Re-audit and re-rank

Every repaired row must be re-audited.

Possible outcomes:

```text
UPGRADE_TO_DEMO_READY_CANDIDATE
KEEP_QUALITY_LIMITED
DOWNGRADE_TO_EXCLUDED
NEEDS_HUMAN_REVIEW
```

A repair is not successful because a field was filled. A repair is successful only if the row passes the required quality gate for its target status.

---

### 9. Reconciliation only when applicable

Financial reconciliation is valuable, but it is not a universal judgment tool.

Use reconciliation for applicable statement types:

```text
balance_sheet
income_statement
cash_flow_statement
```

Examples:

```text
current_assets + non_current_assets ≈ total_assets
current_liabilities + non_current_liabilities ≈ total_liabilities
operating_revenue - operating_cost ≈ gross_profit
```

Do not force reconciliation onto:

```text
valuation tables
ratio tables
industry comparison tables
forecast summary tables
growth-rate tables
mixed research-report tables
```

Recommended fields:

```text
reconciliation_applicable
reconciliation_rule_id
reconciliation_passed
reconciliation_tolerance
reconciliation_fail_reason
```

Reconciliation is a post-cleaning validation layer, not the first cleaning layer.

---

### 10. Never overwrite source data

Always preserve source data and every transformation layer.

Recommended lineage fields:

```text
raw_value
sanitized_value
context_injected_value
vision_suggested_value
human_reviewed_value
final_value
decision_source
confidence
evidence_refs
repair_history
```

Do not mutate upstream 345D/345E/345F outputs, MinerU outputs, official normalization rules, or official alias assets during experiments.

---

## Standard cleaning flow

```text
quality-limited row
  ↓
Python deterministic sanitizer
  ↓
context state machine / inheritance
  ↓
text + image evidence binding
  ↓
targeted VLM repair suggestion if needed
  ↓
human review for conflicts / low confidence
  ↓
re-audit
  ↓
upgrade / keep limited / downgrade / review
```

Cost rule:

```text
If rules can fix it, do not spend model money.
If context can fix it, do not call VLM.
If image evidence is missing, do not ask VLM to hallucinate.
If VLM conflicts with source evidence, route to human review.
```

---

## Adopted tactics

| Tactic | Status | Layer | Warning |
|---|---|---|---|
| Python deterministic sanitizer | Required | First layer | Fixes format, not business meaning |
| Context state machine / inheritance | Required | Second layer | Must be scoped by PDF/Page/Table/Header |
| Text + image evidence binding | Required | Third layer | Images are evidence, not automatic replacements |
| Targeted VLM repair | Adopted | Fourth layer | Narrow field repair only, no full-table brute force |
| Human review | Required | Conflict fallback | Needed for low confidence and evidence conflicts |
| Financial reconciliation | Conditional | Post-cleaning validation | Only for applicable statement types |
| Excluded row freezing | Required | Strategy layer | Archive and trace, do not prioritize now |
| Full brute-force VLM extraction | Rejected by default | Prohibited default | Too slow, costly, and hallucination-prone |

---

## Near-term priority

The next practical recovery direction should answer:

```text
How many of the 5558 quality-limited rows can be upgraded using deterministic sanitizer + context inheritance + evidence binding before any live VLM cost is introduced?
```

Recommended next technical task:

```text
Quality-Limited Row Recovery Pilot
```

It should measure:

```text
quality_limited_row_count
sanitized_value_success_count
unit_injection_success_count
period_injection_success_count
evidence_bundle_success_count
needs_vlm_count
recovered_demo_candidate_count
still_quality_limited_count
downgraded_excluded_count
```

The project should prefer measurable recovery over vague claims about AI extraction quality.

---

## Non-negotiable boundaries

Do not claim:

```text
production_ready = true
client_ready = true
formal_client_export_allowed = true
official_rules_modified = true
```

unless an explicitly approved formal task changes those gates.

Default truth:

```text
demo_export_only = true
formal_client_export_allowed = false
client_ready = false
production_ready = false
global_strict_human_review_completed = false
```

This playbook is the tactical baseline for DateFac cleaning and recovery work going forward.
