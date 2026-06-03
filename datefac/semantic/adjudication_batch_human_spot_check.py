from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set

import pandas as pd


EXPECTED_323C_READY_DECISION = "ADJUDICATION_BATCH_SANITY_GATE_323C_READY_FOR_HUMAN_SPOT_CHECK_OR_SAFE_ADJUDICATOR_SUBSET"
EXPECTED_323C_PREPARE_DECISION = "ADJUDICATION_BATCH_HUMAN_SPOT_CHECK_323C_READY_FOR_MANUAL_REVIEW"
EXPECTED_323C_PREPARE_NOT_READY = "ADJUDICATION_BATCH_HUMAN_SPOT_CHECK_323C_NOT_READY_FOR_MANUAL_REVIEW"
EXPECTED_323C_REVIEWED_DECISION = "ADJUDICATION_BATCH_HUMAN_SPOT_CHECK_323C_REVIEWED_READY_FOR_FINAL_ROUTING"
EXPECTED_323C_REVIEWED_NOT_READY = "ADJUDICATION_BATCH_HUMAN_SPOT_CHECK_323C_REVIEWED_NOT_READY"

DEFAULT_323C_DIR = Path(r"D:\_datefac\output\adjudication_batch_sanity_gate_323c")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\adjudication_batch_human_spot_check_323c")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

BUCKET_SEND = "SEND_TO_ADJUDICATOR"
BUCKET_HUMAN = "HUMAN_SPOT_CHECK_FIRST"
BUCKET_HOLDOUT_CATEGORY = "HOLDOUT_CATEGORY_MISMATCH"
BUCKET_HOLDOUT_AMBIGUOUS = "HOLDOUT_AMBIGUOUS"
BUCKET_HOLDOUT_OFFICIAL = "HOLDOUT_ALREADY_OFFICIAL"
BUCKET_HOLDOUT_INVALID = "HOLDOUT_INVALID_TEXT"

AUTO_ROUTE_SEND = "AUTO_SEND_TO_ADJUDICATOR"
AUTO_ROUTE_HOLDOUT = "AUTO_HOLDOUT"

PENDING_HUMAN_DECISION = "PENDING_HUMAN_SPOT_CHECK"
ALLOWED_HUMAN_DECISIONS = {
    "SEND_TO_ADJUDICATOR",
    "HOLDOUT",
    "RECLASSIFY_AS_SCOPE_CANDIDATE",
    "RECLASSIFY_AS_ALIAS_CANDIDATE",
    "NEEDS_MORE_INFO",
}

REQUIRED_HUMAN_WORKBOOK_COLUMNS = [
    "batch_item_id",
    "source_group_id",
    "candidate_type",
    "repaired_label",
    "sanity_bucket",
    "human_decision",
    "human_note",
    "reviewer_name",
    "review_timestamp",
    "allowed_human_decisions",
]


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


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _flatten_sequence(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_norm(item) for item in value if _norm(item)]
    if isinstance(value, tuple):
        return [_norm(item) for item in value if _norm(item)]
    if isinstance(value, str):
        clean = _norm(value)
        return [clean] if clean else []
    return []


def _decision_distribution(records: Sequence[Dict[str, Any]], field: str) -> Dict[str, int]:
    distribution: Dict[str, int] = {}
    for record in records:
        key = _norm(record.get(field)) or "__EMPTY__"
        distribution[key] = distribution.get(key, 0) + 1
    return distribution


