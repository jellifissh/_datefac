from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


EXPECTED_325C_DECISION = "ALIAS_REVIEW_BATCH_SANITY_GATE_325C_READY_FOR_HUMAN_SPOT_CHECK_OR_SAFE_ADJUDICATOR_SUBSET"
PREPARE_READY_DECISION = "ALIAS_HUMAN_SPOT_CHECK_325D_READY_FOR_HUMAN_REVIEW"
REVIEWED_READY_DECISION = "ALIAS_HUMAN_SPOT_CHECK_325D_REVIEWED_READY_FOR_SAFE_ADJUDICATOR_REQUEST_PREP"
REVIEWED_NO_SAFE_DECISION = "ALIAS_HUMAN_SPOT_CHECK_325D_REVIEWED_NO_SAFE_ADJUDICATOR_ITEMS"
REVIEWED_NOT_READY_DECISION = "ALIAS_HUMAN_SPOT_CHECK_325D_REVIEWED_NOT_READY"
NOT_READY_DECISION = "ALIAS_HUMAN_SPOT_CHECK_325D_NOT_READY"

DEFAULT_SANITY_GATE_DIR = Path(r"D:\_datefac\output\alias_review_batch_sanity_gate_325c")
DEFAULT_ALIAS_REVIEW_BATCH_DIR = Path(r"D:\_datefac\output\alias_review_batch_325b")
DEFAULT_ALIAS_REFINEMENT_DIR = Path(r"D:\_datefac\output\alias_candidate_refinement_325a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_human_spot_check_325d")
DEFAULT_REVIEWED_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_human_spot_check_325d_reviewed")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

ROUTING_HUMAN = "HUMAN_SPOT_CHECK_FIRST"
DEFAULT_DECISION = "PENDING_HUMAN_SPOT_CHECK"
ALLOWED_DECISIONS = ["SEND_TO_ADJUDICATOR", "HOLDOUT", "REJECT_ALIAS", "NEEDS_MORE_INFO"]
REVIEWED_ALLOWED_WITH_PENDING = [DEFAULT_DECISION, *ALLOWED_DECISIONS]

DEFINITION_SENSITIVE_PATTERN = re.compile(r"(?:\bP\s*/\s*E\b|\bP\s*/\s*B\b|\bPE\b|\bPB\b|\bEBIT\b|\bEBITDA\b|市盈率|市净率)", re.IGNORECASE)
DEFINITION_WARNING = (
    "PE/PB/P/E/P/B/EBIT/EBITDA style aliases are definition-sensitive and must not be auto-promoted; "
    "send onward only when target metric and evidence are explicit."
)


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
        return pd.read_excel(path, sheet_name=sheet_name).fillna("")
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


def _load_routing_records(sanity_gate_dir: Path) -> List[Dict[str, Any]]:
    manifest = _read_json(sanity_gate_dir / "alias_review_batch_sanity_gate_325c_routing_manifest.json")
    records = manifest.get("routing_records", [])
    if isinstance(records, list) and records:
        return [record for record in records if isinstance(record, dict)]
    df = _read_excel_sheet(sanity_gate_dir / "alias_review_batch_sanity_gate_325c_routing_manifest.xlsx", "routing_manifest")
    return df.to_dict(orient="records") if not df.empty else []


def load_alias_human_spot_check_325d_inputs(
    sanity_gate_dir: Path,
    alias_review_batch_dir: Path,
    alias_refinement_dir: Path = DEFAULT_ALIAS_REFINEMENT_DIR,
) -> Dict[str, Any]:
    return {
        "summary_325c": _read_json(sanity_gate_dir / "alias_review_batch_sanity_gate_325c_summary.json"),
        "qa_325c": _read_json(sanity_gate_dir / "alias_review_batch_sanity_gate_325c_qa.json"),
        "routing_records": _load_routing_records(sanity_gate_dir),
        "summary_325b": _read_json(alias_review_batch_dir / "alias_review_batch_325b_summary.json"),
        "summary_325a": _read_json(alias_refinement_dir / "alias_candidate_refinement_325a_summary.json"),
        "official_asset_hashes_before": {
            "formal_scope_rules": _sha256_file(FORMAL_SCOPE_RULES_PATH),
            "semantic_alias_candidates": _sha256_file(SEMANTIC_ALIAS_ASSET_PATH),
        },
    }


