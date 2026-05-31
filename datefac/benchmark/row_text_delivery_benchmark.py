from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pandas as pd


@dataclass
class DeliveryOutputRecord:
    output_type: str
    output_dir: str
    file_path: str
    detected_stage: str
    source_candidate_count: int
    trusted_count: int
    review_required_count: int
    rejected_count: int
    unique_metric_count: int
    unique_year_count: int
    qa_fail_count: int
    decision: str
    usable_for_benchmark: bool
    warnings: str

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


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


def _read_sheet_safe(path: Path, name: str) -> pd.DataFrame:
    try:
        return pd.read_excel(path, sheet_name=name)
    except Exception:
        return pd.DataFrame()


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _discover_candidate_files(delivery_root: Path) -> List[Path]:
    files: List[Path] = []
    for p in delivery_root.rglob("*.xlsx"):
        n = p.name.lower()
        if n.startswith("row_text_delivery_") or n.startswith("row_text_mapping_") or n.startswith("legacy_ppstructure_row_text_"):
            files.append(p)
    return sorted(files)


def _classify_output(path: Path) -> Tuple[str, str]:
    n = path.name.lower()
    if n.startswith("row_text_delivery_"):
        return "delivery_bundle", "320E"
    if n.startswith("row_text_mapping_"):
        return "mapping_output", "320D2"
    if n.startswith("legacy_ppstructure_row_text_"):
        return "candidate_output", "320C4"
    return "unknown", "unknown"


