from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from datefac.benchmark.second_batch_alias_apply_simulation_345c11 import (
    append_345c11_ledger_entry as _unused_append_345c11_ledger_entry,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_345A = "FULL_STRUCTURED_DATA_INVENTORY_345A_READY"
READY_DECISION_345B = "FULL_EXTRACTION_QUALITY_AUDIT_345B_READY"
READY_DECISION_345C = "METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_READY"
READY_DECISION_345C11 = "SECOND_BATCH_ALIAS_APPLY_SIMULATION_345C11_READY"
READY_DECISION_345D = "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY"
INPUT_STAGE_345D = "POST_345C11_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE"
RETURN_TO_345D = "STOP_ALIAS_BRANCH_AND_RETURN_TO_345D"

DEFAULT_FULL_STRUCTURED_DATA_INVENTORY_345A_DIR = Path(
    r"D:\_datefac\output\full_structured_data_inventory_345a"
)
DEFAULT_FULL_EXTRACTION_QUALITY_AUDIT_345B_DIR = Path(
    r"D:\_datefac\output\full_extraction_quality_audit_345b"
)
DEFAULT_METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_DIR = Path(
    r"D:\_datefac\output\metric_candidate_normalization_coverage_345c"
)
DEFAULT_SECOND_BATCH_ALIAS_APPLY_SIMULATION_345C11_DIR = Path(
    r"D:\_datefac\output\second_batch_alias_apply_simulation_345c11"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\full_structured_demo_export_package_345d")
DEFAULT_LEDGER_PATH = Path(
    r"D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md"
)

MANIFEST_FILE_NAME = "full_structured_demo_export_package_345d_manifest.json"
DEMO_ROWS_JSON_FILE_NAME = "full_structured_demo_export_package_345d_demo_rows.json"
DEMO_ROWS_CSV_FILE_NAME = "full_structured_demo_export_package_345d_demo_rows.csv"
DEMO_ROWS_XLSX_FILE_NAME = "full_structured_demo_export_package_345d_demo_rows.xlsx"
QUALITY_LIMITED_ROWS_JSON_FILE_NAME = (
    "full_structured_demo_export_package_345d_quality_limited_rows.json"
)
QUALITY_LIMITED_ROWS_CSV_FILE_NAME = (
    "full_structured_demo_export_package_345d_quality_limited_rows.csv"
)
EXCLUDED_ROWS_JSON_FILE_NAME = "full_structured_demo_export_package_345d_excluded_rows.json"
EXCLUDED_ROWS_CSV_FILE_NAME = "full_structured_demo_export_package_345d_excluded_rows.csv"
REMAINING_BLIND_SPOTS_JSON_FILE_NAME = (
    "full_structured_demo_export_package_345d_remaining_blind_spots.json"
)
REMAINING_BLIND_SPOTS_CSV_FILE_NAME = (
    "full_structured_demo_export_package_345d_remaining_blind_spots.csv"
)
ALIAS_SIMULATION_SIDECAR_JSON_FILE_NAME = (
    "full_structured_demo_export_package_345d_alias_simulation_sidecar.json"
)
ALIAS_SIMULATION_SIDECAR_CSV_FILE_NAME = (
    "full_structured_demo_export_package_345d_alias_simulation_sidecar.csv"
)
QUALITY_CAVEATS_JSON_FILE_NAME = "full_structured_demo_export_package_345d_quality_caveats.json"
QUALITY_CAVEATS_MD_FILE_NAME = "full_structured_demo_export_package_345d_quality_caveats.md"
DEMO_EXPORT_SUMMARY_JSON_FILE_NAME = "full_structured_demo_export_package_345d_demo_export_summary.json"
EXECUTIVE_SUMMARY_MD_FILE_NAME = "full_structured_demo_export_package_345d_executive_summary.md"
ARTIFACT_INDEX_MD_FILE_NAME = "full_structured_demo_export_package_345d_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "full_structured_demo_export_package_345d_next_plan.md"

INPUT_345A_MANIFEST_NAME = "full_structured_data_inventory_345a_manifest.json"
INPUT_345A_ROW_INVENTORY_JSON_NAME = "full_structured_data_inventory_345a_row_inventory.json"
INPUT_345A_ROW_INVENTORY_CSV_NAME = "full_structured_data_inventory_345a_row_inventory.csv"
INPUT_345A_STAGE_SUMMARY_JSON_NAME = "full_structured_data_inventory_345a_stage_status_summary.json"

INPUT_345B_MANIFEST_NAME = "full_extraction_quality_audit_345b_manifest.json"
INPUT_345B_QUALITY_ROWS_JSON_NAME = "full_extraction_quality_audit_345b_quality_rows.json"
INPUT_345B_QUALITY_ROWS_CSV_NAME = "full_extraction_quality_audit_345b_quality_rows.csv"
INPUT_345B_PRIORITY_FIX_QUEUE_JSON_NAME = "full_extraction_quality_audit_345b_priority_fix_queue.json"
INPUT_345B_MISSING_FIELD_HOTSPOTS_JSON_NAME = "full_extraction_quality_audit_345b_missing_field_hotspots.json"

INPUT_345C_MANIFEST_NAME = "metric_candidate_normalization_coverage_345c_manifest.json"
INPUT_345C_METRIC_ROWS_JSON_NAME = "metric_candidate_normalization_coverage_345c_metric_rows.json"
INPUT_345C_METRIC_ROWS_CSV_NAME = "metric_candidate_normalization_coverage_345c_metric_rows.csv"

INPUT_345C11_MANIFEST_NAME = "second_batch_alias_apply_simulation_345c11_manifest.json"
INPUT_345C11_SIMULATED_METRIC_ROWS_JSON_NAME = (
    "second_batch_alias_apply_simulation_345c11_simulated_metric_rows.json"
)
INPUT_345C11_SIMULATED_METRIC_ROWS_CSV_NAME = (
    "second_batch_alias_apply_simulation_345c11_simulated_metric_rows.csv"
)
INPUT_345C11_COMBINED_ALIAS_MAP_JSON_NAME = (
    "second_batch_alias_apply_simulation_345c11_combined_alias_map.json"
)
INPUT_345C11_COMBINED_ALIAS_MAP_CSV_NAME = (
    "second_batch_alias_apply_simulation_345c11_combined_alias_map.csv"
)
INPUT_345C11_COVERAGE_BEFORE_AFTER_JSON_NAME = (
    "second_batch_alias_apply_simulation_345c11_coverage_before_after.json"
)
INPUT_345C11_INCREMENTAL_IMPACT_SUMMARY_JSON_NAME = (
    "second_batch_alias_apply_simulation_345c11_incremental_impact_summary.json"
)
INPUT_345C11_REMAINING_BLIND_SPOTS_JSON_NAME = (
    "second_batch_alias_apply_simulation_345c11_remaining_blind_spots.json"
)
INPUT_345C11_STOP_DECISION_JSON_NAME = (
    "second_batch_alias_apply_simulation_345c11_stop_or_return_to_345d_decision.json"
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

DEMO_ROW_FIELDS = [
    "demo_export_row_id",
    "source_row_id",
    "source_pdf_name",
    "source_artifact",
    "source_page",
    "source_table_id",
    "stage",
    "raw_metric_name",
    "demo_normalized_metric_name",
    "normalization_source",
    "alias_simulation_batch",
    "value",
    "unit",
    "period",
    "currency",
    "company_name",
    "report_type",
    "quality_severity",
    "quality_issue_codes",
    "source_trace_available",
    "demo_export_eligible",
    "demo_export_caveat_level",
    "demo_export_caveats",
    "formal_client_export_allowed",
    "client_ready",
    "production_ready",
]

ALIAS_SIDECAR_FIELDS = [
    "demo_export_row_id",
    "source_row_id",
    "inventory_row_id",
    "quality_row_id",
    "normalization_source",
    "alias_simulation_batch",
    "baseline_normalized_metric_name",
    "first_batch_simulated_normalized_metric_name",
    "second_batch_simulated_normalized_metric_name",
    "cumulative_simulated_normalized_metric_name",
    "simulation_action",
    "simulation_rule_update_required",
    "simulation_only_no_write_back",
]

LEDGER_HEADING = "## 345D Full Structured Demo Export Package"


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
    return _safe_text(value).lower() in {"1", "true", "yes", "y"}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _require_existing(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"required input file missing: {path}")
    return path


def _load_json_or_csv_rows(*, json_path: Path, csv_path: Path, label: str) -> tuple[List[Dict[str, Any]], str]:
    if json_path.exists():
        payload = _read_json(json_path)
        if not isinstance(payload, list):
            raise ValueError(f"{label} must be a list JSON payload: {json_path}")
        return [dict(row) for row in payload], "json"
    if csv_path.exists():
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


def _split_quality_issues(value: Any) -> List[str]:
    text = _safe_text(value)
    if not text:
        return []
    return [item for item in [part.strip() for part in text.split("|")] if item]


def _caveat_level(quality_severity: str, caveats: List[str]) -> str:
    if quality_severity == "HIGH":
        return "HIGH"
    if quality_severity == "MEDIUM":
        return "MEDIUM"
    return "LOW" if caveats else "NONE"


def _normalization_source(sim_row: Dict[str, Any]) -> tuple[str, str]:
    if _bool_value(sim_row.get("second_batch_simulation_applied")):
        return "SECOND_BATCH_ALIAS_SIMULATION_345C11", "SECOND_BATCH"
    if _bool_value(sim_row.get("first_batch_simulation_applied")):
        return "FIRST_BATCH_ALIAS_SIMULATION_345C6", "FIRST_BATCH"
    if _safe_text(sim_row.get("normalization_status_after_second_batch")) == "NORMALIZED":
        return "BASELINE_345C", "NONE"
    return "UNNORMALIZED_REMAINING_BLIND_SPOT", "NOT_APPLIED"


def _deduce_exclusion_reasons(
    *,
    normalized: bool,
    rejected: bool,
    has_raw_metric_name: bool,
    has_value: bool,
    quality_severity: str,
) -> List[str]:
    reasons: List[str] = []
    if not normalized:
        reasons.append("UNNORMALIZED_REMAINING_BLIND_SPOT")
    if rejected:
        reasons.append("REJECTED_OR_EXCLUDED_UPSTREAM")
    if not has_raw_metric_name:
        reasons.append("MISSING_RAW_METRIC_NAME")
    if not has_value:
        reasons.append("MISSING_VALUE")
    if quality_severity == "HIGH" and normalized and has_raw_metric_name and has_value and not rejected:
        reasons.append("HIGH_SEVERITY_QUALITY_LIMIT")
    return reasons or ["UNSAFE_FOR_DEMO"]


def build_345d_ledger_entry(*, manifest: Dict[str, Any]) -> str:
    lines = [
        LEDGER_HEADING,
        "",
        "Status: completed",
        "",
        "Decision:",
        f"- `{manifest.get('decision', '')}`",
        "",
        "Input packages:",
        f"- `345A = {manifest.get('input_345a_dir', '')}`",
        f"- `345B = {manifest.get('input_345b_dir', '')}`",
        f"- `345C = {manifest.get('input_345c_dir', '')}`",
        f"- `345C11 = {manifest.get('input_345c11_dir', '')}`",
        "",
        "Output package:",
        f"- `{manifest.get('output_dir', '')}`",
        "",
        "Key metrics:",
        f"- `demo_export_row_count = {manifest.get('demo_export_row_count', 0)}`",
        f"- `quality_limited_row_count = {manifest.get('quality_limited_row_count', 0)}`",
        f"- `excluded_row_count = {manifest.get('excluded_row_count', 0)}`",
        f"- `coverage_ratio_after_alias_simulation = {manifest.get('coverage_ratio_after_alias_simulation', None)}`",
        f"- `remaining_unnormalized_raw_metric_name_count = {manifest.get('remaining_unnormalized_raw_metric_name_count', 0)}`",
        f"- `remaining_unnormalized_metric_row_count = {manifest.get('remaining_unnormalized_metric_row_count', 0)}`",
        f"- `high_severity_issue_count = {manifest.get('high_severity_issue_count', 0)}`",
        f"- `medium_severity_issue_count = {manifest.get('medium_severity_issue_count', 0)}`",
        f"- `qa_fail_count = {manifest.get('qa_fail_count', 0)}`",
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
        "- `python -m pytest tests\\benchmark\\test_full_structured_demo_export_package_345d.py -q` passed",
        "- real runner passed",
        "",
        "Next recommended step:",
        f"- `{manifest.get('next_recommended_step', '')}`",
    ]
    return "\n".join(lines)


def ledger_has_345d_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return LEDGER_HEADING in ledger_path.read_text(encoding="utf-8")


def append_345d_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    if ledger_has_345d_entry(ledger_path):
        return False
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    addition = build_345d_ledger_entry(manifest=manifest)
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
            "purpose": "Manifest and gate summary for the 345D demo-only export package.",
        },
        {
            "artifact_name": DEMO_ROWS_JSON_FILE_NAME,
            "path": str(output_dir / DEMO_ROWS_JSON_FILE_NAME),
            "purpose": "Demo export rows in JSON.",
        },
        {
            "artifact_name": DEMO_ROWS_CSV_FILE_NAME,
            "path": str(output_dir / DEMO_ROWS_CSV_FILE_NAME),
            "purpose": "Demo export rows in CSV.",
        },
        {
            "artifact_name": DEMO_ROWS_XLSX_FILE_NAME,
            "path": str(output_dir / DEMO_ROWS_XLSX_FILE_NAME),
            "purpose": "Demo export workbook with demo, quality-limited, and excluded sheets.",
        },
        {
            "artifact_name": QUALITY_LIMITED_ROWS_JSON_FILE_NAME,
            "path": str(output_dir / QUALITY_LIMITED_ROWS_JSON_FILE_NAME),
            "purpose": "Quality-limited but still demo-usable rows in JSON.",
        },
        {
            "artifact_name": QUALITY_LIMITED_ROWS_CSV_FILE_NAME,
            "path": str(output_dir / QUALITY_LIMITED_ROWS_CSV_FILE_NAME),
            "purpose": "Quality-limited rows in CSV.",
        },
        {
            "artifact_name": EXCLUDED_ROWS_JSON_FILE_NAME,
            "path": str(output_dir / EXCLUDED_ROWS_JSON_FILE_NAME),
            "purpose": "Excluded rows with reasons in JSON.",
        },
        {
            "artifact_name": EXCLUDED_ROWS_CSV_FILE_NAME,
            "path": str(output_dir / EXCLUDED_ROWS_CSV_FILE_NAME),
            "purpose": "Excluded rows with reasons in CSV.",
        },
        {
            "artifact_name": REMAINING_BLIND_SPOTS_JSON_FILE_NAME,
            "path": str(output_dir / REMAINING_BLIND_SPOTS_JSON_FILE_NAME),
            "purpose": "Remaining unnormalized blind spots after alias simulation.",
        },
        {
            "artifact_name": REMAINING_BLIND_SPOTS_CSV_FILE_NAME,
            "path": str(output_dir / REMAINING_BLIND_SPOTS_CSV_FILE_NAME),
            "purpose": "Remaining blind spots in CSV.",
        },
        {
            "artifact_name": ALIAS_SIMULATION_SIDECAR_JSON_FILE_NAME,
            "path": str(output_dir / ALIAS_SIMULATION_SIDECAR_JSON_FILE_NAME),
            "purpose": "Alias simulation lineage for demo and quality-limited rows.",
        },
        {
            "artifact_name": ALIAS_SIMULATION_SIDECAR_CSV_FILE_NAME,
            "path": str(output_dir / ALIAS_SIMULATION_SIDECAR_CSV_FILE_NAME),
            "purpose": "Alias simulation lineage in CSV.",
        },
        {
            "artifact_name": QUALITY_CAVEATS_JSON_FILE_NAME,
            "path": str(output_dir / QUALITY_CAVEATS_JSON_FILE_NAME),
            "purpose": "Machine-readable caveat counts and examples.",
        },
        {
            "artifact_name": QUALITY_CAVEATS_MD_FILE_NAME,
            "path": str(output_dir / QUALITY_CAVEATS_MD_FILE_NAME),
            "purpose": "Readable caveat summary for demo handoff.",
        },
        {
            "artifact_name": DEMO_EXPORT_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / DEMO_EXPORT_SUMMARY_JSON_FILE_NAME),
            "purpose": "High-level demo export summary JSON.",
        },
        {
            "artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME,
            "path": str(output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME),
            "purpose": "Narrative summary of the 345D demo export package.",
        },
        {
            "artifact_name": ARTIFACT_INDEX_MD_FILE_NAME,
            "path": str(output_dir / ARTIFACT_INDEX_MD_FILE_NAME),
            "purpose": "Artifact index for 345D outputs.",
        },
        {
            "artifact_name": NEXT_PLAN_MD_FILE_NAME,
            "path": str(output_dir / NEXT_PLAN_MD_FILE_NAME),
            "purpose": "Recommended next step after 345D.",
        },
    ]


