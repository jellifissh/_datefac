from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set

import pandas as pd


EXPECTED_324C_DECISION = "SCOPE_NOISE_SAFE_ADJUDICATOR_REQUEST_324C_READY_FOR_MANUAL_OR_CONFIGURED_ADJUDICATOR_RUN"
EXPECTED_324D_MANUAL_READY = "SCOPE_NOISE_ADJUDICATOR_RESPONSE_COLLECTION_324D_MANUAL_TEMPLATE_READY"
EXPECTED_324D_RAW_READY = (
    "SCOPE_NOISE_ADJUDICATOR_RESPONSE_COLLECTION_324D_RAW_RESPONSE_READY_FOR_324E_SCHEMA_VALIDATION"
)
EXPECTED_324D_NOT_READY = "SCOPE_NOISE_ADJUDICATOR_RESPONSE_COLLECTION_324D_NOT_READY"

DEFAULT_REQUEST_DIR = Path(r"D:\_datefac\output\scope_noise_safe_adjudicator_request_324c")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\scope_noise_adjudicator_response_collection_324d")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

RAW_RESPONSE_REQUIRED_FIELDS = [
    "request_id",
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
    "source_scope_review_id",
    "source_refined_scope_candidate_id",
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
    "collector_note",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _exact_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    if isinstance(value, str):
        return value
    return str(value)


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


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _norm(value).lower()
    return text in {"true", "1", "yes", "y"}


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_workbook_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, dtype=object)
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


def _build_manual_template_row(request_item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "request_id": _norm(request_item.get("request_id")),
        "source_scope_review_id": _norm(request_item.get("source_scope_review_id")),
        "source_refined_scope_candidate_id": _norm(request_item.get("source_refined_scope_candidate_id")),
        "candidate_type": _norm(request_item.get("candidate_type")),
        "candidate_label": _norm(request_item.get("candidate_label")),
        "allowed_response_labels": " | ".join(_flatten_sequence(request_item.get("allowed_response_labels"))),
        "candidate_question": _norm(request_item.get("candidate_question")),
        "sample_candidate_ids": " | ".join(_flatten_sequence(request_item.get("sample_candidate_ids"))),
        "sample_texts": " | ".join(_flatten_sequence(request_item.get("sample_texts"))),
        "response_received": False,
        "provider_or_source": "MANUAL_RESPONSE_TEMPLATE",
        "model_or_review_source": "PENDING_MANUAL_RESPONSE",
        "run_timestamp": "",
        "raw_response_text": "",
        "raw_response_json": "",
        "collector_note": "",
    }


def _build_placeholder_raw_response(request_item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "request_id": _norm(request_item.get("request_id")),
        "source_scope_review_id": _norm(request_item.get("source_scope_review_id")),
        "source_refined_scope_candidate_id": _norm(request_item.get("source_refined_scope_candidate_id")),
        "candidate_type": _norm(request_item.get("candidate_type")),
        "candidate_label": _norm(request_item.get("candidate_label")),
        "raw_response_text": "",
        "raw_response_json": "",
        "response_received": False,
        "provider_or_source": "MANUAL_TEMPLATE",
        "model_or_review_source": "NOT_RUN",
        "run_timestamp": "",
        "collector_note": "",
    }


def _flatten_request_response_row(request_item: Dict[str, Any], raw_response: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "request_id": _norm(request_item.get("request_id")),
        "source_scope_review_id": _norm(request_item.get("source_scope_review_id")),
        "source_refined_scope_candidate_id": _norm(request_item.get("source_refined_scope_candidate_id")),
        "candidate_type": _norm(request_item.get("candidate_type")),
        "candidate_label": _norm(request_item.get("candidate_label")),
        "allowed_response_labels": " | ".join(_flatten_sequence(request_item.get("allowed_response_labels"))),
        "candidate_question": _norm(request_item.get("candidate_question")),
        "sample_candidate_ids": " | ".join(_flatten_sequence(request_item.get("sample_candidate_ids"))),
        "sample_texts": " | ".join(_flatten_sequence(request_item.get("sample_texts"))),
        "raw_response_text": _exact_text(raw_response.get("raw_response_text")),
        "raw_response_json": _exact_text(raw_response.get("raw_response_json")),
        "response_received": bool(raw_response.get("response_received")),
        "provider_or_source": _norm(raw_response.get("provider_or_source")),
        "model_or_review_source": _norm(raw_response.get("model_or_review_source")),
        "run_timestamp": _exact_text(raw_response.get("run_timestamp")),
        "collector_note": _exact_text(raw_response.get("collector_note")),
    }


