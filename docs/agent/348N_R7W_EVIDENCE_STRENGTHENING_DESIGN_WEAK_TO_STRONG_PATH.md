## Task ID

`348N-R7W evidence strengthening design: WEAK_EVIDENCE -> STRONG_EVIDENCE path`

## Task Type

documentation-only design task. No code, tests, output, input, or config was modified. No workbook reruns, MinerU, OCR, LLM, or VLM calls were made. One result report was created.

---

## Preflight

```text
git status -sb (before pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 6e8a5fc..da46f4c
  Fast-forward
   ...348N_R7W_evidence_strengthening_design_weak_to_strong_path.md | 350 +++++
   1 file changed, 350 insertions(+)

git status -sb (after pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation (clean)

git log --oneline -12:
  da46f4c docs: add R7W evidence strengthening task
  6e8a5fc docs: add R7V readiness review
  3206d7d docs: add R7V readiness review task
  b4a0ee9 docs: add R7U workbook regression review
  bb4ae21 docs: add R7U workbook regression task
  7a8f35a docs: add R7T Taihao rerun review
  0e9344c docs: add R7T Taihao rerun task
  8d1c063 docs: add R7S QA review
  b623c58 docs: add R7S QA task
  0e09901 fix: narrow strict table clean admission
  96fb1aa docs: add R7S implementation task
  fd2325b docs: add R7R clean-boundary design
```

Worktree was clean after pull.

---

## Files reviewed

Read-only review:

- `AGENTS.md`
- `.skills/README.md`, `.skills/git_workflow.md`, `.skills/datefac_agent_foundation.md`, `.skills/agent_excel_intake_audit_workflow.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/agent/项目进程.md`
- `项目进展大白话说明.md`
- `docs/agent/348N_R7V_CROSS_FAMILY_CLEAN_BOUNDARY_SUMMARY_AND_READINESS_REVIEW.md`
- `docs/agent/348N_R7U_LINYANG_ANJING_WORKBOOK_FAMILY_REGRESSION_CHECK.md`
- `docs/agent/348N_R7T_TAIHAO_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_PILOT_RERUN.md`
- `docs/agent/348N_R7S_QA_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_REVIEW.md`
- `docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md`
- `docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md`

Implementation and model files reviewed read-only to ground the design:

- `datefac_agent/audit/evidence_checker.py` (current evidence classification)
- `datefac_agent/schemas/audit_models.py` (EvidenceRef, SpreadsheetRow, AuditRowResult, EvidenceLevel)
- `datefac_agent/intake/excel_intake.py` (explicit_evidence_ref extraction, provenance fields)
- `datefac_agent/delivery/evidence_index_writer.py` (evidence index output shape)
- `datefac_agent/review/clean_candidate_policy.py` (clean admission interaction)
- `datefac_agent/review/review_queue_builder.py` (review routing)
- `tests/agent/test_agent_excel_intake_audit_348a.py` (existing evidence tests)

---

## Current evidence model

Evidence strength is classified in `datefac_agent/audit/evidence_checker.py::classify_evidence_level(...)`. The current model has three levels:

```text
STRONG_EVIDENCE   <- has_explicit: any evidence ref is_explicit, OR any ref.page_number is not None,
                     OR row.explicit_evidence_ref is non-empty
WEAK_EVIDENCE     <- has pdf identity + sheet identity + row_index > 0 + metric identity non-empty
                     + at least one workbook_row evidence ref
MISSING_EVIDENCE  <- otherwise (no usable lineage)
```

`build_evidence_refs(...)` constructs exactly two refs by default:

```text
1. source_type="source_pdf", source_id=<pdf_path>, locator=<sheet_name>, page_number=None, is_explicit=False
2. source_type="workbook_row", source_id="<sheet>:<row_index>", locator=<metric_name>, page_number=None, is_explicit=False
```

If `row.explicit_evidence_ref` is non-empty, a third ref is added:

```text
3. source_type="explicit_workbook_evidence", source_id=<explicit_evidence_ref>, locator=<metric_name>, is_explicit=True
```

So STRONG_EVIDENCE today is reached solely by having an explicit evidence reference (typically a page-number column in the workbook). No PDF parsing, no value agreement check, and no cell-address anchoring are performed.

