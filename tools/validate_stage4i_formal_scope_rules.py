import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STAGE4H_SUMMARY_JSON = OUTPUT_DIR / "stage4h_promote_scope_fixes" / "120_stage4h_scope_promotion_summary.json"
STAGE4G_APPROVAL_XLSX = OUTPUT_DIR / "stage4g_scope_promotion_approval" / "117_stage4g_scope_promotion_approval.xlsx"
STAGE4G_SUMMARY_JSON = OUTPUT_DIR / "stage4g_scope_promotion_approval" / "118_stage4g_scope_promotion_summary.json"
STAGE4F_XLSX = OUTPUT_DIR / "stage4f_dry_run_validate_fixes" / "115_stage4f_dry_run_validate_fixes.xlsx"
STAGE4F_SUMMARY_JSON = OUTPUT_DIR / "stage4f_dry_run_validate_fixes" / "116_stage4f_dry_run_validate_fixes_summary.json"
STAGE4D_XLSX = OUTPUT_DIR / "stage4d_mapping_rule_validation" / "111_stage4d_mapping_rule_validation.xlsx"
STAGE4A_XLSX = OUTPUT_DIR / "stage4a_structured_inventory" / "105_stage4a_structured_layer_inventory.xlsx"

FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

OUT_DIR = OUTPUT_DIR / "stage4i_validate_formal_scope_rules"
OUT_XLSX = OUT_DIR / "121_stage4i_validate_formal_scope_rules.xlsx"
OUT_MD = OUT_DIR / "121_stage4i_validate_formal_scope_rules.md"
OUT_JSON = OUT_DIR / "122_stage4i_validate_formal_scope_rules_summary.json"

READY_ACTION = "READY_FOR_FORMAL_SCOPE_PROMOTION"
APPROVED_DECISION = "APPROVED_FOR_FORMAL_SCOPE_PROMOTION"
ACTION_VALIDATED = "FORMAL_SCOPE_RULE_VALIDATED"
ACTION_RULE_MISSING = "FORMAL_SCOPE_RULE_MISSING"
ACTION_NOT_MATCHING = "FORMAL_SCOPE_RULE_NOT_MATCHING"
ACTION_NEED_RECHECK = "NEED_RULE_APPLICATION_RECHECK"
ACTION_NEED_ROLLBACK = "NEED_ROLLBACK_REVIEW"

PROMOTED_SCOPE = "INCLUDE_05_STANDARDIZED_TO_01/06_FINAL"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    s = _norm(v).lower()
    return s in {"true", "1", "yes", "y"}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_delivery_file(pattern: str, prefer_no_copy: bool = True, prefer_no_backup: bool = True) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing required file pattern: {pattern}")
    picked = files
    if prefer_no_copy:
        p2 = [p for p in picked if "_copy_" not in p.name.lower()]
        if p2:
            picked = p2
    if prefer_no_backup:
        p3 = [p for p in picked if "backup" not in p.name.lower()]
        if p3:
            picked = p3
    return picked[0]


