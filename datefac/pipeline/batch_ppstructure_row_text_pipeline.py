from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd

from datefac.extraction.row_text_cleaner import clean_row_texts
from datefac.extraction.row_text_metric_extractor import extract_metric_candidates_from_repaired_rows
from datefac.extraction.row_text_repair import repair_row_fragments
from datefac.governance.risk_splitter import split_candidates_for_sandbox_preview
from datefac.governance.row_text_candidate_mapper import (
    candidates_to_dataframe,
    map_row_text_candidates,
    resolve_duplicates_and_conflicts,
)
from datefac.recognition.legacy_ppstructure_result_reader import read_legacy_ppstructure_results


YEAR_TOKEN_RULE = re.compile(r"\b20\d{2}[AEae]?\b")

CASH_FLOW_METRICS = {
    "net_profit",
    "asset_impairment_provision",
    "depreciation_amortization",
    "fair_value_change_loss",
    "finance_expense",
    "working_capital_change",
    "other_operating_cf",
    "operating_cash_flow",
    "capex",
    "other_investing_cash_flow",
    "investing_cash_flow",
    "equity_financing",
    "debt_net_change",
    "dividend_interest_paid",
    "other_financing_cash_flow",
    "financing_cash_flow",
    "net_cash_change",
    "cash_beginning_balance",
    "cash_ending_balance",
    "free_cash_flow_firm",
    "free_cash_flow_equity",
}
CORE_VALUATION_METRICS = {"eps", "roe", "pe", "pb", "ev_ebitda", "revenue", "net_profit", "gross_margin", "revenue_growth", "net_profit_growth", "debt_ratio"}
INCOME_PREFERRED = {"revenue", "net_profit", "gross_margin", "revenue_growth", "net_profit_growth", "eps"}
BALANCE_PREFERRED = {"debt_ratio"}


@dataclass
class TableRunContext:
    table_run_id: str
    ppstructure_output_dir: Path
    priority: Optional[int]
    report: str
    table_asset_id: str
    table_type: str
    image_path: str
    status_from_batch: str
    warnings: List[str]


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _safe_int(v: Any, default: int = 0) -> int:
    s = _norm(v)
    if not s:
        return default
    try:
        return int(float(s))
    except Exception:
        return default


