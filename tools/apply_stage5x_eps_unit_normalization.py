import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

INPUT_STAGE5W_DIR = OUTPUT_DIR / "stage5w_eps_unit_conflict_review"
INPUT_STAGE5W_SUMMARY_JSON = INPUT_STAGE5W_DIR / "173_stage5w_eps_unit_conflict_summary.json"
INPUT_STAGE5W_REVIEW_XLSX = INPUT_STAGE5W_DIR / "172_stage5w_eps_conflict_review.xlsx"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"

OUT_DIR = OUTPUT_DIR / "stage5x_eps_unit_apply"
OUT_BACKUP_DIR = OUT_DIR / "backup"
OUT_AUDIT_XLSX = OUT_DIR / "174_stage5x_eps_unit_apply_audit.xlsx"
OUT_SUMMARY_JSON = OUT_DIR / "174_stage5x_eps_unit_apply_summary.json"
OUT_REPORT_MD = OUT_DIR / "174_stage5x_eps_unit_apply_report.md"

EPS_METRIC = "\u6bcf\u80a1\u6536\u76ca"
RECOMMENDED_UNIT = "\u5143/\u80a1"
BASED_ON_STAGE5W_COMMIT = "dd533f9e2e3eb6e5e3385de0701574a71a13ea10"
TARGET_METRIC_SCOPE = ["EPS", EPS_METRIC]


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


def _find_delivery_file(pattern: str) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing delivery file: {pattern}")
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


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for s, df in sheets.items():
            df.to_excel(writer, sheet_name=s[:31], index=False)


def _build_key(asset_package: str, source_pdf: str, standard_metric: str, year: str) -> str:
    return f"{asset_package}||{source_pdf}||{standard_metric}||{year}"


def _parse_key(key: str) -> Tuple[str, str, str, str]:
    parts = key.split("||")
    if len(parts) != 4:
        return "", "", "", ""
    return parts[0], parts[1], parts[2], parts[3]


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


def _count_conflicts_06(df: pd.DataFrame) -> Tuple[int, int, int, int]:
    if df.empty:
        return 0, 0, 0, 0
    work = _prepare_06(df)
    duplicate_key_count = int(work["key"].duplicated().sum())
    value_mismatch_count = 0
    unit_conflict_count = 0
    year_conflict_count = 0

    for _, grp in work.groupby("key"):
        if grp["final_value"].nunique() > 1:
            value_mismatch_count += 1
        if grp["final_unit"].nunique() > 1:
            unit_conflict_count += 1
    for _, grp in work.groupby(["asset_package", "source_pdf", "standard_metric"]):
        years = [y for y in grp["year"].tolist() if y]
        if len(years) != len(set(years)):
            year_conflict_count += 1
    return duplicate_key_count, value_mismatch_count, unit_conflict_count, year_conflict_count


def _rollback(prod06: Path, backup06: Path) -> None:
    shutil.copy2(backup06, prod06)


