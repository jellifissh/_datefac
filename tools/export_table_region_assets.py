import argparse
import traceback
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    import pdfplumber
except Exception:  # pragma: no cover
    pdfplumber = None

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None


DEFAULT_INPUT_DIR = Path(r"D:\_datefac\input")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output")
ASSET_SUFFIX = "_" + "\u8d44\u4ea7\u5305"
DEFAULT_GLOBAL_REPORT = Path(r"D:\_datefac\output\25_table_region_assets_overview.xlsx")

COL_CANDIDATES = {
    "source_pdf": ["source_pdf"],
    "backend": ["backend"],
    "backend_profile": ["backend_profile", "profile", "selected_profile"],
    "page": ["page", "page_number"],
    "table_index": ["table_index", "table_idx", "index"],
    "sheet_name": ["sheet_name"],
    "row_count": ["row_count"],
    "col_count": ["col_count"],
    "quality_score": ["quality_score"],
    "quality_level": ["quality_level"],
    "quality_flags": ["quality_flags"],
    "preview": ["preview"],
}


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _to_int(v, default: int = 0) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def _to_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _safe_sheet_name(name: str, used: set) -> str:
    invalid = "\\/*?:[]"
    s = "".join("_" if c in invalid else c for c in (_norm(name) or "Sheet"))[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


def _save_excel_robust(sheet_map: Dict[str, pd.DataFrame], report_path: Path) -> str:
    final = report_path
    if report_path.exists():
        try:
            with open(report_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final = report_path.with_name(f"{report_path.stem}_copy_{ts}{report_path.suffix}")

    used = set()
    with pd.ExcelWriter(final, engine="openpyxl") as writer:
        for sheet, df in sheet_map.items():
            safe = _safe_sheet_name(sheet, used)
            out_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out_df.to_excel(writer, sheet_name=safe, index=False)
    return str(final)


def _find_asset_dirs(output_dir: Path) -> List[Path]:
    if not output_dir.exists():
        return []
    return sorted([p for p in output_dir.iterdir() if p.is_dir() and p.name.endswith(ASSET_SUFFIX)], key=lambda x: x.name)


def _find_pdf_map(input_dir: Path) -> Dict[str, Path]:
    mapping = {}
    if not input_dir.exists():
        return mapping
    for p in input_dir.glob("*.pdf"):
        if p.is_file():
            mapping[p.stem] = p
    return mapping


def _find_col(df: pd.DataFrame, names: List[str]) -> Optional[str]:
    if df is None or df.empty:
        return None
    cols = list(df.columns)
    lower = {str(c).strip().lower(): c for c in cols}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    # contains fallback for english names
    for n in names:
        key = n.lower()
        for c in cols:
            cl = str(c).strip().lower()
            if key in cl:
                return c
    return None


def _load_02a_index(file_02a: Path, logs: List[str]) -> pd.DataFrame:
    try:
        xls = pd.ExcelFile(file_02a, engine="openpyxl")
        idx_sheet = next((s for s in xls.sheet_names if s.startswith("00_")), xls.sheet_names[0])
        df = pd.read_excel(file_02a, sheet_name=idx_sheet, engine="openpyxl").fillna("")
        logs.append(f"02A loaded: {file_02a.name}, sheet={idx_sheet}, rows={len(df)}")
        return df
    except Exception as exc:
        logs.append(f"02A load failed: {exc}")
        return pd.DataFrame()


def _load_optional_17(output_dir: Path) -> pd.DataFrame:
    path = output_dir / "17_raw_table_business_relevance_report.xlsx"
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name="table_relevance_details", engine="openpyxl").fillna("")
    except Exception:
        return pd.DataFrame()


def _load_optional_19(output_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    path = output_dir / "19_financial_value_validation_report.xlsx"
    if not path.exists():
        return pd.DataFrame(), pd.DataFrame()
    try:
        d = pd.read_excel(path, sheet_name="metric_value_details", engine="openpyxl").fillna("")
    except Exception:
        d = pd.DataFrame()
    try:
        a = pd.read_excel(path, sheet_name="asset_value_summary", engine="openpyxl").fillna("")
    except Exception:
        a = pd.DataFrame()
    return d, a


def _load_05_detail(asset_dir: Path) -> pd.DataFrame:
    file_05 = next((x for x in asset_dir.glob("05_*.xlsx") if x.is_file()), None)
    if not file_05:
        return pd.DataFrame()
    try:
        xls = pd.ExcelFile(file_05, engine="openpyxl")
        for s in xls.sheet_names:
            df = pd.read_excel(file_05, sheet_name=s, engine="openpyxl").fillna("")
            if "source_row_label" in df.columns:
                return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _build_05_table_link_map(df05: pd.DataFrame) -> Dict[str, Dict[str, object]]:
    out: Dict[str, Dict[str, object]] = {}
    if df05.empty:
        return out
    metric_col = "标准指标" if "标准指标" in df05.columns else ("standard_metric" if "standard_metric" in df05.columns else None)
    table_col = "source_table_index" if "source_table_index" in df05.columns else None
    if not metric_col or not table_col:
        return out
    grouped = defaultdict(set)
    for _, r in df05.iterrows():
        tid = _norm(r.get(table_col))
        met = _norm(r.get(metric_col))
        if not tid or not met:
            continue
        grouped[tid].add(met)
    for tid, mets in grouped.items():
        out[tid] = {
            "linked_metric_count": len(mets),
            "linked_metrics": "|".join(sorted(mets)),
        }
    return out


def _build_19_link_maps(detail19: pd.DataFrame, asset19: pd.DataFrame) -> Tuple[Dict[Tuple[str, str], Dict[str, object]], Dict[str, Dict[str, object]]]:
    # per (asset, source_table_index)
    per_table: Dict[Tuple[str, str], Dict[str, object]] = {}
    per_asset: Dict[str, Dict[str, object]] = {}
    if not asset19.empty and "asset_package" in asset19.columns:
        for _, r in asset19.iterrows():
            asset = _norm(r.get("asset_package"))
            if not asset:
                continue
            per_asset[asset] = {
                "linked_valid_metric_count": _to_int(r.get("value_valid_metric_count"), 0),
                "linked_invalid_metric_count": _to_int(r.get("value_invalid_metric_count"), 0),
                "linked_suspicious_metric_count": _to_int(r.get("value_suspicious_metric_count"), 0),
            }

    if detail19.empty:
        return per_table, per_asset

    cols = detail19.columns
    if not {"asset_package", "source_table_index", "standard_metric", "validation_status"}.issubset(set(cols)):
        return per_table, per_asset

    grouped = defaultdict(list)
    for _, r in detail19.iterrows():
        asset = _norm(r.get("asset_package"))
        tid = _norm(r.get("source_table_index"))
        metric = _norm(r.get("standard_metric"))
        status = _norm(r.get("validation_status")).lower()
        flags = _norm(r.get("issue_flags"))
        if not asset or not tid or not metric:
            continue
        grouped[(asset, tid)].append((metric, status, flags))

    for key, rows in grouped.items():
        metric_state: Dict[str, str] = {}
        all_flags = []
        for metric, status, flags in rows:
            prev = metric_state.get(metric, "")
            if status == "invalid" or prev == "invalid":
                metric_state[metric] = "invalid"
            elif status == "suspicious" or prev == "suspicious":
                metric_state[metric] = "suspicious"
            elif status == "valid" or prev == "valid":
                metric_state[metric] = "valid"
            if flags:
                all_flags.extend([x.strip() for x in flags.replace(";", "|").split("|") if x.strip()])

        linked_metrics = sorted(metric_state.keys())
        valid = sum(1 for _, s in metric_state.items() if s == "valid")
        invalid = sum(1 for _, s in metric_state.items() if s == "invalid")
        suspicious = sum(1 for _, s in metric_state.items() if s == "suspicious")
        uniq_flags = []
        seen = set()
        for f in all_flags:
            if f not in seen:
                seen.add(f)
                uniq_flags.append(f)

        per_table[key] = {
            "linked_metric_count": len(linked_metrics),
            "linked_valid_metric_count": valid,
            "linked_invalid_metric_count": invalid,
            "linked_suspicious_metric_count": suspicious,
            "linked_metrics": "|".join(linked_metrics),
            "linked_issue_flags": "|".join(uniq_flags),
        }

    return per_table, per_asset


def _build_17_maps(df17: pd.DataFrame) -> Tuple[Dict[Tuple[str, str], Dict[str, object]], Dict[Tuple[str, int, int], Dict[str, object]]]:
    by_sheet = {}
    by_page_idx = {}
    if df17.empty:
        return by_sheet, by_page_idx
    for _, r in df17.iterrows():
        asset = _norm(r.get("asset_package"))
        sheet = _norm(r.get("sheet_name"))
        page = _to_int(r.get("page"), -1)
        tidx = _to_int(r.get("table_index"), -1)
        payload = {
            "business_table_type": _norm(r.get("business_table_type")),
            "business_relevance_score": _to_float(r.get("business_relevance_score"), 0.0),
            "financial_keyword_count": _to_int(r.get("financial_keyword_count"), 0),
            "metric_keyword_count": _to_int(r.get("metric_keyword_count"), 0),
            "year_token_count": _to_int(r.get("year_token_count"), 0),
        }
        if asset and sheet:
            by_sheet[(asset, sheet)] = payload
        if asset and page >= 0 and tidx >= 0:
            by_page_idx[(asset, page, tidx)] = payload
    return by_sheet, by_page_idx


def _detect_bboxes(pdf_path: Path, logs: List[str]) -> Dict[int, List[Tuple[float, float, float, float]]]:
    out: Dict[int, List[Tuple[float, float, float, float]]] = defaultdict(list)
    if pdfplumber is None:
        logs.append("bbox detect skipped: pdfplumber not available")
        return out
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_no, page in enumerate(pdf.pages, start=1):
                try:
                    tables = page.find_tables()
                    out[page_no] = [tuple(tb.bbox) for tb in tables if tb.bbox]
                except Exception as exc:
                    logs.append(f"bbox detect failed on page {page_no}: {exc}")
                    out[page_no] = []
        logs.append(f"bbox detected pages={len(out)}")
    except Exception as exc:
        logs.append(f"bbox detect failed for pdf: {exc}")
    return out


def _clip_rect(x0: float, y0: float, x1: float, y1: float, max_w: float, max_h: float, pad: float = 10.0) -> Tuple[float, float, float, float]:
    nx0 = max(0.0, x0 - pad)
    ny0 = max(0.0, y0 - pad)
    nx1 = min(max_w, x1 + pad)
    ny1 = min(max_h, y1 + pad)
    if nx1 <= nx0:
        nx1 = min(max_w, nx0 + 1.0)
    if ny1 <= ny0:
        ny1 = min(max_h, ny0 + 1.0)
    return nx0, ny0, nx1, ny1


def _render_page_and_crop(
    pdf_path: Path,
    page_number: int,
    bbox: Optional[Tuple[float, float, float, float]],
    page_png: Path,
    crop_png: Optional[Path],
    logs: List[str],
) -> bool:
    # Prefer PyMuPDF; fallback to pdfplumber images.
    if fitz is not None:
        try:
            doc = fitz.open(str(pdf_path))
            page = doc[page_number - 1]
            if not page_png.exists():
                pix_page = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0), alpha=False)
                page_png.parent.mkdir(parents=True, exist_ok=True)
                pix_page.save(str(page_png))
            if bbox and crop_png:
                x0, y0, x1, y1 = _clip_rect(bbox[0], bbox[1], bbox[2], bbox[3], page.rect.width, page.rect.height, pad=10.0)
                clip = fitz.Rect(x0, y0, x1, y1)
                pix_crop = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), clip=clip, alpha=False)
                crop_png.parent.mkdir(parents=True, exist_ok=True)
                pix_crop.save(str(crop_png))
            doc.close()
            return True
        except Exception as exc:
            logs.append(f"fitz render failed page {page_number}: {exc}")

    if pdfplumber is None:
        logs.append("render failed: no fitz and no pdfplumber")
        return False

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            page = pdf.pages[page_number - 1]
            if not page_png.exists():
                im = page.to_image(resolution=72)
                page_png.parent.mkdir(parents=True, exist_ok=True)
                im.save(str(page_png), format="PNG")
            if bbox and crop_png:
                crop = page.crop(bbox)
                cim = crop.to_image(resolution=150)
                crop_png.parent.mkdir(parents=True, exist_ok=True)
                cim.save(str(crop_png), format="PNG")
        return True
    except Exception as exc:
        logs.append(f"pdfplumber render failed page {page_number}: {exc}")
        return False


