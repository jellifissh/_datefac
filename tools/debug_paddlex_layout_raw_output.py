import argparse
import json
import os
import sys
import traceback
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pypdfium2 as pdfium


DEFAULT_INPUT_DIR = Path(r"D:\_datefac\input")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output")
DEFAULT_STEM = "H3_AP202605141822318031_1"
ASSET_SUFFIX = "_" + "资产包"
DEFAULT_JSON_PATH = Path(r"D:\_datefac\output\debug_paddlex_layout_raw_output.json")
DEFAULT_PAGE_IMG_PATH = Path(r"D:\_datefac\output\debug_paddlex_layout_page.png")


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
    raise ModuleNotFoundError("openpyxl is unavailable for reading 02B index.")


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _to_int(v: Any, default: int = 0) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def _truthy(v: Any) -> bool:
    return _norm(v).lower() in {"1", "true", "yes", "y"}


def _load_02b_index(asset_dir: Path) -> pd.DataFrame:
    _ensure_openpyxl_available()
    path = asset_dir / "02B_table_region_assets" / "table_region_index.xlsx"
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, engine="openpyxl").fillna("")
    except Exception:
        return pd.DataFrame()


def _pick_page(df02b: pd.DataFrame) -> Tuple[int, str]:
    if df02b.empty or "page_number" not in df02b.columns:
        return 1, "fallback_page_1"
    scores = defaultdict(lambda: {"score": 0, "reasons": []})
    for _, r in df02b.iterrows():
        page = _to_int(r.get("page_number"), 0)
        if page <= 0:
            continue
        if _norm(r.get("bbox_status")) != "matched":
            scores[page]["score"] += 60
            scores[page]["reasons"].append("unmatched_bbox")
        if _truthy(r.get("needs_manual_review")):
            scores[page]["score"] += 40
            scores[page]["reasons"].append("needs_manual_review")
        if _norm(r.get("quality_level")).upper() == "BAD":
            scores[page]["score"] += 25
            scores[page]["reasons"].append("bad_quality")
        qf = _norm(r.get("quality_flags"))
        if "single_column" in qf:
            scores[page]["score"] += 18
            scores[page]["reasons"].append("single_column")
        if "possible_glued_table" in qf:
            scores[page]["score"] += 15
            scores[page]["reasons"].append("possible_glued_table")
    if not scores:
        return 1, "fallback_page_1"
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1]["score"], kv[0]))
    best_page, meta = ranked[0]
    reasons = []
    seen = set()
    for x in meta["reasons"]:
        if x not in seen:
            seen.add(x)
            reasons.append(x)
    return best_page, "|".join(reasons) or "highest_risk"


def _render_page_to_png(pdf_path: Path, page_number: int, output_png: Path) -> Dict[str, Any]:
    output_png.parent.mkdir(parents=True, exist_ok=True)
    doc = pdfium.PdfDocument(str(pdf_path))
    page_count = len(doc)
    use_page = max(1, min(page_number, page_count))
    page = doc[use_page - 1]
    bitmap = page.render(scale=2.0)
    image = bitmap.to_pil()
    image.save(output_png)
    return {"page_count": page_count, "rendered_page_number": use_page, "image_size": list(image.size)}


