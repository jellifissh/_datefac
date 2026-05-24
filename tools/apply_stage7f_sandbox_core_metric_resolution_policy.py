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
STAGE7D_DIR = BASE_DIR / "output" / "stage7d_pipeline_sandbox"
STAGE7E_DIR = BASE_DIR / "output" / "stage7e_sandbox_conflict_diagnosis"
OUT_DIR = BASE_DIR / "output" / "stage7f_core_metrics_policy_sandbox"

IN_STAGE7D_SUMMARY = STAGE7D_DIR / "183_stage7d_pipeline_summary.json"
IN_CORE = STAGE7D_DIR / "183_stage7d_core_metrics_candidate_preview.xlsx"
IN_CLASSIFIED = STAGE7D_DIR / "183_stage7d_classified_structured_table.xlsx"

IN_S7E_SUMMARY = STAGE7E_DIR / "184_stage7e_conflict_diagnosis_summary.json"
IN_S7E_DETAIL = STAGE7E_DIR / "184_stage7e_conflict_detail.xlsx"
IN_S7E_POLICY = STAGE7E_DIR / "184_stage7e_resolution_policy_draft.json"
IN_S7E_DRYRUN = STAGE7E_DIR / "184_stage7e_resolved_06_preview_dry_run.xlsx"

OUT_SUMMARY = OUT_DIR / "185_stage7f_policy_apply_summary.json"
OUT_REPORT = OUT_DIR / "185_stage7f_policy_apply_report.md"
OUT_CLEAN_PREVIEW = OUT_DIR / "185_stage7f_clean_sandbox_06_preview.xlsx"
OUT_MANUAL_QUEUE = OUT_DIR / "185_stage7f_manual_review_queue.xlsx"
OUT_EXCLUDED = OUT_DIR / "185_stage7f_excluded_conflict_rows.xlsx"
OUT_AUDIT = OUT_DIR / "185_stage7f_policy_application_audit.xlsx"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

AMOUNT_METRICS = {"营业收入", "归属母公司净利润"}
RATIO_METRICS = {"毛利率", "ROE"}
PER_SHARE_METRICS = {"每股收益"}
VALUATION_METRICS = {"P/E", "P/B", "EV/EBITDA"}
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


def _normalize_unit(metric: str, unit: str) -> str:
    m = _norm(metric)
    u = _norm(unit)
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
    c["standard_metric"] = c["standard_metric"].map(_norm)
    c["year"] = c["year"].map(_norm)
    c["final_value"] = c["value"].map(_normalize_value)
    c["final_unit"] = c.apply(lambda r: _normalize_unit(_norm(r.get("standard_metric")), _norm(r.get("inferred_unit"))), axis=1)
    c["key"] = c["asset_package"] + "||" + c["standard_metric"] + "||" + c["year"]
    c["is_growth_like"] = c["raw_metric_name"].map(_contains_growth) | c["source_text_excerpt"].map(_contains_growth)
    c["expected_unit_group"] = c["standard_metric"].map(_expected_unit_group)
    c["unit_group"] = c["final_unit"].map(_unit_group)
    c["statement_type_for_priority"] = c["normalized_statement_type"].map(_norm)
    return c


def _contains_growth(v: Any) -> bool:
    t = _norm(v)
    return any(k in t for k in GROWTH_TOKENS)


def _metric_priority_key(metric: str) -> str:
    if metric in AMOUNT_METRICS:
        return "amount_metrics"
    if metric in RATIO_METRICS:
        return "ratio_metrics"
    if metric in PER_SHARE_METRICS:
        return "per_share_metrics"
    if metric in VALUATION_METRICS:
        return "valuation_metrics"
    return "amount_metrics"


def _statement_priority(metric: str, statement_type: str, policy: Dict[str, Any]) -> int:
    mp = policy.get("metric_priority", {})
    key = _metric_priority_key(metric)
    order = mp.get(key, [])
    st = _norm(statement_type)
    return order.index(st) if st in order else 99


def _score_row(row: pd.Series, policy: Dict[str, Any]) -> float:
    metric = _norm(row.get("standard_metric"))
    st = _norm(row.get("statement_type_for_priority"))
    pri = _statement_priority(metric, st, policy)
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


def _conflict_stats(df: pd.DataFrame) -> Dict[str, int]:
    if df.empty:
        return {"duplicate_key_count_after": 0, "value_mismatch_count_after": 0, "unit_conflict_count_after": 0, "year_conflict_count_after": 0}
    w = df.copy()
    w["key"] = w["asset_package"].map(_norm) + "||" + w["standard_metric"].map(_norm) + "||" + w["year"].map(_norm)
    duplicate_key = int(w["key"].duplicated().sum())
    value_mismatch = 0
    unit_conflict = 0
    for _, g in w.groupby("key", dropna=False):
        if g["final_value"].map(_norm).nunique() > 1:
            value_mismatch += 1
        if g["final_unit"].map(_norm).nunique() > 1:
            unit_conflict += 1
    year_conflict = 0
    for _, g in w.groupby(["asset_package", "standard_metric"], dropna=False):
        ys = [y for y in g["year"].map(_norm).tolist() if y]
        if len(ys) != len(set(ys)):
            year_conflict += 1
    return {
        "duplicate_key_count_after": duplicate_key,
        "value_mismatch_count_after": value_mismatch,
        "unit_conflict_count_after": unit_conflict,
        "year_conflict_count_after": year_conflict,
    }


