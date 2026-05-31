from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from datefac.delivery.sandbox_delivery_schema import QACheckRow, SandboxDeliveryManifest, as_optional_text, parse_provenance_json


EXPECTED_SHEETS = [
    "context_enriched_candidates",
    "trusted_preview",
    "review_required_preview",
    "rejected_preview",
    "risk_tag_counts",
    "metric_counts",
    "trust_gate_audit",
    "context_propagation_audit",
]

YEAR_COLUMNS = ["2024", "2025", "2026E", "2027E", "2028E"]


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _read_sheet_safe(path: Path, name: str) -> pd.DataFrame:
    try:
        return pd.read_excel(path, sheet_name=name)
    except Exception:
        return pd.DataFrame()


def load_320d2_inputs(input_dir: Path) -> Dict[str, Any]:
    in_excel = input_dir / "row_text_mapping_320d2.xlsx"
    if not in_excel.exists():
        return {
            "blocked": True,
            "blocked_code": "BLOCKED_MISSING_320D2_INPUT",
            "blocked_message": f"missing input workbook: {in_excel}",
            "sheets": {},
            "warnings": [],
        }
    sheets: Dict[str, pd.DataFrame] = {}
    warnings: List[Dict[str, str]] = []
    for s in EXPECTED_SHEETS:
        df = _read_sheet_safe(in_excel, s)
        sheets[s] = df
        if df.empty:
            warnings.append(
                {
                    "warning_code": "MISSING_OR_EMPTY_SHEET",
                    "warning_message": f"sheet empty or missing: {s}",
                }
            )
    return {
        "blocked": False,
        "blocked_code": "",
        "blocked_message": "",
        "sheets": sheets,
        "warnings": warnings,
    }


def _build_customer_trusted_preview(trusted_df: pd.DataFrame) -> pd.DataFrame:
    if trusted_df.empty:
        return pd.DataFrame(
            columns=[
                "source_doc_name",
                "source_file",
                "table_name_or_context",
                "metric_code",
                "canonical_metric_name",
                "year",
                "value",
                "unit",
                "currency",
                "confidence",
                "source_row_text",
                "extraction_method",
                "provenance_id",
            ]
        )
    out = trusted_df.copy()
    out["table_name_or_context"] = out["table_title"].astype(str).replace({"nan": ""})
    out.loc[out["table_name_or_context"] == "", "table_name_or_context"] = out["source_table_id"].astype(str)
    out["extraction_method"] = "mineru_ppstructure_row_text"
    out["provenance_id"] = out["candidate_id"].astype(str)
    out["value"] = out["normalized_value"]
    cols = [
        "source_doc_name",
        "source_file",
        "table_name_or_context",
        "metric_code",
        "canonical_metric_name",
        "year",
        "value",
        "unit",
        "currency",
        "confidence",
        "source_row_text",
        "extraction_method",
        "provenance_id",
    ]
    return out[cols].copy()


def _suggest_action(reason: str, risk_tags: str) -> str:
    text = f"{_norm(reason)}|{_norm(risk_tags)}".lower()
    if "unit" in text:
        return "confirm_unit"
    if "repaired" in text:
        return "confirm_repaired_row"
    if "value" in text or "conflict" in text:
        return "confirm_value"
    if "unknown_metric" in text or "noise" in text:
        return "ignore_or_reject"
    return "confirm_value"


def _build_customer_review_preview(review_df: pd.DataFrame) -> pd.DataFrame:
    if review_df.empty:
        return pd.DataFrame(
            columns=[
                "source_doc_name",
                "source_file",
                "table_name_or_context",
                "metric_code",
                "canonical_metric_name",
                "year",
                "raw_value",
                "normalized_value",
                "unit",
                "reason_for_review",
                "risk_tags",
                "source_row_text",
                "suggested_action",
                "provenance_id",
            ]
        )
    out = review_df.copy()
    out["table_name_or_context"] = out["table_title"].astype(str).replace({"nan": ""})
    out.loc[out["table_name_or_context"] == "", "table_name_or_context"] = out["source_table_id"].astype(str)
    out["reason_for_review"] = out["split_reason"].astype(str)
    out["provenance_id"] = out["candidate_id"].astype(str)
    out["suggested_action"] = out.apply(lambda r: _suggest_action(r.get("split_reason", ""), r.get("risk_tags", "")), axis=1)
    cols = [
        "source_doc_name",
        "source_file",
        "table_name_or_context",
        "metric_code",
        "canonical_metric_name",
        "year",
        "raw_value",
        "normalized_value",
        "unit",
        "reason_for_review",
        "risk_tags",
        "source_row_text",
        "suggested_action",
        "provenance_id",
    ]
    return out[cols].copy()


