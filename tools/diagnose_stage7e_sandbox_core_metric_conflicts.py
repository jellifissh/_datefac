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
IN_DIR = BASE_DIR / "output" / "stage7d_pipeline_sandbox"
OUT_DIR = BASE_DIR / "output" / "stage7e_sandbox_conflict_diagnosis"

IN_SUMMARY = IN_DIR / "183_stage7d_pipeline_summary.json"
IN_FULL = IN_DIR / "183_stage7d_full_structured_table.xlsx"
IN_CLASSIFIED = IN_DIR / "183_stage7d_classified_structured_table.xlsx"
IN_CORE = IN_DIR / "183_stage7d_core_metrics_candidate_preview.xlsx"
IN_SANDBOX06 = IN_DIR / "183_stage7d_sandbox_06_preview.xlsx"
IN_CONFLICT = IN_DIR / "183_stage7d_conflict_report.xlsx"

OUT_SUMMARY = OUT_DIR / "184_stage7e_conflict_diagnosis_summary.json"
OUT_REPORT = OUT_DIR / "184_stage7e_conflict_diagnosis_report.md"
OUT_DETAIL = OUT_DIR / "184_stage7e_conflict_detail.xlsx"
OUT_POLICY = OUT_DIR / "184_stage7e_resolution_policy_draft.json"
OUT_RESOLVED = OUT_DIR / "184_stage7e_resolved_06_preview_dry_run.xlsx"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

AMOUNT_METRICS = {"营业收入", "归属母公司净利润"}
RATIO_METRICS = {"毛利率", "ROE"}
PER_SHARE_METRICS = {"每股收益"}
VALUATION_METRICS = {"P/E", "P/B", "EV/EBITDA"}

FINANCIAL_ST_TYPES = {"income_statement", "balance_sheet", "cash_flow_statement", "financial_data_and_valuation"}

GROWTH_TOKENS = ["增长率", "同比", "YoY", "yoy", "增速"]


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


def _normalize_unit(unit: str, metric: str) -> str:
    u = _norm(unit)
    m = _norm(metric)
    uc = _compact(u)
    if m == "每股收益":
        return "元/股"
    if uc in {"БЖ", "X", "倍"}:
        return "倍"
    if uc in {"RATIO"}:
        return "ratio"
    if "%" in u:
        return "%"
    return u


def _normalize_value(v: Any) -> str:
    s = _norm(v).replace(",", "")
    if not s:
        return ""
    try:
        f = float(s)
        if abs(f - int(f)) < 1e-9:
            return str(int(f))
        return ("%0.10f" % f).rstrip("0").rstrip(".")
    except Exception:
        return s


def _has_growth_text(text: str) -> bool:
    t = _norm(text)
    return any(k in t for k in GROWTH_TOKENS)


def _statement_priority(metric: str, st: str) -> int:
    metric = _norm(metric)
    st = _norm(st)
    pri: List[str]
    if metric in AMOUNT_METRICS:
        pri = ["income_statement", "financial_data_and_valuation", "balance_sheet", "cash_flow_statement", "financial_ratios", "valuation_metrics", "per_share_metrics"]
    elif metric in RATIO_METRICS:
        pri = ["financial_ratios", "financial_data_and_valuation", "income_statement", "valuation_metrics", "per_share_metrics", "balance_sheet", "cash_flow_statement"]
    elif metric in PER_SHARE_METRICS:
        pri = ["per_share_metrics", "financial_data_and_valuation", "income_statement", "financial_ratios", "valuation_metrics", "balance_sheet", "cash_flow_statement"]
    elif metric in VALUATION_METRICS:
        pri = ["valuation_metrics", "financial_data_and_valuation", "financial_ratios", "income_statement", "per_share_metrics", "balance_sheet", "cash_flow_statement"]
    else:
        pri = ["financial_data_and_valuation", "income_statement", "financial_ratios", "valuation_metrics", "per_share_metrics", "balance_sheet", "cash_flow_statement"]
    return pri.index(st) if st in pri else 99


def _expected_unit_group(metric: str) -> str:
    if metric in AMOUNT_METRICS:
        return "amount"
    if metric in RATIO_METRICS:
        return "ratio"
    if metric in PER_SHARE_METRICS:
        return "per_share"
    if metric in VALUATION_METRICS:
        return "multiple"
    return "unknown"


