from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_306h_clean_candidate_regression"

IN_306G_FIX_SUMMARY = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_summary.json"
IN_306G_FIX_CLEAN_CORE = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_clean_core_candidates.xlsx"
IN_306G_FIX_CLEAN_STRUCT = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_clean_structured_rows.xlsx"
IN_306G_FIX_SUSP = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_suspicious_structured_rows.xlsx"

IN_306E_SUMMARY = BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design" / "306e_summary.json"
IN_306F_SUMMARY = BASE_DIR / "output" / "eval_306f_fusion_result_quality_validation" / "306f_summary.json"
IN_306F_RESCUED = BASE_DIR / "output" / "eval_306f_fusion_result_quality_validation" / "306f_rescued_zero_candidate_pdf_audit.xlsx"

OUT_SUMMARY = OUT_DIR / "306h_summary.json"
OUT_REPORT = OUT_DIR / "306h_report.md"
OUT_PER_PDF = OUT_DIR / "306h_per_pdf_clean_candidate_coverage.xlsx"
OUT_CORE_MATRIX = OUT_DIR / "306h_core_metric_matrix.xlsx"
OUT_DUP = OUT_DIR / "306h_duplicate_key_audit.xlsx"
OUT_CONFLICT = OUT_DIR / "306h_value_conflict_audit.xlsx"
OUT_MISSING = OUT_DIR / "306h_missing_core_metric_audit.xlsx"
OUT_SOURCE = OUT_DIR / "306h_source_parser_distribution.xlsx"
OUT_MANUAL = OUT_DIR / "306h_manual_spot_check_samples.xlsx"
OUT_NO_APPLY = OUT_DIR / "306h_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

CORE_METRICS = [
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
]


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


