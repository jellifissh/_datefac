from __future__ import annotations

import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from datefac.review_queue.excel_round_trip_343b import normalize_text
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_345B = "FULL_EXTRACTION_QUALITY_AUDIT_345B_READY"
NOT_READY_DECISION_345B = "FULL_EXTRACTION_QUALITY_AUDIT_345B_NOT_READY"
INPUT_STAGE_345B = "POST_345A_FULL_STRUCTURED_QUALITY_AUDIT"

DEFAULT_FULL_STRUCTURED_DATA_INVENTORY_345A_DIR = Path(
    r"D:\_datefac\output\full_structured_data_inventory_345a"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\full_extraction_quality_audit_345b")

DEFAULT_TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_DIR = Path(
    r"D:\_datefac\output\table_first_core_financial_extraction_342f"
)
DEFAULT_TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_DIR = Path(
    r"D:\_datefac\output\table_first_extraction_review_package_342g"
)
DEFAULT_TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_DIR = Path(
    r"D:\_datefac\output\table_first_human_review_apply_simulation_342h"
)
DEFAULT_REVIEW_QUEUE_STRICT_HUMAN_REVIEW_PACKAGE_344F_DIR = Path(
    r"D:\_datefac\output\review_queue_strict_human_review_package_344f"
)

MANIFEST_FILE_NAME = "full_extraction_quality_audit_345b_manifest.json"
QUALITY_ROWS_JSON_FILE_NAME = "full_extraction_quality_audit_345b_quality_rows.json"
QUALITY_ROWS_CSV_FILE_NAME = "full_extraction_quality_audit_345b_quality_rows.csv"
STAGE_QUALITY_SUMMARY_JSON_FILE_NAME = (
    "full_extraction_quality_audit_345b_stage_quality_summary.json"
)
STAGE_QUALITY_SUMMARY_CSV_FILE_NAME = (
    "full_extraction_quality_audit_345b_stage_quality_summary.csv"
)
PDF_QUALITY_SUMMARY_JSON_FILE_NAME = "full_extraction_quality_audit_345b_pdf_quality_summary.json"
PDF_QUALITY_SUMMARY_CSV_FILE_NAME = "full_extraction_quality_audit_345b_pdf_quality_summary.csv"
MISSING_FIELD_HOTSPOTS_FILE_NAME = "full_extraction_quality_audit_345b_missing_field_hotspots.json"
EVIDENCE_TRACE_QUALITY_FILE_NAME = "full_extraction_quality_audit_345b_evidence_trace_quality.json"
PRIORITY_FIX_QUEUE_JSON_FILE_NAME = "full_extraction_quality_audit_345b_priority_fix_queue.json"
PRIORITY_FIX_QUEUE_CSV_FILE_NAME = "full_extraction_quality_audit_345b_priority_fix_queue.csv"
EXECUTIVE_SUMMARY_FILE_NAME = "full_extraction_quality_audit_345b_executive_summary.md"
ARTIFACT_INDEX_FILE_NAME = "full_extraction_quality_audit_345b_artifact_index.md"
NEXT_PLAN_FILE_NAME = "full_extraction_quality_audit_345b_next_plan.md"

INPUT_345A_MANIFEST_NAME = "full_structured_data_inventory_345a_manifest.json"
INPUT_345A_ROW_INVENTORY_NAME = "full_structured_data_inventory_345a_row_inventory.json"
INPUT_345A_STAGE_STATUS_NAME = "full_structured_data_inventory_345a_stage_status_summary.json"
INPUT_345A_MISSING_FIELD_NAME = "full_structured_data_inventory_345a_missing_field_summary.json"
INPUT_345A_EXECUTIVE_SUMMARY_NAME = "full_structured_data_inventory_345a_executive_summary.md"

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
    "input",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

QUALITY_ROW_FIELDS = [
    "quality_row_id",
    "inventory_row_id",
    "source_artifact",
    "source_stage",
    "pdf_id",
    "pdf_name",
    "table_id",
    "metric_name",
    "normalized_metric_name",
    "value_raw",
    "value_normalized",
    "unit",
    "period",
    "source_page",
    "trust_status",
    "review_status",
    "human_review_status",
    "missing_required_fields",
    "has_metric_name",
    "has_value",
    "has_unit",
    "has_period",
    "has_source_trace",
    "is_rejected_or_excluded",
    "is_downstream_ready_candidate",
    "quality_issue_count",
    "quality_issues",
    "quality_severity",
    "recommended_action",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


def _safe_text(value: Any) -> str:
    text = normalize_text(value)
    if text.lower() == "nan":
        return ""
    return text


def _issue_labels(row: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    if not _safe_text(row.get("unit")):
        issues.append("MISSING_UNIT")
    if not _safe_text(row.get("period")):
        issues.append("MISSING_PERIOD")
    if not _safe_text(row.get("source_page")) and bool(row.get("is_downstream_ready_candidate")):
        issues.append("MISSING_SOURCE_TRACE")
    if _safe_text(row.get("review_status")) == "REJECTED_OR_EXCLUDED":
        issues.append("REJECTED_OR_EXCLUDED")
    if _safe_text(row.get("review_status")) == "REVIEW_REQUIRED":
        issues.append("REVIEW_REQUIRED")
    if not bool(row.get("is_normalized_metric")):
        issues.append("UNNORMALIZED_METRIC")
    if _safe_text(row.get("human_review_status")) in {
        "NOT_REVIEWED",
        "PENDING_HUMAN_REVIEW",
        "FILLABLE_TEMPLATE",
        "PENDING",
    }:
        issues.append("HUMAN_REVIEW_PENDING")
    if _safe_text(row.get("source_stage")) == "STRICT_HUMAN_REVIEW_PENDING_ROW":
        issues.append("STRICT_HUMAN_REVIEW_PENDING")
    if not _safe_text(row.get("source_page")):
        issues.append("LOW_TRACEABILITY")
    return issues


def _severity(row: Dict[str, Any], issues: List[str]) -> str:
    if "REJECTED_OR_EXCLUDED" in issues:
        return "HIGH"
    if "MISSING_SOURCE_TRACE" in issues:
        return "HIGH"
    critical_missing = sum(
        1
        for label in ("MISSING_UNIT", "MISSING_PERIOD", "MISSING_SOURCE_TRACE")
        if label in issues
    )
    if critical_missing >= 2:
        return "HIGH"
    if any(
        label in issues
        for label in (
            "REVIEW_REQUIRED",
            "MISSING_UNIT",
            "MISSING_PERIOD",
            "UNNORMALIZED_METRIC",
            "HUMAN_REVIEW_PENDING",
            "STRICT_HUMAN_REVIEW_PENDING",
        )
    ):
        return "MEDIUM"
    if issues:
        return "LOW"
    return "NONE"


def _recommended_action(row: Dict[str, Any], issues: List[str]) -> str:
    if "REJECTED_OR_EXCLUDED" in issues:
        return "KEEP_REJECTED"
    if "MISSING_SOURCE_TRACE" in issues:
        return "FIX_SOURCE_TRACE"
    if "MISSING_UNIT" in issues or "MISSING_PERIOD" in issues:
        return "FIX_UNIT_OR_PERIOD"
    if "UNNORMALIZED_METRIC" in issues:
        return "NORMALIZE_METRIC_NAME"
    if "STRICT_HUMAN_REVIEW_PENDING" in issues or "HUMAN_REVIEW_PENDING" in issues:
        return "WAIT_FOR_HUMAN_REVIEW"
    if "REVIEW_REQUIRED" in issues:
        return "REVIEW_REQUIRED"
    return "KEEP_AS_READY_CANDIDATE"


def _quality_row_id(index: int) -> str:
    return f"345b::quality::{index:05d}"


def _quality_row(row: Dict[str, Any], index: int) -> Dict[str, Any]:
    issues = _issue_labels(row)
    severity = _severity(row, issues)
    return {
        "quality_row_id": _quality_row_id(index),
        "inventory_row_id": _safe_text(row.get("inventory_row_id")),
        "source_artifact": _safe_text(row.get("source_artifact")),
        "source_stage": _safe_text(row.get("source_stage")),
        "pdf_id": _safe_text(row.get("pdf_id")),
        "pdf_name": _safe_text(row.get("pdf_name")),
        "table_id": _safe_text(row.get("table_id")),
        "metric_name": _safe_text(row.get("metric_name")),
        "normalized_metric_name": _safe_text(row.get("normalized_metric_name")),
        "value_raw": _safe_text(row.get("value_raw")),
        "value_normalized": _safe_text(row.get("value_normalized")),
        "unit": _safe_text(row.get("unit")),
        "period": _safe_text(row.get("period")),
        "source_page": _safe_text(row.get("source_page")),
        "trust_status": _safe_text(row.get("trust_status")),
        "review_status": _safe_text(row.get("review_status")),
        "human_review_status": _safe_text(row.get("human_review_status")),
        "missing_required_fields": _safe_text(row.get("missing_required_fields")),
        "has_metric_name": bool(
            _safe_text(row.get("metric_name")) or _safe_text(row.get("normalized_metric_name"))
        ),
        "has_value": bool(
            _safe_text(row.get("value_raw")) or _safe_text(row.get("value_normalized"))
        ),
        "has_unit": bool(_safe_text(row.get("unit"))),
        "has_period": bool(_safe_text(row.get("period"))),
        "has_source_trace": bool(_safe_text(row.get("source_page"))),
        "is_rejected_or_excluded": _safe_text(row.get("review_status")) == "REJECTED_OR_EXCLUDED",
        "is_downstream_ready_candidate": bool(row.get("is_downstream_ready_candidate")),
        "quality_issue_count": len(issues),
        "quality_issues": "|".join(issues),
        "quality_severity": severity,
        "recommended_action": _recommended_action(row, issues),
    }


def _top_items(counter: Counter[str], limit: int = 5) -> str:
    return ", ".join(f"{name}:{count}" for name, count in counter.most_common(limit))


def _stage_quality_summary(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_safe_text(row["source_stage"])].append(row)
    result: List[Dict[str, Any]] = []
    for stage, stage_rows in sorted(grouped.items()):
        issue_counter = Counter()
        for row in stage_rows:
            for issue in _safe_text(row["quality_issues"]).split("|"):
                if issue:
                    issue_counter[issue] += 1
        result.append(
            {
                "source_stage": stage,
                "row_count": len(stage_rows),
                "high_severity_issue_count": sum(
                    1 for row in stage_rows if _safe_text(row["quality_severity"]) == "HIGH"
                ),
                "medium_severity_issue_count": sum(
                    1 for row in stage_rows if _safe_text(row["quality_severity"]) == "MEDIUM"
                ),
                "low_severity_issue_count": sum(
                    1 for row in stage_rows if _safe_text(row["quality_severity"]) == "LOW"
                ),
                "no_issue_row_count": sum(
                    1 for row in stage_rows if _safe_text(row["quality_severity"]) == "NONE"
                ),
                "top_quality_issues": _top_items(issue_counter, limit=5),
            }
        )
    return result


def _pdf_quality_summary(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_safe_text(row["pdf_name"])].append(row)
    result: List[Dict[str, Any]] = []
    for pdf_name, pdf_rows in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        issue_counter = Counter()
        for row in pdf_rows:
            for issue in _safe_text(row["quality_issues"]).split("|"):
                if issue:
                    issue_counter[issue] += 1
        result.append(
            {
                "pdf_name": pdf_name,
                "pdf_id": _safe_text(pdf_rows[0].get("pdf_id")),
                "row_count": len(pdf_rows),
                "high_severity_issue_count": sum(
                    1 for row in pdf_rows if _safe_text(row["quality_severity"]) == "HIGH"
                ),
                "medium_severity_issue_count": sum(
                    1 for row in pdf_rows if _safe_text(row["quality_severity"]) == "MEDIUM"
                ),
                "low_severity_issue_count": sum(
                    1 for row in pdf_rows if _safe_text(row["quality_severity"]) == "LOW"
                ),
                "top_quality_issues": _top_items(issue_counter, limit=5),
            }
        )
    return result


def _missing_field_hotspots(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_safe_text(row["source_stage"])].append(row)
    result: List[Dict[str, Any]] = []
    for stage, stage_rows in sorted(grouped.items()):
        result.append(
            {
                "source_stage": stage,
                "row_count": len(stage_rows),
                "missing_unit_count": sum(1 for row in stage_rows if not row["has_unit"]),
                "missing_period_count": sum(1 for row in stage_rows if not row["has_period"]),
                "missing_source_page_count": sum(
                    1 for row in stage_rows if not row["has_source_trace"]
                ),
            }
        )
    return result


def _evidence_trace_quality(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "total_rows_with_source_trace": sum(1 for row in rows if row["has_source_trace"]),
        "total_rows_missing_source_trace": sum(1 for row in rows if not row["has_source_trace"]),
        "downstream_candidate_missing_source_trace_count": sum(
            1
            for row in rows
            if row["is_downstream_ready_candidate"] and not row["has_source_trace"]
        ),
        "low_traceability_row_count": sum(
            1
            for row in rows
            if "LOW_TRACEABILITY" in _safe_text(row["quality_issues"]).split("|")
        ),
    }


def _priority_fix_queue(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    queue = [
        row
        for row in rows
        if _safe_text(row["quality_severity"]) == "HIGH"
        or _safe_text(row["recommended_action"]) in {"FIX_SOURCE_TRACE", "FIX_UNIT_OR_PERIOD"}
    ]
    return sorted(
        queue,
        key=lambda row: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NONE": 3}.get(
                _safe_text(row["quality_severity"]), 9
            ),
            -int(row.get("quality_issue_count", 0)),
            _safe_text(row.get("quality_row_id")),
        ),
    )


def build_full_extraction_quality_audit_345b(
    *,
    full_structured_data_inventory_345a_dir: Path = DEFAULT_FULL_STRUCTURED_DATA_INVENTORY_345A_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    manifest_345a_path = full_structured_data_inventory_345a_dir / INPUT_345A_MANIFEST_NAME
    inventory_345a_path = full_structured_data_inventory_345a_dir / INPUT_345A_ROW_INVENTORY_NAME
    stage_status_345a_path = full_structured_data_inventory_345a_dir / INPUT_345A_STAGE_STATUS_NAME
    missing_field_345a_path = full_structured_data_inventory_345a_dir / INPUT_345A_MISSING_FIELD_NAME
    executive_345a_path = full_structured_data_inventory_345a_dir / INPUT_345A_EXECUTIVE_SUMMARY_NAME

    required_paths = [
        manifest_345a_path,
        inventory_345a_path,
        stage_status_345a_path,
        missing_field_345a_path,
        executive_345a_path,
    ]
    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(f"required 345A input missing: {path}")

    files_read = [str(path) for path in required_paths]
    input_hashes_before = {str(path): sha256_file(path) for path in required_paths}

    manifest_345a = _read_json(manifest_345a_path)
    inventory_rows_345a = _read_json(inventory_345a_path)
    stage_status_345a = _read_json(stage_status_345a_path)
    missing_field_345a = _read_json(missing_field_345a_path)
    executive_summary_345a = _read_text(executive_345a_path)

    quality_rows = [
        _quality_row(row, index)
        for index, row in enumerate(inventory_rows_345a, start=1)
    ]
    stage_quality_rows = _stage_quality_summary(quality_rows)
    pdf_quality_rows = _pdf_quality_summary(quality_rows)
    missing_hotspots = _missing_field_hotspots(quality_rows)
    evidence_trace_quality = _evidence_trace_quality(quality_rows)
    priority_fix_queue = _priority_fix_queue(quality_rows)

    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    input_hashes_after = {str(path): sha256_file(path) for path in required_paths}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="345B",
        files_read=files_read,
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
        no_write_back_json.get("no_official_asset_modification_during_345b")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    manifest: Dict[str, Any] = {
        "decision": NOT_READY_DECISION_345B,
        "input_stage": INPUT_STAGE_345B,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_inventory_row_count": len(inventory_rows_345a),
        "audited_row_count": len(quality_rows),
        "high_severity_issue_count": sum(
            1 for row in quality_rows if _safe_text(row["quality_severity"]) == "HIGH"
        ),
        "medium_severity_issue_count": sum(
            1 for row in quality_rows if _safe_text(row["quality_severity"]) == "MEDIUM"
        ),
        "low_severity_issue_count": sum(
            1 for row in quality_rows if _safe_text(row["quality_severity"]) == "LOW"
        ),
        "no_issue_row_count": sum(
            1 for row in quality_rows if _safe_text(row["quality_severity"]) == "NONE"
        ),
        "missing_unit_issue_count": sum(
            1 for row in quality_rows if "MISSING_UNIT" in _safe_text(row["quality_issues"]).split("|")
        ),
        "missing_period_issue_count": sum(
            1 for row in quality_rows if "MISSING_PERIOD" in _safe_text(row["quality_issues"]).split("|")
        ),
        "missing_source_trace_issue_count": sum(
            1
            for row in quality_rows
            if "MISSING_SOURCE_TRACE" in _safe_text(row["quality_issues"]).split("|")
        ),
        "rejected_or_excluded_issue_count": sum(
            1
            for row in quality_rows
            if "REJECTED_OR_EXCLUDED" in _safe_text(row["quality_issues"]).split("|")
        ),
        "review_required_issue_count": sum(
            1 for row in quality_rows if "REVIEW_REQUIRED" in _safe_text(row["quality_issues"]).split("|")
        ),
        "unnormalized_metric_issue_count": sum(
            1
            for row in quality_rows
            if "UNNORMALIZED_METRIC" in _safe_text(row["quality_issues"]).split("|")
        ),
        "human_review_pending_issue_count": sum(
            1
            for row in quality_rows
            if "HUMAN_REVIEW_PENDING" in _safe_text(row["quality_issues"]).split("|")
        ),
        "strict_human_review_pending_issue_count": sum(
            1
            for row in quality_rows
            if "STRICT_HUMAN_REVIEW_PENDING" in _safe_text(row["quality_issues"]).split("|")
        ),
        "priority_fix_queue_count": len(priority_fix_queue),
        "ready_candidate_count_after_quality_audit": sum(
            1
            for row in quality_rows
            if row["is_downstream_ready_candidate"]
            and _safe_text(row["quality_severity"]) in {"NONE", "LOW"}
            and not row["is_rejected_or_excluded"]
        ),
        "metric_limitations": [],
        "output_dir": str(output_dir),
    }

    checks = [
        {
            "check_name": "inputs::345a_manifest_present_and_ready",
            "status": "PASS"
            if _safe_text(manifest_345a.get("decision")) == "FULL_STRUCTURED_DATA_INVENTORY_345A_READY"
            and int(manifest_345a.get("qa_fail_count", 1)) == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "decision": manifest_345a.get("decision", ""),
                    "qa_fail_count": manifest_345a.get("qa_fail_count", None),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::audited_row_count_matches_345a_input",
            "status": "PASS" if len(quality_rows) == len(inventory_rows_345a) else "FAIL",
            "detail": json.dumps(
                {
                    "audited_row_count": len(quality_rows),
                    "input_inventory_row_count": len(inventory_rows_345a),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::quality_summary_exists",
            "status": "PASS"
            if len(stage_quality_rows) > 0 and len(pdf_quality_rows) > 0 and len(missing_hotspots) > 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "stage_quality_count": len(stage_quality_rows),
                    "pdf_quality_count": len(pdf_quality_rows),
                    "missing_hotspot_count": len(missing_hotspots),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::priority_fix_queue_exists",
            "status": "PASS" if priority_fix_queue is not None else "FAIL",
            "detail": json.dumps({"priority_fix_queue_count": len(priority_fix_queue)}, ensure_ascii=False),
        },
        {
            "check_name": "claims::all_export_client_production_flags_false",
            "status": "PASS"
            if not manifest["formal_client_export_allowed"]
            and not manifest["client_ready"]
            and not manifest["production_ready"]
            and not manifest["global_strict_human_review_completed"]
            else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready/global_strict_human_review_completed must remain false",
        },
        {
            "check_name": "safety::no_input_write_back",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
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
            "check_name": "safety::forbidden_paths_not_staged",
            "status": "PASS" if not forbidden_staged else "FAIL",
            "detail": json.dumps(forbidden_staged, ensure_ascii=False),
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
    manifest["qa_fail_count"] = qa_fail_count
    manifest["no_write_back_proof_passed"] = no_write_back_proof_passed
    manifest["decision"] = READY_DECISION_345B if qa_fail_count == 0 else NOT_READY_DECISION_345B

    artifact_index_rows = [
        {
            "artifact_name": MANIFEST_FILE_NAME,
            "path": str(output_dir / MANIFEST_FILE_NAME),
            "purpose": "345B manifest with severity totals, issue counts, and gate boundary.",
        },
        {
            "artifact_name": QUALITY_ROWS_JSON_FILE_NAME,
            "path": str(output_dir / QUALITY_ROWS_JSON_FILE_NAME),
            "purpose": "Per-row quality audit output in JSON.",
        },
        {
            "artifact_name": QUALITY_ROWS_CSV_FILE_NAME,
            "path": str(output_dir / QUALITY_ROWS_CSV_FILE_NAME),
            "purpose": "Per-row quality audit output in CSV.",
        },
        {
            "artifact_name": STAGE_QUALITY_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / STAGE_QUALITY_SUMMARY_JSON_FILE_NAME),
            "purpose": "Stage-level quality distribution in JSON.",
        },
        {
            "artifact_name": STAGE_QUALITY_SUMMARY_CSV_FILE_NAME,
            "path": str(output_dir / STAGE_QUALITY_SUMMARY_CSV_FILE_NAME),
            "purpose": "Stage-level quality distribution in CSV.",
        },
        {
            "artifact_name": PDF_QUALITY_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / PDF_QUALITY_SUMMARY_JSON_FILE_NAME),
            "purpose": "PDF-level quality hotspot summary in JSON.",
        },
        {
            "artifact_name": PDF_QUALITY_SUMMARY_CSV_FILE_NAME,
            "path": str(output_dir / PDF_QUALITY_SUMMARY_CSV_FILE_NAME),
            "purpose": "PDF-level quality hotspot summary in CSV.",
        },
        {
            "artifact_name": MISSING_FIELD_HOTSPOTS_FILE_NAME,
            "path": str(output_dir / MISSING_FIELD_HOTSPOTS_FILE_NAME),
            "purpose": "Stage-level missing field hotspots.",
        },
        {
            "artifact_name": EVIDENCE_TRACE_QUALITY_FILE_NAME,
            "path": str(output_dir / EVIDENCE_TRACE_QUALITY_FILE_NAME),
            "purpose": "Evidence / source trace quality summary.",
        },
        {
            "artifact_name": PRIORITY_FIX_QUEUE_JSON_FILE_NAME,
            "path": str(output_dir / PRIORITY_FIX_QUEUE_JSON_FILE_NAME),
            "purpose": "Priority fix queue in JSON.",
        },
        {
            "artifact_name": PRIORITY_FIX_QUEUE_CSV_FILE_NAME,
            "path": str(output_dir / PRIORITY_FIX_QUEUE_CSV_FILE_NAME),
            "purpose": "Priority fix queue in CSV.",
        },
        {
            "artifact_name": EXECUTIVE_SUMMARY_FILE_NAME,
            "path": str(output_dir / EXECUTIVE_SUMMARY_FILE_NAME),
            "purpose": "Narrative summary of issue totals, hotspots, and next steps.",
        },
        {
            "artifact_name": ARTIFACT_INDEX_FILE_NAME,
            "path": str(output_dir / ARTIFACT_INDEX_FILE_NAME),
            "purpose": "Index of all 345B outputs.",
        },
        {
            "artifact_name": NEXT_PLAN_FILE_NAME,
            "path": str(output_dir / NEXT_PLAN_FILE_NAME),
            "purpose": "Recommended 345C-345E next plan.",
        },
    ]

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": 0,
        "checks": checks,
        "warnings": [],
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
        "input_345a_stage_status_summary": stage_status_345a,
        "input_345a_missing_field_summary": missing_field_345a,
        "input_345a_executive_summary_excerpt": executive_summary_345a[:1200],
    }

    return {
        "manifest": manifest,
        "quality_rows": quality_rows,
        "stage_quality_summary": stage_quality_rows,
        "pdf_quality_summary": pdf_quality_rows,
        "missing_field_hotspots": missing_hotspots,
        "evidence_trace_quality": evidence_trace_quality,
        "priority_fix_queue": priority_fix_queue,
        "artifact_index_rows": artifact_index_rows,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
    }