def _unit_group(unit: str) -> str:
    u = _norm(unit)
    if u in {"百万元", "亿元", "万元", "元"}:
        return "amount"
    if u in {"%", "ratio"}:
        return "ratio"
    if u in {"元/股"}:
        return "per_share"
    if u in {"倍"}:
        return "multiple"
    return "unknown"


def _build_candidate_df(core_df: pd.DataFrame) -> pd.DataFrame:
    c = core_df.copy()
    c["asset_package"] = c["source_pdf_name"].map(_norm).map(lambda x: x.replace(".pdf", "_stage7d_sandbox"))
    c["final_value"] = c["value"].map(_normalize_value)
    c["final_unit"] = c.apply(lambda r: _normalize_unit(_norm(r.get("inferred_unit")), _norm(r.get("standard_metric"))), axis=1)
    c["year"] = c["year"].map(_norm)
    c["key"] = c["asset_package"] + "||" + c["standard_metric"].map(_norm) + "||" + c["year"]
    c["statement_type_for_priority"] = c["normalized_statement_type"].map(_norm)
    c["is_growth_like"] = (c["raw_metric_name"].map(_has_growth_text) | c["source_text_excerpt"].map(_has_growth_text))
    c["expected_unit_group"] = c["standard_metric"].map(_expected_unit_group)
    c["unit_group"] = c["final_unit"].map(_unit_group)
    return c


def _conflict_stats(df: pd.DataFrame) -> Dict[str, int]:
    if df.empty:
        return {"duplicate_key_count": 0, "value_mismatch_count": 0, "unit_conflict_count": 0, "year_conflict_count": 0}
    work = df.copy()
    work["key"] = work["asset_package"].map(_norm) + "||" + work["standard_metric"].map(_norm) + "||" + work["year"].map(_norm)
    dup = int(work["key"].duplicated().sum())
    v_mis = 0
    u_mis = 0
    for _, g in work.groupby("key", dropna=False):
        if g["final_value"].map(_norm).nunique() > 1:
            v_mis += 1
        if g["final_unit"].map(_norm).nunique() > 1:
            u_mis += 1
    y_mis = 0
    for _, g in work.groupby(["asset_package", "standard_metric"], dropna=False):
        ys = [y for y in g["year"].map(_norm).tolist() if y]
        if len(ys) != len(set(ys)):
            y_mis += 1
    return {"duplicate_key_count": dup, "value_mismatch_count": v_mis, "unit_conflict_count": u_mis, "year_conflict_count": y_mis}


def _categorize_key(group: pd.DataFrame) -> str:
    metric = _norm(group.iloc[0].get("standard_metric"))
    vals = group["final_value"].map(_norm).unique().tolist()
    units = group["final_unit"].map(_norm).unique().tolist()
    stypes = group["statement_type_for_priority"].map(_norm).unique().tolist()
    has_growth = bool(group["is_growth_like"].astype(bool).any())
    has_non_growth = bool((~group["is_growth_like"].astype(bool)).any())

    if len(vals) == 1 and len(units) == 1:
        return "same_metric_same_value_duplicate"
    if has_growth and has_non_growth and metric in AMOUNT_METRICS:
        return "amount_vs_growth_rate_collision"
    if metric in AMOUNT_METRICS and any(u in {"%", "ratio"} for u in units):
        return "amount_vs_ratio_collision"
    if metric in VALUATION_METRICS and any(st in FINANCIAL_ST_TYPES for st in stypes):
        return "valuation_vs_financial_metric_collision"
    if len(units) > 1:
        return "unit_inference_error"
    if len(stypes) > 1:
        return "statement_type_collision"
    if len(vals) > 1:
        return "true_value_conflict"
    return "source_priority_needed"


def _score_row(row: pd.Series) -> float:
    metric = _norm(row.get("standard_metric"))
    st = _norm(row.get("statement_type_for_priority"))
    pri = _statement_priority(metric, st)
    score = 100 - pri * 8

    exp = _norm(row.get("expected_unit_group"))
    ug = _norm(row.get("unit_group"))
    if exp == ug:
        score += 12
    elif ug == "unknown":
        score -= 8
    else:
        score -= 4

    if bool(row.get("is_growth_like")) and metric in AMOUNT_METRICS:
        score -= 16

    score += float(pd.to_numeric(row.get("extraction_confidence"), errors="coerce") or 0.0) * 5
    score += float(pd.to_numeric(row.get("classification_confidence"), errors="coerce") or 0.0) * 5
    return float(score)


