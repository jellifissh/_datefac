from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


EXPECTED_325G_DECISION = "ALIAS_RESPONSE_SCHEMA_VALIDATION_325G_READY_FOR_HUMAN_CONFIRMATION"
PREPARE_READY_DECISION = "ALIAS_HUMAN_CONFIRMATION_325H_READY_FOR_HUMAN_REVIEW"
REVIEWED_READY_DECISION = "ALIAS_HUMAN_CONFIRMATION_325H_REVIEWED_READY_FOR_325I_SANDBOX_REPLAY"
REVIEWED_NO_CONFIRMED_DECISION = "ALIAS_HUMAN_CONFIRMATION_325H_REVIEWED_NO_CONFIRMED_ALIAS_SUGGESTIONS"
REVIEWED_NOT_READY_DECISION = "ALIAS_HUMAN_CONFIRMATION_325H_REVIEWED_NOT_READY"
NOT_READY_DECISION = "ALIAS_HUMAN_CONFIRMATION_325H_NOT_READY"

DEFAULT_SCHEMA_VALIDATION_DIR = Path(r"D:\_datefac\output\alias_response_schema_validation_325g")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_human_confirmation_325h")
DEFAULT_REVIEWED_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_human_confirmation_325h_reviewed")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

CLASS_ACCEPTED = "ACCEPTED_FOR_HUMAN_CONFIRMATION"
PENDING_DECISION = "PENDING_HUMAN_CONFIRMATION"
ALLOWED_DECISIONS = ["CONFIRM", "REJECT", "NEEDS_MORE_INFO"]


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


def _read_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
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


def load_alias_human_confirmation_325h_inputs(schema_validation_dir: Path) -> Dict[str, Any]:
    suggestions = _read_json(schema_validation_dir / "alias_response_schema_validation_325g_validated_suggestions.json")
    return {
        "summary_325g": _read_json(schema_validation_dir / "alias_response_schema_validation_325g_summary.json"),
        "qa_325g": _read_json(schema_validation_dir / "alias_response_schema_validation_325g_qa.json"),
        "validated_suggestions": suggestions.get("validated_suggestions", []) if isinstance(suggestions.get("validated_suggestions"), list) else [],
        "official_hashes_before": _official_hashes(),
    }


