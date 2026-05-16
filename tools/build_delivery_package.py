import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output")
DEFAULT_DELIVERY_DIR = Path(r"D:\_datefac\output\delivery_package")

TIER_PRIORITY = {
    "A_usable": 6,
    "B_partial_review": 5,
    "C_label_only_untrusted": 4,
    "D_insufficient": 3,
    "E_hard_sample": 2,
    "": 1,
}

LOW_RISK_SUSPICIOUS_FLAGS = {
    "amount_percent_group_decoupled",
    "ignored_percent_year_group",
    "value_repair_applied",
    "repaired_from_label_value_glued",
    "trailing_number_from_matching_label",
    "numeric_tail_if_source_label_exact",
}

HIGH_RISK_FLAGS = {
    "source_row_semantic_mismatch",
    "forbidden_account_row_as_metric_source",
    "multiple_mixed_text_source",
    "mixed_text_values",
    "likely_wrong_row",
    "non_numeric_value",
    "label_value_glued",
    "amount_has_percent",
    "invalid_ratio_too_large",
    "invalid_eps_too_large",
    "suspicious_pb_too_large",
}


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _to_int(v, default: int = -1) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def _to_bool(v) -> bool:
    return _norm(v).lower() in {"1", "true", "yes", "y"}


def _tier_priority(v: str) -> int:
    return TIER_PRIORITY.get(_norm(v), 0)


def _method_priority(v: str) -> int:
    s = _norm(v).lower()
    if s == "exact":
        return 6
    if s == "synonym":
        return 5
    if s == "ev_prefix_noise_guard":
        return 4
    if s == "metric_candidate_scan":
        return 3
    if "fallback" in s:
        return 2
    return 1


def _to_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _split_flags(v) -> List[str]:
    s = _norm(v)
    if not s:
        return []
    return [x.strip() for x in s.split("|") if x.strip()]


def _assess_delivery_acceptance(
    value_validation_status: str,
    value_issue_flags: str,
    value_repair_applied,
    value_repair_strategy: str,
) -> Dict[str, str]:
    status = _norm(value_validation_status).lower()
    issue_flags = set(_split_flags(value_issue_flags))
    indicators = set(issue_flags)
    if _to_bool(value_repair_applied):
        indicators.add("value_repair_applied")
    strategy = _norm(value_repair_strategy)
    if strategy:
        indicators.add(strategy)
    warning_flags = "|".join(sorted(indicators))

    if status == "valid":
        return {
            "delivery_acceptance_level": "auto_trusted",
            "delivery_warning_flags": warning_flags,
            "delivery_acceptance_reason": "value_validation_status_valid",
            "_accepted": "1",
        }

    if status == "suspicious":
        if issue_flags & HIGH_RISK_FLAGS:
            return {
                "delivery_acceptance_level": "manual_review_required",
                "delivery_warning_flags": warning_flags,
                "delivery_acceptance_reason": "suspicious_with_high_risk_flags",
                "_accepted": "0",
            }
        if indicators and indicators.issubset(LOW_RISK_SUSPICIOUS_FLAGS):
            return {
                "delivery_acceptance_level": "auto_usable_with_warning",
                "delivery_warning_flags": warning_flags,
                "delivery_acceptance_reason": "suspicious_with_low_risk_flags_only",
                "_accepted": "1",
            }
        return {
            "delivery_acceptance_level": "manual_review_required",
            "delivery_warning_flags": warning_flags,
            "delivery_acceptance_reason": "suspicious_with_unknown_or_unapproved_flags",
            "_accepted": "0",
        }

    if status == "invalid":
        has_hard = bool(issue_flags & HIGH_RISK_FLAGS)
        return {
            "delivery_acceptance_level": "blocked_invalid" if has_hard else "manual_review_required",
            "delivery_warning_flags": warning_flags,
            "delivery_acceptance_reason": "invalid_with_hard_flags" if has_hard else "invalid_without_hard_flags",
            "_accepted": "0",
        }

    return {
        "delivery_acceptance_level": "manual_review_required",
        "delivery_warning_flags": warning_flags,
        "delivery_acceptance_reason": "missing_or_unknown_validation_status",
        "_accepted": "0",
    }


def _safe_read_excel(path: Optional[Path], sheet_name: str) -> pd.DataFrame:
    if not path or not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl").fillna("")
    except Exception:
        return pd.DataFrame()


def _find_report_file(output_dir: Path, preferred_name: str, prefix: str) -> Optional[Path]:
    p = output_dir / preferred_name
    if p.exists():
        return p
    matches = sorted(output_dir.glob(f"{prefix}*.xlsx"))
    return matches[0] if matches else None


