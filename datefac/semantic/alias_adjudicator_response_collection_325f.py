from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


EXPECTED_325E_DECISION = "ALIAS_SAFE_ADJUDICATOR_REQUEST_325E_READY_FOR_MANUAL_OR_CONFIGURED_ADJUDICATOR_RUN"
EXPECTED_325F_MANUAL_READY = "ALIAS_ADJUDICATOR_RESPONSE_COLLECTION_325F_MANUAL_TEMPLATE_READY"
EXPECTED_325F_RAW_READY = "ALIAS_ADJUDICATOR_RESPONSE_COLLECTION_325F_RAW_RESPONSE_READY_FOR_325G_SCHEMA_VALIDATION"
EXPECTED_325F_NOT_READY = "ALIAS_ADJUDICATOR_RESPONSE_COLLECTION_325F_NOT_READY"

DEFAULT_REQUEST_DIR = Path(r"D:\_datefac\output\alias_safe_adjudicator_request_325e")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_adjudicator_response_collection_325f")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

ALLOWED_RESPONSE_LABELS = ["ACCEPT_ALIAS", "REJECT_ALIAS", "NEEDS_MORE_INFO"]
REQUIRED_RAW_RESPONSE_FIELDS = [
    "request_id",
    "response_label",
    "target_metric_if_accept",
    "normalized_alias_label",
    "confidence",
    "rationale",
    "safety_flags",
    "needs_human_confirmation",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _exact_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return value if isinstance(value, str) else str(value)


def _safe_int(value: Any) -> int:
    if value in ("", None):
        return 0
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return 0


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _norm(value).lower() in {"true", "1", "yes", "y"}


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_workbook_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name=sheet_name, dtype=object).fillna("")
    except Exception:
        return pd.DataFrame()


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


def _add_qa(rows: List[Dict[str, Any]], name: str, status: str, detail: str) -> None:
    rows.append({"check_name": name, "status": status, "detail": detail})


def load_alias_adjudicator_response_collection_325f_inputs(request_dir: Path) -> Dict[str, Any]:
    request_package = _read_json(request_dir / "alias_safe_adjudicator_request_325e_request_package.json")
    request_items = request_package.get("request_items", []) if isinstance(request_package.get("request_items"), list) else []
    return {
        "summary": _read_json(request_dir / "alias_safe_adjudicator_request_325e_summary.json"),
        "qa": _read_json(request_dir / "alias_safe_adjudicator_request_325e_qa.json"),
        "request_package": request_package,
        "request_items": request_items,
        "schema": _read_json(request_dir / "alias_safe_adjudicator_request_325e_schema.json"),
        "official_hashes_before": _official_hashes(),
    }


