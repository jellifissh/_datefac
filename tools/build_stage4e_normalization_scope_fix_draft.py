import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

STAGE4D_XLSX = OUTPUT_DIR / "stage4d_mapping_rule_validation" / "111_stage4d_mapping_rule_validation.xlsx"
STAGE4D_SUMMARY_JSON = OUTPUT_DIR / "stage4d_mapping_rule_validation" / "112_stage4d_mapping_rule_validation_summary.json"
STAGE4B_XLSX = OUTPUT_DIR / "stage4b_mapping_gap_classification" / "107_stage4b_mapping_gap_classification.xlsx"
STAGE4A_XLSX = OUTPUT_DIR / "stage4a_structured_inventory" / "105_stage4a_structured_layer_inventory.xlsx"
FORMAL_MAPPING_RULE_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

DRAFT_DIR = BASE_DIR / "data" / "mapping" / "drafts"
NORM_DRAFT_XLSX = DRAFT_DIR / "stage4e_normalization_fix_draft.xlsx"
SCOPE_DRAFT_XLSX = DRAFT_DIR / "stage4e_scope_fix_draft.xlsx"

OUT_DIR = OUTPUT_DIR / "stage4e_normalization_scope_fix_draft"
OUT_XLSX = OUT_DIR / "113_stage4e_normalization_scope_fix_draft.xlsx"
OUT_MD = OUT_DIR / "113_stage4e_normalization_scope_fix_draft.md"
OUT_JSON = OUT_DIR / "114_stage4e_normalization_scope_fix_summary.json"


REASON_RULE_EXISTS_BUT_NOT_APPLIED = "RULE_EXISTS_BUT_NOT_APPLIED"
REASON_NORMALIZATION_MISMATCH = "NORMALIZATION_MISMATCH"
REASON_SCOPE_MISMATCH = "SCOPE_MISMATCH"
REASON_INVENTORY_FALSE_POSITIVE = "INVENTORY_FALSE_POSITIVE"

ACTION_DRAFT_NORMALIZATION_FIX = "DRAFT_NORMALIZATION_FIX"
ACTION_DRAFT_SCOPE_FIX = "DRAFT_SCOPE_FIX"
ACTION_NEED_MANUAL_OVERLAP_REVIEW = "NEED_MANUAL_OVERLAP_REVIEW"
ACTION_MARK_AS_FALSE_POSITIVE = "MARK_AS_FALSE_POSITIVE"
ACTION_DEFER_TO_MAPPING_RULE_PROMOTION = "DEFER_TO_MAPPING_RULE_PROMOTION"
ACTION_NO_ACTION = "NO_ACTION"

ALLOWED_STAGE4E_ACTIONS = {
    ACTION_DRAFT_NORMALIZATION_FIX,
    ACTION_DRAFT_SCOPE_FIX,
    ACTION_NEED_MANUAL_OVERLAP_REVIEW,
    ACTION_MARK_AS_FALSE_POSITIVE,
    ACTION_DEFER_TO_MAPPING_RULE_PROMOTION,
    ACTION_NO_ACTION,
}

FIX_ADD_METRIC_ALIAS = "ADD_METRIC_ALIAS"
FIX_NORMALIZE_RAW_METRIC_NAME = "NORMALIZE_RAW_METRIC_NAME"
FIX_EXPAND_RULE_SCOPE = "EXPAND_RULE_SCOPE"
FIX_ADD_PACKAGE_SCOPE = "ADD_PACKAGE_SCOPE"
FIX_ADD_STATEMENT_SCOPE = "ADD_STATEMENT_TYPE_SCOPE"
FIX_MARK_FALSE_POSITIVE = "MARK_FALSE_POSITIVE"
FIX_NEED_MANUAL_OVERLAP = "NEED_MANUAL_OVERLAP_REVIEW"

ALLOWED_FIX_TYPES = {
    FIX_ADD_METRIC_ALIAS,
    FIX_NORMALIZE_RAW_METRIC_NAME,
    FIX_EXPAND_RULE_SCOPE,
    FIX_ADD_PACKAGE_SCOPE,
    FIX_ADD_STATEMENT_SCOPE,
    FIX_MARK_FALSE_POSITIVE,
    FIX_NEED_MANUAL_OVERLAP,
}

CONF_HIGH = "HIGH"
CONF_MEDIUM = "MEDIUM"
CONF_LOW = "LOW"
ALLOWED_CONFIDENCE = {CONF_HIGH, CONF_MEDIUM, CONF_LOW}

