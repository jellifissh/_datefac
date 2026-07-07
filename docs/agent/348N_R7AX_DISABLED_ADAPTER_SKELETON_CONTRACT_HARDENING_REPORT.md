# 348N-R7AX disabled adapter skeleton contract hardening report

## Task ID

```text
348N-R7AX disabled adapter skeleton contract hardening
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating a98ae83..17fd029
  Fast-forward
  docs/codex_tasks/348N_R7AX_disabled_adapter_skeleton_contract_hardening.md created

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
```

Worktree was clean after pull and before R7AX changes.

## Files reviewed

- `docs/codex_tasks/348N_R7AX_disabled_adapter_skeleton_contract_hardening.md`
- `docs/agent/348N_R7AW_QA_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REVIEW.md`
- `docs/agent/348N_R7AW_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REPORT.md`
- `docs/agent/348N_R7AV_QA_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST_REVIEW.md`
- `docs/agent/348N_R7AU_QA_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REVIEW.md`
- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json`

## R7AW-QA recap

R7AW-QA confirmed the skeleton was valid as a disabled-by-default, no-hook, no-IO, metadata-first adapter skeleton. It also identified the next hardening need: malformed boundary-like payloads should fail closed without turning the skeleton into a production hookup.

## Files modified

Allowed files modified:

- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json`
- `docs/agent/348N_R7AX_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REPORT.md`

No other tracked files were modified.

## Hardening summary

R7AX keeps the R7AW skeleton disabled by default and adds stricter enabled-mode contract validation:

```text
expected adapter contract_version required
unexpected top-level boundary fields rejected
required audit metadata expanded and checked
input_file_hashes must be non-empty
status count totals must match metadata counts
review item evidence_preview required and bounded
discrepancy report rows validated explicitly
blocked delivery rows validated explicitly
delivery candidates validated explicitly
unresolved non-VERIFIED delivery candidates rejected
parser-like payload keys rejected recursively
```

## Input contract hardening

New checks:

```text
unexpected contract_version -> fail closed
unexpected top-level boundary fields -> fail closed
missing audit metadata -> fail closed
empty input_file_hashes -> fail closed
review_queue_status_counts mismatch -> fail closed
unknown agreement_status -> fail closed
nested source_text -> fail closed
parser-like payload -> fail closed
```

Parser-like forbidden keys now include:

```text
parser_output
pdf_parser_output
pdf_pages
raw_pdf_pages
page_texts
text_layer
extracted_pages
extracted_text
mineru_output
ocr_output
blocks
table_blocks
tables
html
markdown
```

## Reviewer action hardening

Reviewer actions are now checked across:

```text
review_queue_items
discrepancy_report_rows
blocked_delivery_rows
delivery_clean_candidates
```

Unsupported actions such as `AUTO_PROMOTE_TO_CLEAN` fail closed.

## Clean data and delivery guard

Preserved and hardened behavior:

```text
clean_data_eligible=true -> fail closed
delivery_clean_admitted=true -> fail closed
VERIFIED -> review_queue_candidate_items = never automatic
VERIFIED -> clean_data = never automatic
non-VERIFIED delivery candidates require resolved review_status and valid reviewer action
unresolved non-VERIFIED delivery candidates -> fail closed
blocked_delivery_rows must remain unresolved non-VERIFIED rows
```

## Evidence preview hardening

Evidence previews are now required where the skeleton relies on evidence preview metadata:

```text
review_queue_items.evidence_preview required and bounded
discrepancy_report_rows.evidence_preview required and bounded
oversized evidence_preview -> fail closed
missing evidence_preview -> fail closed
evidence_preview_sha256 remains metadata-only
full source_text remains rejected
```

## Audit metadata hardening

Required audit metadata now includes:

```text
run_id
adapter_version
input_file_hashes
comparison_row_count
comparison_status_counts
review_queue_count
review_queue_status_counts
discrepancy_report_count
delivery_clean_candidate_count
blocked_delivery_row_count
verified_without_clean_gate_count
readiness_gates
external_call_counts
boundary_flags
audit_metadata_hash
```

Metadata checks also confirm closed readiness gates, zero external calls, non-empty hashes, and matching status-count totals.

## Determinism and immutability

Tests confirm:

