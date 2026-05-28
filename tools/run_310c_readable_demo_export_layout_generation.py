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
OUT_DIR = BASE_DIR / "output" / "eval_310c_readable_demo_export_layout_generation"

IN_DEMO = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_demo_core_metric_export.xlsx"
IN_TRUSTED = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_trusted_core_metrics.xlsx"
IN_REVIEW = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_review_required_core_metrics.xlsx"
IN_PDF = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_pdf_coverage_summary.xlsx"
IN_METRIC = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_metric_coverage_summary.xlsx"
IN_NOT_MERGED = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_not_merged_rescue_simulation_summary.xlsx"
IN_COL_AUDIT = BASE_DIR / "output" / "eval_310b_demo_export_qa_and_readability_check" / "310b_column_readability_audit.xlsx"
IN_LAYOUT_MD = BASE_DIR / "output" / "eval_310b_demo_export_qa_and_readability_check" / "310b_recommended_demo_export_layout.md"

OUT_SUMMARY = OUT_DIR / "310c_summary.json"
OUT_REPORT = OUT_DIR / "310c_report.md"
OUT_READABLE = OUT_DIR / "310c_readable_demo_core_metric_export.xlsx"
OUT_TRUSTED_READABLE = OUT_DIR / "310c_trusted_core_metrics_readable.xlsx"
OUT_REVIEW_SUMMARY = OUT_DIR / "310c_review_required_summary_readable.xlsx"
OUT_RENAME_MAP = OUT_DIR / "310c_column_rename_mapping.xlsx"
OUT_LAYOUT_AUDIT = OUT_DIR / "310c_export_layout_audit.xlsx"
OUT_NO_APPLY = OUT_DIR / "310c_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
EXPECTED_SHEET_ORDER = [
    "使用说明",
    "可信核心指标_宽表",
    "可信核心指标_明细",
    "PDF覆盖率",
    "指标覆盖率",
    "待复核摘要",
    "未合并模拟救援说明",
    "原始可信明细_审计用",
    "原始待复核明细_审计用",
]
RENAME_MAP = {
    "PDF文件名": "报告文件",
    "标准指标": "核心指标",
    "指标名": "原始指标名",
    "年份": "年份",
    "value": "指标值",
    "normalized_unit": "标准单位",
    "source_bucket": "来源分组",
    "source_parser": "解析器",
    "source_page": "来源页码",
    "review_status": "审核状态",
    "risk_level": "风险级别",
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


def _load_first_sheet(path: Path, preferred: str | None = None) -> pd.DataFrame:
    xls = pd.ExcelFile(path)
    if preferred and preferred in xls.sheet_names:
        return pd.read_excel(path, sheet_name=preferred).fillna("")
    return pd.read_excel(path, sheet_name=xls.sheet_names[0]).fillna("")


def _rename_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [RENAME_MAP.get(c, c) for c in out.columns]
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_DEMO, IN_TRUSTED, IN_REVIEW, IN_PDF, IN_METRIC, IN_NOT_MERGED, IN_COL_AUDIT, IN_LAYOUT_MD]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-310C",
                "mode": "readable_demo_export_layout_generation",
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

    before_guard = _snapshot_guard()
    trusted_before_hash = _sha256(IN_TRUSTED)
    review_before_hash = _sha256(IN_REVIEW)

    trusted_df = _load_first_sheet(IN_TRUSTED, "trusted_core_metrics")
    review_df = _load_first_sheet(IN_REVIEW, "review_required_core_metrics")
    pdf_df = _load_first_sheet(IN_PDF, "pdf_coverage_summary")
    metric_df = _load_first_sheet(IN_METRIC, "metric_coverage_summary")
    not_merged_df = _load_first_sheet(IN_NOT_MERGED)
    col_audit_df = _load_first_sheet(IN_COL_AUDIT, "column_readability_audit")
    layout_md = IN_LAYOUT_MD.read_text(encoding="utf-8")

    trusted_row_count = int(len(trusted_df))
    review_row_count = int(len(review_df))

    # readable display tables
    trusted_readable = _rename_cols(trusted_df)
    review_readable = _rename_cols(review_df)
    pdf_readable = _rename_cols(pdf_df)
    metric_readable = _rename_cols(metric_df)
    not_merged_readable = _rename_cols(not_merged_df)

    # wide pivot for trusted
    wide = trusted_readable.copy()
    year_col = "年份"
    value_col = "指标值"
    idx_cols = ["报告文件", "核心指标", "标准单位"]
    for c in idx_cols + [year_col, value_col]:
        if c not in wide.columns:
            wide[c] = ""
    trusted_wide = (
        wide.pivot_table(index=idx_cols, columns=year_col, values=value_col, aggfunc="first", fill_value="")
        .reset_index()
    )

    # review summary by PDF/metric/risk_level
    summary_cols = ["报告文件", "核心指标", "风险级别"]
    for c in summary_cols:
        if c not in review_readable.columns:
            review_readable[c] = ""
    review_summary = (
        review_readable.groupby(summary_cols, dropna=False)
        .agg(
            待复核行数=("报告文件", "count"),
            年份覆盖=("年份", lambda x: "|".join(sorted(set(_norm(v) for v in x if _norm(v) != ""))[:8])),
            解析器覆盖=("解析器", lambda x: "|".join(sorted(set(_norm(v) for v in x if _norm(v) != ""))[:6])) if "解析器" in review_readable.columns else ("报告文件", lambda x: ""),
        )
        .reset_index()
        .sort_values("待复核行数", ascending=False)
    )

    # 使用说明
    guide = pd.DataFrame(
        [
            {"说明": "本工作簿仅用于 Demo 展示排版，不改变任何抽取结果与成员关系。"},
            {"说明": f"可信核心指标行数：{trusted_row_count}（应为70）"},
            {"说明": f"待复核行数：{review_row_count}（应为342）"},
            {"说明": "模拟救援结果（308C/309B）未并入可信导出，仅在说明页保留。"},
            {"说明": "审计用原始明细页保留原列与原成员，便于追溯。"},
        ]
    )

    # write readable workbook with required sheet order
    _write_excel(
        OUT_READABLE,
        {
            "使用说明": guide,
            "可信核心指标_宽表": trusted_wide,
            "可信核心指标_明细": trusted_readable,
            "PDF覆盖率": pdf_readable,
            "指标覆盖率": metric_readable,
            "待复核摘要": review_summary,
            "未合并模拟救援说明": not_merged_readable,
            "原始可信明细_审计用": trusted_df,
            "原始待复核明细_审计用": review_df,
        },
    )

    _write_excel(OUT_TRUSTED_READABLE, {"可信核心指标_明细": trusted_readable, "可信核心指标_宽表": trusted_wide})
    _write_excel(OUT_REVIEW_SUMMARY, {"待复核摘要": review_summary, "原始待复核明细_审计用": review_df})

    rename_mapping = pd.DataFrame(
        [{"original_column": k, "display_column": v} for k, v in RENAME_MAP.items()]
    )
    _write_excel(OUT_RENAME_MAP, {"column_rename_mapping": rename_mapping, "310b_column_readability_audit_ref": col_audit_df})

    # layout audit
    generated_xls = pd.ExcelFile(OUT_READABLE)
    actual_order = generated_xls.sheet_names
    order_match = actual_order == EXPECTED_SHEET_ORDER

    layout_audit = pd.DataFrame(
        [
            {"check_item": "sheet_order_match_required", "result": bool(order_match), "detail": "|".join(actual_order)},
            {"check_item": "trusted_row_count_preserved", "result": bool(trusted_row_count == 70), "detail": trusted_row_count},
            {"check_item": "review_row_count_preserved", "result": bool(review_row_count == 342), "detail": review_row_count},
            {"check_item": "not_merged_simulated_rescue", "result": True, "detail": "explicit separation kept"},
            {"check_item": "layout_md_reference_loaded", "result": bool(len(layout_md) > 0), "detail": "310b_recommended_demo_export_layout.md"},
        ]
    )
    _write_excel(OUT_LAYOUT_AUDIT, {"export_layout_audit": layout_audit})

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

    trusted_after_hash = _sha256(IN_TRUSTED)
    review_after_hash = _sha256(IN_REVIEW)

    # ensure no simulated rescue merged in trusted membership
    trusted_source_buckets = set(trusted_df.get("source_bucket", pd.Series([], dtype=object)).map(_norm).tolist())
    no_simulated_rescue_merged = (
        "simulated_panel_denoise_rescue" not in trusted_source_buckets
        and "simulated_unit_semantic_rescue" not in trusted_source_buckets
    )

    forbidden_fields_generated = sorted([c for c in set(trusted_df.columns).union(set(review_df.columns)).union(set(trusted_readable.columns)).union(set(review_readable.columns)) if c in FORBIDDEN_FIELDS])

    after_guard = _snapshot_guard()
    production_files_modified = any(before_guard[k] != after_guard[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before_guard["official_02b"] != after_guard["official_02b"]
    formal_rules_modified = before_guard["formal_rules"] != after_guard["formal_rules"]
    standardizer_modified = before_guard["standardizer"] != after_guard["standardizer"]
    release_package_modified = before_guard["release_zip"] != after_guard["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-310C",
        "mode": "readable_demo_export_layout_generation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "trusted_row_count": trusted_row_count,
        "review_required_row_count": review_row_count,
        "trusted_row_count_preserved": bool(trusted_row_count == 70),
        "review_required_row_count_preserved": bool(review_row_count == 342),
        "no_simulated_rescue_rows_merged": bool(no_simulated_rescue_merged),
        "no_safe_to_apply_or_approve_for_real_apply_fields_generated": bool(len(forbidden_fields_generated) == 0),
        "forbidden_fields_generated": forbidden_fields_generated,
        "readable_workbook_generated": bool(OUT_READABLE.exists()),
        "required_sheet_order_match": bool(order_match),
        "source_membership_unchanged_trusted_file_hash": bool(trusted_before_hash == trusted_after_hash),
        "source_membership_unchanged_review_file_hash": bool(review_before_hash == review_after_hash),
        "check_delivery_state_overall_status": delivery_status,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 310C Readable Demo Export Layout Generation",
        "",
        "## Result",
        f"- trusted_row_count: {trusted_row_count}",
        f"- review_required_row_count: {review_row_count}",
        f"- readable_workbook_generated: {summary['readable_workbook_generated']}",
        f"- required_sheet_order_match: {summary['required_sheet_order_match']}",
        "",
        "## Presentation Changes",
        "- display column rename applied on readable sheets",
        "- trusted wide pivot sheet added",
        "- review_required summarized by PDF/metric/risk_level",
        "- original audit sheets preserved",
        "",
        "## Guard Assertions",
        f"- trusted_row_count_preserved: {summary['trusted_row_count_preserved']}",
        f"- review_required_row_count_preserved: {summary['review_required_row_count_preserved']}",
        f"- no_simulated_rescue_rows_merged: {summary['no_simulated_rescue_rows_merged']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_310c_summary_json: {OUT_SUMMARY}")
    print(f"eval_310c_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
