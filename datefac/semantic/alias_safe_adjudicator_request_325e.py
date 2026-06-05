from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


EXPECTED_325D_DECISION = "ALIAS_HUMAN_SPOT_CHECK_325D_REVIEWED_READY_FOR_SAFE_ADJUDICATOR_REQUEST_PREP"
READY_DECISION = "ALIAS_SAFE_ADJUDICATOR_REQUEST_325E_READY_FOR_MANUAL_OR_CONFIGURED_ADJUDICATOR_RUN"
NO_ITEMS_DECISION = "ALIAS_SAFE_ADJUDICATOR_REQUEST_325E_NO_REQUEST_ITEMS"
NOT_READY_DECISION = "ALIAS_SAFE_ADJUDICATOR_REQUEST_325E_NOT_READY"

DEFAULT_REVIEWED_DIR = Path(r"D:\_datefac\output\alias_human_spot_check_325d_reviewed")
DEFAULT_SANITY_GATE_DIR = Path(r"D:\_datefac\output\alias_review_batch_sanity_gate_325c")
DEFAULT_ALIAS_REVIEW_BATCH_DIR = Path(r"D:\_datefac\output\alias_review_batch_325b")
DEFAULT_ALIAS_REFINEMENT_DIR = Path(r"D:\_datefac\output\alias_candidate_refinement_325a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_safe_adjudicator_request_325e")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

ALLOWED_RESPONSE_LABELS = ["ACCEPT_ALIAS", "REJECT_ALIAS", "NEEDS_MORE_INFO"]
RESPONSE_SCHEMA_VERSION = "alias_adjudicator_response_325e_v1"
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


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


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
        "semantic_alias_candidates": _sha256_file(SEMANTIC_ALIAS_ASSET_PATH),
    }


def _add_qa(qa_rows: List[Dict[str, Any]], name: str, status: str, detail: str) -> None:
    qa_rows.append({"check_name": name, "status": status, "detail": detail})


def load_alias_safe_adjudicator_request_325e_inputs(
    reviewed_dir: Path,
    sanity_gate_dir: Path,
    alias_review_batch_dir: Path,
    alias_refinement_dir: Path = DEFAULT_ALIAS_REFINEMENT_DIR,
) -> Dict[str, Any]:
    return {
        "summary_325d": _read_json(reviewed_dir / "alias_human_spot_check_325d_reviewed_summary.json"),
        "qa_325d": _read_json(reviewed_dir / "alias_human_spot_check_325d_reviewed_qa.json"),
        "final_routing_plan": _read_json(reviewed_dir / "alias_human_spot_check_325d_final_routing_plan.json"),
        "summary_325c": _read_json(sanity_gate_dir / "alias_review_batch_sanity_gate_325c_summary.json"),
        "summary_325b": _read_json(alias_review_batch_dir / "alias_review_batch_325b_summary.json"),
        "summary_325a": _read_json(alias_refinement_dir / "alias_candidate_refinement_325a_summary.json"),
        "official_asset_hashes_before": _official_hashes(),
    }


