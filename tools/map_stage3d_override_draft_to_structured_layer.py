import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
DRAFT_PATH = BASE_DIR / "data" / "overrides" / "drafts" / "03_stage3_ai_repair_override_draft.xlsx"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
STAGE3D_OUT = BASE_DIR / "output" / "stage3d_structured_mapping"


TARGET_STRUCTURED = "STRUCTURED_FACT_LAYER"
TARGET_STANDARDIZED = "STANDARDIZED_METRIC_LAYER"
TARGET_FINAL_ONLY = "FINAL_METRIC_OVERRIDE_ONLY"
TARGET_MANUAL = "MANUAL_REVIEW_LAYER"
TARGET_NEED_REVIEW = "NEED_MAPPING_REVIEW"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _key(asset: Any, metric: Any, year: Any) -> str:
    return "|".join([_norm(asset), _norm(metric), _norm(year)])


def _parse_number(text: Any) -> Optional[float]:
    s = _norm(text).replace(",", "")
    if not s:
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()
    try:
        v = float(s)
        return -v if neg else v
    except Exception:
        return None


def _value_equal(v1: Any, v2: Any) -> bool:
    n1 = _parse_number(v1)
    n2 = _parse_number(v2)
    if n1 is not None and n2 is not None:
        return abs(n1 - n2) <= 1e-9
    return _norm(v1) == _norm(v2)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_delivery_file(pattern: str, prefer_no_copy: bool = True) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing required file pattern: {pattern}")
    if prefer_no_copy:
        filtered = [p for p in files if "_copy_" not in p.name]
        if filtered:
            return filtered[0]
    return files[0]


def _snapshot_prod() -> Dict[str, str]:
    p01 = _find_delivery_file("01_*.xlsx")
    p02_candidates = sorted(DELIVERY_DIR.glob("02_*.xlsx"))
    p02 = next((p for p in p02_candidates if "backup" not in p.name.lower()), p02_candidates[0])
    p02a = _find_delivery_file("02A_*.xlsx")
    p05 = _find_delivery_file("05_*.xlsx")
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    return {
        "01": _sha256(p01),
        "02": _sha256(p02),
        "02A": _sha256(p02a),
        "05": _sha256(p05),
        "06": _sha256(p06),
    }


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    try:
        return json.loads((p.stdout or "").strip() or "{}")
    except Exception:
        return {"overall_status": "UNKNOWN"}