def main() -> int:
    required = [
        INPUT_STAGE5W_SUMMARY_JSON,
        INPUT_STAGE5W_REVIEW_XLSX,
        OFFICIAL_02B_PATH,
        FORMAL_SCOPE_RULES_JSON,
        FORMAL_STANDARDIZER_FILE,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    production_06_file = _find_delivery_file("06_*.xlsx")
    if not production_06_file.exists():
        raise FileNotFoundError("Production 06 file not found.")

    # Pre-check
    stage5w_summary = json.loads(INPUT_STAGE5W_SUMMARY_JSON.read_text(encoding="utf-8"))
    if int(stage5w_summary.get("eps_conflict_count", -1)) != 5:
        raise RuntimeError("Precondition failed: eps_conflict_count != 5")
    if int(stage5w_summary.get("eps_value_same_count", -1)) != 5:
        raise RuntimeError("Precondition failed: eps_value_same_count != 5")
    if int(stage5w_summary.get("eps_value_mismatch_count", -1)) != 0:
        raise RuntimeError("Precondition failed: eps_value_mismatch_count != 0")
    if not bool(stage5w_summary.get("ready_for_stage5x_eps_apply")):
        raise RuntimeError("Precondition failed: ready_for_stage5x_eps_apply is not true")

    before_snapshot = _snapshot_hashes()
    production_06_hash_before = _sha256(production_06_file)

    backup_06_file = OUT_BACKUP_DIR / "06_before_stage5x.xlsx"
    shutil.copy2(production_06_file, backup_06_file)
    production_06_backup_hash = _sha256(backup_06_file)

    eps_review = pd.read_excel(INPUT_STAGE5W_REVIEW_XLSX, sheet_name="eps_conflict_review").fillna("")
    eps_review["key"] = eps_review.get("key", "").map(_norm)
    eps_review["year"] = eps_review.get("year", "").map(_norm)
    eps_review["candidate_value"] = eps_review.get("candidate_value", "").map(_norm)
    eps_review["value_same"] = eps_review.get("value_same", False).astype(bool)

    if len(eps_review) != 5:
        _rollback(production_06_file, backup_06_file)
        raise RuntimeError(f"Precondition failed: eps review rows is {len(eps_review)}, expected 5.")

    current_06 = pd.read_excel(production_06_file).fillna("")
    current_06_work = _prepare_06(current_06)
    production_06_row_count_before = int(len(current_06))
    if production_06_row_count_before != 114:
        _rollback(production_06_file, backup_06_file)
        raise RuntimeError(f"Precondition failed: production 06 rows is {production_06_row_count_before}, expected 114.")

    updated_existing_count = 0
    inserted_new_count = 0
    skipped_count = 0
    blocker_count = 0
    eps_rows: List[Dict[str, Any]] = []
    blocker_messages: List[str] = []

    df = current_06.copy()
    df_work = current_06_work.copy()

    for _, r in eps_review.sort_values("year").iterrows():
        key = _norm(r.get("key", ""))
        metric_name = EPS_METRIC
        year = _norm(r.get("year", ""))
        candidate_value = _norm(r.get("candidate_value", ""))
        value_same = bool(r.get("value_same", False))

        if not value_same:
            blocker_count += 1
            blocker_messages.append(f"value_same=false for {key}")
            eps_rows.append(
                {
                    "metric_name": metric_name,
                    "year": year,
                    "value": candidate_value,
                    "unit_before": "",
                    "unit_after": RECOMMENDED_UNIT,
                    "action": "BLOCKED",
                    "value_same": value_same,
                    "source_evidence": [_norm(r.get("evidence", ""))],
                    "status": "VALUE_MISMATCH_BLOCKED",
                }
            )
            continue

        asset_package, source_pdf, standard_metric, parsed_year = _parse_key(key)
        if parsed_year != year:
            blocker_count += 1
            blocker_messages.append(f"year label mismatch in key: {key}")
            continue

        hit_idx = df_work.index[df_work["key"] == key].tolist()
        if len(hit_idx) > 1:
            blocker_count += 1
            blocker_messages.append(f"duplicate existing key in production 06: {key}")
            continue

        if len(hit_idx) == 1:
            i = hit_idx[0]
            cur_val = _norm(df_work.at[i, "final_value"])
            cur_unit = _norm(df_work.at[i, "final_unit"])
            if cur_val != candidate_value:
                blocker_count += 1
                blocker_messages.append(f"value mismatch for existing key {key}: {cur_val} vs {candidate_value}")
                eps_rows.append(
                    {
                        "metric_name": metric_name,
                        "year": year,
                        "value": candidate_value,
                        "unit_before": cur_unit,
                        "unit_after": RECOMMENDED_UNIT,
                        "action": "BLOCKED",
                        "value_same": value_same,
                        "source_evidence": [_norm(r.get("evidence", ""))],
                        "status": "EXISTING_VALUE_MISMATCH",
                    }
                )
                continue

            # unit normalization update only
            df.at[i, "final_unit"] = RECOMMENDED_UNIT
            df.at[i, "final_value_source"] = "STAGE5X_EPS_UNIT_NORMALIZED"
            df.at[i, "final_review_status"] = "EPS_UNIT_NORMALIZED"
            updated_existing_count += 1
            eps_rows.append(
                {
                    "metric_name": metric_name,
                    "year": year,
                    "value": candidate_value,
                    "unit_before": cur_unit,
                    "unit_after": RECOMMENDED_UNIT,
                    "action": "UPDATE_UNIT",
                    "value_same": value_same,
                    "source_evidence": [_norm(r.get("evidence", ""))],
                    "status": "APPLIED",
                }
            )
            df_work.at[i, "final_unit"] = RECOMMENDED_UNIT
            continue

        # not exists -> insert
        new_row = {c: "" for c in df.columns}
        for c, v in [
            ("source_pdf", source_pdf),
            ("asset_package", asset_package),
            ("standard_metric", standard_metric),
            ("year", year),
            ("final_value", candidate_value),
            ("final_unit", RECOMMENDED_UNIT),
            ("final_value_source", "STAGE5X_EPS_UNIT_NORMALIZED"),
            ("final_review_status", "EPS_UNIT_NORMALIZED"),
            ("trace_note", "stage5x_eps_unit_apply_insert"),
        ]:
            if c in new_row:
                new_row[c] = v
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        inserted_new_count += 1
        eps_rows.append(
            {
                "metric_name": metric_name,
                "year": year,
                "value": candidate_value,
                "unit_before": "",
                "unit_after": RECOMMENDED_UNIT,
                "action": "INSERT_NEW",
                "value_same": value_same,
                "source_evidence": [_norm(r.get("evidence", ""))],
                "status": "APPLIED",
            }
        )
        # refresh work for next iterations
        df_work = _prepare_06(df)

    applied_count = int(updated_existing_count + inserted_new_count)
    if blocker_count > 0:
        _rollback(production_06_file, backup_06_file)
        raise RuntimeError("Blockers found during Stage5X apply: " + "; ".join(blocker_messages))

    # Write 06
    df.to_excel(production_06_file, index=False)
    post_df = pd.read_excel(production_06_file).fillna("")
    production_06_row_count_after = int(len(post_df))
    production_06_hash_after = _sha256(production_06_file)
    production_06_modified = bool(production_06_hash_before != production_06_hash_after)

    duplicate_key_count, value_mismatch_count, unit_conflict_count, year_conflict_count = _count_conflicts_06(post_df)

    post_work = _prepare_06(post_df)
    target_keys = set(eps_review["key"].map(_norm).tolist())
    eps_scope = post_work[post_work["key"].map(_norm).isin(target_keys)].copy()
    eps_unit_conflict_remaining_count = int(
        eps_scope["final_unit"].map(_norm).isin({"ratio", "", "元"}).sum()
    )

    after_snapshot = _snapshot_hashes()
    production_01_unchanged = bool(before_snapshot["01"] == after_snapshot["01"])
    production_02_unchanged = bool(before_snapshot["02"] == after_snapshot["02"])
    production_02a_unchanged = bool(before_snapshot["02A"] == after_snapshot["02A"])
    production_05_unchanged = bool(before_snapshot["05"] == after_snapshot["05"])
    official_02b_modified = bool(before_snapshot["02B"] != after_snapshot["02B"])
    formal_rules_modified = bool(
        before_snapshot["scope_rules"] != after_snapshot["scope_rules"]
        or before_snapshot["standardizer"] != after_snapshot["standardizer"]
    )

    fail_reasons: List[str] = []
    if not production_06_modified:
        fail_reasons.append("production_06_modified=false")
    if applied_count != 5:
        fail_reasons.append(f"applied_count={applied_count}")
    if duplicate_key_count != 0:
        fail_reasons.append(f"duplicate_key_count={duplicate_key_count}")
    if value_mismatch_count != 0:
        fail_reasons.append(f"value_mismatch_count={value_mismatch_count}")
    if unit_conflict_count != 0:
        fail_reasons.append(f"unit_conflict_count={unit_conflict_count}")
    if year_conflict_count != 0:
        fail_reasons.append(f"year_conflict_count={year_conflict_count}")
    if eps_unit_conflict_remaining_count != 0:
        fail_reasons.append(f"eps_unit_conflict_remaining_count={eps_unit_conflict_remaining_count}")
    if not production_01_unchanged:
        fail_reasons.append("production_01_unchanged=false")
    if not production_02_unchanged:
        fail_reasons.append("production_02_unchanged=false")
    if not production_02a_unchanged:
        fail_reasons.append("production_02a_unchanged=false")
    if not production_05_unchanged:
        fail_reasons.append("production_05_unchanged=false")
    if official_02b_modified:
        fail_reasons.append("official_02b_modified=true")
    if formal_rules_modified:
        fail_reasons.append("formal_rules_modified=true")

    must_rollback = len(fail_reasons) > 0
    if must_rollback:
        _rollback(production_06_file, backup_06_file)
        raise RuntimeError("Post-apply guard failed in Stage5X; rollback completed. " + "; ".join(fail_reasons))

    check_delivery_state_overall_status = _run_delivery_check()
    rollback_possible = bool(backup_06_file.exists())

    summary = {
        "stage": "stage5x_eps_unit_apply",
        "mode": "real_apply_limited_scope",
        "based_on_stage5w_commit": BASED_ON_STAGE5W_COMMIT,
        "stage5w_summary_file": str(INPUT_STAGE5W_SUMMARY_JSON),
        "target_metric_scope": TARGET_METRIC_SCOPE,
        "target_conflict_count": 5,
        "applied_count": applied_count,
        "updated_existing_count": updated_existing_count,
        "inserted_new_count": inserted_new_count,
        "skipped_count": skipped_count,
        "blocker_count": blocker_count,
        "recommended_unit": RECOMMENDED_UNIT,
        "formal_rules_modified": formal_rules_modified,
        "official_02b_modified": official_02b_modified,
        "production_01_unchanged": production_01_unchanged,
        "production_02_unchanged": production_02_unchanged,
        "production_02a_unchanged": production_02a_unchanged,
        "production_05_unchanged": production_05_unchanged,
        "production_06_modified": production_06_modified,
        "production_06_row_count_before": production_06_row_count_before,
        "production_06_row_count_after": production_06_row_count_after,
        "eps_rows": eps_rows,
        "post_apply_checks": {
            "duplicate_key_count": duplicate_key_count,
            "value_mismatch_count": value_mismatch_count,
            "unit_conflict_count": unit_conflict_count,
            "year_conflict_count": year_conflict_count,
            "eps_unit_conflict_remaining_count": eps_unit_conflict_remaining_count,
            "check_delivery_state_overall_status": check_delivery_state_overall_status,
            "rollback_possible": rollback_possible,
        },
        "ready_for_next_stage": False,
    }

    summary["ready_for_next_stage"] = bool(
        summary["applied_count"] == 5
        and summary["recommended_unit"] == RECOMMENDED_UNIT
        and (summary["formal_rules_modified"] is False)
        and (summary["official_02b_modified"] is False)
        and summary["production_01_unchanged"]
        and summary["production_02_unchanged"]
        and summary["production_02a_unchanged"]
        and summary["production_05_unchanged"]
        and summary["production_06_modified"]
        and summary["post_apply_checks"]["duplicate_key_count"] == 0
        and summary["post_apply_checks"]["value_mismatch_count"] == 0
        and summary["post_apply_checks"]["unit_conflict_count"] == 0
        and summary["post_apply_checks"]["year_conflict_count"] == 0
        and summary["post_apply_checks"]["eps_unit_conflict_remaining_count"] == 0
        and summary["post_apply_checks"]["check_delivery_state_overall_status"] == "PASS"
        and summary["post_apply_checks"]["rollback_possible"]
    )

    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    report_lines = [
        "# Stage5X EPS Unit Conflict Apply Report",
        "",
        "## Scope",
        "- Limited to EPS / 每股收益 5 reviewed rows from Stage 5W",
        "",
        "## Basis",
        f"- stage5w summary: {INPUT_STAGE5W_SUMMARY_JSON}",
        f"- based_on_stage5w_commit: {BASED_ON_STAGE5W_COMMIT}",
        "",
        "## Apply Detail",
        f"- applied_count: {applied_count}",
        f"- updated_existing_count: {updated_existing_count}",
        f"- inserted_new_count: {inserted_new_count}",
        f"- skipped_count: {skipped_count}",
        f"- blocker_count: {blocker_count}",
        "",
        "## Row Count",
        f"- production_06_row_count_before: {production_06_row_count_before}",
        f"- production_06_row_count_after: {production_06_row_count_after}",
        "",
        "## Unit Decision",
        f"- recommended_unit: {RECOMMENDED_UNIT}",
        "- ratio vs 元 conflict normalized to 元/股",
        "",
        "## Guard",
        f"- formal_rules_modified: {formal_rules_modified}",
        f"- official_02b_modified: {official_02b_modified}",
        f"- production_01_unchanged: {production_01_unchanged}",
        f"- production_02_unchanged: {production_02_unchanged}",
        f"- production_02a_unchanged: {production_02a_unchanged}",
        f"- production_05_unchanged: {production_05_unchanged}",
        "",
        "## Validation",
        f"- duplicate_key_count: {duplicate_key_count}",
        f"- value_mismatch_count: {value_mismatch_count}",
        f"- unit_conflict_count: {unit_conflict_count}",
        f"- year_conflict_count: {year_conflict_count}",
        f"- eps_unit_conflict_remaining_count: {eps_unit_conflict_remaining_count}",
        f"- check_delivery_state_overall_status: {check_delivery_state_overall_status}",
        f"- rollback_possible: {rollback_possible}",
        f"- ready_for_next_stage: {summary['ready_for_next_stage']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(report_lines), encoding="utf-8")

    _write_excel(
        OUT_AUDIT_XLSX,
        {
            "eps_apply_rows": pd.DataFrame(eps_rows),
            "production_06_before": current_06,
            "production_06_after": post_df,
        },
    )

    print(f"stage5x_summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5x_report_md: {OUT_REPORT_MD}")
    print(f"stage5x_audit_xlsx: {OUT_AUDIT_XLSX}")
    print(f"ready_for_next_stage: {summary['ready_for_next_stage']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
