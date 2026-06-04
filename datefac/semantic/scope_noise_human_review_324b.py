from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set

import pandas as pd


EXPECTED_324A_DECISION = "SCOPE_NOISE_REFINEMENT_324A_READY_FOR_SCOPE_REVIEW_BATCH"
EXPECTED_324B_PREPARE_DECISION = "SCOPE_NOISE_HUMAN_REVIEW_324B_READY_FOR_HUMAN_REVIEW"
EXPECTED_324B_PREPARE_NOT_READY = "SCOPE_NOISE_HUMAN_REVIEW_324B_NOT_READY"
EXPECTED_324B_REVIEWED_SANDBOX_DECISION = (
    "SCOPE_NOISE_HUMAN_REVIEW_324B_REVIEWED_READY_FOR_324C_SANDBOX_REPLAY"
)
EXPECTED_324B_REVIEWED_ADJUDICATOR_DECISION = (
    "SCOPE_NOISE_HUMAN_REVIEW_324B_REVIEWED_READY_FOR_SAFE_ADJUDICATOR_REQUEST_PREP"
)
EXPECTED_324B_REVIEWED_NOT_READY = "SCOPE_NOISE_HUMAN_REVIEW_324B_REVIEWED_NOT_READY"

DEFAULT_SCOPE_REFINEMENT_324A_DIR = Path(r"D:\_datefac\output\scope_noise_refinement_324a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\scope_noise_human_review_324b")
DEFAULT_REVIEWED_OUTPUT_DIR = Path(r"D:\_datefac\output\scope_noise_human_review_324b_reviewed")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

PENDING_HUMAN_SCOPE_REVIEW = "PENDING_HUMAN_SCOPE_REVIEW"
ALLOWED_HUMAN_DECISIONS = {
    "CONFIRM_SCOPE_NOISE",
    "REJECT_SCOPE_NOISE",
    "NEEDS_MORE_INFO",
    "ESCALATE_TO_ADJUDICATOR",
}
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


def _join_unique(items: Iterable[Any], limit: int = 12) -> str:
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
        key = _norm(record.get("reviewer_decision")) or PENDING_HUMAN_SCOPE_REVIEW
        distribution[key] = distribution.get(key, 0) + 1
    return distribution


def _canonical_reviewer_decision(value: Any) -> str:
    return _norm(value).upper()


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def _build_warning_text(risk_flags: Sequence[Any]) -> str:
    flags = {_norm(item) for item in risk_flags if _norm(item)}
    if "LONG_LABEL_REVIEW_REQUIRED" in flags:
        return (
            "This candidate includes LONG_LABEL_REVIEW_REQUIRED. "
            "Do not treat this long narrative label as a low-risk automatic scope exclusion. "
            "Confirm only if the text is clearly non-core contextual noise after manual inspection."
        )
    return "Review conservatively before confirming any scope-noise exclusion."


def _missing_required_fields(records: Sequence[Dict[str, Any]], fields: Sequence[str]) -> List[Dict[str, str]]:
    missing: List[Dict[str, str]] = []
    for record in records:
        record_id = _norm(record.get("scope_review_id")) or "UNKNOWN_RECORD"
        for field in fields:
            if _norm(record.get(field)) == "":
                missing.append({"record_id": record_id, "field": field})
    return missing


def load_scope_noise_human_review_324b_inputs(scope_refinement_dir: Path) -> Dict[str, Any]:
    refined_batch = _read_json(scope_refinement_dir / "scope_noise_refinement_324a_refined_batch.json")
    return {
        "summary_324a": _read_json(scope_refinement_dir / "scope_noise_refinement_324a_summary.json"),
        "qa_324a": _read_json(scope_refinement_dir / "scope_noise_refinement_324a_qa.json"),
        "refined_batch_324a": refined_batch,
        "refined_scope_candidates": refined_batch.get("refined_scope_candidates", [])
        if isinstance(refined_batch.get("refined_scope_candidates", []), list)
        else [],
        "excluded_source_groups": refined_batch.get("excluded_source_groups", [])
        if isinstance(refined_batch.get("excluded_source_groups", []), list)
        else [],
        "duplicate_provenance": refined_batch.get("duplicate_provenance", [])
        if isinstance(refined_batch.get("duplicate_provenance", []), list)
        else [],
    }


