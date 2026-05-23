import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"

STAGE5S_SUMMARY_JSON = OUTPUT_DIR / "stage5s_real_apply" / "163_stage5s_real_apply_summary.json"
STAGE5R_RISK_REVIEW_XLSX = OUTPUT_DIR / "stage5r_final_apply_plan" / "160_stage5r_apply_risk_review.xlsx"

OUT_DIR = OUTPUT_DIR / "stage5t_post_apply_verify_06_dry_run"
OUT_VERIFY_XLSX = OUT_DIR / "164_stage5t_post_apply_verification.xlsx"
OUT_DRYRUN_XLSX = OUT_DIR / "164_stage5t_06_impact_dry_run.xlsx"
OUT_DIFF_MD = OUT_DIR / "164_stage5t_06_impact_diff.md"
OUT_SUMMARY_JSON = OUT_DIR / "165_stage5t_post_apply_06_dry_run_summary.json"

FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_STANDARDIZER = BASE_DIR / "financial_standardizer.py"

SHEET_APPLIED_02 = "stage5s_applied_02_long"
SHEET_APPLIED_05 = "stage5s_applied_05_long"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def _find_current_06() -> Path:
    delivery_dir = OUTPUT_DIR / "delivery_package"
    if not delivery_dir.exists():
        raise FileNotFoundError(f"Missing delivery package directory: {delivery_dir}")
    candidates = sorted(delivery_dir.glob("06_*.xlsx"))
    if not candidates:
        raise FileNotFoundError("No 06 workbook found in output/delivery_package.")
    non_copy = [p for p in candidates if "_copy_" not in p.name.lower()]
    return non_copy[0] if non_copy else candidates[0]


def _first_sheet(path: Path) -> str:
    xls = pd.ExcelFile(path)
    if not xls.sheet_names:
        raise RuntimeError(f"No sheets found: {path}")
    return xls.sheet_names[0]


def _duplicate_and_conflicts(df: pd.DataFrame) -> Tuple[int, int, int, int]:
    if df.empty:
        return 0, 0, 0, 0
    work = df.copy()
    work["metric_level_key"] = work.get("metric_level_key", "").map(_norm)
    work["year"] = work.get("year", "").map(_norm)
    work["value"] = work.get("value", "").map(_norm)
    work["unit"] = work.get("unit", "").map(_norm)
    work["key"] = work["metric_level_key"] + "||" + work["year"]

    duplicate_key_count = int(work["key"].duplicated().sum())
    value_conflict_count = 0
    unit_conflict_count = 0
    year_conflict_count = 0

    for _, grp in work.groupby("metric_level_key"):
        years = [y for y in grp["year"].tolist() if y]
        if len(years) != len(set(years)):
            year_conflict_count += 1
    for _, grp in work.groupby("key"):
        if grp["value"].nunique() > 1:
            value_conflict_count += 1
        if grp["unit"].nunique() > 1:
            unit_conflict_count += 1
    return duplicate_key_count, value_conflict_count, unit_conflict_count, year_conflict_count


def _build_06_candidate_rows(applied_05: pd.DataFrame) -> pd.DataFrame:
    work = applied_05.copy()
    for col in ["asset_package", "source_pdf", "standard_metric", "year", "value", "unit"]:
        if col not in work.columns:
            work[col] = ""
    work = work[
        work["standard_metric"].map(_norm).ne("")
        & work["year"].map(_norm).ne("")
    ].copy()

    work["asset_package"] = work["asset_package"].map(_norm)
    work["source_pdf"] = work["source_pdf"].map(_norm)
    work["standard_metric"] = work["standard_metric"].map(_norm)
    work["year"] = work["year"].map(_norm)
    work["value"] = work["value"].map(_norm)
    work["unit"] = work["unit"].map(_norm)
    work["key"] = (
        work["asset_package"]
        + "||"
        + work["source_pdf"]
        + "||"
        + work["standard_metric"]
        + "||"
        + work["year"]
    )
    return work


