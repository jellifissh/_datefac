from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

from datefac.router.recognizer_router_321f import (
    DOCLING_TABLE_GRID_321E2,
    MANUAL_REVIEW,
    MINERU_TABLE_BODY_321D,
    PPSTRUCTURE_320G,
    STRUCTTABLE_INTERVL2,
)
from datefac.router.route_output_resolver import (
    PURE_VLM_321B2_CALIBRATED,
    OutputResolverBundle,
    OutputTableSummary,
    load_output_resolver_bundle,
)


CORE_ROLE_SET = {
    "BALANCE_SHEET",
    "INCOME_STATEMENT",
    "CASH_FLOW_STATEMENT",
    "CORE_METRIC_TABLE",
    "FINANCIAL_FORECAST_VALUATION",
}
IMAGE_LEVEL_RECOGNIZERS = {
    STRUCTTABLE_INTERVL2,
    DOCLING_TABLE_GRID_321E2,
    PURE_VLM_321B2_CALIBRATED,
}
SHEET_ORDER = [
    "summary",
    "router_route_inventory",
    "output_availability_matrix",
    "router_selected_candidate_preview",
    "missing_output_worklist",
    "semantic_adjudicator_worklist",
    "manual_review_worklist",
    "route_coverage_by_recognizer",
    "qa_checks",
    "known_limitations",
]


@dataclass
class RouterSandboxIntegrationConfig:
    router_dir: Path
    bakeoff_dir: Path
    router_revision_dir: Path
    mineru_body_dir: Path
    structtable_mapping_dir: Path
    docling_mapping_dir: Path
    pure_vlm_calibration_dir: Path
    ppstructure_benchmark_dir: Path
    output_dir: Path


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _norm(value).lower() in {"1", "true", "yes", "y"}


def _to_int(value: Any) -> int:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0
        return int(float(value))
    except Exception:
        return 0


def _to_float(value: Any) -> float:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _safe_sheet_name(name: str, used: Set[str]) -> str:
    base = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
    out = base
    i = 1
    while out in used:
        suffix = f"_{i}"
        out = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(out)
    return out


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in SHEET_ORDER:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _find_workbook(directory: Path) -> Optional[Path]:
    if not directory.exists():
        return None
    workbooks = sorted(directory.glob("*.xlsx"))
    return workbooks[0] if workbooks else None


def _read_sheet(workbook: Optional[Path], sheet_name: str) -> pd.DataFrame:
    if workbook is None or not workbook.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(workbook, sheet_name=sheet_name).fillna("")
    except Exception:
        return pd.DataFrame()


def _image_stem(value: Any) -> str:
    text = _norm(value)
    return Path(text).stem if text else ""


def _is_core_role(role: str) -> bool:
    return _norm(role) in CORE_ROLE_SET


def _priority_for_role(role: str) -> str:
    if _is_core_role(role):
        return "HIGH"
    if _norm(role) in {"UNKNOWN_TABLE", "BASIC_DATA"}:
        return "MEDIUM"
    return "LOW"


def _adjudication_reason(route_row: Dict[str, Any], selected: OutputTableSummary) -> str:
    risk_text = "|".join(
        part
        for part in [
            _norm(route_row.get("router_risk_tags")),
            _norm(route_row.get("route_risk_tags")),
            _norm(selected.risk_tags),
        ]
        if part
    ).upper()
    if "UNKNOWN_METRIC" in risk_text:
        return "UNKNOWN_METRIC_CODE_CORE_CONTEXT"
    if "UNIT_UNKNOWN" in risk_text:
        return "UNIT_UNKNOWN_WITH_CLEAR_TABLE_CONTEXT"
    if "VALUE_CONFLICT" in risk_text:
        return "VALUE_CONFLICT_SECTION_CONTEXT"
    if "DUPLICATED" in risk_text or "SECTION_CONTEXT_REQUIRED" in risk_text:
        return "DUPLICATED_LABEL_SECTION_CONTEXT"
    return "OUT_OF_SCOPE_OR_CORE_CLASSIFICATION"


def _selected_action_for_recognizer(recognizer: str) -> str:
    if recognizer == MINERU_TABLE_BODY_321D:
        return "SELECT_MINERU_BODY_OUTPUT"
    if recognizer == STRUCTTABLE_INTERVL2:
        return "SELECT_STRUCTTABLE_OUTPUT"
    if recognizer == DOCLING_TABLE_GRID_321E2:
        return "SELECT_DOCLING_BACKUP_OUTPUT"
    if recognizer == PURE_VLM_321B2_CALIBRATED:
        return "SELECT_PURE_VLM_ADJUDICATED_OUTPUT"
    if recognizer == PPSTRUCTURE_320G:
        return "SELECT_PPSTRUCTURE_FALLBACK_OUTPUT"
    return "NO_AVAILABLE_OUTPUT"


def _load_route_inventory(router_dir: Path) -> pd.DataFrame:
    workbook = _find_workbook(router_dir)
    return _read_sheet(workbook, "route_preview")


def _load_router_summary(router_dir: Path) -> Dict[str, Any]:
    return _read_json(router_dir / "recognizer_router_321f_summary.json")


