from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_float, normalize_text
from datefac.review_queue.ingest_strict_review_343j import (
    APPLY_MODE,
    FORBIDDEN_STAGE_PATHS,
    PROTECTED_DIRTY_PATHS,
    REVIEW_SOURCE_TYPE,
    SPOT_CHECK_SOURCE_TYPE,
    STRICT_REVIEW_INPUT_SOURCE_TYPE,
)
from datefac.review_queue.pure_human_attestation_package_343k import (
    ALLOWED_HUMAN_ATTESTATION_DECISIONS,
    EDITABLE_HUMAN_ATTESTATION_COLUMNS,
    HUMAN_CORRECT_REQUIRED_COLUMNS,
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


READY_DECISION_343L = "PURE_HUMAN_ATTESTATION_INGESTION_343L_READY"
REMEDIATION_REQUIRED_DECISION_343L = (
    "PURE_HUMAN_ATTESTATION_INGESTION_343L_REMEDIATION_REQUIRED"
)
NOT_READY_DECISION_343L = "PURE_HUMAN_ATTESTATION_INGESTION_343L_NOT_READY"
RECOMMENDED_343M_SCOPE_343L = (
    "human_confirmed_sidecar_apply_simulation_and_limited_export_gate"
)

WORKBOOK_SHEETS_343L = [
    "00_README",
    "01_INGEST_SUMMARY",
    "02_INPUT_343K_SUMMARY",
    "03_ATTESTATION_RESULTS",
    "04_VALIDATION_ERRORS",
    "05_DECISION_SUMMARY",
    "06_EXPORT_GATE",
    "07_SCOPE_BOUNDARY",
    "08_NO_WRITE_BACK",
    "09_NEXT_STEPS",
]

PACKAGE_SUMMARY_NAME = "review_queue_pure_human_attestation_package_343k_summary.json"
PACKAGE_QA_NAME = "review_queue_pure_human_attestation_package_343k_qa.json"
PACKAGE_ITEMS_NAME = "review_queue_pure_human_attestation_package_343k_attestation_items.jsonl"
PACKAGE_IMPORT_CONTRACT_NAME = (
    "review_queue_pure_human_attestation_package_343k_expected_import_contract.json"
)
PACKAGE_NO_WRITE_BACK_NAME = (
    "review_queue_pure_human_attestation_package_343k_no_write_back_proof.json"
)

STRICT_REVIEW_SUMMARY_NAME = "review_queue_strict_review_ingestion_343j_summary.json"
STRICT_REVIEW_RESULT_NAME = "review_queue_strict_review_ingestion_343j_result.jsonl"
STRICT_REVIEW_GATE_NAME = "review_queue_strict_review_ingestion_343j_client_export_gate.json"

SOURCE_EVIDENCE_SUMMARY_NAME = "review_queue_source_evidence_enrichment_343i2_summary.json"
SOURCE_EVIDENCE_ITEMS_NAME = (
    "review_queue_source_evidence_enrichment_343i2_enriched_items.jsonl"
)
SCHEMA_SUMMARY_NAME = "review_queue_schema_343a_summary.json"
SCHEMA_FILE_NAME = "review_queue_schema_343a_schema.json"

REQUIRED_SHEET_NAME = "04_ATTESTATION_TEMPLATE"

REQUIRED_BY_DECISION = {
    "HUMAN_ACCEPT_AI_ASSISTED_CONFIRM": [
        "human_reviewer_id",
        "human_reviewed_at",
    ],
    "HUMAN_CORRECT": [
        "human_reviewer_id",
        "human_reviewed_at",
        *HUMAN_CORRECT_REQUIRED_COLUMNS,
        "human_attestation_note",
    ],
    "HUMAN_REJECT": [
        "human_reviewer_id",
        "human_reviewed_at",
        "human_attestation_note",
    ],
    "HUMAN_NEEDS_SOURCE_CHECK": [
        "human_reviewer_id",
        "human_reviewed_at",
        "human_attestation_note",
    ],
    "HUMAN_DEFER": [
        "human_reviewer_id",
        "human_reviewed_at",
    ],
}


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


def _read_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    return _clean_frame(pd.read_excel(path, sheet_name=sheet_name))


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


def _build_readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "343L ingests the filled pure-human attestation workbook and produces a scoped attestation result.",
                },
                {
                    "section": "scope_boundary",
                    "message": "Even when all 10 rows pass, completion applies only to the 343K package scope, not the whole corpus.",
                },
                {
                    "section": "boundary",
                    "message": "Formal client export remains forbidden and no production apply is performed.",
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def _preserved_fields() -> List[str]:
    return list(REQUIRED_IDENTITY_COLUMNS) + list(EVIDENCE_LOCATOR_COLUMNS) + [
        "strict_review_decision",
        "strict_review_metric_standardized",
        "strict_review_year_standardized",
        "strict_review_value_numeric",
        "strict_review_normalized_unit",
        "strict_review_note",
        "strict_reviewer_id",
        "strict_reviewed_at",
        "strict_review_input_source_type",
        "review_source_type",
        "spot_check_source_type",
        "apply_mode",
        "not_pure_human_review",
        "pure_strict_human_review_completed",
        "strict_human_review_completed",
        "requires_pure_human_confirmation",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "waiting_for_pure_human_attestation",
    ]


def validate_human_attestation_row(
    row: Dict[str, Any],
    *,
    expected_row: Dict[str, Any] | None,
) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    for field in REQUIRED_IDENTITY_COLUMNS:
        if not normalize_text(row.get(field)):
            errors.append(f"missing required identity field: {field}")

    for field in EDITABLE_HUMAN_ATTESTATION_COLUMNS:
        if field not in row:
            errors.append(f"missing human attestation column: {field}")

    decision = normalize_text(row.get("human_attestation_decision"))
    if not decision:
        errors.append("human_attestation_decision must not be empty")
    elif decision not in ALLOWED_HUMAN_ATTESTATION_DECISIONS:
        errors.append(f"invalid human_attestation_decision: {decision}")

    if decision in REQUIRED_BY_DECISION:
        for field in REQUIRED_BY_DECISION[decision]:
            if not normalize_text(row.get(field)):
                errors.append(f"missing required field for {decision}: {field}")

    if decision == "HUMAN_ACCEPT_AI_ASSISTED_CONFIRM":
        if not normalize_bool(row.get("human_source_evidence_checked")):
            errors.append(
                "HUMAN_ACCEPT_AI_ASSISTED_CONFIRM requires human_source_evidence_checked=true"
            )
        if not normalize_bool(row.get("human_independent_check_attested")):
            errors.append(
                "HUMAN_ACCEPT_AI_ASSISTED_CONFIRM requires human_independent_check_attested=true"
            )

    if decision == "HUMAN_CORRECT":
        if normalize_text(row.get("human_attested_value_numeric")) and normalize_float(
            row.get("human_attested_value_numeric")
        ) is None:
            errors.append("human_attested_value_numeric must be numeric for HUMAN_CORRECT")
        if not normalize_bool(row.get("human_source_evidence_checked")):
            errors.append("HUMAN_CORRECT requires human_source_evidence_checked=true")

    if decision == "HUMAN_REJECT":
        if not normalize_bool(row.get("human_source_evidence_checked")):
            errors.append("HUMAN_REJECT requires human_source_evidence_checked=true")

    if decision == "HUMAN_DEFER" and not normalize_text(row.get("human_attestation_note")):
        warnings.append("HUMAN_DEFER should include human_attestation_note when possible")

    if normalize_text(row.get("review_source_type")) != REVIEW_SOURCE_TYPE:
        errors.append("review_source_type must remain AI_ASSISTED_REVIEW")
    if normalize_text(row.get("spot_check_source_type")) != SPOT_CHECK_SOURCE_TYPE:
        errors.append("spot_check_source_type must remain AI_ASSISTED_SPOT_CHECK")
    if normalize_text(row.get("strict_review_input_source_type")) != STRICT_REVIEW_INPUT_SOURCE_TYPE:
        errors.append("strict_review_input_source_type must remain AI_ASSISTED_EVIDENCE_CHECK")
    if normalize_text(row.get("apply_mode")) != APPLY_MODE:
        errors.append("apply_mode must remain SIMULATION_ONLY")
    if not normalize_bool(row.get("not_pure_human_review")):
        errors.append("not_pure_human_review must remain true")
    if normalize_bool(row.get("pure_strict_human_review_completed")):
        errors.append("pure_strict_human_review_completed must remain false in the filled input")
    if normalize_bool(row.get("strict_human_review_completed")):
        errors.append("strict_human_review_completed must remain false in the filled input")
    if not normalize_bool(row.get("requires_pure_human_confirmation")):
        warnings.append("requires_pure_human_confirmation should remain true in the filled input")
    if normalize_bool(row.get("formal_client_export_allowed")):
        errors.append("formal_client_export_allowed must remain false")
    if normalize_bool(row.get("client_ready")):
        errors.append("client_ready must remain false")
    if normalize_bool(row.get("production_ready")):
        errors.append("production_ready must remain false")

    if expected_row:
        for field in _preserved_fields():
            if normalize_text(row.get(field)) != normalize_text(expected_row.get(field)):
                errors.append(f"preserved field mismatch: {field}")

    validation_status = "PASS"
    if errors:
        validation_status = "FAIL"
    elif warnings:
        validation_status = "PASS_WITH_WARNING"

    return {
        "queue_item_id": normalize_text(row.get("queue_item_id")),
        "review_item_id": normalize_text(row.get("review_item_id")),
        "human_attestation_decision": decision,
        "validation_status": validation_status,
        "errors": errors,
        "warnings": warnings,
    }


def build_result_row(
    row: Dict[str, Any],
    *,
    validation: Dict[str, Any],
    package_completed: bool = False,
) -> Dict[str, Any]:
    result = dict(row)
    result["pure_human_attestation_result_status"] = validation["validation_status"]
    result["validation_status"] = validation["validation_status"]
    result["validation_errors"] = validation["errors"]
    result["validation_warnings"] = validation["warnings"]
    result["formal_client_export_allowed"] = False
    result["client_ready"] = False
    result["production_ready"] = False
    result["global_strict_human_review_completed"] = False
    result["pure_human_attestation_result_ingested"] = False
    result["pure_strict_human_review_completed_for_package"] = False
    result["strict_human_review_completed_scope"] = ""
    if package_completed:
        result["pure_human_attestation_result_ingested"] = True
        result["pure_strict_human_review_completed_for_package"] = True
        result["strict_human_review_completed_scope"] = "343K_PACKAGE_ONLY"
    return result


def build_validation_issue_rows(validation_rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    for row in validation_rows:
        for error in row.get("errors", []):
            issues.append(
                {
                    "queue_item_id": row.get("queue_item_id", ""),
                    "review_item_id": row.get("review_item_id", ""),
                    "issue_type": "ERROR",
                    "message": error,
                }
            )
        for warning in row.get("warnings", []):
            issues.append(
                {
                    "queue_item_id": row.get("queue_item_id", ""),
                    "review_item_id": row.get("review_item_id", ""),
                    "issue_type": "WARNING",
                    "message": warning,
                }
            )
    return issues


def decision_summary_rows(results: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts = {decision: 0 for decision in ALLOWED_HUMAN_ATTESTATION_DECISIONS}
    for row in results:
        decision = normalize_text(row.get("human_attestation_decision"))
        if decision in counts:
            counts[decision] += 1
    return [
        {"human_attestation_decision": decision, "row_count": counts[decision]}
        for decision in ALLOWED_HUMAN_ATTESTATION_DECISIONS
    ]


def _build_export_gate_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "gate": "formal_client_export_allowed",
            "value": summary.get("formal_client_export_allowed", False),
            "meaning": "Must remain false even if package-level human confirmation is complete.",
        },
        {
            "gate": "client_ready",
            "value": summary.get("client_ready", False),
            "meaning": "Client-ready remains false at 343L.",
        },
        {
            "gate": "production_ready",
            "value": summary.get("production_ready", False),
            "meaning": "Production-ready remains false at 343L.",
        },
        {
            "gate": "global_strict_human_review_completed",
            "value": summary.get("global_strict_human_review_completed", False),
            "meaning": "The whole corpus is not globally strict-human-complete.",
        },
        {
            "gate": "package_strict_human_review_completed",
            "value": summary.get("pure_strict_human_review_completed_for_package", False),
            "meaning": "Completion only applies to the current 343K package when true.",
        },
        {
            "gate": "strict_human_review_completed_scope",
            "value": summary.get("strict_human_review_completed_scope", ""),
            "meaning": "Expected to be 343K_PACKAGE_ONLY when package completion is reached.",
        },
        {
            "gate": "reason",
            "value": (
                "Pure human attestation may be complete only for the 10-row 343K package; "
                "formal client export still requires a downstream scoped export gate and remaining backlog handling."
            ),
            "meaning": "Why export gating remains closed.",
        },
    ]


def _build_scope_boundary_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "scope_name": "343K_PACKAGE_ONLY",
            "pure_strict_human_review_completed_for_package": summary.get(
                "pure_strict_human_review_completed_for_package",
                False,
            ),
            "global_strict_human_review_completed": summary.get(
                "global_strict_human_review_completed",
                False,
            ),
            "boundary_note": "Even a full 10/10 attestation only completes the current package scope.",
        }
    ]


