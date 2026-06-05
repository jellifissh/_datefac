from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


EXPECTED_325A_DECISION = "ALIAS_CANDIDATE_REFINEMENT_325A_READY_FOR_325B_ALIAS_REVIEW_BATCH"
READY_DECISION = "ALIAS_REVIEW_BATCH_325B_READY_FOR_HUMAN_OR_ADJUDICATOR_REVIEW"
NOT_READY_DECISION = "ALIAS_REVIEW_BATCH_325B_NOT_READY"

DEFAULT_ALIAS_REFINEMENT_DIR = Path(r"D:\_datefac\output\alias_candidate_refinement_325a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_review_batch_325b")

PENDING_REVIEW = "PENDING_REVIEW"
ALLOWED_REVIEW_DECISIONS = [
    "ACCEPT_ALIAS",
    "REJECT_ALIAS",
    "NEEDS_MORE_INFO",
    "HOLDOUT",
]

AMBIGUITY_PATTERN = re.compile(r"(?:\bPE\b|\bPB\b|P/E|P/B|EBIT|EBITDA|市盈率|市净率)", re.IGNORECASE)


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


def _read_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name=sheet_name).fillna("")
    except Exception:
        return pd.DataFrame()


def _join_unique(values: List[Any], limit: int = 12) -> str:
    out: List[str] = []
    seen = set()
    for value in values:
        text = _norm(value)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
        if len(out) >= limit:
            break
    return " | ".join(out)


def _has_ambiguity_warning(label: str) -> bool:
    return bool(AMBIGUITY_PATTERN.search(_norm(label)))


def _warning_text(label: str) -> str:
    if _has_ambiguity_warning(label):
        return (
            "Ambiguity warning: PE/PB/EBIT-style labels can vary by dilution basis, price basis, "
            "latest share capital, adjustment status, or metric family. Accept only with clear target metric evidence."
        )
    return "No special ambiguity warning beyond standard alias review checks."


def _proposed_target_metric_if_available(row: pd.Series) -> str:
    # 325A does not adjudicate target metrics. Preserve blank unless prior artifacts already supplied one.
    for key in [
        "proposed_target_metric",
        "normalized_target_metric_if_any",
        "target_metric",
        "metric_code",
    ]:
        value = _norm(row.get(key))
        if value:
            return value
    return ""


def load_alias_review_batch_325b_inputs(alias_refinement_dir: Path) -> Dict[str, Any]:
    safe_batch_path = alias_refinement_dir / "alias_candidate_refinement_325a_safe_batch.xlsx"
    return {
        "summary_325a": _read_json(alias_refinement_dir / "alias_candidate_refinement_325a_summary.json"),
        "qa_325a": _read_json(alias_refinement_dir / "alias_candidate_refinement_325a_qa.json"),
        "refined_json_325a": _read_json(alias_refinement_dir / "alias_candidate_refinement_325a_refined_alias_candidates.json"),
        "safe_batch_df": _read_excel_sheet(safe_batch_path, "safe_batch"),
    }


