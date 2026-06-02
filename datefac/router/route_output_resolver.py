from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from datefac.router.recognizer_router_321f import (
    DOCLING_TABLE_GRID_321E2,
    MINERU_TABLE_BODY_321D,
    PPSTRUCTURE_320G,
    STRUCTTABLE_INTERVL2,
)


PURE_VLM_321B2_CALIBRATED = "PURE_VLM_321B2_CALIBRATED"


@dataclass
class OutputTableSummary:
    recognizer: str
    match_mode: str
    match_key: str
    source_doc_name: str
    source_report_name: str
    source_table_id: str
    table_title: str
    candidate_count: int
    trusted_count: int
    review_required_count: int
    rejected_count: int
    all_candidate_trusted_rate: float
    core_candidate_trusted_rate: float
    risk_tags: str
    provenance_status: str
    provenance_complete_rate: float
    notes: str


@dataclass
class OutputResolverBundle:
    mineru_by_asset: Dict[str, OutputTableSummary]
    structtable_by_image: Dict[str, OutputTableSummary]
    docling_by_image: Dict[str, OutputTableSummary]
    pure_vlm_by_image: Dict[str, OutputTableSummary]
    ppstructure_by_asset: Dict[str, OutputTableSummary]
    workbook_paths: Dict[str, str]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


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


