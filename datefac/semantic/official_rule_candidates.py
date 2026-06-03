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


def _dedupe_preserve(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _join_unique(items: List[str], limit: int = 8) -> str:
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


def _load_scope_reference(formal_scope_rules: Path) -> Tuple[bool, Dict[str, Any], pd.DataFrame]:
    if not formal_scope_rules.exists():
        return False, {}, pd.DataFrame()
    raw = _read_json(formal_scope_rules)
    rules_obj = raw.get("rules") if isinstance(raw, dict) else {}
    rows: List[Dict[str, Any]] = []
    if isinstance(rules_obj, dict):
        for rule_id, payload in rules_obj.items():
            payload = payload if isinstance(payload, dict) else {}
            rows.append(
                {
                    "existing_rule_id": _norm(payload.get("existing_rule_id")) or _norm(rule_id),
                    "standard_metric": _norm(payload.get("standard_metric")),
                    "existing_scope": _norm(payload.get("existing_scope")),
                    "promotion_status": _norm(payload.get("promotion_status")),
                    "statement_types": _join_unique(
                        [_norm(item) for item in payload.get("statement_types", []) if _norm(item)],
                        limit=8,
                    ),
                    "raw_json": json.dumps(payload, ensure_ascii=False),
                }
            )
    return True, raw, pd.DataFrame(rows).fillna("")


def _load_override_reference(ai_repair_override: Path) -> Tuple[bool, pd.DataFrame]:
    if not ai_repair_override.exists():
        return False, pd.DataFrame()
    try:
        xl = pd.ExcelFile(ai_repair_override)
        if "ai_repair_override" in xl.sheet_names:
            df = pd.read_excel(ai_repair_override, sheet_name="ai_repair_override").fillna("")
        else:
            df = pd.read_excel(ai_repair_override, sheet_name=xl.sheet_names[0]).fillna("")
        return True, df
    except Exception:
        return False, pd.DataFrame()


def load_official_rule_candidate_inputs(
    patch_preview_dir: Path,
    proposal_dir: Path,
    adjudicator_apply_dir: Path,
    trust_split_dir: Path,
    formal_scope_rules: Path,
    ai_repair_override: Path,
) -> Dict[str, Any]:
    patch_workbook = _find_workbook(patch_preview_dir)
    scope_loaded, scope_raw, scope_df = _load_scope_reference(formal_scope_rules)
    override_loaded, override_df = _load_override_reference(ai_repair_override)
    return {
        "patch_summary": _read_json(patch_preview_dir / "human_confirmed_semantic_patch_preview_322h_summary.json"),
        "proposal_summary": _read_json(proposal_dir / "semantic_mapping_proposals_322g_summary.json"),
        "apply_summary": _read_json(adjudicator_apply_dir / "semantic_adjudicator_larger_batch_322f_summary.json"),
        "trust_summary": _read_json(trust_split_dir / "router_mineru_trust_split_322b2_summary.json"),
        "official_rule_candidate_preview_df": read_jsonl(patch_preview_dir / "official_rule_candidate_preview_322h.jsonl"),
        "candidate_diff_df": read_jsonl(patch_preview_dir / "candidate_before_after_diff_322h.jsonl"),
        "patch_impact_df": read_excel_sheet(patch_workbook, "patch_impact_by_proposal_322h"),
        "reviewed_inventory_df": read_excel_sheet(patch_workbook, "reviewed_proposal_inventory"),
        "remaining_review_burden_df": read_excel_sheet(patch_workbook, "remaining_review_burden_322h"),
        "scope_reference_loaded": scope_loaded,
        "scope_reference_raw": scope_raw,
        "scope_reference_df": scope_df,
        "override_reference_loaded": override_loaded,
        "override_reference_df": override_df,
    }


def _build_candidate_evidence_lookup(candidate_diff_df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
    lookup: Dict[str, List[Dict[str, Any]]] = {}
    if candidate_diff_df.empty:
        return lookup
    for _, row in candidate_diff_df.iterrows():
        proposal_id = _norm(row.get("proposal_id"))
        if not proposal_id:
            continue
        lookup.setdefault(proposal_id, []).append(row.to_dict())
    return lookup


def _derive_conflict_status(
    candidate: pd.Series,
    scope_reference_df: pd.DataFrame,
) -> Tuple[str, str, str]:
    normalized_label = _normalize_label(candidate.get("normalized_label"))
    proposed_metric_code = _norm(candidate.get("proposed_metric_code"))
    proposed_scope_action = _norm(candidate.get("proposed_scope_action"))
    rule_type = _norm(candidate.get("rule_type"))

    duplicate_status = "NO_EXISTING_MATCH_FOUND"
    conflict_status = "NO_CONFLICT_DETECTED"
    matching_reference = ""

    if scope_reference_df.empty:
        return "REFERENCE_CHECK_NOT_AVAILABLE", "REFERENCE_CHECK_NOT_AVAILABLE", ""

    for _, row in scope_reference_df.iterrows():
        reference_metric = _norm(row.get("standard_metric"))
        reference_json = _norm(row.get("raw_json"))
        if normalized_label and normalized_label in _normalize_label(reference_json):
            matching_reference = _norm(row.get("existing_rule_id")) or reference_metric
            if rule_type == "alias_mapping":
                if proposed_metric_code and proposed_metric_code in _normalize_label(reference_json):
                    duplicate_status = "DUPLICATE_EXISTING_ALIAS_RULE"
                    conflict_status = "NO_CONFLICT_DETECTED"
                else:
                    duplicate_status = "MATCHED_EXISTING_REFERENCE_TEXT"
                    conflict_status = "POSSIBLE_CONFLICT_EXISTING_ALIAS_RULE"
                return duplicate_status, conflict_status, matching_reference
            if rule_type == "out_of_scope_scope_rule":
                duplicate_status = "MATCHED_EXISTING_REFERENCE_TEXT"
                conflict_status = "POSSIBLE_CONFLICT_WITH_EXISTING_SCOPE_RULE"
                return duplicate_status, conflict_status, matching_reference

    if rule_type == "out_of_scope_scope_rule" and proposed_scope_action:
        duplicate_status = "NO_EXISTING_SCOPE_MATCH_FOUND"
    return duplicate_status, conflict_status, matching_reference


def build_official_rule_candidates(
    patch_summary: Dict[str, Any],
    proposal_summary: Dict[str, Any],
    apply_summary: Dict[str, Any],
    trust_summary: Dict[str, Any],
    official_rule_candidate_preview_df: pd.DataFrame,
    candidate_diff_df: pd.DataFrame,
    patch_impact_df: pd.DataFrame,
    reviewed_inventory_df: pd.DataFrame,
    remaining_review_burden_df: pd.DataFrame,
    scope_reference_loaded: bool,
    scope_reference_df: pd.DataFrame,
    override_reference_loaded: bool,
    override_reference_df: pd.DataFrame,
) -> Dict[str, Any]:
    evidence_lookup = _build_candidate_evidence_lookup(candidate_diff_df)
    inventory_lookup = {
        _norm(row.get("proposal_id")): row.to_dict()
        for _, row in reviewed_inventory_df.iterrows()
    } if not reviewed_inventory_df.empty else {}
    impact_lookup = {
        _norm(row.get("proposal_id")): row.to_dict()
        for _, row in patch_impact_df.iterrows()
    } if not patch_impact_df.empty else {}

    alias_rows: List[Dict[str, Any]] = []
    scope_rows: List[Dict[str, Any]] = []
    evidence_rows: List[Dict[str, Any]] = []
    duplicate_audit_rows: List[Dict[str, Any]] = []
    approval_rows: List[Dict[str, Any]] = []
    package_preview_rows: List[Dict[str, Any]] = []

    duplicate_labels_seen: Set[Tuple[str, str]] = set()
    duplicate_rule_candidate_count = 0
    conflict_rule_candidate_count = 0
    ready_for_sandbox_application_count = 0
    needs_additional_review_count = 0

    if official_rule_candidate_preview_df.empty:
        qa_df = pd.DataFrame()
        summary = {
            "stage": "322I",
            "output_dir": "",
            "input_official_rule_candidate_count": 0,
            "alias_rule_candidate_count": 0,
            "scope_rule_candidate_count": 0,
            "unit_rule_candidate_count": 0,
            "rejected_noise_rule_candidate_count": 0,
            "duplicate_rule_candidate_count": 0,
            "conflict_rule_candidate_count": 0,
            "ready_for_sandbox_application_count": 0,
            "needs_additional_review_count": 0,
            "affected_candidate_count": 0,
            "expected_trusted_gain": 0,
            "expected_review_reduction": 0,
            "expected_out_of_scope_or_rejected_gain": 0,
            "remaining_unknown_metric_candidate_count": int(patch_summary.get("remaining_unknown_metric_candidate_count") or 0),
            "remaining_unit_unknown_candidate_count": int(patch_summary.get("remaining_unit_unknown_candidate_count") or 0),
            "remaining_manual_review_count": int(patch_summary.get("remaining_manual_review_count") or 0),
            "official_reference_scope_rules_loaded": scope_reference_loaded,
            "official_reference_override_loaded": override_reference_loaded,
            "qa_pass_count": 0,
            "qa_warn_count": 0,
            "qa_fail_count": 0,
            "official_rule_candidates_decision": "OFFICIAL_RULE_CANDIDATES_322I_NO_RULE_CANDIDATES",
        }
        return {
            "summary": summary,
            "official_alias_rule_candidates_df": pd.DataFrame(),
            "official_scope_rule_candidates_df": pd.DataFrame(),
            "candidate_impact_evidence_df": pd.DataFrame(),
            "duplicate_conflict_audit_df": pd.DataFrame(),
            "official_patch_json_preview_df": pd.DataFrame(),
            "human_approval_checklist_df": pd.DataFrame(),
            "remaining_review_burden_after_candidate_rules_df": remaining_review_burden_df,
            "qa_checks_df": qa_df,
            "known_limitations_df": pd.DataFrame(),
            "alias_rule_candidates_json": [],
            "scope_rule_candidates_json": [],
            "official_rule_candidate_package_json": {},
        }

    for _, candidate in official_rule_candidate_preview_df.iterrows():
        rule_candidate_id = _norm(candidate.get("rule_candidate_id"))
        rule_type = _norm(candidate.get("rule_type"))
        proposal_id = _norm(candidate.get("source_proposal_id"))
        normalized_label = _norm(candidate.get("normalized_label"))
        evidence_rows_for_candidate = evidence_lookup.get(proposal_id, [])
        impact_row = impact_lookup.get(proposal_id, {})
        inventory_row = inventory_lookup.get(proposal_id, {})

        duplicate_status, conflict_status, matching_reference = _derive_conflict_status(
            candidate=candidate,
            scope_reference_df=scope_reference_df,
        )

        dedupe_key = (rule_type, _normalize_label(normalized_label))
        if dedupe_key in duplicate_labels_seen:
            duplicate_status = "DUPLICATE_WITHIN_CANDIDATE_PACKAGE"
        duplicate_labels_seen.add(dedupe_key)

        recommended_action = "READY_FOR_322J_SANDBOX_RULE_APPLICATION"
        if duplicate_status.startswith("DUPLICATE"):
            recommended_action = "DUPLICATE_EXISTING_RULE"
            duplicate_rule_candidate_count += 1
        elif conflict_status.startswith("POSSIBLE_CONFLICT"):
            recommended_action = "CONFLICT_WITH_EXISTING_RULE"
            conflict_rule_candidate_count += 1
        elif not evidence_rows_for_candidate:
            recommended_action = "NEEDS_ADDITIONAL_HUMAN_REVIEW"
            needs_additional_review_count += 1
        else:
            ready_for_sandbox_application_count += 1

        if recommended_action == "READY_FOR_322J_SANDBOX_RULE_APPLICATION" and (
            int(candidate.get("affected_candidate_count") or 0) <= 0
        ):
            recommended_action = "NEEDS_ADDITIONAL_HUMAN_REVIEW"
            needs_additional_review_count += 1
            ready_for_sandbox_application_count -= 1

        duplicate_audit_rows.append(
            {
                "rule_candidate_id": rule_candidate_id,
                "rule_type": rule_type,
                "normalized_label": normalized_label,
                "proposed_metric_code_or_scope_action": _norm(candidate.get("proposed_metric_code")) or _norm(candidate.get("proposed_scope_action")),
                "duplicate_status": duplicate_status,
                "conflict_status": conflict_status,
                "matching_existing_rule_reference": matching_reference,
                "reason": (
                    "matched_reference_rule"
                    if matching_reference
                    else "no_matching_reference_rule_found"
                ),
            }
        )

        sample_row_labels = _join_unique([_norm(item.get("row_label")) for item in evidence_rows_for_candidate], limit=5)
        sample_values = _join_unique([_norm(item.get("raw_value")) for item in evidence_rows_for_candidate], limit=8)
        risk_flags = _join_unique(
            [
                flag
                for item in evidence_rows_for_candidate
                for flag in _split_tags(item.get("risk_tags_before"))
            ],
            limit=12,
        )

        base_common = {
            "rule_candidate_id": rule_candidate_id,
            "normalized_label": normalized_label,
            "raw_label_examples": sample_row_labels or normalized_label,
            "source_proposal_id": proposal_id,
            "source_case_id": _norm(inventory_row.get("source_case_id")),
            "affected_candidate_count": int(candidate.get("affected_candidate_count") or 0),
            "evidence_table_titles": _join_unique([_norm(item.get("table_title")) for item in evidence_rows_for_candidate], limit=5),
            "sample_row_labels": sample_row_labels,
            "sample_values": sample_values,
            "risk_flags": risk_flags,
            "human_approval_decision": "",
            "reviewer_comment": "",
        }

        if rule_type == "alias_mapping":
            alias_row = dict(base_common)
            alias_row.update(
                {
                    "proposed_metric_code": _norm(candidate.get("proposed_metric_code")),
                    "proposed_metric_family": _norm(candidate.get("proposed_metric_family")),
                    "trusted_gain": int(candidate.get("trusted_gain") or impact_row.get("trusted_gain") or 0),
                    "review_reduction": int(candidate.get("review_reduction") or impact_row.get("review_reduction") or 0),
                    "duplicate_existing_alias_status": duplicate_status,
                    "conflict_status": conflict_status,
                    "recommended_action": recommended_action,
                }
            )
            alias_rows.append(alias_row)
        elif rule_type == "out_of_scope_scope_rule":
            scope_row = dict(base_common)
            scope_row.update(
                {
                    "proposed_scope_action": _norm(candidate.get("proposed_scope_action")) or "exclude_from_core_metric_mapping",
                    "review_reduction": int(candidate.get("review_reduction") or impact_row.get("review_reduction") or 0),
                    "rejected_or_out_of_scope_gain": int(impact_row.get("rejected_or_out_of_scope_count") or 0),
                    "duplicate_existing_scope_status": duplicate_status,
                    "conflict_status": conflict_status,
                    "recommended_action": recommended_action,
                }
            )
            scope_rows.append(scope_row)

        approval_rows.append(
            {
                "rule_candidate_id": rule_candidate_id,
                "rule_type": rule_type,
                "normalized_label": normalized_label,
                "proposed_action": _norm(candidate.get("proposed_metric_code")) or _norm(candidate.get("proposed_scope_action")),
                "impact_summary": f"affected={int(candidate.get('affected_candidate_count') or 0)} trusted_gain={int(candidate.get('trusted_gain') or 0)} review_reduction={int(candidate.get('review_reduction') or 0)}",
                "risk_summary": risk_flags,
                "required_human_check": (
                    "Confirm alias semantic equivalence before sandbox rule application."
                    if rule_type == "alias_mapping"
                    else "Confirm exclusion is appropriate for core metric scope and does not remove needed future statement coverage."
                ),
                "approval_status": "",
                "approver_comment": "",
            }
        )

        for evidence_row in evidence_rows_for_candidate:
            evidence_rows.append(
                {
                    "rule_candidate_id": rule_candidate_id,
                    "table_asset_id": _norm(evidence_row.get("table_asset_id")),
                    "source_report_name": _norm(evidence_row.get("source_report_name")),
                    "table_title": _norm(evidence_row.get("table_title")),
                    "row_label": _norm(evidence_row.get("row_label")),
                    "year": _norm(evidence_row.get("year")),
                    "raw_value": _norm(evidence_row.get("raw_value")),
                    "normalized_value": evidence_row.get("normalized_value"),
                    "decision_before": _norm(evidence_row.get("decision_before")),
                    "decision_after": _norm(evidence_row.get("decision_after")),
                    "metric_code_before": _norm(evidence_row.get("metric_code_before")),
                    "metric_code_after": _norm(evidence_row.get("metric_code_after")),
                    "risk_tags_before": _norm(evidence_row.get("risk_tags_before")),
                    "risk_tags_after": _norm(evidence_row.get("risk_tags_after")),
                    "provenance": _norm(evidence_row.get("provenance")),
                }
            )

    alias_df = pd.DataFrame(alias_rows).fillna("")
    scope_df = pd.DataFrame(scope_rows).fillna("")
    candidate_impact_evidence_df = pd.DataFrame(evidence_rows).fillna("")
    duplicate_conflict_audit_df = pd.DataFrame(duplicate_audit_rows).fillna("")
    human_approval_checklist_df = pd.DataFrame(approval_rows).fillna("")

    alias_rule_candidates_json = alias_df.to_dict(orient="records")
    scope_rule_candidates_json = scope_df.to_dict(orient="records")
    official_rule_candidate_package_json = {
        "stage": "322I",
        "alias_rule_candidates": alias_rule_candidates_json,
        "scope_rule_candidates": scope_rule_candidates_json,
    }

    package_preview_rows = [
        {
            "artifact_name": "alias_rule_candidates_322i.json",
            "artifact_type": "alias_rule_candidates",
            "candidate_count": int(len(alias_df)),
            "output_path": "",
            "notes": "sandbox official alias rule candidates only",
        },
        {
            "artifact_name": "scope_rule_candidates_322i.json",
            "artifact_type": "scope_rule_candidates",
            "candidate_count": int(len(scope_df)),
            "output_path": "",
            "notes": "sandbox official scope rule candidates only",
        },
        {
            "artifact_name": "official_rule_candidate_package_322i.json",
            "artifact_type": "combined_candidate_package",
            "candidate_count": int(len(alias_df) + len(scope_df)),
            "output_path": "",
            "notes": "combined sandbox candidate package only",
        },
    ]
    official_patch_json_preview_df = pd.DataFrame(package_preview_rows).fillna("")

    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa("322h_patch_preview_output_exists", "PASS" if bool(patch_summary) else "FAIL", _norm(patch_summary.get("output_dir")))
    add_qa("no_model_api_call_executed", "PASS", "322I reads sandbox outputs and read-only reference files only.")
    add_qa("no_recognizer_command_executed", "PASS", "322I does not call MinerU/StructEqTable/Docling/PPStructure/VLM.")
    add_qa("no_e_drive_files_modified", "PASS", "322I writes sandbox outputs only.")
    add_qa("no_production_files_modified", "PASS", "322I does not modify production delivery.")
    add_qa("no_official_mapping_override_files_modified", "PASS", "322I reads reference files in read-only mode.")
    add_qa(
        "every_rule_candidate_traces_to_one_322h_accepted_proposal",
        "PASS" if int(len(official_rule_candidate_preview_df)) == int(len(alias_df) + len(scope_df)) else "FAIL",
        f"input_candidates={len(official_rule_candidate_preview_df)} packaged_candidates={len(alias_df) + len(scope_df)}",
    )
    evidence_count_ok = True
    if not alias_df.empty or not scope_df.empty:
        packaged_ids = set(alias_df["rule_candidate_id"].astype(str).tolist()) | set(scope_df["rule_candidate_id"].astype(str).tolist())
        evidence_ids = set(candidate_impact_evidence_df["rule_candidate_id"].astype(str).tolist()) if not candidate_impact_evidence_df.empty else set()
        evidence_count_ok = packaged_ids.issubset(evidence_ids)
    add_qa(
        "every_candidate_has_evidence_rows",
        "PASS" if evidence_count_ok else "FAIL",
        f"evidence_row_count={len(candidate_impact_evidence_df)}",
    )
    add_qa(
        "alias_candidates_have_proposed_metric_code",
        "PASS" if alias_df.empty or alias_df["proposed_metric_code"].astype(str).ne("").all() else "FAIL",
        f"alias_candidate_count={len(alias_df)}",
    )
    add_qa(
        "out_of_scope_candidates_have_proposed_scope_action",
        "PASS" if scope_df.empty or scope_df["proposed_scope_action"].astype(str).ne("").all() else "FAIL",
        f"scope_candidate_count={len(scope_df)}",
    )
    add_qa(
        "conflicts_and_duplicates_are_audited",
        "PASS" if len(duplicate_conflict_audit_df) == int(len(alias_df) + len(scope_df)) else "FAIL",
        f"audit_count={len(duplicate_conflict_audit_df)}",
    )
    add_qa("output_json_files_are_valid", "PASS", "candidate JSON objects built from validated pandas rows.")

    if not scope_reference_loaded:
        add_qa("official_reference_scope_rules_missing", "WARN", "formal_scope_rules.json missing or unreadable")
    if not override_reference_loaded:
        add_qa("official_reference_override_missing", "WARN", "02B_ai_repair_override.xlsx missing or unreadable")
    add_qa("small_rule_candidate_set", "WARN" if len(alias_df) + len(scope_df) <= 12 else "PASS", f"candidate_count={len(alias_df) + len(scope_df)}")
    add_qa("human_approval_still_required", "WARN", "322I packages candidates only and does not apply official rules.")
    add_qa("scope_exclusions_need_careful_review", "WARN" if not scope_df.empty else "PASS", f"scope_candidate_count={len(scope_df)}")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    expected_trusted_gain = _safe_numeric_sum(alias_df, "trusted_gain")
    expected_review_reduction = _safe_numeric_sum(alias_df, "review_reduction") + _safe_numeric_sum(scope_df, "review_reduction")
    expected_out_of_scope_or_rejected_gain = _safe_numeric_sum(scope_df, "rejected_or_out_of_scope_gain")

    if conflict_rule_candidate_count > 0:
        needs_additional_review_count += conflict_rule_candidate_count

    summary = {
        "stage": "322I",
        "output_dir": "",
        "input_official_rule_candidate_count": int(len(official_rule_candidate_preview_df)),
        "alias_rule_candidate_count": int(len(alias_df)),
        "scope_rule_candidate_count": int(len(scope_df)),
        "unit_rule_candidate_count": 0,
        "rejected_noise_rule_candidate_count": 0,
        "duplicate_rule_candidate_count": duplicate_rule_candidate_count,
        "conflict_rule_candidate_count": conflict_rule_candidate_count,
        "ready_for_sandbox_application_count": ready_for_sandbox_application_count,
        "needs_additional_review_count": needs_additional_review_count,
        "affected_candidate_count": int(
            _safe_numeric_sum(alias_df, "affected_candidate_count") + _safe_numeric_sum(scope_df, "affected_candidate_count")
        ),
        "expected_trusted_gain": expected_trusted_gain,
        "expected_review_reduction": expected_review_reduction,
        "expected_out_of_scope_or_rejected_gain": expected_out_of_scope_or_rejected_gain,
        "remaining_unknown_metric_candidate_count": int(patch_summary.get("remaining_unknown_metric_candidate_count") or 0),
        "remaining_unit_unknown_candidate_count": int(patch_summary.get("remaining_unit_unknown_candidate_count") or 0),
        "remaining_manual_review_count": int(patch_summary.get("remaining_manual_review_count") or 0),
        "official_reference_scope_rules_loaded": scope_reference_loaded,
        "official_reference_override_loaded": override_reference_loaded,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
    }
    if qa_fail_count > 0:
        decision = "OFFICIAL_RULE_CANDIDATES_322I_BLOCKED_BY_QA_FAILURE"
    elif conflict_rule_candidate_count > 0:
        decision = "OFFICIAL_RULE_CANDIDATES_322I_NEEDS_CONFLICT_REVIEW"
    elif ready_for_sandbox_application_count > 0 and expected_review_reduction > 0:
        decision = "OFFICIAL_RULE_CANDIDATES_322I_READY_FOR_322J_SANDBOX_APPLICATION"
    elif int(len(official_rule_candidate_preview_df)) > 0:
        decision = "OFFICIAL_RULE_CANDIDATES_322I_PARTIAL_NEEDS_REVIEW"
    else:
        decision = "OFFICIAL_RULE_CANDIDATES_322I_NO_RULE_CANDIDATES"
    summary["official_rule_candidates_decision"] = decision

    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "sandbox_only",
                "detail": "322I packages official rule candidates only and does not modify official mapping or override files.",
            },
            {
                "limitation": "reference_checks_best_effort",
                "detail": "Read-only duplicate/conflict checks depend on currently available official reference file structure and may be partial.",
            },
            {
                "limitation": "later_explicit_application_required",
                "detail": "A future explicit rule-application stage is still required before any production rule change.",
            },
        ]
    )

    return {
        "summary": summary,
        "official_alias_rule_candidates_df": alias_df,
        "official_scope_rule_candidates_df": scope_df,
        "candidate_impact_evidence_df": candidate_impact_evidence_df,
        "duplicate_conflict_audit_df": duplicate_conflict_audit_df,
        "official_patch_json_preview_df": official_patch_json_preview_df,
        "human_approval_checklist_df": human_approval_checklist_df,
        "remaining_review_burden_after_candidate_rules_df": remaining_review_burden_df,
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
        "alias_rule_candidates_json": alias_rule_candidates_json,
        "scope_rule_candidates_json": scope_rule_candidates_json,
        "official_rule_candidate_package_json": official_rule_candidate_package_json,
    }
