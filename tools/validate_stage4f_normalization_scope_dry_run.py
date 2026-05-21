import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

STAGE4E_NORM_DRAFT_XLSX = BASE_DIR / "data" / "mapping" / "drafts" / "stage4e_normalization_fix_draft.xlsx"
STAGE4E_SCOPE_DRAFT_XLSX = BASE_DIR / "data" / "mapping" / "drafts" / "stage4e_scope_fix_draft.xlsx"
STAGE4E_REPORT_XLSX = OUTPUT_DIR / "stage4e_normalization_scope_fix_draft" / "113_stage4e_normalization_scope_fix_draft.xlsx"
STAGE4E_SUMMARY_JSON = OUTPUT_DIR / "stage4e_normalization_scope_fix_draft" / "114_stage4e_normalization_scope_fix_summary.json"
STAGE4D_XLSX = OUTPUT_DIR / "stage4d_mapping_rule_validation" / "111_stage4d_mapping_rule_validation.xlsx"
STAGE4D_SUMMARY_JSON = OUTPUT_DIR / "stage4d_mapping_rule_validation" / "112_stage4d_mapping_rule_validation_summary.json"
STAGE4A_XLSX = OUTPUT_DIR / "stage4a_structured_inventory" / "105_stage4a_structured_layer_inventory.xlsx"
STAGE4B_XLSX = OUTPUT_DIR / "stage4b_mapping_gap_classification" / "107_stage4b_mapping_gap_classification.xlsx"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_MAPPING_RULE_FILE = BASE_DIR / "financial_standardizer.py"

OUT_DIR = OUTPUT_DIR / "stage4f_dry_run_validate_fixes"
OUT_XLSX = OUT_DIR / "115_stage4f_dry_run_validate_fixes.xlsx"
OUT_MD = OUT_DIR / "115_stage4f_dry_run_validate_fixes.md"
OUT_JSON = OUT_DIR / "116_stage4f_dry_run_validate_fixes_summary.json"


STATUS_MATCHED_AFTER_DRAFT_NORMALIZATION = "MATCHED_AFTER_DRAFT_NORMALIZATION"
STATUS_MATCHED_AFTER_DRAFT_SCOPE_FIX = "MATCHED_AFTER_DRAFT_SCOPE_FIX"
STATUS_STILL_NOT_MATCHED = "STILL_NOT_MATCHED"
STATUS_NEED_MANUAL_OVERLAP_REVIEW = "NEED_MANUAL_OVERLAP_REVIEW"
STATUS_FALSE_POSITIVE_CONFIRMED = "FALSE_POSITIVE_CONFIRMED"
STATUS_DRAFT_FIX_NOT_APPLICABLE = "DRAFT_FIX_NOT_APPLICABLE"

ALLOWED_DRY_RUN_STATUS = {
    STATUS_MATCHED_AFTER_DRAFT_NORMALIZATION,
    STATUS_MATCHED_AFTER_DRAFT_SCOPE_FIX,
    STATUS_STILL_NOT_MATCHED,
    STATUS_NEED_MANUAL_OVERLAP_REVIEW,
    STATUS_FALSE_POSITIVE_CONFIRMED,
    STATUS_DRAFT_FIX_NOT_APPLICABLE,
}

ACTION_READY_FOR_FORMAL_NORMALIZATION_PROMOTION = "READY_FOR_FORMAL_NORMALIZATION_PROMOTION"
ACTION_READY_FOR_FORMAL_SCOPE_PROMOTION = "READY_FOR_FORMAL_SCOPE_PROMOTION"
ACTION_NEED_MANUAL_OVERLAP_REVIEW = "NEED_MANUAL_OVERLAP_REVIEW"
ACTION_REJECT_DRAFT_FIX = "REJECT_DRAFT_FIX"
ACTION_KEEP_AS_WARNING = "KEEP_AS_WARNING"
ACTION_NEED_ADDITIONAL_RULE_ANALYSIS = "NEED_ADDITIONAL_RULE_ANALYSIS"

