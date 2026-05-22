import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import financial_standardizer as fs


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

STAGE5C_DIR = OUTPUT_DIR / "stage5c_raw_tables_to_structured_02"
INPUT_02_XLSX = STAGE5C_DIR / "130_stage5c_structured_02_sandbox.xlsx"
INPUT_02_REPORT_XLSX = STAGE5C_DIR / "130_stage5c_raw_to_02_conversion_report.xlsx"
INPUT_02_SUMMARY_JSON = STAGE5C_DIR / "131_stage5c_raw_to_02_summary.json"

FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

OUT_DIR = OUTPUT_DIR / "stage5d_standardize_sandbox_02_to_05"
OUT_05_XLSX = OUT_DIR / "132_stage5d_sandbox_05_standardized.xlsx"
OUT_REPORT_XLSX = OUT_DIR / "132_stage5d_standardization_report.xlsx"
OUT_REPORT_MD = OUT_DIR / "132_stage5d_standardization_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "133_stage5d_standardization_summary.json"

STATUS_STANDARDIZED_OK = "STANDARDIZED_OK"
STATUS_MAPPING_MISS = "MAPPING_MISS"
STATUS_SCOPE_MISS = "SCOPE_MISS"
STATUS_NORMALIZATION_MISS = "NORMALIZATION_MISS"
STATUS_VALUE_INVALID = "VALUE_INVALID"
STATUS_UNIT_INVALID = "UNIT_INVALID"
STATUS_YEAR_INVALID = "YEAR_INVALID"
STATUS_DUPLICATE_CANDIDATE = "DUPLICATE_CANDIDATE"
STATUS_AMBIGUOUS_MAPPING = "AMBIGUOUS_MAPPING"
STATUS_STANDARDIZATION_FAILED = "STANDARDIZATION_FAILED"

ALL_STATUSES = {
    STATUS_STANDARDIZED_OK,
    STATUS_MAPPING_MISS,
    STATUS_SCOPE_MISS,
    STATUS_NORMALIZATION_MISS,
    STATUS_VALUE_INVALID,
    STATUS_UNIT_INVALID,
    STATUS_YEAR_INVALID,
    STATUS_DUPLICATE_CANDIDATE,
    STATUS_AMBIGUOUS_MAPPING,
    STATUS_STANDARDIZATION_FAILED,
}

ISSUE_NONE = "NONE"
ISSUE_MAPPING = "METRIC_MAPPING_ISSUE"
ISSUE_SCOPE = "SCOPE_RULE_ISSUE"
ISSUE_NORMALIZATION = "NORMALIZATION_ISSUE"
ISSUE_VUY = "VALUE_UNIT_YEAR_ISSUE"
ISSUE_DUPLICATE = "DUPLICATE_KEY"
ISSUE_AMBIGUOUS = "AMBIGUOUS_STANDARD_METRIC"
ISSUE_SCHEMA = "SCHEMA_MISMATCH"
ISSUE_UNKNOWN = "UNKNOWN"

ALL_ISSUES = {
    ISSUE_NONE,
    ISSUE_MAPPING,
    ISSUE_SCOPE,
    ISSUE_NORMALIZATION,
    ISSUE_VUY,
    ISSUE_DUPLICATE,
    ISSUE_AMBIGUOUS,
    ISSUE_SCHEMA,
    ISSUE_UNKNOWN,
}

YEAR_VALID_RE = re.compile(r"^20\d{2}([AE])?$", re.IGNORECASE)
VALUE_NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?$")

OUT_COLUMNS = [
    "asset_package",
    "source_pdf",
    "source_page",
    "source_table_id",
    "raw_metric_name",
    "standard_metric",
    "year",
    "value",
    "unit",
    "statement_type",
    "mapping_rule_id",
    "scope_rule_id",
    "normalization_rule_id",
    "source_reference",
    "row_trace_id",
    "standardization_status",
    "standardization_issue_type",
    "standardization_issue_reason",
]


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    return re.sub(r"\s+", "", _norm(v)).upper()


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
    }


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    text = (p.stdout or "").strip()
    if not text:
        return {"overall_status": "UNKNOWN"}
    return json.loads(text)


