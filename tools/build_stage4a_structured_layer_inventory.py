import argparse
import hashlib
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
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
STAGE4A_OUT = OUTPUT_DIR / "stage4a_structured_inventory"


ACTION_NEED_STRUCTURED_FACT_OVERRIDE = "NEED_STRUCTURED_FACT_OVERRIDE"
ACTION_NEED_STANDARDIZED_METRIC_CORRECTION = "NEED_STANDARDIZED_METRIC_CORRECTION"
ACTION_NEED_MAPPING_RULE_FIX = "NEED_MAPPING_RULE_FIX"
ACTION_NEED_UNIT_NORMALIZATION = "NEED_UNIT_NORMALIZATION"
ACTION_NEED_YEAR_NORMALIZATION = "NEED_YEAR_NORMALIZATION"
ACTION_FINAL_METRIC_OVERRIDE_ONLY = "FINAL_METRIC_OVERRIDE_ONLY"
ACTION_NO_ACTION = "NO_ACTION"
ACTION_NEED_MANUAL_REVIEW = "NEED_MANUAL_REVIEW"

ALLOWED_ACTIONS = {
    ACTION_NEED_STRUCTURED_FACT_OVERRIDE,
    ACTION_NEED_STANDARDIZED_METRIC_CORRECTION,
    ACTION_NEED_MAPPING_RULE_FIX,
    ACTION_NEED_UNIT_NORMALIZATION,
    ACTION_NEED_YEAR_NORMALIZATION,
    ACTION_FINAL_METRIC_OVERRIDE_ONLY,
    ACTION_NO_ACTION,
    ACTION_NEED_MANUAL_REVIEW,
}

YEAR_RE = re.compile(r"(20\d{2}(?:[AE])?)", re.IGNORECASE)

CORE_METRIC_ALIASES = {
    "营业收入": "营业收入",
    "收入": "营业收入",
    "归母净利润": "归属母公司净利润",
    "归属于母公司净利润": "归属母公司净利润",
    "归属于母公司股东的净利润": "归属母公司净利润",
    "归属母公司净利润": "归属母公司净利润",
    "净利润": "归属母公司净利润",
    "毛利率": "毛利率",
    "roe": "ROE",
    "每股收益": "每股收益",
    "eps": "每股收益",
    "p/e": "P/E",
    "pe": "P/E",
    "p/b": "P/B",
    "pb": "P/B",
    "ev/ebitda": "EV/EBITDA",
}

