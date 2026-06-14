from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.reviewed_alias_apply_simulation_345c6 import (  # noqa: E402
    READY_DECISION_345C6,
    build_reviewed_alias_apply_simulation_345c6,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_reviewed_alias_apply_simulation_345c6"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345c_outputs(root: Path) -> Path:
    dir_345c = root / "output" / "metric_candidate_normalization_coverage_345c"
    dir_345c.mkdir(parents=True, exist_ok=True)
    metric_rows = [
        {
            "metric_coverage_row_id": "345c::metric::00001",
            "inventory_row_id": "inv::001",
            "quality_row_id": "qual::001",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "345a",
            "pdf_id": "pdf_001",
            "pdf_name": "demo_a.pdf",
            "raw_metric_name": "Alias A",
            "normalized_metric_name": "",
            "quality_severity": "LOW",
            "quality_issues": "",
            "downstream_ready_before_normalization": True,
            "normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
        },
        {
            "metric_coverage_row_id": "345c::metric::00002",
            "inventory_row_id": "inv::002",
            "quality_row_id": "qual::002",
            "source_stage": "REVIEW_REQUIRED",
            "source_artifact": "345a",
            "pdf_id": "pdf_001",
            "pdf_name": "demo_a.pdf",
            "raw_metric_name": "Alias A",
            "normalized_metric_name": "",
            "quality_severity": "MEDIUM",
            "quality_issues": "needs review",
            "downstream_ready_before_normalization": False,
            "normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
        },
        {
            "metric_coverage_row_id": "345c::metric::00003",
            "inventory_row_id": "inv::003",
            "quality_row_id": "qual::003",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "345a",
            "pdf_id": "pdf_002",
            "pdf_name": "demo_b.pdf",
            "raw_metric_name": "Alias B",
            "normalized_metric_name": "",
            "quality_severity": "LOW",
            "quality_issues": "",
            "downstream_ready_before_normalization": True,
            "normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
        },
        {
            "metric_coverage_row_id": "345c::metric::00004",
            "inventory_row_id": "inv::004",
            "quality_row_id": "qual::004",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "345a",
            "pdf_id": "pdf_003",
            "pdf_name": "demo_c.pdf",
            "raw_metric_name": "Existing Metric",
            "normalized_metric_name": "revenue",
            "quality_severity": "LOW",
            "quality_issues": "",
            "downstream_ready_before_normalization": True,
            "normalization_status": "NORMALIZED",
        },
        {
            "metric_coverage_row_id": "345c::metric::00005",
            "inventory_row_id": "inv::005",
            "quality_row_id": "qual::005",
            "source_stage": "REVIEW_REQUIRED",
            "source_artifact": "345a",
            "pdf_id": "pdf_004",
            "pdf_name": "demo_d.pdf",
            "raw_metric_name": "Alias C",
            "normalized_metric_name": "",
            "quality_severity": "HIGH",
            "quality_issues": "pending",
            "downstream_ready_before_normalization": True,
            "normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
        },
    ]
    manifest = {
        "decision": "METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "metric_candidate_row_count": 5,
    }
    raw_metric_summary = [
        {"raw_metric_name": "Alias A", "row_count": 2},
        {"raw_metric_name": "Alias B", "row_count": 1},
        {"raw_metric_name": "Alias C", "row_count": 1},
    ]
    alias_queue = [
        {"raw_metric_name": "Alias A", "frequency": 2},
        {"raw_metric_name": "Alias B", "frequency": 1},
        {"raw_metric_name": "Alias C", "frequency": 1},
    ]
    _write_json(dir_345c / "metric_candidate_normalization_coverage_345c_manifest.json", manifest)
    _write_json(dir_345c / "metric_candidate_normalization_coverage_345c_metric_rows.json", metric_rows)
    _write_json(
        dir_345c / "metric_candidate_normalization_coverage_345c_raw_metric_summary.json",
        raw_metric_summary,
    )
    _write_json(
        dir_345c / "metric_candidate_normalization_coverage_345c_alias_candidate_queue.json",
        alias_queue,
    )
    (dir_345c / "metric_candidate_normalization_coverage_345c_metric_rows.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c / "metric_candidate_normalization_coverage_345c_raw_metric_summary.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c / "metric_candidate_normalization_coverage_345c_alias_candidate_queue.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    return dir_345c


def _seed_345c5_outputs(root: Path) -> Path:
    dir_345c5 = root / "output" / "reviewed_alias_decision_ingestion_345c5"
    dir_345c5.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "REVIEWED_ALIAS_DECISION_INGESTION_345C5_READY",
        "qa_fail_count": 0,
        "apply_simulation_eligible_count": 2,
        "alias_rule_update_allowed_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
    }
    validated_approved_aliases = [
        {
            "raw_metric_name": "Alias A",
            "canonical_alias_target": "metric_a",
            "human_alias_review_decision": "APPROVE_NEW_STANDARD",
            "decision_validation_status": "VALID",
            "apply_simulation_eligible": True,
            "review_priority": "HIGH",
            "source_stages": "LONG_FORM_CELL|REVIEW_REQUIRED",
        },
        {
            "raw_metric_name": "Alias B",
            "canonical_alias_target": "metric_b",
            "human_alias_review_decision": "APPROVE_EXISTING_MAPPING",
            "decision_validation_status": "VALID",
            "apply_simulation_eligible": True,
            "review_priority": "MEDIUM",
            "source_stages": "LONG_FORM_CELL",
        },
    ]
    rejected_or_deferred = [
        {
            "raw_metric_name": "Alias Z",
            "human_alias_review_decision": "REJECT_ALIAS",
        }
    ]
    _write_json(dir_345c5 / "reviewed_alias_decision_ingestion_345c5_manifest.json", manifest)
    _write_json(
        dir_345c5 / "reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.json",
        validated_approved_aliases,
    )
    _write_json(
        dir_345c5 / "reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.json",
        rejected_or_deferred,
    )
    _write_json(
        dir_345c5 / "reviewed_alias_decision_ingestion_345c5_validation_issues.json",
        [],
    )
    (dir_345c5 / "reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c5 / "reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    return dir_345c5


def test_345c6_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_345c = _seed_345c_outputs(case_root)
        dir_345c5 = _seed_345c5_outputs(case_root)
        artifacts = build_reviewed_alias_apply_simulation_345c6(
            metric_candidate_normalization_coverage_345c_dir=dir_345c,
            reviewed_alias_decision_ingestion_345c5_dir=dir_345c5,
            output_dir=case_root / "output" / "reviewed_alias_apply_simulation_345c6",
            repo_root=case_root,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_345C6
        assert manifest["qa_fail_count"] == 0
        assert manifest["validated_approved_alias_count"] == 2
        assert manifest["applied_alias_key_count"] == 2
        assert manifest["simulated_alias_applied_row_count"] == 3
        assert manifest["simulated_newly_normalized_row_count"] == 3
        assert manifest["normalized_metric_row_count_before"] == 1
        assert manifest["normalized_metric_row_count_after_simulation"] == 4
        assert manifest["normalization_coverage_ratio_before"] == 0.2
        assert manifest["normalization_coverage_ratio_after_simulation"] == 0.8
        assert manifest["normalization_coverage_ratio_delta"] == 0.6
        assert manifest["ready_candidate_count_before_simulation"] == 1
        assert manifest["ready_candidate_count_after_alias_simulation"] == 3
        assert manifest["ready_candidate_count_delta"] == 2
        assert manifest["remaining_unnormalized_raw_metric_name_count"] == 1
        assert manifest["remaining_unnormalized_metric_row_count"] == 1
        assert manifest["official_rules_modified"] is False
        assert manifest["official_alias_assets_modified"] is False
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        simulated_rows = artifacts["simulated_metric_rows"]
        assert simulated_rows[0]["normalized_metric_name"] == ""
        assert simulated_rows[0]["simulated_normalized_metric_name"] == "metric_a"
        assert simulated_rows[3]["normalized_metric_name"] == "revenue"
        assert simulated_rows[3]["simulation_applied"] is False
        assert len(artifacts["non_applied_aliases"]) == 0
        assert artifacts["remaining_blind_spots"][0]["raw_metric_name"] == "Alias C"
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345c6_missing_required_inputs_fail_clearly() -> None:
    case_root = _make_case_root()
    try:
        missing_dir = case_root / "missing"
        missing_dir.mkdir(parents=True, exist_ok=True)
        try:
            build_reviewed_alias_apply_simulation_345c6(
                metric_candidate_normalization_coverage_345c_dir=missing_dir,
                reviewed_alias_decision_ingestion_345c5_dir=missing_dir,
                output_dir=case_root / "output" / "reviewed_alias_apply_simulation_345c6",
                repo_root=case_root,
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing 345C/345C5 inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
