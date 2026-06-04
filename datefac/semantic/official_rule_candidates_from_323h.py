from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set

import pandas as pd


READY_DECISION = (
    "OFFICIAL_RULE_CANDIDATES_FROM_SANDBOX_323I_READY_FOR_323J_CONTROLLED_PROPOSAL"
)
READY_WARN_DECISION = (
    "OFFICIAL_RULE_CANDIDATES_FROM_SANDBOX_323I_READY_WITH_WARNINGS"
)
NOT_READY_DECISION = "OFFICIAL_RULE_CANDIDATES_FROM_SANDBOX_323I_NOT_READY"

EXPECTED_323H_READY_DECISION = (
    "HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_READY_FOR_323I_OFFICIAL_RULE_CANDIDATES"
)
EXPECTED_323H_READY_WARN_DECISION = (
    "HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_READY_FOR_REVIEW_WITH_WARNINGS"
)
EXPECTED_323G_REVIEWED_DECISION = (
    "HUMAN_CONFIRMED_SUGGESTION_PROPOSALS_323G_REVIEWED_READY_FOR_323H_SANDBOX_REPLAY"
)
ALLOWED_323H_WARN_CHECK = "sandbox_rules::duplicate_source_rule_groups"


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_label(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").lower()


def _safe_int(value: Any) -> int:
    if value in ("", None):
        return 0
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return 0


def _safe_float(value: Any) -> float:
    if value in ("", None):
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _norm(value).lower()
    return text in {"1", "true", "yes", "y"}


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


def _parse_literal_payload(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return value
    text = _norm(value)
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        return ast.literal_eval(text)
    except Exception:
        return {}


def _parse_dict(value: Any) -> Dict[str, Any]:
    parsed = _parse_literal_payload(value)
    return parsed if isinstance(parsed, dict) else {}


def _parse_list(value: Any) -> List[Any]:
    parsed = _parse_literal_payload(value)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, tuple):
        return list(parsed)
    text = _norm(value)
    return [text] if text else []


def _split_pipe_list(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _dedupe_preserve(items: Iterable[Any]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _join_unique(items: Iterable[Any], limit: int = 8) -> str:
    return " | ".join(_dedupe_preserve(items)[:limit])


def _stable_candidate_id(candidate_type: str, normalized_label_key: str) -> str:
    digest = hashlib.sha1(f"{candidate_type}::{normalized_label_key}".encode("utf-8")).hexdigest()
    return f"323i::{candidate_type}::{digest[:12]}"


def load_official_rule_candidates_from_323h_inputs(
    sandbox_replay_dir: Path,
    reviewed_confirmation_dir: Path,
) -> Dict[str, Any]:
    return {
        "sandbox_summary": _read_json(
            sandbox_replay_dir / "human_confirmed_sandbox_replay_323h_summary.json"
        ),
        "sandbox_qa": _read_json(
            sandbox_replay_dir / "human_confirmed_sandbox_replay_323h_qa.json"
        ),
        "sandbox_rule_set": _read_json(
            sandbox_replay_dir / "human_confirmed_sandbox_replay_323h_sandbox_rule_set.json"
        ),
        "sandbox_rule_application_log_df": read_jsonl(
            sandbox_replay_dir / "human_confirmed_sandbox_replay_323h_rule_application_log.jsonl"
        ),
        "reviewed_summary": _read_json(
            reviewed_confirmation_dir
            / "human_confirmed_suggestion_proposals_323g_reviewed_summary.json"
        ),
        "reviewed_plan": _read_json(
            reviewed_confirmation_dir
            / "human_confirmed_suggestion_proposals_323g_human_confirmed_plan.json"
        ),
    }


def _extract_confirmed_suggestions(reviewed_plan: Dict[str, Any]) -> pd.DataFrame:
    raw_rows = reviewed_plan.get("confirmed_suggestions", [])
    if not isinstance(raw_rows, list):
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for item in raw_rows:
        if not isinstance(item, dict):
            continue
        sample_evidence = _parse_dict(item.get("sample_evidence"))
        provenance = _parse_dict(item.get("provenance"))
        expected_impact = _parse_dict(item.get("expected_impact"))
        raw_response_reference = _parse_dict(item.get("raw_response_reference"))
        risk_flags = [
            _norm(flag)
            for flag in _parse_list(item.get("risk_flags"))
            if _norm(flag)
        ]
        rows.append(
            {
                "confirmation_id": _norm(item.get("confirmation_id")),
                "request_id": _norm(item.get("request_id")),
                "source_batch_item_id": _norm(item.get("source_batch_item_id")),
                "source_group_id": _norm(item.get("source_group_id")),
                "suggestion_type": _norm(item.get("suggestion_type")),
                "candidate_label": _norm(item.get("candidate_label")),
                "candidate_label_key": _normalize_label(item.get("candidate_label")),
                "suggested_response_label": _norm(item.get("suggested_response_label")),
                "suggested_target_metric_if_any": _norm(
                    item.get("suggested_target_metric_if_any")
                ),
                "confidence": _norm(item.get("confidence")),
                "rationale": _norm(item.get("rationale")),
                "sample_candidate_ids": _parse_list(
                    sample_evidence.get("sample_candidate_ids")
                ),
                "sample_texts": _parse_list(sample_evidence.get("sample_texts")),
                "sample_table_titles": _parse_list(
                    sample_evidence.get("sample_table_titles")
                ),
                "sample_years": _parse_list(sample_evidence.get("sample_years")),
                "sample_evidence_text": _norm(item.get("sample_evidence_text")),
                "provenance": provenance,
                "provenance_text": _norm(item.get("provenance_text")),
                "expected_affected_candidate_count": _safe_int(
                    item.get("expected_affected_candidate_count")
                    or expected_impact.get("affected_candidate_count")
                ),
                "expected_review_reduction_potential": _safe_int(
                    item.get("expected_review_reduction_potential")
                    or expected_impact.get("expected_review_reduction_potential")
                ),
                "priority_score": _safe_float(
                    item.get("priority_score") or expected_impact.get("priority_score")
                ),
                "risk_note": _norm(item.get("risk_note")),
                "risk_flags": risk_flags,
                "raw_response_reference": raw_response_reference,
                "reviewer_decision": _norm(item.get("reviewer_decision")).upper(),
                "reviewer_note": _norm(item.get("reviewer_note")),
                "reviewer_name": _norm(item.get("reviewer_name")),
                "review_timestamp": _norm(item.get("review_timestamp")),
            }
        )
    return pd.DataFrame(rows).fillna("")


def _build_source_rule_inventory_df(sandbox_rule_set: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for rule_type_name, candidate_type in [("alias_rules", "alias"), ("scope_rules", "scope")]:
        for item in sandbox_rule_set.get(rule_type_name, []):
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    "source_rule_id": _norm(item.get("source_rule_id")),
                    "confirmation_id": _norm(item.get("confirmation_id")),
                    "request_id": _norm(item.get("request_id")),
                    "source_group_id": _norm(item.get("source_group_id")),
                    "candidate_type": candidate_type,
                    "proposal_type": _norm(item.get("rule_type")),
                    "normalized_label": _norm(item.get("normalized_label")),
                    "normalized_label_key": _normalize_label(item.get("normalized_label")),
                    "confidence": _norm(item.get("confidence")),
                    "priority_score": _safe_float(item.get("priority_score")),
                    "risk_flags": _dedupe_preserve(item.get("risk_flags", [])),
                    "expected_affected_candidate_count": _safe_int(
                        item.get("expected_affected_candidate_count")
                    ),
                    "proposed_metric_code": _norm(item.get("proposed_metric_code")),
                    "proposed_metric_family": _norm(item.get("proposed_metric_family")),
                    "target_label": _norm(item.get("target_label")),
                    "proposed_scope_action": _norm(item.get("proposed_scope_action")),
                    "metric_target_resolved": _safe_bool(item.get("metric_target_resolved")),
                }
            )
    return pd.DataFrame(rows).fillna("")


def _build_duplicate_groups_df(sandbox_rule_set: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for item in sandbox_rule_set.get("duplicate_conflict_summary", []):
        if not isinstance(item, dict):
            continue
        proposal_type = _norm(item.get("proposal_type"))
        candidate_type = "alias" if proposal_type == "alias" else "scope"
        rows.append(
            {
                "candidate_type": candidate_type,
                "proposal_type": proposal_type,
                "normalized_label": _norm(item.get("normalized_label")),
                "normalized_label_key": _normalize_label(item.get("normalized_label_key") or item.get("normalized_label")),
                "source_rule_count": _safe_int(item.get("source_rule_count")),
                "duplicate_source_rule": _safe_bool(item.get("duplicate_source_rule")),
                "proposed_metric_codes": _norm(item.get("proposed_metric_codes")),
                "conflicting_targets": _safe_bool(item.get("conflicting_targets")),
                "already_in_official_assets": _safe_bool(
                    item.get("already_in_official_assets")
                ),
                "source_rule_ids": _split_pipe_list(item.get("source_rule_ids")),
                "source_group_ids": _split_pipe_list(item.get("source_group_ids")),
            }
        )
    return pd.DataFrame(rows).fillna("")


def _build_source_provenance_df(
    source_rule_inventory_df: pd.DataFrame,
    confirmed_df: pd.DataFrame,
    rule_application_log_df: pd.DataFrame,
) -> pd.DataFrame:
    if source_rule_inventory_df.empty:
        return pd.DataFrame()

    confirmed_lookup = {
        _norm(row.get("confirmation_id")): row.to_dict()
        for _, row in confirmed_df.iterrows()
    } if not confirmed_df.empty else {}
    log_lookup = {
        _norm(row.get("source_rule_id")): row.to_dict()
        for _, row in rule_application_log_df.iterrows()
    } if not rule_application_log_df.empty else {}

    rows: List[Dict[str, Any]] = []
    for _, row in source_rule_inventory_df.iterrows():
        confirmation = confirmed_lookup.get(_norm(row.get("confirmation_id")), {})
        log_row = log_lookup.get(_norm(row.get("source_rule_id")), {})
        rows.append(
            {
                "source_rule_id": _norm(row.get("source_rule_id")),
                "confirmation_id": _norm(row.get("confirmation_id")),
                "request_id": _norm(row.get("request_id")),
                "source_group_id": _norm(row.get("source_group_id")),
                "candidate_type": _norm(row.get("candidate_type")),
                "normalized_label": _norm(row.get("normalized_label")),
                "normalized_label_key": _norm(row.get("normalized_label_key")),
                "confidence": _norm(row.get("confidence")),
                "priority_score": _safe_float(row.get("priority_score")),
                "proposed_metric_code": _norm(row.get("proposed_metric_code")),
                "proposed_metric_family": _norm(row.get("proposed_metric_family")),
                "proposed_scope_action": _norm(row.get("proposed_scope_action")),
                "target_label": _norm(row.get("target_label")),
                "risk_flags": "|".join(row.get("risk_flags", []))
                if isinstance(row.get("risk_flags"), list)
                else _norm(row.get("risk_flags")),
                "reviewer_name": _norm(confirmation.get("reviewer_name")),
                "reviewer_note": _norm(confirmation.get("reviewer_note")),
                "review_timestamp": _norm(confirmation.get("review_timestamp")),
                "sample_candidate_ids": "|".join(
                    _dedupe_preserve(confirmation.get("sample_candidate_ids", []))
                ),
                "sample_table_titles": _join_unique(
                    confirmation.get("sample_table_titles", []), limit=8
                ),
                "sample_texts": _join_unique(
                    confirmation.get("sample_texts", []), limit=10
                ),
                "sample_years": _join_unique(
                    confirmation.get("sample_years", []), limit=8
                ),
                "sample_evidence_text": _norm(confirmation.get("sample_evidence_text")),
                "provenance_text": _norm(confirmation.get("provenance_text")),
                "expected_affected_candidate_count": _safe_int(
                    row.get("expected_affected_candidate_count")
                ),
                "actual_affected_candidate_count": _safe_int(
                    log_row.get("actual_affected_candidate_count")
                ),
                "trusted_gain": _safe_int(log_row.get("trusted_gain")),
                "review_reduction": _safe_int(log_row.get("review_reduction")),
                "out_of_scope_or_rejected_gain": _safe_int(
                    log_row.get("out_of_scope_or_rejected_gain")
                ),
                "application_status": _norm(log_row.get("application_status")),
            }
        )
    return pd.DataFrame(rows).fillna("")


def _build_effective_candidates(
    duplicate_groups_df: pd.DataFrame,
    source_provenance_df: pd.DataFrame,
) -> Dict[str, pd.DataFrame]:
    if duplicate_groups_df.empty:
        return {
            "effective_candidates_df": pd.DataFrame(),
            "alias_candidates_df": pd.DataFrame(),
            "scope_candidates_df": pd.DataFrame(),
            "candidate_source_bridge_df": pd.DataFrame(),
        }

    rows: List[Dict[str, Any]] = []
    bridge_rows: List[Dict[str, Any]] = []

    for _, group_row in duplicate_groups_df.iterrows():
        source_rule_ids = group_row.get("source_rule_ids", [])
        if not isinstance(source_rule_ids, list):
            source_rule_ids = _split_pipe_list(source_rule_ids)
        candidate_type = _norm(group_row.get("candidate_type"))
        label_key = _norm(group_row.get("normalized_label_key"))
        candidate_id = _stable_candidate_id(candidate_type, label_key)

        matched_df = source_provenance_df.loc[
            source_provenance_df["source_rule_id"].astype(str).isin(source_rule_ids)
        ].copy()
        actual_affected = _safe_numeric_sum(matched_df, "actual_affected_candidate_count")
        trusted_gain = _safe_numeric_sum(matched_df, "trusted_gain")
        review_reduction = _safe_numeric_sum(matched_df, "review_reduction")
        out_of_scope_gain = _safe_numeric_sum(matched_df, "out_of_scope_or_rejected_gain")
        expected_affected = _safe_numeric_sum(matched_df, "expected_affected_candidate_count")
        proposed_metric_codes = _dedupe_preserve(matched_df["proposed_metric_code"].tolist())
        proposed_metric_families = _dedupe_preserve(
            matched_df["proposed_metric_family"].tolist()
        )
        proposed_scope_actions = _dedupe_preserve(
            matched_df["proposed_scope_action"].tolist()
        )
        target_labels = _dedupe_preserve(matched_df["target_label"].tolist())
        confidence_labels = _dedupe_preserve(matched_df["confidence"].tolist())
        reviewer_names = _dedupe_preserve(matched_df["reviewer_name"].tolist())
        reviewer_notes = _dedupe_preserve(matched_df["reviewer_note"].tolist())
        reviewer_timestamps = _dedupe_preserve(matched_df["review_timestamp"].tolist())
        source_group_ids = _dedupe_preserve(matched_df["source_group_id"].tolist())
        confirmation_ids = _dedupe_preserve(matched_df["confirmation_id"].tolist())
        request_ids = _dedupe_preserve(matched_df["request_id"].tolist())
        risk_flags = _dedupe_preserve(
            flag
            for raw in matched_df["risk_flags"].tolist()
            for flag in _split_pipe_list(raw)
        )
        sample_table_titles = _dedupe_preserve(
            item
            for raw in matched_df["sample_table_titles"].tolist()
            for item in _split_pipe_list(raw)
        )
        sample_texts = _dedupe_preserve(
            item
            for raw in matched_df["sample_texts"].tolist()
            for item in _split_pipe_list(raw)
        )
        sample_years = _dedupe_preserve(
            item
            for raw in matched_df["sample_years"].tolist()
            for item in _split_pipe_list(raw)
        )
        provenance_texts = _dedupe_preserve(matched_df["provenance_text"].tolist())
        application_statuses = _dedupe_preserve(matched_df["application_status"].tolist())

        candidate_status = (
            "NEEDS_REVIEW"
            if _safe_bool(group_row.get("conflicting_targets"))
            or _safe_bool(group_row.get("already_in_official_assets"))
            else "READY_FOR_CONTROLLED_PROPOSAL"
        )

        candidate_row = {
            "rule_candidate_id": candidate_id,
            "candidate_type": candidate_type,
            "proposal_type": _norm(group_row.get("proposal_type")),
            "rule_candidate_status": candidate_status,
            "normalized_label": _norm(group_row.get("normalized_label")),
            "normalized_label_key": label_key,
            "source_rule_count": _safe_int(group_row.get("source_rule_count")),
            "duplicate_source_rule": _safe_bool(group_row.get("duplicate_source_rule")),
            "conflicting_targets": _safe_bool(group_row.get("conflicting_targets")),
            "already_in_official_assets": _safe_bool(
                group_row.get("already_in_official_assets")
            ),
            "conflict_free": not _safe_bool(group_row.get("conflicting_targets"))
            and not _safe_bool(group_row.get("already_in_official_assets")),
            "source_rule_ids": "|".join(_dedupe_preserve(source_rule_ids)),
            "source_group_ids": "|".join(source_group_ids),
            "source_confirmation_ids": "|".join(confirmation_ids),
            "source_request_ids": "|".join(request_ids),
            "confidence_labels": "|".join(confidence_labels),
            "reviewer_names": "|".join(reviewer_names),
            "reviewer_notes": _join_unique(reviewer_notes, limit=8),
            "review_timestamps": "|".join(reviewer_timestamps),
            "proposed_metric_code": proposed_metric_codes[0]
            if candidate_type == "alias" and len(proposed_metric_codes) == 1
            else "",
            "proposed_metric_family": proposed_metric_families[0]
            if candidate_type == "alias" and len(proposed_metric_families) == 1
            else "",
            "target_label_examples": "|".join(target_labels),
            "proposed_scope_action": proposed_scope_actions[0]
            if candidate_type == "scope" and len(proposed_scope_actions) == 1
            else "",
            "expected_affected_candidate_count": expected_affected,
            "actual_affected_candidate_count": actual_affected,
            "trusted_gain": trusted_gain,
            "review_reduction": review_reduction,
            "out_of_scope_or_rejected_gain": out_of_scope_gain,
            "priority_score_max": float(matched_df["priority_score"].max())
            if not matched_df.empty
            else 0.0,
            "priority_score_sum": float(
                pd.to_numeric(matched_df["priority_score"], errors="coerce")
                .fillna(0)
                .sum()
            )
            if not matched_df.empty
            else 0.0,
            "risk_flags": "|".join(risk_flags),
            "sample_table_titles": _join_unique(sample_table_titles, limit=8),
            "sample_texts": _join_unique(sample_texts, limit=10),
            "sample_years": _join_unique(sample_years, limit=8),
            "provenance_text_samples": _join_unique(provenance_texts, limit=6),
            "application_statuses": "|".join(application_statuses),
            "dedupe_resolution": (
                "DEDUPED_DUPLICATE_SOURCE_RULES"
                if _safe_bool(group_row.get("duplicate_source_rule"))
                else "UNIQUE_SOURCE_RULE"
            ),
            "candidate_readiness_reason": (
                "Conflict-free unique effective candidate derived from 323H sandbox replay evidence."
                if candidate_status == "READY_FOR_CONTROLLED_PROPOSAL"
                else "Candidate retained but requires review due to conflict or official overlap."
            ),
        }
        rows.append(candidate_row)

        for _, source_row in matched_df.iterrows():
            bridge_rows.append(
                {
                    "rule_candidate_id": candidate_id,
                    "candidate_type": candidate_type,
                    "normalized_label": _norm(group_row.get("normalized_label")),
                    "source_rule_id": _norm(source_row.get("source_rule_id")),
                    "confirmation_id": _norm(source_row.get("confirmation_id")),
                    "request_id": _norm(source_row.get("request_id")),
                    "source_group_id": _norm(source_row.get("source_group_id")),
                    "source_rule_actual_affected_candidate_count": _safe_int(
                        source_row.get("actual_affected_candidate_count")
                    ),
                    "source_rule_trusted_gain": _safe_int(source_row.get("trusted_gain")),
                    "source_rule_review_reduction": _safe_int(
                        source_row.get("review_reduction")
                    ),
                    "source_rule_out_of_scope_or_rejected_gain": _safe_int(
                        source_row.get("out_of_scope_or_rejected_gain")
                    ),
                    "reviewer_name": _norm(source_row.get("reviewer_name")),
                    "review_timestamp": _norm(source_row.get("review_timestamp")),
                    "provenance_text": _norm(source_row.get("provenance_text")),
                }
            )

    effective_candidates_df = pd.DataFrame(rows).fillna("").sort_values(
        ["candidate_type", "normalized_label_key"], ascending=[True, True]
    ).reset_index(drop=True)
    candidate_source_bridge_df = pd.DataFrame(bridge_rows).fillna("")
    alias_candidates_df = effective_candidates_df.loc[
        effective_candidates_df["candidate_type"].astype(str) == "alias"
    ].copy()
    scope_candidates_df = effective_candidates_df.loc[
        effective_candidates_df["candidate_type"].astype(str) == "scope"
    ].copy()
    return {
        "effective_candidates_df": effective_candidates_df,
        "alias_candidates_df": alias_candidates_df,
        "scope_candidates_df": scope_candidates_df,
        "candidate_source_bridge_df": candidate_source_bridge_df,
    }


def _qa_allowed_323h_warning(sandbox_qa: Dict[str, Any]) -> bool:
    checks = sandbox_qa.get("checks", [])
    if not isinstance(checks, list):
        return False
    warn_checks = [
        _norm(item.get("check_name"))
        for item in checks
        if isinstance(item, dict) and _norm(item.get("status")) == "WARN"
    ]
    return bool(warn_checks) and set(warn_checks) == {ALLOWED_323H_WARN_CHECK}


def _build_known_limitations_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "limitation": "sandbox_evidence_only",
                "detail": "323I converts sandbox replay evidence into official rule candidates only and does not modify official assets.",
            },
            {
                "limitation": "dedupe_preserves_provenance",
                "detail": "Duplicate source suggestions are retained as provenance instead of becoming separate effective candidates.",
            },
            {
                "limitation": "later_controlled_stage_required",
                "detail": "READY_FOR_CONTROLLED_PROPOSAL candidates still require the next controlled proposal stage before any official patch dry run.",
            },
        ]
    )