OVERRIDE_SOURCES = {
    "ai_extract_real_apply",
    "ai_repair_override",
    "stage3_ai_repair_override",
    "ai_repair_override_stage3",
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
        non_copy = [p for p in picked if "_copy_" not in p.name.lower()]
        if non_copy:
            picked = non_copy
    if prefer_no_backup:
        non_backup = [p for p in picked if "backup" not in p.name.lower()]
        if non_backup:
            picked = non_backup
    return picked[0]


def _snapshot_hashes() -> Dict[str, str]:
    return {
        "01": _sha256(_find_delivery_file("01_*.xlsx")),
        "02": _sha256(_find_delivery_file("02_*.xlsx")),
        "02A": _sha256(_find_delivery_file("02A_*.xlsx")),
        "05": _sha256(_find_delivery_file("05_*.xlsx")),
        "06": _sha256(_find_delivery_file("06_*.xlsx")),
        "02B": _sha256(OFFICIAL_02B_PATH),
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


def _normalize_metric_name(metric: str) -> str:
    raw = _norm(metric)
    low = raw.lower()
    if raw in CORE_METRIC_ALIASES:
        return CORE_METRIC_ALIASES[raw]
    if low in CORE_METRIC_ALIASES:
        return CORE_METRIC_ALIASES[low]
    return raw


def _extract_metric_from_text(text: str) -> str:
    t = _norm(text)
    low = t.lower()
    for alias, standard in CORE_METRIC_ALIASES.items():
        if alias.lower() in low:
            return standard
    return ""


def _extract_year_columns(columns: Iterable[Any]) -> List[str]:
    years: List[str] = []
    for c in columns:
        name = _norm(c)
        m = YEAR_RE.search(name)
        if m:
            years.append(m.group(1).upper())
    return list(dict.fromkeys(years))


def _find_metric_col(df: pd.DataFrame) -> Optional[str]:
    preferred = ["标准指标", "standard_metric", "指标", "metric", "source_row_label"]
    for c in preferred:
        if c in df.columns:
            return c
    for c in df.columns:
        cc = _norm(c).lower()
        if "指标" in cc or "metric" in cc:
            return c
    return None


def _find_asset_dirs() -> List[Path]:
    out: List[Path] = []
    for p in OUTPUT_DIR.iterdir():
        if not p.is_dir():
            continue
        n = p.name
        if ("资产包" in n) and (n.endswith("_资产包") or n.endswith("资产包")):
            out.append(p)
    return sorted(out)


def _pick_latest_asset_file(asset_dir: Path, prefix: str, include_keywords: Optional[List[str]] = None) -> Optional[Path]:
    candidates: List[Path] = []
    for p in asset_dir.glob(f"{prefix}*.xlsx"):
        name_low = p.name.lower()
        if "backup" in name_low or "copy" in name_low:
            continue
        if "副本" in p.name:
            continue
        if include_keywords and not all(k in p.name for k in include_keywords):
            continue
        candidates.append(p)
    if not candidates:
        return None
    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return candidates[0]


def _load_05_map(asset_dir: Path) -> Dict[str, Dict[str, str]]:
    result: Dict[str, Dict[str, str]] = {}
    f05 = _pick_latest_asset_file(asset_dir, "05_", include_keywords=["核心财务指标"])
    if not f05:
        f05 = _pick_latest_asset_file(asset_dir, "05_")
    if not f05 or not f05.exists():
        return result

    xls = pd.ExcelFile(f05)
    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(f05, sheet_name=sheet).fillna("")
        except Exception:
            continue
        if df.empty:
            continue
        metric_col = _find_metric_col(df)
        if not metric_col:
            continue
        year_cols = [c for c in df.columns if YEAR_RE.search(_norm(c))]
        if not year_cols:
            continue

        for _, row in df.iterrows():
            metric = _normalize_metric_name(_norm(row.get(metric_col)))
            if not metric:
                continue
            for yc in year_cols:
                year_match = YEAR_RE.search(_norm(yc))
                if not year_match:
                    continue
                year = year_match.group(1).upper()
                value = _norm(row.get(yc))
                if not value:
                    continue
                key = _key(asset_dir.name, metric, year)
                if key not in result:
                    result[key] = {
                        "asset_package": asset_dir.name,
                        "standard_metric": metric,
                        "year": year,
                        "value": value,
                        "unit": "",
                        "evidence": f"{f05.name}:{sheet}",
                    }
    return result


def _load_structured_row_texts(asset_dir: Path) -> List[str]:
    rows: List[str] = []
    f02 = _pick_latest_asset_file(asset_dir, "02_")
    if not f02:
        return rows
    try:
        xls = pd.ExcelFile(f02)
    except Exception:
        return rows

    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(f02, sheet_name=sheet).fillna("")
        except Exception:
            continue
        if df.empty:
            continue
        for _, row in df.iterrows():
            text = " ".join([_norm(x) for x in row.tolist() if _norm(x)])
            if text:
                rows.append(text)
    return rows


def _exists_in_structured(structured_texts_by_asset: Dict[str, List[str]], asset: str, metric: str, year: str) -> bool:
    asset_rows = structured_texts_by_asset.get(asset, [])
    if not asset_rows:
        return False
    y = _norm(year)
    m = _norm(metric)
    for row_text in asset_rows:
        if m and m not in row_text:
            continue
        if y and y not in row_text:
            continue
        return True
    return False


def _build_issue(
    issue_id: int,
    asset_package: str,
    standard_metric: str,
    year: str,
    source_layer: str,
    target_layer: str,
    current_value: str,
    current_unit: str,
    expected_value: str,
    issue_type: str,
    evidence_source: str,
    recommended_stage4_action: str,
    action_reason: str,
    risk_level: str,
) -> Dict[str, Any]:
    action = recommended_stage4_action if recommended_stage4_action in ALLOWED_ACTIONS else ACTION_NEED_MANUAL_REVIEW
    return {
        "issue_id": f"S4A-{issue_id:04d}",
        "asset_package": _norm(asset_package),
        "standard_metric": _norm(standard_metric),
        "year": _norm(year),
        "source_layer": _norm(source_layer),
        "target_layer": _norm(target_layer),
        "current_value": _norm(current_value),
        "current_unit": _norm(current_unit),
        "expected_value": _norm(expected_value),
        "issue_type": _norm(issue_type),
        "evidence_source": _norm(evidence_source),
        "recommended_stage4_action": action,
        "action_reason": _norm(action_reason),
        "risk_level": _norm(risk_level),
    }


def _is_year_normalized(year: str) -> bool:
    return bool(re.fullmatch(r"20\d{2}(?:[AE])?", _norm(year)))


def _collect_unit_issue(
    issue_id: int,
    key: str,
    layer_units: Dict[str, str],
) -> Optional[Dict[str, Any]]:
    asset, metric, year = key.split("|", 2)
    non_empty = {k: v for k, v in layer_units.items() if _norm(v)}
    unique_units = sorted(set([_norm(v) for v in non_empty.values()]))
    if len(unique_units) <= 1:
        return None
    evidence = ", ".join([f"{k}:{v}" for k, v in sorted(non_empty.items())])
    return _build_issue(
        issue_id=issue_id,
        asset_package=asset,
        standard_metric=metric,
        year=year,
        source_layer="MULTI_LAYER",
        target_layer="UNIT_NORMALIZATION",
        current_value="",
        current_unit=";".join(unique_units),
        expected_value="",
        issue_type="UNIT_INCONSISTENT_ACROSS_LAYERS",
        evidence_source=evidence,
        recommended_stage4_action=ACTION_NEED_UNIT_NORMALIZATION,
        action_reason="same key appears with multiple unit labels across layers",
        risk_level="MEDIUM",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage4A structured-layer repair inventory builder.")
    parser.parse_args()

    if not OFFICIAL_02B_PATH.exists():
        raise FileNotFoundError(f"Missing official 02B file: {OFFICIAL_02B_PATH}")

    snapshot_before = _snapshot_hashes()

    p01 = _find_delivery_file("01_*.xlsx")
    p06 = _find_delivery_file("06_*.xlsx")
    p02b = OFFICIAL_02B_PATH

    df01 = pd.read_excel(p01).fillna("")
    df06 = pd.read_excel(p06).fillna("")
    df02b = pd.read_excel(p02b, sheet_name="ai_repair_override").fillna("")

    map01: Dict[str, Dict[str, str]] = {}
    for _, r in df01.iterrows():
        k = _key(r.get("asset_package"), _normalize_metric_name(_norm(r.get("standard_metric"))), r.get("year"))
        map01[k] = {"value": _norm(r.get("value")), "unit": _norm(r.get("unit"))}

    map06: Dict[str, Dict[str, str]] = {}
    for _, r in df06.iterrows():
        k = _key(r.get("asset_package"), _normalize_metric_name(_norm(r.get("standard_metric"))), r.get("year"))
        map06[k] = {
            "value": _norm(r.get("final_value")),
            "unit": _norm(r.get("final_unit")),
            "source": _norm(r.get("final_value_source")),
        }

    map02b: Dict[str, Dict[str, str]] = {}
    for _, r in df02b.iterrows():
        k = _key(r.get("asset_package"), _normalize_metric_name(_norm(r.get("standard_metric"))), r.get("year"))
        map02b[k] = {
            "value": _norm(r.get("final_value")),
            "unit": _norm(r.get("final_unit")),
            "source": _norm(r.get("final_value_source")),
            "evidence": _norm(r.get("source_reference")),
            "provenance_status": _norm(r.get("provenance_status")),
        }

    standardized_05_map: Dict[str, Dict[str, str]] = {}
    structured_texts_by_asset: Dict[str, List[str]] = {}
    scanned_structured_record_count = 0

    for asset_dir in _find_asset_dirs():
        texts = _load_structured_row_texts(asset_dir)
        structured_texts_by_asset[asset_dir.name] = texts
        scanned_structured_record_count += len(texts)

        std_map = _load_05_map(asset_dir)
        for k, v in std_map.items():
            if k not in standardized_05_map:
                standardized_05_map[k] = v

    scanned_standardized_metric_count = len(standardized_05_map)
    scanned_final_metric_count = len(map06)

    issues: List[Dict[str, Any]] = []
    issue_id = 1
    seen_issue_fingerprint: Set[Tuple[str, str]] = set()

    # A) 06 / 02B traceability against 02 and 05.
    union_final_keys = sorted(set(map06.keys()) | set(map02b.keys()))
    for k in union_final_keys:
        asset, metric, year = k.split("|", 2)
        from_06 = map06.get(k)
        from_02b = map02b.get(k)
        in_05 = k in standardized_05_map
        in_02 = _exists_in_structured(structured_texts_by_asset, asset, metric, year)

        if not _is_year_normalized(year):
            issues.append(
                _build_issue(
                    issue_id,
                    asset,
                    metric,
                    year,
                    "06/02B",
                    "YEAR_NORMALIZATION",
                    (from_06 or from_02b or {}).get("value", ""),
                    (from_06 or from_02b or {}).get("unit", ""),
                    "",
                    "YEAR_FORMAT_NON_STANDARD",
                    "06 or 02B key year field",
                    ACTION_NEED_YEAR_NORMALIZATION,
                    "year field is not normalized to 20YY or 20YYA/E",
                    "MEDIUM",
                )
            )
            issue_id += 1
            continue

        if (not in_02) and (not in_05):
            source = _norm((from_06 or {}).get("source"))
            if (k in map02b) or (source in OVERRIDE_SOURCES):
                action = ACTION_FINAL_METRIC_OVERRIDE_ONLY
                target = "FINAL_METRIC_OVERRIDE_LAYER"
                reason = "key currently rebuildable only through override/final layer, not 02/05"
                issue_type = "FINAL_KEY_NOT_TRACEABLE_TO_02_OR_05"
                risk = "MEDIUM"
            elif source.startswith("manual_"):
                action = ACTION_NEED_STRUCTURED_FACT_OVERRIDE
                target = "STRUCTURED_FACT_LAYER"
                reason = "manual final key cannot be traced to 02/05"
                issue_type = "MANUAL_FINAL_KEY_NOT_TRACEABLE_UPSTREAM"
                risk = "HIGH"
            else:
                action = ACTION_NEED_MANUAL_REVIEW
                target = "STRUCTURED_CHAIN_REVIEW"
                reason = "key not traceable to 02/05 and source is not explicit override"
                issue_type = "UNTRACEABLE_FINAL_KEY"
                risk = "HIGH"

            issues.append(
                _build_issue(
                    issue_id,
                    asset,
                    metric,
                    year,
                    "06/02B",
                    target,
                    (from_06 or from_02b or {}).get("value", ""),
                    (from_06 or from_02b or {}).get("unit", ""),
                    "",
                    issue_type,
                    (from_02b or {}).get("evidence", "06_final_row"),
                    action,
                    reason,
                    risk,
                )
            )
            issue_id += 1
            continue

        if in_02 and (not in_05):
            issues.append(
                _build_issue(
                    issue_id,
                    asset,
                    metric,
                    year,
                    "02_STRUCTURED",
                    "05_STANDARDIZED",
                    (from_06 or from_02b or {}).get("value", ""),
                    (from_06 or from_02b or {}).get("unit", ""),
                    "",
                    "STRUCTURED_PRESENT_STANDARDIZED_MISSING",
                    f"{asset}::02_to_05_gap_check",
                    ACTION_NEED_STANDARDIZED_METRIC_CORRECTION,
                    "structured evidence exists but standardized 05 key not found",
                    "MEDIUM",
                )
            )
            issue_id += 1
            continue

        fingerprint = (k, ACTION_NO_ACTION)
        if fingerprint not in seen_issue_fingerprint:
            seen_issue_fingerprint.add(fingerprint)
            issues.append(
                _build_issue(
                    issue_id,
                    asset,
                    metric,
                    year,
                    "FULL_CHAIN",
                    "NO_ACTION",
                    (from_06 or from_02b or {}).get("value", ""),
                    (from_06 or from_02b or {}).get("unit", ""),
                    "",
                    "TRACEABLE_CHAIN_OK",
                    "02/05/06 key linkage check",
                    ACTION_NO_ACTION,
                    "key can be traced in current structured-standardized-final chain",
                    "LOW",
                )
            )
            issue_id += 1

    # B) 05 -> 01/06 dropouts.
    for k, v05 in sorted(standardized_05_map.items()):
        if k in map01 or k in map06:
            continue
        asset, metric, year = k.split("|", 2)
        issues.append(
            _build_issue(
                issue_id,
                asset,
                metric,
                year,
                "05_STANDARDIZED",
                "01/06_FINAL",
                v05.get("value", ""),
                v05.get("unit", ""),
                v05.get("value", ""),
                "STANDARDIZED_KEY_NOT_ENTERED_FINAL",
                v05.get("evidence", "05_standardized"),
                ACTION_NEED_MAPPING_RULE_FIX,
                "standardized key exists in 05 but not found in 01 or 06",
                "MEDIUM",
            )
        )
        issue_id += 1

    # C) Unit normalization issues across layers by same key.
    all_keys = sorted(set(map01.keys()) | set(map06.keys()) | set(map02b.keys()) | set(standardized_05_map.keys()))
    for k in all_keys:
        units = {
            "01": _norm(map01.get(k, {}).get("unit")),
            "05": _norm(standardized_05_map.get(k, {}).get("unit")),
            "06": _norm(map06.get(k, {}).get("unit")),
            "02B": _norm(map02b.get(k, {}).get("unit")),
        }
        unit_issue = _collect_unit_issue(issue_id, k, units)
        if unit_issue is not None:
            issues.append(unit_issue)
            issue_id += 1

    # D) Metric mapping sanity: keys with empty metric.
    for k in all_keys:
        asset, metric, year = k.split("|", 2)
        if metric:
            continue
        issues.append(
            _build_issue(
                issue_id,
                asset,
                metric,
                year,
                "MULTI_LAYER",
                "METRIC_MAPPING",
                "",
                "",
                "",
                "EMPTY_STANDARD_METRIC_KEY",
                "key synthesis from layer tables",
                ACTION_NEED_MAPPING_RULE_FIX,
                "standard_metric missing in key, mapping rule fix required",
                "HIGH",
            )
        )
        issue_id += 1

    issues_df = pd.DataFrame(
        issues,
        columns=[
            "issue_id",
            "asset_package",
            "standard_metric",
            "year",
            "source_layer",
            "target_layer",
            "current_value",
            "current_unit",
            "expected_value",
            "issue_type",
            "evidence_source",
            "recommended_stage4_action",
            "action_reason",
            "risk_level",
        ],
    ).sort_values(by=["recommended_stage4_action", "asset_package", "standard_metric", "year"], kind="mergesort")

    counts = issues_df["recommended_stage4_action"].value_counts().to_dict() if not issues_df.empty else {}

    snapshot_after = _snapshot_hashes()
    production_files_unchanged = snapshot_before["01"] == snapshot_after["01"] and snapshot_before["02"] == snapshot_after["02"] and snapshot_before["02A"] == snapshot_after["02A"] and snapshot_before["05"] == snapshot_after["05"] and snapshot_before["06"] == snapshot_after["06"]
    output_06_unchanged = snapshot_before["06"] == snapshot_after["06"]
    official_02B_unchanged = snapshot_before["02B"] == snapshot_after["02B"]
    delivery_status = _run_delivery_check().get("overall_status", "UNKNOWN")

    summary = {
        "scanned_structured_record_count": int(scanned_structured_record_count),
        "scanned_standardized_metric_count": int(scanned_standardized_metric_count),
        "scanned_final_metric_count": int(scanned_final_metric_count),
        "structured_fact_override_needed_count": int(counts.get(ACTION_NEED_STRUCTURED_FACT_OVERRIDE, 0)),
        "standardized_metric_correction_needed_count": int(counts.get(ACTION_NEED_STANDARDIZED_METRIC_CORRECTION, 0)),
        "mapping_rule_fix_needed_count": int(counts.get(ACTION_NEED_MAPPING_RULE_FIX, 0)),
        "unit_normalization_needed_count": int(counts.get(ACTION_NEED_UNIT_NORMALIZATION, 0)),
        "year_normalization_needed_count": int(counts.get(ACTION_NEED_YEAR_NORMALIZATION, 0)),
        "final_metric_override_only_count": int(counts.get(ACTION_FINAL_METRIC_OVERRIDE_ONLY, 0)),
        "no_action_count": int(counts.get(ACTION_NO_ACTION, 0)),
        "need_manual_review_count": int(counts.get(ACTION_NEED_MANUAL_REVIEW, 0)),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage4a_inventory_pass": bool(
            scanned_structured_record_count > 0
            and scanned_standardized_metric_count > 0
            and scanned_final_metric_count > 0
            and production_files_unchanged
            and output_06_unchanged
            and official_02B_unchanged
            and delivery_status == "PASS"
        ),
        "delivery_status_after": delivery_status,
    }

    distribution_df = (
        issues_df.groupby("recommended_stage4_action", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(by=["count", "recommended_stage4_action"], ascending=[False, True], kind="mergesort")
        if not issues_df.empty
        else pd.DataFrame(columns=["recommended_stage4_action", "count"])
    )

    out_xlsx = STAGE4A_OUT / "105_stage4a_structured_layer_inventory.xlsx"
    out_md = STAGE4A_OUT / "105_stage4a_structured_layer_inventory.md"
    out_json = STAGE4A_OUT / "106_stage4a_structured_layer_inventory_summary.json"

    _safe_write_excel_multi(
        {
            "stage4a_inventory": issues_df,
            "summary": pd.DataFrame([summary]),
            "action_distribution": distribution_df,
        },
        out_xlsx,
    )

    md_lines = [
        "# Stage4A Structured-Layer Repair Inventory",
        "",
        "## Summary",
        f"- scanned_structured_record_count: {summary['scanned_structured_record_count']}",
        f"- scanned_standardized_metric_count: {summary['scanned_standardized_metric_count']}",
        f"- scanned_final_metric_count: {summary['scanned_final_metric_count']}",
        f"- structured_fact_override_needed_count: {summary['structured_fact_override_needed_count']}",
        f"- standardized_metric_correction_needed_count: {summary['standardized_metric_correction_needed_count']}",
        f"- mapping_rule_fix_needed_count: {summary['mapping_rule_fix_needed_count']}",
        f"- unit_normalization_needed_count: {summary['unit_normalization_needed_count']}",
        f"- year_normalization_needed_count: {summary['year_normalization_needed_count']}",
        f"- final_metric_override_only_count: {summary['final_metric_override_only_count']}",
        f"- no_action_count: {summary['no_action_count']}",
        f"- need_manual_review_count: {summary['need_manual_review_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- output_06_unchanged: {summary['output_06_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- delivery_status_after: {summary['delivery_status_after']}",
        f"- stage4a_inventory_pass: {summary['stage4a_inventory_pass']}",
    ]
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md_lines), encoding="utf-8")
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage4a_inventory_xlsx: {out_xlsx}")
    print(f"stage4a_inventory_md: {out_md}")
    print(f"stage4a_inventory_summary_json: {out_json}")
    for k in [
        "scanned_structured_record_count",
        "scanned_standardized_metric_count",
        "scanned_final_metric_count",
        "structured_fact_override_needed_count",
        "standardized_metric_correction_needed_count",
        "mapping_rule_fix_needed_count",
        "unit_normalization_needed_count",
        "year_normalization_needed_count",
        "final_metric_override_only_count",
        "no_action_count",
        "need_manual_review_count",
        "production_files_unchanged",
        "output_06_unchanged",
        "official_02B_unchanged",
        "stage4a_inventory_pass",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
