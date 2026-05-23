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

STAGE5X_SUMMARY = OUTPUT_DIR / "stage5x_eps_unit_apply" / "174_stage5x_eps_unit_apply_summary.json"
STAGE5W_REVIEW = OUTPUT_DIR / "stage5w_eps_unit_conflict_review" / "172_stage5w_eps_conflict_review.xlsx"
OUT_DIR = OUTPUT_DIR / "stage5y_final_delivery_audit"
OUT_SUMMARY = OUT_DIR / "175_stage5y_final_delivery_audit_summary.json"
OUT_REPORT = OUT_DIR / "175_stage5y_final_delivery_audit_report.md"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"

BASE_STAGE5X_COMMIT = "82025971de98ea7ae038b27f37920c66d1aa86e8"
EPS_METRIC = "\u6bcf\u80a1\u6536\u76ca"
EPS_UNIT = "\u5143/\u80a1"
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
        "scope_rules": _sha256(FORMAL_SCOPE_RULES_JSON),
        "standardizer": _sha256(FORMAL_STANDARDIZER_FILE),
    }


def _run(cmd: List[str]) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def _run_delivery_check() -> str:
    code, out, _ = _run([sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"])
    if code != 0:
        return "FAIL"
    try:
        payload = json.loads(out or "{}")
        return _norm(payload.get("overall_status")) or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def _prepare_06(df: pd.DataFrame) -> pd.DataFrame:
    w = df.copy().fillna("")
    for c in ["asset_package", "source_pdf", "standard_metric", "year", "final_value", "final_unit"]:
        if c not in w.columns:
            w[c] = ""
        w[c] = w[c].map(_norm)
    w["key"] = w.apply(
        lambda r: f"{_norm(r['asset_package'])}||{_norm(r['source_pdf'])}||{_norm(r['standard_metric'])}||{_norm(r['year'])}",
        axis=1,
    )
    return w


def _conflicts_06(df: pd.DataFrame) -> Tuple[int, int, int, int]:
    w = _prepare_06(df)
    duplicate_key_count = int(w["key"].duplicated().sum())
    value_mismatch_count = 0
    unit_conflict_count = 0
    year_conflict_count = 0

    for _, g in w.groupby("key"):
        if g["final_value"].nunique() > 1:
            value_mismatch_count += 1
        if g["final_unit"].nunique() > 1:
            unit_conflict_count += 1
    for _, g in w.groupby(["asset_package", "source_pdf", "standard_metric"]):
        ys = [y for y in g["year"].tolist() if y]
        if len(ys) != len(set(ys)):
            year_conflict_count += 1
    return duplicate_key_count, value_mismatch_count, unit_conflict_count, year_conflict_count


def main() -> int:
    if not STAGE5X_SUMMARY.exists():
        raise FileNotFoundError(f"Missing Stage5X summary: {STAGE5X_SUMMARY}")
    if not STAGE5W_REVIEW.exists():
        raise FileNotFoundError(f"Missing Stage5W review: {STAGE5W_REVIEW}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # HEAD must include Stage5X commit
    code, _, _ = _run(["git", "-C", str(BASE_DIR), "merge-base", "--is-ancestor", BASE_STAGE5X_COMMIT, "HEAD"])
    if code != 0:
        raise RuntimeError(f"Current HEAD does not include required commit {BASE_STAGE5X_COMMIT}.")

    before = _snapshot_hashes()
    production_06 = _find_delivery_file("06_*.xlsx")
    df06 = pd.read_excel(production_06).fillna("")
    production_06_row_count = int(len(df06))

    w06 = _prepare_06(df06)
    eps_keys_df = pd.read_excel(STAGE5W_REVIEW, sheet_name="eps_conflict_review").fillna("")
    eps_target_keys = sorted(eps_keys_df.get("key", "").map(_norm).tolist())
    eps_df = w06[w06["key"].map(_norm).isin(set(eps_target_keys))].copy()
    eps_row_count = int(len(eps_df))
    eps_years = sorted(eps_df["year"].tolist())
    eps_year_set_ok = sorted(EPS_YEARS) == eps_years
    eps_unit_all_normalized = bool(eps_row_count == 5 and eps_df["final_unit"].map(_norm).eq(EPS_UNIT).all())

    duplicate_key_count, value_mismatch_count, unit_conflict_count, year_conflict_count = _conflicts_06(df06)

    check_delivery_state_overall_status = _run_delivery_check()

    after = _snapshot_hashes()
    production_01_unchanged = before["01"] == after["01"]
    production_02_unchanged = before["02"] == after["02"]
    production_02a_unchanged = before["02A"] == after["02A"]
    production_05_unchanged = before["05"] == after["05"]
    production_06_unchanged = before["06"] == after["06"]
    official_02b_unchanged = before["02B"] == after["02B"]
    formal_rules_unchanged = (before["scope_rules"] == after["scope_rules"]) and (
        before["standardizer"] == after["standardizer"]
    )

    summary = {
        "stage": "stage5y_final_delivery_audit",
        "mode": "read_only_audit",
        "based_on_stage5x_commit": BASE_STAGE5X_COMMIT,
        "production_06_row_count": production_06_row_count,
        "eps_row_count": eps_row_count,
        "eps_years": eps_years,
        "eps_year_labels_ok": eps_year_set_ok,
        "eps_unit_all_normalized": eps_unit_all_normalized,
        "eps_unit": EPS_UNIT,
        "duplicate_key_count": duplicate_key_count,
        "value_mismatch_count": value_mismatch_count,
        "unit_conflict_count": unit_conflict_count,
        "year_conflict_count": year_conflict_count,
        "production_01_unchanged": production_01_unchanged,
        "production_02_unchanged": production_02_unchanged,
        "production_02a_unchanged": production_02a_unchanged,
        "production_05_unchanged": production_05_unchanged,
        "production_06_unchanged": production_06_unchanged,
        "official_02b_unchanged": official_02b_unchanged,
        "formal_rules_unchanged": formal_rules_unchanged,
        "check_delivery_state_overall_status": check_delivery_state_overall_status,
        "ready_for_delivery_freeze": False,
        "ready_for_stage5z_rule_review": False,
    }

    summary["ready_for_delivery_freeze"] = bool(
        summary["production_06_row_count"] == 119
        and summary["eps_row_count"] == 5
        and summary["eps_year_labels_ok"]
        and summary["eps_unit_all_normalized"]
        and summary["duplicate_key_count"] == 0
        and summary["value_mismatch_count"] == 0
        and summary["unit_conflict_count"] == 0
        and summary["year_conflict_count"] == 0
        and summary["production_01_unchanged"]
        and summary["production_02_unchanged"]
        and summary["production_02a_unchanged"]
        and summary["production_05_unchanged"]
        and summary["production_06_unchanged"]
        and summary["official_02b_unchanged"]
        and summary["formal_rules_unchanged"]
        and summary["check_delivery_state_overall_status"] == "PASS"
    )
    summary["ready_for_stage5z_rule_review"] = summary["ready_for_delivery_freeze"]

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Stage5Y Final Delivery Audit Report",
        "",
        "## Head Baseline",
        f"- based_on_stage5x_commit: {BASE_STAGE5X_COMMIT}",
        "",
        "## Delivery Check",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        "",
        "## Production 06",
        f"- production_06_row_count: {summary['production_06_row_count']}",
        f"- eps_row_count: {summary['eps_row_count']}",
        f"- eps_years: {', '.join(summary['eps_years'])}",
        f"- eps_unit_all_normalized: {summary['eps_unit_all_normalized']}",
        f"- eps_unit: {summary['eps_unit']}",
        "",
        "## Conflict Check",
        f"- duplicate_key_count: {summary['duplicate_key_count']}",
        f"- value_mismatch_count: {summary['value_mismatch_count']}",
        f"- unit_conflict_count: {summary['unit_conflict_count']}",
        f"- year_conflict_count: {summary['year_conflict_count']}",
        "",
        "## Unchanged Guard",
        f"- production_01_unchanged: {summary['production_01_unchanged']}",
        f"- production_02_unchanged: {summary['production_02_unchanged']}",
        f"- production_02a_unchanged: {summary['production_02a_unchanged']}",
        f"- production_05_unchanged: {summary['production_05_unchanged']}",
        f"- production_06_unchanged: {summary['production_06_unchanged']}",
        f"- official_02b_unchanged: {summary['official_02b_unchanged']}",
        f"- formal_rules_unchanged: {summary['formal_rules_unchanged']}",
        "",
        "## Decision",
        f"- ready_for_delivery_freeze: {summary['ready_for_delivery_freeze']}",
        f"- ready_for_stage5z_rule_review: {summary['ready_for_stage5z_rule_review']}",
    ]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"stage5y_summary_json: {OUT_SUMMARY}")
    print(f"stage5y_report_md: {OUT_REPORT}")
    print(f"ready_for_delivery_freeze: {summary['ready_for_delivery_freeze']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
