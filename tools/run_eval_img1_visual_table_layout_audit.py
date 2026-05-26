import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
INPUT_DIR = BASE_DIR / "input"
EVAL1B_DIR = BASE_DIR / "output" / "eval1b_profile_selection_fix_regression"
OUT_DIR = BASE_DIR / "output" / "eval_img1_visual_table_layout_audit"
PAGE_IMG_DIR = OUT_DIR / "page_images"

IN_EVAL1B_SUMMARY = EVAL1B_DIR / "302_eval1b_profile_selection_fix_summary.json"
IN_EVAL1B_PER_PDF = EVAL1B_DIR / "302_eval1b_per_pdf_metrics.xlsx"
IN_EVAL1B_FULL = EVAL1B_DIR / "302_eval1b_full_structured_table.xlsx"
IN_EVAL1B_CLASSIFIED = EVAL1B_DIR / "302_eval1b_classified_structured_table.xlsx"
IN_EVAL1B_CANDIDATE = EVAL1B_DIR / "302_eval1b_core_metrics_candidate_preview.xlsx"
IN_EVAL1B_PROFILE_CMP = EVAL1B_DIR / "302_eval1b_profile_selection_comparison.xlsx"
IN_RAW_DIR = EVAL1B_DIR / "raw_tables_per_pdf"
IN_BLOCK_DIR = EVAL1B_DIR / "table_blocks_per_pdf"
IN_DEBUG_DIR = EVAL1B_DIR / "debug_per_pdf"

OUT_SUMMARY = OUT_DIR / "303_eval_img1_visual_table_layout_summary.json"
OUT_REPORT = OUT_DIR / "303_eval_img1_visual_table_layout_report.md"
OUT_MANIFEST = OUT_DIR / "303_eval_img1_page_image_manifest.xlsx"
OUT_COVERAGE = OUT_DIR / "303_eval_img1_visual_vs_raw_page_coverage.xlsx"
OUT_VISUAL_AUDIT = OUT_DIR / "303_eval_img1_visual_table_region_audit.xlsx"
OUT_MULTI_PANEL = OUT_DIR / "303_eval_img1_multi_panel_visual_audit.xlsx"
OUT_MISSED = OUT_DIR / "303_eval_img1_missed_visual_table_audit.xlsx"
OUT_SAMPLE = OUT_DIR / "303_eval_img1_known_sample_pdf_visual_audit.xlsx"
OUT_NO_APPLY = OUT_DIR / "303_eval_img1_no_apply_proof.json"

EXPECTED_PDFS = [
    INPUT_DIR / "0b4b955b8219ffd0bc5a277fab5b8b6c.pdf",
    INPUT_DIR / "6a0b9e0769373f552c4348621ad58543.pdf",
    INPUT_DIR / "7ef666d64e743498aa76e6ad4ef70fa1.pdf",
    INPUT_DIR / "6862e6f3995d3dbfbed310b51601fb0a.pdf",
    INPUT_DIR / "H3_AP202604291821755175_1.pdf",
    INPUT_DIR / "H3_AP202605251822844635_1.pdf",
    INPUT_DIR / "H3_AP202605251822845141_1.pdf",
    INPUT_DIR / "H3_AP202605251822853403_1.pdf",
    INPUT_DIR / "H3_AP202605251822859039_1.pdf",
    INPUT_DIR / "H3_AP202605231822706325_1.pdf",
]

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

SUMMARY_TABLE_KEYWORDS = ["盈利预测和财务指标", "财务预测", "营业收入", "净利润", "每股收益", "市盈率", "市净率", "EV/EBITDA"]
MULTI_PANEL_KEYWORDS = ["资产负债表", "利润表", "现金流量表", "关键财务与估值指标"]

KNOWN_SAMPLE = "0b4b955b8219ffd0bc5a277fab5b8b6c.pdf"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _snapshot_guard() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP) if RELEASE_ZIP.exists() else "MISSING"
    return snap


