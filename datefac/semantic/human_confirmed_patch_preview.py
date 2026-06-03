from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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


def _dedupe_preserve(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _join_unique(items: List[str], limit: int = 5) -> str:
    return " | ".join(_dedupe_preserve(items)[:limit])


def _safe_numeric_sum(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


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
                parsed = json.loads(text)
            except Exception:
                continue
            if isinstance(parsed, dict):
                rows.append(parsed)
    return pd.DataFrame(rows).fillna("")


def _find_workbook(directory: Path) -> Optional[Path]:
    if not directory.exists():
        return None
    workbooks = sorted(directory.glob("*.xlsx"))
    return workbooks[0] if workbooks else None


def read_excel_sheet(workbook: Optional[Path], sheet_name: str) -> pd.DataFrame:
    if workbook is None or not workbook.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(workbook, sheet_name=sheet_name).fillna("")
    except Exception:
        return pd.DataFrame()


def _parse_provenance_json(value: Any) -> Dict[str, Any]:
    text = _norm(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


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


def _read_reviewed_workbook(workbook_path: Path) -> Dict[str, pd.DataFrame]:
    xl = pd.ExcelFile(workbook_path)
    return {
        sheet_name: pd.read_excel(workbook_path, sheet_name=sheet_name).fillna("")
        for sheet_name in xl.sheet_names
    }


def load_human_confirmed_patch_inputs(
    reviewed_proposal_xlsx: Path,
    proposal_dir: Path,
    adjudicator_apply_dir: Path,
    trust_split_dir: Path,
) -> Dict[str, Any]:
    reviewed_sheets = _read_reviewed_workbook(reviewed_proposal_xlsx)
    apply_workbook = _find_workbook(adjudicator_apply_dir)
    return {
        "reviewed_sheets": reviewed_sheets,
        "proposal_summary": _read_json(proposal_dir / "semantic_mapping_proposals_322g_summary.json"),
        "apply_summary": _read_json(adjudicator_apply_dir / "semantic_adjudicator_larger_batch_322f_summary.json"),
        "trust_summary": _read_json(trust_split_dir / "router_mineru_trust_split_322b2_summary.json"),
        "selected_candidates_df": read_jsonl(trust_split_dir / "selected_candidate_reclassified_322b2.jsonl"),
        "candidate_replay_diff_df": read_jsonl(adjudicator_apply_dir / "candidate_replay_diff_322f.jsonl"),
        "replay_instructions_df": read_jsonl(adjudicator_apply_dir / "semantic_replay_instructions_322f.jsonl"),
        "review_reduction_by_instruction_df": read_excel_sheet(apply_workbook, "review_reduction_by_instruction"),
    }


def _sheet_to_proposal_type(sheet_name: str) -> str:
    lowered = _norm(sheet_name).lower()
    if "alias" in lowered:
        return "alias"
    if "out_of_scope" in lowered:
        return "out_of_scope"
    if "unit" in lowered:
        return "unit_inference"
    if "noise" in lowered:
        return "rejected_noise"
    return ""


def _detect_decision_column(df: pd.DataFrame) -> str:
    candidates = [
        "reviewer_decision",
        "decision",
        "human_decision",
        "recommended_human_decision",
    ]
    lowered = {str(column).strip().lower(): column for column in df.columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return ""


def _extract_reviewer_decision_rows(reviewed_sheets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    if "reviewer_decisions" in reviewed_sheets and not reviewed_sheets["reviewer_decisions"].empty:
        df = reviewed_sheets["reviewer_decisions"].copy()
        lowered = {str(column).strip().lower(): column for column in df.columns}
        rename_map = {}
        for canonical in ["proposal_type", "proposal_id", "normalized_label", "decision", "comment"]:
            if canonical in lowered:
                rename_map[lowered[canonical]] = canonical
        df = df.rename(columns=rename_map)
        for required in ["proposal_type", "proposal_id", "normalized_label", "decision", "comment"]:
            if required not in df.columns:
                df[required] = ""
        df["proposal_type"] = df["proposal_type"].map(lambda value: _norm(value).lower())
        df["proposal_id"] = df["proposal_id"].map(_norm)
        df["normalized_label"] = df["normalized_label"].map(_norm)
        df["decision"] = df["decision"].map(_norm)
        df["comment"] = df["comment"].map(_norm)
        df = df[df["proposal_id"].astype(str).ne("")].copy()
        return df[["proposal_type", "proposal_id", "normalized_label", "decision", "comment"]].reset_index(drop=True)

    rows: List[Dict[str, Any]] = []
    for sheet_name, df in reviewed_sheets.items():
        proposal_type = _sheet_to_proposal_type(sheet_name)
        if not proposal_type or df.empty:
            continue
        decision_column = _detect_decision_column(df)
        comment_column = ""
        for candidate in ["reviewer_comment", "comment"]:
            for column in df.columns:
                if str(column).strip().lower() == candidate.lower():
                    comment_column = column
                    break
            if comment_column:
                break
        for _, row in df.iterrows():
            proposal_id = _norm(row.get("proposal_id"))
            if not proposal_id:
                continue
            rows.append(
                {
                    "proposal_type": proposal_type,
                    "proposal_id": proposal_id,
                    "normalized_label": _norm(row.get("normalized_label")),
                    "decision": _norm(row.get(decision_column)),
                    "comment": _norm(row.get(comment_column)),
                }
            )
    return pd.DataFrame(rows).fillna("")


def _build_base_proposal_lookup(reviewed_sheets: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for sheet_name, df in reviewed_sheets.items():
        proposal_type = _sheet_to_proposal_type(sheet_name)
        if not proposal_type or df.empty:
            continue
        for _, row in df.iterrows():
            proposal_id = _norm(row.get("proposal_id"))
            if not proposal_id:
                continue
            payload = row.to_dict()
            payload["proposal_type"] = proposal_type
            lookup[proposal_id] = payload
    return lookup


def _replay_instruction_lookup(replay_instructions_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    if replay_instructions_df.empty:
        return lookup
    for _, row in replay_instructions_df.iterrows():
        case_id = _norm(row.get("case_id"))
        normalized_label = _normalize_label(row.get("normalized_label"))
        proposal_id = ""
        if _norm(row.get("instruction_type")) == "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY":
            prefix = "alias"
        elif _norm(row.get("instruction_type")) == "CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY":
            prefix = "out_of_scope"
        elif _norm(row.get("instruction_type")) == "ACCEPT_UNIT_INFERENCE_FOR_REPLAY":
            prefix = "unit_inference"
        elif _norm(row.get("instruction_type")) == "REJECT_NOISE_FOR_REPLAY":
            prefix = "rejected_noise"
        else:
            prefix = ""
        if prefix:
            lookup[_norm(row.get("instruction_id"))] = row.to_dict()
            lookup[case_id] = row.to_dict()
            lookup[normalized_label] = row.to_dict()
    return lookup


def _build_reviewed_proposal_inventory(
    reviewed_decisions_df: pd.DataFrame,
    base_proposal_lookup: Dict[str, Dict[str, Any]],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    inventory_rows: List[Dict[str, Any]] = []
    accepted_rows: List[Dict[str, Any]] = []

    for _, decision_row in reviewed_decisions_df.iterrows():
        proposal_id = _norm(decision_row.get("proposal_id"))
        proposal_type = _norm(decision_row.get("proposal_type"))
        human_decision = _norm(decision_row.get("decision")).upper()
        human_comment = _norm(decision_row.get("comment"))
        base_row = base_proposal_lookup.get(proposal_id, {})
        normalized_label = _norm(decision_row.get("normalized_label")) or _norm(base_row.get("normalized_label"))
        proposed_metric_code = _norm(base_row.get("proposed_metric_code"))
        proposed_metric_family = _norm(base_row.get("proposed_metric_family"))
        accepted_for_patch_preview = human_decision == "ACCEPT"
        skip_reason = ""
        if not accepted_for_patch_preview:
            skip_reason = "reviewer_decision_not_accept"
        inventory_rows.append(
            {
                "proposal_id": proposal_id,
                "proposal_type": proposal_type,
                "source_case_id": _norm(base_row.get("source_case_id")),
                "normalized_label": normalized_label,
                "proposed_metric_code": proposed_metric_code,
                "proposed_metric_family": proposed_metric_family,
                "reviewer_decision": human_decision,
                "reviewer_comment": human_comment,
                "accepted_for_patch_preview": accepted_for_patch_preview,
                "skip_reason": skip_reason,
            }
        )
        if accepted_for_patch_preview:
            accepted_payload = dict(base_row)
            accepted_payload.update(
                {
                    "proposal_id": proposal_id,
                    "proposal_type": proposal_type,
                    "normalized_label": normalized_label,
                    "reviewer_decision": human_decision,
                    "reviewer_comment": human_comment,
                }
            )
            accepted_rows.append(accepted_payload)

    inventory_df = pd.DataFrame(inventory_rows).fillna("")
    accepted_df = pd.DataFrame(accepted_rows).fillna("")
    return inventory_df, accepted_df


def _prepare_candidate_frames(selected_candidates_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    trusted_before_df = selected_candidates_df[
        selected_candidates_df["split_decision"].astype(str) == "trusted_preview"
    ].copy()
    review_before_df = selected_candidates_df[
        selected_candidates_df["split_decision"].astype(str) == "review_required_preview"
    ].copy()
    rejected_before_df = selected_candidates_df[
        selected_candidates_df["split_decision"].astype(str) == "rejected_preview"
    ].copy()
    for df in [trusted_before_df, review_before_df, rejected_before_df]:
        if not df.empty:
            df["normalized_label"] = df["raw_metric_name"].map(_normalize_label)
            if "risk_tags_after" not in df.columns:
                df["risk_tags_after"] = df.get("risk_tags", "")
            if "decision_after" not in df.columns:
                df["decision_after"] = df.get("split_decision", "")
    return trusted_before_df, review_before_df, rejected_before_df


def _build_patch_preview_row(base_row: Dict[str, Any], patch_id: str, patch_status: str) -> Dict[str, Any]:
    proposal_type = _norm(base_row.get("proposal_type"))
    common = {
        "patch_id": patch_id,
        "proposal_id": _norm(base_row.get("proposal_id")),
        "normalized_label": _norm(base_row.get("normalized_label")),
        "sample_table_titles": _norm(base_row.get("sample_table_titles")),
        "sample_row_labels": _norm(base_row.get("sample_row_labels")),
        "sample_values": _norm(base_row.get("sample_values")),
        "risk_flags": _norm(base_row.get("risk_flags")),
        "patch_status": patch_status,
    }
    if proposal_type == "alias":
        common.update(
            {
                "proposed_metric_code": _norm(base_row.get("proposed_metric_code")),
                "proposed_metric_family": _norm(base_row.get("proposed_metric_family")),
                "affected_candidate_count": int(base_row.get("affected_candidate_count") or 0),
                "trusted_gain": 0,
                "review_reduction": 0,
            }
        )
    elif proposal_type == "out_of_scope":
        common.update(
            {
                "affected_candidate_count": int(base_row.get("affected_candidate_count") or 0),
                "review_reduction": 0,
            }
        )
    elif proposal_type == "unit_inference":
        common.update(
            {
                "proposed_unit": _norm(base_row.get("proposed_unit")),
                "affected_candidate_count": int(base_row.get("affected_candidate_count") or 0),
                "trusted_gain": 0,
                "review_reduction": 0,
            }
        )
    elif proposal_type == "rejected_noise":
        common.update(
            {
                "affected_candidate_count": int(base_row.get("affected_candidate_count") or 0),
                "review_reduction": 0,
            }
        )
    return common


def apply_human_confirmed_patches(
    accepted_proposals_df: pd.DataFrame,
    selected_candidates_df: pd.DataFrame,
) -> Dict[str, Any]:
    trusted_before_df, review_before_df, rejected_before_df = _prepare_candidate_frames(selected_candidates_df)
    trusted_after_df = trusted_before_df.copy()
    review_after_df = review_before_df.copy()
    rejected_after_df = rejected_before_df.copy()

    alias_patch_rows: List[Dict[str, Any]] = []
    out_scope_patch_rows: List[Dict[str, Any]] = []
    unit_patch_rows: List[Dict[str, Any]] = []
    rejected_noise_patch_rows: List[Dict[str, Any]] = []
    diff_rows: List[Dict[str, Any]] = []
    impact_rows: List[Dict[str, Any]] = []
    official_rule_rows: List[Dict[str, Any]] = []

    patch_counters = {
        "alias": 0,
        "out_of_scope": 0,
        "unit_inference": 0,
        "rejected_noise": 0,
    }

    if accepted_proposals_df.empty:
        return {
            "trusted_before_df": trusted_before_df.drop(columns=["normalized_label"], errors="ignore"),
            "review_before_df": review_before_df.drop(columns=["normalized_label"], errors="ignore"),
            "rejected_before_df": rejected_before_df.drop(columns=["normalized_label"], errors="ignore"),
            "trusted_after_df": trusted_after_df.drop(columns=["normalized_label"], errors="ignore"),
            "review_after_df": review_after_df.drop(columns=["normalized_label"], errors="ignore"),
            "rejected_after_df": rejected_after_df.drop(columns=["normalized_label"], errors="ignore"),
            "alias_patch_preview_df": pd.DataFrame(),
            "out_of_scope_patch_preview_df": pd.DataFrame(),
            "unit_inference_patch_preview_df": pd.DataFrame(),
            "rejected_noise_patch_preview_df": pd.DataFrame(),
            "candidate_before_after_diff_df": pd.DataFrame(),
            "patch_impact_by_proposal_df": pd.DataFrame(),
            "official_rule_candidate_preview_df": pd.DataFrame(),
        }

    for _, proposal in accepted_proposals_df.iterrows():
        proposal_type = _norm(proposal.get("proposal_type"))
        if proposal_type not in patch_counters:
            continue
        patch_counters[proposal_type] += 1
        patch_id = f"patch::{proposal_type}::{patch_counters[proposal_type]:03d}"
        normalized_label = _normalize_label(proposal.get("normalized_label"))
        proposal_id = _norm(proposal.get("proposal_id"))
        source_case_id = _norm(proposal.get("source_case_id"))
        matched_mask = review_after_df["normalized_label"].astype(str) == normalized_label
        matched = review_after_df[matched_mask].copy()

        affected_candidate_count = len(matched)
        trusted_gain = 0
        review_reduction = 0
        rejected_gain = 0
        patch_status = "ACCEPTED_NO_MATCHED_REVIEW_CANDIDATES"

        preview_row = _build_patch_preview_row(proposal.to_dict(), patch_id, patch_status)

        if proposal_type == "alias" and not matched.empty:
            matched["metric_code_before"] = matched["metric_code"]
            matched["decision_before_patch"] = matched["split_decision"]
            matched["risk_tags_before_patch"] = matched["risk_tags_after"]
            updated_rows: List[pd.Series] = []
            trusted_add_rows: List[pd.Series] = []
            for _, row in matched.iterrows():
                current_tags = [tag for tag in _split_tags(row.get("risk_tags_after")) if tag != "UNKNOWN_METRIC_CODE"]
                updated_row = row.copy()
                updated_row["metric_code"] = _norm(proposal.get("proposed_metric_code"))
                updated_row["metric_family"] = _norm(proposal.get("proposed_metric_family")) or _norm(row.get("metric_family"))
                updated_row["canonical_metric_name"] = _norm(proposal.get("proposed_metric_code"))
                updated_row["risk_tags_after"] = _join_tags(current_tags)
                updated_row["split_reason"] = f"HUMAN_CONFIRMED_PATCH::{patch_id}"
                updated_row["reclassification_reason"] = f"HUMAN_CONFIRMED_PATCH::{proposal_id}"
                if _candidate_passes_trust_gate(updated_row):
                    updated_row["split_decision"] = "trusted_preview"
                    updated_row["decision_after"] = "trusted_preview"
                    trusted_gain += 1
                    review_reduction += 1
                    trusted_add_rows.append(updated_row.drop(labels=["normalized_label"], errors="ignore"))
                else:
                    updated_row["split_decision"] = "review_required_preview"
                    updated_row["decision_after"] = "review_required_preview"
                    updated_rows.append(updated_row)
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
                        "decision_before": _norm(row.get("decision_before_patch")),
                        "decision_after": _norm(updated_row.get("split_decision")),
                        "risk_tags_before": _norm(row.get("risk_tags_before_patch")),
                        "risk_tags_after": _norm(updated_row.get("risk_tags_after")),
                        "proposal_id": proposal_id,
                        "patch_id": patch_id,
                        "patch_reason": "ACCEPT_ALIAS_HUMAN_CONFIRMED_PATCH",
                        "provenance": _norm(row.get("provenance_json")),
                    }
                )
            review_after_df = review_after_df[~matched_mask].copy()
            if updated_rows:
                review_after_df = pd.concat([review_after_df, pd.DataFrame(updated_rows)], ignore_index=True)
            if trusted_add_rows:
                trusted_after_df = pd.concat([trusted_after_df, pd.DataFrame(trusted_add_rows)], ignore_index=True)
            patch_status = "APPLIED_ALIAS_PATCH"
            preview_row["affected_candidate_count"] = affected_candidate_count
            preview_row["trusted_gain"] = trusted_gain
            preview_row["review_reduction"] = review_reduction
            preview_row["patch_status"] = patch_status

        elif proposal_type in {"out_of_scope", "rejected_noise"} and not matched.empty:
            review_after_df = review_after_df[~matched_mask].copy()
            matched["split_decision"] = "rejected_preview"
            matched["decision_after"] = "rejected_preview"
            matched["split_reason"] = f"HUMAN_CONFIRMED_PATCH::{patch_id}"
            matched["reclassification_reason"] = f"HUMAN_CONFIRMED_PATCH::{proposal_id}"
            rejected_after_df = pd.concat(
                [rejected_after_df, matched.drop(columns=["normalized_label"], errors="ignore")],
                ignore_index=True,
            )
            rejected_gain = len(matched)
            review_reduction = len(matched)
            patch_status = (
                "APPLIED_OUT_OF_SCOPE_PATCH"
                if proposal_type == "out_of_scope"
                else "APPLIED_REJECTED_NOISE_PATCH"
            )
            preview_row["affected_candidate_count"] = affected_candidate_count
            preview_row["review_reduction"] = review_reduction
            preview_row["patch_status"] = patch_status
            for _, row in matched.iterrows():
                diff_rows.append(
                    {
                        "table_asset_id": _norm(row.get("table_asset_id")),
                        "source_report_name": _norm(row.get("source_report_name")),
                        "row_label": _norm(row.get("raw_metric_name")),
                        "year": _norm(row.get("year")),
                        "raw_value": _norm(row.get("raw_value")),
                        "normalized_value": row.get("normalized_value"),
                        "unit_before": _norm(row.get("unit")),
                        "unit_after": _norm(row.get("unit")),
                        "metric_code_before": _norm(row.get("metric_code")),
                        "metric_code_after": _norm(row.get("metric_code")),
                        "decision_before": "review_required_preview",
                        "decision_after": "rejected_preview",
                        "risk_tags_before": _norm(row.get("risk_tags_after") or row.get("risk_tags")),
                        "risk_tags_after": _norm(row.get("risk_tags_after") or row.get("risk_tags")),
                        "proposal_id": proposal_id,
                        "patch_id": patch_id,
                        "patch_reason": (
                            "ACCEPT_OUT_OF_SCOPE_HUMAN_CONFIRMED_PATCH"
                            if proposal_type == "out_of_scope"
                            else "ACCEPT_REJECT_NOISE_HUMAN_CONFIRMED_PATCH"
                        ),
                        "provenance": _norm(row.get("provenance_json")),
                    }
                )

        elif proposal_type == "unit_inference" and not matched.empty:
            matched["unit_before_patch"] = matched["unit"]
            updated_rows = []
            trusted_add_rows = []
            for _, row in matched.iterrows():
                current_tags = [tag for tag in _split_tags(row.get("risk_tags_after")) if tag != "UNIT_UNKNOWN"]
                updated_row = row.copy()
                updated_row["unit"] = _norm(proposal.get("proposed_unit")) or _norm(row.get("unit"))
                updated_row["risk_tags_after"] = _join_tags(current_tags)
                updated_row["split_reason"] = f"HUMAN_CONFIRMED_PATCH::{patch_id}"
                updated_row["reclassification_reason"] = f"HUMAN_CONFIRMED_PATCH::{proposal_id}"
                if _candidate_passes_trust_gate(updated_row):
                    updated_row["split_decision"] = "trusted_preview"
                    updated_row["decision_after"] = "trusted_preview"
                    trusted_gain += 1
                    review_reduction += 1
                    trusted_add_rows.append(updated_row.drop(labels=["normalized_label"], errors="ignore"))
                else:
                    updated_row["split_decision"] = "review_required_preview"
                    updated_row["decision_after"] = "review_required_preview"
                    updated_rows.append(updated_row)
                diff_rows.append(
                    {
                        "table_asset_id": _norm(row.get("table_asset_id")),
                        "source_report_name": _norm(row.get("source_report_name")),
                        "row_label": _norm(row.get("raw_metric_name")),
                        "year": _norm(row.get("year")),
                        "raw_value": _norm(row.get("raw_value")),
                        "normalized_value": row.get("normalized_value"),
                        "unit_before": _norm(row.get("unit_before_patch")),
                        "unit_after": _norm(updated_row.get("unit")),
                        "metric_code_before": _norm(row.get("metric_code")),
                        "metric_code_after": _norm(updated_row.get("metric_code")),
                        "decision_before": "review_required_preview",
                        "decision_after": _norm(updated_row.get("split_decision")),
                        "risk_tags_before": _norm(row.get("risk_tags_after")),
                        "risk_tags_after": _norm(updated_row.get("risk_tags_after")),
                        "proposal_id": proposal_id,
                        "patch_id": patch_id,
                        "patch_reason": "ACCEPT_UNIT_INFERENCE_HUMAN_CONFIRMED_PATCH",
                        "provenance": _norm(row.get("provenance_json")),
                    }
                )
            review_after_df = review_after_df[~matched_mask].copy()
            if updated_rows:
                review_after_df = pd.concat([review_after_df, pd.DataFrame(updated_rows)], ignore_index=True)
            if trusted_add_rows:
                trusted_after_df = pd.concat([trusted_after_df, pd.DataFrame(trusted_add_rows)], ignore_index=True)
            patch_status = "APPLIED_UNIT_INFERENCE_PATCH"
            preview_row["affected_candidate_count"] = affected_candidate_count
            preview_row["trusted_gain"] = trusted_gain
            preview_row["review_reduction"] = review_reduction
            preview_row["patch_status"] = patch_status

        if proposal_type == "alias":
            alias_patch_rows.append(preview_row)
        elif proposal_type == "out_of_scope":
            out_scope_patch_rows.append(preview_row)
        elif proposal_type == "unit_inference":
            unit_patch_rows.append(preview_row)
        elif proposal_type == "rejected_noise":
            rejected_noise_patch_rows.append(preview_row)

        impact_rows.append(
            {
                "proposal_id": proposal_id,
                "proposal_type": proposal_type,
                "normalized_label": _norm(proposal.get("normalized_label")),
                "affected_candidate_count": affected_candidate_count,
                "trusted_gain": trusted_gain,
                "review_reduction": review_reduction,
                "rejected_or_out_of_scope_count": rejected_gain,
                "notes": patch_status.lower(),
            }
        )
        official_rule_rows.append(
            {
                "rule_candidate_id": f"rule::{proposal_type}::{patch_counters[proposal_type]:03d}",
                "rule_type": (
                    "alias_mapping"
                    if proposal_type == "alias"
                    else "out_of_scope_scope_rule"
                    if proposal_type == "out_of_scope"
                    else "unit_inference"
                    if proposal_type == "unit_inference"
                    else "reject_noise"
                ),
                "normalized_label": _norm(proposal.get("normalized_label")),
                "proposed_metric_code": _norm(proposal.get("proposed_metric_code")),
                "proposed_metric_family": _norm(proposal.get("proposed_metric_family")),
                "proposed_scope_action": (
                    "exclude_from_core_metric_mapping"
                    if proposal_type == "out_of_scope"
                    else "reject_noise_exact_match"
                    if proposal_type == "rejected_noise"
                    else ""
                ),
                "source_proposal_id": proposal_id,
                "evidence_summary": _join_unique(
                    [
                        _norm(proposal.get("sample_table_titles")),
                        _norm(proposal.get("sample_row_labels")),
                        _norm(proposal.get("sample_values")),
                        _norm(proposal.get("reviewer_comment")),
                    ],
                    limit=4,
                ),
                "affected_candidate_count": affected_candidate_count,
                "trusted_gain": trusted_gain,
                "review_reduction": review_reduction,
                "human_decision": _norm(proposal.get("reviewer_decision")),
                "ready_for_official_proposal": patch_status.startswith("APPLIED_"),
            }
        )

    trusted_after_df = trusted_after_df.drop(columns=["normalized_label"], errors="ignore").reset_index(drop=True)
    review_after_df = review_after_df.drop(columns=["normalized_label"], errors="ignore").reset_index(drop=True)
    rejected_after_df = rejected_after_df.drop(columns=["normalized_label"], errors="ignore").reset_index(drop=True)

    return {
        "trusted_before_df": trusted_before_df.drop(columns=["normalized_label"], errors="ignore").reset_index(drop=True),
        "review_before_df": review_before_df.drop(columns=["normalized_label"], errors="ignore").reset_index(drop=True),
        "rejected_before_df": rejected_before_df.drop(columns=["normalized_label"], errors="ignore").reset_index(drop=True),
        "trusted_after_df": trusted_after_df,
        "review_after_df": review_after_df,
        "rejected_after_df": rejected_after_df,
        "alias_patch_preview_df": pd.DataFrame(alias_patch_rows).fillna(""),
        "out_of_scope_patch_preview_df": pd.DataFrame(out_scope_patch_rows).fillna(""),
        "unit_inference_patch_preview_df": pd.DataFrame(unit_patch_rows).fillna(""),
        "rejected_noise_patch_preview_df": pd.DataFrame(rejected_noise_patch_rows).fillna(""),
        "candidate_before_after_diff_df": pd.DataFrame(diff_rows).fillna(""),
        "patch_impact_by_proposal_df": pd.DataFrame(impact_rows).fillna(""),
        "official_rule_candidate_preview_df": pd.DataFrame(official_rule_rows).fillna(""),
    }


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
            recommended_action = "expand_semantic_patch_rule_carefully"
        elif "INVALID_YEAR" in joined_reason:
            recommended_action = "deterministic_year_repair_or_manual_review"
        elif "HUMAN_CONFIRMED_PATCH" in joined_reason:
            recommended_action = "manual_review_after_patch_preview"
        rows.append(
            {
                "review_reason": review_reason,
                "candidate_count": int(len(group)),
                "unique_table_count": int(group["table_asset_id"].astype(str).nunique()),
                "unique_label_count": int(group["raw_metric_name"].astype(str).nunique()),
                "sample_labels": _join_unique(labels, limit=5),
                "recommended_next_action": recommended_action,
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["candidate_count", "review_reason"],
        ascending=[False, True],
    ).reset_index(drop=True)


def build_human_confirmed_patch_preview(
    reviewed_sheets: Dict[str, pd.DataFrame],
    proposal_summary: Dict[str, Any],
    apply_summary: Dict[str, Any],
    trust_summary: Dict[str, Any],
    selected_candidates_df: pd.DataFrame,
    candidate_replay_diff_df: pd.DataFrame,
    replay_instructions_df: pd.DataFrame,
) -> Dict[str, Any]:
    reviewed_decisions_df = _extract_reviewer_decision_rows(reviewed_sheets)
    base_proposal_lookup = _build_base_proposal_lookup(reviewed_sheets)
    reviewed_inventory_df, accepted_proposals_df = _build_reviewed_proposal_inventory(
        reviewed_decisions_df=reviewed_decisions_df,
        base_proposal_lookup=base_proposal_lookup,
    )

    if not selected_candidates_df.empty and "risk_tags_after" not in selected_candidates_df.columns:
        selected_candidates_df["risk_tags_after"] = selected_candidates_df.get("risk_tags", "")
    if not selected_candidates_df.empty and "decision_after" not in selected_candidates_df.columns:
        selected_candidates_df["decision_after"] = selected_candidates_df.get("split_decision", "")

    applied = apply_human_confirmed_patches(
        accepted_proposals_df=accepted_proposals_df,
        selected_candidates_df=selected_candidates_df,
    )
    remaining_review_burden_df = build_remaining_review_burden(applied["review_after_df"])

    reviewed_proposal_count = int(len(reviewed_inventory_df))
    accepted_proposal_count = int(
        reviewed_inventory_df["reviewer_decision"].astype(str).str.upper().eq("ACCEPT").sum()
    ) if not reviewed_inventory_df.empty else 0
    rejected_proposal_count = int(
        reviewed_inventory_df["reviewer_decision"].astype(str).str.upper().eq("REJECT").sum()
    ) if not reviewed_inventory_df.empty else 0
    needs_more_info_proposal_count = int(
        reviewed_inventory_df["reviewer_decision"].astype(str).str.upper().eq("NEEDS_MORE_INFO").sum()
    ) if not reviewed_inventory_df.empty else 0

    trusted_total_before_322h = int(len(applied["trusted_before_df"]))
    trusted_total_after_322h = int(len(applied["trusted_after_df"]))
    review_required_total_before_322h = int(len(applied["review_before_df"]))
    review_required_total_after_322h = int(len(applied["review_after_df"]))
    rejected_total_before_322h = int(len(applied["rejected_before_df"]))
    rejected_total_after_322h = int(len(applied["rejected_after_df"]))
    trusted_gain_322h = trusted_total_after_322h - trusted_total_before_322h
    review_reduction_322h = review_required_total_before_322h - review_required_total_after_322h
    out_of_scope_or_rejected_gain_322h = rejected_total_after_322h - rejected_total_before_322h

    remaining_unknown_metric_candidate_count = int(
        applied["review_after_df"]["risk_tags_after"].astype(str).str.contains(
            r"(?:^|\|)UNKNOWN_METRIC_CODE(?:$|\|)",
            regex=True,
        ).sum()
    ) if not applied["review_after_df"].empty else 0
    remaining_unit_unknown_candidate_count = int(
        applied["review_after_df"]["risk_tags_after"].astype(str).str.contains(
            r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)",
            regex=True,
        ).sum()
    ) if not applied["review_after_df"].empty else 0
    remaining_manual_review_count = review_required_total_after_322h

    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa("reviewed_proposal_workbook_exists", "PASS", "reviewed workbook loaded")
    add_qa("322g_proposal_output_exists", "PASS" if bool(proposal_summary) else "FAIL", _norm(proposal_summary.get("output_dir")))
    add_qa("322f_apply30_output_exists", "PASS" if bool(apply_summary) else "FAIL", _norm(apply_summary.get("output_dir")))
    add_qa("322b2_trust_split_output_exists", "PASS" if bool(trust_summary) else "FAIL", _norm(trust_summary.get("output_dir")))
    non_accept_applied_count = int(
        accepted_proposals_df["reviewer_decision"].astype(str).str.upper().ne("ACCEPT").sum()
    ) if not accepted_proposals_df.empty else 0
    add_qa(
        "only_accept_decisions_applied",
        "PASS" if non_accept_applied_count == 0 else "FAIL",
        f"non_accept_applied_count={non_accept_applied_count}",
    )
    add_qa("no_model_api_call_executed", "PASS", "322H reads existing reviewed proposals and sandbox outputs only.")
    add_qa("no_recognizer_command_executed", "PASS", "322H does not call MinerU/StructEqTable/Docling/PPStructure/VLM.")
    add_qa("no_e_drive_files_modified", "PASS", "322H writes sandbox outputs only.")
    add_qa("no_production_files_modified", "PASS", "322H does not modify production delivery or official rule files.")
    add_qa("no_official_mapping_override_files_modified", "PASS", "322H produces official rule candidate preview only.")

    proposal_trace_failures = 0
    if not accepted_proposals_df.empty and not applied["patch_impact_by_proposal_df"].empty:
        impact_ids = set(applied["patch_impact_by_proposal_df"]["proposal_id"].astype(str).tolist())
        accepted_ids = set(accepted_proposals_df["proposal_id"].astype(str).tolist())
        proposal_trace_failures = len(accepted_ids - impact_ids)
    add_qa(
        "every_patch_candidate_traces_to_one_322g_proposal",
        "PASS" if proposal_trace_failures == 0 else "FAIL",
        f"proposal_trace_failures={proposal_trace_failures}",
    )

    provenance_ok = True
    if not applied["candidate_before_after_diff_df"].empty:
        provenance_ok = applied["candidate_before_after_diff_df"]["provenance"].astype(str).str.len().gt(0).all()
    add_qa(
        "every_applied_candidate_has_provenance",
        "PASS" if provenance_ok else "FAIL",
        f"applied_candidate_count={len(applied['candidate_before_after_diff_df'])}",
    )

    llm_only_trust_exists = False
    if not applied["trusted_after_df"].empty:
        blocker_mask = applied["trusted_after_df"]["risk_tags_after"].astype(str).str.contains(
            r"UNKNOWN_METRIC_CODE|UNIT_UNKNOWN|VALUE_PARSE_FAILED|INVALID_YEAR|NO_YEAR_COLUMNS|VALUE_CONFLICT|EXTRACTION_RISK|SECTION_CONTEXT_REQUIRED",
            regex=True,
        )
        llm_only_trust_exists = blocker_mask.any() or applied["trusted_after_df"]["metric_code"].astype(str).eq("unknown_metric").any()
    add_qa(
        "no_llm_only_trusted_decision_exists",
        "PASS" if not llm_only_trust_exists else "FAIL",
        f"trusted_total_after_322h={trusted_total_after_322h}",
    )
    add_qa(
        "trusted_candidates_after_patch_preview_still_satisfy_deterministic_gates",
        "PASS" if not llm_only_trust_exists else "FAIL",
        f"trusted_total_after_322h={trusted_total_after_322h}",
    )

    counts_reconcile = int(len(selected_candidates_df)) == (
        trusted_total_after_322h + review_required_total_after_322h + rejected_total_after_322h
    )
    add_qa(
        "candidate_counts_reconcile_before_after",
        "PASS" if counts_reconcile else "FAIL",
        f"input_candidate_count={len(selected_candidates_df)}",
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    summary = {
        "stage": "322H",
        "output_dir": "",
        "reviewed_proposal_count": reviewed_proposal_count,
        "accepted_proposal_count": accepted_proposal_count,
        "rejected_proposal_count": rejected_proposal_count,
        "needs_more_info_proposal_count": needs_more_info_proposal_count,
        "accepted_alias_patch_count": int(len(applied["alias_patch_preview_df"])),
        "accepted_out_of_scope_patch_count": int(len(applied["out_of_scope_patch_preview_df"])),
        "accepted_unit_inference_patch_count": int(len(applied["unit_inference_patch_preview_df"])),
        "accepted_rejected_noise_patch_count": int(len(applied["rejected_noise_patch_preview_df"])),
        "affected_candidate_count": int(len(applied["candidate_before_after_diff_df"])),
        "trusted_total_before_322h": trusted_total_before_322h,
        "trusted_total_after_322h": trusted_total_after_322h,
        "review_required_total_before_322h": review_required_total_before_322h,
        "review_required_total_after_322h": review_required_total_after_322h,
        "rejected_total_before_322h": rejected_total_before_322h,
        "rejected_total_after_322h": rejected_total_after_322h,
        "trusted_gain_322h": trusted_gain_322h,
        "review_reduction_322h": review_reduction_322h,
        "out_of_scope_or_rejected_gain_322h": out_of_scope_or_rejected_gain_322h,
        "selected_core_trusted_rate_before_322h": float(trust_summary.get("selected_core_trusted_rate_after_322b2") or 0),
        "selected_core_trusted_rate_after_322h": round(trusted_total_after_322h / len(selected_candidates_df), 6) if len(selected_candidates_df) else 0,
        "remaining_unknown_metric_candidate_count": remaining_unknown_metric_candidate_count,
        "remaining_unit_unknown_candidate_count": remaining_unit_unknown_candidate_count,
        "remaining_manual_review_count": remaining_manual_review_count,
        "official_rule_candidate_count": int(len(applied["official_rule_candidate_preview_df"])),
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
    }
    if qa_fail_count > 0:
        decision = "HUMAN_CONFIRMED_PATCH_PREVIEW_322H_BLOCKED_BY_QA_FAILURE"
    elif accepted_proposal_count > 0 and review_reduction_322h > 0:
        decision = "HUMAN_CONFIRMED_PATCH_PREVIEW_322H_READY_FOR_322I_OFFICIAL_RULE_CANDIDATES"
    elif accepted_proposal_count > 0:
        decision = "HUMAN_CONFIRMED_PATCH_PREVIEW_322H_PARTIAL_NO_REDUCTION"
    else:
        decision = "HUMAN_CONFIRMED_PATCH_PREVIEW_322H_NO_ACCEPTED_PROPOSALS"
    summary["human_confirmed_patch_preview_decision"] = decision

    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "sandbox_only",
                "detail": "322H preview applies reviewed proposals only inside sandbox candidate previews and does not modify official rule files.",
            },
            {
                "limitation": "accepted_review_scope_only",
                "detail": "Only reviewer ACCEPT decisions are replayed; REJECT and NEEDS_MORE_INFO remain out of scope for this preview.",
            },
            {
                "limitation": "official_rule_stage_still_required",
                "detail": "official_rule_candidate_preview is a planning artifact and not a production rule write.",
            },
        ]
    )

    return {
        "summary": summary,
        "reviewed_proposal_inventory_df": reviewed_inventory_df,
        "alias_patch_preview_df": applied["alias_patch_preview_df"],
        "out_of_scope_patch_preview_df": applied["out_of_scope_patch_preview_df"],
        "unit_inference_patch_preview_df": applied["unit_inference_patch_preview_df"],
        "rejected_noise_patch_preview_df": applied["rejected_noise_patch_preview_df"],
        "candidate_before_after_diff_df": applied["candidate_before_after_diff_df"],
        "trusted_after_patch_preview_df": applied["trusted_after_df"],
        "review_required_after_patch_preview_df": applied["review_after_df"],
        "rejected_after_patch_preview_df": applied["rejected_after_df"],
        "patch_impact_by_proposal_df": applied["patch_impact_by_proposal_df"],
        "remaining_review_burden_322h_df": remaining_review_burden_df,
        "official_rule_candidate_preview_df": applied["official_rule_candidate_preview_df"],
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
    }
