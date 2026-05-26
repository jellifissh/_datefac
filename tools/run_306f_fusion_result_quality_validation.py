from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_306f_fusion_result_quality_validation"

IN_306E_SUMMARY = BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design" / "306e_summary.json"
IN_306E_FUSION = BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design" / "306e_fusion_structured_table.xlsx"
IN_306E_CORE = BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design" / "306e_fusion_core_metric_candidates.xlsx"
IN_306E_DECISION = BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design" / "306e_fusion_source_decision_audit.xlsx"
IN_306E_CONFLICT = BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design" / "306e_fusion_conflict_audit.xlsx"
IN_306E_BLOCKED = BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design" / "306e_fusion_blocked_rows.xlsx"

IN_306D_SUMMARY = BASE_DIR / "output" / "eval_306d_marker_vs_pdfplumber_structured_regression" / "306d_summary.json"
IN_306D_PER_PDF = BASE_DIR / "output" / "eval_306d_marker_vs_pdfplumber_structured_regression" / "306d_per_pdf_comparison.xlsx"
IN_306C_FULL = BASE_DIR / "output" / "eval_306c_marker_panels_to_full_structured_sandbox" / "306c_marker_full_structured_table.xlsx"

OUT_SUMMARY = OUT_DIR / "306f_summary.json"
OUT_REPORT = OUT_DIR / "306f_report.md"
OUT_CORE_AUDIT = OUT_DIR / "306f_core_candidate_quality_audit.xlsx"
OUT_CONFLICT_AUDIT = OUT_DIR / "306f_conflict_reason_audit.xlsx"
OUT_ROUTING_AUDIT = OUT_DIR / "306f_source_routing_audit.xlsx"
OUT_RESCUED_AUDIT = OUT_DIR / "306f_rescued_zero_candidate_pdf_audit.xlsx"
OUT_SUSPICIOUS = OUT_DIR / "306f_suspicious_fusion_rows.xlsx"
OUT_MANUAL = OUT_DIR / "306f_manual_review_samples.xlsx"
OUT_NO_APPLY = OUT_DIR / "306f_no_apply_proof.json"

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

STATEMENT_PANELS = {
    "balance_sheet",
    "income_statement",
    "cash_flow_statement",
    "valuation_metrics",
    "financial_summary",
    "business_assumption",
}

VALID_BLOCK_REASONS = {
    "cross_source_conflict_blocked",
    "marker_blocked_no_pdfplumber_fallback",
    "marker_blocked_only_source",
    "no_source_available",
    "marker_blocked_no_fallback",
}

