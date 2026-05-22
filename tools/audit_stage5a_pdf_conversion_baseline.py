import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from financial_standardizer import standardize_core_financials


BASE_DIR = Path(r"D:\_datefac")
INPUT_DIR = BASE_DIR / "input"
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
OUT_DIR = BASE_DIR / "output" / "stage5a_pdf_conversion_audit"
SANDBOX_DIR = OUT_DIR / "sandbox"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES_PATH = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"

OUT_XLSX = OUT_DIR / "126_stage5a_pdf_conversion_audit.xlsx"
OUT_MD = OUT_DIR / "126_stage5a_pdf_conversion_audit.md"
OUT_JSON = OUT_DIR / "127_stage5a_pdf_conversion_audit_summary.json"


YEAR_RE = re.compile(r"\b(20\d{2}(?:[AE])?)\b", re.IGNORECASE)
NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")

ISSUE_TYPES = {
    "PDF_PARSE_ISSUE",
    "TABLE_EXTRACTION_ISSUE",
    "STRUCTURED_SCHEMA_ISSUE",
    "METRIC_MAPPING_ISSUE",
    "SCOPE_RULE_ISSUE",
    "NORMALIZATION_ISSUE",
    "VALUE_UNIT_YEAR_ISSUE",
    "FINAL_METRIC_SELECTION_ISSUE",
    "NO_ACTION",
}


@dataclass
class ExtractedTable:
    page: int
    table_index: int
    df: pd.DataFrame


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    return re.sub(r"\s+", "", _norm(v)).upper()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = s
    idx = 1
    while s in used:
        suffix = f"_{idx}"
        s = f"{base[:31-len(suffix)]}{suffix}"
        idx += 1
    used.add(s)
    return s


def _find_delivery_file(pattern: str) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing delivery file by pattern: {pattern}")
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
        "formal_scope_rules": _sha256(FORMAL_SCOPE_RULES_PATH),
    }


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    text = (p.stdout or "").strip()
    if not text:
        return {"overall_status": "UNKNOWN"}
    return json.loads(text)


