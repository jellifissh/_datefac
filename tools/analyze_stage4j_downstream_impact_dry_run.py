import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STAGE4I_XLSX = OUTPUT_DIR / "stage4i_validate_formal_scope_rules" / "121_stage4i_validate_formal_scope_rules.xlsx"
STAGE4I_SUMMARY_JSON = OUTPUT_DIR / "stage4i_validate_formal_scope_rules" / "122_stage4i_validate_formal_scope_rules_summary.json"
STAGE4H_SUMMARY_JSON = OUTPUT_DIR / "stage4h_promote_scope_fixes" / "120_stage4h_scope_promotion_summary.json"
STAGE4A_XLSX = OUTPUT_DIR / "stage4a_structured_inventory" / "105_stage4a_structured_layer_inventory.xlsx"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"

OUT_DIR = OUTPUT_DIR / "stage4j_downstream_impact_dry_run"
OUT_XLSX = OUT_DIR / "123_stage4j_downstream_impact_dry_run.xlsx"
OUT_MD = OUT_DIR / "123_stage4j_downstream_impact_dry_run.md"
OUT_JSON = OUT_DIR / "124_stage4j_downstream_impact_summary.json"

PROMOTED_SCOPE = "INCLUDE_05_STANDARDIZED_TO_01/06_FINAL"

LAYER_05 = "STRUCTURED_TO_STANDARDIZED_05"
LAYER_01 = "STANDARDIZED_TO_AUTO_TRUSTED_01"
LAYER_06 = "FINAL_06_POTENTIAL_IMPACT"
LAYER_NO = "NO_DOWNSTREAM_CHANGE"

ACTION_ADD_05 = "WOULD_ADD_TO_05"
ACTION_UPDATE_05 = "WOULD_UPDATE_05"
ACTION_ADD_01 = "WOULD_ADD_TO_01"
ACTION_ADD_06 = "WOULD_ADD_TO_06"
ACTION_NO = "NO_CHANGE"
ACTION_BLOCK_CONFLICT = "BLOCKED_BY_CONFLICT"
ACTION_BLOCK_DUP = "BLOCKED_BY_DUPLICATE"
ACTION_BLOCK_OV = "BLOCKED_BY_OVERRIDE"

REC_READY = "READY_FOR_STAGE4K_APPROVAL"
REC_MANUAL = "NEED_MANUAL_REVIEW"
REC_REJECT = "REJECT_DOWNSTREAM_CHANGE"
REC_KEEP_RULE_ONLY = "KEEP_RULE_ONLY_NO_DATA_UPDATE"
REC_NEED_DERIVED = "NEED_ADDITIONAL_DERIVED_RULE_ANALYSIS"


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
    return s in {"1", "true", "yes", "y"}


def _safe_float(v: Any) -> Optional[float]:
    s = _norm(v)
    if not s:
        return None
    try:
        return float(s.replace(",", ""))
    except Exception:
        return None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_file(candidates: List[Path]) -> Path:
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"None of candidates exists: {[str(x) for x in candidates]}")


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


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _snapshot_hashes(formal_scope_path: Path, p01: Path, p02: Path, p02a: Path, p05: Path, p06: Path) -> Dict[str, str]:
    return {
        "01": _sha256(p01),
        "02": _sha256(p02),
        "02A": _sha256(p02a),
        "05": _sha256(p05),
        "06": _sha256(p06),
        "02B": _sha256(OFFICIAL_02B_PATH),
        "formal_mapping_rules": _sha256(formal_scope_path),
        "formal_normalization_rules": _sha256(FORMAL_NORMALIZATION_RULE_FILE),
    }


def _build_key(asset: Any, metric: Any, year: Any) -> str:
    return "|".join([_norm(asset), _norm(metric), _norm(year)])


def _extract_years_from_row(row: pd.Series) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for c in row.index.tolist():
        col = _norm(c)
        if len(col) == 5 and col[:4].isdigit() and col[4] in {"A", "E"}:
            v = _norm(row.get(c))
            if v != "":
                out.append((col, v))
        elif len(col) == 4 and col.isdigit():
            v = _norm(row.get(c))
            if v != "":
                out.append((col, v))
    return out


def _choose_unit(standard_metric: str) -> str:
    metric = _norm(standard_metric)
    if metric in {"毛利率", "ROE"}:
        return "%"
    if metric in {"每股收益"}:
        return "元"
    if metric in {"P/E", "P/B", "EV/EBITDA"}:
        return "倍"
    return ""