`EvidenceLevel` is a Literal type: `"STRONG_EVIDENCE" | "WEAK_EVIDENCE" | "MISSING_EVIDENCE" | "NOT_APPLICABLE"`.

---

## Current provenance model

`SpreadsheetRow` carries these provenance-relevant fields:

```text
source_excel_path        : str            (workbook file path)
sheet_name               : str
row_index                : int            (1-based sheet row index)
column_names             : list[str]      (header row)
raw_values               : dict[str, Any] (cell values keyed by header)
metric_name              : str
unit_hint                : str | None
period_values            : dict[str, Any] (period label -> value)
explicit_evidence_ref    : str | None     (extracted from 页/page/evidence/source/出处/来源 columns)
row_type                 : RowType
```

`EvidenceRef` carries:

```text
source_type              : str
source_id                : str
page_number              : int | None     (always None today; never populated by the runner)
locator                  : str | None
is_explicit              : bool           (True only for explicit_workbook_evidence refs)
```

What the current provenance model does NOT carry:

```text
- Excel cell address (e.g. "B5", "C12") per value
- PDF source span / text coordinate / bounding box
- Page number as a structured int (explicit_evidence_ref is a free-text string, page_number is never set)
- Value-level provenance (which PDF page/cell backs which period value)
- Numeric agreement status between structured value and source
- Confidence score (separate from evidence level)
- Any cross-check result against the source PDF
```

---

## Gap analysis

```text
Gap 1: STRONG_EVIDENCE is reachable without any PDF verification.
  - Today a row becomes STRONG just because the workbook has a 页码 column with a value.
  - The page number is not validated as a real PDF page, not bound to a PDF text span,
    and the structured value is not compared against anything in the PDF.
  - This is "explicit but unverified" provenance, not "auditable traceable" provenance.

Gap 2: page_number is never populated as a structured int.
  - EvidenceRef.page_number is always None in the current runner.
  - explicit_evidence_ref is a free-text string (e.g. "1", "12-13", "附录A"),
    not parsed into a usable page or range.

Gap 3: No value-level provenance.
  - A row may have multiple period_values, but evidence is row-level only.
  - There is no way to say "2024A value 4356 is backed by PDF page 12, table 3, row 2".
  - This matters for wide financial tables where one row spans multiple source pages.

Gap 4: No numeric agreement check.
  - Even if a page number is present, the structured value (e.g. 4356) is never
    compared against any source value. A typo or extraction error stays invisible.

Gap 5: Confidence is conflated with evidence level.
  - The workbook may carry a 置信度 (confidence) column (Linyang qualitative_facts does),
    but it is not represented in EvidenceLevel or AuditRowResult as a separate field.
  - LLM confidence must NOT be treated as strong evidence, but a workbook-provided
    human/extractor confidence could be a useful separate signal if kept distinct.

Gap 6: Taihao has no page-number column at all.
  - All 158 Taihao rows are WEAK_EVIDENCE because the workbook has no evidence column.
  - Strengthening Taihao requires either adding an evidence path the workbook does not
    currently provide, or accepting that Taihao cannot reach STRONG_EVIDENCE without
    PDF-side work (which is out of scope for this deterministic Excel-intake design).

Gap 7: STRONG_EVIDENCE and clean admission are coupled only through policy, not by contract.
  - Today STRONG_EVIDENCE strict rows route to REVIEW_REQUIRED (not clean), while
    WEAK_EVIDENCE strict rows without issues route to INTERNAL_CLEAN_CANDIDATE.
  - This is counter-intuitive but intentional: evidence strength and clean admission
    are separate concepts. The design must keep them separate.
```

---

## WEAK_EVIDENCE meaning

```text
WEAK_EVIDENCE means:
  - the row has workbook lineage (sheet + row index + metric name)
  - the row has source PDF identity (the PDF path is known)
  - BUT no explicit page-level or cell-level provenance is available
  - AND no source-value agreement has been verified

WEAK_EVIDENCE does NOT mean:
  - the data is wrong
  - the data is unreviewable
  - the data must be discarded

WEAK_EVIDENCE means the row is structurally traceable to a workbook + PDF pair,
but not yet traceable to a specific verified location in the source PDF.
A WEAK_EVIDENCE row may still enter clean_data under the current conservative policy
(STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE + no issues + numeric period_values),
but its trust is limited because no human or deterministic process has anchored it
to a specific source page.
```

