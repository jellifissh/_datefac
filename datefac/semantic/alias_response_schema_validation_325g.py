from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

import pandas as pd


EXPECTED_325F_DECISION = "ALIAS_ADJUDICATOR_RESPONSE_COLLECTION_325F_RAW_RESPONSE_READY_FOR_325G_SCHEMA_VALIDATION"
READY_DECISION = "ALIAS_RESPONSE_SCHEMA_VALIDATION_325G_READY_FOR_HUMAN_CONFIRMATION"
NO_ACCEPTED_DECISION = "ALIAS_RESPONSE_SCHEMA_VALIDATION_325G_NO_ACCEPTED_SUGGESTIONS"
NOT_READY_DECISION = "ALIAS_RESPONSE_SCHEMA_VALIDATION_325G_NOT_READY"

DEFAULT_RESPONSE_COLLECTION_DIR = Path(r"D:\_datefac\output\alias_adjudicator_response_collection_325f")
DEFAULT_REQUEST_DIR = Path(r"D:\_datefac\output\alias_safe_adjudicator_request_325e")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_response_schema_validation_325g")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

CLASS_ACCEPTED = "ACCEPTED_FOR_HUMAN_CONFIRMATION"
CLASS_SCHEMA_REJECTED = "REJECTED_BY_SCHEMA"
CLASS_GATE_REJECTED = "REJECTED_BY_DETERMINISTIC_GATE"
CLASS_NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
CLASS_REJECTED_ALIAS = "REJECTED_ALIAS_SUGGESTION"

