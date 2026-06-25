## Task ID

`348N-R7X-QA evidence provenance parsing review`

## Task Type

QA / review task. This is not an implementation task. No code, tests, output, input, temp, data, legacy, config, or dependencies were modified. No workbook rerun, MinerU, OCR, LLM, or VLM was run. One QA report was created.

---

## Preflight

```text
git status -sb (before pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Already up to date.

git status -sb (after pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  d7737f2 docs: update handoff after R7X
  6069553 docs: refresh plain-language progress after R7X
  00e1985 docs: sync progress after R7X
  f3ab39b docs: add R7X QA task
  5d8aa24 feat: add evidence provenance parsing
  bcf6e5b docs: add R7X evidence provenance parsing task
  56d42f9 docs: add R7W evidence strengthening design
  da46f4c docs: add R7W evidence strengthening task
  6e8a5fc docs: add R7V readiness review
  3206d7d docs: add R7V readiness review task
  b4a0ee9 docs: add R7U workbook regression review
  bb4ae21 docs: add R7U workbook regression task
```

Worktree was clean after pull.

---

## Files reviewed

Required context read-only:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R7X_QA_evidence_provenance_parsing_review.md`
- `docs/agent/348N_R7W_EVIDENCE_STRENGTHENING_DESIGN_WEAK_TO_STRONG_PATH.md`
- `docs/agent/348N_R7V_CROSS_FAMILY_CLEAN_BOUNDARY_SUMMARY_AND_READINESS_REVIEW.md`
- `docs/agent/348N_R7U_LINYANG_ANJING_WORKBOOK_FAMILY_REGRESSION_CHECK.md`
- `docs/agent/348N_R7T_TAIHAO_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_PILOT_RERUN.md`

R7X implementation files reviewed read-only:

- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`

---

## Implementation review

R7X implementation commit under review:

```text
5d8aa24 feat: add evidence provenance parsing
```

Modified files in that implementation:

```text
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

QA finding: **VALID**.

R7X correctly implements the first R7W slice:

1. deterministic page-number parsing from `explicit_evidence_ref`;
2. `agreement_status` field on `AuditRowResult`;
3. `agreement_status` population through `build_row_audit_result(...)`;
4. evidence index serialization of `agreement_status`;
5. conservative evidence semantics: explicit/page provenance + `UNVERIFIED` remains `WEAK_EVIDENCE` and does not become verified `STRONG_EVIDENCE`.

No clean-boundary policy, MARKET_REFERENCE_ROW policy, qualitative_facts admission, output guardrail, or readiness gate behavior was changed by R7X.

---

## Page parser review

Implementation reviewed in `datefac_agent/audit/evidence_checker.py`:

```text
parse_page_number(ref_text: str | None) -> int | None
```

QA findings:

```text
Chinese forms supported:
  第12页       -> 12
  12页        -> 12
  页码：12     -> 12
  第12-13页   -> 12 (first page)

English forms supported:
  page 12     -> 12
  Page 12     -> 12
  p.12        -> 12
  P12         -> 12
  pp. 12-13   -> 12 (first page)

Unparseable refs:
  附录A / 空字符串 / None -> None
```

Range behavior is conservative and matches task requirements: when the model supports only one `page_number`, R7X uses the first page number and preserves the full raw reference string in the explicit evidence ref (`source_id`) and raw locator context.

Important boundary: the parser does **not** OCR or inspect the PDF. It only parses deterministic page-number text from workbook provenance.

QA answer summary:

```text
page_number parsed = provenance anchor exists
page_number parsed != source-value agreement verified
page_number parsed != STRONG_EVIDENCE
```

---

## Agreement status review

Implementation reviewed in:

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/review/review_queue_builder.py`

R7X adds:

```python
EvidenceAgreementStatus = Literal["MISSING", "UNVERIFIED", "VERIFIED", "DISAGREED"]
```

and:

```python
AuditRowResult.agreement_status: EvidenceAgreementStatus = "MISSING"
```

Population logic reviewed:

```text
classify_agreement_status(...):
  explicit/page provenance present -> UNVERIFIED
  no explicit/page provenance      -> MISSING
```

QA findings:

- `MISSING` vs `UNVERIFIED` are correctly distinguished.
- R7X only populates `MISSING` and `UNVERIFIED`.
- R7X does **not** set `VERIFIED` or `DISAGREED` because no deterministic source-value agreement checker exists yet.
- The field is backward-compatible: it has a default value and is additive to `AuditRowResult`.