---

## STRONG_EVIDENCE requirements

The design proposes a stricter, deterministic STRONG_EVIDENCE definition. Strong evidence must mean **traceable and auditable, not merely plausible**.

```text
A row qualifies for STRONG_EVIDENCE only when ALL of the following hold:

1. Explicit page provenance
   - explicit_evidence_ref is present AND parses to a usable page or page range (int or int-int)
   - OR a future structured page_number int is populated on an EvidenceRef

2. Source identity completeness
   - source_excel_path is non-empty
   - sheet_name is non-empty
   - row_index > 0
   - metric_name is non-empty
   - source PDF path is non-empty

3. Value-level numeric agreement (for numeric fact rows)
   - each numeric period_value can be matched to a numeric token on the cited PDF page
     (deterministic text-token agreement, NOT LLM judgment)
   - OR, if PDF text extraction is not available in the current pipeline scope,
     the row is marked "STRONG_EVIDENCE_UNVERIFIED" rather than fully STRONG,
     and a future PDF-side task must close the gap

4. No blocking issues
   - no error-severity issues
   - no unit / period / valuation category issues that contradict the evidence

5. Deterministic, auditable, reproducible
   - the promotion decision must be reproducible from the manifest + evidence_index alone
   - no LLM / VLM judgment in the promotion path
   - LLM/extractor confidence (if present) is recorded separately, never used as evidence
```

The key change vs. today: STRONG_EVIDENCE must require a **verifiable** page reference, not just a **present** one. Today's "explicit_evidence_ref non-empty -> STRONG" is a necessary but not sufficient condition under this design.

---

## Promotion criteria

Promotion path from WEAK_EVIDENCE to STRONG_EVIDENCE:

```text
Step 1: Provenance enrichment (deterministic, workbook-side)
  - parse explicit_evidence_ref into a structured page or page range when possible
  - populate EvidenceRef.page_number with the parsed int (or range start)
  - if the workbook has no evidence column, the row cannot be promoted at this step
    and stays WEAK_EVIDENCE (this is the Taihao case)

Step 2: Source-identity completeness check (deterministic)
  - confirm source_excel_path, sheet_name, row_index, metric_name, pdf_path all present
  - if any missing, stay WEAK_EVIDENCE

Step 3: Numeric agreement check (deterministic, optional PDF-text-side)
  - for each numeric period_value, attempt a deterministic text-token match on the
    cited PDF page (exact numeric string match or normalized numeric equality)
  - if ALL numeric values agree -> agreement_ok = True
  - if ANY value disagrees -> agreement_ok = False, stay WEAK_EVIDENCE (or downgrade)
  - if PDF text extraction is not available -> agreement_ok = UNVERIFIED
    (row may be marked STRONG_EVIDENCE_UNVERIFIED but not fully STRONG)

Step 4: Issue gate (deterministic)
  - no error-severity issues
  - no unit/period/valuation category issues

Step 5: Promotion decision
  - if Step 1 + Step 2 + Step 4 pass AND Step 3 agreement_ok = True -> STRONG_EVIDENCE
  - if Step 1 + Step 2 + Step 4 pass AND Step 3 agreement_ok = UNVERIFIED -> STRONG_EVIDENCE_UNVERIFIED
  - otherwise -> stay WEAK_EVIDENCE (or MISSING_EVIDENCE if lineage is missing)
```

Promotion is **row-level** by default (matching the current row-level evidence model), with an optional **value-level** extension for future wide-table rows that span multiple source pages. The first implementation slice should stay row-level.

---

## Negative criteria

A row must NOT be promoted to STRONG_EVIDENCE (and should stay WEAK or go to REVIEW) when:

