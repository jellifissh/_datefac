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
OUT_DIR = BASE_DIR / "output" / "eval_310d_demo_package_acceptance_report"

IN_WORKBOOK = BASE_DIR / "output" / "eval_310c_readable_demo_export_layout_generation" / "310c_readable_demo_core_metric_export.xlsx"
IN_310C_SUMMARY = BASE_DIR / "output" / "eval_310c_readable_demo_export_layout_generation" / "310c_summary.json"
IN_310C_LAYOUT_AUDIT = BASE_DIR / "output" / "eval_310c_readable_demo_export_layout_generation" / "310c_export_layout_audit.xlsx"
IN_310B_SUMMARY = BASE_DIR / "output" / "eval_310b_demo_export_qa_and_readability_check" / "310b_summary.json"
IN_310A_SUMMARY = BASE_DIR / "output" / "eval_310a_demo_ready_core_metric_export_package" / "310a_summary.json"
IN_307X_REPORT = BASE_DIR / "output" / "eval_307x_core_metric_pipeline_stage_summary" / "307x_stage_summary_report.md"

OUT_SUMMARY = OUT_DIR / "310d_summary.json"
OUT_REPORT = OUT_DIR / "310d_acceptance_report.md"
OUT_WALKTHROUGH = OUT_DIR / "310d_demo_walkthrough.md"
OUT_CHECKLIST = OUT_DIR / "310d_demo_acceptance_checklist.xlsx"
OUT_LIMITATIONS = OUT_DIR / "310d_known_limitations.md"
OUT_ROADMAP = OUT_DIR / "310d_next_phase_roadmap.md"
OUT_NO_APPLY = OUT_DIR / "310d_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
EXPECTED_TRUSTED = 70
EXPECTED_REVIEW = 342


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    s = _norm(v).lower()
    return s in {"1", "true", "yes", "y"}


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


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_sheet(path: Path, preferred: str | None = None) -> pd.DataFrame:
    xls = pd.ExcelFile(path)
    if preferred and preferred in xls.sheet_names:
        return pd.read_excel(path, sheet_name=preferred).fillna("")
    return pd.read_excel(path, sheet_name=xls.sheet_names[0]).fillna("")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_WORKBOOK,
        IN_310C_SUMMARY,
        IN_310C_LAYOUT_AUDIT,
        IN_310B_SUMMARY,
        IN_310A_SUMMARY,
        IN_307X_REPORT,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-310D",
                "mode": "demo_package_acceptance_report",
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

    s310c = _read_json(IN_310C_SUMMARY)
    s310b = _read_json(IN_310B_SUMMARY)
    s310a = _read_json(IN_310A_SUMMARY)
    stage_report_307x = IN_307X_REPORT.read_text(encoding="utf-8")

    wb = pd.ExcelFile(IN_WORKBOOK)
    sheet_list = wb.sheet_names

    trusted_df = pd.read_excel(IN_WORKBOOK, sheet_name="原始可信明细_审计用").fillna("") if "原始可信明细_审计用" in sheet_list else pd.DataFrame()
    review_df = pd.read_excel(IN_WORKBOOK, sheet_name="原始待复核明细_审计用").fillna("") if "原始待复核明细_审计用" in sheet_list else pd.DataFrame()

    trusted_row_count = int(len(trusted_df))
    review_row_count = int(len(review_df))

    trusted_source_buckets = set(trusted_df.get("source_bucket", pd.Series([], dtype=object)).map(_norm).tolist()) if not trusted_df.empty else set()
    no_simulated_rescue_rows_merged = (
        "simulated_panel_denoise_rescue" not in trusted_source_buckets
        and "simulated_unit_semantic_rescue" not in trusted_source_buckets
    )

    forbidden_fields_found = sorted([c for c in set(trusted_df.columns).union(set(review_df.columns)) if c in FORBIDDEN_FIELDS])

    layout_audit_df = _read_sheet(IN_310C_LAYOUT_AUDIT, "export_layout_audit")
    layout_order_ok = False
    if not layout_audit_df.empty and "check_item" in layout_audit_df.columns and "result" in layout_audit_df.columns:
        m = layout_audit_df[layout_audit_df["check_item"].astype(str) == "sheet_order_match_required"]
        if len(m) > 0:
            layout_order_ok = _to_bool(m.iloc[0]["result"])

    readiness_label = "demo_ready" if _norm(s310b.get("readiness_status")) in {"demo_ready", "needs_readability_fix"} and _to_bool(s310c.get("required_sheet_order_match")) else "not_ready"

    checklist_rows = [
        {
            "check_item": "readable_workbook_exists",
            "result": bool(IN_WORKBOOK.exists()),
            "detail": str(IN_WORKBOOK),
        },
        {
            "check_item": "trusted_row_count_preserved",
            "result": bool(trusted_row_count == EXPECTED_TRUSTED),
            "detail": trusted_row_count,
        },
        {
            "check_item": "review_required_row_count_preserved",
            "result": bool(review_row_count == EXPECTED_REVIEW),
            "detail": review_row_count,
        },
        {
            "check_item": "no_simulated_rescue_rows_merged",
            "result": bool(no_simulated_rescue_rows_merged),
            "detail": "source_bucket guard",
        },
        {
            "check_item": "no_safe_to_apply_or_approve_for_real_apply_fields_generated",
            "result": bool(len(forbidden_fields_found) == 0),
            "detail": "|".join(forbidden_fields_found),
        },
        {
            "check_item": "readable_workbook_sheet_order_verified",
            "result": bool(layout_order_ok),
            "detail": "from 310c_export_layout_audit.xlsx",
        },
    ]

    can_demo_lines = [
        "可信核心指标与待复核池的双轨输出结构（trusted/review_required split）。",
        "当前可信数据规模与覆盖结构（70 条可信核心指标，342 条待复核）。",
        "每条可信数据的来源追溯字段（来源分组、解析器、页码、文件名、指标、年份、单位）。",
        "当前规则下为何保持模拟救援结果不并入可信导出。",
    ]

    must_not_claim_lines = [
        "不得宣称系统已达到生产可自动应用（production apply）状态。",
        "不得宣称待复核已清零或无需人工复核。",
        "不得宣称 308C/309B 模拟救援结果已通过最终合并验证。",
        "不得宣称当前结果可替代完整人工财务审校。",
    ]

    acceptance_lines = [
        "# 310D Demo Package Acceptance Report",
        "",
        "## Demo Workbook",
        f"- workbook_path: `{IN_WORKBOOK}`",
        f"- trusted_row_count: {trusted_row_count}",
        f"- review_required_row_count: {review_row_count}",
        f"- readiness_label: {readiness_label}",
        "",
        "## Readable Workbook Sheets",
    ]
    acceptance_lines.extend([f"- {s}" for s in sheet_list])
    acceptance_lines.extend(
        [
            "",
            "## Why Simulated Rescue Rows Are Not Merged",
            "- 308C/309B 结果属于 sandbox 规则模拟，仅用于风险评估与影响估计。",
            "- 这些行尚未完成最终安全校准闭环，不满足可信导出并入条件。",
            "- 当前策略保持 trusted 数据稳定，避免将潜在静默风险带入 demo 主视图。",
            "",
            "## What Can Be Safely Demonstrated",
        ]
    )
    acceptance_lines.extend([f"- {x}" for x in can_demo_lines])
    acceptance_lines.extend(["", "## What Must Not Be Claimed"])
    acceptance_lines.extend([f"- {x}" for x in must_not_claim_lines])
    acceptance_lines.extend(
        [
            "",
            "## Current Context",
            f"- 310A summary trusted/review: {s310a.get('final_preview_v2_row_count')} / {s310a.get('review_required_v2_row_count')}",
            f"- 310B readiness_status: {s310b.get('readiness_status')}",
            f"- 310C readable_workbook_generated: {s310c.get('readable_workbook_generated')}",
            f"- 307X stage readiness snippet: {'demo_ready: True' if 'demo_ready: True' in stage_report_307x else 'demo_ready status refer 307x report'}",
        ]
    )
    OUT_REPORT.write_text("\n".join(acceptance_lines) + "\n", encoding="utf-8")

    walkthrough_lines = [
        "# 310D Demo Walkthrough",
        "",
        "## 1) Opening",
        f"- 打开 `{IN_WORKBOOK}`，先讲解“使用说明”页。",
        "",
        "## 2) Trusted Core Metrics",
        "- 切到“可信核心指标_宽表”展示按年份透视后的核心指标趋势。",
        "- 切到“可信核心指标_明细”解释来源分组、解析器、来源页码等追溯信息。",
        "",
        "## 3) Coverage",
        "- 在“PDF覆盖率”“指标覆盖率”页说明当前覆盖现状与空白点。",
        "",
        "## 4) Review Required",
        "- 进入“待复核摘要”，强调 342 条待复核仍独立保留，未并入可信池。",
        "",
        "## 5) Simulation Separation",
        "- 展示“未合并模拟救援说明”页，说明 308C/309B 仅为模拟校准，不做可信合并。",
        "",
        "## 6) Auditability",
        "- 最后展示两张审计用原始明细页，确认成员关系未变、可追溯。",
    ]
    OUT_WALKTHROUGH.write_text("\n".join(walkthrough_lines) + "\n", encoding="utf-8")

    limitations_lines = [
        "# 310D Known Limitations",
        "",
        "- 当前仍有 342 条待复核，尚未达到内部测试可自动消费的稳定门槛。",
        "- 模拟救援规则（面板去噪、单位语义补全）未进入可信合并闭环。",
        "- 证据展示仍以表格字段为主，页面级视觉证据呈现能力有限。",
        "- 高负担指标（如 ROE）仍受多类阻塞因子叠加影响。",
        "- 本包仅用于 demo 与沟通，不可作为生产 apply 依据。",
    ]
    OUT_LIMITATIONS.write_text("\n".join(limitations_lines) + "\n", encoding="utf-8")

    roadmap_lines = [
        "# 310D Next Phase Roadmap",
        "",
        "1. reduce review_required through safer parser/standardizer improvements",
        "- 优先处理跨指标共性阻塞：panel 噪声、单位语义、年份连续性守卫。",
        "",
        "2. improve evidence/source page display",
        "- 增强来源页与证据说明可视化，降低人工复核上下文切换成本。",
        "",
        "3. build lightweight UI around trusted/review_required split",
        "- 提供可信与待复核双池浏览、筛选、导出与审计联动。",
        "",
        "4. later consider production apply only after validation",
        "- 仅在模拟规则通过安全验证、冲突审计稳定、回归持续 PASS 后再评估。",
    ]
    OUT_ROADMAP.write_text("\n".join(roadmap_lines) + "\n", encoding="utf-8")

    checklist_df = pd.DataFrame(checklist_rows)
    _write_excel(OUT_CHECKLIST, {"demo_acceptance_checklist": checklist_df})

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

    after_guard = _snapshot_guard()
    production_files_modified = any(before_guard[k] != after_guard[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before_guard["official_02b"] != after_guard["official_02b"]
    formal_rules_modified = before_guard["formal_rules"] != after_guard["formal_rules"]
    standardizer_modified = before_guard["standardizer"] != after_guard["standardizer"]
    release_package_modified = before_guard["release_zip"] != after_guard["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-310D",
        "mode": "demo_package_acceptance_report",
        "demo_workbook_path": str(IN_WORKBOOK),
        "readable_workbook_exists": bool(IN_WORKBOOK.exists()),
        "trusted_row_count": trusted_row_count,
        "review_required_row_count": review_row_count,
        "trusted_row_count_preserved": bool(trusted_row_count == EXPECTED_TRUSTED),
        "review_required_row_count_preserved": bool(review_row_count == EXPECTED_REVIEW),
        "readable_workbook_sheet_list": sheet_list,
        "no_simulated_rescue_rows_merged": bool(no_simulated_rescue_rows_merged),
        "current_demo_readiness_label": readiness_label,
        "no_safe_to_apply_or_approve_for_real_apply_fields_generated": bool(len(forbidden_fields_found) == 0),
        "forbidden_fields_generated": forbidden_fields_found,
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "check_delivery_state_overall_status": delivery_status,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
    }
    _write_json(OUT_SUMMARY, summary)

    print(f"eval_310d_summary_json: {OUT_SUMMARY}")
    print(f"eval_310d_acceptance_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
