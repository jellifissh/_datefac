from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from datefac.review_queue.excel_round_trip_343b import normalize_float, normalize_text


READY_DECISION_344D = "EXPANDED_TRUSTED_DEMO_EXPORT_PACKAGE_344D_READY"
NOT_READY_DECISION_344D = "EXPANDED_TRUSTED_DEMO_EXPORT_PACKAGE_344D_NOT_READY"
RECOMMENDED_344E_SCOPE_344D = (
    "expanded_trusted_demo_audit_snapshot_and_final_handoff_summary"
)
EXPANDED_EXPORT_SCOPE_344D = "343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED"
EXPORT_USAGE_344D = "REVIEW_DEMO_ONLY"

BASE_AUDIT_LABELS_344D = [
    "EXPANDED_TRUSTED_CANDIDATE",
    "REVIEW_DEMO_ONLY",
    "NOT_FORMAL_CLIENT_EXPORT",
    "NOT_PRODUCTION_READY",
    "NO_PRODUCTION_WRITE_BACK",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalized_numeric_text(value: Any) -> str:
    numeric = normalize_float(value)
    if numeric is None:
        return normalize_text(value)
    return f"{numeric:g}"


def build_expanded_export_row(candidate_row: Dict[str, Any]) -> Dict[str, Any]:
    row = dict(candidate_row)
    source_lineage_stage = normalize_text(candidate_row.get("source_lineage_stage"))
    row.update(
        {
            "expanded_export_scope": EXPANDED_EXPORT_SCOPE_344D,
            "export_usage": EXPORT_USAGE_344D,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "global_strict_human_review_completed": False,
            "source_lineage_summary": (
                "Prior 10-row demo trusted arc"
                if source_lineage_stage == "343N_DEMO"
                else "344B source-check resolved sidecar"
            ),
            "value_numeric": _normalized_numeric_text(candidate_row.get("value_numeric")),
        }
    )
    return row


def build_audit_label_row(export_row: Dict[str, Any]) -> Dict[str, Any]:
    labels = list(BASE_AUDIT_LABELS_344D)
    source_lineage_stage = normalize_text(export_row.get("source_lineage_stage"))
    if source_lineage_stage == "343N_DEMO":
        labels.append("PACKAGE_SCOPE_HUMAN_CONFIRMED")
    if source_lineage_stage == "344B_SOURCE_CHECK":
        labels.append("SOURCE_CHECK_RESOLVED")
        source_check_status = normalize_text(export_row.get("source_check_status"))
        if source_check_status == "CONFIRMED":
            labels.append("SOURCE_CHECK_CONFIRMED")
        if source_check_status == "CORRECTED":
            labels.append("SOURCE_CHECK_CORRECTED")
    return {
        "queue_item_id": normalize_text(export_row.get("queue_item_id")),
        "review_item_id": normalize_text(export_row.get("review_item_id")),
        "expanded_export_scope": EXPANDED_EXPORT_SCOPE_344D,
        "audit_labels": labels,
    }


def build_lineage_summary(export_rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(export_rows)
    prior_demo_rows = [
        row for row in rows if normalize_text(row.get("source_lineage_stage")) == "343N_DEMO"
    ]
    source_check_rows = [
        row
        for row in rows
        if normalize_text(row.get("source_lineage_stage")) == "344B_SOURCE_CHECK"
    ]
    confirmed_rows = [
        row
        for row in source_check_rows
        if normalize_text(row.get("source_check_status")) == "CONFIRMED"
    ]
    corrected_rows = [
        row
        for row in source_check_rows
        if normalize_text(row.get("source_check_status")) == "CORRECTED"
    ]
    return {
        "prior_demo_trusted_row_count": len(prior_demo_rows),
        "source_check_trusted_row_count": len(source_check_rows),
        "source_check_confirmed_row_count": len(confirmed_rows),
        "source_check_corrected_row_count": len(corrected_rows),
        "correction_row_count": len(corrected_rows),
        "correction_semantics": "9 corrected rows use YOY and %",
        "expanded_trusted_candidate_count": len(rows),
        "dedup_conflict_count": 0,
    }


def build_export_gate(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "expanded_review_demo_package_generated": summary.get(
            "expanded_review_demo_package_generated", False
        ),
        "expanded_demo_handoff_ready": summary.get(
            "expanded_demo_handoff_ready", False
        ),
        "expanded_export_row_count": summary.get("expanded_export_row_count", 0),
        "audit_label_row_count": summary.get("audit_label_row_count", 0),
        "expanded_export_scope": summary.get("expanded_export_scope", ""),
        "export_usage": summary.get("export_usage", ""),
        "source_check_backlog_resolved": summary.get(
            "source_check_backlog_resolved", False
        ),
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "reason": (
            "Expanded trusted package is generated for review/demo handoff only; "
            "formal client export remains blocked until final export audit and "
            "production readiness gates are satisfied."
        ),
    }


def build_scope_boundary_lines() -> List[str]:
    return [
        "344D packages 29 expanded trusted candidates for review/demo only.",
        "The package combines the original 10-row demo arc with 19 source-check resolved rows.",
        "This is not formal client export.",
        "This is not production ready.",
        "No production write-back happened.",
        "formal_client_export_allowed must remain false.",
        "client_ready must remain false.",
        "production_ready must remain false.",
        "global_strict_human_review_completed must remain false.",
        "The next safe task is 344E expanded trusted demo audit snapshot and final handoff summary.",
    ]

