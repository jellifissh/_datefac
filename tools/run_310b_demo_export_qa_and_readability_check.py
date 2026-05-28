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
OUT_DIR = BASE_DIR / "output" / "eval_310b_demo_export_qa_and_readability_check"

IN_DEMO_EXPORT = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_demo_core_metric_export.xlsx"
IN_TRUSTED = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_trusted_core_metrics.xlsx"
IN_REVIEW = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_review_required_core_metrics.xlsx"
IN_PDF = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_pdf_coverage_summary.xlsx"
IN_METRIC = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_metric_coverage_summary.xlsx"
IN_NOT_MERGED = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_not_merged_rescue_simulation_summary.xlsx"
IN_NOTES = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_demo_readiness_notes.md"

OUT_SUMMARY = OUT_DIR / "310b_summary.json"
OUT_REPORT = OUT_DIR / "310b_report.md"
OUT_SHEET_AUDIT = OUT_DIR / "310b_workbook_sheet_audit.xlsx"
OUT_COL_AUDIT = OUT_DIR / "310b_column_readability_audit.xlsx"
OUT_CHECKLIST = OUT_DIR / "310b_demo_readiness_checklist.xlsx"
OUT_LAYOUT = OUT_DIR / "310b_recommended_demo_export_layout.md"
OUT_NO_APPLY = OUT_DIR / "310b_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
EXPECTED_TRUSTED_ROWS = 70
EXPECTED_REVIEW_ROWS = 342
REQUIRED_PROVENANCE_COLS = [
    "source_bucket",
    "source_parser",
    "source_page",
    "PDF文件名",
    "标准指标",
    "年份",
    "value",
    "normalized_unit",
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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_DEMO_EXPORT, IN_TRUSTED, IN_REVIEW, IN_PDF, IN_METRIC, IN_NOT_MERGED, IN_NOTES]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-310B",
                "mode": "demo_export_qa_and_readability_check",
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

    demo_xls = pd.ExcelFile(IN_DEMO_EXPORT)
    trusted_df = _load_first_sheet(IN_TRUSTED, "trusted_core_metrics")
    review_df = _load_first_sheet(IN_REVIEW, "review_required_core_metrics")
    pdf_df = _load_first_sheet(IN_PDF, "pdf_coverage_summary")
    metric_df = _load_first_sheet(IN_METRIC, "metric_coverage_summary")
    not_merged_df = _load_first_sheet(IN_NOT_MERGED)
    notes_text = IN_NOTES.read_text(encoding="utf-8")

    # workbook sheet audit
    sheet_audit_rows: List[Dict[str, Any]] = []
    for s in demo_xls.sheet_names:
        df = pd.read_excel(IN_DEMO_EXPORT, sheet_name=s).fillna("")
        sheet_audit_rows.append(
            {
                "sheet_name": s,
                "row_count": int(len(df)),
                "col_count": int(len(df.columns)),
                "non_empty_expected": bool(len(df) > 0) if s != "中文说明" else bool(len(df) > 0),
            }
        )
    sheet_audit_df = pd.DataFrame(sheet_audit_rows)

    trusted_row_count = int(len(trusted_df))
    review_row_count = int(len(review_df))

    # no simulated rescue merged
    trusted_source_buckets = set(trusted_df.get("source_bucket", pd.Series([], dtype=object)).map(_norm).tolist())
    no_simulated_rescue_merged = (
        "simulated_panel_denoise_rescue" not in trusted_source_buckets
        and "simulated_unit_semantic_rescue" not in trusted_source_buckets
    )

    # provenance columns check
    trusted_cols = list(trusted_df.columns)
    missing_provenance_cols = [c for c in REQUIRED_PROVENANCE_COLS if c not in trusted_cols]

    # Chinese explanation readability
    chinese_explanation_exists = any(s == "中文说明" for s in demo_xls.sheet_names) or ("中文" in notes_text)
    chinese_readable = chinese_explanation_exists and ("当前" in notes_text or "行数" in notes_text or "建议" in notes_text)

    # column readability audit (rename suggestions)
    rename_map = {
        "PDF文件名": "报告文件",
        "标准指标": "核心指标",
        "指标名": "原始指标名",
        "年份": "年份(年)",
        "value": "指标值",
        "normalized_unit": "标准单位",
        "source_bucket": "来源分组",
        "source_parser": "来源解析器",
        "source_page": "来源页码",
        "review_status": "审核状态",
        "risk_level": "风险级别",
    }

    col_audit_rows: List[Dict[str, Any]] = []
    for c in trusted_cols:
        col_audit_rows.append(
            {
                "column_name": c,
                "present_in_trusted": True,
                "readability_level": "clear" if c in {"PDF文件名", "标准指标", "年份", "value"} else "ok",
                "recommended_display_name": rename_map.get(c, c),
                "rename_recommended": c in rename_map and rename_map[c] != c,
            }
        )
    col_audit_df = pd.DataFrame(col_audit_rows)

    # readiness decision
    hard_fail = (
        trusted_row_count != EXPECTED_TRUSTED_ROWS
        or review_row_count != EXPECTED_REVIEW_ROWS
        or not no_simulated_rescue_merged
        or len(missing_provenance_cols) > 0
        or not chinese_readable
    )
    if hard_fail:
        readiness = "not_ready"
    else:
        # if all hard checks pass but has rename suggestions -> needs_readability_fix
        rename_cnt = int(col_audit_df["rename_recommended"].sum()) if not col_audit_df.empty else 0
        readiness = "needs_readability_fix" if rename_cnt > 0 else "demo_ready"

    checklist = pd.DataFrame(
        [
            {"check_item": "workbook_sheets_exist", "result": bool(len(demo_xls.sheet_names) >= 6), "detail": "expected >=6 sheets"},
            {"check_item": "trusted_row_count_eq_70", "result": bool(trusted_row_count == EXPECTED_TRUSTED_ROWS), "detail": trusted_row_count},
            {"check_item": "review_required_row_count_eq_342", "result": bool(review_row_count == EXPECTED_REVIEW_ROWS), "detail": review_row_count},
            {"check_item": "no_simulated_rescue_merged", "result": bool(no_simulated_rescue_merged), "detail": "check source_bucket"},
            {"check_item": "trusted_has_provenance_columns", "result": bool(len(missing_provenance_cols) == 0), "detail": "missing=" + "|".join(missing_provenance_cols)},
            {"check_item": "chinese_explanation_readable", "result": bool(chinese_readable), "detail": "sheet/notes check"},
            {"check_item": "presentation_readiness", "result": True, "detail": readiness},
        ]
    )

    layout_lines = [
        "# 310B Recommended Demo Export Layout",
        "",
        "## 推荐展示顺序",
        "1. trusted_core_metrics（核心演示页）",
        "2. pdf_coverage_summary（按报告覆盖）",
        "3. metric_coverage_summary（按指标覆盖）",
        "4. review_required_core_metrics（待复核池）",
        "5. not_merged_rescue_simulation（模拟未合并说明）",
        "6. 中文说明（面向业务讲解）",
        "",
        "## 列名可读性建议",
        "- PDF文件名 -> 报告文件",
        "- 标准指标 -> 核心指标",
        "- 指标名 -> 原始指标名",
        "- value -> 指标值",
        "- normalized_unit -> 标准单位",
        "- source_bucket -> 来源分组",
        "- source_parser -> 来源解析器",
        "- source_page -> 来源页码",
    ]
    OUT_LAYOUT.write_text("\n".join(layout_lines) + "\n", encoding="utf-8")

    _write_excel(OUT_SHEET_AUDIT, {"workbook_sheet_audit": sheet_audit_df})
    _write_excel(OUT_COL_AUDIT, {"column_readability_audit": col_audit_df})
    _write_excel(OUT_CHECKLIST, {"demo_readiness_checklist": checklist})

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

    forbidden_fields_generated = sorted([c for c in set(trusted_cols).union(set(review_df.columns)) if c in FORBIDDEN_FIELDS])

    after_guard = _snapshot_guard()
    production_files_modified = any(before_guard[k] != after_guard[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before_guard["official_02b"] != after_guard["official_02b"]
    formal_rules_modified = before_guard["formal_rules"] != after_guard["formal_rules"]
    standardizer_modified = before_guard["standardizer"] != after_guard["standardizer"]
    release_package_modified = before_guard["release_zip"] != after_guard["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-310B",
        "mode": "demo_export_qa_and_readability_check",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "trusted_row_count": trusted_row_count,
        "review_required_row_count": review_row_count,
        "trusted_row_count_preserved_310a": bool(trusted_row_count == EXPECTED_TRUSTED_ROWS),
        "review_required_row_count_preserved_310a": bool(review_row_count == EXPECTED_REVIEW_ROWS),
        "no_simulated_rescue_rows_merged": bool(no_simulated_rescue_merged),
        "missing_provenance_columns": missing_provenance_cols,
        "chinese_explanation_exists_and_readable": bool(chinese_readable),
        "readiness_status": readiness,
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
        "# 310B Demo Export QA And Readability Check",
        "",
        "## QA Snapshot",
        f"- trusted_row_count: {trusted_row_count}",
        f"- review_required_row_count: {review_row_count}",
        f"- no_simulated_rescue_rows_merged: {no_simulated_rescue_merged}",
        f"- chinese_explanation_readable: {chinese_readable}",
        f"- readiness_status: {readiness}",
        "",
        "## Readability Notes",
        f"- rename_recommended_column_count: {int(col_audit_df['rename_recommended'].sum()) if not col_audit_df.empty else 0}",
        f"- missing_provenance_columns: {'|'.join(missing_provenance_cols) if missing_provenance_cols else 'none'}",
        "",
        "## Guard Assertions",
        f"- trusted_row_count_preserved_310a: {summary['trusted_row_count_preserved_310a']}",
        f"- review_required_row_count_preserved_310a: {summary['review_required_row_count_preserved_310a']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_310b_summary_json: {OUT_SUMMARY}")
    print(f"eval_310b_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
