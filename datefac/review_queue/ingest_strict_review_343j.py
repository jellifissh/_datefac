from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_float, normalize_text
from datefac.review_queue.strict_human_review_package_343i import (
    ALLOWED_STRICT_REVIEW_DECISIONS,
    EDITABLE_STRICT_REVIEW_COLUMNS,
    REQUIRED_IDENTITY_COLUMNS,
    STRICT_CORRECT_REQUIRED_COLUMNS,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_343J = "AI_ASSISTED_STRICT_REVIEW_INGESTION_343J_READY"
NOT_READY_DECISION_343J = "AI_ASSISTED_STRICT_REVIEW_INGESTION_343J_NOT_READY"
RECOMMENDED_343K_SCOPE_343J = (
    "pure_human_confirmation_attestation_package_for_ai_assisted_strict_confirmed_rows"
)

STRICT_REVIEW_INPUT_SOURCE_TYPE = "AI_ASSISTED_EVIDENCE_CHECK"
REVIEW_SOURCE_TYPE = "AI_ASSISTED_REVIEW"
SPOT_CHECK_SOURCE_TYPE = "AI_ASSISTED_SPOT_CHECK"
APPLY_MODE = "SIMULATION_ONLY"

WORKBOOK_SHEETS_343J = [
    "00_README",
    "01_INGEST_SUMMARY",
    "02_INPUT_343I2_SUMMARY",
    "03_REVIEW_RESULTS",
    "04_VALIDATION_ERRORS",
    "05_DECISION_SUMMARY",
    "06_EXPORT_GATE",
    "07_SOURCE_DISCLOSURE",
    "08_NO_WRITE_BACK",
    "09_NEXT_STEPS",
]

STRICT_DECISION_TO_RESULT_STATUS = {
    "STRICT_CONFIRM": "STRICT_CONFIRMED",
    "STRICT_CORRECT": "STRICT_CORRECTED",
    "STRICT_REJECT": "STRICT_REJECTED",
    "STRICT_NEEDS_SOURCE_CHECK": "STRICT_NEEDS_SOURCE_CHECK",
    "STRICT_DEFER": "STRICT_DEFERRED",
}

STRICT_REQUIRED_COLUMNS_BY_DECISION = {
    "STRICT_CONFIRM": ["strict_reviewer_id", "strict_reviewed_at"],
    "STRICT_CORRECT": [
        "strict_reviewer_id",
        "strict_reviewed_at",
        *STRICT_CORRECT_REQUIRED_COLUMNS,
        "strict_review_note",
    ],
    "STRICT_REJECT": ["strict_reviewer_id", "strict_reviewed_at", "strict_review_note"],
    "STRICT_NEEDS_SOURCE_CHECK": [
        "strict_reviewer_id",
        "strict_reviewed_at",
        "strict_review_note",
    ],
    "STRICT_DEFER": ["strict_reviewer_id", "strict_reviewed_at"],
}

STRICT_DECISION_NOTE_REQUIRED = {"STRICT_CORRECT", "STRICT_REJECT", "STRICT_NEEDS_SOURCE_CHECK"}

PRESERVED_EVIDENCE_FIELDS = [
    "queue_item_id",
    "review_item_id",
    "resulting_status",
    "simulated_downstream_action",
    "priority_tier",
    "source_stage",
    "source_artifact_path",
    "source_artifact_sheet",
    "source_row_id",
    "source_detail_level",
    "source_pdf_id",
    "source_pdf_name",
    "source_pdf_path",
    "page_number",
    "table_id",
    "cell_id",
    "bbox",
    "image_path",
    "source_html_snippet",
    "source_text_snippet",
    "metric_candidate_raw",
    "evidence_source_stage",
    "evidence_source_artifact",
    "evidence_resolution_status",
    "evidence_gap_reason",
]

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

FORBIDDEN_STAGE_PATHS = [
    "output",
    "temp",
    "input/review_queue_strict_human_review_343i2_filled",
    "input/review_queue_strict_human_review_343i_filled",
    "input/review_queue_spot_check_package_343f_filled",
    "input/review_queue_real_excel_review_343c_filled",
    "input/llm_review_responses_342m",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]


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


def _read_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    return _clean_frame(pd.read_excel(path, sheet_name=sheet_name))


def _strip_html_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _build_readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "343J ingests the AI-assisted evidence-check-filled strict review workbook and writes sidecar-only audit outputs.",
                },
                {
                    "section": "boundary",
                    "message": "343J does not claim pure human strict review completion and does not allow formal client export.",
                },
                {
                    "section": "next",
                    "message": "If QA passes, proceed to the 343K pure human confirmation attestation package.",
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def _build_source_disclosure_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "field_name": "strict_review_input_source_type",
            "value": summary.get("strict_review_input_source_type", STRICT_REVIEW_INPUT_SOURCE_TYPE),
            "meaning": "The filled workbook came from an AI-assisted evidence check.",
        },
        {
            "field_name": "review_source_type",
            "value": summary.get("review_source_type", REVIEW_SOURCE_TYPE),
            "meaning": "Preserved upstream AI-assisted review lineage.",
        },
        {
            "field_name": "spot_check_source_type",
            "value": summary.get("spot_check_source_type", SPOT_CHECK_SOURCE_TYPE),
            "meaning": "Preserved upstream AI-assisted spot-check lineage.",
        },
        {
            "field_name": "not_pure_human_review",
            "value": summary.get("not_pure_human_review", True),
            "meaning": "The result must not be presented as pure human-only review.",
        },
        {
            "field_name": "pure_strict_human_review_completed",
            "value": summary.get("pure_strict_human_review_completed", False),
            "meaning": "Pure human confirmation is still pending.",
        },
        {
            "field_name": "strict_human_review_completed",
            "value": summary.get("strict_human_review_completed", False),
            "meaning": "Strict human review completion must remain false at 343J.",
        },
        {
            "field_name": "requires_pure_human_confirmation",
            "value": summary.get("requires_pure_human_confirmation", True),
            "meaning": "A later human attestation task is still required.",
        },
        {
            "field_name": "apply_mode",
            "value": summary.get("apply_mode", APPLY_MODE),
            "meaning": "The chain remains simulation-only.",
        },
        {
            "field_name": "review_source_disclosure",
            "value": summary.get("review_source_disclosure", ""),
            "meaning": "Human-readable disclosure for downstream users.",
        },
    ]


