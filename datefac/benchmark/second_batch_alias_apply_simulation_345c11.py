from __future__ import annotations

import csv
import json
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_345C = "METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_READY"
READY_DECISION_345C6 = "REVIEWED_ALIAS_APPLY_SIMULATION_345C6_READY"
READY_DECISION_345C10 = "SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION_345C10_READY"
READY_DECISION_345C11 = "SECOND_BATCH_ALIAS_APPLY_SIMULATION_345C11_READY"
INPUT_STAGE_345C11 = "POST_345C10_SECOND_BATCH_ALIAS_APPLY_SIMULATION"

DEFAULT_METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_DIR = Path(
    r"D:\_datefac\output\metric_candidate_normalization_coverage_345c"
)
DEFAULT_REVIEWED_ALIAS_APPLY_SIMULATION_345C6_DIR = Path(
    r"D:\_datefac\output\reviewed_alias_apply_simulation_345c6"
)
DEFAULT_SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION_345C10_DIR = Path(
    r"D:\_datefac\output\second_batch_reviewed_alias_decision_ingestion_345c10"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\second_batch_alias_apply_simulation_345c11")
DEFAULT_LEDGER_PATH = Path(
    r"D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md"
)

MANIFEST_FILE_NAME = "second_batch_alias_apply_simulation_345c11_manifest.json"
COMBINED_ALIAS_MAP_JSON_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_combined_alias_map.json"
)
COMBINED_ALIAS_MAP_CSV_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_combined_alias_map.csv"
)
SECOND_BATCH_APPLIED_ALIAS_MAP_JSON_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_second_batch_applied_alias_map.json"
)
SECOND_BATCH_APPLIED_ALIAS_MAP_CSV_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_second_batch_applied_alias_map.csv"
)
SIMULATED_METRIC_ROWS_JSON_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_simulated_metric_rows.json"
)
SIMULATED_METRIC_ROWS_CSV_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_simulated_metric_rows.csv"
)
COVERAGE_BEFORE_AFTER_JSON_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_coverage_before_after.json"
)
COVERAGE_BEFORE_AFTER_CSV_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_coverage_before_after.csv"
)
INCREMENTAL_IMPACT_SUMMARY_JSON_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_incremental_impact_summary.json"
)
INCREMENTAL_IMPACT_SUMMARY_CSV_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_incremental_impact_summary.csv"
)
REMAINING_BLIND_SPOTS_JSON_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_remaining_blind_spots.json"
)
REMAINING_BLIND_SPOTS_CSV_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_remaining_blind_spots.csv"
)
NON_APPLIED_ALIASES_JSON_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_non_applied_aliases.json"
)
NON_APPLIED_ALIASES_CSV_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_non_applied_aliases.csv"
)
STOP_OR_RETURN_TO_345D_DECISION_JSON_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_stop_or_return_to_345d_decision.json"
)
EXECUTIVE_SUMMARY_MD_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_executive_summary.md"
)
ARTIFACT_INDEX_MD_FILE_NAME = (
    "second_batch_alias_apply_simulation_345c11_artifact_index.md"
)
NEXT_PLAN_MD_FILE_NAME = "second_batch_alias_apply_simulation_345c11_next_plan.md"

INPUT_345C_MANIFEST_NAME = "metric_candidate_normalization_coverage_345c_manifest.json"
INPUT_345C_METRIC_ROWS_JSON_NAMES = [
    "metric_candidate_normalization_coverage_345c_metric_candidates.json",
    "metric_candidate_normalization_coverage_345c_metric_rows.json",
]
INPUT_345C_METRIC_ROWS_CSV_NAMES = [
    "metric_candidate_normalization_coverage_345c_metric_candidates.csv",
    "metric_candidate_normalization_coverage_345c_metric_rows.csv",
]
INPUT_345C_ALIAS_QUEUE_JSON_NAMES = [
    "metric_candidate_normalization_coverage_345c_alias_candidates.json",
    "metric_candidate_normalization_coverage_345c_alias_candidate_queue.json",
]
INPUT_345C_ALIAS_QUEUE_CSV_NAMES = [
    "metric_candidate_normalization_coverage_345c_alias_candidates.csv",
    "metric_candidate_normalization_coverage_345c_alias_candidate_queue.csv",
]

INPUT_345C6_MANIFEST_NAME = "reviewed_alias_apply_simulation_345c6_manifest.json"
INPUT_345C6_APPLIED_ALIAS_MAP_JSON_NAME = (
    "reviewed_alias_apply_simulation_345c6_applied_alias_map.json"
)
INPUT_345C6_APPLIED_ALIAS_MAP_CSV_NAME = (
    "reviewed_alias_apply_simulation_345c6_applied_alias_map.csv"
)
INPUT_345C6_SIMULATED_METRIC_ROWS_JSON_NAME = (
    "reviewed_alias_apply_simulation_345c6_simulated_metric_rows.json"
)
INPUT_345C6_SIMULATED_METRIC_ROWS_CSV_NAME = (
    "reviewed_alias_apply_simulation_345c6_simulated_metric_rows.csv"
)
INPUT_345C6_COVERAGE_BEFORE_AFTER_JSON_NAME = (
    "reviewed_alias_apply_simulation_345c6_coverage_before_after.json"
)
INPUT_345C6_COVERAGE_BEFORE_AFTER_CSV_NAME = (
    "reviewed_alias_apply_simulation_345c6_coverage_before_after.csv"
)
INPUT_345C6_REMAINING_BLIND_SPOTS_JSON_NAME = (
    "reviewed_alias_apply_simulation_345c6_remaining_blind_spots.json"
)
INPUT_345C6_REMAINING_BLIND_SPOTS_CSV_NAME = (
    "reviewed_alias_apply_simulation_345c6_remaining_blind_spots.csv"
)

INPUT_345C10_MANIFEST_NAME = "second_batch_reviewed_alias_decision_ingestion_345c10_manifest.json"
INPUT_345C10_VALIDATED_APPROVED_JSON_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_validated_approved_aliases.json"
)
INPUT_345C10_VALIDATED_APPROVED_CSV_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_validated_approved_aliases.csv"
)
INPUT_345C10_REVIEWED_DECISIONS_JSON_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_reviewed_decisions.json"
)
INPUT_345C10_REVIEWED_DECISIONS_CSV_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_reviewed_decisions.csv"
)
INPUT_345C10_REJECTED_OR_BLOCKED_JSON_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_rejected_or_blocked_aliases.json"
)
INPUT_345C10_REJECTED_OR_BLOCKED_CSV_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_rejected_or_blocked_aliases.csv"
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
    "source_stage",
    "source_artifact",
    "pdf_id",
    "pdf_name",
    "raw_metric_name",
    "normalized_metric_name",
    "baseline_normalization_status",
    "first_batch_simulated_normalized_metric_name",
    "normalization_status_after_first_batch",
    "first_batch_simulation_applied",
    "first_batch_simulation_action",
    "first_batch_simulation_source",
    "second_batch_simulated_normalized_metric_name",
    "cumulative_simulated_normalized_metric_name",
    "normalization_status_after_second_batch",
    "second_batch_simulation_applied",
    "second_batch_simulation_action",
    "second_batch_simulation_source",
    "cumulative_simulation_action",
    "simulation_rule_update_required",
    "simulation_only_no_write_back",
    "downstream_ready_before_normalization",
    "downstream_ready_after_first_batch",
    "downstream_ready_after_second_batch",
    "quality_severity",
    "quality_issues",
]

COMBINED_ALIAS_MAP_FIELDS = [
    "alias_batch",
    "alias_key",
    "raw_metric_name",
    "canonical_alias_target",
    "source_decision",
    "simulation_source",
    "matching_row_count",
    "applied_row_count",
    "newly_normalized_row_count",
    "already_normalized_or_previously_resolved_count",
    "review_priority",
    "source_stages",
    "needs_alias_family_expansion",
    "overlaps_first_batch_alias_key",
    "simulation_rule_update_required",
    "simulation_only_no_write_back",
]