def _build_notes_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Scope Noise Adjudicator Response Collection 324D",
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
            "- 324D stores raw/manual responses only.",
            "- 324D does not validate response schema or deterministic gates.",
            "- 324D does not apply rules and does not produce sandbox replay candidates.",
            "",
        ]
    )


def _build_run_metadata(mode: str, llm_called: bool, request_dir: Path, manual_workbook: Path | None = None) -> Dict[str, Any]:
    return {
        "stage": "324D",
        "mode": mode,
        "llm_or_adjudicator_called": llm_called,
        "request_dir": str(request_dir),
        "manual_response_workbook": str(manual_workbook) if manual_workbook else "",
        "generated_timestamp": datetime.now().isoformat(timespec="seconds"),
        "run_boundary": "raw_response_collection_only",
        "schema_validation_performed": False,
        "deterministic_gate_performed": False,
        "rule_application_performed": False,
        "sandbox_replay_candidate_produced": False,
    }


def load_scope_noise_adjudicator_response_collection_324d_inputs(request_dir: Path) -> Dict[str, Any]:
    request_package = _read_json(request_dir / "scope_noise_safe_adjudicator_request_324c_request_package.json")
    request_items = request_package.get("request_items", []) if isinstance(request_package.get("request_items"), list) else []
    return {
        "summary": _read_json(request_dir / "scope_noise_safe_adjudicator_request_324c_summary.json"),
        "qa": _read_json(request_dir / "scope_noise_safe_adjudicator_request_324c_qa.json"),
        "request_package": request_package,
        "request_items": request_items,
        "schema": _read_json(request_dir / "scope_noise_safe_adjudicator_request_324c_schema.json"),
    }


def build_scope_noise_adjudicator_response_collection_324d_prepare_manual(
    inputs: Dict[str, Any],
    mode: str,
    request_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    summary_324c = inputs.get("summary", {})
    qa_324c = inputs.get("qa", {})
    request_package = inputs.get("request_package", {})
    request_items = [item for item in inputs.get("request_items", []) if isinstance(item, dict)]

    add_qa(
        "input_324c::decision",
        "PASS" if _norm(summary_324c.get("decision")) == EXPECTED_324C_DECISION else "FAIL",
        _norm(summary_324c.get("decision")),
    )
    add_qa(
        "input_324c::summary_qa_fail_count",
        "PASS" if _safe_int(summary_324c.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_324c.get("qa_fail_count", "")),
    )
    add_qa(
        "input_324c::qa_json_fail_count",
        "PASS" if _safe_int(qa_324c.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_324c.get("qa_fail_count", "")),
    )
    add_qa(
        "input_324c::request_count",
        "PASS" if _safe_int(summary_324c.get("request_count")) == 1 else "FAIL",
        str(summary_324c.get("request_count", "")),
    )
    add_qa(
        "input_324c::scope_noise_request_count",
        "PASS" if _safe_int(summary_324c.get("scope_noise_request_count")) == 1 else "FAIL",
        str(summary_324c.get("scope_noise_request_count", "")),
    )
    add_qa(
        "input_324c::llm_not_called",
        "PASS" if not bool(summary_324c.get("llm_or_adjudicator_called")) else "FAIL",
        str(summary_324c.get("llm_or_adjudicator_called")),
    )
    add_qa(
        "request::loaded_single_request",
        "PASS" if len(request_items) == 1 else "FAIL",
        f"actual={len(request_items)}",
    )
    add_qa(
        "request::package_count_matches",
        "PASS" if _safe_int(request_package.get("request_count")) == len(request_items) == 1 else "FAIL",
        f"package_count={request_package.get('request_count', '')} loaded_count={len(request_items)}",
    )

    request_item = request_items[0] if request_items else {}
    add_qa(
        "request::request_id_present",
        "PASS" if _norm(request_item.get("request_id")) else "FAIL",
        _norm(request_item.get("request_id")),
    )
    add_qa(
        "request::candidate_type_scope_noise",
        "PASS" if _norm(request_item.get("candidate_type")) == "scope_noise" else "FAIL",
        _norm(request_item.get("candidate_type")),
    )
    add_qa(
        "request::allowed_response_labels_present",
        "PASS" if _flatten_sequence(request_item.get("allowed_response_labels")) else "FAIL",
        " | ".join(_flatten_sequence(request_item.get("allowed_response_labels"))),
    )
    add_qa(
        "request::sample_evidence_present",
        "PASS"
        if _flatten_sequence(request_item.get("sample_candidate_ids")) and _flatten_sequence(request_item.get("sample_texts"))
        else "FAIL",
        f"sample_candidate_ids={len(_flatten_sequence(request_item.get('sample_candidate_ids')))} sample_texts={len(_flatten_sequence(request_item.get('sample_texts')))}",
    )

    manual_template_rows = [_build_manual_template_row(item) for item in request_items]
    raw_response_placeholders = [_build_placeholder_raw_response(item) for item in request_items]
    response_manifest = {
        "stage": "324D",
        "mode": mode,
        "request_count": len(request_items),
        "raw_response_count": 0,
        "response_received_count": 0,
        "llm_or_adjudicator_called": False,
        "request_ids": [_norm(item.get("request_id")) for item in request_items],
    }
    run_metadata = _build_run_metadata(mode=mode, llm_called=False, request_dir=request_dir)

    add_qa("run::mode_recorded", "PASS", mode)
    add_qa("run::manual_template_generated", "PASS", f"template_row_count={len(manual_template_rows)}")
    add_qa("run::raw_response_count_zero", "PASS", "0")
    add_qa("run::response_received_count_zero", "PASS", "0")
    add_qa("safety::llm_or_adjudicator_not_called", "PASS", "llm_called=False")
    add_qa("safety::no_schema_validation_in_324d", "PASS", "324D does not validate response schema.")
    add_qa("safety::no_deterministic_gate_in_324d", "PASS", "324D does not run deterministic gates.")
    add_qa("safety::no_sandbox_replay_candidate", "PASS", "324D does not produce sandbox replay candidates.")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "324D",
        "mode": mode,
        "output_dir": "",
        "request_count": len(request_items),
        "raw_response_count": 0,
        "response_received_count": 0,
        "llm_or_adjudicator_called": False,
        "collect_manual_mode_implemented": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_324D_MANUAL_READY if qa_fail_count == 0 else EXPECTED_324D_NOT_READY,
    }

    no_apply_proof_json = {
        "files_read": [
            str(request_dir / "scope_noise_safe_adjudicator_request_324c_summary.json"),
            str(request_dir / "scope_noise_safe_adjudicator_request_324c_qa.json"),
            str(request_dir / "scope_noise_safe_adjudicator_request_324c_request_package.json"),
            str(request_dir / "scope_noise_safe_adjudicator_request_324c_schema.json"),
        ],
        "files_written": [],
        "official_target_files_not_modified": [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_ALIAS_OVERRIDE_PATH),
        ],
        "output_only_write_confirmation": True,
        "decision": "scope_noise_adjudicator_response_collection_prepare_manual_no_apply",
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
        "raw_responses": raw_response_placeholders,
        "request_response_df": pd.DataFrame(
            [_flatten_request_response_row(req, raw) for req, raw in zip(request_items, raw_response_placeholders)]
        ).fillna(""),
        "response_manifest_json": response_manifest,
        "run_metadata_json": run_metadata,
        "notes_md": _build_notes_markdown(summary),
        "no_apply_proof_json": no_apply_proof_json,
    }


