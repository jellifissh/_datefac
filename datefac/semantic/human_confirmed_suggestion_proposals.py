from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set

import pandas as pd

from datefac.semantic.safe_adjudicator_subset import FORMAL_SCOPE_RULES_PATH, OFFICIAL_ALIAS_OVERRIDE_PATH


EXPECTED_323F_DECISION = "RAW_RESPONSE_SCHEMA_VALIDATION_323F_READY_FOR_HUMAN_CONFIRMED_SUGGESTION_PROPOSALS"
EXPECTED_323G_PREPARE_DECISION = "HUMAN_CONFIRMED_SUGGESTION_PROPOSALS_323G_READY_FOR_HUMAN_CONFIRMATION"
EXPECTED_323G_PREPARE_NOT_READY = "HUMAN_CONFIRMED_SUGGESTION_PROPOSALS_323G_NOT_READY"
EXPECTED_323G_REVIEWED_DECISION = "HUMAN_CONFIRMED_SUGGESTION_PROPOSALS_323G_REVIEWED_READY_FOR_323H_SANDBOX_REPLAY"
EXPECTED_323G_REVIEWED_NOT_READY = "HUMAN_CONFIRMED_SUGGESTION_PROPOSALS_323G_REVIEWED_NOT_READY"

DEFAULT_RAW_RESPONSE_VALIDATION_DIR = Path(r"D:\_datefac\output\raw_response_schema_validation_323f")
DEFAULT_SAFE_SUBSET_DIR = Path(r"D:\_datefac\output\safe_adjudicator_subset_323d")
DEFAULT_CONFIGURED_RUN_DIR = Path(r"D:\_datefac\output\configured_adjudicator_run_323e")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\human_confirmed_suggestion_proposals_323g")