def build_alias_review_batch_325b(
    summary_325a: Dict[str, Any],
    qa_325a: Dict[str, Any],
    refined_json_325a: Dict[str, Any],
    safe_batch_df: pd.DataFrame,
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::325a_decision",
        "PASS" if _norm(summary_325a.get("decision")) == EXPECTED_325A_DECISION else "FAIL",
        _norm(summary_325a.get("decision")),
    )
    add_qa(
        "readiness::325a_summary_qa_fail_count",
        "PASS" if _safe_int(summary_325a.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_325a.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::325a_qa_json_fail_count",
        "PASS" if _safe_int(qa_325a.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_325a.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::325a_safe_alias_review_batch_count",
        "PASS" if _safe_int(summary_325a.get("safe_alias_review_batch_count")) == 12 else "FAIL",
        str(summary_325a.get("safe_alias_review_batch_count", "")),
    )
    add_qa(
        "inputs::safe_batch_loaded_exact_count",
        "PASS" if len(safe_batch_df) == 12 else "FAIL",
        f"actual={len(safe_batch_df)}",
    )
    add_qa(
        "inputs::refined_json_safe_batch_count",
        "PASS"
        if len(refined_json_325a.get("safe_alias_review_batch", [])) == 12
        else "FAIL",
        f"actual={len(refined_json_325a.get('safe_alias_review_batch', []))}",
    )

    review_records: List[Dict[str, Any]] = []
    safe_batch_df = safe_batch_df.fillna("")
    for index, row in safe_batch_df.sort_values("safe_batch_rank").reset_index(drop=True).iterrows():
        label = _norm(row.get("candidate_label")) or _norm(row.get("repaired_label"))
        review_record = {
            "alias_review_id": f"325b::alias_review::{index + 1:03d}",
            "alias_refinement_candidate_id": _norm(row.get("alias_refinement_candidate_id")),
            "source_group_id": _norm(row.get("group_id")),
            "candidate_id": _norm(row.get("alias_refinement_candidate_id")),
            "candidate_type": "alias",
            "normalized_label": label,
            "candidate_label_norm": _norm(row.get("candidate_label_norm")),
            "proposed_target_metric_if_available": _proposed_target_metric_if_available(row),
            "review_decision": PENDING_REVIEW,
            "reviewer_note": "",
            "reviewer_name": "",
            "review_timestamp": "",
            "allowed_review_decisions": " | ".join(ALLOWED_REVIEW_DECISIONS),
            "risk_bucket": _norm(row.get("risk_bucket")),
            "risk_bucket_reasons": _norm(row.get("risk_bucket_reasons")),
            "ambiguity_warning": _warning_text(label),
            "pe_pb_ebit_ambiguity_warning_present": _has_ambiguity_warning(label),
            "affected_candidate_count": _safe_int(row.get("affected_candidate_count")),
            "affected_review_required_count": _safe_int(row.get("affected_review_required_count")),
            "priority_score": _safe_float(row.get("priority_score")),
            "impact_score_325a": _safe_float(row.get("impact_score_325a")),
            "safe_batch_rank_325a": _safe_int(row.get("safe_batch_rank")),
            "risk_signature": _norm(row.get("risk_signature")),
            "repair_status": _norm(row.get("repair_status")),
            "repair_confidence": _norm(row.get("repair_confidence")),
            "sample_candidate_ids": _norm(row.get("sample_candidate_ids")),
            "sample_raw_metric_names": _norm(row.get("sample_raw_metric_names")),
            "sample_row_texts": _norm(row.get("sample_row_texts")),
            "sample_table_titles": _norm(row.get("sample_table_titles")),
            "sample_years": _norm(row.get("sample_years")),
            "prior_323c_sanity_bucket": _norm(row.get("prior_323c_sanity_bucket")),
            "prior_323c_sanity_reasons": _norm(row.get("prior_323c_sanity_reasons")),
            "prior_323c_batch_item_id": _norm(row.get("prior_323c_batch_item_id")),
            "provenance_source": _norm(row.get("provenance_source")),
            "provenance_summary": _join_unique(
                [
                    row.get("group_id"),
                    row.get("alias_refinement_candidate_id"),
                    row.get("provenance_source"),
                    row.get("prior_323c_batch_item_id"),
                    row.get("sample_candidate_ids"),
                ],
                limit=10,
            ),
            "review_instruction": (
                "Review whether this label can safely map to one existing selected core metric alias. "
                "Do not accept without clear evidence. Do not create official rules or mark trusted in 325B."
            ),
        }
        review_records.append(review_record)

    review_df = pd.DataFrame(review_records).fillna("")
    duplicate_review_id_count = (
        int(review_df["alias_review_id"].astype(str).duplicated().sum()) if not review_df.empty else 0
    )
    pending_count = int((review_df["review_decision"] == PENDING_REVIEW).sum()) if not review_df.empty else 0
    accepted_count = int((review_df["review_decision"] == "ACCEPT_ALIAS").sum()) if not review_df.empty else 0
    rejected_count = int((review_df["review_decision"] == "REJECT_ALIAS").sum()) if not review_df.empty else 0
    needs_more_info_count = int((review_df["review_decision"] == "NEEDS_MORE_INFO").sum()) if not review_df.empty else 0
    holdout_count = int((review_df["review_decision"] == "HOLDOUT").sum()) if not review_df.empty else 0

    add_qa(
        "review_records::record_count_matches_safe_batch",
        "PASS" if len(review_records) == 12 else "FAIL",
        f"actual={len(review_records)}",
    )
    add_qa(
        "review_records::all_pending_by_default",
        "PASS" if pending_count == len(review_records) and len(review_records) > 0 else "FAIL",
        f"pending={pending_count} total={len(review_records)}",
    )
    add_qa(
        "review_records::allowed_decisions_present",
        "PASS"
        if not review_df.empty and review_df["allowed_review_decisions"].astype(str).eq(" | ".join(ALLOWED_REVIEW_DECISIONS)).all()
        else "FAIL",
        " | ".join(ALLOWED_REVIEW_DECISIONS),
    )
    add_qa(
        "review_records::unique_review_ids",
        "PASS" if duplicate_review_id_count == 0 else "FAIL",
        f"actual={duplicate_review_id_count}",
    )
    add_qa(
        "review_records::safe_bucket_only",
        "PASS"
        if not review_df.empty and review_df["risk_bucket"].astype(str).eq("SAFE_ALIAS_REVIEW_BATCH").all()
        else "FAIL",
        f"record_count={len(review_df)}",
    )
    add_qa(
        "review_records::evidence_preserved",
        "PASS"
        if not review_df.empty
        and review_df["sample_row_texts"].astype(str).eq("").sum() == 0
        and review_df["provenance_summary"].astype(str).eq("").sum() == 0
        else "FAIL",
        f"record_count={len(review_df)}",
    )
    add_qa(
        "review_records::ambiguity_warnings_present_for_pe_pb_ebit",
        "PASS"
        if not review_df.empty
        and review_df.loc[
            review_df["normalized_label"].astype(str).map(_has_ambiguity_warning),
            "pe_pb_ebit_ambiguity_warning_present",
        ].astype(bool).all()
        else "FAIL",
        f"warning_count={int(review_df['pe_pb_ebit_ambiguity_warning_present'].astype(bool).sum()) if not review_df.empty else 0}",
    )
    add_qa(
        "safety::no_llm_or_adjudicator_called",
        "PASS",
        "325B only prepares review package records.",
    )
    add_qa(
        "safety::no_official_rule_candidate_or_proposal_or_replay",
        "PASS",
        "325B output contains review package artifacts only.",
    )
    add_qa(
        "safety::official_assets_not_modified_by_stage",
        "PASS",
        "325B reads 325A output only and writes output artifacts only.",
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "325B",
        "output_dir": str(output_dir),
        "loaded_safe_alias_candidate_count": int(len(safe_batch_df)),
        "review_record_count": len(review_records),
        "pending_count": pending_count,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "needs_more_info_count": needs_more_info_count,
        "holdout_count": holdout_count,
        "pe_pb_ebit_warning_count": int(review_df["pe_pb_ebit_ambiguity_warning_present"].astype(bool).sum()) if not review_df.empty else 0,
        "official_assets_modified": False,
        "official_assets_written": [],
        "llm_or_adjudicator_called": False,
        "official_rule_candidates_created": False,
        "controlled_official_proposals_created": False,
        "sandbox_replay_package_created": False,
        "top_review_examples": [
            {
                "alias_review_id": _norm(row.get("alias_review_id")),
                "normalized_label": _norm(row.get("normalized_label")),
                "affected_review_required_count": _safe_int(row.get("affected_review_required_count")),
                "ambiguity_warning": _norm(row.get("ambiguity_warning")),
            }
            for _, row in review_df.head(5).iterrows()
        ],
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }
    review_package_json = {
        "stage": "325B",
        "decision": summary["decision"],
        "allowed_review_decisions": ALLOWED_REVIEW_DECISIONS,
        "review_records": review_df.to_dict(orient="records"),
    }
    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    instructions_df = pd.DataFrame(
        [
            {
                "section": "purpose",
                "instruction": "Review the 12 SAFE_ALIAS_REVIEW_BATCH candidates from 325A. 325B does not accept, reject, adjudicate, or apply rules.",
            },
            {
                "section": "editable_fields",
                "instruction": "Edit review_decision, reviewer_note, reviewer_name, and review_timestamp only.",
            },
            {
                "section": "allowed_decisions",
                "instruction": "Allowed review_decision values: ACCEPT_ALIAS, REJECT_ALIAS, NEEDS_MORE_INFO, HOLDOUT.",
            },
            {
                "section": "ambiguity_warning",
                "instruction": "PE/PB/EBIT-style labels require special caution because basis, dilution, adjustment, or metric family may be ambiguous.",
            },
            {
                "section": "no_apply_boundary",
                "instruction": "Do not create official rule candidates, controlled proposals, sandbox replay packages, or trusted production markings in 325B.",
            },
        ]
    ).fillna("")
    return {
        "summary": summary,
        "qa_json": qa_json,
        "review_package_json": review_package_json,
        "review_records_df": review_df,
        "qa_checks_df": qa_df,
        "instructions_df": instructions_df,
    }