def _run_delivery_check() -> Dict[str, Any]:
    p = subprocess.run(
        [sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "").strip()
    return json.loads(txt) if txt else {"overall_status": "UNKNOWN"}


def _blocked_summary(reason: str, extra: Dict[str, Any]) -> int:
    payload = {
        "stage": "EVAL-IMG-1",
        "mode": "visual_table_layout_audit_only",
        "blocked": True,
        "blocked_reason": reason,
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
    }
    payload.update(extra)
    _write_json(OUT_SUMMARY, payload)
    OUT_REPORT.write_text(f"# EVAL-IMG-1 BLOCKED\n\nReason: {reason}\n", encoding="utf-8")
    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "ocr_called": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "production_apply_attempt_count": 0,
        },
    )
    print(f"eval_img1_status=blocked_{reason}")
    return 0


def _build_raw_page_maps() -> Tuple[Dict[Tuple[str, int], int], Dict[Tuple[str, int], int], Dict[Tuple[str, int], int], Dict[Tuple[str, int], int]]:
    raw_count: Dict[Tuple[str, int], int] = {}
    block_count: Dict[Tuple[str, int], int] = {}
    full_row_count: Dict[Tuple[str, int], int] = {}
    candidate_count: Dict[Tuple[str, int], int] = {}

    for raw_file in sorted(IN_RAW_DIR.glob("*_raw_tables.xlsx")):
        pdf_name = raw_file.name.replace("_raw_tables.xlsx", "") + ".pdf"
        try:
            raw_df = pd.read_excel(raw_file, sheet_name="raw_tables").fillna("")
        except Exception:
            raw_df = pd.DataFrame()
        if not raw_df.empty and "table_id" in raw_df.columns:
            for page in sorted(pd.to_numeric(raw_df.get("page", pd.Series([], dtype=float)), errors="coerce").dropna().astype(int).unique().tolist()):
                mask = pd.to_numeric(raw_df.get("page"), errors="coerce").fillna(-1).astype(int) == int(page)
                cnt = int(raw_df.loc[mask, "table_id"].astype(str).nunique())
                raw_count[(pdf_name, int(page))] = cnt

    for blk_file in sorted(IN_BLOCK_DIR.glob("*_table_blocks.xlsx")):
        pdf_name = blk_file.name.replace("_table_blocks.xlsx", "") + ".pdf"
        try:
            blk_df = pd.read_excel(blk_file, sheet_name="table_blocks").fillna("")
        except Exception:
            blk_df = pd.DataFrame()
        if not blk_df.empty and "page_number" in blk_df.columns:
            s = pd.to_numeric(blk_df["page_number"], errors="coerce").dropna().astype(int).value_counts()
            for page, cnt in s.to_dict().items():
                block_count[(pdf_name, int(page))] = int(cnt)

    try:
        full_df = pd.read_excel(IN_EVAL1B_FULL, sheet_name="full_structured_table").fillna("")
    except Exception:
        full_df = pd.DataFrame()
    if not full_df.empty and "page_number" in full_df.columns and "source_pdf_name" in full_df.columns:
        g = full_df.groupby(["source_pdf_name", "page_number"], dropna=False).size().reset_index(name="cnt")
        for _, r in g.iterrows():
            pdf_name = _norm(r.get("source_pdf_name"))
            page = int(pd.to_numeric(r.get("page_number"), errors="coerce") or 0)
            full_row_count[(pdf_name, page)] = int(r.get("cnt", 0))

    try:
        cand_df = pd.read_excel(IN_EVAL1B_CANDIDATE, sheet_name="core_metrics_candidate_preview").fillna("")
    except Exception:
        cand_df = pd.DataFrame()
    if not cand_df.empty and "page_number" in cand_df.columns and "source_pdf_name" in cand_df.columns:
        g = cand_df.groupby(["source_pdf_name", "page_number"], dropna=False).size().reset_index(name="cnt")
        for _, r in g.iterrows():
            pdf_name = _norm(r.get("source_pdf_name"))
            page = int(pd.to_numeric(r.get("page_number"), errors="coerce") or 0)
            candidate_count[(pdf_name, page)] = int(r.get("cnt", 0))

    return raw_count, block_count, full_row_count, candidate_count