```text
N1: no explicit page provenance (no evidence column, or empty value)
N2: explicit_evidence_ref is non-numeric / unparseable (e.g. "附录A", "见正文") and no
    structured page_number is available
N3: any numeric period_value disagrees with the cited PDF page token
N4: the row is a pseudo-header / comparison-dimension / scaffolding row
    (R7S scaffolding guard already routes these to REVIEW_REQUIRED; they must never
    be promoted regardless of evidence)
N5: the row is MARKET_REFERENCE_ROW (R7P-FIX2 routes these to REVIEW_REQUIRED;
    market reference rows stay review-only regardless of evidence)
N6: the row is TESTSET_SUPPORTING_ROW or NORMALIZED_TESTSET_RECORD_ROW (review-only by design)
N7: the row has any error-severity issue
N8: the row has a unit / period / valuation category issue
N9: the row relies solely on LLM/VLM confidence for its evidence claim
N10: the row's evidence cannot be reproduced from manifest + evidence_index alone
```

---

## Interaction with clean-boundary policy

```text
- Evidence strengthening is SEPARATE from clean admission.
  STRONG_EVIDENCE must NOT automatically imply clean admission.

- Current policy (clean_candidate_policy.py):
    STRONG_EVIDENCE strict rows -> REVIEW_REQUIRED (not clean)
    WEAK_EVIDENCE strict rows + no issues + numeric period_values -> INTERNAL_CLEAN_CANDIDATE
  This is counter-intuitive but intentional: a STRONG_EVIDENCE row is better evidenced
  but still subject to the same clean-admission policy. The design must NOT change this
  coupling in R7W.

- The R7S scaffolding guard is independent of evidence level:
  a scaffolding row stays REVIEW_REQUIRED whether WEAK or STRONG.
  Promotion must never bypass the scaffolding guard.

- A future task MAY reconsider whether STRONG_EVIDENCE + numeric agreement should
  enable a different clean-admission path, but that is a separate policy decision
  and must NOT be bundled into R7W.
```

---

## Interaction with market-reference policy

```text
- MARKET_REFERENCE_ROW -> REVIEW_REQUIRED (R7P-FIX2), regardless of evidence level.
- Evidence strengthening must NOT change MARKET_REFERENCE_ROW routing.
- A market reference row with a verified page number is still REVIEW_REQUIRED;
  it is better evidenced for human review, but it does not enter clean_data.
- The design explicitly keeps market-reference boundaries unchanged.
```

---

## Interaction with readiness gates

```text
- Evidence strengthening does NOT open any readiness gate.
- client_ready = false
- production_ready = false
- formal_client_export_allowed = false
- demo_export_only = true

- STRONG_EVIDENCE is a data-quality signal, not a production-readiness signal.
  A workbook where all rows reach STRONG_EVIDENCE is better evidenced, but:
    - it is not automatically client_ready
    - it is not automatically production_ready
    - it does not automatically allow formal client export

- The five concepts must stay separate:
    evidence_strength       (WEAK / STRONG / STRONG_UNVERIFIED / MISSING)
    clean_admission         (INTERNAL_CLEAN_CANDIDATE / REVIEW_REQUIRED / ...)
    review_required         (per-row review decision)
    export_readiness        (demo_export_only / formal_client_export_allowed)
    production_readiness    (production_ready)
```

---

## Proposed evidence schema additions / reuse

Reuse existing fields where possible; add minimal new fields only where the gap is real.

```text
Reuse (no change):
  - SpreadsheetRow.explicit_evidence_ref (string, already extracted)
  - EvidenceRef.source_type / source_id / locator / is_explicit
  - EvidenceLevel Literal type

Add / populate (in a future R7X implementation, not here):
  - EvidenceRef.page_number: int | None
      -> populate by parsing explicit_evidence_ref into an int when it is a plain number
      -> keep None for non-numeric refs like "附录A"
  - AuditRowResult.evidence_agreement_status: Literal["verified", "unverified", "disagreed", "not_applicable"] | None
      -> default None (not checked)
      -> "verified" = all numeric values agreed with cited PDF page token
      -> "unverified" = PDF text check not available or page not parseable
      -> "disagreed" = at least one value disagreed
      -> "not_applicable" = row has no numeric period_values (e.g. narrative)
  - AuditRowResult.evidence_confidence: str | None
      -> optional workbook-provided confidence (e.g. 置信度 column), kept strictly separate
         from evidence_level; never used to promote evidence strength

Optional new EvidenceLevel literal (debated):
  - "STRONG_EVIDENCE_UNVERIFIED" for rows with explicit page provenance but no PDF
    value-agreement check yet.
  - This avoids over-claiming STRONG when no PDF-side verification ran.
  - If adding a new literal is too invasive, reuse STRONG_EVIDENCE but set
    evidence_agreement_status="unverified" to distinguish.
  - R7W recommends the agreement-status field over a new literal, to avoid
    proliferating evidence levels.
```

