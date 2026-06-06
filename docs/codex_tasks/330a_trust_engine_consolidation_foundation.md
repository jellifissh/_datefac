# DateFac 330A Task
## Trust Engine Consolidation Foundation

## Context

The 325 alias patch cycle is closed.

325P output:

```text
D:\_datefac\output\alias_patch_cycle_closure_325p
```

325P result:

```text
325A input_alias_inventory_count = 211
325A safe_alias_review_batch_count = 12
325D send_to_adjudicator_count = 6
325E request_count = 6
325G accepted_for_human_confirmation_count = 6
325H confirmed_count = 6
325I sandbox_alias_rule_count = 6
325J ready_candidate_count = 6
325K ready_proposal_count = 6
325L patch_operation_count = 6
325M approved_patch_operation_count = 6
325N applied_or_idempotent_operation_count = 6
325O visible_official_alias_rule_count = 6

official_alias_rule_count_325 = 6
trusted_gain_325 = 45
review_reduction_325 = 45
out_of_scope_or_rejected_gain_325 = 0
affected_candidate_count_325 = 45

cumulative_official_rule_count_after_325 = 23
cumulative_trusted_gain_after_325 = 138
cumulative_review_reduction_after_325 = 503
cumulative_out_of_scope_or_rejected_gain_after_325 = 365

qa_fail_count = 0
decision = ALIAS_PATCH_CYCLE_325P_CLOSED_WITH_WARNINGS_READY_FOR_TRUST_ENGINE_CONSOLIDATION
```

Residual warnings:

```text
- existing alias official asset contains historical mojibake/encoding artifacts
- 325O validates official visibility, target mapping, and cached impact, not full production semantic recalculation
- remaining burden is inherited from 323P and not recomputed in 325P
```

The next project direction is not another rule mining cycle. The next direction is to consolidate 323/324/325 safety flows into a reusable Trust Engine foundation.

## Goal

Implement 330A: Trust Engine Consolidation Foundation.

330A must introduce a small, stable trust layer package that standardizes candidate confidence records, risk flags, routing decisions, and no-apply reporting. It must not change production extraction behavior yet.

This stage is architectural consolidation, not a new rule mining cycle.

## Hard constraints

- Do not start 326A or any new alias/scope/unit rule mining cycle.
- Do not modify production pipeline behavior.
- Do not modify parser/extraction/delivery code behavior.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM or semantic adjudicator.
- Do not recompute production outputs.
- Use cached 323/324/325 artifacts only for schema examples and smoke fixtures.
- Do not commit output, temp, input/semantic_adjudicator_responses_*, or existing dirty files.
- Do not use git add -A or git add .
- Only precisely add 330A trust-layer source/report/runner/test/docs files.

Existing dirty files to leave untouched:

```text
datefac/benchmark/batch_row_text_delivery_benchmark.py
datefac/extraction/row_text_metric_extractor.py
datefac/pipeline/batch_ppstructure_row_text_pipeline.py
tools/run_batch_ppstructure_outputs_320g.py
input/semantic_adjudicator_responses_322d/
input/semantic_adjudicator_responses_322f/
temp/
```

## Scope

Create the foundation for a reusable Trust Engine package.

Suggested package files:

```text
datefac/trust/__init__.py
datefac/trust/schema.py
datefac/trust/risk_registry.py
datefac/trust/routing_policy.py
datefac/trust/no_apply_proof.py
```

Suggested report/runner files:

```text
datefac/trust/trust_engine_foundation_330a_report.py
tools/run_trust_engine_foundation_330a.py
```

Optional tests if the project test structure is available and lightweight:

```text
tests/trust/test_trust_engine_foundation_330a.py
```

Do not edit existing production modules to import this package in 330A unless only for non-invasive compile checks. Integration should be a later stage.

## Required data model

Define stable enums/constants or dataclasses for:

### Routing decisions

```text
TRUSTED
REVIEW_REQUIRED
REJECTED
NEEDS_MORE_INFO
OUT_OF_SCOPE
```

### Confidence levels

```text
HIGH
MEDIUM
LOW
UNKNOWN
```

### Risk severities

```text
BLOCKING
WARNING
INFO
```

### Risk flags

At minimum include:

```text
UNIT_UNKNOWN
UNIT_CONFLICT
YEAR_MISSING
YEAR_MISMATCH
VALUE_PARSE_FAILED
PARSER_CONFLICT
LOW_EVIDENCE_STRENGTH
LABEL_AMBIGUOUS
TARGET_METRIC_AMBIGUOUS
SCOPE_NOISE_RISK
ALIAS_MAPPING_RISK
ADJUSTED_METRIC_RISK
DILUTED_EPS_RISK
LONG_NARRATIVE_LABEL
TABLE_STRUCTURE_UNSTABLE
OFFICIAL_RULE_CONFLICT
HISTORICAL_DUPLICATE_WARNING
MOJIBAKE_ENCODING_ARTIFACT
```

