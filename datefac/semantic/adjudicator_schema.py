from __future__ import annotations

from typing import Any, Dict, List

from datefac.vlm.vlm_candidate_mapper import KNOWN_METRICS


ALLOWED_ACTIONS = [
    "map_to_existing_metric_code",
    "classify_out_of_scope",
    "requires_table_context",
    "requires_manual_review",
    "reject_noise",
]


def build_allowed_metric_codes_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for metric_code, meta in sorted(KNOWN_METRICS.items()):
        rows.append(
            {
                "metric_code": metric_code,
                "metric_family": meta.get("metric_family", ""),
                "description_if_available": meta.get("canonical_name", ""),
                "example_aliases_if_available": "",
            }
        )
    return rows


def build_llm_output_schema() -> Dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "DateFacSemanticAdjudicatorOutput",
        "type": "object",
        "required": [
            "case_id",
            "action",
            "metric_code",
            "metric_family",
            "confidence_label",
            "is_core_metric",
            "unit_inference",
            "reason",
            "evidence",
            "risk_flags",
        ],
        "properties": {
            "case_id": {"type": "string"},
            "action": {
                "type": "string",
                "enum": ALLOWED_ACTIONS,
            },
            "metric_code": {
                "type": ["string", "null"],
                "enum": sorted(list(KNOWN_METRICS.keys())) + [None],
            },
            "metric_family": {"type": ["string", "null"]},
            "confidence_label": {
                "type": "string",
                "enum": ["high", "medium", "low"],
            },
            "is_core_metric": {"type": "boolean"},
            "unit_inference": {
                "type": "object",
                "required": ["unit", "source", "confidence_label"],
                "properties": {
                    "unit": {"type": ["string", "null"]},
                    "source": {
                        "type": "string",
                        "enum": ["table_title", "header", "row_label", "unavailable"],
                    },
                    "confidence_label": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                },
                "additionalProperties": False,
            },
            "reason": {"type": "string"},
            "evidence": {
                "type": "array",
                "items": {"type": "string"},
            },
            "risk_flags": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "additionalProperties": False,
    }


def validate_output_schema_dict(schema: Dict[str, Any]) -> bool:
    required = {"type", "properties", "required"}
    return isinstance(schema, dict) and required.issubset(schema.keys())

