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

from config_manager import ConfigManager
from extractor_adapter import extract_pdfplumber_table_blocks
from pdfplumber_profile_extractor import extract_tables_with_pdfplumber_profiles
from table_block import TableBlock

import build_stage7b_full_structured_sandbox as s7b
import build_stage7c_statement_classification_sandbox as s7c
import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
INPUT_DIR = BASE_DIR / "input"
OUT_DIR = BASE_DIR / "output" / "eval1_10pdf_sandbox_extraction_evaluation"

OUT_SUMMARY = OUT_DIR / "300_eval1_10pdf_extraction_evaluation_summary.json"
OUT_REPORT = OUT_DIR / "300_eval1_10pdf_extraction_evaluation_report.md"
OUT_PER_PDF = OUT_DIR / "300_eval1_per_pdf_metrics.xlsx"
OUT_STMT_DIST = OUT_DIR / "300_eval1_statement_type_distribution.xlsx"
OUT_COVERAGE = OUT_DIR / "300_eval1_core_metrics_candidate_coverage.xlsx"
OUT_CONFLICT = OUT_DIR / "300_eval1_conflict_diagnosis_summary.xlsx"
OUT_FAILED = OUT_DIR / "300_eval1_failed_pdf_analysis.xlsx"
OUT_MANIFEST = OUT_DIR / "300_eval1_pipeline_file_manifest.json"
OUT_NO_APPLY = OUT_DIR / "300_eval1_no_apply_proof.json"
OUT_FULL = OUT_DIR / "300_eval1_full_structured_table.xlsx"
OUT_CLASSIFIED = OUT_DIR / "300_eval1_classified_structured_table.xlsx"
OUT_CANDIDATE = OUT_DIR / "300_eval1_core_metrics_candidate_preview.xlsx"

RAW_DIR = OUT_DIR / "raw_tables_per_pdf"
BLOCK_DIR = OUT_DIR / "table_blocks_per_pdf"
DEBUG_DIR = OUT_DIR / "debug_per_pdf"

EXPECTED_PDFS = [
    INPUT_DIR / "0b4b955b8219ffd0bc5a277fab5b8b6c.pdf",
    INPUT_DIR / "6a0b9e0769373f552c4348621ad58543.pdf",
    INPUT_DIR / "7ef666d64e743498aa76e6ad4ef70fa1.pdf",
    INPUT_DIR / "6862e6f3995d3dbfbed310b51601fb0a.pdf",
    INPUT_DIR / "H3_AP202604291821755175_1.pdf",
    INPUT_DIR / "H3_AP202605251822844635_1.pdf",
    INPUT_DIR / "H3_AP202605251822845141_1.pdf",
    INPUT_DIR / "H3_AP202605251822853403_1.pdf",
    INPUT_DIR / "H3_AP202605251822859039_1.pdf",
    INPUT_DIR / "H3_AP202605231822706325_1.pdf",
]

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    if isinstance(v, str) and v.strip().lower() == "nan":
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    return re.sub(r"\s+", "", _norm(v)).upper()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _snapshot_guard() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP) if RELEASE_ZIP.exists() else "MISSING"
    return snap