def _safe_json_load(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _parse_priority_from_name(name: str) -> Optional[int]:
    m = re.match(r"^p(\d+)_", _norm(name))
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def _scan_batch_entries(ppstructure_batch_dir: Path) -> Tuple[List[TableRunContext], List[str], str]:
    warnings: List[str] = []
    status = "OK"
    summary_path = ppstructure_batch_dir / "batch_summary.json"
    summary_items: List[Dict[str, Any]] = []
    if summary_path.exists():
        try:
            loaded = json.loads(summary_path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                summary_items = [x for x in loaded if isinstance(x, dict)]
            else:
                warnings.append("BATCH_SUMMARY_NOT_LIST")
        except Exception:
            warnings.append("BATCH_SUMMARY_PARSE_FAILED")
    else:
        status = "WARN_BATCH_SUMMARY_MISSING_SCAN_SUBDIRS"
        warnings.append("WARN_BATCH_SUMMARY_MISSING_SCAN_SUBDIRS")

    by_output_dir: Dict[str, Dict[str, Any]] = {}
    for item in summary_items:
        out_dir = _norm(item.get("output_dir"))
        if out_dir:
            by_output_dir[str(Path(out_dir).resolve())] = item

    contexts: List[TableRunContext] = []
    for d in sorted([x for x in ppstructure_batch_dir.iterdir() if x.is_dir()]):
        meta = _safe_json_load(d / "table_meta.json")
        suc = _safe_json_load(d / "success.json")
        summary_row = by_output_dir.get(str(d.resolve()), {})

        report = _norm(meta.get("report") or suc.get("report") or summary_row.get("report"))
        table_asset_id = _norm(meta.get("table_asset_id") or suc.get("table_asset_id") or summary_row.get("table_asset_id"))
        table_type = _norm(meta.get("table_type") or suc.get("table_type") or summary_row.get("table_type"))
        image_path = _norm(meta.get("image") or suc.get("image") or summary_row.get("image"))
        status_from_batch = _norm(summary_row.get("status") or suc.get("status") or "UNKNOWN")
        priority = summary_row.get("priority")
        if priority is None:
            priority = meta.get("priority")
        if priority is None:
            priority = _parse_priority_from_name(d.name)
        p_int = _safe_int(priority, default=-1)
        priority_val = p_int if p_int >= 0 else None

        row_warnings: List[str] = []
        if not meta:
            row_warnings.append("MISSING_TABLE_META")
        if not suc:
            row_warnings.append("MISSING_SUCCESS_JSON")
        if not report:
            report = d.name
            row_warnings.append("MISSING_REPORT_FALLBACK_DIRNAME")
        if not table_asset_id:
            table_asset_id = d.name
            row_warnings.append("MISSING_TABLE_ASSET_ID_FALLBACK_DIRNAME")
        if not table_type:
            table_type = "unknown"
            row_warnings.append("MISSING_TABLE_TYPE")

        contexts.append(
            TableRunContext(
                table_run_id=d.name,
                ppstructure_output_dir=d,
                priority=priority_val,
                report=report,
                table_asset_id=table_asset_id,
                table_type=table_type,
                image_path=image_path,
                status_from_batch=status_from_batch,
                warnings=row_warnings,
            )
        )

    return contexts, warnings, status


def _row_text_from_grid_row(row: Iterable[Any]) -> str:
    vals = [_norm(x) for x in row]
    vals = [x for x in vals if x]
    if not vals:
        return ""
    return " ".join(vals)


def _build_raw_rows_for_table(ctx: TableRunContext, extracted_tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    grid_tables = [t for t in extracted_tables if _norm(t.get("recognition_status")).startswith("RECOGNIZED_GRID")]
    use_tables = grid_tables if grid_tables else extracted_tables

    for t in use_tables:
        extracted_table_id = _norm(t.get("extracted_table_id")) or ctx.table_asset_id
        table_grid = t.get("table_grid", [])
        row_texts: List[str] = []

        if isinstance(table_grid, list) and table_grid and isinstance(table_grid[0], list):
            for r in table_grid:
                txt = _row_text_from_grid_row(r)
                if txt:
                    row_texts.append(txt)

        if not row_texts:
            rt = t.get("row_texts", [])
            if isinstance(rt, list):
                row_texts.extend([_norm(x) for x in rt if _norm(x)])

        if not row_texts and _norm(t.get("raw_text")):
            row_texts.extend([x.strip() for x in _norm(t.get("raw_text")).splitlines() if x.strip()])

        for i, rt in enumerate(row_texts):
            rows.append(
                {
                    "source_file": ctx.report,
                    "source_doc_name": ctx.report,
                    "extracted_table_id": extracted_table_id,
                    "row_index": i,
                    "row_text": _norm(rt),
                    "recognition_status": _norm(t.get("recognition_status")),
                    "table_run_id": ctx.table_run_id,
                    "table_asset_id": ctx.table_asset_id,
                    "table_type": ctx.table_type,
                    "priority": ctx.priority,
                    "image_path": ctx.image_path,
                    "ppstructure_output_dir": str(ctx.ppstructure_output_dir),
                }
            )
    return rows


def _detect_context_from_rows(rows: List[Dict[str, Any]], table_type: str) -> Tuple[str, str, Set[str]]:
    txts = [_norm(x.get("row_text")) for x in rows if _norm(x.get("row_text"))]
    title = txts[0] if txts else ""
    unit = ""
    for t in txts[:20]:
        if "百万元" in t:
            unit = "百万元"
            break
        if "万元" in t:
            unit = "万元"
            break
        if "元" in t and "每股" not in t:
            unit = "元"
            break
    if not title:
        title = table_type

    years: Set[str] = set()
    for t in txts[:20]:
        for y in YEAR_TOKEN_RULE.findall(t):
            years.add(_norm(y).upper())
    return title, unit, years


def _append_risk_tag(raw: str, tag: str) -> str:
    parts = [x.strip() for x in _norm(raw).split("|") if x.strip()]
    if tag not in parts:
        parts.append(tag)
    return "|".join(parts)


def _apply_table_type_guard(candidate_rows: List[Dict[str, Any]], table_type: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    t = _norm(table_type).lower()
    for r in candidate_rows:
        rr = dict(r)
        code = _norm(rr.get("metric_code"))
        if t == "cash_flow_statement":
            if code not in CASH_FLOW_METRICS:
                rr["risk_tags"] = _append_risk_tag(rr.get("risk_tags"), "TABLE_TYPE_MISMATCH")
        elif t == "income_statement":
            if code not in INCOME_PREFERRED and code in CASH_FLOW_METRICS:
                rr["risk_tags"] = _append_risk_tag(rr.get("risk_tags"), "TABLE_TYPE_MISMATCH")
        elif t == "balance_sheet":
            if code not in BALANCE_PREFERRED and code in CASH_FLOW_METRICS:
                rr["risk_tags"] = _append_risk_tag(rr.get("risk_tags"), "TABLE_TYPE_MISMATCH")
        elif t in {"financial_summary_valuation", "key_financial_valuation"}:
            if code not in CORE_VALUATION_METRICS:
                rr["risk_tags"] = _append_risk_tag(rr.get("risk_tags"), "TABLE_TYPE_MISMATCH")
        else:
            rr["risk_tags"] = _append_risk_tag(rr.get("risk_tags"), "TABLE_TYPE_UNKNOWN")
        out.append(rr)
    return out


def _add_common_meta(df: pd.DataFrame, ctx: TableRunContext, parse_status: str) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["table_run_id"] = ctx.table_run_id
    out["priority"] = ctx.priority
    out["report"] = ctx.report
    out["table_asset_id"] = ctx.table_asset_id
    out["table_type"] = ctx.table_type
    out["image_path"] = ctx.image_path
    out["ppstructure_output_dir"] = str(ctx.ppstructure_output_dir)
    out["status_from_batch"] = ctx.status_from_batch
    out["parse_status"] = parse_status
    return out


def _metric_family(code: str) -> str:
    c = _norm(code)
    if c in {"net_profit", "eps", "roe", "revenue"}:
        return "profitability"
    if c in {"pe", "pb", "ev_ebitda"}:
        return "valuation"
    if c in {"debt_ratio"}:
        return "balance_sheet"
    if c in CASH_FLOW_METRICS:
        return "cash_flow"
    if "growth" in c:
        return "growth"
    if "margin" in c:
        return "margin"
    return "other"


def _risk_tag_counts(df: pd.DataFrame) -> pd.DataFrame:
    counts: Dict[str, int] = {}
    if df.empty:
        return pd.DataFrame(columns=["risk_tag", "count"])
    for tags in df["risk_tags"].astype(str).tolist():
        for t in [x.strip() for x in tags.split("|") if x.strip()]:
            counts[t] = counts.get(t, 0) + 1
    rows = [{"risk_tag": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]
    return pd.DataFrame(rows)


def _count_risk(df: pd.DataFrame, tag: str) -> int:
    if df.empty:
        return 0
    return int(df["risk_tags"].astype(str).str.contains(rf"(?:^|\|){re.escape(tag)}(?:$|\|)", regex=True).sum())


def _build_provenance_coverage_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "candidate_id",
                "table_run_id",
                "report",
                "metric_code",
                "year",
                "has_source_file",
                "has_source_row_text",
                "has_source_table_id",
                "has_source_stage",
                "has_year_source",
                "has_unit_source",
                "provenance_complete",
                "missing_fields",
            ]
        )

    rows: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        missing: List[str] = []
        has_source_file = bool(_norm(r.get("source_file")))
        has_source_row_text = bool(_norm(r.get("source_row_text")))
        has_source_table_id = bool(_norm(r.get("source_table_id")))
        has_source_stage = bool(_norm(r.get("source_stage")))
        has_year_source = bool(_norm(r.get("year_source")))
        has_unit_source = bool(_norm(r.get("unit_source")))
        if not has_source_file:
            missing.append("source_file")
        if not has_source_row_text:
            missing.append("source_row_text")
        if not has_source_table_id:
            missing.append("source_table_id")
        if not has_source_stage:
            missing.append("source_stage")
        if not has_year_source:
            missing.append("year_source")
        if not has_unit_source:
            missing.append("unit_source")
        rows.append(
            {
                "candidate_id": _norm(r.get("candidate_id")),
                "table_run_id": _norm(r.get("table_run_id")),
                "report": _norm(r.get("report")),
                "metric_code": _norm(r.get("metric_code")),
                "year": _norm(r.get("year")),
                "has_source_file": has_source_file,
                "has_source_row_text": has_source_row_text,
                "has_source_table_id": has_source_table_id,
                "has_source_stage": has_source_stage,
                "has_year_source": has_year_source,
                "has_unit_source": has_unit_source,
                "provenance_complete": len(missing) == 0,
                "missing_fields": "|".join(missing),
            }
        )
    return pd.DataFrame(rows)


def _build_qa_checks(
    inventory_df: pd.DataFrame,
    normalized_df: pd.DataFrame,
    trusted_df: pd.DataFrame,
    provenance_cov_df: pd.DataFrame,
    source_ok_count: int,
) -> Tuple[pd.DataFrame, int, int, int]:
    checks: List[Dict[str, Any]] = []

    def add(check_name: str, status: str, detail: str) -> None:
        checks.append({"check_name": check_name, "status": status, "detail": detail})

    parsed_or_warn = int((inventory_df["parse_status"].astype(str) != "TABLE_PARSE_FAILED").sum()) if not inventory_df.empty else 0
    if parsed_or_warn == source_ok_count:
        add("all_ok_batch_dirs_parsed_or_warned", "PASS", f"ok_dirs={source_ok_count}, parsed_or_warn={parsed_or_warn}")
    else:
        add("all_ok_batch_dirs_parsed_or_warned", "WARN", f"ok_dirs={source_ok_count}, parsed_or_warn={parsed_or_warn}")

    noise_leak = _count_risk(normalized_df, "NOISE_LEAK_BBOX_HTML")
    add("no_bbox_html_noise_candidates_in_normalized_output", "PASS" if noise_leak == 0 else "FAIL", f"noise_leak_count={noise_leak}")

    invalid_year = _count_risk(trusted_df, "INVALID_YEAR") + _count_risk(trusted_df, "YEAR_MISSING")
    add("no_invalid_year_in_trusted_output", "PASS" if invalid_year == 0 else "FAIL", f"invalid_year_count={invalid_year}")

    unknown_metric = _count_risk(trusted_df, "UNKNOWN_METRIC_CODE")
    add("no_unknown_metric_code_in_trusted_output", "PASS" if unknown_metric == 0 else "FAIL", f"unknown_metric_code_count={unknown_metric}")

    dup_conflict = 0
    if not trusted_df.empty:
        dup_conflict = int((trusted_df.groupby(["report", "table_asset_id", "metric_code", "year"], dropna=False)["normalized_value"].nunique() > 1).sum())
    add("no_duplicate_conflict_in_trusted_output", "PASS" if dup_conflict == 0 else "FAIL", f"duplicate_conflict_groups={dup_conflict}")

    prov_rate = float(provenance_cov_df["provenance_complete"].mean()) if not provenance_cov_df.empty else 0.0
    add("provenance_complete_for_trusted_output", "PASS" if prov_rate >= 0.95 else "WARN", f"provenance_complete_rate={prov_rate:.6f}")

    count_match = True
    detail_count = ""
    if not inventory_df.empty:
        inv = int(inventory_df["metric_candidate_count"].sum())
        norm = int(len(normalized_df))
        count_match = inv == norm
        detail_count = f"inventory_metric_candidate_count={inv}, normalized_rows={norm}"
    add("output_counts_match_source_tables", "PASS" if count_match else "WARN", detail_count or "no_inventory")

    meta_missing = int(inventory_df["warnings"].astype(str).str.contains("MISSING_TABLE_META", regex=False).sum()) if not inventory_df.empty else 0
    add("each_table_has_table_meta_or_explicit_warning", "PASS" if meta_missing == 0 else "WARN", f"missing_table_meta_count={meta_missing}")

    chinese_ok = True
    if not normalized_df.empty and "source_row_text" in normalized_df.columns:
        txt = "\n".join(normalized_df["source_row_text"].astype(str).head(200).tolist())
        if "�" in txt or "????" in txt:
            chinese_ok = False
    add("chinese_text_preserved", "PASS" if chinese_ok else "FAIL", "no replacement chars found" if chinese_ok else "found replacement chars")

    qa_df = pd.DataFrame(checks)
    qa_pass = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    return qa_df, qa_pass, qa_warn, qa_fail


def run_batch_ppstructure_row_text_pipeline(ppstructure_batch_dir: Path) -> Dict[str, Any]:
    if not ppstructure_batch_dir.exists():
        return {
            "blocked": True,
            "blocked_code": "BLOCKED_MISSING_PPSTRUCTURE_BATCH_DIR",
            "blocked_message": f"missing input dir: {ppstructure_batch_dir}",
            "summary": {},
            "dataframes": {},
        }

    table_contexts, scan_warnings, batch_scan_status = _scan_batch_entries(ppstructure_batch_dir)

    inventory_rows: List[Dict[str, Any]] = []
    extracted_rows_all: List[Dict[str, Any]] = []
    metric_candidates_all: List[pd.DataFrame] = []
    normalized_all: List[pd.DataFrame] = []
    trusted_all: List[pd.DataFrame] = []
    review_all: List[pd.DataFrame] = []
    rejected_all: List[pd.DataFrame] = []
    table_summary_rows: List[Dict[str, Any]] = []

    for ctx in table_contexts:
        warnings_local = list(ctx.warnings)
        parse_status = "PARSED_OK"

        if _norm(ctx.status_from_batch).upper() in {"FAILED", "IMAGE_MISSING"}:
            parse_status = "TABLE_BLOCKED_MISSING_OUTPUT"
            warnings_local.append(f"STATUS_FROM_BATCH_{_norm(ctx.status_from_batch).upper()}")
            inventory_rows.append(
                {
                    "table_run_id": ctx.table_run_id,
                    "priority": ctx.priority,
                    "report": ctx.report,
                    "table_asset_id": ctx.table_asset_id,
                    "table_type": ctx.table_type,
                    "image_path": ctx.image_path,
                    "ppstructure_output_dir": str(ctx.ppstructure_output_dir),
                    "status_from_batch": ctx.status_from_batch,
                    "parse_status": parse_status,
                    "extracted_table_count": 0,
                    "row_text_count": 0,
                    "metric_candidate_count": 0,
                    "normalized_candidate_count": 0,
                    "trusted_count": 0,
                    "review_required_count": 0,
                    "rejected_count": 0,
                    "warnings": "|".join(warnings_local),
                }
            )
            table_summary_rows.append(
                {
                    "table_run_id": ctx.table_run_id,
                    "report": ctx.report,
                    "table_asset_id": ctx.table_asset_id,
                    "table_type": ctx.table_type,
                    "metric_candidate_count": 0,
                    "normalized_candidate_count": 0,
                    "trusted_count": 0,
                    "review_required_count": 0,
                    "rejected_count": 0,
                    "unique_metric_count": 0,
                    "unique_year_count": 0,
                    "unit_unknown_count": 0,
                    "year_inferred_count": 0,
                    "conflict_count": 0,
                    "qa_status": "WARN",
                    "table_decision": "TABLE_BLOCKED_MISSING_OUTPUT",
                }
            )
            continue

        rr = read_legacy_ppstructure_results(ctx.ppstructure_output_dir)
        extracted_tables = [x.to_dict() for x in rr.extracted_tables]
        extracted_table_count = len(extracted_tables)
        if extracted_table_count == 0:
            parse_status = "TABLE_PARSE_FAILED"
            warnings_local.append("NO_EXTRACTED_TABLES")

        for w in rr.warnings:
            code = _norm(w.get("warning_code"))
            if code:
                warnings_local.append(code)

        raw_rows = _build_raw_rows_for_table(ctx, extracted_tables)
        row_text_count = len(raw_rows)
        extracted_rows_all.extend(raw_rows)

        metric_candidate_count = 0
        normalized_candidate_count = 0
        trusted_count = 0
        review_count = 0
        rejected_count = 0
        unique_metric_count = 0
        unique_year_count = 0
        unit_unknown_count = 0
        year_inferred_count = 0
        conflict_count = 0
        table_decision = "TABLE_ROW_TEXT_PARSED_NO_CANDIDATES"
        qa_status = "WARN"

        if parse_status == "PARSED_OK" and row_text_count > 0:
            cleaned = clean_row_texts(raw_rows)
            repaired = repair_row_fragments(cleaned["cleaned_rows"], expected_year_count=5)
            extracted = extract_metric_candidates_from_repaired_rows(repaired["repaired_rows"], expected_year_count=5)

            for w in cleaned.get("warnings", []):
                code = _norm(w.get("warning_code"))
                if code:
                    warnings_local.append(code)
            for w in repaired.get("warnings", []):
                code = _norm(w.get("warning_code"))
                if code:
                    warnings_local.append(code)
            for w in extracted.get("parse_warnings", []):
                code = _norm(w.get("warning_code"))
                if code:
                    warnings_local.append(code)

            candidate_rows = extracted.get("metric_candidate_preview", [])
            candidate_rows = _apply_table_type_guard(candidate_rows, ctx.table_type)
            metric_candidate_count = len(candidate_rows)

            if metric_candidate_count > 0:
                cand_df = pd.DataFrame(candidate_rows)
                cand_df = _add_common_meta(cand_df, ctx, parse_status)
                metric_candidates_all.append(cand_df)

                table_title, table_unit, header_years = _detect_context_from_rows(raw_rows, ctx.table_type)

                smoke_ids: Set[str] = set()
                smoke_codes: Set[str] = set()
                for r in candidate_rows:
                    tags = [x.strip() for x in _norm(r.get("risk_tags")).split("|") if x.strip()]
                    if "NUMERIC_COUNT_MISMATCH" in tags or "TABLE_TYPE_MISMATCH" in tags:
                        continue
                    cid = _norm(r.get("candidate_row_id"))
                    if cid:
                        smoke_ids.add(cid)
                        smoke_codes.add(_norm(r.get("metric_code")))

                mapped, _, _ = map_row_text_candidates(
                    source_candidate_rows_df=pd.DataFrame(candidate_rows),
                    table_title=table_title,
                    table_unit=table_unit,
                    table_header_years=header_years,
                    smoke_passed_candidate_ids=smoke_ids,
                    smoke_passed_metric_codes=smoke_codes,
                )

                dedup = resolve_duplicates_and_conflicts(mapped)
                canonical = dedup["canonical_candidates"]
                conflict_count = int(dedup["conflict_count"])

                split = split_candidates_for_sandbox_preview(canonical, smoke_passed_candidate_source_ids=smoke_ids)

                normalized_df = candidates_to_dataframe(canonical)
                trusted_df = candidates_to_dataframe(split["trusted_preview"])
                review_df = candidates_to_dataframe(split["review_required_preview"])
                rej_df = candidates_to_dataframe(split["rejected_preview"])

                normalized_df = _add_common_meta(normalized_df, ctx, parse_status)
                trusted_df = _add_common_meta(trusted_df, ctx, parse_status)
                review_df = _add_common_meta(review_df, ctx, parse_status)
                rej_df = _add_common_meta(rej_df, ctx, parse_status)

                normalized_all.append(normalized_df)
                trusted_all.append(trusted_df)
                review_all.append(review_df)
                rejected_all.append(rej_df)

                normalized_candidate_count = int(len(normalized_df))
                trusted_count = int(len(trusted_df))
                review_count = int(len(review_df))
                rejected_count = int(len(rej_df))
                unique_metric_count = int(normalized_df["metric_code"].astype(str).replace("", pd.NA).dropna().nunique()) if not normalized_df.empty else 0
                unique_year_count = int(normalized_df["year"].astype(str).replace("", pd.NA).dropna().nunique()) if not normalized_df.empty else 0
                unit_unknown_count = int(normalized_df["risk_tags"].astype(str).str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True).sum()) if not normalized_df.empty else 0
                year_inferred_count = int((normalized_df["year_source"].astype(str) == "INFERRED_SEQUENCE").sum()) if not normalized_df.empty else 0

                if trusted_count > 0:
                    table_decision = "TABLE_DELIVERY_READY"
                    qa_status = "PASS"
                else:
                    table_decision = "TABLE_USABLE_NEEDS_REVIEW"
                    qa_status = "WARN"
            else:
                table_decision = "TABLE_ROW_TEXT_PARSED_NO_CANDIDATES"
                qa_status = "WARN"
        elif parse_status == "PARSED_OK":
            table_decision = "TABLE_ROW_TEXT_PARSED_NO_CANDIDATES"
            qa_status = "WARN"
        else:
            table_decision = "TABLE_PARSE_FAILED"
            qa_status = "FAIL"

        inventory_rows.append(
            {
                "table_run_id": ctx.table_run_id,
                "priority": ctx.priority,
                "report": ctx.report,
                "table_asset_id": ctx.table_asset_id,
                "table_type": ctx.table_type,
                "image_path": ctx.image_path,
                "ppstructure_output_dir": str(ctx.ppstructure_output_dir),
                "status_from_batch": ctx.status_from_batch,
                "parse_status": parse_status,
                "extracted_table_count": extracted_table_count,
                "row_text_count": row_text_count,
                "metric_candidate_count": metric_candidate_count,
                "normalized_candidate_count": normalized_candidate_count,
                "trusted_count": trusted_count,
                "review_required_count": review_count,
                "rejected_count": rejected_count,
                "warnings": "|".join(sorted(set([x for x in warnings_local if x]))),
            }
        )
        table_summary_rows.append(
            {
                "table_run_id": ctx.table_run_id,
                "report": ctx.report,
                "table_asset_id": ctx.table_asset_id,
                "table_type": ctx.table_type,
                "metric_candidate_count": metric_candidate_count,
                "normalized_candidate_count": normalized_candidate_count,
                "trusted_count": trusted_count,
                "review_required_count": review_count,
                "rejected_count": rejected_count,
                "unique_metric_count": unique_metric_count,
                "unique_year_count": unique_year_count,
                "unit_unknown_count": unit_unknown_count,
                "year_inferred_count": year_inferred_count,
                "conflict_count": conflict_count,
                "qa_status": qa_status,
                "table_decision": table_decision,
            }
        )

    inventory_df = pd.DataFrame(inventory_rows)
    extracted_rows_df = pd.DataFrame(extracted_rows_all)
    metric_candidates_df = pd.concat(metric_candidates_all, ignore_index=True, sort=False) if metric_candidates_all else pd.DataFrame()
    normalized_df = pd.concat(normalized_all, ignore_index=True, sort=False) if normalized_all else pd.DataFrame()
    trusted_df = pd.concat(trusted_all, ignore_index=True, sort=False) if trusted_all else pd.DataFrame()
    review_df = pd.concat(review_all, ignore_index=True, sort=False) if review_all else pd.DataFrame()
    rejected_df = pd.concat(rejected_all, ignore_index=True, sort=False) if rejected_all else pd.DataFrame()
    per_table_df = pd.DataFrame(table_summary_rows)

    if per_table_df.empty:
        per_table_df = pd.DataFrame(
            columns=[
                "table_run_id",
                "report",
                "table_asset_id",
                "table_type",
                "metric_candidate_count",
                "normalized_candidate_count",
                "trusted_count",
                "review_required_count",
                "rejected_count",
                "unique_metric_count",
                "unique_year_count",
                "unit_unknown_count",
                "year_inferred_count",
                "conflict_count",
                "qa_status",
                "table_decision",
            ]
        )

    if not per_table_df.empty:
        per_report_df = per_table_df.groupby("report", dropna=False).agg(
            table_count_processed=("table_run_id", "count"),
            table_count_ready=("table_decision", lambda s: int((pd.Series(s) == "TABLE_DELIVERY_READY").sum())),
            trusted_count=("trusted_count", "sum"),
            review_required_count=("review_required_count", "sum"),
            rejected_count=("rejected_count", "sum"),
            unique_metric_count=("unique_metric_count", "sum"),
            unique_table_type_count=("table_type", lambda s: int(pd.Series(s).replace("", pd.NA).dropna().nunique())),
        ).reset_index()
        per_report_df["report_decision"] = per_report_df.apply(
            lambda r: "REPORT_HAS_DELIVERABLE_TABLES"
            if int(r["table_count_ready"]) > 0
            else ("REPORT_NEEDS_MORE_TABLES" if int(r["table_count_processed"]) > 0 else "REPORT_NO_USEFUL_ROW_TEXT"),
            axis=1,
        )
    else:
        per_report_df = pd.DataFrame(
            columns=[
                "report",
                "table_count_processed",
                "table_count_ready",
                "trusted_count",
                "review_required_count",
                "rejected_count",
                "unique_metric_count",
                "unique_table_type_count",
                "report_decision",
            ]
        )

    if not normalized_df.empty:
        tmp = normalized_df.copy()
        tmp["metric_family"] = tmp["metric_code"].apply(_metric_family)
        metric_cov_df = tmp.groupby(["table_type", "metric_family", "metric_code"], dropna=False).agg(
            candidate_count=("candidate_id", "count"),
            trusted_count=("split_decision", lambda s: int((pd.Series(s) == "trusted_preview").sum())),
            review_required_count=("split_decision", lambda s: int((pd.Series(s) == "review_required_preview").sum())),
            unique_report_count=("report", lambda s: int(pd.Series(s).replace("", pd.NA).dropna().nunique())),
            unique_table_count=("table_asset_id", lambda s: int(pd.Series(s).replace("", pd.NA).dropna().nunique())),
            years_covered=("year", lambda s: "|".join(sorted(set([_norm(x) for x in s.tolist() if _norm(x)])))),
        ).reset_index()
    else:
        metric_cov_df = pd.DataFrame(columns=["table_type", "metric_family", "metric_code", "candidate_count", "trusted_count", "review_required_count", "unique_report_count", "unique_table_count", "years_covered"])

    if not per_table_df.empty:
        type_perf_df = per_table_df.groupby("table_type", dropna=False).agg(
            table_count=("table_run_id", "count"),
            table_ready_count=("table_decision", lambda s: int((pd.Series(s) == "TABLE_DELIVERY_READY").sum())),
            metric_candidate_count=("metric_candidate_count", "sum"),
            normalized_candidate_count=("normalized_candidate_count", "sum"),
            trusted_count=("trusted_count", "sum"),
            review_required_count=("review_required_count", "sum"),
            rejected_count=("rejected_count", "sum"),
        ).reset_index()
        type_perf_df["trusted_rate"] = type_perf_df.apply(
            lambda r: float(r["trusted_count"] / r["normalized_candidate_count"]) if int(r["normalized_candidate_count"]) > 0 else 0.0,
            axis=1,
        )
    else:
        type_perf_df = pd.DataFrame(columns=["table_type", "table_count", "table_ready_count", "metric_candidate_count", "normalized_candidate_count", "trusted_count", "review_required_count", "rejected_count", "trusted_rate"])

    risk_counts_df = _risk_tag_counts(normalized_df)
    provenance_cov_df = _build_provenance_coverage_df(trusted_df)

    batch_table_count = int(len(inventory_df))
    batch_ok_count = int((inventory_df["status_from_batch"].astype(str).str.upper() == "OK").sum()) if not inventory_df.empty else 0
    parsed_table_count = int((inventory_df["parse_status"].astype(str) != "TABLE_PARSE_FAILED").sum()) if not inventory_df.empty else 0
    table_with_row_text_count = int((inventory_df["row_text_count"] > 0).sum()) if not inventory_df.empty else 0
    table_with_candidates_count = int((inventory_df["metric_candidate_count"] > 0).sum()) if not inventory_df.empty else 0
    table_with_trusted_count = int((inventory_df["trusted_count"] > 0).sum()) if not inventory_df.empty else 0
    report_count = int(inventory_df["report"].replace("", pd.NA).dropna().nunique()) if not inventory_df.empty else 0

    trusted_total_count = int(len(trusted_df))
    review_total_count = int(len(review_df))
    rejected_total_count = int(len(rejected_df))
    total_split = trusted_total_count + review_total_count + rejected_total_count

    trusted_rate = float(trusted_total_count / total_split) if total_split > 0 else 0.0
    review_rate = float(review_total_count / total_split) if total_split > 0 else 0.0
    rejected_rate = float(rejected_total_count / total_split) if total_split > 0 else 0.0

    unique_metric_count = int(normalized_df["metric_code"].replace("", pd.NA).dropna().nunique()) if not normalized_df.empty else 0
    unique_year_count = int(normalized_df["year"].replace("", pd.NA).dropna().nunique()) if not normalized_df.empty else 0
    unique_report_count = int(normalized_df["report"].replace("", pd.NA).dropna().nunique()) if not normalized_df.empty else 0

    unit_unknown_count = _count_risk(normalized_df, "UNIT_UNKNOWN")
    year_inferred_count = int((normalized_df["year_source"].astype(str) == "INFERRED_SEQUENCE").sum()) if not normalized_df.empty else 0
    conflict_count = int(per_table_df["conflict_count"].sum()) if not per_table_df.empty else 0
    provenance_complete_rate = float(provenance_cov_df["provenance_complete"].mean()) if not provenance_cov_df.empty else 0.0

    qa_df, qa_pass_count, qa_warn_count, qa_fail_count = _build_qa_checks(
        inventory_df=inventory_df,
        normalized_df=normalized_df,
        trusted_df=trusted_df,
        provenance_cov_df=provenance_cov_df,
        source_ok_count=batch_ok_count,
    )

    if qa_fail_count > 0:
        batch_decision = "BATCH_DELIVERY_BLOCKED_BY_QA_FAILURE"
    elif parsed_table_count >= 8 and table_with_trusted_count >= 5 and trusted_rate >= 0.50 and provenance_complete_rate >= 0.95 and qa_fail_count == 0:
        batch_decision = "BATCH_ROW_TEXT_DELIVERY_READY_FOR_320H_PIPELINE_PLAN"
    elif parsed_table_count >= 5 and table_with_candidates_count >= 3 and qa_fail_count == 0:
        batch_decision = "BATCH_ROW_TEXT_DELIVERY_PARTIAL_NEEDS_CALIBRATION"
    elif parsed_table_count > 0:
        batch_decision = "BATCH_ROW_TEXT_DELIVERY_WEAK_NEEDS_MORE_RECOGNITION_OR_RULES"
    else:
        batch_decision = "BATCH_ROW_TEXT_DELIVERY_NOT_READY"

    top_risk_tags = []
    if not risk_counts_df.empty:
        top_risk_tags = risk_counts_df.head(10).to_dict(orient="records")

    known_limitations_df = pd.DataFrame(
        [
            {"limitation": "sandbox_only", "detail": "320G output is sandbox diagnostics only; no production apply is performed."},
            {"limitation": "no_ocr_or_llm", "detail": "This stage reuses existing PPStructure outputs only and does not run OCR/LLM."},
            {"limitation": "table_type_rule_conservative", "detail": "Table-type mismatch rows are conservatively routed to review-required."},
        ]
    )

    summary_payload = {
        "batch_table_count": batch_table_count,
        "batch_ok_count": batch_ok_count,
        "parsed_table_count": parsed_table_count,
        "table_with_row_text_count": table_with_row_text_count,
        "table_with_candidates_count": table_with_candidates_count,
        "table_with_trusted_count": table_with_trusted_count,
        "report_count": report_count,
        "trusted_total_count": trusted_total_count,
        "review_required_total_count": review_total_count,
        "rejected_total_count": rejected_total_count,
        "trusted_rate": trusted_rate,
        "review_required_rate": review_rate,
        "rejected_rate": rejected_rate,
        "unique_metric_count": unique_metric_count,
        "unique_year_count": unique_year_count,
        "unique_report_count": unique_report_count,
        "unit_unknown_count": unit_unknown_count,
        "year_inferred_count": year_inferred_count,
        "conflict_count": conflict_count,
        "provenance_complete_rate": provenance_complete_rate,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "batch_delivery_decision": batch_decision,
        "batch_scan_status": batch_scan_status,
        "scan_warnings": scan_warnings,
        "top_risk_tags": top_risk_tags,
    }

    dataframes = {
        "table_run_inventory": inventory_df,
        "extracted_row_texts_all": extracted_rows_df,
        "metric_candidates_all": metric_candidates_df,
        "normalized_candidates_all": normalized_df,
        "trusted_preview_all": trusted_df,
        "review_required_preview_all": review_df,
        "rejected_preview_all": rejected_df,
        "per_table_summary": per_table_df,
        "per_report_summary": per_report_df,
        "metric_coverage": metric_cov_df,
        "table_type_performance": type_perf_df,
        "risk_tag_counts": risk_counts_df,
        "provenance_coverage": provenance_cov_df,
        "qa_checks": qa_df,
        "known_limitations": known_limitations_df,
    }

    return {
        "blocked": False,
        "blocked_code": "",
        "blocked_message": "",
        "summary": summary_payload,
        "dataframes": dataframes,
    }
