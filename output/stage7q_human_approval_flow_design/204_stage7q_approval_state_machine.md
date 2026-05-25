# Stage7Q Approval State Machine

## States
- `pending_human_review`
- `approve`
- `reject`
- `needs_more_info`

## Allowed Transition
- queue initialization -> `pending_human_review`
- `pending_human_review` -> `approve` / `reject` / `needs_more_info`
- invalid or empty human input -> remain `pending_human_review`

## Enforcement Rules
1. Only `approve` can enter sandbox apply preview.
2. `reject` goes to rejected_by_human queue.
3. `needs_more_info` goes to needs_more_info queue.
4. `apply_allowed` is system-generated from final status; human template cannot force it.
5. Even when `approve`, this stage cannot write production 06.
6. `real_apply_executed` must remain `false` in Stage7Q.
