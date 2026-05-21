import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

STAGE4G_APPROVAL_XLSX = OUTPUT_DIR / "stage4g_scope_promotion_approval" / "117_stage4g_scope_promotion_approval.xlsx"
STAGE4G_SUMMARY_JSON = OUTPUT_DIR / "stage4g_scope_promotion_approval" / "118_stage4g_scope_promotion_summary.json"
STAGE4F_SUMMARY_JSON = OUTPUT_DIR / "stage4f_dry_run_validate_fixes" / "116_stage4f_dry_run_validate_fixes_summary.json"
STAGE4E_SCOPE_DRAFT_XLSX = BASE_DIR / "data" / "mapping" / "drafts" / "stage4e_scope_fix_draft.xlsx"

FORMAL_SCOPE_RULE_FILE = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

OUT_DIR = OUTPUT_DIR / "stage4h_promote_scope_fixes"
OUT_XLSX = OUT_DIR / "119_stage4h_scope_promotion_log.xlsx"
OUT_MD = OUT_DIR / "119_stage4h_scope_promotion_log.md"
OUT_JSON = OUT_DIR / "120_stage4h_scope_promotion_summary.json"
BACKUP_PATH = OUT_DIR / "backup" / "formal_scope_rules.before_stage4h.json"

APPROVED_DECISION = "APPROVED_FOR_FORMAL_SCOPE_PROMOTION"
PROMOTED_SCOPE = "INCLUDE_05_STANDARDIZED_TO_01/06_FINAL"
BASE_SCOPE = "GLOBAL_ALIAS_MATCH_ONLY"


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


def _sha256_or_missing(path: Path) -> str:
    return _sha256(path) if path.exists() else "__MISSING__"


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