QA result: **VALID**.

---

## Evidence level behavior review

Expected R7X behavior:

```text
explicit/page provenance + agreement_status = UNVERIFIED -> WEAK_EVIDENCE
workbook lineage only -> WEAK_EVIDENCE + agreement_status = MISSING
missing lineage -> MISSING_EVIDENCE
```

Reviewed implementation confirms this behavior:

- `classify_evidence_level(...)` no longer returns `STRONG_EVIDENCE` merely because `explicit_evidence_ref` exists or page_number parsed.
- If explicit/page provenance exists and workbook/PDF lineage is complete, evidence remains `WEAK_EVIDENCE`.
- If explicit/page provenance exists but lineage is incomplete, evidence is `MISSING_EVIDENCE`.
- `STRONG_EVIDENCE` is not claimed in R7X because no value-agreement checker exists.

This is the critical QA boundary. R7X preserves the distinction:

```text
page_number parsed = provenance anchor exists
agreement_status = UNVERIFIED = source-value agreement not checked yet
UNVERIFIED provenance remains WEAK_EVIDENCE
parsed page_number does not automatically become VERIFIED or STRONG_EVIDENCE
```

QA result: **VALID**.

---

## Evidence index writer review

Reviewed `datefac_agent/delivery/evidence_index_writer.py`.

R7X adds `agreement_status` to the serialized evidence index payload:

```text
agreement_status = result.agreement_status
```

The existing `evidence_refs` serialization already includes:

```text
source_type
source_id
page_number
locator
is_explicit
```

QA findings:

- `agreement_status` is auditable in `evidence_index.json` for future runner outputs.
- `page_number` is preserved in each serialized EvidenceRef.
- This change is additive and does not require modifying old output artifacts.
- No output artifacts were created or modified in this QA task.

QA result: **VALID**.

---

## Test review

`pytest tests/agent -q` result:

```text
95 passed in 1.18s
```

R7X tests cover:

```text
- 第12页 -> page_number 12 + UNVERIFIED
- page 12 / p.12 / P12 -> page_number 12
- 第12-13页 / pp. 12-13 -> first page 12, raw reference preserved
- 附录A -> page_number None, raw reference preserved, UNVERIFIED
- missing explicit ref -> agreement_status MISSING
- parsed page + UNVERIFIED does not claim STRONG_EVIDENCE
- workbook-row weak evidence behavior preserved
- empty / non-numeric refs return None
- evidence_index_writer emits agreement_status and parsed page_number
```

Existing behavior checks preserved:

```text
- R7S strict-table scaffolding guard tests pass
- MARKET_REFERENCE_ROW tests pass
- qualitative_facts remains review-only; admission not broadened
- output guardrail tests pass
```

Test specificity: sufficient. Tests directly target the page parser, agreement_status, evidence-level conservatism, evidence index serialization, and key regression boundaries.

QA result: **VALID**.

---

## Compatibility risk review

Main compatibility risk:

```text
Before R7X: explicit_evidence_ref -> STRONG_EVIDENCE
After R7X:  explicit_evidence_ref -> WEAK_EVIDENCE + agreement_status=UNVERIFIED
```

This is an intentional semantic tightening from R7W, not a regression. It prevents overclaiming strong evidence where source-value agreement has not been checked.

Expected impacts:

- Linyang qualitative_facts rows with page references may now be reported as `WEAK_EVIDENCE + UNVERIFIED` rather than `STRONG_EVIDENCE`; they remain `TESTSET_SUPPORTING_ROW -> REVIEW_REQUIRED`, so clean admission remains conservative.
- market_base_data / MARKET_REFERENCE_ROW rows with page references remain `REVIEW_REQUIRED` and do not enter clean_data.
- clean-boundary policy is not broadened.
- Existing output artifacts are not rewritten; the new field affects future outputs only.
- Consumers that interpreted old `STRONG_EVIDENCE` as "page exists" must now use `agreement_status` to distinguish page provenance from value verification.

Risk is acceptable because the change is conservative and aligns with the R7W principle:

```text
Strong evidence must mean traceable and auditable, not merely plausible.
```

---

## Readiness gates review

R7X and R7X-QA do not change readiness gates.

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

No production readiness or formal client export is claimed. Parsed page provenance and `UNVERIFIED` agreement status are data-quality improvements only; they are not delivery readiness signals.

---

## QA Questions (answers)

