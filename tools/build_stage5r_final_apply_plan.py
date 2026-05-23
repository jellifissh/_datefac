import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

INPUT_STAGE5Q_DIR = OUTPUT_DIR / "stage5q_apply_precheck_fix"
INPUT_FIXED_REVIEW_XLSX = INPUT_STAGE5Q_DIR / "158_stage5q_fixed_metric_level_review.xlsx"
INPUT_FIXED_DIFF_XLSX = INPUT_STAGE5Q_DIR / "158_stage5q_fixed_diff_with_production_02_05.xlsx"
INPUT_STAGE5Q_SUMMARY_JSON = INPUT_STAGE5Q_DIR / "159_stage5q_apply_precheck_fix_summary.json"

INPUT_STAGE5O_DIR = OUTPUT_DIR / "stage5o_promotion_review"
INPUT_STAGE5O_CANDIDATE_02_XLSX = INPUT_STAGE5O_DIR / "154_stage5o_candidate_02.xlsx"
INPUT_STAGE5O_CANDIDATE_05_XLSX = INPUT_STAGE5O_DIR / "154_stage5o_candidate_05.xlsx"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
FORMAL_ALIAS_RULE_FILE = BASE_DIR / "financial_standardizer.py"

OUT_DIR = OUTPUT_DIR / "stage5r_final_apply_plan"
OUT_APPLY_MANIFEST_XLSX = OUT_DIR / "160_stage5r_apply_manifest.xlsx"
OUT_APPLY_RISK_REVIEW_XLSX = OUT_DIR / "160_stage5r_apply_risk_review.xlsx"
OUT_BACKUP_ROLLBACK_MD = OUT_DIR / "160_stage5r_backup_rollback_plan.md"
OUT_REPORT_MD = OUT_DIR / "160_stage5r_final_apply_plan_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "161_stage5r_final_apply_plan_summary.json"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31-len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


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
        "formal_scope_rules": _sha256(FORMAL_SCOPE_RULES_JSON),
        "formal_mapping_rules": _sha256(FORMAL_MAPPING_RULE_FILE),
        "formal_normalization_rules": _sha256(FORMAL_NORMALIZATION_RULE_FILE),
        "formal_alias_rules": _sha256(FORMAL_ALIAS_RULE_FILE),
    }


def _find_true_production_ref_files() -> Tuple[Optional[Path], Optional[Path]]:
    out = BASE_DIR / "output"
    cand02: List[Path] = []
    cand05: List[Path] = []
    for p in out.rglob("*.xlsx"):
        sp = str(p)
        if "H3_AP202605121822223662_1" not in sp:
            continue
        if "stage5a_pdf_conversion_audit" in sp or "stage5k_full_sandbox_rebuild" in sp or "_stage1_safe_runner_trial" in sp:
            continue
        if p.name.startswith("02_") and "结构化" in p.name:
            cand02.append(p)
        if p.name.startswith("05_") and "标准化" in p.name:
            cand05.append(p)
    cand02 = sorted(cand02, key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True)
    cand05 = sorted(cand05, key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True)
    return (cand02[0] if cand02 else None, cand05[0] if cand05 else None)


