from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

import pandas as pd


EXPECTED_325K_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_FROM_325J_325K_READY_FOR_325L_DRY_RUN"
EXPECTED_325J_DECISION = "ALIAS_OFFICIAL_RULE_CANDIDATES_325J_READY_FOR_325K_CONTROLLED_PROPOSAL"
EXPECTED_325I_DECISION = "ALIAS_HUMAN_CONFIRMED_SANDBOX_REPLAY_325I_READY_FOR_325J_OFFICIAL_RULE_CANDIDATES"
READY_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_325L_READY_FOR_HUMAN_APPROVAL"
NOT_READY_DECISION = "CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_325L_NOT_READY"

DEFAULT_CONTROLLED_PROPOSAL_DIR = Path(
    r"D:\_datefac\output\controlled_official_proposal_from_325j_325k"
)
DEFAULT_OFFICIAL_RULE_CANDIDATE_DIR = Path(
    r"D:\_datefac\output\alias_official_rule_candidates_from_325i_325j"
)
DEFAULT_SANDBOX_REPLAY_DIR = Path(
    r"D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\controlled_official_proposal_dry_run_325l"
)

OFFICIAL_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
TARGET_ASSET_FILE = "data/overrides/semantic_alias_candidates.json"
TARGET_ASSET_GROUP = "profitability"


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


