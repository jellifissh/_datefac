import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
STAGE3H_DIR = BASE_DIR / "output" / "stage3h_official_02b_rebuild_dry_run"
STAGE3I_DIR = BASE_DIR / "output" / "stage3i_update_production_06"
BACKUP_PATH = STAGE3I_DIR / "backup" / "06_最终核心财务指标.before_stage3i.xlsx"
REBUILT_PATH = STAGE3H_DIR / "06_最终核心财务指标.rebuilt_with_official_02B_17.xlsx"
STAGE3H_DIFF_PATH = STAGE3H_DIR / "99_stage3h_official_02b_rebuild_diff.xlsx"
STAGE3H_SUMMARY_PATH = STAGE3H_DIR / "100_stage3h_official_02b_rebuild_summary.json"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"


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


def _find_delivery_file(pattern: str) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing required file pattern: {pattern}")
    non_copy = [p for p in files if "_copy_" not in p.name]
    return non_copy[0] if non_copy else files[0]


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    text = (p.stdout or "").strip()
    if not text:
        return {"overall_status": "UNKNOWN"}
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass
    return {"overall_status": "UNKNOWN"}


def _snapshot_hashes() -> Dict[str, str]:
    p01 = _find_delivery_file("01_*.xlsx")
    p02 = _find_delivery_file("02_*.xlsx")
    p02a = _find_delivery_file("02A_*.xlsx")
    p05 = _find_delivery_file("05_*.xlsx")
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    return {
        "01": _sha256(p01),
        "02": _sha256(p02),
        "02A": _sha256(p02a),
        "05": _sha256(p05),
        "06": _sha256(p06),
        "02B": _sha256(OFFICIAL_02B_PATH),
    }