def _safe_write_excel(df: pd.DataFrame, path: Path) -> Path:
    final_path = path
    if path.exists():
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(final_path, index=False, engine="openpyxl")
    return final_path


def _safe_write_text(text: str, path: Path) -> Path:
    final_path = path
    if path.exists():
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(text, encoding="utf-8")
    return final_path


def _build_pdf_map(df24_summary: pd.DataFrame, df26_regions: pd.DataFrame, df08_raw_quality: pd.DataFrame) -> Dict[str, str]:
    m: Dict[str, str] = {}
    for df, col in [(df24_summary, "source_pdf"), (df26_regions, "source_pdf"), (df08_raw_quality, "source_pdf")]:
        if df.empty or col not in df.columns or "asset_package" not in df.columns:
            continue
        for _, r in df.iterrows():
            ap = _norm(r.get("asset_package"))
            sp = _norm(r.get(col))
            if ap and sp and ap not in m:
                m[ap] = Path(sp).name
    return m


def _build_crop_lookup(df26_regions: pd.DataFrame) -> Dict[Tuple[str, int], Dict[str, str]]:
    lookup: Dict[Tuple[str, int], Dict[str, str]] = {}
    if df26_regions.empty:
        return lookup
    for _, r in df26_regions.iterrows():
        ap = _norm(r.get("asset_package"))
        tidx = _to_int(r.get("table_index"))
        if not ap or tidx < 0:
            continue
        key = (ap, tidx)
        cur = lookup.get(key)
        cand = {
            "crop_png_path": _norm(r.get("crop_png_path")),
            "review_reason": _norm(r.get("review_reason")),
            "needs_manual_review": _norm(r.get("needs_manual_review")),
            "linked_invalid_metric_count": _norm(r.get("linked_invalid_metric_count")),
        }
        if cur is None:
            lookup[key] = cand
        else:
            # Prefer rows with existing crop path.
            if not _norm(cur.get("crop_png_path")) and _norm(cand.get("crop_png_path")):
                lookup[key] = cand
    return lookup


def _resolve_year_columns(df08_fin_metrics: pd.DataFrame) -> List[str]:
    ignore = {
        "asset_package",
        "标准指标",
        "source_row_label",
        "source_table_index",
        "source_table_type",
        "source_row_index",
        "source_label_column",
        "label_detect_method",
        "source_column",
        "matched_alias",
        "match_method",
        "confidence",
        "non_empty_year_count",
        "raw_year_values",
        "value_repair_applied",
        "value_repair_strategy",
        "value_repair_issue_flags",
        "repaired_year_count",
        "value_validation_status",
        "value_issue_flags",
        "valid_year_count",
        "invalid_year_count",
        "header_repaired",
        "header_source_row",
    }
    year_cols: List[str] = []
    for c in df08_fin_metrics.columns:
        cs = _norm(c)
        if cs in ignore:
            continue
        if any(ch.isdigit() for ch in cs):
            year_cols.append(cs)
    return year_cols


def _infer_unit(metric: str) -> str:
    if metric in {"毛利率", "ROE"}:
        return "%"
    if metric in {"P/E", "P/B", "EV/EBITDA"}:
        return "x"
    return ""


