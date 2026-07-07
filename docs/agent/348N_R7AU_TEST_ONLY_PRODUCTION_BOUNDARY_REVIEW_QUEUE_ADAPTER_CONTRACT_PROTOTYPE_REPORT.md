# 348N-R7AU test-only production-boundary review queue adapter contract prototype report

## Task ID

```text
348N-R7AU test-only production-boundary review queue adapter contract prototype
```

## Task size / reasoning level used

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-contract-prototype
reason = R7AT-QA passed and approved a conservative production-boundary adapter design. R7AU proves that contract shape in tests only, with compact curated fixtures and no production wiring.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating ecb5908..6e3070c
  Fast-forward
  docs/codex_tasks/348N_R7AU_test_only_production_boundary_review_queue_adapter_contract_prototype.md created

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  6e3070c docs: add R7AU contract prototype task
  ecb5908 docs: add R7AT QA review
  897681a docs: add R7AT production boundary adapter design
  b402e57 docs: add R7AS QA review
  5bddf67 test: add discrepancy review queue integration boundary prototype
  f01bd54 docs: add R7AR integration boundary design
  a9e1637 docs: add R7AQ QA review
  0fb9a3d test: add discrepancy review queue policy prototype
  f68c59b docs: add R7AP discrepancy workflow design
  0634345 docs: update handoff after R7AO QA
  607a782 docs: refresh plain-language progress after R7AO QA
  046e66f docs: sync progress after R7AO QA