def main() -> int:
    for p in [IN_SUMMARY, IN_FULL, IN_CLASSIFIED, IN_CORE, IN_SANDBOX06]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    before = _snapshot_guard()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    stage7d_summary = json.loads(IN_SUMMARY.read_text(encoding="utf-8"))
    core = pd.read_excel(IN_CORE, sheet_name="core_metrics_candidate_preview").fillna("")
    candidate = _build_candidate_df(core)

    before_stats = _conflict_stats(candidate)
    # keep source of truth as stage7d summary if provided
    before_stats["duplicate_key_count"] = int(stage7d_summary.get("duplicate_key_count", before_stats["duplicate_key_count"]))
    before_stats["value_mismatch_count"] = int(stage7d_summary.get("value_mismatch_count", before_stats["value_mismatch_count"]))
    before_stats["unit_conflict_count"] = int(stage7d_summary.get("unit_conflict_count", before_stats["unit_conflict_count"]))
    before_stats["year_conflict_count"] = int(stage7d_summary.get("year_conflict_count", before_stats["year_conflict_count"]))

    key_counts = candidate["key"].value_counts()
    conflict_keys = key_counts[key_counts > 1].index.tolist()

    conflict_rows: List[Dict[str, Any]] = []
    resolved_rows: List[Dict[str, Any]] = []
    auto_resolvable = 0
    manual_required = 0

    for key in candidate["key"].tolist():
        if key not in conflict_keys:
            continue
    for key in conflict_keys:
        g = candidate[candidate["key"] == key].copy()
        cat = _categorize_key(g)
        g["resolution_score"] = g.apply(_score_row, axis=1)
        g = g.sort_values(["resolution_score", "page_number", "row_order"], ascending=[False, True, True], kind="mergesort")
        top = g.iloc[0]
        second_score = float(g.iloc[1]["resolution_score"]) if len(g) > 1 else -999
        top_score = float(top["resolution_score"])
        ambiguous = bool(len(g) > 1 and abs(top_score - second_score) < 0.5 and g["final_value"].map(_norm).nunique() > 1)
        if ambiguous:
            manual_required += 1
        else:
            auto_resolvable += 1

        for _, r in g.iterrows():
            conflict_rows.append(
                {
                    "key": key,
                    "asset_package": _norm(r.get("asset_package")),
                    "standard_metric": _norm(r.get("standard_metric")),
                    "year": _norm(r.get("year")),
                    "final_value": _norm(r.get("final_value")),
                    "final_unit": _norm(r.get("final_unit")),
                    "statement_type_for_priority": _norm(r.get("statement_type_for_priority")),
                    "source_pdf_name": _norm(r.get("source_pdf_name")),
                    "page_number": _norm(r.get("page_number")),
                    "raw_metric_name": _norm(r.get("raw_metric_name")),
                    "source_text_excerpt": _norm(r.get("source_text_excerpt")),
                    "conflict_category": cat,
                    "resolution_score": float(r.get("resolution_score", 0)),
                    "selected_in_dry_run": bool(_norm(r.get("block_id")) == _norm(top.get("block_id")) and _norm(r.get("raw_metric_name")) == _norm(top.get("raw_metric_name")) and _norm(r.get("final_value")) == _norm(top.get("final_value")) and _norm(r.get("source_pdf_name")) == _norm(top.get("source_pdf_name"))),
                    "manual_review_required": ambiguous,
                }
            )
        resolved_rows.append(top.to_dict())

    # include non-conflict keys directly
    non_conf = candidate[~candidate["key"].isin(conflict_keys)].copy()
    if not non_conf.empty:
        for _, r in non_conf.iterrows():
            resolved_rows.append(r.to_dict())

    resolved = pd.DataFrame(resolved_rows).fillna("")
    if not resolved.empty:
        resolved = resolved.drop_duplicates(subset=["key"], keep="first").copy()

    # ensure eps unit
    resolved.loc[resolved["standard_metric"].map(_norm) == "每股收益", "final_unit"] = "元/股"

    after_stats = _conflict_stats(resolved)

    conflict_detail = pd.DataFrame(conflict_rows).fillna("")
    cat_dist = conflict_detail["conflict_category"].value_counts().to_dict() if not conflict_detail.empty else {}

    policy = {
        "version": "stage7e_draft_v1",
        "metric_priority": {
            "amount_metrics": ["income_statement", "financial_data_and_valuation", "balance_sheet", "cash_flow_statement", "financial_ratios", "valuation_metrics", "per_share_metrics"],
            "ratio_metrics": ["financial_ratios", "financial_data_and_valuation", "income_statement", "valuation_metrics", "per_share_metrics"],
            "per_share_metrics": ["per_share_metrics", "financial_data_and_valuation", "income_statement", "financial_ratios"],
            "valuation_metrics": ["valuation_metrics", "financial_data_and_valuation", "financial_ratios", "income_statement"],
        },
        "unit_policy": {
            "每股收益": "元/股",
            "valuation_metrics": "倍",
            "ratio_metrics": "%",
            "amount_metrics": "百万元/亿元/万元",
        },
        "merge_rules": [
            "same key + same value + same unit => merge as same_metric_same_value_duplicate",
            "if source contains 增长率/同比 and metric is amount metric, deprioritize for core 06 preview",
            "if unit group mismatches metric expected group, mark unit_inference_error",
        ],
        "tie_breakers": [
            "higher statement priority wins",
            "higher extraction_confidence wins",
            "higher classification_confidence wins",
            "earlier page/row wins when still tied",
        ],
        "manual_review_trigger": "top two candidates score gap < 0.5 and conflicting values",
    }
    OUT_POLICY.write_text(json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")

    # output resolved preview schema
    resolved_preview = resolved[
        [
            "source_pdf",
            "asset_package",
            "standard_metric",
            "year",
            "final_value",
            "final_unit",
            "statement_type_for_priority",
            "source_pdf_name",
            "page_number",
            "raw_metric_name",
            "source_text_excerpt",
            "resolution_score",
            "expected_unit_group",
            "unit_group",
        ]
    ].copy()
    resolved_preview = resolved_preview.rename(columns={"statement_type_for_priority": "statement_type"})

    eps_detected_count = int((resolved_preview["standard_metric"].map(_norm) == "每股收益").sum())
    bad_eps_ratio_count = int(
        resolved_preview[
            (resolved_preview["standard_metric"].map(_norm) == "每股收益")
            & (resolved_preview["final_unit"].map(_norm).isin({"ratio", "%"}))
        ].shape[0]
    )

    _write_excel(
        OUT_DETAIL,
        {
            "conflict_detail": conflict_detail.sort_values(["key", "resolution_score"], ascending=[True, False]) if not conflict_detail.empty else conflict_detail,
            "conflict_category_distribution": pd.DataFrame([{"conflict_category": k, "count": v} for k, v in cat_dist.items()]),
            "input_candidate_rows": candidate,
        },
    )
    _write_excel(
        OUT_RESOLVED,
        {
            "resolved_06_preview_dry_run": resolved_preview,
            "before_conflict_stats": pd.DataFrame([before_stats]),
            "after_conflict_stats": pd.DataFrame([after_stats]),
        },
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
    delivery = _run_delivery_check()
    overall_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "stage7e_sandbox_conflict_diagnosis",
        "mode": "sandbox_diagnosis_only",
        "based_on_stage7d_commit": "efefde274bf07af30a3021e395c3b359c55c2a90",
        "input_core_metrics_candidate_rows": int(len(candidate)),
        "input_sandbox_06_preview_rows": int(stage7d_summary.get("sandbox_06_preview_rows", len(candidate))),
        "duplicate_key_count_before": int(before_stats["duplicate_key_count"]),
        "value_mismatch_count_before": int(before_stats["value_mismatch_count"]),
        "unit_conflict_count_before": int(before_stats["unit_conflict_count"]),
        "year_conflict_count_before": int(before_stats["year_conflict_count"]),
        "auto_resolvable_conflict_count": int(auto_resolvable),
        "manual_review_required_count": int(manual_required),
        "resolved_06_preview_generated": True,
        "duplicate_key_count_after_dry_run": int(after_stats["duplicate_key_count"]),
        "value_mismatch_count_after_dry_run": int(after_stats["value_mismatch_count"]),
        "unit_conflict_count_after_dry_run": int(after_stats["unit_conflict_count"]),
        "year_conflict_count_after_dry_run": int(after_stats["year_conflict_count"]),
        "eps_detected_count": int(eps_detected_count),
        "bad_eps_ratio_count": int(bad_eps_ratio_count),
        "production_files_modified": bool(production_files_modified),
        "official_02b_modified": bool(official_02b_modified),
        "formal_rules_modified": bool(formal_rules_modified),
        "standardizer_modified": bool(standardizer_modified),
        "release_package_modified": bool(release_package_modified),
        "check_delivery_state_overall_status": overall_status,
        "ready_for_stage7f_core_metrics_policy_apply_sandbox": False,
        "conflict_category_distribution": cat_dist,
    }
    summary["ready_for_stage7f_core_metrics_policy_apply_sandbox"] = bool(
        summary["resolved_06_preview_generated"]
        and summary["bad_eps_ratio_count"] == 0
        and summary["duplicate_key_count_after_dry_run"] == 0
        and summary["value_mismatch_count_after_dry_run"] == 0
        and summary["unit_conflict_count_after_dry_run"] == 0
        and summary["year_conflict_count_after_dry_run"] == 0
        and not summary["production_files_modified"]
        and not summary["official_02b_modified"]
        and not summary["formal_rules_modified"]
        and not summary["standardizer_modified"]
        and not summary["release_package_modified"]
        and summary["check_delivery_state_overall_status"] == "PASS"
    )

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# Stage 7E Sandbox Core Metrics Conflict Diagnosis",
        "",
        "## Input",
        f"- input_core_metrics_candidate_rows: {summary['input_core_metrics_candidate_rows']}",
        f"- input_sandbox_06_preview_rows: {summary['input_sandbox_06_preview_rows']}",
        "",
        "## Conflict Before",
        f"- duplicate_key_count_before: {summary['duplicate_key_count_before']}",
        f"- value_mismatch_count_before: {summary['value_mismatch_count_before']}",
        f"- unit_conflict_count_before: {summary['unit_conflict_count_before']}",
        f"- year_conflict_count_before: {summary['year_conflict_count_before']}",
        "",
        "## Resolution Dry Run",
        f"- auto_resolvable_conflict_count: {summary['auto_resolvable_conflict_count']}",
        f"- manual_review_required_count: {summary['manual_review_required_count']}",
        f"- duplicate_key_count_after_dry_run: {summary['duplicate_key_count_after_dry_run']}",
        f"- value_mismatch_count_after_dry_run: {summary['value_mismatch_count_after_dry_run']}",
        f"- unit_conflict_count_after_dry_run: {summary['unit_conflict_count_after_dry_run']}",
        f"- year_conflict_count_after_dry_run: {summary['year_conflict_count_after_dry_run']}",
        "",
        "## Conflict Category Distribution",
    ]
    for k, v in cat_dist.items():
        md_lines.append(f"- {k}: {v}")
    md_lines.extend(
        [
            "",
            "## EPS Check",
            f"- eps_detected_count: {summary['eps_detected_count']}",
            f"- bad_eps_ratio_count: {summary['bad_eps_ratio_count']}",
            "",
            "## Safety",
            f"- production_files_modified: {summary['production_files_modified']}",
            f"- official_02b_modified: {summary['official_02b_modified']}",
            f"- formal_rules_modified: {summary['formal_rules_modified']}",
            f"- standardizer_modified: {summary['standardizer_modified']}",
            f"- release_package_modified: {summary['release_package_modified']}",
            f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
            "",
            "## Decision",
            f"- ready_for_stage7f_core_metrics_policy_apply_sandbox: {summary['ready_for_stage7f_core_metrics_policy_apply_sandbox']}",
        ]
    )
    OUT_REPORT.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"stage7e_summary_json: {OUT_SUMMARY}")
    print(f"stage7e_report_md: {OUT_REPORT}")
    print(f"stage7e_ready_for_stage7f_core_metrics_policy_apply_sandbox: {summary['ready_for_stage7f_core_metrics_policy_apply_sandbox']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
