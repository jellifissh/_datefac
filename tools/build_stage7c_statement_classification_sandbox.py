import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
STAGE7B_DIR = BASE_DIR / "output" / "stage7b_full_structured_sandbox"
OUT_DIR = BASE_DIR / "output" / "stage7c_statement_classification_sandbox"

IN_FULL = STAGE7B_DIR / "181_stage7b_full_structured_table.xlsx"
IN_STD = STAGE7B_DIR / "181_stage7b_standardized_structured_table.xlsx"
IN_INV = STAGE7B_DIR / "181_stage7b_per_pdf_table_block_inventory.xlsx"
IN_SUMMARY = STAGE7B_DIR / "181_stage7b_full_structured_summary.json"

OUT_SUMMARY = OUT_DIR / "182_stage7c_statement_classification_summary.json"
OUT_REPORT = OUT_DIR / "182_stage7c_statement_classification_report.md"
OUT_CLASSIFIED = OUT_DIR / "182_stage7c_classified_full_structured_table.xlsx"
OUT_STMT_INV = OUT_DIR / "182_stage7c_statement_type_inventory.xlsx"
OUT_UNKNOWN_REVIEW = OUT_DIR / "182_stage7c_unknown_reclassification_review.xlsx"
OUT_CORE_PREVIEW = OUT_DIR / "182_stage7c_core_metrics_candidate_preview.xlsx"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

CORE_METRICS = {"营业收入", "归属母公司净利润", "毛利率", "ROE", "每股收益", "P/E", "P/B", "EV/EBITDA"}

YEAR_RE = re.compile(r"20\d{2}(?:[AE])?$", re.IGNORECASE)
NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?$")


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    return re.sub(r"\s+", "", _norm(v)).upper()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for s, df in sheets.items():
            df.to_excel(writer, sheet_name=s[:31], index=False)


def _run_delivery_check() -> Dict[str, Any]:
    p = subprocess.run(
        [sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "").strip()
    if not txt:
        return {"overall_status": "UNKNOWN"}
    return json.loads(txt)


def _snapshot_guard() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_scope_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP) if RELEASE_ZIP.exists() else "MISSING"
    return snap


def _contains_any(text: str, keywords: List[str]) -> bool:
    t = _compact(text)
    return any(_compact(k) in t for k in keywords)


def _classify_unknown(row: pd.Series) -> Tuple[str, str, float]:
    metric = _norm(row.get("normalized_metric_name")) or _norm(row.get("raw_metric_name"))
    excerpt = _norm(row.get("source_text_excerpt"))
    block_type = _norm(row.get("block_type"))
    joined = f"{metric} || {excerpt} || {block_type}"

    if _contains_any(joined, ["资产总计", "流动资产", "非流动资产", "负债合计", "股本", "资本公积", "所有者权益"]):
        return "balance_sheet", "keyword_balance_sheet", 0.92
    if _contains_any(joined, ["经营活动现金流", "投资活动现金流", "筹资活动现金流", "现金及现金等价物"]):
        return "cash_flow_statement", "keyword_cash_flow", 0.92
    if _contains_any(joined, ["营业收入", "营业成本", "销售费用", "管理费用", "研发费用", "财务费用", "营业利润", "利润总额", "归母净利润"]):
        return "income_statement", "keyword_income_statement", 0.92
    if _contains_any(joined, ["毛利率", "净利率", "ROE", "ROIC", "资产负债率", "流动比率", "速动比率"]):
        return "financial_ratios", "keyword_financial_ratios", 0.9
    if _contains_any(joined, ["EPS", "每股收益", "每股净资产", "每股经营现金流"]):
        return "per_share_metrics", "keyword_per_share", 0.95
    if _contains_any(joined, ["PE", "P/E", "PB", "P/B", "EV/EBITDA", "市盈率", "市净率"]):
        return "valuation_metrics", "keyword_valuation_metrics", 0.9
    if _contains_any(joined, ["评级说明", "免责声明", "分析师声明", "请务必阅读"]):
        return "non_financial_table", "keyword_non_financial", 0.97
    if _contains_any(joined, ["公司简介", "公司基本情况", "国药准字", "临床", "疫苗", "NabiBiota", "Pfizer", "Merck"]):
        return "company_profile", "keyword_company_profile", 0.86
    if _contains_any(joined, ["会计年度", "指标/年度", "TABLE", "MAINPROFIT"]):
        return "financial_data_and_valuation", "header_financial_data_and_valuation", 0.74
    return "unknown_financial_table", "insufficient_evidence_keep_unknown", 0.45