def _match_bbox_for_row(
    page_no: int,
    table_index: int,
    page_rows_seen: Dict[int, int],
    bboxes_by_page: Dict[int, List[Tuple[float, float, float, float]]],
) -> Tuple[Optional[Tuple[float, float, float, float]], str]:
    bboxes = bboxes_by_page.get(page_no, [])
    if not bboxes:
        return None, "unmatched"

    # explicit table_index preferred.
    if table_index >= 1 and table_index <= len(bboxes):
        return bboxes[table_index - 1], "matched"
    if table_index >= 0 and table_index < len(bboxes):
        return bboxes[table_index], "matched"

    # fallback by row order within page.
    seq = page_rows_seen.get(page_no, 0)
    if seq < len(bboxes):
        page_rows_seen[page_no] = seq + 1
        return bboxes[seq], "matched_by_order"
    return None, "unmatched"


def _needs_manual_review(row: Dict[str, object]) -> Tuple[bool, str]:
    reasons = []
    q_level = _norm(row.get("quality_level")).upper()
    q_flags = _norm(row.get("quality_flags"))
    btype = _norm(row.get("business_table_type"))
    invalid_cnt = _to_int(row.get("linked_invalid_metric_count"), 0)
    bbox_status = _norm(row.get("bbox_status"))

    if q_level == "BAD":
        reasons.append("quality_bad")
    if "possible_glued_table" in q_flags or "single_column" in q_flags:
        reasons.append("quality_flag_risky")
    if btype in {"glued_financial_table", "narrative_text_table", "disclaimer_or_rating_table"}:
        reasons.append("business_type_risky")
    if invalid_cnt > 0:
        reasons.append("linked_invalid_metric")
    if bbox_status != "matched":
        reasons.append("bbox_not_strict_matched")

    return bool(reasons), "|".join(reasons)


