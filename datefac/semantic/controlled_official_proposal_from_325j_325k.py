from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

import pandas as pd


EXPECTED_325J_DECISION = "ALIAS_OFFICIAL_RULE_CANDIDATES_325J_READY_FOR_325K_CONTROLLED_PROPOSAL"
READY_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_FROM_325J_325K_READY_FOR_325L_DRY_RUN"
NOT_READY_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_FROM_325J_325K_NOT_READY"

DEFAULT_OFFICIAL_RULE_CANDIDATE_DIR = Path(
    r"D:\_datefac\output\alias_official_rule_candidates_from_325i_325j"
)
DEFAULT_SANDBOX_REPLAY_DIR = Path(
    r"D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\controlled_official_proposal_from_325j_325k"
)

OFFICIAL_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
TARGET_ASSET_FILE = "data/overrides/semantic_alias_candidates.json"


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_label(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").lower()


def _metric_key(value: Any) -> str:
    return _norm(value).lower().replace(" ", "").replace("_", "").replace("-", "")


def _safe_int(value: Any) -> int:
    if value in ("", None):
        return 0
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return 0


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


def _official_hashes() -> Dict[str, str]:
    return {
        "formal_scope_rules": _sha256_file(FORMAL_SCOPE_RULES_PATH),
        "semantic_alias_candidates": _sha256_file(OFFICIAL_ALIAS_ASSET_PATH),
    }


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


def _safe_json_loads(value: Any) -> Dict[str, Any]:
    text = _norm(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _flatten_official_aliases(payload: Dict[str, Any]) -> Tuple[pd.DataFrame, Set[str]]:
    rows: List[Dict[str, Any]] = []
    groups = payload.get("groups", {}) if isinstance(payload, dict) else {}
    if not isinstance(groups, dict):
        return pd.DataFrame(), set()
    for group_name, entries in groups.items():
        if not isinstance(entries, list):
            continue
        for item in entries:
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    "target_asset_group": _norm(group_name),
                    "normalized_label": _norm(item.get("normalized_label")),
                    "normalized_label_key": _normalize_label(item.get("normalized_label")),
                    "metric_code": _norm(item.get("metric_code")),
                    "metric_code_key": _metric_key(item.get("metric_code")),
                    "metric_family": _norm(item.get("metric_family")) or _norm(group_name),
                    "rule_id": _norm(item.get("rule_id")),
                    "status": _norm(item.get("status")),
                }
            )
    return pd.DataFrame(rows).fillna(""), set(groups.keys())


def load_controlled_official_proposal_from_325j_inputs(
    official_rule_candidate_dir: Path,
    sandbox_replay_dir: Path,
) -> Dict[str, Any]:
    candidate_package = _read_json(
        official_rule_candidate_dir
        / "alias_official_rule_candidates_from_325i_325j_candidate_package.json"
    )
    official_alias_payload = _read_json(OFFICIAL_ALIAS_ASSET_PATH)
    official_alias_df, official_alias_groups = _flatten_official_aliases(official_alias_payload)
    return {
        "candidate_summary": _read_json(
            official_rule_candidate_dir
            / "alias_official_rule_candidates_from_325i_325j_summary.json"
        ),
        "candidate_qa": _read_json(
            official_rule_candidate_dir / "alias_official_rule_candidates_from_325i_325j_qa.json"
        ),
        "candidate_package": candidate_package,
        "candidates_df": pd.DataFrame(candidate_package.get("candidates", [])).fillna(""),
        "sandbox_summary": _read_json(
            sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_summary.json"
        ),
        "sandbox_rules": _read_json(
            sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_sandbox_rules.json"
        ),
        "official_alias_payload": official_alias_payload,
        "official_alias_df": official_alias_df,
        "official_alias_groups": official_alias_groups,
        "official_hashes_before": _official_hashes(),
    }


def _proposal_id(index: int) -> str:
    return f"proposal_325k::alias::{index:03d}"


