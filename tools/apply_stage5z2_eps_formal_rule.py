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

STAGE5Z_SUMMARY = OUTPUT_DIR / "stage5z_eps_formal_rule_review" / "176_stage5z_eps_formal_rule_review_summary.json"
STAGE5Y_SUMMARY = OUTPUT_DIR / "stage5y_final_delivery_audit" / "175_stage5y_final_delivery_audit_summary.json"
STAGE5X_SUMMARY = OUTPUT_DIR / "stage5x_eps_unit_apply" / "174_stage5x_eps_unit_apply_summary.json"
STAGE5W_REVIEW = OUTPUT_DIR / "stage5w_eps_unit_conflict_review" / "172_stage5w_eps_conflict_review.xlsx"

FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

OUT_DIR = OUTPUT_DIR / "stage5z2_eps_formal_rule_apply"
OUT_SUMMARY = OUT_DIR / "177_stage5z2_eps_formal_rule_apply_summary.json"
OUT_REPORT = OUT_DIR / "177_stage5z2_eps_formal_rule_apply_report.md"

BASE_STAGE5Z_COMMIT = "8940c90876fa2beb1be877309d3aa60b112d80c1"
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


def _snapshot_delivery_hashes() -> Dict[str, str]:
    return {
        "01": _sha256(_find_delivery_file("01_*.xlsx")),
        "02": _sha256(_find_delivery_file("02_*.xlsx")),
        "02A": _sha256(_find_delivery_file("02A_*.xlsx")),
        "05": _sha256(_find_delivery_file("05_*.xlsx")),
        "06": _sha256(_find_delivery_file("06_*.xlsx")),
    }


def _run(cmd: List[str]) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=str(BASE_DIR))
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def _git_diff_exists(path: Path) -> bool:
    code, out, _ = _run(["git", "diff", "--name-only", "--", str(path.relative_to(BASE_DIR))])
    return bool(code == 0 and out)


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