def _dry_run_06(current_06: pd.DataFrame, applied_05: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, int]:
    candidate = _build_06_candidate_rows(applied_05)
    dry_conflict_count = 0

    # candidate internal conflicts
    for _, grp in candidate.groupby("key"):
        if grp["value"].nunique() > 1 or grp["unit"].nunique() > 1:
            dry_conflict_count += 1

    # keep deterministic representative row per key
    candidate_dedup = candidate.drop_duplicates(subset=["key"], keep="first").copy()

    c06 = current_06.copy()
    for col in ["asset_package", "source_pdf", "standard_metric", "year", "final_value", "final_unit"]:
        if col not in c06.columns:
            c06[col] = ""
    c06["asset_package"] = c06["asset_package"].map(_norm)
    c06["source_pdf"] = c06["source_pdf"].map(_norm)
    c06["standard_metric"] = c06["standard_metric"].map(_norm)
    c06["year"] = c06["year"].map(_norm)
    c06["final_value"] = c06["final_value"].map(_norm)
    c06["final_unit"] = c06["final_unit"].map(_norm)
    c06["key"] = (
        c06["asset_package"]
        + "||"
        + c06["source_pdf"]
        + "||"
        + c06["standard_metric"]
        + "||"
        + c06["year"]
    )

    current_index = {k: i for i, k in enumerate(c06["key"].tolist())}
    dry_run = c06.copy()
    new_rows: List[Dict[str, Any]] = []
    changed_rows: List[Dict[str, Any]] = []

    for _, row in candidate_dedup.iterrows():
        key = row["key"]
        cand_val = _norm(row["value"])
        cand_unit = _norm(row["unit"])
        if key not in current_index:
            rec = {c: "" for c in dry_run.columns}
            rec["source_pdf"] = row["source_pdf"]
            rec["asset_package"] = row["asset_package"]
            rec["standard_metric"] = row["standard_metric"]
            rec["year"] = row["year"]
            rec["final_value"] = cand_val
            rec["final_unit"] = cand_unit
            rec["final_value_source"] = "STAGE5T_DRY_RUN_FROM_05"
            rec["final_review_status"] = "DRY_RUN_CANDIDATE"
            rec["key"] = key
            new_rows.append(rec)
            continue

        idx = current_index[key]
        cur_val = _norm(dry_run.at[idx, "final_value"])
        cur_unit = _norm(dry_run.at[idx, "final_unit"])
        if cur_val != cand_val or cur_unit != cand_unit:
            changed_rows.append(
                {
                    "key": key,
                    "asset_package": row["asset_package"],
                    "source_pdf": row["source_pdf"],
                    "standard_metric": row["standard_metric"],
                    "year": row["year"],
                    "current_final_value": cur_val,
                    "current_final_unit": cur_unit,
                    "dry_run_value": cand_val,
                    "dry_run_unit": cand_unit,
                }
            )
            dry_run.at[idx, "final_value"] = cand_val
            dry_run.at[idx, "final_unit"] = cand_unit
            dry_run.at[idx, "final_value_source"] = "STAGE5T_DRY_RUN_FROM_05"
            dry_run.at[idx, "final_review_status"] = "DRY_RUN_CHANGED"

    if new_rows:
        dry_run = pd.concat([dry_run, pd.DataFrame(new_rows)], ignore_index=True)
    dry_run = dry_run.drop(columns=["key"], errors="ignore")
    return (
        dry_run,
        pd.DataFrame(new_rows),
        pd.DataFrame(changed_rows),
        dry_conflict_count,
    )


