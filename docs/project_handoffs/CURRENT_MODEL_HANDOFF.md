# Current Handoff

## Workspace

```text
D:\_datefac_agent
pivot/348-agent-foundation
```

## Current task

```text
348N-R7AM test-only MinerU artifact adapter prototype
```

Task sizing:

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = implementation-with-self-QA
reason = R7AL completed a controlled DateFac-vs-MinerU dry-run; R7AM should turn the proven local comparison shape into a small test-only adapter prototype.
```

Task document:

```text
docs/codex_tasks/348N_R7AM_test_only_mineru_artifact_adapter_prototype.md
```

Expected report:

```text
docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md
```

Allowed R7AM files:

```text
tests/agent/mineru_artifact_adapter_348n.py
tests/agent/test_mineru_artifact_adapter_348n.py
tests/agent/fixtures/mineru_artifacts/anjing_minimal_content_list_v2__r7am.json
docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md
```

## Latest completed local result

```text
R7AL Anjing DateFac-vs-MinerU controlled comparison dry-run
Decision = COMPLETED_CONTROLLED_COMPARISON_DRY_RUN
DateFac candidate rows normalized = 451
MinerU blocks indexed = 173
VERIFIED = 395
review_required_total = 56
DISAGREED = 10
AMBIGUOUS = 10
MISSING_EVIDENCE = 2
required 11 probe examples = all found and VERIFIED against MinerU v2 blocks
primary input recommendation = content_list_v2
fallback/cross-check = content_list
commit = none
push = none
readiness_gates = CLOSED
```

Local R7AL outputs are under:

```text
D:\_datefac_agent\output\comparison\anjing_foods_datefac_vs_mineru\
```

Do not commit these local output files.

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

Execute R7AM. Keep it test-only. Use a small curated MinerU-like fixture, not the full real MinerU output. Do not modify production code or open readiness gates.