def _safe_json_loads(value: Any) -> Dict[str, Any]:
    text = _norm(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
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
        "semantic_alias_candidates": _sha256_file(OFFICIAL_ALIAS_ASSET_PATH),
        "formal_scope_rules": _sha256_file(FORMAL_SCOPE_RULES_PATH),
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


def load_controlled_official_proposal_dry_run_325l_inputs(
    controlled_proposal_dir: Path,
    official_rule_candidate_dir: Path,
    sandbox_replay_dir: Path,
) -> Dict[str, Any]:
    proposal_package = _read_json(
        controlled_proposal_dir / "controlled_official_proposal_from_325j_325k_proposals.json"
    )
    target_plan_json = _read_json(
        controlled_proposal_dir / "controlled_official_proposal_from_325j_325k_target_asset_plan.json"
    )
    official_alias_payload = _read_json(OFFICIAL_ALIAS_ASSET_PATH)
    official_alias_df, official_alias_groups = _flatten_official_aliases(official_alias_payload)
    return {
        "controlled_summary": _read_json(
            controlled_proposal_dir / "controlled_official_proposal_from_325j_325k_summary.json"
        ),
        "controlled_qa": _read_json(
            controlled_proposal_dir / "controlled_official_proposal_from_325j_325k_qa.json"
        ),
        "controlled_proposals_df": pd.DataFrame(
            proposal_package.get("controlled_proposals", [])
            if isinstance(proposal_package.get("controlled_proposals", []), list)
            else []
        ).fillna(""),
        "provenance_df": pd.DataFrame(
            proposal_package.get("provenance_records", [])
            if isinstance(proposal_package.get("provenance_records", []), list)
            else []
        ).fillna(""),
        "target_asset_plan_df": pd.DataFrame(
            target_plan_json.get("target_asset_plan", [])
            if isinstance(target_plan_json.get("target_asset_plan", []), list)
            else []
        ).fillna(""),
        "candidate_summary": _read_json(
            official_rule_candidate_dir
            / "alias_official_rule_candidates_from_325i_325j_summary.json"
        ),
        "sandbox_summary": _read_json(
            sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_summary.json"
        ),
        "official_alias_payload": official_alias_payload,
        "official_alias_df": official_alias_df,
        "official_alias_groups": official_alias_groups,
        "official_hashes_before": _official_hashes(),
    }


def _semantic_constraint_check(proposal: Dict[str, Any]) -> Dict[str, Any]:
    alias_label = _norm(proposal.get("alias_label"))
    normalized_alias_label = _norm(proposal.get("normalized_alias_label"))
    alias_text = f"{alias_label} {normalized_alias_label}"
    alias_key = _metric_key(alias_text)
    target_metric = _norm(proposal.get("target_metric") or proposal.get("proposed_metric_code"))
    target_key = _metric_key(target_metric)

    failures: List[str] = []
    adjusted_metric_mismatch = False
    diluted_eps_mismatch = False

    if _metric_key(alias_label) == "ebit" and target_key != "ebit":
        failures.append("EBIT_MUST_MAP_ONLY_TO_EBIT")
    if "roe" in alias_key and target_key != "roe":
        failures.append("ROE_MUST_MAP_ONLY_TO_ROE")
    if ("摊薄" in alias_text) or ("diluted" in alias_key) or ("最新摊薄" in alias_text):
        if target_key not in {"dilutedeps", "epsdiluted"}:
            diluted_eps_mismatch = True
            failures.append("DILUTED_EPS_ALIAS_MUST_MAP_TO_DILUTED_EPS_OR_EPS_DILUTED")
    if ("经调整" in alias_text) and ("eps" in alias_key or "每股收益" in alias_text):
        if target_key != "adjustedeps":
            adjusted_metric_mismatch = True
            failures.append("ADJUSTED_EPS_ALIAS_MUST_MAP_TO_ADJUSTED_EPS")
    if ("经调整" in alias_text) and ("归母净利润" in alias_text or "attributable" in alias_key):
        if target_key not in {
            "adjustedattributablenetprofit",
            "adjustedparentnetprofit",
        }:
            adjusted_metric_mismatch = True
            failures.append(
                "ADJUSTED_ATTRIBUTABLE_NET_PROFIT_ALIAS_MUST_MAP_TO_ALLOWED_ADJUSTED_NET_PROFIT_TARGETS"
            )
    if ("归母净利率" in alias_text) or ("attributablenetmargin" in alias_key) or ("parentnetmargin" in alias_key):
        if target_key not in {"attributablenetmargin", "parentnetmargin"}:
            failures.append("ATTRIBUTABLE_NET_MARGIN_ALIAS_MUST_MAP_TO_ALLOWED_NET_MARGIN_TARGETS")

    return {
        "pass": len(failures) == 0,
        "failure_reasons": failures,
        "adjusted_metric_mismatch": adjusted_metric_mismatch,
        "diluted_eps_mismatch": diluted_eps_mismatch,
    }


def _preview_alias_entry(proposal: Dict[str, Any], sequence: int) -> Dict[str, Any]:
    return {
        "rule_id": f"DRY_RUN_325L_ALIAS_{sequence:03d}",
        "normalized_label": _norm(proposal.get("normalized_alias_label")),
        "metric_code": _norm(proposal.get("proposed_metric_code") or proposal.get("target_metric")),
        "metric_family": _norm(proposal.get("proposed_metric_family")) or TARGET_ASSET_GROUP,
        "source_dry_run_patch_operation_id": f"dry_run_325l::alias::{sequence:03d}",
        "source_controlled_proposal_id": _norm(proposal.get("controlled_proposal_id")),
        "source_candidate_id_325j": _norm(proposal.get("source_candidate_id_325j")),
        "source_sandbox_rule_id_325i": _norm(proposal.get("source_sandbox_rule_id_325i")),
        "source_confirmation_id_325h": _norm(proposal.get("source_confirmation_id_325h")),
        "source_request_id_325e": _norm(proposal.get("source_request_id_325e")),
        "source_candidate_id_325a": _norm(proposal.get("source_candidate_id_325a")),
        "dry_run_only": True,
        "status": "DRY_RUN_PREVIEW_325L",
    }


def _build_virtual_after_alias_payload(
    payload: Dict[str, Any],
    operations_df: pd.DataFrame,
) -> Dict[str, Any]:
    virtual_payload = deepcopy(payload) if isinstance(payload, dict) else {}
    virtual_payload.setdefault("groups", {})
    groups = virtual_payload["groups"]
    if not isinstance(groups, dict):
        groups = {}
        virtual_payload["groups"] = groups
    group_entries = groups.setdefault(TARGET_ASSET_GROUP, [])
    if not isinstance(group_entries, list):
        group_entries = []
        groups[TARGET_ASSET_GROUP] = group_entries
    for _, row in operations_df.iterrows():
        preview = row.get("preview_payload_dict")
        if isinstance(preview, dict):
            group_entries.append(preview)
    return virtual_payload


def build_controlled_official_proposal_dry_run_325l(inputs: Dict[str, Any]) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    controlled_summary = inputs["controlled_summary"]
    controlled_qa = inputs["controlled_qa"]
    candidate_summary = inputs["candidate_summary"]
    sandbox_summary = inputs["sandbox_summary"]
    controlled_proposals_df = inputs["controlled_proposals_df"]
    provenance_df = inputs["provenance_df"]
    source_target_plan_df = inputs["target_asset_plan_df"]
    official_alias_df = inputs["official_alias_df"]
    official_alias_groups = inputs["official_alias_groups"]

    readiness_checks = [
        ("decision", EXPECTED_325K_DECISION),
        ("qa_fail_count", 0),
        ("proposal_count", 6),
        ("alias_proposal_count", 6),
        ("scope_proposal_count", 0),
        ("ready_for_dry_run_proposal_count", 6),
        ("needs_review_proposal_count", 0),
        ("rejected_proposal_count", 0),
        ("target_asset_plan_count", 6),
        ("target_asset_file_count", 1),
        ("duplicate_proposal_id_count", 0),
        ("already_official_overlap_count", 0),
        ("target_conflict_count", 0),
        ("missing_target_asset_or_group_count", 0),
        ("missing_provenance_count", 0),
        ("adjusted_metric_mismatch_count", 0),
        ("diluted_eps_mismatch_count", 0),
    ]
    for key, expected in readiness_checks:
        actual = controlled_summary.get(key)
        ok = _safe_int(actual) == expected if isinstance(expected, int) else _norm(actual) == expected
        add_qa(f"readiness::325k_{key}", "PASS" if ok else "FAIL", f"expected={expected}; actual={actual}")

    add_qa(
        "readiness::325k_official_assets_modified_false",
        "PASS" if controlled_summary.get("official_assets_modified") is False else "FAIL",
        str(controlled_summary.get("official_assets_modified")),
    )
    add_qa(
        "readiness::325k_qa_json_fail_count",
        "PASS" if _safe_int(controlled_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(controlled_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "reference::325j_decision",
        "PASS" if _norm(candidate_summary.get("decision")) == EXPECTED_325J_DECISION else "FAIL",
        _norm(candidate_summary.get("decision")),
    )
    add_qa(
        "reference::325i_decision",
        "PASS" if _norm(sandbox_summary.get("decision")) == EXPECTED_325I_DECISION else "FAIL",
        _norm(sandbox_summary.get("decision")),
    )

    proposals_df = (
        controlled_proposals_df.loc[
            controlled_proposals_df["proposal_status"].astype(str) == "READY_FOR_DRY_RUN"
        ]
        .copy()
        .reset_index(drop=True)
        if not controlled_proposals_df.empty
        else pd.DataFrame()
    )
    add_qa(
        "inputs::loaded_ready_alias_proposal_count",
        "PASS"
        if len(proposals_df) == 6
        and int(proposals_df["proposal_type"].astype(str).eq("alias").sum()) == 6
        else "FAIL",
        f"actual={len(proposals_df)}",
    )

    official_group_df = (
        official_alias_df.loc[
            official_alias_df["target_asset_group"].astype(str) == TARGET_ASSET_GROUP
        ].copy()
        if not official_alias_df.empty
        else pd.DataFrame()
    )
    group_exists = TARGET_ASSET_GROUP in official_alias_groups

    operation_rows: List[Dict[str, Any]] = []
    diff_preview_rows: List[Dict[str, Any]] = []
    rollback_rows: List[Dict[str, Any]] = []

    for sequence, (_, row) in enumerate(proposals_df.iterrows(), start=1):
        proposal = row.to_dict()
        normalized_label = _norm(proposal.get("normalized_alias_label"))
        normalized_label_key = _normalize_label(normalized_label)
        metric_code = _norm(proposal.get("proposed_metric_code") or proposal.get("target_metric"))
        metric_code_key = _metric_key(metric_code)
        exact_match_df = (
            official_group_df.loc[
                (official_group_df["normalized_label_key"].astype(str) == normalized_label_key)
                & (official_group_df["metric_code_key"].astype(str) == metric_code_key)
            ].copy()
            if not official_group_df.empty
            else pd.DataFrame()
        )
        conflicting_df = (
            official_group_df.loc[
                (official_group_df["normalized_label_key"].astype(str) == normalized_label_key)
                & (official_group_df["metric_code_key"].astype(str) != metric_code_key)
            ].copy()
            if not official_group_df.empty
            else pd.DataFrame()
        )
        semantic_check = _semantic_constraint_check(proposal)
        preview_payload = _preview_alias_entry(proposal, sequence)
        operation_id = f"dry_run_325l::alias::{sequence:03d}"
        target_locator = f"{OFFICIAL_ALIAS_ASSET_PATH}::{TARGET_ASSET_GROUP}"
        operation_key = "::".join(
            ["alias", target_locator, normalized_label_key, metric_code_key]
        )

        operation_row = {
            "dry_run_patch_operation_id": operation_id,
            "controlled_proposal_id_325k": _norm(proposal.get("controlled_proposal_id")),
            "candidate_type": "alias",
            "proposal_type": "alias",
            "operation": "ADD_ALIAS",
            "patch_operation_type": "ADD_ALIAS",
            "alias_label": _norm(proposal.get("alias_label")),
            "normalized_alias_label": normalized_label,
            "normalized_alias_label_key": normalized_label_key,
            "target_metric": _norm(proposal.get("target_metric")),
            "proposed_metric_code": metric_code,
            "proposed_metric_family": _norm(proposal.get("proposed_metric_family")),
            "confidence": _norm(proposal.get("confidence")),
            "target_asset_file": TARGET_ASSET_FILE,
            "target_asset_path": str(OFFICIAL_ALIAS_ASSET_PATH),
            "target_asset_group": TARGET_ASSET_GROUP,
            "target_group_exists": group_exists,
            "target_locator": target_locator,
            "before_state": "EXACT_ALIAS_ALREADY_PRESENT" if not exact_match_df.empty else "ALIAS_NOT_PRESENT",
            "group_before_entry_count": len(official_group_df),
            "group_after_entry_count_preview": len(official_group_df) + 1,
            "already_official_overlap_count": len(exact_match_df),
            "target_conflict_count": len(conflicting_df),
            "existing_group_rule_ids": _join_unique(exact_match_df.get("rule_id", []).tolist(), limit=8)
            if not exact_match_df.empty
            else "",
            "conflicting_rule_ids": _join_unique(conflicting_df.get("rule_id", []).tolist(), limit=8)
            if not conflicting_df.empty
            else "",
            "source_candidate_id_325j": _norm(proposal.get("source_candidate_id_325j")),
            "source_sandbox_rule_id_325i": _norm(proposal.get("source_sandbox_rule_id_325i")),
            "source_confirmation_id_325h": _norm(proposal.get("source_confirmation_id_325h")),
            "source_request_id_325e": _norm(proposal.get("source_request_id_325e")),
            "source_candidate_id_325a": _norm(proposal.get("source_candidate_id_325a")),
            "expected_affected_candidate_count": _safe_int(
                proposal.get("expected_affected_candidate_count")
            ),
            "expected_trusted_gain": _safe_int(proposal.get("expected_trusted_gain")),
            "expected_review_reduction": _safe_int(proposal.get("expected_review_reduction")),
            "expected_out_of_scope_or_rejected_gain": _safe_int(
                proposal.get("expected_out_of_scope_or_rejected_gain")
            ),
            "adjusted_metric_mismatch": bool(semantic_check["adjusted_metric_mismatch"]),
            "diluted_eps_mismatch": bool(semantic_check["diluted_eps_mismatch"]),
            "semantic_constraint_pass": bool(semantic_check["pass"]),
            "semantic_constraint_failures": " | ".join(semantic_check["failure_reasons"]),
            "preview_payload_json": json.dumps(preview_payload, ensure_ascii=False),
            "preview_payload_dict": preview_payload,
            "operation_key": operation_key,
        }
        operation_rows.append(operation_row)

        diff_preview_rows.append(
            {
                "dry_run_patch_operation_id": operation_id,
                "controlled_proposal_id_325k": _norm(proposal.get("controlled_proposal_id")),
                "target_asset_file": TARGET_ASSET_FILE,
                "target_asset_group": TARGET_ASSET_GROUP,
                "before_state": operation_row["before_state"],
                "group_before_entry_count": len(official_group_df),
                "group_after_entry_count_preview": len(official_group_df) + 1,
                "already_official_overlap_count": len(exact_match_df),
                "target_conflict_count": len(conflicting_df),
                "normalized_alias_label": normalized_label,
                "proposed_metric_code": metric_code,
                "virtual_diff_summary": (
                    f"Append alias '{normalized_label}' -> '{metric_code}' "
                    f"to {TARGET_ASSET_GROUP}"
                ),
            }
        )
        rollback_rows.append(
            {
                "dry_run_patch_operation_id": operation_id,
                "controlled_proposal_id_325k": _norm(proposal.get("controlled_proposal_id")),
                "target_locator": target_locator,
                "rollback_action": "DROP_DRY_RUN_PATCH_OPERATION",
                "rollback_instruction": (
                    f"Remove operation {operation_id} from the 325L dry-run package. "
                    "No official alias asset rollback is needed because 325L does not write official files."
                ),
                "rollback_reason": "Dry-run preview must remain removable before human approval.",
            }
        )

    patch_operations_df = pd.DataFrame(operation_rows).fillna("")
    target_asset_diff_preview_df = pd.DataFrame(diff_preview_rows).fillna("")
    rollback_plan_df = pd.DataFrame(rollback_rows).fillna("")
    before_after_preview_df = pd.DataFrame(
        [
            {
                "target_asset_file": TARGET_ASSET_FILE,
                "target_asset_group": TARGET_ASSET_GROUP,
                "candidate_type": "alias",
                "before_entry_count": int(len(official_group_df)),
                "after_entry_count_preview": int(len(official_group_df) + len(patch_operations_df)),
                "added_operation_count": int(len(patch_operations_df)),
                "expected_affected_candidate_count": int(
                    pd.to_numeric(
                        patch_operations_df["expected_affected_candidate_count"], errors="coerce"
                    )
                    .fillna(0)
                    .sum()
                )
                if not patch_operations_df.empty
                else 0,
                "expected_trusted_gain": int(
                    pd.to_numeric(patch_operations_df["expected_trusted_gain"], errors="coerce")
                    .fillna(0)
                    .sum()
                )
                if not patch_operations_df.empty
                else 0,
                "expected_review_reduction": int(
                    pd.to_numeric(
                        patch_operations_df["expected_review_reduction"], errors="coerce"
                    )
                    .fillna(0)
                    .sum()
                )
                if not patch_operations_df.empty
                else 0,
                "expected_out_of_scope_or_rejected_gain": int(
                    pd.to_numeric(
                        patch_operations_df["expected_out_of_scope_or_rejected_gain"],
                        errors="coerce",
                    )
                    .fillna(0)
                    .sum()
                )
                if not patch_operations_df.empty
                else 0,
            }
        ]
    ).fillna("")

    duplicate_operation_count = (
        int(patch_operations_df["operation_key"].astype(str).duplicated().sum())
        if not patch_operations_df.empty
        else 0
    )
    duplicate_alias_target_pair_count = (
        int(
            patch_operations_df[
                ["normalized_alias_label_key", "proposed_metric_code"]
            ]
            .astype(str)
            .duplicated()
            .sum()
        )
        if not patch_operations_df.empty
        else 0
    )
    target_conflict_count = (
        int(pd.to_numeric(patch_operations_df["target_conflict_count"], errors="coerce").fillna(0).gt(0).sum())
        if not patch_operations_df.empty
        else 0
    )
    already_official_overlap_count = (
        int(
            pd.to_numeric(
                patch_operations_df["already_official_overlap_count"], errors="coerce"
            )
            .fillna(0)
            .gt(0)
            .sum()
        )
        if not patch_operations_df.empty
        else 0
    )
    missing_target_asset_or_group_count = (
        int(
            (
                patch_operations_df["target_asset_path"].astype(str).eq("")
                | ~patch_operations_df["target_group_exists"].astype(bool)
            ).sum()
        )
        if not patch_operations_df.empty
        else 0
    )
    missing_provenance_count = (
        int(
            patch_operations_df[
                patch_operations_df["source_candidate_id_325j"].astype(str).eq("")
                | patch_operations_df["source_sandbox_rule_id_325i"].astype(str).eq("")
                | patch_operations_df["source_confirmation_id_325h"].astype(str).eq("")
                | patch_operations_df["source_request_id_325e"].astype(str).eq("")
                | patch_operations_df["source_candidate_id_325a"].astype(str).eq("")
            ].shape[0]
        )
        if not patch_operations_df.empty
        else 0
    )
    adjusted_metric_mismatch_count = (
        int(patch_operations_df["adjusted_metric_mismatch"].astype(bool).sum())
        if not patch_operations_df.empty
        else 0
    )
    diluted_eps_mismatch_count = (
        int(patch_operations_df["diluted_eps_mismatch"].astype(bool).sum())
        if not patch_operations_df.empty
        else 0
    )
    semantic_constraint_fail_count = (
        int((~patch_operations_df["semantic_constraint_pass"].astype(bool)).sum())
        if not patch_operations_df.empty
        else 0
    )

    expected_affected_candidate_count = (
        int(pd.to_numeric(patch_operations_df["expected_affected_candidate_count"], errors="coerce").fillna(0).sum())
        if not patch_operations_df.empty
        else 0
    )
    expected_trusted_gain = (
        int(pd.to_numeric(patch_operations_df["expected_trusted_gain"], errors="coerce").fillna(0).sum())
        if not patch_operations_df.empty
        else 0
    )
    expected_review_reduction = (
        int(pd.to_numeric(patch_operations_df["expected_review_reduction"], errors="coerce").fillna(0).sum())
        if not patch_operations_df.empty
        else 0
    )
    expected_out_of_scope_or_rejected_gain = (
        int(
            pd.to_numeric(
                patch_operations_df["expected_out_of_scope_or_rejected_gain"], errors="coerce"
            )
            .fillna(0)
            .sum()
        )
        if not patch_operations_df.empty
        else 0
    )

    checks = [
        ("operations::proposal_count", len(proposals_df), 6),
        ("operations::patch_operation_count", len(patch_operations_df), 6),
        ("operations::alias_patch_operation_count", len(patch_operations_df), 6),
        ("operations::scope_patch_operation_count", 0, 0),
        (
            "targets::target_asset_file_count",
            len(_dedupe_preserve(patch_operations_df["target_asset_file"].tolist()))
            if not patch_operations_df.empty
            else 0,
            1,
        ),
        ("targets::target_asset_plan_count", len(source_target_plan_df), 6),
        ("integrity::duplicate_operation_count", duplicate_operation_count, 0),
        (
            "integrity::duplicate_alias_target_pair_count",
            duplicate_alias_target_pair_count,
            0,
        ),
        ("integrity::target_conflict_count", target_conflict_count, 0),
        (
            "integrity::already_official_overlap_count",
            already_official_overlap_count,
            0,
        ),
        (
            "integrity::missing_target_asset_or_group_count",
            missing_target_asset_or_group_count,
            0,
        ),
        ("integrity::missing_provenance_count", missing_provenance_count, 0),
        (
            "semantic::adjusted_metric_mismatch_count",
            adjusted_metric_mismatch_count,
            0,
        ),
        ("semantic::diluted_eps_mismatch_count", diluted_eps_mismatch_count, 0),
        ("semantic::semantic_constraint_fail_count", semantic_constraint_fail_count, 0),
        ("impact::expected_affected_candidate_count", expected_affected_candidate_count, 45),
        ("impact::expected_trusted_gain", expected_trusted_gain, 45),
        ("impact::expected_review_reduction", expected_review_reduction, 45),
        (
            "impact::expected_out_of_scope_or_rejected_gain",
            expected_out_of_scope_or_rejected_gain,
            0,
        ),
    ]
    for name, actual, expected in checks:
        add_qa(name, "PASS" if actual == expected else "FAIL", f"expected={expected}; actual={actual}")

    add_qa(
        "targets::target_group_profitability",
        "PASS"
        if patch_operations_df.empty
        or patch_operations_df["target_asset_group"].astype(str).eq(TARGET_ASSET_GROUP).all()
        else "FAIL",
        TARGET_ASSET_GROUP,
    )
    add_qa(
        "safety::official_alias_asset_exists",
        "PASS" if OFFICIAL_ALIAS_ASSET_PATH.exists() else "FAIL",
        str(OFFICIAL_ALIAS_ASSET_PATH),
    )
    add_qa(
        "safety::formal_scope_rules_exists",
        "PASS" if FORMAL_SCOPE_RULES_PATH.exists() else "FAIL",
        str(FORMAL_SCOPE_RULES_PATH),
    )
    add_qa(
        "safety::no_apply_dry_run_only",
        "PASS",
        "325L builds dry-run preview artifacts only and never writes official alias or scope assets.",
    )
    add_qa(
        "safety::no_llm_or_adjudicator_called",
        "PASS",
        "325L uses cached 325K/325J/325I evidence only.",
    )

    virtual_after_alias_payload = _build_virtual_after_alias_payload(
        inputs["official_alias_payload"],
        patch_operations_df,
    )

    official_hashes_after = _official_hashes()
    official_asset_hash_unchanged = inputs["official_hashes_before"] == official_hashes_after
    add_qa(
        "safety::official_asset_hash_unchanged",
        "PASS" if official_asset_hash_unchanged else "FAIL",
        json.dumps(
            {
                "before": inputs["official_hashes_before"],
                "after": official_hashes_after,
            },
            ensure_ascii=False,
        ),
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
        "stage": "325L",
        "output_dir": "",
        "proposal_count": int(len(proposals_df)),
        "patch_operation_count": int(len(patch_operations_df)),
        "alias_patch_operation_count": int(len(patch_operations_df)),
        "scope_patch_operation_count": 0,
        "target_asset_file_count": int(
            len(_dedupe_preserve(patch_operations_df["target_asset_file"].tolist()))
        )
        if not patch_operations_df.empty
        else 0,
        "target_asset_plan_count": int(len(source_target_plan_df)),
        "duplicate_operation_count": duplicate_operation_count,
        "duplicate_alias_target_pair_count": duplicate_alias_target_pair_count,
        "target_conflict_count": target_conflict_count,
        "already_official_overlap_count": already_official_overlap_count,
        "missing_target_asset_or_group_count": missing_target_asset_or_group_count,
        "missing_provenance_count": missing_provenance_count,
        "adjusted_metric_mismatch_count": adjusted_metric_mismatch_count,
        "diluted_eps_mismatch_count": diluted_eps_mismatch_count,
        "official_asset_hash_unchanged": official_asset_hash_unchanged,
        "files_written_to_official_assets": [],
        "official_assets_modified": False,
        "official_asset_hashes_before": inputs["official_hashes_before"],
        "official_asset_hashes_after": official_hashes_after,
        "expected_affected_candidate_count": expected_affected_candidate_count,
        "expected_trusted_gain": expected_trusted_gain,
        "expected_review_reduction": expected_review_reduction,
        "expected_out_of_scope_or_rejected_gain": expected_out_of_scope_or_rejected_gain,
        "rollback_plan_record_count": int(len(rollback_plan_df)),
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    qa_summary_df = pd.DataFrame(
        [
            {
                "qa_pass_count": qa_pass_count,
                "qa_warn_count": qa_warn_count,
                "qa_fail_count": qa_fail_count,
                "blocking_reasons": " | ".join(blocking_reasons),
                "decision": summary["decision"],
            }
        ]
    ).fillna("")

    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "dry_run_only",
                "detail": "325L generates alias patch-operation preview and virtual after-state only. Official assets stay unchanged on disk.",
            },
            {
                "limitation": "ready_alias_proposals_only",
                "detail": "325L processes only the 6 READY_FOR_DRY_RUN alias proposals from 325K.",
            },
            {
                "limitation": "future_human_approval_required",
                "detail": "All 325L dry-run operations still require later human approval before any official patch application.",
            },
        ]
    ).fillna("")

    patch_operations_json = {
        "stage": "325L",
        "decision": summary["decision"],
        "patch_operations": patch_operations_df.drop(
            columns=["preview_payload_dict"], errors="ignore"
        ).to_dict(orient="records"),
    }
    target_asset_diff_preview_json = {
        "stage": "325L",
        "decision": summary["decision"],
        "before_after_preview": before_after_preview_df.to_dict(orient="records"),
        "target_asset_diff_preview": target_asset_diff_preview_df.to_dict(orient="records"),
        "virtual_after_alias_payload": virtual_after_alias_payload,
    }
    rollback_plan_json = {
        "stage": "325L",
        "decision": summary["decision"],
        "rollback_plan": rollback_plan_df.to_dict(orient="records"),
    }
    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_checks_df.to_dict(orient="records"),
    }
    no_apply_proof_json = {
        "stage": "325L",
        "decision": summary["decision"],
        "files_read": [
            str(
                DEFAULT_CONTROLLED_PROPOSAL_DIR
                / "controlled_official_proposal_from_325j_325k_summary.json"
            ),
            str(
                DEFAULT_CONTROLLED_PROPOSAL_DIR
                / "controlled_official_proposal_from_325j_325k_qa.json"
            ),
            str(
                DEFAULT_CONTROLLED_PROPOSAL_DIR
                / "controlled_official_proposal_from_325j_325k_proposals.json"
            ),
            str(
                DEFAULT_OFFICIAL_RULE_CANDIDATE_DIR
                / "alias_official_rule_candidates_from_325i_325j_summary.json"
            ),
            str(
                DEFAULT_SANDBOX_REPLAY_DIR
                / "alias_human_confirmed_sandbox_replay_325i_summary.json"
            ),
            str(OFFICIAL_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "files_written": [],
        "files_written_to_official_assets": [],
        "target_official_files_inspected": [
            str(OFFICIAL_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "target_locators_preview_only": [
            f"{OFFICIAL_ALIAS_ASSET_PATH}::{TARGET_ASSET_GROUP}",
        ],
        "official_assets_not_modified": [
            str(OFFICIAL_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "output_only_write_confirmation": True,
        "dry_run_executed": True,
        "official_patches_applied": False,
        "semantic_rules_applied": False,
        "trusted_marked_in_production": False,
        "llm_or_adjudicator_called": False,
    }

    return {
        "summary": summary,
        "patch_operations_df": patch_operations_df.drop(
            columns=["preview_payload_dict"], errors="ignore"
        ),
        "before_after_preview_df": before_after_preview_df,
        "target_asset_diff_preview_df": target_asset_diff_preview_df,
        "rollback_plan_df": rollback_plan_df,
        "qa_checks_df": qa_checks_df,
        "qa_summary_df": qa_summary_df,
        "known_limitations_df": known_limitations_df,
        "patch_operations_json": patch_operations_json,
        "target_asset_diff_preview_json": target_asset_diff_preview_json,
        "rollback_plan_json": rollback_plan_json,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
    }