def _df_content_hash(df: pd.DataFrame, sort_cols: List[str]) -> str:
    work = df.copy().fillna("")
    for c in sort_cols:
        if c not in work.columns:
            work[c] = ""
    work = work.sort_values(sort_cols, kind="mergesort")
    csv_text = work.to_csv(index=False, encoding="utf-8")
    return hashlib.sha256(csv_text.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5R build final apply plan (manifest/risk/rollback) without real apply.")
    parser.parse_args()

    required = [
        INPUT_FIXED_REVIEW_XLSX,
        INPUT_FIXED_DIFF_XLSX,
        INPUT_STAGE5Q_SUMMARY_JSON,
        INPUT_STAGE5O_CANDIDATE_02_XLSX,
        INPUT_STAGE5O_CANDIDATE_05_XLSX,
        OFFICIAL_02B_PATH,
        FORMAL_SCOPE_RULES_JSON,
        FORMAL_MAPPING_RULE_FILE,
        FORMAL_NORMALIZATION_RULE_FILE,
        FORMAL_ALIAS_RULE_FILE,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    before = _snapshot_hashes()

    stage5q_summary = json.loads(INPUT_STAGE5Q_SUMMARY_JSON.read_text(encoding="utf-8"))
    review_df = pd.read_excel(INPUT_FIXED_REVIEW_XLSX, sheet_name="fixed_metric_level_review").fillna("")
    fixed_candidate_02_df = pd.read_excel(INPUT_FIXED_REVIEW_XLSX, sheet_name="fixed_candidate_02").fillna("")
    fixed_candidate_05_df = pd.read_excel(INPUT_FIXED_REVIEW_XLSX, sheet_name="fixed_candidate_05").fillna("")

    diff02_df = pd.read_excel(INPUT_FIXED_DIFF_XLSX, sheet_name="fixed_diff_with_production_02").fillna("")
    diff05_df = pd.read_excel(INPUT_FIXED_DIFF_XLSX, sheet_name="fixed_diff_with_production_05").fillna("")

    # Resolve production refs (prefer summary paths if valid, otherwise discover)
    p02_from_summary = Path(_norm(stage5q_summary.get("production_02_reference_file"))) if _norm(stage5q_summary.get("production_02_reference_file")) else None
    p05_from_summary = Path(_norm(stage5q_summary.get("production_05_reference_file"))) if _norm(stage5q_summary.get("production_05_reference_file")) else None
    if p02_from_summary and p02_from_summary.exists():
        production_02_ref = p02_from_summary
    else:
        production_02_ref, _ = _find_true_production_ref_files()
    if p05_from_summary and p05_from_summary.exists():
        production_05_ref = p05_from_summary
    else:
        _, production_05_ref = _find_true_production_ref_files()

    if not production_02_ref or not production_02_ref.exists():
        raise FileNotFoundError("Production 02 reference not found for Stage5R.")
    if not production_05_ref or not production_05_ref.exists():
        raise FileNotFoundError("Production 05 reference not found for Stage5R.")

    # Build metric key on candidates and review.
    fixed_candidate_02_df["metric_level_key"] = (
        fixed_candidate_02_df["raw_metric_name"].map(_norm)
        + "||"
        + fixed_candidate_02_df["statement_type"].map(_norm)
        + "||"
        + fixed_candidate_02_df["unit"].map(_norm)
    )
    fixed_candidate_05_df["metric_level_key"] = (
        fixed_candidate_05_df["raw_metric_name"].map(_norm)
        + "||"
        + fixed_candidate_05_df["statement_type"].map(_norm)
        + "||"
        + fixed_candidate_05_df["unit"].map(_norm)
    )

    promote02_metric_keys = set(
        review_df[review_df["recommended_action"] == "PROMOTE_TO_02_ONLY"]["metric_level_key"].map(_norm).tolist()
    )
    promote05_metric_keys = set(
        review_df[review_df["recommended_action"] == "PROMOTE_TO_05_SAFE"]["metric_level_key"].map(_norm).tolist()
    )
    excluded_need_mapping_metrics = review_df[review_df["recommended_action"] == "NEED_MAPPING_RULE"].copy()
    excluded_need_scope_metrics = review_df[review_df["recommended_action"] == "NEED_SCOPE_REVIEW"].copy()
    blocked_metrics = review_df[review_df["recommended_action"] == "BLOCKED"].copy()

    apply02_df = fixed_candidate_02_df[fixed_candidate_02_df["metric_level_key"].map(_norm).isin(promote02_metric_keys)].copy()
    apply05_df = fixed_candidate_05_df[fixed_candidate_05_df["metric_level_key"].map(_norm).isin(promote05_metric_keys)].copy()
    apply05_df = apply05_df[apply05_df["standardization_status"] == "STANDARDIZED_OK"].copy()

    promote_to_02_metric_count = int(len(promote02_metric_keys))
    promote_to_02_row_count = int(len(apply02_df))
    promote_to_05_metric_count = int(len(promote05_metric_keys))
    promote_to_05_row_count = int(len(apply05_df))

    excluded_need_mapping_metric_count = int(len(excluded_need_mapping_metrics))
    excluded_need_scope_review_metric_count = int(len(excluded_need_scope_metrics))
    blocked_metric_count = int(len(blocked_metrics))

    # Hash guard values
    production_02_hash_before = _sha256(production_02_ref)
    production_05_hash_before = _sha256(production_05_ref)
    candidate_02_hash = _df_content_hash(
        apply02_df,
        ["metric_level_key", "year", "value", "source_reference"],
    ) if not apply02_df.empty else hashlib.sha256(b"").hexdigest()
    candidate_05_hash = _df_content_hash(
        apply05_df,
        ["metric_level_key", "standard_metric", "year", "value", "source_reference"],
    ) if not apply05_df.empty else hashlib.sha256(b"").hexdigest()

    # Apply manifest
    manifest_rows: List[Dict[str, Any]] = []
    for _, r in apply02_df.iterrows():
        manifest_rows.append(
            {
                "target_layer": "02",
                "metric_level_key": _norm(r.get("metric_level_key")),
                "metric_name_cleaned": _norm(r.get("metric_name_cleaned")),
                "statement_type": _norm(r.get("statement_type")),
                "unit": _norm(r.get("unit")),
                "year": _norm(r.get("year")),
                "value": _norm(r.get("value")),
                "source_reference": _norm(r.get("source_reference")),
                "planned_action": "UPSERT_CANDIDATE_TO_02",
            }
        )
    for _, r in apply05_df.iterrows():
        manifest_rows.append(
            {
                "target_layer": "05",
                "metric_level_key": _norm(r.get("metric_level_key")),
                "metric_name_cleaned": _norm(r.get("metric_name_cleaned")),
                "standard_metric": _norm(r.get("standard_metric")),
                "statement_type": _norm(r.get("statement_type")),
                "unit": _norm(r.get("unit")),
                "year": _norm(r.get("year")),
                "value": _norm(r.get("value")),
                "source_reference": _norm(r.get("source_reference")),
                "planned_action": "UPSERT_CANDIDATE_TO_05",
            }
        )
    manifest_df = pd.DataFrame(manifest_rows).fillna("")

    hash_guard_df = pd.DataFrame(
        [
            {"item": "production_02_reference_file", "value": str(production_02_ref)},
            {"item": "production_05_reference_file", "value": str(production_05_ref)},
            {"item": "production_02_hash_before", "value": production_02_hash_before},
            {"item": "production_05_hash_before", "value": production_05_hash_before},
            {"item": "candidate_02_hash", "value": candidate_02_hash},
            {"item": "candidate_05_hash", "value": candidate_05_hash},
        ]
    )

    _write_excel(
        OUT_APPLY_MANIFEST_XLSX,
        {
            "apply_manifest": manifest_df,
            "apply_02_rows": apply02_df,
            "apply_05_rows": apply05_df,
            "hash_guard": hash_guard_df,
        },
    )

    # Risk review
    risk_rows: List[Dict[str, Any]] = []
    for _, r in excluded_need_mapping_metrics.iterrows():
        risk_rows.append(
            {
                "risk_type": "EXCLUDED_NEED_MAPPING_RULE",
                "metric_level_key": _norm(r.get("metric_level_key")),
                "metric_name_cleaned": _norm(r.get("metric_name_cleaned")),
                "statement_type": _norm(r.get("statement_type")),
                "unit": _norm(r.get("unit")),
                "recommended_action": _norm(r.get("recommended_action")),
                "risk_level": "HIGH",
                "mitigation": "mapping rule review before real apply",
            }
        )
    for _, r in excluded_need_scope_metrics.iterrows():
        risk_rows.append(
            {
                "risk_type": "EXCLUDED_NEED_SCOPE_REVIEW",
                "metric_level_key": _norm(r.get("metric_level_key")),
                "metric_name_cleaned": _norm(r.get("metric_name_cleaned")),
                "statement_type": _norm(r.get("statement_type")),
                "unit": _norm(r.get("unit")),
                "recommended_action": _norm(r.get("recommended_action")),
                "risk_level": "HIGH",
                "mitigation": "scope/business definition review before real apply",
            }
        )
    for _, r in blocked_metrics.iterrows():
        risk_rows.append(
            {
                "risk_type": "BLOCKED_METRIC",
                "metric_level_key": _norm(r.get("metric_level_key")),
                "metric_name_cleaned": _norm(r.get("metric_name_cleaned")),
                "statement_type": _norm(r.get("statement_type")),
                "unit": _norm(r.get("unit")),
                "recommended_action": _norm(r.get("recommended_action")),
                "risk_level": "CRITICAL",
                "mitigation": "do not apply until blocker cleared",
            }
        )
    risk_df = pd.DataFrame(risk_rows).fillna("")

    diff_summary_df = pd.DataFrame(
        [
            {"layer": "02", "diff_class": k, "count": int(v)}
            for k, v in diff02_df["diff_class"].value_counts().to_dict().items()
        ]
        + [
            {"layer": "05", "diff_class": k, "count": int(v)}
            for k, v in diff05_df["diff_class"].value_counts().to_dict().items()
        ]
    )
    _write_excel(
        OUT_APPLY_RISK_REVIEW_XLSX,
        {
            "excluded_review_queue": risk_df,
            "metric_level_review": review_df,
            "diff_summary": diff_summary_df,
            "fixed_diff_02": diff02_df,
            "fixed_diff_05": diff05_df,
        },
    )

    rollback_md_lines = [
        "# Stage5R Backup and Rollback Plan",
        "",
        "## Backup Plan (Pre-Apply, Stage5S prerequisite)",
        f"1. Backup production 02 file: `{production_02_ref}`",
        f"2. Backup production 05 file: `{production_05_ref}`",
        "3. Record SHA256 hash before apply for both files.",
        "4. Freeze apply manifest hash and candidate hashes before execution.",
        "",
        "## Hash Guard",
        f"- production_02_hash_before: `{production_02_hash_before}`",
        f"- production_05_hash_before: `{production_05_hash_before}`",
        f"- candidate_02_hash: `{candidate_02_hash}`",
        f"- candidate_05_hash: `{candidate_05_hash}`",
        "",
        "## Rollback Trigger",
        "1. Any hash mismatch before write.",
        "2. Any row-level duplicate/conflict beyond pre-approved scope.",
        "3. Any post-apply check fails or delivery state degrades from PASS.",
        "",
        "## Rollback Steps",
        "1. Stop apply immediately (no partial continue).",
        "2. Restore 02/05 from backup copies.",
        "3. Re-check hashes to ensure exact restoration.",
        "4. Re-run delivery state check and capture incident report.",
        "",
        "## Scope Guard",
        "- No changes to production 01/02A/06, official 02B, or formal rules in Stage5R.",
    ]
    OUT_BACKUP_ROLLBACK_MD.write_text("\n".join(rollback_md_lines), encoding="utf-8")

    rollback_plan_generated = OUT_BACKUP_ROLLBACK_MD.exists()
    apply_manifest_generated = OUT_APPLY_MANIFEST_XLSX.exists()

    after = _snapshot_hashes()
    production_files_unchanged = bool(
        before["01"] == after["01"]
        and before["02"] == after["02"]
        and before["02A"] == after["02A"]
        and before["05"] == after["05"]
        and before["06"] == after["06"]
    )
    formal_rules_unchanged = bool(
        before["formal_scope_rules"] == after["formal_scope_rules"]
        and before["formal_mapping_rules"] == after["formal_mapping_rules"]
        and before["formal_normalization_rules"] == after["formal_normalization_rules"]
        and before["formal_alias_rules"] == after["formal_alias_rules"]
    )
    official_02B_unchanged = bool(before["02B"] == after["02B"])

    ready_for_stage5s_real_apply = bool(
        promote_to_02_row_count > 0
        and promote_to_05_row_count > 0
        and blocked_metric_count == 0
        and apply_manifest_generated
        and rollback_plan_generated
        and production_files_unchanged
        and formal_rules_unchanged
    )

    summary = {
        "production_02_reference_file": str(production_02_ref),
        "production_05_reference_file": str(production_05_ref),
        "promote_to_02_metric_count": int(promote_to_02_metric_count),
        "promote_to_02_row_count": int(promote_to_02_row_count),
        "promote_to_05_metric_count": int(promote_to_05_metric_count),
        "promote_to_05_row_count": int(promote_to_05_row_count),
        "excluded_need_mapping_metric_count": int(excluded_need_mapping_metric_count),
        "excluded_need_scope_review_metric_count": int(excluded_need_scope_review_metric_count),
        "blocked_metric_count": int(blocked_metric_count),
        "production_02_hash_before": production_02_hash_before,
        "production_05_hash_before": production_05_hash_before,
        "candidate_02_hash": candidate_02_hash,
        "candidate_05_hash": candidate_05_hash,
        "rollback_plan_generated": bool(rollback_plan_generated),
        "apply_manifest_generated": bool(apply_manifest_generated),
        "ready_for_stage5s_real_apply": bool(ready_for_stage5s_real_apply),
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_rules_unchanged": bool(formal_rules_unchanged),
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage5r_apply_plan_pass": False,
    }

    summary["stage5r_apply_plan_pass"] = bool(
        summary["promote_to_02_row_count"] > 0
        and summary["promote_to_05_row_count"] > 0
        and summary["apply_manifest_generated"]
        and summary["rollback_plan_generated"]
        and summary["production_files_unchanged"]
        and summary["formal_rules_unchanged"]
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    report_lines = [
        "# Stage5R Final Apply Plan (No Real Apply)",
        "",
        "## Apply Scope",
        f"- promote_to_02_metric_count: {summary['promote_to_02_metric_count']}",
        f"- promote_to_02_row_count: {summary['promote_to_02_row_count']}",
        f"- promote_to_05_metric_count: {summary['promote_to_05_metric_count']}",
        f"- promote_to_05_row_count: {summary['promote_to_05_row_count']}",
        "",
        "## Excluded Review Queue",
        f"- excluded_need_mapping_metric_count: {summary['excluded_need_mapping_metric_count']}",
        f"- excluded_need_scope_review_metric_count: {summary['excluded_need_scope_review_metric_count']}",
        f"- blocked_metric_count: {summary['blocked_metric_count']}",
        "",
        "## Hash Guard",
        f"- production_02_hash_before: {summary['production_02_hash_before']}",
        f"- production_05_hash_before: {summary['production_05_hash_before']}",
        f"- candidate_02_hash: {summary['candidate_02_hash']}",
        f"- candidate_05_hash: {summary['candidate_05_hash']}",
        "",
        "## Readiness",
        f"- rollback_plan_generated: {summary['rollback_plan_generated']}",
        f"- apply_manifest_generated: {summary['apply_manifest_generated']}",
        f"- ready_for_stage5s_real_apply: {summary['ready_for_stage5s_real_apply']}",
        f"- stage5r_apply_plan_pass: {summary['stage5r_apply_plan_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(report_lines), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage5r_apply_manifest_xlsx: {OUT_APPLY_MANIFEST_XLSX}")
    print(f"stage5r_apply_risk_review_xlsx: {OUT_APPLY_RISK_REVIEW_XLSX}")
    print(f"stage5r_backup_rollback_md: {OUT_BACKUP_ROLLBACK_MD}")
    print(f"stage5r_report_md: {OUT_REPORT_MD}")
    print(f"stage5r_summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5r_apply_plan_pass: {summary['stage5r_apply_plan_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