```text
adapter_item_id remains deterministic
adapter_audit_hash remains deterministic
review_item_id is preserved
audit_hash is preserved
output input_file_hashes do not share mutable input references
output readiness_gates do not share mutable input references
```

## No-hook and no-IO review

R7AX preserved R7AW boundaries:

```text
disabled by default = yes
explicit test-only enable required = yes
pipeline hook added = no
file/database/export/local output write = no
MinerU/OCR/LLM/VLM/PDF extraction = no
new dependency = no
readiness gate opened = no
```

The skeleton module remains in-memory only.

## Fixture result

Fixture updated:

```text
tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
```

Added invalid parser-like payload:

```text
invalid_parser_like_payload
```

Existing fixture coverage remains:

```text
disabled default case
valid boundary output
raw MinerU-like invalid case
raw Excel-like invalid case
full source_text invalid case
VERIFIED row
DISAGREED row
AMBIGUOUS row
unresolved rows
corrected re-audit row
```

## Test result

Test file updated:

```text
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
```

Targeted test count increased:

```text
before R7AX = 15 tests
after R7AX = 26 tests
```

Added coverage:

```text
unexpected contract_version
unexpected top-level boundary fields
nested source_text
missing audit metadata
empty input_file_hashes
status count mismatch
unknown agreement_status
unknown reviewer_action across row types
unresolved non-VERIFIED delivery candidate
missing required evidence_preview
output mutable reference isolation
parser-like payload rejection through fixture invalid cases
```

## Validation outputs

Required commands run:

```text
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
  PASS

python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
  PASS

pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
  26 passed in 0.12s

pytest tests/agent -q
  266 passed in 0.98s

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
   M datefac_agent/review/production_boundary_review_queue_adapter.py
   M tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
   M tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
  ?? docs/agent/348N_R7AX_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REPORT.md

git diff --stat
  datefac_agent/review/production_boundary_review_queue_adapter.py | 163 ++++++++++++++++++++-
  tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json | 13 ++
  tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py | 132 +++++++++++++++++
  3 files changed, 300 insertions(+), 8 deletions(-)

git diff --name-only
  datefac_agent/review/production_boundary_review_queue_adapter.py
  tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
  tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py

git diff --check
  PASS
```

## Limitations

- R7AX hardens the disabled skeleton contract only.
- It does not add production pipeline hookup, persistence, output writing, or readiness changes.
- The fixture remains curated and synthetic.
- The skeleton still requires future QA before any broader integration step.

## Decision

```text
Decision = 348N_R7AX_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_VALID
```

R7AX hardens malformed boundary-like payload rejection while preserving the core R7AW boundary: disabled by default, explicit test-only enable required, no IO, no production hook, no clean-data admission, no readiness opening, and no promotion of VERIFIED to STRONG_EVIDENCE.

## Recommended next task

```text
348N-R7AX-QA disabled adapter skeleton contract hardening review
```

## Data Result / 数据结果

```text
Decision = PASS：348N_R7AX_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_VALID
build_result = PASS：py_compile validation passed
test_result = PASS：pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q => 26 passed；pytest tests/agent -q => 266 passed
files_modified = 4
error_count = 0
hardening_result = PASS：enabled-mode contract validation strengthened without changing disabled default behavior
input_contract_hardening_result = PASS：unexpected contract_version, malformed top-level fields, unknown status, parser-like payload, nested source_text, and metadata mismatches fail closed
reviewer_action_hardening_result = PASS：unsupported reviewer actions fail closed across review, discrepancy, blocked delivery, and delivery candidate rows
clean_data_delivery_guard_result = PASS：clean_data_eligible=true, delivery_clean_admitted=true, and unresolved non-VERIFIED delivery candidates fail closed
evidence_preview_hardening_result = PASS：required previews are enforced and oversized previews fail closed
audit_metadata_hardening_result = PASS：run_id / adapter_version / input_file_hashes / status counts / audit metadata hash / readiness / external-call counters are validated
determinism_immutability_result = PASS：adapter IDs and hashes remain stable; output does not share mutable input references
no_hook_no_io_result = PASS：no pipeline hook, IO, parser/model call, extraction call, or dependency change
boundary_check = PASS：only the four allowed files changed
readiness_gates = CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task = 348N-R7AX-QA disabled adapter skeleton contract hardening review
```
