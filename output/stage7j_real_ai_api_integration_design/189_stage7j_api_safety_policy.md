# Stage7J API Safety Policy

## Mandatory controls
1. No real API call in Stage7J.
2. No API keys committed to repository.
3. Default `external_api_enabled=false`.
4. Without `--enable-external-api`, client must refuse request.
5. All AI output must pass Stage7H/7I validation rules.
6. `requires_human_approval=true` for all suggestions.
7. AI suggestions are sandbox-only and cannot write production 06.
8. No modification to formal rules / official 02B / delivery package.

## Logging and redaction
- Log request/response IDs and validation status.
- Redact potential secrets in any diagnostic logs.
- Keep source trace: pdf/page/table/row.

## Fail-safe defaults
- Validation failure => reject suggestion.
- Low confidence => keep manual review.
- Schema parse failure => keep manual review.
- Any policy ambiguity => keep manual review.