ALLOWED_ACTIONS = {
    ACTION_READY_FOR_FORMAL_NORMALIZATION_PROMOTION,
    ACTION_READY_FOR_FORMAL_SCOPE_PROMOTION,
    ACTION_NEED_MANUAL_OVERLAP_REVIEW,
    ACTION_REJECT_DRAFT_FIX,
    ACTION_KEEP_AS_WARNING,
    ACTION_NEED_ADDITIONAL_RULE_ANALYSIS,
}


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


def _load_formal_module() -> Any:
    spec = importlib.util.spec_from_file_location("financial_standardizer", FORMAL_MAPPING_RULE_FILE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _compact_text(mod: Any, text: str) -> str:
    return _norm(mod._compact_text(text))  # type: ignore[attr-defined]


def _match_standard_metric(mod: Any, label: str) -> Tuple[str, str]:
    fn = getattr(mod, "_match_standard_metric")
    out = fn(label)
    if not out:
        return "", ""
    return _norm(out.get("standard_metric")), _norm(out.get("match_method"))


def _build_scope_index(scope_df: pd.DataFrame) -> Dict[str, List[Dict[str, str]]]:
    index: Dict[str, List[Dict[str, str]]] = {}
    if scope_df.empty:
        return index
    for _, r in scope_df.iterrows():
        rule_id = _norm(r.get("existing_rule_id"))
        if not rule_id:
            continue
        index.setdefault(rule_id, []).append(
            {
                "draft_fix_id": _norm(r.get("draft_fix_id")),
                "issue_id": _norm(r.get("issue_id")),
                "asset_package": _norm(r.get("asset_package")),
                "statement_type": _norm(r.get("statement_type")),
                "target_standard_metric": _norm(r.get("target_standard_metric")),
                "proposed_scope": _norm(r.get("proposed_scope")),
                "fix_type": _norm(r.get("fix_type")),
            }
        )
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage4F dry-run validate normalization/scope fix drafts.")
    parser.parse_args()

    for p in [
        STAGE4E_NORM_DRAFT_XLSX,
        STAGE4E_SCOPE_DRAFT_XLSX,
        STAGE4E_REPORT_XLSX,
        STAGE4E_SUMMARY_JSON,
        STAGE4D_XLSX,
        STAGE4D_SUMMARY_JSON,
        STAGE4A_XLSX,
        STAGE4B_XLSX,
        FORMAL_MAPPING_RULE_FILE,
        OFFICIAL_02B_PATH,
    ]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    snapshot_before = _snapshot_hashes()

    # Boundary reads for read-only compliance.
    _ = pd.read_excel(_find_delivery_file("01_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("02_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("02A_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("05_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("06_*.xlsx")).fillna("")
    _ = pd.read_excel(OFFICIAL_02B_PATH).fillna("")

    stage4e_summary = json.loads(STAGE4E_SUMMARY_JSON.read_text(encoding="utf-8"))
    stage4d_summary = json.loads(STAGE4D_SUMMARY_JSON.read_text(encoding="utf-8"))
    if not bool(stage4e_summary.get("stage4e_fix_draft_ready", False)):
        raise RuntimeError("Stage4E summary indicates not ready; abort Stage4F.")
    if not bool(stage4d_summary.get("stage4d_validation_pass", False)):
        raise RuntimeError("Stage4D summary indicates not pass; abort Stage4F.")

    norm_df = pd.read_excel(STAGE4E_NORM_DRAFT_XLSX, sheet_name="stage4e_normalization_fix_draft").fillna("")
    scope_df = pd.read_excel(STAGE4E_SCOPE_DRAFT_XLSX, sheet_name="stage4e_scope_fix_draft").fillna("")
    stage4e_review_df = pd.read_excel(STAGE4E_REPORT_XLSX, sheet_name="stage4e_review").fillna("")
    stage4d_df = pd.read_excel(STAGE4D_XLSX, sheet_name="stage4d_validation").fillna("")
    stage4b_df = pd.read_excel(STAGE4B_XLSX, sheet_name="stage4b_classification").fillna("")
    _ = pd.read_excel(STAGE4A_XLSX, sheet_name="stage4a_inventory").fillna("")

    stage4e_action_by_issue = {
        _norm(r["issue_id"]): _norm(r.get("recommended_stage4e_action"))
        for _, r in stage4e_review_df.iterrows()
        if _norm(r.get("issue_id"))
    }
    stage4b_by_issue = {
        _norm(r["issue_id"]): r
        for _, r in stage4b_df.iterrows()
        if _norm(r.get("issue_id"))
    }

    # Load formal module and copy aliases for dry-run.
    mod_base = _load_formal_module()
    mod_draft = _load_formal_module()
    base_aliases: Dict[str, List[str]] = copy.deepcopy(getattr(mod_base, "STANDARD_METRIC_ALIASES", {}))
    draft_aliases: Dict[str, List[str]] = copy.deepcopy(base_aliases)

    alias_to_standards: Dict[str, Set[str]] = {}
    for std_metric, alias_list in draft_aliases.items():
        for alias in alias_list:
            c = _compact_text(mod_base, _norm(alias))
            if not c:
                continue
            alias_to_standards.setdefault(c, set()).add(_norm(std_metric))

    # Simulate applying normalization drafts to alias map (in-memory only).
    norm_conflict_draft_ids: Set[str] = set()
    norm_duplicate_draft_ids: Set[str] = set()
    applied_norm_rows: List[Dict[str, str]] = []
    for _, r in norm_df.iterrows():
        draft_fix_id = _norm(r.get("draft_fix_id"))
        raw_metric_name = _norm(r.get("raw_metric_name"))
        proposed_alias = _norm(r.get("proposed_alias"))
        target_std = _norm(r.get("target_standard_metric"))

        if not draft_fix_id or not proposed_alias or not target_std:
            norm_conflict_draft_ids.add(draft_fix_id or f"missing:{raw_metric_name}")
            continue

        c = _compact_text(mod_base, proposed_alias)
        std_set = alias_to_standards.get(c, set())
        if std_set and target_std not in std_set:
            norm_conflict_draft_ids.add(draft_fix_id)
            continue
        if target_std in std_set:
            norm_duplicate_draft_ids.add(draft_fix_id)
            applied_norm_rows.append(
                {
                    "draft_fix_id": draft_fix_id,
                    "raw_metric_name": raw_metric_name,
                    "proposed_alias": proposed_alias,
                    "target_standard_metric": target_std,
                    "apply_result": "ALREADY_EXISTS_SAME_MAPPING",
                }
            )
            continue

        draft_aliases.setdefault(target_std, []).append(proposed_alias)
        alias_to_standards.setdefault(c, set()).add(target_std)
        applied_norm_rows.append(
            {
                "draft_fix_id": draft_fix_id,
                "raw_metric_name": raw_metric_name,
                "proposed_alias": proposed_alias,
                "target_standard_metric": target_std,
                "apply_result": "ADDED_IN_MEMORY",
            }
        )

    setattr(mod_draft, "STANDARD_METRIC_ALIASES", draft_aliases)

    # Scope draft validation for conflicts/duplicates.
    scope_conflict_draft_ids: Set[str] = set()
    scope_duplicate_draft_ids: Set[str] = set()
    scope_key_seen: Set[str] = set()
    scope_rule_scopes: Dict[str, Set[str]] = {}
    for _, r in scope_df.iterrows():
        draft_fix_id = _norm(r.get("draft_fix_id"))
        issue_id = _norm(r.get("issue_id"))
        existing_rule_id = _norm(r.get("existing_rule_id"))
        proposed_scope = _norm(r.get("proposed_scope"))
        fix_type = _norm(r.get("fix_type"))
        k = "|".join([issue_id, existing_rule_id, proposed_scope, fix_type])
        if k in scope_key_seen:
            scope_duplicate_draft_ids.add(draft_fix_id)
            continue
        scope_key_seen.add(k)

        if existing_rule_id:
            scope_rule_scopes.setdefault(existing_rule_id, set()).add(proposed_scope)

    for _, r in scope_df.iterrows():
        draft_fix_id = _norm(r.get("draft_fix_id"))
        existing_rule_id = _norm(r.get("existing_rule_id"))
        if not existing_rule_id:
            scope_conflict_draft_ids.add(draft_fix_id)
            continue
        if len(scope_rule_scopes.get(existing_rule_id, set())) > 1:
            scope_conflict_draft_ids.add(draft_fix_id)

    scope_index = _build_scope_index(scope_df)
    norm_by_issue = { _norm(r["issue_id"]): r for _, r in norm_df.iterrows() if _norm(r.get("issue_id")) }
    scope_by_issue = { _norm(r["issue_id"]): r for _, r in scope_df.iterrows() if _norm(r.get("issue_id")) }

    # Allow one normalization draft to cover same raw+std pattern across years/assets in dry-run.
    norm_pattern_index: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for _, r in norm_df.iterrows():
        raw = _norm(r.get("raw_metric_name"))
        std = _norm(r.get("target_standard_metric"))
        if raw and std and (raw, std) not in norm_pattern_index:
            norm_pattern_index[(raw, std)] = r

    detail_rows: List[Dict[str, Any]] = []
    conflict_after_draft_count = 0
    duplicate_after_draft_count = 0

    for _, r in stage4d_df.iterrows():
        issue_id = _norm(r.get("issue_id"))
        raw_metric_name = _norm(r.get("raw_metric_name"))
        asset_package = _norm(r.get("asset_package"))
        year = _norm(r.get("year"))
        existing_rule_id = _norm(r.get("matched_existing_rule_id"))
        original_reason = _norm(r.get("non_effective_reason"))
        target_std = _norm(r.get("proposed_standard_metric"))
        stage4e_action = stage4e_action_by_issue.get(issue_id, "")

        b = stage4b_by_issue.get(issue_id, {})
        affects_05 = bool(b.get("affects_05", False))
        affects_01 = bool(b.get("affects_01", False))
        affects_06 = bool(b.get("affects_06", False))

        applied_draft_fix_id = ""
        draft_fix_type = ""
        dry_run_status = STATUS_STILL_NOT_MATCHED
        matched_std_after = ""
        conflict_after = False
        duplicate_after = False
        recommended_action = ACTION_NEED_ADDITIONAL_RULE_ANALYSIS
        risk_level = "MEDIUM"
        action_reason = ""

        # Baseline and draft matching using formal matcher.
        base_std, _ = _match_standard_metric(mod_base, raw_metric_name)
        draft_std, _ = _match_standard_metric(mod_draft, raw_metric_name)

        if stage4e_action == "MARK_AS_FALSE_POSITIVE" or original_reason == "INVENTORY_FALSE_POSITIVE":
            dry_run_status = STATUS_FALSE_POSITIVE_CONFIRMED
            matched_std_after = draft_std or base_std
            recommended_action = ACTION_KEEP_AS_WARNING
            risk_level = "LOW"
            action_reason = "confirmed false-positive category from Stage4D/Stage4E; keep as warning"
        elif stage4e_action == "NEED_MANUAL_OVERLAP_REVIEW":
            dry_run_status = STATUS_NEED_MANUAL_OVERLAP_REVIEW
            matched_std_after = draft_std or base_std
            recommended_action = ACTION_NEED_MANUAL_OVERLAP_REVIEW
            risk_level = "HIGH"
            action_reason = "overlap unresolved; manual review required before promotion"
        elif stage4e_action == "DRAFT_NORMALIZATION_FIX":
            row_norm = norm_by_issue.get(issue_id)
            if row_norm is None:
                row_norm = norm_pattern_index.get((raw_metric_name, target_std))
            if row_norm is not None:
                applied_draft_fix_id = _norm(row_norm.get("draft_fix_id"))
                draft_fix_type = _norm(row_norm.get("fix_type"))
                if applied_draft_fix_id in norm_conflict_draft_ids:
                    conflict_after = True
                    dry_run_status = STATUS_DRAFT_FIX_NOT_APPLICABLE
                    recommended_action = ACTION_REJECT_DRAFT_FIX
                    risk_level = "HIGH"
                    action_reason = "normalization draft conflicts with existing alias-standard mapping"
                elif applied_draft_fix_id in norm_duplicate_draft_ids and issue_id == _norm(row_norm.get("issue_id")):
                    # Exact draft issue is duplicate to existing formal alias; keep for additional analysis.
                    duplicate_after = False
                    dry_run_status = STATUS_DRAFT_FIX_NOT_APPLICABLE
                    recommended_action = ACTION_NEED_ADDITIONAL_RULE_ANALYSIS
                    risk_level = "MEDIUM"
                    action_reason = "draft alias already exists in formal rules; no incremental effect in dry-run"
                else:
                    matched_std_after = draft_std
                    if draft_std == target_std:
                        dry_run_status = STATUS_MATCHED_AFTER_DRAFT_NORMALIZATION
                        recommended_action = ACTION_READY_FOR_FORMAL_NORMALIZATION_PROMOTION
                        risk_level = "LOW"
                        action_reason = "draft normalization enables/maintains expected standard metric match in dry-run"
                    else:
                        dry_run_status = STATUS_STILL_NOT_MATCHED
                        recommended_action = ACTION_NEED_ADDITIONAL_RULE_ANALYSIS
                        risk_level = "MEDIUM"
                        action_reason = "normalization draft loaded but expected standard metric still not matched"
            else:
                dry_run_status = STATUS_DRAFT_FIX_NOT_APPLICABLE
                recommended_action = ACTION_NEED_ADDITIONAL_RULE_ANALYSIS
                risk_level = "MEDIUM"
                action_reason = "no applicable normalization draft found for this issue"
        elif stage4e_action == "DRAFT_SCOPE_FIX":
            row_scope = scope_by_issue.get(issue_id)
            if row_scope is None:
                dry_run_status = STATUS_DRAFT_FIX_NOT_APPLICABLE
                recommended_action = ACTION_NEED_ADDITIONAL_RULE_ANALYSIS
                risk_level = "MEDIUM"
                action_reason = "no issue-level scope draft found"
            else:
                applied_draft_fix_id = _norm(row_scope.get("draft_fix_id"))
                draft_fix_type = _norm(row_scope.get("fix_type"))
                matched_std_after = draft_std or base_std
                if applied_draft_fix_id in scope_conflict_draft_ids:
                    conflict_after = True
                    dry_run_status = STATUS_DRAFT_FIX_NOT_APPLICABLE
                    recommended_action = ACTION_REJECT_DRAFT_FIX
                    risk_level = "HIGH"
                    action_reason = "scope draft conflicts with rule-level scope proposals"
                elif applied_draft_fix_id in scope_duplicate_draft_ids:
                    duplicate_after = True
                    dry_run_status = STATUS_DRAFT_FIX_NOT_APPLICABLE
                    recommended_action = ACTION_NEED_ADDITIONAL_RULE_ANALYSIS
                    risk_level = "MEDIUM"
                    action_reason = "duplicate scope draft entry detected for same issue/rule/scope"
                else:
                    candidates = scope_index.get(existing_rule_id, [])
                    applicable = any(
                        _norm(c.get("issue_id")) == issue_id
                        and _norm(c.get("asset_package")) == asset_package
                        and _norm(c.get("target_standard_metric")) == target_std
                        for c in candidates
                    )
                    if applicable:
                        dry_run_status = STATUS_MATCHED_AFTER_DRAFT_SCOPE_FIX
                        recommended_action = ACTION_READY_FOR_FORMAL_SCOPE_PROMOTION
                        risk_level = "LOW"
                        action_reason = "scope draft covers this issue context and is conflict-free in dry-run"
                    else:
                        dry_run_status = STATUS_DRAFT_FIX_NOT_APPLICABLE
                        recommended_action = ACTION_NEED_ADDITIONAL_RULE_ANALYSIS
                        risk_level = "MEDIUM"
                        action_reason = "scope draft exists but not applicable to issue context"
        else:
            dry_run_status = STATUS_DRAFT_FIX_NOT_APPLICABLE
            matched_std_after = draft_std or base_std
            recommended_action = ACTION_NEED_ADDITIONAL_RULE_ANALYSIS
            risk_level = "LOW"
            action_reason = "issue not in Stage4E draft processing set"

        if conflict_after:
            conflict_after_draft_count += 1
        if duplicate_after:
            duplicate_after_draft_count += 1
        if dry_run_status not in ALLOWED_DRY_RUN_STATUS:
            dry_run_status = STATUS_STILL_NOT_MATCHED
        if recommended_action not in ALLOWED_ACTIONS:
            recommended_action = ACTION_NEED_ADDITIONAL_RULE_ANALYSIS

        detail_rows.append(
            {
                "issue_id": issue_id,
                "raw_metric_name": raw_metric_name,
                "asset_package": asset_package,
                "year": year,
                "existing_rule_id": existing_rule_id,
                "original_non_effective_reason": original_reason,
                "applied_draft_fix_id": applied_draft_fix_id,
                "draft_fix_type": draft_fix_type,
                "dry_run_match_status": dry_run_status,
                "matched_standard_metric_after_draft": matched_std_after,
                "conflict_after_draft": bool(conflict_after),
                "duplicate_after_draft": bool(duplicate_after),
                "affects_05": bool(affects_05),
                "affects_01": bool(affects_01),
                "affects_06": bool(affects_06),
                "recommended_stage4f_action": recommended_action,
                "action_reason": action_reason,
                "risk_level": risk_level,
            }
        )

    out_df = pd.DataFrame(detail_rows).sort_values(
        by=["dry_run_match_status", "recommended_stage4f_action", "asset_package", "raw_metric_name", "year"],
        kind="mergesort",
    )

    # Additional safety: if any alias compact maps to multiple standards after draft, mark conflict.
    multi_std_alias_count = int(sum(1 for _, v in alias_to_standards.items() if len(v) > 1))
    if multi_std_alias_count > 0:
        conflict_after_draft_count += multi_std_alias_count

    matched_after_draft_normalization_count = int((out_df["dry_run_match_status"] == STATUS_MATCHED_AFTER_DRAFT_NORMALIZATION).sum())
    matched_after_draft_scope_fix_count = int((out_df["dry_run_match_status"] == STATUS_MATCHED_AFTER_DRAFT_SCOPE_FIX).sum())
    still_not_matched_count = int((out_df["dry_run_match_status"] == STATUS_STILL_NOT_MATCHED).sum())
    manual_overlap_review_count = int((out_df["dry_run_match_status"] == STATUS_NEED_MANUAL_OVERLAP_REVIEW).sum())
    false_positive_confirmed_count = int((out_df["dry_run_match_status"] == STATUS_FALSE_POSITIVE_CONFIRMED).sum())
    draft_fix_not_applicable_count = int((out_df["dry_run_match_status"] == STATUS_DRAFT_FIX_NOT_APPLICABLE).sum())

    ready_for_formal_normalization_promotion_count = int(
        (out_df["recommended_stage4f_action"] == ACTION_READY_FOR_FORMAL_NORMALIZATION_PROMOTION).sum()
    )
    ready_for_formal_scope_promotion_count = int(
        (out_df["recommended_stage4f_action"] == ACTION_READY_FOR_FORMAL_SCOPE_PROMOTION).sum()
    )
    reject_draft_fix_count = int((out_df["recommended_stage4f_action"] == ACTION_REJECT_DRAFT_FIX).sum())

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
        "input_normalization_fix_draft_count": int(len(norm_df)),
        "input_scope_fix_draft_count": int(len(scope_df)),
        "dry_run_issue_count": int(len(out_df)),
        "matched_after_draft_normalization_count": int(matched_after_draft_normalization_count),
        "matched_after_draft_scope_fix_count": int(matched_after_draft_scope_fix_count),
        "still_not_matched_count": int(still_not_matched_count),
        "manual_overlap_review_count": int(manual_overlap_review_count),
        "false_positive_confirmed_count": int(false_positive_confirmed_count),
        "draft_fix_not_applicable_count": int(draft_fix_not_applicable_count),
        "ready_for_formal_normalization_promotion_count": int(ready_for_formal_normalization_promotion_count),
        "ready_for_formal_scope_promotion_count": int(ready_for_formal_scope_promotion_count),
        "reject_draft_fix_count": int(reject_draft_fix_count),
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
        "stage4f_dry_run_validation_pass": bool(
            production_files_unchanged
            and output_06_unchanged
            and official_02B_unchanged
            and formal_mapping_rules_unchanged
            and formal_normalization_rules_unchanged
            and conflict_after_draft_count == 0
            and duplicate_after_draft_count == 0
            and delivery_status_after == "PASS"
        ),
        "delivery_status_after": delivery_status_after,
    }

    action_dist = (
        out_df.groupby("recommended_stage4f_action", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(by=["count", "recommended_stage4f_action"], ascending=[False, True], kind="mergesort")
    )
    status_dist = (
        out_df.groupby("dry_run_match_status", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(by=["count", "dry_run_match_status"], ascending=[False, True], kind="mergesort")
    )

    _safe_write_excel_multi(
        {
            "stage4f_dry_run_validation": out_df,
            "normalization_draft_apply": pd.DataFrame(applied_norm_rows),
            "summary": pd.DataFrame([summary]),
            "status_distribution": status_dist,
            "action_distribution": action_dist,
        },
        OUT_XLSX,
    )

    md_lines = [
        "# Stage4F Dry-Run Validate Normalization and Scope Fixes",
        "",
        "## Summary",
        f"- input_normalization_fix_draft_count: {summary['input_normalization_fix_draft_count']}",
        f"- input_scope_fix_draft_count: {summary['input_scope_fix_draft_count']}",
        f"- dry_run_issue_count: {summary['dry_run_issue_count']}",
        f"- matched_after_draft_normalization_count: {summary['matched_after_draft_normalization_count']}",
        f"- matched_after_draft_scope_fix_count: {summary['matched_after_draft_scope_fix_count']}",
        f"- still_not_matched_count: {summary['still_not_matched_count']}",
        f"- manual_overlap_review_count: {summary['manual_overlap_review_count']}",
        f"- false_positive_confirmed_count: {summary['false_positive_confirmed_count']}",
        f"- draft_fix_not_applicable_count: {summary['draft_fix_not_applicable_count']}",
        f"- ready_for_formal_normalization_promotion_count: {summary['ready_for_formal_normalization_promotion_count']}",
        f"- ready_for_formal_scope_promotion_count: {summary['ready_for_formal_scope_promotion_count']}",
        f"- reject_draft_fix_count: {summary['reject_draft_fix_count']}",
        f"- conflict_after_draft_count: {summary['conflict_after_draft_count']}",
        f"- duplicate_after_draft_count: {summary['duplicate_after_draft_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- output_06_unchanged: {summary['output_06_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- formal_normalization_rules_unchanged: {summary['formal_normalization_rules_unchanged']}",
        f"- delivery_status_after: {summary['delivery_status_after']}",
        f"- stage4f_dry_run_validation_pass: {summary['stage4f_dry_run_validation_pass']}",
    ]
    _safe_write_text("\n".join(md_lines), OUT_MD)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage4f_report_xlsx: {OUT_XLSX}")
    print(f"stage4f_report_md: {OUT_MD}")
    print(f"stage4f_summary_json: {OUT_JSON}")
    for k in [
        "input_normalization_fix_draft_count",
        "input_scope_fix_draft_count",
        "dry_run_issue_count",
        "matched_after_draft_normalization_count",
        "matched_after_draft_scope_fix_count",
        "still_not_matched_count",
        "manual_overlap_review_count",
        "false_positive_confirmed_count",
        "draft_fix_not_applicable_count",
        "ready_for_formal_normalization_promotion_count",
        "ready_for_formal_scope_promotion_count",
        "reject_draft_fix_count",
        "conflict_after_draft_count",
        "duplicate_after_draft_count",
        "production_files_unchanged",
        "output_06_unchanged",
        "official_02B_unchanged",
        "formal_mapping_rules_unchanged",
        "formal_normalization_rules_unchanged",
        "stage4f_dry_run_validation_pass",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

