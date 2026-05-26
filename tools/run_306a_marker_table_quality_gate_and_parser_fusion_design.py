from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_306a_marker_table_quality_gate_and_parser_fusion_design"

IN_305B_SUMMARY = BASE_DIR / "output" / "eval_marker1b_html_table_readable_render_fix" / "305b_summary.json"
IN_305B_INDEX = BASE_DIR / "output" / "eval_marker1b_html_table_readable_render_fix" / "305b_table_render_index.xlsx"
IN_304_SUMMARY = BASE_DIR / "output" / "eval_marker1_no_llm_parser_benchmark" / "304_eval_marker1_no_llm_benchmark_summary.json"
IN_304_INV = BASE_DIR / "output" / "eval_marker1_no_llm_parser_benchmark" / "304_eval_marker1_marker_table_inventory.xlsx"
IN_304_CMP = BASE_DIR / "output" / "eval_marker1_no_llm_parser_benchmark" / "304_eval_marker1_pdfplumber_vs_marker_comparison.xlsx"
IN_302_PER_PDF = BASE_DIR / "output" / "eval1b_profile_selection_fix_regression" / "302_eval1b_per_pdf_metrics.xlsx"

OUT_SUMMARY = OUT_DIR / "306a_summary.json"
OUT_REPORT = OUT_DIR / "306a_report.md"
OUT_GATE = OUT_DIR / "306a_marker_table_quality_gate.xlsx"
OUT_HIGH_VALUE = OUT_DIR / "306a_high_value_marker_tables.xlsx"
OUT_JUNK = OUT_DIR / "306a_junk_or_low_value_tables.xlsx"
OUT_MULTI_PANEL = OUT_DIR / "306a_multi_panel_candidates.xlsx"
OUT_FUSION_MD = OUT_DIR / "306a_parser_fusion_recommendation.md"
OUT_FUSION_JSON = OUT_DIR / "306a_parser_fusion_recommendation.json"
OUT_NO_APPLY = OUT_DIR / "306a_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"


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


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
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
    used: set = set()
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


def _contains_any(text: str, patterns: List[str]) -> bool:
    t = _norm(text).lower()
    if not t:
        return False
    for p in patterns:
        if re.search(p, t, flags=re.IGNORECASE):
            return True
    return False


