import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import financial_standardizer as fs


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

STAGE5G_DIR = OUTPUT_DIR / "stage5g_remaining_mapping_miss_analysis"
STAGE5F_DIR = OUTPUT_DIR / "stage5f_raw_metric_extraction_fix"

INPUT_5G_XLSX = STAGE5G_DIR / "138_stage5g_remaining_mapping_miss_analysis.xlsx"
INPUT_5G_MD = STAGE5G_DIR / "138_stage5g_remaining_mapping_miss_analysis.md"
INPUT_5G_SUMMARY_JSON = STAGE5G_DIR / "139_stage5g_remaining_mapping_miss_summary.json"
INPUT_5F_IMPROVED_02_XLSX = STAGE5F_DIR / "136_stage5f_improved_structured_02.xlsx"
INPUT_5F_PREVIEW_XLSX = STAGE5F_DIR / "136_stage5f_improved_standardization_preview.xlsx"
INPUT_5F_SUMMARY_JSON = STAGE5F_DIR / "137_stage5f_raw_metric_extraction_fix_summary.json"

FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
FORMAL_ALIAS_RULE_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

OUT_DIR = OUTPUT_DIR / "stage5h_alias_draft_validation"
OUT_ALIAS_DRAFT_XLSX = OUT_DIR / "140_stage5h_alias_draft.xlsx"
OUT_DRY_RUN_XLSX = OUT_DIR / "140_stage5h_alias_dry_run_result.xlsx"
OUT_REPORT_XLSX = OUT_DIR / "140_stage5h_alias_draft_validation_report.xlsx"
OUT_REPORT_MD = OUT_DIR / "140_stage5h_alias_draft_validation_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "141_stage5h_alias_draft_validation_summary.json"

DRAFT_STATUS_READY = "DRAFT_ALIAS_READY"
DRAFT_STATUS_REVIEW = "DRAFT_ALIAS_NEEDS_REVIEW"
DRAFT_STATUS_REJECT = "DRAFT_ALIAS_REJECTED"

CHANGE_ALIAS_OK = "ALIAS_MATCHED_NEW_STANDARDIZED_OK"
CHANGE_UNCHANGED_ALREADY_OK = "UNCHANGED_ALREADY_STANDARDIZED"
CHANGE_UNCHANGED_DERIVED = "UNCHANGED_DERIVED_METRIC_NOT_SUPPORTED"
CHANGE_UNCHANGED_NON_CORE = "UNCHANGED_NON_CORE_METRIC"
CHANGE_UNCHANGED_MISS = "UNCHANGED_MAPPING_MISS"
CHANGE_UNCHANGED_OTHER = "UNCHANGED_OTHER"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    t = _norm(v).replace("（", "(").replace("）", ")").replace("／", "/")
    return re.sub(r"\s+", "", t).upper()


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31-len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_delivery_file(pattern: str) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing delivery file pattern: {pattern}")
    non_copy = [p for p in files if "_copy_" not in p.name.lower()]
    return non_copy[0] if non_copy else files[0]


def _snapshot_hashes() -> Dict[str, str]:
    return {
        "01": _sha256(_find_delivery_file("01_*.xlsx")),
        "02": _sha256(_find_delivery_file("02_*.xlsx")),
        "02A": _sha256(_find_delivery_file("02A_*.xlsx")),
        "05": _sha256(_find_delivery_file("05_*.xlsx")),
        "06": _sha256(_find_delivery_file("06_*.xlsx")),
        "02B": _sha256(OFFICIAL_02B_PATH),
        "formal_scope_rules": _sha256(FORMAL_SCOPE_RULES_JSON),
        "formal_mapping_rules": _sha256(FORMAL_MAPPING_RULE_FILE),
        "formal_normalization_rules": _sha256(FORMAL_NORMALIZATION_RULE_FILE),
        "formal_alias_rules": _sha256(FORMAL_ALIAS_RULE_FILE),
    }


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    text = (p.stdout or "").strip()
    if not text:
        return {"overall_status": "UNKNOWN"}
    return json.loads(text)


def _mapping_rule_id(metric: str) -> str:
    m = _norm(metric)
    if not m:
        return ""
    return f"FS_MAP_{_compact(m)}"


