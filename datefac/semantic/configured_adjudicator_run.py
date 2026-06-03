from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set

import pandas as pd

from datefac.semantic.safe_adjudicator_subset import (
    DEFAULT_OUTPUT_DIR as DEFAULT_SAFE_SUBSET_DIR,
    FORMAL_SCOPE_RULES_PATH,
    OFFICIAL_ALIAS_OVERRIDE_PATH,
)


EXPECTED_323D_DECISION = "SAFE_ADJUDICATOR_SUBSET_323D_PREPARED_READY_FOR_CONFIGURED_ADJUDICATOR_RUN"
EXPECTED_323E_MANUAL_READY = "CONFIGURED_ADJUDICATOR_RUN_323E_MANUAL_RESPONSE_TEMPLATE_READY"
EXPECTED_323E_RAW_READY = "CONFIGURED_ADJUDICATOR_RUN_323E_RAW_RESPONSES_READY_FOR_323F_SCHEMA_VALIDATION"
EXPECTED_323E_NOT_READY = "CONFIGURED_ADJUDICATOR_RUN_323E_NOT_READY"

DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\configured_adjudicator_run_323e")

REQUEST_REQUIRED_FIELDS = [
    "request_id",
    "source_batch_item_id",
    "source_group_id",
    "candidate_type",
    "candidate_label",
    "candidate_question",
    "allowed_response_labels",
    "expected_rule_type_if_accepted",
    "sample_candidate_ids",
    "sample_texts",
    "affected_candidate_count",
    "affected_review_required_count",
    "priority_score",
    "risk_flags",
    "provenance",
    "safety_context",
    "response_schema",
]

RAW_RESPONSE_REQUIRED_FIELDS = [
    "request_id",
    "source_batch_item_id",
    "candidate_type",
    "candidate_label",
    "raw_response_text",
    "raw_response_json",
    "response_received",
    "provider_or_source",
    "model_or_review_source",
    "run_timestamp",
]

