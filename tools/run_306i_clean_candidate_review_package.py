from __future__ import annotations

import hashlib
import json
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
OUT_DIR = BASE_DIR / "output" / "eval_306i_clean_candidate_review_package"

IN_306I_SOURCE_SUMMARY = BASE_DIR / "output" / "eval_306h_fix2_alias_recovery_growth_guard" / "306h_fix2_summary.json"
IN_V3 = BASE_DIR / "output" / "eval_306h_fix2_alias_recovery_growth_guard" / "306h_fix2_clean_core_candidates_v3.xlsx"
IN_VALID_RECOVERED = BASE_DIR / "output" / "eval_306h_fix2_alias_recovery_growth_guard" / "306h_fix2_valid_recovered_alias_candidates.xlsx"
IN_UNRESOLVED_FIX2 = BASE_DIR / "output" / "eval_306h_fix2_alias_recovery_growth_guard" / "306h_fix2_unresolved_missing_core_metric_audit.xlsx"

IN_306H_PER_PDF = BASE_DIR / "output" / "eval_306h_clean_candidate_regression" / "306h_per_pdf_clean_candidate_coverage.xlsx"
IN_306H_MISSING = BASE_DIR / "output" / "eval_306h_clean_candidate_regression" / "306h_missing_core_metric_audit.xlsx"
IN_306G_SUSP = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_suspicious_structured_rows.xlsx"

OUT_SUMMARY = OUT_DIR / "306i_summary.json"
OUT_REPORT = OUT_DIR / "306i_report.md"
OUT_PER_PDF = OUT_DIR / "306i_per_pdf_candidate_summary.xlsx"
OUT_REVIEW = OUT_DIR / "306i_clean_core_candidates_review.xlsx"
OUT_MISSING = OUT_DIR / "306i_missing_metric_review.xlsx"
OUT_RESCUED = OUT_DIR / "306i_rescued_zero_candidate_review.xlsx"
OUT_MANUAL = OUT_DIR / "306i_manual_spot_check_package.xlsx"
OUT_NO_APPLY = OUT_DIR / "306i_no_apply_proof.json"

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

CORE_METRIC_ZH = {
    "revenue": "营业收入",
    "net_profit": "净利润",
    "attributable_net_profit": "归母净利润",
    "total_assets": "资产总计",
    "total_liabilities": "负债合计",
    "operating_cash_flow": "经营活动现金流净额",
    "eps": "每股收益",
    "roe": "净资产收益率",
    "gross_margin": "毛利率",
    "pe": "市盈率",
    "pb": "市净率",
    "ev_ebitda": "EV/EBITDA",
}