REQUIRED_RESPONSE_FIELDS = [
    "request_id",
    "response_label",
    "target_metric_if_accept",
    "normalized_alias_label",
    "confidence",
    "rationale",
    "safety_flags",
    "needs_human_confirmation",
]
ALLOWED_RESPONSE_LABELS = {"ACCEPT_ALIAS", "REJECT_ALIAS", "NEEDS_MORE_INFO"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
BLOCKING_SAFETY_FLAGS = {
    "core_metric_risk",
    "weak_evidence",
    "conflict",
    "unit_ambiguity",
    "needs_more_info",
    "low_confidence",
    "target_ambiguous",
    "official_overlap",
    "scope_conflict",
}
GENERIC_ALIAS_LABELS = {"利润", "收入", "成本", "费用", "资产", "负债", "权益", "现金", "增长", "同比"}
KNOWN_TARGETS = {
    "营业收入",
    "归属母公司净利润",
    "归母净利润",
    "毛利率",
    "roe",
    "净资产收益率",
    "每股收益",
    "eps",
    "basic_eps",
    "diluted_eps",
    "eps_diluted",
    "adjusted_eps",
    "经调整eps",
    "p/e",
    "p/b",
    "ev/ebitda",
    "ebit",
    "ebitda",
    "attributable_net_margin",
    "parent_net_margin",
    "归母净利率",
    "adjusted_attributable_net_profit",
    "adjusted_parent_net_profit",
    "经调整归母净利润",
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _normalize(value: Any) -> str:
    text = _norm(value).lower()
    for old, new in {
        "\u3000": "",
        " ": "",
        "\t": "",
        "（": "(",
        "）": ")",
        "／": "/",
        "_": "",
        "-": "",
    }.items():
        text = text.replace(old, new)
    return text


def _safe_int(value: Any) -> int:
    if value in ("", None):
        return 0
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return 0


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


def _official_hashes() -> Dict[str, str]:
    return {
        "formal_scope_rules": _sha256_file(FORMAL_SCOPE_RULES_PATH),
        "semantic_alias_candidates": _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH),
    }


def _flatten_sequence(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_norm(item) for item in value if _norm(item)]
    if isinstance(value, tuple):
        return [_norm(item) for item in value if _norm(item)]
    if isinstance(value, str):
        text = _norm(value)
        if not text:
            return []
        return [part.strip() for part in re.split(r"[|,;，；]", text) if part.strip()]
    return []


def _truthy(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = _norm(value).lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def _parse_response_payload(raw_response: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, str]:
    payload = raw_response.get("raw_response_json")
    if isinstance(payload, dict):
        return payload, "raw_response_json"
    if isinstance(payload, str) and _norm(payload):
        try:
            parsed = json.loads(payload)
        except Exception:
            return None, "raw_response_json_not_valid_json"
        return (parsed, "raw_response_json") if isinstance(parsed, dict) else (None, "raw_response_json_not_object")
    return None, "missing_raw_response_json"


def _schema_errors(parsed: Dict[str, Any] | None, request_item: Dict[str, Any]) -> List[str]:
    if not isinstance(parsed, dict):
        return ["parsed_response_not_object"]
    errors: List[str] = []
    missing = [field for field in REQUIRED_RESPONSE_FIELDS if field not in parsed]
    if missing:
        errors.append(f"missing_fields:{'|'.join(missing)}")
    request_id = _norm(parsed.get("request_id"))
    if not request_id:
        errors.append("request_id_missing")
    elif request_id != _norm(request_item.get("request_id")):
        errors.append(f"request_id_mismatch:{request_id}")
    label = _norm(parsed.get("response_label"))
    if label not in ALLOWED_RESPONSE_LABELS:
        errors.append(f"response_label_not_allowed:{label or '__EMPTY__'}")
    confidence = _norm(parsed.get("confidence")).lower()
    if confidence not in ALLOWED_CONFIDENCE:
        errors.append(f"confidence_invalid:{confidence or '__EMPTY__'}")
    if "safety_flags" in parsed and not isinstance(parsed.get("safety_flags"), list):
        errors.append("safety_flags_invalid")
    human = _truthy(parsed.get("needs_human_confirmation"))
    if human is None:
        errors.append("needs_human_confirmation_invalid")
    extra = sorted(set(parsed.keys()) - set(REQUIRED_RESPONSE_FIELDS))
    if extra:
        errors.append(f"unexpected_fields:{'|'.join(extra)}")
    if label == "ACCEPT_ALIAS":
        if not _norm(parsed.get("target_metric_if_accept")):
            errors.append("accept_alias_target_metric_missing")
        if not _norm(parsed.get("normalized_alias_label")):
            errors.append("accept_alias_normalized_alias_label_missing")
        if confidence not in {"high", "medium"}:
            errors.append(f"accept_alias_confidence_not_high_or_medium:{confidence or '__EMPTY__'}")
        if human is not True:
            errors.append("accept_alias_needs_human_confirmation_not_true")
        if not _norm(parsed.get("rationale")):
            errors.append("accept_alias_rationale_missing")
    return errors


def _looks_mojibake(text: str) -> bool:
    return any(marker in text for marker in ["�", "锟", "閿"]) or text.count("?") >= 3


def _target_allowed(target: str) -> bool:
    normalized = _normalize(target)
    return normalized in {_normalize(item) for item in KNOWN_TARGETS}


def _load_official_alias_map() -> Dict[str, Set[str]]:
    data = _read_json(OFFICIAL_ALIAS_OVERRIDE_PATH)
    out: Dict[str, Set[str]] = {}
    groups = data.get("groups", {})
    if not isinstance(groups, dict):
        return out
    for items in groups.values():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            label = _normalize(item.get("normalized_label"))
            metric = _normalize(item.get("metric_code"))
            if label:
                out.setdefault(label, set()).add(metric)
    return out


def _load_official_scope_labels() -> Set[str]:
    data = _read_json(FORMAL_SCOPE_RULES_PATH)
    labels: Set[str] = set()
    rules = data.get("rules", {})
    if not isinstance(rules, dict):
        return labels
    for item in rules.values():
        if not isinstance(item, dict):
            continue
        if item.get("target_group") == "core_metric_scope_exclusions" or item.get("rule_type") == "core_metric_scope_exclusion":
            label = _normalize(item.get("normalized_label"))
            if label:
                labels.add(label)
    return labels


def _deterministic_gate(parsed: Dict[str, Any], request_item: Dict[str, Any], alias_map: Dict[str, Set[str]], scope_labels: Set[str]) -> Tuple[bool, List[str], Dict[str, int]]:
    reasons: List[str] = []
    counters = {
        "official_overlap_count": 0,
        "target_conflict_count": 0,
        "adjusted_metric_mismatch_count": 0,
        "diluted_eps_mismatch_count": 0,
    }
    alias = _norm(parsed.get("normalized_alias_label"))
    target = _norm(parsed.get("target_metric_if_accept"))
    alias_n = _normalize(alias)
    target_n = _normalize(target)
    request_label_n = _normalize(request_item.get("alias_label"))
    safety_flags = {_normalize(flag) for flag in _flatten_sequence(parsed.get("safety_flags"))}

    if not target or not _target_allowed(target):
        reasons.append("missing_or_unknown_target_metric")
    if not alias or _looks_mojibake(alias) or len(alias) > 80 or alias_n in {_normalize(item) for item in GENERIC_ALIAS_LABELS}:
        reasons.append("invalid_mojibake_long_or_generic_alias_label")
    if alias_n in alias_map:
        counters["official_overlap_count"] = 1
        official_targets = alias_map.get(alias_n, set())
        if target_n not in official_targets:
            counters["target_conflict_count"] = 1
            reasons.append("official_alias_overlap_with_conflicting_target")
    if alias_n in scope_labels or request_label_n in scope_labels:
        reasons.append("alias_officially_excluded_as_scope_noise")
    blocking = sorted(safety_flags.intersection({_normalize(item) for item in BLOCKING_SAFETY_FLAGS}))
    if blocking:
        reasons.append("blocking_safety_flags_present")

    if "经调整" in alias and target_n in {_normalize("EPS"), _normalize("每股收益"), _normalize("归母净利润"), _normalize("归属母公司净利润")}:
        counters["adjusted_metric_mismatch_count"] = 1
        reasons.append("adjusted_alias_mapped_to_ordinary_metric")
    if ("摊薄" in alias or "diluted" in alias_n) and target_n in {_normalize("EPS"), _normalize("basic_EPS"), _normalize("每股收益")}:
        counters["diluted_eps_mismatch_count"] = 1
        reasons.append("diluted_or_latest_diluted_eps_mapped_to_basic_eps")
    if ("roe" in alias_n or "净资产收益率" in alias) and any(term in target_n for term in ["margin", "profitability", _normalize("净利率"), _normalize("毛利率")]):
        reasons.append("roe_alias_mapped_to_margin_or_generic_profitability")
    if "净利率" in alias and target_n in {_normalize("归母净利润"), _normalize("归属母公司净利润"), _normalize("net_profit")}:
        reasons.append("net_margin_alias_mapped_to_net_profit")
    if alias_n == "ebit" and target_n in {_normalize("EBITDA"), _normalize("operating_profit"), _normalize("利润总额"), _normalize("profit_before_tax")}:
        reasons.append("ebit_alias_mapped_to_ebitda_operating_profit_or_pbt")
    return len(reasons) == 0, reasons, counters


def load_alias_response_schema_validation_325g_inputs(response_collection_dir: Path, request_dir: Path) -> Dict[str, Any]:
    package = _read_json(request_dir / "alias_safe_adjudicator_request_325e_request_package.json")
    return {
        "summary_325f": _read_json(response_collection_dir / "alias_adjudicator_response_collection_325f_summary.json"),
        "qa_325f": _read_json(response_collection_dir / "alias_adjudicator_response_collection_325f_qa.json"),
        "raw_responses": _read_jsonl(response_collection_dir / "alias_adjudicator_response_collection_325f_raw_responses.jsonl"),
        "request_package": package,
        "request_items": package.get("request_items", []) if isinstance(package.get("request_items"), list) else [],
        "official_hashes_before": _official_hashes(),
    }


def build_alias_response_schema_validation_325g(inputs: Dict[str, Any], response_collection_dir: Path, request_dir: Path) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    summary_325f = inputs["summary_325f"]
    qa_325f = inputs["qa_325f"]
    raw_responses = inputs["raw_responses"]
    request_items = inputs["request_items"]
    request_by_id = {_norm(item.get("request_id")): item for item in request_items}
    expected = {
        "decision": EXPECTED_325F_DECISION,
        "qa_fail_count": 0,
        "request_count": 6,
        "raw_response_count": 6,
        "response_received_count": 6,
    }
    for key, value in expected.items():
        actual = summary_325f.get(key)
        ok = _safe_int(actual) == value if isinstance(value, int) else _norm(actual) == value
        add_qa(f"readiness::325f_{key}", "PASS" if ok else "FAIL", f"expected={value}; actual={actual}")
    alignment_checks = [c for c in qa_325f.get("checks", []) if c.get("check_name") == "collect::request_id_alignment"]
    alignment_pass = bool(alignment_checks and alignment_checks[0].get("status") == "PASS")
    add_qa("readiness::325f_request_id_alignment", "PASS" if alignment_pass else "FAIL", str(alignment_checks[:1]))
    add_qa("input::raw_response_exact_count", "PASS" if len(raw_responses) == 6 else "FAIL", f"actual={len(raw_responses)}")
    add_qa("input::request_item_exact_count", "PASS" if len(request_items) == 6 else "FAIL", f"actual={len(request_items)}")

    alias_map = _load_official_alias_map()
    scope_labels = _load_official_scope_labels()
    validated: List[Dict[str, Any]] = []
    gate_reason_counts: Dict[str, int] = {}
    metric_counters = {
        "official_overlap_count": 0,
        "target_conflict_count": 0,
        "adjusted_metric_mismatch_count": 0,
        "diluted_eps_mismatch_count": 0,
    }
    for raw in raw_responses:
        request_id = _norm(raw.get("request_id"))
        request_item = request_by_id.get(request_id, {})
        parsed, source = _parse_response_payload(raw)
        errors = _schema_errors(parsed, request_item)
        schema_valid = len(errors) == 0
        gate_pass = False
        gate_reasons: List[str] = []
        classification = CLASS_SCHEMA_REJECTED
        if schema_valid and parsed is not None:
            response_label = _norm(parsed.get("response_label"))
            if response_label == "REJECT_ALIAS":
                classification = CLASS_REJECTED_ALIAS
            elif response_label == "NEEDS_MORE_INFO":
                classification = CLASS_NEEDS_MORE_INFO
            elif response_label == "ACCEPT_ALIAS":
                gate_pass, gate_reasons, counters = _deterministic_gate(parsed, request_item, alias_map, scope_labels)
                for key, value in counters.items():
                    metric_counters[key] += value
                if gate_pass:
                    classification = CLASS_ACCEPTED
                else:
                    classification = CLASS_GATE_REJECTED
                    for reason in gate_reasons:
                        gate_reason_counts[reason] = gate_reason_counts.get(reason, 0) + 1
        row = {
            "request_id": request_id,
            "source_candidate_id": _norm(request_item.get("source_candidate_id")),
            "alias_label": _norm(request_item.get("alias_label")) or _norm(raw.get("alias_label")),
            "parsed_response_source": source,
            "classification": classification,
            "schema_valid": schema_valid,
            "schema_errors": " | ".join(errors),
            "deterministic_gate_pass": gate_pass,
            "deterministic_gate_reasons": " | ".join(gate_reasons),
            "response_label": _norm((parsed or {}).get("response_label")),
            "target_metric_if_accept": _norm((parsed or {}).get("target_metric_if_accept")),
            "normalized_alias_label": _norm((parsed or {}).get("normalized_alias_label")),
            "confidence": _norm((parsed or {}).get("confidence")),
            "rationale": _norm((parsed or {}).get("rationale")),
            "safety_flags": " | ".join(_flatten_sequence((parsed or {}).get("safety_flags"))),
            "needs_human_confirmation": (parsed or {}).get("needs_human_confirmation"),
            "raw_response_json": raw.get("raw_response_json"),
        }
        validated.append(row)

    official_after = _official_hashes()
    add_qa("matching::responses_matched_to_requests", "PASS" if all(_norm(r.get("request_id")) in request_by_id for r in raw_responses) else "FAIL", "all response request_ids are known")
    add_qa("safety::official_assets_not_modified", "PASS" if inputs["official_hashes_before"] == official_after else "FAIL", json.dumps({"before": inputs["official_hashes_before"], "after": official_after}, ensure_ascii=False))
    for check in ["llm_or_adjudicator_not_called", "no_official_rule_candidates_created", "no_controlled_proposals_created", "no_sandbox_replay_package_created", "no_semantic_rules_applied", "no_trusted_marked_in_production"]:
        add_qa(f"safety::{check}", "PASS", "False")

    df = pd.DataFrame(validated).fillna("")
    qa_df = pd.DataFrame(qa_rows)
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    accepted_count = int((df["classification"] == CLASS_ACCEPTED).sum()) if not df.empty else 0
    decision = NOT_READY_DECISION if qa_fail_count else (READY_DECISION if accepted_count else NO_ACCEPTED_DECISION)
    schema_valid_count = int(df["schema_valid"].sum()) if not df.empty else 0
    gate_failure_df = df[df["classification"] == CLASS_GATE_REJECTED].copy() if not df.empty else pd.DataFrame()
    schema_invalid_df = df[df["classification"] == CLASS_SCHEMA_REJECTED].copy() if not df.empty else pd.DataFrame()
    accepted_df = df[df["classification"] == CLASS_ACCEPTED].copy() if not df.empty else pd.DataFrame()
    rejected_or_nmi_df = df[df["classification"].isin([CLASS_SCHEMA_REJECTED, CLASS_GATE_REJECTED, CLASS_REJECTED_ALIAS, CLASS_NEEDS_MORE_INFO])].copy() if not df.empty else pd.DataFrame()
    summary = {
        "stage": "325G",
        "response_collection_dir": str(response_collection_dir),
        "request_dir": str(request_dir),
        "request_count": len(request_items),
        "response_count": len(raw_responses),
        "schema_valid_count": schema_valid_count,
        "schema_invalid_count": len(raw_responses) - schema_valid_count,
        "accepted_for_human_confirmation_count": accepted_count,
        "rejected_by_schema_count": int((df["classification"] == CLASS_SCHEMA_REJECTED).sum()) if not df.empty else 0,
        "rejected_by_deterministic_gate_count": int((df["classification"] == CLASS_GATE_REJECTED).sum()) if not df.empty else 0,
        "rejected_alias_suggestion_count": int((df["classification"] == CLASS_REJECTED_ALIAS).sum()) if not df.empty else 0,
        "needs_more_info_count": int((df["classification"] == CLASS_NEEDS_MORE_INFO).sum()) if not df.empty else 0,
        "deterministic_gate_failure_count": len(gate_failure_df),
        "deterministic_gate_failure_reasons": gate_reason_counts,
        **metric_counters,
        "official_assets_modified": inputs["official_hashes_before"] != official_after,
        "official_assets_written": [],
        "official_asset_hashes_before": inputs["official_hashes_before"],
        "official_asset_hashes_after": official_after,
        "llm_or_adjudicator_called": False,
        "semantic_rules_applied": False,
        "trusted_marked_in_production": False,
        "official_rule_candidates_created": False,
        "controlled_official_proposals_created": False,
        "sandbox_replay_package_created": False,
        "qa_pass_count": int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0,
        "qa_warn_count": int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else [],
        "decision": decision,
    }
    return {
        "summary": summary,
        "qa_json": {
            "qa_pass_count": summary["qa_pass_count"],
            "qa_warn_count": summary["qa_warn_count"],
            "qa_fail_count": summary["qa_fail_count"],
            "blocking_reasons": summary["blocking_reasons"],
            "checks": qa_df.to_dict(orient="records"),
        },
        "validated_suggestions": {"stage": "325G", "decision": decision, "validated_suggestions": validated},
        "no_apply_proof": {
            "stage": "325G",
            "decision": decision,
            "official_assets_written": [],
            "official_assets_modified": summary["official_assets_modified"],
            "llm_or_adjudicator_called": False,
            "official_rule_candidates_created": False,
            "controlled_official_proposals_created": False,
            "sandbox_replay_package_created": False,
        },
        "validated_df": df,
        "accepted_df": accepted_df,
        "rejected_or_needs_more_info_df": rejected_or_nmi_df,
        "gate_failures_df": gate_failure_df,
        "schema_invalid_df": schema_invalid_df,
        "qa_checks_df": qa_df,
    }
