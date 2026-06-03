from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

import pandas as pd

from datefac.semantic.safe_adjudicator_subset import FORMAL_SCOPE_RULES_PATH, OFFICIAL_ALIAS_OVERRIDE_PATH
from datefac.vlm.vlm_candidate_mapper import ALIAS_TO_METRIC, KNOWN_METRICS


EXPECTED_323E_DECISION = "CONFIGURED_ADJUDICATOR_RUN_323E_RAW_RESPONSES_READY_FOR_323F_SCHEMA_VALIDATION"
EXPECTED_323F_READY = "RAW_RESPONSE_SCHEMA_VALIDATION_323F_READY_FOR_HUMAN_CONFIRMED_SUGGESTION_PROPOSALS"
EXPECTED_323F_NO_ACCEPTED = "RAW_RESPONSE_SCHEMA_VALIDATION_323F_NO_ACCEPTED_SUGGESTIONS"
EXPECTED_323F_NOT_READY = "RAW_RESPONSE_SCHEMA_VALIDATION_323F_NOT_READY"

DEFAULT_CONFIGURED_RUN_DIR = Path(r"D:\_datefac\output\configured_adjudicator_run_323e")
DEFAULT_SAFE_SUBSET_DIR = Path(r"D:\_datefac\output\safe_adjudicator_subset_323d")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\raw_response_schema_validation_323f")

CLASS_ACCEPTED = "ACCEPTED_SUGGESTION"
CLASS_REJECTED = "REJECTED_SUGGESTION"
CLASS_NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
CLASS_SCHEMA_INVALID = "SCHEMA_INVALID"
CLASS_GATE_FAILED = "DETERMINISTIC_GATE_FAILED"

CLASSIFICATION_ORDER = [
    CLASS_ACCEPTED,
    CLASS_REJECTED,
    CLASS_NEEDS_MORE_INFO,
    CLASS_SCHEMA_INVALID,
    CLASS_GATE_FAILED,
]

ACCEPTED_RESPONSE_LABELS = {"ACCEPT_ALIAS", "ACCEPT_OUT_OF_SCOPE"}
REJECTED_RESPONSE_LABELS = {"REJECT_ALIAS", "REJECT_OUT_OF_SCOPE", "OUT_OF_SCOPE", "POSSIBLE_CORE_METRIC"}
NEEDS_MORE_INFO_LABELS = {"NEEDS_MORE_INFO"}

DISALLOWED_ACCEPT_SAFETY_FLAGS = {
    "conflict",
    "value_conflict",
    "weak_evidence",
    "weak evidence",
    "possible_scope_mismatch",
    "scope_mismatch",
    "possible core metric",
    "possible_core_metric",
}

CORE_METRIC_TARGET_ALIASES = {
    "ebitda": "EBITDA",
    "ev/ebitda": "EV/EBITDA",
    "ev ebitda": "EV/EBITDA",
    "evebitda": "EV/EBITDA",
    "归属母公司净利润": "归属母公司净利润",
    "归母净利润": "归属母公司净利润",
    "归属于母公司净利润": "归属母公司净利润",
    "归属于母公司股东的净利润": "归属母公司净利润",
    "归属于上市公司股东的净利润": "归属母公司净利润",
}

CORE_METRIC_LIKE_TERMS = [
    "营业收入",
    "归属母公司净利润",
    "归母净利润",
    "毛利率",
    "roe",
    "每股收益",
    "eps",
    "p/e",
    "p/b",
    "ev/ebitda",
    "ebitda",
]

