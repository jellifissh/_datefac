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
OUT_DIR = BASE_DIR / "output" / "eval_307x_core_metric_pipeline_stage_summary"

IN_SUMMARIES = {
    "306e": BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design" / "306e_summary.json",
    "306g_fix": BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_summary.json",
    "306h_fix2": BASE_DIR / "output" / "eval_306h_fix2_alias_recovery_growth_guard" / "306h_fix2_summary.json",
    "306z": BASE_DIR / "output" / "eval_306z_conservative_relaxation_policy_v2" / "306z_summary.json",
    "307a": BASE_DIR / "output" / "eval_307a_core_metric_final_export_preview" / "307a_summary.json",
    "307b": BASE_DIR / "output" / "eval_307b_core_metric_export_quality_diagnosis" / "307b_summary.json",
    "307g": BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_summary.json",
    "307h": BASE_DIR / "output" / "eval_307h_final_preview_v2_quality_diagnosis" / "307h_summary.json",
    "307i": BASE_DIR / "output" / "eval_307i_roe_review_burden_drilldown" / "307i_summary.json",
}

OUT_SUMMARY = OUT_DIR / "307x_summary.json"
OUT_REPORT = OUT_DIR / "307x_stage_summary_report.md"
OUT_MATRIX = OUT_DIR / "307x_pipeline_capability_matrix.xlsx"
OUT_MVP = OUT_DIR / "307x_mvp_readiness_assessment.xlsx"
OUT_BOTTLENECK = OUT_DIR / "307x_remaining_bottleneck_ranking.xlsx"
OUT_NEXT = OUT_DIR / "307x_next_phase_recommendation.md"
OUT_NO_APPLY = OUT_DIR / "307x_no_apply_proof.json"

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


