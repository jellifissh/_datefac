# DateFac 330B Task
## Risk Registry and Deterministic Scoring Integration

## Context

330A Trust Engine foundation is complete and pushed.

330A commit:

```text
7b6120ed171ef9f8bca6b02b1b852492462b9b9f
```

330A output:

```text
D:\_datefac\output\trust_engine_foundation_330a
```

330A result:

```text
risk_registry_count = 18
example_trust_record_count = 3
routing_policy_smoke_test_count = 3
routing_policy_smoke_test_passed = true
validated_325p_closure = true
no_official_asset_modification_during_330a = true
qa_fail_count = 0
decision = TRUST_ENGINE_FOUNDATION_330A_READY_FOR_330B_RISK_REGISTRY_AND_SCORING_INTEGRATION
```

330A introduced:

```text
datefac/trust/__init__.py
datefac/trust/schema.py
datefac/trust/risk_registry.py
datefac/trust/routing_policy.py
datefac/trust/no_apply_proof.py
datefac/trust/trust_engine_foundation_330a_report.py
tools/run_trust_engine_foundation_330a.py
tests/trust/test_trust_engine_foundation_330a.py
```

330B is the next step. It should deepen the Trust Engine foundation by introducing deterministic confidence scoring and a lightweight cached-artifact scoring smoke test. It must still be non-invasive and must not take over production routing.

## Goal

Implement 330B: Risk Registry and Deterministic Scoring Integration.

330B must add a deterministic confidence scoring layer on top of the 330A schema/risk/routing foundation.

The goal is to make candidate trust records scoreable in a consistent, explainable way:

```text
input candidate dict + risk flags + evidence signals
  -> confidence score components
  -> risk penalty
  -> final confidence_score
  -> confidence_level
  -> routing_decision via routing_policy
```

330B is still a sidecar trust evaluation layer. It must not change production trusted/review/rejected behavior.

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
- Do not let 330B override existing trusted/review routing.
- Use cached 323/324/325 artifacts only for examples and smoke fixtures.
- Do not commit output, temp, input/semantic_adjudicator_responses_*, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add/update 330B trust-layer source/report/runner/test files.

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

## Suggested files

New files:

```text
datefac/trust/confidence_scoring.py
datefac/trust/trust_engine_scoring_330b_report.py
tools/run_trust_engine_scoring_330b.py
tests/trust/test_trust_engine_scoring_330b.py
```

Possible precise updates if needed:

```text
datefac/trust/__init__.py
datefac/trust/schema.py
datefac/trust/routing_policy.py
```

Do not edit production pipeline modules in 330B.

## Scoring requirements

Add a deterministic scoring model with explicit score components:

```text
evidence_score
semantic_score
unit_year_score
parser_agreement_score
risk_penalty
confidence_score
confidence_level
```

Suggested score model v1:

```text
base score = 0

evidence_score:
  source evidence present: +20
  source page/table/row reference present: +10
  evidence_refs count >= 2: +5
  max evidence_score = 35

semantic_score:
  normalized_metric present: +15
  official alias/rule match signal: +10
  semantic target unambiguous: +10
  max semantic_score = 35

unit_year_score:
  unit present and not unknown: +10
  year present and not unknown: +10
  value parse success: +10
  max unit_year_score = 30

parser_agreement_score:
  one parser source: +5
  two or more parser sources: +10
  explicit parser agreement signal: +10
  max parser_agreement_score = 20

risk_penalty:
  each INFO risk: -2
  each WARNING risk: -8
  each BLOCKING risk: -30
  specific higher penalties:
    ADJUSTED_METRIC_RISK: -35
    DILUTED_EPS_RISK: -35
    OFFICIAL_RULE_CONFLICT: -45
    VALUE_PARSE_FAILED: -40
    TARGET_METRIC_AMBIGUOUS: -30
    UNIT_CONFLICT: -30
    YEAR_MISMATCH: -30
```

Final score:

```text
confidence_score = clamp(evidence_score + semantic_score + unit_year_score + parser_agreement_score + risk_penalty, 0, 100)
```

Confidence level:

```text
score >= 85 -> HIGH
score >= 60 -> MEDIUM
score > 0 -> LOW
score == 0 -> UNKNOWN
```

Routing should reuse 330A routing policy:

```text
score >= 85 and no blocking risk -> TRUSTED
score >= 60 -> REVIEW_REQUIRED
score < 60 -> NEEDS_MORE_INFO or REJECTED depending on caller policy
any blocking risk -> REVIEW_REQUIRED or REJECTED depending on caller policy
```

## Required behavior

