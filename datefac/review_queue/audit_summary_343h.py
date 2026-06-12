from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text


READY_DECISION_343H = "AI_ASSISTED_SPOT_CHECK_AUDIT_SUMMARY_343H_READY"
NOT_READY_DECISION_343H = "AI_ASSISTED_SPOT_CHECK_AUDIT_SUMMARY_343H_NOT_READY"
RECOMMENDED_343I_SCOPE = "strict_human_review_package_for_ai_assisted_confirmed_rows"

AI_ASSISTED_ONLY_REASON = (
    "AI-assisted review and spot-check are pilot validation artifacts, "
    "not strict human approval"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_chain_overview_rows(
    *,
    summary_343a: Dict[str, Any],
    summary_343d: Dict[str, Any],
    summary_343e: Dict[str, Any],
    summary_343f: Dict[str, Any],
    summary_343g: Dict[str, Any],
) -> List[Dict[str, Any]]:
    return [
        {
            "milestone_id": "343A",
            "decision": summary_343a.get("decision", ""),
            "input_row_count": summary_343a.get("sample_queue_item_count", 0),
            "output_row_count": summary_343a.get("sample_queue_item_count", 0),
            "review_source_type": "SCHEMA_ONLY",
            "processing_mode": "QUEUE_SCHEMA_AND_UI_CONTRACT",
            "ready_flag": summary_343a.get("ready_for_343b", False),
            "downstream_limitation": "Schema only; not review evidence",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
        {
            "milestone_id": "343D",
            "decision": summary_343d.get("decision", ""),
            "input_row_count": summary_343d.get("filled_row_count", 0),
            "output_row_count": summary_343d.get("valid_row_count", 0),
            "review_source_type": summary_343d.get("review_source_type", ""),
            "processing_mode": "AI_ASSISTED_REVIEW_INGESTION",
            "ready_flag": summary_343d.get("ready_for_343e", False),
            "downstream_limitation": "AI-assisted review only; human spot-check still required",
            "formal_client_export_allowed": summary_343d.get("formal_client_export_allowed", False),
            "client_ready": summary_343d.get("client_ready", False),
            "production_ready": summary_343d.get("production_ready", False),
        },
        {
            "milestone_id": "343E",
            "decision": summary_343e.get("decision", ""),
            "input_row_count": summary_343e.get("input_reviewed_result_row_count", 0),
            "output_row_count": summary_343e.get("apply_plan_row_count", 0),
            "review_source_type": summary_343e.get("review_source_type", ""),
            "processing_mode": summary_343e.get("apply_mode", ""),
            "ready_flag": summary_343e.get("ready_for_343f", False),
            "downstream_limitation": "Simulation only; no real apply or export",
            "formal_client_export_allowed": summary_343e.get("formal_client_export_allowed", False),
            "client_ready": summary_343e.get("client_ready", False),
            "production_ready": summary_343e.get("production_ready", False),
        },
        {
            "milestone_id": "343F",
            "decision": summary_343f.get("decision", ""),
            "input_row_count": summary_343f.get("input_apply_plan_row_count", 0),
            "output_row_count": summary_343f.get("spot_check_item_count", 0),
            "review_source_type": summary_343f.get("review_source_type", ""),
            "processing_mode": "AI_ASSISTED_SPOT_CHECK_PACKAGE",
            "ready_flag": summary_343f.get("waiting_for_spot_check", False),
            "downstream_limitation": "Workbook package only; waiting for filled spot-check result",
            "formal_client_export_allowed": summary_343f.get("formal_client_export_allowed", False),
            "client_ready": summary_343f.get("client_ready", False),
            "production_ready": summary_343f.get("production_ready", False),
        },
        {
            "milestone_id": "343G",
            "decision": summary_343g.get("decision", ""),
            "input_row_count": summary_343g.get("filled_spot_check_row_count", 0),
            "output_row_count": summary_343g.get("valid_row_count", 0),
            "review_source_type": summary_343g.get("spot_check_source_type", ""),
            "processing_mode": summary_343g.get("apply_mode", ""),
            "ready_flag": summary_343g.get("ready_for_343h", False),
            "downstream_limitation": "AI-assisted spot-check only; strict human review still required",
            "formal_client_export_allowed": summary_343g.get("formal_client_export_allowed", False),
            "client_ready": summary_343g.get("client_ready", False),
            "production_ready": summary_343g.get("production_ready", False),
        },
    ]


def build_confirmed_ai_assisted_items(result_rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in result_rows:
        if normalize_text(row.get("spot_check_decision")) != "CONFIRM_AI_ASSISTED_RESULT":
            continue
        if normalize_text(row.get("resulting_spot_check_status")) != "SPOT_CHECK_CONFIRMED_AI_ASSISTED":
            continue
        copied = dict(row)
        copied["strict_human_confirmation_available"] = False
        copied["confirmation_scope_note"] = (
            "AI-assisted spot-check confirmed only; not strict human confirmed"
        )
        rows.append(copied)
    return rows


def build_source_check_backlog_rows(
    *,
    result_rows: Iterable[Dict[str, Any]],
    source_check_todo_rows: Iterable[Dict[str, Any]],
    apply_plan_rows: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    backlog_index: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def key_for(row: Dict[str, Any]) -> Tuple[str, str]:
        queue_item_id = normalize_text(row.get("queue_item_id"))
        review_item_id = normalize_text(row.get("review_item_id"))
        return (queue_item_id, review_item_id or queue_item_id)

    for row in source_check_todo_rows:
        key = key_for(row)
        backlog_index[key] = {
            "queue_item_id": key[0],
            "review_item_id": key[1],
            "backlog_source": "343F_SOURCE_CHECK_TODO",
            "reason": normalize_text(row.get("reason_for_source_check")),
            "suggested_action": normalize_text(row.get("suggested_reviewer_action")),
            "source_stage": normalize_text(row.get("source_stage")),
            "source_artifact_path": normalize_text(row.get("source_artifact_path")),
            "source_artifact_sheet": normalize_text(row.get("source_artifact_sheet")),
            "source_row_id": normalize_text(row.get("source_row_id")),
            "review_source_type": "AI_ASSISTED_REVIEW",
            "spot_check_source_type": "AI_ASSISTED_SPOT_CHECK",
            "not_pure_human_review": True,
            "strict_human_review_completed": False,
            "requires_strict_human_review": True,
            "apply_mode": "SIMULATION_ONLY",
        }

    for row in apply_plan_rows:
        if normalize_text(row.get("simulated_downstream_action")) != "HOLD_SOURCE_CHECK_REQUIRED":
            continue
        key = key_for(row)
        merged = backlog_index.get(
            key,
            {
                "queue_item_id": key[0],
                "review_item_id": key[1],
                "backlog_source": "343E_APPLY_PLAN",
                "review_source_type": "AI_ASSISTED_REVIEW",
                "spot_check_source_type": "AI_ASSISTED_SPOT_CHECK",
                "not_pure_human_review": True,
                "strict_human_review_completed": False,
                "requires_strict_human_review": True,
                "apply_mode": "SIMULATION_ONLY",
            },
        )
        merged["apply_plan_action"] = normalize_text(row.get("simulated_downstream_action"))
        merged["apply_plan_risk_notes"] = row.get("risk_notes", [])
        backlog_index[key] = merged

    for row in result_rows:
        if normalize_text(row.get("spot_check_decision")) != "SOURCE_CHECK_REQUIRED":
            continue
        key = key_for(row)
        merged = backlog_index.get(
            key,
            {
                "queue_item_id": key[0],
                "review_item_id": key[1],
                "backlog_source": "343G_RESULT",
                "review_source_type": "AI_ASSISTED_REVIEW",
                "spot_check_source_type": "AI_ASSISTED_SPOT_CHECK",
                "not_pure_human_review": True,
                "strict_human_review_completed": False,
                "requires_strict_human_review": True,
                "apply_mode": "SIMULATION_ONLY",
            },
        )
        merged["backlog_source"] = "343G_RESULT"
        merged["spot_check_decision"] = normalize_text(row.get("spot_check_decision"))
        merged["resulting_spot_check_status"] = normalize_text(row.get("resulting_spot_check_status"))
        merged["spot_check_note"] = normalize_text(row.get("spot_check_note"))
        merged["priority_tier"] = normalize_text(row.get("priority_tier"))
        merged["simulated_downstream_action"] = normalize_text(row.get("simulated_downstream_action"))
        backlog_index[key] = merged

    return list(backlog_index.values())


def build_gap_items(
    *,
    result_rows: Iterable[Dict[str, Any]],
    client_export_gate: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in result_rows:
        decision = normalize_text(row.get("spot_check_decision"))
        gap_category = ""
        gap_reason = ""
        next_action = ""
        if decision == "CONFIRM_AI_ASSISTED_RESULT":
            gap_category = "STRICT_HUMAN_CONFIRMATION_MISSING"
            gap_reason = "AI-assisted confirmed row still lacks strict human confirmation"
            next_action = "Include in strict human review package"
        elif decision == "SOURCE_CHECK_REQUIRED":
            gap_category = "SOURCE_CHECK_BACKLOG"
            gap_reason = "Source evidence remains insufficient for stronger trust claim"
            next_action = "Resolve source check evidence"
        elif decision in {"KEEP_HOLD", "SKIP_SPOT_CHECK"}:
            gap_category = "UNRESOLVED_HOLD_OR_SKIP"
            gap_reason = "Row remains unresolved after AI-assisted spot-check"
            next_action = "Re-review or escalate to strict human review"
        elif decision == "REJECT_AI_ASSISTED_RESULT":
            gap_category = "REJECTED_NOT_EXPORTABLE"
            gap_reason = "Rejected row must not enter export candidate path"
            next_action = "Keep excluded from downstream export"
        elif decision == "CORRECT_AI_ASSISTED_RESULT":
            gap_category = "STRICT_HUMAN_CORRECTION_CONFIRMATION_MISSING"
            gap_reason = "AI-assisted correction still lacks strict human approval"
            next_action = "Validate correction under strict human review"
        else:
            continue
        rows.append(
            {
                "queue_item_id": normalize_text(row.get("queue_item_id")),
                "review_item_id": normalize_text(row.get("review_item_id")),
                "gap_category": gap_category,
                "spot_check_decision": decision,
                "resulting_spot_check_status": normalize_text(row.get("resulting_spot_check_status")),
                "gap_reason": gap_reason,
                "next_action": next_action,
                "formal_client_export_allowed": client_export_gate["formal_client_export_allowed"],
                "client_ready": client_export_gate["client_ready"],
                "production_ready": client_export_gate["production_ready"],
                "strict_human_review_completed": False,
                "requires_strict_human_review": True,
                "review_source_type": "AI_ASSISTED_REVIEW",
                "spot_check_source_type": "AI_ASSISTED_SPOT_CHECK",
                "apply_mode": "SIMULATION_ONLY",
            }
        )
    return rows


def build_client_export_gate() -> Dict[str, Any]:
    return {
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "strict_human_review_completed": False,
        "requires_strict_human_review": True,
        "ai_assisted_only": True,
        "reason": AI_ASSISTED_ONLY_REASON,
    }


def build_next_action_plan() -> Dict[str, Any]:
    return {
        "recommended_343i_scope": RECOMMENDED_343I_SCOPE,
        "default_recommendation_reason": (
            "Strict human review for the 10 AI-assisted confirmed rows directly addresses "
            "the formal gap for the only simulated-applied rows."
        ),
        "options": [
            {
                "option_id": "343I_STRICT_HUMAN_REVIEW_PACKAGE",
                "title": "Strict human review package for AI-assisted confirmed rows",
                "target_row_count": 10,
                "priority": "RECOMMENDED",
                "why": "Directly validates the only rows currently AI-assisted confirmed after spot-check.",
            },
            {
                "option_id": "343I_SOURCE_CHECK_RESOLUTION_PACKAGE",
                "title": "Source-check resolution package",
                "target_row_count": 19,
                "priority": "SECONDARY",
                "why": "Clears the uncertainty backlog before any broader downstream trust claim.",
            },
        ],
    }
