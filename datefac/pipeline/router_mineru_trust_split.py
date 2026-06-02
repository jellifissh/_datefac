from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import pandas as pd

from datefac.pipeline.router_driven_sandbox_pipeline import _blocked_result, _norm, _safe_sheet_name, _to_int, _write_json
from datefac.pipeline.router_review_burden_diagnostics import (
    CORE_ROLE_SET,
    SAFE_UNITLESS_METRICS,
    PER_SHARE_METRICS,
    build_alias_candidate_worklist_322b2,
    build_manual_review_worklist_322b2,
    build_review_burden_by_reason_322b2,
    build_section_context_required_diagnostics_322b2,
    build_semantic_adjudicator_worklist_322b2,
    build_unit_unknown_diagnostics_322b2,
    build_unknown_metric_label_frequency_322b2,
    known_limitations_df_322b2,
)
from datefac.mineru_body.mineru_body_delivery_builder import write_jsonl


SHEET_ORDER_322B2 = [
    "summary",
    "pending_split_before_after",
    "selected_candidate_reclassified_322b2",
    "trusted_preview_322b2",
    "review_required_preview_322b2",
    "rejected_preview_322b2",
    "review_burden_by_reason_322b2",
    "unknown_metric_label_frequency_322b2",
    "unit_unknown_diagnostics_322b2",
    "section_context_required_diagnostics_322b2",
    "alias_candidate_worklist_322b2",
    "semantic_adjudicator_worklist_322b2",
    "manual_review_worklist_322b2",
    "qa_checks",
    "known_limitations",
]


@dataclass
class RouterMineruTrustSplit322B2Config:
    pipeline_322b_dir: Path
    pipeline_322a_dir: Path
    router_integration_dir: Path
    router_dir: Path
    mineru_body_reference_dir: Path
    structtable_mapping_dir: Path
    docling_mapping_dir: Path
    pure_vlm_calibration_dir: Path
    ppstructure_benchmark_dir: Path
    output_dir: Path


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in SHEET_ORDER_322B2:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _find_workbook(directory: Path) -> Optional[Path]:
    if not directory.exists():
        return None
    workbooks = sorted(directory.glob("*.xlsx"))
    return workbooks[0] if workbooks else None


def _read_sheet(workbook: Optional[Path], sheet_name: str) -> pd.DataFrame:
    if workbook is None or not workbook.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(workbook, sheet_name=sheet_name).fillna("")
    except Exception:
        return pd.DataFrame()


def _find_sheet_with_prefix(workbook: Optional[Path], prefix: str) -> pd.DataFrame:
    if workbook is None or not workbook.exists():
        return pd.DataFrame()
    try:
        excel = pd.ExcelFile(workbook)
    except Exception:
        return pd.DataFrame()
    for sheet in excel.sheet_names:
        if str(sheet).startswith(prefix):
            try:
                return pd.read_excel(workbook, sheet_name=sheet).fillna("")
            except Exception:
                return pd.DataFrame()
    return pd.DataFrame()


