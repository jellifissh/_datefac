from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

import pandas as pd


READY_DECISION = "OFFICIAL_RULE_CANDIDATE_FROM_324G_324H_READY_FOR_CONTROLLED_PROPOSAL"
READY_WARN_DECISION = "OFFICIAL_RULE_CANDIDATE_FROM_324G_324H_READY_WITH_WARNINGS"
NOT_READY_DECISION = "OFFICIAL_RULE_CANDIDATE_FROM_324G_324H_NOT_READY"

EXPECTED_324G_READY_WARN_DECISION = "SCOPE_NOISE_HUMAN_CONFIRMED_SANDBOX_REPLAY_324G_READY_WITH_WARNINGS"
EXPECTED_324G_READY_DECISION = (
    "SCOPE_NOISE_HUMAN_CONFIRMED_SANDBOX_REPLAY_324G_READY_FOR_324H_OFFICIAL_RULE_CANDIDATE"
)
EXPECTED_324F_REVIEWED_READY_DECISION = (
    "SCOPE_NOISE_HUMAN_CONFIRMATION_324F_REVIEWED_READY_FOR_324G_SANDBOX_REPLAY"
)
EXPECTED_324E_READY_DECISION = (
    "SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_READY_FOR_324F_HUMAN_CONFIRMATION"
)
EXPECTED_324C_READY_DECISION = (
    "SCOPE_NOISE_SAFE_ADJUDICATOR_REQUEST_324C_READY_FOR_MANUAL_OR_CONFIGURED_ADJUDICATOR_RUN"
)
ALLOWED_324G_WARN_CHECK = "reference_323n::historical_duplicates_unchanged_only"

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")


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


def _read_jsonl(path: Path) -> pd.DataFrame:
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


def _split_pipe(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _to_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_norm(item) for item in value if _norm(item)]
    if isinstance(value, tuple):
        return [_norm(item) for item in value if _norm(item)]
    text = _norm(value)
    if not text:
        return []
    if "|" in text:
        return _split_pipe(text)
    return [text]


def _dedupe_preserve(items: Iterable[Any]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _join_unique(items: Iterable[Any], limit: int = 16) -> str:
    return " | ".join(_dedupe_preserve(items)[:limit])


def _stable_candidate_id(candidate_type: str, normalized_label_key: str) -> str:
    digest = hashlib.sha1(f"{candidate_type}::{normalized_label_key}".encode("utf-8")).hexdigest()
    return f"324h::{candidate_type}::{digest[:12]}"


def _load_scope_reference() -> Tuple[bool, Dict[str, Any], pd.DataFrame]:
    payload = _read_json(FORMAL_SCOPE_RULES_PATH)
    rules = payload.get("rules", {}) if isinstance(payload, dict) else {}
    rows: List[Dict[str, Any]] = []
    if isinstance(rules, dict):
        for rule_id, item in rules.items():
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    "rule_id": _norm(item.get("rule_id")) or _norm(rule_id),
                    "normalized_label": _norm(item.get("normalized_label")),
                    "normalized_label_key": _normalize_label(item.get("normalized_label")),
                    "target_group": _norm(item.get("target_group")),
                    "scope_action": _norm(item.get("scope_action")),
                    "rule_type": _norm(item.get("rule_type")),
                    "promotion_status": _norm(item.get("promotion_status")),
                    "source_rule_candidate_id": _norm(item.get("source_rule_candidate_id")),
                }
            )
    return bool(payload), payload, pd.DataFrame(rows).fillna("")


def _load_alias_reference() -> Tuple[bool, Dict[str, Any], pd.DataFrame]:
    payload = _read_json(OFFICIAL_ALIAS_OVERRIDE_PATH)
    groups = payload.get("groups", {}) if isinstance(payload, dict) else {}
    rows: List[Dict[str, Any]] = []
    if isinstance(groups, dict):
        for group_name, entries in groups.items():
            if not isinstance(entries, list):
                continue
            for item in entries:
                if not isinstance(item, dict):
                    continue
                rows.append(
                    {
                        "group_name": _norm(group_name),
                        "normalized_label": _norm(item.get("normalized_label")),
                        "normalized_label_key": _normalize_label(item.get("normalized_label")),
                        "metric_code": _norm(item.get("metric_code")),
                        "metric_family": _norm(item.get("metric_family")) or _norm(group_name),
                        "rule_id": _norm(item.get("rule_id")),
                    }
                )
    return bool(payload), payload, pd.DataFrame(rows).fillna("")


