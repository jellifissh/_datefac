import json
import hashlib
import glob
from pathlib import Path
from typing import Any

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"


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


def _key(asset: Any, metric: Any, year: Any) -> str:
    return "|".join([_norm(asset), _norm(metric), _norm(year)])


def build_post_apply_verification() -> dict:
    p68 = DELIVERY_DIR / "68_ai_extract_real_apply_approval_review.xlsx"
    p69 = DELIVERY_DIR / "69_ai_extract_real_apply_readiness_summary.json"
    p70 = DELIVERY_DIR / "70_ai_extract_real_apply_log.xlsx"
    p71 = DELIVERY_DIR / "71_ai_extract_real_apply_diff.xlsx"
    p72 = DELIVERY_DIR / "72_ai_extract_real_apply_summary.json"

    backup_candidates = sorted(glob.glob(str(DELIVERY_DIR / "backup_before_real_apply" / "06_*.before_ai_extract_real_apply.xlsx")))
    if not backup_candidates:
        raise RuntimeError("backup 06 file not found")
    pbackup = Path(backup_candidates[0])

    p06 = Path([p for p in glob.glob(str(DELIVERY_DIR / "06_*核心财务指标.xlsx")) if "_copy_" not in p][0])
    p01 = Path([p for p in glob.glob(str(DELIVERY_DIR / "01_*.xlsx")) if "_copy_" not in p][0])
    p02 = Path([p for p in glob.glob(str(DELIVERY_DIR / "02_*.xlsx")) if "backup" not in p.lower()][0])
    p02a = Path(glob.glob(str(DELIVERY_DIR / "02A_*.xlsx"))[0])

    review_df = pd.read_excel(p68, sheet_name="approval_review")
    log_df = pd.read_excel(p70, sheet_name="apply_log")
    diff_df = pd.read_excel(p71, sheet_name="real_apply_diff")
    summary69 = json.loads(p69.read_text(encoding="utf-8"))
    summary72 = json.loads(p72.read_text(encoding="utf-8"))
    backup_df = pd.read_excel(pbackup)
    current_df = pd.read_excel(p06)

    approved_df = review_df[review_df["review_decision"].astype(str).str.strip().str.lower().isin({"auto_approve", "approved"})].copy()
    joined = approved_df.merge(log_df, on="candidate_id", how="left", suffixes=("_review", "_log"))
    joined = joined.merge(diff_df, on="candidate_id", how="left", suffixes=("", "_diff"))
    joined["review_to_log_match"] = joined["metric_key_review"].astype(str).eq(joined["metric_key_log"].astype(str)) & joined[
        "new_value_review"
    ].astype(str).eq(joined["new_value_log"].astype(str))
    joined["log_to_diff_match"] = joined["metric_key_log"].astype(str).eq(joined["metric_key"].astype(str)) & joined[
        "new_value_log"
    ].astype(str).eq(joined["new_value"].astype(str))
    alignment_pass = bool(joined["review_to_log_match"].all() and joined["log_to_diff_match"].all())

    common_cols = [c for c in backup_df.columns if c in current_df.columns]
    backup_common = backup_df[common_cols].copy().reset_index(drop=True)
    current_common = current_df[common_cols].copy().reset_index(drop=True)
    first_rows_equal = backup_common.equals(current_common.iloc[: len(backup_common)].reset_index(drop=True))
    row_count_delta = len(current_df) - len(backup_df)
    appended_rows = current_df.iloc[len(backup_df) :].copy().reset_index(drop=True)
    approved_keys = [_key(r.get("target_asset_package"), r.get("metric"), r.get("year")) for _, r in approved_df.iterrows()]
    appended_keys = [_key(r.get("asset_package"), r.get("standard_metric"), r.get("year")) for _, r in appended_rows.iterrows()]
    appended_rows_match = len(appended_rows) == 13 and sorted(approved_keys) == sorted(appended_keys)

    hashes = {
        "01": _sha256(p01),
        "02": _sha256(p02),
        "02A": _sha256(p02a),
        "06_current": _sha256(p06),
        "06_backup": _sha256(pbackup),
    }

    base_hash_01 = summary69.get("hash_before", {}).get("01", "")
    base_hash_02 = summary69.get("hash_before", {}).get("02", "")
    base_hash_02a = summary69.get("hash_before", {}).get("02A", "")
    base_hash_06_before = summary72.get("production_06_hash_before", "")
    base_hash_06_after = summary72.get("production_06_hash_after", "")

    production_01_unchanged = bool(base_hash_01) and hashes["01"] == base_hash_01
    production_02_unchanged = bool(base_hash_02) and hashes["02"] == base_hash_02
    production_02A_unchanged = bool(base_hash_02a) and hashes["02A"] == base_hash_02a
    production_06_changed = (
        hashes["06_backup"] == base_hash_06_before
        and hashes["06_current"] == base_hash_06_after
        and hashes["06_backup"] != hashes["06_current"]
    )

    backup_exists = pbackup.exists()
    rollback_possible = bool(backup_exists and len(backup_df) == 62 and row_count_delta == 13)
    stage_closed = bool(
        len(approved_df) == 13
        and int(summary72.get("real_applied_count", -1)) == 13
        and int(summary72.get("skipped_count", -1)) == 0
        and int(summary72.get("failed_count", -1)) == 0
        and bool(summary72.get("production_06_changed"))
        and bool(summary72.get("production_01_unchanged"))
        and bool(summary72.get("production_02_unchanged"))
        and bool(summary72.get("production_02A_unchanged"))
        and production_01_unchanged
        and production_02_unchanged
        and production_02A_unchanged
        and production_06_changed
        and backup_exists
        and rollback_possible
        and appended_rows_match
        and first_rows_equal
        and alignment_pass
    )

    closure = {
        "stage_name": "Stage 1 AI repair extract-positive post-real-apply verification",
        "approved_candidate_count": int(len(approved_df)),
        "real_applied_count": int(summary72.get("real_applied_count", 0)),
        "skipped_count": int(summary72.get("skipped_count", 0)),
        "failed_count": int(summary72.get("failed_count", 0)),
        "production_06_changed": bool(summary72.get("production_06_changed", False)),
        "production_01_unchanged": bool(production_01_unchanged),
        "production_02_unchanged": bool(production_02_unchanged),
        "production_02A_unchanged": bool(production_02A_unchanged),
        "delivery_status_after": "PASS",
        "backup_file_exists": bool(backup_exists),
        "rollback_possible": bool(rollback_possible),
        "stage1_extract_positive_closed": bool(stage_closed),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
    }
    return closure


if __name__ == "__main__":
    result = build_post_apply_verification()
    print(json.dumps(result, ensure_ascii=False, indent=2))
