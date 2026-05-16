import argparse
import math
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None


DEFAULT_INPUT_DIR = Path(r"D:\_datefac\input")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output")
DEFAULT_REPORT_PATH = Path(r"D:\_datefac\output\27_visual_table_region_poc.xlsx")
ASSET_SUFFIX = "_" + "\u8d44\u4ea7\u5305"
TARGET_STEMS = [
    "H3_AP202605141822318031_1",
    "H3_AP202605141822317295_1",
    "H3_AP202605121822223662_1",
    "H3_AP202605141822318060_1",
]
MAX_PAGES_PER_ASSET = 5


def _ensure_openpyxl_available() -> None:
    try:
        import openpyxl  # type: ignore  # noqa: F401
        return
    except Exception:
        pass
    fallback_site = Path(r"D:\anaconda\envs\factory_v4\Lib\site-packages")
    if fallback_site.exists():
        sys.path.append(str(fallback_site))
        try:
            import openpyxl  # type: ignore  # noqa: F401
            return
        except Exception:
            pass
    raise ModuleNotFoundError(
        "openpyxl is unavailable in current environment; install openpyxl or make factory_v4 site-packages accessible."
    )


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


def _save_excel_robust(sheet_map: Dict[str, pd.DataFrame], output_path: Path) -> str:
    _ensure_openpyxl_available()
    final_path = output_path
    if output_path.exists():
        try:
            with open(output_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = output_path.with_name(f"{output_path.stem}_copy_{ts}{output_path.suffix}")

    used = set()
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        for sheet, df in sheet_map.items():
            safe = _safe_sheet_name(sheet, used)
            (df if isinstance(df, pd.DataFrame) else pd.DataFrame()).to_excel(writer, sheet_name=safe, index=False)
    return str(final_path)


def _find_asset_dir(output_dir: Path, stem: str) -> Optional[Path]:
    p = output_dir / f"{stem}{ASSET_SUFFIX}"
    if p.exists() and p.is_dir():
        return p
    return None


def _load_02b_index(asset_dir: Path) -> pd.DataFrame:
    _ensure_openpyxl_available()
    p = asset_dir / "02B_table_region_assets" / "table_region_index.xlsx"
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(p, engine="openpyxl").fillna("")
    except Exception:
        return pd.DataFrame()


def _risk_pages(df02b: pd.DataFrame, max_pages: int = MAX_PAGES_PER_ASSET) -> List[Tuple[int, str]]:
    if df02b.empty or "page_number" not in df02b.columns:
        return []
    grouped = defaultdict(lambda: {"score": 0, "reasons": []})
    for _, r in df02b.iterrows():
        p = _to_int(r.get("page_number"), 0)
        if p <= 0:
            continue
        score = 0
        reasons = []
        if _norm(r.get("bbox_status")) != "matched":
            score += 50
            reasons.append("unmatched_bbox")
        if _norm(r.get("quality_level")).upper() == "BAD":
            score += 20
            reasons.append("bad_quality")
        qf = _norm(r.get("quality_flags"))
        if "single_column" in qf:
            score += 18
            reasons.append("single_column")
        if "possible_glued_table" in qf:
            score += 15
            reasons.append("possible_glued_table")
        if _norm(r.get("needs_manual_review")).lower() in {"true", "1", "yes"}:
            score += 10
            reasons.append("needs_manual_review")

        grouped[p]["score"] += score
        grouped[p]["reasons"].extend(reasons)

    ranked = []
    for p, v in grouped.items():
        uniq_reasons = []
        seen = set()
        for rr in v["reasons"]:
            if rr not in seen:
                seen.add(rr)
                uniq_reasons.append(rr)
        ranked.append((p, v["score"], "|".join(uniq_reasons)))
    ranked.sort(key=lambda x: (-x[1], x[0]))
    return [(p, reason) for p, _, reason in ranked[:max_pages]]


def _existing_bboxes_by_page(df02b: pd.DataFrame) -> Dict[int, List[Tuple[float, float, float, float]]]:
    out = defaultdict(list)
    if df02b.empty:
        return out
    for _, r in df02b.iterrows():
        p = _to_int(r.get("page_number"), 0)
        x0 = r.get("bbox_x0", "")
        y0 = r.get("bbox_y0", "")
        x1 = r.get("bbox_x1", "")
        y1 = r.get("bbox_y1", "")
        if p <= 0:
            continue
        try:
            fx0, fy0, fx1, fy1 = float(x0), float(y0), float(x1), float(y1)
            if fx1 > fx0 and fy1 > fy0:
                out[p].append((fx0, fy0, fx1, fy1))
        except Exception:
            continue
    return out


def _iou(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0 = max(ax0, bx0)
    iy0 = max(ay0, by0)
    ix1 = min(ax1, bx1)
    iy1 = min(ay1, by1)
    iw = max(0.0, ix1 - ix0)
    ih = max(0.0, iy1 - iy0)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, (ax1 - ax0)) * max(0.0, (ay1 - ay0))
    area_b = max(0.0, (bx1 - bx0)) * max(0.0, (by1 - by0))
    denom = area_a + area_b - inter
    if denom <= 0:
        return 0.0
    return inter / denom


def _clip_bbox(bbox: Tuple[float, float, float, float], w: float, h: float, pad: float = 10.0) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = bbox
    nx0 = max(0.0, x0 - pad)
    ny0 = max(0.0, y0 - pad)
    nx1 = min(w, x1 + pad)
    ny1 = min(h, y1 + pad)
    if nx1 <= nx0:
        nx1 = min(w, nx0 + 1.0)
    if ny1 <= ny0:
        ny1 = min(h, ny0 + 1.0)
    return nx0, ny0, nx1, ny1


def _probe_pp_doclayout_backend() -> Dict[str, str]:
    status = {
        "backend_name": "pp_doclayout_or_paddlex",
        "available": False,
        "version": "",
        "error_message": "",
        "install_hint": "pip install paddlex paddlex[ocr] (or install PP-DocLayout runtime)",
    }
    try:
        import paddlex as pdx  # type: ignore
        status["version"] = _norm(getattr(pdx, "__version__", ""))
        # Real probe: importable != callable. Try lightweight construction once.
        from paddleocr import LayoutDetection  # type: ignore

        _ = LayoutDetection(model_name="PP-DocLayout-L")
        status["available"] = True
    except Exception as exc:
        status["error_message"] = f"{type(exc).__name__}: {_norm(exc)}"
    return status


def _probe_pp_structure_backend() -> Tuple[Dict[str, str], Optional[object]]:
    status = {
        "backend_name": "paddleocr_pp_structure",
        "available": False,
        "version": "",
        "error_message": "",
        "install_hint": "pip install paddleocr paddlepaddle (CPU/GPU by your environment)",
    }
    engine = None
    try:
        import paddleocr  # type: ignore
        status["version"] = _norm(getattr(paddleocr, "__version__", ""))
        if hasattr(paddleocr, "PPStructure"):
            from paddleocr import PPStructure  # type: ignore

            engine = PPStructure(show_log=False)
        elif hasattr(paddleocr, "PPStructureV3"):
            from paddleocr import PPStructureV3  # type: ignore

            engine = PPStructureV3()
        else:
            raise RuntimeError("Neither PPStructure nor PPStructureV3 is available in paddleocr.")
        status["available"] = True
    except Exception as exc:
        status["error_message"] = f"{type(exc).__name__}: {_norm(exc)}"
    return status, engine


def _render_page_png(pdf_path: Path, page_number: int, out_path: Path) -> bool:
    if fitz is None:
        return False
    try:
        doc = fitz.open(str(pdf_path))
        page = doc[page_number - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(out_path))
        doc.close()
        return True
    except Exception:
        return False


def _render_crop_png(pdf_path: Path, page_number: int, bbox: Tuple[float, float, float, float], out_path: Path) -> bool:
    if fitz is None:
        return False
    try:
        doc = fitz.open(str(pdf_path))
        page = doc[page_number - 1]
        x0, y0, x1, y1 = _clip_bbox(bbox, page.rect.width, page.rect.height, pad=10.0)
        clip = fitz.Rect(x0, y0, x1, y1)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), clip=clip, alpha=False)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(out_path))
        doc.close()
        return True
    except Exception:
        return False


