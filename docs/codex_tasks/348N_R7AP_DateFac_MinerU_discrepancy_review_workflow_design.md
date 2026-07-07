# 348N-R7AP DateFac-MinerU discrepancy review workflow design

```text
task_size = small
recommended_reasoning_level = max
execution_mode = design-review-only
reason = R7AO-QA confirmed the local controlled comparison runner and outputs are valid. R7AP should design how non-VERIFIED rows become an auditable discrepancy review workflow before any production integration.
```

## Goal

Design a workflow for rows where DateFac candidate output and MinerU evidence do not cleanly agree.

This task is design-only. Do not implement code, create runners, add fixtures, add dependencies, run MinerU/OCR/LLM/VLM, or open readiness gates.

## Background

R7AO-QA passed with:

```text
total rows = 451
VERIFIED = 402
non-VERIFIED = 49
DISAGREED = 5
AMBIGUOUS = 10
MISSING_EVIDENCE = 1
PARSE_SKIPPED = 18
probe examples = 11/11 VERIFIED
readiness_gates = CLOSED
commit = 6e02622
```

R7AP should focus on what happens to the 49 non-VERIFIED rows.

## Required preflight

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -12
```

If the worktree is not clean after pull, stop and report.

## Required reading

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348N_R7AO_QA_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_RUNNER_REVIEW.md
docs/agent/348N_R7AN_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_DRY_RUN_DESIGN.md
docs/agent/348N_R7AM_QA_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REVIEW.md
```

Review production boundary files read-only:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/delivery/evidence_index_writer.py
```

Read local R7AO outputs if present, but do not commit them:

```text
D:\_datefac_agent\output\comparison\anjing_foods_mineru_adapter_r7ao\
```

## Design questions

Answer these in the report:

```text
What happens to VERIFIED rows?
What happens to DISAGREED rows?
What happens to AMBIGUOUS rows?
What happens to MISSING_EVIDENCE rows?
What happens to PARSE_SKIPPED rows?
Which statuses enter review_queue in a future implementation?
Which statuses are excluded from clean_data automatically?
What fields should a discrepancy review item contain?
How should evidence previews be stored without dumping full source_text?
What reviewer actions are needed?
How do reviewer decisions affect clean_data eligibility?
How are unresolved rows exported or hidden from delivery?
How are table-vs-paragraph conflicts shown?
How are parse failures separated from true evidence disagreement?
What severity ranking should be used?
What metrics should discrepancy reports show?
What is the safest next task?
```

## Required decisions

The report must decide:

```text
verified_row_policy
disagreed_row_policy
ambiguous_row_policy
missing_evidence_row_policy
parse_skipped_row_policy
review_queue_admission_policy
clean_data_exclusion_policy
review_item_schema
reviewer_action_model
post_review_clean_data_policy
evidence_preview_policy
severity_model
reporting_metrics
export_policy
reproducibility_policy
future_implementation_scope
next_task_name
```

## Suggested review item fields

Consider at least:

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
reviewer_note
reviewed_at
reviewed_by
audit_hash
run_id
adapter_version
input_file_hashes
```

## Suggested reviewer actions

Consider at least:

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

## Boundaries

Forbidden:

```text
modify datefac_agent/
modify tests/
create implementation
create runner script
create fixtures
commit local output files
commit DateFac Excel
commit MinerU output
run MinerU/OCR/LLM/VLM
run real PDF extraction
add dependencies
promote VERIFIED to STRONG_EVIDENCE
promote VERIFIED directly to clean_data without a future policy gate
open readiness gates
use broad git staging
```

Allowed:

```text
create one design report under docs/agent/
read local R7AO outputs if present
run validation commands
```

## Validation commands

```text
python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
pytest tests/agent/test_mineru_artifact_adapter_348n.py -q
pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

## Allowed file

Create exactly one tracked file:

```text
docs/agent/348N_R7AP_DATEFAC_MINERU_DISCREPANCY_REVIEW_WORKFLOW_DESIGN.md
```

## Expected report

The report must include:

```text
Task ID
Preflight
Files reviewed
R7AO-QA recap
Discrepancy taxonomy
Row policy matrix
Review queue admission policy
Review item schema design
Reviewer action model
Evidence preview policy
Severity model
Post-review clean_data policy
Export / delivery policy
Reproducibility and audit policy
Future implementation slice
Boundary review
Validation outputs
Limitations
Decision
Recommended next task
Data Result / 数据结果
```

Data Result must include:

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
discrepancy_taxonomy_result（差异分类结果）=
review_queue_policy_result（复核队列策略结果）=
review_item_schema_result（复核项schema结果）=
reviewer_action_model_result（复核动作模型结果）=
clean_data_policy_result（clean_data策略结果）=
export_policy_result（导出策略结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should normally be:

```text
348N-R7AQ test-only discrepancy review queue fixture and policy prototype
```

## Commit / push

If validation passes and only the design report is created, stage exactly:

```text
git add docs/agent/348N_R7AP_DATEFAC_MINERU_DISCREPANCY_REVIEW_WORKFLOW_DESIGN.md
git commit -m "docs: add R7AP discrepancy workflow design"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
