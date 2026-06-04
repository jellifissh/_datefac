from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set

import pandas as pd

from datefac.semantic.human_confirmed_patch_preview import (
    _candidate_passes_trust_gate,
    _normalize_label,
    apply_human_confirmed_patches,
    build_remaining_review_burden,
    read_jsonl,
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
EXPECTED_324A_READY_DECISION = "SCOPE_NOISE_REFINEMENT_324A_READY_FOR_SCOPE_REVIEW_BATCH"
EXPECTED_323N_READY_DECISIONS = {
    "POST_PATCH_REGRESSION_VALIDATION_323N_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE",
    "POST_PATCH_REGRESSION_VALIDATION_323N_READY_WITH_WARNINGS",
}

READY_DECISION = (
    "SCOPE_NOISE_HUMAN_CONFIRMED_SANDBOX_REPLAY_324G_READY_FOR_324H_OFFICIAL_RULE_CANDIDATE"
)
READY_WARN_DECISION = "SCOPE_NOISE_HUMAN_CONFIRMED_SANDBOX_REPLAY_324G_READY_WITH_WARNINGS"
NOT_READY_DECISION = "SCOPE_NOISE_HUMAN_CONFIRMED_SANDBOX_REPLAY_324G_NOT_READY"

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
    if " | " in text or "|" in text:
        return _split_pipe(text)
    return [text]


def _join_unique(items: Iterable[Any], limit: int = 16) -> str:
    out: List[str] = []
    seen: Set[str] = set()
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            out.append(clean)
            seen.add(clean)
        if len(out) >= limit:
            break
    return " | ".join(out)


def _safe_numeric_sum(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def load_scope_noise_human_confirmed_sandbox_replay_324g_inputs(
    reviewed_confirmation_dir: Path,
    scope_noise_response_schema_validation_dir: Path,
    safe_adjudicator_request_dir: Path,
    scope_refinement_dir: Path,
    trust_split_dir: Path,
    post_patch_regression_dir: Path,
) -> Dict[str, Any]:
    return {
        "reviewed_summary": _read_json(
            reviewed_confirmation_dir / "scope_noise_human_confirmation_324f_reviewed_summary.json"
        ),
        "reviewed_qa": _read_json(
            reviewed_confirmation_dir / "scope_noise_human_confirmation_324f_reviewed_qa.json"
        ),
        "reviewed_outcome": _read_json(
            reviewed_confirmation_dir / "scope_noise_human_confirmation_324f_reviewed_outcome.json"
        ),
        "schema_validation_summary": _read_json(
            scope_noise_response_schema_validation_dir
            / "scope_noise_response_schema_validation_324e_summary.json"
        ),
        "safe_request_package": _read_json(
            safe_adjudicator_request_dir
            / "scope_noise_safe_adjudicator_request_324c_request_package.json"
        ),
        "scope_refinement_summary": _read_json(
            scope_refinement_dir / "scope_noise_refinement_324a_summary.json"
        ),
        "scope_refinement_batch": _read_json(
            scope_refinement_dir / "scope_noise_refinement_324a_refined_batch.json"
        ),
        "trust_summary": _read_json(
            trust_split_dir / "router_mineru_trust_split_322b2_summary.json"
        ),
        "selected_candidates_df": read_jsonl(
            trust_split_dir / "selected_candidate_reclassified_322b2.jsonl"
        ),
        "post_patch_summary": _read_json(
            post_patch_regression_dir / "post_patch_regression_validation_323n_summary.json"
        ),
    }


def _extract_confirmed_scope_noise_records(reviewed_outcome: Dict[str, Any]) -> pd.DataFrame:
    rows = reviewed_outcome.get("confirmed_records", [])
    if not isinstance(rows, list):
        return pd.DataFrame()
    cleaned = [row for row in rows if isinstance(row, dict)]
    return pd.DataFrame(cleaned).fillna("")


def _request_lookup(safe_request_package: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    items = safe_request_package.get("request_items", [])
    if not isinstance(items, list):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        request_id = _norm(item.get("request_id"))
        if request_id:
            out[request_id] = item
    return out


def _refined_candidate_lookup(scope_refinement_batch: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    items = scope_refinement_batch.get("refined_scope_candidates", [])
    if not isinstance(items, list):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        candidate_id = _norm(item.get("refined_scope_candidate_id"))
        if candidate_id:
            out[candidate_id] = item
    return out


def _build_source_rule_inventory(
    confirmed_df: pd.DataFrame,
    request_map: Dict[str, Dict[str, Any]],
    refined_candidate_map: Dict[str, Dict[str, Any]],
) -> pd.DataFrame:
    if confirmed_df.empty:
        return pd.DataFrame()

    rows: List[Dict[str, Any]] = []
    for index, (_, row) in enumerate(confirmed_df.iterrows(), start=1):
        request_id = _norm(row.get("request_id"))
        request_item = request_map.get(request_id, {})
        refined_candidate_id = _norm(row.get("source_refined_scope_candidate_id"))
        refined_candidate = refined_candidate_map.get(refined_candidate_id, {})

        provenance = request_item.get("provenance", {})
        if not isinstance(provenance, dict):
            provenance = {}

        candidate_label = _norm(row.get("candidate_label")) or _norm(request_item.get("candidate_label"))
        sample_texts = _to_list(request_item.get("sample_texts")) or _to_list(row.get("sample_texts"))
        sample_candidate_ids = _to_list(request_item.get("sample_candidate_ids")) or _split_pipe(
            row.get("sample_candidate_ids")
        )
        sample_years = _to_list(provenance.get("sample_years")) or _split_pipe(row.get("sample_years"))
        sample_table_titles = _to_list(provenance.get("sample_table_titles"))
        sample_raw_metric_names = _to_list(provenance.get("sample_raw_metric_names"))

        rows.append(
            {
                "source_rule_id": f"324g::sandbox_scope_rule::{index:03d}",
                "confirmation_id": _norm(row.get("confirmation_id")),
                "request_id": request_id,
                "source_scope_review_id": _norm(row.get("source_scope_review_id")),
                "source_refined_scope_candidate_id": refined_candidate_id,
                "proposal_type": "out_of_scope",
                "candidate_type": "scope_noise",
                "normalized_label": candidate_label,
                "normalized_label_key": _normalize_label(candidate_label),
                "candidate_label": candidate_label,
                "response_label": _norm(row.get("response_label")),
                "confidence": _norm(row.get("confidence")),
                "rationale": _norm(row.get("rationale")),
                "reviewer_decision": _norm(row.get("reviewer_decision")),
                "reviewer_note": _norm(row.get("reviewer_note")),
                "reviewer_name": _norm(row.get("reviewer_name")),
                "review_timestamp": _norm(row.get("review_timestamp")),
                "expected_affected_candidate_count": _safe_int(
                    row.get("affected_candidate_count") or request_item.get("affected_candidate_count")
                ),
                "expected_review_reduction_potential": _safe_int(
                    row.get("affected_review_required_count")
                    or request_item.get("affected_review_required_count")
                ),
                "expected_out_of_scope_or_rejected_gain": _safe_int(
                    row.get("affected_review_required_count")
                    or request_item.get("affected_review_required_count")
                ),
                "priority_score": _safe_float(
                    row.get("priority_score") or request_item.get("priority_score")
                ),
                "risk_flags": _join_unique(
                    _split_pipe(row.get("risk_flags")) or _to_list(request_item.get("risk_flags")),
                    limit=16,
                ),
                "manual_review_warning": _norm(row.get("manual_review_warning")),
                "adjudicator_caution": _norm(row.get("adjudicator_caution")),
                "proposed_scope_action": "exclude_from_core_metric_mapping",
                "representative_group_id": _norm(
                    row.get("representative_group_id") or provenance.get("representative_group_id")
                ),
                "source_group_ids": _join_unique(
                    _split_pipe(row.get("source_group_ids")) or _to_list(provenance.get("source_group_ids")),
                    limit=32,
                ),
                "source_group_count": _safe_int(provenance.get("source_group_count"))
                or _safe_int(refined_candidate.get("source_group_count")),
                "duplicate_source_group_count": _safe_int(provenance.get("duplicate_source_group_count"))
                or _safe_int(refined_candidate.get("duplicate_source_group_count")),
                "source_stage_signatures": _join_unique(
                    _split_pipe(row.get("source_stage_signatures"))
                    or _to_list(provenance.get("source_stage_signatures")),
                    limit=16,
                ),
                "source_stage_chain": _join_unique(
                    _split_pipe(row.get("source_stage_chain"))
                    or _to_list(provenance.get("source_stage_chain")),
                    limit=16,
                ),
                "sample_candidate_ids": _join_unique(sample_candidate_ids, limit=24),
                "sample_texts": _join_unique(sample_texts, limit=8),
                "sample_years": _join_unique(sample_years, limit=8),
                "sample_table_titles": _join_unique(sample_table_titles, limit=8),
                "sample_raw_metric_names": _join_unique(sample_raw_metric_names, limit=8),
                "why_high_impact": _norm(row.get("why_high_impact")) or _norm(provenance.get("why_high_impact")),
                "why_safe_or_risky": _norm(row.get("why_safe_or_risky"))
                or _norm(provenance.get("why_safe_or_risky")),
                "risk_notes": _norm(row.get("risk_notes")) or _norm(provenance.get("risk_notes")),
                "raw_request_reference": json.dumps(request_item, ensure_ascii=False),
                "raw_refined_candidate_reference": json.dumps(refined_candidate, ensure_ascii=False),
            }
        )

    return pd.DataFrame(rows).fillna("")


def _build_apply_dataframe(source_rule_inventory_df: pd.DataFrame) -> pd.DataFrame:
    if source_rule_inventory_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for _, row in source_rule_inventory_df.iterrows():
        rows.append(
            {
                "proposal_id": _norm(row.get("source_rule_id")),
                "proposal_type": "out_of_scope",
                "source_case_id": _norm(row.get("confirmation_id")),
                "normalized_label": _norm(row.get("normalized_label")),
                "sample_table_titles": _norm(row.get("sample_table_titles")),
                "sample_row_labels": _norm(row.get("candidate_label")),
                "sample_values": _norm(row.get("sample_texts")),
                "risk_flags": _norm(row.get("risk_flags")),
                "affected_candidate_count": _safe_int(row.get("expected_affected_candidate_count")),
                "review_reduction": _safe_int(row.get("expected_review_reduction_potential")),
                "reviewer_decision": "CONFIRM",
                "reviewer_comment": _join_unique(
                    [
                        _norm(row.get("reviewer_note")),
                        _norm(row.get("rationale")),
                        _norm(row.get("manual_review_warning")),
                    ],
                    limit=6,
                ),
                "proposed_scope_action": "exclude_from_core_metric_mapping",
            }
        )
    return pd.DataFrame(rows).fillna("")


def _build_duplicate_conflict_df(source_rule_inventory_df: pd.DataFrame) -> pd.DataFrame:
    if source_rule_inventory_df.empty:
        return pd.DataFrame()

    grouped = source_rule_inventory_df.groupby(
        ["proposal_type", "normalized_label_key"], dropna=False
    )
    rows: List[Dict[str, Any]] = []
    for (proposal_type, label_key), group in grouped:
        rows.append(
            {
                "proposal_type": _norm(proposal_type),
                "normalized_label": _norm(group.iloc[0].get("normalized_label")),
                "normalized_label_key": _norm(label_key),
                "source_rule_count": int(len(group)),
                "duplicate_rule": int(len(group)) > 1,
                "conflict_detected": False,
                "source_rule_ids": _join_unique(group["source_rule_id"].astype(str).tolist(), limit=16),
                "source_group_ids": _join_unique(group["source_group_ids"].astype(str).tolist(), limit=16),
                "conflict_note": "",
            }
        )
    return pd.DataFrame(rows).fillna("").sort_values(
        ["proposal_type", "normalized_label_key"]
    ).reset_index(drop=True)


def _build_sandbox_rule_set_json(
    source_rule_inventory_df: pd.DataFrame,
    duplicate_conflict_df: pd.DataFrame,
) -> Dict[str, Any]:
    rules: List[Dict[str, Any]] = []
    for _, row in source_rule_inventory_df.iterrows():
        rules.append(
            {
                "source_rule_id": _norm(row.get("source_rule_id")),
                "confirmation_id": _norm(row.get("confirmation_id")),
                "request_id": _norm(row.get("request_id")),
                "source_scope_review_id": _norm(row.get("source_scope_review_id")),
                "source_refined_scope_candidate_id": _norm(
                    row.get("source_refined_scope_candidate_id")
                ),
                "proposal_type": "out_of_scope",
                "candidate_type": "scope_noise",
                "normalized_label": _norm(row.get("normalized_label")),
                "confidence": _norm(row.get("confidence")),
                "response_label": _norm(row.get("response_label")),
                "proposed_scope_action": "exclude_from_core_metric_mapping",
                "expected_affected_candidate_count": _safe_int(
                    row.get("expected_affected_candidate_count")
                ),
                "expected_review_reduction_potential": _safe_int(
                    row.get("expected_review_reduction_potential")
                ),
                "risk_flags": _split_pipe(row.get("risk_flags")),
                "source_group_ids": _split_pipe(row.get("source_group_ids")),
                "sample_candidate_ids": _split_pipe(row.get("sample_candidate_ids")),
            }
        )
    return {
        "stage": "324G",
        "mode": "sandbox_replay_only",
        "source_rule_count": int(len(source_rule_inventory_df)),
        "confirmed_scope_noise_count": int(len(source_rule_inventory_df)),
        "alias_rule_count": 0,
        "scope_rule_count": int(len(source_rule_inventory_df)),
        "duplicate_conflict_summary": duplicate_conflict_df.to_dict(orient="records"),
        "scope_rules": rules,
    }


def _build_before_after_overview(summary: Dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "metric": "trusted_total",
                "before": _safe_int(summary.get("trusted_total_before_324g")),
                "after": _safe_int(summary.get("trusted_total_after_324g")),
                "delta": _safe_int(summary.get("trusted_gain_324g")),
            },
            {
                "metric": "review_required_total",
                "before": _safe_int(summary.get("review_required_total_before_324g")),
                "after": _safe_int(summary.get("review_required_total_after_324g")),
                "delta": _safe_int(summary.get("review_required_total_after_324g"))
                - _safe_int(summary.get("review_required_total_before_324g")),
            },
            {
                "metric": "rejected_total",
                "before": _safe_int(summary.get("rejected_total_before_324g")),
                "after": _safe_int(summary.get("rejected_total_after_324g")),
                "delta": _safe_int(summary.get("out_of_scope_or_rejected_gain_324g")),
            },
            {
                "metric": "selected_core_trusted_rate",
                "before": _safe_float(summary.get("selected_core_trusted_rate_before_324g")),
                "after": _safe_float(summary.get("selected_core_trusted_rate_after_324g")),
                "delta": round(
                    _safe_float(summary.get("selected_core_trusted_rate_after_324g"))
                    - _safe_float(summary.get("selected_core_trusted_rate_before_324g")),
                    6,
                ),
            },
            {
                "metric": "full_pool_label_match_count",
                "before": _safe_int(summary.get("full_pool_label_match_count")),
                "after": _safe_int(summary.get("full_pool_label_match_count")),
                "delta": 0,
            },
            {
                "metric": "review_required_label_match_count",
                "before": _safe_int(summary.get("review_required_label_match_count")),
                "after": _safe_int(summary.get("review_required_label_match_count")),
                "delta": 0,
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
                "proposal_type": "out_of_scope",
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
    rows: List[Dict[str, Any]] = []
    for proposal_type in ["alias", "out_of_scope"]:
        group = (
            patch_impact_df.loc[patch_impact_df["proposal_type"].astype(str) == proposal_type].copy()
            if not patch_impact_df.empty
            else pd.DataFrame()
        )
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
    return pd.DataFrame(rows).fillna("")


def _build_notes_markdown(summary: Dict[str, Any], qa_df: pd.DataFrame) -> str:
    lines = [
        "# Scope Noise Human Confirmed Sandbox Replay 324G",
        "",
        "## Scope",
        "- Sandbox-only replay against cached 322B2 selected candidates.",
        "- No official mapping or override asset was modified.",
        "- No parser, OCR, VLM, LLM, or semantic adjudicator call was executed.",
        "- Only the single 324F human-confirmed scope-noise suggestion was replayed.",
        "",
        "## Result",
        f"- decision: {summary.get('decision', '')}",
        f"- confirmed_scope_noise_count: {summary.get('confirmed_scope_noise_count', 0)}",
        f"- sandbox_rule_count: {summary.get('sandbox_rule_count', 0)}",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- trusted_gain_324g: {summary.get('trusted_gain_324g', 0)}",
        f"- review_reduction_324g: {summary.get('review_reduction_324g', 0)}",
        f"- out_of_scope_or_rejected_gain_324g: {summary.get('out_of_scope_or_rejected_gain_324g', 0)}",
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


def build_scope_noise_human_confirmed_sandbox_replay_324g(
    reviewed_summary: Dict[str, Any],
    reviewed_qa: Dict[str, Any],
    reviewed_outcome: Dict[str, Any],
    schema_validation_summary: Dict[str, Any],
    safe_request_package: Dict[str, Any],
    scope_refinement_summary: Dict[str, Any],
    scope_refinement_batch: Dict[str, Any],
    trust_summary: Dict[str, Any],
    selected_candidates_df: pd.DataFrame,
    post_patch_summary: Dict[str, Any],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    confirmed_df = _extract_confirmed_scope_noise_records(reviewed_outcome)
    request_map = _request_lookup(safe_request_package)
    refined_candidate_map = _refined_candidate_lookup(scope_refinement_batch)
    source_rule_inventory_df = _build_source_rule_inventory(
        confirmed_df=confirmed_df,
        request_map=request_map,
        refined_candidate_map=refined_candidate_map,
    )
    duplicate_conflict_df = _build_duplicate_conflict_df(source_rule_inventory_df)
    sandbox_rule_set_json = _build_sandbox_rule_set_json(
        source_rule_inventory_df=source_rule_inventory_df,
        duplicate_conflict_df=duplicate_conflict_df,
    )

    add_qa(
        "readiness::324f_reviewed_decision",
        "PASS"
        if _norm(reviewed_summary.get("decision")) == EXPECTED_324F_REVIEWED_READY_DECISION
        else "FAIL",
        _norm(reviewed_summary.get("decision")),
    )
    add_qa(
        "readiness::324f_reviewed_summary_qa_fail_count",
        "PASS" if _safe_int(reviewed_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(reviewed_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324f_reviewed_qa_json_fail_count",
        "PASS" if _safe_int(reviewed_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(reviewed_qa.get("qa_fail_count", "")),
    )
    for key, expected in [
        ("confirmation_record_count", 1),
        ("confirmed_count", 1),
        ("rejected_count", 0),
        ("needs_more_info_count", 0),
        ("pending_count", 0),
        ("invalid_decision_count", 0),
    ]:
        add_qa(
            f"readiness::324f_reviewed_{key}",
            "PASS" if _safe_int(reviewed_summary.get(key)) == expected else "FAIL",
            f"expected={expected} actual={reviewed_summary.get(key, '')}",
        )

    add_qa(
        "readiness::324e_decision",
        "PASS"
        if _norm(schema_validation_summary.get("decision")) == EXPECTED_324E_READY_DECISION
        else "FAIL",
        _norm(schema_validation_summary.get("decision")),
    )
    add_qa(
        "readiness::324a_decision",
        "PASS"
        if _norm(scope_refinement_summary.get("decision")) == EXPECTED_324A_READY_DECISION
        else "FAIL",
        _norm(scope_refinement_summary.get("decision")),
    )
    add_qa(
        "readiness::324c_decision",
        "PASS"
        if _norm(safe_request_package.get("decision")) == EXPECTED_324C_READY_DECISION
        else "FAIL",
        _norm(safe_request_package.get("decision")),
    )
    add_qa(
        "readiness::323n_decision",
        "PASS"
        if _norm(post_patch_summary.get("decision")) in EXPECTED_323N_READY_DECISIONS
        else "FAIL",
        _norm(post_patch_summary.get("decision")),
    )
    add_qa(
        "readiness::323n_qa_fail_count",
        "PASS" if _safe_int(post_patch_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(post_patch_summary.get("qa_fail_count", "")),
    )

    confirmed_scope_noise_count = int(len(confirmed_df))
    sandbox_rule_count = int(len(source_rule_inventory_df))
    add_qa(
        "confirmed_records::single_scope_noise_confirmed_record_loaded",
        "PASS"
        if confirmed_scope_noise_count == 1
        and not confirmed_df.empty
        and confirmed_df["candidate_type"].astype(str).eq("scope_noise").all()
        else "FAIL",
        f"actual={confirmed_scope_noise_count}",
    )
    add_qa(
        "confirmed_records::single_sandbox_scope_rule_built",
        "PASS" if sandbox_rule_count == 1 else "FAIL",
        f"actual={sandbox_rule_count}",
    )

    request_id_found = False
    refined_candidate_found = False
    response_label_ok = False
    if not confirmed_df.empty:
        request_id = _norm(confirmed_df.iloc[0].get("request_id"))
        refined_candidate_id = _norm(confirmed_df.iloc[0].get("source_refined_scope_candidate_id"))
        request_id_found = request_id in request_map
        refined_candidate_found = refined_candidate_id in refined_candidate_map
        response_label_ok = _norm(confirmed_df.iloc[0].get("response_label")) == "ACCEPT_OUT_OF_SCOPE"
    add_qa(
        "confirmed_records::request_id_found_in_324c_request_package",
        "PASS" if request_id_found else "FAIL",
        _norm(confirmed_df.iloc[0].get("request_id")) if not confirmed_df.empty else "",
    )
    add_qa(
        "confirmed_records::source_refined_candidate_found_in_324a_batch",
        "PASS" if refined_candidate_found else "FAIL",
        _norm(confirmed_df.iloc[0].get("source_refined_scope_candidate_id"))
        if not confirmed_df.empty
        else "",
    )
    add_qa(
        "confirmed_records::response_label_accept_out_of_scope",
        "PASS" if response_label_ok else "FAIL",
        _norm(confirmed_df.iloc[0].get("response_label")) if not confirmed_df.empty else "",
    )

    duplicate_count = int(
        duplicate_conflict_df["duplicate_rule"].astype(bool).sum()
    ) if not duplicate_conflict_df.empty else 0
    conflict_count = int(
        duplicate_conflict_df["conflict_detected"].astype(bool).sum()
    ) if not duplicate_conflict_df.empty else 0
    add_qa(
        "sandbox_rules::duplicate_count_zero",
        "PASS" if duplicate_count == 0 else "FAIL",
        f"duplicate_count={duplicate_count}",
    )
    add_qa(
        "sandbox_rules::conflict_count_zero",
        "PASS" if conflict_count == 0 else "FAIL",
        f"conflict_count={conflict_count}",
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

    label_key = (
        _normalize_label(source_rule_inventory_df.iloc[0].get("normalized_label"))
        if not source_rule_inventory_df.empty
        else ""
    )
    full_match_df = (
        selected_candidates_df.loc[
            selected_candidates_df["raw_metric_name"].map(_normalize_label) == label_key
        ].copy()
        if label_key and not selected_candidates_df.empty
        else pd.DataFrame()
    )
    review_required_match_count = int(
        full_match_df["split_decision"].astype(str).eq("review_required_preview").sum()
    ) if not full_match_df.empty else 0
    trusted_match_count = int(
        full_match_df["split_decision"].astype(str).eq("trusted_preview").sum()
    ) if not full_match_df.empty else 0
    rejected_match_count = int(
        full_match_df["split_decision"].astype(str).eq("rejected_preview").sum()
    ) if not full_match_df.empty else 0

    trusted_total_before_324g = int(len(trusted_before_df))
    trusted_total_after_324g = int(len(trusted_after_df))
    review_required_total_before_324g = int(len(review_before_df))
    review_required_total_after_324g = int(len(review_after_df))
    rejected_total_before_324g = int(len(rejected_before_df))
    rejected_total_after_324g = int(len(rejected_after_df))

    trusted_gain_324g = trusted_total_after_324g - trusted_total_before_324g
    review_reduction_324g = (
        review_required_total_before_324g - review_required_total_after_324g
    )
    out_of_scope_or_rejected_gain_324g = (
        rejected_total_after_324g - rejected_total_before_324g
    )
    affected_candidate_count = int(len(diff_df))

    scope_review_reduction_324g = _safe_numeric_sum(patch_impact_df, "review_reduction")
    scope_out_of_scope_or_rejected_gain_324g = _safe_numeric_sum(
        patch_impact_df, "rejected_or_out_of_scope_count"
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

    selected_core_trusted_rate_before_324g = round(
        _safe_float(trust_summary.get("selected_core_trusted_rate_after_322b2")), 6
    )
    selected_core_trusted_rate_after_324g = (
        round(trusted_total_after_324g / len(selected_candidates_df), 6)
        if len(selected_candidates_df)
        else 0.0
    )

    add_qa(
        "matching_candidates::full_pool_match_count_reconciles",
        "PASS"
        if int(len(full_match_df))
        == review_required_match_count + trusted_match_count + rejected_match_count
        else "FAIL",
        (
            f"full={len(full_match_df)} review_required={review_required_match_count} "
            f"trusted={trusted_match_count} rejected={rejected_match_count}"
        ),
    )
    add_qa(
        "matching_candidates::review_required_match_count_equals_affected_count",
        "PASS" if review_required_match_count == affected_candidate_count else "FAIL",
        f"review_required_match_count={review_required_match_count} affected={affected_candidate_count}",
    )
    add_qa(
        "before_after::candidate_counts_reconcile",
        "PASS"
        if len(selected_candidates_df)
        == trusted_total_after_324g + review_required_total_after_324g + rejected_total_after_324g
        else "FAIL",
        (
            f"input={len(selected_candidates_df)} "
            f"after_total={trusted_total_after_324g + review_required_total_after_324g + rejected_total_after_324g}"
        ),
    )
    add_qa(
        "before_after::trusted_gain_matches_impact_rows",
        "PASS" if trusted_gain_324g == _safe_numeric_sum(patch_impact_df, "trusted_gain") else "FAIL",
        f"summary={trusted_gain_324g} impact={_safe_numeric_sum(patch_impact_df, 'trusted_gain')}",
    )
    add_qa(
        "before_after::review_reduction_matches_impact_rows",
        "PASS"
        if review_reduction_324g == _safe_numeric_sum(patch_impact_df, "review_reduction")
        else "FAIL",
        (
            f"summary={review_reduction_324g} "
            f"impact={_safe_numeric_sum(patch_impact_df, 'review_reduction')}"
        ),
    )
    add_qa(
        "before_after::rejected_gain_matches_impact_rows",
        "PASS"
        if out_of_scope_or_rejected_gain_324g
        == _safe_numeric_sum(patch_impact_df, "rejected_or_out_of_scope_count")
        else "FAIL",
        (
            f"summary={out_of_scope_or_rejected_gain_324g} "
            f"impact={_safe_numeric_sum(patch_impact_df, 'rejected_or_out_of_scope_count')}"
        ),
    )
    add_qa(
        "before_after::affected_count_matches_diff_rows",
        "PASS"
        if affected_candidate_count == _safe_numeric_sum(patch_impact_df, "affected_candidate_count")
        else "FAIL",
        (
            f"summary={affected_candidate_count} "
            f"impact={_safe_numeric_sum(patch_impact_df, 'affected_candidate_count')}"
        ),
    )

    trusted_gate_ok = (
        trusted_after_df.apply(_candidate_passes_trust_gate, axis=1).all()
        if not trusted_after_df.empty
        else True
    )
    no_trusted_regression = trusted_total_after_324g >= trusted_total_before_324g
    selected_core_trusted_rate_not_down = (
        selected_core_trusted_rate_after_324g >= selected_core_trusted_rate_before_324g
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
        f"before={trusted_total_before_324g} after={trusted_total_after_324g}",
    )
    add_qa(
        "safety::selected_core_trusted_rate_not_down",
        "PASS" if selected_core_trusted_rate_not_down else "FAIL",
        (
            f"before={selected_core_trusted_rate_before_324g} "
            f"after={selected_core_trusted_rate_after_324g}"
        ),
    )
    add_qa(
        "safety::unknown_metric_not_worse_than_322b2",
        "PASS" if unknown_metric_not_worse else "WARN",
        (
            f"before={trust_summary.get('unknown_metric_candidate_count', '')} "
            f"after={remaining_unknown_metric_candidate_count}"
        ),
    )
    add_qa(
        "safety::unit_unknown_not_worse_than_322b2",
        "PASS" if unit_unknown_not_worse else "WARN",
        (
            f"before={trust_summary.get('unit_unknown_candidate_count', '')} "
            f"after={remaining_unit_unknown_candidate_count}"
        ),
    )
    add_qa(
        "safety::manual_review_not_worse_than_322b2",
        "PASS" if manual_review_not_worse else "WARN",
        (
            f"before={trust_summary.get('review_required_total_after_322b2', '')} "
            f"after={remaining_manual_review_count}"
        ),
    )
    add_qa(
        "safety::no_core_metric_false_exclusion",
        "PASS" if core_false_exclusion_count == 0 else "FAIL",
        f"core_false_exclusion_count={core_false_exclusion_count}",
    )
    add_qa("safety::no_llm_call_executed", "PASS", "324G uses cached 324F/324E/324C/324A/322B2/323N outputs only.")
    add_qa("safety::no_parser_or_vlm_run_executed", "PASS", "324G does not run MinerU/StructEqTable/Docling/PPStructure/VLM.")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    official_assets_not_modified = (
        alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    )
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if official_assets_not_modified else "FAIL",
        (
            f"alias_before={alias_hash_before} alias_after={alias_hash_after} "
            f"scope_before={scope_hash_before} scope_after={scope_hash_after}"
        ),
    )

    inherited_historical_duplicate_warning = (
        _norm(post_patch_summary.get("decision"))
        == "POST_PATCH_REGRESSION_VALIDATION_323N_READY_WITH_WARNINGS"
        and _safe_int(post_patch_summary.get("new_duplicate_delta_count")) == 0
    )
    add_qa(
        "reference_323n::historical_duplicates_unchanged_only",
        "WARN" if inherited_historical_duplicate_warning else "PASS",
        (
            f"historical_duplicate_count={post_patch_summary.get('historical_duplicate_count', '')} "
            f"current_duplicate_count={post_patch_summary.get('current_duplicate_count', '')} "
            f"new_duplicate_delta_count={post_patch_summary.get('new_duplicate_delta_count', '')}"
        ),
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
        "stage": "324G",
        "output_dir": "",
        "confirmed_scope_noise_count": confirmed_scope_noise_count,
        "sandbox_rule_count": sandbox_rule_count,
        "sandbox_scope_rule_count": sandbox_rule_count,
        "sandbox_alias_rule_count": 0,
        "effective_unique_rule_count": int(len(duplicate_conflict_df)),
        "duplicate_count": duplicate_count,
        "conflict_count": conflict_count,
        "full_pool_label_match_count": int(len(full_match_df)),
        "review_required_label_match_count": review_required_match_count,
        "trusted_label_match_count": trusted_match_count,
        "rejected_label_match_count": rejected_match_count,
        "trusted_total_before_324g": trusted_total_before_324g,
        "trusted_total_after_324g": trusted_total_after_324g,
        "review_required_total_before_324g": review_required_total_before_324g,
        "review_required_total_after_324g": review_required_total_after_324g,
        "rejected_total_before_324g": rejected_total_before_324g,
        "rejected_total_after_324g": rejected_total_after_324g,
        "affected_candidate_count": affected_candidate_count,
        "trusted_gain_324g": trusted_gain_324g,
        "review_reduction_324g": review_reduction_324g,
        "out_of_scope_or_rejected_gain_324g": out_of_scope_or_rejected_gain_324g,
        "alias_trusted_gain_324g": 0,
        "alias_review_reduction_324g": 0,
        "scope_trusted_gain_324g": 0,
        "scope_review_reduction_324g": scope_review_reduction_324g,
        "scope_out_of_scope_or_rejected_gain_324g": scope_out_of_scope_or_rejected_gain_324g,
        "selected_core_trusted_rate_before_324g": selected_core_trusted_rate_before_324g,
        "selected_core_trusted_rate_after_324g": selected_core_trusted_rate_after_324g,
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
        "reference_323n_affected_candidate_count": _safe_int(
            post_patch_summary.get("affected_candidate_count")
        ),
        "reference_323n_trusted_gain": _safe_int(post_patch_summary.get("trusted_gain_323n")),
        "reference_323n_review_reduction": _safe_int(
            post_patch_summary.get("review_reduction_323n")
        ),
        "reference_323n_out_of_scope_or_rejected_gain": _safe_int(
            post_patch_summary.get("out_of_scope_or_rejected_gain_323n")
        ),
        "core_false_exclusion_count": core_false_exclusion_count,
        "official_assets_not_modified": official_assets_not_modified,
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
    scope_rule_inventory_df = source_rule_inventory_df.copy()
    scope_diff_df = diff_df.copy()
    full_pool_match_breakdown_df = pd.DataFrame(
        [
            {
                "match_type": "full_pool_label_match_count",
                "count": int(len(full_match_df)),
            },
            {
                "match_type": "review_required_label_match_count",
                "count": review_required_match_count,
            },
            {
                "match_type": "trusted_label_match_count",
                "count": trusted_match_count,
            },
            {
                "match_type": "rejected_label_match_count",
                "count": rejected_match_count,
            },
        ]
    ).fillna("")
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
        "full_pool_match_breakdown_df": full_pool_match_breakdown_df,
        "candidate_before_after_diff_df": diff_df,
        "patch_impact_by_rule_df": patch_impact_df,
        "trusted_after_df": trusted_after_df,
        "review_after_df": review_after_df,
        "rejected_after_df": rejected_after_df,
        "remaining_review_burden_df": remaining_review_burden_df,
        "scope_rule_inventory_df": scope_rule_inventory_df,
        "scope_diff_df": scope_diff_df,
        "core_false_exclusion_df": core_false_exclusion_df,
        "qa_checks_df": qa_df,
        "notes_markdown": notes_markdown,
    }