def _normalize_statement(row: pd.Series) -> Tuple[str, str, float]:
    original = _norm(row.get("statement_type"))
    metric = _norm(row.get("normalized_metric_name")) or _norm(row.get("raw_metric_name"))
    excerpt = _norm(row.get("source_text_excerpt"))
    joined = f"{metric} || {excerpt}"

    if original == "unknown_financial_table":
        return _classify_unknown(row)

    if original in {"non_financial_table", "rating_explanation", "company_profile"}:
        if _contains_any(joined, ["EPS", "每股收益"]):
            return "per_share_metrics", "override_from_non_financial_eps_keyword", 0.7
        return original, "keep_existing_non_financial_type", 0.95

    if original == "financial_ratios" and _contains_any(joined, ["EPS", "每股收益"]):
        return "per_share_metrics", "eps_not_ratio_fix", 0.96

    if original == "valuation_metrics" and _contains_any(joined, ["EPS", "每股收益"]):
        return "per_share_metrics", "eps_valuation_reclass_fix", 0.9

    return original, "keep_existing_type", 0.93


def _usability_layer(row: pd.Series) -> str:
    st = _norm(row.get("normalized_statement_type"))
    mapping_status = _norm(row.get("mapping_status"))
    needs_manual = bool(row.get("needs_manual_review"))
    needs_mapping = bool(row.get("needs_mapping_review"))
    needs_unit = bool(row.get("needs_unit_review"))
    metric = _norm(row.get("standard_metric"))
    year = _norm(row.get("year"))
    value = _norm(row.get("value"))

    if st in {"non_financial_table", "rating_explanation", "company_profile", "disclaimer"}:
        return "non_financial_excluded"

    if needs_manual or needs_mapping or needs_unit:
        if metric in CORE_METRICS and YEAR_RE.fullmatch(year) and NUM_RE.fullmatch(value):
            return "manual_review_required"
        return "full_structured_only"

    if mapping_status == "MAPPED":
        if metric in CORE_METRICS and YEAR_RE.fullmatch(year) and NUM_RE.fullmatch(value):
            return "candidate_for_core_metrics"
        return "candidate_for_standardized"

    return "full_structured_only"


