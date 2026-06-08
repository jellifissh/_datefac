# DateFac AI Review 架构说明 339A（中文）

## 1. 这部分架构解决什么问题

AI review 这条链路解决的不是“把模型接上就完事”，而是：

> 如果我们已经有 reviewed 候选行，怎样在不越过硬规则和不写回的前提下，让模型给出可审计的文本裁决建议？

## 2. 当前分层

当前 AI review 分层如下：

1. 337D：先把 reviewed 候选行用 deterministic QA 收紧
2. 338A：用 DeepSeek flash 做 baseline dry-run
3. 338B：让 `AI_REVIEW_MODEL` 对同一批行做 A/B 对比
4. 338C：要求输出更 grounded，分离 raw quote 与 context quote
5. 338D：再决定哪些模型建议在 dry-run policy 下可以接受

## 3. 为什么 337D 必须在前

如果 reviewed 行本身还很松，AI review 会放大噪声。

337D 当前做了三件关键事：

- stricter reviewed gate
- year alignment repair
- suspicious row QA

这一步之后 reviewed 才从 `148` 收紧到 `112`，让 AI 层面对的是更干净的输入。

## 4. 338A 的角色

338A 不是最终方案，它是 baseline。

当前 baseline：

- model: `deepseek-v4-flash`
- `low_confidence = 34 / 50`
- `NEEDS_MORE_CONTEXT = 33 / 50`

它的价值是提供一个保守对照组。

## 5. 338B 的角色

338B 让 `AI_REVIEW_MODEL` 和 DeepSeek flash 对同一批 50 行做对比。

当前新模型结果：

- model: `gpt-5.5`
- `low_confidence = 0 / 50`
- `NEEDS_MORE_CONTEXT = 3 / 50`
- `invalid_response = 3`

这说明新模型在文本裁决上更积极、更强，但还不等于可以直接默认采用。

## 6. 338C 的角色

338C 的重点不是换模型，而是收紧 schema 和 grounding：

- `raw_evidence_quote`
- `supporting_context_quote`
- `grounding_source`

当前结果：

- `invalid_response_count_338c = 1`
- `grounding_source BOTH = 49`

这一步的意义是让模型结论更可审计，而不是只看最终标签。

## 7. 338D 的角色

338D 把模型输出和正式 adoption policy 分开。

动作分为：

- `ACCEPT_MODEL_CONFIRM`
- `ACCEPT_MODEL_DOWNGRADE`
- `ACCEPT_MODEL_REJECT`
- `HOLD_FOR_HUMAN_REVIEW`
- `REJECT_BY_DETERMINISTIC_RULE`
- `INVALID_MODEL_RESPONSE`

当前结果：

- `ACCEPT_MODEL_CONFIRM = 39`
- `ACCEPT_MODEL_REJECT = 3`
- `HOLD_FOR_HUMAN_REVIEW = 3`
- `REJECT_BY_DETERMINISTIC_RULE = 4`
- `INVALID_MODEL_RESPONSE = 1`
- `deterministic_rule_override_count = 0`

最重要的是：

- deterministic hard reject 不会被模型覆盖
- invalid response 不会被接受
- `NEEDS_MORE_CONTEXT` 仍然保留给人工

## 8. 当前模型角色结论

- `AI_REVIEW_MODEL`：主文本裁决候选模型
- DeepSeek flash：fallback / baseline
- vision model：未来版面与截图歧义的补充层

但当前仍然：

- 不是 client-ready
- 不是 production-ready
- 不是正式写回链路

## 9. 为什么现在还不能默认采用

虽然 `gpt-5.5` 在 338B/338C 的表现更强，但 338D 最终仍给出：

- `suggest_set_ai_review_model_default = false`

原因很清楚：

- 还有 invalid cases
- adoption policy 还需要更多证据
- deterministic safety 仍然优先

## 10. 一句话结论

> 当前 AI review 架构的重点不是“证明模型足够聪明”，而是“证明模型就算被引入，也必须被规则、证据和人工边界约束”。