---

## Test plan

A future R7X implementation task should add tests for:

```text
T1: explicit_evidence_ref = "12" parses to page_number=12 -> provenance enriched
T2: explicit_evidence_ref = "12-13" parses to page range -> provenance enriched
T3: explicit_evidence_ref = "附录A" does not parse -> page_number stays None, no promotion
T4: explicit_evidence_ref = "" / None -> stays WEAK_EVIDENCE
T5: row with page_number + all numeric values agreeing -> STRONG_EVIDENCE (or STRONG_UNVERIFIED if no PDF check)
T6: row with page_number + one numeric value disagreeing -> stays WEAK_EVIDENCE
T7: scaffolding row (市场数据 + non-numeric period_values) -> stays REVIEW_REQUIRED, never promoted
T8: MARKET_REFERENCE_ROW with page_number -> stays REVIEW_REQUIRED, never promoted
T9: TESTSET_SUPPORTING_ROW with page_number -> stays REVIEW_REQUIRED, never promoted
T10: row with unit issue + page_number -> stays WEAK_EVIDENCE / REVIEW_REQUIRED
T11: STRONG_EVIDENCE row still routes through clean_candidate_policy independently (no auto-clean)
T12: evidence_agreement_status is recorded in evidence_index.json and manifest
T13: LLM/extractor confidence field is recorded but does not affect evidence_level
T14: promotion decision is reproducible from manifest + evidence_index alone
```

---

## Migration / compatibility plan

```text
- R7W is design-only; no code change in this task.
- R7X implementation must be backward compatible:
    - rows without explicit_evidence_ref behave exactly as today (WEAK_EVIDENCE)
    - rows with explicit_evidence_ref but no PDF check become STRONG_EVIDENCE_UNVERIFIED
      (or STRONG + agreement_status=unverified), NOT downgraded
    - existing tests (86 passed) must remain green
    - existing manifests must remain valid (new fields are additive, optional)
- The output_schema_guardrails contract must NOT be weakened:
    - new evidence fields are not forbidden row_types and do not trigger guardrails
    - guardrails still forbid MARKET_REFERENCE_ROW / TESTSET_SUPPORTING_ROW /
      NORMALIZED_TESTSET_RECORD_ROW / UNKNOWN_ROW in clean_data
- Linyang qualitative_facts (currently STRONG_EVIDENCE via 页码 column) must not regress:
    - under the new design they would become STRONG_EVIDENCE_UNVERIFIED
      (explicit page but no PDF value check), which is honest
    - this is a label refinement, not a regression, because the page was never verified
- Taihao rows stay WEAK_EVIDENCE (no evidence column) — no change, honest.
```

---

## Recommended R7X implementation slice

```text
348N-R7X evidence provenance parsing (page_number population) only

Scope:
  - parse explicit_evidence_ref into EvidenceRef.page_number (int or range) when numeric
  - add evidence_agreement_status field (default "not_applicable" / None)
  - add optional evidence_confidence field (workbook 置信度, separate from evidence_level)
  - do NOT add PDF text extraction or value-agreement checking yet
  - rows with explicit page -> STRONG_EVIDENCE_UNVERIFIED (or STRONG + agreement_status=unverified)
  - rows without explicit page -> unchanged (WEAK_EVIDENCE)
  - keep all clean-admission policy, scaffolding guard, market-reference policy unchanged
  - keep all readiness gates closed
  - add tests T1-T4, T9, T11-T14
  - rerun Linyang (has 页码) + Taihao (no 页码) to confirm no regression

Deferred to a later task (R7Y or beyond):
  - deterministic PDF text-token extraction for value-agreement checking
  - value-level provenance (per period_value page binding)
  - any consideration of STRONG_EVIDENCE enabling a different clean-admission path

Rationale: page_number parsing is the smallest safe slice that closes Gap 2 without
requiring PDF-side work. It makes provenance machine-readable without over-claiming
verification. PDF value-agreement (Gap 4) is the harder, more invasive step and
should be a separate task.
```