def _build_export_gate_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    reason = (
        "Current strict-review-style decisions were filled via AI-assisted evidence check; "
        "pure human reviewer confirmation is still required."
    )
    return [
        {
            "gate": "strict_review_result_ingested",
            "value": summary.get("strict_review_result_ingested", False),
            "meaning": "AI-assisted strict review results were ingested by 343J.",
        },
        {
            "gate": "pure_strict_human_review_completed",
            "value": summary.get("pure_strict_human_review_completed", False),
            "meaning": "Must remain false until 343K or later attestation.",
        },
        {
            "gate": "strict_human_review_completed",
            "value": summary.get("strict_human_review_completed", False),
            "meaning": "Must remain false for the current AI-assisted workbook.",
        },
        {
            "gate": "requires_pure_human_confirmation",
            "value": summary.get("requires_pure_human_confirmation", True),
            "meaning": "A pure human confirmation step is still required.",
        },
        {
            "gate": "formal_client_export_allowed",
            "value": summary.get("formal_client_export_allowed", False),
            "meaning": "Formal client export remains forbidden.",
        },
        {
            "gate": "client_ready",
            "value": summary.get("client_ready", False),
            "meaning": "Client-ready must remain false.",
        },
        {
            "gate": "production_ready",
            "value": summary.get("production_ready", False),
            "meaning": "Production-ready must remain false.",
        },
        {
            "gate": "reason",
            "value": reason,
            "meaning": "Why export gating remains closed.",
        },
    ]


