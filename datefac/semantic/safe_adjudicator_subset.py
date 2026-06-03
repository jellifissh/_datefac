from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set

import pandas as pd


EXPECTED_323C_REVIEWED_DECISION = "ADJUDICATION_BATCH_HUMAN_SPOT_CHECK_323C_REVIEWED_READY_FOR_FINAL_ROUTING"
EXPECTED_323D_PREPARE_DECISION = "SAFE_ADJUDICATOR_SUBSET_323D_PREPARED_READY_FOR_CONFIGURED_ADJUDICATOR_RUN"
EXPECTED_323D_RESPONSE_READY_DECISION = "SAFE_ADJUDICATOR_SUBSET_323D_RESPONSES_READY_FOR_SCHEMA_VALIDATION"
EXPECTED_323D_NOT_READY = "SAFE_ADJUDICATOR_SUBSET_323D_NOT_READY"

DEFAULT_HUMAN_SPOT_CHECK_DIR = Path(r"D:\_datefac\output\adjudication_batch_human_spot_check_323c")
DEFAULT_SANITY_GATE_DIR = Path(r"D:\_datefac\output\adjudication_batch_sanity_gate_323c")
DEFAULT_BATCH_PREP_DIR = Path(r"D:\_datefac\output\semantic_adjudication_batch_prep_323ab")
DEFAULT_CANDIDATE_TEXT_REPAIR_DIR = Path(r"D:\_datefac\output\candidate_text_repair_323ar")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\safe_adjudicator_subset_323d")
DEFAULT_RESPONSE_DIR = Path(r"D:\_datefac\output\safe_adjudicator_subset_323d_responses")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

ALIAS_ALLOWED_RESPONSE_LABELS = [
    "ACCEPT_ALIAS",
    "REJECT_ALIAS",
    "NEEDS_MORE_INFO",
    "OUT_OF_SCOPE",
]

SCOPE_ALLOWED_RESPONSE_LABELS = [
    "ACCEPT_OUT_OF_SCOPE",
    "REJECT_OUT_OF_SCOPE",
    "NEEDS_MORE_INFO",
    "POSSIBLE_CORE_METRIC",
]

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


def build_response_schema(candidate_type: str) -> Dict[str, Any]:
    labels = ALIAS_ALLOWED_RESPONSE_LABELS if candidate_type == "alias" else SCOPE_ALLOWED_RESPONSE_LABELS
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "DateFacSafeAdjudicatorSubsetResponse",
        "type": "object",
        "required": [
            "response_label",
            "confidence",
            "rationale",
            "normalized_target_metric_if_any",
            "safety_flags",
            "needs_human_confirmation",
        ],
        "properties": {
            "response_label": {
                "type": "string",
                "enum": labels,
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
            },
            "rationale": {"type": "string"},
            "normalized_target_metric_if_any": {"type": ["string", "null"]},
            "safety_flags": {
                "type": "array",
                "items": {"type": "string"},
            },
            "needs_human_confirmation": {"type": "boolean"},
        },
        "additionalProperties": False,
    }


def build_prompt_template() -> str:
    return "\n".join(
        [
            "# Safe Adjudicator Subset 323D Prompt Template",
            "",
            "You are the DateFac semantic adjudicator for a safe, pre-filtered subset.",
            "",
            "Rules:",
            "- Do not invent metrics, rule targets, provenance, or evidence.",
            "- Do not mark anything trusted.",
            "- Choose only from the provided allowed_response_labels.",
            "- Keep the rationale concise and evidence-based.",
            "- Flag uncertainty in confidence or safety_flags when context is weak.",
            "- Any accepted suggestion still requires schema validation, deterministic gate, human confirmation, and sandbox replay before any official rule can be considered.",
            "- If the evidence does not support acceptance, choose a non-accept response label.",
            "",
            "Output contract:",
            "- Return JSON only.",
            "- Follow the provided response_schema exactly.",
            "- Set needs_human_confirmation to true for every response.",
            "",
        ]
    )


def _build_request_id(batch_item_id: str) -> str:
    compact = batch_item_id.replace("::", "__")
    return f"323d::{compact}"


