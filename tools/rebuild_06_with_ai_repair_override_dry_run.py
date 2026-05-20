import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
OVERRIDE_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
STAGE2C_OUT = BASE_DIR / "output" / "stage2c_rebuild_dry_run"


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


def _safe_write_excel(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False, engine="openpyxl")


def _safe_write_excel_multi(sheets: Dict[str, pd.DataFrame], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def _load_inputs() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    p01 = _find_delivery_file("01_*.xlsx")
    p02 = _find_delivery_file("02_*.xlsx")
    p02a = _find_delivery_file("02A_*.xlsx")
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    if not OVERRIDE_PATH.exists():
        raise FileNotFoundError(f"Missing override table: {OVERRIDE_PATH}")

    df01 = pd.read_excel(p01).fillna("")
    df02 = pd.read_excel(p02).fillna("")
    df02a = pd.read_excel(p02a).fillna("")
    df02b = pd.read_excel(OVERRIDE_PATH, sheet_name="ai_repair_override").fillna("")
    df06 = pd.read_excel(p06).fillna("")
    return df01, df02, df02a, df02b, df06


def _build_baseline_from_01(df01: pd.DataFrame) -> pd.DataFrame:
    required = ["asset_package", "standard_metric", "year", "value", "unit"]
    for c in required:
        if c not in df01.columns:
            raise RuntimeError(f"01 missing required column: {c}")

    out = pd.DataFrame(
        {
            "asset_package": df01["asset_package"].map(_norm),
            "standard_metric": df01["standard_metric"].map(_norm),
            "year": df01["year"].map(_norm),
            "final_value": df01["value"].map(_norm),
            "final_unit": df01["unit"].map(_norm),
            "final_value_source": "auto_trusted",
            "final_review_status": "auto",
            "reviewer": "",
            "reviewed_at": "",
            "reviewer_note": "",
            "_pri_source": 1,
            "_pri_order": range(len(df01)),
        }
    )
    out["_key"] = out.apply(lambda r: _key(r["asset_package"], r["standard_metric"], r["year"]), axis=1)
    return out


def _collect_manual_candidates(df02: pd.DataFrame, df02a: pd.DataFrame) -> pd.DataFrame:
    # 02 candidates
    candidates: List[Dict[str, Any]] = []
    for _, r in df02.iterrows():
        review_status = _norm(r.get("review_status")).lower()
        use_corrected = _norm(r.get("use_corrected_value")).lower()
        if review_status not in {"corrected", "accepted", "修正", "已修正", "已确认", "确认"}:
            continue
        if use_corrected not in {"是", "true", "1", "yes", "y", "使用", "采用", "√"}:
            continue
        asset = _norm(r.get("asset_package"))
        metric = _norm(r.get("standard_metric"))
        year = _norm(r.get("year"))
        val = _norm(r.get("corrected_value"))
        if not asset or not metric or not year or not val:
            continue
        candidates.append(
            {
                "asset_package": asset,
                "standard_metric": metric,
                "year": year,
                "final_value": val,
                "final_unit": _norm(r.get("corrected_unit")),
                "final_value_source": "manual_corrected",
                "final_review_status": "corrected",
                "reviewer": _norm(r.get("reviewer")),
                "reviewed_at": _norm(r.get("reviewed_at")),
                "reviewer_note": _norm(r.get("reviewer_note")),
                "_pri_source": 3,
            }
        )

    # 02A year overrides
    for _, r in df02a.iterrows():
        review_status = _norm(r.get("review_status")).lower()
        use_corrected = _norm(r.get("use_corrected_value")).lower()
        if review_status not in {"corrected", "accepted", "修正", "已修正", "已确认", "确认"}:
            continue
        if use_corrected not in {"是", "true", "1", "yes", "y", "使用", "采用", "√"}:
            continue
        asset = _norm(r.get("asset_package"))
        metric = _norm(r.get("standard_metric"))
        year = _norm(r.get("year"))
        val = _norm(r.get("corrected_value"))
        if not asset or not metric or not year or not val:
            continue
        candidates.append(
            {
                "asset_package": asset,
                "standard_metric": metric,
                "year": year,
                "final_value": val,
                "final_unit": _norm(r.get("corrected_unit")),
                "final_value_source": "manual_year_override",
                "final_review_status": "corrected",
                "reviewer": _norm(r.get("reviewer")),
                "reviewed_at": _norm(r.get("reviewed_at")),
                "reviewer_note": _norm(r.get("reviewer_note")),
                "_pri_source": 4,
            }
        )

    out = pd.DataFrame(candidates)
    if out.empty:
        out = pd.DataFrame(
            columns=[
                "asset_package",
                "standard_metric",
                "year",
                "final_value",
                "final_unit",
                "final_value_source",
                "final_review_status",
                "reviewer",
                "reviewed_at",
                "reviewer_note",
                "_pri_source",
            ]
        )
    out["_key"] = out.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    out["_pri_order"] = range(len(out))
    return out


def _collect_override_candidates(df02b: pd.DataFrame) -> pd.DataFrame:
    required = ["asset_package", "standard_metric", "year", "final_value", "final_unit", "final_value_source", "final_review_status"]
    for c in required:
        if c not in df02b.columns:
            raise RuntimeError(f"02B missing required column: {c}")

    out = pd.DataFrame(
        {
            "asset_package": df02b["asset_package"].map(_norm),
            "standard_metric": df02b["standard_metric"].map(_norm),
            "year": df02b["year"].map(_norm),
            "final_value": df02b["final_value"].map(_norm),
            "final_unit": df02b["final_unit"].map(_norm),
            "final_value_source": df02b["final_value_source"].map(_norm),
            "final_review_status": df02b["final_review_status"].map(_norm),
            "reviewer": "",
            "reviewed_at": "",
            "reviewer_note": "",
            "_pri_source": 2,
        }
    )
    out["_key"] = out.apply(lambda r: _key(r["asset_package"], r["standard_metric"], r["year"]), axis=1)
    out["_pri_order"] = range(len(out))
    return out


def _merge_with_priority(base: pd.DataFrame, manual_df: pd.DataFrame, override_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    all_df = pd.concat([base, manual_df, override_df], ignore_index=True)
    all_df["_src_type"] = all_df["final_value_source"].map(
        lambda s: "manual" if _norm(s) in {"manual_corrected", "manual_year_override", "manual_added"} else ("override" if _norm(s) in {"ai_extract_real_apply", "ai_repair_override"} else "auto")
    )

    # conflicts: manual vs override same key value mismatch
    conflict_rows: List[Dict[str, Any]] = []
    for key, grp in all_df.groupby("_key", dropna=False):
        g_manual = grp[grp["_src_type"] == "manual"]
        g_override = grp[grp["_src_type"] == "override"]
        if g_manual.empty or g_override.empty:
            continue
        m = g_manual.iloc[0]
        for _, o in g_override.iterrows():
            if _norm(m.get("final_value")) != _norm(o.get("final_value")) or _norm(m.get("final_unit")) != _norm(o.get("final_unit")):
                conflict_rows.append(
                    {
                        "key": key,
                        "manual_value": _norm(m.get("final_value")),
                        "manual_unit": _norm(m.get("final_unit")),
                        "manual_source": _norm(m.get("final_value_source")),
                        "override_value": _norm(o.get("final_value")),
                        "override_unit": _norm(o.get("final_unit")),
                        "override_source": _norm(o.get("final_value_source")),
                        "conflict_reason": "manual_vs_override_value_mismatch",
                    }
                )

    # choose top priority per key: manual(4/3) > override(2) > auto(1)
    all_df = all_df.sort_values(by=["_key", "_pri_source", "_pri_order"], ascending=[True, False, True], kind="mergesort")
    rebuilt = all_df.drop_duplicates(subset=["_key"], keep="first").copy().reset_index(drop=True)

    # detect duplicate keys in input layers
    dup_keys = all_df[all_df.duplicated(subset=["_key"], keep=False)][["_key", "final_value_source", "final_value", "final_unit", "_pri_source"]].copy()

    return rebuilt, pd.DataFrame(conflict_rows), dup_keys


def _align_rebuilt_schema(rebuilt: pd.DataFrame, current06: pd.DataFrame) -> pd.DataFrame:
    # Keep delivery-facing 06 columns, fill unknowns.
    cols = list(current06.columns)
    out = pd.DataFrame(columns=cols)
    for c in cols:
        out[c] = ""

    for i, r in rebuilt.iterrows():
        out.at[i, "asset_package"] = _norm(r.get("asset_package"))
        out.at[i, "standard_metric"] = _norm(r.get("standard_metric"))
        out.at[i, "year"] = _norm(r.get("year"))
        out.at[i, "final_value"] = _norm(r.get("final_value"))
        out.at[i, "final_unit"] = _norm(r.get("final_unit"))
        out.at[i, "final_value_source"] = _norm(r.get("final_value_source"))
        out.at[i, "final_review_status"] = _norm(r.get("final_review_status"))
        out.at[i, "reviewer"] = _norm(r.get("reviewer"))
        out.at[i, "reviewed_at"] = _norm(r.get("reviewed_at"))
        out.at[i, "reviewer_note"] = _norm(r.get("reviewer_note"))

    return out


def _compare_rebuilt_vs_current(rebuilt06: pd.DataFrame, current06: pd.DataFrame, override_df: pd.DataFrame) -> Tuple[Dict[str, Any], pd.DataFrame]:
    rebuilt_row_count = len(rebuilt06)
    current_row_count = len(current06)
    row_count_match = rebuilt_row_count == current_row_count

    rebuilt06["_key"] = rebuilt06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    current06["_key"] = current06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    rebuilt_keys = set(rebuilt06["_key"].tolist())
    current_keys = set(current06["_key"].tolist())
    key_set_match = rebuilt_keys == current_keys

    rebuilt_map = {r["_key"]: r for _, r in rebuilt06.iterrows()}
    current_map = {r["_key"]: r for _, r in current06.iterrows()}

    diff_rows: List[Dict[str, Any]] = []
    for k in sorted(rebuilt_keys | current_keys):
        rb = rebuilt_map.get(k)
        cu = current_map.get(k)
        if rb is None:
            diff_rows.append({"key": k, "diff_type": "missing_in_rebuilt", "rebuilt_value": "", "current_value": _norm(cu.get("final_value")), "rebuilt_unit": "", "current_unit": _norm(cu.get("final_unit")), "rebuilt_source": "", "current_source": _norm(cu.get("final_value_source"))})
            continue
        if cu is None:
            diff_rows.append({"key": k, "diff_type": "missing_in_current", "rebuilt_value": _norm(rb.get("final_value")), "current_value": "", "rebuilt_unit": _norm(rb.get("final_unit")), "current_unit": "", "rebuilt_source": _norm(rb.get("final_value_source")), "current_source": ""})
            continue

        rv, cv = _norm(rb.get("final_value")), _norm(cu.get("final_value"))
        ru, cuu = _norm(rb.get("final_unit")), _norm(cu.get("final_unit"))
        rs, cs = _norm(rb.get("final_value_source")), _norm(cu.get("final_value_source"))
        if rv != cv or ru != cuu or rs != cs:
            diff_rows.append({"key": k, "diff_type": "value_or_unit_or_source_mismatch", "rebuilt_value": rv, "current_value": cv, "rebuilt_unit": ru, "current_unit": cuu, "rebuilt_source": rs, "current_source": cs})

    value_set_match = len(diff_rows) == 0

    override_keys = set(override_df.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist())
    override_records_present_in_rebuilt_06 = override_keys.issubset(rebuilt_keys)

    return (
        {
            "rebuilt_row_count": rebuilt_row_count,
            "current_06_row_count": current_row_count,
            "row_count_match": row_count_match,
            "key_set_match": key_set_match,
            "value_set_match": value_set_match,
            "override_record_count": len(override_df),
            "override_records_present_in_rebuilt_06": override_records_present_in_rebuilt_06,
        },
        pd.DataFrame(diff_rows),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage2C dry-run rebuild 06 with 02B override (no production writes).")
    parser.parse_args()

    snap_before = _snapshot_prod()

    df01, df02, df02a, df02b, df06_current = _load_inputs()
    baseline = _build_baseline_from_01(df01)
    manual = _collect_manual_candidates(df02, df02a)
    override = _collect_override_candidates(df02b)

    rebuilt_core, conflict_df, dup_df = _merge_with_priority(baseline, manual, override)
    rebuilt06 = _align_rebuilt_schema(rebuilt_core, df06_current.copy())
    comp, diff_df = _compare_rebuilt_vs_current(rebuilt06.copy(), df06_current.copy(), override.copy())

    STAGE2C_OUT.mkdir(parents=True, exist_ok=True)
    rebuilt_path = STAGE2C_OUT / "06_最终核心财务指标.rebuilt_with_02B.xlsx"
    diff_xlsx = STAGE2C_OUT / "79_stage2c_rebuild_06_with_02B_diff.xlsx"
    diff_md = STAGE2C_OUT / "79_stage2c_rebuild_06_with_02B_diff.md"
    summary_json = STAGE2C_OUT / "80_stage2c_rebuild_06_with_02B_summary.json"

    _safe_write_excel(rebuilt06, rebuilt_path)
    _safe_write_excel_multi(
        {
            "diff_rows": diff_df if not diff_df.empty else pd.DataFrame(columns=["key", "diff_type"]),
            "conflicts": conflict_df if not conflict_df.empty else pd.DataFrame(columns=["key", "conflict_reason"]),
            "duplicate_keys": dup_df if not dup_df.empty else pd.DataFrame(columns=["_key"]),
            "summary": pd.DataFrame([comp]),
        },
        diff_xlsx,
    )

    conflict_count = len(conflict_df)
    duplicate_key_count = int(dup_df["_key"].nunique()) if not dup_df.empty else 0
    diff_md.write_text(
        "\n".join(
            [
                "# Stage2C Rebuild Dry-Run Diff",
                "",
                f"- rebuilt_row_count: {comp['rebuilt_row_count']}",
                f"- current_06_row_count: {comp['current_06_row_count']}",
                f"- row_count_match: {comp['row_count_match']}",
                f"- key_set_match: {comp['key_set_match']}",
                f"- value_set_match: {comp['value_set_match']}",
                f"- override_record_count: {comp['override_record_count']}",
                f"- override_records_present_in_rebuilt_06: {comp['override_records_present_in_rebuilt_06']}",
                f"- duplicate_key_count: {duplicate_key_count}",
                f"- conflict_count: {conflict_count}",
            ]
        ),
        encoding="utf-8",
    )

    snap_after = _snapshot_prod()
    production_files_unchanged = snap_before == snap_after
    output_06_unchanged = snap_before["06"] == snap_after["06"]
    delivery_status = _run_delivery_check()

    summary = {
        "rebuilt_row_count": comp["rebuilt_row_count"],
        "current_06_row_count": comp["current_06_row_count"],
        "row_count_match": bool(comp["row_count_match"]),
        "key_set_match": bool(comp["key_set_match"]),
        "value_set_match": bool(comp["value_set_match"]),
        "override_record_count": comp["override_record_count"],
        "override_records_present_in_rebuilt_06": bool(comp["override_records_present_in_rebuilt_06"]),
        "duplicate_key_count": int(duplicate_key_count),
        "conflict_count": int(conflict_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage2c_rebuild_dry_run_pass": bool(
            comp["override_record_count"] == 13
            and comp["override_records_present_in_rebuilt_06"]
            and duplicate_key_count == 0
            and conflict_count == 0
            and production_files_unchanged
            and output_06_unchanged
            and delivery_status.get("overall_status") == "PASS"
        ),
        "delivery_status_after": delivery_status.get("overall_status", "UNKNOWN"),
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"rebuilt_path: {rebuilt_path}")
    print(f"diff_xlsx: {diff_xlsx}")
    print(f"summary_json: {summary_json}")
    print(f"rebuilt_row_count: {summary['rebuilt_row_count']}")
    print(f"current_06_row_count: {summary['current_06_row_count']}")
    print(f"row_count_match: {summary['row_count_match']}")
    print(f"key_set_match: {summary['key_set_match']}")
    print(f"value_set_match: {summary['value_set_match']}")
    print(f"override_record_count: {summary['override_record_count']}")
    print(f"override_records_present_in_rebuilt_06: {summary['override_records_present_in_rebuilt_06']}")
    print(f"duplicate_key_count: {summary['duplicate_key_count']}")
    print(f"conflict_count: {summary['conflict_count']}")
    print(f"production_files_unchanged: {summary['production_files_unchanged']}")
    print(f"output_06_unchanged: {summary['output_06_unchanged']}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    print(f"stage2c_rebuild_dry_run_pass: {summary['stage2c_rebuild_dry_run_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
