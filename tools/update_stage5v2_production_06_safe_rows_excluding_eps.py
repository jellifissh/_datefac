import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

INPUT_STAGE5U_DIR = OUTPUT_DIR / "stage5u_06_conflict_review"
INPUT_SAFE_MANIFEST_XLSX = INPUT_STAGE5U_DIR / "166_stage5u_06_safe_update_manifest.xlsx"
INPUT_CONFLICT_REVIEW_XLSX = INPUT_STAGE5U_DIR / "166_stage5u_06_conflict_review.xlsx"
INPUT_STAGE5U_SUMMARY_JSON = INPUT_STAGE5U_DIR / "167_stage5u_06_conflict_review_summary.json"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"

OUT_DIR = OUTPUT_DIR / "stage5v2_update_06_safe_rows_excluding_eps"
OUT_BACKUP_DIR = OUT_DIR / "backup"
OUT_CORRECTED_MANIFEST_XLSX = OUT_DIR / "170_stage5v2_corrected_safe_manifest.xlsx"
OUT_LOG_XLSX = OUT_DIR / "170_stage5v2_update_06_log.xlsx"
OUT_DIFF_XLSX = OUT_DIR / "170_stage5v2_update_06_diff.xlsx"
OUT_REPORT_MD = OUT_DIR / "170_stage5v2_update_06_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "171_stage5v2_update_06_summary.json"

EPS_YEARS = {"2024A", "2025A", "2026E", "2027E", "2028E"}


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
        for s, df in sheets.items():
            df.to_excel(writer, sheet_name=s[:31], index=False)


def _find_delivery_file(pattern: str) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing delivery file pattern: {pattern}")
    non_copy = [p for p in files if "_copy_" not in p.name.lower()]
    return non_copy[0] if non_copy else files[0]


def _snapshot_hashes() -> Dict[str, str]:
    return {
        "01": _sha256(_find_delivery_file("01_*.xlsx")),
        "02": _sha256(_find_delivery_file("02_*.xlsx")),
        "02A": _sha256(_find_delivery_file("02A_*.xlsx")),
        "05": _sha256(_find_delivery_file("05_*.xlsx")),
        "06": _sha256(_find_delivery_file("06_*.xlsx")),
        "02B": _sha256(OFFICIAL_02B_PATH),
        "scope_rules": _sha256(FORMAL_SCOPE_RULES_JSON),
        "standardizer": _sha256(FORMAL_STANDARDIZER_FILE),
    }


def _run_delivery_check() -> str:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    proc = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return "FAIL"
    try:
        payload = json.loads((proc.stdout or "").strip() or "{}")
        return _norm(payload.get("overall_status")) or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def _build_key(asset_package: str, source_pdf: str, standard_metric: str, year: str) -> str:
    return f"{asset_package}||{source_pdf}||{standard_metric}||{year}"