def _add_qa(qa_rows: List[Dict[str, Any]], name: str, status: str, detail: str) -> None:
    qa_rows.append({"check_name": name, "status": status, "detail": detail})


def _readiness_qa(summary_325c: Dict[str, Any], qa_325c: Dict[str, Any], routing_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    qa_rows: List[Dict[str, Any]] = []
    expected = {
        "decision": EXPECTED_325C_DECISION,
        "qa_fail_count": 0,
        "input_review_record_count": 12,
        "human_spot_check_count": 11,
        "send_to_adjudicator_count": 0,
        "holdout_count": 1,
    }
    for key, value in expected.items():
        actual = summary_325c.get(key)
        ok = _safe_int(actual) == value if isinstance(value, int) else _norm(actual) == value
        _add_qa(qa_rows, f"readiness::325c_{key}", "PASS" if ok else "FAIL", f"expected={value}; actual={actual}")
    _add_qa(
        qa_rows,
        "readiness::325c_qa_json_fail_count",
        "PASS" if _safe_int(qa_325c.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_325c.get("qa_fail_count", "")),
    )
    _add_qa(
        qa_rows,
        "input::routing_manifest_loaded_exact_count",
        "PASS" if len(routing_records) == 12 else "FAIL",
        f"actual={len(routing_records)}",
    )
    return qa_rows


def _build_spot_check_record(record: Dict[str, Any], index: int) -> Dict[str, Any]:
    label = _norm(record.get("normalized_label"))
    definition_sensitive = bool(DEFINITION_SENSITIVE_PATTERN.search(label))
    warning = DEFINITION_WARNING if definition_sensitive else "No PE/PB/P/E/P/B/EBIT/EBITDA warning beyond standard alias spot-check."
    return {
        "spot_check_id": f"325d::spot_check::{index:03d}",
        "source_325c_routing_id": _norm(record.get("routing_id")),
        "alias_review_id_325b": _norm(record.get("alias_review_id")),
        "alias_refinement_candidate_id_325a": _norm(record.get("alias_refinement_candidate_id")),
        "candidate_id": _norm(record.get("candidate_id")),
        "candidate_type": _norm(record.get("candidate_type")) or "alias",
        "alias_label": label,
        "normalized_label": label,
        "proposed_target_metric_if_available": _norm(record.get("proposed_target_metric_if_available")),
        "human_spot_check_decision": DEFAULT_DECISION,
        "allowed_human_decisions": " | ".join(ALLOWED_DECISIONS),
        "reviewer_note": "",
        "reviewer_name": "",
        "review_timestamp": "",
        "risk_flags": _norm(record.get("risk_bucket_reasons")) or _norm(record.get("routing_reasons")),
        "ambiguity_notes": warning,
        "definition_sensitive_alias_warning_present": definition_sensitive,
        "routing_bucket_325c": _norm(record.get("routing_bucket")),
        "routing_reason_325c": _norm(record.get("routing_reasons")),
        "price_or_ratio_ambiguity_325c": record.get("price_or_ratio_ambiguity", False),
        "target_ambiguity_325c": record.get("target_ambiguity", False),
        "sample_candidate_ids": _norm(record.get("sample_candidate_ids")),
        "sample_raw_metric_names": _norm(record.get("sample_raw_metric_names")),
        "sample_row_texts": _norm(record.get("sample_row_texts")),
        "sample_table_titles": _norm(record.get("sample_table_titles")),
        "sample_years": _norm(record.get("sample_years")),
        "affected_candidate_count": _safe_int(record.get("affected_candidate_count")),
        "affected_review_required_count": _safe_int(record.get("affected_review_required_count")),
        "priority_score": record.get("priority_score", ""),
        "provenance_source": _norm(record.get("provenance_source")),
        "provenance_summary": _norm(record.get("provenance_summary")),
        "review_instruction": (
            "Human spot-check only. Choose SEND_TO_ADJUDICATOR only if the alias and target metric are explicit, "
            "evidence is sufficient, and no definition-sensitive ambiguity remains."
        ),
    }


def _official_hashes_after() -> Dict[str, str]:
    return {
        "formal_scope_rules": _sha256_file(FORMAL_SCOPE_RULES_PATH),
        "semantic_alias_candidates": _sha256_file(SEMANTIC_ALIAS_ASSET_PATH),
    }


def build_alias_human_spot_check_325d_prepare(
    summary_325c: Dict[str, Any],
    qa_325c: Dict[str, Any],
    routing_records: List[Dict[str, Any]],
    official_asset_hashes_before: Dict[str, str],
) -> Dict[str, Any]:
    qa_rows = _readiness_qa(summary_325c, qa_325c, routing_records)
    human_records = [record for record in routing_records if _norm(record.get("routing_bucket")) == ROUTING_HUMAN]
    holdout_records = [record for record in routing_records if _norm(record.get("routing_bucket")).startswith("HOLDOUT")]
    spot_check_records = [_build_spot_check_record(record, index) for index, record in enumerate(human_records, start=1)]
    spot_df = pd.DataFrame(spot_check_records).fillna("")
    holdout_df = pd.DataFrame(holdout_records).fillna("")

    _add_qa(qa_rows, "prepare::loaded_human_spot_check_exact_count", "PASS" if len(human_records) == 11 else "FAIL", f"actual={len(human_records)}")
    _add_qa(qa_rows, "prepare::carried_forward_holdout_exact_count", "PASS" if len(holdout_records) == 1 else "FAIL", f"actual={len(holdout_records)}")
    _add_qa(qa_rows, "prepare::spot_check_record_exact_count", "PASS" if len(spot_check_records) == 11 else "FAIL", f"actual={len(spot_check_records)}")
    pending_count = int((spot_df["human_spot_check_decision"] == DEFAULT_DECISION).sum()) if not spot_df.empty else 0
    _add_qa(qa_rows, "prepare::all_records_pending", "PASS" if pending_count == 11 else "FAIL", f"pending={pending_count}")
    official_asset_hashes_after = _official_hashes_after()
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
    ]:
        _add_qa(qa_rows, f"safety::{check}", "PASS", "False")

    qa_df = pd.DataFrame(qa_rows)
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    decision = PREPARE_READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION
    summary = {
        "stage": "325D",
        "mode": "prepare",
        "spot_check_record_count": len(spot_check_records),
        "pending_count": pending_count,
        "send_to_adjudicator_count": 0,
        "holdout_count": 0,
        "rejected_count": 0,
        "needs_more_info_count": 0,
        "invalid_decision_count": 0,
        "carried_forward_325c_holdout_count": len(holdout_records),
        "validate_reviewed_mode_implemented": True,
        "official_assets_modified": official_assets_modified,
        "official_assets_written": [],
        "official_asset_hashes_before": official_asset_hashes_before,
        "official_asset_hashes_after": official_asset_hashes_after,
        "llm_or_adjudicator_called": False,
        "semantic_rules_applied": False,
        "trusted_marked_in_production": False,
        "official_rule_candidates_created": False,
        "controlled_official_proposals_created": False,
        "sandbox_replay_package_created": False,
        "top_spot_check_examples": spot_df[["spot_check_id", "alias_label", "human_spot_check_decision", "routing_reason_325c"]].head(8).to_dict(orient="records") if not spot_df.empty else [],
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
        "review_package": {
            "stage": "325D",
            "mode": "prepare",
            "decision": decision,
            "allowed_human_decisions": ALLOWED_DECISIONS,
            "spot_check_records": spot_check_records,
            "carried_forward_325c_holdout_records": holdout_records,
        },
        "no_apply_proof": {
            "stage": "325D",
            "mode": "prepare",
            "decision": decision,
            "official_assets_read": [str(FORMAL_SCOPE_RULES_PATH), str(SEMANTIC_ALIAS_ASSET_PATH)],
            "official_assets_written": [],
            "official_assets_modified": official_assets_modified,
            "official_asset_hashes_before": official_asset_hashes_before,
            "official_asset_hashes_after": official_asset_hashes_after,
            "llm_or_adjudicator_called": False,
            "official_rule_candidates_created": False,
            "controlled_official_proposals_created": False,
            "sandbox_replay_package_created": False,
        },
        "spot_check_df": spot_df,
        "holdout_df": holdout_df,
        "qa_checks_df": qa_df,
    }


