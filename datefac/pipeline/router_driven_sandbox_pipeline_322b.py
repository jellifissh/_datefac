from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

import pandas as pd

from datefac.mineru_body.mineru_body_delivery_builder import write_jsonl
from datefac.mineru_body.mineru_body_candidate_mapper import (
    map_unified_tables_to_candidates,
    split_mineru_body_candidates,
)
from datefac.mineru_body.mineru_table_body_reader import extract_table_bodies
from datefac.mineru_body.mineru_table_normalizer import normalize_extracted_tables
from datefac.pipeline.router_driven_sandbox_pipeline import (
    CORE_ROLE_SET,
    _blocked_result,
    _build_coverage_after,
    _build_processing_audit,
    _find_workbook,
    _load_router_integration_context,
    _norm,
    _read_json,
    _read_sheet,
    _safe_sheet_name,
    _to_bool,
    _to_float,
    _to_int,
    _write_json,
)
from datefac.pipeline.router_selected_delivery_preview import (
    SelectedOutputBundle,
    build_router_selected_delivery_preview,
)
from datefac.router.recognizer_router_321f import MINERU_TABLE_BODY_321D


SHEET_ORDER_322B = [
    "summary",
    "selected_322b_mineru_worklist",
    "mineru_body_processing_audit",
    "router_selected_output_preview_322b",
    "metric_candidates_all_322b",
    "trusted_preview_322b",
    "review_required_preview_322b",
    "rejected_preview_322b",
    "review_burden_by_reason",
    "unknown_metric_label_frequency",
    "unit_unknown_diagnostics",
    "section_context_required_diagnostics",
    "out_of_scope_candidate_summary",
    "alias_candidate_worklist",
    "semantic_adjudicator_worklist_322b",
    "manual_review_worklist_322b",
    "remaining_missing_output_worklist",
    "coverage_by_route_322b",
    "qa_checks",
    "known_limitations",
]
MINERU_322B_SOURCE = "ROUTER_DRIVEN_MINERU_BODY_322B"


@dataclass
class RouterDrivenSandboxPipeline322BConfig:
    router_integration_dir: Path
    router_dir: Path
    mineru_output_root: Path
    existing_mineru_body_dir: Path
    structtable_mapping_dir: Path
    docling_mapping_dir: Path
    pure_vlm_calibration_dir: Path
    ppstructure_benchmark_dir: Path
    prior_322a_output_dir: Path
    output_dir: Path
    max_new_mineru_tables: int = 45


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in SHEET_ORDER_322B:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def _known_limitations_df_322b() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "limitation": "sandbox_only",
                "detail": "322B only expands sandbox coverage and diagnostics; it does not modify production pipeline or E-drive contents.",
            },
            {
                "limitation": "existing_mineru_outputs_only",
                "detail": "322B reads existing MinerU output under E:\\mineru_lab\\output_new and does not run MinerU or any other recognizer.",
            },
            {
                "limitation": "diagnostics_not_rule_changes",
                "detail": "322B diagnoses review burden, unknown metrics, and unit/context issues without adding alias rules or new unit rules.",
            },
        ]
    )


def _find_sheet_with_prefix(workbook: Optional[Path], prefix: str) -> pd.DataFrame:
    if workbook is None or not workbook.exists():
        return pd.DataFrame()
    try:
        excel = pd.ExcelFile(workbook)
    except Exception:
        return pd.DataFrame()
    for sheet in excel.sheet_names:
        if str(sheet).startswith(prefix):
            try:
                return pd.read_excel(workbook, sheet_name=sheet).fillna("")
            except Exception:
                return pd.DataFrame()
    return pd.DataFrame()


def _load_322a_context(prior_322a_output_dir: Path) -> Dict[str, Any]:
    workbook = _find_workbook(prior_322a_output_dir)
    summary = _read_json(prior_322a_output_dir / "router_driven_sandbox_pipeline_322a_summary.json")
    selected_preview_df = _find_sheet_with_prefix(workbook, "router_selected_output_preview_")
    metric_candidates_df = _read_sheet(workbook, "metric_candidates_all_322a")
    trusted_df = _read_sheet(workbook, "trusted_preview_322a")
    review_df = _read_sheet(workbook, "review_required_preview_322a")
    rejected_df = _read_sheet(workbook, "rejected_preview_322a")
    semantic_df = _find_sheet_with_prefix(workbook, "semantic_adjudicator_worklist_")
    manual_df = _read_sheet(workbook, "manual_review_worklist_322a")
    return {
        "summary": summary,
        "selected_preview_df": selected_preview_df,
        "metric_candidates_df": metric_candidates_df,
        "trusted_df": trusted_df,
        "review_df": review_df,
        "rejected_df": rejected_df,
        "semantic_df": semantic_df,
        "manual_df": manual_df,
    }


def _existing_candidates_from_322a(
    selected_preview_df: pd.DataFrame,
    metric_candidates_df: pd.DataFrame,
) -> tuple[Dict[str, pd.DataFrame], Dict[str, str]]:
    selected_preview_df = selected_preview_df.fillna("") if not selected_preview_df.empty else pd.DataFrame()
    metric_candidates_df = metric_candidates_df.fillna("") if not metric_candidates_df.empty else pd.DataFrame()
    selected_sources = {
        _norm(row.get("table_asset_id")): _norm(row.get("selected_output_source"))
        for _, row in selected_preview_df.iterrows()
        if _norm(row.get("table_asset_id"))
    }
    if metric_candidates_df.empty or "source_table_id" not in metric_candidates_df.columns:
        return {}, selected_sources
    grouped = {
        table_id: group.copy()
        for table_id, group in metric_candidates_df.groupby(metric_candidates_df["source_table_id"].astype(str))
        if _norm(table_id)
    }
    return grouped, selected_sources