def _classify_row(r: Dict[str, Any]) -> str:
    if _to_bool(r["empty_shell_table"]) or _to_bool(r["disclaimer_rating_contact_table"]):
        return "low_value_or_junk"
    if _to_bool(r["multi_panel_wide_table"]):
        if _norm(r["render_status"]).startswith("FAILED"):
            return "manual_inspection_required"
        return "multi_panel_split_required"
    if _norm(r["render_status"]).startswith("FAILED") and (
        _to_bool(r["high_value_financial_forecast_table"])
        or _to_bool(r["financial_summary_table"])
        or _to_bool(r["has_financial_panel"])
    ):
        return "manual_inspection_required"
    if _to_bool(r["high_value_financial_forecast_table"]) and _to_int(r["quality_gate_score"]) >= 70:
        return "direct_structurable"
    if _to_bool(r["has_financial_panel"]) and _to_int(r["structure_score"]) >= 60 and _to_int(r["quality_gate_score"]) >= 60:
        return "direct_structurable"
    if _to_bool(r["business_assumption_table"]) or _to_bool(r["financial_summary_table"]):
        return "context_required"
    if _to_bool(r["contains_financial_keywords"]) and _to_int(r["parsed_table_count"]) > 0:
        return "context_required"
    if _norm(r["render_status"]).startswith("FAILED"):
        return "manual_inspection_required"
    return "low_value_or_junk"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_305B_SUMMARY, IN_305B_INDEX, IN_304_SUMMARY, IN_304_INV, IN_304_CMP, IN_302_PER_PDF]
    missing = [str(x) for x in required if not x.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306A",
                "mode": "marker_table_quality_gate_and_parser_fusion_design",
                "blocked": True,
                "blocked_reason": "missing_required_inputs",
                "missing_input_count": len(missing),
                "missing_input_list": missing,
                "external_api_called": False,
                "llm_api_called": False,
                "ocr_called": False,
                "marker_rerun_executed": False,
            },
        )
        return 0

    before = _snapshot_guard()

    s305b = json.loads(IN_305B_SUMMARY.read_text(encoding="utf-8"))
    s304 = json.loads(IN_304_SUMMARY.read_text(encoding="utf-8"))
    d305b = pd.read_excel(IN_305B_INDEX).fillna("")
    d304_inv = pd.read_excel(IN_304_INV).fillna("")
    d304_cmp = pd.read_excel(IN_304_CMP).fillna("")
    d302 = pd.read_excel(IN_302_PER_PDF).fillna("")

    for df in [d305b, d304_inv]:
        df["pdf_file_name"] = df["pdf_file_name"].map(_norm)
        df["marker_table_id"] = df["marker_table_id"].map(_norm)
        if "page_number" in df.columns:
            df["page_number"] = df["page_number"].map(_to_int)

    merged = d305b.merge(
        d304_inv,
        on=["pdf_file_name", "marker_table_id", "page_number"],
        how="left",
        suffixes=("_305b", "_304"),
    )

    out_rows: List[Dict[str, Any]] = []
    forecast_kw = [r"盈利预测", r"财务预测", r"forecast", r"关键财务与估值指标"]
    summary_kw = [r"财务指标", r"summary", r"核心观点", r"关键财务"]
    bs_kw = [r"资产负债表", r"balance\s*sheet", r"资产总计", r"负债合计"]
    is_kw = [r"利润表", r"income\s*statement", r"营业收入", r"净利润", r"归母净利润"]
    cf_kw = [r"现金流量表", r"cash\s*flow", r"经营活动现金流", r"经营现金流"]
    val_kw = [r"市盈率", r"\bp/e\b", r"\bpe\b", r"市净率", r"\bp/b\b", r"\bpb\b", r"ev/ebitda", r"估值"]
    business_kw = [r"业务假设", r"正面银浆业务", r"空白掩模版业务", r"其他主营业务", r"同比增长率"]
    junk_kw = [r"投资评级", r"评级标准", r"免责声明", r"法律声明", r"联系人", r"联系方式", r"电话", r"邮箱", r"地址"]

    for _, row in merged.iterrows():
        text = _norm(row.get("table_text_preview_305b")) or _norm(row.get("table_text_preview_304"))
        row_count = _to_int(row.get("row_count", 0))
        col_count = _to_int(row.get("col_count", 0))
        parsed_count = _to_int(row.get("parsed_table_count", 0))
        render_status = _norm(row.get("render_status", ""))
        contains_fin = _to_bool(row.get("contains_financial_keywords", False))
        contains_core = _to_bool(row.get("contains_core_metric_keywords", False))
        contains_year = _to_bool(row.get("contains_year_headers", False))
        suspected_multi = _to_bool(row.get("suspected_multi_panel", False))

        high_value_forecast = _contains_any(text, forecast_kw) and (_contains_any(text, val_kw) or _contains_any(text, is_kw))
        financial_summary = _contains_any(text, summary_kw)
        balance_sheet_panel = _contains_any(text, bs_kw)
        income_statement_panel = _contains_any(text, is_kw)
        cash_flow_panel = _contains_any(text, cf_kw)
        valuation_panel = _contains_any(text, val_kw)
        business_assumption_table = _contains_any(text, business_kw)
        disclaimer_rating_contact_table = _contains_any(text, junk_kw)
        empty_shell_table = bool((parsed_count == 0 and row_count <= 1) or (row_count <= 1 and col_count <= 1 and _norm(text) == ""))
        multi_panel_wide_table = bool(
            suspected_multi
            or ((balance_sheet_panel and income_statement_panel) or (income_statement_panel and cash_flow_panel))
            or (col_count >= 10 and sum([balance_sheet_panel, income_statement_panel, cash_flow_panel, valuation_panel]) >= 2)
        )

        has_financial_panel = bool(balance_sheet_panel or income_statement_panel or cash_flow_panel or valuation_panel)
        high_value_financial_table = bool(high_value_forecast or financial_summary or has_financial_panel or business_assumption_table)

        structure_score = 0
        structure_score += 40 if render_status == "SUCCESS" else 5
        structure_score += 20 if parsed_count >= 1 else 0
        structure_score += 10 if parsed_count >= 2 else 0
        structure_score += 10 if row_count >= 5 else 0
        structure_score += 10 if col_count >= 4 else 0
        structure_score -= 10 if empty_shell_table else 0
        structure_score -= 10 if render_status.startswith("FAILED") else 0
        structure_score = max(0, min(100, structure_score))

        finance_signal_score = 0
        finance_signal_score += 25 if contains_fin else 0
        finance_signal_score += 20 if contains_core else 0
        finance_signal_score += 15 if contains_year else 0
        finance_signal_score += 15 if high_value_forecast else 0
        finance_signal_score += 10 if financial_summary else 0
        finance_signal_score += 10 if has_financial_panel else 0
        finance_signal_score += 10 if valuation_panel else 0
        finance_signal_score -= 20 if disclaimer_rating_contact_table else 0
        finance_signal_score = max(0, min(100, finance_signal_score))

        quality_gate_score = round(0.6 * structure_score + 0.4 * finance_signal_score, 1)

        row_out = {
            "pdf_file_name": _norm(row.get("pdf_file_name")),
            "page_number": _to_int(row.get("page_number", 0)),
            "marker_table_id": _norm(row.get("marker_table_id")),
            "block_type": _norm(row.get("block_type_305b")) or _norm(row.get("block_type_304")),
            "render_status": render_status,
            "parser_used": _norm(row.get("parser_used", "")),
            "parsed_table_count": parsed_count,
            "row_count": row_count,
            "col_count": col_count,
            "contains_financial_keywords": contains_fin,
            "contains_core_metric_keywords": contains_core,
            "contains_year_headers": contains_year,
            "suspected_multi_panel": suspected_multi,
            "table_text_preview": text,
            "high_value_financial_forecast_table": high_value_forecast,
            "financial_summary_table": financial_summary,
            "balance_sheet_panel": balance_sheet_panel,
            "income_statement_panel": income_statement_panel,
            "cash_flow_panel": cash_flow_panel,
            "valuation_panel": valuation_panel,
            "business_assumption_table": business_assumption_table,
            "empty_shell_table": empty_shell_table,
            "disclaimer_rating_contact_table": disclaimer_rating_contact_table,
            "multi_panel_wide_table": multi_panel_wide_table,
            "has_financial_panel": has_financial_panel,
            "high_value_financial_table": high_value_financial_table,
            "structure_score": structure_score,
            "finance_signal_score": finance_signal_score,
            "quality_gate_score": quality_gate_score,
        }
        row_out["table_classification"] = _classify_row(row_out)
        out_rows.append(row_out)

    gate_df = pd.DataFrame(out_rows).fillna("")
    class_counts = gate_df["table_classification"].value_counts().to_dict()
    high_value_df = gate_df[gate_df["high_value_financial_table"] == True].copy()
    junk_df = gate_df[gate_df["table_classification"] == "low_value_or_junk"].copy()
    multi_panel_df = gate_df[(gate_df["multi_panel_wide_table"] == True) | (gate_df["table_classification"] == "multi_panel_split_required")].copy()

    _write_excel(
        OUT_GATE,
        {
            "quality_gate": gate_df,
            "class_counts": pd.DataFrame(
                [{"table_classification": k, "count": int(v)} for k, v in sorted(class_counts.items())]
            ),
        },
    )
    _write_excel(OUT_HIGH_VALUE, {"high_value_marker_tables": high_value_df})
    _write_excel(OUT_JUNK, {"junk_or_low_value_tables": junk_df})
    _write_excel(OUT_MULTI_PANEL, {"multi_panel_candidates": multi_panel_df})

    # Parser fusion planning
    cmp_df = d304_cmp.copy()
    cmp_df["pdf_file_name"] = cmp_df["pdf_file_name"].map(_norm)
    gate_per_pdf = gate_df.groupby("pdf_file_name").agg(
        marker_table_count=("marker_table_id", "count"),
        direct_structurable_count=("table_classification", lambda s: int((s == "direct_structurable").sum())),
        multi_panel_split_required_count=("table_classification", lambda s: int((s == "multi_panel_split_required").sum())),
        context_required_count=("table_classification", lambda s: int((s == "context_required").sum())),
        low_value_or_junk_count=("table_classification", lambda s: int((s == "low_value_or_junk").sum())),
        manual_inspection_required_count=("table_classification", lambda s: int((s == "manual_inspection_required").sum())),
        high_value_count=("high_value_financial_table", "sum"),
        failed_render_count=("render_status", lambda s: int((s != "SUCCESS").sum())),
    ).reset_index()

    fusion_df = cmp_df.merge(gate_per_pdf, on="pdf_file_name", how="left").fillna(0)
    rec_rows: List[Dict[str, Any]] = []
    for _, r in fusion_df.iterrows():
        marker_better = _to_bool(r.get("marker_better_for_complex_layout_candidate", False))
        pdfplumber_zero = _to_bool(r.get("pdfplumber_zero_candidate", False))
        multi_cnt = _to_int(r.get("multi_panel_split_required_count", 0))
        manual_cnt = _to_int(r.get("manual_inspection_required_count", 0))
        direct_cnt = _to_int(r.get("direct_structurable_count", 0))
        high_cnt = _to_int(r.get("high_value_count", 0))

        if (multi_cnt + manual_cnt >= 2) and marker_better:
            rec = "use_parser_fusion"
        elif pdfplumber_zero and high_cnt > 0:
            rec = "marker_priority_with_pdfplumber_backfill"
        elif direct_cnt > 0 and not marker_better:
            rec = "keep_pdfplumber_primary_marker_secondary"
        else:
            rec = "pdfplumber_primary_with_targeted_marker_fallback"

        rec_rows.append(
            {
                "pdf_file_name": _norm(r.get("pdf_file_name")),
                "marker_better_for_complex_layout_candidate": marker_better,
                "pdfplumber_zero_candidate": pdfplumber_zero,
                "direct_structurable_count": direct_cnt,
                "multi_panel_split_required_count": multi_cnt,
                "manual_inspection_required_count": manual_cnt,
                "high_value_count": high_cnt,
                "recommended_parser_strategy": rec,
            }
        )

    rec_df = pd.DataFrame(rec_rows).fillna("")
    parser_fusion_recommended = bool((rec_df["recommended_parser_strategy"] == "use_parser_fusion").any())
    strategy_counts = rec_df["recommended_parser_strategy"].value_counts().to_dict()

    rec_json = {
        "stage": "EVAL-306A",
        "parser_fusion_recommended": parser_fusion_recommended,
        "strategy_counts": {k: int(v) for k, v in strategy_counts.items()},
        "default_policy": {
            "direct_structurable": "prefer_marker_direct_structuring",
            "multi_panel_split_required": "route_to_multi_panel_splitter_and_compare_with_pdfplumber",
            "context_required": "apply_title_context_propagation_then_re-score",
            "low_value_or_junk": "filter_out_from_candidate_pipeline",
            "manual_inspection_required": "manual_review_before_any_structuring",
        },
        "per_pdf_recommendation": rec_rows,
    }
    _write_json(OUT_FUSION_JSON, rec_json)

    fusion_md_lines = [
        "# 306A Parser Fusion Recommendation",
        "",
        f"- parser_fusion_recommended: {parser_fusion_recommended}",
        f"- marker_table_total: {len(gate_df)}",
        f"- direct_structurable_count: {int((gate_df['table_classification'] == 'direct_structurable').sum())}",
        f"- multi_panel_split_required_count: {int((gate_df['table_classification'] == 'multi_panel_split_required').sum())}",
        f"- context_required_count: {int((gate_df['table_classification'] == 'context_required').sum())}",
        f"- low_value_or_junk_count: {int((gate_df['table_classification'] == 'low_value_or_junk').sum())}",
        f"- manual_inspection_required_count: {int((gate_df['table_classification'] == 'manual_inspection_required').sum())}",
        "",
        "## Strategy Counts",
    ]
    for k, v in strategy_counts.items():
        fusion_md_lines.append(f"- {k}: {int(v)}")
    fusion_md_lines.append("")
    fusion_md_lines.append("## Per-PDF Recommendation")
    for _, r in rec_df.iterrows():
        fusion_md_lines.append(
            f"- {_norm(r['pdf_file_name'])}: {_norm(r['recommended_parser_strategy'])}"
        )
    OUT_FUSION_MD.write_text("\n".join(fusion_md_lines) + "\n", encoding="utf-8")

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "ocr_called": False,
            "marker_rerun_executed": False,
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
        "stage": "EVAL-306A",
        "mode": "marker_table_quality_gate_and_parser_fusion_design",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval_marker1b_summary_loaded": bool(_norm(s305b.get("stage")) == "EVAL-MARKER-1B"),
        "eval_marker1_summary_loaded": bool(_norm(s304.get("stage")) == "EVAL-MARKER-1"),
        "marker_table_total": int(len(gate_df)),
        "direct_structurable_count": int((gate_df["table_classification"] == "direct_structurable").sum()),
        "multi_panel_split_required_count": int((gate_df["table_classification"] == "multi_panel_split_required").sum()),
        "context_required_count": int((gate_df["table_classification"] == "context_required").sum()),
        "low_value_or_junk_count": int((gate_df["table_classification"] == "low_value_or_junk").sum()),
        "manual_inspection_required_count": int((gate_df["table_classification"] == "manual_inspection_required").sum()),
        "high_value_financial_forecast_table_count": int(gate_df["high_value_financial_forecast_table"].sum()),
        "financial_summary_table_count": int(gate_df["financial_summary_table"].sum()),
        "balance_sheet_panel_count": int(gate_df["balance_sheet_panel"].sum()),
        "income_statement_panel_count": int(gate_df["income_statement_panel"].sum()),
        "cash_flow_panel_count": int(gate_df["cash_flow_panel"].sum()),
        "valuation_panel_count": int(gate_df["valuation_panel"].sum()),
        "business_assumption_table_count": int(gate_df["business_assumption_table"].sum()),
        "empty_shell_table_count": int(gate_df["empty_shell_table"].sum()),
        "disclaimer_rating_contact_table_count": int(gate_df["disclaimer_rating_contact_table"].sum()),
        "multi_panel_wide_table_count": int(gate_df["multi_panel_wide_table"].sum()),
        "parser_fusion_recommended": parser_fusion_recommended,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306A Marker Table Quality Gate and Parser Fusion Design",
        "",
        f"- marker_table_total: {summary['marker_table_total']}",
        f"- direct_structurable_count: {summary['direct_structurable_count']}",
        f"- multi_panel_split_required_count: {summary['multi_panel_split_required_count']}",
        f"- context_required_count: {summary['context_required_count']}",
        f"- low_value_or_junk_count: {summary['low_value_or_junk_count']}",
        f"- manual_inspection_required_count: {summary['manual_inspection_required_count']}",
        f"- high_value_financial_forecast_table_count: {summary['high_value_financial_forecast_table_count']}",
        f"- financial_summary_table_count: {summary['financial_summary_table_count']}",
        f"- multi_panel_wide_table_count: {summary['multi_panel_wide_table_count']}",
        f"- parser_fusion_recommended: {summary['parser_fusion_recommended']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306a_summary_json: {OUT_SUMMARY}")
    print(f"eval_306a_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