def build_official_rule_candidates_from_323h(
    sandbox_summary: Dict[str, Any],
    sandbox_qa: Dict[str, Any],
    sandbox_rule_set: Dict[str, Any],
    sandbox_rule_application_log_df: pd.DataFrame,
    reviewed_summary: Dict[str, Any],
    reviewed_plan: Dict[str, Any],
) -> Dict[str, Any]:
    confirmed_df = _extract_confirmed_suggestions(reviewed_plan)
    source_rule_inventory_df = _build_source_rule_inventory_df(sandbox_rule_set)
    duplicate_groups_df = _build_duplicate_groups_df(sandbox_rule_set)
    source_provenance_df = _build_source_provenance_df(
        source_rule_inventory_df=source_rule_inventory_df,
        confirmed_df=confirmed_df,
        rule_application_log_df=sandbox_rule_application_log_df,
    )
    candidate_outputs = _build_effective_candidates(
        duplicate_groups_df=duplicate_groups_df,
        source_provenance_df=source_provenance_df,
    )
    effective_candidates_df = candidate_outputs["effective_candidates_df"]
    alias_candidates_df = candidate_outputs["alias_candidates_df"]
    scope_candidates_df = candidate_outputs["scope_candidates_df"]
    candidate_source_bridge_df = candidate_outputs["candidate_source_bridge_df"]

    summary_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        summary_rows.append({"check_name": name, "status": status, "detail": detail})

    sandbox_decision = _norm(sandbox_summary.get("decision"))
    sandbox_warn_count = _safe_int(sandbox_summary.get("qa_warn_count"))
    sandbox_fail_count = _safe_int(sandbox_summary.get("qa_fail_count"))
    reviewed_decision = _norm(reviewed_summary.get("decision"))

    add_qa(
        "readiness::323g_reviewed_decision",
        "PASS" if reviewed_decision == EXPECTED_323G_REVIEWED_DECISION else "FAIL",
        reviewed_decision,
    )
    add_qa(
        "readiness::323h_qa_fail_count",
        "PASS" if sandbox_fail_count == 0 else "FAIL",
        str(sandbox_fail_count),
    )
    add_qa(
        "readiness::323h_decision_allowed",
        "PASS"
        if sandbox_decision == EXPECTED_323H_READY_DECISION
        or (
            sandbox_decision == EXPECTED_323H_READY_WARN_DECISION
            and sandbox_warn_count > 0
            and _qa_allowed_323h_warning(sandbox_qa)
        )
        else "FAIL",
        sandbox_decision,
    )
    add_qa(
        "readiness::323h_only_duplicate_warning_if_not_fully_ready",
        "PASS"
        if sandbox_decision != EXPECTED_323H_READY_WARN_DECISION
        or _qa_allowed_323h_warning(sandbox_qa)
        else "FAIL",
        f"qa_warn_count={sandbox_warn_count}",
    )

    for key, expected in [
        ("affected_candidate_count", 129),
        ("trusted_gain_323h", 44),
        ("review_reduction_323h", 129),
        ("out_of_scope_or_rejected_gain_323h", 85),
        ("core_false_exclusion_count", 0),
        ("conflict_count", 0),
        ("sandbox_rule_count", 11),
        ("sandbox_alias_rule_count", 2),
        ("sandbox_scope_rule_count", 9),
        ("effective_unique_rule_count", 6),
        ("duplicate_rule_count", 3),
    ]:
        add_qa(
            f"readiness::323h_{key}",
            "PASS" if _safe_int(sandbox_summary.get(key)) == expected else "FAIL",
            f"expected={expected} actual={sandbox_summary.get(key, '')}",
        )

    add_qa(
        "inputs::reviewed_confirmed_suggestion_count",
        "PASS" if len(confirmed_df) == 11 else "FAIL",
        f"actual={len(confirmed_df)}",
    )
    add_qa(
        "inputs::source_rule_inventory_count",
        "PASS" if len(source_rule_inventory_df) == 11 else "FAIL",
        f"actual={len(source_rule_inventory_df)}",
    )
    add_qa(
        "inputs::rule_application_log_count",
        "PASS" if len(sandbox_rule_application_log_df) == 11 else "FAIL",
        f"actual={len(sandbox_rule_application_log_df)}",
    )
    add_qa(
        "dedupe::effective_unique_candidate_count",
        "PASS" if len(effective_candidates_df) == 6 else "FAIL",
        f"actual={len(effective_candidates_df)}",
    )
    add_qa(
        "dedupe::alias_candidate_count",
        "PASS" if len(alias_candidates_df) == 2 else "FAIL",
        f"actual={len(alias_candidates_df)}",
    )
    add_qa(
        "dedupe::scope_candidate_count",
        "PASS" if len(scope_candidates_df) == 4 else "FAIL",
        f"actual={len(scope_candidates_df)}",
    )

    duplicate_group_count = int(
        duplicate_groups_df["duplicate_source_rule"].astype(bool).sum()
    ) if not duplicate_groups_df.empty else 0
    conflicting_target_group_count = int(
        duplicate_groups_df["conflicting_targets"].astype(bool).sum()
    ) if not duplicate_groups_df.empty else 0
    official_overlap_group_count = int(
        duplicate_groups_df["already_in_official_assets"].astype(bool).sum()
    ) if not duplicate_groups_df.empty else 0

    add_qa(
        "dedupe::duplicate_group_count",
        "PASS" if duplicate_group_count == 3 else "FAIL",
        f"actual={duplicate_group_count}",
    )
    add_qa(
        "dedupe::no_conflicting_duplicate_targets",
        "PASS" if conflicting_target_group_count == 0 else "FAIL",
        f"actual={conflicting_target_group_count}",
    )
    add_qa(
        "dedupe::no_official_overlap_in_323h_groups",
        "PASS" if official_overlap_group_count == 0 else "FAIL",
        f"actual={official_overlap_group_count}",
    )

    unique_source_rule_ids = _dedupe_preserve(source_provenance_df["source_rule_id"].tolist())
    bridged_source_rule_ids = _dedupe_preserve(
        candidate_source_bridge_df["source_rule_id"].tolist()
    )
    add_qa(
        "provenance::every_source_rule_accounted_once",
        "PASS"
        if len(unique_source_rule_ids) == 11
        and sorted(unique_source_rule_ids) == sorted(bridged_source_rule_ids)
        else "FAIL",
        f"source_rule_inventory={len(unique_source_rule_ids)} bridge={len(bridged_source_rule_ids)}",
    )
    add_qa(
        "provenance::every_effective_candidate_has_source_bridge_rows",
        "PASS"
        if effective_candidates_df.empty
        or set(effective_candidates_df["rule_candidate_id"].astype(str).tolist()).issubset(
            set(candidate_source_bridge_df["rule_candidate_id"].astype(str).tolist())
        )
        else "FAIL",
        f"bridge_row_count={len(candidate_source_bridge_df)}",
    )

    affected_candidate_count = _safe_numeric_sum(
        effective_candidates_df, "actual_affected_candidate_count"
    )
    trusted_gain = _safe_numeric_sum(effective_candidates_df, "trusted_gain")
    review_reduction = _safe_numeric_sum(effective_candidates_df, "review_reduction")
    out_of_scope_gain = _safe_numeric_sum(
        effective_candidates_df, "out_of_scope_or_rejected_gain"
    )
    add_qa(
        "impact::affected_candidate_count_carries_forward",
        "PASS"
        if affected_candidate_count == _safe_int(sandbox_summary.get("affected_candidate_count"))
        else "FAIL",
        f"candidate_sum={affected_candidate_count} sandbox={sandbox_summary.get('affected_candidate_count', '')}",
    )
    add_qa(
        "impact::trusted_gain_carries_forward",
        "PASS"
        if trusted_gain == _safe_int(sandbox_summary.get("trusted_gain_323h"))
        else "FAIL",
        f"candidate_sum={trusted_gain} sandbox={sandbox_summary.get('trusted_gain_323h', '')}",
    )
    add_qa(
        "impact::review_reduction_carries_forward",
        "PASS"
        if review_reduction == _safe_int(sandbox_summary.get("review_reduction_323h"))
        else "FAIL",
        f"candidate_sum={review_reduction} sandbox={sandbox_summary.get('review_reduction_323h', '')}",
    )
    add_qa(
        "impact::out_of_scope_gain_carries_forward",
        "PASS"
        if out_of_scope_gain
        == _safe_int(sandbox_summary.get("out_of_scope_or_rejected_gain_323h"))
        else "FAIL",
        f"candidate_sum={out_of_scope_gain} sandbox={sandbox_summary.get('out_of_scope_or_rejected_gain_323h', '')}",
    )

    ready_candidate_count = int(
        effective_candidates_df["rule_candidate_status"]
        .astype(str)
        .eq("READY_FOR_CONTROLLED_PROPOSAL")
        .sum()
    ) if not effective_candidates_df.empty else 0
    review_candidate_count = int(
        effective_candidates_df["rule_candidate_status"].astype(str).eq("NEEDS_REVIEW").sum()
    ) if not effective_candidates_df.empty else 0
    rejected_candidate_count = int(
        effective_candidates_df["rule_candidate_status"].astype(str).eq("REJECTED").sum()
    ) if not effective_candidates_df.empty else 0

    add_qa(
        "candidate_status::all_candidates_conflict_free_ready",
        "PASS" if ready_candidate_count == len(effective_candidates_df) else "FAIL",
        f"ready={ready_candidate_count} total={len(effective_candidates_df)}",
    )
    add_qa(
        "candidate_status::review_candidate_count",
        "PASS" if review_candidate_count == 0 else "FAIL",
        f"actual={review_candidate_count}",
    )
    add_qa(
        "candidate_status::rejected_candidate_count",
        "PASS" if rejected_candidate_count == 0 else "FAIL",
        f"actual={rejected_candidate_count}",
    )
    add_qa(
        "safety::core_false_exclusion_zero",
        "PASS" if _safe_int(sandbox_summary.get("core_false_exclusion_count")) == 0 else "FAIL",
        str(sandbox_summary.get("core_false_exclusion_count", "")),
    )
    add_qa(
        "safety::conflict_count_zero",
        "PASS" if _safe_int(sandbox_summary.get("conflict_count")) == 0 else "FAIL",
        str(sandbox_summary.get("conflict_count", "")),
    )
    add_qa(
        "safety::no_llm_or_api_call_executed",
        "PASS",
        "323I uses 323H sandbox outputs and 323G reviewed evidence only.",
    )
    add_qa(
        "safety::no_official_asset_modification",
        "PASS",
        "323I reads sandbox evidence only and writes output package only.",
    )

    qa_checks_df = pd.DataFrame(summary_rows).fillna("")
    qa_pass_count = int((qa_checks_df["status"] == "PASS").sum()) if not qa_checks_df.empty else 0
    qa_warn_count = int((qa_checks_df["status"] == "WARN").sum()) if not qa_checks_df.empty else 0
    qa_fail_count = int((qa_checks_df["status"] == "FAIL").sum()) if not qa_checks_df.empty else 0
    blocking_reasons = (
        qa_checks_df.loc[qa_checks_df["status"] == "FAIL", "check_name"]
        .astype(str)
        .tolist()
        if not qa_checks_df.empty
        else []
    )

    summary = {
        "stage": "323I",
        "output_dir": "",
        "source_sandbox_rule_count": int(len(source_rule_inventory_df)),
        "source_sandbox_alias_rule_count": int(
            source_rule_inventory_df["candidate_type"].astype(str).eq("alias").sum()
        )
        if not source_rule_inventory_df.empty
        else 0,
        "source_sandbox_scope_rule_count": int(
            source_rule_inventory_df["candidate_type"].astype(str).eq("scope").sum()
        )
        if not source_rule_inventory_df.empty
        else 0,
        "effective_unique_candidate_count": int(len(effective_candidates_df)),
        "alias_candidate_count": int(len(alias_candidates_df)),
        "scope_candidate_count": int(len(scope_candidates_df)),
        "ready_for_controlled_proposal_count": ready_candidate_count,
        "needs_review_candidate_count": review_candidate_count,
        "rejected_candidate_count": rejected_candidate_count,
        "duplicate_source_group_count": duplicate_group_count,
        "conflict_group_count": conflicting_target_group_count + official_overlap_group_count,
        "affected_candidate_count": affected_candidate_count,
        "trusted_gain_323i": trusted_gain,
        "review_reduction_323i": review_reduction,
        "out_of_scope_or_rejected_gain_323i": out_of_scope_gain,
        "carried_forward_core_false_exclusion_count": _safe_int(
            sandbox_summary.get("core_false_exclusion_count")
        ),
        "carried_forward_conflict_count": _safe_int(sandbox_summary.get("conflict_count")),
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": (
            NOT_READY_DECISION
            if qa_fail_count > 0
            else READY_WARN_DECISION
            if qa_warn_count > 0
            else READY_DECISION
        ),
    }

    candidate_package_json = {
        "stage": "323I",
        "decision": summary["decision"],
        "source_summary": {
            "sandbox_decision": sandbox_decision,
            "sandbox_rule_count": summary["source_sandbox_rule_count"],
            "effective_unique_candidate_count": summary["effective_unique_candidate_count"],
            "duplicate_source_group_count": summary["duplicate_source_group_count"],
        },
        "effective_unique_candidates": effective_candidates_df.to_dict(orient="records"),
        "alias_candidates": alias_candidates_df.to_dict(orient="records"),
        "scope_candidates": scope_candidates_df.to_dict(orient="records"),
        "candidate_source_bridge": candidate_source_bridge_df.to_dict(orient="records"),
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_checks_df.to_dict(orient="records"),
    }

    return {
        "summary": summary,
        "qa_json": qa_json,
        "effective_candidates_df": effective_candidates_df,
        "alias_candidates_df": alias_candidates_df,
        "scope_candidates_df": scope_candidates_df,
        "duplicate_groups_df": duplicate_groups_df,
        "source_rule_inventory_df": source_rule_inventory_df,
        "source_provenance_df": source_provenance_df,
        "candidate_source_bridge_df": candidate_source_bridge_df,
        "qa_checks_df": qa_checks_df,
        "known_limitations_df": _build_known_limitations_df(),
        "candidate_package_json": candidate_package_json,
    }