```

Worktree was clean after pull and before R7AU file creation.

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
- `docs/agent/348N_R7AT_QA_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_DESIGN_REVIEW.md`
- `docs/agent/348N_R7AT_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_DESIGN.md`
- `docs/agent/348N_R7AS_QA_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7AS_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_PROTOTYPE_REPORT.md`

Read-only implementation context:

- `tests/agent/discrepancy_review_queue_integration_boundary_348n.py`
- `tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py`
- `tests/agent/discrepancy_review_queue_policy_348n.py`
- `tests/agent/test_discrepancy_review_queue_policy_348n.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/delivery/evidence_index_writer.py`

## Files created

Created exactly the requested R7AU files:

- `tests/agent/production_boundary_review_queue_adapter_contract_348n.py`
- `tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7au_production_boundary_contract_fixture.json`
- `docs/agent/348N_R7AU_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REPORT.md`

No `datefac_agent/` production files, existing tests, existing fixtures, outputs, dependency/config files, DateFac Excel files, or MinerU outputs were modified.

## Fixture result

Fixture:

```text
tests/agent/fixtures/discrepancy_review_queue/r7au_production_boundary_contract_fixture.json
```

Fixture facts:

```text
schema_version = 1
fixture_scope = test_only_r7au
fixture_size_bytes = 10218
valid_comparison_boundary_payload rows = 8
invalid_inputs = 3
```

Valid row coverage:

```text
VERIFIED = 1
DISAGREED = 2
AMBIGUOUS = 1
MISSING_EVIDENCE = 2
PARSE_SKIPPED = 1
UNVERIFIED = 1
resolved reviewer correction row = included
unresolved reviewer action row = included
```

Invalid input coverage:

```text
invalid_raw_mineru_like_input = covered
invalid_raw_excel_like_input = covered
invalid_full_source_text_input = covered
```

The fixture is curated and synthetic. It does not contain real R7AO output, DateFac Excel, complete MinerU output, or full source text.

## Contract prototype result

Prototype:

```text
tests/agent/production_boundary_review_queue_adapter_contract_348n.py
```

Implemented test-only helpers:

```text
load_contract_fixture(...)
build_boundary_output_from_fixture(...)
load_boundary_output_from_comparison_fixture(...)
build_production_boundary_review_queue_contract(...)
validate_boundary_output_shape(...)
validate_no_forbidden_fields(...)
```

The prototype accepts only the R7AS-style boundary output shape:

```text
review_queue_items
discrepancy_report_rows
delivery_clean_candidates
blocked_delivery_rows
audit_metadata
```

It rejects direct raw comparison payloads and raw artifact-like payloads before creating contract output.

## Input rejection result

Fail-closed input behavior:

```text
raw MinerU-like input -> rejected
raw DateFac Excel-like input -> rejected
full source_text input -> rejected
direct comparison payload instead of boundary output -> rejected
unsupported reviewer action -> rejected
opened readiness gate -> rejected
delivery_clean_admitted=true -> rejected
missing run_id / adapter_version / input_file_hashes -> rejected
unbounded evidence_preview -> rejected
```

Forbidden payload fields include:

```text
source_text
full_source_text
source_text_full
full_text
raw_mineru_block
raw_mineru_artifact
content_list_v2
full_table_html
raw_pdf_text
raw_excel_row
raw_datefac_excel_row
datefac_excel_rows
workbook_sheets
worksheets
cells
```

## Review queue contract result

Observed contract counts:

```text
review_queue_contract_count = 7
discrepancy_report_contract_count = 7
blocked_delivery_contract_count = 6
delivery_reaudit_contract_count = 1
clean_data_eligible_contract_count = 0 by default
verified_review_queue_contract_count = 0
```

Observed status counts:

```text
DISAGREED = 2
AMBIGUOUS = 1
MISSING_EVIDENCE = 2
PARSE_SKIPPED = 1
UNVERIFIED = 1
```

Contract item fields include:

```text
contract_item_id
review_item_id
source_document_id
source_row_id
candidate_metric_name
candidate_period
candidate_value
candidate_unit
agreement_status
subqueue
risk_reason
severity
review_status
reviewer_action
clean_data_eligible
delivery_blocked
evidence_preview
matched_locator
run_id
adapter_version
input_file_hashes
audit_hash
contract_version
created_from
```

`VERIFIED` rows do not produce review queue contract items.

## Delivery gate contract result

Delivery contract outputs:

```text
blocked_delivery_contract_rows = 6
delivery_reaudit_contract_rows = 1
```

Rules proven:

```text
unresolved non-VERIFIED rows become blocked delivery contract rows.
resolved correction row is not clean delivery; it remains a re-audit contract row.
delivery_clean_admitted remains false.
requires_reaudit_before_clean_delivery remains true.
```

## Clean data gate contract result

Clean-data guard behavior:

```text
VERIFIED rows do not bypass clean_data gate.
non-VERIFIED rows default clean_data_eligible=false.
unreviewed rows cannot become clean_data.
explicit_future_policy_gate is required for clean_data_eligible=true.
even with explicit_future_policy_gate, delivery_clean_admitted remains false.
```

Default contract:

```text
explicit_future_policy_gate = false
clean_data_eligible_contract_count = 0
```

Gated contract test:

```text
explicit_future_policy_gate = true
resolved correction row can become clean_data_eligible=true as a re-audit candidate only.
delivery_clean_admitted remains false.
```

## Audit contract result

Observed audit contract:

```text
contract_version = r7au_production_boundary_review_queue_contract_test_only_v1
created_from = r7as_discrepancy_boundary_output
run_id = r7au_fixture_run_001
adapter_version = r7as_integration_boundary_test_only_v1
input_file_hashes.datefac_excel = sha256:r7au-datefac-fixture
input_file_hashes.mineru_content_list_v2 = sha256:r7au-mineru-fixture
source_audit_metadata_hash = a994a63659a503d0812133e65b116d154cc6b69782a4cb26f3a8f96b49268ed7
audit_contract_hash = 16c259c7cead832b6c97bd0a7c4a3ac023e6a9b9bd4d12d9400799fe7cff77b8
```

Hash behavior:

```text
contract_item_id is deterministic.
review_item_id is preserved from R7AS/R7AQ boundary output.
audit_hash is preserved from R7AS/R7AQ boundary output.
audit_contract_hash is deterministic.
```

Readiness and external calls:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
mineru_run_count = 0
ocr_run_count = 0
llm_api_call_count = 0
vlm_api_call_count = 0
```

## Test coverage

Created:

```text
tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py
```

Test coverage:

- fixture loads and stays curated
- valid discrepancy boundary output is accepted
- direct non-boundary payload is rejected
- raw MinerU-like input is rejected
- raw Excel-like input is rejected
- full source text input is rejected
- VERIFIED rows do not auto-clean
- all non-VERIFIED rows become review queue contract items
- unresolved rows become blocked delivery contract rows
- discrepancy rows remain metadata-first and bounded-preview only
- stable `contract_item_id`, `review_item_id`, `audit_hash`, and `audit_contract_hash`
- unsupported reviewer actions fail closed
- explicit future policy gate is required for clean-data eligibility
- readiness gates remain closed and fail closed if changed
- helper has no `datefac_agent/` production import or heavy parser hooks