def _build_next_steps_rows(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    next_scope = summary.get("recommended_343k_scope", "")
    if not next_scope:
        next_scope = "Refill the workbook correctly and rerun 343J."
    return [
        {
            "step": "review_ingestion_output",
            "recommendation": "Open the 343J workbook and result JSONL to verify ingested strict-review decisions.",
        },
        {
            "step": "preserve_ai_assisted_disclosure",
            "recommendation": "Keep the AI-assisted evidence-check disclosure in all downstream tasks.",
        },
        {
            "step": "prepare_next_task",
            "recommendation": next_scope,
        },
    ]


def _build_input_contract(review_queue_schema_version: str, output_dir_hint: str) -> Dict[str, Any]:
    return {
        "contract_version": "343J.strict_review_ingestion.v1",
        "source_review_queue_schema_version": review_queue_schema_version,
        "required_sheet_name": "04_REVIEW_TEMPLATE",
        "required_identity_columns": REQUIRED_IDENTITY_COLUMNS,
        "editable_strict_review_columns": EDITABLE_STRICT_REVIEW_COLUMNS,
        "allowed_strict_review_decisions": ALLOWED_STRICT_REVIEW_DECISIONS,
        "strict_correct_required_columns": STRICT_CORRECT_REQUIRED_COLUMNS,
        "strict_review_input_source_type": STRICT_REVIEW_INPUT_SOURCE_TYPE,
        "review_source_type": REVIEW_SOURCE_TYPE,
        "spot_check_source_type": SPOT_CHECK_SOURCE_TYPE,
        "apply_mode": APPLY_MODE,
        "expected_input_path_pattern": "D:/_datefac/input/review_queue_strict_human_review_343i2_filled/*.xlsx",
        "required_disclosure": {
            "not_pure_human_review": True,
            "pure_strict_human_review_completed": False,
            "strict_human_review_completed": False,
            "requires_pure_human_confirmation": True,
        },
        "recommended_output_dir_hint": output_dir_hint,
    }


def validate_filled_strict_review_row(
    row: Dict[str, Any],
    *,
    expected_row: Dict[str, Any] | None,
) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    for field in REQUIRED_IDENTITY_COLUMNS:
        if not normalize_text(row.get(field)):
            errors.append(f"missing required identity field: {field}")

    for field in EDITABLE_STRICT_REVIEW_COLUMNS:
        if field not in row:
            errors.append(f"missing strict review column: {field}")

    decision = normalize_text(row.get("strict_review_decision"))
    if not decision:
        errors.append("strict_review_decision must not be empty")
    elif decision not in ALLOWED_STRICT_REVIEW_DECISIONS:
        errors.append(f"invalid strict_review_decision: {decision}")

    if decision in STRICT_REQUIRED_COLUMNS_BY_DECISION:
        for field in STRICT_REQUIRED_COLUMNS_BY_DECISION[decision]:
            if not normalize_text(row.get(field)):
                errors.append(f"missing required field for {decision}: {field}")

    if decision in STRICT_DECISION_NOTE_REQUIRED and not normalize_text(row.get("strict_review_note")):
        errors.append(f"{decision} requires strict_review_note")

    if decision == "STRICT_DEFER" and not normalize_text(row.get("strict_review_note")):
        warnings.append("STRICT_DEFER should include strict_review_note when available")

    if decision == "STRICT_CORRECT":
        strict_value = normalize_text(row.get("strict_review_value_numeric"))
        if strict_value and normalize_float(row.get("strict_review_value_numeric")) is None:
            errors.append("strict_review_value_numeric must be numeric for STRICT_CORRECT")

    if normalize_text(row.get("review_source_type")) != REVIEW_SOURCE_TYPE:
        errors.append("review_source_type must remain AI_ASSISTED_REVIEW")
    if normalize_text(row.get("spot_check_source_type")) != SPOT_CHECK_SOURCE_TYPE:
        errors.append("spot_check_source_type must remain AI_ASSISTED_SPOT_CHECK")
    if not normalize_bool(row.get("not_pure_human_review")):
        errors.append("not_pure_human_review must remain true")
    if normalize_bool(row.get("pure_strict_human_review_completed")):
        errors.append("pure_strict_human_review_completed must remain false")
    if normalize_bool(row.get("strict_human_review_completed")):
        errors.append("strict_human_review_completed must remain false")
    if not normalize_bool(row.get("requires_human_spot_check")):
        errors.append("requires_human_spot_check must remain true")
    if not normalize_bool(row.get("requires_strict_human_review")):
        errors.append("requires_strict_human_review must remain true")
    if normalize_text(row.get("apply_mode")) != APPLY_MODE:
        errors.append("apply_mode must remain SIMULATION_ONLY")
    if normalize_bool(row.get("formal_client_export_allowed")):
        errors.append("formal_client_export_allowed must remain false")
    if normalize_bool(row.get("client_ready")):
        errors.append("client_ready must remain false")
    if normalize_bool(row.get("production_ready")):
        errors.append("production_ready must remain false")
    if not normalize_bool(row.get("waiting_for_strict_human_review")):
        errors.append("waiting_for_strict_human_review must remain true")
    if normalize_bool(row.get("strict_human_review_result_ingested")):
        warnings.append(
            "strict_human_review_result_ingested should remain false for AI-assisted evidence-check input"
        )

    if expected_row:
        for field in PRESERVED_EVIDENCE_FIELDS:
            if normalize_text(row.get(field)) != normalize_text(expected_row.get(field)):
                errors.append(f"preserved evidence field mismatch: {field}")

    validation_status = "PASS"
    if errors:
        validation_status = "FAIL"
    elif warnings:
        validation_status = "PASS_WITH_WARNING"

    return {
        "queue_item_id": normalize_text(row.get("queue_item_id")),
        "review_item_id": normalize_text(row.get("review_item_id")),
        "strict_review_decision": decision,
        "strict_review_result_status": STRICT_DECISION_TO_RESULT_STATUS.get(decision, ""),
        "validation_status": validation_status,
        "errors": errors,
        "warnings": warnings,
    }


def build_strict_review_result_row(
    row: Dict[str, Any],
    *,
    validation: Dict[str, Any],
) -> Dict[str, Any]:
    result = dict(row)
    result["strict_review_input_source_type"] = STRICT_REVIEW_INPUT_SOURCE_TYPE
    result["pure_strict_human_review_completed"] = False
    result["requires_pure_human_confirmation"] = True
    result["strict_review_result_status"] = validation["strict_review_result_status"]
    result["strict_review_result_ingested"] = False
    result["review_source_disclosure"] = (
        "AI-assisted evidence check filled the strict_review_* fields; "
        "pure human confirmation is still required before any stronger trust claim."
    )
    result["validation_status"] = validation["validation_status"]
    result["validation_errors"] = validation["errors"]
    result["validation_warnings"] = validation["warnings"]
    return result


def decision_summary_rows(review_results: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts = {decision: 0 for decision in ALLOWED_STRICT_REVIEW_DECISIONS}
    for row in review_results:
        decision = normalize_text(row.get("strict_review_decision"))
        if decision in counts:
            counts[decision] += 1
    return [
        {
            "strict_review_decision": decision,
            "strict_review_result_status": STRICT_DECISION_TO_RESULT_STATUS[decision],
            "row_count": counts[decision],
        }
        for decision in ALLOWED_STRICT_REVIEW_DECISIONS
    ]


def build_validation_issue_rows(validation_rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    for row in validation_rows:
        for error in row.get("errors", []):
            issues.append(
                {
                    "row_index": row.get("row_index", ""),
                    "queue_item_id": row.get("queue_item_id", ""),
                    "review_item_id": row.get("review_item_id", ""),
                    "issue_type": "ERROR",
                    "message": error,
                }
            )
        for warning in row.get("warnings", []):
            issues.append(
                {
                    "row_index": row.get("row_index", ""),
                    "queue_item_id": row.get("queue_item_id", ""),
                    "review_item_id": row.get("review_item_id", ""),
                    "issue_type": "WARNING",
                    "message": warning,
                }
            )
    return issues


def build_review_queue_strict_review_ingestion_343j(
    *,
    source_evidence_enrichment_343i2_dir: Path,
    strict_human_review_package_343i_dir: Path,
    audit_summary_343h_dir: Path,
    review_queue_schema_343a_dir: Path,
    filled_workbook: Path,
    output_dir: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_343i2_path = (
        source_evidence_enrichment_343i2_dir
        / "review_queue_source_evidence_enrichment_343i2_summary.json"
    )
    qa_343i2_path = (
        source_evidence_enrichment_343i2_dir
        / "review_queue_source_evidence_enrichment_343i2_qa.json"
    )
    report_343i2_path = (
        source_evidence_enrichment_343i2_dir
        / "review_queue_source_evidence_enrichment_343i2_report.md"
    )
    evidence_gap_343i2_path = (
        source_evidence_enrichment_343i2_dir
        / "review_queue_source_evidence_enrichment_343i2_evidence_gap_report.md"
    )
    enriched_template_343i2_path = (
        source_evidence_enrichment_343i2_dir
        / "review_queue_source_evidence_enrichment_343i2_enriched_review_template.xlsx"
    )
    enriched_items_343i2_path = (
        source_evidence_enrichment_343i2_dir
        / "review_queue_source_evidence_enrichment_343i2_enriched_items.jsonl"
    )
    import_contract_343i2_path = (
        source_evidence_enrichment_343i2_dir
        / "review_queue_source_evidence_enrichment_343i2_expected_import_contract.json"
    )
    no_write_back_343i2_path = (
        source_evidence_enrichment_343i2_dir
        / "review_queue_source_evidence_enrichment_343i2_no_write_back_proof.json"
    )

    summary_343i_path = (
        strict_human_review_package_343i_dir
        / "review_queue_strict_human_review_package_343i_summary.json"
    )
    review_items_343i_path = (
        strict_human_review_package_343i_dir
        / "review_queue_strict_human_review_package_343i_review_items.jsonl"
    )
    import_contract_343i_path = (
        strict_human_review_package_343i_dir
        / "review_queue_strict_human_review_package_343i_expected_import_contract.json"
    )

    summary_343h_path = audit_summary_343h_dir / "review_queue_audit_summary_343h_summary.json"
    client_export_gate_343h_path = (
        audit_summary_343h_dir / "review_queue_audit_summary_343h_client_export_gate.json"
    )

    spot_check_343g_dir = audit_summary_343h_dir.parent / "review_queue_spot_check_ingestion_343g"
    result_343g_path = spot_check_343g_dir / "review_queue_spot_check_ingestion_343g_result.jsonl"

    summary_343a_path = review_queue_schema_343a_dir / "review_queue_schema_343a_summary.json"
    schema_343a_path = review_queue_schema_343a_dir / "review_queue_schema_343a_schema.json"
    json_schema_343a_path = (
        review_queue_schema_343a_dir / "review_queue_schema_343a_json_schema.json"
    )

    input_paths = [
        summary_343i2_path,
        qa_343i2_path,
        report_343i2_path,
        evidence_gap_343i2_path,
        enriched_template_343i2_path,
        enriched_items_343i2_path,
        import_contract_343i2_path,
        no_write_back_343i2_path,
        summary_343i_path,
        review_items_343i_path,
        import_contract_343i_path,
        summary_343h_path,
        client_export_gate_343h_path,
        result_343g_path,
        summary_343a_path,
        schema_343a_path,
        json_schema_343a_path,
        filled_workbook,
    ]

    files_read: List[str] = []
    warnings: List[str] = []
    for path in input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input: {path}")

    summary_343i2 = _read_json(summary_343i2_path) if summary_343i2_path.exists() else {}
    qa_343i2 = _read_json(qa_343i2_path) if qa_343i2_path.exists() else {}
    enriched_items_343i2 = _read_jsonl(enriched_items_343i2_path) if enriched_items_343i2_path.exists() else []
    import_contract_343i2 = (
        _read_json(import_contract_343i2_path) if import_contract_343i2_path.exists() else {}
    )
    summary_343i = _read_json(summary_343i_path) if summary_343i_path.exists() else {}
    review_items_343i = _read_jsonl(review_items_343i_path) if review_items_343i_path.exists() else []
    import_contract_343i = (
        _read_json(import_contract_343i_path) if import_contract_343i_path.exists() else {}
    )
    summary_343h = _read_json(summary_343h_path) if summary_343h_path.exists() else {}
    client_export_gate_343h = (
        _read_json(client_export_gate_343h_path)
        if client_export_gate_343h_path.exists()
        else {}
    )
    result_343g = _read_jsonl(result_343g_path) if result_343g_path.exists() else []
    summary_343a = _read_json(summary_343a_path) if summary_343a_path.exists() else {}

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    expected_sheet = normalize_text(import_contract_343i2.get("required_sheet_name")) or "04_REVIEW_TEMPLATE"
    workbook_sheet_names: List[str] = []
    workbook_read_error = ""
    filled_df = pd.DataFrame()
    if filled_workbook.exists():
        try:
            excel = pd.ExcelFile(filled_workbook)
            workbook_sheet_names = list(excel.sheet_names)
            if expected_sheet not in workbook_sheet_names:
                workbook_read_error = f"required sheet missing: {expected_sheet}"
            else:
                filled_df = _read_excel_sheet(filled_workbook, expected_sheet)
        except Exception as exc:
            workbook_read_error = f"unable to read filled workbook: {exc}"
    else:
        workbook_read_error = f"filled workbook missing: {filled_workbook}"

    input_ready = bool(
        summary_343i2.get("decision")
        == "SOURCE_EVIDENCE_ENRICHMENT_343I2_WAITING_FOR_STRICT_REVIEW"
        and int(summary_343i2.get("qa_fail_count", 1)) == 0
        and normalize_bool(summary_343i2.get("source_evidence_enrichment_completed"))
        and normalize_bool(summary_343i2.get("waiting_for_strict_human_review"))
        and not normalize_bool(summary_343i2.get("strict_human_review_result_ingested"))
        and not normalize_bool(summary_343i2.get("strict_human_review_completed"))
        and normalize_bool(summary_343i2.get("requires_strict_human_review"))
        and not normalize_bool(summary_343i2.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343i2.get("client_ready"))
        and not normalize_bool(summary_343i2.get("production_ready"))
        and int(summary_343i2.get("input_strict_review_item_count", -1)) == 10
        and int(summary_343i2.get("evidence_resolved_count", -1)) == 10
        and int(summary_343i2.get("evidence_partial_count", -1)) == 0
        and int(summary_343i2.get("evidence_unresolved_count", -1)) == 0
        and import_contract_343i2.get("required_sheet_name") == "04_REVIEW_TEMPLATE"
        and summary_343i.get("decision") == "STRICT_HUMAN_REVIEW_PACKAGE_343I_WAITING_FOR_STRICT_REVIEW"
        and int(summary_343i.get("qa_fail_count", 1)) == 0
        and normalize_bool(summary_343i.get("waiting_for_strict_human_review"))
        and not normalize_bool(summary_343i.get("strict_human_review_result_ingested"))
        and int(summary_343i.get("strict_review_item_count", -1)) == len(review_items_343i)
        and import_contract_343i.get("required_sheet_name") == "04_REVIEW_TEMPLATE"
        and summary_343h.get("decision") == "AI_ASSISTED_SPOT_CHECK_AUDIT_SUMMARY_343H_READY"
        and int(summary_343h.get("qa_fail_count", 1)) == 0
        and normalize_bool(summary_343h.get("ready_for_343i"))
        and int(summary_343h.get("ai_assisted_confirmed_count", -1)) == 10
        and int(summary_343h.get("source_check_required_count", -1)) == 19
        and int(summary_343h.get("keep_hold_count", -1)) == 1
        and not normalize_bool(client_export_gate_343h.get("formal_client_export_allowed"))
        and not normalize_bool(client_export_gate_343h.get("client_ready"))
        and not normalize_bool(client_export_gate_343h.get("production_ready"))
        and normalize_bool(client_export_gate_343h.get("requires_strict_human_review"))
        and result_343g_path.exists()
        and len(result_343g) > 0
        and summary_343a_path.exists()
        and schema_343a_path.exists()
        and json_schema_343a_path.exists()
        and filled_workbook.exists()
        and workbook_read_error == ""
    )

    expected_rows_by_pair = {
        (
            normalize_text(item.get("queue_item_id")),
            normalize_text(item.get("review_item_id")),
        ): item
        for item in enriched_items_343i2
    }

    review_results: List[Dict[str, Any]] = []
    validation_rows: List[Dict[str, Any]] = []
    validation_errors: List[Dict[str, Any]] = []
    validation_warnings: List[Dict[str, Any]] = []
    valid_rows: List[Dict[str, Any]] = []
    invalid_rows: List[Dict[str, Any]] = []

    if not filled_df.empty:
        for index, row in enumerate(filled_df.to_dict(orient="records"), start=1):
            key = (
                normalize_text(row.get("queue_item_id")),
                normalize_text(row.get("review_item_id")),
            )
            validation = validate_filled_strict_review_row(
                row,
                expected_row=expected_rows_by_pair.get(key),
            )
            validation_rows.append({"row_index": index, **validation})
            result_row = build_strict_review_result_row(row, validation=validation)
            result_row["row_index"] = index
            review_results.append(result_row)
            if validation["validation_status"] == "FAIL":
                invalid_rows.append(
                    {
                        **row,
                        "row_index": index,
                        "validation_errors": validation["errors"],
                        "validation_warnings": validation["warnings"],
                    }
                )
            else:
                valid_rows.append(result_row)
            if validation["errors"]:
                validation_errors.append(
                    {
                        "row_index": index,
                        "queue_item_id": validation["queue_item_id"],
                        "review_item_id": validation["review_item_id"],
                        "errors": validation["errors"],
                    }
                )
            if validation["warnings"]:
                validation_warnings.append(
                    {
                        "row_index": index,
                        "queue_item_id": validation["queue_item_id"],
                        "review_item_id": validation["review_item_id"],
                        "warnings": validation["warnings"],
                    }
                )

    strict_confirm_count = sum(
        1
        for row in review_results
        if normalize_text(row.get("strict_review_decision")) == "STRICT_CONFIRM"
    )
    strict_correct_count = sum(
        1
        for row in review_results
        if normalize_text(row.get("strict_review_decision")) == "STRICT_CORRECT"
    )
    strict_reject_count = sum(
        1
        for row in review_results
        if normalize_text(row.get("strict_review_decision")) == "STRICT_REJECT"
    )
    strict_needs_source_check_count = sum(
        1
        for row in review_results
        if normalize_text(row.get("strict_review_decision")) == "STRICT_NEEDS_SOURCE_CHECK"
    )
    strict_defer_count = sum(
        1
        for row in review_results
        if normalize_text(row.get("strict_review_decision")) == "STRICT_DEFER"
    )

    row_pairs = [
        (normalize_text(row.get("queue_item_id")), normalize_text(row.get("review_item_id")))
        for row in review_results
    ]
    row_count_matches = len(review_results) == len(enriched_items_343i2)
    row_pair_set_matches = set(row_pairs) == set(expected_rows_by_pair.keys()) and len(row_pairs) == len(
        set(row_pairs)
    )

    validation_error_count = sum(len(item["errors"]) for item in validation_errors)
    validation_warning_count = sum(len(item["warnings"]) for item in validation_warnings)
    strict_review_result_ingested = bool(
        input_ready and row_count_matches and row_pair_set_matches and validation_error_count == 0
    )
    ready_for_343k = strict_review_result_ingested

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343I2",
        "decision": READY_DECISION_343J if ready_for_343k else NOT_READY_DECISION_343J,
        "review_queue_schema_version": summary_343i2.get(
            "review_queue_schema_version",
            summary_343a.get("review_queue_schema_version", ""),
        ),
        "filled_workbook_path": str(filled_workbook),
        "filled_row_count": len(review_results),
        "valid_row_count": len(valid_rows),
        "invalid_row_count": len(invalid_rows),
        "strict_confirm_count": strict_confirm_count,
        "strict_correct_count": strict_correct_count,
        "strict_reject_count": strict_reject_count,
        "strict_needs_source_check_count": strict_needs_source_check_count,
        "strict_defer_count": strict_defer_count,
        "validation_error_count": validation_error_count,
        "validation_warning_count": validation_warning_count,
        "strict_review_input_source_type": STRICT_REVIEW_INPUT_SOURCE_TYPE,
        "review_source_type": REVIEW_SOURCE_TYPE,
        "spot_check_source_type": SPOT_CHECK_SOURCE_TYPE,
        "apply_mode": APPLY_MODE,
        "not_pure_human_review": True,
        "pure_strict_human_confirm_count": 0,
        "ai_assisted_strict_review_confirm_count": strict_confirm_count,
        "strict_review_result_ingested": strict_review_result_ingested,
        "strict_human_review_result_ingested": False,
        "pure_strict_human_review_completed": False,
        "strict_human_review_completed": False,
        "requires_strict_human_review": True,
        "requires_pure_human_confirmation": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343k": ready_for_343k,
        "recommended_343k_scope": RECOMMENDED_343K_SCOPE_343J if ready_for_343k else "",
        "strict_review_source_disclosure": (
            "AI-assisted evidence check filled the strict_review_* fields; pure human confirmation is still required."
        ),
        "review_source_disclosure": (
            "review_source_type remains AI_ASSISTED_REVIEW and strict_review_input_source_type remains "
            "AI_ASSISTED_EVIDENCE_CHECK; the workbook is not pure strict human review."
        ),
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "output_directory": str(output_dir),
    }

    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="343J",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["strict_review_result_ingested"] = strict_review_result_ingested
    no_write_back_json["real_production_apply_performed"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343j")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    validation_issue_rows = build_validation_issue_rows(validation_rows)
    decision_summary = decision_summary_rows(review_results)

    checks = [
        {
            "check_name": "inputs::filled_workbook_exists",
            "status": "PASS" if filled_workbook.exists() else "FAIL",
            "detail": str(filled_workbook),
        },
        {
            "check_name": "inputs::filled_workbook_readable",
            "status": "PASS" if workbook_read_error == "" else "FAIL",
            "detail": workbook_read_error or "ok",
        },
        {
            "check_name": "inputs::required_sheet_exists",
            "status": "PASS" if expected_sheet in workbook_sheet_names else "FAIL",
            "detail": json.dumps(
                {"required_sheet": expected_sheet, "sheet_names": workbook_sheet_names},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::343i2_source_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "summary_343i2_decision": summary_343i2.get("decision", ""),
                    "summary_343i_decision": summary_343i.get("decision", ""),
                    "summary_343h_decision": summary_343h.get("decision", ""),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::filled_row_count_matches_expected_10",
            "status": "PASS" if row_count_matches else "FAIL",
            "detail": json.dumps(
                {"filled_row_count": len(review_results), "expected": len(enriched_items_343i2)},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "identity::id_set_matches_343i2_enriched_items",
            "status": "PASS" if row_pair_set_matches else "FAIL",
            "detail": json.dumps({"row_pairs": row_pairs}, ensure_ascii=False),
        },
        {
            "check_name": "validation::allowed_decisions_only",
            "status": "PASS"
            if all(
                normalize_text(row.get("strict_review_decision")) in ALLOWED_STRICT_REVIEW_DECISIONS
                for row in review_results
            )
            else "FAIL",
            "detail": json.dumps(ALLOWED_STRICT_REVIEW_DECISIONS, ensure_ascii=False),
        },
        {
            "check_name": "validation::strict_confirm_requires_reviewer_id_and_date",
            "status": "PASS"
            if not any(
                normalize_text(row.get("strict_review_decision")) == "STRICT_CONFIRM"
                and (
                    not normalize_text(row.get("strict_reviewer_id"))
                    or not normalize_text(row.get("strict_reviewed_at"))
                )
                for row in review_results
            )
            else "FAIL",
            "detail": "STRICT_CONFIRM requires strict_reviewer_id and strict_reviewed_at",
        },
        {
            "check_name": "validation::strict_correct_requires_payload",
            "status": "PASS"
            if not any(
                normalize_text(row.get("strict_review_decision")) == "STRICT_CORRECT"
                and any(
                    not normalize_text(row.get(field))
                    for field in STRICT_REQUIRED_COLUMNS_BY_DECISION["STRICT_CORRECT"]
                )
                for row in review_results
            )
            else "FAIL",
            "detail": json.dumps(STRICT_REQUIRED_COLUMNS_BY_DECISION["STRICT_CORRECT"], ensure_ascii=False),
        },
        {
            "check_name": "validation::reject_and_source_check_require_notes",
            "status": "PASS"
            if not any(
                normalize_text(row.get("strict_review_decision"))
                in {"STRICT_REJECT", "STRICT_NEEDS_SOURCE_CHECK"}
                and not normalize_text(row.get("strict_review_note"))
                for row in review_results
            )
            else "FAIL",
            "detail": "STRICT_REJECT and STRICT_NEEDS_SOURCE_CHECK require notes",
        },
        {
            "check_name": "disclosure::ai_assisted_source_preserved",
            "status": "PASS"
            if all(
                normalize_text(row.get("strict_review_input_source_type"))
                == STRICT_REVIEW_INPUT_SOURCE_TYPE
                and normalize_text(row.get("review_source_type")) == REVIEW_SOURCE_TYPE
                and normalize_text(row.get("spot_check_source_type")) == SPOT_CHECK_SOURCE_TYPE
                and normalize_text(row.get("apply_mode")) == APPLY_MODE
                and normalize_bool(row.get("not_pure_human_review"))
                and not normalize_bool(row.get("pure_strict_human_review_completed"))
                and not normalize_bool(row.get("strict_human_review_completed"))
                and normalize_bool(row.get("requires_pure_human_confirmation"))
                for row in review_results
            )
            else "FAIL",
            "detail": STRICT_REVIEW_INPUT_SOURCE_TYPE,
        },
        {
            "check_name": "claims::strict_human_review_not_claimed_complete",
            "status": "PASS"
            if not summary["pure_strict_human_review_completed"]
            and not summary["strict_human_review_completed"]
            else "FAIL",
            "detail": "pure_strict_human_review_completed and strict_human_review_completed must remain false",
        },
        {
            "check_name": "claims::formal_client_export_gate_remains_false",
            "status": "PASS"
            if not summary["formal_client_export_allowed"]
            and not summary["client_ready"]
            and not summary["production_ready"]
            else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready must remain false",
        },
        {
            "check_name": "outputs::reviewer_source_disclosure_generated",
            "status": "PASS",
            "detail": "review_queue_strict_review_ingestion_343j_reviewer_source_disclosure.md",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "343J is workbook ingestion only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "343J does not perform real apply or workbook write-back.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343J adds review-queue sidecar files only.",
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
            "status": "PASS" if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_343J) else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_343J, ensure_ascii=False),
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
    summary["qa_fail_count"] = qa_fail_count
    summary["strict_review_result_ingested"] = bool(strict_review_result_ingested and qa_fail_count == 0)
    summary["ready_for_343k"] = bool(summary["strict_review_result_ingested"] and qa_fail_count == 0)
    summary["recommended_343k_scope"] = (
        RECOMMENDED_343K_SCOPE_343J if summary["ready_for_343k"] else ""
    )
    summary["decision"] = READY_DECISION_343J if summary["ready_for_343k"] else NOT_READY_DECISION_343J
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    for row in review_results:
        row["strict_review_result_ingested"] = summary["strict_review_result_ingested"]

    client_export_gate = {
        "strict_review_input_source_type": STRICT_REVIEW_INPUT_SOURCE_TYPE,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "strict_human_review_completed": False,
        "requires_strict_human_review": True,
        "requires_pure_human_confirmation": True,
        "strict_review_result_ingested": summary["strict_review_result_ingested"],
        "ready_for_343k": summary["ready_for_343k"],
        "recommended_343k_scope": summary["recommended_343k_scope"],
        "reason": (
            "Current strict-review-style decisions were filled via AI-assisted evidence check; "
            "pure human reviewer confirmation is still required."
        ),
    }

    manifest = {
        "task": "343J_strict_review_result_ingestion_from_enriched_workbook",
        "source_evidence_enrichment_343i2_dir": str(source_evidence_enrichment_343i2_dir),
        "strict_human_review_package_343i_dir": str(strict_human_review_package_343i_dir),
        "audit_summary_343h_dir": str(audit_summary_343h_dir),
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "filled_workbook": str(filled_workbook),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "review_queue_strict_review_ingestion_343j_summary.json"),
            "manifest_json": str(output_dir / "review_queue_strict_review_ingestion_343j_manifest.json"),
            "qa_json": str(output_dir / "review_queue_strict_review_ingestion_343j_qa.json"),
            "no_write_back_proof_json": str(
                output_dir / "review_queue_strict_review_ingestion_343j_no_write_back_proof.json"
            ),
            "report_md": str(output_dir / "review_queue_strict_review_ingestion_343j_report.md"),
            "workbook_xlsx": str(output_dir / "review_queue_strict_review_ingestion_343j.xlsx"),
            "result_jsonl": str(output_dir / "review_queue_strict_review_ingestion_343j_result.jsonl"),
            "validation_errors_json": str(
                output_dir / "review_queue_strict_review_ingestion_343j_validation_errors.json"
            ),
            "decision_summary_json": str(
                output_dir / "review_queue_strict_review_ingestion_343j_decision_summary.json"
            ),
            "client_export_gate_json": str(
                output_dir / "review_queue_strict_review_ingestion_343j_client_export_gate.json"
            ),
            "reviewer_source_disclosure_md": str(
                output_dir / "review_queue_strict_review_ingestion_343j_reviewer_source_disclosure.md"
            ),
        },
        "files_read": list(files_read),
        "warnings": warnings,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    result_df = _clean_frame(pd.DataFrame(review_results))
    validation_issue_df = _clean_frame(pd.DataFrame(validation_issue_rows))
    workbook_sheets = {
        "00_README": _build_readme_df(summary),
        "01_INGEST_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343I2_SUMMARY": _build_key_value_df(summary_343i2),
        "03_REVIEW_RESULTS": result_df,
        "04_VALIDATION_ERRORS": validation_issue_df,
        "05_DECISION_SUMMARY": _clean_frame(pd.DataFrame(decision_summary)),
        "06_EXPORT_GATE": _clean_frame(pd.DataFrame(_build_export_gate_rows(summary))),
        "07_SOURCE_DISCLOSURE": _clean_frame(
            pd.DataFrame(_build_source_disclosure_rows(summary))
        ),
        "08_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "09_NEXT_STEPS": _clean_frame(pd.DataFrame(_build_next_steps_rows(summary))),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "result_rows": review_results,
        "validation_errors": validation_issue_rows,
        "decision_summary": decision_summary,
        "client_export_gate": client_export_gate,
        "reviewer_source_disclosure_rows": _build_source_disclosure_rows(summary),
        "expected_import_contract": _build_input_contract(
            review_queue_schema_version=summary["review_queue_schema_version"],
            output_dir_hint=str(output_dir),
        ),
        "workbook_sheets": workbook_sheets,
    }
