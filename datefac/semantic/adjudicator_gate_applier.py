from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import pandas as pd

from datefac.vlm.vlm_candidate_mapper import KNOWN_METRICS


OUT_OF_SCOPE_TABLE_KEYWORDS = [
    "可比公司",
    "估值",
    "基础数据",
    "股价",
    "行业均值",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_label(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").lower()


def _split_tags(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _parse_provenance_json(value: Any) -> Dict[str, Any]:
    text = _norm(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _build_label_group_lookup(review_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    if review_df.empty:
        return {}

    temp = review_df.copy()
    temp["normalized_label"] = temp["raw_metric_name"].map(_normalize_label)
    lookup: Dict[str, Dict[str, Any]] = {}
    for normalized_label, group in temp.groupby("normalized_label", dropna=False):
        candidate_count = len(group)
        valid_year_all = True
        numeric_parsed_all = True
        provenance_complete_all = True
        no_conflict_all = True
        no_extraction_risk_all = True
        unit_known_all = True
        titles: List[str] = []
        current_reasons: List[str] = []
        for _, row in group.iterrows():
            titles.append(_norm(row.get("table_title")))
            current_reasons.append(_norm(row.get("split_reason")))
            risk_tags = set(_split_tags(row.get("risk_tags_after") or row.get("risk_tags")))
            year_source = _norm(row.get("year_source"))
            normalized_value = row.get("normalized_value")
            provenance = _parse_provenance_json(row.get("provenance_json"))
            if year_source == "INVALID" or not _norm(row.get("year")):
                valid_year_all = False
            if normalized_value in ("", None) or (isinstance(normalized_value, float) and pd.isna(normalized_value)) or "VALUE_PARSE_FAILED" in risk_tags:
                numeric_parsed_all = False
            if not provenance:
                provenance_complete_all = False
            if "VALUE_CONFLICT" in risk_tags:
                no_conflict_all = False
            if any(tag in risk_tags for tag in ["INVALID_YEAR", "NO_YEAR_COLUMNS", "VALUE_PARSE_FAILED", "EXTRACTION_RISK"]):
                no_extraction_risk_all = False
            if not (_norm(row.get("unit")) or _norm(row.get("table_unit"))):
                unit_known_all = False
        clear_out_of_scope_context = any(keyword in title for title in titles for keyword in OUT_OF_SCOPE_TABLE_KEYWORDS)
        lookup[normalized_label] = {
            "candidate_count": int(candidate_count),
            "valid_year_all": valid_year_all,
            "numeric_parsed_all": numeric_parsed_all,
            "provenance_complete_all": provenance_complete_all,
            "no_conflict_all": no_conflict_all,
            "no_extraction_risk_all": no_extraction_risk_all,
            "unit_known_all": unit_known_all,
            "clear_out_of_scope_context": clear_out_of_scope_context,
            "table_title_examples": "|".join(dict.fromkeys([title for title in titles if title]).keys())[:1000],
            "split_reason_examples": "|".join(dict.fromkeys([reason for reason in current_reasons if reason]).keys())[:500],
        }
    return lookup


def _build_candidate_lookup(selected_candidate_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    if selected_candidate_df.empty:
        return lookup
    for _, row in selected_candidate_df.iterrows():
        case_id = _norm(row.get("case_id"))
        lookup[case_id] = {
            "candidate_count": 1,
            "valid_year_all": _norm(row.get("current_review_reason")) != "INVALID_OR_MISSING_YEAR",
            "numeric_parsed_all": _norm(row.get("current_review_reason")) != "VALUE_PARSE_FAILED_OR_SCHEMA_UNCERTAIN",
            "provenance_complete_all": _norm(row.get("available_provenance")) in {"yes", "provenance_warning"},
            "no_conflict_all": "VALUE_CONFLICT" not in _split_tags(row.get("current_risk_tags")),
            "no_extraction_risk_all": "VALUE_PARSE_FAILED" not in _split_tags(row.get("current_risk_tags")),
            "unit_known_all": bool(_norm(row.get("unit_context"))),
            "clear_out_of_scope_context": any(keyword in _norm(row.get("table_title")) for keyword in OUT_OF_SCOPE_TABLE_KEYWORDS),
            "table_title_examples": _norm(row.get("table_title")),
            "split_reason_examples": _norm(row.get("current_review_reason")),
        }
    return lookup


def apply_deterministic_gates(
    selected_label_df: pd.DataFrame,
    selected_candidate_df: pd.DataFrame,
    response_validation_df: pd.DataFrame,
    valid_payloads: Dict[str, Dict[str, Any]],
    review_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    gate_columns = [
        "case_id",
        "action",
        "metric_code",
        "confidence_label",
        "gate_result",
        "affected_candidate_count",
        "estimated_trusted_candidate_gain",
        "estimated_review_reduction",
        "reason",
    ]
    alias_columns = [
        "normalized_label",
        "proposed_metric_code",
        "proposed_metric_family",
        "confidence_label",
        "affected_candidate_count",
        "replay_allowed",
        "replay_block_reason",
        "requires_human_confirmation",
    ]
    out_scope_columns = [
        "normalized_label",
        "affected_candidate_count",
        "replay_allowed",
        "reason",
    ]
    unit_columns = [
        "case_id",
        "proposed_unit",
        "unit_source",
        "confidence_label",
        "affected_candidate_count",
        "replay_allowed",
        "reason",
    ]
    manual_columns = [
        "case_id",
        "normalized_label_or_row",
        "reason",
        "priority",
    ]

    label_lookup = _build_label_group_lookup(review_df)
    candidate_lookup = _build_candidate_lookup(selected_candidate_df)
    validation_lookup = {
        _norm(row.get("case_id")): row.to_dict()
        for _, row in response_validation_df.iterrows()
    }
    label_meta_lookup = {
        _norm(row.get("label_case_id")): row.to_dict()
        for _, row in selected_label_df.iterrows()
    }
    candidate_meta_lookup = {
        _norm(row.get("case_id")): row.to_dict()
        for _, row in selected_candidate_df.iterrows()
    }

    gate_rows: List[Dict[str, Any]] = []
    alias_rows: List[Dict[str, Any]] = []
    out_scope_rows: List[Dict[str, Any]] = []
    unit_rows: List[Dict[str, Any]] = []
    manual_rows: List[Dict[str, Any]] = []

    ordered_case_ids = list(label_meta_lookup.keys()) + list(candidate_meta_lookup.keys())
    for case_id in ordered_case_ids:
        validation = validation_lookup.get(case_id, {})
        meta_row = label_meta_lookup.get(case_id) or candidate_meta_lookup.get(case_id) or {}
        is_label_case = case_id in label_meta_lookup
        normalized_label = _norm(meta_row.get("normalized_label")) if is_label_case else _norm(meta_row.get("row_label"))
        priority = _norm(meta_row.get("priority"))
        lookup_key = normalized_label if is_label_case else case_id
        diagnostics = label_lookup.get(lookup_key) if is_label_case else candidate_lookup.get(lookup_key, {})
        affected_candidate_count = int(
            diagnostics.get("candidate_count")
            or meta_row.get("candidate_count")
            or 0
        )

        if not validation or not bool(validation.get("response_available")):
            gate_rows.append(
                {
                    "case_id": case_id,
                    "action": "",
                    "metric_code": "",
                    "confidence_label": "",
                    "gate_result": "KEEP_REVIEW_REQUIRED",
                    "affected_candidate_count": affected_candidate_count,
                    "estimated_trusted_candidate_gain": 0,
                    "estimated_review_reduction": 0,
                    "reason": "NO_RESPONSE_AVAILABLE",
                }
            )
            manual_rows.append(
                {
                    "case_id": case_id,
                    "normalized_label_or_row": normalized_label,
                    "reason": "NO_RESPONSE_AVAILABLE",
                    "priority": priority,
                }
            )
            continue

        if not bool(validation.get("schema_valid")):
            gate_rows.append(
                {
                    "case_id": case_id,
                    "action": _norm(validation.get("action")),
                    "metric_code": _norm(validation.get("metric_code")),
                    "confidence_label": _norm(validation.get("confidence_label")),
                    "gate_result": "LLM_RESPONSE_SCHEMA_INVALID",
                    "affected_candidate_count": affected_candidate_count,
                    "estimated_trusted_candidate_gain": 0,
                    "estimated_review_reduction": 0,
                    "reason": _norm(validation.get("validation_errors")) or "LLM_RESPONSE_SCHEMA_INVALID",
                }
            )
            manual_rows.append(
                {
                    "case_id": case_id,
                    "normalized_label_or_row": normalized_label,
                    "reason": "LLM_RESPONSE_SCHEMA_INVALID",
                    "priority": priority,
                }
            )
            continue

        payload = valid_payloads.get(case_id, {})
        action = _norm(payload.get("action"))
        metric_code = _norm(payload.get("metric_code"))
        confidence_label = _norm(payload.get("confidence_label"))
        unit_inference = payload.get("unit_inference") if isinstance(payload.get("unit_inference"), dict) else {}
        unit_value = _norm(unit_inference.get("unit"))
        unit_source = _norm(unit_inference.get("source"))
        unit_confidence = _norm(unit_inference.get("confidence_label"))

        valid_year_all = bool(diagnostics.get("valid_year_all"))
        numeric_parsed_all = bool(diagnostics.get("numeric_parsed_all"))
        provenance_complete_all = bool(diagnostics.get("provenance_complete_all"))
        no_conflict_all = bool(diagnostics.get("no_conflict_all"))
        no_extraction_risk_all = bool(diagnostics.get("no_extraction_risk_all"))
        unit_known_all = bool(diagnostics.get("unit_known_all"))
        clear_out_of_scope_context = bool(diagnostics.get("clear_out_of_scope_context"))

        if confidence_label == "low":
            gate_result = "LLM_RESPONSE_LOW_CONFIDENCE"
            reason = "confidence_label=low"
            trusted_gain = 0
            review_reduction = 0
        elif action == "map_to_existing_metric_code" and metric_code and metric_code not in KNOWN_METRICS:
            gate_result = "LLM_RESPONSE_UNSUPPORTED_METRIC_CODE"
            reason = f"metric_code_not_allowed:{metric_code}"
            trusted_gain = 0
            review_reduction = 0
        elif action == "reject_noise" and confidence_label in {"high", "medium"}:
            gate_result = "REJECT_NOISE_FOR_REPLAY"
            reason = "high_or_medium_confidence_noise_classification"
            trusted_gain = 0
            review_reduction = affected_candidate_count
        elif action == "classify_out_of_scope" and confidence_label in {"high", "medium"} and clear_out_of_scope_context:
            gate_result = "CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY"
            reason = "clear_out_of_scope_context_and_semantic_support"
            trusted_gain = 0
            review_reduction = affected_candidate_count
            out_scope_rows.append(
                {
                    "normalized_label": normalized_label,
                    "affected_candidate_count": affected_candidate_count,
                    "replay_allowed": True,
                    "reason": reason,
                }
            )
        elif action == "map_to_existing_metric_code" and confidence_label == "high" and metric_code in KNOWN_METRICS:
            unit_inference_accepted = bool(unit_value) and unit_source in {"table_title", "header", "row_label"} and unit_confidence == "high"
            deterministic_ok = all(
                [
                    valid_year_all,
                    numeric_parsed_all,
                    provenance_complete_all,
                    no_conflict_all,
                    no_extraction_risk_all,
                    unit_known_all or unit_inference_accepted,
                ]
            )
            if not deterministic_ok and unit_inference_accepted and all(
                [
                    valid_year_all,
                    numeric_parsed_all,
                    provenance_complete_all,
                    no_conflict_all,
                    no_extraction_risk_all,
                ]
            ):
                gate_result = "ACCEPT_UNIT_INFERENCE_FOR_REPLAY"
                reason = "unit_missing_but_high_confidence_unit_inference_available"
                trusted_gain = 0
                review_reduction = affected_candidate_count
                unit_rows.append(
                    {
                        "case_id": case_id,
                        "proposed_unit": unit_value,
                        "unit_source": unit_source,
                        "confidence_label": unit_confidence,
                        "affected_candidate_count": affected_candidate_count,
                        "replay_allowed": True,
                        "reason": reason,
                    }
                )
            elif deterministic_ok:
                gate_result = "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY"
                reason = "semantic_alias_and_deterministic_gate_passed"
                trusted_gain = affected_candidate_count
                review_reduction = affected_candidate_count
                alias_rows.append(
                    {
                        "normalized_label": normalized_label,
                        "proposed_metric_code": metric_code,
                        "proposed_metric_family": _norm(payload.get("metric_family")),
                        "confidence_label": confidence_label,
                        "affected_candidate_count": affected_candidate_count,
                        "replay_allowed": True,
                        "replay_block_reason": "",
                        "requires_human_confirmation": True,
                    }
                )
            else:
                gate_result = "KEEP_REVIEW_REQUIRED"
                blockers: List[str] = []
                if not valid_year_all:
                    blockers.append("invalid_year_present")
                if not numeric_parsed_all:
                    blockers.append("numeric_parse_not_clean")
                if not provenance_complete_all:
                    blockers.append("missing_provenance")
                if not no_conflict_all:
                    blockers.append("value_conflict_present")
                if not no_extraction_risk_all:
                    blockers.append("extraction_risk_present")
                if not unit_known_all and not unit_inference_accepted:
                    blockers.append("unit_unknown_without_high_confidence_inference")
                reason = "|".join(blockers or ["deterministic_gate_blocked"])
                trusted_gain = 0
                review_reduction = 0
        elif action in {"requires_table_context", "requires_manual_review"}:
            gate_result = "REQUIRES_MANUAL_REVIEW"
            reason = action
            trusted_gain = 0
            review_reduction = 0
        else:
            gate_result = "KEEP_REVIEW_REQUIRED"
            reason = "deterministic_gate_kept_review"
            trusted_gain = 0
            review_reduction = 0

        gate_rows.append(
            {
                "case_id": case_id,
                "action": action,
                "metric_code": metric_code,
                "confidence_label": confidence_label,
                "gate_result": gate_result,
                "affected_candidate_count": affected_candidate_count,
                "estimated_trusted_candidate_gain": trusted_gain,
                "estimated_review_reduction": review_reduction,
                "reason": reason,
            }
        )

        if gate_result not in {
            "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY",
            "CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY",
            "ACCEPT_UNIT_INFERENCE_FOR_REPLAY",
            "REJECT_NOISE_FOR_REPLAY",
        }:
            manual_rows.append(
                {
                    "case_id": case_id,
                    "normalized_label_or_row": normalized_label,
                    "reason": gate_result,
                    "priority": priority,
                }
            )

    return (
        pd.DataFrame(gate_rows, columns=gate_columns).fillna(""),
        pd.DataFrame(alias_rows, columns=alias_columns).fillna(""),
        pd.DataFrame(out_scope_rows, columns=out_scope_columns).fillna(""),
        pd.DataFrame(unit_rows, columns=unit_columns).fillna(""),
        pd.DataFrame(manual_rows, columns=manual_columns).fillna(""),
    )