## Validation outputs

Required commands run:

```text
python -m py_compile tests/agent/production_boundary_review_queue_adapter_contract_348n.py tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py
  PASS

python -m py_compile tests/agent/discrepancy_review_queue_integration_boundary_348n.py tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py
  PASS

python -m py_compile tests/agent/discrepancy_review_queue_policy_348n.py tests/agent/test_discrepancy_review_queue_policy_348n.py
  PASS

python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
  PASS

python -m py_compile datefac_agent/review/clean_candidate_policy.py
  PASS

python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
  PASS

pytest tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py -q
  13 passed

pytest tests/agent -q
  240 passed

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  ?? docs/agent/348N_R7AU_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REPORT.md
  ?? tests/agent/fixtures/discrepancy_review_queue/r7au_production_boundary_contract_fixture.json
  ?? tests/agent/production_boundary_review_queue_adapter_contract_348n.py
  ?? tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py

git diff --stat
  no tracked diff before staging because new files were untracked

git diff --name-only
  no tracked diff before staging because new files were untracked

git diff --check
  PASS
```

## Boundary review

R7AU stayed within scope:

```text
datefac_agent/ modified = no
existing tests modified = no
existing fixtures modified = no
production pipeline modified = no
runner created = no
local output report created = no
DateFac Excel committed = no
MinerU output committed = no
MinerU run = no
OCR / LLM / VLM run = no
real PDF extraction = no
dependency/config files modified = no
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

## Limitations

- This is a test-only contract prototype under `tests/agent/`.
- It does not create a production adapter in `datefac_agent/`.
- It uses a compact curated fixture, not full R7AO local outputs.
- It produces in-memory contract structures only.
- Reviewer persistence, authorization, UI, and production audit logging remain future work.
- Clean-data admission remains out of scope and requires a separate future gate.

## Decision

```text
Decision = 348N_R7AU_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_VALID
```

R7AU proves the future production-boundary review queue adapter contract shape with test-only fixtures. It accepts only validated discrepancy boundary output, rejects raw MinerU/Excel/full-source inputs, maps all non-VERIFIED rows to review queue contract items, blocks unresolved delivery rows, keeps discrepancy rows metadata-first and bounded, preserves audit metadata and deterministic hashes, requires an explicit future policy gate for clean-data eligibility, and keeps readiness gates closed.

## Recommended next task

```text
348N-R7AU-QA test-only production-boundary review queue adapter contract prototype review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：348N_R7AU_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_VALID
build_result（构建结果）= PASS：py_compile validation passed
test_result（测试结果）= PASS：pytest tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py -q => 13 passed；pytest tests/agent -q => 240 passed
files_modified（修改文件数）= 4
error_count（错误数）= 0
fixture_result（fixture结果）= PASS：8-row curated valid payload plus invalid raw MinerU-like / raw Excel-like / full-source-text inputs
contract_prototype_result（契约原型结果）= PASS：test-only helper converts R7AS boundary output to in-memory production-boundary review queue contract structures
input_rejection_result（输入拒绝结果）= PASS：raw artifacts, direct comparison payloads, full source_text, unsupported actions, opened readiness, and clean admission attempts fail closed
review_queue_contract_result（复核队列契约结果）= PASS：7 non-VERIFIED rows become contract items; VERIFIED excluded; deterministic contract_item_id/review_item_id/audit_hash retained
delivery_gate_contract_result（交付闸门契约结果）= PASS：6 unresolved rows become blocked delivery contract rows; resolved correction remains re-audit-only and not clean delivery
clean_data_gate_contract_result（clean_data闸门契约结果）= PASS：default clean_data_eligible=false; explicit future policy gate required; no delivery_clean_admitted
audit_contract_result（审计契约结果）= PASS：run_id / adapter_version / input_file_hashes / source audit hash / contract hash / readiness snapshot / zero external calls retained
boundary_check（边界检查）= PASS：tests/docs/fixture only; no datefac_agent/ changes; no output/DateFac/MinerU/dependency commits; no MinerU/OCR/LLM/VLM/PDF extraction
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AU-QA test-only production-boundary review queue adapter contract prototype review
```