def _build_trusted_metrics(
    df08_fin_metrics: pd.DataFrame,
    df23_assets: pd.DataFrame,
    df24_summary: pd.DataFrame,
    df26_regions: pd.DataFrame,
    pdf_map: Dict[str, str],
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    if df08_fin_metrics.empty:
        return pd.DataFrame(
            columns=[
                "source_pdf",
                "asset_package",
                "report_type",
                "data_usability_tier",
                "standard_metric",
                "year",
                "value",
                "unit",
                "value_validation_status",
                "value_repair_applied",
                "source_row_label",
                "source_table_index",
                "source_row_index",
                "source_column",
                "evidence_crop_path",
                "trace_note",
                "delivery_acceptance_level",
                "delivery_warning_flags",
                "delivery_acceptance_reason",
            ]
        ), {
            "trusted_rows_before": 0,
            "auto_trusted_count": 0,
            "auto_usable_with_warning_count": 0,
            "manual_review_required_count": 0,
            "blocked_invalid_count": 0,
        }

    year_cols = _resolve_year_columns(df08_fin_metrics)
    crop_lookup = _build_crop_lookup(df26_regions)

    tier_map = {}
    for _, r in df23_assets.iterrows():
        ap = _norm(r.get("asset_package"))
        if ap:
            tier_map[ap] = {
                "data_usability_tier": _norm(r.get("data_usability_tier")),
                "report_type": _norm(r.get("report_type")),
            }
    for _, r in df24_summary.iterrows():
        ap = _norm(r.get("asset_package"))
        if ap and ap in tier_map and not tier_map[ap].get("report_type"):
            tier_map[ap]["report_type"] = _norm(r.get("report_type"))
        elif ap and ap not in tier_map:
            tier_map[ap] = {
                "data_usability_tier": "",
                "report_type": _norm(r.get("report_type")),
            }

    out_rows: List[Dict[str, str]] = []
    acceptance_stats = {
        "trusted_rows_before": 0,
        "auto_trusted_count": 0,
        "auto_usable_with_warning_count": 0,
        "manual_review_required_count": 0,
        "blocked_invalid_count": 0,
    }

    for source_order, (_, r) in enumerate(df08_fin_metrics.iterrows()):
        acceptance = _assess_delivery_acceptance(
            value_validation_status=_norm(r.get("value_validation_status")),
            value_issue_flags=_norm(r.get("value_issue_flags")),
            value_repair_applied=r.get("value_repair_applied"),
            value_repair_strategy=_norm(r.get("value_repair_strategy")),
        )

        ap = _norm(r.get("asset_package"))
        metric = _norm(r.get("standard_metric")) or _norm(r.get("标准指标")) or _norm(r.get("鏍囧噯鎸囨爣"))
        if not metric:
            for c in r.index.tolist():
                cs = _norm(c)
                if cs.lower() == "standard_metric" or ("标准指标" in cs) or ("鏍囧噯鎸囨爣" in cs):
                    metric = _norm(r.get(c))
                    if metric:
                        break
        source_table_index = _to_int(r.get("source_table_index"))
        source_row_index = _to_int(r.get("source_row_index"))
        source_col = _norm(r.get("source_column"))
        source_label = _norm(r.get("source_row_label"))
        value_issue_flags = _norm(r.get("value_issue_flags"))
        value_repair_strategy = _norm(r.get("value_repair_strategy"))
        valid_year_count = _to_int(r.get("valid_year_count"), 0)
        confidence = _to_float(r.get("confidence"), 0.0)
        match_method = _norm(r.get("match_method"))

        evidence_crop = ""
        if (ap, source_table_index) in crop_lookup:
            evidence_crop = _norm(crop_lookup[(ap, source_table_index)].get("crop_png_path"))

        for y in year_cols:
            sval = _norm(r.get(y))
            if not sval:
                continue

            level = acceptance["delivery_acceptance_level"]
            counter_key = f"{level}_count"
            if counter_key in acceptance_stats:
                acceptance_stats[counter_key] += 1
            if acceptance.get("_accepted") != "1":
                continue

            acceptance_stats["trusted_rows_before"] += 1
            out_rows.append(
                {
                    "source_pdf": pdf_map.get(ap, ""),
                    "asset_package": ap,
                    "report_type": tier_map.get(ap, {}).get("report_type", ""),
                    "data_usability_tier": tier_map.get(ap, {}).get("data_usability_tier", ""),
                    "standard_metric": metric,
                    "year": y,
                    "value": sval,
                    "unit": _infer_unit(metric),
                    "value_validation_status": _norm(r.get("value_validation_status")),
                    "value_issue_flags": value_issue_flags,
                    "value_repair_applied": _norm(r.get("value_repair_applied")),
                    "value_repair_strategy": value_repair_strategy,
                    "source_row_label": source_label,
                    "source_table_index": source_table_index if source_table_index >= 0 else "",
                    "source_row_index": source_row_index if source_row_index >= 0 else "",
                    "source_column": source_col,
                    "valid_year_count": valid_year_count,
                    "confidence": confidence,
                    "match_method": match_method,
                    "evidence_crop_path": evidence_crop,
                    "trace_note": "08.financial_metrics accepted candidate",
                    "delivery_acceptance_level": acceptance["delivery_acceptance_level"],
                    "delivery_warning_flags": acceptance["delivery_warning_flags"],
                    "delivery_acceptance_reason": acceptance["delivery_acceptance_reason"],
                    "_source_order": source_order,
                }
            )

    return pd.DataFrame(out_rows), acceptance_stats


def _dedupe_trusted_metrics(trusted_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, int]]:
    base_cols = [
        "conflict_key",
        "asset_package",
        "standard_metric",
        "year",
        "kept",
        "dedupe_rank",
        "dedupe_reason",
        "value",
        "value_validation_status",
        "value_issue_flags",
        "value_repair_applied",
        "value_repair_strategy",
        "source_row_label",
        "source_table_index",
        "source_row_index",
        "source_column",
        "evidence_crop_path",
        "report_type",
        "data_usability_tier",
    ]
    if trusted_df.empty:
        return trusted_df, pd.DataFrame(columns=base_cols), {
            "trusted_metric_rows_before_dedupe": 0,
            "trusted_metric_rows_after_dedupe": 0,
            "duplicate_key_count_before_dedupe": 0,
            "duplicate_key_count_after_dedupe": 0,
            "conflict_group_count": 0,
            "conflict_detail_rows": 0,
        }

    df = trusted_df.copy().reset_index(drop=True)
    if "_source_order" not in df.columns:
        df["_source_order"] = list(range(len(df)))

    # Sorting priority for deterministic best-record selection.
    df["_pri_valid"] = df["value_validation_status"].map(lambda x: 1 if _norm(x).lower() == "valid" else 0)
    df["_pri_tier"] = df["data_usability_tier"].map(_tier_priority)
    df["_pri_issue_empty"] = df["value_issue_flags"].map(lambda x: 1 if not _norm(x) else 0)
    df["_pri_valid_year"] = df.get("valid_year_count", 0).map(lambda x: _to_int(x, 0))
    df["_pri_conf"] = df.get("confidence", 0).map(lambda x: _to_float(x, 0.0))
    df["_pri_method"] = df.get("match_method", "").map(_method_priority)
    df["_pri_not_repair"] = df.get("value_repair_applied", "").map(lambda x: 1 if not _to_bool(x) else 0)
    df["_pri_evidence"] = df["evidence_crop_path"].map(lambda x: 1 if _norm(x) else 0)
    df["_pri_source_table"] = df["source_table_index"].map(lambda x: _to_int(x, 999999))
    df["_pri_source_row"] = df["source_row_index"].map(lambda x: _to_int(x, 999999))
    df["_pri_source_order"] = df["_source_order"].map(lambda x: _to_int(x, 999999))

    sort_cols = [
        "_pri_valid",
        "_pri_tier",
        "_pri_issue_empty",
        "_pri_valid_year",
        "_pri_conf",
        "_pri_method",
        "_pri_not_repair",
        "_pri_evidence",
    ]
    asc_flags = [False, False, False, False, False, False, False, False]

    key_cols = ["asset_package", "standard_metric", "year"]
    conflict_rows: List[Dict[str, object]] = []
    kept_rows: List[pd.Series] = []
    duplicate_key_count_before = 0
    conflict_group_count = 0

    grouped = df.groupby(key_cols, dropna=False, sort=False)
    for key_vals, grp in grouped:
        g = grp.copy()
        if len(g) > 1:
            duplicate_key_count_before += 1
            conflict_group_count += 1
        g = g.sort_values(
            by=sort_cols + ["_pri_source_table", "_pri_source_row", "_pri_source_order"],
            ascending=asc_flags + [True, True, True],
            kind="mergesort",
        ).reset_index(drop=True)
        g["_rank"] = g.index + 1
        best_idx = 0
        kept_rows.append(g.iloc[best_idx])
        conflict_key = f"{_norm(key_vals[0])}|{_norm(key_vals[1])}|{_norm(key_vals[2])}"
        for _, row in g.iterrows():
            kept = int(row["_rank"]) == 1
            conflict_rows.append(
                {
                    "conflict_key": conflict_key,
                    "asset_package": _norm(row.get("asset_package")),
                    "standard_metric": _norm(row.get("standard_metric")),
                    "year": _norm(row.get("year")),
                    "kept": bool(kept),
                    "dedupe_rank": int(row.get("_rank", 0)),
                    "dedupe_reason": "best_by_valid_status_tier_confidence_evidence"
                    if kept
                    else "duplicate_lower_rank",
                    "value": _norm(row.get("value")),
                    "value_validation_status": _norm(row.get("value_validation_status")),
                    "value_issue_flags": _norm(row.get("value_issue_flags")),
                    "value_repair_applied": _norm(row.get("value_repair_applied")),
                    "value_repair_strategy": _norm(row.get("value_repair_strategy")),
                    "source_row_label": _norm(row.get("source_row_label")),
                    "source_table_index": _norm(row.get("source_table_index")),
                    "source_row_index": _norm(row.get("source_row_index")),
                    "source_column": _norm(row.get("source_column")),
                    "evidence_crop_path": _norm(row.get("evidence_crop_path")),
                    "report_type": _norm(row.get("report_type")),
                    "data_usability_tier": _norm(row.get("data_usability_tier")),
                }
            )

    deduped_df = pd.DataFrame(kept_rows).reset_index(drop=True)
    drop_cols = [c for c in deduped_df.columns if c.startswith("_pri_") or c in {"_rank", "_source_order"}]
    deduped_df = deduped_df.drop(columns=drop_cols, errors="ignore")
    conflict_df = pd.DataFrame(conflict_rows)
    duplicate_key_count_after = int(deduped_df.duplicated(subset=key_cols, keep=False).sum() / 2) if not deduped_df.empty else 0

    stats = {
        "trusted_metric_rows_before_dedupe": int(len(df)),
        "trusted_metric_rows_after_dedupe": int(len(deduped_df)),
        "duplicate_key_count_before_dedupe": int(duplicate_key_count_before),
        "duplicate_key_count_after_dedupe": int(
            deduped_df.groupby(key_cols, dropna=False).size().gt(1).sum() if not deduped_df.empty else 0
        ),
        "conflict_group_count": int(conflict_group_count),
        "conflict_detail_rows": int(len(conflict_df)),
    }
    return deduped_df, conflict_df, stats