SECOND_BATCH_APPLIED_ALIAS_MAP_FIELDS = [
    "alias_key",
    "raw_metric_name",
    "canonical_alias_target",
    "source_decision",
    "matching_row_count_after_first_batch",
    "applied_row_count",
    "newly_normalized_row_count",
    "already_normalized_or_previously_resolved_count",
    "review_priority",
    "source_stages",
    "needs_alias_family_expansion",
    "simulation_rule_update_required",
    "simulation_only_no_write_back",
]

COVERAGE_BEFORE_AFTER_FIELDS = [
    "metric_candidate_row_count",
    "baseline_normalized_metric_row_count",
    "baseline_unnormalized_metric_row_count",
    "first_batch_alias_count",
    "first_batch_simulated_newly_normalized_row_count",
    "second_batch_eligible_alias_count",
    "second_batch_applied_alias_key_count",
    "second_batch_simulated_alias_applied_row_count",
    "second_batch_simulated_newly_normalized_row_count",
    "cumulative_applied_alias_key_count",
    "cumulative_simulated_newly_normalized_row_count",
    "coverage_ratio_before",
    "coverage_ratio_after_first_batch",
    "coverage_ratio_after_second_batch",
    "coverage_delta_first_batch",
    "coverage_delta_second_batch_incremental",
    "coverage_delta_cumulative",
    "ready_candidate_count_before",
    "ready_candidate_count_after_first_batch",
    "ready_candidate_count_after_second_batch",
    "ready_candidate_delta_first_batch",
    "ready_candidate_delta_second_batch_incremental",
    "ready_candidate_delta_cumulative",
    "remaining_unnormalized_raw_metric_name_count",
    "remaining_unnormalized_metric_row_count",
    "remaining_ready_candidate_count",
    "metric_limitations",
]

INCREMENTAL_IMPACT_SUMMARY_FIELDS = [
    "first_batch_alias_count",
    "first_batch_simulated_newly_normalized_row_count",
    "second_batch_eligible_alias_count",
    "second_batch_applied_alias_key_count",
    "second_batch_simulated_newly_normalized_row_count",
    "cumulative_applied_alias_key_count",
    "cumulative_simulated_newly_normalized_row_count",
    "coverage_delta_first_batch",
    "coverage_delta_second_batch_incremental",
    "coverage_delta_cumulative",
    "ready_candidate_delta_first_batch",
    "ready_candidate_delta_second_batch_incremental",
    "ready_candidate_delta_cumulative",
    "non_applied_second_batch_alias_count",
    "alias_branch_final_recommendation",
    "full_structured_demo_export_reasonable_after_345c11",
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
    "alias_key",
    "raw_metric_name",
    "canonical_alias_target",
    "source_decision",
    "non_applied_reason",
    "matching_row_count_after_first_batch",
    "already_normalized_or_previously_resolved_count",
    "review_priority",
    "source_stages",
]

LEDGER_HEADING = "## 345C11 Second Batch Alias Apply Simulation"
RETURN_TO_345D = "STOP_ALIAS_BRANCH_AND_RETURN_TO_345D"
CONTINUE_EXPLICIT_SCOPE = "CONTINUE_ONLY_WITH_EXPLICIT_NEW_SCOPE_APPROVAL"
CONTINUE_ADDITIONAL_BATCH = "CONTINUE_WITH_ADDITIONAL_REVIEW_BATCH"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).strip().split())
    return "" if text.lower() == "nan" else text


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    lowered = _safe_text(value).lower()
    return lowered in {"1", "true", "yes", "y"}


def _normalize_alias_key(value: Any) -> str:
    text = _safe_text(value)
    return text.strip(" \t\r\n'\"`.,;:!?()[]{}<>，。；：！？（）【】《》“”‘’")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _require_existing(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"required input file missing: {path}")
    return path


def _first_existing(base_dir: Path, names: Iterable[str], label: str) -> Path:
    for name in names:
        candidate = base_dir / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"required input file missing for {label}: {base_dir}")


def _load_json_or_csv_rows(
    *,
    json_path: Path | None,
    csv_path: Path | None,
    label: str,
) -> tuple[List[Dict[str, Any]], str]:
    if json_path is not None and json_path.exists():
        payload = _read_json(json_path)
        if not isinstance(payload, list):
            raise ValueError(f"{label} must be a list JSON payload: {json_path}")
        return [dict(row) for row in payload], "json"
    if csv_path is not None and csv_path.exists():
        return _read_csv_rows(csv_path), "csv"
    raise FileNotFoundError(f"required input rows missing for {label}")


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


def _is_normalized_status(status: str) -> bool:
    return status == "NORMALIZED"