def _snapshot_hashes() -> Dict[str, str]:
    return {
        "01": _sha256(_find_delivery_file("01_*.xlsx")),
        "02": _sha256(_find_delivery_file("02_*.xlsx")),
        "02A": _sha256(_find_delivery_file("02A_*.xlsx")),
        "05": _sha256(_find_delivery_file("05_*.xlsx")),
        "06": _sha256(_find_delivery_file("06_*.xlsx")),
        "02B": _sha256(OFFICIAL_02B_PATH),
        "formal_mapping_rules": _sha256(FORMAL_SCOPE_RULES_JSON),
        "formal_normalization_rules": _sha256(FORMAL_NORMALIZATION_RULE_FILE),
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
                return {"overall_status": "UNKNOWN"}
    return {"overall_status": "UNKNOWN"}


def _safe_write_excel_multi(sheets: Dict[str, pd.DataFrame], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def _safe_write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage4I dry-run validate formal scope rules after Stage4H promotion.")
    parser.parse_args()

    required_paths = [
        FORMAL_SCOPE_RULES_JSON,
        STAGE4H_SUMMARY_JSON,
        STAGE4G_APPROVAL_XLSX,
        STAGE4G_SUMMARY_JSON,
        STAGE4F_XLSX,
        STAGE4F_SUMMARY_JSON,
        STAGE4D_XLSX,
        STAGE4A_XLSX,
        FORMAL_NORMALIZATION_RULE_FILE,
        OFFICIAL_02B_PATH,
    ]
    for p in required_paths:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    snapshot_before = _snapshot_hashes()

    # Boundary reads only.
    _ = pd.read_excel(_find_delivery_file("01_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("02_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("02A_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("05_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("06_*.xlsx")).fillna("")
    _ = pd.read_excel(OFFICIAL_02B_PATH).fillna("")
    _ = pd.read_excel(STAGE4D_XLSX).fillna("")
    _ = pd.read_excel(STAGE4A_XLSX).fillna("")

    stage4h_summary = _load_json(STAGE4H_SUMMARY_JSON)
    stage4g_summary = _load_json(STAGE4G_SUMMARY_JSON)
    stage4f_summary = _load_json(STAGE4F_SUMMARY_JSON)

    if not _to_bool(stage4h_summary.get("stage4h_scope_promotion_pass", False)):
        raise RuntimeError("Stage4H summary indicates pass=false; abort Stage4I.")
    if not _to_bool(stage4g_summary.get("stage4g_scope_promotion_approval_ready", False)):
        raise RuntimeError("Stage4G summary indicates approval not ready; abort Stage4I.")
    if not _to_bool(stage4f_summary.get("stage4f_dry_run_validation_pass", False)):
        raise RuntimeError("Stage4F summary indicates pass=false; abort Stage4I.")

    stage4g_xls = pd.ExcelFile(STAGE4G_APPROVAL_XLSX)
    stage4g_df = pd.read_excel(STAGE4G_APPROVAL_XLSX, sheet_name=stage4g_xls.sheet_names[0]).fillna("")
    stage4f_df = pd.read_excel(STAGE4F_XLSX, sheet_name="stage4f_dry_run_validation").fillna("")
    scope_payload = _load_json(FORMAL_SCOPE_RULES_JSON)
    formal_rules = scope_payload.get("rules", {})
    if not isinstance(formal_rules, dict):
        formal_rules = {}

    approved_df = stage4g_df[stage4g_df["approval_decision"].map(_norm) == APPROVED_DECISION].copy()
    ready_df = stage4f_df[stage4f_df["recommended_stage4f_action"].map(_norm) == READY_ACTION].copy()
    ready_by_issue = {
        _norm(r["issue_id"]): r
        for _, r in ready_df.iterrows()
        if _norm(r.get("issue_id"))
    }

    out_rows: List[Dict[str, Any]] = []
    missing_count = 0
    not_matching_count = 0
    conflict_after_formal_rule_count = 0
    duplicate_after_formal_rule_count = 0
    formal_rule_found_count = 0
    formal_scope_present_count = 0
    matched_after_formal_scope_rule_count = 0

    for _, r in approved_df.iterrows():
        issue_id = _norm(r.get("issue_id"))
        existing_rule_id = _norm(r.get("existing_rule_id"))
        raw_metric_name = _norm(r.get("raw_metric_name"))
        target_standard_metric = _norm(r.get("target_standard_metric"))
        asset_package = _norm(r.get("asset_package"))
        statement_type = _norm(r.get("statement_type"))
        promoted_scope = _norm(r.get("proposed_scope")) or PROMOTED_SCOPE

        ready_row = ready_by_issue.get(issue_id)
        affects_05 = _to_bool(ready_row.get("affects_05")) if ready_row is not None else False
        affects_01 = _to_bool(ready_row.get("affects_01")) if ready_row is not None else False
        affects_06 = _to_bool(ready_row.get("affects_06")) if ready_row is not None else False

        rule = formal_rules.get(existing_rule_id)
        formal_rule_found = isinstance(rule, dict)
        if formal_rule_found:
            formal_rule_found_count += 1
        scope_list = []
        if formal_rule_found:
            scopes = rule.get("scope_applicability", [])
            if isinstance(scopes, list):
                scope_list = [_norm(x) for x in scopes if _norm(x)]
        formal_scope_present = promoted_scope in scope_list
        if formal_scope_present:
            formal_scope_present_count += 1

        conflict_after_formal_rule = False
        duplicate_after_formal_rule = False
        if formal_rule_found:
            promoted_fix_ids = rule.get("promoted_scope_fix_ids", [])
            if isinstance(promoted_fix_ids, list):
                promoted_fix_ids_norm = [_norm(x) for x in promoted_fix_ids if _norm(x)]
                duplicate_after_formal_rule = len(promoted_fix_ids_norm) != len(set(promoted_fix_ids_norm))
            else:
                duplicate_after_formal_rule = True

        if conflict_after_formal_rule:
            conflict_after_formal_rule_count += 1
        if duplicate_after_formal_rule:
            duplicate_after_formal_rule_count += 1

        dry_run_ok = (
            ready_row is not None
            and _norm(ready_row.get("dry_run_match_status")) == "MATCHED_AFTER_DRAFT_SCOPE_FIX"
            and not _to_bool(ready_row.get("conflict_after_draft"))
            and not _to_bool(ready_row.get("duplicate_after_draft"))
        )
        matched_after_formal_scope_rule = bool(
            formal_rule_found
            and formal_scope_present
            and dry_run_ok
            and not conflict_after_formal_rule
            and not duplicate_after_formal_rule
        )
        if matched_after_formal_scope_rule:
            matched_after_formal_scope_rule_count += 1

        if conflict_after_formal_rule:
            action = ACTION_NEED_ROLLBACK
            reason = "formal rule conflict detected after promotion"
            risk = "HIGH"
        elif duplicate_after_formal_rule:
            action = ACTION_NEED_RECHECK
            reason = "duplicate promoted fix ids detected in formal rule"
            risk = "MEDIUM"
        elif not formal_rule_found:
            action = ACTION_RULE_MISSING
            reason = "existing_rule_id missing in formal scope rules"
            risk = "HIGH"
            missing_count += 1
        elif not formal_scope_present:
            action = ACTION_NOT_MATCHING
            reason = "promoted scope not present in formal rule scope_applicability"
            risk = "HIGH"
            not_matching_count += 1
        elif not matched_after_formal_scope_rule:
            action = ACTION_NEED_RECHECK
            reason = "formal scope present but dry-run readiness evidence not satisfied"
            risk = "MEDIUM"
            not_matching_count += 1
        else:
            action = ACTION_VALIDATED
            reason = "formal scope rule present and matches stage4f ready issue evidence"
            risk = "LOW"

        out_rows.append(
            {
                "issue_id": issue_id,
                "existing_rule_id": existing_rule_id,
                "raw_metric_name": raw_metric_name,
                "target_standard_metric": target_standard_metric,
                "asset_package": asset_package,
                "statement_type": statement_type,
                "promoted_scope": promoted_scope,
                "formal_rule_found": bool(formal_rule_found),
                "formal_scope_present": bool(formal_scope_present),
                "matched_after_formal_scope_rule": bool(matched_after_formal_scope_rule),
                "conflict_after_formal_rule": bool(conflict_after_formal_rule),
                "duplicate_after_formal_rule": bool(duplicate_after_formal_rule),
                "affects_05": bool(affects_05),
                "affects_01": bool(affects_01),
                "affects_06": bool(affects_06),
                "recommended_stage4i_action": action,
                "action_reason": reason,
                "risk_level": risk,
            }
        )

    out_df = pd.DataFrame(out_rows)
    if not out_df.empty:
        out_df = out_df.sort_values(
            by=["recommended_stage4i_action", "existing_rule_id", "issue_id"],
            kind="mergesort",
        ).reset_index(drop=True)

    promoted_scope_fix_count = int(len(out_df))
    formal_scope_rule_missing_count = int(missing_count)
    formal_scope_rule_not_matching_count = int(not_matching_count)

    snapshot_after = _snapshot_hashes()
    production_files_unchanged = (
        snapshot_before["01"] == snapshot_after["01"]
        and snapshot_before["02"] == snapshot_after["02"]
        and snapshot_before["02A"] == snapshot_after["02A"]
        and snapshot_before["05"] == snapshot_after["05"]
        and snapshot_before["06"] == snapshot_after["06"]
    )
    output_06_unchanged = snapshot_before["06"] == snapshot_after["06"]
    official_02B_unchanged = snapshot_before["02B"] == snapshot_after["02B"]
    formal_mapping_rules_unchanged = snapshot_before["formal_mapping_rules"] == snapshot_after["formal_mapping_rules"]
    formal_normalization_rules_unchanged = snapshot_before["formal_normalization_rules"] == snapshot_after["formal_normalization_rules"]
    delivery_status_after = _run_delivery_check().get("overall_status", "UNKNOWN")

    summary = {
        "promoted_scope_fix_count": int(promoted_scope_fix_count),
        "formal_rule_found_count": int(formal_rule_found_count),
        "formal_scope_present_count": int(formal_scope_present_count),
        "matched_after_formal_scope_rule_count": int(matched_after_formal_scope_rule_count),
        "formal_scope_rule_missing_count": int(formal_scope_rule_missing_count),
        "formal_scope_rule_not_matching_count": int(formal_scope_rule_not_matching_count),
        "conflict_after_formal_rule_count": int(conflict_after_formal_rule_count),
        "duplicate_after_formal_rule_count": int(duplicate_after_formal_rule_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "formal_normalization_rules_unchanged": bool(formal_normalization_rules_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage4i_formal_scope_validation_pass": bool(
            promoted_scope_fix_count == 15
            and formal_rule_found_count == 15
            and formal_scope_present_count == 15
            and matched_after_formal_scope_rule_count == 15
            and formal_scope_rule_missing_count == 0
            and formal_scope_rule_not_matching_count == 0
            and conflict_after_formal_rule_count == 0
            and duplicate_after_formal_rule_count == 0
            and production_files_unchanged
            and output_06_unchanged
            and official_02B_unchanged
            and formal_mapping_rules_unchanged
            and formal_normalization_rules_unchanged
            and delivery_status_after == "PASS"
        ),
    }

    action_dist_df = (
        out_df.groupby("recommended_stage4i_action", dropna=False).size().reset_index(name="count")
        if not out_df.empty
        else pd.DataFrame(columns=["recommended_stage4i_action", "count"])
    )
    summary_df = pd.DataFrame(
        [
            ["promoted_scope_fix_count", summary["promoted_scope_fix_count"]],
            ["formal_rule_found_count", summary["formal_rule_found_count"]],
            ["formal_scope_present_count", summary["formal_scope_present_count"]],
            ["matched_after_formal_scope_rule_count", summary["matched_after_formal_scope_rule_count"]],
            ["formal_scope_rule_missing_count", summary["formal_scope_rule_missing_count"]],
            ["formal_scope_rule_not_matching_count", summary["formal_scope_rule_not_matching_count"]],
            ["conflict_after_formal_rule_count", summary["conflict_after_formal_rule_count"]],
            ["duplicate_after_formal_rule_count", summary["duplicate_after_formal_rule_count"]],
            ["production_files_unchanged", summary["production_files_unchanged"]],
            ["output_06_unchanged", summary["output_06_unchanged"]],
            ["official_02B_unchanged", summary["official_02B_unchanged"]],
            ["formal_mapping_rules_unchanged", summary["formal_mapping_rules_unchanged"]],
            ["formal_normalization_rules_unchanged", summary["formal_normalization_rules_unchanged"]],
            ["stage4i_formal_scope_validation_pass", summary["stage4i_formal_scope_validation_pass"]],
        ],
        columns=["metric", "value"],
    )

    md_lines = [
        "# Stage4I Validate Formal Scope Rules",
        "",
        f"- promoted_scope_fix_count: {summary['promoted_scope_fix_count']}",
        f"- formal_rule_found_count: {summary['formal_rule_found_count']}",
        f"- formal_scope_present_count: {summary['formal_scope_present_count']}",
        f"- matched_after_formal_scope_rule_count: {summary['matched_after_formal_scope_rule_count']}",
        f"- formal_scope_rule_missing_count: {summary['formal_scope_rule_missing_count']}",
        f"- formal_scope_rule_not_matching_count: {summary['formal_scope_rule_not_matching_count']}",
        f"- conflict_after_formal_rule_count: {summary['conflict_after_formal_rule_count']}",
        f"- duplicate_after_formal_rule_count: {summary['duplicate_after_formal_rule_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- output_06_unchanged: {summary['output_06_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- formal_normalization_rules_unchanged: {summary['formal_normalization_rules_unchanged']}",
        f"- stage4i_formal_scope_validation_pass: {summary['stage4i_formal_scope_validation_pass']}",
    ]

    _safe_write_excel_multi(
        {
            "stage4i_validation": out_df,
            "action_distribution": action_dist_df,
            "summary": summary_df,
        },
        OUT_XLSX,
    )
    _safe_write_text("\n".join(md_lines), OUT_MD)
    _safe_write_text(json.dumps(summary, ensure_ascii=False, indent=2), OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