Each risk definition should include:

```text
risk_code
severity
blocking
description
recommended_action
```

### Trust record schema

Define a serializable candidate trust record that can represent future candidate-level trust decisions:

```text
candidate_id
metric_label_raw
normalized_metric
value
unit
year
parser_sources
evidence_refs
risk_flags
blocking_risks
warning_risks
confidence_score
confidence_level
evidence_score
semantic_score
unit_year_score
parser_agreement_score
risk_penalty
routing_decision
decision_reasons
next_action
provenance
```

The record must be JSON-serializable.

## Required behavior

1. Provide constructors/helpers to build a trust record from plain dictionaries.
2. Normalize risk flags through the registry.
3. Derive blocking and warning risk lists.
4. Provide a deterministic routing helper:

```text
- any blocking risk -> REVIEW_REQUIRED or REJECTED depending on caller policy
- score >= 85 and no blocking risk -> TRUSTED
- score >= 60 -> REVIEW_REQUIRED
- score < 60 -> NEEDS_MORE_INFO or REJECTED depending on caller policy
```

5. Provide a no-apply proof helper confirming that 330A did not modify official assets.
6. Provide a 330A runner that:
   - validates 325P closure readiness from cached output
   - generates a small Trust Engine foundation summary
   - creates example trust records for at least 3 cases:
     - high-confidence trusted candidate
     - review-required candidate with warning risks
     - rejected or needs-more-info candidate with blocking risks
   - writes output artifacts to a 330A output directory
   - confirms official assets are not modified

## Output directory

```text
D:\_datefac\output\trust_engine_foundation_330a
```

Suggested outputs:

```text
trust_engine_foundation_330a_summary.json
trust_engine_foundation_330a_qa.json
trust_engine_foundation_330a_example_records.json
trust_engine_foundation_330a_risk_registry.json
trust_engine_foundation_330a_no_apply_proof.json
trust_engine_foundation_330a_report.md
```

## Input

Primary previous closure input:

```text
D:\_datefac\output\alias_patch_cycle_closure_325p
```

Official assets may be read only for hash/no-apply proof:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Expected summary metrics

```text
risk_registry_count >= 18
example_trust_record_count = 3
routing_policy_smoke_test_count >= 3
routing_policy_smoke_test_passed = true
validated_325p_closure = true
no_official_asset_modification_during_330a = true
qa_fail_count = 0
decision = TRUST_ENGINE_FOUNDATION_330A_READY_FOR_330B_RISK_REGISTRY_AND_SCORING_INTEGRATION
```

If QA passes with warnings:

```text
TRUST_ENGINE_FOUNDATION_330A_READY_WITH_WARNINGS
```

If blocking QA fails:

```text
TRUST_ENGINE_FOUNDATION_330A_NOT_READY
```

## Suggested command

```bash
python tools/run_trust_engine_foundation_330a.py \
  --cycle-closure-dir D:\_datefac\output\alias_patch_cycle_closure_325p \
  --output-dir D:\_datefac\output\trust_engine_foundation_330a
```

## Compile checks

```bash
python -m py_compile datefac\trust\__init__.py datefac\trust\schema.py datefac\trust\risk_registry.py datefac\trust\routing_policy.py datefac\trust\no_apply_proof.py datefac\trust\trust_engine_foundation_330a_report.py tools\run_trust_engine_foundation_330a.py
```

If tests are added, run only the new lightweight trust tests.

## Git workflow

Use precise adds only. Example:

```bash
git add datefac/trust/__init__.py
git add datefac/trust/schema.py
git add datefac/trust/risk_registry.py
git add datefac/trust/routing_policy.py
git add datefac/trust/no_apply_proof.py
git add datefac/trust/trust_engine_foundation_330a_report.py
git add tools/run_trust_engine_foundation_330a.py
```

If tests are added:

```bash
git add tests/trust/test_trust_engine_foundation_330a.py
```

Commit:

```text
Add 330A trust engine foundation
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Risk registry count.
5. Example trust record count.
6. Routing policy smoke test result.
7. 325P closure validation result.
8. Official asset modification confirmation.
9. QA fail count.
10. Decision.
11. Git status result.
12. Commit hash.
13. Push result.
14. Verification result and residual risks.