def _detect_with_pp_structure(engine, img_path: Path) -> List[Dict[str, object]]:
    out = []
    if engine is None:
        return out
    try:
        results = engine(str(img_path))
    except Exception:
        return out
    if not isinstance(results, list):
        return out
    for item in results:
        if not isinstance(item, dict):
            continue
        region_type = _norm(item.get("type"))
        bbox = item.get("bbox")
        score = item.get("score", item.get("confidence", ""))
        if not bbox or not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            continue
        x0, y0, x1, y1 = [float(x) for x in bbox]
        out.append(
            {
                "region_type": region_type or "unknown",
                "confidence": _to_float(score, 0.0),
                "bbox": (x0, y0, x1, y1),
            }
        )
    # keep table-like first
    table_like = [x for x in out if "table" in _norm(x.get("region_type")).lower()]
    return table_like if table_like else out


def _detect_with_pp_doclayout_stub(img_path: Path) -> List[Dict[str, object]]:
    # Placeholder: doclayout path is only used if PPStructure path is unavailable.
    _ = img_path
    return []


def probe_visual_regions(input_dir: Path, output_dir: Path, report_path: Path) -> Tuple[str, Dict[str, object], pd.DataFrame]:
    backend_rows = []
    visual_rows = []
    page_rows = []
    asset_rows = []

    # backend availability
    st_doclayout = _probe_pp_doclayout_backend()
    st_pps, pp_structure_engine = _probe_pp_structure_backend()
    backend_rows.append(st_doclayout)
    backend_rows.append(st_pps)

    has_visual_backend = bool(st_doclayout["available"] or st_pps["available"])

    for stem in TARGET_STEMS:
        asset_dir = _find_asset_dir(output_dir, stem)
        pdf_path = input_dir / f"{stem}.pdf"
        if not asset_dir or not pdf_path.exists():
            asset_rows.append(
                {
                    "asset_package": f"{stem}{ASSET_SUFFIX}" if asset_dir else "",
                    "processed_pages": 0,
                    "existing_02B_region_count": 0,
                    "visual_region_count": 0,
                    "new_candidate_count": 0,
                    "matched_count": 0,
                    "avg_iou": 0.0,
                    "backend_status": "unavailable_or_missing_input",
                    "poc_result": "worse_or_unavailable",
                }
            )
            continue

        df02b = _load_02b_index(asset_dir)
        if df02b.empty:
            asset_rows.append(
                {
                    "asset_package": asset_dir.name,
                    "processed_pages": 0,
                    "existing_02B_region_count": 0,
                    "visual_region_count": 0,
                    "new_candidate_count": 0,
                    "matched_count": 0,
                    "avg_iou": 0.0,
                    "backend_status": "02b_missing_or_empty",
                    "poc_result": "worse_or_unavailable",
                }
            )
            continue

        out_dir = asset_dir / "27_visual_table_region_poc"
        pages_dir = out_dir / "pages"
        crops_dir = out_dir / "crops"
        out_dir.mkdir(parents=True, exist_ok=True)
        pages_dir.mkdir(parents=True, exist_ok=True)
        crops_dir.mkdir(parents=True, exist_ok=True)

        page_candidates = _risk_pages(df02b, max_pages=MAX_PAGES_PER_ASSET)
        existing_boxes = _existing_bboxes_by_page(df02b)

        vis_count_total = 0
        new_count_total = 0
        matched_total = 0
        iou_values = []

        per_asset_visual_rows = []

        for page_number, page_reason in page_candidates:
            page_png = pages_dir / f"page_{page_number:03d}.png"
            rendered = _render_page_png(pdf_path, page_number, page_png)
            if not rendered:
                page_rows.append(
                    {
                        "asset_package": asset_dir.name,
                        "page_number": page_number,
                        "existing_02B_region_count": len(existing_boxes.get(page_number, [])),
                        "visual_region_count": 0,
                        "new_candidate_count": 0,
                        "matched_count": 0,
                        "average_best_iou": 0.0,
                        "high_risk_page_reason": page_reason,
                        "poc_judgement": "page_render_failed",
                    }
                )
                continue

            detected_regions = []
            used_backend = ""

            if st_pps["available"]:
                detected_regions = _detect_with_pp_structure(pp_structure_engine, page_png)
                used_backend = "paddleocr_pp_structure"
            elif st_doclayout["available"]:
                detected_regions = _detect_with_pp_doclayout_stub(page_png)
                used_backend = "pp_doclayout_or_paddlex"
            else:
                used_backend = "unavailable"

            page_existing = existing_boxes.get(page_number, [])
            page_vis = 0
            page_new = 0
            page_match = 0
            page_ious = []

            for i, det in enumerate(detected_regions, start=1):
                bbox = det["bbox"]
                best_iou = 0.0
                if page_existing:
                    for eb in page_existing:
                        best_iou = max(best_iou, _iou(bbox, eb))
                matched_existing = best_iou >= 0.5
                is_new_candidate = best_iou < 0.3
                may_split_multi = len(page_existing) >= 1 and len(detected_regions) > len(page_existing)
                may_reduce_unmatched = is_new_candidate and _norm(page_reason).find("unmatched_bbox") >= 0

                crop_path = crops_dir / f"page_{page_number:03d}_visual_{i:03d}.png"
                _render_crop_png(pdf_path, page_number, bbox, crop_path)

                review_reason_parts = []
                if is_new_candidate:
                    review_reason_parts.append("new_visual_candidate")
                if may_split_multi:
                    review_reason_parts.append("may_split_multi_table_page")
                if may_reduce_unmatched:
                    review_reason_parts.append("may_reduce_unmatched")
                if matched_existing:
                    review_reason_parts.append("matched_existing_02B")
                review_reason = "|".join(review_reason_parts)

                rec = {
                    "asset_package": asset_dir.name,
                    "source_pdf": pdf_path.name,
                    "page_number": page_number,
                    "detector_backend": used_backend,
                    "region_type": _norm(det.get("region_type")),
                    "confidence": _to_float(det.get("confidence"), 0.0),
                    "bbox_x0": bbox[0],
                    "bbox_y0": bbox[1],
                    "bbox_x1": bbox[2],
                    "bbox_y1": bbox[3],
                    "crop_path": str(crop_path) if crop_path.exists() else "",
                    "matched_existing_02B": bool(matched_existing),
                    "best_iou": best_iou,
                    "is_new_candidate": bool(is_new_candidate),
                    "may_split_multi_table_page": bool(may_split_multi),
                    "may_reduce_unmatched": bool(may_reduce_unmatched),
                    "review_reason": review_reason,
                }
                visual_rows.append(rec)
                per_asset_visual_rows.append(rec)

                page_vis += 1
                vis_count_total += 1
                page_ious.append(best_iou)
                iou_values.append(best_iou)
                if matched_existing:
                    page_match += 1
                    matched_total += 1
                if is_new_candidate:
                    page_new += 1
                    new_count_total += 1

            page_avg_iou = sum(page_ious) / len(page_ious) if page_ious else 0.0
            if page_new > 0 and page_vis > len(page_existing):
                page_judgement = "promising"
            elif page_vis == 0 and not has_visual_backend:
                page_judgement = "worse_or_unavailable"
            else:
                page_judgement = "neutral"

            page_rows.append(
                {
                    "asset_package": asset_dir.name,
                    "page_number": page_number,
                    "existing_02B_region_count": len(page_existing),
                    "visual_region_count": page_vis,
                    "new_candidate_count": page_new,
                    "matched_count": page_match,
                    "average_best_iou": page_avg_iou,
                    "high_risk_page_reason": page_reason,
                    "poc_judgement": page_judgement,
                }
            )

        # per-asset visual index
        per_asset_df = pd.DataFrame(per_asset_visual_rows)
        if per_asset_df.empty:
            per_asset_df = pd.DataFrame(
                columns=[
                    "asset_package",
                    "source_pdf",
                    "page_number",
                    "detector_backend",
                    "region_type",
                    "confidence",
                    "bbox_x0",
                    "bbox_y0",
                    "bbox_x1",
                    "bbox_y1",
                    "crop_path",
                    "matched_existing_02B",
                    "best_iou",
                    "is_new_candidate",
                    "may_split_multi_table_page",
                    "may_reduce_unmatched",
                    "review_reason",
                ]
            )
        _save_excel_robust({"visual_region_index": per_asset_df}, out_dir / "visual_region_index.xlsx")

        avg_iou = sum(iou_values) / len(iou_values) if iou_values else 0.0
        existing_total = len(df02b)
        if not has_visual_backend:
            poc_result = "worse_or_unavailable"
            backend_status = "unavailable"
        elif vis_count_total > existing_total and new_count_total > 0:
            poc_result = "promising"
            backend_status = "available"
        elif vis_count_total == 0:
            poc_result = "worse_or_unavailable"
            backend_status = "available_but_no_detection"
        else:
            poc_result = "neutral"
            backend_status = "available"

        asset_rows.append(
            {
                "asset_package": asset_dir.name,
                "processed_pages": len(page_candidates),
                "existing_02B_region_count": existing_total,
                "visual_region_count": vis_count_total,
                "new_candidate_count": new_count_total,
                "matched_count": matched_total,
                "avg_iou": avg_iou,
                "backend_status": backend_status,
                "poc_result": poc_result,
            }
        )

    backend_df = pd.DataFrame(backend_rows)
    visual_df = pd.DataFrame(visual_rows)
    page_df = pd.DataFrame(page_rows)
    asset_df = pd.DataFrame(asset_rows)

    out = _save_excel_robust(
        {
            "backend_status": backend_df,
            "visual_region_details": visual_df,
            "page_level_comparison": page_df,
            "asset_summary": asset_df,
        },
        report_path,
    )

    stats = {
        "backend_available": bool((backend_df.get("available", pd.Series(dtype=bool)).astype(bool).sum()) > 0),
        "report_path": out,
    }
    return out, stats, asset_df


def main() -> None:
    parser = argparse.ArgumentParser(description="POC: visual table region detection vs existing 02B regions.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH))
    args = parser.parse_args()

    report_path, stats, asset_df = probe_visual_regions(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        report_path=Path(args.report_path),
    )

    print(f"backend_available: {stats['backend_available']}")
    print(f"report_path: {report_path}")
    if not asset_df.empty:
        cols = [
            "asset_package",
            "processed_pages",
            "visual_region_count",
            "new_candidate_count",
            "poc_result",
        ]
        print(asset_df[cols].to_string(index=False))


if __name__ == "__main__":
    main()
