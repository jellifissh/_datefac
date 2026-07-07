# 348N-R7AQ test-only discrepancy review queue fixture and policy prototype report

## Task ID

```text
348N-R7AQ test-only discrepancy review queue fixture and policy prototype
```

## Task size / reasoning level used

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-policy-prototype
reason = R7AP designed the DateFac-MinerU discrepancy review workflow. R7AQ reduces that design into a compact test-only fixture and pure policy prototype without production wiring, real outputs, external calls, or readiness changes.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Already up to date.

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git branch --show-current:
  pivot/348-agent-foundation

git log --oneline -12:
  f68c59b docs: add R7AP discrepancy workflow design
  0634345 docs: update handoff after R7AO QA
  607a782 docs: refresh plain-language progress after R7AO QA
  046e66f docs: sync progress after R7AO QA
  6341ad2 docs: add R7AP discrepancy workflow design task
  6e02622 docs: add R7AO QA review
  07ecb4c docs: update handoff after R7AO
  ccc30bd docs: refresh plain-language progress after R7AO
  c1065f5 docs: sync progress after R7AO
  78ddbd6 docs: add R7AO QA review task
  ab8175f docs: update handoff after R7AN
  7ac4823 docs: refresh plain-language progress after R7AN
```

Worktree was clean after pull and before R7AQ file creation.

## Files reviewed

Required context:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `docs/codex_tasks/348N_R7AP_DateFac_MinerU_discrepancy_review_workflow_design.md`
- `docs/agent/348N_R7AP_DATEFAC_MINERU_DISCREPANCY_REVIEW_WORKFLOW_DESIGN.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`

Read-only implementation context:

- `tests/agent/mineru_artifact_adapter_348n.py`
- `tests/agent/test_mineru_artifact_adapter_348n.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`

No full R7AO output was read into committed tests. No DateFac Excel or MinerU artifact was committed.

## Files created

Created exactly the requested R7AQ files:

- `tests/agent/discrepancy_review_queue_policy_348n.py`
- `tests/agent/test_discrepancy_review_queue_policy_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7aq_discrepancy_rows_fixture.json`
- `docs/agent/348N_R7AQ_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_FIXTURE_AND_POLICY_PROTOTYPE_REPORT.md`

No `datefac_agent/` production files were modified.

## Fixture result

Fixture:

```text
tests/agent/fixtures/discrepancy_review_queue/r7aq_discrepancy_rows_fixture.json
```

Fixture scope:

```text
schema_version = 1
fixture_scope = test_only_r7aq
row_count = 8
fixture_size < 20 KB
```

Coverage:

```text
VERIFIED = 1
DISAGREED = 2
AMBIGUOUS = 2
MISSING_EVIDENCE = 1
PARSE_SKIPPED = 1
UNVERIFIED = 1
table evidence conflict row = included
repeated ambiguous value row = included
```

The fixture is curated and synthetic. It does not contain full R7AO output, DateFac Excel data, or MinerU content_list artifacts.

## Policy prototype result

Prototype:

```text
tests/agent/discrepancy_review_queue_policy_348n.py
```

Implemented test-only helpers:

```text
load_discrepancy_rows_fixture(...)
should_enter_discrepancy_review_queue(...)
candidate_clean_data_eligible(...)
build_discrepancy_review_item(...)
build_discrepancy_review_queue_items(...)
severity_for_row(...)
discrepancy_subtype(...)
apply_reviewer_action(...)
unresolved_export_bucket(...)
```

Policy behavior:

```text
VERIFIED -> no discrepancy review_queue item
VERIFIED -> clean_data_eligible false
UNVERIFIED -> review_queue, partial_anchor_queue, MEDIUM
DISAGREED -> review_queue, evidence_conflict_queue, HIGH
AMBIGUOUS -> review_queue, evidence_ambiguity_queue, MEDIUM_HIGH
MISSING_EVIDENCE -> review_queue, missing_evidence_queue, MEDIUM
PARSE_SKIPPED -> review_queue, parse_schema_queue, LOW
all non-VERIFIED -> clean_data_eligible false
unresolved rows -> discrepancy_review_output only
```

This prototype is pure test code and does not import or modify production DateFac Agent code.

## Review queue item result

Generated review items include the required fields:

```text
review_item_id
source_document_id
source_row_id
candidate_metric_name
candidate_period
candidate_value
candidate_unit
candidate_page_number
agreement_status
source_text_status
evidence_type
matched_page_number
matched_locator
matched_block_index
evidence_preview
candidate_raw_text
match_reason
risk_reason
suggested_action
severity
review_status
reviewer_decision
reviewer_corrected_value
reviewer_corrected_unit
reviewer_note
audit_hash
run_id
adapter_version
input_file_hashes
clean_data_eligible
```

Additional metadata-first fields:

```text
review_subqueue
discrepancy_subtype
matched_text_sha256
matched_char_count
evidence_preview_sha256
alternative_evidence_candidates
export_bucket
```

Determinism:

```text
review_item_id = deterministic hash prefix from run_id + source_row_id + status + value + locator/hash
audit_hash = deterministic hash of stable source/audit fields, excluding mutable reviewer fields
```

## Clean data guard result

Verified by tests:

```text
VERIFIED does not automatically enter clean_data.
all non-VERIFIED rows are clean_data_eligible=false.
reviewer decisions do not make rows clean_data_eligible unless explicit_policy_gate=true and a reviewer note is present.
even when explicit_policy_gate=true, export bucket is requires_reaudit_before_clean_delivery rather than direct clean delivery.
```

No `STRONG_EVIDENCE` promotion and no clean admission behavior was implemented.

## Evidence preview result

Evidence preview policy:

```text
evidence_preview is bounded by preview_limit.
alternative evidence previews are bounded by preview_limit.
review items do not include source_text, full_source_text, source_text_full, or text fields.
matched_text_sha256 / char_count / locator metadata are retained.
```

Test fixture intentionally includes `full_source_text` in selected rows to prove the policy output does not copy it.

## Reviewer action model result

Reviewer actions include the required set:

```text
ACCEPT_CANDIDATE
REJECT_CANDIDATE
CORRECT_VALUE
CORRECT_UNIT
CORRECT_PERIOD
CORRECT_METRIC
MARK_NOT_IN_REPORT
MARK_EVIDENCE_INSUFFICIENT
REQUEST_REEXTRACTION
REQUEST_MANUAL_SOURCE_CHECK
```

Additional action:

```text
SELECT_EVIDENCE
```

Fail-closed behavior:

```text
unsupported reviewer actions raise ValueError
AUTO_PROMOTE_TO_CLEAN is rejected
```

## Test coverage

Created:

```text
tests/agent/test_discrepancy_review_queue_policy_348n.py
```

Test coverage includes:

- fixture smallness and required status coverage
- `VERIFIED` excluded from discrepancy queue
- `VERIFIED` not clean-data eligible
- all non-VERIFIED statuses admitted to review queue
- expected status-to-subqueue routing
- expected severity mapping
- all non-VERIFIED rows clean-data ineligible
- unresolved rows exported only to discrepancy/review output
- metadata-first review item schema
- bounded evidence previews
- no full source_text copy
- deterministic `review_item_id` and `audit_hash`
- required reviewer actions
- reviewer action fail-closed validation
- reviewer decision cannot bypass explicit policy gate
- parse skipped separated from true evidence disagreement
- table-vs-paragraph conflict subtype
- repeated ambiguous value subtype

## Validation outputs

Required commands run:

```text
python -m py_compile tests/agent/discrepancy_review_queue_policy_348n.py tests/agent/test_discrepancy_review_queue_policy_348n.py
  PASS

