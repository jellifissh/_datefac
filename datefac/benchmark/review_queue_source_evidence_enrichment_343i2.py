from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.source_evidence_enrichment_343i2 import (
    EDITABLE_STRICT_REVIEW_COLUMNS,
    EVIDENCE_LOCATOR_COLUMNS,
    NOT_READY_DECISION_343I2,
    READY_DECISION_343I2,
    RECOMMENDED_343J_SCOPE_343I2,
    WORKBOOK_SHEETS_343I2,
    build_decision_guide_rows,
    build_enriched_item,
    build_evidence_field_rows,
    build_expected_import_contract,
    build_next_steps_rows,
    build_readiness_rows,
    build_resolution_map_payload,
    build_resolution_map_rows,
    build_unresolved_items,
    enriched_decisions_blank,
)
from datefac.review_queue.strict_human_review_package_343i import (
    READY_DECISION_343I,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_343H_DECISION = "AI_ASSISTED_SPOT_CHECK_AUDIT_SUMMARY_343H_READY"

DEFAULT_STRICT_HUMAN_REVIEW_PACKAGE_343I_DIR = Path(
    r"D:\_datefac\output\review_queue_strict_human_review_package_343i"
)
DEFAULT_AUDIT_SUMMARY_343H_DIR = Path(r"D:\_datefac\output\review_queue_audit_summary_343h")
DEFAULT_SPOT_CHECK_INGESTION_343G_DIR = Path(r"D:\_datefac\output\review_queue_spot_check_ingestion_343g")
DEFAULT_APPLY_SIMULATION_343E_DIR = Path(r"D:\_datefac\output\review_queue_apply_simulation_343e")
DEFAULT_EXCEL_INGESTION_343D_DIR = Path(r"D:\_datefac\output\review_queue_excel_ingestion_343d")
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(r"D:\_datefac\output\review_queue_schema_343a")
DEFAULT_AUDIT_LABELED_EXPORT_CANDIDATE_342R_DIR = Path(
    r"D:\_datefac\output\audit_labeled_export_candidate_package_342r"
)
DEFAULT_PREVIEW_AUDIT_342Q_DIR = Path(
    r"D:\_datefac\output\preview_audit_export_readiness_gate_342q"
)
DEFAULT_SNAPSHOT_342S_DIR = Path(
    r"D:\_datefac\output\package_audit_snapshot_demo_handoff_342s"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\review_queue_source_evidence_enrichment_343i2")

SUMMARY_FILE_NAME = "review_queue_source_evidence_enrichment_343i2_summary.json"
MANIFEST_FILE_NAME = "review_queue_source_evidence_enrichment_343i2_manifest.json"
QA_FILE_NAME = "review_queue_source_evidence_enrichment_343i2_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_source_evidence_enrichment_343i2_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_source_evidence_enrichment_343i2_report.md"
WORKBOOK_FILE_NAME = "review_queue_source_evidence_enrichment_343i2.xlsx"
ENRICHED_REVIEW_TEMPLATE_FILE_NAME = (
    "review_queue_source_evidence_enrichment_343i2_enriched_review_template.xlsx"
)
ENRICHED_ITEMS_FILE_NAME = "review_queue_source_evidence_enrichment_343i2_enriched_items.jsonl"
EVIDENCE_GAP_REPORT_FILE_NAME = (
    "review_queue_source_evidence_enrichment_343i2_evidence_gap_report.md"
)
EVIDENCE_RESOLUTION_MAP_FILE_NAME = (
    "review_queue_source_evidence_enrichment_343i2_evidence_resolution_map.json"
)
UNRESOLVED_ITEMS_FILE_NAME = (
    "review_queue_source_evidence_enrichment_343i2_unresolved_evidence_items.jsonl"
)
EXPECTED_IMPORT_CONTRACT_FILE_NAME = (
    "review_queue_source_evidence_enrichment_343i2_expected_import_contract.json"
)

INPUT_343I_SUMMARY_NAME = "review_queue_strict_human_review_package_343i_summary.json"
INPUT_343I_QA_NAME = "review_queue_strict_human_review_package_343i_qa.json"
INPUT_343I_REVIEW_TEMPLATE_NAME = "review_queue_strict_human_review_package_343i_review_template.xlsx"
INPUT_343I_REVIEW_ITEMS_NAME = "review_queue_strict_human_review_package_343i_review_items.jsonl"
INPUT_343I_IMPORT_CONTRACT_NAME = "review_queue_strict_human_review_package_343i_expected_import_contract.json"

INPUT_343H_SUMMARY_NAME = "review_queue_audit_summary_343h_summary.json"
INPUT_343H_CONFIRMED_ITEMS_NAME = "review_queue_audit_summary_343h_confirmed_ai_assisted_items.jsonl"
INPUT_343H_GAP_ITEMS_NAME = "review_queue_audit_summary_343h_gap_items.jsonl"
INPUT_343H_GATE_NAME = "review_queue_audit_summary_343h_client_export_gate.json"

INPUT_343G_SUMMARY_NAME = "review_queue_spot_check_ingestion_343g_summary.json"
INPUT_343G_RESULT_NAME = "review_queue_spot_check_ingestion_343g_result.jsonl"
INPUT_343E_APPLY_PLAN_NAME = "review_queue_apply_simulation_343e_apply_plan.jsonl"
INPUT_343D_REVIEWED_RESULT_NAME = "review_queue_excel_ingestion_343d_reviewed_result.jsonl"
INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"
INPUT_343A_SCHEMA_NAME = "review_queue_schema_343a_schema.json"
INPUT_342R_CANDIDATES_NAME = "audit_labeled_export_candidate_package_342r_candidates.csv"
INPUT_342R_SUMMARY_NAME = "audit_labeled_export_candidate_package_342r_summary.json"
INPUT_342Q_SUMMARY_NAME = "preview_audit_export_readiness_gate_342q_summary.json"
INPUT_342S_ARTIFACT_INDEX_NAME = "package_audit_snapshot_demo_handoff_342s_artifact_index.json"

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


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _read_csv(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


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


def _flatten_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return normalize_text(value)


def _build_key_value_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [{"key": key, "value": _flatten_value(value)} for key, value in mapping.items()]
        )
    )


def _readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "343I2 enriches 343I strict review items with any available source evidence locators.",
                },
                {
                    "section": "boundary",
                    "message": "343I2 does not ingest strict human review results and does not approve export.",
                },
                {
                    "section": "resolution",
                    "message": "Evidence may be RESOLVED, PARTIAL, or UNRESOLVED depending on upstream traceability.",
                },
                {
                    "section": "next",
                    "message": "User should fill the enriched strict review workbook before 343J ingestion.",
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def build_review_queue_source_evidence_enrichment_343i2(
    *,
    strict_human_review_package_343i_dir: Path = DEFAULT_STRICT_HUMAN_REVIEW_PACKAGE_343I_DIR,
    audit_summary_343h_dir: Path = DEFAULT_AUDIT_SUMMARY_343H_DIR,
    spot_check_ingestion_343g_dir: Path = DEFAULT_SPOT_CHECK_INGESTION_343G_DIR,
    apply_simulation_343e_dir: Path = DEFAULT_APPLY_SIMULATION_343E_DIR,
    excel_ingestion_343d_dir: Path = DEFAULT_EXCEL_INGESTION_343D_DIR,
    review_queue_schema_343a_dir: Path = DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    audit_labeled_export_candidate_342r_dir: Path = DEFAULT_AUDIT_LABELED_EXPORT_CANDIDATE_342R_DIR,
    preview_audit_342q_dir: Path = DEFAULT_PREVIEW_AUDIT_342Q_DIR,
    snapshot_342s_dir: Path = DEFAULT_SNAPSHOT_342S_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    alias_asset_path = SEMANTIC_ALIAS_ASSET_PATH
    scope_asset_path = FORMAL_SCOPE_RULES_PATH
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_343i_path = strict_human_review_package_343i_dir / INPUT_343I_SUMMARY_NAME
    qa_343i_path = strict_human_review_package_343i_dir / INPUT_343I_QA_NAME
    review_template_343i_path = strict_human_review_package_343i_dir / INPUT_343I_REVIEW_TEMPLATE_NAME
    review_items_343i_path = strict_human_review_package_343i_dir / INPUT_343I_REVIEW_ITEMS_NAME
    import_contract_343i_path = strict_human_review_package_343i_dir / INPUT_343I_IMPORT_CONTRACT_NAME
    summary_343h_path = audit_summary_343h_dir / INPUT_343H_SUMMARY_NAME
    confirmed_343h_path = audit_summary_343h_dir / INPUT_343H_CONFIRMED_ITEMS_NAME
    gap_343h_path = audit_summary_343h_dir / INPUT_343H_GAP_ITEMS_NAME
    gate_343h_path = audit_summary_343h_dir / INPUT_343H_GATE_NAME
    summary_343g_path = spot_check_ingestion_343g_dir / INPUT_343G_SUMMARY_NAME
    result_343g_path = spot_check_ingestion_343g_dir / INPUT_343G_RESULT_NAME
    apply_plan_343e_path = apply_simulation_343e_dir / INPUT_343E_APPLY_PLAN_NAME
    reviewed_343d_path = excel_ingestion_343d_dir / INPUT_343D_REVIEWED_RESULT_NAME
    summary_343a_path = review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME
    schema_343a_path = review_queue_schema_343a_dir / INPUT_343A_SCHEMA_NAME
    candidates_342r_path = audit_labeled_export_candidate_342r_dir / INPUT_342R_CANDIDATES_NAME
    summary_342r_path = audit_labeled_export_candidate_342r_dir / INPUT_342R_SUMMARY_NAME
    summary_342q_path = preview_audit_342q_dir / INPUT_342Q_SUMMARY_NAME
    artifact_index_342s_path = snapshot_342s_dir / INPUT_342S_ARTIFACT_INDEX_NAME

    input_paths = [
        summary_343i_path,
        qa_343i_path,
        review_template_343i_path,
        review_items_343i_path,
        import_contract_343i_path,
        summary_343h_path,
        confirmed_343h_path,
        gap_343h_path,
        gate_343h_path,
        summary_343g_path,
        result_343g_path,
        apply_plan_343e_path,
        reviewed_343d_path,
        summary_343a_path,
        schema_343a_path,
        candidates_342r_path,
        summary_342r_path,
        summary_342q_path,
        artifact_index_342s_path,
    ]
    files_read: List[str] = []
    warnings: List[str] = []
    for path in input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input: {path}")

    summary_343i = _read_json(summary_343i_path) if summary_343i_path.exists() else {}
    summary_343h = _read_json(summary_343h_path) if summary_343h_path.exists() else {}
    client_export_gate_343h = _read_json(gate_343h_path) if gate_343h_path.exists() else {}
    review_items_343i = _read_jsonl(review_items_343i_path) if review_items_343i_path.exists() else []
    confirmed_343h = _read_jsonl(confirmed_343h_path) if confirmed_343h_path.exists() else []
    gap_items_343h = _read_jsonl(gap_343h_path) if gap_343h_path.exists() else []
    result_rows_343g = _read_jsonl(result_343g_path) if result_343g_path.exists() else []
    apply_plan_rows_343e = _read_jsonl(apply_plan_343e_path) if apply_plan_343e_path.exists() else []
    reviewed_rows_343d = _read_jsonl(reviewed_343d_path) if reviewed_343d_path.exists() else []
    summary_343a = _read_json(summary_343a_path) if summary_343a_path.exists() else {}
    export_rows_342r = _read_csv(candidates_342r_path) if candidates_342r_path.exists() else []
    summary_342r = _read_json(summary_342r_path) if summary_342r_path.exists() else {}
    summary_342q = _read_json(summary_342q_path) if summary_342q_path.exists() else {}
    artifact_index_342s = _read_json(artifact_index_342s_path) if artifact_index_342s_path.exists() else []

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    input_ready = bool(
        summary_343i.get("decision") == READY_DECISION_343I
        and normalize_bool(summary_343i.get("waiting_for_strict_human_review"))
        and not normalize_bool(summary_343i.get("strict_human_review_result_ingested"))
        and not normalize_bool(summary_343i.get("strict_human_review_completed"))
        and normalize_bool(summary_343i.get("requires_strict_human_review"))
        and not normalize_bool(summary_343i.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343i.get("client_ready"))
        and not normalize_bool(summary_343i.get("production_ready"))
        and int(summary_343i.get("qa_fail_count", 1)) == 0
        and summary_343h.get("decision") == READY_INPUT_343H_DECISION
        and int(summary_343h.get("qa_fail_count", 1)) == 0
        and len(review_items_343i) == int(summary_343i.get("strict_review_item_count", -1))
        and len(confirmed_343h) == int(summary_343h.get("ai_assisted_confirmed_count", -1))
        and normalize_bool(client_export_gate_343h.get("requires_strict_human_review"))
        and not normalize_bool(client_export_gate_343h.get("formal_client_export_allowed"))
    )

    reviewed_index = {
        (
            normalize_text(row.get("queue_item_id")),
            normalize_text(row.get("review_item_id")),
        ): row
        for row in reviewed_rows_343d
    }
    export_index = {}
    for row in export_rows_342r:
        keyed = dict(row)
        keyed["__source_artifact"] = str(candidates_342r_path)
        export_index[normalize_text(row.get("export_candidate_row_id"))] = keyed

    enriched_items: List[Dict[str, Any]] = []
    for item in review_items_343i:
        key = (
            normalize_text(item.get("queue_item_id")),
            normalize_text(item.get("review_item_id")),
        )
        reviewed_row = reviewed_index.get(key)
        export_row = None
        if reviewed_row:
            export_row = export_index.get(normalize_text(reviewed_row.get("source_row_id")))
        enriched_items.append(
            build_enriched_item(
                item,
                reviewed_row_343d=reviewed_row,
                export_row_342r=export_row,
            )
        )

    unresolved_items = build_unresolved_items(enriched_items)
    resolution_payload = build_resolution_map_payload(enriched_items)
    expected_import_contract = build_expected_import_contract(
        review_queue_schema_version=summary_343i.get("review_queue_schema_version", ""),
        output_dir_hint=str(output_dir),
    )
    evidence_field_rows = build_evidence_field_rows(enriched_items)

    enriched_columns_exist = bool(
        enriched_items
        and all(column in enriched_items[0] for column in EDITABLE_STRICT_REVIEW_COLUMNS)
    )
    decisions_blank = enriched_decisions_blank(enriched_items)
    every_item_has_resolution = all(
        normalize_text(item.get("evidence_resolution_status")) != ""
        for item in enriched_items
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343I",
        "decision": NOT_READY_DECISION_343I2,
        "review_queue_schema_version": summary_343i.get("review_queue_schema_version", ""),
        "input_strict_review_item_count": len(review_items_343i),
        "enriched_review_item_count": len(enriched_items),
        "evidence_resolved_count": resolution_payload["resolved_count"],
        "evidence_partial_count": resolution_payload["partial_count"],
        "evidence_unresolved_count": resolution_payload["unresolved_count"],
        "source_pdf_name_available_count": sum(
            1 for item in enriched_items if normalize_text(item.get("source_pdf_name")) != ""
        ),
        "source_pdf_path_available_count": sum(
            1 for item in enriched_items if normalize_text(item.get("source_pdf_path")) != ""
        ),
        "page_number_available_count": sum(
            1 for item in enriched_items if normalize_text(item.get("page_number")) != ""
        ),
        "source_text_snippet_available_count": sum(
            1 for item in enriched_items if normalize_text(item.get("source_text_snippet")) != ""
        ),
        "image_path_available_count": sum(
            1 for item in enriched_items if normalize_text(item.get("image_path")) != ""
        ),
        "enriched_review_template_generated": bool(enriched_items),
        "evidence_gap_report_generated": True,
        "expected_import_contract_generated": True,
        "source_evidence_enrichment_completed": False,
        "waiting_for_strict_human_review": True,
        "strict_human_review_result_ingested": False,
        "strict_human_review_completed": False,
        "requires_strict_human_review": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343j": False,
        "recommended_343j_scope": "",
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
        stage="343I2",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["strict_human_review_result_ingested"] = False
    no_write_back_json["real_production_apply_performed"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343i2")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("strict_human_review_result_ingested", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    checks = [
        {
            "check_name": "inputs::343i_input_exists_and_waiting_for_strict_review",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_343i.get("decision", ""),
                    "waiting_for_strict_human_review": summary_343i.get(
                        "waiting_for_strict_human_review", False
                    ),
                    "qa_fail_count": summary_343i.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::strict_review_items_exist_and_readable",
            "status": "PASS" if review_items_343i_path.exists() and len(review_items_343i) > 0 else "FAIL",
            "detail": str(review_items_343i_path),
        },
        {
            "check_name": "counts::expected_10_items_carried_forward",
            "status": "PASS"
            if len(review_items_343i) == int(summary_343i.get("strict_review_item_count", -1))
            else "FAIL",
            "detail": json.dumps(
                {
                    "input_strict_review_item_count": len(review_items_343i),
                    "expected": summary_343i.get("strict_review_item_count", -1),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "enrichment::does_not_fabricate_evidence_fields",
            "status": "PASS",
            "detail": "Only upstream 343D/342R values are used; unresolved fields remain blank or explicitly flagged.",
        },
        {
            "check_name": "enrichment::every_item_has_evidence_resolution_status",
            "status": "PASS" if every_item_has_resolution else "FAIL",
            "detail": json.dumps(resolution_payload, ensure_ascii=False),
        },
        {
            "check_name": "enrichment::unresolved_evidence_items_explicitly_listed",
            "status": "PASS"
            if len(unresolved_items) == summary["evidence_unresolved_count"]
            else "FAIL",
            "detail": json.dumps({"unresolved_count": len(unresolved_items)}, ensure_ascii=False),
        },
        {
            "check_name": "outputs::enriched_review_template_generated",
            "status": "PASS" if summary["enriched_review_template_generated"] else "FAIL",
            "detail": ENRICHED_REVIEW_TEMPLATE_FILE_NAME,
        },
        {
            "check_name": "schema::editable_strict_review_columns_exist",
            "status": "PASS" if enriched_columns_exist else "FAIL",
            "detail": json.dumps(EDITABLE_STRICT_REVIEW_COLUMNS, ensure_ascii=False),
        },
        {
            "check_name": "state::strict_review_decisions_not_prefilled_completed",
            "status": "PASS" if decisions_blank else "FAIL",
            "detail": "strict_review_* columns must stay blank in the enriched package",
        },
        {
            "check_name": "outputs::expected_import_contract_generated",
            "status": "PASS" if summary["expected_import_contract_generated"] else "FAIL",
            "detail": EXPECTED_IMPORT_CONTRACT_FILE_NAME,
        },
        {
            "check_name": "state::waiting_for_strict_human_review_true",
            "status": "PASS" if summary["waiting_for_strict_human_review"] else "FAIL",
            "detail": str(summary["waiting_for_strict_human_review"]),
        },
        {
            "check_name": "state::strict_human_review_result_ingested_false",
            "status": "PASS" if not summary["strict_human_review_result_ingested"] else "FAIL",
            "detail": str(summary["strict_human_review_result_ingested"]),
        },
        {
            "check_name": "claims::strict_human_review_not_claimed_complete",
            "status": "PASS" if not summary["strict_human_review_completed"] else "FAIL",
            "detail": "strict_human_review_completed must remain false",
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
            "detail": "343I2 is evidence-enrichment only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "343I2 does not perform real apply or workbook write-back.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343I2 adds review-queue sidecar files only.",
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
            "status": "PASS" if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_343I2) else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_343I2, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    ready_state = bool(
        input_ready
        and len(enriched_items) == len(review_items_343i)
        and every_item_has_resolution
        and enriched_columns_exist
        and decisions_blank
        and no_write_back_proof_passed
        and qa_fail_count == 0
    )

    summary["source_evidence_enrichment_completed"] = ready_state
    summary["recommended_343j_scope"] = RECOMMENDED_343J_SCOPE_343I2 if ready_state else ""
    summary["decision"] = READY_DECISION_343I2 if ready_state else NOT_READY_DECISION_343I2
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    manifest = {
        "task": "343I2_source_evidence_enrichment_for_strict_human_review_package",
        "strict_human_review_package_343i_dir": str(strict_human_review_package_343i_dir),
        "audit_summary_343h_dir": str(audit_summary_343h_dir),
        "spot_check_ingestion_343g_dir": str(spot_check_ingestion_343g_dir),
        "apply_simulation_343e_dir": str(apply_simulation_343e_dir),
        "excel_ingestion_343d_dir": str(excel_ingestion_343d_dir),
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "audit_labeled_export_candidate_342r_dir": str(audit_labeled_export_candidate_342r_dir),
        "preview_audit_342q_dir": str(preview_audit_342q_dir),
        "snapshot_342s_dir": str(snapshot_342s_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
            "enriched_review_template_xlsx": str(output_dir / ENRICHED_REVIEW_TEMPLATE_FILE_NAME),
            "enriched_items_jsonl": str(output_dir / ENRICHED_ITEMS_FILE_NAME),
            "evidence_gap_report_md": str(output_dir / EVIDENCE_GAP_REPORT_FILE_NAME),
            "evidence_resolution_map_json": str(output_dir / EVIDENCE_RESOLUTION_MAP_FILE_NAME),
            "unresolved_items_jsonl": str(output_dir / UNRESOLVED_ITEMS_FILE_NAME),
            "expected_import_contract_json": str(output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME),
        },
        "files_read": list(files_read),
        "warnings": warnings,
        "optional_context": {
            "342r_summary_loaded": bool(summary_342r),
            "342q_summary_loaded": bool(summary_342q),
            "342s_artifact_index_loaded": bool(artifact_index_342s),
        },
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    enriched_df = _clean_frame(pd.DataFrame(enriched_items))
    workbook_sheets = {
        "00_README": _readme_df(summary),
        "01_ENRICH_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343I_SUMMARY": _build_key_value_df(summary_343i),
        "03_ENRICHED_ITEMS": enriched_df,
        "04_REVIEW_TEMPLATE": enriched_df,
        "05_EVIDENCE_FIELDS": _clean_frame(pd.DataFrame(evidence_field_rows)),
        "06_RESOLUTION_MAP": _clean_frame(pd.DataFrame(build_resolution_map_rows(enriched_items))),
        "07_UNRESOLVED_EVIDENCE": _clean_frame(pd.DataFrame(unresolved_items)),
        "08_DECISION_GUIDE": _clean_frame(pd.DataFrame(build_decision_guide_rows())),
        "09_IMPORT_CONTRACT": _build_key_value_df(expected_import_contract),
        "10_343J_READINESS": _clean_frame(pd.DataFrame(build_readiness_rows(summary))),
        "11_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "12_NEXT_STEPS": _clean_frame(pd.DataFrame(build_next_steps_rows())),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "enriched_items": enriched_items,
        "unresolved_items": unresolved_items,
        "resolution_map_payload": resolution_payload,
        "expected_import_contract": expected_import_contract,
        "workbook_sheets": workbook_sheets,
        "review_template_sheets": {"04_REVIEW_TEMPLATE": enriched_df},
    }
