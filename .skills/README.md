# Skills Index

## Current Mainline

The current effective mainline is:

```text
DateFac Agent foundation / extraction audit workflow
```

The active new package is:

```text
datefac_agent/
```

Legacy extraction, MinerU benchmark, and client-preview chains remain reference assets, not the default direction for new work.

## Read Order For New Contributors And Codex

For any new numbered DateFac task, read in this order:

1. `AGENTS.md`
2. `.skills/git_workflow.md`
3. `.skills/datefac_agent_foundation.md`
4. `.skills/agent_excel_intake_audit_workflow.md`
5. `.skills/project_milestone_ledger.md`
6. `datefac_agent/README.md`
7. `datefac_agent/PROJECT_BACKGROUND.md`
8. `datefac_agent/CODE_MIGRATION_PLAN.md`
9. `docs/project_strategy/348_agent_pivot_brief.md`
10. `docs/agent/AGENT_ARCHITECTURE.md`
11. `docs/agent/348A_INPUT_OUTPUT_CONTRACT.md`
12. `docs/agent/FIXTURE_STRATEGY.md`
13. `docs/legacy/LEGACY_ASSET_MAP.md`
14. the latest relevant task doc under `docs/codex_tasks/`

Read legacy skills only when the task explicitly touches their area:

- `.skills/mineru_local_benchmark_workflow.md`
- `.skills/real_pdf_benchmark_workflow.md`
- `.skills/human_reviewed_client_preview_workflow.md`
- `.skills/table_extraction.md`
- `.skills/asset_artifacts.md`
- `.skills/financial_standardizer.md`
- `.skills/regression_validation.md`
- `.skills/environment_troubleshooting.md`

## Skill Purposes

- `datefac_agent_foundation.md`: current Agent pivot, new package boundaries, legacy freeze rules, and migration posture
- `agent_excel_intake_audit_workflow.md`: 348A-style Excel intake audit workflow, output contract, and no-MinerU/no-LLM boundaries
- `project_milestone_ledger.md`: numbered-task preflight, no-repeat rules, ledger update requirements, rollup rules, and readiness flag discipline
- `git_workflow.md`: staging and protected-dirty-file rules
- `mineru_local_benchmark_workflow.md`: legacy MinerU workflow plus MinerU 3.3.1 sidecar notes; not the 348A mainline
- `asset_artifacts.md`: asset-layer meaning and evidence boundaries
- `table_extraction.md`: legacy parser strategy and extraction evidence order; use only for extraction tasks
- `financial_standardizer.md`: standardization-layer rules and guardrails; mine for Agent audit rules, do not wholesale copy
- `regression_validation.md`: validation expectations by task type
- `human_reviewed_client_preview_workflow.md`: legacy `340B-341B` trusted preview chain
- `real_pdf_benchmark_workflow.md`: legacy `342A-342C4` benchmark chain
- `environment_troubleshooting.md`: env split, SSL, package provenance, and HF repair guidance

## Current Safety Summary

Default current work should happen under:

```text
D:\_datefac_agent
pivot/348-agent-foundation
```

Default current code path should be:

```text
datefac_agent/
tests/agent/
docs/agent/
docs/legacy/
```

Do not treat old MinerU benchmark, old PDF extraction, or 346B recovery expansion as the active mainline unless a task explicitly says so.