1. **Does R7X parse deterministic page references from explicit_evidence_ref correctly?** Yes.
2. **Does it support Chinese forms such as 第12页, 12页, 页码：12, 第12-13页?** Yes.
3. **Does it support English forms such as page 12, Page 12, p.12, P12, pp. 12-13?** Yes.
4. **Does a page range use first page and preserve raw locator?** Yes: first page stored in `page_number`, raw reference preserved in evidence ref.
5. **Do 附录A, empty string, None leave page_number None?** Yes.
6. **Is agreement_status added backward-compatibly?** Yes: additive default field on `AuditRowResult`.
7. **Does agreement_status distinguish MISSING vs UNVERIFIED?** Yes.
8. **Does R7X avoid setting VERIFIED / DISAGREED?** Yes; both are reserved for future deterministic agreement checker.
9. **Does explicit/page provenance + UNVERIFIED remain WEAK_EVIDENCE?** Yes.
10. **Does workbook-row weak evidence behavior remain unchanged?** Yes.
11. **Does evidence_index_writer include agreement_status?** Yes.
12. **Did R7X avoid changing MARKET_REFERENCE_ROW policy?** Yes.
13. **Did R7X avoid broadening qualitative_facts admission?** Yes.
14. **Did R7X avoid changing R7S strict-table scaffolding guard?** Yes.
15. **Did R7X avoid changing output_schema_guardrails?** Yes.
16. **Did R7X avoid changing readiness gates?** Yes.
17. **Does tests/agent pass?** Yes, 95 passed.
18. **Do tests cover parser/agreement/strong-evidence overclaim prevention?** Yes.
19. **Compatibility risk from explicit STRONG -> WEAK+UNVERIFIED?** Present but intended and conservative; acceptable.
20. **Recommended next task?** R7Y deterministic source-value agreement checker / evidence agreement verification slice.

---

## Validation outputs

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
  -> COMPILE_OK

python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
  -> COMPILE_OK

pytest tests/agent -q
  -> 95 passed in 1.18s
```

Post-report git checks are run after creating this report:

```text
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

---

## Decision

`348N_R7X_QA_CONFIRMED_EVIDENCE_PROVENANCE_PARSING_VALID`

R7X QA result: **VALID**.

R7X correctly parses page provenance and records agreement status while preserving the critical conservative boundary:

```text
page_number parsed != VERIFIED
UNVERIFIED != STRONG_EVIDENCE
```

No blocking issue found.

---

## Recommended next task

```text
348N-R7Y deterministic source-value agreement checker / evidence agreement verification slice
```

Recommended R7Y scope:

- design or implement deterministic numeric token agreement checking for rows with parsed page provenance;
- set `agreement_status=VERIFIED` only when deterministic source-value agreement is proven;
- set `agreement_status=DISAGREED` only when deterministic mismatch is proven;
- keep `UNVERIFIED` conservative when source text cannot be checked;
- keep MARKET_REFERENCE_ROW, qualitative_facts, R7S scaffolding guard, output guardrails, and readiness gates unchanged;
- do not declare production readiness or formal client export.

---

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R7X_QA_CONFIRMED_EVIDENCE_PROVENANCE_PARSING_VALID
build_result（构建结果）= COMPILE_OK
test_result（测试结果）= tests/agent 95 passed
files_modified（修改文件数）= 1 (QA report only; no code/test/output/input changes)
error_count（错误数）= 0
boundary_check（边界检查）= passed (only allowed QA report created; no code/test/output/input/temp/data/legacy/config/handoff/progress/codex_tasks changes; no workbook rerun; no MinerU/OCR/LLM/VLM; no MARKET_REFERENCE_ROW / qualitative_facts / R7S guard / output_schema_guardrails / readiness gate changes)
page_number_parsing_result（页码解析结果）= valid (Chinese/English refs and ranges parse; unparseable refs remain None; raw refs preserved)
agreement_status_result（一致性状态结果）= valid (MISSING vs UNVERIFIED distinguished; VERIFIED/DISAGREED not set in R7X)
strong_evidence_claim_result（强证据声明结果）= valid (parsed page_number + UNVERIFIED remains WEAK_EVIDENCE; no false verified STRONG_EVIDENCE claim)
qa_result（QA结果）= VALID
readiness_gates（就绪门）= closed (client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true)
recommended_next_task（推荐下一任务）= 348N-R7Y deterministic source-value agreement checker / evidence agreement verification slice
```
