# Current Handoff

## Workspace

```text
D:\_datefac_agent
pivot/348-agent-foundation
```

## Current task

```text
348N-R7AO test-only MinerU adapter controlled comparison runner
```

Task sizing:

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = single-run-data-analysis + no-commit
reason = R7AN completed the dry-run design. R7AO should execute the local controlled comparison runner with full Anjing DateFac Excel and full local MinerU content_list_v2, using the R7AM adapter shape, without committing local outputs or modifying production code.
```

Task document:

```text
docs/codex_tasks/348N_R7AO_test_only_mineru_adapter_controlled_comparison_runner.md
```

Local output directory:

```text
D:\_datefac_agent\output\comparison\anjing_foods_mineru_adapter_r7ao\
```

Expected local outputs, not committed:

```text
run_r7ao_mineru_adapter_comparison.py
r7ao_mineru_adapter_comparison_report.xlsx
r7ao_mineru_adapter_comparison_summary.md
r7ao_mineru_adapter_evidence_rows.csv
r7ao_mineru_adapter_unmatched_rows.csv
r7ao_mineru_adapter_run_metadata.json
```

## Latest completed result

```text
R7AN commit = f29cc07 docs: add R7AN controlled comparison design
Decision = PASS
pytest tests/agent/test_mineru_artifact_adapter_348n.py -q = 21 passed
pytest tests/agent -q = 201 passed
files_modified = 1
input_scope_decision = full Anjing DateFac Excel + full local MinerU content_list_v2 for R7AO, optional smoke mode only
runner_scope_decision = local test-only runner under output/comparison/anjing_foods_mineru_adapter_r7ao/
adapter_usage_decision = reuse tests.agent.mineru_artifact_adapter_348n directly
output_policy_decision = write local xlsx/csv/md/json reports, do not commit outputs
boundary_check = PASS
readiness_gates = CLOSED
```

## R7AO input policy

Required:

```text
D:\_datefac_agent\output\datefac_raw_material_anjing_foods.xlsx
one resolved *H3_AP202606081823352906_1*content_list_v2.json
```

MinerU search roots:

```text
E:\mineru331\smoke_output\H3_AP202606081823352906_1\auto
E:\mineru331\smoke_output\H3_AP202606081823352906_1
E:\mineru331\smoke_output
E:\mineru331
E:\mineru_lab
```

## Current boundaries

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
output files are not committed
MinerU / OCR / LLM / VLM remain unused unless explicitly allowed
VERIFIED is not automatic clean admission
VERIFIED is not STRONG_EVIDENCE
VERIFIED is not production readiness
agent tasks should stage only explicit allowed paths
```

## Next-step guidance

Execute R7AO locally. No commit, no push. If R7AO passes, recommended next task should normally be `348N-R7AO-QA test-only MinerU adapter controlled comparison runner review`.