def _build_manual_review(
    df22_metric_queue: pd.DataFrame,
    df22_invalid: pd.DataFrame,
    df26_regions: pd.DataFrame,
) -> pd.DataFrame:
    crop_lookup = _build_crop_lookup(df26_regions)
    out_rows: List[Dict[str, str]] = []

    for _, r in df22_metric_queue.iterrows():
        ap = _norm(r.get("asset_package"))
        tidx = _to_int(r.get("source_table_index"))
        evidence = _norm(crop_lookup.get((ap, tidx), {}).get("crop_png_path", ""))
        out_rows.append(
            {
                "asset_package": ap,
                "standard_metric": _norm(r.get("standard_metric")),
                "metric_value_status": _norm(r.get("metric_value_status")),
                "value_issue_flags": _norm(r.get("value_issue_flags")),
                "raw_value_examples": _norm(r.get("raw_value_examples")),
                "source_row_label": _norm(r.get("source_row_label")),
                "source_table_index": tidx if tidx >= 0 else "",
                "source_row_index": _to_int(r.get("source_row_index"), default=""),
                "recommendation": _norm(r.get("recommendation")),
                "evidence_crop_path": evidence,
                "source": "metric_review_queue",
            }
        )

    for _, r in df22_invalid.iterrows():
        ap = _norm(r.get("asset_package"))
        tidx = _to_int(r.get("source_table_index"))
        evidence = _norm(crop_lookup.get((ap, tidx), {}).get("crop_png_path", ""))
        raw_val = _norm(r.get("raw_value"))
        out_rows.append(
            {
                "asset_package": ap,
                "standard_metric": _norm(r.get("standard_metric")),
                "metric_value_status": "invalid",
                "value_issue_flags": _norm(r.get("issue_flags")),
                "raw_value_examples": raw_val,
                "source_row_label": _norm(r.get("source_row_label")),
                "source_table_index": tidx if tidx >= 0 else "",
                "source_row_index": _to_int(r.get("source_row_index"), default=""),
                "recommendation": _norm(r.get("recommendation")),
                "evidence_crop_path": evidence,
                "source": "invalid_value_examples",
            }
        )
    return pd.DataFrame(out_rows)


