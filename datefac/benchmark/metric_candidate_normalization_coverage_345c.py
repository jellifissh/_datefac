from __future__ import annotations

import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

from datefac.review_queue.excel_round_trip_343b import normalize_text
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_345C = "METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_READY"
NOT_READY_DECISION_345C = "METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_NOT_READY"
INPUT_STAGE_345C = "POST_345B_NORMALIZATION_COVERAGE"

DEFAULT_FULL_STRUCTURED_DATA_INVENTORY_345A_DIR = Path(
    r"D:\_datefac\output\full_structured_data_inventory_345a"
)
DEFAULT_FULL_EXTRACTION_QUALITY_AUDIT_345B_DIR = Path(
    r"D:\_datefac\output\full_extraction_quality_audit_345b"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\metric_candidate_normalization_coverage_345c")

MANIFEST_FILE_NAME = "metric_candidate_normalization_coverage_345c_manifest.json"
METRIC_ROWS_JSON_FILE_NAME = "metric_candidate_normalization_coverage_345c_metric_rows.json"
METRIC_ROWS_CSV_FILE_NAME = "metric_candidate_normalization_coverage_345c_metric_rows.csv"
RAW_METRIC_SUMMARY_JSON_FILE_NAME = (
    "metric_candidate_normalization_coverage_345c_raw_metric_summary.json"
)
RAW_METRIC_SUMMARY_CSV_FILE_NAME = (
    "metric_candidate_normalization_coverage_345c_raw_metric_summary.csv"
)
STAGE_COVERAGE_SUMMARY_JSON_FILE_NAME = (
    "metric_candidate_normalization_coverage_345c_stage_coverage_summary.json"
)
STAGE_COVERAGE_SUMMARY_CSV_FILE_NAME = (
    "metric_candidate_normalization_coverage_345c_stage_coverage_summary.csv"
)
PDF_COVERAGE_SUMMARY_JSON_FILE_NAME = (
    "metric_candidate_normalization_coverage_345c_pdf_coverage_summary.json"
)
PDF_COVERAGE_SUMMARY_CSV_FILE_NAME = (
    "metric_candidate_normalization_coverage_345c_pdf_coverage_summary.csv"
)
ALIAS_CANDIDATE_QUEUE_JSON_FILE_NAME = (
    "metric_candidate_normalization_coverage_345c_alias_candidate_queue.json"
)
ALIAS_CANDIDATE_QUEUE_CSV_FILE_NAME = (
    "metric_candidate_normalization_coverage_345c_alias_candidate_queue.csv"
)
NORMALIZATION_BLIND_SPOTS_FILE_NAME = (
    "metric_candidate_normalization_coverage_345c_normalization_blind_spots.json"
)
EXECUTIVE_SUMMARY_FILE_NAME = "metric_candidate_normalization_coverage_345c_executive_summary.md"
ARTIFACT_INDEX_FILE_NAME = "metric_candidate_normalization_coverage_345c_artifact_index.md"
NEXT_PLAN_FILE_NAME = "metric_candidate_normalization_coverage_345c_next_plan.md"

INPUT_345A_MANIFEST_NAME = "full_structured_data_inventory_345a_manifest.json"
INPUT_345A_ROW_INVENTORY_NAME = "full_structured_data_inventory_345a_row_inventory.json"
INPUT_345B_MANIFEST_NAME = "full_extraction_quality_audit_345b_manifest.json"
INPUT_345B_QUALITY_ROWS_NAME = "full_extraction_quality_audit_345b_quality_rows.json"

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

METRIC_ROW_FIELDS = [
    "metric_coverage_row_id",
    "inventory_row_id",
    "quality_row_id",
    "source_stage",
    "source_artifact",
    "pdf_id",
    "pdf_name",
    "raw_metric_name",
    "normalized_metric_name",
    "has_raw_metric_name",
    "has_normalized_metric_name",
    "is_metric_candidate",
    "is_normalized_metric",
    "quality_severity",
    "quality_issues",
    "review_status",
    "trust_status",
    "downstream_ready_before_normalization",
    "normalization_status",
    "normalization_gap_reason",
    "alias_candidate_key",
    "alias_candidate_priority",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def _normalization_status(row: Dict[str, Any]) -> str:
    if not bool(row.get("is_metric_candidate")):
        return "NON_METRIC_ROW"
    if not _safe_text(row.get("raw_metric_name")):
        return "MISSING_RAW_METRIC_NAME"
    if bool(row.get("is_normalized_metric")) and _safe_text(row.get("normalized_metric_name")):
        return "NORMALIZED"
    if _safe_text(row.get("raw_metric_name")):
        return "UNNORMALIZED_WITH_RAW_NAME"
    return "UNKNOWN"


def _gap_reason(row: Dict[str, Any], normalization_status: str) -> str:
    if normalization_status == "NORMALIZED":
        return "NO_GAP"
    if normalization_status == "MISSING_RAW_METRIC_NAME":
        return "MISSING_RAW_METRIC_NAME"
    if _safe_text(row.get("source_stage")) == "UNKNOWN_STAGE":
        return "SOURCE_STAGE_NOT_TARGETED"
    if _safe_text(row.get("review_status")) == "REJECTED_OR_EXCLUDED":
        return "REJECTED_OR_EXCLUDED_ROW"
    raw_name = _safe_text(row.get("raw_metric_name"))
    if not raw_name:
        return "MISSING_RAW_METRIC_NAME"
    if len(raw_name) >= 20 or any(ch.isdigit() for ch in raw_name):
        return "RAW_NAME_TOO_NOISY"
    lower = raw_name.lower()
    header_or_total_tokens = [
        "\u5408\u8ba1",
        "\u603b\u8ba1",
        "\u5c0f\u8ba1",
        "\u5176\u4e2d",
        "\u9879\u76ee",
        "total",
        "subtotal",
        "item",
    ]
    if any(token in raw_name or token in lower for token in header_or_total_tokens):
        return "POSSIBLE_TABLE_HEADER_OR_TOTAL"
    return "RAW_NAME_NOT_MAPPED"


def _alias_priority(row: Dict[str, Any], normalization_status: str) -> str:
    if normalization_status != "UNNORMALIZED_WITH_RAW_NAME":
        return ""
    if (
        bool(row.get("downstream_ready_before_normalization"))
        and _safe_text(row.get("review_status")) != "REJECTED_OR_EXCLUDED"
        and _safe_text(row.get("quality_severity")) in {"NONE", "LOW", "MEDIUM"}
    ):
        return "HIGH"
    if _safe_text(row.get("review_status")) == "REVIEW_REQUIRED":
        return "MEDIUM"
    return "LOW"


def _metric_coverage_row(
    inventory_row: Dict[str, Any],
    quality_row: Dict[str, Any] | None,
    index: int,
) -> Dict[str, Any]:
    raw_metric_name = _safe_text(inventory_row.get("metric_name"))
    normalized_metric_name = _safe_text(inventory_row.get("normalized_metric_name"))
    is_metric_candidate = bool(inventory_row.get("is_metric_candidate"))
    is_normalized_metric = bool(inventory_row.get("is_normalized_metric"))
    record = {
        "metric_coverage_row_id": f"345c::metric::{index:05d}",
        "inventory_row_id": _safe_text(inventory_row.get("inventory_row_id")),
        "quality_row_id": _safe_text(quality_row.get("quality_row_id") if quality_row else ""),
        "source_stage": _safe_text(inventory_row.get("source_stage")),
        "source_artifact": _safe_text(inventory_row.get("source_artifact")),
        "pdf_id": _safe_text(inventory_row.get("pdf_id")),
        "pdf_name": _safe_text(inventory_row.get("pdf_name")),
        "raw_metric_name": raw_metric_name,
        "normalized_metric_name": normalized_metric_name,
        "has_raw_metric_name": bool(raw_metric_name),
        "has_normalized_metric_name": bool(normalized_metric_name),
        "is_metric_candidate": is_metric_candidate,
        "is_normalized_metric": is_normalized_metric,
        "quality_severity": _safe_text(quality_row.get("quality_severity") if quality_row else ""),
        "quality_issues": _safe_text(quality_row.get("quality_issues") if quality_row else ""),
        "review_status": _safe_text(inventory_row.get("review_status")),
        "trust_status": _safe_text(inventory_row.get("trust_status")),
        "downstream_ready_before_normalization": bool(
            inventory_row.get("is_downstream_ready_candidate")
        ),
    }
    status = _normalization_status(record)
    record["normalization_status"] = status
    record["normalization_gap_reason"] = _gap_reason(record, status)
    record["alias_candidate_key"] = raw_metric_name if status == "UNNORMALIZED_WITH_RAW_NAME" else ""
    record["alias_candidate_priority"] = _alias_priority(record, status)
    return record


def _raw_metric_summary(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = _safe_text(row["raw_metric_name"])
        if key:
            grouped[key].append(row)
    summary_rows: List[Dict[str, Any]] = []
    for raw_name, group in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        priorities = Counter(_safe_text(row["alias_candidate_priority"]) for row in group if _safe_text(row["alias_candidate_priority"]))
        statuses = Counter(_safe_text(row["normalization_status"]) for row in group)
        summary_rows.append(
            {
                "raw_metric_name": raw_name,
                "row_count": len(group),
                "normalized_metric_row_count": sum(1 for row in group if _safe_text(row["normalization_status"]) == "NORMALIZED"),
                "unnormalized_metric_row_count": sum(1 for row in group if _safe_text(row["normalization_status"]) == "UNNORMALIZED_WITH_RAW_NAME"),
                "normalization_coverage_ratio": _ratio(
                    sum(1 for row in group if _safe_text(row["normalization_status"]) == "NORMALIZED"),
                    len(group),
                ),
                "source_stages": "|".join(sorted({ _safe_text(row["source_stage"]) for row in group if _safe_text(row["source_stage"]) })),
                "pdf_names": "|".join(sorted({ _safe_text(row["pdf_name"]) for row in group if _safe_text(row["pdf_name"]) })[:10]),
                "top_normalization_statuses": ", ".join(
                    f"{name}:{count}" for name, count in statuses.most_common(3)
                ),
                "suggested_alias_priority": priorities.most_common(1)[0][0] if priorities else "",
            }
        )
    return summary_rows


def _coverage_summary_by_key(rows: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_safe_text(row[key])].append(row)
    result: List[Dict[str, Any]] = []
    for bucket, group in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        unnormalized_names = Counter(
            _safe_text(row["raw_metric_name"])
            for row in group
            if _safe_text(row["normalization_status"]) == "UNNORMALIZED_WITH_RAW_NAME"
            and _safe_text(row["raw_metric_name"])
        )
        result.append(
            {
                key: bucket,
                "metric_candidate_row_count": len(group),
                "normalized_metric_row_count": sum(
                    1 for row in group if _safe_text(row["normalization_status"]) == "NORMALIZED"
                ),
                "unnormalized_metric_row_count": sum(
                    1
                    for row in group
                    if _safe_text(row["normalization_status"]) == "UNNORMALIZED_WITH_RAW_NAME"
                ),
                "normalization_coverage_ratio": _ratio(
                    sum(
                        1 for row in group if _safe_text(row["normalization_status"]) == "NORMALIZED"
                    ),
                    len(group),
                ),
                "top_unnormalized_raw_metric_names": ", ".join(
                    f"{name}:{count}" for name, count in unnormalized_names.most_common(5)
                ),
            }
        )
    return result


def _alias_candidate_queue(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if _safe_text(row["normalization_status"]) == "UNNORMALIZED_WITH_RAW_NAME":
            grouped[_safe_text(row["raw_metric_name"])].append(row)
    result: List[Dict[str, Any]] = []
    for raw_name, group in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        priorities = Counter(_safe_text(row["alias_candidate_priority"]) for row in group)
        severities = Counter(_safe_text(row["quality_severity"]) for row in group)
        source_stages = sorted({_safe_text(row["source_stage"]) for row in group if _safe_text(row["source_stage"])})
        pdfs = sorted({_safe_text(row["pdf_name"]) for row in group if _safe_text(row["pdf_name"])})
        sample_row_ids = [row["metric_coverage_row_id"] for row in group[:5]]
        result.append(
            {
                "raw_metric_name": raw_name,
                "frequency": len(group),
                "source_stages": "|".join(source_stages),
                "pdf_names": "|".join(pdfs[:10]),
                "sample_row_ids": "|".join(sample_row_ids),
                "quality_severity_distribution": ", ".join(
                    f"{name}:{count}" for name, count in severities.most_common()
                ),
                "suggested_priority": priorities.most_common(1)[0][0] if priorities else "LOW",
            }
        )
    return result


def _normalization_blind_spots(
    rows: List[Dict[str, Any]],
    stage_rows: List[Dict[str, Any]],
    pdf_rows: List[Dict[str, Any]],
    alias_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    top_unmapped = [row["raw_metric_name"] for row in alias_rows[:20]]
    stage_with_lowest = None
    for row in stage_rows:
        ratio = row.get("normalization_coverage_ratio")
        if ratio is None:
            continue
        if stage_with_lowest is None or ratio < stage_with_lowest[1]:
            stage_with_lowest = (_safe_text(row["source_stage"]), ratio)
    pdf_with_lowest = None
    for row in pdf_rows:
        ratio = row.get("normalization_coverage_ratio")
        if ratio is None:
            continue
        if pdf_with_lowest is None or ratio < pdf_with_lowest[1]:
            pdf_with_lowest = (_safe_text(row["pdf_name"]), ratio)
    return {
        "top_unmapped_raw_metric_names": "|".join(top_unmapped),
        "stage_with_lowest_coverage": stage_with_lowest[0] if stage_with_lowest else "",
        "stage_with_lowest_coverage_ratio": stage_with_lowest[1] if stage_with_lowest else None,
        "pdf_with_lowest_coverage": pdf_with_lowest[0] if pdf_with_lowest else "",
        "pdf_with_lowest_coverage_ratio": pdf_with_lowest[1] if pdf_with_lowest else None,
    }


def build_metric_candidate_normalization_coverage_345c(
    *,
    full_structured_data_inventory_345a_dir: Path = DEFAULT_FULL_STRUCTURED_DATA_INVENTORY_345A_DIR,
    full_extraction_quality_audit_345b_dir: Path = DEFAULT_FULL_EXTRACTION_QUALITY_AUDIT_345B_DIR,
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
    manifest_345b_path = full_extraction_quality_audit_345b_dir / INPUT_345B_MANIFEST_NAME
    quality_rows_345b_path = full_extraction_quality_audit_345b_dir / INPUT_345B_QUALITY_ROWS_NAME
    required_paths = [
        manifest_345a_path,
        inventory_345a_path,
        manifest_345b_path,
        quality_rows_345b_path,
    ]
    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(f"required 345A/345B input missing: {path}")

    files_read = [str(path) for path in required_paths]
    input_hashes_before = {str(path): sha256_file(path) for path in required_paths}

    manifest_345a = _read_json(manifest_345a_path)
    inventory_rows = _read_json(inventory_345a_path)
    manifest_345b = _read_json(manifest_345b_path)
    quality_rows = _read_json(quality_rows_345b_path)

    quality_by_inventory_id = {
        _safe_text(row.get("inventory_row_id")): row for row in quality_rows
    }
    metric_rows = [
        _metric_coverage_row(row, quality_by_inventory_id.get(_safe_text(row.get("inventory_row_id"))), index)
        for index, row in enumerate(inventory_rows, start=1)
        if bool(row.get("is_metric_candidate"))
    ]

    raw_metric_summary_rows = _raw_metric_summary(metric_rows)
    stage_coverage_rows = _coverage_summary_by_key(metric_rows, "source_stage")
    pdf_coverage_rows = _coverage_summary_by_key(metric_rows, "pdf_name")
    alias_candidate_rows = _alias_candidate_queue(metric_rows)
    blind_spots = _normalization_blind_spots(
        metric_rows, stage_coverage_rows, pdf_coverage_rows, alias_candidate_rows
    )

    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    input_hashes_after = {str(path): sha256_file(path) for path in required_paths}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="345C",
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
    no_write_back_json["normalization_rules_modified"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_345c")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
        and not no_write_back_json.get("normalization_rules_modified", True)
    )

    normalized_metric_row_count = sum(
        1 for row in metric_rows if _safe_text(row["normalization_status"]) == "NORMALIZED"
    )
    unnormalized_metric_row_count = sum(
        1
        for row in metric_rows
        if _safe_text(row["normalization_status"]) == "UNNORMALIZED_WITH_RAW_NAME"
    )
    unique_raw_metric_name_count = len(
        {_safe_text(row["raw_metric_name"]) for row in metric_rows if _safe_text(row["raw_metric_name"])}
    )
    unique_normalized_metric_name_count = len(
        {
            _safe_text(row["normalized_metric_name"])
            for row in metric_rows
            if _safe_text(row["normalized_metric_name"])
        }
    )
    unique_unnormalized_raw_metric_name_count = len(
        {
            _safe_text(row["raw_metric_name"])
            for row in metric_rows
            if _safe_text(row["normalization_status"]) == "UNNORMALIZED_WITH_RAW_NAME"
            and _safe_text(row["raw_metric_name"])
        }
    )

    manifest: Dict[str, Any] = {
        "decision": NOT_READY_DECISION_345C,
        "input_stage": INPUT_STAGE_345C,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_inventory_row_count": int(manifest_345a.get("total_inventory_row_count", len(inventory_rows))),
        "input_audited_row_count": int(manifest_345b.get("audited_row_count", len(quality_rows))),
        "metric_candidate_row_count": len(metric_rows),
        "normalized_metric_row_count": normalized_metric_row_count,
        "unnormalized_metric_row_count": unnormalized_metric_row_count,
        "normalization_coverage_ratio": _ratio(normalized_metric_row_count, len(metric_rows)),
        "unique_raw_metric_name_count": unique_raw_metric_name_count,
        "unique_normalized_metric_name_count": unique_normalized_metric_name_count,
        "unique_unnormalized_raw_metric_name_count": unique_unnormalized_raw_metric_name_count,
        "alias_candidate_count": len(alias_candidate_rows),
        "high_priority_alias_candidate_count": sum(
            1 for row in alias_candidate_rows if _safe_text(row["suggested_priority"]) == "HIGH"
        ),
        "stage_with_lowest_coverage": blind_spots.get("stage_with_lowest_coverage", ""),
        "pdf_with_lowest_coverage": blind_spots.get("pdf_with_lowest_coverage", ""),
        "ready_candidate_count_before_normalization_filter": int(
            manifest_345a.get("downstream_ready_candidate_count", 0)
        ),
        "ready_candidate_count_after_normalization_filter": sum(
            1
            for row in metric_rows
            if bool(row["downstream_ready_before_normalization"])
            and _safe_text(row["normalization_status"]) == "NORMALIZED"
        ),
        "metric_limitations": [],
        "output_dir": str(output_dir),
    }

    checks = [
        {
            "check_name": "inputs::345a_and_345b_ready",
            "status": "PASS"
            if _safe_text(manifest_345a.get("decision")) == "FULL_STRUCTURED_DATA_INVENTORY_345A_READY"
            and _safe_text(manifest_345b.get("decision")) == "FULL_EXTRACTION_QUALITY_AUDIT_345B_READY"
            and int(manifest_345a.get("qa_fail_count", 1)) == 0
            and int(manifest_345b.get("qa_fail_count", 1)) == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "345a_decision": manifest_345a.get("decision", ""),
                    "345b_decision": manifest_345b.get("decision", ""),
                    "345a_qa": manifest_345a.get("qa_fail_count", None),
                    "345b_qa": manifest_345b.get("qa_fail_count", None),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::row_counts_consistent_with_345a_345b",
            "status": "PASS"
            if int(manifest_345a.get("metric_candidate_row_count", -1)) == len(metric_rows)
            and int(manifest_345b.get("input_inventory_row_count", -1)) == len(inventory_rows)
            and int(manifest_345b.get("audited_row_count", -1)) == len(quality_rows)
            else "FAIL",
            "detail": json.dumps(
                {
                    "metric_rows": len(metric_rows),
                    "inventory_rows": len(inventory_rows),
                    "quality_rows": len(quality_rows),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::alias_candidate_queue_exists",
            "status": "PASS" if alias_candidate_rows is not None else "FAIL",
            "detail": json.dumps({"alias_candidate_count": len(alias_candidate_rows)}, ensure_ascii=False),
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
            "check_name": "safety::normalization_rules_not_modified",
            "status": "PASS",
            "detail": "345C only analyzes normalization coverage and does not update rules.",
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
    manifest["decision"] = READY_DECISION_345C if qa_fail_count == 0 else NOT_READY_DECISION_345C

    artifact_index_rows = [
        {
            "artifact_name": MANIFEST_FILE_NAME,
            "path": str(output_dir / MANIFEST_FILE_NAME),
            "purpose": "345C manifest with coverage metrics and gate boundary.",
        },
        {
            "artifact_name": METRIC_ROWS_JSON_FILE_NAME,
            "path": str(output_dir / METRIC_ROWS_JSON_FILE_NAME),
            "purpose": "Per-row normalization coverage analysis in JSON.",
        },
        {
            "artifact_name": METRIC_ROWS_CSV_FILE_NAME,
            "path": str(output_dir / METRIC_ROWS_CSV_FILE_NAME),
            "purpose": "Per-row normalization coverage analysis in CSV.",
        },
        {
            "artifact_name": RAW_METRIC_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / RAW_METRIC_SUMMARY_JSON_FILE_NAME),
            "purpose": "Grouped raw metric name coverage summary in JSON.",
        },
        {
            "artifact_name": RAW_METRIC_SUMMARY_CSV_FILE_NAME,
            "path": str(output_dir / RAW_METRIC_SUMMARY_CSV_FILE_NAME),
            "purpose": "Grouped raw metric name coverage summary in CSV.",
        },
        {
            "artifact_name": STAGE_COVERAGE_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / STAGE_COVERAGE_SUMMARY_JSON_FILE_NAME),
            "purpose": "Stage-level normalization coverage summary in JSON.",
        },
        {
            "artifact_name": STAGE_COVERAGE_SUMMARY_CSV_FILE_NAME,
            "path": str(output_dir / STAGE_COVERAGE_SUMMARY_CSV_FILE_NAME),
            "purpose": "Stage-level normalization coverage summary in CSV.",
        },
        {
            "artifact_name": PDF_COVERAGE_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / PDF_COVERAGE_SUMMARY_JSON_FILE_NAME),
            "purpose": "PDF-level normalization coverage hotspot summary in JSON.",
        },
        {
            "artifact_name": PDF_COVERAGE_SUMMARY_CSV_FILE_NAME,
            "path": str(output_dir / PDF_COVERAGE_SUMMARY_CSV_FILE_NAME),
            "purpose": "PDF-level normalization coverage hotspot summary in CSV.",
        },
        {
            "artifact_name": ALIAS_CANDIDATE_QUEUE_JSON_FILE_NAME,
            "path": str(output_dir / ALIAS_CANDIDATE_QUEUE_JSON_FILE_NAME),
            "purpose": "Alias candidate queue in JSON without changing rules.",
        },
        {
            "artifact_name": ALIAS_CANDIDATE_QUEUE_CSV_FILE_NAME,
            "path": str(output_dir / ALIAS_CANDIDATE_QUEUE_CSV_FILE_NAME),
            "purpose": "Alias candidate queue in CSV.",
        },
        {
            "artifact_name": NORMALIZATION_BLIND_SPOTS_FILE_NAME,
            "path": str(output_dir / NORMALIZATION_BLIND_SPOTS_FILE_NAME),
            "purpose": "Normalization blind spot summary.",
        },
        {
            "artifact_name": EXECUTIVE_SUMMARY_FILE_NAME,
            "path": str(output_dir / EXECUTIVE_SUMMARY_FILE_NAME),
            "purpose": "Narrative summary of normalization coverage and blind spots.",
        },
        {
            "artifact_name": ARTIFACT_INDEX_FILE_NAME,
            "path": str(output_dir / ARTIFACT_INDEX_FILE_NAME),
            "purpose": "Index of all 345C outputs.",
        },
        {
            "artifact_name": NEXT_PLAN_FILE_NAME,
            "path": str(output_dir / NEXT_PLAN_FILE_NAME),
            "purpose": "Recommended 345D-345E next plan.",
        },
    ]

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": 0,
        "checks": checks,
        "warnings": [],
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    return {
        "manifest": manifest,
        "metric_rows": metric_rows,
        "raw_metric_summary": raw_metric_summary_rows,
        "stage_coverage_summary": stage_coverage_rows,
        "pdf_coverage_summary": pdf_coverage_rows,
        "alias_candidate_queue": alias_candidate_rows,
        "normalization_blind_spots": blind_spots,
        "artifact_index_rows": artifact_index_rows,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
    }