def _target_group_for_candidate(candidate: Dict[str, Any], official_groups: Set[str]) -> str:
    direct_group = _norm(candidate.get("target_asset_group"))
    if direct_group and direct_group in official_groups:
        return direct_group
    metric_family = _norm(candidate.get("proposed_metric_family"))
    if metric_family and metric_family in official_groups:
        return metric_family
    return ""


def _target_plan_for_alias_candidate(
    candidate_row: Dict[str, Any],
    official_alias_df: pd.DataFrame,
    official_alias_groups: Set[str],
) -> Dict[str, Any]:
    normalized_label_key = _normalize_label(
        candidate_row.get("normalized_alias_label") or candidate_row.get("alias_label")
    )
    target_metric_key = _metric_key(candidate_row.get("target_metric"))
    target_group_name = _target_group_for_candidate(candidate_row, official_alias_groups)
    same_label_rows = (
        official_alias_df.loc[
            official_alias_df["normalized_label_key"].astype(str) == normalized_label_key
        ].copy()
        if not official_alias_df.empty
        else pd.DataFrame()
    )
    same_mapping_rows = (
        same_label_rows.loc[
            same_label_rows["metric_code_key"].astype(str) == target_metric_key
        ].copy()
        if not same_label_rows.empty
        else pd.DataFrame()
    )
    conflicting_rows = (
        same_label_rows.loc[
            same_label_rows["metric_code_key"].astype(str) != target_metric_key
        ].copy()
        if not same_label_rows.empty
        else pd.DataFrame()
    )

    already_official_overlap = not same_mapping_rows.empty
    target_conflict = not conflicting_rows.empty
    target_group_exists = bool(target_group_name) and target_group_name in official_alias_groups

    if already_official_overlap:
        overlap_status = "ALREADY_OFFICIAL_SAME_ALIAS_MAPPING"
    else:
        overlap_status = "NO_OFFICIAL_OVERLAP"

    if target_conflict:
        target_conflict_status = "TARGET_CONFLICT_ALIAS_LABEL_ALREADY_USED_FOR_DIFFERENT_METRIC"
    else:
        target_conflict_status = "NO_TARGET_CONFLICT"

    return {
        "target_asset_file": TARGET_ASSET_FILE,
        "target_asset_path": str(OFFICIAL_ALIAS_ASSET_PATH),
        "target_asset_exists": OFFICIAL_ALIAS_ASSET_PATH.exists(),
        "target_rule_family": "semantic_alias_candidates",
        "target_asset_group": target_group_name,
        "target_group_exists": target_group_exists,
        "target_group_resolution": "EXISTING_GROUP" if target_group_exists else "MISSING_GROUP",
        "operation": "ADD_ALIAS",
        "proposal_type": "alias",
        "already_official_overlap_status": overlap_status,
        "target_conflict_status": target_conflict_status,
        "existing_group_rule_ids": _join_unique(same_mapping_rows.get("rule_id", []).tolist(), limit=8)
        if not same_mapping_rows.empty
        else "",
        "conflicting_rule_ids": _join_unique(conflicting_rows.get("rule_id", []).tolist(), limit=8)
        if not conflicting_rows.empty
        else "",
    }