def _prepare_06(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy().fillna("")
    for c in ["asset_package", "source_pdf", "standard_metric", "year", "final_value", "final_unit"]:
        if c not in work.columns:
            work[c] = ""
        work[c] = work[c].map(_norm)
    work["key"] = work.apply(
        lambda r: _build_key(
            _norm(r.get("asset_package", "")),
            _norm(r.get("source_pdf", "")),
            _norm(r.get("standard_metric", "")),
            _norm(r.get("year", "")),
        ),
        axis=1,
    )
    return work


def _prepare_safe_rows(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy().fillna("")
    needed = ["asset_package", "source_pdf", "standard_metric", "year", "recommended_action"]
    for c in needed:
        if c not in work.columns:
            work[c] = ""
        work[c] = work[c].map(_norm)
    if "key" not in work.columns:
        work["key"] = work.apply(
            lambda r: _build_key(
                _norm(r.get("asset_package", "")),
                _norm(r.get("source_pdf", "")),
                _norm(r.get("standard_metric", "")),
                _norm(r.get("year", "")),
            ),
            axis=1,
        )
    else:
        work["key"] = work["key"].map(_norm)
    return work


def _count_conflicts_06(df: pd.DataFrame) -> Tuple[int, int, int, int]:
    if df.empty:
        return 0, 0, 0, 0
    work = _prepare_06(df)
    duplicate_key_count = int(work["key"].duplicated().sum())
    value_conflict_count = 0
    unit_conflict_count = 0
    year_conflict_count = 0

    for _, grp in work.groupby("key"):
        if grp["final_value"].nunique() > 1:
            value_conflict_count += 1
        if grp["final_unit"].nunique() > 1:
            unit_conflict_count += 1
    for _, grp in work.groupby(["asset_package", "source_pdf", "standard_metric"]):
        years = [y for y in grp["year"].tolist() if y]
        if len(years) != len(set(years)):
            year_conflict_count += 1

    return duplicate_key_count, value_conflict_count, unit_conflict_count, year_conflict_count


def _rollback(prod06: Path, backup06: Path) -> None:
    shutil.copy2(backup06, prod06)


def main() -> int:
    required = [
        INPUT_SAFE_MANIFEST_XLSX,
        INPUT_CONFLICT_REVIEW_XLSX,
        INPUT_STAGE5U_SUMMARY_JSON,
        OFFICIAL_02B_PATH,
        FORMAL_SCOPE_RULES_JSON,
        FORMAL_STANDARDIZER_FILE,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    stage5u_summary = json.loads(INPUT_STAGE5U_SUMMARY_JSON.read_text(encoding="utf-8"))
    if not bool(stage5u_summary.get("stage5u_06_conflict_review_pass")):
        raise RuntimeError("Precondition failed: Stage5U summary pass is not true.")

    production_06_file = _find_delivery_file("06_*.xlsx")
    if not production_06_file.exists():
        raise FileNotFoundError(f"Production 06 not found: {production_06_file}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    before_snapshot = _snapshot_hashes()
    production_06_hash_before = _sha256(production_06_file)

    backup_06_file = OUT_BACKUP_DIR / "06_before_stage5v2.xlsx"
    shutil.copy2(production_06_file, backup_06_file)
    production_06_backup_hash = _sha256(backup_06_file)

    safe_input_raw = pd.read_excel(INPUT_SAFE_MANIFEST_XLSX, sheet_name="safe_to_add_06_rows").fillna("")
    blocked_input_raw = pd.read_excel(INPUT_SAFE_MANIFEST_XLSX, sheet_name="blocked_conflict_rows").fillna("")
    conflict_review_df = pd.read_excel(INPUT_CONFLICT_REVIEW_XLSX, sheet_name="conflict_review").fillna("")

    safe_input = _prepare_safe_rows(safe_input_raw)
    blocked_input_raw["key"] = blocked_input_raw.get("key", "").map(_norm)
    blocked_keys: Set[str] = set(blocked_input_raw["key"].tolist())

    input_safe_to_add_06_row_count = int(len(safe_input))
    input_blocked_conflict_count = int(len(blocked_keys))

    safe_blocked_overlap_mask = safe_input["key"].isin(blocked_keys)
    safe_blocked_overlap_count = int(safe_blocked_overlap_mask.sum())
    overlap_df = safe_input[safe_blocked_overlap_mask].copy()

    eps_conflict_mask = (
        (safe_input["standard_metric"].map(_norm) == "每股收益")
        & (safe_input["year"].map(_norm).isin(EPS_YEARS))
        & (safe_input["key"].isin(blocked_keys))
    )
    eps_conflict_excluded_count = int(eps_conflict_mask.sum())

    # Corrected safe manifest: remove any blocked overlap and EPS conflict records.
    corrected_safe = safe_input[~safe_blocked_overlap_mask & ~eps_conflict_mask].copy()
    corrected_safe_manifest_row_count = int(len(corrected_safe))

    # Pre-apply hard guards from Stage5V2 doc
    if input_safe_to_add_06_row_count != 40:
        _rollback(production_06_file, backup_06_file)
        raise RuntimeError(f"Expected 40 input safe rows, got {input_safe_to_add_06_row_count}.")
    if input_blocked_conflict_count != 5:
        _rollback(production_06_file, backup_06_file)
        raise RuntimeError(f"Expected 5 blocked rows, got {input_blocked_conflict_count}.")
    if safe_blocked_overlap_count != 5:
        _rollback(production_06_file, backup_06_file)
        raise RuntimeError(f"Expected overlap 5, got {safe_blocked_overlap_count}.")
    if eps_conflict_excluded_count != 5:
        _rollback(production_06_file, backup_06_file)
        raise RuntimeError(f"Expected EPS excluded 5, got {eps_conflict_excluded_count}.")
    if corrected_safe_manifest_row_count != 35:
        _rollback(production_06_file, backup_06_file)
        raise RuntimeError(f"Expected corrected safe 35 rows, got {corrected_safe_manifest_row_count}.")
    if not corrected_safe[corrected_safe["recommended_action"].map(_norm) == "SAFE_TO_ADD_TO_06"].shape[0] == corrected_safe_manifest_row_count:
        _rollback(production_06_file, backup_06_file)
        raise RuntimeError("Corrected safe manifest has non-safe action rows.")

    # Confirm corrected safe has no blocked/EPS conflict row.
    if corrected_safe["key"].isin(blocked_keys).any():
        _rollback(production_06_file, backup_06_file)
        raise RuntimeError("Corrected safe manifest still contains blocked keys.")
    if (
        (corrected_safe["standard_metric"].map(_norm) == "每股收益")
        & (corrected_safe["year"].map(_norm).isin(EPS_YEARS))
    ).any():
        _rollback(production_06_file, backup_06_file)
        raise RuntimeError("Corrected safe manifest still contains EPS conflict rows.")

    _write_excel(
        OUT_CORRECTED_MANIFEST_XLSX,
        {
            "corrected_safe_to_add_06": corrected_safe,
            "excluded_overlap_eps_rows": overlap_df,
            "blocked_conflict_rows": blocked_input_raw,
            "conflict_review": conflict_review_df,
        },
    )

    current_06 = pd.read_excel(production_06_file).fillna("")
    current_06_work = _prepare_06(current_06)
    existing_keys = set(current_06_work["key"].tolist())
    production_06_row_count_before = int(len(current_06))

    rows_to_append: List[Dict[str, Any]] = []
    skipped_existing_06_row_count = 0
    for _, row in corrected_safe.iterrows():
        key = _norm(row.get("key", ""))
        if key in existing_keys:
            skipped_existing_06_row_count += 1
            continue

        rec = {c: "" for c in current_06.columns}
        for c in current_06.columns:
            if c in corrected_safe.columns:
                rec[c] = row.get(c, "")
        rec["final_value_source"] = _norm(rec.get("final_value_source", "")) or "STAGE5V2_SAFE_APPLY_FROM_05"
        rec["final_review_status"] = _norm(rec.get("final_review_status", "")) or "SAFE_ADDED_EXCLUDING_EPS_CONFLICT"
        rows_to_append.append(rec)
        existing_keys.add(key)

    applied_to_06_row_count = int(len(rows_to_append))

    updated_06 = current_06.copy()
    if rows_to_append:
        updated_06 = pd.concat([updated_06, pd.DataFrame(rows_to_append)], ignore_index=True)
    production_06_row_count_after = int(len(updated_06))
    expected_06_row_count_after = int(production_06_row_count_before + applied_to_06_row_count)

    updated_06.to_excel(production_06_file, index=False)

    production_06_hash_after = _sha256(production_06_file)
    production_06_changed = bool(production_06_hash_after != production_06_hash_before)

    post_06_df = pd.read_excel(production_06_file).fillna("")
    duplicate_key_count_06, value_conflict_count_06, unit_conflict_count_06, year_conflict_count_06 = _count_conflicts_06(post_06_df)

    appended_df = pd.DataFrame(rows_to_append) if rows_to_append else pd.DataFrame(columns=current_06.columns)
    appended_work = _prepare_06(appended_df) if not appended_df.empty else appended_df

    blocked_conflict_written_count = int(appended_work["key"].isin(blocked_keys).sum()) if not appended_df.empty else 0
    eps_unit_conflict_written_count = int(
        (
            (appended_df.get("standard_metric", "").map(_norm) == "每股收益")
            & (appended_df.get("year", "").map(_norm).isin(EPS_YEARS))
        ).sum()
    ) if not appended_df.empty else 0

    after_snapshot = _snapshot_hashes()
    production_01_unchanged = bool(before_snapshot["01"] == after_snapshot["01"])
    production_02_unchanged = bool(before_snapshot["02"] == after_snapshot["02"])
    production_02A_unchanged = bool(before_snapshot["02A"] == after_snapshot["02A"])
    production_05_unchanged = bool(before_snapshot["05"] == after_snapshot["05"])
    official_02B_unchanged = bool(before_snapshot["02B"] == after_snapshot["02B"])
    formal_rules_unchanged = bool(
        before_snapshot["scope_rules"] == after_snapshot["scope_rules"]
        and before_snapshot["standardizer"] == after_snapshot["standardizer"]
    )

    must_rollback = bool(
        (not production_06_changed)
        or (production_06_row_count_before != 79)
        or (applied_to_06_row_count != 35)
        or (production_06_row_count_after != 114)
        or (production_06_row_count_after != expected_06_row_count_after)
        or (duplicate_key_count_06 != 0)
        or (value_conflict_count_06 != 0)
        or (unit_conflict_count_06 != 0)
        or (year_conflict_count_06 != 0)
        or (blocked_conflict_written_count != 0)
        or (eps_unit_conflict_written_count != 0)
        or (not production_01_unchanged)
        or (not production_02_unchanged)
        or (not production_02A_unchanged)
        or (not production_05_unchanged)
        or (not official_02B_unchanged)
        or (not formal_rules_unchanged)
    )
    if must_rollback:
        _rollback(production_06_file, backup_06_file)
        production_06_hash_after = _sha256(production_06_file)
        production_06_changed = bool(production_06_hash_after != production_06_hash_before)
        raise RuntimeError("Post-write guard failed. Rolled back production 06.")

    check_delivery_state_after = _run_delivery_check()
    rollback_possible = bool(backup_06_file.exists())

    summary = {
        "production_06_file": str(production_06_file),
        "production_06_hash_before": production_06_hash_before,
        "production_06_backup_file": str(backup_06_file),
        "production_06_backup_hash": production_06_backup_hash,
        "production_06_hash_after": production_06_hash_after,
        "input_safe_to_add_06_row_count": input_safe_to_add_06_row_count,
        "input_blocked_conflict_count": input_blocked_conflict_count,
        "safe_blocked_overlap_count": safe_blocked_overlap_count,
        "eps_conflict_excluded_count": eps_conflict_excluded_count,
        "corrected_safe_manifest_row_count": corrected_safe_manifest_row_count,
        "applied_to_06_row_count": applied_to_06_row_count,
        "skipped_existing_06_row_count": skipped_existing_06_row_count,
        "blocked_conflict_written_count": blocked_conflict_written_count,
        "eps_unit_conflict_written_count": eps_unit_conflict_written_count,
        "production_06_row_count_before": production_06_row_count_before,
        "production_06_row_count_after": production_06_row_count_after,
        "expected_06_row_count_after": expected_06_row_count_after,
        "duplicate_key_count_06": duplicate_key_count_06,
        "value_conflict_count_06": value_conflict_count_06,
        "unit_conflict_count_06": unit_conflict_count_06,
        "year_conflict_count_06": year_conflict_count_06,
        "production_06_changed": production_06_changed,
        "production_01_unchanged": production_01_unchanged,
        "production_02_unchanged": production_02_unchanged,
        "production_02A_unchanged": production_02A_unchanged,
        "production_05_unchanged": production_05_unchanged,
        "official_02B_unchanged": official_02B_unchanged,
        "formal_rules_unchanged": formal_rules_unchanged,
        "rollback_possible": rollback_possible,
        "check_delivery_state_after": check_delivery_state_after,
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage5v2_update_06_safe_rows_pass": False,
    }

    summary["stage5v2_update_06_safe_rows_pass"] = bool(
        summary["input_safe_to_add_06_row_count"] == 40
        and summary["input_blocked_conflict_count"] == 5
        and summary["safe_blocked_overlap_count"] == 5
        and summary["eps_conflict_excluded_count"] == 5
        and summary["corrected_safe_manifest_row_count"] == 35
        and summary["applied_to_06_row_count"] == 35
        and summary["blocked_conflict_written_count"] == 0
        and summary["eps_unit_conflict_written_count"] == 0
        and summary["production_06_row_count_before"] == 79
        and summary["production_06_row_count_after"] == 114
        and summary["duplicate_key_count_06"] == 0
        and summary["value_conflict_count_06"] == 0
        and summary["unit_conflict_count_06"] == 0
        and summary["year_conflict_count_06"] == 0
        and summary["production_06_changed"]
        and summary["production_01_unchanged"]
        and summary["production_02_unchanged"]
        and summary["production_02A_unchanged"]
        and summary["production_05_unchanged"]
        and summary["official_02B_unchanged"]
        and summary["formal_rules_unchanged"]
        and summary["rollback_possible"]
        and summary["check_delivery_state_after"] == "PASS"
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    _write_excel(
        OUT_LOG_XLSX,
        {
            "summary": pd.DataFrame([{"metric": k, "value": v} for k, v in summary.items()]),
            "safe_input_40": safe_input,
            "blocked_input_5": blocked_input_raw,
            "corrected_safe_35": corrected_safe,
            "excluded_overlap_eps_5": overlap_df,
        },
    )
    _write_excel(
        OUT_DIFF_XLSX,
        {
            "production_06_before": current_06,
            "appended_35_rows": appended_df,
            "production_06_after": post_06_df,
        },
    )

    md_lines = [
        "# Stage5V2 Update 06 Report",
        "",
        "## Corrected Safe Manifest",
        f"- input_safe_to_add_06_row_count: {summary['input_safe_to_add_06_row_count']}",
        f"- input_blocked_conflict_count: {summary['input_blocked_conflict_count']}",
        f"- safe_blocked_overlap_count: {summary['safe_blocked_overlap_count']}",
        f"- eps_conflict_excluded_count: {summary['eps_conflict_excluded_count']}",
        f"- corrected_safe_manifest_row_count: {summary['corrected_safe_manifest_row_count']}",
        "",
        "## Apply Result",
        f"- applied_to_06_row_count: {summary['applied_to_06_row_count']}",
        f"- skipped_existing_06_row_count: {summary['skipped_existing_06_row_count']}",
        f"- production_06_row_count_before: {summary['production_06_row_count_before']}",
        f"- production_06_row_count_after: {summary['production_06_row_count_after']}",
        "",
        "## Conflict Guard",
        f"- blocked_conflict_written_count: {summary['blocked_conflict_written_count']}",
        f"- eps_unit_conflict_written_count: {summary['eps_unit_conflict_written_count']}",
        f"- duplicate_key_count_06: {summary['duplicate_key_count_06']}",
        f"- value_conflict_count_06: {summary['value_conflict_count_06']}",
        f"- unit_conflict_count_06: {summary['unit_conflict_count_06']}",
        f"- year_conflict_count_06: {summary['year_conflict_count_06']}",
        "",
        "## Guard",
        f"- production_01_unchanged: {summary['production_01_unchanged']}",
        f"- production_02_unchanged: {summary['production_02_unchanged']}",
        f"- production_02A_unchanged: {summary['production_02A_unchanged']}",
        f"- production_05_unchanged: {summary['production_05_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_rules_unchanged: {summary['formal_rules_unchanged']}",
        f"- check_delivery_state_after: {summary['check_delivery_state_after']}",
        f"- stage5v2_update_06_safe_rows_pass: {summary['stage5v2_update_06_safe_rows_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"corrected_manifest_xlsx: {OUT_CORRECTED_MANIFEST_XLSX}")
    print(f"update_log_xlsx: {OUT_LOG_XLSX}")
    print(f"update_diff_xlsx: {OUT_DIFF_XLSX}")
    print(f"update_report_md: {OUT_REPORT_MD}")
    print(f"summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5v2_update_06_safe_rows_pass: {summary['stage5v2_update_06_safe_rows_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