def _pick_first(row: Dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = _norm(row.get(key))
        if value:
            return value
    return ""


def _image_stem_from_row(row: Dict[str, Any]) -> str:
    for key in ("source_file", "source_doc_name", "image_path", "image_filename"):
        value = _norm(row.get(key))
        if value:
            return Path(value).stem
    return ""


def _aggregate_preview_counts(
    trusted_df: pd.DataFrame,
    review_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
    key_getter,
) -> Dict[str, Dict[str, Any]]:
    aggregate: Dict[str, Dict[str, Any]] = {}

    def ensure(match_key: str) -> Dict[str, Any]:
        item = aggregate.get(match_key)
        if item is None:
            item = {
                "candidate_count": 0,
                "trusted_count": 0,
                "review_required_count": 0,
                "rejected_count": 0,
                "risk_tags": set(),
                "provenance_nonempty_count": 0,
                "row_count": 0,
                "table_titles": [],
                "source_doc_names": [],
                "source_table_ids": [],
            }
            aggregate[match_key] = item
        return item

    def feed(df: pd.DataFrame, counter_key: str) -> None:
        if df.empty:
            return
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            match_key = _norm(key_getter(row_dict))
            if not match_key:
                continue
            item = ensure(match_key)
            item["candidate_count"] += 1
            item[counter_key] += 1
            item["row_count"] += 1
            risk_text = _pick_first(row_dict, ("risk_tags",))
            if risk_text:
                for tag in risk_text.split("|"):
                    tag = tag.strip()
                    if tag:
                        item["risk_tags"].add(tag)
            if _pick_first(row_dict, ("provenance_json",)):
                item["provenance_nonempty_count"] += 1
            table_title = _pick_first(row_dict, ("table_title",))
            if table_title:
                item["table_titles"].append(table_title)
            source_doc_name = _pick_first(row_dict, ("source_doc_name", "source_doc", "report"))
            if source_doc_name:
                item["source_doc_names"].append(source_doc_name)
            source_table_id = _pick_first(row_dict, ("source_table_id", "table_asset_id", "table_id"))
            if source_table_id:
                item["source_table_ids"].append(source_table_id)

    feed(trusted_df, "trusted_count")
    feed(review_df, "review_required_count")
    feed(rejected_df, "rejected_count")
    return aggregate


def _most_common(values: List[str]) -> str:
    cleaned = [value for value in values if _norm(value)]
    if not cleaned:
        return ""
    return pd.Series(cleaned).value_counts().idxmax()


def _finalize_record(
    recognizer: str,
    match_mode: str,
    match_key: str,
    preview_stats: Dict[str, Any],
    summary_row: Optional[Dict[str, Any]] = None,
    notes: str = "",
) -> OutputTableSummary:
    summary_row = summary_row or {}
    candidate_count = _to_int(summary_row.get("candidate_count"))
    trusted_count = _to_int(summary_row.get("trusted_count"))
    review_required_count = _to_int(summary_row.get("review_required_count"))
    rejected_count = _to_int(summary_row.get("rejected_count"))
    if candidate_count <= 0:
        candidate_count = _to_int(preview_stats.get("candidate_count"))
    if trusted_count <= 0:
        trusted_count = _to_int(preview_stats.get("trusted_count"))
    if review_required_count <= 0:
        review_required_count = _to_int(preview_stats.get("review_required_count"))
    if rejected_count <= 0:
        rejected_count = _to_int(preview_stats.get("rejected_count"))
    if candidate_count <= 0:
        candidate_count = trusted_count + review_required_count + rejected_count

    provenance_nonempty = _to_int(preview_stats.get("provenance_nonempty_count"))
    row_count = max(_to_int(preview_stats.get("row_count")), candidate_count)
    provenance_complete_rate = 0.0 if row_count <= 0 else round(provenance_nonempty / row_count, 6)
    provenance_status = "COMPLETE" if row_count > 0 and provenance_nonempty == row_count else "PARTIAL_OR_MISSING"
    all_candidate_trusted_rate = 0.0 if candidate_count <= 0 else round(trusted_count / candidate_count, 6)

    table_title = _pick_first(summary_row, ("table_title", "table_name"))
    if not table_title:
        table_title = _most_common(list(preview_stats.get("table_titles", [])))
    source_doc_name = _pick_first(summary_row, ("source_report_name", "report", "source_doc_name"))
    if not source_doc_name:
        source_doc_name = _most_common(list(preview_stats.get("source_doc_names", [])))
    source_table_id = _pick_first(summary_row, ("table_asset_id", "table_id", "table_run_id", "source_table_id"))
    if not source_table_id:
        source_table_id = _most_common(list(preview_stats.get("source_table_ids", [])))
    return OutputTableSummary(
        recognizer=recognizer,
        match_mode=match_mode,
        match_key=match_key,
        source_doc_name=source_doc_name,
        source_report_name=source_doc_name,
        source_table_id=source_table_id,
        table_title=table_title,
        candidate_count=candidate_count,
        trusted_count=trusted_count,
        review_required_count=review_required_count,
        rejected_count=rejected_count,
        all_candidate_trusted_rate=all_candidate_trusted_rate,
        core_candidate_trusted_rate=all_candidate_trusted_rate,
        risk_tags="|".join(sorted(preview_stats.get("risk_tags", set()))),
        provenance_status=provenance_status,
        provenance_complete_rate=provenance_complete_rate,
        notes=notes,
    )


def _load_exact_asset_workbook(
    workbook: Optional[Path],
    recognizer: str,
    summary_sheet: str,
    trusted_sheet: str,
    review_sheet: str,
    rejected_sheet: str,
    notes: str,
) -> Dict[str, OutputTableSummary]:
    summary_df = _read_sheet(workbook, summary_sheet)
    trusted_df = _read_sheet(workbook, trusted_sheet)
    review_df = _read_sheet(workbook, review_sheet)
    rejected_df = _read_sheet(workbook, rejected_sheet)
    preview_stats = _aggregate_preview_counts(
        trusted_df,
        review_df,
        rejected_df,
        lambda row: _pick_first(row, ("table_asset_id", "source_table_id", "table_id")),
    )
    results: Dict[str, OutputTableSummary] = {}
    if not summary_df.empty:
        for _, row in summary_df.iterrows():
            row_dict = row.to_dict()
            match_key = _pick_first(row_dict, ("table_asset_id", "table_id"))
            if not match_key:
                continue
            results[match_key] = _finalize_record(
                recognizer=recognizer,
                match_mode="table_asset_id",
                match_key=match_key,
                preview_stats=preview_stats.get(match_key, {}),
                summary_row=row_dict,
                notes=notes,
            )
    for match_key, stats in preview_stats.items():
        if match_key in results:
            continue
        results[match_key] = _finalize_record(
            recognizer=recognizer,
            match_mode="table_asset_id",
            match_key=match_key,
            preview_stats=stats,
            summary_row=None,
            notes=notes,
        )
    return results


def _load_image_level_workbook(
    workbook: Optional[Path],
    recognizer: str,
    trusted_sheet: str,
    review_sheet: str,
    rejected_sheet: str,
    notes: str,
) -> Dict[str, OutputTableSummary]:
    trusted_df = _read_sheet(workbook, trusted_sheet)
    review_df = _read_sheet(workbook, review_sheet)
    rejected_df = _read_sheet(workbook, rejected_sheet)
    preview_stats = _aggregate_preview_counts(
        trusted_df,
        review_df,
        rejected_df,
        _image_stem_from_row,
    )
    results: Dict[str, OutputTableSummary] = {}
    for match_key, stats in preview_stats.items():
        results[match_key] = _finalize_record(
            recognizer=recognizer,
            match_mode="image_stem",
            match_key=match_key,
            preview_stats=stats,
            summary_row=None,
            notes=notes,
        )
    return results


def load_output_resolver_bundle(
    mineru_body_dir: Path,
    structtable_mapping_dir: Path,
    docling_mapping_dir: Path,
    pure_vlm_calibration_dir: Path,
    ppstructure_benchmark_dir: Path,
) -> OutputResolverBundle:
    mineru_workbook = _find_workbook(mineru_body_dir)
    structtable_workbook = _find_workbook(structtable_mapping_dir)
    docling_workbook = _find_workbook(docling_mapping_dir)
    pure_vlm_workbook = _find_workbook(pure_vlm_calibration_dir)
    ppstructure_workbook = _find_workbook(ppstructure_benchmark_dir)

    return OutputResolverBundle(
        mineru_by_asset=_load_exact_asset_workbook(
            workbook=mineru_workbook,
            recognizer=MINERU_TABLE_BODY_321D,
            summary_sheet="per_table_summary",
            trusted_sheet="trusted_preview",
            review_sheet="review_required_preview",
            rejected_sheet="rejected_preview",
            notes="exact table_asset_id match from 321D per_table_summary",
        ),
        structtable_by_image=_load_image_level_workbook(
            workbook=structtable_workbook,
            recognizer=STRUCTTABLE_INTERVL2,
            trusted_sheet="structtable_trusted_preview",
            review_sheet="structtable_review_required_pre",
            rejected_sheet="structtable_rejected_preview",
            notes="image-level benchmark match from 321E4B preview sheets",
        ),
        docling_by_image=_load_image_level_workbook(
            workbook=docling_workbook,
            recognizer=DOCLING_TABLE_GRID_321E2,
            trusted_sheet="docling_trusted_preview",
            review_sheet="docling_review_required_preview",
            rejected_sheet="docling_rejected_preview",
            notes="image-level benchmark match from 321E2 preview sheets",
        ),
        pure_vlm_by_image=_load_image_level_workbook(
            workbook=pure_vlm_workbook,
            recognizer=PURE_VLM_321B2_CALIBRATED,
            trusted_sheet="trusted_preview",
            review_sheet="review_required_preview",
            rejected_sheet="rejected_preview",
            notes="image-level benchmark match from 321B2 preview sheets",
        ),
        ppstructure_by_asset=_load_exact_asset_workbook(
            workbook=ppstructure_workbook,
            recognizer=PPSTRUCTURE_320G,
            summary_sheet="per_table_summary",
            trusted_sheet="trusted_preview_all",
            review_sheet="review_required_preview_all",
            rejected_sheet="rejected_preview_all",
            notes="exact table_asset_id match from 320G batch summary",
        ),
        workbook_paths={
            "mineru": str(mineru_workbook) if mineru_workbook else "",
            "structtable": str(structtable_workbook) if structtable_workbook else "",
            "docling": str(docling_workbook) if docling_workbook else "",
            "pure_vlm": str(pure_vlm_workbook) if pure_vlm_workbook else "",
            "ppstructure": str(ppstructure_workbook) if ppstructure_workbook else "",
        },
    )