def _write_debug_log(debug_path: Path, logs: List[str]) -> None:
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    with open(debug_path, "w", encoding="utf-8") as f:
        for line in logs:
            f.write(line.rstrip() + "\n")


def export_table_region_assets(input_dir: Path, output_dir: Path, global_report_path: Path) -> Tuple[Dict[str, int], str]:
    asset_dirs = _find_asset_dirs(output_dir)
    pdf_map = _find_pdf_map(input_dir)
    df17 = _load_optional_17(output_dir)
    detail19, asset19 = _load_optional_19(output_dir)
    map17_sheet, map17_page = _build_17_maps(df17)
    map19_table, map19_asset = _build_19_link_maps(detail19, asset19)

    all_rows: List[Dict[str, object]] = []
    asset_summary_rows: List[Dict[str, object]] = []

    scanned_asset_count = len(asset_dirs)
    processed_asset_count = 0
    total_table_regions = 0
    crop_generated_count = 0
    unmatched_bbox_count = 0

    for asset_dir in asset_dirs:
        logs = [f"[{datetime.now().isoformat()}] start asset={asset_dir.name}"]
        try:
            stem = asset_dir.name[:-len(ASSET_SUFFIX)] if asset_dir.name.endswith(ASSET_SUFFIX) else asset_dir.name
            pdf_path = pdf_map.get(stem)
            if not pdf_path:
                logs.append(f"pdf not found for stem={stem}")
            else:
                logs.append(f"pdf matched: {pdf_path}")

            out_dir = asset_dir / "02B_table_region_assets"
            crops_dir = out_dir / "crops"
            pages_dir = out_dir / "pages"
            debug_dir = out_dir / "debug"
            out_dir.mkdir(parents=True, exist_ok=True)
            crops_dir.mkdir(parents=True, exist_ok=True)
            pages_dir.mkdir(parents=True, exist_ok=True)
            debug_dir.mkdir(parents=True, exist_ok=True)

            file_02a = next((x for x in asset_dir.glob("02A_*.xlsx") if x.is_file()), None)
            if not file_02a:
                logs.append("02A not found; skip asset")
                _write_debug_log(debug_dir / "table_region_export_log.txt", logs)
                asset_summary_rows.append(
                    {
                        "asset_package": asset_dir.name,
                        "total_regions": 0,
                        "matched_bbox_count": 0,
                        "unmatched_bbox_count": 0,
                        "crop_generated_count": 0,
                        "financial_region_count": 0,
                        "glued_region_count": 0,
                        "review_region_count": 0,
                    }
                )
                processed_asset_count += 1
                continue

            df02a = _load_02a_index(file_02a, logs)
            if df02a.empty:
                logs.append("02A index empty; skip asset")
                _write_debug_log(debug_dir / "table_region_export_log.txt", logs)
                asset_summary_rows.append(
                    {
                        "asset_package": asset_dir.name,
                        "total_regions": 0,
                        "matched_bbox_count": 0,
                        "unmatched_bbox_count": 0,
                        "crop_generated_count": 0,
                        "financial_region_count": 0,
                        "glued_region_count": 0,
                        "review_region_count": 0,
                    }
                )
                processed_asset_count += 1
                continue

            # detect bboxes
            bboxes_by_page = _detect_bboxes(pdf_path, logs) if pdf_path else {}
            page_rows_seen: Dict[int, int] = {}

            # optional linked maps
            df05 = _load_05_detail(asset_dir)
            map05_table = _build_05_table_link_map(df05)

            # resolve 02A columns
            c_source_pdf = _find_col(df02a, COL_CANDIDATES["source_pdf"])
            c_backend = _find_col(df02a, COL_CANDIDATES["backend"])
            c_backend_profile = _find_col(df02a, COL_CANDIDATES["backend_profile"])
            c_page = _find_col(df02a, COL_CANDIDATES["page"])
            c_table_index = _find_col(df02a, COL_CANDIDATES["table_index"])
            c_sheet_name = _find_col(df02a, COL_CANDIDATES["sheet_name"])
            c_row_count = _find_col(df02a, COL_CANDIDATES["row_count"])
            c_col_count = _find_col(df02a, COL_CANDIDATES["col_count"])
            c_quality_score = _find_col(df02a, COL_CANDIDATES["quality_score"])
            c_quality_level = _find_col(df02a, COL_CANDIDATES["quality_level"])
            c_quality_flags = _find_col(df02a, COL_CANDIDATES["quality_flags"])
            c_preview = _find_col(df02a, COL_CANDIDATES["preview"])

            asset_rows = []
            for _, r in df02a.iterrows():
                page_no = _to_int(r.get(c_page, 0), 0) if c_page else 0
                table_index = _to_int(r.get(c_table_index, 0), 0) if c_table_index else 0
                sheet_name = _norm(r.get(c_sheet_name, "")) if c_sheet_name else ""

                bbox, bbox_status = _match_bbox_for_row(page_no, table_index, page_rows_seen, bboxes_by_page)
                x0 = y0 = x1 = y1 = ""
                crop_path = ""
                page_path = ""

                if bbox:
                    x0, y0, x1, y1 = bbox
                    crop_file = crops_dir / f"page_{page_no:03d}_table_{max(table_index,1):03d}.png"
                    page_file = pages_dir / f"page_{page_no:03d}.png"
                    ok = False
                    if pdf_path and page_no > 0:
                        ok = _render_page_and_crop(pdf_path, page_no, bbox, page_file, crop_file, logs)
                    if ok and crop_file.exists():
                        crop_path = str(crop_file)
                    if page_file.exists():
                        page_path = str(page_file)
                    if not ok and bbox_status.startswith("matched"):
                        bbox_status = "matched_but_crop_failed"
                else:
                    if bbox_status == "unmatched":
                        unmatched_bbox_count += 1

                row = {
                    "asset_package": asset_dir.name,
                    "source_pdf": _norm(r.get(c_source_pdf, "")) if c_source_pdf else (pdf_path.name if pdf_path else ""),
                    "pdf_path": str(pdf_path) if pdf_path else "",
                    "page_number": page_no,
                    "table_index": table_index,
                    "sheet_name": sheet_name,
                    "backend": _norm(r.get(c_backend, "")) if c_backend else "",
                    "backend_profile": _norm(r.get(c_backend_profile, "")) if c_backend_profile else "",
                    "detector_backend": "pdfplumber.find_tables",
                    "bbox_x0": x0,
                    "bbox_y0": y0,
                    "bbox_x1": x1,
                    "bbox_y1": y1,
                    "bbox_status": bbox_status,
                    "crop_png_path": crop_path,
                    "page_png_path": page_path,
                    "row_count": _to_int(r.get(c_row_count, 0), 0) if c_row_count else 0,
                    "col_count": _to_int(r.get(c_col_count, 0), 0) if c_col_count else 0,
                    "quality_score": _to_float(r.get(c_quality_score, 0), 0.0) if c_quality_score else 0.0,
                    "quality_level": _norm(r.get(c_quality_level, "")) if c_quality_level else "",
                    "quality_flags": _norm(r.get(c_quality_flags, "")) if c_quality_flags else "",
                    "preview": _norm(r.get(c_preview, "")) if c_preview else "",
                    "business_table_type": "",
                    "business_relevance_score": "",
                    "financial_keyword_count": "",
                    "metric_keyword_count": "",
                    "year_token_count": "",
                    "linked_metric_count": 0,
                    "linked_valid_metric_count": 0,
                    "linked_invalid_metric_count": 0,
                    "linked_suspicious_metric_count": 0,
                    "linked_metrics": "",
                    "linked_issue_flags": "",
                    "linked_05_status": "",
                    "needs_manual_review": False,
                    "review_reason": "",
                }

                # enrich from 17
                p17 = map17_sheet.get((asset_dir.name, sheet_name), None)
                if p17 is None:
                    p17 = map17_page.get((asset_dir.name, page_no, table_index), None)
                if p17:
                    row.update(
                        {
                            "business_table_type": _norm(p17.get("business_table_type")),
                            "business_relevance_score": p17.get("business_relevance_score", ""),
                            "financial_keyword_count": p17.get("financial_keyword_count", ""),
                            "metric_keyword_count": p17.get("metric_keyword_count", ""),
                            "year_token_count": p17.get("year_token_count", ""),
                        }
                    )

                tid_str = str(table_index)
                # enrich linked metrics from 05
                if tid_str in map05_table:
                    row["linked_metric_count"] = _to_int(map05_table[tid_str].get("linked_metric_count"), 0)
                    row["linked_metrics"] = _norm(map05_table[tid_str].get("linked_metrics"))

                # enrich validity from 19 table-level
                k19 = (asset_dir.name, tid_str)
                if k19 in map19_table:
                    t19 = map19_table[k19]
                    row["linked_metric_count"] = _to_int(t19.get("linked_metric_count"), row["linked_metric_count"])
                    row["linked_valid_metric_count"] = _to_int(t19.get("linked_valid_metric_count"), 0)
                    row["linked_invalid_metric_count"] = _to_int(t19.get("linked_invalid_metric_count"), 0)
                    row["linked_suspicious_metric_count"] = _to_int(t19.get("linked_suspicious_metric_count"), 0)
                    if _norm(t19.get("linked_metrics")):
                        row["linked_metrics"] = _norm(t19.get("linked_metrics"))
                    row["linked_issue_flags"] = _norm(t19.get("linked_issue_flags"))
                else:
                    # fallback asset-level from 19 summary
                    a19 = map19_asset.get(asset_dir.name, {})
                    if a19:
                        row["linked_valid_metric_count"] = _to_int(a19.get("linked_valid_metric_count"), 0)
                        row["linked_invalid_metric_count"] = _to_int(a19.get("linked_invalid_metric_count"), 0)
                        row["linked_suspicious_metric_count"] = _to_int(a19.get("linked_suspicious_metric_count"), 0)

                row["linked_05_status"] = f"valid={row['linked_valid_metric_count']};invalid={row['linked_invalid_metric_count']};suspicious={row['linked_suspicious_metric_count']}"

                needs, reason = _needs_manual_review(row)
                row["needs_manual_review"] = needs
                row["review_reason"] = reason

                if crop_path:
                    crop_generated_count += 1
                if not bbox and bbox_status != "matched":
                    unmatched_bbox_count += 1

                asset_rows.append(row)
                all_rows.append(row)

            idx_path = out_dir / "table_region_index.xlsx"
            _save_excel_robust({"table_region_index": pd.DataFrame(asset_rows)}, idx_path)
            logs.append(f"table_region_index saved: {idx_path}")

            # asset summary row
            adf = pd.DataFrame(asset_rows)
            if adf.empty:
                asset_summary_rows.append(
                    {
                        "asset_package": asset_dir.name,
                        "total_regions": 0,
                        "matched_bbox_count": 0,
                        "unmatched_bbox_count": 0,
                        "crop_generated_count": 0,
                        "financial_region_count": 0,
                        "glued_region_count": 0,
                        "review_region_count": 0,
                    }
                )
            else:
                matched_count = int((adf["bbox_status"].astype(str) == "matched").sum())
                unmatched_count = int((adf["bbox_status"].astype(str) != "matched").sum())
                crop_count = int(adf["crop_png_path"].astype(str).str.len().gt(0).sum())
                financial_count = int(adf["business_table_type"].astype(str).isin(["financial_candidate", "glued_financial_table"]).sum())
                glued_count = int(
                    adf["business_table_type"].astype(str).eq("glued_financial_table").sum()
                    + adf["quality_flags"].astype(str).str.contains("possible_glued_table", na=False).sum()
                )
                review_count = int(adf["needs_manual_review"].astype(bool).sum())
                asset_summary_rows.append(
                    {
                        "asset_package": asset_dir.name,
                        "total_regions": len(adf),
                        "matched_bbox_count": matched_count,
                        "unmatched_bbox_count": unmatched_count,
                        "crop_generated_count": crop_count,
                        "financial_region_count": financial_count,
                        "glued_region_count": glued_count,
                        "review_region_count": review_count,
                    }
                )
            total_table_regions += len(asset_rows)
            processed_asset_count += 1

        except Exception as exc:
            logs.append(f"asset failed: {exc}")
            logs.append(traceback.format_exc())
        finally:
            debug_file = asset_dir / "02B_table_region_assets" / "debug" / "table_region_export_log.txt"
            _write_debug_log(debug_file, logs)

    all_df = pd.DataFrame(all_rows)
    summary_df = pd.DataFrame(asset_summary_rows)
    needs_review_df = all_df[all_df["needs_manual_review"].astype(bool)] if not all_df.empty else pd.DataFrame()

    global_report = _save_excel_robust(
        {
            "table_regions_all": all_df,
            "asset_summary": summary_df,
            "needs_review_regions": needs_review_df,
        },
        global_report_path,
    )

    stats = {
        "scanned_asset_count": scanned_asset_count,
        "processed_asset_count": processed_asset_count,
        "total_table_regions": total_table_regions,
        "crop_generated_count": crop_generated_count,
        "unmatched_bbox_count": unmatched_bbox_count,
    }
    return stats, global_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Export table region assets (02B) from existing asset packages and input PDFs.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR), help="Input PDF directory")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output asset packages directory")
    parser.add_argument("--global-report", default=str(DEFAULT_GLOBAL_REPORT), help="Global overview xlsx path")
    args = parser.parse_args()

    stats, report_path = export_table_region_assets(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        global_report_path=Path(args.global_report),
    )

    print(f"scanned_asset_count: {stats['scanned_asset_count']}")
    print(f"processed_asset_count: {stats['processed_asset_count']}")
    print(f"total_table_regions: {stats['total_table_regions']}")
    print(f"crop_generated_count: {stats['crop_generated_count']}")
    print(f"unmatched_bbox_count: {stats['unmatched_bbox_count']}")
    print(f"global_report_path: {report_path}")


if __name__ == "__main__":
    main()

