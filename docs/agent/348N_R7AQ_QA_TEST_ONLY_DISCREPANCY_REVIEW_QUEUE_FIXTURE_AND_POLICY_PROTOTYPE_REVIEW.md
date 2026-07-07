# 348N-R7AQ-QA test-only discrepancy review queue fixture and policy prototype review

## Task ID

```text
348N-R7AQ-QA test-only discrepancy review queue fixture and policy prototype review
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
  0fb9a3d test: add discrepancy review queue policy prototype
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
```

Worktree was clean after pull and before this QA report.

## Files reviewed

Required context:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/agent/348N_R7AQ_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_FIXTURE_AND_POLICY_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7AP_DATEFAC_MINERU_DISCREPANCY_REVIEW_WORKFLOW_DESIGN.md`

R7AQ files reviewed:

- `tests/agent/discrepancy_review_queue_policy_348n.py`
- `tests/agent/test_discrepancy_review_queue_policy_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7aq_discrepancy_rows_fixture.json`

Boundary files reviewed read-only:

- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/delivery/evidence_index_writer.py`

## R7AQ recap

R7AQ commit reviewed:

```text
0fb9a3d test: add discrepancy review queue policy prototype
```

Files in commit:

```text
docs/agent/348N_R7AQ_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_FIXTURE_AND_POLICY_PROTOTYPE_REPORT.md
tests/agent/discrepancy_review_queue_policy_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7aq_discrepancy_rows_fixture.json
tests/agent/test_discrepancy_review_queue_policy_348n.py
```

QA result:

```text
PASS: R7AQ modified only the allowed test/helper/fixture/report files.
PASS: no datefac_agent/ production code was modified.
PASS: no output/, DateFac Excel, MinerU output, dependency, or config files were committed.
PASS: prototype remains under tests/agent/ and has no production hook.
```

## Fixture review

Fixture reviewed:

```text
tests/agent/fixtures/discrepancy_review_queue/r7aq_discrepancy_rows_fixture.json
```

Observed fixture facts:

```text
fixture_scope = test_only_r7aq
fixture_size_bytes = 10955
row_count = 8
```

Observed status coverage:

```text
VERIFIED = 1
DISAGREED = 2
AMBIGUOUS = 2
MISSING_EVIDENCE = 1
PARSE_SKIPPED = 1
UNVERIFIED = 1
```

Required scenario coverage:

```text
VERIFIED = covered
DISAGREED = covered
AMBIGUOUS = covered
MISSING_EVIDENCE = covered
PARSE_SKIPPED = covered
UNVERIFIED = covered
table conflict = covered by table-conflict:R8:2026E
repeated ambiguity = covered by repeated-ambiguous:R3
```

QA result:

```text
PASS: fixture is an 8-row curated test fixture, not full R7AO output.
PASS: fixture does not commit DateFac Excel or MinerU content_list output.
PASS: fixture intentionally includes a full_source_text field in selected rows only to prove policy output does not copy it.
```

## Policy prototype review

Prototype reviewed:

```text
tests/agent/discrepancy_review_queue_policy_348n.py
```

Implemented test-only helpers:

```text
load_discrepancy_rows_fixture
should_enter_discrepancy_review_queue
candidate_clean_data_eligible
build_discrepancy_review_item
build_discrepancy_review_queue_items
severity_for_row
discrepancy_subtype
apply_reviewer_action
unresolved_export_bucket
```

Import/boundary review:

```text
PASS: no datefac_agent import.
PASS: no production runner/CLI hook.
PASS: no subprocess/network/OpenAI/OCR/LLM/VLM integration.
PASS: helper uses only standard-library modules.
```

Policy behavior observed:

```text
review_queue item count = 7
VERIFIED rows generate no discrepancy item.
all non-VERIFIED statuses generate discrepancy items.
```

## Review queue admission review

Observed review item status counts:

```text
DISAGREED = 2
AMBIGUOUS = 2
MISSING_EVIDENCE = 1
PARSE_SKIPPED = 1
UNVERIFIED = 1
```

Observed subqueues:

```text
evidence_conflict_queue = 2
evidence_ambiguity_queue = 2
missing_evidence_queue = 1
parse_schema_queue = 1
partial_anchor_queue = 1
```

QA result:

```text
PASS: VERIFIED does not enter discrepancy review_queue.
PASS: all non-VERIFIED rows enter discrepancy review_queue.
PASS: PARSE_SKIPPED is separated into parse_schema_queue, not collapsed into true evidence disagreement.
PASS: DISAGREED enters evidence_conflict_queue.
PASS: AMBIGUOUS enters evidence_ambiguity_queue.
```

## Clean data guard review

Observed:

```text
candidate_clean_data_eligible(VERIFIED fixture row) = false
non-VERIFIED item clean_data_eligible values = false for all 7 items
ACCEPT_CANDIDATE without explicit_policy_gate => clean_data_eligible=false
ACCEPT_CANDIDATE with explicit_policy_gate + note => clean_data_eligible=true, but export bucket = requires_reaudit_before_clean_delivery
unsupported AUTO_PROMOTE_TO_CLEAN action => ValueError
```

QA result:

```text
PASS: VERIFIED does not automatically enter clean_data.
PASS: all non-VERIFIED rows are clean_data_eligible=false.
PASS: reviewer action cannot bypass the explicit policy gate.
PASS: even explicit policy gate does not directly create delivery clean output; it requires re-audit before clean delivery.
PASS: no STRONG_EVIDENCE promotion exists in prototype behavior.
```

## Evidence preview review

Observed:

```text
max evidence_preview length at preview_limit=120 = 78
forbidden full source text keys in review items = absent
fixture contains full_source_text test field = true
review items contain fixture full_source_text value = false
matched_text_sha256 / matched_char_count / locator metadata retained
alternative evidence candidate previews are bounded
```

QA result:

```text
PASS: evidence_preview has a length cap.
PASS: review items do not dump full source_text.
PASS: metadata-first evidence fields are retained.
PASS: table-vs-paragraph conflict and repeated ambiguity retain compact alternative evidence candidates.
```

## Reviewer action model review

Required actions:

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

Observed action model:

```text
all required actions present = true
additional SELECT_EVIDENCE action present = true
unsupported actions fail closed = true
reviewer decisions do not create clean eligibility unless explicit_policy_gate=true and reviewer_note is present
```

QA result:

```text
PASS: reviewer action model is complete for R7AP/R7AQ scope.
PASS: validation fails closed for unsupported actions.
PASS: reviewer decision cannot silently promote into clean_data.
```

## Review item metadata/audit review

Required review item fields were present for all 7 generated review items:

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

Determinism:

```text
review_item_id first run = r7aq:59cc820e884c6fbbd5606ad4
review_item_id second run = r7aq:59cc820e884c6fbbd5606ad4
audit_hash first run = 53cd0f9b498f6080eb5ade7a345b45d4d8b37878a43745d45401fff6b9288fa8
audit_hash second run = 53cd0f9b498f6080eb5ade7a345b45d4d8b37878a43745d45401fff6b9288fa8
```

QA result:

```text
PASS: review_item_id is deterministic.
PASS: audit_hash is deterministic.
PASS: metadata-first audit fields are sufficient for test-only prototype scope.
PASS: unresolved rows export only to discrepancy_review_output.
```

## Boundary review

QA result:

```text
PASS: R7AQ changed only allowed files.
PASS: prototype lives under tests/agent/.
PASS: no datefac_agent/ files were modified.
PASS: no production pipeline hook was added.
PASS: no output files were committed.
PASS: no DateFac Excel was committed.
PASS: no MinerU output was committed.
PASS: no dependency/config files were changed.
PASS: no MinerU run.
PASS: no OCR / LLM / VLM calls.
PASS: no real PDF extraction.
PASS: readiness gates remain CLOSED.
```

Readiness remains:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

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
  12 passed in 0.08s

pytest tests/agent -q
  213 passed in 0.87s

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git diff --stat
  no output before QA report creation

git diff --name-only
  no output before QA report creation

git diff --check
  PASS
```

## Limitations

- R7AQ remains a test-only prototype under `tests/agent/`.
- Fixture rows are curated and synthetic; they are not a full R7AO output sample.
- The prototype does not implement production review_queue integration, persistence, UI, or delivery behavior.
- `clean_data_eligible=true` under explicit policy gate is still only a re-audit precondition, not direct clean admission.
- Severity labels are deterministic and conservative for this fixture, but production materiality ranking remains future integration design work.
- The fixture intentionally includes `full_source_text` as a negative-control input field; QA confirms output review items do not copy it.

## Decision

```text
Decision = 348N_R7AQ_QA_CONFIRMED_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_FIXTURE_AND_POLICY_PROTOTYPE_VALID
```

R7AQ-QA confirms the prototype is test-only, conservative, metadata-first, and boundary-safe. VERIFIED rows do not enter the discrepancy queue or clean_data, all non-VERIFIED rows enter review queue items and remain clean-data ineligible, evidence previews are bounded, reviewer actions fail closed, and readiness gates remain closed.

## Recommended next task

```text
348N-R7AR discrepancy review queue integration boundary design
```

Rationale:

```text
After QA confirms the test-only policy prototype, the next safe slice is design-only production/integration boundary planning, not implementation. R7AR should decide how this policy would connect to future review_queue/evidence_index/clean_data flows without opening readiness gates.
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，348N_R7AQ_QA_CONFIRMED_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_FIXTURE_AND_POLICY_PROTOTYPE_VALID
build_result（构建结果）= PASS，py_compile validation passed
test_result（测试结果）= PASS，pytest tests/agent/test_discrepancy_review_queue_policy_348n.py -q => 12 passed; pytest tests/agent -q => 213 passed
files_modified（修改文件数）= 1，only docs/agent/348N_R7AQ_QA_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_FIXTURE_AND_POLICY_PROTOTYPE_REVIEW.md
error_count（错误数）= 0
fixture_review_result（fixture审查结果）= PASS，8-row curated fixture covers VERIFIED / UNVERIFIED / DISAGREED / AMBIGUOUS / MISSING_EVIDENCE / PARSE_SKIPPED plus table conflict and repeated ambiguity
policy_review_result（策略审查结果）= PASS，test-only helper is conservative, no production import/hook, all non-VERIFIED statuses route to review
review_queue_item_review_result（复核项审查结果）= PASS，7 non-VERIFIED review items generated with required fields, deterministic review_item_id/audit_hash, subqueues and severity
clean_data_guard_review_result（clean_data防护审查结果）= PASS，VERIFIED not auto-clean; all non-VERIFIED clean_data_eligible=false; reviewer decision cannot bypass explicit policy gate
evidence_preview_review_result（证据预览审查结果）= PASS，bounded previews and metadata retained; full_source_text not copied into review items
reviewer_action_model_review_result（复核动作模型审查结果）= PASS，required actions present; unsupported actions fail closed
boundary_check（边界检查）= PASS，docs-only QA; no datefac_agent/tests/fixture/output/dependency changes in QA; no MinerU/OCR/LLM/VLM; readiness untouched
readiness_gates（就绪门）= CLOSED，client_ready=false; production_ready=false; formal_client_export_allowed=false; demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AR discrepancy review queue integration boundary design
```
