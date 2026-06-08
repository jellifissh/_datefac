# DateFac AI Review Architecture 339A (English)

## 1. What This Architecture Solves

The AI review path is not about “plug in a model and trust the answer.” It is about:

> given a reviewed candidate set, how can a model provide auditable text adjudication suggestions without outranking hard rules and without writing back?

## 2. Current Layering

The current AI review stack is:

1. 337D tightens the reviewed candidate set with deterministic QA
2. 338A runs DeepSeek flash as the baseline dry-run
3. 338B runs `AI_REVIEW_MODEL` on the same sample for A/B comparison
4. 338C tightens schema and grounding requirements
5. 338D decides which model outputs would be safe to accept under dry-run policy

## 3. Why 337D Must Come First

If the reviewed pool is still too loose, AI review just amplifies noise.

337D performs:

- stricter reviewed gating
- year-alignment repair
- suspicious-row QA

That is why the reviewed set tightens from `148` to `112` before the AI layer runs.

## 4. Role Of 338A

338A is not the final solution. It is the baseline.

Current baseline:

- model: `deepseek-v4-flash`
- `low_confidence = 34 / 50`
- `NEEDS_MORE_CONTEXT = 33 / 50`

Its value is to provide a conservative reference point.

## 5. Role Of 338B

338B compares `AI_REVIEW_MODEL` with DeepSeek flash on the same 50 rows.

Current new-model result:

- model: `gpt-5.5`
- `low_confidence = 0 / 50`
- `NEEDS_MORE_CONTEXT = 3 / 50`
- `invalid_response = 3`

This shows that the new model is stronger on the sampled text-adjudication task, but that still does not mean it is ready for default adoption.

## 6. Role Of 338C

338C is not mainly about changing the model. It is about tightening schema and grounding:

- `raw_evidence_quote`
- `supporting_context_quote`
- `grounding_source`

Current result:

- `invalid_response_count_338c = 1`
- `grounding_source BOTH = 49`

The purpose is to make model decisions more auditable instead of merely more confident.

## 7. Role Of 338D

338D separates model output from formal adoption policy.

Its actions are:

- `ACCEPT_MODEL_CONFIRM`
- `ACCEPT_MODEL_DOWNGRADE`
- `ACCEPT_MODEL_REJECT`
- `HOLD_FOR_HUMAN_REVIEW`
- `REJECT_BY_DETERMINISTIC_RULE`
- `INVALID_MODEL_RESPONSE`

Current result:

- `ACCEPT_MODEL_CONFIRM = 39`
- `ACCEPT_MODEL_REJECT = 3`
- `HOLD_FOR_HUMAN_REVIEW = 3`
- `REJECT_BY_DETERMINISTIC_RULE = 4`
- `INVALID_MODEL_RESPONSE = 1`
- `deterministic_rule_override_count = 0`

The key points are:

- deterministic hard rejects are never overridden by the model
- invalid responses are never accepted
- `NEEDS_MORE_CONTEXT` still stays with human review

## 8. Current Model Role Split

- `AI_REVIEW_MODEL`: main candidate text adjudicator
- DeepSeek flash: fallback / baseline
- vision model: future complement for layout, screenshot, or image-table uncertainty

And still:

- not client-ready
- not production-ready
- not a write-back path

## 9. Why Default Adoption Is Still Not Approved

Even though `gpt-5.5` performs better in 338B and 338C, 338D still concludes:

- `suggest_set_ai_review_model_default = false`

That is reasonable because:

- invalid cases still exist
- adoption policy still needs more evidence
- deterministic safety still comes first

## 10. One-Line Conclusion

> The current AI review architecture is not designed to prove that the model is “smart enough.” It is designed to prove that even a strong model must remain constrained by rules, evidence, and human-review boundaries.