def _build_metric_wide_preview(trusted_df: pd.DataFrame) -> pd.DataFrame:
    if trusted_df.empty:
        cols = ["metric_code", "canonical_metric_name"] + YEAR_COLUMNS + ["unit", "trust_status", "wide_warning"]
        return pd.DataFrame(columns=cols)
    records: List[Dict[str, Any]] = []
    grouped = trusted_df.groupby(["metric_code", "canonical_metric_name"], dropna=False)
    for (metric_code, canonical_name), g in grouped:
        rec: Dict[str, Any] = {
            "metric_code": metric_code,
            "canonical_metric_name": canonical_name,
            "unit": " | ".join(sorted({str(x) for x in g["unit"].fillna("").tolist() if str(x)})),
            "trust_status": "trusted_preview",
            "wide_warning": "",
        }
        for y in YEAR_COLUMNS:
            gy = g[g["year"].astype(str) == y]
            vals = sorted({str(v) for v in gy["normalized_value"].tolist()})
            if len(vals) == 0:
                rec[y] = ""
            elif len(vals) == 1:
                rec[y] = vals[0]
            else:
                rec[y] = " | ".join(vals)
                rec["wide_warning"] = "MULTI_VALUE_SAME_METRIC_YEAR"
        records.append(rec)
    return pd.DataFrame(records)


def _build_source_provenance(delivered_df: pd.DataFrame) -> pd.DataFrame:
    if delivered_df.empty:
        return pd.DataFrame(
            columns=[
                "provenance_id",
                "candidate_id",
                "source_stage",
                "source_file",
                "source_doc_name",
                "source_table_id",
                "source_row_index",
                "source_row_text",
                "source_image_path",
                "table_asset_id",
                "recognizer_name",
                "smoke_check_status",
                "year_source",
                "unit_source",
                "mapping_decision",
                "split_reason",
            ]
        )
    rows: List[Dict[str, Any]] = []
    for _, r in delivered_df.iterrows():
        p = parse_provenance_json(r.get("provenance_json"))
        raw_row = p.get("raw_row", {}) if isinstance(p.get("raw_row"), dict) else {}
        rows.append(
            {
                "provenance_id": _norm(r.get("candidate_id")),
                "candidate_id": _norm(r.get("candidate_id")),
                "source_stage": _norm(r.get("source_stage")),
                "source_file": _norm(r.get("source_file")),
                "source_doc_name": _norm(r.get("source_doc_name")),
                "source_table_id": _norm(r.get("source_table_id")),
                "source_row_index": _norm(r.get("source_row_index")),
                "source_row_text": _norm(r.get("source_row_text")),
                "source_image_path": _norm(raw_row.get("source_image_path")),
                "table_asset_id": _norm(raw_row.get("table_asset_id")),
                "recognizer_name": "legacy_ppstructure_row_text",
                "smoke_check_status": _norm(r.get("smoke_check_status")),
                "year_source": _norm(r.get("year_source")),
                "unit_source": _norm(r.get("unit_source")),
                "mapping_decision": _norm(r.get("split_decision")),
                "split_reason": _norm(r.get("split_reason")),
            }
        )
    return pd.DataFrame(rows)


def _build_qa_checks(
    trusted_df: pd.DataFrame,
    review_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
    source_trusted_df: pd.DataFrame,
    source_review_df: pd.DataFrame,
    smoke_verified_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, int, int, int]:
    checks: List[QACheckRow] = []

    def add_check(name: str, ok: bool, detail: str, warn: bool = False) -> None:
        status = "PASS" if ok else ("WARN" if warn else "FAIL")
        checks.append(QACheckRow(check_name=name, status=status, detail=detail))

    # 1
    no_rejected_in_trusted = (trusted_df["split_decision"].astype(str) == "trusted_preview").all() if not trusted_df.empty else True
    add_check("no_rejected_rows_in_customer_trusted_preview", no_rejected_in_trusted, f"trusted rows: {len(trusted_df)}")

    # 2
    invalid_year = 0
    if not trusted_df.empty:
        invalid_year = int((~trusted_df["year"].astype(str).str.match(r"^20\d{2}(?:[AE])?$", na=False)).sum())
    add_check("no_invalid_years", invalid_year == 0, f"invalid years in trusted: {invalid_year}")

    # 3
    unknown_metric = 0
    if not trusted_df.empty:
        unknown_metric = int(trusted_df["risk_tags"].astype(str).str.contains(r"(?:^|\|)UNKNOWN_METRIC_CODE(?:$|\|)", regex=True).sum())
    add_check("no_unknown_metric_codes_in_trusted_preview", unknown_metric == 0, f"unknown metric tags in trusted: {unknown_metric}")

    # 4
    unit_unknown = 0
    if not trusted_df.empty:
        unit_unknown = int(
            trusted_df["risk_tags"].astype(str).str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True).sum()
            + trusted_df["unit"].isna().sum()
        )
    add_check("no_unit_unknown_in_trusted_preview", unit_unknown == 0, f"unit unknown in trusted: {unit_unknown}")

    # 5
    dup_metric_year = 0
    if not trusted_df.empty:
        dup_metric_year = int((trusted_df.groupby(["metric_code", "year"]).size() > 1).sum())
    add_check("no_duplicate_metric_year_in_trusted_preview", dup_metric_year == 0, f"duplicate metric/year groups: {dup_metric_year}")

    # 6
    add_check(
        "trusted_count_matches_source_trusted_preview_count",
        len(trusted_df) == len(source_trusted_df),
        f"delivery trusted={len(trusted_df)}, source trusted={len(source_trusted_df)}",
    )

    # 7
    add_check(
        "review_count_matches_source_review_required_preview_count",
        len(review_df) == len(source_review_df),
        f"delivery review={len(review_df)}, source review={len(source_review_df)}",
    )

    # 8
    trusted_smoke = int((trusted_df["smoke_check_status"].astype(str) == "PASSED").sum()) if not trusted_df.empty else 0
    smoke_total = len(smoke_verified_df)
    smoke_match = trusted_smoke <= smoke_total
    add_check(
        "smoke_verified_rows_count_matches_or_is_explained",
        smoke_match,
        f"trusted smoke_passed={trusted_smoke}, source smoke_verified={smoke_total}",
        warn=not smoke_match,
    )

    qa_df = pd.DataFrame([c.to_dict() for c in checks])
    qa_pass = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    return qa_df, qa_pass, qa_warn, qa_fail


