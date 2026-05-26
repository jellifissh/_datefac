import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
INPUT_DIR = BASE_DIR / "input"
EVAL1B_DIR = BASE_DIR / "output" / "eval1b_profile_selection_fix_regression"
EVAL_IMG1_DIR = BASE_DIR / "output" / "eval_img1_visual_table_layout_audit"
OUT_DIR = BASE_DIR / "output" / "eval_marker1_no_llm_parser_benchmark"

IN_EVAL1B_SUMMARY = EVAL1B_DIR / "302_eval1b_profile_selection_fix_summary.json"
IN_EVAL1B_PER_PDF = EVAL1B_DIR / "302_eval1b_per_pdf_metrics.xlsx"
IN_EVAL1B_FULL = EVAL1B_DIR / "302_eval1b_full_structured_table.xlsx"
IN_EVAL1B_CLASSIFIED = EVAL1B_DIR / "302_eval1b_classified_structured_table.xlsx"
IN_EVAL1B_CANDIDATE = EVAL1B_DIR / "302_eval1b_core_metrics_candidate_preview.xlsx"
IN_EVAL_IMG1_SUMMARY = EVAL_IMG1_DIR / "303_eval_img1_visual_table_layout_summary.json"
IN_EVAL_IMG1_COVERAGE = EVAL_IMG1_DIR / "303_eval_img1_visual_vs_raw_page_coverage.xlsx"
IN_EVAL_IMG1_MULTI = EVAL_IMG1_DIR / "303_eval_img1_multi_panel_visual_audit.xlsx"
IN_EVAL_IMG1_SAMPLE = EVAL_IMG1_DIR / "303_eval_img1_known_sample_pdf_visual_audit.xlsx"

OUT_SUMMARY = OUT_DIR / "304_eval_marker1_no_llm_benchmark_summary.json"
OUT_REPORT = OUT_DIR / "304_eval_marker1_no_llm_benchmark_report.md"
OUT_MARKER_AVAIL = OUT_DIR / "304_eval_marker1_marker_availability.json"
OUT_PER_PDF = OUT_DIR / "304_eval_marker1_per_pdf_benchmark.xlsx"
OUT_TABLE_INV = OUT_DIR / "304_eval_marker1_marker_table_inventory.xlsx"
OUT_KEYWORDS = OUT_DIR / "304_eval_marker1_financial_keyword_hits.xlsx"
OUT_CMP = OUT_DIR / "304_eval_marker1_pdfplumber_vs_marker_comparison.xlsx"
OUT_SAMPLE_CMP = OUT_DIR / "304_eval_marker1_sample_pdf_comparison.xlsx"
OUT_STRATEGY = OUT_DIR / "304_eval_marker1_parser_strategy_recommendation.json"
OUT_NO_APPLY = OUT_DIR / "304_eval_marker1_no_apply_proof.json"

MARKER_INPUT_DIR = OUT_DIR / "marker_input_batch"
MARKER_OUTPUTS_DIR = OUT_DIR / "marker_outputs"

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