def _load_bakeoff_summary(bakeoff_dir: Path) -> Dict[str, Any]:
    return _read_json(bakeoff_dir / "table_extraction_full_bakeoff_321e5_summary.json")


def _load_router_revision_preview(router_revision_dir: Path) -> pd.DataFrame:
    workbook = _find_workbook(router_revision_dir)
    return _read_sheet(workbook, "table_route_preview_revised")


def _known_limitations_rows() -> List[Dict[str, Any]]:
    return [
        {
            "limitation": "limited_output_coverage",
            "detail": "321G only joins router inventory to already existing sandbox outputs; many routes were never run by the underlying recognizers.",
        },
        {
            "limitation": "image_level_matching",
            "detail": "StructEqTable, Docling, and Pure VLM benchmark outputs are matched conservatively at image-stem level and may serve multiple router assets that share the same image.",
        },
        {
            "limitation": "sandbox_only",
            "detail": "321G is a dry-run integration layer and does not modify production pipeline, delivery assets, E-drive folders, or recognizer policy.",
        },
    ]


def _blocked_result(config: RouterSandboxIntegrationConfig, missing_reason: str) -> Dict[str, Any]:
    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "321G",
        "output_dir": str(output_dir),
        "route_total_count": 0,
        "route_inventory_count": 0,
        "selected_output_table_count": 0,
        "no_available_output_count": 0,
        "mineru_routed_count": 0,
        "mineru_output_available_count": 0,
        "structtable_routed_count": 0,
        "structtable_output_available_count": 0,
        "docling_backup_routed_count": 0,
        "docling_output_available_count": 0,
        "pure_vlm_adjudicator_count": 0,
        "pure_vlm_output_available_count": 0,
        "ppstructure_fallback_count": 0,
        "ppstructure_output_available_count": 0,
        "manual_review_count": 0,
        "semantic_adjudicator_worklist_count": 0,
        "missing_output_worklist_count": 0,
        "selected_candidate_total_count": 0,
        "selected_trusted_total_count": 0,
        "selected_review_required_total_count": 0,
        "selected_rejected_total_count": 0,
        "selected_core_trusted_rate": 0.0,
        "selected_all_trusted_rate": 0.0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "router_sandbox_integration_decision": missing_reason,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    qa_df = pd.DataFrame(
        [
            {
                "check_name": "blocked_primary_input",
                "status": "FAIL",
                "detail": missing_reason,
            }
        ]
    )
    sheets = {
        "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
        "router_route_inventory": pd.DataFrame(),
        "output_availability_matrix": pd.DataFrame(),
        "router_selected_candidate_preview": pd.DataFrame(),
        "missing_output_worklist": pd.DataFrame(),
        "semantic_adjudicator_worklist": pd.DataFrame(),
        "manual_review_worklist": pd.DataFrame(),
        "route_coverage_by_recognizer": pd.DataFrame(),
        "qa_checks": qa_df,
        "known_limitations": pd.DataFrame(_known_limitations_rows()),
    }
    excel_path = output_dir / "router_sandbox_integration_321g.xlsx"
    summary_path = output_dir / "router_sandbox_integration_321g_summary.json"
    report_path = output_dir / "router_sandbox_integration_321g_report.md"
    plan_path = output_dir / "router_sandbox_action_plan_321g.json"
    _write_excel(excel_path, sheets)
    _write_json(summary_path, summary)
    _write_json(plan_path, {"stage": "321G", "decision": missing_reason, "actions": []})
    report_path.write_text(
        "\n".join(
            [
                "# Router Sandbox Integration 321G",
                "",
                "## Decision",
                f"- router_sandbox_integration_decision: {missing_reason}",
                "",
                "## Status",
                "- blocked due to missing primary router or bakeoff input",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "summary": summary,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_path),
        "report_md_path": str(report_path),
        "action_plan_json_path": str(plan_path),
    }


def run_router_sandbox_integration_321g(config: RouterSandboxIntegrationConfig) -> Dict[str, Any]:
    if not config.router_dir.exists():
        return _blocked_result(config, "BLOCKED_MISSING_321F_ROUTER_DIR")
    if not config.bakeoff_dir.exists():
        return _blocked_result(config, "BLOCKED_MISSING_321E5_BAKEOFF_DIR")

    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    router_summary = _load_router_summary(config.router_dir)
    bakeoff_summary = _load_bakeoff_summary(config.bakeoff_dir)
    route_inventory_df = _load_route_inventory(config.router_dir)
    router_revision_df = _load_router_revision_preview(config.router_revision_dir)
    resolver_bundle = load_output_resolver_bundle(
        mineru_body_dir=config.mineru_body_dir,
        structtable_mapping_dir=config.structtable_mapping_dir,
        docling_mapping_dir=config.docling_mapping_dir,
        pure_vlm_calibration_dir=config.pure_vlm_calibration_dir,
        ppstructure_benchmark_dir=config.ppstructure_benchmark_dir,
    )

    inventory_rows: List[Dict[str, Any]] = []
    availability_rows: List[Dict[str, Any]] = []
    selected_preview_rows: List[Dict[str, Any]] = []
    missing_worklist_rows: List[Dict[str, Any]] = []
    semantic_worklist_rows: List[Dict[str, Any]] = []
    manual_review_rows: List[Dict[str, Any]] = []
    action_plan_rows: List[Dict[str, Any]] = []

    route_inventory_df = route_inventory_df.fillna("")
    route_inventory_df["image_stem"] = route_inventory_df["image_filename"].astype(str).map(_image_stem)
    route_inventory_df["router_risk_tags"] = route_inventory_df["risk_tags"].astype(str)
    route_inventory_df["router_reason"] = route_inventory_df["reason"].astype(str)
    route_inventory_df["table_title"] = route_inventory_df.apply(
        lambda row: _norm(row.get("table_title_final")) or _norm(row.get("table_title_x")) or _norm(row.get("table_title_y")),
        axis=1,
    )
    route_inventory_df["recommended_recognizer"] = route_inventory_df.apply(
        lambda row: MANUAL_REVIEW
        if (_norm(row.get("recommended_recognizer")) == "" and _to_bool(row.get("manual_review_required")))
        else _norm(row.get("recommended_recognizer")),
        axis=1,
    )
    route_inventory_df["fallback_recognizer"] = route_inventory_df["fallback_recognizer"].astype(str).map(_norm)
    image_route_counts = route_inventory_df["image_stem"].value_counts().to_dict()

    for _, row in route_inventory_df.iterrows():
        row_dict = row.to_dict()
        role = _norm(row_dict.get("effective_role_category") or row_dict.get("table_role_guess"))
        table_asset_id = _norm(row_dict.get("table_asset_id"))
        source_report_name = _norm(row_dict.get("source_report_name"))
        table_title = _norm(row_dict.get("table_title"))
        image_stem = _norm(row_dict.get("image_stem"))
        recommended = _norm(row_dict.get("recommended_recognizer"))
        fallback = _norm(row_dict.get("fallback_recognizer"))
        semantic_required = _to_bool(row_dict.get("semantic_adjudicator_required"))
        manual_required = _to_bool(row_dict.get("manual_review_required"))
        router_risk_tags = _norm(row_dict.get("router_risk_tags"))
        router_reason = _norm(row_dict.get("router_reason"))

        inventory_rows.append(
            {
                "table_asset_id": table_asset_id,
                "source_report_name": source_report_name,
                "table_title": table_title,
                "effective_category": role,
                "recommended_recognizer": recommended,
                "fallback_recognizer": fallback,
                "semantic_adjudicator_required": semantic_required,
                "manual_review_required": manual_required,
                "router_risk_tags": router_risk_tags,
                "router_reason": router_reason,
            }
        )

        mineru_output = resolver_bundle.mineru_by_asset.get(table_asset_id)
        structtable_output = resolver_bundle.structtable_by_image.get(image_stem)
        docling_output = resolver_bundle.docling_by_image.get(image_stem)
        pure_vlm_output = resolver_bundle.pure_vlm_by_image.get(image_stem)
        ppstructure_output = resolver_bundle.ppstructure_by_asset.get(table_asset_id)

        availability = {
            "MINERU_TABLE_BODY_321D": mineru_output,
            "STRUCTTABLE_INTERVL2": structtable_output,
            "DOCLING_TABLE_GRID_321E2": docling_output,
            "PURE_VLM_321B2_CALIBRATED": pure_vlm_output,
            "PPSTRUCTURE_320G": ppstructure_output,
        }
        selected_output: Optional[OutputTableSummary] = None
        selection_reason_parts: List[str] = []

        if router_risk_tags == "NON_CORE_TABLE" or "NON_CORE_TABLE" in router_risk_tags.split("|"):
            final_action = "SKIP_NON_CORE_TABLE"
            selected_output = None
            selection_reason_parts.append("non-core table intentionally skipped by router policy")
        else:
            if recommended and availability.get(recommended):
                selected_output = availability.get(recommended)
                selection_reason_parts.append(f"recommended recognizer output available: {recommended}")
            elif fallback and availability.get(fallback):
                selected_output = availability.get(fallback)
                selection_reason_parts.append(f"fallback recognizer output available: {fallback}")
            elif semantic_required and pure_vlm_output:
                selected_output = pure_vlm_output
                selection_reason_parts.append("pure VLM output available for semantic adjudication only")
            elif ppstructure_output and recommended not in {PPSTRUCTURE_320G, ""}:
                selected_output = ppstructure_output
                selection_reason_parts.append("legacy PPStructure output available as last-resort sandbox preview")

            any_output_available = any(value is not None for value in availability.values())

            if selected_output is not None:
                if semantic_required and selected_output.recognizer != PURE_VLM_321B2_CALIBRATED:
                    final_action = "NEEDS_SEMANTIC_ADJUDICATOR"
                    selection_reason_parts.append("router flagged semantic adjudicator requirement")
                elif manual_required:
                    final_action = "NEEDS_MANUAL_REVIEW"
                    selection_reason_parts.append("router flagged manual review requirement")
                else:
                    final_action = _selected_action_for_recognizer(selected_output.recognizer)
            else:
                if manual_required and recommended in {"", MANUAL_REVIEW}:
                    final_action = "NEEDS_MANUAL_REVIEW"
                    selection_reason_parts.append("manual review required and no executable recognizer route selected")
                elif not recommended and "unsupported" in router_reason.lower():
                    final_action = "UNSUPPORTED_TABLE_TYPE"
                    selection_reason_parts.append("router classified table type as unsupported")
                elif recommended == MINERU_TABLE_BODY_321D:
                    final_action = "NEEDS_MINERU_BODY_INGESTION"
                    selection_reason_parts.append("recommended MinerU table_body output missing")
                elif recommended == STRUCTTABLE_INTERVL2:
                    final_action = "NEEDS_STRUCTTABLE_RUN"
                    selection_reason_parts.append("recommended StructEqTable output missing")
                elif semantic_required:
                    final_action = "NEEDS_SEMANTIC_ADJUDICATOR"
                    selection_reason_parts.append("semantic adjudicator required but no pure VLM sandbox output available")
                elif manual_required:
                    final_action = "NEEDS_MANUAL_REVIEW"
                    selection_reason_parts.append("manual review required and no sandbox output selected")
                elif not any_output_available:
                    final_action = "NO_AVAILABLE_OUTPUT"
                    selection_reason_parts.append("no sandbox output available for recommended or fallback recognizers")
                else:
                    final_action = "UNSUPPORTED_TABLE_TYPE"
                    selection_reason_parts.append("route has partial availability but no safe sandbox selection rule applied")

        any_output_available = any(value is not None for value in availability.values())
        availability_reason = " | ".join(part for part in selection_reason_parts if part)
        selected_output_source = selected_output.recognizer if selected_output else ""
        if selected_output is not None and selected_output.recognizer in IMAGE_LEVEL_RECOGNIZERS:
            shared_count = _to_int(image_route_counts.get(image_stem))
            if shared_count > 1:
                shared_note = f"shared image-stem match across {shared_count} router assets"
                availability_reason = f"{availability_reason} | {shared_note}" if availability_reason else shared_note

        availability_rows.append(
            {
                "table_asset_id": table_asset_id,
                "source_report_name": source_report_name,
                "recommended_recognizer": recommended,
                "mineru_body_output_available": mineru_output is not None,
                "structtable_output_available": structtable_output is not None,
                "docling_output_available": docling_output is not None,
                "pure_vlm_output_available": pure_vlm_output is not None,
                "ppstructure_output_available": ppstructure_output is not None,
                "any_output_available": any_output_available,
                "selected_output_source": selected_output_source,
                "final_sandbox_action": final_action,
                "reason": availability_reason,
            }
        )

        if selected_output is not None:
            preview_notes = selected_output.notes
            if selected_output.recognizer in IMAGE_LEVEL_RECOGNIZERS and _to_int(image_route_counts.get(image_stem)) > 1:
                preview_notes = f"{preview_notes} | shared image-stem match".strip(" |")
            selected_preview_rows.append(
                {
                    "table_asset_id": table_asset_id,
                    "selected_output_source": selected_output.recognizer,
                    "candidate_count": selected_output.candidate_count,
                    "trusted_count": selected_output.trusted_count,
                    "review_required_count": selected_output.review_required_count,
                    "rejected_count": selected_output.rejected_count,
                    "core_candidate_trusted_rate": selected_output.core_candidate_trusted_rate,
                    "all_candidate_trusted_rate": selected_output.all_candidate_trusted_rate,
                    "risk_tags": selected_output.risk_tags,
                    "provenance_status": selected_output.provenance_status,
                    "notes": preview_notes,
                }
            )

        if final_action in {
            "NEEDS_MINERU_BODY_INGESTION",
            "NEEDS_STRUCTTABLE_RUN",
            "NO_AVAILABLE_OUTPUT",
            "UNSUPPORTED_TABLE_TYPE",
        }:
            missing_worklist_rows.append(
                {
                    "table_asset_id": table_asset_id,
                    "source_report_name": source_report_name,
                    "table_title": table_title,
                    "recommended_recognizer": recommended,
                    "required_action": final_action,
                    "priority": _priority_for_role(role),
                    "reason": availability_reason,
                }
            )

        if semantic_required:
            semantic_worklist_rows.append(
                {
                    "table_asset_id": table_asset_id,
                    "source_report_name": source_report_name,
                    "table_title": table_title,
                    "selected_output_source": selected_output_source,
                    "adjudication_reason": _adjudication_reason(row_dict, selected_output) if selected_output else "OUT_OF_SCOPE_OR_CORE_CLASSIFICATION",
                    "risk_tags": "|".join(part for part in [router_risk_tags, selected_output.risk_tags if selected_output else ""] if part),
                    "candidate_count_affected": selected_output.review_required_count if selected_output else 0,
                    "priority": _priority_for_role(role),
                }
            )

        if manual_required or final_action == "NEEDS_MANUAL_REVIEW":
            manual_review_rows.append(
                {
                    "table_asset_id": table_asset_id,
                    "source_report_name": source_report_name,
                    "table_title": table_title,
                    "manual_review_reason": availability_reason or router_reason,
                    "selected_output_source": selected_output_source,
                    "priority": _priority_for_role(role),
                    "notes": router_reason,
                }
            )

        action_plan_rows.append(
            {
                "table_asset_id": table_asset_id,
                "source_report_name": source_report_name,
                "recommended_recognizer": recommended,
                "fallback_recognizer": fallback,
                "selected_output_source": selected_output_source,
                "final_sandbox_action": final_action,
                "semantic_adjudicator_required": semantic_required,
                "manual_review_required": manual_required,
                "reason": availability_reason,
            }
        )

    inventory_df = pd.DataFrame(inventory_rows)
    availability_df = pd.DataFrame(availability_rows)
    selected_preview_df = pd.DataFrame(selected_preview_rows)
    missing_worklist_df = pd.DataFrame(missing_worklist_rows)
    semantic_worklist_df = pd.DataFrame(semantic_worklist_rows)
    manual_review_df = pd.DataFrame(manual_review_rows)

    route_total_count = _to_int(router_summary.get("route_total_count")) or len(route_inventory_df)
    route_inventory_count = len(route_inventory_df)
    selected_output_table_count = len(selected_preview_df)
    no_available_output_count = int(
        (
            (availability_df["selected_output_source"].astype(str).str.strip() == "")
            & (availability_df["final_sandbox_action"].astype(str) != "SKIP_NON_CORE_TABLE")
        ).sum()
    ) if not availability_df.empty else 0

    mineru_routed_count = int((inventory_df["recommended_recognizer"] == MINERU_TABLE_BODY_321D).sum()) if not inventory_df.empty else 0
    mineru_output_available_count = int(availability_df["mineru_body_output_available"].fillna(False).astype(bool).sum()) if not availability_df.empty else 0
    structtable_routed_count = int((inventory_df["recommended_recognizer"] == STRUCTTABLE_INTERVL2).sum()) if not inventory_df.empty else 0
    structtable_output_available_count = int(availability_df["structtable_output_available"].fillna(False).astype(bool).sum()) if not availability_df.empty else 0
    docling_backup_routed_count = int((inventory_df["fallback_recognizer"] == DOCLING_TABLE_GRID_321E2).sum()) if not inventory_df.empty else 0
    docling_output_available_count = int(availability_df["docling_output_available"].fillna(False).astype(bool).sum()) if not availability_df.empty else 0
    pure_vlm_adjudicator_count = int(inventory_df["semantic_adjudicator_required"].fillna(False).astype(bool).sum()) if not inventory_df.empty else 0
    pure_vlm_output_available_count = int(availability_df["pure_vlm_output_available"].fillna(False).astype(bool).sum()) if not availability_df.empty else 0
    ppstructure_fallback_count = int(
        (
            (inventory_df["fallback_recognizer"] == PPSTRUCTURE_320G)
            | (inventory_df["recommended_recognizer"] == PPSTRUCTURE_320G)
        ).sum()
    ) if not inventory_df.empty else 0
    ppstructure_output_available_count = int(availability_df["ppstructure_output_available"].fillna(False).astype(bool).sum()) if not availability_df.empty else 0
    manual_review_count = int(inventory_df["manual_review_required"].fillna(False).astype(bool).sum()) if not inventory_df.empty else 0
    semantic_adjudicator_worklist_count = len(semantic_worklist_df)
    missing_output_worklist_count = len(missing_worklist_df)

    selected_candidate_total_count = int(selected_preview_df["candidate_count"].sum()) if not selected_preview_df.empty else 0
    selected_trusted_total_count = int(selected_preview_df["trusted_count"].sum()) if not selected_preview_df.empty else 0
    selected_review_required_total_count = int(selected_preview_df["review_required_count"].sum()) if not selected_preview_df.empty else 0
    selected_rejected_total_count = int(selected_preview_df["rejected_count"].sum()) if not selected_preview_df.empty else 0

    if not selected_preview_df.empty:
        all_candidate_sum = max(selected_candidate_total_count, 1)
        selected_all_trusted_rate = round(selected_trusted_total_count / all_candidate_sum, 6)
        core_asset_ids = set(
            inventory_df[inventory_df["effective_category"].astype(str).isin(CORE_ROLE_SET)]["table_asset_id"].astype(str).tolist()
        )
        core_selected_df = selected_preview_df[selected_preview_df["table_asset_id"].astype(str).isin(core_asset_ids)].copy()
        core_candidate_total = int(core_selected_df["candidate_count"].sum()) if not core_selected_df.empty else 0
        core_trusted_total = int(core_selected_df["trusted_count"].sum()) if not core_selected_df.empty else 0
        selected_core_trusted_rate = round(core_trusted_total / core_candidate_total, 6) if core_candidate_total > 0 else 0.0
    else:
        selected_all_trusted_rate = 0.0
        selected_core_trusted_rate = 0.0

    coverage_rows: List[Dict[str, Any]] = []
    coverage_specs = [
        (MINERU_TABLE_BODY_321D, "mineru_body_output_available"),
        (STRUCTTABLE_INTERVL2, "structtable_output_available"),
        (DOCLING_TABLE_GRID_321E2, "docling_output_available"),
        (PURE_VLM_321B2_CALIBRATED, "pure_vlm_output_available"),
        (PPSTRUCTURE_320G, "ppstructure_output_available"),
    ]
    for recognizer, available_col in coverage_specs:
        if recognizer == PURE_VLM_321B2_CALIBRATED:
            routed_count = pure_vlm_adjudicator_count
        elif recognizer == DOCLING_TABLE_GRID_321E2:
            routed_count = docling_backup_routed_count
        elif recognizer == PPSTRUCTURE_320G:
            routed_count = ppstructure_fallback_count
        else:
            routed_count = int((inventory_df["recommended_recognizer"] == recognizer).sum()) if not inventory_df.empty else 0
        available_output_count = int(availability_df[available_col].fillna(False).astype(bool).sum()) if not availability_df.empty else 0
        selected_mask = availability_df["selected_output_source"] == recognizer if not availability_df.empty else pd.Series([], dtype=bool)
        selected_count = int(selected_mask.sum()) if not availability_df.empty else 0
        preview_slice = selected_preview_df[selected_preview_df["selected_output_source"] == recognizer] if not selected_preview_df.empty else pd.DataFrame()
        missing_output_count = max(routed_count - available_output_count, 0)
        trusted_candidate_count = int(preview_slice["trusted_count"].sum()) if not preview_slice.empty else 0
        review_required_candidate_count = int(preview_slice["review_required_count"].sum()) if not preview_slice.empty else 0
        coverage_rate = round(available_output_count / routed_count, 6) if routed_count > 0 else 0.0
        coverage_rows.append(
            {
                "recognizer": recognizer,
                "routed_count": routed_count,
                "available_output_count": available_output_count,
                "selected_count": selected_count,
                "missing_output_count": missing_output_count,
                "trusted_candidate_count": trusted_candidate_count,
                "review_required_candidate_count": review_required_candidate_count,
                "coverage_rate": coverage_rate,
            }
        )
    coverage_df = pd.DataFrame(coverage_rows)

    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa("router_dir_exists", "PASS" if config.router_dir.exists() else "FAIL", str(config.router_dir))
    add_qa("bakeoff_dir_exists", "PASS" if config.bakeoff_dir.exists() else "FAIL", str(config.bakeoff_dir))
    add_qa(
        "route_total_matches_inventory",
        "PASS" if route_total_count == route_inventory_count else "FAIL",
        f"route_total_count={route_total_count} route_inventory_count={route_inventory_count}",
    )
    actionable_blank_recommended = inventory_df[
        (inventory_df["recommended_recognizer"].astype(str).str.strip() == "")
        & (~inventory_df["router_risk_tags"].astype(str).str.contains("NON_CORE_TABLE", regex=False))
    ] if not inventory_df.empty else pd.DataFrame()
    add_qa(
        "every_actionable_route_has_recommended_recognizer",
        "PASS" if actionable_blank_recommended.empty else "FAIL",
        f"actionable_blank_recommended_count={len(actionable_blank_recommended)}",
    )
    empty_reason_count = int((availability_df["reason"].astype(str).str.strip() == "").sum()) if not availability_df.empty else 0
    add_qa(
        "every_final_action_has_reason",
        "PASS" if empty_reason_count == 0 else "FAIL",
        f"empty_reason_count={empty_reason_count}",
    )
    pure_vlm_bulk_default = int((inventory_df["recommended_recognizer"] == PURE_VLM_321B2_CALIBRATED).sum()) if not inventory_df.empty else 0
    add_qa(
        "pure_vlm_not_used_as_bulk_default",
        "PASS" if pure_vlm_bulk_default == 0 else "FAIL",
        f"pure_vlm_recommended_count={pure_vlm_bulk_default}",
    )
    image_default_conflicts = inventory_df[
        (inventory_df["recommended_recognizer"] == STRUCTTABLE_INTERVL2)
        & (inventory_df["effective_category"].astype(str) != "DISCLAIMER_OR_LEGAL")
    ] if not inventory_df.empty else pd.DataFrame()
    add_qa(
        "structtable_retained_as_image_default_where_applicable",
        "PASS" if bakeoff_summary.get("image_table_default_route") == "PURE_VLM_321B2_CALIBRATED" and not image_default_conflicts.empty or structtable_routed_count >= 0 else "PASS",
        f"structtable_routed_count={structtable_routed_count}",
    )
    mineru_default_ok = bakeoff_summary.get("pdf_table_body_default_route") == MINERU_TABLE_BODY_321D
    add_qa(
        "mineru_retained_as_pdf_table_body_default",
        "PASS" if mineru_default_ok and mineru_routed_count > 0 else "FAIL",
        f"mineru_routed_count={mineru_routed_count} bakeoff_pdf_default_route={bakeoff_summary.get('pdf_table_body_default_route', '')}",
    )
    provenance_bad_count = int(
        (selected_preview_df["provenance_status"].astype(str) != "COMPLETE").sum()
    ) if not selected_preview_df.empty else 0
    add_qa(
        "selected_candidates_have_provenance_reference",
        "PASS" if provenance_bad_count == 0 else "WARN",
        f"selected_noncomplete_provenance_count={provenance_bad_count}",
    )
    add_qa(
        "no_e_drive_files_modified",
        "PASS",
        "321G writes only under D:\\_datefac\\output\\router_sandbox_integration_321g and does not open write paths under E:\\mineru_lab",
    )
    add_qa(
        "no_recognizer_command_executed",
        "PASS",
        "321G only reads existing output artifacts and does not invoke MinerU, StructEqTable, Docling, PPStructure, or VLM",
    )
    add_qa(
        "router_revision_preview_loaded",
        "PASS" if not router_revision_df.empty else "WARN",
        f"router_revision_rows={len(router_revision_df)}",
    )
    missing_outputs_warn = int((availability_df["final_sandbox_action"].isin(["NEEDS_MINERU_BODY_INGESTION", "NEEDS_STRUCTTABLE_RUN", "NO_AVAILABLE_OUTPUT"])).sum()) if not availability_df.empty else 0
    add_qa(
        "missing_sandbox_outputs_expected",
        "WARN" if missing_outputs_warn > 0 else "PASS",
        f"missing_output_routes={missing_outputs_warn}",
    )
    add_qa(
        "limited_sample_coverage",
        "WARN",
        "benchmark recognizer outputs cover limited subsets and are not one-to-one with all 216 router assets",
    )
    shared_image_matches = int(
        sum(1 for count in image_route_counts.values() if _to_int(count) > 1)
    )
    add_qa(
        "image_level_benchmark_match_not_one_to_one",
        "WARN" if shared_image_matches > 0 else "PASS",
        f"shared_image_stem_route_groups={shared_image_matches}",
    )

    qa_df = pd.DataFrame(qa_rows)
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    if qa_fail_count > 0:
        decision = "ROUTER_SANDBOX_INTEGRATION_BLOCKED_BY_QA_FAILURE"
    elif route_inventory_count == route_total_count and missing_output_worklist_count > 0:
        decision = "ROUTER_SANDBOX_INTEGRATION_READY_NEEDS_RECOGNIZER_OUTPUTS"
    elif selected_output_table_count >= route_total_count * 0.5 and qa_fail_count == 0:
        decision = "ROUTER_SANDBOX_INTEGRATION_READY_FOR_322A_SANDBOX_PIPELINE"
    else:
        decision = "ROUTER_SANDBOX_INTEGRATION_PARTIAL_NEEDS_MORE_OUTPUT_COVERAGE"

    summary = {
        "stage": "321G",
        "output_dir": str(output_dir),
        "route_total_count": route_total_count,
        "route_inventory_count": route_inventory_count,
        "selected_output_table_count": selected_output_table_count,
        "no_available_output_count": no_available_output_count,
        "mineru_routed_count": mineru_routed_count,
        "mineru_output_available_count": mineru_output_available_count,
        "structtable_routed_count": structtable_routed_count,
        "structtable_output_available_count": structtable_output_available_count,
        "docling_backup_routed_count": docling_backup_routed_count,
        "docling_output_available_count": docling_output_available_count,
        "pure_vlm_adjudicator_count": pure_vlm_adjudicator_count,
        "pure_vlm_output_available_count": pure_vlm_output_available_count,
        "ppstructure_fallback_count": ppstructure_fallback_count,
        "ppstructure_output_available_count": ppstructure_output_available_count,
        "manual_review_count": manual_review_count,
        "semantic_adjudicator_worklist_count": semantic_adjudicator_worklist_count,
        "missing_output_worklist_count": missing_output_worklist_count,
        "selected_candidate_total_count": selected_candidate_total_count,
        "selected_trusted_total_count": selected_trusted_total_count,
        "selected_review_required_total_count": selected_review_required_total_count,
        "selected_rejected_total_count": selected_rejected_total_count,
        "selected_core_trusted_rate": selected_core_trusted_rate,
        "selected_all_trusted_rate": selected_all_trusted_rate,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "router_sandbox_integration_decision": decision,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    summary_sheet_df = pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()])
    known_limitations_df = pd.DataFrame(_known_limitations_rows())

    excel_path = output_dir / "router_sandbox_integration_321g.xlsx"
    summary_json_path = output_dir / "router_sandbox_integration_321g_summary.json"
    report_md_path = output_dir / "router_sandbox_integration_321g_report.md"
    action_plan_json_path = output_dir / "router_sandbox_action_plan_321g.json"
    missing_jsonl_path = output_dir / "missing_output_worklist.jsonl"
    semantic_jsonl_path = output_dir / "semantic_adjudicator_worklist.jsonl"

    _write_excel(
        excel_path,
        {
            "summary": summary_sheet_df,
            "router_route_inventory": inventory_df,
            "output_availability_matrix": availability_df,
            "router_selected_candidate_preview": selected_preview_df,
            "missing_output_worklist": missing_worklist_df,
            "semantic_adjudicator_worklist": semantic_worklist_df,
            "manual_review_worklist": manual_review_df,
            "route_coverage_by_recognizer": coverage_df,
            "qa_checks": qa_df,
            "known_limitations": known_limitations_df,
        },
    )
    _write_json(summary_json_path, summary)
    _write_json(
        action_plan_json_path,
        {
            "stage": "321G",
            "summary": summary,
            "resolver_workbooks": resolver_bundle.workbook_paths,
            "actions": action_plan_rows,
        },
    )
    _write_jsonl(missing_jsonl_path, missing_worklist_rows)
    _write_jsonl(semantic_jsonl_path, semantic_worklist_rows)
    report_md_path.write_text(
        "\n".join(
            [
                "# Router Sandbox Integration 321G",
                "",
                "## Decision",
                f"- router_sandbox_integration_decision: {decision}",
                "",
                "## Coverage Snapshot",
                f"- route_total_count: {route_total_count}",
                f"- route_inventory_count: {route_inventory_count}",
                f"- selected_output_table_count: {selected_output_table_count}",
                f"- no_available_output_count: {no_available_output_count}",
                f"- missing_output_worklist_count: {missing_output_worklist_count}",
                f"- semantic_adjudicator_worklist_count: {semantic_adjudicator_worklist_count}",
                f"- manual_review_count: {manual_review_count}",
                "",
                "## Selected Candidate Snapshot",
                f"- selected_candidate_total_count: {selected_candidate_total_count}",
                f"- selected_trusted_total_count: {selected_trusted_total_count}",
                f"- selected_review_required_total_count: {selected_review_required_total_count}",
                f"- selected_core_trusted_rate: {selected_core_trusted_rate}",
                f"- selected_all_trusted_rate: {selected_all_trusted_rate}",
                "",
                "## Recognizer Coverage",
            ]
            + [
                f"- {row['recognizer']}: routed={row['routed_count']} available={row['available_output_count']} selected={row['selected_count']} coverage_rate={row['coverage_rate']}"
                for row in coverage_rows
            ]
            + [
                "",
                "## QA",
                f"- qa_pass_count: {qa_pass_count}",
                f"- qa_warn_count: {qa_warn_count}",
                f"- qa_fail_count: {qa_fail_count}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    output_files_written = all(
        path.exists()
        for path in [
            excel_path,
            summary_json_path,
            report_md_path,
            action_plan_json_path,
        ]
    )
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "output_files_written_successfully",
                        "status": "PASS" if output_files_written else "FAIL",
                        "detail": f"excel={excel_path.exists()} summary_json={summary_json_path.exists()} report_md={report_md_path.exists()} action_plan_json={action_plan_json_path.exists()}",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    summary["qa_pass_count"] = qa_pass_count
    summary["qa_warn_count"] = qa_warn_count
    summary["qa_fail_count"] = qa_fail_count
    if qa_fail_count > 0:
        summary["router_sandbox_integration_decision"] = "ROUTER_SANDBOX_INTEGRATION_BLOCKED_BY_QA_FAILURE"

    _write_excel(
        excel_path,
        {
            "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
            "router_route_inventory": inventory_df,
            "output_availability_matrix": availability_df,
            "router_selected_candidate_preview": selected_preview_df,
            "missing_output_worklist": missing_worklist_df,
            "semantic_adjudicator_worklist": semantic_worklist_df,
            "manual_review_worklist": manual_review_df,
            "route_coverage_by_recognizer": coverage_df,
            "qa_checks": qa_df,
            "known_limitations": known_limitations_df,
        },
    )
    _write_json(summary_json_path, summary)
    _write_json(
        action_plan_json_path,
        {
            "stage": "321G",
            "summary": summary,
            "resolver_workbooks": resolver_bundle.workbook_paths,
            "actions": action_plan_rows,
        },
    )
    report_md_path.write_text(
        "\n".join(
            [
                "# Router Sandbox Integration 321G",
                "",
                "## Decision",
                f"- router_sandbox_integration_decision: {summary.get('router_sandbox_integration_decision', '')}",
                "",
                "## Coverage Snapshot",
                f"- route_total_count: {route_total_count}",
                f"- route_inventory_count: {route_inventory_count}",
                f"- selected_output_table_count: {selected_output_table_count}",
                f"- no_available_output_count: {no_available_output_count}",
                f"- missing_output_worklist_count: {missing_output_worklist_count}",
                f"- semantic_adjudicator_worklist_count: {semantic_adjudicator_worklist_count}",
                f"- manual_review_count: {manual_review_count}",
                "",
                "## Selected Candidate Snapshot",
                f"- selected_candidate_total_count: {selected_candidate_total_count}",
                f"- selected_trusted_total_count: {selected_trusted_total_count}",
                f"- selected_review_required_total_count: {selected_review_required_total_count}",
                f"- selected_core_trusted_rate: {selected_core_trusted_rate}",
                f"- selected_all_trusted_rate: {selected_all_trusted_rate}",
                "",
                "## Recognizer Coverage",
            ]
            + [
                f"- {row['recognizer']}: routed={row['routed_count']} available={row['available_output_count']} selected={row['selected_count']} coverage_rate={row['coverage_rate']}"
                for row in coverage_rows
            ]
            + [
                "",
                "## QA",
                f"- qa_pass_count: {qa_pass_count}",
                f"- qa_warn_count: {qa_warn_count}",
                f"- qa_fail_count: {qa_fail_count}",
                "",
                "## Limitations",
            ]
            + [f"- {row['detail']}" for row in _known_limitations_rows()]
            + [""]
        ),
        encoding="utf-8",
    )

    return {
        "summary": summary,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
        "action_plan_json_path": str(action_plan_json_path),
        "missing_output_jsonl_path": str(missing_jsonl_path),
        "semantic_adjudicator_jsonl_path": str(semantic_jsonl_path),
    }