def _build_safety_context(item: Dict[str, Any], mode: str) -> Dict[str, Any]:
    candidate_type = _norm(item.get("candidate_type"))
    return {
        "stage": "323D_safe_adjudicator_subset",
        "mode": mode,
        "prepare_only": mode == "prepare",
        "llm_call_allowed_in_this_artifact": False,
        "do_not_apply_rules": True,
        "do_not_mark_trusted": True,
        "requires_schema_validation": True,
        "requires_deterministic_gate": True,
        "requires_human_confirmation": True,
        "requires_sandbox_replay": True,
        "candidate_type_routing_basis": candidate_type,
        "adjudicator_scope": "safe_subset_only",
    }


def _build_request_item(item: Dict[str, Any], mode: str) -> Dict[str, Any]:
    candidate_type = _norm(item.get("candidate_type"))
    allowed_response_labels = ALIAS_ALLOWED_RESPONSE_LABELS if candidate_type == "alias" else SCOPE_ALLOWED_RESPONSE_LABELS
    candidate_label = _norm(item.get("repaired_label")) or _norm(item.get("original_label"))
    request = {
        "request_id": _build_request_id(_norm(item.get("batch_item_id"))),
        "source_batch_item_id": _norm(item.get("batch_item_id")),
        "source_group_id": _norm(item.get("source_group_id")),
        "candidate_type": candidate_type,
        "candidate_label": candidate_label,
        "candidate_question": _norm(item.get("candidate_question")),
        "allowed_response_labels": allowed_response_labels,
        "expected_rule_type_if_accepted": _norm(item.get("expected_rule_type_if_accepted")),
        "sample_candidate_ids": _flatten_sequence(item.get("sample_candidate_ids")),
        "sample_texts": _flatten_sequence(item.get("sample_texts")),
        "affected_candidate_count": _safe_int(item.get("affected_candidate_count")),
        "affected_review_required_count": _safe_int(item.get("affected_review_required_count")),
        "priority_score": _safe_float(item.get("priority_score")),
        "risk_flags": _flatten_sequence(item.get("risk_flags")),
        "provenance": item.get("provenance") if isinstance(item.get("provenance"), dict) else {},
        "safety_context": _build_safety_context(item, mode),
        "response_schema": build_response_schema(candidate_type),
    }
    return request


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


def _flatten_request_item(request_item: Dict[str, Any]) -> Dict[str, Any]:
    provenance = request_item.get("provenance") if isinstance(request_item.get("provenance"), dict) else {}
    safety_context = request_item.get("safety_context") if isinstance(request_item.get("safety_context"), dict) else {}
    return {
        "request_id": _norm(request_item.get("request_id")),
        "source_batch_item_id": _norm(request_item.get("source_batch_item_id")),
        "source_group_id": _norm(request_item.get("source_group_id")),
        "candidate_type": _norm(request_item.get("candidate_type")),
        "candidate_label": _norm(request_item.get("candidate_label")),
        "candidate_question": _norm(request_item.get("candidate_question")),
        "allowed_response_labels": " | ".join(_flatten_sequence(request_item.get("allowed_response_labels"))),
        "expected_rule_type_if_accepted": _norm(request_item.get("expected_rule_type_if_accepted")),
        "sample_candidate_ids": " | ".join(_flatten_sequence(request_item.get("sample_candidate_ids"))),
        "sample_texts": " | ".join(_flatten_sequence(request_item.get("sample_texts"))),
        "affected_candidate_count": _safe_int(request_item.get("affected_candidate_count")),
        "affected_review_required_count": _safe_int(request_item.get("affected_review_required_count")),
        "priority_score": _safe_float(request_item.get("priority_score")),
        "risk_flags": " | ".join(_flatten_sequence(request_item.get("risk_flags"))),
        "provenance_source_stage": _norm(provenance.get("source_stage")),
        "provenance_source_stage_signature": _norm(provenance.get("source_stage_signature")),
        "provenance_source_report_examples": _join_unique(provenance.get("source_report_examples", []), limit=5),
        "provenance_table_asset_examples": _join_unique(provenance.get("table_asset_examples", []), limit=5),
        "provenance_sample_table_titles": _join_unique(provenance.get("sample_table_titles", []), limit=5),
        "provenance_sample_years": _join_unique(provenance.get("sample_years", []), limit=8),
        "provenance_sample_raw_metric_names": _join_unique(provenance.get("sample_raw_metric_names", []), limit=8),
        "prepare_only": bool(safety_context.get("prepare_only")),
        "llm_call_allowed_in_this_artifact": bool(safety_context.get("llm_call_allowed_in_this_artifact")),
        "requires_schema_validation": bool(safety_context.get("requires_schema_validation")),
        "requires_deterministic_gate": bool(safety_context.get("requires_deterministic_gate")),
        "requires_human_confirmation": bool(safety_context.get("requires_human_confirmation")),
        "requires_sandbox_replay": bool(safety_context.get("requires_sandbox_replay")),
    }


