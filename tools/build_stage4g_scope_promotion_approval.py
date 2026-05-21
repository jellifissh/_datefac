import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

STAGE4F_XLSX = OUTPUT_DIR / "stage4f_dry_run_validate_fixes" / "115_stage4f_dry_run_validate_fixes.xlsx"
STAGE4F_SUMMARY_JSON = OUTPUT_DIR / "stage4f_dry_run_validate_fixes" / "116_stage4f_dry_run_validate_fixes_summary.json"
STAGE4E_SCOPE_XLSX = BASE_DIR / "data" / "mapping" / "drafts" / "stage4e_scope_fix_draft.xlsx"
STAGE4E_NORM_XLSX = BASE_DIR / "data" / "mapping" / "drafts" / "stage4e_normalization_fix_draft.xlsx"
STAGE4E_REPORT_XLSX = OUTPUT_DIR / "stage4e_normalization_scope_fix_draft" / "113_stage4e_normalization_scope_fix_draft.xlsx"
STAGE4D_XLSX = OUTPUT_DIR / "stage4d_mapping_rule_validation" / "111_stage4d_mapping_rule_validation.xlsx"
FORMAL_MAPPING_RULE_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

OUT_DIR = OUTPUT_DIR / "stage4g_scope_promotion_approval"
OUT_XLSX = OUT_DIR / "117_stage4g_scope_promotion_approval.xlsx"
OUT_MD = OUT_DIR / "117_stage4g_scope_promotion_approval.md"
OUT_JSON = OUT_DIR / "118_stage4g_scope_promotion_summary.json"