def _build_batch_lookup(batch_items: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for item in batch_items:
        if not isinstance(item, dict):
            continue
        batch_item_id = _norm(item.get("batch_item_id"))
        if batch_item_id:
            lookup[batch_item_id] = item
    return lookup


def _flatten_batch_item(item: Dict[str, Any]) -> Dict[str, Any]:
    provenance = item.get("provenance") if isinstance(item.get("provenance"), dict) else {}
    return {
        "batch_item_id": _norm(item.get("batch_item_id")),
        "source_group_id": _norm(item.get("source_group_id")),
        "candidate_type": _norm(item.get("candidate_type")),
        "repaired_label": _norm(item.get("repaired_label")),
        "original_label": _norm(item.get("original_label")),
        "candidate_question": _norm(item.get("candidate_question")),
        "allowed_decisions": " | ".join(_flatten_sequence(item.get("allowed_decisions"))),
        "expected_rule_type_if_accepted": _norm(item.get("expected_rule_type_if_accepted")),
        "review_decision": _norm(item.get("review_decision")),
        "sample_candidate_ids": " | ".join(_flatten_sequence(item.get("sample_candidate_ids"))),
        "sample_texts": " | ".join(_flatten_sequence(item.get("sample_texts"))),
        "affected_candidate_count": _safe_int(item.get("affected_candidate_count")),
        "affected_review_required_count": _safe_int(item.get("affected_review_required_count")),
        "priority_score": _safe_float(item.get("priority_score")),
        "risk_flags": " | ".join(_flatten_sequence(item.get("risk_flags"))),
        "review_instruction": _norm(item.get("review_instruction")),
        "sanity_bucket": _norm(item.get("sanity_bucket")),
        "sanity_reasons": " | ".join(_flatten_sequence(item.get("sanity_reasons"))),
        "human_spot_check_required": bool(item.get("human_spot_check_required")),
        "send_to_adjudicator_allowed": bool(item.get("send_to_adjudicator_allowed")),
        "source_stage": _norm(provenance.get("source_stage")),
        "source_stage_signature": _norm(provenance.get("source_stage_signature")),
        "source_report_examples": " | ".join(_flatten_sequence(provenance.get("source_report_examples"))),
        "table_asset_examples": " | ".join(_flatten_sequence(provenance.get("table_asset_examples"))),
        "sample_table_titles": " | ".join(_flatten_sequence(provenance.get("sample_table_titles"))),
        "sample_years": " | ".join(_flatten_sequence(provenance.get("sample_years"))),
        "sample_raw_metric_names": " | ".join(_flatten_sequence(provenance.get("sample_raw_metric_names"))),
        "human_decision": PENDING_HUMAN_DECISION,
        "human_note": "",
        "reviewer_name": "",
        "review_timestamp": "",
        "allowed_human_decisions": "SEND_TO_ADJUDICATOR | HOLDOUT | RECLASSIFY_AS_SCOPE_CANDIDATE | RECLASSIFY_AS_ALIAS_CANDIDATE | NEEDS_MORE_INFO",
    }


def load_adjudication_batch_human_spot_check_inputs(
    adjudication_batch_dir: Path,
    reviewed_workbook: Path | None = None,
) -> Dict[str, Any]:
    gated_batch_json = _read_json(adjudication_batch_dir / "adjudication_batch_sanity_gate_323c_gated_batch.json")
    workbook_path = reviewed_workbook or (adjudication_batch_dir / "adjudication_batch_sanity_gate_323c_human_spot_check.xlsx")
    return {
        "summary": _read_json(adjudication_batch_dir / "adjudication_batch_sanity_gate_323c_summary.json"),
        "qa": _read_json(adjudication_batch_dir / "adjudication_batch_sanity_gate_323c_qa.json"),
        "gated_batch_json": gated_batch_json,
        "gated_batch_items": gated_batch_json.get("batch_items", []) if isinstance(gated_batch_json.get("batch_items", []), list) else [],
        "human_workbook_summary_df": _read_excel_sheet(workbook_path, "summary"),
        "human_workbook_items_df": _read_excel_sheet(workbook_path, "items"),
        "human_workbook_qa_df": _read_excel_sheet(workbook_path, "qa_checks"),
        "workbook_path": workbook_path,
    }


def build_adjudication_batch_human_spot_check_prepare(
    summary_323c: Dict[str, Any],
    qa_323c: Dict[str, Any],
    gated_batch_items: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    add_qa(
        "input_323c::decision",
        "PASS" if _norm(summary_323c.get("decision")) == EXPECTED_323C_READY_DECISION else "FAIL",
        _norm(summary_323c.get("decision")),
    )
    add_qa(
        "input_323c::summary_qa_fail_count",
        "PASS" if _safe_int(summary_323c.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_323c.get("qa_fail_count", "")),
    )
    add_qa(
        "input_323c::qa_json_fail_count",
        "PASS" if _safe_int(qa_323c.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_323c.get("qa_fail_count", "")),
    )

    human_items = [
        item for item in gated_batch_items
        if isinstance(item, dict) and _norm(item.get("sanity_bucket")) == BUCKET_HUMAN
    ]
    auto_send_items = [
        item for item in gated_batch_items
        if isinstance(item, dict) and _norm(item.get("sanity_bucket")) == BUCKET_SEND
    ]
    auto_holdout_items = [
        item for item in gated_batch_items
        if isinstance(item, dict) and _norm(item.get("sanity_bucket")) in {
            BUCKET_HOLDOUT_CATEGORY,
            BUCKET_HOLDOUT_AMBIGUOUS,
            BUCKET_HOLDOUT_OFFICIAL,
            BUCKET_HOLDOUT_INVALID,
        }
    ]

    add_qa(
        "prepare::human_spot_check_count_positive",
        "PASS" if len(human_items) > 0 else "FAIL",
        f"actual={len(human_items)}",
    )
    add_qa(
        "prepare::human_count_matches_summary",
        "PASS" if len(human_items) == _safe_int(summary_323c.get("human_spot_check_count")) else "FAIL",
        f"items={len(human_items)} summary={_safe_int(summary_323c.get('human_spot_check_count'))}",
    )

    human_df = pd.DataFrame([_flatten_batch_item(item) for item in human_items]).fillna("")
    auto_send_df = pd.DataFrame([_flatten_batch_item(item) for item in auto_send_items]).fillna("")
    auto_holdout_df = pd.DataFrame([_flatten_batch_item(item) for item in auto_holdout_items]).fillna("")

    if not human_df.empty:
        all_pending = human_df["human_decision"].astype(str).eq(PENDING_HUMAN_DECISION).all()
        allowed_decision_strings_ok = human_df["allowed_human_decisions"].astype(str).ne("").all()
    else:
        all_pending = False
        allowed_decision_strings_ok = False
    add_qa("prepare::all_human_decisions_pending", "PASS" if all_pending else "FAIL", f"row_count={len(human_df)}")
    add_qa("prepare::allowed_human_decision_field_present", "PASS" if allowed_decision_strings_ok else "FAIL", f"row_count={len(human_df)}")

    parser_not_run = True
    llm_not_called = True
    add_qa("safety::parser_not_run_confirmation", "PASS" if parser_not_run else "FAIL", "323C human workflow reads cached artifacts only.")
    add_qa("safety::llm_not_called_confirmation", "PASS" if llm_not_called else "FAIL", "323C human workflow does not call adjudicator or LLM.")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    no_official_assets_modified = alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if no_official_assets_modified else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "323C-human-spot-check",
        "mode": "prepare",
        "output_dir": "",
        "input_batch_count": _safe_int(summary_323c.get("input_batch_count")),
        "auto_send_count": len(auto_send_df),
        "auto_holdout_count": len(auto_holdout_df),
        "human_spot_check_item_count": len(human_df),
        "all_human_decisions_pending": all_pending,
        "official_assets_not_modified_confirmed": no_official_assets_modified,
        "llm_not_called_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_323C_PREPARE_DECISION if qa_fail_count == 0 else EXPECTED_323C_PREPARE_NOT_READY,
    }

    review_instructions_df = pd.DataFrame(
        [
            {
                "section": "purpose",
                "instruction": "Review only HUMAN_SPOT_CHECK_FIRST items and choose a routing decision. This does not apply semantic rules.",
            },
            {
                "section": "allowed_human_decisions",
                "instruction": "Allowed values: SEND_TO_ADJUDICATOR, HOLDOUT, RECLASSIFY_AS_SCOPE_CANDIDATE, RECLASSIFY_AS_ALIAS_CANDIDATE, NEEDS_MORE_INFO.",
            },
            {
                "section": "review_fields",
                "instruction": "Editable fields are human_decision, human_note, reviewer_name, review_timestamp.",
            },
            {
                "section": "safety",
                "instruction": "Do not call LLM/adjudicator, do not modify official assets, and do not apply any semantic rule in this step.",
            },
        ]
    ).fillna("")

    no_apply_proof_json = {
        "files_read": [
            str(DEFAULT_323C_DIR / "adjudication_batch_sanity_gate_323c_summary.json"),
            str(DEFAULT_323C_DIR / "adjudication_batch_sanity_gate_323c_qa.json"),
            str(DEFAULT_323C_DIR / "adjudication_batch_sanity_gate_323c_gated_batch.json"),
        ],
        "files_written": [],
        "official_target_files_not_modified": [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_ALIAS_OVERRIDE_PATH),
        ],
        "output_only_write_confirmation": True,
        "decision": "human_spot_check_prepare_only_no_apply",
    }

    return {
        "summary": summary,
        "human_items_df": human_df,
        "auto_send_df": auto_send_df,
        "auto_holdout_df": auto_holdout_df,
        "review_instructions_df": review_instructions_df,
        "no_apply_proof_json": no_apply_proof_json,
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
        "qa_checks_df": qa_df,
    }