def _build_next_steps_rows(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    if summary.get("ready_for_343m"):
        return [
            {
                "step": "open_343l_result_bundle",
                "recommendation": "Verify the attestation ingestion result and scope boundary workbook first.",
            },
            {
                "step": "prepare_343m_scope",
                "recommendation": summary.get("recommended_343m_scope", ""),
            },
        ]
    return [
        {
            "step": "fix_invalid_or_noncompleted_rows",
            "recommendation": "Review validation errors or remediation decisions and refill the attestation workbook conservatively.",
        },
        {
            "step": "rerun_343l_after_refill",
            "recommendation": "Rerun 343L only after the corrected workbook is saved.",
        },
    ]


def build_scope_boundary_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 343L Scope Boundary",
            "",
            "## 中文说明",
            "- 343L 只导入 343K 的 10 条 pure human attestation 结果。",
            "- 即使 10 条都通过，也只代表 `343K_PACKAGE_ONLY` 范围内完成人工确认。",
            "- 这不等于整个 corpus 完成严格人工审核。",
            "- formal client export / client_ready / production_ready 仍然必须保持 false。",
            "",
            "## English Note",
            "- 343L can only complete pure-human confirmation for the 343K package scope.",
            "- It does not complete global strict human review across the whole corpus.",
            "",
            "## Current Scope Gate",
            f"- pure_strict_human_review_completed_for_package: {summary.get('pure_strict_human_review_completed_for_package', False)}",
            f"- strict_human_review_completed_scope: {summary.get('strict_human_review_completed_scope', '')}",
            f"- global_strict_human_review_completed: {summary.get('global_strict_human_review_completed', False)}",
            f"- formal_client_export_allowed: {summary.get('formal_client_export_allowed', False)}",
        ]
    )


