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

STAGE4C_DRAFT_XLSX = BASE_DIR / "data" / "mapping" / "drafts" / "stage4c_mapping_rule_draft.xlsx"
STAGE4C_REPORT_XLSX = OUTPUT_DIR / "stage4c_mapping_rule_draft" / "109_stage4c_mapping_rule_draft_report.xlsx"
STAGE4C_SUMMARY_JSON = OUTPUT_DIR / "stage4c_mapping_rule_draft" / "110_stage4c_mapping_rule_draft_summary.json"
STAGE4B_XLSX = OUTPUT_DIR / "stage4b_mapping_gap_classification" / "107_stage4b_mapping_gap_classification.xlsx"
STAGE4A_XLSX = OUTPUT_DIR / "stage4a_structured_inventory" / "105_stage4a_structured_layer_inventory.xlsx"
FORMAL_MAPPING_RULE_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

OUT_DIR = OUTPUT_DIR / "stage4d_mapping_rule_validation"


REASON_RULE_EXISTS_BUT_NOT_APPLIED = "RULE_EXISTS_BUT_NOT_APPLIED"
REASON_NORMALIZATION_MISMATCH = "NORMALIZATION_MISMATCH"
REASON_SCOPE_MISMATCH = "SCOPE_MISMATCH"
REASON_STATEMENT_TYPE_MISMATCH = "STATEMENT_TYPE_MISMATCH"
REASON_ASSET_PACKAGE_MISMATCH = "ASSET_PACKAGE_MISMATCH"
REASON_YEAR_OR_PERIOD_MISMATCH = "YEAR_OR_PERIOD_MISMATCH"
REASON_VALUE_LAYER_JOIN_MISMATCH = "VALUE_LAYER_JOIN_MISMATCH"
REASON_INVENTORY_FALSE_POSITIVE = "INVENTORY_FALSE_POSITIVE"
REASON_NEED_RULE_ENGINE_FIX = "NEED_RULE_ENGINE_FIX"

ACTION_VALIDATE_DRAFT_RULE_IN_DRY_RUN = "VALIDATE_DRAFT_RULE_IN_DRY_RUN"
ACTION_FIX_RULE_APPLICATION_LOGIC = "FIX_RULE_APPLICATION_LOGIC"
ACTION_FIX_NORMALIZATION_MATCHING = "FIX_NORMALIZATION_MATCHING"
ACTION_FIX_SCOPE_MATCHING = "FIX_SCOPE_MATCHING"
ACTION_MARK_AS_FALSE_POSITIVE = "MARK_AS_FALSE_POSITIVE"
ACTION_NEED_MANUAL_OVERLAP_REVIEW = "NEED_MANUAL_OVERLAP_REVIEW"
ACTION_DEFER_TO_DERIVED_RULE_FLOW = "DEFER_TO_DERIVED_RULE_FLOW"
ACTION_READY_FOR_FORMAL_RULE_PROMOTION = "READY_FOR_FORMAL_RULE_PROMOTION"

ALLOWED_ACTIONS = {
    ACTION_VALIDATE_DRAFT_RULE_IN_DRY_RUN,
    ACTION_FIX_RULE_APPLICATION_LOGIC,
    ACTION_FIX_NORMALIZATION_MATCHING,
    ACTION_FIX_SCOPE_MATCHING,
    ACTION_MARK_AS_FALSE_POSITIVE,
    ACTION_NEED_MANUAL_OVERLAP_REVIEW,
    ACTION_DEFER_TO_DERIVED_RULE_FLOW,
    ACTION_READY_FOR_FORMAL_RULE_PROMOTION,
}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


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


def _compact_text(value: Any) -> str:
    text = _norm(value)
    text = text.replace("（", "(").replace("）", ")").replace("％", "%")
    text = re.sub(r"\s+", "", text)
    return text.upper()


def _is_numeric_like(value: str) -> bool:
    s = _norm(value)
    if not s:
        return False
    s = s.replace(",", "").replace(" ", "").replace("（", "(").replace("）", ")")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    if s.endswith("%"):
        s = s[:-1]
    return bool(re.fullmatch(r"[-+]?\d+(?:\.\d+)?", s))