def _build_excluded_or_failed(
    df23_assets: pd.DataFrame,
    df24_summary: pd.DataFrame,
    df08_summary: pd.DataFrame,
    pdf_map: Dict[str, str],
) -> pd.DataFrame:
    m24 = {}
    for _, r in df24_summary.iterrows():
        ap = _norm(r.get("asset_package"))
        if ap:
            m24[ap] = {
                "source_pdf": _norm(r.get("source_pdf")),
                "report_type": _norm(r.get("report_type")),
                "target_applicability": _norm(r.get("target_applicability")),
                "should_include_in_8_metric_eval": _norm(r.get("should_include_in_8_metric_eval")),
                "reason": _norm(r.get("reason")),
                "recommendation": _norm(r.get("recommendation")),
            }
    m08 = {}
    for _, r in df08_summary.iterrows():
        ap = _norm(r.get("asset_package"))
        if ap:
            m08[ap] = {
                "missing_core_artifacts": _norm(r.get("missing_core_artifacts")),
                "recommendation": _norm(r.get("recommendation")),
                "eval_scope": _norm(r.get("eval_scope")),
            }
    out_rows: List[Dict[str, str]] = []
    for _, r in df23_assets.iterrows():
        ap = _norm(r.get("asset_package"))
        tier = _norm(r.get("data_usability_tier"))
        report_type = _norm(r.get("report_type")) or _norm(m24.get(ap, {}).get("report_type"))
        target_app = _norm(r.get("target_applicability")) or _norm(m24.get(ap, {}).get("target_applicability"))
        in_eval = _norm(r.get("should_include_in_8_metric_eval")) or _norm(
            m24.get(ap, {}).get("should_include_in_8_metric_eval")
        )
        missing_core = _norm(m08.get(ap, {}).get("missing_core_artifacts"))
        is_out_scope = str(in_eval).lower() in {"false", "0", "no"} or _norm(m08.get(ap, {}).get("eval_scope")) == "out_of_scope_non_target"
        is_failed_tier = tier in {"D_insufficient", "E_hard_sample"}
        has_core_missing = bool(missing_core)
        if not (is_out_scope or is_failed_tier or has_core_missing):
            continue
        out_rows.append(
            {
                "source_pdf": _norm(m24.get(ap, {}).get("source_pdf")) or pdf_map.get(ap, ""),
                "asset_package": ap,
                "report_type": report_type,
                "target_applicability": target_app,
                "should_include_in_8_metric_eval": in_eval,
                "data_usability_tier": tier,
                "reason": _norm(m24.get(ap, {}).get("reason")) or _norm(r.get("primary_bottleneck")) or missing_core,
                "recommendation": _norm(m24.get(ap, {}).get("recommendation"))
                or _norm(m08.get(ap, {}).get("recommendation"))
                or _norm(r.get("recommended_action")),
            }
        )
    return pd.DataFrame(out_rows)


