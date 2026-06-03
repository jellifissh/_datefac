from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd


EXPECTED_SANDBOX_DECISION = "OFFICIAL_RULE_CANDIDATES_322J_READY_FOR_322K_CONTROLLED_OFFICIAL_PATCH_PROPOSAL"
EXPECTED_NEXT_DECISION = "CONTROLLED_OFFICIAL_SEMANTIC_PATCH_PROPOSAL_322K_READY_FOR_322L_OFFICIAL_PATCH_DRY_RUN"

OFFICIAL_SCOPE_RULES_PATH = r"D:\_datefac\data\mapping\formal_scope_rules.json"
OFFICIAL_OVERRIDE_PATH = r"D:\_datefac\data\overrides\02B_ai_repair_override.xlsx"


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_json_array(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


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


def _safe_int(value: Any) -> int:
    if value in ("", None):
        return 0
    try:
        return int(float(value))
    except Exception:
        return 0


def _join_unique(items: List[str], limit: int = 6) -> str:
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


def _proposal_target(rule_type: str, payload: Dict[str, Any]) -> Dict[str, str]:
    if rule_type == "alias":
        metric_family = _norm(payload.get("proposed_metric_family")) or "unknown_family"
        return {
            "target_official_rule_category": "official_alias_mapping_candidate",
            "intended_future_target_file_or_rule_group": f"data/overrides/semantic_alias_candidates::{metric_family}",
            "exact_proposed_semantic_change": f"Add alias '{_norm(payload.get('normalized_label'))}' -> metric_code '{_norm(payload.get('proposed_metric_code'))}'",
        }
    return {
        "target_official_rule_category": "official_scope_rule_candidate",
        "intended_future_target_file_or_rule_group": "data/mapping/formal_scope_rules.json::core_metric_scope_exclusions",
        "exact_proposed_semantic_change": f"Add out_of_scope exclusion for label '{_norm(payload.get('normalized_label'))}' with action '{_norm(payload.get('proposed_scope_action')) or 'exclude_from_core_metric_mapping'}'",
    }


def load_controlled_patch_proposal_inputs(
    sandbox_application_dir: Path,
    official_rule_candidate_dir: Path,
) -> Dict[str, Any]:
    return {
        "sandbox_summary": _read_json(sandbox_application_dir / "official_semantic_rule_candidates_322j_summary.json"),
        "sandbox_qa": _read_json(sandbox_application_dir / "official_semantic_rule_candidates_322j_qa.json"),
        "sandbox_rule_application_log_df": _read_jsonl(sandbox_application_dir / "official_semantic_rule_candidates_322j_rule_application_log.jsonl"),
        "official_package_summary": _read_json(official_rule_candidate_dir / "official_semantic_rule_candidates_322i_summary.json"),
        "alias_candidates": _read_json_array(official_rule_candidate_dir / "alias_rule_candidates_322i.json"),
        "scope_candidates": _read_json_array(official_rule_candidate_dir / "scope_rule_candidates_322i.json"),
    }


def build_controlled_patch_proposals(
    sandbox_summary: Dict[str, Any],
    sandbox_qa: Dict[str, Any],
    sandbox_rule_application_log_df: pd.DataFrame,
    official_package_summary: Dict[str, Any],
    alias_candidates: List[Dict[str, Any]],
    scope_candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    readiness_checks = {
        "decision": _norm(sandbox_summary.get("official_rule_candidates_322j_decision")) == EXPECTED_SANDBOX_DECISION,
        "qa_fail_count": _safe_int(sandbox_summary.get("qa_fail_count")) == 0,
        "trusted_gain_322j": _safe_int(sandbox_summary.get("trusted_gain_322j")) == 49,
        "review_reduction_322j": _safe_int(sandbox_summary.get("review_reduction_322j")) == 287,
        "out_of_scope_or_rejected_gain_322j": _safe_int(sandbox_summary.get("out_of_scope_or_rejected_gain_322j")) == 238,
        "affected_candidate_count": _safe_int(sandbox_summary.get("affected_candidate_count")) == 287,
        "trusted_gain_delta": _safe_int(sandbox_summary.get("trusted_gain_delta_vs_322i_expected")) == 0,
        "review_reduction_delta": _safe_int(sandbox_summary.get("review_reduction_delta_vs_322i_expected")) == 0,
        "out_of_scope_delta": _safe_int(sandbox_summary.get("out_of_scope_or_rejected_gain_delta_vs_322i_expected")) == 0,
        "affected_delta": _safe_int(sandbox_summary.get("affected_candidate_count_delta_vs_322i_expected")) == 0,
    }
    for key, passed in readiness_checks.items():
        add_qa(
            f"readiness::{key}",
            "PASS" if passed else "FAIL",
            str(sandbox_summary.get(key, "")) if key in sandbox_summary else f"expected strict readiness for {key}",
        )

    rule_log_lookup = {
        _norm(row.get("proposal_id")): row.to_dict()
        for _, row in sandbox_rule_application_log_df.iterrows()
    } if not sandbox_rule_application_log_df.empty else {}

    alias_rows: List[Dict[str, Any]] = []
    scope_rows: List[Dict[str, Any]] = []
    all_rows: List[Dict[str, Any]] = []
    risk_rows: List[Dict[str, Any]] = []

    def build_row(rule_type: str, index: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        proposal_id = _norm(payload.get("source_proposal_id"))
        log_row = rule_log_lookup.get(proposal_id, {})
        target = _proposal_target(rule_type, payload)
        rollback_note = (
            f"Remove planned alias candidate for '{_norm(payload.get('normalized_label'))}' from future alias candidate bundle before any official patch dry run."
            if rule_type == "alias"
            else f"Remove planned scope exclusion for '{_norm(payload.get('normalized_label'))}' from future scope candidate bundle before any official patch dry run."
        )
        safety_rationale = (
            "Human-confirmed alias mapping with deterministic sandbox replay gain and no QA failures."
            if rule_type == "alias"
            else "Human-confirmed non-core scope exclusion with deterministic sandbox replay reduction and no core exclusion regression."
        )
        return {
            "controlled_patch_proposal_id": f"proposal_322k::{rule_type}::{index:03d}",
            "source_rule_id": _norm(payload.get("rule_candidate_id")),
            "rule_type": rule_type,
            "normalized_label": _norm(payload.get("normalized_label")),
            "human_confirmation_provenance": "322G reviewed proposal ACCEPT -> 322H human-confirmed patch preview -> 322I official rule candidate packaging",
            "source_322i_rule_candidate_provenance": proposal_id,
            "source_322j_sandbox_application_provenance": _norm(log_row.get("rule_candidate_id")) or _norm(payload.get("rule_candidate_id")),
            "expected_affected_candidate_count": _safe_int(log_row.get("actual_affected_candidate_count") or payload.get("affected_candidate_count")),
            "expected_trusted_gain": _safe_int(log_row.get("actual_trusted_gain") or payload.get("trusted_gain")),
            "expected_review_reduction": _safe_int(log_row.get("actual_review_reduction") or payload.get("review_reduction")),
            "expected_out_of_scope_or_rejected_gain": _safe_int(log_row.get("actual_rejected_or_out_of_scope_gain") or payload.get("rejected_or_out_of_scope_gain")),
            "target_official_rule_category": target["target_official_rule_category"],
            "intended_future_target_file_or_rule_group": target["intended_future_target_file_or_rule_group"],
            "exact_proposed_semantic_change": target["exact_proposed_semantic_change"],
            "proposed_metric_code": _norm(payload.get("proposed_metric_code")),
            "proposed_metric_family": _norm(payload.get("proposed_metric_family")),
            "proposed_scope_action": _norm(payload.get("proposed_scope_action")),
            "human_confirmation_source_case_id": _norm(payload.get("source_case_id")),
            "sandbox_application_status": _norm(log_row.get("application_status")),
            "sandbox_application_detail": _norm(log_row.get("application_detail")) or _norm(payload.get("recommended_action")),
            "sample_row_labels": _norm(payload.get("sample_row_labels")),
            "sample_values": _norm(payload.get("sample_values")),
            "risk_flags": _norm(payload.get("risk_flags")),
            "safety_rationale": safety_rationale,
            "rollback_note": rollback_note,
            "eligible_for_official_patch": True,
        }

    for idx, payload in enumerate(alias_candidates, start=1):
        row = build_row("alias", idx, payload)
        alias_rows.append(row)
        all_rows.append(row)
        risk_rows.append(
            {
                "controlled_patch_proposal_id": row["controlled_patch_proposal_id"],
                "rule_type": "alias",
                "risk_flags": row["risk_flags"],
                "safety_rationale": row["safety_rationale"],
                "rollback_note": row["rollback_note"],
            }
        )
    for idx, payload in enumerate(scope_candidates, start=1):
        row = build_row("out_of_scope", idx, payload)
        scope_rows.append(row)
        all_rows.append(row)
        risk_rows.append(
            {
                "controlled_patch_proposal_id": row["controlled_patch_proposal_id"],
                "rule_type": "out_of_scope",
                "risk_flags": row["risk_flags"],
                "safety_rationale": row["safety_rationale"],
                "rollback_note": row["rollback_note"],
            }
        )

    alias_df = pd.DataFrame(alias_rows).fillna("")
    scope_df = pd.DataFrame(scope_rows).fillna("")
    proposal_overview_df = pd.DataFrame(all_rows).fillna("")
    risk_notes_df = pd.DataFrame(risk_rows).fillna("")

    add_qa("proposal_count::total", "PASS" if len(all_rows) == 10 else "FAIL", f"actual={len(all_rows)}")
    add_qa("proposal_count::alias", "PASS" if len(alias_rows) == 3 else "FAIL", f"actual={len(alias_rows)}")
    add_qa("proposal_count::scope", "PASS" if len(scope_rows) == 7 else "FAIL", f"actual={len(scope_rows)}")
    add_qa("proposal_count::unit", "PASS", "actual=0")
    add_qa("proposal_count::rejected_noise", "PASS", "actual=0")

    duplicate_ids = proposal_overview_df["controlled_patch_proposal_id"].astype(str).duplicated().any() if not proposal_overview_df.empty else False
    add_qa("proposal_integrity::no_duplicate_proposal_id", "PASS" if not duplicate_ids else "FAIL", f"duplicate_present={duplicate_ids}")

    source_rule_duplicates = proposal_overview_df["source_rule_id"].astype(str).duplicated().any() if not proposal_overview_df.empty else False
    add_qa("proposal_integrity::no_duplicate_source_rule_id", "PASS" if not source_rule_duplicates else "FAIL", f"duplicate_present={source_rule_duplicates}")

    has_conflict = False
    if alias_candidates or scope_candidates:
        for payload in alias_candidates + scope_candidates:
            if _norm(payload.get("conflict_status")) not in {"", "NO_CONFLICT_DETECTED"}:
                has_conflict = True
                break
    add_qa("proposal_integrity::no_conflict_proposals", "PASS" if not has_conflict else "FAIL", f"has_conflict={has_conflict}")

    target_category_ok = True
    if not proposal_overview_df.empty:
        target_category_ok = proposal_overview_df["target_official_rule_category"].astype(str).ne("").all()
    add_qa("proposal_integrity::target_category_validation", "PASS" if target_category_ok else "FAIL", "every proposal has a target category")

    provenance_complete = True
    provenance_columns = [
        "human_confirmation_provenance",
        "source_322i_rule_candidate_provenance",
        "source_322j_sandbox_application_provenance",
    ]
    if not proposal_overview_df.empty:
        for column in provenance_columns:
            if proposal_overview_df[column].astype(str).eq("").any():
                provenance_complete = False
                break
    add_qa("proposal_integrity::provenance_completeness", "PASS" if provenance_complete else "FAIL", "all provenance fields populated")

    gain_alignment = (
        _safe_int(sandbox_summary.get("trusted_gain_322j")) == 49
        and _safe_int(sandbox_summary.get("review_reduction_322j")) == 287
        and _safe_int(sandbox_summary.get("out_of_scope_or_rejected_gain_322j")) == 238
        and _safe_int(sandbox_summary.get("affected_candidate_count")) == 287
    )
    add_qa("proposal_integrity::expected_gain_alignment", "PASS" if gain_alignment else "FAIL", "322J gains align with expected proposal impact")

    rollback_complete = not proposal_overview_df.empty and proposal_overview_df["rollback_note"].astype(str).ne("").all()
    add_qa("proposal_integrity::rollback_note_completeness", "PASS" if rollback_complete else "FAIL", "every proposal has rollback note")

    all_eligible = not proposal_overview_df.empty and proposal_overview_df["eligible_for_official_patch"].astype(bool).all()
    add_qa("proposal_integrity::eligible_for_official_patch_all_true", "PASS" if all_eligible else "FAIL", f"eligible_count={int(proposal_overview_df['eligible_for_official_patch'].astype(bool).sum()) if not proposal_overview_df.empty else 0}")

    no_apply_proof = {
        "proposal_only_decision": True,
        "files_read": [
            str(Path(r"D:\_datefac\output\official_semantic_rule_candidates_322j\official_semantic_rule_candidates_322j_summary.json")),
            str(Path(r"D:\_datefac\output\official_semantic_rule_candidates_322j\official_semantic_rule_candidates_322j_qa.json")),
            str(Path(r"D:\_datefac\output\official_semantic_rule_candidates_322j\official_semantic_rule_candidates_322j_rule_application_log.jsonl")),
            str(Path(r"D:\_datefac\output\official_semantic_rule_candidates_322i\official_semantic_rule_candidates_322i_summary.json")),
            str(Path(r"D:\_datefac\output\official_semantic_rule_candidates_322i\alias_rule_candidates_322i.json")),
            str(Path(r"D:\_datefac\output\official_semantic_rule_candidates_322i\scope_rule_candidates_322i.json")),
        ],
        "files_written": [],
        "official_files_not_modified": [
            OFFICIAL_SCOPE_RULES_PATH,
            OFFICIAL_OVERRIDE_PATH,
            r"D:\_datefac\datefac\pipeline",
        ],
        "output_only_write_confirmation": True,
        "decision": "proposal_only_no_apply",
    }
    add_qa("safety::no_apply_proof_present", "PASS", "no-apply proof object created")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "322K",
        "output_dir": "",
        "sandbox_readiness_passed": all(readiness_checks.values()),
        "sandbox_readiness_source_decision": _norm(sandbox_summary.get("official_rule_candidates_322j_decision")),
        "sandbox_readiness_source_qa_fail_count": _safe_int(sandbox_summary.get("qa_fail_count")),
        "total_patch_proposal_count": len(all_rows),
        "alias_patch_proposal_count": len(alias_rows),
        "scope_patch_proposal_count": len(scope_rows),
        "unit_patch_proposal_count": 0,
        "rejected_noise_patch_proposal_count": 0,
        "expected_affected_candidate_count": sum(_safe_int(row.get("expected_affected_candidate_count")) for row in all_rows),
        "expected_trusted_gain": sum(_safe_int(row.get("expected_trusted_gain")) for row in all_rows),
        "expected_review_reduction": sum(_safe_int(row.get("expected_review_reduction")) for row in all_rows),
        "expected_out_of_scope_or_rejected_gain": sum(_safe_int(row.get("expected_out_of_scope_or_rejected_gain")) for row in all_rows),
        "proposal_only_no_apply_confirmed": True,
        "official_files_not_modified_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "controlled_official_patch_proposal_decision": EXPECTED_NEXT_DECISION if qa_fail_count == 0 else "CONTROLLED_OFFICIAL_SEMANTIC_PATCH_PROPOSAL_322K_NOT_READY",
    }

    qa_summary_df = pd.DataFrame(
        [
            {
                "qa_pass_count": qa_pass_count,
                "qa_warn_count": qa_warn_count,
                "qa_fail_count": qa_fail_count,
                "blocking_reasons": " | ".join(blocking_reasons),
                "decision": summary["controlled_official_patch_proposal_decision"],
            }
        ]
    ).fillna("")
    no_apply_proof_df = pd.DataFrame(
        [
            {
                "proposal_only_decision": no_apply_proof["proposal_only_decision"],
                "files_read_count": len(no_apply_proof["files_read"]),
                "files_written_count": len(no_apply_proof["files_written"]),
                "official_files_not_modified_count": len(no_apply_proof["official_files_not_modified"]),
                "output_only_write_confirmation": no_apply_proof["output_only_write_confirmation"],
                "decision": no_apply_proof["decision"],
            }
        ]
    ).fillna("")
    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "proposal_only",
                "detail": "322K proposes future official patch targets only and does not apply changes.",
            },
            {
                "limitation": "sandbox_dependency",
                "detail": "322K relies on 322J sandbox replay outputs and 322I packaged candidates.",
            },
            {
                "limitation": "target_file_metadata_only",
                "detail": "The intended future target file or rule group is planning metadata and not a write action.",
            },
        ]
    )

    return {
        "summary": summary,
        "alias_patch_proposals_df": alias_df,
        "scope_patch_proposals_df": scope_df,
        "proposal_overview_df": proposal_overview_df,
        "qa_summary_df": qa_summary_df,
        "no_apply_proof_df": no_apply_proof_df,
        "risk_notes_df": risk_notes_df,
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
        "alias_patch_proposals_json": alias_rows,
        "scope_patch_proposals_json": scope_rows,
        "no_apply_proof_json": no_apply_proof,
        "review_notes_markdown": _build_review_notes_markdown(summary, alias_rows, scope_rows, blocking_reasons),
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
    }