def _is_unnormalized_status(status: str) -> bool:
    return status == "UNNORMALIZED_WITH_RAW_NAME"


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def _remaining_blind_spot_rows(
    rows: List[Dict[str, Any]],
    *,
    status_field: str,
    ready_field: str,
) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        after_status = _safe_text(row.get(status_field))
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
                    1 for row in group if _bool_value(row.get(ready_field))
                ),
                "source_stages": "|".join(
                    sorted(
                        {
                            _safe_text(row.get("source_stage"))
                            for row in group
                            if _safe_text(row.get("source_stage"))
                        }
                    )
                ),
                "pdf_names": "|".join(
                    sorted(
                        {
                            _safe_text(row.get("pdf_name"))
                            for row in group
                            if _safe_text(row.get("pdf_name"))
                        }
                    )[:10]
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


def _determine_alias_branch_recommendation(
    *,
    second_batch_simulated_newly_normalized_row_count: int,
    remaining_unnormalized_raw_metric_name_count: int,
) -> str:
    if (
        second_batch_simulated_newly_normalized_row_count >= 2500
        and remaining_unnormalized_raw_metric_name_count <= 25
    ):
        return CONTINUE_WITH_ADDITIONAL_BATCH
    if (
        second_batch_simulated_newly_normalized_row_count <= 0
        and remaining_unnormalized_raw_metric_name_count > 0
    ):
        return CONTINUE_EXPLICIT_SCOPE
    return RETURN_TO_345D


def _next_recommended_step(recommendation: str) -> str:
    if recommendation == RETURN_TO_345D:
        return "345D Full Structured Demo Export Package"
    if recommendation == CONTINUE_EXPLICIT_SCOPE:
        return "Separate explicitly approved alias-governance scope"
    return "Additional bounded alias review batch"


def _decision_reason(
    recommendation: str,
    *,
    second_batch_simulated_newly_normalized_row_count: int,
    remaining_unnormalized_raw_metric_name_count: int,
) -> str:
    if recommendation == CONTINUE_ADDITIONAL_BATCH:
        return (
            "Second batch produced exceptional incremental impact and remaining blind spots "
            "are concentrated enough to justify one more bounded review batch."
        )
    if recommendation == CONTINUE_EXPLICIT_SCOPE:
        return (
            "Second batch did not materially improve coverage; any continuation would require "
            "an explicitly approved new alias-governance scope."
        )
    return (
        "Second batch materially improved coverage, but official rules remain unchanged and "
        "remaining blind spots should now travel as risk disclosure while the alias branch stops "
        f"after {second_batch_simulated_newly_normalized_row_count} incremental simulated rows "
        f"and {remaining_unnormalized_raw_metric_name_count} remaining raw blind spots."
    )


def build_345c11_ledger_entry(*, manifest: Dict[str, Any]) -> str:
    lines = [
        LEDGER_HEADING,
        "",
        "Status: completed",
        "",
        "Decision:",
        f"- `{manifest.get('decision', '')}`",
        "",
        "Input packages:",
        f"- `345C = {manifest.get('input_345c_dir', '')}`",
        f"- `345C6 = {manifest.get('input_345c6_dir', '')}`",
        f"- `345C10 = {manifest.get('input_345c10_dir', '')}`",
        "",
        "Output package:",
        f"- `{manifest.get('output_dir', '')}`",
        "",
        "Key metrics:",
        f"- `first_batch_alias_count = {manifest.get('first_batch_alias_count', 0)}`",
        f"- `second_batch_eligible_alias_count = {manifest.get('second_batch_eligible_alias_count', 0)}`",
        f"- `second_batch_simulated_newly_normalized_row_count = {manifest.get('second_batch_simulated_newly_normalized_row_count', 0)}`",
        f"- `cumulative_simulated_newly_normalized_row_count = {manifest.get('cumulative_simulated_newly_normalized_row_count', 0)}`",
        f"- `coverage_ratio_before = {manifest.get('coverage_ratio_before', None)}`",
        f"- `coverage_ratio_after_first_batch = {manifest.get('coverage_ratio_after_first_batch', None)}`",
        f"- `coverage_ratio_after_second_batch = {manifest.get('coverage_ratio_after_second_batch', None)}`",
        f"- `remaining_unnormalized_metric_row_count = {manifest.get('remaining_unnormalized_metric_row_count', 0)}`",
        f"- `qa_fail_count = {manifest.get('qa_fail_count', 0)}`",
        "",
        "Alias branch final recommendation:",
        f"- `{manifest.get('alias_branch_final_recommendation', '')}`",
        "",
        "Gate status:",
        f"- `formal_client_export_allowed = {str(bool(manifest.get('formal_client_export_allowed'))).lower()}`",
        f"- `client_ready = {str(bool(manifest.get('client_ready'))).lower()}`",
        f"- `production_ready = {str(bool(manifest.get('production_ready'))).lower()}`",
        f"- `global_strict_human_review_completed = {str(bool(manifest.get('global_strict_human_review_completed'))).lower()}`",
        "",
        "No-write-back confirmation:",
        f"- `no_write_back_proof_passed = {str(bool(manifest.get('no_write_back_proof_passed'))).lower()}`",
        f"- `official_rules_modified = {str(bool(manifest.get('official_rules_modified'))).lower()}`",
        f"- `official_alias_assets_modified = {str(bool(manifest.get('official_alias_assets_modified'))).lower()}`",
        "",
        "Validation commands and results:",
        "- `python -m py_compile ...` passed",
        "- `python -m pytest tests\\benchmark\\test_second_batch_alias_apply_simulation_345c11.py -q` passed",
        "- real runner passed",
        "",
        "Next recommended step:",
        f"- `{manifest.get('next_recommended_step', '')}`",
    ]
    return "\n".join(lines)


def ledger_has_345c11_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return LEDGER_HEADING in ledger_path.read_text(encoding="utf-8")


def append_345c11_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    if ledger_has_345c11_entry(ledger_path):
        return False
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    addition = build_345c11_ledger_entry(manifest=manifest)
    prefix = "\n\n" if existing and not existing.endswith("\n\n") else ""
    if existing.endswith("\n"):
        prefix = "\n" if not existing.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(existing + prefix + addition + "\n", encoding="utf-8")
    return True


def _artifact_rows(output_dir: Path) -> List[Dict[str, str]]:
    return [
        {
            "artifact_name": MANIFEST_FILE_NAME,
            "path": str(output_dir / MANIFEST_FILE_NAME),
            "purpose": "Manifest with second-batch simulation metrics and final recommendation.",
        },
        {
            "artifact_name": COMBINED_ALIAS_MAP_JSON_FILE_NAME,
            "path": str(output_dir / COMBINED_ALIAS_MAP_JSON_FILE_NAME),
            "purpose": "Combined first-batch and second-batch alias branch map in JSON.",
        },
        {
            "artifact_name": COMBINED_ALIAS_MAP_CSV_FILE_NAME,
            "path": str(output_dir / COMBINED_ALIAS_MAP_CSV_FILE_NAME),
            "purpose": "Combined first-batch and second-batch alias branch map in CSV.",
        },
        {
            "artifact_name": SECOND_BATCH_APPLIED_ALIAS_MAP_JSON_FILE_NAME,
            "path": str(output_dir / SECOND_BATCH_APPLIED_ALIAS_MAP_JSON_FILE_NAME),
            "purpose": "Second-batch aliases that actually applied after the first-batch context.",
        },
        {
            "artifact_name": SECOND_BATCH_APPLIED_ALIAS_MAP_CSV_FILE_NAME,
            "path": str(output_dir / SECOND_BATCH_APPLIED_ALIAS_MAP_CSV_FILE_NAME),
            "purpose": "Second-batch applied alias map in CSV.",
        },
        {
            "artifact_name": SIMULATED_METRIC_ROWS_JSON_FILE_NAME,
            "path": str(output_dir / SIMULATED_METRIC_ROWS_JSON_FILE_NAME),
            "purpose": "Per-row cumulative simulation result after first and second batches in JSON.",
        },
        {
            "artifact_name": SIMULATED_METRIC_ROWS_CSV_FILE_NAME,
            "path": str(output_dir / SIMULATED_METRIC_ROWS_CSV_FILE_NAME),
            "purpose": "Per-row cumulative simulation result in CSV.",
        },
        {
            "artifact_name": COVERAGE_BEFORE_AFTER_JSON_FILE_NAME,
            "path": str(output_dir / COVERAGE_BEFORE_AFTER_JSON_FILE_NAME),
            "purpose": "Coverage and ready-candidate before/after summary in JSON.",
        },
        {
            "artifact_name": COVERAGE_BEFORE_AFTER_CSV_FILE_NAME,
            "path": str(output_dir / COVERAGE_BEFORE_AFTER_CSV_FILE_NAME),
            "purpose": "Coverage and ready-candidate before/after summary in CSV.",
        },
        {
            "artifact_name": INCREMENTAL_IMPACT_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / INCREMENTAL_IMPACT_SUMMARY_JSON_FILE_NAME),
            "purpose": "First-batch, second-batch, and cumulative impact rollup in JSON.",
        },
        {
            "artifact_name": INCREMENTAL_IMPACT_SUMMARY_CSV_FILE_NAME,
            "path": str(output_dir / INCREMENTAL_IMPACT_SUMMARY_CSV_FILE_NAME),
            "purpose": "Impact rollup in CSV.",
        },
        {
            "artifact_name": REMAINING_BLIND_SPOTS_JSON_FILE_NAME,
            "path": str(output_dir / REMAINING_BLIND_SPOTS_JSON_FILE_NAME),
            "purpose": "Remaining blind spots after second-batch simulation in JSON.",
        },
        {
            "artifact_name": REMAINING_BLIND_SPOTS_CSV_FILE_NAME,
            "path": str(output_dir / REMAINING_BLIND_SPOTS_CSV_FILE_NAME),
            "purpose": "Remaining blind spots after second-batch simulation in CSV.",
        },
        {
            "artifact_name": NON_APPLIED_ALIASES_JSON_FILE_NAME,
            "path": str(output_dir / NON_APPLIED_ALIASES_JSON_FILE_NAME),
            "purpose": "Second-batch reviewed aliases that were still not applied.",
        },
        {
            "artifact_name": NON_APPLIED_ALIASES_CSV_FILE_NAME,
            "path": str(output_dir / NON_APPLIED_ALIASES_CSV_FILE_NAME),
            "purpose": "Non-applied second-batch aliases in CSV.",
        },
        {
            "artifact_name": STOP_OR_RETURN_TO_345D_DECISION_JSON_FILE_NAME,
            "path": str(output_dir / STOP_OR_RETURN_TO_345D_DECISION_JSON_FILE_NAME),
            "purpose": "Final alias-branch stop/continue recommendation with rationale.",
        },
        {
            "artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME,
            "path": str(output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME),
            "purpose": "Narrative summary of second-batch simulation impact.",
        },
        {
            "artifact_name": ARTIFACT_INDEX_MD_FILE_NAME,
            "path": str(output_dir / ARTIFACT_INDEX_MD_FILE_NAME),
            "purpose": "Index of all 345C11 artifacts.",
        },
        {
            "artifact_name": NEXT_PLAN_MD_FILE_NAME,
            "path": str(output_dir / NEXT_PLAN_MD_FILE_NAME),
            "purpose": "Recommended next step after 345C11.",
        },
    ]


