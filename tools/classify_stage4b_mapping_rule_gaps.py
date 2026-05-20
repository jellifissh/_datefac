import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"
STAGE4A_XLSX = OUTPUT_DIR / "stage4a_structured_inventory" / "105_stage4a_structured_layer_inventory.xlsx"
STAGE4A_SUMMARY = OUTPUT_DIR / "stage4a_structured_inventory" / "106_stage4a_structured_layer_inventory_summary.json"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
OUT_DIR = OUTPUT_DIR / "stage4b_mapping_gap_classification"


CATEGORY_MISSING_RAW_TO_STANDARD_MAPPING = "MISSING_RAW_TO_STANDARD_MAPPING"
CATEGORY_AMBIGUOUS_METRIC_NAME = "AMBIGUOUS_METRIC_NAME"
CATEGORY_NON_CORE_METRIC = "NON_CORE_METRIC"
CATEGORY_DUPLICATE_OR_OVERLAPPING_MAPPING = "DUPLICATE_OR_OVERLAPPING_MAPPING"
CATEGORY_DERIVED_METRIC_NOT_DIRECT_MAPPING = "DERIVED_METRIC_NOT_DIRECT_MAPPING"
CATEGORY_PACKAGE_SPECIFIC_MAPPING_GAP = "PACKAGE_SPECIFIC_MAPPING_GAP"
CATEGORY_LIKELY_FALSE_POSITIVE = "LIKELY_FALSE_POSITIVE"

ALLOWED_CATEGORIES = {
    CATEGORY_MISSING_RAW_TO_STANDARD_MAPPING,
    CATEGORY_AMBIGUOUS_METRIC_NAME,
    CATEGORY_NON_CORE_METRIC,
    CATEGORY_DUPLICATE_OR_OVERLAPPING_MAPPING,
    CATEGORY_DERIVED_METRIC_NOT_DIRECT_MAPPING,
    CATEGORY_PACKAGE_SPECIFIC_MAPPING_GAP,
    CATEGORY_LIKELY_FALSE_POSITIVE,
}

ACTION_READY_FOR_MAPPING_RULE_DRAFT = "READY_FOR_MAPPING_RULE_DRAFT"
ACTION_NEED_MANUAL_MAPPING_REVIEW = "NEED_MANUAL_MAPPING_REVIEW"
ACTION_DEFER_NON_CORE_METRIC = "DEFER_NON_CORE_METRIC"
ACTION_REJECT_FALSE_POSITIVE = "REJECT_FALSE_POSITIVE"
ACTION_NEED_DERIVED_METRIC_RULE = "NEED_DERIVED_METRIC_RULE"
ACTION_NEED_PACKAGE_SPECIFIC_RULE = "NEED_PACKAGE_SPECIFIC_RULE"

ALLOWED_ACTIONS = {
    ACTION_READY_FOR_MAPPING_RULE_DRAFT,
    ACTION_NEED_MANUAL_MAPPING_REVIEW,
    ACTION_DEFER_NON_CORE_METRIC,
    ACTION_REJECT_FALSE_POSITIVE,
    ACTION_NEED_DERIVED_METRIC_RULE,
    ACTION_NEED_PACKAGE_SPECIFIC_RULE,
}

PRIORITY_HIGH = "HIGH"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_LOW = "LOW"
ALLOWED_PRIORITIES = {PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW}

DERIVED_METRICS = {"ROE", "毛利率", "P/E", "P/B", "EV/EBITDA"}
CORE_METRICS = {"营业收入", "归属母公司净利润", "毛利率", "ROE", "每股收益", "P/E", "P/B", "EV/EBITDA"}
AMBIGUOUS_TOKENS = ("净利润", "收入", "利润", "盈利", "收益")
YEAR_RE = re.compile(r"^20\d{2}(?:[AE])?$", re.IGNORECASE)


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


def _year_cols(columns: Iterable[Any]) -> List[str]:
    out: List[str] = []
    for c in columns:
        cc = _norm(c)
        if YEAR_RE.match(cc):
            out.append(cc)
    return out


def _first_existing_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _find_asset_dirs() -> List[Path]:
    out = []
    for p in OUTPUT_DIR.iterdir():
        if not p.is_dir():
            continue
        n = p.name
        if ("资产包" in n) and (n.endswith("_资产包") or n.endswith("资产包")):
            out.append(p)
    return sorted(out)


