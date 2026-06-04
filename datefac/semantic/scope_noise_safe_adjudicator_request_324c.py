from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set

import pandas as pd


EXPECTED_324B_REVIEWED_DECISION = (
    "SCOPE_NOISE_HUMAN_REVIEW_324B_REVIEWED_READY_FOR_SAFE_ADJUDICATOR_REQUEST_PREP"
)
EXPECTED_324C_READY_DECISION = (
    "SCOPE_NOISE_SAFE_ADJUDICATOR_REQUEST_324C_READY_FOR_MANUAL_OR_CONFIGURED_ADJUDICATOR_RUN"
)
EXPECTED_324C_NOT_READY = "SCOPE_NOISE_SAFE_ADJUDICATOR_REQUEST_324C_NOT_READY"

DEFAULT_SCOPE_REFINEMENT_324A_DIR = Path(r"D:\_datefac\output\scope_noise_refinement_324a")
DEFAULT_REVIEWED_324B_DIR = Path(r"D:\_datefac\output\scope_noise_human_review_324b_reviewed")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\scope_noise_safe_adjudicator_request_324c")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

ALLOWED_RESPONSE_LABELS = [
    "ACCEPT_OUT_OF_SCOPE",
    "REJECT_OUT_OF_SCOPE",
    "NEEDS_MORE_INFO",
]

EXPECTED_RISK_FLAGS = [
    "INVALID_YEAR",
    "NO_YEAR_COLUMNS",
    "UNKNOWN_METRIC_CODE",
    "VALUE_PARSE_FAILED",
    "LONG_LABEL_REVIEW_REQUIRED",
]

REQUEST_REQUIRED_FIELDS = [
    "request_id",
    "source_scope_review_id",
    "source_refined_scope_candidate_id",
    "candidate_type",
    "candidate_label",
    "original_label",
    "candidate_question",
    "allowed_response_labels",
    "expected_rule_type_if_accepted",
    "sample_candidate_ids",
    "sample_texts",
    "affected_candidate_count",
    "affected_review_required_count",
    "priority_score",
    "risk_flags",
    "provenance",
    "safety_context",
    "response_schema",
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


def _split_pipe_string(value: Any) -> List[str]:
    clean = _norm(value)
    if not clean:
        return []
    return [_norm(part) for part in clean.split("|") if _norm(part)]


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


def _canonical_decision(value: Any) -> str:
    return _norm(value).upper()


def _build_response_schema() -> Dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "DateFacScopeNoiseSafeAdjudicatorResponse324C",
        "type": "object",
        "required": [
            "request_id",
            "response_label",
            "confidence",
            "rationale",
            "normalized_target_metric_if_any",
            "safety_flags",
            "needs_human_confirmation",
        ],
        "properties": {
            "request_id": {"type": "string"},
            "response_label": {"type": "string", "enum": ALLOWED_RESPONSE_LABELS},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "rationale": {"type": "string"},
            "normalized_target_metric_if_any": {"type": ["string", "null"]},
            "safety_flags": {"type": "array", "items": {"type": "string"}},
            "needs_human_confirmation": {"type": "boolean"},
        },
        "additionalProperties": False,
    }


def _build_request_id(scope_review_id: str) -> str:
    suffix = scope_review_id.replace("::", "__") or "scope_review_001"
    return f"324c::{suffix}"


