from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

import pandas as pd

from datefac.semantic.human_confirmed_patch_preview import (
    _candidate_passes_trust_gate,
    _normalize_label,
    _split_tags,
    apply_human_confirmed_patches,
    build_remaining_review_burden,
    read_jsonl,
)


EXPECTED_323G_REVIEWED_DECISION = (
    "HUMAN_CONFIRMED_SUGGESTION_PROPOSALS_323G_REVIEWED_READY_FOR_323H_SANDBOX_REPLAY"
)
READY_DECISION = "HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_READY_FOR_323I_OFFICIAL_RULE_CANDIDATES"
READY_WARN_DECISION = "HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_READY_FOR_REVIEW_WITH_WARNINGS"
NOT_READY_DECISION = "HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_NOT_READY"

OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")

CORE_METRIC_CODES = {
    "revenue",
    "net_profit",
    "gross_margin",
    "roe",
    "eps",
    "pe",
    "pb",
    "ev_ebitda",
}

# Sandbox-only target resolution for 323H replay. This does not modify any
# official mapping asset; it only lets confirmed suggestions replay against the
# cached review pool in a deterministic way.
SANDBOX_ALIAS_TARGETS_323H = {
    "ebitda": {
        "metric_code": "ebitda",
        "metric_family": "profitability",
        "canonical_metric_name": "EBITDA",
    },
    "归属母公司净利润": {
        "metric_code": "net_profit",
        "metric_family": "profitability",
        "canonical_metric_name": "Net Profit",
    },
    "归母净利润": {
        "metric_code": "net_profit",
        "metric_family": "profitability",
        "canonical_metric_name": "Net Profit",
    },
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


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


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _join_unique(items: Iterable[Any], limit: int = 8) -> str:
    out: List[str] = []
    seen: Set[str] = set()
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
        if len(out) >= limit:
            break
    return " | ".join(out)


def _safe_numeric_sum(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


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


def _flatten_alias_entries(payload: Dict[str, Any]) -> pd.DataFrame:
    groups = payload.get("groups", {})
    if not isinstance(groups, dict):
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for group_name, items in groups.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            row["target_group"] = _norm(group_name)
            rows.append(row)
    return pd.DataFrame(rows).fillna("")


def _flatten_scope_entries(payload: Dict[str, Any]) -> pd.DataFrame:
    rules = payload.get("rules", {})
    if not isinstance(rules, dict):
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for rule_id, item in rules.items():
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row.setdefault("rule_id", _norm(rule_id))
        rows.append(row)
    return pd.DataFrame(rows).fillna("")


def load_human_confirmed_sandbox_replay_inputs(
    reviewed_confirmation_dir: Path,
    trust_split_dir: Path,
    post_patch_regression_dir: Path,
) -> Dict[str, Any]:
    return {
        "reviewed_summary": _read_json(
            reviewed_confirmation_dir / "human_confirmed_suggestion_proposals_323g_reviewed_summary.json"
        ),
        "reviewed_qa": _read_json(
            reviewed_confirmation_dir / "human_confirmed_suggestion_proposals_323g_reviewed_qa.json"
        ),
        "reviewed_plan": _read_json(
            reviewed_confirmation_dir / "human_confirmed_suggestion_proposals_323g_human_confirmed_plan.json"
        ),
        "trust_summary": _read_json(
            trust_split_dir / "router_mineru_trust_split_322b2_summary.json"
        ),
        "selected_candidates_df": read_jsonl(
            trust_split_dir / "selected_candidate_reclassified_322b2.jsonl"
        ),
        "post_patch_summary": _read_json(
            post_patch_regression_dir / "post_patch_regression_validation_322o_summary.json"
        ),
        "official_alias_df": _flatten_alias_entries(_read_json(OFFICIAL_ALIAS_OVERRIDE_PATH)),
        "official_scope_df": _flatten_scope_entries(_read_json(FORMAL_SCOPE_RULES_PATH)),
    }


def _normalize_risk_flags(value: Any) -> str:
    tags: List[str] = []
    if isinstance(value, str):
        parsed = _parse_literal_payload(value)
        if isinstance(parsed, list):
            tags = [_norm(item) for item in parsed if _norm(item)]
        elif "|" in value:
            tags = _split_tags(value)
        elif _norm(value):
            tags = [_norm(value)]
    elif isinstance(value, (list, tuple)):
        tags = [_norm(item) for item in value if _norm(item)]
    return "|".join(dict.fromkeys(tags))


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
        risk_flags_list = _parse_list(item.get("risk_flags"))
        candidate_label = _norm(item.get("candidate_label"))
        target_label = _norm(item.get("suggested_target_metric_if_any"))
        rows.append(
            {
                "confirmation_id": _norm(item.get("confirmation_id")),
                "request_id": _norm(item.get("request_id")),
                "source_batch_item_id": _norm(item.get("source_batch_item_id")),
                "source_group_id": _norm(item.get("source_group_id")),
                "suggestion_type": _norm(item.get("suggestion_type")),
                "candidate_label": candidate_label,
                "candidate_label_normalized": _normalize_label(candidate_label),
                "target_label": target_label,
                "target_label_normalized": _normalize_label(target_label),
                "suggested_response_label": _norm(item.get("suggested_response_label")),
                "confidence": _norm(item.get("confidence")),
                "rationale": _norm(item.get("rationale")),
                "reviewer_decision": _norm(item.get("reviewer_decision")).upper(),
                "reviewer_note": _norm(item.get("reviewer_note")),
                "reviewer_name": _norm(item.get("reviewer_name")),
                "review_timestamp": _norm(item.get("review_timestamp")),
                "sample_candidate_ids": sample_evidence.get("sample_candidate_ids", []),
                "sample_texts": sample_evidence.get("sample_texts", []),
                "sample_table_titles": sample_evidence.get("sample_table_titles", []),
                "sample_years": sample_evidence.get("sample_years", []),
                "sample_evidence_text": _norm(item.get("sample_evidence_text")),
                "provenance": provenance,
                "provenance_text": _norm(item.get("provenance_text")),
                "expected_impact": expected_impact,
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
                "risk_flags": _normalize_risk_flags(risk_flags_list),
                "sandbox_replay_required": bool(item.get("sandbox_replay_required")),
                "raw_response_reference": raw_response_reference,
            }
        )
    return pd.DataFrame(rows).fillna("")


def _resolve_alias_target(label: str) -> Dict[str, str]:
    direct = SANDBOX_ALIAS_TARGETS_323H.get(label, {})
    if direct:
        return direct
    return SANDBOX_ALIAS_TARGETS_323H.get(_normalize_label(label), {})


def _build_source_level_rule_inventory(confirmed_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    if confirmed_df.empty:
        return pd.DataFrame()
    for _, row in confirmed_df.iterrows():
        suggestion_type = _norm(row.get("suggestion_type"))
        candidate_label = _norm(row.get("candidate_label"))
        source_rule_id = f"323h::{suggestion_type}::{_norm(row.get('confirmation_id'))}"
        target_payload = (
            _resolve_alias_target(_norm(row.get("target_label")))
            if suggestion_type == "alias"
            else {}
        )
        rows.append(
            {
                "source_rule_id": source_rule_id,
                "confirmation_id": _norm(row.get("confirmation_id")),
                "request_id": _norm(row.get("request_id")),
                "source_batch_item_id": _norm(row.get("source_batch_item_id")),
                "source_group_id": _norm(row.get("source_group_id")),
                "suggestion_type": suggestion_type,
                "proposal_type": "alias" if suggestion_type == "alias" else "out_of_scope",
                "normalized_label": candidate_label,
                "normalized_label_key": _normalize_label(candidate_label),
                "candidate_label": candidate_label,
                "target_label": _norm(row.get("target_label")),
                "proposed_metric_code": _norm(target_payload.get("metric_code")),
                "proposed_metric_family": _norm(target_payload.get("metric_family")),
                "canonical_metric_name": _norm(target_payload.get("canonical_metric_name")),
                "proposed_scope_action": (
                    "exclude_from_core_metric_mapping"
                    if suggestion_type == "scope_noise"
                    else ""
                ),
                "suggested_response_label": _norm(row.get("suggested_response_label")),
                "confidence": _norm(row.get("confidence")),
                "rationale": _norm(row.get("rationale")),
                "reviewer_note": _norm(row.get("reviewer_note")),
                "reviewer_name": _norm(row.get("reviewer_name")),
                "review_timestamp": _norm(row.get("review_timestamp")),
                "expected_affected_candidate_count": _safe_int(
                    row.get("expected_affected_candidate_count")
                ),
                "expected_review_reduction_potential": _safe_int(
                    row.get("expected_review_reduction_potential")
                ),
                "priority_score": _safe_float(row.get("priority_score")),
                "sample_table_titles": _join_unique(row.get("sample_table_titles", []), limit=5),
                "sample_row_labels": _join_unique([candidate_label], limit=5),
                "sample_values": _join_unique(row.get("sample_texts", []), limit=8),
                "sample_years": _join_unique(row.get("sample_years", []), limit=5),
                "risk_flags": _norm(row.get("risk_flags")),
                "source_provenance_text": _norm(row.get("provenance_text")),
                "raw_response_reference": json.dumps(
                    row.get("raw_response_reference", {}), ensure_ascii=False
                ),
                "metric_target_resolved": bool(target_payload) if suggestion_type == "alias" else True,
            }
        )
    return pd.DataFrame(rows).fillna("")


def _build_apply_dataframe(source_rule_inventory_df: pd.DataFrame) -> pd.DataFrame:
    if source_rule_inventory_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for _, row in source_rule_inventory_df.iterrows():
        proposal_type = _norm(row.get("proposal_type"))
        entry = {
            "proposal_id": _norm(row.get("source_rule_id")),
            "proposal_type": proposal_type,
            "source_case_id": _norm(row.get("confirmation_id")),
            "normalized_label": _norm(row.get("normalized_label")),
            "sample_table_titles": _norm(row.get("sample_table_titles")),
            "sample_row_labels": _norm(row.get("sample_row_labels")),
            "sample_values": _norm(row.get("sample_values")),
            "risk_flags": _norm(row.get("risk_flags")),
            "affected_candidate_count": _safe_int(row.get("expected_affected_candidate_count")),
            "review_reduction": _safe_int(row.get("expected_review_reduction_potential")),
            "reviewer_decision": "CONFIRM",
            "reviewer_comment": _join_unique(
                [
                    _norm(row.get("reviewer_note")),
                    _norm(row.get("rationale")),
                    _norm(row.get("source_provenance_text")),
                ],
                limit=4,
            ),
        }
        if proposal_type == "alias":
            entry["proposed_metric_code"] = _norm(row.get("proposed_metric_code"))
            entry["proposed_metric_family"] = _norm(row.get("proposed_metric_family"))
        else:
            entry["proposed_scope_action"] = _norm(row.get("proposed_scope_action"))
        rows.append(entry)
    return pd.DataFrame(rows).fillna("")


def _build_duplicate_conflict_df(
    source_rule_inventory_df: pd.DataFrame,
    official_alias_df: pd.DataFrame,
    official_scope_df: pd.DataFrame,
) -> pd.DataFrame:
    if source_rule_inventory_df.empty:
        return pd.DataFrame()

    official_alias_keys = set(
        official_alias_df.get("normalized_label", pd.Series(dtype=str))
        .astype(str)
        .map(_normalize_label)
        .tolist()
    ) if not official_alias_df.empty else set()
    official_scope_keys = set(
        official_scope_df.get("normalized_label", pd.Series(dtype=str))
        .astype(str)
        .map(_normalize_label)
        .tolist()
    ) if not official_scope_df.empty else set()

    duplicate_counts = (
        source_rule_inventory_df.groupby(["proposal_type", "normalized_label_key"], dropna=False)
        .size()
        .rename("source_rule_count")
        .reset_index()
    )
    grouped = source_rule_inventory_df.groupby(
        ["proposal_type", "normalized_label_key"], dropna=False
    )
    rows: List[Dict[str, Any]] = []
    for _, dup_row in duplicate_counts.iterrows():
        proposal_type = _norm(dup_row.get("proposal_type"))
        label_key = _norm(dup_row.get("normalized_label_key"))
        group = grouped.get_group((proposal_type, label_key))
        target_values = sorted(
            {
                _norm(value)
                for value in group.get("proposed_metric_code", pd.Series(dtype=str)).tolist()
                if _norm(value)
            }
        )
        conflicting_targets = proposal_type == "alias" and len(target_values) > 1
        official_conflict = False
        if proposal_type == "alias":
            official_conflict = label_key in official_alias_keys
        else:
            official_conflict = label_key in official_scope_keys
        rows.append(
            {
                "proposal_type": proposal_type,
                "normalized_label": _norm(group.iloc[0].get("normalized_label")),
                "normalized_label_key": label_key,
                "source_rule_count": _safe_int(dup_row.get("source_rule_count")),
                "duplicate_source_rule": _safe_int(dup_row.get("source_rule_count")) > 1,
                "proposed_metric_codes": "|".join(target_values),
                "conflicting_targets": conflicting_targets,
                "already_in_official_assets": official_conflict,
                "source_rule_ids": _join_unique(group["source_rule_id"].astype(str).tolist(), limit=12),
                "source_group_ids": _join_unique(group["source_group_id"].astype(str).tolist(), limit=12),
            }
        )
    return pd.DataFrame(rows).fillna("").sort_values(
        ["proposal_type", "normalized_label_key"], ascending=[True, True]
    ).reset_index(drop=True)


def _build_sandbox_rule_set_json(
    source_rule_inventory_df: pd.DataFrame,
    duplicate_conflict_df: pd.DataFrame,
) -> Dict[str, Any]:
    alias_rules = []
    scope_rules = []
    for _, row in source_rule_inventory_df.iterrows():
        payload = {
            "source_rule_id": _norm(row.get("source_rule_id")),
            "confirmation_id": _norm(row.get("confirmation_id")),
            "request_id": _norm(row.get("request_id")),
            "source_group_id": _norm(row.get("source_group_id")),
            "normalized_label": _norm(row.get("normalized_label")),
            "confidence": _norm(row.get("confidence")),
            "priority_score": _safe_float(row.get("priority_score")),
            "risk_flags": _split_tags(row.get("risk_flags")),
            "expected_affected_candidate_count": _safe_int(
                row.get("expected_affected_candidate_count")
            ),
        }
        if _norm(row.get("proposal_type")) == "alias":
            payload.update(
                {
                    "rule_type": "alias",
                    "target_label": _norm(row.get("target_label")),
                    "proposed_metric_code": _norm(row.get("proposed_metric_code")),
                    "proposed_metric_family": _norm(row.get("proposed_metric_family")),
                    "metric_target_resolved": bool(row.get("metric_target_resolved")),
                }
            )
            alias_rules.append(payload)
        else:
            payload.update(
                {
                    "rule_type": "out_of_scope",
                    "proposed_scope_action": _norm(row.get("proposed_scope_action")),
                }
            )
            scope_rules.append(payload)
    return {
        "stage": "323H",
        "mode": "sandbox_replay_only",
        "source_rule_count": int(len(source_rule_inventory_df)),
        "alias_rule_count": int(len(alias_rules)),
        "scope_rule_count": int(len(scope_rules)),
        "duplicate_conflict_summary": duplicate_conflict_df.to_dict(orient="records"),
        "alias_rules": alias_rules,
        "scope_rules": scope_rules,
    }


def _build_before_after_overview(summary: Dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "metric": "trusted_total",
                "before": _safe_int(summary.get("trusted_total_before_323h")),
                "after": _safe_int(summary.get("trusted_total_after_323h")),
                "delta": _safe_int(summary.get("trusted_gain_323h")),
            },
            {
                "metric": "review_required_total",
                "before": _safe_int(summary.get("review_required_total_before_323h")),
                "after": _safe_int(summary.get("review_required_total_after_323h")),
                "delta": _safe_int(summary.get("review_required_total_after_323h"))
                - _safe_int(summary.get("review_required_total_before_323h")),
            },
            {
                "metric": "rejected_total",
                "before": _safe_int(summary.get("rejected_total_before_323h")),
                "after": _safe_int(summary.get("rejected_total_after_323h")),
                "delta": _safe_int(summary.get("out_of_scope_or_rejected_gain_323h")),
            },
            {
                "metric": "selected_core_trusted_rate",
                "before": _safe_float(summary.get("selected_core_trusted_rate_before_323h")),
                "after": _safe_float(summary.get("selected_core_trusted_rate_after_323h")),
                "delta": round(
                    _safe_float(summary.get("selected_core_trusted_rate_after_323h"))
                    - _safe_float(summary.get("selected_core_trusted_rate_before_323h")),
                    6,
                ),
            },
            {
                "metric": "remaining_unknown_metric_candidate_count",
                "before": _safe_int(summary.get("baseline_unknown_metric_candidate_count")),
                "after": _safe_int(summary.get("remaining_unknown_metric_candidate_count")),
                "delta": _safe_int(summary.get("remaining_unknown_metric_candidate_count"))
                - _safe_int(summary.get("baseline_unknown_metric_candidate_count")),
            },
            {
                "metric": "remaining_unit_unknown_candidate_count",
                "before": _safe_int(summary.get("baseline_unit_unknown_candidate_count")),
                "after": _safe_int(summary.get("remaining_unit_unknown_candidate_count")),
                "delta": _safe_int(summary.get("remaining_unit_unknown_candidate_count"))
                - _safe_int(summary.get("baseline_unit_unknown_candidate_count")),
            },
            {
                "metric": "remaining_manual_review_count",
                "before": _safe_int(summary.get("baseline_manual_review_count")),
                "after": _safe_int(summary.get("remaining_manual_review_count")),
                "delta": _safe_int(summary.get("remaining_manual_review_count"))
                - _safe_int(summary.get("baseline_manual_review_count")),
            },
        ]
    ).fillna("")


def _build_rule_application_overview(
    source_rule_inventory_df: pd.DataFrame,
    patch_impact_df: pd.DataFrame,
) -> pd.DataFrame:
    if source_rule_inventory_df.empty:
        return pd.DataFrame()
    impact_lookup = (
        {
            _norm(row.get("proposal_id")): row.to_dict()
            for _, row in patch_impact_df.iterrows()
        }
        if not patch_impact_df.empty
        else {}
    )
    rows: List[Dict[str, Any]] = []
    for _, row in source_rule_inventory_df.iterrows():
        impact_row = impact_lookup.get(_norm(row.get("source_rule_id")), {})
        rows.append(
            {
                "source_rule_id": _norm(row.get("source_rule_id")),
                "confirmation_id": _norm(row.get("confirmation_id")),
                "proposal_type": _norm(row.get("proposal_type")),
                "normalized_label": _norm(row.get("normalized_label")),
                "expected_affected_candidate_count": _safe_int(
                    row.get("expected_affected_candidate_count")
                ),
                "actual_affected_candidate_count": _safe_int(
                    impact_row.get("affected_candidate_count")
                ),
                "trusted_gain": _safe_int(impact_row.get("trusted_gain")),
                "review_reduction": _safe_int(impact_row.get("review_reduction")),
                "out_of_scope_or_rejected_gain": _safe_int(
                    impact_row.get("rejected_or_out_of_scope_count")
                ),
                "application_status": _norm(impact_row.get("notes")).upper() or "NOT_APPLIED",
                "metric_target_resolved": bool(row.get("metric_target_resolved")),
            }
        )
    return pd.DataFrame(rows).fillna("")


def _build_core_false_exclusion_df(diff_df: pd.DataFrame) -> pd.DataFrame:
    if diff_df.empty:
        return pd.DataFrame()
    temp = diff_df.copy()
    temp["metric_code_before"] = temp.get("metric_code_before", "").astype(str)
    temp["metric_code_after"] = temp.get("metric_code_after", "").astype(str)
    temp["decision_after"] = temp.get("decision_after", "").astype(str)
    mask = temp["decision_after"].eq("rejected_preview") & (
        temp["metric_code_before"].isin(CORE_METRIC_CODES)
        | temp["metric_code_after"].isin(CORE_METRIC_CODES)
    )
    wanted = [
        "candidate_id",
        "proposal_id",
        "patch_id",
        "row_label",
        "table_title",
        "metric_code_before",
        "metric_code_after",
        "decision_before",
        "decision_after",
        "risk_tags_before",
        "risk_tags_after",
    ]
    existing = [column for column in wanted if column in temp.columns]
    return temp.loc[mask, existing].fillna("").reset_index(drop=True)


def _build_alias_scope_contribution_df(patch_impact_df: pd.DataFrame) -> pd.DataFrame:
    if patch_impact_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for proposal_type, group in patch_impact_df.groupby("proposal_type", dropna=False):
        rows.append(
            {
                "proposal_type": proposal_type,
                "rule_count": int(len(group)),
                "affected_candidate_count": _safe_numeric_sum(group, "affected_candidate_count"),
                "trusted_gain": _safe_numeric_sum(group, "trusted_gain"),
                "review_reduction": _safe_numeric_sum(group, "review_reduction"),
                "out_of_scope_or_rejected_gain": _safe_numeric_sum(
                    group, "rejected_or_out_of_scope_count"
                ),
            }
        )
    return pd.DataFrame(rows).fillna("").sort_values("proposal_type").reset_index(drop=True)


def _build_notes_markdown(summary: Dict[str, Any], qa_df: pd.DataFrame) -> str:
    lines = [
        "# Human Confirmed Sandbox Replay 323H",
        "",
        "## Scope",
        "- Sandbox-only replay against cached 322B2 selected candidates.",
        "- No official mapping/override asset was modified.",
        "- No parser, OCR, VLM, LLM, or semantic adjudicator call was executed.",
        "",
        "## Result",
        f"- decision: {summary.get('decision', '')}",
        f"- total_confirmed_suggestion_count: {summary.get('total_confirmed_suggestion_count', 0)}",
        f"- alias_confirmed_suggestion_count: {summary.get('alias_confirmed_suggestion_count', 0)}",
        f"- scope_confirmed_suggestion_count: {summary.get('scope_confirmed_suggestion_count', 0)}",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- trusted_gain_323h: {summary.get('trusted_gain_323h', 0)}",
        f"- review_reduction_323h: {summary.get('review_reduction_323h', 0)}",
        f"- out_of_scope_or_rejected_gain_323h: {summary.get('out_of_scope_or_rejected_gain_323h', 0)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    warning_rows = qa_df.loc[qa_df["status"] == "WARN"] if not qa_df.empty else pd.DataFrame()
    if not warning_rows.empty:
        lines.extend(["## Warnings"])
        for _, row in warning_rows.iterrows():
            lines.append(f"- {_norm(row.get('check_name'))}: {_norm(row.get('detail'))}")
        lines.append("")
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking], ""])
    return "\n".join(lines)