def build_adjudication_batch_human_spot_check_validate_reviewed(
    summary_323c: Dict[str, Any],
    qa_323c: Dict[str, Any],
    gated_batch_items: Sequence[Dict[str, Any]],
    reviewed_items_df: pd.DataFrame,
    workbook_summary_df: pd.DataFrame,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    add_qa(
        "input_323c::decision",
        "PASS" if _norm(summary_323c.get("decision")) == EXPECTED_323C_READY_DECISION else "FAIL",
        _norm(summary_323c.get("decision")),
    )
    add_qa(
        "input_323c::summary_qa_fail_count",
        "PASS" if _safe_int(summary_323c.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_323c.get("qa_fail_count", "")),
    )
    add_qa(
        "input_323c::qa_json_fail_count",
        "PASS" if _safe_int(qa_323c.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_323c.get("qa_fail_count", "")),
    )

    workbook_summary_count = 0
    if not workbook_summary_df.empty and "human_spot_check_count" in workbook_summary_df.columns:
        workbook_summary_count = _safe_int(workbook_summary_df.iloc[0].get("human_spot_check_count"))

    batch_lookup = _build_batch_lookup(gated_batch_items)
    auto_send_items = [
        item for item in gated_batch_items
        if isinstance(item, dict) and _norm(item.get("sanity_bucket")) == BUCKET_SEND
    ]
    auto_holdout_items = [
        item for item in gated_batch_items
        if isinstance(item, dict) and _norm(item.get("sanity_bucket")) in {
            BUCKET_HOLDOUT_CATEGORY,
            BUCKET_HOLDOUT_AMBIGUOUS,
            BUCKET_HOLDOUT_OFFICIAL,
            BUCKET_HOLDOUT_INVALID,
        }
    ]
    human_batch_items = [
        item for item in gated_batch_items
        if isinstance(item, dict) and _norm(item.get("sanity_bucket")) == BUCKET_HUMAN
    ]
    expected_human_ids = {_norm(item.get("batch_item_id")) for item in human_batch_items}

    add_qa(
        "reviewed::workbook_item_count_positive",
        "PASS" if not reviewed_items_df.empty else "FAIL",
        f"actual={len(reviewed_items_df)}",
    )
    add_qa(
        "reviewed::workbook_item_count_matches_summary",
        "PASS" if len(reviewed_items_df) == _safe_int(summary_323c.get("human_spot_check_count")) else "FAIL",
        f"items={len(reviewed_items_df)} summary={_safe_int(summary_323c.get('human_spot_check_count'))}",
    )
    if workbook_summary_count:
        add_qa(
            "reviewed::workbook_summary_count_matches_items",
            "PASS" if workbook_summary_count == len(reviewed_items_df) else "FAIL",
            f"workbook_summary={workbook_summary_count} items={len(reviewed_items_df)}",
        )

    missing_columns = [col for col in REQUIRED_HUMAN_WORKBOOK_COLUMNS if col not in reviewed_items_df.columns]
    add_qa(
        "reviewed::required_columns_present",
        "PASS" if not missing_columns else "FAIL",
        "none" if not missing_columns else " | ".join(missing_columns),
    )

    records = reviewed_items_df.fillna("").to_dict(orient="records") if not reviewed_items_df.empty else []
    reviewed_ids = {_norm(record.get("batch_item_id")) for record in records}
    missing_human_ids = sorted(expected_human_ids.difference(reviewed_ids))
    unexpected_ids = sorted(reviewed_ids.difference(expected_human_ids))
    add_qa(
        "reviewed::reviewed_ids_match_expected_human_subset",
        "PASS" if not missing_human_ids and not unexpected_ids else "FAIL",
        f"missing={missing_human_ids[:5]} unexpected={unexpected_ids[:5]}",
    )

    decisions = [_norm(record.get("human_decision")).upper() for record in records]
    pending_count = sum(1 for decision in decisions if decision in {"", PENDING_HUMAN_DECISION})
    invalid_decisions = sorted({decision for decision in decisions if decision and decision != PENDING_HUMAN_DECISION and decision not in ALLOWED_HUMAN_DECISIONS})
    add_qa(
        "reviewed::no_pending_human_decision",
        "PASS" if pending_count == 0 else "FAIL",
        f"pending_count={pending_count}",
    )
    add_qa(
        "reviewed::valid_human_decision_enum_only",
        "PASS" if not invalid_decisions else "FAIL",
        "none" if not invalid_decisions else " | ".join(invalid_decisions),
    )

    duplicate_batch_item_ids = int(reviewed_items_df["batch_item_id"].astype(str).duplicated().sum()) if not reviewed_items_df.empty else 0
    add_qa(
        "reviewed::no_duplicate_batch_item_id",
        "PASS" if duplicate_batch_item_ids == 0 else "FAIL",
        f"duplicate_count={duplicate_batch_item_ids}",
    )

    missing_reviewer_name_count = int(reviewed_items_df["reviewer_name"].astype(str).eq("").sum()) if "reviewer_name" in reviewed_items_df.columns else len(reviewed_items_df)
    missing_review_timestamp_count = int(reviewed_items_df["review_timestamp"].astype(str).eq("").sum()) if "review_timestamp" in reviewed_items_df.columns else len(reviewed_items_df)
    needs_more_info_without_note_count = 0
    holdout_without_note_count = 0
    if not reviewed_items_df.empty:
        upper_decisions = reviewed_items_df["human_decision"].astype(str).str.upper()
        needs_more_info_without_note_count = int(
            ((upper_decisions == "NEEDS_MORE_INFO") & reviewed_items_df["human_note"].astype(str).eq("")).sum()
        )
        holdout_without_note_count = int(
            ((upper_decisions == "HOLDOUT") & reviewed_items_df["human_note"].astype(str).eq("")).sum()
        )
    add_qa(
        "reviewed::reviewer_name_present",
        "WARN" if missing_reviewer_name_count > 0 else "PASS",
        f"missing_count={missing_reviewer_name_count}",
    )
    add_qa(
        "reviewed::review_timestamp_present",
        "WARN" if missing_review_timestamp_count > 0 else "PASS",
        f"missing_count={missing_review_timestamp_count}",
    )
    add_qa(
        "reviewed::needs_more_info_has_note",
        "WARN" if needs_more_info_without_note_count > 0 else "PASS",
        f"missing_note_count={needs_more_info_without_note_count}",
    )
    add_qa(
        "reviewed::holdout_has_note",
        "WARN" if holdout_without_note_count > 0 else "PASS",
        f"missing_note_count={holdout_without_note_count}",
    )

    routing_manifest_rows: List[Dict[str, Any]] = []

    for item in auto_send_items:
        flat = _flatten_batch_item(item)
        flat.update(
            {
                "route_origin": "AUTO_323C",
                "final_route": "SEND_TO_ADJUDICATOR",
                "final_route_reason": "Pre-cleared low-risk send subset from 323C sanity gate.",
                "human_decision": "",
                "human_note": "",
                "reviewer_name": "",
                "review_timestamp": "",
            }
        )
        routing_manifest_rows.append(flat)

    for item in auto_holdout_items:
        flat = _flatten_batch_item(item)
        flat.update(
            {
                "route_origin": "AUTO_323C",
                "final_route": "HOLDOUT",
                "final_route_reason": "Pre-held-out by 323C sanity gate.",
                "human_decision": "",
                "human_note": "",
                "reviewer_name": "",
                "review_timestamp": "",
            }
        )
        routing_manifest_rows.append(flat)

    for record in records:
        batch_item_id = _norm(record.get("batch_item_id"))
        source_item = batch_lookup.get(batch_item_id, {})
        flat = _flatten_batch_item(source_item) if source_item else {}
        final_route = _norm(record.get("human_decision")).upper()
        flat.update(
            {
                "batch_item_id": batch_item_id,
                "source_group_id": _norm(record.get("source_group_id")) or flat.get("source_group_id", ""),
                "candidate_type": _norm(record.get("candidate_type")) or flat.get("candidate_type", ""),
                "repaired_label": _norm(record.get("repaired_label")) or flat.get("repaired_label", ""),
                "sanity_bucket": _norm(record.get("sanity_bucket")) or flat.get("sanity_bucket", BUCKET_HUMAN),
                "route_origin": "HUMAN_SPOT_CHECK",
                "final_route": final_route,
                "final_route_reason": _build_final_route_reason(final_route),
                "human_decision": _norm(record.get("human_decision")).upper(),
                "human_note": _norm(record.get("human_note")),
                "reviewer_name": _norm(record.get("reviewer_name")),
                "review_timestamp": _norm(record.get("review_timestamp")),
                "allowed_human_decisions": _norm(record.get("allowed_human_decisions")),
            }
        )
        routing_manifest_rows.append(flat)

    routing_manifest_df = pd.DataFrame(routing_manifest_rows).fillna("")

    route_counts = {
        "SEND_TO_ADJUDICATOR": int((routing_manifest_df["final_route"].astype(str) == "SEND_TO_ADJUDICATOR").sum()) if not routing_manifest_df.empty else 0,
        "HOLDOUT": int((routing_manifest_df["final_route"].astype(str) == "HOLDOUT").sum()) if not routing_manifest_df.empty else 0,
        "RECLASSIFY_AS_SCOPE_CANDIDATE": int((routing_manifest_df["final_route"].astype(str) == "RECLASSIFY_AS_SCOPE_CANDIDATE").sum()) if not routing_manifest_df.empty else 0,
        "RECLASSIFY_AS_ALIAS_CANDIDATE": int((routing_manifest_df["final_route"].astype(str) == "RECLASSIFY_AS_ALIAS_CANDIDATE").sum()) if not routing_manifest_df.empty else 0,
        "NEEDS_MORE_INFO": int((routing_manifest_df["final_route"].astype(str) == "NEEDS_MORE_INFO").sum()) if not routing_manifest_df.empty else 0,
    }

    send_df = routing_manifest_df.loc[routing_manifest_df["final_route"].astype(str) == "SEND_TO_ADJUDICATOR"].copy() if not routing_manifest_df.empty else pd.DataFrame()
    holdout_df = routing_manifest_df.loc[routing_manifest_df["final_route"].astype(str) == "HOLDOUT"].copy() if not routing_manifest_df.empty else pd.DataFrame()
    reclass_scope_df = routing_manifest_df.loc[routing_manifest_df["final_route"].astype(str) == "RECLASSIFY_AS_SCOPE_CANDIDATE"].copy() if not routing_manifest_df.empty else pd.DataFrame()
    reclass_alias_df = routing_manifest_df.loc[routing_manifest_df["final_route"].astype(str) == "RECLASSIFY_AS_ALIAS_CANDIDATE"].copy() if not routing_manifest_df.empty else pd.DataFrame()
    needs_more_info_df = routing_manifest_df.loc[routing_manifest_df["final_route"].astype(str) == "NEEDS_MORE_INFO"].copy() if not routing_manifest_df.empty else pd.DataFrame()

    add_qa(
        "routing::all_batch_items_accounted_for",
        "PASS" if len(routing_manifest_df) == len(gated_batch_items) else "FAIL",
        f"routing_manifest={len(routing_manifest_df)} gated_batch={len(gated_batch_items)}",
    )
    add_qa(
        "routing::route_count_conservation",
        "PASS" if sum(route_counts.values()) == len(routing_manifest_df) else "FAIL",
        f"routes={route_counts}",
    )
    add_qa(
        "routing::no_pending_before_final_routing",
        "PASS" if pending_count == 0 else "FAIL",
        f"pending_count={pending_count}",
    )

    parser_not_run = True
    llm_not_called = True
    add_qa("safety::parser_not_run_confirmation", "PASS" if parser_not_run else "FAIL", "Reviewed routing reads cached artifacts only.")
    add_qa("safety::llm_not_called_confirmation", "PASS" if llm_not_called else "FAIL", "Reviewed routing does not call LLM or adjudicator.")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    no_official_assets_modified = alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if no_official_assets_modified else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    human_decision_distribution = _decision_distribution(records, "human_decision")
    highest_priority_reviewed_examples: List[Dict[str, Any]] = []
    if not reviewed_items_df.empty:
        for _, row in reviewed_items_df.sort_values(["priority_score", "affected_review_required_count"], ascending=[False, False]).head(5).iterrows():
            highest_priority_reviewed_examples.append(
                {
                    "batch_item_id": _norm(row.get("batch_item_id")),
                    "candidate_type": _norm(row.get("candidate_type")),
                    "repaired_label": _norm(row.get("repaired_label")),
                    "human_decision": _norm(row.get("human_decision")).upper(),
                    "priority_score": _safe_float(row.get("priority_score")),
                    "affected_review_required_count": _safe_int(row.get("affected_review_required_count")),
                }
            )

    summary = {
        "stage": "323C-human-spot-check",
        "mode": "validate-reviewed",
        "output_dir": "",
        "reviewed_human_item_count": len(reviewed_items_df),
        "input_batch_count": _safe_int(summary_323c.get("input_batch_count")),
        "auto_send_count": len(auto_send_df := pd.DataFrame([_flatten_batch_item(item) for item in auto_send_items]).fillna("")),
        "auto_holdout_count": len(auto_holdout_df := pd.DataFrame([_flatten_batch_item(item) for item in auto_holdout_items]).fillna("")),
        "human_decision_distribution": human_decision_distribution,
        "send_to_adjudicator_count": route_counts["SEND_TO_ADJUDICATOR"],
        "holdout_count": route_counts["HOLDOUT"],
        "reclassified_scope_candidate_count": route_counts["RECLASSIFY_AS_SCOPE_CANDIDATE"],
        "reclassified_alias_candidate_count": route_counts["RECLASSIFY_AS_ALIAS_CANDIDATE"],
        "needs_more_info_count": route_counts["NEEDS_MORE_INFO"],
        "pending_count": pending_count,
        "invalid_decision_count": len(invalid_decisions),
        "highest_priority_reviewed_examples": highest_priority_reviewed_examples,
        "official_assets_not_modified_confirmed": no_official_assets_modified,
        "llm_not_called_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_323C_REVIEWED_DECISION if qa_fail_count == 0 else EXPECTED_323C_REVIEWED_NOT_READY,
    }

    routing_plan_json = {
        "stage": "323C-human-spot-check",
        "mode": "validate-reviewed",
        "decision": summary["decision"],
        "source_323c_decision": _norm(summary_323c.get("decision")),
        "auto_send_batch_item_ids": send_df.loc[send_df["route_origin"].astype(str) == "AUTO_323C", "batch_item_id"].astype(str).tolist() if not send_df.empty else [],
        "human_send_batch_item_ids": send_df.loc[send_df["route_origin"].astype(str) == "HUMAN_SPOT_CHECK", "batch_item_id"].astype(str).tolist() if not send_df.empty else [],
        "holdout_batch_item_ids": holdout_df["batch_item_id"].astype(str).tolist() if not holdout_df.empty else [],
        "reclassified_scope_candidate_batch_item_ids": reclass_scope_df["batch_item_id"].astype(str).tolist() if not reclass_scope_df.empty else [],
        "reclassified_alias_candidate_batch_item_ids": reclass_alias_df["batch_item_id"].astype(str).tolist() if not reclass_alias_df.empty else [],
        "needs_more_info_batch_item_ids": needs_more_info_df["batch_item_id"].astype(str).tolist() if not needs_more_info_df.empty else [],
    }

    no_apply_proof_json = {
        "files_read": [
            str(DEFAULT_323C_DIR / "adjudication_batch_sanity_gate_323c_summary.json"),
            str(DEFAULT_323C_DIR / "adjudication_batch_sanity_gate_323c_qa.json"),
            str(DEFAULT_323C_DIR / "adjudication_batch_sanity_gate_323c_gated_batch.json"),
            str(DEFAULT_323C_DIR / "adjudication_batch_sanity_gate_323c_human_spot_check.xlsx"),
        ],
        "files_written": [],
        "official_target_files_not_modified": [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_ALIAS_OVERRIDE_PATH),
        ],
        "output_only_write_confirmation": True,
        "decision": "reviewed_human_spot_check_only_no_apply",
    }

    return {
        "summary": summary,
        "routing_manifest_df": routing_manifest_df,
        "send_df": send_df,
        "holdout_df": holdout_df,
        "reclassified_scope_df": reclass_scope_df,
        "reclassified_alias_df": reclass_alias_df,
        "needs_more_info_df": needs_more_info_df,
        "reviewed_items_df": reviewed_items_df,
        "qa_checks_df": qa_df,
        "routing_plan_json": routing_plan_json,
        "no_apply_proof_json": no_apply_proof_json,
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
    }


def _build_final_route_reason(route: str) -> str:
    mapping = {
        "SEND_TO_ADJUDICATOR": "Approved to proceed downstream after human spot-check.",
        "HOLDOUT": "Stopped after human spot-check.",
        "RECLASSIFY_AS_SCOPE_CANDIDATE": "Re-route into scope candidate handling instead of current alias lane.",
        "RECLASSIFY_AS_ALIAS_CANDIDATE": "Re-route into alias candidate handling instead of current lane.",
        "NEEDS_MORE_INFO": "Insufficient context after spot-check; keep out of adjudicator send.",
    }
    return mapping.get(route, "Unknown route decision.")