def _parse_summary_sheet(path: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    s = _read_sheet_safe(path, "summary")
    if s.empty:
        return out
    if "metric" in s.columns and "value" in s.columns:
        for _, r in s.iterrows():
            k = _norm(r.get("metric"))
            if k:
                out[k] = r.get("value")
    return out


def _load_benchmark_payload(path: Path) -> Dict[str, Any]:
    output_type, detected_stage = _classify_output(path)
    payload = {}
    payload.update(_parse_summary_sheet(path))
    payload.update(_load_json(path.parent / f"{path.stem}_summary.json"))

    if output_type == "delivery_bundle":
        trusted = _safe_int(payload.get("trusted_delivery_count"))
        review = _safe_int(payload.get("review_required_delivery_count"))
        rejected = _safe_int(payload.get("rejected_source_count"))
        src = _safe_int(payload.get("source_candidate_count"))
        uniq_metric = _safe_int(payload.get("unique_metric_count"))
        uniq_year = _safe_int(payload.get("unique_year_count"))
        qa_fail = _safe_int(payload.get("qa_fail_count"))
        decision = _norm(payload.get("delivery_decision"))
        usable = src > 0 and qa_fail == 0
    elif output_type == "mapping_output":
        trusted = _safe_int(payload.get("trusted_preview_count"))
        review = _safe_int(payload.get("review_required_preview_count"))
        rejected = _safe_int(payload.get("rejected_preview_count"))
        src = _safe_int(payload.get("source_candidate_count")) or _safe_int(payload.get("context_enriched_candidate_count"))
        uniq_metric = _safe_int(payload.get("unique_metric_count"))
        uniq_year = _safe_int(payload.get("unique_year_count"))
        qa_fail = _safe_int(payload.get("qa_fail_count"))
        decision = _norm(payload.get("sandbox_mapping_decision"))
        usable = src > 0 and qa_fail == 0
    else:
        trusted = _safe_int(payload.get("trusted_preview_count"))
        review = _safe_int(payload.get("review_required_preview_count"))
        rejected = _safe_int(payload.get("rejected_preview_count"))
        src = _safe_int(payload.get("source_candidate_count")) or _safe_int(payload.get("metric_candidate_count"))
        uniq_metric = _safe_int(payload.get("unique_metric_count"))
        uniq_year = _safe_int(payload.get("unique_year_count"))
        qa_fail = _safe_int(payload.get("qa_fail_count"))
        decision = _norm(payload.get("row_text_smoke_fix_decision"))
        usable = src > 0

    warnings: List[str] = []
    if src <= 0:
        warnings.append("empty_source_count")

    rec = DeliveryOutputRecord(
        output_type=output_type,
        output_dir=str(path.parent),
        file_path=str(path),
        detected_stage=detected_stage,
        source_candidate_count=src,
        trusted_count=trusted,
        review_required_count=review,
        rejected_count=rejected,
        unique_metric_count=uniq_metric,
        unique_year_count=uniq_year,
        qa_fail_count=qa_fail,
        decision=decision,
        usable_for_benchmark=bool(usable),
        warnings="|".join(warnings),
    )
    return {"record": rec, "payload": payload}


def _stage_rank(stage: str) -> int:
    s = _norm(stage).upper()
    if s == "320E":
        return 1
    if s == "320D2":
        return 2
    if s == "320C4":
        return 3
    return 9


def _ensure_str_cols(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = ""
    return out


def _extract_rows_from_delivery(path: Path, stage: str) -> pd.DataFrame:
    su = _norm(stage).upper()
    if su == "320E":
        trusted = _read_sheet_safe(path, "customer_trusted_metrics_preview")
        review = _read_sheet_safe(path, "customer_review_required_preview")
        prov = _read_sheet_safe(path, "source_provenance")
        prov_cols = [
            "provenance_id",
            "candidate_id",
            "source_stage",
            "source_file",
            "source_doc_name",
            "source_table_id",
            "source_row_index",
            "source_row_text",
            "year_source",
            "unit_source",
            "mapping_decision",
            "split_reason",
        ]
        prov = _ensure_str_cols(prov, prov_cols) if not prov.empty else pd.DataFrame(columns=prov_cols)

        rows: List[pd.DataFrame] = []
        if not trusted.empty:
            t = trusted.copy()
            t["split_decision"] = "trusted_preview"
            t = t.rename(columns={
                "value": "normalized_value",
                "provenance_id": "candidate_id",
                "table_name_or_context": "source_table_id",
            })
            rows.append(t)
        if not review.empty:
            r = review.copy()
            r["split_decision"] = "review_required_preview"
            r = r.rename(columns={
                "provenance_id": "candidate_id",
                "raw_value": "raw_value",
                "table_name_or_context": "source_table_id",
                "reason_for_review": "split_reason",
            })
            rows.append(r)
        if not rows:
            return pd.DataFrame()
        df = pd.concat(rows, ignore_index=True, sort=False)
        df = _ensure_str_cols(df, [
            "candidate_id",
            "source_file",
            "source_doc_name",
            "source_table_id",
            "source_row_text",
            "metric_code",
            "canonical_metric_name",
            "year",
            "unit",
            "risk_tags",
            "split_reason",
            "split_decision",
        ])
        if not prov.empty:
            p = prov.copy()
            p["candidate_id"] = p["provenance_id"].where(p["provenance_id"].astype(str).str.len() > 0, p["candidate_id"])
            p = p.drop_duplicates(subset=["candidate_id"], keep="first")
            keep = [
                "candidate_id",
                "source_stage",
                "source_file",
                "source_doc_name",
                "source_table_id",
                "source_row_index",
                "source_row_text",
                "year_source",
                "unit_source",
                "split_reason",
            ]
            df = df.drop(columns=[c for c in ["source_stage", "year_source", "unit_source"] if c in df.columns], errors="ignore")
            df = df.merge(p[keep], on="candidate_id", how="left", suffixes=("", "_prov"))
        if "source_stage" not in df.columns:
            df["source_stage"] = "mineru_ppstructure_row_text_320c4"
        return df

    if su == "320D2":
        parts: List[pd.DataFrame] = []
        for sname, split in [
            ("trusted_preview", "trusted_preview"),
            ("review_required_preview", "review_required_preview"),
            ("rejected_preview", "rejected_preview"),
        ]:
            s = _read_sheet_safe(path, sname)
            if not s.empty:
                d = s.copy()
                d["split_decision"] = split
                parts.append(d)
        if parts:
            return pd.concat(parts, ignore_index=True, sort=False)
        c = _read_sheet_safe(path, "context_enriched_candidates")
        if not c.empty:
            c = c.copy()
            c["split_decision"] = "context_only"
            return c
        return pd.DataFrame()

    if su == "320C4":
        c = _read_sheet_safe(path, "metric_candidate_preview")
        if c.empty:
            return pd.DataFrame()
        c = c.copy()
        c["split_decision"] = "candidates_only"
        return c

    return pd.DataFrame()


def _build_dedupe_key(row: Dict[str, Any]) -> str:
    # Prefer semantic/source identity over stage-local ids to avoid double-counting
    # the same candidate across 320C4/320D2/320E.
    parts = [
        _norm(row.get("source_file")),
        _norm(row.get("source_row_text") or row.get("row_text")),
        _norm(row.get("metric_code")),
        _norm(row.get("year")),
    ]
    return "|".join(parts)


def _metric_family(metric_code: str) -> str:
    m = _norm(metric_code).lower()
    if m in {"roe", "eps", "net_profit", "attributable_net_profit"}:
        return "profitability"
    if m in {"pe", "pb", "ev_ebitda"}:
        return "valuation"
    if m in {"total_assets", "total_liabilities", "equity", "book_value_per_share"}:
        return "balance_sheet"
    if m in {"operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "net_cash_change", "free_cash_flow"}:
        return "cash_flow"
    if "growth" in m:
        return "growth"
    if "margin" in m:
        return "margin"
    return "other"


def benchmark_delivery_outputs(delivery_root: Path) -> Dict[str, Any]:
    files = _discover_candidate_files(delivery_root)
    loaded = [_load_benchmark_payload(f) for f in files]

    available_df = pd.DataFrame([x["record"].to_dict() for x in loaded])
    if available_df.empty:
        available_df = pd.DataFrame(columns=[
            "output_type",
            "output_dir",
            "file_path",
            "detected_stage",
            "source_candidate_count",
            "trusted_count",
            "review_required_count",
            "rejected_count",
            "unique_metric_count",
            "unique_year_count",
            "qa_fail_count",
            "decision",
            "usable_for_benchmark",
            "warnings",
        ])

    all_rows: List[Dict[str, Any]] = []
    for item in loaded:
        rec: DeliveryOutputRecord = item["record"]
        raw = _extract_rows_from_delivery(Path(rec.file_path), rec.detected_stage)
        if raw.empty:
            continue

        raw = _ensure_str_cols(raw, [
            "candidate_id",
            "source_stage",
            "source_file",
            "source_doc_name",
            "source_table_id",
            "source_row_index",
            "source_row_text",
            "metric_code",
            "canonical_metric_name",
            "year",
            "raw_value",
            "normalized_value",
            "unit",
            "year_source",
            "unit_source",
            "risk_tags",
            "split_reason",
            "split_decision",
        ])

        for _, rr in raw.iterrows():
            row = rr.to_dict()
            source_file = _norm(row.get("source_file"))
            report_name = _norm(row.get("source_doc_name")) or (Path(source_file).stem if source_file else "")
            table_id = _norm(row.get("source_table_id")) or _norm(row.get("table_name_or_context")) or _norm(row.get("extracted_table_id"))
            candidate_id = _norm(row.get("candidate_id")) or _norm(row.get("provenance_id"))
            split = _norm(row.get("split_decision")) or "candidates_only"
            stage = _norm(rec.detected_stage)

            all_rows.append({
                "sample_id": f"{report_name}|{table_id}|{_norm(row.get('metric_code'))}|{_norm(row.get('year'))}",
                "candidate_id": candidate_id,
                "provenance_id": _norm(row.get("provenance_id")) or candidate_id,
                "source_stage": _norm(row.get("source_stage")) or stage,
                "source_stage_bucket": stage,
                "source_report_name": report_name,
                "source_file": source_file,
                "source_table_id": table_id,
                "table_context": _norm(row.get("table_context")) or _norm(row.get("table_name_or_context")),
                "source_row_index": _norm(row.get("source_row_index")),
                "source_row_text": _norm(row.get("source_row_text")) or _norm(row.get("row_text")),
                "metric_code": _norm(row.get("metric_code")),
                "canonical_metric_name": _norm(row.get("canonical_metric_name")),
                "year": _norm(row.get("year")),
                "raw_value": _norm(row.get("raw_value")),
                "normalized_value": _norm(row.get("normalized_value")) or _norm(row.get("value")),
                "unit": _norm(row.get("unit")),
                "unit_source": _norm(row.get("unit_source")),
                "year_source": _norm(row.get("year_source")),
                "risk_tags": _norm(row.get("risk_tags")),
                "split_reason": _norm(row.get("split_reason")),
                "split_decision": split,
                "available_delivery_bundle": rec.file_path if stage == "320E" else "",
                "has_qa": rec.qa_fail_count == 0,
                "stage_rank": _stage_rank(stage),
                "dedupe_key": _build_dedupe_key(row),
            })

    sample_df = pd.DataFrame(all_rows)
    if sample_df.empty:
        sample_df = pd.DataFrame(columns=[
            "sample_id",
            "candidate_id",
            "provenance_id",
            "source_stage",
            "source_stage_bucket",
            "source_report_name",
            "source_file",
            "source_table_id",
            "table_context",
            "source_row_index",
            "source_row_text",
            "metric_code",
            "canonical_metric_name",
            "year",
            "raw_value",
            "normalized_value",
            "unit",
            "unit_source",
            "year_source",
            "risk_tags",
            "split_reason",
            "split_decision",
            "available_delivery_bundle",
            "has_qa",
            "stage_rank",
            "dedupe_key",
        ])

    if not sample_df.empty:
        sample_df["stage_rank"] = sample_df["stage_rank"].astype(int)

        # Stage preference rule for 320F:
        # 1) 320E delivery bundle
        # 2) 320D2 mapping output
        # 3) 320C4 candidate output
        # For each source_file, keep only rows from the highest available stage.
        stage_floor_df = (
            sample_df.groupby("source_file", dropna=False)["stage_rank"]
            .min()
            .reset_index(name="preferred_stage_rank")
        )
        sample_df = sample_df.merge(stage_floor_df, on="source_file", how="left")
        sample_df = sample_df[sample_df["stage_rank"] == sample_df["preferred_stage_rank"]].copy()
        sample_df = sample_df.drop(columns=["preferred_stage_rank"], errors="ignore")

        # Defensive dedupe within selected stage rows.
        sample_df = (
            sample_df.sort_values(["dedupe_key", "stage_rank"])
            .drop_duplicates(subset=["dedupe_key"], keep="first")
            .reset_index(drop=True)
        )

    # Sample inventory (one row per report + table + stage)
    inv_rows: List[Dict[str, Any]] = []
    if not sample_df.empty:
        gcols = ["source_report_name", "source_table_id", "source_stage_bucket"]
        grouped = sample_df.groupby(gcols, dropna=False)
        for (report_name, table_id, stage_bucket), g in grouped:
            s = g["split_decision"].astype(str)
            sample_status = "MAPPING_ONLY_AVAILABLE"
            if _norm(stage_bucket).upper() == "320E":
                sample_status = "BENCHMARKED_DELIVERY"
            elif _norm(stage_bucket).upper() == "320C4":
                sample_status = "CANDIDATES_ONLY_AVAILABLE"

            inv_rows.append({
                "sample_id": f"{_norm(report_name)}|{_norm(table_id)}|{_norm(stage_bucket)}",
                "source_report_name": _norm(report_name),
                "source_file": _norm(g["source_file"].iloc[0]) if len(g) else "",
                "source_table_id": _norm(table_id),
                "table_context": _norm(g["table_context"].iloc[0]) if len(g) else "",
                "source_stage": _norm(stage_bucket),
                "available_delivery_bundle": _norm(g["available_delivery_bundle"].iloc[0]) if len(g) else "",
                "candidate_count": int(len(g)),
                "trusted_count": int((s == "trusted_preview").sum()),
                "review_required_count": int((s == "review_required_preview").sum()),
                "rejected_count": int((s == "rejected_preview").sum()),
                "unique_metric_count": int(g["metric_code"].replace("", pd.NA).dropna().nunique()),
                "unique_year_count": int(g["year"].replace("", pd.NA).dropna().nunique()),
                "has_provenance": bool(g["provenance_id"].astype(str).str.len().gt(0).any()),
                "has_qa": bool(g["has_qa"].all()),
                "sample_status": sample_status,
            })

    inventory_df = pd.DataFrame(inv_rows)
    if inventory_df.empty:
        inventory_df = pd.DataFrame(columns=[
            "sample_id",
            "source_report_name",
            "source_file",
            "source_table_id",
            "table_context",
            "source_stage",
            "available_delivery_bundle",
            "candidate_count",
            "trusted_count",
            "review_required_count",
            "rejected_count",
            "unique_metric_count",
            "unique_year_count",
            "has_provenance",
            "has_qa",
            "sample_status",
        ])

    # delivery table-level aggregated
    delivery_table_df = pd.DataFrame(columns=[
        "source_report_name",
        "source_table_id",
        "candidate_count",
        "trusted_count",
        "review_required_count",
        "rejected_count",
        "key_metric_hit_count",
        "has_320c4_candidates",
        "has_320d2_mapping",
        "has_320e_delivery",
    ])
    if not sample_df.empty:
        x = sample_df.copy()
        x["has_320c4_candidates"] = x["source_stage_bucket"].astype(str).str.upper().eq("320C4")
        x["has_320d2_mapping"] = x["source_stage_bucket"].astype(str).str.upper().eq("320D2")
        x["has_320e_delivery"] = x["source_stage_bucket"].astype(str).str.upper().eq("320E")
        s = x["split_decision"].astype(str)
        x["trusted_count_row"] = (s == "trusted_preview").astype(int)
        x["review_required_count_row"] = (s == "review_required_preview").astype(int)
        x["rejected_count_row"] = (s == "rejected_preview").astype(int)

        delivery_table_df = x.groupby(["source_report_name", "source_table_id"], dropna=False).agg(
            candidate_count=("candidate_id", "count"),
            trusted_count=("trusted_count_row", "sum"),
            review_required_count=("review_required_count_row", "sum"),
            rejected_count=("rejected_count_row", "sum"),
            key_metric_hit_count=("metric_code", lambda a: int(pd.Series(a).replace("", pd.NA).dropna().nunique())),
            has_320c4_candidates=("has_320c4_candidates", "max"),
            has_320d2_mapping=("has_320d2_mapping", "max"),
            has_320e_delivery=("has_320e_delivery", "max"),
        ).reset_index()

    # metric coverage
    metric_families = ["profitability", "valuation", "balance_sheet", "cash_flow", "growth", "margin", "other"]
    metric_cov_rows: List[Dict[str, Any]] = []
    if not sample_df.empty:
        t = sample_df.copy()
        t["metric_family"] = t["metric_code"].apply(_metric_family)
        s = t["split_decision"].astype(str)
        t["trusted_count_row"] = (s == "trusted_preview").astype(int)
        t["review_required_count_row"] = (s == "review_required_preview").astype(int)
        for fam in metric_families:
            g = t[t["metric_family"] == fam]
            metric_cov_rows.append({
                "metric_family": fam,
                "candidate_count": int(len(g)),
                "trusted_count": int(g["trusted_count_row"].sum()) if len(g) else 0,
                "review_required_count": int(g["review_required_count_row"].sum()) if len(g) else 0,
                "unique_metric_count": int(g["metric_code"].replace("", pd.NA).dropna().nunique()) if len(g) else 0,
                "unique_report_count": int(g["source_report_name"].replace("", pd.NA).dropna().nunique()) if len(g) else 0,
                "coverage_notes": "",
            })
    else:
        for fam in metric_families:
            metric_cov_rows.append({
                "metric_family": fam,
                "candidate_count": 0,
                "trusted_count": 0,
                "review_required_count": 0,
                "unique_metric_count": 0,
                "unique_report_count": 0,
                "coverage_notes": "",
            })
    metric_cov_df = pd.DataFrame(metric_cov_rows)

    total_candidates = int(len(sample_df))
    trusted_total_count = int((sample_df["split_decision"] == "trusted_preview").sum()) if total_candidates else 0
    review_total_count = int((sample_df["split_decision"] == "review_required_preview").sum()) if total_candidates else 0
    rejected_total_count = int((sample_df["split_decision"] == "rejected_preview").sum()) if total_candidates else 0

    trusted_rate = float(trusted_total_count / total_candidates) if total_candidates else 0.0
    review_rate = float(review_total_count / total_candidates) if total_candidates else 0.0
    rejected_rate = float(rejected_total_count / total_candidates) if total_candidates else 0.0

    # top risk tags
    tag_counts: Dict[str, int] = {}
    for tags in sample_df.get("risk_tags", pd.Series(dtype=str)).astype(str).tolist():
        for t in [x.strip() for x in tags.split("|") if x.strip()]:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    top_risk_tags = "|".join([k for k, _ in sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))[:5]])

    trust_split_df = pd.DataFrame([{
        "total_candidates": total_candidates,
        "trusted_count": trusted_total_count,
        "review_required_count": review_total_count,
        "rejected_count": rejected_total_count,
        "trusted_rate": trusted_rate,
        "review_required_rate": review_rate,
        "rejected_rate": rejected_rate,
        "top_review_reasons": "review_required_preview" if review_total_count > 0 else "",
        "top_risk_tags": top_risk_tags,
    }])

    # unit/year context summary
    risk_series = sample_df.get("risk_tags", pd.Series(dtype=str)).astype(str)
    year_src = sample_df.get("year_source", pd.Series(dtype=str)).astype(str)
    unit_src = sample_df.get("unit_source", pd.Series(dtype=str)).astype(str)
    year_col = sample_df.get("year", pd.Series(dtype=str)).astype(str)

    unit_unknown_count = int(risk_series.str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True).sum()) if total_candidates else 0
    year_inferred_count = int((year_src == "INFERRED_SEQUENCE").sum()) if total_candidates else 0
    table_header_year_count = int((year_src == "TABLE_HEADER").sum()) if total_candidates else 0
    smoke_context_year_count = int((year_src == "SMOKE_CHECK_CONTEXT").sum()) if total_candidates else 0
    invalid_year_count = int((~year_col.str.match(r"^20\d{2}(?:[AE])?$", na=False)).sum()) if total_candidates else 0

    unit_year_context_df = pd.DataFrame([{
        "unit_unknown_count": unit_unknown_count,
        "year_inferred_count": year_inferred_count,
        "table_header_year_count": table_header_year_count,
        "smoke_context_year_count": smoke_context_year_count,
        "invalid_year_count": invalid_year_count,
        "unit_context_sources": "|".join(sorted(set([x for x in unit_src.tolist() if _norm(x)]))),
        "year_context_sources": "|".join(sorted(set([x for x in year_src.tolist() if _norm(x)]))),
    }])

    # provenance coverage per candidate row
    prov_rows: List[Dict[str, Any]] = []
    for _, r in sample_df.iterrows():
        has_source_file = bool(_norm(r.get("source_file")))
        has_source_row_text = bool(_norm(r.get("source_row_text")))
        has_source_table_id = bool(_norm(r.get("source_table_id")))
        has_source_stage = bool(_norm(r.get("source_stage")))
        has_year_source = bool(_norm(r.get("year_source")))
        has_unit_source = bool(_norm(r.get("unit_source")))
        missing = []
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
        prov_rows.append({
            "sample_id": _norm(r.get("sample_id")),
            "candidate_id": _norm(r.get("candidate_id")),
            "provenance_id": _norm(r.get("provenance_id")),
            "has_source_file": has_source_file,
            "has_source_row_text": has_source_row_text,
            "has_source_table_id": has_source_table_id,
            "has_source_stage": has_source_stage,
            "has_year_source": has_year_source,
            "has_unit_source": has_unit_source,
            "provenance_complete": len(missing) == 0,
            "missing_fields": "|".join(missing),
            "source_report_name": _norm(r.get("source_report_name")),
        })
    provenance_df = pd.DataFrame(prov_rows)
    if provenance_df.empty:
        provenance_df = pd.DataFrame(columns=[
            "sample_id",
            "candidate_id",
            "provenance_id",
            "has_source_file",
            "has_source_row_text",
            "has_source_table_id",
            "has_source_stage",
            "has_year_source",
            "has_unit_source",
            "provenance_complete",
            "missing_fields",
            "source_report_name",
        ])

    qa_fail_count = int((available_df["qa_fail_count"] > 0).sum()) if not available_df.empty else 0
    qa_summary_df = pd.DataFrame([{
        "qa_fail_count": qa_fail_count,
        "qa_warn_count": 0,
        "qa_pass_count": int((available_df["qa_fail_count"] == 0).sum()) if not available_df.empty else 0,
    }])

    known_limitations_df = pd.DataFrame([
        {"limitation": "manual_recognizer_dependency", "detail": "PPStructure row-text outputs rely on manual offline runs and are not auto-produced by this benchmark."},
        {"limitation": "sandbox_only", "detail": "This benchmark is diagnostics-only and must not be interpreted as production apply readiness."},
        {"limitation": "partial_report_coverage", "detail": "If recognizer outputs cover only a subset of MinerU reports/tables, generalization remains unproven."},
    ])

    recognized_report_table_keys: Set[Tuple[str, str]] = set()
    recognized_report_names: Set[str] = set()
    recognized_source_table_ids: Set[str] = set()
    if not inventory_df.empty:
        for _, r in inventory_df.iterrows():
            rn = _norm(r.get("source_report_name"))
            st = _norm(r.get("source_table_id"))
            if rn:
                recognized_report_names.add(rn)
            if st:
                recognized_source_table_ids.add(st)
            if rn and st:
                recognized_report_table_keys.add((rn, st))

    report_level_seed_df = pd.DataFrame()
    if not sample_df.empty:
        s = sample_df.copy()
        dec = s["split_decision"].astype(str)
        s["trusted_count_row"] = (dec == "trusted_preview").astype(int)
        s["review_required_count_row"] = (dec == "review_required_preview").astype(int)
        s["rejected_count_row"] = (dec == "rejected_preview").astype(int)
        s["metric_family"] = s["metric_code"].apply(_metric_family)

        report_level_seed_df = s.groupby("source_report_name", dropna=False).agg(
            recognized_table_count=("source_table_id", lambda a: int(pd.Series(a).replace("", pd.NA).dropna().nunique())),
            delivery_sample_count=("candidate_id", "count"),
            trusted_count=("trusted_count_row", "sum"),
            review_required_count=("review_required_count_row", "sum"),
            rejected_count=("rejected_count_row", "sum"),
            unique_metric_count=("metric_code", lambda a: int(pd.Series(a).replace("", pd.NA).dropna().nunique())),
            metric_family_coverage=("metric_family", lambda a: int(pd.Series(a).replace("", pd.NA).dropna().nunique())),
        ).reset_index().rename(columns={"source_report_name": "report_name"})

    return {
        "available_delivery_outputs_df": available_df,
        "benchmark_sample_inventory_df": inventory_df,
        "delivery_table_seed_df": delivery_table_df,
        "report_level_seed_df": report_level_seed_df,
        "metric_coverage_df": metric_cov_df,
        "trust_split_summary_df": trust_split_df,
        "unit_year_context_summary_df": unit_year_context_df,
        "provenance_coverage_df": provenance_df,
        "qa_summary_df": qa_summary_df,
        "known_limitations_df": known_limitations_df,
        "all_samples_df": sample_df,
        "recognized_report_table_keys": recognized_report_table_keys,
        "recognized_report_names": recognized_report_names,
        "recognized_source_table_ids": recognized_source_table_ids,
        "discovered_delivery_bundle_count": int((available_df["output_type"] == "delivery_bundle").sum()) if not available_df.empty else 0,
        "benchmarked_report_count": int(report_level_seed_df["report_name"].replace("", pd.NA).dropna().nunique()) if not report_level_seed_df.empty else 0,
        "benchmarked_table_count": int(delivery_table_df[["source_report_name", "source_table_id"]].drop_duplicates().shape[0]) if not delivery_table_df.empty else 0,
        "trusted_total_count": trusted_total_count,
        "review_required_total_count": review_total_count,
        "rejected_total_count": rejected_total_count,
        "trusted_rate": trusted_rate,
        "qa_fail_count": qa_fail_count,
        "provenance_complete_rate": float(provenance_df["provenance_complete"].mean()) if not provenance_df.empty else 0.0,
    }