STATUS_DRAFT_READY = "DRAFT_READY"
STATUS_NEED_MANUAL_REVIEW = "NEED_MANUAL_REVIEW"
STATUS_REJECTED_FALSE_POSITIVE = "REJECTED_FALSE_POSITIVE"
ALLOWED_DRAFT_STATUS = {STATUS_DRAFT_READY, STATUS_NEED_MANUAL_REVIEW, STATUS_REJECTED_FALSE_POSITIVE}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compact_text(value: Any) -> str:
    text = _norm(value)
    text = text.replace("（", "(").replace("）", ")").replace("％", "%")
    text = re.sub(r"\s+", "", text)
    return text.upper()


def _key(asset: Any, metric: Any, year: Any) -> str:
    return "|".join([_norm(asset), _norm(metric), _norm(year)])


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


def _clean_metric_label_noise(label: str) -> str:
    text = _norm(label)
    if not text:
        return ""
    text = text.replace("（", "(").replace("）", ")")
    text = re.sub(r"\s+", " ", text).strip()

    # Remove trailing numeric tokens mixed into row labels, e.g. "每股收益 1.04 1.5"
    text = re.sub(r"(?:\s+[-+]?\d+(?:\.\d+)?[%]?)\s*$", "", text).strip()
    text = re.sub(r"(?:\s+[-+]?\d+(?:\.\d+)?[%]?)+\s*$", "", text).strip()
    return text