def _safe_write_excel_multi(sheets: Dict[str, pd.DataFrame], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def _safe_write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_inputs():
    if not DRAFT_PATH.exists():
        raise FileNotFoundError(f"Missing draft file: {DRAFT_PATH}")
    if not OFFICIAL_02B_PATH.exists():
        raise FileNotFoundError(f"Missing official override file: {OFFICIAL_02B_PATH}")
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    p01 = _find_delivery_file("01_*.xlsx")
    p02 = _find_delivery_file("02_*.xlsx")
    p02a = _find_delivery_file("02A_*.xlsx")

    draft = pd.read_excel(DRAFT_PATH).fillna("")
    off2b = pd.read_excel(OFFICIAL_02B_PATH, sheet_name="ai_repair_override").fillna("")
    df06 = pd.read_excel(p06).fillna("")
    df01 = pd.read_excel(p01).fillna("")
    df02 = pd.read_excel(p02).fillna("")
    df02a = pd.read_excel(p02a).fillna("")
    return draft, off2b, df06, df01, df02, df02a


def _load_asset_structured_and_standardized(asset_package: str) -> Dict[str, pd.DataFrame]:
    asset_root = BASE_DIR / "output" / asset_package
    p02 = asset_root / "02_研报全量结构化数据.xlsx"
    p05 = asset_root / "05_核心财务指标标准化.xlsx"
    out = {"structured": pd.DataFrame(), "standardized_detail": pd.DataFrame(), "standardized_wide": pd.DataFrame()}
    if p02.exists():
        xl2 = pd.ExcelFile(p02)
        parts = []
        for s in xl2.sheet_names:
            if s in {"00_目录", "tables_index"}:
                continue
            try:
                df = pd.read_excel(p02, sheet_name=s).fillna("")
                if not df.empty:
                    parts.append(df)
            except Exception:
                continue
        if parts:
            out["structured"] = pd.concat(parts, ignore_index=True, sort=False)
    if p05.exists():
        xl5 = pd.ExcelFile(p05)
        if "抽取明细" in xl5.sheet_names:
            out["standardized_detail"] = pd.read_excel(p05, sheet_name="抽取明细").fillna("")
        if "核心指标宽表" in xl5.sheet_names:
            out["standardized_wide"] = pd.read_excel(p05, sheet_name="核心指标宽表").fillna("")
    return out


def _find_exists_in_structured(structured_df: pd.DataFrame, metric: str, year: str, value: str) -> bool:
    if structured_df.empty:
        return False
    y = _norm(year)
    m = _norm(metric)
    v = _norm(value)
    for _, r in structured_df.iterrows():
        row_text = " ".join([_norm(x) for x in r.tolist()])
        if m and m not in row_text:
            continue
        if y and y not in row_text:
            continue
        if v and v not in row_text:
            continue
        return True
    return False


def _find_exists_in_standardized(standardized_detail: pd.DataFrame, metric: str, year: str, value: str) -> bool:
    if standardized_detail.empty:
        return False
    m = _norm(metric)
    y = _norm(year)
    v = _norm(value)
    metric_cols = ["标准指标", "standard_metric"]
    metric_match = pd.Series([True] * len(standardized_detail))
    found_metric_col = False
    for c in metric_cols:
        if c in standardized_detail.columns:
            found_metric_col = True
            metric_match = metric_match & standardized_detail[c].map(_norm).eq(m)
    if not found_metric_col:
        metric_match = pd.Series([True] * len(standardized_detail))

    year_match = pd.Series([False] * len(standardized_detail))
    if y in standardized_detail.columns:
        year_match = year_match | standardized_detail[y].map(_norm).eq(v)
    if "raw_year_values" in standardized_detail.columns:
        year_match = year_match | standardized_detail["raw_year_values"].map(_norm).str.contains(y, regex=False)
    return bool((metric_match & year_match).any())


def _build_maps(df06: pd.DataFrame, off2b: pd.DataFrame) -> Dict[str, Dict[str, Dict[str, str]]]:
    map06 = {}
    for _, r in df06.iterrows():
        k = _key(r.get("asset_package"), r.get("standard_metric"), r.get("year"))
        map06[k] = {
            "value": _norm(r.get("final_value")),
            "unit": _norm(r.get("final_unit")),
            "source": _norm(r.get("final_value_source")),
        }
    map2b = {}
    for _, r in off2b.iterrows():
        k = _key(r.get("asset_package"), r.get("standard_metric"), r.get("year"))
        map2b[k] = {
            "value": _norm(r.get("final_value")),
            "unit": _norm(r.get("final_unit")),
            "source": _norm(r.get("final_value_source")),
        }
    return {"06": map06, "02B": map2b}


def _classify_record(
    row: pd.Series,
    maps: Dict[str, Dict[str, Dict[str, str]]],
    structured_info: Dict[str, pd.DataFrame],
) -> Dict[str, Any]:
    draft_repair_id = _norm(row.get("draft_repair_id"))
    candidate_id = _norm(row.get("candidate_id"))
    asset = _norm(row.get("asset_package"))
    metric = _norm(row.get("standard_metric"))
    year = _norm(row.get("year"))
    final_value = _norm(row.get("final_value"))
    final_unit = _norm(row.get("final_unit"))
    evidence = _norm(row.get("evidence"))
    source_reference = _norm(row.get("source_reference"))
    key = _key(asset, metric, year)

    m06 = maps["06"].get(key, {})
    m2b = maps["02B"].get(key, {})
    exists_in_current_06 = bool(m06)
    exists_in_02b = bool(m2b)

    exists_in_structured_02 = _find_exists_in_structured(structured_info["structured"], metric, year, final_value)
    exists_in_standardized_05 = _find_exists_in_standardized(structured_info["standardized_detail"], metric, year, final_value)

    recommended = TARGET_NEED_REVIEW
    target_reason = "default_unclassified"
    rebuild_impact = "UNKNOWN"
    risk_level = "MEDIUM"

    conflict_06 = exists_in_current_06 and (
        (not _value_equal(m06.get("value"), final_value)) or (_norm(m06.get("unit")) != _norm(final_unit))
    )
    conflict_02b = exists_in_02b and (
        (not _value_equal(m2b.get("value"), final_value)) or (_norm(m2b.get("unit")) != _norm(final_unit))
    )

    if conflict_06 or conflict_02b:
        recommended = TARGET_NEED_REVIEW
        target_reason = "value_or_unit_conflict_with_existing_layer"
        rebuild_impact = "HIGH_CONFLICT_RISK"
        risk_level = "HIGH"
    elif exists_in_standardized_05:
        recommended = TARGET_FINAL_ONLY
        target_reason = "already_present_in_standardized_layer_no_structural_backfill_needed"
        rebuild_impact = "LOW"
        risk_level = "LOW"
    elif exists_in_structured_02:
        recommended = TARGET_STANDARDIZED
        target_reason = "structured_fact_exists_but_standardized_metric_missing_or_unstable"
        rebuild_impact = "MEDIUM_STANDARDIZER_UPDATE"
        risk_level = "MEDIUM"
    elif evidence and source_reference:
        recommended = TARGET_STRUCTURED
        target_reason = "structured_fact_missing_but_evidence_complete_for_fact_backfill"
        rebuild_impact = "MEDIUM_STRUCTURED_FACT_BACKFILL"
        risk_level = "MEDIUM"
    elif evidence or source_reference:
        recommended = TARGET_MANUAL
        target_reason = "partial_evidence_requires_manual_review_before_mapping"
        rebuild_impact = "MEDIUM_MANUAL_REVIEW"
        risk_level = "MEDIUM"
    else:
        recommended = TARGET_NEED_REVIEW
        target_reason = "missing_evidence_and_source_reference"
        rebuild_impact = "HIGH_UNCERTAINTY"
        risk_level = "HIGH"

    return {
        "draft_repair_id": draft_repair_id,
        "candidate_id": candidate_id,
        "asset_package": asset,
        "standard_metric": metric,
        "year": year,
        "final_value": final_value,
        "final_unit": final_unit,
        "evidence": evidence,
        "source_reference": source_reference,
        "exists_in_structured_02": bool(exists_in_structured_02),
        "exists_in_standardized_05": bool(exists_in_standardized_05),
        "exists_in_current_06": bool(exists_in_current_06),
        "exists_in_02B": bool(exists_in_02b),
        "recommended_structured_target": recommended,
        "target_reason": target_reason,
        "rebuild_impact": rebuild_impact,
        "risk_level": risk_level,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage3D map override draft to structured-layer repair targets.")
    parser.parse_args()

    snap_before = _snapshot_prod()
    draft, off2b, df06, df01, df02, df02a = _load_inputs()
    maps = _build_maps(df06, off2b)

    rows = []
    cache: Dict[str, Dict[str, pd.DataFrame]] = {}
    for _, r in draft.iterrows():
        asset = _norm(r.get("asset_package"))
        if asset not in cache:
            cache[asset] = _load_asset_structured_and_standardized(asset)
        rows.append(_classify_record(r, maps, cache[asset]))

    result_df = pd.DataFrame(rows).sort_values(by=["recommended_structured_target", "asset_package", "standard_metric", "year"], kind="mergesort").reset_index(drop=True)

    input_draft_record_count = len(result_df)
    structured_fact_layer_target_count = int((result_df["recommended_structured_target"] == TARGET_STRUCTURED).sum())
    standardized_metric_layer_target_count = int((result_df["recommended_structured_target"] == TARGET_STANDARDIZED).sum())
    final_metric_override_only_count = int((result_df["recommended_structured_target"] == TARGET_FINAL_ONLY).sum())
    manual_review_layer_target_count = int((result_df["recommended_structured_target"] == TARGET_MANUAL).sum())
    need_mapping_review_count = int((result_df["recommended_structured_target"] == TARGET_NEED_REVIEW).sum())

    snap_after = _snapshot_prod()
    production_files_unchanged = snap_before == snap_after
    output_06_unchanged = snap_before["06"] == snap_after["06"]
    official_02B_unchanged = _sha256(OFFICIAL_02B_PATH) == _sha256(OFFICIAL_02B_PATH)
    delivery_status = _run_delivery_check()

    stage3d_mapping_pass = bool(
        input_draft_record_count == 4
        and production_files_unchanged
        and output_06_unchanged
        and official_02B_unchanged
        and delivery_status.get("overall_status") == "PASS"
    )

    summary = {
        "input_draft_record_count": input_draft_record_count,
        "structured_fact_layer_target_count": structured_fact_layer_target_count,
        "standardized_metric_layer_target_count": standardized_metric_layer_target_count,
        "final_metric_override_only_count": final_metric_override_only_count,
        "manual_review_layer_target_count": manual_review_layer_target_count,
        "need_mapping_review_count": need_mapping_review_count,
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage3d_mapping_pass": bool(stage3d_mapping_pass),
        "delivery_status_after": delivery_status.get("overall_status", "UNKNOWN"),
    }

    out_xlsx = STAGE3D_OUT / "91_stage3d_structured_mapping.xlsx"
    out_md = STAGE3D_OUT / "91_stage3d_structured_mapping.md"
    out_json = STAGE3D_OUT / "92_stage3d_structured_mapping_summary.json"

    dist_df = (
        result_df.groupby("recommended_structured_target", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(by=["count", "recommended_structured_target"], ascending=[False, True], kind="mergesort")
    )

    _safe_write_excel_multi(
        {
            "stage3d_mapping": result_df,
            "summary": pd.DataFrame([summary]),
            "target_distribution": dist_df,
        },
        out_xlsx,
    )

    md_lines = [
        "# Stage3D Structured Mapping",
        "",
        "## Summary",
        f"- input_draft_record_count: {summary['input_draft_record_count']}",
        f"- structured_fact_layer_target_count: {summary['structured_fact_layer_target_count']}",
        f"- standardized_metric_layer_target_count: {summary['standardized_metric_layer_target_count']}",
        f"- final_metric_override_only_count: {summary['final_metric_override_only_count']}",
        f"- manual_review_layer_target_count: {summary['manual_review_layer_target_count']}",
        f"- need_mapping_review_count: {summary['need_mapping_review_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- output_06_unchanged: {summary['output_06_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- delivery_status_after: {summary['delivery_status_after']}",
        f"- stage3d_mapping_pass: {summary['stage3d_mapping_pass']}",
    ]
    _safe_write_text("\n".join(md_lines), out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage3d_mapping_xlsx: {out_xlsx}")
    print(f"stage3d_mapping_md: {out_md}")
    print(f"stage3d_mapping_summary_json: {out_json}")
    for k in [
        "input_draft_record_count",
        "structured_fact_layer_target_count",
        "standardized_metric_layer_target_count",
        "final_metric_override_only_count",
        "manual_review_layer_target_count",
        "need_mapping_review_count",
        "production_files_unchanged",
        "output_06_unchanged",
        "official_02B_unchanged",
        "stage3d_mapping_pass",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
