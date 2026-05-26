from __future__ import annotations

import hashlib
import json
import re
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
OUT_DIR = BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design"

IN_306D_SUMMARY = BASE_DIR / "output" / "eval_306d_marker_vs_pdfplumber_structured_regression" / "306d_summary.json"
IN_306D_PER_PDF = BASE_DIR / "output" / "eval_306d_marker_vs_pdfplumber_structured_regression" / "306d_per_pdf_comparison.xlsx"
IN_306C_FULL = BASE_DIR / "output" / "eval_306c_marker_panels_to_full_structured_sandbox" / "306c_marker_full_structured_table.xlsx"
IN_1B_FULL = BASE_DIR / "output" / "eval1b_profile_selection_fix_regression" / "302_eval1b_full_structured_table.xlsx"
IN_1B_PER_PDF = BASE_DIR / "output" / "eval1b_profile_selection_fix_regression" / "302_eval1b_per_pdf_metrics.xlsx"

OUT_SUMMARY = OUT_DIR / "306e_summary.json"
OUT_REPORT = OUT_DIR / "306e_report.md"
OUT_FUSION = OUT_DIR / "306e_fusion_structured_table.xlsx"
OUT_CORE = OUT_DIR / "306e_fusion_core_metric_candidates.xlsx"
OUT_DECISION = OUT_DIR / "306e_fusion_source_decision_audit.xlsx"
OUT_CONFLICT = OUT_DIR / "306e_fusion_conflict_audit.xlsx"
OUT_BLOCKED = OUT_DIR / "306e_fusion_blocked_rows.xlsx"
OUT_POLICY = OUT_DIR / "306e_parser_routing_policy.json"
OUT_NO_APPLY = OUT_DIR / "306e_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

CORE_METRICS = {
    "revenue",
    "net_profit",
    "attributable_net_profit",
    "total_assets",
    "total_liabilities",
    "operating_cash_flow",
    "eps",
    "roe",
    "gross_margin",
    "pe",
    "pb",
    "ev_ebitda",
}

BLOCK_MARKER_FLAGS = {"merged_value_cell", "suspicious_year", "polluted_metric_name"}

PDFP_CORE_NAME_MAP = {
    "营业收入": "revenue",
    "净利润": "net_profit",
    "归属于母公司净利润": "attributable_net_profit",
    "归母净利润": "attributable_net_profit",
    "资产总计": "total_assets",
    "负债合计": "total_liabilities",
    "经营活动现金流": "operating_cash_flow",
    "经营现金流": "operating_cash_flow",
    "每股收益": "eps",
    "roe": "roe",
    "净资产收益率": "roe",
    "毛利率": "gross_margin",
    "市盈率": "pe",
    "p/e": "pe",
    "市净率": "pb",
    "p/b": "pb",
    "ev/ebitda": "ev_ebitda",
}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def _to_int(v: Any) -> int:
    s = _norm(v)
    if s == "":
        return 0
    try:
        return int(float(s))
    except Exception:
        return 0


def _to_float(v: Any) -> Optional[float]:
    s = _norm(v)
    if s == "":
        return None
    s = s.replace(",", "")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_sheet_name(name: str, used: set) -> str:
    s = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
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
    used: set = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def _extract_year(year_val: Any) -> int:
    s = _norm(year_val)
    if s == "":
        return 0
    m = re.search(r"(19|20)\d{2}", s)
    if not m:
        return 0
    return int(m.group(0))


def _canonical_metric_marker(row: pd.Series) -> str:
    nm = _norm(row.get("normalized_metric_name", "")).lower()
    return nm if nm else _norm(row.get("raw_metric_name", "")).lower()


def _canonical_metric_pdfp(row: pd.Series) -> str:
    merged = " ".join(
        [
            _norm(row.get("standard_metric", "")),
            _norm(row.get("normalized_metric_name", "")),
            _norm(row.get("raw_metric_name", "")),
        ]
    ).lower()
    for k, v in PDFP_CORE_NAME_MAP.items():
        if k.lower() in merged:
            return v
    nm = _norm(row.get("normalized_metric_name", "")).lower()
    return nm if nm else _norm(row.get("raw_metric_name", "")).lower()


