import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import financial_standardizer as fs


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

INPUT_PDF = BASE_DIR / "input" / "H3_AP202605121822223662_1.pdf"

STAGE5B_DIR = OUTPUT_DIR / "stage5b_table_extraction_restore"
STAGE5F_DIR = OUTPUT_DIR / "stage5f_raw_metric_extraction_fix"
STAGE5I_DIR = OUTPUT_DIR / "stage5i_alias_promotion"

RAW_TABLE_XLSX = STAGE5B_DIR / "raw_tables.xlsx"
RAW_TABLE_JSON = STAGE5B_DIR / "raw_tables.json"
STAGE5B_SUMMARY = STAGE5B_DIR / "129_stage5b_table_extraction_restore_summary.json"

IMPROVED_02_XLSX = STAGE5F_DIR / "136_stage5f_improved_structured_02.xlsx"
IMPROVED_PREVIEW_XLSX = STAGE5F_DIR / "136_stage5f_improved_standardization_preview.xlsx"
STAGE5F_SUMMARY = STAGE5F_DIR / "137_stage5f_raw_metric_extraction_fix_summary.json"

STAGE5I_LOG_XLSX = STAGE5I_DIR / "142_stage5i_alias_promotion_log.xlsx"
STAGE5I_VERIFY_XLSX = STAGE5I_DIR / "142_stage5i_alias_promotion_verification.xlsx"
STAGE5I_SUMMARY = STAGE5I_DIR / "143_stage5i_alias_promotion_summary.json"

FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
FORMAL_ALIAS_RULE_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

OUT_DIR = OUTPUT_DIR / "stage5j_pdf_to_05_baseline_closure"
OUT_VERIFY_XLSX = OUT_DIR / "144_stage5j_pdf_to_05_baseline_verification.xlsx"
OUT_REPORT_MD = OUT_DIR / "144_stage5j_pdf_to_05_baseline_closure_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "145_stage5j_pdf_to_05_baseline_closure_summary.json"

CHG_FORMAL_OK = "FORMAL_ALIAS_MATCHED_STANDARDIZED_OK"
CHG_UNCHANGED_OK = "UNCHANGED_ALREADY_STANDARDIZED"
CHG_UNCHANGED_DERIVED = "UNCHANGED_DERIVED_METRIC_NOT_SUPPORTED"
CHG_UNCHANGED_NON_CORE = "UNCHANGED_NON_CORE_METRIC"
CHG_UNCHANGED_MISS = "UNCHANGED_MAPPING_MISS"
CHG_UNCHANGED_OTHER = "UNCHANGED_OTHER"


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


def _json_load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_df_first_sheet(path: Path) -> pd.DataFrame:
    xl = pd.ExcelFile(path)
    return pd.read_excel(path, sheet_name=xl.sheet_names[0]).fillna("")


def _read_pdf_page_count(pdf_path: Path, fallback: int = 0) -> int:
    try:
        from pypdf import PdfReader  # type: ignore

        return int(len(PdfReader(str(pdf_path)).pages))
    except Exception:
        return int(fallback)


def _is_valid_year(y: str) -> bool:
    return bool(re.fullmatch(r"20\d{2}(?:[AE])?", _norm(y).upper()))


def _is_valid_value(v: str) -> bool:
    return bool(re.fullmatch(r"[-+]?\d+(?:\.\d+)?", _norm(v).replace(",", "")))


def _is_valid_unit(u: str) -> bool:
    return _norm(u) != ""


