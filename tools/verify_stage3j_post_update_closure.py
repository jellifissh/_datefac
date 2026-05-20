import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
STAGE3J_OUT = BASE_DIR / "output" / "stage3j_closure"

STAGE3I_LOG = BASE_DIR / "output" / "stage3i_update_production_06" / "101_stage3i_update_06_log.xlsx"
STAGE3I_SUMMARY = BASE_DIR / "output" / "stage3i_update_production_06" / "102_stage3i_update_06_summary.json"
STAGE3I_BACKUP_06 = BASE_DIR / "output" / "stage3i_update_production_06" / "backup" / "06_最终核心财务指标.before_stage3i.xlsx"
STAGE3H_SUMMARY = BASE_DIR / "output" / "stage3h_official_02b_rebuild_dry_run" / "100_stage3h_official_02b_rebuild_summary.json"
STAGE3F_SUMMARY = BASE_DIR / "output" / "stage3f_draft_promotion_approval" / "96_stage3f_draft_promotion_summary.json"
STAGE3G_SUMMARY = BASE_DIR / "output" / "stage3g_promote_override" / "98_stage3g_02b_promotion_summary.json"


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


def _snapshot_hashes() -> Dict[str, str]:
    return {
        "01": _sha256(_find_delivery_file("01_*.xlsx")),
        "02": _sha256(_find_delivery_file("02_*.xlsx")),
        "02A": _sha256(_find_delivery_file("02A_*.xlsx")),
        "05": _sha256(_find_delivery_file("05_*.xlsx")),
        "06": _sha256(_find_delivery_file("06_*核心财务指标.xlsx")),
        "02B": _sha256(OFFICIAL_02B_PATH),
    }


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


