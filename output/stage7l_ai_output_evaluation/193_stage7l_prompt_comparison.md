# Prompt Comparison: Stage7K vs Stage7K2

## Stage7K (low-rate prompt)
- Result: schema invalid
- Missing fields: review_id, suggested_row_ids, suggested_metric_name, suggested_year, suggested_value, suggested_unit, confidence, reasoning_summary, risk_flags
- Typical response shape: only suggested_action + requires_human_approval

## Stage7K2 (strict schema prompt)
- Result: schema valid
- Missing fields: none
- Full schema present: yes
- Deterministic validation pass: True

## Conclusion
- strict_schema_prompt_effective: True
- Recommendation: keep strict field checklist + explicit fallback JSON template.