def _request_missing_fields(request_item: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    for field in REQUEST_REQUIRED_FIELDS:
        if field not in request_item:
            missing.append(field)
            continue
        value = request_item.get(field)
        if field in {"allowed_response_labels", "sample_candidate_ids", "sample_texts", "risk_flags"}:
            if not isinstance(value, list) or not value:
                missing.append(field)
        elif field in {"provenance", "safety_context", "response_schema"}:
            if not isinstance(value, dict) or not value:
                missing.append(field)
        elif field in {"affected_candidate_count", "affected_review_required_count", "priority_score"}:
            continue
        elif _norm(value) == "":
            missing.append(field)
    return missing


def _flatten_request_item(request_item: Dict[str, Any]) -> Dict[str, Any]:
    provenance = request_item.get("provenance") if isinstance(request_item.get("provenance"), dict) else {}
    safety_context = (
        request_item.get("safety_context") if isinstance(request_item.get("safety_context"), dict) else {}
    )
    return {
        "request_id": _norm(request_item.get("request_id")),
        "source_scope_review_id": _norm(request_item.get("source_scope_review_id")),
        "source_refined_scope_candidate_id": _norm(request_item.get("source_refined_scope_candidate_id")),
        "candidate_type": _norm(request_item.get("candidate_type")),
        "candidate_label": _norm(request_item.get("candidate_label")),
        "original_label": _norm(request_item.get("original_label")),
        "candidate_question": _norm(request_item.get("candidate_question")),
        "allowed_response_labels": " | ".join(_flatten_sequence(request_item.get("allowed_response_labels"))),
        "expected_rule_type_if_accepted": _norm(request_item.get("expected_rule_type_if_accepted")),
        "affected_candidate_count": _safe_int(request_item.get("affected_candidate_count")),
        "affected_review_required_count": _safe_int(request_item.get("affected_review_required_count")),
        "priority_score": _safe_float(request_item.get("priority_score")),
        "risk_flags": " | ".join(_flatten_sequence(request_item.get("risk_flags"))),
        "sample_candidate_ids": " | ".join(_flatten_sequence(request_item.get("sample_candidate_ids"))),
        "sample_texts": " | ".join(_flatten_sequence(request_item.get("sample_texts"))),
        "sample_table_titles": _join_unique(provenance.get("sample_table_titles", []), limit=8),
        "sample_years": _join_unique(provenance.get("sample_years", []), limit=8),
        "sample_raw_metric_names": _join_unique(provenance.get("sample_raw_metric_names", []), limit=6),
        "representative_group_id": _norm(provenance.get("representative_group_id")),
        "source_group_ids": _join_unique(provenance.get("source_group_ids", []), limit=16),
        "source_stage_signatures": _join_unique(provenance.get("source_stage_signatures", []), limit=8),
        "manual_review_warning": _norm(provenance.get("manual_review_warning")),
        "reviewer_decision": _norm(provenance.get("reviewer_decision")),
        "reviewer_name": _norm(provenance.get("reviewer_name")),
        "reviewer_note": _norm(provenance.get("reviewer_note")),
        "prepare_only": bool(safety_context.get("prepare_only")),
        "llm_call_allowed_in_this_artifact": bool(
            safety_context.get("llm_call_allowed_in_this_artifact")
        ),
        "auto_scope_exclusion_allowed": bool(safety_context.get("auto_scope_exclusion_allowed")),
        "long_narrative_label": bool(safety_context.get("long_narrative_label")),
    }


def _build_evidence_row(
    request_item: Dict[str, Any],
    escalated_record: Dict[str, Any],
    refined_candidate: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "request_id": _norm(request_item.get("request_id")),
        "scope_review_id": _norm(escalated_record.get("scope_review_id")),
        "refined_scope_candidate_id": _norm(escalated_record.get("refined_scope_candidate_id")),
        "candidate_type": _norm(escalated_record.get("candidate_type")),
        "reviewer_decision": _norm(escalated_record.get("reviewer_decision")),
        "risk_flags": _norm(escalated_record.get("risk_flags")),
        "manual_review_warning": _norm(escalated_record.get("manual_review_warning")),
        "auto_scope_exclusion_allowed": _norm(escalated_record.get("auto_scope_exclusion_allowed")),
        "candidate_label": _norm(request_item.get("candidate_label")),
        "original_label": _norm(request_item.get("original_label")),
        "representative_group_id": _norm(refined_candidate.get("representative_group_id")),
        "source_group_ids": _join_unique(refined_candidate.get("source_group_ids", []), limit=16),
        "source_group_count": _safe_int(refined_candidate.get("source_group_count")),
        "duplicate_source_group_count": _safe_int(refined_candidate.get("duplicate_source_group_count")),
        "affected_candidate_count": _safe_int(refined_candidate.get("affected_candidate_count")),
        "affected_review_required_count": _safe_int(refined_candidate.get("affected_review_required_count")),
        "affected_report_count": _safe_int(refined_candidate.get("affected_report_count")),
        "priority_score_max": _safe_float(refined_candidate.get("priority_score_max")),
        "priority_score_sum": _safe_float(refined_candidate.get("priority_score_sum")),
        "sample_candidate_ids": _join_unique(refined_candidate.get("sample_candidate_ids", []), limit=16),
        "sample_raw_metric_names": _join_unique(refined_candidate.get("sample_raw_metric_names", []), limit=6),
        "sample_row_texts": _join_unique(refined_candidate.get("sample_row_texts", []), limit=8),
        "sample_table_titles": _join_unique(refined_candidate.get("sample_table_titles", []), limit=8),
        "sample_years": _join_unique(refined_candidate.get("sample_years", []), limit=8),
        "why_high_impact": _norm(refined_candidate.get("why_high_impact")),
        "why_safe_or_risky": _norm(refined_candidate.get("why_safe_or_risky")),
        "suggested_review_question": _norm(refined_candidate.get("suggested_review_question")),
        "risk_notes": _norm(refined_candidate.get("risk_notes")),
    }


def load_scope_noise_safe_adjudicator_request_324c_inputs(
    reviewed_dir: Path,
    scope_refinement_dir: Path,
) -> Dict[str, Any]:
    reviewed_workbook = reviewed_dir / "scope_noise_human_review_324b_reviewed_workbook.xlsx"
    refined_batch = _read_json(scope_refinement_dir / "scope_noise_refinement_324a_refined_batch.json")
    return {
        "reviewed_workbook_path": reviewed_workbook,
        "reviewed_summary": _read_json(reviewed_dir / "scope_noise_human_review_324b_reviewed_summary.json"),
        "reviewed_qa": _read_json(reviewed_dir / "scope_noise_human_review_324b_reviewed_qa.json"),
        "routing_plan": _read_json(reviewed_dir / "scope_noise_human_review_324b_final_routing_plan.json"),
        "all_reviewed_records_df": _read_workbook_sheet(reviewed_workbook, "all_reviewed_records"),
        "summary_324a": _read_json(scope_refinement_dir / "scope_noise_refinement_324a_summary.json"),
        "qa_324a": _read_json(scope_refinement_dir / "scope_noise_refinement_324a_qa.json"),
        "refined_batch_324a": refined_batch,
        "refined_scope_candidates": refined_batch.get("refined_scope_candidates", [])
        if isinstance(refined_batch.get("refined_scope_candidates"), list)
        else [],
    }


def build_scope_noise_safe_adjudicator_request_324c(inputs: Dict[str, Any]) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    reviewed_summary = inputs.get("reviewed_summary", {})
    reviewed_qa = inputs.get("reviewed_qa", {})
    routing_plan = inputs.get("routing_plan", {})
    all_reviewed_records_df = inputs.get("all_reviewed_records_df", pd.DataFrame()).fillna("")
    summary_324a = inputs.get("summary_324a", {})
    qa_324a = inputs.get("qa_324a", {})
    refined_scope_candidates = [
        item for item in inputs.get("refined_scope_candidates", []) if isinstance(item, dict)
    ]
    reviewed_workbook_path = inputs.get("reviewed_workbook_path", Path())

    add_qa(
        "readiness::324b_reviewed_decision",
        "PASS" if _norm(reviewed_summary.get("decision")) == EXPECTED_324B_REVIEWED_DECISION else "FAIL",
        _norm(reviewed_summary.get("decision")),
    )
    add_qa(
        "readiness::324b_reviewed_summary_qa_fail_count",
        "PASS" if _safe_int(reviewed_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(reviewed_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324b_reviewed_qa_json_fail_count",
        "PASS" if _safe_int(reviewed_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(reviewed_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324b_reviewed_review_record_count",
        "PASS" if _safe_int(reviewed_summary.get("review_record_count")) == 1 else "FAIL",
        str(reviewed_summary.get("review_record_count", "")),
    )
    add_qa(
        "readiness::324b_reviewed_escalate_count",
        "PASS" if _safe_int(reviewed_summary.get("escalate_to_adjudicator_count")) == 1 else "FAIL",
        str(reviewed_summary.get("escalate_to_adjudicator_count", "")),
    )
    add_qa(
        "readiness::324b_reviewed_confirmed_count",
        "PASS" if _safe_int(reviewed_summary.get("confirmed_scope_noise_count")) == 0 else "FAIL",
        str(reviewed_summary.get("confirmed_scope_noise_count", "")),
    )
    add_qa(
        "readiness::324b_reviewed_pending_count",
        "PASS" if _safe_int(reviewed_summary.get("pending_count")) == 0 else "FAIL",
        str(reviewed_summary.get("pending_count", "")),
    )
    add_qa(
        "readiness::324a_scope_refinement_decision",
        "PASS"
        if _norm(summary_324a.get("decision")) == "SCOPE_NOISE_REFINEMENT_324A_READY_FOR_SCOPE_REVIEW_BATCH"
        else "FAIL",
        _norm(summary_324a.get("decision")),
    )
    add_qa(
        "readiness::324a_scope_refinement_qa_fail_count",
        "PASS" if _safe_int(qa_324a.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_324a.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324a_refined_scope_candidate_count",
        "PASS" if len(refined_scope_candidates) == 1 else "FAIL",
        f"actual={len(refined_scope_candidates)}",
    )
    add_qa(
        "routing::reviewed_workbook_present",
        "PASS" if isinstance(reviewed_workbook_path, Path) and reviewed_workbook_path.exists() else "FAIL",
        str(reviewed_workbook_path),
    )

    reviewed_records = all_reviewed_records_df.to_dict(orient="records") if not all_reviewed_records_df.empty else []
    workbook_decisions = [_canonical_decision(row.get("reviewer_decision")) for row in reviewed_records]
    invalid_decision_values = sorted(
        {
            decision
            for decision in workbook_decisions
            if decision and decision not in {"CONFIRM_SCOPE_NOISE", "REJECT_SCOPE_NOISE", "NEEDS_MORE_INFO", "ESCALATE_TO_ADJUDICATOR"}
        }
    )
    workbook_pending_count = sum(1 for decision in workbook_decisions if decision in {"", "PENDING_HUMAN_SCOPE_REVIEW"})
    workbook_escalation_count = sum(1 for decision in workbook_decisions if decision == "ESCALATE_TO_ADJUDICATOR")

    add_qa(
        "routing::reviewed_workbook_record_count",
        "PASS" if len(reviewed_records) == 1 else "FAIL",
        f"actual={len(reviewed_records)}",
    )
    add_qa(
        "routing::reviewed_workbook_pending_count_zero",
        "PASS" if workbook_pending_count == 0 else "FAIL",
        str(workbook_pending_count),
    )
    add_qa(
        "routing::reviewed_workbook_invalid_decision_count_zero",
        "PASS" if not invalid_decision_values else "FAIL",
        "none" if not invalid_decision_values else " | ".join(invalid_decision_values),
    )
    add_qa(
        "routing::reviewed_workbook_escalation_count_one",
        "PASS" if workbook_escalation_count == 1 else "FAIL",
        str(workbook_escalation_count),
    )

    escalated_records = routing_plan.get("escalated_to_adjudicator_records", [])
    escalated_records = [item for item in escalated_records if isinstance(item, dict)]
    add_qa(
        "routing::final_routing_plan_decision",
        "PASS" if _norm(routing_plan.get("decision")) == EXPECTED_324B_REVIEWED_DECISION else "FAIL",
        _norm(routing_plan.get("decision")),
    )
    add_qa(
        "routing::next_route_safe_request_prep",
        "PASS" if _norm(routing_plan.get("next_route")) == "SAFE_ADJUDICATOR_REQUEST_PREP" else "FAIL",
        _norm(routing_plan.get("next_route")),
    )
    add_qa(
        "routing::single_escalated_record",
        "PASS" if len(escalated_records) == 1 else "FAIL",
        f"actual={len(escalated_records)}",
    )
    add_qa(
        "routing::no_confirmed_records_for_324c",
        "PASS" if not routing_plan.get("confirmed_scope_noise_records") else "FAIL",
        str(len(routing_plan.get("confirmed_scope_noise_records", []))),
    )
    add_qa(
        "routing::no_rejected_or_needs_more_info_records_for_324c",
        "PASS"
        if not routing_plan.get("rejected_scope_noise_records")
        and not routing_plan.get("needs_more_info_records")
        else "FAIL",
        (
            f"rejected={len(routing_plan.get('rejected_scope_noise_records', []))} "
            f"needs_more_info={len(routing_plan.get('needs_more_info_records', []))}"
        ),
    )

    refined_candidate = refined_scope_candidates[0] if refined_scope_candidates else {}
    refined_candidate_lookup = {
        _norm(item.get("refined_scope_candidate_id")): item for item in refined_scope_candidates if isinstance(item, dict)
    }
    escalated_record = escalated_records[0] if escalated_records else {}
    refined_scope_candidate_id = _norm(escalated_record.get("refined_scope_candidate_id"))
    if refined_scope_candidate_id:
        refined_candidate = refined_candidate_lookup.get(refined_scope_candidate_id, refined_candidate)

    risk_flags = _flatten_sequence(refined_candidate.get("risk_flags")) or _split_pipe_string(
        escalated_record.get("risk_flags")
    )
    risk_flags_joined = " | ".join(risk_flags)
    expected_risk_flags_joined = " | ".join(EXPECTED_RISK_FLAGS)

    add_qa(
        "request_inputs::refined_candidate_id_match",
        "PASS"
        if _norm(refined_candidate.get("refined_scope_candidate_id")) == refined_scope_candidate_id
        else "FAIL",
        (
            f"routing={refined_scope_candidate_id} "
            f"refined={_norm(refined_candidate.get('refined_scope_candidate_id'))}"
        ),
    )
    add_qa(
        "request_inputs::candidate_type_scope_noise",
        "PASS" if _norm(escalated_record.get("candidate_type")) == "scope_noise" else "FAIL",
        _norm(escalated_record.get("candidate_type")),
    )
    add_qa(
        "request_inputs::risk_flags_carried_forward",
        "PASS" if risk_flags_joined == expected_risk_flags_joined else "FAIL",
        risk_flags_joined,
    )
    add_qa(
        "request_inputs::manual_warning_preserved",
        "PASS"
        if "do not treat this long narrative label as a low-risk automatic scope exclusion"
        in _norm(escalated_record.get("manual_review_warning")).lower()
        else "FAIL",
        _norm(escalated_record.get("manual_review_warning")),
    )
    add_qa(
        "request_inputs::auto_scope_exclusion_disabled",
        "PASS" if str(escalated_record.get("auto_scope_exclusion_allowed")).lower() == "false" else "FAIL",
        str(escalated_record.get("auto_scope_exclusion_allowed")),
    )

    candidate_label = _norm(refined_candidate.get("repaired_label")) or _norm(escalated_record.get("repaired_label"))
    original_label = _norm(refined_candidate.get("original_label_examples")) or candidate_label
    priority_score = _safe_float(refined_candidate.get("priority_score_sum")) or _safe_float(
        escalated_record.get("priority_score_sum")
    )
    if priority_score == 0.0:
        priority_score = _safe_float(refined_candidate.get("priority_score_max")) or _safe_float(
            escalated_record.get("priority_score_max")
        )

    sample_candidate_ids = _flatten_sequence(refined_candidate.get("sample_candidate_ids")) or _split_pipe_string(
        escalated_record.get("sample_candidate_ids")
    )
    sample_texts = _flatten_sequence(refined_candidate.get("sample_row_texts")) or _split_pipe_string(
        escalated_record.get("sample_row_texts")
    )
    source_group_ids = _flatten_sequence(refined_candidate.get("source_group_ids")) or _split_pipe_string(
        escalated_record.get("source_group_ids")
    )
    source_stage_signatures = _flatten_sequence(refined_candidate.get("source_stage_signatures")) or _split_pipe_string(
        escalated_record.get("source_stage_signatures")
    )

    request_item = {
        "request_id": _build_request_id(_norm(escalated_record.get("scope_review_id"))),
        "source_scope_review_id": _norm(escalated_record.get("scope_review_id")),
        "source_refined_scope_candidate_id": refined_scope_candidate_id,
        "candidate_type": "scope_noise",
        "candidate_label": candidate_label,
        "original_label": original_label,
        "candidate_question": _norm(refined_candidate.get("suggested_review_question"))
        or _norm(escalated_record.get("suggested_review_question"))
        or (
            "Is this long narrative label clearly contextual non-core noise that may be treated "
            "as out-of-scope, or should it remain excluded from scope-noise rules?"
        ),
        "allowed_response_labels": list(ALLOWED_RESPONSE_LABELS),
        "expected_rule_type_if_accepted": "scope_noise",
        "sample_candidate_ids": sample_candidate_ids,
        "sample_texts": sample_texts,
        "affected_candidate_count": _safe_int(refined_candidate.get("affected_candidate_count"))
        or _safe_int(escalated_record.get("affected_candidate_count")),
        "affected_review_required_count": _safe_int(refined_candidate.get("affected_review_required_count"))
        or _safe_int(escalated_record.get("affected_review_required_count")),
        "priority_score": priority_score,
        "risk_flags": risk_flags,
        "provenance": {
            "source_stage": "324B_reviewed_scope_noise_human_review",
            "source_scope_review_id": _norm(escalated_record.get("scope_review_id")),
            "source_refined_scope_candidate_id": refined_scope_candidate_id,
            "representative_group_id": _norm(refined_candidate.get("representative_group_id"))
            or _norm(escalated_record.get("representative_group_id")),
            "source_group_ids": source_group_ids,
            "source_group_count": _safe_int(refined_candidate.get("source_group_count"))
            or _safe_int(escalated_record.get("source_group_count")),
            "duplicate_source_group_count": _safe_int(refined_candidate.get("duplicate_source_group_count"))
            or _safe_int(escalated_record.get("duplicate_source_group_count")),
            "source_stage_signatures": source_stage_signatures,
            "sample_table_titles": _flatten_sequence(refined_candidate.get("sample_table_titles"))
            or _split_pipe_string(escalated_record.get("sample_table_titles")),
            "sample_years": _flatten_sequence(refined_candidate.get("sample_years"))
            or _split_pipe_string(escalated_record.get("sample_years")),
            "sample_raw_metric_names": _flatten_sequence(refined_candidate.get("sample_raw_metric_names"))
            or _split_pipe_string(escalated_record.get("sample_raw_metric_names")),
            "why_high_impact": _norm(refined_candidate.get("why_high_impact"))
            or _norm(escalated_record.get("why_high_impact")),
            "why_safe_or_risky": _norm(refined_candidate.get("why_safe_or_risky"))
            or _norm(escalated_record.get("why_safe_or_risky")),
            "risk_notes": _norm(refined_candidate.get("risk_notes")) or _norm(escalated_record.get("risk_notes")),
            "manual_review_warning": _norm(escalated_record.get("manual_review_warning")),
            "review_instruction": _norm(escalated_record.get("review_instruction")),
            "reviewer_decision": _norm(escalated_record.get("reviewer_decision")),
            "reviewer_name": _norm(escalated_record.get("reviewer_name")),
            "reviewer_note": _norm(escalated_record.get("reviewer_note")),
            "reviewer_timestamp": _norm(escalated_record.get("review_timestamp")),
            "source_stage_chain": ["323A", "323A-R", "324A", "324B"],
        },
        "safety_context": {
            "stage": "324C_scope_noise_safe_adjudicator_request",
            "prepare_only": True,
            "llm_call_allowed_in_this_artifact": False,
            "do_not_apply_rules": True,
            "do_not_mark_trusted": True,
            "do_not_create_sandbox_replay_candidate": True,
            "requires_human_confirmation": True,
            "long_narrative_label": True,
            "auto_scope_exclusion_allowed": False,
            "manual_review_warning": _norm(escalated_record.get("manual_review_warning")),
            "adjudicator_caution": (
                "This is a long narrative label with LONG_LABEL_REVIEW_REQUIRED and must not be "
                "auto-accepted as scope noise."
            ),
        },
        "response_schema": _build_response_schema(),
    }

    request_items = [request_item] if refined_candidate else []
    missing_request_fields = {
        _norm(item.get("request_id")): _request_missing_fields(item)
        for item in request_items
        if _request_missing_fields(item)
    }

    add_qa(
        "request::single_request_built",
        "PASS" if len(request_items) == 1 else "FAIL",
        f"actual={len(request_items)}",
    )
    add_qa(
        "request::allowed_response_labels_match",
        "PASS" if request_item.get("allowed_response_labels") == ALLOWED_RESPONSE_LABELS else "FAIL",
        " | ".join(_flatten_sequence(request_item.get("allowed_response_labels"))),
    )
    add_qa(
        "request::response_schema_requires_expected_fields",
        "PASS"
        if _flatten_sequence(request_item.get("response_schema", {}).get("required")) == [
            "request_id",
            "response_label",
            "confidence",
            "rationale",
            "normalized_target_metric_if_any",
            "safety_flags",
            "needs_human_confirmation",
        ]
        else "FAIL",
        " | ".join(_flatten_sequence(request_item.get("response_schema", {}).get("required"))),
    )
    add_qa(
        "request::schema_completeness",
        "PASS" if not missing_request_fields else "FAIL",
        "none" if not missing_request_fields else json.dumps(missing_request_fields, ensure_ascii=False),
    )
    add_qa(
        "request::long_label_caution_present",
        "PASS"
        if "must not be auto-accepted" in _norm(request_item.get("safety_context", {}).get("adjudicator_caution")).lower()
        else "FAIL",
        _norm(request_item.get("safety_context", {}).get("adjudicator_caution")),
    )
    add_qa(
        "request::sample_evidence_present",
        "PASS" if sample_candidate_ids and sample_texts else "FAIL",
        f"sample_candidate_ids={len(sample_candidate_ids)} sample_texts={len(sample_texts)}",
    )

    llm_called = False
    add_qa("safety::llm_or_adjudicator_not_called", "PASS", f"llm_called={llm_called}")
    add_qa("safety::no_sandbox_replay_candidate_produced", "PASS", "324C prepares request artifacts only.")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after else "FAIL",
        (
            f"alias_before={alias_hash_before} alias_after={alias_hash_after} "
            f"scope_before={scope_hash_before} scope_after={scope_hash_after}"
        ),
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    request_items_df = pd.DataFrame([_flatten_request_item(item) for item in request_items]).fillna("")
    evidence_df = pd.DataFrame(
        [_build_evidence_row(request_item, escalated_record, refined_candidate)] if request_items else []
    ).fillna("")
    response_schema = request_item.get("response_schema", {})
    response_schema_df = pd.DataFrame(
        [
            {
                "required_fields": " | ".join(_flatten_sequence(response_schema.get("required"))),
                "response_label_enum": " | ".join(
                    _flatten_sequence(
                        response_schema.get("properties", {}).get("response_label", {}).get("enum", [])
                    )
                ),
                "confidence_enum": " | ".join(
                    _flatten_sequence(
                        response_schema.get("properties", {}).get("confidence", {}).get("enum", [])
                    )
                ),
                "needs_human_confirmation_type": _norm(
                    response_schema.get("properties", {}).get("needs_human_confirmation", {}).get("type")
                ),
            }
        ]
        if request_items
        else []
    ).fillna("")

    summary = {
        "stage": "324C",
        "mode": "prepare",
        "output_dir": "",
        "request_count": len(request_items),
        "scope_noise_request_count": len(request_items),
        "risk_flags_carried_forward": risk_flags_joined,
        "allowed_response_labels": " | ".join(ALLOWED_RESPONSE_LABELS),
        "llm_or_adjudicator_called": llm_called,
        "review_record_count": len(reviewed_records),
        "escalate_to_adjudicator_count": len(escalated_records),
        "confirmed_scope_noise_count": _safe_int(reviewed_summary.get("confirmed_scope_noise_count")),
        "pending_count": workbook_pending_count,
        "invalid_decision_count": len(invalid_decision_values),
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_324C_READY_DECISION if qa_fail_count == 0 else EXPECTED_324C_NOT_READY,
    }

    request_package_json = {
        "stage": "324C",
        "mode": "prepare",
        "decision": summary["decision"],
        "request_count": len(request_items),
        "request_items": request_items,
    }
    schema_json = {
        "request_required_fields": REQUEST_REQUIRED_FIELDS,
        "allowed_response_labels": ALLOWED_RESPONSE_LABELS,
        "response_schema": _build_response_schema(),
    }
    manual_prompt_md = "\n".join(
        [
            "# Scope Noise Safe Adjudicator Request 324C",
            "",
            "You are reviewing one escalated scope-noise candidate from a prior human review stage.",
            "",
            "Safety rules:",
            "- This is a long narrative label with LONG_LABEL_REVIEW_REQUIRED.",
            "- Do not auto-accept it as scope noise.",
            "- Choose only from: ACCEPT_OUT_OF_SCOPE, REJECT_OUT_OF_SCOPE, NEEDS_MORE_INFO.",
            "- Do not apply rules, mark anything trusted, or produce sandbox replay results.",
            "- Return JSON only and follow the response_schema exactly.",
            "- Set needs_human_confirmation to true.",
            "- For ACCEPT_OUT_OF_SCOPE, normalized_target_metric_if_any should be empty or null.",
            "",
            "Request payload:",
            "```json",
            json.dumps(request_package_json, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    notes_md = "\n".join(
        [
            "# Scope Noise Safe Adjudicator Request 324C",
            "",
            "## Purpose",
            "- Prepare one safe adjudicator request for the single 324B-escalated long-narrative scope candidate.",
            "- No LLM/adjudicator call occurred in this stage.",
            "- No sandbox replay candidate is produced in 324C.",
            "",
            "## Caution",
            "- This candidate carries LONG_LABEL_REVIEW_REQUIRED and must not be auto-accepted.",
            f"- Risk flags: {risk_flags_joined}",
            "",
            "## Decision",
            f"- decision: {summary['decision']}",
            "",
        ]
    )
    no_apply_proof_json = {
        "files_read": [
            str(inputs.get("reviewed_workbook_path", "")),
            str(DEFAULT_REVIEWED_324B_DIR / "scope_noise_human_review_324b_reviewed_summary.json"),
            str(DEFAULT_REVIEWED_324B_DIR / "scope_noise_human_review_324b_reviewed_qa.json"),
            str(DEFAULT_REVIEWED_324B_DIR / "scope_noise_human_review_324b_final_routing_plan.json"),
            str(DEFAULT_SCOPE_REFINEMENT_324A_DIR / "scope_noise_refinement_324a_summary.json"),
            str(DEFAULT_SCOPE_REFINEMENT_324A_DIR / "scope_noise_refinement_324a_qa.json"),
            str(DEFAULT_SCOPE_REFINEMENT_324A_DIR / "scope_noise_refinement_324a_refined_batch.json"),
        ],
        "files_written": [],
        "official_target_files_not_modified": [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_ALIAS_OVERRIDE_PATH),
        ],
        "output_only_write_confirmation": True,
        "decision": "scope_noise_safe_adjudicator_request_prepare_only_no_apply",
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
        "request_items": request_items,
        "request_items_df": request_items_df,
        "evidence_df": evidence_df,
        "response_schema_df": response_schema_df,
        "request_package_json": request_package_json,
        "schema_json": schema_json,
        "manual_prompt_md": manual_prompt_md,
        "notes_md": notes_md,
        "no_apply_proof_json": no_apply_proof_json,
    }
