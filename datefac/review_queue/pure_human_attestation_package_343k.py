from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.ingest_strict_review_343j import (
    APPLY_MODE,
    FORBIDDEN_STAGE_PATHS,
    NOT_READY_DECISION_343J,
    PROTECTED_DIRTY_PATHS,
    READY_DECISION_343J,
    REVIEW_SOURCE_TYPE,
    SPOT_CHECK_SOURCE_TYPE,
    STRICT_REVIEW_INPUT_SOURCE_TYPE,
)
from datefac.review_queue.source_evidence_enrichment_343i2 import EVIDENCE_LOCATOR_COLUMNS
from datefac.review_queue.strict_human_review_package_343i import REQUIRED_IDENTITY_COLUMNS
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_343K = "PURE_HUMAN_ATTESTATION_PACKAGE_343K_WAITING_FOR_HUMAN_ATTESTATION"
NOT_READY_DECISION_343K = "PURE_HUMAN_ATTESTATION_PACKAGE_343K_NOT_READY"
RECOMMENDED_343L_SCOPE_343K = (
    "pure_human_confirmation_attestation_result_ingestion_after_user_fills_workbook"
)

ALLOWED_HUMAN_ATTESTATION_DECISIONS = [
    "HUMAN_ACCEPT_AI_ASSISTED_CONFIRM",
    "HUMAN_CORRECT",
    "HUMAN_REJECT",
    "HUMAN_NEEDS_SOURCE_CHECK",
    "HUMAN_DEFER",
]

EDITABLE_HUMAN_ATTESTATION_COLUMNS = [
    "human_attestation_decision",
    "human_attested_metric_standardized",
    "human_attested_year_standardized",
    "human_attested_value_numeric",
    "human_attested_normalized_unit",
    "human_attestation_note",
    "human_reviewer_id",
    "human_reviewed_at",
    "human_source_evidence_checked",
    "human_independent_check_attested",
]

HUMAN_CORRECT_REQUIRED_COLUMNS = [
    "human_attested_metric_standardized",
    "human_attested_year_standardized",
    "human_attested_value_numeric",
    "human_attested_normalized_unit",
]

WORKBOOK_SHEETS_343K = [
    "00_README",
    "01_PACKAGE_SUMMARY",
    "02_INPUT_343J_SUMMARY",
    "03_ATTESTATION_ITEMS",
    "04_ATTESTATION_TEMPLATE",
    "05_SOURCE_EVIDENCE",
    "06_ATTESTATION_RULES",
    "07_CLIENT_EXPORT_BOUNDARY",
    "08_IMPORT_CONTRACT",
    "09_343L_READINESS",
    "10_NO_WRITE_BACK",
    "11_NEXT_STEPS",
]

STRICT_REVIEW_RESULT_INGESTION_SUMMARY_NAME = (
    "review_queue_strict_review_ingestion_343j_summary.json"
)
STRICT_REVIEW_RESULT_INGESTION_QA_NAME = "review_queue_strict_review_ingestion_343j_qa.json"
STRICT_REVIEW_RESULT_NAME = "review_queue_strict_review_ingestion_343j_result.jsonl"
STRICT_REVIEW_DECISION_SUMMARY_NAME = (
    "review_queue_strict_review_ingestion_343j_decision_summary.json"
)
STRICT_REVIEW_CLIENT_EXPORT_GATE_NAME = (
    "review_queue_strict_review_ingestion_343j_client_export_gate.json"
)
STRICT_REVIEW_DISCLOSURE_NAME = (
    "review_queue_strict_review_ingestion_343j_reviewer_source_disclosure.md"
)
STRICT_REVIEW_NO_WRITE_BACK_NAME = (
    "review_queue_strict_review_ingestion_343j_no_write_back_proof.json"
)

SOURCE_EVIDENCE_SUMMARY_NAME = "review_queue_source_evidence_enrichment_343i2_summary.json"
SOURCE_EVIDENCE_ITEMS_NAME = (
    "review_queue_source_evidence_enrichment_343i2_enriched_items.jsonl"
)
SOURCE_EVIDENCE_MAP_NAME = (
    "review_queue_source_evidence_enrichment_343i2_evidence_resolution_map.json"
)
SOURCE_EVIDENCE_CONTRACT_NAME = (
    "review_queue_source_evidence_enrichment_343i2_expected_import_contract.json"
)

SCHEMA_SUMMARY_NAME = "review_queue_schema_343a_summary.json"
SCHEMA_FILE_NAME = "review_queue_schema_343a_schema.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _flatten_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return normalize_text(value)