def build_human_confirmed_sandbox_replay(
    reviewed_summary: Dict[str, Any],
    reviewed_qa: Dict[str, Any],
    reviewed_plan: Dict[str, Any],
    trust_summary: Dict[str, Any],
    selected_candidates_df: pd.DataFrame,
    post_patch_summary: Dict[str, Any],
    official_alias_df: pd.DataFrame,
    official_scope_df: pd.DataFrame,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    confirmed_df = _extract_confirmed_suggestions(reviewed_plan)
    source_rule_inventory_df = _build_source_level_rule_inventory(confirmed_df)
    duplicate_conflict_df = _build_duplicate_conflict_df(
        source_rule_inventory_df=source_rule_inventory_df,
        official_alias_df=official_alias_df,
        official_scope_df=official_scope_df,
    )
    sandbox_rule_set_json = _build_sandbox_rule_set_json(
        source_rule_inventory_df=source_rule_inventory_df,
        duplicate_conflict_df=duplicate_conflict_df,
    )

    add_qa(
        "readiness::323g_reviewed_decision",
        "PASS" if _norm(reviewed_summary.get("decision")) == EXPECTED_323G_REVIEWED_DECISION else "FAIL",
        _norm(reviewed_summary.get("decision")),
    )
    add_qa(
        "readiness::323g_reviewed_summary_qa_fail_count",
        "PASS" if _safe_int(reviewed_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(reviewed_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323g_reviewed_qa_json_fail_count",
        "PASS" if _safe_int(reviewed_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(reviewed_qa.get("qa_fail_count", "")),
    )
    for key, expected in [
        ("confirmation_record_count", 11),
        ("confirmed_suggestion_count", 11),
        ("rejected_suggestion_count", 0),
        ("needs_more_info_count", 0),
        ("pending_count", 0),
        ("invalid_decision_count", 0),
    ]:
        add_qa(
            f"readiness::323g_reviewed_{key}",
            "PASS" if _safe_int(reviewed_summary.get(key)) == expected else "FAIL",
            f"expected={expected} actual={reviewed_summary.get(key, '')}",
        )

    total_confirmed_suggestion_count = int(len(confirmed_df))
    alias_confirmed_suggestion_count = int(
        confirmed_df["suggestion_type"].astype(str).eq("alias").sum()
    ) if not confirmed_df.empty else 0
    scope_confirmed_suggestion_count = int(
        confirmed_df["suggestion_type"].astype(str).eq("scope_noise").sum()
    ) if not confirmed_df.empty else 0

    add_qa(
        "confirmed_suggestions::total_count",
        "PASS" if total_confirmed_suggestion_count == 11 else "FAIL",
        f"actual={total_confirmed_suggestion_count}",
    )
    add_qa(
        "confirmed_suggestions::alias_count",
        "PASS" if alias_confirmed_suggestion_count == 2 else "FAIL",
        f"actual={alias_confirmed_suggestion_count}",
    )
    add_qa(
        "confirmed_suggestions::scope_count",
        "PASS" if scope_confirmed_suggestion_count == 9 else "FAIL",
        f"actual={scope_confirmed_suggestion_count}",
    )

    if not source_rule_inventory_df.empty:
        only_confirm = confirmed_df["reviewer_decision"].astype(str).eq("CONFIRM").all()
    else:
        only_confirm = False
    add_qa(
        "confirmed_suggestions::only_confirm_rows_loaded",
        "PASS" if only_confirm else "FAIL",
        f"loaded_count={len(confirmed_df)}",
    )

    metric_target_unresolved_count = int(
        source_rule_inventory_df.loc[
            source_rule_inventory_df["proposal_type"].astype(str) == "alias",
            "metric_target_resolved",
        ]
        .astype(bool)
        .eq(False)
        .sum()
    ) if not source_rule_inventory_df.empty else 0
    add_qa(
        "sandbox_rules::alias_targets_resolved",
        "PASS" if metric_target_unresolved_count == 0 else "WARN",
        f"unresolved_alias_target_count={metric_target_unresolved_count}",
    )

    duplicate_rule_count = int(
        duplicate_conflict_df["duplicate_source_rule"].astype(bool).sum()
    ) if not duplicate_conflict_df.empty else 0
    duplicate_conflicting_target_count = int(
        duplicate_conflict_df["conflicting_targets"].astype(bool).sum()
    ) if not duplicate_conflict_df.empty else 0
    conflict_count = int(
        duplicate_conflict_df["already_in_official_assets"].astype(bool).sum()
    ) if not duplicate_conflict_df.empty else 0

    add_qa(
        "sandbox_rules::duplicate_source_rule_groups",
        "WARN" if duplicate_rule_count > 0 else "PASS",
        f"duplicate_group_count={duplicate_rule_count}",
    )
    add_qa(
        "sandbox_rules::no_conflicting_duplicate_targets",
        "PASS" if duplicate_conflicting_target_count == 0 else "FAIL",
        f"duplicate_conflicting_target_count={duplicate_conflicting_target_count}",
    )
    add_qa(
        "sandbox_rules::no_conflict_with_official_assets",
        "PASS" if conflict_count == 0 else "WARN",
        f"official_conflict_count={conflict_count}",
    )
    add_qa(
        "sandbox_rules::selected_candidate_pool_loaded",
        "PASS" if not selected_candidates_df.empty else "FAIL",
        f"candidate_count={len(selected_candidates_df)}",
    )

    apply_df = _build_apply_dataframe(source_rule_inventory_df)
    applied = apply_human_confirmed_patches(
        accepted_proposals_df=apply_df,
        selected_candidates_df=selected_candidates_df.copy(),
    )

    trusted_before_df = applied["trusted_before_df"]
    review_before_df = applied["review_before_df"]
    rejected_before_df = applied["rejected_before_df"]
    trusted_after_df = applied["trusted_after_df"]
    review_after_df = applied["review_after_df"]
    rejected_after_df = applied["rejected_after_df"]
    diff_df = applied["candidate_before_after_diff_df"].copy()
    patch_impact_df = applied["patch_impact_by_proposal_df"].copy()
    remaining_review_burden_df = build_remaining_review_burden(review_after_df)

    trusted_total_before_323h = int(len(trusted_before_df))
    trusted_total_after_323h = int(len(trusted_after_df))
    review_required_total_before_323h = int(len(review_before_df))
    review_required_total_after_323h = int(len(review_after_df))
    rejected_total_before_323h = int(len(rejected_before_df))
    rejected_total_after_323h = int(len(rejected_after_df))

    trusted_gain_323h = trusted_total_after_323h - trusted_total_before_323h
    review_reduction_323h = (
        review_required_total_before_323h - review_required_total_after_323h
    )
    out_of_scope_or_rejected_gain_323h = (
        rejected_total_after_323h - rejected_total_before_323h
    )
    affected_candidate_count = int(len(diff_df))

    alias_trusted_gain_323h = _safe_numeric_sum(
        patch_impact_df.loc[
            patch_impact_df["proposal_type"].astype(str) == "alias"
        ].copy(),
        "trusted_gain",
    )
    alias_review_reduction_323h = _safe_numeric_sum(
        patch_impact_df.loc[
            patch_impact_df["proposal_type"].astype(str) == "alias"
        ].copy(),
        "review_reduction",
    )
    scope_trusted_gain_323h = _safe_numeric_sum(
        patch_impact_df.loc[
            patch_impact_df["proposal_type"].astype(str) == "out_of_scope"
        ].copy(),
        "trusted_gain",
    )
    scope_review_reduction_323h = _safe_numeric_sum(
        patch_impact_df.loc[
            patch_impact_df["proposal_type"].astype(str) == "out_of_scope"
        ].copy(),
        "review_reduction",
    )
    scope_out_of_scope_or_rejected_gain_323h = _safe_numeric_sum(
        patch_impact_df.loc[
            patch_impact_df["proposal_type"].astype(str) == "out_of_scope"
        ].copy(),
        "rejected_or_out_of_scope_count",
    )

    remaining_unknown_metric_candidate_count = int(
        review_after_df.get("risk_tags_after", pd.Series(dtype=str))
        .astype(str)
        .str.contains(r"(?:^|\|)UNKNOWN_METRIC_CODE(?:$|\|)", regex=True)
        .sum()
    ) if not review_after_df.empty else 0
    remaining_unit_unknown_candidate_count = int(
        review_after_df.get("risk_tags_after", pd.Series(dtype=str))
        .astype(str)
        .str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True)
        .sum()
    ) if not review_after_df.empty else 0
    remaining_manual_review_count = int(len(review_after_df))

    selected_core_trusted_rate_before_323h = round(
        _safe_float(trust_summary.get("selected_core_trusted_rate_after_322b2")), 6
    )
    selected_core_trusted_rate_after_323h = (
        round(trusted_total_after_323h / len(selected_candidates_df), 6)
        if len(selected_candidates_df)
        else 0.0
    )

    add_qa(
        "before_after::candidate_counts_reconcile",
        "PASS"
        if len(selected_candidates_df)
        == trusted_total_after_323h + review_required_total_after_323h + rejected_total_after_323h
        else "FAIL",
        f"input={len(selected_candidates_df)} after_total={trusted_total_after_323h + review_required_total_after_323h + rejected_total_after_323h}",
    )
    add_qa(
        "before_after::trusted_gain_matches_impact_rows",
        "PASS" if trusted_gain_323h == _safe_numeric_sum(patch_impact_df, "trusted_gain") else "FAIL",
        f"summary={trusted_gain_323h} impact={_safe_numeric_sum(patch_impact_df, 'trusted_gain')}",
    )
    add_qa(
        "before_after::review_reduction_matches_impact_rows",
        "PASS"
        if review_reduction_323h == _safe_numeric_sum(patch_impact_df, "review_reduction")
        else "FAIL",
        f"summary={review_reduction_323h} impact={_safe_numeric_sum(patch_impact_df, 'review_reduction')}",
    )
    add_qa(
        "before_after::rejected_gain_matches_impact_rows",
        "PASS"
        if out_of_scope_or_rejected_gain_323h
        == _safe_numeric_sum(patch_impact_df, "rejected_or_out_of_scope_count")
        else "FAIL",
        f"summary={out_of_scope_or_rejected_gain_323h} impact={_safe_numeric_sum(patch_impact_df, 'rejected_or_out_of_scope_count')}",
    )
    add_qa(
        "before_after::affected_count_matches_diff_rows",
        "PASS"
        if affected_candidate_count == _safe_numeric_sum(patch_impact_df, "affected_candidate_count")
        else "FAIL",
        f"summary={affected_candidate_count} impact={_safe_numeric_sum(patch_impact_df, 'affected_candidate_count')}",
    )

    trusted_gate_ok = (
        trusted_after_df.apply(_candidate_passes_trust_gate, axis=1).all()
        if not trusted_after_df.empty
        else True
    )
    no_trusted_regression = trusted_total_after_323h >= trusted_total_before_323h
    selected_core_trusted_rate_not_down = (
        selected_core_trusted_rate_after_323h >= selected_core_trusted_rate_before_323h
    )
    unknown_metric_not_worse = remaining_unknown_metric_candidate_count <= _safe_int(
        trust_summary.get("unknown_metric_candidate_count")
    )
    unit_unknown_not_worse = remaining_unit_unknown_candidate_count <= _safe_int(
        trust_summary.get("unit_unknown_candidate_count")
    )
    manual_review_not_worse = remaining_manual_review_count <= _safe_int(
        trust_summary.get("review_required_total_after_322b2")
    )
    core_false_exclusion_df = _build_core_false_exclusion_df(diff_df)
    core_false_exclusion_count = int(len(core_false_exclusion_df))

    add_qa(
        "safety::trusted_after_candidates_still_pass_deterministic_gate",
        "PASS" if trusted_gate_ok else "FAIL",
        f"trusted_after_count={len(trusted_after_df)}",
    )
    add_qa(
        "safety::no_trusted_regression",
        "PASS" if no_trusted_regression else "FAIL",
        f"before={trusted_total_before_323h} after={trusted_total_after_323h}",
    )
    add_qa(
        "safety::selected_core_trusted_rate_not_down",
        "PASS" if selected_core_trusted_rate_not_down else "FAIL",
        f"before={selected_core_trusted_rate_before_323h} after={selected_core_trusted_rate_after_323h}",
    )
    add_qa(
        "safety::unknown_metric_not_worse_than_322b2",
        "PASS" if unknown_metric_not_worse else "WARN",
        f"before={trust_summary.get('unknown_metric_candidate_count', '')} after={remaining_unknown_metric_candidate_count}",
    )
    add_qa(
        "safety::unit_unknown_not_worse_than_322b2",
        "PASS" if unit_unknown_not_worse else "WARN",
        f"before={trust_summary.get('unit_unknown_candidate_count', '')} after={remaining_unit_unknown_candidate_count}",
    )
    add_qa(
        "safety::manual_review_not_worse_than_322b2",
        "PASS" if manual_review_not_worse else "WARN",
        f"before={trust_summary.get('review_required_total_after_322b2', '')} after={remaining_manual_review_count}",
    )
    add_qa(
        "safety::no_core_metric_false_exclusion",
        "PASS" if core_false_exclusion_count == 0 else "FAIL",
        f"core_false_exclusion_count={core_false_exclusion_count}",
    )
    add_qa("safety::no_llm_call_executed", "PASS", "323H uses cached 323G/322B2/322O outputs only.")
    add_qa("safety::no_parser_or_vlm_run_executed", "PASS", "323H does not run MinerU/StructEqTable/Docling/PPStructure/VLM.")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    add_qa(
        "safety::official_assets_not_modified",
        "PASS"
        if alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
        else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    reference_322o_ready = (
        _norm(post_patch_summary.get("decision"))
        == "POST_PATCH_REGRESSION_VALIDATION_322O_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE"
    )
    add_qa(
        "reference_322o::closed_state_ready",
        "PASS" if reference_322o_ready else "WARN",
        _norm(post_patch_summary.get("decision")),
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )

    summary = {
        "stage": "323H",
        "output_dir": "",
        "total_confirmed_suggestion_count": total_confirmed_suggestion_count,
        "alias_confirmed_suggestion_count": alias_confirmed_suggestion_count,
        "scope_confirmed_suggestion_count": scope_confirmed_suggestion_count,
        "sandbox_rule_count": int(len(source_rule_inventory_df)),
        "sandbox_alias_rule_count": int(
            source_rule_inventory_df["proposal_type"].astype(str).eq("alias").sum()
        )
        if not source_rule_inventory_df.empty
        else 0,
        "sandbox_scope_rule_count": int(
            source_rule_inventory_df["proposal_type"].astype(str).eq("out_of_scope").sum()
        )
        if not source_rule_inventory_df.empty
        else 0,
        "effective_unique_rule_count": int(len(duplicate_conflict_df)),
        "duplicate_rule_count": duplicate_rule_count,
        "conflict_count": conflict_count,
        "metric_target_unresolved_count": metric_target_unresolved_count,
        "trusted_total_before_323h": trusted_total_before_323h,
        "trusted_total_after_323h": trusted_total_after_323h,
        "review_required_total_before_323h": review_required_total_before_323h,
        "review_required_total_after_323h": review_required_total_after_323h,
        "rejected_total_before_323h": rejected_total_before_323h,
        "rejected_total_after_323h": rejected_total_after_323h,
        "affected_candidate_count": affected_candidate_count,
        "trusted_gain_323h": trusted_gain_323h,
        "review_reduction_323h": review_reduction_323h,
        "out_of_scope_or_rejected_gain_323h": out_of_scope_or_rejected_gain_323h,
        "alias_trusted_gain_323h": alias_trusted_gain_323h,
        "alias_review_reduction_323h": alias_review_reduction_323h,
        "scope_trusted_gain_323h": scope_trusted_gain_323h,
        "scope_review_reduction_323h": scope_review_reduction_323h,
        "scope_out_of_scope_or_rejected_gain_323h": scope_out_of_scope_or_rejected_gain_323h,
        "selected_core_trusted_rate_before_323h": selected_core_trusted_rate_before_323h,
        "selected_core_trusted_rate_after_323h": selected_core_trusted_rate_after_323h,
        "baseline_unknown_metric_candidate_count": _safe_int(
            trust_summary.get("unknown_metric_candidate_count")
        ),
        "baseline_unit_unknown_candidate_count": _safe_int(
            trust_summary.get("unit_unknown_candidate_count")
        ),
        "baseline_manual_review_count": _safe_int(
            trust_summary.get("review_required_total_after_322b2")
        ),
        "remaining_unknown_metric_candidate_count": remaining_unknown_metric_candidate_count,
        "remaining_unit_unknown_candidate_count": remaining_unit_unknown_candidate_count,
        "remaining_manual_review_count": remaining_manual_review_count,
        "reference_322o_trusted_gain": _safe_int(post_patch_summary.get("trusted_gain_322o")),
        "reference_322o_review_reduction": _safe_int(
            post_patch_summary.get("review_reduction_322o")
        ),
        "reference_322o_out_of_scope_or_rejected_gain": _safe_int(
            post_patch_summary.get("out_of_scope_or_rejected_gain_322o")
        ),
        "reference_322o_affected_candidate_count": _safe_int(
            post_patch_summary.get("affected_candidate_count")
        ),
        "core_false_exclusion_count": core_false_exclusion_count,
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

    before_after_overview_df = _build_before_after_overview(summary)
    rule_application_overview_df = _build_rule_application_overview(
        source_rule_inventory_df=source_rule_inventory_df,
        patch_impact_df=patch_impact_df,
    )
    alias_scope_contribution_df = _build_alias_scope_contribution_df(patch_impact_df)
    alias_rule_inventory_df = source_rule_inventory_df.loc[
        source_rule_inventory_df["proposal_type"].astype(str) == "alias"
    ].copy() if not source_rule_inventory_df.empty else pd.DataFrame()
    scope_rule_inventory_df = source_rule_inventory_df.loc[
        source_rule_inventory_df["proposal_type"].astype(str) == "out_of_scope"
    ].copy() if not source_rule_inventory_df.empty else pd.DataFrame()
    alias_diff_df = diff_df.loc[
        diff_df["proposal_id"].astype(str).isin(alias_rule_inventory_df["source_rule_id"].astype(str).tolist())
    ].copy() if not diff_df.empty and not alias_rule_inventory_df.empty else pd.DataFrame()
    scope_diff_df = diff_df.loc[
        diff_df["proposal_id"].astype(str).isin(scope_rule_inventory_df["source_rule_id"].astype(str).tolist())
    ].copy() if not diff_df.empty and not scope_rule_inventory_df.empty else pd.DataFrame()

    notes_markdown = _build_notes_markdown(summary, qa_df)
    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }

    return {
        "summary": summary,
        "qa_json": qa_json,
        "sandbox_rule_set_json": sandbox_rule_set_json,
        "source_rule_inventory_df": source_rule_inventory_df,
        "duplicate_conflict_df": duplicate_conflict_df,
        "before_after_overview_df": before_after_overview_df,
        "rule_application_overview_df": rule_application_overview_df,
        "alias_scope_contribution_df": alias_scope_contribution_df,
        "candidate_before_after_diff_df": diff_df,
        "patch_impact_by_rule_df": patch_impact_df,
        "trusted_after_df": trusted_after_df,
        "review_after_df": review_after_df,
        "rejected_after_df": rejected_after_df,
        "remaining_review_burden_df": remaining_review_burden_df,
        "alias_rule_inventory_df": alias_rule_inventory_df,
        "scope_rule_inventory_df": scope_rule_inventory_df,
        "alias_diff_df": alias_diff_df,
        "scope_diff_df": scope_diff_df,
        "core_false_exclusion_df": core_false_exclusion_df,
        "qa_checks_df": qa_df,
        "notes_markdown": notes_markdown,
    }
