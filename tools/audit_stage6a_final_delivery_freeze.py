import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

STAGE5Z2_SUMMARY = OUTPUT_DIR / "stage5z2_eps_formal_rule_apply" / "177_stage5z2_eps_formal_rule_apply_summary.json"
STAGE5Y_SUMMARY = OUTPUT_DIR / "stage5y_final_delivery_audit" / "175_stage5y_final_delivery_audit_summary.json"
STAGE5X_SUMMARY = OUTPUT_DIR / "stage5x_eps_unit_apply" / "174_stage5x_eps_unit_apply_summary.json"
STAGE5W_REVIEW = OUTPUT_DIR / "stage5w_eps_unit_conflict_review" / "172_stage5w_eps_conflict_review.xlsx"

FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

OUT_DIR = OUTPUT_DIR / "stage6a_final_delivery_freeze"
OUT_SUMMARY = OUT_DIR / "178_stage6a_final_delivery_freeze_summary.json"
OUT_REPORT = OUT_DIR / "178_stage6a_final_delivery_freeze_report.md"
OUT_HASH_MANIFEST = OUT_DIR / "178_stage6a_delivery_file_hash_manifest.json"

BASED_ON_STAGE5Z2_COMMIT = "1cde761d8ccb9875cd93b0260f9e2af230b47969"
EPS_METRIC = "每股收益"
EPS_UNIT = "元/股"
EPS_YEARS = ["2024A", "2025A", "2026E", "2027E", "2028E"]


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
        "formal_rules": _sha256(FORMAL_SCOPE_RULES_JSON),
        "standardizer": _sha256(STANDARDIZER_FILE),
    }