def _pick_latest_asset_file(asset_dir: Path, prefix: str, include_keywords: Optional[List[str]] = None) -> Optional[Path]:
    files = []
    for p in asset_dir.glob(f"{prefix}*.xlsx"):
        low = p.name.lower()
        if "backup" in low or "copy" in low or "副本" in p.name:
            continue
        if include_keywords and not all(k in p.name for k in include_keywords):
            continue
        files.append(p)
    if not files:
        return None
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0]


def _parse_05_context() -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, str]]:
    detail_map: Dict[str, List[Dict[str, Any]]] = {}
    asset_file_map: Dict[str, str] = {}

    for asset_dir in _find_asset_dirs():
        f05 = _pick_latest_asset_file(asset_dir, "05_", include_keywords=["核心财务指标"])
        if not f05:
            f05 = _pick_latest_asset_file(asset_dir, "05_")
        if not f05:
            continue

        asset_file_map[asset_dir.name] = f05.name
        try:
            xls = pd.ExcelFile(f05)
        except Exception:
            continue
        if "抽取明细" not in xls.sheet_names:
            continue
        try:
            df = pd.read_excel(f05, sheet_name="抽取明细").fillna("")
        except Exception:
            continue
        if df.empty:
            continue

        col_metric = _first_existing_column(df, ["标准指标", "standard_metric", "指标"])
        col_raw = _first_existing_column(df, ["source_row_label", "raw_metric_name", "source_metric_name"])
        col_method = _first_existing_column(df, ["match_method"])
        col_alias = _first_existing_column(df, ["matched_alias"])
        col_conf = _first_existing_column(df, ["confidence"])
        col_source_table = _first_existing_column(df, ["source_table_type"])
        yc = _year_cols(df.columns)
        if not col_metric or not yc:
            continue

        for _, r in df.iterrows():
            metric = _norm(r.get(col_metric))
            raw_label = _norm(r.get(col_raw)) if col_raw else ""
            match_method = _norm(r.get(col_method)) if col_method else ""
            matched_alias = _norm(r.get(col_alias)) if col_alias else ""
            confidence = _norm(r.get(col_conf)) if col_conf else ""
            source_table_type = _norm(r.get(col_source_table)) if col_source_table else ""
            if not metric:
                continue
            for y in yc:
                v = _norm(r.get(y))
                if not v:
                    continue
                k = _key(asset_dir.name, metric, y)
                detail_map.setdefault(k, []).append(
                    {
                        "raw_metric_name": raw_label,
                        "match_method": match_method,
                        "matched_alias": matched_alias,
                        "confidence": confidence,
                        "source_table_type": source_table_type,
                        "value": v,
                    }
                )
    return detail_map, asset_file_map