1. Implement a scoring helper that accepts a trust record or plain dict and returns a JSON-serializable scored trust record.
2. Reuse 330A risk registry normalization and blocking/warning derivation.
3. Reuse 330A routing policy instead of duplicating routing logic.
4. Preserve original candidate fields and provenance.
5. Add scoring explanations / decision reasons such as:

```text
source_evidence_present
normalized_metric_present
unit_year_resolved
parser_agreement_present
warning_risk_penalty_applied
blocking_risk_penalty_applied
```

6. Add smoke examples for at least 5 trust records:

```text
HIGH TRUSTED candidate
MEDIUM REVIEW_REQUIRED candidate
LOW NEEDS_MORE_INFO candidate
BLOCKING REJECTED candidate
MOJIBAKE WARNING REVIEW_REQUIRED candidate
```

7. Validate 330A readiness from cached 330A output.
8. Validate 325P closure remains the previous project milestone if needed.
9. Generate 330B output artifacts and no-apply proof.
10. Confirm official assets are not modified.

## Cached artifact sidecar smoke test

Use cached artifacts only. Do not recompute production outputs.

330B runner should optionally sample lightweight candidate-like examples from existing cached outputs if present. Good sources include:

```text
D:\_datefac\output\alias_patch_cycle_closure_325p
D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i
D:\_datefac\output\controlled_official_proposal_dry_run_325l
D:\_datefac\output\post_patch_regression_validation_325o
```

If reliable candidate rows are not easily available, use deterministic built-in smoke examples and report:

```text
cached_candidate_sidecar_sample_count = 0
cached_candidate_sidecar_reason = no compatible candidate-level cache found
```

Do not treat lack of candidate-level cache as QA failure.

## Output directory

```text
D:\_datefac\output\trust_engine_scoring_330b
```

Suggested outputs:

```text
trust_engine_scoring_330b_summary.json
trust_engine_scoring_330b_qa.json
trust_engine_scoring_330b_scored_examples.json
trust_engine_scoring_330b_scoring_model.json
trust_engine_scoring_330b_no_apply_proof.json
trust_engine_scoring_330b_report.md
```

## Inputs

Primary previous foundation input:

```text
D:\_datefac\output\trust_engine_foundation_330a
```

Reference closure input:

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
validated_330a_foundation = true
risk_registry_count >= 18
scoring_model_component_count >= 5
scored_example_count >= 5
routing_policy_reused = true
routing_policy_smoke_test_count >= 5
routing_policy_smoke_test_passed = true
cached_candidate_sidecar_sample_count >= 0
no_official_asset_modification_during_330b = true
qa_fail_count = 0
decision = TRUST_ENGINE_SCORING_330B_READY_FOR_330C_CACHED_CANDIDATE_TRUST_SCORING_BENCHMARK
```

If QA passes with warnings:

```text
TRUST_ENGINE_SCORING_330B_READY_WITH_WARNINGS
```

If blocking QA fails:

```text
TRUST_ENGINE_SCORING_330B_NOT_READY
```

## Suggested command

```bash
python tools/run_trust_engine_scoring_330b.py \
  --trust-foundation-dir D:\_datefac\output\trust_engine_foundation_330a \
  --cycle-closure-dir D:\_datefac\output\alias_patch_cycle_closure_325p \
  --output-dir D:\_datefac\output\trust_engine_scoring_330b
```

## Compile checks

```bash
python -m py_compile datefac\trust\__init__.py datefac\trust\schema.py datefac\trust\risk_registry.py datefac\trust\routing_policy.py datefac\trust\no_apply_proof.py datefac\trust\confidence_scoring.py datefac\trust\trust_engine_scoring_330b_report.py tools\run_trust_engine_scoring_330b.py tests\trust\test_trust_engine_scoring_330b.py
```

Run only the new lightweight trust tests if tests are added.

## Git workflow

Use precise adds only. Example:

```bash
git add datefac/trust/confidence_scoring.py
git add datefac/trust/trust_engine_scoring_330b_report.py
git add tools/run_trust_engine_scoring_330b.py
git add tests/trust/test_trust_engine_scoring_330b.py
```

If existing trust package files are deliberately updated:

```bash
git add datefac/trust/__init__.py
git add datefac/trust/schema.py
git add datefac/trust/routing_policy.py
```

Commit:

```text
Add 330B trust engine scoring
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. 330A foundation validation result.
5. Risk registry count.
6. Scoring model component count.
7. Scored example count.
8. Routing policy reuse / smoke test result.
9. Cached sidecar sample count and reason if zero.
10. Official asset modification confirmation.
11. QA fail count.
12. Decision.
13. Git status result.
14. Commit hash.
15. Push result.
16. Verification result and residual risks.
