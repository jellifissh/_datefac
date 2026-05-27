from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_307h_final_preview_v2_quality_diagnosis"

IN_FINAL_V2 = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_final_core_metric_preview_v2.xlsx"
IN_REVIEW_V2 = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_review_required_core_metrics_v2.xlsx"
IN_DELTA_G = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_coverage_delta_from_307a.xlsx"
IN_CONFLICT_G = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_conflict_audit.xlsx"
IN_V1_METRIC = BASE_DIR / "output" / "eval_307b_core_metric_export_quality_diagnosis" / "307b_metric_level_coverage.xlsx"
IN_V1_REVIEW_METRIC = BASE_DIR / "output" / "eval_307b_core_metric_export_quality_diagnosis" / "307b_review_burden_by_metric.xlsx"

OUT_SUMMARY = OUT_DIR / "307h_summary.json"
OUT_REPORT = OUT_DIR / "307h_report.md"
OUT_PDF_COV = OUT_DIR / "307h_pdf_level_coverage_v2.xlsx"
OUT_METRIC_COV = OUT_DIR / "307h_metric_level_coverage_v2.xlsx"
OUT_BUCKET = OUT_DIR / "307h_source_bucket_distribution_v2.xlsx"
OUT_REVIEW_BREAK = OUT_DIR / "307h_review_required_breakdown_v2.xlsx"
OUT_REVIEW_PDF = OUT_DIR / "307h_review_burden_by_pdf_v2.xlsx"
OUT_REVIEW_METRIC = OUT_DIR / "307h_review_burden_by_metric_v2.xlsx"
OUT_DELTA = OUT_DIR / "307h_v1_vs_v2_quality_delta.xlsx"
OUT_READY = OUT_DIR / "307h_export_readiness_assessment_v2.xlsx"
OUT_NEXT = OUT_DIR / "307h_next_bottleneck_recommendation.md"
OUT_NO_APPLY = OUT_DIR / "307h_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
TARGET_METRICS = [
    "revenue",
    "attributable_net_profit",
    "gross_margin",
    "roe",
    "eps",
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


def _load_first_sheet(path: Path, preferred: str | None = None) -> pd.DataFrame:
    xls = pd.ExcelFile(path)
    if preferred and preferred in xls.sheet_names:
        return pd.read_excel(path, sheet_name=preferred).fillna("")
    return pd.read_excel(path, sheet_name=xls.sheet_names[0]).fillna("")


def _drop_note_rows(df: pd.DataFrame) -> pd.DataFrame:
    if "note" in df.columns:
        return df[~df["note"].map(_norm).str.startswith("no_")].copy()
    return df.copy()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_FINAL_V2, IN_REVIEW_V2, IN_DELTA_G, IN_CONFLICT_G, IN_V1_METRIC, IN_V1_REVIEW_METRIC]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-307H",
                "mode": "final_preview_v2_quality_diagnosis",
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

    final_v2 = _drop_note_rows(_load_first_sheet(IN_FINAL_V2, "final_core_metric_preview_v2"))
    review_v2 = _drop_note_rows(_load_first_sheet(IN_REVIEW_V2, "review_required_core_metrics_v2"))
    delta_g = _drop_note_rows(_load_first_sheet(IN_DELTA_G, "coverage_delta_from_307a"))
    conflict_g = _drop_note_rows(_load_first_sheet(IN_CONFLICT_G, "conflict_audit"))
    v1_metric = _drop_note_rows(_load_first_sheet(IN_V1_METRIC, "metric_level_coverage"))
    v1_review_metric = _drop_note_rows(_load_first_sheet(IN_V1_REVIEW_METRIC, "review_burden_by_metric"))

    for df in [final_v2, review_v2, v1_metric, v1_review_metric]:
        if "标准指标" in df.columns:
            df["标准指标"] = df["标准指标"].map(_norm).str.lower()
    if "source_bucket" in final_v2.columns:
        final_v2["source_bucket"] = final_v2["source_bucket"].map(_norm)
    if "年份" in final_v2.columns:
        final_v2["年份"] = final_v2["年份"].map(_to_int)
    if "source_parser" in review_v2.columns:
        review_v2["source_parser"] = review_v2["source_parser"].map(_norm)
    if "risk_level" in review_v2.columns:
        review_v2["risk_level"] = review_v2["risk_level"].map(_norm)

    final_v2_row_count = int(len(final_v2))
    review_v2_row_count = int(len(review_v2))

    # coverage views
    pdf_cov_v2 = (
        final_v2.groupby("PDF文件名", dropna=False)
        .agg(
            trusted_row_count=("PDF文件名", "count"),
            trusted_metric_count=("标准指标", "nunique"),
            trusted_year_count=("年份", "nunique"),
            source_bucket_mix=("source_bucket", lambda x: "|".join(sorted(set(x)))),
        )
        .reset_index()
        if not final_v2.empty
        else pd.DataFrame(columns=["PDF文件名", "trusted_row_count", "trusted_metric_count", "trusted_year_count", "source_bucket_mix"])
    )

    metric_cov_v2 = (
        final_v2.groupby("标准指标", dropna=False)
        .agg(
            trusted_row_count=("标准指标", "count"),
            pdf_count=("PDF文件名", "nunique"),
            year_count=("年份", "nunique"),
            source_bucket_mix=("source_bucket", lambda x: "|".join(sorted(set(x)))),
        )
        .reset_index()
        if not final_v2.empty
        else pd.DataFrame(columns=["标准指标", "trusted_row_count", "pdf_count", "year_count", "source_bucket_mix"])
    )
    metric_cov_v2["is_target_core_metric"] = metric_cov_v2["标准指标"].isin(TARGET_METRICS) if not metric_cov_v2.empty else False

    source_bucket_dist_v2 = (
        final_v2.groupby("source_bucket", dropna=False)
        .agg(row_count=("source_bucket", "count"), pdf_count=("PDF文件名", "nunique"), metric_count=("标准指标", "nunique"))
        .reset_index()
        if not final_v2.empty
        else pd.DataFrame(columns=["source_bucket", "row_count", "pdf_count", "metric_count"])
    )

    review_breakdown_v2 = (
        review_v2.groupby(["source_bucket", "risk_level", "source_parser"], dropna=False)
        .agg(row_count=("PDF文件名", "count"), pdf_count=("PDF文件名", "nunique"), metric_count=("标准指标", "nunique"))
        .reset_index()
        if not review_v2.empty
        else pd.DataFrame(columns=["source_bucket", "risk_level", "source_parser", "row_count", "pdf_count", "metric_count"])
    )

    review_burden_pdf_v2 = (
        review_v2.groupby("PDF文件名", dropna=False)
        .agg(
            review_required_row_count=("PDF文件名", "count"),
            review_required_metric_count=("标准指标", "nunique"),
            parser_mix=("source_parser", lambda x: "|".join(sorted({v for v in x if _norm(v) != ""}))),
            risk_mix=("risk_level", lambda x: "|".join(sorted({v for v in x if _norm(v) != ""}))),
        )
        .reset_index()
        .sort_values(["review_required_row_count", "review_required_metric_count"], ascending=[False, False])
        if not review_v2.empty
        else pd.DataFrame(columns=["PDF文件名", "review_required_row_count", "review_required_metric_count", "parser_mix", "risk_mix"])
    )

    review_burden_metric_v2 = (
        review_v2.groupby("标准指标", dropna=False)
        .agg(
            review_required_row_count=("标准指标", "count"),
            review_required_pdf_count=("PDF文件名", "nunique"),
            parser_mix=("source_parser", lambda x: "|".join(sorted({v for v in x if _norm(v) != ""}))),
            risk_mix=("risk_level", lambda x: "|".join(sorted({v for v in x if _norm(v) != ""}))),
        )
        .reset_index()
        .sort_values(["review_required_row_count", "review_required_pdf_count"], ascending=[False, False])
        if not review_v2.empty
        else pd.DataFrame(columns=["标准指标", "review_required_row_count", "review_required_pdf_count", "parser_mix", "risk_mix"])
    )

    # v1 baselines from 307b artifacts + 307g delta
    v1_trusted_rows = _to_int(delta_g[delta_g["metric"].map(_norm) == "trusted_rows_total"]["v1"].iloc[0]) if not delta_g.empty and (delta_g["metric"].map(_norm) == "trusted_rows_total").any() else 0
    v2_trusted_rows = _to_int(delta_g[delta_g["metric"].map(_norm) == "trusted_rows_total"]["v2"].iloc[0]) if not delta_g.empty and (delta_g["metric"].map(_norm) == "trusted_rows_total").any() else final_v2_row_count
    v1_review_rows = _to_int(delta_g[delta_g["metric"].map(_norm) == "review_required_rows"]["v1"].iloc[0]) if not delta_g.empty and (delta_g["metric"].map(_norm) == "review_required_rows").any() else 0
    v2_review_rows = _to_int(delta_g[delta_g["metric"].map(_norm) == "review_required_rows"]["v2"].iloc[0]) if not delta_g.empty and (delta_g["metric"].map(_norm) == "review_required_rows").any() else review_v2_row_count

    eps_v1 = _to_int(v1_review_metric[v1_review_metric["标准指标"] == "eps"]["review_required_row_count"].iloc[0]) if not v1_review_metric.empty and (v1_review_metric["标准指标"] == "eps").any() else 0
    eps_v2 = _to_int(review_burden_metric_v2[review_burden_metric_v2["标准指标"] == "eps"]["review_required_row_count"].iloc[0]) if not review_burden_metric_v2.empty and (review_burden_metric_v2["标准指标"] == "eps").any() else 0

    v1_target_cov = int(v1_metric[v1_metric["is_target_core_metric"] == True]["标准指标"].nunique()) if not v1_metric.empty else 0
    v2_target_cov = int(metric_cov_v2[metric_cov_v2["is_target_core_metric"] == True]["标准指标"].nunique()) if not metric_cov_v2.empty else 0

    v1_vs_v2_delta = pd.DataFrame(
        [
            {"metric": "trusted_rows_total", "v1": v1_trusted_rows, "v2": v2_trusted_rows, "delta": v2_trusted_rows - v1_trusted_rows},
            {"metric": "review_required_rows_total", "v1": v1_review_rows, "v2": v2_review_rows, "delta": v2_review_rows - v1_review_rows},
            {"metric": "eps_review_required_rows", "v1": eps_v1, "v2": eps_v2, "delta": eps_v2 - eps_v1},
            {"metric": "target_metric_coverage_count", "v1": v1_target_cov, "v2": v2_target_cov, "delta": v2_target_cov - v1_target_cov},
        ]
    )

    top_burden_metric_v2 = _norm(review_burden_metric_v2.iloc[0]["标准指标"]) if not review_burden_metric_v2.empty else ""
    top_burden_pdf_v2 = _norm(review_burden_pdf_v2.iloc[0]["PDF文件名"]) if not review_burden_pdf_v2.empty else ""

    target_metric_coverage_ratio_v2 = float(v2_target_cov / len(TARGET_METRICS)) if len(TARGET_METRICS) > 0 else 0.0
    trusted_to_total_ratio_v2 = float(v2_trusted_rows / (v2_trusted_rows + v2_review_rows)) if (v2_trusted_rows + v2_review_rows) > 0 else 0.0

    conflict_count = 0 if conflict_g.empty or ("note" in conflict_g.columns and len(conflict_g) == 1) else int(len(conflict_g))
    if target_metric_coverage_ratio_v2 >= 0.75 and trusted_to_total_ratio_v2 >= 0.20 and conflict_count == 0:
        readiness = "internal_test_ready"
    elif target_metric_coverage_ratio_v2 >= 0.5 and trusted_to_total_ratio_v2 >= 0.10 and conflict_count == 0:
        readiness = "demo_ready"
    else:
        readiness = "not_ready"

    readiness_df = pd.DataFrame(
        [
            {"assessment": "readiness_level", "value": readiness},
            {"assessment": "trusted_rows_v2", "value": v2_trusted_rows},
            {"assessment": "review_required_rows_v2", "value": v2_review_rows},
            {"assessment": "trusted_to_total_ratio_v2", "value": trusted_to_total_ratio_v2},
            {"assessment": "target_metric_coverage_ratio_v2", "value": target_metric_coverage_ratio_v2},
            {"assessment": "covered_target_metric_count_v2", "value": v2_target_cov},
            {"assessment": "target_metric_total", "value": len(TARGET_METRICS)},
            {"assessment": "conflict_audit_row_count", "value": conflict_count},
            {"assessment": "top_review_burden_metric_v2", "value": top_burden_metric_v2},
            {"assessment": "top_review_burden_pdf_v2", "value": top_burden_pdf_v2},
        ]
    )

    _write_excel(OUT_PDF_COV, {"pdf_level_coverage_v2": pdf_cov_v2})
    _write_excel(OUT_METRIC_COV, {"metric_level_coverage_v2": metric_cov_v2})
    _write_excel(OUT_BUCKET, {"source_bucket_distribution_v2": source_bucket_dist_v2})
    _write_excel(OUT_REVIEW_BREAK, {"review_required_breakdown_v2": review_breakdown_v2})
    _write_excel(OUT_REVIEW_PDF, {"review_burden_by_pdf_v2": review_burden_pdf_v2})
    _write_excel(OUT_REVIEW_METRIC, {"review_burden_by_metric_v2": review_burden_metric_v2})
    _write_excel(OUT_DELTA, {"v1_vs_v2_quality_delta": v1_vs_v2_delta})
    _write_excel(OUT_READY, {"export_readiness_assessment_v2": readiness_df})

    next_lines = [
        "# 307H Next Bottleneck Recommendation",
        "",
        f"- readiness: `{readiness}`",
        f"- top_review_burden_metric_v2: `{top_burden_metric_v2}`",
        f"- top_review_burden_pdf_v2: `{top_burden_pdf_v2}`",
        "",
        "## Recommendation",
        "- Prioritize next manual-review package on current top burden metric and top burden PDF.",
        "- Keep EPS merged trusted rows stable; avoid relaxing safety gates until burden decreases further.",
        "- Continue conflict-free incremental merges for high-impact metrics.",
    ]
    OUT_NEXT.write_text("\n".join(next_lines) + "\n", encoding="utf-8")

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

    forbidden_fields_generated = sorted([c for c in set(final_v2.columns).union(set(review_v2.columns)) if c in FORBIDDEN_FIELDS])

    # required assertions
    final_preview_v2_rows_remain_unchanged = (int(len(final_v2)) == v2_trusted_rows)
    review_required_v2_rows_remain_separate = (int(len(review_v2)) == v2_review_rows)

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-307H",
        "mode": "final_preview_v2_quality_diagnosis",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "final_preview_v2_row_count": final_v2_row_count,
        "review_required_v2_row_count": review_v2_row_count,
        "trusted_rows_delta_v2_minus_v1": v2_trusted_rows - v1_trusted_rows,
        "review_required_delta_v2_minus_v1": v2_review_rows - v1_review_rows,
        "eps_review_burden_delta_v2_minus_v1": eps_v2 - eps_v1,
        "target_metric_coverage_delta_v2_minus_v1": v2_target_cov - v1_target_cov,
        "top_review_burden_metric_v2": top_burden_metric_v2,
        "top_review_burden_pdf_v2": top_burden_pdf_v2,
        "readiness_assessment_v2": readiness,
        "final_preview_v2_rows_remain_unchanged": bool(final_preview_v2_rows_remain_unchanged),
        "review_required_v2_rows_remain_separate": bool(review_required_v2_rows_remain_separate),
        "no_safe_to_apply_or_approve_for_real_apply_fields_generated": bool(len(forbidden_fields_generated) == 0),
        "forbidden_fields_generated": forbidden_fields_generated,
        "check_delivery_state_overall_status": delivery_status,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 307H Final Preview v2 Quality Diagnosis",
        "",
        "## V1 vs V2 Delta",
        f"- trusted_rows_delta_v2_minus_v1: {summary['trusted_rows_delta_v2_minus_v1']}",
        f"- review_required_delta_v2_minus_v1: {summary['review_required_delta_v2_minus_v1']}",
        f"- eps_review_burden_delta_v2_minus_v1: {summary['eps_review_burden_delta_v2_minus_v1']}",
        f"- target_metric_coverage_delta_v2_minus_v1: {summary['target_metric_coverage_delta_v2_minus_v1']}",
        "",
        "## Current Burden",
        f"- top_review_burden_metric_v2: {summary['top_review_burden_metric_v2']}",
        f"- top_review_burden_pdf_v2: {summary['top_review_burden_pdf_v2']}",
        f"- readiness_assessment_v2: {summary['readiness_assessment_v2']}",
        "",
        "## Assertions",
        f"- final_preview_v2_rows_remain_unchanged: {summary['final_preview_v2_rows_remain_unchanged']}",
        f"- review_required_v2_rows_remain_separate: {summary['review_required_v2_rows_remain_separate']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        "",
        "## Guard",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_307h_summary_json: {OUT_SUMMARY}")
    print(f"eval_307h_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