def _detect_regions(image_bgr, cv2, np) -> Dict[str, Any]:
    h, w = image_bgr.shape[:2]
    page_area = float(h * w)
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    bin_inv = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 15)

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(20, w // 30), 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(20, h // 30)))
    h_lines = cv2.morphologyEx(bin_inv, cv2.MORPH_OPEN, h_kernel)
    v_lines = cv2.morphologyEx(bin_inv, cv2.MORPH_OPEN, v_kernel)
    line_map = cv2.bitwise_or(h_lines, v_lines)
    line_map = cv2.dilate(line_map, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(line_map, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    big_regions: List[Tuple[int, int, int, int, float]] = []
    small_regions: List[Tuple[int, int, int, int, float]] = []

    for c in contours:
        x, y, rw, rh = cv2.boundingRect(c)
        area = float(rw * rh)
        if area < max(400.0, page_area * 0.00015):
            continue
        if rw < max(20, int(w * 0.03)) or rh < max(12, int(h * 0.015)):
            continue
        rec = (int(x), int(y), int(rw), int(rh), area)
        if area >= page_area * 0.002 and rw >= w * 0.12 and rh >= h * 0.03:
            big_regions.append(rec)
        else:
            small_regions.append(rec)

    big_regions = sorted(big_regions, key=lambda z: z[4], reverse=True)
    largest = big_regions[0] if big_regions else None
    largest_bbox = ""
    if largest:
        largest_bbox = f"{largest[0]},{largest[1]},{largest[2]},{largest[3]}"

    wide_like = bool(largest and largest[2] >= int(w * 0.72) and largest[3] >= int(h * 0.06))

    # Multi-panel heuristic: >=2 major regions OR one very wide region + strong vertical/horizontal lines.
    multi_panel = False
    if len(big_regions) >= 2:
        multi_panel = True
    elif wide_like:
        v_density = float((v_lines > 0).sum()) / max(1.0, page_area)
        h_density = float((h_lines > 0).sum()) / max(1.0, page_area)
        if v_density > 0.003 and h_density > 0.003:
            multi_panel = True

    # Fragmentation heuristic: many small adjacent regions and/or many one-line structures.
    frag_small_count = len([r for r in small_regions if r[2] >= int(w * 0.10) and r[3] <= int(h * 0.05)])
    fragmented = frag_small_count >= 4

    return {
        "table_region_count": int(len(big_regions)),
        "small_region_count": int(len(small_regions)),
        "largest_table_region_bbox": largest_bbox,
        "has_wide_table_like_region": wide_like,
        "suspected_multi_panel_visual_layout": bool(multi_panel),
        "suspected_fragmented_small_regions": bool(fragmented),
        "frag_small_region_count": int(frag_small_count),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required_inputs = [
        IN_EVAL1B_SUMMARY,
        IN_EVAL1B_PER_PDF,
        IN_EVAL1B_FULL,
        IN_EVAL1B_CLASSIFIED,
        IN_EVAL1B_CANDIDATE,
        IN_EVAL1B_PROFILE_CMP,
        IN_RAW_DIR,
        IN_BLOCK_DIR,
        IN_DEBUG_DIR,
    ]
    missing_inputs = [str(p) for p in required_inputs if not p.exists()]
    if missing_inputs:
        return _blocked_summary("missing_eval1b_inputs", {"missing_input_count": len(missing_inputs), "missing_input_list": missing_inputs})

    missing_pdfs = [str(p) for p in EXPECTED_PDFS if not p.exists()]
    if missing_pdfs:
        return _blocked_summary("missing_expected_pdf", {"missing_pdf_count": len(missing_pdfs), "missing_pdf_list": missing_pdfs})

    # Lightweight dependency checks
    missing_deps: List[str] = []
    try:
        import fitz  # type: ignore
    except Exception:
        fitz = None
        missing_deps.append("fitz")
    try:
        import cv2  # type: ignore
    except Exception:
        cv2 = None
        missing_deps.append("cv2")
    try:
        import numpy as np  # type: ignore
    except Exception:
        np = None
        missing_deps.append("numpy")

    if missing_deps:
        return _blocked_summary("missing_visual_dependency", {"missing_dependency_count": len(missing_deps), "missing_dependency_list": missing_deps})

    eval1b_summary = json.loads(IN_EVAL1B_SUMMARY.read_text(encoding="utf-8"))
    _ = pd.read_excel(IN_EVAL1B_PER_PDF).fillna("")
    _ = pd.read_excel(IN_EVAL1B_FULL, sheet_name="full_structured_table").fillna("")
    _ = pd.read_excel(IN_EVAL1B_CLASSIFIED, sheet_name="classified_structured_table").fillna("")
    _ = pd.read_excel(IN_EVAL1B_CANDIDATE, sheet_name="core_metrics_candidate_preview").fillna("")
    _ = pd.read_excel(IN_EVAL1B_PROFILE_CMP).fillna("")

    raw_map, block_map, full_row_map, candidate_map = _build_raw_page_maps()

    before = _snapshot_guard()
    PAGE_IMG_DIR.mkdir(parents=True, exist_ok=True)

    manifest_rows: List[Dict[str, Any]] = []
    visual_rows: List[Dict[str, Any]] = []
    coverage_rows: List[Dict[str, Any]] = []

    rendered_pdf_set = set()

    for pdf_path in EXPECTED_PDFS:
        pdf_name = pdf_path.name
        pdf_stem = pdf_path.stem
        pdf_img_dir = PAGE_IMG_DIR / pdf_stem
        pdf_img_dir.mkdir(parents=True, exist_ok=True)

        try:
            doc = fitz.open(str(pdf_path))
        except Exception as exc:
            manifest_rows.append(
                {
                    "pdf_file_name": pdf_name,
                    "page_number": "",
                    "image_path": "",
                    "image_width": "",
                    "image_height": "",
                    "render_status": "FAILED",
                    "error_message": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        for i in range(doc.page_count):
            page_no = i + 1
            out_img = pdf_img_dir / f"page_{page_no:03d}.png"
            try:
                page = doc.load_page(i)
                mat = fitz.Matrix(150 / 72.0, 150 / 72.0)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                pix.save(str(out_img))

                arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if pix.n == 4:
                    image_bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:
                    image_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                else:
                    image_bgr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)

                det = _detect_regions(image_bgr, cv2=cv2, np=np)
                text_meta = _norm(page.get_text("text"))
                summary_kw_hit = any(k in text_meta for k in SUMMARY_TABLE_KEYWORDS)
                multi_kw_hit = any(k in text_meta for k in MULTI_PANEL_KEYWORDS)

                manifest_rows.append(
                    {
                        "pdf_file_name": pdf_name,
                        "page_number": page_no,
                        "image_path": str(out_img),
                        "image_width": int(pix.width),
                        "image_height": int(pix.height),
                        "render_status": "SUCCESS",
                        "error_message": "",
                    }
                )

                visual_rows.append(
                    {
                        "pdf_file_name": pdf_name,
                        "page_number": page_no,
                        "table_region_count": int(det["table_region_count"]),
                        "small_region_count": int(det["small_region_count"]),
                        "largest_table_region_bbox": _norm(det["largest_table_region_bbox"]),
                        "visual_table_region_detected": bool(det["table_region_count"] > 0),
                        "has_wide_table_like_region": bool(det["has_wide_table_like_region"]),
                        "suspected_multi_panel_visual_layout": bool(det["suspected_multi_panel_visual_layout"] or multi_kw_hit),
                        "suspected_fragmented_visual_layout": bool(det["suspected_fragmented_small_regions"]),
                        "frag_small_region_count": int(det["frag_small_region_count"]),
                        "summary_keyword_hit": bool(summary_kw_hit),
                        "multi_panel_keyword_hit": bool(multi_kw_hit),
                        "page1_summary_keyword_hint": bool(page_no == 1 and summary_kw_hit),
                    }
                )
                rendered_pdf_set.add(pdf_name)
            except Exception as exc:
                manifest_rows.append(
                    {
                        "pdf_file_name": pdf_name,
                        "page_number": page_no,
                        "image_path": str(out_img),
                        "image_width": "",
                        "image_height": "",
                        "render_status": "FAILED",
                        "error_message": f"{type(exc).__name__}: {exc}",
                    }
                )
        doc.close()

    manifest_df = pd.DataFrame(manifest_rows).fillna("")
    visual_df = pd.DataFrame(visual_rows).fillna("")

    # Build coverage rows from all rendered pages (and any raw-only pages, if any).
    rendered_pages = set(
        (
            _norm(r.get("pdf_file_name")),
            int(pd.to_numeric(r.get("page_number"), errors="coerce") or 0),
        )
        for _, r in manifest_df.iterrows()
        if _norm(r.get("render_status")) == "SUCCESS" and int(pd.to_numeric(r.get("page_number"), errors="coerce") or 0) > 0
    )
    raw_pages = set(raw_map.keys()) | set(block_map.keys()) | set(full_row_map.keys()) | set(candidate_map.keys())
    all_pages = sorted(rendered_pages | raw_pages, key=lambda z: (z[0], z[1]))

    visual_index = {}
    if not visual_df.empty:
        for _, r in visual_df.iterrows():
            k = (_norm(r.get("pdf_file_name")), int(pd.to_numeric(r.get("page_number"), errors="coerce") or 0))
            visual_index[k] = r

    for k in all_pages:
        pdf_name, page_no = k
        vr = visual_index.get(k, {})
        visual_rendered = k in rendered_pages
        visual_table = bool(vr.get("visual_table_region_detected", False)) if isinstance(vr, dict) else bool(vr.get("visual_table_region_detected"))
        raw_cnt = int(raw_map.get(k, 0))
        blk_cnt = int(block_map.get(k, 0))
        full_cnt = int(full_row_map.get(k, 0))
        cand_cnt = int(candidate_map.get(k, 0))
        raw_table_detected = raw_cnt > 0

        suspected_visual_missing_from_raw = bool(visual_rendered and visual_table and not raw_table_detected)
        suspected_raw_without_visual = bool(visual_rendered and raw_table_detected and not visual_table)
        suspected_multi_panel = bool(vr.get("suspected_multi_panel_visual_layout", False)) if isinstance(vr, dict) else bool(vr.get("suspected_multi_panel_visual_layout"))

        coverage_rows.append(
            {
                "pdf_file_name": pdf_name,
                "page_number": page_no,
                "visual_page_rendered": visual_rendered,
                "visual_table_region_detected": visual_table,
                "pdfplumber_raw_table_detected": raw_table_detected,
                "raw_table_count_on_page": raw_cnt,
                "table_block_count_on_page": blk_cnt,
                "full_structured_row_count_on_page": full_cnt,
                "candidate_count_on_page": cand_cnt,
                "suspected_visual_table_missing_from_raw": suspected_visual_missing_from_raw,
                "suspected_raw_table_without_visual_table": suspected_raw_without_visual,
                "suspected_multi_panel_visual_layout": suspected_multi_panel,
                "summary_keyword_hit": bool(vr.get("summary_keyword_hit", False)) if isinstance(vr, dict) else bool(vr.get("summary_keyword_hit")),
                "multi_panel_keyword_hit": bool(vr.get("multi_panel_keyword_hit", False)) if isinstance(vr, dict) else bool(vr.get("multi_panel_keyword_hit")),
            }
        )

    coverage_df = pd.DataFrame(coverage_rows).fillna("")
    multi_panel_df = coverage_df[coverage_df["suspected_multi_panel_visual_layout"] == True].copy() if not coverage_df.empty else pd.DataFrame()
    missed_df = coverage_df[
        (coverage_df["suspected_visual_table_missing_from_raw"] == True)
        | (coverage_df["suspected_raw_table_without_visual_table"] == True)
        | ((coverage_df["page_number"] == 1) & (coverage_df["summary_keyword_hit"] == True))
    ].copy() if not coverage_df.empty else pd.DataFrame()

    # Known sample focused audit
    sample_rows: List[Dict[str, Any]] = []
    sample_pdf = KNOWN_SAMPLE
    sample_cov = coverage_df[coverage_df["pdf_file_name"] == sample_pdf].copy() if not coverage_df.empty else pd.DataFrame()
    page1 = sample_cov[sample_cov["page_number"] == 1]
    page3 = sample_cov[sample_cov["page_number"] == 3]
    page4 = sample_cov[sample_cov["page_number"] == 4]

    page1_rendered = bool(len(page1) > 0 and bool(page1.iloc[0]["visual_page_rendered"]))
    page1_visual = bool(len(page1) > 0 and bool(page1.iloc[0]["visual_table_region_detected"]))
    page1_raw = bool(len(page1) > 0 and bool(page1.iloc[0]["pdfplumber_raw_table_detected"]))
    page3_fragment = False
    page4_multi = False
    if not visual_df.empty:
        v3 = visual_df[(visual_df["pdf_file_name"] == sample_pdf) & (visual_df["page_number"] == 3)]
        v4 = visual_df[(visual_df["pdf_file_name"] == sample_pdf) & (visual_df["page_number"] == 4)]
        if not v3.empty:
            page3_fragment = bool(v3.iloc[0].get("suspected_fragmented_visual_layout", False))
        if not v4.empty:
            page4_multi = bool(v4.iloc[0].get("suspected_multi_panel_visual_layout", False))

    followup = "prioritize_fragment_merge_then_multi_panel_splitter_for_sample_pdf" if (page3_fragment or page4_multi) else "inspect_page_block_mapping_for_sample_pdf"

    sample_rows.extend(
        [
            {"pdf_file_name": sample_pdf, "check_item": "page1_image_rendered", "result": page1_rendered},
            {"pdf_file_name": sample_pdf, "check_item": "page1_visual_table_like_region", "result": page1_visual},
            {"pdf_file_name": sample_pdf, "check_item": "page1_in_eval1b_raw_tables", "result": page1_raw},
            {"pdf_file_name": sample_pdf, "check_item": "page3_fragmented_or_grouped_business_assumption_evidence", "result": page3_fragment},
            {"pdf_file_name": sample_pdf, "check_item": "page4_multi_panel_table_evidence", "result": page4_multi},
            {"pdf_file_name": sample_pdf, "check_item": "recommended_followup_action", "result": followup},
        ]
    )
    sample_df = pd.DataFrame(sample_rows).fillna("")

    _write_excel(OUT_MANIFEST, {"page_image_manifest": manifest_df})
    _write_excel(OUT_COVERAGE, {"visual_vs_raw_page_coverage": coverage_df})
    _write_excel(OUT_VISUAL_AUDIT, {"visual_table_region_audit": visual_df})
    _write_excel(OUT_MULTI_PANEL, {"multi_panel_visual_audit": multi_panel_df})
    _write_excel(OUT_MISSED, {"missed_visual_table_audit": missed_df})
    _write_excel(OUT_SAMPLE, {"known_sample_pdf_visual_audit": sample_df})

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "ocr_called": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "production_apply_attempt_count": 0,
            "note": "EVAL-IMG-1 is visual layout audit only.",
        },
    )

    rendered_page_count = int((manifest_df["render_status"] == "SUCCESS").sum()) if not manifest_df.empty else 0
    render_failed_page_count = int((manifest_df["render_status"] == "FAILED").sum()) if not manifest_df.empty else 0

    suspected_visual_table_missing_from_raw_count = int((coverage_df["suspected_visual_table_missing_from_raw"] == True).sum()) if not coverage_df.empty else 0
    suspected_multi_panel_visual_page_count = int((coverage_df["suspected_multi_panel_visual_layout"] == True).sum()) if not coverage_df.empty else 0
    suspected_fragmented_visual_page_count = int((visual_df["suspected_fragmented_visual_layout"] == True).sum()) if not visual_df.empty else 0

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    ready_for_eval1c = bool(
        delivery_status == "PASS"
        and not production_files_modified
        and not official_02b_modified
        and not formal_rules_modified
        and not standardizer_modified
        and not release_package_modified
    )
    ready_for_marker1 = bool(
        ready_for_eval1c
        and len(rendered_pdf_set) == 10
        and rendered_page_count > 0
    )

    summary = {
        "stage": "EVAL-IMG-1",
        "mode": "visual_table_layout_audit_only",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval1b_summary_loaded": bool(_norm(eval1b_summary.get("stage")) == "EVAL-1B"),
        "input_pdf_count": 10,
        "page_images_generated": bool(rendered_page_count > 0),
        "rendered_pdf_count": int(len(rendered_pdf_set)),
        "rendered_page_count": rendered_page_count,
        "render_failed_page_count": render_failed_page_count,
        "visual_page_manifest_generated": True,
        "visual_vs_raw_coverage_generated": True,
        "visual_table_region_audit_generated": True,
        "missed_visual_table_audit_generated": True,
        "multi_panel_visual_audit_generated": True,
        "known_sample_pdf_visual_audit_generated": True,
        "suspected_visual_table_missing_from_raw_count": suspected_visual_table_missing_from_raw_count,
        "suspected_multi_panel_visual_page_count": suspected_multi_panel_visual_page_count,
        "suspected_fragmented_visual_page_count": suspected_fragmented_visual_page_count,
        "extraction_logic_modified": False,
        "candidate_rules_modified": False,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "ready_for_eval1c_fragmented_table_merge_fix": ready_for_eval1c,
        "ready_for_eval_marker1_parser_benchmark": ready_for_marker1,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# EVAL-IMG-1 Visual Table Layout Audit",
        "",
        "## Render",
        f"- input_pdf_count: 10",
        f"- rendered_pdf_count: {len(rendered_pdf_set)}",
        f"- rendered_page_count: {rendered_page_count}",
        f"- render_failed_page_count: {render_failed_page_count}",
        "",
        "## Cross Coverage",
        f"- suspected_visual_table_missing_from_raw_count: {suspected_visual_table_missing_from_raw_count}",
        f"- suspected_multi_panel_visual_page_count: {suspected_multi_panel_visual_page_count}",
        f"- suspected_fragmented_visual_page_count: {suspected_fragmented_visual_page_count}",
        "",
        "## Known Sample",
        f"- sample_pdf: {KNOWN_SAMPLE}",
        f"- page1_rendered: {page1_rendered}",
        f"- page1_visual_table_like_region: {page1_visual}",
        f"- page1_in_eval1b_raw_tables: {page1_raw}",
        f"- page3_fragment_evidence: {page3_fragment}",
        f"- page4_multi_panel_evidence: {page4_multi}",
        f"- recommended_followup_action: {followup}",
        "",
        "## Safety",
        f"- production_files_modified: {production_files_modified}",
        f"- official_02b_modified: {official_02b_modified}",
        f"- formal_rules_modified: {formal_rules_modified}",
        f"- standardizer_modified: {standardizer_modified}",
        f"- release_package_modified: {release_package_modified}",
        f"- check_delivery_state_overall_status: {delivery_status}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"eval_img1_summary_json: {OUT_SUMMARY}")
    print(f"eval_img1_report_md: {OUT_REPORT}")
    print(f"eval_img1_ready_for_eval1c_fragmented_table_merge_fix: {ready_for_eval1c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