STAGE4F_READY = "READY_FOR_FORMAL_SCOPE_PROMOTION"
APPROVED = "APPROVED_FOR_FORMAL_SCOPE_PROMOTION"
NEED_MANUAL = "NEED_MANUAL_APPROVAL"
REJECT = "REJECT_SCOPE_PROMOTION"


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
        "formal_mapping_rules": _sha256(FORMAL_MAPPING_RULE_FILE),
        "formal_normalization_rules": _sha256(FORMAL_MAPPING_RULE_FILE),
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage4G build approval package for scope fix promotion.")
    parser.parse_args()

    for p in [
        STAGE4F_XLSX,
        STAGE4F_SUMMARY_JSON,
        STAGE4E_SCOPE_XLSX,
        STAGE4E_NORM_XLSX,
        STAGE4E_REPORT_XLSX,
        STAGE4D_XLSX,
        FORMAL_MAPPING_RULE_FILE,
        OFFICIAL_02B_PATH,
    ]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    snapshot_before = _snapshot_hashes()

    _ = pd.read_excel(_find_delivery_file("01_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("02_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("02A_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("05_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("06_*.xlsx")).fillna("")
    _ = pd.read_excel(OFFICIAL_02B_PATH).fillna("")

    stage4f_summary = json.loads(STAGE4F_SUMMARY_JSON.read_text(encoding="utf-8"))
    if not bool(stage4f_summary.get("stage4f_dry_run_validation_pass", False)):
        raise RuntimeError("Stage4F summary indicates pass=false; abort Stage4G.")

    stage4f_df = pd.read_excel(STAGE4F_XLSX, sheet_name="stage4f_dry_run_validation").fillna("")
    scope_df = pd.read_excel(STAGE4E_SCOPE_XLSX, sheet_name="stage4e_scope_fix_draft").fillna("")
    norm_df = pd.read_excel(STAGE4E_NORM_XLSX, sheet_name="stage4e_normalization_fix_draft").fillna("")
    stage4e_df = pd.read_excel(STAGE4E_REPORT_XLSX, sheet_name="stage4e_review").fillna("")
    stage4d_df = pd.read_excel(STAGE4D_XLSX, sheet_name="stage4d_validation").fillna("")

    stage4f_scope_ready = stage4f_df[stage4f_df["recommended_stage4f_action"].map(_norm) == STAGE4F_READY].copy()
    input_ready_scope_fix_count = int(len(stage4f_scope_ready))

    stage4e_action_by_issue = {
        _norm(r["issue_id"]): _norm(r.get("recommended_stage4e_action"))
        for _, r in stage4e_df.iterrows()
        if _norm(r.get("issue_id"))
    }
    stage4d_status_by_issue = {
        _norm(r["issue_id"]): _norm(r.get("non_effective_reason"))
        for _, r in stage4d_df.iterrows()
        if _norm(r.get("issue_id"))
    }

    norm_scope_issue_ids = set(norm_df["issue_id"].map(_norm).tolist())
    scope_issue_ids = set(scope_df["issue_id"].map(_norm).tolist())

    rows = []
    approved_count = 0
    need_manual_count = 0
    reject_count = 0
    excluded_normalization_fix_count = 0
    excluded_manual_overlap_review_count = 0
    excluded_false_positive_count = 0
    excluded_not_applicable_count = 0
    conflict_after_draft_count = 0
    duplicate_after_draft_count = 0

    for _, r in stage4f_scope_ready.iterrows():
        issue_id = _norm(r.get("issue_id"))
        dry_run_status = _norm(r.get("dry_run_match_status"))
        conflict_after_draft = bool(r.get("conflict_after_draft"))
        duplicate_after_draft = bool(r.get("duplicate_after_draft"))
        stage4e_action = stage4e_action_by_issue.get(issue_id, "")
        original_reason = stage4d_status_by_issue.get(issue_id, "")

        excluded_normalization_fix_count += 0
        approval_decision = NEED_MANUAL
        approval_reason = ""

        if issue_id in norm_scope_issue_ids:
            excluded_normalization_fix_count += 1
            approval_decision = REJECT
            approval_reason = "issue belongs to normalization draft, excluded from scope promotion"
        elif original_reason == "INVENTORY_FALSE_POSITIVE" or stage4e_action == "MARK_AS_FALSE_POSITIVE":
            excluded_false_positive_count += 1
            approval_decision = REJECT
            approval_reason = "false positive"
        elif dry_run_status != "MATCHED_AFTER_DRAFT_SCOPE_FIX":
            excluded_not_applicable_count += 1
            approval_decision = REJECT
            approval_reason = "dry-run did not match after scope fix"
        elif conflict_after_draft:
            conflict_after_draft_count += 1
            approval_decision = REJECT
            approval_reason = "conflict after draft"
        elif duplicate_after_draft:
            duplicate_after_draft_count += 1
            approval_decision = REJECT
            approval_reason = "duplicate after draft"
        else:
            approved_count += 1
            approval_decision = APPROVED
            approval_reason = "dry-run matched after scope fix with no conflict or duplicate"

        if stage4e_action == "NEED_MANUAL_OVERLAP_REVIEW":
            excluded_manual_overlap_review_count += 1
            if approval_decision == APPROVED:
                approval_decision = NEED_MANUAL
                approval_reason = "manual overlap review required"
                approved_count -= 1
                need_manual_count += 1
        if approval_decision == NEED_MANUAL:
            need_manual_count += 1
        elif approval_decision == REJECT:
            reject_count += 1

        rows.append(
            {
                "draft_fix_id": _norm(r.get("applied_draft_fix_id")),
                "issue_id": issue_id,
                "existing_rule_id": _norm(r.get("existing_rule_id")),
                "existing_rule_scope": _norm(scope_df[scope_df["issue_id"].map(_norm) == issue_id].iloc[0].get("existing_rule_scope", "")) if issue_id in scope_issue_ids and not scope_df[scope_df["issue_id"].map(_norm) == issue_id].empty else "",
                "proposed_scope": _norm(scope_df[scope_df["issue_id"].map(_norm) == issue_id].iloc[0].get("proposed_scope", "")) if issue_id in scope_issue_ids and not scope_df[scope_df["issue_id"].map(_norm) == issue_id].empty else "",
                "asset_package": _norm(r.get("asset_package")),
                "statement_type": _norm(scope_df[scope_df["issue_id"].map(_norm) == issue_id].iloc[0].get("statement_type", "")) if issue_id in scope_issue_ids and not scope_df[scope_df["issue_id"].map(_norm) == issue_id].empty else "",
                "raw_metric_name": _norm(r.get("raw_metric_name")),
                "target_standard_metric": _norm(r.get("matched_standard_metric_after_draft")),
                "dry_run_match_status": dry_run_status,
                "conflict_after_draft": bool(conflict_after_draft),
                "duplicate_after_draft": bool(duplicate_after_draft),
                "approval_decision": approval_decision,
                "approval_reason": approval_reason,
            }
        )

    out_columns = [
        "draft_fix_id",
        "issue_id",
        "existing_rule_id",
        "existing_rule_scope",
        "proposed_scope",
        "asset_package",
        "statement_type",
        "raw_metric_name",
        "target_standard_metric",
        "dry_run_match_status",
        "conflict_after_draft",
        "duplicate_after_draft",
        "approval_decision",
        "approval_reason",
    ]
    out_df = pd.DataFrame(rows, columns=out_columns)
    if not out_df.empty:
        out_df = out_df.sort_values(
            by=["approval_decision", "asset_package", "raw_metric_name", "issue_id"],
            kind="mergesort",
        )

    approved_for_formal_scope_promotion_count = int((out_df["approval_decision"] == APPROVED).sum())
    need_manual_approval_count = int((out_df["approval_decision"] == NEED_MANUAL).sum())
    reject_scope_promotion_count = int((out_df["approval_decision"] == REJECT).sum())

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
        "input_ready_scope_fix_count": int(input_ready_scope_fix_count),
        "approved_for_formal_scope_promotion_count": int(approved_for_formal_scope_promotion_count),
        "need_manual_approval_count": int(need_manual_approval_count),
        "reject_scope_promotion_count": int(reject_scope_promotion_count),
        "excluded_normalization_fix_count": int(excluded_normalization_fix_count),
        "excluded_manual_overlap_review_count": int(excluded_manual_overlap_review_count),
        "excluded_false_positive_count": int(excluded_false_positive_count),
        "excluded_not_applicable_count": int(excluded_not_applicable_count),
        "conflict_after_draft_count": int(conflict_after_draft_count),
        "duplicate_after_draft_count": int(duplicate_after_draft_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "formal_normalization_rules_unchanged": bool(formal_normalization_rules_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage4g_scope_promotion_approval_ready": bool(
            input_ready_scope_fix_count == 15
            and approved_for_formal_scope_promotion_count == 15
            and need_manual_approval_count == 0
            and reject_scope_promotion_count == 0
            and conflict_after_draft_count == 0
            and duplicate_after_draft_count == 0
            and production_files_unchanged
            and output_06_unchanged
            and official_02B_unchanged
            and formal_mapping_rules_unchanged
            and formal_normalization_rules_unchanged
            and delivery_status_after == "PASS"
        ),
        "delivery_status_after": delivery_status_after,
    }

    _safe_write_excel_multi(
        {
            "stage4g_scope_promotion_approval": out_df,
            "summary": pd.DataFrame([summary]),
        },
        OUT_XLSX,
    )

    md_lines = [
        "# Stage4G Scope Promotion Approval",
        "",
        "## Summary",
        f"- input_ready_scope_fix_count: {summary['input_ready_scope_fix_count']}",
        f"- approved_for_formal_scope_promotion_count: {summary['approved_for_formal_scope_promotion_count']}",
        f"- need_manual_approval_count: {summary['need_manual_approval_count']}",
        f"- reject_scope_promotion_count: {summary['reject_scope_promotion_count']}",
        f"- excluded_normalization_fix_count: {summary['excluded_normalization_fix_count']}",
        f"- excluded_manual_overlap_review_count: {summary['excluded_manual_overlap_review_count']}",
        f"- excluded_false_positive_count: {summary['excluded_false_positive_count']}",
        f"- excluded_not_applicable_count: {summary['excluded_not_applicable_count']}",
        f"- conflict_after_draft_count: {summary['conflict_after_draft_count']}",
        f"- duplicate_after_draft_count: {summary['duplicate_after_draft_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- output_06_unchanged: {summary['output_06_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- formal_normalization_rules_unchanged: {summary['formal_normalization_rules_unchanged']}",
        f"- delivery_status_after: {summary['delivery_status_after']}",
        f"- stage4g_scope_promotion_approval_ready: {summary['stage4g_scope_promotion_approval_ready']}",
    ]
    _safe_write_text("\n".join(md_lines), OUT_MD)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage4g_report_xlsx: {OUT_XLSX}")
    print(f"stage4g_report_md: {OUT_MD}")
    print(f"stage4g_summary_json: {OUT_JSON}")
    for k in [
        "input_ready_scope_fix_count",
        "approved_for_formal_scope_promotion_count",
        "need_manual_approval_count",
        "reject_scope_promotion_count",
        "excluded_normalization_fix_count",
        "excluded_manual_overlap_review_count",
        "excluded_false_positive_count",
        "excluded_not_applicable_count",
        "conflict_after_draft_count",
        "duplicate_after_draft_count",
        "production_files_unchanged",
        "output_06_unchanged",
        "official_02B_unchanged",
        "formal_mapping_rules_unchanged",
        "formal_normalization_rules_unchanged",
        "stage4g_scope_promotion_approval_ready",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