def _load_scope_rules(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    data = _load_json(path)
    rules = data.get("rules", {})
    if not isinstance(rules, dict):
        return {}
    return rules


def _write_scope_rules(path: Path, rules: Dict[str, Dict[str, Any]]) -> None:
    payload = {
        "schema_version": "1.0",
        "rule_family": "formal_scope_rules",
        "description": "Formal scope applicability rules for financial standardization.",
        "rules": {k: rules[k] for k in sorted(rules)},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _snapshot_hashes() -> Dict[str, str]:
    return {
        "01": _sha256(_find_delivery_file("01_*.xlsx")),
        "02": _sha256(_find_delivery_file("02_*.xlsx")),
        "02A": _sha256(_find_delivery_file("02A_*.xlsx")),
        "05": _sha256(_find_delivery_file("05_*.xlsx")),
        "06": _sha256(_find_delivery_file("06_*.xlsx")),
        "02B": _sha256(OFFICIAL_02B_PATH),
        "formal_mapping_rules": _sha256_or_missing(FORMAL_SCOPE_RULE_FILE),
        "formal_normalization_rules": _sha256(FORMAL_NORMALIZATION_RULE_FILE),
    }


def _load_inputs() -> Dict[str, Any]:
    for p in [STAGE4G_APPROVAL_XLSX, STAGE4G_SUMMARY_JSON, STAGE4F_SUMMARY_JSON, STAGE4E_SCOPE_DRAFT_XLSX, OFFICIAL_02B_PATH]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")
    approval_xls = pd.ExcelFile(STAGE4G_APPROVAL_XLSX)
    approval_df = pd.read_excel(STAGE4G_APPROVAL_XLSX, sheet_name=approval_xls.sheet_names[0]).fillna("")
    scope_draft_df = pd.read_excel(STAGE4E_SCOPE_DRAFT_XLSX, sheet_name="stage4e_scope_fix_draft").fillna("")
    stage4g_summary = _load_json(STAGE4G_SUMMARY_JSON)
    stage4f_summary = _load_json(STAGE4F_SUMMARY_JSON)
    scope_rules_before = _load_scope_rules(FORMAL_SCOPE_RULE_FILE)
    return {
        "approval_df": approval_df,
        "scope_draft_df": scope_draft_df,
        "stage4g_summary": stage4g_summary,
        "stage4f_summary": stage4f_summary,
        "scope_rules_before": scope_rules_before,
    }


def _validate_gates(stage4g_summary: Dict[str, Any], stage4f_summary: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not bool(stage4g_summary.get("stage4g_scope_promotion_approval_ready", False)):
        errors.append("stage4g_scope_promotion_approval_ready must be true")
    if int(stage4g_summary.get("input_ready_scope_fix_count", -1)) != 15:
        errors.append("input_ready_scope_fix_count must be 15")
    if int(stage4g_summary.get("approved_for_formal_scope_promotion_count", -1)) != 15:
        errors.append("approved_for_formal_scope_promotion_count must be 15")
    if int(stage4g_summary.get("need_manual_approval_count", -1)) != 0:
        errors.append("need_manual_approval_count must be 0")
    if int(stage4g_summary.get("reject_scope_promotion_count", -1)) != 0:
        errors.append("reject_scope_promotion_count must be 0")
    if int(stage4g_summary.get("conflict_after_draft_count", -1)) != 0:
        errors.append("conflict_after_draft_count must be 0")
    if int(stage4g_summary.get("duplicate_after_draft_count", -1)) != 0:
        errors.append("duplicate_after_draft_count must be 0")

    if not bool(stage4f_summary.get("stage4f_dry_run_validation_pass", False)):
        errors.append("stage4f_dry_run_validation_pass must be true")
    if int(stage4f_summary.get("ready_for_formal_scope_promotion_count", -1)) != 15:
        errors.append("ready_for_formal_scope_promotion_count must be 15")
    if int(stage4f_summary.get("ready_for_formal_normalization_promotion_count", -1)) != 0:
        errors.append("ready_for_formal_normalization_promotion_count must be 0")
    if int(stage4f_summary.get("conflict_after_draft_count", -1)) != 0:
        errors.append("stage4f conflict_after_draft_count must be 0")
    if int(stage4f_summary.get("duplicate_after_draft_count", -1)) != 0:
        errors.append("stage4f duplicate_after_draft_count must be 0")
    return errors


def _prepare_rule_index(scope_rules: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = {}
    for rule_id, payload in scope_rules.items():
        if not _norm(rule_id):
            continue
        data = deepcopy(payload)
        scopes = data.get("scope_applicability", [])
        if not isinstance(scopes, list):
            scopes = []
        data["scope_applicability"] = [s for s in [_norm(x) for x in scopes] if s]
        data.setdefault("promoted_scope_fix_ids", [])
        data.setdefault("promoted_issue_ids", [])
        data.setdefault("asset_packages", [])
        data.setdefault("statement_types", [])
        data.setdefault("existing_scope", data["scope_applicability"][0] if data["scope_applicability"] else BASE_SCOPE)
        data.setdefault("standard_metric", "")
        data.setdefault("existing_rule_id", rule_id)
        idx[rule_id] = data
    return idx


def _append_unique(seq: List[str], value: str) -> List[str]:
    value = _norm(value)
    if value and value not in seq:
        seq.append(value)
    return seq


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage4H promote approved scope fixes into formal scope rules.")
    parser.parse_args()

    inputs = _load_inputs()
    errors = _validate_gates(inputs["stage4g_summary"], inputs["stage4f_summary"])
    if errors:
        raise RuntimeError("Stage4H gate validation failed: " + "; ".join(errors))

    approval_df: pd.DataFrame = inputs["approval_df"]
    scope_draft_df: pd.DataFrame = inputs["scope_draft_df"]
    scope_rules_before: Dict[str, Dict[str, Any]] = inputs["scope_rules_before"]

    snapshot_before = _snapshot_hashes()

    # Read boundary production inputs without modifying them.
    _ = pd.read_excel(_find_delivery_file("01_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("02_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("02A_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("05_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("06_*.xlsx")).fillna("")
    _ = pd.read_excel(OFFICIAL_02B_PATH).fillna("")

    approval_approved = approval_df[approval_df["approval_decision"].map(_norm) == APPROVED_DECISION].copy()
    approved_scope_fix_count = int(len(approval_approved))

    draft_by_fix_id = {
        _norm(r["draft_fix_id"]): r
        for _, r in scope_draft_df.iterrows()
        if _norm(r.get("draft_fix_id"))
    }

    rule_index = _prepare_rule_index(scope_rules_before)
    rule_before = deepcopy(rule_index)

    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    if FORMAL_SCOPE_RULE_FILE.exists():
        shutil.copy2(FORMAL_SCOPE_RULE_FILE, BACKUP_PATH)
        backup_file_exists = True
    else:
        _write_scope_rules(BACKUP_PATH, rule_index)
        backup_file_exists = True

    promoted_rows: List[Dict[str, Any]] = []
    duplicate_scope_count = 0
    conflict_rule_count = 0
    missing_rule_id_count = 0
    missing_required_field_count = 0
    promoted_scope_fix_count = 0
    seen_promoted_fix_ids: set[str] = set()

    for _, a in approval_approved.iterrows():
        draft_fix_id = _norm(a.get("draft_fix_id"))
        issue_id = _norm(a.get("issue_id"))
        existing_rule_id = _norm(a.get("existing_rule_id"))
        existing_rule_scope = _norm(a.get("existing_rule_scope"))
        proposed_scope = _norm(a.get("proposed_scope"))
        asset_package = _norm(a.get("asset_package"))
        statement_type = _norm(a.get("statement_type"))
        raw_metric_name = _norm(a.get("raw_metric_name"))
        target_standard_metric = _norm(a.get("target_standard_metric"))
        approval_decision = _norm(a.get("approval_decision"))

        draft_row = draft_by_fix_id.get(draft_fix_id, {})
        required_missing = [x for x in [draft_fix_id, issue_id, existing_rule_id, proposed_scope, asset_package, statement_type, raw_metric_name, target_standard_metric] if not x]
        if required_missing:
            missing_required_field_count += 1
            promoted_rows.append(
                {
                    "draft_fix_id": draft_fix_id,
                    "issue_id": issue_id,
                    "existing_rule_id": existing_rule_id,
                    "existing_rule_scope": existing_rule_scope,
                    "proposed_scope": proposed_scope,
                    "asset_package": asset_package,
                    "statement_type": statement_type,
                    "raw_metric_name": raw_metric_name,
                    "target_standard_metric": target_standard_metric,
                    "approval_decision": approval_decision,
                    "before_scope_applicability": "",
                    "after_scope_applicability": "",
                    "promotion_result": "REJECTED_MISSING_REQUIRED_FIELD",
                    "promotion_reason": "required field missing in approved scope fix",
                }
            )
            continue

        if draft_fix_id in seen_promoted_fix_ids:
            duplicate_scope_count += 1
            promoted_rows.append(
                {
                    "draft_fix_id": draft_fix_id,
                    "issue_id": issue_id,
                    "existing_rule_id": existing_rule_id,
                    "existing_rule_scope": existing_rule_scope,
                    "proposed_scope": proposed_scope,
                    "asset_package": asset_package,
                    "statement_type": statement_type,
                    "raw_metric_name": raw_metric_name,
                    "target_standard_metric": target_standard_metric,
                    "approval_decision": approval_decision,
                    "before_scope_applicability": "",
                    "after_scope_applicability": "",
                    "promotion_result": "DUPLICATE_APPROVED_FIX",
                    "promotion_reason": "approved scope fix already promoted in this run",
                }
            )
            continue

        rule = rule_index.get(existing_rule_id)
        if rule is None:
            missing_rule_id_count += 1
            conflict_rule_count += 1
            promoted_rows.append(
                {
                    "draft_fix_id": draft_fix_id,
                    "issue_id": issue_id,
                    "existing_rule_id": existing_rule_id,
                    "existing_rule_scope": existing_rule_scope,
                    "proposed_scope": proposed_scope,
                    "asset_package": asset_package,
                    "statement_type": statement_type,
                    "raw_metric_name": raw_metric_name,
                    "target_standard_metric": target_standard_metric,
                    "approval_decision": approval_decision,
                    "before_scope_applicability": "",
                    "after_scope_applicability": "",
                    "promotion_result": "CONFLICT_MISSING_RULE_ID",
                    "promotion_reason": "existing rule id not found in formal scope rules",
                }
            )
            continue

        before_scopes = list(rule.get("scope_applicability", []))
        after_scopes = before_scopes
        if proposed_scope not in after_scopes:
            after_scopes = before_scopes + [proposed_scope]
        rule["scope_applicability"] = after_scopes
        rule["promoted_scope_fix_ids"] = _append_unique(list(rule.get("promoted_scope_fix_ids", [])), draft_fix_id)
        rule["promoted_issue_ids"] = _append_unique(list(rule.get("promoted_issue_ids", [])), issue_id)
        rule["asset_packages"] = _append_unique(list(rule.get("asset_packages", [])), asset_package)
        rule["statement_types"] = _append_unique(list(rule.get("statement_types", [])), statement_type)
        rule["standard_metric"] = target_standard_metric or rule.get("standard_metric", "")
        rule["existing_scope"] = rule.get("existing_scope") or existing_rule_scope or BASE_SCOPE
        rule["promotion_status"] = "PROMOTED_STAGE4H"
        rule_index[existing_rule_id] = rule
        promoted_scope_fix_count += 1
        seen_promoted_fix_ids.add(draft_fix_id)
        promoted_rows.append(
            {
                "draft_fix_id": draft_fix_id,
                "issue_id": issue_id,
                "existing_rule_id": existing_rule_id,
                "existing_rule_scope": existing_rule_scope,
                "proposed_scope": proposed_scope,
                "asset_package": asset_package,
                "statement_type": statement_type,
                "raw_metric_name": raw_metric_name,
                "target_standard_metric": target_standard_metric,
                "approval_decision": approval_decision,
                "before_scope_applicability": "|".join(before_scopes),
                "after_scope_applicability": "|".join(after_scopes),
                "promotion_result": "PROMOTED",
                "promotion_reason": "approved scope fix promoted into formal scope rules",
            }
        )

    _write_scope_rules(FORMAL_SCOPE_RULE_FILE, rule_index)

    snapshot_after = _snapshot_hashes()
    formal_mapping_rules_changed = snapshot_before["formal_mapping_rules"] != snapshot_after["formal_mapping_rules"]
    formal_normalization_rules_unchanged = snapshot_before["formal_normalization_rules"] == snapshot_after["formal_normalization_rules"]
    production_01_unchanged = snapshot_before["01"] == snapshot_after["01"]
    production_02_unchanged = snapshot_before["02"] == snapshot_after["02"]
    production_02A_unchanged = snapshot_before["02A"] == snapshot_after["02A"]
    production_05_unchanged = snapshot_before["05"] == snapshot_after["05"]
    production_06_unchanged = snapshot_before["06"] == snapshot_after["06"]
    official_02B_unchanged = snapshot_before["02B"] == snapshot_after["02B"]
    backup_file_exists = BACKUP_PATH.exists()
    rollback_possible = backup_file_exists and BACKUP_PATH.stat().st_size > 0
    delivery_status_after = _run_delivery_check().get("overall_status", "UNKNOWN")

    conflict_rule_count = int(conflict_rule_count)
    duplicate_scope_count = int(duplicate_scope_count)
    missing_rule_id_count = int(missing_rule_id_count)
    missing_required_field_count = int(missing_required_field_count)

    summary = {
        "approved_scope_fix_count": int(approved_scope_fix_count),
        "promoted_scope_fix_count": int(promoted_scope_fix_count),
        "formal_mapping_rules_changed": bool(formal_mapping_rules_changed),
        "formal_normalization_rules_unchanged": bool(formal_normalization_rules_unchanged),
        "duplicate_scope_count": int(duplicate_scope_count),
        "conflict_rule_count": int(conflict_rule_count),
        "missing_rule_id_count": int(missing_rule_id_count),
        "missing_required_field_count": int(missing_required_field_count),
        "production_01_unchanged": bool(production_01_unchanged),
        "production_02_unchanged": bool(production_02_unchanged),
        "production_02A_unchanged": bool(production_02A_unchanged),
        "production_05_unchanged": bool(production_05_unchanged),
        "production_06_unchanged": bool(production_06_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "backup_file_exists": bool(backup_file_exists),
        "rollback_possible": bool(rollback_possible),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "delivery_status_after": delivery_status_after,
        "stage4h_scope_promotion_pass": bool(
            approved_scope_fix_count == 15
            and promoted_scope_fix_count == 15
            and formal_mapping_rules_changed
            and formal_normalization_rules_unchanged
            and duplicate_scope_count == 0
            and conflict_rule_count == 0
            and missing_rule_id_count == 0
            and missing_required_field_count == 0
            and production_01_unchanged
            and production_02_unchanged
            and production_02A_unchanged
            and production_05_unchanged
            and production_06_unchanged
            and official_02B_unchanged
            and backup_file_exists
            and rollback_possible
            and delivery_status_after == "PASS"
        ),
    }

    promoted_df = pd.DataFrame(promoted_rows)
    if not promoted_df.empty:
        promoted_df = promoted_df[
            [
                "draft_fix_id",
                "issue_id",
                "existing_rule_id",
                "existing_rule_scope",
                "proposed_scope",
                "asset_package",
                "statement_type",
                "raw_metric_name",
                "target_standard_metric",
                "approval_decision",
                "before_scope_applicability",
                "after_scope_applicability",
                "promotion_result",
                "promotion_reason",
            ]
        ].copy()

    summary_df = pd.DataFrame(
        [
            ["approved_scope_fix_count", summary["approved_scope_fix_count"]],
            ["promoted_scope_fix_count", summary["promoted_scope_fix_count"]],
            ["formal_mapping_rules_changed", summary["formal_mapping_rules_changed"]],
            ["formal_normalization_rules_unchanged", summary["formal_normalization_rules_unchanged"]],
            ["duplicate_scope_count", summary["duplicate_scope_count"]],
            ["conflict_rule_count", summary["conflict_rule_count"]],
            ["missing_rule_id_count", summary["missing_rule_id_count"]],
            ["missing_required_field_count", summary["missing_required_field_count"]],
            ["backup_file_exists", summary["backup_file_exists"]],
            ["rollback_possible", summary["rollback_possible"]],
            ["delivery_status_after", summary["delivery_status_after"]],
            ["stage4h_scope_promotion_pass", summary["stage4h_scope_promotion_pass"]],
        ],
        columns=["metric", "value"],
    )

    md_lines = [
        "# Stage4H Scope Promotion Log",
        "",
        f"- approved_scope_fix_count: {summary['approved_scope_fix_count']}",
        f"- promoted_scope_fix_count: {summary['promoted_scope_fix_count']}",
        f"- formal_mapping_rules_changed: {summary['formal_mapping_rules_changed']}",
        f"- formal_normalization_rules_unchanged: {summary['formal_normalization_rules_unchanged']}",
        f"- duplicate_scope_count: {summary['duplicate_scope_count']}",
        f"- conflict_rule_count: {summary['conflict_rule_count']}",
        f"- missing_rule_id_count: {summary['missing_rule_id_count']}",
        f"- missing_required_field_count: {summary['missing_required_field_count']}",
        f"- backup_file_exists: {summary['backup_file_exists']}",
        f"- rollback_possible: {summary['rollback_possible']}",
        f"- delivery_status_after: {summary['delivery_status_after']}",
        f"- stage4h_scope_promotion_pass: {summary['stage4h_scope_promotion_pass']}",
        "",
        "## Promoted Rules",
        "",
    ]
    for rid in sorted(rule_index):
        scopes = rule_index[rid].get("scope_applicability", [])
        md_lines.append(f"- {rid}: {'|'.join(scopes)}")

    _safe_write_excel_multi({"stage4h_scope_promotion_log": promoted_df, "summary": summary_df}, OUT_XLSX)
    _safe_write_text("\n".join(md_lines), OUT_MD)
    _safe_write_text(json.dumps(summary, ensure_ascii=False, indent=2), OUT_JSON)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