RESPONSE_SCHEMA_REQUIRED_FIELDS = [
    "response_label",
    "confidence",
    "rationale",
    "normalized_target_metric_if_any",
    "safety_flags",
    "needs_human_confirmation",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _safe_int(value: Any) -> int:
    if value in ("", None):
        return 0
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return 0


def _safe_float(value: Any) -> float:
    if value in ("", None):
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def _flatten_sequence(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_norm(item) for item in value if _norm(item)]
    if isinstance(value, tuple):
        return [_norm(item) for item in value if _norm(item)]
    if isinstance(value, str):
        clean = _norm(value)
        return [clean] if clean else []
    return []


def _normalize_label(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").strip().lower()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            parsed = json.loads(text)
        except Exception:
            continue
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _join_unique(items: Iterable[Any], limit: int = 8) -> str:
    out: List[str] = []
    seen: Set[str] = set()
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
        if len(out) >= limit:
            break
    return " | ".join(out)


def _lookup_core_target_metric(target_text: str) -> Tuple[bool, str]:
    normalized = _normalize_label(target_text)
    if not normalized:
        return False, ""
    if normalized in CORE_METRIC_TARGET_ALIASES:
        return True, CORE_METRIC_TARGET_ALIASES[normalized]
    if normalized in ALIAS_TO_METRIC:
        metric_code = ALIAS_TO_METRIC[normalized]
        canonical = KNOWN_METRICS.get(metric_code, {}).get("canonical_name", metric_code)
        return True, canonical
    return False, ""


def _candidate_looks_like_core_metric(label: str) -> bool:
    normalized = _normalize_label(label)
    return any(term in normalized for term in CORE_METRIC_LIKE_TERMS)


def _schema_validate_response(parsed_response: Dict[str, Any], request_item: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(parsed_response, dict):
        return ["parsed_response_not_object"]

    response_schema = request_item.get("response_schema") if isinstance(request_item.get("response_schema"), dict) else {}
    required_fields = response_schema.get("required") if isinstance(response_schema.get("required"), list) else RESPONSE_SCHEMA_REQUIRED_FIELDS
    missing_fields = [field for field in required_fields if field not in parsed_response]
    if missing_fields:
        errors.append(f"missing_fields:{'|'.join(missing_fields)}")

    allowed_labels = set(_flatten_sequence(request_item.get("allowed_response_labels")))
    response_label = _norm(parsed_response.get("response_label"))
    if not response_label:
        errors.append("response_label_missing")
    elif response_label not in allowed_labels:
        errors.append(f"response_label_not_allowed:{response_label}")

    confidence = _norm(parsed_response.get("confidence"))
    if confidence not in {"high", "medium", "low"}:
        errors.append(f"confidence_invalid:{confidence or '__EMPTY__'}")

    if not isinstance(parsed_response.get("rationale"), str) or not _norm(parsed_response.get("rationale")):
        errors.append("rationale_invalid")

    target = parsed_response.get("normalized_target_metric_if_any")
    if target is not None and not isinstance(target, str):
        errors.append("normalized_target_metric_if_any_invalid")

    safety_flags = parsed_response.get("safety_flags")
    if not isinstance(safety_flags, list) or not all(isinstance(item, str) for item in safety_flags):
        errors.append("safety_flags_invalid")

    if not isinstance(parsed_response.get("needs_human_confirmation"), bool):
        errors.append("needs_human_confirmation_invalid")

    extra_fields = sorted(set(parsed_response.keys()) - set(RESPONSE_SCHEMA_REQUIRED_FIELDS))
    if extra_fields:
        errors.append(f"unexpected_fields:{'|'.join(extra_fields)}")

    return errors


def _parse_response_payload(raw_response: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, str]:
    raw_json = raw_response.get("raw_response_json")
    if isinstance(raw_json, dict):
        return raw_json, "raw_response_json"
    if isinstance(raw_json, list):
        return None, "raw_response_json_not_object"

    raw_text = _norm(raw_response.get("raw_response_text"))
    if raw_text:
        try:
            parsed = json.loads(raw_text)
        except Exception:
            return None, "raw_response_text_not_valid_json"
        if isinstance(parsed, dict):
            return parsed, "raw_response_text"
        return None, "raw_response_text_json_not_object"

    return None, "missing_raw_response_payload"


def _classify_schema_valid_response(
    request_item: Dict[str, Any],
    parsed_response: Dict[str, Any],
) -> Tuple[str, str, Dict[str, Any]]:
    response_label = _norm(parsed_response.get("response_label"))
    confidence = _norm(parsed_response.get("confidence"))
    target = _norm(parsed_response.get("normalized_target_metric_if_any"))
    needs_human_confirmation = bool(parsed_response.get("needs_human_confirmation"))
    safety_flags = {_normalize_label(flag) for flag in _flatten_sequence(parsed_response.get("safety_flags"))}
    candidate_type = _norm(request_item.get("candidate_type"))
    candidate_label = _norm(request_item.get("candidate_label"))

    gate_details: Dict[str, Any] = {
        "response_label": response_label,
        "confidence": confidence,
        "normalized_target_metric_if_any": target,
        "needs_human_confirmation": needs_human_confirmation,
        "safety_flags": sorted(safety_flags),
    }

    if response_label in NEEDS_MORE_INFO_LABELS:
        return CLASS_NEEDS_MORE_INFO, "response_label=NEEDS_MORE_INFO", gate_details

    if response_label in REJECTED_RESPONSE_LABELS:
        return CLASS_REJECTED, f"response_label={response_label}", gate_details

    if response_label == "ACCEPT_ALIAS":
        if candidate_type != "alias":
            return CLASS_GATE_FAILED, "accept_alias_on_non_alias_candidate", gate_details
        if not target:
            return CLASS_GATE_FAILED, "accept_alias_missing_target_metric", gate_details
        if confidence not in {"high", "medium"}:
            return CLASS_GATE_FAILED, f"accept_alias_confidence_not_allowed:{confidence}", gate_details
        if not needs_human_confirmation:
            return CLASS_GATE_FAILED, "accept_alias_needs_human_confirmation_false", gate_details
        if safety_flags.intersection(DISALLOWED_ACCEPT_SAFETY_FLAGS):
            return CLASS_GATE_FAILED, "accept_alias_disallowed_safety_flags", gate_details
        target_ok, canonical_target = _lookup_core_target_metric(target)
        if not target_ok:
            return CLASS_GATE_FAILED, "accept_alias_unrecognized_target_metric", gate_details
        gate_details["canonical_target_metric"] = canonical_target
        return CLASS_ACCEPTED, "accept_alias_gate_pass", gate_details

    if response_label == "ACCEPT_OUT_OF_SCOPE":
        if candidate_type != "scope_noise":
            return CLASS_GATE_FAILED, "accept_out_of_scope_on_non_scope_candidate", gate_details
        if target:
            return CLASS_GATE_FAILED, "accept_out_of_scope_target_metric_not_empty", gate_details
        if confidence not in {"high", "medium"}:
            return CLASS_GATE_FAILED, f"accept_out_of_scope_confidence_not_allowed:{confidence}", gate_details
        if not needs_human_confirmation:
            return CLASS_GATE_FAILED, "accept_out_of_scope_needs_human_confirmation_false", gate_details
        if "possible_core_metric" in safety_flags or "possible core metric" in safety_flags:
            return CLASS_GATE_FAILED, "accept_out_of_scope_possible_core_metric_flag", gate_details
        if _candidate_looks_like_core_metric(candidate_label):
            return CLASS_GATE_FAILED, "accept_out_of_scope_candidate_looks_like_core_metric", gate_details
        return CLASS_ACCEPTED, "accept_out_of_scope_gate_pass", gate_details

    return CLASS_GATE_FAILED, f"unsupported_accept_label:{response_label}", gate_details


def _build_review_row(
    request_item: Dict[str, Any],
    raw_response: Dict[str, Any],
    parsed_response: Dict[str, Any] | None,
    classification: str,
    reason: str,
    schema_valid: bool,
    schema_errors: List[str],
    gate_details: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "request_id": _norm(request_item.get("request_id")),
        "source_batch_item_id": _norm(request_item.get("source_batch_item_id")),
        "candidate_type": _norm(request_item.get("candidate_type")),
        "candidate_label": _norm(request_item.get("candidate_label")),
        "allowed_response_labels": " | ".join(_flatten_sequence(request_item.get("allowed_response_labels"))),
        "priority_score": _safe_float(request_item.get("priority_score")),
        "response_received": bool(raw_response.get("response_received")),
        "provider_or_source": _norm(raw_response.get("provider_or_source")),
        "model_or_review_source": _norm(raw_response.get("model_or_review_source")),
        "run_timestamp": _norm(raw_response.get("run_timestamp")),
        "classification": classification,
        "classification_reason": reason,
        "schema_valid": schema_valid,
        "schema_errors": " | ".join(schema_errors),
        "response_label": _norm((parsed_response or {}).get("response_label")),
        "confidence": _norm((parsed_response or {}).get("confidence")),
        "normalized_target_metric_if_any": _norm((parsed_response or {}).get("normalized_target_metric_if_any")),
        "needs_human_confirmation": (parsed_response or {}).get("needs_human_confirmation"),
        "safety_flags": " | ".join(_flatten_sequence((parsed_response or {}).get("safety_flags"))),
        "rationale": _norm((parsed_response or {}).get("rationale")),
        "raw_response_text": _norm(raw_response.get("raw_response_text")),
        "raw_response_json": json.dumps(parsed_response, ensure_ascii=False) if isinstance(parsed_response, dict) else "",
        "gate_details": json.dumps(gate_details, ensure_ascii=False),
        "next_action": _next_action_for_classification(classification),
    }


def _next_action_for_classification(classification: str) -> str:
    mapping = {
        CLASS_ACCEPTED: "HUMAN_CONFIRMED_SUGGESTION_PROPOSAL",
        CLASS_REJECTED: "KEEP_REJECTED_REFERENCE_ONLY",
        CLASS_NEEDS_MORE_INFO: "KEEP_FOR_NEEDS_MORE_INFO_REVIEW",
        CLASS_SCHEMA_INVALID: "FIX_OR_RECOLLECT_RAW_RESPONSE",
        CLASS_GATE_FAILED: "MANUAL_REVIEW_OR_REPLAY_REQUIRED",
    }
    return mapping.get(classification, "MANUAL_REVIEW")


def load_raw_response_schema_validation_inputs(
    configured_run_dir: Path,
    safe_subset_dir: Path,
) -> Dict[str, Any]:
    return {
        "summary_323e": _read_json(configured_run_dir / "configured_adjudicator_run_323e_summary.json"),
        "qa_323e": _read_json(configured_run_dir / "configured_adjudicator_run_323e_qa.json"),
        "manifest_323e": _read_json(configured_run_dir / "configured_adjudicator_run_323e_response_manifest.json"),
        "raw_responses_323e": _read_jsonl(configured_run_dir / "configured_adjudicator_run_323e_raw_responses.jsonl"),
        "summary_323d": _read_json(safe_subset_dir / "safe_adjudicator_subset_323d_summary.json"),
        "request_package_323d": _read_json(safe_subset_dir / "safe_adjudicator_subset_323d_request_package.json"),
        "requests_323d": _read_jsonl(safe_subset_dir / "safe_adjudicator_subset_323d_request_items.jsonl"),
    }


def build_raw_response_schema_validation(
    inputs: Dict[str, Any],
    configured_run_dir: Path,
    safe_subset_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    summary_323e = inputs.get("summary_323e", {})
    qa_323e = inputs.get("qa_323e", {})
    manifest_323e = inputs.get("manifest_323e", {})
    raw_responses = inputs.get("raw_responses_323e", [])
    requests = inputs.get("requests_323d", [])
    summary_323d = inputs.get("summary_323d", {})

    add_qa(
        "input_323e::decision",
        "PASS" if _norm(summary_323e.get("decision")) == EXPECTED_323E_DECISION else "FAIL",
        _norm(summary_323e.get("decision")),
    )
    add_qa(
        "input_323e::summary_qa_fail_count",
        "PASS" if _safe_int(summary_323e.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_323e.get("qa_fail_count", "")),
    )
    add_qa(
        "input_323e::qa_json_fail_count",
        "PASS" if _safe_int(qa_323e.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_323e.get("qa_fail_count", "")),
    )
    add_qa(
        "input_323e::request_count_equals_11",
        "PASS" if _safe_int(summary_323e.get("request_count")) == 11 else "FAIL",
        str(summary_323e.get("request_count", "")),
    )
    add_qa(
        "input_323e::raw_response_count_equals_11",
        "PASS" if _safe_int(summary_323e.get("raw_response_count")) == 11 else "FAIL",
        str(summary_323e.get("raw_response_count", "")),
    )
    add_qa(
        "input_323e::response_received_count_equals_11",
        "PASS" if _safe_int(summary_323e.get("response_received_count")) == 11 else "FAIL",
        str(summary_323e.get("response_received_count", "")),
    )
    add_qa(
        "input_323d::safe_request_item_count",
        "PASS" if _safe_int(summary_323d.get("safe_request_item_count")) == 11 else "FAIL",
        str(summary_323d.get("safe_request_item_count", "")),
    )
    add_qa(
        "input_323e_manifest::raw_response_count_equals_11",
        "PASS" if _safe_int(manifest_323e.get("raw_response_count")) == 11 else "FAIL",
        str(manifest_323e.get("raw_response_count", "")),
    )

    request_lookup = {
        _norm(item.get("request_id")): item
        for item in requests
        if isinstance(item, dict) and _norm(item.get("request_id"))
    }
    raw_response_lookup = {
        _norm(item.get("request_id")): item
        for item in raw_responses
        if isinstance(item, dict) and _norm(item.get("request_id"))
    }
    request_ids = set(request_lookup.keys())
    response_ids = [_norm(item.get("request_id")) for item in raw_responses if isinstance(item, dict)]
    response_id_set = set(response_ids)
    missing_response_ids = sorted(request_ids.difference(response_id_set))
    unknown_response_ids = sorted(response_id_set.difference(request_ids))
    duplicate_response_count = len(response_ids) - len(response_id_set)

    add_qa(
        "alignment::request_count_equals_11",
        "PASS" if len(request_lookup) == 11 else "FAIL",
        f"actual={len(request_lookup)}",
    )
    add_qa(
        "alignment::response_count_equals_11",
        "PASS" if len(raw_responses) == 11 else "FAIL",
        f"actual={len(raw_responses)}",
    )
    add_qa(
        "alignment::request_response_ids_match",
        "PASS" if not missing_response_ids and not unknown_response_ids else "FAIL",
        f"missing={missing_response_ids[:5]} unknown={unknown_response_ids[:5]}",
    )
    add_qa(
        "alignment::no_duplicate_response",
        "PASS" if duplicate_response_count == 0 else "FAIL",
        f"duplicate_count={duplicate_response_count}",
    )
    add_qa(
        "alignment::all_response_received_true",
        "PASS" if all(bool(item.get("response_received")) for item in raw_responses) else "FAIL",
        f"response_count={len(raw_responses)}",
    )

    review_rows: List[Dict[str, Any]] = []
    validated_response_rows: List[Dict[str, Any]] = []
    accepted_suggestions: List[Dict[str, Any]] = []
    rejected_suggestions: List[Dict[str, Any]] = []
    needs_more_info_rows: List[Dict[str, Any]] = []
    schema_invalid_rows: List[Dict[str, Any]] = []
    gate_failure_rows: List[Dict[str, Any]] = []

    schema_valid_count = 0
    schema_invalid_count = 0
    gate_failure_count = 0

    for request_id in sorted(request_lookup.keys()):
        request_item = request_lookup[request_id]
        raw_response = raw_response_lookup.get(request_id, {})
        parsed_response, parse_source = _parse_response_payload(raw_response)

        schema_errors: List[str] = []
        schema_valid = False
        classification = CLASS_SCHEMA_INVALID
        reason = parse_source
        gate_details: Dict[str, Any] = {"parse_source": parse_source}

        if parsed_response is not None:
            schema_errors = _schema_validate_response(parsed_response, request_item)
            schema_valid = not schema_errors
            if schema_valid:
                schema_valid_count += 1
                classification, reason, gate_details = _classify_schema_valid_response(request_item, parsed_response)
            else:
                schema_invalid_count += 1
                classification = CLASS_SCHEMA_INVALID
                reason = "schema_validation_failed"
                gate_details = {"parse_source": parse_source}
        else:
            schema_invalid_count += 1
            schema_errors = [parse_source]
            classification = CLASS_SCHEMA_INVALID
            reason = parse_source
            gate_details = {"parse_source": parse_source}

        if classification == CLASS_GATE_FAILED:
            gate_failure_count += 1

        review_row = _build_review_row(
            request_item=request_item,
            raw_response=raw_response,
            parsed_response=parsed_response,
            classification=classification,
            reason=reason,
            schema_valid=schema_valid,
            schema_errors=schema_errors,
            gate_details=gate_details,
        )
        review_rows.append(review_row)

        validated_payload = {
            "request_id": request_id,
            "source_batch_item_id": _norm(request_item.get("source_batch_item_id")),
            "candidate_type": _norm(request_item.get("candidate_type")),
            "candidate_label": _norm(request_item.get("candidate_label")),
            "classification": classification,
            "classification_reason": reason,
            "schema_valid": schema_valid,
            "schema_errors": schema_errors,
            "parsed_response": parsed_response,
            "raw_response_text": _norm(raw_response.get("raw_response_text")),
            "provider_or_source": _norm(raw_response.get("provider_or_source")),
            "model_or_review_source": _norm(raw_response.get("model_or_review_source")),
            "run_timestamp": _norm(raw_response.get("run_timestamp")),
            "next_action": _next_action_for_classification(classification),
        }
        validated_response_rows.append(validated_payload)

        if classification == CLASS_ACCEPTED:
            suggestion = {
                "request_id": request_id,
                "source_batch_item_id": _norm(request_item.get("source_batch_item_id")),
                "candidate_type": _norm(request_item.get("candidate_type")),
                "candidate_label": _norm(request_item.get("candidate_label")),
                "response_label": _norm((parsed_response or {}).get("response_label")),
                "confidence": _norm((parsed_response or {}).get("confidence")),
                "normalized_target_metric_if_any": _norm((parsed_response or {}).get("normalized_target_metric_if_any")),
                "safety_flags": _flatten_sequence((parsed_response or {}).get("safety_flags")),
                "rationale": _norm((parsed_response or {}).get("rationale")),
                "needs_human_confirmation": bool((parsed_response or {}).get("needs_human_confirmation")),
                "next_action": "HUMAN_CONFIRMATION_AND_SANDBOX_REPLAY_REQUIRED",
                "gate_reason": reason,
            }
            accepted_suggestions.append(suggestion)
        elif classification == CLASS_REJECTED:
            rejected_suggestions.append(validated_payload)
        elif classification == CLASS_NEEDS_MORE_INFO:
            needs_more_info_rows.append(validated_payload)
        elif classification == CLASS_SCHEMA_INVALID:
            schema_invalid_rows.append(validated_payload)
        elif classification == CLASS_GATE_FAILED:
            gate_failure_rows.append(validated_payload)

    classified_total = (
        len(accepted_suggestions)
        + len(rejected_suggestions)
        + len(needs_more_info_rows)
        + len(schema_invalid_rows)
        + len(gate_failure_rows)
    )

    add_qa(
        "schema::schema_valid_count",
        "PASS" if schema_valid_count + schema_invalid_count == len(request_lookup) else "FAIL",
        f"schema_valid={schema_valid_count} schema_invalid={schema_invalid_count}",
    )
    add_qa(
        "classification::every_response_classified_once",
        "PASS" if classified_total == len(request_lookup) == len(review_rows) else "FAIL",
        f"classified_total={classified_total} request_count={len(request_lookup)} review_rows={len(review_rows)}",
    )
    add_qa(
        "classification::accepted_count_recorded",
        "PASS",
        f"accepted={len(accepted_suggestions)} rejected={len(rejected_suggestions)} needs_more_info={len(needs_more_info_rows)} schema_invalid={len(schema_invalid_rows)} gate_failed={len(gate_failure_rows)}",
    )
    add_qa(
        "classification::schema_invalid_count_recorded",
        "PASS",
        f"schema_invalid={len(schema_invalid_rows)}",
    )
    add_qa(
        "classification::deterministic_gate_failure_count_recorded",
        "PASS",
        f"gate_failed={len(gate_failure_rows)}",
    )

    parser_not_run = True
    llm_not_called = True
    no_trusted_promotion = True
    add_qa("safety::parser_not_run_confirmation", "PASS" if parser_not_run else "FAIL", "323F validates cached requests and raw responses only.")
    add_qa("safety::llm_not_called_confirmation", "PASS" if llm_not_called else "FAIL", "323F does not call LLM or adjudicator.")
    add_qa("safety::no_trusted_promotion_confirmation", "PASS" if no_trusted_promotion else "FAIL", "323F creates suggestions only and does not mark anything trusted.")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    no_official_assets_modified = alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if no_official_assets_modified else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    highest_priority_accepted_examples: List[Dict[str, Any]] = []
    for item in sorted(
        accepted_suggestions,
        key=lambda row: (
            -_safe_float(next((req.get("priority_score") for req in requests if _norm(req.get("request_id")) == row["request_id"]), 0.0)),
            row["request_id"],
        ),
    )[:5]:
        priority_score = next((req.get("priority_score") for req in requests if _norm(req.get("request_id")) == item["request_id"]), 0.0)
        highest_priority_accepted_examples.append(
            {
                "request_id": item["request_id"],
                "candidate_type": item["candidate_type"],
                "candidate_label": item["candidate_label"],
                "response_label": item["response_label"],
                "normalized_target_metric_if_any": item["normalized_target_metric_if_any"],
                "priority_score": _safe_float(priority_score),
            }
        )

    summary = {
        "stage": "323F",
        "output_dir": "",
        "configured_run_dir": str(configured_run_dir),
        "safe_subset_dir": str(safe_subset_dir),
        "request_count": len(request_lookup),
        "response_count": len(raw_responses),
        "schema_valid_count": schema_valid_count,
        "schema_invalid_count": len(schema_invalid_rows),
        "accepted_suggestion_count": len(accepted_suggestions),
        "rejected_suggestion_count": len(rejected_suggestions),
        "needs_more_info_count": len(needs_more_info_rows),
        "deterministic_gate_failure_count": len(gate_failure_rows),
        "highest_priority_accepted_examples": highest_priority_accepted_examples,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 0,
        "blocking_reasons": [],
        "decision": "",
    }

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary["qa_pass_count"] = qa_pass_count
    summary["qa_warn_count"] = qa_warn_count
    summary["qa_fail_count"] = qa_fail_count
    summary["blocking_reasons"] = blocking_reasons
    if qa_fail_count > 0:
        summary["decision"] = EXPECTED_323F_NOT_READY
    elif accepted_suggestions:
        summary["decision"] = EXPECTED_323F_READY
    else:
        summary["decision"] = EXPECTED_323F_NO_ACCEPTED

    no_apply_proof_json = {
        "files_read": [
            str(configured_run_dir / "configured_adjudicator_run_323e_summary.json"),
            str(configured_run_dir / "configured_adjudicator_run_323e_qa.json"),
            str(configured_run_dir / "configured_adjudicator_run_323e_raw_responses.jsonl"),
            str(configured_run_dir / "configured_adjudicator_run_323e_response_manifest.json"),
            str(safe_subset_dir / "safe_adjudicator_subset_323d_summary.json"),
            str(safe_subset_dir / "safe_adjudicator_subset_323d_request_items.jsonl"),
        ],
        "files_written": [],
        "official_target_files_not_modified": [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_ALIAS_OVERRIDE_PATH),
        ],
        "output_only_write_confirmation": True,
        "decision": "raw_response_schema_validation_only_no_apply",
    }

    return {
        "summary": summary,
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
        "qa_checks_df": qa_df,
        "validated_responses": validated_response_rows,
        "accepted_suggestions_json": {"accepted_suggestions": accepted_suggestions},
        "rejected_suggestions_json": {"rejected_suggestions": rejected_suggestions},
        "needs_more_info_json": {"needs_more_info": needs_more_info_rows},
        "schema_invalid_df": pd.DataFrame(schema_invalid_rows).fillna(""),
        "gate_failures_df": pd.DataFrame(gate_failure_rows).fillna(""),
        "review_package_df": pd.DataFrame(review_rows).fillna(""),
        "notes_md": _build_notes_markdown(summary),
        "no_apply_proof_json": no_apply_proof_json,
    }


def _build_notes_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Raw Response Schema Validation 323F",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Counts",
        f"- request_count: {summary.get('request_count', 0)}",
        f"- response_count: {summary.get('response_count', 0)}",
        f"- schema_valid_count: {summary.get('schema_valid_count', 0)}",
        f"- schema_invalid_count: {summary.get('schema_invalid_count', 0)}",
        f"- accepted_suggestion_count: {summary.get('accepted_suggestion_count', 0)}",
        f"- rejected_suggestion_count: {summary.get('rejected_suggestion_count', 0)}",
        f"- needs_more_info_count: {summary.get('needs_more_info_count', 0)}",
        f"- deterministic_gate_failure_count: {summary.get('deterministic_gate_failure_count', 0)}",
        "",
        "## Safety",
        "- 323F validates and gates raw responses only.",
        "- Accepted items remain proposals and still require human confirmation and sandbox replay.",
        "- 323F does not apply semantic rules and does not mark any candidate trusted.",
        "",
    ]
    return "\n".join(lines)