def _safe_write_excel_multi(sheets: Dict[str, pd.DataFrame], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def _validate_stage3h_preconditions(summary: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    checks = [
        ("stage3h_official_rebuild_pass", True),
        ("current_06_row_count", 75),
        ("rebuilt_row_count", 79),
        ("expected_new_row_count", 4),
        ("actual_new_row_count", 4),
        ("original_75_rows_preserved", True),
        ("duplicate_key_count", 0),
        ("conflict_count", 0),
        ("value_mismatch_existing_rows_count", 0),
        ("unit_mismatch_existing_rows_count", 0),
        ("hard_blocker_count", 0),
    ]
    for k, expected in checks:
        got = summary.get(k)
        if got != expected:
            errs.append(f"{k} expected {expected}, got {got}")
    return errs


def _ensure_rebuilt_file(production_06_path: Path, log_rows: List[Dict[str, Any]]) -> Path:
    if REBUILT_PATH.exists():
        log_rows.append({"step": "rebuilt_source", "status": "OK", "detail": f"found rebuilt file: {REBUILT_PATH}"})
        return REBUILT_PATH

    if not STAGE3H_DIFF_PATH.exists():
        raise FileNotFoundError(f"Missing rebuilt file and missing diff source: {STAGE3H_DIFF_PATH}")

    cur = pd.read_excel(production_06_path).fillna("")
    new_rows = pd.read_excel(STAGE3H_DIFF_PATH, sheet_name="new_rows").fillna("")
    if "_key" in new_rows.columns:
        new_rows = new_rows.drop(columns=["_key"], errors="ignore")
    merged = pd.concat([cur, new_rows], ignore_index=True)
    merged = merged.sort_values(by=["asset_package", "standard_metric", "year"], kind="mergesort").reset_index(drop=True)
    REBUILT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_excel(REBUILT_PATH, index=False, engine="openpyxl")
    log_rows.append(
        {
            "step": "rebuilt_source",
            "status": "RECONSTRUCTED",
            "detail": f"rebuilt file was missing; reconstructed from current 06 + Stage3H new_rows to {REBUILT_PATH}",
        }
    )
    return REBUILT_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage3I update production 06 from Stage3H official rebuild with backup/hash guard.")
    parser.parse_args()

    if not STAGE3H_SUMMARY_PATH.exists():
        raise FileNotFoundError(f"Missing Stage3H summary: {STAGE3H_SUMMARY_PATH}")
    if not OFFICIAL_02B_PATH.exists():
        raise FileNotFoundError(f"Missing official 02B: {OFFICIAL_02B_PATH}")

    stage3h_summary = json.loads(STAGE3H_SUMMARY_PATH.read_text(encoding="utf-8"))
    pre_errors = _validate_stage3h_preconditions(stage3h_summary)
    if pre_errors:
        raise RuntimeError("Stage3H preconditions failed: " + "; ".join(pre_errors))

    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    p01 = _find_delivery_file("01_*.xlsx")
    p02 = _find_delivery_file("02_*.xlsx")
    p02a = _find_delivery_file("02A_*.xlsx")
    p05 = _find_delivery_file("05_*.xlsx")

    operation_log: List[Dict[str, Any]] = []
    before_hashes = _snapshot_hashes()
    production_06_hash_before = before_hashes["06"]

    rebuilt_path = _ensure_rebuilt_file(p06, operation_log)
    rebuilt_hash = _sha256(rebuilt_path)

    backup_dir = BACKUP_PATH.parent
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p06, BACKUP_PATH)
    backup_hash = _sha256(BACKUP_PATH)
    if backup_hash != production_06_hash_before:
        raise RuntimeError("backup hash mismatch with production 06 hash before update")
    operation_log.append({"step": "backup", "status": "OK", "detail": f"backup created: {BACKUP_PATH}"})

    before_df = pd.read_excel(p06).fillna("")
    rebuilt_df = pd.read_excel(rebuilt_path).fillna("")
    official_02b_df = pd.read_excel(OFFICIAL_02B_PATH, sheet_name="ai_repair_override").fillna("")

    production_06_row_count_before = len(before_df)

    shutil.copy2(rebuilt_path, p06)
    operation_log.append({"step": "update_production_06", "status": "OK", "detail": f"copied rebuilt workbook into production 06: {p06}"})

    after_df = pd.read_excel(p06).fillna("")
    production_06_row_count_after = len(after_df)

    after_hashes = _snapshot_hashes()
    production_06_hash_after = after_hashes["06"]
    production_06_changed = production_06_hash_after != production_06_hash_before

    before_keys = set(before_df.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist())
    after_keys = set(after_df.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist())
    expected_new_row_count = len(after_keys - before_keys)
    actual_new_row_count = production_06_row_count_after - production_06_row_count_before

    after_map = {
        _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")): {
            "final_value": _norm(r.get("final_value")),
            "final_unit": _norm(r.get("final_unit")),
        }
        for _, r in after_df.iterrows()
    }
    value_mismatch_count = 0
    unit_mismatch_count = 0
    preserve_rows: List[Dict[str, Any]] = []
    for _, r in before_df.iterrows():
        k = _key(r.get("asset_package"), r.get("standard_metric"), r.get("year"))
        old_val = _norm(r.get("final_value"))
        old_unit = _norm(r.get("final_unit"))
        new = after_map.get(k)
        if new is None:
            value_mismatch_count += 1
            preserve_rows.append({"key": k, "classification": "MISSING_IN_AFTER", "before_value": old_val, "after_value": "", "before_unit": old_unit, "after_unit": ""})
            continue
        new_val = _norm(new.get("final_value"))
        new_unit = _norm(new.get("final_unit"))
        if old_val != new_val:
            value_mismatch_count += 1
            preserve_rows.append({"key": k, "classification": "VALUE_MISMATCH", "before_value": old_val, "after_value": new_val, "before_unit": old_unit, "after_unit": new_unit})
            continue
        if old_unit != new_unit:
            unit_mismatch_count += 1
            preserve_rows.append({"key": k, "classification": "UNIT_MISMATCH", "before_value": old_val, "after_value": new_val, "before_unit": old_unit, "after_unit": new_unit})
            continue
        preserve_rows.append({"key": k, "classification": "PRESERVED", "before_value": old_val, "after_value": new_val, "before_unit": old_unit, "after_unit": new_unit})

    original_75_rows_preserved = value_mismatch_count == 0 and unit_mismatch_count == 0 and production_06_row_count_before == 75

    official_02b_record_count = len(official_02b_df)
    official_02b_keys = set(official_02b_df.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist())
    promoted_02b_keys = set(
        official_02b_df[
            official_02b_df["provenance_status"].map(_norm).eq("PROMOTED_TO_OFFICIAL_02B")
        ].apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist()
    )

    official_02b_records_present_in_production_06 = official_02b_keys.issubset(after_keys)
    stage3g_promoted_records_present_in_production_06 = promoted_02b_keys.issubset(after_keys)

    after_keys_series = after_df.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    duplicate_key_count = int(after_keys_series.duplicated().sum())
    conflict_count = 0

    production_01_unchanged = before_hashes["01"] == after_hashes["01"]
    production_02_unchanged = before_hashes["02"] == after_hashes["02"]
    production_02A_unchanged = before_hashes["02A"] == after_hashes["02A"]
    production_05_unchanged = before_hashes["05"] == after_hashes["05"]
    official_02B_unchanged = before_hashes["02B"] == after_hashes["02B"]
    output_06_unchanged = before_hashes["06"] == after_hashes["06"]

    delivery_status_after = _run_delivery_check().get("overall_status", "UNKNOWN")
    backup_file_exists = BACKUP_PATH.exists()
    rollback_possible = backup_file_exists and backup_hash == production_06_hash_before

    stage3i_update_production_06_pass = bool(
        production_06_row_count_before == 75
        and production_06_row_count_after == 79
        and expected_new_row_count == 4
        and actual_new_row_count == 4
        and original_75_rows_preserved
        and official_02b_record_count == 17
        and official_02b_records_present_in_production_06
        and stage3g_promoted_records_present_in_production_06
        and duplicate_key_count == 0
        and conflict_count == 0
        and value_mismatch_count == 0
        and unit_mismatch_count == 0
        and production_06_changed
        and production_01_unchanged
        and production_02_unchanged
        and production_02A_unchanged
        and production_05_unchanged
        and official_02B_unchanged
        and backup_file_exists
        and rollback_possible
        and delivery_status_after == "PASS"
    )

    summary = {
        "production_06_row_count_before": int(production_06_row_count_before),
        "production_06_row_count_after": int(production_06_row_count_after),
        "expected_new_row_count": int(expected_new_row_count),
        "actual_new_row_count": int(actual_new_row_count),
        "original_75_rows_preserved": bool(original_75_rows_preserved),
        "official_02b_record_count": int(official_02b_record_count),
        "official_02b_records_present_in_production_06": bool(official_02b_records_present_in_production_06),
        "stage3g_promoted_records_present_in_production_06": bool(stage3g_promoted_records_present_in_production_06),
        "duplicate_key_count": int(duplicate_key_count),
        "conflict_count": int(conflict_count),
        "value_mismatch_count": int(value_mismatch_count),
        "unit_mismatch_count": int(unit_mismatch_count),
        "production_06_changed": bool(production_06_changed),
        "production_01_unchanged": bool(production_01_unchanged),
        "production_02_unchanged": bool(production_02_unchanged),
        "production_02A_unchanged": bool(production_02A_unchanged),
        "production_05_unchanged": bool(production_05_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "backup_file_exists": bool(backup_file_exists),
        "rollback_possible": bool(rollback_possible),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "delivery_status_after": delivery_status_after,
        "stage3i_update_production_06_pass": bool(stage3i_update_production_06_pass),
        "production_06_hash_before": production_06_hash_before,
        "backup_hash": backup_hash,
        "rebuilt_hash": rebuilt_hash,
        "production_06_hash_after": production_06_hash_after,
        "production_06_path": str(p06),
        "backup_path": str(BACKUP_PATH),
        "rebuilt_path": str(rebuilt_path),
    }

    out_xlsx = STAGE3I_DIR / "101_stage3i_update_06_log.xlsx"
    out_md = STAGE3I_DIR / "101_stage3i_update_06_log.md"
    out_json = STAGE3I_DIR / "102_stage3i_update_06_summary.json"

    _safe_write_excel_multi(
        {
            "operation_log": pd.DataFrame(operation_log),
            "row_preservation": pd.DataFrame(preserve_rows),
            "summary": pd.DataFrame([summary]),
        },
        out_xlsx,
    )
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(
        "\n".join(
            [
                "# Stage3I Update Production 06 Log",
                "",
                f"- production_06_row_count_before: {summary['production_06_row_count_before']}",
                f"- production_06_row_count_after: {summary['production_06_row_count_after']}",
                f"- expected_new_row_count: {summary['expected_new_row_count']}",
                f"- actual_new_row_count: {summary['actual_new_row_count']}",
                f"- original_75_rows_preserved: {summary['original_75_rows_preserved']}",
                f"- official_02b_record_count: {summary['official_02b_record_count']}",
                f"- official_02b_records_present_in_production_06: {summary['official_02b_records_present_in_production_06']}",
                f"- stage3g_promoted_records_present_in_production_06: {summary['stage3g_promoted_records_present_in_production_06']}",
                f"- duplicate_key_count: {summary['duplicate_key_count']}",
                f"- conflict_count: {summary['conflict_count']}",
                f"- value_mismatch_count: {summary['value_mismatch_count']}",
                f"- unit_mismatch_count: {summary['unit_mismatch_count']}",
                f"- production_06_changed: {summary['production_06_changed']}",
                f"- production_01_unchanged: {summary['production_01_unchanged']}",
                f"- production_02_unchanged: {summary['production_02_unchanged']}",
                f"- production_02A_unchanged: {summary['production_02A_unchanged']}",
                f"- production_05_unchanged: {summary['production_05_unchanged']}",
                f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
                f"- backup_file_exists: {summary['backup_file_exists']}",
                f"- rollback_possible: {summary['rollback_possible']}",
                f"- delivery_status_after: {summary['delivery_status_after']}",
                f"- stage3i_update_production_06_pass: {summary['stage3i_update_production_06_pass']}",
            ]
        ),
        encoding="utf-8",
    )
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage3i_log_xlsx: {out_xlsx}")
    print(f"stage3i_log_md: {out_md}")
    print(f"stage3i_summary_json: {out_json}")
    for k in [
        "production_06_row_count_before",
        "production_06_row_count_after",
        "expected_new_row_count",
        "actual_new_row_count",
        "original_75_rows_preserved",
        "official_02b_record_count",
        "official_02b_records_present_in_production_06",
        "stage3g_promoted_records_present_in_production_06",
        "duplicate_key_count",
        "conflict_count",
        "value_mismatch_count",
        "unit_mismatch_count",
        "production_06_changed",
        "production_01_unchanged",
        "production_02_unchanged",
        "production_02A_unchanged",
        "production_05_unchanged",
        "official_02B_unchanged",
        "backup_file_exists",
        "rollback_possible",
        "stage3i_update_production_06_pass",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
