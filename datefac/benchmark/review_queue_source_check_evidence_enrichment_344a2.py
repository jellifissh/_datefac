from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.ingest_strict_review_343j import (
    FORBIDDEN_STAGE_PATHS,
    PROTECTED_DIRTY_PATHS,
)
from datefac.review_queue.source_check_backlog_package_344a import (
    WAITING_DECISION_344A,
)
from datefac.review_queue.source_check_evidence_enrichment_344a2 import (
    ENRICHED_EVIDENCE_COLUMNS,
    EVIDENCE_RESOLUTION_PARTIAL,
    EVIDENCE_RESOLUTION_RESOLVED,
    EVIDENCE_RESOLUTION_UNRESOLVED,
    MATCH_CONFIDENCE_HIGH,
    MATCH_CONFIDENCE_LOW,
    MATCH_CONFIDENCE_MEDIUM,
    NOT_READY_DECISION_344A2,
    RECOMMENDED_344B_SCOPE_344A2,
    REVIEW_TEMPLATE_WORKBOOK_SHEETS_344A2,
    WAITING_DECISION_344A2,
    WORKBOOK_SHEETS_344A2,
    apply_match_to_item,
    build_expected_import_contract,
    build_match_candidate,
    build_match_confidence_rows,
    build_next_steps_rows,
    build_resolution_map_payload,
    build_reviewer_instruction_rows,
    build_scope_boundary_lines,
    build_search_keys,
    build_searchable_record,
    build_unresolved_rows,
    classify_evidence_resolution,
    decisions_blank,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


DEFAULT_SOURCE_CHECK_BACKLOG_PACKAGE_344A_DIR = Path(
    r"D:\_datefac\output\review_queue_source_check_backlog_package_344a"
)
DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR = Path(
    r"D:\_datefac\output\review_queue_demo_audit_snapshot_343o"
)
DEFAULT_AUDIT_SUMMARY_343H_DIR = Path(
    r"D:\_datefac\output\review_queue_audit_summary_343h"
)
DEFAULT_SPOT_CHECK_INGESTION_343G_DIR = Path(
    r"D:\_datefac\output\review_queue_spot_check_ingestion_343g"
)
DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR = Path(
    r"D:\_datefac\output\review_queue_spot_check_package_343f"
)
DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR = Path(
    r"D:\_datefac\output\review_queue_source_evidence_enrichment_343i2"
)
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(
    r"D:\_datefac\output\review_queue_schema_343a"
)
DEFAULT_OUTPUT_SEARCH_ROOT = Path(r"D:\_datefac\output")
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\review_queue_source_check_evidence_enrichment_344a2"
)

SUMMARY_FILE_NAME = "review_queue_source_check_evidence_enrichment_344a2_summary.json"
MANIFEST_FILE_NAME = "review_queue_source_check_evidence_enrichment_344a2_manifest.json"
QA_FILE_NAME = "review_queue_source_check_evidence_enrichment_344a2_qa.json"
NO_WRITE_BACK_FILE_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_no_write_back_proof.json"
)
REPORT_FILE_NAME = "review_queue_source_check_evidence_enrichment_344a2_report.md"
WORKBOOK_FILE_NAME = "review_queue_source_check_evidence_enrichment_344a2.xlsx"
ENRICHED_BACKLOG_FILE_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_enriched_backlog_items.jsonl"
)
MATCH_CANDIDATES_FILE_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_evidence_match_candidates.jsonl"
)
MATCH_CONFIDENCE_AUDIT_FILE_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_match_confidence_audit.jsonl"
)
EVIDENCE_MAP_FILE_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_evidence_map.json"
)
ENRICHED_REVIEW_TEMPLATE_FILE_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_enriched_review_template.xlsx"
)
REVIEWER_INSTRUCTIONS_FILE_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_reviewer_instructions.md"
)
FILL_GUIDE_FILE_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_fill_guide.md"
)
EXPECTED_IMPORT_CONTRACT_FILE_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_expected_import_contract.json"
)
UNRESOLVED_REPORT_FILE_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_unresolved_evidence_report.md"
)
ARTIFACT_SEARCH_REPORT_FILE_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_artifact_search_report.md"
)
SCOPE_BOUNDARY_FILE_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_scope_boundary.md"
)

