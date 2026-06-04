from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set

import pandas as pd


EXPECTED_324E_READY_DECISION = "SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_READY_FOR_324F_HUMAN_CONFIRMATION"
EXPECTED_324F_PREPARE_DECISION = "SCOPE_NOISE_HUMAN_CONFIRMATION_324F_READY_FOR_HUMAN_REVIEW"
EXPECTED_324F_PREPARE_NOT_READY = "SCOPE_NOISE_HUMAN_CONFIRMATION_324F_NOT_READY"
EXPECTED_324F_REVIEWED_READY_DECISION = "SCOPE_NOISE_HUMAN_CONFIRMATION_324F_REVIEWED_READY_FOR_324G_SANDBOX_REPLAY"
EXPECTED_324F_REVIEWED_REJECTED_DECISION = "SCOPE_NOISE_HUMAN_CONFIRMATION_324F_REVIEWED_REJECTED_NO_SANDBOX_REPLAY"
EXPECTED_324F_REVIEWED_NEEDS_MORE_INFO_DECISION = "SCOPE_NOISE_HUMAN_CONFIRMATION_324F_REVIEWED_NEEDS_MORE_INFO_BLOCKED"
EXPECTED_324F_REVIEWED_NOT_READY = "SCOPE_NOISE_HUMAN_CONFIRMATION_324F_REVIEWED_NOT_READY"