VALID_ROUTE_REASONS = {
    "default_pdfplumber",
    "multi_panel_or_split_prefer_marker",
    "pdfplumber_zero_candidate_prefer_marker",
    "cross_source_conflict_blocked",
    "only_marker_available",
    "page1_summary_forecast_prefer_marker",
    "marker_dirty_prefer_pdfplumber",
    "marker_blocked_no_pdfplumber_fallback",
    "marker_blocked_prefer_pdfplumber_fallback",
    "marker_blocked_only_source",
    "no_source_available",
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


def _safe_sheet_name(name: str, used: Set[str]) -> str:
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
    used: Set[str] = set()
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


def _contains_multi_number_cell(text: str) -> bool:
    s = _norm(text)
    if s == "":
        return False
    return bool(re.search(r"\d+\s+\d+", s)) or bool(re.search(r"\d+\s+\(\d+\)", s))


def _metric_noisy(text: str) -> bool:
    s = _norm(text)
    if s == "":
        return False
    if len(s) >= 25:
        return True
    if any(ch in s for ch in ["。", "，", ",", ":", "：", ";", "；"]):
        return True
    return False


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_306E_SUMMARY,
        IN_306E_FUSION,
        IN_306E_CORE,
        IN_306E_DECISION,
        IN_306E_CONFLICT,
        IN_306E_BLOCKED,
        IN_306D_SUMMARY,
        IN_306D_PER_PDF,
        IN_306C_FULL,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306F",
                "mode": "fusion_result_quality_validation",
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

    fusion = pd.read_excel(IN_306E_FUSION).fillna("")
    core = pd.read_excel(IN_306E_CORE).fillna("")
    decision = pd.read_excel(IN_306E_DECISION).fillna("")
    conflict = pd.read_excel(IN_306E_CONFLICT).fillna("")
    blocked = pd.read_excel(IN_306E_BLOCKED).fillna("")
    per_pdf_306d = pd.read_excel(IN_306D_PER_PDF).fillna("")
    marker_306c = pd.read_excel(IN_306C_FULL).fillna("")
    sum_306e = json.loads(IN_306E_SUMMARY.read_text(encoding="utf-8"))
    sum_306d = json.loads(IN_306D_SUMMARY.read_text(encoding="utf-8"))

    # Core quality audit.
    core_eval = core.copy()
    if not core_eval.empty:
        core_eval["key"] = (
            core_eval["source_pdf_name"].map(_norm)
            + "|"
            + core_eval["normalized_metric_name"].map(_norm)
            + "|"
            + core_eval["year"].map(lambda x: str(_to_int(x)))
        )
        dup_series = core_eval["key"].value_counts()
        core_eval["duplicate_key_in_core"] = core_eval["key"].map(lambda x: _to_int(dup_series.get(x, 0)) > 1)
        core_eval["numeric_value_parsed"] = core_eval["value_raw"].map(lambda x: _to_float(x) is not None)
        core_eval["missing_value_raw"] = core_eval["value_raw"].map(lambda x: _norm(x) == "")
        core_eval["invalid_core_metric_name"] = core_eval["normalized_metric_name"].map(lambda x: _norm(x) not in CORE_METRICS)
        core_eval["dirty_confidence_flag"] = core_eval["confidence_flags"].map(lambda x: _norm(x) not in {"", "ok", "pdfplumber_selected"})
        core_eval["page1_summary_row"] = (
            core_eval["page_number"].map(_to_int).eq(1)
            & core_eval["panel_label"].map(_norm).isin({"financial_summary", "valuation_metrics"})
        )
        core_eval["multi_panel_row"] = (
            core_eval["source_panel_id"].map(_norm).str.startswith("split|")
            | core_eval["statement_type"].map(_norm).isin({"balance_sheet", "income_statement", "cash_flow_statement", "valuation_metrics"})
        )
        core_eval["suspicious_value_cell"] = core_eval["value_raw"].map(_contains_multi_number_cell)
        core_eval["quality_status"] = "PASS"
        fail_mask = (
            core_eval["missing_value_raw"]
            | core_eval["invalid_core_metric_name"]
            | core_eval["dirty_confidence_flag"]
        )
        warn_mask = (~fail_mask) & (
            core_eval["duplicate_key_in_core"] | (~core_eval["numeric_value_parsed"]) | core_eval["suspicious_value_cell"]
        )
        core_eval.loc[warn_mask, "quality_status"] = "WARN"
        core_eval.loc[fail_mask, "quality_status"] = "FAIL"

    # Conflict reason audit.
    conflict_eval = conflict.copy()
    if not conflict_eval.empty and "conflict_type" in conflict_eval.columns:
        conflict_eval["valid_conflict_type"] = conflict_eval["conflict_type"].map(_norm).eq("value_conflict_same_pdf_metric_year")
        conflict_eval["marker_value_missing"] = conflict_eval["marker_value_raw"].map(lambda x: _norm(x) == "")
        conflict_eval["pdfplumber_value_missing"] = conflict_eval["pdfplumber_value_raw"].map(lambda x: _norm(x) == "")
        conflict_eval["marker_value_non_numeric"] = conflict_eval["marker_value_raw"].map(lambda x: _to_float(x) is None)
        conflict_eval["pdfplumber_value_non_numeric"] = conflict_eval["pdfplumber_value_raw"].map(lambda x: _to_float(x) is None)
        conflict_eval["likely_text_pollution"] = conflict_eval["pdfplumber_value_raw"].map(lambda x: _metric_noisy(x)) | conflict_eval["marker_value_raw"].map(lambda x: _metric_noisy(x))
    else:
        conflict_eval = pd.DataFrame([{"note": "no_conflict_rows"}])

    # Source routing audit.
    routing = decision.copy()
    if not routing.empty:
        routing["route_reason_norm"] = routing["route_reason"].map(_norm)
        routing["selected_source_norm"] = routing["selected_source"].map(_norm)
        routing["route_reason_known"] = routing["route_reason_norm"].isin(VALID_ROUTE_REASONS)
        routing["has_marker_bool"] = routing["has_marker"].map(lambda x: str(x).lower() in {"true", "1"})
        routing["has_pdfplumber_bool"] = routing["has_pdfplumber"].map(lambda x: str(x).lower() in {"true", "1"})
        routing["value_conflict_bool"] = routing["value_conflict"].map(lambda x: str(x).lower() in {"true", "1"})
        routing["marker_dirty_bool"] = routing["marker_dirty"].map(lambda x: str(x).lower() in {"true", "1"})
        routing["routing_inconsistent"] = False

        conflict_mask = routing["value_conflict_bool"]
        routing.loc[conflict_mask, "routing_inconsistent"] = routing.loc[conflict_mask, "route_reason_norm"] != "cross_source_conflict_blocked"

        dirty_pref_mask = routing["marker_dirty_bool"] & routing["has_pdfplumber_bool"] & (~routing["value_conflict_bool"])
        routing.loc[dirty_pref_mask, "routing_inconsistent"] = (
            routing.loc[dirty_pref_mask, "selected_source_norm"] != "pdfplumber"
        ) | (
            routing.loc[dirty_pref_mask, "route_reason_norm"] != "marker_dirty_prefer_pdfplumber"
        )

        unknown_reason_mask = ~routing["route_reason_known"]
        routing.loc[unknown_reason_mask, "routing_inconsistent"] = True
    else:
        routing = pd.DataFrame([{"note": "no_routing_rows"}])

    # Zero-candidate rescued audit.
    per_pdf_306d["pdf_file_name"] = per_pdf_306d["pdf_file_name"].map(_norm)
    per_pdf_306d["pdfplumber_zero_candidate_bool"] = per_pdf_306d["pdfplumber_zero_candidate"].map(lambda x: str(x).lower() in {"true", "1"})
    zero_set = set(per_pdf_306d[per_pdf_306d["pdfplumber_zero_candidate_bool"]]["pdf_file_name"].tolist())

    rescued_rows: List[Dict[str, Any]] = []
    for pdf_name in sorted(zero_set):
        pdf_core = core[core["source_pdf_name"].map(_norm) == pdf_name].copy()
        marker_rows = pdf_core[pdf_core["fusion_selected_source"].map(_norm) == "marker"]
        page1_summary_rows = pdf_core[
            (pdf_core["page_number"].map(_to_int) == 1)
            & (pdf_core["panel_label"].map(_norm).isin({"financial_summary", "valuation_metrics"}))
        ]
        multi_panel_rows = pdf_core[
            pdf_core["source_panel_id"].map(_norm).str.startswith("split|")
            | pdf_core["statement_type"].map(_norm).isin({"balance_sheet", "income_statement", "cash_flow_statement", "valuation_metrics"})
        ]
        rescued_rows.append(
            {
                "pdf_file_name": pdf_name,
                "pdfplumber_zero_candidate": True,
                "fusion_core_row_count": int(len(pdf_core)),
                "marker_selected_core_row_count": int(len(marker_rows)),
                "page1_summary_core_row_count": int(len(page1_summary_rows)),
                "multi_panel_core_row_count": int(len(multi_panel_rows)),
                "rescued_by_fusion": bool(len(pdf_core) > 0),
                "rescued_by_marker": bool(len(marker_rows) > 0),
            }
        )
    rescued_df = pd.DataFrame(rescued_rows)

    # Suspicious fusion rows (non-core + noisy, or malformed key/value).
    suspicious = fusion.copy()
    if not suspicious.empty:
        suspicious["year_int"] = suspicious["year"].map(_to_int)
        suspicious["metric_norm"] = suspicious["normalized_metric_name"].map(_norm)
        suspicious["value_raw_s"] = suspicious["value_raw"].map(_norm)
        suspicious["raw_metric_s"] = suspicious["raw_metric_name"].map(_norm)
        suspicious["confidence_s"] = suspicious["confidence_flags"].map(_norm)
        suspicious["suspicious_reason"] = ""

        m1 = suspicious["metric_norm"].map(lambda x: x == "" or _metric_noisy(x))
        suspicious.loc[m1, "suspicious_reason"] += "|metric_name_noisy_or_empty"

        m2 = suspicious["value_raw_s"].map(_contains_multi_number_cell)
        suspicious.loc[m2, "suspicious_reason"] += "|value_cell_multi_number"

        m3 = suspicious["year_int"].map(lambda y: y < 1990 or y > 2035 or y == 0)
        suspicious.loc[m3, "suspicious_reason"] += "|year_out_of_range"

        m4 = suspicious["raw_metric_s"].eq("") & suspicious["value_raw_s"].ne("")
        suspicious.loc[m4, "suspicious_reason"] += "|empty_metric_with_value"

        m5 = suspicious["confidence_s"].map(lambda x: x not in {"", "ok", "pdfplumber_selected"})
        suspicious.loc[m5, "suspicious_reason"] += "|dirty_confidence_flag"

        suspicious["suspicious_reason"] = suspicious["suspicious_reason"].map(lambda x: _norm(x).lstrip("|"))
        suspicious = suspicious[suspicious["suspicious_reason"].map(_norm) != ""].copy()
    else:
        suspicious = pd.DataFrame([{"note": "no_fusion_rows"}])

    # Manual review sample workbook.
    conflict_sample = conflict_eval.head(40).copy()
    blocked_sample = blocked.head(40).copy()
    suspicious_sample = suspicious.head(80).copy()
    rescued_sample = rescued_df.copy()
    manual_count = int(len(conflict_sample) + len(blocked_sample) + len(suspicious_sample))

    # Output workbooks.
    core_sheet = core_eval if not core_eval.empty else pd.DataFrame([{"note": "no_core_rows"}])
    _write_excel(OUT_CORE_AUDIT, {"core_candidate_quality_audit": core_sheet})

    _write_excel(
        OUT_CONFLICT_AUDIT,
        {
            "conflict_reason_audit": conflict_eval,
            "blocked_dirty_rows": blocked if not blocked.empty else pd.DataFrame([{"note": "no_blocked_rows"}]),
        },
    )

    route_stats = (
        routing.groupby(["route_reason_norm", "selected_source_norm"], dropna=False)
        .size()
        .reset_index(name="count")
        if "route_reason_norm" in routing.columns
        else pd.DataFrame([{"note": "no_route_stats"}])
    )
    _write_excel(
        OUT_ROUTING_AUDIT,
        {
            "source_routing_audit": routing,
            "route_reason_stats": route_stats,
        },
    )
    _write_excel(OUT_RESCUED_AUDIT, {"rescued_zero_candidate_pdf_audit": rescued_df if not rescued_df.empty else pd.DataFrame([{"note": "no_zero_candidate_pdf"}])})
    _write_excel(OUT_SUSPICIOUS, {"suspicious_fusion_rows": suspicious})
    _write_excel(
        OUT_MANUAL,
        {
            "manual_conflict_samples": conflict_sample if not conflict_sample.empty else pd.DataFrame([{"note": "no_conflict_samples"}]),
            "manual_blocked_samples": blocked_sample if not blocked_sample.empty else pd.DataFrame([{"note": "no_blocked_samples"}]),
            "manual_suspicious_samples": suspicious_sample if not suspicious_sample.empty else pd.DataFrame([{"note": "no_suspicious_samples"}]),
            "manual_rescued_pdf_samples": rescued_sample if not rescued_sample.empty else pd.DataFrame([{"note": "no_rescued_samples"}]),
        },
    )

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

    core_pass = int((core_eval["quality_status"] == "PASS").sum()) if not core_eval.empty else 0
    core_warn = int((core_eval["quality_status"] == "WARN").sum()) if not core_eval.empty else 0
    core_fail = int((core_eval["quality_status"] == "FAIL").sum()) if not core_eval.empty else 0

    valid_conflicts = int(conflict_eval["valid_conflict_type"].sum()) if "valid_conflict_type" in conflict_eval.columns else 0
    valid_block_reasons = int(blocked["block_reason"].map(_norm).isin(VALID_BLOCK_REASONS).sum()) if "block_reason" in blocked.columns else 0
    routing_inconsistent_count = int(routing["routing_inconsistent"].sum()) if "routing_inconsistent" in routing.columns else 0

    page1_summary_core_row_count = int(
        (
            (core["page_number"].map(_to_int) == 1)
            & (core["panel_label"].map(_norm).isin({"financial_summary", "valuation_metrics"}))
        ).sum()
    ) if not core.empty else 0
    multi_panel_core_row_count = int(
        (
            core["source_panel_id"].map(_norm).str.startswith("split|")
            | core["statement_type"].map(_norm).isin({"balance_sheet", "income_statement", "cash_flow_statement", "valuation_metrics"})
        ).sum()
    ) if not core.empty else 0
    rescued_count = int(rescued_df["rescued_by_fusion"].sum()) if not rescued_df.empty else 0

    summary = {
        "stage": "EVAL-306F",
        "mode": "fusion_result_quality_validation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval_306e_summary_loaded": True,
        "eval_306d_summary_loaded": True,
        "eval_306c_table_loaded": True,
        "input_pdf_count": int(_to_int(sum_306d.get("pdf_count", 0))),
        "fusion_row_count": int(len(fusion)),
        "fusion_core_candidate_count": int(len(core)),
        "core_candidate_pass_count": core_pass,
        "core_candidate_warn_count": core_warn,
        "core_candidate_fail_count": core_fail,
        "conflict_row_count": int(len(conflict)),
        "valid_conflict_reason_count": valid_conflicts,
        "blocked_row_count": int(len(blocked)),
        "valid_block_reason_count": valid_block_reasons,
        "routing_decision_row_count": int(len(decision)),
        "routing_inconsistent_count": routing_inconsistent_count,
        "pdfplumber_zero_candidate_pdf_count_from_306d": int(_to_int(sum_306d.get("pdfplumber_zero_candidate_pdf_count", 0))),
        "rescued_zero_candidate_pdf_count": rescued_count,
        "page1_summary_core_row_count": page1_summary_core_row_count,
        "multi_panel_core_row_count": multi_panel_core_row_count,
        "suspicious_fusion_row_count": int(len(suspicious)),
        "manual_review_sample_count": manual_count,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "ready_for_downstream_candidate_stage": bool(
            delivery_status == "PASS"
            and not production_files_modified
            and not official_02b_modified
            and not formal_rules_modified
            and not standardizer_modified
            and not release_package_modified
            and core_fail == 0
        ),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306F Fusion Result Quality Validation",
        "",
        f"- fusion_row_count: {summary['fusion_row_count']}",
        f"- fusion_core_candidate_count: {summary['fusion_core_candidate_count']}",
        f"- core_candidate_pass/warn/fail: {summary['core_candidate_pass_count']}/{summary['core_candidate_warn_count']}/{summary['core_candidate_fail_count']}",
        f"- conflict_row_count: {summary['conflict_row_count']}",
        f"- blocked_row_count: {summary['blocked_row_count']}",
        f"- routing_inconsistent_count: {summary['routing_inconsistent_count']}",
        f"- zero_candidate_rescued: {summary['rescued_zero_candidate_pdf_count']}/{summary['pdfplumber_zero_candidate_pdf_count_from_306d']}",
        f"- page1_summary_core_row_count: {summary['page1_summary_core_row_count']}",
        f"- multi_panel_core_row_count: {summary['multi_panel_core_row_count']}",
        f"- suspicious_fusion_row_count: {summary['suspicious_fusion_row_count']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306f_summary_json: {OUT_SUMMARY}")
    print(f"eval_306f_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