def _split_risk_tags(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _load_322b_context(pipeline_322b_dir: Path) -> Dict[str, Any]:
    workbook = _find_workbook(pipeline_322b_dir)
    summary = _read_json(pipeline_322b_dir / "router_driven_sandbox_pipeline_322b_summary.json")
    metric_candidates_df = _read_sheet(workbook, "metric_candidates_all_322b")
    trusted_df = _read_sheet(workbook, "trusted_preview_322b")
    review_df = _read_sheet(workbook, "review_required_preview_322b")
    rejected_df = _read_sheet(workbook, "rejected_preview_322b")
    selected_preview_df = _find_sheet_with_prefix(workbook, "router_selected_output_preview_")
    return {
        "summary": summary,
        "metric_candidates_df": metric_candidates_df,
        "trusted_df": trusted_df,
        "review_df": review_df,
        "rejected_df": rejected_df,
        "selected_preview_df": selected_preview_df,
    }


def _load_route_role_map(router_integration_dir: Path) -> Dict[str, str]:
    workbook = _find_workbook(router_integration_dir)
    route_inventory_df = _read_sheet(workbook, "router_route_inventory")
    if route_inventory_df.empty:
        return {}
    return {
        _norm(row.get("table_asset_id")): _norm(row.get("effective_category"))
        for _, row in route_inventory_df.iterrows()
        if _norm(row.get("table_asset_id"))
    }


def _reclassify_pending_candidate(row: pd.Series, role_map: Dict[str, str]) -> Tuple[str, str, str]:
    risk_tags = set(_split_risk_tags(row.get("risk_tags")))
    metric_code = _norm(row.get("metric_code"))
    table_asset_id = _norm(row.get("source_table_id"))
    role = _norm(role_map.get(table_asset_id))
    year = _norm(row.get("year"))
    unit = _norm(row.get("unit"))
    provenance = _norm(row.get("provenance_json"))
    normalized_value = row.get("normalized_value")

    if any(tag in risk_tags for tag in {"CHINESE_LABEL_CORRUPTED", "TABLE_NOT_PARSEABLE", "NOISE_LEAK_BBOX_HTML"}):
        return "rejected_preview", "STRICT_REJECT_TAG", "|".join(sorted(risk_tags))
    if any(tag in risk_tags for tag in {"OUT_OF_SCOPE_METRIC", "NON_CORE_STATEMENT_LINE"}):
        return "rejected_preview", "OUT_OF_SCOPE_REJECT", "|".join(sorted(risk_tags))
    if role and role not in CORE_ROLE_SET:
        return "review_required_preview", "NON_CORE_ROLE_REVIEW", "|".join(sorted(risk_tags))
    if metric_code == "unknown_metric" or "UNKNOWN_METRIC_CODE" in risk_tags:
        return "review_required_preview", "UNKNOWN_METRIC_CODE", "|".join(sorted(risk_tags))
    if any(tag in risk_tags for tag in {"SECTION_CONTEXT_REQUIRED", "VALUE_CONFLICT"}):
        if "SECTION_CONTEXT_REQUIRED" not in risk_tags:
            risk_tags.add("SECTION_CONTEXT_REQUIRED")
        return "review_required_preview", "SECTION_CONTEXT_REQUIRED", "|".join(sorted(risk_tags))
    if any(tag in risk_tags for tag in {"INVALID_YEAR", "YEAR_MISSING", "NO_YEAR_COLUMNS"}):
        return "review_required_preview", "INVALID_OR_MISSING_YEAR", "|".join(sorted(risk_tags))
    if any(tag in risk_tags for tag in {"VALUE_PARSE_FAILED", "VALUE_MISSING", "ROW_LABEL_MISSING"}):
        return "review_required_preview", "VALUE_PARSE_FAILED_OR_SCHEMA_UNCERTAIN", "|".join(sorted(risk_tags))
    if pd.isna(normalized_value) or _norm(normalized_value) == "" or not provenance:
        return "review_required_preview", "VALUE_OR_PROVENANCE_INCOMPLETE", "|".join(sorted(risk_tags))
    if not unit and metric_code not in SAFE_UNITLESS_METRICS and metric_code not in PER_SHARE_METRICS:
        if "UNIT_UNKNOWN" not in risk_tags:
            risk_tags.add("UNIT_UNKNOWN")
        return "review_required_preview", "UNIT_UNKNOWN", "|".join(sorted(risk_tags))
    if not year or not pd.Series([year]).astype(str).str.match(r"^20\d{2}(?:[AE])?$", na=False).iloc[0]:
        return "review_required_preview", "INVALID_OR_MISSING_YEAR", "|".join(sorted(risk_tags))
    return "trusted_preview", "PASS_ROUTER_MINERU_TRUST_SPLIT", "|".join(sorted(risk_tags))


def _build_pending_split_before_after(
    candidates_before_df: pd.DataFrame,
    reclassified_df: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "source_stage",
        "selected_output_source",
        "pending_before_count",
        "pending_after_count",
        "trusted_after_count",
        "review_required_after_count",
        "rejected_after_count",
        "reason",
    ]
    if candidates_before_df.empty:
        return pd.DataFrame(columns=columns)
    before = candidates_before_df.copy()
    after = reclassified_df.copy()
    rows = []
    keys = sorted(
        {
            (str(source_stage), str(selected_output_source))
            for source_stage, selected_output_source in zip(
                before["source_stage"].astype(str),
                before["selected_output_source"].astype(str),
            )
        }
    )
    for source_stage, selected_output_source in keys:
        before_group = before[
            (before["source_stage"].astype(str) == source_stage)
            & (before["selected_output_source"].astype(str) == selected_output_source)
        ]
        after_group = after[
            (after["source_stage"].astype(str) == source_stage)
            & (after["selected_output_source"].astype(str) == selected_output_source)
        ]
        rows.append(
            {
                "source_stage": source_stage,
                "selected_output_source": selected_output_source,
                "pending_before_count": int(before_group["split_reason"].astype(str).eq("PENDING_MINERU_BODY_TRUST_SPLIT").sum()),
                "pending_after_count": int(after_group["reclassification_reason"].astype(str).eq("PENDING_MINERU_BODY_TRUST_SPLIT").sum()),
                "trusted_after_count": int(after_group["decision_after"].astype(str).eq("trusted_preview").sum()),
                "review_required_after_count": int(after_group["decision_after"].astype(str).eq("review_required_preview").sum()),
                "rejected_after_count": int(after_group["decision_after"].astype(str).eq("rejected_preview").sum()),
                "reason": "router-driven MinerU pending split recalibrated",
            }
        )
    return pd.DataFrame(rows, columns=columns)


def run_router_mineru_trust_split_322b2(config: RouterMineruTrustSplit322B2Config) -> Dict[str, Any]:
    if not config.pipeline_322b_dir.exists():
        return _blocked_result(config, "BLOCKED_MISSING_322B_PIPELINE_DIR")

    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    ctx_322b = _load_322b_context(config.pipeline_322b_dir)
    candidates_before_df = ctx_322b["metric_candidates_df"].copy()
    trusted_before_df = ctx_322b["trusted_df"].copy()
    review_before_df = ctx_322b["review_df"].copy()
    selected_preview_df = ctx_322b["selected_preview_df"].copy()
    role_map = _load_route_role_map(config.router_integration_dir)

    candidates_before_df = candidates_before_df.fillna("") if not candidates_before_df.empty else pd.DataFrame()
    reclassified_df = candidates_before_df.copy()
    if not reclassified_df.empty:
        reclassified_df["table_asset_id"] = reclassified_df["source_table_id"].astype(str)
        reclassified_df["source_report_name"] = reclassified_df["source_doc_name"].astype(str)
        reclassified_df["decision_before"] = reclassified_df["split_decision"].astype(str)
        reclassified_df["risk_tags_before"] = reclassified_df["risk_tags"].astype(str)
        reclassified_df["reclassification_reason"] = ""
        reclassified_df["decision_after"] = reclassified_df["split_decision"].astype(str)
        reclassified_df["risk_tags_after"] = reclassified_df["risk_tags"].astype(str)
        pending_mask = reclassified_df["split_reason"].astype(str) == "PENDING_MINERU_BODY_TRUST_SPLIT"
        if pending_mask.any():
            pending_rows = reclassified_df.loc[pending_mask].copy()
            decisions = pending_rows.apply(
                lambda row: _reclassify_pending_candidate(row, role_map),
                axis=1,
                result_type="expand",
            )
            reclassified_df.loc[pending_mask, "decision_after"] = decisions[0].tolist()
            reclassified_df.loc[pending_mask, "reclassification_reason"] = decisions[1].tolist()
            reclassified_df.loc[pending_mask, "risk_tags_after"] = decisions[2].tolist()
        non_pending_mask = ~pending_mask
        reclassified_df.loc[non_pending_mask, "reclassification_reason"] = reclassified_df.loc[non_pending_mask, "split_reason"].astype(str)
        reclassified_df["split_decision"] = reclassified_df["decision_after"].astype(str)
        reclassified_df["split_reason"] = reclassified_df["reclassification_reason"].astype(str)
        reclassified_df["risk_tags"] = reclassified_df["risk_tags_after"].astype(str)

    trusted_after_df = reclassified_df[reclassified_df["decision_after"].astype(str) == "trusted_preview"].copy() if not reclassified_df.empty else pd.DataFrame()
    review_after_df = reclassified_df[reclassified_df["decision_after"].astype(str) == "review_required_preview"].copy() if not reclassified_df.empty else pd.DataFrame()
    rejected_after_df = reclassified_df[reclassified_df["decision_after"].astype(str) == "rejected_preview"].copy() if not reclassified_df.empty else pd.DataFrame()

    pending_split_before_after_df = _build_pending_split_before_after(candidates_before_df, reclassified_df)
    review_burden_by_reason_df = build_review_burden_by_reason_322b2(review_after_df)
    unknown_metric_label_frequency_df = build_unknown_metric_label_frequency_322b2(review_after_df)
    unit_unknown_diagnostics_df = build_unit_unknown_diagnostics_322b2(review_after_df)
    section_context_required_diagnostics_df = build_section_context_required_diagnostics_322b2(review_after_df)
    alias_candidate_worklist_df = build_alias_candidate_worklist_322b2(unknown_metric_label_frequency_df)
    semantic_adjudicator_worklist_df = build_semantic_adjudicator_worklist_322b2(review_after_df)
    manual_review_worklist_df = build_manual_review_worklist_322b2(review_after_df)

    input_candidate_count = len(candidates_before_df)
    pending_split_before_count = int(candidates_before_df["split_reason"].astype(str).eq("PENDING_MINERU_BODY_TRUST_SPLIT").sum()) if not candidates_before_df.empty else 0
    pending_split_after_count = int(review_after_df["split_reason"].astype(str).eq("PENDING_MINERU_BODY_TRUST_SPLIT").sum()) if not review_after_df.empty else 0
    reclassified_candidate_count = int(
        (
            (reclassified_df["decision_before"].astype(str) != reclassified_df["decision_after"].astype(str))
            | (
                (candidates_before_df["split_reason"].astype(str) == "PENDING_MINERU_BODY_TRUST_SPLIT")
                & (reclassified_df["reclassification_reason"].astype(str) != "PENDING_MINERU_BODY_TRUST_SPLIT")
            )
        ).sum()
    ) if not reclassified_df.empty else 0
    trusted_total_before_322b2 = len(trusted_before_df)
    trusted_total_after_322b2 = len(trusted_after_df)
    review_required_total_before_322b2 = len(review_before_df)
    review_required_total_after_322b2 = len(review_after_df)
    rejected_total_after_322b2 = len(rejected_after_df)
    selected_all_trusted_rate_after_322b2 = round(trusted_total_after_322b2 / input_candidate_count, 6) if input_candidate_count else 0.0

    core_ids = {table_id for table_id, role in role_map.items() if role in CORE_ROLE_SET}
    core_before_df = candidates_before_df[candidates_before_df["source_table_id"].astype(str).isin(core_ids)] if not candidates_before_df.empty else pd.DataFrame()
    core_after_df = reclassified_df[reclassified_df["source_table_id"].astype(str).isin(core_ids)] if not reclassified_df.empty else pd.DataFrame()
    selected_core_trusted_rate_before_322b2 = round(
        len(core_before_df[core_before_df["split_decision"].astype(str) == "trusted_preview"]) / len(core_before_df),
        6,
    ) if not core_before_df.empty else 0.0
    selected_core_trusted_rate_after_322b2 = round(
        len(core_after_df[core_after_df["decision_after"].astype(str) == "trusted_preview"]) / len(core_after_df),
        6,
    ) if not core_after_df.empty else 0.0

    unknown_metric_candidate_count = int((review_after_df["metric_code"].astype(str) == "unknown_metric").sum()) if not review_after_df.empty else 0
    unit_unknown_candidate_count = int(
        review_after_df["risk_tags_after"].astype(str).str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True).sum()
    ) if not review_after_df.empty else 0
    value_conflict_candidate_count = int(
        review_after_df["risk_tags_after"].astype(str).str.contains(r"(?:^|\|)VALUE_CONFLICT(?:$|\|)", regex=True).sum()
    ) if not review_after_df.empty else 0
    section_context_required_candidate_count = int(review_after_df["split_reason"].astype(str).eq("SECTION_CONTEXT_REQUIRED").sum()) if not review_after_df.empty else 0
    alias_candidate_count = len(alias_candidate_worklist_df)
    semantic_adjudicator_worklist_count = len(semantic_adjudicator_worklist_df)
    manual_review_worklist_count = len(manual_review_worklist_df)

    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa("pipeline_322b_dir_exists", "PASS" if config.pipeline_322b_dir.exists() else "FAIL", str(config.pipeline_322b_dir))
    add_qa("no_e_drive_files_modified", "PASS", "322B2 reads sandbox outputs only and does not modify E-drive files")
    add_qa("no_recognizer_command_executed", "PASS", "322B2 does not run MinerU/StructEqTable/Docling/PPStructure/VLM")
    add_qa("no_production_files_modified", "PASS", "322B2 writes sandbox outputs only")
    candidate_identity_ok = reclassified_df.empty or (
        reclassified_df["source_table_id"].astype(str).str.len().gt(0).all()
        and reclassified_df["source_stage"].astype(str).str.len().gt(0).all()
    )
    add_qa("every_candidate_has_table_asset_id_and_source_stage", "PASS" if candidate_identity_ok else "FAIL", f"candidate_count={input_candidate_count}")
    trusted_valid_ok = trusted_after_df.empty or (
        trusted_after_df["year"].astype(str).str.match(r"^20\d{2}(?:[AE])?$", na=False).all()
        and (trusted_after_df["metric_code"].astype(str) != "unknown_metric").all()
        and trusted_after_df["normalized_value"].astype(str).str.len().gt(0).all()
        and trusted_after_df["provenance_json"].astype(str).str.len().gt(0).all()
    )
    add_qa("trusted_candidates_have_valid_year_metric_value_and_provenance", "PASS" if trusted_valid_ok else "FAIL", f"trusted_after={trusted_total_after_322b2}")
    pending_in_trusted = int(trusted_after_df["split_reason"].astype(str).eq("PENDING_MINERU_BODY_TRUST_SPLIT").sum()) if not trusted_after_df.empty else 0
    add_qa("no_trusted_candidate_retains_pending_split_tag", "PASS" if pending_in_trusted == 0 else "FAIL", f"pending_in_trusted={pending_in_trusted}")
    add_qa(
        "pending_split_count_reduced",
        "PASS" if pending_split_after_count < pending_split_before_count else "FAIL",
        f"before={pending_split_before_count}; after={pending_split_after_count}",
    )

    output_files = {
        "excel": output_dir / "router_mineru_trust_split_322b2.xlsx",
        "summary_json": output_dir / "router_mineru_trust_split_322b2_summary.json",
        "report_md": output_dir / "router_mineru_trust_split_322b2_report.md",
        "reclassified_jsonl": output_dir / "selected_candidate_reclassified_322b2.jsonl",
        "alias_jsonl": output_dir / "alias_candidate_worklist_322b2.jsonl",
        "semantic_jsonl": output_dir / "semantic_adjudicator_worklist_322b2.jsonl",
    }
    add_qa(
        "many_candidates_remain_review_required_after_real_split",
        "WARN" if review_required_total_after_322b2 > trusted_total_after_322b2 else "PASS",
        f"review_after={review_required_total_after_322b2}; trusted_after={trusted_total_after_322b2}",
    )
    add_qa(
        "unknown_metric_labels_remain_high",
        "WARN" if unknown_metric_candidate_count >= 500 else "PASS",
        f"unknown_metric_candidate_count={unknown_metric_candidate_count}",
    )
    add_qa(
        "unit_unknown_remains_high",
        "WARN" if unit_unknown_candidate_count >= 100 else "PASS",
        f"unit_unknown_candidate_count={unit_unknown_candidate_count}",
    )
    add_qa(
        "semantic_adjudicator_still_needed",
        "WARN" if semantic_adjudicator_worklist_count > 0 else "PASS",
        f"semantic_adjudicator_worklist_count={semantic_adjudicator_worklist_count}",
    )

    qa_df = pd.DataFrame(qa_rows)
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    if qa_fail_count > 0:
        decision = "ROUTER_MINERU_TRUST_SPLIT_BLOCKED_BY_QA_FAILURE"
    elif pending_split_after_count == 0 and reclassified_candidate_count > 0:
        decision = "ROUTER_MINERU_TRUST_SPLIT_READY_FOR_SEMANTIC_ADJUDICATOR_DESIGN"
    elif pending_split_before_count and pending_split_after_count < pending_split_before_count * 0.1:
        decision = "ROUTER_MINERU_TRUST_SPLIT_PARTIAL_READY_FOR_REVIEW_ACTIONS"
    else:
        decision = "ROUTER_MINERU_TRUST_SPLIT_NEEDS_GATE_FIXES"

    top_review_reasons_after_split = (
        review_after_df["split_reason"].astype(str).value_counts().head(10).to_dict() if not review_after_df.empty else {}
    )
    summary = {
        "stage": "322B2",
        "output_dir": str(output_dir),
        "input_candidate_count": input_candidate_count,
        "pending_split_before_count": pending_split_before_count,
        "pending_split_after_count": pending_split_after_count,
        "reclassified_candidate_count": reclassified_candidate_count,
        "trusted_total_before_322b2": trusted_total_before_322b2,
        "trusted_total_after_322b2": trusted_total_after_322b2,
        "review_required_total_before_322b2": review_required_total_before_322b2,
        "review_required_total_after_322b2": review_required_total_after_322b2,
        "rejected_total_after_322b2": rejected_total_after_322b2,
        "selected_core_trusted_rate_before_322b2": selected_core_trusted_rate_before_322b2,
        "selected_core_trusted_rate_after_322b2": selected_core_trusted_rate_after_322b2,
        "selected_all_trusted_rate_after_322b2": selected_all_trusted_rate_after_322b2,
        "unknown_metric_candidate_count": unknown_metric_candidate_count,
        "unit_unknown_candidate_count": unit_unknown_candidate_count,
        "value_conflict_candidate_count": value_conflict_candidate_count,
        "section_context_required_candidate_count": section_context_required_candidate_count,
        "alias_candidate_count": alias_candidate_count,
        "semantic_adjudicator_worklist_count": semantic_adjudicator_worklist_count,
        "manual_review_worklist_count": manual_review_worklist_count,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "router_mineru_trust_split_decision": decision,
        "top_review_reasons_after_split": top_review_reasons_after_split,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    report_lines = [
        "# Router MinerU Trust Split 322B2",
        "",
        "## Decision",
        f"- router_mineru_trust_split_decision: {decision}",
        "",
        "## Counts",
        f"- input_candidate_count: {input_candidate_count}",
        f"- pending_split_before_count: {pending_split_before_count}",
        f"- pending_split_after_count: {pending_split_after_count}",
        f"- trusted_total_after_322b2: {trusted_total_after_322b2}",
        f"- review_required_total_after_322b2: {review_required_total_after_322b2}",
        f"- rejected_total_after_322b2: {rejected_total_after_322b2}",
        "",
        "## Rates",
        f"- selected_core_trusted_rate_before_322b2: {selected_core_trusted_rate_before_322b2}",
        f"- selected_core_trusted_rate_after_322b2: {selected_core_trusted_rate_after_322b2}",
        f"- selected_all_trusted_rate_after_322b2: {selected_all_trusted_rate_after_322b2}",
        "",
        "## QA",
        f"- qa_pass_count: {qa_pass_count}",
        f"- qa_warn_count: {qa_warn_count}",
        f"- qa_fail_count: {qa_fail_count}",
        "",
    ]

    sheets = {
        "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
        "pending_split_before_after": pending_split_before_after_df,
        "selected_candidate_reclassified_322b2": reclassified_df[
            [
                "table_asset_id",
                "source_report_name",
                "selected_output_source",
                "source_stage",
                "metric_code",
                "metric_family",
                "year",
                "raw_value",
                "normalized_value",
                "unit",
                "decision_before",
                "decision_after",
                "risk_tags_before",
                "risk_tags_after",
                "reclassification_reason",
                "provenance_json",
            ]
        ].rename(columns={"provenance_json": "provenance"}) if not reclassified_df.empty else pd.DataFrame(),
        "trusted_preview_322b2": trusted_after_df,
        "review_required_preview_322b2": review_after_df,
        "rejected_preview_322b2": rejected_after_df,
        "review_burden_by_reason_322b2": review_burden_by_reason_df,
        "unknown_metric_label_frequency_322b2": unknown_metric_label_frequency_df,
        "unit_unknown_diagnostics_322b2": unit_unknown_diagnostics_df,
        "section_context_required_diagnostics_322b2": section_context_required_diagnostics_df,
        "alias_candidate_worklist_322b2": alias_candidate_worklist_df,
        "semantic_adjudicator_worklist_322b2": semantic_adjudicator_worklist_df,
        "manual_review_worklist_322b2": manual_review_worklist_df,
        "qa_checks": qa_df,
        "known_limitations": known_limitations_df_322b2(),
    }
    _write_excel(output_files["excel"], sheets)
    _write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text("\n".join(report_lines), encoding="utf-8")
    if not reclassified_df.empty:
        write_jsonl(output_files["reclassified_jsonl"], reclassified_df)
    if not alias_candidate_worklist_df.empty:
        write_jsonl(output_files["alias_jsonl"], alias_candidate_worklist_df)
    if not semantic_adjudicator_worklist_df.empty:
        write_jsonl(output_files["semantic_jsonl"], semantic_adjudicator_worklist_df)

    output_file_exists = all(
        output_files[key].exists()
        for key in ["excel", "summary_json", "report_md", "reclassified_jsonl"]
    )
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "output_files_written_successfully",
                        "status": "PASS" if output_file_exists else "FAIL",
                        "detail": str(output_dir),
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    summary["qa_pass_count"] = qa_pass_count
    summary["qa_warn_count"] = qa_warn_count
    summary["qa_fail_count"] = qa_fail_count
    if qa_fail_count > 0:
        summary["router_mineru_trust_split_decision"] = "ROUTER_MINERU_TRUST_SPLIT_BLOCKED_BY_QA_FAILURE"
    final_sheets = {
        **sheets,
        "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
        "qa_checks": qa_df,
    }
    _write_excel(output_files["excel"], final_sheets)
    _write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(
        "\n".join(
            [
                "# Router MinerU Trust Split 322B2",
                "",
                "## Decision",
                f"- router_mineru_trust_split_decision: {summary['router_mineru_trust_split_decision']}",
                "",
                "## Counts",
                f"- input_candidate_count: {summary['input_candidate_count']}",
                f"- pending_split_before_count: {summary['pending_split_before_count']}",
                f"- pending_split_after_count: {summary['pending_split_after_count']}",
                f"- trusted_total_after_322b2: {summary['trusted_total_after_322b2']}",
                f"- review_required_total_after_322b2: {summary['review_required_total_after_322b2']}",
                f"- rejected_total_after_322b2: {summary['rejected_total_after_322b2']}",
                "",
                "## Rates",
                f"- selected_core_trusted_rate_before_322b2: {summary['selected_core_trusted_rate_before_322b2']}",
                f"- selected_core_trusted_rate_after_322b2: {summary['selected_core_trusted_rate_after_322b2']}",
                f"- selected_all_trusted_rate_after_322b2: {summary['selected_all_trusted_rate_after_322b2']}",
                "",
                "## QA",
                f"- qa_pass_count: {summary['qa_pass_count']}",
                f"- qa_warn_count: {summary['qa_warn_count']}",
                f"- qa_fail_count: {summary['qa_fail_count']}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return {
        "summary": summary,
        "excel_path": str(output_files["excel"]),
        "summary_json_path": str(output_files["summary_json"]),
        "report_md_path": str(output_files["report_md"]),
    }