def _flatten_excluded_item(item: Dict[str, Any], exclusion_reason: str) -> Dict[str, Any]:
    provenance = item.get("provenance") if isinstance(item.get("provenance"), dict) else {}
    return {
        "batch_item_id": _norm(item.get("batch_item_id")),
        "source_group_id": _norm(item.get("source_group_id")),
        "candidate_type": _norm(item.get("candidate_type")),
        "candidate_label": _norm(item.get("repaired_label")) or _norm(item.get("original_label")),
        "final_route": exclusion_reason,
        "affected_candidate_count": _safe_int(item.get("affected_candidate_count")),
        "affected_review_required_count": _safe_int(item.get("affected_review_required_count")),
        "priority_score": _safe_float(item.get("priority_score")),
        "risk_flags": " | ".join(_flatten_sequence(item.get("risk_flags"))),
        "source_report_examples": _join_unique(provenance.get("source_report_examples", []), limit=5),
        "sample_table_titles": _join_unique(provenance.get("sample_table_titles", []), limit=5),
        "sample_texts": " | ".join(_flatten_sequence(item.get("sample_texts"))),
    }


def load_safe_adjudicator_subset_inputs(
    human_spot_check_dir: Path,
    sanity_gate_dir: Path,
    batch_prep_dir: Path,
    candidate_text_repair_dir: Path,
) -> Dict[str, Any]:
    routing_plan = _read_json(human_spot_check_dir / "adjudication_batch_human_spot_check_323c_final_routing_plan.json")
    reviewed_summary = _read_json(human_spot_check_dir / "adjudication_batch_human_spot_check_323c_reviewed_summary.json")
    reviewed_qa = _read_json(human_spot_check_dir / "adjudication_batch_human_spot_check_323c_reviewed_qa.json")
    gated_batch = _read_json(sanity_gate_dir / "adjudication_batch_sanity_gate_323c_gated_batch.json")
    gated_items = gated_batch.get("batch_items", []) if isinstance(gated_batch.get("batch_items"), list) else []
    batch_prep = _read_json(batch_prep_dir / "semantic_adjudication_batch_prep_323ab_batch.json")
    batch_prep_items = batch_prep.get("batch_items", []) if isinstance(batch_prep.get("batch_items"), list) else []
    return {
        "routing_plan": routing_plan,
        "reviewed_summary": reviewed_summary,
        "reviewed_qa": reviewed_qa,
        "gated_batch": gated_batch,
        "gated_items": gated_items,
        "batch_prep_summary": _read_json(batch_prep_dir / "semantic_adjudication_batch_prep_323ab_summary.json"),
        "batch_prep_items": batch_prep_items,
        "candidate_text_repair_summary": _read_json(candidate_text_repair_dir / "candidate_text_repair_323ar_summary.json"),
    }