def _classify_mapping_miss(raw: str) -> str:
    t = _norm(raw)
    if any(x in t for x in ["(%)", "%", "周转率", "ROIC", "资产负债率", "净利率"]):
        return CHG_UNCHANGED_DERIVED
    if any(x in t for x in ["营业利润", "净利润", "EBITDA"]):
        return CHG_UNCHANGED_NON_CORE
    return CHG_UNCHANGED_MISS


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    text = (p.stdout or "").strip()
    return json.loads(text) if text else {"overall_status": "UNKNOWN"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5J close pdf-to-05 sandbox baseline.")
    parser.parse_args()

    required_paths = [
        INPUT_PDF,
        RAW_TABLE_XLSX,
        RAW_TABLE_JSON,
        STAGE5B_SUMMARY,
        IMPROVED_02_XLSX,
        IMPROVED_PREVIEW_XLSX,
        STAGE5F_SUMMARY,
        STAGE5I_LOG_XLSX,
        STAGE5I_VERIFY_XLSX,
        STAGE5I_SUMMARY,
        FORMAL_SCOPE_RULES_JSON,
        FORMAL_MAPPING_RULE_FILE,
        FORMAL_NORMALIZATION_RULE_FILE,
        FORMAL_ALIAS_RULE_FILE,
        OFFICIAL_02B_PATH,
    ]
    for p in required_paths:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    before = _snapshot_hashes()

    s5b = _json_load(STAGE5B_SUMMARY)
    s5f = _json_load(STAGE5F_SUMMARY)
    s5i = _json_load(STAGE5I_SUMMARY)
    df_02 = _load_df_first_sheet(IMPROVED_02_XLSX)
    df_preview = _load_df_first_sheet(IMPROVED_PREVIEW_XLSX)

    pdf_exists = INPUT_PDF.exists()
    pdf_page_count = _read_pdf_page_count(INPUT_PDF, fallback=int(s5b.get("pdf_page_count", 0)))
    raw_table_file_exists = bool(RAW_TABLE_XLSX.exists() and RAW_TABLE_JSON.exists())

    raw_table_count = int(s5b.get("raw_table_count", 0))
    raw_table_total_row_count = int(s5b.get("raw_table_total_row_count", 0))
    raw_table_total_cell_count = int(s5b.get("raw_table_total_cell_count", 0))

    improved_structured_02_file_exists = IMPROVED_02_XLSX.exists()
    improved_structured_02_row_count = int(len(df_02))

    formal_alias_rules_available = bool(
        hasattr(fs, "STANDARD_METRIC_ALIASES")
        and isinstance(fs.STANDARD_METRIC_ALIASES, dict)
        and len(fs.STANDARD_METRIC_ALIASES) > 0
    )

    verify_rows: List[Dict[str, Any]] = []
    for _, r in df_preview.iterrows():
        row_trace_id = _norm(r.get("row_trace_id"))
        raw_metric_name = _norm(r.get("raw_metric_name"))
        source_reference = _norm(r.get("source_reference"))
        status_before = _norm(r.get("standardization_status"))
        raw_clean = fs._clean_metric_label_noise(raw_metric_name)

        m = fs._match_standard_metric(raw_metric_name)
        standard_metric_after = _norm(m.get("standard_metric")) if m else ""
        if status_before == "STANDARDIZED_OK":
            status_after = "STANDARDIZED_OK"
            change_type = CHG_UNCHANGED_OK
            issue_type_after = "NONE"
        elif status_before == "DUPLICATE_CANDIDATE":
            status_after = "DUPLICATE_CANDIDATE"
            change_type = CHG_UNCHANGED_OTHER
            issue_type_after = "DUPLICATE_KEY"
        elif status_before == "MAPPING_MISS":
            if m and _is_valid_year(_norm(r.get("year"))) and _is_valid_value(_norm(r.get("value"))) and _is_valid_unit(_norm(r.get("unit"))):
                status_after = "STANDARDIZED_OK"
                change_type = CHG_FORMAL_OK
                issue_type_after = "NONE"
            else:
                status_after = "MAPPING_MISS"
                change_type = _classify_mapping_miss(raw_clean or raw_metric_name)
                issue_type_after = "METRIC_MAPPING_ISSUE"
        else:
            status_after = status_before
            change_type = CHG_UNCHANGED_OTHER
            issue_type_after = _norm(r.get("standardization_issue_type")) or "UNKNOWN"

        verify_rows.append(
            {
                "row_trace_id": row_trace_id,
                "raw_metric_name": raw_metric_name,
                "source_reference": source_reference,
                "standard_metric_after_formal_alias": standard_metric_after,
                "standardization_status_before": status_before,
                "standardization_status_after_formal_alias": status_after,
                "change_type": change_type,
                "issue_type_after": issue_type_after,
            }
        )

    verify_df = pd.DataFrame(verify_rows).fillna("")
    sandbox_05_verification_row_count = int(len(verify_df))
    formal_alias_standardized_ok_count = int(
        (verify_df["standardization_status_after_formal_alias"].map(_norm) == "STANDARDIZED_OK").sum()
    )
    formal_alias_mapping_miss_count = int(
        (verify_df["standardization_status_after_formal_alias"].map(_norm) == "MAPPING_MISS").sum()
    )
    remaining_derived_metric_not_supported_count = int(
        (verify_df["change_type"].map(_norm) == CHG_UNCHANGED_DERIVED).sum()
    )
    remaining_non_core_metric_count = int(
        (verify_df["change_type"].map(_norm) == CHG_UNCHANGED_NON_CORE).sum()
    )
    remaining_unknown_count = int(
        (verify_df["change_type"].map(_norm) == CHG_UNCHANGED_OTHER).sum()
    )
    remaining_true_mapping_gap_count = int(
        (
            (verify_df["standardization_status_after_formal_alias"].map(_norm) == "MAPPING_MISS")
            & (~verify_df["change_type"].map(_norm).isin([CHG_UNCHANGED_DERIVED, CHG_UNCHANGED_NON_CORE]))
        ).sum()
    )

    stage5b_pdf_to_raw_tables_pass = bool(s5b.get("stage5b_restore_pass", False))
    stage5f_raw_metric_extraction_fix_pass = bool(s5f.get("stage5f_raw_metric_extraction_fix_pass", False))
    stage5i_alias_promotion_pass = bool(s5i.get("stage5i_alias_promotion_pass", False))

    recommended_next_stage = "STAGE5K_DERIVED_METRIC_AND_NON_CORE_FILTER_STRATEGY"
    stage5j_pdf_to_05_baseline_closed = bool(
        pdf_exists
        and raw_table_count == 5
        and improved_structured_02_row_count == 130
        and formal_alias_standardized_ok_count >= 45
        and formal_alias_mapping_miss_count <= 80
        and remaining_true_mapping_gap_count == 0
        and stage5b_pdf_to_raw_tables_pass
        and stage5f_raw_metric_extraction_fix_pass
        and stage5i_alias_promotion_pass
    )

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
        "input_pdf_file": str(INPUT_PDF),
        "pdf_exists": bool(pdf_exists),
        "pdf_page_count": int(pdf_page_count),
        "raw_table_file_exists": bool(raw_table_file_exists),
        "raw_table_count": int(raw_table_count),
        "raw_table_total_row_count": int(raw_table_total_row_count),
        "raw_table_total_cell_count": int(raw_table_total_cell_count),
        "improved_structured_02_file_exists": bool(improved_structured_02_file_exists),
        "improved_structured_02_row_count": int(improved_structured_02_row_count),
        "formal_alias_rules_available": bool(formal_alias_rules_available),
        "sandbox_05_verification_row_count": int(sandbox_05_verification_row_count),
        "formal_alias_standardized_ok_count": int(formal_alias_standardized_ok_count),
        "formal_alias_mapping_miss_count": int(formal_alias_mapping_miss_count),
        "remaining_derived_metric_not_supported_count": int(remaining_derived_metric_not_supported_count),
        "remaining_non_core_metric_count": int(remaining_non_core_metric_count),
        "remaining_true_mapping_gap_count": int(remaining_true_mapping_gap_count),
        "remaining_unknown_count": int(remaining_unknown_count),
        "stage5b_pdf_to_raw_tables_pass": bool(stage5b_pdf_to_raw_tables_pass),
        "stage5f_raw_metric_extraction_fix_pass": bool(stage5f_raw_metric_extraction_fix_pass),
        "stage5i_alias_promotion_pass": bool(stage5i_alias_promotion_pass),
        "stage5j_pdf_to_05_baseline_closed": bool(stage5j_pdf_to_05_baseline_closed),
        "recommended_next_stage": str(recommended_next_stage),
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
        "stage5j_closure_pass": False,
    }

    summary["stage5j_closure_pass"] = bool(
        summary["pdf_exists"]
        and summary["raw_table_count"] == 5
        and summary["improved_structured_02_row_count"] == 130
        and summary["formal_alias_standardized_ok_count"] >= 45
        and summary["formal_alias_mapping_miss_count"] <= 80
        and summary["remaining_true_mapping_gap_count"] == 0
        and summary["stage5b_pdf_to_raw_tables_pass"]
        and summary["stage5f_raw_metric_extraction_fix_pass"]
        and summary["stage5i_alias_promotion_pass"]
        and summary["stage5j_pdf_to_05_baseline_closed"]
        and bool(summary["recommended_next_stage"])
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

    breakdown_df = (
        verify_df.groupby(["change_type", "standardization_status_after_formal_alias"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "change_type"], ascending=[False, True], kind="mergesort")
        if not verify_df.empty
        else pd.DataFrame(columns=["change_type", "standardization_status_after_formal_alias", "count"])
    )

    _write_excel(
        OUT_VERIFY_XLSX,
        {
            "baseline_verification": verify_df,
            "status_distribution": breakdown_df,
            "summary": pd.DataFrame([summary]),
            "stage5b_summary_ref": pd.DataFrame([s5b]),
            "stage5f_summary_ref": pd.DataFrame([s5f]),
            "stage5i_summary_ref": pd.DataFrame([s5i]),
        },
    )

    md_lines = [
        "# Stage5J PDF-To-05 Baseline Closure",
        "",
        "## Pipeline Status",
        f"- PDF exists: {summary['pdf_exists']}",
        f"- PDF page count: {summary['pdf_page_count']}",
        f"- Raw table files ready: {summary['raw_table_file_exists']}",
        f"- Raw table count: {summary['raw_table_count']}",
        f"- Raw table total rows: {summary['raw_table_total_row_count']}",
        f"- Raw table total cells: {summary['raw_table_total_cell_count']}",
        f"- Improved structured 02 rows: {summary['improved_structured_02_row_count']}",
        f"- Sandbox 05 verification rows: {summary['sandbox_05_verification_row_count']}",
        "",
        "## Formal Alias Verification",
        f"- formal_alias_standardized_ok_count: {summary['formal_alias_standardized_ok_count']}",
        f"- formal_alias_mapping_miss_count: {summary['formal_alias_mapping_miss_count']}",
        f"- remaining_derived_metric_not_supported_count: {summary['remaining_derived_metric_not_supported_count']}",
        f"- remaining_non_core_metric_count: {summary['remaining_non_core_metric_count']}",
        f"- remaining_true_mapping_gap_count: {summary['remaining_true_mapping_gap_count']}",
        f"- remaining_unknown_count: {summary['remaining_unknown_count']}",
        "",
        "## Guardrail Checks",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_scope_rules_unchanged: {summary['formal_scope_rules_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- formal_normalization_rules_unchanged: {summary['formal_normalization_rules_unchanged']}",
        f"- formal_alias_rules_unchanged: {summary['formal_alias_rules_unchanged']}",
        "",
        "## Closure Decision",
        f"- stage5j_pdf_to_05_baseline_closed: {summary['stage5j_pdf_to_05_baseline_closed']}",
        f"- recommended_next_stage: {summary['recommended_next_stage']}",
        f"- stage5j_closure_pass: {summary['stage5j_closure_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    delivery_status = _run_delivery_check()
    print(f"stage5j_verification_xlsx: {OUT_VERIFY_XLSX}")
    print(f"stage5j_report_md: {OUT_REPORT_MD}")
    print(f"stage5j_summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5j_closure_pass: {summary['stage5j_closure_pass']}")
    print(f"delivery_overall_status: {delivery_status.get('overall_status', 'UNKNOWN')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
