from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_label(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").lower()


def _split_tags(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _join_tags(tags: List[str]) -> str:
    seen: List[str] = []
    for tag in tags:
        clean = _norm(tag)
        if clean and clean not in seen:
            seen.append(clean)
    return "|".join(seen)


def _parse_provenance_json(value: Any) -> Dict[str, Any]:
    text = _norm(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _find_workbook(directory: Path) -> Optional[Path]:
    if not directory.exists():
        return None
    workbooks = sorted(directory.glob("*.xlsx"))
    return workbooks[0] if workbooks else None


def read_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                rows.append(json.loads(text))
            except Exception:
                continue
    return pd.DataFrame(rows).fillna("")


def read_excel_sheet(workbook: Optional[Path], sheet_name: str) -> pd.DataFrame:
    if workbook is None or not workbook.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(workbook, sheet_name=sheet_name).fillna("")
    except Exception:
        return pd.DataFrame()


def load_replay_inputs(adjudicator_limited_dir: Path, trust_split_dir: Path) -> Dict[str, pd.DataFrame]:
    limited_workbook = _find_workbook(adjudicator_limited_dir)
    trust_workbook = _find_workbook(trust_split_dir)

    return {
        "limited_summary_df": read_excel_sheet(limited_workbook, "summary"),
        "deterministic_gate_results_df": read_excel_sheet(limited_workbook, "deterministic_gate_results"),
        "alias_replay_df": read_excel_sheet(limited_workbook, "alias_replay_instructions"),
        "out_scope_replay_df": read_excel_sheet(limited_workbook, "out_of_scope_replay_instruction"),
        "unit_replay_df": read_excel_sheet(limited_workbook, "unit_inference_replay_instructi"),
        "trusted_before_df": read_excel_sheet(trust_workbook, "trusted_preview_322b2"),
        "review_before_df": read_excel_sheet(trust_workbook, "review_required_preview_322b2"),
        "rejected_before_df": read_excel_sheet(trust_workbook, "rejected_preview_322b2"),
        "trust_summary_df": read_excel_sheet(trust_workbook, "summary"),
    }


def build_replay_instruction_inventory(
    deterministic_gate_results_df: pd.DataFrame,
    alias_replay_df: pd.DataFrame,
    out_scope_replay_df: pd.DataFrame,
    unit_replay_df: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "instruction_id",
        "case_id",
        "instruction_type",
        "normalized_label",
        "proposed_metric_code",
        "proposed_metric_family",
        "proposed_unit",
        "confidence_label",
        "affected_candidate_count",
        "replay_allowed",
        "replay_block_reason",
    ]
    rows: List[Dict[str, Any]] = []
    alias_lookup = {
        _normalize_label(row.get("normalized_label")): row.to_dict()
        for _, row in alias_replay_df.iterrows()
    } if not alias_replay_df.empty else {}
    out_scope_lookup = {
        _normalize_label(row.get("normalized_label")): row.to_dict()
        for _, row in out_scope_replay_df.iterrows()
    } if not out_scope_replay_df.empty else {}
    unit_lookup = {
        _norm(row.get("case_id")): row.to_dict()
        for _, row in unit_replay_df.iterrows()
    } if not unit_replay_df.empty else {}

    if deterministic_gate_results_df.empty:
        return pd.DataFrame(columns=columns)

    for index, row in deterministic_gate_results_df.iterrows():
        case_id = _norm(row.get("case_id"))
        gate_result = _norm(row.get("gate_result"))
        normalized_label = case_id.split("label::", 1)[1] if case_id.startswith("label::") else ""
        alias_row = alias_lookup.get(_normalize_label(normalized_label), {})
        out_scope_row = out_scope_lookup.get(_normalize_label(normalized_label), {})
        unit_row = unit_lookup.get(case_id, {})
        instruction_type = gate_result
        proposed_metric_code = ""
        proposed_metric_family = ""
        proposed_unit = ""
        confidence_label = _norm(row.get("confidence_label"))
        affected_candidate_count = int(row.get("affected_candidate_count") or 0)
        replay_allowed = gate_result in {
            "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY",
            "CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY",
            "ACCEPT_UNIT_INFERENCE_FOR_REPLAY",
            "REJECT_NOISE_FOR_REPLAY",
        }
        replay_block_reason = "" if replay_allowed else gate_result

        if gate_result == "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY":
            proposed_metric_code = _norm(alias_row.get("proposed_metric_code") or row.get("metric_code"))
            proposed_metric_family = _norm(alias_row.get("proposed_metric_family"))
            confidence_label = _norm(alias_row.get("confidence_label") or confidence_label)
        elif gate_result == "CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY":
            confidence_label = _norm(out_scope_row.get("confidence_label") or confidence_label)
        elif gate_result == "ACCEPT_UNIT_INFERENCE_FOR_REPLAY":
            proposed_unit = _norm(unit_row.get("proposed_unit"))
            confidence_label = _norm(unit_row.get("confidence_label") or confidence_label)
        elif gate_result == "REJECT_NOISE_FOR_REPLAY":
            proposed_metric_code = ""

        rows.append(
            {
                "instruction_id": f"replay::{index + 1:03d}",
                "case_id": case_id,
                "instruction_type": instruction_type,
                "normalized_label": normalized_label,
                "proposed_metric_code": proposed_metric_code,
                "proposed_metric_family": proposed_metric_family,
                "proposed_unit": proposed_unit,
                "confidence_label": confidence_label,
                "affected_candidate_count": affected_candidate_count,
                "replay_allowed": replay_allowed,
                "replay_block_reason": replay_block_reason,
            }
        )
    return pd.DataFrame(rows, columns=columns).fillna("")


def _candidate_passes_trust_gate(row: pd.Series) -> bool:
    year_source = _norm(row.get("year_source"))
    unit = _norm(row.get("unit")) or _norm(row.get("table_unit"))
    provenance = _parse_provenance_json(row.get("provenance_json"))
    risk_tags = set(_split_tags(row.get("risk_tags_after")))
    normalized_value = row.get("normalized_value")

    if year_source == "INVALID" or not _norm(row.get("year")):
        return False
    if normalized_value in ("", None) or (isinstance(normalized_value, float) and pd.isna(normalized_value)):
        return False
    if not provenance:
        return False
    if not unit:
        return False
    blocker_tags = {
        "UNKNOWN_METRIC_CODE",
        "UNIT_UNKNOWN",
        "VALUE_PARSE_FAILED",
        "INVALID_YEAR",
        "NO_YEAR_COLUMNS",
        "VALUE_CONFLICT",
        "EXTRACTION_RISK",
        "SECTION_CONTEXT_REQUIRED",
    }
    if risk_tags.intersection(blocker_tags):
        return False
    if _norm(row.get("metric_code")) in {"", "unknown_metric"}:
        return False
    return True


def apply_replay(
    replay_instruction_inventory_df: pd.DataFrame,
    trusted_before_df: pd.DataFrame,
    review_before_df: pd.DataFrame,
    rejected_before_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    trusted_after_df = trusted_before_df.copy()
    review_after_df = review_before_df.copy()
    rejected_after_df = rejected_before_df.copy()

    if trusted_after_df.empty:
        trusted_after_df = pd.DataFrame(columns=review_before_df.columns)
    if review_after_df.empty:
        review_after_df = pd.DataFrame(columns=trusted_before_df.columns)
    if rejected_after_df.empty:
        rejected_after_df = pd.DataFrame(columns=review_before_df.columns)

    for df in [trusted_after_df, review_after_df, rejected_after_df]:
        if not df.empty:
            df["normalized_label"] = df["raw_metric_name"].map(_normalize_label)
    diff_rows: List[Dict[str, Any]] = []
    reduction_rows: List[Dict[str, Any]] = []

    if replay_instruction_inventory_df.empty:
        return (
            replay_instruction_inventory_df,
            pd.DataFrame(),
            trusted_after_df.drop(columns=["normalized_label"], errors="ignore"),
            review_after_df.drop(columns=["normalized_label"], errors="ignore"),
            rejected_after_df.drop(columns=["normalized_label"], errors="ignore"),
        )

    for _, instruction in replay_instruction_inventory_df.iterrows():
        instruction_id = _norm(instruction.get("instruction_id"))
        case_id = _norm(instruction.get("case_id"))
        instruction_type = _norm(instruction.get("instruction_type"))
        normalized_label = _normalize_label(instruction.get("normalized_label"))
        proposed_metric_code = _norm(instruction.get("proposed_metric_code"))
        proposed_metric_family = _norm(instruction.get("proposed_metric_family"))
        proposed_unit = _norm(instruction.get("proposed_unit"))
        replay_allowed = bool(instruction.get("replay_allowed"))

        candidates_affected = 0
        trusted_gain = 0
        review_reduction = 0
        rejected_gain = 0

        if not replay_allowed:
            reduction_rows.append(
                {
                    "instruction_id": instruction_id,
                    "case_id": case_id,
                    "instruction_type": instruction_type,
                    "candidates_affected": 0,
                    "trusted_gain": 0,
                    "review_reduction": 0,
                    "rejected_or_out_of_scope_count": 0,
                    "notes": "instruction_not_replay_allowed",
                }
            )
            continue

        if instruction_type == "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY":
            mask = review_after_df["normalized_label"].astype(str) == normalized_label
            matched = review_after_df[mask].copy()
            candidates_affected = len(matched)
            if matched.empty:
                reduction_rows.append(
                    {
                        "instruction_id": instruction_id,
                        "case_id": case_id,
                        "instruction_type": instruction_type,
                        "candidates_affected": 0,
                        "trusted_gain": 0,
                        "review_reduction": 0,
                        "rejected_or_out_of_scope_count": 0,
                        "notes": "no_review_candidates_matched",
                    }
                )
                continue

            matched["metric_code_before"] = matched["metric_code"]
            matched["unit_before"] = matched["unit"]
            matched["decision_before_replay"] = matched["split_decision"]
            matched["risk_tags_before_replay"] = matched["risk_tags_after"]

            for idx, row in matched.iterrows():
                current_tags = _split_tags(row.get("risk_tags_after"))
                current_tags = [tag for tag in current_tags if tag != "UNKNOWN_METRIC_CODE"]
                metric_code_after = proposed_metric_code
                metric_family_after = proposed_metric_family or _norm(row.get("metric_family"))
                updated_row = row.copy()
                updated_row["metric_code"] = metric_code_after
                updated_row["metric_family"] = metric_family_after
                updated_row["canonical_metric_name"] = metric_code_after
                updated_row["risk_tags_after"] = _join_tags(current_tags)
                updated_row["reclassification_reason"] = f"SEMANTIC_REPLAY::{instruction_id}"
                updated_row["split_reason"] = f"SEMANTIC_REPLAY::{instruction_type}"

                if _candidate_passes_trust_gate(updated_row):
                    decision_after = "trusted_preview"
                    trusted_gain += 1
                    review_reduction += 1
                    updated_row["split_decision"] = decision_after
                    updated_row["decision_after"] = decision_after
                    trusted_after_df = pd.concat([trusted_after_df, pd.DataFrame([updated_row.drop(labels=['normalized_label'], errors='ignore')])], ignore_index=True)
                else:
                    decision_after = "review_required_preview"
                    updated_row["split_decision"] = decision_after
                    updated_row["decision_after"] = decision_after
                    review_after_df = pd.concat([review_after_df, pd.DataFrame([updated_row])], ignore_index=True)

                diff_rows.append(
                    {
                        "table_asset_id": _norm(row.get("table_asset_id")),
                        "source_report_name": _norm(row.get("source_report_name")),
                        "row_label": _norm(row.get("raw_metric_name")),
                        "year": _norm(row.get("year")),
                        "raw_value": _norm(row.get("raw_value")),
                        "normalized_value": row.get("normalized_value"),
                        "unit_before": _norm(row.get("unit")),
                        "unit_after": _norm(updated_row.get("unit")),
                        "metric_code_before": _norm(row.get("metric_code_before")),
                        "metric_code_after": _norm(updated_row.get("metric_code")),
                        "decision_before": _norm(row.get("decision_before_replay")),
                        "decision_after": _norm(updated_row.get("split_decision")),
                        "risk_tags_before": _norm(row.get("risk_tags_before_replay")),
                        "risk_tags_after": _norm(updated_row.get("risk_tags_after")),
                        "replay_instruction_id": instruction_id,
                        "replay_reason": instruction_type,
                        "provenance": _norm(row.get("provenance_json")),
                    }
                )

            review_after_df = review_after_df[~mask].copy()
            review_after_df.reset_index(drop=True, inplace=True)

        elif instruction_type in {"CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY", "REJECT_NOISE_FOR_REPLAY"}:
            mask = review_after_df["normalized_label"].astype(str) == normalized_label
            matched = review_after_df[mask].copy()
            candidates_affected = len(matched)
            if not matched.empty:
                review_after_df = review_after_df[~mask].copy()
                matched["split_decision"] = "rejected_preview"
                matched["decision_after"] = "rejected_preview"
                matched["split_reason"] = f"SEMANTIC_REPLAY::{instruction_type}"
                matched["reclassification_reason"] = f"SEMANTIC_REPLAY::{instruction_id}"
                rejected_after_df = pd.concat([rejected_after_df, matched.drop(columns=["normalized_label"], errors="ignore")], ignore_index=True)
                rejected_gain = len(matched)
                review_reduction = len(matched)
            reduction_rows.append(
                {
                    "instruction_id": instruction_id,
                    "case_id": case_id,
                    "instruction_type": instruction_type,
                    "candidates_affected": candidates_affected,
                    "trusted_gain": 0,
                    "review_reduction": review_reduction,
                    "rejected_or_out_of_scope_count": rejected_gain,
                    "notes": "sandbox_rejected_from_review",
                }
            )
            continue

        elif instruction_type == "ACCEPT_UNIT_INFERENCE_FOR_REPLAY":
            mask = review_after_df["normalized_label"].astype(str) == normalized_label
            matched = review_after_df[mask].copy()
            candidates_affected = len(matched)
            if matched.empty:
                reduction_rows.append(
                    {
                        "instruction_id": instruction_id,
                        "case_id": case_id,
                        "instruction_type": instruction_type,
                        "candidates_affected": 0,
                        "trusted_gain": 0,
                        "review_reduction": 0,
                        "rejected_or_out_of_scope_count": 0,
                        "notes": "no_review_candidates_matched",
                    }
                )
                continue
            matched["unit_before"] = matched["unit"]
            for idx, row in matched.iterrows():
                current_tags = _split_tags(row.get("risk_tags_after"))
                current_tags = [tag for tag in current_tags if tag != "UNIT_UNKNOWN"]
                updated_row = row.copy()
                updated_row["unit"] = proposed_unit or _norm(row.get("unit"))
                updated_row["risk_tags_after"] = _join_tags(current_tags)
                updated_row["reclassification_reason"] = f"SEMANTIC_REPLAY::{instruction_id}"
                updated_row["split_reason"] = f"SEMANTIC_REPLAY::{instruction_type}"
                if _candidate_passes_trust_gate(updated_row):
                    decision_after = "trusted_preview"
                    trusted_gain += 1
                    review_reduction += 1
                    updated_row["split_decision"] = decision_after
                    updated_row["decision_after"] = decision_after
                    trusted_after_df = pd.concat([trusted_after_df, pd.DataFrame([updated_row.drop(labels=['normalized_label'], errors='ignore')])], ignore_index=True)
                else:
                    updated_row["split_decision"] = "review_required_preview"
                    updated_row["decision_after"] = "review_required_preview"
                    review_after_df = pd.concat([review_after_df, pd.DataFrame([updated_row])], ignore_index=True)
                diff_rows.append(
                    {
                        "table_asset_id": _norm(row.get("table_asset_id")),
                        "source_report_name": _norm(row.get("source_report_name")),
                        "row_label": _norm(row.get("raw_metric_name")),
                        "year": _norm(row.get("year")),
                        "raw_value": _norm(row.get("raw_value")),
                        "normalized_value": row.get("normalized_value"),
                        "unit_before": _norm(row.get("unit_before")),
                        "unit_after": _norm(updated_row.get("unit")),
                        "metric_code_before": _norm(row.get("metric_code")),
                        "metric_code_after": _norm(updated_row.get("metric_code")),
                        "decision_before": "review_required_preview",
                        "decision_after": _norm(updated_row.get("split_decision")),
                        "risk_tags_before": _norm(row.get("risk_tags_after")),
                        "risk_tags_after": _norm(updated_row.get("risk_tags_after")),
                        "replay_instruction_id": instruction_id,
                        "replay_reason": instruction_type,
                        "provenance": _norm(row.get("provenance_json")),
                    }
                )
            review_after_df = review_after_df[~mask].copy()
            review_after_df.reset_index(drop=True, inplace=True)

        reduction_rows.append(
            {
                "instruction_id": instruction_id,
                "case_id": case_id,
                "instruction_type": instruction_type,
                "candidates_affected": candidates_affected,
                "trusted_gain": trusted_gain,
                "review_reduction": review_reduction,
                "rejected_or_out_of_scope_count": rejected_gain,
                "notes": "sandbox_replay_applied" if candidates_affected else "no_candidates_affected",
            }
        )

    trusted_after_df = trusted_after_df.drop(columns=["normalized_label"], errors="ignore").reset_index(drop=True)
    review_after_df = review_after_df.drop(columns=["normalized_label"], errors="ignore").reset_index(drop=True)
    rejected_after_df = rejected_after_df.drop(columns=["normalized_label"], errors="ignore").reset_index(drop=True)
    return (
        replay_instruction_inventory_df,
        pd.DataFrame(diff_rows).fillna(""),
        trusted_after_df,
        review_after_df,
        rejected_after_df,
        pd.DataFrame(reduction_rows).fillna(""),
    )


def build_remaining_review_burden(review_after_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "review_reason",
        "candidate_count",
        "unique_table_count",
        "unique_label_count",
        "sample_labels",
        "recommended_next_action",
    ]
    if review_after_df.empty:
        return pd.DataFrame(columns=columns)
    temp = review_after_df.copy()
    temp["review_reason"] = temp["split_reason"].map(_norm)
    rows: List[Dict[str, Any]] = []
    for review_reason, group in temp.groupby("review_reason", dropna=False):
        labels = [label for label in group["raw_metric_name"].astype(str).tolist() if label]
        recommended_action = "manual_review"
        joined_reason = _norm(review_reason)
        if "UNKNOWN_METRIC_CODE" in joined_reason:
            recommended_action = "expand_semantic_batch_carefully"
        elif "INVALID_YEAR" in joined_reason:
            recommended_action = "deterministic_year_repair_or_manual_review"
        elif "SEMANTIC_REPLAY" in joined_reason:
            recommended_action = "manual_review_after_replay"
        rows.append(
            {
                "review_reason": review_reason,
                "candidate_count": int(len(group)),
                "unique_table_count": int(group["table_asset_id"].astype(str).nunique()),
                "unique_label_count": int(group["raw_metric_name"].astype(str).nunique()),
                "sample_labels": "|".join(list(dict.fromkeys(labels))[:5]),
                "recommended_next_action": recommended_action,
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values(["candidate_count", "review_reason"], ascending=[False, True]).reset_index(drop=True)