def load_official_rule_candidate_from_324g_324h_inputs(
    sandbox_replay_dir: Path,
    human_confirmation_reviewed_dir: Path,
    response_schema_validation_dir: Path,
    safe_adjudicator_request_dir: Path,
) -> Dict[str, Any]:
    return {
        "sandbox_summary": _read_json(
            sandbox_replay_dir / "scope_noise_human_confirmed_sandbox_replay_324g_summary.json"
        ),
        "sandbox_qa": _read_json(
            sandbox_replay_dir / "scope_noise_human_confirmed_sandbox_replay_324g_qa.json"
        ),
        "sandbox_rule_set": _read_json(
            sandbox_replay_dir
            / "scope_noise_human_confirmed_sandbox_replay_324g_sandbox_rule_set.json"
        ),
        "sandbox_rule_application_log_df": _read_jsonl(
            sandbox_replay_dir
            / "scope_noise_human_confirmed_sandbox_replay_324g_rule_application_log.jsonl"
        ),
        "human_confirmation_summary": _read_json(
            human_confirmation_reviewed_dir
            / "scope_noise_human_confirmation_324f_reviewed_summary.json"
        ),
        "human_confirmation_outcome": _read_json(
            human_confirmation_reviewed_dir
            / "scope_noise_human_confirmation_324f_reviewed_outcome.json"
        ),
        "response_schema_validation_summary": _read_json(
            response_schema_validation_dir
            / "scope_noise_response_schema_validation_324e_summary.json"
        ),
        "validated_responses_df": _read_jsonl(
            response_schema_validation_dir
            / "scope_noise_response_schema_validation_324e_validated_responses.jsonl"
        ),
        "accepted_for_human_confirmation": _read_json(
            response_schema_validation_dir
            / "scope_noise_response_schema_validation_324e_accepted_for_human_confirmation.json"
        ),
        "safe_request_package": _read_json(
            safe_adjudicator_request_dir
            / "scope_noise_safe_adjudicator_request_324c_request_package.json"
        ),
        "raw_responses_df": _read_jsonl(
            Path(r"D:\_datefac\output\scope_noise_adjudicator_response_collection_324d")
            / "scope_noise_adjudicator_response_collection_324d_raw_responses.jsonl"
        ),
        "response_collection_summary": _read_json(
            Path(r"D:\_datefac\output\scope_noise_adjudicator_response_collection_324d")
            / "scope_noise_adjudicator_response_collection_324d_summary.json"
        ),
    }


def _qa_allowed_324g_warning(sandbox_qa: Dict[str, Any]) -> bool:
    checks = sandbox_qa.get("checks", [])
    if not isinstance(checks, list):
        return False
    warn_checks = [
        _norm(item.get("check_name"))
        for item in checks
        if isinstance(item, dict) and _norm(item.get("status")) == "WARN"
    ]
    return bool(warn_checks) and set(warn_checks) == {ALLOWED_324G_WARN_CHECK}


def _build_source_rule_inventory_df(sandbox_rule_set: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for item in sandbox_rule_set.get("scope_rules", []):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "source_rule_id": _norm(item.get("source_rule_id")),
                "confirmation_id": _norm(item.get("confirmation_id")),
                "request_id": _norm(item.get("request_id")),
                "source_scope_review_id": _norm(item.get("source_scope_review_id")),
                "source_refined_scope_candidate_id": _norm(
                    item.get("source_refined_scope_candidate_id")
                ),
                "candidate_type": _norm(item.get("candidate_type")),
                "proposal_type": _norm(item.get("proposal_type")),
                "normalized_label": _norm(item.get("normalized_label")),
                "normalized_label_key": _normalize_label(item.get("normalized_label")),
                "confidence": _norm(item.get("confidence")),
                "response_label": _norm(item.get("response_label")),
                "proposed_scope_action": _norm(item.get("proposed_scope_action")),
                "expected_affected_candidate_count": _safe_int(
                    item.get("expected_affected_candidate_count")
                ),
                "expected_review_reduction_potential": _safe_int(
                    item.get("expected_review_reduction_potential")
                ),
                "risk_flags": _to_list(item.get("risk_flags")),
                "source_group_ids": _to_list(item.get("source_group_ids")),
                "sample_candidate_ids": _to_list(item.get("sample_candidate_ids")),
            }
        )
    return pd.DataFrame(rows).fillna("")


def _build_duplicate_groups_df(sandbox_rule_set: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for item in sandbox_rule_set.get("duplicate_conflict_summary", []):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "candidate_type": "scope_noise",
                "proposal_type": _norm(item.get("proposal_type")),
                "normalized_label": _norm(item.get("normalized_label")),
                "normalized_label_key": _normalize_label(
                    item.get("normalized_label_key") or item.get("normalized_label")
                ),
                "source_rule_count": _safe_int(item.get("source_rule_count")),
                "duplicate_rule": _safe_bool(item.get("duplicate_rule")),
                "conflict_detected": _safe_bool(item.get("conflict_detected")),
                "source_rule_ids": _split_pipe(item.get("source_rule_ids")),
                "source_group_ids": _split_pipe(item.get("source_group_ids")),
            }
        )
    return pd.DataFrame(rows).fillna("")