def _build_key_value_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    rows = [{"key": key, "value": _flatten_value(value)} for key, value in mapping.items()]
    return _clean_frame(pd.DataFrame(rows))


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _is_git_repo(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def _run_git(repo_root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git_status_porcelain_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = _run_git(repo_root, ["status", "--porcelain", "--", *paths])
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_staged_names_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    lines = _git_status_porcelain_for_paths(paths, repo_root)
    staged: List[str] = []
    for line in lines:
        if line.startswith("__ERROR__::"):
            return [line]
        if len(line) >= 3 and line[0] in {"A", "M", "D", "R", "C", "U", "T"}:
            staged.append(line[3:].strip())
    return staged


def _readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "343K packages AI-assisted strict-confirm rows into a pure-human confirmation attestation workbook.",
                },
                {
                    "section": "boundary",
                    "message": "343K does not ingest human attestation results and does not allow formal client export.",
                },
                {
                    "section": "reviewer_expectation",
                    "message": "The human reviewer must independently inspect source evidence, not merely approve the AI-assisted strict confirm.",
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def _merge_source_evidence_fields(
    row_343j: Dict[str, Any],
    *,
    item_343i2: Dict[str, Any] | None,
) -> Dict[str, Any]:
    merged = dict(row_343j)
    source_item = item_343i2 or {}
    for field in EVIDENCE_LOCATOR_COLUMNS:
        if normalize_text(merged.get(field)) == "":
            merged[field] = source_item.get(field, "")
    return merged


def build_attestation_item(
    row_343j: Dict[str, Any],
    *,
    item_343i2: Dict[str, Any] | None,
) -> Dict[str, Any]:
    item = _merge_source_evidence_fields(row_343j, item_343i2=item_343i2)
    for field in EDITABLE_HUMAN_ATTESTATION_COLUMNS:
        item[field] = ""
    item["pure_human_attestation_result_ingested"] = False
    item["waiting_for_pure_human_attestation"] = True
    item["pure_strict_human_review_completed"] = False
    item["strict_human_review_completed"] = False
    item["requires_pure_human_confirmation"] = True
    item["formal_client_export_allowed"] = False
    item["client_ready"] = False
    item["production_ready"] = False
    item["strict_human_confirmation_available"] = False
    item["pure_human_attestation_scope_note"] = (
        "AI-assisted strict confirm only; independent human confirmation is still required."
    )
    return item


def build_attestation_rules_rows() -> List[Dict[str, str]]:
    return [
        {
            "human_attestation_decision": "HUMAN_ACCEPT_AI_ASSISTED_CONFIRM",
            "when_to_use": "Human reviewer independently verifies the source evidence and accepts the AI-assisted strict confirm.",
            "required_fields": "human_reviewer_id, human_reviewed_at, human_source_evidence_checked=true, human_independent_check_attested=true",
        },
        {
            "human_attestation_decision": "HUMAN_CORRECT",
            "when_to_use": "Human reviewer confirms the row only after entering corrected metric/year/value/unit.",
            "required_fields": "corrected metric/year/value/unit, human_attestation_note, human_reviewer_id, human_reviewed_at, human_source_evidence_checked=true",
        },
        {
            "human_attestation_decision": "HUMAN_REJECT",
            "when_to_use": "Human reviewer rejects the AI-assisted strict confirm after checking source evidence.",
            "required_fields": "human_attestation_note, human_reviewer_id, human_reviewed_at, human_source_evidence_checked=true",
        },
        {
            "human_attestation_decision": "HUMAN_NEEDS_SOURCE_CHECK",
            "when_to_use": "Human reviewer still cannot verify the row from the currently available evidence package.",
            "required_fields": "human_attestation_note, human_reviewer_id, human_reviewed_at",
        },
        {
            "human_attestation_decision": "HUMAN_DEFER",
            "when_to_use": "Human reviewer intentionally defers the row for a later pure-human batch.",
            "required_fields": "human_reviewer_id, human_reviewed_at, human_attestation_note when possible",
        },
    ]


def build_boundary_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "strict_review_input_source_type": summary.get(
                "strict_review_input_source_type",
                STRICT_REVIEW_INPUT_SOURCE_TYPE,
            ),
            "review_source_type": summary.get("review_source_type", REVIEW_SOURCE_TYPE),
            "spot_check_source_type": summary.get(
                "spot_check_source_type",
                SPOT_CHECK_SOURCE_TYPE,
            ),
            "apply_mode": summary.get("apply_mode", APPLY_MODE),
            "pure_strict_human_review_completed": summary.get(
                "pure_strict_human_review_completed",
                False,
            ),
            "strict_human_review_completed": summary.get(
                "strict_human_review_completed",
                False,
            ),
            "requires_pure_human_confirmation": summary.get(
                "requires_pure_human_confirmation",
                True,
            ),
            "formal_client_export_allowed": summary.get(
                "formal_client_export_allowed",
                False,
            ),
            "client_ready": summary.get("client_ready", False),
            "production_ready": summary.get("production_ready", False),
            "boundary_note": "343K generates a fillable pure-human attestation package only. No attestation result is imported yet.",
        }
    ]