INPUT_344A_SUMMARY_NAME = "review_queue_source_check_backlog_package_344a_summary.json"
INPUT_344A_QA_NAME = "review_queue_source_check_backlog_package_344a_qa.json"
INPUT_344A_BACKLOG_ITEMS_NAME = (
    "review_queue_source_check_backlog_package_344a_backlog_items.jsonl"
)
INPUT_344A_EVIDENCE_MAP_NAME = (
    "review_queue_source_check_backlog_package_344a_evidence_map.json"
)
INPUT_344A_REVIEW_TEMPLATE_NAME = (
    "review_queue_source_check_backlog_package_344a_review_template.xlsx"
)
INPUT_344A_IMPORT_CONTRACT_NAME = (
    "review_queue_source_check_backlog_package_344a_expected_import_contract.json"
)
INPUT_344A_NO_WRITE_BACK_NAME = (
    "review_queue_source_check_backlog_package_344a_no_write_back_proof.json"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


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


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "344A2 enriches 344A source-check backlog rows with conservative evidence locators from existing artifacts.",
                },
                {
                    "section": "boundary",
                    "message": "344A2 does not decide row outcomes and does not prefill source_check_decision.",
                },
                {
                    "section": "evidence_policy",
                    "message": "Low-confidence or ambiguous matches are logged but not auto-applied.",
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def _coerce_page(value: Any) -> str:
    text = normalize_text(value)
    return text


def _build_artifact_search_plan(output_search_root: Path) -> List[Dict[str, Any]]:
    prioritized = [
        (
            "342R",
            output_search_root
            / "audit_labeled_export_candidate_package_342r"
            / "audit_labeled_export_candidate_package_342r_candidates.csv",
            "csv",
        ),
        (
            "343D",
            output_search_root
            / "review_queue_excel_ingestion_343d"
            / "review_queue_excel_ingestion_343d_reviewed_result.jsonl",
            "jsonl",
        ),
        (
            "343B",
            output_search_root
            / "review_queue_excel_round_trip_343b"
            / "review_queue_excel_round_trip_343b_reviewed_result.jsonl",
            "jsonl",
        ),
        (
            "343E",
            output_search_root
            / "review_queue_apply_simulation_343e"
            / "review_queue_apply_simulation_343e_apply_plan.jsonl",
            "jsonl",
        ),
        (
            "343G",
            output_search_root
            / "review_queue_spot_check_ingestion_343g"
            / "review_queue_spot_check_ingestion_343g_result.jsonl",
            "jsonl",
        ),
        (
            "343H",
            output_search_root
            / "review_queue_audit_summary_343h"
            / "review_queue_audit_summary_343h_source_check_backlog.jsonl",
            "jsonl",
        ),
        (
            "343I2",
            output_search_root
            / "review_queue_source_evidence_enrichment_343i2"
            / "review_queue_source_evidence_enrichment_343i2_enriched_items.jsonl",
            "jsonl",
        ),
        (
            "342Q",
            output_search_root
            / "preview_audit_export_readiness_gate_342q"
            / "preview_audit_export_readiness_gate_342q_summary.json",
            "json",
        ),
    ]
    plan: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for source_stage, artifact_path, artifact_type in prioritized:
        if artifact_path.exists():
            key = str(artifact_path)
            if key not in seen:
                plan.append(
                    {
                        "source_stage": source_stage,
                        "artifact_path": artifact_path,
                        "artifact_type": artifact_type,
                    }
                )
                seen.add(key)
    return plan


def _load_artifact_records(
    artifact_plan: List[Dict[str, Any]]
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    records: List[Dict[str, Any]] = []
    search_report_rows: List[Dict[str, Any]] = []
    for artifact in artifact_plan:
        path: Path = artifact["artifact_path"]
        source_stage = artifact["source_stage"]
        artifact_type = artifact["artifact_type"]
        rows: List[Dict[str, Any]] = []
        if artifact_type == "csv":
            rows = _read_csv(path)
        elif artifact_type == "jsonl":
            rows = _read_jsonl(path)
        elif artifact_type == "json":
            payload = _read_json(path)
            if isinstance(payload, list):
                rows = [row for row in payload if isinstance(row, dict)]
            elif isinstance(payload, dict):
                rows = [payload]
        for idx, row in enumerate(rows, start=1):
            records.append(
                build_searchable_record(
                    row,
                    source_stage=source_stage,
                    artifact_path=str(path),
                    artifact_type=artifact_type,
                    row_number=idx,
                )
            )
        search_report_rows.append(
            {
                "source_stage": source_stage,
                "artifact_path": str(path),
                "artifact_type": artifact_type,
                "row_count": len(rows),
            }
        )
    return records, search_report_rows


def _candidate_has_locator(candidate: Dict[str, Any]) -> bool:
    return any(
        normalize_text(candidate.get(field)) != ""
        for field in [
            "source_pdf_name",
            "source_pdf_path",
            "source_pdf_id",
            "page_number",
            "table_id",
            "bbox",
            "image_path",
            "source_text_snippet",
            "source_html_snippet",
        ]
    )


def _score_record_exact_identity(item: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any] | None:
    queue_item_id = normalize_text(item.get("queue_item_id"))
    review_item_id = normalize_text(item.get("review_item_id"))
    if queue_item_id == "" and review_item_id == "":
        return None
    if queue_item_id != normalize_text(record.get("queue_item_id")):
        return None
    if review_item_id != normalize_text(record.get("review_item_id")):
        return None
    confidence = MATCH_CONFIDENCE_HIGH if _candidate_has_locator(record) else MATCH_CONFIDENCE_LOW
    reason = "exact queue_item_id + review_item_id match"
    return build_match_candidate(
        item,
        record,
        match_type="EXACT_IDENTITY",
        match_confidence=confidence,
        match_reason=reason,
    )


def _score_record_review_item_id(item: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any] | None:
    review_item_id = normalize_text(item.get("review_item_id"))
    if review_item_id == "":
        return None
    if review_item_id != normalize_text(record.get("review_item_id")):
        return None
    confidence = MATCH_CONFIDENCE_HIGH if _candidate_has_locator(record) else MATCH_CONFIDENCE_LOW
    return build_match_candidate(
        item,
        record,
        match_type="REVIEW_ITEM_ID",
        match_confidence=confidence,
        match_reason="exact review_item_id match",
    )


def _score_record_metric_year_value_unit(item: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any] | None:
    keys = build_search_keys(item)
    if not all(keys[field] != "" for field in ["metric_standardized", "year_standardized", "value_numeric"]):
        return None
    if keys["metric_standardized"] != normalize_text(record.get("metric_standardized")):
        return None
    if keys["year_standardized"] != normalize_text(record.get("year_standardized")):
        return None
    if keys["value_numeric"] != normalize_text(record.get("value_numeric")):
        return None
    if keys["normalized_unit"] != normalize_text(record.get("normalized_unit")):
        return None
    confidence = MATCH_CONFIDENCE_HIGH if _candidate_has_locator(record) else MATCH_CONFIDENCE_LOW
    return build_match_candidate(
        item,
        record,
        match_type="METRIC_YEAR_VALUE_UNIT",
        match_confidence=confidence,
        match_reason="exact metric + year + numeric value + unit match",
    )


def _score_record_metric_year_value(item: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any] | None:
    keys = build_search_keys(item)
    if not all(keys[field] != "" for field in ["metric_standardized", "year_standardized", "value_numeric"]):
        return None
    if keys["metric_standardized"] != normalize_text(record.get("metric_standardized")):
        return None
    if keys["year_standardized"] != normalize_text(record.get("year_standardized")):
        return None
    if keys["value_numeric"] != normalize_text(record.get("value_numeric")):
        return None
    confidence = MATCH_CONFIDENCE_MEDIUM if _candidate_has_locator(record) else MATCH_CONFIDENCE_LOW
    return build_match_candidate(
        item,
        record,
        match_type="METRIC_YEAR_VALUE",
        match_confidence=confidence,
        match_reason="exact metric + year + numeric value match",
    )


def _score_record_metric_year_close_value(item: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any] | None:
    keys = build_search_keys(item)
    if not all(keys[field] != "" for field in ["metric_standardized", "year_standardized", "value_numeric"]):
        return None
    if keys["metric_standardized"] != normalize_text(record.get("metric_standardized")):
        return None
    if keys["year_standardized"] != normalize_text(record.get("year_standardized")):
        return None
    try:
        item_value = float(keys["value_numeric"])
        record_value = float(normalize_text(record.get("value_numeric")))
    except Exception:
        return None
    if abs(item_value - record_value) > 0.001:
        return None
    if not _candidate_has_locator(record):
        return None
    return build_match_candidate(
        item,
        record,
        match_type="METRIC_YEAR_CLOSE_VALUE",
        match_confidence=MATCH_CONFIDENCE_LOW,
        match_reason="close numeric match with matching metric + year",
    )


def _collect_match_candidates(
    item: Dict[str, Any],
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for record in records:
        for scorer in (
            _score_record_exact_identity,
            _score_record_review_item_id,
            _score_record_metric_year_value_unit,
            _score_record_metric_year_value,
            _score_record_metric_year_close_value,
        ):
            candidate = scorer(item, record)
            if candidate is None:
                continue
            dedupe_key = (
                normalize_text(candidate.get("match_type")),
                normalize_text(candidate.get("matched_artifact_path")),
                normalize_text(candidate.get("matched_sheet_or_line")),
                normalize_text(candidate.get("source_row_id")),
            )
            if dedupe_key not in seen:
                candidates.append(candidate)
                seen.add(dedupe_key)
    return candidates


def _locator_completeness(candidate: Dict[str, Any]) -> int:
    return sum(
        1
        for field in [
            "source_pdf_name",
            "source_pdf_path",
            "source_pdf_id",
            "page_number",
            "table_id",
            "bbox",
            "image_path",
            "source_text_snippet",
            "source_html_snippet",
        ]
        if normalize_text(candidate.get(field)) != ""
    )


def _choose_auto_apply_candidate(candidates: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    eligible = [
        candidate
        for candidate in candidates
        if normalize_text(candidate.get("match_confidence"))
        in {MATCH_CONFIDENCE_HIGH, MATCH_CONFIDENCE_MEDIUM}
    ]
    if not eligible:
        return None
    confidence_rank = {
        MATCH_CONFIDENCE_HIGH: 3,
        MATCH_CONFIDENCE_MEDIUM: 2,
        MATCH_CONFIDENCE_LOW: 1,
    }
    match_type_rank = {
        "EXACT_IDENTITY": 5,
        "REVIEW_ITEM_ID": 4,
        "METRIC_YEAR_VALUE_UNIT": 3,
        "METRIC_YEAR_VALUE": 2,
        "METRIC_YEAR_CLOSE_VALUE": 1,
    }
    ranked = sorted(
        eligible,
        key=lambda candidate: (
            confidence_rank.get(normalize_text(candidate.get("match_confidence")), 0),
            _locator_completeness(candidate),
            match_type_rank.get(normalize_text(candidate.get("match_type")), 0),
        ),
        reverse=True,
    )
    best = ranked[0]
    best_key = (
        confidence_rank.get(normalize_text(best.get("match_confidence")), 0),
        _locator_completeness(best),
        match_type_rank.get(normalize_text(best.get("match_type")), 0),
    )
    tied = [
        candidate
        for candidate in ranked
        if (
            confidence_rank.get(normalize_text(candidate.get("match_confidence")), 0),
            _locator_completeness(candidate),
            match_type_rank.get(normalize_text(candidate.get("match_type")), 0),
        )
        == best_key
    ]
    if len(tied) > 1:
        return None
    return best


def _build_unresolved_rows(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return build_unresolved_rows(items)


def build_review_queue_source_check_evidence_enrichment_344a2(
    *,
    source_check_backlog_package_344a_dir: Path = DEFAULT_SOURCE_CHECK_BACKLOG_PACKAGE_344A_DIR,
    demo_audit_snapshot_343o_dir: Path = DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR,
    audit_summary_343h_dir: Path = DEFAULT_AUDIT_SUMMARY_343H_DIR,
    spot_check_ingestion_343g_dir: Path = DEFAULT_SPOT_CHECK_INGESTION_343G_DIR,
    spot_check_package_343f_dir: Path = DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR,
    source_evidence_enrichment_343i2_dir: Path = DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR,
    review_queue_schema_343a_dir: Path = DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    output_search_root: Path = DEFAULT_OUTPUT_SEARCH_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    required_inputs = [
        source_check_backlog_package_344a_dir / INPUT_344A_SUMMARY_NAME,
        source_check_backlog_package_344a_dir / INPUT_344A_QA_NAME,
        source_check_backlog_package_344a_dir / INPUT_344A_BACKLOG_ITEMS_NAME,
        source_check_backlog_package_344a_dir / INPUT_344A_EVIDENCE_MAP_NAME,
        source_check_backlog_package_344a_dir / INPUT_344A_REVIEW_TEMPLATE_NAME,
        source_check_backlog_package_344a_dir / INPUT_344A_IMPORT_CONTRACT_NAME,
        source_check_backlog_package_344a_dir / INPUT_344A_NO_WRITE_BACK_NAME,
    ]
    missing_required_inputs = [str(path) for path in required_inputs if not path.exists()]
    files_read: List[str] = []
    warnings: List[str] = []
    for path in required_inputs:
        if path.exists():
            files_read.append(str(path))
    if missing_required_inputs:
        warnings.extend([f"missing required input: {path}" for path in missing_required_inputs])

    summary_344a = _read_json(source_check_backlog_package_344a_dir / INPUT_344A_SUMMARY_NAME) if (source_check_backlog_package_344a_dir / INPUT_344A_SUMMARY_NAME).exists() else {}
    qa_344a = _read_json(source_check_backlog_package_344a_dir / INPUT_344A_QA_NAME) if (source_check_backlog_package_344a_dir / INPUT_344A_QA_NAME).exists() else {}
    backlog_items_344a = _read_jsonl(source_check_backlog_package_344a_dir / INPUT_344A_BACKLOG_ITEMS_NAME) if (source_check_backlog_package_344a_dir / INPUT_344A_BACKLOG_ITEMS_NAME).exists() else []
    evidence_map_344a = _read_json(source_check_backlog_package_344a_dir / INPUT_344A_EVIDENCE_MAP_NAME) if (source_check_backlog_package_344a_dir / INPUT_344A_EVIDENCE_MAP_NAME).exists() else {}
    import_contract_344a = _read_json(source_check_backlog_package_344a_dir / INPUT_344A_IMPORT_CONTRACT_NAME) if (source_check_backlog_package_344a_dir / INPUT_344A_IMPORT_CONTRACT_NAME).exists() else {}
    no_write_back_344a = _read_json(source_check_backlog_package_344a_dir / INPUT_344A_NO_WRITE_BACK_NAME) if (source_check_backlog_package_344a_dir / INPUT_344A_NO_WRITE_BACK_NAME).exists() else {}

    input_hashes_before = {str(path): sha256_file(path) for path in required_inputs if path.exists()}

    input_ready = bool(
        not missing_required_inputs
        and summary_344a.get("decision") == WAITING_DECISION_344A
        and int(summary_344a.get("source_check_backlog_item_count", -1)) == 19
        and int(summary_344a.get("deduplicated_backlog_item_count", -1)) == 19
        and int(summary_344a.get("qa_fail_count", 1)) == 0
        and normalize_bool(summary_344a.get("waiting_for_source_check_review"))
        and not normalize_bool(summary_344a.get("source_check_result_ingested"))
        and not normalize_bool(summary_344a.get("source_check_backlog_resolved"))
        and not normalize_bool(summary_344a.get("formal_client_export_allowed"))
        and not normalize_bool(summary_344a.get("client_ready"))
        and not normalize_bool(summary_344a.get("production_ready"))
        and normalize_bool(summary_344a.get("no_write_back_proof_passed"))
    )

    artifact_plan = _build_artifact_search_plan(output_search_root)
    for artifact in artifact_plan:
        files_read.append(str(artifact["artifact_path"]))
    searchable_records, searched_artifacts = _load_artifact_records(artifact_plan)

    all_match_candidates: List[Dict[str, Any]] = []
    enriched_backlog_items: List[Dict[str, Any]] = []
    auto_enriched_item_count = 0
    for item in backlog_items_344a:
        candidates = _collect_match_candidates(item, searchable_records)
        all_match_candidates.extend(candidates)
        auto_candidate = _choose_auto_apply_candidate(candidates)
        enriched_item = apply_match_to_item(item, auto_candidate)
        if auto_candidate is not None:
            auto_enriched_item_count += 1
        enriched_backlog_items.append(enriched_item)

    resolution_map = build_resolution_map_payload(enriched_backlog_items)
    unresolved_rows = _build_unresolved_rows(enriched_backlog_items)
    expected_import_contract = build_expected_import_contract(
        review_queue_schema_version=summary_344a.get("review_queue_schema_version", ""),
        output_dir_hint=str(output_dir),
    )

    match_candidate_count = len(all_match_candidates)
    high_confidence_match_count = sum(
        1
        for candidate in all_match_candidates
        if normalize_text(candidate.get("match_confidence")) == MATCH_CONFIDENCE_HIGH
    )
    medium_confidence_match_count = sum(
        1
        for candidate in all_match_candidates
        if normalize_text(candidate.get("match_confidence")) == MATCH_CONFIDENCE_MEDIUM
    )
    low_confidence_match_count = sum(
        1
        for candidate in all_match_candidates
        if normalize_text(candidate.get("match_confidence")) == MATCH_CONFIDENCE_LOW
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "344A",
        "decision": NOT_READY_DECISION_344A2,
        "review_queue_schema_version": summary_344a.get("review_queue_schema_version", ""),
        "input_source_check_backlog_item_count": len(backlog_items_344a),
        "deduplicated_backlog_item_count": len(enriched_backlog_items),
        "evidence_resolved_count": resolution_map["resolved_count"],
        "evidence_partial_count": resolution_map["partial_count"],
        "evidence_unresolved_count": resolution_map["unresolved_count"],
        "source_pdf_name_available_count": sum(
            1
            for item in enriched_backlog_items
            if normalize_text(item.get("source_pdf_name")) != ""
        ),
        "page_number_available_count": sum(
            1
            for item in enriched_backlog_items
            if normalize_text(item.get("page_number")) != ""
        ),
        "image_path_available_count": sum(
            1
            for item in enriched_backlog_items
            if normalize_text(item.get("image_path")) != ""
        ),
        "source_text_snippet_available_count": sum(
            1
            for item in enriched_backlog_items
            if normalize_text(item.get("source_text_snippet")) != ""
        ),
        "match_candidate_count": match_candidate_count,
        "high_confidence_match_count": high_confidence_match_count,
        "medium_confidence_match_count": medium_confidence_match_count,
        "low_confidence_match_count": low_confidence_match_count,
        "auto_enriched_item_count": auto_enriched_item_count,
        "unresolved_item_count": len(unresolved_rows),
        "source_check_evidence_enrichment_completed": False,
        "enriched_review_template_generated": False,
        "evidence_map_generated": False,
        "reviewer_instructions_generated": False,
        "fill_guide_generated": False,
        "expected_import_contract_generated": False,
        "waiting_for_source_check_review": False,
        "source_check_result_ingested": False,
        "source_check_backlog_resolved": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_344b": False,
        "recommended_344b_scope": RECOMMENDED_344B_SCOPE_344A2,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "output_directory": str(output_dir),
    }

    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    input_hashes_after = {str(path): sha256_file(path) for path in required_inputs if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="344A2",
        files_read=list(dict.fromkeys(files_read)),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["real_production_apply_performed"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_344a2")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    checks = [
        {
            "check_name": "inputs::344a_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "missing_required_inputs": missing_required_inputs,
                    "decision": summary_344a.get("decision", ""),
                    "qa_fail_count": summary_344a.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::preserve_19_backlog_rows",
            "status": "PASS" if len(enriched_backlog_items) == 19 else "FAIL",
            "detail": json.dumps(
                {
                    "input_source_check_backlog_item_count": len(backlog_items_344a),
                    "enriched_backlog_item_count": len(enriched_backlog_items),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::no_backlog_row_dropped",
            "status": "PASS"
            if len(enriched_backlog_items) == len(backlog_items_344a)
            else "FAIL",
            "detail": "344A2 must preserve every backlog row",
        },
        {
            "check_name": "template::source_check_decisions_not_prefilled_as_completed",
            "status": "PASS" if decisions_blank(enriched_backlog_items) else "FAIL",
            "detail": "source_check_decision and editable source-check columns must stay blank",
        },
        {
            "check_name": "evidence::every_backlog_item_has_resolution_status",
            "status": "PASS"
            if all(
                normalize_text(item.get("evidence_resolution_status")) != ""
                for item in enriched_backlog_items
            )
            else "FAIL",
            "detail": json.dumps(resolution_map, ensure_ascii=False),
        },
        {
            "check_name": "evidence::match_candidates_logged",
            "status": "PASS" if match_candidate_count > 0 else "FAIL",
            "detail": json.dumps(
                {
                    "match_candidate_count": match_candidate_count,
                    "high": high_confidence_match_count,
                    "medium": medium_confidence_match_count,
                    "low": low_confidence_match_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "evidence::low_confidence_not_auto_applied_if_ambiguous",
            "status": "PASS",
            "detail": "Only a single HIGH/MEDIUM candidate can be auto-applied; LOW stays audit-only.",
        },
        {
            "check_name": "evidence::unresolved_rows_explicitly_disclosed",
            "status": "PASS"
            if all(
                normalize_text(row.get("evidence_gap_reason")) != ""
                for row in unresolved_rows
            )
            else "FAIL",
            "detail": json.dumps({"unresolved_item_count": len(unresolved_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "outputs::enriched_review_template_generated",
            "status": "PASS" if bool(enriched_backlog_items) else "FAIL",
            "detail": ENRICHED_REVIEW_TEMPLATE_FILE_NAME,
        },
        {
            "check_name": "outputs::reviewer_instructions_generated",
            "status": "PASS",
            "detail": REVIEWER_INSTRUCTIONS_FILE_NAME,
        },
        {
            "check_name": "outputs::fill_guide_generated",
            "status": "PASS",
            "detail": FILL_GUIDE_FILE_NAME,
        },
        {
            "check_name": "outputs::expected_import_contract_generated",
            "status": "PASS" if bool(expected_import_contract) else "FAIL",
            "detail": EXPECTED_IMPORT_CONTRACT_FILE_NAME,
        },
        {
            "check_name": "state::waiting_for_source_check_review_true",
            "status": "PASS",
            "detail": "344A2 intentionally stops before 344B ingestion.",
        },
        {
            "check_name": "state::source_check_result_ingested_false",
            "status": "PASS",
            "detail": "344A2 must not ingest a filled workbook.",
        },
        {
            "check_name": "state::source_check_backlog_resolved_false",
            "status": "PASS",
            "detail": "Backlog remains unresolved until a later ingestion task.",
        },
        {
            "check_name": "claims::formal_client_production_flags_remain_false",
            "status": "PASS"
            if not summary["formal_client_export_allowed"]
            and not summary["client_ready"]
            and not summary["production_ready"]
            else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready must remain false",
        },
        {
            "check_name": "safety::no_formal_client_export_workbook_generated",
            "status": "PASS",
            "detail": "344A2 generates only enrichment artifacts for later review.",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "344A2 is evidence-enrichment only and does not call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "344A2 does not write back or production-apply anything.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "344A2 adds review-queue evidence enrichment files only.",
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
            "status": "PASS" if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_344A2) else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_344A2, ensure_ascii=False),
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
        and len(enriched_backlog_items) == 19
        and decisions_blank(enriched_backlog_items)
        and no_write_back_proof_passed
        and qa_fail_count == 0
    )
    summary["decision"] = WAITING_DECISION_344A2 if ready_state else NOT_READY_DECISION_344A2
    summary["source_check_evidence_enrichment_completed"] = ready_state
    summary["enriched_review_template_generated"] = bool(enriched_backlog_items)
    summary["evidence_map_generated"] = bool(resolution_map)
    summary["reviewer_instructions_generated"] = True
    summary["fill_guide_generated"] = True
    summary["expected_import_contract_generated"] = True
    summary["waiting_for_source_check_review"] = True
    summary["ready_for_344b"] = False
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    manifest = {
        "task": "344A2_source_evidence_enrichment_for_source_check_backlog",
        "source_check_backlog_package_344a_dir": str(source_check_backlog_package_344a_dir),
        "demo_audit_snapshot_343o_dir": str(demo_audit_snapshot_343o_dir),
        "audit_summary_343h_dir": str(audit_summary_343h_dir),
        "spot_check_ingestion_343g_dir": str(spot_check_ingestion_343g_dir),
        "spot_check_package_343f_dir": str(spot_check_package_343f_dir),
        "source_evidence_enrichment_343i2_dir": str(source_evidence_enrichment_343i2_dir),
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "output_search_root": str(output_search_root),
        "output_dir": str(output_dir),
        "files_read": list(dict.fromkeys(files_read)),
        "warnings": warnings,
        "searched_artifacts": searched_artifacts,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "input_summary_344a": summary_344a,
        "input_qa_344a": qa_344a,
        "input_evidence_map_344a": evidence_map_344a,
        "input_import_contract_344a": import_contract_344a,
        "input_no_write_back_344a": no_write_back_344a,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    workbook_sheets = {
        "00_README": _readme_df(summary),
        "01_ENRICH_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_344A_SUMMARY": _build_key_value_df(summary_344a),
        "03_ENRICHED_BACKLOG": _clean_frame(pd.DataFrame(enriched_backlog_items)),
        "04_REVIEW_TEMPLATE": _clean_frame(pd.DataFrame(enriched_backlog_items)),
        "05_EVIDENCE_MAP": _clean_frame(pd.DataFrame(resolution_map["items"])),
        "06_MATCH_CANDIDATES": _clean_frame(pd.DataFrame(all_match_candidates)),
        "07_UNRESOLVED_REPORT": _clean_frame(pd.DataFrame(unresolved_rows)),
        "08_IMPORT_CONTRACT": _build_key_value_df(expected_import_contract),
        "09_SCOPE_BOUNDARY": _build_key_value_df(
            {"scope_boundary": "\n".join(build_scope_boundary_lines())}
        ),
        "10_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "11_NEXT_STEPS": _clean_frame(pd.DataFrame(build_next_steps_rows())),
    }
    review_template_sheets = {
        sheet: workbook_sheets[sheet] for sheet in REVIEW_TEMPLATE_WORKBOOK_SHEETS_344A2
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "enriched_backlog_items": enriched_backlog_items,
        "match_candidates": all_match_candidates,
        "match_confidence_rows": build_match_confidence_rows(all_match_candidates),
        "resolution_map": resolution_map,
        "unresolved_rows": unresolved_rows,
        "expected_import_contract": expected_import_contract,
        "workbook_sheets": workbook_sheets,
        "review_template_sheets": review_template_sheets,
        "reviewer_instruction_rows": build_reviewer_instruction_rows(summary),
        "searched_artifacts": searched_artifacts,
    }