def _normalize_table_df(raw_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    if raw_df is None or raw_df.empty:
        return None
    df = raw_df.fillna("").astype(str)
    df = df.apply(lambda c: c.map(lambda x: re.sub(r"\s+", " ", _norm(x))))
    df = df.loc[(df != "").any(axis=1), (df != "").any(axis=0)]
    if df.empty:
        return None

    header_row_idx = None
    for ridx in range(min(3, len(df))):
        cells = [_norm(x) for x in df.iloc[ridx].tolist()]
        year_hits = sum(1 for cell in cells if YEAR_RE.search(cell))
        if year_hits >= 2:
            header_row_idx = ridx
            break

    if header_row_idx is not None:
        header = [_norm(x) or f"col_{i}" for i, x in enumerate(df.iloc[header_row_idx].tolist())]
        body = df.iloc[header_row_idx + 1 :].copy()
        body.columns = _make_unique(header)
        body = body.reset_index(drop=True)
        body = body.loc[(body != "").any(axis=1)]
        return body if not body.empty else None

    df = df.reset_index(drop=True)
    df.columns = _make_unique([f"col_{i}" for i in range(df.shape[1])])
    return df


def _make_unique(cols: List[str]) -> List[str]:
    out: List[str] = []
    seen: Dict[str, int] = {}
    for c in cols:
        base = _norm(c) or "col"
        if base not in seen:
            seen[base] = 0
            out.append(base)
        else:
            seen[base] += 1
            out.append(f"{base}.{seen[base]}")
    return out


def _extract_tables_pdfplumber(pdf_path: Path) -> Tuple[List[ExtractedTable], List[Dict[str, Any]]]:
    issues: List[Dict[str, Any]] = []
    tables: List[ExtractedTable] = []
    try:
        import pdfplumber  # type: ignore
    except Exception as exc:
        issues.append(
            {
                "issue_type": "PDF_PARSE_ISSUE",
                "layer": "PDF",
                "severity": "HIGH",
                "entity_key": pdf_path.name,
                "description": f"pdfplumber unavailable: {type(exc).__name__}",
                "evidence": str(exc),
            }
        )
        return tables, issues

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for pidx, page in enumerate(pdf.pages, start=1):
                page_tables = page.extract_tables() or []
                for tidx, table in enumerate(page_tables, start=1):
                    raw = pd.DataFrame(table) if table else pd.DataFrame()
                    df = _normalize_table_df(raw)
                    if df is None:
                        continue
                    tables.append(ExtractedTable(page=pidx, table_index=tidx, df=df))
    except Exception as exc:
        issues.append(
            {
                "issue_type": "PDF_PARSE_ISSUE",
                "layer": "PDF",
                "severity": "HIGH",
                "entity_key": pdf_path.name,
                "description": "failed during pdfplumber extraction",
                "evidence": f"{type(exc).__name__}: {exc}",
            }
        )
        return tables, issues

    if not tables:
        issues.append(
            {
                "issue_type": "TABLE_EXTRACTION_ISSUE",
                "layer": "02A",
                "severity": "HIGH",
                "entity_key": pdf_path.name,
                "description": "no non-empty tables extracted",
                "evidence": "pdfplumber extracted zero normalized tables",
            }
        )
    return tables, issues


def _guess_unit(metric_label: str, value_raw: str) -> str:
    m = _norm(metric_label)
    v = _norm(value_raw)
    if "%" in v or "率" in m.upper():
        return "%"
    if "每股" in m or "EPS" in _compact(m):
        return "元"
    if any(x in m for x in ["P/E", "P/B", "EV/EBITDA"]):
        return "倍"
    return ""


def _build_structured_02_rows(asset_package: str, tables: List[ExtractedTable]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for t in tables:
        col_year_map: Dict[str, str] = {}
        for c in t.df.columns.tolist():
            m = YEAR_RE.search(_norm(c))
            if m:
                col_year_map[c] = m.group(1).upper()

        label_col = t.df.columns[0] if len(t.df.columns) > 0 else ""

        for ridx, row in t.df.iterrows():
            raw_label = _norm(row.get(label_col, ""))
            if not raw_label:
                # fallback: first non-empty non-numeric cell in first 3 columns
                for c in t.df.columns[:3]:
                    cv = _norm(row.get(c, ""))
                    if cv and not NUM_RE.fullmatch(cv.replace(",", "")):
                        raw_label = cv
                        break
            if not raw_label:
                continue

            for c in t.df.columns:
                if c == label_col:
                    continue
                year = col_year_map.get(c, "")
                cell = _norm(row.get(c, ""))
                if not cell:
                    continue
                n = NUM_RE.search(cell.replace(",", ""))
                if not n:
                    continue
                value = n.group(0)
                rows.append(
                    {
                        "asset_package": asset_package,
                        "raw_metric_name": raw_label,
                        "value": value,
                        "year": year,
                        "unit": _guess_unit(raw_label, cell),
                        "source_page": t.page,
                        "source_reference": f"p{t.page}_t{t.table_index}_r{int(ridx)+1}_c{c}",
                        "source_table_index": t.table_index,
                    }
                )
    return rows


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _count_missing_required(df: pd.DataFrame, cols: List[str]) -> int:
    missing = 0
    for c in cols:
        if c not in df.columns:
            missing += len(df)
        else:
            missing += int(df[c].map(lambda x: _norm(x) == "").sum())
    return int(missing)


def _add_issue(
    issues: List[Dict[str, Any]],
    issue_type: str,
    layer: str,
    severity: str,
    entity_key: str,
    description: str,
    evidence: str,
) -> None:
    if issue_type not in ISSUE_TYPES:
        issue_type = "NO_ACTION"
    issues.append(
        {
            "issue_type": issue_type,
            "layer": layer,
            "severity": severity,
            "entity_key": entity_key,
            "description": description,
            "evidence": evidence,
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5A end-to-end PDF conversion baseline audit (sandbox only).")
    parser.add_argument("--pdf", default="", help="Optional absolute PDF path. If empty, auto-pick from input/")
    args = parser.parse_args()

    snapshot_before = _snapshot_hashes()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    input_pdf = Path(args.pdf) if _norm(args.pdf) else None
    if input_pdf is None:
        candidates = sorted(INPUT_DIR.glob("*.pdf"))
        if not candidates:
            raise FileNotFoundError(f"No PDF found under {INPUT_DIR}")
        input_pdf = candidates[0]
    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

    sample_id = input_pdf.stem
    asset_package = f"{sample_id}_stage5a"
    sandbox_sample_dir = SANDBOX_DIR / sample_id
    sandbox_sample_dir.mkdir(parents=True, exist_ok=True)

    issues: List[Dict[str, Any]] = []

    tables, parse_issues = _extract_tables_pdfplumber(input_pdf)
    issues.extend(parse_issues)

    # Build sandbox 02 structured rows from extracted tables.
    rows_02 = _build_structured_02_rows(asset_package, tables)
    df_02 = pd.DataFrame(rows_02)
    if df_02.empty:
        df_02 = pd.DataFrame(
            columns=[
                "asset_package",
                "raw_metric_name",
                "value",
                "year",
                "unit",
                "source_page",
                "source_reference",
                "source_table_index",
            ]
        )

    # Build 05 with financial standardizer.
    df_list = [t.df for t in tables]
    std_result = standardize_core_financials(df_list=df_list, classification_results=None, logger=None, config=None)
    df_05_wide = std_result.get("wide_df", pd.DataFrame()).fillna("")
    df_05_detail = std_result.get("detail_df", pd.DataFrame()).fillna("")

    # 01/06 are not generated by this sandbox conversion path.
    df_01 = pd.DataFrame(columns=["asset_package", "standard_metric", "year", "value", "unit"])
    df_06 = pd.DataFrame(columns=["asset_package", "standard_metric", "year", "final_value", "final_unit"])

    # Write sandbox conversion artifacts.
    path_02 = sandbox_sample_dir / "02_研报全量结构化数据.xlsx"
    path_05 = sandbox_sample_dir / "05_核心财务指标标准化.xlsx"
    _write_excel(path_02, {"structured_02": df_02})
    _write_excel(path_05, {"核心指标宽表": df_05_wide, "抽取明细": df_05_detail})

    # Optional files (empty placeholders for explicit pipeline boundary).
    path_01 = sandbox_sample_dir / "01_自动可信核心指标.xlsx"
    path_06 = sandbox_sample_dir / "06_最终核心财务指标.xlsx"
    _write_excel(path_01, {"auto_trusted_01": df_01})
    _write_excel(path_06, {"final_06": df_06})

    # ---- Quality checks ----
    # Structure checks.
    required_02_cols = ["asset_package", "raw_metric_name", "value", "year", "unit", "source_page", "source_reference"]
    for c in required_02_cols:
        if c not in df_02.columns:
            _add_issue(issues, "STRUCTURED_SCHEMA_ISSUE", "02", "HIGH", c, "required column missing in 02", c)

    if len(df_02) == 0:
        _add_issue(issues, "TABLE_EXTRACTION_ISSUE", "02", "HIGH", sample_id, "02 has zero rows after extraction", "structured_02_row_count=0")

    required_05_cols = ["标准指标", "来源指标名", "value_validation_status"]
    for c in required_05_cols:
        if c not in df_05_wide.columns:
            _add_issue(issues, "STRUCTURED_SCHEMA_ISSUE", "05", "MEDIUM", c, "required column missing in 05 wide", c)

    # 02 checks.
    missing_02_fields = _count_missing_required(df_02, ["raw_metric_name", "value", "year", "unit", "source_page", "source_reference"])
    if missing_02_fields > 0:
        _add_issue(
            issues,
            "STRUCTURED_SCHEMA_ISSUE",
            "02",
            "MEDIUM",
            sample_id,
            "missing required fields in 02 rows",
            f"missing_required_field_count={missing_02_fields}",
        )

    dup_02_count = 0
    if not df_02.empty:
        dup_02_count = int(
            df_02.duplicated(
                subset=["asset_package", "raw_metric_name", "year", "value", "unit", "source_page"],
                keep=False,
            ).sum()
        )
    if dup_02_count > 0:
        _add_issue(
            issues,
            "STRUCTURED_SCHEMA_ISSUE",
            "02",
            "MEDIUM",
            sample_id,
            "duplicate rows detected in 02",
            f"duplicate_rows={dup_02_count}",
        )

    # 05 checks and mapping miss analysis.
    mapped_raw_labels = set(df_05_detail["source_row_label"].map(_norm).tolist()) if "source_row_label" in df_05_detail.columns else set()
    raw_labels_02 = set(df_02["raw_metric_name"].map(_norm).tolist()) if "raw_metric_name" in df_02.columns else set()
    raw_labels_02 = {x for x in raw_labels_02 if x}
    mapping_miss = sorted(raw_labels_02 - mapped_raw_labels)
    if mapping_miss:
        _add_issue(
            issues,
            "METRIC_MAPPING_ISSUE",
            "05",
            "MEDIUM",
            sample_id,
            "raw_metric_name in 02 not mapped to 05 standard metrics",
            f"mapping_miss_count={len(mapping_miss)}",
        )

    # Normalization miss heuristic: compact-equal but not exact label.
    normalization_miss_count = 0
    if mapped_raw_labels and raw_labels_02:
        compact_mapped = {_compact(x) for x in mapped_raw_labels if x}
        for r in mapping_miss:
            if _compact(r) in compact_mapped:
                normalization_miss_count += 1
    if normalization_miss_count > 0:
        _add_issue(
            issues,
            "NORMALIZATION_ISSUE",
            "05",
            "LOW",
            sample_id,
            "potential normalization mismatch between 02 raw label and 05 mapping",
            f"normalization_miss_count={normalization_miss_count}",
        )

    # Scope miss heuristic is not directly derivable in this isolated flow; record as NO_ACTION.
    _add_issue(
        issues,
        "NO_ACTION",
        "SCOPE",
        "INFO",
        sample_id,
        "scope-rule miss not deterministically inferable in isolated pdfplumber+standardizer baseline flow",
        "scope_rule_issue_count treated as 0 in stage5a baseline",
    )

    # 01/06 checks (flow support boundary).
    _add_issue(
        issues,
        "FINAL_METRIC_SELECTION_ISSUE",
        "01/06",
        "LOW",
        sample_id,
        "this sandbox baseline flow does not generate trusted/final selection outputs",
        "01 and 06 are placeholders with zero business rows",
    )

    # Link breakpoints.
    # 02 -> 05
    if mapping_miss:
        _add_issue(
            issues,
            "METRIC_MAPPING_ISSUE",
            "CHAIN",
            "MEDIUM",
            sample_id,
            "chain breakpoint: 02 has records not entering 05",
            f"breakpoint_02_to_05={len(mapping_miss)}",
        )
    # 05 -> 01 and 01 -> 06
    if len(df_05_detail) > 0 and len(df_01) == 0:
        _add_issue(
            issues,
            "FINAL_METRIC_SELECTION_ISSUE",
            "CHAIN",
            "LOW",
            sample_id,
            "chain breakpoint: 05 has candidates but 01 layer not produced in this flow",
            "breakpoint_05_to_01=1",
        )
    if len(df_01) == 0 and len(df_06) == 0:
        _add_issue(
            issues,
            "FINAL_METRIC_SELECTION_ISSUE",
            "CHAIN",
            "LOW",
            sample_id,
            "chain breakpoint: 01 layer absent and 06 layer absent in this flow",
            "breakpoint_01_to_06=1",
        )

    # Value/unit/year checks
    value_unit_year_issue_count = 0
    if not df_02.empty:
        value_unit_year_issue_count = int(
            df_02["value"].map(lambda x: _norm(x) == "").sum()
            + df_02["year"].map(lambda x: _norm(x) == "").sum()
            + df_02["unit"].map(lambda x: _norm(x) == "").sum()
        )
    if value_unit_year_issue_count > 0:
        _add_issue(
            issues,
            "VALUE_UNIT_YEAR_ISSUE",
            "02",
            "MEDIUM",
            sample_id,
            "value/year/unit completeness issues found in 02",
            f"value_unit_year_issue_count={value_unit_year_issue_count}",
        )

    # 06 traceability (with placeholders here -> 0 actual rows)
    upstream_trace_missing_count = 0
    duplicate_key_count = 0

    issues_df = pd.DataFrame(issues)
    if issues_df.empty:
        issues_df = pd.DataFrame(
            columns=["issue_type", "layer", "severity", "entity_key", "description", "evidence"]
        )

    def _count_issue(t: str) -> int:
        if issues_df.empty:
            return 0
        return int((issues_df["issue_type"] == t).sum())

    snapshot_after = _snapshot_hashes()
    production_files_unchanged = (
        snapshot_before["01"] == snapshot_after["01"]
        and snapshot_before["02"] == snapshot_after["02"]
        and snapshot_before["02A"] == snapshot_after["02A"]
        and snapshot_before["05"] == snapshot_after["05"]
        and snapshot_before["06"] == snapshot_after["06"]
    )
    official_02B_unchanged = snapshot_before["02B"] == snapshot_after["02B"]
    formal_scope_rules_unchanged = snapshot_before["formal_scope_rules"] == snapshot_after["formal_scope_rules"]

    summary = {
        "input_pdf_file": str(input_pdf),
        "sandbox_output_dir": str(sandbox_sample_dir),
        "structured_02_row_count": int(len(df_02)),
        "standardized_05_row_count": int(len(df_05_detail)),
        "auto_trusted_01_row_count": int(len(df_01)),
        "final_06_row_count": int(len(df_06)),
        "parse_issue_count": _count_issue("PDF_PARSE_ISSUE"),
        "table_extraction_issue_count": _count_issue("TABLE_EXTRACTION_ISSUE"),
        "structured_schema_issue_count": _count_issue("STRUCTURED_SCHEMA_ISSUE"),
        "metric_mapping_issue_count": _count_issue("METRIC_MAPPING_ISSUE"),
        "scope_rule_issue_count": _count_issue("SCOPE_RULE_ISSUE"),
        "normalization_issue_count": _count_issue("NORMALIZATION_ISSUE"),
        "value_unit_year_issue_count": _count_issue("VALUE_UNIT_YEAR_ISSUE"),
        "final_metric_selection_issue_count": _count_issue("FINAL_METRIC_SELECTION_ISSUE"),
        "duplicate_key_count": int(duplicate_key_count),
        "missing_required_field_count": int(missing_02_fields),
        "upstream_trace_missing_count": int(upstream_trace_missing_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_scope_rules_unchanged": bool(formal_scope_rules_unchanged),
        "ai_called": False,
        "internet_called": False,
        "stage5a_audit_pass": bool(
            production_files_unchanged
            and official_02B_unchanged
            and formal_scope_rules_unchanged
            and _count_issue("PDF_PARSE_ISSUE") == 0
        ),
    }

    summary_df = pd.DataFrame([summary])
    table_overview_df = pd.DataFrame(
        [
            {
                "sheet": "structured_02",
                "exists": True,
                "row_count": len(df_02),
                "col_count": len(df_02.columns),
            },
            {
                "sheet": "standardized_05_wide",
                "exists": True,
                "row_count": len(df_05_wide),
                "col_count": len(df_05_wide.columns),
            },
            {
                "sheet": "standardized_05_detail",
                "exists": True,
                "row_count": len(df_05_detail),
                "col_count": len(df_05_detail.columns),
            },
            {
                "sheet": "auto_trusted_01",
                "exists": True,
                "row_count": len(df_01),
                "col_count": len(df_01.columns),
            },
            {
                "sheet": "final_06",
                "exists": True,
                "row_count": len(df_06),
                "col_count": len(df_06.columns),
            },
        ]
    )

    _write_excel(
        OUT_XLSX,
        {
            "issues": issues_df,
            "summary": summary_df,
            "table_overview": table_overview_df,
            "structured_02_sample": df_02.head(300),
            "standardized_05_detail": df_05_detail.head(300),
        },
    )

    md_lines = [
        "# Stage5A PDF Conversion Baseline Audit",
        "",
        f"- input_pdf_file: {summary['input_pdf_file']}",
        f"- sandbox_output_dir: {summary['sandbox_output_dir']}",
        f"- structured_02_row_count: {summary['structured_02_row_count']}",
        f"- standardized_05_row_count: {summary['standardized_05_row_count']}",
        f"- auto_trusted_01_row_count: {summary['auto_trusted_01_row_count']}",
        f"- final_06_row_count: {summary['final_06_row_count']}",
        f"- parse_issue_count: {summary['parse_issue_count']}",
        f"- table_extraction_issue_count: {summary['table_extraction_issue_count']}",
        f"- structured_schema_issue_count: {summary['structured_schema_issue_count']}",
        f"- metric_mapping_issue_count: {summary['metric_mapping_issue_count']}",
        f"- scope_rule_issue_count: {summary['scope_rule_issue_count']}",
        f"- normalization_issue_count: {summary['normalization_issue_count']}",
        f"- value_unit_year_issue_count: {summary['value_unit_year_issue_count']}",
        f"- final_metric_selection_issue_count: {summary['final_metric_selection_issue_count']}",
        f"- duplicate_key_count: {summary['duplicate_key_count']}",
        f"- missing_required_field_count: {summary['missing_required_field_count']}",
        f"- upstream_trace_missing_count: {summary['upstream_trace_missing_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_scope_rules_unchanged: {summary['formal_scope_rules_unchanged']}",
        f"- stage5a_audit_pass: {summary['stage5a_audit_pass']}",
        "",
        "## Key Notes",
        "- This audit is sandbox-only and does not perform real apply.",
        "- 01/06 are placeholders in this baseline extraction path; selection logic not promoted in Stage5A.",
    ]
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage5a_audit_xlsx: {OUT_XLSX}")
    print(f"stage5a_audit_md: {OUT_MD}")
    print(f"stage5a_audit_summary: {OUT_JSON}")
    print(f"input_pdf_file: {summary['input_pdf_file']}")
    print(f"sandbox_output_dir: {summary['sandbox_output_dir']}")
    print(f"stage5a_audit_pass: {summary['stage5a_audit_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