def build_readiness_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "gate": "pure_human_attestation_package_generated",
            "value": summary.get("pure_human_attestation_package_generated", False),
            "meaning": "The main 343K workbook and package artifacts were generated.",
        },
        {
            "gate": "attestation_template_generated",
            "value": summary.get("attestation_template_generated", False),
            "meaning": "A dedicated fillable attestation workbook exists for the reviewer.",
        },
        {
            "gate": "waiting_for_pure_human_attestation",
            "value": summary.get("waiting_for_pure_human_attestation", False),
            "meaning": "343K intentionally stops before any human result ingestion.",
        },
        {
            "gate": "pure_human_attestation_result_ingested",
            "value": summary.get("pure_human_attestation_result_ingested", False),
            "meaning": "Must remain false until 343L.",
        },
        {
            "gate": "ready_for_343l",
            "value": summary.get("ready_for_343l", False),
            "meaning": "Should remain false until the user fills the workbook and a later ingestion task runs.",
        },
        {
            "gate": "recommended_343l_scope",
            "value": summary.get("recommended_343l_scope", ""),
            "meaning": "Expected next ingestion scope after the user fills the pure-human attestation workbook.",
        },
    ]


def build_next_steps_rows() -> List[Dict[str, str]]:
    return [
        {
            "step": "open_attestation_template",
            "recommendation": "Open the dedicated pure-human attestation template workbook first.",
        },
        {
            "step": "independently_check_source_evidence",
            "recommendation": "Use source_pdf_name, page_number, table_id, bbox, image_path, source_text_snippet, and source_html_snippet before deciding.",
        },
        {
            "step": "fill_only_human_attestation_columns",
            "recommendation": "Do not edit row identity or upstream evidence fields; fill only the human_* attestation columns.",
        },
        {
            "step": "save_for_343l_ingestion",
            "recommendation": "Save the filled workbook under D:/_datefac/input/review_queue_pure_human_attestation_343k_filled/ for later 343L ingestion.",
        },
    ]


def attestation_decisions_blank(rows: Iterable[Dict[str, Any]]) -> bool:
    for row in rows:
        if any(normalize_text(row.get(field)) for field in EDITABLE_HUMAN_ATTESTATION_COLUMNS):
            return False
    return True


def build_expected_import_contract(
    *,
    review_queue_schema_version: str,
    output_dir_hint: str,
) -> Dict[str, Any]:
    return {
        "contract_version": "343K.pure_human_attestation_package.v1",
        "source_review_queue_schema_version": review_queue_schema_version,
        "required_sheet_name": "04_ATTESTATION_TEMPLATE",
        "required_identity_columns": REQUIRED_IDENTITY_COLUMNS,
        "source_evidence_columns": EVIDENCE_LOCATOR_COLUMNS,
        "editable_human_attestation_columns": EDITABLE_HUMAN_ATTESTATION_COLUMNS,
        "allowed_human_attestation_decisions": ALLOWED_HUMAN_ATTESTATION_DECISIONS,
        "human_correct_required_columns": HUMAN_CORRECT_REQUIRED_COLUMNS,
        "expected_input_path_pattern": "D:/_datefac/input/review_queue_pure_human_attestation_343k_filled/*.xlsx",
        "waiting_for_pure_human_attestation": True,
        "pure_human_attestation_result_ingested": False,
        "recommended_output_dir_hint": output_dir_hint,
        "validation_rules": [
            "identity columns must remain unchanged for 343L row matching",
            "human_attestation_decision must be one of the allowed HUMAN_* decisions when filled",
            "HUMAN_ACCEPT_AI_ASSISTED_CONFIRM requires human_source_evidence_checked=true and human_independent_check_attested=true",
            "HUMAN_CORRECT requires corrected metric/year/value/unit plus note and reviewer/date",
            "formal_client_export_allowed/client_ready/production_ready must remain false",
            "pure_strict_human_review_completed and strict_human_review_completed must remain false at 343K",
        ],
    }