def build_scope_noise_human_review_324b_prepare(inputs: Dict[str, Any]) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    summary_324a = inputs.get("summary_324a", {})
    qa_324a = inputs.get("qa_324a", {})
    refined_scope_candidates = [
        item for item in inputs.get("refined_scope_candidates", []) if isinstance(item, dict)
    ]

    add_qa(
        "readiness::324a_decision",
        "PASS" if _norm(summary_324a.get("decision")) == EXPECTED_324A_DECISION else "FAIL",
        _norm(summary_324a.get("decision")),
    )
    add_qa(
        "readiness::324a_qa_fail_count",
        "PASS" if _safe_int(summary_324a.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_324a.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324a_qa_json_fail_count",
        "PASS" if _safe_int(qa_324a.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_324a.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324a_refined_scope_candidate_count",
        "PASS" if _safe_int(summary_324a.get("refined_scope_candidate_count")) == 1 else "FAIL",
        str(summary_324a.get("refined_scope_candidate_count", "")),
    )
    add_qa(
        "readiness::324a_loaded_single_candidate",
        "PASS" if len(refined_scope_candidates) == 1 else "FAIL",
        f"actual={len(refined_scope_candidates)}",
    )

    review_records: List[Dict[str, Any]] = []
    if refined_scope_candidates:
        candidate = refined_scope_candidates[0]
        risk_flags = _flatten_sequence(candidate.get("risk_flags"))
        review_record = {
            "scope_review_id": "324b::scope_review::001",
            "refined_scope_candidate_id": _norm(candidate.get("refined_scope_candidate_id")),
            "candidate_type": "scope_noise",
            "reviewer_decision": PENDING_HUMAN_SCOPE_REVIEW,
            "reviewer_note": "",
            "reviewer_name": "",
            "review_timestamp": "",
            "allowed_reviewer_decisions": "CONFIRM_SCOPE_NOISE | REJECT_SCOPE_NOISE | NEEDS_MORE_INFO | ESCALATE_TO_ADJUDICATOR",
            "repaired_label": _norm(candidate.get("repaired_label")),
            "representative_group_id": _norm(candidate.get("representative_group_id")),
            "source_group_ids": _join_unique(candidate.get("source_group_ids", []), limit=16),
            "source_group_count": _safe_int(candidate.get("source_group_count")),
            "duplicate_source_group_count": _safe_int(candidate.get("duplicate_source_group_count")),
            "affected_candidate_count": _safe_int(candidate.get("affected_candidate_count")),
            "affected_review_required_count": _safe_int(candidate.get("affected_review_required_count")),
            "affected_report_count": _safe_int(candidate.get("affected_report_count")),
            "priority_score_max": _safe_float(candidate.get("priority_score_max")),
            "priority_score_sum": _safe_float(candidate.get("priority_score_sum")),
            "expected_review_reduction_potential": _safe_int(candidate.get("expected_review_reduction_potential")),
            "risk_flags": _join_unique(risk_flags, limit=16),
            "risk_notes": _norm(candidate.get("risk_notes")),
            "manual_review_warning": _build_warning_text(risk_flags),
            "auto_scope_exclusion_allowed": False,
            "source_stage_signatures": _join_unique(candidate.get("source_stage_signatures", []), limit=8),
            "sample_candidate_ids": _join_unique(candidate.get("sample_candidate_ids", []), limit=16),
            "sample_raw_metric_names": _join_unique(candidate.get("sample_raw_metric_names", []), limit=6),
            "sample_row_texts": _join_unique(candidate.get("sample_row_texts", []), limit=8),
            "sample_table_titles": _join_unique(candidate.get("sample_table_titles", []), limit=8),
            "sample_years": _join_unique(candidate.get("sample_years", []), limit=8),
            "why_high_impact": _norm(candidate.get("why_high_impact")),
            "why_safe_or_risky": _norm(candidate.get("why_safe_or_risky")),
            "suggested_review_question": _norm(candidate.get("suggested_review_question")),
            "expected_rule_type_if_confirmed": _norm(candidate.get("expected_rule_type_if_confirmed")),
            "review_instruction": (
                "Review this candidate manually. Because LONG_LABEL_REVIEW_REQUIRED is present, "
                "do not confirm scope noise unless the long narrative text is clearly contextual and non-core."
            ),
            "provenance_summary": _join_unique(
                [
                    _norm(candidate.get("representative_group_id")),
                    *candidate.get("source_group_ids", []),
                    *candidate.get("source_stage_signatures", []),
                ],
                limit=16,
            ),
        }
        review_records.append(review_record)

    review_df = pd.DataFrame(review_records).fillna("")
    duplicate_review_id_count = (
        int(review_df["scope_review_id"].astype(str).duplicated().sum()) if not review_df.empty else 0
    )
    default_all_pending = (
        not review_df.empty
        and review_df["reviewer_decision"].astype(str).eq(PENDING_HUMAN_SCOPE_REVIEW).all()
    )
    long_label_warning_present = (
        not review_df.empty
        and review_df["manual_review_warning"].astype(str).str.contains(
            "do not treat this long narrative label as a low-risk automatic scope exclusion",
            case=False,
            regex=False,
        ).all()
    )

    add_qa(
        "review_records::count",
        "PASS" if len(review_records) == 1 else "FAIL",
        f"actual={len(review_records)}",
    )
    add_qa(
        "review_records::default_pending_human_scope_review",
        "PASS" if default_all_pending else "FAIL",
        json.dumps(_decision_distribution(review_records), ensure_ascii=False),
    )
    add_qa(
        "review_records::unique_scope_review_id",
        "PASS" if duplicate_review_id_count == 0 else "FAIL",
        f"actual={duplicate_review_id_count}",
    )
    add_qa(
        "review_records::allowed_decisions_present",
        "PASS"
        if not review_df.empty
        and review_df["allowed_reviewer_decisions"].astype(str).eq(
            "CONFIRM_SCOPE_NOISE | REJECT_SCOPE_NOISE | NEEDS_MORE_INFO | ESCALATE_TO_ADJUDICATOR"
        ).all()
        else "FAIL",
        "CONFIRM_SCOPE_NOISE | REJECT_SCOPE_NOISE | NEEDS_MORE_INFO | ESCALATE_TO_ADJUDICATOR",
    )
    add_qa(
        "review_records::risk_flags_carried_forward",
        "PASS"
        if not review_df.empty and review_df["risk_flags"].astype(str).eq("").sum() == 0
        else "FAIL",
        review_df["risk_flags"].iloc[0] if not review_df.empty else "",
    )
    add_qa(
        "review_records::manual_warning_for_long_label",
        "PASS" if long_label_warning_present else "FAIL",
        review_df["manual_review_warning"].iloc[0] if not review_df.empty else "",
    )
    add_qa(
        "review_records::auto_scope_exclusion_disabled",
        "PASS"
        if not review_df.empty and review_df["auto_scope_exclusion_allowed"].astype(bool).eq(False).all()
        else "FAIL",
        "False",
    )
    add_qa(
        "review_records::provenance_present",
        "PASS"
        if not review_df.empty
        and review_df["source_group_ids"].astype(str).eq("").sum() == 0
        and review_df["provenance_summary"].astype(str).eq("").sum() == 0
        else "FAIL",
        review_df["provenance_summary"].iloc[0] if not review_df.empty else "",
    )
    add_qa(
        "review_records::sample_evidence_present",
        "PASS"
        if not review_df.empty
        and review_df["sample_row_texts"].astype(str).eq("").sum() == 0
        and review_df["sample_candidate_ids"].astype(str).eq("").sum() == 0
        else "FAIL",
        review_df["sample_row_texts"].iloc[0] if not review_df.empty else "",
    )

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )
    add_qa("safety::llm_not_called_confirmation", "PASS", "324B prepares deterministic human review only.")
    add_qa("safety::parser_not_run_confirmation", "PASS", "324B reads 324A outputs and cached evidence only.")

    review_instructions_df = pd.DataFrame(
        [
            {
                "section": "package_purpose",
                "instruction": "Review the single refined scope-noise candidate from 324A and decide whether it is safe to treat as scope noise, hold out, or escalate.",
            },
            {
                "section": "editable_fields",
                "instruction": "Edit reviewer_decision, reviewer_note, reviewer_name, and review_timestamp only.",
            },
            {
                "section": "allowed_decisions",
                "instruction": "Allowed reviewer_decision values: CONFIRM_SCOPE_NOISE, REJECT_SCOPE_NOISE, NEEDS_MORE_INFO, ESCALATE_TO_ADJUDICATOR.",
            },
            {
                "section": "long_label_warning",
                "instruction": "This candidate includes LONG_LABEL_REVIEW_REQUIRED. Do not treat the long narrative label as a low-risk automatic exclusion.",
            },
            {
                "section": "confirm_rule",
                "instruction": "Use CONFIRM_SCOPE_NOISE only if the narrative text is clearly contextual non-core noise after manual inspection of the sample evidence.",
            },
            {
                "section": "escalation_rule",
                "instruction": "Use ESCALATE_TO_ADJUDICATOR if the label still looks ambiguous enough to require a safer adjudicator request instead of direct sandbox replay.",
            },
        ]
    ).fillna("")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "324B",
        "mode": "prepare",
        "output_dir": "",
        "review_record_count": len(review_records),
        "pending_count": int(_decision_distribution(review_records).get(PENDING_HUMAN_SCOPE_REVIEW, 0)),
        "confirmed_scope_noise_count": 0,
        "rejected_scope_noise_count": 0,
        "needs_more_info_count": 0,
        "escalate_to_adjudicator_count": 0,
        "risk_flags_carried_forward": review_records[0]["risk_flags"] if review_records else "",
        "official_assets_not_modified_confirmed": True,
        "human_review_only_no_apply_confirmed": True,
        "validate_reviewed_mode_implemented": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_324B_PREPARE_DECISION if qa_fail_count == 0 else EXPECTED_324B_PREPARE_NOT_READY,
    }

    review_package_json = {
        "stage": "324B",
        "mode": "prepare",
        "decision": summary["decision"],
        "allowed_reviewer_decisions": sorted(ALLOWED_HUMAN_DECISIONS),
        "scope_review_records": [_to_jsonable(item) for item in review_records],
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
        "scope_review_records_df": review_df,
        "review_instructions_df": review_instructions_df,
        "review_package_json": review_package_json,
    }


