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
OUT_DIR = BASE_DIR / "output" / "eval_307d_eps_focused_human_review_package"

IN_307C_REVIEW = BASE_DIR / "output" / "eval_307c_eps_review_burden_drilldown" / "307c_eps_review_required_rows.xlsx"
IN_307C_SUSP = BASE_DIR / "output" / "eval_307c_eps_review_burden_drilldown" / "307c_eps_suspicious_value_audit.xlsx"
IN_307C_MUST = BASE_DIR / "output" / "eval_307c_eps_review_burden_drilldown" / "307c_eps_must_review_candidates.xlsx"
IN_306L_GROUP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_grouped_review_table.xlsx"
IN_306L_MAP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_group_to_candidate_manifest.xlsx"

OUT_SUMMARY = OUT_DIR / "307d_summary.json"
OUT_REPORT = OUT_DIR / "307d_report.md"
OUT_TEMPLATE = OUT_DIR / "307d_eps_grouped_review_template.xlsx"
OUT_SUSP_PRIORITY = OUT_DIR / "307d_eps_suspicious_review_priority.xlsx"
OUT_PDF_ORDER = OUT_DIR / "307d_eps_by_pdf_review_order.xlsx"
OUT_README = OUT_DIR / "307d_eps_review_readme.md"
OUT_MAP = OUT_DIR / "307d_eps_group_to_candidate_manifest.xlsx"
OUT_NO_APPLY = OUT_DIR / "307d_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
YEAR_COLS = [str(y) for y in range(2020, 2031)]


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

    required = [IN_307C_REVIEW, IN_307C_SUSP, IN_307C_MUST, IN_306L_GROUP, IN_306L_MAP]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-307D",
                "mode": "eps_focused_human_review_package",
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

    review_rows = _drop_note_rows(_load_first_sheet(IN_307C_REVIEW, "eps_review_required_rows"))
    susp_rows = _drop_note_rows(_load_first_sheet(IN_307C_SUSP, "eps_suspicious_value_audit"))
    must_rows = _drop_note_rows(_load_first_sheet(IN_307C_MUST, "eps_must_review_candidates"))
    group_rows = _drop_note_rows(_load_first_sheet(IN_306L_GROUP, "grouped_review_table"))
    map_rows = _drop_note_rows(_load_first_sheet(IN_306L_MAP, "group_to_candidate_manifest"))

    for df in [review_rows, susp_rows, must_rows, group_rows, map_rows]:
        if "group_id" in df.columns:
            df["group_id"] = df["group_id"].map(_norm)
    if "标准指标" in group_rows.columns:
        group_rows["标准指标"] = group_rows["标准指标"].map(_norm).str.lower()

    eps_group_ids = sorted({g for g in must_rows["group_id"].map(_norm).tolist() if g != ""})
    must_group_count = len(eps_group_ids)

    eps_group_rows = group_rows[(group_rows["标准指标"] == "eps") & (group_rows["group_id"].isin(eps_group_ids))].copy()
    eps_group_rows = eps_group_rows.drop_duplicates(subset=["group_id"], keep="first")

    # suspicious flag aggregation by group
    susp_rows["group_id"] = susp_rows["group_id"].map(_norm)
    susp_group = (
        susp_rows.groupby("group_id", dropna=False)
        .agg(
            suspicious_row_count=("group_id", "count"),
            very_large_abs_gt_20_count=("very_large_abs_gt_20", lambda x: int(sum(bool(v) for v in x))),
            percent_like_count=("percent_like", lambda x: int(sum(bool(v) for v in x))),
            mixed_chinese_text_count=("mixed_chinese_text", lambda x: int(sum(bool(v) for v in x))),
            non_numeric_value_count=("non_numeric_value", lambda x: int(sum(bool(v) for v in x))),
        )
        .reset_index()
        if not susp_rows.empty
        else pd.DataFrame(columns=["group_id", "suspicious_row_count", "very_large_abs_gt_20_count", "percent_like_count", "mixed_chinese_text_count", "non_numeric_value_count"])
    )

    # source parser/page from review rows
    rv_meta = (
        review_rows.groupby("group_id", dropna=False)
        .agg(
            source_parser=("source_parser", lambda x: "|".join(sorted({_norm(v) for v in x if _norm(v) != ""}))),
            source_page=("source_page", lambda x: "|".join(sorted({_norm(v) for v in x if _norm(v) != ""}))),
            current_row_count=("group_id", "count"),
        )
        .reset_index()
        if not review_rows.empty
        else pd.DataFrame(columns=["group_id", "source_parser", "source_page", "current_row_count"])
    )

    # year pivot from review rows
    pivot = (
        review_rows.pivot_table(
            index="group_id",
            columns="年份",
            values="value",
            aggfunc=lambda s: "|".join(sorted({_norm(v) for v in s if _norm(v) != ""})),
        )
        if not review_rows.empty
        else pd.DataFrame()
    )
    if isinstance(pivot, pd.DataFrame) and not pivot.empty:
        pivot = pivot.reset_index()
        pivot.columns = ["group_id"] + [str(int(c)) for c in pivot.columns[1:]]
    else:
        pivot = pd.DataFrame(columns=["group_id"] + YEAR_COLS)
    for y in YEAR_COLS:
        if y not in pivot.columns:
            pivot[y] = ""

    template = (
        must_rows[["group_id", "PDF文件名", "source_panel_id", "blocker_list"]].copy()
        .drop_duplicates(subset=["group_id"], keep="first")
        .merge(rv_meta, on="group_id", how="left")
        .merge(susp_group, on="group_id", how="left")
        .merge(pivot[["group_id"] + YEAR_COLS], on="group_id", how="left")
    )
    template["source_parser"] = template["source_parser"].fillna("")
    template["source_page"] = template["source_page"].fillna("")
    template["blocker_reasons"] = template["blocker_list"].map(_norm)
    template["suspicious_value_flags"] = template.apply(
        lambda r: "|".join(
            [
                f
                for f, c in [
                    ("very_large_abs_gt_20", _to_int(r.get("very_large_abs_gt_20_count", 0)) > 0),
                    ("percent_like", _to_int(r.get("percent_like_count", 0)) > 0),
                    ("mixed_chinese_text", _to_int(r.get("mixed_chinese_text_count", 0)) > 0),
                    ("non_numeric_value", _to_int(r.get("non_numeric_value_count", 0)) > 0),
                ]
                if c
            ]
        ),
        axis=1,
    )
    template["suspicious_priority_score"] = template.apply(
        lambda r: _to_int(r.get("suspicious_row_count", 0)) * 10
        + _to_int(r.get("very_large_abs_gt_20_count", 0)) * 5
        + _to_int(r.get("percent_like_count", 0)) * 3
        + _to_int(r.get("mixed_chinese_text_count", 0)) * 2
        + _to_int(r.get("non_numeric_value_count", 0)) * 1,
        axis=1,
    )
    template["is_suspicious_group"] = template["suspicious_priority_score"].map(lambda x: _to_int(x) > 0)

    # review fields
    template["decision"] = ""
    template["reviewer_id"] = ""
    template["reviewed_at"] = ""
    template["review_comment"] = ""
    for y in YEAR_COLS:
        template[f"corrected_{y}"] = ""
    template["corrected_unit"] = ""
    template["extra_info_request"] = ""

    # output ordering: suspicious first, then by row count, then pdf/group
    template = template.sort_values(
        by=["is_suspicious_group", "suspicious_priority_score", "current_row_count", "PDF文件名", "group_id"],
        ascending=[False, False, False, True, True],
    ).reset_index(drop=True)

    cols_front = [
        "PDF文件名",
        "group_id",
        "source_page",
        "source_parser",
        "blocker_reasons",
        "suspicious_value_flags",
        "suspicious_priority_score",
        "is_suspicious_group",
        "current_row_count",
    ]
    review_cols = ["decision", "reviewer_id", "reviewed_at", "review_comment"] + [f"corrected_{y}" for y in YEAR_COLS] + ["corrected_unit", "extra_info_request"]
    keep_cols = cols_front + YEAR_COLS + review_cols + ["source_panel_id"]
    for c in keep_cols:
        if c not in template.columns:
            template[c] = ""
    template = template[keep_cols]

    # suspicious priority table
    suspicious_priority = template[template["is_suspicious_group"] == True].copy()

    # by-pdf review order
    by_pdf_order = (
        template.groupby("PDF文件名", dropna=False)
        .agg(
            eps_group_count=("group_id", "nunique"),
            suspicious_group_count=("is_suspicious_group", lambda x: int(sum(bool(v) for v in x))),
            total_priority_score=("suspicious_priority_score", lambda x: int(sum(_to_int(v) for v in x))),
            group_id_list=("group_id", lambda x: "|".join(sorted({_norm(v) for v in x if _norm(v) != ""}))),
        )
        .reset_index()
        .sort_values(["suspicious_group_count", "total_priority_score", "eps_group_count"], ascending=[False, False, False])
    )

    # group->candidate manifest preserved (EPS must-review groups)
    map_rows["标准指标"] = map_rows["标准指标"].map(_norm).str.lower()
    eps_map = map_rows[(map_rows["标准指标"] == "eps") & (map_rows["group_id"].isin(eps_group_ids))].copy()
    eps_map["candidate_id"] = eps_map["candidate_id"].map(_norm)

    _write_excel(OUT_TEMPLATE, {"eps_grouped_review_template": template})
    _write_excel(OUT_SUSP_PRIORITY, {"eps_suspicious_review_priority": suspicious_priority if not suspicious_priority.empty else pd.DataFrame([{"note": "no_suspicious_eps_groups"}])})
    _write_excel(OUT_PDF_ORDER, {"eps_by_pdf_review_order": by_pdf_order})
    _write_excel(OUT_MAP, {"eps_group_to_candidate_manifest": eps_map})

    readme_lines = [
        "# 307D EPS Focused Human Review README",
        "",
        "## Decision Enum",
        "- approve_eps_series",
        "- reject_eps_series",
        "- correct_eps_series",
        "- needs_more_info",
        "",
        "## Validation Rules",
        "- decision=correct_eps_series: at least one corrected_2020...corrected_2030 or corrected_unit must be provided.",
        "- decision=needs_more_info: extra_info_request is required.",
        "- reviewer_id and reviewed_at are required for all non-empty decisions.",
        "",
        "## Safety",
        "- This package is review-only. No safe_to_apply / approve_for_real_apply fields are included.",
    ]
    OUT_README.write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

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

    forbidden_fields_generated = sorted([c for c in set(template.columns).union(set(eps_map.columns)) if c in FORBIDDEN_FIELDS])

    # assertions
    eps_group_count = int(template["group_id"].nunique()) if not template.empty else 0
    suspicious_prioritized = True
    if len(template) > 1:
        # check monotonic non-increasing suspicious flag in sorted table front
        flags = template["is_suspicious_group"].tolist()
        first_false = next((i for i, v in enumerate(flags) if not bool(v)), len(flags))
        suspicious_prioritized = all(bool(v) for v in flags[:first_false]) and all(not bool(v) for v in flags[first_false:])
    group_to_candidate_mapping_preserved = int(eps_map["group_id"].nunique()) == eps_group_count

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-307D",
        "mode": "eps_focused_human_review_package",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eps_group_count": eps_group_count,
        "eps_must_review_group_count_from_307c": int(must_group_count),
        "eps_group_count_matches_307c": bool(eps_group_count == must_group_count),
        "suspicious_eps_groups_prioritized": bool(suspicious_prioritized),
        "group_to_candidate_mapping_preserved": bool(group_to_candidate_mapping_preserved),
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
        "# 307D EPS Focused Human Review Package",
        "",
        "## Core Counts",
        f"- eps_group_count: {summary['eps_group_count']}",
        f"- eps_must_review_group_count_from_307c: {summary['eps_must_review_group_count_from_307c']}",
        f"- eps_group_count_matches_307c: {summary['eps_group_count_matches_307c']}",
        "",
        "## Package Checks",
        f"- suspicious_eps_groups_prioritized: {summary['suspicious_eps_groups_prioritized']}",
        f"- group_to_candidate_mapping_preserved: {summary['group_to_candidate_mapping_preserved']}",
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

    print(f"eval_307d_summary_json: {OUT_SUMMARY}")
    print(f"eval_307d_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
