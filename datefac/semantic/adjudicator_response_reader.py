from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from datefac.semantic.adjudicator_schema import ALLOWED_ACTIONS
from datefac.vlm.vlm_candidate_mapper import KNOWN_METRICS


ALLOWED_UNIT_SOURCES = {"table_title", "header", "row_label", "unavailable"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _validate_response_payload(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    required_fields = {
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
    }
    payload_keys = set(payload.keys())
    missing = sorted(required_fields - payload_keys)
    extra = sorted(payload_keys - required_fields)
    if missing:
        errors.append(f"missing_fields:{'|'.join(missing)}")
    if extra:
        errors.append(f"unexpected_fields:{'|'.join(extra)}")

    if not isinstance(payload.get("case_id"), str) or not _norm(payload.get("case_id")):
        errors.append("case_id_invalid")
    if payload.get("action") not in ALLOWED_ACTIONS:
        errors.append("action_invalid")

    metric_code = payload.get("metric_code")
    if metric_code is not None and metric_code not in KNOWN_METRICS:
        errors.append("metric_code_unsupported")

    metric_family = payload.get("metric_family")
    if metric_family is not None and not isinstance(metric_family, str):
        errors.append("metric_family_invalid")
    if payload.get("confidence_label") not in ALLOWED_CONFIDENCE:
        errors.append("confidence_label_invalid")
    if not isinstance(payload.get("is_core_metric"), bool):
        errors.append("is_core_metric_invalid")

    unit_inference = payload.get("unit_inference")
    if not isinstance(unit_inference, dict):
        errors.append("unit_inference_invalid")
    else:
        expected_unit_keys = {"unit", "source", "confidence_label"}
        unit_keys = set(unit_inference.keys())
        if unit_keys != expected_unit_keys:
            errors.append("unit_inference_fields_invalid")
        if unit_inference.get("unit") is not None and not isinstance(unit_inference.get("unit"), str):
            errors.append("unit_inference_unit_invalid")
        if unit_inference.get("source") not in ALLOWED_UNIT_SOURCES:
            errors.append("unit_inference_source_invalid")
        if unit_inference.get("confidence_label") not in ALLOWED_CONFIDENCE:
            errors.append("unit_inference_confidence_invalid")

    if not isinstance(payload.get("reason"), str):
        errors.append("reason_invalid")
    if not isinstance(payload.get("evidence"), list) or not all(isinstance(item, str) for item in payload.get("evidence", [])):
        errors.append("evidence_invalid")
    if not isinstance(payload.get("risk_flags"), list) or not all(isinstance(item, str) for item in payload.get("risk_flags", [])):
        errors.append("risk_flags_invalid")
    return errors


def _read_single_response_file(path: Path) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    responses: Dict[str, Dict[str, Any]] = {}
    extras: List[Dict[str, Any]] = []
    if not path.exists():
        return responses, extras
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
                case_id = _norm(parsed.get("case_id"))
                if case_id and case_id not in responses:
                    responses[case_id] = {"payload": parsed, "json_parse_ok": True, "validation_errors": []}
                elif case_id:
                    extras.append({"case_id": case_id, "issue": "duplicate_case_id", "line_number": line_number})
                else:
                    extras.append({"case_id": "", "issue": "missing_case_id", "line_number": line_number})
            except Exception as exc:
                extras.append({"case_id": "", "issue": f"json_parse_error:{exc.__class__.__name__}", "line_number": line_number})
    return responses, extras


def validate_responses(
    request_inventory_df: pd.DataFrame,
    response_dir: Path | None,
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]], pd.DataFrame]:
    columns = [
        "case_id",
        "response_available",
        "json_parse_ok",
        "schema_valid",
        "action",
        "metric_code",
        "confidence_label",
        "validation_errors",
    ]
    all_responses: Dict[str, Dict[str, Any]] = {}
    extra_rows: List[Dict[str, Any]] = []
    if response_dir is not None:
        label_responses, label_extras = _read_single_response_file(response_dir / "llm_label_responses_322d.jsonl")
        candidate_responses, candidate_extras = _read_single_response_file(response_dir / "llm_candidate_responses_322d.jsonl")
        all_responses.update(label_responses)
        all_responses.update(candidate_responses)
        extra_rows.extend(label_extras)
        extra_rows.extend(candidate_extras)

    validation_rows: List[Dict[str, Any]] = []
    valid_payloads: Dict[str, Dict[str, Any]] = {}
    for _, request_row in request_inventory_df.iterrows():
        case_id = _norm(request_row.get("case_id"))
        response_info = all_responses.get(case_id)
        if response_info is None:
            validation_rows.append(
                {
                    "case_id": case_id,
                    "response_available": False,
                    "json_parse_ok": False,
                    "schema_valid": False,
                    "action": "",
                    "metric_code": "",
                    "confidence_label": "",
                    "validation_errors": "NO_RESPONSE_AVAILABLE",
                }
            )
            continue

        payload = response_info.get("payload") or {}
        validation_errors = _validate_response_payload(payload)
        schema_valid = not validation_errors
        if schema_valid:
            valid_payloads[case_id] = payload
        validation_rows.append(
            {
                "case_id": case_id,
                "response_available": True,
                "json_parse_ok": True,
                "schema_valid": schema_valid,
                "action": _norm(payload.get("action")),
                "metric_code": _norm(payload.get("metric_code")),
                "confidence_label": _norm(payload.get("confidence_label")),
                "validation_errors": "|".join(validation_errors),
            }
        )

    extras_df = pd.DataFrame(extra_rows).fillna("")
    return pd.DataFrame(validation_rows, columns=columns).fillna(""), valid_payloads, extras_df