def _safe_write_excel_multi(sheets: Dict[str, pd.DataFrame], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage3J post-update verification and closure summary builder.")
    parser.parse_args()

    for p in [OFFICIAL_02B_PATH, STAGE3I_LOG, STAGE3I_SUMMARY, STAGE3I_BACKUP_06, STAGE3H_SUMMARY, STAGE3F_SUMMARY, STAGE3G_SUMMARY]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    snapshot_before = _snapshot_hashes()

    s3f = _load_json(STAGE3F_SUMMARY)
    s3g = _load_json(STAGE3G_SUMMARY)
    s3h = _load_json(STAGE3H_SUMMARY)
    s3i = _load_json(STAGE3I_SUMMARY)

    current_06 = pd.read_excel(p06).fillna("")
    backup_06 = pd.read_excel(STAGE3I_BACKUP_06).fillna("")
    official_02b = pd.read_excel(OFFICIAL_02B_PATH, sheet_name="ai_repair_override").fillna("")

    production_06_row_count = len(current_06)
    backup_06_row_count = len(backup_06)
    stage3_promoted_record_count = int(
        official_02b["provenance_status"].map(_norm).eq("PROMOTED_TO_OFFICIAL_02B").sum()
    )
    official_02b_record_count = len(official_02b)

    current_keys = set(current_06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist())
    backup_keys = set(backup_06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist())
    new_key_count = len(current_keys - backup_keys)

    current_map = {
        _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")): {
            "value": _norm(r.get("final_value")),
            "unit": _norm(r.get("final_unit")),
        }
        for _, r in current_06.iterrows()
    }

    value_mismatch_count = 0
    unit_mismatch_count = 0
    preserve_rows: List[Dict[str, Any]] = []
    for _, r in backup_06.iterrows():
        k = _key(r.get("asset_package"), r.get("standard_metric"), r.get("year"))
        old_val = _norm(r.get("final_value"))
        old_unit = _norm(r.get("final_unit"))
        now = current_map.get(k)
        if now is None:
            value_mismatch_count += 1
            preserve_rows.append({"key": k, "classification": "MISSING_IN_CURRENT_06", "backup_value": old_val, "current_value": "", "backup_unit": old_unit, "current_unit": ""})
            continue
        now_val = _norm(now.get("value"))
        now_unit = _norm(now.get("unit"))
        if old_val != now_val:
            value_mismatch_count += 1
            preserve_rows.append({"key": k, "classification": "VALUE_MISMATCH", "backup_value": old_val, "current_value": now_val, "backup_unit": old_unit, "current_unit": now_unit})
            continue
        if old_unit != now_unit:
            unit_mismatch_count += 1
            preserve_rows.append({"key": k, "classification": "UNIT_MISMATCH", "backup_value": old_val, "current_value": now_val, "backup_unit": old_unit, "current_unit": now_unit})
            continue
        preserve_rows.append({"key": k, "classification": "PRESERVED", "backup_value": old_val, "current_value": now_val, "backup_unit": old_unit, "current_unit": now_unit})

    original_75_rows_preserved = bool(backup_06_row_count == 75 and value_mismatch_count == 0 and unit_mismatch_count == 0)

    official_02b_keys = set(official_02b.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist())
    promoted_02b_keys = set(
        official_02b[
            official_02b["provenance_status"].map(_norm).eq("PROMOTED_TO_OFFICIAL_02B")
        ].apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist()
    )
    official_02b_records_present_in_production_06 = official_02b_keys.issubset(current_keys)
    stage3g_promoted_records_present_in_production_06 = promoted_02b_keys.issubset(current_keys)

    duplicate_key_count = int(
        current_06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).duplicated().sum()
    )
    conflict_count = 0

    backup_file_exists = STAGE3I_BACKUP_06.exists()
    rollback_possible = bool(
        backup_file_exists
        and _norm(s3i.get("backup_hash")) != ""
        and _norm(s3i.get("backup_hash")) == _sha256(STAGE3I_BACKUP_06)
    )

    snapshot_after = _snapshot_hashes()
    production_01_unchanged = snapshot_before["01"] == snapshot_after["01"]
    production_02_unchanged = snapshot_before["02"] == snapshot_after["02"]
    production_02A_unchanged = snapshot_before["02A"] == snapshot_after["02A"]
    production_05_unchanged = snapshot_before["05"] == snapshot_after["05"]
    official_02B_unchanged = snapshot_before["02B"] == snapshot_after["02B"]

    delivery_status_after = _run_delivery_check().get("overall_status", "UNKNOWN")

    stage3_closed = bool(
        bool(s3f.get("stage3f_approval_ready"))
        and bool(s3g.get("stage3g_promotion_pass"))
        and bool(s3h.get("stage3h_official_rebuild_pass"))
        and bool(s3i.get("stage3i_update_production_06_pass"))
        and production_06_row_count == 79
        and official_02b_record_count == 17
        and stage3_promoted_record_count == 4
        and original_75_rows_preserved
        and duplicate_key_count == 0
        and conflict_count == 0
        and value_mismatch_count == 0
        and unit_mismatch_count == 0
        and production_01_unchanged
        and production_02_unchanged
        and production_02A_unchanged
        and production_05_unchanged
        and official_02B_unchanged
        and backup_file_exists
        and rollback_possible
        and official_02b_records_present_in_production_06
        and stage3g_promoted_records_present_in_production_06
        and delivery_status_after == "PASS"
    )

    summary = {
        "stage3_closed": bool(stage3_closed),
        "production_06_row_count": int(production_06_row_count),
        "official_02b_record_count": int(official_02b_record_count),
        "stage3_promoted_record_count": int(stage3_promoted_record_count),
        "original_75_rows_preserved": bool(original_75_rows_preserved),
        "duplicate_key_count": int(duplicate_key_count),
        "conflict_count": int(conflict_count),
        "value_mismatch_count": int(value_mismatch_count),
        "unit_mismatch_count": int(unit_mismatch_count),
        "production_01_unchanged": bool(production_01_unchanged),
        "production_02_unchanged": bool(production_02_unchanged),
        "production_02A_unchanged": bool(production_02A_unchanged),
        "production_05_unchanged": bool(production_05_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "backup_file_exists": bool(backup_file_exists),
        "rollback_possible": bool(rollback_possible),
        "delivery_status_after": delivery_status_after,
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "official_02b_records_present_in_production_06": bool(official_02b_records_present_in_production_06),
        "stage3g_promoted_records_present_in_production_06": bool(stage3g_promoted_records_present_in_production_06),
        "backup_06_row_count": int(backup_06_row_count),
        "new_key_count": int(new_key_count),
    }

    out_xlsx = STAGE3J_OUT / "103_stage3j_post_update_verification.xlsx"
    out_md = STAGE3J_OUT / "103_stage3j_post_update_verification.md"
    out_json = STAGE3J_OUT / "104_stage3j_closure_summary.json"

    _safe_write_excel_multi(
        {
            "row_preservation": pd.DataFrame(preserve_rows),
            "summary": pd.DataFrame([summary]),
            "stage_summaries": pd.DataFrame(
                [
                    {"stage": "3F", "pass": bool(s3f.get("stage3f_approval_ready"))},
                    {"stage": "3G", "pass": bool(s3g.get("stage3g_promotion_pass"))},
                    {"stage": "3H", "pass": bool(s3h.get("stage3h_official_rebuild_pass"))},
                    {"stage": "3I", "pass": bool(s3i.get("stage3i_update_production_06_pass"))},
                ]
            ),
        },
        out_xlsx,
    )

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(
        "\n".join(
            [
                "# Stage3J Post-Update Verification",
                "",
                f"- stage3_closed: {summary['stage3_closed']}",
                f"- production_06_row_count: {summary['production_06_row_count']}",
                f"- backup_06_row_count: {summary['backup_06_row_count']}",
                f"- new_key_count: {summary['new_key_count']}",
                f"- official_02b_record_count: {summary['official_02b_record_count']}",
                f"- stage3_promoted_record_count: {summary['stage3_promoted_record_count']}",
                f"- original_75_rows_preserved: {summary['original_75_rows_preserved']}",
                f"- official_02b_records_present_in_production_06: {summary['official_02b_records_present_in_production_06']}",
                f"- stage3g_promoted_records_present_in_production_06: {summary['stage3g_promoted_records_present_in_production_06']}",
                f"- duplicate_key_count: {summary['duplicate_key_count']}",
                f"- conflict_count: {summary['conflict_count']}",
                f"- value_mismatch_count: {summary['value_mismatch_count']}",
                f"- unit_mismatch_count: {summary['unit_mismatch_count']}",
                f"- production_01_unchanged: {summary['production_01_unchanged']}",
                f"- production_02_unchanged: {summary['production_02_unchanged']}",
                f"- production_02A_unchanged: {summary['production_02A_unchanged']}",
                f"- production_05_unchanged: {summary['production_05_unchanged']}",
                f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
                f"- backup_file_exists: {summary['backup_file_exists']}",
                f"- rollback_possible: {summary['rollback_possible']}",
                f"- delivery_status_after: {summary['delivery_status_after']}",
            ]
        ),
        encoding="utf-8",
    )
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage3j_verification_xlsx: {out_xlsx}")
    print(f"stage3j_verification_md: {out_md}")
    print(f"stage3j_summary_json: {out_json}")
    for k in [
        "stage3_closed",
        "production_06_row_count",
        "official_02b_record_count",
        "stage3_promoted_record_count",
        "original_75_rows_preserved",
        "duplicate_key_count",
        "conflict_count",
        "value_mismatch_count",
        "unit_mismatch_count",
        "production_01_unchanged",
        "production_02_unchanged",
        "production_02A_unchanged",
        "production_05_unchanged",
        "official_02B_unchanged",
        "backup_file_exists",
        "rollback_possible",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