def _clean_metric_label_noise(label: str) -> str:
    text = _norm(label)
    if not text:
        return ""
    text = text.replace("（", "(").replace("）", ")").replace("／", "/")
    text = re.sub(r"\s+", " ", text).strip()
    compact = _compact_text(text)
    has_metric_token = any(
        token in compact
        for token in (
            "EV/EBITDA",
            "EVEBITDA",
            "EPS",
            "ROE",
            "P/E",
            "P/B",
            "营业收入",
            "归属母公司",
            "归母净利润",
            "毛利率",
            "每股收益",
        )
    )
    if not has_metric_token:
        return text
    text = re.sub(
        r"([\s\|,:：;；]+[-+]?\d*\.?\d+(?:[%％])?)+\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()
    return text


def _load_alias_catalog() -> Tuple[List[Dict[str, str]], Dict[str, List[Dict[str, str]]], Dict[str, List[Dict[str, str]]]]:
    spec = importlib.util.spec_from_file_location("financial_standardizer", FORMAL_MAPPING_RULE_FILE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    aliases: Dict[str, List[str]] = getattr(mod, "STANDARD_METRIC_ALIASES", {})

    catalog: List[Dict[str, str]] = []
    exact_map: Dict[str, List[Dict[str, str]]] = {}
    compact_map: Dict[str, List[Dict[str, str]]] = {}
    for std_metric, raw_list in aliases.items():
        for idx, alias in enumerate(raw_list, start=1):
            alias_text = _norm(alias)
            if not alias_text:
                continue
            rid = f"FS_ALIAS_{_compact_text(std_metric)}_{idx:03d}"
            rec = {
                "rule_id": rid,
                "standard_metric": _norm(std_metric),
                "alias_text": alias_text,
                "alias_compact": _compact_text(alias_text),
            }
            catalog.append(rec)
            exact_map.setdefault(alias_text, []).append(rec)
            compact_map.setdefault(rec["alias_compact"], []).append(rec)
    return catalog, exact_map, compact_map


def _match_existing_rule(
    raw_metric_name: str,
    normalized_raw_metric_name: str,
    proposed_standard_metric: str,
    exact_map: Dict[str, List[Dict[str, str]]],
    compact_map: Dict[str, List[Dict[str, str]]],
) -> Tuple[str, str, bool]:
    # returns (rule_id, rule_text, exact_or_normalized_match)
    candidates: List[Dict[str, str]] = []
    candidates.extend(exact_map.get(_norm(raw_metric_name), []))
    candidates.extend(exact_map.get(_norm(normalized_raw_metric_name), []))
    if not candidates:
        c1 = _compact_text(raw_metric_name)
        c2 = _compact_text(normalized_raw_metric_name)
        if c1:
            candidates.extend(compact_map.get(c1, []))
        if c2 and c2 != c1:
            candidates.extend(compact_map.get(c2, []))

    if not candidates:
        return "", "", False

    # Prefer candidate with same standard metric.
    same_std = [c for c in candidates if _norm(c["standard_metric"]) == _norm(proposed_standard_metric)]
    chosen = same_std[0] if same_std else candidates[0]
    text = f"{chosen['alias_text']} => {chosen['standard_metric']}"
    exact_or_normalized = _norm(raw_metric_name) == _norm(chosen["alias_text"]) or _norm(normalized_raw_metric_name) == _norm(chosen["alias_text"])
    return chosen["rule_id"], text, exact_or_normalized


def _derive_non_effective_reason_for_existing(
    row: pd.Series,
    matched_rule_id: str,
    in_01: bool,
    in_06: bool,
) -> str:
    raw = _norm(row.get("raw_metric_name"))
    norm_raw = _norm(row.get("normalized_raw_metric_name"))
    statement_type = _norm(row.get("statement_type"))
    year = _norm(row.get("year"))
    val = _norm(row.get("current_value"))
    std = _norm(row.get("proposed_standard_metric"))

    if not matched_rule_id:
        return REASON_ASSET_PACKAGE_MISMATCH
    if raw != norm_raw:
        return REASON_NORMALIZATION_MISMATCH
    if not _is_numeric_like(val) and std in {"每股收益", "归属母公司净利润", "营业收入"}:
        return REASON_INVENTORY_FALSE_POSITIVE
    if statement_type in {"其他"}:
        return REASON_STATEMENT_TYPE_MISMATCH
    if statement_type in {"财务三表混合表"} and std in {"每股收益", "归属母公司净利润"}:
        return REASON_SCOPE_MISMATCH
    if re.fullmatch(r"20\d{2}$", year):
        return REASON_YEAR_OR_PERIOD_MISMATCH
    if (not in_01) and (not in_06):
        return REASON_RULE_EXISTS_BUT_NOT_APPLIED
    if in_01 and (not in_06):
        return REASON_VALUE_LAYER_JOIN_MISMATCH
    return REASON_NEED_RULE_ENGINE_FIX


def _action_for_reason(reason: str) -> str:
    if reason == REASON_RULE_EXISTS_BUT_NOT_APPLIED:
        return ACTION_FIX_RULE_APPLICATION_LOGIC
    if reason == REASON_NORMALIZATION_MISMATCH:
        return ACTION_FIX_NORMALIZATION_MATCHING
    if reason in {REASON_SCOPE_MISMATCH, REASON_STATEMENT_TYPE_MISMATCH, REASON_ASSET_PACKAGE_MISMATCH, REASON_YEAR_OR_PERIOD_MISMATCH}:
        return ACTION_FIX_SCOPE_MATCHING
    if reason == REASON_VALUE_LAYER_JOIN_MISMATCH:
        return ACTION_FIX_RULE_APPLICATION_LOGIC
    if reason == REASON_INVENTORY_FALSE_POSITIVE:
        return ACTION_MARK_AS_FALSE_POSITIVE
    if reason == REASON_NEED_RULE_ENGINE_FIX:
        return ACTION_FIX_RULE_APPLICATION_LOGIC
    return ACTION_FIX_RULE_APPLICATION_LOGIC


def _risk_for_reason(reason: str) -> str:
    if reason in {REASON_NEED_RULE_ENGINE_FIX, REASON_RULE_EXISTS_BUT_NOT_APPLIED}:
        return "HIGH"
    if reason in {REASON_SCOPE_MISMATCH, REASON_STATEMENT_TYPE_MISMATCH, REASON_YEAR_OR_PERIOD_MISMATCH, REASON_VALUE_LAYER_JOIN_MISMATCH, REASON_NORMALIZATION_MISMATCH}:
        return "MEDIUM"
    if reason in {REASON_ASSET_PACKAGE_MISMATCH, REASON_INVENTORY_FALSE_POSITIVE}:
        return "LOW"
    return "MEDIUM"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage4D validate Stage4C mapping draft and reconcile existing-rule gaps.")
    parser.parse_args()

    for p in [
        STAGE4C_DRAFT_XLSX,
        STAGE4C_REPORT_XLSX,
        STAGE4C_SUMMARY_JSON,
        STAGE4B_XLSX,
        STAGE4A_XLSX,
        FORMAL_MAPPING_RULE_FILE,
        OFFICIAL_02B_PATH,
    ]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    snapshot_before = _snapshot_hashes()

    # Read-only layer files for verification boundary.
    p01 = _find_delivery_file("01_*.xlsx")
    p06 = _find_delivery_file("06_*.xlsx")
    _ = pd.read_excel(_find_delivery_file("02_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("05_*.xlsx")).fillna("")
    df01 = pd.read_excel(p01).fillna("")
    df06 = pd.read_excel(p06).fillna("")

    # Core inputs.
    stage4c_summary = json.loads(STAGE4C_SUMMARY_JSON.read_text(encoding="utf-8"))
    if not bool(stage4c_summary.get("stage4c_mapping_rule_draft_ready", False)):
        raise RuntimeError("Stage4C summary indicates not ready; abort Stage4D validation.")

    draft_df = pd.read_excel(STAGE4C_DRAFT_XLSX, sheet_name="stage4c_mapping_rule_draft").fillna("")
    rec_df = pd.read_excel(STAGE4C_REPORT_XLSX, sheet_name="stage4c_input_ready_records").fillna("")
    stage4b_df = pd.read_excel(STAGE4B_XLSX, sheet_name="stage4b_classification").fillna("")
    stage4a_df = pd.read_excel(STAGE4A_XLSX, sheet_name="stage4a_inventory").fillna("")

    _, exact_map, compact_map = _load_alias_catalog()
    stage4b_issue_set = set(stage4b_df["issue_id"].map(_norm).tolist())
    stage4a_issue_set = set(stage4a_df["issue_id"].map(_norm).tolist())

    key01 = set(df01.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist())
    key06 = set(df06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist())

    draft_issue_set = set(draft_df["issue_id"].map(_norm).tolist())
    draft_rule_count = len(draft_df)

    # Draft validation checks.
    draft_required_cols = [
        "draft_rule_id",
        "issue_id",
        "asset_package",
        "raw_metric_name",
        "normalized_raw_metric_name",
        "proposed_standard_metric",
        "statement_type",
        "year",
        "rule_scope",
        "confidence_level",
        "draft_status",
    ]
    for c in draft_required_cols:
        if c not in draft_df.columns:
            raise RuntimeError(f"Draft workbook missing required column: {c}")

    duplicate_draft_count = int(
        draft_df.duplicated(subset=["raw_metric_name", "proposed_standard_metric", "rule_scope"], keep=False).sum()
    ) if not draft_df.empty else 0

    # Build per-record Stage4D rows (28 records expected).
    rows: List[Dict[str, Any]] = []
    for _, r in rec_df.iterrows():
        issue_id = _norm(r.get("issue_id"))
        raw_metric_name = _norm(r.get("raw_metric_name"))
        proposed_standard_metric = _norm(r.get("proposed_standard_metric"))
        asset_package = _norm(r.get("asset_package"))
        year = _norm(r.get("year"))
        normalized_raw_metric_name = _norm(r.get("normalized_raw_metric_name")) or _clean_metric_label_noise(raw_metric_name)
        stage4c_status = "READY_RECORD"
        if issue_id in draft_issue_set:
            stage4c_status = "DRAFT_RULE"
        elif bool(r.get("already_existing")):
            stage4c_status = "ALREADY_EXISTING_RULE"
        elif bool(r.get("possible_overlap")):
            stage4c_status = "POSSIBLE_OVERLAP"

        matched_rule_id, existing_rule_text, _ = _match_existing_rule(
            raw_metric_name=raw_metric_name,
            normalized_raw_metric_name=normalized_raw_metric_name,
            proposed_standard_metric=proposed_standard_metric,
            exact_map=exact_map,
            compact_map=compact_map,
        )

        k = _key(asset_package, proposed_standard_metric, year)
        in01 = k in key01
        in06 = k in key06

        # Draft row special handling.
        if issue_id in draft_issue_set:
            draft_row = draft_df[draft_df["issue_id"].map(_norm) == issue_id].head(1)
            confidence_ok = not draft_row.empty and _norm(draft_row.iloc[0].get("confidence_level")) in {"HIGH", "MEDIUM"}
            scope_ok = not draft_row.empty and _norm(draft_row.iloc[0].get("rule_scope")) in {"GLOBAL", "PACKAGE_SPECIFIC_CANDIDATE"}
            status_ok = not draft_row.empty and _norm(draft_row.iloc[0].get("draft_status")) == "DRAFT_READY"
            required_ok = bool(raw_metric_name and proposed_standard_metric and issue_id and (not draft_row.empty))
            no_dup = duplicate_draft_count == 0
            no_conflict = bool(matched_rule_id == "" or proposed_standard_metric in _norm(existing_rule_text))
            linked_gap = issue_id in stage4b_issue_set and issue_id in stage4a_issue_set
            theoretical_close = bool(required_ok and linked_gap and (not in01) and (not in06))
            draft_valid = bool(confidence_ok and scope_ok and status_ok and required_ok and no_dup and no_conflict and linked_gap)

            overlap_flag = bool(r.get("possible_overlap"))
            if draft_valid and theoretical_close and (not overlap_flag):
                action = ACTION_READY_FOR_FORMAL_RULE_PROMOTION
                non_effective_reason = REASON_RULE_EXISTS_BUT_NOT_APPLIED
                risk = "LOW"
                action_reason = "draft is complete and linked to unresolved gap with no overlap risk"
            elif draft_valid and overlap_flag:
                action = ACTION_VALIDATE_DRAFT_RULE_IN_DRY_RUN
                non_effective_reason = REASON_NORMALIZATION_MISMATCH
                risk = "MEDIUM"
                action_reason = "draft is structurally valid but overlaps with existing normalized alias; dry-run needed"
            elif overlap_flag:
                action = ACTION_NEED_MANUAL_OVERLAP_REVIEW
                non_effective_reason = REASON_NORMALIZATION_MISMATCH
                risk = "HIGH"
                action_reason = "overlap indicates possible duplicate mapping; manual review required before promotion"
            else:
                action = ACTION_FIX_RULE_APPLICATION_LOGIC
                non_effective_reason = REASON_NEED_RULE_ENGINE_FIX
                risk = "HIGH"
                action_reason = "draft failed structural/link checks and cannot be promoted safely"

            rows.append(
                {
                    "issue_id": issue_id,
                    "raw_metric_name": raw_metric_name,
                    "proposed_standard_metric": proposed_standard_metric,
                    "asset_package": asset_package,
                    "year": year,
                    "stage4c_status": stage4c_status,
                    "matched_existing_rule_id": matched_rule_id,
                    "existing_rule_text / pattern": existing_rule_text,
                    "non_effective_reason": non_effective_reason,
                    "recommended_stage4d_action": action,
                    "action_reason": action_reason,
                    "risk_level": risk,
                    "draft_rule_valid": bool(draft_valid),
                    "linked_stage4b_gap": bool(linked_gap),
                    "theoretical_gap_closure": bool(theoretical_close),
                }
            )
            continue

        # Non-draft rows.
        if bool(r.get("possible_overlap")):
            non_effective_reason = REASON_NORMALIZATION_MISMATCH
            action = ACTION_NEED_MANUAL_OVERLAP_REVIEW
            action_reason = "possible overlap with existing normalized alias; avoid duplicate mapping"
            risk = "MEDIUM"
        elif bool(r.get("already_existing")):
            non_effective_reason = _derive_non_effective_reason_for_existing(
                row=r,
                matched_rule_id=matched_rule_id,
                in_01=in01,
                in_06=in06,
            )
            action = _action_for_reason(non_effective_reason)
            action_reason = f"existing rule located but gap remains; reason={non_effective_reason}"
            risk = _risk_for_reason(non_effective_reason)
        else:
            non_effective_reason = REASON_NEED_RULE_ENGINE_FIX
            action = ACTION_FIX_RULE_APPLICATION_LOGIC
            action_reason = "record is ready-classified but not in draft/existing/overlap buckets; engine path review needed"
            risk = "MEDIUM"

        if action not in ALLOWED_ACTIONS:
            action = ACTION_FIX_RULE_APPLICATION_LOGIC

        rows.append(
            {
                "issue_id": issue_id,
                "raw_metric_name": raw_metric_name,
                "proposed_standard_metric": proposed_standard_metric,
                "asset_package": asset_package,
                "year": year,
                "stage4c_status": stage4c_status,
                "matched_existing_rule_id": matched_rule_id,
                "existing_rule_text / pattern": existing_rule_text,
                "non_effective_reason": non_effective_reason,
                "recommended_stage4d_action": action,
                "action_reason": action_reason,
                "risk_level": risk,
                "draft_rule_valid": False,
                "linked_stage4b_gap": issue_id in stage4b_issue_set,
                "theoretical_gap_closure": False,
            }
        )

    out_df = pd.DataFrame(rows).sort_values(
        by=["stage4c_status", "recommended_stage4d_action", "asset_package", "proposed_standard_metric", "year"],
        kind="mergesort",
    )

    # Summary.
    draft_rule_valid_count = int(out_df[(out_df["stage4c_status"] == "DRAFT_RULE") & (out_df["draft_rule_valid"] == True)].shape[0])
    ready_for_formal_rule_promotion_count = int((out_df["recommended_stage4d_action"] == ACTION_READY_FOR_FORMAL_RULE_PROMOTION).sum())
    already_existing_rule_count = int((out_df["stage4c_status"] == "ALREADY_EXISTING_RULE").sum())

    reason_counts = out_df["non_effective_reason"].value_counts().to_dict() if not out_df.empty else {}
    action_counts = out_df["recommended_stage4d_action"].value_counts().to_dict() if not out_df.empty else {}
    possible_overlap_count = int((out_df["stage4c_status"] == "POSSIBLE_OVERLAP").sum()) + int(
        ((out_df["stage4c_status"] == "DRAFT_RULE") & (out_df["recommended_stage4d_action"].isin([ACTION_VALIDATE_DRAFT_RULE_IN_DRY_RUN, ACTION_NEED_MANUAL_OVERLAP_REVIEW]))).sum()
    )

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
    delivery_status_after = _run_delivery_check().get("overall_status", "UNKNOWN")

    summary = {
        "draft_rule_count": int(draft_rule_count),
        "draft_rule_valid_count": int(draft_rule_valid_count),
        "ready_for_formal_rule_promotion_count": int(ready_for_formal_rule_promotion_count),
        "already_existing_rule_count": int(already_existing_rule_count),
        "existing_rule_not_applied_count": int(reason_counts.get(REASON_RULE_EXISTS_BUT_NOT_APPLIED, 0)),
        "normalization_mismatch_count": int(reason_counts.get(REASON_NORMALIZATION_MISMATCH, 0)),
        "scope_mismatch_count": int(reason_counts.get(REASON_SCOPE_MISMATCH, 0)),
        "statement_type_mismatch_count": int(reason_counts.get(REASON_STATEMENT_TYPE_MISMATCH, 0)),
        "asset_package_mismatch_count": int(reason_counts.get(REASON_ASSET_PACKAGE_MISMATCH, 0)),
        "inventory_false_positive_count": int(reason_counts.get(REASON_INVENTORY_FALSE_POSITIVE, 0)),
        "need_rule_engine_fix_count": int(reason_counts.get(REASON_NEED_RULE_ENGINE_FIX, 0)),
        "possible_overlap_count": int(possible_overlap_count),
        "need_manual_overlap_review_count": int(action_counts.get(ACTION_NEED_MANUAL_OVERLAP_REVIEW, 0)),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage4d_validation_pass": bool(
            draft_rule_count == 1
            and production_files_unchanged
            and output_06_unchanged
            and official_02B_unchanged
            and formal_mapping_rules_unchanged
            and delivery_status_after == "PASS"
        ),
        "delivery_status_after": delivery_status_after,
    }

    out_xlsx = OUT_DIR / "111_stage4d_mapping_rule_validation.xlsx"
    out_md = OUT_DIR / "111_stage4d_mapping_rule_validation.md"
    out_json = OUT_DIR / "112_stage4d_mapping_rule_validation_summary.json"

    dist_reason_df = (
        out_df.groupby("non_effective_reason", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(by=["count", "non_effective_reason"], ascending=[False, True], kind="mergesort")
    )
    dist_action_df = (
        out_df.groupby("recommended_stage4d_action", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(by=["count", "recommended_stage4d_action"], ascending=[False, True], kind="mergesort")
    )

    _safe_write_excel_multi(
        {
            "stage4d_validation": out_df,
            "summary": pd.DataFrame([summary]),
            "reason_distribution": dist_reason_df,
            "action_distribution": dist_action_df,
        },
        out_xlsx,
    )

    md_lines = [
        "# Stage4D Mapping Rule Validation",
        "",
        "## Summary",
        f"- draft_rule_count: {summary['draft_rule_count']}",
        f"- draft_rule_valid_count: {summary['draft_rule_valid_count']}",
        f"- ready_for_formal_rule_promotion_count: {summary['ready_for_formal_rule_promotion_count']}",
        f"- already_existing_rule_count: {summary['already_existing_rule_count']}",
        f"- existing_rule_not_applied_count: {summary['existing_rule_not_applied_count']}",
        f"- normalization_mismatch_count: {summary['normalization_mismatch_count']}",
        f"- scope_mismatch_count: {summary['scope_mismatch_count']}",
        f"- statement_type_mismatch_count: {summary['statement_type_mismatch_count']}",
        f"- asset_package_mismatch_count: {summary['asset_package_mismatch_count']}",
        f"- inventory_false_positive_count: {summary['inventory_false_positive_count']}",
        f"- need_rule_engine_fix_count: {summary['need_rule_engine_fix_count']}",
        f"- possible_overlap_count: {summary['possible_overlap_count']}",
        f"- need_manual_overlap_review_count: {summary['need_manual_overlap_review_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- output_06_unchanged: {summary['output_06_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- delivery_status_after: {summary['delivery_status_after']}",
        f"- stage4d_validation_pass: {summary['stage4d_validation_pass']}",
    ]
    _safe_write_text("\n".join(md_lines), out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage4d_validation_xlsx: {out_xlsx}")
    print(f"stage4d_validation_md: {out_md}")
    print(f"stage4d_summary_json: {out_json}")
    for k in [
        "draft_rule_count",
        "draft_rule_valid_count",
        "ready_for_formal_rule_promotion_count",
        "already_existing_rule_count",
        "existing_rule_not_applied_count",
        "normalization_mismatch_count",
        "scope_mismatch_count",
        "statement_type_mismatch_count",
        "asset_package_mismatch_count",
        "inventory_false_positive_count",
        "need_rule_engine_fix_count",
        "possible_overlap_count",
        "need_manual_overlap_review_count",
        "production_files_unchanged",
        "output_06_unchanged",
        "official_02B_unchanged",
        "formal_mapping_rules_unchanged",
        "stage4d_validation_pass",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

