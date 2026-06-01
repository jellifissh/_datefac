from __future__ import annotations

import hashlib
import json
from io import StringIO
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from datefac.parser.mineru_output_reader import MineruReadResult, read_mineru_output


MINERU_ROUTE = "MINERU_TABLE_BODY_STRUCTURING"
PRIORITY_ROLE_ORDER = {
    "FINANCIAL_FORECAST_VALUATION": 1,
    "BALANCE_SHEET": 2,
    "INCOME_STATEMENT": 3,
    "CASH_FLOW_STATEMENT": 4,
    "CORE_METRIC_TABLE": 5,
}


@dataclass
class ExtractedTableBody:
    selected_rank: int
    source_report_name: str
    table_asset_id: str
    image_path: str
    page_idx: Optional[int]
    bbox: str
    effective_role_category: str
    table_title_final: str
    match_status: str
    matched_by: str
    content_source_file: str
    content_item_index: Optional[int]
    has_table_body: bool
    has_html: bool
    has_markdown_table: bool
    raw_table_title: str
    raw_unit: str
    raw_table_text: str
    raw_table_html: str
    provenance: Dict[str, Any]
    warnings: List[str]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_int(value: Any) -> Optional[int]:
    text = _norm(value)
    if not text:
        return None
    try:
        return int(float(text))
    except Exception:
        return None


def _stable_asset_id(report_name: str, source_file: str, block_index: Any, bbox: Any) -> str:
    seed = f"{_norm(report_name)}|{_norm(source_file)}|{_norm(block_index)}|{_norm(bbox)}"
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name=sheet_name).fillna("")
    except Exception:
        return pd.DataFrame()


def _parse_bbox(value: Any) -> Tuple[float, float, float, float]:
    text = _norm(value)
    if not text:
        return (0.0, 0.0, 0.0, 0.0)
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list) and len(parsed) >= 4:
            return tuple(float(item) for item in parsed[:4])  # type: ignore[return-value]
    except Exception:
        pass
    cleaned = text.replace("[", "").replace("]", "").replace("(", "").replace(")", "")
    parts = [part.strip() for part in cleaned.split(",") if part.strip()]
    if len(parts) >= 4:
        try:
            return tuple(float(part) for part in parts[:4])  # type: ignore[return-value]
        except Exception:
            return (0.0, 0.0, 0.0, 0.0)
    return (0.0, 0.0, 0.0, 0.0)


def _bbox_distance(a: Any, b: Any) -> float:
    box_a = _parse_bbox(a)
    box_b = _parse_bbox(b)
    return sum(abs(x - y) for x, y in zip(box_a, box_b))


def _role_priority(role: str) -> int:
    return PRIORITY_ROLE_ORDER.get(_norm(role), 99)


def _preferable_row(row: pd.Series) -> Tuple[Any, ...]:
    return (
        _role_priority(_norm(row.get("effective_role_category"))),
        0 if _norm(row.get("table_title_final")) else 1,
        0 if "clean_mineru_table_body_available" in _norm(row.get("route_reason")) else 1,
        _norm(row.get("source_report_name")),
        _norm(row.get("table_asset_id")),
    )