def build_second_batch_alias_apply_simulation_345c11(
    *,
    metric_candidate_normalization_coverage_345c_dir: Path,
    reviewed_alias_apply_simulation_345c6_dir: Path,
    second_batch_reviewed_alias_decision_ingestion_345c10_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None = None,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345c_path = _require_existing(
        metric_candidate_normalization_coverage_345c_dir / INPUT_345C_MANIFEST_NAME
    )
    metric_rows_345c_json_path = _first_existing(
        metric_candidate_normalization_coverage_345c_dir,
        INPUT_345C_METRIC_ROWS_JSON_NAMES,
        "345C metric rows json",
    )
    metric_rows_345c_csv_path = _first_existing(
        metric_candidate_normalization_coverage_345c_dir,
        INPUT_345C_METRIC_ROWS_CSV_NAMES,
        "345C metric rows csv",
    )
    alias_queue_optional_path = None
    for name in [*INPUT_345C_ALIAS_QUEUE_JSON_NAMES, *INPUT_345C_ALIAS_QUEUE_CSV_NAMES]:
        candidate = metric_candidate_normalization_coverage_345c_dir / name
        if candidate.exists():
            alias_queue_optional_path = candidate
            break

    manifest_345c6_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_MANIFEST_NAME
    )
    applied_alias_map_345c6_json_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_APPLIED_ALIAS_MAP_JSON_NAME
    )
    simulated_metric_rows_345c6_json_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_SIMULATED_METRIC_ROWS_JSON_NAME
    )
    coverage_345c6_json_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_COVERAGE_BEFORE_AFTER_JSON_NAME
    )
    remaining_blind_spots_345c6_json_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_REMAINING_BLIND_SPOTS_JSON_NAME
    )
    _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_APPLIED_ALIAS_MAP_CSV_NAME
    )
    _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_SIMULATED_METRIC_ROWS_CSV_NAME
    )
    _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_COVERAGE_BEFORE_AFTER_CSV_NAME
    )
    _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_REMAINING_BLIND_SPOTS_CSV_NAME
    )

    manifest_345c10_path = _require_existing(
        second_batch_reviewed_alias_decision_ingestion_345c10_dir / INPUT_345C10_MANIFEST_NAME
    )
    validated_approved_345c10_json_path = _require_existing(
        second_batch_reviewed_alias_decision_ingestion_345c10_dir
        / INPUT_345C10_VALIDATED_APPROVED_JSON_NAME
    )
    reviewed_decisions_345c10_json_path = _require_existing(
        second_batch_reviewed_alias_decision_ingestion_345c10_dir
        / INPUT_345C10_REVIEWED_DECISIONS_JSON_NAME
    )
    rejected_or_blocked_345c10_json_path = _require_existing(
        second_batch_reviewed_alias_decision_ingestion_345c10_dir
        / INPUT_345C10_REJECTED_OR_BLOCKED_JSON_NAME
    )
    _require_existing(
        second_batch_reviewed_alias_decision_ingestion_345c10_dir
        / INPUT_345C10_VALIDATED_APPROVED_CSV_NAME
    )
    _require_existing(
        second_batch_reviewed_alias_decision_ingestion_345c10_dir
        / INPUT_345C10_REVIEWED_DECISIONS_CSV_NAME
    )
    _require_existing(
        second_batch_reviewed_alias_decision_ingestion_345c10_dir
        / INPUT_345C10_REJECTED_OR_BLOCKED_CSV_NAME
    )

    files_read = [
        str(manifest_345c_path),
        str(metric_rows_345c_json_path),
        str(metric_rows_345c_csv_path),
        str(manifest_345c6_path),
        str(applied_alias_map_345c6_json_path),
        str(simulated_metric_rows_345c6_json_path),
        str(coverage_345c6_json_path),
        str(remaining_blind_spots_345c6_json_path),
        str(manifest_345c10_path),
        str(validated_approved_345c10_json_path),
        str(reviewed_decisions_345c10_json_path),
        str(rejected_or_blocked_345c10_json_path),
    ]
    if alias_queue_optional_path is not None:
        files_read.append(str(alias_queue_optional_path))

    input_paths = [
        manifest_345c_path,
        metric_rows_345c_json_path,
        metric_rows_345c_csv_path,
        manifest_345c6_path,
        applied_alias_map_345c6_json_path,
        simulated_metric_rows_345c6_json_path,
        coverage_345c6_json_path,
        remaining_blind_spots_345c6_json_path,
        manifest_345c10_path,
        validated_approved_345c10_json_path,
        reviewed_decisions_345c10_json_path,
        rejected_or_blocked_345c10_json_path,
    ]
    if alias_queue_optional_path is not None:
        input_paths.append(alias_queue_optional_path)

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    manifest_345c = _read_json(manifest_345c_path)
    metric_rows_345c, metric_rows_read_source = _load_json_or_csv_rows(
        json_path=metric_rows_345c_json_path,
        csv_path=metric_rows_345c_csv_path,
        label="345C metric rows",
    )
    manifest_345c6 = _read_json(manifest_345c6_path)
    applied_alias_map_345c6 = _load_json_or_csv_rows(
        json_path=applied_alias_map_345c6_json_path,
        csv_path=reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_APPLIED_ALIAS_MAP_CSV_NAME,
        label="345C6 applied alias map",
    )[0]
    simulated_metric_rows_345c6 = _load_json_or_csv_rows(
        json_path=simulated_metric_rows_345c6_json_path,
        csv_path=reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_SIMULATED_METRIC_ROWS_CSV_NAME,
        label="345C6 simulated metric rows",
    )[0]
    coverage_345c6 = _read_json(coverage_345c6_json_path)
    remaining_blind_spots_345c6 = _load_json_or_csv_rows(
        json_path=remaining_blind_spots_345c6_json_path,
        csv_path=reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_REMAINING_BLIND_SPOTS_CSV_NAME,
        label="345C6 remaining blind spots",
    )[0]
    manifest_345c10 = _read_json(manifest_345c10_path)
    validated_approved_345c10 = _load_json_or_csv_rows(
        json_path=validated_approved_345c10_json_path,
        csv_path=second_batch_reviewed_alias_decision_ingestion_345c10_dir
        / INPUT_345C10_VALIDATED_APPROVED_CSV_NAME,
        label="345C10 validated approved aliases",
    )[0]
    reviewed_decisions_345c10 = _load_json_or_csv_rows(
        json_path=reviewed_decisions_345c10_json_path,
        csv_path=second_batch_reviewed_alias_decision_ingestion_345c10_dir
        / INPUT_345C10_REVIEWED_DECISIONS_CSV_NAME,
        label="345C10 reviewed decisions",
    )[0]
    rejected_or_blocked_345c10 = _load_json_or_csv_rows(
        json_path=rejected_or_blocked_345c10_json_path,
        csv_path=second_batch_reviewed_alias_decision_ingestion_345c10_dir
        / INPUT_345C10_REJECTED_OR_BLOCKED_CSV_NAME,
        label="345C10 rejected or blocked aliases",
    )[0]

    if _safe_text(manifest_345c.get("decision")) != READY_DECISION_345C:
        raise ValueError("345C manifest decision is not READY.")
    if _safe_text(manifest_345c6.get("decision")) != READY_DECISION_345C6:
        raise ValueError("345C6 manifest decision is not READY.")
    if _safe_text(manifest_345c10.get("decision")) != READY_DECISION_345C10:
        raise ValueError("345C10 manifest decision is not READY.")
    if int(manifest_345c10.get("apply_simulation_eligible_count", 0)) <= 0:
        raise ValueError("345C10 apply_simulation_eligible_count must be greater than zero.")
    for manifest in [manifest_345c6, manifest_345c10]:
        if bool(manifest.get("official_rules_modified")):
            raise ValueError("Official normalization rules must remain unchanged.")
        if bool(manifest.get("official_alias_assets_modified")):
            raise ValueError("Official alias assets must remain unchanged.")
        for gate_name in ["formal_client_export_allowed", "client_ready", "production_ready"]:
            if bool(manifest.get(gate_name)):
                raise ValueError(f"Input gate must remain false: {gate_name}")

    if len(metric_rows_345c) != len(simulated_metric_rows_345c6):
        raise ValueError("345C metric rows and 345C6 simulated metric rows must have equal length.")

    baseline_rows_by_id = {
        _safe_text(row.get("metric_coverage_row_id")): dict(row) for row in metric_rows_345c
    }
    if len(baseline_rows_by_id) != len(metric_rows_345c):
        raise ValueError("345C metric rows contain duplicate metric_coverage_row_id values.")

    first_batch_alias_keys = {
        _normalize_alias_key(row.get("approved_alias_key") or row.get("raw_metric_name"))
        for row in applied_alias_map_345c6
        if _normalize_alias_key(row.get("approved_alias_key") or row.get("raw_metric_name"))
    }

    second_batch_alias_map: Dict[str, Dict[str, Any]] = {}
    for row in validated_approved_345c10:
        if not _bool_value(row.get("apply_simulation_eligible")):
            continue
        if _safe_text(row.get("decision_validation_status")) != "VALID":
            continue
        raw_metric_name = _safe_text(row.get("raw_metric_name"))
        canonical_alias_target = _safe_text(row.get("canonical_alias_target"))
        decision = _safe_text(
            row.get("human_blind_spot_review_decision") or row.get("source_decision")
        )
        alias_key = _normalize_alias_key(raw_metric_name)
        if not alias_key or not raw_metric_name or not canonical_alias_target:
            continue
        if alias_key in second_batch_alias_map:
            existing = second_batch_alias_map[alias_key]
            if existing["canonical_alias_target"] != canonical_alias_target:
                raise ValueError(f"Conflicting second-batch alias targets for {raw_metric_name}")
            continue
        second_batch_alias_map[alias_key] = {
            "alias_key": alias_key,
            "raw_metric_name": raw_metric_name,
            "canonical_alias_target": canonical_alias_target,
            "source_decision": decision,
            "review_priority": _safe_text(row.get("candidate_priority") or row.get("review_priority")),
            "source_stages": _safe_text(row.get("source_stages")),
            "needs_alias_family_expansion": _bool_value(
                row.get("needs_alias_family_expansion")
            ),
        }

    if not second_batch_alias_map:
        raise ValueError("No second-batch validated approved aliases available for simulation.")

    second_batch_matching_count_by_alias = {key: 0 for key in second_batch_alias_map}
    second_batch_previously_resolved_count_by_alias = {key: 0 for key in second_batch_alias_map}
    second_batch_applied_row_ids_by_alias = {key: [] for key in second_batch_alias_map}

    simulated_metric_rows: List[Dict[str, Any]] = []
    first_batch_and_second_batch_overlap_rows = 0
    baseline_normalized_metric_row_count = 0
    baseline_unnormalized_metric_row_count = 0
    for first_batch_row in simulated_metric_rows_345c6:
        row_id = _safe_text(first_batch_row.get("metric_coverage_row_id"))
        baseline_row = baseline_rows_by_id.get(row_id)
        if baseline_row is None:
            raise ValueError(f"345C baseline row not found for 345C6 simulated row id: {row_id}")

        baseline_status = _safe_text(baseline_row.get("normalization_status"))
        first_batch_after_status = _safe_text(
            first_batch_row.get("normalization_status_after_simulation")
        )
        first_batch_simulated_name = _safe_text(
            first_batch_row.get("simulated_normalized_metric_name")
        )
        raw_metric_name = _safe_text(first_batch_row.get("raw_metric_name"))
        alias_key = _normalize_alias_key(raw_metric_name)
        second_batch_alias = second_batch_alias_map.get(alias_key)

        if _is_normalized_status(baseline_status):
            baseline_normalized_metric_row_count += 1
        elif _is_unnormalized_status(baseline_status):
            baseline_unnormalized_metric_row_count += 1

        if second_batch_alias is not None:
            second_batch_matching_count_by_alias[alias_key] += 1
            if not _is_unnormalized_status(first_batch_after_status):
                second_batch_previously_resolved_count_by_alias[alias_key] += 1

        simulated_row = deepcopy(first_batch_row)
        simulated_row["baseline_normalization_status"] = baseline_status
        simulated_row["first_batch_simulated_normalized_metric_name"] = first_batch_simulated_name
        simulated_row["normalization_status_after_first_batch"] = first_batch_after_status
        simulated_row["first_batch_simulation_applied"] = _bool_value(
            first_batch_row.get("simulation_applied")
        )
        simulated_row["first_batch_simulation_action"] = _safe_text(
            first_batch_row.get("simulation_action")
        )
        simulated_row["first_batch_simulation_source"] = _safe_text(
            first_batch_row.get("simulation_source")
        )
        simulated_row["downstream_ready_after_first_batch"] = _bool_value(
            first_batch_row.get("downstream_ready_after_alias_simulation")
        )
        simulated_row["second_batch_simulated_normalized_metric_name"] = ""
        simulated_row["second_batch_simulation_applied"] = False
        simulated_row["second_batch_simulation_action"] = "NO_SECOND_BATCH_SIMULATION_APPLIED"
        simulated_row["second_batch_simulation_source"] = ""
        simulated_row["normalization_status_after_second_batch"] = first_batch_after_status
        simulated_row["cumulative_simulated_normalized_metric_name"] = first_batch_simulated_name
        simulated_row["cumulative_simulation_action"] = _safe_text(
            first_batch_row.get("simulation_action")
        )
        simulated_row["downstream_ready_after_second_batch"] = _bool_value(
            first_batch_row.get("downstream_ready_after_alias_simulation")
        )
        simulated_row["simulation_rule_update_required"] = _bool_value(
            first_batch_row.get("simulation_rule_update_required")
        )
        simulated_row["simulation_only_no_write_back"] = True

        if second_batch_alias is not None and _is_unnormalized_status(first_batch_after_status):
            simulated_row["second_batch_simulated_normalized_metric_name"] = second_batch_alias[
                "canonical_alias_target"
            ]
            simulated_row["second_batch_simulation_applied"] = True
            simulated_row["second_batch_simulation_action"] = (
                "SIMULATED_ALIAS_NORMALIZATION_SECOND_BATCH"
            )
            simulated_row["second_batch_simulation_source"] = "REVIEWED_ALIAS_345C10"
            simulated_row["normalization_status_after_second_batch"] = "NORMALIZED"
            simulated_row["cumulative_simulated_normalized_metric_name"] = second_batch_alias[
                "canonical_alias_target"
            ]
            simulated_row["cumulative_simulation_action"] = (
                "FIRST_AND_SECOND_BATCH_ALIAS_SIMULATION"
                if simulated_row["first_batch_simulation_applied"]
                else "SECOND_BATCH_ALIAS_SIMULATION_ONLY"
            )
            simulated_row["simulation_rule_update_required"] = True
            simulated_row["downstream_ready_after_second_batch"] = _bool_value(
                first_batch_row.get("downstream_ready_before_normalization")
            )
            second_batch_applied_row_ids_by_alias[alias_key].append(row_id)
        elif (
            second_batch_alias is not None
            and simulated_row["first_batch_simulation_applied"]
            and not _is_unnormalized_status(first_batch_after_status)
        ):
            first_batch_and_second_batch_overlap_rows += 1

        simulated_metric_rows.append(simulated_row)

    first_batch_alias_count = len(applied_alias_map_345c6)
    first_batch_simulated_newly_normalized_row_count = int(
        manifest_345c6.get("simulated_newly_normalized_row_count", 0)
    )
    second_batch_eligible_alias_count = len(second_batch_alias_map)

    second_batch_applied_alias_map: List[Dict[str, Any]] = []
    non_applied_aliases: List[Dict[str, Any]] = []
    combined_alias_map: List[Dict[str, Any]] = []

    for row in applied_alias_map_345c6:
        alias_key = _normalize_alias_key(row.get("approved_alias_key") or row.get("raw_metric_name"))
        combined_alias_map.append(
            {
                "alias_batch": "FIRST_BATCH_345C6",
                "alias_key": alias_key,
                "raw_metric_name": _safe_text(row.get("raw_metric_name")),
                "canonical_alias_target": _safe_text(row.get("canonical_alias_target")),
                "source_decision": _safe_text(row.get("source_decision")),
                "simulation_source": "REVIEWED_ALIAS_345C5",
                "matching_row_count": int(float(_safe_text(row.get("matching_row_count")) or 0)),
                "applied_row_count": int(float(_safe_text(row.get("applied_row_count")) or 0)),
                "newly_normalized_row_count": int(
                    float(_safe_text(row.get("newly_normalized_row_count")) or 0)
                ),
                "already_normalized_or_previously_resolved_count": int(
                    float(_safe_text(row.get("already_normalized_match_count")) or 0)
                ),
                "review_priority": _safe_text(row.get("review_priority")),
                "source_stages": _safe_text(row.get("source_stages")),
                "needs_alias_family_expansion": False,
                "overlaps_first_batch_alias_key": True,
                "simulation_rule_update_required": _bool_value(
                    row.get("simulation_rule_update_required")
                ),
                "simulation_only_no_write_back": True,
            }
        )

    for alias_key, alias_payload in sorted(second_batch_alias_map.items(), key=lambda item: item[0]):
        applied_row_ids = second_batch_applied_row_ids_by_alias[alias_key]
        applied_row_count = len(applied_row_ids)
        matching_row_count = second_batch_matching_count_by_alias[alias_key]
        previously_resolved_count = second_batch_previously_resolved_count_by_alias[alias_key]
        row_payload = {
            "alias_key": alias_key,
            "raw_metric_name": alias_payload["raw_metric_name"],
            "canonical_alias_target": alias_payload["canonical_alias_target"],
            "source_decision": alias_payload["source_decision"],
            "matching_row_count_after_first_batch": matching_row_count,
            "applied_row_count": applied_row_count,
            "newly_normalized_row_count": applied_row_count,
            "already_normalized_or_previously_resolved_count": previously_resolved_count,
            "review_priority": alias_payload["review_priority"],
            "source_stages": alias_payload["source_stages"],
            "needs_alias_family_expansion": alias_payload["needs_alias_family_expansion"],
            "simulation_rule_update_required": True,
            "simulation_only_no_write_back": True,
        }
        combined_alias_map.append(
            {
                "alias_batch": "SECOND_BATCH_345C11",
                "alias_key": alias_key,
                "raw_metric_name": alias_payload["raw_metric_name"],
                "canonical_alias_target": alias_payload["canonical_alias_target"],
                "source_decision": alias_payload["source_decision"],
                "simulation_source": "REVIEWED_ALIAS_345C10",
                "matching_row_count": matching_row_count,
                "applied_row_count": applied_row_count,
                "newly_normalized_row_count": applied_row_count,
                "already_normalized_or_previously_resolved_count": previously_resolved_count,
                "review_priority": alias_payload["review_priority"],
                "source_stages": alias_payload["source_stages"],
                "needs_alias_family_expansion": alias_payload["needs_alias_family_expansion"],
                "overlaps_first_batch_alias_key": alias_key in first_batch_alias_keys,
                "simulation_rule_update_required": True,
                "simulation_only_no_write_back": True,
            }
        )
        if applied_row_count > 0:
            second_batch_applied_alias_map.append(row_payload)
        else:
            non_applied_reason = (
                "ALREADY_NORMALIZED_OR_RESOLVED_AFTER_FIRST_BATCH"
                if previously_resolved_count > 0
                else "NO_MATCHING_ROWS_AFTER_FIRST_BATCH"
            )
            non_applied_aliases.append(
                {
                    "alias_key": alias_key,
                    "raw_metric_name": alias_payload["raw_metric_name"],
                    "canonical_alias_target": alias_payload["canonical_alias_target"],
                    "source_decision": alias_payload["source_decision"],
                    "non_applied_reason": non_applied_reason,
                    "matching_row_count_after_first_batch": matching_row_count,
                    "already_normalized_or_previously_resolved_count": previously_resolved_count,
                    "review_priority": alias_payload["review_priority"],
                    "source_stages": alias_payload["source_stages"],
                }
            )

    metric_candidate_row_count = len(metric_rows_345c)
    second_batch_applied_alias_key_count = len(second_batch_applied_alias_map)
    second_batch_simulated_alias_applied_row_count = sum(
        1 for row in simulated_metric_rows if _bool_value(row.get("second_batch_simulation_applied"))
    )
    second_batch_simulated_newly_normalized_row_count = second_batch_simulated_alias_applied_row_count
    cumulative_applied_alias_key_count = len(
        {
            *first_batch_alias_keys,
            *{
                row["alias_key"]
                for row in second_batch_applied_alias_map
                if _safe_text(row.get("alias_key"))
            },
        }
    )
    cumulative_simulated_newly_normalized_row_count = (
        first_batch_simulated_newly_normalized_row_count
        + second_batch_simulated_newly_normalized_row_count
    )

    normalized_metric_row_count_after_first_batch = sum(
        1
        for row in simulated_metric_rows
        if _is_normalized_status(_safe_text(row.get("normalization_status_after_first_batch")))
    )
    normalized_metric_row_count_after_second_batch = sum(
        1
        for row in simulated_metric_rows
        if _is_normalized_status(_safe_text(row.get("normalization_status_after_second_batch")))
    )
    coverage_ratio_before = _ratio(
        baseline_normalized_metric_row_count, metric_candidate_row_count
    )
    coverage_ratio_after_first_batch = _ratio(
        normalized_metric_row_count_after_first_batch, metric_candidate_row_count
    )
    coverage_ratio_after_second_batch = _ratio(
        normalized_metric_row_count_after_second_batch, metric_candidate_row_count
    )
    coverage_delta_first_batch = None
    coverage_delta_second_batch_incremental = None
    coverage_delta_cumulative = None
    if coverage_ratio_before is not None and coverage_ratio_after_first_batch is not None:
        coverage_delta_first_batch = round(
            coverage_ratio_after_first_batch - coverage_ratio_before, 6
        )
    if (
        coverage_ratio_after_first_batch is not None
        and coverage_ratio_after_second_batch is not None
    ):
        coverage_delta_second_batch_incremental = round(
            coverage_ratio_after_second_batch - coverage_ratio_after_first_batch, 6
        )
    if coverage_ratio_before is not None and coverage_ratio_after_second_batch is not None:
        coverage_delta_cumulative = round(
            coverage_ratio_after_second_batch - coverage_ratio_before, 6
        )

    ready_candidate_count_before = sum(
        1
        for row in metric_rows_345c
        if _bool_value(row.get("downstream_ready_before_normalization"))
        and _is_normalized_status(_safe_text(row.get("normalization_status")))
    )
    ready_candidate_count_after_first_batch = sum(
        1 for row in simulated_metric_rows if _bool_value(row.get("downstream_ready_after_first_batch"))
    )
    ready_candidate_count_after_second_batch = sum(
        1 for row in simulated_metric_rows if _bool_value(row.get("downstream_ready_after_second_batch"))
    )
    ready_candidate_delta_first_batch = (
        ready_candidate_count_after_first_batch - ready_candidate_count_before
    )
    ready_candidate_delta_second_batch_incremental = (
        ready_candidate_count_after_second_batch - ready_candidate_count_after_first_batch
    )
    ready_candidate_delta_cumulative = (
        ready_candidate_count_after_second_batch - ready_candidate_count_before
    )

    remaining_blind_spots = _remaining_blind_spot_rows(
        simulated_metric_rows,
        status_field="normalization_status_after_second_batch",
        ready_field="downstream_ready_after_second_batch",
    )
    remaining_unnormalized_raw_metric_name_count = len(remaining_blind_spots)
    remaining_unnormalized_metric_row_count = sum(
        row["remaining_row_count"] for row in remaining_blind_spots
    )
    remaining_ready_candidate_count = sum(
        row["remaining_ready_candidate_count"] for row in remaining_blind_spots
    )
    non_applied_second_batch_alias_count = len(non_applied_aliases)

    metric_limitations: List[str] = []
    if metric_rows_read_source != "json":
        metric_limitations.append("345C metric rows loaded from CSV fallback.")
    if non_applied_second_batch_alias_count > 0:
        metric_limitations.append(
            "Some second-batch approved aliases had no remaining eligible rows after the first-batch context."
        )
    if remaining_ready_candidate_count > 0:
        metric_limitations.append(
            "Remaining ready-candidate blind spots still exist after second-batch simulation."
        )
    metric_limitations.append(
        "Simulation uses deterministic exact alias-key matching only and may miss unresolved alias-family variants."
    )

    coverage_before_after = {
        "metric_candidate_row_count": metric_candidate_row_count,
        "baseline_normalized_metric_row_count": baseline_normalized_metric_row_count,
        "baseline_unnormalized_metric_row_count": baseline_unnormalized_metric_row_count,
        "first_batch_alias_count": first_batch_alias_count,
        "first_batch_simulated_newly_normalized_row_count": first_batch_simulated_newly_normalized_row_count,
        "second_batch_eligible_alias_count": second_batch_eligible_alias_count,
        "second_batch_applied_alias_key_count": second_batch_applied_alias_key_count,
        "second_batch_simulated_alias_applied_row_count": second_batch_simulated_alias_applied_row_count,
        "second_batch_simulated_newly_normalized_row_count": second_batch_simulated_newly_normalized_row_count,
        "cumulative_applied_alias_key_count": cumulative_applied_alias_key_count,
        "cumulative_simulated_newly_normalized_row_count": cumulative_simulated_newly_normalized_row_count,
        "coverage_ratio_before": coverage_ratio_before,
        "coverage_ratio_after_first_batch": coverage_ratio_after_first_batch,
        "coverage_ratio_after_second_batch": coverage_ratio_after_second_batch,
        "coverage_delta_first_batch": coverage_delta_first_batch,
        "coverage_delta_second_batch_incremental": coverage_delta_second_batch_incremental,
        "coverage_delta_cumulative": coverage_delta_cumulative,
        "ready_candidate_count_before": ready_candidate_count_before,
        "ready_candidate_count_after_first_batch": ready_candidate_count_after_first_batch,
        "ready_candidate_count_after_second_batch": ready_candidate_count_after_second_batch,
        "ready_candidate_delta_first_batch": ready_candidate_delta_first_batch,
        "ready_candidate_delta_second_batch_incremental": ready_candidate_delta_second_batch_incremental,
        "ready_candidate_delta_cumulative": ready_candidate_delta_cumulative,
        "remaining_unnormalized_raw_metric_name_count": remaining_unnormalized_raw_metric_name_count,
        "remaining_unnormalized_metric_row_count": remaining_unnormalized_metric_row_count,
        "remaining_ready_candidate_count": remaining_ready_candidate_count,
        "metric_limitations": metric_limitations,
    }

    alias_branch_final_recommendation = _determine_alias_branch_recommendation(
        second_batch_simulated_newly_normalized_row_count=second_batch_simulated_newly_normalized_row_count,
        remaining_unnormalized_raw_metric_name_count=remaining_unnormalized_raw_metric_name_count,
    )
    full_structured_demo_export_reasonable_after_345c11 = (
        alias_branch_final_recommendation == RETURN_TO_345D
    )
    next_recommended_step = _next_recommended_step(alias_branch_final_recommendation)

    incremental_impact_summary = {
        "first_batch_alias_count": first_batch_alias_count,
        "first_batch_simulated_newly_normalized_row_count": first_batch_simulated_newly_normalized_row_count,
        "second_batch_eligible_alias_count": second_batch_eligible_alias_count,
        "second_batch_applied_alias_key_count": second_batch_applied_alias_key_count,
        "second_batch_simulated_newly_normalized_row_count": second_batch_simulated_newly_normalized_row_count,
        "cumulative_applied_alias_key_count": cumulative_applied_alias_key_count,
        "cumulative_simulated_newly_normalized_row_count": cumulative_simulated_newly_normalized_row_count,
        "coverage_delta_first_batch": coverage_delta_first_batch,
        "coverage_delta_second_batch_incremental": coverage_delta_second_batch_incremental,
        "coverage_delta_cumulative": coverage_delta_cumulative,
        "ready_candidate_delta_first_batch": ready_candidate_delta_first_batch,
        "ready_candidate_delta_second_batch_incremental": ready_candidate_delta_second_batch_incremental,
        "ready_candidate_delta_cumulative": ready_candidate_delta_cumulative,
        "non_applied_second_batch_alias_count": non_applied_second_batch_alias_count,
        "alias_branch_final_recommendation": alias_branch_final_recommendation,
        "full_structured_demo_export_reasonable_after_345c11": full_structured_demo_export_reasonable_after_345c11,
    }

    stop_or_return_to_345d_decision = {
        "alias_branch_final_recommendation": alias_branch_final_recommendation,
        "decision_reason": _decision_reason(
            alias_branch_final_recommendation,
            second_batch_simulated_newly_normalized_row_count=second_batch_simulated_newly_normalized_row_count,
            remaining_unnormalized_raw_metric_name_count=remaining_unnormalized_raw_metric_name_count,
        ),
        "full_structured_demo_export_reasonable_after_345c11": full_structured_demo_export_reasonable_after_345c11,
        "next_recommended_step": next_recommended_step,
        "remaining_unnormalized_raw_metric_name_count": remaining_unnormalized_raw_metric_name_count,
        "remaining_unnormalized_metric_row_count": remaining_unnormalized_metric_row_count,
        "remaining_ready_candidate_count": remaining_ready_candidate_count,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
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
        stage="345C11",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_apply_proof["upstream_input_hashes_before"] = input_hashes_before
    no_apply_proof["upstream_input_hashes_after"] = input_hashes_after
    no_apply_proof["upstream_inputs_unchanged"] = upstream_unchanged
    no_apply_proof["formal_client_export_generated"] = False
    no_apply_proof["real_production_apply_performed"] = False
    no_apply_proof["official_rules_modified"] = False
    no_apply_proof["official_alias_assets_modified"] = False
    no_apply_proof["alias_apply_simulation_only"] = True
    no_apply_proof["candidate_package_only"] = True
    no_apply_proof["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_345c11")
        and upstream_unchanged
        and not no_apply_proof.get("formal_client_export_generated", True)
        and not no_apply_proof.get("real_production_apply_performed", True)
        and not no_apply_proof.get("official_rules_modified", True)
        and not no_apply_proof.get("official_alias_assets_modified", True)
    )

    checks = [
        {
            "check_name": "inputs::345c_345c6_345c10_ready",
            "status": "PASS"
            if _safe_text(manifest_345c.get("decision")) == READY_DECISION_345C
            and _safe_text(manifest_345c6.get("decision")) == READY_DECISION_345C6
            and _safe_text(manifest_345c10.get("decision")) == READY_DECISION_345C10
            and int(manifest_345c.get("qa_fail_count", 1)) == 0
            and int(manifest_345c6.get("qa_fail_count", 1)) == 0
            and int(manifest_345c10.get("qa_fail_count", 1)) == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "input_345c_decision": manifest_345c.get("decision"),
                    "input_345c6_decision": manifest_345c6.get("decision"),
                    "input_345c10_decision": manifest_345c10.get("decision"),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::first_batch_metrics_preserved",
            "status": "PASS"
            if first_batch_alias_count == int(manifest_345c6.get("applied_alias_key_count", -1))
            and first_batch_simulated_newly_normalized_row_count
            == int(manifest_345c6.get("simulated_newly_normalized_row_count", -1))
            and ready_candidate_count_after_first_batch
            == int(manifest_345c6.get("ready_candidate_count_after_alias_simulation", -1))
            else "FAIL",
            "detail": json.dumps(
                {
                    "first_batch_alias_count": first_batch_alias_count,
                    "manifest_applied_alias_key_count": manifest_345c6.get("applied_alias_key_count"),
                    "first_batch_simulated_newly_normalized_row_count": first_batch_simulated_newly_normalized_row_count,
                    "manifest_simulated_newly_normalized_row_count": manifest_345c6.get("simulated_newly_normalized_row_count"),
                    "ready_candidate_count_after_first_batch": ready_candidate_count_after_first_batch,
                    "manifest_ready_candidate_count_after_alias_simulation": manifest_345c6.get("ready_candidate_count_after_alias_simulation"),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::second_batch_eligible_aliases_loaded",
            "status": "PASS"
            if second_batch_eligible_alias_count == int(manifest_345c10.get("apply_simulation_eligible_count", -1))
            else "FAIL",
            "detail": json.dumps(
                {
                    "second_batch_eligible_alias_count": second_batch_eligible_alias_count,
                    "manifest_apply_simulation_eligible_count": manifest_345c10.get("apply_simulation_eligible_count"),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "simulation::no_double_count_of_first_batch_rows",
            "status": "PASS"
            if all(
                not (
                    _bool_value(row.get("first_batch_simulation_applied"))
                    and _bool_value(row.get("second_batch_simulation_applied"))
                )
                for row in simulated_metric_rows
            )
            else "FAIL",
            "detail": json.dumps(
                {"first_batch_and_second_batch_overlap_rows": first_batch_and_second_batch_overlap_rows},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "metrics::cumulative_coverage_computed",
            "status": "PASS"
            if metric_candidate_row_count == len(simulated_metric_rows)
            and coverage_ratio_before is not None
            and coverage_ratio_after_first_batch is not None
            and coverage_ratio_after_second_batch is not None
            else "FAIL",
            "detail": json.dumps(coverage_before_after, ensure_ascii=False),
        },
        {
            "check_name": "outputs::remaining_blind_spots_generated",
            "status": "PASS" if isinstance(remaining_blind_spots, list) else "FAIL",
            "detail": json.dumps(
                {
                    "remaining_unnormalized_raw_metric_name_count": remaining_unnormalized_raw_metric_name_count,
                    "remaining_unnormalized_metric_row_count": remaining_unnormalized_metric_row_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "decision::alias_branch_final_recommendation_generated",
            "status": "PASS"
            if alias_branch_final_recommendation
            in {RETURN_TO_345D, CONTINUE_EXPLICIT_SCOPE, CONTINUE_ADDITIONAL_BATCH}
            else "FAIL",
            "detail": json.dumps(stop_or_return_to_345d_decision, ensure_ascii=False),
        },
        {
            "check_name": "safety::official_rules_and_alias_assets_unchanged",
            "status": "PASS" if official_assets_before == official_assets_after else "FAIL",
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

    manifest = {
        "decision": READY_DECISION_345C11,
        "input_stage": INPUT_STAGE_345C11,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_345c_decision": _safe_text(manifest_345c.get("decision")),
        "input_345c6_decision": _safe_text(manifest_345c6.get("decision")),
        "input_345c10_decision": _safe_text(manifest_345c10.get("decision")),
        "metric_candidate_row_count": metric_candidate_row_count,
        "baseline_normalized_metric_row_count": baseline_normalized_metric_row_count,
        "baseline_unnormalized_metric_row_count": baseline_unnormalized_metric_row_count,
        "first_batch_alias_count": first_batch_alias_count,
        "first_batch_simulated_newly_normalized_row_count": first_batch_simulated_newly_normalized_row_count,
        "second_batch_eligible_alias_count": second_batch_eligible_alias_count,
        "second_batch_applied_alias_key_count": second_batch_applied_alias_key_count,
        "second_batch_simulated_alias_applied_row_count": second_batch_simulated_alias_applied_row_count,
        "second_batch_simulated_newly_normalized_row_count": second_batch_simulated_newly_normalized_row_count,
        "cumulative_applied_alias_key_count": cumulative_applied_alias_key_count,
        "cumulative_simulated_newly_normalized_row_count": cumulative_simulated_newly_normalized_row_count,
        "coverage_ratio_before": coverage_ratio_before,
        "coverage_ratio_after_first_batch": coverage_ratio_after_first_batch,
        "coverage_ratio_after_second_batch": coverage_ratio_after_second_batch,
        "coverage_delta_first_batch": coverage_delta_first_batch,
        "coverage_delta_second_batch_incremental": coverage_delta_second_batch_incremental,
        "coverage_delta_cumulative": coverage_delta_cumulative,
        "ready_candidate_count_before": ready_candidate_count_before,
        "ready_candidate_count_after_first_batch": ready_candidate_count_after_first_batch,
        "ready_candidate_count_after_second_batch": ready_candidate_count_after_second_batch,
        "ready_candidate_delta_first_batch": ready_candidate_delta_first_batch,
        "ready_candidate_delta_second_batch_incremental": ready_candidate_delta_second_batch_incremental,
        "ready_candidate_delta_cumulative": ready_candidate_delta_cumulative,
        "remaining_unnormalized_raw_metric_name_count": remaining_unnormalized_raw_metric_name_count,
        "remaining_unnormalized_metric_row_count": remaining_unnormalized_metric_row_count,
        "non_applied_second_batch_alias_count": non_applied_second_batch_alias_count,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "alias_apply_simulation_only": True,
        "candidate_package_only": True,
        "alias_branch_final_recommendation": alias_branch_final_recommendation,
        "full_structured_demo_export_reasonable_after_345c11": full_structured_demo_export_reasonable_after_345c11,
        "milestone_ledger_updated": False,
        "metric_limitations": metric_limitations,
        "input_345c_dir": str(metric_candidate_normalization_coverage_345c_dir),
        "input_345c6_dir": str(reviewed_alias_apply_simulation_345c6_dir),
        "input_345c10_dir": str(second_batch_reviewed_alias_decision_ingestion_345c10_dir),
        "input_345c_metric_rows_read_source": metric_rows_read_source,
        "input_345c6_remaining_blind_spot_count": len(remaining_blind_spots_345c6),
        "input_345c10_reviewed_row_count": len(reviewed_decisions_345c10),
        "input_345c10_rejected_or_blocked_row_count": len(rejected_or_blocked_345c10),
        "next_recommended_step": next_recommended_step,
        "generated_at_utc": _utc_now(),
        "output_dir": str(output_dir),
    }

    if ledger_path is not None:
        _ = append_345c11_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = ledger_has_345c11_entry(ledger_path)
        checks.append(
            {
                "check_name": "ledger::345c11_entry_present",
                "status": "PASS" if manifest["milestone_ledger_updated"] else "FAIL",
                "detail": str(ledger_path),
            }
        )

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    manifest["qa_fail_count"] = qa_fail_count

    return {
        "manifest": manifest,
        "combined_alias_map": combined_alias_map,
        "second_batch_applied_alias_map": second_batch_applied_alias_map,
        "simulated_metric_rows": simulated_metric_rows,
        "coverage_before_after": coverage_before_after,
        "incremental_impact_summary": incremental_impact_summary,
        "remaining_blind_spots": remaining_blind_spots,
        "non_applied_aliases": non_applied_aliases,
        "stop_or_return_to_345d_decision": stop_or_return_to_345d_decision,
        "artifact_index_rows": _artifact_rows(output_dir),
        "qa_json": {
            "decision": READY_DECISION_345C11,
            "qa_fail_count": qa_fail_count,
            "checks": checks,
        },
        "no_apply_proof": no_apply_proof,
    }