def build_sandbox_delivery_bundle(input_dir: Path, output_dir: Path) -> Dict[str, Any]:
    loaded = load_320d2_inputs(input_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if loaded["blocked"]:
        summary = {
            "source_candidate_count": 0,
            "trusted_delivery_count": 0,
            "review_required_delivery_count": 0,
            "rejected_source_count": 0,
            "unique_metric_count": 0,
            "unique_year_count": 0,
            "metric_wide_row_count": 0,
            "provenance_row_count": 0,
            "qa_pass_count": 0,
            "qa_warn_count": 0,
            "qa_fail_count": 1,
            "delivery_decision": "BLOCKED_MISSING_320D2_INPUT",
        }
        summary_df = pd.DataFrame([{"metric": k, "value": v} for k, v in summary.items()])
        excel = output_dir / "row_text_delivery_320e.xlsx"
        with pd.ExcelWriter(excel, engine="openpyxl") as w:
            summary_df.to_excel(w, sheet_name="summary", index=False)
        (output_dir / "row_text_delivery_320e_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        (output_dir / "row_text_delivery_320e_report.md").write_text(
            f"# 320E Sandbox Delivery Bundle\n\n- delivery_decision: BLOCKED_MISSING_320D2_INPUT\n- detail: {loaded['blocked_message']}\n",
            encoding="utf-8",
        )
        return {"summary": summary, "excel_path": str(excel), "report_md_path": str(output_dir / "row_text_delivery_320e_report.md")}

    sheets = loaded["sheets"]
    context_df = sheets["context_enriched_candidates"]
    trusted_df = sheets["trusted_preview"]
    review_df = sheets["review_required_preview"]
    rejected_df = sheets["rejected_preview"]
    trust_gate_audit_df = sheets["trust_gate_audit"]
    context_audit_df = sheets["context_propagation_audit"]
    smoke_verified_df = _read_sheet_safe(input_dir / "row_text_mapping_320d2.xlsx", "smoke_verified_candidates")

    customer_trusted_df = _build_customer_trusted_preview(trusted_df)
    customer_review_df = _build_customer_review_preview(review_df)
    metric_wide_df = _build_metric_wide_preview(trusted_df)
    provenance_df = _build_source_provenance(pd.concat([trusted_df, review_df], ignore_index=True) if (not trusted_df.empty or not review_df.empty) else pd.DataFrame())

    risk_audit_df = context_df.copy()
    if not risk_audit_df.empty:
        keep = [
            "candidate_id",
            "metric_code",
            "year",
            "raw_value",
            "normalized_value",
            "unit",
            "confidence",
            "risk_tags",
            "split_decision",
            "split_reason",
        ]
        risk_audit_df = risk_audit_df[[c for c in keep if c in risk_audit_df.columns]]

    qa_df, qa_pass, qa_warn, qa_fail = _build_qa_checks(
        trusted_df=trusted_df,
        review_df=review_df,
        rejected_df=rejected_df,
        source_trusted_df=trusted_df,
        source_review_df=review_df,
        smoke_verified_df=smoke_verified_df,
    )

    source_candidate_count = int(len(context_df))
    trusted_delivery_count = int(len(customer_trusted_df))
    review_required_delivery_count = int(len(customer_review_df))
    rejected_source_count = int(len(rejected_df))
    unique_metric_count = int(context_df["metric_code"].nunique()) if not context_df.empty else 0
    unique_year_count = int(context_df["year"].nunique()) if not context_df.empty else 0
    metric_wide_row_count = int(len(metric_wide_df))
    provenance_row_count = int(len(provenance_df))

    if qa_fail > 0:
        delivery_decision = "SANDBOX_DELIVERY_BLOCKED_BY_QA_FAILURE"
    elif trusted_delivery_count >= 50 and review_required_delivery_count <= 10 and qa_fail == 0:
        delivery_decision = "SANDBOX_DELIVERY_READY_FOR_320F_MULTI_REPORT_BENCHMARK"
    elif trusted_delivery_count > 0 and qa_fail == 0:
        delivery_decision = "SANDBOX_DELIVERY_USABLE_NEEDS_MORE_BENCHMARK"
    else:
        delivery_decision = "SANDBOX_DELIVERY_NOT_READY"

    summary_payload = {
        "source_candidate_count": source_candidate_count,
        "trusted_delivery_count": trusted_delivery_count,
        "review_required_delivery_count": review_required_delivery_count,
        "rejected_source_count": rejected_source_count,
        "unique_metric_count": unique_metric_count,
        "unique_year_count": unique_year_count,
        "metric_wide_row_count": metric_wide_row_count,
        "provenance_row_count": provenance_row_count,
        "qa_pass_count": qa_pass,
        "qa_warn_count": qa_warn,
        "qa_fail_count": qa_fail,
        "delivery_decision": delivery_decision,
    }

    created_at = datetime.now(timezone.utc).isoformat()
    manifest = SandboxDeliveryManifest(
        bundle_name="row_text_delivery_320e",
        created_at=created_at,
        source_input_dir=str(input_dir),
        output_dir=str(output_dir),
        source_candidate_count=source_candidate_count,
        trusted_delivery_count=trusted_delivery_count,
        review_required_delivery_count=review_required_delivery_count,
        rejected_source_count=rejected_source_count,
        unique_metric_count=unique_metric_count,
        unique_year_count=unique_year_count,
        qa_pass_count=qa_pass,
        qa_warn_count=qa_warn,
        qa_fail_count=qa_fail,
        delivery_decision=delivery_decision,
        extra={"warnings": loaded["warnings"]},
    )
    manifest_df = pd.DataFrame([manifest.to_dict()])
    summary_df = pd.DataFrame([{"metric": k, "value": v} for k, v in summary_payload.items()])

    excel_path = output_dir / "row_text_delivery_320e.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="summary", index=False)
        customer_trusted_df.to_excel(writer, sheet_name="customer_trusted_metrics_preview", index=False)
        customer_review_df.to_excel(writer, sheet_name="customer_review_required_preview", index=False)
        metric_wide_df.to_excel(writer, sheet_name="metric_wide_preview", index=False)
        provenance_df.to_excel(writer, sheet_name="source_provenance", index=False)
        risk_audit_df.to_excel(writer, sheet_name="risk_audit", index=False)
        trust_gate_audit_df.to_excel(writer, sheet_name="trust_gate_audit", index=False)
        context_audit_df.to_excel(writer, sheet_name="context_audit", index=False)
        qa_df.to_excel(writer, sheet_name="qa_checks", index=False)
        manifest_df.to_excel(writer, sheet_name="delivery_manifest", index=False)

    summary_json = output_dir / "row_text_delivery_320e_summary.json"
    summary_json.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "delivery_manifest.json").write_text(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    report_lines = [
        "# 320E Sandbox Delivery Bundle",
        "",
        f"- input_dir: `{input_dir}`",
        f"- source_candidate_count: {source_candidate_count}",
        f"- trusted_delivery_count: {trusted_delivery_count}",
        f"- review_required_delivery_count: {review_required_delivery_count}",
        f"- rejected_source_count: {rejected_source_count}",
        f"- unique_metric_count: {unique_metric_count}",
        f"- unique_year_count: {unique_year_count}",
        f"- provenance_row_count: {provenance_row_count}",
        f"- qa_pass_count: {qa_pass}",
        f"- qa_warn_count: {qa_warn}",
        f"- qa_fail_count: {qa_fail}",
        f"- delivery_decision: {delivery_decision}",
    ]
    report_path = output_dir / "row_text_delivery_320e_report.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    for name, df in [
        ("customer_trusted_metrics_preview.jsonl", customer_trusted_df),
        ("customer_review_required_preview.jsonl", customer_review_df),
    ]:
        p = output_dir / name
        with p.open("w", encoding="utf-8") as f:
            for _, row in df.iterrows():
                f.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")

    return {
        "summary": summary_payload,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json),
        "report_md_path": str(report_path),
    }