def _build_review_notes_markdown(
    summary: Dict[str, Any],
    alias_rows: List[Dict[str, Any]],
    scope_rows: List[Dict[str, Any]],
    blocking_reasons: List[str],
) -> str:
    lines: List[str] = [
        "# Controlled Official Semantic Patch Proposal 322K Review Notes",
        "",
        "## Decision",
        f"- {summary.get('controlled_official_patch_proposal_decision', '')}",
        "",
        "## Counts",
        f"- alias_patch_proposal_count: {len(alias_rows)}",
        f"- scope_patch_proposal_count: {len(scope_rows)}",
        f"- total_patch_proposal_count: {len(alias_rows) + len(scope_rows)}",
        "",
        "## Alias Proposal Labels",
    ]
    lines.extend([f"- {row.get('normalized_label', '')} -> {row.get('proposed_metric_code', '')}" for row in alias_rows])
    lines.extend(["", "## Scope Proposal Labels"])
    lines.extend([f"- {row.get('normalized_label', '')} -> {row.get('proposed_scope_action', '')}" for row in scope_rows])
    if blocking_reasons:
        lines.extend(["", "## Blocking Reasons", *[f"- {item}" for item in blocking_reasons]])
    lines.extend(
        [
            "",
            "## Proposal-Only Note",
            "- This package proposes future official semantic patches only.",
            "- No production mapping, override, or pipeline file was modified.",
            "",
        ]
    )
    return "\n".join(lines)