def build_safe_adjudicator_subset_prepare(inputs: Dict[str, Any], mode: str = "prepare") -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    reviewed_summary = inputs.get("reviewed_summary", {})
    reviewed_qa = inputs.get("reviewed_qa", {})
    routing_plan = inputs.get("routing_plan", {})
    gated_items = inputs.get("gated_items", [])
    batch_prep_items = inputs.get("batch_prep_items", [])
    candidate_text_repair_summary = inputs.get("candidate_text_repair_summary", {})

    add_qa(
        "input_323c_reviewed::decision",
        "PASS" if _norm(reviewed_summary.get("decision")) == EXPECTED_323C_REVIEWED_DECISION else "FAIL",
        _norm(reviewed_summary.get("decision")),
    )
    add_qa(
        "input_323c_reviewed::summary_qa_fail_count",
        "PASS" if _safe_int(reviewed_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(reviewed_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "input_323c_reviewed::qa_json_fail_count",
        "PASS" if _safe_int(reviewed_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(reviewed_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "input_323c_reviewed::send_to_adjudicator_count",
        "PASS" if _safe_int(reviewed_summary.get("send_to_adjudicator_count")) == 11 else "FAIL",
        str(reviewed_summary.get("send_to_adjudicator_count", "")),
    )
    add_qa(
        "input_323c_reviewed::pending_count_zero",
        "PASS" if _safe_int(reviewed_summary.get("pending_count")) == 0 else "FAIL",
        str(reviewed_summary.get("pending_count", "")),
    )
    add_qa(
        "input_323c_reviewed::invalid_decision_count_zero",
        "PASS" if _safe_int(reviewed_summary.get("invalid_decision_count")) == 0 else "FAIL",
        str(reviewed_summary.get("invalid_decision_count", "")),
    )
    add_qa(
        "input_323ar::reference_loaded",
        "PASS" if bool(candidate_text_repair_summary) else "WARN",
        _norm(candidate_text_repair_summary.get("decision")),
    )

    auto_send_ids = [_norm(value) for value in routing_plan.get("auto_send_batch_item_ids", []) if _norm(value)]
    human_send_ids = [_norm(value) for value in routing_plan.get("human_send_batch_item_ids", []) if _norm(value)]
    holdout_ids = [_norm(value) for value in routing_plan.get("holdout_batch_item_ids", []) if _norm(value)]
    needs_more_info_ids = [_norm(value) for value in routing_plan.get("needs_more_info_batch_item_ids", []) if _norm(value)]
    reclassified_scope_ids = [_norm(value) for value in routing_plan.get("reclassified_scope_candidate_batch_item_ids", []) if _norm(value)]
    reclassified_alias_ids = [_norm(value) for value in routing_plan.get("reclassified_alias_candidate_batch_item_ids", []) if _norm(value)]

    all_routing_ids = auto_send_ids + human_send_ids + holdout_ids + needs_more_info_ids + reclassified_scope_ids + reclassified_alias_ids
    total_preserved_count = len(all_routing_ids)

    add_qa(
        "routing_plan::total_preserved_count",
        "PASS" if total_preserved_count == 34 else "FAIL",
        f"actual={total_preserved_count}",
    )
    add_qa(
        "routing_plan::send_count",
        "PASS" if len(auto_send_ids) + len(human_send_ids) == 11 else "FAIL",
        f"auto_send={len(auto_send_ids)} human_send={len(human_send_ids)}",
    )
    add_qa(
        "routing_plan::holdout_count",
        "PASS" if len(holdout_ids) == 20 else "FAIL",
        f"actual={len(holdout_ids)}",
    )
    add_qa(
        "routing_plan::needs_more_info_count",
        "PASS" if len(needs_more_info_ids) == 3 else "FAIL",
        f"actual={len(needs_more_info_ids)}",
    )
    add_qa(
        "routing_plan::no_reclassified_items",
        "PASS" if not reclassified_scope_ids and not reclassified_alias_ids else "FAIL",
        f"reclass_scope={len(reclassified_scope_ids)} reclass_alias={len(reclassified_alias_ids)}",
    )
    add_qa(
        "routing_plan::unique_batch_item_ids",
        "PASS" if len(set(all_routing_ids)) == total_preserved_count else "FAIL",
        f"unique={len(set(all_routing_ids))} total={total_preserved_count}",
    )

    gated_lookup = {
        _norm(item.get("batch_item_id")): item
        for item in gated_items
        if isinstance(item, dict) and _norm(item.get("batch_item_id"))
    }
    batch_prep_lookup = {
        _norm(item.get("batch_item_id")): item
        for item in batch_prep_items
        if isinstance(item, dict) and _norm(item.get("batch_item_id"))
    }

    subset_ids = auto_send_ids + human_send_ids
    subset_items: List[Dict[str, Any]] = []
    missing_subset_ids: List[str] = []
    for batch_item_id in subset_ids:
        item = gated_lookup.get(batch_item_id) or batch_prep_lookup.get(batch_item_id)
        if not item:
            missing_subset_ids.append(batch_item_id)
            continue
        subset_items.append(item)

    excluded_items: List[Dict[str, Any]] = []
    for batch_item_id in holdout_ids:
        item = gated_lookup.get(batch_item_id) or batch_prep_lookup.get(batch_item_id)
        if item:
            excluded_items.append(item)
    for batch_item_id in needs_more_info_ids:
        item = gated_lookup.get(batch_item_id) or batch_prep_lookup.get(batch_item_id)
        if item:
            excluded_items.append(item)

    add_qa(
        "subset::source_item_lookup_complete",
        "PASS" if not missing_subset_ids else "FAIL",
        "none" if not missing_subset_ids else " | ".join(missing_subset_ids[:5]),
    )

    request_items = [_build_request_item(item, mode=mode) for item in subset_items]
    request_ids = [_norm(item.get("request_id")) for item in request_items]

    invalid_subset_route_ids: List[str] = []
    for item in subset_items:
        batch_item_id = _norm(item.get("batch_item_id"))
        if batch_item_id not in subset_ids:
            invalid_subset_route_ids.append(batch_item_id)

    missing_request_fields: Dict[str, List[str]] = {}
    for item in request_items:
        missing = _request_missing_fields(item)
        if missing:
            missing_request_fields[_norm(item.get("request_id"))] = missing

    unsafe_included_ids: List[str] = []
    for item in subset_items:
        batch_item_id = _norm(item.get("batch_item_id"))
        if batch_item_id in holdout_ids or batch_item_id in needs_more_info_ids or batch_item_id in reclassified_scope_ids or batch_item_id in reclassified_alias_ids:
            unsafe_included_ids.append(batch_item_id)

    add_qa(
        "subset::safe_request_item_count",
        "PASS" if len(request_items) == 11 else "FAIL",
        f"actual={len(request_items)}",
    )
    add_qa(
        "subset::excluded_holdout_count",
        "PASS" if len(holdout_ids) == 20 else "FAIL",
        f"actual={len(holdout_ids)}",
    )
    add_qa(
        "subset::excluded_needs_more_info_count",
        "PASS" if len(needs_more_info_ids) == 3 else "FAIL",
        f"actual={len(needs_more_info_ids)}",
    )
    add_qa(
        "subset::no_unsafe_item_included",
        "PASS" if not unsafe_included_ids and not invalid_subset_route_ids else "FAIL",
        f"unsafe_included={unsafe_included_ids[:5]} invalid_subset_route={invalid_subset_route_ids[:5]}",
    )
    add_qa(
        "requests::unique_request_id",
        "PASS" if len(set(request_ids)) == len(request_ids) == len(request_items) else "FAIL",
        f"request_count={len(request_ids)} unique={len(set(request_ids))}",
    )
    add_qa(
        "requests::schema_completeness",
        "PASS" if not missing_request_fields else "FAIL",
        "none" if not missing_request_fields else json.dumps(missing_request_fields, ensure_ascii=False),
    )
    add_qa(
        "requests::allowed_response_labels_present",
        "PASS" if all(_flatten_sequence(item.get("allowed_response_labels")) for item in request_items) else "FAIL",
        f"request_count={len(request_items)}",
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

    alias_request_count = int(sum(1 for item in request_items if _norm(item.get("candidate_type")) == "alias"))
    scope_request_count = int(sum(1 for item in request_items if _norm(item.get("candidate_type")) == "scope_noise"))

    parser_not_run = True
    llm_called = False
    add_qa("safety::prompt_template_generated", "PASS", "Prepare output includes prompt template for offline/configured review.")
    add_qa("safety::parser_not_run_confirmation", "PASS" if parser_not_run else "FAIL", "323D reads cached outputs only.")
    add_qa("safety::llm_call_status_explicit", "PASS", f"llm_called={llm_called}")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    no_official_assets_modified = alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if no_official_assets_modified else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    highest_priority_request_examples: List[Dict[str, Any]] = []
    for item in sorted(
        request_items,
        key=lambda record: (
            -_safe_float(record.get("priority_score")),
            -_safe_int(record.get("affected_review_required_count")),
            _norm(record.get("request_id")),
        ),
    )[:5]:
        highest_priority_request_examples.append(
            {
                "request_id": _norm(item.get("request_id")),
                "candidate_type": _norm(item.get("candidate_type")),
                "candidate_label": _norm(item.get("candidate_label")),
                "priority_score": _safe_float(item.get("priority_score")),
                "affected_review_required_count": _safe_int(item.get("affected_review_required_count")),
                "allowed_response_labels": _flatten_sequence(item.get("allowed_response_labels")),
            }
        )

    request_items_df = pd.DataFrame([_flatten_request_item(item) for item in request_items]).fillna("")
    excluded_rows: List[Dict[str, Any]] = []
    for item in excluded_items:
        batch_item_id = _norm(item.get("batch_item_id"))
        route = "HOLDOUT" if batch_item_id in holdout_ids else "NEEDS_MORE_INFO"
        excluded_rows.append(_flatten_excluded_item(item, route))
    excluded_items_df = pd.DataFrame(excluded_rows).fillna("")

    summary = {
        "stage": "323D",
        "mode": mode,
        "output_dir": "",
        "prepare_only": mode == "prepare",
        "llm_or_adjudicator_called": llm_called,
        "input_323c_decision": _norm(reviewed_summary.get("decision")),
        "input_batch_count": total_preserved_count,
        "safe_request_item_count": len(request_items),
        "alias_request_count": alias_request_count,
        "scope_request_count": scope_request_count,
        "excluded_holdout_count": len(holdout_ids),
        "excluded_needs_more_info_count": len(needs_more_info_ids),
        "excluded_total_count": len(holdout_ids) + len(needs_more_info_ids),
        "pending_count": _safe_int(reviewed_summary.get("pending_count")),
        "invalid_decision_count": _safe_int(reviewed_summary.get("invalid_decision_count")),
        "highest_priority_request_examples": highest_priority_request_examples,
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
    summary["decision"] = EXPECTED_323D_PREPARE_DECISION if qa_fail_count == 0 else EXPECTED_323D_NOT_READY

    request_package_json = {
        "stage": "323D",
        "mode": mode,
        "decision": summary["decision"],
        "prepare_only": mode == "prepare",
        "llm_or_adjudicator_called": llm_called,
        "request_item_count": len(request_items),
        "request_items": request_items,
    }
    schema_json = {
        "request_required_fields": REQUEST_REQUIRED_FIELDS,
        "alias_allowed_response_labels": ALIAS_ALLOWED_RESPONSE_LABELS,
        "scope_allowed_response_labels": SCOPE_ALLOWED_RESPONSE_LABELS,
        "response_schema_by_candidate_type": {
            "alias": build_response_schema("alias"),
            "scope_noise": build_response_schema("scope_noise"),
        },
    }
    notes_markdown = "\n".join(
        [
            "# Safe Adjudicator Subset 323D",
            "",
            "## Decision",
            f"- decision: {summary['decision']}",
            f"- mode: {mode}",
            f"- prepare_only: {summary['prepare_only']}",
            f"- llm_or_adjudicator_called: {summary['llm_or_adjudicator_called']}",
            "",
            "## Counts",
            f"- input_batch_count: {summary['input_batch_count']}",
            f"- safe_request_item_count: {summary['safe_request_item_count']}",
            f"- alias_request_count: {summary['alias_request_count']}",
            f"- scope_request_count: {summary['scope_request_count']}",
            f"- excluded_holdout_count: {summary['excluded_holdout_count']}",
            f"- excluded_needs_more_info_count: {summary['excluded_needs_more_info_count']}",
            "",
            "## Safety",
            "- This package is request preparation only.",
            "- No semantic rule is applied at this stage.",
            "- No request may mark any candidate trusted.",
            "- Any future response must still pass schema validation, deterministic gate, human confirmation, and sandbox replay.",
            "",
        ]
    )
    no_apply_proof_json = {
        "files_read": [
            str(DEFAULT_HUMAN_SPOT_CHECK_DIR / "adjudication_batch_human_spot_check_323c_final_routing_plan.json"),
            str(DEFAULT_HUMAN_SPOT_CHECK_DIR / "adjudication_batch_human_spot_check_323c_reviewed_summary.json"),
            str(DEFAULT_HUMAN_SPOT_CHECK_DIR / "adjudication_batch_human_spot_check_323c_reviewed_qa.json"),
            str(DEFAULT_SANITY_GATE_DIR / "adjudication_batch_sanity_gate_323c_gated_batch.json"),
            str(DEFAULT_BATCH_PREP_DIR / "semantic_adjudication_batch_prep_323ab_batch.json"),
            str(DEFAULT_CANDIDATE_TEXT_REPAIR_DIR / "candidate_text_repair_323ar_summary.json"),
        ],
        "files_written": [],
        "official_target_files_not_modified": [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_ALIAS_OVERRIDE_PATH),
        ],
        "output_only_write_confirmation": True,
        "decision": "safe_adjudicator_subset_prepare_only_no_apply",
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
        "request_items": request_items,
        "request_items_df": request_items_df,
        "excluded_items_df": excluded_items_df,
        "request_package_json": request_package_json,
        "schema_json": schema_json,
        "prompt_template_md": build_prompt_template(),
        "notes_md": notes_markdown,
        "no_apply_proof_json": no_apply_proof_json,
    }

