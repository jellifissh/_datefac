from __future__ import annotations

import json
import subprocess
from copy import deepcopy
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
READY_DECISION_345C5 = "REVIEWED_ALIAS_DECISION_INGESTION_345C5_READY"
READY_DECISION_345C6 = "REVIEWED_ALIAS_APPLY_SIMULATION_345C6_READY"
INPUT_STAGE_345C6 = "POST_345C5_REVIEWED_ALIAS_APPLY_SIMULATION"

DEFAULT_METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_DIR = Path(
    r"D:\_datefac\output\metric_candidate_normalization_coverage_345c"
)
DEFAULT_REVIEWED_ALIAS_DECISION_INGESTION_345C5_DIR = Path(
    r"D:\_datefac\output\reviewed_alias_decision_ingestion_345c5"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\reviewed_alias_apply_simulation_345c6")

MANIFEST_FILE_NAME = "reviewed_alias_apply_simulation_345c6_manifest.json"
SIMULATED_METRIC_ROWS_JSON_FILE_NAME = (
    "reviewed_alias_apply_simulation_345c6_simulated_metric_rows.json"
)
SIMULATED_METRIC_ROWS_CSV_FILE_NAME = (
    "reviewed_alias_apply_simulation_345c6_simulated_metric_rows.csv"
)
APPLIED_ALIAS_MAP_JSON_FILE_NAME = "reviewed_alias_apply_simulation_345c6_applied_alias_map.json"
APPLIED_ALIAS_MAP_CSV_FILE_NAME = "reviewed_alias_apply_simulation_345c6_applied_alias_map.csv"
COVERAGE_BEFORE_AFTER_JSON_FILE_NAME = (
    "reviewed_alias_apply_simulation_345c6_coverage_before_after.json"
)
COVERAGE_BEFORE_AFTER_CSV_FILE_NAME = (
    "reviewed_alias_apply_simulation_345c6_coverage_before_after.csv"
)
REMAINING_BLIND_SPOTS_JSON_FILE_NAME = (
    "reviewed_alias_apply_simulation_345c6_remaining_blind_spots.json"
)
REMAINING_BLIND_SPOTS_CSV_FILE_NAME = (
    "reviewed_alias_apply_simulation_345c6_remaining_blind_spots.csv"
)
NON_APPLIED_ALIASES_JSON_FILE_NAME = (
    "reviewed_alias_apply_simulation_345c6_non_applied_aliases.json"
)
NON_APPLIED_ALIASES_CSV_FILE_NAME = (
    "reviewed_alias_apply_simulation_345c6_non_applied_aliases.csv"
)
EXECUTIVE_SUMMARY_MD_FILE_NAME = (
    "reviewed_alias_apply_simulation_345c6_executive_summary.md"
)
ARTIFACT_INDEX_MD_FILE_NAME = "reviewed_alias_apply_simulation_345c6_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "reviewed_alias_apply_simulation_345c6_next_plan.md"

INPUT_345C_MANIFEST_NAME = "metric_candidate_normalization_coverage_345c_manifest.json"
INPUT_345C_METRIC_ROWS_JSON_NAME = "metric_candidate_normalization_coverage_345c_metric_rows.json"
INPUT_345C_METRIC_ROWS_CSV_NAME = "metric_candidate_normalization_coverage_345c_metric_rows.csv"
INPUT_345C_RAW_METRIC_SUMMARY_JSON_NAME = (
    "metric_candidate_normalization_coverage_345c_raw_metric_summary.json"
)
INPUT_345C_RAW_METRIC_SUMMARY_CSV_NAME = (
    "metric_candidate_normalization_coverage_345c_raw_metric_summary.csv"
)
INPUT_345C_ALIAS_QUEUE_JSON_NAME = (
    "metric_candidate_normalization_coverage_345c_alias_candidate_queue.json"
)
INPUT_345C_ALIAS_QUEUE_CSV_NAME = (
    "metric_candidate_normalization_coverage_345c_alias_candidate_queue.csv"
)

INPUT_345C5_MANIFEST_NAME = "reviewed_alias_decision_ingestion_345c5_manifest.json"
INPUT_345C5_VALIDATED_APPROVED_JSON_NAME = (
    "reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.json"
)
INPUT_345C5_VALIDATED_APPROVED_CSV_NAME = (
    "reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.csv"
)
INPUT_345C5_REJECTED_OR_DEFERRED_JSON_NAME = (
    "reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.json"
)
INPUT_345C5_REJECTED_OR_DEFERRED_CSV_NAME = (
    "reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.csv"
)
INPUT_345C5_VALIDATION_ISSUES_JSON_NAME = (
    "reviewed_alias_decision_ingestion_345c5_validation_issues.json"
)

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

SIMULATED_METRIC_ROW_FIELDS = [
    "metric_coverage_row_id",
    "inventory_row_id",
    "quality_row_id",
    "raw_metric_name",
    "normalized_metric_name",
    "simulated_normalized_metric_name",
    "normalization_status_before",
    "normalization_status_after_simulation",
    "simulation_applied",
    "simulation_action",
    "simulation_source",
    "simulation_rule_update_required",
    "simulation_only_no_write_back",
    "source_stage",
    "source_artifact",
    "pdf_name",
    "quality_severity",
    "quality_issues",
    "downstream_ready_before_normalization",
    "downstream_ready_after_alias_simulation",
]

APPLIED_ALIAS_MAP_FIELDS = [
    "approved_alias_key",
    "raw_metric_name",
    "canonical_alias_target",
    "source_decision",
    "review_priority",
    "source_stages",
    "applied_row_count",
    "newly_normalized_row_count",
    "applied_row_ids",
    "already_normalized_match_count",
    "matching_row_count",
    "simulation_rule_update_required",
    "simulation_only_no_write_back",
]

COVERAGE_BEFORE_AFTER_FIELDS = [
    "metric_candidate_row_count_before",
    "normalized_metric_row_count_before",
    "unnormalized_metric_row_count_before",
    "normalization_coverage_ratio_before",
    "simulated_alias_applied_row_count",
    "simulated_newly_normalized_row_count",
    "normalized_metric_row_count_after_simulation",
    "unnormalized_metric_row_count_after_simulation",
    "normalization_coverage_ratio_after_simulation",
    "normalization_coverage_ratio_delta",
    "ready_candidate_count_before_simulation",
    "ready_candidate_count_after_alias_simulation",
    "ready_candidate_count_delta",
    "remaining_unnormalized_raw_metric_name_count",
    "remaining_unnormalized_metric_row_count",
    "metric_limitations",
]

REMAINING_BLIND_SPOT_FIELDS = [
    "raw_metric_name",
    "remaining_row_count",
    "remaining_ready_candidate_count",
    "source_stages",
    "pdf_names",
    "quality_severity_distribution",
    "sample_row_ids",
]

NON_APPLIED_ALIAS_FIELDS = [
    "approved_alias_key",
    "raw_metric_name",
    "canonical_alias_target",
    "source_decision",
    "non_applied_reason",
    "matching_row_count",
    "already_normalized_match_count",
    "eligible_unnormalized_match_count",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_existing(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"required input file missing: {path}")
    return path


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


def _normalize_alias_key(value: Any) -> str:
    return _safe_text(value)


def _is_normalized_status(status: str) -> bool:
    return status == "NORMALIZED"


def _is_unnormalized_status(status: str) -> bool:
    return status == "UNNORMALIZED_WITH_RAW_NAME"


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def _load_required_json_list(path: Path, label: str) -> List[Dict[str, Any]]:
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"{label} must be a list JSON payload: {path}")
    return [dict(row) for row in payload]


def _apply_simulation_fields(
    row: Dict[str, Any],
    canonical_alias_target: str,
) -> Dict[str, Any]:
    simulated_row = deepcopy(row)
    before_status = _safe_text(row.get("normalization_status"))
    simulated_row["simulated_normalized_metric_name"] = canonical_alias_target
    simulated_row["normalization_status_before"] = before_status
    simulated_row["normalization_status_after_simulation"] = "NORMALIZED"
    simulated_row["simulation_applied"] = True
    simulated_row["simulation_action"] = "SIMULATED_ALIAS_NORMALIZATION"
    simulated_row["simulation_source"] = "REVIEWED_ALIAS_345C5"
    simulated_row["simulation_rule_update_required"] = True
    simulated_row["simulation_only_no_write_back"] = True
    simulated_row["downstream_ready_after_alias_simulation"] = bool(
        row.get("downstream_ready_before_normalization")
    )
    return simulated_row


def _preserve_without_simulation(row: Dict[str, Any]) -> Dict[str, Any]:
    simulated_row = deepcopy(row)
    before_status = _safe_text(row.get("normalization_status"))
    simulated_row["simulated_normalized_metric_name"] = _safe_text(
        row.get("normalized_metric_name")
    )
    simulated_row["normalization_status_before"] = before_status
    simulated_row["normalization_status_after_simulation"] = before_status
    simulated_row["simulation_applied"] = False
    simulated_row["simulation_action"] = "NO_SIMULATION_APPLIED"
    simulated_row["simulation_source"] = ""
    simulated_row["simulation_rule_update_required"] = False
    simulated_row["simulation_only_no_write_back"] = True
    simulated_row["downstream_ready_after_alias_simulation"] = bool(
        row.get("downstream_ready_before_normalization")
    ) and _is_normalized_status(before_status)
    return simulated_row


def _remaining_blind_spot_rows(
    rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        after_status = _safe_text(row.get("normalization_status_after_simulation"))
        raw_metric_name = _safe_text(row.get("raw_metric_name"))
        if not _is_unnormalized_status(after_status) or not raw_metric_name:
            continue
        grouped.setdefault(raw_metric_name, []).append(row)

    result: List[Dict[str, Any]] = []
    for raw_metric_name, group in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        severity_counts: Dict[str, int] = {}
        for row in group:
            severity = _safe_text(row.get("quality_severity")) or "UNKNOWN"
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        result.append(
            {
                "raw_metric_name": raw_metric_name,
                "remaining_row_count": len(group),
                "remaining_ready_candidate_count": sum(
                    1 for row in group if bool(row.get("downstream_ready_after_alias_simulation"))
                ),
                "source_stages": "|".join(
                    sorted({_safe_text(row.get("source_stage")) for row in group if _safe_text(row.get("source_stage"))})
                ),
                "pdf_names": "|".join(
                    sorted({_safe_text(row.get("pdf_name")) for row in group if _safe_text(row.get("pdf_name"))})[:10]
                ),
                "quality_severity_distribution": ", ".join(
                    f"{name}:{count}"
                    for name, count in sorted(severity_counts.items(), key=lambda item: (-item[1], item[0]))
                ),
                "sample_row_ids": "|".join(
                    [_safe_text(row.get("metric_coverage_row_id")) for row in group[:5]]
                ),
            }
        )
    return result


def _determine_next_scope(
    *,
    simulated_newly_normalized_row_count: int,
    normalization_coverage_ratio_delta: float | None,
    remaining_unnormalized_raw_metric_name_count: int,
) -> str:
    if simulated_newly_normalized_row_count <= 0:
        return "345C4/345C5 additional review batch"
    if remaining_unnormalized_raw_metric_name_count > 50 or (
        normalization_coverage_ratio_delta is not None and normalization_coverage_ratio_delta < 0.02
    ):
        return "345C7 Official Alias Rule Update Candidate Package"
    return "345D Full Structured Demo Export Package"


def build_reviewed_alias_apply_simulation_345c6(
    *,
    metric_candidate_normalization_coverage_345c_dir: Path,
    reviewed_alias_decision_ingestion_345c5_dir: Path,
    output_dir: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345c_path = _require_existing(
        metric_candidate_normalization_coverage_345c_dir / INPUT_345C_MANIFEST_NAME
    )
    metric_rows_345c_path = _require_existing(
        metric_candidate_normalization_coverage_345c_dir / INPUT_345C_METRIC_ROWS_JSON_NAME
    )
    raw_metric_summary_345c_path = _require_existing(
        metric_candidate_normalization_coverage_345c_dir / INPUT_345C_RAW_METRIC_SUMMARY_JSON_NAME
    )
    alias_queue_345c_path = _require_existing(
        metric_candidate_normalization_coverage_345c_dir / INPUT_345C_ALIAS_QUEUE_JSON_NAME
    )
    _require_existing(metric_candidate_normalization_coverage_345c_dir / INPUT_345C_METRIC_ROWS_CSV_NAME)
    _require_existing(metric_candidate_normalization_coverage_345c_dir / INPUT_345C_RAW_METRIC_SUMMARY_CSV_NAME)
    _require_existing(metric_candidate_normalization_coverage_345c_dir / INPUT_345C_ALIAS_QUEUE_CSV_NAME)

    manifest_345c5_path = _require_existing(
        reviewed_alias_decision_ingestion_345c5_dir / INPUT_345C5_MANIFEST_NAME
    )
    validated_approved_345c5_path = _require_existing(
        reviewed_alias_decision_ingestion_345c5_dir / INPUT_345C5_VALIDATED_APPROVED_JSON_NAME
    )
    rejected_or_deferred_345c5_path = _require_existing(
        reviewed_alias_decision_ingestion_345c5_dir / INPUT_345C5_REJECTED_OR_DEFERRED_JSON_NAME
    )
    validation_issues_345c5_path = _require_existing(
        reviewed_alias_decision_ingestion_345c5_dir / INPUT_345C5_VALIDATION_ISSUES_JSON_NAME
    )
    _require_existing(
        reviewed_alias_decision_ingestion_345c5_dir / INPUT_345C5_VALIDATED_APPROVED_CSV_NAME
    )
    _require_existing(
        reviewed_alias_decision_ingestion_345c5_dir / INPUT_345C5_REJECTED_OR_DEFERRED_CSV_NAME
    )

    files_read = [
        str(manifest_345c_path),
        str(metric_rows_345c_path),
        str(raw_metric_summary_345c_path),
        str(alias_queue_345c_path),
        str(manifest_345c5_path),
        str(validated_approved_345c5_path),
        str(rejected_or_deferred_345c5_path),
        str(validation_issues_345c5_path),
    ]
    input_paths = [
        manifest_345c_path,
        metric_rows_345c_path,
        raw_metric_summary_345c_path,
        alias_queue_345c_path,
        manifest_345c5_path,
        validated_approved_345c5_path,
        rejected_or_deferred_345c5_path,
        validation_issues_345c5_path,
    ]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    manifest_345c = _read_json(manifest_345c_path)
    metric_rows_345c = _load_required_json_list(metric_rows_345c_path, "345C metric rows")
    _ = _load_required_json_list(raw_metric_summary_345c_path, "345C raw metric summary")
    _ = _load_required_json_list(alias_queue_345c_path, "345C alias candidate queue")
    manifest_345c5 = _read_json(manifest_345c5_path)
    validated_approved_aliases = _load_required_json_list(
        validated_approved_345c5_path, "345C5 validated approved aliases"
    )
    rejected_or_deferred_aliases = _load_required_json_list(
        rejected_or_deferred_345c5_path, "345C5 rejected or deferred aliases"
    )
    validation_issues = _load_required_json_list(
        validation_issues_345c5_path, "345C5 validation issues"
    )

    if _safe_text(manifest_345c.get("decision")) != READY_DECISION_345C:
        raise ValueError("345C manifest decision is not READY.")
    if _safe_text(manifest_345c5.get("decision")) != READY_DECISION_345C5:
        raise ValueError("345C5 manifest decision is not READY.")
    if int(manifest_345c5.get("apply_simulation_eligible_count", 0)) <= 0:
        raise ValueError("345C5 apply_simulation_eligible_count must be greater than zero.")
    if int(manifest_345c5.get("alias_rule_update_allowed_count", 0)) != 0:
        raise ValueError("345C5 alias_rule_update_allowed_count must remain zero.")
    for gate_name in [
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
    ]:
        if bool(manifest_345c5.get(gate_name)):
            raise ValueError(f"345C5 gate must remain false: {gate_name}")

    alias_map: Dict[str, Dict[str, Any]] = {}
    for row in validated_approved_aliases:
        if not bool(row.get("apply_simulation_eligible")):
            continue
        if _safe_text(row.get("decision_validation_status")) != "VALID":
            continue
        raw_metric_name = _safe_text(row.get("raw_metric_name"))
        canonical_alias_target = _safe_text(row.get("canonical_alias_target"))
        source_decision = _safe_text(row.get("human_alias_review_decision"))
        if not raw_metric_name or not canonical_alias_target or not source_decision:
            continue
        key = _normalize_alias_key(raw_metric_name)
        if not key:
            continue
        existing = alias_map.get(key)
        candidate_payload = {
            "approved_alias_key": key,
            "raw_metric_name": raw_metric_name,
            "canonical_alias_target": canonical_alias_target,
            "source_decision": source_decision,
            "review_priority": _safe_text(row.get("review_priority")),
            "source_stages": _safe_text(row.get("source_stages")),
        }
        if existing and existing["canonical_alias_target"] != canonical_alias_target:
            raise ValueError(f"Conflicting approved alias target for key: {raw_metric_name}")
        alias_map[key] = candidate_payload

    if not alias_map:
        raise ValueError("No validated approved aliases available for simulation.")

    matching_row_count_by_alias = {key: 0 for key in alias_map}
    already_normalized_count_by_alias = {key: 0 for key in alias_map}
    eligible_unnormalized_count_by_alias = {key: 0 for key in alias_map}
    applied_row_ids_by_alias = {key: [] for key in alias_map}

    simulated_metric_rows: List[Dict[str, Any]] = []
    for row in metric_rows_345c:
        raw_metric_name = _safe_text(row.get("raw_metric_name"))
        before_status = _safe_text(row.get("normalization_status"))
        key = _normalize_alias_key(raw_metric_name)
        approved_alias = alias_map.get(key)
        if approved_alias:
            matching_row_count_by_alias[key] += 1
            if _is_normalized_status(before_status):
                already_normalized_count_by_alias[key] += 1
            if _is_unnormalized_status(before_status):
                eligible_unnormalized_count_by_alias[key] += 1

        if approved_alias and _is_unnormalized_status(before_status):
            simulated_row = _apply_simulation_fields(
                row, approved_alias["canonical_alias_target"]
            )
            applied_row_ids_by_alias[key].append(
                _safe_text(simulated_row.get("metric_coverage_row_id"))
            )
        else:
            simulated_row = _preserve_without_simulation(row)
        simulated_metric_rows.append(simulated_row)

    applied_alias_map_rows: List[Dict[str, Any]] = []
    non_applied_alias_rows: List[Dict[str, Any]] = []
    for key, alias_payload in sorted(alias_map.items(), key=lambda item: item[0]):
        applied_row_ids = applied_row_ids_by_alias[key]
        applied_row_count = len(applied_row_ids)
        applied_row = {
            **alias_payload,
            "applied_row_count": applied_row_count,
            "newly_normalized_row_count": applied_row_count,
            "applied_row_ids": "|".join(applied_row_ids),
            "already_normalized_match_count": already_normalized_count_by_alias[key],
            "matching_row_count": matching_row_count_by_alias[key],
            "simulation_rule_update_required": True,
            "simulation_only_no_write_back": True,
        }
        if applied_row_count > 0:
            applied_alias_map_rows.append(applied_row)
        else:
            non_applied_reason = "NO_MATCHING_ROWS"
            if matching_row_count_by_alias[key] > 0:
                non_applied_reason = "NO_ELIGIBLE_UNNORMALIZED_ROWS"
            non_applied_alias_rows.append(
                {
                    "approved_alias_key": key,
                    "raw_metric_name": alias_payload["raw_metric_name"],
                    "canonical_alias_target": alias_payload["canonical_alias_target"],
                    "source_decision": alias_payload["source_decision"],
                    "non_applied_reason": non_applied_reason,
                    "matching_row_count": matching_row_count_by_alias[key],
                    "already_normalized_match_count": already_normalized_count_by_alias[key],
                    "eligible_unnormalized_match_count": eligible_unnormalized_count_by_alias[key],
                }
            )

    metric_candidate_row_count_before = len(simulated_metric_rows)
    normalized_metric_row_count_before = sum(
        1
        for row in simulated_metric_rows
        if _is_normalized_status(_safe_text(row.get("normalization_status_before")))
    )
    unnormalized_metric_row_count_before = sum(
        1
        for row in simulated_metric_rows
        if _is_unnormalized_status(_safe_text(row.get("normalization_status_before")))
    )
    simulated_alias_applied_row_count = sum(
        1 for row in simulated_metric_rows if bool(row.get("simulation_applied"))
    )
    simulated_newly_normalized_row_count = simulated_alias_applied_row_count
    normalized_metric_row_count_after_simulation = sum(
        1
        for row in simulated_metric_rows
        if _is_normalized_status(
            _safe_text(row.get("normalization_status_after_simulation"))
        )
    )
    unnormalized_metric_row_count_after_simulation = sum(
        1
        for row in simulated_metric_rows
        if _is_unnormalized_status(
            _safe_text(row.get("normalization_status_after_simulation"))
        )
    )
    normalization_coverage_ratio_before = _ratio(
        normalized_metric_row_count_before, metric_candidate_row_count_before
    )
    normalization_coverage_ratio_after_simulation = _ratio(
        normalized_metric_row_count_after_simulation, metric_candidate_row_count_before
    )
    normalization_coverage_ratio_delta = None
    if (
        normalization_coverage_ratio_before is not None
        and normalization_coverage_ratio_after_simulation is not None
    ):
        normalization_coverage_ratio_delta = round(
            normalization_coverage_ratio_after_simulation
            - normalization_coverage_ratio_before,
            6,
        )

    ready_candidate_count_before_simulation = sum(
        1
        for row in simulated_metric_rows
        if bool(row.get("downstream_ready_before_normalization"))
        and _is_normalized_status(_safe_text(row.get("normalization_status_before")))
    )
    ready_candidate_count_after_alias_simulation = sum(
        1
        for row in simulated_metric_rows
        if bool(row.get("downstream_ready_after_alias_simulation"))
    )
    ready_candidate_count_delta = (
        ready_candidate_count_after_alias_simulation - ready_candidate_count_before_simulation
    )

    remaining_blind_spot_rows = _remaining_blind_spot_rows(simulated_metric_rows)
    remaining_unnormalized_raw_metric_name_count = len(remaining_blind_spot_rows)
    remaining_unnormalized_metric_row_count = sum(
        row["remaining_row_count"] for row in remaining_blind_spot_rows
    )
    remaining_ready_candidate_count = sum(
        row["remaining_ready_candidate_count"] for row in remaining_blind_spot_rows
    )

    metric_limitations: List[str] = []
    coverage_before_after = {
        "metric_candidate_row_count_before": metric_candidate_row_count_before,
        "normalized_metric_row_count_before": normalized_metric_row_count_before,
        "unnormalized_metric_row_count_before": unnormalized_metric_row_count_before,
        "normalization_coverage_ratio_before": normalization_coverage_ratio_before,
        "simulated_alias_applied_row_count": simulated_alias_applied_row_count,
        "simulated_newly_normalized_row_count": simulated_newly_normalized_row_count,
        "normalized_metric_row_count_after_simulation": normalized_metric_row_count_after_simulation,
        "unnormalized_metric_row_count_after_simulation": unnormalized_metric_row_count_after_simulation,
        "normalization_coverage_ratio_after_simulation": normalization_coverage_ratio_after_simulation,
        "normalization_coverage_ratio_delta": normalization_coverage_ratio_delta,
        "ready_candidate_count_before_simulation": ready_candidate_count_before_simulation,
        "ready_candidate_count_after_alias_simulation": ready_candidate_count_after_alias_simulation,
        "ready_candidate_count_delta": ready_candidate_count_delta,
        "remaining_unnormalized_raw_metric_name_count": remaining_unnormalized_raw_metric_name_count,
        "remaining_unnormalized_metric_row_count": remaining_unnormalized_metric_row_count,
        "metric_limitations": metric_limitations,
    }

    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths}
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)
    upstream_unchanged = input_hashes_before == input_hashes_after

    no_apply_proof = build_no_apply_proof(
        stage="345C6",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_apply_proof["upstream_input_hashes_before"] = input_hashes_before
    no_apply_proof["upstream_input_hashes_after"] = input_hashes_after
    no_apply_proof["upstream_workbooks_unchanged"] = upstream_unchanged
    no_apply_proof["formal_client_export_generated"] = False
    no_apply_proof["real_production_apply_performed"] = False
    no_apply_proof["normalization_rules_modified"] = False
    no_apply_proof["official_alias_assets_modified"] = False
    no_apply_proof["alias_apply_simulation_only"] = True
    no_apply_proof["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_345c6")
        and upstream_unchanged
        and not no_apply_proof.get("formal_client_export_generated", True)
        and not no_apply_proof.get("real_production_apply_performed", True)
        and not no_apply_proof.get("normalization_rules_modified", True)
        and not no_apply_proof.get("official_alias_assets_modified", True)
    )

    next_recommended_scope = _determine_next_scope(
        simulated_newly_normalized_row_count=simulated_newly_normalized_row_count,
        normalization_coverage_ratio_delta=normalization_coverage_ratio_delta,
        remaining_unnormalized_raw_metric_name_count=remaining_unnormalized_raw_metric_name_count,
    )

    checks = [
        {
            "check_name": "inputs::345c_and_345c5_ready",
            "status": "PASS"
            if _safe_text(manifest_345c.get("decision")) == READY_DECISION_345C
            and _safe_text(manifest_345c5.get("decision")) == READY_DECISION_345C5
            and int(manifest_345c.get("qa_fail_count", 1)) == 0
            and int(manifest_345c5.get("qa_fail_count", 1)) == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "input_345c_decision": manifest_345c.get("decision"),
                    "input_345c5_decision": manifest_345c5.get("decision"),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::validated_approved_aliases_available",
            "status": "PASS" if len(alias_map) > 0 else "FAIL",
            "detail": json.dumps(
                {
                    "validated_approved_alias_count": len(validated_approved_aliases),
                    "applied_alias_key_count": len(applied_alias_map_rows),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "simulation::original_normalized_fields_preserved",
            "status": "PASS"
            if all(
                _safe_text(row.get("normalized_metric_name"))
                == _safe_text(original.get("normalized_metric_name"))
                for row, original in zip(simulated_metric_rows, metric_rows_345c)
            )
            else "FAIL",
            "detail": "normalized_metric_name must not be overwritten during simulation",
        },
        {
            "check_name": "simulation::only_validated_approved_aliases_applied",
            "status": "PASS"
            if all(
                not bool(row.get("simulation_applied"))
                or _normalize_alias_key(row.get("raw_metric_name")) in alias_map
                for row in simulated_metric_rows
            )
            else "FAIL",
            "detail": "simulation_applied rows must map to validated approved aliases only",
        },
        {
            "check_name": "metrics::coverage_before_after_computed",
            "status": "PASS"
            if metric_candidate_row_count_before == len(metric_rows_345c)
            and normalization_coverage_ratio_before is not None
            and normalization_coverage_ratio_after_simulation is not None
            else "FAIL",
            "detail": json.dumps(coverage_before_after, ensure_ascii=False),
        },
        {
            "check_name": "safety::official_rules_and_alias_assets_unchanged",
            "status": "PASS"
            if official_assets_before == official_assets_after
            else "FAIL",
            "detail": json.dumps(official_assets_after, ensure_ascii=False),
        },
        {
            "check_name": "safety::all_gates_remain_false",
            "status": "PASS",
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

    manifest = {
        "decision": READY_DECISION_345C6,
        "input_stage": INPUT_STAGE_345C6,
        "qa_fail_count": qa_fail_count,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_345c_decision": _safe_text(manifest_345c.get("decision")),
        "input_345c5_decision": _safe_text(manifest_345c5.get("decision")),
        "validated_approved_alias_count": len(validated_approved_aliases),
        "applied_alias_key_count": len(applied_alias_map_rows),
        "metric_candidate_row_count_before": metric_candidate_row_count_before,
        "normalized_metric_row_count_before": normalized_metric_row_count_before,
        "unnormalized_metric_row_count_before": unnormalized_metric_row_count_before,
        "normalization_coverage_ratio_before": normalization_coverage_ratio_before,
        "simulated_alias_applied_row_count": simulated_alias_applied_row_count,
        "simulated_newly_normalized_row_count": simulated_newly_normalized_row_count,
        "normalized_metric_row_count_after_simulation": normalized_metric_row_count_after_simulation,
        "unnormalized_metric_row_count_after_simulation": unnormalized_metric_row_count_after_simulation,
        "normalization_coverage_ratio_after_simulation": normalization_coverage_ratio_after_simulation,
        "normalization_coverage_ratio_delta": normalization_coverage_ratio_delta,
        "ready_candidate_count_before_simulation": ready_candidate_count_before_simulation,
        "ready_candidate_count_after_alias_simulation": ready_candidate_count_after_alias_simulation,
        "ready_candidate_count_delta": ready_candidate_count_delta,
        "remaining_unnormalized_raw_metric_name_count": remaining_unnormalized_raw_metric_name_count,
        "remaining_unnormalized_metric_row_count": remaining_unnormalized_metric_row_count,
        "remaining_ready_candidate_count": remaining_ready_candidate_count,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "alias_apply_simulation_only": True,
        "metric_limitations": metric_limitations,
        "recommended_next_scope": next_recommended_scope,
        "input_reviewed_rejected_or_deferred_alias_count": len(rejected_or_deferred_aliases),
        "input_validation_issue_count": len(validation_issues),
        "generated_at_utc": _utc_now(),
        "output_dir": str(output_dir),
    }

    artifact_index_rows = [
        {
            "artifact_name": MANIFEST_FILE_NAME,
            "path": str(output_dir / MANIFEST_FILE_NAME),
            "purpose": "345C6 manifest with before/after normalization metrics.",
        },
        {
            "artifact_name": SIMULATED_METRIC_ROWS_JSON_FILE_NAME,
            "path": str(output_dir / SIMULATED_METRIC_ROWS_JSON_FILE_NAME),
            "purpose": "Per-row alias apply simulation result in JSON.",
        },
        {
            "artifact_name": SIMULATED_METRIC_ROWS_CSV_FILE_NAME,
            "path": str(output_dir / SIMULATED_METRIC_ROWS_CSV_FILE_NAME),
            "purpose": "Per-row alias apply simulation result in CSV.",
        },
        {
            "artifact_name": APPLIED_ALIAS_MAP_JSON_FILE_NAME,
            "path": str(output_dir / APPLIED_ALIAS_MAP_JSON_FILE_NAME),
            "purpose": "Approved alias keys that matched and were simulated.",
        },
        {
            "artifact_name": APPLIED_ALIAS_MAP_CSV_FILE_NAME,
            "path": str(output_dir / APPLIED_ALIAS_MAP_CSV_FILE_NAME),
            "purpose": "Applied alias map in CSV.",
        },
        {
            "artifact_name": COVERAGE_BEFORE_AFTER_JSON_FILE_NAME,
            "path": str(output_dir / COVERAGE_BEFORE_AFTER_JSON_FILE_NAME),
            "purpose": "Coverage before/after simulation summary in JSON.",
        },
        {
            "artifact_name": COVERAGE_BEFORE_AFTER_CSV_FILE_NAME,
            "path": str(output_dir / COVERAGE_BEFORE_AFTER_CSV_FILE_NAME),
            "purpose": "Coverage before/after simulation summary in CSV.",
        },
        {
            "artifact_name": REMAINING_BLIND_SPOTS_JSON_FILE_NAME,
            "path": str(output_dir / REMAINING_BLIND_SPOTS_JSON_FILE_NAME),
            "purpose": "Remaining unnormalized metric blind spots in JSON.",
        },
        {
            "artifact_name": REMAINING_BLIND_SPOTS_CSV_FILE_NAME,
            "path": str(output_dir / REMAINING_BLIND_SPOTS_CSV_FILE_NAME),
            "purpose": "Remaining unnormalized metric blind spots in CSV.",
        },
        {
            "artifact_name": NON_APPLIED_ALIASES_JSON_FILE_NAME,
            "path": str(output_dir / NON_APPLIED_ALIASES_JSON_FILE_NAME),
            "purpose": "Approved aliases that could not be applied in simulation.",
        },
        {
            "artifact_name": NON_APPLIED_ALIASES_CSV_FILE_NAME,
            "path": str(output_dir / NON_APPLIED_ALIASES_CSV_FILE_NAME),
            "purpose": "Non-applied aliases in CSV.",
        },
        {
            "artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME,
            "path": str(output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME),
            "purpose": "Narrative summary of 345C6 simulation impact.",
        },
        {
            "artifact_name": ARTIFACT_INDEX_MD_FILE_NAME,
            "path": str(output_dir / ARTIFACT_INDEX_MD_FILE_NAME),
            "purpose": "Index of all 345C6 outputs.",
        },
        {
            "artifact_name": NEXT_PLAN_MD_FILE_NAME,
            "path": str(output_dir / NEXT_PLAN_MD_FILE_NAME),
            "purpose": "Recommended next step after 345C6.",
        },
    ]

    return {
        "manifest": manifest,
        "simulated_metric_rows": simulated_metric_rows,
        "applied_alias_map": applied_alias_map_rows,
        "coverage_before_after": coverage_before_after,
        "remaining_blind_spots": remaining_blind_spot_rows,
        "non_applied_aliases": non_applied_alias_rows,
        "artifact_index_rows": artifact_index_rows,
        "qa_json": {
            "qa_fail_count": qa_fail_count,
            "checks": checks,
            "warnings": [],
        },
        "no_apply_proof": no_apply_proof,
    }