def _pick_best_detail(detail_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not detail_rows:
        return {}

    def _rank(row: Dict[str, Any]) -> Tuple[int, float, int]:
        method = _norm(row.get("match_method"))
        method_rank = {"exact": 0, "synonym": 1, "normalized_fuzzy": 2}.get(method, 9)
        try:
            conf = float(_norm(row.get("confidence")) or 0.0)
        except Exception:
            conf = 0.0
        raw_len = len(_norm(row.get("raw_metric_name")))
        return (method_rank, -conf, -raw_len)

    ranked = sorted(detail_rows, key=_rank)
    return ranked[0]


def _existing_mapping_status(best_detail: Dict[str, Any]) -> str:
    if not best_detail:
        return "NO_05_DETAIL_CONTEXT"
    mm = _norm(best_detail.get("match_method"))
    if mm in {"exact", "synonym"}:
        return "MAPPED_STRONG_ALIAS_IN_05"
    if mm == "normalized_fuzzy":
        return "MAPPED_FUZZY_IN_05"
    return "MAPPED_IN_05_WITH_WEAK_CONTEXT"


def _is_ambiguous_raw(raw_metric_name: str, standard_metric: str) -> bool:
    raw = _norm(raw_metric_name)
    if not raw:
        return False
    # Generic label only, without explicit core disambiguation.
    if raw in {"净利润", "收入", "利润", "收益"}:
        return True
    if any(t in raw for t in AMBIGUOUS_TOKENS):
        std = _norm(standard_metric)
        if std == "归属母公司净利润" and ("母公司" not in raw and "归母" not in raw):
            return True
        if std == "营业收入" and "营业收入" not in raw:
            return True
    return False


def _is_non_core_metric(standard_metric: str) -> bool:
    return _norm(standard_metric) not in CORE_METRICS


def _is_package_specific(asset_count_by_metric: Dict[str, int], standard_metric: str, asset_package: str) -> bool:
    metric = _norm(standard_metric)
    if not metric:
        return False
    # Metric appears in <=2 packages and current package contributes all/most issues.
    return int(asset_count_by_metric.get(metric, 0)) <= 2 and _norm(asset_package) != ""


def _build_06_overlap_maps(df06: pd.DataFrame) -> Dict[Tuple[str, str, str], List[str]]:
    # Map (asset, year, value) -> metrics in 06 for overlap detection.
    overlap_map: Dict[Tuple[str, str, str], List[str]] = {}
    for _, r in df06.iterrows():
        asset = _norm(r.get("asset_package"))
        year = _norm(r.get("year"))
        value = _norm(r.get("final_value"))
        metric = _norm(r.get("standard_metric"))
        if not asset or not year or not value:
            continue
        overlap_map.setdefault((asset, year, value), []).append(metric)
    return overlap_map


def _classify_category(
    standard_metric: str,
    raw_metric_name: str,
    current_value: str,
    overlap_metrics: List[str],
    asset_count_by_metric: Dict[str, int],
    asset_package: str,
) -> str:
    metric = _norm(standard_metric)
    raw = _norm(raw_metric_name)
    value = _norm(current_value)

    if not value:
        return CATEGORY_LIKELY_FALSE_POSITIVE
    if _is_non_core_metric(metric):
        return CATEGORY_NON_CORE_METRIC
    if _is_ambiguous_raw(raw, metric):
        return CATEGORY_AMBIGUOUS_METRIC_NAME
    if overlap_metrics:
        # same (asset,year,value) already exists under another metric in 06.
        return CATEGORY_DUPLICATE_OR_OVERLAPPING_MAPPING
    if metric in DERIVED_METRICS:
        return CATEGORY_DERIVED_METRIC_NOT_DIRECT_MAPPING
    if _is_package_specific(asset_count_by_metric, metric, asset_package):
        return CATEGORY_PACKAGE_SPECIFIC_MAPPING_GAP
    if not raw:
        return CATEGORY_MISSING_RAW_TO_STANDARD_MAPPING
    return CATEGORY_MISSING_RAW_TO_STANDARD_MAPPING


def _decide_action(category: str) -> str:
    if category == CATEGORY_MISSING_RAW_TO_STANDARD_MAPPING:
        return ACTION_READY_FOR_MAPPING_RULE_DRAFT
    if category == CATEGORY_AMBIGUOUS_METRIC_NAME:
        return ACTION_NEED_MANUAL_MAPPING_REVIEW
    if category == CATEGORY_NON_CORE_METRIC:
        return ACTION_DEFER_NON_CORE_METRIC
    if category == CATEGORY_DUPLICATE_OR_OVERLAPPING_MAPPING:
        return ACTION_NEED_MANUAL_MAPPING_REVIEW
    if category == CATEGORY_DERIVED_METRIC_NOT_DIRECT_MAPPING:
        return ACTION_NEED_DERIVED_METRIC_RULE
    if category == CATEGORY_PACKAGE_SPECIFIC_MAPPING_GAP:
        return ACTION_NEED_PACKAGE_SPECIFIC_RULE
    if category == CATEGORY_LIKELY_FALSE_POSITIVE:
        return ACTION_REJECT_FALSE_POSITIVE
    return ACTION_NEED_MANUAL_MAPPING_REVIEW


def _decide_priority(
    category: str,
    standard_metric: str,
    affects_06: bool,
    existing_mapping_status: str,
    raw_metric_name: str,
    year: str,
    overlap_metrics: List[str],
) -> str:
    metric = _norm(standard_metric)
    raw = _norm(raw_metric_name)
    year_ok = bool(YEAR_RE.match(_norm(year)))
    mapping_clear = existing_mapping_status in {"MAPPED_STRONG_ALIAS_IN_05", "MAPPED_FUZZY_IN_05"} and bool(raw)
    no_conflict = not overlap_metrics
    is_derived = category == CATEGORY_DERIVED_METRIC_NOT_DIRECT_MAPPING

    if affects_06 and metric in CORE_METRICS and mapping_clear and year_ok and no_conflict and (not is_derived):
        return PRIORITY_HIGH
    if category in {
        CATEGORY_AMBIGUOUS_METRIC_NAME,
        CATEGORY_DUPLICATE_OR_OVERLAPPING_MAPPING,
        CATEGORY_DERIVED_METRIC_NOT_DIRECT_MAPPING,
        CATEGORY_PACKAGE_SPECIFIC_MAPPING_GAP,
    }:
        return PRIORITY_MEDIUM
    if category in {CATEGORY_NON_CORE_METRIC, CATEGORY_LIKELY_FALSE_POSITIVE}:
        return PRIORITY_LOW
    return PRIORITY_MEDIUM


def _likely_mapping_pattern(category: str, best_detail: Dict[str, Any], standard_metric: str, raw_metric_name: str) -> str:
    mm = _norm(best_detail.get("match_method"))
    if category == CATEGORY_DERIVED_METRIC_NOT_DIRECT_MAPPING:
        return "derived_ratio_or_multiple_requires_bridge_rule"
    if category == CATEGORY_PACKAGE_SPECIFIC_MAPPING_GAP:
        return "package_specific_metric_shape"
    if category == CATEGORY_DUPLICATE_OR_OVERLAPPING_MAPPING:
        return "overlapping_value_with_existing_final_metric"
    if mm == "exact":
        return "direct_name_match_missing_delivery_bridge"
    if mm == "synonym":
        return "alias_mapping_missing_delivery_bridge"
    if mm == "normalized_fuzzy":
        return "fuzzy_alias_mapping_needs_rule_hardening"
    if _norm(raw_metric_name):
        return "raw_to_standard_present_but_not_propagated"
    return "missing_raw_metric_context"


def _action_reason(
    category: str,
    existing_mapping_status: str,
    overlap_metrics: List[str],
    standard_metric: str,
) -> str:
    if category == CATEGORY_MISSING_RAW_TO_STANDARD_MAPPING:
        return f"05 has key but delivery bridge missing; status={existing_mapping_status}"
    if category == CATEGORY_AMBIGUOUS_METRIC_NAME:
        return "raw metric label is ambiguous and needs manual disambiguation before rule draft"
    if category == CATEGORY_NON_CORE_METRIC:
        return "metric is outside current core scope and should be deferred in this stage"
    if category == CATEGORY_DUPLICATE_OR_OVERLAPPING_MAPPING:
        return f"same asset/year/value already appears in 06 under metrics={','.join(overlap_metrics)}"
    if category == CATEGORY_DERIVED_METRIC_NOT_DIRECT_MAPPING:
        return f"{standard_metric} is treated as derived/ratio metric and needs dedicated derived rule"
    if category == CATEGORY_PACKAGE_SPECIFIC_MAPPING_GAP:
        return "gap appears package-specific and should be handled by package-scoped rule"
    if category == CATEGORY_LIKELY_FALSE_POSITIVE:
        return "record lacks stable value context and is likely false positive"
    return "fallback_manual_review"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage4B classify mapping rule gaps before fixing.")
    parser.parse_args()

    if not STAGE4A_XLSX.exists():
        raise FileNotFoundError(f"Missing Stage4A inventory: {STAGE4A_XLSX}")
    if not STAGE4A_SUMMARY.exists():
        raise FileNotFoundError(f"Missing Stage4A summary: {STAGE4A_SUMMARY}")
    if not OFFICIAL_02B_PATH.exists():
        raise FileNotFoundError(f"Missing official 02B: {OFFICIAL_02B_PATH}")

    snapshot_before = _snapshot_hashes()

    p01 = _find_delivery_file("01_*.xlsx")
    p06 = _find_delivery_file("06_*.xlsx")
    p02 = _find_delivery_file("02_*.xlsx")
    p05 = _find_delivery_file("05_*.xlsx")
    _ = pd.read_excel(p01).fillna("")
    _ = pd.read_excel(p02).fillna("")
    _ = pd.read_excel(p05).fillna("")
    df06 = pd.read_excel(p06).fillna("")

    inv = pd.read_excel(STAGE4A_XLSX, sheet_name="stage4a_inventory").fillna("")
    stage4a_summary = json.loads(STAGE4A_SUMMARY.read_text(encoding="utf-8"))
    if not bool(stage4a_summary.get("stage4a_inventory_pass", False)):
        raise RuntimeError("Stage4A summary indicates pass=false, abort Stage4B classification.")

    mapping_df = inv[inv["recommended_stage4_action"].map(_norm) == "NEED_MAPPING_RULE_FIX"].copy()
    input_mapping_gap_count = len(mapping_df)

    detail_map, asset_05_file_map = _parse_05_context()
    overlap_map = _build_06_overlap_maps(df06)

    # Metric -> number of packages containing mapping gaps.
    metric_pkg = (
        mapping_df[["standard_metric", "asset_package"]]
        .drop_duplicates()
        .groupby("standard_metric")
        .size()
        .to_dict()
    )

    out_rows: List[Dict[str, Any]] = []
    for _, r in mapping_df.iterrows():
        issue_id = _norm(r.get("issue_id"))
        asset_package = _norm(r.get("asset_package"))
        standard_metric = _norm(r.get("standard_metric"))
        year = _norm(r.get("year"))
        source_layer = _norm(r.get("source_layer"))
        target_layer = _norm(r.get("target_layer"))
        current_value = _norm(r.get("current_value"))
        current_unit = _norm(r.get("current_unit"))

        key = _key(asset_package, standard_metric, year)
        details = detail_map.get(key, [])
        best_detail = _pick_best_detail(details)
        raw_metric_name = _norm(best_detail.get("raw_metric_name")) or standard_metric
        existing_mapping_status = _existing_mapping_status(best_detail)

        affects_05 = bool(existing_mapping_status in {"NO_05_DETAIL_CONTEXT", "MAPPED_IN_05_WITH_WEAK_CONTEXT"})
        affects_01 = True
        affects_06 = True

        ov_key = (asset_package, year, current_value)
        overlap_metrics = [m for m in overlap_map.get(ov_key, []) if _norm(m) != standard_metric]

        category = _classify_category(
            standard_metric=standard_metric,
            raw_metric_name=raw_metric_name,
            current_value=current_value,
            overlap_metrics=overlap_metrics,
            asset_count_by_metric=metric_pkg,
            asset_package=asset_package,
        )
        if category not in ALLOWED_CATEGORIES:
            category = CATEGORY_AMBIGUOUS_METRIC_NAME

        action = _decide_action(category)
        if action not in ALLOWED_ACTIONS:
            action = ACTION_NEED_MANUAL_MAPPING_REVIEW

        priority = _decide_priority(
            category=category,
            standard_metric=standard_metric,
            affects_06=affects_06,
            existing_mapping_status=existing_mapping_status,
            raw_metric_name=raw_metric_name,
            year=year,
            overlap_metrics=overlap_metrics,
        )
        if priority not in ALLOWED_PRIORITIES:
            priority = PRIORITY_MEDIUM

        likely_mapping_pattern = _likely_mapping_pattern(
            category=category,
            best_detail=best_detail,
            standard_metric=standard_metric,
            raw_metric_name=raw_metric_name,
        )
        action_reason = _action_reason(
            category=category,
            existing_mapping_status=existing_mapping_status,
            overlap_metrics=overlap_metrics,
            standard_metric=standard_metric,
        )

        out_rows.append(
            {
                "issue_id": issue_id,
                "asset_package": asset_package,
                "raw_metric_name": raw_metric_name,
                "standard_metric": standard_metric,
                "year": year,
                "source_layer": source_layer,
                "target_layer": target_layer,
                "current_value": current_value,
                "current_unit": current_unit,
                "existing_mapping_status": existing_mapping_status,
                "affects_05": bool(affects_05),
                "affects_01": bool(affects_01),
                "affects_06": bool(affects_06),
                "likely_mapping_pattern": likely_mapping_pattern,
                "mapping_gap_category": category,
                "priority": priority,
                "recommended_stage4b_action": action,
                "action_reason": action_reason,
            }
        )

    out_df = pd.DataFrame(out_rows).sort_values(
        by=["priority", "recommended_stage4b_action", "asset_package", "standard_metric", "year"],
        kind="mergesort",
    )

    counts_action = out_df["recommended_stage4b_action"].value_counts().to_dict() if not out_df.empty else {}
    counts_priority = out_df["priority"].value_counts().to_dict() if not out_df.empty else {}
    counts_category = out_df["mapping_gap_category"].value_counts().to_dict() if not out_df.empty else {}

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
    delivery_status = _run_delivery_check().get("overall_status", "UNKNOWN")

    summary = {
        "input_mapping_gap_count": int(input_mapping_gap_count),
        "ready_for_mapping_rule_draft_count": int(counts_action.get(ACTION_READY_FOR_MAPPING_RULE_DRAFT, 0)),
        "need_manual_mapping_review_count": int(counts_action.get(ACTION_NEED_MANUAL_MAPPING_REVIEW, 0)),
        "defer_non_core_metric_count": int(counts_action.get(ACTION_DEFER_NON_CORE_METRIC, 0)),
        "reject_false_positive_count": int(counts_action.get(ACTION_REJECT_FALSE_POSITIVE, 0)),
        "need_derived_metric_rule_count": int(counts_action.get(ACTION_NEED_DERIVED_METRIC_RULE, 0)),
        "need_package_specific_rule_count": int(counts_action.get(ACTION_NEED_PACKAGE_SPECIFIC_RULE, 0)),
        "high_priority_count": int(counts_priority.get(PRIORITY_HIGH, 0)),
        "medium_priority_count": int(counts_priority.get(PRIORITY_MEDIUM, 0)),
        "low_priority_count": int(counts_priority.get(PRIORITY_LOW, 0)),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage4b_classification_pass": bool(
            input_mapping_gap_count == 118
            and production_files_unchanged
            and output_06_unchanged
            and official_02B_unchanged
            and delivery_status == "PASS"
        ),
        "delivery_status_after": delivery_status,
    }

    out_xlsx = OUT_DIR / "107_stage4b_mapping_gap_classification.xlsx"
    out_md = OUT_DIR / "107_stage4b_mapping_gap_classification.md"
    out_json = OUT_DIR / "108_stage4b_mapping_gap_classification_summary.json"

    category_dist_df = (
        out_df.groupby("mapping_gap_category", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(by=["count", "mapping_gap_category"], ascending=[False, True], kind="mergesort")
    )
    action_dist_df = (
        out_df.groupby("recommended_stage4b_action", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(by=["count", "recommended_stage4b_action"], ascending=[False, True], kind="mergesort")
    )
    priority_dist_df = (
        out_df.groupby("priority", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(by=["count", "priority"], ascending=[False, True], kind="mergesort")
    )

    _safe_write_excel_multi(
        {
            "stage4b_classification": out_df,
            "summary": pd.DataFrame([summary]),
            "category_distribution": category_dist_df,
            "action_distribution": action_dist_df,
            "priority_distribution": priority_dist_df,
            "category_raw_counts": pd.DataFrame(
                [{"mapping_gap_category": k, "count": int(v)} for k, v in sorted(counts_category.items())]
            ),
        },
        out_xlsx,
    )

    md_lines = [
        "# Stage4B Mapping Gap Classification",
        "",
        "## Summary",
        f"- input_mapping_gap_count: {summary['input_mapping_gap_count']}",
        f"- ready_for_mapping_rule_draft_count: {summary['ready_for_mapping_rule_draft_count']}",
        f"- need_manual_mapping_review_count: {summary['need_manual_mapping_review_count']}",
        f"- defer_non_core_metric_count: {summary['defer_non_core_metric_count']}",
        f"- reject_false_positive_count: {summary['reject_false_positive_count']}",
        f"- need_derived_metric_rule_count: {summary['need_derived_metric_rule_count']}",
        f"- need_package_specific_rule_count: {summary['need_package_specific_rule_count']}",
        f"- high_priority_count: {summary['high_priority_count']}",
        f"- medium_priority_count: {summary['medium_priority_count']}",
        f"- low_priority_count: {summary['low_priority_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- output_06_unchanged: {summary['output_06_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- delivery_status_after: {summary['delivery_status_after']}",
        f"- stage4b_classification_pass: {summary['stage4b_classification_pass']}",
        "",
        "## Notes",
        f"- Stage4A inventory source: {STAGE4A_XLSX.name}",
        f"- 05 detail context loaded from packages: {len(asset_05_file_map)}",
    ]
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md_lines), encoding="utf-8")
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage4b_classification_xlsx: {out_xlsx}")
    print(f"stage4b_classification_md: {out_md}")
    print(f"stage4b_classification_summary_json: {out_json}")
    for k in [
        "input_mapping_gap_count",
        "ready_for_mapping_rule_draft_count",
        "need_manual_mapping_review_count",
        "defer_non_core_metric_count",
        "reject_false_positive_count",
        "need_derived_metric_rule_count",
        "need_package_specific_rule_count",
        "high_priority_count",
        "medium_priority_count",
        "low_priority_count",
        "production_files_unchanged",
        "output_06_unchanged",
        "official_02B_unchanged",
        "stage4b_classification_pass",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