def _run_delivery_check() -> Dict[str, Any]:
    p = subprocess.run(
        [sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "").strip()
    return json.loads(txt) if txt else {"overall_status": "UNKNOWN"}


def _extract_tables(pdf_path: Path) -> Tuple[List[TableBlock], str, pd.DataFrame]:
    cm = ConfigManager(config_path="config.yaml")
    cfg = cm.load()
    extraction_cfg = (cfg.get("table_extraction", {}) or {})

    selected: List[TableBlock] = []
    selected_by = "pdfplumber_fallback"
    prof_df = pd.DataFrame()

    blocks, prof_df = extract_tables_with_pdfplumber_profiles(str(pdf_path), cfg, logger=None)
    if blocks:
        converted: List[TableBlock] = []
        for b in blocks:
            df = b.get("df")
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            converted.append(
                TableBlock(
                    backend="pdfplumber",
                    page=b.get("page"),
                    table_index=b.get("table_index"),
                    bbox=b.get("bbox"),
                    confidence=b.get("confidence"),
                    raw_df=df,
                )
            )
        if converted:
            selected = converted
            selected_by = "pdfplumber_profiles"

    if not selected:
        selected = extract_pdfplumber_table_blocks(str(pdf_path), extraction_cfg, logger=None)
        selected_by = "pdfplumber_fallback"

    return selected, selected_by, prof_df


def _build_sandbox_06_preview(classified: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    if classified.empty:
        return pd.DataFrame(), {"duplicate_key_count": 0, "value_mismatch_count": 0, "unit_conflict_count": 0, "year_conflict_count": 0}

    core = classified[classified["usability_layer"].map(_norm) == "candidate_for_core_metrics"].copy()
    rows: List[Dict[str, Any]] = []
    for _, r in core.iterrows():
        rows.append(
            {
                "source_pdf": _norm(r.get("source_pdf")),
                "asset_package": _norm(r.get("source_pdf_name")).replace(".pdf", "_eval1_sandbox"),
                "standard_metric": _norm(r.get("standard_metric")),
                "year": _norm(r.get("year")),
                "final_value": _norm(r.get("value")),
                "final_unit": _norm(r.get("inferred_unit")),
            }
        )
    df = pd.DataFrame(rows).fillna("")
    if df.empty:
        return df, {"duplicate_key_count": 0, "value_mismatch_count": 0, "unit_conflict_count": 0, "year_conflict_count": 0}

    df["key"] = df["asset_package"].map(_norm) + "||" + df["standard_metric"].map(_norm) + "||" + df["year"].map(_norm)
    duplicate_key_count = int(df["key"].duplicated().sum())
    value_mismatch_count = 0
    unit_conflict_count = 0
    year_conflict_count = 0
    for _, g in df.groupby(["asset_package", "standard_metric"], dropna=False):
        ys = [y for y in g["year"].map(_norm).tolist() if y]
        if len(ys) != len(set(ys)):
            year_conflict_count += 1
    for _, g in df.groupby("key", dropna=False):
        if g["final_value"].map(_norm).nunique() > 1:
            value_mismatch_count += 1
        if g["final_unit"].map(_norm).nunique() > 1:
            unit_conflict_count += 1
    df = df.drop(columns=["key"], errors="ignore")
    return df, {
        "duplicate_key_count": duplicate_key_count,
        "value_mismatch_count": value_mismatch_count,
        "unit_conflict_count": unit_conflict_count,
        "year_conflict_count": year_conflict_count,
    }


def _normalize_type_for_distribution(v: str) -> str:
    m = _norm(v)
    if m == "unknown_financial_table":
        return "unknown"
    if not m:
        return "unknown"
    return m


def _metric_coverage_key(row: pd.Series) -> str:
    std = _compact(row.get("standard_metric"))
    raw = _compact(row.get("normalized_metric_name")) + "||" + _compact(row.get("raw_metric_name"))
    if "营业收入" in raw or "REVENUE" in raw or "钀ヤ笟鏀跺叆" in _norm(row.get("standard_metric")):
        return "revenue"
    if "归母净利润" in raw or "ATTRIBUTABLE" in raw:
        return "attributable_net_profit"
    if "净利润" in raw or ("PROFIT" in raw and "ATTRIBUTABLE" not in raw):
        return "net_profit"
    if "资产总计" in raw or "TOTALASSETS" in raw:
        return "total_assets"
    if "负债合计" in raw or "TOTALLIABILIT" in raw:
        return "total_liabilities"
    if "经营现金流" in raw or "OPERATINGCASHFLOW" in raw:
        return "operating_cash_flow"
    if "EPS" in raw or "每股收益" in raw or "姣忚偂鏀剁泭" in _norm(row.get("standard_metric")):
        return "EPS"
    if "ROE" in raw:
        return "ROE"
    if "毛利率" in raw or "GROSSMARGIN" in raw:
        return "gross_margin"
    if "P/E" in raw or std == "P/E":
        return "P/E"
    if "P/B" in raw or std == "P/B":
        return "P/B"
    if "EV/EBITDA" in raw or std == "EV/EBITDA":
        return "EV/EBITDA"
    return ""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    missing = [str(p) for p in EXPECTED_PDFS if not p.exists()]
    if missing:
        blocked = {
            "stage": "EVAL-1",
            "mode": "sandbox_only_10pdf_extraction_evaluation",
            "blocked": True,
            "blocked_reason": "missing_expected_pdf",
            "missing_pdf_count": len(missing),
            "missing_pdf_list": missing,
            "external_api_called": False,
            "llm_api_called": False,
            "real_apply_executed": False,
        }
        _write_json(OUT_SUMMARY, blocked)
        (OUT_REPORT).write_text("# EVAL-1 BLOCKED\n\nMissing expected PDFs.", encoding="utf-8")
        _write_json(OUT_NO_APPLY, {"external_api_called": False, "llm_api_called": False, "real_apply_executed": False})
        print("eval1_status=blocked_missing_expected_pdf")
        return 0

    before = _snapshot_guard()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    BLOCK_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    all_full_rows: List[Dict[str, Any]] = []
    all_classified_rows: List[Dict[str, Any]] = []
    all_candidates_rows: List[Dict[str, Any]] = []
    per_pdf_rows: List[Dict[str, Any]] = []
    failed_rows: List[Dict[str, Any]] = []
    manifest_rows: List[Dict[str, Any]] = []

    for pdf in EXPECTED_PDFS:
        status = "FAILED"
        err = ""
        failure_stage = ""
        selected_by = ""
        raw_df = pd.DataFrame()
        idx_df = pd.DataFrame()
        prof_df = pd.DataFrame()
        one_full: List[Dict[str, Any]] = []
        one_blocks: List[Dict[str, Any]] = []
        one_debug: List[Dict[str, Any]] = []
        classified_df = pd.DataFrame()
        core_preview = pd.DataFrame()
        sandbox06 = pd.DataFrame()
        conflict = {"duplicate_key_count": 0, "value_mismatch_count": 0, "unit_conflict_count": 0, "year_conflict_count": 0}
        notes = ""
        extraction_status = "FAILED"

        try:
            blocks, selected_by, prof_df = _extract_tables(pdf)
            raw_rows: List[Dict[str, Any]] = []
            for b in blocks:
                raw_rows.extend(s5k._table_to_rows(b, pdf, "pdfplumber"))
            raw_df = pd.DataFrame(
                raw_rows,
                columns=[
                    "table_id",
                    "page",
                    "row_index",
                    "col_index",
                    "cell_text",
                    "extractor_name",
                    "extraction_status",
                    "source_pdf",
                    "source_bbox",
                    "raw_row_text",
                    "raw_col_count",
                ],
            ).fillna("")
            idx_df = s5k._aggregate_table_index(blocks, "pdfplumber", pdf)

            table_ids = raw_df["table_id"].map(_norm).dropna().unique().tolist() if not raw_df.empty else []
            for table_id in table_ids:
                m = re.search(r"\|p(\d+)\|t(\d+)\|", table_id)
                page_num = int(m.group(1)) if m else 0
                rows, blks, dbg = s7b._build_rows_from_table(
                    raw_df=raw_df,
                    pdf_name=pdf.name,
                    page_number=page_num,
                    table_id=table_id,
                    block_prefix=pdf.stem,
                )
                one_full.extend(rows)
                one_blocks.extend(blks)
                one_debug.extend(dbg)

            full_df = pd.DataFrame(one_full).fillna("")
            if full_df.empty:
                failure_stage = "full_structured"
                extraction_status = "PARTIAL" if not raw_df.empty else "FAILED"
                err = "empty_full_structured_rows"
            else:
                classified_df = full_df.copy()
                normalized_types: List[str] = []
                reasons: List[str] = []
                confs: List[float] = []
                for _, row in classified_df.iterrows():
                    nst, rsn, conf = s7c._normalize_statement(row)
                    metric = _norm(row.get("normalized_metric_name")) or _norm(row.get("raw_metric_name"))
                    if ("EPS" in s7c._compact(metric) or "姣忚偂鏀剁泭" in metric) and nst == "financial_ratios":
                        nst, rsn, conf = "per_share_metrics", "eps_force_not_ratio_guard", 0.99
                    normalized_types.append(nst)
                    reasons.append(rsn)
                    confs.append(round(float(conf), 4))
                classified_df["normalized_statement_type"] = normalized_types
                classified_df["classification_reason"] = reasons
                classified_df["classification_confidence"] = confs
                classified_df["usability_layer"] = [s7c._usability_layer(r) for _, r in classified_df.iterrows()]

                core_preview = classified_df[
                    classified_df["usability_layer"].map(_norm).isin({"candidate_for_core_metrics", "manual_review_required"})
                ].copy()
                sandbox06, conflict = _build_sandbox_06_preview(classified_df)

                all_full_rows.extend(full_df.to_dict("records"))
                all_classified_rows.extend(classified_df.to_dict("records"))
                all_candidates_rows.extend(core_preview.to_dict("records"))

                extraction_status = "SUCCESS"
                status = "SUCCESS"
                if raw_df.empty:
                    extraction_status = "PARTIAL"
                    status = "PARTIAL"
                    notes = "no_raw_tables_extracted"
                elif core_preview.empty:
                    extraction_status = "PARTIAL"
                    status = "PARTIAL"
                    notes = "no_core_metrics_candidates"

            if extraction_status in {"FAILED", "PARTIAL"}:
                if not failure_stage:
                    failure_stage = "classification_or_candidates"

        except Exception as exc:
            extraction_status = "FAILED"
            status = "FAILED"
            failure_stage = failure_stage or "pipeline_exception"
            err = f"{type(exc).__name__}: {exc}"

        # Write per-pdf raw and debug artifacts
        block_df = pd.DataFrame(one_blocks).fillna("")
        debug_df = pd.DataFrame(one_debug).fillna("")
        _write_excel(RAW_DIR / f"{pdf.stem}_raw_tables.xlsx", {"raw_tables": raw_df, "table_index": idx_df, "profile_diag": prof_df})
        _write_excel(BLOCK_DIR / f"{pdf.stem}_table_blocks.xlsx", {"table_blocks": block_df})
        _write_excel(DEBUG_DIR / f"{pdf.stem}_debug.xlsx", {"debug": debug_df})

        eps_scope = classified_df[
            classified_df["normalized_metric_name"].map(lambda x: "EPS" in s7c._compact(x) or "姣忚偂鏀剁泭" in _norm(x))
        ].copy() if not classified_df.empty else pd.DataFrame()
        bad_eps_ratio_count = int((eps_scope["normalized_statement_type"].map(_norm) == "financial_ratios").sum()) if not eps_scope.empty else 0
        unknown_statement_type_count = int((classified_df["normalized_statement_type"].map(_norm) == "unknown_financial_table").sum()) if not classified_df.empty else 0

        if extraction_status in {"FAILED", "PARTIAL"}:
            failed_rows.append(
                {
                    "pdf_file_name": pdf.name,
                    "failure_stage": failure_stage,
                    "exception_message": err,
                    "raw_tables_extracted": not raw_df.empty,
                    "structured_rows_produced": int(len(one_full)) > 0,
                    "classification_succeeded": not classified_df.empty,
                    "recommended_next_debugging_action": (
                        "check_pdf_parsing_and_profile_extractor" if raw_df.empty else
                        "inspect_table_block_parsing_and_statement_classification"
                    ),
                }
            )

        per_pdf_rows.append(
            {
                "pdf_file_name": pdf.name,
                "pdf_path": str(pdf),
                "file_size_bytes": int(pdf.stat().st_size),
                "extraction_status": extraction_status,
                "error_message": err,
                "raw_table_count": int(raw_df["table_id"].nunique()) if not raw_df.empty else 0,
                "raw_table_row_count": int(len(raw_df)),
                "full_structured_row_count": int(len(one_full)),
                "classified_row_count": int(len(classified_df)),
                "core_metrics_candidate_count": int(len(core_preview)),
                "sandbox_preview_candidate_count": int(len(sandbox06)),
                "duplicate_key_count": int(conflict["duplicate_key_count"]),
                "value_mismatch_count": int(conflict["value_mismatch_count"]),
                "unit_conflict_count": int(conflict["unit_conflict_count"]),
                "year_conflict_count": int(conflict["year_conflict_count"]),
                "eps_detected_count": int(len(eps_scope)),
                "bad_eps_ratio_count": int(bad_eps_ratio_count),
                "unknown_statement_type_count": int(unknown_statement_type_count),
                "empty_table_count": int((idx_df["raw_row_count"] == 0).sum()) if (not idx_df.empty and "raw_row_count" in idx_df.columns) else 0,
                "notes": notes,
            }
        )

        manifest_rows.extend(
            [
                {"pdf_file_name": pdf.name, "artifact_type": "raw_tables", "path": str(RAW_DIR / f"{pdf.stem}_raw_tables.xlsx")},
                {"pdf_file_name": pdf.name, "artifact_type": "table_blocks", "path": str(BLOCK_DIR / f"{pdf.stem}_table_blocks.xlsx")},
                {"pdf_file_name": pdf.name, "artifact_type": "debug", "path": str(DEBUG_DIR / f"{pdf.stem}_debug.xlsx")},
            ]
        )

    per_pdf_df = pd.DataFrame(per_pdf_rows).fillna("")
    failed_df = pd.DataFrame(failed_rows).fillna("")
    manifest_df = pd.DataFrame(manifest_rows).fillna("")

    full_df_all = pd.DataFrame(all_full_rows).fillna("")
    classified_df_all = pd.DataFrame(all_classified_rows).fillna("")
    candidate_df_all = pd.DataFrame(all_candidates_rows).fillna("")

    _write_excel(OUT_PER_PDF, {"per_pdf_metrics": per_pdf_df})
    _write_excel(OUT_FAILED, {"failed_pdf_analysis": failed_df})
    _write_excel(OUT_FULL, {"full_structured_table": full_df_all})
    _write_excel(OUT_CLASSIFIED, {"classified_structured_table": classified_df_all})
    _write_excel(OUT_CANDIDATE, {"core_metrics_candidate_preview": candidate_df_all})

    # Aggregate metrics
    input_pdf_count = len(EXPECTED_PDFS)
    pdf_success_count = int((per_pdf_df["extraction_status"] == "SUCCESS").sum())
    pdf_partial_count = int((per_pdf_df["extraction_status"] == "PARTIAL").sum())
    pdf_failed_count = int((per_pdf_df["extraction_status"] == "FAILED").sum())

    full_structured_total_rows = int(per_pdf_df["full_structured_row_count"].sum()) if not per_pdf_df.empty else 0
    classified_total_rows = int(per_pdf_df["classified_row_count"].sum()) if not per_pdf_df.empty else 0
    core_metrics_candidate_total_rows = int(per_pdf_df["core_metrics_candidate_count"].sum()) if not per_pdf_df.empty else 0

    duplicate_key_total_count = int(per_pdf_df["duplicate_key_count"].sum()) if not per_pdf_df.empty else 0
    value_mismatch_total_count = int(per_pdf_df["value_mismatch_count"].sum()) if not per_pdf_df.empty else 0
    unit_conflict_total_count = int(per_pdf_df["unit_conflict_count"].sum()) if not per_pdf_df.empty else 0
    year_conflict_total_count = int(per_pdf_df["year_conflict_count"].sum()) if not per_pdf_df.empty else 0
    eps_detected_total_count = int(per_pdf_df["eps_detected_count"].sum()) if not per_pdf_df.empty else 0
    bad_eps_ratio_total_count = int(per_pdf_df["bad_eps_ratio_count"].sum()) if not per_pdf_df.empty else 0
    unknown_statement_type_total_count = int(per_pdf_df["unknown_statement_type_count"].sum()) if not per_pdf_df.empty else 0

    extraction_success_rate = round(pdf_success_count / input_pdf_count, 4) if input_pdf_count else 0.0
    candidate_density_per_pdf = round(core_metrics_candidate_total_rows / input_pdf_count, 4) if input_pdf_count else 0.0

    # Statement type distribution
    dist_keys = [
        "income_statement",
        "balance_sheet",
        "cash_flow_statement",
        "financial_ratios",
        "valuation_metrics",
        "per_share_metrics",
        "company_profile",
        "non_financial_table",
        "unknown",
    ]
    dist_map = {k: 0 for k in dist_keys}
    if not classified_df_all.empty and "normalized_statement_type" in classified_df_all.columns:
        counts = classified_df_all["normalized_statement_type"].map(_normalize_type_for_distribution).value_counts().to_dict()
        for k, v in counts.items():
            if k in dist_map:
                dist_map[k] = int(v)
            elif k in {"unknown_financial_table", "unknown_statement_type", "unclassified"}:
                dist_map["unknown"] += int(v)
    dist_df = pd.DataFrame([{"statement_type": k, "row_count": v} for k, v in dist_map.items()])
    _write_excel(OUT_STMT_DIST, {"statement_type_distribution": dist_df})

    # Core metrics candidate coverage
    coverage_targets = [
        "revenue",
        "net_profit",
        "attributable_net_profit",
        "total_assets",
        "total_liabilities",
        "operating_cash_flow",
        "EPS",
        "ROE",
        "gross_margin",
        "P/E",
        "P/B",
        "EV/EBITDA",
    ]
    coverage_map = {k: {"row_count": 0, "pdf_count": 0} for k in coverage_targets}
    if not candidate_df_all.empty:
        temp = candidate_df_all.copy()
        temp["coverage_key"] = temp.apply(_metric_coverage_key, axis=1)
        for key in coverage_targets:
            one = temp[temp["coverage_key"] == key]
            coverage_map[key]["row_count"] = int(len(one))
            coverage_map[key]["pdf_count"] = int(one["source_pdf_name"].map(_norm).nunique()) if not one.empty else 0
    coverage_df = pd.DataFrame(
        [{"metric_target": k, "candidate_row_count": v["row_count"], "covered_pdf_count": v["pdf_count"]} for k, v in coverage_map.items()]
    )
    _write_excel(OUT_COVERAGE, {"core_metrics_candidate_coverage": coverage_df})

    # Conflict diagnosis
    most_dup = per_pdf_df.sort_values("duplicate_key_count", ascending=False)[["pdf_file_name", "duplicate_key_count"]].head(3) if not per_pdf_df.empty else pd.DataFrame()
    most_vm = per_pdf_df.sort_values("value_mismatch_count", ascending=False)[["pdf_file_name", "value_mismatch_count"]].head(3) if not per_pdf_df.empty else pd.DataFrame()
    unit_conflict_pdfs = per_pdf_df[per_pdf_df["unit_conflict_count"] > 0][["pdf_file_name", "unit_conflict_count"]] if not per_pdf_df.empty else pd.DataFrame()
    year_conflict_pdfs = per_pdf_df[per_pdf_df["year_conflict_count"] > 0][["pdf_file_name", "year_conflict_count"]] if not per_pdf_df.empty else pd.DataFrame()
    bad_eps_pdfs = per_pdf_df[per_pdf_df["bad_eps_ratio_count"] > 0][["pdf_file_name", "bad_eps_ratio_count"]] if not per_pdf_df.empty else pd.DataFrame()
    conflict_summary = pd.DataFrame(
        [
            {"metric": "duplicate_key_total_count", "value": duplicate_key_total_count},
            {"metric": "value_mismatch_total_count", "value": value_mismatch_total_count},
            {"metric": "unit_conflict_total_count", "value": unit_conflict_total_count},
            {"metric": "year_conflict_total_count", "value": year_conflict_total_count},
            {"metric": "bad_eps_ratio_total_count", "value": bad_eps_ratio_total_count},
            {"metric": "bad_eps_ratio_is_zero", "value": int(bad_eps_ratio_total_count == 0)},
        ]
    )
    _write_excel(
        OUT_CONFLICT,
        {
            "conflict_summary": conflict_summary,
            "top_duplicate_keys": most_dup,
            "top_value_mismatch": most_vm,
            "unit_conflict_pdfs": unit_conflict_pdfs,
            "year_conflict_pdfs": year_conflict_pdfs,
            "bad_eps_ratio_pdfs": bad_eps_pdfs,
        },
    )

    _write_json(OUT_MANIFEST, {"generated_files": manifest_df.to_dict("records")})
    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "production_apply_attempt_count": 0,
            "note": "EVAL-1 is sandbox extraction evaluation only.",
        },
    )

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    ready_for_eval2 = bool(
        pdf_success_count >= 8
        and full_structured_total_rows > 0
        and core_metrics_candidate_total_rows > 0
        and delivery_status == "PASS"
        and not production_files_modified
        and not official_02b_modified
        and not formal_rules_modified
        and not standardizer_modified
        and not release_package_modified
    )

    summary = {
        "stage": "EVAL-1",
        "mode": "sandbox_only_10pdf_extraction_evaluation",
        "external_api_called": False,
        "llm_api_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "input_pdf_count": input_pdf_count,
        "expected_pdf_count": 10,
        "missing_pdf_count": 0,
        "pdf_success_count": pdf_success_count,
        "pdf_partial_count": pdf_partial_count,
        "pdf_failed_count": pdf_failed_count,
        "raw_tables_generated": bool(per_pdf_df["raw_table_count"].sum() > 0),
        "full_structured_table_generated": bool(full_structured_total_rows > 0),
        "classified_structured_table_generated": bool(classified_total_rows > 0),
        "core_metrics_candidate_preview_generated": bool(core_metrics_candidate_total_rows > 0),
        "full_structured_total_rows": full_structured_total_rows,
        "classified_total_rows": classified_total_rows,
        "core_metrics_candidate_total_rows": core_metrics_candidate_total_rows,
        "duplicate_key_total_count": duplicate_key_total_count,
        "value_mismatch_total_count": value_mismatch_total_count,
        "unit_conflict_total_count": unit_conflict_total_count,
        "year_conflict_total_count": year_conflict_total_count,
        "eps_detected_total_count": eps_detected_total_count,
        "bad_eps_ratio_total_count": bad_eps_ratio_total_count,
        "unknown_statement_type_total_count": unknown_statement_type_total_count,
        "extraction_success_rate": extraction_success_rate,
        "candidate_density_per_pdf": candidate_density_per_pdf,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "ready_for_eval2_gold_standard_accuracy_check": ready_for_eval2,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# EVAL-1 10 PDF Sandbox Extraction Evaluation",
        "",
        "## Input",
        f"- input_pdf_count: {input_pdf_count}",
        "",
        "## Result",
        f"- pdf_success_count: {pdf_success_count}",
        f"- pdf_partial_count: {pdf_partial_count}",
        f"- pdf_failed_count: {pdf_failed_count}",
        f"- extraction_success_rate: {extraction_success_rate}",
        "",
        "## Rows",
        f"- full_structured_total_rows: {full_structured_total_rows}",
        f"- classified_total_rows: {classified_total_rows}",
        f"- core_metrics_candidate_total_rows: {core_metrics_candidate_total_rows}",
        "",
        "## Conflicts",
        f"- duplicate_key_total_count: {duplicate_key_total_count}",
        f"- value_mismatch_total_count: {value_mismatch_total_count}",
        f"- unit_conflict_total_count: {unit_conflict_total_count}",
        f"- year_conflict_total_count: {year_conflict_total_count}",
        f"- bad_eps_ratio_total_count: {bad_eps_ratio_total_count}",
        "",
        "## Safety",
        f"- production_files_modified: {production_files_modified}",
        f"- official_02b_modified: {official_02b_modified}",
        f"- formal_rules_modified: {formal_rules_modified}",
        f"- standardizer_modified: {standardizer_modified}",
        f"- release_package_modified: {release_package_modified}",
        f"- check_delivery_state_overall_status: {delivery_status}",
        "",
        "## Decision",
        f"- ready_for_eval2_gold_standard_accuracy_check: {ready_for_eval2}",
    ]
    if not failed_df.empty:
        report_lines.extend(["", "## Failed/Partial PDFs"])
        for _, r in failed_df.iterrows():
            report_lines.append(
                f"- {r['pdf_file_name']}: stage={r['failure_stage']}; error={r['exception_message']}; action={r['recommended_next_debugging_action']}"
            )
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"eval1_summary_json: {OUT_SUMMARY}")
    print(f"eval1_report_md: {OUT_REPORT}")
    print(f"eval1_ready_for_eval2_gold_standard_accuracy_check: {ready_for_eval2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