KNOWN_SAMPLE = "0b4b955b8219ffd0bc5a277fab5b8b6c.pdf"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FINANCIAL_KEYWORDS = [
    "盈利预测和财务指标",
    "财务预测",
    "营业收入",
    "净利润",
    "归母净利润",
    "每股收益",
    "EPS",
    "ROE",
    "毛利率",
    "PE",
    "P/E",
    "PB",
    "P/B",
    "EV/EBITDA",
    "资产负债表",
    "利润表",
    "现金流量表",
    "经营活动现金流",
    "资产总计",
    "负债合计",
]
CORE_METRIC_KEYWORDS = [
    "营业收入",
    "净利润",
    "归母净利润",
    "每股收益",
    "EPS",
    "ROE",
    "毛利率",
    "PE",
    "P/E",
    "PB",
    "P/B",
    "EV/EBITDA",
]
MULTI_PANEL_HINTS = ["资产负债表", "利润表", "现金流量表", "关键财务", "财务预测", "估值"]
YEAR_RE = re.compile(r"\b20\d{2}(?:E|A)?\b", flags=re.IGNORECASE)


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def _strip_html(html: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", _norm(html))
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def _extract_table_shape(html: str) -> Tuple[int, int]:
    h = _norm(html)
    if not h:
        return 0, 0
    rows = re.findall(r"<tr\b", h, flags=re.IGNORECASE)
    row_count = len(rows)
    max_cols = 0
    for row_html in re.findall(r"<tr\b.*?</tr>", h, flags=re.IGNORECASE | re.DOTALL):
        col_cnt = len(re.findall(r"<t[dh]\b", row_html, flags=re.IGNORECASE))
        max_cols = max(max_cols, col_cnt)
    return row_count, max_cols


def _find_json_for_pdf(pdf_stem: str, marker_out_root: Path) -> Optional[Path]:
    p = marker_out_root / pdf_stem / f"{pdf_stem}.json"
    if p.exists():
        return p
    cands = list((marker_out_root / pdf_stem).glob("*.json")) if (marker_out_root / pdf_stem).exists() else []
    cands = [x for x in cands if not x.name.endswith("_meta.json")]
    if cands:
        return sorted(cands)[0]
    cands2 = [x for x in marker_out_root.rglob("*.json") if x.name == f"{pdf_stem}.json"]
    return sorted(cands2)[0] if cands2 else None


def _find_meta_for_pdf(pdf_stem: str, marker_out_root: Path) -> Optional[Path]:
    p = marker_out_root / pdf_stem / f"{pdf_stem}_meta.json"
    if p.exists():
        return p
    cands = list((marker_out_root / pdf_stem).glob("*_meta.json")) if (marker_out_root / pdf_stem).exists() else []
    if cands:
        return sorted(cands)[0]
    return None


def _walk_blocks(node: Dict[str, Any], page_ctx: Optional[int], rows: List[Dict[str, Any]]) -> None:
    node_id = _norm(node.get("id"))
    page_num = page_ctx
    m = re.search(r"/page/(\d+)/", node_id)
    if m:
        page_num = int(m.group(1)) + 1

    block_type = _norm(node.get("block_type"))
    if block_type in {"Table", "TableGroup"}:
        html = _norm(node.get("html"))
        txt = _strip_html(html)
        row_count, col_count = _extract_table_shape(html)
        has_json_cells = False
        children = node.get("children", [])
        if isinstance(children, list):
            for c in children:
                if isinstance(c, dict) and _norm(c.get("block_type")) == "TableCell":
                    has_json_cells = True
                    break
        bbox = node.get("bbox")
        has_bbox = isinstance(bbox, list) and len(bbox) == 4

        keyword_hits = [k for k in FINANCIAL_KEYWORDS if k in txt]
        core_hits = [k for k in CORE_METRIC_KEYWORDS if k in txt]
        year_headers = YEAR_RE.findall(txt)
        multi_hint_count = sum(1 for k in MULTI_PANEL_HINTS if k in txt)
        suspected_multi_panel = bool(
            multi_hint_count >= 2
            or (col_count >= 10 and len(set(year_headers)) >= 4)
            or (row_count >= 25 and col_count >= 8)
            or block_type == "TableGroup"
        )

        rows.append(
            {
                "page_number": page_num or 0,
                "marker_table_id": node_id,
                "block_type": block_type,
                "table_text_preview": txt[:300],
                "row_count": int(row_count),
                "col_count": int(col_count),
                "has_markdown_table": "<table" in html.lower(),
                "has_json_cells": has_json_cells,
                "has_bbox": has_bbox,
                "contains_financial_keywords": len(keyword_hits) > 0,
                "contains_year_headers": len(set(year_headers)) > 0,
                "contains_core_metric_keywords": len(core_hits) > 0,
                "suspected_multi_panel": suspected_multi_panel,
                "financial_keyword_hits": "|".join(keyword_hits),
                "core_keyword_hits": "|".join(core_hits),
                "parser_notes": "",
            }
        )

    for ch in node.get("children", []) or []:
        if isinstance(ch, dict):
            _walk_blocks(ch, page_num, rows)


def _blocked_summary(reason: str, marker_avail_payload: Dict[str, Any]) -> int:
    summary = {
        "stage": "EVAL-MARKER-1",
        "mode": "marker_no_llm_parser_benchmark",
        "blocked": True,
        "blocked_reason": reason,
        "external_api_called": False,
        "llm_api_called": False,
        "marker_llm_mode_enabled": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "marker_available": False,
        "ready_for_eval_marker1_parser_benchmark": False,
    }
    _write_json(OUT_SUMMARY, summary)
    _write_json(OUT_MARKER_AVAIL, marker_avail_payload)
    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "marker_llm_mode_enabled": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "production_apply_attempt_count": 0,
        },
    )
    OUT_REPORT.write_text(f"# EVAL-MARKER-1 BLOCKED\n\n- blocked_reason: {reason}\n", encoding="utf-8")
    print(f"eval_marker1_status=blocked_{reason}")
    return 0


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Input list correction note: this stage follows EVAL-1B source-of-truth list.
    source_of_truth_pdf_list = [p.name for p in EXPECTED_PDFS]

    required_inputs = [
        IN_EVAL1B_SUMMARY,
        IN_EVAL1B_PER_PDF,
        IN_EVAL1B_FULL,
        IN_EVAL1B_CLASSIFIED,
        IN_EVAL1B_CANDIDATE,
        IN_EVAL_IMG1_SUMMARY,
        IN_EVAL_IMG1_COVERAGE,
        IN_EVAL_IMG1_MULTI,
        IN_EVAL_IMG1_SAMPLE,
    ]
    missing_inputs = [str(p) for p in required_inputs if not p.exists()]
    if missing_inputs:
        return _blocked_summary(
            "missing_required_inputs",
            {
                "marker_available": False,
                "marker_version": "",
                "missing_input_count": len(missing_inputs),
                "missing_input_list": missing_inputs,
            },
        )

    missing_pdfs = [str(p) for p in EXPECTED_PDFS if not p.exists()]
    if missing_pdfs:
        return _blocked_summary(
            "missing_expected_pdf",
            {
                "marker_available": False,
                "marker_version": "",
                "missing_pdf_count": len(missing_pdfs),
                "missing_pdf_list": missing_pdfs,
            },
        )

    marker_spec = importlib.util.find_spec("marker")
    marker_importable = marker_spec is not None
    marker_cli_path = shutil.which("marker") or ""
    marker_cli_available = marker_cli_path != ""
    marker_available = bool(marker_importable and marker_cli_available)

    marker_version = ""
    if marker_available:
        try:
            import importlib.metadata as im

            marker_version = im.version("marker-pdf")
        except Exception:
            marker_version = ""

    marker_avail_payload = {
        "marker_available": marker_available,
        "marker_importable": marker_importable,
        "marker_cli_available": marker_cli_available,
        "marker_cli_path": marker_cli_path,
        "marker_version": marker_version,
    }
    _write_json(OUT_MARKER_AVAIL, marker_avail_payload)

    if not marker_available:
        return _blocked_summary("marker_not_available", marker_avail_payload)

    eval1b_summary = json.loads(IN_EVAL1B_SUMMARY.read_text(encoding="utf-8"))
    eval_img1_summary = json.loads(IN_EVAL_IMG1_SUMMARY.read_text(encoding="utf-8"))
    per_pdf_df = pd.read_excel(IN_EVAL1B_PER_PDF).fillna("")
    coverage_df = pd.read_excel(IN_EVAL_IMG1_COVERAGE).fillna("")

    pdfplumber_map = {_norm(r.get("pdf_file_name")): r for _, r in per_pdf_df.iterrows()}
    eval_img1_multi_count: Dict[str, int] = {}
    if not coverage_df.empty:
        mm = coverage_df[coverage_df["suspected_multi_panel_visual_layout"] == True]
        if not mm.empty:
            g = mm.groupby("pdf_file_name", dropna=False).size().reset_index(name="cnt")
            for _, r in g.iterrows():
                eval_img1_multi_count[_norm(r.get("pdf_file_name"))] = int(r.get("cnt", 0))

    before = _snapshot_guard()

    # Prepare input batch and output folder.
    if MARKER_INPUT_DIR.exists():
        shutil.rmtree(MARKER_INPUT_DIR)
    MARKER_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    MARKER_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    for pdf in EXPECTED_PDFS:
        shutil.copy2(pdf, MARKER_INPUT_DIR / pdf.name)

    # Run marker locally, no LLM mode.
    marker_cmd = [
        "marker",
        str(MARKER_INPUT_DIR),
        "--output_dir",
        str(MARKER_OUTPUTS_DIR),
        "--output_format",
        "json",
        "--disable_ocr",
        "--disable_multiprocessing",
        "--skip_existing",
        "--max_files",
        "10",
    ]
    env = os.environ.copy()
    env["HF_HUB_OFFLINE"] = "1"
    env["TRANSFORMERS_OFFLINE"] = "1"
    run = subprocess.run(marker_cmd, check=False, env=env)
    marker_run_attempted = True

    per_pdf_benchmark_rows: List[Dict[str, Any]] = []
    table_inventory_rows: List[Dict[str, Any]] = []
    keyword_hit_rows: List[Dict[str, Any]] = []
    comparison_rows: List[Dict[str, Any]] = []

    marker_run_success_count = 0
    marker_run_failed_count = 0
    marker_pdf_with_core_metric_keyword_count = 0
    marker_total_table_like_count = 0
    marker_total_financial_table_like_count = 0
    marker_better_candidate_pdf_count = 0
    pdfplumber_better_candidate_pdf_count = 0

    for pdf in EXPECTED_PDFS:
        pdf_name = pdf.name
        stem = pdf.stem
        json_path = _find_json_for_pdf(stem, MARKER_OUTPUTS_DIR)
        meta_path = _find_meta_for_pdf(stem, MARKER_OUTPUTS_DIR)

        marker_ok = bool(json_path and json_path.exists())
        if marker_ok:
            marker_run_success_count += 1
        else:
            marker_run_failed_count += 1

        page_stats = []
        toc_titles: List[str] = []
        if meta_path and meta_path.exists():
            try:
                meta_obj = json.loads(meta_path.read_text(encoding="utf-8"))
                page_stats = meta_obj.get("page_stats", []) or []
                toc_titles = [str(x.get("title", "")) for x in (meta_obj.get("table_of_contents", []) or [])]
            except Exception:
                pass

        table_rows_one: List[Dict[str, Any]] = []
        all_text_chunks: List[str] = []
        if marker_ok and json_path:
            try:
                doc = json.loads(json_path.read_text(encoding="utf-8"))
                _walk_blocks(doc, None, table_rows_one)
            except Exception:
                table_rows_one = []

        for r in table_rows_one:
            r["pdf_file_name"] = pdf_name
            table_inventory_rows.append(r)

        for r in table_rows_one:
            t = _norm(r.get("table_text_preview"))
            all_text_chunks.append(t)
        all_text_chunks.extend([_norm(x) for x in toc_titles if _norm(x)])
        all_text = " ".join(all_text_chunks)

        keyword_hits = [k for k in FINANCIAL_KEYWORDS if k in all_text]
        core_hits = [k for k in CORE_METRIC_KEYWORDS if k in all_text]
        has_core_keywords = len(core_hits) > 0
        if has_core_keywords:
            marker_pdf_with_core_metric_keyword_count += 1

        marker_table_like_count = len(table_rows_one)
        marker_financial_table_like_count = int(sum(1 for r in table_rows_one if bool(r.get("contains_financial_keywords", False))))
        marker_core_metric_keyword_hit_count = len(core_hits)
        marker_multi_panel_signal_count = int(sum(1 for r in table_rows_one if bool(r.get("suspected_multi_panel", False))))
        marker_total_table_like_count += marker_table_like_count
        marker_total_financial_table_like_count += marker_financial_table_like_count

        pdfp = pdfplumber_map.get(pdf_name, {})
        pdfplumber_raw_table_count = int(pdfp.get("raw_table_count", 0) or 0)
        pdfplumber_full_rows = int(pdfp.get("full_structured_row_count", 0) or 0)
        pdfplumber_core_count = int(pdfp.get("core_metrics_candidate_count", 0) or 0)
        pdfplumber_zero_candidate = pdfplumber_core_count == 0
        multi_page_count = int(eval_img1_multi_count.get(pdf_name, 0))

        marker_better_for_complex_layout_candidate = bool(
            marker_ok
            and marker_table_like_count > 0
            and (
                (multi_page_count > 0 and marker_multi_panel_signal_count > 0 and marker_financial_table_like_count > 0)
                or (pdfplumber_zero_candidate and marker_core_metric_keyword_hit_count >= 3)
            )
        )
        pdfplumber_better_candidate = bool(
            pdfplumber_core_count > 0 and (marker_core_metric_keyword_hit_count == 0 or marker_table_like_count == 0)
        )
        if marker_better_for_complex_layout_candidate:
            marker_better_candidate_pdf_count += 1
        if pdfplumber_better_candidate:
            pdfplumber_better_candidate_pdf_count += 1

        for kw in keyword_hits:
            keyword_hit_rows.append(
                {
                    "pdf_file_name": pdf_name,
                    "keyword": kw,
                    "hit": True,
                }
            )

        per_pdf_benchmark_rows.append(
            {
                "pdf_file_name": pdf_name,
                "marker_output_json_path": str(json_path) if json_path else "",
                "marker_output_meta_path": str(meta_path) if meta_path else "",
                "marker_run_success": marker_ok,
                "marker_table_like_count": marker_table_like_count,
                "marker_financial_table_like_count": marker_financial_table_like_count,
                "marker_core_metric_keyword_hit_count": marker_core_metric_keyword_hit_count,
                "marker_has_core_metric_keywords": has_core_keywords,
                "marker_multi_panel_signal_count": marker_multi_panel_signal_count,
                "marker_page_count_from_meta": len(page_stats),
                "marker_keyword_hits": "|".join(keyword_hits),
                "source_of_truth_pdf_list_used": "|".join(source_of_truth_pdf_list),
            }
        )

        comparison_rows.append(
            {
                "pdf_file_name": pdf_name,
                "pdfplumber_raw_table_count": pdfplumber_raw_table_count,
                "marker_table_like_count": marker_table_like_count,
                "pdfplumber_full_structured_row_count": pdfplumber_full_rows,
                "marker_financial_table_like_count": marker_financial_table_like_count,
                "pdfplumber_core_metrics_candidate_count": pdfplumber_core_count,
                "marker_core_metric_keyword_hit_count": marker_core_metric_keyword_hit_count,
                "pdfplumber_zero_candidate": pdfplumber_zero_candidate,
                "marker_has_core_metric_keywords": has_core_keywords,
                "eval_img1_multi_panel_page_count": multi_page_count,
                "marker_multi_panel_signal_count": marker_multi_panel_signal_count,
                "marker_better_for_complex_layout_candidate": marker_better_for_complex_layout_candidate,
                "notes": "",
            }
        )

    per_pdf_benchmark_df = pd.DataFrame(per_pdf_benchmark_rows).fillna("")
    table_inventory_df = pd.DataFrame(table_inventory_rows).fillna("")
    keyword_hits_df = pd.DataFrame(keyword_hit_rows).fillna("")
    comparison_df = pd.DataFrame(comparison_rows).fillna("")

    # Sample PDF focused comparison
    sample_cmp_rows: List[Dict[str, Any]] = []
    sample_tables = table_inventory_df[table_inventory_df["pdf_file_name"] == KNOWN_SAMPLE].copy() if not table_inventory_df.empty else pd.DataFrame()
    sample_text = " ".join(sample_tables.get("table_text_preview", pd.Series([], dtype=str)).astype(str).tolist())
    sample_page1 = sample_tables[sample_tables["page_number"] == 1] if not sample_tables.empty else pd.DataFrame()
    sample_page4 = sample_tables[sample_tables["page_number"] == 4] if not sample_tables.empty else pd.DataFrame()

    sample_page1_detects_summary = bool(
        not sample_page1.empty and any(x in sample_text for x in ["盈利预测和财务指标", "财务预测", "营业收入", "净利润"])
    )
    sample_contains_core_set = {k: (k in sample_text) for k in ["营业收入", "净利润", "每股收益", "ROE", "PE", "PB", "EV/EBITDA"]}
    sample_page4_multi_panel_signal = bool(
        (not sample_page4.empty and int((sample_page4["suspected_multi_panel"] == True).sum()) > 0)
        or ("资产负债表" in sample_text and "利润表" in sample_text and "现金流量表" in sample_text)
    )

    sample_pdfp = comparison_df[comparison_df["pdf_file_name"] == KNOWN_SAMPLE]
    sample_pdfp_zero_candidate = bool(sample_pdfp.iloc[0]["pdfplumber_zero_candidate"]) if not sample_pdfp.empty else True
    sample_marker_core_hits = int(sample_pdfp.iloc[0]["marker_core_metric_keyword_hit_count"]) if not sample_pdfp.empty else 0

    sample_marker_easier_to_convert = bool(
        not sample_tables.empty
        and int((sample_tables["contains_year_headers"] == True).sum()) > 0
        and int((sample_tables["contains_core_metric_keywords"] == True).sum()) > 0
    )

    if sample_marker_core_hits >= 4 and sample_pdfp_zero_candidate:
        sample_strategy = "use_marker_fallback"
    elif sample_marker_core_hits >= 4 and not sample_pdfp_zero_candidate:
        sample_strategy = "use_parser_fusion"
    elif sample_marker_core_hits == 0 and not sample_pdfp_zero_candidate:
        sample_strategy = "keep_pdfplumber"
    else:
        sample_strategy = "needs_manual_inspection"

    sample_cmp_rows.append({"pdf_file_name": KNOWN_SAMPLE, "check_item": "marker_detects_page1_summary_forecast_financial_content", "result": sample_page1_detects_summary})
    for k, v in sample_contains_core_set.items():
        sample_cmp_rows.append({"pdf_file_name": KNOWN_SAMPLE, "check_item": f"marker_contains_{k}", "result": bool(v)})
    sample_cmp_rows.append({"pdf_file_name": KNOWN_SAMPLE, "check_item": "marker_page4_multi_panel_better_than_pdfplumber", "result": sample_page4_multi_panel_signal})
    sample_cmp_rows.append({"pdf_file_name": KNOWN_SAMPLE, "check_item": "marker_easier_to_convert_to_full_structured_table", "result": sample_marker_easier_to_convert})
    sample_cmp_rows.append({"pdf_file_name": KNOWN_SAMPLE, "check_item": "recommended_parser_strategy", "result": sample_strategy})
    sample_df = pd.DataFrame(sample_cmp_rows).fillna("")

    parser_fusion_recommended = bool(
        marker_better_candidate_pdf_count > 0 and (pdfplumber_better_candidate_pdf_count > 0 or int(eval1b_summary.get("new_pdf_success_count", 0) or 0) > 0)
    )
    strategy_payload = {
        "sample_pdf": KNOWN_SAMPLE,
        "sample_pdf_recommended_strategy": sample_strategy,
        "marker_better_candidate_pdf_count": marker_better_candidate_pdf_count,
        "pdfplumber_better_candidate_pdf_count": pdfplumber_better_candidate_pdf_count,
        "parser_fusion_recommended": parser_fusion_recommended,
        "source_of_truth_pdf_list_used": source_of_truth_pdf_list,
    }
    _write_json(OUT_STRATEGY, strategy_payload)

    _write_excel(OUT_PER_PDF, {"per_pdf_benchmark": per_pdf_benchmark_df})
    _write_excel(OUT_TABLE_INV, {"marker_table_inventory": table_inventory_df})
    _write_excel(OUT_KEYWORDS, {"financial_keyword_hits": keyword_hits_df})
    _write_excel(OUT_CMP, {"pdfplumber_vs_marker_comparison": comparison_df})
    _write_excel(OUT_SAMPLE_CMP, {"sample_pdf_comparison": sample_df})

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "marker_llm_mode_enabled": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "production_apply_attempt_count": 0,
        },
    )

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    ready_for_eval_parser_fusion_design = bool(
        marker_available
        and marker_run_success_count > 0
        and not comparison_df.empty
        and delivery_status == "PASS"
    )
    ready_for_eval1c = bool(
        delivery_status == "PASS"
        and not production_files_modified
        and not official_02b_modified
        and not formal_rules_modified
        and not standardizer_modified
        and not release_package_modified
    )

    summary = {
        "stage": "EVAL-MARKER-1",
        "mode": "marker_no_llm_parser_benchmark",
        "external_api_called": False,
        "llm_api_called": False,
        "marker_llm_mode_enabled": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval1b_summary_loaded": bool(_norm(eval1b_summary.get("stage")) == "EVAL-1B"),
        "eval_img1_summary_loaded": bool(_norm(eval_img1_summary.get("stage")) == "EVAL-IMG-1"),
        "input_pdf_count": 10,
        "marker_available": marker_available,
        "marker_version": marker_version,
        "marker_run_attempted": marker_run_attempted,
        "marker_run_success_count": marker_run_success_count,
        "marker_run_failed_count": marker_run_failed_count,
        "marker_table_inventory_generated": not table_inventory_df.empty,
        "marker_financial_keyword_hits_generated": True,
        "pdfplumber_vs_marker_comparison_generated": not comparison_df.empty,
        "sample_pdf_comparison_generated": not sample_df.empty,
        "parser_strategy_recommendation_generated": True,
        "marker_pdf_with_core_metric_keyword_count": marker_pdf_with_core_metric_keyword_count,
        "marker_total_table_like_count": int(marker_total_table_like_count),
        "marker_total_financial_table_like_count": int(marker_total_financial_table_like_count),
        "pdfplumber_total_core_candidate_count_from_eval1b": int(eval1b_summary.get("new_core_metrics_candidate_total_rows", 0) or 0),
        "pdfplumber_zero_candidate_pdf_count_from_eval1b": int(eval1b_summary.get("new_zero_candidate_pdf_count", 0) or 0),
        "marker_better_candidate_pdf_count": int(marker_better_candidate_pdf_count),
        "pdfplumber_better_candidate_pdf_count": int(pdfplumber_better_candidate_pdf_count),
        "parser_fusion_recommended": parser_fusion_recommended,
        "extraction_logic_modified": False,
        "candidate_rules_modified": False,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "ready_for_eval_parser_fusion_design": ready_for_eval_parser_fusion_design,
        "ready_for_eval1c_fragmented_table_merge_fix": ready_for_eval1c,
        "source_of_truth_pdf_list_used": source_of_truth_pdf_list,
        "marker_cmd_returncode": int(run.returncode),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# EVAL-MARKER-1 No-LLM Parser Benchmark",
        "",
        "## Run",
        f"- marker_available: {marker_available}",
        f"- marker_version: {marker_version}",
        f"- marker_run_attempted: {marker_run_attempted}",
        f"- marker_run_success_count: {marker_run_success_count}",
        f"- marker_run_failed_count: {marker_run_failed_count}",
        "",
        "## Comparison",
        f"- marker_total_table_like_count: {marker_total_table_like_count}",
        f"- marker_total_financial_table_like_count: {marker_total_financial_table_like_count}",
        f"- marker_pdf_with_core_metric_keyword_count: {marker_pdf_with_core_metric_keyword_count}",
        f"- pdfplumber_total_core_candidate_count_from_eval1b: {summary['pdfplumber_total_core_candidate_count_from_eval1b']}",
        f"- pdfplumber_zero_candidate_pdf_count_from_eval1b: {summary['pdfplumber_zero_candidate_pdf_count_from_eval1b']}",
        f"- marker_better_candidate_pdf_count: {marker_better_candidate_pdf_count}",
        f"- pdfplumber_better_candidate_pdf_count: {pdfplumber_better_candidate_pdf_count}",
        f"- parser_fusion_recommended: {parser_fusion_recommended}",
        "",
        "## Sample PDF",
        f"- sample_pdf: {KNOWN_SAMPLE}",
        f"- sample_strategy: {sample_strategy}",
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

    print(f"eval_marker1_summary_json: {OUT_SUMMARY}")
    print(f"eval_marker1_report_md: {OUT_REPORT}")
    print(f"eval_marker1_ready_for_eval_parser_fusion_design: {ready_for_eval_parser_fusion_design}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