def select_router_worklist(router_dir: Path, max_tables: int) -> Tuple[pd.DataFrame, List[str], Dict[str, Any]]:
    if not router_dir.exists():
        return pd.DataFrame(), ["BLOCKED_MISSING_321C2_ROUTER_DIR"], {}
    workbook = router_dir / "source_aware_router_revision_321c2.xlsx"
    if not workbook.exists():
        return pd.DataFrame(), ["BLOCKED_MISSING_321C2_ROUTER_WORKBOOK"], {}

    worklist_df = _read_sheet(workbook, "mineru_table_body_worklist")
    preview_df = _read_sheet(workbook, "table_route_preview_revised")
    policy_df = _read_sheet(workbook, "revised_router_policy")
    warnings: List[str] = []
    if worklist_df.empty:
        warnings.append("MISSING_MINERU_TABLE_BODY_WORKLIST")
    if preview_df.empty:
        warnings.append("MISSING_TABLE_ROUTE_PREVIEW_REVISED")

    source_df = worklist_df if not worklist_df.empty else preview_df
    if source_df.empty:
        return pd.DataFrame(), warnings, {"policy_df": policy_df, "preview_df": preview_df}

    if "recommended_route" in source_df.columns:
        filtered = source_df[source_df["recommended_route"].astype(str) == MINERU_ROUTE].copy()
        source_df = filtered if not filtered.empty else source_df.copy()
    else:
        source_df = source_df.copy()

    source_df = source_df.sort_values(
        by=list(source_df.apply(_preferable_row, axis=1)),
    ) if False else source_df

    source_df["role_priority"] = source_df["effective_role_category"].astype(str).apply(_role_priority)
    source_df["title_penalty"] = source_df["table_title_final"].astype(str).apply(lambda text: 0 if _norm(text) else 1)
    source_df["route_penalty"] = source_df["route_reason"].astype(str).apply(lambda text: 0 if "clean_mineru_table_body_available" in text else 1)
    source_df["report_group"] = source_df["source_report_name"].astype(str)
    source_df = source_df.sort_values(
        ["role_priority", "title_penalty", "route_penalty", "report_group", "table_asset_id"],
        ascending=[True, True, True, True, True],
    ).reset_index(drop=True)

    buckets: Dict[str, List[int]] = {}
    for idx, row in source_df.iterrows():
        buckets.setdefault(_norm(row.get("source_report_name")), []).append(idx)

    selected_indexes: List[int] = []
    while len(selected_indexes) < max_tables:
        progressed = False
        for report_name in sorted(buckets.keys()):
            if not buckets[report_name]:
                continue
            selected_indexes.append(buckets[report_name].pop(0))
            progressed = True
            if len(selected_indexes) >= max_tables:
                break
        if not progressed:
            break

    selected = source_df.iloc[selected_indexes].copy() if selected_indexes else source_df.head(max_tables).copy()
    selected = selected.reset_index(drop=True)
    selected["selected_rank"] = selected.index + 1
    return selected, warnings, {"policy_df": policy_df, "preview_df": preview_df}


def load_mineru_report(report_dir: Path) -> MineruReadResult:
    return read_mineru_output(report_dir)


def _extract_title_from_html(html: str) -> str:
    if not _norm(html):
        return ""
    try:
        tables = pd.read_html(StringIO(html))
    except Exception:
        return ""
    if not tables:
        return ""
    df = tables[0].fillna("")
    if df.empty:
        return ""
    first_row = [str(item).strip() for item in df.iloc[0].tolist() if str(item).strip()]
    if len(first_row) == 1:
        return first_row[0]
    return ""