def _safe_json(v: Any, depth: int = 0) -> Any:
    if depth >= 5:
        return repr(v)[:300]
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, dict):
        return {str(k): _safe_json(val, depth + 1) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [_safe_json(x, depth + 1) for x in v[:200]]
    if hasattr(v, "tolist"):
        try:
            return _safe_json(v.tolist(), depth + 1)
        except Exception:
            pass
    if hasattr(v, "json"):
        try:
            j = v.json
            if callable(j):
                j = j()
            return _safe_json(j, depth + 1)
        except Exception:
            pass
    if hasattr(v, "to_dict"):
        try:
            return _safe_json(v.to_dict(), depth + 1)
        except Exception:
            pass
    if hasattr(v, "__dict__"):
        try:
            return _safe_json(vars(v), depth + 1)
        except Exception:
            pass
    return repr(v)[:1000]


def _first_result(result: Any) -> Any:
    if isinstance(result, list):
        return result[0] if result else None
    if hasattr(result, "__iter__") and not isinstance(result, (str, bytes, dict)):
        try:
            return next(iter(result))
        except Exception:
            return None
    return result


def _extract_boxes_with_path(obj: Any, path: str = "$", max_nodes: int = 5000) -> List[Tuple[str, Dict[str, Any]]]:
    stack: List[Tuple[str, Any]] = [(path, obj)]
    out: List[Tuple[str, Dict[str, Any]]] = []
    visited = 0
    while stack and visited < max_nodes:
        cur_path, cur = stack.pop()
        visited += 1
        if isinstance(cur, dict):
            lower_keys = {str(k).lower() for k in cur.keys()}
            if "boxes" in lower_keys:
                for k, v in cur.items():
                    if str(k).lower() == "boxes" and isinstance(v, list):
                        for i, box in enumerate(v):
                            if isinstance(box, dict):
                                out.append((f"{cur_path}.{k}[{i}]", box))
            for k, v in cur.items():
                stack.append((f"{cur_path}.{k}", v))
        elif isinstance(cur, list):
            for i, v in enumerate(cur):
                stack.append((f"{cur_path}[{i}]", v))
    return out


def _bbox_from_region(r: Dict[str, Any]) -> Optional[List[float]]:
    for key in ["bbox", "coordinate"]:
        v = r.get(key)
        if isinstance(v, (list, tuple)) and len(v) >= 4:
            try:
                x0, y0, x1, y1 = float(v[0]), float(v[1]), float(v[2]), float(v[3])
                if x1 > x0 and y1 > y0:
                    return [x0, y0, x1, y1]
            except Exception:
                pass
    poly = r.get("poly")
    if isinstance(poly, (list, tuple)) and len(poly) >= 4:
        pts = []
        for p in poly:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                try:
                    pts.append((float(p[0]), float(p[1])))
                except Exception:
                    continue
        if pts:
            xs = [x for x, _ in pts]
            ys = [y for _, y in pts]
            return [min(xs), min(ys), max(xs), max(ys)]
    return None


def _label_from_region(r: Dict[str, Any]) -> str:
    for key in ["label", "category", "cls", "class_name", "region_type", "type"]:
        if key in r:
            return _norm(r.get(key))
    return ""


def _score_from_region(r: Dict[str, Any]) -> Optional[float]:
    for key in ["score", "confidence"]:
        if key in r:
            try:
                return float(r.get(key))
            except Exception:
                pass
    return None


def _analyze_result(raw_obj: Any) -> Dict[str, Any]:
    serializable = _safe_json(raw_obj)
    top_keys = list(serializable.keys()) if isinstance(serializable, dict) else []
    key_hits = {
        k: (k in top_keys)
        for k in ["boxes", "layout", "result", "res", "objects", "bbox", "label", "cls", "category", "score"]
    }
    region_candidates = []
    if serializable is not None:
        for src_path, reg in _extract_boxes_with_path(serializable):
            bbox = _bbox_from_region(reg)
            label = _label_from_region(reg)
            score = _score_from_region(reg)
            region_candidates.append(
                {
                    "source_path": src_path,
                    "label": label,
                    "score": score,
                    "bbox": bbox,
                    "raw_region": reg,
                }
            )
    counts = Counter([x["label"] for x in region_candidates if x["label"]])
    table_like = [
        x
        for x in region_candidates
        if any(t in _norm(x.get("label")).lower() for t in ["table", "表格", "table_body", "table_region"])
    ]
    return {
        "raw_python_type": type(raw_obj).__name__,
        "top_level_keys": top_keys,
        "key_hits": key_hits,
        "region_count": len(region_candidates),
        "first_5_regions": region_candidates[:5],
        "label_counts": dict(counts),
        "has_table_like_region": len(table_like) > 0,
        "table_like_region_count": len(table_like),
        "table_like_examples": table_like[:5],
        "raw_preview": serializable,
    }


def _run_backend_paddlex_layout_parsing(image_path: Path) -> Dict[str, Any]:
    import paddlex as pdx  # type: ignore

    pipe = pdx.create_pipeline("layout_parsing")
    result = pipe.predict(str(image_path))
    first = _first_result(result)
    return {"backend_name": "paddlex_layout_parsing", "raw_first_result": first}


def _run_backend_paddleocr_layout_detection(image_path: Path) -> Dict[str, Any]:
    from paddleocr import LayoutDetection  # type: ignore

    model = LayoutDetection(model_name="PP-DocLayout-L")
    result = model.predict(str(image_path))
    first = _first_result(result)
    return {"backend_name": "paddleocr_layout_detection", "raw_first_result": first}


def _run_backend_paddleocr_ppstructure(image_path: Path) -> Dict[str, Any]:
    from paddleocr import PPStructureV3  # type: ignore

    model = PPStructureV3()
    result = model.predict(str(image_path))
    first = _first_result(result)
    return {"backend_name": "paddleocr_ppstructurev3", "raw_first_result": first}


def _configure_runtime_env(project_root: Path) -> Dict[str, str]:
    env_updates = {
        "PADDLE_PDX_CACHE_HOME": str(project_root / ".paddlex"),
        "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK": "True",
        "MODELSCOPE_CACHE": str(project_root / ".cache" / "modelscope"),
        "HF_HOME": str(project_root / ".cache" / "huggingface"),
        "AISTUDIO_CACHE_HOME": str(project_root / ".cache" / "aistudio"),
        "TEMP": str(project_root / "temp"),
        "TMP": str(project_root / "temp"),
    }
    for k, v in env_updates.items():
        os.environ.setdefault(k, v)
        Path(os.environ[k]).mkdir(parents=True, exist_ok=True)
    return {k: os.environ.get(k, "") for k in env_updates.keys()}


def run_debug(
    input_dir: Path,
    output_dir: Path,
    asset_stem: str,
    out_json: Path,
    out_png: Path,
) -> Dict[str, Any]:
    runtime_env = _configure_runtime_env(output_dir.parent)

    asset_dir = output_dir / f"{asset_stem}{ASSET_SUFFIX}"
    pdf_path = input_dir / f"{asset_stem}.pdf"

    report: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "asset_stem": asset_stem,
        "asset_dir": str(asset_dir),
        "pdf_path": str(pdf_path),
        "runtime_env": runtime_env,
        "errors": [],
        "backend_attempts": [],
    }

    if not asset_dir.exists():
        report["errors"].append("asset_dir_not_found")
        return report
    if not pdf_path.exists():
        report["errors"].append("pdf_not_found")
        return report

    df02b = _load_02b_index(asset_dir)
    selected_page, page_reason = _pick_page(df02b)
    report["selected_page_number"] = selected_page
    report["selected_page_reason"] = page_reason

    try:
        render_meta = _render_page_to_png(pdf_path, selected_page, out_png)
        report["render_meta"] = render_meta
        report["page_png_path"] = str(out_png)
    except Exception as exc:
        report["errors"].append(f"render_failed: {type(exc).__name__}: {exc}")
        report["traceback"] = traceback.format_exc()
        return report

    runners = [
        _run_backend_paddlex_layout_parsing,
        _run_backend_paddleocr_layout_detection,
        _run_backend_paddleocr_ppstructure,
    ]

    for fn in runners:
        backend_name = fn.__name__.replace("_run_backend_", "")
        rec: Dict[str, Any] = {"backend_name": backend_name, "ok": False, "error": ""}
        try:
            payload = fn(out_png)
            raw_first = payload.get("raw_first_result")
            analysis = _analyze_result(raw_first)
            rec["ok"] = True
            rec["analysis"] = analysis
            if analysis.get("region_count", 0) > 0 and "selected_backend" not in report:
                report["selected_backend"] = payload.get("backend_name", backend_name)
                report["selected_backend_analysis"] = analysis
        except Exception as exc:
            rec["error"] = f"{type(exc).__name__}: {exc}"
            rec["traceback"] = traceback.format_exc(limit=3)
        report["backend_attempts"].append(rec)

    if "selected_backend" not in report:
        report["selected_backend"] = ""
        report["selected_backend_analysis"] = {}

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug raw output format from PaddleX/PaddleOCR layout backends.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--asset-stem", default=DEFAULT_STEM)
    parser.add_argument("--out-json", default=str(DEFAULT_JSON_PATH))
    parser.add_argument("--out-png", default=str(DEFAULT_PAGE_IMG_PATH))
    args = parser.parse_args()

    result = run_debug(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        asset_stem=args.asset_stem,
        out_json=Path(args.out_json),
        out_png=Path(args.out_png),
    )

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"json_path: {out_json}")
    print(f"page_png_path: {args.out_png}")
    print(f"selected_page: {result.get('selected_page_number')} ({result.get('selected_page_reason', '')})")
    for attempt in result.get("backend_attempts", []):
        name = attempt.get("backend_name")
        ok = attempt.get("ok")
        if ok:
            ana = attempt.get("analysis", {})
            print(
                f"backend={name} ok=True region_count={ana.get('region_count', 0)} "
                f"table_like={ana.get('has_table_like_region', False)}"
            )
        else:
            print(f"backend={name} ok=False error={attempt.get('error', '')}")


if __name__ == "__main__":
    main()