def _build_region_index(df26_regions: pd.DataFrame) -> pd.DataFrame:
    if df26_regions.empty:
        return pd.DataFrame(
            columns=[
                "asset_package",
                "page_number",
                "table_index",
                "crop_png_path",
                "quality_level",
                "quality_flags",
                "needs_manual_review",
                "review_reason",
                "linked_invalid_metric_count",
            ]
        )
    cols = {
        "asset_package": "asset_package",
        "page_number": "page_number",
        "table_index": "table_index",
        "crop_png_path": "crop_png_path",
        "quality_level": "quality_level",
        "quality_flags": "quality_flags",
        "needs_manual_review": "needs_manual_review",
        "review_reason": "review_reason",
        "linked_invalid_metric_count": "linked_invalid_metric_count",
    }
    out = pd.DataFrame()
    for c, nc in cols.items():
        out[nc] = df26_regions[c] if c in df26_regions.columns else ""
    return out


def _build_summary_markdown(
    df24_scope: pd.DataFrame,
    df23_summary: pd.DataFrame,
    df23_assets: pd.DataFrame,
    trusted_rows: int,
    manual_rows: int,
    dedupe_stats: Optional[Dict[str, int]] = None,
    acceptance_stats: Optional[Dict[str, int]] = None,
) -> str:
    total_pdf = 0
    target = partial = non_target = unknown = 0
    if not df24_scope.empty:
        row = df24_scope.iloc[0].to_dict()
        total_pdf = _to_int(row.get("total_pdfs"), 0)
        target = _to_int(row.get("target_count"), 0)
        partial = _to_int(row.get("partial_count"), 0)
        non_target = _to_int(row.get("non_target_count"), 0)
        unknown = _to_int(row.get("unknown_count"), 0)

    tier_counts = {"A_usable": 0, "B_partial_review": 0, "C_label_only_untrusted": 0, "D_insufficient": 0, "E_hard_sample": 0}
    if not df23_assets.empty and "data_usability_tier" in df23_assets.columns:
        vc = df23_assets["data_usability_tier"].value_counts(dropna=False)
        for k in tier_counts.keys():
            tier_counts[k] = int(vc.get(k, 0))

    hard_sample_count = tier_counts["E_hard_sample"]
    dedupe_stats = dedupe_stats or {}
    acceptance_stats = acceptance_stats or {}

    before_rows = int(dedupe_stats.get("trusted_metric_rows_before_dedupe", trusted_rows))
    after_rows = int(dedupe_stats.get("trusted_metric_rows_after_dedupe", trusted_rows))
    duplicate_groups = int(dedupe_stats.get("duplicate_key_count_before_dedupe", 0))
    conflict_detail_rows = int(dedupe_stats.get("conflict_detail_rows", 0))
    duplicate_after = int(dedupe_stats.get("duplicate_key_count_after_dedupe", 0))

    auto_trusted_count = int(acceptance_stats.get("auto_trusted_count", 0))
    auto_usable_with_warning_count = int(acceptance_stats.get("auto_usable_with_warning_count", 0))
    manual_review_required_count = int(acceptance_stats.get("manual_review_required_count", 0))
    blocked_invalid_count = int(acceptance_stats.get("blocked_invalid_count", 0))

    lines = [
        "# 处理摘要",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 本次处理 PDF 数：{total_pdf}",
        f"- 目标报告数量：{target + partial}",
        f"- 非目标报告数量：{non_target}",
        f"- 未知类型数量：{unknown}",
        "",
        "## A/B/C/D/E 分布",
        f"- A_usable：{tier_counts['A_usable']}",
        f"- B_partial_review：{tier_counts['B_partial_review']}",
        f"- C_label_only_untrusted：{tier_counts['C_label_only_untrusted']}",
        f"- D_insufficient：{tier_counts['D_insufficient']}",
        f"- E_hard_sample：{tier_counts['E_hard_sample']}",
        "",
        f"- 自动可信指标数量：{trusted_rows}",
        f"- auto_trusted 指标数量：{auto_trusted_count}",
        f"- auto_usable_with_warning 指标数量：{auto_usable_with_warning_count}",
        f"- manual_review_required 指标数量：{manual_review_required_count}",
        f"- blocked_invalid 指标数量：{blocked_invalid_count}",
        f"- 需人工复核指标数量：{manual_rows}",
        f"- hard sample 数量：{hard_sample_count}",
        "- auto_usable_with_warning 表示低风险自动解耦结果，可自动纳入但不等于人工确认。",
        "",
        "## 交付去重质量",
        f"- 自动可信指标原始行数：{before_rows}",
        f"- 自动可信指标去重后行数：{after_rows}",
        f"- 重复键组数：{duplicate_groups}",
        f"- 冲突候选行数：{conflict_detail_rows}",
        f"- 是否存在阻断级重复：{'否' if duplicate_after == 0 else '是'}",
        "",
        "## 当前能力边界",
        "- 当前交付包纳入 valid 与低风险 suspicious 指标。",
        "- B/D/E 与非目标报告仍需人工复核或专用流程处理。",
        "- 当前不是全自动无人工复核系统。",
    ]
    return "\n".join(lines) + "\n"