def _load_formal_scope_rules(path: Path) -> Dict[str, Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rules = payload.get("rules", {})
    return rules if isinstance(rules, dict) else {}


def _metric_alias_matches(raw_metric: str) -> List[Dict[str, str]]:
    raw_n = _norm(raw_metric)
    if not raw_n:
        return []
    raw_c = _compact(raw_n)
    out: List[Dict[str, str]] = []
    for standard_metric, aliases in fs.STANDARD_METRIC_ALIASES.items():
        for alias in aliases:
            if raw_n == _norm(alias):
                out.append({"standard_metric": _norm(standard_metric), "alias": _norm(alias), "method": "exact"})
            elif raw_c == _compact(alias):
                out.append({"standard_metric": _norm(standard_metric), "alias": _norm(alias), "method": "normalized"})
    uniq: Dict[str, Dict[str, str]] = {}
    for x in out:
        uniq[x["standard_metric"]] = x
    return list(uniq.values())


def _is_year_valid(year: str) -> bool:
    return bool(YEAR_VALID_RE.fullmatch(_norm(year).upper()))


def _is_value_valid(value: str) -> bool:
    v = _norm(value).replace(",", "")
    return bool(v and VALUE_NUM_RE.fullmatch(v))


def _to_number(value: str) -> float:
    try:
        return float(_norm(value).replace(",", ""))
    except Exception:
        return 0.0


def _is_unit_valid(unit: str) -> bool:
    return _norm(unit) != ""


def _mapping_rule_id(standard_metric: str) -> str:
    return f"FS_MAP_{_compact(standard_metric)}"


def _normalization_rule_id(match_method: str) -> str:
    mm = _norm(match_method)
    if mm in {"normalized_fuzzy", "ev_prefix_noise_guard"}:
        return f"FS_NORM_{mm.upper()}"
    return ""


def _scope_applies(rule: Dict[str, Any], asset_package: str, statement_type: str) -> bool:
    scopes = rule.get("scope_applicability", [])
    scopes = [_norm(x) for x in scopes] if isinstance(scopes, list) else []
    if "GLOBAL_ALIAS_MATCH_ONLY" in scopes:
        return True

    asset_scope = rule.get("asset_packages", [])
    asset_scope = [_norm(x) for x in asset_scope] if isinstance(asset_scope, list) else []
    stmt_scope = rule.get("statement_types", [])
    stmt_scope = [_norm(x) for x in stmt_scope] if isinstance(stmt_scope, list) else []

    asset_ok = True if not asset_scope else (_norm(asset_package) in asset_scope or "*" in asset_scope)
    stmt_ok = True if not stmt_scope else (_norm(statement_type) in stmt_scope or "*" in stmt_scope)
    return bool(asset_ok and stmt_ok)


def _pick_scope_rule(
    standard_metric: str,
    asset_package: str,
    statement_type: str,
    scope_rules: Dict[str, Dict[str, Any]],
) -> Tuple[str, bool, str]:
    metric = _norm(standard_metric)
    candidates: List[Tuple[str, Dict[str, Any]]] = []
    for rid, rule in scope_rules.items():
        if _norm(rule.get("standard_metric")) == metric:
            candidates.append((rid, rule))
    if not candidates:
        return "", True, "no metric-specific scope rule; default allow"
    for rid, rule in candidates:
        if _scope_applies(rule, asset_package, statement_type):
            return rid, True, "scope matched"
    return "", False, "metric has scope rules but none apply to current asset_package/statement_type"


def _safe_status(v: str) -> str:
    return v if v in ALL_STATUSES else STATUS_STANDARDIZATION_FAILED


def _safe_issue(v: str) -> str:
    return v if v in ALL_ISSUES else ISSUE_UNKNOWN


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5D standardize sandbox 02 to sandbox 05.")
    parser.parse_args()

    required = [
        INPUT_02_XLSX,
        INPUT_02_REPORT_XLSX,
        INPUT_02_SUMMARY_JSON,
        FORMAL_SCOPE_RULES_JSON,
        FORMAL_NORMALIZATION_RULE_FILE,
        OFFICIAL_02B_PATH,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    before = _snapshot_hashes()

    df_02 = pd.read_excel(INPUT_02_XLSX, sheet_name="structured_02_sandbox").fillna("")
    summary_5c = json.loads(INPUT_02_SUMMARY_JSON.read_text(encoding="utf-8"))
    scope_rules = _load_formal_scope_rules(FORMAL_SCOPE_RULES_JSON)

    required_02_cols = [
        "asset_package",
        "source_pdf",
        "source_page",
        "source_table_id",
        "raw_metric_name",
        "year",
        "value",
        "unit",
        "statement_type",
        "source_reference",
        "row_trace_id",
        "parse_status",
    ]
    missing_cols = [c for c in required_02_cols if c not in df_02.columns]

    input_structured_02_row_count = int(len(df_02))
    ready_mask = (df_02["parse_status"].map(_norm) == "STRUCTURED_OK") if "parse_status" in df_02.columns else pd.Series([False] * len(df_02))
    df_ready = df_02[ready_mask].copy() if not df_02.empty else pd.DataFrame(columns=df_02.columns)
    input_ready_for_standardization_count = int(len(df_ready))

    out_rows: List[Dict[str, Any]] = []

    if missing_cols:
        out_rows.append(
            {
                "asset_package": "",
                "source_pdf": "",
                "source_page": "",
                "source_table_id": "",
                "raw_metric_name": "",
                "standard_metric": "",
                "year": "",
                "value": "",
                "unit": "",
                "statement_type": "",
                "mapping_rule_id": "",
                "scope_rule_id": "",
                "normalization_rule_id": "",
                "source_reference": "",
                "row_trace_id": "",
                "standardization_status": STATUS_STANDARDIZATION_FAILED,
                "standardization_issue_type": ISSUE_SCHEMA,
                "standardization_issue_reason": f"missing columns in sandbox 02: {','.join(missing_cols)}",
            }
        )
    else:
        for _, row in df_ready.iterrows():
            asset_package = _norm(row.get("asset_package"))
            source_pdf = _norm(row.get("source_pdf"))
            source_page = _norm(row.get("source_page"))
            source_table_id = _norm(row.get("source_table_id"))
            raw_metric_name = _norm(row.get("raw_metric_name"))
            year = _norm(row.get("year")).upper()
            value = _norm(row.get("value")).replace(",", "")
            unit = _norm(row.get("unit"))
            statement_type = _norm(row.get("statement_type"))
            source_reference = _norm(row.get("source_reference"))
            row_trace_id = _norm(row.get("row_trace_id"))

            standard_metric = ""
            mapping_rule_id = ""
            scope_rule_id = ""
            normalization_rule_id = ""
            status = STATUS_STANDARDIZATION_FAILED
            issue_type = ISSUE_UNKNOWN
            issue_reason = "unexpected standardization path"

            alias_hits = _metric_alias_matches(raw_metric_name)
            if len(alias_hits) > 1:
                status = STATUS_AMBIGUOUS_MAPPING
                issue_type = ISSUE_AMBIGUOUS
                issue_reason = "raw metric matches multiple standard metrics by alias"
            else:
                metric_match = fs._match_standard_metric(raw_metric_name)
                if not metric_match:
                    cleaned = fs._clean_metric_label_noise(raw_metric_name)
                    hint = _compact(raw_metric_name)
                    if cleaned != raw_metric_name or any(k in hint for k in ["ROE", "EPS", "PE", "PB", "EBITDA", "%"]):
                        status = STATUS_NORMALIZATION_MISS
                        issue_type = ISSUE_NORMALIZATION
                        issue_reason = "metric appears finance-related but no normalization/mapping hit"
                    else:
                        status = STATUS_MAPPING_MISS
                        issue_type = ISSUE_MAPPING
                        issue_reason = "no mapping rule hit for raw metric"
                else:
                    standard_metric = _norm(metric_match.get("standard_metric"))
                    mapping_rule_id = _mapping_rule_id(standard_metric)
                    normalization_rule_id = _normalization_rule_id(_norm(metric_match.get("match_method")))

                    scope_rule_id, scope_ok, scope_reason = _pick_scope_rule(
                        standard_metric=standard_metric,
                        asset_package=asset_package,
                        statement_type=statement_type,
                        scope_rules=scope_rules,
                    )
                    if not scope_ok:
                        status = STATUS_SCOPE_MISS
                        issue_type = ISSUE_SCOPE
                        issue_reason = scope_reason
                    elif not _is_year_valid(year):
                        status = STATUS_YEAR_INVALID
                        issue_type = ISSUE_VUY
                        issue_reason = "year token invalid for standardized candidate"
                    elif not _is_value_valid(value):
                        status = STATUS_VALUE_INVALID
                        issue_type = ISSUE_VUY
                        issue_reason = "value token invalid for standardized candidate"
                    elif not _is_unit_valid(unit):
                        status = STATUS_UNIT_INVALID
                        issue_type = ISSUE_VUY
                        issue_reason = "unit missing for standardized candidate"
                    else:
                        status = STATUS_STANDARDIZED_OK
                        issue_type = ISSUE_NONE
                        issue_reason = "mapping/scope/normalization/year/value/unit checks passed"

            out_rows.append(
                {
                    "asset_package": asset_package,
                    "source_pdf": source_pdf,
                    "source_page": source_page,
                    "source_table_id": source_table_id,
                    "raw_metric_name": raw_metric_name,
                    "standard_metric": standard_metric,
                    "year": year,
                    "value": value,
                    "unit": unit,
                    "statement_type": statement_type,
                    "mapping_rule_id": mapping_rule_id,
                    "scope_rule_id": scope_rule_id,
                    "normalization_rule_id": normalization_rule_id,
                    "source_reference": source_reference,
                    "row_trace_id": row_trace_id,
                    "standardization_status": _safe_status(status),
                    "standardization_issue_type": _safe_issue(issue_type),
                    "standardization_issue_reason": issue_reason,
                }
            )

    out_df = pd.DataFrame(out_rows, columns=OUT_COLUMNS).fillna("")

    # Duplicate candidate handling on already standardized rows.
    if not out_df.empty:
        ok_mask = out_df["standardization_status"] == STATUS_STANDARDIZED_OK
        ok_df = out_df[ok_mask].copy()
        if not ok_df.empty:
            ok_df["_value_num"] = ok_df["value"].map(_to_number)
            ok_df["_source_page_num"] = pd.to_numeric(ok_df["source_page"], errors="coerce").fillna(999999)
            ok_df["_score"] = (
                ok_df["_value_num"].abs() * 0 + 1
            )  # stable placeholder; keep deterministic sort by source page/row trace
            ok_df = ok_df.sort_values(
                by=["asset_package", "standard_metric", "year", "_source_page_num", "row_trace_id"],
                kind="mergesort",
            )
            dup_groups = ok_df.groupby(["asset_package", "standard_metric", "year"], dropna=False)
            duplicate_trace_ids: List[str] = []
            for _, g in dup_groups:
                if len(g) <= 1:
                    continue
                # Keep first, mark the rest as duplicate candidates.
                duplicate_trace_ids.extend(g.iloc[1:]["row_trace_id"].map(_norm).tolist())
            if duplicate_trace_ids:
                dup_mask = out_df["row_trace_id"].map(_norm).isin(set(duplicate_trace_ids))
                out_df.loc[dup_mask, "standardization_status"] = STATUS_DUPLICATE_CANDIDATE
                out_df.loc[dup_mask, "standardization_issue_type"] = ISSUE_DUPLICATE
                out_df.loc[dup_mask, "standardization_issue_reason"] = "duplicate key candidate: asset_package+standard_metric+year"

    sandbox_05_row_count = int(len(out_df))
    standardized_ok_count = int((out_df["standardization_status"] == STATUS_STANDARDIZED_OK).sum()) if not out_df.empty else 0
    mapping_miss_count = int((out_df["standardization_status"] == STATUS_MAPPING_MISS).sum()) if not out_df.empty else 0
    scope_miss_count = int((out_df["standardization_status"] == STATUS_SCOPE_MISS).sum()) if not out_df.empty else 0
    normalization_miss_count = int((out_df["standardization_status"] == STATUS_NORMALIZATION_MISS).sum()) if not out_df.empty else 0
    value_invalid_count = int((out_df["standardization_status"] == STATUS_VALUE_INVALID).sum()) if not out_df.empty else 0
    unit_invalid_count = int((out_df["standardization_status"] == STATUS_UNIT_INVALID).sum()) if not out_df.empty else 0
    year_invalid_count = int((out_df["standardization_status"] == STATUS_YEAR_INVALID).sum()) if not out_df.empty else 0
    duplicate_candidate_count = int((out_df["standardization_status"] == STATUS_DUPLICATE_CANDIDATE).sum()) if not out_df.empty else 0
    ambiguous_mapping_count = int((out_df["standardization_status"] == STATUS_AMBIGUOUS_MAPPING).sum()) if not out_df.empty else 0
    standardization_failed_count = int((out_df["standardization_status"] == STATUS_STANDARDIZATION_FAILED).sum()) if not out_df.empty else 0

    unique_standard_metric_count = int(out_df["standard_metric"].map(_norm).replace("", pd.NA).dropna().nunique()) if not out_df.empty else 0
    ready_for_stage5e_auto_trusted_count = int(
        (
            (out_df["standardization_status"] == STATUS_STANDARDIZED_OK)
            & (out_df["standard_metric"].map(_norm) != "")
            & (out_df["year"].map(_norm) != "")
            & (out_df["value"].map(_norm) != "")
        ).sum()
    ) if not out_df.empty else 0

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
    formal_normalization_rules_unchanged = bool(
        before["formal_normalization_rules"] == after["formal_normalization_rules"]
    )

    summary = {
        "input_structured_02_row_count": int(input_structured_02_row_count),
        "input_ready_for_standardization_count": int(input_ready_for_standardization_count),
        "sandbox_05_row_count": int(sandbox_05_row_count),
        "standardized_ok_count": int(standardized_ok_count),
        "mapping_miss_count": int(mapping_miss_count),
        "scope_miss_count": int(scope_miss_count),
        "normalization_miss_count": int(normalization_miss_count),
        "value_invalid_count": int(value_invalid_count),
        "unit_invalid_count": int(unit_invalid_count),
        "year_invalid_count": int(year_invalid_count),
        "duplicate_candidate_count": int(duplicate_candidate_count),
        "ambiguous_mapping_count": int(ambiguous_mapping_count),
        "standardization_failed_count": int(standardization_failed_count),
        "unique_standard_metric_count": int(unique_standard_metric_count),
        "ready_for_stage5e_auto_trusted_count": int(ready_for_stage5e_auto_trusted_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_scope_rules_unchanged": bool(formal_scope_rules_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "formal_normalization_rules_unchanged": bool(formal_normalization_rules_unchanged),
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage5d_standardization_pass": False,
    }

    summary["stage5d_standardization_pass"] = bool(
        summary["input_ready_for_standardization_count"] == 442
        and summary["sandbox_05_row_count"] > 0
        and summary["standardized_ok_count"] > 0
        and summary["standardization_failed_count"] != summary["input_ready_for_standardization_count"]
        and summary["ready_for_stage5e_auto_trusted_count"] > 0
        and summary["production_files_unchanged"]
        and summary["official_02B_unchanged"]
        and summary["formal_scope_rules_unchanged"]
        and summary["formal_mapping_rules_unchanged"]
        and summary["formal_normalization_rules_unchanged"]
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    status_breakdown_df = (
        out_df.groupby(["standardization_status", "standardization_issue_type"], dropna=False)
        .size()
        .reset_index(name="row_count")
        .sort_values(["row_count", "standardization_status"], ascending=[False, True])
        if not out_df.empty
        else pd.DataFrame(columns=["standardization_status", "standardization_issue_type", "row_count"])
    )
    summary_df = pd.DataFrame([summary])
    sample_ok_df = out_df[out_df["standardization_status"] == STATUS_STANDARDIZED_OK].head(300) if not out_df.empty else pd.DataFrame(columns=OUT_COLUMNS)
    sample_issue_df = out_df[out_df["standardization_status"] != STATUS_STANDARDIZED_OK].head(300) if not out_df.empty else pd.DataFrame(columns=OUT_COLUMNS)

    _write_excel(OUT_05_XLSX, {"sandbox_05_standardized": out_df})
    _write_excel(
        OUT_REPORT_XLSX,
        {
            "summary": summary_df,
            "status_breakdown": status_breakdown_df,
            "standardized_ok_sample": sample_ok_df,
            "non_ok_sample": sample_issue_df,
            "stage5c_summary_ref": pd.DataFrame([summary_5c]),
        },
    )

    md_lines = [
        "# Stage5D Sandbox 02 To 05 Standardization",
        "",
        f"- input_structured_02_row_count: {summary['input_structured_02_row_count']}",
        f"- input_ready_for_standardization_count: {summary['input_ready_for_standardization_count']}",
        f"- sandbox_05_row_count: {summary['sandbox_05_row_count']}",
        f"- standardized_ok_count: {summary['standardized_ok_count']}",
        f"- mapping_miss_count: {summary['mapping_miss_count']}",
        f"- scope_miss_count: {summary['scope_miss_count']}",
        f"- normalization_miss_count: {summary['normalization_miss_count']}",
        f"- value_invalid_count: {summary['value_invalid_count']}",
        f"- unit_invalid_count: {summary['unit_invalid_count']}",
        f"- year_invalid_count: {summary['year_invalid_count']}",
        f"- duplicate_candidate_count: {summary['duplicate_candidate_count']}",
        f"- ambiguous_mapping_count: {summary['ambiguous_mapping_count']}",
        f"- standardization_failed_count: {summary['standardization_failed_count']}",
        f"- unique_standard_metric_count: {summary['unique_standard_metric_count']}",
        f"- ready_for_stage5e_auto_trusted_count: {summary['ready_for_stage5e_auto_trusted_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_scope_rules_unchanged: {summary['formal_scope_rules_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- formal_normalization_rules_unchanged: {summary['formal_normalization_rules_unchanged']}",
        f"- stage5d_standardization_pass: {summary['stage5d_standardization_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"sandbox_05_xlsx: {OUT_05_XLSX}")
    print(f"standardization_report_xlsx: {OUT_REPORT_XLSX}")
    print(f"standardization_report_md: {OUT_REPORT_MD}")
    print(f"summary_json: {OUT_SUMMARY_JSON}")
    print(f"input_ready_for_standardization_count: {summary['input_ready_for_standardization_count']}")
    print(f"standardized_ok_count: {summary['standardized_ok_count']}")
    print(f"ready_for_stage5e_auto_trusted_count: {summary['ready_for_stage5e_auto_trusted_count']}")
    print(f"stage5d_standardization_pass: {summary['stage5d_standardization_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
