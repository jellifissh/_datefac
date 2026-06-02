from __future__ import annotations

from typing import Any, Dict, List


def build_acceptance_gate_rules() -> List[Dict[str, Any]]:
    return [
        {
            "rule_id": "GATE_001",
            "rule_type": "trust_blocker",
            "condition": "LLM action alone can never create trusted output without deterministic validation.",
            "allowed_result": "review_required_with_llm_explanation",
            "reason": "forbid LLM-only trusted decisions",
        },
        {
            "rule_id": "GATE_002",
            "rule_type": "trust_promotion",
            "condition": "action=map_to_existing_metric_code AND confidence_label=high AND metric_code in allowed list AND year valid AND numeric parsed AND provenance complete",
            "allowed_result": "eligible_for_trusted_after_deterministic_gate",
            "reason": "only strong semantic matches can enter deterministic trust gate",
        },
        {
            "rule_id": "GATE_003",
            "rule_type": "unit_gate",
            "condition": "unit may be accepted only if unit_inference.source is table_title/header/row_label and confidence_label=high",
            "allowed_result": "review_or_trust_candidate_after_deterministic_check",
            "reason": "prevent weak unit invention",
        },
        {
            "rule_id": "GATE_004",
            "rule_type": "schema_blocker",
            "condition": "invalid year, parse failure, or missing provenance cannot be overridden by semantic adjudication",
            "allowed_result": "review_required_or_manual_review",
            "reason": "semantic adjudicator cannot fix extraction errors",
        },
        {
            "rule_id": "GATE_005",
            "rule_type": "scope_classification",
            "condition": "action=classify_out_of_scope with medium/high confidence and clear table context",
            "allowed_result": "out_of_scope_review_bucket",
            "reason": "allow scoped-down manual burden without trusting content",
        },
        {
            "rule_id": "GATE_006",
            "rule_type": "manual_escalation",
            "condition": "action=requires_table_context OR action=requires_manual_review OR confidence_label=low",
            "allowed_result": "manual_review_required",
            "reason": "retain conservative review posture",
        },
    ]


def design_decision(summary: Dict[str, Any]) -> str:
    if int(summary.get("qa_fail_count", 0)) > 0:
        return "SEMANTIC_ADJUDICATOR_DESIGN_BLOCKED_BY_QA_FAILURE"
    if bool(summary.get("output_schema_defined")) and int(summary.get("label_level_case_count", 0)) > 0 and int(summary.get("acceptance_gate_rule_count", 0)) >= 5:
        return "SEMANTIC_ADJUDICATOR_DESIGN_READY_FOR_322D_LIMITED_EXECUTION"
    if int(summary.get("semantic_case_count", 0)) > 0:
        return "SEMANTIC_ADJUDICATOR_DESIGN_PARTIAL_NEEDS_SCHEMA_REVIEW"
    return "SEMANTIC_ADJUDICATOR_DESIGN_NOT_READY"

