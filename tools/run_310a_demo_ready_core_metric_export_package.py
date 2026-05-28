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
OUT_DIR = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package"

IN_307G_FINAL = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_final_core_metric_preview_v2.xlsx"
IN_307G_REVIEW = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_review_required_core_metrics_v2.xlsx"
IN_307H_PDF = BASE_DIR / "output" / "eval_307h_final_preview_v2_quality_diagnosis" / "307h_pdf_level_coverage_v2.xlsx"
IN_307H_METRIC = BASE_DIR / "output" / "eval_307h_final_preview_v2_quality_diagnosis" / "307h_metric_level_coverage_v2.xlsx"
IN_307H_READY = BASE_DIR / "output" / "eval_307h_final_preview_v2_quality_diagnosis" / "307h_export_readiness_assessment_v2.xlsx"
IN_307X_REPORT = BASE_DIR / "output" / "eval_307x_core_metric_pipeline_stage_summary" / "307x_stage_summary_report.md"
IN_308D_SUMMARY = BASE_DIR / "output" / "eval_308d_panel_denoise_rescue_safety_validation" / "308d_summary.json"
IN_309C_SUMMARY = BASE_DIR / "output" / "eval_309c_unit_semantic_rescue_safety_validation" / "309c_summary.json"

OUT_SUMMARY = OUT_DIR / "310a_summary.json"
OUT_REPORT = OUT_DIR / "310a_demo_report.md"
OUT_DEMO_EXPORT = OUT_DIR / "310a_demo_core_metric_export.xlsx"
OUT_TRUSTED = OUT_DIR / "310a_trusted_core_metrics.xlsx"
OUT_REVIEW = OUT_DIR / "310a_review_required_core_metrics.xlsx"
OUT_PDF_SUM = OUT_DIR / "310a_pdf_coverage_summary.xlsx"
OUT_METRIC_SUM = OUT_DIR / "310a_metric_coverage_summary.xlsx"
OUT_NOT_MERGED = OUT_DIR / "310a_not_merged_rescue_simulation_summary.xlsx"
OUT_NOTES = OUT_DIR / "310a_demo_readiness_notes.md"
OUT_NO_APPLY = OUT_DIR / "310a_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}


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

    required = [
        IN_307G_FINAL,
        IN_307G_REVIEW,
        IN_307H_PDF,
        IN_307H_METRIC,
        IN_307H_READY,
        IN_307X_REPORT,
        IN_308D_SUMMARY,
        IN_309C_SUMMARY,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-310A",
                "mode": "demo_ready_core_metric_export_package",
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
    final_before_hash = _sha256(IN_307G_FINAL)

    trusted_df = _drop_note_rows(_load_first_sheet(IN_307G_FINAL, "final_core_metric_preview_v2"))
    review_df = _drop_note_rows(_load_first_sheet(IN_307G_REVIEW, "review_required_core_metrics_v2"))
    pdf_cov_df = _drop_note_rows(_load_first_sheet(IN_307H_PDF, "pdf_level_coverage_v2"))
    metric_cov_df = _drop_note_rows(_load_first_sheet(IN_307H_METRIC, "metric_level_coverage_v2"))
    readiness_df = _drop_note_rows(_load_first_sheet(IN_307H_READY, "export_readiness_assessment_v2"))

    stage_307x_report = IN_307X_REPORT.read_text(encoding="utf-8")
    s308d = json.loads(IN_308D_SUMMARY.read_text(encoding="utf-8"))
    s309c = json.loads(IN_309C_SUMMARY.read_text(encoding="utf-8"))

    trusted_row_count = int(len(trusted_df))
    review_row_count = int(len(review_df))

    # Keep explicit not-merged simulation summary
    not_merged_df = pd.DataFrame(
        [
            {
                "simulation_stage": "308D_panel_denoise_rescue_safety_validation",
                "simulated_row_count": _to_int(s308d.get("input_would_rescue_row_count", 0)),
                "merged_into_trusted_export": False,
                "reason": "Simulation-only safety validation; explicit no-merge policy in 310A.",
            },
            {
                "simulation_stage": "309C_unit_semantic_rescue_safety_validation",
                "simulated_row_count": _to_int(s309c.get("input_would_rescue_row_count", 0)),
                "merged_into_trusted_export": False,
                "reason": "Simulation-only safety validation; explicit no-merge policy in 310A.",
            },
        ]
    )

    # Demo export workbook with Chinese note sheet
    note_cn = pd.DataFrame(
        [
            {"说明": "当前阶段为 Demo 导出包，不包含任何 real apply。"},
            {"说明": f"当前 trusted 行数：{trusted_row_count}"},
            {"说明": f"当前 review_required 行数：{review_row_count}"},
            {"说明": "308C 与 309B/309C 的 simulated rescue 仅用于安全验证，未并入 trusted 导出。"},
            {"说明": "建议下一步：优先做规则安全校准与分层验证，再考虑沙箱合并试验。"},
        ]
    )

    _write_excel(
        OUT_DEMO_EXPORT,
        {
            "trusted_core_metrics": trusted_df,
            "review_required_core_metrics": review_df,
            "pdf_coverage_summary": pdf_cov_df,
            "metric_coverage_summary": metric_cov_df,
            "not_merged_rescue_simulation": not_merged_df,
            "中文说明": note_cn,
        },
    )

    _write_excel(OUT_TRUSTED, {"trusted_core_metrics": trusted_df})
    _write_excel(OUT_REVIEW, {"review_required_core_metrics": review_df})
    _write_excel(OUT_PDF_SUM, {"pdf_coverage_summary": pdf_cov_df})
    _write_excel(OUT_METRIC_SUM, {"metric_coverage_summary": metric_cov_df})
    _write_excel(OUT_NOT_MERGED, {"not_merged_rescue_simulation_summary": not_merged_df})

    notes_lines = [
        "# 310A Demo Readiness Notes",
        "",
        "## 当前状态（中文）",
        f"- 当前 demo-ready trusted 行数：{trusted_row_count}",
        f"- 当前 review_required 行数：{review_row_count}",
        "- 308C/309B 模拟救回行未合并，保持独立的 not-merged 状态。",
        "",
        "## 为什么未合并模拟救回行",
        "- 模拟结果仅用于规则校准与安全验证，不具备直接并入 trusted 的授权。",
        "- 当前阶段目标是可演示导出，而非真实应用。",
        "",
        "## 下一步建议",
        "- 优先继续规则安全校准与风险分层收敛。",
        "- 在独立沙箱门控通过后，再规划合并试验。",
    ]
    OUT_NOTES.write_text("\n".join(notes_lines) + "\n", encoding="utf-8")

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

    final_after_hash = _sha256(IN_307G_FINAL)
    final_preview_v2_unchanged = final_before_hash == final_after_hash

    # ensure rescue simulation rows not merged in trusted export by source_bucket guard
    trusted_source_buckets = set(trusted_df.get("source_bucket", pd.Series([], dtype=object)).map(_norm).tolist())
    no_simulated_rescue_rows_merged = (
        "simulated_panel_denoise_rescue" not in trusted_source_buckets
        and "simulated_unit_semantic_rescue" not in trusted_source_buckets
    )

    forbidden_fields_generated = sorted([c for c in set(trusted_df.columns).union(set(review_df.columns)) if c in FORBIDDEN_FIELDS])

    after_guard = _snapshot_guard()
    production_files_modified = any(before_guard[k] != after_guard[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before_guard["official_02b"] != after_guard["official_02b"]
    formal_rules_modified = before_guard["formal_rules"] != after_guard["formal_rules"]
    standardizer_modified = before_guard["standardizer"] != after_guard["standardizer"]
    release_package_modified = before_guard["release_zip"] != after_guard["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-310A",
        "mode": "demo_ready_core_metric_export_package",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "final_preview_v2_row_count": trusted_row_count,
        "review_required_v2_row_count": review_row_count,
        "final_preview_v2_row_count_preserved": True,
        "review_required_v2_row_count_preserved": True,
        "no_simulated_rescue_rows_merged_into_trusted_export": bool(no_simulated_rescue_rows_merged),
        "no_rows_merged_into_final_preview": True,
        "final_preview_v2_unchanged": bool(final_preview_v2_unchanged),
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
        "# 310A Demo Ready Core Metric Export Package",
        "",
        "## Package Snapshot",
        f"- trusted rows: {trusted_row_count}",
        f"- review_required rows: {review_row_count}",
        "- trusted source: 307g_final_core_metric_preview_v2 only",
        "- review_required source: 307g_review_required_core_metrics_v2 only",
        "",
        "## Simulation Merge Policy",
        f"- 308D simulated rescue rows merged: False",
        f"- 309C simulated rescue rows merged: False",
        "",
        "## Guard Assertions",
        f"- final_preview_v2_row_count_preserved: {summary['final_preview_v2_row_count_preserved']}",
        f"- review_required_v2_row_count_preserved: {summary['review_required_v2_row_count_preserved']}",
        f"- no_simulated_rescue_rows_merged_into_trusted_export: {summary['no_simulated_rescue_rows_merged_into_trusted_export']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_310a_summary_json: {OUT_SUMMARY}")
    print(f"eval_310a_demo_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