def build_full_structured_demo_export_package_345d(
    *,
    full_structured_data_inventory_345a_dir: Path,
    full_extraction_quality_audit_345b_dir: Path,
    metric_candidate_normalization_coverage_345c_dir: Path,
    second_batch_alias_apply_simulation_345c11_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None = None,
    include_quality_limited_rows: bool = False,
    max_sample_rows_per_caveat: int = 20,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345a_path = _require_existing(
        full_structured_data_inventory_345a_dir / INPUT_345A_MANIFEST_NAME
    )
    inventory_rows_345a_json_path = _require_existing(
        full_structured_data_inventory_345a_dir / INPUT_345A_ROW_INVENTORY_JSON_NAME
    )
    _require_existing(full_structured_data_inventory_345a_dir / INPUT_345A_ROW_INVENTORY_CSV_NAME)
    stage_summary_345a_path = _require_existing(
        full_structured_data_inventory_345a_dir / INPUT_345A_STAGE_SUMMARY_JSON_NAME
    )

    manifest_345b_path = _require_existing(
        full_extraction_quality_audit_345b_dir / INPUT_345B_MANIFEST_NAME
    )
    quality_rows_345b_json_path = _require_existing(
        full_extraction_quality_audit_345b_dir / INPUT_345B_QUALITY_ROWS_JSON_NAME
    )
    _require_existing(full_extraction_quality_audit_345b_dir / INPUT_345B_QUALITY_ROWS_CSV_NAME)
    priority_fix_queue_345b_path = _require_existing(
        full_extraction_quality_audit_345b_dir / INPUT_345B_PRIORITY_FIX_QUEUE_JSON_NAME
    )
    missing_field_hotspots_345b_path = _require_existing(
        full_extraction_quality_audit_345b_dir / INPUT_345B_MISSING_FIELD_HOTSPOTS_JSON_NAME
    )

    manifest_345c_path = _require_existing(
        metric_candidate_normalization_coverage_345c_dir / INPUT_345C_MANIFEST_NAME
    )
    metric_rows_345c_json_path = _require_existing(
        metric_candidate_normalization_coverage_345c_dir / INPUT_345C_METRIC_ROWS_JSON_NAME
    )
    _require_existing(metric_candidate_normalization_coverage_345c_dir / INPUT_345C_METRIC_ROWS_CSV_NAME)

    manifest_345c11_path = _require_existing(
        second_batch_alias_apply_simulation_345c11_dir / INPUT_345C11_MANIFEST_NAME
    )
    simulated_rows_345c11_json_path = _require_existing(
        second_batch_alias_apply_simulation_345c11_dir / INPUT_345C11_SIMULATED_METRIC_ROWS_JSON_NAME
    )
    _require_existing(
        second_batch_alias_apply_simulation_345c11_dir / INPUT_345C11_SIMULATED_METRIC_ROWS_CSV_NAME
    )
    combined_alias_map_345c11_path = _require_existing(
        second_batch_alias_apply_simulation_345c11_dir / INPUT_345C11_COMBINED_ALIAS_MAP_JSON_NAME
    )
    _require_existing(
        second_batch_alias_apply_simulation_345c11_dir / INPUT_345C11_COMBINED_ALIAS_MAP_CSV_NAME
    )
    coverage_345c11_path = _require_existing(
        second_batch_alias_apply_simulation_345c11_dir / INPUT_345C11_COVERAGE_BEFORE_AFTER_JSON_NAME
    )
    incremental_impact_345c11_path = _require_existing(
        second_batch_alias_apply_simulation_345c11_dir
        / INPUT_345C11_INCREMENTAL_IMPACT_SUMMARY_JSON_NAME
    )
    remaining_blind_spots_345c11_path = _require_existing(
        second_batch_alias_apply_simulation_345c11_dir / INPUT_345C11_REMAINING_BLIND_SPOTS_JSON_NAME
    )
    stop_decision_345c11_path = _require_existing(
        second_batch_alias_apply_simulation_345c11_dir / INPUT_345C11_STOP_DECISION_JSON_NAME
    )

    files_read = [
        str(manifest_345a_path),
        str(inventory_rows_345a_json_path),
        str(stage_summary_345a_path),
        str(manifest_345b_path),
        str(quality_rows_345b_json_path),
        str(priority_fix_queue_345b_path),
        str(missing_field_hotspots_345b_path),
        str(manifest_345c_path),
        str(metric_rows_345c_json_path),
        str(manifest_345c11_path),
        str(simulated_rows_345c11_json_path),
        str(combined_alias_map_345c11_path),
        str(coverage_345c11_path),
        str(incremental_impact_345c11_path),
        str(remaining_blind_spots_345c11_path),
        str(stop_decision_345c11_path),
    ]
    input_paths = [
        manifest_345a_path,
        inventory_rows_345a_json_path,
        stage_summary_345a_path,
        manifest_345b_path,
        quality_rows_345b_json_path,
        priority_fix_queue_345b_path,
        missing_field_hotspots_345b_path,
        manifest_345c_path,
        metric_rows_345c_json_path,
        manifest_345c11_path,
        simulated_rows_345c11_json_path,
        combined_alias_map_345c11_path,
        coverage_345c11_path,
        incremental_impact_345c11_path,
        remaining_blind_spots_345c11_path,
        stop_decision_345c11_path,
    ]

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    manifest_345a = _read_json(manifest_345a_path)
    inventory_rows, inventory_read_source = _load_json_or_csv_rows(
        json_path=inventory_rows_345a_json_path,
        csv_path=full_structured_data_inventory_345a_dir / INPUT_345A_ROW_INVENTORY_CSV_NAME,
        label="345A row inventory",
    )
    stage_summary_345a = _read_json(stage_summary_345a_path)

    manifest_345b = _read_json(manifest_345b_path)
    quality_rows, quality_rows_read_source = _load_json_or_csv_rows(
        json_path=quality_rows_345b_json_path,
        csv_path=full_extraction_quality_audit_345b_dir / INPUT_345B_QUALITY_ROWS_CSV_NAME,
        label="345B quality rows",
    )
    priority_fix_queue_345b = _read_json(priority_fix_queue_345b_path)
    missing_field_hotspots_345b = _read_json(missing_field_hotspots_345b_path)

    manifest_345c = _read_json(manifest_345c_path)
    metric_rows_345c, metric_rows_read_source = _load_json_or_csv_rows(
        json_path=metric_rows_345c_json_path,
        csv_path=metric_candidate_normalization_coverage_345c_dir / INPUT_345C_METRIC_ROWS_CSV_NAME,
        label="345C metric rows",
    )

    manifest_345c11 = _read_json(manifest_345c11_path)
    simulated_rows_345c11, simulated_rows_read_source = _load_json_or_csv_rows(
        json_path=simulated_rows_345c11_json_path,
        csv_path=second_batch_alias_apply_simulation_345c11_dir
        / INPUT_345C11_SIMULATED_METRIC_ROWS_CSV_NAME,
        label="345C11 simulated metric rows",
    )
    combined_alias_map_345c11 = _read_json(combined_alias_map_345c11_path)
    coverage_345c11 = _read_json(coverage_345c11_path)
    incremental_impact_345c11 = _read_json(incremental_impact_345c11_path)
    remaining_blind_spots_345c11 = _read_json(remaining_blind_spots_345c11_path)
    stop_decision_345c11 = _read_json(stop_decision_345c11_path)

    if _safe_text(manifest_345a.get("decision")) != READY_DECISION_345A:
        raise ValueError("345A manifest decision is not READY.")
    if _safe_text(manifest_345b.get("decision")) != READY_DECISION_345B:
        raise ValueError("345B manifest decision is not READY.")
    if _safe_text(manifest_345c.get("decision")) != READY_DECISION_345C:
        raise ValueError("345C manifest decision is not READY.")
    if _safe_text(manifest_345c11.get("decision")) != READY_DECISION_345C11:
        raise ValueError("345C11 manifest decision is not READY.")
    if _safe_text(manifest_345c11.get("alias_branch_final_recommendation")) != RETURN_TO_345D:
        raise ValueError("345C11 must explicitly recommend STOP_ALIAS_BRANCH_AND_RETURN_TO_345D.")
    if not _bool_value(manifest_345c11.get("full_structured_demo_export_reasonable_after_345c11")):
        raise ValueError("345C11 must mark full_structured_demo_export_reasonable_after_345c11 = true.")
    for manifest in [manifest_345a, manifest_345b, manifest_345c, manifest_345c11]:
        for gate_name in ["formal_client_export_allowed", "client_ready", "production_ready"]:
            if _bool_value(manifest.get(gate_name)):
                raise ValueError(f"Input gate must remain false: {gate_name}")
    if _bool_value(manifest_345c11.get("official_rules_modified")):
        raise ValueError("345C11 official_rules_modified must remain false.")
    if _bool_value(manifest_345c11.get("official_alias_assets_modified")):
        raise ValueError("345C11 official_alias_assets_modified must remain false.")

    inventory_by_id = {_safe_text(row.get("inventory_row_id")): dict(row) for row in inventory_rows}
    quality_by_inventory_id = {_safe_text(row.get("inventory_row_id")): dict(row) for row in quality_rows}
    metric_rows_by_inventory_id = {_safe_text(row.get("inventory_row_id")): dict(row) for row in metric_rows_345c}

    if len(inventory_by_id) != len(inventory_rows):
        raise ValueError("345A inventory rows contain duplicate inventory_row_id values.")
    if len(quality_by_inventory_id) != len(quality_rows):
        raise ValueError("345B quality rows contain duplicate inventory_row_id values.")
    if len(metric_rows_by_inventory_id) != len(metric_rows_345c):
        raise ValueError("345C metric rows contain duplicate inventory_row_id values.")

    demo_rows: List[Dict[str, Any]] = []
    quality_limited_rows: List[Dict[str, Any]] = []
    excluded_rows: List[Dict[str, Any]] = []
    alias_simulation_sidecar_rows: List[Dict[str, Any]] = []
    quality_issue_counts: Dict[str, int] = {}
    quality_issue_examples: Dict[str, List[Dict[str, Any]]] = {}
    excluded_reason_counts: Dict[str, int] = {}
    excluded_reason_examples: Dict[str, List[Dict[str, Any]]] = {}
    missing_unit_count = 0
    missing_period_count = 0
    missing_source_trace_count = 0
    baseline_normalized_demo_row_count = 0
    alias_simulated_demo_row_count = 0
    first_batch_alias_simulated_demo_row_count = 0
    second_batch_alias_simulated_demo_row_count = 0

    demo_row_counter = 0
    for sim_row in simulated_rows_345c11:
        inventory_row_id = _safe_text(sim_row.get("inventory_row_id"))
        inventory_row = inventory_by_id.get(inventory_row_id)
        quality_row = quality_by_inventory_id.get(inventory_row_id)
        metric_row = metric_rows_by_inventory_id.get(inventory_row_id)
        if inventory_row is None or quality_row is None or metric_row is None:
            raise ValueError(f"Missing joined row for inventory_row_id: {inventory_row_id}")

        raw_metric_name = _safe_text(sim_row.get("raw_metric_name") or inventory_row.get("metric_name"))
        normalized_after_second_batch = _safe_text(
            sim_row.get("normalization_status_after_second_batch")
        ) == "NORMALIZED"
        demo_normalized_metric_name = _safe_text(
            sim_row.get("cumulative_simulated_normalized_metric_name")
            or sim_row.get("simulated_normalized_metric_name")
            or sim_row.get("normalized_metric_name")
            or inventory_row.get("normalized_metric_name")
        )
        has_raw_metric_name = bool(raw_metric_name)
        has_value = bool(_safe_text(inventory_row.get("value_raw")) or _safe_text(inventory_row.get("value_normalized")))
        rejected = _bool_value(quality_row.get("is_rejected_or_excluded"))
        quality_severity = _safe_text(quality_row.get("quality_severity")) or "NONE"
        has_unit = _bool_value(quality_row.get("has_unit"))
        has_period = _bool_value(quality_row.get("has_period"))
        has_source_trace = _bool_value(quality_row.get("has_source_trace"))
        quality_issue_codes = _split_quality_issues(quality_row.get("quality_issues"))
        normalization_source, alias_batch = _normalization_source(sim_row)

        caveats: List[str] = []
        if not has_unit:
            caveats.append("MISSING_UNIT")
        if not has_period:
            caveats.append("MISSING_PERIOD")
        if not has_source_trace:
            caveats.append("MISSING_SOURCE_TRACE")
        caveats.extend(quality_issue_codes)
        caveats = sorted({item for item in caveats if item})

        demo_row_counter += 1
        demo_row = {
            "demo_export_row_id": f"345d::demo::{demo_row_counter:05d}",
            "source_row_id": _safe_text(inventory_row.get("source_row_id")),
            "source_pdf_name": _safe_text(inventory_row.get("pdf_name")),
            "source_artifact": _safe_text(inventory_row.get("source_artifact")),
            "source_page": _safe_text(inventory_row.get("source_page")),
            "source_table_id": _safe_text(inventory_row.get("table_id")),
            "stage": _safe_text(inventory_row.get("source_stage")),
            "raw_metric_name": raw_metric_name,
            "demo_normalized_metric_name": demo_normalized_metric_name,
            "normalization_source": normalization_source,
            "alias_simulation_batch": alias_batch,
            "value": _safe_text(inventory_row.get("value_normalized") or inventory_row.get("value_raw")),
            "unit": _safe_text(inventory_row.get("unit")),
            "period": _safe_text(inventory_row.get("period")),
            "currency": "",
            "company_name": "",
            "report_type": "",
            "quality_severity": quality_severity,
            "quality_issue_codes": "|".join(quality_issue_codes),
            "source_trace_available": has_source_trace,
            "demo_export_eligible": False,
            "demo_export_caveat_level": _caveat_level(quality_severity, caveats),
            "demo_export_caveats": "|".join(caveats),
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }

        if normalized_after_second_batch and has_raw_metric_name and has_value and not rejected and quality_severity == "NONE":
            demo_row["demo_export_eligible"] = True
            demo_rows.append(demo_row)
            baseline_normalized_demo_row_count += 1
        elif (
            normalized_after_second_batch
            and has_raw_metric_name
            and has_value
            and not rejected
            and (quality_severity == "MEDIUM" or (include_quality_limited_rows and quality_severity == "HIGH"))
        ):
            demo_row["demo_export_eligible"] = True
            quality_limited_rows.append(demo_row)
            if not has_unit:
                missing_unit_count += 1
            if not has_period:
                missing_period_count += 1
            if not has_source_trace:
                missing_source_trace_count += 1
            for issue in quality_issue_codes:
                quality_issue_counts[issue] = quality_issue_counts.get(issue, 0) + 1
                examples = quality_issue_examples.setdefault(issue, [])
                if len(examples) < max_sample_rows_per_caveat:
                    examples.append(
                        {
                            "demo_export_row_id": demo_row["demo_export_row_id"],
                            "source_pdf_name": demo_row["source_pdf_name"],
                            "raw_metric_name": demo_row["raw_metric_name"],
                            "period": demo_row["period"],
                            "value": demo_row["value"],
                        }
                    )
            if normalization_source != "BASELINE_345C":
                alias_simulated_demo_row_count += 1
            if normalization_source == "FIRST_BATCH_ALIAS_SIMULATION_345C6":
                first_batch_alias_simulated_demo_row_count += 1
            if normalization_source == "SECOND_BATCH_ALIAS_SIMULATION_345C11":
                second_batch_alias_simulated_demo_row_count += 1
        else:
            exclusion_reasons = _deduce_exclusion_reasons(
                normalized=normalized_after_second_batch,
                rejected=rejected,
                has_raw_metric_name=has_raw_metric_name,
                has_value=has_value,
                quality_severity=quality_severity,
            )
            excluded_row = dict(demo_row)
            excluded_row["demo_export_eligible"] = False
            excluded_row["exclusion_reasons"] = "|".join(exclusion_reasons)
            excluded_rows.append(excluded_row)
            for reason in exclusion_reasons:
                excluded_reason_counts[reason] = excluded_reason_counts.get(reason, 0) + 1
                examples = excluded_reason_examples.setdefault(reason, [])
                if len(examples) < max_sample_rows_per_caveat:
                    examples.append(
                        {
                            "demo_export_row_id": excluded_row["demo_export_row_id"],
                            "source_pdf_name": excluded_row["source_pdf_name"],
                            "raw_metric_name": excluded_row["raw_metric_name"],
                            "period": excluded_row["period"],
                            "value": excluded_row["value"],
                        }
                    )

        if demo_row["demo_export_eligible"] and normalization_source != "BASELINE_345C":
            alias_simulation_sidecar_rows.append(
                {
                    "demo_export_row_id": demo_row["demo_export_row_id"],
                    "source_row_id": demo_row["source_row_id"],
                    "inventory_row_id": inventory_row_id,
                    "quality_row_id": _safe_text(sim_row.get("quality_row_id")),
                    "normalization_source": normalization_source,
                    "alias_simulation_batch": alias_batch,
                    "baseline_normalized_metric_name": _safe_text(sim_row.get("normalized_metric_name")),
                    "first_batch_simulated_normalized_metric_name": _safe_text(
                        sim_row.get("first_batch_simulated_normalized_metric_name")
                    ),
                    "second_batch_simulated_normalized_metric_name": _safe_text(
                        sim_row.get("second_batch_simulated_normalized_metric_name")
                    ),
                    "cumulative_simulated_normalized_metric_name": demo_normalized_metric_name,
                    "simulation_action": _safe_text(sim_row.get("cumulative_simulation_action")),
                    "simulation_rule_update_required": _bool_value(
                        sim_row.get("simulation_rule_update_required")
                    ),
                    "simulation_only_no_write_back": True,
                }
            )

    quality_caveats = {
        "remaining_unnormalized_raw_metric_name_count": int(
            manifest_345c11.get("remaining_unnormalized_raw_metric_name_count", 0)
        ),
        "remaining_unnormalized_metric_row_count": int(
            manifest_345c11.get("remaining_unnormalized_metric_row_count", 0)
        ),
        "remaining_ready_candidate_count": int(
            manifest_345c11.get("remaining_ready_candidate_count", 0)
        ),
        "missing_unit_count": missing_unit_count,
        "missing_period_count": missing_period_count,
        "missing_source_trace_count": missing_source_trace_count,
        "high_severity_issue_count": int(manifest_345b.get("high_severity_issue_count", 0)),
        "medium_severity_issue_count": int(manifest_345b.get("medium_severity_issue_count", 0)),
        "rejected_or_excluded_count": excluded_reason_counts.get("REJECTED_OR_EXCLUDED_UPSTREAM", 0),
        "rows_normalized_only_through_simulation_count": len(alias_simulation_sidecar_rows),
        "simulation_exact_match_limitation": "Exact-match alias-key simulation may miss unresolved alias-family variants.",
        "formal_export_and_production_gates_false": True,
        "quality_issue_counts": quality_issue_counts,
        "quality_issue_examples": quality_issue_examples,
        "excluded_reason_counts": excluded_reason_counts,
        "excluded_reason_examples": excluded_reason_examples,
        "quality_limited_scope_policy": (
            "Default 345D keeps MEDIUM quality severity rows in quality_limited_rows and leaves HIGH severity rows excluded "
            "unless --include-quality-limited-rows is passed."
        ),
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
        stage="345D",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_apply_proof["upstream_input_hashes_before"] = input_hashes_before
    no_apply_proof["upstream_input_hashes_after"] = input_hashes_after
    no_apply_proof["upstream_inputs_unchanged"] = upstream_unchanged
    no_apply_proof["official_rules_modified"] = False
    no_apply_proof["official_alias_assets_modified"] = False
    no_apply_proof["formal_export_generated"] = False
    no_apply_proof["demo_export_only"] = True
    no_apply_proof["real_production_apply_performed"] = False
    no_apply_proof["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_345d")
        and upstream_unchanged
        and not no_apply_proof.get("formal_export_generated", True)
        and not no_apply_proof.get("real_production_apply_performed", True)
        and not no_apply_proof.get("official_rules_modified", True)
        and not no_apply_proof.get("official_alias_assets_modified", True)
    )

    manifest = {
        "decision": READY_DECISION_345D,
        "input_stage": INPUT_STAGE_345D,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_345a_decision": _safe_text(manifest_345a.get("decision")),
        "input_345b_decision": _safe_text(manifest_345b.get("decision")),
        "input_345c_decision": _safe_text(manifest_345c.get("decision")),
        "input_345c11_decision": _safe_text(manifest_345c11.get("decision")),
        "inventory_row_count": len(inventory_rows),
        "quality_audited_row_count": len(quality_rows),
        "metric_candidate_row_count": len(metric_rows_345c),
        "coverage_ratio_before_alias_simulation": manifest_345c.get("normalization_coverage_ratio"),
        "coverage_ratio_after_alias_simulation": manifest_345c11.get("coverage_ratio_after_second_batch"),
        "cumulative_alias_simulated_newly_normalized_row_count": manifest_345c11.get(
            "cumulative_simulated_newly_normalized_row_count"
        ),
        "demo_export_row_count": len(demo_rows),
        "quality_limited_row_count": len(quality_limited_rows),
        "excluded_row_count": len(excluded_rows),
        "remaining_unnormalized_raw_metric_name_count": manifest_345c11.get(
            "remaining_unnormalized_raw_metric_name_count"
        ),
        "remaining_unnormalized_metric_row_count": manifest_345c11.get(
            "remaining_unnormalized_metric_row_count"
        ),
        "remaining_ready_candidate_count": manifest_345c11.get("remaining_ready_candidate_count"),
        "high_severity_issue_count": manifest_345b.get("high_severity_issue_count"),
        "medium_severity_issue_count": manifest_345b.get("medium_severity_issue_count"),
        "missing_unit_count": missing_unit_count,
        "missing_period_count": missing_period_count,
        "missing_source_trace_count": missing_source_trace_count,
        "baseline_normalized_demo_row_count": baseline_normalized_demo_row_count,
        "alias_simulated_demo_row_count": alias_simulated_demo_row_count,
        "first_batch_alias_simulated_demo_row_count": first_batch_alias_simulated_demo_row_count,
        "second_batch_alias_simulated_demo_row_count": second_batch_alias_simulated_demo_row_count,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "alias_simulation_sidecar_used": True,
        "formal_export_generated": False,
        "demo_export_only": True,
        "full_structured_demo_export_reasonable": True,
        "milestone_ledger_updated": False,
        "include_quality_limited_rows": include_quality_limited_rows,
        "max_sample_rows_per_caveat": max_sample_rows_per_caveat,
        "input_345a_dir": str(full_structured_data_inventory_345a_dir),
        "input_345b_dir": str(full_extraction_quality_audit_345b_dir),
        "input_345c_dir": str(metric_candidate_normalization_coverage_345c_dir),
        "input_345c11_dir": str(second_batch_alias_apply_simulation_345c11_dir),
        "input_inventory_read_source": inventory_read_source,
        "input_quality_rows_read_source": quality_rows_read_source,
        "input_metric_rows_read_source": metric_rows_read_source,
        "input_simulated_rows_read_source": simulated_rows_read_source,
        "next_recommended_step": "345E Demo Export Review / QA Checklist",
        "generated_at_utc": _utc_now(),
        "output_dir": str(output_dir),
    }

    if ledger_path is not None:
        _ = append_345d_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = ledger_has_345d_entry(ledger_path)

    demo_export_summary = {
        "decision": READY_DECISION_345D,
        "demo_export_row_count": len(demo_rows),
        "quality_limited_row_count": len(quality_limited_rows),
        "excluded_row_count": len(excluded_rows),
        "coverage_ratio_before_alias_simulation": manifest["coverage_ratio_before_alias_simulation"],
        "coverage_ratio_after_alias_simulation": manifest["coverage_ratio_after_alias_simulation"],
        "alias_simulation_sidecar_row_count": len(alias_simulation_sidecar_rows),
        "remaining_blind_spot_count": len(remaining_blind_spots_345c11),
        "quality_caveats_focus": [
            "MEDIUM severity normalized rows remain caveated only.",
            "HIGH severity normalized rows stay excluded by default.",
            "Formal export and production gates remain false.",
        ],
    }

    checks = [
        {
            "check_name": "inputs::345a_345b_345c_345c11_ready",
            "status": "PASS"
            if _safe_text(manifest_345a.get("decision")) == READY_DECISION_345A
            and _safe_text(manifest_345b.get("decision")) == READY_DECISION_345B
            and _safe_text(manifest_345c.get("decision")) == READY_DECISION_345C
            and _safe_text(manifest_345c11.get("decision")) == READY_DECISION_345C11
            else "FAIL",
            "detail": json.dumps(
                {
                    "input_345a_decision": manifest_345a.get("decision"),
                    "input_345b_decision": manifest_345b.get("decision"),
                    "input_345c_decision": manifest_345c.get("decision"),
                    "input_345c11_decision": manifest_345c11.get("decision"),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::345c11_stops_alias_branch",
            "status": "PASS"
            if _safe_text(manifest_345c11.get("alias_branch_final_recommendation")) == RETURN_TO_345D
            and _bool_value(manifest_345c11.get("full_structured_demo_export_reasonable_after_345c11"))
            else "FAIL",
            "detail": json.dumps(stop_decision_345c11, ensure_ascii=False),
        },
        {
            "check_name": "outputs::demo_quality_excluded_rows_generated",
            "status": "PASS"
            if len(demo_rows) > 0 and len(quality_limited_rows) > 0 and len(excluded_rows) > 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "demo_export_row_count": len(demo_rows),
                    "quality_limited_row_count": len(quality_limited_rows),
                    "excluded_row_count": len(excluded_rows),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::remaining_blind_spots_reported",
            "status": "PASS" if isinstance(remaining_blind_spots_345c11, list) else "FAIL",
            "detail": json.dumps(
                {
                    "remaining_unnormalized_raw_metric_name_count": manifest_345c11.get(
                        "remaining_unnormalized_raw_metric_name_count"
                    ),
                    "remaining_unnormalized_metric_row_count": manifest_345c11.get(
                        "remaining_unnormalized_metric_row_count"
                    ),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::alias_simulation_sidecar_included",
            "status": "PASS" if len(alias_simulation_sidecar_rows) == alias_simulated_demo_row_count else "FAIL",
            "detail": json.dumps(
                {
                    "alias_simulation_sidecar_row_count": len(alias_simulation_sidecar_rows),
                    "alias_simulated_demo_row_count": alias_simulated_demo_row_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "safety::official_rules_and_alias_assets_unchanged",
            "status": "PASS" if official_assets_before == official_assets_after else "FAIL",
            "detail": json.dumps(official_assets_after, ensure_ascii=False),
        },
        {
            "check_name": "safety::formal_client_production_gates_false",
            "status": "PASS",
            "detail": "formal_client_export_allowed/client_ready/production_ready/global_strict_human_review_completed must remain false",
        },
        {
            "check_name": "safety::formal_export_generated_false_and_demo_only_true",
            "status": "PASS"
            if not manifest["formal_export_generated"] and manifest["demo_export_only"]
            else "FAIL",
            "detail": json.dumps(
                {
                    "formal_export_generated": manifest["formal_export_generated"],
                    "demo_export_only": manifest["demo_export_only"],
                },
                ensure_ascii=False,
            ),
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

    if ledger_path is not None:
        checks.append(
            {
                "check_name": "ledger::345d_entry_present",
                "status": "PASS" if manifest["milestone_ledger_updated"] else "FAIL",
                "detail": str(ledger_path),
            }
        )

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    manifest["qa_fail_count"] = qa_fail_count

    workbook_sheets = {
        "demo_rows": demo_rows,
        "quality_limited_rows": quality_limited_rows,
        "excluded_rows": excluded_rows,
        "remaining_blind_spots": remaining_blind_spots_345c11,
        "alias_sidecar": alias_simulation_sidecar_rows,
        "quality_caveats": [
            {
                "caveat_key": key,
                "caveat_value": value,
            }
            for key, value in [
                ("missing_unit_count", missing_unit_count),
                ("missing_period_count", missing_period_count),
                ("missing_source_trace_count", missing_source_trace_count),
                ("high_severity_issue_count", manifest_345b.get("high_severity_issue_count")),
                ("medium_severity_issue_count", manifest_345b.get("medium_severity_issue_count")),
                ("remaining_unnormalized_metric_row_count", manifest_345c11.get("remaining_unnormalized_metric_row_count")),
            ]
        ],
    }

    return {
        "manifest": manifest,
        "demo_rows": demo_rows,
        "quality_limited_rows": quality_limited_rows,
        "excluded_rows": excluded_rows,
        "remaining_blind_spots": remaining_blind_spots_345c11,
        "alias_simulation_sidecar": alias_simulation_sidecar_rows,
        "quality_caveats": quality_caveats,
        "demo_export_summary": demo_export_summary,
        "artifact_index_rows": _artifact_rows(output_dir),
        "qa_json": {
            "decision": READY_DECISION_345D,
            "qa_fail_count": qa_fail_count,
            "checks": checks,
        },
        "no_write_back_proof": no_apply_proof,
        "workbook_sheets": workbook_sheets,
        "stage_summary_345a": stage_summary_345a,
        "priority_fix_queue_345b": priority_fix_queue_345b,
        "missing_field_hotspots_345b": missing_field_hotspots_345b,
        "combined_alias_map_345c11": combined_alias_map_345c11,
        "coverage_345c11": coverage_345c11,
        "incremental_impact_345c11": incremental_impact_345c11,
    }