def build_delivery_package(output_dir: Path, delivery_dir: Path) -> Dict[str, object]:
    p08 = _find_report_file(output_dir, "08_批量回归报告.xlsx", "08_")
    p19 = _find_report_file(output_dir, "19_financial_value_validation_report.xlsx", "19_")
    p22 = _find_report_file(output_dir, "22_manual_review_queue.xlsx", "22_")
    p23 = _find_report_file(output_dir, "23_baseline_evaluation_report.xlsx", "23_")
    p24 = _find_report_file(output_dir, "24_report_type_diagnostics.xlsx", "24_")
    p26 = _find_report_file(output_dir, "26_table_region_asset_quality_report.xlsx", "26_")

    df08_summary = _safe_read_excel(p08, "summary")
    df08_fin_metrics = _safe_read_excel(p08, "financial_metrics")
    df08_raw_quality = _safe_read_excel(p08, "raw_table_quality")

    _ = _safe_read_excel(p19, "metric_value_details")  # optional; currently not mandatory for outputs
    df22_metric_queue = _safe_read_excel(p22, "metric_review_queue")
    df22_invalid = _safe_read_excel(p22, "invalid_value_examples")
    df22_hard = _safe_read_excel(p22, "hard_samples")

    df23_summary = _safe_read_excel(p23, "baseline_summary")
    df23_assets = _safe_read_excel(p23, "asset_quality_matrix")
    df24_summary = _safe_read_excel(p24, "report_type_summary")
    df24_scope = _safe_read_excel(p24, "eval_scope_recommendation")
    df26_regions = _safe_read_excel(p26, "region_quality_details")

    pdf_map = _build_pdf_map(df24_summary, df26_regions, df08_raw_quality)

    trusted_df_before, acceptance_stats = _build_trusted_metrics(df08_fin_metrics, df23_assets, df24_summary, df26_regions, pdf_map)
    trusted_df, trusted_conflict_df, dedupe_stats = _dedupe_trusted_metrics(trusted_df_before)
    manual_df = _build_manual_review(df22_metric_queue, df22_invalid, df26_regions)
    excluded_df = _build_excluded_or_failed(df23_assets, df24_summary, df08_summary, pdf_map)
    region_idx_df = _build_region_index(df26_regions)

    delivery_dir.mkdir(parents=True, exist_ok=True)
    p1 = _safe_write_excel(trusted_df, delivery_dir / "01_自动可信核心指标.xlsx")
    p1a = _safe_write_excel(trusted_conflict_df, delivery_dir / "01A_自动可信核心指标冲突明细.xlsx")
    p2 = _safe_write_excel(manual_df, delivery_dir / "02_人工复核指标队列.xlsx")
    p3 = _safe_write_excel(excluded_df, delivery_dir / "03_非目标报告与失败说明.xlsx")
    p5 = _safe_write_excel(region_idx_df, delivery_dir / "05_表格区域截图索引.xlsx")

    summary_md = _build_summary_markdown(
        df24_scope,
        df23_summary,
        df23_assets,
        len(trusted_df),
        len(manual_df),
        dedupe_stats=dedupe_stats,
        acceptance_stats=acceptance_stats,
    )
    p4 = _safe_write_text(summary_md, delivery_dir / "04_处理摘要.md")

    return {
        "delivery_dir": str(delivery_dir),
        "trusted_metric_rows_before_dedupe": int(dedupe_stats.get("trusted_metric_rows_before_dedupe", len(trusted_df_before))),
        "trusted_metric_rows_after_dedupe": int(dedupe_stats.get("trusted_metric_rows_after_dedupe", len(trusted_df))),
        "duplicate_key_count_after_dedupe": int(dedupe_stats.get("duplicate_key_count_after_dedupe", 0)),
        "conflict_detail_rows": int(dedupe_stats.get("conflict_detail_rows", 0)),
        "conflict_group_count": int(dedupe_stats.get("conflict_group_count", 0)),
        "trusted_metric_rows": int(len(trusted_df)),
        "manual_review_rows": int(len(manual_df)),
        "excluded_or_failed_rows": int(len(excluded_df)),
        "table_region_index_rows": int(len(region_idx_df)),
        "trusted_rows_before": int(acceptance_stats.get("trusted_rows_before", 0)),
        "auto_trusted_count": int(acceptance_stats.get("auto_trusted_count", 0)),
        "auto_usable_with_warning_count": int(acceptance_stats.get("auto_usable_with_warning_count", 0)),
        "manual_review_required_count": int(acceptance_stats.get("manual_review_required_count", 0)),
        "blocked_invalid_count": int(acceptance_stats.get("blocked_invalid_count", 0)),
        "summary_md_path": str(p4),
        "conflict_detail_path": str(p1a),
        "output_files": [str(p1), str(p1a), str(p2), str(p3), str(p4), str(p5)],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build clean delivery package from existing reports/artifacts.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--delivery-dir", default=str(DEFAULT_DELIVERY_DIR))
    args = parser.parse_args()

    result = build_delivery_package(Path(args.output_dir), Path(args.delivery_dir))
    print(f"delivery_dir: {result['delivery_dir']}")
    print(f"trusted_metric_rows_before_dedupe: {result['trusted_metric_rows_before_dedupe']}")
    print(f"trusted_rows_before: {result['trusted_rows_before']}")
    print(f"auto_trusted_count: {result['auto_trusted_count']}")
    print(f"auto_usable_with_warning_count: {result['auto_usable_with_warning_count']}")
    print(f"manual_review_required_count: {result['manual_review_required_count']}")
    print(f"blocked_invalid_count: {result['blocked_invalid_count']}")
    print(f"trusted_metric_rows_after_dedupe: {result['trusted_metric_rows_after_dedupe']}")
    print(f"duplicate_key_count_after_dedupe: {result['duplicate_key_count_after_dedupe']}")
    print(f"conflict_detail_rows: {result['conflict_detail_rows']}")
    print(f"conflict_group_count: {result['conflict_group_count']}")
    print(f"trusted_metric_rows: {result['trusted_metric_rows']}")
    print(f"manual_review_rows: {result['manual_review_rows']}")
    print(f"excluded_or_failed_rows: {result['excluded_or_failed_rows']}")
    print(f"table_region_index_rows: {result['table_region_index_rows']}")
    print(f"conflict_detail_path: {result['conflict_detail_path']}")
    print(f"summary_md_path: {result['summary_md_path']}")


if __name__ == "__main__":
    main()