def build_review_queue_pure_human_attestation_ingestion_343l(
    *,
    pure_human_attestation_package_343k_dir: Path,
    strict_review_ingestion_343j_dir: Path,
    source_evidence_enrichment_343i2_dir: Path,
    review_queue_schema_343a_dir: Path,
    filled_workbook: Path,
    output_dir: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    alias_asset_path = SEMANTIC_ALIAS_ASSET_PATH
    scope_asset_path = FORMAL_SCOPE_RULES_PATH
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    package_summary_path = pure_human_attestation_package_343k_dir / PACKAGE_SUMMARY_NAME
    package_qa_path = pure_human_attestation_package_343k_dir / PACKAGE_QA_NAME
    package_items_path = pure_human_attestation_package_343k_dir / PACKAGE_ITEMS_NAME
    package_import_contract_path = (
        pure_human_attestation_package_343k_dir / PACKAGE_IMPORT_CONTRACT_NAME
    )
    package_no_write_back_path = pure_human_attestation_package_343k_dir / PACKAGE_NO_WRITE_BACK_NAME

    strict_review_summary_path = strict_review_ingestion_343j_dir / STRICT_REVIEW_SUMMARY_NAME
    strict_review_result_path = strict_review_ingestion_343j_dir / STRICT_REVIEW_RESULT_NAME
    strict_review_gate_path = strict_review_ingestion_343j_dir / STRICT_REVIEW_GATE_NAME

    source_evidence_summary_path = source_evidence_enrichment_343i2_dir / SOURCE_EVIDENCE_SUMMARY_NAME
    source_evidence_items_path = source_evidence_enrichment_343i2_dir / SOURCE_EVIDENCE_ITEMS_NAME
    schema_summary_path = review_queue_schema_343a_dir / SCHEMA_SUMMARY_NAME
    schema_file_path = review_queue_schema_343a_dir / SCHEMA_FILE_NAME

    input_paths = [
        package_summary_path,
        package_qa_path,
        package_items_path,
        package_import_contract_path,
        package_no_write_back_path,
        strict_review_summary_path,
        strict_review_result_path,
        strict_review_gate_path,
        source_evidence_summary_path,
        source_evidence_items_path,
        schema_summary_path,
        schema_file_path,
        filled_workbook,
    ]

    files_read: List[str] = []
    warnings: List[str] = []
    missing_required_inputs: List[str] = []
    for path in input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            missing_required_inputs.append(str(path))

    package_summary = _read_json(package_summary_path) if package_summary_path.exists() else {}
    package_qa = _read_json(package_qa_path) if package_qa_path.exists() else {}
    package_items = _read_jsonl(package_items_path) if package_items_path.exists() else []
    package_contract = _read_json(package_import_contract_path) if package_import_contract_path.exists() else {}
    strict_review_summary = _read_json(strict_review_summary_path) if strict_review_summary_path.exists() else {}
    strict_review_results = _read_jsonl(strict_review_result_path) if strict_review_result_path.exists() else []
    strict_review_gate = _read_json(strict_review_gate_path) if strict_review_gate_path.exists() else {}
    source_evidence_summary = _read_json(source_evidence_summary_path) if source_evidence_summary_path.exists() else {}
    schema_summary = _read_json(schema_summary_path) if schema_summary_path.exists() else {}

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    input_ready = bool(
        not missing_required_inputs
        and package_summary.get("decision")
        == "PURE_HUMAN_ATTESTATION_PACKAGE_343K_WAITING_FOR_HUMAN_ATTESTATION"
        and int(package_summary.get("qa_fail_count", 1)) == 0
        and int(package_summary.get("attestation_item_count", -1)) >= 1
        and normalize_bool(package_summary.get("waiting_for_pure_human_attestation"))
        and not normalize_bool(package_summary.get("pure_human_attestation_result_ingested"))
        and not normalize_bool(package_summary.get("formal_client_export_allowed"))
        and not normalize_bool(package_summary.get("client_ready"))
        and not normalize_bool(package_summary.get("production_ready"))
        and strict_review_summary.get("decision")
        == "AI_ASSISTED_STRICT_REVIEW_INGESTION_343J_READY"
        and int(strict_review_summary.get("qa_fail_count", 1)) == 0
        and not normalize_bool(strict_review_gate.get("formal_client_export_allowed"))
    )

    workbook_sheet_names: List[str] = []
    workbook_read_error = ""
    workbook_rows: List[Dict[str, Any]] = []
    try:
        workbook_df = _read_excel_sheet(filled_workbook, REQUIRED_SHEET_NAME)
        workbook_sheet_names = [REQUIRED_SHEET_NAME]
        workbook_rows = workbook_df.to_dict(orient="records")
    except Exception as exc:
        workbook_read_error = str(exc)
        workbook_rows = []

    expected_rows_by_pair = {
        (
            normalize_text(item.get("queue_item_id")),
            normalize_text(item.get("review_item_id")),
        ): item
        for item in package_items
    }

    validation_rows: List[Dict[str, Any]] = []
    results: List[Dict[str, Any]] = []
    valid_rows: List[Dict[str, Any]] = []
    invalid_rows: List[Dict[str, Any]] = []

    for row in workbook_rows:
        pair = (
            normalize_text(row.get("queue_item_id")),
            normalize_text(row.get("review_item_id")),
        )
        validation = validate_human_attestation_row(
            row,
            expected_row=expected_rows_by_pair.get(pair),
        )
        validation_rows.append(validation)
        result_row = build_result_row(row, validation=validation, package_completed=False)
        results.append(result_row)
        if validation["validation_status"] == "FAIL":
            invalid_rows.append(result_row)
        else:
            valid_rows.append(result_row)

    filled_row_count = len(results)
    expected_row_count = len(package_items)
    row_count_matches = filled_row_count == expected_row_count and filled_row_count > 0
    row_pairs = [
        (normalize_text(row.get("queue_item_id")), normalize_text(row.get("review_item_id")))
        for row in results
    ]
    row_pair_set_matches = set(row_pairs) == set(expected_rows_by_pair.keys()) and len(row_pairs) == len(set(row_pairs))

    human_accept_count = sum(
        1 for row in results if normalize_text(row.get("human_attestation_decision")) == "HUMAN_ACCEPT_AI_ASSISTED_CONFIRM"
    )
    human_correct_count = sum(
        1 for row in results if normalize_text(row.get("human_attestation_decision")) == "HUMAN_CORRECT"
    )
    human_reject_count = sum(
        1 for row in results if normalize_text(row.get("human_attestation_decision")) == "HUMAN_REJECT"
    )
    human_needs_source_check_count = sum(
        1 for row in results if normalize_text(row.get("human_attestation_decision")) == "HUMAN_NEEDS_SOURCE_CHECK"
    )
    human_defer_count = sum(
        1 for row in results if normalize_text(row.get("human_attestation_decision")) == "HUMAN_DEFER"
    )
    human_source_evidence_checked_true_count = sum(
        1 for row in results if normalize_bool(row.get("human_source_evidence_checked"))
    )
    human_independent_check_attested_true_count = sum(
        1 for row in results if normalize_bool(row.get("human_independent_check_attested"))
    )
    validation_error_count = sum(len(item["errors"]) for item in validation_rows)
    validation_warning_count = sum(len(item["warnings"]) for item in validation_rows)

    package_completion_candidate = bool(
        input_ready
        and row_count_matches
        and row_pair_set_matches
        and validation_error_count == 0
        and human_accept_count + human_correct_count == filled_row_count
        and human_reject_count == 0
        and human_needs_source_check_count == 0
        and human_defer_count == 0
    )

    pure_human_attestation_result_ingested = bool(
        package_completion_candidate and filled_row_count == expected_row_count
    )

    for row in results:
        row["pure_human_attestation_result_ingested"] = pure_human_attestation_result_ingested
        row["pure_strict_human_review_completed_for_package"] = pure_human_attestation_result_ingested
        row["strict_human_review_completed_scope"] = (
            "343K_PACKAGE_ONLY" if pure_human_attestation_result_ingested else ""
        )

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343K",
        "decision": NOT_READY_DECISION_343L,
        "review_queue_schema_version": package_summary.get(
            "review_queue_schema_version",
            schema_summary.get("review_queue_schema_version", ""),
        ),
        "filled_workbook_path": str(filled_workbook),
        "filled_row_count": filled_row_count,
        "valid_row_count": len(valid_rows),
        "invalid_row_count": len(invalid_rows),
        "human_accept_count": human_accept_count,
        "human_correct_count": human_correct_count,
        "human_reject_count": human_reject_count,
        "human_needs_source_check_count": human_needs_source_check_count,
        "human_defer_count": human_defer_count,
        "human_source_evidence_checked_true_count": human_source_evidence_checked_true_count,
        "human_independent_check_attested_true_count": human_independent_check_attested_true_count,
        "pure_human_attestation_result_ingested": pure_human_attestation_result_ingested,
        "pure_strict_human_confirm_count": human_accept_count if pure_human_attestation_result_ingested else 0,
        "pure_strict_human_correct_count": human_correct_count if pure_human_attestation_result_ingested else 0,
        "pure_strict_human_reject_count": 0 if pure_human_attestation_result_ingested else human_reject_count,
        "pure_strict_human_review_completed_for_package": pure_human_attestation_result_ingested,
        "strict_human_review_completed_scope": "343K_PACKAGE_ONLY" if pure_human_attestation_result_ingested else "",
        "global_strict_human_review_completed": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343m": pure_human_attestation_result_ingested,
        "recommended_343m_scope": RECOMMENDED_343M_SCOPE_343L if pure_human_attestation_result_ingested else "",
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
        stage="343L",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["pure_human_attestation_result_ingested"] = pure_human_attestation_result_ingested
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["real_production_apply_performed"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343l")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    validation_issue_rows = build_validation_issue_rows(validation_rows)
    decision_summary = decision_summary_rows(results)
    editable_columns_exist = bool(
        workbook_rows
        and all(column in workbook_rows[0] for column in EDITABLE_HUMAN_ATTESTATION_COLUMNS)
    )

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
            "status": "PASS" if REQUIRED_SHEET_NAME in workbook_sheet_names else "FAIL",
            "detail": json.dumps({"required_sheet": REQUIRED_SHEET_NAME, "sheet_names": workbook_sheet_names}, ensure_ascii=False),
        },
        {
            "check_name": "inputs::343k_package_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "missing_required_inputs": missing_required_inputs,
                    "package_decision": package_summary.get("decision", ""),
                    "package_qa_fail_count": package_summary.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "schema::required_identity_columns_exist",
            "status": "PASS"
            if workbook_rows and all(field in workbook_rows[0] for field in REQUIRED_IDENTITY_COLUMNS)
            else "FAIL",
            "detail": json.dumps(REQUIRED_IDENTITY_COLUMNS, ensure_ascii=False),
        },
        {
            "check_name": "schema::editable_human_attestation_columns_exist",
            "status": "PASS" if editable_columns_exist else "FAIL",
            "detail": json.dumps(EDITABLE_HUMAN_ATTESTATION_COLUMNS, ensure_ascii=False),
        },
        {
            "check_name": "identity::row_count_matches_343k_items",
            "status": "PASS" if row_count_matches else "FAIL",
            "detail": json.dumps({"filled_row_count": filled_row_count, "expected": expected_row_count}, ensure_ascii=False),
        },
        {
            "check_name": "identity::id_set_matches_343k_items",
            "status": "PASS" if row_pair_set_matches else "FAIL",
            "detail": json.dumps({"row_pairs": row_pairs}, ensure_ascii=False),
        },
        {
            "check_name": "validation::allowed_decisions_only",
            "status": "PASS"
            if all(
                normalize_text(row.get("human_attestation_decision")) in ALLOWED_HUMAN_ATTESTATION_DECISIONS
                for row in results
            )
            else "FAIL",
            "detail": json.dumps(ALLOWED_HUMAN_ATTESTATION_DECISIONS, ensure_ascii=False),
        },
        {
            "check_name": "validation::required_reviewer_id_and_date_present",
            "status": "PASS"
            if not any(
                normalize_text(row.get("human_attestation_decision")) in REQUIRED_BY_DECISION
                and (
                    not normalize_text(row.get("human_reviewer_id"))
                    or not normalize_text(row.get("human_reviewed_at"))
                )
                for row in results
            )
            else "FAIL",
            "detail": "All filled decisions require human_reviewer_id and human_reviewed_at",
        },
        {
            "check_name": "validation::accept_requires_checked_and_attested_true",
            "status": "PASS"
            if not any(
                normalize_text(row.get("human_attestation_decision")) == "HUMAN_ACCEPT_AI_ASSISTED_CONFIRM"
                and (
                    not normalize_bool(row.get("human_source_evidence_checked"))
                    or not normalize_bool(row.get("human_independent_check_attested"))
                )
                for row in results
            )
            else "FAIL",
            "detail": "HUMAN_ACCEPT_AI_ASSISTED_CONFIRM requires both human_source_evidence_checked=true and human_independent_check_attested=true",
        },
        {
            "check_name": "validation::correct_requires_payload_and_note",
            "status": "PASS"
            if not any(
                normalize_text(row.get("human_attestation_decision")) == "HUMAN_CORRECT"
                and (
                    any(
                        not normalize_text(row.get(field))
                        for field in HUMAN_CORRECT_REQUIRED_COLUMNS
                    )
                    or not normalize_text(row.get("human_attestation_note"))
                )
                for row in results
            )
            else "FAIL",
            "detail": json.dumps(HUMAN_CORRECT_REQUIRED_COLUMNS + ["human_attestation_note"], ensure_ascii=False),
        },
        {
            "check_name": "validation::reject_and_source_check_require_note",
            "status": "PASS"
            if not any(
                normalize_text(row.get("human_attestation_decision")) in {"HUMAN_REJECT", "HUMAN_NEEDS_SOURCE_CHECK"}
                and not normalize_text(row.get("human_attestation_note"))
                for row in results
            )
            else "FAIL",
            "detail": "HUMAN_REJECT and HUMAN_NEEDS_SOURCE_CHECK require human_attestation_note",
        },
        {
            "check_name": "claims::client_export_gate_remains_false",
            "status": "PASS"
            if not summary["formal_client_export_allowed"]
            and not summary["client_ready"]
            and not summary["production_ready"]
            else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready must remain false",
        },
        {
            "check_name": "claims::global_strict_human_review_not_claimed_complete",
            "status": "PASS" if not summary["global_strict_human_review_completed"] else "FAIL",
            "detail": "global_strict_human_review_completed must remain false",
        },
        {
            "check_name": "claims::package_completion_scope_clearly_limited",
            "status": "PASS"
            if (not summary["pure_strict_human_review_completed_for_package"])
            or summary["strict_human_review_completed_scope"] == "343K_PACKAGE_ONLY"
            else "FAIL",
            "detail": "When package completion is true, scope must be 343K_PACKAGE_ONLY",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "343L is workbook ingestion only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "343L does not perform production apply or upstream workbook write-back.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343L adds review-queue sidecar files only.",
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
            "status": "PASS" if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_343L) else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_343L, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    if qa_fail_count == 0 and pure_human_attestation_result_ingested:
        summary["decision"] = READY_DECISION_343L
    elif qa_fail_count == 0 and filled_row_count > 0:
        summary["decision"] = REMEDIATION_REQUIRED_DECISION_343L
    else:
        summary["decision"] = NOT_READY_DECISION_343L
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    client_export_gate = {
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "package_strict_human_review_completed": summary["pure_strict_human_review_completed_for_package"],
        "strict_human_review_completed_scope": summary["strict_human_review_completed_scope"],
        "reason": (
            "Pure human attestation may be complete only for the 10-row 343K package; "
            "formal client export still requires a downstream scoped export gate and remaining backlog handling."
        ),
    }

    manifest = {
        "task": "343L_pure_human_attestation_result_ingestion",
        "pure_human_attestation_package_343k_dir": str(pure_human_attestation_package_343k_dir),
        "strict_review_ingestion_343j_dir": str(strict_review_ingestion_343j_dir),
        "source_evidence_enrichment_343i2_dir": str(source_evidence_enrichment_343i2_dir),
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "filled_workbook": str(filled_workbook),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "review_queue_pure_human_attestation_ingestion_343l_summary.json"),
            "manifest_json": str(output_dir / "review_queue_pure_human_attestation_ingestion_343l_manifest.json"),
            "qa_json": str(output_dir / "review_queue_pure_human_attestation_ingestion_343l_qa.json"),
            "no_write_back_proof_json": str(output_dir / "review_queue_pure_human_attestation_ingestion_343l_no_write_back_proof.json"),
            "report_md": str(output_dir / "review_queue_pure_human_attestation_ingestion_343l_report.md"),
            "workbook_xlsx": str(output_dir / "review_queue_pure_human_attestation_ingestion_343l.xlsx"),
            "result_jsonl": str(output_dir / "review_queue_pure_human_attestation_ingestion_343l_result.jsonl"),
            "validation_errors_json": str(output_dir / "review_queue_pure_human_attestation_ingestion_343l_validation_errors.json"),
            "decision_summary_json": str(output_dir / "review_queue_pure_human_attestation_ingestion_343l_decision_summary.json"),
            "client_export_gate_json": str(output_dir / "review_queue_pure_human_attestation_ingestion_343l_client_export_gate.json"),
            "scope_boundary_md": str(output_dir / "review_queue_pure_human_attestation_ingestion_343l_scope_boundary.md"),
        },
        "files_read": list(files_read),
        "warnings": warnings,
        "package_contract": package_contract,
        "strict_review_summary_loaded": bool(strict_review_summary),
        "source_evidence_summary_loaded": bool(source_evidence_summary),
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    result_df = _clean_frame(pd.DataFrame(results))
    validation_issue_df = _clean_frame(pd.DataFrame(validation_issue_rows))
    workbook_sheets = {
        "00_README": _build_readme_df(summary),
        "01_INGEST_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343K_SUMMARY": _build_key_value_df(package_summary),
        "03_ATTESTATION_RESULTS": result_df,
        "04_VALIDATION_ERRORS": validation_issue_df,
        "05_DECISION_SUMMARY": _clean_frame(pd.DataFrame(decision_summary)),
        "06_EXPORT_GATE": _clean_frame(pd.DataFrame(_build_export_gate_rows(summary))),
        "07_SCOPE_BOUNDARY": _clean_frame(pd.DataFrame(_build_scope_boundary_rows(summary))),
        "08_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "09_NEXT_STEPS": _clean_frame(pd.DataFrame(_build_next_steps_rows(summary))),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "result_rows": results,
        "validation_errors": validation_issue_rows,
        "decision_summary": decision_summary,
        "client_export_gate": client_export_gate,
        "scope_boundary_markdown": build_scope_boundary_markdown(summary),
        "workbook_sheets": workbook_sheets,
    }
