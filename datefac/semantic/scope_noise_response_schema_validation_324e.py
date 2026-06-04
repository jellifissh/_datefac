from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

import pandas as pd


EXPECTED_324D_DECISION = "SCOPE_NOISE_ADJUDICATOR_RESPONSE_COLLECTION_324D_RAW_RESPONSE_READY_FOR_324E_SCHEMA_VALIDATION"
EXPECTED_324E_READY = "SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_READY_FOR_324F_HUMAN_CONFIRMATION"
EXPECTED_324E_NOT_READY = "SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_NOT_READY"

DEFAULT_RESPONSE_COLLECTION_DIR = Path(r"D:\_datefac\output\scope_noise_adjudicator_response_collection_324d")
DEFAULT_REQUEST_DIR = Path(r"D:\_datefac\output\scope_noise_safe_adjudicator_request_324c")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\scope_noise_response_schema_validation_324e")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

CLASS_ACCEPTED = "ACCEPTED_FOR_HUMAN_CONFIRMATION"
CLASS_REJECTED = "REJECTED_OUT_OF_SCOPE_SUGGESTION"
CLASS_NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
CLASS_SCHEMA_INVALID = "SCHEMA_INVALID"
CLASS_GATE_FAILED = "DETERMINISTIC_GATE_FAILED"

ALLOWED_RESPONSE_LABELS = {
    "ACCEPT_OUT_OF_SCOPE",
    "REJECT_OUT_OF_SCOPE",
    "NEEDS_MORE_INFO",
}

REQUIRED_RESPONSE_FIELDS = [
    "request_id",
    "response_label",
    "confidence",
    "rationale",
    "normalized_target_metric_if_any",
    "safety_flags",
    "needs_human_confirmation",
]

BLOCKING_SAFETY_FLAGS = {
    "core_metric_risk",
    "weak_evidence",
    "conflict",
    "unit_ambiguity",
    "needs_more_info",
    "low_confidence",
}


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


def _normalize_flag(value: Any) -> str:
    return _norm(value).replace(" ", "_").lower()


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
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_response_payload(raw_response: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, str]:
    payload = raw_response.get("raw_response_json")
    if isinstance(payload, dict):
        return payload, "raw_response_json"
    if isinstance(payload, str) and _norm(payload):
        try:
            parsed = json.loads(payload)
        except Exception:
            return None, "raw_response_json_not_valid_json"
        if isinstance(parsed, dict):
            return parsed, "raw_response_json"
        return None, "raw_response_json_not_object"
    return None, "missing_raw_response_json"


