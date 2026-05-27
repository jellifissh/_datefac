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
OUT_DIR = BASE_DIR / "output" / "eval_306l_grouped_human_review_package"

IN_306J_SUMMARY = BASE_DIR / "output" / "eval_306j_clean_candidate_human_review_input_design" / "306j_summary.json"
IN_MANIFEST = BASE_DIR / "output" / "eval_306j_clean_candidate_human_review_input_design" / "306j_candidate_id_manifest.xlsx"
IN_306I_REVIEW = BASE_DIR / "output" / "eval_306i_clean_candidate_review_package" / "306i_clean_core_candidates_review.xlsx"
IN_306H_FIX2_SUMMARY = BASE_DIR / "output" / "eval_306h_fix2_alias_recovery_growth_guard" / "306h_fix2_summary.json"

OUT_SUMMARY = OUT_DIR / "306l_summary.json"
OUT_REPORT = OUT_DIR / "306l_report.md"
OUT_GROUPED = OUT_DIR / "306l_grouped_review_table.xlsx"
OUT_HIGH = OUT_DIR / "306l_high_priority_review.xlsx"
OUT_MED = OUT_DIR / "306l_medium_priority_review.xlsx"
OUT_LOW = OUT_DIR / "306l_low_priority_auto_accept_candidates.xlsx"
OUT_MAP = OUT_DIR / "306l_group_to_candidate_manifest.xlsx"
OUT_NO_APPLY = OUT_DIR / "306l_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

YEARS = list(range(2020, 2031))
YEAR_COLS = [str(y) for y in YEARS]

GROUP_KEYS = ["PDF文件名", "标准指标", "指标名", "单位", "来源解析器", "source_panel_id"]


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


def _to_bool(v: Any) -> bool:
    s = _norm(v).lower()
    return s in {"true", "1", "yes"}


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