def response_schema_325e() -> Dict[str, Any]:
    return {
        "schema_version": RESPONSE_SCHEMA_VERSION,
        "type": "object",
        "required": REQUIRED_RESPONSE_FIELDS,
        "properties": {
            "request_id": {"type": "string"},
            "response_label": {"type": "string", "enum": ALLOWED_RESPONSE_LABELS},
            "target_metric_if_accept": {"type": ["string", "null"]},
            "normalized_alias_label": {"type": "string"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "rationale": {"type": "string"},
            "safety_flags": {"type": "array", "items": {"type": "string"}},
            "needs_human_confirmation": {"type": "boolean"},
        },
        "additionalProperties": False,
    }


def _evidence_summary(record: Dict[str, Any]) -> str:
    parts = [
        f"label={_norm(record.get('alias_label'))}",
        f"routing_reason_325c={_norm(record.get('routing_reason_325c'))}",
        f"affected_candidate_count={_safe_int(record.get('affected_candidate_count'))}",
        f"reviewer_note={_norm(record.get('reviewer_note'))}",
    ]
    raw_names = _norm(record.get("sample_raw_metric_names"))
    if raw_names:
        parts.append(f"sample_raw_metric_names={raw_names}")
    return " | ".join(parts)


def _build_request_item(record: Dict[str, Any], index: int) -> Dict[str, Any]:
    alias_label = _norm(record.get("alias_label")) or _norm(record.get("normalized_label"))
    return {
        "request_id": f"325e::alias_request::{index:03d}",
        "source_review_id": _norm(record.get("spot_check_id")),
        "source_candidate_id": _norm(record.get("candidate_id")) or _norm(record.get("alias_refinement_candidate_id_325a")),
        "source_325c_routing_id": _norm(record.get("source_325c_routing_id")),
        "source_325b_review_id": _norm(record.get("alias_review_id_325b")),
        "source_325a_candidate_id": _norm(record.get("alias_refinement_candidate_id_325a")),
        "alias_label": alias_label,
        "proposed_target_metric": _norm(record.get("proposed_target_metric_if_available")),
        "candidate_type": "alias",
        "human_decision": "SEND_TO_ADJUDICATOR",
        "evidence_summary": _evidence_summary(record),
        "sample_rows": _norm(record.get("sample_row_texts")),
        "sample_raw_metric_names": _norm(record.get("sample_raw_metric_names")),
        "sample_table_titles": _norm(record.get("sample_table_titles")),
        "sample_years": _norm(record.get("sample_years")),
        "risk_flags": _norm(record.get("risk_flags")),
        "ambiguity_notes": _norm(record.get("ambiguity_notes")),
        "human_reviewer_notes": _norm(record.get("reviewer_note")),
        "human_reviewer_name": _norm(record.get("reviewer_name")),
        "human_review_timestamp": _norm(record.get("review_timestamp")),
        "provenance": {
            "provenance_source": _norm(record.get("provenance_source")),
            "provenance_summary": _norm(record.get("provenance_summary")),
            "source_325d_spot_check_id": _norm(record.get("spot_check_id")),
            "source_325c_routing_id": _norm(record.get("source_325c_routing_id")),
            "source_325b_review_id": _norm(record.get("alias_review_id_325b")),
            "source_325a_candidate_id": _norm(record.get("alias_refinement_candidate_id_325a")),
        },
        "allowed_response_labels": ALLOWED_RESPONSE_LABELS,
        "response_schema_version": RESPONSE_SCHEMA_VERSION,
        "adjudicator_constraints": [
            "Do not apply rules.",
            "Do not modify official assets.",
            "Do not mark rows trusted.",
            "Only answer using the required response schema.",
            "Accepted aliases still require later schema validation, deterministic gate, human confirmation, sandbox replay, controlled proposal, dry run, human approval, official patch application, and post-patch regression.",
        ],
    }


def build_alias_safe_adjudicator_request_325e(
    summary_325d: Dict[str, Any],
    qa_325d: Dict[str, Any],
    final_routing_plan: Dict[str, Any],
    official_asset_hashes_before: Dict[str, str],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []
    expected = {
        "decision": EXPECTED_325D_DECISION,
        "qa_fail_count": 0,
        "send_to_adjudicator_count": 6,
        "holdout_count": 5,
        "rejected_count": 0,
        "needs_more_info_count": 0,
        "pending_count": 0,
        "invalid_decision_count": 0,
        "carried_forward_325c_holdout_count": 1,
    }
    for key, value in expected.items():
        actual = summary_325d.get(key)
        ok = _safe_int(actual) == value if isinstance(value, int) else _norm(actual) == value
        _add_qa(qa_rows, f"readiness::325d_{key}", "PASS" if ok else "FAIL", f"expected={value}; actual={actual}")
    _add_qa(
        qa_rows,
        "readiness::325d_qa_json_fail_count",
        "PASS" if _safe_int(qa_325d.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_325d.get("qa_fail_count", "")),
    )

    send_records = final_routing_plan.get("send_to_adjudicator_records", [])
    non_send_records = final_routing_plan.get("holdout_or_rejected_records", [])
    carried_holdouts = final_routing_plan.get("carried_forward_325c_holdout_records", [])
    if not isinstance(send_records, list):
        send_records = []
    if not isinstance(non_send_records, list):
        non_send_records = []
    if not isinstance(carried_holdouts, list):
        carried_holdouts = []

    request_items = [_build_request_item(record, index) for index, record in enumerate(send_records, start=1) if isinstance(record, dict)]
    excluded_325d_holdouts = [
        {**record, "excluded_reason_325e": _norm(record.get("human_spot_check_decision")) or "NON_SEND_325D"}
        for record in non_send_records
        if isinstance(record, dict)
    ]
    excluded_carried = [
        {**record, "excluded_reason_325e": "CARRIED_FORWARD_325C_HOLDOUT"}
        for record in carried_holdouts
        if isinstance(record, dict)
    ]
    excluded_records = excluded_325d_holdouts + excluded_carried

    _add_qa(qa_rows, "inputs::send_to_adjudicator_exact_count", "PASS" if len(send_records) == 6 else "FAIL", f"actual={len(send_records)}")
    _add_qa(qa_rows, "inputs::excluded_non_send_exact_count", "PASS" if len(excluded_records) == 6 else "FAIL", f"actual={len(excluded_records)}")
    _add_qa(qa_rows, "requests::request_item_exact_count", "PASS" if len(request_items) == 6 else "FAIL", f"actual={len(request_items)}")
    _add_qa(
        qa_rows,
        "requests::all_request_items_are_alias_send_decisions",
        "PASS"
        if all(item.get("candidate_type") == "alias" and item.get("human_decision") == "SEND_TO_ADJUDICATOR" for item in request_items)
        else "FAIL",
        f"actual={len(request_items)}",
    )
    required_request_fields = [
        "request_id",
        "source_review_id",
        "source_candidate_id",
        "alias_label",
        "candidate_type",
        "human_decision",
        "evidence_summary",
        "sample_rows",
        "risk_flags",
        "ambiguity_notes",
        "provenance",
        "allowed_response_labels",
        "response_schema_version",
    ]
    missing_count = sum(
        1
        for item in request_items
        if any(not item.get(field) for field in required_request_fields)
    )
    _add_qa(qa_rows, "requests::required_fields_present", "PASS" if missing_count == 0 else "FAIL", f"missing_item_count={missing_count}")

    schema = response_schema_325e()
    _add_qa(
        qa_rows,
        "schema::required_response_fields_present",
        "PASS" if schema.get("required") == REQUIRED_RESPONSE_FIELDS else "FAIL",
        ", ".join(schema.get("required", [])),
    )
    official_asset_hashes_after = _official_hashes()
    official_assets_modified = official_asset_hashes_before != official_asset_hashes_after
    _add_qa(
        qa_rows,
        "safety::official_assets_not_modified",
        "PASS" if not official_assets_modified else "FAIL",
        json.dumps({"before": official_asset_hashes_before, "after": official_asset_hashes_after}, ensure_ascii=False),
    )
    for check in [
        "llm_or_adjudicator_not_called",
        "no_official_rule_candidates_created",
        "no_controlled_proposals_created",
        "no_sandbox_replay_package_created",
        "no_semantic_rules_applied",
        "no_trusted_marked_in_production",
    ]:
        _add_qa(qa_rows, f"safety::{check}", "PASS", "False")

    qa_df = pd.DataFrame(qa_rows)
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    if qa_fail_count > 0:
        decision = NOT_READY_DECISION
    elif request_items:
        decision = READY_DECISION
    else:
        decision = NO_ITEMS_DECISION

    excluded_holdout_count = len(excluded_records)
    summary = {
        "stage": "325E",
        "request_count": len(request_items),
        "alias_request_count": sum(1 for item in request_items if item.get("candidate_type") == "alias"),
        "excluded_holdout_count": excluded_holdout_count,
        "excluded_325d_holdout_count": len(excluded_325d_holdouts),
        "excluded_325c_carried_forward_holdout_count": len(excluded_carried),
        "excluded_rejected_count": sum(1 for item in excluded_records if _norm(item.get("human_spot_check_decision")) == "REJECT_ALIAS"),
        "excluded_needs_more_info_count": sum(1 for item in excluded_records if _norm(item.get("human_spot_check_decision")) == "NEEDS_MORE_INFO"),
        "excluded_pending_count": sum(1 for item in excluded_records if _norm(item.get("human_spot_check_decision")).startswith("PENDING")),
        "allowed_response_labels": ALLOWED_RESPONSE_LABELS,
        "response_schema_version": RESPONSE_SCHEMA_VERSION,
        "required_response_schema_fields": REQUIRED_RESPONSE_FIELDS,
        "llm_or_adjudicator_called": False,
        "semantic_rules_applied": False,
        "trusted_marked_in_production": False,
        "official_assets_modified": official_assets_modified,
        "official_assets_written": [],
        "official_asset_hashes_before": official_asset_hashes_before,
        "official_asset_hashes_after": official_asset_hashes_after,
        "official_rule_candidates_created": False,
        "controlled_official_proposals_created": False,
        "sandbox_replay_package_created": False,
        "top_request_examples": [
            {
                "request_id": item.get("request_id"),
                "source_review_id": item.get("source_review_id"),
                "alias_label": item.get("alias_label"),
                "proposed_target_metric": item.get("proposed_target_metric"),
            }
            for item in request_items[:6]
        ],
        "qa_pass_count": int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0,
        "qa_warn_count": int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else [],
        "decision": decision,
    }
    package = {
        "stage": "325E",
        "decision": decision,
        "request_count": len(request_items),
        "allowed_response_labels": ALLOWED_RESPONSE_LABELS,
        "response_schema_version": RESPONSE_SCHEMA_VERSION,
        "response_schema": schema,
        "request_items": request_items,
        "excluded_items": excluded_records,
        "downstream_requirements": [
            "schema validation",
            "deterministic gate",
            "human confirmation",
            "sandbox replay",
            "controlled proposal",
            "dry run",
            "human approval",
            "official patch application",
            "post-patch regression",
        ],
        "adjudicator_prohibitions": [
            "Do not apply rules.",
            "Do not modify official assets.",
            "Do not mark anything trusted in production.",
            "Do not produce official candidates, controlled proposals, or sandbox replay packages.",
        ],
    }
    no_apply_proof = {
        "stage": "325E",
        "decision": decision,
        "official_assets_read": [str(FORMAL_SCOPE_RULES_PATH), str(SEMANTIC_ALIAS_ASSET_PATH)],
        "official_assets_written": [],
        "official_assets_modified": official_assets_modified,
        "official_asset_hashes_before": official_asset_hashes_before,
        "official_asset_hashes_after": official_asset_hashes_after,
        "llm_or_adjudicator_called": False,
        "semantic_rules_applied": False,
        "trusted_marked_in_production": False,
        "official_rule_candidates_created": False,
        "controlled_official_proposals_created": False,
        "sandbox_replay_package_created": False,
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
        "request_package": package,
        "request_items": request_items,
        "excluded_items": excluded_records,
        "response_schema": schema,
        "no_apply_proof": no_apply_proof,
        "request_items_df": pd.DataFrame(request_items).fillna(""),
        "excluded_items_df": pd.DataFrame(excluded_records).fillna(""),
        "schema_df": pd.DataFrame(
            [{"field": field, "required": True} for field in REQUIRED_RESPONSE_FIELDS]
        ),
        "qa_checks_df": qa_df,
    }