def extract_table_bodies(selected_worklist_df: pd.DataFrame, mineru_output_root: Path) -> Tuple[List[ExtractedTableBody], pd.DataFrame]:
    extracted: List[ExtractedTableBody] = []
    audit_rows: List[Dict[str, Any]] = []
    cache: Dict[str, MineruReadResult] = {}

    for _, row in selected_worklist_df.iterrows():
        selected_rank = int(row.get("selected_rank", 0))
        report_name = _norm(row.get("source_report_name"))
        table_asset_id = _norm(row.get("table_asset_id"))
        image_path = _norm(row.get("image_path"))
        page_idx = _to_int(row.get("page_idx"))
        bbox = _norm(row.get("bbox"))
        effective_role_category = _norm(row.get("effective_role_category"))
        table_title_final = _norm(row.get("table_title_final"))
        report_dir = mineru_output_root / report_name

        warnings: List[str] = []
        if not report_dir.exists():
            warnings.append("REPORT_DIR_NOT_FOUND")
            extracted.append(
                ExtractedTableBody(
                    selected_rank=selected_rank,
                    source_report_name=report_name,
                    table_asset_id=table_asset_id,
                    image_path=image_path,
                    page_idx=page_idx,
                    bbox=bbox,
                    effective_role_category=effective_role_category,
                    table_title_final=table_title_final,
                    match_status="TABLE_BODY_NOT_FOUND",
                    matched_by="report_dir_missing",
                    content_source_file="",
                    content_item_index=None,
                    has_table_body=False,
                    has_html=False,
                    has_markdown_table=False,
                    raw_table_title="",
                    raw_unit="",
                    raw_table_text="",
                    raw_table_html="",
                    provenance={"selected_rank": selected_rank},
                    warnings=warnings,
                )
            )
            audit_rows.append(
                {
                    "selected_rank": selected_rank,
                    "source_report_name": report_name,
                    "table_asset_id": table_asset_id,
                    "image_path": image_path,
                    "match_status": "TABLE_BODY_NOT_FOUND",
                    "matched_by": "report_dir_missing",
                    "content_source_file": "",
                    "content_item_index": "",
                    "has_table_body": False,
                    "has_html": False,
                    "has_markdown_table": False,
                    "extracted_row_count": 0,
                    "extracted_column_count": 0,
                    "warnings": "|".join(warnings),
                }
            )
            continue

        if report_name not in cache:
            cache[report_name] = load_mineru_report(report_dir)
        result = cache[report_name]

        matched_asset = None
        matched_by = ""
        best_distance = 1e18
        expected_image_name = Path(image_path).name if image_path else ""
        for asset in result.table_assets:
            asset_report_name = report_name
            computed_id = _stable_asset_id(asset_report_name, _norm(asset.source_file), asset.block_index, asset.bbox)
            asset_image_name = Path(_norm(asset.image_path)).name if _norm(asset.image_path) else ""
            if computed_id == table_asset_id:
                matched_asset = asset
                matched_by = "stable_asset_id"
                break
            if expected_image_name and asset_image_name == expected_image_name and page_idx == asset.page_idx:
                distance = _bbox_distance(bbox, asset.bbox)
                if distance < best_distance:
                    best_distance = distance
                    matched_asset = asset
                    matched_by = "image_page_bbox"
            elif expected_image_name and asset_image_name == expected_image_name and matched_asset is None:
                matched_asset = asset
                matched_by = "image_filename"

        if matched_asset is not None:
            initial_raw_block = matched_asset.extra.get("raw_block", {}) if isinstance(matched_asset.extra, dict) else {}
            initial_body = _norm(initial_raw_block.get("table_body") or initial_raw_block.get("html") or initial_raw_block.get("table_html") or initial_raw_block.get("text"))
            if not initial_body:
                matched_image_name = Path(_norm(matched_asset.image_path)).name if _norm(matched_asset.image_path) else expected_image_name
                fallback_candidates = []
                for asset in result.table_assets:
                    raw_block = asset.extra.get("raw_block", {}) if isinstance(asset.extra, dict) else {}
                    body = _norm(raw_block.get("table_body") or raw_block.get("html") or raw_block.get("table_html") or raw_block.get("text"))
                    if not body:
                        continue
                    asset_image_name = Path(_norm(asset.image_path)).name if _norm(asset.image_path) else ""
                    if matched_image_name and asset_image_name != matched_image_name:
                        continue
                    if page_idx is not None and asset.page_idx != page_idx:
                        continue
                    fallback_candidates.append((asset, _bbox_distance(bbox, asset.bbox)))
                if fallback_candidates:
                    fallback_candidates.sort(key=lambda item: item[1])
                    matched_asset = fallback_candidates[0][0]
                    matched_by = f"{matched_by}|fallback_nonempty_body" if matched_by else "fallback_nonempty_body"

        if matched_asset is None:
            warnings.append("TABLE_BODY_NOT_FOUND")
            extracted_item = ExtractedTableBody(
                selected_rank=selected_rank,
                source_report_name=report_name,
                table_asset_id=table_asset_id,
                image_path=image_path,
                page_idx=page_idx,
                bbox=bbox,
                effective_role_category=effective_role_category,
                table_title_final=table_title_final,
                match_status="TABLE_BODY_NOT_FOUND",
                matched_by="no_asset_match",
                content_source_file="",
                content_item_index=None,
                has_table_body=False,
                has_html=False,
                has_markdown_table=False,
                raw_table_title="",
                raw_unit="",
                raw_table_text="",
                raw_table_html="",
                provenance={"selected_rank": selected_rank, "report_dir": str(report_dir)},
                warnings=warnings,
            )
            extracted.append(extracted_item)
            audit_rows.append(
                {
                    "selected_rank": selected_rank,
                    "source_report_name": report_name,
                    "table_asset_id": table_asset_id,
                    "image_path": image_path,
                    "match_status": extracted_item.match_status,
                    "matched_by": extracted_item.matched_by,
                    "content_source_file": extracted_item.content_source_file,
                    "content_item_index": "",
                    "has_table_body": False,
                    "has_html": False,
                    "has_markdown_table": False,
                    "extracted_row_count": 0,
                    "extracted_column_count": 0,
                    "warnings": "|".join(warnings),
                }
            )
            continue

        raw_block = matched_asset.extra.get("raw_block", {}) if isinstance(matched_asset.extra, dict) else {}
        table_body = _norm(raw_block.get("table_body") or raw_block.get("html") or raw_block.get("table_html"))
        raw_text = _norm(raw_block.get("text"))
        caption = raw_block.get("table_caption")
        raw_table_title = ""
        if isinstance(caption, list):
            raw_table_title = " ".join(_norm(item) for item in caption if _norm(item))
        else:
            raw_table_title = _norm(caption)
        if not raw_table_title:
            raw_table_title = _norm(matched_asset.caption)
        if not raw_table_title:
            raw_table_title = _extract_title_from_html(table_body)

        has_html = "<table" in table_body.lower()
        has_markdown_table = "|" in raw_text and "\n" in raw_text
        has_table_body = bool(table_body or raw_text)
        if not has_table_body:
            warnings.append("TABLE_BODY_EMPTY")

        extracted_item = ExtractedTableBody(
            selected_rank=selected_rank,
            source_report_name=report_name,
            table_asset_id=table_asset_id,
            image_path=image_path,
            page_idx=page_idx,
            bbox=bbox,
            effective_role_category=effective_role_category,
            table_title_final=table_title_final,
            match_status="TABLE_BODY_FOUND" if has_table_body else "TABLE_BODY_NOT_FOUND",
            matched_by=matched_by or "asset_match",
            content_source_file=_norm(matched_asset.source_file),
            content_item_index=matched_asset.block_index,
            has_table_body=has_table_body,
            has_html=has_html,
            has_markdown_table=has_markdown_table,
            raw_table_title=raw_table_title,
            raw_unit="",
            raw_table_text=raw_text or table_body,
            raw_table_html=table_body,
            provenance={
                "selected_rank": selected_rank,
                "report_dir": str(report_dir),
                "source_kind": _norm(matched_asset.source_kind),
                "raw_block_type": _norm(matched_asset.raw_block_type),
                "raw_block_id": _norm(matched_asset.raw_block_id),
                "image_path": _norm(matched_asset.image_path),
                "caption": _norm(matched_asset.caption),
                "footnote": _norm(matched_asset.footnote),
                "nearby_text": _norm(matched_asset.nearby_text),
            },
            warnings=warnings,
        )
        extracted.append(extracted_item)
        row_count = 0
        column_count = 0
        if extracted_item.raw_table_html:
            try:
                tables = pd.read_html(StringIO(extracted_item.raw_table_html))
                if tables:
                    parsed = tables[0].fillna("")
                    row_count = int(len(parsed))
                    column_count = int(len(parsed.columns))
            except Exception:
                warnings.append("HTML_PARSE_FAILED")
        audit_rows.append(
            {
                "selected_rank": selected_rank,
                "source_report_name": report_name,
                "table_asset_id": table_asset_id,
                "image_path": image_path,
                "match_status": extracted_item.match_status,
                "matched_by": extracted_item.matched_by,
                "content_source_file": extracted_item.content_source_file,
                "content_item_index": extracted_item.content_item_index if extracted_item.content_item_index is not None else "",
                "has_table_body": extracted_item.has_table_body,
                "has_html": extracted_item.has_html,
                "has_markdown_table": extracted_item.has_markdown_table,
                "extracted_row_count": row_count,
                "extracted_column_count": column_count,
                "warnings": "|".join(warnings),
            }
        )

    return extracted, pd.DataFrame(audit_rows)