def main() -> int:
    if not STAGE5S_SUMMARY_JSON.exists():
        raise FileNotFoundError(f"Missing input: {STAGE5S_SUMMARY_JSON}")
    if not STAGE5R_RISK_REVIEW_XLSX.exists():
        raise FileNotFoundError(f"Missing input: {STAGE5R_RISK_REVIEW_XLSX}")

    s5s = json.loads(STAGE5S_SUMMARY_JSON.read_text(encoding="utf-8"))
    prod02 = Path(_norm(s5s.get("production_02_file")))
    prod05 = Path(_norm(s5s.get("production_05_file")))
    prod06 = _find_current_06()

    for p in [prod02, prod05, prod06, FORMAL_SCOPE_RULES, FORMAL_STANDARDIZER]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required file: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    formal_hash_before = {
        "scope": _sha256(FORMAL_SCOPE_RULES),
        "std": _sha256(FORMAL_STANDARDIZER),
    }
    production_06_hash_before = _sha256(prod06)

    applied_02 = pd.read_excel(prod02, sheet_name=SHEET_APPLIED_02).fillna("")
    applied_05 = pd.read_excel(prod05, sheet_name=SHEET_APPLIED_05).fillna("")

    production_02_applied_metric_count = int(applied_02["metric_level_key"].map(_norm).nunique()) if "metric_level_key" in applied_02.columns else 0
    production_02_applied_row_count = int(len(applied_02))
    production_05_applied_metric_count = int(applied_05["metric_level_key"].map(_norm).nunique()) if "metric_level_key" in applied_05.columns else 0
    production_05_applied_row_count = int(len(applied_05))

    risk_df = pd.read_excel(STAGE5R_RISK_REVIEW_XLSX, sheet_name="excluded_review_queue").fillna("")
    risk_df["recommended_action"] = risk_df["recommended_action"].map(_norm)
    risk_df["metric_level_key"] = risk_df["metric_level_key"].map(_norm)

    need_mapping = set(
        risk_df.loc[risk_df["recommended_action"].eq("NEED_MAPPING_RULE"), "metric_level_key"].tolist()
    )
    need_scope = set(
        risk_df.loc[risk_df["recommended_action"].eq("NEED_SCOPE_REVIEW"), "metric_level_key"].tolist()
    )

    applied_02["metric_level_key"] = applied_02.get("metric_level_key", "").map(_norm)
    applied_05["metric_level_key"] = applied_05.get("metric_level_key", "").map(_norm)

    excluded_need_mapping_written_count = int(
        applied_02["metric_level_key"].isin(need_mapping).sum()
        + applied_05["metric_level_key"].isin(need_mapping).sum()
    )
    excluded_need_scope_review_written_count = int(
        applied_02["metric_level_key"].isin(need_scope).sum()
        + applied_05["metric_level_key"].isin(need_scope).sum()
    )

    duplicate_key_count_02, value_conflict_02, unit_conflict_02, year_conflict_02 = _duplicate_and_conflicts(applied_02)
    duplicate_key_count_05, value_conflict_05, unit_conflict_05, year_conflict_05 = _duplicate_and_conflicts(applied_05)

    value_conflict_count = int(value_conflict_02 + value_conflict_05)
    unit_conflict_count = int(unit_conflict_02 + unit_conflict_05)
    year_conflict_count = int(year_conflict_02 + year_conflict_05)

    sheet06 = _first_sheet(prod06)
    current_06 = pd.read_excel(prod06, sheet_name=sheet06).fillna("")
    production_06_current_row_count = int(len(current_06))

    dry_run_06, dry_new, dry_changed, dry_conflict_count = _dry_run_06(current_06, applied_05)
    dry_run_06_row_count = int(len(dry_run_06))
    dry_run_06_new_row_count = int(len(dry_new))
    dry_run_06_changed_row_count = int(len(dry_changed))

    _write_excel(
        OUT_VERIFY_XLSX,
        {
            "applied_02_rows": applied_02,
            "applied_05_rows": applied_05,
            "excluded_review_queue": risk_df,
            "excluded_hits": pd.DataFrame(
                {
                    "metric_level_key": sorted(set(need_mapping) | set(need_scope)),
                    "in_need_mapping": [m in need_mapping for m in sorted(set(need_mapping) | set(need_scope))],
                    "in_need_scope_review": [m in need_scope for m in sorted(set(need_mapping) | set(need_scope))],
                }
            ),
        },
    )
    _write_excel(
        OUT_DRYRUN_XLSX,
        {
            "current_06": current_06,
            "dry_run_06": dry_run_06,
            "dry_run_new_rows": dry_new,
            "dry_run_changed_rows": dry_changed,
        },
    )

    formal_hash_after = {
        "scope": _sha256(FORMAL_SCOPE_RULES),
        "std": _sha256(FORMAL_STANDARDIZER),
    }
    formal_rules_unchanged = bool(formal_hash_before == formal_hash_after)
    production_06_hash_after = _sha256(prod06)
    production_06_unchanged = bool(production_06_hash_before == production_06_hash_after)

    ready_for_stage5u_update_06 = bool(
        production_02_applied_metric_count == 59
        and production_02_applied_row_count == 295
        and production_05_applied_metric_count == 9
        and production_05_applied_row_count == 45
        and excluded_need_mapping_written_count == 0
        and excluded_need_scope_review_written_count == 0
        and duplicate_key_count_02 == 0
        and duplicate_key_count_05 == 0
        and value_conflict_count == 0
        and unit_conflict_count == 0
        and year_conflict_count == 0
        and dry_conflict_count == 0
        and production_06_unchanged
        and formal_rules_unchanged
    )

    summary = {
        "production_02_applied_metric_count": production_02_applied_metric_count,
        "production_02_applied_row_count": production_02_applied_row_count,
        "production_05_applied_metric_count": production_05_applied_metric_count,
        "production_05_applied_row_count": production_05_applied_row_count,
        "excluded_need_mapping_written_count": excluded_need_mapping_written_count,
        "excluded_need_scope_review_written_count": excluded_need_scope_review_written_count,
        "duplicate_key_count_02": duplicate_key_count_02,
        "duplicate_key_count_05": duplicate_key_count_05,
        "value_conflict_count": value_conflict_count,
        "unit_conflict_count": unit_conflict_count,
        "year_conflict_count": year_conflict_count,
        "production_06_current_row_count": production_06_current_row_count,
        "dry_run_06_row_count": dry_run_06_row_count,
        "dry_run_06_new_row_count": dry_run_06_new_row_count,
        "dry_run_06_changed_row_count": dry_run_06_changed_row_count,
        "dry_run_06_conflict_count": int(dry_conflict_count),
        "ready_for_stage5u_update_06": ready_for_stage5u_update_06,
        "production_06_unchanged": production_06_unchanged,
        "formal_rules_unchanged": formal_rules_unchanged,
        "stage5t_post_apply_verify_pass": False,
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
    }

    summary["stage5t_post_apply_verify_pass"] = bool(
        summary["production_02_applied_metric_count"] == 59
        and summary["production_02_applied_row_count"] == 295
        and summary["production_05_applied_metric_count"] == 9
        and summary["production_05_applied_row_count"] == 45
        and summary["excluded_need_mapping_written_count"] == 0
        and summary["excluded_need_scope_review_written_count"] == 0
        and summary["duplicate_key_count_02"] == 0
        and summary["duplicate_key_count_05"] == 0
        and summary["value_conflict_count"] == 0
        and summary["unit_conflict_count"] == 0
        and summary["year_conflict_count"] == 0
        and summary["dry_run_06_conflict_count"] == 0
        and summary["production_06_unchanged"]
        and summary["formal_rules_unchanged"]
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    diff_lines = [
        "# Stage5T 06 Impact Dry-Run Diff",
        "",
        "## 02/05 Post-Apply Verification",
        f"- production_02_applied_metric_count: {summary['production_02_applied_metric_count']}",
        f"- production_02_applied_row_count: {summary['production_02_applied_row_count']}",
        f"- production_05_applied_metric_count: {summary['production_05_applied_metric_count']}",
        f"- production_05_applied_row_count: {summary['production_05_applied_row_count']}",
        f"- excluded_need_mapping_written_count: {summary['excluded_need_mapping_written_count']}",
        f"- excluded_need_scope_review_written_count: {summary['excluded_need_scope_review_written_count']}",
        "",
        "## 06 Dry-Run Impact",
        f"- production_06_current_row_count: {summary['production_06_current_row_count']}",
        f"- dry_run_06_row_count: {summary['dry_run_06_row_count']}",
        f"- dry_run_06_new_row_count: {summary['dry_run_06_new_row_count']}",
        f"- dry_run_06_changed_row_count: {summary['dry_run_06_changed_row_count']}",
        f"- dry_run_06_conflict_count: {summary['dry_run_06_conflict_count']}",
        "",
        "## Decision",
        f"- ready_for_stage5u_update_06: {summary['ready_for_stage5u_update_06']}",
        f"- stage5t_post_apply_verify_pass: {summary['stage5t_post_apply_verify_pass']}",
    ]
    OUT_DIFF_MD.write_text("\n".join(diff_lines), encoding="utf-8")

    print(f"verify_xlsx: {OUT_VERIFY_XLSX}")
    print(f"dryrun_xlsx: {OUT_DRYRUN_XLSX}")
    print(f"diff_md: {OUT_DIFF_MD}")
    print(f"summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5t_post_apply_verify_pass: {summary['stage5t_post_apply_verify_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