DEFAULT_SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_DIR = Path(
    r"D:\_datefac\output\scope_noise_response_schema_validation_324e"
)
DEFAULT_SCOPE_NOISE_SAFE_ADJUDICATOR_REQUEST_324C_DIR = Path(
    r"D:\_datefac\output\scope_noise_safe_adjudicator_request_324c"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\scope_noise_human_confirmation_324f")
DEFAULT_REVIEWED_OUTPUT_DIR = Path(r"D:\_datefac\output\scope_noise_human_confirmation_324f_reviewed")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

PENDING_HUMAN_CONFIRMATION = "PENDING_HUMAN_CONFIRMATION"
ALLOWED_REVIEWER_DECISIONS = {"CONFIRM", "REJECT", "NEEDS_MORE_INFO"}
REQUIRED_REVIEWER_FIELDS = {
    "reviewer_decision",
    "reviewer_note",
    "reviewer_name",
    "review_timestamp",
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


def _read_workbook_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()
    return df.fillna("")


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _join_unique(items: Iterable[Any], limit: int = 16) -> str:
    out: List[str] = []
    seen: Set[str] = set()
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            out.append(clean)
            seen.add(clean)
        if len(out) >= limit:
            break
    return " | ".join(out)


def _decision_distribution(records: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    distribution: Dict[str, int] = {}
    for record in records:
        key = _norm(record.get("reviewer_decision")) or PENDING_HUMAN_CONFIRMATION
        distribution[key] = distribution.get(key, 0) + 1
    return distribution


def _canonical_reviewer_decision(value: Any) -> str:
    return _norm(value).upper()


def _missing_required_fields(records: Sequence[Dict[str, Any]], fields: Sequence[str]) -> List[Dict[str, str]]:
    missing: List[Dict[str, str]] = []
    for record in records:
        record_id = _norm(record.get("confirmation_id")) or "UNKNOWN_RECORD"
        for field in fields:
            if _norm(record.get(field)) == "":
                missing.append({"record_id": record_id, "field": field})
    return missing


def _build_warning_text() -> str:
    return (
        "This is a long narrative label with LONG_LABEL_REVIEW_REQUIRED. "
        "It must not be auto-promoted to scope noise or any official rule. "
        "Human confirmation is required before any later sandbox replay stage."
    )


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def load_scope_noise_human_confirmation_324f_inputs(
    scope_noise_response_schema_validation_dir: Path,
) -> Dict[str, Any]:
    summary_324e = _read_json(
        scope_noise_response_schema_validation_dir / "scope_noise_response_schema_validation_324e_summary.json"
    )
    request_dir = Path(
        _norm(summary_324e.get("request_dir"))
        or str(DEFAULT_SCOPE_NOISE_SAFE_ADJUDICATOR_REQUEST_324C_DIR)
    )
    request_package = _read_json(
        request_dir / "scope_noise_safe_adjudicator_request_324c_request_package.json"
    )
    request_items = request_package.get("request_items", [])
    if not isinstance(request_items, list) or not request_items:
        request_items = _read_jsonl(
            request_dir / "scope_noise_safe_adjudicator_request_324c_request_items.jsonl"
        )
    return {
        "summary_324e": summary_324e,
        "qa_324e": _read_json(
            scope_noise_response_schema_validation_dir / "scope_noise_response_schema_validation_324e_qa.json"
        ),
        "accepted_payload_324e": _read_json(
            scope_noise_response_schema_validation_dir
            / "scope_noise_response_schema_validation_324e_accepted_for_human_confirmation.json"
        ),
        "validated_responses_324e": _read_jsonl(
            scope_noise_response_schema_validation_dir
            / "scope_noise_response_schema_validation_324e_validated_responses.jsonl"
        ),
        "request_dir_324c": request_dir,
        "request_package_324c": request_package,
        "request_items_324c": request_items if isinstance(request_items, list) else [],
    }


def build_scope_noise_human_confirmation_324f_prepare(inputs: Dict[str, Any]) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    summary_324e = inputs.get("summary_324e", {})
    qa_324e = inputs.get("qa_324e", {})
    accepted_payload_324e = inputs.get("accepted_payload_324e", {})
    validated_rows_324e = [
        row for row in inputs.get("validated_responses_324e", []) if isinstance(row, dict)
    ]
    request_dir_324c = inputs.get("request_dir_324c", DEFAULT_SCOPE_NOISE_SAFE_ADJUDICATOR_REQUEST_324C_DIR)
    request_items_324c = [
        row for row in inputs.get("request_items_324c", []) if isinstance(row, dict)
    ]

    add_qa(
        "readiness::324e_decision",
        "PASS" if _norm(summary_324e.get("decision")) == EXPECTED_324E_READY_DECISION else "FAIL",
        _norm(summary_324e.get("decision")),
    )
    add_qa(
        "readiness::324e_qa_fail_count",
        "PASS" if _safe_int(summary_324e.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_324e.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324e_qa_json_fail_count",
        "PASS" if _safe_int(qa_324e.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_324e.get("qa_fail_count", "")),
    )
    for key, expected in [
        ("request_count", 1),
        ("response_count", 1),
        ("schema_valid_count", 1),
        ("schema_invalid_count", 0),
        ("accepted_for_human_confirmation_count", 1),
    ]:
        add_qa(
            f"readiness::324e_{key}",
            "PASS" if _safe_int(summary_324e.get(key)) == expected else "FAIL",
            str(summary_324e.get(key, "")),
        )
    add_qa(
        "readiness::324e_deterministic_gate_result",
        "PASS" if _norm(summary_324e.get("deterministic_gate_result")) == "PASS" else "FAIL",
        _norm(summary_324e.get("deterministic_gate_result")),
    )

    accepted_rows = accepted_payload_324e.get("accepted_for_human_confirmation", [])
    if not isinstance(accepted_rows, list):
        accepted_rows = []
    accepted_rows = [row for row in accepted_rows if isinstance(row, dict)]
    request_lookup = {
        _norm(row.get("request_id")): row
        for row in request_items_324c
        if _norm(row.get("request_id"))
    }
    validated_lookup = {
        _norm(row.get("request_id")): row
        for row in validated_rows_324e
        if _norm(row.get("request_id"))
    }

    add_qa(
        "accepted_suggestions::count",
        "PASS" if len(accepted_rows) == 1 else "FAIL",
        f"actual={len(accepted_rows)}",
    )
    add_qa(
        "accepted_suggestions::scope_noise_only",
        "PASS"
        if len(accepted_rows) == 1 and _norm(accepted_rows[0].get("candidate_type")) == "scope_noise"
        else "FAIL",
        _norm(accepted_rows[0].get("candidate_type")) if accepted_rows else "",
    )

    confirmation_records: List[Dict[str, Any]] = []
    confirmation_package_records: List[Dict[str, Any]] = []
    if accepted_rows:
        accepted = accepted_rows[0]
        request_id = _norm(accepted.get("request_id"))
        request_item = request_lookup.get(request_id, {})
        validated_row = validated_lookup.get(request_id, {})
        parsed_response = accepted.get("parsed_response", {})
        if not isinstance(parsed_response, dict):
            parsed_response = {}

        risk_flags = _flatten_sequence(request_item.get("risk_flags"))
        safety_flags = _flatten_sequence(parsed_response.get("safety_flags"))
        provenance = request_item.get("provenance", {})
        if not isinstance(provenance, dict):
            provenance = {}
        safety_context = request_item.get("safety_context", {})
        if not isinstance(safety_context, dict):
            safety_context = {}

        confirmation_id = f"324f::{request_id.replace('::', '__')}" if request_id else "324f::001"
        sample_evidence = {
            "sample_candidate_ids": _flatten_sequence(request_item.get("sample_candidate_ids")),
            "sample_texts": _flatten_sequence(request_item.get("sample_texts")),
            "sample_years": _flatten_sequence(provenance.get("sample_years")),
            "sample_raw_metric_names": _flatten_sequence(provenance.get("sample_raw_metric_names")),
            "sample_table_titles": _flatten_sequence(provenance.get("sample_table_titles")),
            "raw_response_text": _norm(validated_row.get("raw_response_text")),
        }
        provenance_payload = {
            "source_scope_review_id": _norm(request_item.get("source_scope_review_id")),
            "source_refined_scope_candidate_id": _norm(request_item.get("source_refined_scope_candidate_id")),
            "representative_group_id": _norm(provenance.get("representative_group_id")),
            "source_group_ids": _flatten_sequence(provenance.get("source_group_ids")),
            "source_group_count": _safe_int(provenance.get("source_group_count")),
            "duplicate_source_group_count": _safe_int(provenance.get("duplicate_source_group_count")),
            "source_stage": _norm(provenance.get("source_stage")),
            "source_stage_signatures": _flatten_sequence(provenance.get("source_stage_signatures")),
            "source_stage_chain": _flatten_sequence(provenance.get("source_stage_chain")),
            "request_package_reference": str(
                request_dir_324c / "scope_noise_safe_adjudicator_request_324c_request_package.json"
            ),
            "accepted_validation_reference": str(
                DEFAULT_SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_DIR
                / "scope_noise_response_schema_validation_324e_accepted_for_human_confirmation.json"
            ),
        }
        confirmation_record = {
            "confirmation_id": confirmation_id,
            "request_id": request_id,
            "source_scope_review_id": provenance_payload["source_scope_review_id"],
            "source_refined_scope_candidate_id": provenance_payload["source_refined_scope_candidate_id"],
            "candidate_type": "scope_noise",
            "candidate_label": _norm(request_item.get("candidate_label")) or _norm(accepted.get("candidate_label")),
            "response_label": _norm(parsed_response.get("response_label")),
            "confidence": _norm(parsed_response.get("confidence")),
            "normalized_target_metric_if_any": _norm(parsed_response.get("normalized_target_metric_if_any")),
            "rationale": _norm(parsed_response.get("rationale")),
            "safety_flags": _join_unique(safety_flags, limit=16),
            "risk_flags": _join_unique(risk_flags, limit=16),
            "affected_candidate_count": _safe_int(request_item.get("affected_candidate_count")),
            "affected_review_required_count": _safe_int(request_item.get("affected_review_required_count")),
            "priority_score": _safe_float(request_item.get("priority_score")),
            "manual_review_warning": _build_warning_text(),
            "adjudicator_caution": _norm(safety_context.get("adjudicator_caution"))
            or "This long narrative label must not be auto-accepted or auto-promoted.",
            "sample_candidate_ids": _join_unique(sample_evidence["sample_candidate_ids"], limit=16),
            "sample_texts": _join_unique(sample_evidence["sample_texts"], limit=8),
            "sample_years": _join_unique(sample_evidence["sample_years"], limit=8),
            "sample_raw_metric_names": _join_unique(sample_evidence["sample_raw_metric_names"], limit=6),
            "sample_table_titles": _join_unique(sample_evidence["sample_table_titles"], limit=8),
            "raw_response_text": sample_evidence["raw_response_text"],
            "representative_group_id": provenance_payload["representative_group_id"],
            "source_group_ids": _join_unique(provenance_payload["source_group_ids"], limit=16),
            "source_stage_signatures": _join_unique(
                provenance_payload["source_stage_signatures"], limit=8
            ),
            "source_stage_chain": _join_unique(provenance_payload["source_stage_chain"], limit=8),
            "why_high_impact": _norm(provenance.get("why_high_impact")),
            "why_safe_or_risky": _norm(provenance.get("why_safe_or_risky")),
            "risk_notes": _norm(provenance.get("risk_notes")),
            "next_action_if_confirmed": "SANDBOX_REPLAY_REQUIRED_BEFORE_ANY_OFFICIAL_RULE_CHANGE",
            "sandbox_replay_required": True,
            "auto_promotion_allowed": False,
            "reviewer_decision": PENDING_HUMAN_CONFIRMATION,
            "reviewer_note": "",
            "reviewer_name": "",
            "review_timestamp": "",
            "allowed_reviewer_decisions": "CONFIRM | REJECT | NEEDS_MORE_INFO",
            "editable_fields_note": "Edit reviewer_decision / reviewer_note / reviewer_name / review_timestamp only.",
        }
        confirmation_records.append(confirmation_record)
        confirmation_package_records.append(
            {
                **confirmation_record,
                "sample_evidence": sample_evidence,
                "provenance": provenance_payload,
                "raw_accepted_row_324e": accepted,
                "raw_request_item_324c": request_item,
                "raw_validated_row_324e": validated_row,
            }
        )

        add_qa(
            "accepted_suggestions::request_id_found_in_324c_cached_request",
            "PASS" if request_item else "FAIL",
            request_id,
        )

    confirmation_df = pd.DataFrame(confirmation_records).fillna("")
    duplicate_confirmation_id_count = (
        int(confirmation_df["confirmation_id"].astype(str).duplicated().sum())
        if not confirmation_df.empty
        else 0
    )
    default_all_pending = (
        not confirmation_df.empty
        and confirmation_df["reviewer_decision"].astype(str).eq(PENDING_HUMAN_CONFIRMATION).all()
    )
    warning_present = (
        not confirmation_df.empty
        and confirmation_df["manual_review_warning"].astype(str).str.contains(
            "must not be auto-promoted",
            case=False,
            regex=False,
        ).all()
    )
    provenance_present = (
        not confirmation_df.empty
        and confirmation_df["source_group_ids"].astype(str).eq("").sum() == 0
        and confirmation_df["source_scope_review_id"].astype(str).eq("").sum() == 0
    )
    sample_evidence_present = (
        not confirmation_df.empty
        and confirmation_df["sample_texts"].astype(str).eq("").sum() == 0
        and confirmation_df["sample_candidate_ids"].astype(str).eq("").sum() == 0
    )
    sandbox_replay_required = (
        not confirmation_df.empty
        and confirmation_df["sandbox_replay_required"].astype(bool).all()
    )

    add_qa(
        "confirmation_records::count",
        "PASS" if len(confirmation_records) == 1 else "FAIL",
        f"actual={len(confirmation_records)}",
    )
    add_qa(
        "confirmation_records::default_pending_human_confirmation",
        "PASS" if default_all_pending else "FAIL",
        json.dumps(_decision_distribution(confirmation_records), ensure_ascii=False),
    )
    add_qa(
        "confirmation_records::unique_confirmation_id",
        "PASS" if duplicate_confirmation_id_count == 0 else "FAIL",
        f"actual={duplicate_confirmation_id_count}",
    )
    add_qa(
        "confirmation_records::allowed_decisions_present",
        "PASS"
        if not confirmation_df.empty
        and confirmation_df["allowed_reviewer_decisions"].astype(str).eq(
            "CONFIRM | REJECT | NEEDS_MORE_INFO"
        ).all()
        else "FAIL",
        "CONFIRM | REJECT | NEEDS_MORE_INFO",
    )
    add_qa(
        "confirmation_records::warning_present",
        "PASS" if warning_present else "FAIL",
        confirmation_df["manual_review_warning"].iloc[0] if not confirmation_df.empty else "",
    )
    add_qa(
        "confirmation_records::risk_flags_carried_forward",
        "PASS"
        if not confirmation_df.empty and confirmation_df["risk_flags"].astype(str).eq("").sum() == 0
        else "FAIL",
        confirmation_df["risk_flags"].iloc[0] if not confirmation_df.empty else "",
    )
    add_qa(
        "confirmation_records::sample_evidence_present",
        "PASS" if sample_evidence_present else "FAIL",
        confirmation_df["sample_texts"].iloc[0] if not confirmation_df.empty else "",
    )
    add_qa(
        "confirmation_records::provenance_present",
        "PASS" if provenance_present else "FAIL",
        confirmation_df["source_group_ids"].iloc[0] if not confirmation_df.empty else "",
    )
    add_qa(
        "confirmation_records::sandbox_replay_required",
        "PASS" if sandbox_replay_required else "FAIL",
        "all confirmations still require sandbox replay",
    )
    add_qa(
        "confirmation_records::no_auto_promotion",
        "PASS"
        if not confirmation_df.empty and confirmation_df["auto_promotion_allowed"].astype(bool).eq(False).all()
        else "FAIL",
        "False",
    )

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    add_qa(
        "safety::official_assets_not_modified",
        "PASS"
        if alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
        else "FAIL",
        (
            f"alias_before={alias_hash_before} alias_after={alias_hash_after} "
            f"scope_before={scope_hash_before} scope_after={scope_hash_after}"
        ),
    )
    add_qa(
        "safety::llm_or_adjudicator_not_called",
        "PASS",
        "324F uses 324E output and cached 324C evidence only.",
    )
    add_qa(
        "safety::no_sandbox_replay_output_in_prepare",
        "PASS",
        "324F prepare creates a human confirmation package only.",
    )
    add_qa(
        "safety::no_official_rule_candidates_created",
        "PASS",
        "324F does not create sandbox replay or official rule candidates.",
    )

    review_instructions_df = pd.DataFrame(
        [
            {
                "section": "package_purpose",
                "instruction": "Review the single 324E accepted scope-noise suggestion and decide whether it may proceed to a later sandbox replay stage.",
            },
            {
                "section": "editable_fields",
                "instruction": "Edit reviewer_decision, reviewer_note, reviewer_name, and review_timestamp only.",
            },
            {
                "section": "allowed_decisions",
                "instruction": "Allowed reviewer_decision values: CONFIRM, REJECT, NEEDS_MORE_INFO.",
            },
            {
                "section": "long_label_warning",
                "instruction": "This is a long narrative label with LONG_LABEL_REVIEW_REQUIRED and must not be auto-promoted.",
            },
            {
                "section": "confirm_rule",
                "instruction": "Use CONFIRM only if the label is clearly non-core contextual disclosure after manual inspection of the carried-forward evidence.",
            },
            {
                "section": "next_stage_note",
                "instruction": "Even after CONFIRM, the item must still go through sandbox replay before any later official-rule stage.",
            },
        ]
    ).fillna("")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )

    summary = {
        "stage": "324F",
        "mode": "prepare",
        "output_dir": "",
        "scope_noise_response_schema_validation_dir": str(
            DEFAULT_SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_DIR
        ),
        "request_dir_324c": str(request_dir_324c),
        "confirmation_record_count": len(confirmation_records),
        "pending_count": int(_decision_distribution(confirmation_records).get(PENDING_HUMAN_CONFIRMATION, 0)),
        "confirmed_count": 0,
        "rejected_count": 0,
        "needs_more_info_count": 0,
        "decision_distribution": _decision_distribution(confirmation_records),
        "validate_reviewed_mode_implemented": True,
        "official_assets_not_modified": True,
        "human_confirmation_only_no_apply_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_324F_PREPARE_DECISION if qa_fail_count == 0 else EXPECTED_324F_PREPARE_NOT_READY,
    }

    confirmation_package_json = {
        "stage": "324F",
        "mode": "prepare",
        "decision": summary["decision"],
        "allowed_reviewer_decisions": sorted(ALLOWED_REVIEWER_DECISIONS),
        "confirmation_records": [_to_jsonable(record) for record in confirmation_package_records],
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
        "confirmation_records_df": confirmation_df,
        "review_instructions_df": review_instructions_df,
        "confirmation_package_json": confirmation_package_json,
    }


def build_scope_noise_human_confirmation_324f_validate_reviewed(
    reviewed_workbook: Path,
    summary_324e: Dict[str, Any],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    add_qa(
        "readiness::324e_decision",
        "PASS" if _norm(summary_324e.get("decision")) == EXPECTED_324E_READY_DECISION else "FAIL",
        _norm(summary_324e.get("decision")),
    )
    add_qa(
        "readiness::324e_qa_fail_count",
        "PASS" if _safe_int(summary_324e.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_324e.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324e_accepted_for_human_confirmation_count",
        "PASS"
        if _safe_int(summary_324e.get("accepted_for_human_confirmation_count")) == 1
        else "FAIL",
        str(summary_324e.get("accepted_for_human_confirmation_count", "")),
    )
    add_qa(
        "readiness::324e_deterministic_gate_result",
        "PASS" if _norm(summary_324e.get("deterministic_gate_result")) == "PASS" else "FAIL",
        _norm(summary_324e.get("deterministic_gate_result")),
    )

    reviewed_df = _read_workbook_sheet(reviewed_workbook, "confirmation_records")
    if reviewed_df.empty:
        reviewed_df = _read_workbook_sheet(reviewed_workbook, "all_reviewed_records")
    reviewed_df = reviewed_df.fillna("")

    required_columns = {
        "confirmation_id",
        "request_id",
        "candidate_type",
        "candidate_label",
        "response_label",
        "manual_review_warning",
        "reviewer_decision",
        "reviewer_note",
        "reviewer_name",
        "review_timestamp",
        "sandbox_replay_required",
        "auto_promotion_allowed",
    }
    missing_columns = sorted(required_columns.difference(set(reviewed_df.columns)))
    add_qa(
        "reviewed_integrity::required_columns_present",
        "PASS" if not missing_columns else "FAIL",
        "none" if not missing_columns else " | ".join(missing_columns),
    )

    records = reviewed_df.to_dict(orient="records") if not reviewed_df.empty else []
    add_qa(
        "reviewed_counts::confirmation_record_count",
        "PASS" if len(records) == 1 else "FAIL",
        f"actual={len(records)}",
    )

    duplicate_confirmation_id_count = (
        int(reviewed_df["confirmation_id"].astype(str).duplicated().sum())
        if not reviewed_df.empty
        else 0
    )
    add_qa(
        "reviewed_integrity::unique_confirmation_id",
        "PASS" if duplicate_confirmation_id_count == 0 else "FAIL",
        f"actual={duplicate_confirmation_id_count}",
    )

    decisions = [_canonical_reviewer_decision(row.get("reviewer_decision")) for row in records]
    pending_count = sum(1 for decision in decisions if decision in {"", PENDING_HUMAN_CONFIRMATION})
    invalid_decision_values = sorted(
        {
            decision
            for decision in decisions
            if decision and decision not in ALLOWED_REVIEWER_DECISIONS
        }
    )
    confirmed_count = sum(1 for decision in decisions if decision == "CONFIRM")
    rejected_count = sum(1 for decision in decisions if decision == "REJECT")
    needs_more_info_count = sum(1 for decision in decisions if decision == "NEEDS_MORE_INFO")

    add_qa(
        "reviewed_integrity::no_pending_decisions",
        "PASS" if pending_count == 0 else "FAIL",
        f"actual={pending_count}",
    )
    add_qa(
        "reviewed_integrity::no_invalid_decisions",
        "PASS" if not invalid_decision_values else "FAIL",
        "none" if not invalid_decision_values else " | ".join(invalid_decision_values),
    )
    add_qa(
        "reviewed_integrity::exactly_one_terminal_route",
        "PASS" if confirmed_count + rejected_count + needs_more_info_count == 1 else "FAIL",
        json.dumps(
            {
                "confirmed": confirmed_count,
                "rejected": rejected_count,
                "needs_more_info": needs_more_info_count,
            },
            ensure_ascii=False,
        ),
    )

    missing_reviewer_fields = _missing_required_fields(records, sorted(REQUIRED_REVIEWER_FIELDS))
    add_qa(
        "reviewed_integrity::reviewer_fields_non_empty",
        "PASS" if not missing_reviewer_fields else "FAIL",
        "none"
        if not missing_reviewer_fields
        else " | ".join(
            f"{item['record_id']}::{item['field']}" for item in missing_reviewer_fields[:10]
        ),
    )
    add_qa(
        "reviewed_integrity::warning_preserved",
        "PASS"
        if not reviewed_df.empty
        and reviewed_df["manual_review_warning"].astype(str).str.contains(
            "must not be auto-promoted",
            case=False,
            regex=False,
        ).all()
        else "FAIL",
        reviewed_df["manual_review_warning"].iloc[0] if not reviewed_df.empty else "",
    )
    add_qa(
        "reviewed_integrity::sandbox_replay_still_required_if_confirmed",
        "PASS"
        if not reviewed_df.empty and reviewed_df["sandbox_replay_required"].astype(bool).all()
        else "FAIL",
        "True",
    )
    add_qa(
        "reviewed_integrity::auto_promotion_still_disabled",
        "PASS"
        if not reviewed_df.empty and reviewed_df["auto_promotion_allowed"].astype(bool).eq(False).all()
        else "FAIL",
        "False",
    )

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    add_qa(
        "safety::official_assets_not_modified",
        "PASS"
        if alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
        else "FAIL",
        (
            f"alias_before={alias_hash_before} alias_after={alias_hash_after} "
            f"scope_before={scope_hash_before} scope_after={scope_hash_after}"
        ),
    )
    add_qa(
        "safety::no_rule_creation_or_apply",
        "PASS",
        "324F validate-reviewed only routes reviewed decisions.",
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )

    if qa_fail_count == 0 and confirmed_count == 1:
        decision = EXPECTED_324F_REVIEWED_READY_DECISION
        next_route = "324G_SANDBOX_REPLAY"
    elif qa_fail_count == 0 and rejected_count == 1:
        decision = EXPECTED_324F_REVIEWED_REJECTED_DECISION
        next_route = "NO_SANDBOX_REPLAY_REJECTED"
    elif qa_fail_count == 0 and needs_more_info_count == 1:
        decision = EXPECTED_324F_REVIEWED_NEEDS_MORE_INFO_DECISION
        next_route = "BLOCKED_NEEDS_MORE_INFO"
    else:
        decision = EXPECTED_324F_REVIEWED_NOT_READY
        next_route = "NOT_READY"

    summary = {
        "stage": "324F",
        "mode": "validate-reviewed",
        "output_dir": "",
        "reviewed_workbook": str(reviewed_workbook),
        "confirmation_record_count": len(records),
        "pending_count": pending_count,
        "confirmed_count": confirmed_count,
        "rejected_count": rejected_count,
        "needs_more_info_count": needs_more_info_count,
        "invalid_decision_count": len(invalid_decision_values),
        "decision_distribution": _decision_distribution(records),
        "validate_reviewed_mode_implemented": True,
        "official_assets_not_modified": True,
        "human_confirmation_only_no_apply_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": decision,
    }

    confirmed_df = (
        reviewed_df.loc[
            reviewed_df["reviewer_decision"].astype(str).map(_canonical_reviewer_decision) == "CONFIRM"
        ].copy()
        if not reviewed_df.empty
        else pd.DataFrame()
    )
    rejected_df = (
        reviewed_df.loc[
            reviewed_df["reviewer_decision"].astype(str).map(_canonical_reviewer_decision) == "REJECT"
        ].copy()
        if not reviewed_df.empty
        else pd.DataFrame()
    )
    needs_more_info_df = (
        reviewed_df.loc[
            reviewed_df["reviewer_decision"].astype(str).map(_canonical_reviewer_decision)
            == "NEEDS_MORE_INFO"
        ].copy()
        if not reviewed_df.empty
        else pd.DataFrame()
    )

    reviewed_outcome_json = {
        "stage": "324F",
        "mode": "validate-reviewed",
        "reviewed_workbook": str(reviewed_workbook),
        "decision": decision,
        "next_route": next_route,
        "confirmed_records": confirmed_df.to_dict(orient="records") if not confirmed_df.empty else [],
        "rejected_records": rejected_df.to_dict(orient="records") if not rejected_df.empty else [],
        "needs_more_info_records": needs_more_info_df.to_dict(orient="records")
        if not needs_more_info_df.empty
        else [],
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
        "confirmed_df": confirmed_df.fillna(""),
        "rejected_df": rejected_df.fillna(""),
        "needs_more_info_df": needs_more_info_df.fillna(""),
        "all_reviewed_df": reviewed_df.fillna(""),
        "reviewed_outcome_json": reviewed_outcome_json,
    }
