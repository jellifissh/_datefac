from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .router_policy import decide_route


def _norm(value: Any) -> str:
    if value is None:
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
        return int(float(str(value).strip()))
    except Exception:
        return 0


def _normalize_path(value: Any) -> str:
    p = _norm(value).replace("/", "\\")
    return p.lower()


def _safe_read_excel(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()


def _safe_read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _stable_asset_id(report_name: str, source_file: str, block_index: Any, bbox: Any) -> str:
    seed = f"{_norm(report_name)}|{_norm(source_file)}|{_norm(block_index)}|{_norm(bbox)}"
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def _parse_extra_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    s = _norm(value)
    if not s:
        return {}
    try:
        parsed = ast.literal_eval(s)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _short_text(value: Any, max_len: int = 200) -> str:
    text = _norm(value)
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _load_mineru_assets(mineru_benchmark_dir: Optional[Path], mineru_output_root: Path) -> Tuple[pd.DataFrame, List[str]]:
    warnings: List[str] = []
    if not mineru_benchmark_dir:
        warnings.append("MISSING_MINERU_BENCHMARK_DIR")
        return pd.DataFrame(), warnings
    xlsx = mineru_benchmark_dir / "mineru_benchmark_320b2.xlsx"
    df = _safe_read_excel(xlsx, "table_assets_all")
    if df.empty:
        warnings.append("MISSING_MINERU_TABLE_ASSETS_ALL")
        return pd.DataFrame(), warnings

    out = df.copy()
    out["report_name"] = out.get("report_name", "").fillna("").astype(str)
    out["image_path"] = out.get("image_path", "").fillna("").astype(str)
    out["image_path_norm"] = out["image_path"].apply(_normalize_path)
    out["image_exists"] = out.get("image_exists", False).apply(_to_bool)
    out["table_asset_id"] = out.apply(
        lambda r: _stable_asset_id(
            report_name=_norm(r.get("report_name")),
            source_file=_norm(r.get("source_file")),
            block_index=r.get("block_index"),
            bbox=r.get("bbox"),
        ),
        axis=1,
    )
    out["report_dir"] = out["report_name"].apply(lambda x: str((mineru_output_root / _norm(x)).resolve()))
    out["nearby_text_preview"] = out.get("nearby_text", "").apply(_short_text)
    out["caption"] = out.get("caption", "").fillna("").astype(str)
    out["bbox"] = out.get("bbox", "").astype(str)
    out["page_idx"] = out.get("page_idx")
    out["extra_dict"] = out.get("extra", "").apply(_parse_extra_dict)
    out["role_category"] = out.get("role_category", "").fillna("").astype(str)
    out["table_role_guess"] = out.get("table_role_guess", "").fillna("").astype(str)
    return out, warnings


def _load_vlm_tables(vlm_benchmark_dir: Optional[Path], vlm_output_root: Optional[Path]) -> Tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    warnings: List[str] = []
    if not vlm_benchmark_dir:
        warnings.append("MISSING_VLM_BENCHMARK_DIR")
        return pd.DataFrame(), {}, warnings
    summary = _safe_read_json(vlm_benchmark_dir / "vlm_mapping_benchmark_321b_summary.json")
    xlsx = vlm_benchmark_dir / "vlm_mapping_benchmark_321b.xlsx"
    inventory = _safe_read_excel(xlsx, "vlm_table_inventory")
    per_table = _safe_read_excel(xlsx, "per_table_summary")
    if inventory.empty:
        warnings.append("MISSING_VLM_TABLE_INVENTORY")
        return pd.DataFrame(), summary, warnings

    out = inventory.copy()
    out["source_image_path"] = out.get("source_image_path", "").fillna("").astype(str)
    out["image_path_norm"] = out["source_image_path"].apply(_normalize_path)
    out["table_folder"] = out.get("table_folder", "").fillna("").astype(str)
    out["folder_path"] = out.get("folder_path", "").fillna("").astype(str)
    if vlm_output_root:
        out["folder_expected_under_root"] = out["table_folder"].apply(lambda x: str((vlm_output_root / _norm(x)).resolve()))
    else:
        out["folder_expected_under_root"] = ""
    out["vlm_output_available"] = out["table_folder"].apply(
        lambda x: bool(vlm_output_root and (vlm_output_root / _norm(x) / "vlm_output.json").exists())
    )

    per_table_cols = {
        "quality_decision": "vlm_quality_decision",
        "quality_main_issue": "vlm_main_issue",
        "candidate_count": "vlm_candidate_count",
        "trusted_count": "vlm_trusted_count",
        "review_required_count": "vlm_review_required_count",
        "rejected_count": "vlm_rejected_count",
        "qa_status": "vlm_qa_status",
        "table_decision": "vlm_table_decision",
        "unique_metric_count": "vlm_unique_metric_count",
        "unique_year_count": "vlm_unique_year_count",
    }
    if not per_table.empty:
        meta = per_table.rename(columns=per_table_cols)
        out = out.merge(meta[["table_folder"] + list(per_table_cols.values())], on="table_folder", how="left")
    else:
        for col in per_table_cols.values():
            out[col] = None

    out["vlm_current_decision"] = out.get("current_decision")
    out["vlm_issue_tags"] = out.get("issue_tags")
    out["vlm_table_warnings"] = out.get("table_warnings")
    out["vlm_unit_unknown_count"] = out.get("unit").isna().astype(int) if "unit" in out.columns else 0
    out["vlm_conflict_count"] = 0
    return out, summary, warnings


def _load_ppstructure_tables(ppstructure_benchmark_dir: Optional[Path]) -> Tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    warnings: List[str] = []
    if not ppstructure_benchmark_dir:
        warnings.append("MISSING_PPSTRUCTURE_BENCHMARK_DIR")
        return pd.DataFrame(), {}, warnings
    summary = {}
    summary_df = _safe_read_excel(ppstructure_benchmark_dir / "batch_row_text_delivery_320g.xlsx", "summary")
    if not summary_df.empty and {"metric", "value"}.issubset(summary_df.columns):
        summary = {str(r["metric"]): r["value"] for _, r in summary_df.iterrows()}

    inventory = _safe_read_excel(ppstructure_benchmark_dir / "batch_row_text_delivery_320g.xlsx", "table_run_inventory")
    per_table = _safe_read_excel(ppstructure_benchmark_dir / "batch_row_text_delivery_320g.xlsx", "per_table_summary")
    if inventory.empty:
        warnings.append("MISSING_PPSTRUCTURE_TABLE_RUN_INVENTORY")
        return pd.DataFrame(), summary, warnings

    out = inventory.copy()
    out["image_path"] = out.get("image_path", "").fillna("").astype(str)
    out["image_path_norm"] = out["image_path"].apply(_normalize_path)
    out["report"] = out.get("report", "").fillna("").astype(str)
    out["table_asset_id"] = out.get("table_asset_id", "").fillna("").astype(str)
    out["ppstructure_output_available"] = out.get("ppstructure_output_dir", "").fillna("").astype(str).str.len() > 0
    if not per_table.empty:
        merged = per_table.rename(
            columns={
                "metric_candidate_count": "ppstructure_candidate_count",
                "trusted_count": "ppstructure_trusted_count",
                "review_required_count": "ppstructure_review_required_count",
                "rejected_count": "ppstructure_rejected_count",
                "qa_status": "ppstructure_qa_status",
                "table_decision": "ppstructure_table_decision",
                "conflict_count": "ppstructure_conflict_count",
            }
        )
        keep_cols = [
            "table_run_id",
            "report",
            "table_asset_id",
            "table_type",
            "ppstructure_candidate_count",
            "ppstructure_trusted_count",
            "ppstructure_review_required_count",
            "ppstructure_rejected_count",
            "ppstructure_qa_status",
            "ppstructure_table_decision",
            "ppstructure_conflict_count",
        ]
        out = out.merge(merged[keep_cols], on=["table_run_id", "report", "table_asset_id", "table_type"], how="left")
    else:
        for col in [
            "ppstructure_candidate_count",
            "ppstructure_trusted_count",
            "ppstructure_review_required_count",
            "ppstructure_rejected_count",
            "ppstructure_qa_status",
            "ppstructure_table_decision",
            "ppstructure_conflict_count",
        ]:
            out[col] = 0
    return out, summary, warnings


def build_table_router_preview(
    *,
    vlm_benchmark_dir: Optional[Path],
    vlm_quality_dir: Optional[Path],
    ppstructure_benchmark_dir: Optional[Path],
    mineru_benchmark_dir: Optional[Path],
    mineru_output_root: Path,
    vlm_output_root: Optional[Path],
) -> Dict[str, Any]:
    mineru_df, mineru_warnings = _load_mineru_assets(mineru_benchmark_dir, mineru_output_root)
    vlm_df, vlm_summary, vlm_warnings = _load_vlm_tables(vlm_benchmark_dir, vlm_output_root)
    pp_df, pp_summary, pp_warnings = _load_ppstructure_tables(ppstructure_benchmark_dir)
    warnings: List[str] = []
    warnings.extend(mineru_warnings)
    warnings.extend(vlm_warnings)
    warnings.extend(pp_warnings)

    if vlm_quality_dir and not vlm_quality_dir.exists():
        warnings.append("MISSING_VLM_QUALITY_DIR")
    if vlm_output_root and not vlm_output_root.exists():
        warnings.append("MISSING_VLM_OUTPUT_ROOT")

    if mineru_df.empty:
        return {
            "router_preview_df": pd.DataFrame(),
            "warnings": warnings + ["NO_MINERU_ASSETS_FOR_ROUTER"],
            "vlm_summary": vlm_summary,
            "ppstructure_summary": pp_summary,
        }

    preview = mineru_df.copy()
    preview = preview.rename(columns={"report_name": "source_report_name"})
    preview["mineru_asset_available"] = True

    if not vlm_df.empty:
        vlm_merge_cols = [
            "image_path_norm",
            "table_folder",
            "table_title",
            "unit",
            "currency",
            "schema_shape",
            "row_count",
            "column_count",
            "numeric_parse_success_rate",
            "numeric_completeness_rate",
            "corrupted_label_row_count",
            "corrupted_label_rate",
            "vlm_output_available",
            "vlm_quality_decision",
            "vlm_main_issue",
            "vlm_candidate_count",
            "vlm_trusted_count",
            "vlm_review_required_count",
            "vlm_rejected_count",
            "vlm_qa_status",
            "vlm_table_decision",
            "vlm_unique_metric_count",
            "vlm_unique_year_count",
            "vlm_current_decision",
            "vlm_issue_tags",
            "vlm_table_warnings",
            "folder_path",
            "source_json_path",
        ]
        preview = preview.merge(vlm_df[vlm_merge_cols], on="image_path_norm", how="left")
    else:
        for col in [
            "table_folder",
            "table_title",
            "unit",
            "currency",
            "schema_shape",
            "row_count",
            "column_count",
            "numeric_parse_success_rate",
            "numeric_completeness_rate",
            "corrupted_label_row_count",
            "corrupted_label_rate",
            "vlm_output_available",
            "vlm_quality_decision",
            "vlm_main_issue",
            "vlm_candidate_count",
            "vlm_trusted_count",
            "vlm_review_required_count",
            "vlm_rejected_count",
            "vlm_qa_status",
            "vlm_table_decision",
            "vlm_unique_metric_count",
            "vlm_unique_year_count",
            "vlm_current_decision",
            "vlm_issue_tags",
            "vlm_table_warnings",
            "folder_path",
            "source_json_path",
        ]:
            preview[col] = None

    if not pp_df.empty:
        pp_merge_cols = [
            "image_path_norm",
            "report",
            "table_asset_id",
            "table_type",
            "ppstructure_output_dir",
            "ppstructure_output_available",
            "parse_status",
            "metric_candidate_count",
            "normalized_candidate_count",
            "trusted_count",
            "review_required_count",
            "rejected_count",
            "warnings",
            "ppstructure_candidate_count",
            "ppstructure_trusted_count",
            "ppstructure_review_required_count",
            "ppstructure_rejected_count",
            "ppstructure_qa_status",
            "ppstructure_table_decision",
            "ppstructure_conflict_count",
        ]
        pp_join = pp_df[pp_merge_cols].rename(
            columns={
                "warnings": "ppstructure_warnings",
                "metric_candidate_count": "ppstructure_metric_candidate_count_inventory",
                "normalized_candidate_count": "ppstructure_normalized_candidate_count",
                "trusted_count": "ppstructure_trusted_count_inventory",
                "review_required_count": "ppstructure_review_required_count_inventory",
                "rejected_count": "ppstructure_rejected_count_inventory",
            }
        )
        pp_join = pp_join.sort_values(["report", "image_path_norm", "table_asset_id"]).drop_duplicates(
            subset=["report", "image_path_norm"],
            keep="first",
        )
        preview = preview.merge(
            pp_join,
            left_on=["image_path_norm", "source_report_name"],
            right_on=["image_path_norm", "report"],
            how="left",
            suffixes=("", "_pp"),
        )
        if "table_asset_id_pp" in preview.columns:
            preview["ppstructure_table_asset_id"] = preview["table_asset_id_pp"]
            preview = preview.drop(columns=["table_asset_id_pp"])
        if "ppstructure_output_available" not in preview.columns:
            preview["ppstructure_output_available"] = False
        preview["ppstructure_output_available"] = preview["ppstructure_output_available"].apply(_to_bool)
    else:
        for col in [
            "report",
            "table_type",
            "ppstructure_output_dir",
            "ppstructure_output_available",
            "parse_status",
            "ppstructure_metric_candidate_count_inventory",
            "ppstructure_normalized_candidate_count",
            "ppstructure_trusted_count_inventory",
            "ppstructure_review_required_count_inventory",
            "ppstructure_rejected_count_inventory",
            "ppstructure_warnings",
            "ppstructure_candidate_count",
            "ppstructure_trusted_count",
            "ppstructure_review_required_count",
            "ppstructure_rejected_count",
            "ppstructure_qa_status",
            "ppstructure_table_decision",
            "ppstructure_conflict_count",
        ]:
            preview[col] = None

    for numeric_col in [
        "vlm_candidate_count",
        "vlm_trusted_count",
        "vlm_review_required_count",
        "vlm_rejected_count",
        "vlm_unique_metric_count",
        "vlm_unique_year_count",
        "ppstructure_candidate_count",
        "ppstructure_trusted_count",
        "ppstructure_review_required_count",
        "ppstructure_rejected_count",
        "ppstructure_conflict_count",
    ]:
        if numeric_col not in preview.columns:
            preview[numeric_col] = 0
        preview[numeric_col] = preview[numeric_col].apply(_to_int)

    preview["vlm_output_available"] = preview.get("vlm_output_available", False).apply(_to_bool)
    preview["ppstructure_output_available"] = preview.get("ppstructure_output_available", False).apply(_to_bool)
    preview["vlm_quality_decision"] = preview.get("vlm_quality_decision", "").fillna("").astype(str)
    preview["vlm_main_issue"] = preview.get("vlm_main_issue", "").fillna("").astype(str)
    preview["vlm_qa_status"] = preview.get("vlm_qa_status", "").fillna("").astype(str)
    preview["table_type"] = preview.get("table_type", "").fillna("").astype(str)
    preview["table_title"] = preview.get("table_title", "").fillna("").astype(str)
    preview["source_json_path"] = preview.get("source_json_path", "").fillna("").astype(str)

    decisions = preview.apply(lambda row: decide_route(row.to_dict()).to_dict(), axis=1, result_type="expand")
    preview = pd.concat([preview, decisions], axis=1)
    preview["route_reason"] = preview["route_reason"].fillna("").astype(str)
    preview["blocker_reason"] = preview["blocker_reason"].fillna("").astype(str)
    preview["table_role_guess"] = preview.get("table_role_guess", "").fillna("").astype(str)
    preview["caption"] = preview.get("caption", "").fillna("").astype(str)
    preview["nearby_text_preview"] = preview.get("nearby_text_preview", "").fillna("").astype(str)
    preview["image_filename"] = preview["image_path"].apply(lambda p: Path(_norm(p)).name if _norm(p) else "")
    preview["vlm_quality_dir_available"] = bool(vlm_quality_dir and vlm_quality_dir.exists())

    keep_cols = [
        "source_report_name",
        "report_dir",
        "table_asset_id",
        "table_role_guess",
        "effective_role_category",
        "table_type",
        "page_idx",
        "bbox",
        "image_path",
        "image_filename",
        "image_exists",
        "caption",
        "nearby_text_preview",
        "mineru_asset_available",
        "ppstructure_output_available",
        "vlm_output_available",
        "vlm_quality_decision",
        "vlm_candidate_count",
        "vlm_trusted_count",
        "ppstructure_candidate_count",
        "ppstructure_trusted_count",
        "estimated_value_score",
        "estimated_cost_class",
        "confidence_score",
        "recommended_route",
        "route_reason",
        "blocker_reason",
        "table_title",
        "unit",
        "currency",
        "schema_shape",
        "row_count",
        "column_count",
        "vlm_main_issue",
        "vlm_qa_status",
        "vlm_table_decision",
        "vlm_current_decision",
        "vlm_issue_tags",
        "folder_path",
        "source_json_path",
        "ppstructure_output_dir",
        "ppstructure_qa_status",
        "ppstructure_table_decision",
        "ppstructure_conflict_count",
    ]
    for col in keep_cols:
        if col not in preview.columns:
            preview[col] = None

    preview = preview[keep_cols].sort_values(
        ["source_report_name", "page_idx", "estimated_value_score", "table_asset_id"],
        ascending=[True, True, False, True],
    ).reset_index(drop=True)

    return {
        "router_preview_df": preview,
        "warnings": warnings,
        "vlm_summary": vlm_summary,
        "ppstructure_summary": pp_summary,
    }