def _readiness_qa(summary: Dict[str, Any], qa: Dict[str, Any], suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    expected = {
        "decision": EXPECTED_325G_DECISION,
        "qa_fail_count": 0,
        "request_count": 6,
        "response_count": 6,
        "schema_valid_count": 6,
        "schema_invalid_count": 0,
        "accepted_for_human_confirmation_count": 6,
        "rejected_by_schema_count": 0,
        "rejected_by_deterministic_gate_count": 0,
        "rejected_alias_suggestion_count": 0,
        "needs_more_info_count": 0,
        "official_overlap_count": 0,
        "target_conflict_count": 0,
        "adjusted_metric_mismatch_count": 0,
        "diluted_eps_mismatch_count": 0,
    }
    for key, value in expected.items():
        actual = summary.get(key)
        ok = _safe_int(actual) == value if isinstance(value, int) else _norm(actual) == value
        _add_qa(rows, f"readiness::325g_{key}", "PASS" if ok else "FAIL", f"expected={value}; actual={actual}")
    _add_qa(rows, "readiness::325g_official_assets_modified", "PASS" if summary.get("official_assets_modified") is False else "FAIL", str(summary.get("official_assets_modified")))
    _add_qa(rows, "readiness::325g_qa_json_fail_count", "PASS" if _safe_int(qa.get("qa_fail_count")) == 0 else "FAIL", str(qa.get("qa_fail_count", "")))
    accepted = [item for item in suggestions if _norm(item.get("classification")) == CLASS_ACCEPTED]
    _add_qa(rows, "input::accepted_suggestion_exact_count", "PASS" if len(accepted) == 6 else "FAIL", f"actual={len(accepted)}")
    return rows


def _confirmation_record(item: Dict[str, Any], index: int) -> Dict[str, Any]:
    return {
        "confirmation_id": f"325h::alias_confirmation::{index:03d}",
        "request_id": _norm(item.get("request_id")),
        "source_candidate_id": _norm(item.get("source_candidate_id")),
        "alias_label": _norm(item.get("alias_label")),
        "normalized_alias_label": _norm(item.get("normalized_alias_label")),
        "target_metric": _norm(item.get("target_metric_if_accept")),
        "confidence": _norm(item.get("confidence")),
        "rationale": _norm(item.get("rationale")),
        "deterministic_gate_result": "PASS" if item.get("deterministic_gate_pass") is True else "FAIL",
        "risk_flags": _norm(item.get("safety_flags")),
        "evidence": _norm(item.get("raw_response_json")),
        "provenance": json.dumps(
            {
                "source_request_id": _norm(item.get("request_id")),
                "source_candidate_id": _norm(item.get("source_candidate_id")),
                "source_stage": "325G",
            },
            ensure_ascii=False,
        ),
        "warning_notes": "Confirmation does not apply official rules; confirmed suggestions must go through 325I sandbox replay next.",
        "human_confirmation_decision": PENDING_DECISION,
        "allowed_human_decisions": " | ".join(ALLOWED_DECISIONS),
        "reviewer_note": "",
        "reviewer_name": "",
        "review_timestamp": "",
    }


def _summary(mode: str, records_df: pd.DataFrame, qa_df: pd.DataFrame, official_before: Dict[str, str], official_after: Dict[str, str], decision: str, invalid_decision_count: int = 0) -> Dict[str, Any]:
    decision_col = "human_confirmation_decision"
    return {
        "stage": "325H",
        "mode": mode,
        "confirmation_record_count": len(records_df),
        "pending_count": int((records_df[decision_col] == PENDING_DECISION).sum()) if decision_col in records_df else 0,
        "confirmed_count": int((records_df[decision_col] == "CONFIRM").sum()) if decision_col in records_df else 0,
        "rejected_count": int((records_df[decision_col] == "REJECT").sum()) if decision_col in records_df else 0,
        "needs_more_info_count": int((records_df[decision_col] == "NEEDS_MORE_INFO").sum()) if decision_col in records_df else 0,
        "invalid_decision_count": invalid_decision_count,
        "validate_reviewed_mode_implemented": True,
        "official_assets_modified": official_before != official_after,
        "official_assets_written": [],
        "official_asset_hashes_before": official_before,
        "official_asset_hashes_after": official_after,
        "llm_or_adjudicator_called": False,
        "semantic_rules_applied": False,
        "trusted_marked_in_production": False,
        "official_rule_candidates_created": False,
        "controlled_official_proposals_created": False,
        "sandbox_replay_package_created": False,
        "top_confirmation_examples": records_df[["confirmation_id", "alias_label", "target_metric", decision_col]].head(6).to_dict(orient="records") if not records_df.empty else [],
        "qa_pass_count": int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0,
        "qa_warn_count": int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0,
        "qa_fail_count": int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0,
        "blocking_reasons": qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else [],
        "decision": decision,
    }


def build_alias_human_confirmation_325h_prepare(inputs: Dict[str, Any]) -> Dict[str, Any]:
    suggestions = [item for item in inputs["validated_suggestions"] if _norm(item.get("classification")) == CLASS_ACCEPTED]
    qa_rows = _readiness_qa(inputs["summary_325g"], inputs["qa_325g"], inputs["validated_suggestions"])
    records = [_confirmation_record(item, index) for index, item in enumerate(suggestions, start=1)]
    records_df = pd.DataFrame(records).fillna("")
    official_after = _official_hashes()
    _add_qa(qa_rows, "prepare::confirmation_record_exact_count", "PASS" if len(records) == 6 else "FAIL", f"actual={len(records)}")
    _add_qa(qa_rows, "prepare::all_pending", "PASS" if int((records_df["human_confirmation_decision"] == PENDING_DECISION).sum()) == 6 else "FAIL", "pending check")
    _add_qa(qa_rows, "safety::official_assets_not_modified", "PASS" if inputs["official_hashes_before"] == official_after else "FAIL", "hash comparison")
    for check in ["llm_or_adjudicator_not_called", "no_official_rule_candidates_created", "no_controlled_proposals_created", "no_sandbox_replay_package_created"]:
        _add_qa(qa_rows, f"safety::{check}", "PASS", "False")
    qa_df = pd.DataFrame(qa_rows)
    decision = PREPARE_READY_DECISION if int((qa_df["status"] == "FAIL").sum()) == 0 else NOT_READY_DECISION
    summary = _summary("prepare", records_df, qa_df, inputs["official_hashes_before"], official_after, decision)
    return _artifacts(summary, records_df, pd.DataFrame(), qa_df)


def load_reviewed_confirmation_records(workbook: Path) -> List[Dict[str, Any]]:
    df = _read_excel_sheet(workbook, "confirmation_records")
    return df.to_dict(orient="records") if not df.empty else []


def build_alias_human_confirmation_325h_reviewed(inputs: Dict[str, Any], reviewed_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    qa_rows = _readiness_qa(inputs["summary_325g"], inputs["qa_325g"], inputs["validated_suggestions"])
    records_df = pd.DataFrame(reviewed_records).fillna("")
    if "human_confirmation_decision" not in records_df:
        records_df["human_confirmation_decision"] = ""
    records_df["human_confirmation_decision"] = records_df["human_confirmation_decision"].astype(str).str.strip()
    invalid_count = int((~records_df["human_confirmation_decision"].isin([PENDING_DECISION, *ALLOWED_DECISIONS])).sum()) if not records_df.empty else 0
    pending_count = int((records_df["human_confirmation_decision"] == PENDING_DECISION).sum()) if not records_df.empty else 0
    official_after = _official_hashes()
    _add_qa(qa_rows, "reviewed::confirmation_record_exact_count", "PASS" if len(records_df) == 6 else "FAIL", f"actual={len(records_df)}")
    _add_qa(qa_rows, "reviewed::all_decisions_allowed", "PASS" if invalid_count == 0 else "FAIL", f"invalid={invalid_count}")
    _add_qa(qa_rows, "reviewed::no_pending_decisions", "PASS" if pending_count == 0 else "FAIL", f"pending={pending_count}")
    _add_qa(qa_rows, "safety::official_assets_not_modified", "PASS" if inputs["official_hashes_before"] == official_after else "FAIL", "hash comparison")
    for check in ["llm_or_adjudicator_not_called", "no_official_rule_candidates_created", "no_controlled_proposals_created", "no_sandbox_replay_package_created"]:
        _add_qa(qa_rows, f"safety::{check}", "PASS", "False")
    qa_df = pd.DataFrame(qa_rows)
    confirmed_count = int((records_df["human_confirmation_decision"] == "CONFIRM").sum()) if not records_df.empty else 0
    if int((qa_df["status"] == "FAIL").sum()) > 0:
        decision = REVIEWED_NOT_READY_DECISION
    elif confirmed_count > 0:
        decision = REVIEWED_READY_DECISION
    else:
        decision = REVIEWED_NO_CONFIRMED_DECISION
    rejected_df = records_df[records_df["human_confirmation_decision"].isin(["REJECT", "NEEDS_MORE_INFO"])].copy() if not records_df.empty else pd.DataFrame()
    summary = _summary("validate-reviewed", records_df, qa_df, inputs["official_hashes_before"], official_after, decision, invalid_count)
    return _artifacts(summary, records_df, rejected_df, qa_df)


def _artifacts(summary: Dict[str, Any], records_df: pd.DataFrame, rejected_df: pd.DataFrame, qa_df: pd.DataFrame) -> Dict[str, Any]:
    confirmed_df = records_df[records_df["human_confirmation_decision"] == "CONFIRM"].copy() if "human_confirmation_decision" in records_df else pd.DataFrame()
    return {
        "summary": summary,
        "qa_json": {
            "qa_pass_count": summary["qa_pass_count"],
            "qa_warn_count": summary["qa_warn_count"],
            "qa_fail_count": summary["qa_fail_count"],
            "blocking_reasons": summary["blocking_reasons"],
            "checks": qa_df.to_dict(orient="records"),
        },
        "package": {
            "stage": "325H",
            "mode": summary["mode"],
            "decision": summary["decision"],
            "confirmation_records": records_df.to_dict(orient="records"),
            "confirmed_records": confirmed_df.to_dict(orient="records"),
        },
        "no_apply_proof": {
            "stage": "325H",
            "decision": summary["decision"],
            "official_assets_written": [],
            "official_assets_modified": summary["official_assets_modified"],
            "llm_or_adjudicator_called": False,
            "official_rule_candidates_created": False,
            "controlled_official_proposals_created": False,
            "sandbox_replay_package_created": False,
        },
        "records_df": records_df,
        "confirmed_df": confirmed_df,
        "rejected_df": rejected_df,
        "qa_checks_df": qa_df,
    }