---

## Remaining risks

```text
R1: STRONG_EVIDENCE_UNVERIFIED may be misread as "fully verified".
    - Mitigation: the name and agreement_status field must make the unverified state explicit.
    - Manifests and evidence_index must clearly show agreement_status.

R2: PDF value-agreement checking (deferred) is the real trust anchor.
    - Without it, evidence strengthening only proves "a page was cited", not "the value matches".
    - This is honest but limited; R7W does not over-claim what page-parsing achieves.

R3: Taihao cannot be strengthened without an evidence column or PDF-side work.
    - This is a real limitation, not a design flaw.
    - Taihao's WEAK_EVIDENCE status is honest given its workbook structure.

R4: LLM/extractor confidence must stay separate from evidence.
    - If a future task accidentally uses 置信度 to promote evidence, it breaks the
      "no LLM confidence as strong evidence" rule.
    - Mitigation: evidence_confidence is a recorded-only field, never read by classify_evidence_level.

R5: Proliferating evidence levels (STRONG / STRONG_UNVERIFIED) could confuse downstream readers.
    - Mitigation: prefer the agreement_status field over new literals; keep EvidenceLevel stable.

R6: No readiness gate opens in R7W.
    - Evidence strengthening is necessary but not sufficient for any readiness claim.
    - production_ready / formal_client_export_allowed remain false.
```

---

## Decision

`348N_R7W_RECOMMENDS_DETERMINISTIC_PAGE_PROVENANCE_PARSING_AS_FIRST_SLICE`

The evidence-strengthening design concludes:

```text
- WEAK_EVIDENCE means "workbook + PDF lineage, but no verified page-level provenance".
- STRONG_EVIDENCE must mean "traceable and auditable", requiring:
    explicit page provenance + source identity completeness + numeric agreement (or
    explicit UNVERIFIED status) + no blocking issues + deterministic reproducibility.
- Today's STRONG_EVIDENCE is reachable without PDF verification (Gap 1); the design
  tightens this by adding agreement_status and requiring page_number parsing.
- Promotion is row-level first, deterministic, no LLM/VLM.
- STRONG_EVIDENCE does NOT auto-imply clean admission; the five concepts
  (evidence_strength / clean_admission / review_required / export_readiness /
  production_readiness) stay separate.
- The recommended R7X slice is page_number parsing + agreement_status field only;
  PDF value-agreement is deferred.
- No readiness gate opens. production_ready = false. formal_client_export_allowed = false.
```

---

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R7W_RECOMMENDS_DETERMINISTIC_PAGE_PROVENANCE_PARSING_AS_FIRST_SLICE
build_result（构建结果）= COMPILE_OK
test_result（测试结果）= tests/agent 86 passed
design_result（设计结果）= evidence strengthening design complete; WEAK->STRONG path defined via page provenance + agreement_status + issue gate; row-level first; deterministic; no LLM; STRONG does not auto-imply clean; readiness gates unchanged
strong_evidence_definition（强证据定义）= explicit page provenance + source identity completeness + numeric agreement (or explicit UNVERIFIED) + no blocking issues + deterministic reproducibility; not merely plausible
promotion_required_fields（提升所需字段）= explicit_evidence_ref (parsed to page_number), source_excel_path, sheet_name, row_index, metric_name, pdf_path, evidence_agreement_status, no error/unit/period/valuation issues
readiness_gates（就绪门）= closed (client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true)
production_ready（是否生产就绪）= no
formal_client_export_allowed（是否允许正式客户导出）= no
files_modified（修改文件数）= 1 (R7W report only; no code/test/output/input/config changes)
error_count（错误数）= 0
boundary_check（边界检查）= passed (only the allowed R7W report created; no code/test/output/input/previous-doc/temp/data/legacy/config/guardrails/row_type_classifier/qualitative_facts/MARKET_REFERENCE_ROW/readiness-gate changes; no workbook reruns; no external calls; no LLM confidence as evidence)
recommended_next_task（推荐下一任务）= 348N-R7X evidence provenance parsing (page_number population + agreement_status field) only
```
