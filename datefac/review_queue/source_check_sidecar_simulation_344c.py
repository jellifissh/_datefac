from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from datefac.review_queue.excel_round_trip_343b import normalize_float, normalize_text


READY_DECISION_344C = "SOURCE_CHECK_SIDECAR_SIMULATION_344C_READY"
NOT_READY_DECISION_344C = "SOURCE_CHECK_SIDECAR_SIMULATION_344C_NOT_READY"
RECOMMENDED_344D_SCOPE_344C = (
    "expanded_trusted_export_package_generation_for_review_demo_only"
)
EXPANDED_TRUST_SCOPE_344C = "343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED"

SOURCE_CHECK_ACTION_TO_APPLY_ACTION_344C = {
    "SOURCE_CHECK_CONFIRMED": "SIMULATE_APPLY_SOURCE_CHECK_CONFIRM",
    "SOURCE_CHECK_CORRECTED": "SIMULATE_APPLY_SOURCE_CHECK_CORRECTION",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalized_numeric_text(value: Any) -> str:
    numeric = normalize_float(value)
    if numeric is None:
        return normalize_text(value)
    return f"{numeric:g}"


def build_source_check_apply_plan_row(
    sidecar_row: Dict[str, Any],
) -> Dict[str, Any]:
    sidecar_action = normalize_text(sidecar_row.get("sidecar_action"))
    apply_action = SOURCE_CHECK_ACTION_TO_APPLY_ACTION_344C.get(sidecar_action, "")
    is_correction = sidecar_action == "SOURCE_CHECK_CORRECTED"
    return {
        "backlog_item_key": normalize_text(sidecar_row.get("backlog_item_key")),
        "queue_item_id": normalize_text(sidecar_row.get("queue_item_id")),
        "review_item_id": normalize_text(sidecar_row.get("review_item_id")),
        "source_row_id": normalize_text(sidecar_row.get("source_row_id")),
        "sidecar_action": sidecar_action,
        "apply_action": apply_action,
        "apply_status": "READY",
        "apply_block_reason": "",
        "final_metric_standardized": normalize_text(
            sidecar_row.get("final_metric_standardized")
        ),
        "final_year_standardized": normalize_text(
            sidecar_row.get("final_year_standardized")
        ),
        "final_value_numeric": _normalized_numeric_text(
            sidecar_row.get("final_value_numeric")
        ),
        "final_normalized_unit": normalize_text(
            sidecar_row.get("final_normalized_unit")
        ),
        "source_check_status": normalize_text(sidecar_row.get("source_check_status")),
        "source_check_decision": normalize_text(
            sidecar_row.get("source_check_decision")
        ),
        "source_check_note": normalize_text(sidecar_row.get("source_check_note")),
        "source_checker_id": normalize_text(sidecar_row.get("source_checker_id")),
        "source_checked_at": normalize_text(sidecar_row.get("source_checked_at")),
        "source_pdf_name": normalize_text(sidecar_row.get("source_pdf_name")),
        "page_number": normalize_text(sidecar_row.get("page_number")),
        "table_id": normalize_text(sidecar_row.get("table_id")),
        "bbox": normalize_text(sidecar_row.get("bbox")),
        "image_path": normalize_text(sidecar_row.get("image_path")),
        "source_text_snippet": normalize_text(sidecar_row.get("source_text_snippet")),
        "source_html_snippet": normalize_text(sidecar_row.get("source_html_snippet")),
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "correction_applied": is_correction,
    }


def build_source_check_applied_sidecar_row(
    apply_plan_row: Dict[str, Any],
    source_row: Dict[str, Any],
) -> Dict[str, Any]:
    row = dict(source_row)
    row.update(
        {
            "simulated_apply_action": normalize_text(apply_plan_row.get("apply_action")),
            "simulated_apply_status": "APPLIED",
            "source_check_sidecar_apply_simulation_completed": True,
            "applied_metric_standardized": normalize_text(
                apply_plan_row.get("final_metric_standardized")
            ),
            "applied_year_standardized": normalize_text(
                apply_plan_row.get("final_year_standardized")
            ),
            "applied_value_numeric": _normalized_numeric_text(
                apply_plan_row.get("final_value_numeric")
            ),
            "applied_normalized_unit": normalize_text(
                apply_plan_row.get("final_normalized_unit")
            ),
            "correction_applied": bool(apply_plan_row.get("correction_applied")),
            "expanded_trusted_scope": EXPANDED_TRUST_SCOPE_344C,
            "source_lineage_stage": "344B_SOURCE_CHECK",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "global_strict_human_review_completed": False,
        }
    )
    return row


def build_expanded_trusted_candidate_from_demo_row(
    row: Dict[str, Any],
) -> Dict[str, Any]:
    candidate = dict(row)
    candidate.update(
        {
            "expanded_trusted_scope": EXPANDED_TRUST_SCOPE_344C,
            "source_lineage_stage": "343N_DEMO",
            "expanded_trust_source": "PRIOR_DEMO_TRUSTED_ARC",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "global_strict_human_review_completed": False,
        }
    )
    return candidate


def build_expanded_trusted_candidate_from_source_check_row(
    row: Dict[str, Any],
) -> Dict[str, Any]:
    candidate = dict(row)
    candidate.update(
        {
            "metric_standardized": normalize_text(row.get("applied_metric_standardized")),
            "year_standardized": normalize_text(row.get("applied_year_standardized")),
            "value_numeric": _normalized_numeric_text(row.get("applied_value_numeric")),
            "normalized_unit": normalize_text(row.get("applied_normalized_unit")),
            "expanded_trusted_scope": EXPANDED_TRUST_SCOPE_344C,
            "source_lineage_stage": "344B_SOURCE_CHECK",
            "expanded_trust_source": "SOURCE_CHECK_APPLIED_SIDECAR",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "global_strict_human_review_completed": False,
        }
    )
    return candidate


def dedup_identity_key(row: Dict[str, Any]) -> str:
    return "||".join(
        [
            normalize_text(row.get("queue_item_id")),
            normalize_text(row.get("review_item_id")),
            normalize_text(row.get("metric_standardized")),
            normalize_text(row.get("year_standardized")),
            _normalized_numeric_text(row.get("value_numeric")),
            normalize_text(row.get("normalized_unit")),
            normalize_text(row.get("source_pdf_name")),
            normalize_text(row.get("page_number")),
            normalize_text(row.get("table_id")),
        ]
    )


def build_dedup_audit_rows(
    candidate_rows: Iterable[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    audit_rows: List[Dict[str, Any]] = []
    canonical_rows: List[Dict[str, Any]] = []
    seen: Dict[str, Dict[str, Any]] = {}
    dedup_conflict_count = 0

    for row in candidate_rows:
        key = dedup_identity_key(row)
        if key not in seen:
            seen[key] = row
            canonical_rows.append(row)
            audit_rows.append(
                {
                    "dedup_key": key,
                    "dedup_status": "UNIQUE",
                    "canonical_queue_item_id": normalize_text(row.get("queue_item_id")),
                    "canonical_review_item_id": normalize_text(row.get("review_item_id")),
                    "source_lineage_stage": normalize_text(row.get("source_lineage_stage")),
                    "conflict_detail": "",
                }
            )
            continue

        existing = seen[key]
        compatible = (
            normalize_text(existing.get("metric_standardized"))
            == normalize_text(row.get("metric_standardized"))
            and normalize_text(existing.get("year_standardized"))
            == normalize_text(row.get("year_standardized"))
            and _normalized_numeric_text(existing.get("value_numeric"))
            == _normalized_numeric_text(row.get("value_numeric"))
            and normalize_text(existing.get("normalized_unit"))
            == normalize_text(row.get("normalized_unit"))
        )
        if compatible:
            lineage = list(
                dict.fromkeys(
                    [
                        normalize_text(existing.get("source_lineage_stage")),
                        normalize_text(row.get("source_lineage_stage")),
                    ]
                )
            )
            existing["merged_source_lineage_stages"] = lineage
            audit_rows.append(
                {
                    "dedup_key": key,
                    "dedup_status": "COMPATIBLE_DUPLICATE_MERGED",
                    "canonical_queue_item_id": normalize_text(existing.get("queue_item_id")),
                    "canonical_review_item_id": normalize_text(existing.get("review_item_id")),
                    "source_lineage_stage": normalize_text(row.get("source_lineage_stage")),
                    "conflict_detail": "Identical values merged into canonical row.",
                }
            )
        else:
            dedup_conflict_count += 1
            audit_rows.append(
                {
                    "dedup_key": key,
                    "dedup_status": "CONFLICT",
                    "canonical_queue_item_id": normalize_text(existing.get("queue_item_id")),
                    "canonical_review_item_id": normalize_text(existing.get("review_item_id")),
                    "source_lineage_stage": normalize_text(row.get("source_lineage_stage")),
                    "conflict_detail": "Duplicate key has incompatible values or lineage.",
                }
            )
    return audit_rows, canonical_rows, dedup_conflict_count


def build_expanded_trust_gate(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_check_sidecar_apply_simulation_completed": summary.get(
            "source_check_sidecar_apply_simulation_completed", False
        ),
        "source_check_applied_sidecar_generated": summary.get(
            "source_check_applied_sidecar_generated", False
        ),
        "expanded_trusted_candidates_generated": summary.get(
            "expanded_trusted_candidates_generated", False
        ),
        "expanded_trust_gate_evaluated": summary.get(
            "expanded_trust_gate_evaluated", False
        ),
        "dedup_audit_generated": summary.get("dedup_audit_generated", False),
        "source_check_backlog_resolved": summary.get(
            "source_check_backlog_resolved", False
        ),
        "prior_demo_trusted_row_count": summary.get("prior_demo_trusted_row_count", 0),
        "source_check_trusted_row_count": summary.get(
            "source_check_trusted_row_count", 0
        ),
        "expanded_trusted_candidate_count": summary.get(
            "expanded_trusted_candidate_count", 0
        ),
        "deduplicated_expanded_trusted_candidate_count": summary.get(
            "deduplicated_expanded_trusted_candidate_count", 0
        ),
        "dedup_conflict_count": summary.get("dedup_conflict_count", 0),
        "expanded_trusted_scope": summary.get("expanded_trusted_scope", ""),
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "ready_for_344d": summary.get("ready_for_344d", False),
        "recommended_344d_scope": summary.get("recommended_344d_scope", ""),
        "reason": (
            "Expanded trusted coverage exists only as a sidecar simulation. "
            "Formal client export and production readiness remain blocked."
        ),
    }


def build_scope_boundary_lines() -> List[str]:
    return [
        "344C only simulates applying the 19 source-check resolved rows from 344B.",
        "344C combines those 19 rows with the prior 10-row demo trusted arc from 343O/343N.",
        "Expanded trusted coverage reaches 29 rows only as a sidecar simulation if dedup passes.",
        "No production data was written back.",
        "No formal client export was generated.",
        "formal_client_export_allowed must remain false.",
        "client_ready must remain false.",
        "production_ready must remain false.",
        "global_strict_human_review_completed must remain false.",
        "The next safe task is 344D expanded trusted export package generation for review/demo only.",
    ]