def _clean_value_text(v: Any) -> str:
    s = _norm(v)
    return s.replace(",", "").replace(" ", "")


def _value_conflict(a: Any, b: Any) -> bool:
    av = _to_float(a)
    bv = _to_float(b)
    if av is not None and bv is not None:
        return abs(av - bv) > 1e-9
    return _clean_value_text(a) != _clean_value_text(b)


def _marker_row_score(r: pd.Series, pdf_zero_set: set) -> int:
    score = 0
    flags = _norm(r.get("confidence_flags", ""))
    is_dirty = flags != "" and flags != "ok"
    if not is_dirty:
        score += 100
    if _to_int(r.get("page_number", 0)) == 1 and _norm(r.get("panel_label", "")) in {"financial_summary", "valuation_metrics"}:
        score += 40
    if _norm(r.get("source_panel_id", "")).startswith("split|"):
        score += 30
    if _norm(r.get("panel_label", "")) in {"balance_sheet", "income_statement", "cash_flow_statement", "valuation_metrics"}:
        score += 20
    if _norm(r.get("source_pdf_name", "")) in pdf_zero_set:
        score += 25
    for bf in BLOCK_MARKER_FLAGS:
        if bf in flags.split("|"):
            score -= 200
    return score


def _pdfp_row_score(r: pd.Series) -> int:
    score = 0
    if _norm(r.get("mapping_status", "")).upper() == "MAPPED":
        score += 25
    if _norm(r.get("needs_manual_review", "")).lower() in {"false", "0", ""}:
        score += 10
    ec = _to_float(r.get("extraction_confidence", ""))
    if ec is not None:
        score += int(ec * 10)
    bc = _to_float(r.get("block_confidence", ""))
    if bc is not None:
        score += int(bc * 5)
    return score


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306D_SUMMARY, IN_306D_PER_PDF, IN_306C_FULL, IN_1B_FULL, IN_1B_PER_PDF]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306E",
                "mode": "parser_fusion_pipeline_design_sandbox",
                "blocked": True,
                "blocked_reason": "missing_required_inputs",
                "missing_input_count": len(missing),
                "missing_input_list": missing,
                "external_api_called": False,
                "llm_api_called": False,
                "ocr_called": False,
                "marker_rerun_executed": False,
                "pdfplumber_rerun_executed": False,
            },
        )
        return 0

    before = _snapshot_guard()

    per_pdf = pd.read_excel(IN_306D_PER_PDF).fillna("")
    marker_full = pd.read_excel(IN_306C_FULL).fillna("")
    pdfp_full = pd.read_excel(IN_1B_FULL).fillna("")
    pdfp_per = pd.read_excel(IN_1B_PER_PDF).fillna("")

    per_pdf["pdf_file_name"] = per_pdf["pdf_file_name"].map(_norm)
    marker_full["source_pdf_name"] = marker_full["source_pdf_name"].map(_norm)
    pdfp_full["source_pdf_name"] = pdfp_full["source_pdf_name"].map(_norm)
    pdfp_per["pdf_file_name"] = pdfp_per["pdf_file_name"].map(_norm)

    marker = marker_full.copy()
    marker["year_norm"] = marker["year"].map(_extract_year)
    marker["metric_norm"] = marker.apply(_canonical_metric_marker, axis=1)
    marker["source"] = "marker"

    pdfp = pdfp_full.copy()
    pdfp["year_norm"] = pdfp["year"].map(_extract_year)
    pdfp["metric_norm"] = pdfp.apply(_canonical_metric_pdfp, axis=1)
    pdfp["source"] = "pdfplumber"

    # restrict to rows with usable keys
    marker = marker[(marker["source_pdf_name"].map(_norm) != "") & (marker["metric_norm"].map(_norm) != "") & (marker["year_norm"].map(_to_int) > 0)].copy()
    pdfp = pdfp[(pdfp["source_pdf_name"].map(_norm) != "") & (pdfp["metric_norm"].map(_norm) != "") & (pdfp["year_norm"].map(_to_int) > 0)].copy()

    pdf_zero_set = set(
        per_pdf[per_pdf["pdfplumber_zero_candidate"].apply(lambda x: str(x).lower() in {"true", "1"})]["pdf_file_name"].tolist()
    )

    # Build key universe.
    marker_keys = set((r["source_pdf_name"], r["metric_norm"], _to_int(r["year_norm"])) for _, r in marker.iterrows())
    pdfp_keys = set((r["source_pdf_name"], r["metric_norm"], _to_int(r["year_norm"])) for _, r in pdfp.iterrows())
    keys = sorted(marker_keys | pdfp_keys)

    fusion_rows: List[Dict[str, Any]] = []
    core_rows: List[Dict[str, Any]] = []
    decision_rows: List[Dict[str, Any]] = []
    conflict_rows: List[Dict[str, Any]] = []
    blocked_rows: List[Dict[str, Any]] = []

    for pdf_name, metric_norm, year_norm in keys:
        mrows = marker[
            (marker["source_pdf_name"] == pdf_name)
            & (marker["metric_norm"] == metric_norm)
            & (marker["year_norm"] == year_norm)
        ].copy()
        prows = pdfp[
            (pdfp["source_pdf_name"] == pdf_name)
            & (pdfp["metric_norm"] == metric_norm)
            & (pdfp["year_norm"] == year_norm)
        ].copy()

        m_best = None
        p_best = None
        if not mrows.empty:
            mrows["score"] = mrows.apply(lambda r: _marker_row_score(r, pdf_zero_set), axis=1)
            m_best = mrows.sort_values("score", ascending=False).iloc[0]
        if not prows.empty:
            prows["score"] = prows.apply(_pdfp_row_score, axis=1)
            p_best = prows.sort_values("score", ascending=False).iloc[0]

        has_marker = m_best is not None
        has_pdfp = p_best is not None

        m_flags = _norm(m_best.get("confidence_flags", "")) if has_marker else ""
        m_flag_set = set([x for x in m_flags.split("|") if x not in {"", "ok"}]) if has_marker else set()
        marker_dirty = has_marker and _norm(m_best.get("confidence_flags", "")) not in {"", "ok"}
        marker_block = bool(m_flag_set & BLOCK_MARKER_FLAGS) if has_marker else False

        conflict = False
        if has_marker and has_pdfp:
            conflict = _value_conflict(m_best.get("value_raw", ""), p_best.get("value_raw", ""))

        selected_source = ""
        route_reason = ""
        selected_row = None

        # hard block on cross-source conflict
        if conflict:
            route_reason = "cross_source_conflict_blocked"
            conflict_rows.append(
                {
                    "source_pdf_name": pdf_name,
                    "metric_norm": metric_norm,
                    "year": year_norm,
                    "marker_value_raw": _norm(m_best.get("value_raw", "")) if has_marker else "",
                    "pdfplumber_value_raw": _norm(p_best.get("value_raw", "")) if has_pdfp else "",
                    "marker_source_panel_id": _norm(m_best.get("source_panel_id", "")) if has_marker else "",
                    "pdfplumber_raw_table_id": _norm(p_best.get("raw_table_id", "")) if has_pdfp else "",
                    "conflict_type": "value_conflict_same_pdf_metric_year",
                }
            )
            blocked_rows.append(
                {
                    "source_pdf_name": pdf_name,
                    "metric_norm": metric_norm,
                    "year": year_norm,
                    "block_reason": route_reason,
                    "marker_value_raw": _norm(m_best.get("value_raw", "")) if has_marker else "",
                    "pdfplumber_value_raw": _norm(p_best.get("value_raw", "")) if has_pdfp else "",
                }
            )
        else:
            if has_marker and marker_dirty and has_pdfp:
                selected_source = "pdfplumber"
                selected_row = p_best
                route_reason = "marker_dirty_prefer_pdfplumber"
            elif has_marker and marker_block and not has_pdfp:
                route_reason = "marker_blocked_no_pdfplumber_fallback"
                blocked_rows.append(
                    {
                        "source_pdf_name": pdf_name,
                        "metric_norm": metric_norm,
                        "year": year_norm,
                        "block_reason": route_reason,
                        "marker_flags": "|".join(sorted(m_flag_set)),
                        "marker_value_raw": _norm(m_best.get("value_raw", "")),
                    }
                )
            elif has_marker and (
                (_to_int(m_best.get("page_number", 0)) == 1 and _norm(m_best.get("panel_label", "")) in {"financial_summary", "valuation_metrics"})
                or _norm(m_best.get("source_panel_id", "")).startswith("split|")
                or _norm(m_best.get("panel_label", "")) in {"balance_sheet", "income_statement", "cash_flow_statement", "valuation_metrics"}
                or pdf_name in pdf_zero_set
            ):
                if marker_block and has_pdfp:
                    selected_source = "pdfplumber"
                    selected_row = p_best
                    route_reason = "marker_blocked_prefer_pdfplumber_fallback"
                else:
                    selected_source = "marker"
                    selected_row = m_best
                    if pdf_name in pdf_zero_set:
                        route_reason = "pdfplumber_zero_candidate_prefer_marker"
                    elif _norm(m_best.get("source_panel_id", "")).startswith("split|") or _norm(m_best.get("panel_label", "")) in {"balance_sheet", "income_statement", "cash_flow_statement", "valuation_metrics"}:
                        route_reason = "multi_panel_or_split_prefer_marker"
                    else:
                        route_reason = "page1_summary_forecast_prefer_marker"
            elif has_pdfp:
                selected_source = "pdfplumber"
                selected_row = p_best
                route_reason = "default_pdfplumber"
            elif has_marker:
                if marker_block:
                    route_reason = "marker_blocked_only_source"
                    blocked_rows.append(
                        {
                            "source_pdf_name": pdf_name,
                            "metric_norm": metric_norm,
                            "year": year_norm,
                            "block_reason": route_reason,
                            "marker_flags": "|".join(sorted(m_flag_set)),
                            "marker_value_raw": _norm(m_best.get("value_raw", "")),
                        }
                    )
                else:
                    selected_source = "marker"
                    selected_row = m_best
                    route_reason = "only_marker_available"
            else:
                route_reason = "no_source_available"
                blocked_rows.append(
                    {
                        "source_pdf_name": pdf_name,
                        "metric_norm": metric_norm,
                        "year": year_norm,
                        "block_reason": route_reason,
                    }
                )

        decision_rows.append(
            {
                "source_pdf_name": pdf_name,
                "metric_norm": metric_norm,
                "year": year_norm,
                "has_marker": has_marker,
                "has_pdfplumber": has_pdfp,
                "marker_dirty": marker_dirty,
                "marker_block_flags": "|".join(sorted(m_flag_set)),
                "value_conflict": conflict,
                "selected_source": selected_source,
                "route_reason": route_reason,
            }
        )

        if selected_row is None:
            continue

        if selected_source == "marker":
            out_row = {
                "source_pdf_name": _norm(selected_row.get("source_pdf_name", "")),
                "page_number": _to_int(selected_row.get("page_number", 0)),
                "panel_label": _norm(selected_row.get("panel_label", "")),
                "statement_type": _norm(selected_row.get("statement_type", "")),
                "raw_metric_name": _norm(selected_row.get("raw_metric_name", "")),
                "normalized_metric_name": metric_norm,
                "year": year_norm,
                "value_raw": _norm(selected_row.get("value_raw", "")),
                "value": selected_row.get("value", ""),
                "inferred_unit": _norm(selected_row.get("inferred_unit", "")),
                "confidence_flags": _norm(selected_row.get("confidence_flags", "")),
                "source_panel_id": _norm(selected_row.get("source_panel_id", "")),
                "fusion_selected_source": "marker",
                "fusion_route_reason": route_reason,
            }
        else:
            out_row = {
                "source_pdf_name": _norm(selected_row.get("source_pdf_name", "")),
                "page_number": _to_int(selected_row.get("page_number", 0)),
                "panel_label": _norm(selected_row.get("statement_type", "")),
                "statement_type": _norm(selected_row.get("statement_type", "")),
                "raw_metric_name": _norm(selected_row.get("raw_metric_name", "")),
                "normalized_metric_name": metric_norm,
                "year": year_norm,
                "value_raw": _norm(selected_row.get("value_raw", "")),
                "value": selected_row.get("value", ""),
                "inferred_unit": _norm(selected_row.get("inferred_unit", "")),
                "confidence_flags": "pdfplumber_selected",
                "source_panel_id": _norm(selected_row.get("raw_table_id", "")),
                "fusion_selected_source": "pdfplumber",
                "fusion_route_reason": route_reason,
            }

        fusion_rows.append(out_row)
        if metric_norm in CORE_METRICS and _norm(out_row["value_raw"]) != "":
            core_rows.append(out_row.copy())

    fusion_df = pd.DataFrame(fusion_rows).fillna("")
    core_df = pd.DataFrame(core_rows).fillna("")
    decision_df = pd.DataFrame(decision_rows).fillna("")
    conflict_df = pd.DataFrame(conflict_rows).fillna("")
    blocked_df = pd.DataFrame(blocked_rows).fillna("")

    _write_excel(OUT_FUSION, {"fusion_structured_table": fusion_df})
    _write_excel(OUT_CORE, {"fusion_core_metric_candidates": core_df})
    _write_excel(OUT_DECISION, {"fusion_source_decision_audit": decision_df})
    _write_excel(OUT_CONFLICT, {"fusion_conflict_audit": conflict_df if not conflict_df.empty else pd.DataFrame([{"note": "no_conflict"}])})
    _write_excel(OUT_BLOCKED, {"fusion_blocked_rows": blocked_df if not blocked_df.empty else pd.DataFrame([{"note": "no_blocked_rows"}])})

    policy_payload = {
        "stage": "EVAL-306E",
        "routing_rules": [
            "prefer_marker_page1_summary_forecast",
            "prefer_marker_multi_panel_and_split_panels",
            "prefer_marker_for_pdfplumber_zero_candidate_pdfs",
            "prefer_pdfplumber_when_marker_dirty",
            "block_marker_rows_with_merged_value_cell_or_suspicious_year_or_polluted_metric_name",
            "block_cross_source_conflicting_values_same_pdf_metric_year",
        ],
        "blocked_marker_flags": sorted(list(BLOCK_MARKER_FLAGS)),
        "core_metrics_set": sorted(list(CORE_METRICS)),
    }
    _write_json(OUT_POLICY, policy_payload)

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "ocr_called": False,
            "marker_rerun_executed": False,
            "pdfplumber_rerun_executed": False,
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

    pdfplumber_zero_candidate_pdf_count = int(
        len(
            set(
                per_pdf[
                    per_pdf["pdfplumber_zero_candidate"].apply(
                        lambda x: str(x).lower() in {"true", "1"}
                    )
                ]["pdf_file_name"].tolist()
            )
        )
    )

    summary = {
        "stage": "EVAL-306E",
        "mode": "parser_fusion_pipeline_design_sandbox",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "fusion_row_count": int(len(fusion_df)),
        "fusion_core_metric_candidate_count": int(len(core_df)),
        "decision_audit_count": int(len(decision_df)),
        "conflict_audit_count": int(len(conflict_df)),
        "blocked_row_count": int(len(blocked_df)),
        "marker_selected_count": int((fusion_df["fusion_selected_source"].map(_norm) == "marker").sum()) if not fusion_df.empty else 0,
        "pdfplumber_selected_count": int((fusion_df["fusion_selected_source"].map(_norm) == "pdfplumber").sum()) if not fusion_df.empty else 0,
        "pdfplumber_zero_candidate_pdf_count": pdfplumber_zero_candidate_pdf_count,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306E Parser Fusion Pipeline Design",
        "",
        f"- fusion_row_count: {summary['fusion_row_count']}",
        f"- fusion_core_metric_candidate_count: {summary['fusion_core_metric_candidate_count']}",
        f"- decision_audit_count: {summary['decision_audit_count']}",
        f"- conflict_audit_count: {summary['conflict_audit_count']}",
        f"- blocked_row_count: {summary['blocked_row_count']}",
        f"- marker_selected_count: {summary['marker_selected_count']}",
        f"- pdfplumber_selected_count: {summary['pdfplumber_selected_count']}",
        f"- pdfplumber_zero_candidate_pdf_count: {summary['pdfplumber_zero_candidate_pdf_count']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306e_summary_json: {OUT_SUMMARY}")
    print(f"eval_306e_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