def _load_alias_catalog() -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, str]]:
    spec = importlib.util.spec_from_file_location("financial_standardizer", FORMAL_MAPPING_RULE_FILE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    aliases: Dict[str, List[str]] = getattr(mod, "STANDARD_METRIC_ALIASES", {})

    exact_map: Dict[str, Set[str]] = {}
    compact_map: Dict[str, Set[str]] = {}
    exact_to_rule_id: Dict[str, str] = {}

    for std_metric, raw_list in aliases.items():
        std = _norm(std_metric)
        for idx, alias in enumerate(raw_list, start=1):
            a = _norm(alias)
            if not a:
                continue
            rid = f"FS_ALIAS_{_compact_text(std)}_{idx:03d}"
            exact_map.setdefault(a, set()).add(std)
            compact_map.setdefault(_compact_text(a), set()).add(std)
            if a not in exact_to_rule_id:
                exact_to_rule_id[a] = rid
    return exact_map, compact_map, exact_to_rule_id


def _extract_asset_pkg_from_issue(issue_id: str, stage4b_map: Dict[str, Dict[str, Any]], stage4a_map: Dict[str, Dict[str, Any]]) -> str:
    if issue_id in stage4b_map:
        return _norm(stage4b_map[issue_id].get("asset_package"))
    if issue_id in stage4a_map:
        return _norm(stage4a_map[issue_id].get("asset_package"))
    return ""


def _extract_year_from_issue(issue_id: str, stage4b_map: Dict[str, Dict[str, Any]], stage4a_map: Dict[str, Dict[str, Any]]) -> str:
    if issue_id in stage4b_map:
        return _norm(stage4b_map[issue_id].get("year"))
    if issue_id in stage4a_map:
        return _norm(stage4a_map[issue_id].get("year"))
    return ""


def _extract_statement_type_from_asset_05(asset_package: str, standard_metric: str, year: str) -> str:
    # Read-only best effort lookup from per-asset 05 files.
    asset_dir = OUTPUT_DIR / asset_package
    if not asset_dir.exists() or not asset_dir.is_dir():
        return ""
    f05 = asset_dir / "05_核心财务指标标准化.xlsx"
    if not f05.exists():
        return ""
    try:
        xls = pd.ExcelFile(f05)
    except Exception:
        return ""
    if "抽取明细" not in xls.sheet_names:
        return ""
    try:
        df = pd.read_excel(f05, sheet_name="抽取明细").fillna("")
    except Exception:
        return ""
    if df.empty:
        return ""

    metric_col = "标准指标" if "标准指标" in df.columns else ""
    stmt_col = "source_table_type" if "source_table_type" in df.columns else ("statement_type" if "statement_type" in df.columns else "")
    if not metric_col:
        return ""
    if year not in df.columns:
        return ""

    for _, r in df.iterrows():
        if _norm(r.get(metric_col)) != _norm(standard_metric):
            continue
        if not _norm(r.get(year)):
            continue
        if stmt_col:
            return _norm(r.get(stmt_col))
        return ""
    return ""


def _risk_from_action(action: str) -> str:
    if action in {ACTION_NEED_MANUAL_OVERLAP_REVIEW}:
        return "HIGH"
    if action in {ACTION_DRAFT_SCOPE_FIX, ACTION_DRAFT_NORMALIZATION_FIX}:
        return "MEDIUM"
    if action in {ACTION_MARK_AS_FALSE_POSITIVE, ACTION_NO_ACTION, ACTION_DEFER_TO_MAPPING_RULE_PROMOTION}:
        return "LOW"
    return "MEDIUM"


def _confidence_from_action(action: str, priority_hint: str = "") -> str:
    p = _norm(priority_hint).upper()
    if action == ACTION_NEED_MANUAL_OVERLAP_REVIEW:
        return CONF_LOW
    if p == "HIGH":
        return CONF_HIGH
    if p == "LOW":
        return CONF_LOW
    return CONF_MEDIUM


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage4E build normalization/scope fix drafts from Stage4D validation.")
    parser.parse_args()

    for p in [STAGE4D_XLSX, STAGE4D_SUMMARY_JSON, STAGE4B_XLSX, STAGE4A_XLSX, FORMAL_MAPPING_RULE_FILE, OFFICIAL_02B_PATH]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    snapshot_before = _snapshot_hashes()

    # Boundary reads: required layers, read-only.
    _ = pd.read_excel(_find_delivery_file("01_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("02_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("02A_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("05_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("06_*.xlsx")).fillna("")
    _ = pd.read_excel(OFFICIAL_02B_PATH).fillna("")

    stage4d_summary = json.loads(STAGE4D_SUMMARY_JSON.read_text(encoding="utf-8"))
    if not bool(stage4d_summary.get("stage4d_validation_pass", False)):
        raise RuntimeError("Stage4D summary indicates pass=false; abort Stage4E.")

    df4d = pd.read_excel(STAGE4D_XLSX, sheet_name="stage4d_validation").fillna("")
    df4b = pd.read_excel(STAGE4B_XLSX, sheet_name="stage4b_classification").fillna("")
    df4a = pd.read_excel(STAGE4A_XLSX, sheet_name="stage4a_inventory").fillna("")

    stage4b_by_issue = {str(_norm(r["issue_id"])): r for _, r in df4b.iterrows() if _norm(r.get("issue_id"))}
    stage4a_by_issue = {str(_norm(r["issue_id"])): r for _, r in df4a.iterrows() if _norm(r.get("issue_id"))}

    exact_alias_map, compact_alias_map, exact_to_rule_id = _load_alias_catalog()

    target_reasons = {
        REASON_NORMALIZATION_MISMATCH,
        REASON_SCOPE_MISMATCH,
        REASON_RULE_EXISTS_BUT_NOT_APPLIED,
    }

    input_stage4d_issue_count = int(len(df4d))
    normalization_mismatch_input_count = int((df4d["non_effective_reason"].map(_norm) == REASON_NORMALIZATION_MISMATCH).sum())
    scope_mismatch_input_count = int((df4d["non_effective_reason"].map(_norm) == REASON_SCOPE_MISMATCH).sum())
    existing_rule_not_applied_input_count = int((df4d["non_effective_reason"].map(_norm) == REASON_RULE_EXISTS_BUT_NOT_APPLIED).sum())
    possible_overlap_input_count = int((df4d["recommended_stage4d_action"].map(_norm) == "NEED_MANUAL_OVERLAP_REVIEW").sum())

    # Detect ambiguous raw -> multiple standard mappings inside Stage4D actionable set.
    actionable_df = df4d[df4d["non_effective_reason"].map(_norm).isin(target_reasons)].copy()
    raw_to_std: Dict[str, Set[str]] = {}
    for _, r in actionable_df.iterrows():
        raw = _norm(r.get("raw_metric_name"))
        std = _norm(r.get("proposed_standard_metric"))
        if raw and std:
            raw_to_std.setdefault(raw, set()).add(std)

    normalization_rows: List[Dict[str, Any]] = []
    scope_rows: List[Dict[str, Any]] = []
    report_rows: List[Dict[str, Any]] = []
    manual_overlap_rows: List[Dict[str, Any]] = []

    conflict_draft_fix_count = 0
    duplicate_draft_fix_count = 0
    missing_required_field_count = 0
    false_positive_count = 0
    no_action_count = 0

    norm_seen_keys: Set[str] = set()
    scope_seen_keys: Set[str] = set()
    scope_rule_scope_seen: Dict[str, str] = {}
    norm_alias_seen: Dict[str, str] = {}

    norm_seq = 0
    scope_seq = 0

    sorted_df = df4d.sort_values(
        by=["non_effective_reason", "asset_package", "proposed_standard_metric", "year"],
        kind="mergesort",
    )
    for _, r in sorted_df.iterrows():
        issue_id = _norm(r.get("issue_id"))
        raw_metric_name = _norm(r.get("raw_metric_name"))
        proposed_standard_metric = _norm(r.get("proposed_standard_metric"))
        year = _norm(r.get("year")) or _extract_year_from_issue(issue_id, stage4b_by_issue, stage4a_by_issue)
        asset_package = _norm(r.get("asset_package")) or _extract_asset_pkg_from_issue(issue_id, stage4b_by_issue, stage4a_by_issue)
        stage4d_status = _norm(r.get("non_effective_reason"))
        non_effective_reason = stage4d_status
        stage4c_status = _norm(r.get("stage4c_status"))
        matched_existing_rule_id = _norm(r.get("matched_existing_rule_id"))

        b = stage4b_by_issue.get(issue_id, {})
        priority_hint = _norm(b.get("priority", ""))
        source_layer = _norm(b.get("source_layer"))
        target_layer = _norm(b.get("target_layer"))
        current_value = _norm(b.get("current_value"))
        current_unit = _norm(b.get("current_unit"))
        statement_type = _extract_statement_type_from_asset_05(asset_package, proposed_standard_metric, year)
        evidence_source = f"stage4d:{issue_id};stage4b:{_norm(b.get('issue_id'))};source={source_layer};target={target_layer}"

        recommended_action = ACTION_NO_ACTION
        draft_target_file = ""
        draft_fix_id = ""
        action_reason = ""
        risk_level = "LOW"

        is_overlap_manual = _norm(r.get("recommended_stage4d_action")) == "NEED_MANUAL_OVERLAP_REVIEW"
        if stage4d_status == REASON_INVENTORY_FALSE_POSITIVE:
            recommended_action = ACTION_MARK_AS_FALSE_POSITIVE
            action_reason = "flagged as inventory false positive in Stage4D; excluded from draft generation"
            false_positive_count += 1
        elif is_overlap_manual:
            recommended_action = ACTION_NEED_MANUAL_OVERLAP_REVIEW
            action_reason = "possible overlap cannot determine unique coverage; manual overlap review required"
            manual_overlap_rows.append(
                {
                    "issue_id": issue_id,
                    "raw_metric_name": raw_metric_name,
                    "proposed_standard_metric": proposed_standard_metric,
                    "asset_package": asset_package,
                    "year": year,
                    "stage4d_status": stage4d_status,
                    "matched_existing_rule_id": matched_existing_rule_id,
                    "existing_rule_text": _norm(r.get("existing_rule_text / pattern")),
                    "review_reason": action_reason,
                }
            )
        elif stage4d_status == REASON_NORMALIZATION_MISMATCH:
            normalized_raw = _clean_metric_label_noise(raw_metric_name) or raw_metric_name
            ambiguous_raw = len(raw_to_std.get(raw_metric_name, set())) > 1

            if ambiguous_raw:
                recommended_action = ACTION_NEED_MANUAL_OVERLAP_REVIEW
                action_reason = "same raw metric maps to multiple standard metrics; requires manual review"
            else:
                proposed_alias = normalized_raw
                proposed_normalized_metric = normalized_raw

                alias_conflict = False
                existing_std_exact = exact_alias_map.get(proposed_alias, set())
                if existing_std_exact and (proposed_standard_metric not in existing_std_exact):
                    alias_conflict = True
                compact_std = compact_alias_map.get(_compact_text(proposed_normalized_metric), set())
                if compact_std and (proposed_standard_metric not in compact_std):
                    alias_conflict = True

                if alias_conflict:
                    recommended_action = ACTION_NEED_MANUAL_OVERLAP_REVIEW
                    action_reason = "proposed alias conflicts with existing alias-standard mapping"
                    conflict_draft_fix_count += 1
                else:
                    fix_type = FIX_ADD_METRIC_ALIAS if raw_metric_name != normalized_raw else FIX_NORMALIZE_RAW_METRIC_NAME
                    conf = _confidence_from_action(ACTION_DRAFT_NORMALIZATION_FIX, priority_hint=priority_hint)
                    status = STATUS_DRAFT_READY
                    if _norm(raw_metric_name) != _norm(normalized_raw):
                        conf = CONF_HIGH if conf != CONF_LOW else CONF_MEDIUM

                    norm_key = "|".join([raw_metric_name, proposed_standard_metric, asset_package, year, fix_type])
                    alias_key = "|".join([proposed_alias, proposed_standard_metric])
                    if norm_key in norm_seen_keys or alias_key in norm_alias_seen:
                        recommended_action = ACTION_NO_ACTION
                        action_reason = "duplicate normalization draft key detected; keep first and skip duplicate"
                    else:
                        norm_seq += 1
                        draft_fix_id = f"S4E-NORM-{norm_seq:04d}"
                        norm_seen_keys.add(norm_key)
                        norm_alias_seen[alias_key] = draft_fix_id
                        draft_target_file = str(NORM_DRAFT_XLSX)
                        recommended_action = ACTION_DRAFT_NORMALIZATION_FIX
                        action_reason = "normalization mismatch with non-conflicting alias candidate"
                        normalization_rows.append(
                            {
                                "draft_fix_id": draft_fix_id,
                                "issue_id": issue_id,
                                "raw_metric_name": raw_metric_name,
                                "normalized_raw_metric_name": normalized_raw,
                                "existing_rule_metric_name": _norm(r.get("existing_rule_text / pattern")),
                                "proposed_alias": proposed_alias,
                                "proposed_normalized_metric": proposed_normalized_metric,
                                "target_standard_metric": proposed_standard_metric,
                                "asset_package": asset_package,
                                "statement_type": statement_type,
                                "evidence_source": evidence_source,
                                "fix_type": fix_type,
                                "confidence_level": conf if conf in ALLOWED_CONFIDENCE else CONF_MEDIUM,
                                "draft_status": status,
                                "action_reason": action_reason,
                            }
                        )
        elif stage4d_status in {REASON_SCOPE_MISMATCH, REASON_RULE_EXISTS_BUT_NOT_APPLIED}:
            # Stage4D concluded rule engine doesn't need fix; route to scope/applicability draft.
            # RULE_EXISTS_BUT_NOT_APPLIED is split here as scope/applicability layer issue.
            if stage4d_status == REASON_RULE_EXISTS_BUT_NOT_APPLIED and _norm(r.get("recommended_stage4d_action")) == "VALIDATE_DRAFT_RULE_IN_DRY_RUN":
                recommended_action = ACTION_DEFER_TO_MAPPING_RULE_PROMOTION
                action_reason = "belongs to draft-rule validation path; defer to mapping-rule promotion flow"
            else:
                fix_type = FIX_EXPAND_RULE_SCOPE
                current_scope_miss_reason = stage4d_status
                if asset_package:
                    fix_type = FIX_ADD_PACKAGE_SCOPE
                if statement_type:
                    fix_type = FIX_EXPAND_RULE_SCOPE

                proposed_scope = "INCLUDE_05_STANDARDIZED_TO_01_06_BRIDGE"
                existing_scope = "GLOBAL_ALIAS_MATCH_ONLY"
                if stage4d_status == REASON_SCOPE_MISMATCH:
                    proposed_scope = "INCLUDE_MIXED_TABLE_STATEMENT_CONTEXT"
                if source_layer and target_layer:
                    proposed_scope = f"INCLUDE_{source_layer}_TO_{target_layer}"

                scope_conflict = False
                if matched_existing_rule_id:
                    prev_scope = scope_rule_scope_seen.get(matched_existing_rule_id)
                    if prev_scope and prev_scope != proposed_scope:
                        scope_conflict = True
                    else:
                        scope_rule_scope_seen[matched_existing_rule_id] = proposed_scope

                if scope_conflict:
                    recommended_action = ACTION_NEED_MANUAL_OVERLAP_REVIEW
                    action_reason = "existing rule has multiple competing proposed scopes; manual review required"
                    conflict_draft_fix_count += 1
                else:
                    scope_key = "|".join([issue_id, matched_existing_rule_id, proposed_scope, fix_type])
                    if scope_key in scope_seen_keys:
                        recommended_action = ACTION_NO_ACTION
                        action_reason = "duplicate scope draft key detected; keep first and skip duplicate"
                    else:
                        scope_seq += 1
                        draft_fix_id = f"S4E-SCOPE-{scope_seq:04d}"
                        scope_seen_keys.add(scope_key)
                        draft_target_file = str(SCOPE_DRAFT_XLSX)
                        recommended_action = ACTION_DRAFT_SCOPE_FIX
                        action_reason = "existing rule not effective in current applicability; draft scope expansion"
                        conf = _confidence_from_action(ACTION_DRAFT_SCOPE_FIX, priority_hint=priority_hint)
                        scope_rows.append(
                            {
                                "draft_fix_id": draft_fix_id,
                                "issue_id": issue_id,
                                "existing_rule_id": matched_existing_rule_id or exact_to_rule_id.get(raw_metric_name, ""),
                                "existing_rule_scope": existing_scope,
                                "proposed_scope": proposed_scope,
                                "asset_package": asset_package,
                                "statement_type": statement_type,
                                "raw_metric_name": raw_metric_name,
                                "target_standard_metric": proposed_standard_metric,
                                "current_scope_miss_reason": current_scope_miss_reason,
                                "fix_type": fix_type if fix_type in ALLOWED_FIX_TYPES else FIX_EXPAND_RULE_SCOPE,
                                "confidence_level": conf if conf in ALLOWED_CONFIDENCE else CONF_MEDIUM,
                                "draft_status": STATUS_DRAFT_READY,
                                "action_reason": action_reason,
                            }
                        )
        else:
            recommended_action = ACTION_NO_ACTION
            action_reason = "outside Stage4E processing scope"

        if recommended_action not in ALLOWED_STAGE4E_ACTIONS:
            recommended_action = ACTION_NO_ACTION
        if recommended_action == ACTION_NO_ACTION:
            no_action_count += 1

        risk_level = _risk_from_action(recommended_action)
        report_rows.append(
            {
                "issue_id": issue_id,
                "raw_metric_name": raw_metric_name,
                "proposed_standard_metric": proposed_standard_metric,
                "asset_package": asset_package,
                "year": year,
                "stage4d_status": stage4d_status,
                "non_effective_reason": non_effective_reason,
                "recommended_stage4e_action": recommended_action,
                "draft_target_file": draft_target_file,
                "draft_fix_id": draft_fix_id,
                "risk_level": risk_level,
                "action_reason": action_reason,
                "stage4c_status": stage4c_status,
                "matched_existing_rule_id": matched_existing_rule_id,
                "source_layer": source_layer,
                "target_layer": target_layer,
                "current_value": current_value,
                "current_unit": current_unit,
            }
        )

    norm_df = pd.DataFrame(normalization_rows)
    scope_df = pd.DataFrame(scope_rows)
    report_df = pd.DataFrame(report_rows)
    manual_overlap_df = pd.DataFrame(manual_overlap_rows)

    # Required-column and enum validation.
    norm_required_cols = [
        "draft_fix_id",
        "issue_id",
        "raw_metric_name",
        "normalized_raw_metric_name",
        "existing_rule_metric_name",
        "proposed_alias",
        "proposed_normalized_metric",
        "target_standard_metric",
        "asset_package",
        "statement_type",
        "evidence_source",
        "fix_type",
        "confidence_level",
        "draft_status",
        "action_reason",
    ]
    scope_required_cols = [
        "draft_fix_id",
        "issue_id",
        "existing_rule_id",
        "existing_rule_scope",
        "proposed_scope",
        "asset_package",
        "statement_type",
        "raw_metric_name",
        "target_standard_metric",
        "current_scope_miss_reason",
        "fix_type",
        "confidence_level",
        "draft_status",
        "action_reason",
    ]

    for c in norm_required_cols:
        if c not in norm_df.columns:
            norm_df[c] = ""
    norm_df = norm_df[norm_required_cols].copy()

    for c in scope_required_cols:
        if c not in scope_df.columns:
            scope_df[c] = ""
    scope_df = scope_df[scope_required_cols].copy()

    # Validate missing required fields in drafts.
    if not norm_df.empty:
        miss_norm = (
            norm_df["raw_metric_name"].map(_norm).eq("")
            | norm_df["target_standard_metric"].map(_norm).eq("")
            | norm_df["proposed_alias"].map(_norm).eq("")
            | norm_df["proposed_normalized_metric"].map(_norm).eq("")
        )
        missing_required_field_count += int(miss_norm.sum())
    if not scope_df.empty:
        miss_scope = (
            scope_df["existing_rule_id"].map(_norm).eq("")
            | scope_df["proposed_scope"].map(_norm).eq("")
            | scope_df["raw_metric_name"].map(_norm).eq("")
            | scope_df["target_standard_metric"].map(_norm).eq("")
        )
        missing_required_field_count += int(miss_scope.sum())

    # Enum compliance checks.
    if not norm_df.empty:
        bad_fix = ~norm_df["fix_type"].isin(ALLOWED_FIX_TYPES)
        if bad_fix.any():
            missing_required_field_count += int(bad_fix.sum())
        bad_conf = ~norm_df["confidence_level"].isin(ALLOWED_CONFIDENCE)
        if bad_conf.any():
            missing_required_field_count += int(bad_conf.sum())
        bad_status = ~norm_df["draft_status"].isin(ALLOWED_DRAFT_STATUS)
        if bad_status.any():
            missing_required_field_count += int(bad_status.sum())
    if not scope_df.empty:
        bad_fix = ~scope_df["fix_type"].isin(ALLOWED_FIX_TYPES)
        if bad_fix.any():
            missing_required_field_count += int(bad_fix.sum())
        bad_conf = ~scope_df["confidence_level"].isin(ALLOWED_CONFIDENCE)
        if bad_conf.any():
            missing_required_field_count += int(bad_conf.sum())
        bad_status = ~scope_df["draft_status"].isin(ALLOWED_DRAFT_STATUS)
        if bad_status.any():
            missing_required_field_count += int(bad_status.sum())

    # De-duplicate drafts and count duplicate keys.
    if not norm_df.empty:
        dup_norm = norm_df.duplicated(
            subset=["issue_id", "raw_metric_name", "target_standard_metric", "asset_package", "fix_type"],
            keep="first",
        )
        norm_df = norm_df[~dup_norm].copy()
    if not scope_df.empty:
        dup_scope = scope_df.duplicated(
            subset=["issue_id", "existing_rule_id", "proposed_scope", "fix_type"],
            keep="first",
        )
        scope_df = scope_df[~dup_scope].copy()

    # duplicate_draft_fix_count should reflect duplicates remaining in final draft outputs.
    final_dup_count = 0
    if not norm_df.empty:
        final_dup_count += int(
            norm_df.duplicated(
                subset=["issue_id", "raw_metric_name", "target_standard_metric", "asset_package", "fix_type"],
                keep=False,
            ).sum()
        )
    if not scope_df.empty:
        final_dup_count += int(
            scope_df.duplicated(
                subset=["issue_id", "existing_rule_id", "proposed_scope", "fix_type"],
                keep=False,
            ).sum()
        )
    duplicate_draft_fix_count = int(final_dup_count)

    # Write two draft workbooks.
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(NORM_DRAFT_XLSX, engine="openpyxl") as writer:
        norm_df.to_excel(writer, sheet_name="stage4e_normalization_fix_draft", index=False)
    with pd.ExcelWriter(SCOPE_DRAFT_XLSX, engine="openpyxl") as writer:
        scope_df.to_excel(writer, sheet_name="stage4e_scope_fix_draft", index=False)

    normalization_fix_draft_count = int(len(norm_df))
    scope_fix_draft_count = int(len(scope_df))
    manual_overlap_review_count = int(len(manual_overlap_df))

    high_confidence_fix_count = int((norm_df["confidence_level"] == CONF_HIGH).sum()) + int((scope_df["confidence_level"] == CONF_HIGH).sum())
    medium_confidence_fix_count = int((norm_df["confidence_level"] == CONF_MEDIUM).sum()) + int((scope_df["confidence_level"] == CONF_MEDIUM).sum())
    low_confidence_fix_count = int((norm_df["confidence_level"] == CONF_LOW).sum()) + int((scope_df["confidence_level"] == CONF_LOW).sum())

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
        "input_stage4d_issue_count": int(input_stage4d_issue_count),
        "normalization_mismatch_input_count": int(normalization_mismatch_input_count),
        "scope_mismatch_input_count": int(scope_mismatch_input_count),
        "existing_rule_not_applied_input_count": int(existing_rule_not_applied_input_count),
        "possible_overlap_input_count": int(possible_overlap_input_count),
        "normalization_fix_draft_count": int(normalization_fix_draft_count),
        "scope_fix_draft_count": int(scope_fix_draft_count),
        "manual_overlap_review_count": int(manual_overlap_review_count),
        "false_positive_count": int(false_positive_count),
        "no_action_count": int(no_action_count),
        "duplicate_draft_fix_count": int(duplicate_draft_fix_count),
        "conflict_draft_fix_count": int(conflict_draft_fix_count),
        "missing_required_field_count": int(missing_required_field_count),
        "high_confidence_fix_count": int(high_confidence_fix_count),
        "medium_confidence_fix_count": int(medium_confidence_fix_count),
        "low_confidence_fix_count": int(low_confidence_fix_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "formal_normalization_rules_unchanged": bool(formal_normalization_rules_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage4e_fix_draft_ready": bool(
            production_files_unchanged
            and output_06_unchanged
            and official_02B_unchanged
            and formal_mapping_rules_unchanged
            and formal_normalization_rules_unchanged
            and duplicate_draft_fix_count == 0
            and conflict_draft_fix_count == 0
            and missing_required_field_count == 0
            and delivery_status_after == "PASS"
        ),
        "delivery_status_after": delivery_status_after,
    }

    # Write report outputs.
    dist_action = report_df.groupby("recommended_stage4e_action", dropna=False).size().reset_index(name="count") if not report_df.empty else pd.DataFrame(columns=["recommended_stage4e_action", "count"])
    dist_reason = report_df.groupby("non_effective_reason", dropna=False).size().reset_index(name="count") if not report_df.empty else pd.DataFrame(columns=["non_effective_reason", "count"])
    _safe_write_excel_multi(
        {
            "stage4e_review": report_df,
            "normalization_fix_draft": norm_df,
            "scope_fix_draft": scope_df,
            "manual_overlap_review": manual_overlap_df,
            "action_distribution": dist_action,
            "reason_distribution": dist_reason,
            "summary": pd.DataFrame([summary]),
        },
        OUT_XLSX,
    )

    md_lines = [
        "# Stage4E Normalization & Scope Fix Draft",
        "",
        "## Summary",
        f"- input_stage4d_issue_count: {summary['input_stage4d_issue_count']}",
        f"- normalization_mismatch_input_count: {summary['normalization_mismatch_input_count']}",
        f"- scope_mismatch_input_count: {summary['scope_mismatch_input_count']}",
        f"- existing_rule_not_applied_input_count: {summary['existing_rule_not_applied_input_count']}",
        f"- possible_overlap_input_count: {summary['possible_overlap_input_count']}",
        f"- normalization_fix_draft_count: {summary['normalization_fix_draft_count']}",
        f"- scope_fix_draft_count: {summary['scope_fix_draft_count']}",
        f"- manual_overlap_review_count: {summary['manual_overlap_review_count']}",
        f"- false_positive_count: {summary['false_positive_count']}",
        f"- no_action_count: {summary['no_action_count']}",
        f"- duplicate_draft_fix_count: {summary['duplicate_draft_fix_count']}",
        f"- conflict_draft_fix_count: {summary['conflict_draft_fix_count']}",
        f"- missing_required_field_count: {summary['missing_required_field_count']}",
        f"- high_confidence_fix_count: {summary['high_confidence_fix_count']}",
        f"- medium_confidence_fix_count: {summary['medium_confidence_fix_count']}",
        f"- low_confidence_fix_count: {summary['low_confidence_fix_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- output_06_unchanged: {summary['output_06_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- formal_normalization_rules_unchanged: {summary['formal_normalization_rules_unchanged']}",
        f"- delivery_status_after: {summary['delivery_status_after']}",
        f"- stage4e_fix_draft_ready: {summary['stage4e_fix_draft_ready']}",
    ]
    _safe_write_text("\n".join(md_lines), OUT_MD)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"normalization_draft_xlsx: {NORM_DRAFT_XLSX}")
    print(f"scope_draft_xlsx: {SCOPE_DRAFT_XLSX}")
    print(f"stage4e_report_xlsx: {OUT_XLSX}")
    print(f"stage4e_report_md: {OUT_MD}")
    print(f"stage4e_summary_json: {OUT_JSON}")
    for k in [
        "input_stage4d_issue_count",
        "normalization_mismatch_input_count",
        "scope_mismatch_input_count",
        "existing_rule_not_applied_input_count",
        "possible_overlap_input_count",
        "normalization_fix_draft_count",
        "scope_fix_draft_count",
        "manual_overlap_review_count",
        "false_positive_count",
        "no_action_count",
        "duplicate_draft_fix_count",
        "conflict_draft_fix_count",
        "missing_required_field_count",
        "high_confidence_fix_count",
        "medium_confidence_fix_count",
        "low_confidence_fix_count",
        "production_files_unchanged",
        "output_06_unchanged",
        "official_02B_unchanged",
        "formal_mapping_rules_unchanged",
        "formal_normalization_rules_unchanged",
        "stage4e_fix_draft_ready",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