def build_controlled_official_proposal_from_325j(inputs: Dict[str, Any]) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    candidate_summary = inputs["candidate_summary"]
    candidate_qa = inputs["candidate_qa"]
    sandbox_summary = inputs["sandbox_summary"]
    candidates_df = inputs["candidates_df"]
    official_alias_df = inputs["official_alias_df"]
    official_alias_groups = inputs["official_alias_groups"]

    readiness_checks = [
        ("decision", EXPECTED_325J_DECISION),
        ("qa_fail_count", 0),
        ("ready_for_controlled_proposal_count", 6),
        ("alias_candidate_count", 6),
        ("official_overlap_count", 0),
        ("target_conflict_count", 0),
        ("adjusted_metric_mismatch_count", 0),
        ("diluted_eps_mismatch_count", 0),
    ]
    for key, expected in readiness_checks:
        actual = candidate_summary.get(key)
        ok = _safe_int(actual) == expected if isinstance(expected, int) else _norm(actual) == expected
        add_qa(f"readiness::325j_{key}", "PASS" if ok else "FAIL", f"expected={expected}; actual={actual}")

    add_qa(
        "readiness::325j_qa_json_fail_count",
        "PASS" if _safe_int(candidate_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(candidate_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::325i_decision_reference",
        "PASS"
        if _norm(sandbox_summary.get("decision"))
        == "ALIAS_HUMAN_CONFIRMED_SANDBOX_REPLAY_325I_READY_FOR_325J_OFFICIAL_RULE_CANDIDATES"
        else "FAIL",
        _norm(sandbox_summary.get("decision")),
    )

    ready_candidates_df = (
        candidates_df.loc[
            candidates_df["status"].astype(str) == "READY_FOR_CONTROLLED_PROPOSAL"
        ]
        .copy()
        .reset_index(drop=True)
        if not candidates_df.empty
        else pd.DataFrame()
    )
    add_qa(
        "inputs::loaded_ready_candidate_count",
        "PASS" if len(ready_candidates_df) == 6 else "FAIL",
        f"actual={len(ready_candidates_df)}",
    )
    add_qa(
        "inputs::loaded_ready_alias_candidate_count",
        "PASS"
        if not ready_candidates_df.empty
        and int(ready_candidates_df["candidate_type"].astype(str).eq("alias").sum()) == 6
        else "FAIL",
        f"actual={int(ready_candidates_df['candidate_type'].astype(str).eq('alias').sum()) if not ready_candidates_df.empty else 0}",
    )

    proposal_rows: List[Dict[str, Any]] = []
    plan_rows: List[Dict[str, Any]] = []
    provenance_rows: List[Dict[str, Any]] = []

    for index, (_, candidate_row) in enumerate(ready_candidates_df.iterrows(), start=1):
        row = candidate_row.to_dict()
        proposal_id = _proposal_id(index)
        target_plan = _target_plan_for_alias_candidate(row, official_alias_df, official_alias_groups)
        safety_checks = _safe_json_loads(row.get("safety_checks"))
        provenance = _safe_json_loads(row.get("provenance"))

        missing_provenance = not provenance or any(
            not _norm(provenance.get(field))
            for field in [
                "source_sandbox_rule_id",
                "source_confirmation_id_325h",
                "source_request_id_325e",
                "source_candidate_id_325a",
            ]
        )
        already_official_overlap = _norm(target_plan.get("already_official_overlap_status")).startswith(
            "ALREADY_OFFICIAL"
        )
        target_conflict = _norm(target_plan.get("target_conflict_status")).startswith("TARGET_CONFLICT")
        missing_target_asset_or_group = (
            not bool(target_plan.get("target_asset_exists"))
            or not bool(target_plan.get("target_group_exists"))
        )
        adjusted_metric_mismatch = bool(row.get("adjusted_metric_mismatch"))
        diluted_eps_mismatch = bool(row.get("diluted_eps_mismatch"))

        proposal_status = (
            "REJECTED"
            if target_conflict
            else "NEEDS_REVIEW"
            if already_official_overlap
            or missing_target_asset_or_group
            or missing_provenance
            or adjusted_metric_mismatch
            or diluted_eps_mismatch
            else "READY_FOR_DRY_RUN"
        )

        proposal_row = {
            "controlled_proposal_id": proposal_id,
            "proposal_type": "alias",
            "operation": "ADD_ALIAS",
            "proposal_status": proposal_status,
            "source_candidate_id_325j": _norm(row.get("candidate_id")),
            "source_sandbox_rule_id_325i": _norm(row.get("source_sandbox_rule_id")),
            "source_confirmation_id_325h": _norm(provenance.get("source_confirmation_id_325h")),
            "source_request_id_325e": _norm(provenance.get("source_request_id_325e")),
            "source_candidate_id_325a": _norm(provenance.get("source_candidate_id_325a")),
            "alias_label": _norm(row.get("alias_label")),
            "normalized_alias_label": _norm(row.get("normalized_alias_label")),
            "normalized_alias_label_key": _norm(row.get("normalized_alias_label_key")),
            "target_metric": _norm(row.get("target_metric")),
            "proposed_metric_code": _norm(row.get("proposed_metric_code")),
            "proposed_metric_family": _norm(row.get("proposed_metric_family")),
            "canonical_metric_name": _norm(row.get("canonical_metric_name")),
            "confidence": _norm(row.get("confidence")),
            "deterministic_gate_result": _norm(row.get("deterministic_gate_result")),
            "target_asset_file": _norm(target_plan.get("target_asset_file")),
            "target_asset_path": _norm(target_plan.get("target_asset_path")),
            "target_rule_family": _norm(target_plan.get("target_rule_family")),
            "target_asset_group": _norm(target_plan.get("target_asset_group")),
            "target_group_resolution": _norm(target_plan.get("target_group_resolution")),
            "already_official_overlap_status": _norm(target_plan.get("already_official_overlap_status")),
            "target_conflict_status": _norm(target_plan.get("target_conflict_status")),
            "existing_group_rule_ids": _norm(target_plan.get("existing_group_rule_ids")),
            "conflicting_rule_ids": _norm(target_plan.get("conflicting_rule_ids")),
            "target_asset_exists": bool(target_plan.get("target_asset_exists")),
            "target_group_exists": bool(target_plan.get("target_group_exists")),
            "expected_affected_candidate_count": _safe_int(row.get("expected_affected_candidate_count")),
            "expected_trusted_gain": _safe_int(row.get("expected_trusted_gain")),
            "expected_review_reduction": _safe_int(row.get("expected_review_reduction")),
            "expected_out_of_scope_or_rejected_gain": _safe_int(
                row.get("expected_out_of_scope_or_rejected_gain")
            ),
            "adjusted_metric_mismatch": adjusted_metric_mismatch,
            "diluted_eps_mismatch": diluted_eps_mismatch,
            "semantic_constraint_failures": _norm(row.get("semantic_constraint_failures")),
            "official_overlap": bool(safety_checks.get("official_overlap")) or already_official_overlap,
            "target_conflict": bool(safety_checks.get("target_conflict")) or target_conflict,
            "official_assets_modified": False,
            "eligible_for_325l_dry_run": proposal_status == "READY_FOR_DRY_RUN",
            "candidate_readiness_reason": _norm(row.get("candidate_readiness_reason")),
            "raw_candidate_provenance": json.dumps(provenance, ensure_ascii=False),
            "raw_candidate_safety_checks": json.dumps(safety_checks, ensure_ascii=False),
        }
        proposal_rows.append(proposal_row)

        plan_rows.append(
            {
                "controlled_proposal_id": proposal_id,
                "proposal_type": "alias",
                "operation": "ADD_ALIAS",
                "alias_label": proposal_row["alias_label"],
                "target_metric": proposal_row["target_metric"],
                "target_asset_file": proposal_row["target_asset_file"],
                "target_asset_group": proposal_row["target_asset_group"],
                "target_group_resolution": proposal_row["target_group_resolution"],
                "already_official_overlap_status": proposal_row["already_official_overlap_status"],
                "target_conflict_status": proposal_row["target_conflict_status"],
                "eligible_for_325l_dry_run": proposal_row["eligible_for_325l_dry_run"],
            }
        )

        provenance_rows.append(
            {
                "controlled_proposal_id": proposal_id,
                "source_candidate_id_325j": _norm(row.get("candidate_id")),
                "source_sandbox_rule_id_325i": _norm(provenance.get("source_sandbox_rule_id")),
                "source_confirmation_id_325h": _norm(provenance.get("source_confirmation_id_325h")),
                "source_request_id_325e": _norm(provenance.get("source_request_id_325e")),
                "source_candidate_id_325a": _norm(provenance.get("source_candidate_id_325a")),
                "source_stage_325i": _norm(provenance.get("source_stage_325i")),
                "source_stage_325g": _norm(provenance.get("source_stage_325g")),
                "source_stage_325h": _norm(provenance.get("source_stage_325h")),
                "raw_325i_provenance": _norm(provenance.get("raw_325i_provenance")),
            }
        )

    proposal_overview_df = pd.DataFrame(proposal_rows).fillna("")
    alias_proposals_df = proposal_overview_df.copy()
    scope_proposals_df = pd.DataFrame(columns=proposal_overview_df.columns).fillna("")
    target_asset_plan_df = pd.DataFrame(plan_rows).fillna("")
    provenance_df = pd.DataFrame(provenance_rows).fillna("")

    duplicate_proposal_id_count = (
        int(proposal_overview_df["controlled_proposal_id"].astype(str).duplicated().sum())
        if not proposal_overview_df.empty
        else 0
    )
    already_official_overlap_count = (
        int(
            proposal_overview_df["already_official_overlap_status"]
            .astype(str)
            .str.startswith("ALREADY_OFFICIAL")
            .sum()
        )
        if not proposal_overview_df.empty
        else 0
    )
    target_conflict_count = (
        int(
            proposal_overview_df["target_conflict_status"]
            .astype(str)
            .str.startswith("TARGET_CONFLICT")
            .sum()
        )
        if not proposal_overview_df.empty
        else 0
    )
    missing_target_asset_or_group_count = (
        int(
            (
                ~proposal_overview_df["target_asset_exists"].astype(bool)
                | ~proposal_overview_df["target_group_exists"].astype(bool)
            ).sum()
        )
        if not proposal_overview_df.empty
        else 0
    )
    missing_provenance_count = (
        int(
            proposal_overview_df[
                proposal_overview_df["source_sandbox_rule_id_325i"].astype(str).eq("")
                | proposal_overview_df["source_confirmation_id_325h"].astype(str).eq("")
                | proposal_overview_df["source_request_id_325e"].astype(str).eq("")
                | proposal_overview_df["source_candidate_id_325a"].astype(str).eq("")
                | proposal_overview_df["source_candidate_id_325j"].astype(str).eq("")
            ].shape[0]
        )
        if not proposal_overview_df.empty
        else 0
    )
    adjusted_metric_mismatch_count = (
        int(proposal_overview_df["adjusted_metric_mismatch"].astype(bool).sum())
        if not proposal_overview_df.empty
        else 0
    )
    diluted_eps_mismatch_count = (
        int(proposal_overview_df["diluted_eps_mismatch"].astype(bool).sum())
        if not proposal_overview_df.empty
        else 0
    )
    ready_proposal_count = (
        int(proposal_overview_df["proposal_status"].astype(str).eq("READY_FOR_DRY_RUN").sum())
        if not proposal_overview_df.empty
        else 0
    )
    review_proposal_count = (
        int(proposal_overview_df["proposal_status"].astype(str).eq("NEEDS_REVIEW").sum())
        if not proposal_overview_df.empty
        else 0
    )
    rejected_proposal_count = (
        int(proposal_overview_df["proposal_status"].astype(str).eq("REJECTED").sum())
        if not proposal_overview_df.empty
        else 0
    )

    proposal_checks = [
        ("proposal_counts::total", len(proposal_overview_df), 6),
        ("proposal_counts::alias", len(alias_proposals_df), 6),
        ("proposal_counts::scope", len(scope_proposals_df), 0),
        ("proposal_counts::ready", ready_proposal_count, 6),
        ("proposal_counts::needs_review", review_proposal_count, 0),
        ("proposal_counts::rejected", rejected_proposal_count, 0),
        ("target_plan::target_asset_plan_count", len(target_asset_plan_df), 6),
        (
            "target_plan::target_asset_file_count",
            len(_dedupe_preserve(target_asset_plan_df["target_asset_file"].tolist()))
            if not target_asset_plan_df.empty
            else 0,
            1,
        ),
        ("target_plan::duplicate_proposal_id_count", duplicate_proposal_id_count, 0),
        ("target_plan::already_official_overlap_count", already_official_overlap_count, 0),
        ("target_plan::target_conflict_count", target_conflict_count, 0),
        ("target_plan::missing_target_asset_or_group_count", missing_target_asset_or_group_count, 0),
        ("provenance::missing_provenance_count", missing_provenance_count, 0),
        ("semantic::adjusted_metric_mismatch_count", adjusted_metric_mismatch_count, 0),
        ("semantic::diluted_eps_mismatch_count", diluted_eps_mismatch_count, 0),
    ]
    for name, actual, expected in proposal_checks:
        add_qa(name, "PASS" if actual == expected else "FAIL", f"expected={expected}; actual={actual}")

    expected_affected_candidate_count = (
        int(pd.to_numeric(proposal_overview_df["expected_affected_candidate_count"], errors="coerce").fillna(0).sum())
        if not proposal_overview_df.empty
        else 0
    )
    expected_trusted_gain = (
        int(pd.to_numeric(proposal_overview_df["expected_trusted_gain"], errors="coerce").fillna(0).sum())
        if not proposal_overview_df.empty
        else 0
    )
    expected_review_reduction = (
        int(pd.to_numeric(proposal_overview_df["expected_review_reduction"], errors="coerce").fillna(0).sum())
        if not proposal_overview_df.empty
        else 0
    )
    expected_out_of_scope_or_rejected_gain = (
        int(
            pd.to_numeric(
                proposal_overview_df["expected_out_of_scope_or_rejected_gain"], errors="coerce"
            )
            .fillna(0)
            .sum()
        )
        if not proposal_overview_df.empty
        else 0
    )
    impact_checks = [
        ("impact::expected_affected_candidate_count", expected_affected_candidate_count, 45),
        ("impact::expected_trusted_gain", expected_trusted_gain, 45),
        ("impact::expected_review_reduction", expected_review_reduction, 45),
        (
            "impact::expected_out_of_scope_or_rejected_gain",
            expected_out_of_scope_or_rejected_gain,
            0,
        ),
    ]
    for name, actual, expected in impact_checks:
        add_qa(name, "PASS" if actual == expected else "FAIL", f"expected={expected}; actual={actual}")

    official_hashes_after = _official_hashes()
    official_assets_modified = inputs["official_hashes_before"] != official_hashes_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if not official_assets_modified else "FAIL",
        json.dumps(
            {"before": inputs["official_hashes_before"], "after": official_hashes_after},
            ensure_ascii=False,
        ),
    )
    add_qa(
        "safety::proposal_only_no_apply_confirmed",
        "PASS",
        "325K creates controlled official proposals only and does not run dry run or apply official patches.",
    )
    add_qa(
        "safety::no_llm_or_adjudicator_called",
        "PASS",
        "325K uses cached 325J and 325I evidence only.",
    )

    qa_checks_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_checks_df["status"] == "PASS").sum()) if not qa_checks_df.empty else 0
    qa_warn_count = int((qa_checks_df["status"] == "WARN").sum()) if not qa_checks_df.empty else 0
    qa_fail_count = int((qa_checks_df["status"] == "FAIL").sum()) if not qa_checks_df.empty else 0
    blocking_reasons = (
        qa_checks_df.loc[qa_checks_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_checks_df.empty
        else []
    )

    summary = {
        "stage": "325K",
        "output_dir": "",
        "loaded_ready_candidate_count": int(len(ready_candidates_df)),
        "proposal_count": int(len(proposal_overview_df)),
        "alias_proposal_count": int(len(alias_proposals_df)),
        "scope_proposal_count": int(len(scope_proposals_df)),
        "ready_for_dry_run_proposal_count": ready_proposal_count,
        "needs_review_proposal_count": review_proposal_count,
        "rejected_proposal_count": rejected_proposal_count,
        "target_asset_plan_count": int(len(target_asset_plan_df)),
        "target_asset_file_count": int(
            len(_dedupe_preserve(target_asset_plan_df["target_asset_file"].tolist()))
        )
        if not target_asset_plan_df.empty
        else 0,
        "duplicate_proposal_id_count": duplicate_proposal_id_count,
        "already_official_overlap_count": already_official_overlap_count,
        "target_conflict_count": target_conflict_count,
        "missing_target_asset_or_group_count": missing_target_asset_or_group_count,
        "missing_provenance_count": missing_provenance_count,
        "adjusted_metric_mismatch_count": adjusted_metric_mismatch_count,
        "diluted_eps_mismatch_count": diluted_eps_mismatch_count,
        "expected_affected_candidate_count": expected_affected_candidate_count,
        "expected_trusted_gain": expected_trusted_gain,
        "expected_review_reduction": expected_review_reduction,
        "expected_out_of_scope_or_rejected_gain": expected_out_of_scope_or_rejected_gain,
        "official_assets_modified": official_assets_modified,
        "official_assets_written": [],
        "official_asset_hashes_before": inputs["official_hashes_before"],
        "official_asset_hashes_after": official_hashes_after,
        "proposal_only_no_apply_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": NOT_READY_DECISION if qa_fail_count else READY_DECISION,
    }

    proposal_package = {
        "stage": "325K",
        "decision": summary["decision"],
        "source_readiness_summary": {
            "alias_official_rule_candidate_decision_325j": _norm(candidate_summary.get("decision")),
            "loaded_ready_candidate_count": summary["loaded_ready_candidate_count"],
        },
        "controlled_proposals": proposal_overview_df.to_dict(orient="records"),
        "alias_proposals": alias_proposals_df.to_dict(orient="records"),
        "scope_proposals": scope_proposals_df.to_dict(orient="records"),
        "target_asset_plan": target_asset_plan_df.to_dict(orient="records"),
        "provenance_records": provenance_df.to_dict(orient="records"),
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_checks_df.to_dict(orient="records"),
    }

    no_apply_proof = {
        "stage": "325K",
        "decision": summary["decision"],
        "official_assets_written": [],
        "official_assets_modified": official_assets_modified,
        "files_written_to_official_assets": [],
        "dry_run_executed": False,
        "official_patches_applied": False,
        "semantic_rules_applied": False,
        "trusted_marked_in_production": False,
        "llm_or_adjudicator_called": False,
    }

    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "proposal_only",
                "detail": "325K creates controlled official proposals only and does not run dry run or apply official patches.",
            },
            {
                "limitation": "ready_candidates_only",
                "detail": "325K processes only the 6 READY_FOR_CONTROLLED_PROPOSAL alias candidates from 325J.",
            },
            {
                "limitation": "existing_groups_only",
                "detail": "325K resolves target asset groups from existing semantic_alias_candidates.json groups and does not create missing groups.",
            },
        ]
    ).fillna("")

    return {
        "summary": summary,
        "qa_json": qa_json,
        "proposal_package": proposal_package,
        "no_apply_proof": no_apply_proof,
        "proposal_overview_df": proposal_overview_df,
        "alias_proposals_df": alias_proposals_df,
        "scope_proposals_df": scope_proposals_df,
        "target_asset_plan_df": target_asset_plan_df,
        "provenance_df": provenance_df,
        "qa_checks_df": qa_checks_df,
        "known_limitations_df": known_limitations_df,
    }