def _run(cmd: List[str]) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=str(BASE_DIR))
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def _run_delivery_check() -> Dict[str, Any]:
    code, out, _ = _run([sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"])
    if code != 0 or not out:
        return {"overall_status": "UNKNOWN"}
    try:
        return json.loads(out)
    except Exception:
        return {"overall_status": "UNKNOWN"}


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _prepare_06(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy().fillna("")
    for c in ["asset_package", "source_pdf", "standard_metric", "year", "final_value", "final_unit"]:
        if c not in work.columns:
            work[c] = ""
        work[c] = work[c].map(_norm)
    work["key"] = work.apply(
        lambda r: f"{_norm(r['asset_package'])}||{_norm(r['source_pdf'])}||{_norm(r['standard_metric'])}||{_norm(r['year'])}",
        axis=1,
    )
    return work


def _conflicts_06(df: pd.DataFrame) -> Tuple[int, int, int, int]:
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


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    for p in [STAGE5Z2_SUMMARY, STAGE5Y_SUMMARY, STAGE5X_SUMMARY, STAGE5W_REVIEW, FORMAL_SCOPE_RULES_JSON, STANDARDIZER_FILE, OFFICIAL_02B_PATH]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    stage5z2 = _load_json(STAGE5Z2_SUMMARY)
    _ = _load_json(STAGE5Y_SUMMARY)
    _ = _load_json(STAGE5X_SUMMARY)
    stage5w_review = pd.read_excel(STAGE5W_REVIEW, sheet_name="eps_conflict_review").fillna("")
    scope_payload = _load_json(FORMAL_SCOPE_RULES_JSON)
    scope_rules = scope_payload.get("rules", {}) if isinstance(scope_payload, dict) else {}
    if not isinstance(scope_rules, dict):
        scope_rules = {}

    before = _snapshot_hashes()
    check_delivery_before = _run_delivery_check()

    production_06_path = _find_delivery_file("06_*.xlsx")
    production_06_df = pd.read_excel(production_06_path).fillna("")
    production_06_row_count = int(len(production_06_df))
    production_06_work = _prepare_06(production_06_df)

    eps_keys = set(stage5w_review.get("key", pd.Series(dtype=str)).map(_norm).tolist())
    eps_df = production_06_work[production_06_work["key"].isin(eps_keys)].copy()
    eps_row_count = int(len(eps_df))
    eps_years = sorted([y for y in eps_df["year"].tolist() if y])
    eps_year_labels_ok = sorted(EPS_YEARS) == eps_years
    eps_unit_all_normalized = bool(
        eps_row_count == 5 and eps_df["final_unit"].map(_norm).eq(EPS_UNIT).all()
    )

    eps_rule_present = False
    eps_rule_has_unit_clause = False
    eps_rule_id = ""
    for rid, rule in scope_rules.items():
        if _norm(rule.get("standard_metric")) == EPS_METRIC:
            eps_rule_present = True
            eps_rule_id = rid
            eps_rule_has_unit_clause = _norm(rule.get("standard_unit")) == EPS_UNIT
            break

    duplicate_key_count, value_mismatch_count, unit_conflict_count, year_conflict_count = _conflicts_06(production_06_df)

    after = _snapshot_hashes()
    check_delivery_after = _run_delivery_check()
    check_delivery_state_overall_status = _norm(check_delivery_after.get("overall_status")) or "UNKNOWN"

    production_01_unchanged = before["01"] == after["01"]
    production_02_unchanged = before["02"] == after["02"]
    production_02a_unchanged = before["02A"] == after["02A"]
    production_05_unchanged = before["05"] == after["05"]
    production_06_unchanged = before["06"] == after["06"]
    official_02b_unchanged = before["02B"] == after["02B"]
    formal_rules_unchanged = before["formal_rules"] == after["formal_rules"]
    financial_standardizer_unchanged = before["standardizer"] == after["standardizer"]

    formal_rules_eps_unit_clause_present = bool(eps_rule_present and eps_rule_has_unit_clause)
    ratio_metric_regression_check_pass = bool(
        formal_rules_eps_unit_clause_present
        and financial_standardizer_unchanged
        and duplicate_key_count == 0
        and value_mismatch_count == 0
        and unit_conflict_count == 0
        and year_conflict_count == 0
        and eps_unit_all_normalized
    )

    ready_for_release_package = bool(
        check_delivery_state_overall_status == "PASS"
        and production_06_row_count == 119
        and eps_row_count == 5
        and eps_year_labels_ok
        and eps_unit_all_normalized
        and formal_rules_eps_unit_clause_present
        and financial_standardizer_unchanged
        and production_01_unchanged
        and production_02_unchanged
        and production_02a_unchanged
        and production_05_unchanged
        and production_06_unchanged
        and official_02b_unchanged
        and formal_rules_unchanged
        and duplicate_key_count == 0
        and value_mismatch_count == 0
        and unit_conflict_count == 0
        and year_conflict_count == 0
        and ratio_metric_regression_check_pass
    )

    summary = {
        "stage": "stage6a_final_delivery_freeze",
        "mode": "read_only_freeze_audit",
        "based_on_stage5z2_commit": BASED_ON_STAGE5Z2_COMMIT,
        "check_delivery_state_overall_status": check_delivery_state_overall_status,
        "production_06_row_count": production_06_row_count,
        "eps_row_count": eps_row_count,
        "eps_unit_all_normalized": eps_unit_all_normalized,
        "eps_unit": EPS_UNIT,
        "formal_rules_eps_unit_clause_present": formal_rules_eps_unit_clause_present,
        "standardizer_modified_this_stage": False,
        "production_files_modified_this_stage": False,
        "official_02b_modified_this_stage": False,
        "formal_rules_modified_this_stage": False,
        "duplicate_key_count": duplicate_key_count,
        "value_mismatch_count": value_mismatch_count,
        "unit_conflict_count": unit_conflict_count,
        "year_conflict_count": year_conflict_count,
        "ratio_metric_regression_check_pass": ratio_metric_regression_check_pass,
        "ready_for_release_package": ready_for_release_package,
        "rollback_possible": True,
        "production_01_unchanged": production_01_unchanged,
        "production_02_unchanged": production_02_unchanged,
        "production_02a_unchanged": production_02a_unchanged,
        "production_05_unchanged": production_05_unchanged,
        "production_06_unchanged": production_06_unchanged,
        "official_02b_unchanged": official_02b_unchanged,
        "formal_rules_unchanged": formal_rules_unchanged,
        "financial_standardizer_unchanged_this_stage": financial_standardizer_unchanged,
        "eps_years": eps_years,
        "eps_year_labels_ok": eps_year_labels_ok,
        "eps_rule_id": eps_rule_id,
        "hash_manifest_path": str(OUT_HASH_MANIFEST),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage6A Final Delivery Freeze Audit",
        "",
        "## Basis",
        f"- based_on_stage5z2_commit: {BASED_ON_STAGE5Z2_COMMIT}",
        "",
        "## Delivery Check",
        f"- check_delivery_state_overall_status: {check_delivery_state_overall_status}",
        "",
        "## Production 06",
        f"- production_06_row_count: {production_06_row_count}",
        f"- eps_row_count: {eps_row_count}",
        f"- eps_years: {', '.join(eps_years)}",
        f"- eps_unit_all_normalized: {eps_unit_all_normalized}",
        f"- eps_unit: {EPS_UNIT}",
        "",
        "## Formal Rule",
        f"- formal_rules_eps_unit_clause_present: {formal_rules_eps_unit_clause_present}",
        f"- eps_rule_id: {eps_rule_id}",
        "",
        "## Conflict Check",
        f"- duplicate_key_count: {duplicate_key_count}",
        f"- value_mismatch_count: {value_mismatch_count}",
        f"- unit_conflict_count: {unit_conflict_count}",
        f"- year_conflict_count: {year_conflict_count}",
        f"- ratio_metric_regression_check_pass: {ratio_metric_regression_check_pass}",
        "",
        "## Unchanged Guard",
        f"- standardizer_modified_this_stage: {False}",
        f"- production_files_modified_this_stage: {False}",
        f"- official_02b_modified_this_stage: {False}",
        f"- formal_rules_modified_this_stage: {False}",
        f"- production_01_unchanged: {production_01_unchanged}",
        f"- production_02_unchanged: {production_02_unchanged}",
        f"- production_02a_unchanged: {production_02a_unchanged}",
        f"- production_05_unchanged: {production_05_unchanged}",
        f"- production_06_unchanged: {production_06_unchanged}",
        f"- official_02b_unchanged: {official_02b_unchanged}",
        f"- formal_rules_unchanged: {formal_rules_unchanged}",
        "",
        "## Decision",
        f"- ready_for_release_package: {ready_for_release_package}",
        f"- rollback_possible: {True}",
    ]
    _write_text(OUT_REPORT, "\n".join(report_lines))

    manifest = {
        "production_01": {"path": str(_find_delivery_file("01_*.xlsx")), "sha256": before["01"]},
        "production_02": {"path": str(_find_delivery_file("02_*.xlsx")), "sha256": before["02"]},
        "production_02A": {"path": str(_find_delivery_file("02A_*.xlsx")), "sha256": before["02A"]},
        "production_05": {"path": str(_find_delivery_file("05_*.xlsx")), "sha256": before["05"]},
        "production_06": {"path": str(production_06_path), "sha256": before["06"]},
        "official_02B": {"path": str(OFFICIAL_02B_PATH), "sha256": before["02B"]},
        "formal_rules": {"path": str(FORMAL_SCOPE_RULES_JSON), "sha256": before["formal_rules"]},
        "financial_standardizer": {"path": str(STANDARDIZER_FILE), "sha256": before["standardizer"]},
        "stage6a_summary": {"path": str(OUT_SUMMARY), "sha256": _sha256(OUT_SUMMARY)},
        "stage6a_report": {"path": str(OUT_REPORT), "sha256": _sha256(OUT_REPORT)},
    }
    _write_json(OUT_HASH_MANIFEST, manifest)

    print(f"stage6a_summary_json: {OUT_SUMMARY}")
    print(f"stage6a_report_md: {OUT_REPORT}")
    print(f"stage6a_hash_manifest_json: {OUT_HASH_MANIFEST}")
    print(f"ready_for_release_package: {ready_for_release_package}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