def main() -> int:
    for p in [STAGE5Z_SUMMARY, STAGE5Y_SUMMARY, STAGE5X_SUMMARY, STAGE5W_REVIEW, FORMAL_SCOPE_RULES_JSON, STANDARDIZER_FILE, OFFICIAL_02B_PATH]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    stage5z = _load_json(STAGE5Z_SUMMARY)
    stage5y = _load_json(STAGE5Y_SUMMARY)
    stage5x = _load_json(STAGE5X_SUMMARY)
    stage5w_review = pd.read_excel(STAGE5W_REVIEW, sheet_name="eps_conflict_review").fillna("")
    scope_payload = _load_json(FORMAL_SCOPE_RULES_JSON)
    scope_rules = scope_payload.get("rules", {}) if isinstance(scope_payload, dict) else {}
    if not isinstance(scope_rules, dict):
        scope_rules = {}

    before_snapshot = _snapshot_delivery_hashes()
    before_check = _run_delivery_check()

    eps_rule_present_before = bool(stage5z.get("eps_rule_present_in_formal_rules"))
    eps_rule_has_unit_clause_before = bool(stage5z.get("eps_rule_has_unit_clause"))
    recommended_formal_unit = EPS_UNIT

    eps_rule = None
    eps_rule_id = ""
    for rid, rule in scope_rules.items():
        if _norm(rule.get("standard_metric")) == EPS_METRIC:
            eps_rule = rule
            eps_rule_id = rid
            break
    eps_rule_present_after = bool(eps_rule)
    eps_rule_has_unit_clause_after = _norm(eps_rule.get("standard_unit")) == EPS_UNIT if eps_rule else False
    eps_rule_scope = _norm(eps_rule.get("existing_scope")) if eps_rule else ""
    eps_rule_statement_types = []
    if eps_rule and isinstance(eps_rule.get("statement_types"), list):
        eps_rule_statement_types = [_norm(x) for x in eps_rule.get("statement_types", []) if _norm(x)]

    formal_rules_modified = _git_diff_exists(FORMAL_SCOPE_RULES_JSON)
    standardizer_modified = _git_diff_exists(STANDARDIZER_FILE)
    official_02b_modified = _git_diff_exists(OFFICIAL_02B_PATH)

    production_06 = pd.read_excel(_find_delivery_file("06_*.xlsx")).fillna("")
    production_06_row_count = int(len(production_06))
    work_06 = _prepare_06(production_06)
    eps_keys = set(stage5w_review.get("key", pd.Series([], dtype=str)).map(_norm).tolist())
    eps_df = work_06[work_06["key"].isin(eps_keys)].copy()
    eps_row_count = int(len(eps_df))
    eps_years = sorted([y for y in eps_df["year"].tolist() if y])
    eps_year_labels_ok = sorted(EPS_YEARS) == eps_years
    eps_unit_all_normalized = bool(
        eps_row_count == 5 and eps_df["final_unit"].map(_norm).eq(EPS_UNIT).all()
    )

    duplicate_key_count, value_mismatch_count, unit_conflict_count, year_conflict_count = _conflicts_06(production_06)
    check_delivery_state = _run_delivery_check()
    check_delivery_state_overall_status = _norm(check_delivery_state.get("overall_status")) or "UNKNOWN"

    after_snapshot = _snapshot_delivery_hashes()
    production_01_unchanged = before_snapshot["01"] == after_snapshot["01"]
    production_02_unchanged = before_snapshot["02"] == after_snapshot["02"]
    production_02a_unchanged = before_snapshot["02A"] == after_snapshot["02A"]
    production_05_unchanged = before_snapshot["05"] == after_snapshot["05"]
    production_06_unchanged = before_snapshot["06"] == after_snapshot["06"]
    official_02b_unchanged = not official_02b_modified
    production_files_modified = not (
        production_01_unchanged and production_02_unchanged and production_02a_unchanged and production_05_unchanged and production_06_unchanged
    )

    standardizer_text = STANDARDIZER_FILE.read_text(encoding="utf-8")
    standardizer_has_ratio_logic = "RATIO_METRICS" in standardizer_text and 'RATIO_METRICS = {"毛利率", "ROE"}' in standardizer_text
    standardizer_has_eps_logic = "EPS_METRICS" in standardizer_text and "每股收益" in standardizer_text and "eps_extreme_no_repair" in standardizer_text
    ratio_metric_regression_check_pass = bool(
        standardizer_has_ratio_logic
        and standardizer_has_eps_logic
        and not standardizer_modified
        and eps_unit_all_normalized
        and duplicate_key_count == 0
        and value_mismatch_count == 0
        and unit_conflict_count == 0
        and year_conflict_count == 0
    )

    applied_rule_location = "formal_rules"
    if formal_rules_modified and standardizer_modified:
        applied_rule_location = "both"
    elif standardizer_modified and not formal_rules_modified:
        applied_rule_location = "financial_standardizer"

    ready_for_final_delivery_freeze = bool(
        check_delivery_state_overall_status == "PASS"
        and production_06_row_count == 119
        and eps_row_count == 5
        and eps_year_labels_ok
        and eps_unit_all_normalized
        and duplicate_key_count == 0
        and value_mismatch_count == 0
        and unit_conflict_count == 0
        and year_conflict_count == 0
        and production_01_unchanged
        and production_02_unchanged
        and production_02a_unchanged
        and production_05_unchanged
        and production_06_unchanged
        and official_02b_unchanged
        and formal_rules_modified
        and ratio_metric_regression_check_pass
    )

    summary = {
        "stage": "stage5z2_eps_formal_rule_apply",
        "mode": "limited_rule_apply",
        "based_on_stage5z_commit": BASE_STAGE5Z_COMMIT,
        "production_files_modified": production_files_modified,
        "production_01_unchanged": production_01_unchanged,
        "production_02_unchanged": production_02_unchanged,
        "production_02a_unchanged": production_02a_unchanged,
        "production_05_unchanged": production_05_unchanged,
        "production_06_unchanged": production_06_unchanged,
        "official_02b_modified": official_02b_modified,
        "official_02b_unchanged": official_02b_unchanged,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "eps_rule_present_before": eps_rule_present_before,
        "eps_rule_has_unit_clause_before": eps_rule_has_unit_clause_before,
        "eps_rule_present_after": eps_rule_present_after,
        "eps_rule_has_unit_clause_after": eps_rule_has_unit_clause_after,
        "eps_rule_id": eps_rule_id,
        "eps_rule_scope": eps_rule_scope,
        "eps_rule_statement_types": eps_rule_statement_types,
        "recommended_formal_unit": recommended_formal_unit,
        "applied_rule_location": applied_rule_location,
        "ratio_metric_regression_check_pass": ratio_metric_regression_check_pass,
        "check_delivery_state_overall_status": check_delivery_state_overall_status,
        "production_06_row_count": production_06_row_count,
        "eps_row_count": eps_row_count,
        "eps_years": eps_years,
        "eps_year_labels_ok": eps_year_labels_ok,
        "eps_unit_all_normalized": eps_unit_all_normalized,
        "eps_unit": EPS_UNIT,
        "duplicate_key_count": duplicate_key_count,
        "value_mismatch_count": value_mismatch_count,
        "unit_conflict_count": unit_conflict_count,
        "year_conflict_count": year_conflict_count,
        "ready_for_final_delivery_freeze": ready_for_final_delivery_freeze,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    report = [
        "# Stage5Z2 EPS Formal Rule Apply",
        "",
        "## Background",
        f"- based_on_stage5z_commit: {BASE_STAGE5Z_COMMIT}",
        f"- recommended_formal_unit: {recommended_formal_unit}",
        "",
        "## Rule Update",
        f"- eps_rule_present_before: {eps_rule_present_before}",
        f"- eps_rule_has_unit_clause_before: {eps_rule_has_unit_clause_before}",
        f"- eps_rule_present_after: {eps_rule_present_after}",
        f"- eps_rule_has_unit_clause_after: {eps_rule_has_unit_clause_after}",
        f"- applied_rule_location: {applied_rule_location}",
        f"- formal_rules_modified: {formal_rules_modified}",
        f"- standardizer_modified: {standardizer_modified}",
        "",
        "## Delivery Audit",
        f"- check_delivery_state_overall_status: {check_delivery_state_overall_status}",
        f"- production_06_row_count: {production_06_row_count}",
        f"- eps_row_count: {eps_row_count}",
        f"- eps_years: {', '.join(eps_years)}",
        f"- eps_unit_all_normalized: {eps_unit_all_normalized}",
        f"- eps_unit: {EPS_UNIT}",
        "",
        "## Conflict Check",
        f"- duplicate_key_count: {duplicate_key_count}",
        f"- value_mismatch_count: {value_mismatch_count}",
        f"- unit_conflict_count: {unit_conflict_count}",
        f"- year_conflict_count: {year_conflict_count}",
        f"- ratio_metric_regression_check_pass: {ratio_metric_regression_check_pass}",
        "",
        "## Unchanged Guard",
        f"- production_01_unchanged: {production_01_unchanged}",
        f"- production_02_unchanged: {production_02_unchanged}",
        f"- production_02a_unchanged: {production_02a_unchanged}",
        f"- production_05_unchanged: {production_05_unchanged}",
        f"- production_06_unchanged: {production_06_unchanged}",
        f"- official_02b_unchanged: {official_02b_unchanged}",
        f"- production_files_modified: {production_files_modified}",
        "",
        "## Decision",
        f"- ready_for_final_delivery_freeze: {ready_for_final_delivery_freeze}",
    ]
    OUT_REPORT.write_text("\n".join(report), encoding="utf-8")

    print(f"stage5z2_summary_json: {OUT_SUMMARY}")
    print(f"stage5z2_report_md: {OUT_REPORT}")
    print(f"ready_for_final_delivery_freeze: {ready_for_final_delivery_freeze}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