def main() -> int:
    for p in [IN_FULL, IN_STD, IN_INV, IN_SUMMARY]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    before = _snapshot_guard()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    full_df = pd.read_excel(IN_FULL, sheet_name="full_structured_table").fillna("")
    stage7b_summary = json.loads(IN_SUMMARY.read_text(encoding="utf-8"))
    input_rows = int(len(full_df))

    unknown_before = int((full_df["statement_type"].map(_norm) == "unknown_financial_table").sum())

    classified = full_df.copy()
    normalized_types: List[str] = []
    reasons: List[str] = []
    confidences: List[float] = []
    usability: List[str] = []

    for _, row in classified.iterrows():
        nst, reason, conf = _normalize_statement(row)
        # hard EPS guard: EPS must not be ratio
        metric = _norm(row.get("normalized_metric_name")) or _norm(row.get("raw_metric_name"))
        if ("EPS" in _compact(metric) or "每股收益" in metric) and nst == "financial_ratios":
            nst = "per_share_metrics"
            reason = "eps_force_not_ratio_guard"
            conf = 0.99
        normalized_types.append(nst)
        reasons.append(reason)
        confidences.append(round(float(conf), 4))

    classified["normalized_statement_type"] = normalized_types
    classified["classification_reason"] = reasons
    classified["classification_confidence"] = confidences

    for _, row in classified.iterrows():
        usability.append(_usability_layer(row))
    classified["usability_layer"] = usability

    classified_rows = int(len(classified))
    unknown_after = int((classified["normalized_statement_type"].map(_norm) == "unknown_financial_table").sum())
    reclassified_unknown = int(unknown_before - unknown_after)

    unknown_review_df = classified[
        (classified["statement_type"].map(_norm) == "unknown_financial_table")
        | (classified["classification_reason"].map(_norm).str.contains("unknown|override|header", case=False, regex=True))
    ].copy()

    stmt_counts = classified["normalized_statement_type"].map(_norm).value_counts().to_dict()
    use_counts = classified["usability_layer"].map(_norm).value_counts().to_dict()

    eps_scope = classified[
        classified["normalized_metric_name"].map(lambda x: "EPS" in _compact(x) or "每股收益" in _norm(x))
    ].copy()
    eps_detected_count = int(len(eps_scope))
    bad_eps_ratio_count = int((eps_scope["normalized_statement_type"].map(_norm) == "financial_ratios").sum())

    core_preview = classified[
        classified["usability_layer"].map(_norm).isin({"candidate_for_core_metrics", "manual_review_required"})
    ].copy()

    per_pdf_inventory = (
        classified.groupby("source_pdf_name", dropna=False)
        .agg(
            input_rows=("source_pdf_name", "size"),
            unknown_before_rows=("statement_type", lambda s: int((s.map(_norm) == "unknown_financial_table").sum())),
            unknown_after_rows=("normalized_statement_type", lambda s: int((s.map(_norm) == "unknown_financial_table").sum())),
            core_candidate_rows=("usability_layer", lambda s: int((s.map(_norm) == "candidate_for_core_metrics").sum())),
            manual_review_rows=("usability_layer", lambda s: int((s.map(_norm) == "manual_review_required").sum())),
        )
        .reset_index()
    )

    stmt_inventory = (
        classified.groupby(["source_pdf_name", "normalized_statement_type"], dropna=False)
        .size()
        .reset_index(name="row_count")
        .sort_values(["source_pdf_name", "row_count"], ascending=[True, False])
    )

    after = _snapshot_guard()
    production_files_modified = not (
        before["01"] == after["01"]
        and before["02"] == after["02"]
        and before["02A"] == after["02A"]
        and before["05"] == after["05"]
        and before["06"] == after["06"]
    )
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_scope_rules"] != after["formal_scope_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    check = _run_delivery_check()
    overall_status = _norm(check.get("overall_status"))

    ready_for_stage7d = bool(
        classified_rows == input_rows
        and (unknown_after < unknown_before or unknown_before == 0)
        and "income_statement" in stmt_counts
        and "financial_ratios" in stmt_counts
        and bad_eps_ratio_count == 0
        and not production_files_modified
        and not official_02b_modified
        and not formal_rules_modified
        and not standardizer_modified
        and not release_package_modified
        and overall_status == "PASS"
    )

    summary = {
        "stage": "stage7c_statement_classification",
        "mode": "sandbox_only",
        "based_on_stage7b_commit": "e041234ae15d618b8b235000f14fe3adda85ca44",
        "input_full_structured_rows": input_rows,
        "classified_rows": classified_rows,
        "unknown_financial_before_count": unknown_before,
        "unknown_financial_after_count": unknown_after,
        "reclassified_unknown_count": reclassified_unknown,
        "statement_type_counts": stmt_counts,
        "usability_layer_counts": use_counts,
        "eps_detected_count": eps_detected_count,
        "bad_eps_ratio_count": bad_eps_ratio_count,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": overall_status,
        "ready_for_stage7d_pipeline_entrypoint": ready_for_stage7d,
    }

    _write_excel(
        OUT_CLASSIFIED,
        {
            "classified_full_structured": classified,
            "per_pdf_inventory": per_pdf_inventory,
        },
    )
    _write_excel(
        OUT_STMT_INV,
        {
            "statement_type_inventory": stmt_inventory,
            "usability_layer_inventory": classified["usability_layer"].value_counts().rename_axis("usability_layer").reset_index(name="row_count"),
        },
    )
    _write_excel(
        OUT_UNKNOWN_REVIEW,
        {
            "unknown_reclassification_review": unknown_review_df,
        },
    )
    _write_excel(
        OUT_CORE_PREVIEW,
        {
            "core_metrics_candidate_preview": core_preview,
            "eps_rows": eps_scope,
        },
    )

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# Stage 7C Statement Type Classification Sandbox",
        "",
        "## Goal",
        "- Focus on statement type refinement and usability layering for Stage 7B full_structured_table.",
        "- Keep all rows; do not drop mapping-miss rows.",
        "",
        "## Input",
        f"- input_full_structured_rows: {input_rows}",
        f"- based_on_stage7b_commit: {summary['based_on_stage7b_commit']}",
        "",
        "## Unknown Reclassification",
        f"- unknown_financial_before_count: {unknown_before}",
        f"- unknown_financial_after_count: {unknown_after}",
        f"- reclassified_unknown_count: {reclassified_unknown}",
        "",
        "## Statement Type Counts",
    ]
    for k, v in stmt_counts.items():
        md_lines.append(f"- {k}: {v}")
    md_lines.extend(["", "## Usability Layer Counts"])
    for k, v in use_counts.items():
        md_lines.append(f"- {k}: {v}")
    md_lines.extend(
        [
            "",
            "## EPS Check",
            f"- eps_detected_count: {eps_detected_count}",
            f"- bad_eps_ratio_count: {bad_eps_ratio_count}",
            "",
            "## Safety",
            f"- production_files_modified: {production_files_modified}",
            f"- official_02b_modified: {official_02b_modified}",
            f"- formal_rules_modified: {formal_rules_modified}",
            f"- standardizer_modified: {standardizer_modified}",
            f"- release_package_modified: {release_package_modified}",
            f"- check_delivery_state_overall_status: {overall_status}",
            "",
            "## Decision",
            f"- ready_for_stage7d_pipeline_entrypoint: {ready_for_stage7d}",
        ]
    )
    OUT_REPORT.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"stage7c_summary_json: {OUT_SUMMARY}")
    print(f"stage7c_report_md: {OUT_REPORT}")
    print(f"stage7c_ready_for_stage7d_pipeline_entrypoint: {ready_for_stage7d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
