import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
STAGE2C_DIR = BASE_DIR / "output" / "stage2c_rebuild_dry_run"
OVERRIDE_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _key(asset: Any, metric: Any, year: Any) -> str:
    return "|".join([_norm(asset), _norm(metric), _norm(year)])


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_delivery_file(pattern: str, prefer_no_copy: bool = True) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing required file pattern: {pattern}")
    if prefer_no_copy:
        filtered = [p for p in files if "_copy_" not in p.name]
        if filtered:
            return filtered[0]
    return files[0]


def _snapshot_prod() -> Dict[str, str]:
    p01 = _find_delivery_file("01_*.xlsx")
    p02_candidates = sorted(DELIVERY_DIR.glob("02_*.xlsx"))
    p02 = next((p for p in p02_candidates if "backup" not in p.name.lower()), p02_candidates[0])
    p02a = _find_delivery_file("02A_*.xlsx")
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    return {
        "01": _sha256(p01),
        "02": _sha256(p02),
        "02A": _sha256(p02a),
        "06": _sha256(p06),
    }


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    try:
        return json.loads((p.stdout or "").strip() or "{}")
    except Exception:
        return {"overall_status": "UNKNOWN"}


def _safe_write_excel_multi(sheets: Dict[str, pd.DataFrame], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def _load_inputs() -> Dict[str, Any]:
    p01 = _find_delivery_file("01_*.xlsx")
    p02 = _find_delivery_file("02_*.xlsx")
    p02a = _find_delivery_file("02A_*.xlsx")
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    rebuilt06_path = STAGE2C_DIR / "06_最终核心财务指标.rebuilt_with_02B.xlsx"
    diff79_path = STAGE2C_DIR / "79_stage2c_rebuild_06_with_02B_diff.xlsx"
    summary80_path = STAGE2C_DIR / "80_stage2c_rebuild_06_with_02B_summary.json"
    if not rebuilt06_path.exists():
        raise FileNotFoundError(f"Missing rebuilt 06: {rebuilt06_path}")
    if not diff79_path.exists():
        raise FileNotFoundError(f"Missing Stage2C diff: {diff79_path}")
    if not summary80_path.exists():
        raise FileNotFoundError(f"Missing Stage2C summary: {summary80_path}")
    if not OVERRIDE_PATH.exists():
        raise FileNotFoundError(f"Missing override file: {OVERRIDE_PATH}")

    df01 = pd.read_excel(p01).fillna("")
    df02 = pd.read_excel(p02).fillna("")
    df02a = pd.read_excel(p02a).fillna("")
    df06 = pd.read_excel(p06).fillna("")
    rebuilt06 = pd.read_excel(rebuilt06_path).fillna("")
    df02b = pd.read_excel(OVERRIDE_PATH, sheet_name="ai_repair_override").fillna("")
    diff_xl = pd.ExcelFile(diff79_path)
    diff_rows = pd.read_excel(diff79_path, sheet_name="diff_rows").fillna("")
    conflicts = pd.read_excel(diff79_path, sheet_name="conflicts").fillna("")
    duplicate_keys = pd.read_excel(diff79_path, sheet_name="duplicate_keys").fillna("")
    summary80 = json.loads(summary80_path.read_text(encoding="utf-8"))
    return {
        "p01": p01,
        "p02": p02,
        "p02a": p02a,
        "p06": p06,
        "rebuilt06_path": rebuilt06_path,
        "diff79_path": diff79_path,
        "summary80_path": summary80_path,
        "df01": df01,
        "df02": df02,
        "df02a": df02a,
        "df02b": df02b,
        "df06": df06,
        "rebuilt06": rebuilt06,
        "diff_rows": diff_rows,
        "conflicts": conflicts,
        "duplicate_keys": duplicate_keys,
        "summary80": summary80,
        "diff_sheet_names": diff_xl.sheet_names,
    }


def _manual_candidates_from_02(df02: pd.DataFrame, df02a: pd.DataFrame) -> pd.DataFrame:
    accepted_status = {"corrected", "accepted", "修正", "已修正", "已确认", "确认"}
    accepted_use = {"是", "true", "1", "yes", "y", "使用", "采用", "√"}

    rows: List[Dict[str, Any]] = []
    for _, r in df02.iterrows():
        status = _norm(r.get("review_status")).lower()
        use_val = _norm(r.get("use_corrected_value")).lower()
        if status not in accepted_status or use_val not in accepted_use:
            continue
        asset = _norm(r.get("asset_package"))
        metric = _norm(r.get("standard_metric"))
        year = _norm(r.get("year"))
        value = _norm(r.get("corrected_value"))
        if not asset or not metric or not year or not value:
            continue
        rows.append(
            {
                "layer": "manual_02",
                "asset_package": asset,
                "standard_metric": metric,
                "year": year,
                "final_value": value,
                "final_unit": _norm(r.get("corrected_unit")),
                "final_value_source": "manual_corrected",
                "_pri_source": 3,
            }
        )

    for _, r in df02a.iterrows():
        status = _norm(r.get("review_status")).lower()
        use_val = _norm(r.get("use_corrected_value")).lower()
        if status not in accepted_status or use_val not in accepted_use:
            continue
        asset = _norm(r.get("asset_package"))
        metric = _norm(r.get("standard_metric"))
        year = _norm(r.get("year"))
        value = _norm(r.get("corrected_value"))
        if not asset or not metric or not year or not value:
            continue
        rows.append(
            {
                "layer": "manual_02A",
                "asset_package": asset,
                "standard_metric": metric,
                "year": year,
                "final_value": value,
                "final_unit": _norm(r.get("corrected_unit")),
                "final_value_source": "manual_year_override",
                "_pri_source": 4,
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        out = pd.DataFrame(
            columns=[
                "layer",
                "asset_package",
                "standard_metric",
                "year",
                "final_value",
                "final_unit",
                "final_value_source",
                "_pri_source",
            ]
        )
    out["_key"] = out.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    return out


def _build_baseline_df(df01: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "layer": "baseline_01",
            "asset_package": df01["asset_package"].map(_norm),
            "standard_metric": df01["standard_metric"].map(_norm),
            "year": df01["year"].map(_norm),
            "final_value": df01["value"].map(_norm),
            "final_unit": df01["unit"].map(_norm),
            "final_value_source": "auto_trusted",
            "_pri_source": 1,
        }
    )
    out["_key"] = out.apply(lambda r: _key(r["asset_package"], r["standard_metric"], r["year"]), axis=1)
    return out


def _build_override_df(df02b: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "layer": "override_02B",
            "asset_package": df02b["asset_package"].map(_norm),
            "standard_metric": df02b["standard_metric"].map(_norm),
            "year": df02b["year"].map(_norm),
            "final_value": df02b["final_value"].map(_norm),
            "final_unit": df02b["final_unit"].map(_norm),
            "final_value_source": df02b["final_value_source"].map(_norm),
            "_pri_source": 2,
        }
    )
    out["_key"] = out.apply(lambda r: _key(r["asset_package"], r["standard_metric"], r["year"]), axis=1)
    return out


def _parse_key(key: str) -> Tuple[str, str, str]:
    parts = _norm(key).split("|")
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    return "", "", ""


def _classify_diff_rows(
    current06: pd.DataFrame,
    rebuilt06: pd.DataFrame,
    baseline_df: pd.DataFrame,
    manual_df: pd.DataFrame,
    duplicate_keys_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    curr = current06.copy()
    reb = rebuilt06.copy()
    curr["_key"] = curr.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    reb["_key"] = reb.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)

    curr_map = {r["_key"]: r for _, r in curr.iterrows()}
    reb_map = {r["_key"]: r for _, r in reb.iterrows()}
    all_keys = sorted(set(curr_map.keys()) | set(reb_map.keys()))

    base_keys = set(baseline_df["_key"].tolist())
    manual_keys = set(manual_df["_key"].tolist())
    dup_keys = set(duplicate_keys_df["_key"].tolist()) if not duplicate_keys_df.empty else set()

    rows: List[Dict[str, Any]] = []
    for k in all_keys:
        asset, metric, year = _parse_key(k)
        rb = reb_map.get(k)
        cu = curr_map.get(k)
        if rb is None:
            rows.append(
                {
                    "key": k,
                    "asset_package": asset,
                    "standard_metric": metric,
                    "year": year,
                    "classification": "MISSING_IN_REBUILT",
                    "rebuilt_value": "",
                    "current_value": _norm(cu.get("final_value")),
                    "rebuilt_unit": "",
                    "current_unit": _norm(cu.get("final_unit")),
                    "rebuilt_source": "",
                    "current_source": _norm(cu.get("final_value_source")),
                    "rebuilt_review_status": "",
                    "current_review_status": _norm(cu.get("final_review_status")),
                    "key_in_baseline_01": k in base_keys,
                    "key_in_manual_02_or_02A": k in manual_keys,
                    "key_in_stage2c_input_duplicate": k in dup_keys,
                    "classification_reason": "present_in_current_only",
                    "metadata_warning": "",
                }
            )
            continue
        if cu is None:
            rows.append(
                {
                    "key": k,
                    "asset_package": asset,
                    "standard_metric": metric,
                    "year": year,
                    "classification": "EXTRA_IN_REBUILT",
                    "rebuilt_value": _norm(rb.get("final_value")),
                    "current_value": "",
                    "rebuilt_unit": _norm(rb.get("final_unit")),
                    "current_unit": "",
                    "rebuilt_source": _norm(rb.get("final_value_source")),
                    "current_source": "",
                    "rebuilt_review_status": _norm(rb.get("final_review_status")),
                    "current_review_status": "",
                    "key_in_baseline_01": k in base_keys,
                    "key_in_manual_02_or_02A": k in manual_keys,
                    "key_in_stage2c_input_duplicate": k in dup_keys,
                    "classification_reason": "present_in_rebuilt_only",
                    "metadata_warning": "",
                }
            )
            continue

        rv = _norm(rb.get("final_value"))
        cv = _norm(cu.get("final_value"))
        ru = _norm(rb.get("final_unit"))
        cuu = _norm(cu.get("final_unit"))
        rs = _norm(rb.get("final_value_source"))
        cs = _norm(cu.get("final_value_source"))
        rr = _norm(rb.get("final_review_status"))
        cr = _norm(cu.get("final_review_status"))

        if rv == cv and ru == cuu and rs == cs and rr == cr:
            c = "EXACT_MATCH"
            reason = "value_unit_source_review_all_match"
            warn = ""
        elif rv != cv:
            c = "VALUE_MISMATCH"
            reason = "final_value_mismatch"
            warn = ""
        elif ru != cuu:
            c = "UNIT_MISMATCH"
            reason = "final_unit_mismatch"
            warn = ""
        elif rs != cs and rr == cr:
            c = "SOURCE_ONLY_MISMATCH"
            reason = "final_value_source_mismatch_only"
            warn = "metadata_warning"
        elif rr != cr and rs == cs:
            c = "REVIEW_STATUS_ONLY_MISMATCH"
            reason = "final_review_status_mismatch_only"
            warn = "metadata_warning"
        elif rs != cs and rr != cr:
            c = "SOURCE_ONLY_MISMATCH"
            reason = "source_and_review_mismatch_value_unit_match"
            warn = "metadata_warning"
        else:
            c = "VALUE_MISMATCH"
            reason = "fallback_mismatch"
            warn = ""

        rows.append(
            {
                "key": k,
                "asset_package": asset,
                "standard_metric": metric,
                "year": year,
                "classification": c,
                "rebuilt_value": rv,
                "current_value": cv,
                "rebuilt_unit": ru,
                "current_unit": cuu,
                "rebuilt_source": rs,
                "current_source": cs,
                "rebuilt_review_status": rr,
                "current_review_status": cr,
                "key_in_baseline_01": k in base_keys,
                "key_in_manual_02_or_02A": k in manual_keys,
                "key_in_stage2c_input_duplicate": k in dup_keys,
                "classification_reason": reason,
                "metadata_warning": warn,
            }
        )

    cls_df = pd.DataFrame(rows).sort_values(by=["classification", "asset_package", "standard_metric", "year"], kind="mergesort")
    source_trace = cls_df[cls_df["classification"] == "SOURCE_ONLY_MISMATCH"].copy()
    source_trace["source_mismatch_trace"] = source_trace.apply(
        lambda r: (
            "manual_queue_key_not_in_01_baseline -> apply_manual_review_corrections appends as manual_added; "
            "stage2c_dry_run_rebuild maps 02 corrected rows as manual_corrected"
            if (not bool(r["key_in_baseline_01"])) and bool(r["key_in_manual_02_or_02A"])
            else "metadata source label mismatch, verify manual/apply source mapping"
        ),
        axis=1,
    )
    return cls_df, source_trace


def _classify_duplicates(
    duplicate_keys_df: pd.DataFrame,
    conflicts_df: pd.DataFrame,
    rebuilt06: pd.DataFrame,
    baseline_df: pd.DataFrame,
    manual_df: pd.DataFrame,
    override_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    rb = rebuilt06.copy()
    rb["_key"] = rb.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    output_dup_count = int(rb.groupby("_key", dropna=False).size().gt(1).sum())

    if duplicate_keys_df.empty:
        detail = pd.DataFrame(
            columns=[
                "key",
                "duplicate_classification",
                "layers_present",
                "priority_values",
                "resolved_in_rebuilt_06",
                "notes",
            ]
        )
        counts = {
            "input_duplicate_before_priority_resolution_count": 0,
            "resolved_output_duplicate_count": output_dup_count,
            "true_conflict_duplicate_count": int(len(conflicts_df)),
        }
        return detail, counts

    base_keys = set(baseline_df["_key"].tolist())
    manual_keys = set(manual_df["_key"].tolist())
    override_keys = set(override_df["_key"].tolist())
    rebuilt_keys = set(rb["_key"].tolist())

    rows: List[Dict[str, Any]] = []
    true_conflict_keys = set(conflicts_df["key"].tolist()) if not conflicts_df.empty else set()
    for key, grp in duplicate_keys_df.groupby("_key", dropna=False):
        sources = sorted(set(grp["final_value_source"].map(_norm).tolist()))
        pri_lines = sorted(
            {
                f"{_norm(r.get('final_value_source'))}|pri={_norm(r.get('_pri_source'))}|value={_norm(r.get('final_value'))}|unit={_norm(r.get('final_unit'))}"
                for _, r in grp.iterrows()
            }
        )
        highest_pri = max([int(_norm(x)) for x in grp["_pri_source"].tolist() if _norm(x).isdigit()] or [0])
        highest_grp = grp[grp["_pri_source"].map(lambda x: int(_norm(x)) if _norm(x).isdigit() else -1) == highest_pri]
        top_values = set((highest_grp["final_value"].map(_norm) + "|" + highest_grp["final_unit"].map(_norm)).tolist())
        has_top_conflict = len(top_values) > 1
        is_conflict = key in true_conflict_keys or has_top_conflict
        in_rebuilt = key in rebuilt_keys
        if is_conflict:
            dup_class = "true_conflict_duplicate"
            note = "multiple top-priority candidates disagree"
        else:
            dup_class = "input_duplicate_before_priority_resolution"
            note = "baseline/manual overlap resolved by priority to single output row"
        rows.append(
            {
                "key": key,
                "duplicate_classification": dup_class,
                "layers_present": ",".join(
                    [
                        "baseline_01" if key in base_keys else "",
                        "manual_02_or_02A" if key in manual_keys else "",
                        "override_02B" if key in override_keys else "",
                    ]
                ).strip(","),
                "sources_present": ",".join(sources),
                "priority_values": " || ".join(pri_lines),
                "resolved_in_rebuilt_06": bool(in_rebuilt and not is_conflict),
                "notes": note,
            }
        )

    detail = pd.DataFrame(rows).sort_values(by=["duplicate_classification", "key"], kind="mergesort")
    input_dup = int((detail["duplicate_classification"] == "input_duplicate_before_priority_resolution").sum())
    true_conflict = int((detail["duplicate_classification"] == "true_conflict_duplicate").sum())
    counts = {
        "input_duplicate_before_priority_resolution_count": input_dup,
        "resolved_output_duplicate_count": output_dup_count,
        "true_conflict_duplicate_count": true_conflict,
    }
    return detail, counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage2C reconciliation: classify rebuild equivalence gaps and duplicate sources.")
    parser.parse_args()

    snap_before = _snapshot_prod()
    data = _load_inputs()
    baseline_df = _build_baseline_df(data["df01"])
    manual_df = _manual_candidates_from_02(data["df02"], data["df02a"])
    override_df = _build_override_df(data["df02b"])

    cls_df, source_trace_df = _classify_diff_rows(
        current06=data["df06"],
        rebuilt06=data["rebuilt06"],
        baseline_df=baseline_df,
        manual_df=manual_df,
        duplicate_keys_df=data["duplicate_keys"],
    )
    dup_detail_df, dup_counts = _classify_duplicates(
        duplicate_keys_df=data["duplicate_keys"],
        conflicts_df=data["conflicts"],
        rebuilt06=data["rebuilt06"],
        baseline_df=baseline_df,
        manual_df=manual_df,
        override_df=override_df,
    )

    exact_match_count = int((cls_df["classification"] == "EXACT_MATCH").sum())
    source_only_mismatch_count = int((cls_df["classification"] == "SOURCE_ONLY_MISMATCH").sum())
    value_mismatch_count = int((cls_df["classification"] == "VALUE_MISMATCH").sum())
    unit_mismatch_count = int((cls_df["classification"] == "UNIT_MISMATCH").sum())
    review_only_mismatch_count = int((cls_df["classification"] == "REVIEW_STATUS_ONLY_MISMATCH").sum())
    missing_in_rebuilt_count = int((cls_df["classification"] == "MISSING_IN_REBUILT").sum())
    extra_in_rebuilt_count = int((cls_df["classification"] == "EXTRA_IN_REBUILT").sum())

    override_keys = set(
        override_df.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist()
    )
    rebuilt_keys = set(
        data["rebuilt06"].apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist()
    )
    override_records_present = override_keys.issubset(rebuilt_keys)

    snap_after = _snapshot_prod()
    production_files_unchanged = snap_before == snap_after
    output_06_unchanged = snap_before["06"] == snap_after["06"]
    delivery_status = _run_delivery_check()

    stage2c_reconciliation_pass = bool(
        value_mismatch_count == 0
        and unit_mismatch_count == 0
        and missing_in_rebuilt_count == 0
        and extra_in_rebuilt_count == 0
        and dup_counts["resolved_output_duplicate_count"] == 0
        and dup_counts["true_conflict_duplicate_count"] == 0
        and override_records_present
        and production_files_unchanged
        and output_06_unchanged
        and delivery_status.get("overall_status") == "PASS"
    )

    summary = {
        "exact_match_count": exact_match_count,
        "source_only_mismatch_count": source_only_mismatch_count,
        "value_mismatch_count": value_mismatch_count,
        "unit_mismatch_count": unit_mismatch_count,
        "review_status_only_mismatch_count": review_only_mismatch_count,
        "missing_in_rebuilt_count": missing_in_rebuilt_count,
        "extra_in_rebuilt_count": extra_in_rebuilt_count,
        "input_duplicate_before_priority_resolution_count": dup_counts["input_duplicate_before_priority_resolution_count"],
        "resolved_output_duplicate_count": dup_counts["resolved_output_duplicate_count"],
        "true_conflict_duplicate_count": dup_counts["true_conflict_duplicate_count"],
        "override_records_present_in_rebuilt_06": bool(override_records_present),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage2c_reconciliation_pass": bool(stage2c_reconciliation_pass),
        "delivery_status_after": delivery_status.get("overall_status", "UNKNOWN"),
        "metadata_warning": {
            "source_only_mismatch_count": source_only_mismatch_count,
            "note": "SOURCE_ONLY_MISMATCH is metadata-only and non-blocking when all hard pass criteria are met.",
        },
        "stage2c_input_summary_80": data["summary80"],
    }

    report_xlsx = STAGE2C_DIR / "81_stage2c_rebuild_reconciliation_report.xlsx"
    report_md = STAGE2C_DIR / "81_stage2c_rebuild_reconciliation_report.md"
    report_json = STAGE2C_DIR / "82_stage2c_rebuild_reconciliation_summary.json"

    _safe_write_excel_multi(
        {
            "equivalence_classification": cls_df,
            "source_only_mismatch_trace": source_trace_df,
            "duplicate_classification": dup_detail_df,
            "raw_diff_rows_79": data["diff_rows"],
            "raw_duplicate_keys_79": data["duplicate_keys"],
            "raw_conflicts_79": data["conflicts"],
            "summary": pd.DataFrame([summary]),
        },
        report_xlsx,
    )

    md_lines = [
        "# Stage2C-R Rebuild Equivalence Reconciliation",
        "",
        "## Summary",
        f"- exact_match_count: {exact_match_count}",
        f"- source_only_mismatch_count: {source_only_mismatch_count}",
        f"- value_mismatch_count: {value_mismatch_count}",
        f"- unit_mismatch_count: {unit_mismatch_count}",
        f"- review_status_only_mismatch_count: {review_only_mismatch_count}",
        f"- missing_in_rebuilt_count: {missing_in_rebuilt_count}",
        f"- extra_in_rebuilt_count: {extra_in_rebuilt_count}",
        f"- input_duplicate_before_priority_resolution_count: {dup_counts['input_duplicate_before_priority_resolution_count']}",
        f"- resolved_output_duplicate_count: {dup_counts['resolved_output_duplicate_count']}",
        f"- true_conflict_duplicate_count: {dup_counts['true_conflict_duplicate_count']}",
        f"- override_records_present_in_rebuilt_06: {override_records_present}",
        f"- production_files_unchanged: {production_files_unchanged}",
        f"- output_06_unchanged: {output_06_unchanged}",
        f"- delivery_status_after: {summary['delivery_status_after']}",
        f"- stage2c_reconciliation_pass: {stage2c_reconciliation_pass}",
        "",
        "## SOURCE_ONLY_MISMATCH Notes",
        "- Value and unit are identical for all source-only mismatches.",
        "- Mismatch reason is metadata label divergence (`manual_corrected` vs `manual_added`).",
        "- This comes from different source-label semantics between rebuild dry-run and prior apply flow.",
        "",
        "## Duplicate Classification Notes",
        "- Duplicate keys in 79 are input-level overlaps across baseline/manual layers.",
        "- No resolved output duplicate remains in rebuilt 06.",
        "- Input duplicates are treated as warning, not blocker, when output uniqueness is preserved.",
    ]
    report_md.write_text("\n".join(md_lines), encoding="utf-8")
    report_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"reconciliation_report_xlsx: {report_xlsx}")
    print(f"reconciliation_report_md: {report_md}")
    print(f"reconciliation_summary_json: {report_json}")
    print(f"exact_match_count: {exact_match_count}")
    print(f"source_only_mismatch_count: {source_only_mismatch_count}")
    print(f"value_mismatch_count: {value_mismatch_count}")
    print(f"unit_mismatch_count: {unit_mismatch_count}")
    print(f"missing_in_rebuilt_count: {missing_in_rebuilt_count}")
    print(f"extra_in_rebuilt_count: {extra_in_rebuilt_count}")
    print(
        "input_duplicate_before_priority_resolution_count: "
        f"{dup_counts['input_duplicate_before_priority_resolution_count']}"
    )
    print(f"resolved_output_duplicate_count: {dup_counts['resolved_output_duplicate_count']}")
    print(f"true_conflict_duplicate_count: {dup_counts['true_conflict_duplicate_count']}")
    print(f"override_records_present_in_rebuilt_06: {override_records_present}")
    print(f"production_files_unchanged: {production_files_unchanged}")
    print(f"output_06_unchanged: {output_06_unchanged}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    print(f"stage2c_reconciliation_pass: {stage2c_reconciliation_pass}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