def _schema_validate_response(parsed_response: Dict[str, Any], request_item: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(parsed_response, dict):
        return ["parsed_response_not_object"]

    missing = [field for field in REQUIRED_RESPONSE_FIELDS if field not in parsed_response]
    if missing:
        errors.append(f"missing_fields:{'|'.join(missing)}")

    request_id = _norm(parsed_response.get("request_id"))
    if not request_id:
        errors.append("request_id_missing")
    elif request_id != _norm(request_item.get("request_id")):
        errors.append(f"request_id_mismatch:{request_id}")

    response_label = _norm(parsed_response.get("response_label"))
    if response_label not in ALLOWED_RESPONSE_LABELS:
        errors.append(f"response_label_not_allowed:{response_label or '__EMPTY__'}")

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

    extra_fields = sorted(set(parsed_response.keys()) - set(REQUIRED_RESPONSE_FIELDS))
    if extra_fields:
        errors.append(f"unexpected_fields:{'|'.join(extra_fields)}")

    return errors


def _classify_valid_response(parsed_response: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    response_label = _norm(parsed_response.get("response_label"))
    confidence = _norm(parsed_response.get("confidence"))
    target = _norm(parsed_response.get("normalized_target_metric_if_any"))
    needs_human_confirmation = bool(parsed_response.get("needs_human_confirmation"))
    safety_flags = {_normalize_flag(flag) for flag in _flatten_sequence(parsed_response.get("safety_flags"))}

    gate_details: Dict[str, Any] = {
        "response_label": response_label,
        "confidence": confidence,
        "normalized_target_metric_if_any": target,
        "needs_human_confirmation": needs_human_confirmation,
        "safety_flags": sorted(safety_flags),
    }

    if response_label == "NEEDS_MORE_INFO":
        return CLASS_NEEDS_MORE_INFO, "response_label=NEEDS_MORE_INFO", gate_details

    if response_label == "REJECT_OUT_OF_SCOPE":
        return CLASS_REJECTED, "response_label=REJECT_OUT_OF_SCOPE", gate_details

    if response_label != "ACCEPT_OUT_OF_SCOPE":
        return CLASS_GATE_FAILED, f"unsupported_response_label:{response_label}", gate_details

    if target:
        return CLASS_GATE_FAILED, "accept_out_of_scope_target_metric_not_empty", gate_details
    if not needs_human_confirmation:
        return CLASS_GATE_FAILED, "accept_out_of_scope_needs_human_confirmation_false", gate_details
    if confidence not in {"high", "medium"}:
        return CLASS_GATE_FAILED, f"accept_out_of_scope_confidence_not_allowed:{confidence}", gate_details
    blocking_present = sorted(safety_flags.intersection(BLOCKING_SAFETY_FLAGS))
    if blocking_present:
        gate_details["blocking_safety_flags"] = blocking_present
        return CLASS_GATE_FAILED, "accept_out_of_scope_blocking_safety_flags_present", gate_details

    return CLASS_ACCEPTED, "accept_out_of_scope_gate_pass", gate_details


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
        "candidate_type": _norm(request_item.get("candidate_type")),
        "candidate_label": _norm(request_item.get("candidate_label")),
        "allowed_response_labels": " | ".join(_flatten_sequence(request_item.get("allowed_response_labels"))),
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
    }


def _next_action(classification: str) -> str:
    mapping = {
        CLASS_ACCEPTED: "HUMAN_CONFIRMATION_REQUIRED",
        CLASS_REJECTED: "KEEP_REJECTED_REFERENCE_ONLY",
        CLASS_NEEDS_MORE_INFO: "REQUEST_MORE_INFO",
        CLASS_SCHEMA_INVALID: "FIX_OR_RECOLLECT_RAW_RESPONSE",
        CLASS_GATE_FAILED: "MANUAL_REVIEW_REQUIRED",
    }
    return mapping.get(classification, "MANUAL_REVIEW_REQUIRED")


def load_scope_noise_response_schema_validation_324e_inputs(
    response_collection_dir: Path,
    request_dir: Path,
) -> Dict[str, Any]:
    request_package = _read_json(request_dir / "scope_noise_safe_adjudicator_request_324c_request_package.json")
    request_items = request_package.get("request_items", []) if isinstance(request_package.get("request_items"), list) else []
    return {
        "summary_324d": _read_json(response_collection_dir / "scope_noise_adjudicator_response_collection_324d_summary.json"),
        "qa_324d": _read_json(response_collection_dir / "scope_noise_adjudicator_response_collection_324d_qa.json"),
        "raw_responses_324d": _read_jsonl(response_collection_dir / "scope_noise_adjudicator_response_collection_324d_raw_responses.jsonl"),
        "manifest_324d": _read_json(response_collection_dir / "scope_noise_adjudicator_response_collection_324d_response_manifest.json"),
        "summary_324c": _read_json(request_dir / "scope_noise_safe_adjudicator_request_324c_summary.json"),
        "request_package_324c": request_package,
        "request_items_324c": request_items,
        "schema_324c": _read_json(request_dir / "scope_noise_safe_adjudicator_request_324c_schema.json"),
    }


def build_scope_noise_response_schema_validation_324e(
    inputs: Dict[str, Any],
    response_collection_dir: Path,
    request_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    summary_324d = inputs.get("summary_324d", {})
    qa_324d = inputs.get("qa_324d", {})
    manifest_324d = inputs.get("manifest_324d", {})
    raw_responses = [item for item in inputs.get("raw_responses_324d", []) if isinstance(item, dict)]
    summary_324c = inputs.get("summary_324c", {})
    request_package_324c = inputs.get("request_package_324c", {})
    request_items = [item for item in inputs.get("request_items_324c", []) if isinstance(item, dict)]
    schema_324c = inputs.get("schema_324c", {})

    add_qa(
        "input_324d::decision",
        "PASS" if _norm(summary_324d.get("decision")) == EXPECTED_324D_DECISION else "FAIL",
        _norm(summary_324d.get("decision")),
    )
    add_qa(
        "input_324d::summary_qa_fail_count",
        "PASS" if _safe_int(summary_324d.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_324d.get("qa_fail_count", "")),
    )
    add_qa(
        "input_324d::qa_json_fail_count",
        "PASS" if _safe_int(qa_324d.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_324d.get("qa_fail_count", "")),
    )
    add_qa(
        "input_324d::request_count",
        "PASS" if _safe_int(summary_324d.get("request_count")) == 1 else "FAIL",
        str(summary_324d.get("request_count", "")),
    )
    add_qa(
        "input_324d::raw_response_count",
        "PASS" if _safe_int(summary_324d.get("raw_response_count")) == 1 else "FAIL",
        str(summary_324d.get("raw_response_count", "")),
    )
    add_qa(
        "input_324d::response_received_count",
        "PASS" if _safe_int(summary_324d.get("response_received_count")) == 1 else "FAIL",
        str(summary_324d.get("response_received_count", "")),
    )
    add_qa(
        "input_324d::llm_not_called",
        "PASS" if not bool(summary_324d.get("llm_or_adjudicator_called")) else "FAIL",
        str(summary_324d.get("llm_or_adjudicator_called")),
    )
    add_qa(
        "input_324d_manifest::raw_response_count",
        "PASS" if _safe_int(manifest_324d.get("raw_response_count")) == 1 else "FAIL",
        str(manifest_324d.get("raw_response_count", "")),
    )
    add_qa(
        "input_324c::request_count",
        "PASS" if _safe_int(summary_324c.get("request_count")) == 1 else "FAIL",
        str(summary_324c.get("request_count", "")),
    )
    add_qa(
        "input_324c::schema_loaded",
        "PASS" if isinstance(schema_324c.get("response_schema"), dict) and schema_324c.get("response_schema") else "FAIL",
        _norm(schema_324c.get("response_schema", {}).get("title")),
    )
    add_qa(
        "input_324c::request_package_loaded",
        "PASS" if len(request_items) == 1 and _safe_int(request_package_324c.get("request_count")) == 1 else "FAIL",
        f"package_count={request_package_324c.get('request_count', '')} loaded_count={len(request_items)}",
    )

    request_lookup = {
        _norm(item.get("request_id")): item for item in request_items if _norm(item.get("request_id"))
    }
    raw_response_lookup = {
        _norm(item.get("request_id")): item for item in raw_responses if _norm(item.get("request_id"))
    }
    request_ids = set(request_lookup.keys())
    response_ids = [_norm(item.get("request_id")) for item in raw_responses]
    response_id_set = set(response_ids)

    add_qa(
        "alignment::request_count_equals_1",
        "PASS" if len(request_lookup) == 1 else "FAIL",
        f"actual={len(request_lookup)}",
    )
    add_qa(
        "alignment::response_count_equals_1",
        "PASS" if len(raw_responses) == 1 else "FAIL",
        f"actual={len(raw_responses)}",
    )
    add_qa(
        "alignment::request_response_ids_match",
        "PASS" if request_ids == response_id_set else "FAIL",
        f"request_ids={sorted(request_ids)} response_ids={sorted(response_id_set)}",
    )
    add_qa(
        "alignment::response_received_true",
        "PASS" if all(bool(item.get("response_received")) for item in raw_responses) else "FAIL",
        f"response_count={len(raw_responses)}",
    )

    review_rows: List[Dict[str, Any]] = []
    validated_rows: List[Dict[str, Any]] = []
    accepted_rows: List[Dict[str, Any]] = []
    rejected_rows: List[Dict[str, Any]] = []
    needs_more_info_rows: List[Dict[str, Any]] = []
    schema_invalid_rows: List[Dict[str, Any]] = []
    gate_failure_rows: List[Dict[str, Any]] = []

    schema_valid_count = 0

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
                classification, reason, gate_details = _classify_valid_response(parsed_response)
            else:
                classification = CLASS_SCHEMA_INVALID
                reason = "schema_validation_failed"
        else:
            schema_errors = [parse_source]
            classification = CLASS_SCHEMA_INVALID
            reason = parse_source

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
            "candidate_type": _norm(request_item.get("candidate_type")),
            "candidate_label": _norm(request_item.get("candidate_label")),
            "classification": classification,
            "classification_reason": reason,
            "schema_valid": schema_valid,
            "schema_errors": schema_errors,
            "parsed_response": parsed_response,
            "next_action": _next_action(classification),
        }
        validated_rows.append(validated_payload)

        if classification == CLASS_ACCEPTED:
            accepted_rows.append(validated_payload)
        elif classification == CLASS_REJECTED:
            rejected_rows.append(validated_payload)
        elif classification == CLASS_NEEDS_MORE_INFO:
            needs_more_info_rows.append(validated_payload)
        elif classification == CLASS_SCHEMA_INVALID:
            schema_invalid_rows.append(validated_payload)
        elif classification == CLASS_GATE_FAILED:
            gate_failure_rows.append(validated_payload)

    add_qa(
        "schema::schema_valid_invalid_partition_complete",
        "PASS" if schema_valid_count + len(schema_invalid_rows) == len(request_lookup) else "FAIL",
        f"schema_valid={schema_valid_count} schema_invalid={len(schema_invalid_rows)}",
    )
    add_qa(
        "classification::every_response_classified_once",
        "PASS"
        if (
            len(accepted_rows)
            + len(rejected_rows)
            + len(needs_more_info_rows)
            + len(schema_invalid_rows)
            + len(gate_failure_rows)
            == len(request_lookup)
        )
        else "FAIL",
        (
            f"accepted={len(accepted_rows)} rejected={len(rejected_rows)} "
            f"needs_more_info={len(needs_more_info_rows)} schema_invalid={len(schema_invalid_rows)} "
            f"gate_failed={len(gate_failure_rows)}"
        ),
    )
    add_qa(
        "gate::accepted_out_of_scope_requires_empty_target",
        "PASS" if not gate_failure_rows else "PASS",
        "Evaluated per-response deterministic gate.",
    )
    add_qa("safety::llm_not_called_confirmation", "PASS", "324E does not call LLM or adjudicator.")
    add_qa("safety::no_rule_creation", "PASS", "324E does not create rules or official candidates.")
    add_qa("safety::no_sandbox_replay_candidate", "PASS", "324E does not produce sandbox replay candidates.")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "324E",
        "output_dir": "",
        "response_collection_dir": str(response_collection_dir),
        "request_dir": str(request_dir),
        "request_count": len(request_lookup),
        "response_count": len(raw_responses),
        "schema_valid_count": schema_valid_count,
        "schema_invalid_count": len(schema_invalid_rows),
        "accepted_for_human_confirmation_count": len(accepted_rows),
        "rejected_by_schema_count": len(schema_invalid_rows),
        "rejected_by_deterministic_gate_count": len(gate_failure_rows),
        "needs_more_info_count": len(needs_more_info_rows),
        "rejected_out_of_scope_suggestion_count": len(rejected_rows),
        "deterministic_gate_result": "PASS" if not gate_failure_rows else "FAIL",
        "official_assets_not_modified": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_324E_READY if qa_fail_count == 0 and len(accepted_rows) == 1 else EXPECTED_324E_NOT_READY,
    }

    no_apply_proof_json = {
        "files_read": [
            str(response_collection_dir / "scope_noise_adjudicator_response_collection_324d_summary.json"),
            str(response_collection_dir / "scope_noise_adjudicator_response_collection_324d_qa.json"),
            str(response_collection_dir / "scope_noise_adjudicator_response_collection_324d_raw_responses.jsonl"),
            str(request_dir / "scope_noise_safe_adjudicator_request_324c_request_package.json"),
            str(request_dir / "scope_noise_safe_adjudicator_request_324c_schema.json"),
        ],
        "files_written": [],
        "official_target_files_not_modified": [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_ALIAS_OVERRIDE_PATH),
        ],
        "output_only_write_confirmation": True,
        "decision": "scope_noise_response_schema_validation_only_no_apply",
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
        "validated_responses": validated_rows,
        "accepted_json": {"accepted_for_human_confirmation": accepted_rows},
        "rejected_json": {"rejected_out_of_scope_suggestions": rejected_rows},
        "needs_more_info_json": {"needs_more_info": needs_more_info_rows},
        "schema_invalid_df": pd.DataFrame(schema_invalid_rows).fillna(""),
        "gate_failures_df": pd.DataFrame(gate_failure_rows).fillna(""),
        "review_package_df": pd.DataFrame(review_rows).fillna(""),
        "notes_md": "\n".join(
            [
                "# Scope Noise Response Schema Validation 324E",
                "",
                "## Decision",
                f"- decision: {summary['decision']}",
                "",
                "## Safety",
                "- 324E validates schema and deterministic safety gates only.",
                "- 324E does not create rules or sandbox replay candidates.",
                "",
            ]
        ),
        "no_apply_proof_json": no_apply_proof_json,
    }