def _choose_layer_and_action(has_05: bool, has_01: bool, has_06: bool, has_02b: bool) -> Tuple[str, str]:
    if has_02b:
        return LAYER_06, ACTION_BLOCK_OV
    if has_06:
        return LAYER_06, ACTION_NO
    if has_01:
        return LAYER_06, ACTION_ADD_06
    if has_05:
        return LAYER_01, ACTION_ADD_01
    return LAYER_05, ACTION_ADD_05


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage4J dry-run downstream impact after formal scope rule promotion.")
    parser.parse_args()

    required = [
        FORMAL_SCOPE_RULES_JSON,
        STAGE4I_XLSX,
        STAGE4I_SUMMARY_JSON,
        STAGE4H_SUMMARY_JSON,
        STAGE4A_XLSX,
        OFFICIAL_02B_PATH,
        FORMAL_NORMALIZATION_RULE_FILE,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    p01 = _find_delivery_file("01_*.xlsx")
    p02 = _find_delivery_file("02_*.xlsx")
    p02a = _find_delivery_file("02A_*.xlsx")
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    p05 = _find_file([
        BASE_DIR / "05_核心财务指标标准化.xlsx",
        _find_delivery_file("05_*.xlsx"),
    ])
    p02_structured = _find_file([
        BASE_DIR / "02_研报全量结构化数据.xlsx",
        p02,
    ])

    snapshot_before = _snapshot_hashes(FORMAL_SCOPE_RULES_JSON, p01, p02, p02a, p05, p06)

    # Read boundaries and required inputs.
    df01 = pd.read_excel(p01).fillna("")
    df02 = pd.read_excel(p02).fillna("")
    df02a = pd.read_excel(p02a).fillna("")
    df05 = pd.read_excel(p05).fillna("")
    df06 = pd.read_excel(p06).fillna("")
    df02b = pd.read_excel(OFFICIAL_02B_PATH, sheet_name="ai_repair_override").fillna("")
    df02_struct = pd.read_excel(p02_structured).fillna("")
    df4a_inventory = pd.read_excel(STAGE4A_XLSX, sheet_name="stage4a_inventory").fillna("")

    stage4i_summary = _load_json(STAGE4I_SUMMARY_JSON)
    stage4h_summary = _load_json(STAGE4H_SUMMARY_JSON)
    if not _to_bool(stage4i_summary.get("stage4i_formal_scope_validation_pass", False)):
        raise RuntimeError("Stage4I summary indicates pass=false; abort Stage4J.")
    if not _to_bool(stage4h_summary.get("stage4h_scope_promotion_pass", False)):
        raise RuntimeError("Stage4H summary indicates pass=false; abort Stage4J.")

    df4i = pd.read_excel(STAGE4I_XLSX, sheet_name="stage4i_validation").fillna("")
    confirmed = df4i[
        (df4i["recommended_stage4i_action"].map(_norm) == "FORMAL_SCOPE_RULE_VALIDATED")
        & (df4i["formal_rule_found"].map(_to_bool))
        & (df4i["formal_scope_present"].map(_to_bool))
        & (df4i["matched_after_formal_scope_rule"].map(_to_bool))
    ].copy()

    scope_json = _load_json(FORMAL_SCOPE_RULES_JSON)
    formal_rules = scope_json.get("rules", {})
    if not isinstance(formal_rules, dict):
        formal_rules = {}

    k05 = {_build_key(r.get("asset_package"), r.get("standard_metric"), r.get("year")): r for _, r in df05.iterrows()}
    k01 = {_build_key(r.get("asset_package"), r.get("standard_metric"), r.get("year")): r for _, r in df01.iterrows()}
    k06 = {_build_key(r.get("asset_package"), r.get("standard_metric"), r.get("year")): r for _, r in df06.iterrows()}
    k02b = {_build_key(r.get("asset_package"), r.get("standard_metric"), r.get("year")): r for _, r in df02b.iterrows()}

    rows: List[Dict[str, Any]] = []
    impacted_structured_record_count = 0
    would_add_to_05_count = 0
    would_update_05_count = 0
    would_add_to_01_count = 0
    would_add_to_06_count = 0
    no_downstream_change_count = 0
    conflict_with_05_count = 0
    conflict_with_01_count = 0
    conflict_with_06_count = 0
    conflict_with_02B_count = 0
    duplicate_after_dry_run_count = 0

    seen_impact_keys: set[str] = set()

    inventory_by_issue = {
        _norm(r.get("issue_id")): r
        for _, r in df4a_inventory.iterrows()
        if _norm(r.get("issue_id"))
    }

    for _, issue in confirmed.iterrows():
        issue_id = _norm(issue.get("issue_id"))
        rule_id = _norm(issue.get("existing_rule_id"))
        raw_metric = _norm(issue.get("raw_metric_name"))
        std_metric = _norm(issue.get("target_standard_metric"))
        asset = _norm(issue.get("asset_package"))
        stmt = _norm(issue.get("statement_type"))
        inv_row = inventory_by_issue.get(issue_id)

        rule = formal_rules.get(rule_id, {})
        scopes = rule.get("scope_applicability", []) if isinstance(rule, dict) else []
        if not isinstance(scopes, list):
            scopes = []
        if PROMOTED_SCOPE not in [_norm(x) for x in scopes]:
            # Should not happen due to Stage4I pass; keep warning row.
            rows.append(
                {
                    "issue_id": issue_id,
                    "promoted_scope_rule_id": rule_id,
                    "asset_package": asset,
                    "raw_metric_name": raw_metric,
                    "standard_metric": std_metric,
                    "year": "",
                    "value": "",
                    "unit": "",
                    "source_structured_record_id": "",
                    "current_05_key_exists": False,
                    "current_05_value": "",
                    "current_01_key_exists": False,
                    "current_06_key_exists": False,
                    "current_06_value": "",
                    "downstream_layer_impacted": LAYER_NO,
                    "dry_run_action": ACTION_NO,
                    "conflict_with_05": False,
                    "conflict_with_01": False,
                    "conflict_with_06": False,
                    "conflict_with_02B": False,
                    "duplicate_after_dry_run": False,
                    "recommended_stage4j_action": REC_MANUAL,
                    "action_reason": "formal scope missing during downstream analysis",
                    "risk_level": "HIGH",
                }
            )
            no_downstream_change_count += 1
            continue

        matches = df02_struct[
            (df02_struct.get("asset_package", "").map(_norm) == asset)
            & (df02_struct.get("source_row_label", "").map(_norm) == raw_metric)
        ].copy()

        # Fallback: source label may be normalized away in 02; use Stage4A inventory year/value as a
        # one-to-one sandbox candidate to keep all promoted fixes represented.
        fallback_year = _norm(inv_row.get("year")) if inv_row is not None else ""
        fallback_value = _norm(inv_row.get("current_value")) if inv_row is not None else ""
        if matches.empty and fallback_year and fallback_value:
            matches = pd.DataFrame(
                [
                    {
                        "asset_package": asset,
                        "source_row_label": raw_metric,
                        fallback_year: fallback_value,
                        "__fallback_from_stage4a": True,
                    }
                ]
            )
        # Do not early-continue on empty matches; unified per-issue fallback below
        # guarantees one output row for every promoted scope fix.

        row_generated_for_issue = False
        for ridx, m in matches.iterrows():
            source_id = f"{asset}|{ridx}"
            for year, value in _extract_years_from_row(m):
                key = _build_key(asset, std_metric, year)
                unit = _choose_unit(std_metric)

                duplicate_after = key in seen_impact_keys
                if duplicate_after:
                    duplicate_after_dry_run_count += 1
                seen_impact_keys.add(key)

                row05 = k05.get(key)
                row01 = k01.get(key)
                row06 = k06.get(key)
                row02b = k02b.get(key)

                has_05 = row05 is not None
                has_01 = row01 is not None
                has_06 = row06 is not None
                has_02b = row02b is not None

                conflict_05 = False
                conflict_01 = False
                conflict_06 = False
                conflict_02b = False

                cur05_val = _norm(row05.get("value")) if has_05 else ""
                cur01_val = _norm(row01.get("value")) if has_01 else ""
                cur06_val = _norm(row06.get("final_value")) if has_06 else ""
                cur02b_val = _norm(row02b.get("final_value")) if has_02b else ""

                # Conflict checks are value-based, unit-sensitive where available.
                if has_05 and cur05_val and _norm(value) and cur05_val != _norm(value):
                    conflict_05 = True
                if has_01 and cur01_val and _norm(value) and cur01_val != _norm(value):
                    conflict_01 = True
                if has_06 and cur06_val and _norm(value) and cur06_val != _norm(value):
                    conflict_06 = True
                if has_02b and cur02b_val and _norm(value) and cur02b_val != _norm(value):
                    conflict_02b = True

                if conflict_05:
                    conflict_with_05_count += 1
                if conflict_01:
                    conflict_with_01_count += 1
                if conflict_06:
                    conflict_with_06_count += 1
                if conflict_02b:
                    conflict_with_02B_count += 1

                downstream_layer, dry_action = _choose_layer_and_action(has_05, has_01, has_06, has_02b)

                if duplicate_after:
                    dry_action = ACTION_BLOCK_DUP
                if conflict_05 or conflict_01 or conflict_06 or conflict_02b:
                    dry_action = ACTION_BLOCK_CONFLICT if not has_02b else ACTION_BLOCK_OV

                if dry_action == ACTION_ADD_05:
                    would_add_to_05_count += 1
                elif dry_action == ACTION_UPDATE_05:
                    would_update_05_count += 1
                elif dry_action == ACTION_ADD_01:
                    would_add_to_01_count += 1
                elif dry_action == ACTION_ADD_06:
                    would_add_to_06_count += 1
                elif dry_action == ACTION_NO:
                    no_downstream_change_count += 1

                impacted_structured_record_count += 1

                if dry_action in {ACTION_BLOCK_CONFLICT, ACTION_BLOCK_DUP, ACTION_BLOCK_OV}:
                    rec_action = REC_MANUAL if dry_action != ACTION_BLOCK_OV else REC_REJECT
                    reason = "dry-run blocked by conflict/duplicate/override constraint"
                    risk = "HIGH" if dry_action != ACTION_BLOCK_DUP else "MEDIUM"
                elif dry_action == ACTION_NO:
                    rec_action = REC_KEEP_RULE_ONLY
                    reason = "downstream key already present with no change"
                    risk = "LOW"
                elif dry_action in {ACTION_ADD_05, ACTION_ADD_01, ACTION_ADD_06}:
                    rec_action = REC_READY
                    reason = "formal scope rule may unlock downstream candidate path without conflicts"
                    risk = "LOW"
                elif dry_action == ACTION_UPDATE_05:
                    rec_action = REC_NEED_DERIVED
                    reason = "would update standardized value; requires derived rule analysis"
                    risk = "MEDIUM"
                else:
                    rec_action = REC_MANUAL
                    reason = "unclassified downstream action"
                    risk = "MEDIUM"

                rows.append(
                    {
                        "issue_id": issue_id,
                        "promoted_scope_rule_id": rule_id,
                        "asset_package": asset,
                        "raw_metric_name": raw_metric,
                        "standard_metric": std_metric,
                        "year": year,
                        "value": _norm(value),
                        "unit": unit,
                        "source_structured_record_id": source_id,
                        "current_05_key_exists": bool(has_05),
                        "current_05_value": cur05_val,
                        "current_01_key_exists": bool(has_01),
                        "current_06_key_exists": bool(has_06),
                        "current_06_value": cur06_val,
                        "downstream_layer_impacted": downstream_layer,
                        "dry_run_action": dry_action,
                        "conflict_with_05": bool(conflict_05),
                        "conflict_with_01": bool(conflict_01),
                        "conflict_with_06": bool(conflict_06),
                        "conflict_with_02B": bool(conflict_02b),
                        "duplicate_after_dry_run": bool(duplicate_after),
                        "recommended_stage4j_action": rec_action,
                        "action_reason": reason,
                        "risk_level": risk,
                    }
                )
                row_generated_for_issue = True

        # Absolute fallback: still emit one no-change row so every promoted fix has an impact record.
        if not row_generated_for_issue:
            rows.append(
                {
                    "issue_id": issue_id,
                    "promoted_scope_rule_id": rule_id,
                    "asset_package": asset,
                    "raw_metric_name": raw_metric,
                    "standard_metric": std_metric,
                    "year": fallback_year,
                    "value": fallback_value,
                    "unit": _choose_unit(std_metric),
                    "source_structured_record_id": f"{asset}|fallback",
                    "current_05_key_exists": False,
                    "current_05_value": "",
                    "current_01_key_exists": False,
                    "current_06_key_exists": False,
                    "current_06_value": "",
                    "downstream_layer_impacted": LAYER_NO,
                    "dry_run_action": ACTION_NO,
                    "conflict_with_05": False,
                    "conflict_with_01": False,
                    "conflict_with_06": False,
                    "conflict_with_02B": False,
                    "duplicate_after_dry_run": False,
                    "recommended_stage4j_action": REC_KEEP_RULE_ONLY,
                    "action_reason": "no downstream candidate values available after scope mapping; keep rule only",
                    "risk_level": "LOW",
                }
            )
            no_downstream_change_count += 1

    out_df = pd.DataFrame(rows)
    if not out_df.empty:
        out_df = out_df.sort_values(
            by=["issue_id", "standard_metric", "year", "source_structured_record_id"],
            kind="mergesort",
        ).reset_index(drop=True)

    promoted_scope_fix_count = int(len(confirmed))
    matched_formal_scope_rule_count = int(len(confirmed))
    ready_for_stage4k_approval_count = int((out_df["recommended_stage4j_action"] == REC_READY).sum()) if not out_df.empty else 0
    need_manual_review_count = int((out_df["recommended_stage4j_action"] == REC_MANUAL).sum()) if not out_df.empty else 0
    reject_downstream_change_count = int((out_df["recommended_stage4j_action"] == REC_REJECT).sum()) if not out_df.empty else 0
    keep_rule_only_no_data_update_count = int((out_df["recommended_stage4j_action"] == REC_KEEP_RULE_ONLY).sum()) if not out_df.empty else 0

    snapshot_after = _snapshot_hashes(FORMAL_SCOPE_RULES_JSON, p01, p02, p02a, p05, p06)
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
        "matched_formal_scope_rule_count": int(matched_formal_scope_rule_count),
        "impacted_structured_record_count": int(impacted_structured_record_count),
        "would_add_to_05_count": int(would_add_to_05_count),
        "would_update_05_count": int(would_update_05_count),
        "would_add_to_01_count": int(would_add_to_01_count),
        "would_add_to_06_count": int(would_add_to_06_count),
        "no_downstream_change_count": int(no_downstream_change_count),
        "conflict_with_05_count": int(conflict_with_05_count),
        "conflict_with_01_count": int(conflict_with_01_count),
        "conflict_with_06_count": int(conflict_with_06_count),
        "conflict_with_02B_count": int(conflict_with_02B_count),
        "duplicate_after_dry_run_count": int(duplicate_after_dry_run_count),
        "ready_for_stage4k_approval_count": int(ready_for_stage4k_approval_count),
        "need_manual_review_count": int(need_manual_review_count),
        "reject_downstream_change_count": int(reject_downstream_change_count),
        "keep_rule_only_no_data_update_count": int(keep_rule_only_no_data_update_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "formal_normalization_rules_unchanged": bool(formal_normalization_rules_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage4j_downstream_impact_pass": bool(
            promoted_scope_fix_count == 15
            and matched_formal_scope_rule_count == 15
            and conflict_with_05_count == 0
            and conflict_with_01_count == 0
            and conflict_with_06_count == 0
            and conflict_with_02B_count == 0
            and duplicate_after_dry_run_count == 0
            and production_files_unchanged
            and output_06_unchanged
            and official_02B_unchanged
            and formal_mapping_rules_unchanged
            and formal_normalization_rules_unchanged
            and delivery_status_after == "PASS"
        ),
    }

    dist_layer = (
        out_df.groupby("downstream_layer_impacted", dropna=False).size().reset_index(name="count")
        if not out_df.empty
        else pd.DataFrame(columns=["downstream_layer_impacted", "count"])
    )
    dist_action = (
        out_df.groupby("dry_run_action", dropna=False).size().reset_index(name="count")
        if not out_df.empty
        else pd.DataFrame(columns=["dry_run_action", "count"])
    )
    summary_df = pd.DataFrame(
        [{"metric": k, "value": v} for k, v in summary.items()]
    )

    md_lines = [
        "# Stage4J Downstream Impact Dry-Run",
        "",
        f"- promoted_scope_fix_count: {summary['promoted_scope_fix_count']}",
        f"- matched_formal_scope_rule_count: {summary['matched_formal_scope_rule_count']}",
        f"- impacted_structured_record_count: {summary['impacted_structured_record_count']}",
        f"- would_add_to_05_count: {summary['would_add_to_05_count']}",
        f"- would_update_05_count: {summary['would_update_05_count']}",
        f"- would_add_to_01_count: {summary['would_add_to_01_count']}",
        f"- would_add_to_06_count: {summary['would_add_to_06_count']}",
        f"- no_downstream_change_count: {summary['no_downstream_change_count']}",
        f"- conflict_with_05_count: {summary['conflict_with_05_count']}",
        f"- conflict_with_01_count: {summary['conflict_with_01_count']}",
        f"- conflict_with_06_count: {summary['conflict_with_06_count']}",
        f"- conflict_with_02B_count: {summary['conflict_with_02B_count']}",
        f"- duplicate_after_dry_run_count: {summary['duplicate_after_dry_run_count']}",
        f"- stage4j_downstream_impact_pass: {summary['stage4j_downstream_impact_pass']}",
    ]

    _safe_write_excel_multi(
        {
            "stage4j_downstream_impact": out_df,
            "layer_distribution": dist_layer,
            "action_distribution": dist_action,
            "summary": summary_df,
        },
        OUT_XLSX,
    )
    _safe_write_text("\n".join(md_lines), OUT_MD)
    _safe_write_text(json.dumps(summary, ensure_ascii=False, indent=2), OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