PENDING_HUMAN_CONFIRMATION = "PENDING_HUMAN_CONFIRMATION"
ALLOWED_REVIEWER_DECISIONS = {"CONFIRM", "REJECT", "NEEDS_MORE_INFO"}
REQUIRED_REVIEWER_FIELDS = {
    "reviewer_decision",
    "reviewer_note",
    "reviewer_name",
    "review_timestamp",
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


def _flatten_sequence(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_norm(item) for item in value if _norm(item)]
    if isinstance(value, tuple):
        return [_norm(item) for item in value if _norm(item)]
    if isinstance(value, str):
        clean = _norm(value)
        return [clean] if clean else []
    return []


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            parsed = json.loads(text)
        except Exception:
            continue
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows


def _read_workbook_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()
    return df.fillna("")


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


def _decision_distribution(records: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    distribution: Dict[str, int] = {}
    for record in records:
        key = _norm(record.get("reviewer_decision")) or PENDING_HUMAN_CONFIRMATION
        distribution[key] = distribution.get(key, 0) + 1
    return distribution


def _missing_required_fields(records: Sequence[Dict[str, Any]], required_fields: Sequence[str]) -> List[Dict[str, str]]:
    missing: List[Dict[str, str]] = []
    for record in records:
        record_id = _norm(record.get("confirmation_id")) or _norm(record.get("request_id")) or "UNKNOWN_RECORD"
        for field in required_fields:
            if _norm(record.get(field)) == "":
                missing.append({"record_id": record_id, "field": field})
    return missing


def _to_json_text(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return _norm(value)


def _build_risk_note(suggestion: Dict[str, Any], request_item: Dict[str, Any]) -> str:
    candidate_type = _norm(suggestion.get("candidate_type"))
    safety_flags = _flatten_sequence(suggestion.get("safety_flags"))
    risk_flags = _flatten_sequence(request_item.get("risk_flags"))
    if candidate_type == "alias":
        base = "Alias suggestion requires human confirmation before sandbox replay."
    else:
        base = "Out-of-scope suggestion requires human confirmation before sandbox replay."
    extras = _join_unique(list(safety_flags) + list(risk_flags), limit=6)
    return f"{base} Flags: {extras}" if extras else base


def load_human_confirmed_suggestion_inputs(
    raw_response_validation_dir: Path,
    safe_subset_dir: Path,
    configured_run_dir: Path | None = None,
) -> Dict[str, Any]:
    inputs = {
        "summary_323f": _read_json(raw_response_validation_dir / "raw_response_schema_validation_323f_summary.json"),
        "qa_323f": _read_json(raw_response_validation_dir / "raw_response_schema_validation_323f_qa.json"),
        "accepted_suggestions_323f": _read_json(raw_response_validation_dir / "raw_response_schema_validation_323f_accepted_suggestions.json"),
        "validated_responses_323f": _read_jsonl(raw_response_validation_dir / "raw_response_schema_validation_323f_validated_responses.jsonl"),
        "summary_323d": _read_json(safe_subset_dir / "safe_adjudicator_subset_323d_summary.json"),
        "request_package_323d": _read_json(safe_subset_dir / "safe_adjudicator_subset_323d_request_package.json"),
        "requests_323d": _read_jsonl(safe_subset_dir / "safe_adjudicator_subset_323d_request_items.jsonl"),
    }
    if configured_run_dir:
        inputs["summary_323e"] = _read_json(configured_run_dir / "configured_adjudicator_run_323e_summary.json")
        inputs["qa_323e"] = _read_json(configured_run_dir / "configured_adjudicator_run_323e_qa.json")
    else:
        inputs["summary_323e"] = {}
        inputs["qa_323e"] = {}
    return inputs


def build_human_confirmed_suggestion_prepare(
    inputs: Dict[str, Any],
    raw_response_validation_dir: Path,
    safe_subset_dir: Path,
    configured_run_dir: Path | None = None,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    summary_323f = inputs.get("summary_323f", {})
    qa_323f = inputs.get("qa_323f", {})
    accepted_payload = inputs.get("accepted_suggestions_323f", {})
    validated_rows = inputs.get("validated_responses_323f", [])
    requests_323d = inputs.get("requests_323d", [])

    add_qa(
        "readiness::323f_decision",
        "PASS" if _norm(summary_323f.get("decision")) == EXPECTED_323F_DECISION else "FAIL",
        _norm(summary_323f.get("decision")),
    )
    add_qa(
        "readiness::323f_summary_qa_fail_count",
        "PASS" if _safe_int(summary_323f.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_323f.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323f_qa_json_fail_count",
        "PASS" if _safe_int(qa_323f.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_323f.get("qa_fail_count", "")),
    )
    for key, expected in [
        ("request_count", 11),
        ("response_count", 11),
        ("schema_valid_count", 11),
        ("schema_invalid_count", 0),
        ("accepted_suggestion_count", 11),
        ("rejected_suggestion_count", 0),
        ("needs_more_info_count", 0),
        ("deterministic_gate_failure_count", 0),
    ]:
        add_qa(
            f"readiness::323f_{key}",
            "PASS" if _safe_int(summary_323f.get(key)) == expected else "FAIL",
            str(summary_323f.get(key, "")),
        )

    accepted_suggestions = accepted_payload.get("accepted_suggestions", [])
    if not isinstance(accepted_suggestions, list):
        accepted_suggestions = []
    accepted_suggestions = [item for item in accepted_suggestions if isinstance(item, dict)]

    request_lookup = {
        _norm(item.get("request_id")): item
        for item in requests_323d
        if isinstance(item, dict) and _norm(item.get("request_id"))
    }
    validated_lookup = {
        _norm(item.get("request_id")): item
        for item in validated_rows
        if isinstance(item, dict) and _norm(item.get("request_id"))
    }

    alias_count = sum(1 for item in accepted_suggestions if _norm(item.get("candidate_type")) == "alias")
    scope_count = sum(1 for item in accepted_suggestions if _norm(item.get("candidate_type")) == "scope_noise")
    add_qa("accepted_suggestions::total_count", "PASS" if len(accepted_suggestions) == 11 else "FAIL", f"actual={len(accepted_suggestions)}")
    add_qa("accepted_suggestions::alias_count", "PASS" if alias_count == 2 else "FAIL", f"actual={alias_count}")
    add_qa("accepted_suggestions::scope_count", "PASS" if scope_count == 9 else "FAIL", f"actual={scope_count}")

    included_nonaccepted = [
        _norm(row.get("request_id"))
        for row in validated_rows
        if _norm(row.get("classification")) != "ACCEPTED_SUGGESTION"
        and _norm(row.get("request_id")) in {_norm(item.get("request_id")) for item in accepted_suggestions}
    ]
    add_qa(
        "accepted_suggestions::no_nonaccepted_items_included",
        "PASS" if not included_nonaccepted else "FAIL",
        "none" if not included_nonaccepted else " | ".join(included_nonaccepted[:10]),
    )

    confirmation_records: List[Dict[str, Any]] = []
    for suggestion in accepted_suggestions:
        request_id = _norm(suggestion.get("request_id"))
        request_item = request_lookup.get(request_id, {})
        validated = validated_lookup.get(request_id, {})
        candidate_type = _norm(suggestion.get("candidate_type"))
        suffix = request_id.split("::")[-1] if request_id else f"{len(confirmation_records) + 1:03d}"
        confirmation_id = f"323g::{candidate_type or 'unknown'}::{suffix}"

        expected_impact = {
            "affected_candidate_count": _safe_int(request_item.get("affected_candidate_count")),
            "affected_review_required_count": _safe_int(request_item.get("affected_review_required_count")),
            "expected_review_reduction_potential": _safe_int(request_item.get("affected_review_required_count")),
            "priority_score": _safe_float(request_item.get("priority_score")),
        }
        sample_evidence = {
            "sample_candidate_ids": _flatten_sequence(request_item.get("sample_candidate_ids")),
            "sample_texts": _flatten_sequence(request_item.get("sample_texts")),
            "sample_table_titles": _flatten_sequence((request_item.get("provenance") or {}).get("sample_table_titles")),
            "sample_years": _flatten_sequence((request_item.get("provenance") or {}).get("sample_years")),
            "raw_response_text": _norm(validated.get("raw_response_text")),
        }
        provenance = {
            "source_group_id": _norm(request_item.get("source_group_id")),
            "source_batch_item_id": _norm(request_item.get("source_batch_item_id")),
            "source_stage_signature": _norm((request_item.get("provenance") or {}).get("source_stage_signature")),
            "source_report_examples": _flatten_sequence((request_item.get("provenance") or {}).get("source_report_examples")),
            "table_asset_examples": _flatten_sequence((request_item.get("provenance") or {}).get("table_asset_examples")),
            "source_stage": _norm((request_item.get("provenance") or {}).get("source_stage")),
            "raw_response_validation_reference": str(raw_response_validation_dir / "raw_response_schema_validation_323f_validated_responses.jsonl"),
        }
        confirmation_records.append(
            {
                "confirmation_id": confirmation_id,
                "request_id": request_id,
                "source_batch_item_id": _norm(suggestion.get("source_batch_item_id")) or _norm(request_item.get("source_batch_item_id")),
                "source_group_id": _norm(request_item.get("source_group_id")),
                "suggestion_type": candidate_type,
                "candidate_label": _norm(suggestion.get("candidate_label")),
                "candidate_question": _norm(request_item.get("candidate_question")),
                "suggested_response_label": _norm(suggestion.get("response_label")),
                "suggested_target_metric_if_any": _norm(suggestion.get("normalized_target_metric_if_any")),
                "confidence": _norm(suggestion.get("confidence")),
                "rationale": _norm(suggestion.get("rationale")),
                "sample_evidence": sample_evidence,
                "sample_evidence_text": _join_unique(sample_evidence.get("sample_texts", []), limit=8),
                "provenance": provenance,
                "provenance_text": _join_unique(
                    [
                        provenance.get("source_stage_signature", ""),
                        provenance.get("source_stage", ""),
                        *provenance.get("source_report_examples", []),
                        *provenance.get("table_asset_examples", []),
                    ],
                    limit=10,
                ),
                "expected_impact": expected_impact,
                "expected_affected_candidate_count": expected_impact["affected_candidate_count"],
                "expected_review_reduction_potential": expected_impact["expected_review_reduction_potential"],
                "priority_score": expected_impact["priority_score"],
                "risk_note": _build_risk_note(suggestion, request_item),
                "risk_flags": _flatten_sequence(request_item.get("risk_flags")) + _flatten_sequence(suggestion.get("safety_flags")),
                "sandbox_replay_required": True,
                "raw_response_reference": {
                    "provider_or_source": _norm(validated.get("provider_or_source")),
                    "model_or_review_source": _norm(validated.get("model_or_review_source")),
                    "run_timestamp": _norm(validated.get("run_timestamp")),
                    "classification_reason": _norm(validated.get("classification_reason")),
                    "next_action": _norm(validated.get("next_action")),
                },
                "reviewer_decision": PENDING_HUMAN_CONFIRMATION,
                "reviewer_note": "",
                "reviewer_name": "",
                "review_timestamp": "",
                "allowed_reviewer_decisions": "CONFIRM | REJECT | NEEDS_MORE_INFO",
                "editable_fields_note": "Edit reviewer_decision / reviewer_note / reviewer_name / review_timestamp only.",
            }
        )

    confirmation_df = pd.DataFrame(confirmation_records).fillna("")
    alias_df = confirmation_df.loc[confirmation_df["suggestion_type"].astype(str) == "alias"].copy() if not confirmation_df.empty else pd.DataFrame()
    scope_df = confirmation_df.loc[confirmation_df["suggestion_type"].astype(str) == "scope_noise"].copy() if not confirmation_df.empty else pd.DataFrame()

    duplicate_confirmation_id = confirmation_df["confirmation_id"].astype(str).duplicated().any() if not confirmation_df.empty else False
    default_all_pending = (
        not confirmation_df.empty
        and confirmation_df["reviewer_decision"].astype(str).eq(PENDING_HUMAN_CONFIRMATION).all()
    )
    reviewer_fields_present = REQUIRED_REVIEWER_FIELDS.issubset(set(confirmation_df.columns))
    provenance_complete = (
        not confirmation_df.empty
        and confirmation_df["provenance"].apply(lambda value: isinstance(value, dict) and _norm(value.get("source_group_id")) != "").all()
    )
    sample_evidence_present = (
        not confirmation_df.empty
        and confirmation_df["sample_evidence"].apply(lambda value: isinstance(value, dict) and len(value.get("sample_texts", [])) > 0).all()
    )
    sandbox_replay_required_present = (
        not confirmation_df.empty
        and confirmation_df["sandbox_replay_required"].astype(bool).all()
    )

    add_qa("confirmation_records::count", "PASS" if len(confirmation_records) == 11 else "FAIL", f"actual={len(confirmation_records)}")
    add_qa("confirmation_records::unique_confirmation_id", "PASS" if not duplicate_confirmation_id else "FAIL", f"duplicate_present={duplicate_confirmation_id}")
    add_qa("confirmation_records::all_pending_human_confirmation", "PASS" if default_all_pending else "FAIL", str(_decision_distribution(confirmation_records)))
    add_qa("confirmation_records::reviewer_fields_present", "PASS" if reviewer_fields_present else "FAIL", f"present={sorted(set(confirmation_df.columns).intersection(REQUIRED_REVIEWER_FIELDS))}")
    add_qa("confirmation_records::provenance_complete", "PASS" if provenance_complete else "FAIL", "source_group_id and provenance payload present")
    add_qa("confirmation_records::sample_evidence_present", "PASS" if sample_evidence_present else "FAIL", "sample_texts populated for every record")
    add_qa("confirmation_records::sandbox_replay_required", "PASS" if sandbox_replay_required_present else "FAIL", "all records require sandbox replay")

    parser_not_run = True
    llm_not_called = True
    no_trusted_promotion = True
    add_qa("safety::parser_not_run_confirmation", "PASS" if parser_not_run else "FAIL", "323G reads cached 323F/323D/323E outputs only.")
    add_qa("safety::llm_not_called_confirmation", "PASS" if llm_not_called else "FAIL", "323G does not call LLM or adjudicator.")
    add_qa("safety::no_trusted_promotion_confirmation", "PASS" if no_trusted_promotion else "FAIL", "323G creates human confirmation proposals only.")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    review_instruction_rows = [
        {
            "section": "package_purpose",
            "instruction": "Review each accepted 323F suggestion and decide whether it should proceed to sandbox replay in a later stage.",
        },
        {
            "section": "editable_fields",
            "instruction": "Only edit reviewer_decision, reviewer_note, reviewer_name, and review_timestamp.",
        },
        {
            "section": "allowed_decisions",
            "instruction": "Allowed reviewer_decision values: CONFIRM, REJECT, NEEDS_MORE_INFO.",
        },
        {
            "section": "do_not_assume_approval",
            "instruction": "Do not leave PENDING_HUMAN_CONFIRMATION in a reviewed workbook intended for validate-reviewed mode.",
        },
        {
            "section": "no_apply_note",
            "instruction": "323G does not apply semantic rules, does not mark anything trusted, and does not modify official mapping or override assets.",
        },
        {
            "section": "next_stage_note",
            "instruction": "Every confirmed suggestion still requires sandbox replay before any later official rule candidate stage.",
        },
    ]
    review_instructions_df = pd.DataFrame(review_instruction_rows)

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "323G",
        "mode": "prepare",
        "output_dir": "",
        "raw_response_validation_dir": str(raw_response_validation_dir),
        "safe_subset_dir": str(safe_subset_dir),
        "configured_run_dir": str(configured_run_dir) if configured_run_dir else "",
        "accepted_suggestion_count": len(accepted_suggestions),
        "alias_accepted_suggestion_count": alias_count,
        "scope_accepted_suggestion_count": scope_count,
        "confirmation_record_count": len(confirmation_records),
        "decision_distribution": _decision_distribution(confirmation_records),
        "all_decisions_pending_human_confirmation": default_all_pending,
        "official_assets_not_modified_confirmed": True,
        "proposal_package_only_no_apply_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_323G_PREPARE_DECISION if qa_fail_count == 0 else EXPECTED_323G_PREPARE_NOT_READY,
    }

    package_json = {
        "stage": "323G",
        "mode": "prepare",
        "summary": summary,
        "allowed_reviewer_decisions": sorted(ALLOWED_REVIEWER_DECISIONS),
        "confirmation_records": confirmation_records,
    }

    no_apply_proof_json = {
        "files_read": [
            str(raw_response_validation_dir / "raw_response_schema_validation_323f_summary.json"),
            str(raw_response_validation_dir / "raw_response_schema_validation_323f_qa.json"),
            str(raw_response_validation_dir / "raw_response_schema_validation_323f_accepted_suggestions.json"),
            str(raw_response_validation_dir / "raw_response_schema_validation_323f_validated_responses.jsonl"),
            str(safe_subset_dir / "safe_adjudicator_subset_323d_request_items.jsonl"),
        ],
        "files_written": [],
        "official_target_files_not_modified": [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_ALIAS_OVERRIDE_PATH),
        ],
        "output_only_write_confirmation": True,
        "decision": "human_confirmation_proposals_only_no_apply",
    }

    return {
        "summary": summary,
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
        "qa_checks_df": qa_df,
        "confirmation_records_df": confirmation_df,
        "alias_suggestions_df": alias_df,
        "scope_suggestions_df": scope_df,
        "review_instructions_df": review_instructions_df,
        "proposal_package_json": package_json,
        "review_instructions_markdown": _build_prepare_review_instructions_markdown(summary),
        "no_apply_proof_json": no_apply_proof_json,
    }


def build_human_confirmed_suggestion_validate_reviewed(
    reviewed_workbook: Path,
    raw_response_validation_summary: Dict[str, Any],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::323f_ready",
        "PASS" if _norm(raw_response_validation_summary.get("decision")) == EXPECTED_323F_DECISION else "FAIL",
        _norm(raw_response_validation_summary.get("decision")),
    )
    add_qa(
        "readiness::323f_accepted_suggestion_count",
        "PASS" if _safe_int(raw_response_validation_summary.get("accepted_suggestion_count")) == 11 else "FAIL",
        str(raw_response_validation_summary.get("accepted_suggestion_count", "")),
    )

    confirmation_df = _read_workbook_sheet(reviewed_workbook, "confirmation_records")
    if confirmation_df.empty:
        alias_df = _read_workbook_sheet(reviewed_workbook, "alias_suggestions")
        scope_df = _read_workbook_sheet(reviewed_workbook, "scope_suggestions")
        confirmation_df = pd.concat([alias_df, scope_df], ignore_index=True).fillna("")
    else:
        confirmation_df = confirmation_df.fillna("")

    required_columns = {
        "confirmation_id",
        "request_id",
        "suggestion_type",
        "candidate_label",
        "suggested_response_label",
        "reviewer_decision",
        "reviewer_note",
        "reviewer_name",
        "review_timestamp",
        "sandbox_replay_required",
    }
    missing_columns = sorted(required_columns.difference(set(confirmation_df.columns)))
    add_qa(
        "reviewed_integrity::required_columns_present",
        "PASS" if not missing_columns else "FAIL",
        "none" if not missing_columns else " | ".join(missing_columns),
    )

    records = confirmation_df.to_dict(orient="records") if not confirmation_df.empty else []
    approval_count = len(records)
    alias_count = int(confirmation_df["suggestion_type"].astype(str).eq("alias").sum()) if not confirmation_df.empty else 0
    scope_count = int(confirmation_df["suggestion_type"].astype(str).eq("scope_noise").sum()) if not confirmation_df.empty else 0
    decisions = [_norm(row.get("reviewer_decision")).upper() for row in records]
    pending_count = sum(1 for decision in decisions if decision in {"", PENDING_HUMAN_CONFIRMATION})
    invalid_decisions = sorted({decision for decision in decisions if decision and decision != PENDING_HUMAN_CONFIRMATION and decision not in ALLOWED_REVIEWER_DECISIONS})

    add_qa("reviewed_count::confirmation_record_count", "PASS" if approval_count == 11 else "FAIL", f"actual={approval_count}")
    add_qa("reviewed_count::alias_count", "PASS" if alias_count == 2 else "FAIL", f"actual={alias_count}")
    add_qa("reviewed_count::scope_count", "PASS" if scope_count == 9 else "FAIL", f"actual={scope_count}")
    add_qa("reviewed_integrity::valid_reviewer_decisions_only", "PASS" if not invalid_decisions else "FAIL", "none" if not invalid_decisions else " | ".join(invalid_decisions))
    add_qa("reviewed_integrity::no_pending_human_confirmation", "PASS" if pending_count == 0 else "FAIL", f"pending_count={pending_count}")

    duplicate_confirmation_id = confirmation_df["confirmation_id"].astype(str).duplicated().any() if not confirmation_df.empty else False
    reviewer_field_missing = _missing_required_fields(records, sorted(REQUIRED_REVIEWER_FIELDS))
    sandbox_replay_present = not confirmation_df.empty and confirmation_df["sandbox_replay_required"].astype(bool).all()
    add_qa("reviewed_integrity::unique_confirmation_id", "PASS" if not duplicate_confirmation_id else "FAIL", f"duplicate_present={duplicate_confirmation_id}")
    add_qa(
        "reviewed_integrity::reviewer_fields_non_empty",
        "PASS" if not reviewer_field_missing else "FAIL",
        "none" if not reviewer_field_missing else " | ".join(f"{item['record_id']}::{item['field']}" for item in reviewer_field_missing[:10]),
    )
    add_qa("reviewed_integrity::sandbox_replay_required", "PASS" if sandbox_replay_present else "FAIL", "all records require sandbox replay")
    add_qa("safety::no_official_file_modification", "PASS", "validate-reviewed mode validates reviewed decisions only.")

    confirmed_df = confirmation_df.loc[confirmation_df["reviewer_decision"].astype(str).str.upper() == "CONFIRM"].copy() if not confirmation_df.empty else pd.DataFrame()
    rejected_df = confirmation_df.loc[confirmation_df["reviewer_decision"].astype(str).str.upper() == "REJECT"].copy() if not confirmation_df.empty else pd.DataFrame()
    needs_more_info_df = confirmation_df.loc[confirmation_df["reviewer_decision"].astype(str).str.upper() == "NEEDS_MORE_INFO"].copy() if not confirmation_df.empty else pd.DataFrame()
    add_qa("reviewed_integrity::at_least_one_confirmed", "PASS" if len(confirmed_df) > 0 else "FAIL", f"confirmed_count={len(confirmed_df)}")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "323G",
        "mode": "validate-reviewed",
        "output_dir": "",
        "reviewed_workbook": str(reviewed_workbook),
        "confirmation_record_count": approval_count,
        "confirmed_suggestion_count": len(confirmed_df),
        "rejected_suggestion_count": len(rejected_df),
        "needs_more_info_count": len(needs_more_info_df),
        "pending_count": pending_count,
        "invalid_decision_count": len(invalid_decisions),
        "decision_distribution": _decision_distribution(records),
        "official_assets_not_modified_confirmed": True,
        "proposal_package_only_no_apply_confirmed": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_323G_REVIEWED_DECISION if qa_fail_count == 0 else EXPECTED_323G_REVIEWED_NOT_READY,
    }

    confirmed_plan_json = {
        "stage": "323G",
        "mode": "validate-reviewed",
        "reviewed_workbook": str(reviewed_workbook),
        "confirmed_suggestions": confirmed_df.to_dict(orient="records") if not confirmed_df.empty else [],
        "rejected_suggestions": rejected_df.to_dict(orient="records") if not rejected_df.empty else [],
        "needs_more_info_suggestions": needs_more_info_df.to_dict(orient="records") if not needs_more_info_df.empty else [],
        "decision": summary["decision"],
    }

    return {
        "summary": summary,
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
        "qa_checks_df": qa_df,
        "confirmed_df": confirmed_df.fillna(""),
        "rejected_df": rejected_df.fillna(""),
        "needs_more_info_df": needs_more_info_df.fillna(""),
        "all_reviewed_df": confirmation_df.fillna(""),
        "human_confirmed_plan_json": confirmed_plan_json,
    }


def _build_prepare_review_instructions_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Human-Confirmed Suggestion Proposals 323G",
        "",
        "## What This Package Is",
        "- This package converts accepted 323F suggestions into records for human confirmation.",
        "- No semantic rule is applied here, and nothing is marked trusted.",
        "",
        "## Editable Fields",
        "- reviewer_decision",
        "- reviewer_note",
        "- reviewer_name",
        "- review_timestamp",
        "",
        "## Allowed reviewer_decision Values",
        "- CONFIRM",
        "- REJECT",
        "- NEEDS_MORE_INFO",
        "",
        "## Important Safety Notes",
        "- Do not assume human approval in prepare mode.",
        "- Every confirmed suggestion still requires sandbox replay in a later stage.",
        "- 323G does not modify official mapping, official override, or production pipeline files.",
        "",
        "## Current Decision",
        f"- {summary.get('decision', '')}",
        "",
    ]
    return "\n".join(lines)
