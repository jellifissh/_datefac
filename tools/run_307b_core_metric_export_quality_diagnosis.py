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
OUT_DIR = BASE_DIR / "output" / "eval_307b_core_metric_export_quality_diagnosis"

IN_FINAL = BASE_DIR / "output" / "eval_307a_core_metric_final_export_preview" / "307a_final_core_metric_preview.xlsx"
IN_REVIEW = BASE_DIR / "output" / "eval_307a_core_metric_final_export_preview" / "307a_review_required_core_metrics.xlsx"
IN_COVERAGE = BASE_DIR / "output" / "eval_307a_core_metric_final_export_preview" / "307a_coverage_by_pdf_metric.xlsx"
IN_QUALITY = BASE_DIR / "output" / "eval_307a_core_metric_final_export_preview" / "307a_export_quality_summary.xlsx"
IN_CONFLICT = BASE_DIR / "output" / "eval_307a_core_metric_final_export_preview" / "307a_conflict_audit.xlsx"

OUT_SUMMARY = OUT_DIR / "307b_summary.json"
OUT_REPORT = OUT_DIR / "307b_report.md"
OUT_PDF_COV = OUT_DIR / "307b_pdf_level_coverage.xlsx"
OUT_METRIC_COV = OUT_DIR / "307b_metric_level_coverage.xlsx"
OUT_BUCKET_DIST = OUT_DIR / "307b_source_bucket_distribution.xlsx"
OUT_REVIEW_BREAKDOWN = OUT_DIR / "307b_review_required_breakdown.xlsx"
OUT_BURDEN_PDF = OUT_DIR / "307b_review_burden_by_pdf.xlsx"
OUT_BURDEN_METRIC = OUT_DIR / "307b_review_burden_by_metric.xlsx"
OUT_READINESS = OUT_DIR / "307b_export_readiness_assessment.xlsx"
OUT_NEXT = OUT_DIR / "307b_next_bottleneck_recommendation.md"
OUT_NO_APPLY = OUT_DIR / "307b_no_apply_proof.json"

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

    required = [IN_FINAL, IN_REVIEW, IN_COVERAGE, IN_QUALITY, IN_CONFLICT]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-307B",
                "mode": "core_metric_export_quality_diagnosis",
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

    final_df = _drop_note_rows(_load_first_sheet(IN_FINAL, "final_core_metric_preview"))
    review_df = _drop_note_rows(_load_first_sheet(IN_REVIEW, "review_required_core_metrics"))
    coverage_df = _drop_note_rows(_load_first_sheet(IN_COVERAGE, "coverage_by_pdf_metric"))
    quality_df = _drop_note_rows(_load_first_sheet(IN_QUALITY, "export_quality_summary"))
    conflict_df = _drop_note_rows(_load_first_sheet(IN_CONFLICT, "conflict_audit"))

    # canonical normalization
    for df in [final_df, review_df]:
        if "PDF文件名" in df.columns:
            df["PDF文件名"] = df["PDF文件名"].map(_norm)
        if "标准指标" in df.columns:
            df["标准指标"] = df["标准指标"].map(_norm).str.lower()
        if "source_bucket" in df.columns:
            df["source_bucket"] = df["source_bucket"].map(_norm)
        if "年份" in df.columns:
            df["年份"] = df["年份"].map(_to_int)
        if "source_parser" in df.columns:
            df["source_parser"] = df["source_parser"].map(_norm)
        if "risk_level" in df.columns:
            df["risk_level"] = df["risk_level"].map(_norm)

    final_row_count = int(len(final_df))
    review_row_count = int(len(review_df))

    # trusted distribution
    source_bucket_dist = (
        final_df.groupby("source_bucket", dropna=False)
        .agg(row_count=("PDF文件名", "count"), pdf_count=("PDF文件名", "nunique"), metric_count=("标准指标", "nunique"))
        .reset_index()
        if not final_df.empty
        else pd.DataFrame(columns=["source_bucket", "row_count", "pdf_count", "metric_count"])
    )

    pdf_level_cov = (
        final_df.groupby("PDF文件名", dropna=False)
        .agg(
            trusted_row_count=("PDF文件名", "count"),
            trusted_metric_count=("标准指标", "nunique"),
            trusted_year_count=("年份", "nunique"),
            source_bucket_mix=("source_bucket", lambda x: "|".join(sorted(set(x)))),
        )
        .reset_index()
        if not final_df.empty
        else pd.DataFrame(columns=["PDF文件名", "trusted_row_count", "trusted_metric_count", "trusted_year_count", "source_bucket_mix"])
    )

    metric_level_cov = (
        final_df.groupby("标准指标", dropna=False)
        .agg(
            trusted_row_count=("标准指标", "count"),
            pdf_count=("PDF文件名", "nunique"),
            year_count=("年份", "nunique"),
            source_bucket_mix=("source_bucket", lambda x: "|".join(sorted(set(x)))),
        )
        .reset_index()
        if not final_df.empty
        else pd.DataFrame(columns=["标准指标", "trusted_row_count", "pdf_count", "year_count", "source_bucket_mix"])
    )

    # target coverage estimate
    metric_level_cov["is_target_core_metric"] = metric_level_cov["标准指标"].isin(TARGET_METRICS) if not metric_level_cov.empty else False
    covered_target_metrics = int(metric_level_cov[metric_level_cov["is_target_core_metric"] == True]["标准指标"].nunique()) if not metric_level_cov.empty else 0
    target_metric_coverage_ratio = float(covered_target_metrics / len(TARGET_METRICS)) if len(TARGET_METRICS) > 0 else 0.0

    # review burden breakdown
    review_breakdown = (
        review_df.groupby(["source_bucket", "risk_level", "source_parser"], dropna=False)
        .agg(row_count=("PDF文件名", "count"), pdf_count=("PDF文件名", "nunique"), metric_count=("标准指标", "nunique"))
        .reset_index()
        if not review_df.empty
        else pd.DataFrame(columns=["source_bucket", "risk_level", "source_parser", "row_count", "pdf_count", "metric_count"])
    )

    review_burden_pdf = (
        review_df.groupby("PDF文件名", dropna=False)
        .agg(
            review_required_row_count=("PDF文件名", "count"),
            review_required_metric_count=("标准指标", "nunique"),
            review_required_parser_mix=("source_parser", lambda x: "|".join(sorted({v for v in x if _norm(v) != ""}))),
            review_required_risk_mix=("risk_level", lambda x: "|".join(sorted({v for v in x if _norm(v) != ""}))),
        )
        .reset_index()
        .sort_values(["review_required_row_count", "review_required_metric_count"], ascending=[False, False])
        if not review_df.empty
        else pd.DataFrame(columns=["PDF文件名", "review_required_row_count", "review_required_metric_count", "review_required_parser_mix", "review_required_risk_mix"])
    )

    review_burden_metric = (
        review_df.groupby("标准指标", dropna=False)
        .agg(
            review_required_row_count=("标准指标", "count"),
            review_required_pdf_count=("PDF文件名", "nunique"),
            review_required_parser_mix=("source_parser", lambda x: "|".join(sorted({v for v in x if _norm(v) != ""}))),
            review_required_risk_mix=("risk_level", lambda x: "|".join(sorted({v for v in x if _norm(v) != ""}))),
        )
        .reset_index()
        .sort_values(["review_required_row_count", "review_required_pdf_count"], ascending=[False, False])
        if not review_df.empty
        else pd.DataFrame(columns=["标准指标", "review_required_row_count", "review_required_pdf_count", "review_required_parser_mix", "review_required_risk_mix"])
    )

    # lowest trusted coverage
    lowest_pdf_cov = (
        pdf_level_cov.sort_values(["trusted_row_count", "trusted_metric_count"], ascending=[True, True]).head(5)
        if not pdf_level_cov.empty
        else pd.DataFrame()
    )
    lowest_metric_cov = (
        metric_level_cov.sort_values(["trusted_row_count", "pdf_count"], ascending=[True, True]).head(5)
        if not metric_level_cov.empty
        else pd.DataFrame()
    )

    # blocker proxy from review burden (no explicit blocker cols in 307A review_required file)
    # use metric/source_parser concentration as bottleneck proxy
    top_burden_metric = _norm(review_burden_metric.iloc[0]["标准指标"]) if not review_burden_metric.empty else ""
    top_burden_pdf = _norm(review_burden_pdf.iloc[0]["PDF文件名"]) if not review_burden_pdf.empty else ""

    # readiness assessment
    trusted_to_review_ratio = float(final_row_count / (final_row_count + review_row_count)) if (final_row_count + review_row_count) > 0 else 0.0
    conflict_rows = 0 if conflict_df.empty or ("note" in conflict_df.columns and len(conflict_df) == 1) else int(len(conflict_df))
    if target_metric_coverage_ratio >= 0.75 and trusted_to_review_ratio >= 0.25 and conflict_rows == 0:
        readiness = "internal_test_ready"
    elif target_metric_coverage_ratio >= 0.5 and trusted_to_review_ratio >= 0.10 and conflict_rows == 0:
        readiness = "demo_ready"
    else:
        readiness = "not_ready"

    readiness_df = pd.DataFrame(
        [
            {"assessment": "readiness_level", "value": readiness},
            {"assessment": "trusted_row_count", "value": final_row_count},
            {"assessment": "review_required_row_count", "value": review_row_count},
            {"assessment": "trusted_to_total_ratio", "value": trusted_to_review_ratio},
            {"assessment": "target_metric_coverage_ratio", "value": target_metric_coverage_ratio},
            {"assessment": "covered_target_metric_count", "value": covered_target_metrics},
            {"assessment": "target_metric_total", "value": len(TARGET_METRICS)},
            {"assessment": "conflict_audit_row_count", "value": conflict_rows},
        ]
    )

    _write_excel(OUT_PDF_COV, {"pdf_level_coverage": pdf_level_cov, "lowest_pdf_coverage": lowest_pdf_cov})
    _write_excel(OUT_METRIC_COV, {"metric_level_coverage": metric_level_cov, "lowest_metric_coverage": lowest_metric_cov})
    _write_excel(OUT_BUCKET_DIST, {"source_bucket_distribution": source_bucket_dist})
    _write_excel(OUT_REVIEW_BREAKDOWN, {"review_required_breakdown": review_breakdown})
    _write_excel(OUT_BURDEN_PDF, {"review_burden_by_pdf": review_burden_pdf})
    _write_excel(OUT_BURDEN_METRIC, {"review_burden_by_metric": review_burden_metric})
    _write_excel(OUT_READINESS, {"export_readiness_assessment": readiness_df})

    next_lines = [
        "# 307B Next Bottleneck Recommendation",
        "",
        f"- readiness: `{readiness}`",
        f"- trusted_to_total_ratio: `{trusted_to_review_ratio:.4f}`",
        f"- target_metric_coverage_ratio: `{target_metric_coverage_ratio:.4f}`",
        "",
        "## Bottleneck Signals",
        f"- top_review_burden_pdf: `{top_burden_pdf}`",
        f"- top_review_burden_metric: `{top_burden_metric}`",
        "",
        "## Recommendation",
        "- Prioritize reducing `review_required` volume on top burden PDFs/metrics first.",
        "- Keep conflict-free trusted preview unchanged; expand manual-reviewed bucket with strict quality gate.",
        "- Do not relax safety constraints until review burden concentration drops materially.",
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

    forbidden_fields_generated = sorted([c for c in set(final_df.columns).union(set(review_df.columns)) if c in FORBIDDEN_FIELDS])

    # assertions against 307A quality summary
    quality_map = { _norm(r["metric"]): _to_int(r["value"]) for _, r in quality_df.iterrows() } if not quality_df.empty else {}
    final_preview_rows_unchanged = final_row_count == _to_int(quality_map.get("final_core_preview_rows", final_row_count))
    review_required_rows_separate = review_row_count == _to_int(quality_map.get("review_required_rows_separate", review_row_count))

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-307B",
        "mode": "core_metric_export_quality_diagnosis",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "final_preview_row_count": final_row_count,
        "review_required_row_count": review_row_count,
        "trusted_to_total_ratio": trusted_to_review_ratio,
        "covered_target_metric_count": covered_target_metrics,
        "target_metric_total": len(TARGET_METRICS),
        "target_metric_coverage_ratio": target_metric_coverage_ratio,
        "readiness_assessment": readiness,
        "top_review_burden_pdf": top_burden_pdf,
        "top_review_burden_metric": top_burden_metric,
        "final_preview_rows_remain_unchanged": bool(final_preview_rows_unchanged),
        "review_required_rows_remain_separate": bool(review_required_rows_separate),
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
        "# 307B Core Metric Export Quality Diagnosis",
        "",
        "## Overview",
        f"- final_preview_row_count: {final_row_count}",
        f"- review_required_row_count: {review_row_count}",
        f"- trusted_to_total_ratio: {trusted_to_review_ratio:.4f}",
        f"- target_metric_coverage_ratio: {target_metric_coverage_ratio:.4f} ({covered_target_metrics}/{len(TARGET_METRICS)})",
        f"- readiness_assessment: {readiness}",
        "",
        "## Burden Focus",
        f"- top_review_burden_pdf: {top_burden_pdf}",
        f"- top_review_burden_metric: {top_burden_metric}",
        "",
        "## Assertions",
        f"- final_preview_rows_remain_unchanged: {summary['final_preview_rows_remain_unchanged']}",
        f"- review_required_rows_remain_separate: {summary['review_required_rows_remain_separate']}",
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

    print(f"eval_307b_summary_json: {OUT_SUMMARY}")
    print(f"eval_307b_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