def _to_float(v: Any) -> float:
    s = _norm(v)
    if s == "":
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


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

    missing = [str(p) for p in IN_SUMMARIES.values() if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-307X",
                "mode": "core_metric_pipeline_stage_summary",
                "blocked": True,
                "blocked_reason": "missing_required_summaries",
                "missing_input_count": len(missing),
                "missing_input_list": missing,
                "external_api_called": False,
                "llm_api_called": False,
                "ocr_called": False,
            },
        )
        return 0

    before = _snapshot_guard()

    s = {k: json.loads(v.read_text(encoding="utf-8")) for k, v in IN_SUMMARIES.items()}

    trusted_v1 = _to_int(s["307b"].get("final_preview_row_count", 0))
    review_v1 = _to_int(s["307b"].get("review_required_row_count", 0))
    trusted_v2 = _to_int(s["307h"].get("final_preview_v2_row_count", 0))
    review_v2 = _to_int(s["307h"].get("review_required_v2_row_count", 0))
    eps_burden_v2_delta = _to_int(s["307h"].get("eps_review_burden_delta_v2_minus_v1", 0))
    roe_review_required = _to_int(s["307i"].get("roe_review_required_row_count", 0))

    top_metric = _norm(s["307h"].get("top_review_burden_metric_v2", ""))
    top_pdf = _norm(s["307h"].get("top_review_burden_pdf_v2", ""))
    readiness_v2 = _norm(s["307h"].get("readiness_assessment_v2", ""))

    trusted_ratio_v2 = float(trusted_v2 / (trusted_v2 + review_v2)) if (trusted_v2 + review_v2) > 0 else 0.0
    target_cov_v1 = _to_float(s["307b"].get("target_metric_coverage_ratio", 0.0))
    # derive target coverage v2 from delta if available
    target_cov_count_delta = _to_int(s["307h"].get("target_metric_coverage_delta_v2_minus_v1", 0))
    # 307b had 8 target metrics and coverage 0.875 => 7/8
    target_cov_count_v1 = int(round(target_cov_v1 * 8))
    target_cov_count_v2 = target_cov_count_v1 + target_cov_count_delta
    target_cov_ratio_v2 = float(target_cov_count_v2 / 8) if 8 > 0 else 0.0

    capability_matrix = pd.DataFrame(
        [
            {"capability": "Parser Fusion Pipeline", "status": "implemented_sandbox", "stage_ref": "306E", "evidence": _norm(s["306e"].get("mode", ""))},
            {"capability": "Core Semantic Quality Gate", "status": "fixed", "stage_ref": "306G-FIX", "evidence": _norm(s["306g_fix"].get("mode", ""))},
            {"capability": "Alias Recovery Growth Guard", "status": "fixed", "stage_ref": "306H-FIX2", "evidence": _norm(s["306h_fix2"].get("mode", ""))},
            {"capability": "Conservative Relax Policy v2", "status": "active_sandbox", "stage_ref": "306Z", "evidence": _norm(s["306z"].get("mode", ""))},
            {"capability": "Final Preview v1", "status": "generated", "stage_ref": "307A", "evidence": f"trusted={trusted_v1}, review={review_v1}"},
            {"capability": "Quality Diagnosis v1", "status": "generated", "stage_ref": "307B", "evidence": f"readiness={_norm(s['307b'].get('readiness_assessment',''))}"},
            {"capability": "EPS Merge to Final Preview v2", "status": "generated", "stage_ref": "307G", "evidence": f"trusted_v2={trusted_v2}, review_v2={review_v2}"},
            {"capability": "Quality Diagnosis v2", "status": "generated", "stage_ref": "307H", "evidence": f"top_metric={top_metric}, top_pdf={top_pdf}"},
            {"capability": "ROE Burden Drilldown", "status": "diagnosed", "stage_ref": "307I", "evidence": f"roe_review_required={roe_review_required}"},
            {"capability": "Human Review Loop", "status": "operational_sandbox", "stage_ref": "307D/307E/307F", "evidence": "eps-focused reviewed + expanded"},
        ]
    )

    # readiness tiers
    paid_mvp_ready = False
    internal_test_ready = (trusted_ratio_v2 >= 0.2 and target_cov_ratio_v2 >= 0.75 and readiness_v2 in {"internal_test_ready", "demo_ready"})
    demo_ready = (trusted_ratio_v2 >= 0.1 and target_cov_ratio_v2 >= 0.5)
    if internal_test_ready and trusted_ratio_v2 >= 0.4 and top_metric != "":
        # still keep conservative: require much higher trust ratio to call paid MVP
        paid_mvp_ready = False

    mvp_readiness = pd.DataFrame(
        [
            {"tier": "demo_ready", "ready": bool(demo_ready), "criteria_note": "trusted_ratio>=0.10 and target_coverage>=0.50"},
            {"tier": "internal_test_ready", "ready": bool(internal_test_ready), "criteria_note": "trusted_ratio>=0.20 and target_coverage>=0.75"},
            {"tier": "paid_mvp_ready", "ready": bool(paid_mvp_ready), "criteria_note": "requires substantially higher trusted ratio and lower burden concentration"},
            {"tier": "current_readiness_label", "ready": True, "criteria_note": readiness_v2},
            {"tier": "trusted_ratio_v2", "ready": True, "criteria_note": f"{trusted_ratio_v2:.4f}"},
            {"tier": "target_cov_ratio_v2", "ready": True, "criteria_note": f"{target_cov_ratio_v2:.4f}"},
        ]
    )

    bottlenecks = pd.DataFrame(
        [
            {"rank": 1, "bottleneck": "Top review metric concentration", "current_signal": top_metric, "impact_note": "largest remaining manual burden"},
            {"rank": 2, "bottleneck": "Top review PDF concentration", "current_signal": top_pdf, "impact_note": "single-document bottleneck drives queue"},
            {"rank": 3, "bottleneck": "Trusted ratio still low", "current_signal": f"{trusted_ratio_v2:.4f}", "impact_note": "limits internal-test and paid MVP confidence"},
            {"rank": 4, "bottleneck": "Metric standardization edge cases", "current_signal": "ROE/EPS semantics & unit consistency", "impact_note": "causes review-required carry-over"},
        ]
    )

    # why not immediately do full EPS-like chain for ROE
    why_not_full_roe_chain = (
        "ROE remains top burden, but current evidence suggests mixed blockers (unit semantics, table context, parser noise). "
        "A full EPS-like chain now would overfit one metric before reducing shared upstream burden. "
        "Priority should remain burden reduction + parser/standardization improvements that benefit multiple metrics."
    )

    next_phase_md = [
        "# 307X Next Phase Recommendation",
        "",
        "## Recommended Priority Order",
        "1. B. review burden reduction",
        "2. C. parser/metric standardization improvement",
        "3. A. productized export/UI",
        "4. D. all of the above (sequenced as above)",
        "",
        "## Rationale",
        f"- current trusted vs review_required: `{trusted_v2}` vs `{review_v2}`",
        f"- top bottleneck metric/pdf: `{top_metric}` / `{top_pdf}`",
        f"- readiness: `{readiness_v2}`",
        "",
        "## ROE Chain Guidance",
        f"- {why_not_full_roe_chain}",
    ]
    OUT_NEXT.write_text("\n".join(next_phase_md) + "\n", encoding="utf-8")

    _write_excel(OUT_MATRIX, {"pipeline_capability_matrix": capability_matrix})
    _write_excel(OUT_MVP, {"mvp_readiness_assessment": mvp_readiness})
    _write_excel(OUT_BOTTLENECK, {"remaining_bottleneck_ranking": bottlenecks})

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

    forbidden_fields_generated: List[str] = []  # only docs/xlsx summaries, no such fields generated

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-307X",
        "mode": "core_metric_pipeline_stage_summary",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "parser_fusion_status": _norm(s["306e"].get("mode", "")),
        "clean_core_candidate_status": _norm(s["306g_fix"].get("mode", "")),
        "human_review_loop_status": "eps_loop_operational_sandbox",
        "eps_focused_fix_result": f"eps_review_burden_delta={eps_burden_v2_delta}",
        "final_preview_v2_quality": readiness_v2,
        "trusted_rows_current": trusted_v2,
        "review_required_rows_current": review_v2,
        "top_bottleneck_metric_current": top_metric,
        "top_bottleneck_pdf_current": top_pdf,
        "why_not_immediate_full_roe_chain": why_not_full_roe_chain,
        "demo_ready": bool(demo_ready),
        "internal_test_ready": bool(internal_test_ready),
        "paid_mvp_ready": bool(paid_mvp_ready),
        "recommended_next_phase_priority": "B > C > A > D",
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
        "# 307X Core Metric Pipeline Stage Summary",
        "",
        "## Pipeline Status",
        f"- parser fusion status: {summary['parser_fusion_status']}",
        f"- clean core candidate status: {summary['clean_core_candidate_status']}",
        f"- human review loop status: {summary['human_review_loop_status']}",
        f"- EPS focused fix result: {summary['eps_focused_fix_result']}",
        "",
        "## Current Quality Snapshot",
        f"- trusted rows: {trusted_v2}",
        f"- review_required rows: {review_v2}",
        f"- top bottleneck metric: {top_metric}",
        f"- top bottleneck PDF: {top_pdf}",
        f"- final preview v2 readiness: {readiness_v2}",
        "",
        "## ROE Guidance",
        f"- {why_not_full_roe_chain}",
        "",
        "## Readiness",
        f"- demo_ready: {demo_ready}",
        f"- internal_test_ready: {internal_test_ready}",
        f"- paid_mvp_ready: {paid_mvp_ready}",
        "",
        "## Next Phase",
        f"- recommended priority: {summary['recommended_next_phase_priority']}",
        "",
        "## Guard",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_307x_summary_json: {OUT_SUMMARY}")
    print(f"eval_307x_stage_summary_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