PARSER_ZH = {
    "marker": "Marker",
    "pdfplumber": "pdfplumber",
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
        IN_306I_SOURCE_SUMMARY,
        IN_V3,
        IN_VALID_RECOVERED,
        IN_UNRESOLVED_FIX2,
        IN_306H_PER_PDF,
        IN_306H_MISSING,
        IN_306G_SUSP,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306I",
                "mode": "clean_candidate_review_package",
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

    s_fix2 = json.loads(IN_306I_SOURCE_SUMMARY.read_text(encoding="utf-8"))
    v3 = pd.read_excel(IN_V3).fillna("")
    valid_recovered = pd.read_excel(IN_VALID_RECOVERED).fillna("")
    unresolved_fix2 = pd.read_excel(IN_UNRESOLVED_FIX2).fillna("")
    per_pdf_306h = pd.read_excel(IN_306H_PER_PDF).fillna("")
    missing_306h = pd.read_excel(IN_306H_MISSING).fillna("")
    suspicious_306g = pd.read_excel(IN_306G_SUSP).fillna("")

    v3["source_pdf_name"] = v3["source_pdf_name"].map(_norm)
    v3["metric_norm"] = v3["normalized_metric_name"].map(_norm).str.lower()
    v3["is_alias_recovered"] = v3["alias_recovery_applied"].map(lambda x: str(x).lower() in {"true", "1"})
    v3["parser"] = v3["fusion_selected_source"].map(_norm).str.lower()

    per_pdf_306h["pdf_file_name"] = per_pdf_306h["pdf_file_name"].map(_norm)
    per_pdf_306h["pdfplumber_zero_candidate_pdf"] = per_pdf_306h["pdfplumber_zero_candidate_pdf"].map(
        lambda x: str(x).lower() in {"true", "1"}
    )
    per_pdf_306h["rescued_zero_candidate_pdf"] = per_pdf_306h["rescued_zero_candidate_pdf"].map(
        lambda x: str(x).lower() in {"true", "1"}
    )
    zero_map = {
        _norm(r["pdf_file_name"]): {
            "is_zero": bool(r["pdfplumber_zero_candidate_pdf"]),
            "is_rescued": bool(r["rescued_zero_candidate_pdf"]),
        }
        for _, r in per_pdf_306h.iterrows()
    }

    # 1) Clean core review table with Chinese-readable columns.
    review_rows: List[Dict[str, Any]] = []
    for _, r in v3.iterrows():
        pdf = _norm(r["source_pdf_name"])
        z = zero_map.get(pdf, {"is_zero": False, "is_rescued": False})
        metric = _norm(r["metric_norm"])
        review_rows.append(
            {
                "PDF文件名": pdf,
                "页码": _to_int(r.get("page_number", 0)),
                "指标名": _norm(r.get("raw_metric_name", "")),
                "标准指标": metric,
                "标准指标中文": CORE_METRIC_ZH.get(metric, ""),
                "年份": _to_int(r.get("year", 0)),
                "数值": _norm(r.get("value_raw", "")),
                "单位": _norm(r.get("inferred_unit", "")),
                "来源解析器": PARSER_ZH.get(_norm(r.get("parser", "")), _norm(r.get("parser", ""))),
                "来源原因": _norm(r.get("fusion_route_reason", "")),
                "是否别名恢复": bool(r.get("is_alias_recovered", False)),
                "是否zero-candidate救回": bool(z["is_zero"] and z["is_rescued"]),
                "source_bucket": _norm(r.get("source_bucket", "")),
                "source_panel_id": _norm(r.get("source_panel_id", "")),
                "row_uid": _norm(r.get("row_uid", "")),
            }
        )
    review_df = pd.DataFrame(review_rows).fillna("")

    # 2) Per-pdf summary based on v3 only.
    pdfs = sorted(review_df["PDF文件名"].unique().tolist())
    per_pdf_rows: List[Dict[str, Any]] = []
    for pdf in pdfs:
        sub = review_df[review_df["PDF文件名"] == pdf]
        metric_set = set(sub["标准指标"].tolist())
        z = zero_map.get(pdf, {"is_zero": False, "is_rescued": False})
        per_pdf_rows.append(
            {
                "PDF文件名": pdf,
                "clean_core候选数": int(len(sub)),
                "覆盖标准指标数": int(len(metric_set)),
                "指标覆盖率": round(len(metric_set) / len(CORE_METRICS), 4),
                "别名恢复行数": int(sub["是否别名恢复"].sum()),
                "Marker行数": int((sub["来源解析器"] == "Marker").sum()),
                "pdfplumber行数": int((sub["来源解析器"] == "pdfplumber").sum()),
                "page1行数": int((sub["页码"] == 1).sum()),
                "是否zero-candidate原始缺失": bool(z["is_zero"]),
                "是否zero-candidate救回": bool(z["is_zero"] and z["is_rescued"]),
            }
        )
    per_pdf_df = pd.DataFrame(per_pdf_rows).fillna("")

    # 3) Missing metric review from v3 coverage.
    missing_rows: List[Dict[str, Any]] = []
    for pdf in pdfs:
        sub = review_df[review_df["PDF文件名"] == pdf]
        have = set(sub["标准指标"].tolist())
        for m in CORE_METRICS:
            if m in have:
                continue
            unresolved_reason = ""
            unresolved_status = ""
            if "status" in unresolved_fix2.columns:
                hit = unresolved_fix2[
                    (unresolved_fix2["pdf_file_name"].map(_norm) == pdf)
                    & (unresolved_fix2["core_metric"].map(_norm).str.lower() == m)
                ]
                if not hit.empty:
                    unresolved_status = _norm(hit.iloc[0].get("status", ""))
                    unresolved_reason = _norm(hit.iloc[0].get("unresolved_reason", ""))
            missing_rows.append(
                {
                    "PDF文件名": pdf,
                    "缺失标准指标": m,
                    "缺失标准指标中文": CORE_METRIC_ZH.get(m, ""),
                    "fix2状态": unresolved_status,
                    "未解决原因": unresolved_reason,
                }
            )
    missing_df = pd.DataFrame(missing_rows).fillna("")
    if missing_df.empty:
        missing_df = pd.DataFrame([{"提示": "无缺失指标"}])

    # 4) Rescued zero-candidate review.
    rescued_rows: List[Dict[str, Any]] = []
    for _, r in per_pdf_df.iterrows():
        if not bool(r["是否zero-candidate原始缺失"]):
            continue
        rescued_rows.append(
            {
                "PDF文件名": _norm(r["PDF文件名"]),
                "是否zero-candidate原始缺失": bool(r["是否zero-candidate原始缺失"]),
                "是否zero-candidate救回": bool(r["是否zero-candidate救回"]),
                "v3候选数": _to_int(r["clean_core候选数"]),
                "覆盖标准指标数": _to_int(r["覆盖标准指标数"]),
                "别名恢复行数": _to_int(r["别名恢复行数"]),
            }
        )
    rescued_df = pd.DataFrame(rescued_rows).fillna("")
    if rescued_df.empty:
        rescued_df = pd.DataFrame([{"提示": "无zero-candidate样本"}])

    # 5) Manual spot check package.
    sample_alias = review_df[review_df["是否别名恢复"] == True].head(80)
    if sample_alias.empty:
        sample_alias = pd.DataFrame([{"提示": "无别名恢复样本"}])
    sample_marker = review_df[review_df["来源解析器"] == "Marker"].head(80)
    sample_pdfp = review_df[review_df["来源解析器"] == "pdfplumber"].head(80)
    sample_missing = missing_df.head(80)
    # suspicious reference for same PDFs as contextual review aid
    susp_ref = suspicious_306g[suspicious_306g["source_pdf_name"].map(_norm).isin(pdfs)].head(120).copy()
    if susp_ref.empty:
        susp_ref = pd.DataFrame([{"提示": "无可参考的可疑结构行"}])

    _write_excel(OUT_PER_PDF, {"per_pdf_candidate_summary": per_pdf_df})
    _write_excel(OUT_REVIEW, {"clean_core_candidates_review": review_df})
    _write_excel(OUT_MISSING, {"missing_metric_review": missing_df})
    _write_excel(OUT_RESCUED, {"rescued_zero_candidate_review": rescued_df})
    _write_excel(
        OUT_MANUAL,
        {
            "alias_recovered_samples": sample_alias,
            "marker_samples": sample_marker if not sample_marker.empty else pd.DataFrame([{"提示": "无Marker样本"}]),
            "pdfplumber_samples": sample_pdfp if not sample_pdfp.empty else pd.DataFrame([{"提示": "无pdfplumber样本"}]),
            "missing_metric_samples": sample_missing,
            "suspicious_reference": susp_ref,
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

    summary = {
        "stage": "EVAL-306I",
        "mode": "clean_candidate_review_package",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "source_clean_core_candidates_v3_row_count": int(len(review_df)),
        "source_pdf_count": int(len(pdfs)),
        "alias_recovered_row_count": int(review_df["是否别名恢复"].sum()),
        "zero_candidate_rescued_pdf_count": int(rescued_df.shape[0] if "提示" not in rescued_df.columns else 0),
        "missing_metric_row_count": int(0 if "提示" in missing_df.columns else len(missing_df)),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306I Clean Candidate Review Package",
        "",
        f"- source_clean_core_candidates_v3_row_count: {summary['source_clean_core_candidates_v3_row_count']}",
        f"- source_pdf_count: {summary['source_pdf_count']}",
        f"- alias_recovered_row_count: {summary['alias_recovered_row_count']}",
        f"- zero_candidate_rescued_pdf_count: {summary['zero_candidate_rescued_pdf_count']}",
        f"- missing_metric_row_count: {summary['missing_metric_row_count']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306i_summary_json: {OUT_SUMMARY}")
    print(f"eval_306i_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