def _priority(row: pd.Series) -> str:
    high = (
        _to_bool(row.get("alias_recovered", False))
        or _to_bool(row.get("zero_candidate_rescued", False))
        or _to_bool(row.get("multi_panel_source", False))
        or _to_bool(row.get("page1_summary", False))
        or _to_bool(row.get("missing_year", False))
    )
    medium = _to_bool(row.get("unit_unknown", False)) or _to_bool(row.get("marker_only", False))
    if high:
        return "HIGH"
    if medium:
        return "MEDIUM"
    return "LOW"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306J_SUMMARY, IN_MANIFEST, IN_306I_REVIEW, IN_306H_FIX2_SUMMARY]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306L",
                "mode": "grouped_human_review_package",
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

    s_306j = json.loads(IN_306J_SUMMARY.read_text(encoding="utf-8"))
    s_fix2 = json.loads(IN_306H_FIX2_SUMMARY.read_text(encoding="utf-8"))
    manifest = pd.read_excel(IN_MANIFEST).fillna("")
    review = pd.read_excel(IN_306I_REVIEW).fillna("")

    # Join candidate_id from manifest.
    mcols = ["candidate_id", "row_uid"]
    if "row_uid" not in manifest.columns:
        raise RuntimeError("candidate_id_manifest missing row_uid")
    review = review.merge(manifest[mcols], on="row_uid", how="left")
    review["candidate_id"] = review["candidate_id"].map(_norm)
    review["年份_int"] = review["年份"].map(_to_int)
    review["数值_str"] = review["数值"].map(_norm)
    review["是否别名恢复_bool"] = review["是否别名恢复"].map(_to_bool)
    review["是否zero_candidate救回_bool"] = review["是否zero-candidate救回"].map(_to_bool)
    review["is_marker"] = review["来源解析器"].map(_norm).str.lower().eq("marker")
    review["is_page1"] = review["页码"].map(_to_int).eq(1)
    review["is_multi_panel"] = review["source_panel_id"].map(_norm).str.startswith("split|")

    # Group pivot
    grouped_rows: List[Dict[str, Any]] = []
    map_rows: List[Dict[str, Any]] = []

    for gvals, gdf in review.groupby(GROUP_KEYS, dropna=False):
        gdict = {k: _norm(v) for k, v in zip(GROUP_KEYS, gvals)}
        year_to_vals: Dict[int, List[str]] = {}
        for _, r in gdf.iterrows():
            y = _to_int(r["年份_int"])
            if y not in year_to_vals:
                year_to_vals[y] = []
            val = _norm(r["数值_str"])
            if val != "" and val not in year_to_vals[y]:
                year_to_vals[y].append(val)

        # year columns
        out = dict(gdict)
        for y in YEARS:
            vals = year_to_vals.get(y, [])
            out[str(y)] = " | ".join(vals) if vals else ""

        years_present = sorted([y for y in year_to_vals.keys() if y in YEARS and len(year_to_vals[y]) > 0])
        out["years_present"] = ",".join(str(y) for y in years_present)
        out["year_count"] = len(years_present)
        out["candidate_count"] = int(len(gdf))

        # flags
        out["missing_year"] = len(years_present) < 2
        out["unit_unknown"] = _norm(gdict.get("单位", "")).lower() in {"unknown", ""}
        out["alias_recovered"] = bool(gdf["是否别名恢复_bool"].any())
        out["zero_candidate_rescued"] = bool(gdf["是否zero_candidate救回_bool"].any())
        out["multi_panel_source"] = bool(gdf["is_multi_panel"].any())
        out["marker_only"] = bool(gdf["is_marker"].all())
        out["page1_summary"] = bool(gdf["is_page1"].any())
        out["review_priority"] = _priority(pd.Series(out))

        # group id
        basis = "|".join(
            [
                _norm(out["PDF文件名"]),
                _norm(out["标准指标"]),
                _norm(out["指标名"]),
                _norm(out["单位"]),
                _norm(out["来源解析器"]),
                _norm(out["source_panel_id"]),
            ]
        )
        gid = "G306L-" + hashlib.sha1(basis.encode("utf-8")).hexdigest()[:10].upper()
        out["group_id"] = gid
        grouped_rows.append(out)

        for _, r in gdf.iterrows():
            map_rows.append(
                {
                    "group_id": gid,
                    "candidate_id": _norm(r.get("candidate_id", "")),
                    "row_uid": _norm(r.get("row_uid", "")),
                    "PDF文件名": _norm(r.get("PDF文件名", "")),
                    "标准指标": _norm(r.get("标准指标", "")),
                    "年份": _to_int(r.get("年份", 0)),
                    "数值": _norm(r.get("数值", "")),
                }
            )

    grouped_df = pd.DataFrame(grouped_rows).fillna("")
    grouped_df = grouped_df.sort_values(
        ["review_priority", "PDF文件名", "标准指标", "指标名", "source_panel_id"],
        ascending=[True, True, True, True, True],
    )
    # order priority: HIGH, MEDIUM, LOW
    priority_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    grouped_df["_prio_rank"] = grouped_df["review_priority"].map(lambda x: priority_rank.get(_norm(x), 9))
    grouped_df = grouped_df.sort_values(["_prio_rank", "PDF文件名", "标准指标", "指标名"]).drop(columns=["_prio_rank"])

    map_df = pd.DataFrame(map_rows).fillna("")

    high_df = grouped_df[grouped_df["review_priority"] == "HIGH"].copy()
    med_df = grouped_df[grouped_df["review_priority"] == "MEDIUM"].copy()
    low_df = grouped_df[grouped_df["review_priority"] == "LOW"].copy()

    if high_df.empty:
        high_df = pd.DataFrame([{"note": "no_high_priority_group"}])
    if med_df.empty:
        med_df = pd.DataFrame([{"note": "no_medium_priority_group"}])
    if low_df.empty:
        low_df = pd.DataFrame([{"note": "no_low_priority_group"}])
    if map_df.empty:
        map_df = pd.DataFrame([{"note": "no_group_mapping"}])

    _write_excel(
        OUT_GROUPED,
        {
            "grouped_review_table": grouped_df,
            "priority_distribution": grouped_df.groupby("review_priority", dropna=False).size().reset_index(name="group_count"),
        },
    )
    _write_excel(OUT_HIGH, {"high_priority_review": high_df})
    _write_excel(OUT_MED, {"medium_priority_review": med_df})
    _write_excel(OUT_LOW, {"low_priority_auto_accept_candidates": low_df})
    _write_excel(OUT_MAP, {"group_to_candidate_manifest": map_df})

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "ocr_called": False,
            "marker_rerun_executed": False,
            "pdfplumber_rerun_executed": False,
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
        "stage": "EVAL-306L",
        "mode": "grouped_human_review_package",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "source_candidate_row_count": int(len(review)),
        "grouped_review_row_count": int(len(grouped_df)),
        "high_priority_group_count": int((grouped_df["review_priority"] == "HIGH").sum()),
        "medium_priority_group_count": int((grouped_df["review_priority"] == "MEDIUM").sum()),
        "low_priority_group_count": int((grouped_df["review_priority"] == "LOW").sum()),
        "group_to_candidate_mapping_row_count": int(len(map_df) if "note" not in map_df.columns else 0),
        "candidate_mapping_complete": bool(
            ("note" not in map_df.columns)
            and (map_df["candidate_id"].map(_norm) != "").all()
            and (map_df["group_id"].map(_norm) != "").all()
        ),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306L Grouped Human Review Package",
        "",
        f"- source_candidate_row_count: {summary['source_candidate_row_count']}",
        f"- grouped_review_row_count: {summary['grouped_review_row_count']}",
        f"- high_priority_group_count: {summary['high_priority_group_count']}",
        f"- medium_priority_group_count: {summary['medium_priority_group_count']}",
        f"- low_priority_group_count: {summary['low_priority_group_count']}",
        f"- group_to_candidate_mapping_row_count: {summary['group_to_candidate_mapping_row_count']}",
        f"- candidate_mapping_complete: {summary['candidate_mapping_complete']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306l_summary_json: {OUT_SUMMARY}")
    print(f"eval_306l_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