python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
  PASS

python -m py_compile datefac_agent/review/clean_candidate_policy.py
  PASS

python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
  PASS

pytest tests/agent/test_discrepancy_review_queue_policy_348n.py -q
  12 passed in 0.09s

pytest tests/agent -q
  213 passed in 0.93s

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  ?? tests/agent/discrepancy_review_queue_policy_348n.py
  ?? tests/agent/fixtures/discrepancy_review_queue/
  ?? tests/agent/test_discrepancy_review_queue_policy_348n.py

git diff --stat
  no tracked diff before report creation because new files were untracked

git diff --name-only
  no tracked diff before report creation because new files were untracked

git diff --check
  PASS
```

## Boundary review

R7AQ stayed within the requested boundary:

```text
datefac_agent/ modified = no
production pipeline modified = no
full R7AO output committed = no
DateFac Excel committed = no
MinerU output committed = no
MinerU run = no
OCR / LLM / VLM run = no
real PDF extraction = no
new dependency added = no
VERIFIED -> STRONG_EVIDENCE promotion = no
VERIFIED -> clean_data admission = no
readiness gates opened = no
```

Readiness remains:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

## Decision

```text
Decision = 348N_R7AQ_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_FIXTURE_AND_POLICY_PROTOTYPE_VALID
```

R7AQ confirms the R7AP discrepancy workflow can be represented as compact test-only fixtures and pure policy helpers. All non-VERIFIED rows enter review queue items, all remain excluded from clean_data, evidence previews remain bounded and metadata-first, reviewer actions are explicit and fail-closed, and readiness gates remain closed.

## Recommended next task

```text
348N-R7AQ-QA test-only discrepancy review queue fixture and policy prototype review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，348N_R7AQ_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_FIXTURE_AND_POLICY_PROTOTYPE_VALID
build_result（构建结果）= PASS，py_compile validation passed
test_result（测试结果）= PASS，pytest tests/agent/test_discrepancy_review_queue_policy_348n.py -q => 12 passed; pytest tests/agent -q => 213 passed
files_modified（修改文件数）= 4
error_count（错误数）= 0
fixture_result（fixture结果）= PASS，small curated test-only fixture with VERIFIED / UNVERIFIED / DISAGREED / AMBIGUOUS / MISSING_EVIDENCE / PARSE_SKIPPED plus table conflict and repeated ambiguity
policy_prototype_result（策略原型结果）= PASS，pure tests/agent helper implements review_queue admission, severity, metadata-first review item generation, and fail-closed reviewer actions
review_queue_item_result（复核项结果）= PASS，non-VERIFIED rows generate deterministic review items with required fields, subqueues, severity, audit_hash, and run/input metadata
clean_data_guard_result（clean_data防护结果）= PASS，VERIFIED not auto-clean; all non-VERIFIED clean_data_eligible=false; reviewer action cannot bypass explicit policy gate
evidence_preview_result（证据预览结果）= PASS，bounded previews only; no source_text/full_source_text copied into review items
reviewer_action_model_result（复核动作模型结果）= PASS，required reviewer actions covered; unsupported auto-promotion fails closed
boundary_check（边界检查）= PASS，tests/docs/fixture only; no production code, no dependencies, no output commits, no MinerU/OCR/LLM/VLM
readiness_gates（就绪门）= CLOSED，client_ready=false; production_ready=false; formal_client_export_allowed=false; demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AQ-QA test-only discrepancy review queue fixture and policy prototype review
```