def _readiness_qa(inputs: Dict[str, Any], request_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    summary = inputs.get("summary", {})
    qa = inputs.get("qa", {})
    expected = {
        "decision": EXPECTED_325E_DECISION,
        "qa_fail_count": 0,
        "request_count": 6,
        "alias_request_count": 6,
        "excluded_holdout_count": 6,
    }
    for key, value in expected.items():
        actual = summary.get(key)
        ok = _safe_int(actual) == value if isinstance(value, int) else _norm(actual) == value
        _add_qa(rows, f"readiness::325e_{key}", "PASS" if ok else "FAIL", f"expected={value}; actual={actual}")
    _add_qa(rows, "readiness::325e_official_assets_modified", "PASS" if summary.get("official_assets_modified") is False else "FAIL", str(summary.get("official_assets_modified")))
    _add_qa(rows, "readiness::325e_llm_or_adjudicator_called", "PASS" if summary.get("llm_or_adjudicator_called") is False else "FAIL", str(summary.get("llm_or_adjudicator_called")))
    _add_qa(rows, "readiness::325e_qa_json_fail_count", "PASS" if _safe_int(qa.get("qa_fail_count")) == 0 else "FAIL", str(qa.get("qa_fail_count", "")))
    _add_qa(rows, "input::request_items_exact_count", "PASS" if len(request_items) == 6 else "FAIL", f"actual={len(request_items)}")
    return rows


def _manual_template_row(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "request_id": _norm(item.get("request_id")),
        "source_review_id": _norm(item.get("source_review_id")),
        "source_candidate_id": _norm(item.get("source_candidate_id")),
        "candidate_type": _norm(item.get("candidate_type")) or "alias",
        "alias_label": _norm(item.get("alias_label")),
        "proposed_target_metric": _norm(item.get("proposed_target_metric")),
        "allowed_response_labels": " | ".join(ALLOWED_RESPONSE_LABELS),
        "required_raw_response_fields": " | ".join(REQUIRED_RAW_RESPONSE_FIELDS),
        "evidence_summary": _norm(item.get("evidence_summary")),
        "sample_rows": _norm(item.get("sample_rows")),
        "risk_flags": _norm(item.get("risk_flags")),
        "ambiguity_notes": _norm(item.get("ambiguity_notes")),
        "provenance": json.dumps(item.get("provenance", {}), ensure_ascii=False),
        "response_state": "PENDING_RESPONSE",
        "response_received": False,
        "response_label": "",
        "target_metric_if_accept": "",
        "normalized_alias_label": "",
        "confidence": "",
        "rationale": "",
        "safety_flags": "",
        "needs_human_confirmation": "",
        "raw_response_text": "",
        "raw_response_json": "",
        "provider_or_source": "MANUAL_RESPONSE_TEMPLATE",
        "model_or_review_source": "PENDING_MANUAL_RESPONSE",
        "run_timestamp": "",
        "collector_note": "",
    }


def _placeholder_raw_response(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "request_id": _norm(item.get("request_id")),
        "source_review_id": _norm(item.get("source_review_id")),
        "source_candidate_id": _norm(item.get("source_candidate_id")),
        "candidate_type": "alias",
        "alias_label": _norm(item.get("alias_label")),
        "response_state": "PENDING_RESPONSE",
        "response_received": False,
        "raw_response_text": "",
        "raw_response_json": "",
        "provider_or_source": "MANUAL_TEMPLATE",
        "model_or_review_source": "NOT_RUN",
        "run_timestamp": "",
        "collector_note": "",
    }


def _flatten_item_response(item: Dict[str, Any], raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "request_id": _norm(item.get("request_id")),
        "source_review_id": _norm(item.get("source_review_id")),
        "source_candidate_id": _norm(item.get("source_candidate_id")),
        "candidate_type": "alias",
        "alias_label": _norm(item.get("alias_label")),
        "proposed_target_metric": _norm(item.get("proposed_target_metric")),
        "allowed_response_labels": " | ".join(ALLOWED_RESPONSE_LABELS),
        "required_raw_response_fields": " | ".join(REQUIRED_RAW_RESPONSE_FIELDS),
        "response_received": bool(raw.get("response_received")),
        "raw_response_text": _exact_text(raw.get("raw_response_text")),
        "raw_response_json": _exact_text(raw.get("raw_response_json")),
        "provider_or_source": _norm(raw.get("provider_or_source")),
        "model_or_review_source": _norm(raw.get("model_or_review_source")),
        "run_timestamp": _exact_text(raw.get("run_timestamp")),
        "collector_note": _exact_text(raw.get("collector_note")),
    }


def _build_summary(mode: str, request_count: int, raw_response_count: int, received_count: int, qa_df: pd.DataFrame, official_before: Dict[str, str], official_after: Dict[str, str], decision: str) -> Dict[str, Any]:
    return {
        "stage": "325F",
        "mode": mode,
        "request_count": request_count,
        "raw_response_count": raw_response_count,
        "response_received_count": received_count,
        "collect_manual_mode_implemented": True,
        "llm_or_adjudicator_called": False,
        "schema_validation_performed": False,
        "deterministic_gate_performed": False,
        "official_rule_candidates_created": False,
        "controlled_official_proposals_created": False,
        "sandbox_replay_package_created": False,
        "semantic_rules_applied": False,
        "trusted_marked_in_production": False,
        "official_assets_modified": official_before != official_after,
        "official_assets_written": [],
        "official_asset_hashes_before": official_before,
        "official_asset_hashes_after": official_after,
        "qa_pass_count": int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0,
        "qa_warn_count": int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0,
        "qa_fail_count": int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0,
        "blocking_reasons": qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else [],
        "decision": decision,
    }


def build_alias_adjudicator_response_collection_325f_prepare_manual(inputs: Dict[str, Any], request_dir: Path) -> Dict[str, Any]:
    request_items = inputs["request_items"]
    qa_rows = _readiness_qa(inputs, request_items)
    manual_rows = [_manual_template_row(item) for item in request_items]
    raw_responses = [_placeholder_raw_response(item) for item in request_items]
    official_after = _official_hashes()
    _add_qa(qa_rows, "prepare::manual_template_exact_count", "PASS" if len(manual_rows) == 6 else "FAIL", f"actual={len(manual_rows)}")
    _add_qa(qa_rows, "prepare::placeholder_raw_response_exact_count", "PASS" if len(raw_responses) == 6 else "FAIL", f"actual={len(raw_responses)}")
    _add_qa(qa_rows, "safety::official_assets_not_modified", "PASS" if inputs["official_hashes_before"] == official_after else "FAIL", json.dumps({"before": inputs["official_hashes_before"], "after": official_after}, ensure_ascii=False))
    qa_df = pd.DataFrame(qa_rows)
    decision = EXPECTED_325F_MANUAL_READY if int((qa_df["status"] == "FAIL").sum()) == 0 else EXPECTED_325F_NOT_READY
    summary = _build_summary("prepare-manual", len(request_items), len(raw_responses), 0, qa_df, inputs["official_hashes_before"], official_after, decision)
    return _artifacts(summary, request_items, raw_responses, manual_rows, qa_df, request_dir)


def _row_to_raw_response(row: Dict[str, Any]) -> Dict[str, Any]:
    raw_json = _exact_text(row.get("raw_response_json"))
    raw_text = _exact_text(row.get("raw_response_text"))
    if not raw_json:
        raw_payload = {
            field: _exact_text(row.get(field))
            for field in REQUIRED_RAW_RESPONSE_FIELDS
        }
        raw_json = json.dumps(raw_payload, ensure_ascii=False)
    return {
        "request_id": _norm(row.get("request_id")),
        "candidate_type": _norm(row.get("candidate_type")) or "alias",
        "alias_label": _norm(row.get("alias_label")),
        "raw_response_text": raw_text,
        "raw_response_json": raw_json,
        "response_received": _truthy(row.get("response_received")) or bool(raw_json or raw_text),
        "provider_or_source": _norm(row.get("provider_or_source")) or "MANUAL_RESPONSE_WORKBOOK",
        "model_or_review_source": _norm(row.get("model_or_review_source")) or "MANUAL_RESPONSE",
        "run_timestamp": _exact_text(row.get("run_timestamp")),
        "collector_note": _exact_text(row.get("collector_note")),
    }


def build_alias_adjudicator_response_collection_325f_collect_manual(inputs: Dict[str, Any], request_dir: Path, manual_response_workbook: Path) -> Dict[str, Any]:
    request_items = inputs["request_items"]
    qa_rows = _readiness_qa(inputs, request_items)
    df = _read_workbook_sheet(manual_response_workbook, "manual_response_template")
    if df.empty:
        df = _read_workbook_sheet(manual_response_workbook, "request_response_items")
    rows = df.to_dict(orient="records") if not df.empty else []
    request_ids = {_norm(item.get("request_id")) for item in request_items}
    raw_responses = [_row_to_raw_response(row) for row in rows if _norm(row.get("request_id")) in request_ids]
    received_count = sum(1 for row in raw_responses if row.get("response_received"))
    aligned_count = sum(1 for row in raw_responses if _norm(row.get("request_id")) in request_ids)
    payload_count = sum(1 for row in raw_responses if _norm(row.get("raw_response_json")) or _norm(row.get("raw_response_text")))
    official_after = _official_hashes()
    _add_qa(qa_rows, "collect::manual_workbook_loaded", "PASS" if len(rows) >= 6 else "FAIL", f"rows={len(rows)}")
    _add_qa(qa_rows, "collect::raw_response_exact_count", "PASS" if len(raw_responses) == 6 else "FAIL", f"actual={len(raw_responses)}")
    _add_qa(qa_rows, "collect::request_id_alignment", "PASS" if aligned_count == 6 else "FAIL", f"aligned={aligned_count}")
    _add_qa(qa_rows, "collect::payload_presence", "PASS" if payload_count == 6 else "FAIL", f"payload={payload_count}")
    _add_qa(qa_rows, "collect::response_received_exact_count", "PASS" if received_count == 6 else "FAIL", f"received={received_count}")
    _add_qa(qa_rows, "safety::official_assets_not_modified", "PASS" if inputs["official_hashes_before"] == official_after else "FAIL", json.dumps({"before": inputs["official_hashes_before"], "after": official_after}, ensure_ascii=False))
    qa_df = pd.DataFrame(qa_rows)
    decision = EXPECTED_325F_RAW_READY if int((qa_df["status"] == "FAIL").sum()) == 0 and received_count == 6 else EXPECTED_325F_NOT_READY
    manual_rows = [_manual_template_row(item) for item in request_items]
    summary = _build_summary("collect-manual", len(request_items), len(raw_responses), received_count, qa_df, inputs["official_hashes_before"], official_after, decision)
    return _artifacts(summary, request_items, raw_responses, manual_rows, qa_df, request_dir, manual_response_workbook)


def _artifacts(summary: Dict[str, Any], request_items: List[Dict[str, Any]], raw_responses: List[Dict[str, Any]], manual_rows: List[Dict[str, Any]], qa_df: pd.DataFrame, request_dir: Path, manual_workbook: Path | None = None) -> Dict[str, Any]:
    by_id = {_norm(item.get("request_id")): item for item in request_items}
    request_response_rows = [
        _flatten_item_response(by_id.get(_norm(raw.get("request_id")), {}), raw)
        for raw in raw_responses
    ]
    manifest = {
        "stage": "325F",
        "mode": summary["mode"],
        "decision": summary["decision"],
        "request_count": summary["request_count"],
        "raw_response_count": summary["raw_response_count"],
        "response_received_count": summary["response_received_count"],
        "raw_response_required_fields": REQUIRED_RAW_RESPONSE_FIELDS,
        "allowed_response_labels": ALLOWED_RESPONSE_LABELS,
        "raw_responses": raw_responses,
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
        "response_manifest_json": manifest,
        "run_metadata_json": {
            "stage": "325F",
            "mode": summary["mode"],
            "request_dir": str(request_dir),
            "manual_response_workbook": str(manual_workbook) if manual_workbook else "",
            "generated_timestamp": datetime.now().isoformat(timespec="seconds"),
            "llm_or_adjudicator_called": False,
            "schema_validation_performed": False,
            "deterministic_gate_performed": False,
        },
        "no_apply_proof_json": {
            "stage": "325F",
            "decision": summary["decision"],
            "official_assets_written": [],
            "official_assets_modified": summary["official_assets_modified"],
            "llm_or_adjudicator_called": False,
            "official_rule_candidates_created": False,
            "controlled_official_proposals_created": False,
            "sandbox_replay_package_created": False,
        },
        "raw_responses": raw_responses,
        "request_response_df": pd.DataFrame(request_response_rows).fillna(""),
        "manual_template_df": pd.DataFrame(manual_rows).fillna(""),
        "qa_checks_df": qa_df,
    }