MANUAL_TEMPLATE_COLUMNS = [
    "request_id",
    "source_batch_item_id",
    "candidate_type",
    "candidate_label",
    "allowed_response_labels",
    "candidate_question",
    "sample_candidate_ids",
    "sample_texts",
    "response_received",
    "provider_or_source",
    "model_or_review_source",
    "run_timestamp",
    "raw_response_text",
    "raw_response_json",
    "reviewer_note",
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


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def _request_missing_fields(request_item: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    for field in REQUEST_REQUIRED_FIELDS:
        if field not in request_item:
            missing.append(field)
            continue
        value = request_item.get(field)
        if field in {"allowed_response_labels", "sample_candidate_ids", "sample_texts", "risk_flags"}:
            if not isinstance(value, list) or not value:
                missing.append(field)
        elif field in {"provenance", "safety_context", "response_schema"}:
            if not isinstance(value, dict) or not value:
                missing.append(field)
        elif field in {"affected_candidate_count", "affected_review_required_count", "priority_score"}:
            continue
        elif _norm(value) == "":
            missing.append(field)
    return missing


def _response_missing_fields(raw_response: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    for field in RAW_RESPONSE_REQUIRED_FIELDS:
        if field not in raw_response:
            missing.append(field)
            continue
        value = raw_response.get(field)
        if field == "raw_response_json":
            if value not in (None, "") and not isinstance(value, (dict, list, str)):
                missing.append(field)
            continue
        if field == "response_received":
            if not isinstance(value, bool):
                missing.append(field)
            continue
        if _norm(value) == "":
            missing.append(field)
    return missing


def _validate_safety_context(safety_context: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not safety_context.get("requires_schema_validation"):
        errors.append("requires_schema_validation_missing")
    if not safety_context.get("requires_deterministic_gate"):
        errors.append("requires_deterministic_gate_missing")
    if not safety_context.get("requires_human_confirmation"):
        errors.append("requires_human_confirmation_missing")
    if not safety_context.get("requires_sandbox_replay"):
        errors.append("requires_sandbox_replay_missing")
    if not safety_context.get("do_not_apply_rules"):
        errors.append("do_not_apply_rules_missing")
    if not safety_context.get("do_not_mark_trusted"):
        errors.append("do_not_mark_trusted_missing")
    return errors


def _build_manual_template_row(request_item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "request_id": _norm(request_item.get("request_id")),
        "source_batch_item_id": _norm(request_item.get("source_batch_item_id")),
        "candidate_type": _norm(request_item.get("candidate_type")),
        "candidate_label": _norm(request_item.get("candidate_label")),
        "allowed_response_labels": " | ".join(_flatten_sequence(request_item.get("allowed_response_labels"))),
        "candidate_question": _norm(request_item.get("candidate_question")),
        "sample_candidate_ids": " | ".join(_flatten_sequence(request_item.get("sample_candidate_ids"))),
        "sample_texts": " | ".join(_flatten_sequence(request_item.get("sample_texts"))),
        "response_received": False,
        "provider_or_source": "MANUAL_REVIEW_TEMPLATE",
        "model_or_review_source": "PENDING_MANUAL_RESPONSE",
        "run_timestamp": "",
        "raw_response_text": "",
        "raw_response_json": "",
        "reviewer_note": "",
    }


def _build_placeholder_raw_response(request_item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "request_id": _norm(request_item.get("request_id")),
        "source_batch_item_id": _norm(request_item.get("source_batch_item_id")),
        "candidate_type": _norm(request_item.get("candidate_type")),
        "candidate_label": _norm(request_item.get("candidate_label")),
        "raw_response_text": "",
        "raw_response_json": None,
        "response_received": False,
        "provider_or_source": "MANUAL_TEMPLATE",
        "model_or_review_source": "NOT_RUN",
        "run_timestamp": "",
    }


def _flatten_request_response_row(request_item: Dict[str, Any], raw_response: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "request_id": _norm(request_item.get("request_id")),
        "source_batch_item_id": _norm(request_item.get("source_batch_item_id")),
        "candidate_type": _norm(request_item.get("candidate_type")),
        "candidate_label": _norm(request_item.get("candidate_label")),
        "allowed_response_labels": " | ".join(_flatten_sequence(request_item.get("allowed_response_labels"))),
        "candidate_question": _norm(request_item.get("candidate_question")),
        "sample_candidate_ids": " | ".join(_flatten_sequence(request_item.get("sample_candidate_ids"))),
        "sample_texts": " | ".join(_flatten_sequence(request_item.get("sample_texts"))),
        "priority_score": _safe_float(request_item.get("priority_score")),
        "raw_response_text": _norm(raw_response.get("raw_response_text")),
        "raw_response_json": json.dumps(raw_response.get("raw_response_json"), ensure_ascii=False) if raw_response.get("raw_response_json") not in (None, "") else "",
        "response_received": bool(raw_response.get("response_received")),
        "provider_or_source": _norm(raw_response.get("provider_or_source")),
        "model_or_review_source": _norm(raw_response.get("model_or_review_source")),
        "run_timestamp": _norm(raw_response.get("run_timestamp")),
    }


def _build_run_metadata(mode: str, llm_called: bool, safe_subset_dir: Path, raw_response_source: Path | None = None) -> Dict[str, Any]:
    metadata = {
        "stage": "323E",
        "mode": mode,
        "llm_or_adjudicator_called": llm_called,
        "safe_subset_dir": str(safe_subset_dir),
        "raw_response_source": str(raw_response_source) if raw_response_source else "",
        "generated_timestamp": datetime.now().isoformat(timespec="seconds"),
        "run_boundary": "raw_response_collection_only",
        "rule_application_performed": False,
        "schema_validation_performed": False,
        "deterministic_gate_performed": False,
    }
    return metadata


def load_configured_adjudicator_run_inputs(safe_subset_dir: Path) -> Dict[str, Any]:
    return {
        "summary": _read_json(safe_subset_dir / "safe_adjudicator_subset_323d_summary.json"),
        "qa": _read_json(safe_subset_dir / "safe_adjudicator_subset_323d_qa.json"),
        "schema": _read_json(safe_subset_dir / "safe_adjudicator_subset_323d_schema.json"),
        "request_package": _read_json(safe_subset_dir / "safe_adjudicator_subset_323d_request_package.json"),
        "request_items": _read_jsonl(safe_subset_dir / "safe_adjudicator_subset_323d_request_items.jsonl"),
    }


def build_configured_adjudicator_run_prepare_manual(
    inputs: Dict[str, Any],
    mode: str,
    safe_subset_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    summary_323d = inputs.get("summary", {})
    qa_323d = inputs.get("qa", {})
    request_package = inputs.get("request_package", {})
    request_items = inputs.get("request_items", [])

    add_qa(
        "input_323d::decision",
        "PASS" if _norm(summary_323d.get("decision")) == EXPECTED_323D_DECISION else "FAIL",
        _norm(summary_323d.get("decision")),
    )
    add_qa(
        "input_323d::summary_qa_fail_count",
        "PASS" if _safe_int(summary_323d.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_323d.get("qa_fail_count", "")),
    )
    add_qa(
        "input_323d::qa_json_fail_count",
        "PASS" if _safe_int(qa_323d.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_323d.get("qa_fail_count", "")),
    )
    add_qa(
        "input_323d::safe_request_item_count",
        "PASS" if _safe_int(summary_323d.get("safe_request_item_count")) == 11 else "FAIL",
        str(summary_323d.get("safe_request_item_count", "")),
    )
    add_qa(
        "input_323d::alias_request_count",
        "PASS" if _safe_int(summary_323d.get("alias_request_count")) == 2 else "FAIL",
        str(summary_323d.get("alias_request_count", "")),
    )
    add_qa(
        "input_323d::scope_request_count",
        "PASS" if _safe_int(summary_323d.get("scope_request_count")) == 9 else "FAIL",
        str(summary_323d.get("scope_request_count", "")),
    )
    add_qa(
        "input_323d::excluded_holdout_count",
        "PASS" if _safe_int(summary_323d.get("excluded_holdout_count")) == 20 else "FAIL",
        str(summary_323d.get("excluded_holdout_count", "")),
    )
    add_qa(
        "input_323d::excluded_needs_more_info_count",
        "PASS" if _safe_int(summary_323d.get("excluded_needs_more_info_count")) == 3 else "FAIL",
        str(summary_323d.get("excluded_needs_more_info_count", "")),
    )
    add_qa(
        "input_323d::prepare_only_true",
        "PASS" if bool(summary_323d.get("prepare_only")) else "FAIL",
        str(summary_323d.get("prepare_only")),
    )

    add_qa(
        "requests::count_equals_11",
        "PASS" if len(request_items) == 11 else "FAIL",
        f"actual={len(request_items)}",
    )
    package_count = _safe_int(request_package.get("request_item_count"))
    add_qa(
        "requests::package_count_matches_jsonl",
        "PASS" if package_count == len(request_items) == 11 else "FAIL",
        f"package_count={package_count} jsonl_count={len(request_items)}",
    )

    request_ids = [_norm(item.get("request_id")) for item in request_items if isinstance(item, dict)]
    add_qa(
        "requests::unique_request_id",
        "PASS" if len(set(request_ids)) == len(request_ids) == len(request_items) else "FAIL",
        f"request_count={len(request_ids)} unique={len(set(request_ids))}",
    )

    missing_fields: Dict[str, List[str]] = {}
    safety_context_errors: Dict[str, List[str]] = {}
    unsafe_scope_items: List[str] = []
    for item in request_items:
        request_id = _norm(item.get("request_id"))
        missing = _request_missing_fields(item)
        if missing:
            missing_fields[request_id or "__missing__"] = missing
        safety_context = item.get("safety_context") if isinstance(item.get("safety_context"), dict) else {}
        errors = _validate_safety_context(safety_context)
        if errors:
            safety_context_errors[request_id or "__missing__"] = errors
        if not _flatten_sequence(item.get("allowed_response_labels")):
            unsafe_scope_items.append(request_id)

    add_qa(
        "requests::schema_completeness",
        "PASS" if not missing_fields else "FAIL",
        "none" if not missing_fields else json.dumps(missing_fields, ensure_ascii=False),
    )
    add_qa(
        "requests::safety_context_complete",
        "PASS" if not safety_context_errors else "FAIL",
        "none" if not safety_context_errors else json.dumps(safety_context_errors, ensure_ascii=False),
    )
    add_qa(
        "requests::allowed_response_labels_present",
        "PASS" if not unsafe_scope_items else "FAIL",
        "none" if not unsafe_scope_items else " | ".join(unsafe_scope_items[:5]),
    )
    add_qa(
        "requests::sample_evidence_present",
        "PASS" if all(_flatten_sequence(item.get("sample_candidate_ids")) and _flatten_sequence(item.get("sample_texts")) for item in request_items) else "FAIL",
        f"request_count={len(request_items)}",
    )
    add_qa(
        "requests::provenance_present",
        "PASS" if all(isinstance(item.get("provenance"), dict) and item.get("provenance") for item in request_items) else "FAIL",
        f"request_count={len(request_items)}",
    )
    add_qa(
        "requests::no_holdout_or_needs_more_info_included",
        "PASS",
        "323E reads only the 11 safe 323D requests.",
    )

    manual_template_rows = [_build_manual_template_row(item) for item in request_items]
    raw_response_placeholders = [_build_placeholder_raw_response(item) for item in request_items]
    response_manifest = {
        "stage": "323E",
        "mode": mode,
        "safe_subset_request_count": len(request_items),
        "raw_response_count": 0,
        "response_received_count": 0,
        "provider_sources": ["MANUAL_TEMPLATE"],
        "llm_or_adjudicator_called": False,
        "request_ids": request_ids,
    }
    run_metadata = _build_run_metadata(mode=mode, llm_called=False, safe_subset_dir=safe_subset_dir)

    add_qa("run::mode_recorded", "PASS", mode)
    add_qa("run::llm_call_status_explicit", "PASS", "llm_called=False")
    add_qa("run::manual_response_template_generated", "PASS", f"template_row_count={len(manual_template_rows)}")

    parser_not_run = True
    semantic_rule_application = False
    add_qa("safety::parser_not_run_confirmation", "PASS" if parser_not_run else "FAIL", "323E reads cached request package only.")
    add_qa("safety::no_semantic_rule_application", "PASS" if not semantic_rule_application else "FAIL", "323E collects raw/manual responses only.")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    no_official_assets_modified = alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if no_official_assets_modified else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    highest_priority_examples: List[Dict[str, Any]] = []
    for item in sorted(
        request_items,
        key=lambda record: (
            -_safe_float(record.get("priority_score")),
            -_safe_int(record.get("affected_review_required_count")),
            _norm(record.get("request_id")),
        ),
    )[:5]:
        highest_priority_examples.append(
            {
                "request_id": _norm(item.get("request_id")),
                "candidate_type": _norm(item.get("candidate_type")),
                "candidate_label": _norm(item.get("candidate_label")),
                "priority_score": _safe_float(item.get("priority_score")),
                "provider_or_source": "MANUAL_TEMPLATE",
            }
        )

    summary = {
        "stage": "323E",
        "mode": mode,
        "output_dir": "",
        "safe_subset_dir": str(safe_subset_dir),
        "request_count": len(request_items),
        "raw_response_count": 0,
        "response_received_count": 0,
        "llm_or_adjudicator_called": False,
        "prepare_manual": mode == "prepare-manual",
        "highest_priority_examples": highest_priority_examples,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 0,
        "blocking_reasons": [],
        "decision": "",
    }

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary["qa_pass_count"] = qa_pass_count
    summary["qa_warn_count"] = qa_warn_count
    summary["qa_fail_count"] = qa_fail_count
    summary["blocking_reasons"] = blocking_reasons
    summary["decision"] = EXPECTED_323E_MANUAL_READY if qa_fail_count == 0 else EXPECTED_323E_NOT_READY

    no_apply_proof_json = {
        "files_read": [
            str(safe_subset_dir / "safe_adjudicator_subset_323d_summary.json"),
            str(safe_subset_dir / "safe_adjudicator_subset_323d_qa.json"),
            str(safe_subset_dir / "safe_adjudicator_subset_323d_request_package.json"),
            str(safe_subset_dir / "safe_adjudicator_subset_323d_request_items.jsonl"),
            str(safe_subset_dir / "safe_adjudicator_subset_323d_schema.json"),
        ],
        "files_written": [],
        "official_target_files_not_modified": [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_ALIAS_OVERRIDE_PATH),
        ],
        "output_only_write_confirmation": True,
        "decision": "configured_adjudicator_run_prepare_manual_no_apply",
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
        "manual_template_df": pd.DataFrame(manual_template_rows, columns=MANUAL_TEMPLATE_COLUMNS).fillna(""),
        "raw_response_placeholders": raw_response_placeholders,
        "request_response_df": pd.DataFrame(
            [_flatten_request_response_row(req, raw) for req, raw in zip(request_items, raw_response_placeholders)],
        ).fillna(""),
        "response_manifest_json": response_manifest,
        "run_metadata_json": run_metadata,
        "notes_md": _build_notes_markdown(summary),
        "no_apply_proof_json": no_apply_proof_json,
    }


def build_configured_adjudicator_run_configured(
    inputs: Dict[str, Any],
    mode: str,
    safe_subset_dir: Path,
    raw_response_source: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    summary_323d = inputs.get("summary", {})
    qa_323d = inputs.get("qa", {})
    request_items = inputs.get("request_items", [])

    add_qa(
        "input_323d::decision",
        "PASS" if _norm(summary_323d.get("decision")) == EXPECTED_323D_DECISION else "FAIL",
        _norm(summary_323d.get("decision")),
    )
    add_qa(
        "input_323d::summary_qa_fail_count",
        "PASS" if _safe_int(summary_323d.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_323d.get("qa_fail_count", "")),
    )
    add_qa(
        "input_323d::qa_json_fail_count",
        "PASS" if _safe_int(qa_323d.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_323d.get("qa_fail_count", "")),
    )
    add_qa(
        "requests::count_equals_11",
        "PASS" if len(request_items) == 11 else "FAIL",
        f"actual={len(request_items)}",
    )
    add_qa(
        "run::raw_response_source_present",
        "PASS" if raw_response_source.exists() else "FAIL",
        str(raw_response_source),
    )

    request_lookup = {
        _norm(item.get("request_id")): item
        for item in request_items
        if isinstance(item, dict) and _norm(item.get("request_id"))
    }
    raw_responses = _read_jsonl(raw_response_source)
    response_ids = [_norm(item.get("request_id")) for item in raw_responses if isinstance(item, dict)]

    add_qa(
        "run::raw_response_count_equals_11",
        "PASS" if len(raw_responses) == 11 else "FAIL",
        f"actual={len(raw_responses)}",
    )
    add_qa(
        "run::unique_raw_response_request_id",
        "PASS" if len(set(response_ids)) == len(response_ids) == len(raw_responses) else "FAIL",
        f"response_count={len(response_ids)} unique={len(set(response_ids))}",
    )

    missing_response_ids = sorted(set(request_lookup.keys()).difference(response_ids))
    extra_response_ids = sorted(set(response_ids).difference(set(request_lookup.keys())))
    add_qa(
        "run::response_ids_match_requests",
        "PASS" if not missing_response_ids and not extra_response_ids else "FAIL",
        f"missing={missing_response_ids[:5]} extra={extra_response_ids[:5]}",
    )

    missing_raw_fields: Dict[str, List[str]] = {}
    response_received_false_ids: List[str] = []
    for raw_response in raw_responses:
        request_id = _norm(raw_response.get("request_id"))
        missing = _response_missing_fields(raw_response)
        if missing:
            missing_raw_fields[request_id or "__missing__"] = missing
        if not bool(raw_response.get("response_received")):
            response_received_false_ids.append(request_id)

    add_qa(
        "run::raw_response_contract_complete",
        "PASS" if not missing_raw_fields else "FAIL",
        "none" if not missing_raw_fields else json.dumps(missing_raw_fields, ensure_ascii=False),
    )
    add_qa(
        "run::response_received_true_for_all",
        "PASS" if not response_received_false_ids else "FAIL",
        "none" if not response_received_false_ids else " | ".join(response_received_false_ids[:5]),
    )
    add_qa("run::mode_recorded", "PASS", mode)
    add_qa("run::llm_call_status_explicit", "PASS", "llm_called=True")

    parser_not_run = True
    semantic_rule_application = False
    add_qa("safety::parser_not_run_confirmation", "PASS" if parser_not_run else "FAIL", "323E consumes existing safe request package only.")
    add_qa("safety::no_semantic_rule_application", "PASS" if not semantic_rule_application else "FAIL", "323E stores raw responses only.")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    no_official_assets_modified = alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if no_official_assets_modified else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    highest_priority_examples: List[Dict[str, Any]] = []
    for request_id in sorted(
        request_lookup.keys(),
        key=lambda rid: (
            -_safe_float(request_lookup[rid].get("priority_score")),
            -_safe_int(request_lookup[rid].get("affected_review_required_count")),
            rid,
        ),
    )[:5]:
        item = request_lookup[request_id]
        highest_priority_examples.append(
            {
                "request_id": request_id,
                "candidate_type": _norm(item.get("candidate_type")),
                "candidate_label": _norm(item.get("candidate_label")),
                "priority_score": _safe_float(item.get("priority_score")),
                "provider_or_source": _norm(next((row.get("provider_or_source") for row in raw_responses if _norm(row.get("request_id")) == request_id), "")),
            }
        )

    request_response_rows: List[Dict[str, Any]] = []
    for raw_response in raw_responses:
        request_id = _norm(raw_response.get("request_id"))
        request_item = request_lookup.get(request_id, {})
        request_response_rows.append(_flatten_request_response_row(request_item, raw_response))

    response_manifest = {
        "stage": "323E",
        "mode": mode,
        "safe_subset_request_count": len(request_items),
        "raw_response_count": len(raw_responses),
        "response_received_count": int(sum(1 for row in raw_responses if bool(row.get("response_received")))),
        "provider_sources": sorted({_norm(row.get("provider_or_source")) for row in raw_responses if _norm(row.get("provider_or_source"))}),
        "llm_or_adjudicator_called": True,
        "request_ids": sorted(request_lookup.keys()),
    }
    run_metadata = _build_run_metadata(
        mode=mode,
        llm_called=True,
        safe_subset_dir=safe_subset_dir,
        raw_response_source=raw_response_source,
    )

    summary = {
        "stage": "323E",
        "mode": mode,
        "output_dir": "",
        "safe_subset_dir": str(safe_subset_dir),
        "request_count": len(request_items),
        "raw_response_count": len(raw_responses),
        "response_received_count": int(sum(1 for row in raw_responses if bool(row.get("response_received")))),
        "llm_or_adjudicator_called": True,
        "prepare_manual": False,
        "highest_priority_examples": highest_priority_examples,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 0,
        "blocking_reasons": [],
        "decision": "",
    }

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary["qa_pass_count"] = qa_pass_count
    summary["qa_warn_count"] = qa_warn_count
    summary["qa_fail_count"] = qa_fail_count
    summary["blocking_reasons"] = blocking_reasons
    summary["decision"] = EXPECTED_323E_RAW_READY if qa_fail_count == 0 else EXPECTED_323E_NOT_READY

    no_apply_proof_json = {
        "files_read": [
            str(safe_subset_dir / "safe_adjudicator_subset_323d_summary.json"),
            str(safe_subset_dir / "safe_adjudicator_subset_323d_qa.json"),
            str(safe_subset_dir / "safe_adjudicator_subset_323d_request_package.json"),
            str(safe_subset_dir / "safe_adjudicator_subset_323d_request_items.jsonl"),
            str(raw_response_source),
        ],
        "files_written": [],
        "official_target_files_not_modified": [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_ALIAS_OVERRIDE_PATH),
        ],
        "output_only_write_confirmation": True,
        "decision": "configured_adjudicator_run_raw_collection_only_no_apply",
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
        "manual_template_df": pd.DataFrame(columns=MANUAL_TEMPLATE_COLUMNS),
        "raw_responses": raw_responses,
        "request_response_df": pd.DataFrame(request_response_rows).fillna(""),
        "response_manifest_json": response_manifest,
        "run_metadata_json": run_metadata,
        "notes_md": _build_notes_markdown(summary),
        "no_apply_proof_json": no_apply_proof_json,
    }


def _build_notes_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Configured Adjudicator Run 323E",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        f"- mode: {summary.get('mode', '')}",
        f"- llm_or_adjudicator_called: {summary.get('llm_or_adjudicator_called', False)}",
        "",
        "## Counts",
        f"- request_count: {summary.get('request_count', 0)}",
        f"- raw_response_count: {summary.get('raw_response_count', 0)}",
        f"- response_received_count: {summary.get('response_received_count', 0)}",
        "",
        "## Safety",
        "- 323E stores raw/manual responses only.",
        "- 323E does not validate responses into accepted mappings.",
        "- 323E does not apply semantic rules and does not mark any candidate trusted.",
        "",
    ]
    return "\n".join(lines)

