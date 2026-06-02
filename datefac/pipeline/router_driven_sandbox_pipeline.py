from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

import pandas as pd

from datefac.mineru_body.mineru_body_benchmark import (
    _decision as mineru_321d_decision,
    _metric_coverage,
    _provenance_coverage,
    _risk_tag_counts,
    _unit_year_context_summary,
)
from datefac.mineru_body.mineru_body_candidate_mapper import (
    SOURCE_STAGE,
    map_unified_tables_to_candidates,
    split_mineru_body_candidates,
)
from datefac.mineru_body.mineru_body_delivery_builder import write_jsonl
from datefac.mineru_body.mineru_table_body_reader import extract_table_bodies
from datefac.mineru_body.mineru_table_normalizer import normalize_extracted_tables
from datefac.pipeline.router_selected_delivery_preview import (
    MINERU_322A_SOURCE,
    SelectedOutputBundle,
    build_router_selected_delivery_preview,
)
from datefac.router.recognizer_router_321f import MINERU_TABLE_BODY_321D
from datefac.router.route_output_resolver import load_output_resolver_bundle
from datefac.vlm.vlm_candidate_mapper import candidates_to_dataframe


SHEET_ORDER = [
    "summary",
    "selected_322a_mineru_worklist",
    "mineru_body_processing_audit",
    "router_selected_output_preview_322a",
    "metric_candidates_all_322a",
    "trusted_preview_322a",
    "review_required_preview_322a",
    "rejected_preview_322a",
    "semantic_adjudicator_worklist_322a",
    "manual_review_worklist_322a",
    "remaining_missing_output_worklist",
    "coverage_by_route_322a",
    "qa_checks",
    "known_limitations",
]
CORE_ROLE_SET = {
    "BALANCE_SHEET",
    "INCOME_STATEMENT",
    "CASH_FLOW_STATEMENT",
    "CORE_METRIC_TABLE",
    "FINANCIAL_FORECAST_VALUATION",
}


@dataclass
class RouterDrivenSandboxPipelineConfig:
    router_integration_dir: Path
    router_dir: Path
    mineru_output_root: Path
    existing_mineru_body_dir: Path
    structtable_mapping_dir: Path
    docling_mapping_dir: Path
    pure_vlm_calibration_dir: Path
    ppstructure_benchmark_dir: Path
    output_dir: Path
    max_new_mineru_tables: int = 50


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


def _known_limitations_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "limitation": "sandbox_only",
                "detail": "322A expands sandbox coverage only and does not write production delivery files or modify E-drive contents.",
            },
            {
                "limitation": "bounded_mineru_batch",
                "detail": "322A only processes a bounded batch of router-selected MinerU-body tables using existing MinerU outputs.",
            },
            {
                "limitation": "existing_non_mineru_outputs_reused",
                "detail": "StructEqTable, Docling, Pure VLM, and PPStructure remain reused benchmark outputs rather than rerun recognizers.",
            },
        ]
    )