def build_scope_noise_adjudicator_response_collection_324d_collect_manual(
    inputs: Dict[str, Any],
    mode: str,
    request_dir: Path,
    manual_response_workbook: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    summary_324c = inputs.get("summary", {})
    qa_324c = inputs.get("qa", {})
    request_package = inputs.get("request_package", {})
    request_items = [item for item in inputs.get("request_items", []) if isinstance(item, dict)]

    add_qa(
        "input_324c::decision",
        "PASS" if _norm(summary_324c.get("decision")) == EXPECTED_324C_DECISION else "FAIL",
        _norm(summary_324c.get("decision")),
    )
    add_qa(
        "input_324c::summary_qa_fail_count",
        "PASS" if _safe_int(summary_324c.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_324c.get("qa_fail_count", "")),
    )
    add_qa(
        "input_324c::qa_json_fail_count",
        "PASS" if _safe_int(qa_324c.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_324c.get("qa_fail_count", "")),
    )
    add_qa(
        "request::loaded_single_request",
        "PASS" if len(request_items) == 1 else "FAIL",
        f"actual={len(request_items)}",
    )
    add_qa(
        "request::package_count_matches",
        "PASS" if _safe_int(request_package.get("request_count")) == len(request_items) == 1 else "FAIL",
        f"package_count={request_package.get('request_count', '')} loaded_count={len(request_items)}",
    )
    add_qa(
        "collect::manual_response_workbook_present",
        "PASS" if manual_response_workbook.exists() else "FAIL",
        str(manual_response_workbook),
    )

    template_df = _read_workbook_sheet(manual_response_workbook, "manual_response_template")
    if template_df.empty:
        template_df = _read_workbook_sheet(manual_response_workbook, "request_response_items")
    template_records = template_df.to_dict(orient="records") if not template_df.empty else []

    add_qa(
        "collect::template_record_count",
        "PASS" if len(template_records) == 1 else "FAIL",
        f"actual={len(template_records)}",
    )

    request_item = request_items[0] if request_items else {}
    expected_request_id = _norm(request_item.get("request_id"))
    raw_responses: List[Dict[str, Any]] = []
    response_received_count = 0

    if template_records:
        row = template_records[0]
        actual_request_id = _norm(row.get("request_id"))
        response_received = _truthy(row.get("response_received"))
        raw_response_text = _exact_text(row.get("raw_response_text"))
        raw_response_json = _exact_text(row.get("raw_response_json"))
        payload_present = bool(raw_response_text or raw_response_json)

        add_qa(
            "collect::request_id_alignment",
            "PASS" if actual_request_id == expected_request_id else "FAIL",
            f"expected={expected_request_id} actual={actual_request_id}",
        )
        add_qa(
            "collect::response_received_true",
            "PASS" if response_received else "FAIL",
            str(row.get("response_received")),
        )
        add_qa(
            "collect::raw_response_payload_present",
            "PASS" if payload_present else "FAIL",
            f"raw_response_text_len={len(raw_response_text)} raw_response_json_len={len(raw_response_json)}",
        )

        raw_response = {
            "request_id": actual_request_id,
            "source_scope_review_id": _norm(row.get("source_scope_review_id")) or _norm(request_item.get("source_scope_review_id")),
            "source_refined_scope_candidate_id": _norm(row.get("source_refined_scope_candidate_id"))
            or _norm(request_item.get("source_refined_scope_candidate_id")),
            "candidate_type": _norm(row.get("candidate_type")) or _norm(request_item.get("candidate_type")),
            "candidate_label": _norm(row.get("candidate_label")) or _norm(request_item.get("candidate_label")),
            "raw_response_text": raw_response_text,
            "raw_response_json": raw_response_json,
            "response_received": response_received,
            "provider_or_source": _exact_text(row.get("provider_or_source")),
            "model_or_review_source": _exact_text(row.get("model_or_review_source")),
            "run_timestamp": _exact_text(row.get("run_timestamp")),
            "collector_note": _exact_text(row.get("collector_note")),
        }
        raw_responses.append(raw_response)
        response_received_count = int(response_received)

    add_qa("run::mode_recorded", "PASS", mode)
    add_qa("safety::llm_or_adjudicator_not_called", "PASS", "llm_called=False")
    add_qa("safety::no_schema_validation_in_324d", "PASS", "324D does not validate response schema.")
    add_qa("safety::no_deterministic_gate_in_324d", "PASS", "324D does not run deterministic gates.")
    add_qa("safety::no_sandbox_replay_candidate", "PASS", "324D does not produce sandbox replay candidates.")

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    response_manifest = {
        "stage": "324D",
        "mode": mode,
        "request_count": len(request_items),
        "raw_response_count": len(raw_responses),
        "response_received_count": response_received_count,
        "llm_or_adjudicator_called": False,
        "request_ids": [expected_request_id] if expected_request_id else [],
    }
    run_metadata = _build_run_metadata(
        mode=mode,
        llm_called=False,
        request_dir=request_dir,
        manual_workbook=manual_response_workbook,
    )

    summary = {
        "stage": "324D",
        "mode": mode,
        "output_dir": "",
        "request_count": len(request_items),
        "raw_response_count": len(raw_responses),
        "response_received_count": response_received_count,
        "llm_or_adjudicator_called": False,
        "collect_manual_mode_implemented": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_324D_RAW_READY if qa_fail_count == 0 else EXPECTED_324D_NOT_READY,
    }

    no_apply_proof_json = {
        "files_read": [
            str(request_dir / "scope_noise_safe_adjudicator_request_324c_summary.json"),
            str(request_dir / "scope_noise_safe_adjudicator_request_324c_qa.json"),
            str(request_dir / "scope_noise_safe_adjudicator_request_324c_request_package.json"),
            str(manual_response_workbook),
        ],
        "files_written": [],
        "official_target_files_not_modified": [
            str(FORMAL_SCOPE_RULES_PATH),
            str(OFFICIAL_ALIAS_OVERRIDE_PATH),
        ],
        "output_only_write_confirmation": True,
        "decision": "scope_noise_adjudicator_response_collection_collect_manual_no_apply",
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
        "manual_template_df": template_df.fillna(""),
        "raw_responses": raw_responses,
        "request_response_df": pd.DataFrame(
            [_flatten_request_response_row(request_item, raw_response) for raw_response in raw_responses]
        ).fillna(""),
        "response_manifest_json": response_manifest,
        "run_metadata_json": run_metadata,
        "notes_md": _build_notes_markdown(summary),
        "no_apply_proof_json": no_apply_proof_json,
    }