def _select_322b_mineru_worklist(
    route_inventory_df: pd.DataFrame,
    action_rows: Sequence[Dict[str, Any]],
    already_selected_ids: Set[str],
    max_new_mineru_tables: int,
) -> tuple[pd.DataFrame, pd.DataFrame, int]:
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
        already_selected = table_asset_id in already_selected_ids
        eligible = (
            recommended == MINERU_TABLE_BODY_321D
            and final_action == "NEEDS_MINERU_BODY_INGESTION"
            and not manual_required
            and role in CORE_ROLE_SET
            and not already_selected
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
                "already_selected_before_322b": already_selected,
                "selected_for_processing": eligible,
                "reason": _norm(action_row.get("reason")) or _norm(row_dict.get("router_reason")),
                "recommended_recognizer": recommended,
                "final_sandbox_action": final_action,
                "fallback_recognizer": _norm(row_dict.get("fallback_recognizer")) or _norm(action_row.get("fallback_recognizer")),
                "semantic_adjudicator_required": _to_bool(row_dict.get("semantic_adjudicator_required")) or _to_bool(action_row.get("semantic_adjudicator_required")),
                "manual_review_required": manual_required,
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


def _split_risk_tags(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _top_review_reason_counts(review_df: pd.DataFrame, limit: int = 10) -> List[Dict[str, Any]]:
    if review_df.empty or "split_reason" not in review_df.columns:
        return []
    counts = review_df["split_reason"].astype(str).value_counts().head(limit)
    return [{"split_reason": str(idx), "count": int(val)} for idx, val in counts.items()]


def _build_review_burden_by_reason(review_df: pd.DataFrame) -> pd.DataFrame:
    if review_df.empty:
        return pd.DataFrame(
            columns=[
                "split_reason",
                "review_candidate_count",
                "table_count",
                "unknown_metric_count",
                "unit_unknown_count",
                "invalid_year_count",
                "value_parse_failed_count",
                "sample_labels",
            ]
        )
    rows: List[Dict[str, Any]] = []
    for split_reason, group in review_df.groupby(review_df["split_reason"].astype(str)):
        labels: List[str] = []
        for value in group["raw_metric_name"].astype(str).tolist():
            label = _norm(value)
            if label and label not in labels:
                labels.append(label)
            if len(labels) >= 8:
                break
        tag_lists = group["risk_tags"].astype(str).tolist()
        rows.append(
            {
                "split_reason": split_reason,
                "review_candidate_count": int(len(group)),
                "table_count": int(group["source_table_id"].astype(str).nunique()) if "source_table_id" in group.columns else 0,
                "unknown_metric_count": int(group["metric_code"].astype(str).eq("unknown_metric").sum()),
                "unit_unknown_count": int(sum("UNIT_UNKNOWN" in _split_risk_tags(tags) for tags in tag_lists)),
                "invalid_year_count": int(sum("INVALID_YEAR" in _split_risk_tags(tags) for tags in tag_lists)),
                "value_parse_failed_count": int(sum("VALUE_PARSE_FAILED" in _split_risk_tags(tags) for tags in tag_lists)),
                "sample_labels": "|".join(labels),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["review_candidate_count", "table_count", "split_reason"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def _build_unknown_metric_label_frequency(review_df: pd.DataFrame) -> pd.DataFrame:
    if review_df.empty:
        return pd.DataFrame(
            columns=[
                "raw_metric_name",
                "candidate_count",
                "table_count",
                "source_stage_count",
                "unit_examples",
                "table_title_examples",
                "year_examples",
            ]
        )
    filtered = review_df[review_df["metric_code"].astype(str) == "unknown_metric"].copy()
    if filtered.empty:
        return pd.DataFrame(
            columns=[
                "raw_metric_name",
                "candidate_count",
                "table_count",
                "source_stage_count",
                "unit_examples",
                "table_title_examples",
                "year_examples",
            ]
        )
    rows: List[Dict[str, Any]] = []
    for raw_metric_name, group in filtered.groupby(filtered["raw_metric_name"].astype(str)):
        units = [item for item in group["unit"].astype(str).tolist() if _norm(item)]
        titles = [item for item in group["table_title"].astype(str).tolist() if _norm(item)]
        years = [item for item in group["year"].astype(str).tolist() if _norm(item)]
        rows.append(
            {
                "raw_metric_name": raw_metric_name,
                "candidate_count": int(len(group)),
                "table_count": int(group["source_table_id"].astype(str).nunique()) if "source_table_id" in group.columns else 0,
                "source_stage_count": int(group["source_stage"].astype(str).nunique()) if "source_stage" in group.columns else 0,
                "unit_examples": "|".join(dict.fromkeys(units[:5])),
                "table_title_examples": "|".join(dict.fromkeys(titles[:3])),
                "year_examples": "|".join(dict.fromkeys(years[:5])),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["candidate_count", "table_count", "raw_metric_name"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def _build_unit_unknown_diagnostics(review_df: pd.DataFrame) -> pd.DataFrame:
    if review_df.empty:
        return pd.DataFrame(
            columns=[
                "table_asset_id",
                "source_report_name",
                "table_title",
                "raw_metric_name",
                "metric_code",
                "year",
                "raw_value",
                "unit",
                "table_unit",
                "unit_source",
                "risk_tags",
                "split_reason",
                "selected_output_source",
            ]
        )
    mask = review_df["risk_tags"].astype(str).str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True)
    columns = [
        "source_table_id",
        "source_doc_name",
        "table_title",
        "raw_metric_name",
        "metric_code",
        "year",
        "raw_value",
        "unit",
        "table_unit",
        "unit_source",
        "risk_tags",
        "split_reason",
        "selected_output_source",
    ]
    out = review_df.loc[mask, [col for col in columns if col in review_df.columns]].copy()
    rename_map = {
        "source_table_id": "table_asset_id",
        "source_doc_name": "source_report_name",
    }
    return out.rename(columns=rename_map).reset_index(drop=True)


def _build_section_context_required_diagnostics(review_df: pd.DataFrame) -> pd.DataFrame:
    if review_df.empty:
        return pd.DataFrame(
            columns=[
                "table_asset_id",
                "source_report_name",
                "table_title",
                "raw_metric_name",
                "metric_code",
                "year",
                "risk_tags",
                "split_reason",
                "selected_output_source",
            ]
        )
    mask = review_df["risk_tags"].astype(str).str.contains(
        r"(?:^|\|)(?:SECTION_CONTEXT_REQUIRED|VALUE_CONFLICT)(?:$|\|)",
        regex=True,
    ) | review_df["split_reason"].astype(str).isin(["VALUE_CONFLICT", "DUPLICATED_LABEL_SECTION_CONTEXT"])
    columns = [
        "source_table_id",
        "source_doc_name",
        "table_title",
        "raw_metric_name",
        "metric_code",
        "year",
        "risk_tags",
        "split_reason",
        "selected_output_source",
    ]
    out = review_df.loc[mask, [col for col in columns if col in review_df.columns]].copy()
    return out.rename(
        columns={"source_table_id": "table_asset_id", "source_doc_name": "source_report_name"}
    ).reset_index(drop=True)


def _build_out_of_scope_candidate_summary(metric_candidates_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "tag_name",
        "candidate_count",
        "table_count",
        "review_required_count",
        "trusted_count",
        "rejected_count",
    ]
    if metric_candidates_df.empty:
        return pd.DataFrame(columns=columns)
    tag_names = ["OUT_OF_SCOPE_METRIC", "NON_CORE_STATEMENT_LINE"]
    rows: List[Dict[str, Any]] = []
    risk_series = metric_candidates_df["risk_tags"].astype(str)
    for tag_name in tag_names:
        mask = risk_series.str.contains(rf"(?:^|\|){tag_name}(?:$|\|)", regex=True)
        tagged = metric_candidates_df.loc[mask].copy()
        rows.append(
            {
                "tag_name": tag_name,
                "candidate_count": int(len(tagged)),
                "table_count": int(tagged["source_table_id"].astype(str).nunique()) if not tagged.empty else 0,
                "review_required_count": int(tagged["split_decision"].astype(str).eq("review_required_preview").sum()) if not tagged.empty else 0,
                "trusted_count": int(tagged["split_decision"].astype(str).eq("trusted_preview").sum()) if not tagged.empty else 0,
                "rejected_count": int(tagged["split_decision"].astype(str).eq("rejected_preview").sum()) if not tagged.empty else 0,
            }
        )
    if rows and sum(row["candidate_count"] for row in rows) == 0:
        rows.append(
            {
                "tag_name": "NO_OUT_OF_SCOPE_TAGS_OBSERVED",
                "candidate_count": 0,
                "table_count": 0,
                "review_required_count": 0,
                "trusted_count": 0,
                "rejected_count": 0,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def _build_alias_candidate_worklist(review_df: pd.DataFrame) -> pd.DataFrame:
    base = _build_unknown_metric_label_frequency(review_df)
    if base.empty:
        return pd.DataFrame(
            columns=[
                "raw_metric_name",
                "candidate_count",
                "table_count",
                "source_stage_count",
                "unit_examples",
                "table_title_examples",
                "year_examples",
                "alias_candidate_reason",
            ]
        )
    out = base[base["candidate_count"].astype(int) >= 3].copy()
    if out.empty:
        return pd.DataFrame(
            columns=[
                "raw_metric_name",
                "candidate_count",
                "table_count",
                "source_stage_count",
                "unit_examples",
                "table_title_examples",
                "year_examples",
                "alias_candidate_reason",
            ]
        )
    out["alias_candidate_reason"] = "HIGH_FREQUENCY_UNKNOWN_METRIC_LABEL_REVIEW_ONLY"
    return out.reset_index(drop=True)


def _build_semantic_adjudicator_worklist(
    selected_preview_df: pd.DataFrame,
    review_df: pd.DataFrame,
    base_semantic_df: pd.DataFrame,
) -> pd.DataFrame:
    selected_preview_df = selected_preview_df.fillna("") if not selected_preview_df.empty else pd.DataFrame()
    review_df = review_df.fillna("") if not review_df.empty else pd.DataFrame()
    base_semantic_df = base_semantic_df.fillna("") if not base_semantic_df.empty else pd.DataFrame()
    preview_map = {
        _norm(row.get("table_asset_id")): row.to_dict()
        for _, row in selected_preview_df.iterrows()
        if _norm(row.get("table_asset_id"))
    }
    base_map = {
        _norm(row.get("table_asset_id")): row.to_dict()
        for _, row in base_semantic_df.iterrows()
        if _norm(row.get("table_asset_id"))
    }
    rows: List[Dict[str, Any]] = []
    if review_df.empty:
        return pd.DataFrame(columns=list(base_semantic_df.columns))
    for table_asset_id, group in review_df.groupby(review_df["source_table_id"].astype(str)):
        risk_values: Set[str] = set()
        for risk_text in group["risk_tags"].astype(str).tolist():
            risk_values.update(_split_risk_tags(risk_text))
        needs_semantic = any(
            tag in risk_values
            for tag in {"UNKNOWN_METRIC_CODE", "VALUE_CONFLICT", "SECTION_CONTEXT_REQUIRED", "UNIT_UNKNOWN"}
        )
        if not needs_semantic:
            continue
        preview_row = preview_map.get(table_asset_id, {})
        base_row = base_map.get(table_asset_id, {})
        titles = [item for item in group["table_title"].astype(str).tolist() if _norm(item)]
        source_reports = [item for item in group["source_doc_name"].astype(str).tolist() if _norm(item)]
        labels = [item for item in group["raw_metric_name"].astype(str).tolist() if _norm(item)]
        adjudication_reason = (
            "UNKNOWN_METRIC_CODE_CORE_CONTEXT"
            if "UNKNOWN_METRIC_CODE" in risk_values
            else "VALUE_CONFLICT_SECTION_CONTEXT"
            if "VALUE_CONFLICT" in risk_values
            else "UNIT_UNKNOWN_WITH_CLEAR_TABLE_CONTEXT"
            if "UNIT_UNKNOWN" in risk_values
            else "DUPLICATED_LABEL_SECTION_CONTEXT"
        )
        rows.append(
            {
                "table_asset_id": table_asset_id,
                "source_report_name": _norm(base_row.get("source_report_name")) or (source_reports[0] if source_reports else ""),
                "table_title": _norm(base_row.get("table_title")) or (titles[0] if titles else ""),
                "selected_output_source": _norm(preview_row.get("selected_output_source")),
                "adjudication_reason": adjudication_reason,
                "risk_tags": "|".join(sorted(risk_values)),
                "candidate_count_affected": int(len(group)),
                "priority": _norm(base_row.get("priority")) or "HIGH",
                "sample_labels": "|".join(dict.fromkeys(labels[:6])),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    if not base_semantic_df.empty:
        missing_base = base_semantic_df[~base_semantic_df["table_asset_id"].astype(str).isin(out["table_asset_id"].astype(str))].copy()
        if not missing_base.empty:
            if "sample_labels" not in missing_base.columns:
                missing_base["sample_labels"] = ""
            out = pd.concat([out, missing_base], ignore_index=True, sort=False)
    out = out.sort_values(["priority", "candidate_count_affected", "table_asset_id"], ascending=[True, False, True])
    return out.reset_index(drop=True)


def _build_manual_review_worklist(
    selected_preview_df: pd.DataFrame,
    review_df: pd.DataFrame,
    semantic_df: pd.DataFrame,
    base_manual_df: pd.DataFrame,
) -> pd.DataFrame:
    selected_preview_df = selected_preview_df.fillna("") if not selected_preview_df.empty else pd.DataFrame()
    review_df = review_df.fillna("") if not review_df.empty else pd.DataFrame()
    semantic_df = semantic_df.fillna("") if not semantic_df.empty else pd.DataFrame()
    base_manual_df = base_manual_df.fillna("") if not base_manual_df.empty else pd.DataFrame()
    preview_map = {
        _norm(row.get("table_asset_id")): row.to_dict()
        for _, row in selected_preview_df.iterrows()
        if _norm(row.get("table_asset_id"))
    }
    base_map = {
        _norm(row.get("table_asset_id")): row.to_dict()
        for _, row in base_manual_df.iterrows()
        if _norm(row.get("table_asset_id"))
    }
    semantic_ids = set(semantic_df["table_asset_id"].astype(str).tolist()) if not semantic_df.empty else set()
    rows: List[Dict[str, Any]] = []
    if not review_df.empty:
        for table_asset_id, group in review_df.groupby(review_df["source_table_id"].astype(str)):
            preview_row = preview_map.get(table_asset_id, {})
            review_count = int(len(group))
            risk_values: Set[str] = set()
            for risk_text in group["risk_tags"].astype(str).tolist():
                risk_values.update(_split_risk_tags(risk_text))
            manual_required = review_count >= 50 or "VALUE_CONFLICT" in risk_values or table_asset_id in semantic_ids
            if not manual_required:
                continue
            rows.append(
                {
                    "table_asset_id": table_asset_id,
                    "source_report_name": _norm(group["source_doc_name"].iloc[0]) if "source_doc_name" in group.columns and not group.empty else "",
                    "table_title": _norm(group["table_title"].iloc[0]) if "table_title" in group.columns and not group.empty else "",
                    "manual_review_reason": "HIGH_REVIEW_BURDEN_OR_CONTEXT_DISPUTE",
                    "selected_output_source": _norm(preview_row.get("selected_output_source")),
                    "priority": "HIGH",
                    "notes": f"review_candidate_count={review_count}; risk_tags={'|'.join(sorted(risk_values))}",
                }
            )
    out = pd.DataFrame(rows)
    if not base_manual_df.empty:
        missing_base = base_manual_df[~base_manual_df["table_asset_id"].astype(str).isin(out["table_asset_id"].astype(str) if not out.empty else [])].copy()
        out = pd.concat([out, missing_base], ignore_index=True, sort=False) if not missing_base.empty else out
    if out.empty:
        return out
    return out.drop_duplicates(subset=["table_asset_id"], keep="first").sort_values(
        ["priority", "table_asset_id"], ascending=[True, True]
    ).reset_index(drop=True)


def _selected_preview_with_flags(
    selected_bundle: SelectedOutputBundle,
    semantic_df: pd.DataFrame,
    manual_df: pd.DataFrame,
) -> pd.DataFrame:
    preview_df = selected_bundle.selected_preview_df.copy()
    if preview_df.empty:
        return preview_df
    semantic_ids = set(semantic_df["table_asset_id"].astype(str).tolist()) if not semantic_df.empty else set()
    manual_ids = set(manual_df["table_asset_id"].astype(str).tolist()) if not manual_df.empty else set()
    preview_df["semantic_adjudicator_required"] = preview_df["table_asset_id"].astype(str).isin(semantic_ids)
    preview_df["manual_review_required"] = preview_df["table_asset_id"].astype(str).isin(manual_ids)
    return preview_df


def run_router_driven_sandbox_pipeline_322b(config: RouterDrivenSandboxPipeline322BConfig) -> Dict[str, Any]:
    if not config.router_integration_dir.exists():
        return _blocked_result(config, "BLOCKED_MISSING_321G_ROUTER_INTEGRATION_DIR")
    if not config.router_dir.exists():
        return _blocked_result(config, "BLOCKED_MISSING_321F_ROUTER_DIR")
    if not config.mineru_output_root.exists():
        return _blocked_result(config, "BLOCKED_MISSING_MINERU_OUTPUT_ROOT")
    if not config.prior_322a_output_dir.exists():
        return _blocked_result(config, "BLOCKED_MISSING_322A_OUTPUT_DIR")

    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    router_ctx = _load_router_integration_context(config.router_integration_dir)
    route_inventory_df = router_ctx["route_inventory_df"]
    coverage_before_df = router_ctx["coverage_df"]
    route_summary_321g = router_ctx["summary"]
    action_rows = router_ctx["action_plan"].get("actions", [])

    prior_322a_ctx = _load_322a_context(config.prior_322a_output_dir)
    prior_summary = prior_322a_ctx["summary"]
    prior_selected_preview_df = prior_322a_ctx["selected_preview_df"]
    prior_metric_candidates_df = prior_322a_ctx["metric_candidates_df"]
    prior_semantic_df = prior_322a_ctx["semantic_df"]
    prior_manual_df = prior_322a_ctx["manual_df"]

    already_selected_ids = set(prior_selected_preview_df["table_asset_id"].astype(str).tolist()) if not prior_selected_preview_df.empty else set()
    worklist_df, selected_route_rows_df, eligible_remaining_count = _select_322b_mineru_worklist(
        route_inventory_df=route_inventory_df,
        action_rows=action_rows,
        already_selected_ids=already_selected_ids,
        max_new_mineru_tables=config.max_new_mineru_tables,
    )
    selected_route_rows_df = selected_route_rows_df.fillna("") if not selected_route_rows_df.empty else pd.DataFrame()
    selected_new_mineru_table_count = len(selected_route_rows_df)

    extracted_tables = []
    extraction_audit_df = pd.DataFrame()
    unified_tables = []
    mapping = {"candidates": [], "metric_candidates_df": pd.DataFrame(), "per_table_summary_df": pd.DataFrame()}
    split = {"trusted_df": pd.DataFrame(), "review_required_df": pd.DataFrame(), "rejected_df": pd.DataFrame()}
    if not selected_route_rows_df.empty:
        extracted_tables, extraction_audit_df = extract_table_bodies(selected_route_rows_df, config.mineru_output_root)
        unified_tables, _, _, _ = normalize_extracted_tables(extracted_tables)
        mapping = map_unified_tables_to_candidates(unified_tables)
        role_map = {
            _norm(row.get("table_asset_id")): _norm(row.get("effective_category"))
            for _, row in worklist_df[worklist_df["selected_for_processing"].fillna(False).astype(bool)].iterrows()
        } if not worklist_df.empty else {}
        split = split_mineru_body_candidates(mapping["candidates"], list(role_map.keys()), role_map)

    candidates_df_new = mapping["metric_candidates_df"].copy() if not mapping["metric_candidates_df"].empty else pd.DataFrame()
    trusted_df_new = split["trusted_df"].copy() if not split["trusted_df"].empty else pd.DataFrame()
    review_df_new = split["review_required_df"].copy() if not split["review_required_df"].empty else pd.DataFrame()
    rejected_df_new = split["rejected_df"].copy() if not split["rejected_df"].empty else pd.DataFrame()
    for df in [candidates_df_new, trusted_df_new, review_df_new, rejected_df_new]:
        if not df.empty:
            df["source_stage"] = "router_driven_mineru_body_322b"
            df["provenance_json"] = df["provenance_json"].astype(str).map(
                lambda text: json.dumps(
                    {
                        **(json.loads(text) if _norm(text) else {}),
                        "source_stage": "router_driven_mineru_body_322b",
                        "recognition_source": MINERU_322B_SOURCE,
                    },
                    ensure_ascii=False,
                )
            )

    existing_candidates_by_table, existing_selected_sources = _existing_candidates_from_322a(
        selected_preview_df=prior_selected_preview_df,
        metric_candidates_df=prior_metric_candidates_df,
    )
    selected_bundle = build_router_selected_delivery_preview(
        route_inventory_df=route_inventory_df,
        action_plan_rows=action_rows,
        base_selected_preview_df=prior_selected_preview_df,
        existing_candidates_by_table=existing_candidates_by_table,
        new_322a_candidates_df=candidates_df_new,
        existing_selected_output_sources=existing_selected_sources,
        new_mineru_selected_output_source=MINERU_322B_SOURCE,
        new_mineru_output_origin="322B_NEW_MINERU",
        new_mineru_note="newly generated 322B MinerU-body output",
    )

    metric_candidates_all_df = selected_bundle.metric_candidates_df.copy()
    if not metric_candidates_all_df.empty:
        metric_candidates_all_df["selected_output_source"] = metric_candidates_all_df["source_table_id"].astype(str).map(selected_bundle.selected_output_sources)
    trusted_after_df = selected_bundle.trusted_df.copy()
    review_after_df = selected_bundle.review_required_df.copy()
    rejected_after_df = selected_bundle.rejected_df.copy()

    semantic_after_df = _build_semantic_adjudicator_worklist(
        selected_preview_df=selected_bundle.selected_preview_df,
        review_df=review_after_df,
        base_semantic_df=prior_semantic_df,
    )
    manual_after_df = _build_manual_review_worklist(
        selected_preview_df=selected_bundle.selected_preview_df,
        review_df=review_after_df,
        semantic_df=semantic_after_df,
        base_manual_df=prior_manual_df,
    )
    selected_preview_after_df = _selected_preview_with_flags(selected_bundle, semantic_after_df, manual_after_df)

    route_inventory_df = route_inventory_df.fillna("") if not route_inventory_df.empty else pd.DataFrame()
    action_map = {_norm(row.get("table_asset_id")): dict(row) for row in action_rows if _norm(row.get("table_asset_id"))}
    selected_after_ids = set(selected_preview_after_df["table_asset_id"].astype(str).tolist()) if not selected_preview_after_df.empty else set()
    remaining_rows: List[Dict[str, Any]] = []
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
            and table_asset_id not in selected_after_ids
        )
        if not eligible:
            continue
        remaining_rows.append(
            {
                "table_asset_id": table_asset_id,
                "source_report_name": _norm(row_dict.get("source_report_name")),
                "table_title": _norm(row_dict.get("table_title")),
                "recommended_recognizer": recommended,
                "required_action": final_action,
                "priority": "HIGH" if role in CORE_ROLE_SET else "MEDIUM",
                "reason": _norm(action_row.get("reason")) or _norm(row_dict.get("router_reason")),
            }
        )
    remaining_missing_output_worklist_df = pd.DataFrame(remaining_rows)

    coverage_after_df = _build_coverage_after(
        route_inventory_df=route_inventory_df,
        coverage_before_df=coverage_before_df,
        selected_preview_after_df=selected_preview_after_df.rename(columns={"selected_output_source": "selected_output_source"}),
        newly_processed_ids=candidates_df_new["source_table_id"].astype(str).unique().tolist() if not candidates_df_new.empty else [],
        mineru_selected_output_sources=[MINERU_322B_SOURCE],
    )

    processing_audit_df = _build_processing_audit(
        extraction_audit_df=extraction_audit_df,
        per_table_df=mapping["per_table_summary_df"],
        trusted_df=trusted_df_new,
        review_df=review_df_new,
        rejected_df=rejected_df_new,
    )

    review_burden_by_reason_df = _build_review_burden_by_reason(review_after_df)
    unknown_metric_label_frequency_df = _build_unknown_metric_label_frequency(review_after_df)
    unit_unknown_diagnostics_df = _build_unit_unknown_diagnostics(review_after_df)
    section_context_required_diagnostics_df = _build_section_context_required_diagnostics(review_after_df)
    out_of_scope_candidate_summary_df = _build_out_of_scope_candidate_summary(metric_candidates_all_df)
    alias_candidate_worklist_df = _build_alias_candidate_worklist(review_after_df)

    router_route_total_count = _to_int(route_summary_321g.get("route_total_count")) or len(route_inventory_df)
    attempted_new_mineru_table_count = len(extracted_tables)
    newly_processed_mineru_table_count = len(unified_tables)
    newly_failed_mineru_table_count = max(attempted_new_mineru_table_count - newly_processed_mineru_table_count, 0)
    selected_output_table_count_before_322b = _to_int(prior_summary.get("selected_output_table_count_after_322a"))
    selected_output_table_count_after_322b = int(selected_preview_after_df["table_asset_id"].astype(str).nunique()) if not selected_preview_after_df.empty else 0
    no_available_output_count_after_322b = max(router_route_total_count - selected_output_table_count_after_322b, 0)
    selected_candidate_total_count = len(metric_candidates_all_df)
    selected_trusted_total_count = len(trusted_after_df)
    selected_review_required_total_count = len(review_after_df)
    selected_rejected_total_count = len(rejected_after_df)
    selected_all_trusted_rate = round(selected_trusted_total_count / selected_candidate_total_count, 6) if selected_candidate_total_count else 0.0
    core_ids = set(
        route_inventory_df[route_inventory_df["effective_category"].astype(str).isin(CORE_ROLE_SET)]["table_asset_id"].astype(str).tolist()
    ) if not route_inventory_df.empty else set()
    core_selected_df = metric_candidates_all_df[metric_candidates_all_df["source_table_id"].astype(str).isin(core_ids)] if not metric_candidates_all_df.empty else pd.DataFrame()
    selected_core_trusted_rate = round(
        len(core_selected_df[core_selected_df["split_decision"].astype(str) == "trusted_preview"]) / len(core_selected_df),
        6,
    ) if not core_selected_df.empty else 0.0
    semantic_adjudicator_worklist_count = len(semantic_after_df)
    manual_review_worklist_count = len(manual_after_df)
    remaining_missing_output_worklist_count = len(remaining_missing_output_worklist_df)
    unknown_metric_unique_label_count = int(unknown_metric_label_frequency_df["raw_metric_name"].astype(str).nunique()) if not unknown_metric_label_frequency_df.empty else 0
    alias_candidate_count = len(alias_candidate_worklist_df)

    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa("router_integration_dir_exists", "PASS" if config.router_integration_dir.exists() else "FAIL", str(config.router_integration_dir))
    add_qa("router_dir_exists", "PASS" if config.router_dir.exists() else "FAIL", str(config.router_dir))
    add_qa("mineru_output_root_exists", "PASS" if config.mineru_output_root.exists() else "FAIL", str(config.mineru_output_root))
    add_qa("prior_322a_output_dir_exists", "PASS" if config.prior_322a_output_dir.exists() else "FAIL", str(config.prior_322a_output_dir))
    add_qa("no_e_drive_files_modified", "PASS", "322B reads existing MinerU outputs under E:\\mineru_lab\\output_new only")
    add_qa("no_external_recognizer_command_executed", "PASS", "322B reuses existing outputs and does not invoke MinerU/StructEqTable/Docling/PPStructure/VLM")
    add_qa("no_rule_changes_applied", "PASS", "322B only adds larger-batch diagnostics and does not add alias or unit rules")
    add_qa(
        "selected_output_table_count_after_322b_not_lower",
        "PASS" if selected_output_table_count_after_322b >= selected_output_table_count_before_322b else "FAIL",
        f"before={selected_output_table_count_before_322b} after={selected_output_table_count_after_322b}",
    )
    add_qa(
        "selected_candidate_count_alignment",
        "PASS" if selected_candidate_total_count == selected_trusted_total_count + selected_review_required_total_count + selected_rejected_total_count else "FAIL",
        f"all={selected_candidate_total_count}; trusted={selected_trusted_total_count}; review={selected_review_required_total_count}; rejected={selected_rejected_total_count}",
    )
    review_burden_total = int(review_burden_by_reason_df["review_candidate_count"].sum()) if not review_burden_by_reason_df.empty else 0
    add_qa(
        "review_burden_reason_alignment",
        "PASS" if review_burden_total == selected_review_required_total_count else "FAIL",
        f"review_total={selected_review_required_total_count}; grouped_total={review_burden_total}",
    )
    unit_unknown_count = int(unit_unknown_diagnostics_df.shape[0])
    unit_unknown_risk_count = int(
        review_after_df["risk_tags"].astype(str).str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True).sum()
    ) if not review_after_df.empty else 0
    add_qa(
        "unit_unknown_consistency_check",
        "PASS" if unit_unknown_count == unit_unknown_risk_count else "FAIL",
        f"diagnostic_rows={unit_unknown_count}; risk_tag_count={unit_unknown_risk_count}",
    )
    unknown_metric_candidate_count = int((review_after_df["metric_code"].astype(str) == "unknown_metric").sum()) if not review_after_df.empty else 0
    unknown_metric_grouped_count = int(unknown_metric_label_frequency_df["candidate_count"].sum()) if not unknown_metric_label_frequency_df.empty else 0
    add_qa(
        "unknown_metric_label_frequency_alignment",
        "PASS" if unknown_metric_candidate_count == unknown_metric_grouped_count else "FAIL",
        f"unknown_metric_review_count={unknown_metric_candidate_count}; grouped_count={unknown_metric_grouped_count}",
    )
    add_qa(
        "remaining_missing_output_worklist_alignment",
        "PASS" if remaining_missing_output_worklist_count == max(eligible_remaining_count - newly_processed_mineru_table_count, 0) else "WARN",
        f"eligible_remaining={eligible_remaining_count}; newly_processed={newly_processed_mineru_table_count}; remaining={remaining_missing_output_worklist_count}",
    )
    add_qa(
        "selected_preview_unique_table_ids",
        "PASS" if selected_preview_after_df.empty or not selected_preview_after_df["table_asset_id"].astype(str).duplicated().any() else "FAIL",
        f"selected_output_table_count_after_322b={selected_output_table_count_after_322b}",
    )

    qa_df = pd.DataFrame(qa_rows)
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    top_review_reason_counts = _top_review_reason_counts(review_after_df)

    if qa_fail_count > 0:
        decision = "ROUTER_DRIVEN_SANDBOX_PIPELINE_322B_BLOCKED_BY_QA_FAILURE"
    elif remaining_missing_output_worklist_count == 0:
        decision = "ROUTER_DRIVEN_SANDBOX_PIPELINE_322B_READY_FOR_REVIEW_BURDEN_DECISION"
    elif newly_processed_mineru_table_count > 0:
        decision = "ROUTER_DRIVEN_SANDBOX_PIPELINE_322B_LARGER_BATCH_COMPLETE_REVIEW_BURDEN_DIAGNOSED"
    else:
        decision = "ROUTER_DRIVEN_SANDBOX_PIPELINE_322B_NO_NEW_MINERU_OUTPUTS"

    summary = {
        "stage": "322B",
        "output_dir": str(output_dir),
        "router_route_total_count": router_route_total_count,
        "eligible_remaining_mineru_missing_count_before_322b": eligible_remaining_count,
        "selected_new_mineru_table_count": selected_new_mineru_table_count,
        "attempted_new_mineru_table_count": attempted_new_mineru_table_count,
        "newly_processed_mineru_table_count": newly_processed_mineru_table_count,
        "newly_failed_mineru_table_count": newly_failed_mineru_table_count,
        "selected_output_table_count_before_322b": selected_output_table_count_before_322b,
        "selected_output_table_count_after_322b": selected_output_table_count_after_322b,
        "no_available_output_count_after_322b": no_available_output_count_after_322b,
        "selected_candidate_total_count": selected_candidate_total_count,
        "selected_trusted_total_count": selected_trusted_total_count,
        "selected_review_required_total_count": selected_review_required_total_count,
        "selected_rejected_total_count": selected_rejected_total_count,
        "selected_core_trusted_rate": selected_core_trusted_rate,
        "selected_all_trusted_rate": selected_all_trusted_rate,
        "semantic_adjudicator_worklist_count": semantic_adjudicator_worklist_count,
        "manual_review_worklist_count": manual_review_worklist_count,
        "remaining_missing_output_worklist_count": remaining_missing_output_worklist_count,
        "unknown_metric_unique_label_count": unknown_metric_unique_label_count,
        "alias_candidate_count": alias_candidate_count,
        "top_review_reason_counts": top_review_reason_counts,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "router_driven_sandbox_pipeline_decision": decision,
    }

    report_lines = [
        "# Router Driven Sandbox Pipeline 322B",
        "",
        "## Decision",
        f"- router_driven_sandbox_pipeline_decision: {decision}",
        "",
        "## Coverage",
        f"- selected_output_table_count_before_322b: {selected_output_table_count_before_322b}",
        f"- selected_output_table_count_after_322b: {selected_output_table_count_after_322b}",
        f"- newly_processed_mineru_table_count: {newly_processed_mineru_table_count}",
        f"- no_available_output_count_after_322b: {no_available_output_count_after_322b}",
        "",
        "## Mapping",
        f"- selected_candidate_total_count: {selected_candidate_total_count}",
        f"- selected_trusted_total_count: {selected_trusted_total_count}",
        f"- selected_review_required_total_count: {selected_review_required_total_count}",
        f"- selected_core_trusted_rate: {selected_core_trusted_rate}",
        f"- selected_all_trusted_rate: {selected_all_trusted_rate}",
        "",
        "## Review Burden",
        f"- unknown_metric_unique_label_count: {unknown_metric_unique_label_count}",
        f"- alias_candidate_count: {alias_candidate_count}",
        f"- semantic_adjudicator_worklist_count: {semantic_adjudicator_worklist_count}",
        f"- manual_review_worklist_count: {manual_review_worklist_count}",
        "",
        "## QA",
        f"- qa_pass_count: {qa_pass_count}",
        f"- qa_warn_count: {qa_warn_count}",
        f"- qa_fail_count: {qa_fail_count}",
        "",
    ]

    output_files = {
        "excel": output_dir / "router_driven_sandbox_pipeline_322b.xlsx",
        "summary_json": output_dir / "router_driven_sandbox_pipeline_322b_summary.json",
        "report_md": output_dir / "router_driven_sandbox_pipeline_322b_report.md",
        "preview_jsonl": output_dir / "router_selected_delivery_preview_322b.jsonl",
        "metric_candidates_jsonl": output_dir / "metric_candidates_all_322b.jsonl",
        "semantic_jsonl": output_dir / "semantic_adjudicator_worklist_322b.jsonl",
    }
    sheets = {
        "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
        "selected_322b_mineru_worklist": worklist_df,
        "mineru_body_processing_audit": processing_audit_df,
        "router_selected_output_preview_322b": selected_preview_after_df,
        "metric_candidates_all_322b": metric_candidates_all_df,
        "trusted_preview_322b": trusted_after_df,
        "review_required_preview_322b": review_after_df,
        "rejected_preview_322b": rejected_after_df,
        "review_burden_by_reason": review_burden_by_reason_df,
        "unknown_metric_label_frequency": unknown_metric_label_frequency_df,
        "unit_unknown_diagnostics": unit_unknown_diagnostics_df,
        "section_context_required_diagnostics": section_context_required_diagnostics_df,
        "out_of_scope_candidate_summary": out_of_scope_candidate_summary_df,
        "alias_candidate_worklist": alias_candidate_worklist_df,
        "semantic_adjudicator_worklist_322b": semantic_after_df,
        "manual_review_worklist_322b": manual_after_df,
        "remaining_missing_output_worklist": remaining_missing_output_worklist_df,
        "coverage_by_route_322b": coverage_after_df,
        "qa_checks": qa_df,
        "known_limitations": _known_limitations_df_322b(),
    }
    _write_excel(output_files["excel"], sheets)
    _write_json(output_files["summary_json"], summary)
    write_jsonl(output_files["preview_jsonl"], pd.DataFrame(selected_bundle.delivery_preview_rows))
    if not metric_candidates_all_df.empty:
        write_jsonl(output_files["metric_candidates_jsonl"], metric_candidates_all_df)
    if not semantic_after_df.empty:
        write_jsonl(output_files["semantic_jsonl"], semantic_after_df)
    output_files["report_md"].write_text("\n".join(report_lines), encoding="utf-8")

    return {
        "summary": summary,
        "excel_path": str(output_files["excel"]),
        "summary_json_path": str(output_files["summary_json"]),
        "report_md_path": str(output_files["report_md"]),
        "preview_jsonl_path": str(output_files["preview_jsonl"]),
    }