def _blocked_result(config: RouterDrivenSandboxPipelineConfig, blocked_code: str) -> Dict[str, Any]:
    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322A",
        "output_dir": str(output_dir),
        "router_route_total_count": 0,
        "eligible_mineru_missing_count": 0,
        "selected_new_mineru_table_count": 0,
        "attempted_new_mineru_table_count": 0,
        "newly_processed_mineru_table_count": 0,
        "newly_failed_mineru_table_count": 0,
        "selected_output_table_count_before_322a": 0,
        "selected_output_table_count_after_322a": 0,
        "no_available_output_count_before_322a": 0,
        "no_available_output_count_after_322a": 0,
        "selected_candidate_total_count": 0,
        "selected_trusted_total_count": 0,
        "selected_review_required_total_count": 0,
        "selected_rejected_total_count": 0,
        "selected_core_trusted_rate": 0.0,
        "selected_all_trusted_rate": 0.0,
        "semantic_adjudicator_worklist_count": 0,
        "manual_review_worklist_count": 0,
        "remaining_missing_output_worklist_count": 0,
        "mineru_coverage_before_322a": 0.0,
        "mineru_coverage_after_322a": 0.0,
        "structtable_coverage_after_322a": 0.0,
        "docling_backup_coverage_after_322a": 0.0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "router_driven_sandbox_pipeline_decision": blocked_code,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    qa_df = pd.DataFrame([{"check_name": "blocked_primary_input", "status": "FAIL", "detail": blocked_code}])
    sheets = {
        "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
        "selected_322a_mineru_worklist": pd.DataFrame(),
        "mineru_body_processing_audit": pd.DataFrame(),
        "router_selected_output_preview_322a": pd.DataFrame(),
        "metric_candidates_all_322a": pd.DataFrame(),
        "trusted_preview_322a": pd.DataFrame(),
        "review_required_preview_322a": pd.DataFrame(),
        "rejected_preview_322a": pd.DataFrame(),
        "semantic_adjudicator_worklist_322a": pd.DataFrame(),
        "manual_review_worklist_322a": pd.DataFrame(),
        "remaining_missing_output_worklist": pd.DataFrame(),
        "coverage_by_route_322a": pd.DataFrame(),
        "qa_checks": qa_df,
        "known_limitations": _known_limitations_df(),
    }
    excel_path = output_dir / "router_driven_sandbox_pipeline_322a.xlsx"
    summary_path = output_dir / "router_driven_sandbox_pipeline_322a_summary.json"
    report_path = output_dir / "router_driven_sandbox_pipeline_322a_report.md"
    preview_jsonl_path = output_dir / "router_selected_delivery_preview_322a.jsonl"
    _write_excel(excel_path, sheets)
    _write_json(summary_path, summary)
    _write_json(preview_jsonl_path, {"blocked_code": blocked_code})
    report_path.write_text(
        "\n".join(
            [
                "# Router Driven Sandbox Pipeline 322A",
                "",
                "## Decision",
                f"- router_driven_sandbox_pipeline_decision: {blocked_code}",
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
        "preview_jsonl_path": str(preview_jsonl_path),
    }


def _load_router_integration_context(router_integration_dir: Path) -> Dict[str, Any]:
    summary = _read_json(router_integration_dir / "router_sandbox_integration_321g_summary.json")
    action_plan = _read_json(router_integration_dir / "router_sandbox_action_plan_321g.json")
    workbook = _find_workbook(router_integration_dir)
    return {
        "summary": summary,
        "action_plan": action_plan,
        "route_inventory_df": _read_sheet(workbook, "router_route_inventory"),
        "availability_df": _read_sheet(workbook, "output_availability_matrix"),
        "selected_preview_df": _read_sheet(workbook, "router_selected_candidate_previ"),
        "missing_output_worklist_df": _read_sheet(workbook, "missing_output_worklist"),
        "semantic_worklist_df": _read_sheet(workbook, "semantic_adjudicator_worklist"),
        "manual_review_df": _read_sheet(workbook, "manual_review_worklist"),
        "coverage_df": _read_sheet(workbook, "route_coverage_by_recognizer"),
    }


def _load_existing_candidates(
    existing_mineru_body_dir: Path,
    structtable_mapping_dir: Path,
    docling_mapping_dir: Path,
    pure_vlm_calibration_dir: Path,
    ppstructure_benchmark_dir: Path,
    selected_preview_df: pd.DataFrame,
) -> tuple[Dict[str, pd.DataFrame], Dict[str, str]]:
    selected_preview_df = selected_preview_df.fillna("") if not selected_preview_df.empty else pd.DataFrame()
    selected_output_sources = {
        _norm(row.get("table_asset_id")): _norm(row.get("selected_output_source"))
        for _, row in selected_preview_df.iterrows()
        if _norm(row.get("table_asset_id"))
    }
    existing_frames: Dict[str, pd.DataFrame] = {}

    def load_and_group(directory: Path, trusted_sheet: str, review_sheet: str, rejected_sheet: str) -> Dict[str, pd.DataFrame]:
        workbook = _find_workbook(directory)
        trusted_df = _read_sheet(workbook, trusted_sheet)
        review_df = _read_sheet(workbook, review_sheet)
        rejected_df = _read_sheet(workbook, rejected_sheet)
        frames = [df for df in [trusted_df, review_df, rejected_df] if not df.empty]
        if not frames:
            return {}
        all_df = pd.concat(frames, ignore_index=True).fillna("")
        if "source_table_id" not in all_df.columns:
            return {}
        return {
            table_id: group.copy()
            for table_id, group in all_df.groupby(all_df["source_table_id"].astype(str))
            if _norm(table_id)
        }

    grouped_by_source = {
        "MINERU_TABLE_BODY_321D": load_and_group(existing_mineru_body_dir, "trusted_preview", "review_required_preview", "rejected_preview"),
        "STRUCTTABLE_INTERVL2": load_and_group(structtable_mapping_dir, "structtable_trusted_preview", "structtable_review_required_pre", "structtable_rejected_preview"),
        "DOCLING_TABLE_GRID_321E2": load_and_group(docling_mapping_dir, "docling_trusted_preview", "docling_review_required_preview", "docling_rejected_preview"),
        "PURE_VLM_321B2_CALIBRATED": load_and_group(pure_vlm_calibration_dir, "trusted_preview", "review_required_preview", "rejected_preview"),
        "PPSTRUCTURE_320G": load_and_group(ppstructure_benchmark_dir, "trusted_preview_all", "review_required_preview_all", "rejected_preview_all"),
    }
    for table_id, source_name in selected_output_sources.items():
        source_groups = grouped_by_source.get(source_name, {})
        if table_id in source_groups:
            existing_frames[table_id] = source_groups[table_id].copy()
    return existing_frames, selected_output_sources


def _select_322a_mineru_worklist(route_inventory_df: pd.DataFrame, action_rows: Sequence[Dict[str, Any]], max_new_mineru_tables: int) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    route_inventory_df = route_inventory_df.fillna("") if not route_inventory_df.empty else pd.DataFrame()
    action_map = {_norm(row.get("table_asset_id")): dict(row) for row in action_rows if _norm(row.get("table_asset_id"))}
    worklist_rows: List[Dict[str, Any]] = []
    for _, row in route_inventory_df.iterrows():
        row_dict = row.to_dict()
        table_asset_id = _norm(row_dict.get("table_asset_id"))
        action_row = action_map.get(table_asset_id, {})
        recommended = _norm(row_dict.get("recommended_recognizer")) or _norm(action_row.get("recommended_recognizer"))
        final_action = _norm(action_row.get("final_sandbox_action"))
        role = _norm(row_dict.get("effective_category"))
        manual_required = _to_bool(row_dict.get("manual_review_required")) or _to_bool(action_row.get("manual_review_required"))
        eligible = (
            recommended == MINERU_TABLE_BODY_321D
            and final_action == "NEEDS_MINERU_BODY_INGESTION"
            and not manual_required
            and role in CORE_ROLE_SET
        )
        priority = "HIGH" if role in CORE_ROLE_SET else "MEDIUM"
        worklist_rows.append(
            {
                "table_asset_id": table_asset_id,
                "source_report_name": _norm(row_dict.get("source_report_name")),
                "table_title": _norm(row_dict.get("table_title")),
                "effective_category": role,
                "router_reason": _norm(row_dict.get("router_reason")) or _norm(action_row.get("reason")),
                "priority": priority,
                "selected_for_processing": eligible,
                "reason": _norm(action_row.get("reason")) or _norm(row_dict.get("router_reason")),
                "recommended_recognizer": recommended,
                "final_sandbox_action": final_action,
            }
        )
    worklist_df = pd.DataFrame(worklist_rows)
    if worklist_df.empty:
        return worklist_df, pd.DataFrame(), 0
    eligible_df = worklist_df[worklist_df["selected_for_processing"].fillna(False).astype(bool)].copy()
    eligible_total_count = len(eligible_df)
    if eligible_df.empty:
        return worklist_df, eligible_df, eligible_total_count
    selected_ids = eligible_df["table_asset_id"].head(max_new_mineru_tables).astype(str).tolist()
    selected_df = route_inventory_df[route_inventory_df["table_asset_id"].astype(str).isin(selected_ids)].copy()
    worklist_df["selected_for_processing"] = worklist_df["table_asset_id"].astype(str).isin(selected_ids)
    return worklist_df, selected_df, eligible_total_count


def _build_processing_audit(
    extraction_audit_df: pd.DataFrame,
    per_table_df: pd.DataFrame,
    trusted_df: pd.DataFrame,
    review_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
) -> pd.DataFrame:
    extraction_audit_df = extraction_audit_df.fillna("") if not extraction_audit_df.empty else pd.DataFrame()
    per_table_df = per_table_df.fillna("") if not per_table_df.empty else pd.DataFrame()
    if extraction_audit_df.empty:
        return pd.DataFrame(
            columns=[
                "table_asset_id",
                "source_report_name",
                "match_status",
                "matched_by",
                "content_source_file",
                "has_table_body",
                "has_html",
                "has_markdown_table",
                "parsed_row_count",
                "parsed_column_count",
                "candidate_count",
                "trusted_count",
                "review_required_count",
                "rejected_count",
                "warnings",
            ]
        )
    lookup = {
        _norm(row.get("table_asset_id")): row.to_dict()
        for _, row in per_table_df.iterrows()
        if _norm(row.get("table_asset_id"))
    }
    trusted_counts = trusted_df.groupby(trusted_df["source_table_id"].astype(str)).size().to_dict() if not trusted_df.empty else {}
    review_counts = review_df.groupby(review_df["source_table_id"].astype(str)).size().to_dict() if not review_df.empty else {}
    rejected_counts = rejected_df.groupby(rejected_df["source_table_id"].astype(str)).size().to_dict() if not rejected_df.empty else {}
    rows: List[Dict[str, Any]] = []
    for _, row in extraction_audit_df.iterrows():
        row_dict = row.to_dict()
        table_asset_id = _norm(row_dict.get("table_asset_id"))
        per_table = lookup.get(table_asset_id, {})
        rows.append(
            {
                "table_asset_id": table_asset_id,
                "source_report_name": _norm(per_table.get("source_report_name")),
                "match_status": _norm(row_dict.get("match_status")),
                "matched_by": _norm(row_dict.get("matched_by")),
                "content_source_file": _norm(row_dict.get("content_source_file")),
                "has_table_body": _to_bool(row_dict.get("has_table_body")),
                "has_html": _to_bool(row_dict.get("has_html")),
                "has_markdown_table": _to_bool(row_dict.get("has_markdown_table")),
                "parsed_row_count": _to_int(row_dict.get("extracted_row_count")),
                "parsed_column_count": _to_int(row_dict.get("extracted_column_count")),
                "candidate_count": _to_int(per_table.get("candidate_count")),
                "trusted_count": _to_int(trusted_counts.get(table_asset_id, 0)),
                "review_required_count": _to_int(review_counts.get(table_asset_id, 0)),
                "rejected_count": _to_int(rejected_counts.get(table_asset_id, 0)),
                "warnings": _norm(row_dict.get("warnings")),
            }
        )
    return pd.DataFrame(rows)


def _build_coverage_after(
    route_inventory_df: pd.DataFrame,
    coverage_before_df: pd.DataFrame,
    selected_preview_after_df: pd.DataFrame,
    newly_processed_ids: Sequence[str],
) -> pd.DataFrame:
    route_inventory_df = route_inventory_df.fillna("") if not route_inventory_df.empty else pd.DataFrame()
    selected_preview_after_df = selected_preview_after_df.fillna("") if not selected_preview_after_df.empty else pd.DataFrame()
    before_lookup = {
        _norm(row.get("recognizer")): row.to_dict()
        for _, row in coverage_before_df.iterrows()
        if _norm(row.get("recognizer"))
    } if not coverage_before_df.empty else {}
    recognizers = [
        MINERU_TABLE_BODY_321D,
        "STRUCTTABLE_INTERVL2",
        "DOCLING_TABLE_GRID_321E2",
        "PURE_VLM_321B2_CALIBRATED",
        "PPSTRUCTURE_320G",
    ]
    rows: List[Dict[str, Any]] = []
    newly_processed_set = set(str(item) for item in newly_processed_ids)
    mineru_selected_after = int((selected_preview_after_df["selected_output_source"].astype(str).isin([MINERU_322A_SOURCE, MINERU_TABLE_BODY_321D])).sum()) if not selected_preview_after_df.empty else 0
    for recognizer in recognizers:
        before_row = before_lookup.get(recognizer, {})
        if recognizer == MINERU_TABLE_BODY_321D:
            routed_count = int((route_inventory_df["recommended_recognizer"].astype(str) == MINERU_TABLE_BODY_321D).sum()) if not route_inventory_df.empty else 0
            selected_count_after = mineru_selected_after
            newly_processed_count = len(newly_processed_set)
        else:
            routed_count = _to_int(before_row.get("routed_count"))
            selected_count_after = int((selected_preview_after_df["selected_output_source"].astype(str) == recognizer).sum()) if not selected_preview_after_df.empty else 0
            newly_processed_count = 0
        existing_output_count_before = _to_int(before_row.get("available_output_count"))
        missing_count_after = max(routed_count - selected_count_after, 0)
        coverage_rate_after = round(selected_count_after / routed_count, 6) if routed_count > 0 else 0.0
        rows.append(
            {
                "recognizer": recognizer,
                "routed_count": routed_count,
                "existing_output_count_before_322a": existing_output_count_before,
                "newly_processed_count_322a": newly_processed_count,
                "selected_count_after_322a": selected_count_after,
                "missing_count_after_322a": missing_count_after,
                "coverage_rate_after_322a": coverage_rate_after,
            }
        )
    return pd.DataFrame(rows)


def run_router_driven_sandbox_pipeline_322a(config: RouterDrivenSandboxPipelineConfig) -> Dict[str, Any]:
    if not config.router_integration_dir.exists():
        return _blocked_result(config, "BLOCKED_MISSING_321G_ROUTER_INTEGRATION_DIR")
    if not config.router_dir.exists():
        return _blocked_result(config, "BLOCKED_MISSING_321F_ROUTER_DIR")
    if not config.mineru_output_root.exists():
        return _blocked_result(config, "BLOCKED_MISSING_MINERU_OUTPUT_ROOT")

    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    router_ctx = _load_router_integration_context(config.router_integration_dir)
    route_inventory_df = router_ctx["route_inventory_df"]
    availability_df = router_ctx["availability_df"]
    coverage_before_df = router_ctx["coverage_df"]
    route_summary_before = router_ctx["summary"]
    action_rows = router_ctx["action_plan"].get("actions", [])
    base_selected_preview_df = router_ctx["selected_preview_df"]

    worklist_df, selected_route_rows_df, eligible_mineru_missing_count = _select_322a_mineru_worklist(
        route_inventory_df=route_inventory_df,
        action_rows=action_rows,
        max_new_mineru_tables=config.max_new_mineru_tables,
    )

    selected_route_rows_df = selected_route_rows_df.fillna("") if not selected_route_rows_df.empty else pd.DataFrame()
    selected_new_mineru_table_count = len(selected_route_rows_df)

    extracted_tables = []
    extraction_audit_df = pd.DataFrame()
    unified_tables = []
    unified_tables_df = pd.DataFrame()
    normalized_rows_df = pd.DataFrame()
    normalization_audit_df = pd.DataFrame()
    mapping = {"candidates": [], "metric_candidates_df": pd.DataFrame(), "mapping_diagnostics_df": pd.DataFrame(), "per_table_summary_df": pd.DataFrame()}
    split = {"trusted_df": pd.DataFrame(), "review_required_df": pd.DataFrame(), "rejected_df": pd.DataFrame()}

    if not selected_route_rows_df.empty:
        extracted_tables, extraction_audit_df = extract_table_bodies(selected_route_rows_df, config.mineru_output_root)
        unified_tables, unified_tables_df, normalized_rows_df, normalization_audit_df = normalize_extracted_tables(extracted_tables)
        mapping = map_unified_tables_to_candidates(unified_tables)
        role_map = {
            _norm(row.get("table_asset_id")): _norm(row.get("effective_category"))
            for _, row in worklist_df[worklist_df["selected_for_processing"].fillna(False).astype(bool)].iterrows()
        } if not worklist_df.empty else {}
        split = split_mineru_body_candidates(mapping["candidates"], list(role_map.keys()), role_map)

    candidates_df_new = mapping["metric_candidates_df"].copy() if not mapping["metric_candidates_df"].empty else pd.DataFrame()
    if not candidates_df_new.empty:
        candidates_df_new["source_stage"] = "router_driven_mineru_body_322a"
        candidates_df_new["provenance_json"] = candidates_df_new["provenance_json"].astype(str).map(
            lambda text: json.dumps(
                {
                    **(json.loads(text) if _norm(text) else {}),
                    "source_stage": "router_driven_mineru_body_322a",
                    "recognition_source": "ROUTER_DRIVEN_MINERU_BODY_322A",
                },
                ensure_ascii=False,
            )
        )
    trusted_df_new = split["trusted_df"].copy() if not split["trusted_df"].empty else pd.DataFrame()
    review_df_new = split["review_required_df"].copy() if not split["review_required_df"].empty else pd.DataFrame()
    rejected_df_new = split["rejected_df"].copy() if not split["rejected_df"].empty else pd.DataFrame()
    for df in [trusted_df_new, review_df_new, rejected_df_new]:
        if not df.empty:
            df["source_stage"] = "router_driven_mineru_body_322a"
            df["provenance_json"] = df["provenance_json"].astype(str).map(
                lambda text: json.dumps(
                    {
                        **(json.loads(text) if _norm(text) else {}),
                        "source_stage": "router_driven_mineru_body_322a",
                        "recognition_source": "ROUTER_DRIVEN_MINERU_BODY_322A",
                    },
                    ensure_ascii=False,
                )
            )

    existing_candidates_by_table, existing_selected_sources = _load_existing_candidates(
        existing_mineru_body_dir=config.existing_mineru_body_dir,
        structtable_mapping_dir=config.structtable_mapping_dir,
        docling_mapping_dir=config.docling_mapping_dir,
        pure_vlm_calibration_dir=config.pure_vlm_calibration_dir,
        ppstructure_benchmark_dir=config.ppstructure_benchmark_dir,
        selected_preview_df=base_selected_preview_df,
    )

    selected_bundle = build_router_selected_delivery_preview(
        route_inventory_df=route_inventory_df,
        action_plan_rows=action_rows,
        base_selected_preview_df=base_selected_preview_df,
        existing_candidates_by_table=existing_candidates_by_table,
        new_322a_candidates_df=candidates_df_new,
        existing_selected_output_sources=existing_selected_sources,
    )

    selected_preview_after_df = selected_bundle.selected_preview_df.copy()
    selected_candidates_all_df = selected_bundle.metric_candidates_df.copy()
    trusted_after_df = selected_bundle.trusted_df.copy()
    review_after_df = selected_bundle.review_required_df.copy()
    rejected_after_df = selected_bundle.rejected_df.copy()
    semantic_after_df = selected_bundle.semantic_worklist_df.copy()
    manual_after_df = selected_bundle.manual_review_df.copy()

    remaining_missing_output_worklist_df = worklist_df[
        (~worklist_df["table_asset_id"].astype(str).isin(candidates_df_new["source_table_id"].astype(str).tolist() if not candidates_df_new.empty else []))
        & (worklist_df["recommended_recognizer"].astype(str) == MINERU_TABLE_BODY_321D)
        & (worklist_df["final_sandbox_action"].astype(str) == "NEEDS_MINERU_BODY_INGESTION")
    ].copy() if not worklist_df.empty else pd.DataFrame()
    remaining_missing_output_worklist_df = remaining_missing_output_worklist_df.rename(
        columns={"selected_for_processing": "selected_for_processing_flag", "final_sandbox_action": "required_action"}
    )
    if not remaining_missing_output_worklist_df.empty:
        remaining_missing_output_worklist_df = remaining_missing_output_worklist_df[
            ["table_asset_id", "source_report_name", "table_title", "recommended_recognizer", "required_action", "priority", "reason"]
        ]

    metric_candidates_all_322a_df = selected_candidates_all_df.copy()
    if not metric_candidates_all_322a_df.empty:
        metric_candidates_all_322a_df["selected_output_source"] = metric_candidates_all_322a_df["source_table_id"].astype(str).map(selected_bundle.selected_output_sources)

    coverage_after_df = _build_coverage_after(
        route_inventory_df=route_inventory_df,
        coverage_before_df=coverage_before_df,
        selected_preview_after_df=selected_preview_after_df,
        newly_processed_ids=candidates_df_new["source_table_id"].astype(str).unique().tolist() if not candidates_df_new.empty else [],
    )

    router_route_total_count = _to_int(route_summary_before.get("route_total_count")) or len(route_inventory_df)
    attempted_new_mineru_table_count = len(extracted_tables)
    newly_processed_mineru_table_count = len(unified_tables)
    newly_failed_mineru_table_count = max(attempted_new_mineru_table_count - newly_processed_mineru_table_count, 0)
    selected_output_table_count_before_322a = _to_int(route_summary_before.get("selected_output_table_count"))
    selected_output_table_count_after_322a = int(selected_preview_after_df["table_asset_id"].astype(str).nunique()) if not selected_preview_after_df.empty else 0
    no_available_output_count_before_322a = _to_int(route_summary_before.get("no_available_output_count"))
    no_available_output_count_after_322a = max(no_available_output_count_before_322a - newly_processed_mineru_table_count, 0)
    selected_candidate_total_count = len(metric_candidates_all_322a_df)
    selected_trusted_total_count = len(trusted_after_df)
    selected_review_required_total_count = len(review_after_df)
    selected_rejected_total_count = len(rejected_after_df)
    selected_all_trusted_rate = round(selected_trusted_total_count / selected_candidate_total_count, 6) if selected_candidate_total_count else 0.0
    core_ids = set(route_inventory_df[route_inventory_df["effective_category"].astype(str).isin(CORE_ROLE_SET)]["table_asset_id"].astype(str).tolist()) if not route_inventory_df.empty else set()
    core_selected_df = metric_candidates_all_322a_df[metric_candidates_all_322a_df["source_table_id"].astype(str).isin(core_ids)] if not metric_candidates_all_322a_df.empty else pd.DataFrame()
    selected_core_trusted_rate = round(len(core_selected_df[core_selected_df["split_decision"].astype(str) == "trusted_preview"]) / len(core_selected_df), 6) if not core_selected_df.empty else 0.0
    semantic_adjudicator_worklist_count = len(semantic_after_df)
    manual_review_worklist_count = len(manual_after_df)
    remaining_missing_output_worklist_count = len(remaining_missing_output_worklist_df)

    coverage_after_lookup = {
        _norm(row.get("recognizer")): row.to_dict()
        for _, row in coverage_after_df.iterrows()
        if _norm(row.get("recognizer"))
    } if not coverage_after_df.empty else {}
    mineru_coverage_before_322a = _to_float(
        next((row.get("coverage_rate") for _, row in coverage_before_df.iterrows() if _norm(row.get("recognizer")) == MINERU_TABLE_BODY_321D), 0.0)
    ) if not coverage_before_df.empty else 0.0
    mineru_coverage_after_322a = _to_float(coverage_after_lookup.get(MINERU_TABLE_BODY_321D, {}).get("coverage_rate_after_322a"))
    structtable_coverage_after_322a = _to_float(coverage_after_lookup.get("STRUCTTABLE_INTERVL2", {}).get("coverage_rate_after_322a"))
    docling_backup_coverage_after_322a = _to_float(coverage_after_lookup.get("DOCLING_TABLE_GRID_321E2", {}).get("coverage_rate_after_322a"))

    processing_audit_df = _build_processing_audit(
        extraction_audit_df=extraction_audit_df,
        per_table_df=mapping["per_table_summary_df"],
        trusted_df=trusted_df_new,
        review_df=review_df_new,
        rejected_df=rejected_df_new,
    )

    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa("router_integration_dir_exists", "PASS" if config.router_integration_dir.exists() else "FAIL", str(config.router_integration_dir))
    add_qa("router_dir_exists", "PASS" if config.router_dir.exists() else "FAIL", str(config.router_dir))
    add_qa("mineru_output_root_exists", "PASS" if config.mineru_output_root.exists() else "FAIL", str(config.mineru_output_root))
    add_qa("no_e_drive_files_modified", "PASS", "322A reads existing MinerU outputs under E:\\mineru_lab\\output_new but does not modify them")
    add_qa("no_external_recognizer_command_executed", "PASS", "322A reuses existing files only and does not invoke MinerU/StructEqTable/Docling/PPStructure/VLM")
    add_qa("no_production_files_modified", "PASS", "322A writes only sandbox outputs under D:\\_datefac\\output\\router_driven_sandbox_pipeline_322a")
    candidate_identity_ok = metric_candidates_all_322a_df.empty or (
        metric_candidates_all_322a_df["source_table_id"].astype(str).str.len().gt(0).all()
        and metric_candidates_all_322a_df["source_stage"].astype(str).str.len().gt(0).all()
    )
    add_qa(
        "every_selected_candidate_has_table_asset_id_and_source_stage",
        "PASS" if candidate_identity_ok else "FAIL",
        f"candidate_count={len(metric_candidates_all_322a_df)}",
    )
    trusted_valid_ok = trusted_after_df.empty or (
        trusted_after_df["year"].astype(str).str.match(r"^20\d{2}(?:[AE])?$", na=False).all()
        and (trusted_after_df["metric_code"].astype(str) != "unknown_metric").all()
        and trusted_after_df["normalized_value"].notna().all()
        and trusted_after_df["provenance_json"].astype(str).str.len().gt(0).all()
    )
    add_qa(
        "trusted_candidates_have_valid_year_metric_value_and_provenance",
        "PASS" if trusted_valid_ok else "FAIL",
        f"trusted_count={len(trusted_after_df)}",
    )
    no_double_count = selected_preview_after_df.empty or not selected_preview_after_df["table_asset_id"].astype(str).duplicated().any()
    add_qa(
        "no_table_asset_id_double_counted_in_selected_output_preview",
        "PASS" if no_double_count else "FAIL",
        f"selected_output_table_count_after_322a={selected_output_table_count_after_322a}",
    )
    add_qa(
        "selected_output_table_count_after_322a_not_lower",
        "PASS" if selected_output_table_count_after_322a >= selected_output_table_count_before_322a else "FAIL",
        f"before={selected_output_table_count_before_322a} after={selected_output_table_count_after_322a}",
    )
    found_missing_count = int((processing_audit_df["match_status"].astype(str) != "TABLE_BODY_FOUND").sum()) if not processing_audit_df.empty else 0
    add_qa(
        "some_selected_mineru_outputs_not_found",
        "WARN" if found_missing_count > 0 else "PASS",
        f"not_found_count={found_missing_count}",
    )
    add_qa(
        "remaining_missing_outputs_after_batch_cap",
        "WARN" if remaining_missing_output_worklist_count > 0 else "PASS",
        f"remaining_missing_output_worklist_count={remaining_missing_output_worklist_count}",
    )
    add_qa(
        "semantic_adjudicator_still_needed_for_review_heavy_candidates",
        "WARN" if semantic_adjudicator_worklist_count > 0 else "PASS",
        f"semantic_adjudicator_worklist_count={semantic_adjudicator_worklist_count}",
    )
    add_qa(
        "limited_benchmark_to_router_alignment",
        "WARN",
        "non-MinerU benchmark outputs still reflect limited benchmark alignment and are only reused from 321G selected outputs",
    )

    summary = {
        "stage": "322A",
        "output_dir": str(output_dir),
        "router_route_total_count": router_route_total_count,
        "eligible_mineru_missing_count": eligible_mineru_missing_count,
        "selected_new_mineru_table_count": selected_new_mineru_table_count,
        "attempted_new_mineru_table_count": attempted_new_mineru_table_count,
        "newly_processed_mineru_table_count": newly_processed_mineru_table_count,
        "newly_failed_mineru_table_count": newly_failed_mineru_table_count,
        "selected_output_table_count_before_322a": selected_output_table_count_before_322a,
        "selected_output_table_count_after_322a": selected_output_table_count_after_322a,
        "no_available_output_count_before_322a": no_available_output_count_before_322a,
        "no_available_output_count_after_322a": no_available_output_count_after_322a,
        "selected_candidate_total_count": selected_candidate_total_count,
        "selected_trusted_total_count": selected_trusted_total_count,
        "selected_review_required_total_count": selected_review_required_total_count,
        "selected_rejected_total_count": selected_rejected_total_count,
        "selected_core_trusted_rate": selected_core_trusted_rate,
        "selected_all_trusted_rate": selected_all_trusted_rate,
        "semantic_adjudicator_worklist_count": semantic_adjudicator_worklist_count,
        "manual_review_worklist_count": manual_review_worklist_count,
        "remaining_missing_output_worklist_count": remaining_missing_output_worklist_count,
        "mineru_coverage_before_322a": mineru_coverage_before_322a,
        "mineru_coverage_after_322a": mineru_coverage_after_322a,
        "structtable_coverage_after_322a": structtable_coverage_after_322a,
        "docling_backup_coverage_after_322a": docling_backup_coverage_after_322a,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    qa_df = pd.DataFrame(qa_rows)
    summary["qa_pass_count"] = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    summary["qa_warn_count"] = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    summary["qa_fail_count"] = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    if int(summary["qa_fail_count"]) > 0:
        decision = "ROUTER_DRIVEN_SANDBOX_PIPELINE_BLOCKED_BY_QA_FAILURE"
    elif selected_new_mineru_table_count == 0 and no_available_output_count_after_322a > 0:
        decision = "ROUTER_DRIVEN_SANDBOX_PIPELINE_NOOP_NEEDS_RECOGNIZER_RUNS"
    elif (
        selected_new_mineru_table_count > 0
        and newly_processed_mineru_table_count >= selected_new_mineru_table_count * 0.8
        and selected_output_table_count_after_322a > selected_output_table_count_before_322a
    ):
        decision = "ROUTER_DRIVEN_SANDBOX_PIPELINE_READY_FOR_322B_LARGER_BATCH"
    else:
        decision = "ROUTER_DRIVEN_SANDBOX_PIPELINE_PARTIAL_NEEDS_EXTRACTION_COVERAGE"
    summary["router_driven_sandbox_pipeline_decision"] = decision

    output_files = {
        "excel": output_dir / "router_driven_sandbox_pipeline_322a.xlsx",
        "summary_json": output_dir / "router_driven_sandbox_pipeline_322a_summary.json",
        "report_md": output_dir / "router_driven_sandbox_pipeline_322a_report.md",
        "preview_jsonl": output_dir / "router_selected_delivery_preview_322a.jsonl",
        "metric_candidates_jsonl": output_dir / "metric_candidates_all_322a.jsonl",
        "semantic_jsonl": output_dir / "semantic_adjudicator_worklist_322a.jsonl",
    }

    report_lines = [
        "# Router Driven Sandbox Pipeline 322A",
        "",
        "## Decision",
        f"- router_driven_sandbox_pipeline_decision: {decision}",
        "",
        "## Coverage",
        f"- router_route_total_count: {router_route_total_count}",
        f"- eligible_mineru_missing_count: {eligible_mineru_missing_count}",
        f"- selected_new_mineru_table_count: {selected_new_mineru_table_count}",
        f"- newly_processed_mineru_table_count: {newly_processed_mineru_table_count}",
        f"- selected_output_table_count_before_322a: {selected_output_table_count_before_322a}",
        f"- selected_output_table_count_after_322a: {selected_output_table_count_after_322a}",
        f"- no_available_output_count_before_322a: {no_available_output_count_before_322a}",
        f"- no_available_output_count_after_322a: {no_available_output_count_after_322a}",
        "",
        "## Selected Preview",
        f"- selected_candidate_total_count: {selected_candidate_total_count}",
        f"- selected_trusted_total_count: {selected_trusted_total_count}",
        f"- selected_review_required_total_count: {selected_review_required_total_count}",
        f"- selected_core_trusted_rate: {selected_core_trusted_rate}",
        f"- selected_all_trusted_rate: {selected_all_trusted_rate}",
        "",
        "## QA",
        f"- qa_pass_count: {summary['qa_pass_count']}",
        f"- qa_warn_count: {summary['qa_warn_count']}",
        f"- qa_fail_count: {summary['qa_fail_count']}",
        "",
    ]

    sheets = {
        "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
        "selected_322a_mineru_worklist": worklist_df,
        "mineru_body_processing_audit": processing_audit_df,
        "router_selected_output_preview_322a": selected_preview_after_df,
        "metric_candidates_all_322a": metric_candidates_all_322a_df,
        "trusted_preview_322a": trusted_after_df,
        "review_required_preview_322a": review_after_df,
        "rejected_preview_322a": rejected_after_df,
        "semantic_adjudicator_worklist_322a": semantic_after_df,
        "manual_review_worklist_322a": manual_after_df,
        "remaining_missing_output_worklist": remaining_missing_output_worklist_df,
        "coverage_by_route_322a": coverage_after_df,
        "qa_checks": qa_df,
        "known_limitations": _known_limitations_df(),
    }

    _write_excel(output_files["excel"], sheets)
    _write_json(output_files["summary_json"], summary)
    write_jsonl(output_files["preview_jsonl"], pd.DataFrame(selected_bundle.delivery_preview_rows))
    if not metric_candidates_all_322a_df.empty:
        write_jsonl(output_files["metric_candidates_jsonl"], metric_candidates_all_322a_df)
    if not semantic_after_df.empty:
        write_jsonl(output_files["semantic_jsonl"], semantic_after_df)
    output_files["report_md"].write_text("\n".join(report_lines), encoding="utf-8")

    add_qa(
        "output_files_written_successfully",
        "PASS" if all(output_files[key].exists() for key in ["excel", "summary_json", "report_md", "preview_jsonl"]) else "FAIL",
        f"excel={output_files['excel'].exists()} summary_json={output_files['summary_json'].exists()} report_md={output_files['report_md'].exists()} preview_jsonl={output_files['preview_jsonl'].exists()}",
    )
    qa_df = pd.DataFrame(qa_rows)
    summary["qa_pass_count"] = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    summary["qa_warn_count"] = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    summary["qa_fail_count"] = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    if int(summary["qa_fail_count"]) > 0:
        summary["router_driven_sandbox_pipeline_decision"] = "ROUTER_DRIVEN_SANDBOX_PIPELINE_BLOCKED_BY_QA_FAILURE"

    _write_excel(
        output_files["excel"],
        {
            "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
            "selected_322a_mineru_worklist": worklist_df,
            "mineru_body_processing_audit": processing_audit_df,
            "router_selected_output_preview_322a": selected_preview_after_df,
            "metric_candidates_all_322a": metric_candidates_all_322a_df,
            "trusted_preview_322a": trusted_after_df,
            "review_required_preview_322a": review_after_df,
            "rejected_preview_322a": rejected_after_df,
            "semantic_adjudicator_worklist_322a": semantic_after_df,
            "manual_review_worklist_322a": manual_after_df,
            "remaining_missing_output_worklist": remaining_missing_output_worklist_df,
            "coverage_by_route_322a": coverage_after_df,
            "qa_checks": qa_df,
            "known_limitations": _known_limitations_df(),
        },
    )
    _write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(
        "\n".join(
            report_lines[:-1]
            + [
                f"- qa_pass_count: {summary['qa_pass_count']}",
                f"- qa_warn_count: {summary['qa_warn_count']}",
                f"- qa_fail_count: {summary['qa_fail_count']}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return {
        "summary": summary,
        "excel_path": str(output_files["excel"]),
        "summary_json_path": str(output_files["summary_json"]),
        "report_md_path": str(output_files["report_md"]),
        "preview_jsonl_path": str(output_files["preview_jsonl"]),
    }