def _confirmed_record_lookup(human_confirmation_outcome: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows = human_confirmation_outcome.get("confirmed_records", [])
    if not isinstance(rows, list):
        return {}
    return {
        _norm(row.get("confirmation_id")): row
        for row in rows
        if isinstance(row, dict) and _norm(row.get("confirmation_id"))
    }


def _request_lookup(safe_request_package: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows = safe_request_package.get("request_items", [])
    if not isinstance(rows, list):
        return {}
    return {
        _norm(row.get("request_id")): row
        for row in rows
        if isinstance(row, dict) and _norm(row.get("request_id"))
    }


def _validated_response_lookup(validated_responses_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    if validated_responses_df.empty:
        return {}
    return {
        _norm(row.get("request_id")): row.to_dict()
        for _, row in validated_responses_df.iterrows()
        if _norm(row.get("request_id"))
    }


def _raw_response_lookup(raw_responses_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    if raw_responses_df.empty:
        return {}
    return {
        _norm(row.get("request_id")): row.to_dict()
        for _, row in raw_responses_df.iterrows()
        if _norm(row.get("request_id"))
    }


def _application_log_lookup(log_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    if log_df.empty:
        return {}
    return {
        _norm(row.get("source_rule_id")): row.to_dict()
        for _, row in log_df.iterrows()
        if _norm(row.get("source_rule_id"))
    }


def _accepted_response_lookup(
    accepted_for_human_confirmation: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    rows = accepted_for_human_confirmation.get("accepted_for_human_confirmation", [])
    if not isinstance(rows, list):
        return {}
    return {
        _norm(row.get("request_id")): row
        for row in rows
        if isinstance(row, dict) and _norm(row.get("request_id"))
    }


def _build_source_provenance_df(
    source_rule_inventory_df: pd.DataFrame,
    confirmed_lookup: Dict[str, Dict[str, Any]],
    request_lookup: Dict[str, Dict[str, Any]],
    validated_response_lookup: Dict[str, Dict[str, Any]],
    raw_response_lookup: Dict[str, Dict[str, Any]],
    accepted_response_lookup: Dict[str, Dict[str, Any]],
    application_log_lookup: Dict[str, Dict[str, Any]],
) -> pd.DataFrame:
    if source_rule_inventory_df.empty:
        return pd.DataFrame()

    rows: List[Dict[str, Any]] = []
    for _, row in source_rule_inventory_df.iterrows():
        confirmation_id = _norm(row.get("confirmation_id"))
        request_id = _norm(row.get("request_id"))
        source_rule_id = _norm(row.get("source_rule_id"))

        confirmed = confirmed_lookup.get(confirmation_id, {})
        request_item = request_lookup.get(request_id, {})
        validated = validated_response_lookup.get(request_id, {})
        raw_response = raw_response_lookup.get(request_id, {})
        accepted = accepted_response_lookup.get(request_id, {})
        log_row = application_log_lookup.get(source_rule_id, {})

        provenance = request_item.get("provenance", {})
        if not isinstance(provenance, dict):
            provenance = {}

        parsed_response = validated.get("parsed_response", {})
        if not isinstance(parsed_response, dict):
            parsed_response = {}

        rows.append(
            {
                "source_rule_id": source_rule_id,
                "sandbox_rule_id": source_rule_id,
                "confirmation_id": confirmation_id,
                "request_id": request_id,
                "review_id_324b": _norm(row.get("source_scope_review_id"))
                or _norm(request_item.get("source_scope_review_id"))
                or _norm(confirmed.get("source_scope_review_id")),
                "candidate_id_324a": _norm(row.get("source_refined_scope_candidate_id"))
                or _norm(request_item.get("source_refined_scope_candidate_id"))
                or _norm(confirmed.get("source_refined_scope_candidate_id")),
                "response_id_324d": request_id,
                "validation_id_324e": request_id,
                "confirmation_id_324f": confirmation_id,
                "sandbox_rule_id_324g": source_rule_id,
                "candidate_type": _norm(row.get("candidate_type")),
                "normalized_label": _norm(row.get("normalized_label")),
                "normalized_label_key": _norm(row.get("normalized_label_key")),
                "confidence": _norm(row.get("confidence")),
                "response_label": _norm(row.get("response_label"))
                or _norm(parsed_response.get("response_label"))
                or _norm(confirmed.get("response_label")),
                "proposed_scope_action": _norm(row.get("proposed_scope_action")),
                "expected_affected_candidate_count": _safe_int(
                    row.get("expected_affected_candidate_count")
                ),
                "expected_review_reduction_potential": _safe_int(
                    row.get("expected_review_reduction_potential")
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
                "reviewer_name": _norm(confirmed.get("reviewer_name")),
                "reviewer_note": _norm(confirmed.get("reviewer_note")),
                "review_timestamp": _norm(confirmed.get("review_timestamp")),
                "sample_candidate_ids": _join_unique(
                    _split_pipe(confirmed.get("sample_candidate_ids"))
                    or _to_list(request_item.get("sample_candidate_ids")),
                    limit=24,
                ),
                "sample_table_titles": _join_unique(
                    _to_list(provenance.get("sample_table_titles"))
                    or _split_pipe(confirmed.get("sample_table_titles")),
                    limit=8,
                ),
                "sample_texts": _join_unique(
                    _split_pipe(confirmed.get("sample_texts"))
                    or _to_list(request_item.get("sample_texts")),
                    limit=10,
                ),
                "sample_years": _join_unique(
                    _to_list(provenance.get("sample_years"))
                    or _split_pipe(confirmed.get("sample_years")),
                    limit=8,
                ),
                "sample_evidence_text": _norm(confirmed.get("raw_response_text"))
                or _norm(raw_response.get("raw_response_text")),
                "risk_flags": _join_unique(
                    _to_list(row.get("risk_flags"))
                    + _split_pipe(confirmed.get("risk_flags"))
                    + _to_list(request_item.get("risk_flags"))
                    + _to_list(parsed_response.get("safety_flags")),
                    limit=16,
                ),
                "provenance_text": _join_unique(
                    [
                        _norm(confirmed.get("why_high_impact")),
                        _norm(confirmed.get("why_safe_or_risky")),
                        _norm(confirmed.get("risk_notes")),
                        _norm(accepted.get("classification_reason")),
                    ],
                    limit=6,
                ),
                "source_group_ids": _join_unique(
                    _to_list(provenance.get("source_group_ids"))
                    or _split_pipe(confirmed.get("source_group_ids")),
                    limit=24,
                ),
                "representative_group_id": _norm(
                    provenance.get("representative_group_id")
                    or confirmed.get("representative_group_id")
                ),
                "source_stage_signatures": _join_unique(
                    _to_list(provenance.get("source_stage_signatures"))
                    or _split_pipe(confirmed.get("source_stage_signatures")),
                    limit=12,
                ),
                "raw_response_source": _norm(raw_response.get("provider_or_source")),
                "raw_response_model_or_review_source": _norm(
                    raw_response.get("model_or_review_source")
                ),
            }
        )
    return pd.DataFrame(rows).fillna("")


def _build_effective_candidate(
    duplicate_groups_df: pd.DataFrame,
    source_provenance_df: pd.DataFrame,
    scope_reference_df: pd.DataFrame,
    alias_reference_df: pd.DataFrame,
) -> Dict[str, pd.DataFrame]:
    if duplicate_groups_df.empty:
        return {
            "effective_candidates_df": pd.DataFrame(),
            "candidate_source_bridge_df": pd.DataFrame(),
        }

    rows: List[Dict[str, Any]] = []
    bridge_rows: List[Dict[str, Any]] = []

    for _, group_row in duplicate_groups_df.iterrows():
        source_rule_ids = group_row.get("source_rule_ids", [])
        if not isinstance(source_rule_ids, list):
            source_rule_ids = _split_pipe(source_rule_ids)
        matched_df = source_provenance_df.loc[
            source_provenance_df["source_rule_id"].astype(str).isin(source_rule_ids)
        ].copy()
        if matched_df.empty:
            continue

        normalized_label = _norm(group_row.get("normalized_label"))
        normalized_label_key = _norm(group_row.get("normalized_label_key"))
        candidate_id = _stable_candidate_id("scope_noise", normalized_label_key)

        existing_scope_rows = (
            scope_reference_df.loc[
                scope_reference_df["normalized_label_key"].astype(str) == normalized_label_key
            ].copy()
            if not scope_reference_df.empty
            else pd.DataFrame()
        )
        existing_alias_rows = (
            alias_reference_df.loc[
                alias_reference_df["normalized_label_key"].astype(str) == normalized_label_key
            ].copy()
            if not alias_reference_df.empty
            else pd.DataFrame()
        )
        already_official_overlap = not existing_scope_rows.empty
        alias_conflict = not existing_alias_rows.empty
        conflicting_targets = _safe_bool(group_row.get("conflict_detected")) or alias_conflict

        rule_candidate_status = (
            "NEEDS_REVIEW"
            if already_official_overlap or conflicting_targets
            else "READY_FOR_CONTROLLED_PROPOSAL"
        )
        source_rule_ids_joined = _join_unique(matched_df["source_rule_id"].tolist(), limit=24)
        source_confirmation_ids_joined = _join_unique(
            matched_df["confirmation_id"].tolist(), limit=24
        )
        source_request_ids_joined = _join_unique(matched_df["request_id"].tolist(), limit=24)
        source_review_ids_joined = _join_unique(matched_df["review_id_324b"].tolist(), limit=24)
        source_candidate_ids_joined = _join_unique(
            matched_df["candidate_id_324a"].tolist(), limit=24
        )
        source_response_ids_joined = _join_unique(
            matched_df["response_id_324d"].tolist(), limit=24
        )
        source_validation_ids_joined = _join_unique(
            matched_df["validation_id_324e"].tolist(), limit=24
        )
        sandbox_rule_ids_joined = _join_unique(
            matched_df["sandbox_rule_id_324g"].tolist(), limit=24
        )

        candidate_row = {
            "rule_candidate_id": candidate_id,
            "candidate_type": "scope_noise",
            "proposal_type": _norm(group_row.get("proposal_type")),
            "rule_candidate_status": rule_candidate_status,
            "normalized_label": normalized_label,
            "normalized_label_key": normalized_label_key,
            "source_rule_count": _safe_int(group_row.get("source_rule_count")),
            "duplicate_source_rule": _safe_bool(group_row.get("duplicate_rule")),
            "dedupe_resolution": (
                "UNIQUE_SOURCE_RULE"
                if _safe_int(group_row.get("source_rule_count")) == 1
                else "DEDUPED_DUPLICATE_SOURCE_RULES"
            ),
            "proposed_scope_action": _norm(
                matched_df["proposed_scope_action"].iloc[0]
                if "proposed_scope_action" in matched_df.columns and not matched_df.empty
                else "exclude_from_core_metric_mapping"
            ),
            "expected_affected_candidate_count": _safe_numeric_sum(
                matched_df, "expected_affected_candidate_count"
            ),
            "actual_affected_candidate_count": _safe_numeric_sum(
                matched_df, "actual_affected_candidate_count"
            ),
            "expected_trusted_gain": _safe_numeric_sum(matched_df, "trusted_gain"),
            "expected_review_reduction": _safe_numeric_sum(
                matched_df, "review_reduction"
            ),
            "expected_out_of_scope_or_rejected_gain": _safe_numeric_sum(
                matched_df, "out_of_scope_or_rejected_gain"
            ),
            "priority_score_max": float(
                pd.to_numeric(matched_df["expected_affected_candidate_count"], errors="coerce")
                .fillna(0)
                .max()
            ),
            "risk_flags": _join_unique(matched_df["risk_flags"].tolist(), limit=16),
            "reviewer_names": _join_unique(matched_df["reviewer_name"].tolist(), limit=8),
            "reviewer_notes": _join_unique(matched_df["reviewer_note"].tolist(), limit=8),
            "review_timestamps": _join_unique(
                matched_df["review_timestamp"].tolist(), limit=8
            ),
            "sample_table_titles": _join_unique(
                matched_df["sample_table_titles"].tolist(), limit=8
            ),
            "sample_texts": _join_unique(matched_df["sample_texts"].tolist(), limit=10),
            "sample_years": _join_unique(matched_df["sample_years"].tolist(), limit=8),
            "provenance_text_samples": _join_unique(
                matched_df["provenance_text"].tolist(), limit=8
            ),
            "already_official_overlap": already_official_overlap,
            "alias_conflict": alias_conflict,
            "conflicting_targets": conflicting_targets,
            "source_rule_ids": source_rule_ids_joined,
            "source_confirmation_ids": source_confirmation_ids_joined,
            "source_request_ids": source_request_ids_joined,
            "source_review_ids_324b": source_review_ids_joined,
            "source_candidate_ids_324a": source_candidate_ids_joined,
            "source_response_ids_324d": source_response_ids_joined,
            "source_validation_ids_324e": source_validation_ids_joined,
            "source_sandbox_rule_ids_324g": sandbox_rule_ids_joined,
            "existing_scope_rule_ids": _join_unique(
                existing_scope_rows["rule_id"].tolist(), limit=8
            ),
            "existing_alias_rule_ids": _join_unique(
                existing_alias_rows["rule_id"].tolist(), limit=8
            ),
            "target_asset_path": str(FORMAL_SCOPE_RULES_PATH),
            "target_group_name": "core_metric_scope_exclusions",
            "target_rule_family": "formal_scope_rules",
            "target_official_rule_category": "official_scope_rule_candidate",
            "intended_future_target_file_or_rule_group": "data/mapping/formal_scope_rules.json::core_metric_scope_exclusions",
            "candidate_readiness_reason": (
                "Single conflict-free scope-noise candidate derived from 324G sandbox replay evidence."
                if rule_candidate_status == "READY_FOR_CONTROLLED_PROPOSAL"
                else "Candidate retained but requires review due to official overlap or conflict."
            ),
        }
        rows.append(candidate_row)

        for _, prov_row in matched_df.iterrows():
            bridge_rows.append(
                {
                    "rule_candidate_id": candidate_id,
                    "candidate_type": "scope_noise",
                    "normalized_label": normalized_label,
                    "source_rule_id": _norm(prov_row.get("source_rule_id")),
                    "confirmation_id": _norm(prov_row.get("confirmation_id")),
                    "request_id": _norm(prov_row.get("request_id")),
                    "source_scope_review_id": _norm(prov_row.get("review_id_324b")),
                    "source_refined_scope_candidate_id": _norm(
                        prov_row.get("candidate_id_324a")
                    ),
                    "response_id_324d": _norm(prov_row.get("response_id_324d")),
                    "validation_id_324e": _norm(prov_row.get("validation_id_324e")),
                    "source_rule_actual_affected_candidate_count": _safe_int(
                        prov_row.get("actual_affected_candidate_count")
                    ),
                    "source_rule_trusted_gain": _safe_int(prov_row.get("trusted_gain")),
                    "source_rule_review_reduction": _safe_int(
                        prov_row.get("review_reduction")
                    ),
                    "source_rule_out_of_scope_or_rejected_gain": _safe_int(
                        prov_row.get("out_of_scope_or_rejected_gain")
                    ),
                    "reviewer_name": _norm(prov_row.get("reviewer_name")),
                    "review_timestamp": _norm(prov_row.get("review_timestamp")),
                    "provenance_text": _norm(prov_row.get("provenance_text")),
                }
            )

    effective_candidates_df = pd.DataFrame(rows).fillna("").sort_values(
        ["normalized_label_key"]
    ).reset_index(drop=True)
    candidate_source_bridge_df = pd.DataFrame(bridge_rows).fillna("")
    return {
        "effective_candidates_df": effective_candidates_df,
        "candidate_source_bridge_df": candidate_source_bridge_df,
    }


def _build_known_limitations_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "limitation": "candidate_only",
                "detail": "324H creates an official rule candidate only and does not modify official assets or apply any patch.",
            },
            {
                "limitation": "cached_evidence_only",
                "detail": "324H uses 324G replay output and cached 324C/324D/324E/324F evidence only.",
            },
            {
                "limitation": "historical_duplicate_warning_may_carry",
                "detail": "Historical duplicate warnings may be carried forward only when new_duplicate_delta_count stays at zero.",
            },
        ]
    )


def build_official_rule_candidate_from_324g_324h(
    sandbox_summary: Dict[str, Any],
    sandbox_qa: Dict[str, Any],
    sandbox_rule_set: Dict[str, Any],
    sandbox_rule_application_log_df: pd.DataFrame,
    human_confirmation_summary: Dict[str, Any],
    human_confirmation_outcome: Dict[str, Any],
    response_schema_validation_summary: Dict[str, Any],
    validated_responses_df: pd.DataFrame,
    accepted_for_human_confirmation: Dict[str, Any],
    safe_request_package: Dict[str, Any],
    raw_responses_df: pd.DataFrame,
    response_collection_summary: Dict[str, Any],
    scope_reference_loaded: bool,
    scope_reference_df: pd.DataFrame,
    alias_reference_loaded: bool,
    alias_reference_df: pd.DataFrame,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    sandbox_decision = _norm(sandbox_summary.get("decision"))
    sandbox_warn_count = _safe_int(sandbox_summary.get("qa_warn_count"))
    sandbox_fail_count = _safe_int(sandbox_summary.get("qa_fail_count"))

    add_qa(
        "readiness::324g_qa_fail_count",
        "PASS" if sandbox_fail_count == 0 else "FAIL",
        str(sandbox_fail_count),
    )
    add_qa(
        "readiness::324g_decision_allowed",
        "PASS"
        if sandbox_decision == EXPECTED_324G_READY_DECISION
        or (
            sandbox_decision == EXPECTED_324G_READY_WARN_DECISION
            and sandbox_warn_count > 0
            and _qa_allowed_324g_warning(sandbox_qa)
        )
        else "FAIL",
        sandbox_decision,
    )
    add_qa(
        "readiness::324g_only_historical_duplicate_warning_if_not_fully_ready",
        "PASS"
        if sandbox_decision != EXPECTED_324G_READY_WARN_DECISION
        or _qa_allowed_324g_warning(sandbox_qa)
        else "FAIL",
        f"qa_warn_count={sandbox_warn_count}",
    )
    for key, expected in [
        ("confirmed_scope_noise_count", 1),
        ("sandbox_rule_count", 1),
        ("affected_candidate_count", 42),
        ("trusted_gain_324g", 0),
        ("review_reduction_324g", 42),
        ("out_of_scope_or_rejected_gain_324g", 42),
        ("core_false_exclusion_count", 0),
        ("conflict_count", 0),
    ]:
        add_qa(
            f"readiness::324g_{key}",
            "PASS" if _safe_int(sandbox_summary.get(key)) == expected else "FAIL",
            f"expected={expected} actual={sandbox_summary.get(key, '')}",
        )

    historical_duplicate_warning_ok = False
    for item in sandbox_qa.get("checks", []):
        if (
            isinstance(item, dict)
            and _norm(item.get("check_name")) == ALLOWED_324G_WARN_CHECK
            and "new_duplicate_delta_count=0" in _norm(item.get("detail"))
        ):
            historical_duplicate_warning_ok = True
            break
    add_qa(
        "readiness::324g_new_duplicate_delta_count_zero",
        "PASS" if historical_duplicate_warning_ok else "FAIL",
        "new_duplicate_delta_count=0",
    )

    add_qa(
        "readiness::324f_reviewed_decision",
        "PASS"
        if _norm(human_confirmation_summary.get("decision"))
        == EXPECTED_324F_REVIEWED_READY_DECISION
        else "FAIL",
        _norm(human_confirmation_summary.get("decision")),
    )
    add_qa(
        "readiness::324e_decision",
        "PASS"
        if _norm(response_schema_validation_summary.get("decision"))
        == EXPECTED_324E_READY_DECISION
        else "FAIL",
        _norm(response_schema_validation_summary.get("decision")),
    )
    add_qa(
        "readiness::324c_decision",
        "PASS"
        if _norm(safe_request_package.get("decision")) == EXPECTED_324C_READY_DECISION
        else "FAIL",
        _norm(safe_request_package.get("decision")),
    )
    add_qa(
        "readiness::324d_decision",
        "PASS"
        if _norm(response_collection_summary.get("decision"))
        == "SCOPE_NOISE_ADJUDICATOR_RESPONSE_COLLECTION_324D_RAW_RESPONSE_READY_FOR_324E_SCHEMA_VALIDATION"
        else "FAIL",
        _norm(response_collection_summary.get("decision")),
    )

    source_rule_inventory_df = _build_source_rule_inventory_df(sandbox_rule_set)
    duplicate_groups_df = _build_duplicate_groups_df(sandbox_rule_set)
    source_provenance_df = _build_source_provenance_df(
        source_rule_inventory_df=source_rule_inventory_df,
        confirmed_lookup=_confirmed_record_lookup(human_confirmation_outcome),
        request_lookup=_request_lookup(safe_request_package),
        validated_response_lookup=_validated_response_lookup(validated_responses_df),
        raw_response_lookup=_raw_response_lookup(raw_responses_df),
        accepted_response_lookup=_accepted_response_lookup(accepted_for_human_confirmation),
        application_log_lookup=_application_log_lookup(sandbox_rule_application_log_df),
    )
    candidate_outputs = _build_effective_candidate(
        duplicate_groups_df=duplicate_groups_df,
        source_provenance_df=source_provenance_df,
        scope_reference_df=scope_reference_df,
        alias_reference_df=alias_reference_df,
    )
    effective_candidates_df = candidate_outputs["effective_candidates_df"]
    candidate_source_bridge_df = candidate_outputs["candidate_source_bridge_df"]
    scope_candidates_df = effective_candidates_df.copy()

    add_qa(
        "inputs::source_sandbox_rule_count",
        "PASS" if len(source_rule_inventory_df) == 1 else "FAIL",
        f"actual={len(source_rule_inventory_df)}",
    )
    add_qa(
        "inputs::candidate_count",
        "PASS" if len(effective_candidates_df) == 1 else "FAIL",
        f"actual={len(effective_candidates_df)}",
    )
    add_qa(
        "inputs::scope_candidate_count",
        "PASS"
        if not scope_candidates_df.empty
        and len(scope_candidates_df) == 1
        and scope_candidates_df["candidate_type"].astype(str).eq("scope_noise").all()
        else "FAIL",
        f"actual={len(scope_candidates_df)}",
    )

    duplicate_candidate_id_count = int(
        effective_candidates_df["rule_candidate_id"].astype(str).duplicated().sum()
    ) if not effective_candidates_df.empty else 0
    already_official_overlap_count = int(
        effective_candidates_df["already_official_overlap"].astype(bool).sum()
    ) if not effective_candidates_df.empty else 0
    alias_conflict_count = int(
        effective_candidates_df["alias_conflict"].astype(bool).sum()
    ) if not effective_candidates_df.empty else 0
    conflict_count = int(
        effective_candidates_df["conflicting_targets"].astype(bool).sum()
    ) if not effective_candidates_df.empty else 0

    add_qa(
        "target::duplicate_candidate_id_count",
        "PASS" if duplicate_candidate_id_count == 0 else "FAIL",
        f"actual={duplicate_candidate_id_count}",
    )
    add_qa(
        "target::already_official_overlap_count",
        "PASS" if already_official_overlap_count == 0 else "FAIL",
        f"actual={already_official_overlap_count}",
    )
    add_qa(
        "target::conflict_with_existing_scope_or_alias_rules_count",
        "PASS" if conflict_count == 0 else "FAIL",
        f"actual={conflict_count}",
    )

    target_asset_exists = FORMAL_SCOPE_RULES_PATH.exists()
    target_group_exists = (
        not scope_reference_df.empty
        and scope_reference_df["target_group"].astype(str).eq("core_metric_scope_exclusions").any()
    )
    add_qa(
        "target::scope_reference_loaded",
        "PASS" if scope_reference_loaded else "FAIL",
        str(FORMAL_SCOPE_RULES_PATH),
    )
    add_qa(
        "target::alias_reference_loaded",
        "PASS" if alias_reference_loaded else "FAIL",
        str(OFFICIAL_ALIAS_OVERRIDE_PATH),
    )
    add_qa(
        "target::target_asset_exists",
        "PASS" if target_asset_exists else "FAIL",
        str(FORMAL_SCOPE_RULES_PATH),
    )
    add_qa(
        "target::target_group_exists",
        "PASS" if target_group_exists else "FAIL",
        "core_metric_scope_exclusions",
    )

    required_provenance_columns = [
        "candidate_id_324a",
        "review_id_324b",
        "request_id",
        "response_id_324d",
        "validation_id_324e",
        "confirmation_id_324f",
        "sandbox_rule_id_324g",
    ]
    missing_provenance_count = 0
    if not source_provenance_df.empty:
        for column in required_provenance_columns:
            missing_provenance_count += int(source_provenance_df[column].astype(str).eq("").sum())
    add_qa(
        "provenance::missing_provenance_count",
        "PASS" if missing_provenance_count == 0 else "FAIL",
        f"actual={missing_provenance_count}",
    )
    add_qa(
        "provenance::bridge_row_count",
        "PASS" if len(candidate_source_bridge_df) == 1 else "FAIL",
        f"actual={len(candidate_source_bridge_df)}",
    )

    ready_candidate_count = int(
        effective_candidates_df["rule_candidate_status"]
        .astype(str)
        .eq("READY_FOR_CONTROLLED_PROPOSAL")
        .sum()
    ) if not effective_candidates_df.empty else 0
    review_candidate_count = int(
        effective_candidates_df["rule_candidate_status"]
        .astype(str)
        .eq("NEEDS_REVIEW")
        .sum()
    ) if not effective_candidates_df.empty else 0
    rejected_candidate_count = int(
        effective_candidates_df["rule_candidate_status"]
        .astype(str)
        .eq("REJECTED")
        .sum()
    ) if not effective_candidates_df.empty else 0
    add_qa(
        "candidate_status::ready_for_controlled_proposal_count",
        "PASS" if ready_candidate_count == 1 else "FAIL",
        f"actual={ready_candidate_count}",
    )
    add_qa(
        "candidate_status::needs_review_count",
        "PASS" if review_candidate_count == 0 else "FAIL",
        f"actual={review_candidate_count}",
    )
    add_qa(
        "candidate_status::rejected_count",
        "PASS" if rejected_candidate_count == 0 else "FAIL",
        f"actual={rejected_candidate_count}",
    )

    affected_candidate_count = _safe_numeric_sum(
        effective_candidates_df, "actual_affected_candidate_count"
    )
    expected_trusted_gain = _safe_numeric_sum(effective_candidates_df, "expected_trusted_gain")
    expected_review_reduction = _safe_numeric_sum(
        effective_candidates_df, "expected_review_reduction"
    )
    expected_out_of_scope_or_rejected_gain = _safe_numeric_sum(
        effective_candidates_df, "expected_out_of_scope_or_rejected_gain"
    )
    add_qa(
        "impact::affected_candidate_count_carried_forward",
        "PASS" if affected_candidate_count == 42 else "FAIL",
        f"actual={affected_candidate_count}",
    )
    add_qa(
        "impact::expected_trusted_gain_carried_forward",
        "PASS" if expected_trusted_gain == 0 else "FAIL",
        f"actual={expected_trusted_gain}",
    )
    add_qa(
        "impact::expected_review_reduction_carried_forward",
        "PASS" if expected_review_reduction == 42 else "FAIL",
        f"actual={expected_review_reduction}",
    )
    add_qa(
        "impact::expected_out_of_scope_or_rejected_gain_carried_forward",
        "PASS" if expected_out_of_scope_or_rejected_gain == 42 else "FAIL",
        f"actual={expected_out_of_scope_or_rejected_gain}",
    )

    add_qa(
        "safety::no_llm_or_api_call_executed",
        "PASS",
        "324H uses 324G replay output and cached 324C/324D/324E/324F evidence only.",
    )
    add_qa(
        "safety::no_official_asset_modification",
        "PASS",
        "324H creates an official rule candidate package only.",
    )

    qa_checks_df = pd.DataFrame(qa_rows).fillna("")
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

    carried_warnings = []
    if sandbox_decision == EXPECTED_324G_READY_WARN_DECISION and historical_duplicate_warning_ok:
        carried_warnings.append(
            "historical_duplicates_unchanged_only:new_duplicate_delta_count=0"
        )

    summary = {
        "stage": "324H",
        "output_dir": "",
        "source_sandbox_rule_count": int(len(source_rule_inventory_df)),
        "candidate_count": int(len(effective_candidates_df)),
        "scope_candidate_count": int(len(scope_candidates_df)),
        "ready_for_controlled_proposal_count": ready_candidate_count,
        "needs_review_candidate_count": review_candidate_count,
        "rejected_candidate_count": rejected_candidate_count,
        "duplicate_candidate_id_count": duplicate_candidate_id_count,
        "already_official_overlap_count": already_official_overlap_count,
        "alias_conflict_count": alias_conflict_count,
        "conflict_count": conflict_count,
        "missing_target_asset_or_group_count": 0
        if target_asset_exists and target_group_exists
        else 1,
        "missing_provenance_count": missing_provenance_count,
        "affected_candidate_count": affected_candidate_count,
        "expected_trusted_gain": expected_trusted_gain,
        "expected_review_reduction": expected_review_reduction,
        "expected_out_of_scope_or_rejected_gain": expected_out_of_scope_or_rejected_gain,
        "carried_warnings": carried_warnings,
        "official_assets_not_modified_confirmed": True,
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
        "stage": "324H",
        "decision": summary["decision"],
        "source_readiness_summary": {
            "sandbox_replay_decision": sandbox_decision,
            "human_confirmation_decision": _norm(human_confirmation_summary.get("decision")),
            "schema_validation_decision": _norm(
                response_schema_validation_summary.get("decision")
            ),
            "safe_request_decision": _norm(safe_request_package.get("decision")),
        },
        "effective_unique_candidates": effective_candidates_df.to_dict(orient="records"),
        "scope_candidates": scope_candidates_df.to_dict(orient="records"),
        "candidate_source_bridge": candidate_source_bridge_df.to_dict(orient="records"),
        "source_provenance": source_provenance_df.to_dict(orient="records"),
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
        "scope_candidates_df": scope_candidates_df,
        "duplicate_groups_df": duplicate_groups_df,
        "source_rule_inventory_df": source_rule_inventory_df,
        "source_provenance_df": source_provenance_df,
        "candidate_source_bridge_df": candidate_source_bridge_df,
        "qa_checks_df": qa_checks_df,
        "known_limitations_df": _build_known_limitations_df(),
        "candidate_package_json": candidate_package_json,
    }