def _build_source_evidence_rows(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in items:
        row = {
            "queue_item_id": normalize_text(item.get("queue_item_id")),
            "review_item_id": normalize_text(item.get("review_item_id")),
        }
        for field in EVIDENCE_LOCATOR_COLUMNS:
            row[field] = item.get(field, "")
        rows.append(row)
    return rows


def _build_client_export_boundary_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 343K Client Export Boundary",
            "",
            "## 中文说明",
            "- 343K 仅生成 pure human confirmation attestation package，不导入 attestation 结果。",
            "- 当前 10 条行仍然来自 AI-assisted strict confirm，不是纯人工最终确认。",
            "- formal client export 仍然禁止，client_ready / production_ready 必须保持 false。",
            "",
            "## English Note",
            "- 343K only prepares a pure-human attestation package and does not ingest attestation results yet.",
            "- The current rows remain AI-assisted strict-confirm rows until an actual human attestation result is ingested later.",
            "",
            "## Current Gate",
            f"- formal_client_export_allowed: {summary.get('formal_client_export_allowed', False)}",
            f"- client_ready: {summary.get('client_ready', False)}",
            f"- production_ready: {summary.get('production_ready', False)}",
            f"- pure_strict_human_review_completed: {summary.get('pure_strict_human_review_completed', False)}",
            f"- strict_human_review_completed: {summary.get('strict_human_review_completed', False)}",
            f"- ready_for_343l: {summary.get('ready_for_343l', False)}",
        ]
    )