def build_scope_noise_human_review_324b_validate_reviewed(
    reviewed_workbook: Path,
    summary_324a: Dict[str, Any],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    add_qa(
        "readiness::324a_decision",
        "PASS" if _norm(summary_324a.get("decision")) == EXPECTED_324A_DECISION else "FAIL",
        _norm(summary_324a.get("decision")),
    )
    add_qa(
        "readiness::324a_qa_fail_count",
        "PASS" if _safe_int(summary_324a.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_324a.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324a_refined_scope_candidate_count",
        "PASS" if _safe_int(summary_324a.get("refined_scope_candidate_count")) == 1 else "FAIL",
        str(summary_324a.get("refined_scope_candidate_count", "")),
    )

    reviewed_df = _read_workbook_sheet(reviewed_workbook, "scope_review_records")
    if reviewed_df.empty:
        reviewed_df = _read_workbook_sheet(reviewed_workbook, "all_reviewed_records")
    reviewed_df = reviewed_df.fillna("")

    required_columns = {
        "scope_review_id",
        "refined_scope_candidate_id",
        "reviewer_decision",
        "reviewer_note",
        "reviewer_name",
        "review_timestamp",
        "repaired_label",
        "source_group_ids",
        "affected_review_required_count",
        "risk_flags",
        "manual_review_warning",
        "auto_scope_exclusion_allowed",
    }
    missing_columns = sorted(required_columns.difference(set(reviewed_df.columns)))
    add_qa(
        "reviewed_integrity::required_columns_present",
        "PASS" if not missing_columns else "FAIL",
        "none" if not missing_columns else " | ".join(missing_columns),
    )

    records = reviewed_df.to_dict(orient="records") if not reviewed_df.empty else []
    add_qa(
        "reviewed_counts::review_record_count",
        "PASS" if len(records) == 1 else "FAIL",
        f"actual={len(records)}",
    )

    duplicate_review_id_count = (
        int(reviewed_df["scope_review_id"].astype(str).duplicated().sum()) if not reviewed_df.empty else 0
    )
    add_qa(
        "reviewed_integrity::unique_scope_review_id",
        "PASS" if duplicate_review_id_count == 0 else "FAIL",
        f"actual={duplicate_review_id_count}",
    )

    decisions = [_canonical_reviewer_decision(row.get("reviewer_decision")) for row in records]
    pending_count = sum(1 for decision in decisions if decision in {"", PENDING_HUMAN_SCOPE_REVIEW})
    invalid_decision_values = sorted(
        {decision for decision in decisions if decision and decision not in ALLOWED_HUMAN_DECISIONS}
    )
    confirmed_count = sum(1 for decision in decisions if decision == "CONFIRM_SCOPE_NOISE")
    rejected_count = sum(1 for decision in decisions if decision == "REJECT_SCOPE_NOISE")
    needs_more_info_count = sum(1 for decision in decisions if decision == "NEEDS_MORE_INFO")
    escalation_count = sum(1 for decision in decisions if decision == "ESCALATE_TO_ADJUDICATOR")

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
        "PASS" if confirmed_count + rejected_count + needs_more_info_count + escalation_count == 1 else "FAIL",
        json.dumps(
            {
                "confirmed": confirmed_count,
                "rejected": rejected_count,
                "needs_more_info": needs_more_info_count,
                "escalation": escalation_count,
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
        "reviewed_integrity::manual_warning_preserved",
        "PASS"
        if not reviewed_df.empty
        and reviewed_df["manual_review_warning"].astype(str).str.contains(
            "do not treat this long narrative label as a low-risk automatic scope exclusion",
            case=False,
            regex=False,
        ).all()
        else "FAIL",
        reviewed_df["manual_review_warning"].iloc[0] if not reviewed_df.empty else "",
    )
    add_qa(
        "reviewed_integrity::auto_scope_exclusion_still_disabled",
        "PASS"
        if not reviewed_df.empty and reviewed_df["auto_scope_exclusion_allowed"].astype(bool).eq(False).all()
        else "FAIL",
        "False",
    )
    add_qa(
        "reviewed_integrity::risk_flags_preserved",
        "PASS"
        if not reviewed_df.empty and reviewed_df["risk_flags"].astype(str).eq("").sum() == 0
        else "FAIL",
        reviewed_df["risk_flags"].iloc[0] if not reviewed_df.empty else "",
    )
    add_qa(
        "reviewed_integrity::sample_evidence_reference_present",
        "PASS"
        if not reviewed_df.empty
        and reviewed_df["source_group_ids"].astype(str).eq("").sum() == 0
        and reviewed_df["affected_review_required_count"].astype(str).eq("").sum() == 0
        else "FAIL",
        reviewed_df["source_group_ids"].iloc[0] if not reviewed_df.empty else "",
    )

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )
    add_qa("safety::llm_not_called_confirmation", "PASS", "324B validate-reviewed does not call LLM or adjudicator.")
    add_qa("safety::no_rule_application_confirmation", "PASS", "324B validate-reviewed only routes the reviewed decision.")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    if qa_fail_count == 0 and confirmed_count == 1:
        decision = EXPECTED_324B_REVIEWED_SANDBOX_DECISION
        next_route = "SANDBOX_REPLAY_324C"
    elif qa_fail_count == 0 and escalation_count == 1:
        decision = EXPECTED_324B_REVIEWED_ADJUDICATOR_DECISION
        next_route = "SAFE_ADJUDICATOR_REQUEST_PREP"
    else:
        decision = EXPECTED_324B_REVIEWED_NOT_READY
        next_route = "HOLDOUT_OR_MANUAL_FOLLOW_UP"

    routing_plan_json = {
        "stage": "324B",
        "mode": "validate-reviewed",
        "reviewed_workbook": str(reviewed_workbook),
        "decision": decision,
        "next_route": next_route,
        "confirmed_scope_noise_records": [
            _to_jsonable(row)
            for row in records
            if _canonical_reviewer_decision(row.get("reviewer_decision")) == "CONFIRM_SCOPE_NOISE"
        ],
        "escalated_to_adjudicator_records": [
            _to_jsonable(row)
            for row in records
            if _canonical_reviewer_decision(row.get("reviewer_decision")) == "ESCALATE_TO_ADJUDICATOR"
        ],
        "rejected_scope_noise_records": [
            _to_jsonable(row)
            for row in records
            if _canonical_reviewer_decision(row.get("reviewer_decision")) == "REJECT_SCOPE_NOISE"
        ],
        "needs_more_info_records": [
            _to_jsonable(row)
            for row in records
            if _canonical_reviewer_decision(row.get("reviewer_decision")) == "NEEDS_MORE_INFO"
        ],
    }

    summary = {
        "stage": "324B",
        "mode": "validate-reviewed",
        "output_dir": "",
        "review_record_count": len(records),
        "pending_count": pending_count,
        "confirmed_scope_noise_count": confirmed_count,
        "rejected_scope_noise_count": rejected_count,
        "needs_more_info_count": needs_more_info_count,
        "escalate_to_adjudicator_count": escalation_count,
        "risk_flags_carried_forward": reviewed_df["risk_flags"].iloc[0] if not reviewed_df.empty else "",
        "official_assets_not_modified_confirmed": True,
        "human_review_only_no_apply_confirmed": True,
        "validate_reviewed_mode_implemented": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": decision,
    }

    confirmed_df = (
        reviewed_df.loc[
            reviewed_df["reviewer_decision"].astype(str).map(_canonical_reviewer_decision) == "CONFIRM_SCOPE_NOISE"
        ].copy()
        if not reviewed_df.empty
        else pd.DataFrame()
    )
    escalated_df = (
        reviewed_df.loc[
            reviewed_df["reviewer_decision"].astype(str).map(_canonical_reviewer_decision) == "ESCALATE_TO_ADJUDICATOR"
        ].copy()
        if not reviewed_df.empty
        else pd.DataFrame()
    )
    rejected_df = (
        reviewed_df.loc[
            reviewed_df["reviewer_decision"].astype(str).map(_canonical_reviewer_decision) == "REJECT_SCOPE_NOISE"
        ].copy()
        if not reviewed_df.empty
        else pd.DataFrame()
    )
    needs_more_info_df = (
        reviewed_df.loc[
            reviewed_df["reviewer_decision"].astype(str).map(_canonical_reviewer_decision) == "NEEDS_MORE_INFO"
        ].copy()
        if not reviewed_df.empty
        else pd.DataFrame()
    )

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
        "escalated_df": escalated_df.fillna(""),
        "rejected_df": rejected_df.fillna(""),
        "needs_more_info_df": needs_more_info_df.fillna(""),
        "all_reviewed_df": reviewed_df.fillna(""),
        "routing_plan_json": routing_plan_json,
    }