def main() -> int:
    for p in [IN_STAGE7D_SUMMARY, IN_CORE, IN_CLASSIFIED, IN_S7E_SUMMARY, IN_S7E_DETAIL, IN_S7E_POLICY, IN_S7E_DRYRUN]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    before = _snapshot_guard()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    s7d_summary = json.loads(IN_STAGE7D_SUMMARY.read_text(encoding="utf-8"))
    s7e_summary = json.loads(IN_S7E_SUMMARY.read_text(encoding="utf-8"))
    policy = json.loads(IN_S7E_POLICY.read_text(encoding="utf-8"))

    core = pd.read_excel(IN_CORE, sheet_name="core_metrics_candidate_preview").fillna("")
    candidate = _build_candidate_df(core)
    detail = pd.read_excel(IN_S7E_DETAIL, sheet_name="conflict_detail").fillna("")
    detail["key"] = detail["key"].map(_norm)

    manual_keys = set(detail[detail["manual_review_required"].astype(bool)]["key"].map(_norm).tolist())
    conflict_keys = set(detail["key"].map(_norm).tolist())

    clean_rows: List[Dict[str, Any]] = []
    manual_rows: List[Dict[str, Any]] = []
    excluded_rows: List[Dict[str, Any]] = []
    audit_rows: List[Dict[str, Any]] = []

    for key, g in candidate.groupby("key", dropna=False):
        g = g.copy()
        key = _norm(key)
        in_conflict = key in conflict_keys
        cat_set = set(detail[detail["key"].map(_norm) == key]["conflict_category"].map(_norm).tolist())
        category = ",".join(sorted(cat_set)) if cat_set else "no_conflict"

        # merge exact duplicates first
        g["merge_sig"] = g["final_value"].map(_norm) + "||" + g["final_unit"].map(_norm) + "||" + g["statement_type_for_priority"].map(_norm)
        g = g.drop_duplicates(subset=["merge_sig", "source_pdf_name", "page_number", "raw_metric_name"], keep="first").copy()

        if key in manual_keys and "true_value_conflict" in cat_set:
            for _, r in g.iterrows():
                rec = r.to_dict()
                rec["policy_action"] = "MANUAL_REVIEW_QUEUE_TRUE_VALUE_CONFLICT"
                rec["conflict_category"] = category
                manual_rows.append(rec)
                excluded_rows.append(rec)
            audit_rows.append(
                {
                    "key": key,
                    "conflict_category": category,
                    "action": "manual_queue",
                    "candidate_count": int(len(g)),
                    "selected_count": 0,
                    "reason": "true_value_conflict requires manual review by policy",
                }
            )
            continue

        # score and pick best row
        g["policy_score"] = g.apply(lambda r: _score_row(r, policy), axis=1)
        g = g.sort_values(["policy_score", "page_number", "row_order"], ascending=[False, True, True], kind="mergesort")
        top = g.iloc[0].to_dict()
        top["policy_action"] = "SELECTED_FOR_CLEAN_PREVIEW"
        top["conflict_category"] = category
        clean_rows.append(top)

        # others go to excluded
        if len(g) > 1:
            for _, r in g.iloc[1:].iterrows():
                rec = r.to_dict()
                rec["policy_action"] = "EXCLUDED_BY_PRIORITY"
                rec["conflict_category"] = category
                excluded_rows.append(rec)

        audit_rows.append(
            {
                "key": key,
                "conflict_category": category,
                "action": "selected",
                "candidate_count": int(len(g)),
                "selected_count": 1,
                "selected_source_pdf_name": _norm(top.get("source_pdf_name")),
                "selected_page_number": _norm(top.get("page_number")),
                "selected_statement_type": _norm(top.get("statement_type_for_priority")),
                "selected_value": _norm(top.get("final_value")),
                "selected_unit": _norm(top.get("final_unit")),
                "reason": "policy priority + confidence score",
            }
        )

    clean = pd.DataFrame(clean_rows).fillna("")
    manual = pd.DataFrame(manual_rows).fillna("")
    excluded = pd.DataFrame(excluded_rows).fillna("")
    audit = pd.DataFrame(audit_rows).fillna("")

    # enforce EPS unit
    if not clean.empty:
        clean.loc[clean["standard_metric"].map(_norm) == "每股收益", "final_unit"] = "元/股"

    # build final preview schema
    clean_preview = clean[
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
            "policy_score",
            "policy_action",
            "conflict_category",
        ]
    ].copy() if not clean.empty else pd.DataFrame(columns=[
        "source_pdf", "asset_package", "standard_metric", "year", "final_value", "final_unit",
        "statement_type_for_priority", "source_pdf_name", "page_number", "raw_metric_name",
        "source_text_excerpt", "policy_score", "policy_action", "conflict_category"
    ])
    clean_preview = clean_preview.rename(columns={"statement_type_for_priority": "statement_type"})

    stats_after = _conflict_stats(clean_preview)
    eps_detected_count = int((clean_preview["standard_metric"].map(_norm) == "每股收益").sum()) if not clean_preview.empty else 0
    bad_eps_ratio_count = int(
        clean_preview[
            (clean_preview["standard_metric"].map(_norm) == "每股收益")
            & (clean_preview["final_unit"].map(_norm).isin({"ratio", "%"}))
        ].shape[0]
    ) if not clean_preview.empty else 0

    _write_excel(
        OUT_CLEAN_PREVIEW,
        {
            "clean_sandbox_06_preview": clean_preview,
        },
    )
    _write_excel(
        OUT_MANUAL_QUEUE,
        {
            "manual_review_queue": manual,
        },
    )
    _write_excel(
        OUT_EXCLUDED,
        {
            "excluded_conflict_rows": excluded,
        },
    )
    _write_excel(
        OUT_AUDIT,
        {
            "policy_application_audit": audit,
            "input_candidate_rows": candidate,
            "before_summary": pd.DataFrame([s7e_summary]),
            "after_summary": pd.DataFrame([stats_after]),
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
        "stage": "stage7f_core_metrics_policy_apply_sandbox",
        "mode": "sandbox_policy_apply_only",
        "based_on_stage7e_commit": "ad5bd14",
        "input_core_metrics_candidate_rows": int(len(candidate)),
        "clean_sandbox_06_preview_rows": int(len(clean_preview)),
        "manual_review_queue_rows": int(len(manual)),
        "excluded_conflict_rows": int(len(excluded)),
        "duplicate_key_count_after": int(stats_after["duplicate_key_count_after"]),
        "value_mismatch_count_after": int(stats_after["value_mismatch_count_after"]),
        "unit_conflict_count_after": int(stats_after["unit_conflict_count_after"]),
        "year_conflict_count_after": int(stats_after["year_conflict_count_after"]),
        "policy_applied": True,
        "policy_source": "184_stage7e_resolution_policy_draft.json",
        "eps_detected_count": int(eps_detected_count),
        "bad_eps_ratio_count": int(bad_eps_ratio_count),
        "production_files_modified": bool(production_files_modified),
        "official_02b_modified": bool(official_02b_modified),
        "formal_rules_modified": bool(formal_rules_modified),
        "standardizer_modified": bool(standardizer_modified),
        "release_package_modified": bool(release_package_modified),
        "check_delivery_state_overall_status": overall_status,
        "ready_for_stage7g_ai_runtime_design_or_client_package": False,
    }
    summary["ready_for_stage7g_ai_runtime_design_or_client_package"] = bool(
        summary["policy_applied"]
        and summary["duplicate_key_count_after"] == 0
        and summary["value_mismatch_count_after"] == 0
        and summary["unit_conflict_count_after"] == 0
        and summary["year_conflict_count_after"] == 0
        and summary["bad_eps_ratio_count"] == 0
        and not summary["production_files_modified"]
        and not summary["official_02b_modified"]
        and not summary["formal_rules_modified"]
        and not summary["standardizer_modified"]
        and not summary["release_package_modified"]
        and summary["check_delivery_state_overall_status"] == "PASS"
    )
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    report_lines = [
        "# Stage 7F Policy Apply Sandbox",
        "",
        "## Input",
        f"- input_core_metrics_candidate_rows: {summary['input_core_metrics_candidate_rows']}",
        f"- policy_source: {summary['policy_source']}",
        "",
        "## Output",
        f"- clean_sandbox_06_preview_rows: {summary['clean_sandbox_06_preview_rows']}",
        f"- manual_review_queue_rows: {summary['manual_review_queue_rows']}",
        f"- excluded_conflict_rows: {summary['excluded_conflict_rows']}",
        "",
        "## Conflict After",
        f"- duplicate_key_count_after: {summary['duplicate_key_count_after']}",
        f"- value_mismatch_count_after: {summary['value_mismatch_count_after']}",
        f"- unit_conflict_count_after: {summary['unit_conflict_count_after']}",
        f"- year_conflict_count_after: {summary['year_conflict_count_after']}",
        "",
        "## EPS",
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
        f"- ready_for_stage7g_ai_runtime_design_or_client_package: {summary['ready_for_stage7g_ai_runtime_design_or_client_package']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"stage7f_summary_json: {OUT_SUMMARY}")
    print(f"stage7f_report_md: {OUT_REPORT}")
    print(f"stage7f_ready_for_stage7g_ai_runtime_design_or_client_package: {summary['ready_for_stage7g_ai_runtime_design_or_client_package']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