def build_review_queue_pure_human_attestation_package_343k(
    *,
    strict_review_ingestion_343j_dir: Path,
    source_evidence_enrichment_343i2_dir: Path,
    review_queue_schema_343a_dir: Path,
    output_dir: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    alias_asset_path = SEMANTIC_ALIAS_ASSET_PATH
    scope_asset_path = FORMAL_SCOPE_RULES_PATH
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_343j_path = strict_review_ingestion_343j_dir / STRICT_REVIEW_RESULT_INGESTION_SUMMARY_NAME
    qa_343j_path = strict_review_ingestion_343j_dir / STRICT_REVIEW_RESULT_INGESTION_QA_NAME
    result_343j_path = strict_review_ingestion_343j_dir / STRICT_REVIEW_RESULT_NAME
    decision_summary_343j_path = strict_review_ingestion_343j_dir / STRICT_REVIEW_DECISION_SUMMARY_NAME
    client_export_gate_343j_path = strict_review_ingestion_343j_dir / STRICT_REVIEW_CLIENT_EXPORT_GATE_NAME
    disclosure_343j_path = strict_review_ingestion_343j_dir / STRICT_REVIEW_DISCLOSURE_NAME
    no_write_back_343j_path = strict_review_ingestion_343j_dir / STRICT_REVIEW_NO_WRITE_BACK_NAME

    summary_343i2_path = source_evidence_enrichment_343i2_dir / SOURCE_EVIDENCE_SUMMARY_NAME
    items_343i2_path = source_evidence_enrichment_343i2_dir / SOURCE_EVIDENCE_ITEMS_NAME
    map_343i2_path = source_evidence_enrichment_343i2_dir / SOURCE_EVIDENCE_MAP_NAME
    contract_343i2_path = source_evidence_enrichment_343i2_dir / SOURCE_EVIDENCE_CONTRACT_NAME

    summary_343a_path = review_queue_schema_343a_dir / SCHEMA_SUMMARY_NAME
    schema_343a_path = review_queue_schema_343a_dir / SCHEMA_FILE_NAME

    input_paths = [
        summary_343j_path,
        qa_343j_path,
        result_343j_path,
        decision_summary_343j_path,
        client_export_gate_343j_path,
        disclosure_343j_path,
        no_write_back_343j_path,
        summary_343i2_path,
        items_343i2_path,
        map_343i2_path,
        contract_343i2_path,
        summary_343a_path,
        schema_343a_path,
    ]

    files_read: List[str] = []
    warnings: List[str] = []
    missing_required_inputs: List[str] = []
    for path in input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            missing_required_inputs.append(str(path))

    summary_343j = _read_json(summary_343j_path) if summary_343j_path.exists() else {}
    qa_343j = _read_json(qa_343j_path) if qa_343j_path.exists() else {}
    result_rows_343j = _read_jsonl(result_343j_path) if result_343j_path.exists() else []
    decision_summary_343j = _read_json(decision_summary_343j_path) if decision_summary_343j_path.exists() else {}
    client_export_gate_343j = _read_json(client_export_gate_343j_path) if client_export_gate_343j_path.exists() else {}
    summary_343i2 = _read_json(summary_343i2_path) if summary_343i2_path.exists() else {}
    items_343i2 = _read_jsonl(items_343i2_path) if items_343i2_path.exists() else []
    resolution_map_343i2 = _read_json(map_343i2_path) if map_343i2_path.exists() else {}
    schema_343a = _read_json(summary_343a_path) if summary_343a_path.exists() else {}

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    input_ready = bool(
        not missing_required_inputs
        and summary_343j.get("decision") == READY_DECISION_343J
        and bool(summary_343j.get("ready_for_343k"))
        and int(summary_343j.get("qa_fail_count", 1)) == 0
        and int(summary_343j.get("strict_confirm_count", -1)) >= 1
        and int(summary_343j.get("valid_row_count", -1)) == int(summary_343j.get("filled_row_count", -2))
        and int(summary_343j.get("invalid_row_count", -1)) == 0
        and normalize_text(summary_343j.get("strict_review_input_source_type"))
        == STRICT_REVIEW_INPUT_SOURCE_TYPE
        and normalize_text(summary_343j.get("review_source_type")) == REVIEW_SOURCE_TYPE
        and normalize_text(summary_343j.get("spot_check_source_type")) == SPOT_CHECK_SOURCE_TYPE
        and normalize_text(summary_343j.get("apply_mode")) == APPLY_MODE
        and normalize_bool(summary_343j.get("not_pure_human_review"))
        and not normalize_bool(summary_343j.get("pure_strict_human_review_completed"))
        and not normalize_bool(summary_343j.get("strict_human_review_completed"))
        and normalize_bool(summary_343j.get("requires_pure_human_confirmation"))
        and not normalize_bool(summary_343j.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343j.get("client_ready"))
        and not normalize_bool(summary_343j.get("production_ready"))
        and not normalize_bool(client_export_gate_343j.get("formal_client_export_allowed"))
    )

    items_343i2_by_pair = {
        (
            normalize_text(item.get("queue_item_id")),
            normalize_text(item.get("review_item_id")),
        ): item
        for item in items_343i2
    }

    strict_confirm_rows = [
        row
        for row in result_rows_343j
        if normalize_text(row.get("strict_review_decision")) == "STRICT_CONFIRM"
        and normalize_text(row.get("strict_review_input_source_type"))
        == STRICT_REVIEW_INPUT_SOURCE_TYPE
        and normalize_bool(row.get("not_pure_human_review"))
        and normalize_bool(row.get("requires_pure_human_confirmation"))
    ]

    attestation_items = [
        build_attestation_item(
            row,
            item_343i2=items_343i2_by_pair.get(
                (
                    normalize_text(row.get("queue_item_id")),
                    normalize_text(row.get("review_item_id")),
                )
            ),
        )
        for row in strict_confirm_rows
    ]

    expected_count = int(summary_343j.get("strict_confirm_count", -1))
    evidence_resolved_count = sum(
        1
        for item in attestation_items
        if normalize_text(item.get("evidence_resolution_status")) == "RESOLVED"
    )
    source_pdf_name_available_count = sum(
        1 for item in attestation_items if normalize_text(item.get("source_pdf_name")) != ""
    )
    source_text_snippet_available_count = sum(
        1
        for item in attestation_items
        if normalize_text(item.get("source_text_snippet")) != ""
    )

    expected_import_contract = build_expected_import_contract(
        review_queue_schema_version=summary_343j.get(
            "review_queue_schema_version",
            schema_343a.get("review_queue_schema_version", ""),
        ),
        output_dir_hint=str(output_dir),
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343J",
        "decision": NOT_READY_DECISION_343K,
        "review_queue_schema_version": summary_343j.get(
            "review_queue_schema_version",
            schema_343a.get("review_queue_schema_version", ""),
        ),
        "input_ai_assisted_strict_review_confirm_count": int(
            summary_343j.get("strict_confirm_count", 0)
        ),
        "attestation_item_count": len(attestation_items),
        "evidence_resolved_count": evidence_resolved_count,
        "source_pdf_name_available_count": source_pdf_name_available_count,
        "source_text_snippet_available_count": source_text_snippet_available_count,
        "pure_human_attestation_package_generated": bool(attestation_items),
        "attestation_template_generated": bool(attestation_items),
        "reviewer_instructions_generated": True,
        "fill_guide_generated": True,
        "expected_import_contract_generated": True,
        "waiting_for_pure_human_attestation": True,
        "pure_human_attestation_result_ingested": False,
        "pure_strict_human_confirm_count": 0,
        "ai_assisted_strict_review_confirm_count": int(
            summary_343j.get("strict_confirm_count", 0)
        ),
        "strict_review_input_source_type": STRICT_REVIEW_INPUT_SOURCE_TYPE,
        "review_source_type": REVIEW_SOURCE_TYPE,
        "spot_check_source_type": SPOT_CHECK_SOURCE_TYPE,
        "apply_mode": APPLY_MODE,
        "not_pure_human_review": True,
        "pure_strict_human_review_completed": False,
        "strict_human_review_completed": False,
        "requires_pure_human_confirmation": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343l": False,
        "recommended_343l_scope": RECOMMENDED_343L_SCOPE_343K,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "output_directory": str(output_dir),
    }

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="343K",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["pure_human_attestation_result_ingested"] = False
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["real_production_apply_performed"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343k")
        and upstream_unchanged
        and not no_write_back_json.get("pure_human_attestation_result_ingested", True)
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    editable_columns_exist = bool(
        attestation_items
        and all(
            column in attestation_items[0] for column in EDITABLE_HUMAN_ATTESTATION_COLUMNS
        )
    )
    decisions_blank = attestation_decisions_blank(attestation_items)
    evidence_locator_preserved = all(
        any(normalize_text(item.get(field)) != "" for field in EVIDENCE_LOCATOR_COLUMNS)
        for item in attestation_items
    )
    strict_confirm_only = all(
        normalize_text(item.get("strict_review_decision")) == "STRICT_CONFIRM"
        for item in attestation_items
    )

    checks = [
        {
            "check_name": "inputs::343j_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "missing_required_inputs": missing_required_inputs,
                    "decision": summary_343j.get("decision", ""),
                    "ready_for_343k": summary_343j.get("ready_for_343k", False),
                    "qa_fail_count": summary_343j.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::343j_disclosure_confirms_ai_assisted_evidence_check",
            "status": "PASS"
            if normalize_text(summary_343j.get("strict_review_input_source_type"))
            == STRICT_REVIEW_INPUT_SOURCE_TYPE
            and normalize_bool(summary_343j.get("not_pure_human_review"))
            and normalize_bool(summary_343j.get("requires_pure_human_confirmation"))
            else "FAIL",
            "detail": STRICT_REVIEW_INPUT_SOURCE_TYPE,
        },
        {
            "check_name": "counts::ai_assisted_strict_confirm_rows_carried_forward",
            "status": "PASS" if len(attestation_items) == expected_count else "FAIL",
            "detail": json.dumps(
                {"attestation_item_count": len(attestation_items), "expected": expected_count},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "rows::strict_confirm_rows_only",
            "status": "PASS" if strict_confirm_only else "FAIL",
            "detail": "Only STRICT_CONFIRM rows from 343J may enter 343K.",
        },
        {
            "check_name": "evidence::source_locator_fields_preserved",
            "status": "PASS" if evidence_locator_preserved else "FAIL",
            "detail": json.dumps(EVIDENCE_LOCATOR_COLUMNS, ensure_ascii=False),
        },
        {
            "check_name": "outputs::attestation_template_generated",
            "status": "PASS" if summary["attestation_template_generated"] else "FAIL",
            "detail": "review_queue_pure_human_attestation_package_343k_attestation_template.xlsx",
        },
        {
            "check_name": "outputs::reviewer_instructions_generated",
            "status": "PASS" if summary["reviewer_instructions_generated"] else "FAIL",
            "detail": "review_queue_pure_human_attestation_package_343k_reviewer_instructions.md",
        },
        {
            "check_name": "outputs::fill_guide_generated",
            "status": "PASS" if summary["fill_guide_generated"] else "FAIL",
            "detail": "review_queue_pure_human_attestation_package_343k_fill_guide.md",
        },
        {
            "check_name": "outputs::expected_import_contract_generated",
            "status": "PASS" if summary["expected_import_contract_generated"] else "FAIL",
            "detail": "review_queue_pure_human_attestation_package_343k_expected_import_contract.json",
        },
        {
            "check_name": "schema::editable_attestation_columns_exist",
            "status": "PASS" if editable_columns_exist else "FAIL",
            "detail": json.dumps(EDITABLE_HUMAN_ATTESTATION_COLUMNS, ensure_ascii=False),
        },
        {
            "check_name": "schema::allowed_human_decision_list_present",
            "status": "PASS" if bool(ALLOWED_HUMAN_ATTESTATION_DECISIONS) else "FAIL",
            "detail": json.dumps(ALLOWED_HUMAN_ATTESTATION_DECISIONS, ensure_ascii=False),
        },
        {
            "check_name": "state::human_attestation_decisions_not_prefilled",
            "status": "PASS" if decisions_blank else "FAIL",
            "detail": "All human_* attestation columns must remain blank in 343K outputs.",
        },
        {
            "check_name": "state::waiting_for_pure_human_attestation_true",
            "status": "PASS" if summary["waiting_for_pure_human_attestation"] else "FAIL",
            "detail": str(summary["waiting_for_pure_human_attestation"]),
        },
        {
            "check_name": "state::pure_human_attestation_result_not_ingested",
            "status": "PASS"
            if not summary["pure_human_attestation_result_ingested"]
            else "FAIL",
            "detail": str(summary["pure_human_attestation_result_ingested"]),
        },
        {
            "check_name": "claims::pure_strict_human_review_not_claimed_complete",
            "status": "PASS"
            if not summary["pure_strict_human_review_completed"]
            and not summary["strict_human_review_completed"]
            else "FAIL",
            "detail": "pure_strict_human_review_completed and strict_human_review_completed must remain false",
        },
        {
            "check_name": "claims::no_formal_client_or_production_ready_true",
            "status": "PASS"
            if not summary["formal_client_export_allowed"]
            and not summary["client_ready"]
            and not summary["production_ready"]
            else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready must remain false",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "343K is package generation only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "343K does not write back or perform production apply.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343K adds review-queue sidecar files only.",
        },
        {
            "check_name": "safety::protected_dirty_status_preserved",
            "status": "PASS" if protected_before == protected_after else "FAIL",
            "detail": json.dumps(protected_after, ensure_ascii=False),
        },
        {
            "check_name": "safety::protected_dirty_files_not_staged",
            "status": "PASS" if not protected_staged else "FAIL",
            "detail": json.dumps(protected_staged, ensure_ascii=False),
        },
        {
            "check_name": "safety::forbidden_output_or_input_artifacts_not_staged",
            "status": "PASS" if not forbidden_staged else "FAIL",
            "detail": json.dumps(forbidden_staged, ensure_ascii=False),
        },
        {
            "check_name": "safety::sheet_names_within_limit",
            "status": "PASS" if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_343K) else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_343K, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps(
                {"no_write_back_proof_passed": no_write_back_proof_passed},
                ensure_ascii=False,
            ),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    ready_for_user_attestation = bool(
        input_ready
        and len(attestation_items) == expected_count
        and strict_confirm_only
        and editable_columns_exist
        and decisions_blank
        and no_write_back_proof_passed
        and qa_fail_count == 0
    )

    summary["decision"] = READY_DECISION_343K if ready_for_user_attestation else NOT_READY_DECISION_343K
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    reviewer_instructions_md = "\n".join(
        [
            "# 343K Pure Human Confirmation Reviewer Instructions",
            "",
            "## 中文说明",
            "- 这 10 条当前是 AI-assisted strict confirm，不是纯人工最终确认。",
            "- 审核人必须独立查看源证据，再填写 human_attestation_decision，不能直接照抄 AI-assisted 结果。",
            "- 请优先结合 `source_pdf_name / page_number / table_id / bbox / image_path / source_text_snippet / source_html_snippet` 做判断。",
            "- 只填写 `human_*` 列，不要修改 identity 或 source evidence 列。",
            "",
            "## Decision Guide",
            "- `HUMAN_ACCEPT_AI_ASSISTED_CONFIRM`: 已独立核对证据并接受当前 strict confirm。",
            "- `HUMAN_CORRECT`: 需要人工修正 metric/year/value/unit 后才能接受。",
            "- `HUMAN_REJECT`: 人工检查后拒绝该行。",
            "- `HUMAN_NEEDS_SOURCE_CHECK`: 当前证据仍不足，需要继续查源。",
            "- `HUMAN_DEFER`: 暂缓到后续纯人工批次。",
            "",
            "## Mandatory Fields",
            "- `HUMAN_ACCEPT_AI_ASSISTED_CONFIRM` 需要 `human_reviewer_id`、`human_reviewed_at`、`human_source_evidence_checked=true`、`human_independent_check_attested=true`。",
            "- `HUMAN_CORRECT` 需要 corrected metric/year/value/unit、`human_attestation_note`、`human_reviewer_id`、`human_reviewed_at`。",
            "- `HUMAN_REJECT` / `HUMAN_NEEDS_SOURCE_CHECK` 需要 `human_attestation_note`、`human_reviewer_id`、`human_reviewed_at`。",
            "",
            "## English Note",
            "- The reviewer must independently inspect source evidence before accepting, correcting, or rejecting any row.",
            "- These 10 rows remain AI-assisted strict-confirm rows until a later attestation result is ingested.",
            "",
            "## Save Path",
            "- 请把填写后的 workbook 保存到 `D:/_datefac/input/review_queue_pure_human_attestation_343k_filled/`，供后续 343L ingestion 使用。",
        ]
    )

    fill_guide_md = "\n".join(
        [
            "# 343K Fill Guide",
            "",
            "1. 打开 `review_queue_pure_human_attestation_package_343k_attestation_template.xlsx`。",
            "2. 先读 `source_pdf_name`、`page_number`、`table_id`、`bbox`、`image_path`、`source_text_snippet`、`source_html_snippet`。",
            "3. 只填写 `human_*` 列。",
            "4. 若选择 `HUMAN_ACCEPT_AI_ASSISTED_CONFIRM`，必须把 `human_source_evidence_checked` 和 `human_independent_check_attested` 填成 `true`。",
            "5. 若选择 `HUMAN_CORRECT`，必须补全 `human_attested_metric_standardized`、`human_attested_year_standardized`、`human_attested_value_numeric`、`human_attested_normalized_unit` 并写明 `human_attestation_note`。",
            "6. 不要把 343K 视为 formal client export 或生产可用结果。",
            "7. 填写后留给后续 343L 做结果导入；343K 本身不会导入任何 attestation 结果。",
        ]
    )

    manifest = {
        "task": "343K_pure_human_confirmation_attestation_package_for_ai_assisted_strict_confirmed_rows",
        "strict_review_ingestion_343j_dir": str(strict_review_ingestion_343j_dir),
        "source_evidence_enrichment_343i2_dir": str(source_evidence_enrichment_343i2_dir),
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "review_queue_pure_human_attestation_package_343k_summary.json"),
            "manifest_json": str(output_dir / "review_queue_pure_human_attestation_package_343k_manifest.json"),
            "qa_json": str(output_dir / "review_queue_pure_human_attestation_package_343k_qa.json"),
            "no_write_back_proof_json": str(output_dir / "review_queue_pure_human_attestation_package_343k_no_write_back_proof.json"),
            "report_md": str(output_dir / "review_queue_pure_human_attestation_package_343k_report.md"),
            "workbook_xlsx": str(output_dir / "review_queue_pure_human_attestation_package_343k.xlsx"),
            "attestation_template_xlsx": str(output_dir / "review_queue_pure_human_attestation_package_343k_attestation_template.xlsx"),
            "attestation_items_jsonl": str(output_dir / "review_queue_pure_human_attestation_package_343k_attestation_items.jsonl"),
            "reviewer_instructions_md": str(output_dir / "review_queue_pure_human_attestation_package_343k_reviewer_instructions.md"),
            "fill_guide_md": str(output_dir / "review_queue_pure_human_attestation_package_343k_fill_guide.md"),
            "expected_import_contract_json": str(output_dir / "review_queue_pure_human_attestation_package_343k_expected_import_contract.json"),
            "client_export_boundary_md": str(output_dir / "review_queue_pure_human_attestation_package_343k_client_export_boundary.md"),
        },
        "files_read": list(files_read),
        "warnings": warnings,
        "decision_summary_343j": decision_summary_343j,
        "resolution_map_343i2": resolution_map_343i2,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    attestation_df = _clean_frame(pd.DataFrame(attestation_items))
    workbook_sheets = {
        "00_README": _readme_df(summary),
        "01_PACKAGE_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343J_SUMMARY": _build_key_value_df(summary_343j),
        "03_ATTESTATION_ITEMS": attestation_df,
        "04_ATTESTATION_TEMPLATE": attestation_df,
        "05_SOURCE_EVIDENCE": _clean_frame(
            pd.DataFrame(_build_source_evidence_rows(attestation_items))
        ),
        "06_ATTESTATION_RULES": _clean_frame(pd.DataFrame(build_attestation_rules_rows())),
        "07_CLIENT_EXPORT_BOUNDARY": _clean_frame(
            pd.DataFrame(build_boundary_rows(summary))
        ),
        "08_IMPORT_CONTRACT": _build_key_value_df(expected_import_contract),
        "09_343L_READINESS": _clean_frame(pd.DataFrame(build_readiness_rows(summary))),
        "10_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "11_NEXT_STEPS": _clean_frame(pd.DataFrame(build_next_steps_rows())),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "attestation_items": attestation_items,
        "expected_import_contract": expected_import_contract,
        "reviewer_instructions_markdown": reviewer_instructions_md,
        "fill_guide_markdown": fill_guide_md,
        "client_export_boundary_markdown": _build_client_export_boundary_markdown(summary),
        "workbook_sheets": workbook_sheets,
        "attestation_template_sheets": {"04_ATTESTATION_TEMPLATE": attestation_df},
    }