def _load_stage5g_inventory(path: Path) -> pd.DataFrame:
    xl = pd.ExcelFile(path)
    sheet = xl.sheet_names[0]
    return pd.read_excel(path, sheet_name=sheet).fillna("")


def _load_stage5f_preview(path: Path) -> pd.DataFrame:
    xl = pd.ExcelFile(path)
    sheet = xl.sheet_names[0]
    return pd.read_excel(path, sheet_name=sheet).fillna("")


def _is_valid_value(v: str) -> bool:
    return bool(re.fullmatch(r"[-+]?\d+(?:\.\d+)?", _norm(v).replace(",", "")))


def _is_valid_year(y: str) -> bool:
    return bool(re.fullmatch(r"20\d{2}(?:[AE])?", _norm(y).upper()))


def _is_valid_unit(u: str) -> bool:
    return _norm(u) != ""


def _classify_remaining(row: pd.Series) -> str:
    raw = _norm(row.get("raw_metric_name_cleaned") or row.get("raw_metric_name"))
    if not raw:
        return CHANGE_UNCHANGED_OTHER
    if any(x in raw for x in ["(%)", "%", "周转率", "ROIC", "资产负债率", "净利率"]):
        return CHANGE_UNCHANGED_DERIVED
    if any(x in raw for x in ["营业利润", "净利润", "EBITDA"]):
        return CHANGE_UNCHANGED_NON_CORE
    return CHANGE_UNCHANGED_MISS


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5H draft alias rules and validate sandbox standardization.")
    parser.parse_args()

    required = [
        INPUT_5G_XLSX,
        INPUT_5G_MD,
        INPUT_5G_SUMMARY_JSON,
        INPUT_5F_IMPROVED_02_XLSX,
        INPUT_5F_PREVIEW_XLSX,
        INPUT_5F_SUMMARY_JSON,
        FORMAL_SCOPE_RULES_JSON,
        OFFICIAL_02B_PATH,
        FORMAL_NORMALIZATION_RULE_FILE,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    before = _snapshot_hashes()

    df_5g = _load_stage5g_inventory(INPUT_5G_XLSX)
    df_5f_preview = _load_stage5f_preview(INPUT_5F_PREVIEW_XLSX)
    _ = pd.read_excel(_find_delivery_file("05_*.xlsx")).fillna("")

    s5g = json.loads(INPUT_5G_SUMMARY_JSON.read_text(encoding="utf-8"))
    s5f = json.loads(INPUT_5F_SUMMARY_JSON.read_text(encoding="utf-8"))

    alias_missing_df = df_5g[df_5g["remaining_miss_category"].map(_norm) == "ALIAS_MISSING"].copy()
    alias_missing_df = alias_missing_df.sort_values(["priority_level", "similarity_score"], ascending=[True, False], kind="mergesort")

    alias_rows: List[Dict[str, Any]] = []
    for i, (_, r) in enumerate(alias_missing_df.iterrows(), start=1):
        raw = _norm(r.get("raw_metric_name"))
        cleaned = _norm(r.get("raw_metric_name_cleaned"))
        target_metric = _norm(r.get("nearest_existing_standard_metric"))
        sim = float(r.get("similarity_score") or 0.0)

        status = DRAFT_STATUS_READY if (target_metric and sim >= 0.70) else DRAFT_STATUS_REVIEW
        confidence = "HIGH" if sim >= 0.90 else ("MEDIUM" if sim >= 0.75 else "LOW")
        if not target_metric:
            status = DRAFT_STATUS_REJECT
            confidence = "LOW"

        alias_rows.append(
            {
                "alias_rule_id": f"S5H-ALIAS-{i:04d}",
                "raw_metric_name": raw,
                "raw_metric_name_cleaned": cleaned,
                "target_standard_metric": target_metric,
                "target_existing_mapping_rule_id": _mapping_rule_id(target_metric),
                "statement_type": _norm(r.get("statement_type")),
                "asset_package": _norm(r.get("asset_package")),
                "unit": _norm(r.get("unit")),
                "year_sample": _norm(r.get("year")),
                "value_sample": _norm(r.get("value")),
                "source_pdf": _norm(r.get("source_pdf")),
                "source_page": _norm(r.get("source_page")),
                "source_table_id": _norm(r.get("source_table_id")),
                "row_trace_id": _norm(r.get("row_trace_id")),
                "confidence_level": confidence,
                "draft_status": status,
                "evidence": _norm(r.get("evidence")),
            }
        )

    draft_df = pd.DataFrame(alias_rows)

    # Build alias map for dry-run
    alias_map: Dict[str, str] = {}
    for _, r in draft_df.iterrows():
        if _norm(r.get("draft_status")) != DRAFT_STATUS_READY:
            continue
        key = _compact(_norm(r.get("raw_metric_name_cleaned")) or _norm(r.get("raw_metric_name")))
        val = _norm(r.get("target_standard_metric"))
        if key and val:
            alias_map[key] = val

    # Dry-run re-standardization on improved preview rows.
    dry_rows: List[Dict[str, Any]] = []
    for _, r in df_5f_preview.iterrows():
        row_trace_id = _norm(r.get("row_trace_id"))
        raw_metric_name = _norm(r.get("raw_metric_name"))
        raw_clean = fs._clean_metric_label_noise(raw_metric_name)
        key = _compact(raw_clean or raw_metric_name)

        std_before = _norm(r.get("standard_metric"))
        status_before = _norm(r.get("standardization_status"))

        std_after = std_before
        status_after = status_before
        matched_alias_rule_id = ""
        issue_type_after = _norm(r.get("standardization_issue_type"))
        change_type = CHANGE_UNCHANGED_OTHER

        if status_before == "STANDARDIZED_OK":
            change_type = CHANGE_UNCHANGED_ALREADY_OK
        elif status_before == "MAPPING_MISS" and key in alias_map:
            target = alias_map[key]
            year_ok = _is_valid_year(_norm(r.get("year")))
            value_ok = _is_valid_value(_norm(r.get("value")))
            unit_ok = _is_valid_unit(_norm(r.get("unit")))
            std_after = target
            if year_ok and value_ok and unit_ok:
                status_after = "STANDARDIZED_OK"
                issue_type_after = "NONE"
                change_type = CHANGE_ALIAS_OK
            else:
                # alias matched, but value/unit/year still not valid
                status_after = "MAPPING_MISS"
                issue_type_after = "VALUE_UNIT_YEAR_ISSUE"
                change_type = CHANGE_UNCHANGED_MISS
            # back-link to alias draft id
            hit = draft_df[
                (draft_df["target_standard_metric"].map(_norm) == target)
                & (
                    draft_df["raw_metric_name_cleaned"].map(lambda x: _compact(x)) == key
                )
            ]
            if hit.empty:
                hit = draft_df[
                    (draft_df["target_standard_metric"].map(_norm) == target)
                    & (draft_df["raw_metric_name"].map(lambda x: _compact(x)) == key)
                ]
            if not hit.empty:
                matched_alias_rule_id = _norm(hit.iloc[0]["alias_rule_id"])
        elif status_before == "MAPPING_MISS":
            change_type = _classify_remaining(r)
        else:
            change_type = CHANGE_UNCHANGED_OTHER

        dry_rows.append(
            {
                "row_trace_id": row_trace_id,
                "raw_metric_name": raw_metric_name,
                "raw_metric_name_cleaned": raw_clean,
                "standard_metric_before": std_before,
                "standardization_status_before": status_before,
                "standard_metric_after": std_after,
                "standardization_status_after": status_after,
                "matched_alias_rule_id": matched_alias_rule_id,
                "change_type": change_type,
                "issue_type_after": issue_type_after,
                "source_reference": _norm(r.get("source_reference")),
            }
        )

    dry_df = pd.DataFrame(dry_rows)

    # summary metrics
    input_stage5g_remaining_miss_count = int(s5g.get("input_remaining_mapping_miss_count", 0))
    input_alias_missing_count = int(len(alias_missing_df))
    draft_alias_rule_count = int(len(draft_df))
    draft_alias_ready_count = int((draft_df["draft_status"].map(_norm) == DRAFT_STATUS_READY).sum()) if not draft_df.empty else 0
    draft_alias_needs_review_count = int((draft_df["draft_status"].map(_norm) == DRAFT_STATUS_REVIEW).sum()) if not draft_df.empty else 0
    draft_alias_rejected_count = int((draft_df["draft_status"].map(_norm) == DRAFT_STATUS_REJECT).sum()) if not draft_df.empty else 0

    previous_improved_standardized_ok_count = int(s5f.get("improved_standardized_ok_count", 0))
    previous_mapping_miss_count = int(s5f.get("improved_mapping_miss_count", 0))

    after_alias_standardized_ok_count = int((dry_df["standardization_status_after"].map(_norm) == "STANDARDIZED_OK").sum()) if not dry_df.empty else 0
    after_alias_mapping_miss_count = int((dry_df["standardization_status_after"].map(_norm) == "MAPPING_MISS").sum()) if not dry_df.empty else 0

    standardized_ok_increment_count = int(after_alias_standardized_ok_count - previous_improved_standardized_ok_count)
    mapping_miss_reduced_count = int(previous_mapping_miss_count - after_alias_mapping_miss_count)
    alias_matched_new_standardized_ok_count = int((dry_df["change_type"].map(_norm) == CHANGE_ALIAS_OK).sum()) if not dry_df.empty else 0

    remaining_derived_metric_not_supported_count = int((dry_df["change_type"].map(_norm) == CHANGE_UNCHANGED_DERIVED).sum()) if not dry_df.empty else 0
    remaining_non_core_metric_count = int((dry_df["change_type"].map(_norm) == CHANGE_UNCHANGED_NON_CORE).sum()) if not dry_df.empty else 0
    remaining_true_mapping_gap_count = int(((dry_df["standardization_status_after"].map(_norm) == "MAPPING_MISS") & (~dry_df["change_type"].map(_norm).isin([CHANGE_UNCHANGED_DERIVED, CHANGE_UNCHANGED_NON_CORE]))).sum()) if not dry_df.empty else 0
    remaining_unknown_count = int((dry_df["change_type"].map(_norm) == CHANGE_UNCHANGED_OTHER).sum()) if not dry_df.empty else 0
    ready_for_stage5i_alias_promotion_count = int(draft_alias_ready_count)

    after = _snapshot_hashes()
    production_files_unchanged = bool(
        before["01"] == after["01"]
        and before["02"] == after["02"]
        and before["02A"] == after["02A"]
        and before["05"] == after["05"]
        and before["06"] == after["06"]
    )
    official_02B_unchanged = bool(before["02B"] == after["02B"])
    formal_scope_rules_unchanged = bool(before["formal_scope_rules"] == after["formal_scope_rules"])
    formal_mapping_rules_unchanged = bool(before["formal_mapping_rules"] == after["formal_mapping_rules"])
    formal_normalization_rules_unchanged = bool(before["formal_normalization_rules"] == after["formal_normalization_rules"])
    formal_alias_rules_unchanged = bool(before["formal_alias_rules"] == after["formal_alias_rules"])

    summary = {
        "input_stage5g_remaining_miss_count": int(input_stage5g_remaining_miss_count),
        "input_alias_missing_count": int(input_alias_missing_count),
        "draft_alias_rule_count": int(draft_alias_rule_count),
        "draft_alias_ready_count": int(draft_alias_ready_count),
        "draft_alias_needs_review_count": int(draft_alias_needs_review_count),
        "draft_alias_rejected_count": int(draft_alias_rejected_count),
        "previous_improved_standardized_ok_count": int(previous_improved_standardized_ok_count),
        "after_alias_standardized_ok_count": int(after_alias_standardized_ok_count),
        "standardized_ok_increment_count": int(standardized_ok_increment_count),
        "previous_mapping_miss_count": int(previous_mapping_miss_count),
        "after_alias_mapping_miss_count": int(after_alias_mapping_miss_count),
        "mapping_miss_reduced_count": int(mapping_miss_reduced_count),
        "alias_matched_new_standardized_ok_count": int(alias_matched_new_standardized_ok_count),
        "remaining_derived_metric_not_supported_count": int(remaining_derived_metric_not_supported_count),
        "remaining_non_core_metric_count": int(remaining_non_core_metric_count),
        "remaining_true_mapping_gap_count": int(remaining_true_mapping_gap_count),
        "remaining_unknown_count": int(remaining_unknown_count),
        "ready_for_stage5i_alias_promotion_count": int(ready_for_stage5i_alias_promotion_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_scope_rules_unchanged": bool(formal_scope_rules_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "formal_normalization_rules_unchanged": bool(formal_normalization_rules_unchanged),
        "formal_alias_rules_unchanged": bool(formal_alias_rules_unchanged),
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage5h_alias_draft_validation_pass": False,
    }

    summary["stage5h_alias_draft_validation_pass"] = bool(
        summary["input_alias_missing_count"] == 5
        and summary["draft_alias_rule_count"] == 5
        and summary["after_alias_standardized_ok_count"] >= summary["previous_improved_standardized_ok_count"]
        and summary["after_alias_mapping_miss_count"] <= summary["previous_mapping_miss_count"]
        and summary["ready_for_stage5i_alias_promotion_count"] > 0
        and summary["production_files_unchanged"]
        and summary["official_02B_unchanged"]
        and summary["formal_scope_rules_unchanged"]
        and summary["formal_mapping_rules_unchanged"]
        and summary["formal_normalization_rules_unchanged"]
        and summary["formal_alias_rules_unchanged"]
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    dry_change_dist_df = (
        dry_df.groupby(["change_type", "standardization_status_after"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "change_type"], ascending=[False, True], kind="mergesort")
        if not dry_df.empty else pd.DataFrame(columns=["change_type", "standardization_status_after", "count"])
    )

    _write_excel(OUT_ALIAS_DRAFT_XLSX, {"alias_draft": draft_df})
    _write_excel(OUT_DRY_RUN_XLSX, {"alias_dry_run_result": dry_df, "change_distribution": dry_change_dist_df})
    _write_excel(
        OUT_REPORT_XLSX,
        {
            "summary": pd.DataFrame([summary]),
            "alias_draft": draft_df,
            "dry_run_result": dry_df,
            "change_distribution": dry_change_dist_df,
            "stage5g_alias_missing_ref": alias_missing_df,
        },
    )

    md_lines = [
        "# Stage5H Alias Draft Validation",
        "",
        f"- input_stage5g_remaining_miss_count: {summary['input_stage5g_remaining_miss_count']}",
        f"- input_alias_missing_count: {summary['input_alias_missing_count']}",
        f"- draft_alias_rule_count: {summary['draft_alias_rule_count']}",
        f"- draft_alias_ready_count: {summary['draft_alias_ready_count']}",
        f"- draft_alias_needs_review_count: {summary['draft_alias_needs_review_count']}",
        f"- draft_alias_rejected_count: {summary['draft_alias_rejected_count']}",
        f"- previous_improved_standardized_ok_count: {summary['previous_improved_standardized_ok_count']}",
        f"- after_alias_standardized_ok_count: {summary['after_alias_standardized_ok_count']}",
        f"- standardized_ok_increment_count: {summary['standardized_ok_increment_count']}",
        f"- previous_mapping_miss_count: {summary['previous_mapping_miss_count']}",
        f"- after_alias_mapping_miss_count: {summary['after_alias_mapping_miss_count']}",
        f"- mapping_miss_reduced_count: {summary['mapping_miss_reduced_count']}",
        f"- alias_matched_new_standardized_ok_count: {summary['alias_matched_new_standardized_ok_count']}",
        f"- remaining_derived_metric_not_supported_count: {summary['remaining_derived_metric_not_supported_count']}",
        f"- remaining_non_core_metric_count: {summary['remaining_non_core_metric_count']}",
        f"- remaining_true_mapping_gap_count: {summary['remaining_true_mapping_gap_count']}",
        f"- remaining_unknown_count: {summary['remaining_unknown_count']}",
        f"- ready_for_stage5i_alias_promotion_count: {summary['ready_for_stage5i_alias_promotion_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_scope_rules_unchanged: {summary['formal_scope_rules_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- formal_normalization_rules_unchanged: {summary['formal_normalization_rules_unchanged']}",
        f"- formal_alias_rules_unchanged: {summary['formal_alias_rules_unchanged']}",
        f"- stage5h_alias_draft_validation_pass: {summary['stage5h_alias_draft_validation_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage5h_alias_draft_xlsx: {OUT_ALIAS_DRAFT_XLSX}")
    print(f"stage5h_alias_dry_run_xlsx: {OUT_DRY_RUN_XLSX}")
    print(f"stage5h_validation_report_xlsx: {OUT_REPORT_XLSX}")
    print(f"stage5h_validation_report_md: {OUT_REPORT_MD}")
    print(f"stage5h_summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5h_alias_draft_validation_pass: {summary['stage5h_alias_draft_validation_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
