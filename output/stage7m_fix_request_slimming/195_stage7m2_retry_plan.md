# Stage7M2 Retry Plan (Slim Requests, No Real Apply)

1. Use `195_stage7m_slim_selected_requests.jsonl` as the only request input.
2. Keep strict schema output requirement unchanged from Stage7K2.
3. Runtime settings:
- timeout_seconds=120
- max_tokens=700
- temperature=0
- inter_request_interval_seconds=15
- non-concurrent, one request at a time
- no automatic retries; stop expansion on first timeout/429
4. Validation gates:
- schema required fields all present
- suggested_row_ids subset of candidate row ids
- suggested_value must come from candidate row values
- EPS must not be ratio
- requires_human_approval must be true
5. Safety gates:
- sandbox only, no real apply
- do not write production 06
- do not change formal rules/official overrides/standardizer/release package