def _canonical_value(v: Any) -> str:
    f = _to_float(v)
    if f is not None:
        return f"{f:.12g}"
    return _norm(v).replace(" ", "").replace(",", "")


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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_306G_FIX_SUMMARY,
        IN_306G_FIX_CLEAN_CORE,
        IN_306G_FIX_CLEAN_STRUCT,
        IN_306G_FIX_SUSP,
        IN_306E_SUMMARY,
        IN_306F_SUMMARY,
        IN_306F_RESCUED,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306H",
                "mode": "clean_candidate_regression_validation",
                "blocked": True,
                "blocked_reason": "missing_required_inputs",
                "missing_input_count": len(missing),
                "missing_input_list": missing,
                "external_api_called": False,
                "llm_api_called": False,
                "ocr_called": False,
            },
        )
        return 0

    before = _snapshot_guard()

    s_306g = json.loads(IN_306G_FIX_SUMMARY.read_text(encoding="utf-8"))
    s_306e = json.loads(IN_306E_SUMMARY.read_text(encoding="utf-8"))
    s_306f = json.loads(IN_306F_SUMMARY.read_text(encoding="utf-8"))

    clean_core = pd.read_excel(IN_306G_FIX_CLEAN_CORE).fillna("")
    clean_struct = pd.read_excel(IN_306G_FIX_CLEAN_STRUCT).fillna("")
    suspicious = pd.read_excel(IN_306G_FIX_SUSP).fillna("")
    rescued = pd.read_excel(IN_306F_RESCUED).fillna("")

    for df, col in [(clean_core, "source_pdf_name"), (clean_struct, "source_pdf_name"), (suspicious, "source_pdf_name")]:
        if col in df.columns:
            df[col] = df[col].map(_norm)

    rescued["pdf_file_name"] = rescued["pdf_file_name"].map(_norm)
    rescued["pdfplumber_zero_candidate"] = rescued["pdfplumber_zero_candidate"].map(lambda x: str(x).lower() in {"true", "1"})
    rescued["rescued_by_fusion"] = rescued["rescued_by_fusion"].map(lambda x: str(x).lower() in {"true", "1"})
    rescued_zero_set = set(rescued[rescued["pdfplumber_zero_candidate"]]["pdf_file_name"].tolist())

    clean_core["metric_norm"] = clean_core["normalized_metric_name"].map(_norm).str.lower()
    clean_core["year_int"] = clean_core["year"].map(_to_int)
    clean_core["value_norm"] = clean_core["value_raw"].map(_canonical_value)
    clean_core["parser_source"] = clean_core["fusion_selected_source"].map(_norm)
    clean_core["is_page1"] = clean_core["page_number"].map(_to_int) == 1
    clean_core["is_multi_panel"] = clean_core["source_panel_id"].map(_norm).str.startswith("split|") | clean_core["panel_label"].map(_norm).isin(
        {"balance_sheet", "income_statement", "cash_flow_statement", "valuation_metrics"}
    )

    pdfs = sorted(set(clean_struct["source_pdf_name"].map(_norm).tolist()) | set(clean_core["source_pdf_name"].map(_norm).tolist()) | rescued_zero_set)

    # Duplicate and conflict audits.
    dup_grp = (
        clean_core.groupby(["source_pdf_name", "metric_norm", "year_int"], dropna=False)
        .agg(
            row_count=("row_uid", "count"),
            unique_value_count=("value_norm", pd.Series.nunique),
            parser_source_count=("parser_source", pd.Series.nunique),
            sample_value_raw=("value_raw", lambda x: " | ".join(sorted(set([_norm(v) for v in x if _norm(v) != ""]))[:3])),
        )
        .reset_index()
    )
    dup_df = dup_grp[dup_grp["row_count"] > 1].copy()
    if dup_df.empty:
        dup_df = pd.DataFrame([{"note": "no_duplicate_pdf_metric_year_keys"}])

    conflict_df = dup_grp[(dup_grp["row_count"] > 1) & (dup_grp["unique_value_count"] > 1)].copy()
    if not conflict_df.empty:
        conflict_df["conflict_type"] = "duplicate_key_value_conflict"
    else:
        conflict_df = pd.DataFrame([{"note": "no_value_conflict_in_duplicate_keys"}])

    dup_key_set: Set[Tuple[str, str, int]] = set()
    if "note" not in dup_df.columns:
        for _, r in dup_df.iterrows():
            dup_key_set.add((_norm(r["source_pdf_name"]), _norm(r["metric_norm"]), _to_int(r["year_int"])))

    conflict_key_set: Set[Tuple[str, str, int]] = set()
    if "note" not in conflict_df.columns:
        for _, r in conflict_df.iterrows():
            conflict_key_set.add((_norm(r["source_pdf_name"]), _norm(r["metric_norm"]), _to_int(r["year_int"])))

    # Per-pdf coverage and matrix.
    coverage_rows: List[Dict[str, Any]] = []
    matrix_rows: List[Dict[str, Any]] = []
    missing_rows: List[Dict[str, Any]] = []
    source_pdf_rows: List[Dict[str, Any]] = []

    for pdf in pdfs:
        sub = clean_core[clean_core["source_pdf_name"] == pdf].copy()
        susp_sub = suspicious[suspicious["source_pdf_name"].map(_norm) == pdf].copy()

        metric_counts = {m: int((sub["metric_norm"] == m).sum()) for m in CORE_METRICS}
        present_metrics = [m for m, c in metric_counts.items() if c > 0]
        missing_metrics = [m for m in CORE_METRICS if metric_counts[m] == 0]

        # duplicates/conflicts count for this pdf
        pdf_dup_count = 0
        pdf_conflict_count = 0
        for k in dup_key_set:
            if k[0] == pdf:
                pdf_dup_count += 1
        for k in conflict_key_set:
            if k[0] == pdf:
                pdf_conflict_count += 1

        marker_count = int((sub["parser_source"] == "marker").sum())
        pdfplumber_count = int((sub["parser_source"] == "pdfplumber").sum())
        page1_count = int(sub["is_page1"].sum())
        multi_panel_count = int(sub["is_multi_panel"].sum())
        suspicious_count = int(len(susp_sub))

        coverage_rows.append(
            {
                "pdf_file_name": pdf,
                "clean_core_candidate_count": int(len(sub)),
                "unique_core_metric_count": int(len(present_metrics)),
                "core_metric_coverage_rate": round(len(present_metrics) / len(CORE_METRICS), 4),
                "year_coverage_count": int(sub["year_int"].nunique()) if len(sub) > 0 else 0,
                "page1_clean_core_count": page1_count,
                "multi_panel_clean_core_count": multi_panel_count,
                "marker_source_count": marker_count,
                "pdfplumber_source_count": pdfplumber_count,
                "duplicate_key_count": pdf_dup_count,
                "value_conflict_count": pdf_conflict_count,
                "missing_core_metric_count": int(len(missing_metrics)),
                "missing_core_metric_list": "|".join(missing_metrics),
                "suspicious_structured_row_count": suspicious_count,
                "pdfplumber_zero_candidate_pdf": bool(pdf in rescued_zero_set),
                "rescued_zero_candidate_pdf": bool(pdf in rescued_zero_set and len(sub) > 0),
            }
        )

        mrow = {"pdf_file_name": pdf}
        for m in CORE_METRICS:
            mrow[f"{m}_count"] = metric_counts[m]
            mrow[f"{m}_present"] = metric_counts[m] > 0
        matrix_rows.append(mrow)

        for m in missing_metrics:
            missing_rows.append({"pdf_file_name": pdf, "missing_core_metric": m})

        source_pdf_rows.append(
            {
                "pdf_file_name": pdf,
                "marker_selected_count": marker_count,
                "pdfplumber_selected_count": pdfplumber_count,
                "total_clean_core_count": int(len(sub)),
                "marker_ratio": round(marker_count / len(sub), 4) if len(sub) > 0 else 0.0,
                "pdfplumber_ratio": round(pdfplumber_count / len(sub), 4) if len(sub) > 0 else 0.0,
            }
        )

    per_pdf_df = pd.DataFrame(coverage_rows).fillna("")
    matrix_df = pd.DataFrame(matrix_rows).fillna("")
    missing_df = pd.DataFrame(missing_rows).fillna("")
    if missing_df.empty:
        missing_df = pd.DataFrame([{"note": "no_missing_core_metric"}])

    # Source parser distribution.
    source_global = (
        clean_core.groupby("parser_source").size().reset_index(name="count")
        if len(clean_core) > 0
        else pd.DataFrame([{"parser_source": "none", "count": 0}])
    )
    if len(clean_core) > 0:
        source_global["ratio"] = source_global["count"] / len(clean_core)
    source_pdf_df = pd.DataFrame(source_pdf_rows).fillna("")

    # Remaining suspicious patterns.
    susp_pattern_df = (
        suspicious.groupby("suspicious_reasons").size().reset_index(name="count")
        if "suspicious_reasons" in suspicious.columns and len(suspicious) > 0
        else pd.DataFrame([{"suspicious_reasons": "none", "count": 0}])
    )
    core_like_in_susp = suspicious[suspicious["normalized_metric_name"].map(_norm).str.lower().isin(CORE_METRICS)].copy()

    # manual samples.
    sample_clean = clean_core.head(80).copy() if len(clean_core) > 0 else pd.DataFrame([{"note": "no_clean_core_rows"}])
    sample_conflict = conflict_df.head(80).copy()
    sample_dup = dup_df.head(80).copy()
    sample_rescued = per_pdf_df[per_pdf_df["pdfplumber_zero_candidate_pdf"] == True].copy()
    if sample_rescued.empty:
        sample_rescued = pd.DataFrame([{"note": "no_rescued_zero_candidate_pdf"}])
    sample_susp = core_like_in_susp.head(80).copy()
    if sample_susp.empty:
        sample_susp = pd.DataFrame([{"note": "no_core_like_rows_in_suspicious"}])

    _write_excel(OUT_PER_PDF, {"per_pdf_clean_candidate_coverage": per_pdf_df})
    _write_excel(
        OUT_CORE_MATRIX,
        {
            "core_metric_matrix": matrix_df,
            "core_metric_matrix_long": pd.melt(
                matrix_df,
                id_vars=["pdf_file_name"],
                value_vars=[c for c in matrix_df.columns if c.endswith("_count")],
                var_name="metric_count_col",
                value_name="metric_count",
            ),
        },
    )
    _write_excel(OUT_DUP, {"duplicate_key_audit": dup_df})
    _write_excel(OUT_CONFLICT, {"value_conflict_audit": conflict_df})
    _write_excel(OUT_MISSING, {"missing_core_metric_audit": missing_df})
    _write_excel(
        OUT_SOURCE,
        {
            "source_parser_distribution_global": source_global,
            "source_parser_distribution_per_pdf": source_pdf_df,
            "remaining_suspicious_patterns": susp_pattern_df,
        },
    )
    _write_excel(
        OUT_MANUAL,
        {
            "sample_clean_core": sample_clean,
            "sample_duplicate_keys": sample_dup,
            "sample_value_conflicts": sample_conflict,
            "sample_rescued_zero_candidate": sample_rescued,
            "sample_core_like_in_suspicious": sample_susp,
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

    rescued_pdf_total = int(len(rescued_zero_set))
    rescued_pdf_with_clean_core = int(
        per_pdf_df[(per_pdf_df["pdfplumber_zero_candidate_pdf"] == True) & (per_pdf_df["clean_core_candidate_count"] > 0)].shape[0]
    )

    summary = {
        "stage": "EVAL-306H",
        "mode": "clean_candidate_regression_validation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval_306g_fix_summary_loaded": True,
        "eval_306e_summary_loaded": True,
        "eval_306f_summary_loaded": True,
        "input_pdf_count": int(len(pdfs)),
        "clean_core_candidate_row_count": int(len(clean_core)),
        "clean_structured_row_count": int(len(clean_struct)),
        "suspicious_structured_row_count": int(len(suspicious)),
        "duplicate_key_count": int(0 if "note" in dup_df.columns else len(dup_df)),
        "value_conflict_count": int(0 if "note" in conflict_df.columns else len(conflict_df)),
        "missing_core_metric_total_count": int(0 if "note" in missing_df.columns else len(missing_df)),
        "pdf_with_missing_core_metric_count": int(
            0 if "note" in missing_df.columns else missing_df["pdf_file_name"].nunique()
        ),
        "rescued_zero_candidate_pdf_total": rescued_pdf_total,
        "rescued_zero_candidate_pdf_with_clean_core": rescued_pdf_with_clean_core,
        "marker_selected_clean_core_count": int((clean_core["parser_source"] == "marker").sum()) if len(clean_core) > 0 else 0,
        "pdfplumber_selected_clean_core_count": int((clean_core["parser_source"] == "pdfplumber").sum()) if len(clean_core) > 0 else 0,
        "remaining_suspicious_pattern_count": int(0 if "count" not in susp_pattern_df.columns else susp_pattern_df["count"].sum()),
        "core_like_rows_in_suspicious_count": int(len(core_like_in_susp)),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "ready_for_downstream_approval_gate": bool(
            delivery_status == "PASS"
            and not production_files_modified
            and not official_02b_modified
            and not formal_rules_modified
            and not standardizer_modified
            and not release_package_modified
            and len(clean_core) > 0
        ),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306H Clean Candidate Regression",
        "",
        f"- input_pdf_count: {summary['input_pdf_count']}",
        f"- clean_core_candidate_row_count: {summary['clean_core_candidate_row_count']}",
        f"- duplicate_key_count: {summary['duplicate_key_count']}",
        f"- value_conflict_count: {summary['value_conflict_count']}",
        f"- missing_core_metric_total_count: {summary['missing_core_metric_total_count']}",
        f"- rescued_zero_candidate_pdf_with_clean_core: {summary['rescued_zero_candidate_pdf_with_clean_core']}/{summary['rescued_zero_candidate_pdf_total']}",
        f"- marker_selected_clean_core_count: {summary['marker_selected_clean_core_count']}",
        f"- pdfplumber_selected_clean_core_count: {summary['pdfplumber_selected_clean_core_count']}",
        f"- core_like_rows_in_suspicious_count: {summary['core_like_rows_in_suspicious_count']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306h_summary_json: {OUT_SUMMARY}")
    print(f"eval_306h_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