def _load_reviewed_spot_check_records(reviewed_workbook: Path) -> List[Dict[str, Any]]:
    df = _read_excel_sheet(reviewed_workbook, "spot_check_records")
    if df.empty:
        df = _read_excel_sheet(reviewed_workbook, "human_spot_check")
    return df.to_dict(orient="records") if not df.empty else []


def build_alias_human_spot_check_325d_reviewed(
    summary_325c: Dict[str, Any],
    qa_325c: Dict[str, Any],
    routing_records: List[Dict[str, Any]],
    reviewed_records: List[Dict[str, Any]],
    official_asset_hashes_before: Dict[str, str],
) -> Dict[str, Any]:
    qa_rows = _readiness_qa(summary_325c, qa_325c, routing_records)
    holdout_records = [record for record in routing_records if _norm(record.get("routing_bucket")).startswith("HOLDOUT")]
    reviewed_df = pd.DataFrame(reviewed_records).fillna("")
    if "human_spot_check_decision" not in reviewed_df.columns:
        reviewed_df["human_spot_check_decision"] = ""
    reviewed_df["human_spot_check_decision"] = reviewed_df["human_spot_check_decision"].astype(str).str.strip()

    _add_qa(qa_rows, "reviewed::spot_check_record_exact_count", "PASS" if len(reviewed_df) == 11 else "FAIL", f"actual={len(reviewed_df)}")
    invalid_mask = ~reviewed_df["human_spot_check_decision"].isin(REVIEWED_ALLOWED_WITH_PENDING) if not reviewed_df.empty else pd.Series(dtype=bool)
    invalid_decision_count = int(invalid_mask.sum()) if not reviewed_df.empty else 0
    pending_count = int((reviewed_df["human_spot_check_decision"] == DEFAULT_DECISION).sum()) if not reviewed_df.empty else 0
    blank_decision_count = int((reviewed_df["human_spot_check_decision"] == "").sum()) if not reviewed_df.empty else 0
    _add_qa(qa_rows, "reviewed::all_decisions_allowed", "PASS" if invalid_decision_count == 0 and blank_decision_count == 0 else "FAIL", f"invalid={invalid_decision_count}; blank={blank_decision_count}")
    _add_qa(qa_rows, "reviewed::no_pending_decisions", "PASS" if pending_count == 0 else "FAIL", f"pending={pending_count}")
    _add_qa(qa_rows, "reviewed::carried_forward_holdout_exact_count", "PASS" if len(holdout_records) == 1 else "FAIL", f"actual={len(holdout_records)}")

    send_df = reviewed_df[reviewed_df["human_spot_check_decision"] == "SEND_TO_ADJUDICATOR"].copy() if not reviewed_df.empty else pd.DataFrame()
    non_send_df = reviewed_df[reviewed_df["human_spot_check_decision"].isin(["HOLDOUT", "REJECT_ALIAS", "NEEDS_MORE_INFO"])].copy() if not reviewed_df.empty else pd.DataFrame()
    holdout_df = reviewed_df[reviewed_df["human_spot_check_decision"] == "HOLDOUT"].copy() if not reviewed_df.empty else pd.DataFrame()
    rejected_df = reviewed_df[reviewed_df["human_spot_check_decision"] == "REJECT_ALIAS"].copy() if not reviewed_df.empty else pd.DataFrame()
    needs_more_info_df = reviewed_df[reviewed_df["human_spot_check_decision"] == "NEEDS_MORE_INFO"].copy() if not reviewed_df.empty else pd.DataFrame()

    official_asset_hashes_after = _official_hashes_after()
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
    ]:
        _add_qa(qa_rows, f"safety::{check}", "PASS", "False")

    qa_df = pd.DataFrame(qa_rows)
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    if qa_fail_count > 0:
        decision = REVIEWED_NOT_READY_DECISION
    elif len(send_df) > 0:
        decision = REVIEWED_READY_DECISION
    else:
        decision = REVIEWED_NO_SAFE_DECISION
    summary = {
        "stage": "325D",
        "mode": "validate-reviewed",
        "spot_check_record_count": len(reviewed_df),
        "pending_count": pending_count,
        "send_to_adjudicator_count": len(send_df),
        "holdout_count": len(holdout_df),
        "rejected_count": len(rejected_df),
        "needs_more_info_count": len(needs_more_info_df),
        "invalid_decision_count": invalid_decision_count + blank_decision_count,
        "carried_forward_325c_holdout_count": len(holdout_records),
        "validate_reviewed_mode_implemented": True,
        "official_assets_modified": official_assets_modified,
        "official_assets_written": [],
        "official_asset_hashes_before": official_asset_hashes_before,
        "official_asset_hashes_after": official_asset_hashes_after,
        "llm_or_adjudicator_called": False,
        "semantic_rules_applied": False,
        "trusted_marked_in_production": False,
        "official_rule_candidates_created": False,
        "controlled_official_proposals_created": False,
        "sandbox_replay_package_created": False,
        "top_spot_check_examples": reviewed_df[["spot_check_id", "alias_label", "human_spot_check_decision"]].head(8).to_dict(orient="records") if not reviewed_df.empty else [],
        "qa_pass_count": int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0,
        "qa_warn_count": int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else [],
        "decision": decision,
    }
    final_plan = {
        "stage": "325D",
        "mode": "validate-reviewed",
        "decision": decision,
        "send_to_adjudicator_records": send_df.to_dict(orient="records"),
        "holdout_or_rejected_records": non_send_df.to_dict(orient="records"),
        "carried_forward_325c_holdout_records": holdout_records,
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
        "final_routing_plan": final_plan,
        "no_apply_proof": {
            "stage": "325D",
            "mode": "validate-reviewed",
            "decision": decision,
            "official_assets_read": [str(FORMAL_SCOPE_RULES_PATH), str(SEMANTIC_ALIAS_ASSET_PATH)],
            "official_assets_written": [],
            "official_assets_modified": official_assets_modified,
            "official_asset_hashes_before": official_asset_hashes_before,
            "official_asset_hashes_after": official_asset_hashes_after,
            "llm_or_adjudicator_called": False,
            "official_rule_candidates_created": False,
            "controlled_official_proposals_created": False,
            "sandbox_replay_package_created": False,
        },
        "reviewed_df": reviewed_df,
        "send_to_adjudicator_df": send_df,
        "holdout_or_rejected_df": pd.concat([non_send_df, pd.DataFrame(holdout_records).fillna("")], ignore_index=True).fillna(""),
        "carried_forward_holdout_df": pd.DataFrame(holdout_records).fillna(""),
        "qa_checks_df": qa_df,
    }


def load_reviewed_workbook_records(reviewed_workbook: Path) -> List[Dict[str, Any]]:
    return _load_reviewed_spot_check_records(reviewed_workbook)
